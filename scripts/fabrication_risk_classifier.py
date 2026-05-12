"""Compute fabrication-risk score per review using existing signals.

Signals (each 0-1, then weighted-summed):
  E = % trials with M11_NO_EVIDENCE (no evidence[] populated)
  P = % trials with null pmid (after our R1+R2+R3 cleanup)
  N = % trials with null NCT or NCT prefix NULLED:
  A = density of multi-agent flags per trial (R1+R2+R3, normalized)
  C = % trials cross-review-colliding (M10)
  V = % trials with single-arm cE=cN=0 (post-R2 should be ~0; residual = fabrication)
  X = "name field" suspicion: % trials where name looks generic (matches NCT itself,
       drug+indication pattern, sponsor-protocol code)

Score = 0.30*E + 0.25*P + 0.15*N + 0.10*A + 0.05*C + 0.05*V + 0.10*X

Thresholds (post-R3 hindsight):
  ≥ 0.70 → quarantine (very likely fabrication)
  ≥ 0.50 → flag for manual review (partial fabrication)
  ≥ 0.30 → low-confidence concern
  < 0.30 → trustworthy

Output: outputs/extraction_audit/fabrication_risk_scores.json
        outputs/extraction_audit/fabrication_risk_table.csv
"""
from __future__ import annotations
import json, csv, re, sys, io
from pathlib import Path
from collections import defaultdict

if hasattr(sys.stdout, "buffer") and getattr(sys.stdout, "encoding", "").lower() != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

HERE = Path(__file__).resolve().parent.parent
DATA = HERE / "outputs" / "extraction_audit" / "data"
OUT = HERE / "outputs" / "extraction_audit"

# Load 12-method audit
m11_no_ev = defaultdict(int)
m11 = defaultdict(int)
m10 = defaultdict(int)
with open(OUT / "audit_12methods.csv", "r", encoding="utf-8") as f:
    for row in csv.DictReader(f):
        if row["method"] == "M11_NO_EVIDENCE": m11_no_ev[row["review"]] += 1
        if row["method"] == "M11": m11[row["review"]] += 1
        if row["method"] == "M10": m10[row["review"]] += 1

# Aggregate agent flags from R1+R2+R3
agent_flags = defaultdict(int)
for cs_file in ["multi_agent_consensus.json", "multi_agent_consensus_r2.json", "multi_agent_consensus_r3.json"]:
    p = OUT / cs_file
    if not p.exists(): continue
    cs = json.loads(p.read_text(encoding="utf-8"))
    for r in cs.get("records", []):
        n_agents = len(r.get("agents_flagged", []))
        # Weight by consensus level (3-of-3 = 3, 2-of-3 = 2, 1-of-3 = 1)
        agent_flags[r["review"]] += n_agents

# Generic-name patterns
GENERIC_NAME_RE = re.compile(
    r"^(NCT\d{8}|[A-Z]{2,}\d{2,}|[A-Z]+-\d+(?:-\d+)?|Study[- ]\d+|Phase \d+|"
    r"C\d{3}|YKP3089-C\d+|N0\d+|PER-\d+)$", re.IGNORECASE
)

# Already-quarantined reviews
quarantined_so_far = set()
fff = OUT / "fully_fabricated_reviews.json"
if fff.exists():
    for x in json.loads(fff.read_text(encoding="utf-8")):
        quarantined_so_far.add(x["review"])
# Also from R3 batch 2 log
r3log = OUT / "multi_agent_fixes_applied_r3.json"
if r3log.exists():
    for x in json.loads(r3log.read_text(encoding="utf-8")).get("batch2", []):
        if x.get("status") == "QUARANTINED":
            quarantined_so_far.add(x["review"])

