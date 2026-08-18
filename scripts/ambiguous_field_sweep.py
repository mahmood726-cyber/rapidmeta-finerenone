"""Sweep for fields whose NAME maps to more than one standard definition.

THE CLASS, named after the ARNI I-squared finding: an ambiguous label on an unambiguous
number. Every value can be correct and the object still defective, because a reader who
recomputes the quantity from the definition the name implies will conclude we are wrong --
and that reader is behaving exactly as we want readers to behave. IT IS SPECIFICALLY A
DEFECT AGAINST THE ONLY READER WE CLAIM TO SERVE.

Measured, not assumed: `alirocumab-lipid` carries Higgins (Q-df)/Q = 87.9 and `arni-hfref`
carries the metafor/REML tau2/(tau2+s2) = 32.89, both in a field named `i2`, on the same
corpus, in opposite directions.

THREE QUESTIONS, because the estimator finding changed the shape of this sweep:

  1. WHICH OBJECTS DECLARE AN ESTIMATOR AND WHICH DO NOT. Proved load-bearing: ignoring
     three objects' declared DerSimonian-Laird produced a false accusation against four
     named live pages. An object carrying a random-effects pool and NO declared estimator
     cannot be re-derived by anyone, including us.
  2. WHICH I-SQUARED DEFINITION EACH CARRIES. Decided by recomputing both from the object's
     own per-trial inputs and seeing which one the stored value matches.
  3. WHICH OTHER FIELD NAMES ARE AMBIGUOUS -- tau2 estimator, interval method, "response
     rate", and anything else a recomputation would need to know and cannot infer.

THIS REPORTS. It changes nothing. The fix belongs in the projector so it cannot drift, and
under `display_change_announced` because the meaning is being made explicit even though no
value moves.
"""
from __future__ import annotations
import io
import json
import math
import os
import sys

if __name__ == "__main__":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
Z = 1.959963985
RATIO = {"HR", "RR", "OR", "IRR", "RATE_RATIO", "RISK_RATIO", "ODDS_RATIO",
         "HAZARD_RATIO"}

# name -> the competing standard definitions a reader could reasonably assume
AMBIGUOUS = {
    "i2": "Higgins (Q-df)/Q  OR  metafor/REML tau2/(tau2+s2)",
    "i_squared": "Higgins (Q-df)/Q  OR  metafor/REML tau2/(tau2+s2)",
    "tau2": "DerSimonian-Laird  OR  REML  OR  Paule-Mandel  OR  Empirical Bayes",
    "ci_low": "normal-theory z  OR  Hartung-Knapp t  OR  profile-likelihood",
    "ci_high": "normal-theory z  OR  Hartung-Knapp t  OR  profile-likelihood",
    "response_rate": "responders/randomised  OR  responders/evaluable  OR  best overall",
    "cure_rate": "test-of-cure  OR  end-of-treatment  OR  clinical vs microbiological",
    "prediction_interval": "t_{k-1} (Handbook 6.5)  OR  t_{k-2} (IntHout 2016)",
}


def both_i2(blk, measure):
    """Recompute Higgins and metafor I2 from the object's own per-trial inputs."""
    pt = blk.get("per_trial") or []
    log = (measure or "").upper() in RATIO
    v = []
    for t in pt:
        p, lo, hi = t.get("point"), t.get("ci_low"), t.get("ci_high")
        ls = t.get("log_se") or t.get("se") or t.get("se_log_rr")
        if ls:
            v.append(ls * ls)
        elif None not in (p, lo, hi):
            if log and min(p, lo, hi) > 0:
                v.append(((math.log(hi) - math.log(lo)) / (2 * Z)) ** 2)
            elif not log:
                v.append(((hi - lo) / (2 * Z)) ** 2)
            else:
                return None
        else:
            return None
    k = len(v)
    het = blk.get("heterogeneity") or {}
    q, t2 = het.get("q"), het.get("tau2")
    if k < 2 or q in (None, 0) or t2 is None:
        return None
    W = [1 / x for x in v]
    SW = sum(W)
    SW2 = sum(x * x for x in W)
    denom = SW * SW - SW2
    if denom <= 0:
        return None
    s2 = (k - 1) * SW / denom
    return ((q - (k - 1)) / q * 100, t2 / (t2 + s2) * 100 if (t2 + s2) else 0.0)


