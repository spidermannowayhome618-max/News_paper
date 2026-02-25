from flask import Flask, render_template, request, jsonify
import feedparser
import re
import requests
from bs4 import BeautifulSoup
import json
import time
from datetime import datetime, timedelta
import urllib.parse
import base64

app = Flask(__name__)

# Cache for news data
news_cache = {
    'data': None,
    'timestamp': None,
    'expiry_minutes': 10  # Increased to 10 minutes for better performance
}


RSS_FEEDS = {
    "📊 Business": "https://feeds.feedburner.com/reuters/businessNews",
    "💰 Finance & Economy": "https://feeds.feedburner.com/Reuters/TopNews",
    "🌍 World News": "https://feeds.feedburner.com/reuters/worldNews",
    "🇮🇳 India News": "https://www.hindustantimes.com/rss/india-news/rssfeed.xml",
    "🚀 Technology": "https://feeds.feedburner.com/reuters/technologyNews",
    "🌍 Politics": "https://feeds.feedburner.com/reuters/politicsNews",
    "⚖️ Legal": "https://feeds.feedburner.com/reuters/legalNews",
    "🏢 Companies": "https://feeds.feedburner.com/reuters/companyNews",
    "🎯 Entertainment": "https://feeds.feedburner.com/reuters/entertainment",
    "🏃 Sports": "https://feeds.feedburner.com/reuters/sportsNews",
}

