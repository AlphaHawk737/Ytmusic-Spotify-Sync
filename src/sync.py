# src/sync.py
import logging
import time
import sys
import re
import os
import difflib
from datetime import datetime
from typing import List, Dict, Any

from src.services_spotify import SpotifyService
from src.services_youtube import YouTubeMusicService
from src.config import Config

class SyncLogger:
    """
    Handles dual-logging: 
    1. Concise, visual output for Terminal.
    2. Detailed, formal, technical output for Log Files.
    """
    def __init__(self, enable_file_logging=False):
        self.file_logger = None
        if enable_file_logging:
            if not os.path.exists('logs'):
                os.makedirs('logs')
            filename = f"logs/sync_session_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.log"
            
            # Setup File Logger
            self.file_logger = logging.getLogger('file_logger')
            self.file_logger.setLevel(logging.DEBUG)
            handler = logging.FileHandler(filename, encoding='utf-8')
            formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(message)s')
            handler.setFormatter(formatter)
            self.file_logger.addHandler(handler)
            print(f"📄 Detailed log file created at: {filename}")

    def log_terminal(self, msg: str):
        """Print to console only"""
        print(msg)

    def log_file(self, msg: str, level='INFO'):
        """Write to file only (Formal tone)"""
        if self.file_logger:
            if level == 'INFO': self.file_logger.info(msg)
            elif level == 'ERROR': self.file_logger.error(msg)
            elif level == 'WARNING': self.file_logger.warning(msg)
            elif level == 'DEBUG': self.file_logger.debug(msg)

    def log_both(self, terminal_msg: str, file_msg: str = None, level='INFO'):
        """Log distinct messages to both destinations"""
        print(terminal_msg)
        if self.file_logger:
            # Use file_msg if provided, else strip emojis from terminal_msg for file
            clean_msg = file_msg if file_msg else self._clean_emojis(terminal_msg)
            if level == 'INFO': self.file_logger.info(clean_msg)
            elif level == 'ERROR': self.file_logger.error(clean_msg)

    def _clean_emojis(self, text):
        return text.encode('ascii', 'ignore').decode('ascii').strip()

