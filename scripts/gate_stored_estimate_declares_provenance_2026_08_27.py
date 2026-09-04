#!/usr/bin/env python3
"""EVERY STORED ESTIMATE MUST SAY WHERE ITS NUMBER CAME FROM.

Measured 2026-08-26 over the 176 per-trial estimates carrying a point:

    journal cited                0   (0%)
    registry recorded           43   (24%)
    NOTHING RECORDED           133   (76%)

Not one number this review publishes cites a journal, and three quarters say nothing at all.
That is not a documentation gap, it is what made `k` meaningless: a count of rows whose origin
is unstated measures the corpus's reach, not the evidence.

    THE RULE THIS GATE ENFORCES IS NOT "CITE A SOURCE". It is: DECLARE A TIER.

`ssot/provenance_tier.py` holds the closed set and the reason each tier ranks where it does.
The tier matters more than the source because "ClinicalTrials.gov" describes both a posted
results table and a background citation the protocol listed, and those are not the same
evidence. `REGISTRY_REFERENCE_ROW` exists precisely so the second cannot masquerade as the
first, and it is barred from carrying a point at all.

BASELINE, NOT AMNESTY. The 133 untraced estimates are recorded in
`scripts/baselines/estimate_provenance_baseline.json` so this gate can be wired in before the
backlog is cleared. THE COUNT MUST NOT RISE: a NEW estimate with no tier fails. The baseline
also refuses to rot -- if it names a row that no longer exists, the gate says so, so the list
cannot quietly become a permanent excuse for rows nobody intends to fix.

WHY A GATE AND NOT A CONVENTION. The corpus already had a convention; it produced 0 of 176.
A convention is a thing everyone agrees with and nobody is stopped by.
"""
import io
import json
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, "ssot"))
SSOT = os.path.join(REPO, "ssot")
BASELINE = os.path.join(REPO, "scripts", "baselines",
                        "estimate_provenance_baseline.json")

from provenance_tier import validate, UNSET  # noqa: E402


def estimates():
    """Every stored value that IS an estimate a reader could act on.

    Two populations, both counted, because they are written by different code and a gate that
    watched one would be silently blind to the other -- the two-layer defect this project has
    already paid for twice.
    """
    for t in sorted(os.listdir(SSOT)):
        p = os.path.join(SSOT, t, t + ".json")
        if not os.path.isdir(os.path.join(SSOT, t)) or not os.path.exists(p):
            continue
        with io.open(p, encoding="utf-8") as fh:
            obj = json.load(fh)
        for oid, b in ((obj.get("results") or {}).get("by_outcome") or {}).items():
            for i, r in enumerate((b or {}).get("per_trial") or []):
                if isinstance(r, dict) and r.get("point") is not None:
                    yield ("%s|results.by_outcome.%s.per_trial[%d]" % (t, oid, i), r)
        for tr in ((obj.get("inputs") or {}).get("trials") or []):
            n = (tr.get("nct") or tr.get("id") or "?")
            for oid, b in (tr.get("by_outcome") or {}).items():
                e = (b or {}).get("effect") or {}
                if e.get("point") is not None:
                    yield ("%s|inputs.trials[%s].by_outcome.%s.effect" % (t, n, oid), e)


# KNOWN-NEGATIVE, NAMED RATHER THAN DESCRIBED, WITH THE RATE MEASURED NOT ASSERTED.
#
#     apixaban-vte-treatment|results.by_outcome.major_bleeding.per_trial[2]
#
# Chosen because it is the case this check is MOST LIKELY TO GET WRONG, not because it
# passes. Its declared tier is COULD_NOT_DETERMINE -- a row that explicitly states its
# provenance could not be established. It therefore LOOKS EXACTLY LIKE THE DEFECT THIS GATE
# HUNTS (a number a reader cannot trace) while being a VALID DECLARATION, and it carries
# `migrated_from_legacy_string: "REGISTRY -- ClinicalTrials.gov posted result..."`, so it is
# a row that WAS untraced and has since been declared honestly. Any implementation that
# conflates "declares it cannot determine" with "declares nothing" flags it.
#
# A KNOWN-NEGATIVE DRAWN FROM THE EASY MAJORITY MEASURES NOTHING: 6 rows here carry
# REGISTRY_POSTED_RESULT and 3 carry JOURNAL_FULL_TEXT, and any of those would pass under a
# broken implementation too. This one would not.
#
# UNREACHABLE IS NOT ZERO. If the row is gone the rate is reported UNMEASURED and the gate
# refuses, because an unmeasured false-positive rate and a measured zero are different
# claims and only one of them is evidence.
KNOWN_NEGATIVE = "apixaban-vte-treatment|results.by_outcome.major_bleeding.per_trial[2]"


