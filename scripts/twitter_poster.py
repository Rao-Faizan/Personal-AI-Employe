#!/usr/bin/env python3
"""
Twitter/X Poster for AI Employee - Gold Tier

Posts to Twitter/X using browser automation (no API required).
Uses Playwright to automate Twitter web interface.

Setup:
1. Install Playwright: pip install playwright
2. Install browsers: playwright install
3. First run: python twitter_poster.py --login
4. Login to Twitter manually (session will be saved)
5. Post: python twitter_poster.py --post "Your tweet text"

Usage:
    python twitter_poster.py --login      # Login to Twitter
    python twitter_poster.py --post "Text"  # Create tweet (requires approval)
    python twitter_poster.py --post-now "Text"  # Post immediately
    python twitter_poster.py --process    # Process approved posts
    python twitter_poster.py --thread     # Create a thread
"""

import os
import sys
import time
import logging
import codecs
import json
from pathlib import Path
from datetime import datetime
from typing import Optional, List

# Fix Windows console encoding
if sys.platform == 'win32':
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, errors='replace')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, errors='replace')

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('twitter.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('TwitterPoster')

try:
    from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout
    PLAYWRIGHT_AVAILABLE = True
    logger.info("Playwright successfully imported")
except ImportError as e:
    PLAYWRIGHT_AVAILABLE = False
    logger.warning(f"Playwright import failed: {e}")
    logger.warning("Try: python -m playwright install")


class TwitterPoster:
    """Post to Twitter/X using browser automation."""

    def __init__(self, vault_path: str = "."):
        self.vault_path = Path(vault_path)
        self.session_path = self.vault_path / ".twitter_session"
        self.pending_approval = self.vault_path / "Pending_Approval"
        self.approved_folder = self.vault_path / "Approved" / "Social"
        self.done_folder = self.vault_path / "Done"

        # Ensure folders exist
        self.session_path.mkdir(exist_ok=True)
        self.pending_approval.mkdir(exist_ok=True)
        self.approved_folder.mkdir(exist_ok=True, parents=True)
        self.done_folder.mkdir(exist_ok=True)

        self.twitter_url = "https://twitter.com/home"

    def login(self) -> bool:
        """Login to Twitter and save session."""
        if not PLAYWRIGHT_AVAILABLE:
            logger.error("Playwright not available. Install: pip install playwright && playwright install")
            return False

        logger.info("Starting Twitter login...")
        logger.info("A browser window will open. Please login to Twitter/X.")
        logger.info("After login, wait 10 seconds for session to save.")

        with sync_playwright() as p:
            # Launch browser with persistent context
            browser = p.chromium.launch_persistent_context(
                str(self.session_path),
                headless=False,  # Show browser for manual login
                args=[
                    '--disable-blink-features=AutomationControlled',
                    '--disable-features=OptimizationHints',
                    '--disable-dev-shm-usage',
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                    '--disable-web-security',
                    '--disable-features=IsolateOrigins,site-per-process'
                ],
                ignore_default_args=['--enable-automation'],
                slow_mo=1000  # Slow down for manual login
            )

            page = browser.pages[0] if browser.pages else browser.new_page()

            # Go to Twitter
            logger.info("Opening Twitter...")
            page.goto("https://twitter.com/login", wait_until="domcontentloaded")
            
            # Wait for user to login (max 5 minutes)
            logger.info("Please login to Twitter/X in the browser window...")
            logger.info("You have 5 minutes to login.")

            # Wait for home timeline (indicates successful login)
            try:
                page.wait_for_url("https://twitter.com/home*", timeout=300000)
                logger.info("Login detected!")

                # Wait more time to ensure session is saved
                logger.info("Waiting for session to save...")
                time.sleep(10)

                # Close browser
                browser.close()

                logger.info("[OK] Twitter login successful!")
                logger.info(f"Session saved to: {self.session_path}")
                return True

            except PlaywrightTimeout:
                logger.error("Login timeout. Please try again.")
                browser.close()
                return False

    def is_logged_in(self) -> bool:
        """Check if we have a valid Twitter session."""
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

    def create_tweet(self, text: str) -> bool:
        """Create a tweet on Twitter using browser automation."""
        if not PLAYWRIGHT_AVAILABLE:
            logger.error("Playwright not available")
            return False

        if not self.is_logged_in():
            logger.error("Not logged in! Run: python twitter_poster.py --login")
            return False

        logger.info("Creating tweet...")

        with sync_playwright() as p:
            try:
                # Launch browser with saved session
                browser = p.chromium.launch_persistent_context(
                    str(self.session_path),
                    headless=True,  # Run in background
                    args=[
                        '--disable-blink-features=AutomationControlled',
                        '--no-sandbox'
                    ]
                )

                page = browser.pages[0] if browser.pages else browser.new_page()

                # Go to Twitter home
                logger.info("Opening Twitter home...")
                try:
                    page.goto(self.twitter_url, wait_until="domcontentloaded", timeout=90000)
                    logger.info("Twitter page loaded")
                    
                    # Wait for page to stabilize
                    time.sleep(5)
                    
                    # Check if we're on the right page
                    current_url = page.url
                    logger.info(f"Current URL: {current_url}")
                    
                except Exception as e:
                    logger.error(f"Error loading Twitter: {e}")
                    # Try alternative URL
                    page.goto("https://x.com/home", wait_until="domcontentloaded", timeout=60000)
                    time.sleep(3)

                # Wait for tweet composer
                logger.info("Waiting for tweet composer...")
                time.sleep(3)

                # Find and click the tweet button
                try:
                    # Click on "What is happening?!" or the tweet button
                    tweet_button = page.locator('[data-testid="tweetButton"], [data-testid="TweetButton"]').first
                    logger.info("Found tweet composer")
                except Exception as e:
                    logger.warning(f"Could not find tweet button: {e}")

                # Find the text area and fill it
                logger.info("Waiting for tweet composer to load...")
                time.sleep(5)  # Wait for composer to fully load
                
                logger.info("Entering tweet text...")
                try:
                    # Try multiple selectors for Twitter's text area
                    text_area = None
                    selectors = [
                        'div[contenteditable="true"][role="textbox"]',
                        '[data-testid="tweetTextarea_0"]',
                        '.public-DraftEditor-content',
                        '[aria-label="Tweet text"]',
                        'div[aria-label="What\'s happening?"]'
                    ]
                    
                    for selector in selectors:
                        try:
                            locator = page.locator(selector).first
                            if locator.count() > 0:
                                text_area = locator
                                logger.info(f"Found text area with selector: {selector}")
                                break
                        except:
                            continue
                    
                    if text_area:
                        # Click to focus
                        text_area.click()
                        time.sleep(1)
                        
                        # Clear existing text
                        page.keyboard.press('Control+A')
                        time.sleep(0.5)
                        page.keyboard.press('Delete')
                        time.sleep(0.5)
                        
                        # Type the tweet text
                        text_area.type(text, delay=30)
                        logger.info("Tweet text entered successfully")
                    else:
                        # Fallback: Use keyboard to type directly
                        logger.info("Using fallback method - direct keyboard input")
                        page.keyboard.type(text, delay=30)
                        logger.info("Tweet text entered via keyboard")

                except Exception as e:
                    logger.error(f"Error entering tweet text: {e}")
                    # Take screenshot for debugging
                    try:
                        page.screenshot(path="twitter_error.png")
                        logger.info(f"Screenshot saved: twitter_error.png")
                    except:
                        pass
                    browser.close()
                    return False

                # Wait for text to be entered
                time.sleep(2)

                # Click Post button
                logger.info("Clicking Post button...")
                try:
                    # Try multiple selectors for Post button
                    post_button = None
                    post_selectors = [
                        '[data-testid="tweetButton"]',
                        '[data-testid="TweetButton"]',
                        'div[role="button"]:has-text("Post")',
                        'div[role="button"]:has-text("Tweet")'
                    ]
                    
                    for selector in post_selectors:
                        try:
                            locator = page.locator(selector).first
                            if locator.count() > 0:
                                post_button = locator
                                logger.info(f"Found post button with: {selector}")
                                break
                        except:
                            continue
                    
                    if post_button:
                        post_button.click(timeout=15000)
                        logger.info("Post button clicked!")
                        
                        # Wait for confirmation
                        time.sleep(5)
                        
                        logger.info("[OK] Tweet created successfully!")
                        browser.close()
                        return True
                    else:
                        logger.error("Could not find post button")
                        browser.close()
                        return False

                except Exception as e:
                    logger.error(f"Error clicking post button: {e}")
                    try:
                        page.screenshot(path="twitter_post_error.png")
                        logger.info("Screenshot saved: twitter_post_error.png")
                    except:
                        pass
                    browser.close()
                    return False

            except Exception as e:
                logger.error(f"Error creating tweet: {e}")
                return False

    def create_thread(self, tweets: List[str]) -> bool:
        """Create a Twitter thread."""
        if not PLAYWRIGHT_AVAILABLE:
            logger.error("Playwright not available")
            return False

        if not self.is_logged_in():
            logger.error("Not logged in! Run: python twitter_poster.py --login")
            return False

        logger.info(f"Creating Twitter thread with {len(tweets)} tweets...")

        with sync_playwright() as p:
            try:
                browser = p.chromium.launch_persistent_context(
                    str(self.session_path),
                    headless=True,
                    args=['--disable-blink-features=AutomationControlled', '--no-sandbox']
                )

                page = browser.pages[0] if browser.pages else browser.new_page()
                page.goto(self.twitter_url, wait_until="networkidle", timeout=60000)
                time.sleep(3)

                # Enter first tweet
                text_area = page.locator('[data-testid="tweetTextarea_0"]').first
                text_area.click()
                page.keyboard.press('Control+A')
                page.keyboard.press('Delete')
                text_area.type(tweets[0], delay=50)
                time.sleep(2)

                # Add remaining tweets in thread
                for i, tweet_text in enumerate(tweets[1:], 1):
                    logger.info(f"Adding tweet {i+1} to thread...")
                    
                    # Click "Add another post" button
                    add_button = page.locator('[data-testid="addTweet"]').first
                    add_button.click()
                    time.sleep(2)

                    # Find the new text area and fill it
                    text_areas = page.locator('[data-testid="tweetTextarea_0"]').all()
                    if len(text_areas) > i:
                        text_areas[i].click()
                        page.keyboard.press('Control+A')
                        page.keyboard.press('Delete')
                        text_areas[i].type(tweet_text, delay=50)
                        time.sleep(2)

                # Post the thread
                post_button = page.locator('[data-testid="tweetButton"]').first
                post_button.click()
                time.sleep(3)

                logger.info("[OK] Twitter thread created successfully!")
                browser.close()
                return True

            except Exception as e:
                logger.error(f"Error creating thread: {e}")
                return False

    def create_approval_request(self, post_text: str, is_thread: bool = False) -> Optional[Path]:
        """Create an approval request file for the tweet."""
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        filename = f"SOCIAL_TWITTER_{timestamp}.md"
        approval_path = self.pending_approval / filename

        # Truncate for filename
        preview = post_text[:30].replace('\n', ' ').replace(':', '')

        content = f"""---
type: social_media_post
platform: Twitter/X
created: {datetime.now().isoformat()}
status: pending_approval
preview: {preview}
is_thread: {is_thread}
---

# Twitter Post Approval Request

## Post Content
{post_text}

## Details
- **Platform:** Twitter/X
- **Visibility:** Public
- **Posted by:** AI Employee
- **Type:** {"Thread" if is_thread else "Single Tweet"}

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
                    new_lines.append(f"- [{datetime.now().strftime('%H:%M')}] Twitter post pending: {post_preview}...")
                else:
                    new_lines.append(line)

            dashboard_path.write_text('\n'.join(new_lines), encoding='utf-8')
        except Exception as e:
            logger.error(f"Error updating dashboard: {e}")

    def process_approved_posts(self) -> int:
        """Process approved posts from Approved/Social folder."""
        if not self.approved_folder.exists():
            return 0

        approved_files = list(self.approved_folder.glob("SOCIAL_TWITTER_*.md"))
        posted_count = 0

        for file_path in approved_files:
            logger.info(f"Processing approved tweet: {file_path.name}")

            content = file_path.read_text(encoding='utf-8')

            # Extract post content
            if "## Post Content" in content:
                start = content.find("## Post Content") + len("## Post Content")
                end = content.find("## Details") if "## Details" in content else len(content)
                post_text = content[start:end].strip()

                # Check if it's a thread
                is_thread = "is_thread: True" in content

                # Create the post
                if is_thread:
                    tweets = [t.strip() for t in post_text.split('\n\n') if t.strip()]
                    success = self.create_thread(tweets)
                else:
                    success = self.create_tweet(post_text)

                if success:
                    posted_count += 1

                    # Move to Done
                    done_path = self.done_folder / f"POSTED_{file_path.name}"
                    file_path.rename(done_path)
                    logger.info(f"Tweet moved to Done: {done_path}")

                    # Log the action
                    self._log_post_action(file_path.name, post_text[:100])
                else:
                    logger.error(f"Failed to post: {file_path.name}")

        return posted_count

    def _log_post_action(self, filename: str, post_preview: str):
        """Log the post action."""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "action": "twitter_post",
            "file": filename,
            "preview": post_preview,
            "status": "success"
        }

        log_file = self.vault_path / "Logs" / "twitter_posts.json"
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
        print("="*60 + "\n")
        return

    parser = argparse.ArgumentParser(description='Twitter/X Poster for AI Employee')
    parser.add_argument('--login', action='store_true', help='Login to Twitter')
    parser.add_argument('--post', type=str, help='Create a new tweet (requires approval)')
    parser.add_argument('--post-now', type=str, help='Post tweet immediately')
    parser.add_argument('--thread', type=str, help='Create a thread (tweets separated by |||)')
    parser.add_argument('--process', action='store_true', help='Process approved posts')
    parser.add_argument('--demo', action='store_true', help='Demo mode (no actual posting)')
    parser.add_argument('--vault', default='.', help='Path to Obsidian vault')

    args = parser.parse_args()

    poster = TwitterPoster(vault_path=args.vault)

    if args.login:
        print("Twitter Login")
        print("=" * 40)
        if poster.login():
            print("\n[OK] Login successful!")
            print("\nNext steps:")
            print("  python twitter_poster.py --post \"Your tweet text\"")
        else:
            print("\n[ERROR] Login failed!")

    elif args.post:
        print("Creating Twitter Post Approval Request")
        print("=" * 40)

        if not poster.is_logged_in():
            print("\n[WARNING] Not logged in to Twitter!")
            print("Run: python twitter_poster.py --login")
            print("\nContinuing with approval request creation...\n")

        approval_file = poster.create_approval_request(args.post)
        if approval_file:
            print(f"\n[OK] Approval request created: {approval_file}")
            print("\nNext steps:")
            print(f"1. Review and move to Approved/Social/: {approval_file}")
            print("2. Run: python twitter_poster.py --process")

    elif args.post_now:
        print("Posting to Twitter (Immediate)")
        print("=" * 40)

        if not poster.is_logged_in():
            print("\n[ERROR] Not logged in!")
            print("Run: python twitter_poster.py --login")
            return

        if poster.create_tweet(args.post_now):
            print("\n[OK] Tweet created successfully!")
        else:
            print("\n[ERROR] Failed to create tweet")

    elif args.thread:
        print("Creating Twitter Thread Approval Request")
        print("=" * 40)

        tweets = [t.strip() for t in args.thread.split('|||')]
        full_text = '\n\n'.join([f"({i+1}/{len(tweets)}) {t}" for i, t in enumerate(tweets)])
        
        approval_file = poster.create_approval_request(full_text, is_thread=True)
        if approval_file:
            print(f"\n[OK] Approval request created: {approval_file}")
            print(f"Thread contains {len(tweets)} tweets")

    elif args.process:
        print("Processing Approved Tweets")
        print("=" * 40)

        if not poster.is_logged_in():
            print("\n[ERROR] Not logged in!")
            print("Run: python twitter_poster.py --login")
            return

        count = poster.process_approved_posts()
        print(f"\n[OK] Posted {count} tweet(s) to Twitter")

    elif args.demo:
        print("Twitter Poster - Demo Mode")
        print("=" * 40)
        print("\nThis is a demo. No actual posts will be made.")
        print("\nCommands:")
        print("  --login              Login to Twitter (saves session)")
        print("  --post \"Text\"        Create tweet approval request")
        print("  --post-now \"Text\"    Post immediately")
        print("  --thread \"T1|||T2\"   Create thread (tweets separated by |||)")
        print("  --process            Process approved posts")
        print("\nExample:")
        print('  python twitter_poster.py --post "Hello Twitter!"')
        print('  python twitter_poster.py --thread "First tweet|||Second tweet|||Third tweet"')

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
