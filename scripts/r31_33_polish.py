"""Polish suite — R31 + R32 + R33.

R31 — Benford after-cleanup: re-run Benford first-digit test on the
      cleaned corpus to verify the natural-distribution property holds.

R32 — Decimal-precision sentinel: flag trials where HR/CI has SUSPICIOUS
      precision (>3 decimals, e.g., 0.7359 vs the usual published 0.74).
      Indicates computed value bled into the extracted slot.

R33 — Trial-identity confidence score: per-trial composite score from
      0-100 combining NCT-in-AACT (R7-S1), drug-in-AACT-intvs (R7-S2),
      PMID-not-null, year-present, name-present, evidence-non-empty.
      Lets users sort trials by trustworthiness within each review.
"""
from __future__ import annotations
import json, csv, re, sys, io, math
from pathlib import Path
from collections import defaultdict, Counter

if hasattr(sys.stdout, "buffer") and getattr(sys.stdout, "encoding", "").lower() != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

HERE = Path(__file__).resolve().parent.parent
OUT = HERE / "outputs" / "extraction_audit"
DATA = OUT / "data"
AACT = Path("D:/AACT-storage/AACT/2026-04-12")
DRY = "--dry-run" in sys.argv

# ─── R31: Benford after cleanup ───
all_trials = []
for json_p in sorted(DATA.glob("*.json")):
    if json_p.name.startswith("_"): continue
    rv = json_p.stem
    try: d = json.loads(json_p.read_text(encoding="utf-8"))
    except: continue
    rd = d.get("realData") or {}
    if not isinstance(rd, dict): continue
    for nct, t in rd.items():
        if not isinstance(t, dict): continue
        if nct.startswith("NULLED:"): continue
        all_trials.append((rv, nct, t))

# Collect first-digits of integer N + event counts
first_digits = Counter()
for rv, nct, t in all_trials:
    for k in ("tE", "tN", "cE", "cN"):
        v = t.get(k)
        try:
            iv = int(v) if v is not None else None
        except: continue
        if iv is None or iv <= 0: continue
        fd = int(str(iv)[0])
        if 1 <= fd <= 9: first_digits[fd] += 1

n = sum(first_digits.values())
expected = [math.log10(1 + 1/d) for d in range(1, 10)]
chi2 = 0.0
print("=== R31: Benford after cleanup ===")
print(f"n = {n} first-digit observations")
print(f"{'d':>3}  {'obs':>6}  {'obs%':>6}  {'expected%':>10}")
for d in range(1, 10):
    obs = first_digits.get(d, 0)
    exp = expected[d-1] * n
    if exp > 0:
        chi2 += (obs - exp)**2 / exp
    print(f"{d:>3}  {obs:>6}  {100*obs/max(n,1):>5.1f}%  {100*expected[d-1]:>9.1f}%")
print(f"chi2(df=8) = {chi2:.2f}  (critical at p=0.05: 15.51)")
print(f"Verdict: {'Benford fit consistent' if chi2 < 15.51 else 'Deviation from Benford'}")

# ─── R32: decimal-precision sentinel ───
print("\n=== R32: decimal-precision sentinel ===")
weird_precision = []
for rv, nct, t in all_trials:
    for k in ("publishedHR", "hrLCI", "hrUCI"):
        v = t.get(k)
        if v is None: continue
        try: vf = float(v)
        except: continue
        s = str(v) if isinstance(v, str) else f"{v}"
        # >3 decimals AND non-integer-rationality
        if "." in s:
            dec_part = s.split(".", 1)[1].rstrip("0")
            if len(dec_part) > 3:
                weird_precision.append({"review": rv, "nct": nct, "field": k, "value": v})
print(f"Trials with >3 decimal precision on HR/CI: {len(weird_precision)} entries")
# Show sample
for w in weird_precision[:5]:
    print(f"  {w['review'][:35]:35s} {w['nct']} {w['field']}={w['value']}")

# ─── R33: per-trial identity-confidence score ───
print("\n=== R33: per-trial identity-confidence score ===")
# Load AACT NCT set (any NCT that exists)
target_ncts = sorted({nct for _, nct, _ in all_trials if re.match(r"^NCT\d{8}$", nct)})
target_set = set(target_ncts)
nct_in_aact = set()
nct_aact_intvs = {}
with open(AACT / "studies.txt", "r", encoding="utf-8", errors="replace") as f:
    reader = csv.DictReader(f, delimiter="|")
    for row in reader:
        n_ = (row.get("nct_id") or "").strip().upper()
        if n_ in target_set: nct_in_aact.add(n_)
with open(AACT / "interventions.txt", "r", encoding="utf-8", errors="replace") as f:
    reader = csv.DictReader(f, delimiter="|")
    for row in reader:
        n_ = (row.get("nct_id") or "").strip().upper()
        if n_ in target_set:
            nct_aact_intvs.setdefault(n_, []).append((row.get("name") or "").lower())

STOPWORDS = {"placebo", "control", "patients", "monthly", "daily"}
def drug_in_aact(t, intvs):
    group = (t.get("group") or "").lower()
    if not group or not intvs: return False
    for w in re.findall(r"[a-z]+", group):
        if len(w) >= 6 and w not in STOPWORDS:
            for intv in intvs:
                if w in intv: return True
    return False


per_trial_scores = []
for rv, nct, t in all_trials:
    s = 0
    if nct in nct_in_aact: s += 25
    if drug_in_aact(t, nct_aact_intvs.get(nct, [])): s += 20
    if t.get("pmid"): s += 15
    if t.get("year"): s += 10
    if t.get("name"): s += 10
    if t.get("evidence"): s += 20
    per_trial_scores.append({"review": rv, "nct": nct, "score": s,
                              "name": t.get("name")})

per_trial_scores.sort(key=lambda x: x["score"])
buckets = Counter()
for r in per_trial_scores:
    if r["score"] >= 80: buckets["80-100 (excellent)"] += 1
    elif r["score"] >= 60: buckets["60-79 (good)"] += 1
    elif r["score"] >= 40: buckets["40-59 (caution)"] += 1
    elif r["score"] >= 20: buckets["20-39 (poor)"] += 1
    else: buckets["0-19 (bad)"] += 1

print(f"Total trials scored: {len(per_trial_scores)}")
for k in ["80-100 (excellent)", "60-79 (good)", "40-59 (caution)", "20-39 (poor)", "0-19 (bad)"]:
    print(f"  {k}: {buckets.get(k, 0)}")

# Write outputs
(OUT / "r31_benford_postcleanup.json").write_text(json.dumps({
    "n": n, "first_digits": dict(first_digits),
    "chi2": round(chi2, 2), "critical_05": 15.51,
    "verdict": "consistent" if chi2 < 15.51 else "deviates",
}, indent=2), encoding="utf-8")
(OUT / "r32_decimal_precision.json").write_text(json.dumps({
    "n_flagged": len(weird_precision), "entries": weird_precision[:200]
}, indent=2), encoding="utf-8")
(OUT / "r33_trial_identity_score.json").write_text(json.dumps({
    "buckets": dict(buckets),
    "n_total": len(per_trial_scores),
    "rows": per_trial_scores
}, indent=2), encoding="utf-8")
print(f"\nLogs written to outputs/extraction_audit/r3[1-3]_*.json")
