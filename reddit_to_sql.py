import praw
import prawcore
import mysql.connector
from mysql.connector import Error
import time

# Reddit API credentials
client_id = '8Y2JBExANVg2hUsbSmDHow'
client_secret = '4via0PULXjg8lOetD62SgCpCuFbzCw'
user_agent = 'windows:beauty_trends:1'

# Authenticate with the Reddit API
reddit = praw.Reddit(client_id=client_id, client_secret=client_secret, user_agent=user_agent)

# Subreddits to get posts from
subreddits = ['beauty', 'makeup']

# Keywords to look for
keywords = ['beauty', 'makeup', 'skincare', 'cosmetics', 'hair', 'skin']

def extract_keywords(title):
    return ','.join([keyword for keyword in keywords if keyword.lower() in title.lower()])

def fetch_posts(subreddit_name, retries=3, delay=5):
    for attempt in range(retries):
        try:
            subreddit = reddit.subreddit(subreddit_name)
            return list(subreddit.hot(limit=50))
        except prawcore.exceptions.RequestException as e:
            print(f"Error fetching posts from subreddit {subreddit_name} (attempt {attempt+1}): {e}")
            time.sleep(delay)
    return []

try:
    # Connect to MySQL database
    connection = mysql.connector.connect(
        host='localhost',
        database='reddit_trends_db',
        user='root',
        password='Lenovo_sql1541@'
    )

    if connection.is_connected():
        cursor = connection.cursor()
        cursor.execute('USE reddit_trends_db')

        # Fetch and insert data from each subreddit
        for subreddit_name in subreddits:
            trending_posts = fetch_posts(subreddit_name)
            
            for post in trending_posts:
                post_keywords = extract_keywords(post.title)
                cursor.execute(
                    "INSERT INTO trends (title, score, url, num_comments, created_utc, subreddit, keywords) VALUES (%s, %s, %s, %s, FROM_UNIXTIME(%s), %s, %s)",
                    (post.title, post.score, post.url, post.num_comments, post.created_utc, subreddit_name, post_keywords)
                )
        
        connection.commit()
        print("Data inserted successfully into the database.")

except Error as e:
    print(f"Error: {e}")
finally:
    if connection.is_connected():
        cursor.close()
        connection.close()
        print("MySQL connection is closed.")
