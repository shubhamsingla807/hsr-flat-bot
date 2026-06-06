# HSR Flat-Hunt Bot — Design Spec

**Date:** 2026-06-06
**Owner:** Shubham Singla
**Status:** Approved for implementation

## Problem

Moving to Bangalore. Need a 1BHK/PG/flatmate spot near HSR Layout (Sector 1 office). Manually scrolling Facebook groups, Reddit, and Twitter is slow and high-noise. Want a bot that watches sources every 30 min and DMs me only the posts that match my needs.

## Goal

Receive Telegram DMs for new posts that are:
- For HSR or nearby areas (within ~6–7 km of HSR Sector 1)
- Targeted at male tenants (men/male/boy/bachelor)
- Not broker-posted
- Not female-only

## Non-Goals

- Auto-replying to posts or contacting sellers
- Long-term operation (bot is disposable, killed once flat is found)
- ML/LLM-based relevance ranking (regex is enough for v1)
- Other cities

## Sources

All sources fetched in parallel each 30-min tick.

1. **Facebook groups** — burner FB account, Playwright with saved session cookies. Group URLs provided by user in `config.py`. Scrape top ~20 posts from each group's feed.
2. **Reddit** — JSON endpoints (no API key needed) for: `r/bangalore`, `r/bangaloreflats`, `r/HSR`. Last 25 posts per subreddit.
3. **Twitter/X** — Nitter RSS for queries: `"HSR flatmate"`, `"HSR PG"`, `"HSR 1BHK male"`. No login. (Note: Nitter availability fluctuates — bot logs and skips if all instances are down.)

Each source returns a normalized `Post` object:
```python
@dataclass
class Post:
    source: str         # "fb" | "reddit" | "twitter"
    source_label: str   # e.g. "Bangalore Flatmates", "r/bangaloreflats"
    id: str             # source-native id
    url: str
    text: str           # full post body
    posted_at: datetime
```

## Filter Logic

A post passes if ALL three rules pass:

### Rule 1: Location match
Post text (case-insensitive) contains at least one of:
- `HSR`
- Whitelisted nearby areas (within ~6–7 km of HSR Sector 1):
  `Koramangala`, `BTM`, `Bommanahalli`, `Sarjapur Road`, `Iblur`, `Agara`, `Bellandur`

Excluded as too far (NOT included even if mentioned alone): Whitefield, Marathahalli, Indiranagar, Electronic City, Jayanagar, JP Nagar.

### Rule 2: Gender match
Post text contains (word-boundary regex, case-insensitive) at least one of:
`men`, `male`, `boy`, `boys`, `guys`, `bachelor`, `bachelors`

### Rule 3: Exclusions (any match → drop)
- Female-only signals: `female only`, `girls only`, `women only`, `ladies only`, `for girls`, `for females`, `females only`, `only girls`, `only women`
- Broker signals: `broker`, `brokerage`, `commission`, `agent fee`, `agent fees`

Matching implementation: precompiled regex per pattern, run on `post.text.lower()`.

## Dedup

- `data/seen.json` stores a dict: `{post_hash: iso_timestamp_seen}`
- `post_hash = sha1(f"{source}:{id}")[:12]`
- Pruned to last 7 days at the start of each tick
- A post is sent only if its hash is not in `seen.json`

## First-Run Bootstrap

First tick (when `seen.json` is empty or missing) only DMs posts from the **last 6 hours** to avoid a flood of historical posts. All older posts are added to `seen.json` silently.

## Delivery

Single Telegram bot, single chat (the user's). Message format:

```
🏠 New flat — [source_label]
[post.text, truncated to 600 chars with "…" if longer]

🔗 [post.url]
```

One message per post. Sent sequentially with 1 sec delay to stay well under Telegram's 30 msg/sec limit.

Telegram bot token and chat ID stored in `.env`:
```
TELEGRAM_BOT_TOKEN=...
TELEGRAM_CHAT_ID=...
FB_GROUP_URLS=https://facebook.com/groups/x,https://facebook.com/groups/y
```

## Project Structure

```
hsr-flat-bot/
├── sources/
│   ├── __init__.py
│   ├── base.py          # Post dataclass, BaseSource interface
│   ├── facebook.py      # Playwright, uses data/cookies.json
│   ├── reddit.py        # requests + json
│   └── twitter.py       # Nitter RSS via feedparser
├── filters.py           # match_post(post) -> bool
├── telegram_client.py   # send_post(post)
├── store.py             # load_seen / mark_seen / prune
├── config.py            # all knobs in one place
├── main.py              # orchestrator
├── setup_fb.py          # one-time: launch headed browser, save cookies
├── data/                # gitignored: cookies.json, seen.json
├── .env                 # gitignored
├── .env.example
├── requirements.txt
├── render.yaml          # cron: */30 * * * *
└── README.md
```

## Orchestrator Flow (`main.py`)

```
1. load_seen()
2. prune_seen(>7 days)
3. fetch from all sources in parallel (asyncio.gather or ThreadPoolExecutor)
4. for each post:
   a. if hash in seen → skip
   b. if first_run and posted_at < now-6h → mark_seen, skip
   c. if not match_post(post) → mark_seen, skip
   d. send via telegram, then mark_seen
5. save_seen()
6. exit 0
```

A source error (e.g., FB blocked, Nitter down) logs the error but does NOT crash the whole tick — other sources continue.

## FB Session Bootstrap (`setup_fb.py`)

Runs once locally:
1. Launches headed Playwright Chromium
2. User logs into burner FB account manually
3. Script waits for the user to press Enter, then saves `context.storage_state()` → `data/cookies.json`
4. `cookies.json` is then uploaded to Render as a secret file (or committed if encrypted, TBD at deploy time)

On Render, `facebook.py` loads `cookies.json` to restore session — no login flow at runtime.

## Hosting

Render free tier cron job, schedule `*/30 * * * *`.

- Build: `pip install -r requirements.txt && playwright install chromium`
- Start: `python main.py`
- **Persistent storage:** `seen.json` and `cookies.json` are committed to a **private GitHub repo**. On each tick: `git pull` at start, `git commit && git push` at end. Auth via a fine-grained GitHub PAT stored as a Render env var. Free forever, no DB, no external accounts.

## Tech Choices

- **Python 3.11**
- **Playwright** (FB scraping)
- **httpx** (Reddit JSON, Telegram API)
- **feedparser** (Nitter RSS)
- **python-dotenv** (config)
- No DB (JSON files), no ORM, no FastAPI — this is a cron, not a service.

## Failure Modes & Handling

| Failure | Handling |
|---|---|
| FB account challenged/locked | FB source returns empty + logs warning. Reddit + Twitter continue. User re-runs `setup_fb.py` locally and re-uploads cookies. |
| Nitter instance down | Try 2–3 fallback instances. If all down, skip Twitter for this tick. |
| Reddit rate limit (429) | Backoff + skip subreddit for this tick. |
| Telegram send fails | Retry once. If still fails, log and do NOT mark the post as seen (will retry next tick). |
| `seen.json` corrupt | Treat as empty + trigger first-run mode (6h window). |

## Out of Scope (Future)

- Web dashboard
- Per-source on/off toggles via Telegram
- Saved-search bookmarking
- LLM-based summary of each post
- Price/area extraction
