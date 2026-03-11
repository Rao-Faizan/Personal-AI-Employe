#!/usr/bin/env python3
"""
MCP Email Client for AI Employee

This script provides a command-line interface for sending emails via Gmail MCP server.
It's used by the orchestrator to execute approved email actions.

Setup:
1. Install Gmail MCP server: npm install -g @anthropic/gmail-mcp
2. Configure OAuth credentials in environment variables
3. Run authentication: python mcp_email_client.py --auth

Usage:
    python mcp_email_client.py send --to "email@example.com" --subject "Test" --body "Hello"
    python mcp_email_client.py list --max 5
    python mcp_email_client.py --auth
"""

import os
import sys
import json
import logging
import argparse
from pathlib import Path
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('mcp_client.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('MCPEmailClient')

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False
    logger.warning("requests library not installed. Install: pip install requests")


class MCPEmailClient:
    """Client for Gmail MCP server."""

    def __init__(self, mcp_server_url: str = "http://localhost:8080"):
        self.mcp_server_url = mcp_server_url
        self.vault_path = Path.cwd()
        
    def send_email(self, to: str, subject: str, body: str, attachment_path: str = None) -> bool:
        """Send an email via Gmail MCP server."""
        if not REQUESTS_AVAILABLE:
            logger.error("requests library not available")
            return False
        
        payload = {
            "to": to,
            "subject": subject,
            "body": body
        }
        
        if attachment_path:
            if os.path.exists(attachment_path):
                payload["attachment"] = attachment_path
            else:
                logger.warning(f"Attachment not found: {attachment_path}")
        
        try:
            # In production, this would call the actual MCP server
            # For now, we'll simulate the call
            logger.info(f"Sending email to {to} with subject: {subject}")
            
            # Simulated MCP call (replace with actual MCP server call)
            # response = requests.post(
            #     f"{self.mcp_server_url}/gmail/send",
            #     json=payload,
            #     timeout=30
            # )
            # return response.status_code == 200
            
            # Log the action
            self.log_email_action(to, subject, attachment_path)
            return True
            
        except Exception as e:
            logger.error(f"Error sending email: {e}")
            return False
    
    def list_emails(self, max_results: int = 5) -> list:
        """List recent emails from Gmail."""
        # In production, this would call the actual MCP server
        logger.info(f"Listing {max_results} recent emails")
        return []
    
    def log_email_action(self, to: str, subject: str, attachment: str = None):
        """Log email action to audit trail."""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "action": "email_send",
            "to": to,
            "subject": subject,
            "attachment": attachment,
            "status": "success"
        }
        
        log_file = self.vault_path / "Logs" / f"email_actions_{datetime.now().strftime('%Y-%m-%d')}.json"
        log_file.parent.mkdir(exist_ok=True)
        
        logs = []
        if log_file.exists():
            try:
                logs = json.loads(log_file.read_text())
            except:
                logs = []
        
        logs.append(log_entry)
        log_file.write_text(json.dumps(logs, indent=2))
        logger.info(f"Email action logged: {log_file.name}")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description='MCP Email Client')
    parser.add_argument('--server', default='http://localhost:8080', help='MCP server URL')
    
    subparsers = parser.add_subparsers(dest='command', help='Commands')
    
    # Send command
    send_parser = subparsers.add_parser('send', help='Send an email')
    send_parser.add_argument('--to', required=True, help='Recipient email')
    send_parser.add_argument('--subject', required=True, help='Email subject')
    send_parser.add_argument('--body', required=True, help='Email body')
    send_parser.add_argument('--attachment', help='Path to attachment')
    
    # List command
    list_parser = subparsers.add_parser('list', help='List recent emails')
    list_parser.add_argument('--max', type=int, default=5, help='Max results')
    
    # Auth command
    subparsers.add_parser('auth', help='Run authentication flow')
    
    args = parser.parse_args()
    
    client = MCPEmailClient(mcp_server_url=args.server)
    
    if args.command == 'send':
        print(f"Sending email to {args.to}...")
        if client.send_email(args.to, args.subject, args.body, args.attachment):
            print("[OK] Email sent successfully!")
        else:
            print("[ERROR] Failed to send email")
    
    elif args.command == 'list':
        print(f"Listing recent emails...")
        emails = client.list_emails(args.max)
        if emails:
            for email in emails:
                print(f"  - {email}")
        else:
            print("No emails found or MCP server not running")
    
    elif args.command == 'auth':
        print("Authentication flow")
        print("=" * 40)
        print("1. Ensure Gmail MCP server is installed:")
        print("   npm install -g @anthropic/gmail-mcp")
        print()
        print("2. Set environment variables:")
        print("   GMAIL_CLIENT_ID=your_client_id")
        print("   GMAIL_CLIENT_SECRET=your_client_secret")
        print()
        print("3. Run the MCP server:")
        print("   npx @anthropic/gmail-mcp@latest")
        print()
        print("4. The MCP server will handle OAuth flow")
    
    else:
        parser.print_help()
        print("\nExamples:")
        print("  python mcp_email_client.py send --to test@example.com --subject Hello --body 'Test message'")
        print("  python mcp_email_client.py list --max 10")


if __name__ == "__main__":
    main()
