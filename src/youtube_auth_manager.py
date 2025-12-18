from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import pickle
import os
import json
from ytmusicapi import YTMusic

SCOPES = [
    'https://www.googleapis.com/auth/youtube',
    'https://www.googleapis.com/auth/youtube.readonly'
]

class YouTubeAuthManager:
    """
    Manages YouTube Music authentication using OAuth to generate browser headers
    """
    
    def __init__(self):
        self.creds = None
        self.token_file = 'youtube_token.pickle'
        self.headers_file = 'ytmusic_headers.json'
        self.client_secret_file = 'youtube_client_secret.json'
    
    def get_oauth_credentials(self):
        """Get or refresh OAuth credentials"""
        
        # Load existing credentials
        if os.path.exists(self.token_file):
            print("📂 Loading existing OAuth credentials...")
            with open(self.token_file, 'rb') as token:
                self.creds = pickle.load(token)
        
        # Refresh or get new credentials
        if not self.creds or not self.creds.valid:
            if self.creds and self.creds.expired and self.creds.refresh_token:
                print("🔄 Refreshing expired OAuth token...")
                self.creds.refresh(Request())
            else:
                print("🔐 Starting OAuth authentication flow...")
                print("🌐 Browser will open for authorization...")
                
                flow = InstalledAppFlow.from_client_secrets_file(
                    self.client_secret_file,
                    SCOPES
                )
                self.creds = flow.run_local_server(port=8080)
            
            # Save credentials
            print("💾 Saving OAuth credentials...")
            with open(self.token_file, 'wb') as token:
                pickle.dump(self.creds, token)
            
            print("✅ OAuth credentials updated!")
        else:
            print("✅ OAuth credentials are valid!")
        
        return self.creds
    
    def generate_headers(self):
        """Generate browser headers from OAuth credentials"""
        
        # Get valid OAuth credentials
        creds = self.get_oauth_credentials()
        
        # Create headers in ytmusicapi format
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "*/*",
            "Accept-Language": "en-US,en;q=0.5",
            "Content-Type": "application/json",
            "X-Goog-AuthUser": "0",
            "x-origin": "https://music.youtube.com",
            "Authorization": f"Bearer {creds.token}"
        }
        
        # Save headers
        print(f"💾 Saving headers to {self.headers_file}...")
        with open(self.headers_file, 'w') as f:
            json.dump(headers, f, indent=2)
        
        print("✅ Headers generated successfully!")
        return headers
    
    def get_ytmusic_instance(self):
        """Get authenticated YTMusic instance with fresh headers"""
        
        # Generate fresh headers
        self.generate_headers()
        
        # Create YTMusic instance
        try:
            ytmusic = YTMusic(self.headers_file)
            print("✅ YouTube Music instance created successfully!")
            return ytmusic
        except Exception as e:
            print(f"❌ Error creating YTMusic instance: {e}")
            raise
    
    def refresh_if_needed(self):
        """Check if headers need refresh and update them"""
        
        if not os.path.exists(self.token_file):
            print("⚠️ No credentials found, generating new ones...")
            return self.generate_headers()
        
        # Load credentials
        with open(self.token_file, 'rb') as token:
            creds = pickle.load(token)
        
        # Check if expired
        if not creds.valid:
            print("🔄 Credentials expired, refreshing...")
            return self.generate_headers()
        else:
            print("✅ Credentials still valid, no refresh needed")
            return None


# Test the auth manager
if __name__ == "__main__":
    print("\n" + "="*70)
    print("YouTube Music Auth Manager - OAuth to Headers Converter")
    print("="*70 + "\n")
    
    auth_manager = YouTubeAuthManager()
    
    print("\n[1/2] Generating authentication headers...")
    auth_manager.generate_headers()
    
    print("\n[2/2] Testing YTMusic instance...")
    ytmusic = auth_manager.get_ytmusic_instance()
    
    # Quick test
    try:
        print("\n[TEST] Searching for a song...")
        results = ytmusic.search("Bohemian Rhapsody Queen", filter="songs", limit=1)
        if results:
            print(f"✅ Search working! Found: {results[0]['title']}")
        else:
            print("⚠️ Search returned no results")
    except Exception as e:
        print(f"❌ Search failed: {e}")
    
    print("\n" + "="*70)
    print("✅ Auth Manager test complete!")
    print("="*70)