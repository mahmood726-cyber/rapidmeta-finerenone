#!/usr/bin/env python
"""Find records at risk of the MEASURE-UP wrong-denominator bug: a binary
(RR/OR) outcome that selects a SPECIFIC dose arm of a multi-dose trial but whose
stored arm size (tN) may belong to a different dose arm.

Signature: estimandType in {RR,OR}, effect present, group/title names a dose
("NN mg" / "high-dose" / "NNmg arm"), and a 2x2 denominator is present. These
are exactly the records where picking the wrong arm's N is easy. Output drives a
targeted CT.gov arm-size verification.

Usage: python scripts/denominator_candidates.py
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

DOSE = re.compile(r"\b\d{1,4}\s?mg\b|high[- ]dose|higher[- ]dose|top dose", re.I)
COUNT_EST = {"RR", "OR"}


def field_after(obj, name):
    m = re.search(name + r':"([^"]*)"', obj)
    return m.group(1) if m else ""


def main():
    rows = []
    for p in sorted(glob.glob(os.path.join(REPO, "*_REVIEW*.html"))):
        if "backup" in p:
            continue
        html = open(p, encoding="utf-8", errors="replace").read()
        for key, obj in dia.find_trial_objects(html):
            est = (re.search(r'estimandType:"([^"]+)"', obj) or [None, ""])
            est = est.group(1).upper() if hasattr(est, "group") else ""
            if est not in COUNT_EST:
                continue
            eff = dia.as_num(dia.field(obj, "publishedHR"))
            if eff is None:
                continue
            group = field_after(obj, "group")
            title = ""
            tl = obj.split("allOutcomes", 1)
            if len(tl) > 1:
                mt = re.search(r'title:"([^"]+)"', tl[1])
                title = mt.group(1) if mt else ""
            ctx = group + " | " + title
            if not DOSE.search(ctx):
                continue
            tN = dia.field(obj, "tN"); cN = dia.field(obj, "cN")
            tE = dia.field(obj, "tE"); cE = dia.field(obj, "cE")
            nm = re.search(r'name:"([^"]+)"', obj)
            rows.append((key.split("_")[0], nm.group(1)[:20] if nm else "?",
                         os.path.basename(p)[:30], est, eff,
                         f"{tE}/{tN} vs {cE}/{cN}", ctx[:70]))

    # de-dup by (nct) keeping first; but list all for review
    print(f"{len(rows)} dose-specific RR/OR records (MEASURE-UP-bug-prone):\n")
    seen = set()
    uniq = []
    for r in rows:
        if r[0] in seen:
            continue
        seen.add(r[0])
        uniq.append(r)
    print(f"{len(uniq)} unique NCTs:\n")
    for nct, nm, app, est, eff, twoby2, ctx in uniq:
        print(f"  {nct} {nm:20} {est} {twoby2:22} | {ctx}")
    # emit just the NCTs for batch CT.gov fetch
    print("\nNCTS=" + ",".join(r[0] for r in uniq))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
