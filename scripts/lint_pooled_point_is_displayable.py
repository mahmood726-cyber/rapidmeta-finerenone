#!/usr/bin/env python3
"""A PUBLISHED ESTIMATE THE PAGE CANNOT DISPLAY IS AN ESTIMATE NOBODY CAN VERIFY.

TWICE IN ONE SESSION, ON THE FIRST TWO CONTINUOUS ENDPOINTS EVER GATED.

    bococizumab   object -55.2406   page -55.24    delivery REFUSED
    azilsartan    object  -5.6912   page  -5.691   delivery REFUSED

`ssot/build_tabbed.py` renders four SIGNIFICANT FIGURES. The pools were stored at four DECIMAL
PLACES. For a risk ratio near 0.78 those are the same thing -- 0.7763 either way -- which is
why every ratio pool in this corpus survived and why nobody had to choose a convention. For a
mean difference of -55 they are not: four significant figures is TWO decimals. For -5.69 it is
three. WHICH CONVENTION WINS DEPENDS ON THE MAGNITUDE OF THE ESTIMATE.

    THE BYTES MATCHED THE BUILD PERFECTLY BOTH TIMES. md5 identical, HTTP 200. What did not
    match was the BUILD against the OBJECT, and a hash alone would have passed both.
    `scripts/verify_delivered_bytes.py`'s content limb caught them -- AFTER a deploy.

This runs BEFORE. It is the same defect `ssot/build_tabbed.py` records in its own docstring at
three significant figures -- sotagliflozin's 0.7171 rendering as 0.717 -- and the rule written
there is the rule enforced here:

    THIS IS THE ONE PLACE WHERE THE DISPLAYED NUMBER MUST EQUAL THE VERIFIED NUMBER.

WHAT IT CHECKS. For every object with a live pooled estimate, whether `point`, `ci_low` and
`ci_high` survive `projectors.sig(x, 4)` unchanged. If they do not, the published string appears
nowhere in the page and the delivery content check will refuse it.

WHAT IT DOES NOT CHECK, so a clean run is not read as more than it is:
  - NOT that the estimate is CORRECT, or that the page renders it in the place a reader looks.
    It compares a stored number to its own rounding.
  - NOT per-trial rows, subgroup estimates or sensitivity analyses. Only the pooled headline,
    because that is what `verify_delivered_bytes.py` projects and therefore what can fail a
    delivery.
  - It reads `sig()` from `ssot/projectors.py` rather than reimplementing it, so if the display
    precision changes this gate changes with it and cannot drift out of agreement.

USAGE:  python scripts/lint_pooled_point_is_displayable.py
        python scripts/lint_pooled_point_is_displayable.py --selftest
"""
import io
import json
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SSOT = os.path.join(REPO, "ssot")
sys.path.insert(0, SSOT)
import projectors as pj                                                  # noqa: E402

FIGURES = 4
FIELDS = ("point", "ci_low", "ci_high")


def displayable(x):
    """Does this value survive the page's own rounding unchanged?"""
    if not isinstance(x, float):
        return True                       # ints and None render exactly
    try:
        return float(pj.sig(x, FIGURES)) == x
    except (TypeError, ValueError):
        return True                       # unrenderable is a different check's business


def scan():
    """[(topic, outcome, field, stored, rendered)] over every live pooled estimate."""
    bad = []
    checked = 0
    for d in sorted(os.listdir(SSOT)):
        p = os.path.join(SSOT, d, d + ".json")
        if not os.path.exists(p):
            continue
        try:
            with io.open(p, encoding="utf-8") as fh:
                obj = json.load(fh)
        except (ValueError, OSError):
            continue
        for oid, blk in (((obj.get("results") or {}).get("by_outcome")) or {}).items():
            if not isinstance(blk, dict):
                continue
            pooled = blk.get("pooled") or {}
            if pooled.get("withdrawn") or pooled.get("point") is None:
                continue
            checked += 1
            for f in FIELDS:
                v = pooled.get(f)
                if not displayable(v):
                    bad.append((d, oid, f, v, pj.sig(v, FIGURES)))
    return bad, checked


BASELINE = os.path.join(REPO, "evidence", "pooled_point_displayable_baseline.json")


