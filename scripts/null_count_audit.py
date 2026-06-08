#!/usr/bin/env python
"""Portfolio scan for the JAKI_AD defect class: binary-outcome trial records that
have a non-null effect but a degenerate / incomplete 2x2 -- the "0/0 and N/N"
look the user spotted (null event counts with present arm sizes).

Flags, per app, trial records where estimandType is a count measure
(RR/OR/HR/IRR) AND the effect (publishedHR) is non-null, but the 2x2 is broken:
  * NULL_EVENTS   tE or cE is null/absent while tN and cN are present
  * ZERO_EVENTS   tE==0 and cE==0 (no events in either arm -> uninformative)
  * EQUAL_ARMS_NULL  tN==cN AND events null (the exact MEASURE-UP shape)

A flag is a data-quality smell, not always an error (some effects are legitimately
published-only without a 2x2). Verify against the primary before filling.

Usage: python scripts/null_count_audit.py [--glob '*_REVIEW*.html']
"""
from __future__ import annotations
import argparse
import glob
import importlib.util
import os
import re

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_spec = importlib.util.spec_from_file_location(
    "dia", os.path.join(REPO, "scripts", "data_integrity_audit.py"))
dia = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(dia)

COUNT_MEASURES = {"RR", "OR", "HR", "IRR", "PETO_OR"}


def est_of(obj):
    m = re.search(r'estimandType:"([^"]+)"', obj)
    return m.group(1).upper() if m else ""


def name_of(obj):
    m = re.search(r'name:"([^"]+)"', obj) or re.search(r'"name":\s*"([^"]+)"', obj)
    return m.group(1) if m else "?"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--glob", default="*_REVIEW*.html")
    args = ap.parse_args()

    by_app = {}
    for p in sorted(glob.glob(os.path.join(REPO, args.glob))):
        if "backup" in p:
            continue
        html = open(p, encoding="utf-8", errors="replace").read()
        for key, obj in dia.find_trial_objects(html):
            est = est_of(obj)
            if est not in COUNT_MEASURES:
                continue
            eff = dia.as_num(dia.field(obj, "publishedHR"))
            if eff is None:
                continue
            tE = dia.field(obj, "tE"); cE = dia.field(obj, "cE")
            tN = dia.field(obj, "tN"); cN = dia.field(obj, "cN")

            def isnull(v):
                return v is None or str(v).strip().lower() in ("null", "", "none")

            flag = None
            if (isnull(tE) or isnull(cE)) and not isnull(tN) and not isnull(cN):
                flag = "NULL_EVENTS"
                if str(tN) == str(cN):
                    flag = "EQUAL_ARMS_NULL"
            elif (not isnull(tE) and not isnull(cE)
                  and dia.as_num(tE) == 0 and dia.as_num(cE) == 0):
                flag = "ZERO_EVENTS"
            if not flag:
                continue
            # A degenerate 2x2 is NOT a defect when the trial carries a published
            # effect + CI: the engine pools it via generic inverse-variance on the
            # log-effect with SE derived from the CI (and shows Mantel-Haenszel OR
            # as "N/A - missing event counts"). Only a missing CI -> no derivable
            # SE -> genuinely unpoolable.
            lci = dia.as_num(dia.field(obj, "hrLCI"))
            uci = dia.as_num(dia.field(obj, "hrUCI"))
            poolable = lci is not None and uci is not None
            bucket = "valid_IV" if poolable else "unpoolable"
            by_app.setdefault(os.path.basename(p), []).append(
                (key.split("_")[0], name_of(obj)[:22], flag, bucket,
                 f"{tE}/{tN} vs {cE}/{cN}", est, eff))

    total = sum(len(v) for v in by_app.values())
    valid = sum(1 for v in by_app.values() for r in v if r[3] == "valid_IV")
    bad = total - valid
    print(f"{total} trials with a degenerate 2x2 across {len(by_app)} apps.")
    print(f"  valid_IV   (published effect + CI -> generic-IV poolable): {valid}")
    print(f"  unpoolable (no CI -> no derivable SE, engine skips):       {bad}\n")
    print("GENUINELY UNPOOLABLE (no CI) -- verify these are intended placeholder "
          "nodes for registered-but-unreported trials, not extraction gaps:\n")
    for app in sorted(by_app):
        rows = [r for r in by_app[app] if r[3] == "unpoolable"]
        if not rows:
            continue
        print(app)
        for nct, nm, flag, bucket, twoby2, est, eff in rows:
            print(f"   [{flag:15}] {nct} {nm:22} {est:3} eff={eff}  2x2={twoby2}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
