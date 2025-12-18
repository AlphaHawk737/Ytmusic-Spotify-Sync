import json

try:
    # Read the client secret file
    with open('youtube_client_secret.json', 'r') as f:
        data = json.load(f)
    
    # Extract credentials
    if 'installed' in data:
        client_id = data['installed']['client_id']
        client_secret = data['installed']['client_secret']
        cred_type = "Desktop (installed)"
    elif 'web' in data:
        client_id = data['web']['client_id']
        client_secret = data['web']['client_secret']
        cred_type = "Web"
    else:
        print("❌ Could not find credentials in JSON file")
        print("File structure:")
        print(json.dumps(data, indent=2))
        exit(1)
    
    print("=" * 70)
    print("YouTube OAuth Credentials")
    print("=" * 70)
    print(f"\n✅ Credential Type: {cred_type}")
    print(f"\n📋 Client ID:\n{client_id}\n")
    print(f"🔑 Client Secret:\n{client_secret}\n")
    print("=" * 70)
    print("\nVerification:")
    print(f"  • Client ID ends with .apps.googleusercontent.com: {client_id.endswith('.apps.googleusercontent.com')}")
    print(f"  • Client Secret starts with GOCSPX-: {client_secret.startswith('GOCSPX-')}")
    print(f"  • Client ID length: {len(client_id)} characters")
    print(f"  • Client Secret length: {len(client_secret)} characters")
    print("=" * 70)
    print("\n📋 Copy these EXACT values when running: ytmusicapi oauth")
    print("=" * 70)
    
except FileNotFoundError:
    print("❌ Error: youtube_client_secret.json not found in current directory")
    print("Make sure the file is in the same folder where you're running this script")
except json.JSONDecodeError:
    print("❌ Error: youtube_client_secret.json is not valid JSON")
except Exception as e:
    print(f"❌ Unexpected error: {e}")