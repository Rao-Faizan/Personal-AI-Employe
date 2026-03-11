#!/usr/bin/env python3
"""
LinkedIn Post Button Clicker - ONLY clicks Post button
Composer already open hona chahiye, text already typed hona chahiye
"""

import sys
import time
from pathlib import Path

try:
    from playwright.sync_api import sync_playwright
except ImportError:
    print("Install: pip install playwright && playwright install")
    sys.exit(1)

def click_post_button(vault_path="."):
    """Just click the Post button - assumes composer is already open."""
    vault = Path(vault_path)
    session = vault / ".linkedin_session"
    
    print("\n" + "="*70)
    print("LINKEDIN POST BUTTON CLICKER")
    print("="*70)
    print("\nBrowser open karo, composer open karo, text type karo")
    print("Phir yeh script run karo - Post button click karega!\n")
    
    with sync_playwright() as p:
        browser = p.chromium.launch_persistent_context(
            str(session),
            headless=False,
            args=['--no-sandbox']
        )
        
        page = browser.pages[0]
        
        print("Finding Post button in open composer...\n")
        
        # ALL possible Post button selectors
        selectors = [
            'button.share-box-actions__submit-button',
            'div.share-box__footer button.artdeco-button--primary',
            'button[aria-label="Post"]',
            'div.share-creation-state__footer button',
            'button.artdeco-button--primary:has-text("Post")',
        ]
        
        for selector in selectors:
            try:
                btn = page.locator(selector).first
                if btn.count() > 0:
                    txt = btn.inner_text(timeout=2000)
                    print(f"✓ Found with: {selector}")
                    print(f"  Button text: '{txt}'")
                    
                    if "Post" in txt or "Submit" in txt:
                        print("  CLICKING...")
                        btn.click()
                        print("  CLICKED!\n")
                        time.sleep(5)
                        print("="*70)
                        print("POST BUTTON CLICKED!")
                        print("="*70)
                        print("\nCheck LinkedIn - post submit ho rahi hogi!")
                        time.sleep(10)
                        browser.close()
                        return True
            except Exception as e:
                pass
        
        print("✗ Post button not found with any selector")
        print("\nTrying JavaScript fallback...\n")
        
        # JavaScript click
        result = page.evaluate("""
            () => {
                const buttons = document.querySelectorAll('button');
                for (let btn of buttons) {
                    const txt = btn.textContent.trim();
                    if (txt === 'Post' && !btn.disabled) {
                        btn.click();
                        return 'clicked';
                    }
                }
                return 'not_found';
            }
        """)
        
        if result == 'clicked':
            print("✓ JavaScript click successful!")
            print("\nPost submit ho rahi hai!")
            time.sleep(10)
        else:
            print("✗ JavaScript bhi fail")
        
        browser.close()
        return result == 'clicked'

if __name__ == "__main__":
    click_post_button()
