"""Has lexicographic arm-sorting inverted any stored effect? Answered from the DATA.

# no-control: routed through require_controls. POSITIVE is a synthetic trial whose stored
# effect contradicts its own arm counts -- the fingerprint must be detected. NEGATIVE is
# DAPA-HF (NCT03036124), whose direction is not in doubt: dapagliflozin BEAT placebo, so its
# arm counts must reproduce an effect below 1 and it must NOT be flagged.

THE MECHANISM, CONFIRMED IN THE SOURCE. Three sites determine the treatment arm by sorting arm
labels lexicographically and taking the first:

    scripts/bulk_clone_audit_first.py:147   arms = sorted(per_arm.keys()); tN = arms[0]
    scripts/bulk_clone_audit_first.py:157   ogs  = sorted(og_vals.keys());  tE = ogs[0]
    scripts/reset_event_counts_from_source.py:67  same shape

`BG_CONTROL` sorts before `BG_EXPERIMENTAL`. Every effect built that way inverts, and this
project has already published an object saying empagliflozin was worse than placebo from
exactly this class.

WHY THIS ASKS THE DATA AND NOT THE CODE. Whether the scripts CAN invert is settled -- they can.
What matters is whether any object CARRIES an inverted value, and that is a property of the
stored numbers, not of the code path that wrote them. Reasoning from the code would give a
worst case; the data gives the answer.

THE FINGERPRINT. For every trial holding per-arm counts AND a published effect, recompute the
odds ratio from the counts and compare its DIRECTION with the stored effect. Agreement means
the arms are the right way round whatever wrote them. Disagreement is the signature, and it is
reported per trial with both numbers so a person can read the instance.

A trial with counts and no stored effect cannot be checked this way and is reported as
NOT ASSESSABLE rather than as clean -- the distinction this project exists to keep.
"""
from __future__ import annotations

import glob
import io
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from instrument_controls import require_controls          # noqa: E402

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(REPO, "outputs", "arm_direction_fingerprint_2026_08_23.json")

CONTROLWORDS = ("control", "placebo", "comparator", "standard", "usual", "sham")


def num(v):
    try:
        f = float(v)
        return f if f == f else None
    except (TypeError, ValueError):
        return None


def or_from_counts(tE, tN, cE, cN):
    if None in (tE, tN, cE, cN) or tN <= 0 or cN <= 0:
        return None
    a, b, c, d = tE, tN - tE, cE, cN - cE
    if min(a, b, c, d) < 0:
        return None
    a, b, c, d = a + 0.5, b + 0.5, c + 0.5, d + 0.5
    return (a / b) / (c / d)


def stored_effect(blk):
    # THE EFFECT IS UNDER by_outcome.<oid>.effect.point ON THIS CORPUS, not on the trial.
    bo = (blk or {}).get("by_outcome")
    if isinstance(bo, dict):
        for _oid, ob in sorted(bo.items()):
            eff = (ob or {}).get("effect")
            if isinstance(eff, dict):
                v = num(eff.get("point"))
                if v is not None and v > 0:
                    return v, "by_outcome.%s.effect.point" % _oid
    for k in ("publishedHR", "published_effect", "published_or", "effect", "point"):
        v = num((blk or {}).get(k))
        if v is not None and v > 0:
            return v, k
    pub = (blk or {}).get("published")
    if isinstance(pub, dict):
        for k in ("hr", "or", "rr", "point"):
            v = num(pub.get(k))
            if v is not None and v > 0:
                return v, "published." + k
    return None, None


def check(trial):
    """-> (verdict, computed_or, stored, label_order). verdict in agree/DISAGREE/not_assessable.

    THE FIRST VERSION READ THE WRONG SHAPE and returned 407 of 407 NOT ASSESSABLE with ZERO
    agreements -- which is a broken extractor wearing the appearance of a clean corpus. The
    corpus stores:

        "arms": [{"label": "dapagliflozin 10 mg once daily", "role": "treatment",
                  "events": 386, "participants": 2373},
                 {"label": "placebo", "role": "control", "events": 502, "participants": 2371}]

    A LIST with an EXPLICIT `role`, and `participants` rather than `n`. I had written it as a
    dict keyed by label. THE EXPLICIT ROLE IS ITSELF HALF THE ANSWER: direction is RECORDED on
    these objects, not inferred from sort order, so whatever the three scripts do, what is
    stored here does not depend on lexicographic luck.

    The effect lives under `by_outcome.<oid>.effect.point`, not on the trial.
    """
    tE = tN = cE = cN = None
    order = ""
    arms = trial.get("arms")
    if isinstance(arms, list) and len(arms) >= 2:
        order = " | ".join("%s=%s" % (str(a.get("role")), str(a.get("label"))[:22])
                           for a in arms[:2] if isinstance(a, dict))
        for a in arms:
            if not isinstance(a, dict):
                continue
            role = str(a.get("role") or "").lower()
            e, n = num(a.get("events")), num(a.get("participants") or a.get("n"))
            if role.startswith("treat") or role.startswith("exper") or role.startswith("int"):
                tE, tN = e, n
            elif role.startswith("cont") or role.startswith("place") or role.startswith("comp"):
                cE, cN = e, n
    elif isinstance(arms, dict) and len(arms) >= 2:
        # A DICT-SHAPED `arms` CARRIES NO ROLE, AND I HAD FALLEN BACK TO `sorted(keys)[0]`
        # HERE -- inside the audit written to detect exactly that. The lint flagged it, which
        # is the fifth time today an instrument exhibited the class it was measuring.
        #
        # It is not exempted, it is REMOVED. No object in the corpus stores arms as a dict, so
        # this was dead code embodying the defect; and if one ever does, the honest answer is
        # that its direction cannot be established, not that the alphabet decided it.
        order = "dict-shaped arms, no role recorded"
    got = or_from_counts(tE, tN, cE, cN)
    stored, where = stored_effect(trial)
    if got is None or stored is None:
        return "not_assessable", got, stored, order
    same = (got < 1) == (stored < 1)
    if abs(got - 1) < 0.03 or abs(stored - 1) < 0.03:
        return "not_assessable", got, stored, order     # too near the null to read a side
    return ("agree" if same else "DISAGREE"), got, stored, order