def extract_image(entry):
    # 1️⃣ media thumbnail (fastest)
    if "media_thumbnail" in entry:
        return entry.media_thumbnail[0]["url"]

    # 2️⃣ media content (fast)
    if "media_content" in entry:
        return entry.media_content[0]["url"]

    # 3️⃣ image inside summary (very fast)
    if "summary" in entry:
        match = re.search(r'<img[^>]+src="([^">]+)"', entry.summary)
        if match:
            return match.group(1)

    # 4️⃣ scrape image from article page (slower, but with timeout)
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        # Reduced timeout for faster loading
        response = requests.get(entry.link, timeout=2, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Try Open Graph image first (most reliable)
        og_image = soup.find('meta', attrs={'property': 'og:image'})
        if og_image and og_image.get('content'):
            return og_image['content']
        
        # Try Twitter image
        twitter_image = soup.find('meta', attrs={'name': 'twitter:image'})
        if twitter_image and twitter_image.get('content'):
            return twitter_image['content']
        
    except requests.exceptions.RequestException:
        # Silently fail for network errors to maintain performance
        pass
    except Exception:
        # Silently fail for other errors
        pass

    return None

def extract_key_points(summary, title):
    """Extract key points from summary and format as bullet points for important topics"""
    important_keywords = [
        'breakthrough', 'launch', 'release', 'update', 'security', 'vulnerability', 
        'hack', 'breach', 'acquisition', 'merger', 'investment', 'funding', 
        'ai', 'artificial intelligence', 'machine learning', 'crypto', 'bitcoin',
        'metaverse', 'nft', 'blockchain', 'cybersecurity', 'data breach',
        'announcement', 'partnership', 'deal', 'acquired', 'funded', 'raised'
    ]
    
    # Check if topic is important
    text_to_check = (title + ' ' + summary).lower()
    is_important = any(keyword in text_to_check for keyword in important_keywords)
    
    if not is_important:
        return summary
    
    # Extract sentences that contain important information
    sentences = summary.split('.')
    key_points = []
    
    for sentence in sentences:
        sentence = sentence.strip()
        if sentence and any(keyword in sentence.lower() for keyword in important_keywords):
            key_points.append(sentence)
    
    # If we found key points, format as bullet points
    if key_points and len(key_points) <= 3:
        bullet_points = '<div class="important-topic"><ul>'
        for point in key_points[:3]:  # Max 3 bullet points
            bullet_points += f'<li>{point.strip()}</li>'
        bullet_points += '</ul></div>'
        return bullet_points
    
    return summary

def fetch_rss(url, limit=25):
    try:
        print(f"Fetching RSS from: {url}")
        
        # Special handling for Google News RSS
        if 'news.google.com' in url:
            return fetch_google_news_rss(url, limit)
        
        feed = feedparser.parse(url)
        articles = []
        
        if not feed.entries:
            print(f"No entries found in feed: {url}")
            return []

        print(f"Found {len(feed.entries)} articles in {url}")
        
        # Simplified date filtering - just check if article is from 2026 or recent
        current_date = datetime.now()
        recent_entries = []
        
        for entry in feed.entries[:limit]:  # Limit entries early for performance
            # Quick date check
            pub_date = None
            is_recent = True  # Default to recent for performance
            
            if hasattr(entry, 'published_parsed') and entry.published_parsed:
                try:
                    pub_date = datetime(*entry.published_parsed[:6])
                    # Only filter if date is very old (more than 6 months)
                    if pub_date < current_date - timedelta(days=180):
                        is_recent = False
                except:
                    pass
            
            if is_recent:
                recent_entries.append(entry)
        
        print(f"Found {len(recent_entries)} recent articles in {url}")
        
        for entry in recent_entries:
            # Clean summary text
            summary = entry.get("summary", "")
            clean_summary = re.sub(r'<[^>]+>', '', summary)
            clean_summary = clean_summary[:300] + "..." if len(clean_summary) > 300 else clean_summary
            
            # Extract key points for important topics
            formatted_summary = extract_key_points(clean_summary, entry.title)
            
            # Get publication date for display
            pub_date_str = ""
            if hasattr(entry, 'published_parsed') and entry.published_parsed:
                try:
                    pub_date = datetime(*entry.published_parsed[:6])
                    pub_date_str = pub_date.strftime("%b %d, %Y")
                except:
                    pass
            
            articles.append({
                "title": entry.title,
                "link": entry.link,
                "summary": formatted_summary,
                "image": extract_image(entry),
                "source": feed.feed.get("title", ""),
                "date": pub_date_str
            })
        return articles
    except Exception as e:
        print(f"Error fetching RSS from {url}: {e}")
        return []

def fetch_google_news_rss(url, limit=25):
    """Special handler for Google News RSS feeds"""
    try:
        print(f"Fetching Google News RSS from: {url}")
        
        # Use requests to get the RSS feed with proper headers
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        
        # Parse the RSS feed
        feed = feedparser.parse(response.content)
        
        if not feed.entries:
            print(f"No entries found in Google News feed: {url}")
            return []
        
        articles = []
        processed_count = 0
        
        for entry in feed.entries:
            if processed_count >= limit:
                break
                
            try:
                # Extract the real article URL from Google News entry
                article_url = extract_google_news_article_url(entry)
                
                if not article_url:
                    continue
                
                # Clean summary text
                summary = entry.get("summary", "")
                clean_summary = re.sub(r'<[^>]+>', '', summary)
                clean_summary = clean_summary[:300] + "..." if len(clean_summary) > 300 else clean_summary
                
                # Extract key points
                formatted_summary = extract_key_points(clean_summary, entry.title)
                
                # Get publication date
                pub_date_str = ""
                if hasattr(entry, 'published_parsed') and entry.published_parsed:
                    try:
                        pub_date = datetime(*entry.published_parsed[:6])
                        pub_date_str = pub_date.strftime("%b %d, %Y")
                    except:
                        pass
                
                articles.append({
                    "title": entry.title,
                    "link": article_url,  # Use the extracted real URL
                    "summary": formatted_summary,
                    "image": extract_image(entry),
                    "source": "Google News",
                    "date": pub_date_str
                })
                
                processed_count += 1
                print(f"Processed Google News article: {entry.title[:50]}...")
                
            except Exception as e:
                print(f"Error processing Google News entry: {e}")
                continue
        
        print(f"Successfully processed {len(articles)} Google News articles")
        return articles
        
    except Exception as e:
        print(f"Error fetching Google News RSS: {e}")
        return []

def decode_google_news_url(encoded_part):
    """Decode a CBMi/0gG-style Google News encoded URL using URL-safe base64.

    Google News encodes the destination article URL inside a protobuf blob
    that is URL-safe base64 encoded. This function handles the protobuf format
    to extract the real article URL.
    """
    try:
        print(f"Attempting to decode Google News URL part: {encoded_part[:50]}...")
        
        # Clean the encoded part - remove any URL parameters or extra characters
        clean_encoded = encoded_part.split('?')[0].split('&')[0]
        
        # Ensure correct padding (base64 length must be multiple of 4)
        padding_needed = (4 - len(clean_encoded) % 4) % 4
        padded = clean_encoded + '=' * padding_needed
        
        decoded_bytes = base64.urlsafe_b64decode(padded)
        print(f"Decoded {len(decoded_bytes)} bytes")
        
        # Method 1: Try to find URL patterns directly in the decoded bytes
        decoded_text = decoded_bytes.decode('utf-8', errors='ignore')
        url_patterns = re.findall(r'https?://[^\s<>"\'\]\)}]+', decoded_text)
        if url_patterns:
            for url in url_patterns:
                if len(url) > 20 and '.' in url:
                    print(f'Found URL via pattern matching: {url}')
                    return url
        
        # Method 2: Look for URL-like strings in the protobuf data
        # URLs in Google News protobuf are often length-prefixed strings
        i = 0
        while i < len(decoded_bytes) - 10:
            # Look for length-prefixed strings (common in protobuf)
            if i + 1 < len(decoded_bytes):
                # Try different length field sizes
                for length_bytes in [1, 2, 4]:
                    if i + length_bytes < len(decoded_bytes):
                        if length_bytes == 1:
                            str_len = decoded_bytes[i]
                        elif length_bytes == 2:
                            str_len = int.from_bytes(decoded_bytes[i:i+2], 'little')
                        else:  # 4 bytes
                            str_len = int.from_bytes(decoded_bytes[i:i+4], 'little')
                        
                        if 10 < str_len < 500 and i + length_bytes + str_len <= len(decoded_bytes):
                            # Extract the string
                            start = i + length_bytes
                            end = start + str_len
                            potential_url = decoded_bytes[start:end].decode('utf-8', errors='ignore')
                            
                            # Check if it looks like a URL
                            if potential_url.startswith(('http://', 'https://')) and '.' in potential_url:
                                # Clean the URL
                                clean_url = re.split(r'[\s<>"\'\]\)}\x00]', potential_url)[0]
                                if len(clean_url) > 20:
                                    print(f'Found URL via protobuf parsing: {clean_url}')
                                    return clean_url
            
            i += 1
        
        # Method 3: Scan for http/https byte sequences more thoroughly
        for prefix in [b'https://', b'http://']:
            idx = decoded_bytes.find(prefix)
            if idx != -1:
                # Extract from the found position until we hit a null byte or invalid URL char
                url_bytes = b''
                for j in range(idx, len(decoded_bytes)):
                    byte = decoded_bytes[j]
                    # Stop at null byte or common URL terminators
                    if byte == 0 or byte in [32, 10, 13, 34, 39, 60, 62]:  # space, newline, cr, quote, bracket
                        break
                    url_bytes += bytes([byte])
                
                try:
                    url_str = url_bytes.decode('utf-8', errors='ignore').strip()
                    if len(url_str) > 15 and '.' in url_str:
                        print(f'Found URL via byte scanning: {url_str}')
                        return url_str
                except:
                    pass
        
        # Method 4: Try to parse as varint-prefixed protobuf string
        i = 0
        while i < len(decoded_bytes) - 5:
            # Try to parse varint length
            varint = 0
            varint_bytes = 0
            for j in range(i, min(i + 5, len(decoded_bytes))):
                byte = decoded_bytes[j]
                varint |= (byte & 0x7F) << (7 * varint_bytes)
                varint_bytes += 1
                if byte < 0x80:  # MSB not set, last byte of varint
                    break
            
            if 10 < varint < 500 and i + varint_bytes + varint <= len(decoded_bytes):
                # Extract the string
                start = i + varint_bytes
                end = start + varint
                potential_url = decoded_bytes[start:end].decode('utf-8', errors='ignore')
                
                if potential_url.startswith(('http://', 'https://')) and '.' in potential_url:
                    clean_url = re.split(r'[\s<>"\'\]\)}\x00]', potential_url)[0]
                    if len(clean_url) > 20:
                        print(f'Found URL via varint parsing: {clean_url}')
                        return clean_url
            
            i += 1
        
        print(f'Could not extract URL from decoded bytes')
        return None
        
    except Exception as e:
        print(f'decode_google_news_url error: {e}')
        import traceback
        traceback.print_exc()
        return None


def extract_google_news_article_url(entry):
    """Extract the real article URL from a Google News RSS entry"""
    try:
        # Method 1: Check if entry has a direct link
        if hasattr(entry, 'link') and entry.link:
            link = entry.link
            # If it's not a Google News URL, use it directly
            if 'news.google.com' not in link:
                return link
            
            # For Google News URLs, try to follow redirects to get the real URL
            print(f"Attempting to resolve Google News URL: {link}")
            
            try:
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
                }
                
                # Make a request with redirect following
                response = requests.get(link, headers=headers, timeout=10, allow_redirects=True)
                final_url = response.url
                
                # If we got redirected to a real article URL, use that
                if final_url != link and 'news.google.com' not in final_url:
                    print(f'Successfully redirected to: {final_url}')
                    return final_url
                else:
                    print(f'Redirect did not yield external URL, final URL: {final_url}')
                    
            except Exception as redirect_error:
                print(f'Redirect attempt failed: {redirect_error}')
            
            # If redirect fails, try to decode the CBM parameter
            path = urllib.parse.urlparse(link).path
            for part in path.split('/'):
                if part.startswith('CBM'):
                    decoded = decode_google_news_url(part)
                    if decoded:
                        print(f'Decoded Google News URL from entry link: {decoded}')
                        return decoded
        
        # Method 2: Check for alternative URL fields
        for field in ['id', 'guid', 'source_link']:
            if hasattr(entry, field):
                url = getattr(entry, field)
                if url and isinstance(url, str) and url.startswith('http') and 'news.google.com' not in url:
                    return url
        
        # Method 3: Parse the summary for URLs
        summary = entry.get("summary", "")
        if summary:
            # Look for URLs in the summary
            url_pattern = r'https?://[^\s<>"\'\)\]]+'
            urls_found = re.findall(url_pattern, summary)
            for url in urls_found:
                if 'news.google.com' not in url and len(url) > 20:
                    print(f'Found URL in summary: {url}')
                    return url
        
        # Method 4: Return the Google News URL as last resort
        if hasattr(entry, 'link') and entry.link:
            print(f'Using original Google News URL as fallback: {entry.link}')
            return entry.link
            
        return None
        
    except Exception as e:
        print(f"Error extracting Google News URL: {e}")
        return None

