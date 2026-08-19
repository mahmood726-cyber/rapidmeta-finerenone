#!/usr/bin/env python3
"""SWEEP THE CORPUS FOR MOJIBAKE -- UTF-8 bytes that were once read as cp1252 and re-saved.

HOW THIS WAS FOUND, AND THE FALSE ALARM THAT FOUND IT. A tombstone repair compared the working
tree against `git show HEAD:` and reported one object mismatching on a single field:

    HEAD : 'AUC0-âˆž) for Bebtelovimab [Arm 23]'
    WORK : 'AUC0-∞) for Bebtelovimab [Arm 23]'

**THAT DIFFERENCE WAS NOT REAL.** The comparison used `subprocess.run(..., text=True)` with no
`encoding=`, so on Windows `git show` was decoded with the locale codec (cp1252). `∞` is the
UTF-8 bytes E2 88 9E; read as cp1252 they are `â`, `ˆ`, `ž`. **The reading harness produced the
corruption and then reported it as a finding about the repository.** Re-run with
`encoding='utf-8'`, all 240 committed objects scan clean and all 19 compared files match
exactly.

  A TOOL THAT DECODES ITS INPUT WRONGLY WILL REPORT THE DAMAGE IT CAUSED AS DAMAGE IT FOUND.
  This nearly produced a registry entry titled "the committed object carries mojibake", and the
  step before that it nearly produced a `git checkout` justified by the false belief that the
  worktree held the good copy.

BUT THE SWEEP IT PROVOKED FOUND SOMETHING REAL, in a different place. Seven DELIVERED HTML pages
carry genuinely double-encoded characters -- verified at byte level, not through any decoder:

    b'Voclosporin \xc3\xa2\xe2\x82\xac\xe2\x80\x9d AURORA-1'

Those bytes are the UTF-8 encoding of `â€”`, which is itself cp1252's misreading of the UTF-8
em dash. The same file contains 67 CORRECT em dashes, so this is not a whole-file encoding
fault -- it is a handful of strings that took a cp1252 round trip at generation time and were
then served to readers.

WHAT MOJIBAKE LOOKS LIKE. Every sequence below is a real UTF-8 byte pair misread as cp1252. They
are searched as literal strings, not as a regex, so nothing here can be defeated by an escape.

WHAT THIS DOES NOT DO. It does not repair. A character can only be restored from the source that
produced it -- the registry -- and guessing the intended glyph from mangled bytes is exactly the
approximation this project refuses. Files are reported; repair is a separate, sourced act.

USAGE
    python scripts/sweep_mojibake.py [--selftest]
"""
import glob
import io
import json
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Each entry: the mangled form, and the character it almost certainly came from. The second
# column is for the human reading the report; nothing here is used to rewrite anything.
SIGNATURES = [
    ("âˆž", "∞  INFINITY"),
    ("â€”", "—  EM DASH"),
    ("â€“", "–  EN DASH"),
    ("â€™", "’  RIGHT SINGLE QUOTE"),
    ("â€œ", "“  LEFT DOUBLE QUOTE"),
    ("â€", "”  RIGHT DOUBLE QUOTE"),
    ("â€¦", "…  ELLIPSIS"),
    ("â‰¥", "≥  GREATER-THAN OR EQUAL"),
    ("â‰¤", "≤  LESS-THAN OR EQUAL"),
    ("Âµ", "µ  MICRO SIGN"),
    ("Â±", "±  PLUS-MINUS"),
    ("Â°", "°  DEGREE SIGN"),
    ("Î±", "α  GREEK ALPHA"),
    ("Î²", "β  GREEK BETA"),
    ("Ï„", "τ  GREEK TAU"),
    ("â‰ˆ", "≈  ALMOST EQUAL"),
    ("â€°", "‰  PER MILLE"),
    ("Ã©", "é  E ACUTE"),
    ("Ã¶", "ö  O UMLAUT"),
    ("Ã¼", "ü  U UMLAUT"),
]


