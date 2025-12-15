"""
Quick test script for Spotify service
"""

from src.config import config
from src.services_spotify import SpotifyService

def main():
    # Validate configuration
    try:
        config.validate()
    except ValueError as e:
        print(f"Configuration error: {e}")
        return
    
    # Initialize Spotify service
    spotify = SpotifyService(
        client_id=config.SPOTIFY_CLIENT_ID,
        client_secret=config.SPOTIFY_CLIENT_SECRET,
        redirect_uri=config.SPOTIFY_REDIRECT_URI
    )
    
    # Authenticate (will open browser for OAuth)
    print("Authenticating with Spotify...")
    if not spotify.authenticate():
        print("Authentication failed!")
        return
    
    # Test: Get playlists
    print("\n" + "="*50)
    print("YOUR PLAYLISTS")
    print("="*50)
    playlists = spotify.get_user_playlists()
    for i, pl in enumerate(playlists, 1):
        print(f"{i}. {pl['name']} - {pl['tracks_total']} tracks")
    
    # Test: Get tracks from first playlist
    if playlists:
        print("\n" + "="*50)
        print(f"TRACKS IN '{playlists[0]['name']}'")
        print("="*50)
        tracks = spotify.get_playlist_tracks(playlists[0]['id'])
        for i, track in enumerate(tracks[:10], 1):  # Show first 10
            artists = ", ".join(track['artists'])
            print(f"{i}. {track['name']} - {artists}")
        
        if len(tracks) > 10:
            print(f"... and {len(tracks) - 10} more tracks")
    
    # Test: Search
    print("\n" + "="*50)
    print("SEARCH TEST: 'Shape of You' by 'Ed Sheeran'")
    print("="*50)
    results = spotify.search_track("Shape of You", "Ed Sheeran")
    for i, track in enumerate(results, 1):
        artists = ", ".join(track['artists'])
        print(f"{i}. {track['name']} - {artists} (Album: {track['album']})")

if __name__ == "__main__":
    main()