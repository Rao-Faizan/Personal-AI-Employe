#!/usr/bin/env python3
"""
WhatsApp Watcher for AI Employee - Silver/Gold Tier

Monitors WhatsApp Web for new messages matching priority keywords and
creates action files in the Needs_Action folder for Claude to process.

NOTE: Uses WhatsApp Web browser automation via Playwright.
      Be aware of WhatsApp's Terms of Service.

Setup:
1. Install Playwright: pip install playwright && playwright install
2. First run: python whatsapp_watcher.py --login
3. Scan QR code in the browser window
4. Session is saved automatically
5. Run: python whatsapp_watcher.py

Usage:
    python whatsapp_watcher.py --login       # Scan QR code to login
    python whatsapp_watcher.py               # Start watching (continuous)
    python whatsapp_watcher.py --check-once  # Run one check and exit
    python whatsapp_watcher.py --status      # Show session status
"""

import sys
import time
import json
import logging
import codecs
from pathlib import Path
from datetime import datetime
from typing import List, Optional

# Fix Windows console encoding
if sys.platform == 'win32':
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, errors='replace')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, errors='replace')

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('whatsapp_watcher.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('WhatsAppWatcher')

try:
    from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout
    PLAYWRIGHT_AVAILABLE = True
    logger.info("Playwright successfully imported")
except ImportError:
    PLAYWRIGHT_AVAILABLE = False
    logger.warning("Playwright not installed. Run: pip install playwright && playwright install")


# Keywords that flag a message as high-priority
HIGH_PRIORITY_KEYWORDS = [
    'urgent', 'asap', 'invoice', 'payment', 'help', 'emergency',
    'important', 'deadline', 'overdue', 'critical', 'immediately'
]

WHATSAPP_URL = "https://web.whatsapp.com"


class WhatsAppWatcher:
    """Watch WhatsApp Web for new messages and create action files."""

    def __init__(self, vault_path: str = ".", check_interval: int = 30):
        self.vault_path = Path(vault_path)
        self.check_interval = check_interval
        self.session_path = self.vault_path / ".whatsapp_session"
        self.needs_action = self.vault_path / "Needs_Action"
        self.logs_folder = self.vault_path / "Logs"
        self.processed_ids: set = set()

        # Ensure folders exist
        self.session_path.mkdir(exist_ok=True)
        self.needs_action.mkdir(exist_ok=True)
        self.logs_folder.mkdir(exist_ok=True)

        # Load previously processed message IDs
        self._load_processed_ids()

    # ------------------------------------------------------------------
    # Session management
    # ------------------------------------------------------------------

    def _load_processed_ids(self):
        cache_file = self.logs_folder / "whatsapp_processed.json"
        if cache_file.exists():
            try:
                data = json.loads(cache_file.read_text(encoding='utf-8'))
                self.processed_ids = set(data.get("processed_ids", []))
                logger.info(f"Loaded {len(self.processed_ids)} processed message IDs")
            except Exception as e:
                logger.warning(f"Could not load processed IDs: {e}")

    def _save_processed_ids(self):
        cache_file = self.logs_folder / "whatsapp_processed.json"
        ids_list = list(self.processed_ids)[-2000:]  # keep last 2000
        cache_file.write_text(
            json.dumps({"processed_ids": ids_list, "updated": datetime.now().isoformat()}),
            encoding='utf-8'
        )

    def is_logged_in(self) -> bool:
        """Check if a valid WhatsApp session exists."""
        if not PLAYWRIGHT_AVAILABLE:
            return False
        if not self.session_path.exists():
            return False
        session_files = list(self.session_path.glob("**/*"))
        return len(session_files) >= 5

    # ------------------------------------------------------------------
    # Login
    # ------------------------------------------------------------------

    def login(self) -> bool:
        """Open WhatsApp Web for QR code scan and save session."""
        if not PLAYWRIGHT_AVAILABLE:
            logger.error("Playwright not available. Run: pip install playwright && playwright install")
            return False

        logger.info("Opening WhatsApp Web for QR code scan...")
        logger.info("Scan the QR code in the browser window. You have 3 minutes.")

        with sync_playwright() as p:
            browser = p.chromium.launch_persistent_context(
                str(self.session_path),
                headless=False,
                user_agent=(
                    "Mozilla/5.0 (X11; Linux x86_64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/125.0.0.0 Safari/537.36"
                ),
                args=[
                    '--disable-blink-features=AutomationControlled',
                    '--no-sandbox',
                    '--disable-dev-shm-usage',
                ],
                ignore_default_args=['--enable-automation'],
            )

            page = browser.pages[0] if browser.pages else browser.new_page()
            page.goto(WHATSAPP_URL, wait_until="domcontentloaded")

            logger.info("Waiting for WhatsApp to load and QR code to be scanned...")

            try:
                # Wait for the chat list — signals successful login
                page.wait_for_selector('[data-testid="chat-list"], #side', timeout=180000)
                logger.info("Login detected! Saving session...")
                time.sleep(5)  # Let session settle
                browser.close()
                logger.info("[OK] WhatsApp login successful!")
                logger.info(f"Session saved to: {self.session_path}")
                return True

            except PlaywrightTimeout:
                logger.error("Login timeout. Please try again and scan the QR code faster.")
                browser.close()
                return False

    # ------------------------------------------------------------------
    # Message checking
    # ------------------------------------------------------------------

    def check_for_messages(self, debug: bool = False) -> List[dict]:
        """
        Open WhatsApp Web with the saved session and collect unread messages
        that contain high-priority keywords.
        Returns a list of dicts with contact and message text.
        """
        if not PLAYWRIGHT_AVAILABLE:
            logger.error("Playwright not available")
            return []

        if not self.is_logged_in():
            logger.error("Not logged in. Run: python whatsapp_watcher.py --login")
            return []

        messages = []

        with sync_playwright() as p:
            try:
                browser = p.chromium.launch_persistent_context(
                    str(self.session_path),
                    headless=True,
                    user_agent=(
                        "Mozilla/5.0 (X11; Linux x86_64) "
                        "AppleWebKit/537.36 (KHTML, like Gecko) "
                        "Chrome/125.0.0.0 Safari/537.36"
                    ),
                    args=[
                        '--disable-blink-features=AutomationControlled',
                        '--no-sandbox',
                        '--disable-dev-shm-usage',
                    ],
                    ignore_default_args=['--enable-automation'],
                )

                page = browser.pages[0] if browser.pages else browser.new_page()
                logger.info("Opening WhatsApp Web...")
                page.goto(WHATSAPP_URL, wait_until="domcontentloaded", timeout=90000)

                # Give WhatsApp time to initialize from saved session
                logger.info("Waiting for WhatsApp to initialize...")
                time.sleep(8)

                # Wait for chat list — try multiple selectors across WhatsApp Web versions
                chat_loaded = False
                for selector in [
                    '[data-testid="chat-list"]',
                    '#side',
                    'div[aria-label="Chat list"]',
                    '[data-testid="cell-frame-container"]',
                    'div[role="grid"]',
                ]:
                    try:
                        page.wait_for_selector(selector, timeout=15000)
                        logger.info(f"WhatsApp loaded (selector: {selector})")
                        chat_loaded = True
                        break
                    except PlaywrightTimeout:
                        continue

                if not chat_loaded:
                    logger.error("WhatsApp did not load. Session may have expired — run --login again.")
                    try:
                        page.screenshot(path="whatsapp_load_error.png")
                        logger.info("Screenshot saved: whatsapp_load_error.png")
                    except Exception:
                        pass
                    browser.close()
                    return []

                time.sleep(3)

                # Get all chat items in the chat list
                all_chats = page.locator('[aria-label="Chat list"] > div').all()
                logger.info(f"Found {len(all_chats)} chat entries")

                for chat in all_chats:
                    try:
                        # Check for unread badge (div._ahlk contains the unread count span)
                        unread_badge = chat.locator('div._ahlk span')
                        if unread_badge.count() == 0:
                            continue

                        # Confirm badge has a numeric count
                        badge_text = unread_badge.first.inner_text(timeout=1000).strip()
                        if not badge_text or not any(c.isdigit() for c in badge_text):
                            continue

                        # Get contact name from title span
                        name_el = chat.locator('span[dir="auto"][title]')
                        contact = name_el.first.get_attribute('title', timeout=2000) if name_el.count() > 0 else "Unknown"
                        if not contact:
                            contact = name_el.first.inner_text(timeout=2000) if name_el.count() > 0 else "Unknown"

                        # Get message preview (last message text)
                        preview_el = chat.locator('span[dir="ltr"], span[dir="auto"]:not([title])')
                        preview = ""
                        for i in range(min(preview_el.count(), 5)):
                            text = preview_el.nth(i).inner_text(timeout=1000).strip()
                            if text and len(text) > 3 and text != contact:
                                preview = text
                                break

                        # Check for priority keywords in contact name or preview
                        combined = (contact + " " + preview).lower()
                        matched_keywords = [kw for kw in HIGH_PRIORITY_KEYWORDS if kw in combined]

                        msg_id = f"{contact}_{preview[:30]}_{badge_text}".replace(" ", "_")

                        if debug:
                            logger.info(f"  [UNREAD {badge_text}] {contact}: {preview[:60]}")

                        if msg_id not in self.processed_ids:
                            if matched_keywords:
                                messages.append({
                                    "id": msg_id,
                                    "contact": contact,
                                    "preview": preview,
                                    "keywords": matched_keywords,
                                    "unread_count": badge_text,
                                    "timestamp": datetime.now().isoformat()
                                })
                                logger.info(f"Priority message [{badge_text} unread] from {contact}: {preview[:60]}")
                            else:
                                logger.debug(f"Unread [{badge_text}] from {contact} — no keywords, skipping")

                    except Exception as e:
                        logger.debug(f"Error reading chat entry: {e}")
                        continue

                browser.close()

            except Exception as e:
                logger.error(f"Error checking WhatsApp messages: {e}")

        return messages

    # ------------------------------------------------------------------
    # Action file creation
    # ------------------------------------------------------------------

    def create_action_file(self, message: dict) -> Optional[Path]:
        """Create a Needs_Action .md file for a priority WhatsApp message."""
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        safe_contact = message['contact'][:20].replace(' ', '_').replace(':', '')
        filename = f"WHATSAPP_{timestamp}_{safe_contact}.md"
        action_path = self.needs_action / filename

        priority = "high" if any(kw in ['urgent', 'asap', 'emergency', 'critical'] for kw in message['keywords']) else "medium"

        content = f"""---
type: whatsapp_message
contact: {message['contact']}
received: {message['timestamp']}
priority: {priority}
keywords: {', '.join(message['keywords'])}
status: pending
---

# WhatsApp Message - Action Required

## Message Details
- **From:** {message['contact']}
- **Received:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
- **Priority:** {priority}
- **Unread Count:** {message.get('unread_count', '?')}
- **Keywords Detected:** {', '.join(message['keywords'])}

## Message Preview
{message['preview']}

## Suggested Actions
- [ ] Open WhatsApp Web and read the full message
- [ ] Determine appropriate response
- [ ] Draft reply (move to Pending_Approval if sensitive)
- [ ] Respond to {message['contact']}
- [ ] Move this file to Done when resolved

## Notes
Add context or response strategy here.
"""

        action_path.write_text(content, encoding='utf-8')
        logger.info(f"Created action file: {filename}")

        # Mark as processed
        self.processed_ids.add(message['id'])
        self._save_processed_ids()

        # Update dashboard
        self._update_dashboard(message['contact'], message['preview'])

        return action_path

    def _update_dashboard(self, contact: str, preview: str):
        dashboard_path = self.vault_path / "Dashboard.md"
        if not dashboard_path.exists():
            return
        try:
            content = dashboard_path.read_text(encoding='utf-8')
            lines = content.split('\n')
            new_lines = []
            for line in lines:
                if line.strip() == "## Recent Activity":
                    new_lines.append(line)
                    new_lines.append(
                        f"- [{datetime.now().strftime('%H:%M')}] "
                        f"WhatsApp priority message from {contact}: {preview[:40]}..."
                    )
                else:
                    new_lines.append(line)
            dashboard_path.write_text('\n'.join(new_lines), encoding='utf-8')
        except Exception as e:
            logger.error(f"Error updating dashboard: {e}")

    # ------------------------------------------------------------------
    # Main loop
    # ------------------------------------------------------------------

    def run_once(self, debug: bool = False) -> int:
        """Run a single check cycle. Returns number of action files created."""
        logger.info("Checking WhatsApp for new priority messages...")
        messages = self.check_for_messages(debug=debug)
        count = 0
        for msg in messages:
            if self.create_action_file(msg):
                count += 1
        logger.info(f"WhatsApp check complete. {count} new action file(s) created.")
        return count

    def run(self):
        """Run the watcher continuously."""
        if not self.is_logged_in():
            logger.error("Not logged in. Run: python whatsapp_watcher.py --login")
            return

        logger.info(f"WhatsApp Watcher started (checking every {self.check_interval}s)")
        logger.info("Press Ctrl+C to stop")

        try:
            while True:
                try:
                    self.run_once()
                except Exception as e:
                    logger.error(f"Error in watcher loop: {e}")
                time.sleep(self.check_interval)
        except KeyboardInterrupt:
            logger.info("WhatsApp Watcher stopped by user")


def main():
    import argparse

    if not PLAYWRIGHT_AVAILABLE:
        print("\n" + "=" * 60)
        print("ERROR: Playwright not installed!")
        print("=" * 60)
        print("\nInstall Playwright:")
        print("  pip install playwright")
        print("  playwright install")
        print("=" * 60 + "\n")
        return

    parser = argparse.ArgumentParser(description='WhatsApp Watcher for AI Employee')
    parser.add_argument('--login', action='store_true', help='Scan QR code to login')
    parser.add_argument('--check-once', action='store_true', help='Run one check and exit')
    parser.add_argument('--debug', action='store_true', help='Show all unread chats regardless of keywords')
    parser.add_argument('--status', action='store_true', help='Show session status')
    parser.add_argument('--vault', default='.', help='Path to Obsidian vault')
    parser.add_argument('--interval', type=int, default=30, help='Check interval in seconds')

    args = parser.parse_args()
    watcher = WhatsAppWatcher(vault_path=args.vault, check_interval=args.interval)

    if args.login:
        print("WhatsApp Login")
        print("=" * 40)
        print("A browser will open. Scan the QR code with your phone.")
        print("WhatsApp → Linked Devices → Link a Device")
        print()
        if watcher.login():
            print("\n[OK] Login successful!")
            print("\nNext step:")
            print("  python whatsapp_watcher.py")
        else:
            print("\n[ERROR] Login failed. Try again.")

    elif args.status:
        print("WhatsApp Watcher Status")
        print("=" * 40)
        logged_in = watcher.is_logged_in()
        print(f"Session exists: {'Yes' if logged_in else 'No'}")
        print(f"Session path:   {watcher.session_path}")
        print(f"Processed IDs:  {len(watcher.processed_ids)}")
        if not logged_in:
            print("\nRun: python whatsapp_watcher.py --login")

    elif args.check_once:
        print("Running single WhatsApp check...")
        count = watcher.run_once(debug=args.debug)
        print(f"\n[OK] Created {count} action file(s)")

    else:
        print("WhatsApp Watcher - Gold Tier")
        print("=" * 40)
        if not watcher.is_logged_in():
            print("\n[ERROR] Not logged in!")
            print("Run: python whatsapp_watcher.py --login")
            return
        watcher.run()


if __name__ == "__main__":
    main()
