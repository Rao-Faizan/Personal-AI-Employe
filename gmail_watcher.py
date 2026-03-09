#!/usr/bin/env python3
"""
Gmail Watcher for AI Employee

Monitors Gmail for new important/unread emails and creates action files
in the Needs_Action folder for Claude to process.

Setup:
1. Enable Gmail API: https://developers.google.com/gmail/api/quickstart/python
2. Download credentials.json from Google Cloud Console
3. Run once to authorize: python gmail_watcher.py --auth
4. Token file will be saved as token.json (keep secure!)

Usage:
    python gmail_watcher.py
"""

import os
import sys
import time
import logging
import base64
from pathlib import Path
from datetime import datetime
from email import message_from_bytes
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# Fix Windows console encoding
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, errors='replace')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, errors='replace')

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('gmail_watcher.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('GmailWatcher')

# Gmail API scopes
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

class GmailWatcher:
    """Monitor Gmail for new messages and create action files."""

    def __init__(self, vault_path: str, check_interval: int = 120):
        self.vault_path = Path(vault_path)
        self.needs_action = self.vault_path / 'Needs_Action'
        self.check_interval = check_interval  # seconds
        self.token_file = Path('token.json')
        self.credentials_file = Path('credentials.json')
        self.processed_ids = set()
        self.service = None
        
        # Ensure target directory exists
        self.needs_action.mkdir(exist_ok=True)
        
        # Load previously processed message IDs
        self._load_processed_ids()

    def _load_processed_ids(self):
        """Load IDs of already processed messages to avoid duplicates."""
        cache_file = self.vault_path / 'Logs' / 'gmail_processed.json'
        if cache_file.exists():
            import json
            try:
                data = json.loads(cache_file.read_text())
                self.processed_ids = set(data.get('processed_ids', []))
                logger.info(f"Loaded {len(self.processed_ids)} processed message IDs")
            except Exception as e:
                logger.warning(f"Could not load processed IDs: {e}")

    def _save_processed_ids(self):
        """Save processed message IDs to cache."""
        cache_file = self.vault_path / 'Logs' / 'gmail_processed.json'
        cache_file.parent.mkdir(exist_ok=True)
        import json
        # Keep only last 1000 IDs to prevent unbounded growth
        ids_list = list(self.processed_ids)[-1000:]
        cache_file.write_text(json.dumps({'processed_ids': ids_list, 'updated': datetime.now().isoformat()}))

    def authenticate(self, port: int = 8080):
        """Perform OAuth2 authentication flow."""
        creds = None
        
        # Load token if exists
        if self.token_file.exists():
            creds = Credentials.from_authorized_user_file(self.token_file, SCOPES)
        
        # Refresh or get new credentials
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                if not self.credentials_file.exists():
                    logger.error("credentials.json not found! Download from Google Cloud Console.")
                    return False
                flow = InstalledAppFlow.from_client_secrets_file(self.credentials_file, SCOPES)
                creds = flow.run_local_server(port=port)
            
            # Save token
            self.token_file.write_text(creds.to_json())
            logger.info("Credentials saved to token.json")
        
        # Build service
        self.service = build('gmail', 'v1', credentials=creds)
        logger.info("Gmail authentication successful")
        return True

    def check_for_new_emails(self) -> list:
        """Check for new unread important emails."""
        if not self.service:
            logger.error("Gmail service not initialized. Run authentication first.")
            return []
        
        try:
            # Search for unread messages
            results = self.service.users().messages().list(
                userId='me',
                q='is:unread -in:chats -in:drafts -in:spam -in:trash',
                maxResults=10
            ).execute()
            
            messages = results.get('messages', [])
            new_messages = [m for m in messages if m['id'] not in self.processed_ids]
            
            logger.info(f"Found {len(messages)} unread, {len(new_messages)} new messages")
            return new_messages
            
        except HttpError as error:
            logger.error(f"Gmail API error: {error}")
            return []

    def get_message_details(self, message_id: str) -> dict:
        """Fetch full message details."""
        try:
            message = self.service.users().messages().get(
                userId='me',
                id=message_id,
                format='full'
            ).execute()
            
            # Extract headers
            headers = message['payload']['headers']
            header_dict = {h['name']: h['value'] for h in headers}
            
            # Get body
            body = self._extract_body(message['payload'])
            
            # Get attachments info
            attachments = self._get_attachments_info(message['payload'])
            
            return {
                'id': message_id,
                'from': header_dict.get('From', 'Unknown'),
                'to': header_dict.get('To', ''),
                'subject': header_dict.get('Subject', 'No Subject'),
                'date': header_dict.get('Date', ''),
                'body': body,
                'attachments': attachments,
                'snippet': message.get('snippet', '')
            }
            
        except HttpError as error:
            logger.error(f"Error fetching message {message_id}: {error}")
            return None

    def _extract_body(self, payload: dict) -> str:
        """Extract email body from payload."""
        if 'parts' in payload:
            for part in payload['parts']:
                if part['mimeType'] == 'text/plain':
                    if 'data' in part['body']:
                        return base64.urlsafe_b64decode(part['body']['data']).decode('utf-8')
                elif part['mimeType'] == 'text/html':
                    if 'data' in part['body']:
                        return base64.urlsafe_b64decode(part['body']['data']).decode('utf-8')
        elif 'body' in payload and 'data' in payload['body']:
            return base64.urlsafe_b64decode(payload['body']['data']).decode('utf-8')
        
        return ''

    def _get_attachments_info(self, payload: dict) -> list:
        """Get list of attachments with their IDs."""
        attachments = []
        if 'parts' in payload:
            for part in payload['parts']:
                if part['filename']:
                    attachments.append({
                        'filename': part['filename'],
                        'mimeType': part['mimeType'],
                        'size': part['body'].get('size', 0)
                    })
        return attachments

    def create_action_file(self, email_data: dict) -> Path:
        """Create an action file in Needs_Action folder."""
        # Determine priority based on sender and subject
        priority = self._determine_priority(email_data)
        
        # Create filename
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        safe_subject = email_data['subject'][:30].replace(' ', '_').replace(':', '')
        filename = f"EMAIL_{timestamp}_{safe_subject}.md"
        action_path = self.needs_action / filename
        
        # Truncate body for action file (first 500 chars)
        body_preview = email_data['body'][:500] if email_data['body'] else email_data['snippet']
        if len(email_data['body'] or '') > 500:
            body_preview += "\n\n... [truncated]"
        
        # Create action file content
        content = f"""---
type: email
from: {email_data['from']}
to: {email_data['to']}
subject: {email_data['subject']}
received: {datetime.now().isoformat()}
priority: {priority}
status: pending
has_attachments: {len(email_data['attachments']) > 0}
---

# New Email Received

## Email Details
- **From:** {email_data['from']}
- **To:** {email_data['to']}
- **Subject:** {email_data['subject']}
- **Received:** {email_data['date']}
- **Priority:** {priority}

## Attachments
{self._format_attachments(email_data['attachments'])}

## Message Content
{body_preview}

## Suggested Actions
- [ ] Read full email
- [ ] Determine appropriate response
- [ ] Draft reply (requires approval for new contacts)
- [ ] Archive after processing

## Notes
Add context or response strategy here.
"""
        
        # Write action file
        action_path.write_text(content)
        logger.info(f"Created action file: {filename}")
        
        # Mark as processed
        self.processed_ids.add(email_data['id'])
        self._save_processed_ids()
        
        # Update dashboard
        self._update_dashboard(email_data)
        
        return action_path

    def _determine_priority(self, email_data: dict) -> str:
        """Determine email priority based on content."""
        subject_lower = email_data['subject'].lower()
        from_lower = email_data['from'].lower()
        
        # High priority keywords
        high_priority_keywords = ['urgent', 'asap', 'invoice', 'payment', 'important', 'deadline']
        if any(kw in subject_lower for kw in high_priority_keywords):
            return 'high'
        
        # Check if from known contact (would need contacts list)
        # For now, default to medium
        return 'medium'

    def _format_attachments(self, attachments: list) -> str:
        """Format attachments list for markdown."""
        if not attachments:
            return "- None"
        
        lines = []
        for att in attachments:
            lines.append(f"- {att['filename']} ({att['mimeType']}, {att['size']} bytes)")
        return '\n'.join(lines)

    def _update_dashboard(self, email_data: dict):
        """Update dashboard with new email activity."""
        dashboard_path = self.vault_path / "Dashboard.md"
        if not dashboard_path.exists():
            return
        
        try:
            content = dashboard_path.read_text()
            lines = content.split('\n')
            new_lines = []
            
            for line in lines:
                if line.strip() == "## Recent Activity":
                    new_lines.append(line)
                    new_lines.append(f"- [{datetime.now().strftime('%H:%M')}] New email: {email_data['subject'][:50]}")
                else:
                    new_lines.append(line)
            
            dashboard_path.write_text('\n'.join(new_lines))
        except Exception as e:
            logger.error(f"Error updating dashboard: {e}")

    def run(self):
        """Main watcher loop."""
        logger.info("Starting Gmail Watcher...")
        
        # Authenticate first
        if not self.authenticate():
            logger.error("Authentication failed. Exiting.")
            return
        
        logger.info(f"Checking for new emails every {self.check_interval} seconds")
        
        try:
            while True:
                try:
                    # Check for new emails
                    new_emails = self.check_for_new_emails()
                    
                    for email in new_emails:
                        email_data = self.get_message_details(email['id'])
                        if email_data:
                            self.create_action_file(email_data)
                    
                    # Sleep until next check
                    time.sleep(self.check_interval)
                    
                except Exception as e:
                    logger.error(f"Error in watcher loop: {e}")
                    time.sleep(10)  # Brief pause before retry
                    
        except KeyboardInterrupt:
            logger.info("Gmail Watcher stopped by user")


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description='Gmail Watcher for AI Employee')
    parser.add_argument('--auth', action='store_true', help='Run authentication flow')
    parser.add_argument('--vault', default='.', help='Path to Obsidian vault')
    parser.add_argument('--interval', type=int, default=120, help='Check interval in seconds')
    parser.add_argument('--port', type=int, default=8080, help='Port for OAuth callback (default: 8080)')

    args = parser.parse_args()

    watcher = GmailWatcher(vault_path=args.vault, check_interval=args.interval)

    if args.auth:
        print("Starting Gmail authentication flow...")
        print("1. Download credentials.json from Google Cloud Console")
        print("2. Place it in this directory")
        print("3. Browser will open for authorization")
        print(f"   Using port: {args.port}")
        print()
        if watcher.authenticate(port=args.port):
            print("[OK] Authentication successful!")
        else:
            print("[ERROR] Authentication failed!")
    else:
        watcher.run()


if __name__ == "__main__":
    main()
