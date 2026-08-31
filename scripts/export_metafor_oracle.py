r"""Export a REML tau-squared oracle from metafor, by RUNNING metafor.

WHY THIS FILE EXISTS
    The estimator in this repository was wrong for as long as it ran, and no
    internal check could have found it: tau2 = 0 means "no heterogeneity",
    which is a legitimate result, so the failure value was also a meaningful
    value. Only an EXTERNAL ORACLE -- the same quantity computed by a
    different program -- can separate the two.

    So the oracle is not asserted here. It is COMPUTED by metafor and written
    to a fixture file. Every number in tests/fixtures/metafor_oracle.json was
    produced by R, not typed by a person. An earlier control tonight was
    hand-typed, two of its four variances were roughly half their true
    values, and it sent a delegated lane chasing a target that did not exist.
    Hand-typing an oracle is how you get a control that agrees with nothing.

WHAT IT COVERS
    arni-hfref on THREE scales -- risk difference, log risk ratio, log odds
    ratio -- because the defect was scale-sensitive: the shipped estimator
    returned exactly 0.0 on the risk-difference scale where the variances are
    ~1e-4. One scale is not a test of a scale-sensitive bug.

    Plus a spread of real sidecars chosen to span k and heterogeneity, so the
    oracle is not four numbers from one dataset.

    The arni values are additionally cross-checkable against tau2 values
    ALREADY stored in ssot/arni-hfref/arni-hfref.json under
    results.by_outcome.cvdeath_or_hfh_first.count_panels.{rd,rr,or}.tau2,
    which were computed by metafor at build time, by someone else, earlier.
    Agreement between a fresh metafor run and those stored values is
    independent evidence that the inputs assembled here are the same inputs
    that object was built from.

USAGE
    python scripts/export_metafor_oracle.py --emit-inputs   # writes inputs
    Rscript scripts/metafor_oracle.R                        # runs metafor
    python scripts/export_metafor_oracle.py --collect       # builds fixture
"""
from __future__ import annotations
import argparse
import glob
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
FIXDIR = os.path.join(ROOT, "tests", "fixtures")
INPUTS = os.path.join(FIXDIR, "metafor_oracle_inputs.json")
ROUT = os.path.join(FIXDIR, "metafor_oracle_r_output.json")
FIXTURE = os.path.join(FIXDIR, "metafor_oracle.json")

# The four arni-hfref trials for cvdeath_or_hfh_first, as 2x2 cells.
# treatment events / treatment n / control events / control n.
# Reconstructed from count_panels.baseline_risk (control arm) and
# count_panels.labbe (treatment risk and total n) in the object itself.
ARNI = [("paradigm-hf", 914, 4187, 1117, 4212),
        ("parachute-hf", 155, 462, 169, 460),
        ("parallel-hf", 30, 111, 28, 112),
        ("answer-hf", 12, 95, 8, 95)]


def cells_to_scales(cells):
    """Build (yi, vi) on the risk-difference, log-RR and log-OR scales."""
    rd_y, rd_v, rr_y, rr_v, or_y, or_v = [], [], [], [], [], []
    for _name, tE, tN, cE, cN in cells:
        a, b, c, d = tE, tN - tE, cE, cN - cE
        if min(a, b, c, d) == 0:          # correction ONLY on a zero cell
            a, b, c, d = a + 0.5, b + 0.5, c + 0.5, d + 0.5
        n1, n0 = a + b, c + d
        p1, p0 = a / n1, c / n0
        rd_y.append(p1 - p0)
        rd_v.append(p1 * (1 - p1) / n1 + p0 * (1 - p0) / n0)
        rr_y.append(math.log(p1 / p0))
        rr_v.append(1 / a - 1 / n1 + 1 / c - 1 / n0)
        or_y.append(math.log((a * d) / (b * c)))
        or_v.append(1 / a + 1 / b + 1 / c + 1 / d)
    return {"rd": (rd_y, rd_v), "rr": (rr_y, rr_v), "or": (or_y, or_v)}


