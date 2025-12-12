"""
Configuration management for Playlist Sync application.
Loads environment variables and provides configuration to other modules.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Get the project root directory (parent of src folder)
PROJECT_ROOT = Path(__file__).parent.parent

# Load environment variables from .env file
load_dotenv(PROJECT_ROOT / ".env")


class Config:
    """
    Configuration class that loads all settings from environment variables.
    """
    
    # Spotify Configuration
    SPOTIFY_CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
    SPOTIFY_CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")
    SPOTIFY_REDIRECT_URI = os.getenv("SPOTIFY_REDIRECT_URI", "http://localhost:8888/callback")
    
    # YouTube Music Configuration
    YOUTUBE_MUSIC_HEADERS_FILE = os.getenv("YOUTUBE_MUSIC_HEADERS_FILE", "youtube_headers_auth.json")
    
    # Application Settings
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    MATCHING_THRESHOLD = int(os.getenv("MATCHING_THRESHOLD", "85"))
    
    @classmethod
    def validate(cls):
        """
        Validates that all required configuration values are set.
        Raises ValueError if any required values are missing.
        """
        required_vars = {
            "SPOTIFY_CLIENT_ID": cls.SPOTIFY_CLIENT_ID,
            "SPOTIFY_CLIENT_SECRET": cls.SPOTIFY_CLIENT_SECRET,
        }
        
        missing = [key for key, value in required_vars.items() if not value]
        
        if missing:
            raise ValueError(
                f"Missing required environment variables: {', '.join(missing)}\n"
                f"Please set them in your .env file."
            )
    
    @classmethod
    def get_youtube_headers_path(cls):
        """
        Returns the full path to the YouTube Music headers file.
        """
        return PROJECT_ROOT / cls.YOUTUBE_MUSIC_HEADERS_FILE


# Convenience function to get config instance
def get_config():
    """
    Returns the Config class and validates configuration.
    """
    Config.validate()
    return Config