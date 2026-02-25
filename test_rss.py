import feedparser
import requests

def test_rss_feed(name, url):
    try:
        print(f"\n=== Testing {name} ===")
        print(f"URL: {url}")
        
        # Test HTTP request first
        response = requests.get(url, timeout=10)
        print(f"HTTP Status: {response.status_code}")
        
        if response.status_code == 200:
            # Parse RSS feed
            feed = feedparser.parse(response.content)
            print(f"Feed title: {feed.feed.get('title', 'No title')}")
            print(f"Number of entries: {len(feed.entries)}")
            
            if feed.entries:
                print(f"First entry: {feed.entries[0].title}")
                return True
            else:
                print("No entries found")
                return False
        else:
            print("HTTP request failed")
            return False
            
    except Exception as e:
        print(f"Error: {e}")
        return False

# Test the new feeds
feeds_to_test = [
    ("Politics", "https://www.theguardian.com/politics/rss"),
    ("Lifestyle & Health", "https://www.medicalnewstoday.com/rss.xml"),
    ("Wired Tech", "https://www.wired.com/feed/rss"),
    ("Hacker News", "https://hnrss.org/frontpage"),
]

print("Testing RSS feeds...")
for name, url in feeds_to_test:
    test_rss_feed(name, url)
