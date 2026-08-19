#!/usr/bin/env python3
"""THE DASHBOARD'S DATA MUST NOT BE SILENTLY STALE, AND IT MUST NOT SERVE A WITHDRAWN ESTIMATE.

Two checks, and each catches a different failure:

  FRESHNESS   `outputs/portfolio_index.json` carries an OBJECTS FINGERPRINT written when it was
              projected. This recomputes it from the objects as they stand now and REFUSES when
              they differ. That is what makes staleness DETECTABLE rather than invisible -- the
              same discipline a page's build stamp provides, applied to the aggregate surface.

  CONTENT     No row may serve a `pooled_OR` for a topic whose object is WITHDRAWN, RETIRED or
              carries no pooled value. **A value served where the object says there is none is a
              DELIVERY FAILURE, not a display detail** -- it is the strongest statement a review
              can make, reversed, on the surface most readers see.

WHY A FINGERPRINT AND NOT A TIMESTAMP. A timestamp answers "when was this made", which is not
the question. The question is "do the objects still say what this was built from", and only a
hash over the object state answers it. A regenerated snapshot with a fresh timestamp and a stale
withdrawal would pass a date check and fail this one.

WHAT THIS DOES NOT ESTABLISH -- written before it was run
  * NOT that the LIVE rows' NUMBERS are right. A row that passes may still be stale by value.
    This gate answers the sharper question only.
  * NOTHING about the rows with no SSOT object. They are UNMAPPED and UNCHECKABLE, counted
    separately and never as clean, and they are the reason a passing run here is a FLOOR.
  * A snapshot that has never been projected at all is NOT_ASSESSABLE on freshness and is
    reported as such -- never as fresh.

USAGE:  python scripts/dashboard_projection_gate.py
        python scripts/dashboard_projection_gate.py --selftest
"""
import io
import json
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import project_dashboard_index as P                                    # noqa: E402


def check(snap, pmap):
    """(problems, notes) -- problems REFUSE, notes are reported and do not."""
    problems, notes = [], []
    proj = snap.get("projection") or {}
    stored = proj.get("objects_fingerprint")
    if not stored:
        problems.append(
            "the snapshot carries NO objects fingerprint, so its freshness is NOT_ASSESSABLE. "
            "An unprojected snapshot is not a fresh one. Run "
            "`python scripts/project_dashboard_index.py --apply`.")
    else:
        now = P.fingerprint(pmap)
        if now != stored:
            problems.append(
                "STALE: the objects fingerprint is %s and the snapshot was projected against "
                "%s. An object's withdrawal, retirement or pooled state has changed since. "
                "Re-project." % (now[:16], stored[:16]))

    served = []
    unmapped = 0
    for r in snap.get("rows") or []:
        if not isinstance(r, dict):
            continue
        if r.get("ssot_state") == P.UNMAPPED:
            unmapped += 1
        if not isinstance(r.get("pooled_OR"), (int, float)):
            continue
        state, detail = P.object_state(r.get("file"), pmap)
        if state in P.NOT_LIVE:
            served.append((r.get("file"), state, r.get("pooled_OR")))
    if served:
        problems.append(
            "%d row(s) serve a pooled estimate for a topic whose object does NOT support one. "
            "A WITHDRAWAL IS THE STRONGEST STATEMENT A REVIEW HERE CAN MAKE and this reverses "
            "it for every reader who never opens the page." % len(served))
    notes.append("%d row(s) have no SSOT object at all -- UNCHECKABLE, never clean. Any pass "
                 "here is a FLOOR." % unmapped)
    return problems, notes, served


def main():
    with io.open(P.SNAP, "r", encoding="utf-8") as fh:
        snap = json.load(fh)
    with io.open(P.PMAP, "r", encoding="utf-8") as fh:
        pmap = json.load(fh)
    problems, notes, served = check(snap, pmap)
    print("dashboard data: %s" % os.path.relpath(P.SNAP, REPO))
    print("rows: %d   snapshot generated: %s" % (len(snap.get("rows") or []),
                                                 snap.get("generated")))
    for n in notes:
        print("   note: %s" % n)
    if served:
        print("\n   serving a value the object does not support:")
        for f, s, v in served[:20]:
            print("      %-48s %-10s pooled_OR %s" % (f, s, v))
        if len(served) > 20:
            print("      ... and %d more" % (len(served) - 20))
    if problems:
        print("\nREFUSED:")
        for x in problems:
            print("   %s" % x)
        return 1
    print("\nOK -- the projection matches the objects as they stand, and no row serves a value "
          "its object withdrew.")
    return 0


def selftest():
    fails = []

    def ck(name, got, want):
        ok = got == want
        print("  %-66s %s  %r" % (name, "ok" if ok else "FAIL", got))
        if not ok:
            fails.append(name)

    with io.open(P.PMAP, "r", encoding="utf-8") as fh:
        pmap = json.load(fh)

    print("1. THE GATE CAN FIRE, on the case that actually shipped (P16's fourth clause):")
    bad = {"rows": [{"file": "COLCHICINE_CVD_REVIEW.html", "pooled_OR": 0.86}],
           "projection": {"objects_fingerprint": P.fingerprint(pmap)}}
    pr, _n, served = check(bad, pmap)
    ck("a withdrawn topic served with a value is refused", len(pr), 1)
    ck("and the row is named", served[0][0], "COLCHICINE_CVD_REVIEW.html")

    print("\n2. AND DOES NOT FIRE ON THE CORRECT CASE:")
    good = {"rows": [{"file": "COLCHICINE_CVD_REVIEW.html", "pooled_OR": None},
                     {"file": "SGLT2_HF_REVIEW.html", "pooled_OR": 0.76}],
            "projection": {"objects_fingerprint": P.fingerprint(pmap)}}
    ck("a nulled withdrawn row and a live row pass", check(good, pmap)[0], [])

    print("\n3. A STALE FINGERPRINT IS REFUSED -- this is the half a timestamp cannot do:")
    stale = {"rows": [], "projection": {"objects_fingerprint": "0" * 64}}
    pr = check(stale, pmap)[0]
    ck("a wrong fingerprint refuses", len(pr), 1)
    ck("and says STALE", "STALE" in pr[0], True)

    print("\n4. AN UNPROJECTED SNAPSHOT IS NOT_ASSESSABLE, never fresh:")
    none = {"rows": []}
    pr = check(none, pmap)[0]
    ck("no fingerprint refuses", len(pr), 1)
    ck("and says NOT_ASSESSABLE", "NOT_ASSESSABLE" in pr[0], True)

    print("\n5. AND THE UNMAPPED COUNT IS A NOTE, NEVER A REFUSAL:")
    um = {"rows": [{"file": "NO_SUCH.html", "ssot_state": P.UNMAPPED}],
          "projection": {"objects_fingerprint": P.fingerprint(pmap)}}
    pr, notes, _ = check(um, pmap)
    ck("an unmapped row does not refuse", pr, [])
    ck("but is reported", "UNCHECKABLE" in notes[0], True)

    print("\n%s" % ("SELFTEST FAILED: %s" % fails if fails else "SELFTEST PASSED"))
    return 1 if fails else 0


if __name__ == "__main__":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.exit(selftest() if "--selftest" in sys.argv else main())
