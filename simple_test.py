import base64
import re

def decode_google_news_url(encoded_part):
    try:
        print(f"Testing with: {encoded_part[:50]}...")
        
        # Clean the encoded part
        clean_encoded = encoded_part.split('?')[0].split('&')[0]
        
        # Ensure correct padding
        padding_needed = (4 - len(clean_encoded) % 4) % 4
        padded = clean_encoded + '=' * padding_needed
        
        print(f"Length after padding: {len(padded)}")
        
        decoded_bytes = base64.urlsafe_b64decode(padded)
        print(f"Decoded {len(decoded_bytes)} bytes")
        
        # Look for URLs
        decoded_text = decoded_bytes.decode('utf-8', errors='ignore')
        url_patterns = re.findall(r'https?://[^\s<>"\'\]\)}]+', decoded_text)
        
        if url_patterns:
            for url in url_patterns:
                if len(url) > 20 and '.' in url:
                    print(f'Found URL: {url}')
                    return url
        
        print('No URL found')
        return None
        
    except Exception as e:
        print(f'Error: {e}')
        return None

# Test
test_url = "CBMi3gFBVV95cUxNQmZaMXFIZHJLZzRsWjFwYjB2MWVsX3JRM2lqQkhHOVNWZWJuWmpaelNWLXF0ekFCd1FzSllTQ1VJeEpXM1F3QnZSeHpmNk96YW94eHVVVnBDWjhCSmlOblNpQ1g0eC0wOTNwdXVjbk1VSnA2MlNWRzIzYmlTT2d2QzY5YnI0aDIxWjFmLWlGdGhwVFJ1WTF1WWl5aUk3Q0VsRUpZY3ZUdW5qbGxrbEFxRHB6YVlnbUFHU2xYMG9GR3pJX0ZNSHZmRlpOSkFnVDhGMGFLMDVXeVdWQkhGOWc"
result = decode_google_news_url(test_url)
print(f"Final result: {result}")
