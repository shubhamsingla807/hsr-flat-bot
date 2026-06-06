import json
import logging
import os
from datetime import datetime, timezone, timedelta
from typing import Dict

log = logging.getLogger(__name__)


def load(path: str) -> Dict[str, str]:
    if not os.path.exists(path):
        return {}
    try:
        with open(path) as f:
            data = json.load(f)
        if not isinstance(data, dict):
            log.warning("seen file %s not a dict, resetting", path)
            return {}
        return data
    except Exception as e:
        log.warning("seen file %s corrupt (%s), resetting", path, e)
        return {}


def save(path: str, seen: Dict[str, str]) -> None:
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w") as f:
        json.dump(seen, f, indent=0, sort_keys=True)


def prune(seen: Dict[str, str], ttl_days: int) -> Dict[str, str]:
    cutoff = datetime.now(tz=timezone.utc) - timedelta(days=ttl_days)
    kept = {}
    for h, ts in seen.items():
        try:
            if datetime.fromisoformat(ts) >= cutoff:
                kept[h] = ts
        except Exception:
            continue
    return kept


def mark(seen: Dict[str, str], hash_: str) -> None:
    seen[hash_] = datetime.now(tz=timezone.utc).isoformat()
