#!/usr/bin/env python
"""Triage report: app effect value vs CT.gov source, where they disagree.

For every trial whose non-null effect (publishedHR) disagrees with the
source-verified value in outputs/pmid_resolver/nct_continuous.json by >5%, and
where the measures match (outcome estimandType == source kind), emit a row with
both values, both CIs, the outcome title, and a category:

  SIGNFLIP    opposite sign (MD/RD) -- direction differs
  RECIPROCAL  ratio ~= 1/source -- CT.gov posted the inverse comparison
  EXTREME     >100% relative difference
  MODERATE    25-100%
  MILD        5-25%

IMPORTANT -- this is a REVIEW aid, not an auto-fix list. Empirically most
disagreements are NOT app errors: CT.gov's posted analysis is frequently a
different outcome / timepoint / arm / parameterization, or the inverse
direction, and the app value is the correct published primary (e.g. T1D
TIR +12% vs a 0.19 source; gastric OS HR 0.82 vs a 1.27 inverse). Correcting
these to the source would re-introduce errors. Genuine fixes require per-trial
verification against the SAME outcome in the primary publication.

Usage: python scripts/source_disagreement_report.py [--out outputs/source_disagreements.csv]
"""
from __future__ import annotations
import argparse
import csv
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
CONT = json.load(open(os.path.join(REPO, "outputs", "pmid_resolver", "nct_continuous.json"),
                     encoding="utf-8"))


def outcome_field(obj, name):
    tail = obj.split("allOutcomes", 1)
    if len(tail) < 2:
        return None
    m = re.search(name + r':"([^"]+)"', tail[1])
    return m.group(1) if m else None


def categorize(est, app, src, rel):
    if est in ("MD", "SMD", "WMD", "RD") and abs(app) > 1e-6 and abs(src) > 1e-6 and (app < 0) != (src < 0):
        return "SIGNFLIP"
    if est in ("HR", "OR", "RR", "IRR") and app > 0 and src > 0 and abs(app - 1.0 / src) / max(1e-9, 1.0 / src) < 0.1:
        return "RECIPROCAL"
    if rel > 1.0:
        return "EXTREME"
    if rel > 0.25:
        return "MODERATE"
    return "MILD"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="outputs/source_disagreements.csv")
    args = ap.parse_args()

    rows = []
    seen = set()
    for p in sorted(glob.glob(os.path.join(REPO, "*_REVIEW*.html"))):
        html = open(p, encoding="utf-8", errors="replace").read()
        for key, obj in dia.find_trial_objects(html):
            app = dia.as_num(dia.field(obj, "publishedHR"))
            if app is None:
                continue
            nct = key.split("_")[0]
            e = CONT.get(nct)
            if not e or e.get("effect") is None:
                continue
            est = (outcome_field(obj, "estimandType") or "").upper()
            if est != str(e.get("kind", "")).upper():
                continue  # only compare like-for-like measures
            src = e["effect"]
            rel = abs(app - src) / max(1e-9, abs(src))
            if rel <= 0.05 or (nct, est) in seen:
                continue
            seen.add((nct, est))
            rows.append({
                "cat": categorize(est, app, src, rel),
                "rel_pct": round(rel * 100),
                "app": os.path.basename(p).replace("_AUTO_FULL_REVIEW.html", "").replace("_REVIEW.html", ""),
                "nct": nct, "est": est,
                "app_val": app, "app_lci": dia.field(obj, "hrLCI"), "app_uci": dia.field(obj, "hrUCI"),
                "src_val": src, "src_lci": e.get("lci"), "src_uci": e.get("uci"),
                "src_origin": e.get("source", ""),
                "outcome_title": (outcome_field(obj, "title") or "")[:80],
            })
    order = {"SIGNFLIP": 4, "RECIPROCAL": 3, "EXTREME": 2, "MODERATE": 1, "MILD": 0}
    rows.sort(key=lambda r: (-order[r["cat"]], -r["rel_pct"]))

    out = os.path.join(REPO, args.out)
    with open(out, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    from collections import Counter
    c = Counter(r["cat"] for r in rows)
    print(f"{len(rows)} measure-matched disagreements (>5%). By category: {dict(c)}")
    print(f"Wrote {args.out}")
    print("NOTE: review aid only -- most disagreements are different-outcome/inverse, "
          "not app errors. Do not bulk-correct to source.")


if __name__ == "__main__":
    main()
