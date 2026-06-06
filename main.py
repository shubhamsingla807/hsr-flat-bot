import logging
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone, timedelta
from typing import List

import config
from filters import match_post
from sources import facebook, reddit
from sources.base import Post
import store
import telegram_client

logging.basicConfig(
    level=config.LOG_LEVEL,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
log = logging.getLogger("hsr-bot")


def fetch_all() -> List[Post]:
    jobs = {
        "reddit": lambda: reddit.fetch(config.SUBREDDITS, searches=config.REDDIT_SEARCHES),
        "fb": lambda: facebook.fetch(config.FB_GROUP_URLS, config.COOKIES_PATH),
    }
    posts: List[Post] = []
    with ThreadPoolExecutor(max_workers=len(jobs)) as pool:
        futures = {pool.submit(fn): name for name, fn in jobs.items()}
        for fut in as_completed(futures):
            name = futures[fut]
            try:
                got = fut.result()
                log.info("source %s returned %d posts", name, len(got))
                posts.extend(got)
            except Exception as e:
                log.warning("source %s crashed: %s", name, e)
    return posts


def main():
    start = time.time()
    seen = store.prune(store.load(config.SEEN_PATH), config.SEEN_TTL_DAYS)
    is_first_run = len(seen) == 0
    if is_first_run:
        log.info("first run: only DMing posts from last %dh", config.FIRST_RUN_WINDOW_HOURS)
    first_run_cutoff = datetime.now(tz=timezone.utc) - timedelta(hours=config.FIRST_RUN_WINDOW_HOURS)
    age_cutoff = datetime.now(tz=timezone.utc) - timedelta(days=config.MAX_POST_AGE_DAYS)

    posts = fetch_all()
    log.info("fetched %d total posts", len(posts))

    sent = 0
    for post in posts:
        if post.hash in seen:
            continue
        if post.posted_at < age_cutoff:
            store.mark(seen, post.hash)
            continue
        if is_first_run and post.posted_at < first_run_cutoff:
            store.mark(seen, post.hash)
            continue
        if not match_post(post):
            store.mark(seen, post.hash)
            continue

        ok = telegram_client.send_post(config.TELEGRAM_BOT_TOKEN, config.TELEGRAM_CHAT_ID, post)
        if ok:
            store.mark(seen, post.hash)
            sent += 1
            time.sleep(1.0)
        else:
            log.warning("telegram failed; leaving post unsent for retry next tick: %s", post.url)

    store.save(config.SEEN_PATH, seen)
    log.info("done in %.1fs — sent %d", time.time() - start, sent)


if __name__ == "__main__":
    main()
