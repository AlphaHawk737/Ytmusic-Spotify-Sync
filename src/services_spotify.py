"""
Spotify API Service Module
Handles all interactions with Spotify's API
"""

import spotipy
from spotipy.oauth2 import SpotifyOAuth, SpotifyOauthError
from typing import List, Dict, Optional
import logging
import sys
import os

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SpotifyService:
    """Service class for Spotify API operations"""
    
    def __init__(self, client_id: str, client_secret: str, redirect_uri: str):
        """
        Initialize Spotify service with credentials
        
        Args:
            client_id: Spotify app client ID
            client_secret: Spotify app client secret
            redirect_uri: Redirect URI for OAuth (must match Spotify app settings)
        """
        # Validate and strip credentials
        if not client_id or not client_id.strip():
            raise ValueError("client_id cannot be None or empty")
        if not client_secret or not client_secret.strip():
            raise ValueError("client_secret cannot be None or empty")
        if not redirect_uri or not redirect_uri.strip():
            raise ValueError("redirect_uri cannot be None or empty")
        
        self.client_id = client_id.strip()
        self.client_secret = client_secret.strip()
        self.redirect_uri = redirect_uri.strip()
        self.sp = None
        
    def authenticate(self, scope: str = "playlist-read-private playlist-modify-public playlist-modify-private") -> bool:
        """
        Authenticate with Spotify using OAuth 2.0
        
        Args:
            scope: Permission scopes needed (space-separated)
            
        Returns:
            True if authentication successful, False otherwise
        """
        auth_manager = None
        try:
            # Log credentials status (without exposing secrets)
            logger.info(f"Attempting authentication with client_id: {self.client_id[:10]}...")
            logger.info(f"Using redirect_uri: {self.redirect_uri}")
            
            # Validate credential format before creating auth manager
            # Client ID should be 32 characters, Client Secret should be 32 characters
            if len(self.client_id) != 32:
                logger.warning(f"Client ID length is {len(self.client_id)}, expected 32 characters")
            if len(self.client_secret) != 32:
                logger.warning(f"Client Secret length is {len(self.client_secret)}, expected 32 characters")
            
            # Create auth manager
            # Note: Browser will open automatically if no cached token exists
            auth_manager = SpotifyOAuth(
                client_id=self.client_id,
                client_secret=self.client_secret,
                redirect_uri=self.redirect_uri,
                scope=scope,
                cache_path=".spotify_cache"  # Stores auth token locally
            )
            
            # Check if we have a cached token first
            token_info = auth_manager.get_cached_token()
            if token_info:
                if auth_manager.is_token_expired(token_info):
                    logger.info("Cached token expired, attempting to refresh...")
                    try:
                        token_info = auth_manager.refresh_access_token(token_info['refresh_token'])
                    except Exception as refresh_error:
                        error_msg = str(refresh_error)
                        if "invalid_client" in error_msg.lower() or "invalid" in error_msg.lower() or "401" in error_msg:
                            logger.warning("Token refresh failed - credentials may be invalid")
                            self._handle_invalid_client_error(error_msg)
                            return False
                        else:
                            raise
                else:
                    logger.info("Using cached token")
            else:
                logger.info("No cached token found, will need to authorize...")
                # Try to get authorization URL to validate credentials early
                # This doesn't fully validate but helps catch some issues
                try:
                    auth_url = auth_manager.get_authorize_url()
                    logger.info("Authorization URL generated successfully")
                except Exception as url_error:
                    error_msg = str(url_error)
                    if "invalid_client" in error_msg.lower() or "invalid" in error_msg.lower():
                        self._handle_invalid_client_error(error_msg)
                        return False
                    # If it's not an invalid_client error, continue with normal flow
            
            self.sp = spotipy.Spotify(auth_manager=auth_manager)
            
            # Test authentication by getting current user
            # This will trigger OAuth flow if no cached token exists
            # IMPORTANT: If you see "invalid client" in browser, close it and check credentials
            # The terminal should not freeze - errors are caught below
            try:
                user = self.sp.current_user()
                logger.info(f"Successfully authenticated as: {user['display_name']}")
                return True
            except spotipy.exceptions.SpotifyException as api_error:
                # Handle API-level errors that might indicate invalid credentials
                error_msg = str(api_error)
                error_code = getattr(api_error, 'http_status', None)
                
                # Check for invalid client errors
                if "invalid_client" in error_msg.lower() or "invalid client" in error_msg.lower():
                    self._handle_invalid_client_error(error_msg)
                    return False
                # 401 Unauthorized often means invalid credentials
                if error_code == 401 or "401" in error_msg:
                    logger.error("Received 401 Unauthorized - credentials may be invalid")
                    self._handle_invalid_client_error("401 Unauthorized - Invalid credentials")
                    return False
                raise
            
        except SpotifyOauthError as oauth_error:
            error_msg = str(oauth_error)
            logger.error(f"OAuth Error: {error_msg}")
            
            if "invalid_client" in error_msg.lower() or "invalid client" in error_msg.lower():
                self._handle_invalid_client_error(error_msg)
            else:
                logger.error("OAuth authentication failed. Check your credentials and redirect URI.")
            
            return False
            
        except spotipy.exceptions.SpotifyException as spotify_error:
            error_msg = str(spotify_error)
            logger.error(f"Spotify API Error: {error_msg}")
            
            if "invalid_client" in error_msg.lower() or "invalid client" in error_msg.lower():
                self._handle_invalid_client_error(error_msg)
            else:
                logger.error("Spotify API request failed.")
            
            return False
            
        except KeyboardInterrupt:
            logger.error("\nAuthentication interrupted by user (Ctrl+C)")
            print("\n⚠ Authentication cancelled by user.")
            return False
            
        except Exception as e:
            error_msg = str(e)
            error_type = type(e).__name__
            logger.error(f"Unexpected error during authentication ({error_type}): {error_msg}")
            
            if "invalid_client" in error_msg.lower() or "invalid client" in error_msg.lower():
                self._handle_invalid_client_error(error_msg)
            else:
                logger.error("An unexpected error occurred. Please check your configuration.")
                # Print traceback for debugging (but don't let it hang)
                import traceback
                logger.debug(traceback.format_exc())
            
            return False
    
    def _handle_invalid_client_error(self, error_msg: str):
        """Handle invalid client errors with detailed diagnostics"""
        import os
        
        print("\n" + "=" * 60)
        print("❌ INVALID CLIENT ERROR")
        print("=" * 60)
        print("\n⚠ If a browser window opened showing this error, you can close it safely.")
        print("   The terminal should respond normally - if it's frozen, press Ctrl+C.\n")
        
        # Show actual values being used (safely)
        print("Current Configuration:")
        print(f"  Client ID: {self.client_id[:8]}...{self.client_id[-4:] if len(self.client_id) > 12 else '...'} (length: {len(self.client_id)})")
        print(f"  Client Secret: {'*' * min(20, len(self.client_secret))}... (length: {len(self.client_secret)})")
        print(f"  Redirect URI: {self.redirect_uri}")
        print()
        
        # Check for cache file
        cache_file = ".spotify_cache"
        if os.path.exists(cache_file):
            print(f"⚠ Found existing cache file: {cache_file}")
            print("  This may contain invalid credentials. Consider deleting it.")
            print()
        
        print("Possible causes:")
        print("1. ✗ Client ID or Client Secret is incorrect")
        print("   → Go to https://developer.spotify.com/dashboard")
        print("   → Select your app and verify Client ID and Client Secret")
        print("   → Copy them EXACTLY (no extra spaces, no quotes) to .env file")
        print(f"   → Current Client ID length: {len(self.client_id)} (should be 32)")
        print(f"   → Current Client Secret length: {len(self.client_secret)} (should be 32)")
        
        print(f"\n2. ✗ Redirect URI mismatch")
        print(f"   → Your code uses: {self.redirect_uri}")
        print("   → In Spotify Dashboard, go to 'Edit Settings'")
        print("   → Under 'Redirect URIs', ensure this EXACT string is listed:")
        print(f"     {self.redirect_uri}")
        print("   → Common mistakes:")
        print("     - Using 'localhost' instead of '127.0.0.1' (or vice versa)")
        print("     - Missing 'http://' prefix")
        print("     - Wrong port number")
        print("     - Extra trailing slash or missing path")
        
        print("\n3. ✗ Credentials formatting issues in .env file")
        print("   → .env file should look like this (NO quotes):")
        print("     SPOTIFY_CLIENT_ID=your_32_char_client_id_here")
        print("     SPOTIFY_CLIENT_SECRET=your_32_char_secret_here")
        print("     SPOTIFY_REDIRECT_URI=http://127.0.0.1:8888/callback")
        print("   → NOT like this (with quotes):")
        print('     SPOTIFY_CLIENT_ID="your_client_id"  ❌ WRONG')
        print("   → Check for hidden characters or BOM markers")
        
        print("\n4. ✗ App configuration issues")
        print("   → Ensure your app is not restricted")
        print("   → Check that you're using the correct app (not a deleted one)")
        print("   → Verify the app is active in your dashboard")
        
        print("\n" + "=" * 60)
        print("💡 TROUBLESHOOTING STEPS:")
        print("=" * 60)
        print("1. Delete .spotify_cache file if it exists")
        print("2. Double-check credentials in Spotify Dashboard")
        print("3. Verify redirect URI matches EXACTLY (character by character)")
        print("4. Ensure .env file has no quotes around values")
        print("5. Restart your terminal/IDE after changing .env")
        print("=" * 60)
        logger.error("INVALID CLIENT ERROR - See detailed diagnostics above")
    
    def get_user_playlists(self) -> List[Dict]:
        """
        Fetch all playlists for the authenticated user
        
        Returns:
            List of playlist dictionaries with id, name, and track count
        """
        if not self.sp:
            raise RuntimeError("Not authenticated. Call authenticate() first.")
        
        playlists = []
        try:
            # Spotify returns paginated results, fetch all
            results = self.sp.current_user_playlists(limit=50)
            
            while results:
                for playlist in results['items']:
                    playlists.append({
                        'id': playlist['id'],
                        'name': playlist['name'],
                        'tracks_total': playlist['tracks']['total'],
                        'owner': playlist['owner']['display_name'],
                        'public': playlist['public']
                    })
                
                # Get next page if it exists
                if results['next']:
                    results = self.sp.next(results)
                else:
                    break
            
            logger.info(f"Found {len(playlists)} playlists")
            return playlists
            
        except Exception as e:
            logger.error(f"Failed to fetch playlists: {str(e)}")
            return []
    
    def get_playlist_tracks(self, playlist_id: str) -> List[Dict]:
        """
        Get all tracks from a specific playlist
        
        Args:
            playlist_id: Spotify playlist ID
            
        Returns:
            List of track dictionaries with name, artist, album, etc.
        """
        if not self.sp:
            raise RuntimeError("Not authenticated. Call authenticate() first.")
        
        tracks = []
        try:
            results = self.sp.playlist_tracks(playlist_id, limit=100)
            
            while results:
                for item in results['items']:
                    track = item['track']
                    if track:  # Sometimes tracks can be None (deleted/unavailable)
                        tracks.append({
                            'id': track['id'],
                            'name': track['name'],
                            'artists': [artist['name'] for artist in track['artists']],
                            'album': track['album']['name'],
                            'duration_ms': track['duration_ms'],
                            'uri': track['uri']
                        })
                
                # Get next page
                if results['next']:
                    results = self.sp.next(results)
                else:
                    break
            
            logger.info(f"Found {len(tracks)} tracks in playlist {playlist_id}")
            return tracks
            
        except Exception as e:
            logger.error(f"Failed to fetch tracks for playlist {playlist_id}: {str(e)}")
            return []
    
    def search_track(self, track_name: str, artist_name: str, limit: int = 5) -> List[Dict]:
        """
        Search for a track on Spotify
        
        Args:
            track_name: Name of the track
            artist_name: Name of the artist
            limit: Maximum number of results to return
            
        Returns:
            List of matching tracks
        """
        if not self.sp:
            raise RuntimeError("Not authenticated. Call authenticate() first.")
        
        try:
            # Construct search query
            query = f"track:{track_name} artist:{artist_name}"
            results = self.sp.search(q=query, type='track', limit=limit)
            
            tracks = []
            for track in results['tracks']['items']:
                tracks.append({
                    'id': track['id'],
                    'name': track['name'],
                    'artists': [artist['name'] for artist in track['artists']],
                    'album': track['album']['name'],
                    'uri': track['uri']
                })
            
            return tracks
            
        except Exception as e:
            logger.error(f"Search failed for '{track_name}' by '{artist_name}': {str(e)}")
            return []
    
    def create_playlist(self, name: str, description: str = "", public: bool = False) -> Optional[str]:
        """
        Create a new playlist
        
        Args:
            name: Playlist name
            description: Playlist description
            public: Whether playlist should be public
            
        Returns:
            Playlist ID if successful, None otherwise
        """
        if not self.sp:
            raise RuntimeError("Not authenticated. Call authenticate() first.")
        
        try:
            user_id = self.sp.current_user()['id']
            playlist = self.sp.user_playlist_create(
                user=user_id,
                name=name,
                public=public,
                description=description
            )
            
            logger.info(f"Created playlist '{name}' with ID: {playlist['id']}")
            return playlist['id']
            
        except Exception as e:
            logger.error(f"Failed to create playlist '{name}': {str(e)}")
            return None
    
    def add_tracks_to_playlist(self, playlist_id: str, track_uris: List[str]) -> bool:
        """
        Add tracks to a playlist
        
        Args:
            playlist_id: Spotify playlist ID
            track_uris: List of Spotify track URIs (format: spotify:track:xxx)
            
        Returns:
            True if successful, False otherwise
        """
        if not self.sp:
            raise RuntimeError("Not authenticated. Call authenticate() first.")
        
        try:
            # Spotify API has a limit of 100 tracks per request
            batch_size = 100
            for i in range(0, len(track_uris), batch_size):
                batch = track_uris[i:i + batch_size]
                self.sp.playlist_add_items(playlist_id, batch)
            
            logger.info(f"Added {len(track_uris)} tracks to playlist {playlist_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to add tracks to playlist {playlist_id}: {str(e)}")
            return False


