import logging
import time

import httpx

from sources.base import Post

log = logging.getLogger(__name__)

API = "https://api.telegram.org/bot{token}/sendMessage"
MAX_BODY = 600


def send_post(token: str, chat_id: str, post: Post) -> bool:
    body = post.text if len(post.text) <= MAX_BODY else post.text[:MAX_BODY].rstrip() + "…"
    msg = (
        f"🏠 New flat — {post.source_label}\n\n"
        f"{body}\n\n"
        f"🔗 {post.url}"
    )
    return _send(token, chat_id, msg)


def _send(token: str, chat_id: str, text: str, retries: int = 1) -> bool:
    url = API.format(token=token)
    payload = {"chat_id": chat_id, "text": text, "disable_web_page_preview": False}
    for attempt in range(retries + 1):
        try:
            r = httpx.post(url, json=payload, timeout=15.0)
            if r.status_code == 200 and r.json().get("ok"):
                return True
            log.warning("telegram send failed (%s): %s", r.status_code, r.text[:200])
        except Exception as e:
            log.warning("telegram send exception: %s", e)
        if attempt < retries:
            time.sleep(2)
    return False
