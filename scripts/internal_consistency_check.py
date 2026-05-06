"""Internal consistency check — for each trial-row in realData, compute the
implied effect estimate from raw counts (tE, tN, cE, cN) and compare against
the claimed `publishedHR` field. Disagreement flags a transcription error
WITHOUT needing external ground-truth.

This is the BETTER verification method per user (2026-05-04): "use published
metas to check against to find the ground truth to some extent but the other
and better method is internal consitency. The data will be internally
consistent".

Checks per trial-row:

  1. SIGN consistency: if pT < pC then for RR/HR/OR the claim should be <1;
     if pT > pC the claim should be >1. (Skip if either rate is 0 — sparse.)
  2. MAGNITUDE consistency: for RR/OR estimands compute implied estimate
     from raw 2x2; flag if claim diverges by >50% on log scale.
  3. RD-vs-RR-vs-OR LABEL CONFUSION: RD must be in [-1, +1]; values outside
     that range with `RD` label are mis-labelled (probably RR).
  4. NEGATIVE HR/RR/OR: physically impossible; flag.
  5. CI containment: publishedHR should be inside [hrLCI, hrUCI].
  6. CI sign consistency: hrLCI and hrUCI should both be on same side of
     null OR span it (a CI can't be entirely below null AND entirely above).

Output: outputs/internal_consistency_check.csv
"""
from __future__ import annotations
import sys, io, csv, re, math
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
from pathlib import Path

REPO_DIR = Path(__file__).resolve().parent.parent
OUT_CSV = REPO_DIR / "outputs" / "internal_consistency_check.csv"

# Single-arm trials with synthetic pre-vs-post comparator: row counts can't
# match publishedHR by 2x2 implication. Skip from sign/drift checks.
SINGLE_ARM_EXEMPT = {
    ("HEMOPHILIA_GENE_THERAPY_REVIEW.html", "NCT03569891"),  # HOPE-B
    ("HEMOPHILIA_GENE_THERAPY_REVIEW.html", "NCT04370054"),  # AFFINE
    ("HEMOPHILIA_GENE_THERAPY_REVIEW.html", "NCT03370913"),  # GENEr8-1
    ("MDR_TB_SHORTENED_REVIEW.html", "NCT02333799"),  # Nix-TB
}

# Trials where raw counts reflect a DIFFERENT outcome to publishedHR (a known
# divergence preserved deliberately so the user can show both data points).
# Documented case-by-case in the trial's `group` field.
# Filename keys updated 2026-05-05 after Phase 1+2 demote/rename pass.
MIXED_METRIC_EXEMPT = {
    # HCC HIMALAYA: HR 0.78 OS time-to-death; raw 421/393 vs 395/389 are
    # crude proportion of deaths at end of follow-up.
    ("HCC_1L_REVIEW.html", "NCT03298451"),
    # DESTINY-Breast06: HR 0.62 PFS time-to-event; raw is response-rate.
    ("HER2_LOW_ADC_REVIEW.html", "NCT04494425"),
    # HPTN 052: HR 0.07 genotype-confirmed transmission; raw is all incident HIV.
    ("HIV_ART_TIMING_REVIEW.html", "NCT00074581"),
    # SERAPHIN PAH: HR 0.55 composite morbidity-mortality; raw all-cause.
    ("PAH_THERAPY_REVIEW.html", "NCT00660179"),
    # R21 Phase 3 malaria: HR 0.25 time-adjusted VE 75%; raw is crude RR 0.56.
    ("MALARIA_VACCINE_REVIEW.html", "NCT04704830"),
    # SURMOUNT-1 tirzepatide: RR 36.7 ≥20% weight loss; raw is ≥5%.
    ("OBESITY_DRUGS_REVIEW.html", "NCT04184622"),
    # SCALE Obesity liraglutide: RR 6.0 ≥10% weight loss; raw is ≥5%.
    ("OBESITY_DRUGS_REVIEW.html", "NCT01272219"),
    # ENERGIZE mitapivat: RR 24.7 hemoglobin response ≥1.5g/dL; raw is ≥1g/dL.
    ("MITAPIVAT_THALASSEMIA_REVIEW.html", "NCT04770753"),
}

