#!/usr/bin/env python3
"""
Test script to verify Google News URL decoding fix
"""
import base64
import re

def decode_google_news_url(encoded_part):
    """Decode a CBMi/0gG-style Google News encoded URL using URL-safe base64."""
    try:
        print(f"Attempting to decode Google News URL part: {encoded_part[:50]}...")
        
        # Clean the encoded part - remove any URL parameters or extra characters
        clean_encoded = encoded_part.split('?')[0].split('&')[0]
        
        # Ensure correct padding (base64 length must be multiple of 4)
        padding_needed = (4 - len(clean_encoded) % 4) % 4
        padded = clean_encoded + '=' * padding_needed
        
        print(f"Padded encoded length: {len(padded)}")
        
        decoded_bytes = base64.urlsafe_b64decode(padded)
        print(f"Decoded bytes length: {len(decoded_bytes)}")
        
        # Convert to hex for debugging
        hex_str = decoded_bytes.hex()
        print(f"First 100 hex chars: {hex_str[:100]}")
        
        # Scan decoded bytes for an embedded HTTP URL
        for prefix in [b'https://', b'http://']:
            idx = decoded_bytes.find(prefix)
            if idx != -1:
                # Extract URL from the found position to the next null byte or end
                raw = decoded_bytes[idx:].split(b'\x00')[0]
                url_str = raw.decode('ascii', errors='ignore').strip()
                
                # Clean up the URL - remove trailing non-URL characters
                url_str = re.split(r'[\s<>"\'\]\)}]', url_str)[0]
                
                # Additional cleaning for common patterns
                url_str = re.sub(r'[^a-zA-Z0-9\-._~:/?#[\]@!$&\'()*+,;=%]', '', url_str)
                
                if url_str and len(url_str) > 15 and ('.' in url_str):
                    print(f'Successfully decoded Google News URL: {url_str}')
                    return url_str
        
        # If standard method fails, try alternative approach
        # Look for URL patterns in the raw bytes
        decoded_text = decoded_bytes.decode('utf-8', errors='ignore')
        url_patterns = re.findall(r'https?://[^\s<>"\'\]\)}]+', decoded_text)
        if url_patterns:
            for url in url_patterns:
                if len(url) > 20 and '.' in url:
                    print(f'Found URL via pattern matching: {url}')
                    return url
        
        print(f'Could not extract URL from decoded bytes')
        return None
        
    except Exception as e:
        print(f'decode_google_news_url error: {e}')
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    # Test with the problematic URL from the user's issue
    test_url = "CBMi3gFBVV95cUxNQmZaMXFIZHJLZzRsWjFwYjB2MWVsX3JRM2lqQkhHOVNWZWJuWmpaelNWLXF0ekFCd1FzSllTQ1VJeEpXM1F3QnZSeHpmNk96YW94eHVVVnBDWjhCSmlOblNpQ1g0eC0wOTNwdXVjbk1VSnA2MlNWRzIzYmlTT2d2QzY5YnI0aDIxWjFmLWlGdGhwVFJ1WTF1WWl5aUk3Q0VsRUpZY3ZUdW5qbGxrbEFxRHB6YVlnbUFHU2xYMG9GR3pJX0ZNSHZmRlpOSkFnVDhGMGFLMDVXeVdWQkhGOWc"
    
    print("Testing Google News URL decoding...")
    print("=" * 50)
    
    result = decode_google_news_url(test_url)
    
    print("=" * 50)
    if result:
        print(f"✅ SUCCESS: Decoded URL: {result}")
    else:
        print("❌ FAILED: Could not decode URL")
