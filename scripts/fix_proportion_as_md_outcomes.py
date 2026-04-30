"""
REM-CONT-2: relabel within-arm proportions encoded as continuous MDs.

The Aflibercept-HD and Faricimab-nAMD dashboards have outcomes
labelled `Q12W_pct` / `Q16W_pct` typed as `CONTINUOUS` with `md` ~0.78
and `se` ~0.022. These are within-arm proportions of patients
maintaining a dosing interval, NOT between-arm mean differences.
Pooling them as continuous MDs is incorrect (the SE is binomial, the
contrast is single-arm, the engine's pooled estimate is meaningless).

Fix: change `type: 'CONTINUOUS'` -> `type: 'DESCRIPTIVE_PROPORTION'`.
The engine recognises only `'CONTINUOUS'` for the MD pool path, so
relabelling excludes these outcomes from pooling without removing the
descriptive value.

Idempotent: skips entries already labelled DESCRIPTIVE_PROPORTION.

Usage:
  python scripts/fix_proportion_as_md_outcomes.py [--dry-run]
"""
from __future__ import annotations

import argparse
import io
import re
import sys
from pathlib import Path

ROOT = Path(r"C:\Projects\Finrenone")
TARGETS = [
    ROOT / "AFLIBERCEPT_HD_REVIEW.html",
    ROOT / "FARICIMAB_NAMD_REVIEW.html",
]

# Each entry to relabel: shortLabel + (Aflibercept|Faricimab) keyword.
# Two short-labels per dashboard, two trials per dashboard = 4 per file.
SHORT_LABELS = ("Q12W_pct", "Q16W_pct")

# Pattern: { shortLabel: 'Q12W_pct', title: '...', type: 'CONTINUOUS', ... }
# We match the type substring inside an outcome line that contains the
# right shortLabel, and flip CONTINUOUS -> DESCRIPTIVE_PROPORTION.
LINE_RE = re.compile(
    r"(\{[^{}]*?shortLabel:\s*'(?:Q12W_pct|Q16W_pct)'[^{}]*?type:\s*')CONTINUOUS('[^{}]*?\})"
)


def patch_one(path: Path, dry_run: bool) -> dict:
    text = path.read_text(encoding="utf-8")
    new_text, n = LINE_RE.subn(r"\1DESCRIPTIVE_PROPORTION\2", text)
    result = {"file": path.name, "edits": n}
    if n > 0 and not dry_run:
        path.write_text(new_text, encoding="utf-8", newline="")
    return result


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    if hasattr(sys.stdout, "buffer"):
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace", line_buffering=True)

    print("Mode:", "DRY-RUN" if args.dry_run else "WRITE")
    total = 0
    for path in TARGETS:
        if not path.exists():
            print(f"  MISSING: {path}")
            continue
        r = patch_one(path, dry_run=args.dry_run)
        total += r["edits"]
        print(f"  {r['file']:42} edits: {r['edits']}")
    print(f"  total: {total}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
