"""Round 2 sample: deeper coverage on high-suspicion reviews.

Strategy:
  Tier A — All 30 single-lens 1-of-3 findings from Round 1 (re-grade with
           multi-lens scrutiny; one agent's flag is weakest evidence)
  Tier B — Up to 8 additional trials per Round-1-suspect review (deep-dive
           on reviews where ≥1 trial was already flagged)
  Tier C — Random calibration from previously-unsampled reviews

Target: ~250 trials. Output: outputs/extraction_audit/multi_agent_sample_r2.json
"""
from __future__ import annotations
import json, sys, io, random
from pathlib import Path
from collections import defaultdict

if hasattr(sys.stdout, "buffer") and getattr(sys.stdout, "encoding", "").lower() != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

HERE = Path(__file__).resolve().parent.parent
DATA = HERE / "outputs" / "extraction_audit" / "data"
random.seed(2026)

# Load all trials (excluding nulled)
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

# Trials by (review, nct) for fast lookup
by_key = {(t["review"], t["nct"]): t for t in all_trials}

# Round 1 sample to exclude (avoid re-grading the same fixed trials)
r1 = json.loads((HERE / "outputs/extraction_audit/multi_agent_sample.json").read_text(encoding="utf-8"))
r1_keys = {(t["review"], t["nct"]) for t in r1}
r1_consensus = json.loads((HERE / "outputs/extraction_audit/multi_agent_consensus.json").read_text(encoding="utf-8"))

# Reviews where ≥1 R1 trial was flagged → high-suspicion
suspect_reviews = {r["review"] for r in r1_consensus["records"]}
print(f"R1 suspect reviews: {len(suspect_reviews)}")

# Tier A — Re-grade the 30 single-lens 1-of-3 (we already have those keys)
# Skip the 11 that were auto-fixed (they no longer need re-grade)
fixed_ncts = {(o["review"], o["nct"]) for o in json.loads(
    (HERE / "outputs/extraction_audit/multi_agent_fixes_applied.json").read_text(encoding="utf-8"))}
tier_a = []
for r in r1_consensus["records"]:
    if len(r["agents_flagged"]) != 1: continue
    key = (r["review"], r["nct"])
    if key in fixed_ncts: continue
    t = by_key.get(key)
    if t: tier_a.append({**t, "tier": "A"})
print(f"Tier A (R1 single-lens re-grade): {len(tier_a)}")

# Tier B — additional trials from suspect reviews
already_in_sample = set(r1_keys)
already_in_sample.update((t["review"], t["nct"]) for t in tier_a)
tier_b = []
for rv in suspect_reviews:
    candidates = [t for t in all_trials if t["review"] == rv
                   and (t["review"], t["nct"]) not in already_in_sample]
    random.shuffle(candidates)
    for t in candidates[:8]:
        tier_b.append({**t, "tier": "B"})
        already_in_sample.add((t["review"], t["nct"]))
        if len(tier_b) >= 150: break
    if len(tier_b) >= 150: break
print(f"Tier B (suspect-review deep-dive): {len(tier_b)}")

# Tier C — random from unsampled reviews
sampled_reviews = {t["review"] for t in r1} | suspect_reviews
unsampled_trials = [t for t in all_trials if t["review"] not in sampled_reviews
                    and (t["review"], t["nct"]) not in already_in_sample]
random.shuffle(unsampled_trials)
tier_c = [{**t, "tier": "C"} for t in unsampled_trials[:70]]
print(f"Tier C (unsampled-review calibration): {len(tier_c)}")

sample = tier_a + tier_b + tier_c
for i, t in enumerate(sample):
    t["id"] = 1000 + i  # avoid collision with R1 ids

print(f"Round 2 total: {len(sample)}")

out_p = HERE / "outputs/extraction_audit" / "multi_agent_sample_r2.json"
out_p.write_text(json.dumps(sample, indent=2, ensure_ascii=False), encoding="utf-8")
print(f"Wrote {out_p}")
