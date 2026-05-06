"""Aggregate the data-integrity gate CSVs into one verdict per review topic.

Inputs (from outputs/):
  - internal_consistency_check.csv  (P0 — per-trial DEFECT)
  - aact_outcome_concordance.csv    (P1 — per-trial DEFECT)
  - aact_cross_check_v2.csv         (P0 — per-trial verdict != OK)
  - evidence_completeness_audit.csv (P2 — per-trial score_3 < 3)
  - pi_gap_check.csv                (P1 — per-topic PI_GAP_FAIL)
  - grim_benford_check.csv          (P0 — per-trial GRIM violation)
  - fragility_index.csv             (P1 — per-trial FI≤1 = FAIL, FI≤3 = WARN)

Per-topic verdict rules:
  🟢 STABLE      — 0 P0 defects, 0 PI gap, 0 FI=1, ≤1 minor advisory
  🟡 MODERATE    — 1 P0 defect OR 1 topic-level issue (PI gap OR FI=1)
  🔴 EXPOSED     — ≥2 P0 defects OR (PI gap + ≥1 FI=1) OR ≥3 FI≤3
  ⚪ UNCERTAIN   — review file has no usable trials in the gates (k<3 etc.)

Output: outputs/verdict_badges.json — { "FILE.html": { verdict, counts: {...},
reasons: [...] }, ... }
"""
from __future__ import annotations
import sys, io, csv, json
from pathlib import Path
from collections import defaultdict
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

REPO = Path(__file__).resolve().parent.parent
OUT_JSON = REPO / "outputs" / "verdict_badges.json"


def read_csv(path: Path):
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8", errors="replace") as f:
        return list(csv.DictReader(f))


