# src/sync.py
"""
Sync engine - orchestrates playlist synchronization between platforms
"""

from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import logging

# We'll import your services later
# from services_spotify import SpotifyService
# from services_youtube import YouTubeService
# from matching import match_song
# from normalize import normalize_track_info

logger = logging.getLogger(__name__)


class SyncDirection(Enum):
    """Sync direction options"""
    SPOTIFY_TO_YOUTUBE = "spotify_to_youtube"
    YOUTUBE_TO_SPOTIFY = "youtube_to_spotify"
    BIDIRECTIONAL_AUTO = "bidirectional_auto"  # auto-detect which has more
    BIDIRECTIONAL_MANUAL = "bidirectional_manual"  # user specifies per sync


class SyncMode(Enum):
    """How to handle sync operations"""
    ADDITIONS_ONLY = "additions_only"  # Only add new songs
    DELETIONS_ONLY = "deletions_only"  # Only remove songs
    FULL_SYNC = "full_sync"  # Both additions and deletions
    DRY_RUN = "dry_run"  # Show what would change without changing


@dataclass
class SyncConfig:
    """Configuration for a sync operation"""
    direction: SyncDirection
    mode: SyncMode = SyncMode.FULL_SYNC
    matching_threshold: float = 0.85  # 85% similarity required
    playlist_ids: Optional[List[str]] = None  # None = all playlists
    exclude_playlists: List[str] = None  # Playlists to skip
    retry_attempts: int = 3
    skip_missing_songs: bool = True  # Skip songs that can't be found
    sync_order: bool = True  # Preserve track order
    backup_before_sync: bool = True


@dataclass
class SyncResult:
    """Results of a sync operation"""
    playlist_name: str
    source_platform: str
    destination_platform: str
    total_tracks: int
    matched_tracks: int
    added_tracks: int
    failed_tracks: int
    skipped_tracks: int
    failed_songs: List[Dict]  # Songs that couldn't be matched
    duration_seconds: float
    errors: List[str]


class SyncEngine:
    """Main sync engine - orchestrates playlist synchronization"""
    
    def __init__(self, spotify_service, youtube_service):
        """
        Initialize sync engine
        
        Args:
            spotify_service: Instance of SpotifyService
            youtube_service: Instance of YouTubeService
        """
        self.spotify = spotify_service
        self.youtube = youtube_service
        self.logger = logging.getLogger(__name__)
    
    def sync_playlist(
        self, 
        source_playlist_id: str,
        destination_playlist_id: Optional[str],
        config: SyncConfig
    ) -> SyncResult:
        """
        Sync a single playlist
        
        Args:
            source_playlist_id: ID of source playlist
            destination_playlist_id: ID of destination playlist (None = create new)
            config: Sync configuration
            
        Returns:
            SyncResult with operation details
        """
        # Implementation goes here
        pass
    
    def sync_all_playlists(self, config: SyncConfig) -> List[SyncResult]:
        """
        Sync all user playlists (respecting filters in config)
        
        Args:
            config: Sync configuration
            
        Returns:
            List of SyncResult for each playlist
        """
        # Implementation goes here
        pass
    
    def _fetch_source_tracks(self, playlist_id: str, platform: str) -> List[Dict]:
        """Fetch tracks from source playlist"""
        pass
    
    def _fetch_destination_tracks(self, playlist_id: str, platform: str) -> List[Dict]:
        """Fetch tracks from destination playlist"""
        pass
    
    def _match_tracks(
        self, 
        source_tracks: List[Dict], 
        destination_platform: str,
        threshold: float
    ) -> Tuple[List[Dict], List[Dict]]:
        """
        Match source tracks on destination platform
        
        Returns:
            Tuple of (matched_tracks, failed_tracks)
        """
        pass
    
    def _add_tracks_to_playlist(
        self, 
        playlist_id: str, 
        track_ids: List[str], 
        platform: str
    ):
        """Add tracks to destination playlist"""
        pass
    
    def _create_playlist(
        self, 
        name: str, 
        description: str, 
        platform: str
    ) -> str:
        """
        Create new playlist on destination platform
        
        Returns:
            New playlist ID
        """
        pass
    
    def _determine_sync_direction(
        self, 
        config: SyncConfig
    ) -> Tuple[str, str]:
        """
        Determine source and destination platforms
        
        Returns:
            Tuple of (source_platform, destination_platform)
        """
        if config.direction == SyncDirection.SPOTIFY_TO_YOUTUBE:
            return ("spotify", "youtube")
        elif config.direction == SyncDirection.YOUTUBE_TO_SPOTIFY:
            return ("youtube", "spotify")
        elif config.direction == SyncDirection.BIDIRECTIONAL_AUTO:
            # Logic to determine which has more tracks
            pass
        else:
            raise ValueError("Bidirectional manual not yet implemented")