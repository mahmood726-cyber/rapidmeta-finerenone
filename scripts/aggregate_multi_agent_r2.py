"""Aggregate Round 2 multi-agent findings + combine with Round 1.

Outputs:
  outputs/extraction_audit/multi_agent_consensus_r2.json
  outputs/extraction_audit/MULTI_AGENT_SYNTHESIS_R2.md
"""
from __future__ import annotations
import json, sys, io
from pathlib import Path
from collections import defaultdict, Counter

if hasattr(sys.stdout, "buffer") and getattr(sys.stdout, "encoding", "").lower() != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

HERE = Path(__file__).resolve().parent.parent
OUT_DIR = HERE / "outputs" / "extraction_audit"
SAMPLE = json.loads((OUT_DIR / "multi_agent_sample_r2.json").read_text(encoding="utf-8"))
BY_ID = {t["id"]: t for t in SAMPLE}
SEV_RANK = {"HIGH": 3, "MED": 2, "LOW": 1}

agents = {}
for name, path in [
    ("coherence", OUT_DIR / "agent1_coherence_r2.json"),
    ("plausibility", OUT_DIR / "agent2_plausibility_r2.json"),
    ("identity", OUT_DIR / "agent3_identity_r2.json"),
]:
    agents[name] = json.loads(path.read_text(encoding="utf-8")) if path.exists() else []

by_id = defaultdict(lambda: {"flags": {}, "max_severity_rank": 0, "max_severity": "—"})
for agent_name, findings in agents.items():
    for f in findings:
        i = f["id"]
        by_id[i]["flags"][agent_name] = {
            "severity": f.get("severity", "LOW"),
            "category": f.get("category"),
            "reason": f.get("reason"),
            "confidence": f.get("confidence", 0.5),
            "ground_truth_hint": f.get("ground_truth_hint"),
        }
        rank = SEV_RANK.get(f.get("severity", "LOW"), 1)
        if rank > by_id[i]["max_severity_rank"]:
            by_id[i]["max_severity_rank"] = rank
            by_id[i]["max_severity"] = f.get("severity", "LOW")

records = []
for i, rec in by_id.items():
    trial = BY_ID.get(i, {})
    records.append({
        "id": i, "review": trial.get("review"), "nct": trial.get("nct"),
        "name": trial.get("name"), "pmid": trial.get("pmid"),
        "year": trial.get("year"), "group": (trial.get("group") or "")[:80],
        "max_severity": rec["max_severity"],
        "consensus_level": f"{len(rec['flags'])}-of-3",
        "agents_flagged": list(rec["flags"].keys()),
        "details": rec["flags"], "tier": trial.get("tier"),
    })
records.sort(key=lambda r: (-len(r["agents_flagged"]), -SEV_RANK.get(r["max_severity"], 0), r["id"]))

n_total = len(records)
n_3 = sum(1 for r in records if len(r["agents_flagged"]) == 3)
n_2 = sum(1 for r in records if len(r["agents_flagged"]) == 2)
n_1 = sum(1 for r in records if len(r["agents_flagged"]) == 1)
n_high = sum(1 for r in records if r["max_severity"] == "HIGH")
n_med  = sum(1 for r in records if r["max_severity"] == "MED")
n_low  = sum(1 for r in records if r["max_severity"] == "LOW")

cat_counts = Counter()
for r in records:
    for ag, det in r["details"].items():
        if det.get("category"):
            cat_counts[(ag, det["category"])] += 1

tier_a_ids = {t["id"] for t in SAMPLE if t.get("tier") == "A"}
tier_a_in_records = sum(1 for r in records if r["id"] in tier_a_ids)

out_json = OUT_DIR / "multi_agent_consensus_r2.json"
out_json.write_text(json.dumps({
    "summary": {
        "total_sample": len(SAMPLE),
        "total_flagged": n_total,
        "consensus_3of3": n_3, "consensus_2of3": n_2, "consensus_1of3": n_1,
        "max_severity_HIGH": n_high, "max_severity_MED": n_med, "max_severity_LOW": n_low,
        "tier_a_reflag_rate": f"{tier_a_in_records}/{len(tier_a_ids)}",
        "categories": {f"{a}:{c}": n for (a,c), n in cat_counts.most_common()},
    },
    "records": records,
}, indent=2, ensure_ascii=False), encoding="utf-8")
print(f"Wrote {out_json}")
print(f"\nR2 results:")
print(f"  flagged: {n_total}/{len(SAMPLE)}")
print(f"  3-of-3:  {n_3}")
print(f"  2-of-3:  {n_2}")
print(f"  1-of-3:  {n_1}")
print(f"  HIGH:    {n_high}")
print(f"  Tier-A re-flag rate (R1 1-of-3 → R2): {tier_a_in_records}/{len(tier_a_ids)}")

# Show 3-of-3 records
print("\n3-of-3 records:")
for r in records:
    if len(r["agents_flagged"]) == 3:
        print(f"  [{r['max_severity']}] id={r['id']} {r['name']} ({r['nct']}) — {r['review']}")
        for ag, det in r["details"].items():
            print(f"    {ag}: {det.get('reason','')[:100]}")

print("\n2-of-3 HIGH records:")
for r in records:
    if len(r["agents_flagged"]) == 2 and r["max_severity"] == "HIGH":
        print(f"  id={r['id']} {r['name']} ({r['nct']}) — {r['review']}")
