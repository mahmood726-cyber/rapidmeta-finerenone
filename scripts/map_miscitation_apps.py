#!/usr/bin/env python
"""For each candidate-miscitation NCT, show which app cites the DESIGN/SUB paper
and what outcome that record displays -- so we can tell a true miscitation
(results record citing a protocol) from a legitimate sub-study citation.
"""
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
DESIGN = re.compile(r"rationale|study design|design of|protocol|baseline charact"
                    r"|methodology|trial design", re.I)
SUB = re.compile(r"post.?hoc|subgroup|sub-study|substudy|exploratory"
                 r"|secondary analysis|long.term|extension|follow.up|\d+-year"
                 r"|open-label ext|pooled analysis|patient-reported"
                 r"|quality of life|health-related|economic|cost-eff", re.I)


def tag_of(p):
    t = M.get(p, {}).get("t", "")
    out = []
    if DESIGN.search(t):
        out.append("DESIGN")
    if SUB.search(t):
        out.append("SUB")
    return "/".join(out)


def otitle(obj):
    tl = obj.split("allOutcomes", 1)
    if len(tl) < 2:
        return ""
    m = re.search(r'title:"([^"]+)"', tl[1]) or re.search(r'"title":\s*"([^"]+)"', tl[1])
    return m.group(1) if m else ""


def otype(obj):
    tl = obj.split("allOutcomes", 1)
    if len(tl) < 2:
        return ""
    m = re.search(r'type:"([^"]+)"', tl[1]) or re.search(r'"type":\s*"([^"]+)"', tl[1])
    return m.group(1) if m else ""


conf = json.load(open(os.path.join(REPO, "outputs", "pmid_conflicts.json")))["conflicts"]
cand = {nct: ps for nct, ps in conf.items()
        if any(tag_of(p) for p in ps) and any(not tag_of(p) and p in M for p in ps)}

# nct -> pmid -> list of (app, outcome_title, outcome_type)
usage = {}
for p in sorted(glob.glob(os.path.join(REPO, "*_REVIEW*.html"))):
    if "backup" in p:
        continue
    html = open(p, encoding="utf-8", errors="replace").read()
    for key, obj in dia.find_trial_objects(html):
        nct = key.split("_")[0]
        if nct not in cand:
            continue
        pmid = str(dia.str_field(obj, "pmid"))
        usage.setdefault(nct, {}).setdefault(pmid, []).append(
            (os.path.basename(p), otitle(obj)[:54], otype(obj)))

for nct in sorted(cand):
    clean = [p for p in cand[nct] if not tag_of(p) and p in M]
    print(f"\n{nct}  (clean primary-results PMID candidate: {clean})")
    for pmid in cand[nct]:
        tg = tag_of(pmid) or ("clean" if pmid in M else "UNRESOLVED")
        print(f"  PMID {pmid} <{tg}> {M.get(pmid,{}).get('t','')[:58]}")
        for app, ot, oty in usage.get(nct, {}).get(pmid, []):
            print(f"       cited by {app[:40]:40} [{oty}] {ot}")