def clear_cache():
    """Clear the news cache to force fresh data fetch"""
    global news_cache
    news_cache['data'] = None
    news_cache['timestamp'] = None
    print("News cache cleared!")

def get_news_data():
    # Check if cache is still valid
    now = datetime.now()
    if (news_cache['data'] is not None and 
        news_cache['timestamp'] is not None and 
        now - news_cache['timestamp'] < timedelta(minutes=news_cache['expiry_minutes'])):
        print("Using cached news data")
        return news_cache['data']
    
    print("Fetching fresh news data...")
    news_data = {}
    
    # Fetch news with timeout handling
    for category, url in RSS_FEEDS.items():
        try:
            print(f"\n=== Fetching {category} ===")
            news_data[category] = fetch_rss(url)
            print(f"Successfully fetched {len(news_data[category])} articles for {category}")
        except Exception as e:
            print(f"Failed to fetch {category}: {e}")
            news_data[category] = []  # Empty list as fallback
    
    # Update cache
    news_cache['data'] = news_data
    news_cache['timestamp'] = now
    
    print(f"\n=== News Summary ===")
    for category, articles in news_data.items():
        print(f"{category}: {len(articles)} articles")
    
    return news_data

def process_news_for_chatbot():
    """Process all news articles for chatbot analysis"""
    news_data = get_news_data()
    processed_articles = []
    
    for category, articles in news_data.items():
        for article in articles:
            processed_articles.append({
                'title': article['title'],
                'summary': article['summary'],
                'category': category,
                'source': article['source'],
                'link': article['link']
            })
    
    return processed_articles

