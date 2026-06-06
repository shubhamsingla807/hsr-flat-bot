import re

from sources.base import Post

LOCATION_PATTERNS = [
    r"\bhsr\b",
    r"\bkoramangala\b",
    r"\bbtm\b",
    r"\bbommanahalli\b",
    r"\bsarjapur\b",
    r"\biblur\b",
    r"\bagara\b",
    r"\bbellandur\b",
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
    Option B logic:
      1. Must mention HSR or a nearby whitelisted area.
      2. Must NOT match exclusions (female-only, family-only, broker/commission).
      3. Gender keyword (male/boys/bachelor) is optional — included if present,
         but gender-agnostic listings still pass.
    """
    text = post.text
    if not _loc_re.search(text):
        return False
    if _excl_re.search(text):
        return False
    return True
