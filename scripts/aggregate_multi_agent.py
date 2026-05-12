"""Aggregate the 3 multi-agent consistency check outputs.

Per arXiv:2604.16706 (Apr 2026), substring-match grading is chance-level vs
human; LLM ensemble achieves κ ≈ 0.43 at ≥3 judges. We follow the ≥2-of-3
agreement gate for HIGH-confidence flags.

Inputs:
  agent1_coherence.json (drug/disease lens)
  agent2_plausibility.json (effect-size lens)
  agent3_identity.json (NCT/PMID/year triangulation)

Output:
  outputs/extraction_audit/multi_agent_consensus.json
    {
      "by_id": { "<id>": {trial info, agents flagging it, max_severity, consensus_level} },
      "tier_summary": ...,
      "patterns": ...
    }
  outputs/extraction_audit/MULTI_AGENT_SYNTHESIS.md (human report)
"""
from __future__ import annotations
import json, sys, io
from pathlib import Path
from collections import defaultdict, Counter

if hasattr(sys.stdout, "buffer") and getattr(sys.stdout, "encoding", "").lower() != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

HERE = Path(__file__).resolve().parent.parent
OUT_DIR = HERE / "outputs" / "extraction_audit"
SAMPLE = json.loads((OUT_DIR / "multi_agent_sample.json").read_text(encoding="utf-8"))
BY_ID = {t["id"]: t for t in SAMPLE}

agents = {}
for name, path in [
    ("coherence", OUT_DIR / "agent1_coherence.json"),
    ("plausibility", OUT_DIR / "agent2_plausibility.json"),
    ("identity", OUT_DIR / "agent3_identity.json"),
]:
    if path.exists():
        agents[name] = json.loads(path.read_text(encoding="utf-8"))
    else:
        agents[name] = []
        print(f"  ! missing {path.name}")

SEV_RANK = {"HIGH": 3, "MED": 2, "LOW": 1}

# Aggregate by trial id
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

# Decorate with trial metadata + consensus
consensus_records = []
for i, rec in by_id.items():
    n_agents = len(rec["flags"])
    trial = BY_ID.get(i, {})
    record = {
        "id": i,
        "review": trial.get("review"),
        "nct": trial.get("nct"),
        "name": trial.get("name"),
        "pmid": trial.get("pmid"),
        "year": trial.get("year"),
        "group": (trial.get("group") or "")[:80],
        "max_severity": rec["max_severity"],
        "consensus_level": f"{n_agents}-of-3",
        "agents_flagged": list(rec["flags"].keys()),
        "details": rec["flags"],
        "tier": trial.get("tier"),
    }
    consensus_records.append(record)

# Sort by (consensus_level desc, max_severity_rank desc)
consensus_records.sort(key=lambda r: (
    -len(r["agents_flagged"]),
    -SEV_RANK.get(r["max_severity"], 0),
    r["id"],
))

# Counts
n_total_flagged = len(consensus_records)
n_3of3 = sum(1 for r in consensus_records if len(r["agents_flagged"]) == 3)
n_2of3 = sum(1 for r in consensus_records if len(r["agents_flagged"]) == 2)
n_1of3 = sum(1 for r in consensus_records if len(r["agents_flagged"]) == 1)
n_high = sum(1 for r in consensus_records if r["max_severity"] == "HIGH")
n_med  = sum(1 for r in consensus_records if r["max_severity"] == "MED")
n_low  = sum(1 for r in consensus_records if r["max_severity"] == "LOW")

# Categories from each agent
cat_counts = Counter()
for r in consensus_records:
    for ag, det in r["details"].items():
        if det.get("category"):
            cat_counts[(ag, det["category"])] += 1

# Tier 2 (known divergent pairs) — confirm they were caught
tier2_ids = {t["id"] for t in SAMPLE if t.get("tier") == 2}
tier2_caught = sum(1 for r in consensus_records if r["id"] in tier2_ids)

# Write JSON
out_json = OUT_DIR / "multi_agent_consensus.json"
out_json.write_text(json.dumps({
    "summary": {
        "total_sample": len(SAMPLE),
        "total_flagged": n_total_flagged,
        "consensus_3of3": n_3of3,
        "consensus_2of3": n_2of3,
        "consensus_1of3": n_1of3,
        "max_severity_HIGH": n_high,
        "max_severity_MED": n_med,
        "max_severity_LOW": n_low,
        "tier2_caught": f"{tier2_caught}/{len(tier2_ids)}",
        "categories": {f"{a}:{c}": n for (a,c), n in cat_counts.most_common()},
    },
    "records": consensus_records,
}, indent=2, ensure_ascii=False), encoding="utf-8")
print(f"Wrote {out_json}")

