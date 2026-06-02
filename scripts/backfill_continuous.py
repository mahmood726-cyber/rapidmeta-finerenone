#!/usr/bin/env python
"""Backfill source-verified effect values into trials whose effect is null.

Reads outputs/pmid_resolver/nct_continuous.json (per-NCT effect + CI extracted
from ClinicalTrials.gov structured results: outcome_analyses /
outcome_measurements_mean_arms), and fills the generic effect fields
(publishedHR/hrLCI/hrUCI + pubHR/pubHR_LCI/pubHR_UCI) for every trial whose
publishedHR is currently null. The engine reads MD/RD/HR/OR/RR from these fields
uniformly; the outcome-level estimandType drives interpretation.

This restores the legitimate mean-differences that the over-aggressive
continuous-as-ratio null removed, corrects the values that were genuinely wrong,
and fills trials that never had an effect extracted. It only writes where the
field is currently null, so curated non-null values are never overwritten.

Binary-safe (preserves line endings), idempotent, dry-run-first.

Usage:
  python scripts/backfill_continuous.py --dry-run
  python scripts/backfill_continuous.py
"""
from __future__ import annotations
import argparse
import importlib.util
import glob
import json
import os
import re
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_spec = importlib.util.spec_from_file_location(
    "dia", os.path.join(REPO, "scripts", "data_integrity_audit.py"))
dia = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(dia)

CONT = json.load(open(os.path.join(REPO, "outputs", "pmid_resolver", "nct_continuous.json"),
                     encoding="utf-8"))

# Map the generic effect fields to the source keys.
FIELD_SRC = [
    ("publishedHR", "effect"), ("hrLCI", "lci"), ("hrUCI", "uci"),
    ("pubHR", "effect"), ("pubHR_LCI", "lci"), ("pubHR_UCI", "uci"),
]


def numstr(v):
    if v is None:
        return "null"
    if isinstance(v, float) and v.is_integer():
        return str(int(v))
    return repr(v) if isinstance(v, float) else str(v)


def set_null_field(obj_head: str, name: str, value):
    """Replace `name:null` with `name:value` in the head (before allOutcomes).
    Only touches a currently-null field. Returns (head, changed)."""
    pat = re.compile(r"(?<![A-Za-z_])(" + re.escape(name) + r")\s*:\s*null")
    new, n = pat.subn(lambda m: f"{m.group(1)}:{numstr(value)}", obj_head, count=1)
    return new, n > 0


def backfill_trial(obj: str, info: dict):
    if info.get("effect") is None:
        return obj, []
    head, sep, tail = obj.partition("allOutcomes")
    changed = []
    for field_name, src_key in FIELD_SRC:
        head, c = set_null_field(head, field_name, info.get(src_key))
        if c:
            changed.append(field_name)
    return head + sep + tail, changed


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--glob", default="*_REVIEW*.html")
    args = ap.parse_args()

    files = sorted(glob.glob(os.path.join(REPO, args.glob)))
    trials_filled = 0
    apps_changed = 0
    by_kind = {}
    no_source = 0
    for path in files:
        data = open(path, "rb").read().decode("utf-8", "replace")
        new_data = data
        app_changed = False
        for key, obj in dia.find_trial_objects(data):
            # Only fill where publishedHR is currently null.
            if dia.as_num(dia.field(obj, "publishedHR")) is not None:
                continue
            nct = key.split("_")[0]
            info = CONT.get(nct)
            if not info:
                no_source += 1
                continue
            new_obj, changed = backfill_trial(obj, info)
            if not changed:
                continue
            assert new_data.count(obj) == 1, f"{os.path.basename(path)}:{key} not unique"
            new_data = new_data.replace(obj, new_obj, 1)
            trials_filled += 1
            kind = str(info.get("kind", "?")).upper()
            by_kind[kind] = by_kind.get(kind, 0) + 1
            app_changed = True
        if app_changed:
            apps_changed += 1
            if not args.dry_run:
                open(path, "wb").write(new_data.encode("utf-8"))

    verb = "WOULD backfill" if args.dry_run else "backfilled"
    print(f"{verb} {trials_filled} trials across {apps_changed} apps.")
    print("  by source kind: " + ", ".join(f"{k}={v}" for k, v in sorted(by_kind.items())))
    print(f"  null-effect trials with no source data (left null): {no_source}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
