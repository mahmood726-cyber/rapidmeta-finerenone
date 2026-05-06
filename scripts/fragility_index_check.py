"""Fragility Index check (Walsh 2014) — for each trial-row with binary outcome
data, compute the minimum number of additional events in the smaller-event arm
(switched from non-event to event) required to flip statistical significance
of Fisher's exact test from p<0.05 to p>=0.05.

Reference: Walsh M et al. JCE 2014;67:622-628 — "The statistical significance
of randomized controlled trial results is frequently fragile: a case for a
Fragility Index". A median FI of 2 across major NEJM/JAMA trials suggested
many "significant" trials hinge on a handful of patients.

Adapted from Mahmood's MetaAudit Fragility Index detector. Threshold:
  FI <= 3 = WARN (highly fragile)
  FI <= 1 = FAIL (one patient flips significance)
  not significant at baseline -> SKIP

Output: outputs/fragility_index.csv with one row per binary trial, plus
per-topic FI distribution summary.
"""
from __future__ import annotations
import sys, io, csv, re, math
from pathlib import Path
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

REPO_DIR = Path(__file__).resolve().parent.parent
OUT_CSV = REPO_DIR / "outputs" / "fragility_index.csv"

TRIAL_RE = re.compile(
    r"'(NCT\d+(?:_[A-Za-z0-9]+)?|LEGACY-[A-Za-z0-9-]+)'\s*:\s*\{[^}]*?"
    r"name:\s*'([^']+?)'[^}]*?"
    r"tE:\s*([\d.eE+\-]+|null|None|NaN)\s*,\s*"
    r"tN:\s*([\d.eE+\-]+|null|None|NaN)\s*,\s*"
    r"cE:\s*([\d.eE+\-]+|null|None|NaN)\s*,\s*"
    r"cN:\s*([\d.eE+\-]+|null|None|NaN)",
    re.DOTALL,
)


def parse_int(s):
    if s is None:
        return None
    s = s.strip()
    if s.lower() in ("null", "none", "nan"):
        return None
    try:
        v = float(s)
        return int(v) if v == int(v) and v >= 0 else None
    except ValueError:
        return None


def log_factorial(n):
    """Stirling-corrected log(n!)."""
    if n < 0:
        return float("nan")
    if n <= 1:
        return 0.0
    # Use math.lgamma which is accurate
    return math.lgamma(n + 1)


def hyper_pmf_log(a, b, c, d):
    """log P(A=a) for 2x2 with row sums (a+b, c+d) and col sums (a+c, b+d).
    Hypergeometric P[X=a | row1=a+b, row2=c+d, col1=a+c]."""
    n = a + b + c + d
    return (log_factorial(a + b) + log_factorial(c + d)
            + log_factorial(a + c) + log_factorial(b + d)
            - log_factorial(n)
            - log_factorial(a) - log_factorial(b)
            - log_factorial(c) - log_factorial(d))


def fishers_two_sided(a, b, c, d):
    """Fisher's exact two-sided p-value for 2x2 table:
       [[a, b],
        [c, d]]
    Sum probabilities of all tables with same marginals AND p_table <= p_observed.
    """
    if any(x < 0 for x in (a, b, c, d)):
        return 1.0
    n1 = a + b  # row1 total
    n2 = c + d  # row2 total
    m1 = a + c  # col1 total
    n = n1 + n2
    if n == 0 or n1 == 0 or n2 == 0 or m1 == 0 or m1 == n:
        return 1.0
    log_p_obs = hyper_pmf_log(a, b, c, d)
    p_total = 0.0
    a_min = max(0, m1 - n2)
    a_max = min(n1, m1)
    for a_i in range(a_min, a_max + 1):
        b_i = n1 - a_i
        c_i = m1 - a_i
        d_i = n2 - c_i
        log_p_i = hyper_pmf_log(a_i, b_i, c_i, d_i)
        # Use a small numerical tolerance so the observed table is always counted
        if log_p_i <= log_p_obs + 1e-12:
            p_total += math.exp(log_p_i)
    return min(1.0, p_total)


