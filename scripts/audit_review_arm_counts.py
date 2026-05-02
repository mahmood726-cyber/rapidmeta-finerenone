"""Audit *_REVIEW.html files for arm-count inconsistencies.

For each trial-row in each file, compare:
  (a) trial-row tN+cN (what the engine uses for analysis)
  (b) sum of "n=NUM" mentions inside the Enrollment evidence narrative
      (what reviewers see)

Flags rows where (b) deviates from (a) by more than 5% — typically caused by
narrative typos or by the narrative being on a different denominator
(randomized vs mITT vs safety-set) than the trial-row.

Outputs CSV with one row per flagged finding.

Usage:
  python scripts/audit_review_arm_counts.py --out outputs/arm_count_audit.csv
"""
from __future__ import annotations
import argparse
import csv
import os
import re
import sys
from pathlib import Path

# Match a trial-row entry in realData. Captures NCT key, name, tN, cN, and the
# block of code up to the next entry (or closing brace of realData).
TRIAL_ROW_RE = re.compile(
    r"'(?P<nct>NCT[0-9_A-Za-z]+)'\s*:\s*\{\s*"
    r"\n[^\n]*name:\s*'(?P<name>[^']+)'[^\n]*?"
    r"tN:\s*(?P<tN>\d+|null)[^\n]*?"
    r"cN:\s*(?P<cN>\d+|null)[^\n]*?",
    re.DOTALL,
)

# Within the row, find Enrollment evidence. The text field contains "n=NUM" mentions.
ENROLLMENT_RE = re.compile(
    r"label:\s*'Enrollment'[^}]*?text:\s*'([^']+)'",
    re.DOTALL,
)
N_EQ_RE = re.compile(r"\bn\s*=\s*([\d,]+)", re.IGNORECASE)


def parse_n(raw: str) -> int:
    """Parse 'n=' value, stripping thousands-separator commas."""
    return int(raw.replace(",", ""))


def find_enrollment_context(content: str, name_match_start: int, max_chars: int = 8000) -> str | None:
    """Find the Enrollment evidence text inside a trial-row body."""
    block = content[name_match_start : name_match_start + max_chars]
    m = ENROLLMENT_RE.search(block)
    return m.group(1) if m else None


def audit_file(path: Path) -> list[dict]:
    findings: list[dict] = []
    text = path.read_text(encoding="utf-8")

    # Walk each trial-row by its key
    for m in TRIAL_ROW_RE.finditer(text):
        nct = m.group("nct")
        name = m.group("name")
        tN_raw = m.group("tN")
        cN_raw = m.group("cN")

        if tN_raw == "null" or cN_raw == "null":
            continue
        tN = int(tN_raw)
        cN = int(cN_raw)
        row_total = tN + cN

        enroll_text = find_enrollment_context(text, m.start())
        if not enroll_text:
            continue

        n_values = [parse_n(x) for x in N_EQ_RE.findall(enroll_text)]
        # Drop tiny n-values (< 20) — typically "n=2 dropped" or "n=4 lost"
        n_values = [v for v in n_values if v >= 20]
        if not n_values:
            continue

        narr_sum = sum(n_values)

        if len(n_values) < 2:
            continue

        # Multi-arm filter: if narrative contains BOTH the row's tN and cN as
        # individual values (within tolerance), this is a multi-arm trial where
        # the row is a 2-arm contrast and the narrative lists all arms — not a typo.
        def near(a: int, b: int, tol: float = 0.02) -> bool:
            return abs(a - b) / max(b, 1) <= tol

        narrative_has_tN = any(near(v, tN) for v in n_values)
        narrative_has_cN = any(near(v, cN) for v in n_values)

        diff_pct = abs(narr_sum - row_total) / max(row_total, 1) * 100
        category = "TYPO_OR_REAL"
        if narrative_has_tN and narrative_has_cN and len(n_values) > 2:
            # Row's two arms are both in narrative AND there are extra arms — by design
            category = "MULTI_ARM_BY_DESIGN"
        elif narrative_has_tN and narrative_has_cN and len(n_values) == 2:
            # Exact match of the two arms
            if narr_sum == row_total:
                continue  # no finding
            category = "EXACT_TWO_ARM_MATCH"

        if diff_pct > 5.0 and category == "TYPO_OR_REAL":
            findings.append({
                "file": path.name,
                "nct": nct,
                "trial_name": name,
                "row_tN": tN,
                "row_cN": cN,
                "row_total": row_total,
                "narrative_n_values": ",".join(str(v) for v in n_values),
                "narrative_sum": narr_sum,
                "diff_abs": narr_sum - row_total,
                "diff_pct": round(diff_pct, 1),
                "category": category,
                "enrollment_excerpt": enroll_text[:200].replace("\n", " "),
            })

    return findings


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".", help="Directory containing *_REVIEW.html")
    parser.add_argument("--out", default="outputs/arm_count_audit.csv", help="CSV output path")
    parser.add_argument("--threshold", type=float, default=5.0, help="Flag deviation > N%% (default 5)")
    args = parser.parse_args()

    root = Path(args.root)
    files = sorted(root.glob("*_REVIEW.html"))
    print(f"Auditing {len(files)} review files...")

    all_findings: list[dict] = []
    files_with_issues: set[str] = set()
    for f in files:
        findings = audit_file(f)
        for fi in findings:
            if fi["diff_pct"] > args.threshold:
                all_findings.append(fi)
                files_with_issues.add(fi["file"])

    print(f"Total findings (>{args.threshold}%% deviation): {len(all_findings)}")
    print(f"Files with at least one finding: {len(files_with_issues)}")

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    if all_findings:
        fieldnames = list(all_findings[0].keys())
        with out_path.open("w", encoding="utf-8", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=fieldnames)
            w.writeheader()
            w.writerows(all_findings)
        print(f"Wrote: {out_path}")
        # Also print top 10 to stdout for quick triage
        print("\nTop findings:")
        for fi in sorted(all_findings, key=lambda x: -x["diff_pct"])[:10]:
            print(f"  {fi['file']:50s} {fi['trial_name']:24s} row_total={fi['row_total']:5d}  "
                  f"narrative_sum={fi['narrative_sum']:5d}  diff={fi['diff_pct']:5.1f}%")
    else:
        out_path.write_text("file,nct,trial_name,row_tN,row_cN,row_total,narrative_n_values,narrative_sum,diff_abs,diff_pct,enrollment_excerpt\n", encoding="utf-8")
        print("(no findings — clean!)")

    return 0


if __name__ == "__main__":
    sys.exit(main())
