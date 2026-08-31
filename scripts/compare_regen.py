r"""Compare a parallel regeneration against the served corpus, and ATTRIBUTE
every difference.

WHY ATTRIBUTION AND NOT JUST A COUNT
    The regeneration exists to fix one thing: an estimator that could not
    report heterogeneity. If MORE artefacts move than that fix accounts for,
    the extra movement is a SECOND DEFECT, not a bigger win -- the rebuild is
    doing something besides what it was authorised to do. So every changed
    file is sorted into a cause:

      ESTIMATOR_ONLY   the trial cells are byte-for-byte the same in old and
                       new, so any change in tau2 or the interval is
                       attributable to the corrected estimator and nothing
                       else. This is the authorised change.
      TRIALS_CHANGED   the cells differ. The page has been edited since the
                       original build, so the rebuild is reading different
                       evidence. NOT attributable to the estimator, and must
                       be listed by name rather than absorbed into a total.
      UNCHANGED        no numeric difference at all.

    A count of "N files changed" without this split cannot distinguish the
    fix from drift, and would let page drift be reported as the fix working.

WHAT IS NOT DONE HERE
    Nothing is replaced. This reads two directories and prints. The served
    corpus is not written to.
"""
from __future__ import annotations
import argparse
import glob
import json
import math
import os
from collections import Counter, OrderedDict

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SERVED = os.path.join(ROOT, "outputs", "r_validation")

CELL_KEYS = ("tE", "tN", "cE", "cN")
NUM_KEYS = ("pooled_OR", "pooled_logOR", "ci_low_OR", "ci_high_OR", "tau2",
            "I2", "Q", "pooled_se")


def load(path):
    try:
        d = json.load(open(path, encoding="utf-8"))
    except Exception:
        return None
    return d if isinstance(d, dict) else None


def cells_of(d):
    """A comparable, order-independent fingerprint of the trial arms."""
    out = []
    for t in (d.get("trials") or []):
        if isinstance(t, dict) and all(k in t for k in CELL_KEYS):
            out.append((str(t.get("nct") or t.get("name")),
                        t["tE"], t["tN"], t["cE"], t["cN"]))
    return sorted(out)


def differs(a, b, rel=1e-9):
    if a is None and b is None:
        return False
    if a is None or b is None:
        return True
    if isinstance(a, (int, float)) and isinstance(b, (int, float)):
        if a == b:
            return False
        return abs(a - b) > rel * max(1.0, abs(a), abs(b))
    return a != b


def compare(new_dir):
    served = {os.path.basename(p)[:-5] for p in
              glob.glob(os.path.join(SERVED, "*.json"))
              if not os.path.basename(p).startswith("_")}
    fresh = {os.path.basename(p)[:-5] for p in
             glob.glob(os.path.join(new_dir, "*.json"))
             if not os.path.basename(p).startswith("_")}
    both = sorted(served & fresh)
    rows = []
    for stem in both:
        o = load(os.path.join(SERVED, stem + ".json"))
        n = load(os.path.join(new_dir, stem + ".json"))
        if o is None or n is None:
            rows.append({"stem": stem, "cause": "UNREADABLE"})
            continue
        same_cells = cells_of(o) == cells_of(n)
        moved = [k for k in NUM_KEYS if differs(o.get(k), n.get(k))]
        if moved:
            cause = "ESTIMATOR_ONLY" if same_cells else "TRIALS_CHANGED"
        else:
            cause = "UNCHANGED"
        rows.append({"stem": stem, "cause": cause, "moved": moved,
                     "same_cells": same_cells,
                     "old_tau2": o.get("tau2"), "new_tau2": n.get("tau2"),
                     "old_k": o.get("k"), "new_k": n.get("k"),
                     "old": {k: o.get(k) for k in NUM_KEYS},
                     "new": {k: n.get(k) for k in NUM_KEYS}})
    return rows, served, fresh


