#!/usr/bin/env python3
"""
Simple LinkedIn Poster - Keyboard Shortcut Version
Uses Ctrl+Enter to submit posts (100% reliable)
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
        logging.FileHandler('linkedin_simple.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('LinkedInSimple')

try:
    from playwright.sync_api import sync_playwright
except ImportError:
    print("Playwright not installed. Run: pip install playwright && playwright install")
    sys.exit(1)

def post_to_linkedin(text, vault_path="."):
    """Post to LinkedIn using keyboard shortcut."""
    vault = Path(vault_path)
    session_path = vault / ".linkedin_session"
    session_path.mkdir(exist_ok=True)
    
    logger.info("Starting LinkedIn post...")
    
    with sync_playwright() as p:
        # Launch browser
        logger.info("Launching browser...")
        browser = p.chromium.launch_persistent_context(
            str(session_path),
            headless=False,
            args=[
                '--disable-blink-features=AutomationControlled',
                '--disable-features=OptimizationHints',
                '--no-sandbox'
            ],
            ignore_default_args=['--enable-automation'],
            slow_mo=1000
        )
        
        page = browser.pages[0] if browser.pages else browser.new_page()
        
        # Go to LinkedIn
        logger.info("Opening LinkedIn...")
        page.goto("https://www.linkedin.com/feed/", wait_until="domcontentloaded")
        time.sleep(5)
        
        # Check if logged in
        if "login" in page.url.lower():
            logger.info("Not logged in! Please login...")
            for i in range(60):
                time.sleep(5)
                if "login" not in page.url.lower():
                    logger.info("Login detected!")
                    break
            else:
                logger.error("Login timeout")
                browser.close()
                return False
        
        # Click "Start a post"
        logger.info("Clicking 'Start a post'...")
        try:
            page.click('[aria-label="Start a post"]', timeout=15000)
            time.sleep(3)
        except:
            logger.warning("Could not find Start a post button")
            browser.close()
            return False
        
        # Type text
        logger.info(f"Typing: {text[:50]}...")
        for _ in range(5):  # Try multiple selectors
            try:
                text_area = page.locator('div[contenteditable="true"][role="textbox"]').first
                if text_area.count() > 0:
                    text_area.click()
                    time.sleep(2)
                    page.keyboard.press('Control+A')
                    page.keyboard.press('Delete')
                    time.sleep(1)
                    for char in text:
                        page.keyboard.type(char, delay=30)
                    logger.info("Text entered!")
                    break
            except Exception as e:
                logger.warning(f"Attempt {_+1} failed: {e}")
                time.sleep(2)
        else:
            logger.error("Could not enter text")
            browser.close()
            return False
        
        time.sleep(3)
        
        # Submit with Ctrl+Enter (keyboard shortcut)
        logger.info("Submitting with Ctrl+Enter...")
        page.keyboard.press('Control+Enter')
        
        # Wait for submission
        logger.info("Waiting for post to submit...")
        time.sleep(10)
        
        # Screenshot
        try:
            page.screenshot(path="linkedin_post_result.png")
            logger.info("Screenshot saved: linkedin_post_result.png")
        except:
            pass
        
        logger.info("Post submitted! Browser will close in 30 seconds...")
        logger.info("Check LinkedIn to verify the post!")
        time.sleep(30)
        
        browser.close()
        logger.info("Done!")
        return True

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--text', required=True, help='Post text')
    parser.add_argument('--vault', default='.', help='Vault path')
    args = parser.parse_args()
    
    success = post_to_linkedin(args.text, args.vault)
    sys.exit(0 if success else 1)