def extract_article_content(url):
    """Extract article content from external URL with advanced paywall bypass"""
    
    # If the URL is just the CBMi encoded string, reconstruct the full Google News URL
    if url.startswith('CBMi') and ' ' not in url:
        url = f"https://news.google.com/rss/articles/{url}"
        print(f"Reconstructed Google News URL: {url}")

    # Handle Google News RSS URLs
    if 'news.google.com/rss/articles/' in url:
        # Google News RSS URLs need to be resolved to actual article URLs
        try:
            print(f"Processing Google News URL: {url}")
            
            # Extract the actual article URL from Google News RSS parameters
            
            # Parse the URL to get the actual article URL
            parsed_url = urllib.parse.urlparse(url)
            query_params = urllib.parse.parse_qs(parsed_url.query)
            
            # Try to extract the article URL from the CBM parameter (query or path)
            encoded_url = None
            if 'CBMi' in query_params:
                encoded_url = query_params['CBMi'][0]
            else:
                # Try to extract from path
                path_parts = parsed_url.path.split('/')
                for part in path_parts:
                    if part.startswith('CBM'):
                        encoded_url = part
                        break
            
            if encoded_url:
                print(f"Found encoded Google News parameter: {encoded_url[:80]}...")
                # Use URL-safe base64 + protobuf-aware decoder
                decoded_url = decode_google_news_url(encoded_url)
                if decoded_url:
                    url = decoded_url
                    print(f"Successfully decoded Google News URL: {url}")
                else:
                    print("Could not decode CBM parameter, will try redirect fallback")
            
            # If we still have a Google News URL, try direct approach
            if 'news.google.com' in url:
                print("Still have Google News URL, trying direct access...")
                
                # Try to follow redirects as fallback
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
                }
                response = requests.get(url, timeout=10, headers=headers, allow_redirects=True)
                final_url = response.url
                
                print(f"Redirect result: {final_url}")
                
                # If we got redirected to a real article URL, use that
                if final_url != url and 'news.google.com' not in final_url:
                    url = final_url
                    print(f"Successfully redirected to: {url}")
                else:
                    # Last resort: try to extract from response content
                    try:
                        content = response.text
                        # Look for canonical URL or alternative links
                        canonical_match = re.search(r'<link[^>]*rel=["\']canonical["\'][^>]*href=["\']([^"\']+)["\']', content)
                        if canonical_match:
                            canonical_url = canonical_match.group(1)
                            if 'news.google.com' not in canonical_url:
                                url = canonical_url
                                print(f"Found canonical URL: {url}")
                    except Exception as e:
                        print(f"Error extracting canonical URL: {e}")
            
            # If we still have a Google News URL, return helpful message
            if 'news.google.com' in url:
                print("Could not resolve Google News URL, returning message")
                return {
                    'title': "Google News Article",
                    'content': f"This is a Google News RSS article. Google News aggregates content from various sources and often requires visiting the original source website. The article URL could not be automatically resolved. Please visit the original source to read the full article: {url}",
                    'image': None,
                    'source_url': url
                }
            else:
                print(f"Proceeding with extracted URL: {url}")
                
        except Exception as e:
            print(f"Error resolving Google News URL: {e}")
            return {
                'title': "Google News Article",
                'content': f"This Google News article could not be resolved automatically. Google News articles often require visiting the original source. Please visit the original source to read the full article: {url}",
                'image': None,
                'source_url': url
            }
    
    # Multiple user agent strings to try
    user_agents = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15',
        'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    ]
    
    def try_extract_with_headers(url, headers, referer=None):
        """Try to extract content with specific headers"""
        try:
            response = requests.get(url, timeout=15, headers=headers)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Remove unwanted elements
            for element in soup(['script', 'style', 'nav', 'footer', 'header', 'aside', 'advertisement', 'button', 'form']):
                element.decompose()
            
            # Try to find article title
            title = None
            title_selectors = ['h1', 'h2', '.headline', '.article-title', '[data-testid="headline"]', '.entry-title', '.page-title', 'title']
            
            # Add Times of India specific selectors
            if 'timesofindia' in url.lower():
                title_selectors = ['h1', '.headline', 'h1.artTitle', '.artTitle', '.main-title'] + title_selectors
            
            for selector in title_selectors:
                title_elem = soup.select_one(selector)
                if title_elem and title_elem.get_text().strip():
                    title = title_elem.get_text().strip()
                    break
            
            if not title:
                title = "Article"
            
            # Try to find article content
            content = None
            content_selectors = [
                '.article-content', '.story-content', '.entry-content',
                '[data-testid="articleBody"]', '.post-content', '.article-body',
                '.main-content', '.content-body', '.page-content', '.content'
            ]
            
            # Add Times of India specific selectors
            if 'timesofindia' in url.lower():
                content_selectors = [
                    '.artText', '.article-content', '.story-content', 
                    '[data-testid="articleBody"]', '.Normal', '.content',
                    '.story', '.article', '.main-story'
                ] + content_selectors
            
            for selector in content_selectors:
                content_elem = soup.select_one(selector)
                if content_elem:
                    content = content_elem.get_text().strip()
                    if len(content) > 100:
                        break
            
            # If no specific content found, try to get all paragraphs
            if not content or len(content) < 100:
                paragraphs = soup.find_all('p')
                all_paragraphs = [p.get_text().strip() for p in paragraphs if p.get_text().strip() and len(p.get_text().strip()) > 20]
                
                # For Times of India, try to filter out non-article paragraphs
                if 'timesofindia' in url.lower():
                    filtered_paragraphs = []
                    for p in all_paragraphs:
                        if not any(skip in p.lower() for skip in ['times of india', 'follow us', 'click here', 'read more', 'subscribe', 'download', 'also read']):
                            filtered_paragraphs.append(p)
                    all_paragraphs = filtered_paragraphs[:20]
                else:
                    all_paragraphs = all_paragraphs[:15]
                
                content = '\n\n'.join(all_paragraphs)
            
            # Clean up content and format for readability
            if content:
                content = re.sub(r'\s+', ' ', content)
                content = content.replace('\n', ' ').replace('\t', ' ')
                # Remove multiple spaces
                content = re.sub(r'\s{2,}', ' ', content)
                
                # Break long content into paragraphs for better readability
                sentences = re.split(r'[.!?]+', content)
                paragraphs = []
                current_paragraph = ""
                
                for sentence in sentences:
                    sentence = sentence.strip()
                    if sentence:
                        if len(current_paragraph + sentence) < 300:  # Paragraph should be around 300 chars
                            current_paragraph += sentence + ". "
                        else:
                            if current_paragraph:
                                paragraphs.append(current_paragraph.strip())
                            current_paragraph = sentence + ". "
                
                # Add remaining content
                if current_paragraph:
                    paragraphs.append(current_paragraph.strip())
                
                # Join paragraphs with proper HTML paragraph tags
                if len(paragraphs) > 1:
                    content = '\n\n'.join([f'<p>{para}</p>' for para in paragraphs])
                else:
                    content = f'<p>{content}</p>'
                
                # Limit content length
                if len(content) > 4000:
                    content = content[:4000] + "...</p>"
            
            # Try to find main image
            image = None
            image_elem = soup.select_one('meta[property="og:image"]')
            if image_elem:
                image = image_elem.get('content')
            
            return {
                'title': title,
                'content': content or "Content not available",
                'image': image,
                'source_url': url
            }
            
        except Exception as e:
            print(f"Extraction failed with headers: {e}")
            return None
    
    # Try different strategies
    strategies = [
        # Strategy 1: Standard headers
        lambda url: try_extract_with_headers(url, {
            'User-Agent': user_agents[0],
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Cache-Control': 'max-age=0'
        }),
        
        # Strategy 2: Google bot user agent (often bypasses paywalls)
        lambda url: try_extract_with_headers(url, {
            'User-Agent': 'Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'From': 'googlebot(at)googlebot.com'
        }),
        
        # Strategy 3: Facebook referer (many sites allow Facebook crawler)
        lambda url: try_extract_with_headers(url, {
            'User-Agent': user_agents[1],
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Referer': 'https://www.facebook.com/',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'same-site'
        }),
        
        # Strategy 4: Twitter referer
        lambda url: try_extract_with_headers(url, {
            'User-Agent': user_agents[2],
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Referer': 'https://t.co/',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'cross-site'
        }),
        
        # Strategy 5: Different user agent with no referer
        lambda url: try_extract_with_headers(url, {
            'User-Agent': user_agents[3],
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Cache-Control': 'no-cache',
            'Pragma': 'no-cache'
        })
    ]
    
    # Add TOI-specific strategies at the beginning if it's a TOI URL
    if 'timesofindia' in url.lower():
        toi_strategies = [
            # TOI Strategy 1: Googlebot (newspaper rule allows Google bots)
            lambda url: try_extract_with_headers(url, {
                'User-Agent': 'Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.9',
                'Accept-Encoding': 'gzip, deflate',
                'From': 'googlebot(at)googlebot.com',
                'X-Forwarded-For': '66.249.64.1',
            }),
            # TOI Strategy 2: Mobile user agent (AMP version often has less restriction)
            lambda url: try_extract_with_headers(
                url.replace('timesofindia.indiatimes.com', 'm.timesofindia.com'),
                {
                    'User-Agent': 'Mozilla/5.0 (Linux; Android 10; SM-G973F) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.6099.144 Mobile Safari/537.36',
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                    'Accept-Language': 'en-US,en;q=0.9',
                    'Accept-Encoding': 'gzip, deflate',
                }
            ),
            # TOI Strategy 3: Google first-click-free via referer
            lambda url: try_extract_with_headers(url, {
                'User-Agent': user_agents[0],
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.9',
                'Accept-Encoding': 'gzip, deflate',
                'Referer': 'https://www.google.com/search?q=' + url.split('/')[-2].replace('-', '+'),
                'Cache-Control': 'no-cache',
            }),
        ]
        strategies = toi_strategies + strategies

    # Try each strategy
    for i, strategy in enumerate(strategies):
        try:
            result = strategy(url)
            if result and result['content'] and len(result['content'].strip()) > 100:
                print(f"Successfully extracted content using strategy {i+1}")
                return result
        except Exception as e:
            print(f"Strategy {i+1} failed: {e}")
            continue
    
    # If all strategies fail, return appropriate message
    if 'timesofindia' in url.lower():
        return {
            'title': "📰 Times of India Article",
            'content': (
                '<div style="text-align:center; padding: 30px 20px; background: #fff8f0; border: 1px solid #f0c040; border-radius: 8px;">' 
                '<div style="font-size: 48px; margin-bottom: 15px;">📰</div>'
                '<h2 style="color: #c0392b; margin-bottom: 10px;">Times of India - Subscription Required</h2>'
                '<p style="color: #555; margin-bottom: 15px; line-height: 1.6;">'
                'Times of India places most of its content behind a subscription paywall. '
                'We tried multiple bypass strategies but were unable to retrieve the full article text.</p>'
                f'<a href="{url}" target="_blank" style="display:inline-block; background: #c0392b; color: white; padding: 12px 24px; border-radius: 6px; text-decoration: none; font-weight: bold;">'
                '🔗 Read on Times of India</a>'
                '</div>'
            ),
            'image': None,
            'source_url': url
        }
    elif any(site in url.lower() for site in ['thehindu', 'ndtv', 'indiatoday', 'hindustantimes', 'livemint', 'economictimes']):
        site_name = next((s for s in ['The Hindu', 'NDTV', 'India Today', 'Hindustan Times', 'Livemint', 'Economic Times'] 
                         if s.lower().replace(' ', '') in url.lower().replace('.', '').replace('-', '')), 'this publication')
        return {
            'title': f"Article from {site_name}",
            'content': (
                f'<div style="text-align:center; padding: 30px 20px; background: #f0f4ff; border: 1px solid #a0b8e0; border-radius: 8px;">'
                '<div style="font-size: 48px; margin-bottom: 15px;">🔒</div>'
                f'<h2 style="color: #2c5f8a; margin-bottom: 10px;">Article from {site_name}</h2>'
                '<p style="color: #555; margin-bottom: 15px; line-height: 1.6;">'
                f'This article from {site_name} could not be loaded automatically. '
                'This may be due to paywall restrictions or site structure. </p>'
                f'<a href="{url}" target="_blank" style="display:inline-block; background: #2c5f8a; color: white; padding: 12px 24px; border-radius: 6px; text-decoration: none; font-weight: bold;">'
                f'🔗 Read on {site_name}</a>'
                '</div>'
            ),
            'image': None,
            'source_url': url
        }
    else:
        return {
            'title': "Article Loading Error",
            'content': f"Unable to load article content after multiple attempts. Please visit the original source: {url}",
            'image': None,
            'source_url': url
        }