class SyncEngine:
    def __init__(self, logger: SyncLogger):
        self.logger = logger
        self.config = Config()
        self.spotify = SpotifyService(
            client_id=self.config.SPOTIFY_CLIENT_ID,
            client_secret=self.config.SPOTIFY_CLIENT_SECRET,
            redirect_uri=self.config.SPOTIFY_REDIRECT_URI
        )
        yt_header_file = getattr(self.config, 'YOUTUBE_HEADERS_FILE', 'youtube_auth.json')
        self.youtube = YouTubeMusicService(headers_file=yt_header_file)
        
        # State tracking for summary
        self.unmatched_songs = []
        self.failed_to_add_songs = []

    def clean_text(self, text):
        if not text: return ""
        text = text.lower()
        # Remove (...) and [...]
        text = re.sub(r'[\(\[].*?[\)\]]', '', text) 
        # Remove specific filler words
        text = text.replace("feat.", "").replace("ft.", "").replace("remastered", "").replace("remaster", "")
        # Remove non-alphanumeric
        return re.sub(r'[^a-z0-9\s]', '', text).strip()

    def calculate_score(self, s_title, s_artist, t_title, t_artist):
        """
        Calculates a precise match score (0-100).
        """
        clean_s = self.clean_text(f"{s_title} {s_artist}")
        clean_t = self.clean_text(f"{t_title} {t_artist}")
        
        # 1. Exact Match
        if clean_s == clean_t:
            return 100.0
            
        # 2. Sequence Matcher (Levenshtein ratio)
        ratio = difflib.SequenceMatcher(None, clean_s, clean_t).ratio()
        score = ratio * 100
        
        # 3. Penalize if length difference is huge (prevents "Love" matching "Love Story" too highly)
        len_diff = abs(len(clean_s) - len(clean_t))
        if len_diff > 10 and score > 80:
            score -= 10
            
        return round(score, 2)

    def sync_playlist(self, sp_playlist_id: str, target_yt_id: str = None):
        # --- 1. SETUP ---
        self.logger.log_file("=== SESSION START ===")
        self.logger.log_file(f"Source Spotify Playlist ID: {sp_playlist_id}")
        
        self.logger.log_terminal("\n🔍 Fetching Spotify Tracks...")
        sp_tracks = self.spotify.get_playlist_tracks(sp_playlist_id)
        
        if not sp_tracks:
            self.logger.log_both("❌ No tracks found.", "Error: No tracks found in Spotify playlist.", "ERROR")
            return

        sp_playlist_info = self.spotify.sp.playlist(sp_playlist_id)
        source_name = sp_playlist_info['name']
        self.logger.log_file(f"Source Playlist Name: {source_name}")
        self.logger.log_file(f"Total Source Tracks: {len(sp_tracks)}")
        self.logger.log_terminal(f"✅ Found {len(sp_tracks)} tracks in '{source_name}'.")

        # --- 2. TARGET PLAYLIST ---
        if not target_yt_id:
            self.logger.log_terminal(f"\n🔨 Creating NEW YouTube Playlist: '{source_name}'...")
            target_yt_id = self.youtube.create_playlist(source_name, "Synced by Python Sync Tool")
            if not target_yt_id:
                self.logger.log_both("❌ Creation failed.", "CRITICAL: Failed to create YouTube playlist.", "ERROR")
                return
            self.logger.log_file(f"Action: Created New Playlist. ID: {target_yt_id}")
        else:
            self.logger.log_file(f"Action: Using Existing Playlist. ID: {target_yt_id}")

        # --- 3. MATCHING ---
        self.logger.log_terminal("\n🔄 Starting Matching Process...")
        self.logger.log_file("=== MATCHING PHASE ===")
        
        matched_videos = [] # List of dicts {videoId, title, original_name}
        
        for i, track in enumerate(sp_tracks):
            sp_name = track['name']
            sp_artist = track['artists'][0] if track['artists'] else "Unknown"
            sp_id = track.get('id', 'N/A')
            
            log_prefix = f"Track {i+1}/{len(sp_tracks)}: {sp_name} - {sp_artist}"
            self.logger.log_file(f"Processing {log_prefix} (SpotifyID: {sp_id})")
            
            # Search
            search_query = f"{sp_name} {sp_artist}"
            self.logger.log_file(f"  > Search Query: '{search_query}'")
            search_result = self.youtube.search_song(sp_name, sp_artist)
            
            if search_result:
                yt_title = search_result['title']
                yt_id = search_result['videoId']
                yt_artists = search_result.get('artists', [])
                # Normalize artist format
                yt_artist_str = yt_artists[0].get('name') if isinstance(yt_artists, list) and yt_artists and isinstance(yt_artists[0], dict) else str(yt_artists)
                
                score = self.calculate_score(sp_name, sp_artist, yt_title, yt_artist_str)
                
                self.logger.log_file(f"  > Top Result: '{yt_title}' by '{yt_artist_str}' (ID: {yt_id})")
                self.logger.log_file(f"  > Match Score: {score}/100")

                if score >= 60: # Threshold
                    matched_videos.append({'id': yt_id, 'title': yt_title, 'sp_name': sp_name})
                    self.logger.log_file("  > Result: MATCH ACCEPTED")
                    self.logger.log_terminal(f"  ✅ {score:.0f}% | {sp_name[:20]}... -> {yt_title[:20]}...")
                else:
                    self.unmatched_songs.append({'name': sp_name, 'artist': sp_artist, 'reason': f"Low Score ({score}%)", 'best_match': yt_title})
                    self.logger.log_file("  > Result: MATCH REJECTED (Low Score)")
                    self.logger.log_terminal(f"  ⚠️ {score:.0f}% | {sp_name[:20]}... != {yt_title[:20]}... (Skipped)")
            else:
                self.unmatched_songs.append({'name': sp_name, 'artist': sp_artist, 'reason': "No Search Results", 'best_match': "N/A"})
                self.logger.log_file("  > Result: MATCH FAILED (No results found)")
                self.logger.log_terminal(f"  ❌ ??? | {sp_name} (Not found)")

            # Rate limit
            if (i+1) % 10 == 0: time.sleep(0.5)

        # --- 4. BATCHING ---
        unique_matches = {v['id']: v for v in matched_videos}.values() # Deduplicate by ID
        unique_ids = [v['id'] for v in unique_matches]
        
        self.logger.log_terminal(f"\n🚀 Sending {len(unique_ids)} songs to YouTube...")
        self.logger.log_file("=== BATCHING PHASE ===")
        self.logger.log_file(f"Total Unique Matches: {len(unique_ids)}")
        
        batch_size = 20
        total_batches = (len(unique_ids) + batch_size - 1) // batch_size
        
        for i in range(0, len(unique_ids), batch_size):
            batch_ids = unique_ids[i : i + batch_size]
            batch_num = i//batch_size + 1
            
            self.logger.log_file(f"Preparing Batch {batch_num}/{total_batches}")
            self.logger.log_file(f"  > IDs: {batch_ids}")
            
            self.logger.log_terminal(f"  📦 Batch {batch_num}/{total_batches}: Sending {len(batch_ids)} items...")
            
            try:
                response = self.youtube.ytmusic.add_playlist_items(target_yt_id, batch_ids)
                self.logger.log_file(f"  > API Response: {response}")
                
                # Verify Success in response
                success = False
                if isinstance(response, dict):
                    if 'status' in response and response['status'] == 'STATUS_SUCCEEDED':
                        success = True
                    elif 'playlistId' in response:
                        success = True
                        
                if success:
                    self.logger.log_terminal(f"     ✅ Success")
                else:
                    self.logger.log_terminal(f"     ⚠️ Check Logs")
                    # Track failures
                    for vid in batch_ids:
                        self.failed_to_add_songs.append({'id': vid, 'reason': f"Batch {batch_num} API Error"})
                        
            except Exception as e:
                self.logger.log_terminal(f"     ❌ Error: {e}")
                self.logger.log_file(f"  > CRITICAL BATCH ERROR: {e}", "ERROR")
                for vid in batch_ids:
                    self.failed_to_add_songs.append({'id': vid, 'reason': f"Exception: {str(e)}"})
            
            time.sleep(2)

        # --- 5. VERIFICATION & SUMMARY ---
        self.logger.log_terminal("\n🏁 Verifying...")
        time.sleep(2)
        final_count = 0
        try:
            pl = self.youtube.ytmusic.get_playlist(target_yt_id)
            final_count = int(pl.get('trackCount', len(pl.get('tracks', []))))
        except Exception as e:
            self.logger.log_file(f"Verification Failed: {e}", "ERROR")

        # --- LOG FILE SUMMARY SECTIONS ---
        self.logger.log_file("\n=== UNMATCHED SONGS REPORT ===")
        if self.unmatched_songs:
            for s in self.unmatched_songs:
                self.logger.log_file(f"- {s['name']} by {s['artist']} | Reason: {s['reason']} | Best Found: {s['best_match']}")
        else:
            self.logger.log_file("None. All songs matched.")

        self.logger.log_file("\n=== FAILED TO ADD REPORT ===")
        if self.failed_to_add_songs:
            for s in self.failed_to_add_songs:
                self.logger.log_file(f"- VideoID: {s['id']} | Reason: {s['reason']}")
        else:
            self.logger.log_file("None. All matched songs were processed successfully.")

        # --- FINAL TERMINAL OUTPUT ---
        self.logger.log_terminal("\n" + "="*30)
        self.logger.log_terminal(f"🎉 Sync Complete for '{source_name}'")
        self.logger.log_terminal(f"📊 Final YouTube Playlist Count: {final_count}")
        self.logger.log_terminal(f"📉 Unmatched Songs: {len(self.unmatched_songs)}")
        if self.failed_to_add_songs:
            self.logger.log_terminal(f"⚠️ Failed to Add: {len(self.failed_to_add_songs)} (Check logs)")
        self.logger.log_terminal("="*30)

