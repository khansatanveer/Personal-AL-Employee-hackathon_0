"""
WhatsApp Watcher for AI Employee - Silver Tier

Monitors WhatsApp Web for important messages using Playwright.

Usage:
    python watchers/whatsapp_watcher.py
"""

import time
import logging
import sys
from pathlib import Path
import datetime
from typing import List, Dict


class WhatsAppWatcher:
    """WhatsApp Watcher - Monitors WhatsApp Web for important messages"""
    
    def __init__(self, vault_path: str, check_interval: int = 30, dry_run: bool = False):
        self.vault_path = Path(vault_path)
        self.session_path = self.vault_path / "sessions" / "whatsapp"
        self.check_interval = check_interval
        self.dry_run = dry_run
        self.logs = self.vault_path / "Logs"
        self.needs_action = self.vault_path / "Needs_Action"
        
        self.keywords = ['urgent', 'asap', 'invoice', 'payment', 'help', 'emergency', 'important']
        
        self.logs.mkdir(exist_ok=True)
        self.needs_action.mkdir(exist_ok=True)
        self.session_path.parent.mkdir(parents=True, exist_ok=True)
        
        self._setup_logging()
        self.playwright = None
    
    def _setup_logging(self):
        """Setup logging"""
        log_file = self.logs / f"whatsapp_watcher_{datetime.datetime.now().strftime('%Y-%m-%d')}.log"
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger("WhatsAppWatcher")
    
    def _check_for_updates(self) -> List[Dict]:
        """Check for important WhatsApp messages"""
        try:
            from playwright.sync_api import sync_playwright
            
            self.playwright = sync_playwright().start()
            browser = self.playwright.chromium.launch_persistent_context(
                str(self.session_path), headless=True
            )
            
            page = browser.pages[0] if browser.pages else browser.new_page()
            page.goto('https://web.whatsapp.com')
            page.wait_for_selector('[data-testid="chat-list"]', timeout=10000)
            
            unread = page.query_selector_all('[aria-label*="unread"]')
            important_messages = []
            
            for chat in unread:
                text = chat.inner_text().lower()
                if any(kw in text for kw in self.keywords):
                    chat_name = chat.query_selector('[dir="auto"]').inner_text()
                    important_messages.append({
                        'chat_name': chat_name,
                        'text': text,
                        'timestamp': datetime.datetime.now().isoformat()
                    })
            
            browser.close()
            self.playwright.stop()
            
            if important_messages:
                self.logger.info(f"Found {len(important_messages)} important message(s)")
            
            return important_messages
            
        except Exception as e:
            self.logger.error(f"Error checking WhatsApp: {e}")
            return []
    
    def _create_action_file(self, message: Dict) -> Path:
        """Create an action file for WhatsApp message"""
        timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        safe_name = self._sanitize_filename(message['chat_name'])
        filename = f"WHATSAPP_{safe_name}_{timestamp}.md"
        filepath = self.needs_action / filename
        
        content = f"""---
type: whatsapp
from: {message['chat_name']}
received: {message['timestamp']}
priority: high
status: pending
---

# WhatsApp Message

**From:** {message['chat_name']}
**Received:** {message['timestamp']}

## Message Content
{message['text']}

## Suggested Actions
- [ ] Read full conversation
- [ ] Reply to sender
- [ ] Take necessary action
"""
        
        if not self.dry_run:
            filepath.write_text(content, encoding='utf-8')
            self.logger.info(f"✓ Created action file: {filename}")
            self._update_dashboard(filename)
        else:
            self.logger.info(f"[DRY RUN] Would create: {filename}")
        
        return filepath
    
    def _sanitize_filename(self, text: str) -> str:
        for char in '<>:"/\\|?* ':
            text = text.replace(char, '_')
        return text[:50].strip()
    
    def _update_dashboard(self, filename: str):
        """Update dashboard"""
        try:
            sys.path.insert(0, str(self.vault_path))
            from agent_skills import AIEmployeeSkills
            skills = AIEmployeeSkills(str(self.vault_path))
            skills.update_dashboard_activity(f"New WhatsApp message: {filename}", "whatsapp")
        except Exception as e:
            self.logger.error(f"Error updating dashboard: {e}")
    
    def run(self):
        """Run the WhatsApp watcher loop"""
        self.logger.info(f"Starting WhatsApp Watcher (interval: {self.check_interval}s)")
        
        try:
            while True:
                try:
                    items = self._check_for_updates()
                    for item in items:
                        self._create_action_file(item)
                except Exception as e:
                    self.logger.error(f"Error in watch loop: {e}")
                
                time.sleep(self.check_interval)
                
        except KeyboardInterrupt:
            self.logger.info("WhatsApp Watcher stopped by user")


def main():
    import argparse
    parser = argparse.ArgumentParser(description='WhatsApp Watcher')
    parser.add_argument('--vault-path', type=str, default='.')
    parser.add_argument('--interval', type=int, default=30)
    parser.add_argument('--dry-run', action='store_true')
    
    args = parser.parse_args()
    
    watcher = WhatsAppWatcher(
        vault_path=args.vault_path,
        check_interval=args.interval,
        dry_run=args.dry_run
    )
    watcher.run()


if __name__ == "__main__":
    main()
