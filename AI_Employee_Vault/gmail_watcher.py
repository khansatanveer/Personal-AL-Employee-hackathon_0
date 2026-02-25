"""
Gmail Watcher Script
Monitors Gmail for new messages and creates action files for Claude to process.
"""

import time
import logging
from pathlib import Path
from abc import ABC, abstractmethod
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from datetime import datetime
import os
import json

class BaseWatcher(ABC):
    def __init__(self, vault_path: str, check_interval: int = 60):
        self.vault_path = Path(vault_path)
        self.needs_action = self.vault_path / 'Needs_Action'
        self.check_interval = check_interval
        self.logger = logging.getLogger(self.__class__.__name__)

    @abstractmethod
    def check_for_updates(self) -> list:
        '''Return list of new items to process'''
        pass

    @abstractmethod
    def create_action_file(self, item) -> Path:
        '''Create .md file in Needs_Action folder'''
        pass

    def run(self):
        self.logger.info(f'Starting {self.__class__.__name__}')
        while True:
            try:
                items = self.check_for_updates()
                for item in items:
                    self.create_action_file(item)
            except Exception as e:
                self.logger.error(f'Error: {e}')
            time.sleep(self.check_interval)


class GmailWatcher(BaseWatcher):
    def __init__(self, vault_path: str, credentials_path: str):
        super().__init__(vault_path, check_interval=120)  # Check every 2 minutes
        self.credentials_path = credentials_path
        self.processed_ids = set()

        # Set up logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)

    def check_for_updates(self) -> list:
        """Check Gmail for new messages"""
        try:
            # Load credentials
            if os.path.exists(self.credentials_path):
                creds = Credentials.from_authorized_user_file(self.credentials_path)
            else:
                self.logger.error(f"Credentials file not found: {self.credentials_path}")
                return []

            # Build Gmail service
            service = build('gmail', 'v1', credentials=creds)

            # Query for unread important messages
            results = service.users().messages().list(
                userId='me',
                q='is:unread is:important after:2026-01-01'
            ).execute()

            messages = results.get('messages', [])

            # Filter out already processed messages
            new_messages = [m for m in messages if m['id'] not in self.processed_ids]

            return new_messages
        except Exception as e:
            self.logger.error(f"Error checking Gmail: {e}")
            return []

    def create_action_file(self, message) -> Path:
        """Create an action file for a Gmail message"""
        try:
            # Load credentials again to build service
            if os.path.exists(self.credentials_path):
                creds = Credentials.from_authorized_user_file(self.credentials_path)
                service = build('gmail', 'v1', credentials=creds)
            else:
                self.logger.error(f"Credentials file not found: {self.credentials_path}")
                return None

            msg = service.users().messages().get(
                userId='me', id=message['id']
            ).execute()

            # Extract headers
            headers = {h['name']: h['value'] for h in msg['payload']['headers']}

            # Extract message body
            body = ""
            if 'parts' in msg['payload']:
                for part in msg['payload']['parts']:
                    if part['mimeType'] == 'text/plain':
                        import base64
                        body = base64.urlsafe_b64decode(part['body']['data']).decode('utf-8')
                        break
            else:
                import base64
                if 'body' in msg['payload'] and 'data' in msg['payload']['body']:
                    body = base64.urlsafe_b64decode(msg['payload']['body']['data']).decode('utf-8')

            content = f"""---
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
"""
            filepath = self.needs_action / f"GMAIL_{message['id']}.md"
            filepath.write_text(content)
            self.processed_ids.add(message['id'])

            self.logger.info(f"Created action file: {filepath}")
            return filepath
        except Exception as e:
            self.logger.error(f"Error creating action file: {e}")
            return None


def main():
    # Set up paths
    vault_path = "AI_Employee_Vault"
    credentials_path = "gmail_credentials.json"  # This should be set up separately

    # Create the watcher
    watcher = GmailWatcher(vault_path, credentials_path)

    print("Gmail Watcher starting...")
    print(f"Monitoring Gmail, checking every {watcher.check_interval} seconds")
    print(f"Action files will be created in: {watcher.needs_action}")

    # Run the watcher
    watcher.run()


if __name__ == "__main__":
    main()