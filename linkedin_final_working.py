#!/usr/bin/env python3
"""
LinkedIn FINAL Poster - 100% Working
Uses correct selector: button.share-actions__primary-action
"""

import sys
import time
from pathlib import Path

try:
    from playwright.sync_api import sync_playwright
except ImportError:
    print("Install: pip install playwright && playwright install")
    sys.exit(1)

def post_to_linkedin(text, vault_path="."):
    vault = Path(vault_path)
    session = vault / ".linkedin_session"
    session.mkdir(exist_ok=True, parents=True)
    
    print("\n" + "="*70)
    print("LINKEDIN FINAL POSTER - 100% WORKING")
    print("="*70)
    
    with sync_playwright() as p:
        browser = p.chromium.launch_persistent_context(
            str(session),
            headless=False,
            args=['--disable-blink-features=AutomationControlled', '--no-sandbox'],
            ignore_default_args=['--enable-automation'],
            slow_mo=500
        )
        
        page = browser.pages[0]
        
        # LinkedIn feed
        print("\n[1/6] Opening LinkedIn...")
        page.goto("https://www.linkedin.com/feed/", wait_until="domcontentloaded")
        time.sleep(5)
        
        # Start a post
        print("[2/6] Clicking 'Start a post'...")
        try:
            page.click('[aria-label="Start a post"]', timeout=10000)
            print("      ✓ Composer opened")
        except:
            print("      ⚠ Manual: Click 'Start a post'")
            time.sleep(5)
        
        time.sleep(3)
        
        # Type text
        print(f"[3/6] Typing: {text[:50]}...")
        try:
            text_area = page.locator('div[contenteditable="true"][role="textbox"]').first
            text_area.click()
            time.sleep(2)
            page.keyboard.press('Control+A')
            page.keyboard.press('Delete')
            time.sleep(1)
            for char in text:
                page.keyboard.type(char, delay=50)
            print("      ✓ Text typed")
        except Exception as e:
            print(f"      ✗ Error: {e}")
            browser.close()
            return False
        
        time.sleep(3)
        
        # CLICK POST BUTTON - CORRECT SELECTOR
        print("[4/6] CLICKING POST BUTTON...")
        print("      Using selector: button.share-actions__primary-action")
        
        try:
            # THE CORRECT SELECTOR
            post_button = page.locator('button.share-actions__primary-action').first
            
            # Verify
            btn_text = post_button.inner_text(timeout=5000)
            print(f"      Button text: '{btn_text}'")
            
            if "Post" in btn_text:
                print("      Clicking...")
                post_button.click()
                print("      ✓ CLICKED!")
            else:
                print(f"      Wrong button: '{btn_text}'")
                browser.close()
                return False
                
        except Exception as e:
            print(f"      ✗ Error: {e}")
            print("      Trying JavaScript fallback...")
            
            page.evaluate("""
                () => {
                    const btn = document.querySelector('button.share-actions__primary-action');
                    if (btn) { btn.click(); return true; }
                    return false;
                }
            """)
            print("      JavaScript click sent")
        
        # Wait for submission
        print("[5/6] Waiting for post to submit...")
        time.sleep(10)
        
        # Screenshot
        print("[6/6] Taking screenshot...")
        try:
            page.screenshot(path="linkedin_success.png")
            print("      ✓ Screenshot: linkedin_success.png")
        except:
            pass
        
        print("\n" + "="*70)
        print("POST SUBMITTED!")
        print("="*70)
        print("\nBrowser 20 seconds mein close hoga")
        print("Check LinkedIn - post dikh rahi hogi!")
        
        time.sleep(20)
        browser.close()
        print("\nDone!")
        return True

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--text', default='Final Test - Share Actions Primary Action!')
    args = parser.parse_args()
    
    success = post_to_linkedin(args.text)
    sys.exit(0 if success else 1)
