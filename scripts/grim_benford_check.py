"""GRIM (Granularity-Related Inconsistency of Means) test + Benford's law
first-digit distribution check.

Both are data-integrity tools from the MetaAudit lineage adapted for the
RapidMeta corpus.

GRIM (Brown & Heathers 2017): For any reported mean of integer items with N,
the mean must equal an integer multiple of (1/N). E.g., a reported mean of
3.42 with N=15 is GRIM-inconsistent because 3.42 × 15 = 51.30, not an
integer; closest valid means at N=15 are 3.40 (=51/15) or 3.47 (=52/15).

Applied here: We don't have integer-item-scale outcomes in our publishedHR
field (those are HR/RR/OR/MD on continuous scales), so direct GRIM is rare.
Instead, check that integer event counts (tE, cE) yield rates consistent
with the reported per-trial denominators.

Benford's law: First-digit distribution should follow log10(1+1/d). For
binary-event counts in a corpus of 600+ trial-rows, deviations from Benford
suggest possible fabrication. Per Mahmood's MetaAudit threshold:
χ² p-value < 0.05 = WARN; < 0.001 = FAIL.

Output: outputs/grim_benford_check.csv + summary.
"""
from __future__ import annotations
import sys, io, csv, re, math
from pathlib import Path
from collections import Counter
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

REPO = Path("C:/Projects/Finrenone")
OUT_CSV = REPO / "outputs" / "grim_benford_check.csv"

# Match trial blocks
TRIAL_RE = re.compile(
    r"'(NCT\d+(?:_[A-Za-z0-9]+)?|LEGACY-[A-Za-z0-9-]+)'\s*:\s*\{[^}]*?"
    r"name:\s*'([^']+?)'[^}]*?"
    r"tE:\s*([\d.eE+\-]+)\s*,\s*"
    r"tN:\s*([\d.eE+\-]+)\s*,\s*"
    r"cE:\s*([\d.eE+\-]+)\s*,\s*"
    r"cN:\s*([\d.eE+\-]+)",
    re.DOTALL,
)


def parse_int(s):
    try:
        v = float(s)
        return int(v) if v == int(v) else None
    except ValueError:
        return None


def benford_chi2(observed_counts: list[int]) -> tuple[float, float]:
    """Return (chi2, p_value_approx) for first-digit Benford fit.
    observed_counts is list of count of digits 1..9 in that order."""
    n = sum(observed_counts)
    if n == 0:
        return 0.0, 1.0
    expected_props = [math.log10(1 + 1 / d) for d in range(1, 10)]
    chi2 = 0.0
    for obs, p in zip(observed_counts, expected_props):
        exp = n * p
        if exp > 0:
            chi2 += (obs - exp) ** 2 / exp
    # df = 8 (9 digits - 1 constraint); approximate p-value
    # Critical chi2 at df=8: 15.51 (p=0.05), 26.12 (p=0.001)
    if chi2 > 26.12:
        p = 0.001
    elif chi2 > 20.09:
        p = 0.01
    elif chi2 > 15.51:
        p = 0.05
    elif chi2 > 13.36:
        p = 0.10
    else:
        p = 0.5  # rough
    return chi2, p


def main():
    review_files = sorted(REPO.glob("*_REVIEW.html"))
    print(f"Scanning {len(review_files)} review HTMLs ...")

    all_first_digits: list[int] = []
    grim_findings = []

    for hp in review_files:
        text = hp.read_text(encoding="utf-8", errors="replace")
        for m in TRIAL_RE.finditer(text):
            key = m.group(1)
            name = m.group(2)
            tE = parse_int(m.group(3))
            tN = parse_int(m.group(4))
            cE = parse_int(m.group(5))
            cN = parse_int(m.group(6))

            # Collect first digits of event counts (>0) for Benford
            for v in [tE, cE]:
                if v is not None and v > 0:
                    fd = int(str(v)[0])
                    if 1 <= fd <= 9:
                        all_first_digits.append(fd)

            # GRIM-style consistency: for binary outcomes, rate must equal tE/tN exactly
            # The "GRIM violation" pattern in our corpus is: rate inconsistency between
            # reported `effect` field in allOutcomes and raw 2x2.
            # Simpler check: if tE > tN (impossible) or cE > cN, flag.
            issues = []
            if tE is not None and tN is not None and tE > tN:
                issues.append(f"tE>tN ({tE}>{tN})")
            if cE is not None and cN is not None and cE > cN:
                issues.append(f"cE>cN ({cE}>{cN})")
            if tE is not None and tE < 0:
                issues.append(f"tE_negative ({tE})")
            if cE is not None and cE < 0:
                issues.append(f"cE_negative ({cE})")

            if issues:
                grim_findings.append({
                    "file": hp.name, "key": key, "name": name[:30],
                    "tE": tE, "tN": tN, "cE": cE, "cN": cN,
                    "verdict": "GRIM_VIOLATION",
                    "issues": ";".join(issues),
                })

    # Compute Benford on the corpus
    digit_counts = [0] * 9
    for d in all_first_digits:
        digit_counts[d - 1] += 1
    chi2, p_approx = benford_chi2(digit_counts)
    n_total = sum(digit_counts)

    # Save findings
    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    with OUT_CSV.open("w", newline="", encoding="utf-8") as f:
        if grim_findings:
            w = csv.DictWriter(f, fieldnames=list(grim_findings[0].keys()))
            w.writeheader()
            w.writerows(grim_findings)

    print(f"\n=== GRIM violations ===")
    print(f"  {len(grim_findings)} trial-rows with raw-count violations")
    for r in grim_findings[:20]:
        print(f"  {r['file'][:42]:42s} {r['name'][:25]:25s} {r['issues']}")

    print(f"\n=== Benford's law first-digit distribution ===")
    print(f"  N event-count values: {n_total}")
    print(f"  Observed digits 1-9: {digit_counts}")
    expected_props = [math.log10(1 + 1 / d) for d in range(1, 10)]
    print(f"  Expected props (Benford): {[f'{p:.3f}' for p in expected_props]}")
    print(f"  Observed props:           {[f'{c/n_total:.3f}' if n_total else 'NA' for c in digit_counts]}")
    print(f"  Chi-squared (df=8): {chi2:.2f}")
    print(f"  Approx p-value: {p_approx:.4f}")
    if p_approx < 0.001:
        print("  VERDICT: FAIL — strong deviation from Benford's law")
    elif p_approx < 0.05:
        print("  VERDICT: WARN — moderate deviation from Benford's law")
    else:
        print("  VERDICT: OK — distribution consistent with Benford's law")


if __name__ == "__main__":
    main()
