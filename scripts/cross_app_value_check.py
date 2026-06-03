#!/usr/bin/env python
"""Cross-app value consistency check (doubly-corroborated error finder).

A trial (NCT) often appears in several apps. When the SAME trial carries
different effect values across apps, at most one can be right. This finds the
high-confidence errors: cases where one app's value matches the CT.gov
source-verified value (outputs/pmid_resolver/nct_continuous.json) within
tolerance, but another app disagrees by >REL. The source-matching value is the
corroborated reference; the disagreeing app(s) are flagged as likely-wrong.

This reliably surfaces the "dedicated single-drug app is right, broad/NMA app is
wrong" pattern (e.g. RAISE, SIRIUS, EMBARK) without a per-trial literature
lookup -- the agreement of an independent app AND the registry is strong
evidence. Still verify against the primary before correcting.

Usage: python scripts/cross_app_value_check.py [--rel 0.05]
"""
from __future__ import annotations
import argparse
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


def outcome_est(obj):
    tail = obj.split("allOutcomes", 1)
    if len(tail) < 2:
        return None
    m = re.search(r'estimandType:"([^"]+)"', tail[1])
    return m.group(1).upper() if m else None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--rel", type=float, default=0.05)
    args = ap.parse_args()

    # nct -> list of (app, value, est)
    by_nct = {}
    for p in sorted(glob.glob(os.path.join(REPO, "*_REVIEW*.html"))):
        html = open(p, encoding="utf-8", errors="replace").read()
        for key, obj in dia.find_trial_objects(html):
            v = dia.as_num(dia.field(obj, "publishedHR"))
            if v is None:
                continue
            by_nct.setdefault(key.split("_")[0], []).append(
                (os.path.basename(p), v, outcome_est(obj)))

    flagged = []
    for nct, entries in by_nct.items():
        vals = {round(v, 4) for _, v, _ in entries}
        if len(vals) < 2:
            continue  # all apps agree
        info = CONT.get(nct, {})
        src = info.get("effect")
        src_kind = str(info.get("kind", "")).upper()
        if src is None or abs(src) < 0.1:
            continue  # near-zero/degenerate source -> spurious % differences
        # apps whose value matches the source = corroborated reference
        matching = [e for e in entries if abs(e[1] - src) / max(1e-9, abs(src)) <= args.rel]
        if not matching:
            continue
        ref = matching[0][1]
        wrong = [e for e in entries if abs(e[1] - ref) / max(1e-9, abs(ref)) > args.rel]
        for app, v, est in wrong:
            # Measure-consistency: only flag when this app's measure matches the
            # source kind. A different measure (e.g. responder RR vs the MD the
            # source reports) is a different OUTCOME, not a value error.
            if est and src_kind and est != src_kind:
                continue
            flagged.append({
                "nct": nct, "wrong_app": app, "wrong_val": v, "est": est,
                "ref_val": ref, "src_val": src,
                "ref_apps": ",".join(a for a, vv, _ in matching),
            })

    flagged.sort(key=lambda f: -abs(f["wrong_val"] - f["ref_val"]) / max(1e-9, abs(f["ref_val"])))
    print(f"{len(flagged)} doubly-corroborated cross-app value mismatches "
          f"(another app + CT.gov source agree; this app disagrees):\n")
    for f in flagged:
        rel = abs(f["wrong_val"] - f["ref_val"]) / max(1e-9, abs(f["ref_val"]))
        print(f"  {f['nct']}  {f['wrong_app'][:38]:38} {f['wrong_val']:>8}  "
              f"vs ref {f['ref_val']:>8} ({rel*100:.0f}% off; src={f['src_val']}, ref_apps={f['ref_apps'][:40]})")
    return 0


if __name__ == "__main__":
    main()