def main():
    """A RATCHET, AND HERE IS WHY IT IS NOT A BLOCK.

    Measured before wiring: 44 undisplayable values over 18 topics, of which 13 are the POOLED
    POINT and 31 are interval bounds. Blocking outright would refuse every commit over a
    condition that predates this gate by months.

    ONLY THE POINT CAN FAIL A DELIVERY. `verify_delivered_bytes.expected_from_object` projects
    the pooled POINT and nothing else, so an undisplayable `ci_high` is a page that rounds its
    interval -- ordinary, and invisible to the delivery check. The 31 are reported and not
    blocked, and this file says which is which rather than presenting one number.

    NONE OF THE 13 IS IN THE DELIVERY MAP TODAY. Every one WOULD refuse the moment it were
    added, which is exactly the trap that caught bococizumab and azilsartan within an hour of
    each other. The baseline names them, so adding one becomes a deliberate act.
    """
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    bad, checked = scan()
    points = [b for b in bad if b[2] == "point"]
    bounds = [b for b in bad if b[2] != "point"]
    print("live pooled estimates checked         %d" % checked)
    print("POOLED POINTS the page cannot display %d   <- these can FAIL A DELIVERY"
          % len(points))
    for topic, oid, f, stored, rendered in points:
        print("   %-46s %-24s stored %r renders %s" % (topic, oid, stored, rendered))
    print("interval bounds, reported not blocked %d   <- the delivery check projects the "
          "POINT only, so a rounded interval cannot fail it" % len(bounds))

    cur = sorted({t for t, _o, _f, _s, _r in points})
    if not os.path.exists(BASELINE):
        with io.open(BASELINE, "w", encoding="utf-8") as fh:
            fh.write(json.dumps({"undisplayable_points": cur}, indent=1))
        print("")
        print("baseline written: %s" % BASELINE)
        return 0
    with io.open(BASELINE, encoding="utf-8") as fh:
        base = set(json.load(fh).get("undisplayable_points") or [])
    new_ones = sorted(set(cur) - base)
    if new_ones:
        for t in new_ones:
            print("")
            print("REFUSED: %s publishes a pooled point the page cannot render." % t)
        print("The stored string will appear NOWHERE in the delivered bytes and the delivery "
              "content check will refuse it. Store what the page displays; keep full precision "
              "in the evidence file.")
        return 1
    if set(cur) != base:
        with io.open(BASELINE, "w", encoding="utf-8") as fh:
            fh.write(json.dumps({"undisplayable_points": cur}, indent=1))
        print("")
        print("baseline advanced (fewer topics affected): %s" % BASELINE)
    print("")
    print("no NEW pooled point is stored at a precision the page cannot render.")
    print("NOT CHECKED: whether any estimate is CORRECT; nothing outside the pooled headline; "
          "and the %d baselined topics are NOT absolved -- each would refuse the moment it "
          "entered the delivery map." % len(base))
    return 0


def selftest():
    """P16, and the firing cases are the two that REALLY happened, not invented values."""
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    fails = []

    def check(name, got, want):
        ok = got == want
        print("  %-62s %s  %r" % (name, "ok" if ok else "FAIL", got))
        if not ok:
            fails.append(name)

    # THE TWO THAT ACTUALLY OCCURRED, both refused at the public host before this existed.
    check("bococizumab's -55.2406 is NOT displayable", displayable(-55.2406), False)
    check("azilsartan's  -5.6912 is NOT displayable", displayable(-5.6912), False)
    # AND THE VALUES THAT SURVIVED, which is why nobody had to choose a convention until now.
    check("a risk ratio 0.7763 IS displayable", displayable(0.7763), True)
    check("alirocumab's -54.66 IS displayable", displayable(-54.66), True)
    check("the corrected -55.24 IS displayable", displayable(-55.24), True)
    check("an int is displayable", displayable(2), True)
    check("None is displayable", displayable(None), True)

    # THE PROPERTY IS THE RATCHET'S, NOT A BLOCK'S -- and this case asserted the block's
    # until the measurement came in. `bad == []` is false and will stay false: 44 values over
    # 18 topics predate this gate. Asserting it would have made the suite red for a condition
    # the gate deliberately does not block, which is a self-test disagreeing with the file it
    # tests about what the file is for.
    bad, checked = scan()
    points = {t for t, _o, f, _s, _r in bad if f == "point"}
    with io.open(BASELINE, encoding="utf-8") as fh:
        base = set(json.load(fh).get("undisplayable_points") or [])
    check("no pooled point is undisplayable BEYOND the baseline", sorted(points - base), [])
    check("the baseline is non-empty -- an empty one would absolve everything silently",
          len(base) > 0, True)
    check("and there is something to check -- a scan over zero pools proves nothing",
          checked > 0, True)
    # The two that shipped tonight are FIXED and must be absent from the baseline, or the
    # ratchet would be quietly carrying the very defects it was written for.
    check("bococizumab is NOT baselined -- it was fixed, not excused",
          "bococizumab-lipid-review" in base, False)
    check("azilsartan is NOT baselined either",
          "azilsartan-chlorthalidone-vs-olmesartan-hctz" in base, False)

    print("\n%s" % ("ALL PROOFS HELD" if not fails else "FAILED: %s" % fails))
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(selftest() if "--selftest" in sys.argv else main())
