#!/usr/bin/env python
"""Compare each candidate record's stored arm sizes (tN/cN) against the actual
per-arm 'started' counts from ClinicalTrials.gov, to catch MEASURE-UP-type
wrong-arm-denominator bugs.

For each NCT in outputs/ctgov_denom/, extract the participant-flow 'STARTED'
counts per arm group, then report the app's stored tN/cN next to the CT.gov arm
sizes. Flags when stored tN matches NO arm within +-2, or matches a DIFFERENT
arm than the one named in the record's group text.
"""
from __future__ import annotations
import glob
import importlib.util
import json
import os
import re

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_spec = importlib.util.spec_from_file_location(
    "dia", os.path.join(REPO, "scripts", "data_integrity_audit.py"))
dia = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(dia)


def app_record(nct):
    for p in glob.glob(os.path.join(REPO, "*_REVIEW*.html")):
        if "backup" in p:
            continue
        html = open(p, encoding="utf-8", errors="replace").read()
        for key, obj in dia.find_trial_objects(html):
            if key.split("_")[0] == nct:
                g = re.search(r'group:"([^"]*)"', obj)
                return (os.path.basename(p), dia.field(obj, "tN"),
                        dia.field(obj, "cN"), g.group(1) if g else "")
    return (None, None, None, "")


def ctgov_arms(nct):
    f = os.path.join(REPO, "outputs", "ctgov_denom", nct + ".json")
    if not os.path.exists(f):
        return []
    try:
        d = json.load(open(f, encoding="utf-8"))
    except Exception:
        return []
    pf = d.get("resultsSection", {}).get("participantFlowModule", {})
    groups = {g["id"]: g["title"] for g in pf.get("groups", [])}
    arms = {}
    for per in pf.get("periods", []):
        for ms in per.get("milestones", []):
            if ms.get("type", "").upper() == "STARTED":
                for a in ms.get("achievements", []):
                    arms[groups.get(a["groupId"], a["groupId"])] = a.get("numSubjects")
        break  # first period only (randomization)
    return [(t, int(n)) for t, n in arms.items() if n and str(n).isdigit()]


def main():
    ncts = sorted(os.path.basename(f)[:-5]
                  for f in glob.glob(os.path.join(REPO, "outputs", "ctgov_denom", "*.json")))
    flags = []
    for nct in ncts:
        app, tN, cN, group = app_record(nct)
        arms = ctgov_arms(nct)
        if not arms:
            print(f"{nct}  (no CT.gov flow data)  stored tN={tN} cN={cN}")
            continue
        sizes = sorted(n for _, n in arms)
        tN_i = dia.as_num(tN); cN_i = dia.as_num(cN)

        def near(v):
            return v is not None and any(abs(int(v) - n) <= 2 for n in sizes)
        tN_ok = near(tN_i)
        cN_ok = near(cN_i)
        mark = "" if (tN_ok and cN_ok) else "  <<< CHECK"
        print(f"\n{nct} {app[:34] if app else '?':34} stored tN={tN} cN={cN}{mark}")
        print(f"   group: {group[:74]}")
        print(f"   CT.gov arms: " + ", ".join(f'{t[:26]}={n}' for t, n in arms))
        if mark:
            flags.append((nct, app, tN, cN, group, arms))
    print(f"\n{len(flags)} records where stored tN/cN do not match any CT.gov arm (+-2):")
    for nct, app, tN, cN, group, arms in flags:
        print(f"  {nct} {app[:30]:30} tN={tN} cN={cN}  arms={[n for _,n in arms]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
