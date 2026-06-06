import logging
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from typing import List

import feedparser

from .base import Post

log = logging.getLogger(__name__)


def fetch(subreddits: List[str], per_sub: int = 25) -> List[Post]:
    posts: List[Post] = []
    for sub in subreddits:
        url = f"https://www.reddit.com/r/{sub}/new.rss?limit={per_sub}"
        try:
            feed = feedparser.parse(url)
            if feed.bozo and not feed.entries:
                log.warning("reddit r/%s: feed parse error %s", sub, feed.bozo_exception)
                continue
            for e in feed.entries:
                try:
                    posted_at = parsedate_to_datetime(e.updated) if hasattr(e, "updated") else datetime.now(tz=timezone.utc)
                except Exception:
                    posted_at = datetime.now(tz=timezone.utc)
                # e.id looks like "https://www.reddit.com/r/bangalore/t3_1ty7wf2"
                post_id = e.id.rsplit("/", 1)[-1]
                # RSS content is HTML; title is plain. Combine for matching.
                summary = getattr(e, "summary", "")
                text = f"{e.title}\n\n{_strip_html(summary)}".strip()
                posts.append(Post(
                    source="reddit",
                    source_label=f"r/{sub}",
                    id=post_id,
                    url=e.link,
                    text=text,
                    posted_at=posted_at,
                ))
        except Exception as e:
            log.warning("reddit r/%s failed: %s", sub, e)
    return posts


def _strip_html(s: str) -> str:
    import re
    return re.sub(r"<[^>]+>", " ", s).strip()
