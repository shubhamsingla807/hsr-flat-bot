"""
Run locally when FB cookies expire (GH Actions logs show "fb session expired").

Usage:
    python refresh_fb_cookies.py

After it saves data/cookies.json, push the new cookies as a GitHub secret:
    gh secret set FB_COOKIES_JSON --body "$(cat data/cookies.json)" --repo shubhamsingla807/hsr-flat-bot
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
        print(">>> Wait until you see your FB home feed, then come back and press Enter.")
        input()
        context.storage_state(path=COOKIES_PATH)
        print(f"\n✅ Saved cookies to {COOKIES_PATH}")
        print("\nNow push the new cookies to GitHub Actions:")
        print(f'  gh secret set FB_COOKIES_JSON --body "$(cat {COOKIES_PATH})" --repo shubhamsingla807/hsr-flat-bot')
        browser.close()


if __name__ == "__main__":
    main()