results = []
for json_p in sorted(DATA.glob("*.json")):
    if json_p.name.startswith("_"): continue
    rv = json_p.stem
    try: d = json.loads(json_p.read_text(encoding="utf-8"))
    except Exception: continue
    rd = d.get("realData") or {}
    if not isinstance(rd, dict): continue
    trials = [(k, v) for k, v in rd.items() if isinstance(v, dict)]
    tot = len(trials)
    if tot == 0: continue

    n_null_pmid = sum(1 for k, v in trials if not v.get("pmid"))
    n_nulled_nct = sum(1 for k, v in trials if k.startswith("NULLED:"))
    n_cross = m10.get(rv, 0)
    n_single_arm = sum(1 for k, v in trials
                        if v.get("cE") == 0 and v.get("cN") == 0
                        and v.get("publishedHR") is not None)
    n_generic_name = sum(1 for k, v in trials
                          if v.get("name") and GENERIC_NAME_RE.match(str(v.get("name", ""))))

    e_score = m11_no_ev.get(rv, 0) / tot
    p_score = n_null_pmid / tot
    n_score = n_nulled_nct / tot
    a_score = min(1.0, agent_flags.get(rv, 0) / (tot * 3))
    c_score = min(1.0, n_cross / tot)
    v_score = n_single_arm / tot
    x_score = n_generic_name / tot

    score = (0.30*e_score + 0.25*p_score + 0.15*n_score +
             0.10*a_score + 0.05*c_score + 0.05*v_score + 0.10*x_score)

    classification = ("QUARANTINE" if score >= 0.70 else
                      "MANUAL_REVIEW" if score >= 0.50 else
                      "LOW_CONCERN" if score >= 0.30 else
                      "OK")

    results.append({
        "review": rv, "n_trials": tot, "score": round(score, 3),
        "classification": classification,
        "already_quarantined": rv in quarantined_so_far,
        "components": {
            "E_no_evidence": round(e_score, 3),
            "P_null_pmid": round(p_score, 3),
            "N_nulled_nct": round(n_score, 3),
            "A_agent_flag_density": round(a_score, 3),
            "C_cross_review": round(c_score, 3),
            "V_residual_single_arm": round(v_score, 3),
            "X_generic_name": round(x_score, 3),
        },
        "raw_counts": {
            "m11_no_ev": m11_no_ev.get(rv, 0),
            "null_pmid": n_null_pmid,
            "nulled_nct": n_nulled_nct,
            "cross_review_flags": n_cross,
            "single_arm_with_HR": n_single_arm,
            "generic_names": n_generic_name,
            "agent_flag_weight": agent_flags.get(rv, 0),
        },
    })

results.sort(key=lambda r: -r["score"])

# Write outputs
(OUT / "fabrication_risk_scores.json").write_text(
    json.dumps(results, indent=2, ensure_ascii=False), encoding="utf-8")

with open(OUT / "fabrication_risk_table.csv", "w", encoding="utf-8", newline="") as f:
    w = csv.writer(f)
    w.writerow(["review", "n_trials", "score", "classification", "already_quarantined",
                "E_no_ev", "P_null_pmid", "N_nulled_nct", "A_agent", "C_cross", "V_sa", "X_generic"])
    for r in results:
        c = r["components"]
        w.writerow([r["review"], r["n_trials"], r["score"], r["classification"],
                    r["already_quarantined"],
                    c["E_no_evidence"], c["P_null_pmid"], c["N_nulled_nct"],
                    c["A_agent_flag_density"], c["C_cross_review"],
                    c["V_residual_single_arm"], c["X_generic_name"]])

# Print top tier
print(f"Total reviews scored: {len(results)}")
print()
print("Classification counts:")
from collections import Counter
cc = Counter(r["classification"] for r in results)
for k in ["QUARANTINE", "MANUAL_REVIEW", "LOW_CONCERN", "OK"]:
    print(f"  {k}: {cc.get(k, 0)}")

print()
print("Top 25 by fabrication risk:")
for r in results[:25]:
    flag = "[Q]" if r["already_quarantined"] else "   "
    print(f"  {flag} {r['score']:.3f}  {r['classification']:15s}  "
          f"({r['n_trials']:3d}t)  {r['review']}")

newly_quarantine = [r for r in results
                     if r["classification"] == "QUARANTINE" and not r["already_quarantined"]]
print(f"\nNEWLY-FLAGGED for quarantine (not yet quarantined): {len(newly_quarantine)}")
for r in newly_quarantine:
    print(f"  {r['score']:.3f}  {r['review']}")
