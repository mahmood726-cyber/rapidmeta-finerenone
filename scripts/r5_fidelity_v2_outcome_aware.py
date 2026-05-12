"""Round 5 v2 — outcome-aware fidelity comparison.

Some published landmark trials have MULTIPLE primary/secondary outcomes,
each with its own HR/event counts. A review may legitimately extract any
of those outcomes depending on its scope. The v1 test only checked one
canonical outcome per trial, which flagged legitimate different-outcome
extractions as DIVERGE.

V2 adds OUTCOME ALTERNATES for each landmark trial and accepts a match
to ANY published outcome from that trial as EXACT_MATCH.
"""
from __future__ import annotations
import json, sys, io
from pathlib import Path
from collections import defaultdict

if hasattr(sys.stdout, "buffer") and getattr(sys.stdout, "encoding", "").lower() != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

HERE = Path(__file__).resolve().parent.parent
DATA = HERE / "outputs" / "extraction_audit" / "data"
OUT = HERE / "outputs" / "extraction_audit"

# Outcome alternates: each NCT maps to a list of published outcomes
GROUND_TRUTH = {
    "NCT00403767": [  # ROCKET AF
        {"outcome": "Stroke/SE, per-protocol (PRIMARY, prespecified)",
         "ref": "Patel NEJM 2011 PMID 21830957 DOI 10.1056/NEJMoa1009638",
         "tE": 188, "tN": 7081, "cE": 241, "cN": 7090,
         "hr": 0.79, "lci": 0.66, "uci": 0.96},
        {"outcome": "Stroke/SE, ITT-full-period (secondary sensitivity)",
         "ref": "Patel NEJM 2011 PMID 21830957",
         "tE": 269, "tN": 7081, "cE": 306, "cN": 7090,
         "hr": 0.88, "lci": 0.74, "uci": 1.03},
    ],
    "NCT00412984": [  # ARISTOTLE
        {"outcome": "Stroke/SE (primary)",
         "ref": "Granger NEJM 2011 PMID 21870978",
         "tE": 212, "tN": 9120, "cE": 265, "cN": 9081,
         "hr": 0.79, "lci": 0.66, "uci": 0.95},
    ],
    "NCT02540993": [  # FIDELIO-DKD
        {"outcome": "Renal composite (primary)",
         "ref": "Bakris NEJM 2020 PMID 33053267",
         "tE": 504, "tN": 2833, "cE": 600, "cN": 2841,
         "hr": 0.82, "lci": 0.73, "uci": 0.93},
        {"outcome": "CV composite (secondary)",
         "ref": "Bakris NEJM 2020 PMID 33053267",
         "tE": 367, "tN": 2833, "cE": 420, "cN": 2841,
         "hr": 0.86, "lci": 0.75, "uci": 0.99},
    ],
    "NCT02545049": [  # FIGARO-DKD
        {"outcome": "CV composite (primary)",
         "ref": "Pitt NEJM 2021 PMID 34449181",
         "tE": 458, "tN": 3686, "cE": 519, "cN": 3666,
         "hr": 0.87, "lci": 0.76, "uci": 0.98},
    ],
    "NCT04435626": [  # FINEARTS-HF
        {"outcome": "CV death + total worsening HF events (primary)",
         "ref": "Solomon NEJM 2024 PMID 39213776",
         "tE": 624, "tN": 3003, "cE": 719, "cN": 2998,
         "hr": 0.84, "lci": 0.74, "uci": 0.95},
    ],
    "NCT03036124": [  # DAPA-HF
        {"outcome": "CV death + HHF (primary)",
         "ref": "McMurray NEJM 2019 PMID 31535829",
         "tE": 386, "tN": 2373, "cE": 502, "cN": 2371,
         "hr": 0.74, "lci": 0.65, "uci": 0.85},
    ],
    "NCT03057977": [  # EMPEROR-Reduced
        {"outcome": "CV death + HHF (primary)",
         "ref": "Packer NEJM 2020 PMID 32865377",
         "tE": 361, "tN": 1863, "cE": 462, "cN": 1867,
         "hr": 0.75, "lci": 0.65, "uci": 0.86},
    ],
    "NCT03057951": [  # EMPEROR-Preserved
        {"outcome": "CV death + HHF (primary)",
         "ref": "Anker NEJM 2021 PMID 34449189",
         "tE": 415, "tN": 2997, "cE": 511, "cN": 2991,
         "hr": 0.79, "lci": 0.69, "uci": 0.90},
    ],
    "NCT03619213": [  # DELIVER
        {"outcome": "CV death + worsening HF event (primary)",
         "ref": "Solomon NEJM 2022 PMID 36027564",
         "tE": 512, "tN": 3131, "cE": 610, "cN": 3132,
         "hr": 0.82, "lci": 0.73, "uci": 0.92},
    ],
    "NCT01035255": [  # PARADIGM-HF
        {"outcome": "CV death + HHF (primary)",
         "ref": "McMurray NEJM 2014 PMID 25176015",
         "tE": 914, "tN": 4187, "cE": 1117, "cN": 4212,
         "hr": 0.80, "lci": 0.73, "uci": 0.87},
    ],
    "NCT02861534": [  # VICTORIA
        {"outcome": "CV death + HHF (primary)",
         "ref": "Armstrong NEJM 2020 PMID 32222134",
         "tE": 897, "tN": 2526, "cE": 972, "cN": 2524,
         "hr": 0.90, "lci": 0.82, "uci": 0.98},
    ],
    "NCT01131676": [  # EMPA-REG OUTCOME
        {"outcome": "3-point MACE (primary)",
         "ref": "Zinman NEJM 2015 PMID 26378978",
         "tE": 490, "tN": 4687, "cE": 282, "cN": 2333,
         "hr": 0.86, "lci": 0.74, "uci": 0.99},
    ],
    "NCT00089791": [  # FREEDOM (denosumab)
        {"outcome": "Vertebral fracture (PRIMARY)",
         "ref": "Cummings NEJM 2009 PMID 19671655",
         "tE": 86, "tN": 3902, "cE": 264, "cN": 3906,
         "hr": 0.32, "lci": 0.26, "uci": 0.41},
        {"outcome": "Hip fracture (key secondary)",
         "ref": "Cummings NEJM 2009 PMID 19671655",
         "hr": 0.60, "lci": 0.37, "uci": 0.97},
        {"outcome": "Nonvertebral fracture (key secondary)",
         "ref": "Cummings NEJM 2009 PMID 19671655",
         "hr": 0.80, "lci": 0.67, "uci": 0.95},
    ],
    "NCT00049829": [  # HORIZON-PFT
        {"outcome": "Vertebral fracture (PRIMARY)",
         "ref": "Black NEJM 2007 PMID 17476007",
         "hr": 0.30, "lci": 0.24, "uci": 0.38},
        {"outcome": "Hip fracture (key secondary)",
         "ref": "Black NEJM 2007 PMID 17476007",
         "hr": 0.59, "lci": 0.42, "uci": 0.83},
    ],
}