def compute_fragility(tE, tN, cE, cN):
    """Compute Walsh fragility index. Returns dict with FI, baseline_p, flipped_p,
    or None if trial doesn't qualify (not initially significant or not informative).
    """
    if None in (tE, tN, cE, cN):
        return None
    if tN <= 0 or cN <= 0:
        return None
    if tE > tN or cE > cN or tE < 0 or cE < 0:
        return None  # raw count violation — already flagged by GRIM
    a = tE
    b = tN - tE
    c = cE
    d = cN - cE
    p0 = fishers_two_sided(a, b, c, d)
    if p0 >= 0.05:
        return {"FI": None, "p0": p0, "p_flipped": None, "verdict": "NOT_SIGNIFICANT"}

    # Identify direction: which arm had FEWER events as proportion?
    # Convert non-events to events in the LOWER-event-rate arm to push toward null.
    pT = a / tN
    pC = c / cN
    if pT <= pC:
        # Add events to treatment arm (a -> a+1, b -> b-1)
        max_steps = b
        flip_target = "treatment"
    else:
        max_steps = d
        flip_target = "control"

    # Cap iterations — FI almost always small relative to N
    max_steps = min(max_steps, max(tN, cN))
    p_flipped = p0
    fi = None
    for step in range(1, max_steps + 1):
        if flip_target == "treatment":
            a_i, b_i = a + step, b - step
            c_i, d_i = c, d
        else:
            a_i, b_i = a, b
            c_i, d_i = c + step, d - step
        p_i = fishers_two_sided(a_i, b_i, c_i, d_i)
        if p_i >= 0.05:
            fi = step
            p_flipped = p_i
            break

    if fi is None:
        # Even max flip cannot push to non-significance — record as ROBUST
        return {"FI": max_steps, "p0": p0, "p_flipped": p_flipped, "verdict": "ROBUST",
                "flip_target": flip_target}

    if fi <= 1:
        verdict = "FAIL"
    elif fi <= 3:
        verdict = "WARN"
    else:
        verdict = "OK"

    return {"FI": fi, "p0": p0, "p_flipped": p_flipped, "verdict": verdict,
            "flip_target": flip_target}


# Trials where the published primary endpoint is NOT a parallel-arm binary
# proportion (e.g., rate ratio, continuous mean difference). Fragility
# Index doesn't apply to these — exclude from the audit to avoid false
# alarms. Documented per Agent 2 audit findings (2026-05-05).
NON_BINARY_PRIMARY_EXEMPT = {
    # HOPE-B (NCT03569891): primary is annualized bleeding rate ratio
    # (within-subject comparison vs lead-in). Our 54/54 vs 45/52 binary
    # tabulation is a derived patient-level any-bleed counts, not the
    # primary endpoint. Pipe 2023 NEJM PMID 36812434.
    ("HEMOPHILIA_GENE_THERAPY_REVIEW.html", "NCT03569891"),
    # PATENT-1 (NCT00810693): primary is 6-minute walk distance change
    # (continuous, MD = +30m vs placebo). Our 23/254 vs 21/126 binary
    # tabulation is from a non-primary clinical-worsening secondary.
    # Ghofrani 2013 NEJM PMID 23883378.
    ("PAH_THERAPY_REVIEW.html", "NCT00810693"),
}


def main():
    review_files = sorted(REPO_DIR.glob("*_REVIEW.html"))
    print(f"Scanning {len(review_files)} review HTMLs ...")

    findings = []
    for hp in review_files:
        text = hp.read_text(encoding="utf-8", errors="replace")
        for m in TRIAL_RE.finditer(text):
            key = m.group(1)
            name = m.group(2)
            if (hp.name, key) in NON_BINARY_PRIMARY_EXEMPT:
                continue
            tE = parse_int(m.group(3))
            tN = parse_int(m.group(4))
            cE = parse_int(m.group(5))
            cN = parse_int(m.group(6))
            r = compute_fragility(tE, tN, cE, cN)
            if r is None:
                continue
            findings.append({
                "file": hp.name, "key": key, "name": name[:40],
                "tE": tE, "tN": tN, "cE": cE, "cN": cN,
                "p0": f"{r['p0']:.4f}",
                "FI": r["FI"] if r["FI"] is not None else "",
                "p_flipped": f"{r['p_flipped']:.4f}" if r["p_flipped"] is not None else "",
                "flip_target": r.get("flip_target", ""),
                "verdict": r["verdict"],
            })

    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    with OUT_CSV.open("w", newline="", encoding="utf-8") as f:
        if findings:
            w = csv.DictWriter(f, fieldnames=list(findings[0].keys()))
            w.writeheader()
            w.writerows(findings)

    by_v: dict[str, int] = {}
    for r in findings:
        by_v[r["verdict"]] = by_v.get(r["verdict"], 0) + 1
    print(f"\n=== Fragility Index distribution ===")
    print(f"  Trial-rows: {len(findings)}")
    for k_, v in sorted(by_v.items()):
        print(f"  {k_:25s} {v}")

    sig = [r for r in findings if r["verdict"] in ("FAIL", "WARN", "OK", "ROBUST")]
    fis = [int(r["FI"]) for r in sig if r["FI"] != "" and r["FI"] is not None]
    if fis:
        fis_sorted = sorted(fis)
        median = fis_sorted[len(fis_sorted) // 2]
        print(f"\n  Median FI (significant trials, n={len(fis)}): {median}")
        print(f"  Min FI: {min(fis)}; Max FI: {max(fis)}")

    print(f"\n=== Fragile trials (FI <= 3) ===")
    fragile = [r for r in findings if r["verdict"] in ("FAIL", "WARN")]
    fragile.sort(key=lambda r: int(r["FI"]) if r["FI"] != "" else 9999)
    for r in fragile[:25]:
        print(f"  FI={r['FI']:>2}  {r['file'][:42]:42s} {r['name'][:30]:30s} p0={r['p0']} -> {r['p_flipped']}")

    print(f"\nWritten: {OUT_CSV}")


if __name__ == "__main__":
    main()
