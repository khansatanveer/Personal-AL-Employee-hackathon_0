#!/usr/bin/env python3
"""
Main orchestrator for the Personal AI Employee
Manages the various watchers and system components
"""

import os
import sys
import time
import logging
import threading
from pathlib import Path
from datetime import datetime


class AIEmployee:
    def __init__(self, vault_path):
        self.vault_path = Path(vault_path)
        self.logger = self._setup_logging()
        self.running = False
        self.watchers = []

    def _setup_logging(self):
        """Set up logging for the AI Employee"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(self.vault_path / 'ai_employee.log'),
                logging.StreamHandler()
            ]
        )
        return logging.getLogger('AIEmployee')

    def add_watcher(self, watcher):
        """Add a watcher to the system"""
        self.watchers.append(watcher)
        self.logger.info(f"Added watcher: {watcher.__class__.__name__}")

    def start_watchers(self):
        """Start all registered watchers in separate threads"""
        for watcher in self.watchers:
            thread = threading.Thread(target=watcher.run, daemon=True)
            thread.start()
            self.logger.info(f"Started watcher: {watcher.__class__.__name__}")

    def update_dashboard(self):
        """Update the dashboard with current status"""
        dashboard_path = self.vault_path / 'Dashboard.md'

        if dashboard_path.exists():
            content = dashboard_path.read_text()
            # Update the status and timestamp
            updated_content = content.replace(
                '{{date}}', datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            ).replace(
                '{{time}}', datetime.now().strftime('%H:%M:%S')
            )

            # Update counts
            needs_action_dir = self.vault_path / 'Needs_Action'
            action_count = 0
            if needs_action_dir.exists():
                action_count = len(list(needs_action_dir.glob('*.md')))

            updated_content = updated_content.replace(
                '{{action_count}}', str(action_count)
            )

            dashboard_path.write_text(updated_content)
            self.logger.info("Dashboard updated")

    def run(self):
        """Main run loop"""
        self.logger.info("Starting Personal AI Employee")
        self.running = True

        # Start all watchers
        self.start_watchers()

        # Main loop - periodically update dashboard
        while self.running:
            try:
                self.update_dashboard()
                time.sleep(300)  # Update dashboard every 5 minutes
            except KeyboardInterrupt:
                self.logger.info("Shutdown requested")
                break
            except Exception as e:
                self.logger.error(f"Error in main loop: {e}")
                time.sleep(60)  # Wait 1 minute before retrying

    def stop(self):
        """Stop the AI Employee"""
        self.logger.info("Stopping Personal AI Employee")
        self.running = False


def main():
    vault_path = "AI_Employee_Vault"

    # Check if vault exists
    if not Path(vault_path).exists():
        print(f"Vault directory {vault_path} does not exist!")
        return

    # Create the AI Employee instance
    ai_employee = AIEmployee(vault_path)

    print("Personal AI Employee - Bronze Tier Implementation")
    print("=" * 55)
    print(f"Vault location: {Path(vault_path).absolute()}")
    print(f"Dashboard: {Path(vault_path) / 'Dashboard.md'}")
    print(f"Handbook: {Path(vault_path) / 'Company_Handbook.md'}")
    print()

    print("Initializing watchers...")

    # Try to initialize Gmail watcher (but don't fail if credentials aren't available)
    try:
        from gmail_watcher import GmailWatcher
        import os

        # Check if credentials file exists
        creds_path = "gmail_credentials.json"
        if Path(creds_path).exists():
            gmail_watcher = GmailWatcher(vault_path, creds_path)
            ai_employee.add_watcher(gmail_watcher)
            print("Gmail Watcher initialized")
        else:
            print("Gmail Watcher: Credentials not found (gmail_credentials.json)")
            print("   To use Gmail functionality, set up Google API credentials")
    except ImportError as e:
        print(f"Gmail Watcher: Could not import (need google-api-python-client): {e}")
    except Exception as e:
        print(f"Gmail Watcher: Error initializing: {e}")

    print("\nBronze Tier Requirements Status:")
    print("Obsidian vault with Dashboard.md and Company_Handbook.md")
    print("Gmail Watcher script implemented")
    print("Claude Code can read from and write to the vault")
    print()

    print("Starting Personal AI Employee...")
    print("Press Ctrl+C to stop")
    print()

    ai_employee.run()


if __name__ == "__main__":
    main()