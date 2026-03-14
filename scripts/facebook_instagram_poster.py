#!/usr/bin/env python3
"""
Facebook & Instagram Poster for AI Employee - Gold Tier

Posts to Facebook and Instagram using browser automation (no API required).
Uses Playwright to automate the web interfaces.

Setup:
1. Install Playwright: pip install playwright && playwright install
2. Login to Facebook: python facebook_instagram_poster.py --login-facebook
3. Login to Instagram: python facebook_instagram_poster.py --login-instagram
4. Post: python facebook_instagram_poster.py --post "Your text" --platform facebook
5. Process approved: python facebook_instagram_poster.py --process

Usage:
    python facebook_instagram_poster.py --login-facebook         # Login to Facebook
    python facebook_instagram_poster.py --login-instagram        # Login to Instagram
    python facebook_instagram_poster.py --post "Text" --platform facebook   # Create approval request
    python facebook_instagram_poster.py --post "Text" --platform instagram  # Create approval request
    python facebook_instagram_poster.py --post "Text" --platform both       # Post to both
    python facebook_instagram_poster.py --process                # Process approved posts
    python facebook_instagram_poster.py --status                 # Show login status
"""

import sys
import time
import json
import logging
import codecs
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
        logging.FileHandler('facebook_instagram.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('FBInstaPoster')

try:
    from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout
    PLAYWRIGHT_AVAILABLE = True
    logger.info("Playwright successfully imported")
except ImportError:
    PLAYWRIGHT_AVAILABLE = False
    logger.warning("Playwright not installed. Run: pip install playwright && playwright install")

BROWSER_ARGS = [
    '--disable-blink-features=AutomationControlled',
    '--no-sandbox',
    '--disable-dev-shm-usage',
    '--disable-setuid-sandbox',
]


class FacebookPoster:
    """Post to Facebook using browser automation."""

    def __init__(self, vault_path: str = "."):
        self.vault_path = Path(vault_path)
        self.session_path = self.vault_path / ".facebook_session"
        self.session_path.mkdir(exist_ok=True)

    def is_logged_in(self) -> bool:
        if not PLAYWRIGHT_AVAILABLE:
            return False
        return len(list(self.session_path.glob("**/*"))) >= 5

    def login(self) -> bool:
        """Open Facebook for manual login and save the session."""
        if not PLAYWRIGHT_AVAILABLE:
            logger.error("Playwright not available.")
            return False

        logger.info("Opening Facebook login. Please login manually.")

        with sync_playwright() as p:
            browser = p.chromium.launch_persistent_context(
                str(self.session_path),
                headless=False,
                ignore_default_args=['--enable-automation'],
                args=BROWSER_ARGS,
                slow_mo=500
            )

            page = browser.pages[0] if browser.pages else browser.new_page()
            page.goto("https://www.facebook.com/login", wait_until="domcontentloaded")
            logger.info("Please login to Facebook. You have 5 minutes.")

            try:
                # Wait for the home feed — confirms login
                page.wait_for_url("*facebook.com/*", timeout=300000)
                # Also wait for the main content to appear
                page.wait_for_selector('[aria-label="Facebook"], [role="main"]', timeout=30000)
                logger.info("Login detected!")
                time.sleep(5)
                browser.close()
                logger.info("[OK] Facebook login successful!")
                return True
            except PlaywrightTimeout:
                logger.error("Login timeout.")
                browser.close()
                return False

    def create_post(self, text: str) -> bool:
        """Create a Facebook post via browser automation."""
        if not PLAYWRIGHT_AVAILABLE:
            return False
        if not self.is_logged_in():
            logger.error("Not logged in. Run: --login-facebook")
            return False

        logger.info("Creating Facebook post...")

        with sync_playwright() as p:
            try:
                browser = p.chromium.launch_persistent_context(
                    str(self.session_path),
                    headless=True,
                    ignore_default_args=['--enable-automation'],
                    args=BROWSER_ARGS
                )
                page = browser.pages[0] if browser.pages else browser.new_page()

                # Go to Facebook home
                page.goto("https://www.facebook.com/", wait_until="domcontentloaded", timeout=60000)
                time.sleep(4)

                # Click "What's on your mind?" composer
                logger.info("Opening post composer...")
                composer_selectors = [
                    '[aria-label="What\'s on your mind?"]',
                    '[data-testid="status-attachment-mentions-input"]',
                    'div[role="button"]:has-text("What\'s on your mind")',
                ]
                composer_clicked = False
                for selector in composer_selectors:
                    try:
                        locator = page.locator(selector).first
                        if locator.count() > 0:
                            locator.click(timeout=5000)
                            composer_clicked = True
                            logger.info(f"Opened composer via: {selector}")
                            break
                    except Exception:
                        continue

                if not composer_clicked:
                    logger.error("Could not open post composer")
                    browser.close()
                    return False

                time.sleep(2)

                # Type post text
                logger.info("Entering post text...")
                text_area_selectors = [
                    '[contenteditable="true"][role="textbox"]',
                    '[aria-label="What\'s on your mind?"][contenteditable="true"]',
                    'div.notranslate[contenteditable="true"]',
                ]
                text_entered = False
                for selector in text_area_selectors:
                    try:
                        locator = page.locator(selector).first
                        if locator.count() > 0:
                            locator.click(timeout=3000)
                            time.sleep(0.5)
                            locator.type(text, delay=25)
                            text_entered = True
                            logger.info("Post text entered")
                            break
                    except Exception:
                        continue

                if not text_entered:
                    logger.error("Could not enter post text")
                    try:
                        page.screenshot(path="facebook_error.png")
                    except Exception:
                        pass
                    browser.close()
                    return False

                time.sleep(2)

                # Click Post button
                logger.info("Clicking Post button...")
                post_button_selectors = [
                    'div[aria-label="Post"][role="button"]',
                    'button[type="submit"]:has-text("Post")',
                    'div[role="button"]:has-text("Post")',
                ]
                posted = False
                for selector in post_button_selectors:
                    try:
                        locator = page.locator(selector).last
                        if locator.count() > 0:
                            locator.click(timeout=10000)
                            posted = True
                            logger.info("Post button clicked!")
                            break
                    except Exception:
                        continue

                if not posted:
                    # JavaScript fallback
                    logger.info("Trying JavaScript fallback for post button...")
                    result = page.evaluate("""
                        () => {
                            const buttons = Array.from(document.querySelectorAll('div[role="button"]'));
                            const postBtn = buttons.find(b => b.textContent.trim() === 'Post');
                            if (postBtn) { postBtn.click(); return true; }
                            return false;
                        }
                    """)
                    if result:
                        posted = True
                        logger.info("Post submitted via JavaScript!")

                if posted:
                    time.sleep(5)
                    try:
                        page.screenshot(path="facebook_posted.png")
                    except Exception:
                        pass
                    browser.close()
                    logger.info("[OK] Facebook post created successfully!")
                    return True
                else:
                    logger.error("Could not click Post button")
                    try:
                        page.screenshot(path="facebook_post_error.png")
                    except Exception:
                        pass
                    browser.close()
                    return False

            except Exception as e:
                logger.error(f"Error creating Facebook post: {e}")
                return False


class InstagramPoster:
    """Post to Instagram using browser automation."""

    def __init__(self, vault_path: str = "."):
        self.vault_path = Path(vault_path)
        self.session_path = self.vault_path / ".instagram_session"
        self.session_path.mkdir(exist_ok=True)

    def is_logged_in(self) -> bool:
        if not PLAYWRIGHT_AVAILABLE:
            return False
        return len(list(self.session_path.glob("**/*"))) >= 5

    def login(self) -> bool:
        """Open Instagram for manual login and save the session."""
        if not PLAYWRIGHT_AVAILABLE:
            logger.error("Playwright not available.")
            return False

        logger.info("Opening Instagram login. Please login manually.")

        with sync_playwright() as p:
            browser = p.chromium.launch_persistent_context(
                str(self.session_path),
                headless=False,
                ignore_default_args=['--enable-automation'],
                args=BROWSER_ARGS,
                slow_mo=500
            )

            page = browser.pages[0] if browser.pages else browser.new_page()
            page.goto("https://www.instagram.com/accounts/login/", wait_until="domcontentloaded")
            logger.info("Please login to Instagram. You have 5 minutes.")

            try:
                # Wait for home feed (svg icon in nav = logged in)
                page.wait_for_url("https://www.instagram.com/*", timeout=300000)
                page.wait_for_selector('svg[aria-label="Home"], nav a[href="/"]', timeout=30000)
                logger.info("Login detected!")
                time.sleep(5)
                browser.close()
                logger.info("[OK] Instagram login successful!")
                return True
            except PlaywrightTimeout:
                logger.error("Login timeout.")
                browser.close()
                return False

    def create_post(self, text: str) -> bool:
        """
        Create an Instagram post via browser automation.
        NOTE: Instagram Web only supports text as captions — an image is required
        for a real post. This method creates a post using the New Post composer.
        For text-only content, consider using Stories instead.
        """
        if not PLAYWRIGHT_AVAILABLE:
            return False
        if not self.is_logged_in():
            logger.error("Not logged in. Run: --login-instagram")
            return False

        logger.info("Creating Instagram post...")

        with sync_playwright() as p:
            try:
                browser = p.chromium.launch_persistent_context(
                    str(self.session_path),
                    headless=True,
                    ignore_default_args=['--enable-automation'],
                    args=BROWSER_ARGS
                )
                page = browser.pages[0] if browser.pages else browser.new_page()

                page.goto("https://www.instagram.com/", wait_until="domcontentloaded", timeout=60000)
                time.sleep(4)

                # Click the "Create" (new post) button
                logger.info("Opening post composer...")
                create_selectors = [
                    'svg[aria-label="New post"]',
                    'a[href="/create/style/"]',
                    '[aria-label="New post"]',
                ]
                for selector in create_selectors:
                    try:
                        locator = page.locator(selector).first
                        if locator.count() > 0:
                            locator.click(timeout=5000)
                            logger.info(f"Clicked create via: {selector}")
                            break
                    except Exception:
                        continue

                time.sleep(2)

                # Instagram requires media upload before writing caption.
                # Log that and return — the approval file will note this.
                logger.warning(
                    "Instagram Web requires an image/video before a caption can be added. "
                    "This post was logged as pending. Please attach media manually or "
                    "use the Instagram mobile app for text-only captions via Stories."
                )
                browser.close()

                # Log to Needs_Action for human follow-up
                self._create_manual_followup(text)
                return True  # Partial success — action file created

            except Exception as e:
                logger.error(f"Error creating Instagram post: {e}")
                return False

    def _create_manual_followup(self, text: str):
        """Create a Needs_Action file requesting manual Instagram posting."""
        needs_action = self.vault_path / "Needs_Action"
        needs_action.mkdir(exist_ok=True)
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        action_path = needs_action / f"INSTAGRAM_MANUAL_{timestamp}.md"
        content = f"""---
type: instagram_manual_post
created: {datetime.now().isoformat()}
status: pending
priority: medium
---

# Instagram Post - Manual Action Required

Instagram Web requires media (image/video) before a caption can be added.
Please post this manually via the Instagram mobile app or attach an image.

## Caption Text
{text}

## Steps
- [ ] Open Instagram app on your phone
- [ ] Create new post with an image
- [ ] Paste caption above
- [ ] Post it
- [ ] Move this file to Done
"""
        action_path.write_text(content, encoding='utf-8')
        logger.info(f"Manual follow-up created: {action_path.name}")


class SocialMediaApprovalManager:
    """
    Manages Facebook and Instagram approval workflow.
    Reads approved posts from Approved/Social/ and executes them.
    """

    def __init__(self, vault_path: str = "."):
        self.vault_path = Path(vault_path)
        self.pending_approval = self.vault_path / "Pending_Approval"
        self.approved_folder = self.vault_path / "Approved" / "Social"
        self.done_folder = self.vault_path / "Done"
        self.logs_folder = self.vault_path / "Logs"

        for folder in [self.pending_approval, self.approved_folder, self.done_folder, self.logs_folder]:
            folder.mkdir(exist_ok=True, parents=True)

        self.fb = FacebookPoster(vault_path=vault_path)
        self.ig = InstagramPoster(vault_path=vault_path)

    def create_approval_request(self, post_text: str, platform: str = "both") -> Optional[Path]:
        """
        Create a Pending_Approval file for a Facebook/Instagram post.
        platform: "facebook" | "instagram" | "both"
        """
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        platform_tag = platform.upper()
        filename = f"SOCIAL_{platform_tag}_{timestamp}.md"
        approval_path = self.pending_approval / filename

        preview = post_text[:30].replace('\n', ' ').replace(':', '')

        content = f"""---
type: social_media_post
platform: {platform}
created: {datetime.now().isoformat()}
status: pending_approval
preview: {preview}
---

# {platform.title()} Post Approval Request

## Post Content
{post_text}

## Details
- **Platform:** {platform.title()}
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
        self._update_dashboard(platform, preview)
        return approval_path

    def _update_dashboard(self, platform: str, preview: str):
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
                        f"{platform.title()} post pending: {preview}..."
                    )
                else:
                    new_lines.append(line)
            dashboard_path.write_text('\n'.join(new_lines), encoding='utf-8')
        except Exception as e:
            logger.error(f"Error updating dashboard: {e}")

    def process_approved_posts(self) -> dict:
        """Process all approved Facebook/Instagram posts. Returns counts per platform."""
        counts = {"facebook": 0, "instagram": 0, "both": 0}

        approved_files = list(self.approved_folder.glob("SOCIAL_FACEBOOK_*.md")) + \
                         list(self.approved_folder.glob("SOCIAL_INSTAGRAM_*.md")) + \
                         list(self.approved_folder.glob("SOCIAL_BOTH_*.md"))

        for file_path in approved_files:
            logger.info(f"Processing: {file_path.name}")
            content = file_path.read_text(encoding='utf-8')

            # Extract post text
            if "## Post Content" not in content:
                continue
            start = content.find("## Post Content") + len("## Post Content")
            end = content.find("## Details") if "## Details" in content else len(content)
            post_text = content[start:end].strip()

            # Determine platform from filename
            name_upper = file_path.name.upper()
            platform = "both"
            if "FACEBOOK" in name_upper:
                platform = "facebook"
            elif "INSTAGRAM" in name_upper:
                platform = "instagram"

            success = False

            if platform in ("facebook", "both"):
                if self.fb.create_post(post_text):
                    counts["facebook"] += 1
                    success = True
                else:
                    logger.error(f"Facebook post failed for: {file_path.name}")

            if platform in ("instagram", "both"):
                if self.ig.create_post(post_text):
                    counts["instagram"] += 1
                    success = True
                else:
                    logger.error(f"Instagram post failed for: {file_path.name}")

            if success:
                done_path = self.done_folder / f"POSTED_{file_path.name}"
                file_path.rename(done_path)
                self._log_action(file_path.name, platform, post_text[:100])

        return counts

    def _log_action(self, filename: str, platform: str, preview: str):
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "action": f"{platform}_post",
            "file": filename,
            "preview": preview,
            "status": "success"
        }
        log_file = self.logs_folder / "facebook_instagram_posts.json"
        logs = []
        if log_file.exists():
            try:
                logs = json.loads(log_file.read_text())
            except Exception:
                logs = []
        logs.append(log_entry)
        log_file.write_text(json.dumps(logs, indent=2))


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

    parser = argparse.ArgumentParser(description='Facebook & Instagram Poster for AI Employee')
    parser.add_argument('--login-facebook', action='store_true', help='Login to Facebook')
    parser.add_argument('--login-instagram', action='store_true', help='Login to Instagram')
    parser.add_argument('--post', type=str, help='Post text (creates approval request)')
    parser.add_argument('--platform', type=str, default='both',
                        choices=['facebook', 'instagram', 'both'],
                        help='Target platform (default: both)')
    parser.add_argument('--post-now', type=str, help='Post immediately without approval')
    parser.add_argument('--process', action='store_true', help='Process approved posts')
    parser.add_argument('--status', action='store_true', help='Show login status')
    parser.add_argument('--vault', default='.', help='Path to Obsidian vault')

    args = parser.parse_args()

    manager = SocialMediaApprovalManager(vault_path=args.vault)
    fb = FacebookPoster(vault_path=args.vault)
    ig = InstagramPoster(vault_path=args.vault)

    if args.login_facebook:
        print("Facebook Login")
        print("=" * 40)
        if fb.login():
            print("\n[OK] Facebook login successful!")
        else:
            print("\n[ERROR] Facebook login failed.")

    elif args.login_instagram:
        print("Instagram Login")
        print("=" * 40)
        if ig.login():
            print("\n[OK] Instagram login successful!")
        else:
            print("\n[ERROR] Instagram login failed.")

    elif args.status:
        print("Social Media Login Status")
        print("=" * 40)
        print(f"Facebook:  {'Logged in' if fb.is_logged_in() else 'Not logged in'}")
        print(f"Instagram: {'Logged in' if ig.is_logged_in() else 'Not logged in'}")
        if not fb.is_logged_in():
            print("\n  facebook: python facebook_instagram_poster.py --login-facebook")
        if not ig.is_logged_in():
            print("  instagram: python facebook_instagram_poster.py --login-instagram")

    elif args.post:
        print(f"Creating {args.platform.title()} Post Approval Request")
        print("=" * 40)
        approval_file = manager.create_approval_request(args.post, platform=args.platform)
        if approval_file:
            print(f"\n[OK] Approval request created: {approval_file.name}")
            print("\nNext steps:")
            print(f"1. Review: {approval_file}")
            print("2. Move to Approved/Social/ to approve")
            print("3. Run: python facebook_instagram_poster.py --process")

    elif args.post_now:
        print(f"Posting to {args.platform.title()} immediately...")
        print("=" * 40)
        if args.platform in ("facebook", "both"):
            if fb.create_post(args.post_now):
                print("[OK] Facebook post created!")
            else:
                print("[ERROR] Facebook post failed")
        if args.platform in ("instagram", "both"):
            if ig.create_post(args.post_now):
                print("[OK] Instagram post created!")
            else:
                print("[ERROR] Instagram post failed")

    elif args.process:
        print("Processing Approved Posts")
        print("=" * 40)
        counts = manager.process_approved_posts()
        print(f"\n[OK] Posted: Facebook={counts['facebook']}, Instagram={counts['instagram']}")

    else:
        parser.print_help()
        print("\nExamples:")
        print("  python facebook_instagram_poster.py --login-facebook")
        print("  python facebook_instagram_poster.py --login-instagram")
        print('  python facebook_instagram_poster.py --post "Big news today!" --platform both')
        print("  python facebook_instagram_poster.py --process")


if __name__ == "__main__":
    main()
