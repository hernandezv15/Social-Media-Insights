import praw
import mysql.connector
from mysql.connector import Error

# Reddit API credentials
client_id = '8Y2JBExANVg2hUsbSmDHow'
client_secret = '4via0PULXjg8lOetD62SgCpCuFbzCw'
user_agent = 'windows:beauty_trends:1'

# Authenticate with the Reddit API
reddit = praw.Reddit(client_id=client_id, client_secret=client_secret, user_agent=user_agent)

# Subreddits to get posts from
subreddits = ['beauty', 'makeup', 'makeupaddiction', 'skincareaddiction', 'hair']

def load_keywords_with_categories(cursor):
    """Loads keywords and their categories from the database into a dictionary."""
    cursor.execute("SELECT keyword, category_id FROM keywords")
    results = cursor.fetchall()
    return {row[0]: row[1] for row in results}

def extract_keywords(title, keyword_categories):
    """Extracts keywords from a title based on predefined keywords."""
    return [keyword for keyword in keyword_categories if keyword.lower() in title.lower()]

def fetch_posts(subreddit_name):
    """Fetches posts from a specified subreddit."""
    try:
        subreddit = reddit.subreddit(subreddit_name)
        return list(subreddit.hot(limit=100))
    except Exception as e:
        print(f"Error fetching posts from subreddit {subreddit_name}: {e}")
        return []

def fetch_subreddit_id(cursor, subreddit_name):
    """Fetches or inserts the subreddit id for a given subreddit name."""
    cursor.execute("SELECT subreddit_id FROM subreddits WHERE name = %s", (subreddit_name,))
    result = cursor.fetchone()
    if result:
        return result[0]
    else:
        cursor.execute("INSERT INTO subreddits (name) VALUES (%s)", (subreddit_name,))
        return cursor.lastrowid

def insert_data_into_db(posts, cursor, subreddit_name, keyword_categories):
    """Inserts posts and their related keywords into the database."""
    subreddit_id = fetch_subreddit_id(cursor, subreddit_name)
    for post in posts:
        cursor.execute(
            "INSERT INTO posts (title, score, url, num_comments, created_utc, subreddit_id) VALUES (%s, %s, %s, %s, FROM_UNIXTIME(%s), %s)",
            (post.title, post.score, post.url, post.num_comments, post.created_utc, subreddit_id)
        )
        post_id = cursor.lastrowid

        # Extract and insert keywords
        post_keywords = extract_keywords(post.title, keyword_categories)
        for keyword in post_keywords:
            cursor.execute("SELECT keyword_id FROM keywords WHERE keyword = %s", (keyword,))
            keyword_id = cursor.fetchone()[0]
            cursor.execute("INSERT INTO post_keywords (post_id, keyword_id) VALUES (%s, %s)", (post_id, keyword_id))
            if keyword_categories[keyword]:
                update_post_category(cursor, post_id, keyword_categories[keyword])

def update_post_category(cursor, post_id, category_id):
    """Updates the category ID of a post."""
    query = """
    UPDATE posts
    SET category_id = %s
    WHERE post_id = %s;
    """
    cursor.execute(query, (category_id, post_id))
    print(f"Updated post {post_id} with category_id {category_id}")

def main():
    """Main function to handle the workflow."""
    try:
        connection = mysql.connector.connect(host='localhost', database='reddit_trends_db', user='root', password='password')
        cursor = connection.cursor(buffered=True)
        keyword_categories = load_keywords_with_categories(cursor)
        for subreddit_name in subreddits:
            print(f"Fetching posts from /r/{subreddit_name}")
            posts = fetch_posts(subreddit_name)
            if posts:
                insert_data_into_db(posts, cursor, subreddit_name, keyword_categories)
        connection.commit()
        print("All data has been inserted and processed successfully.")
    except Error as e:
        print(f"Database error: {e}")
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()
            print("MySQL connection is closed.")

if __name__ == "__main__":
    main()
