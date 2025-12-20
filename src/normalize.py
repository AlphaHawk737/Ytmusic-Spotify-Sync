"""
Song metadata normalization module.

Handles cleaning and standardizing song/artist names from different platforms
to enable accurate matching between Spotify and YouTube Music.
"""

import re
import unicodedata
from typing import Dict, List, Optional
import logging

# Set up logging
logger = logging.getLogger(__name__)


class SongNormalizer:
    """Handles normalization of song and artist metadata."""
    
    # Common suffixes to remove from song titles
    VIDEO_SUFFIXES = [
        r'\(official video\)',
        r'\(official music video\)',
        r'\(official audio\)',
        r'\(lyric video\)',
        r'\(lyrics\)',
        r'\[official video\]',
        r'\[official music video\]',
        r'\[official audio\]',
        r'\[lyric video\]',
        r'\[lyrics\]',
        r'- official video',
        r'- official music video',
        r'- official audio',
        r'- lyric video',
        r'- lyrics',
    ]
    
    # Featuring variations to standardize
    FEATURING_PATTERNS = [
        r'\bfeat\.?\b',
        r'\bft\.?\b',
        r'\bfeaturing\b',
        r'\bwith\b',
    ]
    
    def __init__(self):
        """Initialize the normalizer with compiled regex patterns."""
        try:
            # Compile video suffix patterns for efficiency
            self.video_suffix_pattern = re.compile(
                '|'.join(self.VIDEO_SUFFIXES),
                re.IGNORECASE
            )
            
            # Compile featuring patterns
            self.featuring_pattern = re.compile(
                '|'.join(self.FEATURING_PATTERNS),
                re.IGNORECASE
            )
            
            logger.info("SongNormalizer initialized successfully")
            
        except Exception as e:
            logger.error(f"Error initializing SongNormalizer: {e}")
            raise
    
    def normalize_text(self, text: str) -> str:
        """
        Apply basic text normalization.
        
        Args:
            text: Raw text to normalize
            
        Returns:
            Normalized text
            
        Raises:
            ValueError: If text is None or empty
        """
        if not text:
            raise ValueError("Text cannot be None or empty")
        
        try:
            # Convert to lowercase
            normalized = text.lower()
            
            # Remove accents and diacritics
            normalized = self._remove_accents(normalized)
            
            # Remove special characters but keep spaces, hyphens, and alphanumeric
            normalized = re.sub(r'[^a-z0-9\s\-]', '', normalized)
            
            # Normalize whitespace (multiple spaces to single space)
            normalized = re.sub(r'\s+', ' ', normalized)
            
            # Trim leading/trailing whitespace
            normalized = normalized.strip()
            
            return normalized
            
        except Exception as e:
            logger.error(f"Error normalizing text '{text}': {e}")
            raise
    
    def _remove_accents(self, text: str) -> str:
        """
        Remove accents and diacritical marks from text.
        
        Example: 'Beyoncé' -> 'beyonce'
        
        Args:
            text: Text with potential accents
            
        Returns:
            Text without accents
        """
        try:
            # Normalize to NFD (decomposed form)
            nfd = unicodedata.normalize('NFD', text)
            
            # Filter out combining characters (accents)
            return ''.join(
                char for char in nfd
                if unicodedata.category(char) != 'Mn'
            )
            
        except Exception as e:
            logger.error(f"Error removing accents from '{text}': {e}")
            return text  # Return original if error
    
    def remove_video_suffixes(self, title: str) -> str:
        """
        Remove common video-related suffixes from song titles.
        
        Args:
            title: Song title potentially with video suffixes
            
        Returns:
            Title with suffixes removed
        """
        if not title:
            return title
        
        try:
            # Remove all video suffix patterns
            cleaned = self.video_suffix_pattern.sub('', title)
            
            # Clean up any resulting double spaces or trailing dashes
            cleaned = re.sub(r'\s+', ' ', cleaned)
            cleaned = re.sub(r'\s*-\s*$', '', cleaned)
            cleaned = cleaned.strip()
            
            return cleaned
            
        except Exception as e:
            logger.error(f"Error removing video suffixes from '{title}': {e}")
            return title
    
    def normalize_featuring(self, text: str) -> str:
        """
        Standardize featuring artist notation.
        
        Converts 'feat.', 'ft.', 'featuring', 'with' to 'feat'
        
        Args:
            text: Text with potential featuring notation
            
        Returns:
            Text with standardized featuring notation
        """
        if not text:
            return text
        
        try:
            # Replace all featuring variations with 'feat'
            normalized = self.featuring_pattern.sub('feat', text)
            
            # Clean up spacing around 'feat'
            normalized = re.sub(r'\s+feat\s+', ' feat ', normalized)
            
            return normalized
            
        except Exception as e:
            logger.error(f"Error normalizing featuring in '{text}': {e}")
            return text
    
    def extract_main_artists(self, artists: str) -> str:
        """
        Extract main artist(s) before featuring notation.
        
        Example: "Drake feat. Rihanna" -> "Drake"
        
        Args:
            artists: Full artist string
            
        Returns:
            Main artist(s) only
        """
        if not artists:
            return artists
        
        try:
            # Split on featuring keywords
            parts = re.split(
                r'\s+(?:feat\.?|ft\.?|featuring|with)\s+',
                artists,
                flags=re.IGNORECASE,
                maxsplit=1
            )
            
            return parts[0].strip() if parts else artists
            
        except Exception as e:
            logger.error(f"Error extracting main artists from '{artists}': {e}")
            return artists
    
    def normalize_song(
        self,
        title: str,
        artist: str,
        remove_featuring: bool = False
    ) -> Dict[str, str]:
        """
        Fully normalize a song's metadata.
        
        Args:
            title: Song title
            artist: Artist name(s)
            remove_featuring: If True, remove featuring artists
            
        Returns:
            Dictionary with normalized 'title' and 'artist'
            
        Raises:
            ValueError: If title or artist is None/empty
        """
        if not title or not artist:
            raise ValueError("Both title and artist must be provided")
        
        try:
            # Step 1: Remove video suffixes from title
            normalized_title = self.remove_video_suffixes(title)
            
            # Step 2: Normalize featuring notation
            normalized_title = self.normalize_featuring(normalized_title)
            normalized_artist = self.normalize_featuring(artist)
            
            # Step 3: Extract main artists if requested
            if remove_featuring:
                normalized_artist = self.extract_main_artists(normalized_artist)
            
            # Step 4: Apply basic text normalization
            normalized_title = self.normalize_text(normalized_title)
            normalized_artist = self.normalize_text(normalized_artist)
            
            result = {
                'title': normalized_title,
                'artist': normalized_artist
            }
            
            logger.debug(
                f"Normalized '{title}' by '{artist}' -> "
                f"'{result['title']}' by '{result['artist']}'"
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Error normalizing song '{title}' by '{artist}': {e}")
            raise
    
    def create_search_string(
        self,
        title: str,
        artist: str,
        album: Optional[str] = None
    ) -> str:
        """
        Create a normalized search string for matching.
        
        Args:
            title: Song title
            artist: Artist name
            album: Optional album name
            
        Returns:
            Formatted search string
        """
        try:
            # Normalize the song
            normalized = self.normalize_song(title, artist, remove_featuring=True)
            
            # Build search string
            search_parts = [
                normalized['artist'],
                normalized['title']
            ]
            
            # Optionally add album
            if album:
                normalized_album = self.normalize_text(album)
                search_parts.append(normalized_album)
            
            search_string = ' '.join(search_parts)
            
            logger.debug(f"Created search string: '{search_string}'")
            
            return search_string
            
        except Exception as e:
            logger.error(
                f"Error creating search string for '{title}' by '{artist}': {e}"
            )
            raise


def normalize_song_simple(title: str, artist: str) -> Dict[str, str]:
    """
    Convenience function for simple song normalization.
    
    Args:
        title: Song title
        artist: Artist name
    
    Returns:
        Dictionary with normalized 'title' and 'artist'
    """
    normalizer = SongNormalizer()
    return normalizer.normalize_song(title, artist)


def normalize_track_name(track_name: str) -> str:
    """
    Normalize a track name for matching.
    
    Args:
        track_name: Original track name
    
    Returns:
        Normalized track name string
    """
    if not track_name:
        return ""
    try:
        normalizer = SongNormalizer()
        # Remove video suffixes, normalize featuring, then normalize text
        cleaned = normalizer.remove_video_suffixes(track_name)
        cleaned = normalizer.normalize_featuring(cleaned)
        return normalizer.normalize_text(cleaned)
    except Exception:
        # Fallback to simple lowercase if normalization fails
        return track_name.lower().strip()


def normalize_artist_name(artist_name: str) -> str:
    """
    Normalize an artist name for matching.
    
    Args:
        artist_name: Original artist name(s)
    
    Returns:
        Normalized artist name string
    """
    if not artist_name:
        return ""
    try:
        normalizer = SongNormalizer()
        # Normalize featuring notation, then normalize text
        cleaned = normalizer.normalize_featuring(artist_name)
        return normalizer.normalize_text(cleaned)
    except Exception:
        # Fallback to simple lowercase if normalization fails
        return artist_name.lower().strip()


# Example usage and testing
if __name__ == "__main__":
    # Set up logging for testing
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Create normalizer instance
    normalizer = SongNormalizer()
    
    # Test cases
    test_songs = [
        {
            'title': 'Let It Be (Official Video)',
            'artist': 'The Beatles',
        },
        {
            'title': 'Work',
            'artist': 'Drake feat. Rihanna',
        },
        {
            'title': 'Back In Black [Official Audio]',
            'artist': 'AC/DC',
        },
        {
            'title': 'Despacito - Remix',
            'artist': 'Luis Fonsi ft. Daddy Yankee, Justin Bieber',
        },
    ]
    
    print("\n" + "="*80)
    print("SONG NORMALIZATION TESTS")
    print("="*80 + "\n")
    
    for song in test_songs:
        print(f"Original: '{song['title']}' by '{song['artist']}'")
        
        try:
            normalized = normalizer.normalize_song(
                song['title'],
                song['artist'],
                remove_featuring=False
            )
            print(f"Normalized: '{normalized['title']}' by '{normalized['artist']}'")
            
            search_string = normalizer.create_search_string(
                song['title'],
                song['artist']
            )
            print(f"Search String: '{search_string}'")
            
        except Exception as e:
            print(f"Error: {e}")
        
        print("-" * 80 + "\n")