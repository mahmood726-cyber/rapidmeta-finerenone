"""Of the topics whose estimate is COMPUTABLE, how many yield a USABLE interval?

A ceiling of "objects that could carry an HTA table" is misleading if the
estimate such an object would carry has a 95% interval spanning seventy orders
of magnitude. All 73 objects classed COMPUTABLE_NOT_COMPUTED already hold a
pooled estimate in their r_validation sidecar -- they are not merely
computable, they are COMPUTED AND UNUSED. But k is 2 or 3 for most of them,
and a REML+HKSJ interval at k=2 with high heterogeneity is enormous by
construction, not by accident.

CRITERIA, STATED BEFORE THE COUNT AND CHOSEN ON PRINCIPLE, NOT FITTED:

  DEGENERATE_INTERVAL  ci_high / ci_low > 1000, or ci_low <= 0, or either
                       bound non-finite. Three orders of magnitude is already
                       past the point where an interval constrains any
                       decision; the threshold is not tuned to the data and
                       moving it an order of magnitude either way is reported
                       below so nobody has to take it on trust.
  SINGLE_TRIAL_POOL    k < 2. Not a pool.
  DIRECTION_CONFLICTED per-trial odds ratios include one below 0.9 AND one
                       above 2.0, with I-squared above 90. Such a pool is
                       combining outcomes that are not the same quantity.
                       DEMONSTRATED, not theorised: pcsk9-inhibitors-cv-review
                       pools FOURIER and ODYSSEY OUTCOMES at OR ~0.84 (CV
                       events, protective) with ORION-10, ORION-11 and BERSON
                       at OR 35 to 401 -- an LDL-C target-attainment outcome
                       where benefit means MORE events. Interval width alone
                       called that pool USABLE, which is why this state
                       exists: a narrow interval around an incommensurable
                       pool is worse than a wide one, not better.
  USABLE               everything else.

This does not say a USABLE estimate is correct or that the topic should be
published -- only that the interval carries decision content. The ceiling
worth quoting is the USABLE one, and both figures are printed so neither can
be quoted alone.
"""
import io
import json
import math
import os
import sys
from collections import Counter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))

from hta_ceiling import (objects, live_outcomes, _sidecar_index,  # noqa
                         proven_sidecar_for, sidecar_cells)

SPREAD = 1000.0


def bounds(side):
    """(point, lo, hi) on the ratio scale, whichever measure the file names."""
    for pk, lk, hk in (("pooled_OR", "ci_low_OR", "ci_high_OR"),
                       ("pooled_RR", "ci_low_RR", "ci_high_RR"),
                       ("pooled_HR", "ci_low_HR", "ci_high_HR")):
        p, lo, hi = side.get(pk), side.get(lk), side.get(hk)
        if p is not None and lo is not None and hi is not None:
            return p, lo, hi
    return None, None, None


def per_trial_ors(side):
    """Per-trial odds ratios with a 0.5 correction, for direction screening."""
    out = []
    for t in (side.get("trials") or []):
        if isinstance(t, dict) is False:
            continue
        try:
            a = t["tE"] + 0.5
            b = t["tN"] - t["tE"] + 0.5
            c = t["cE"] + 0.5
            d = t["cN"] - t["cE"] + 0.5
        except Exception:
            continue
        if b > 0 and c > 0 and d > 0:
            out.append((a / b) / (c / d))
    return out


def classify(side, spread=SPREAD):
    k = side.get("k")
    p, lo, hi = bounds(side)
    if p is None:
        return "NO_POOLED_ESTIMATE"
    if isinstance(k, int) and k < 2:
        return "SINGLE_TRIAL_POOL"
    for v in (p, lo, hi):
        if isinstance(v, (int, float)) is False or math.isfinite(v) is False:
            return "DEGENERATE_INTERVAL"
    if lo <= 0:
        return "DEGENERATE_INTERVAL"
    if hi / lo > spread:
        return "DEGENERATE_INTERVAL"
    ors = per_trial_ors(side)
    i2 = side.get("I2") or 0
    if ors and min(ors) < 0.9 and max(ors) > 2.0 and i2 > 90:
        return "DIRECTION_CONFLICTED"
    return "USABLE"


