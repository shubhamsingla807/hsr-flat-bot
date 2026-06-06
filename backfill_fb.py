"""
One-time deep-scroll of FB groups. DMs matches + marks everything as seen
so the 30-min cron doesn't re-DM the same posts.

Usage:
    python backfill_fb.py [posts_per_group]

Default 80 posts/group. 13 groups × 80 = ~1040 posts, ~10 min runtime.
"""
import logging
import sys
import time

import config
from filters import match_post
from sources import facebook
from sources.base import Post
import store
import telegram_client

logging.basicConfig(level="INFO", format="%(asctime)s %(levelname)s %(name)s: %(message)s")
log = logging.getLogger("backfill")


def main():
    per_group = int(sys.argv[1]) if len(sys.argv) > 1 else 80
    log.info("backfill: scraping ~%d posts per FB group across %d groups",
             per_group, len(config.FB_GROUP_URLS))

    seen = store.load(config.SEEN_PATH)
    log.info("starting with %d already-seen posts", len(seen))

    # Deep scroll: monkey-patch the scroll count and per_group limit.
    posts = _deep_fetch_fb(config.FB_GROUP_URLS, config.COOKIES_PATH, per_group)
    log.info("scraped %d total FB posts", len(posts))

    matches_sent = 0
    new_marked = 0
    for post in posts:
        if post.hash in seen:
            continue
        new_marked += 1
        if match_post(post):
            ok = telegram_client.send_post(config.TELEGRAM_BOT_TOKEN, config.TELEGRAM_CHAT_ID, post)
            if ok:
                matches_sent += 1
                time.sleep(1.0)
        store.mark(seen, post.hash)

    store.save(config.SEEN_PATH, seen)
    log.info("backfill done: scraped=%d new=%d matches_sent=%d total_seen=%d",
             len(posts), new_marked, matches_sent, len(seen))


def _deep_fetch_fb(group_urls, cookies_path, per_group):
    """Like facebook.fetch but with more aggressive scrolling per group."""
    import os
    if not group_urls:
        return []
    if not os.path.exists(cookies_path):
        log.error("fb cookies missing at %s — run refresh_fb_cookies.py first", cookies_path)
        return []

    from playwright.sync_api import sync_playwright
    from datetime import datetime, timezone
    import re

    posts = []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(storage_state=cookies_path)
        page = context.new_page()

        for url in group_urls:
            try:
                log.info("scraping %s", url)
                page.goto(url, wait_until="domcontentloaded", timeout=30000)
                page.wait_for_timeout(4000)

                if "/login" in page.url:
                    log.warning("fb session expired for %s — re-run refresh_fb_cookies.py", url)
                    continue

                # Aggressive scroll: per_group / 4 scrolls (each loads ~3-5 posts)
                scroll_count = max(8, per_group // 4)
                for _ in range(scroll_count):
                    page.mouse.wheel(0, 5000)
                    page.wait_for_timeout(1200)

                articles = page.query_selector_all('div[role="article"]')[:per_group]
                group_label = _group_label(url)

                for h in articles:
                    try:
                        text = (h.inner_text() or "").strip()
                        if len(text) < 30:
                            continue
                        link_el = h.query_selector('a[href*="/groups/"][href*="/posts/"], a[href*="/permalink/"]')
                        permalink = link_el.get_attribute("href") if link_el else None
                        if permalink and permalink.startswith("/"):
                            permalink = f"https://www.facebook.com{permalink}"
                        post_id = _extract_post_id(permalink) or f"{group_label}:{hash(text) & 0xffffffff:x}"

                        posts.append(Post(
                            source="fb",
                            source_label=f"FB: {group_label}",
                            id=post_id,
                            url=permalink or url,
                            text=text[:2000],
                            posted_at=datetime.now(tz=timezone.utc),
                        ))
                    except Exception as e:
                        log.debug("article skipped: %s", e)
                log.info("  → got %d articles from this group", len([p for p in posts if f"FB: {group_label}" in p.source_label]))
            except Exception as e:
                log.warning("group %s failed: %s", url, e)

        browser.close()
    return posts


def _group_label(url):
    import re
    m = re.search(r"/groups/([^/?]+)", url)
    return m.group(1) if m else url


def _extract_post_id(url):
    if not url:
        return None
    import re
    m = re.search(r"/posts/(\d+)|/permalink/(\d+)", url)
    return (m.group(1) or m.group(2)) if m else None


if __name__ == "__main__":
    main()
