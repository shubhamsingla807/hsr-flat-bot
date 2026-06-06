import logging
import re
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from typing import List, Optional
from urllib.parse import quote

import feedparser

from .base import Post

log = logging.getLogger(__name__)


def fetch(subreddits: List[str], per_sub: int = 25, searches: Optional[List[str]] = None) -> List[Post]:
    posts: List[Post] = []
    for sub in subreddits:
        url = f"https://www.reddit.com/r/{sub}/new.rss?limit={per_sub}"
        posts.extend(_parse_feed(url, label=f"r/{sub}", sub=sub))
    for query in searches or []:
        url = f"https://www.reddit.com/search.rss?q={quote(query)}&sort=new&restrict_sr=&limit=25"
        posts.extend(_parse_feed(url, label=f"reddit: {query}", sub=None))
    return posts


def _parse_feed(url: str, label: str, sub: Optional[str]) -> List[Post]:
    out: List[Post] = []
    try:
        feed = feedparser.parse(url)
        if feed.bozo and not feed.entries:
            log.warning("reddit %s: feed parse error %s", label, feed.bozo_exception)
            return out
        for e in feed.entries:
            try:
                posted_at = parsedate_to_datetime(e.updated) if hasattr(e, "updated") else datetime.now(tz=timezone.utc)
            except Exception:
                posted_at = datetime.now(tz=timezone.utc)
            post_id = e.id.rsplit("/", 1)[-1]
            summary = getattr(e, "summary", "")
            text = f"{e.title}\n\n{_strip_html(summary)}".strip()
            out.append(Post(
                source="reddit",
                source_label=label,
                id=post_id,
                url=e.link,
                text=text,
                posted_at=posted_at,
            ))
    except Exception as exc:
        log.warning("reddit %s failed: %s", label, exc)
    return out


def _strip_html(s: str) -> str:
    return re.sub(r"<[^>]+>", " ", s).strip()
