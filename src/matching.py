"""
Song matching module using fuzzy string matching.
Finds best matches between songs from different platforms.
"""

from typing import Dict, List, Optional, Tuple
from rapidfuzz import fuzz, process
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class MatchResult:
    """Result of a song matching operation."""
    matched: bool
    confidence: float
    match_data: Optional[Dict] = None
    reason: str = ""


class SongMatcher:
    """Handles fuzzy matching between songs from different platforms."""
    
    def __init__(
        self,
        title_weight: float = 0.6,
        artist_weight: float = 0.4,
        min_confidence: float = 85.0
    ):
        """
        Initialize the matcher.
        
        Args:
            title_weight: Weight for song title matching (0-1)
            artist_weight: Weight for artist matching (0-1)
            min_confidence: Minimum confidence score to consider a match (0-100)
        """
        self.title_weight = title_weight
        self.artist_weight = artist_weight
        self.min_confidence = min_confidence
        
        # Ensure weights sum to 1
        total_weight = title_weight + artist_weight
        self.title_weight /= total_weight
        self.artist_weight /= total_weight
    
    def calculate_similarity(
        self,
        source_title: str,
        source_artist: str,
        target_title: str,
        target_artist: str
    ) -> float:
        """
        Calculate weighted similarity score between two songs.
        
        Args:
            source_title: Title of source song
            source_artist: Artist of source song
            target_title: Title of target song
            target_artist: Artist of target song
        
        Returns:
            Similarity score (0-100)
        """
        # Use token_sort_ratio which handles word order variations
        title_score = fuzz.token_sort_ratio(
            source_title.lower(),
            target_title.lower()
        )
        
        artist_score = fuzz.token_sort_ratio(
            source_artist.lower(),
            target_artist.lower()
        )
        
        # Calculate weighted score
        weighted_score = (
            title_score * self.title_weight +
            artist_score * self.artist_weight
        )
        
        logger.debug(
            f"Similarity: '{source_title}' vs '{target_title}' = {title_score:.1f}, "
            f"'{source_artist}' vs '{target_artist}' = {artist_score:.1f}, "
            f"weighted = {weighted_score:.1f}"
        )
        
        return weighted_score
    
    def find_best_match(
        self,
        source_song: Dict,
        candidate_songs: List[Dict],
        source_title_key: str = "title",
        source_artist_key: str = "artist",
        target_title_key: str = "title",
        target_artist_key: str = "artist"
    ) -> MatchResult:
        """
        Find the best matching song from a list of candidates.
        
        Args:
            source_song: Source song dictionary
            candidate_songs: List of candidate song dictionaries
            source_title_key: Key for title in source_song
            source_artist_key: Key for artist in source_song
            target_title_key: Key for title in candidate songs
            target_artist_key: Key for artist in candidate songs
        
        Returns:
            MatchResult with best match information
        """
        if not candidate_songs:
            return MatchResult(
                matched=False,
                confidence=0.0,
                reason="No candidates provided"
            )
        
        source_title = source_song.get(source_title_key, "")
        source_artist = source_song.get(source_artist_key, "")
        
        if not source_title or not source_artist:
            return MatchResult(
                matched=False,
                confidence=0.0,
                reason="Missing source song metadata"
            )
        
        # Calculate similarity for each candidate
        best_score = 0.0
        best_match = None
        scores = []
        
        for candidate in candidate_songs:
            target_title = candidate.get(target_title_key, "")
            target_artist = candidate.get(target_artist_key, "")
            
            if not target_title or not target_artist:
                continue
            
            score = self.calculate_similarity(
                source_title, source_artist,
                target_title, target_artist
            )
            
            scores.append((score, candidate))
            
            if score > best_score:
                best_score = score
                best_match = candidate
        
        # Check if best match meets confidence threshold
        if best_score >= self.min_confidence and best_match:
            logger.info(
                f"Match found: '{source_title}' by '{source_artist}' -> "
                f"'{best_match.get(target_title_key)}' by "
                f"'{best_match.get(target_artist_key)}' "
                f"(confidence: {best_score:.1f}%)"
            )
            return MatchResult(
                matched=True,
                confidence=best_score,
                match_data=best_match,
                reason=f"Best match with {best_score:.1f}% confidence"
            )
        
        # Log top 3 candidates for debugging
        top_scores = sorted(scores, key=lambda x: x[0], reverse=True)[:3]
        logger.warning(
            f"No match found for '{source_title}' by '{source_artist}'. "
            f"Best score: {best_score:.1f}%. Top candidates: "
            + ", ".join([
                f"{s[1].get(target_title_key)} ({s[0]:.1f}%)"
                for s in top_scores
            ])
        )
        
        return MatchResult(
            matched=False,
            confidence=best_score,
            match_data=best_match,
            reason=f"Best match ({best_score:.1f}%) below threshold ({self.min_confidence}%)"
        )
    
    def match_playlists(
        self,
        source_tracks: List[Dict],
        target_search_func,
        source_title_key: str = "title",
        source_artist_key: str = "artist"
    ) -> Tuple[List[Dict], List[Dict]]:
        """
        Match all songs from source playlist to target platform.
        
        Args:
            source_tracks: List of source track dictionaries
            target_search_func: Function to search target platform (takes title, artist)
            source_title_key: Key for title in source tracks
            source_artist_key: Key for artist in source tracks
        
        Returns:
            Tuple of (matched_tracks, unmatched_tracks)
        """
        matched = []
        unmatched = []
        
        total = len(source_tracks)
        logger.info(f"Starting to match {total} tracks...")
        
        for idx, track in enumerate(source_tracks, 1):
            title = track.get(source_title_key, "")
            artist = track.get(source_artist_key, "")
            
            if not title or not artist:
                logger.warning(f"Track {idx}/{total}: Missing metadata, skipping")
                unmatched.append({
                    "source_track": track,
                    "reason": "Missing metadata"
                })
                continue
            
            logger.info(f"Matching {idx}/{total}: '{title}' by '{artist}'")
            
            try:
                # Search target platform
                candidates = target_search_func(title, artist)
                
                # Find best match
                result = self.find_best_match(
                    track,
                    candidates,
                    source_title_key=source_title_key,
                    source_artist_key=source_artist_key
                )
                
                if result.matched:
                    matched.append({
                        "source_track": track,
                        "target_track": result.match_data,
                        "confidence": result.confidence
                    })
                else:
                    unmatched.append({
                        "source_track": track,
                        "reason": result.reason,
                        "best_candidate": result.match_data,
                        "confidence": result.confidence
                    })
            
            except Exception as e:
                logger.error(f"Error matching track {idx}/{total}: {str(e)}")
                unmatched.append({
                    "source_track": track,
                    "reason": f"Search error: {str(e)}"
                })
        
        logger.info(
            f"Matching complete: {len(matched)}/{total} matched "
            f"({len(matched)/total*100:.1f}%), {len(unmatched)} unmatched"
        )
        
        return matched, unmatched


# Convenience function for quick matching
def match_song(
    source_title: str,
    source_artist: str,
    candidates: List[Dict],
    min_confidence: float = 85.0
) -> MatchResult:
    """
    Quick function to match a single song.
    
    Args:
        source_title: Title of source song
        source_artist: Artist of source song
        candidates: List of candidate song dictionaries
        min_confidence: Minimum confidence threshold
    
    Returns:
        MatchResult
    """
    matcher = SongMatcher(min_confidence=min_confidence)
    source_song = {"title": source_title, "artist": source_artist}
    return matcher.find_best_match(source_song, candidates)


def find_best_match(
    source_title: str,
    source_artist: str,
    target_title: str,
    target_artist: str
) -> float:
    """
    Calculate confidence score for a match between two songs.
    
    Args:
        source_title: Title of source song
        source_artist: Artist of source song
        target_title: Title of target song
        target_artist: Artist of target song
    
    Returns:
        Confidence score as a float between 0.0 and 1.0
    """
    matcher = SongMatcher()
    # Calculate similarity (returns 0-100)
    similarity = matcher.calculate_similarity(
        source_title, source_artist,
        target_title, target_artist
    )
    # Convert to 0.0-1.0 range
    return similarity / 100.0