if __name__ == "__main__":
    # --- UI ---
    print("\n🎵 Spotify -> YouTube Music Sync 🎵")
    log_choice = input("📝 Generate detailed log file? (y/n): ").lower()
    enable_logs = log_choice == 'y'
    
    # Init
    logger = SyncLogger(enable_logs)
    engine = SyncEngine(logger)
    
    # Auth
    if not engine.spotify.authenticate():
        logger.log_terminal("❌ Spotify Auth Failed")
        sys.exit(1)

    # Playlist Select
    playlists = engine.spotify.get_user_playlists()
    if not playlists:
        print("No Spotify playlists found.")
        sys.exit(0)
        
    print("\nAvailable Playlists:")
    for i, p in enumerate(playlists):
        print(f"{i+1}. {p['name']} ({p['tracks_total']} tracks)")
        
    try:
        p_idx = int(input("\nSelect Playlist #: ")) - 1
        sp_id = playlists[p_idx]['id']
    except:
        print("Invalid.")
        sys.exit(1)

    # Target Select
    print("\n1. Create NEW Playlist")
    print("2. Add to EXISTING Playlist")
    mode = input("Choice: ")
    
    target_id = None
    if mode == '2':
        yt_pls = engine.youtube.get_user_playlists()
        print("\nYouTube Playlists:")
        for i, p in enumerate(yt_pls):
             print(f"{i+1}. {p.get('title','?')} ({p.get('count',0)} tracks)")
        try:
             y_idx = int(input("Select #: ")) - 1
             target_id = yt_pls[y_idx]['playlistId']
        except:
             sys.exit(1)
             
    engine.sync_playlist(sp_id, target_id)