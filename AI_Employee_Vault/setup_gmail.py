"""
Gmail API Setup Script

Setup Gmail API for AI Employee.

Usage:
    python setup_gmail.py
"""

import sys
from pathlib import Path


def setup_gmail(vault_path: str = ".", credentials_file: str = None):
    """Setup Gmail API authorization"""
    vault_path = Path(vault_path).resolve()
    
    # Find credentials file
    if credentials_file:
        creds_path = Path(credentials_file).resolve()
    else:
        possible_paths = [
            vault_path / "credentials.json",
            vault_path.parent / "credentials.json",
            Path.cwd() / "credentials.json"
        ]
        
        for path in possible_paths:
            if path.exists():
                creds_path = path
                break
        else:
            print("❌ credentials.json not found!")
            print("\nDownload from: https://developers.google.com/gmail/api/quickstart/python")
            print("Then run: python setup_gmail.py --credentials path/to/credentials.json")
            return False
    
    if not creds_path.exists():
        print(f"❌ credentials.json not found at: {creds_path}")
        return False
    
    print(f"✓ Found credentials: {creds_path}")
    
    # Create credentials directory
    creds_dir = vault_path / "credentials"
    creds_dir.mkdir(parents=True, exist_ok=True)
    
    # Copy credentials
    import shutil
    vault_creds = creds_dir / "gmail_credentials.json"
    shutil.copy2(creds_path, vault_creds)
    print(f"✓ Copied credentials to: {vault_creds}")
    
    try:
        from google.oauth2.credentials import Credentials
        from google_auth_oauthlib.flow import InstalledAppFlow
        from googleapiclient.discovery import build
        from google.auth.transport.requests import Request
        import pickle
        
        SCOPES = [
            'https://www.googleapis.com/auth/gmail.readonly',
            'https://www.googleapis.com/auth/gmail.compose',
            'https://www.googleapis.com/auth/gmail.send'
        ]
        token_path = creds_dir / "gmail_token.pickle"
        creds = None

        if token_path.exists():
            print("⚠️  Existing token found. Deleting to refresh with send permissions...")
            token_path.unlink()
            print("   Old token deleted.")

        if not creds or not creds.valid:
            print("\n🌐 Opening browser for authorization...")
            print("   Please GRANT all requested permissions (including Send access)")
            flow = InstalledAppFlow.from_client_secrets_file(
                str(creds_path), SCOPES
            )
            creds = flow.run_local_server(port=8080, open_browser=True)
            print("✓ Authorization successful!")

        with open(token_path, 'wb') as f:
            pickle.dump(creds, f)
        print(f"✓ Token saved to: {token_path}")

        # Verify scopes in token
        print(f"\n   Granted scopes: {creds.scopes}")
        
        # Test connection
        service = build('gmail', 'v1', credentials=creds)
        profile = service.users().getProfile(userId='me').execute()
        print(f"\n✅ Gmail API setup complete!")
        print(f"   Connected to: {profile['emailAddress']}")
        print(f"   Total messages: {profile['messagesTotal']}")
        
        return True
        
    except ImportError as e:
        print(f"\n❌ Missing dependencies: {e}")
        print("\nInstall: pip install google-api-python-client google-auth-oauthlib")
        return False
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return False


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='Setup Gmail API')
    parser.add_argument('--vault-path', type=str, default='.')
    parser.add_argument('--credentials', type=str, default=None)
    
    args = parser.parse_args()
    
    print("="*60)
    print("Gmail API Setup for AI Employee")
    print("="*60 + "\n")
    
    success = setup_gmail(vault_path=args.vault_path, credentials_file=args.credentials)
    
    if not success:
        sys.exit(1)