def main():
    idx = _sidecar_index()
    rows = []
    for topic, _path, obj in objects():
        if live_outcomes(obj):
            continue
        side, _st = proven_sidecar_for(topic, obj, idx)
        if side is None or sidecar_cells(side) < 2:
            continue
        p, lo, hi = bounds(side)
        rows.append((topic, side.get("k"), p, lo, hi,
                     side.get("I2"), side.get("method"), classify(side)))

    c = Counter(r[7] for r in rows)
    print("UNIT: OBJECT. denominator = %d objects classed "
          "COMPUTABLE_NOT_COMPUTED" % len(rows))
    for k in ("USABLE", "DIRECTION_CONFLICTED", "DEGENERATE_INTERVAL",
              "SINGLE_TRIAL_POOL", "NO_POOLED_ESTIMATE"):
        print("  %-22s %d" % (k, c.get(k, 0)))
    print("  identity: %d == %d" % (sum(c.values()), len(rows)))
    print("")
    print("SENSITIVITY OF THE THRESHOLD (it is not tuned; here is the curve)")
    for s in (100.0, 1000.0, 10000.0, 1e6):
        cc = Counter(classify(
            {"k": r[1], "pooled_OR": r[2], "ci_low_OR": r[3],
             "ci_high_OR": r[4]}, s) for r in rows)
        print("   ci_high/ci_low > %-9g  ->  USABLE %d, DEGENERATE %d"
              % (s, cc.get("USABLE", 0), cc.get("DEGENERATE_INTERVAL", 0)))
    print("")
    ks = Counter(r[1] for r in rows)
    print("k DISTRIBUTION ACROSS THOSE OBJECTS (unit: OBJECT)")
    for k in sorted(x for x in ks if isinstance(x, int)):
        print("   k=%-3d %d" % (k, ks[k]))
    print("")
    print("USABLE, BY NAME")
    for r in sorted([x for x in rows if x[7] == "USABLE"],
                    key=lambda x: -(x[1] or 0)):
        print("   %-38s k=%-3s %.3f (%.3f to %.3f)  I2=%.0f%%"
              % (r[0][:38], r[1], r[2], r[3], r[4], r[5] or 0))
    print("")
    print("DEGENERATE, WORST 10 BY SPREAD")
    deg = [x for x in rows if x[7] == "DEGENERATE_INTERVAL"
           and x[3] and x[3] > 0 and math.isfinite(x[4])]
    for r in sorted(deg, key=lambda x: -(x[4] / x[3]))[:10]:
        print("   %-38s k=%-3s spread %.3g  I2=%.0f%%"
              % (r[0][:38], r[1], r[4] / r[3], r[5] or 0))

    out = {
        "unit": "OBJECT",
        "denominator_computable_not_computed": len(rows),
        "threshold_ci_high_over_ci_low": SPREAD,
        "states": dict(c),
        "rows": [{"topic": r[0], "k": r[1], "point": r[2], "ci_low": r[3],
                  "ci_high": r[4], "I2": r[5], "method": r[6], "state": r[7]}
                 for r in rows],
    }
    d = os.path.join(ROOT, "evidence", "2026-09-02-hta-ceiling")
    if os.path.isdir(d) is False:
        os.makedirs(d)
    io.open(os.path.join(d, "ceiling_usable.json"), "w",
            encoding="utf-8", newline="\n").write(
                json.dumps(out, indent=1, ensure_ascii=False))
    print("")
    print("wrote evidence/2026-09-02-hta-ceiling/ceiling_usable.json")
    return out


if __name__ == "__main__":
    main()