EFFECT_TOL_ABS = 0.01
EFFECT_TOL_REL = 0.05


def cmp_one_outcome(extracted: dict, gt_outcome: dict) -> dict:
    """Compare one extraction against one published outcome. Return match-info."""
    field_map = {"tE": "tE", "tN": "tN", "cE": "cE", "cN": "cN",
                 "hr": "publishedHR", "lci": "hrLCI", "uci": "hrUCI"}
    matches = 0
    mismatches = 0
    fields_compared = 0
    deltas = {}
    for gf, ef in field_map.items():
        gv = gt_outcome.get(gf); ev = extracted.get(ef)
        if gv is None or ev is None: continue
        fields_compared += 1
        try: gvf = float(gv); evf = float(ev)
        except: continue
        if gf in ("tE", "tN", "cE", "cN"):
            if int(gv) == int(ev):
                deltas[ef] = {"match": True}; matches += 1
            else:
                deltas[ef] = {"match": False, "extracted": int(ev), "published": int(gv)}
                mismatches += 1
        else:
            d = abs(gvf - evf)
            tol = max(EFFECT_TOL_ABS, EFFECT_TOL_REL * gvf)
            if d <= tol:
                deltas[ef] = {"match": True}; matches += 1
            else:
                deltas[ef] = {"match": False, "extracted": evf, "published": gvf,
                              "delta": round(evf-gvf, 4)}
                mismatches += 1
    return {"matches": matches, "mismatches": mismatches,
            "fields_compared": fields_compared, "deltas": deltas}


