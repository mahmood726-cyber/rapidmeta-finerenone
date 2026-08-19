#!/usr/bin/env python3
"""REPAIR DOUBLE-ENCODED CHARACTERS IN DELIVERED PAGES -- by exact inverse, never by guess.

THE DEFECT, verified at byte level and not through any decoder:

    b'"Voclosporin \\xc3\\xa2\\xe2\\x82\\xac\\xe2\\x80\\x9d AURORA-1"'

Those bytes are the UTF-8 encoding of `â€”`, which is itself cp1252's misreading of the UTF-8
em dash. A string took a cp1252 round trip at generation time and was then SERVED. Seven
committed pages carry it: 17 em dashes and one Greek alpha, reader-visible in trial display
names.

WHY THIS IS A REPAIR AND NOT AN APPROXIMATION. The transform that caused it is exactly
invertible: take the mangled text, encode it as cp1252, decode it as UTF-8, and the original
character comes back. Nothing is guessed. The inverse is applied ONLY where it round-trips
cleanly; anything that does not is left alone and reported.

    'â€”'.encode('cp1252').decode('utf-8')  ->  '—'

WHAT THIS DOES NOT CLAIM. It does not identify the generator that produced the corruption. The
SSOT objects are clean -- all 240 scan clean -- so these strings did not come from them, and the
source is NOT YET TRACED. Repairing the served bytes does not close that, and a regenerated page
may reintroduce it. Recorded as open rather than implied fixed.
"""
import io
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

PAGES = [
    "AGALSIDASE_FABRY_AUTO_FULL_REVIEW.html",
    "DAPAGLIFLOZIN_T2D_CV_AUTO_FULL_REVIEW.html",
    "EVIDENCE_GAPS.html",
    "HEMOPHILIA_GENE_THERAPY_REVIEW.html",
    "VOCLOSPORIN_LN_AUTO_FULL_REVIEW.html",
    "VOCLOSPORIN_LN_REVIEW.html",
    "VOCLOSPORIN_LUPUS_AUTO_FULL_REVIEW.html",
]

MANGLED = ["â€”", "â€“", "â€™", "â€œ", "â€¦", "âˆž", "â‰¥", "â‰¤", "Î±", "Î²", "Ï„",
           "Âµ", "Â±", "Â°", "Ã©", "Ã¶", "Ã¼"]


def invert(s):
    """The exact inverse. Returns None if it does not round-trip -- never a guess."""
    try:
        out = s.encode("cp1252").decode("utf-8")
    except (UnicodeEncodeError, UnicodeDecodeError):
        return None
    # It must survive the forward transform too, or the inversion is not the one that happened.
    try:
        if out.encode("utf-8").decode("cp1252") != s:
            return None
    except (UnicodeEncodeError, UnicodeDecodeError):
        return None
    return out


def run(apply_it):
    total, touched, refused = 0, [], []
    for name in PAGES:
        p = os.path.join(REPO, name)
        if not os.path.exists(p):
            refused.append((name, "not on disk"))
            continue
        # BYTES, NOT TEXT. The first version read with `io.open(..., "r", encoding="utf-8")`,
        # whose universal-newline translation turned every CRLF into LF, and wrote back with
        # `newline=""`. The 18-character repair became a 40,946-line diff that rewrote the line
        # endings of seven DELIVERED pages. Reading bytes leaves everything but the mangled
        # sequences untouched, and the CRLF count is asserted unchanged before any write.
        with io.open(p, "rb") as fh:
            raw = fh.read()
        t = raw.decode("utf-8")
        before, n = t, 0
        for bad in MANGLED:
            if bad not in t:
                continue
            good = invert(bad)
            if good is None:
                refused.append((name, "%r does not round-trip -- left alone" % bad))
                continue
            n += t.count(bad)
            t = t.replace(bad, good)
        if n:
            total += n
            touched.append((name, n))
            print("  %-46s %d replacement(s)" % (name, n))
            if apply_it:
                out = t.encode("utf-8")
                # NOTHING BUT THE MANGLED SEQUENCES MAY CHANGE.
                crlf = bytes([13, 10])
                assert out.count(crlf) == raw.count(crlf), (
                    "%s: line endings changed -- refusing" % name)
                assert len(out) < len(raw), "%s did not shrink" % name
                with io.open(p, "wb") as fh:
                    fh.write(out)
                with io.open(p, "rb") as fh:
                    assert fh.read() == out, "%s did not write back byte-identical" % name

    print("\n%d replacement(s) across %d page(s) %s"
          % (total, len(touched), "APPLIED" if apply_it else "would be applied"))
    for n, why in refused:
        print("   REFUSED %-42s %s" % (n, why))
    return 0


def selftest():
    fails = []

    def ck(n, got, want):
        ok = got == want
        print("  %-58s %s  %r" % (n, "ok" if ok else "FAIL", got))
        if not ok:
            fails.append(n)

    print("1. THE INVERSE IS EXACT ON THE CHARACTERS ACTUALLY FOUND:")
    ck("em dash", invert("â€”"), "—")
    ck("greek alpha", invert("Î±"), "α")
    ck("infinity", invert("âˆž"), "∞")

    print("\n2. IT REFUSES ANYTHING THAT DOES NOT ROUND-TRIP, rather than guessing:")
    ck("already-correct text is not 'repaired' again", invert("—"), None)
    # THE ASSERTION HERE WAS WRONG BEFORE THE CODE WAS. It expected None for plain ASCII, but
    # ASCII round-trips cp1252 -> utf-8 UNCHANGED, so `invert` correctly returns it as a no-op.
    # Refusing ASCII would have been the wrong behaviour to demand; the identity is the right
    # answer, and in any case the caller only ever passes strings drawn from MANGLED. Stated
    # here so a reader does not conclude the guard was relaxed to make a test pass.
    ck("plain ascii is returned unchanged -- a no-op, not a refusal",
       invert("AURORA-1"), "AURORA-1")

    print("\n3. AND THE FULL STRING FROM THE PAGE COMES BACK EXACTLY:")
    ck("the served name", "Voclosporin â€” AURORA-1".replace("â€”", invert("â€”")),
       "Voclosporin — AURORA-1")

    print("\n%s" % ("SELFTEST FAILED: %s" % fails if fails else "SELFTEST PASSED"))
    return 1 if fails else 0


if __name__ == "__main__":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    if "--selftest" in sys.argv:
        sys.exit(selftest())
    sys.exit(run("--apply" in sys.argv))
