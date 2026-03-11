#!/usr/bin/env python3
"""
LinkedIn Poster using Playwright

Posts to LinkedIn using browser automation (no API required).
Uses Playwright to automate LinkedIn web interface.

Setup:
1. Install Playwright: pip install playwright
2. Install browsers: playwright install
3. First run: python linkedin_poster.py --login
4. Login to LinkedIn manually (session will be saved)
5. Post: python linkedin_poster.py --post "Your post text"

Usage:
    python linkedin_poster.py --login      # Login to LinkedIn
    python linkedin_poster.py --post "Text"  # Create post (requires approval)
    python linkedin_poster.py --post-now "Text"  # Post immediately
    python linkedin_poster.py --process    # Process approved posts
"""

import os
import sys
import time
import logging
import codecs
import json
from pathlib import Path
from datetime import datetime
from typing import Optional

# Fix Windows console encoding
if sys.platform == 'win32':
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, errors='replace')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, errors='replace')

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('linkedin.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('LinkedInPoster')

try:
    from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False
    logger.warning("Playwright not installed. Run: pip install playwright && playwright install")


class LinkedInPoster:
    """Post to LinkedIn using browser automation."""

    def __init__(self, vault_path: str = "."):
        self.vault_path = Path(vault_path)
        self.session_path = self.vault_path / ".linkedin_session"
        self.pending_approval = self.vault_path / "Pending_Approval"
        self.approved_folder = self.vault_path / "Approved" / "Social"
        self.done_folder = self.vault_path / "Done"
        
        # Ensure folders exist
        self.session_path.mkdir(exist_ok=True)
        self.pending_approval.mkdir(exist_ok=True)
        self.approved_folder.mkdir(exist_ok=True, parents=True)
        self.done_folder.mkdir(exist_ok=True)
        
        self.linkedin_url = "https://www.linkedin.com/feed/"

    def login(self) -> bool:
        """Login to LinkedIn and save session."""
        if not PLAYWRIGHT_AVAILABLE:
            logger.error("Playwright not available. Install: pip install playwright && playwright install")
            return False
        
        logger.info("Starting LinkedIn login...")
        logger.info("A browser window will open. Please login to LinkedIn.")
        logger.info("After login, the browser will close automatically in 5 seconds.")
        
        with sync_playwright() as p:
            # Launch browser with persistent context
            browser = p.chromium.launch_persistent_context(
                str(self.session_path),
                headless=False,  # Show browser for manual login
                args=[
                    '--disable-blink-features=AutomationControlled',
                    '--no-sandbox'
                ]
            )
            
            page = browser.pages[0] if browser.pages else browser.new_page()
            
            # Go to LinkedIn
            logger.info("Opening LinkedIn...")
            page.goto("https://www.linkedin.com/login", wait_until="networkidle")
            
            # Wait for user to login (max 5 minutes)
            logger.info("Please login to LinkedIn in the browser window...")
            logger.info("You have 5 minutes to login.")
            
            # Wait for feed page (indicates successful login)
            try:
                page.wait_for_url("https://www.linkedin.com/feed/*", timeout=300000)
                logger.info("Login detected!")
                
                # Wait a bit more to ensure session is saved
                time.sleep(5)
                
                # Close browser
                browser.close()
                
                logger.info("[OK] LinkedIn login successful!")
                logger.info(f"Session saved to: {self.session_path}")
                return True
                
            except PlaywrightTimeout:
                logger.error("Login timeout. Please try again.")
                browser.close()
                return False

    def is_logged_in(self) -> bool:
        """Check if we have a valid LinkedIn session."""
        if not PLAYWRIGHT_AVAILABLE:
            return False
        
        # Check if session directory exists and has data
        if not self.session_path.exists():
            return False
        
        # Check if session directory has any files
        session_files = list(self.session_path.glob("**/*"))
        if len(session_files) < 5:  # Should have multiple session files
            return False
        
        return True

    def create_post(self, text: str) -> bool:
        """Create a post on LinkedIn using browser automation."""
        if not PLAYWRIGHT_AVAILABLE:
            logger.error("Playwright not available")
            return False
        
        if not self.is_logged_in():
            logger.error("Not logged in! Run: python linkedin_poster.py --login")
            return False
        
        logger.info("Creating LinkedIn post...")
        
        with sync_playwright() as p:
            try:
                # Launch browser with saved session
                browser = p.chromium.launch_persistent_context(
                    str(self.session_path),
                    headless=False,  # Show browser
                    args=[
                        '--disable-blink-features=AutomationControlled',
                        '--disable-features=OptimizationHints',
                        '--disable-dev-shm-usage',
                        '--no-sandbox',
                        '--disable-setuid-sandbox'
                    ],
                    ignore_default_args=['--enable-automation'],
                    slow_mo=0  # FAST - no delay
                )
                
                page = browser.pages[0] if browser.pages else browser.new_page()
                
                # Go to LinkedIn feed
                logger.info("Opening LinkedIn feed...")
                page.goto(self.linkedin_url, wait_until="domcontentloaded", timeout=60000)
                
                # Wait for page to fully load
                time.sleep(5)
                
                # Wait for post input box
                logger.info("Waiting for post input box...")
                try:
                    # Click on the "Start a post" button
                    start_post_button = page.locator('button:has-text("Start a post"), [aria-label="Start a post"]').first
                    start_post_button.click(timeout=15000)
                    logger.info("Clicked 'Start a post' button")
                    
                    # Wait for composer to open
                    time.sleep(3)
                except Exception as e:
                    logger.warning(f"Could not find start post button: {e}")
                    # Try alternative selector
                    try:
                        page.click('[data-id="gh-create-a-post"]', timeout=5000)
                        time.sleep(3)
                    except:
                        logger.error("Could not open post composer")
                        browser.close()
                        return False
                
                # Wait for text input
                time.sleep(2)
                
                # Find and fill the text area
                logger.info("Entering post text...")
                try:
                    # Try different selectors for the post text area
                    text_area = None
                    selectors = [
                        '[aria-label="What do you want to talk about?"]',
                        '[aria-label="What do you want to talk about?"]',
                        'div[contenteditable="true"][role="textbox"]',
                        '.ql-editor'
                    ]
                    
                    for selector in selectors:
                        try:
                            text_area = page.locator(selector).first
                            if text_area.count() > 0:
                                break
                            text_area = None
                        except:
                            continue
                    
                    if text_area:
                        # FAST typing - fill directly
                        text_area.fill(text, timeout=10000)
                        logger.info("Post text entered (fast)")
                        time.sleep(2)
                    else:
                        logger.error("Could not find text input area")
                        browser.close()
                        return False
                        
                except Exception as e:
                    logger.error(f"Error filling text: {e}")
                    browser.close()
                    return False
                
                # Wait for text to be entered
                time.sleep(2)
                
                # Click Post button (specific selector to avoid privacy dropdown)
                logger.info("Clicking Post button...")
                time.sleep(1)

                try:
                    # CORRECT SELECTOR - The blue Post button
                    post_button = page.locator('button.share-actions__primary-action').first
                    
                    # Verify
                    btn_text = post_button.inner_text(timeout=5000)
                    logger.info(f"Found button: '{btn_text}'")
                    
                    if "Post" in btn_text:
                        # Click directly
                        post_button.click(timeout=10000)
                        logger.info("Post button clicked!")
                        
                        # Wait for submission
                        time.sleep(8)
                        
                        # Screenshot
                        try:
                            page.screenshot(path="linkedin_success.png")
                        except:
                            pass

                        logger.info("[OK] Post created successfully!")
                        browser.close()
                        return True
                    else:
                        logger.error(f"Wrong button: '{btn_text}'")
                        browser.close()
                        return False

                except Exception as e:
                    logger.error(f"Error: {e}")
                    
                    # Fallback: JavaScript with correct selector
                    logger.info("JavaScript fallback with share-actions__primary-action...")
                    result = page.evaluate("""
                        () => {
                            const btn = document.querySelector('button.share-actions__primary-action');
                            if (btn && !btn.disabled) {
                                btn.click();
                                return true;
                            }
                            return false;
                        }
                    """)
                    
                    if result:
                        logger.info("JavaScript click successful!")
                        time.sleep(5)
                        browser.close()
                        return True
                    else:
                        logger.error("JavaScript also failed")
                        browser.close()
                        return False
                        time.sleep(3)
                        
                        # Take screenshot
                        try:
                            page.screenshot(path="linkedin_posted.png")
                        except:
                            pass
                        
                        logger.info("[OK] Post submitted via keyboard!")
                        browser.close()
                        return True

                except Exception as e:
                    logger.error(f"Error clicking post button: {e}")
                    try:
                        page.screenshot(path="linkedin_error.png")
                        logger.info(f"Screenshot saved: linkedin_error.png")
                    except:
                        pass
                    browser.close()
                    return False
                
            except Exception as e:
                logger.error(f"Error creating post: {e}")
                return False

    def create_approval_request(self, post_text: str) -> Optional[Path]:
        """Create an approval request file for the post."""
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        filename = f"SOCIAL_LINKEDIN_{timestamp}.md"
        approval_path = self.pending_approval / filename
        
        # Truncate for filename
        preview = post_text[:30].replace('\n', ' ').replace(':', '')
        
        content = f"""---
type: social_media_post
platform: LinkedIn
created: {datetime.now().isoformat()}
status: pending_approval
preview: {preview}
---

# LinkedIn Post Approval Request

## Post Content
{post_text}

## Details
- **Platform:** LinkedIn
- **Visibility:** Public
- **Posted by:** AI Employee

## To Approve
Move this file to: `/Approved/Social/`

## To Reject
Move this file to: `/Rejected/` with reason.

## To Edit
Edit the post content above, then move to `/Approved/Social/`
"""
        
        approval_path.write_text(content, encoding='utf-8')
        logger.info(f"Approval request created: {approval_path}")
        
        # Update dashboard
        self._update_dashboard(preview)
        
        return approval_path

    def _update_dashboard(self, post_preview: str):
        """Update dashboard with pending post."""
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
                    new_lines.append(f"- [{datetime.now().strftime('%H:%M')}] LinkedIn post pending: {post_preview}...")
                else:
                    new_lines.append(line)
            
            dashboard_path.write_text('\n'.join(new_lines), encoding='utf-8')
        except Exception as e:
            logger.error(f"Error updating dashboard: {e}")

    def process_approved_posts(self) -> int:
        """Process approved posts from Approved/Social folder."""
        if not self.approved_folder.exists():
            return 0
        
        approved_files = list(self.approved_folder.glob("SOCIAL_LINKEDIN_*.md"))
        posted_count = 0
        
        for file_path in approved_files:
            logger.info(f"Processing approved post: {file_path.name}")
            
            content = file_path.read_text(encoding='utf-8')
            
            # Extract post content
            if "## Post Content" in content:
                start = content.find("## Post Content") + len("## Post Content")
                end = content.find("## Details") if "## Details" in content else len(content)
                post_text = content[start:end].strip()
                
                # Create the post
                if self.create_post(post_text):
                    posted_count += 1
                    
                    # Move to Done
                    done_path = self.done_folder / f"POSTED_{file_path.name}"
                    file_path.rename(done_path)
                    logger.info(f"Post moved to Done: {done_path}")
                    
                    # Log the action
                    self._log_post_action(file_path.name, post_text[:100])
                else:
                    logger.error(f"Failed to post: {file_path.name}")
        
        return posted_count

    def _log_post_action(self, filename: str, post_preview: str):
        """Log the post action."""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "action": "linkedin_post",
            "file": filename,
            "preview": post_preview,
            "status": "success"
        }
        
        log_file = self.vault_path / "Logs" / "linkedin_posts.json"
        log_file.parent.mkdir(exist_ok=True)
        
        logs = []
        if log_file.exists():
            try:
                logs = json.loads(log_file.read_text())
            except:
                logs = []
        
        logs.append(log_entry)
        log_file.write_text(json.dumps(logs, indent=2))


