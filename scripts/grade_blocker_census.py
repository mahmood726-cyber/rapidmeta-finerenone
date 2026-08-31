# -*- coding: utf-8 -*-
"""WHY the certainty ratings are refused, counted, with the denominator on every line.

⭐ THE FINDING THIS EXISTS TO KEEP REPRODUCIBLE, measured 2026-08-30:

    D1  72/75  96%   NO_INFORMATION
    D2  72/75  96%
    D3  72/75  96%
    D4   4/75   5%
    D5   9/75  12%

Three of the five RoB 2 domains are NO INFORMATION on almost every assessed result, and
the objects say why in their own `sources_NOT_read` field: "The trial publications. D2 and
D3 depend on..." -- the assessments were made from ClinicalTrials.gov registration records,
and a registration does not carry allocation concealment, the analysis population actually
used, or how missing outcome data were handled.

⚠️ SO THE BOTTLENECK IS NOT ASSESSMENT EFFORT, IT IS RETRIEVAL. Our risk-of-bias work is
not weak; it is SOURCE-BOUNDED, and this script says by exactly how much and which
document would lift it. That distinction is the whole difference between "we judged these
trials and had concerns" and "we could not find out" -- and a published review that scores
SOME CONCERNS from a registration alone has made the first claim while only being entitled
to the second.

⭐ WHICH IS ALSO WHY THIS IS WORTH PRINTING RATHER THAN FIXING QUIETLY. A reader can check
it, it is unflattering, and nobody else reports it.

THE COUNTERFACTUAL, same run: of 54 live pooled results, supplying indirectness alone
would rate 4, risk of bias alone would rate 0 (indirectness still blocks every one), and
both together would rate 31. Those are the only two inputs that matter, and one of them is
a retrieval job with a named document per trial.
"""
import collections
import io
import json
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, "..", "ssot"))

import grade_engine as ge          # noqa: E402
from rob_block import rob_block    # noqa: E402


def census(page_map="ssot/PAGE_MAP.json"):
    objs = sorted(set(json.load(open(page_map, encoding="utf-8")).values()))
    out = {
        "objects": len(objs), "by_outcome": 0, "withdrawn": 0, "live": 0,
        "states": collections.Counter(),
        "rob_refusal_reasons": collections.Counter(),
        "domain_no_information": collections.Counter(),
        "domain_total": collections.Counter(),
        "counterfactual": collections.Counter(),
        "bounds": collections.Counter(),
        "entailed": 0,
    }
    for p in objs:
        o = json.load(open(p, encoding="utf-8"))
        b = rob_block(o)
        if b:
            for t in (b.get("trials") or []):
                for d in (t.get("domains") or []):
                    nm = (d.get("domain") or "?")[:2]
                    out["domain_total"][nm] += 1
                    js = [str(x).upper() for x in (d.get("judgements") or []) if x]
                    if any("NO_INFORMATION" in x for x in js):
                        out["domain_no_information"][nm] += 1
        for oid, r in ((o.get("results") or {}).get("by_outcome") or {}).items():
            if not isinstance(r, dict):
                continue
            out["by_outcome"] += 1
            pooled = r.get("pooled") if isinstance(r.get("pooled"), dict) else {}
            if pooled.get("withdrawn"):
                out["withdrawn"] += 1
                continue
            out["live"] += 1
            rec = ge.derive(o, oid)
            out["states"][rec["state"]] += 1
            ref = set(rec.get("refused_domains") or [])
            # ⚠️ SUBSET, NOT MEMBERSHIP. "would be rated if we supplied X" means every
            # refusal it has is inside X -- not merely that X is among them. Getting this
            # wrong would count a result blocked by three domains as unblocked by one.
            if ref <= {"indirectness"}:
                out["counterfactual"]["indirectness_only"] += 1
            if ref <= {"risk_of_bias"}:
                out["counterfactual"]["risk_of_bias_only"] += 1
            if ref <= {"indirectness", "risk_of_bias"}:
                out["counterfactual"]["both"] += 1
            bd = rec.get("certainty_bounds") or {}
            if bd:
                out["bounds"][(bd["best_case"], bd["worst_case"])] += 1
                if bd.get("entailed"):
                    out["entailed"] += 1
            d = next((x for x in (rec.get("domains") or [])
                      if x["domain"] == "risk_of_bias"), None)
            if d and d["state"] == ge.REFUSED:
                m = " ".join(d.get("inputs_missing") or [])
                if "adjudication" in m:
                    key = "unadjudicated disagreement"
                elif "NO_INFORMATION" in m:
                    key = "an assessor recorded NO_INFORMATION"
                elif "by_outcome" in m:
                    key = "assessed, but not for this outcome"
                elif "readable" in m:
                    key = "unreadable verdict"
                else:
                    key = "no risk-of-bias assessment at all"
                out["rob_refusal_reasons"][key] += 1
    return out


def main():
    c = census()
    live = c["live"]
    print("GRADE BLOCKER CENSUS")
    print("  objects                        : %d" % c["objects"])
    print("  by_outcome results             : %d" % c["by_outcome"])
    print("  WITHDRAWN (no estimate to rate): %d/%d" % (c["withdrawn"], c["by_outcome"]))
    print("  LIVE -- the real denominator   : %d/%d" % (live, c["by_outcome"]))
    print()
    print("  states:")
    for k, v in c["states"].most_common():
        print("     %-18s %d/%d" % (k, v, live))
    print()
    print("WHY RISK OF BIAS REFUSES (%d of %d live):"
          % (sum(c["rob_refusal_reasons"].values()), live))
    for k, v in c["rob_refusal_reasons"].most_common():
        print("     %-36s %d" % (k, v))
    print()
    print("NO_INFORMATION BY RoB 2 DOMAIN -- the retrieval diagnosis:")
    for k in sorted(c["domain_total"]):
        n, d = c["domain_no_information"].get(k, 0), c["domain_total"][k]
        print("     %-4s %3d/%3d  %3.0f%%" % (k, n, d, 100.0 * n / d if d else 0))
    print("     D1/D2/D3 are what a registration cannot answer; D4/D5 are what it can.")
    print()
    print("CERTAINTY BOUNDS over the live results:")
    for (a, z), n in c["bounds"].most_common():
        print("     %-10s .. %-10s %d" % (a, z, n))
    print("     entailed (the letter is determined despite the refusal): %d/%d"
          % (c["entailed"], live))
    print()
    print("COUNTERFACTUAL -- results that would be RATED if we supplied:")
    for k in ("indirectness_only", "risk_of_bias_only", "both"):
        print("     %-22s %d/%d" % (k, c["counterfactual"].get(k, 0), live))


if __name__ == "__main__":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    main()
