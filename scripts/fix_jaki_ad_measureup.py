#!/usr/bin/env python
"""Fix MEASURE-UP 1 & 2 records in JAKI_AD_REVIEW.html.

Both records analyse the upadacitinib 30 mg vs placebo comparison (vIGA-AD 0/1
with >=2-grade improvement at week 16) but had null event counts AND the wrong
arm denominator (the 15 mg arm n, not the 30 mg n). Counts sourced from the
primary: Guttman-Yassky et al, Lancet 2021;397:2151-2168 (NCT03569293 MEASURE
UP 1, NCT03607422 MEASURE UP 2), DOI 10.1016/S0140-6736(21)00588-2:

  MU1 30 mg: 177/285 vIGA-AD response; placebo 24/281
  MU2 30 mg: 147/282 vIGA-AD response; placebo 13/278

Also repoints both PMIDs to the primary (MU1 had the 52-wk follow-up 35262646;
MU2 had null + a snippet mis-citing the AD Up paper), and corrects MU2's outcome
estimandType OR->RR (the value 11.16 is the risk ratio; crude RR from the counts
= 11.15). Effect values left as the published adjusted RRs (7.43, 11.16).

Object-scoped, binary-safe, asserting, idempotent.
"""
from __future__ import annotations
import importlib.util
import os

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(REPO, "JAKI_AD_REVIEW.html")
_spec = importlib.util.spec_from_file_location(
    "dia", os.path.join(REPO, "scripts", "data_integrity_audit.py"))
dia = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(dia)

# nct -> list of (old, new) replacements applied WITHIN that trial object
EDITS = {
    "NCT03569293": [  # MEASURE-UP 1
        ("tE:null,tN:281,cE:null,cN:281", "tE:177,tN:285,cE:24,cN:281"),
        ('tE:null,cE:null,type:"PRIMARY"', 'tE:177,cE:24,type:"PRIMARY"'),
        ('pmid:"35262646"', 'pmid:"34023008"'),
    ],
    "NCT03607422": [  # MEASURE-UP 2
        ("tE:null,tN:276,cE:null,cN:278", "tE:147,tN:282,cE:13,cN:278"),
        ('tE:null,cE:null,type:"PRIMARY"', 'tE:147,cE:13,type:"PRIMARY"'),
        ("pmid:null", 'pmid:"34023008"'),
        ('uci:19.18,estimandType:"OR"', 'uci:19.18,estimandType:"RR"'),
    ],
}


def main():
    data = open(PATH, "rb").read().decode("utf-8", "replace")
    total = 0
    for key, obj in dia.find_trial_objects(data):
        nct = key.split("_")[0]
        edits = EDITS.get(nct)
        if not edits:
            continue
        new_obj = obj
        for old, new in edits:
            if old not in new_obj:
                # idempotent: maybe already applied; verify the new value is present
                assert new in new_obj, f"{nct}: neither old nor new present for {old!r}"
                continue
            assert new_obj.count(old) == 1, f"{nct}: {old!r} not unique in object"
            new_obj = new_obj.replace(old, new, 1)
        if new_obj != obj:
            assert data.count(obj) == 1, f"{nct}: object not unique in file"
            data = data.replace(obj, new_obj, 1)
            total += 1
            print(f"updated {nct}")
    open(PATH, "wb").write(data.encode("utf-8"))
    print(f"records updated: {total}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
