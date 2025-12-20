# test_sync_basic.py
"""Quick test to verify sync engine setup"""


from src.services_spotify import SpotifyService
from src.services_youtube import YouTubeMusicService
from src.sync import SimpleSyncEngine
from src.config import Config

def test_connections():
    """Test that all services connect properly"""
    
    print("🔧 Testing Sync Engine Setup\n")
    print("=" * 60)
    
    # 1. Test Config
    print("\n[1/4] Testing config...")
    try:
        config = Config()
        print(f"  ✅ Config loaded")
        print(f"  📋 Spotify Client ID: {config.SPOTIFY_CLIENT_ID[:10]}...")
    except Exception as e:
        print(f"  ❌ Config failed: {e}")
        return
    
    # 2. Test Spotify Service
    print("\n[2/4] Testing Spotify authentication...")
    try:
        spotify = SpotifyService(
            client_id=config.SPOTIFY_CLIENT_ID,
            client_secret=config.SPOTIFY_CLIENT_SECRET,
            redirect_uri=config.SPOTIFY_REDIRECT_URI
        )
        
        if spotify.authenticate():
            print("  ✅ Spotify authenticated!")
            
            # Quick test: fetch playlists
            playlists = spotify.get_user_playlists()
            print(f"  📋 Found {len(playlists)} playlists")
        else:
            print("  ❌ Spotify authentication failed")
            return
    except Exception as e:
        print(f"  ❌ Spotify service failed: {e}")
        return
    
    # 3. Test YouTube Music Service
    print("\n[3/4] Testing YouTube Music authentication...")
    try:
        youtube = YouTubeMusicService()
        print("  ✅ YouTube Music authenticated!")
        
        # Quick test: fetch playlists
        yt_playlists = youtube.get_user_playlists()
        print(f"  📋 Found {len(yt_playlists)} playlists")
    except Exception as e:
        print(f"  ❌ YouTube Music service failed: {e}")
        return
    
    # 4. Test Sync Engine Initialization
    print("\n[4/4] Testing sync engine initialization...")
    try:
        sync_engine = SimpleSyncEngine(spotify, youtube)
        print("  ✅ Sync engine initialized!")
    except Exception as e:
        print(f"  ❌ Sync engine failed: {e}")
        return
    
    print("\n" + "=" * 60)
    print("🎉 All systems ready! You can now run a sync.")
    print("=" * 60)

if __name__ == "__main__":
    test_connections()