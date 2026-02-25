"""
Gmail Watcher Script - Bronze Tier Implementation
Monitors Gmail for new messages and creates action files for Claude to process.
This is a simplified version for the Bronze tier that demonstrates the concept.
"""

import time
import logging
from pathlib import Path
from datetime import datetime
import json
import os

class GmailWatcher:
    def __init__(self, vault_path: str, check_interval: int = 60):
        self.vault_path = Path(vault_path)
        self.needs_action = self.vault_path / 'Needs_Action'
        self.check_interval = check_interval
        self.processed_ids = set()

        # Set up logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)

    def check_for_updates(self):
        """Check for new messages (simulated for Bronze tier)"""
        try:
            # In a complete implementation, this would connect to Gmail API
            # For Bronze tier, we'll simulate monitoring by checking for
            # mock email files in a special directory
            mock_email_dir = self.vault_path / 'Mock_Emails'
            if not mock_email_dir.exists():
                mock_email_dir.mkdir(exist_ok=True)
                self.logger.info(f"Created mock email directory: {mock_email_dir}")

            # Look for new mock email files
            new_emails = []
            for email_file in mock_email_dir.glob("*.json"):
                if email_file.stem not in self.processed_ids:
                    try:
                        with open(email_file, 'r', encoding='utf-8') as f:
                            email_data = json.load(f)
                            new_emails.append({
                                'id': email_file.stem,
                                'data': email_data
                            })
                    except Exception as e:
                        self.logger.error(f"Error reading email file {email_file}: {e}")

            return new_emails
        except Exception as e:
            self.logger.error(f"Error checking for updates: {e}")
            return []

    def create_action_file(self, email_message):
        """Create an action file for a Gmail message"""
        try:
            email_data = email_message['data']

            content = f"""---
type: email
from: {email_data.get('from', 'Unknown')}
subject: {email_data.get('subject', 'No Subject')}
received: {email_data.get('received', datetime.now().isoformat())}
priority: {email_data.get('priority', 'medium')}
status: pending
---

## Email Content
{email_data.get('body', 'No body content')}

## Sender Information
- From: {email_data.get('from', 'Unknown')}
- To: {email_data.get('to', 'Unknown')}
- CC: {email_data.get('cc', 'None')}

## Suggested Actions
- [ ] Review content
- [ ] Determine appropriate response
- [ ] {f'Respond to {email_data.get("from", "sender")}' if email_data.get('requires_response') else 'File for reference'}

## Context
This email was flagged as requiring attention based on priority and content.
"""
            filepath = self.needs_action / f"GMAIL_{email_message['id']}.md"
            filepath.write_text(content)
            self.processed_ids.add(email_message['id'])

            self.logger.info(f"Created action file: {filepath}")
            return filepath
        except Exception as e:
            self.logger.error(f"Error creating action file: {e}")
            return None

    def run(self):
        """Main run loop for the watcher"""
        self.logger.info(f'Starting Gmail Watcher')
        self.logger.info(f'Checking for updates every {self.check_interval} seconds')

        try:
            while True:
                items = self.check_for_updates()
                for item in items:
                    self.create_action_file(item)

                # Wait before next check
                time.sleep(self.check_interval)
        except KeyboardInterrupt:
            self.logger.info("Gmail Watcher stopped by user")
        except Exception as e:
            self.logger.error(f"Error in main loop: {e}")


def main():
    # Set up paths
    vault_path = "AI_Employee_Vault"

    # Verify vault exists
    vault = Path(vault_path)
    if not vault.exists():
        print(f"Error: Vault directory {vault_path} does not exist!")
        return

    # Create the watcher
    watcher = GmailWatcher(vault_path, check_interval=30)  # Check every 30 seconds for demo

    print("Gmail Watcher starting...")
    print(f"Monitoring for new mock emails, checking every {watcher.check_interval} seconds")
    print(f"Action files will be created in: {watcher.needs_action}")
    print("To test, create JSON files in the Mock_Emails directory")
    print("Press Ctrl+C to stop the watcher")

    # Run the watcher
    watcher.run()


if __name__ == "__main__":
    main()