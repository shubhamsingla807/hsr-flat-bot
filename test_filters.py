"""Quick sanity test for filter rules. Run: python test_filters.py"""
from datetime import datetime, timezone

from filters import match_post
from sources.base import Post


def p(text: str) -> Post:
    return Post(source="t", source_label="t", id="x", url="u", text=text,
                posted_at=datetime.now(tz=timezone.utc))


CASES = [
    # High-signal explicit-male posts — should pass
    ("Looking for male flatmate in HSR Sector 2, 12k", True, "hsr + explicit male"),
    ("1BHK available in Koramangala for bachelors", True, "koramangala + bachelors"),
    ("PG for boys near BTM Layout, 8k/mo", True, "btm + boys"),
    ("Need male roommate near Sarjapur road, 1BHK", True, "sarjapur + male"),
    ("Flatmate wanted in Bellandur, guys preferred", True, "bellandur + guys"),

    # Gender-agnostic listings — should NOW pass (Option B)
    ("1BHK semi-furnished for rent in HSR Sector 7, 22k", True, "gender-agnostic HSR rental"),
    ("3BHK available in Koramangala, ₹40k, immediate move-in", True, "gender-agnostic koramangala"),
    ("Brand new 2BHK flat for rent in HSR Layout, 25k", True, "gender-agnostic HSR flat"),
    ("Studio for rent in Bellandur near RMZ Ecospace, 14k", True, "gender-agnostic studio"),

    # Female-only — must drop
    ("Female only flat in HSR, 15k", False, "female-only excluded"),
    ("Girls only PG in Koramangala", False, "girls only excluded"),
    ("HSR PG for working women only", False, "working women excluded"),
    ("1BHK in BTM for ladies only", False, "ladies only excluded"),

    # Family/couples-only — must drop (new in Option B)
    ("HSR 2BHK for family only, no bachelors", False, "family only excluded"),
    ("Strictly for family, 3BHK in Koramangala", False, "strictly family excluded"),
    ("Married couples only, BTM Layout flat", False, "couples only excluded"),

    # Broker — must drop
    ("HSR 2BHK for male, broker fee 1 month", False, "broker excluded"),
    ("HSR flat for bachelors, no brokerage", False, "brokerage excluded"),

    # Out-of-area — must drop
    ("Looking for flatmate in Whitefield, male", False, "whitefield not in whitelist"),
    ("Single room available in Indiranagar for boys", False, "indiranagar excluded"),

    # No location — must drop
    ("Looking for male flatmate, 12k budget anywhere", False, "no location mentioned"),
]


def main():
    fails = 0
    for text, expected, label in CASES:
        got = match_post(p(text))
        ok = got == expected
        mark = "PASS" if ok else "FAIL"
        print(f"{mark} {label}: expected={expected} got={got} | {text[:80]}")
        if not ok:
            fails += 1
    print(f"\n{len(CASES) - fails}/{len(CASES)} passed")
    return 0 if fails == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
