"""
Sync Engine - Simple One-Way Sync (Spotify → YouTube Music)
Phase 5, Step 9 - Simplest Case Implementation
"""

import logging
import time
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

# Import your services (adjust paths if needed)
from src.services_spotify import SpotifyService
from src.services_youtube import YouTubeMusicService
from src.normalize import normalize_track_name, normalize_artist_name
from src.matching import find_best_match

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class SyncResult:
    """Results of a sync operation"""
    playlist_name: str
    total_tracks: int
    matched_tracks: int
    failed_tracks: int
    failed_songs: List[Dict]
    duration_seconds: float
    success: bool


class SimpleSyncEngine:
    """Simple sync engine - Spotify to YouTube Music, additions only"""
    
    def __init__(self, spotify_service: SpotifyService, youtube_service: YouTubeMusicService):
        """
        Initialize sync engine
        
        Args:
            spotify_service: Authenticated SpotifyService instance
            youtube_service: Authenticated YouTubeMusicService instance
        """
        self.spotify = spotify_service
        self.youtube = youtube_service
        self.logger = logging.getLogger(__name__)
    
    def sync_playlist_spotify_to_youtube(
        self, 
        spotify_playlist_id: str,
        youtube_playlist_id: Optional[str] = None,
        create_if_missing: bool = True
    ) -> SyncResult:
        """
        Sync a single Spotify playlist to YouTube Music (additions only)
        
        Args:
            spotify_playlist_id: ID of Spotify playlist to sync from
            youtube_playlist_id: ID of YouTube Music playlist to sync to (None = create new)
            create_if_missing: If True, create YouTube playlist if youtube_playlist_id is None
            
        Returns:
            SyncResult with operation details
        """
        start_time = time.time()
        
        try:
            # Step 1: Fetch source playlist info and tracks
            self.logger.info("=" * 60)
            self.logger.info("Starting Spotify → YouTube Music Sync")
            self.logger.info("=" * 60)
            
            spotify_playlists = self.spotify.get_user_playlists()
            playlist_name = next(
                (pl['name'] for pl in spotify_playlists if pl['id'] == spotify_playlist_id),
                "Unknown Playlist"
            )
            
            self.logger.info(f"📋 Source Playlist: {playlist_name}")
            self.logger.info(f"🔍 Fetching tracks from Spotify...")
            
            source_tracks = self.spotify.get_playlist_tracks(spotify_playlist_id)
            
            if not source_tracks:
                self.logger.warning("⚠️  No tracks found in source playlist")
                return SyncResult(
                    playlist_name=playlist_name,
                    total_tracks=0,
                    matched_tracks=0,
                    failed_tracks=0,
                    failed_songs=[],
                    duration_seconds=time.time() - start_time,
                    success=True
                )
            
            self.logger.info(f"✅ Found {len(source_tracks)} tracks in Spotify playlist")
            
            # Step 2: Create or get YouTube Music playlist
            if youtube_playlist_id is None:
                if create_if_missing:
                    self.logger.info(f"🆕 Creating new YouTube Music playlist: {playlist_name}")
                    youtube_playlist_id = self.youtube.create_playlist(
                        name=f"{playlist_name} (from Spotify)",
                        description=f"Synced from Spotify playlist '{playlist_name}'"
                    )
                    
                    if not youtube_playlist_id:
                        raise Exception("Failed to create YouTube Music playlist")
                else:
                    raise ValueError("youtube_playlist_id is required when create_if_missing=False")
            
            self.logger.info(f"🎵 Target YouTube Music Playlist ID: {youtube_playlist_id}")
            
            # Step 3: Get existing tracks in YouTube playlist (to avoid duplicates)
            self.logger.info("🔍 Checking existing tracks in YouTube Music playlist...")
            existing_youtube_tracks = self.youtube.get_playlist_tracks(youtube_playlist_id)
            existing_track_ids = {track['videoId'] for track in existing_youtube_tracks if track.get('videoId')}
            
            self.logger.info(f"📊 YouTube playlist currently has {len(existing_youtube_tracks)} tracks")
            
            # Step 4: Match and add tracks
            matched_video_ids = []
            failed_songs = []
            
            self.logger.info("\n" + "=" * 60)
            self.logger.info("Starting Track Matching Process")
            self.logger.info("=" * 60)
            
            for idx, track in enumerate(source_tracks, 1):
                track_name = track['name']
                artists = ', '.join(track['artists']) if isinstance(track['artists'], list) else track['artists']
                
                self.logger.info(f"\n[{idx}/{len(source_tracks)}] Processing: {track_name} - {artists}")
                
                # Normalize track info for better matching
                normalized_track = normalize_track_name(track_name)
                normalized_artist = normalize_artist_name(artists)
                
                # Search on YouTube Music
                self.logger.info(f"  🔍 Searching YouTube Music...")
                youtube_result = self.youtube.search_song(normalized_track, normalized_artist)
                
                if youtube_result and youtube_result.get('videoId'):
                    video_id = youtube_result['videoId']
                    
                    # Validate video ID format
                    if not video_id or len(video_id) < 5:
                        self.logger.warning(f"  ⚠️  Invalid video ID: {video_id}")
                        failed_songs.append({
                            'track': track_name,
                            'artist': artists,
                            'reason': f'Invalid video ID: {video_id}'
                        })
                        continue
                    
                    # Check if already in playlist
                    if video_id in existing_track_ids:
                        self.logger.info(f"  ⏭️  Already in playlist, skipping")
                        continue
                    
                    # Use fuzzy matching to verify it's a good match
                    match_confidence = find_best_match(
                        track_name, 
                        artists,
                        youtube_result['title'],
                        youtube_result['artists']
                    )
                    
                    if match_confidence >= 0.80:  # 80% confidence threshold
                        matched_video_ids.append(video_id)
                        self.logger.info(f"  ✅ Matched! Confidence: {match_confidence:.1%}")
                        self.logger.info(f"     YouTube: {youtube_result['title']} - {youtube_result['artists']}")
                        self.logger.info(f"     Video ID: {video_id}")
                    elif match_confidence >= 0.70:  # Between 70-80% - possible match
                        self.logger.warning(f"  ⚠️  Possible match ({match_confidence:.1%})")
                        self.logger.warning(f"     Spotify: {track_name} - {artists}")
                        self.logger.warning(f"     YouTube: {youtube_result['title']} - {youtube_result['artists']}")
                        self.logger.warning(f"     Video ID: {video_id}")
                        
                        # Auto-add if confidence is 75% or higher
                        if match_confidence >= 0.75:
                            self.logger.info(f"  ➕ Auto-adding (75%+ confidence)")
                            matched_video_ids.append(video_id)
                        else:
                            failed_songs.append({
                                'track': track_name,
                                'artist': artists,
                                'reason': f'Low match confidence: {match_confidence:.1%} (YouTube: {youtube_result["title"]})'
                            })
                    else:
                        self.logger.warning(f"  ⚠️  Low confidence match ({match_confidence:.1%}), skipping")
                        failed_songs.append({
                            'track': track_name,
                            'artist': artists,
                            'reason': f'Low match confidence: {match_confidence:.1%}'
                        })
                else:
                    self.logger.warning(f"  ❌ No match found on YouTube Music")
                    failed_songs.append({
                        'track': track_name,
                        'artist': artists,
                        'reason': 'Not found on YouTube Music'
                    })
            
            # Step 5: Add matched tracks to YouTube Music playlist
            self.logger.info("\n" + "=" * 60)
            self.logger.info("Adding Tracks to YouTube Music Playlist")
            self.logger.info("=" * 60)
            
            if matched_video_ids:
                self.logger.info(f"📤 Adding {len(matched_video_ids)} tracks to YouTube Music...")
                
                # Add in smaller batches with error handling
                batch_size = 10  # Reduced from 50 to avoid rate limits
                successfully_added = 0
                
                for i in range(0, len(matched_video_ids), batch_size):
                    batch = matched_video_ids[i:i + batch_size]
                    batch_num = i//batch_size + 1
                    
                    self.logger.info(f"  📦 Processing batch {batch_num} ({len(batch)} tracks)...")
                    
                    try:
                        result = self.youtube.add_songs_to_playlist(youtube_playlist_id, batch)
                        
                        if result and isinstance(result, dict):
                            if result['success']:
                                added = result['added']
                                successfully_added += added
                                self.logger.info(f"  ✅ Batch {batch_num}: {added}/{len(batch)} songs added")
                                if result.get('error'):
                                    self.logger.warning(f"     ⚠️  {result['error']}")
                            else:
                                self.logger.error(f"  ❌ Batch {batch_num} failed: {result.get('error', 'Unknown error')}")
                        else:
                            self.logger.error(f"  ❌ Batch {batch_num} failed (API returned invalid response)")
                        
                        # Add delay between batches to avoid rate limiting
                        if i + batch_size < len(matched_video_ids):
                            time.sleep(1)  # 1 second delay between batches
                            
                    except Exception as e:
                        self.logger.error(f"  ❌ Batch {batch_num} failed with error: {e}")
                        # Continue with next batch even if one fails
                
                self.logger.info(f"\n📊 Addition Summary:")
                self.logger.info(f"  • Attempted: {len(matched_video_ids)} tracks")
                self.logger.info(f"  • Successfully added: {successfully_added} tracks")
                
                if successfully_added < len(matched_video_ids):
                    self.logger.warning(f"  ⚠️  {len(matched_video_ids) - successfully_added} tracks failed to add")
            else:
                self.logger.warning("⚠️  No new tracks to add")
            
            # Step 6: Summary
            duration = time.time() - start_time
            
            self.logger.info("\n" + "=" * 60)
            self.logger.info("Sync Complete - Summary")
            self.logger.info("=" * 60)
            self.logger.info(f"📋 Playlist: {playlist_name}")
            self.logger.info(f"📊 Total tracks processed: {len(source_tracks)}")
            self.logger.info(f"✅ Successfully matched: {len(matched_video_ids)}")
            self.logger.info(f"❌ Failed to match: {len(failed_songs)}")
            self.logger.info(f"⏱️  Duration: {duration:.2f} seconds")
            
            if failed_songs:
                self.logger.info("\n❌ Failed Songs:")
                for song in failed_songs[:10]:  # Show first 10
                    self.logger.info(f"  • {song['track']} - {song['artist']}")
                    self.logger.info(f"    Reason: {song['reason']}")
                if len(failed_songs) > 10:
                    self.logger.info(f"  ... and {len(failed_songs) - 10} more")
            
            return SyncResult(
                playlist_name=playlist_name,
                total_tracks=len(source_tracks),
                matched_tracks=len(matched_video_ids),
                failed_tracks=len(failed_songs),
                failed_songs=failed_songs,
                duration_seconds=duration,
                success=True
            )
            
        except Exception as e:
            self.logger.error(f"❌ Sync failed with error: {str(e)}", exc_info=True)
            return SyncResult(
                playlist_name="Unknown",
                total_tracks=0,
                matched_tracks=0,
                failed_tracks=0,
                failed_songs=[],
                duration_seconds=time.time() - start_time,
                success=False
            )


