import base64
import re

def debug_decode(encoded_part):
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
        
        # Show raw bytes as text
        decoded_text = decoded_bytes.decode('utf-8', errors='ignore')
        print(f"Decoded text (first 200 chars): {repr(decoded_text[:200])}")
        
        # Show hex
        print(f"Hex (first 100 chars): {decoded_bytes.hex()[:100]}")
        
        # Look for http patterns in bytes
        for i, byte in enumerate(decoded_bytes):
            if decoded_bytes[i:i+8] == b'https://':
                print(f"Found https:// at position {i}")
                rest = decoded_bytes[i:]
                print(f"Rest of bytes: {rest[:100]}")
                break
            elif decoded_bytes[i:i+7] == b'http://':
                print(f"Found http:// at position {i}")
                rest = decoded_bytes[i:]
                print(f"Rest of bytes: {rest[:100]}")
                break
        
        return None
        
    except Exception as e:
        print(f'Error: {e}')
        import traceback
        traceback.print_exc()
        return None

# Test
test_url = "CBMi3gFBVV95cUxNQmZaMXFIZHJLZzRsWjFwYjB2MWVsX3JRM2lqQkhHOVNWZWJuWmpaelNWLXF0ekFCd1FzSllTQ1VJeEpXM1F3QnZSeHpmNk96YW94eHVVVnBDWjhCSmlOblNpQ1g0eC0wOTNwdXVjbk1VSnA2MlNWRzIzYmlTT2d2QzY5YnI0aDIxWjFmLWlGdGhwVFJ1WTF1WWl5aUk3Q0VsRUpZY3ZUdW5qbGxrbEFxRHB6YVlnbUFHU2xYMG9GR3pJX0ZNSHZmRlpOSkFnVDhGMGFLMDVXeVdWQkhGOWc"
result = debug_decode(test_url)
