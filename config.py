import os
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
TELEGRAM_CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]

FB_GROUP_URLS = [u.strip() for u in os.environ.get("FB_GROUP_URLS", "").split(",") if u.strip()]

SUBREDDITS = ["bangalore", "bangaloreflats", "HSR", "IndianFlatmates", "IndianRoommates", "BangaloreHousing"]

# Cross-sub keyword searches via Reddit RSS — catches HSR posts in any subreddit
REDDIT_SEARCHES = [
    "hsr flatmate",
    "hsr male",
    "hsr bachelor",
    "koramangala flatmate male",
    "btm flatmate male",
    "sarjapur flatmate male",
    "bellandur flatmate male",
]

DATA_DIR = "data"
COOKIES_PATH = f"{DATA_DIR}/cookies.json"
SEEN_PATH = f"{DATA_DIR}/seen.json"

SEEN_TTL_DAYS = 7
FIRST_RUN_WINDOW_HOURS = 6
MAX_POST_AGE_DAYS = 6

LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO")
