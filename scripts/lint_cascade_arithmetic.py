#!/usr/bin/env python3
"""THE CASCADE MUST RECONCILE WITH ITSELF, AND ON THREE OBJECTS IT DOES NOT.

FOUND 2026-08-19 while re-gating the five completed topics against the repaired classifier.

    alirocumab-lipid   k2_role_located 99   k3+k4+k5 = 98   kNA 1
    attr-cm-review     k2_role_located 55   k3+k4+k5 = 52   kNA 3
    iv-iron-hf         k2_role_located 47   k3+k4+k5 = 45   kNA 2

`k2_role_located` is defined by the instrument that produced it -- `ssot/batch1_cascade.py` --
as `len(EXPERIMENTAL) + len(COMPARATOR) + len(BACKGROUND)`. On these three it holds `k0`
instead, so **the stage named "role located" is counting the records whose role could NOT be
located.** kNA is added twice: once as itself, and once inside the count that says it was
resolved.

THE DIRECTION IS THE FAMILIAR ONE. It makes the instrument look more successful than it was --
"every record classified" -- which is the same overclaim as reporting a NOT_ASSESSABLE as an
exclusion, moved one stage later.

AND IT IS INVISIBLE ON EXACTLY THE OBJECTS THAT CANNOT EXPOSE IT. bempedoic-acid-review and
sglt2-hf both carry kNA = 0, so k0 and k3+k4+k5 coincide and the field reads correct. A defect
that only shows itself where kNA > 0 is one a spot-check of two topics will pass.

    A SUM THAT IS RIGHT WHENEVER THE THING IT OMITS IS ZERO HAS NOT BEEN TESTED.

WHAT THIS CHECKS -- all arithmetic INTERNAL to the object, never against an outside expectation:

  A  k2_role_located == k3 + k4 + k5
  B  k0_surfaced     == k3 + k4 + k5 + kNA (+ kUNREACHABLE where recorded)
  C  k_included_in_object == len(inputs.trials)
  D  k_included_in_object == prisma_flow.included.in_this_object == len(...included.nct)
  E  k_included_in_object <= k3_experimental

ABSENT IS NOT FAIL. A missing stage is NOT_ASSESSABLE and is reported as its own state, under
the law this repo runs on: an instrument that could not read must not report a negative reading.
A topic with no k_cascade at all is NO_CASCADE -- a third state again, because 132 of 135 topics
are in it and folding them into "clean" is the corpus-scale version of this same error.
"""
import io
import json
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SSOT = os.path.join(REPO, "ssot")

FAIL, NA, OK = "FAIL", "NOT_ASSESSABLE", "OK"


def _int(d, key):
    v = d.get(key)
    return v if isinstance(v, int) and not isinstance(v, bool) else None