def answer_news_question(question, articles):
    """Answer questions about news based on article content"""
    question_lower = question.lower()
    
    # Define keywords for different types of questions
    keywords = {
        'budget': ['budget', 'finance', 'economy', 'financial', 'tax', 'spending'],
        'tech': ['technology', 'tech', 'ai', 'artificial intelligence', 'startup', 'software'],
        'business': ['business', 'company', 'market', 'stock', 'investment', 'merger'],
        'highlights': ['highlight', 'important', 'top', 'main', 'key', 'summary'],
        'today': ['today', 'latest', 'recent', 'new', 'current']
    }
    
    # Find relevant articles based on keywords
    relevant_articles = []
    
    for article in articles:
        title_lower = article['title'].lower()
        summary_lower = article['summary'].lower()
        combined_text = title_lower + ' ' + summary_lower
        
        # Check if article matches question keywords
        relevance_score = 0
        for topic, kws in keywords.items():
            if topic in question_lower or any(kw in question_lower for kw in kws):
                if any(kw in combined_text for kw in kws):
                    relevance_score += 2
                if topic in question_lower:
                    relevance_score += 1
        
        if relevance_score > 0:
            article['relevance_score'] = relevance_score
            relevant_articles.append(article)
    
    # Sort by relevance and get top articles
    relevant_articles.sort(key=lambda x: x['relevance_score'], reverse=True)
    top_articles = relevant_articles[:5]
    
    if not top_articles:
        return "I couldn't find specific information about that topic in today's news. Try asking about technology, business, or general news highlights."
    
    # Generate response based on question type
    if 'highlight' in question_lower or 'summary' in question_lower or 'important' in question_lower:
        return generate_summary_response(top_articles)
    elif 'budget' in question_lower:
        return generate_budget_response(top_articles)
    elif 'tech' in question_lower or 'technology' in question_lower:
        return generate_tech_response(top_articles)
    elif 'business' in question_lower:
        return generate_business_response(top_articles)
    else:
        return generate_general_response(top_articles)

