r"""Which of the corrected pools are arithmetically right but still questionable?

WHY THIS EXISTS
    Correcting tau2 makes a pool's numbers right. It does not make the pool
    a good idea. ATEZOLIZUMAB_BLADDER is two trials pointing opposite ways,
    one holding 97.9% of the precision; the correction makes it MORE honest
    and MORE obviously questionable at once. The store already refuses 142 of
    its own outcomes on grounds of exactly that kind.

    So the swap carries a named state per file, and the questionable class is
    COUNTABLE. Nothing is withheld on my judgement -- that is the store's call
    and Mahmood's -- but nobody should read 232 corrected files as 232
    answered questions.

STATES
    CORRECTED_AND_SOUND              the estimator was wrong; the pool is fine
    CORRECTED_BUT_POOL_QUESTIONABLE  arithmetically right; whether these
                                     trials should be pooled at all is
                                     UNSETTLED and is not decided here

THE CRITERIA, STATED BEFORE USE
    A pool is QUESTIONABLE if ANY of the following holds. Each is a property
    of the evidence, not of the estimator, so none of them is created by the
    correction -- the correction only makes them visible.

      A  DIRECTIONAL DISAGREEMENT WITH A DOMINANT TRIAL
         the trial effects span both signs AND one trial holds >= 80% of the
         fixed-effect weight. Then that single trial's sign IS the pooled
         sign, and the pool is reporting one trial wearing the authority of
         several.

      B  TWO TRIALS DISAGREEING
         k == 2 and the two effects have opposite signs. A pool of two that
         cannot agree on direction has no majority to appeal to.

      C  HETEROGENEITY DOMINATES THE EVIDENCE
         corrected tau2 >= 10x the median within-trial variance. The
         between-study variance then swamps the within-study information,
         which is the condition under which a pooled point estimate carries
         least meaning.

    The thresholds 80%, and 10x, are choices. The distributions they were
    chosen against are printed by --distribution, so the choice can be
    audited rather than taken on trust.
"""
from __future__ import annotations
import argparse
import glob
import json
import math
import os
import statistics
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)

from build_binary_sidecar import reml_tau2  # noqa: E402

SERVED = os.path.join(ROOT, "outputs", "r_validation")
DOM_SHARE = 0.80
TAU_OVER_V = 10.0


def cells(d):
    return sorted((str(t.get("nct") or t.get("name")), t.get("tE"), t.get("tN"),
                   t.get("cE"), t.get("cN")) for t in (d.get("trials") or []))


def swap_set(new_dir):
    """The cell-identical files: trials byte-identical between served and new."""
    out = []
    for p in sorted(glob.glob(os.path.join(new_dir, "*.json"))):
        stem = os.path.basename(p)[:-5]
        sp = os.path.join(SERVED, stem + ".json")
        if os.path.exists(sp) is False:
            continue
        try:
            s = json.load(open(sp, encoding="utf-8"))
            n = json.load(open(p, encoding="utf-8"))
        except Exception:
            continue
        if cells(s) == cells(n):
            out.append((stem, s, n, p))
    return out


def features(n):
    """The measurable properties the criteria are built from."""
    rows = [t for t in (n.get("trials") or [])
            if isinstance(t.get("yi"), (int, float))
            and isinstance(t.get("vi"), (int, float)) and t["vi"] > 0]
    if len(rows) < 2:
        return None
    ys = [t["yi"] for t in rows]
    vs = [t["vi"] for t in rows]
    wf = [1.0 / v for v in vs]
    swf = sum(wf)
    return {
        "k": len(ys),
        "max_share": max(wf) / swf,
        "both_signs": (min(ys) < 0 < max(ys)),
        "tau2": n.get("tau2") if isinstance(n.get("tau2"), (int, float))
        else reml_tau2(ys, vs),
        "median_v": statistics.median(vs),
    }


