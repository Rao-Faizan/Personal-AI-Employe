#!/usr/bin/env python3
"""Test Playwright import"""

try:
    from playwright.sync_api import sync_playwright
    print("✓ Playwright import successful!")
    
    # Test browser launch
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        print("✓ Browser launched successfully!")
        browser.close()
        print("✓ Test PASSED - Playwright is working!")
        
except ImportError as e:
    print(f"✗ Import Error: {e}")
    print("\nSolution: Install Python 3.12 from:")
    print("https://www.python.org/ftp/python/3.12.8/python-3.12.8-amd64.exe")
except Exception as e:
    print(f"✗ Error: {e}")
