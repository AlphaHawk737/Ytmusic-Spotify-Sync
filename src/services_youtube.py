from ytmusicapi import YTMusic
import os

class YouTubeMusicService:
    def __init__(self, headers_file='headers_auth.json'):
        """Initialize YouTube Music service with browser headers"""
        
        if not os.path.exists(headers_file):
            print(f"\n❌ {headers_file} not found!")
            print("\n📋 To set up authentication:")
            print("1. Run: ytmusicapi browser")
            print("2. Follow the instructions to copy browser headers")
            print("3. This will create headers_auth.json")
            print("\nOr use the helper: python update_youtube_headers.py\n")
            raise FileNotFoundError(f"{headers_file} not found")
        
        print(f"📂 Loading YouTube Music credentials from {headers_file}...")
        
        try:
            self.ytmusic = YTMusic(headers_file)
            print("✅ YouTube Music authenticated successfully!")
        except Exception as e:
            print(f"❌ Authentication failed: {e}")
            print("\n💡 Headers may have expired. Run: ytmusicapi browser")
            raise
    
    def get_user_playlists(self):
        """Fetch user's playlists from YouTube Music"""
        try:
            playlists = self.ytmusic.get_library_playlists(limit=None)
            print(f"✅ Retrieved {len(playlists)} playlists from YouTube Music")
            return playlists
        except Exception as e:
            if "401" in str(e) or "400" in str(e):
                print(f"\n❌ Authentication error: {e}")
                print("💡 Your headers have expired. Please update them:")
                print("   Run: ytmusicapi browser\n")
            else:
                print(f"❌ Error fetching playlists: {e}")
            return []
    
    def get_playlist_tracks(self, playlist_id):
        """Get all tracks from a specific playlist"""
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
            if "401" in str(e) or "400" in str(e):
                print(f"\n❌ Authentication error: {e}")
                print("💡 Your headers have expired. Run: ytmusicapi browser\n")
            else:
                print(f"❌ Error fetching playlist tracks: {e}")
            return []
    
    def search_song(self, title, artist):
        """Search for a song on YouTube Music"""
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
            if "401" in str(e) or "400" in str(e):
                print(f"\n❌ Authentication error: {e}")
                print("💡 Your headers have expired. Run: ytmusicapi browser\n")
            else:
                print(f"❌ Error searching song: {e}")
            return None
    
    def create_playlist(self, name, description=""):
        """Create a new playlist"""
        try:
            playlist_id = self.ytmusic.create_playlist(name, description)
            print(f"✅ Created playlist: {name} (ID: {playlist_id})")
            return playlist_id
        except Exception as e:
            print(f"❌ Error creating playlist: {e}")
            return None
    
    def add_songs_to_playlist(self, playlist_id, video_ids):
        """Add songs to a playlist"""
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
        print("\n💡 Set up authentication first using one of these methods:")
        print("   • Simple: ytmusicapi browser")
        print("   • With helper: python update_youtube_headers.py")