# Match a trial block grabbing tE/tN/cE/cN + publishedHR + hrLCI/hrUCI + estimandType.
TRIAL_RE = re.compile(
    r"'(NCT\d+(?:_[A-Za-z0-9]+)?|LEGACY-[A-Za-z0-9-]+)'\s*:\s*\{[^}]*?"
    r"name:\s*'([^']+?)'[^}]*?"
    r"tE:\s*([\d.eE+\-]+|null|None|NaN)\s*,\s*"
    r"tN:\s*([\d.eE+\-]+|null|None|NaN)\s*,\s*"
    r"cE:\s*([\d.eE+\-]+|null|None|NaN)\s*,\s*"
    r"cN:\s*([\d.eE+\-]+|null|None|NaN)[^}]*?"
    r"publishedHR:\s*([\d.eE+\-]+|null|None|NaN)"
    r"(?:\s*,\s*hrLCI:\s*([\d.eE+\-]+|null|None|NaN))?"
    r"(?:\s*,\s*hrUCI:\s*([\d.eE+\-]+|null|None|NaN))?",
    re.DOTALL,
)


def parse_num(s):
    if s is None:
        return None
    s = s.strip()
    if s.lower() in ("null", "none", "nan"):
        return None
    try:
        return float(s)
    except ValueError:
        return None


def estimand_type_for_block(text: str, block_start: int) -> str:
    """Try to extract `estimandType: 'XXX'` from the same block."""
    block_end = text.find("},", block_start + 100)
    if block_end == -1:
        block_end = block_start + 5000
    block = text[block_start:block_end]
    m = re.search(r"estimandType:\s*'([^']+)'", block)
    return m.group(1).upper() if m else "HR"  # default to HR


