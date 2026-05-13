"""Path ii — Build per-review TruthCert manifests.

Each review gets a manifest at outputs/extraction_audit/truthcert/<review>.json
that records:
  - review_stem, classification, score, n_trials, components
  - audit_rounds: list of rounds where this review was touched (R1-R23)
  - fixes_applied: list of (round, op, nct, reason) for every fix
  - ground_truth_sources: AACT 2026-04-12, PubMed cached, PMC OA, multi-agent, internal
  - hmac_sig: HMAC-SHA256 over the canonical payload

Replayable: anyone can verify HMAC matches given the key (gitignored).
"""
from __future__ import annotations
import json, hashlib, hmac, os, sys, io, datetime
from pathlib import Path
from collections import defaultdict

if hasattr(sys.stdout, "buffer") and getattr(sys.stdout, "encoding", "").lower() != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

HERE = Path(__file__).resolve().parent.parent
OUT = HERE / "outputs" / "extraction_audit"
MANIFEST_DIR = OUT / "truthcert"
MANIFEST_DIR.mkdir(parents=True, exist_ok=True)

# Reuse the 8-agent HMAC key
KEYFILE = HERE / ".truthcert_8agent.key"
if KEYFILE.exists():
    HMAC_KEY = KEYFILE.read_text(encoding="utf-8").strip()
else:
    HMAC_KEY = hashlib.sha256(os.urandom(32)).hexdigest()
    KEYFILE.write_text(HMAC_KEY, encoding="utf-8")

# Aggregate fixes per review across all rounds
# Each round produces a JSON file with applied fixes; we extract (round_tag, fixes_for_review)
ROUND_FILES = [
    ("R1_extraction_fixes", "fix_extraction_defects.json"),
    ("R1_P0_residual", "fix_p0_residuals.json"),
    ("R1_8agent", "AUDIT_8AGENT_SYNTHESIS.md"),  # not JSON; skipped
    ("R1_multi_agent", "multi_agent_fixes_applied.json"),
    ("R1_evidence_inject", "evidence_patches_applied.json"),
    ("R1_pmid_void", "pmid_voided.json"),
    ("R1_nct_collisions", "nct_collision_fix_manifest.json"),
    ("R2_multi_agent", "multi_agent_fixes_applied_r2.json"),
    ("R3_multi_agent", "multi_agent_fixes_applied_r3.json"),
    ("R3_schema_md", "schema_md_with_events_fixed.json"),
    ("R3_aggressive", "aggressive_cleanup_1of3.json"),
    ("R4_multi_agent", "multi_agent_fixes_applied_r4.json"),
    ("R5_fidelity_fix", "r5_fidelity_v2_results.json"),
    ("R6_internal", "r6_internal_consistency.json"),
    ("R6b_internal", "r6b_internal_consistency.json"),
    ("R6c_internal", "r6c_internal_consistency.json"),
    ("R7_aact", "r7b_verification.json"),
    ("R7c_aact_ok", "r7c_ok_band_verification.json"),
    ("R8_pmid_year", "r8_year_from_pmid.json"),
    ("R8agent_blinded", "8agent_aggregate.json"),
    ("R8agent_extended", "8agent_extended_fixes.json"),
    ("R8agent_med", "med_severity_fixes.json"),
    ("R1_3_carryforward", "r1r3_med_low_carryforward_fixes.json"),
    ("R9_per_arm", "r9_per_arm.json"),
    ("R10_outcomes", "r10_outcome_events.json"),
    ("R19_completion", "r19_completion_date.json"),
    ("R22_mesh", "r22_mesh_matching.json"),
    ("R23_acronym", "r23_acronym_vs_aact.json"),
]

per_review_fixes = defaultdict(list)
rounds_touched = defaultdict(set)
for round_tag, fname in ROUND_FILES:
    fp = OUT / fname
    if not fp.exists() or not fname.endswith(".json"): continue
    try: doc = json.loads(fp.read_text(encoding="utf-8"))
    except: continue
    # Different shapes — handle both list and dict-with-applied
    entries = []
    if isinstance(doc, list): entries = doc
    elif isinstance(doc, dict):
        for k in ("applied", "fixes", "findings", "log", "batch1", "batch2", "batch3"):
            v = doc.get(k)
            if isinstance(v, list): entries.extend(v)
        # Nested log dict (R6/R6b)
        log = doc.get("log")
        if isinstance(log, list): entries.extend(log)
        elif isinstance(log, dict):
            for k, v in log.items():
                if isinstance(v, list): entries.extend(v)
    for e in entries:
        if not isinstance(e, dict): continue
        rv = e.get("review")
        nct = e.get("nct")
        op = e.get("op") or e.get("fix") or e.get("status") or e.get("fix_type")
        if not rv: continue
        if not isinstance(op, str): continue
        if "NULL" not in op.upper() and "QUAR" not in op.upper() and "SET_" not in op.upper() and "INJECT" not in op.upper():
            continue  # Skip flag-only / status-only entries
        rounds_touched[rv].add(round_tag)
        per_review_fixes[rv].append({
            "round": round_tag,
            "nct": nct,
            "op": op,
            "reason": (e.get("reason") or e.get("category") or e.get("status") or "")[:140],
        })

# Load classifier scores
scores = json.loads((OUT / "fabrication_risk_scores.json").read_text(encoding="utf-8"))

now = datetime.datetime.now(datetime.timezone.utc).isoformat()
n_manifests = 0
total_fixes_logged = 0
for r in scores:
    rv = r["review"]
    fixes = per_review_fixes.get(rv, [])
    rounds = sorted(rounds_touched.get(rv, set()))
    payload = {
        "review": rv,
        "audit_completed_at": now,
        "classification": r["classification"],
        "fabrication_risk_score": r["score"],
        "n_trials": r["n_trials"],
        "score_components": r.get("components", {}),
        "already_quarantined": r.get("already_quarantined", False),
        "audit_rounds_touched": rounds,
        "fixes_applied": fixes,
        "n_fixes_applied": len(fixes),
        "ground_truth_sources": [
            "AACT 2026-04-12 (Clinical Trials Transformation Initiative)",
            "PubMed E-utilities (NCBI)",
            "PMC OAI full-text (NCBI)",
            "Multi-agent consensus (≥2-of-3 gate, R1-R3 + R4 + 8-agent)",
            "Internal cross-consistency (R6abc)",
            "Published landmark trial values (R5)",
            "Published reference meta-analyses (R5b)",
        ],
        "methodology": "outputs/extraction_audit/FINAL_INTEGRITY_REPORT_V2.md",
    }
    # Canonical JSON + HMAC-SHA256
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    sig = hmac.new(HMAC_KEY.encode("utf-8"), canonical, hashlib.sha256).hexdigest()
    payload["truthcert_hmac_sha256"] = sig
    payload["truthcert_key_id"] = hashlib.sha256(HMAC_KEY.encode("utf-8")).hexdigest()[:16]
    manifest_p = MANIFEST_DIR / f"{rv}.json"
    manifest_p.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    n_manifests += 1
    total_fixes_logged += len(fixes)

print(f"Wrote {n_manifests} per-review TruthCert manifests")
print(f"Total fixes logged across manifests: {total_fixes_logged}")
print(f"HMAC algorithm: SHA-256")
print(f"Key ID: {hashlib.sha256(HMAC_KEY.encode('utf-8')).hexdigest()[:16]}")
