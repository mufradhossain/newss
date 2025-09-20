import streamlit as st
import psycopg2
from datetime import datetime, timedelta
import pytz

st.set_page_config(layout="wide")
# Accessing secrets
secrets = st.secrets
db_user = secrets["db_user"]
db_password = secrets["db_password"]
db_host = secrets["db_host"]
db_port = secrets["db_port"]
db_name = secrets["db_name"]



# Function to fetch unique categories from the PostgreSQL database
def fetch_categories_from_db():
    # Get the timestamp for 24 hours ago
    twenty_four_hours_ago = (datetime.now() - timedelta(hours=24)).timestamp() * 1000
    conn = psycopg2.connect(database=db_name, user=db_user, password=db_password, host=db_host, port=db_port)
    c = conn.cursor()
    c.execute(f"SELECT slug FROM articles WHERE summary != '' AND last_published_at > {twenty_four_hours_ago} ORDER BY last_published_at DESC")
    categories = {row[0].split('/')[0].upper() for row in c.fetchall()}  # Convert slugs to uppercase
    conn.close()
    categories_list = sorted(categories)
    categories_list.insert(0, 'All')  # Insert 'All' at the beginning
    return categories_list





# Function to fetch data from PostgreSQL database based on selected categories
def fetch_data_from_db(selected_categories):
    conn = psycopg2.connect(database=db_name, user=db_user, password=db_password, host=db_host, port=db_port)
    c = conn.cursor()
    # Get the timestamp for 24 hours ago
    twenty_four_hours_ago = (datetime.now() - timedelta(hours=24)).timestamp() * 1000
    
    # Construct the query based on selected categories
# Construct the query based on selected categories
    if not selected_categories or 'All' in selected_categories:
        query = "SELECT headline, last_published_at, summary, url, hero_image_s3_key, slug FROM articles WHERE summary != '' AND last_published_at > %s ORDER BY last_published_at DESC"
        c.execute(query, (twenty_four_hours_ago,))
    elif len(selected_categories) == 1:  # Only one category selected
        query = f"SELECT headline, last_published_at, summary, url, hero_image_s3_key, slug FROM articles WHERE slug LIKE %s AND summary != '' AND last_published_at > %s ORDER BY last_published_at DESC"
        params = [f"{selected_categories[0].lower()}%", twenty_four_hours_ago]
        c.execute(query, params)
    else:
        placeholders = ','.join(['%s']*len(selected_categories))
        selected_categories_condition = " OR ".join([f"slug LIKE %s" for _ in selected_categories])
        query = f"SELECT headline, last_published_at, summary, url, hero_image_s3_key, slug FROM articles WHERE ({selected_categories_condition}) AND summary != '' AND last_published_at > %s ORDER BY last_published_at DESC"
        params = [f"{category.lower()}%" for category in selected_categories] + [twenty_four_hours_ago]
        c.execute(query, params)


    data = c.fetchall()
    conn.close()
    return data





# Function to append the base URL to the hero image S3 key
def get_image_url(hero_image_s3_key):
    if hero_image_s3_key is not None:
        base_url = "https://media.prothomalo.com/"
        return base_url + hero_image_s3_key
    else:
        return None

# Function to convert timestamp to Dhaka datetime
def timestamp_to_dhaka_datetime(timestamp):
    dhaka_tz = pytz.timezone('Asia/Dhaka')
    utc_dt = datetime.utcfromtimestamp(int(timestamp) / 1000)
    utc_dt = pytz.utc.localize(utc_dt)
    dhaka_dt = utc_dt.astimezone(dhaka_tz)
    current_time = datetime.now(pytz.timezone('Asia/Dhaka'))
    time_difference = current_time - dhaka_dt

    if time_difference.total_seconds() < 3600:  # Less than an hour
        minutes_difference = int(time_difference.total_seconds() / 60)
        return f"{minutes_difference} mins ago"
    elif time_difference.total_seconds() < 86400:  # Less than 24 hours
        hours_difference = int(time_difference.total_seconds() / 3600)
        return f"{hours_difference} hours ago"
    else:
        return dhaka_dt.strftime('%Y-%m-%d %H:%M')

# Fetch unique categories from the SQLite database
categories = fetch_categories_from_db()

# Sidebar radio button for selecting categories
selected_category = st.sidebar.radio('Select Category', categories, index=0)  # Default to 'All' at the top

# Fetch data based on selected categories
if selected_category == 'All':
    articles_data = fetch_data_from_db([])
else:
    articles_data = fetch_data_from_db([selected_category.upper()]) 

# Display each news card
for article in articles_data:
    headline, last_published_at, summary, url, hero_image_s3_key, slug = article
    image_url = get_image_url(hero_image_s3_key)

    if image_url is not None:
        col1, col2 = st.columns([1, 3]) 
        with col1:
            st.image(image_url, use_container_width='always')
        with col2:
            st.title(f"{headline}")
            published_datetime = timestamp_to_dhaka_datetime(last_published_at)
            st.write(f"**{slug.split('/')[0].upper()}  |  {published_datetime}**")
            st.write(summary)
            st.link_button("Read more", url)
    else:
        st.title(f"{headline}")
        published_datetime = timestamp_to_dhaka_datetime(last_published_at)
        st.write(f"**{slug.split('/')[0].upper()}  |  {published_datetime}**")
        st.write(summary)
        st.link_button("Read more", url)
    st.write('---')