# Example usage / test function
def test_sync():
    """Test the sync engine"""
    from src.config import Config
    
    # Load config
    config = Config()
    
    # Initialize services
    spotify = SpotifyService(
        client_id=config.SPOTIFY_CLIENT_ID,
        client_secret=config.SPOTIFY_CLIENT_SECRET,
        redirect_uri=config.SPOTIFY_REDIRECT_URI
    )
    
    youtube = YouTubeMusicService()
    
    # Authenticate
    print("🔐 Authenticating with Spotify...")
    if not spotify.authenticate():
        print("❌ Spotify authentication failed")
        return
    
    print("✅ Spotify authenticated!")
    
    # Initialize sync engine
    sync_engine = SimpleSyncEngine(spotify, youtube)
    
    # Get user's Spotify playlists
    print("\n📋 Fetching your Spotify playlists...")
    playlists = spotify.get_user_playlists()
    
    if not playlists:
        print("❌ No playlists found")
        return
    
    print(f"\n✅ Found {len(playlists)} playlists:\n")
    for idx, pl in enumerate(playlists, 1):
        print(f"{idx}. {pl['name']} ({pl['tracks_total']} tracks)")
    
    # Let user choose a playlist
    choice = input(f"\nEnter playlist number to sync (1-{len(playlists)}): ")
    
    try:
        playlist_idx = int(choice) - 1
        selected_playlist = playlists[playlist_idx]
        
        print(f"\n🎵 You selected: {selected_playlist['name']}")
        confirm = input("Start sync? (y/n): ")
        
        if confirm.lower() == 'y':
            # Sync the playlist
            result = sync_engine.sync_playlist_spotify_to_youtube(
                spotify_playlist_id=selected_playlist['id'],
                youtube_playlist_id=None,  # Will create new playlist
                create_if_missing=True
            )
            
            if result.success:
                print("\n🎉 Sync completed successfully!")
            else:
                print("\n❌ Sync failed")
        else:
            print("Sync cancelled")
            
    except (ValueError, IndexError):
        print("❌ Invalid selection")


if __name__ == "__main__":
    test_sync()