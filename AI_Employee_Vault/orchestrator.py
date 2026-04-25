"""
Orchestrator for AI Employee - Silver Tier

Manages all watchers, scheduled tasks, and approved actions.

Usage:
    python orchestrator.py
"""

import subprocess
import time
import signal
import sys
from pathlib import Path
import datetime
import threading


class Orchestrator:
    """Main orchestrator for AI Employee"""
    
    def __init__(self, vault_path: str = ".", dry_run: bool = False):
        self.vault_path = Path(vault_path)
        self.dry_run = dry_run
        self.logs_path = self.vault_path / "Logs"
        self.logs_path.mkdir(exist_ok=True)
        self.running = False
        self.watchers = []
        
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        self._setup_logging()
    
    def _setup_logging(self):
        """Setup logging"""
        import logging
        log_file = self.logs_path / f"orchestrator_{datetime.datetime.now().strftime('%Y-%m-%d')}.log"
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger("Orchestrator")
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown"""
        self.logger.info("Shutting down...")
        self.running = False
        sys.exit(0)
    
    def start_watcher(self, name: str, script: str):
        """Start a watcher process"""
        script_path = self.vault_path / "watchers" / script
        if not script_path.exists():
            self.logger.warning(f"Watcher not found: {script}")
            return
        
        try:
            process = subprocess.Popen(
                [sys.executable, str(script_path), "--vault-path", str(self.vault_path)],
                cwd=str(self.vault_path)
            )
            self.watchers.append({"name": name, "process": process})
            self.logger.info(f"Started watcher: {name} (PID: {process.pid})")
        except Exception as e:
            self.logger.error(f"Failed to start {name}: {e}")
    
    def process_approved_actions(self):
        """Process approved actions"""
        approved_path = self.vault_path / "Approved"
        if not approved_path.exists():
            return
        
        for file in approved_path.glob("*.md"):
            try:
                done_path = self.vault_path / "Done" / file.name
                file.rename(done_path)
                self.logger.info(f"Processed approved file: {file.name}")
            except Exception as e:
                self.logger.error(f"Error processing {file.name}: {e}")
    
    def generate_daily_briefing(self):
        """Generate daily CEO briefing"""
        try:
            sys.path.insert(0, str(self.vault_path))
            from agent_skills import AIEmployeeSkills
            skills = AIEmployeeSkills(str(self.vault_path))
            briefing_path = skills.generate_ceo_briefing()
            self.logger.info(f"Generated CEO briefing: {briefing_path}")
        except Exception as e:
            self.logger.error(f"Error generating briefing: {e}")
    
    def run(self, mode: str = "all"):
        """Run the orchestrator"""
        self.running = True
        self.logger.info(f"Starting orchestrator (mode: {mode})")

        if mode in ["all", "watchers"]:
            # Start watchers
            self.start_watcher("Gmail", "gmail_watcher.py")
            self.start_watcher("LinkedIn", "linkedin_poster.py")

        if mode in ["all", "scheduler"]:
            # Process approved actions periodically
            last_briefing = None

            while self.running:
                try:
                    self.process_approved_actions()

                    # Generate daily briefing at 8 AM
                    now = datetime.datetime.now()
                    if now.hour == 8 and now.minute == 0 and last_briefing != now.date():
                        self.generate_daily_briefing()
                        last_briefing = now.date()

                    time.sleep(60)
                except Exception as e:
                    self.logger.error(f"Error in scheduler: {e}")

        self.logger.info("Orchestrator stopped")


def main():
    import argparse
    parser = argparse.ArgumentParser(description='AI Employee Orchestrator')
    parser.add_argument('--vault-path', type=str, default='.')
    parser.add_argument('--mode', type=str, default='all', choices=['all', 'watchers', 'scheduler'])
    parser.add_argument('--dry-run', action='store_true')
    
    args = parser.parse_args()
    
    orchestrator = Orchestrator(vault_path=args.vault_path, dry_run=args.dry_run)
    orchestrator.run(mode=args.mode)


if __name__ == "__main__":
    main()
