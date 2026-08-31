#!/usr/bin/env python
"""Planted-defect proof for scripts/check_cross_surface_consistency.py.

A check nobody has watched fail is not a check.  This script perturbs ONE value
in a REAL, tracked file (outputs/portfolio_index.json), asserts the gate refuses
where it previously did not, restores the file, and asserts the restoration is
byte-identical and the gate's verdict returns to exactly its baseline.

Target: ROTAVIRUS_VACCINE_AFRICA_REVIEW.html.  It is the one review in the
corpus where both surfaces compute the SAME quantity (both declare an OR, both
k=3) and the point estimates already agree to 6 dp - so an ESTIMATE_MISMATCH is
absent at baseline and must appear when the value is moved.  The perturbation
leaves the JSON well-formed and every single-file gate in the repo still green:
only a check that reads BOTH surfaces can see it.

Exit 0 = the gate demonstrably fails on the plant and recovers on restore.
Exit 1 = the gate did NOT fail when it should have, or did not recover.
"""
from __future__ import annotations

import hashlib
import json
import sys

sys.path.insert(0, "scripts")
import check_cross_surface_consistency as gate  # noqa: E402

PORTFOLIO = "outputs/portfolio_index.json"
INDEX = "origin/main:index.html"          # the DEPLOYED landing page
TARGET = "ROTAVIRUS_VACCINE_AFRICA_REVIEW.html"
FIELD = "pooled_OR"
FACTOR = 1.30                              # move the estimate 30%

ok = True


def say(sym, msg):
    print("  {} {}".format(sym, msg))


def assert_(cond, msg):
    global ok
    say("PASS" if cond else "FAIL", msg)
    if not cond:
        ok = False
    return cond


def verdict():
    """Return the gate's findings as a comparable set of (code, subject)."""
    fail, _, _ = gate.check(INDEX, PORTFOLIO)
    return {(c, s) for c, s, _ in fail}


def leaf_diff(a, b, path=""):
    """Yield dotted paths where two parsed JSON documents differ."""
    if type(a) is not type(b):
        yield path or "<root>"
        return
    if isinstance(a, dict):
        for k in set(a) | set(b):
            if k not in a or k not in b:
                yield "{}.{}".format(path, k)
            else:
                yield from leaf_diff(a[k], b[k], "{}.{}".format(path, k))
    elif isinstance(a, list):
        if len(a) != len(b):
            yield path
            return
        for i, (x, y) in enumerate(zip(a, b)):
            yield from leaf_diff(x, y, "{}[{}]".format(path, i))
    elif a != b:
        yield path or "<root>"


def main():
    print(__doc__.strip().splitlines()[0])
    print("=" * 72)

    original = open(PORTFOLIO, "rb").read()
    sha_before = hashlib.sha256(original).hexdigest()
    doc_before = json.loads(original.decode("utf-8"))
    print("\nreal file : {}".format(PORTFOLIO))
    print("index     : {}".format(INDEX))
    print("sha256    : {}".format(sha_before))

    row = next((r for r in doc_before["rows"] if r.get("file") == TARGET), None)
    if row is None or row.get(FIELD) is None:
        print("\nABORT: {} carries no {} in this file.".format(TARGET, FIELD))
        return 1
    live = row[FIELD]

    # ---- 1. baseline -----------------------------------------------------
    print("\n[1] BASELINE - gate on the untouched file")
    base = verdict()
    print("      {} standing finding(s)".format(len(base)))
    assert_(("ESTIMATE_MISMATCH", TARGET) not in base,
            "no ESTIMATE_MISMATCH for {} at baseline "
            "(its estimate agrees across surfaces: {})".format(TARGET, live))

    try:
        # ---- 2. plant ----------------------------------------------------
        planted = round(live * FACTOR, 6)
        print("\n[2] PLANT - {}.{}  {}  ->  {}".format(TARGET, FIELD, live, planted))
        doc_after = json.loads(original.decode("utf-8"))
        for r in doc_after["rows"]:
            if r.get("file") == TARGET:
                r[FIELD] = planted
        payload = json.dumps(doc_after, indent=2, ensure_ascii=False).encode("utf-8")
        open(PORTFOLIO, "wb").write(payload)

        diffs = list(leaf_diff(doc_before, doc_after))
        assert_(len(diffs) == 1, "exactly one leaf changed: {}".format(diffs))
        assert_(json.loads(open(PORTFOLIO, "rb").read().decode("utf-8")) == doc_after,
                "planted file is still well-formed JSON (no single-file gate sees a problem)")

        # ---- 3. the gate must refuse -------------------------------------
        print("\n[3] GATE ON THE PLANTED FILE")
        after = verdict()
        new = after - base
        gone = base - after
        assert_(("ESTIMATE_MISMATCH", TARGET) in after,
                "gate now REFUSES with ESTIMATE_MISMATCH on {}".format(TARGET))
        assert_(new == {("ESTIMATE_MISMATCH", TARGET)},
                "the plant produced exactly one new finding, no collateral: "
                "{}".format(sorted(new)))
        assert_(not gone, "the plant silenced nothing: {}".format(sorted(gone)))
        print("      {} finding(s) after plant (was {})".format(len(after), len(base)))

    finally:
        # ---- 4. restore --------------------------------------------------
        print("\n[4] RESTORE")
        open(PORTFOLIO, "wb").write(original)
        sha_after = hashlib.sha256(open(PORTFOLIO, "rb").read()).hexdigest()
        assert_(sha_after == sha_before,
                "file restored byte-for-byte (sha256 {})".format(sha_after))

    # ---- 5. the gate must recover ---------------------------------------
    print("\n[5] GATE ON THE RESTORED FILE")
    back = verdict()
    assert_(back == base,
            "verdict returned to baseline exactly ({} findings)".format(len(back)))
    assert_(("ESTIMATE_MISMATCH", TARGET) not in back,
            "planted finding is gone")

    print("\n" + "=" * 72)
    print("PROVEN: the gate failed on the plant and recovered on restore."
          if ok else
          "NOT PROVEN: see FAIL lines above.")
    return 0 if ok else 1


if __name__ == "__main__":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.exit(main())
