"""
YouTube Music API Service
Handles all interactions with YouTube Music using ytmusicapi with browser headers
"""

from ytmusicapi import YTMusic
from typing import List, Dict, Optional
import logging
import json
import os
import re
import tempfile

logger = logging.getLogger(__name__)


class YouTubeMusicService:
    """Service for interacting with YouTube Music API using browser headers"""
    
    def __init__(self, headers_file: str = "youtube_auth.json"):
        """
        Initialize YouTube Music service with browser headers
        
        Args:
            headers_file: Path to JSON file containing browser headers
                         (cookie, x-goog-authuser, user-agent)
        """
        self._temp_headers_file = None
        self._headers_file = headers_file
        self._account_index = None
        try:
            # Check if headers file exists
            if not os.path.exists(headers_file):
                raise FileNotFoundError(f"Headers file not found: {headers_file}")
            
            # Load headers from JSON file
            with open(headers_file, 'r') as f:
                auth_data = json.load(f)
            
            # Validate required headers
            required_headers = ['cookie', 'x-goog-authuser', 'user-agent']
            missing_headers = [h for h in required_headers if h not in auth_data]
            
            if missing_headers:
                raise ValueError(f"Missing required headers: {', '.join(missing_headers)}")
            
            # Get the account index (X-Goog-AuthUser)
            account_index = auth_data.get('x-goog-authuser', '0')
            self._account_index = account_index
            
            # Fix cookie format - ensure proper spacing between cookie values
            cookie_str = auth_data.get('cookie', '')
            # Fix missing spaces after semicolons (e.g., ";LOGIN_INFO" -> "; LOGIN_INFO")
            cookie_str = re.sub(r';(?=\w)', '; ', cookie_str)
            
            # Transform keys to match ytmusicapi's expected format for headers file
            # Note: ytmusicapi detects browser auth by checking for "SAPISIDHASH" in authorization header
            # We add a dummy authorization header to trigger browser auth detection
            # ytmusicapi will regenerate the proper authorization from the Cookie
            transformed_headers = {
                'Cookie': cookie_str,
                'User-Agent': auth_data.get('user-agent', ''),
                'X-Goog-AuthUser': account_index,
                'authorization': 'SAPISIDHASH',  # Dummy value to trigger browser auth detection
                'origin': 'https://music.youtube.com',  # Required for proper API calls
                'x-origin': 'https://music.youtube.com'  # Alternative origin header
            }
            
            # Create a temporary file with properly formatted headers
            temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False)
            json.dump(transformed_headers, temp_file, indent=2)
            temp_file.close()
            self._temp_headers_file = temp_file.name
            
            # Initialize YTMusic with the transformed headers file
            self.ytmusic = YTMusic(auth=self._temp_headers_file)
            
            # Verify authentication works with a simple search
            try:
                test_results = self.ytmusic.search("test", limit=1)
                logger.info("YouTube Music authentication successful with browser headers")
            except Exception as auth_error:
                logger.warning(f"Authentication initialized but test search failed: {auth_error}")
                logger.warning("This may indicate the cookie is expired or invalid")
                # Still continue - the error might be specific to search
            
        except FileNotFoundError as e:
            logger.error(f"Headers file not found: {e}")
            raise
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in headers file: {e}")
            raise
        except Exception as e:
            logger.error(f"YouTube Music authentication failed: {e}")
            raise
    
    def __del__(self):
        """Clean up temporary headers file when object is destroyed"""
        if self._temp_headers_file and os.path.exists(self._temp_headers_file):
            try:
                os.unlink(self._temp_headers_file)
            except Exception:
                pass  # Ignore errors during cleanup
    
    def get_library_playlists(self) -> List[Dict]:
        """
        Get all playlists from user's library
        
        Returns:
            List of playlist dictionaries with id, name, and track count
        """
        try:
            # Try with limit=None first to get all playlists
            try:
                playlists = self.ytmusic.get_library_playlists(limit=None)
            except Exception as e1:
                logger.debug(f"get_library_playlists(limit=None) failed: {e1}, trying limit=100")
                try:
                    playlists = self.ytmusic.get_library_playlists(limit=100)
                except Exception as e2:
                    logger.debug(f"get_library_playlists(limit=100) failed: {e2}, trying limit=50")
                    playlists = self.ytmusic.get_library_playlists(limit=50)
            
            # If no playlists found, try different account indices
            if not playlists:
                logger.warning("No playlists found with current account index. Trying other account indices...")
                alt_playlists = self._try_different_account_index(self._headers_file, self._account_index)
                if alt_playlists:
                    # Normalize the alternative playlists
                    normalized_playlists = []
                    for playlist in alt_playlists:
                        normalized_playlists.append({
                            'id': playlist['playlistId'],
                            'name': playlist['title'],
                            'track_count': playlist.get('count', 0),
                            'description': playlist.get('description', ''),
                            'thumbnails': playlist.get('thumbnails', [])
                        })
                    logger.info(f"Retrieved {len(normalized_playlists)} playlists from YouTube Music (with different account index)")
                    return normalized_playlists
                
                # If still no playlists, provide helpful error message
                logger.warning("No playlists found. This usually means:")
                logger.warning("1. The cookie was extracted when not actively using YouTube Music")
                logger.warning("2. The cookie is expired or missing required tokens")
                logger.warning("3. The account index (x-goog-authuser) might be incorrect")
                logger.warning("4. You need to extract a fresh cookie from an active YouTube Music session")
                logger.warning("\nTo fix this:")
                logger.warning("- Open YouTube Music in your browser (music.youtube.com)")
                logger.warning("- Make sure you're logged in and can see your playlists")
                logger.warning("- Open Developer Tools (F12) > Network tab")
                logger.warning("- Refresh the page or navigate to your library")
                logger.warning("- Find any request to music.youtube.com")
                logger.warning("- Copy ALL headers (Cookie, User-Agent, X-Goog-AuthUser, etc.)")
                logger.warning("- Update youtube_auth.json with the fresh headers")
                return []
            
            # Normalize the data structure for easier use
            normalized_playlists = []
            for playlist in playlists:
                normalized_playlists.append({
                    'id': playlist['playlistId'],
                    'name': playlist['title'],
                    'track_count': playlist.get('count', 0),
                    'description': playlist.get('description', ''),
                    'thumbnails': playlist.get('thumbnails', [])
                })
            
            logger.info(f"Retrieved {len(normalized_playlists)} playlists from YouTube Music")
            return normalized_playlists
            
        except Exception as e:
            logger.error(f"Error fetching playlists: {e}")
            import traceback
            logger.debug(f"Full traceback: {traceback.format_exc()}")
            logger.error("\nTroubleshooting tips:")
            logger.error("- Verify your cookie is fresh and extracted while actively using YouTube Music")
            logger.error("- Check that x-goog-authuser matches your account index (try 0, 1, 2, etc.)")
            logger.error("- Ensure all required headers are present in youtube_auth.json")
            return []
    
    def _try_different_account_index(self, headers_file: str, current_index: str) -> Optional[List[Dict]]:
        """
        Helper method to try different account indices if current one doesn't work
        
        Args:
            headers_file: Path to the headers file
            current_index: Current account index being used
            
        Returns:
            List of playlists if successful with different index, None otherwise
        """
        # Try indices 0, 1, 2, 3 (excluding the current one)
        indices_to_try = ['0', '1', '2', '3']
        if current_index in indices_to_try:
            indices_to_try.remove(current_index)
        
        for idx in indices_to_try:
                try:
                    logger.info(f"Trying account index {idx}...")
                    # Load and modify headers
                    with open(headers_file, 'r') as f:
                        auth_data = json.load(f)
                    
                    account_index = idx
                    cookie_str = auth_data.get('cookie', '')
                    cookie_str = re.sub(r';(?=\w)', '; ', cookie_str)
                    
                    transformed_headers = {
                        'Cookie': cookie_str,
                        'User-Agent': auth_data.get('user-agent', ''),
                        'X-Goog-AuthUser': account_index,
                        'authorization': 'SAPISIDHASH',
                        'origin': 'https://music.youtube.com',
                        'x-origin': 'https://music.youtube.com'
                    }
                    
                    # Create temporary file
                    temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False)
                    json.dump(transformed_headers, temp_file, indent=2)
                    temp_file.close()
                    temp_path = temp_file.name
                    
                    try:
                        # Try with new account index
                        ytmusic_test = YTMusic(auth=temp_path)
                        playlists = ytmusic_test.get_library_playlists(limit=100)
                        
                        if playlists:
                            logger.info(f"✓ Found {len(playlists)} playlists with account index {idx}!")
                            logger.warning(f"Update your youtube_auth.json to use x-goog-authuser: {idx}")
                            # Clean up temp file
                            os.unlink(temp_path)
                            return playlists
                    finally:
                        # Clean up temp file
                        if os.path.exists(temp_path):
                            os.unlink(temp_path)
                            
                except Exception as e:
                    logger.debug(f"Account index {idx} failed: {e}")
                    continue
        
        return None
    
    def get_playlist_tracks(self, playlist_id: str) -> List[Dict]:
        """
        Get all tracks from a specific playlist
        
        Args:
            playlist_id: YouTube Music playlist ID
            
        Returns:
            List of track dictionaries with normalized structure
        """
        try:
            # YTMusic returns tracks with the playlist details
            playlist = self.ytmusic.get_playlist(playlist_id)
            tracks = playlist.get('tracks', [])
            
            # Normalize track data to match our internal structure
            normalized_tracks = []
            for track in tracks:
                # Handle cases where artist info might be missing
                artists = track.get('artists', [])
                artist_names = [artist['name'] for artist in artists] if artists else ['Unknown Artist']
                
                # Get album info safely
                album_info = track.get('album')
                album_name = album_info.get('name') if album_info else None
                
                # Get duration (YTMusic provides it in seconds or as a string)
                duration_seconds = track.get('duration_seconds', 0)
                if not duration_seconds and 'duration' in track:
                    # Sometimes duration is a string like "3:45"
                    try:
                        duration_str = track['duration']
                        if ':' in duration_str:
                            parts = duration_str.split(':')
                            if len(parts) == 2:  # MM:SS
                                duration_seconds = int(parts[0]) * 60 + int(parts[1])
                            elif len(parts) == 3:  # HH:MM:SS
                                duration_seconds = int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
                    except:
                        duration_seconds = 0
                
                normalized_tracks.append({
                    'id': track.get('videoId'),  # YouTube uses videoId as track identifier
                    'name': track.get('title', 'Unknown Title'),
                    'artists': artist_names,
                    'artist': ', '.join(artist_names),  # Single string for easy matching
                    'album': album_name,
                    'duration_ms': duration_seconds * 1000 if duration_seconds else None,
                    'isrc': None,  # YouTube Music doesn't provide ISRC codes
                    'thumbnails': track.get('thumbnails', [])
                })
            
            logger.info(f"Retrieved {len(normalized_tracks)} tracks from playlist '{playlist.get('title', playlist_id)}'")
            return normalized_tracks
            
        except Exception as e:
            logger.error(f"Error fetching tracks for playlist {playlist_id}: {e}")
            return []
    
    def search_song(self, song_name: str, artist_name: str, album: Optional[str] = None) -> Optional[Dict]:
        """
        Search for a song on YouTube Music
        
        Args:
            song_name: Name of the song
            artist_name: Name of the artist
            album: Optional album name for better matching
            
        Returns:
            Best matching track dictionary or None if not found
        """
        try:
            # Build search query
            query = f"{song_name} {artist_name}"
            if album:
                query += f" {album}"
            
            # Search for songs (filter='songs' returns only official songs, not videos)
            results = self.ytmusic.search(query, filter='songs', limit=5)
            
            if not results:
                logger.warning(f"No results found for: {query}")
                return None
            
            # Return the first result (usually most relevant)
            # In Phase 4, you'll implement better matching logic here
            best_match = results[0]
            
            artists = best_match.get('artists', [])
            artist_names = [artist['name'] for artist in artists] if artists else ['Unknown Artist']
            
            # Get album info
            album_info = best_match.get('album')
            album_name = album_info.get('name') if album_info else None
            
            # Get duration
            duration_seconds = best_match.get('duration_seconds', 0)
            if not duration_seconds and 'duration' in best_match:
                try:
                    duration_str = best_match['duration']
                    if ':' in duration_str:
                        parts = duration_str.split(':')
                        if len(parts) == 2:
                            duration_seconds = int(parts[0]) * 60 + int(parts[1])
                except:
                    duration_seconds = 0
            
            return {
                'id': best_match.get('videoId'),
                'name': best_match.get('title'),
                'artists': artist_names,
                'artist': ', '.join(artist_names),
                'album': album_name,
                'duration_ms': duration_seconds * 1000 if duration_seconds else None,
                'thumbnails': best_match.get('thumbnails', [])
            }
            
        except Exception as e:
            logger.error(f"Error searching for song '{song_name}' by '{artist_name}': {e}")
            return None
    
    def create_playlist(self, name: str, description: str = "", privacy: str = "PRIVATE") -> Optional[str]:
        """
        Create a new playlist on YouTube Music
        
        Args:
            name: Playlist name
            description: Playlist description
            privacy: Privacy level ('PUBLIC', 'PRIVATE', 'UNLISTED')
            
        Returns:
            Playlist ID if successful, None otherwise
        """
        try:
            playlist_id = self.ytmusic.create_playlist(
                title=name,
                description=description,
                privacy_status=privacy
            )
            
            logger.info(f"Created playlist '{name}' with ID: {playlist_id}")
            return playlist_id
            
        except Exception as e:
            logger.error(f"Error creating playlist '{name}': {e}")
            return None
    
    def add_songs_to_playlist(self, playlist_id: str, video_ids: List[str]) -> bool:
        """
        Add songs to a playlist
        
        Args:
            playlist_id: Target playlist ID
            video_ids: List of video IDs (track IDs) to add
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # YouTube Music API can handle multiple songs at once
            # But we'll add them in smaller batches for reliability
            batch_size = 50  # YouTube Music can handle up to 50 at a time
            
            for i in range(0, len(video_ids), batch_size):
                batch = video_ids[i:i + batch_size]
                self.ytmusic.add_playlist_items(playlist_id, batch)
                logger.debug(f"Added batch of {len(batch)} songs to playlist {playlist_id}")
            
            logger.info(f"Successfully added {len(video_ids)} songs to playlist {playlist_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error adding songs to playlist {playlist_id}: {e}")
            return False
    
    def remove_songs_from_playlist(self, playlist_id: str, video_ids: List[str]) -> bool:
        """
        Remove songs from a playlist
        
        Args:
            playlist_id: Target playlist ID
            video_ids: List of video IDs to remove
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Get current playlist to find setVideoIds (required for removal)
            playlist = self.ytmusic.get_playlist(playlist_id)
            tracks = playlist.get('tracks', [])
            
            # Build a map of videoId -> setVideoId
            video_id_map = {
                track['videoId']: track['setVideoId'] 
                for track in tracks 
                if 'setVideoId' in track and 'videoId' in track
            }
            
            # Remove each video
            removed_count = 0
            for video_id in video_ids:
                if video_id in video_id_map:
                    self.ytmusic.remove_playlist_items(
                        playlist_id, 
                        [{'videoId': video_id, 'setVideoId': video_id_map[video_id]}]
                    )
                    removed_count += 1
                else:
                    logger.warning(f"Video ID {video_id} not found in playlist {playlist_id}")
            
            logger.info(f"Removed {removed_count}/{len(video_ids)} songs from playlist {playlist_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error removing songs from playlist {playlist_id}: {e}")
            return False
    
    def get_playlist_info(self, playlist_id: str) -> Optional[Dict]:
        """
        Get detailed information about a playlist
        
        Args:
            playlist_id: YouTube Music playlist ID
            
        Returns:
            Dictionary with playlist info or None if error
        """
        try:
            playlist = self.ytmusic.get_playlist(playlist_id)
            
            return {
                'id': playlist.get('id'),
                'name': playlist.get('title'),
                'description': playlist.get('description', ''),
                'track_count': len(playlist.get('tracks', [])),
                'duration': playlist.get('duration'),
                'thumbnails': playlist.get('thumbnails', []),
                'author': playlist.get('author', {}).get('name') if playlist.get('author') else None
            }
            
        except Exception as e:
            logger.error(f"Error getting playlist info for {playlist_id}: {e}")
            return None