# Markdown synthesis
md = []
md.append("# Multi-agent internal-consistency audit — 2026-05-12")
md.append("")
md.append("## Method")
md.append("")
md.append("3 specialized agents reviewed a stratified sample of 77 trials:")
md.append("- Agent 1 — drug/disease coherence (is the drug plausibly used for this disease?)")
md.append("- Agent 2 — effect-size plausibility (HR magnitude, CI consistency, schema)")
md.append("- Agent 3 — trial identity triangulation (NCT ⟷ acronym ⟷ PMID ⟷ year)")
md.append("")
md.append("Per arXiv:2604.16706 (Apr 2026), substring-match grading is chance-level vs")
md.append("human (κ≈0.05); LLM ensemble at ≥3 judges achieves κ≈0.43. We use ≥2-of-3")
md.append("agreement as the HIGH-confidence consensus gate.")
md.append("")
md.append("## Sample")
md.append("- Tier 1 (n=24): trials from reviews with highest post-fix M11 count")
md.append("- Tier 2 (n=13): the 6 known cross-review NCT-divergent-value cases")
md.append("- Tier 3 (n=40): random calibration baseline across the corpus")
md.append("")
md.append("## Results")
md.append("")
md.append(f"- Total trials flagged: **{n_total_flagged}/{len(SAMPLE)}**")
md.append(f"  - 3-of-3 agreement: **{n_3of3}** (highest confidence)")
md.append(f"  - 2-of-3 agreement: **{n_2of3}** (high confidence)")
md.append(f"  - 1-of-3 agreement: **{n_1of3}** (single-lens flag; manual review)")
md.append("")
md.append(f"- Max severity:")
md.append(f"  - HIGH: **{n_high}**")
md.append(f"  - MED:  **{n_med}**")
md.append(f"  - LOW:  **{n_low}**")
md.append("")
md.append(f"- Tier 2 catch rate: **{tier2_caught}/{len(tier2_ids)}** of known divergent pairs")
md.append("")
md.append("## Top defect categories")
md.append("")
for (ag, cat), n in cat_counts.most_common(15):
    md.append(f"- {ag} · {cat}: {n}")
md.append("")
md.append("## Highest-confidence findings (3-of-3 + HIGH)")
md.append("")
for r in consensus_records:
    if len(r["agents_flagged"]) == 3 and r["max_severity"] == "HIGH":
        md.append(f"### id={r['id']} — {r['name']} ({r['nct']}) in {r['review']}")
        md.append(f"- year={r['year']} pmid={r['pmid']} group={r['group']}")
        for ag, det in r["details"].items():
            md.append(f"  - **{ag}** ({det['severity']} / {det.get('category')}): {det.get('reason')}")
        md.append("")

md.append("## 2-of-3 + HIGH findings")
md.append("")
for r in consensus_records:
    if len(r["agents_flagged"]) == 2 and r["max_severity"] == "HIGH":
        md.append(f"### id={r['id']} — {r['name']} ({r['nct']}) in {r['review']}")
        md.append(f"- year={r['year']} pmid={r['pmid']} group={r['group']}")
        for ag, det in r["details"].items():
            md.append(f"  - **{ag}** ({det['severity']} / {det.get('category')}): {det.get('reason')}")
        md.append("")

md.append("## 1-of-3 + HIGH (single-lens; review individually)")
md.append("")
single_high = [r for r in consensus_records if len(r["agents_flagged"]) == 1 and r["max_severity"] == "HIGH"]
for r in single_high:
    md.append(f"- **id={r['id']}** — {r['name']} ({r['nct']}) in {r['review']}")
    for ag, det in r["details"].items():
        md.append(f"   - {ag}/{det.get('category')}: {det.get('reason')}")
md.append("")

md_p = OUT_DIR / "MULTI_AGENT_SYNTHESIS.md"
md_p.write_text("\n".join(md), encoding="utf-8")
print(f"Wrote {md_p}")
print()
print("=" * 60)
print(f"Total flagged:    {n_total_flagged}/{len(SAMPLE)}")
print(f"3-of-3 agreement: {n_3of3}")
print(f"2-of-3 agreement: {n_2of3}")
print(f"1-of-3 agreement: {n_1of3}")
print(f"HIGH severity:    {n_high}")
print(f"Tier 2 catch:     {tier2_caught}/{len(tier2_ids)}")
