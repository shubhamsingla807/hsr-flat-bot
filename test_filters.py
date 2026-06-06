"""Quick sanity test for filter rules. Run: python test_filters.py"""
from datetime import datetime, timezone

from filters import match_post
from sources.base import Post


def p(text: str) -> Post:
    return Post(source="t", source_label="t", id="x", url="u", text=text,
                posted_at=datetime.now(tz=timezone.utc))


CASES = [
    ("Looking for male flatmate in HSR Sector 2, 12k", True, "hsr + male"),
    ("1BHK available in Koramangala for bachelors", True, "koramangala + bachelors"),
    ("PG for boys near BTM Layout, 8k/mo", True, "btm + boys"),
    ("Female only flat in HSR, 15k", False, "female-only excluded"),
    ("HSR 2BHK for male, broker fee 1 month", False, "broker excluded"),
    ("Looking for flatmate in Whitefield, male", False, "whitefield not in whitelist"),
    ("Hi everyone, anyone selling iPhone in HSR?", False, "hsr but no gender keyword"),
    ("Single room available in Indiranagar for boys", False, "indiranagar excluded"),
    ("Need male roommate near Sarjapur road, 1BHK", True, "sarjapur + male"),
    ("Girls only PG in Koramangala", False, "girls only excluded"),
    ("HSR flat for bachelors, no brokerage", False, "brokerage excluded"),
    ("Flatmate wanted in Bellandur, guys preferred", True, "bellandur + guys"),
]


def main():
    fails = 0
    for text, expected, label in CASES:
        got = match_post(p(text))
        ok = got == expected
        mark = "✓" if ok else "✗"
        print(f"{mark} {label}: expected={expected} got={got} | {text}")
        if not ok:
            fails += 1
    print(f"\n{len(CASES) - fails}/{len(CASES)} passed")
    return 0 if fails == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
