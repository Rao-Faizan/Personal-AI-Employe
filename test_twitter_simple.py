#!/usr/bin/env python3
"""
Simple Twitter Test - Gold Tier
Quick test for Twitter posting with better error handling
"""

import sys
import time
from pathlib import Path

# Fix Windows console encoding
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, errors='replace')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, errors='replace')

try:
    from playwright.sync_api import sync_playwright
    print("✓ Playwright loaded")
except ImportError as e:
    print(f"✗ Playwright import failed: {e}")
    sys.exit(1)

def test_twitter():
    """Test Twitter with simple approach."""
    
    vault_path = Path(".")
    session_path = vault_path / ".twitter_session"
    session_path.mkdir(exist_ok=True)
    
    print("\n" + "="*60)
    print("Twitter Test - Gold Tier")
    print("="*60)
    
    with sync_playwright() as p:
        print("\n[1/5] Launching browser...")
        browser = p.chromium.launch_persistent_context(
            str(session_path),
            headless=False,
            args=[
                '--disable-blink-features=AutomationControlled',
                '--disable-features=OptimizationHints',
                '--disable-dev-shm-usage',
                '--no-sandbox'
            ],
            ignore_default_args=['--enable-automation']
        )
        
        page = browser.pages[0] if browser.pages else browser.new_page()
        
        print("[2/5] Going to Twitter...")
        try:
            page.goto("https://twitter.com/home", wait_until="domcontentloaded", timeout=90000)
            print("     Twitter page loaded!")
        except Exception as e:
            print(f"     Error loading Twitter: {e}")
            browser.close()
            return False
        
        time.sleep(5)
        
        print("[3/5] Checking login status...")
        current_url = page.url
        print(f"     Current URL: {current_url}")
        
        if "login" in current_url.lower():
            print("\n     ⚠️  Not logged in!")
            print("     Please login in the browser window...")
            print("     (You have 2 minutes)")
            
            # Wait for login
            for i in range(24):  # 2 minutes
                time.sleep(5)
                if "login" not in page.url.lower():
                    print("     ✓ Login detected!")
                    break
            else:
                print("     ✗ Login timeout")
                browser.close()
                return False
        
        print("[4/5] Looking for tweet composer...")
        
        # Find tweet button
        selectors = [
            'div[contenteditable="true"][role="textbox"]',
            '[data-testid="tweetTextarea_0"]',
            '[aria-label="Tweet text"]',
            'div[aria-label="What\'s happening?"]'
        ]
        
        text_area = None
        for selector in selectors:
            try:
                locator = page.locator(selector).first
                if locator.count() > 0:
                    text_area = locator
                    print(f"     Found with: {selector}")
                    break
            except:
                pass
        
        if not text_area:
            print("     ✗ Could not find tweet composer")
            print("     Taking screenshot...")
            try:
                page.screenshot(path="twitter_test_error.png")
                print("     Screenshot saved: twitter_test_error.png")
            except:
                pass
            browser.close()
            return False
        
        print("[5/5] Test tweet likh rahe hain...")
        
        # Click and type
        text_area.click()
        time.sleep(1)
        page.keyboard.press('Control+A')
        page.keyboard.press('Delete')
        time.sleep(1)
        
        test_text = f"AI Employee Gold Tier Test - {time.strftime('%H:%M:%S')}"
        text_area.type(test_text, delay=30)
        print(f"     Tweet text: {test_text}")
        
        time.sleep(3)
        
        # Look for post button
        print("\n[6/6] Looking for Post button...")
        post_selectors = [
            '[data-testid="tweetButton"]',
            '[data-testid="TweetButton"]',
            'div[role="button"]:has-text("Post")',
            'div[role="button"]:has-text("Tweet")'
        ]
        
        post_button = None
        for selector in post_selectors:
            try:
                locator = page.locator(selector).first
                if locator.count() > 0:
                    post_button = locator
                    print(f"     Found with: {selector}")
                    break
            except:
                pass
        
        if post_button:
            print("\n     ✓ Post button found!")
            print("\n" + "="*60)
            print("TEST SUCCESSFUL!")
            print("="*60)
            print("\nTwitter is working correctly.")
            print("Aap manually tweet post kar sakte hain ya approval workflow use kar sakte hain.")
            print("\nBrowser close ho jayega 10 seconds mein...")
            time.sleep(10)
            browser.close()
            return True
        else:
            print("     ✗ Post button nahi mila")
            print("     Browser open rahega for manual testing")
            print("\nManual test ke liye browser open hai.")
            print("Tweet manually post karein aur browser close karein.")
            
            # Wait for manual action
            try:
                for i in range(60):
                    time.sleep(1)
            except:
                pass
            
            browser.close()
            return False

if __name__ == "__main__":
    print("\nTwitter Test Script")
    print("This will test if Twitter posting works on your system\n")
    
    success = test_twitter()
    
    if success:
        print("\n✓ Twitter test PASSED!")
        print("\nAb aap use kar sakte hain:")
        print("  python scripts/twitter_poster.py --login")
        print("  python scripts/twitter_poster.py --post \"Your tweet\"")
    else:
        print("\n✗ Twitter test FAILED")
        print("\nPossible solutions:")
        print("  1. Check internet connection")
        print("  2. Try again in a few minutes")
        print("  3. Check if Twitter/X is accessible in your region")
    
    sys.exit(0 if success else 1)
