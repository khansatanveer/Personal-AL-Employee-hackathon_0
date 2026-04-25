"""
File System Watcher for AI Employee

This script monitors the Inbox folder for new files and moves them to Needs_Action
when detected. This serves as the basic perception layer for the AI Employee.
"""

import time
import logging
from pathlib import Path
import shutil
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import datetime

class FileWatcherHandler(FileSystemEventHandler):
    def __init__(self, vault_path: str):
        self.vault_path = Path(vault_path)
        self.needs_action = self.vault_path / 'Needs_Action'
        self.logs = self.vault_path / 'Logs'
        self.setup_logging()

    def setup_logging(self):
        # Create logs directory if it doesn't exist
        self.logs.mkdir(exist_ok=True)

        # Setup logging
        log_filename = self.logs / f"file_watcher_{datetime.datetime.now().strftime('%Y-%m-%d')}.log"
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_filename),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)

    def on_created(self, event):
        if event.is_directory:
            return

        # Only process .md files
        if event.src_path.endswith('.md'):
            source = Path(event.src_path)
            if 'Inbox' in str(source):
                self.process_new_file(source)

    def on_moved(self, event):
        if event.is_directory:
            return

        # Only process .md files
        if event.dest_path.endswith('.md'):
            source = Path(event.dest_path)
            if 'Inbox' in str(source):
                self.process_new_file(source)

    def process_new_file(self, source: Path):
        """Process a new file by moving it to Needs_Action"""
        try:
            # Create a new filename with timestamp
            timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
            new_filename = f"{timestamp}_{source.name}"
            dest_path = self.needs_action / new_filename

            # Move the file to Needs_Action
            shutil.move(str(source), str(dest_path))

            self.logger.info(f"Moved {source.name} to Needs_Action as {new_filename}")

            # Update the dashboard to reflect the new task
            self.update_dashboard()

        except Exception as e:
            self.logger.error(f"Error processing file {source}: {str(e)}")

    def update_dashboard(self):
        """Update the dashboard with the latest status"""
        try:
            dashboard_path = self.vault_path / 'Dashboard.md'
            if not dashboard_path.exists():
                return

            content = dashboard_path.read_text()

            # Count files in each directory
            inbox_count = len(list((self.vault_path / 'Inbox').glob('*.md')))
            needs_action_count = len(list((self.vault_path / 'Needs_Action').glob('*.md')))
            done_count = len(list((self.vault_path / 'Done').glob('*.md')))
            pending_approval_count = len(list((self.vault_path / 'Pending_Approval').glob('*.md')))

            # Update the dashboard content
            import re
            content = re.sub(r'Files in Inbox: \d+', f'Files in Inbox: {inbox_count}', content)
            content = re.sub(r'Files in Needs_Action: \d+', f'Files in Needs_Action: {needs_action_count}', content)
            content = re.sub(r'Files in Done: \d+', f'Files in Done: {done_count}', content)
            content = re.sub(r'Files in Pending Approval: \d+', f'Files in Pending Approval: {pending_approval_count}', content)

            # Update last updated time
            current_time = datetime.datetime.now().strftime('%Y-%m-%dT%H:%M:%S%z')
            content = re.sub(r'Last Updated: [\d\-:T\+]+', f'Last Updated: {current_time}', content)

            # Add to recent activity
            if 'Recent Activity' in content:
                activity_section_start = content.find('## Recent Activity')
                if activity_section_start != -1:
                    next_header = content.find('## ', activity_section_start + 1)
                    if next_header == -1:
                        next_header = len(content)

                    activity_section = content[activity_section_start:next_header]
                    new_activity = f"- [{datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}] New file detected and moved to Needs_Action\n"

                    # Insert new activity right after the "Recent Activity" header
                    lines = activity_section.split('\n')
                    if len(lines) > 1:
                        lines.insert(1, new_activity.rstrip())
                        updated_activity = '\n'.join(lines)
                        content = content[:activity_section_start] + updated_activity + content[next_header:]

            dashboard_path.write_text(content)
            self.logger.info("Dashboard updated successfully")

        except Exception as e:
            self.logger.error(f"Error updating dashboard: {str(e)}")


def run_file_watcher(vault_path: str = "./AI_Employee_Vault"):
    """Run the file system watcher"""
    vault_path = Path(vault_path)

    # Ensure required directories exist
    (vault_path / 'Inbox').mkdir(parents=True, exist_ok=True)
    (vault_path / 'Needs_Action').mkdir(parents=True, exist_ok=True)
    (vault_path / 'Done').mkdir(parents=True, exist_ok=True)
    (vault_path / 'Pending_Approval').mkdir(parents=True, exist_ok=True)
    (vault_path / 'Logs').mkdir(parents=True, exist_ok=True)

    event_handler = FileWatcherHandler(vault_path)
    observer = Observer()
    observer.schedule(event_handler, str(vault_path / 'Inbox'), recursive=False)

    observer.start()
    event_handler.logger.info(f"File watcher started, monitoring: {vault_path}/Inbox")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
        event_handler.logger.info("File watcher stopped by user")

    observer.join()


if __name__ == "__main__":
    # Default to current directory if no argument provided
    import sys
    vault_path = sys.argv[1] if len(sys.argv) > 1 else "./AI_Employee_Vault"
    run_file_watcher(vault_path)