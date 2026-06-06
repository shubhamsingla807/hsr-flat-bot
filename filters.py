import re
from typing import Optional

from sources.base import Post

MAX_RENT = 16000

LOCATION_PATTERNS = [
    r"\bhsr\b",
    r"\bkoramangala\b",
    r"\bbtm\b",
    r"\bbommanahalli\b",
    r"\bsarjapur\b",
    r"\biblur\b",
    r"\bagara\b",
    r"\bbellandur\b",
    r"\bkudlu\b",
    r"\bkasavanahalli\b",
    r"\bharalur\b",
    r"\bmadiwala\b",
    r"\bjakkasandra\b",
]

# Posts that explicitly say "male/boys" are always allowed (high signal).
GENDER_INCLUDE_PATTERNS = [
    r"\bmen\b",
    r"\bmale\b",
    r"\bboy\b",
    r"\bboys\b",
    r"\bguys\b",
    r"\bbachelor\b",
    r"\bbachelors\b",
]

# Drop posts that signal "not for you": female/girls-only, family-only, couples-only.
EXCLUSION_PATTERNS = [
    # Female-only
    r"female only",
    r"females only",
    r"only females",
    r"girls only",
    r"only girls",
    r"women only",
    r"only women",
    r"ladies only",
    r"for girls",
    r"for females",
    r"\bfor girl\b",
    r"\bfor lady\b",
    r"\bfor ladies\b",
    r"\bworking women\b",
    r"\bworking woman\b",
    # Family/couples only
    r"family only",
    r"only family",
    r"families only",
    r"only families",
    r"couples only",
    r"only couples",
    r"married couples? only",
    r"for family only",
    r"strictly for family",
    r"strictly family",
    # Brokers / fee-takers
    r"\bbroker\b",
    r"brokerage",
    r"commission",
    r"agent fee",
    r"agent fees",
]

_loc_re = re.compile("|".join(LOCATION_PATTERNS), re.IGNORECASE)
_gender_re = re.compile("|".join(GENDER_INCLUDE_PATTERNS), re.IGNORECASE)
_excl_re = re.compile("|".join(EXCLUSION_PATTERNS), re.IGNORECASE)


def match_post(post: Post) -> bool:
    """
    1. Must mention HSR or a nearby whitelisted area.
    2. Must NOT match exclusions (female/family/couples-only, broker/commission).
    3. If a rent figure is present, min rent must be <= MAX_RENT.
       If no rent figure parseable, post still passes (avoid losing legit listings).
    """
    text = post.text
    if not _loc_re.search(text):
        return False
    if _excl_re.search(text):
        return False
    rent = extract_min_rent(text)
    if rent is not None and rent > MAX_RENT:
        return False
    return True


# Range like "12-18k" — capture min (first number)
_RENT_RANGE_K = re.compile(r"\b(\d{1,3}(?:\.\d+)?)\s*[-–]\s*\d{1,3}(?:\.\d+)?\s*k\b(?!m|g)", re.IGNORECASE)

# Matches: ₹15000, Rs.15000, Rs 15,000, 15000/-, 15k, 15K, 1.5L, 1.5 lakh
_RENT_PATTERNS = [
    # ₹15000 or ₹ 15,000
    (re.compile(r"₹\s*([\d,]+)(?!\s*(?:sq|sft|sec|main|cross|th|nd|rd|st))", re.IGNORECASE), 1),
    # Rs 15000, Rs. 15,000, INR 15000
    (re.compile(r"\b(?:rs\.?|inr)\s*([\d,]+)(?!\s*(?:sq|sft))", re.IGNORECASE), 1),
    # 15k, 15K (must be word boundary, not "15kg" or "15km")
    (re.compile(r"\b(\d{1,3}(?:\.\d+)?)\s*k\b(?!m|g)", re.IGNORECASE), 1000),
    # 1.5L, 2 lakh
    (re.compile(r"\b(\d+(?:\.\d+)?)\s*(?:l|lakh|lac)\b", re.IGNORECASE), 100000),
    # "rent 15000" / "rent: 15,000" / "rent is 15000"
    (re.compile(r"\brent\s*(?:is|:)?\s*([\d,]+)", re.IGNORECASE), 1),
    # "15000/month" or "15,000 per month"
    (re.compile(r"\b([\d,]+)\s*(?:/|per)\s*(?:month|mo)\b", re.IGNORECASE), 1),
    # "15000/-"
    (re.compile(r"\b([\d,]+)\s*/-"), 1),
]


def extract_min_rent(text: str) -> Optional[int]:
    """Find the smallest plausible rent figure in the post (in rupees).
    Returns None if no rent-looking figure found."""
    candidates: list[int] = []
    # Range "12-18k" → use min (12k)
    for m in _RENT_RANGE_K.finditer(text):
        try:
            val = int(float(m.group(1)) * 1000)
            if 3000 <= val <= 200000:
                candidates.append(val)
        except ValueError:
            continue
    # Standard patterns
    for pattern, multiplier in _RENT_PATTERNS:
        for m in pattern.finditer(text):
            raw = m.group(1).replace(",", "")
            try:
                val = float(raw) * multiplier
            except ValueError:
                continue
            ival = int(val)
            # Plausible rent in Bangalore: ₹3k to ₹2L
            if 3000 <= ival <= 200000:
                candidates.append(ival)
    return min(candidates) if candidates else None