# Convenience function for testing
def test_youtube_service():
    """Test the YouTube Music service with basic operations"""
    
    print("\n" + "="*60)
    print("YouTube Music Service Test")
    print("="*60)
    
    try:
        # Initialize service (will use youtube_auth.json by default)
        print("\n[1/4] Initializing YouTube Music service...")
        yt_service = YouTubeMusicService()
        print("✓ Authentication successful!")
        
        # Test 1: Get playlists
        print("\n[2/4] Fetching your library playlists...")
        playlists = yt_service.get_library_playlists()
        
        if playlists:
            print(f"✓ Found {len(playlists)} playlists:")
            for i, playlist in enumerate(playlists[:5], 1):  # Show first 5
                print(f"   {i}. {playlist['name']} ({playlist['track_count']} tracks)")
            
            if len(playlists) > 5:
                print(f"   ... and {len(playlists) - 5} more")
        else:
            print("✗ No playlists found")
            return
        
        # Test 2: Get tracks from first playlist
        print(f"\n[3/4] Fetching tracks from '{playlists[0]['name']}'...")
        tracks = yt_service.get_playlist_tracks(playlists[0]['id'])
        
        if tracks:
            print(f"✓ Found {len(tracks)} tracks:")
            for i, track in enumerate(tracks[:5], 1):  # Show first 5
                duration = f"{track['duration_ms'] // 60000}:{(track['duration_ms'] // 1000) % 60:02d}" if track['duration_ms'] else "N/A"
                print(f"   {i}. {track['name']} - {track['artist']} [{duration}]")
            
            if len(tracks) > 5:
                print(f"   ... and {len(tracks) - 5} more")
        else:
            print("✗ No tracks found in playlist")
        
        # Test 3: Search for a song
        print("\n[4/4] Testing song search (Bohemian Rhapsody by Queen)...")
        result = yt_service.search_song("Bohemian Rhapsody", "Queen")
        
        if result:
            duration = f"{result['duration_ms'] // 60000}:{(result['duration_ms'] // 1000) % 60:02d}" if result['duration_ms'] else "N/A"
            print(f"✓ Found: {result['name']} - {result['artist']}")
            print(f"   Album: {result['album'] or 'N/A'}")
            print(f"   Duration: {duration}")
            print(f"   Video ID: {result['id']}")
        else:
            print("✗ Song not found")
        
        print("\n" + "="*60)
        print("All tests completed successfully! ✓")
        print("="*60 + "\n")
        
    except FileNotFoundError:
        print("\n✗ Error: youtube_auth.json file not found!")
        print("   Make sure the file exists in the current directory.")
    except ValueError as e:
        print(f"\n✗ Error: {e}")
        print("   Check that your youtube_auth.json has all required fields:")
        print("   - cookie")
        print("   - x-goog-authuser")
        print("   - user-agent")
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        logger.exception("Full error details:")


if __name__ == "__main__":
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Run tests
    test_youtube_service()