def check(obj):
    """-> (state, [(check_id, verdict, detail)]). Every limb reported, never the first only."""
    kc = obj.get("k_cascade")
    if not isinstance(kc, dict):
        return "NO_CASCADE", []

    k0 = _int(kc, "k0_surfaced")
    k2 = _int(kc, "k2_role_located")
    k3 = _int(kc, "k3_experimental")
    k4 = _int(kc, "k4_comparator")
    k5 = _int(kc, "k5_background")
    na = _int(kc, "kNA_not_assessable")
    unr = _int(kc, "kUNREACHABLE")
    inc = _int(kc, "k_included_in_object")
    n_trials = len(((obj.get("inputs") or {}).get("trials") or []))
    pf_inc = ((obj.get("prisma_flow") or {}).get("included") or {})

    rows = []

    # A -- the stage named "located" must not count the unlocatable.
    if None in (k2, k3, k4, k5):
        rows.append(("A_k2_is_the_located_sum", NA,
                     "one of k2/k3/k4/k5 is absent or non-integer; absent input is not a "
                     "wrong value"))
    elif k2 != k3 + k4 + k5:
        rows.append(("A_k2_is_the_located_sum", FAIL,
                     "k2_role_located=%d but k3+k4+k5=%d (delta %+d). kNA=%s. The stage named "
                     "'role located' is counting records whose role could not be located."
                     % (k2, k3 + k4 + k5, k2 - (k3 + k4 + k5), na)))
    else:
        rows.append(("A_k2_is_the_located_sum", OK, "k2=%d == k3+k4+k5" % k2))

    # B -- the surfaced set is exhausted by the stages, with nothing dropped and nothing double
    #      counted. kUNREACHABLE is included when recorded because a record never read is a
    #      fourth state, not an absence.
    if None in (k0, k3, k4, k5, na):
        rows.append(("B_k0_is_exhausted", NA, "k0 or a stage is absent or non-integer"))
    else:
        total = k3 + k4 + k5 + na + (unr or 0)
        if k0 != total:
            rows.append(("B_k0_is_exhausted", FAIL,
                         "k0_surfaced=%d but k3+k4+k5+kNA%s=%d (delta %+d)"
                         % (k0, "+kUNREACHABLE" if unr else "", total, k0 - total)))
        else:
            rows.append(("B_k0_is_exhausted", OK, "k0=%d == k3+k4+k5+kNA%s"
                         % (k0, "+kUNREACHABLE" if unr else "")))

    # C -- the object's own included count against the trials it actually holds.
    if inc is None:
        rows.append(("C_included_matches_inputs", NA, "k_included_in_object absent"))
    elif not n_trials:
        rows.append(("C_included_matches_inputs", NA, "inputs.trials absent or empty"))
    elif inc != n_trials:
        rows.append(("C_included_matches_inputs", FAIL,
                     "k_cascade.k_included_in_object=%d but inputs.trials holds %d. The "
                     "cascade and the object disagree about how many trials this review "
                     "includes." % (inc, n_trials)))
    else:
        rows.append(("C_included_matches_inputs", OK, "k_included=%d == len(inputs.trials)" % inc))

    # D -- and against the PRISMA flow, which is the reader-facing statement of the same fact.
    pf_n = pf_inc.get("in_this_object")
    pf_list = pf_inc.get("nct")
    if not isinstance(pf_n, int) and not isinstance(pf_list, list):
        rows.append(("D_prisma_matches_included", NA, "prisma_flow.included absent"))
    else:
        parts, bad = [], False
        if isinstance(pf_n, int):
            parts.append("prisma.in_this_object=%d" % pf_n)
            if inc is not None and pf_n != inc:
                bad = True
            if n_trials and pf_n != n_trials:
                bad = True
        if isinstance(pf_list, list):
            parts.append("len(prisma.nct)=%d" % len(pf_list))
            if n_trials and len(pf_list) != n_trials:
                bad = True
        parts.append("len(inputs.trials)=%d" % n_trials)
        rows.append(("D_prisma_matches_included", FAIL if bad else OK,
                     ("PRISMA disagrees with the object: " if bad else "") + ", ".join(parts)))

    # E -- a review cannot include more trials than the cascade says carry the intervention.
    if inc is None or k3 is None:
        rows.append(("E_included_within_experimental", NA, "k_included or k3 absent"))
    elif inc > k3:
        rows.append(("E_included_within_experimental", FAIL,
                     "k_included_in_object=%d exceeds k3_experimental=%d" % (inc, k3)))
    else:
        rows.append(("E_included_within_experimental", OK, "%d <= %d" % (inc, k3)))

    return "CHECKED", rows


def main():
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    only = sys.argv[1] if len(sys.argv) > 1 else None
    scanned = no_cascade = 0
    failing = {}
    na_rows = 0
    for d in sorted(os.listdir(SSOT)):
        if only and d != only:
            continue
        p = os.path.join(SSOT, d, d + ".json")
        if not os.path.exists(p):
            continue
        try:
            with io.open(p, encoding="utf-8") as fh:
                obj = json.load(fh)
        except (ValueError, OSError) as exc:
            print("%s  UNREADABLE: %s -- NOT_ASSESSABLE, not a failure" % (d, exc))
            continue
        scanned += 1
        state, rows = check(obj)
        if state == "NO_CASCADE":
            no_cascade += 1
            continue
        bad = [r for r in rows if r[1] == FAIL]
        na_rows += sum(1 for r in rows if r[1] == NA)
        if bad:
            failing[d] = bad
            print(d)
            for cid, verdict, detail in rows:
                if verdict == OK:
                    continue
                print("   %-28s %-15s %s" % (cid, verdict, detail))
            print()

    print("topic objects scanned            %d" % scanned)
    print("carrying no k_cascade at all     %d   <- NO_CASCADE, a state, not a pass" % no_cascade)
    print("limbs that could not be assessed %d   <- NOT_ASSESSABLE, never counted as FAIL"
          % na_rows)
    print("objects whose cascade contradicts itself  %d" % len(failing))
    if failing:
        print()
        print("REFUSED. A cascade is the one place k is supposed to be inspectable at every")
        print("stage. A stage that does not reconcile with the stages beside it is a number")
        print("that cannot be checked by the reader it was written for.")
        return 1
    print()
    print("every cascade present reconciles with itself.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
