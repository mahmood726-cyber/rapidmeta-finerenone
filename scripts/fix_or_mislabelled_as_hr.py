"""For each trial-row flagged HR_DRIFT or RR_DRIFT in internal_consistency_check.csv,
compute the implied OR from raw 2x2. If implied OR matches claimed value within
20% on log scale, change estimandType to OR.

This handles the OR-vs-RR-vs-HR label confusion for binary-response endpoints
in psoriasis/atopic-derm/RA biologics where authors typically report OR but
the field stored 'HR'.
"""
from __future__ import annotations
import sys, io, re, math, csv
from pathlib import Path
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

REPO = Path(__file__).resolve().parent.parent
CSV_PATH = REPO / "outputs" / "internal_consistency_check.csv"

# Read defects
rows = list(csv.DictReader(CSV_PATH.open(encoding="utf-8")))
candidates = [r for r in rows if "DRIFT" in r["issues"] and "SIGN_FLIP" not in r["issues"]]

LINE_RE = re.compile(
    r"name:\s*'([^']+)'[^\n]*?publishedHR:\s*(-?[\d.eE+]+),\s*hrLCI:\s*(-?[\d.eE+]+),\s*hrUCI:\s*(-?[\d.eE+]+)"
)


def main():
    fixed = 0
    for r in candidates:
        try:
            tE = float(r["tE"])
            tN = float(r["tN"])
            cE = float(r["cE"])
            cN = float(r["cN"])
            ph = float(r["claim_pt"])
        except (ValueError, KeyError):
            continue

        if tN <= tE or cN <= cE or cE <= 0:
            continue
        impl_or = (tE / (tN - tE)) / (cE / (cN - cE))
        if impl_or <= 0 or ph <= 0:
            continue

        log_diff_or = abs(math.log(impl_or) - math.log(ph))
        impl_rr = (tE / tN) / (cE / cN) if cN > 0 and cE > 0 else None

        # Decide: is this an OR mislabelled as HR/RR?
        is_or = log_diff_or < math.log(1.25)  # within 25% on log scale
        is_rr = impl_rr is not None and abs(math.log(impl_rr) - math.log(ph)) < math.log(1.25)

        if not is_or:
            continue  # not a clear OR mislabel

        # Find the file and replace estimandType in this trial's line
        path = REPO / r["file"]
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        lines = text.splitlines(keepends=True)
        modified = False
        for i, line in enumerate(lines):
            m = LINE_RE.search(line)
            if not m:
                continue
            if m.group(1) != r["name"][:35].strip() and m.group(1)[:35] != r["name"][:35].strip():
                # Compare names; r["name"] is truncated to 35 in CSV
                continue
            try:
                line_ph = float(m.group(2))
            except ValueError:
                continue
            if abs(line_ph - ph) > 0.001:
                continue  # not the same trial-row

            # Now apply
            if "estimandType: 'OR'" in line:
                continue  # already correct
            if re.search(r"estimandType:\s*'(HR|RR|MD)'", line):
                lines[i] = re.sub(r"estimandType:\s*'(HR|RR|MD)'", "estimandType: 'OR'", line)
                modified = True
                fixed += 1
                print(f"  REPLACE-ET-OR {r['file']}::{r['name'][:30]} (impl_OR={impl_or:.2f} claim={ph})")
            else:
                # Insert before publishedHR
                ph_match = re.search(r"publishedHR:", line)
                if ph_match:
                    new_line = line[:ph_match.start()] + "estimandType: 'OR', " + line[ph_match.start():]
                    lines[i] = new_line
                    modified = True
                    fixed += 1
                    print(f"  INSERT-ET-OR  {r['file']}::{r['name'][:30]} (impl_OR={impl_or:.2f} claim={ph})")
            break  # only first match
        if modified:
            path.write_text("".join(lines), encoding="utf-8")

    print(f"\n=== Fixed: {fixed} trial blocks (HR/RR -> OR) ===")


if __name__ == "__main__":
    main()
