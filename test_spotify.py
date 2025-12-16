"""
Quick test script for Spotify service
"""

from src.config import config, Config
from src.services_spotify import SpotifyService

def main():
    # Validate Spotify configuration
    try:
        Config.validate_spotify()  # Changed from config.validate()
        print("✓ Spotify configuration validated")
    except ValueError as e:
        print(f"✗ Configuration error: {e}")
        print("\nPlease make sure you have:")
        print("1. Created a .env file in your project root")
        print("2. Added SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET to .env")
        print("3. Obtained these credentials from https://developer.spotify.com/dashboard")
        return
    
    # Initialize Spotify service
    spotify = SpotifyService(
        client_id=config.SPOTIFY_CLIENT_ID,
        client_secret=config.SPOTIFY_CLIENT_SECRET,
        redirect_uri=config.SPOTIFY_REDIRECT_URI
    )
    
    # Authenticate (will open browser for OAuth)
    print("\nAuthenticating with Spotify...")
    print("A browser window will open for authorization.")
    print("After authorizing, you'll be redirected to a localhost URL.")
    print("Copy that ENTIRE URL and paste it back here when prompted.\n")
    
    if not spotify.authenticate():
        print("✗ Authentication failed!")
        return
    
    print("✓ Authentication successful!\n")
    
    # Test: Get playlists
    print("=" * 60)
    print("YOUR PLAYLISTS")
    print("=" * 60)
    playlists = spotify.get_user_playlists()
    
    if not playlists:
        print("No playlists found or failed to fetch playlists.")
        return
    
    for i, pl in enumerate(playlists, 1):
        owner_info = f" (by {pl['owner']})" if pl['owner'] else ""
        public_info = "Public" if pl['public'] else "Private"
        print(f"{i}. {pl['name']}{owner_info}")
        print(f"   {pl['tracks_total']} tracks | {public_info}")
    
    # Test: Get tracks from first playlist
    if playlists:
        print("\n" + "=" * 60)
        print(f"TRACKS IN '{playlists[0]['name']}'")
        print("=" * 60)
        tracks = spotify.get_playlist_tracks(playlists[0]['id'])
        
        if tracks:
            for i, track in enumerate(tracks[:10], 1):  # Show first 10
                artists = ", ".join(track['artists'])
                duration_min = track['duration_ms'] // 60000
                duration_sec = (track['duration_ms'] % 60000) // 1000
                print(f"{i}. {track['name']}")
                print(f"   by {artists} | {duration_min}:{duration_sec:02d}")
            
            if len(tracks) > 10:
                print(f"\n... and {len(tracks) - 10} more tracks")
        else:
            print("No tracks found in this playlist.")
    
    # Test: Search
    print("\n" + "=" * 60)
    print("SEARCH TEST: 'Shape of You' by 'Ed Sheeran'")
    print("=" * 60)
    results = spotify.search_track("Shape of You", "Ed Sheeran")
    
    if results:
        for i, track in enumerate(results, 1):
            artists = ", ".join(track['artists'])
            print(f"{i}. {track['name']}")
            print(f"   by {artists}")
            print(f"   Album: {track['album']}")
    else:
        print("No results found.")
    
    print("\n" + "=" * 60)
    print("TEST COMPLETED SUCCESSFULLY!")
    print("=" * 60)

if __name__ == "__main__":
    main()