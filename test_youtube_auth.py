from ytmusicapi import YTMusic

try:
    print("Testing with headers_auth.json...")
    ytmusic = YTMusic('youtube_auth.json')
    
    print("✓ Authentication successful!")
    
    playlists = ytmusic.get_library_playlists(limit=5)
    print(f"\nFound {len(playlists)} playlists:\n")
    
    for p in playlists:
        print(f"  - {p['title']}")
        
except Exception as e:
    print(f"✗ Error: {e}")
    print(f"Error type: {type(e).__name__}")