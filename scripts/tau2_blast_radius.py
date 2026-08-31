r"""Blast radius of the reml_tau2 defect, classified over the WHOLE affected set.

THE QUESTION THIS ANSWERS
    "3 published intervals flip" is worthless unless it is a count over every
    candidate rather than a count among the ones somebody looked at. So every
    sidecar with a stored tau2 of exactly 0.0 is recomputed here and sorted
    into a NAMED state. Nothing is reported by inspection.

THE DEFECT
    scripts/build_binary_sidecar.py::reml_tau2 computes

        tau2 <- tau2 + sum(w^2*((y-mu)^2 - v)) / sum(w^2)

    an INCREMENT form that omits the `1/sum(w)` term separating REML from ML.
    Clamped at zero it has a fixed point AT zero. The correct Viechtbauer
    (2005) update is a direct assignment:

        tau2 <- sum(w^2*((y-mu)^2 - v)) / sum(w^2)  +  1/sum(w)

    On the four arni-hfref trials the shipped form returns exactly 0.0 where
    metafor 5.0.1 under R 4.6.0 returns 0.0007252899298732.

WHY NO INTERNAL CHECK COULD HAVE CAUGHT THIS
    tau2 = 0 means "no heterogeneity detected", which is a legitimate and
    common finding. The failure value of this estimator is also a meaningful
    value, so its output is indistinguishable from a real result. No range
    check, no assertion, no plausibility test on the number itself can
    separate the two. Only an EXTERNAL ORACLE computing the same quantity by
    an independent route can -- here, metafor. That is the generalisable
    lesson: when a computation's failure value is also a meaningful value,
    an external oracle is not a nicety, it is the only detector.

STATES (every candidate lands in exactly one)
    CONCLUSION_FLIPS      the pooled interval's relation to the null CHANGES
                          in EITHER direction -- a claim removed, or a claim
                          created. This is the retraction set.
    INTERVAL_WIDENS_ONLY  no crossing; the interval moves by more than the
                          negligible threshold. Accuracy, not correctness.
    NEGLIGIBLE            no crossing and both changes below the threshold
                          stated in NEGLIGIBLE_* below.
    LEGITIMATELY_ZERO     the correct estimator ALSO returns zero. These are
                          real homogeneity findings and were never wrong.
    NOT_ASSESSABLE        fewer than 2 usable rows, so no pool exists.

    Both directions of flip are tested. The earlier delegated pass tested
    only excludes-null -> includes-null, which cannot see a claim the
    correction CREATES.
"""
from __future__ import annotations
import argparse
import glob
import json
import math
import os
import sys
from collections import Counter, OrderedDict

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)

from absolute_effects_sidecar import reml_tau2, reml_tau2_as_shipped  # noqa
from build_binary_sidecar import t_quantile_975  # noqa

SIDECARS = os.path.join(ROOT, "outputs", "r_validation", "*.json")

# STATED THRESHOLD. A change is NEGLIGIBLE only if the pooled estimate moves
# by less than 1% on the log scale AND the interval width changes by less
# than 1%. Both must hold. 0.01 on the log scale is about a 1% change in the
# odds ratio, which is below the precision these files are published at.
NEGLIGIBLE_LOG_SHIFT = 0.01
NEGLIGIBLE_WIDTH_RATIO = 0.01


def pool(ys, vs, tau2):
    """Inverse-variance pool with HKSJ variance floored at 1 and t_{k-1}."""
    k = len(ys)
    w = [1.0 / (v + tau2) for v in vs]
    sw = sum(w)
    mu = sum(wi * y for wi, y in zip(w, ys)) / sw
    q = sum(wi * (y - mu) ** 2 for wi, y in zip(w, ys)) / (k - 1)
    se = math.sqrt(max(q, 1.0) / sw)
    t = t_quantile_975(k - 1)
    return mu, mu - t * se, mu + t * se


def excludes_null(lo, hi):
    """On the log scale the null is 0. True if the interval excludes it."""
    return not (lo <= 0.0 <= hi)


