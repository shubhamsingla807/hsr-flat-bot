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

GENDER_PATTERNS = [
    r"\bmen\b",
    r"\bmale\b",
    r"\bboy\b",
    r"\bboys\b",
    r"\bguys\b",
    r"\bbachelor\b",
    r"\bbachelors\b",
]

EXCLUSION_PATTERNS = [
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
    r"\bbroker\b",
    r"brokerage",
    r"commission",
    r"agent fee",
    r"agent fees",
]

_loc_re = re.compile("|".join(LOCATION_PATTERNS), re.IGNORECASE)
_gender_re = re.compile("|".join(GENDER_PATTERNS), re.IGNORECASE)
_excl_re = re.compile("|".join(EXCLUSION_PATTERNS), re.IGNORECASE)


def match_post(post: Post) -> bool:
    text = post.text
    if _excl_re.search(text):
        return False
    if not _loc_re.search(text):
        return False
    if not _gender_re.search(text):
        return False
    return True
