"""
Spotify API Service Module
Handles all interactions with Spotify's API
"""

import spotipy
from spotipy.oauth2 import SpotifyOAuth
from typing import List, Dict, Optional
import logging

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
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri
        self.sp = None
        
    def authenticate(self, scope: str = "playlist-read-private playlist-modify-public playlist-modify-private") -> bool:
        """
        Authenticate with Spotify using OAuth 2.0
        
        Args:
            scope: Permission scopes needed (space-separated)
            
        Returns:
            True if authentication successful, False otherwise
        """
        try:
            auth_manager = SpotifyOAuth(
                client_id=self.client_id,
                client_secret=self.client_secret,
                redirect_uri=self.redirect_uri,
                scope=scope,
                cache_path=".spotify_cache"  # Stores auth token locally
            )
            
            self.sp = spotipy.Spotify(auth_manager=auth_manager)
            
            # Test authentication by getting current user
            user = self.sp.current_user()
            logger.info(f"Successfully authenticated as: {user['display_name']}")
            return True
            
        except Exception as e:
            logger.error(f"Authentication failed: {str(e)}")
            return False
    
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
    REDIRECT_URI = "http://localhost:8888/callback"
    
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