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

    # P_null_pmid: now CONDITIONAL on the trial also lacking a validation source.
    # A trial with valid NCT + populated evidence[] but missing PMID is just
    # "publication not yet linked" - common for recent/Chinese/regional trials.
    # We only penalise null-PMID when the trial ALSO has nulled NCT OR no
    # evidence (which is already captured by E, but double-counting here is
    # exactly what made E+P stack to flag legitimate research-in-progress).
    def _trial_at_risk(k, v):
        if v.get("pmid"): return False  # has PMID, not at risk
        if k.startswith("NULLED:"): return True
        # Evidence may be a list/empty list. Treat empty/missing as a risk multiplier.
        evidence = v.get("evidence") or []
        if not isinstance(evidence, list) or len(evidence) == 0: return True
        return False
    n_null_pmid = sum(1 for k, v in trials if _trial_at_risk(k, v))
    n_nulled_nct = sum(1 for k, v in trials if k.startswith("NULLED:"))
    n_cross = m10.get(rv, 0)
    n_single_arm = sum(1 for k, v in trials
                        if v.get("cE") == 0 and v.get("cN") == 0
                        and v.get("publishedHR") is not None)
    # Generic name is a fabrication signal ONLY when the NCT is also nulled/missing.
    # Legitimate pivotal trials commonly use acronyms like KEYNOTE-189, SURPASS-1,
    # IMPOWER150 that match the generic-name regex; flagging them is a false positive.
    n_generic_name = sum(1 for k, v in trials
                          if v.get("name")
                          and GENERIC_NAME_RE.match(str(v.get("name", "")))
                          and k.startswith("NULLED:"))

    # M_unverifiable: trial has a valid PMID + cached PubMed abstract but
    # neither the V2 RCT extractor nor the loose-match fallback was able to
    # extract a published effect-with-CI from the abstract. Means the
    # published-vs-pooled integrity cross-check cannot be performed for this
    # trial — important for flagship reviews that look complete on metadata
    # but whose claims are unverifiable from the abstract.
    PUBMED_CACHE_DIR = HERE / "outputs" / "extraction_audit" / "pubmed_cache"
    n_unverifiable = 0
    n_with_abstract = 0
    for k, v in trials:
        pmid = v.get("pmid")
        if not pmid: continue
        if not (PUBMED_CACHE_DIR / f"{pmid}.json").exists(): continue
        n_with_abstract += 1
        if v.get("publishedHR") is None:
            n_unverifiable += 1

    e_score = m11_no_ev.get(rv, 0) / tot
    p_score = n_null_pmid / tot
    n_score = n_nulled_nct / tot
    a_score = min(1.0, agent_flags.get(rv, 0) / (tot * 3))
    c_score = min(1.0, n_cross / tot)
    v_score = n_single_arm / tot
    x_score = n_generic_name / tot
    # M_unverifiable normalised by trials that HAD a cached abstract to extract
    # from. If no trials had abstracts, the signal is 0 (not penalised).
    m_score = (n_unverifiable / n_with_abstract) if n_with_abstract > 0 else 0.0

    # E and P fire on the same trials when both PMID and evidence[] are absent;
    # double-counting over-penalised research-in-progress reviews where the
    # primary publication / inline evidence quotation hadn't been backfilled.
    # Treat (E+P) as a single "evidence gap" capped at max(E, P).
    evidence_gap = max(e_score, p_score)
    # When the NCT layer is clean (N<=0.10), missing evidence/PMID is most
    # likely just "publication or quote not yet backfilled" rather than
    # fabrication, so halve the evidence_gap contribution. When the NCT
    # layer itself is suspicious (N>0.10), keep the full weight.
    eg_weight = 0.20 if n_score <= 0.10 else 0.40
    score = (eg_weight*evidence_gap + 0.15*n_score +
             0.10*a_score + 0.05*c_score + 0.05*v_score + 0.10*x_score
             + 0.05*m_score)

    # Score-based classification.
    score_class = ("QUARANTINE" if score >= 0.70 else
                   "MANUAL_REVIEW" if score >= 0.50 else
                   "LOW_CONCERN" if score >= 0.30 else
                   "OK")
    # Reviews that were explicitly placed on the manual quarantine list
    # (fully_fabricated_reviews.json / R3 quarantine log) stay quarantined
    # regardless of how the relaxed score moves. The list is operator-curated
    # ground truth; the score is just a heuristic.
    if rv in quarantined_so_far:
        classification = "QUARANTINE"
    else:
        classification = score_class

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
            "M_unverifiable_published": round(m_score, 3),
        },
        "raw_counts": {
            "m11_no_ev": m11_no_ev.get(rv, 0),
            "null_pmid": n_null_pmid,
            "nulled_nct": n_nulled_nct,
            "cross_review_flags": n_cross,
            "single_arm_with_HR": n_single_arm,
            "generic_names": n_generic_name,
            "agent_flag_weight": agent_flags.get(rv, 0),
            "trials_with_abstract": n_with_abstract,
            "unverifiable_with_abstract": n_unverifiable,
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
