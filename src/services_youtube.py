from ytmusicapi import YTMusic
import os

class YouTubeMusicService:
    def __init__(self, headers_file='headers_auth.json'):
        """Initialize YouTube Music service with browser headers"""
        
        self.headers_file = headers_file
        self.ytmusic = None
        self.authenticate()
    
    def authenticate(self):
        """Authenticate using browser headers from ytmusicapi"""
        
        if not os.path.exists(self.headers_file):
            self._show_setup_instructions()
            raise FileNotFoundError(f"{self.headers_file} not found")
        
        print(f"📂 Loading YouTube Music credentials from {self.headers_file}...")
        
        try:
            self.ytmusic = YTMusic(self.headers_file)
            print("✅ YouTube Music authenticated successfully!")
        except Exception as e:
            print(f"❌ Authentication failed: {e}")
            print("💡 Headers may be corrupted. Try running setup again.")
            self._show_setup_instructions()
            raise
    
    def _show_setup_instructions(self):
        """Display setup instructions"""
        print("\n" + "="*70)
        print("YouTube Music Authentication Setup")
        print("="*70)
        print("\n📋 Run this command:\n")
        print("   ytmusicapi browser --file headers_auth.json\n")
        print("Then follow the prompts:")
        print("  1. Open https://music.youtube.com in Chrome/Firefox")
        print("  2. Log in to your Google account")
        print("  3. Press F12 to open Developer Tools")
        print("  4. Go to 'Network' tab")
        print("  5. Refresh the page or click a playlist")
        print("  6. Click on any request to 'music.youtube.com'")
        print("  7. Right-click on the request → Copy → Copy as cURL")
        print("  8. Paste into the terminal")
        print("  9. Press Ctrl+Z then Enter (Windows PowerShell)")
        print("\n✅ This creates headers_auth.json (valid for weeks/months)")
        print("="*70 + "\n")
    
    def _check_auth_and_handle_expiry(self):
        """Check if authentication is still valid"""
        try:
            # Test with a lightweight request
            self.ytmusic.get_library_playlists(limit=1)
            return True
        except Exception as e:
            error_str = str(e).lower()
            if any(code in error_str for code in ['401', '403', '400', 'unauthorized', 'forbidden']):
                print("\n" + "="*70)
                print("⚠️ Authentication Expired")
                print("="*70)
                print("\n💡 Your browser headers have expired.")
                print("   This typically happens every few weeks/months.")
                print("\n📋 To refresh, run:\n")
                print("   ytmusicapi browser --file headers_auth.json\n")
                print("And follow the same steps as initial setup.")
                print("="*70 + "\n")
                return False
            else:
                # Some other error, re-raise
                raise
    
    def get_user_playlists(self):
        """Fetch user's playlists from YouTube Music"""
        if not self._check_auth_and_handle_expiry():
            return []
        
        try:
            playlists = self.ytmusic.get_library_playlists(limit=None)
            print(f"✅ Retrieved {len(playlists)} playlists from YouTube Music")
            return playlists
        except Exception as e:
            print(f"❌ Error fetching playlists: {e}")
            return []
    
    def get_playlist_tracks(self, playlist_id):
        """Get all tracks from a specific playlist"""
        if not self._check_auth_and_handle_expiry():
            return []
        
        try:
            playlist = self.ytmusic.get_playlist(playlist_id, limit=None)
            tracks = playlist.get('tracks', [])
            print(f"✅ Retrieved {len(tracks)} tracks from playlist")
            
            formatted_tracks = []
            for track in tracks:
                formatted_track = {
                    'title': track.get('title', ''),
                    'artists': ', '.join([artist['name'] for artist in track.get('artists', [])]),
                    'album': track.get('album', {}).get('name', '') if track.get('album') else '',
                    'duration': track.get('duration', ''),
                    'videoId': track.get('videoId', '')
                }
                formatted_tracks.append(formatted_track)
            
            return formatted_tracks
        except Exception as e:
            print(f"❌ Error fetching playlist tracks: {e}")
            return []
    
    def search_song(self, title, artist):
        """Search for a song on YouTube Music"""
        if not self._check_auth_and_handle_expiry():
            return None
        
        try:
            query = f"{title} {artist}"
            results = self.ytmusic.search(query, filter="songs", limit=5)
            
            if results:
                top_result = results[0]
                print(f"✅ Found: {top_result['title']} - {top_result['artists'][0]['name']}")
                return {
                    'title': top_result.get('title', ''),
                    'artists': ', '.join([artist['name'] for artist in top_result.get('artists', [])]),
                    'album': top_result.get('album', {}).get('name', '') if top_result.get('album') else '',
                    'duration': top_result.get('duration', ''),
                    'videoId': top_result.get('videoId', '')
                }
            else:
                print(f"❌ No results found for: {query}")
                return None
        except Exception as e:
            print(f"❌ Error searching song: {e}")
            return None
    
    def create_playlist(self, name, description=""):
        """Create a new playlist"""
        if not self._check_auth_and_handle_expiry():
            return None
        
        try:
            playlist_id = self.ytmusic.create_playlist(name, description)
            print(f"✅ Created playlist: {name} (ID: {playlist_id})")
            return playlist_id
        except Exception as e:
            print(f"❌ Error creating playlist: {e}")
            return None
    
    def add_songs_to_playlist(self, playlist_id, video_ids):
        """Add songs to a playlist"""
        if not self._check_auth_and_handle_expiry():
            return None
        
        try:
            result = self.ytmusic.add_playlist_items(playlist_id, video_ids)
            print(f"✅ Added {len(video_ids)} songs to playlist")
            return result
        except Exception as e:
            print(f"❌ Error adding songs to playlist: {e}")
            return None


# Test the service
if __name__ == "__main__":
    print("\n" + "="*50)
    print("Testing YouTube Music Service")
    print("="*50 + "\n")
    
    try:
        ytm = YouTubeMusicService()
        
        print("\n[1/3] Fetching user playlists...")
        playlists = ytm.get_user_playlists()
        if playlists:
            for i, playlist in enumerate(playlists[:3], 1):
                print(f"  {i}. {playlist.get('title', 'Untitled')} ({playlist.get('count', 0)} tracks)")
        
        if playlists:
            print(f"\n[2/3] Fetching tracks from '{playlists[0].get('title')}'...")
            tracks = ytm.get_playlist_tracks(playlists[0]['playlistId'])
            for i, track in enumerate(tracks[:3], 1):
                print(f"  {i}. {track['title']} - {track['artists']} [{track['duration']}]")
        
        print("\n[3/3] Testing song search (Bohemian Rhapsody by Queen)...")
        result = ytm.search_song("Bohemian Rhapsody", "Queen")
        if result:
            print(f"  Album: {result['album']}")
            print(f"  Duration: {result['duration']}")
            print(f"  Video ID: {result['videoId']}")
        
        print("\n" + "="*50)
        print("✅ All tests complete!")
        print("="*50)
        
    except FileNotFoundError:
        print("⚠️  Setup required before testing.")
    except Exception as e:
        print(f"\n❌ Test failed: {e}")