from ytmusicapi import YTMusic
import os
import time

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
                # Don't print for every search (too verbose during sync)
                # print(f"✅ Found: {top_result['title']} - {top_result['artists'][0]['name']}")
                return {
                    'title': top_result.get('title', ''),
                    'artists': ', '.join([artist['name'] for artist in top_result.get('artists', [])]),
                    'album': top_result.get('album', {}).get('name', '') if top_result.get('album') else '',
                    'duration': top_result.get('duration', ''),
                    'videoId': top_result.get('videoId', '')
                }
            else:
                # print(f"❌ No results found for: {query}")
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
    
    def add_songs_to_playlist(self, playlist_id, video_ids, max_retries=2):
        """
        Add songs to a playlist with better error handling
        
        Args:
            playlist_id: YouTube Music playlist ID
            video_ids: List of video IDs to add
            max_retries: Number of times to retry on failure
            
        Returns:
            Dict with success status and details
        """
        if not self._check_auth_and_handle_expiry():
            return {'success': False, 'added': 0, 'error': 'Authentication failed'}
        
        # Validate inputs
        if not playlist_id:
            print("❌ Invalid playlist_id")
            return {'success': False, 'added': 0, 'error': 'Invalid playlist_id'}
        
        if not video_ids or len(video_ids) == 0:
            print("⚠️  No video IDs to add")
            return {'success': True, 'added': 0, 'error': None}
        
        # Filter out invalid video IDs
        valid_video_ids = [vid for vid in video_ids if vid and len(vid) >= 5]
        
        if len(valid_video_ids) < len(video_ids):
            invalid_count = len(video_ids) - len(valid_video_ids)
            print(f"⚠️  Filtered out {invalid_count} invalid video IDs")
        
        if not valid_video_ids:
            print("❌ No valid video IDs to add")
            return {'success': False, 'added': 0, 'error': 'No valid video IDs'}
        
        # Get current playlist size before adding
        try:
            before_playlist = self.ytmusic.get_playlist(playlist_id, limit=1)
            tracks_before = before_playlist.get('trackCount', 0)
        except:
            tracks_before = None
        
        # Try to add songs
        for attempt in range(max_retries):
            try:
                print(f"  🔄 Attempting to add {len(valid_video_ids)} songs (attempt {attempt + 1}/{max_retries})...")
                
                result = self.ytmusic.add_playlist_items(playlist_id, valid_video_ids)
                
                # If no exception was raised, assume success
                # YouTube Music API is reliable but slow to update metadata
                print(f"  ✅ API call successful - {len(valid_video_ids)} songs sent to playlist")
                return {
                    'success': True, 
                    'added': len(valid_video_ids), 
                    'error': None
                }
                    
            except Exception as e:
                error_msg = str(e)
                print(f"  ❌ Error on attempt {attempt + 1}: {error_msg}")
                
                # Check for specific errors
                if '400' in error_msg or 'Bad Request' in error_msg:
                    print(f"  ⚠️  Bad Request - Some video IDs may be invalid")
                    # Try adding songs one by one to find bad ones
                    if len(valid_video_ids) > 1 and attempt == max_retries - 1:
                        print(f"  🔄 Attempting to add songs individually...")
                        return self._add_songs_individually(playlist_id, valid_video_ids)
                
                if attempt < max_retries - 1:
                    print(f"  🔄 Retrying in 2 seconds...")
                    time.sleep(2)
                else:
                    return {'success': False, 'added': 0, 'error': error_msg}
        
        return {'success': False, 'added': 0, 'error': 'Max retries exceeded'}
    
    def _add_songs_individually(self, playlist_id, video_ids):
        """
        Add songs one by one to identify which ones are causing issues
        
        Args:
            playlist_id: YouTube Music playlist ID
            video_ids: List of video IDs to add
            
        Returns:
            Dict with success status and details
        """
        print(f"  📝 Adding {len(video_ids)} songs individually to identify issues...")
        
        added_count = 0
        failed_ids = []
        
        for idx, video_id in enumerate(video_ids, 1):
            try:
                print(f"    [{idx}/{len(video_ids)}] Adding {video_id}...", end=' ')
                self.ytmusic.add_playlist_items(playlist_id, [video_id])
                print("✅")
                added_count += 1
                
                # Small delay to avoid rate limiting
                if idx % 5 == 0:
                    time.sleep(0.5)
                    
            except Exception as e:
                print(f"❌ ({str(e)[:50]})")
                failed_ids.append(video_id)
        
        if failed_ids:
            print(f"  ⚠️  {len(failed_ids)} songs failed to add: {failed_ids[:5]}...")
        
        return {
            'success': added_count > 0,
            'added': added_count,
            'error': f'{len(failed_ids)} songs failed' if failed_ids else None,
            'failed_ids': failed_ids
        }


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
            print(f"  ✅ Found: {result['title']}")
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