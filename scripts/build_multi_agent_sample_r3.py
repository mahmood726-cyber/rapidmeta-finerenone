"""Round 3 sample.

Strategy:
  Tier A — R2 1-of-3 single-lens findings (re-grade with multi-lens scrutiny)
  Tier B — All trials from the 10 fully-fabricated reviews (deep audit)
  Tier C — Random calibration from previously-unsampled reviews

Target ~200 trials. Output: outputs/extraction_audit/multi_agent_sample_r3.json
"""
from __future__ import annotations
import json, sys, io, random
from pathlib import Path

if hasattr(sys.stdout, "buffer") and getattr(sys.stdout, "encoding", "").lower() != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

HERE = Path(__file__).resolve().parent.parent
DATA = HERE / "outputs" / "extraction_audit" / "data"
random.seed(2027)

all_trials = []
for f in sorted(DATA.glob("*.json")):
    if f.name.startswith("_"): continue
    stem = f.stem
    try: d = json.loads(f.read_text(encoding="utf-8"))
    except Exception: continue
    rd = d.get("realData") or {}
    if not isinstance(rd, dict): continue
    for nct, t in rd.items():
        if not isinstance(t, dict): continue
        if nct.startswith("NULLED:"): continue
        all_trials.append({
            "review": stem, "nct": nct, "name": t.get("name"),
            "year": t.get("year"), "pmid": t.get("pmid"),
            "group": t.get("group"),
            "tE": t.get("tE"), "tN": t.get("tN"),
            "cE": t.get("cE"), "cN": t.get("cN"),
            "publishedHR": t.get("publishedHR"),
            "hrLCI": t.get("hrLCI"), "hrUCI": t.get("hrUCI"),
            "estimandType": t.get("estimandType"),
        })
by_key = {(t["review"], t["nct"]): t for t in all_trials}

# Exclude trials already auto-fixed
r1_fixed = {(o["review"], o["nct"]) for o in json.loads(
    (HERE / "outputs/extraction_audit/multi_agent_fixes_applied.json").read_text(encoding="utf-8"))}
r2_fixed_log = json.loads((HERE / "outputs/extraction_audit/multi_agent_fixes_applied_r2.json").read_text(encoding="utf-8"))
r2_fixed = {(o["review"], o["nct"]) for o in r2_fixed_log.get("batch1", [])}
for entry in r2_fixed_log.get("batch2", []):
    for nct in entry.get("ncts", []):
        r2_fixed.add((entry["review"], nct))
all_fixed = r1_fixed | r2_fixed

# Tier A — R2 1-of-3 single-lens
r2_consensus = json.loads((HERE / "outputs/extraction_audit/multi_agent_consensus_r2.json").read_text(encoding="utf-8"))
tier_a = []
for r in r2_consensus["records"]:
    if len(r["agents_flagged"]) != 1: continue
    key = (r["review"], r["nct"])
    if key in all_fixed: continue
    t = by_key.get(key)
    if t: tier_a.append({**t, "tier": "A"})
tier_a = tier_a[:90]
print(f"Tier A (R2 1-of-3 re-grade): {len(tier_a)}")

# Tier B — 10 fully-fabricated reviews (audit ALL their trials)
fully_fab = json.loads((HERE / "outputs/extraction_audit/fully_fabricated_reviews.json").read_text(encoding="utf-8"))
fab_review_set = {x["review"] for x in fully_fab}
already_in_sample = {(t["review"], t["nct"]) for t in tier_a}
tier_b = []
for rv in fab_review_set:
    candidates = [t for t in all_trials if t["review"] == rv
                   and (t["review"], t["nct"]) not in already_in_sample
                   and (t["review"], t["nct"]) not in all_fixed]
    for t in candidates:
        tier_b.append({**t, "tier": "B"})
        already_in_sample.add((t["review"], t["nct"]))
print(f"Tier B (fully-fabricated reviews deep-audit): {len(tier_b)} from {len(fab_review_set)} reviews")

# Tier C — random unsampled
r1 = json.loads((HERE / "outputs/extraction_audit/multi_agent_sample.json").read_text(encoding="utf-8"))
r2 = json.loads((HERE / "outputs/extraction_audit/multi_agent_sample_r2.json").read_text(encoding="utf-8"))
sampled_reviews = ({t["review"] for t in r1} | {t["review"] for t in r2} | fab_review_set)
unsampled = [t for t in all_trials if t["review"] not in sampled_reviews
              and (t["review"], t["nct"]) not in already_in_sample]
random.shuffle(unsampled)
tier_c = [{**t, "tier": "C"} for t in unsampled[:40]]
print(f"Tier C (unsampled-review calibration): {len(tier_c)}")

sample = tier_a + tier_b + tier_c
for i, t in enumerate(sample):
    t["id"] = 2000 + i

print(f"Round 3 total: {len(sample)}")
out_p = HERE / "outputs/extraction_audit" / "multi_agent_sample_r3.json"
out_p.write_text(json.dumps(sample, indent=2, ensure_ascii=False), encoding="utf-8")
print(f"Wrote {out_p}")
