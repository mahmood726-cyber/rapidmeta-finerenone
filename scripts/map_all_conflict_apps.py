#!/usr/bin/env python
"""For every non-fixed cross-app PMID conflict, print each PMID with its resolved
title, the apps citing it, and the outcome each shows. Drives adjudication of the
wrong-trial citations the DESIGN/SUB heuristic missed (one PMID is the correct
trial primary; the sibling is an entirely unrelated paper)."""
import importlib.util
import glob
import json
import os
import re

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_spec = importlib.util.spec_from_file_location(
    "dia", os.path.join(REPO, "scripts", "data_integrity_audit.py"))
dia = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(dia)

M = json.load(open(os.path.join(REPO, "outputs", "pmid_meta.json"), encoding="utf-8"))
conf = json.load(open(os.path.join(REPO, "outputs", "pmid_conflicts.json")))["conflicts"]
FIXED = {"NCT00262600", "NCT00781391", "NCT01156571", "NCT01626079", "NCT01631214",
         "NCT01663402", "NCT01764633", "NCT01960348", "NCT02207231", "NCT02504216",
         "NCT02879305", "NCT02970942", "NCT03104400", "NCT03470545", "NCT03496298",
         "NCT03511664", "NCT02065791"}
rest = {n: p for n, p in conf.items() if n not in FIXED}


def otitle(obj):
    tl = obj.split("allOutcomes", 1)
    if len(tl) < 2:
        return ""
    m = re.search(r'title:"([^"]+)"', tl[1]) or re.search(r'"title":\s*"([^"]+)"', tl[1])
    return m.group(1) if m else ""


usage = {}
for p in sorted(glob.glob(os.path.join(REPO, "*_REVIEW*.html"))):
    if "backup" in p:
        continue
    html = open(p, encoding="utf-8", errors="replace").read()
    for key, obj in dia.find_trial_objects(html):
        nct = key.split("_")[0]
        if nct not in rest:
            continue
        pmid = str(dia.str_field(obj, "pmid"))
        usage.setdefault(nct, {}).setdefault(pmid, []).append(
            (os.path.basename(p)[:36], otitle(obj)[:42]))

for nct in sorted(rest):
    print(f"\n{nct}:")
    for pmid in rest[nct]:
        t = M.get(pmid, {}).get("t", "<UNRESOLVED>")
        print(f"  {pmid} [{M.get(pmid,{}).get('y','?')}] {t[:70]}")
        for app, ot in usage.get(nct, {}).get(pmid, []):
            print(f"        {app:36} {ot}")
