"""Build a stratified sample for multi-agent internal-consistency review.

Sampling strategy:
  Tier 1 — 30 trials from reviews with HIGH post-fix M11 count (>= 25 findings)
           (most likely to still have data errors)
  Tier 2 — 30 trials from the 6 known data-divergence pairs (Op C from NCT
           collisions — these have legitimate cross-review presence but
           extraction-values diverge)
  Tier 3 — 40 trials randomly sampled across the corpus (calibration baseline)

Output: outputs/extraction_audit/multi_agent_sample.json
  [
    {
      "id": "<sequential int>",
      "review": "...",
      "nct": "...",
      "name": "...",
      "year": ...,
      "pmid": "...",
      "group": "...",
      "tE": ..., "tN": ..., "cE": ..., "cN": ...,
      "publishedHR": ..., "hrLCI": ..., "hrUCI": ...,
      "tier": 1|2|3
    },
    ...
  ]
"""
from __future__ import annotations
import json, csv, sys, os, io, random
from pathlib import Path
from collections import defaultdict, Counter

if hasattr(sys.stdout, "buffer") and getattr(sys.stdout, "encoding", "").lower() != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

HERE = Path(__file__).resolve().parent.parent
DATA = HERE / "outputs" / "extraction_audit" / "data"

random.seed(42)

# Load all trials
all_trials = []
for f in sorted(DATA.glob("*.json")):
    if f.name.startswith("_"): continue
    stem = f.stem
    try:
        d = json.loads(f.read_text(encoding="utf-8"))
    except Exception:
        continue
    rd = d.get("realData") or {}
    if not isinstance(rd, dict): continue
    for nct, t in rd.items():
        if not isinstance(t, dict): continue
        if nct.startswith("NULLED:"): continue
        all_trials.append({
            "review": stem,
            "nct": nct,
            "name": t.get("name"),
            "year": t.get("year"),
            "pmid": t.get("pmid"),
            "group": t.get("group"),
            "tE": t.get("tE"), "tN": t.get("tN"),
            "cE": t.get("cE"), "cN": t.get("cN"),
            "publishedHR": t.get("publishedHR"),
            "hrLCI": t.get("hrLCI"), "hrUCI": t.get("hrUCI"),
            "estimandType": t.get("estimandType"),
        })

print(f"Total trials in corpus: {len(all_trials)}")

# Tier 1: from top-M11 reviews
m11_per_rv = Counter()
with open(HERE / "outputs/extraction_audit/audit_12methods.csv","r",encoding="utf-8") as f:
    for row in csv.DictReader(f):
        if row['method'] == 'M11':
            m11_per_rv[row['review']] += 1
top_rv = [r for r,n in m11_per_rv.most_common(20) if n >= 25]
print(f"Top-M11 reviews (≥25 findings): {len(top_rv)}")
tier1 = []
for rv in top_rv:
    trials_in_rv = [t for t in all_trials if t["review"] == rv]
    random.shuffle(trials_in_rv)
    tier1.extend(trials_in_rv[:3])  # 3 per review
tier1 = tier1[:30]
for t in tier1: t["tier"] = 1

# Tier 2: the 6 Op C NCTs (each appears in 2 reviews — take both)
op_c_ncts = ["NCT03775200","NCT02418585","NCT02668653","NCT03860935","NCT02388906","NCT03410992"]
tier2 = [t for t in all_trials if t["nct"] in op_c_ncts]
for t in tier2: t["tier"] = 2

# Tier 3: random calibration baseline (exclude tier1 + tier2)
used = {(t["review"], t["nct"]) for t in tier1 + tier2}
remaining = [t for t in all_trials if (t["review"], t["nct"]) not in used]
random.shuffle(remaining)
tier3 = remaining[:40]
for t in tier3: t["tier"] = 3

sample = tier1 + tier2 + tier3
for i, t in enumerate(sample):
    t["id"] = i

print(f"Sample: {len(tier1)} tier1 + {len(tier2)} tier2 + {len(tier3)} tier3 = {len(sample)} trials")

out_p = HERE / "outputs" / "extraction_audit" / "multi_agent_sample.json"
out_p.write_text(json.dumps(sample, indent=2, ensure_ascii=False), encoding="utf-8")
print(f"Wrote {out_p}")