def known_negative(rows):
    """(n, false_positives, note) measured over the SAME traversal the findings come from."""
    for key, rec in rows:
        if key == KNOWN_NEGATIVE:
            probs = validate(rec)
            tier = (rec.get("provenance") or {}).get("tier")
            return 1, (1 if probs else 0), "tier=%s" % tier
    return 0, 0, "NOT REACHED by the traversal"


def main():
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    rows = list(estimates())
    problems = {}
    tiers = {}
    for key, rec in rows:
        p = rec.get("provenance")
        if isinstance(p, dict):
            tiers[key] = p.get("tier") or "(block, no tier)"
        elif isinstance(p, str):
            tiers[key] = "(legacy string)"
        else:
            tiers[key] = "(none)"
        probs = validate(rec)
        if probs:
            problems[key] = probs

    if "--write-baseline" in sys.argv:
        d = os.path.dirname(BASELINE)
        if not os.path.isdir(d):
            os.makedirs(d)
        with io.open(BASELINE, "w", encoding="utf-8") as fh:
            fh.write(json.dumps({
                "written": "2026-08-27",
                "why": ("Stored estimates carrying a point with no declared provenance tier. "
                        "NOT AN AMNESTY -- each is a number a reader cannot trace. THE COUNT "
                        "MUST NOT RISE."),
                "measured": {"estimates": len(rows), "untiered": len(problems)},
                "untiered": sorted(problems)}, indent=1))
        print("wrote baseline: %d of %d estimates untiered" % (len(problems), len(rows)))
        return 0

    base = set()
    if os.path.exists(BASELINE):
        with io.open(BASELINE, encoding="utf-8") as fh:
            base = set(json.load(fh).get("untiered") or [])

    new = sorted(set(problems) - base)
    gone = sorted(base - {k for k, _ in rows})
    fixed = sorted(base - set(problems) - set(gone))

    dist = {}
    for v in tiers.values():
        dist[v] = dist.get(v, 0) + 1
    print("STORED ESTIMATES CARRYING A POINT: %d" % len(rows))
    print("   declaring a valid tier      : %d" % (len(rows) - len(problems)))
    print("   NOT declaring one           : %d" % len(problems))
    print("   baselined (known, owed)     : %d" % len(base))
    print("   NEW since the baseline      : %d" % len(new))
    print("   repaired since the baseline : %d" % len(fixed))
    print("   baselined rows now ABSENT   : %d" % len(gone))
    print()
    print("TIER DISTRIBUTION")
    for k in sorted(dist, key=lambda x: -dist[x]):
        print("   %-32s %4d" % (k, dist[k]))

    n_neg, fp_neg, neg_note = known_negative(rows)
    print()
    if n_neg == 0:
        print("KNOWN-NEGATIVE CONTROL: UNMEASURED -- %s (%s)." % (KNOWN_NEGATIVE, neg_note))
        print("   An unmeasured false-positive rate is NOT a measured zero. No count below")
        print("   is trustworthy until the control is reachable again.")
    else:
        print("KNOWN-NEGATIVE CONTROL: %d/%d matched (measured false-positive rate %.1f%%)"
              % (fp_neg, n_neg, 100.0 * fp_neg / n_neg))
        print("   %s  [%s]" % (KNOWN_NEGATIVE, neg_note))
        print("   It DECLARES that provenance could not be determined, so it resembles the")
        print("   defect while being a valid declaration -- the case most likely to be got")
        print("   wrong. It must never be flagged.")

    rc = 0
    if n_neg == 0 or fp_neg:
        print()
        print("REFUSED: the known-negative control did not hold, so this gate is not trusted "
              "for anything else and NO COUNT IS RELIED ON.")
        rc = 1
    if gone:
        print()
        print("REFUSED: the baseline names %d row(s) that no longer exist. A baseline that "
              "outlives its rows becomes a permanent excuse. Re-write it." % len(gone))
        for k in gone[:8]:
            print("   %s" % k)
        rc = 1
    if new:
        print()
        print("REFUSED: %d estimate(s) stored with no declared provenance tier." % len(new))
        print("A number whose origin is unstated cannot be weighted, checked or defended. "
              "Declare a tier from ssot/provenance_tier.py, or %s if it is genuinely "
              "untraced." % UNSET)
        for k in new[:12]:
            print("   %-70s %s" % (k[:70], problems[k][0][:60]))
        rc = 1
    if rc == 0:
        print()
        print("PASS: no new untiered estimate.")
    return rc


if __name__ == "__main__":
    sys.exit(main())
