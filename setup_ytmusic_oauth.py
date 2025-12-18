import json
import os

def setup_ytmusic_oauth():
    """
    Helper script to set up ytmusicapi OAuth credentials
    """
    print("\n" + "="*70)
    print("YouTube Music OAuth Setup Helper")
    print("="*70 + "\n")
    
    # Check if client secret exists
    if not os.path.exists('youtube_client_secret.json'):
        print("❌ youtube_client_secret.json not found!")
        print("Please download it from Google Cloud Console")
        return
    
    # Read and display credentials
    with open('youtube_client_secret.json', 'r') as f:
        data = json.load(f)
    
    if 'installed' in data:
        client_id = data['installed']['client_id']
        client_secret = data['installed']['client_secret']
    else:
        print("❌ Invalid client_secret.json format")
        return
    
    print("✅ Found credentials in youtube_client_secret.json\n")
    print("="*70)
    print("INSTRUCTIONS:")
    print("="*70)
    print("\n1. Run this command in PowerShell:\n")
    print("   ytmusicapi oauth\n")
    print("2. When prompted for 'Client ID', paste this:\n")
    print(f"   {client_id}\n")
    print("3. When prompted for 'Client Secret', paste this:\n")
    print(f"   {client_secret}\n")
    print("4. Browser will open - log in and authorize")
    print("5. File 'oauth.json' will be created\n")
    print("="*70)
    
    # Also create a version that might work with ytmusicapi setup
    print("\n🔧 Attempting automatic setup...\n")
    
    try:
        from ytmusicapi import setup_oauth
        
        # This should trigger the OAuth flow
        setup_oauth(
            filepath='oauth.json',
            open_browser=True
        )
        print("\n✅ OAuth setup complete!")
        print("📁 File 'oauth.json' created successfully")
        
    except ImportError:
        print("⚠️ setup_oauth not available in your ytmusicapi version")
        print("Please run 'ytmusicapi oauth' manually with the credentials above")
    except Exception as e:
        print(f"⚠️ Automatic setup failed: {e}")
        print("\nPlease run 'ytmusicapi oauth' manually with the credentials above")

if __name__ == "__main__":
    setup_ytmusic_oauth()