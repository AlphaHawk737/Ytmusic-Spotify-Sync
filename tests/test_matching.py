"""
Test script for the matching module.
Run this to see how the fuzzy matching works.
Run from project root with: python -m tests.test_matching
"""

import logging
from src.matching import match_song

# Set up logging to see what's happening
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s: %(message)s'
)

def test_exact_match():
    """Test when song names are exactly the same."""
    print("\n" + "="*60)
    print("TEST 1: Exact Match")
    print("="*60)
    
    source_title = "Bohemian Rhapsody"
    source_artist = "Queen"
    
    candidates = [
        {"title": "Bohemian Rhapsody", "artist": "Queen", "id": "yt_123"},
        {"title": "We Will Rock You", "artist": "Queen", "id": "yt_456"},
    ]
    
    result = match_song(source_title, source_artist, candidates)
    
    print(f"\nSource: '{source_title}' by '{source_artist}'")
    print(f"Match found: {result.matched}")
    print(f"Confidence: {result.confidence:.1f}%")
    if result.match_data:
        print(f"Matched to: '{result.match_data['title']}' by '{result.match_data['artist']}'")


def test_fuzzy_match():
    """Test when song names have slight variations."""
    print("\n" + "="*60)
    print("TEST 2: Fuzzy Match (with variations)")
    print("="*60)
    
    source_title = "Bohemian Rhapsody"
    source_artist = "Queen"
    
    # YouTube Music often has these variations
    candidates = [
        {
            "title": "Bohemian Rhapsody (Remastered 2011)",
            "artist": "Queen Official",
            "id": "yt_123"
        },
        {
            "title": "Bohemian Rhapsody - Live",
            "artist": "Queen",
            "id": "yt_456"
        },
        {
            "title": "We Are The Champions",
            "artist": "Queen",
            "id": "yt_789"
        }
    ]
    
    result = match_song(source_title, source_artist, candidates)
    
    print(f"\nSource: '{source_title}' by '{source_artist}'")
    print(f"Match found: {result.matched}")
    print(f"Confidence: {result.confidence:.1f}%")
    if result.match_data:
        print(f"Matched to: '{result.match_data['title']}' by '{result.match_data['artist']}'")


def test_no_match():
    """Test when no good match exists."""
    print("\n" + "="*60)
    print("TEST 3: No Match (completely different songs)")
    print("="*60)
    
    source_title = "Bohemian Rhapsody"
    source_artist = "Queen"
    
    candidates = [
        {"title": "Shape of You", "artist": "Ed Sheeran", "id": "yt_123"},
        {"title": "Blinding Lights", "artist": "The Weeknd", "id": "yt_456"},
    ]
    
    result = match_song(source_title, source_artist, candidates, min_confidence=85.0)
    
    print(f"\nSource: '{source_title}' by '{source_artist}'")
    print(f"Match found: {result.matched}")
    print(f"Confidence: {result.confidence:.1f}%")
    print(f"Reason: {result.reason}")


def test_word_order():
    """Test when words are in different order."""
    print("\n" + "="*60)
    print("TEST 4: Different Word Order")
    print("="*60)
    
    source_title = "Stairway to Heaven"
    source_artist = "Led Zeppelin"
    
    candidates = [
        {
            "title": "Heaven to Stairway",  # Words reversed
            "artist": "Led Zeppelin",
            "id": "yt_123"
        },
        {
            "title": "Stairway to Heaven",  # Correct
            "artist": "Led Zeppelin",
            "id": "yt_456"
        }
    ]
    
    result = match_song(source_title, source_artist, candidates)
    
    print(f"\nSource: '{source_title}' by '{source_artist}'")
    print(f"Match found: {result.matched}")
    print(f"Confidence: {result.confidence:.1f}%")
    if result.match_data:
        print(f"Matched to: '{result.match_data['title']}' by '{result.match_data['artist']}'")


def test_custom_confidence():
    """Test with different confidence thresholds."""
    print("\n" + "="*60)
    print("TEST 5: Custom Confidence Threshold")
    print("="*60)
    
    source_title = "Bohemian Rhapsody"
    source_artist = "Queen"
    
    candidates = [
        {
            "title": "Bohemian Rhapsody (Live Aid 1985)",
            "artist": "Queen + Paul Rodgers",
            "id": "yt_123"
        }
    ]
    
    # Try with default threshold (85%)
    result_strict = match_song(source_title, source_artist, candidates, min_confidence=85.0)
    print(f"\nWith 85% threshold:")
    print(f"  Match found: {result_strict.matched}, Confidence: {result_strict.confidence:.1f}%")
    
    # Try with lower threshold (70%)
    result_relaxed = match_song(source_title, source_artist, candidates, min_confidence=70.0)
    print(f"\nWith 70% threshold:")
    print(f"  Match found: {result_relaxed.matched}, Confidence: {result_relaxed.confidence:.1f}%")


if __name__ == "__main__":
    print("\n" + "="*60)
    print("FUZZY MATCHING TESTS")
    print("="*60)
    print("Testing the song matching algorithm with various scenarios...")
    
    test_exact_match()
    test_fuzzy_match()
    test_no_match()
    test_word_order()
    test_custom_confidence()
    
    print("\n" + "="*60)
    print("TESTS COMPLETE")
    print("="*60)
    print("\nKey Takeaways:")
    print("- Exact matches get 100% confidence")
    print("- Variations like '(Remastered)' still match well (85-95%)")
    print("- Completely different songs score low (<50%)")
    print("- Token sort handles word order changes")
    print("- You can adjust min_confidence threshold based on your needs")