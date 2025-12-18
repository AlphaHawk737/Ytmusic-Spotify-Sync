"""
Simple script to update YouTube Music browser headers
Run this when you get authentication errors
"""

def update_headers():
    print("\n" + "="*70)
    print("YouTube Music Headers Update Guide")
    print("="*70 + "\n")
    
    print("📋 INSTRUCTIONS:\n")
    print("1. Open Chrome/Firefox and go to: https://music.youtube.com")
    print("2. Open Developer Tools (F12)")
    print("3. Go to 'Network' tab")
    print("4. Click on any request to 'music.youtube.com'")
    print("5. Find 'Request Headers' section")
    print("6. Copy ALL headers")
    print("7. Paste them below and press Enter twice:\n")
    
    print("="*70)
    print("Paste headers here (press Enter twice when done):")
    print("="*70 + "\n")
    
    headers = []
    while True:
        line = input()
        if line == "":
            if headers and headers[-1] == "":
                break
            headers.append(line)
        else:
            headers.append(line)
    
    # Remove last empty line
    if headers and headers[-1] == "":
        headers.pop()
    
    headers_text = "\n".join(headers)
    
    # Save to file
    with open('youtube_headers_raw.txt', 'w') as f:
        f.write(headers_text)
    
    print("\n✅ Headers saved to youtube_headers_raw.txt")
    print("\nNow run: ytmusicapi browser")
    print("When prompted for headers file, enter: youtube_headers_raw.txt\n")
    print("="*70)

if __name__ == "__main__":
    update_headers()