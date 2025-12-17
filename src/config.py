"""
Configuration Management
Loads API credentials and settings from environment variables
"""

import os
from dotenv import load_dotenv
from pathlib import Path

# Get the project root directory
BASE_DIR = Path(__file__).resolve().parent.parent

# Load environment variables from .env file
load_dotenv(dotenv_path=BASE_DIR / '.env')


class Config:
    """Application configuration loaded from environment variables"""
    
    # Spotify Configuration
    SPOTIFY_CLIENT_ID = os.getenv('SPOTIFY_CLIENT_ID')
    SPOTIFY_CLIENT_SECRET = os.getenv('SPOTIFY_CLIENT_SECRET')
    SPOTIFY_REDIRECT_URI = os.getenv('SPOTIFY_REDIRECT_URI', 'http://127.0.0.1:8888/callback')
    
    # YouTube Music Configuration (we'll add this later in Phase 3-Step 6)
    YOUTUBE_HEADERS_FILE = os.getenv('YOUTUBE_HEADERS_FILE', 'youtube_auth.json')
    
    # Application Settings
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    
    # Database Configuration (for future use in Phase 8-Step 14)
    DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///sync_history.db')
    
    # Sync Configuration (for future use)
    DEFAULT_MATCH_THRESHOLD = float(os.getenv('DEFAULT_MATCH_THRESHOLD', '0.85'))  # 85% similarity
    MAX_SEARCH_RESULTS = int(os.getenv('MAX_SEARCH_RESULTS', '5'))
    
    @classmethod
    def validate_spotify(cls):
        """Validate that Spotify configuration is present"""
        missing = []
        
        if not cls.SPOTIFY_CLIENT_ID:
            missing.append('SPOTIFY_CLIENT_ID')
        if not cls.SPOTIFY_CLIENT_SECRET:
            missing.append('SPOTIFY_CLIENT_SECRET')
        
        if missing:
            raise ValueError(f"Missing required Spotify environment variables: {', '.join(missing)}")
        
        return True
    
    @classmethod
    def validate_youtube(cls):
        """Validate that YouTube Music configuration is present"""
        headers_path = BASE_DIR / cls.YOUTUBE_HEADERS_FILE
        
        if not headers_path.exists():
            raise ValueError(f"YouTube headers file not found at: {headers_path}")
        
        return True
    
    @classmethod
    def validate_all(cls):
        """Validate all required configuration"""
        try:
            cls.validate_spotify()
            cls.validate_youtube()
            return True
        except ValueError as e:
            raise ValueError(f"Configuration validation failed: {e}")
    
    @classmethod
    def get_base_dir(cls):
        """Get the project base directory"""
        return BASE_DIR
    
    @classmethod
    def get_youtube_headers_path(cls):
        """Get full path to YouTube headers file"""
        return BASE_DIR / cls.YOUTUBE_HEADERS_FILE


# Create a singleton instance for easy importing
config = Config()


# Helper function to check if configuration is ready
def is_spotify_configured():
    """Check if Spotify is configured"""
    try:
        Config.validate_spotify()
        return True
    except ValueError:
        return False


def is_youtube_configured():
    """Check if YouTube Music is configured"""
    try:
        Config.validate_youtube()
        return True
    except ValueError:
        return False


def get_config_status():
    """Get status of all configuration"""
    status = {
        'spotify': is_spotify_configured(),
        'youtube': is_youtube_configured(),
        'base_dir': str(Config.get_base_dir())
    }
    return status


# Display configuration status when imported (for debugging)
if __name__ == "__main__":
    print("=" * 60)
    print("CONFIGURATION STATUS")
    print("=" * 60)
    
    status = get_config_status()
    
    print(f"\nBase Directory: {status['base_dir']}")
    print(f"\nSpotify Configured: {'✓' if status['spotify'] else '✗'}")
    if status['spotify']:
        print(f"  - Client ID: {config.SPOTIFY_CLIENT_ID[:10]}...")
        print(f"  - Redirect URI: {config.SPOTIFY_REDIRECT_URI}")
    else:
        print("  - Missing: SPOTIFY_CLIENT_ID and/or SPOTIFY_CLIENT_SECRET in .env")
    
    print(f"\nYouTube Music Configured: {'✓' if status['youtube'] else '✗'}")
    if status['youtube']:
        print(f"  - Headers File: {config.YOUTUBE_HEADERS_FILE}")
    else:
        print(f"  - Missing: {config.YOUTUBE_HEADERS_FILE} file")
    
    print(f"\nLog Level: {config.LOG_LEVEL}")
    print(f"Match Threshold: {config.DEFAULT_MATCH_THRESHOLD}")
    print(f"Max Search Results: {config.MAX_SEARCH_RESULTS}")
    print("\n" + "=" * 60)