def best_match(extracted: dict, gt_outcomes: list[dict]) -> dict:
    """Return best-matching outcome among all alternates."""
    best = None
    for gt_o in gt_outcomes:
        cmp_ = cmp_one_outcome(extracted, gt_o)
        if cmp_["fields_compared"] == 0: continue
        score = cmp_["matches"] - cmp_["mismatches"]
        if best is None or score > best["score"]:
            best = {**cmp_, "outcome": gt_o["outcome"],
                    "ref": gt_o["ref"], "score": score}
    if best is None:
        return {"verdict": "no-comparable-fields"}
    n_cmp = best["fields_compared"]
    if best["mismatches"] == 0:
        best["verdict"] = "EXACT_MATCH"
    elif best["matches"] >= n_cmp * 0.75:
        best["verdict"] = "PARTIAL_MATCH"
    else:
        best["verdict"] = "DIVERGE"
    return best


all_results = []
for json_p in sorted(DATA.glob("*.json")):
    if json_p.name.startswith("_"): continue
    rv = json_p.stem
    try: d = json.loads(json_p.read_text(encoding="utf-8"))
    except: continue
    rd = d.get("realData") or {}
    if not isinstance(rd, dict): continue
    for nct, t in rd.items():
        if nct.startswith("NULLED:"): continue
        if nct not in GROUND_TRUTH: continue
        if not isinstance(t, dict): continue
        res = best_match(t, GROUND_TRUTH[nct])
        all_results.append({
            "review": rv, "nct": nct,
            "trial_name": GROUND_TRUTH[nct][0]["ref"].split(" ")[0],
            "matched_outcome": res.get("outcome"),
            "ref": res.get("ref"),
            "verdict": res.get("verdict"),
            "matches": res.get("matches", 0),
            "mismatches": res.get("mismatches", 0),
            "fields_compared": res.get("fields_compared", 0),
            "deltas": res.get("deltas", {}),
        })

# Counts
total = len(all_results)
exact = sum(1 for r in all_results if r["verdict"] == "EXACT_MATCH")
partial = sum(1 for r in all_results if r["verdict"] == "PARTIAL_MATCH")
diverge = sum(1 for r in all_results if r["verdict"] == "DIVERGE")

(OUT / "r5_fidelity_v2_results.json").write_text(
    json.dumps(all_results, indent=2, ensure_ascii=False), encoding="utf-8")

print("=" * 70)
print(f"R5 fidelity v2 — outcome-aware comparison")
print("=" * 70)
print(f"Occurrences compared: {total}")
print(f"  EXACT_MATCH:   {exact:3d} ({100*exact/max(total,1):.0f}%)")
print(f"  PARTIAL_MATCH: {partial:3d} ({100*partial/max(total,1):.0f}%)")
print(f"  DIVERGE:       {diverge:3d} ({100*diverge/max(total,1):.0f}%)")
print()
print("Detail:")
for r in all_results:
    print(f"  [{r['verdict']:14s}] {r['nct']} in {r['review']:40s}  matched_to: {r['matched_outcome'][:60] if r['matched_outcome'] else '—'}")
    if r["verdict"] in ("PARTIAL_MATCH", "DIVERGE"):
        for fld, d in r["deltas"].items():
            if not d.get("match"):
                print(f"      {fld}: extracted={d.get('extracted')} published={d.get('published')} Δ={d.get('delta', d.get('extracted', 0) - d.get('published', 0))}")