def generate_summary_response(articles):
    """Generate a summary of top news"""
    response = "📰 **Today's Top News Highlights:**\n\n"
    
    for i, article in enumerate(articles[:3], 1):
        response += f"{i}. **{article['title']}**\n"
        response += f"   📂 {article['category']}\n"
        # Clean summary for better readability
        clean_summary = re.sub(r'<[^>]+>', '', article['summary'])
        response += f"   📝 {clean_summary[:100]}...\n\n"
    
    return response

def generate_budget_response(articles):
    """Generate budget-specific response"""
    response = "💰 **Budget & Financial News:**\n\n"
    
    for i, article in enumerate(articles[:3], 1):
        response += f"{i}. **{article['title']}**\n"
        clean_summary = re.sub(r'<[^>]+>', '', article['summary'])
        response += f"   📝 {clean_summary[:120]}...\n\n"
    
    return response

def generate_tech_response(articles):
    """Generate technology-specific response"""
    response = "💻 **Technology News:**\n\n"
    
    for i, article in enumerate(articles[:3], 1):
        response += f"{i}. **{article['title']}**\n"
        response += f"   🏷️ {article['category']}\n"
        clean_summary = re.sub(r'<[^>]+>', '', article['summary'])
        response += f"   📝 {clean_summary[:120]}...\n\n"
    
    return response

