"""
Quick test to verify configuration is loading correctly.
"""

from src.config import Config

try:
    print("Testing configuration loading...\n")
    
    # Try to load config
    print(f"Spotify Client ID: {Config.SPOTIFY_CLIENT_ID}")
    print(f"Spotify Client Secret: {Config.SPOTIFY_CLIENT_SECRET}")
    print(f"Spotify Redirect URI: {Config.SPOTIFY_REDIRECT_URI}")
    print(f"YouTube Headers File: {Config.YOUTUBE_MUSIC_HEADERS_FILE}")
    print(f"Log Level: {Config.LOG_LEVEL}")
    print(f"Matching Threshold: {Config.MATCHING_THRESHOLD}")
    
    print("\n✅ Configuration loaded successfully!")
    
    # Test validation (this will fail until you add real credentials)
    print("\nTesting validation...")
    Config.validate()
    print("✅ Validation passed!")
    
except ValueError as e:
    print(f"\n⚠️  Validation failed (expected until you add real credentials):")
    print(f"   {e}")
except Exception as e:
    print(f"\n❌ Error: {e}")