#!/usr/bin/env python
"""Relabel estimandType MD -> RR for two CGRP-migraine responder trials.

STRIVE (NCT02456740) and ARISE (NCT02483585) carry their "<=50% reduction in
monthly migraine days" RESPONDER outcome with estimandType:"MD", but that
outcome is a responder PROPORTION -- a ratio measure, not a mean difference:
  * The stored values have log-symmetric (ratio) CIs: STRIVE 2.04 [1.66,2.51],
    ARISE 1.34 [1.07,1.69].
  * The published primaries (PubMed: Goadsby 2017 NEJM 10.1056/NEJMoa1705848;
    Dodick 2018 Cephalalgia 10.1177/0333102418759786) report this as a >=50%
    responder endpoint (ARISE: OR 1.59); the mean-difference primary is a
    separate outcome (STRIVE -1.4 at 70 mg, ARISE -1.0).
  * The other 13 CGRP trials in the topic all use estimandType:"RR" for the
    identical "<=50% reduction" outcome.

This relabels both estimandType occurrences (trial-level + the single outcome)
from "MD" to "RR" for these two NCTs only, in every app that contains them. The
VALUES are unchanged. Binary-safe, idempotent, dry-run-first, asserting.
"""
from __future__ import annotations
import argparse
import glob
import importlib.util
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_spec = importlib.util.spec_from_file_location(
    "dia", os.path.join(REPO, "scripts", "data_integrity_audit.py"))
dia = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(dia)

NCTS = {"NCT02456740", "NCT02483585"}  # STRIVE, ARISE


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    total_objs = 0
    total_repl = 0
    apps = 0
    for path in sorted(glob.glob(os.path.join(REPO, "*_REVIEW*.html"))):
        data = open(path, "rb").read().decode("utf-8", "replace")
        new_data = data
        app_changed = False
        for key, obj in dia.find_trial_objects(data):
            if key.split("_")[0] not in NCTS:
                continue
            if 'estimandType:"MD"' not in obj:
                continue
            new_obj = obj.replace('estimandType:"MD"', 'estimandType:"RR"')
            n = obj.count('estimandType:"MD"')
            assert new_data.count(obj) == 1, f"{os.path.basename(path)}:{key} not unique"
            new_data = new_data.replace(obj, new_obj, 1)
            total_objs += 1
            total_repl += n
            app_changed = True
        if app_changed:
            apps += 1
            if not args.dry_run:
                open(path, "wb").write(new_data.encode("utf-8"))

    verb = "WOULD relabel" if args.dry_run else "relabeled"
    print(f"{verb} MD->RR in {total_objs} trial objects ({total_repl} estimandType "
          f"occurrences) across {apps} apps.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