def pick_sidecars(n=12):
    """A spread of real sidecars across k and stored tau2, chosen by a stated
    rule rather than by taste: sorted by name, take every Nth with k>=3 so
    the set is reproducible and not curated toward agreement."""
    out = []
    files = [f for f in sorted(glob.glob(os.path.join(
        ROOT, "outputs", "r_validation", "*.json")))
        if not os.path.basename(f).startswith("_")]
    eligible = []
    for f in files:
        try:
            d = json.load(open(f, encoding="utf-8"))
        except Exception:
            continue
        if not isinstance(d, dict):
            continue
        rows = [t for t in (d.get("trials") or [])
                if isinstance(t, dict)
                and isinstance(t.get("yi"), (int, float))
                and isinstance(t.get("vi"), (int, float)) and t["vi"] > 0]
        if len(rows) >= 3:
            eligible.append((os.path.basename(f)[:-5], rows))
    if not eligible:
        return out
    step = max(1, len(eligible) // n)
    for stem, rows in eligible[::step][:n]:
        out.append({"id": "sidecar:" + stem,
                    "scale": "logOR",
                    "yi": [t["yi"] for t in rows],
                    "vi": [t["vi"] for t in rows]})
    return out


def emit_inputs():
    os.makedirs(FIXDIR, exist_ok=True)
    items = []
    scales = cells_to_scales(ARNI)
    for scale, (y, v) in scales.items():
        items.append({"id": "arni-hfref:cvdeath_or_hfh_first:" + scale,
                      "scale": scale, "yi": y, "vi": v})
    items.extend(pick_sidecars())
    json.dump(items, open(INPUTS, "w", encoding="utf-8"), indent=1)
    print("wrote %s with %d items" % (INPUTS, len(items)))
    print("  arni scales: rd, rr, or (a scale-sensitive bug needs >1 scale)")
    print("  sidecars   : %d" % (len(items) - 3))
    return 0


def collect():
    if not os.path.exists(ROUT):
        print("MISSING %s -- run: Rscript scripts/metafor_oracle.R" % ROUT)
        return 2
    inputs = {i["id"]: i for i in json.load(open(INPUTS, encoding="utf-8"))}
    rout = json.load(open(ROUT, encoding="utf-8"))
    fixture = []
    for r in rout:
        i = inputs[r["id"]]
        fixture.append({"id": r["id"], "scale": i["scale"],
                        "yi": i["yi"], "vi": i["vi"],
                        "metafor_tau2": r["tau2"],
                        "metafor_estimate": r["estimate"],
                        "metafor_version": r["metafor_version"],
                        "r_version": r["r_version"]})
    json.dump(fixture, open(FIXTURE, "w", encoding="utf-8"), indent=1)
    print("wrote %s with %d oracle values" % (FIXTURE, len(fixture)))

    # cross-check the arni scales against the tau2 values ALREADY stored in
    # the object, computed by metafor at build time by a different run
    obj = json.load(open(os.path.join(ROOT, "ssot", "arni-hfref",
                                      "arni-hfref.json"), encoding="utf-8"))
    cp = obj["results"]["by_outcome"]["cvdeath_or_hfh_first"]["count_panels"]
    print("\nCROSS-CHECK: fresh metafor run vs the tau2 already stored in the "
          "object")
    ok = True
    for scale in ("rd", "rr", "or"):
        stored = cp.get(scale, {}).get("tau2")
        fresh = next((f["metafor_tau2"] for f in fixture
                      if f["id"].endswith(":" + scale)), None)
        if stored is None or fresh is None:
            print("  %-3s stored=%r fresh=%r  -- cannot compare"
                  % (scale, stored, fresh))
            continue
        rel = abs(fresh - stored) / max(abs(stored), 1e-30)
        good = rel < 1e-6
        ok = ok and good
        print("  %-3s stored %.13g   fresh %.13g   rel %.2e  %s"
              % (scale, stored, fresh, rel, "AGREE" if good else "DIFFER"))
    print("  -> %s" % ("the inputs assembled here are the inputs that object "
                       "was built from" if ok else
                       "MISMATCH: do not use this fixture until explained"))
    return 0 if ok else 1


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--emit-inputs", action="store_true")
    ap.add_argument("--collect", action="store_true")
    a = ap.parse_args()
    if a.emit_inputs:
        return emit_inputs()
    if a.collect:
        return collect()
    ap.print_help()
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