def main() -> int:
    ss = os.path.join(REPO, "ssot")
    no_est, est_kinds, i2_kind, amb = [], {}, {"higgins": [], "metafor": [],
                                               "neither": [], "undecidable": []}, {}
    pooled_n = 0
    for d in sorted(os.listdir(ss)):
        f = os.path.join(ss, d, d + ".json")
        if not os.path.exists(f):
            continue
        try:
            o = json.load(io.open(f, encoding="utf-8"))
        except Exception:
            continue
        for name, blk in ((o.get("results") or {}).get("by_outcome") or {}).items():
            if not isinstance(blk, dict):
                continue
            pl = blk.get("pooled") or {}
            if pl.get("point") is None:
                continue
            pooled_n += 1
            est = blk.get("estimator") or blk.get("estimator_used")
            if not est:
                no_est.append("%s :: %s" % (d, name))
            else:
                key = ("DL" if "dersimonian" in str(est).lower()
                       else "REML" if "reml" in str(est).lower() else str(est)[:26])
                est_kinds[key] = est_kinds.get(key, 0) + 1
            het = blk.get("heterogeneity") or {}
            stored = het.get("i2") or het.get("i2_percent")
            if stored is not None:
                got = both_i2(blk, pl.get("measure") or blk.get("measure"))
                if not got:
                    i2_kind["undecidable"].append("%s :: %s" % (d, name))
                else:
                    hg, mf = got
                    # AT I2 = 0 THE TWO DEFINITIONS ARE INDISTINGUISHABLE. Where Q < df,
                    # Higgins is negative and clamped to 0 while metafor is exactly 0, so
                    # both match a stored 0.00 and the object CANNOT be classified. The
                    # first version of this sweep assigned all six such objects to
                    # "metafor" and would have reported a 10-7 split where the real,
                    # decidable split is 10-1.
                    if abs(stored) < 0.05 and abs(hg - mf) < 0.05 or stored == 0.0:
                        i2_kind["undecidable"].append(
                            "%s (i2=0, Q=%.4f < df -- both definitions give 0)"
                            % (d, (blk.get("heterogeneity") or {}).get("q") or 0))
                    elif abs(stored - hg) < 0.05:
                        i2_kind["higgins"].append("%s (%.2f)" % (d, stored))
                    elif abs(stored - mf) < 0.05:
                        i2_kind["metafor"].append("%s (%.2f)" % (d, stored))
                    else:
                        i2_kind["neither"].append(
                            "%s stored=%.2f higgins=%.2f metafor=%.2f"
                            % (d, stored, hg, mf))
            for fld in list(blk.keys()) + list(het.keys()) + list(pl.keys()):
                if fld in AMBIGUOUS:
                    amb.setdefault(fld, set()).add(d)

    print("outcome blocks carrying a pooled point: %d" % pooled_n)
    print()
    print("=== 1. ESTIMATOR DECLARED?")
    for k, n in sorted(est_kinds.items(), key=lambda x: -x[1]):
        print("    declared %-26s %d" % (k, n))
    print("    NOT DECLARED                %d" % len(no_est))
    for x in no_est[:14]:
        print("        %s" % x[:76])
    print()
    print("=== 2. WHICH I-SQUARED DEFINITION")
    for k in ["higgins", "metafor", "neither", "undecidable"]:
        rows = i2_kind[k]
        print("    %-12s %d" % (k, len(rows)))
        for x in rows[:8]:
            print("        %s" % x[:76])
    print()
    print("=== 3. AMBIGUOUS FIELD NAMES PRESENT IN THE CORPUS")
    for fld, topics in sorted(amb.items(), key=lambda x: -len(x[1])):
        print("    %-22s %3d objects   competing: %s" % (fld, len(topics), AMBIGUOUS[fld]))
    print()
    print("NOTHING HAS BEEN CHANGED. The fix belongs in the projector, under "
          "display_change_announced, because the meaning is made explicit while no value "
          "moves.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
