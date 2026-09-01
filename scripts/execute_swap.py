r"""Swap the 232 cell-identical sidecars, and prove afterwards what landed.

SCOPE, ENFORCED IN CODE
    Only files whose trial cells are BYTE-IDENTICAL between the served copy
    and the regenerated one. Anything whose cells differ is skipped and
    counted -- those 34 are parked as their own state because their
    underlying data moved, which is a different question from an estimator
    correction and must not ride along on this authorisation.

WHAT IS PROVEN AFTER WRITING
    1. every written file is byte-identical to its source in the parallel
       corpus. A swap that half-wrote would otherwise look like a swap.
    2. every written file's cells still match what was served before it. If
       a cell moved, the file was not what this operation was authorised to
       write.
    3. corrections/ is untouched -- same file list, same sha256 for each.
       A regeneration destroying retractions is the standing warning this
       project has, and it is now checked on every swap rather than believed.
    4. the count that ACTUALLY landed, not the count intended.
"""
from __future__ import annotations
import argparse
import glob
import hashlib
import json
import os
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SERVED = os.path.join(ROOT, "outputs", "r_validation")
CORRECTIONS = os.path.join(ROOT, "corrections")


def sha(path):
    with open(path, "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()


def cells(d):
    return sorted((str(t.get("nct") or t.get("name")), t.get("tE"), t.get("tN"),
                   t.get("cE"), t.get("cN")) for t in (d.get("trials") or []))


def corrections_state():
    return {os.path.basename(p): sha(p)
            for p in sorted(glob.glob(os.path.join(CORRECTIONS, "*.md")))}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--new-dir", required=True)
    ap.add_argument("--apply", action="store_true",
                    help="without this, nothing is written")
    a = ap.parse_args()
    new_dir = a.new_dir if os.path.isabs(a.new_dir) else os.path.join(ROOT, a.new_dir)

    before_corr = corrections_state()
    print("corrections/ before: %d files" % len(before_corr))

    eligible, skipped_cells, missing = [], [], []
    for p in sorted(glob.glob(os.path.join(new_dir, "*.json"))):
        stem = os.path.basename(p)[:-5]
        sp = os.path.join(SERVED, stem + ".json")
        if os.path.exists(sp) is False:
            missing.append(stem)
            continue
        try:
            s = json.load(open(sp, encoding="utf-8"))
            n = json.load(open(p, encoding="utf-8"))
        except Exception:
            skipped_cells.append(stem)
            continue
        if cells(s) != cells(n):
            skipped_cells.append(stem)
            continue
        eligible.append((stem, sp, p, cells(s)))

    print("eligible (cell-identical)     %d" % len(eligible))
    print("skipped, cells differ         %d  <- parked, not swapped"
          % len(skipped_cells))
    print("regenerated with no served twin %d" % len(missing))
    if a.apply is False:
        print("\nDRY RUN. Nothing written. Re-run with --apply.")
        return 0

    written, failed = [], []
    for stem, sp, p, pre_cells in eligible:
        try:
            shutil.copyfile(p, sp)
        except Exception as exc:
            failed.append((stem, "copy failed: %s" % str(exc)[:60]))
            continue
        # 1. byte-identical to source
        if sha(sp) != sha(p):
            failed.append((stem, "written file differs from its source"))
            continue
        # 2. cells unchanged from what was served
        try:
            after = json.load(open(sp, encoding="utf-8"))
        except Exception as exc:
            failed.append((stem, "unreadable after write: %s" % str(exc)[:50]))
            continue
        if cells(after) != pre_cells:
            failed.append((stem, "cells moved during the swap"))
            continue
        written.append(stem)

    after_corr = corrections_state()
    corr_ok = (before_corr == after_corr)

    print("")
    print("SWAP COMPLETE")
    print("  intended        %d" % len(eligible))
    print("  ACTUALLY WROTE  %d" % len(written))
    print("  failed          %d" % len(failed))
    for stem, why in failed[:20]:
        print("      %-44s %s" % (stem, why))
    print("  identity: %d + %d == %d : %s"
          % (len(written), len(failed), len(eligible),
             "HOLDS" if len(written) + len(failed) == len(eligible) else "FAILS"))
    print("")
    print("  corrections/ after: %d files, unchanged: %s"
          % (len(after_corr), corr_ok))
    if corr_ok is False:
        for k in set(before_corr) | set(after_corr):
            if before_corr.get(k) != after_corr.get(k):
                print("      CHANGED OR MISSING: %s" % k)
    clean = (len(failed) == 0) and corr_ok
    return 0 if clean else 1


if __name__ == "__main__":
    raise SystemExit(main())
