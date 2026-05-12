"""Round 5 — Empirical fidelity test against published primary outcomes.

For each landmark trial in our ground-truth list, find every occurrence
across the 412-review corpus and compare extracted (tE, tN, cE, cN,
publishedHR, hrLCI, hrUCI) against the published primary-outcome values.

Ground truth source: NEJM / Lancet primary publications (cited per trial).
Tolerances:
  - Event counts: exact match (integer) — anything off is an error
  - HR / CI bounds: |Δ| ≤ 0.01 OR ≤ 5% relative (whichever larger) — accounting for
    rounding in published HRs ("0.74 (0.65-0.85)" → 0.736-0.744)

Output:
  outputs/extraction_audit/r5_fidelity_results.json
  outputs/extraction_audit/r5_fidelity_results.csv
  outputs/extraction_audit/R5_FIDELITY_REPORT.md
"""
from __future__ import annotations
import json, csv, sys, io
from pathlib import Path
from collections import defaultdict

if hasattr(sys.stdout, "buffer") and getattr(sys.stdout, "encoding", "").lower() != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

HERE = Path(__file__).resolve().parent.parent
DATA = HERE / "outputs" / "extraction_audit" / "data"
OUT = HERE / "outputs" / "extraction_audit"

# ─────────── Ground truth — published primary outcomes ───────────
# Each entry: nct → {name, ref, pmid, doi, tE, tN, cE, cN, hr, lci, uci, outcome}
# References cited per PubMed attribution policy.
GROUND_TRUTH = {
    # HF / cardiology
    "NCT03036124": {
        "name": "DAPA-HF", "ref": "McMurray NEJM 2019", "pmid": "31535829",
        "doi": "10.1056/NEJMoa1911303",
        "outcome": "CV death + HHF (primary)",
        "tE": 386, "tN": 2373, "cE": 502, "cN": 2371,
        "hr": 0.74, "lci": 0.65, "uci": 0.85,
    },
    "NCT03057977": {
        "name": "EMPEROR-Reduced", "ref": "Packer NEJM 2020", "pmid": "32865377",
        "doi": "10.1056/NEJMoa2022190",
        "outcome": "CV death + HHF (primary)",
        "tE": 361, "tN": 1863, "cE": 462, "cN": 1867,
        "hr": 0.75, "lci": 0.65, "uci": 0.86,
    },
    "NCT03057951": {
        "name": "EMPEROR-Preserved", "ref": "Anker NEJM 2021", "pmid": "34449189",
        "doi": "10.1056/NEJMoa2107038",
        "outcome": "CV death + HHF (primary)",
        "tE": 415, "tN": 2997, "cE": 511, "cN": 2991,
        "hr": 0.79, "lci": 0.69, "uci": 0.90,
    },
    "NCT03619213": {
        "name": "DELIVER", "ref": "Solomon NEJM 2022", "pmid": "36027564",
        "doi": "10.1056/NEJMoa2206286",
        "outcome": "CV death + worsening HF event (primary)",
        "tE": 512, "tN": 3131, "cE": 610, "cN": 3132,
        "hr": 0.82, "lci": 0.73, "uci": 0.92,
    },
    "NCT01035255": {
        "name": "PARADIGM-HF", "ref": "McMurray NEJM 2014", "pmid": "25176015",
        "doi": "10.1056/NEJMoa1409077",
        "outcome": "CV death + HHF (primary)",
        "tE": 914, "tN": 4187, "cE": 1117, "cN": 4212,
        "hr": 0.80, "lci": 0.73, "uci": 0.87,
    },
    "NCT02861534": {
        "name": "VICTORIA", "ref": "Armstrong NEJM 2020", "pmid": "32222134",
        "doi": "10.1056/NEJMoa1915928",
        "outcome": "CV death + HHF (primary)",
        "tE": 897, "tN": 2526, "cE": 972, "cN": 2524,
        "hr": 0.90, "lci": 0.82, "uci": 0.98,
    },
    "NCT02540993": {
        "name": "FIDELIO-DKD", "ref": "Bakris NEJM 2020", "pmid": "33053267",
        "doi": "10.1056/NEJMoa2025845",
        "outcome": "Renal composite (primary)",
        "tE": 504, "tN": 2833, "cE": 600, "cN": 2841,
        "hr": 0.82, "lci": 0.73, "uci": 0.93,
    },
    "NCT02545049": {
        "name": "FIGARO-DKD", "ref": "Pitt NEJM 2021", "pmid": "34449181",
        "doi": "10.1056/NEJMoa2110956",
        "outcome": "CV composite (primary)",
        "tE": 458, "tN": 3686, "cE": 519, "cN": 3666,
        "hr": 0.87, "lci": 0.76, "uci": 0.98,
    },
    "NCT04435626": {
        "name": "FINEARTS-HF", "ref": "Solomon NEJM 2024", "pmid": "39213776",
        "doi": "10.1056/NEJMoa2407107",
        "outcome": "CV death + worsening HF events (primary)",
        "tE": 624, "tN": 3003, "cE": 719, "cN": 2998,
        "hr": 0.84, "lci": 0.74, "uci": 0.95,
    },
    "NCT01131676": {
        "name": "EMPA-REG OUTCOME", "ref": "Zinman NEJM 2015", "pmid": "26378978",
        "doi": "10.1056/NEJMoa1504720",
        "outcome": "3-point MACE (primary)",
        "tE": 490, "tN": 4687, "cE": 282, "cN": 2333,
        "hr": 0.86, "lci": 0.74, "uci": 0.99,
    },
    # Oncology landmark
    "NCT02853486": {
        "name": "KEYNOTE-189", "ref": "Gandhi NEJM 2018", "pmid": "29658856",
        "doi": "10.1056/NEJMoa1801005",
        "outcome": "Overall survival (primary)",
        "tE": 127, "tN": 410, "cE": 108, "cN": 206,
        "hr": 0.49, "lci": 0.38, "uci": 0.64,
    },
    "NCT02499862": {
        "name": "CheckMate-067 (5y)", "ref": "Larkin NEJM 2019", "pmid": "30995075",
        "doi": "10.1056/NEJMoa1910836",
        "outcome": "Overall survival nivo+ipi vs ipi (primary)",
        "hr": 0.52, "lci": 0.43, "uci": 0.64,
    },
    # Anticoagulation
    "NCT00403767": {
        "name": "ROCKET AF", "ref": "Patel NEJM 2011", "pmid": "21830957",
        "doi": "10.1056/NEJMoa1009638",
        "outcome": "Stroke or systemic embolism (primary)",
        "tE": 188, "tN": 7081, "cE": 241, "cN": 7090,
        "hr": 0.79, "lci": 0.66, "uci": 0.96,
    },
    "NCT00412984": {
        "name": "ARISTOTLE", "ref": "Granger NEJM 2011", "pmid": "21870978",
        "doi": "10.1056/NEJMoa1107039",
        "outcome": "Stroke or systemic embolism (primary)",
        "tE": 212, "tN": 9120, "cE": 265, "cN": 9081,
        "hr": 0.79, "lci": 0.66, "uci": 0.95,
    },
    # Bisphosphonate
    "NCT00049829": {
        "name": "HORIZON-PFT", "ref": "Black NEJM 2007", "pmid": "17476007",
        "doi": "10.1056/NEJMoa067312",
        "outcome": "Hip fracture (key secondary)",
        "hr": 0.59, "lci": 0.42, "uci": 0.83,
    },
    "NCT00089791": {
        "name": "FREEDOM", "ref": "Cummings NEJM 2009", "pmid": "19671655",
        "doi": "10.1056/NEJMoa0809493",
        "outcome": "Hip fracture (key secondary)",
        "hr": 0.60, "lci": 0.37, "uci": 0.97,
    },
}

