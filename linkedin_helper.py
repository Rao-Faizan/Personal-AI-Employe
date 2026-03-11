#!/usr/bin/env python3
"""
LinkedIn Helper - Semi-Automatic Poster
Browser open karega, aap manually click karein, script type karegi
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
        logging.FileHandler('linkedin_helper.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('LinkedInHelper')

try:
    from playwright.sync_api import sync_playwright
except ImportError:
    print("Install: pip install playwright && playwright install")
    sys.exit(1)

def helper_post(text, vault_path="."):
    """Helper post to LinkedIn."""
    vault = Path(vault_path)
    session_path = vault / ".linkedin_session"
    session_path.mkdir(exist_ok=True, parents=True)
    
    print("\n" + "="*70)
    print("LINKEDIN HELPER - SEMI-AUTOMATIC POSTER")
    print("="*70)
    print(f"\nPost text: {text}\n")
    
    with sync_playwright() as p:
        browser = p.chromium.launch_persistent_context(
            str(session_path),
            headless=False,
            args=['--disable-blink-features=AutomationControlled', '--no-sandbox'],
            ignore_default_args=['--enable-automation']
        )
        
        page = browser.pages[0] if browser.pages else browser.new_page()
        
        # Go to LinkedIn
        logger.info("Opening LinkedIn...")
        page.goto("https://www.linkedin.com/feed/", wait_until="domcontentloaded")
        time.sleep(5)
        
        print("\n" + "="*70)
        print("STEP 1: Click 'Start a post' button MANUALLY")
        print("="*70)
        print("Browser mein LinkedIn khula hai.")
        print("'Start a post' button par click karein.")
        print("Jab composer khul jaye, Enter press karein ya 10 seconds wait karein...")
        
        # Wait for user to click
        for i in range(30):
            time.sleep(1)
            try:
                text_area = page.locator('div[contenteditable="true"][role="textbox"]').first
                if text_area.count() > 0:
                    logger.info("Composer detected!")
                    break
            except:
                pass
        else:
            print("\nTimeout - composer nahi khula")
            browser.close()
            return False
        
        time.sleep(2)
        
        # Type the text
        print("\n" + "="*70)
        print("STEP 2: Typing post text...")
        print("="*70)
        
        try:
            text_area = page.locator('div[contenteditable="true"][role="textbox"]').first
            text_area.click()
            time.sleep(1)
            page.keyboard.press('Control+A')
            page.keyboard.press('Delete')
            time.sleep(1)
            
            for char in text:
                page.keyboard.type(char, delay=30)
            
            logger.info("Text typed successfully!")
            print("Text type ho gaya!")
            
        except Exception as e:
            logger.error(f"Error typing: {e}")
            print(f"Error: {e}")
            browser.close()
            return False
        
        time.sleep(3)
        
        print("\n" + "="*70)
        print("STEP 3: Click 'Post' button MANUALLY")
        print("="*70)
        print("Browser mein neeche right corner mein blue 'Post' button hai.")
        print("Us par click karein.")
        print("Post submit hone ke baad browser automatically close ho jayega.")
        print("\n(You have 60 seconds to click Post)")
        
        # Wait for user to click Post
        for i in range(60):
            time.sleep(1)
            try:
                # Check if composer is closed (post submitted)
                text_area = page.locator('div[contenteditable="true"][role="textbox"]').first
                if text_area.count() == 0:
                    logger.info("Post submitted detected!")
                    break
            except:
                pass
        else:
            logger.warning("60 seconds ho gaye")
        
        # Wait a bit more and take screenshot
        time.sleep(5)
        
        try:
            page.screenshot(path="linkedin_post_result.png")
            logger.info("Screenshot saved")
        except:
            pass
        
        browser.close()
        logger.info("Done!")
        
        print("\n" + "="*70)
        print("DONE!")
        print("="*70)
        print("\nCheck your LinkedIn profile to verify the post.")
        print("Screenshot saved: linkedin_post_result.png")
        
        return True

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--text', default='Auto posted from AI Employee!', help='Post text')
    parser.add_argument('--vault', default='.', help='Vault path')
    args = parser.parse_args()
    
    success = helper_post(args.text, args.vault)
    sys.exit(0 if success else 1)