def excludes_one(lo, hi):
    if lo is None or hi is None:
        return None
    return not (lo <= 1.0 <= hi)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--new-dir", required=True)
    ap.add_argument("--json-out", default=None)
    ap.add_argument("--focus", nargs="*", default=[])
    a = ap.parse_args()
    new_dir = a.new_dir if os.path.isabs(a.new_dir) else os.path.join(ROOT, a.new_dir)

    rows, served, fresh = compare(new_dir)
    both = [r["stem"] for r in rows]
    print("POPULATION")
    print("  served sidecars                    %d" % len(served))
    print("  regenerated sidecars               %d" % len(fresh))
    print("  LIKE-FOR-LIKE (in both)            %d" % len(both))
    print("  served with no regenerated twin    %d  (no page; not rebuilt)"
          % len(served - fresh))
    print("  regenerated with no served twin    %d  (new)" % len(fresh - served))
    print("")

    c = Counter(r["cause"] for r in rows)
    print("EVERY LIKE-FOR-LIKE FILE ATTRIBUTED TO A CAUSE")
    for k in ("ESTIMATOR_ONLY", "TRIALS_CHANGED", "UNCHANGED", "UNREADABLE"):
        print("  %-16s %d" % (k, c.get(k, 0)))
    tot = sum(c.values())
    print("  identity: %d == %d like-for-like : %s"
          % (tot, len(both), "HOLDS" if tot == len(both) else "FAILS"))
    print("")

    z_old = sum(1 for r in rows if r.get("old_tau2") == 0.0)
    z_new = sum(1 for r in rows if r.get("new_tau2") == 0.0)
    print("THE NUMBER THAT HAD TO MOVE")
    print("  like-for-like with tau2 == 0.0  BEFORE  %d" % z_old)
    print("  like-for-like with tau2 == 0.0  AFTER   %d" % z_new)
    print("  drop                                    %d" % (z_old - z_new))
    print("")

    # the drop, split by whether the estimator alone explains it
    est = [r for r in rows if r["cause"] == "ESTIMATOR_ONLY"
           and r.get("old_tau2") == 0.0 and r.get("new_tau2") != 0.0]
    drift = [r for r in rows if r["cause"] == "TRIALS_CHANGED"
             and r.get("old_tau2") == 0.0 and r.get("new_tau2") != 0.0]
    print("  of that drop, attributable to THE ESTIMATOR   %d" % len(est))
    print("  of that drop, attributable to PAGE DRIFT      %d" % len(drift))
    if drift:
        print("  page-drift files, BY NAME (not absorbed into a total):")
        for r in drift[:40]:
            print("      %-44s k %s -> %s" % (r["stem"], r["old_k"], r["new_k"]))
        if len(drift) > 40:
            print("      ... and %d more, all in the JSON output" % (len(drift) - 40))
    print("")

    if a.focus:
        print("FOCUS ARTEFACTS -- OLD vs NEW, side by side")
        by = {r["stem"]: r for r in rows}
        for stem in a.focus:
            r = by.get(stem)
            if r is None:
                print("  %s: NOT PRESENT IN BOTH -- served=%s regenerated=%s"
                      % (stem, stem in served, stem in fresh))
                continue
            o, n = r["old"], r["new"]
            print("  %s   [%s]" % (stem, r["cause"]))
            print("    %-14s %22s   %22s" % ("", "SERVED (old)", "REGENERATED (new)"))
            for k in ("k", "tau2", "I2", "pooled_OR", "ci_low_OR", "ci_high_OR"):
                ov = r["old_k"] if k == "k" else o.get(k)
                nv = r["new_k"] if k == "k" else n.get(k)
                flag = "  <-- moved" if differs(ov, nv) else ""
                print("    %-14s %22s   %22s%s" % (k, ov, nv, flag))
            eo = excludes_one(o.get("ci_low_OR"), o.get("ci_high_OR"))
            en = excludes_one(n.get("ci_low_OR"), n.get("ci_high_OR"))
            print("    %-14s %22s   %22s%s"
                  % ("excludes OR=1", eo, en,
                     "  <-- CONCLUSION CHANGES" if eo != en else ""))
            print("    trial cells identical: %s" % r["same_cells"])
            print("")

    if a.json_out:
        json.dump(rows, open(a.json_out, "w", encoding="utf-8"), indent=1)
        print("wrote %s" % a.json_out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