# Tolerances
EXACT_FIELDS = ("tE", "tN", "cE", "cN")
EFFECT_FIELDS = ("hr", "lci", "uci")  # map to publishedHR / hrLCI / hrUCI in our data
EFFECT_TOL_ABS = 0.01
EFFECT_TOL_REL = 0.05


def compare_trial(extracted: dict, gt: dict) -> dict:
    """Compare one trial extraction against ground truth. Return per-field deltas + verdict."""
    deltas = {}
    matches = 0
    mismatches = 0
    fields_compared = 0

    for f in EXACT_FIELDS:
        gv = gt.get(f)
        ev = extracted.get(f)
        if gv is None or ev is None: continue
        fields_compared += 1
        if int(gv) == int(ev):
            deltas[f] = {"match": True, "extracted": ev, "published": gv}
            matches += 1
        else:
            deltas[f] = {"match": False, "extracted": ev, "published": gv,
                          "abs_delta": int(ev) - int(gv)}
            mismatches += 1

    # Map field names: hr → publishedHR, lci → hrLCI, uci → hrUCI
    field_map = {"hr": "publishedHR", "lci": "hrLCI", "uci": "hrUCI"}
    for gf, ef in field_map.items():
        gv = gt.get(gf); ev = extracted.get(ef)
        if gv is None or ev is None: continue
        fields_compared += 1
        try:
            gvf = float(gv); evf = float(ev)
        except Exception:
            continue
        d = abs(gvf - evf)
        tol = max(EFFECT_TOL_ABS, EFFECT_TOL_REL * gvf)
        if d <= tol:
            deltas[ef] = {"match": True, "extracted": evf, "published": gvf,
                           "abs_delta": round(evf - gvf, 4)}
            matches += 1
        else:
            deltas[ef] = {"match": False, "extracted": evf, "published": gvf,
                           "abs_delta": round(evf - gvf, 4),
                           "tol_used": round(tol, 4)}
            mismatches += 1

    if fields_compared == 0:
        verdict = "no-comparable-fields"
    elif mismatches == 0:
        verdict = "EXACT_MATCH"
    elif matches >= fields_compared * 0.75:
        verdict = "PARTIAL_MATCH"
    else:
        verdict = "DIVERGE"

    return {"verdict": verdict, "matches": matches, "mismatches": mismatches,
            "fields_compared": fields_compared, "deltas": deltas}