def generate_business_response(articles):
    """Generate business-specific response"""
    response = "📊 **Business News:**\n\n"
    
    for i, article in enumerate(articles[:3], 1):
        response += f"{i}. **{article['title']}**\n"
        response += f"   🏢 {article['source']}\n"
        clean_summary = re.sub(r'<[^>]+>', '', article['summary'])
        response += f"   📝 {clean_summary[:120]}...\n\n"
    
    return response

def generate_general_response(articles):
    """Generate general response"""
    response = "📰 **Relevant News:**\n\n"
    
    for i, article in enumerate(articles[:3], 1):
        response += f"{i}. **{article['title']}**\n"
        response += f"   📂 {article['category']}\n"
        clean_summary = re.sub(r'<[^>]+>', '', article['summary'])
        response += f"   📝 {clean_summary[:120]}...\n\n"
    
    return response

@app.route("/api/chat", methods=["POST"])
def chat_api():
    """API endpoint for chatbot questions"""
    try:
        data = request.get_json()
        question = data.get("question", "")
        
        if not question:
            return jsonify({"error": "No question provided"}), 400
        
        # Get current news articles
        articles = process_news_for_chatbot()
        
        # Generate answer
        answer = answer_news_question(question, articles)
        
        return jsonify({
            "answer": answer,
            "timestamp": json.dumps({"timestamp": "now"})  # Simple timestamp
        })
        
    except Exception as e:
        return jsonify({"error": f"An error occurred: {str(e)}"}), 500

