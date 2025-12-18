"""
Quick test script for Spotify service
"""

import signal
import sys
from src.config import config, Config
from src.services_spotify import SpotifyService

# Handle Ctrl+C gracefully
def signal_handler(sig, frame):
    print("\n\n⚠ Interrupted by user (Ctrl+C)")
    print("Exiting gracefully...")
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)

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
    
    # Diagnostic output (safe - doesn't expose full secrets)
    print("\n" + "=" * 60)
    print("CONFIGURATION DIAGNOSTICS")
    print("=" * 60)
    print(f"Client ID (first 10 chars): {config.SPOTIFY_CLIENT_ID[:10] if config.SPOTIFY_CLIENT_ID else 'None'}...")
    print(f"Client ID length: {len(config.SPOTIFY_CLIENT_ID) if config.SPOTIFY_CLIENT_ID else 0}")
    print(f"Client Secret length: {len(config.SPOTIFY_CLIENT_SECRET) if config.SPOTIFY_CLIENT_SECRET else 0}")
    print(f"Redirect URI: {config.SPOTIFY_REDIRECT_URI}")
    print("=" * 60 + "\n")
    
    # Check for common issues
    if config.SPOTIFY_CLIENT_ID and (config.SPOTIFY_CLIENT_ID.startswith('"') or config.SPOTIFY_CLIENT_ID.startswith("'")):
        print("⚠ WARNING: Client ID appears to have quotes. Remove quotes from .env file!")
    if config.SPOTIFY_CLIENT_SECRET and (config.SPOTIFY_CLIENT_SECRET.startswith('"') or config.SPOTIFY_CLIENT_SECRET.startswith("'")):
        print("⚠ WARNING: Client Secret appears to have quotes. Remove quotes from .env file!")
    if config.SPOTIFY_CLIENT_ID and config.SPOTIFY_CLIENT_ID != config.SPOTIFY_CLIENT_ID.strip():
        print("⚠ WARNING: Client ID has leading/trailing whitespace!")
    if config.SPOTIFY_CLIENT_SECRET and config.SPOTIFY_CLIENT_SECRET != config.SPOTIFY_CLIENT_SECRET.strip():
        print("⚠ WARNING: Client Secret has leading/trailing whitespace!")
    
    # Initialize Spotify service
    try:
        spotify = SpotifyService(
            client_id=config.SPOTIFY_CLIENT_ID,
            client_secret=config.SPOTIFY_CLIENT_SECRET,
            redirect_uri=config.SPOTIFY_REDIRECT_URI
        )
    except ValueError as e:
        print(f"✗ Service initialization failed: {e}")
        return
    
    # Authenticate (will open browser for OAuth)
    print("\nAuthenticating with Spotify...")
    print("Note: If this is your first time, a browser window may open for authorization.")
    print("If you see an 'invalid client' error in the browser, check the diagnostics above.\n")
    
    try:
        if not spotify.authenticate():
            print("\n✗ Authentication failed!")
            print("\nTroubleshooting steps:")
            print("1. Verify SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET in .env file")
            print("2. Ensure redirect URI matches exactly in Spotify Dashboard:")
            print(f"   {config.SPOTIFY_REDIRECT_URI}")
            print("3. Check that credentials don't have quotes or extra whitespace")
            print("4. Visit https://developer.spotify.com/dashboard to verify your app settings")
            return
    except KeyboardInterrupt:
        print("\n\n⚠ Authentication interrupted by user")
        print("Exiting...")
        return
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        print("Please check the error messages above for details.")
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