def classify(f):
    reasons = []
    if f["both_signs"] and f["max_share"] >= DOM_SHARE:
        reasons.append("A: trials disagree in direction and one holds %.1f%% "
                       "of the fixed-effect weight" % (100 * f["max_share"]))
    if f["k"] == 2 and f["both_signs"]:
        reasons.append("B: a pool of two whose trials point opposite ways")
    if f["median_v"] > 0 and f["tau2"] >= TAU_OVER_V * f["median_v"]:
        reasons.append("C: tau2 %.4g is %.0fx the median within-trial variance "
                       "%.4g" % (f["tau2"], f["tau2"] / f["median_v"],
                                 f["median_v"]))
    return reasons


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--new-dir", required=True)
    ap.add_argument("--distribution", action="store_true")
    ap.add_argument("--json-out", default=None)
    a = ap.parse_args()
    new_dir = a.new_dir if os.path.isabs(a.new_dir) else os.path.join(ROOT, a.new_dir)

    items = swap_set(new_dir)
    feats = []
    for stem, s, n, p in items:
        f = features(n)
        if f:
            feats.append((stem, f, p))

    if a.distribution:
        shares = sorted(f["max_share"] for _, f, _ in feats)
        ratios = sorted((f["tau2"] / f["median_v"]) if f["median_v"] else 0.0
                        for _, f, _ in feats)
        ks = sorted(f["k"] for _, f, _ in feats)
        both = sum(1 for _, f, _ in feats if f["both_signs"])
        print("DISTRIBUTIONS ACROSS THE %d CELL-IDENTICAL FILES" % len(feats))
        print("  these are printed BEFORE any threshold is applied, so the")
        print("  thresholds can be audited against them")
        print("")
        def pct(v, q):
            return v[min(len(v) - 1, int(q * len(v)))]
        print("  largest fixed-effect weight share:")
        print("    min %.3f  median %.3f  75th %.3f  90th %.3f  max %.3f"
              % (shares[0], pct(shares, .5), pct(shares, .75),
                 pct(shares, .90), shares[-1]))
        print("    at or above 0.80: %d files" % sum(1 for s in shares if s >= .80))
        print("")
        print("  tau2 / median within-trial variance:")
        print("    min %.3g  median %.3g  75th %.3g  90th %.3g  max %.3g"
              % (ratios[0], pct(ratios, .5), pct(ratios, .75),
                 pct(ratios, .90), ratios[-1]))
        print("    at or above 10x: %d files" % sum(1 for r in ratios if r >= 10))
        print("")
        print("  k: min %d median %d max %d ; k==2 in %d files"
              % (ks[0], pct(ks, .5), ks[-1], sum(1 for k in ks if k == 2)))
        print("  trials spanning both signs: %d files" % both)
        print("")

    sound, quest = [], []
    for stem, f, p in feats:
        r = classify(f)
        (quest if r else sound).append((stem, f, r))

    print("SWAP SET CLASSIFIED")
    print("  CORRECTED_AND_SOUND              %d" % len(sound))
    print("  CORRECTED_BUT_POOL_QUESTIONABLE  %d" % len(quest))
    print("  identity: %d + %d == %d : %s"
          % (len(sound), len(quest), len(feats),
             "HOLDS" if len(sound) + len(quest) == len(feats) else "FAILS"))
    print("")
    quest.sort(key=lambda x: (-len(x[2]), -x[1]["max_share"]))
    print("  THE QUESTIONABLE ONES, worst first (most criteria, then most")
    print("  dominated). Arithmetically correct; whether they should be")
    print("  pooled is NOT decided here.")
    for stem, f, r in quest[:15]:
        print("    %-40s k=%d  top weight %.1f%%" % (stem[:40], f["k"],
                                                     100 * f["max_share"]))
        for line in r:
            print("        %s" % line)
    if len(quest) > 15:
        print("    ... and %d more, all in the JSON output" % (len(quest) - 15))
    if a.json_out:
        json.dump([{"sidecar": s, "state": "CORRECTED_BUT_POOL_QUESTIONABLE"
                    if r else "CORRECTED_AND_SOUND", "reasons": r,
                    "k": f["k"], "max_weight_share": f["max_share"],
                    "tau2": f["tau2"], "median_within_trial_variance":
                    f["median_v"]}
                   for s, f, r in sound + quest],
                  open(a.json_out, "w", encoding="utf-8"), indent=1)
        print("\nwrote %s" % a.json_out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
