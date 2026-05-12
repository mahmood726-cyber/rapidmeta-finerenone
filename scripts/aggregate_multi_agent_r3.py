"""Aggregate Round 3 multi-agent findings."""
from __future__ import annotations
import json, sys, io
from pathlib import Path
from collections import defaultdict, Counter

if hasattr(sys.stdout, "buffer") and getattr(sys.stdout, "encoding", "").lower() != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

HERE = Path(__file__).resolve().parent.parent
OUT_DIR = HERE / "outputs" / "extraction_audit"
SAMPLE = json.loads((OUT_DIR / "multi_agent_sample_r3.json").read_text(encoding="utf-8"))
BY_ID = {t["id"]: t for t in SAMPLE}
SEV_RANK = {"HIGH": 3, "MED": 2, "LOW": 1}

agents = {}
for name, path in [
    ("coherence", OUT_DIR / "agent1_coherence_r3.json"),
    ("plausibility", OUT_DIR / "agent2_plausibility_r3.json"),
    ("identity", OUT_DIR / "agent3_identity_r3.json"),
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

# Tier breakdown
tier_breakdown = defaultdict(lambda: {"flagged": 0, "high": 0})
for r in records:
    t = r.get("tier", "?")
    tier_breakdown[t]["flagged"] += 1
    if r["max_severity"] == "HIGH":
        tier_breakdown[t]["high"] += 1
total_per_tier = Counter(t.get("tier") for t in SAMPLE)

out_json = OUT_DIR / "multi_agent_consensus_r3.json"
out_json.write_text(json.dumps({
    "summary": {
        "total_sample": len(SAMPLE),
        "total_flagged": n_total,
        "consensus_3of3": n_3, "consensus_2of3": n_2, "consensus_1of3": n_1,
        "max_severity_HIGH": n_high, "max_severity_MED": n_med, "max_severity_LOW": n_low,
        "tier_breakdown": {t: {**v, "of": total_per_tier.get(t, 0)} for t, v in tier_breakdown.items()},
    },
    "records": records,
}, indent=2, ensure_ascii=False), encoding="utf-8")
print(f"Wrote {out_json}")

print(f"\nR3 results:")
print(f"  flagged: {n_total}/{len(SAMPLE)}")
print(f"  3-of-3:  {n_3}")
print(f"  2-of-3:  {n_2}")
print(f"  1-of-3:  {n_1}")
print(f"  HIGH:    {n_high}")
print(f"\nTier breakdown (flagged / total):")
for t in ["A", "B", "C"]:
    tb = tier_breakdown.get(t, {"flagged": 0, "high": 0})
    tot = total_per_tier.get(t, 0)
    print(f"  Tier {t}: {tb['flagged']}/{tot} flagged, {tb['high']} HIGH")

print(f"\n3-of-3 + 2-of-3 HIGH records:")
for r in records:
    if len(r["agents_flagged"]) >= 2 and r["max_severity"] == "HIGH":
        print(f"  [{len(r['agents_flagged'])}-of-3 {r['tier']}] id={r['id']} {r['name']} ({r['nct']}) — {r['review']}")
