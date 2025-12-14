from ytmusicapi import YTMusic
import json
import tempfile
import os

try:
    print("Testing with youtube_auth.json...")
    
    # Read the auth file
    with open('youtube_auth.json', 'r') as f:
        auth_data = json.load(f)
    
    # Get the account index (X-Goog-AuthUser)
    account_index = auth_data.get('x-goog-authuser', '0')
    print(f"Using account index: {account_index}")
    
    # Fix cookie format - ensure proper spacing between cookie values
    cookie_str = auth_data.get('cookie', '')
    # Fix missing spaces after semicolons (e.g., ";LOGIN_INFO" -> "; LOGIN_INFO")
    import re
    cookie_str = re.sub(r';(?=\w)', '; ', cookie_str)
    
    # Transform keys to match ytmusicapi's expected format for headers file
    # Note: ytmusicapi detects browser auth by checking for "SAPISIDHASH" in authorization header
    # We add a dummy authorization header to trigger browser auth detection
    # ytmusicapi will regenerate the proper authorization from the Cookie
    headers = {
        'Cookie': cookie_str,
        'User-Agent': auth_data.get('user-agent', ''),
        'X-Goog-AuthUser': account_index,
        'authorization': 'SAPISIDHASH',  # Dummy value to trigger browser auth detection
        'origin': 'https://music.youtube.com',  # Required for proper API calls
        'x-origin': 'https://music.youtube.com'  # Alternative origin header
    }
    
    # Create a temporary file with properly formatted headers
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as tmp_file:
        json.dump(headers, tmp_file, indent=2)
        tmp_file_path = tmp_file.name
    
    try:
        # Initialize YTMusic with the file path
        ytmusic = YTMusic(auth=tmp_file_path)
        
        print("Authentication successful!")
        print(f"Auth type: {ytmusic.auth_type}")
        
        # Verify SAPISID extraction
        if hasattr(ytmusic, 'sapisid') and ytmusic.sapisid:
            print(f"SAPISID extracted successfully: {ytmusic.sapisid[:20]}...")
        else:
            print("WARNING: SAPISID not extracted - authorization may not work!")
        
        # First, test authentication with a simple API call
        print("\nTesting authentication with a search query...")
        try:
            search_results = ytmusic.search("test", limit=1)
            print(f"Search test successful! Found {len(search_results)} results.")
        except Exception as e:
            print(f"Search test failed: {e}")
            print("This suggests authentication may not be working properly.")
        
        # Try get_library_playlists (returns playlists in user's library)
        print("\nAttempting to get library playlists...")
        playlists = []
        try:
            # Try with different limits - start with None to get all
            playlists = ytmusic.get_library_playlists(limit=None)
            print(f"get_library_playlists(limit=None) returned {len(playlists)} playlists")
            
            if not playlists:
                # Try with a larger limit
                playlists = ytmusic.get_library_playlists(limit=100)
                print(f"get_library_playlists(limit=100) returned {len(playlists)} playlists")
        except Exception as e:
            print(f"get_library_playlists() error: {e}")
            import traceback
            traceback.print_exc()
        
        # If no playlists found, the cookie might not have library access
        # This is common - the cookie needs to be extracted while actively using YouTube Music
        if not playlists:
            print("\nWARNING: No playlists found. This usually means:")
            print("1. The cookie was extracted when not actively using YouTube Music")
            print("2. The cookie is expired or missing required tokens")
            print("3. You need to extract a fresh cookie from an active YouTube Music session")
            print("\nTo fix this:")
            print("- Open YouTube Music in your browser (music.youtube.com)")
            print("- Make sure you're logged in and can see your playlists")
            print("- Open Developer Tools (F12) > Network tab")
            print("- Refresh the page or navigate to your library")
            print("- Find any request to music.youtube.com")
            print("- Copy ALL headers (Cookie, User-Agent, X-Goog-AuthUser, etc.)")
            print("- Update youtube_auth.json with the fresh headers")
        
        # Display results
        if playlists:
            print(f"\nSUCCESS! Found {len(playlists)} playlists:\n")
            for i, p in enumerate(playlists, 1):
                title = p.get('title', 'Unknown')
                playlist_id = p.get('playlistId', 'N/A')
                count = p.get('count', 'N/A')
                print(f"  {i}. {title} (ID: {playlist_id}, Tracks: {count})")
        else:
            # Try different account indices as a last resort
            if account_index == '0':
                print(f"\nTrying other account indices (1, 2, 3)...")
                for idx in ['1', '2', '3']:
                    try:
                        headers['X-Goog-AuthUser'] = idx
                        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as tmp_file2:
                            json.dump(headers, tmp_file2, indent=2)
                            tmp_file_path2 = tmp_file2.name
                        ytmusic2 = YTMusic(auth=tmp_file_path2)
                        playlists2 = ytmusic2.get_library_playlists(limit=100)
                        if playlists2:
                            print(f"\nSUCCESS! Found {len(playlists2)} playlists with account index {idx}!")
                            for i, p in enumerate(playlists2, 1):
                                print(f"  {i}. {p.get('title', 'Unknown')} (ID: {p.get('playlistId', 'N/A')})")
                            os.unlink(tmp_file_path2)
                            break
                        os.unlink(tmp_file_path2)
                    except Exception as e3:
                        print(f"  Account index {idx}: {type(e3).__name__} - {str(e3)[:100]}")
    finally:
        # Clean up temporary file
        if os.path.exists(tmp_file_path):
            os.unlink(tmp_file_path)
        
except FileNotFoundError:
    print("Error: youtube_auth.json file not found")
except json.JSONDecodeError as e:
    print(f"Error: Invalid JSON in youtube_auth.json: {e}")
except Exception as e:
    print(f"\nERROR: {e}")
    print(f"Error type: {type(e).__name__}")
    import traceback
    print("\nFull traceback:")
    traceback.print_exc()