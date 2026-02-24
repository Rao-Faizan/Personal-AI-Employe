#!/usr/bin/env python3
"""
File System Watcher for AI Employee

This script monitors a designated drop folder and creates action files
in the Needs_Action folder when new files are detected.
"""

import time
import logging
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import shutil
from datetime import datetime
import mimetypes

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('watcher.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('FileSystemWatcher')

class DropFolderHandler(FileSystemEventHandler):
    """Handles file system events in the monitored folder."""

    def __init__(self, vault_path: str):
        self.vault_path = Path(vault_path)
        self.needs_action = self.vault_path / 'Needs_Action'
        self.inbox = self.vault_path / 'Inbox'
        self.supported_types = {'.txt', '.pdf', '.docx', '.xlsx', '.csv', '.jpg', '.png', '.md'}

        # Ensure target directories exist
        self.needs_action.mkdir(exist_ok=True)
        self.inbox.mkdir(exist_ok=True)

    def on_created(self, event):
        """Handle file creation events."""
        if event.is_directory:
            return

        source = Path(event.src_path)

        # Check if file type is supported
        if source.suffix.lower() not in self.supported_types:
            logger.info(f"Ignoring unsupported file type: {source.name}")
            return

        logger.info(f"New file detected: {source.name}")

        # Copy file to inbox
        inbox_dest = self.inbox / f"NEW_{source.name}"
        shutil.copy2(source, inbox_dest)

        # Create metadata file in Needs_Action
        self.create_action_file(source, inbox_dest)

    def on_modified(self, event):
        """Handle file modification events."""
        if event.is_directory:
            return

        source = Path(event.src_path)

        # Only process if it's a new file (not a temp file being written)
        if source.suffix.lower() in self.supported_types:
            # Add a small delay to ensure file is fully written
            time.sleep(1)
            logger.info(f"File modified: {source.name}")
            # Re-process the file
            self.create_action_file(source, self.inbox / f"MODIFIED_{source.name}")

    def create_action_file(self, source: Path, inbox_file: Path):
        """Create an action file in Needs_Action folder."""
        # Determine file type
        mime_type, _ = mimetypes.guess_type(str(source))
        if mime_type:
            if 'image' in mime_type:
                file_type = 'image'
            elif 'pdf' in mime_type:
                file_type = 'document'
            elif 'text' in mime_type or source.suffix.lower() in ['.txt', '.md']:
                file_type = 'text'
            elif 'spreadsheet' in mime_type or source.suffix.lower() in ['.xls', '.xlsx', '.csv']:
                file_type = 'spreadsheet'
            else:
                file_type = 'file'
        else:
            file_type = 'file'

        # Create metadata
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        action_filename = f"FILE_DROP_{timestamp}_{source.stem}.md"
        action_path = self.needs_action / action_filename

        # Get file size
        size = source.stat().st_size
        size_kb = round(size / 1024, 2)

        # Create action file content
        content = f"""---
type: file_drop
original_name: {source.name}
file_type: {file_type}
size_kb: {size_kb}
received_at: {datetime.now().isoformat()}
status: pending
priority: medium
---

# New File Received

A new file has been dropped for processing:

- **Original Name:** `{source.name}`
- **Type:** {file_type}
- **Size:** {size_kb} KB
- **Received:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Processing Instructions

1. Review the file content in [[{inbox_file.name}]]
2. Determine appropriate action based on file type and content
3. Follow company handbook guidelines for handling
4. Update status when processed

## Suggested Actions
- [ ] Review file content
- [ ] Determine next steps
- [ ] Process according to company guidelines
- [ ] Move original file to Done when complete

## Notes
Add any relevant notes about the file or required actions here.
"""

        # Write the action file
        action_path.write_text(content)
        logger.info(f"Created action file: {action_filename}")

        # Update dashboard to reflect new activity
        self.update_dashboard(source.name)

    def update_dashboard(self, filename: str):
        """Update the dashboard with the new activity."""
        try:
            dashboard_path = self.vault_path / "Dashboard.md"
            if dashboard_path.exists():
                content = dashboard_path.read_text()

                # Find the Recent Activity section
                if "## Recent Activity" in content:
                    lines = content.split('\n')
                    new_lines = []

                    for line in lines:
                        new_lines.append(line)
                        if line.strip() == "## Recent Activity":
                            new_lines.append(f"- [{datetime.now().strftime('%H:%M')}] New file: {filename}")

                    # Write updated content
                    dashboard_path.write_text('\n'.join(new_lines))

        except Exception as e:
            logger.error(f"Error updating dashboard: {e}")


def main():
    """Main function to start the file system watcher."""
    vault_path = Path.cwd()  # Current directory as vault
    drop_folder = vault_path / "Drop_Folder"  # Folder to monitor

    # Create the drop folder if it doesn't exist
    drop_folder.mkdir(exist_ok=True)

    # Create the handler
    event_handler = DropFolderHandler(str(vault_path))

    # Create observer
    observer = Observer()
    observer.schedule(event_handler, str(drop_folder), recursive=False)

    logger.info(f"Starting file system watcher...")
    logger.info(f"Monitoring folder: {drop_folder}")
    logger.info(f"Vault path: {vault_path}")
    logger.info("Press Ctrl+C to stop the watcher")

    try:
        observer.start()
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
        logger.info("File system watcher stopped.")

    observer.join()


if __name__ == "__main__":
    main()