def main():
    """Main entry point."""
    import argparse
    
    if not PLAYWRIGHT_AVAILABLE:
        print("\n" + "="*60)
        print("ERROR: Playwright not installed!")
        print("="*60)
        print("\nInstall Playwright:")
        print("  pip install playwright")
        print("  playwright install")
        print("\nOr use demo mode:")
        print("  python linkedin_poster.py --demo")
        print("="*60 + "\n")
        return
    
    parser = argparse.ArgumentParser(description='LinkedIn Poster for AI Employee')
    parser.add_argument('--login', action='store_true', help='Login to LinkedIn')
    parser.add_argument('--post', type=str, help='Create a new post (requires approval)')
    parser.add_argument('--post-now', type=str, help='Post immediately')
    parser.add_argument('--process', action='store_true', help='Process approved posts')
    parser.add_argument('--demo', action='store_true', help='Demo mode (no actual posting)')
    parser.add_argument('--vault', default='.', help='Path to Obsidian vault')
    
    args = parser.parse_args()
    
    poster = LinkedInPoster(vault_path=args.vault)
    
    if args.login:
        print("LinkedIn Login")
        print("=" * 40)
        if poster.login():
            print("\n[OK] Login successful!")
            print("\nNext steps:")
            print("  python linkedin_poster.py --post \"Your post text\"")
        else:
            print("\n[ERROR] Login failed!")
    
    elif args.post:
        print("Creating LinkedIn Post Approval Request")
        print("=" * 40)
        
        if not poster.is_logged_in():
            print("\n[WARNING] Not logged in to LinkedIn!")
            print("Run: python linkedin_poster.py --login")
            print("\nContinuing with approval request creation...\n")
        
        approval_file = poster.create_approval_request(args.post)
        if approval_file:
            print(f"\n[OK] Approval request created: {approval_file}")
            print("\nNext steps:")
            print(f"1. Review and move to Approved/Social/: {approval_file}")
            print("2. Run: python linkedin_poster.py --process")
    
    elif args.post_now:
        print("Posting to LinkedIn (Immediate)")
        print("=" * 40)
        
        if not poster.is_logged_in():
            print("\n[ERROR] Not logged in!")
            print("Run: python linkedin_poster.py --login")
            return
        
        if poster.create_post(args.post_now):
            print("\n[OK] Post created successfully!")
        else:
            print("\n[ERROR] Failed to create post")
    
    elif args.process:
        print("Processing Approved Posts")
        print("=" * 40)
        
        if not poster.is_logged_in():
            print("\n[ERROR] Not logged in!")
            print("Run: python linkedin_poster.py --login")
            return
        
        count = poster.process_approved_posts()
        print(f"\n[OK] Posted {count} message(s) to LinkedIn")
    
    elif args.demo:
        print("LinkedIn Poster - Demo Mode")
        print("=" * 40)
        print("\nThis is a demo. No actual posts will be made.")
        print("\nCommands:")
        print("  --login    Login to LinkedIn (saves session)")
        print("  --post     Create post approval request")
        print("  --post-now Post immediately")
        print("  --process  Process approved posts")
        print("\nExample:")
        print('  python linkedin_poster.py --post "Hello LinkedIn!"')
    
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