def main():
    review_files = sorted(REPO.glob("*_REVIEW.html"))
    print(f"Aggregating gates across {len(review_files)} review HTMLs ...")

    # Per-file counters
    counters = {hp.name: {
        "P0_internal": 0,
        "P0_aact_nct_missing": 0,
        "P0_grim": 0,
        "P1_aact_concord": 0,
        "P1_fi_critical": 0,    # FI=1
        "P1_fi_warn": 0,         # FI=2-3
        "P1_pi_gap": 0,
        "P2_evidence_incomplete": 0,
        "n_trials_seen": 0,
    } for hp in review_files}

    # 1. Internal consistency (P0)
    for r in read_csv(REPO / "outputs" / "internal_consistency_check.csv"):
        f = r.get("file", "")
        if f in counters:
            counters[f]["n_trials_seen"] += 1
            if r.get("verdict") == "DEFECT":
                counters[f]["P0_internal"] += 1

    # 2. AACT cross-check v2.
    # P0 = hard failures (NCT_NOT_FOUND, AACT_NO_RESULTS, etc).
    # P2 = advisory (TITLE_LOW_OVERLAP — title formatting drift; ISRCTN_ONLY —
    #      non-AACT registry; COUNTRY_NOT_IN_AACT — AACT coverage gap).
    BENIGN = {"OK", "AACT_FACILITY_OK", "MULTI_ARM_SUBSET", "MITT_FRACTION",
              "POOLED_NCT_GROUP", "SINGLE_ARM_HISTORICAL_CONTROL",
              "VARIABLE_FOLLOWUP", "EVENT_BASED_TRIAL"}
    P2_ADVISORY = {"TITLE_LOW_OVERLAP", "ISRCTN_ONLY", "COUNTRY_NOT_IN_AACT"}
    for r in read_csv(REPO / "outputs" / "aact_cross_check_v2.csv"):
        f = r.get("file", "")
        v = r.get("verdict", "")
        if not f or f not in counters or not v:
            continue
        if r.get("exempt", "").lower() in ("true", "1", "yes", "exempt"):
            continue
        if v in BENIGN:
            continue
        if any(tag in v for tag in P2_ADVISORY):
            counters[f].setdefault("P2_aact_advisory", 0)
            counters[f]["P2_aact_advisory"] += 1
            continue
        counters[f]["P0_aact_nct_missing"] += 1

    # 3. AACT outcome concordance (P1)
    for r in read_csv(REPO / "outputs" / "aact_outcome_concordance.csv"):
        f = r.get("file", "")
        if f in counters and r.get("verdict") == "DEFECT":
            counters[f]["P1_aact_concord"] += 1

    # 4. Evidence completeness (P2)
    for r in read_csv(REPO / "outputs" / "evidence_completeness_audit.csv"):
        f = r.get("file", "")
        if f in counters:
            try:
                s = int(r.get("score_3", "3") or "3")
                if s < 3:
                    counters[f]["P2_evidence_incomplete"] += 1
            except ValueError:
                pass

    # 5. PI gap (P1, per-topic)
    for r in read_csv(REPO / "outputs" / "pi_gap_check.csv"):
        f = r.get("file", "")
        if f in counters and r.get("verdict") == "PI_GAP_FAIL":
            counters[f]["P1_pi_gap"] = 1

    # 6. GRIM (P0, per-trial)
    for r in read_csv(REPO / "outputs" / "grim_benford_check.csv"):
        f = r.get("file", "")
        if f in counters and r.get("verdict") == "GRIM_VIOLATION":
            counters[f]["P0_grim"] += 1

    # 7. Fragility (P1)
    for r in read_csv(REPO / "outputs" / "fragility_index.csv"):
        f = r.get("file", "")
        if f in counters:
            v = r.get("verdict", "")
            if v == "FAIL":
                counters[f]["P1_fi_critical"] += 1
            elif v == "WARN":
                counters[f]["P1_fi_warn"] += 1

    # Roll up
    badges = {}
    for fname, c in counters.items():
        p0 = c["P0_internal"] + c["P0_aact_nct_missing"] + c["P0_grim"]
        topic_issues = c["P1_pi_gap"] + min(1, c["P1_fi_critical"])
        reasons = []
        if c["P0_internal"]:
            reasons.append(f"{c['P0_internal']} internal-consistency defect(s)")
        if c["P0_aact_nct_missing"]:
            reasons.append(f"{c['P0_aact_nct_missing']} AACT NCT issue(s)")
        if c.get("P2_aact_advisory", 0):
            reasons.append(f"{c['P2_aact_advisory']} AACT title/registry advisory")
        if c["P0_grim"]:
            reasons.append(f"{c['P0_grim']} GRIM violation(s)")
        if c["P1_pi_gap"]:
            reasons.append("PI gap (heterogeneity-fragile)")
        if c["P1_fi_critical"]:
            reasons.append(f"{c['P1_fi_critical']} trial(s) at FI=1")
        if c["P1_fi_warn"]:
            reasons.append(f"{c['P1_fi_warn']} trial(s) at FI=2–3")
        if c["P1_aact_concord"]:
            reasons.append(f"{c['P1_aact_concord']} AACT outcome-direction divergence(s)")
        if c["P2_evidence_incomplete"]:
            reasons.append(f"{c['P2_evidence_incomplete']} trial(s) missing evidence rows")

        # Verdict
        if c["n_trials_seen"] == 0:
            verdict = "UNCERTAIN"
        elif p0 >= 2 or (c["P1_pi_gap"] and c["P1_fi_critical"]) or c["P1_fi_warn"] >= 3:
            verdict = "EXPOSED"
        elif p0 == 1 or topic_issues == 1:
            verdict = "MODERATE"
        else:
            verdict = "STABLE"

        badges[fname] = {
            "verdict": verdict,
            "counts": c,
            "reasons": reasons,
            "p0_total": p0,
        }

    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(badges, indent=2), encoding="utf-8")

    # Summary
    by_v = defaultdict(int)
    for b in badges.values():
        by_v[b["verdict"]] += 1
    print(f"\n=== Verdict distribution ===")
    for v in ("STABLE", "MODERATE", "EXPOSED", "UNCERTAIN"):
        print(f"  {v:12s} {by_v[v]}")
    print(f"\n=== EXPOSED topics ===")
    for fname, b in sorted(badges.items()):
        if b["verdict"] == "EXPOSED":
            print(f"  {fname[:48]:48s} P0={b['p0_total']}  reasons={'; '.join(b['reasons'])[:90]}")
    print(f"\nWritten: {OUT_JSON}")


if __name__ == "__main__":
    main()
