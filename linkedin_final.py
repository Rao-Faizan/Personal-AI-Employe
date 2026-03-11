#!/usr/bin/env python3
"""
LinkedIn Poster - Final Version
Uses correct selector: button.artdeco-button__text
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
        logging.FileHandler('linkedin_final.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('LinkedInFinal')

try:
    from playwright.sync_api import sync_playwright
except ImportError:
    print("Install: pip install playwright && playwright install")
    sys.exit(1)

def post_to_linkedin(text, vault_path="."):
    """Post to LinkedIn with correct button selector."""
    vault = Path(vault_path)
    session_path = vault / ".linkedin_session"
    session_path.mkdir(exist_ok=True)
    
    logger.info("="*60)
    logger.info("LinkedIn Poster - Final Version")
    logger.info("="*60)
    
    with sync_playwright() as p:
        # Launch browser
        logger.info("[1/7] Launching browser...")
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
        
        # Go to LinkedIn feed
        logger.info("[2/7] Opening LinkedIn feed...")
        page.goto("https://www.linkedin.com/feed/", wait_until="domcontentloaded")
        time.sleep(5)
        
        # Check if logged in
        if "login" in page.url.lower():
            logger.info("Not logged in! Please login in the browser...")
            logger.info("(You have 2 minutes)")
            for i in range(24):
                time.sleep(5)
                if "login" not in page.url.lower():
                    logger.info("Login detected!")
                    break
            else:
                logger.error("Login timeout")
                browser.close()
                return False
        
        logger.info("[3/7] Clicking 'Start a post'...")
        try:
            page.click('[aria-label="Start a post"]', timeout=15000)
            time.sleep(4)
            logger.info("Post composer opened!")
        except Exception as e:
            logger.error(f"Could not open composer: {e}")
            browser.close()
            return False
        
        # Type text
        logger.info(f"[4/7] Typing post: {text[:40]}...")
        typed = False
        for attempt in range(5):
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
                    logger.info("Text entered successfully!")
                    typed = True
                    break
            except Exception as e:
                logger.warning(f"Attempt {attempt+1} failed: {e}")
                time.sleep(2)
        
        if not typed:
            logger.error("Could not enter text")
            browser.close()
            return False
        
        time.sleep(3)
        
        # Find and click Post button
        logger.info("[5/7] Finding Post button...")
        try:
            # Use the correct selector from LinkedIn HTML
            post_button = page.locator('button.artdeco-button__text').first
            
            # Verify button text
            button_text = post_button.inner_text(timeout=5000)
            logger.info(f"Button text: '{button_text}'")
            
            if "Post" in button_text:
                logger.info("[6/7] Clicking Post button...")
                post_button.click(timeout=15000)
                logger.info("Post button clicked!")
            else:
                logger.warning(f"Button says '{button_text}', clicking anyway...")
                post_button.click(timeout=15000)
                
        except Exception as e:
            logger.error(f"Could not click Post button: {e}")
            logger.info("Trying keyboard shortcut (Ctrl+Enter)...")
            page.keyboard.press('Control+Enter')
        
        # Wait for submission
        logger.info("[7/7] Waiting for post to submit...")
        time.sleep(10)
        
        # Screenshot
        try:
            page.screenshot(path="linkedin_post_result.png")
            logger.info("Screenshot saved: linkedin_post_result.png")
        except:
            pass
        
        logger.info("="*60)
        logger.info("POST SUBMITTED!")
        logger.info("="*60)
        logger.info("Browser will stay open for 30 seconds...")
        logger.info("Check LinkedIn to verify your post!")
        time.sleep(30)
        
        browser.close()
        logger.info("Done!")
        return True

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='LinkedIn Poster - Final Version')
    parser.add_argument('--text', required=True, help='Post text')
    parser.add_argument('--vault', default='.', help='Vault path')
    args = parser.parse_args()
    
    print("\nLinkedIn Poster - Final Version")
    print("="*60)
    print(f"Post text: {args.text}")
    print("="*60 + "\n")
    
    success = post_to_linkedin(args.text, args.vault)
    
    if success:
        print("\n✓ Post submitted successfully!")
        print("Check LinkedIn to verify!")
    else:
        print("\n✗ Post failed")
    
    sys.exit(0 if success else 1)