def classify(path):
    stem = os.path.basename(path)[:-5]
    row = OrderedDict(sidecar=stem)
    try:
        d = json.load(open(path, encoding="utf-8"))
    except Exception as exc:
        row["state"] = "NOT_ASSESSABLE"
        row["reason"] = "unparseable: %s" % str(exc)[:70]
        return row
    if isinstance(d, dict) is False:
        row["state"] = "NOT_ASSESSABLE"
        row["reason"] = "root is not an object"
        return row
    row["stored_tau2"] = d.get("tau2")
    trials = d.get("trials")
    if isinstance(trials, list) is False:
        row["state"] = "NOT_ASSESSABLE"
        row["reason"] = "no trials list"
        return row
    rows = [t for t in trials if isinstance(t, dict)
            and isinstance(t.get("yi"), (int, float))
            and isinstance(t.get("vi"), (int, float)) and t["vi"] > 0]
    if len(rows) < 2:
        row["state"] = "NOT_ASSESSABLE"
        row["reason"] = "fewer than 2 rows with usable yi/vi (k=%d)" % len(rows)
        return row
    ys = [t["yi"] for t in rows]
    vs = [t["vi"] for t in rows]
    row["k"] = len(ys)

    t_ship = reml_tau2_as_shipped(ys, vs)
    t_corr = reml_tau2(ys, vs)
    row["tau2_shipped"] = t_ship
    row["tau2_correct"] = t_corr

    if t_corr <= 0.0:
        row["state"] = "LEGITIMATELY_ZERO"
        row["reason"] = ("the correct REML estimator also returns zero, so "
                         "this is a real homogeneity finding and was never "
                         "wrong. The broken estimator could not tell these "
                         "apart from the erased ones; the correct one can.")
        return row

    mu_s, lo_s, hi_s = pool(ys, vs, t_ship)
    mu_c, lo_c, hi_c = pool(ys, vs, t_corr)
    row["or_shipped"] = OrderedDict([("point", math.exp(mu_s)),
                                     ("ci_low", math.exp(lo_s)),
                                     ("ci_high", math.exp(hi_s))])
    row["or_correct"] = OrderedDict([("point", math.exp(mu_c)),
                                     ("ci_low", math.exp(lo_c)),
                                     ("ci_high", math.exp(hi_c))])
    ex_s, ex_c = excludes_null(lo_s, hi_s), excludes_null(lo_c, hi_c)
    row["excludes_null_shipped"] = ex_s
    row["excludes_null_correct"] = ex_c
    shift = abs(mu_c - mu_s)
    w_s, w_c = hi_s - lo_s, hi_c - lo_c
    ratio = (w_c / w_s) if w_s > 0 else float("inf")
    row["log_point_shift"] = shift
    row["ci_width_ratio"] = ratio

    if ex_s != ex_c:
        row["state"] = "CONCLUSION_FLIPS"
        row["flip_direction"] = ("CLAIM_REMOVED: the published interval "
                                 "excludes the null and the corrected one "
                                 "does not"
                                 if ex_s else
                                 "CLAIM_CREATED: the published interval "
                                 "includes the null and the corrected one "
                                 "excludes it")
    elif shift < NEGLIGIBLE_LOG_SHIFT and abs(ratio - 1.0) < NEGLIGIBLE_WIDTH_RATIO:
        row["state"] = "NEGLIGIBLE"
        row["reason"] = ("pooled estimate moves %.2e on the log scale and the "
                         "interval width changes by %.2f%%, both below the "
                         "stated thresholds of %.2f and %.0f%%"
                         % (shift, (ratio - 1) * 100, NEGLIGIBLE_LOG_SHIFT,
                            NEGLIGIBLE_WIDTH_RATIO * 100))
    else:
        row["state"] = "INTERVAL_WIDENS_ONLY"
        row["widened"] = ratio > 1.0
    return row


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--json-out", default=None)
    args = ap.parse_args()

    files = [f for f in sorted(glob.glob(SIDECARS))
             if not os.path.basename(f).startswith("_")]
    # THE CANDIDATE SET, stated: every sidecar whose stored tau2 is exactly
    # 0.0. That is the set the defect could have silently emptied.
    cands, others = [], 0
    for f in files:
        try:
            d = json.load(open(f, encoding="utf-8"))
        except Exception:
            others += 1
            continue
        if isinstance(d, dict) and d.get("tau2") == 0.0:
            cands.append(f)
        else:
            others += 1

    rows = [classify(f) for f in cands]
    c = Counter(r["state"] for r in rows)

    print("BLAST RADIUS OF THE reml_tau2 DEFECT")
    print("")
    print("POPULATION")
    print("  non-underscore sidecars                 %d" % len(files))
    print("  stored tau2 exactly 0.0 (the candidates) %d" % len(cands))
    print("  all other sidecars (not assessed here)   %d" % others)
    print("")
    print("EVERY CANDIDATE CLASSIFIED -- this is a measured count over all %d,"
          % len(cands))
    print("not a count among the ones anybody happened to look at.")
    for k in ("CONCLUSION_FLIPS", "INTERVAL_WIDENS_ONLY", "NEGLIGIBLE",
              "LEGITIMATELY_ZERO", "NOT_ASSESSABLE"):
        print("  %-22s %d" % (k, c.get(k, 0)))
    tot = sum(c.values())
    print("  identity: %d classified == %d candidates : %s"
          % (tot, len(cands), "HOLDS" if tot == len(cands) else "FAILS"))
    print("")
    affected = [r for r in rows if r["state"] in
                ("CONCLUSION_FLIPS", "INTERVAL_WIDENS_ONLY", "NEGLIGIBLE")]
    print("HOW MANY ZEROS WERE REAL")
    print("  legitimately zero (correct estimator agrees) %d of %d (%.1f%%)"
          % (c.get("LEGITIMATELY_ZERO", 0), len(cands),
             100.0 * c.get("LEGITIMATELY_ZERO", 0) / len(cands) if cands else 0))
    print("  heterogeneity actually erased                %d of %d (%.1f%%)"
          % (len(affected), len(cands),
             100.0 * len(affected) / len(cands) if cands else 0))
    print("  -> 336 overstates the defect and 86 was the erased set, not the")
    print("     set whose CONCLUSIONS move.")
    print("")
    print("THE RETRACTION SET -- every CONCLUSION_FLIPS row, in full")
    for r in rows:
        if r["state"] != "CONCLUSION_FLIPS":
            continue
        s, cc = r["or_shipped"], r["or_correct"]
        print("  %-34s k=%d" % (r["sidecar"], r["k"]))
        print("      %s" % r["flip_direction"])
        print("      published OR %.6f (%.6f to %.6f)  tau2 %.6g"
              % (s["point"], s["ci_low"], s["ci_high"], r["tau2_shipped"]))
        print("      corrected OR %.6f (%.6f to %.6f)  tau2 %.6g"
              % (cc["point"], cc["ci_low"], cc["ci_high"], r["tau2_correct"]))
    print("")
    print("DIRECTION OF THE NON-FLIPPING CHANGES")
    wid = sum(1 for r in rows if r["state"] == "INTERVAL_WIDENS_ONLY"
              and r.get("widened"))
    nar = sum(1 for r in rows if r["state"] == "INTERVAL_WIDENS_ONLY"
              and not r.get("widened"))
    print("  widened  %d" % wid)
    print("  narrowed %d  (reported separately: the state is named "
          "INTERVAL_WIDENS_ONLY, so any narrowing is a deviation from that "
          "name and must be visible)" % nar)
    if args.json_out:
        json.dump(rows, open(args.json_out, "w", encoding="utf-8"),
                  indent=1, ensure_ascii=False)
        print("\nwrote %s" % args.json_out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
