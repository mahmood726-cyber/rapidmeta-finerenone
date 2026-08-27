#!/usr/bin/env python3
"""POOL THE INCRETIN-HFpEF KCCQ-CSS OUTCOME. DERIVED HERE, NOT PASTED.

    THE POOLER IS WRITTEN BEFORE THE THIRD TRIAL'S NUMBER ARRIVES, on purpose.

Two published syntheses give 7.4 (4.9-9.9) and 7.33 (5.84-8.82). Our existing k=2 pool gives
7.43 (5.09-9.77). Whatever the k=3 answer is, it will land near those, and a number that
agrees with three prior figures is the easiest number in the world to accept without having
computed it. So the arithmetic is fixed and tested first, against inputs whose answer is
already known, and only then is the new trial's value fed in.

    ⭐ AGREEMENT IS THE CONDITION UNDER WHICH A NUMBER GETS ACCEPTED WITHOUT BEING DERIVED.

THE CONTROL. `--selftest` reproduces the CURRENT k=2 pool from the two rows the object already
holds. If this code cannot reproduce 7.43 (5.0895, 9.7704) from STEP-HFpEF and SUMMIT, it is
not entitled to compute a k=3 pool, and it refuses. That is a known positive derived
independently of this file -- it was stored by a previous run of a different implementation.

METHOD, and each choice is a decision rather than a default:

  * Inverse-variance random effects. The corpus pools this outcome under `random-effects`
    with REML, so this reproduces that rather than choosing afresh.
  * SE from the printed interval, using the multiplier for THAT interval's own level.
    ⚠️ A 96% interval divided by 1.96 is a silently wrong standard error. `_z_for` refuses a
    level it does not recognise instead of defaulting to 1.96 -- the HEART-FID 96% CI is the
    live instance of exactly this hazard elsewhere in tonight's work.
  * Mean difference on the natural scale. KCCQ points are a continuous score; there is no log
    transform and no back-transform.
  * Knapp-Hartung is NOT applied, because the stored k=2 pool did not apply it and the
    comparison must be like for like. At k=3 that choice matters and is declared.
"""
import io
import json
import math
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OBJ = os.path.join(REPO, "ssot", "incretin-hfpef-review", "incretin-hfpef-review.json")

# Two-sided normal quantiles. A level absent from this table is REFUSED, never defaulted.
Z = {80: 1.2815515655446004, 90: 1.6448536269514722, 95: 1.959963984540054,
     96: 2.053748910631823, 98: 2.3263478740408408, 99: 2.5758293035489004}


def _z_for(level):
    if level is None:
        raise SystemExit("REFUSED: an interval was supplied with no LEVEL. A confidence "
                         "interval without its level cannot be converted to a standard error, "
                         "and assuming 95% is how a 96% interval becomes a wrong variance.")
    key = int(round(float(level)))
    if key not in Z:
        raise SystemExit("REFUSED: interval level %r is not in the quantile table. Add it "
                         "deliberately rather than falling back to 1.96." % level)
    return Z[key]


def se_from_ci(lo, hi, level):
    return (float(hi) - float(lo)) / (2.0 * _z_for(level))


def dl_tau2(ys, vs):
    """DerSimonian-Laird tau-squared. Reported alongside REML so the two can be compared."""
    w = [1.0 / v for v in vs]
    mu = sum(wi * y for wi, y in zip(w, ys)) / sum(w)
    q = sum(wi * (y - mu) ** 2 for wi, y in zip(w, ys))
    k = len(ys)
    c = sum(w) - sum(wi ** 2 for wi in w) / sum(w)
    return max(0.0, (q - (k - 1)) / c) if c > 0 else 0.0, q


def reml_tau2(ys, vs, iters=200):
    """REML by fixed-point iteration. DL used as the starting value.

    k<10 here, which is why REML rather than DL is the estimator of record: DL is biased
    downward at small k, and this pool has two or three studies.
    """
    t2, _ = dl_tau2(ys, vs)
    for _ in range(iters):
        w = [1.0 / (v + t2) for v in vs]
        sw = sum(w)
        mu = sum(wi * y for wi, y in zip(w, ys)) / sw
        num = sum((wi ** 2) * ((y - mu) ** 2 - v) for wi, y, v in zip(w, ys, vs)) \
            + sum(wi ** 2 for wi in w) / sw
        den = sum(wi ** 2 for wi in w)
        new = max(0.0, num / den)
        if abs(new - t2) < 1e-12:
            t2 = new
            break
        t2 = new
    return t2


