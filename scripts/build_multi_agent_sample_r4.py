"""Round 4 sample — newly-suspect reviews flagged by the fabrication classifier.

Target: reviews with score ≥ 0.55 AND n_trials ≥ 5 that aren't yet quarantined.
Sample every remaining trial in those reviews (deep audit).
"""
from __future__ import annotations
import json, sys, io
from pathlib import Path

if hasattr(sys.stdout, "buffer") and getattr(sys.stdout, "encoding", "").lower() != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

HERE = Path(__file__).resolve().parent.parent
OUT = HERE / "outputs" / "extraction_audit"
DATA = OUT / "data"

scores = json.loads((OUT / "fabrication_risk_scores.json").read_text(encoding="utf-8"))
target_reviews = [r["review"] for r in scores
                   if r["score"] >= 0.55 and r["n_trials"] >= 5 and not r["already_quarantined"]]
print(f"Target reviews ({len(target_reviews)}):")
for rv in target_reviews:
    print(f"  {rv}")

# Load all trials
sample = []
for rv in target_reviews:
    json_p = DATA / f"{rv}.json"
    if not json_p.exists(): continue
    try: d = json.loads(json_p.read_text(encoding="utf-8"))
    except: continue
    rd = d.get("realData") or {}
    if not isinstance(rd, dict): continue
    for nct, t in rd.items():
        if not isinstance(t, dict): continue
        if nct.startswith("NULLED:"): continue
        sample.append({
            "review": rv, "nct": nct, "name": t.get("name"),
            "year": t.get("year"), "pmid": t.get("pmid"),
            "group": t.get("group"),
            "tE": t.get("tE"), "tN": t.get("tN"),
            "cE": t.get("cE"), "cN": t.get("cN"),
            "publishedHR": t.get("publishedHR"),
            "estimandType": t.get("estimandType"),
        })

for i, t in enumerate(sample):
    t["id"] = 3000 + i

out_p = OUT / "multi_agent_sample_r4.json"
out_p.write_text(json.dumps(sample, indent=2, ensure_ascii=False), encoding="utf-8")
print(f"\nTotal trials: {len(sample)}")
print(f"Wrote {out_p}")
