import logging
import os
import re
from datetime import datetime, timezone
from typing import List

from .base import Post

log = logging.getLogger(__name__)


def fetch(group_urls: List[str], cookies_path: str, per_group: int = 20) -> List[Post]:
    if not group_urls:
        return []
    if not os.path.exists(cookies_path):
        log.warning("fb cookies missing at %s — skipping FB. Run setup_fb.py.", cookies_path)
        return []

    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        log.warning("playwright not installed — skipping FB. Run: pip install playwright && playwright install chromium")
        return []

    posts: List[Post] = []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(storage_state=cookies_path)
        page = context.new_page()

        for url in group_urls:
            try:
                posts.extend(_scrape_group(page, url, per_group))
            except Exception as e:
                log.warning("fb group %s failed: %s", url, e)

        browser.close()
    return posts


def _scrape_group(page, url: str, per_group: int) -> List[Post]:
    page.goto(url, wait_until="domcontentloaded", timeout=30000)
    page.wait_for_timeout(4000)

    # Detect login wall — if FB redirected us to login, our cookies are dead.
    if "/login" in page.url:
        log.warning("fb session expired (redirected to login) for %s", url)
        return []

    # Scroll a few times to load posts.
    for _ in range(3):
        page.mouse.wheel(0, 4000)
        page.wait_for_timeout(1500)

    # Grab post containers. FB DOM changes frequently — use a permissive selector.
    article_handles = page.query_selector_all('div[role="article"]')[:per_group]
    group_label = _group_label_from_url(url)
    results: List[Post] = []

    for i, h in enumerate(article_handles):
        try:
            text = (h.inner_text() or "").strip()
            if len(text) < 30:
                continue
            link_el = h.query_selector('a[href*="/groups/"][href*="/posts/"], a[href*="/permalink/"]')
            permalink = link_el.get_attribute("href") if link_el else None
            if permalink and permalink.startswith("/"):
                permalink = f"https://www.facebook.com{permalink}"
            post_id = _extract_post_id(permalink) or f"{group_label}:{hash(text) & 0xffffffff:x}"

            results.append(Post(
                source="fb",
                source_label=f"FB: {group_label}",
                id=post_id,
                url=permalink or url,
                text=text[:2000],
                posted_at=datetime.now(tz=timezone.utc),
            ))
        except Exception as e:
            log.debug("fb article %d skipped: %s", i, e)
    return results


def _group_label_from_url(url: str) -> str:
    m = re.search(r"/groups/([^/?]+)", url)
    return m.group(1) if m else url


def _extract_post_id(url: str | None) -> str | None:
    if not url:
        return None
    m = re.search(r"/posts/(\d+)|/permalink/(\d+)", url)
    if m:
        return m.group(1) or m.group(2)
    return None
