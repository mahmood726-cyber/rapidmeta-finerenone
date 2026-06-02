#!/usr/bin/env python
"""Null provably-invalid ratio data flagged by the data-integrity audit.

The `additive_ratio_ci` findings are trials whose publishedHR/CI is a ratio with
an additively-symmetric CI (impossible for a ratio). Investigation showed two
sub-classes:

  * continuous (MD) outcome (e.g. DAS28-CRP, CDR-SB, BCVA): a ratio CANNOT exist
    for a continuous endpoint, and the trial-level 2x2 (tE/cE) is fabricated
    (continuous outcomes have no event counts). We null the ratio fields AND the
    fake event counts, leaving estimandType:"MD" so the app honestly shows the
    continuous effect as not-extracted rather than a fabricated ratio/OR.

  * binary outcome with a real 2x2: the ratio override is provably wrong (its CI
    is additive and its point doesn't match the counts), but the 2x2 is real.
    We null only the ratio override so the app's engine repools from the
    verified counts with the topic's own measure.

This is removal of provably-invalid data, not fabrication: nothing plausible is
invented. Binary-safe (preserves line endings), idempotent, dry-run-first.

Usage:
  python scripts/fix_continuous_as_ratio.py --audit outputs/data_integrity_audit.json --dry-run
  python scripts/fix_continuous_as_ratio.py --audit outputs/data_integrity_audit.json
"""
from __future__ import annotations
import argparse
import importlib.util
import json
import os
import re
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

_spec = importlib.util.spec_from_file_location(
    "dia", os.path.join(REPO, "scripts", "data_integrity_audit.py"))
dia = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(dia)

RATIO_FIELDS = ("publishedHR", "hrLCI", "hrUCI", "pubHR", "pubHR_LCI", "pubHR_UCI")
NUM = r"-?\d*\.?\d+(?:[eE][-+]?\d+)?"


def outcome_is_md(obj: str) -> bool:
    tail = obj.split("allOutcomes", 1)
    if len(tail) < 2:
        return False
    m = re.search(r'estimandType:"([^"]+)"', tail[1])
    return bool(m) and m.group(1).upper() == "MD"


def null_field_in_head(obj: str, fieldname: str):
    """Null a top-level numeric field (before allOutcomes). Returns (obj, changed)."""
    head, sep, tail = obj.partition("allOutcomes")
    pat = re.compile(r"(?<![A-Za-z_])(" + re.escape(fieldname) + r")\s*:\s*" + NUM)
    new_head, n = pat.subn(r"\1:null", head, count=1)
    return new_head + sep + tail, n > 0


def fix_trial(obj: str):
    changed = []
    is_md = outcome_is_md(obj)
    for f in RATIO_FIELDS:
        obj, c = null_field_in_head(obj, f)
        if c:
            changed.append(f)
    if is_md:
        # Null the fabricated event counts so no bogus OR can be derived.
        for f in ("tE", "cE"):
            obj, c = null_field_in_head(obj, f)
            if c:
                changed.append(f)
    return obj, changed, ("MD" if is_md else "binary")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--audit", default="outputs/data_integrity_audit.json")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    audit = json.load(open(os.path.join(REPO, args.audit), encoding="utf-8"))
    targets = {}
    # Root class is ratio_on_continuous (a ratio value on an MD outcome).
    # additive_ratio_ci is the subset whose CI was additively symmetric; both
    # are handled identically (null the impossible ratio + any fake 2x2).
    for f in audit["findings"]:
        if f["class"] in ("ratio_on_continuous", "additive_ratio_ci"):
            targets.setdefault(f["app"], set()).add(f["trial"])

    total_trials = 0
    total_apps = 0
    kinds = {"MD": 0, "binary": 0}
    skipped = 0
    for app in sorted(targets):
        path = os.path.join(REPO, app)
        data = open(path, "rb").read().decode("utf-8", "replace")
        new_data = data
        app_changed = False
        for key, obj in dia.find_trial_objects(data):
            if key not in targets[app]:
                continue
            new_obj, changed, kind = fix_trial(obj)
            if not changed:
                skipped += 1
                continue
            assert new_data.count(obj) == 1, f"{app}:{key} object not unique"
            new_data = new_data.replace(obj, new_obj, 1)
            total_trials += 1
            kinds[kind] += 1
            app_changed = True
        if app_changed:
            total_apps += 1
            if not args.dry_run:
                open(path, "wb").write(new_data.encode("utf-8"))

    verb = "WOULD null" if args.dry_run else "nulled"
    print(f"{verb} ratio data in {total_trials} trials across {total_apps} apps.")
    print(f"  continuous (MD, ratio+event-counts nulled): {kinds['MD']}")
    print(f"  binary (ratio override nulled, 2x2 kept):   {kinds['binary']}")
    if skipped:
        print(f"  already clean / skipped: {skipped}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
