import base64

def analyze_hex(encoded_part):
    try:
        clean_encoded = encoded_part.split('?')[0].split('&')[0]
        padding_needed = (4 - len(clean_encoded) % 4) % 4
        padded = clean_encoded + '=' * padding_needed
        
        decoded_bytes = base64.urlsafe_b64decode(padded)
        
        # Print hex with positions
        hex_str = decoded_bytes.hex()
        print("Hex analysis:")
        for i in range(0, len(hex_str), 32):
            chunk = hex_str[i:i+32]
            print(f"{i:04d}: {chunk}")
        
        # Look for readable text
        print("\nReadable text analysis:")
        for i in range(len(decoded_bytes)):
            if 32 <= decoded_bytes[i] <= 126:  # printable ASCII
                text = ""
                for j in range(i, min(i + 50, len(decoded_bytes))):
                    if 32 <= decoded_bytes[j] <= 126:
                        text += chr(decoded_bytes[j])
                    else:
                        break
                if len(text) > 5:
                    print(f"Position {i}: {text}")
        
        # Look for http patterns in bytes
        print("\nHTTP pattern search:")
        for i in range(len(decoded_bytes) - 4):
            if decoded_bytes[i:i+4] == b'http':
                print(f"Found 'http' at position {i}")
                # Show next 50 bytes
                end = min(i + 50, len(decoded_bytes))
                snippet = decoded_bytes[i:end]
                print(f"Next bytes: {snippet}")
                try:
                    text = snippet.decode('utf-8', errors='ignore')
                    print(f"As text: {repr(text)}")
                except:
                    pass
        
        return None
        
    except Exception as e:
        print(f'Error: {e}')
        return None

# Test
test_url = "CBMi3gFBVV95cUxNQmZaMXFIZHJLZzRsWjFwYjB2MWVsX3JRM2lqQkhHOVNWZWJuWmpaelNWLXF0ekFCd1FzSllTQ1VJeEpXM1F3QnZSeHpmNk96YW94eHVVVnBDWjhCSmlOblNpQ1g0eC0wOTNwdXVjbk1VSnA2MlNWRzIzYmlTT2d2QzY5YnI0aDIxWjFmLWlGdGhwVFJ1WTF1WWl5aUk3Q0VsRUpZY3ZUdW5qbGxrbEFxRHB6YVlnbUFHU2xYMG9GR3pJX0ZNSHZmRlpOSkFnVDhGMGFLMDVXeVdWQkhGOWc"
analyze_hex(test_url)
