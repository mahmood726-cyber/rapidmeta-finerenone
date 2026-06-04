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


def is_nulled(html: str, nct: str, obj: str):
    """True if this trial object is keyed under a NULLED:<nct> prefix.
    The key '"NULLED:NCTxxxxxxxx":' sits immediately before the object's '{'."""
    idx = html.find(obj)
    if idx < 0:
        return False
    return ("NULLED:" + nct) in html[max(0, idx - 40):idx]


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
            nulled = is_nulled(html, nct, obj)
            d = by_nct.setdefault(nct, {})
            slot = d.setdefault(norm(nm), [nm, [], True])
            slot[1].append(os.path.basename(p)[:34])
            if not nulled:
                slot[2] = False  # at least one LIVE record with this name

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

    # a conflict is LIVE-vs-LIVE (can corrupt a meta-analysis) only if >=2
    # distinct names each have at least one non-NULLED record.
    live_conf = {nct: d for nct, d in real.items()
                 if sum(0 if v[2] else 1 for v in d.values()) >= 2}

    print(f"{len(conflicts)} NCTs with >1 distinct name; {len(real)} real "
          f"(non-alias); {len(live_conf)} are LIVE-vs-LIVE (the serious set):\n")
    print("=== LIVE-vs-LIVE (different names, both contributing to a pooled MA) ===")
    for nct, d in sorted(live_conf.items()):
        print(f"{nct}:")
        for _, (raw, apps, nulled) in sorted(d.items()):
            tag = "NULLED" if nulled else "LIVE"
            print(f'    [{tag:6}] "{raw[:32]}"  x{len(apps)}  {sorted(set(apps))[:2]}')
    print("\n=== remaining (>=1 side already NULLED/inert -- metadata only) ===")
    for nct, d in sorted(real.items()):
        if nct in live_conf:
            continue
        names = " | ".join(f'{v[0][:20]}({"N" if v[2] else "L"})' for v in d.values())
        print(f"  {nct}: {names}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
