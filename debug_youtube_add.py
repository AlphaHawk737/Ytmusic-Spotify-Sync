# debug_youtube_add.py
"""Debug YouTube Music song addition issues"""

from src.services_youtube import YouTubeMusicService
from src.services_spotify import SpotifyService
from src.config import Config

def debug_add_songs():
    """Test adding songs one by one with detailed output"""
    
    print("🔍 YouTube Music Add Debug Tool\n")
    print("="*70)
    
    # Initialize services
    config = Config()
    spotify = SpotifyService(
        client_id=config.SPOTIFY_CLIENT_ID,
        client_secret=config.SPOTIFY_CLIENT_SECRET,
        redirect_uri=config.SPOTIFY_REDIRECT_URI
    )
    
    if not spotify.authenticate():
        print("❌ Spotify auth failed")
        return
    
    youtube = YouTubeMusicService()
    
    # Get a test playlist
    print("\n📋 Your Spotify Playlists:")
    playlists = spotify.get_user_playlists()
    
    for idx, pl in enumerate(playlists[:10], 1):
        print(f"{idx}. {pl['name']} ({pl['tracks_total']} tracks)")
    
    choice = int(input("\nSelect playlist to test (1-10): ")) - 1
    selected = playlists[choice]
    
    print(f"\n🎵 Selected: {selected['name']}")
    
    # Get first 5 tracks
    tracks = spotify.get_playlist_tracks(selected['id'])[:5]
    
    print(f"\n🔍 Testing first 5 tracks from playlist:")
    print("="*70)
    
    # Create test playlist
    test_playlist_id = youtube.create_playlist(
        name="DEBUG TEST - DELETE ME",
        description="Debugging playlist - safe to delete"
    )
    
    if not test_playlist_id:
        print("❌ Failed to create test playlist")
        return
    
    print(f"\n✅ Created test playlist: {test_playlist_id}")
    print("\n" + "="*70)
    print("Testing Individual Song Additions")
    print("="*70 + "\n")
    
    for idx, track in enumerate(tracks, 1):
        track_name = track['name']
        artists = ', '.join(track['artists'])
        
        print(f"\n[{idx}/5] {track_name} - {artists}")
        print("-" * 70)
        
        # Search on YouTube
        print("  🔍 Searching YouTube Music...")
        yt_result = youtube.search_song(track_name, artists)
        
        if not yt_result:
            print("  ❌ Not found on YouTube Music")
            continue
        
        video_id = yt_result.get('videoId')
        print(f"  ✅ Found: {yt_result['title']}")
        print(f"  📺 Video ID: {video_id}")
        
        # Try to add
        print(f"  📤 Attempting to add to playlist...")
        result = youtube.add_songs_to_playlist(test_playlist_id, [video_id])
        
        if result and result['success'] and result['added'] > 0:
            print(f"  ✅ SUCCESS - Song added!")
        else:
            print(f"  ❌ FAILED - {result.get('error', 'Unknown error')}")
            print(f"  ⚠️  This video ID cannot be added to playlists")
        
        # Small delay
        import time
        time.sleep(1)
    
    print("\n" + "="*70)
    print("🏁 Debug Complete")
    print("="*70)
    print(f"\n💡 Check YouTube Music playlist: {test_playlist_id}")
    print("   Delete it when done debugging.\n")

if __name__ == "__main__":
    debug_add_songs()