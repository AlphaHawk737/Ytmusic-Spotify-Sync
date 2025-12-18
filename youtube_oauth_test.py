from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import pickle
import os

# Scopes for YouTube Music access
SCOPES = [
    'https://www.googleapis.com/auth/youtube',
    'https://www.googleapis.com/auth/youtube.readonly'
]

def authenticate_youtube():
    """
    Authenticate with YouTube using OAuth 2.0
    """
    creds = None
    token_file = 'youtube_token.pickle'
    
    # Load existing credentials if available
    if os.path.exists(token_file):
        with open(token_file, 'rb') as token:
            creds = pickle.load(token)
    
    # If no valid credentials, let user log in
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'youtube_client_secret.json',  # The file you downloaded
                SCOPES
            )
            creds = flow.run_local_server(port=8080)
        
        # Save credentials for next time
        with open(token_file, 'wb') as token:
            pickle.dump(creds, token)
    
    print("✅ Successfully authenticated with YouTube!")
    print(f"Access Token: {creds.token[:50]}...")
    return creds

if __name__ == "__main__":
    authenticate_youtube()