def main():
    review_files = sorted(REPO_DIR.glob("*_REVIEW.html"))
    print(f"Scanning {len(review_files)} review HTMLs ...")

    findings = []
    for hp in review_files:
        text = hp.read_text(encoding="utf-8", errors="replace")
        for m in TRIAL_RE.finditer(text):
            key = m.group(1)
            name = m.group(2)
            # Skip single-arm trials with synthetic comparator (raw counts won't reconcile)
            if (hp.name, key) in SINGLE_ARM_EXEMPT:
                continue
            # Skip trials with documented different-metric raw counts vs publishedHR
            if (hp.name, key) in MIXED_METRIC_EXEMPT:
                continue
            tE = parse_num(m.group(3))
            tN = parse_num(m.group(4))
            cE = parse_num(m.group(5))
            cN = parse_num(m.group(6))
            ph = parse_num(m.group(7))
            lci = parse_num(m.group(8))
            uci = parse_num(m.group(9))
            et = estimand_type_for_block(text, m.start())

            issues = []

            # Skip if essential numbers missing
            if ph is None or tN is None or cN is None or tN == 0 or cN == 0:
                continue

            # Check 1: NEGATIVE for HR/RR/OR
            if et in ("HR", "RR", "OR") and ph < 0:
                issues.append(f"NEG_{et}={ph}")

            # Check 2: RD out of [-1, +1]
            if et == "RD" and (ph < -1 or ph > 1):
                issues.append(f"RD_OUT_OF_RANGE={ph}")

            # Check 3: implied vs claimed (only when tE/cE both present and integer-like)
            if tE is not None and cE is not None and tE >= 0 and cE >= 0 and tE.is_integer() and cE.is_integer():
                pT = tE / tN if tN > 0 else None
                pC = cE / cN if cN > 0 else None

                if pT is not None and pC is not None and pC > 0 and pT >= 0:
                    # Sign check: only meaningful for RR/HR/OR with both rates > 0.5/N (i.e. some events on each side)
                    if pT > 0 and pC > 0 and et in ("RR", "HR", "OR"):
                        # For RR, expected ratio
                        if et == "RR":
                            implied = pT / pC
                            tol_ratio = 1.5  # 50% tolerance
                            if implied > 0 and ph > 0:
                                log_diff = abs(math.log(ph) - math.log(implied))
                                if log_diff > math.log(tol_ratio):
                                    issues.append(f"RR_DRIFT(impl={implied:.2f}, claim={ph:.2f})")
                            # Sign:
                            if (implied < 1) != (ph < 1) and abs(implied - 1) > 0.1 and abs(ph - 1) > 0.1:
                                issues.append(f"RR_SIGN_FLIP(impl={implied:.2f},claim={ph:.2f})")
                        elif et == "HR":
                            # HR ≈ RR for short FU + low rate; tolerance higher
                            implied = pT / pC
                            tol_ratio = 2.0
                            if implied > 0 and ph > 0:
                                log_diff = abs(math.log(ph) - math.log(implied))
                                if log_diff > math.log(tol_ratio):
                                    issues.append(f"HR_DRIFT(impl_RR={implied:.2f},claim_HR={ph:.2f})")
                            if (implied < 1) != (ph < 1) and abs(implied - 1) > 0.15 and abs(ph - 1) > 0.15:
                                issues.append(f"HR_SIGN_FLIP(impl_RR={implied:.2f},claim_HR={ph:.2f})")
                        elif et == "OR":
                            if tN > tE and cN > cE:
                                impl_or = (tE / (tN - tE)) / (cE / (cN - cE)) if (tN - tE) > 0 and cE > 0 and (cN - cE) > 0 else None
                                if impl_or is not None and impl_or > 0 and ph > 0:
                                    log_diff = abs(math.log(ph) - math.log(impl_or))
                                    if log_diff > math.log(2.5):
                                        issues.append(f"OR_DRIFT(impl={impl_or:.2f},claim={ph:.2f})")
                                    if (impl_or < 1) != (ph < 1) and abs(impl_or - 1) > 0.2 and abs(ph - 1) > 0.2:
                                        issues.append(f"OR_SIGN_FLIP")
                    elif et == "RD":
                        impl_rd = pT - pC
                        if abs(impl_rd - ph) > 0.10:  # 10pp tolerance
                            issues.append(f"RD_DRIFT(impl={impl_rd:.3f},claim={ph})")

            # Check 4: CI containment
            if lci is not None and uci is not None and ph is not None:
                if not (lci <= ph <= uci):
                    issues.append(f"CI_CONTAINMENT_FAIL(claim={ph} not in [{lci},{uci}])")
                if lci > uci:
                    issues.append(f"CI_REVERSED")

            # Check 5: CI sign consistency for RR/HR/OR (must be positive bounds)
            if et in ("HR", "RR", "OR"):
                if lci is not None and lci < 0:
                    issues.append(f"NEG_LCI_{et}={lci}")
                if uci is not None and uci < 0:
                    issues.append(f"NEG_UCI_{et}={uci}")

            verdict = "OK" if not issues else "DEFECT"

            findings.append({
                "file": hp.name,
                "key": key,
                "name": name[:35],
                "estimandType": et,
                "tE": tE if tE is not None else "",
                "tN": tN if tN is not None else "",
                "cE": cE if cE is not None else "",
                "cN": cN if cN is not None else "",
                "claim_pt": ph,
                "claim_lci": lci if lci is not None else "",
                "claim_uci": uci if uci is not None else "",
                "implied_pT": f"{tE/tN:.4f}" if (tE is not None and tN is not None and tN > 0) else "",
                "implied_pC": f"{cE/cN:.4f}" if (cE is not None and cN is not None and cN > 0) else "",
                "verdict": verdict,
                "issues": ";".join(issues),
            })

    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    with OUT_CSV.open("w", newline="", encoding="utf-8") as f:
        if findings:
            w = csv.DictWriter(f, fieldnames=list(findings[0].keys()))
            w.writeheader()
            w.writerows(findings)

    by_v = {"OK": 0, "DEFECT": 0}
    for r in findings:
        by_v[r["verdict"]] = by_v.get(r["verdict"], 0) + 1
    print(f"\n=== Internal-consistency results ===")
    print(f"  Trial-rows analysed: {len(findings)}")
    print(f"  OK: {by_v.get('OK', 0)}")
    print(f"  DEFECT: {by_v.get('DEFECT', 0)}")

    # Categorise issue types
    issue_buckets: dict[str, int] = {}
    for r in findings:
        if not r["issues"]:
            continue
        for iss in r["issues"].split(";"):
            cat = iss.split("(")[0].strip()
            issue_buckets[cat] = issue_buckets.get(cat, 0) + 1
    print(f"\n=== Issue categories ===")
    for cat, n in sorted(issue_buckets.items(), key=lambda x: -x[1]):
        print(f"  {cat:40s} {n}")

    # Top examples per category
    print(f"\n=== First 5 sample defects per category ===\n")
    seen_cat = set()
    sample_count = 0
    for r in findings:
        if r["verdict"] != "DEFECT":
            continue
        if sample_count >= 60:
            break
        cat = r["issues"].split("(")[0].split(";")[0].strip()
        if cat not in seen_cat:
            seen_cat.add(cat)
            print(f"\n[{cat}]")
        print(f"  {r['file'][:45]:45s} {r['name'][:25]:25s} {r['estimandType']:3s} pt={r['claim_pt']} pT={r['implied_pT']} pC={r['implied_pC']} -> {r['issues'][:80]}")
        sample_count += 1

    print(f"\nWritten: {OUT_CSV}")


if __name__ == "__main__":
    main()