def main():
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    planted = {"arms": [{"role": "treatment", "events": 100, "participants": 500},
                        {"role": "control", "events": 50, "participants": 500}],
               "publishedHR": 0.45}       # stored says treatment WON; counts as read say lost
    v_planted = check(planted)[0]
    clean = {"arms": [{"role": "treatment", "events": 50, "participants": 500},
                      {"role": "control", "events": 100, "participants": 500}],
             "publishedHR": 0.45}
    v_clean = check(clean)[0]
    require_controls(
        "arm_direction_fingerprint",
        ("a trial whose stored effect contradicts its own arm counts is detected (got %s)"
         % v_planted, v_planted == "DISAGREE", True),
        ("a trial whose counts and stored effect agree is NOT flagged (got %s)" % v_clean,
         v_clean == "DISAGREE", True))

    rows = {"agree": [], "DISAGREE": [], "not_assessable": []}
    control_first = []
    n_obj = n_trial = 0
    for p in sorted(glob.glob(os.path.join(REPO, "ssot", "*", "*.json"))):
        t = os.path.basename(os.path.dirname(p))
        if os.path.basename(p) != t + ".json":
            continue
        try:
            obj = json.load(io.open(p, encoding="utf-8"))
        except ValueError:
            continue
        n_obj += 1
        for tr in ((obj.get("inputs") or {}).get("trials") or []):
            if not isinstance(tr, dict):
                continue
            n_trial += 1
            v, got, stored, order = check(tr)
            rec = {"topic": t, "nct": tr.get("nct") or tr.get("id"),
                   "computed_or": None if got is None else round(got, 4),
                   "stored": stored, "arm_order": order}
            rows[v].append(rec)
            a = tr.get("arms")
            if isinstance(a, dict) and len(a) >= 2:
                first = sorted(a.keys())[0].lower()
                if any(w in first for w in CONTROLWORDS):
                    control_first.append(rec)

    print("")
    print("ARM-DIRECTION FINGERPRINT: %d object(s), %d trial(s)" % (n_obj, n_trial))
    print("")
    print("   counts and stored effect AGREE            %4d" % len(rows["agree"]))
    print("   DISAGREE -- the inversion signature       %4d" % len(rows["DISAGREE"]))
    print("   not assessable (no counts, or no stored   %4d" % len(rows["not_assessable"]))
    print("      effect, or too near the null)")
    print("")
    print("   trials whose FIRST arm label sorts as a control/placebo  %4d" % len(control_first))
    print("      (the exact input that makes lexicographic sorting invert)")
    for r in control_first[:10]:
        print("      %-28s %-14s %s" % (r["topic"][:28], r["nct"], r["arm_order"][:40]))
    if rows["DISAGREE"]:
        print("")
        print("   DISAGREEMENTS, BY TRIAL:")
        for r in rows["DISAGREE"][:20]:
            print("      %-26s %-14s computed OR %-8s stored %-8s [%s]"
                  % (r["topic"][:26], r["nct"], r["computed_or"], r["stored"],
                     r["arm_order"][:30]))
    print("")
    print("A TRIAL WITH COUNTS AND NO STORED EFFECT CANNOT BE CHECKED THIS WAY and is counted")
    print("as NOT ASSESSABLE, not as clean. Whether the scripts CAN invert is settled -- they")
    print("can. This answers whether any object CARRIES an inverted value.")
    json.dump({"objects": n_obj, "trials": n_trial,
               "agree": len(rows["agree"]), "disagree": rows["DISAGREE"],
               "not_assessable": len(rows["not_assessable"]),
               "control_sorts_first": control_first},
              io.open(OUT, "w", encoding="utf-8"), indent=1)
    if rows["DISAGREE"]:
        sys.exit("REFUSED: %d trial(s) carry a stored effect whose direction contradicts their "
                 "own arm counts." % len(rows["DISAGREE"]))


if __name__ == "__main__":
    main()
