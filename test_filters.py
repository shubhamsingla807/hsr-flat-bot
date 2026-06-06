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

    # Gender-agnostic listings under rent cap — should pass
    ("Studio for rent in Bellandur near RMZ Ecospace, 14k", True, "gender-agnostic studio 14k"),
    ("1BHK in HSR for rent, ₹15,000", True, "gender-agnostic HSR 15k"),
    ("Single room in Koramangala, 12k", True, "gender-agnostic koramangala 12k"),
    # Gender-agnostic listings over rent cap — should drop (rent filter)
    ("1BHK semi-furnished for rent in HSR Sector 7, 22k", False, "22k over cap"),
    ("3BHK available in Koramangala, ₹40k, immediate move-in", False, "40k over cap"),
    ("Brand new 2BHK flat for rent in HSR Layout, 25k", False, "25k over cap"),

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

    # Rent cap — under 16k passes
    ("HSR PG for boys, 12k/month", True, "12k passes"),
    ("1BHK in BTM, rent 15000", True, "15000 passes"),
    ("Studio in Bellandur, ₹14,000", True, "14k passes"),
    ("HSR room for male, 15.5k", True, "15.5k passes"),
    ("Koramangala flat, Rs. 16,000", True, "16k passes (boundary)"),

    # Rent cap — over 16k drops
    ("HSR 2BHK for bachelors, 25k", False, "25k dropped"),
    ("BTM 3BHK, rent ₹35,000 per month", False, "35k dropped"),
    ("Bellandur 1BHK 20000/-", False, "20k dropped"),
    ("Sarjapur 2BHK, 1.5L deposit, rent 22k", False, "22k rent dropped despite L deposit"),
    ("Studio in Koramangala, 17k", False, "17k dropped"),

    # Range — should use minimum
    ("HSR 1BHK & 2BHK, 12-18k", True, "range 12-18k uses 12k min, passes"),
    ("Bellandur 2-3BHK, 22-30k", False, "range 22-30k uses 22k min, drops"),

    # No rent mentioned — should still pass (don't lose legit posts)
    ("Need a flatmate in HSR, DM for details", True, "no rent passes"),

    # Numbers that look like rent but aren't (sector, sq ft) — should not break
    ("HSR Sector 7 1BHK, 850 sqft, 13k", True, "13k correctly identified, sector not"),
    ("HSR Layout 27th main, ₹12,000", True, "12k correctly identified, main road not"),
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
