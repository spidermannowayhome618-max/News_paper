import base64
import re

def decode_google_news_url(encoded_part):
    """Improved Google News URL decoder"""
    try:
        print(f"Testing with: {encoded_part[:50]}...")
        
        clean_encoded = encoded_part.split('?')[0].split('&')[0]
        padding_needed = (4 - len(clean_encoded) % 4) % 4
        padded = clean_encoded + '=' * padding_needed
        
        decoded_bytes = base64.urlsafe_b64decode(padded)
        print(f"Decoded {len(decoded_bytes)} bytes")
        
        # Method 1: Direct pattern matching
        decoded_text = decoded_bytes.decode('utf-8', errors='ignore')
        url_patterns = re.findall(r'https?://[^\s<>"\'\]\)}]+', decoded_text)
        if url_patterns:
            for url in url_patterns:
                if len(url) > 20 and '.' in url:
                    print(f'Found URL via pattern matching: {url}')
                    return url
        
        # Method 2: Byte scanning for http/https
        for prefix in [b'https://', b'http://']:
            idx = decoded_bytes.find(prefix)
            if idx != -1:
                url_bytes = b''
                for j in range(idx, len(decoded_bytes)):
                    byte = decoded_bytes[j]
                    if byte == 0 or byte in [32, 10, 13, 34, 39, 60, 62]:
                        break
                    url_bytes += bytes([byte])
                
                try:
                    url_str = url_bytes.decode('utf-8', errors='ignore').strip()
                    if len(url_str) > 15 and '.' in url_str:
                        print(f'Found URL via byte scanning: {url_str}')
                        return url_str
                except:
                    pass
        
        # Method 3: Manual hex analysis
        hex_str = decoded_bytes.hex()
        print(f"Hex: {hex_str}")
        
        # Look for http in hex
        http_hex = '68747470'  # 'http' in hex
        https_hex = '6874747073'  # 'https' in hex
        
        if http_hex in hex_str:
            print(f"Found 'http' in hex at position: {hex_str.find(http_hex)}")
        if https_hex in hex_str:
            print(f"Found 'https' in hex at position: {hex_str.find(https_hex)}")
        
        return None
        
    except Exception as e:
        print(f'Error: {e}')
        return None

# Test
test_url = "CBMi3gFBVV95cUxNQmZaMXFIZHJLZzRsWjFwYjB2MWVsX3JRM2lqQkhHOVNWZWJuWmpaelNWLXF0ekFCd1FzSllTQ1VJeEpXM1F3QnZSeHpmNk96YW94eHVVVnBDWjhCSmlOblNpQ1g0eC0wOTNwdXVjbk1VSnA2MlNWRzIzYmlTT2d2QzY5YnI0aDIxWjFmLWlGdGhwVFJ1WTF1WWl5aUk3Q0VsRUpZY3ZUdW5qbGxrbEFxRHB6YVlnbUFHU2xYMG9GR3pJX0ZNSHZmRlpOSkFnVDhGMGFLMDVXeVdWQkhGOWc"
result = decode_google_news_url(test_url)
print(f"Final result: {result}")
