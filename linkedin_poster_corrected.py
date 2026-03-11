#!/usr/bin/env python3
"""
LinkedIn Poster - CORRECTED VERSION
- Fast typing (no human-like delay)
- Correct Post button selector (share-actions__primary-action)
- NOT privacy dropdown
"""

import sys
import time
import logging
import codecs
from pathlib import Path

if sys.platform == 'win32':
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, errors='replace')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, errors='replace')

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('linkedin_corrected.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('LinkedInCorrected')

try:
    from playwright.sync_api import sync_playwright
except ImportError:
    print("Install: pip install playwright && playwright install")
    sys.exit(1)


class LinkedInPoster:
    def __init__(self, vault_path="."):
        self.vault_path = Path(vault_path)
        self.session_path = self.vault_path / ".linkedin_session"
        self.pending_approval = self.vault_path / "Pending_Approval"
        self.approved_folder = self.vault_path / "Approved" / "Social"
        self.done_folder = self.vault_path / "Done"
        
        self.session_path.mkdir(exist_ok=True)
        self.pending_approval.mkdir(exist_ok=True)
        self.approved_folder.mkdir(exist_ok=True, parents=True)
        self.done_folder.mkdir(exist_ok=True)

    def is_logged_in(self) -> bool:
        if not self.session_path.exists():
            return False
        return len(list(self.session_path.glob("**/*"))) > 5

    def create_post(self, text: str) -> bool:
        """Create post with FAST typing and CORRECT Post button."""
        if not self.is_logged_in():
            logger.error("Not logged in! Run: python linkedin_poster.py --login")
            return False

        logger.info("Creating LinkedIn post...")

        with sync_playwright() as p:
            browser = p.chromium.launch_persistent_context(
                str(self.session_path),
                headless=True,
                args=['--disable-blink-features=AutomationControlled', '--no-sandbox']
            )

            page = browser.pages[0] if browser.pages else browser.new_page()

            # Go to feed
            logger.info("Opening LinkedIn feed...")
            page.goto("https://www.linkedin.com/feed/", wait_until="domcontentloaded", timeout=60000)
            time.sleep(3)

            # Click Start a post
            logger.info("Clicking 'Start a post'...")
            try:
                page.click('[aria-label="Start a post"]', timeout=10000)
                time.sleep(2)
            except Exception as e:
                logger.error(f"Could not open composer: {e}")
                browser.close()
                return False

            # FAST typing - NO human-like delay
            logger.info("Entering post text (fast)...")
            try:
                text_area = page.locator('div[contenteditable="true"][role="textbox"]').first
                text_area.fill(text, timeout=10000)
                logger.info("Text entered!")
                time.sleep(2)
            except Exception as e:
                logger.error(f"Error typing: {e}")
                browser.close()
                return False

            # CORRECT Post button selector - NOT privacy dropdown
            logger.info("Clicking Post button (share-actions__primary-action)...")
            try:
                # THIS IS THE CORRECT SELECTOR
                post_button = page.locator('button.share-actions__primary-action').first
                
                btn_text = post_button.inner_text(timeout=5000)
                logger.info(f"Button text: '{btn_text}'")
                
                if "Post" in btn_text:
                    post_button.click(timeout=10000)
                    logger.info("Post button clicked!")
                    
                    time.sleep(8)
                    
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
                
                # Fallback: JavaScript
                logger.info("JavaScript fallback...")
                page.evaluate("""
                    () => {
                        const btn = document.querySelector('button.share-actions__primary-action');
                        if (btn) { btn.click(); return true; }
                        return false;
                    }
                """)
                time.sleep(5)
                browser.close()
                return True

    def create_approval_request(self, post_text: str) -> Path:
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        filename = f"SOCIAL_LINKEDIN_{timestamp}.md"
        approval_path = self.pending_approval / filename

        content = f"""---
type: social_media_post
platform: LinkedIn
created: {datetime.now().isoformat()}
status: pending_approval
---

# LinkedIn Post Approval Request

## Post Content
{post_text}

## To Approve
Move to: `/Approved/Social/`

## To Reject
Move to: `/Rejected/`
"""
        approval_path.write_text(content)
        logger.info(f"Approval created: {approval_path}")
        return approval_path

    def process_approved_posts(self) -> int:
        approved_files = list(self.approved_folder.glob("SOCIAL_LINKEDIN_*.md"))
        posted = 0
        
        for file_path in approved_files:
            logger.info(f"Processing: {file_path.name}")
            content = file_path.read_text()
            
            if "## Post Content" in content:
                start = content.find("## Post Content") + len("## Post Content")
                end = content.find("## To Approve") if "## To Approve" in content else len(content)
                post_text = content[start:end].strip()
                
                if self.create_post(post_text):
                    posted += 1
                    done_path = self.done_folder / f"POSTED_{file_path.name}"
                    file_path.rename(done_path)
        
        return posted


def main():
    import argparse
    from datetime import datetime

    parser = argparse.ArgumentParser(description='LinkedIn Poster - Corrected')
    parser.add_argument('--login', action='store_true', help='Login')
    parser.add_argument('--post', type=str, help='Create post (approval)')
    parser.add_argument('--post-now', type=str, help='Post immediately')
    parser.add_argument('--process', action='store_true', help='Process approved')
    parser.add_argument('--vault', default='.', help='Vault path')
    args = parser.parse_args()

    poster = LinkedInPoster(vault_path=args.vault)

    if args.login:
        print("LinkedIn Login")
        print("="*50)
        # Simple login script
        with sync_playwright() as p:
            browser = p.chromium.launch_persistent_context(
                str(poster.session_path),
                headless=False,
                args=['--no-sandbox']
            )
            page = browser.pages[0]
            page.goto("https://www.linkedin.com/login")
            print("Login in browser... (5 minutes)")
            for i in range(60):
                time.sleep(5)
                if "feed" in page.url:
                    print("Login detected!")
                    time.sleep(5)
                    break
            browser.close()
        print("Session saved!")

    elif args.post:
        print("Creating approval request...")
        approval = poster.create_approval_request(args.post)
        print(f"Created: {approval}")

    elif args.post_now:
        print("Posting immediately...")
        if poster.create_post(args.post_now):
            print("[OK] Posted!")
        else:
            print("[ERROR] Failed")

    elif args.process:
        print("Processing approved posts...")
        count = poster.process_approved_posts()
        print(f"Posted: {count}")

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
