#!/usr/bin/env python3
"""
LinkedIn FINAL Poster - Button Ko Click Karega!
No excuses - seedha button click!
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
    print("LINKEDIN FINAL POSTER - BUTTON CLICK PAKKA!")
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
        print("\n[1/5] Opening LinkedIn...")
        page.goto("https://www.linkedin.com/feed/", wait_until="domcontentloaded")
        time.sleep(5)
        
        # Start a post
        print("[2/5] Clicking 'Start a post'...")
        try:
            page.click('[aria-label="Start a post"]', timeout=10000)
            print("      Composer opened!")
        except:
            print("      Manual: Click 'Start a post' button...")
        
        time.sleep(4)
        
        # Type text
        print(f"[3/5] Typing: {text[:40]}...")
        text_area = page.locator('div[contenteditable="true"]').first
        text_area.click()
        time.sleep(2)
        page.keyboard.press('Control+A')
        page.keyboard.press('Delete')
        time.sleep(1)
        
        for char in text:
            page.keyboard.type(char, delay=50)
        print("      Text typed!")
        
        time.sleep(3)
        
        # CLICK POST BUTTON - FINAL ATTEMPT
        print("[4/5] CLICKING POST BUTTON...")
        
        # Try ALL possible selectors
        selectors = [
            'button[aria-label="Post"]',
            'button:has-text("Post")',
            'button.artdeco-button--primary',
            'div[role="dialog"] button:nth-child(2)',
            '.share-box-actions button',
        ]
        
        clicked = False
        for selector in selectors:
            try:
                btn = page.locator(selector).first
                if btn.count() > 0:
                    txt = btn.inner_text(timeout=2000)
                    if "Post" in txt:
                        print(f"      Found with: {selector}")
                        print(f"      Button text: '{txt}'")
                        btn.click()
                        print("      CLICKED!")
                        clicked = True
                        break
            except Exception as e:
                pass
        
        if not clicked:
            print("      Button not found - using JavaScript!")
            page.evaluate("""
                () => {
                    const buttons = document.querySelectorAll('button');
                    for (let btn of buttons) {
                        if (btn.textContent.trim() === 'Post') {
                            btn.click();
                            return true;
                        }
                    }
                    return false;
                }
            """)
            print("      JavaScript click sent!")
        
        # Wait
        print("[5/5] Waiting for submission...")
        time.sleep(10)
        
        # Screenshot
        try:
            page.screenshot(path="linkedin_final.png")
            print("      Screenshot saved: linkedin_final.png")
        except:
            pass
        
        print("\n" + "="*70)
        print("DONE! Browser 30 seconds mein close hoga")
        print("="*70)
        print("\nCheck LinkedIn - post ho gayi honi chahiye!")
        
        time.sleep(30)
        browser.close()
        return True

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--text', default='Final Test Post!')
    args = parser.parse_args()
    
    post_to_linkedin(args.text)