@app.route("/refresh")
def refresh_news():
    """Endpoint to manually refresh news data"""
    clear_cache()
    news_data = get_news_data()
    return jsonify({
        "status": "success",
        "message": "News data refreshed successfully!",
        "categories": {category: len(articles) for category, articles in news_data.items()}
    })

# URL mapping for RSS categories
CATEGORY_URLS = {
    "📊 Business": "business",
    "💰 Finance & Economy": "finance",
    "🌍 World News": "world",
    "🇮🇳 India News": "india",
    "🚀 Technology": "technology",
    "🌍 Politics": "politics",
    "⚖️ Legal": "legal",
    "🏢 Companies": "companies",
    "🎯 Entertainment": "entertainment",
    "🏃 Sports": "sports",
}

@app.route("/")
def home():
    news_data = get_news_data()
    return render_template("index.html", news_data=news_data, current_category="Home", rss_categories=RSS_FEEDS.keys(), category_urls=CATEGORY_URLS)

@app.route("/article")
def article_view():
    """Display article content from external URL"""
    url = request.args.get('url')
    
    if not url:
        return "Article URL not provided", 400
    
    # Try to find a cached RSS summary for this article as fallback
    rss_summary = None
    rss_title = None
    rss_image = None
    try:
        cached_news = news_cache.get('data')
        if cached_news:
            for category, articles in cached_news.items():
                for art in articles:
                    if art.get('link') == url:
                        rss_summary = art.get('summary', '')
                        rss_title = art.get('title', '')
                        rss_image = art.get('image')
                        break
                if rss_summary:
                    break
    except Exception:
        pass
    
    # Extract article content
    article_data = extract_article_content(url)
    
    # If extraction failed / returned paywall message, enrich with RSS summary
    failed_keywords = ['Subscription Required', 'Article Loading Error', 'could not be loaded', 'Unable to load']
    content_failed = any(kw in article_data.get('content', '') for kw in failed_keywords)
    
    if content_failed and rss_summary:
        # Clean HTML from RSS summary to get plain text
        clean_summary = re.sub(r'<[^>]+>', '', rss_summary).strip()
        if clean_summary and len(clean_summary) > 30:
            # Prepend the RSS summary to the paywall message as a teaser
            teaser = (
                f'<div style="background:#f9f9f9; border-left: 4px solid #a7d6e8; padding: 15px 20px; '
                f'margin-bottom: 20px; border-radius: 0 8px 8px 0;">'
                f'<p style="font-style: italic; color: #444; line-height: 1.7; margin: 0;">'
                f'{clean_summary}</p></div>'
            )
            article_data['content'] = teaser + article_data['content']
        if rss_title and (article_data.get('title', '') in ['📰 Times of India Article', 'Article Loading Error', '']):
            article_data['title'] = rss_title
        if rss_image and not article_data.get('image'):
            article_data['image'] = rss_image
    
    return render_template("article.html", article=article_data, rss_categories=RSS_FEEDS.keys(), category_urls=CATEGORY_URLS)

@app.route("/clear-cache")
def clear_cache_endpoint():
    """Endpoint to clear news cache"""
    clear_cache()
    return "Cache cleared! <a href='/'>Go back to home</a>"

@app.route("/api/news")
def api_news():
    """API endpoint to get news data for related articles"""
    news_data = get_news_data()
    return jsonify(news_data)

@app.route("/category/<category_name>")
def category_news(category_name):
    news_data = get_news_data()
    
    # Filter news based on category
    filtered_news = {}
    category_mapping = {
        'business': '📊 Business',
        'finance': '💰 Finance & Economy',
        'economy': '💰 Finance & Economy',
        'world': '🌍 World News',
        'india': '🇮🇳 India News',
        'technology': '🚀 Technology',
        'tech': '🚀 Technology',
        'politics': '🌍 Politics',
        'legal': '⚖️ Legal',
        'companies': '🏢 Companies',
        'entertainment': '🎯 Entertainment',
        'sports': '🏃 Sports',
    }
    
    # Get the proper category name
    mapped_category = category_mapping.get(category_name.lower(), category_name.title())
    
    # Only show the selected category
    if mapped_category in news_data:
        filtered_news[mapped_category] = news_data[mapped_category]
    else:
        # If category not found, show all categories
        filtered_news = news_data
    
    return render_template("index.html", news_data=filtered_news, current_category=mapped_category, rss_categories=RSS_FEEDS.keys(), category_urls=CATEGORY_URLS)

if __name__ == "__main__":
  app.run(host="0.0.0.0", port=8080, debug=True)
