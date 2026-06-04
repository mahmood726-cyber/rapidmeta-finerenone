#!/usr/bin/env python
"""Fix PEARL-1 / PEARL-2 ligelizumab records in CHRONIC_URTICARIA_BIOLOGICS.

The records compare ligelizumab 120 mg vs omalizumab (UAS7=0 at week 12) but
stored 502/501 and 498/498 -- denominators that match no real arm -- AND effect
values (1.26, 1.23) that show false superiority. Per ClinicalTrials.gov results
(UAS7=0 responders, Lige 120 mg vs Omalizumab 300 mg):

  PEARL-1 (NCT03580356): Lige120 103/320 vs Oma 94/321  -> RR 1.10 [0.87, 1.39]
  PEARL-2 (NCT03580369): Lige120 104/322 vs Oma 116/318 -> RR 0.89 [0.71, 1.10]

This matches the trials' real outcome: ligelizumab did NOT beat omalizumab (PEARL
failed; ligelizumab was not approved). Fills tE/cE, corrects tN/cN and
baseline.n, and replaces the inflated effect+CI with the count-derived RR + Wald
log-RR CI. Object-scoped, binary-safe, asserting, idempotent.
"""
from __future__ import annotations
import importlib.util
import os

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(REPO, "CHRONIC_URTICARIA_BIOLOGICS_REVIEW.html")
_spec = importlib.util.spec_from_file_location(
    "dia", os.path.join(REPO, "scripts", "data_integrity_audit.py"))
dia = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(dia)

EDITS = {
    "NCT03580356": [  # PEARL-1
        ("baseline:{n:1003,age:42}", "baseline:{n:641,age:42}"),
        ("tE:null,tN:502,cE:null,cN:501", "tE:103,tN:320,cE:94,cN:321"),
        ("publishedHR:1.26,hrLCI:1.04,hrUCI:1.52", "publishedHR:1.1,hrLCI:0.87,hrUCI:1.39"),
        ('tE:null,cE:null,type:"PRIMARY",matchScore:95,effect:1.26,lci:1.04,uci:1.52',
         'tE:103,cE:94,type:"PRIMARY",matchScore:95,effect:1.1,lci:0.87,uci:1.39'),
    ],
    "NCT03580369": [  # PEARL-2
        ("baseline:{n:996,age:42}", "baseline:{n:640,age:42}"),
        ("tE:null,tN:498,cE:null,cN:498", "tE:104,tN:322,cE:116,cN:318"),
        ("publishedHR:1.23,hrLCI:1.02,hrUCI:1.49", "publishedHR:0.89,hrLCI:0.71,hrUCI:1.1"),
        ('tE:null,cE:null,type:"PRIMARY",matchScore:95,effect:1.23,lci:1.02,uci:1.49',
         'tE:104,cE:116,type:"PRIMARY",matchScore:95,effect:0.89,lci:0.71,uci:1.1'),
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
                assert new in new_obj, f"{nct}: neither old nor new for {old!r}"
                continue
            assert new_obj.count(old) == 1, f"{nct}: {old!r} not unique"
            new_obj = new_obj.replace(old, new, 1)
        if new_obj != obj:
            assert data.count(obj) == 1, f"{nct}: object not unique"
            data = data.replace(obj, new_obj, 1)
            total += 1
            print(f"fixed {nct}")
    open(PATH, "wb").write(data.encode("utf-8"))
    print(f"records updated: {total}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
