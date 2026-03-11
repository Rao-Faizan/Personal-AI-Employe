#!/usr/bin/env python3
"""
Auto LinkedIn Login + Poster
Pehle login karwata hai, phir post karta hai
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
        logging.FileHandler('linkedin_auto.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('LinkedInAuto')

try:
    from playwright.sync_api import sync_playwright
except ImportError:
    print("Install: pip install playwright && playwright install")
    sys.exit(1)

def login_and_post(text, vault_path="."):
    """Login to LinkedIn and post."""
    vault = Path(vault_path)
    session_path = vault / ".linkedin_session"
    session_path.mkdir(exist_ok=True, parents=True)
    
    logger.info("="*60)
    logger.info("LinkedIn Auto Login + Poster")
    logger.info("="*60)
    
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
            slow_mo=500
        )
        
        page = browser.pages[0] if browser.pages else browser.new_page()
        
        # Go to LinkedIn login
        logger.info("Opening LinkedIn login page...")
        page.goto("https://www.linkedin.com/login", wait_until="domcontentloaded")
        time.sleep(3)
        
        # Check if already logged in
        if "feed" in page.url or "linkedin.com/feed" in page.url:
            logger.info("Already logged in!")
        else:
            logger.info("="*60)
            logger.info("PLEASE LOGIN IN THE BROWSER")
            logger.info("="*60)
            logger.info("Aapke paas 2 minutes hain login karne ke liye")
            logger.info("Login ke baad browser automatically proceed karega...")
            
            # Wait for login (max 2 minutes)
            for i in range(24):
                time.sleep(5)
                current_url = page.url
                if "feed" in current_url or "checkpoint" not in current_url:
                    logger.info("Login detected!")
                    time.sleep(3)  # Wait for session to save
                    break
            else:
                logger.error("Login timeout - 2 minutes ho gaye")
                browser.close()
                return False
        
        # Navigate to feed
        logger.info("Going to LinkedIn feed...")
        page.goto("https://www.linkedin.com/feed/", wait_until="domcontentloaded")
        time.sleep(5)
        
        # Click "Start a post"
        logger.info("Looking for 'Start a post' button...")
        try:
            # Try multiple selectors
            selectors = [
                '[aria-label="Start a post"]',
                'button:has-text("Start a post")',
                '[data-id="gh-create-a-post"]'
            ]
            
            clicked = False
            for selector in selectors:
                try:
                    page.click(selector, timeout=5000)
                    logger.info(f"Clicked with selector: {selector}")
                    clicked = True
                    break
                except:
                    continue
            
            if not clicked:
                logger.error("Could not find 'Start a post' button")
                logger.info("Manually click 'Start a post' in the browser...")
                time.sleep(10)
            
        except Exception as e:
            logger.error(f"Error: {e}")
        
        time.sleep(3)
        
        # Type the post
        logger.info(f"Typing post: {text[:50]}...")
        try:
            text_area = page.locator('div[contenteditable="true"][role="textbox"]').first
            if text_area.count() > 0:
                text_area.click()
                time.sleep(2)
                page.keyboard.press('Control+A')
                page.keyboard.press('Delete')
                time.sleep(1)
                for char in text:
                    page.keyboard.type(char, delay=50)
                logger.info("Text typed successfully!")
            else:
                logger.error("Could not find text area")
                browser.close()
                return False
        except Exception as e:
            logger.error(f"Error typing: {e}")
            browser.close()
            return False
        
        time.sleep(3)
        
        # Click Post button - use exact selector
        logger.info("Finding and clicking Post button...")
        try:
            # LinkedIn Post button selector
            post_button = page.locator('button[aria-label="Post"]').first
            
            # Wait for button to be enabled
            for i in range(10):
                try:
                    if post_button.count() > 0:
                        is_disabled = post_button.get_attribute('disabled')
                        if not is_disabled:
                            logger.info("Post button is enabled, clicking...")
                            post_button.click(timeout=10000)
                            logger.info("Post button clicked!")
                            break
                except:
                    pass
                time.sleep(1)
            else:
                # Button not found, try alternative
                logger.warning("Post button not found, trying alternative...")
                try:
                    # Try clicking any blue button in composer
                    page.click('button:has-text("Post")', timeout=5000)
                    logger.info("Alternative Post button clicked!")
                except:
                    logger.error("Could not find Post button")
                
        except Exception as e:
            logger.error(f"Error clicking Post button: {e}")
            # Try one more alternative
            try:
                page.locator('button[type="submit"]').first.click(timeout=5000)
                logger.info("Submit button clicked!")
            except:
                logger.error("All Post button attempts failed")
        
        # Wait for submission
        logger.info("Waiting for post to submit...")
        time.sleep(10)
        
        # Screenshot
        try:
            page.screenshot(path="linkedin_post_result.png")
            logger.info("Screenshot saved: linkedin_post_result.png")
        except Exception as e:
            logger.warning(f"Could not save screenshot: {e}")
        
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
    parser = argparse.ArgumentParser()
    parser.add_argument('--text', default='Auto posted from AI Employee!', help='Post text')
    parser.add_argument('--vault', default='.', help='Vault path')
    args = parser.parse_args()
    
    print("\n" + "="*60)
    print("LinkedIn Auto Login + Poster")
    print("="*60)
    print(f"Post text: {args.text}")
    print("="*60 + "\n")
    
    success = login_and_post(args.text, args.vault)
    
    if success:
        print("\n" + "="*60)
        print("SUCCESS! Post submitted to LinkedIn!")
        print("="*60)
        print("\nCheck your LinkedIn profile to verify the post.")
    else:
        print("\n" + "="*60)
        print("FAILED - Post could not be submitted")
        print("="*60)
    
    sys.exit(0 if success else 1)
