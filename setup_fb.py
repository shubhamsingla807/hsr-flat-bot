"""
One-time: launch a visible browser, log into the burner FB account, then save cookies.

Usage:
    python setup_fb.py
"""
import os
from playwright.sync_api import sync_playwright

from config import COOKIES_PATH, DATA_DIR


def main():
    os.makedirs(DATA_DIR, exist_ok=True)
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()
        page.goto("https://www.facebook.com/login")
        print("\n>>> Log in with the burner account in the browser window.")
        print(">>> After you see your FB home feed, come back here and press Enter.")
        input()
        context.storage_state(path=COOKIES_PATH)
        print(f"Saved cookies to {COOKIES_PATH}")
        browser.close()


if __name__ == "__main__":
    main()
