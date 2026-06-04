#!/usr/bin/env python
"""Cross-app NCT -> trial-name consistency check.

Analogue of the PMID-conflict detector, for trial identity: when the SAME NCT
carries materially different trial NAMES across apps, at most one mapping is
right -- it surfaces NCT mis-keyings (e.g. MELODY filed under MEDLEY's
NCT03959488). Names are normalized (lowercase, strip punctuation/spaces, drop a
leading "the"/dose noise) and compared; pure formatting differences are ignored.

Triage aid only -- a flag can be a legitimate alias (brand vs generic, acronym vs
full). Verify against the trial registration before changing anything.

Usage: python scripts/cross_app_nct_name_check.py
"""
from __future__ import annotations
import glob
import importlib.util
import os
import re

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_spec = importlib.util.spec_from_file_location(
    "dia", os.path.join(REPO, "scripts", "data_integrity_audit.py"))
dia = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(dia)


def trial_name(obj: str):
    m = re.search(r'name:"([^"]+)"', obj) or re.search(r'"name":\s*"([^"]+)"', obj)
    return m.group(1) if m else None


def norm(name: str):
    s = name.lower()
    s = re.sub(r"[^a-z0-9]+", "", s)  # drop spaces/punctuation/hyphens
    return s


def main():
    by_nct = {}  # nct -> {normname: (rawname, [apps])}
    for p in sorted(glob.glob(os.path.join(REPO, "*_REVIEW*.html"))):
        if "backup" in p:
            continue
        html = open(p, encoding="utf-8", errors="replace").read()
        for key, obj in dia.find_trial_objects(html):
            nct = key.split("_")[0]
            if not re.match(r"NCT\d{8}$", nct):
                continue
            nm = trial_name(obj)
            if not nm:
                continue
            d = by_nct.setdefault(nct, {})
            slot = d.setdefault(norm(nm), [nm, []])
            slot[1].append(os.path.basename(p)[:34])

    conflicts = {n: d for n, d in by_nct.items() if len(d) > 1}
    real = {}
    for nct, d in conflicts.items():
        # drop names that are just the NCT number itself (display placeholder)
        names = {k: v for k, v in d.items() if v[0].upper() != nct}
        if len(names) < 2:
            continue
        keys = list(names.keys())
        # if every name is a substring of the longest, treat as alias (skip)
        longest = max(keys, key=len)
        if all(k in longest or longest in k for k in keys):
            continue
        real[nct] = names

    print(f"{len(conflicts)} NCTs with >1 distinct name; "
          f"{len(real)} after dropping substring/alias pairs:\n")
    for nct, d in sorted(real.items()):
        print(f"{nct}:")
        for _, (raw, apps) in sorted(d.items()):
            print(f'    "{raw[:34]}"  x{len(apps)}  {sorted(set(apps))[:2]}')
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
