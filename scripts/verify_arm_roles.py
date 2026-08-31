r"""Independent check that absolute_effects.py reads the arms in the RIGHT ROLES.

THE FAILURE THIS EXISTS TO CATCH
    Nothing in a pair of integers says which arm is the control. If the two
    are swapped, every number downstream is wrong -- and wrong QUIETLY: the
    baseline becomes the treated risk, the risk difference flips sign, and
    the NNT is still a plausible two-digit number. No exception is raised
    and no output looks odd.

THE CHECK
    The store already records a per-trial relative estimate that it derived
    from those same arms. So recompute the trial's risk ratio from the arm
    counts THIS MODULE read, and compare it against the point the store
    stored. Agreement is evidence the roles are right. A reciprocal is the
    signature of a swap -- and a swap is exactly what a reciprocal looks
    like, which is why this check can tell them apart rather than merely
    noticing that something is off.

    This is not a re-reading of the same bytes by the same logic: the stored
    per-trial point was computed elsewhere, at a different time, by a
    different code path. It is an independent witness.
"""
from __future__ import annotations
import sys, os, json, math

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from absolute_effects import (candidates, evaluate, declared_comparator,
                              collect_control_arms)

TOL = 0.02  # relative tolerance; stored points are rounded to 4 dp


def check():
    agree = swapped = unchecked = mismatch = 0
    problems = []
    for path, obj, name, entry, _k in candidates():
        row = evaluate(path, obj, name, entry)
        if row["state"] != "COMPUTABLE":
            continue
        comp = declared_comparator(obj, name)
        arms, _ = collect_control_arms(obj, name, entry, comp)
        # index the store's own per-trial points
        stored = {}
        for r in (entry.get("per_trial") or []):
            if isinstance(r, dict) and isinstance(r.get("point"), (int, float)):
                key = r.get("trial_id") or r.get("nct")
                if key:
                    stored[key] = (r["point"], r.get("measure"))
        for a in arms:
            if a["treatment_events"] is None or not a["control_n"] \
                    or not a["treatment_n"]:
                unchecked += 1
                continue
            got = stored.get(a["trial"])
            if not got or got[1] != "RR":
                unchecked += 1
                continue
            point = got[0]
            cr = a["control_events"] / a["control_n"]
            tr = a["treatment_events"] / a["treatment_n"]
            if cr == 0 or tr == 0:
                unchecked += 1
                continue
            rr_as_read = tr / cr
            rr_if_swapped = cr / tr
            if abs(rr_as_read - point) <= TOL * max(point, 1e-9):
                agree += 1
            elif abs(rr_if_swapped - point) <= TOL * max(point, 1e-9):
                swapped += 1
                problems.append("SWAPPED %s/%s trial %s: as-read RR %.4f, "
                                "store says %.4f, reciprocal %.4f"
                                % (row["topic"], name, a["trial"],
                                   rr_as_read, point, rr_if_swapped))
            else:
                mismatch += 1
                problems.append("MISMATCH %s/%s trial %s: as-read RR %.4f, "
                                "store says %.4f (neither, nor reciprocal "
                                "%.4f)" % (row["topic"], name, a["trial"],
                                           rr_as_read, point, rr_if_swapped))
    return agree, swapped, mismatch, unchecked, problems


def main():
    agree, swapped, mismatch, unchecked, problems = check()
    checked = agree + swapped + mismatch
    print("ARM-ROLE VERIFICATION against the store's own per-trial estimates")
    print("  trial-arms agreeing with the stored RR : %d" % agree)
    print("  trial-arms matching the RECIPROCAL     : %d  <-- role swap" % swapped)
    print("  trial-arms matching neither            : %d" % mismatch)
    print("  trial-arms not checkable               : %d  (no stored per-trial"
          " RR, or control-only shape)" % unchecked)
    print("  checkable denominator                  : %d" % checked)
    for p in problems:
        print("  ! " + p)
    if checked == 0:
        print("\nVERDICT: NO VERDICT. Nothing was checkable, so this run "
              "measured the harness, not the arms.")
        return 2
    if swapped or mismatch:
        print("\nVERDICT: FAIL -- %d of %d checkable trial-arms disagree."
              % (swapped + mismatch, checked))
        return 1
    print("\nVERDICT: PASS -- all %d checkable trial-arms reproduce the "
          "store's own per-trial risk ratio, so the control and treatment "
          "arms are being read in the roles the store assigned them."
          % checked)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