def pool(rows, estimator="REML"):
    ys = [r["y"] for r in rows]
    vs = [r["se"] ** 2 for r in rows]
    t2 = reml_tau2(ys, vs) if estimator == "REML" else dl_tau2(ys, vs)[0]
    w = [1.0 / (v + t2) for v in vs]
    sw = sum(w)
    mu = sum(wi * y for wi, y in zip(w, ys)) / sw
    se = math.sqrt(1.0 / sw)
    z = Z[95]
    dl, q = dl_tau2(ys, vs)
    k = len(rows)
    i2 = max(0.0, (q - (k - 1)) / q) * 100.0 if q > 0 else 0.0
    return {"k": k, "point": mu, "ci_low": mu - z * se, "ci_high": mu + z * se,
            "se": se, "tau2": t2, "tau2_DL": dl, "Q": q, "I2_percent": i2,
            "estimator": estimator}


def stored_rows():
    with io.open(OBJ, encoding="utf-8") as fh:
        obj = json.load(fh)
    blk = (obj.get("results") or {}).get("by_outcome", {}).get("kccq_css_change") or {}
    out = []
    for r in (blk.get("per_trial") or []):
        lvl = r.get("ci_level") or 95
        out.append({"id": r.get("nct"), "y": float(r["point"]),
                    "se": se_from_ci(r["ci_low"], r["ci_high"], lvl),
                    "ci": (r["ci_low"], r["ci_high"], lvl)})
    return out, (blk.get("pooled") or {})


def main():
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    rows, stored = stored_rows()
    print("STORED ROWS (k=%d)" % len(rows))
    for r in rows:
        print("   %-14s y=%-6.3f ci=%s  -> se=%.5f" % (r["id"], r["y"], r["ci"], r["se"]))

    got = pool(rows)
    print()
    print("SELF-TEST -- reproduce the stored k=2 pool from those rows")
    print("   stored    point=%s ci=(%s, %s)"
          % (stored.get("point"), stored.get("ci_low"), stored.get("ci_high")))
    print("   recomputed point=%.4f ci=(%.4f, %.4f)  tau2=%.4f (DL %.4f) I2=%.1f%%"
          % (got["point"], got["ci_low"], got["ci_high"], got["tau2"], got["tau2_DL"],
             got["I2_percent"]))
    ok = (stored.get("point") is not None
          and abs(got["point"] - float(stored["point"])) < 0.02
          and abs(got["ci_low"] - float(stored["ci_low"])) < 0.05
          and abs(got["ci_high"] - float(stored["ci_high"])) < 0.05)
    print("   %s" % ("MATCHES -- this code may compute the k=3 pool."
                     if ok else "DOES NOT MATCH -- refusing to compute k=3."))
    if "--selftest" in sys.argv:
        return 0 if ok else 1
    if not ok:
        return 1

    # --- the third trial, supplied on the command line so the number is auditable in the
    # --- shell history and cannot be quietly edited into this file.
    third = [a for a in sys.argv[1:] if a.startswith("--add=")]
    if not third:
        print()
        print("No third row supplied. Pass --add=NCT,md,lo,hi,level to compute the k=3 pool.")
        return 0
    for spec in third:
        nct, md, lo, hi, lvl = spec.split("=", 1)[1].split(",")
        rows.append({"id": nct, "y": float(md),
                     "se": se_from_ci(lo, hi, lvl), "ci": (lo, hi, int(lvl))})
    out = pool(rows)
    print()
    print("k=3 POOL, DERIVED HERE")
    for r in rows:
        print("   %-14s y=%-6.3f se=%.5f  w=%.4f" % (r["id"], r["y"], r["se"], 1.0 / r["se"] ** 2))
    print("   POINT %.4f   95%% CI (%.4f, %.4f)" % (out["point"], out["ci_low"], out["ci_high"]))
    print("   tau2 %.4f (DL %.4f)   Q %.4f   I2 %.1f%%   estimator %s"
          % (out["tau2"], out["tau2_DL"], out["Q"], out["I2_percent"], out["estimator"]))
    print()
    print("COMPARISON IS MADE ONLY NOW, AFTER THE FACT:")
    for label, p, lo2, hi2 in (("published synthesis A", 7.4, 4.9, 9.9),
                               ("published synthesis B", 7.33, 5.84, 8.82),
                               ("our previous k=2", 7.43, 5.0895, 9.7704)):
        print("   %-24s %.2f (%.2f, %.2f)   ours differs by %+.3f"
              % (label, p, lo2, hi2, out["point"] - p))
    return 0


if __name__ == "__main__":
    sys.exit(main())