# ─────────── Run ───────────
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
        gt = GROUND_TRUTH[nct]
        result = compare_trial(t, gt)
        all_results.append({
            "review": rv, "nct": nct, "trial_name": gt["name"],
            "reference": gt["ref"], "pmid": gt["pmid"], "doi": gt["doi"],
            "extracted_name": t.get("name"), "extracted_pmid": t.get("pmid"),
            **result,
        })

# Counts
total = len(all_results)
exact = sum(1 for r in all_results if r["verdict"] == "EXACT_MATCH")
partial = sum(1 for r in all_results if r["verdict"] == "PARTIAL_MATCH")
diverge = sum(1 for r in all_results if r["verdict"] == "DIVERGE")
no_fields = sum(1 for r in all_results if r["verdict"] == "no-comparable-fields")

# Per-NCT (one trial can appear in multiple reviews)
nct_summary = defaultdict(list)
for r in all_results:
    nct_summary[r["nct"]].append(r)

# Save
(OUT / "r5_fidelity_results.json").write_text(
    json.dumps(all_results, indent=2, ensure_ascii=False), encoding="utf-8")

with open(OUT / "r5_fidelity_results.csv", "w", encoding="utf-8", newline="") as f:
    w = csv.writer(f)
    w.writerow(["review", "nct", "trial_name", "verdict", "matches", "mismatches",
                "fields_compared", "extracted_pmid", "true_pmid", "doi"])
    for r in all_results:
        w.writerow([r["review"], r["nct"], r["trial_name"], r["verdict"],
                    r["matches"], r["mismatches"], r["fields_compared"],
                    r["extracted_pmid"], r["pmid"], r["doi"]])

print("=" * 70)
print(f"R5 fidelity test — Round summary")
print("=" * 70)
print(f"Ground-truth trials defined: {len(GROUND_TRUTH)}")
print(f"Occurrences found in corpus: {total}")
print(f"Unique NCTs found: {len(nct_summary)}/{len(GROUND_TRUTH)}")
print()
print(f"Verdict breakdown:")
print(f"  EXACT_MATCH:           {exact:3d} ({100*exact/max(total,1):.0f}%)")
print(f"  PARTIAL_MATCH:         {partial:3d} ({100*partial/max(total,1):.0f}%)")
print(f"  DIVERGE:               {diverge:3d} ({100*diverge/max(total,1):.0f}%)")
print(f"  no-comparable-fields:  {no_fields:3d}")
print()

# Per-NCT detail (showing one row per occurrence)
print("Per-occurrence detail:")
for r in all_results:
    print(f"  [{r['verdict']:14s}] {r['trial_name']:20s} ({r['nct']}) in {r['review']}")
    if r["verdict"] in ("PARTIAL_MATCH", "DIVERGE"):
        for fld, d in r["deltas"].items():
            if not d["match"]:
                print(f"      {fld}: extracted={d['extracted']} published={d['published']} Δ={d.get('abs_delta', 'n/a')}")