# Test function to demonstrate usage
def test_spotify_service():
    """
    Test function - demonstrates how to use SpotifyService
    Run this after setting up your .env file
    """
    # These would come from your .env file in actual usage
    CLIENT_ID = "your_client_id_here"
    CLIENT_SECRET = "your_client_secret_here"
    REDIRECT_URI = "http://127.0.0.1:8888/callback"
    
    # Initialize service
    spotify = SpotifyService(CLIENT_ID, CLIENT_SECRET, REDIRECT_URI)
    
    # Authenticate
    if not spotify.authenticate():
        print("Authentication failed!")
        return
    
    # Get user's playlists
    playlists = spotify.get_user_playlists()
    print(f"\nFound {len(playlists)} playlists:")
    for pl in playlists[:5]:  # Show first 5
        print(f"  - {pl['name']} ({pl['tracks_total']} tracks)")
    
    # Get tracks from first playlist
    if playlists:
        first_playlist = playlists[0]
        tracks = spotify.get_playlist_tracks(first_playlist['id'])
        print(f"\nFirst 5 tracks from '{first_playlist['name']}':")
        for track in tracks[:5]:
            artists = ", ".join(track['artists'])
            print(f"  - {track['name']} by {artists}")
    
    # Search for a song
    search_results = spotify.search_track("Bohemian Rhapsody", "Queen")
    print(f"\nSearch results for 'Bohemian Rhapsody' by Queen:")
    for track in search_results:
        artists = ", ".join(track['artists'])
        print(f"  - {track['name']} by {artists} (Album: {track['album']})")


if __name__ == "__main__":
    test_spotify_service()