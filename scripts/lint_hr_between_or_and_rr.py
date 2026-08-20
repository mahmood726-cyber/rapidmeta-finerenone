"""A stored hazard ratio must lie between the odds ratio and the risk ratio from the same
arm counts.

THIS IS THE TEST THAT SHOULD HAVE EXISTED YESTERDAY. scripts/lint_registration_counts_arm_
order.py compared a stored effect against an odds ratio recomputed from arms[], flagged
four rows as "does NOT reproduce", and was wrong about every one of them: all four store a
HAZARD RATIO read from a publication, and an HR is not an OR. AN HR MERELY DIFFERING FROM
AN OR IS NOT A SIGNAL.

An HR outside [RR, OR] on the same counts IS one. For a binary outcome with a treatment
that reduces risk, the risk ratio is the least extreme, the odds ratio the most, and the
hazard ratio for time to first event sits between them -- the standard non-collapsibility
ordering. It is a WEAK test and that is its value: it cannot confirm an HR is right, and it
cannot be passed by a number invented from nothing.

Verified on sglt2-hf when the containment was first noticed, four rows for four:

    DAPA-HF            HR 0.74   RR 0.7683   OR 0.7233
    EMPEROR-Reduced    HR 0.75   RR 0.7831   OR 0.7309
    EMPEROR-Preserved  HR 0.79   RR 0.8105   OR 0.7801
    DELIVER            HR 0.82   RR 0.8396   OR 0.8083

WHAT THIS DOES NOT TEST, named rather than implied: that the HR is correct, that it belongs
to the outcome it is filed under, or that the arm counts are the right ones. Containment is
a necessary condition and nothing more. A row that passes has not been checked; it has
merely failed to be caught.

A row is only tested where the object DECLARES the effect a hazard ratio and carries event
counts on both arms. Everything else is NOT_APPLICABLE with the reason named -- because
guessing the measure is how the previous lint manufactured its false alarms.

Exit non-zero on any containment failure. NOT_ASSESSABLE, never PASS, if zero rows were
testable.
"""
import io
import json
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SSOT = os.path.join(REPO, "ssot")
TOL = 0.02          # relative slack: published HRs are rounded to two decimals


def main():
    objects_read = 0
    tested = []
    skipped = {}
    for name in sorted(os.listdir(SSOT)):
        d = os.path.join(SSOT, name)
        if not os.path.isdir(d):
            continue
        fp = os.path.join(d, name + ".json")
        if not os.path.exists(fp):
            continue
        try:
            obj = json.load(io.open(fp, encoding="utf-8"))
        except Exception:
            continue
        objects_read += 1
        for t in (obj.get("inputs") or {}).get("trials") or []:
            arms = t.get("arms") or []
            tr = [a for a in arms if a.get("role") == "treatment"]
            ct = [a for a in arms if a.get("role") == "control"]
            if len(tr) != 1 or len(ct) != 1:
                skipped["not a two-arm contrast on arms[]"] = \
                    skipped.get("not a two-arm contrast on arms[]", 0) + 1
                continue
            a, na = tr[0].get("events"), tr[0].get("participants")
            c, nc = ct[0].get("events"), ct[0].get("participants")
            if None in (a, na, c, nc) or not (0 < a < na) or not (0 < c < nc):
                skipped["arms[] carries no usable event counts"] = \
                    skipped.get("arms[] carries no usable event counts", 0) + 1
                continue
            for oid, bo in (t.get("by_outcome") or {}).items():
                eff = (bo or {}).get("effect") or {}
                pt = eff.get("point")
                if pt is None:
                    continue
                measure = eff.get("measure")
                if measure != "HR":
                    key = ("effect declares %s, not HR" % (measure or "no measure"))
                    skipped[key] = skipped.get(key, 0) + 1
                    continue
                rr = (a / na) / (c / nc)
                orv = (a / (na - a)) / (c / (nc - c))
                lo, hi = min(rr, orv), max(rr, orv)
                inside = (lo * (1 - TOL)) <= float(pt) <= (hi * (1 + TOL))
                tested.append((name, t.get("name") or t.get("nct"), oid, float(pt),
                               rr, orv, inside))

    print("objects read            %d" % objects_read)
    print("rows TESTED             %d" % len(tested))
    print("rows not applicable     %d" % sum(skipped.values()))
    for reason, n in sorted(skipped.items(), key=lambda kv: -kv[1]):
        print("    %-46s %d" % (reason, n))
    print()
    if not tested:
        print("NOT_ASSESSABLE: no row declared a hazard ratio beside usable arm counts. A "
              "checker with nothing to check has not passed.")
        return 2

    bad = [r for r in tested if not r[6]]
    print("%-34s %-26s %-24s %8s %8s %8s  %s"
          % ("topic", "trial", "outcome", "HR", "RR", "OR", ""))
    print("-" * 132)
    for name, trial, oid, pt, rr, orv, inside in tested:
        print("%-34s %-26s %-24s %8.4f %8.4f %8.4f  %s"
              % (name[:34], str(trial)[:26], oid[:24], pt, rr, orv,
                 "" if inside else "OUTSIDE [RR, OR]"))
    print()
    if bad:
        print("REFUSED: %d of %d hazard ratios lie outside the interval bounded by the risk "
              "ratio and the odds ratio from their own arm counts. That is not proof the "
              "number is wrong; it is a number the arm counts cannot account for."
              % (len(bad), len(tested)))
        return 1
    print("PASS, measured on %d testable rows across %d objects: every stored hazard ratio "
          "lies between the risk ratio and the odds ratio from its own arm counts. THIS IS "
          "A NECESSARY CONDITION AND NOTHING MORE -- a row that passes has not been "
          "checked, it has failed to be caught." % (len(tested), objects_read))
    return 0


if __name__ == "__main__":
    sys.exit(main())
