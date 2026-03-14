from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from base_watcher import BaseWatcher
from datetime import datetime
import time
from pathlib import Path
import logging


class GmailWatcher(BaseWatcher):
    def __init__(self, vault_path: str, credentials_path: str):
        super().__init__(vault_path, check_interval=120)  # Check every 2 minutes
        self.creds = Credentials.from_authorized_user_file(credentials_path)
        self.service = build('gmail', 'v1', credentials=self.creds)
        self.processed_ids = set()

    def check_for_updates(self) -> list:
        """Check Gmail for new important/unread messages"""
        try:
            results = self.service.users().messages().list(
                userId='me', q='is:unread is:important'
            ).execute()
            messages = results.get('messages', [])
            # Filter messages that haven't been processed yet
            new_messages = [m for m in messages if m['id'] not in self.processed_ids]
            return new_messages
        except Exception as e:
            self.logger.error(f"Error checking Gmail: {e}")
            return []

    def create_action_file(self, message) -> Path:
        """Create a markdown file in Needs_Action folder for the email"""
        try:
            msg = self.service.users().messages().get(
                userId='me', id=message['id']
            ).execute()

            # Extract headers
            headers = {h['name']: h['value'] for h in msg['payload']['headers']}

            # Get the email body (try to extract text from payload)
            body = "Email content not accessible via API"
            if 'parts' in msg['payload']:
                for part in msg['payload']['parts']:
                    if part['mimeType'] == 'text/plain':
                        import base64
                        body = base64.urlsafe_b64decode(part['body']['data']).decode('utf-8')
                        break
            elif 'body' in msg['payload'] and 'data' in msg['payload']['body']:
                import base64
                body = base64.urlsafe_b64decode(msg['payload']['body']['data']).decode('utf-8')

            content = f'''---
type: email
from: {headers.get('From', 'Unknown')}
subject: {headers.get('Subject', 'No Subject')}
received: {datetime.now().isoformat()}
priority: high
status: pending
---

## Email Content
{body}

## Suggested Actions
- [ ] Reply to sender
- [ ] Forward to relevant party
- [ ] Archive after processing
'''

            # Create a safe filename using the message ID
            filename = f"EMAIL_{message['id']}.md"
            filepath = self.needs_action / filename
            filepath.write_text(content)
            self.processed_ids.add(message['id'])
            self.logger.info(f"Created action file: {filepath}")
            return filepath
        except Exception as e:
            self.logger.error(f"Error creating action file: {e}")
            raise


# Example usage and testing
if __name__ == "__main__":
    import os
    # Set up logging
    logging.basicConfig(level=logging.INFO)

    # Example instantiation (credentials file would need to be set up separately)
    # watcher = GmailWatcher(
    #     vault_path="./Personal AI Employee",
    #     credentials_path="./gmail_credentials.json"
    # )
    # watcher.run()  # This would run indefinitely
    print("GmailWatcher class defined. Ready to use when credentials are configured.")