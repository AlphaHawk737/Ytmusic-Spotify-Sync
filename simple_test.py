print("Test starting...")

try:
    print("Attempting to import dotenv...")
    from dotenv import load_dotenv
    print("✅ dotenv imported successfully!")
    
    print("\nAttempting to import config...")
    from src.config import Config
    print("✅ config imported successfully!")
    
    print("\nTrying to access config values...")
    print(f"Spotify Client ID: {Config.SPOTIFY_CLIENT_ID}")
    print(f"Log Level: {Config.LOG_LEVEL}")
    
    print("\n✅ Everything works!")
    
except ImportError as e:
    print(f"❌ Import Error: {e}")
except Exception as e:
    print(f"❌ Error: {e}")

print("\nTest complete.")