def scan_text(text):
    hits = {}
    for bad, meant in SIGNATURES:
        n = text.count(bad)
        if n:
            hits[meant] = hits.get(meant, 0) + n
    return hits


def context(text, bad, width=46):
    i = text.find(bad)
    if i < 0:
        return ""
    return text[max(0, i - width):i + len(bad) + width].replace("\n", " ")


def run():
    targets = []
    for pat in ("ssot/*/*.json", "evidence/**/*.json", "*.md", "scripts/*.py",
                "ssot/*.py", "*.html"):
        targets.extend(glob.glob(os.path.join(REPO, pat), recursive=True))
    targets = sorted(set(targets))

    flagged, scanned, unreadable = [], 0, []
    for p in targets:
        try:
            with io.open(p, "r", encoding="utf-8") as fh:
                t = fh.read()
        except Exception as e:
            unreadable.append((p, str(e)[:80]))
            continue
        scanned += 1
        hits = scan_text(t)
        if hits:
            worst = max(hits.items(), key=lambda kv: kv[1])
            bad = [b for b, m in SIGNATURES if m == worst[0]][0]
            flagged.append((os.path.relpath(p, REPO).replace(os.sep, "/"), hits,
                            context(t, bad)))

    print("scanned %d file(s); %d unreadable" % (scanned, len(unreadable)))
    for p, why in unreadable:
        print("   UNREADABLE %-56s %s" % (os.path.relpath(p, REPO), why))
    print("\nfiles carrying mojibake: %d\n" % len(flagged))
    for rel, hits, ctx in flagged:
        print("  %s" % rel)
        for meant, n in sorted(hits.items(), key=lambda kv: -kv[1]):
            print("      %-32s x%d" % (meant, n))
        print("      context: ...%s..." % ctx)

    dest = os.path.join(REPO, "evidence", "2026-08-19-batch1", "mojibake_sweep.json")
    with io.open(dest, "w", encoding="utf-8") as fh:
        fh.write(json.dumps({
            "swept_utc": "2026-08-19",
            "files_scanned": scanned,
            "files_flagged": len(flagged),
            "unreadable": [[os.path.relpath(p, REPO), w] for p, w in unreadable],
            "what_this_does_not_do": ("It does not repair. A character can only be restored "
                                      "from the source that produced it. Guessing the intended "
                                      "glyph from mangled bytes is an approximation, and this "
                                      "project reports unresolvable rather than approximating."),
            "flagged": [{"file": r, "signatures": h, "context": c} for r, h, c in flagged],
        }, indent=1, ensure_ascii=False))
    print("\nwrote %s" % os.path.relpath(dest, REPO))
    return 0


def selftest():
    fails = []

    def ck(n, got, want):
        ok = got == want
        print("  %-62s %s  %r" % (n, "ok" if ok else "FAIL", got))
        if not ok:
            fails.append(n)

    print("1. THE ACTUAL STRING THIS SWEEP WAS BORN FROM:")
    real = "Phase 2/3, PK: Area Under the Concentration-time Curve (AUC0-âˆž)"
    ck("flagged", bool(scan_text(real)), True)
    ck("and named as INFINITY", list(scan_text(real))[0], "∞  INFINITY")

    print("\n2. THE CORRECT TEXT IS NOT FLAGGED -- no false positive on clean Unicode:")
    ck("clean infinity", scan_text("Curve (AUC0-∞) for Bebtelovimab"), {})
    ck("clean em dash", scan_text("a — b"), {})
    ck("clean greek", scan_text("τ² = 0.04, α = 0.05"), {})
    ck("plain ascii", scan_text("no special characters here at all"), {})

    print("\n3. COUNTS ARE PER OCCURRENCE, so a report cannot understate the damage:")
    ck("three em dashes", scan_text("aâ€”bâ€”câ€”d"),
       {"—  EM DASH": 3})

    print("\n%s" % ("SELFTEST FAILED: %s" % fails if fails else "SELFTEST PASSED"))
    return 1 if fails else 0


if __name__ == "__main__":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.exit(selftest() if "--selftest" in sys.argv else run())
