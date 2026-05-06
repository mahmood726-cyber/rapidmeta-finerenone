"""
Hot-fix for scripts/add_lsmd_disclaimer.py: the disclaimer text I
appended contained the literal apostrophe `trial's` which is INSIDE a
single-quoted JS string (`out: '...'`). The unescaped apostrophe
terminated the string and broke 27 dashboards (Playwright confirmed
"Unexpected identifier 's'" on PEGCETACOPLAN_GA_REVIEW.html).

Fix: replace `each trial's published` with `the trial-published`
(apostrophe-free, semantically equivalent), and similarly clean the
trailing fragment.

Idempotent: skips files that don't contain the broken phrase.

Usage:
  python scripts/fix_lsmd_disclaimer_apostrophe.py [--dry-run]
"""
from __future__ import annotations

import argparse
import io
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

OLD = (
    "Pooled mean differences reflect each trial's published primary "
    "analytic method (typically LSMD via MMRM or ANCOVA-adjusted change "
    "from baseline; see per-trial snippet for the trial-specific model)."
)
NEW = (
    "Pooled mean differences reflect the trial-published primary "
    "analytic method (typically LSMD via MMRM or ANCOVA-adjusted change "
    "from baseline; see per-trial snippet for the trial-specific model)."
)


def patch_one(path: Path, dry_run: bool) -> dict:
    text = path.read_text(encoding="utf-8")
    if OLD not in text:
        return {"file": path.name, "status": "no_op", "edits": 0}
    new_text = text.replace(OLD, NEW)
    if not dry_run:
        path.write_text(new_text, encoding="utf-8", newline="")
    return {"file": path.name, "status": "fixed", "edits": text.count(OLD)}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    if hasattr(sys.stdout, "buffer"):
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace", line_buffering=True)

    print("Mode:", "DRY-RUN" if args.dry_run else "WRITE")
    counts: dict[str, int] = {}
    for path in sorted(ROOT.glob("*_REVIEW.html")):
        r = patch_one(path, dry_run=args.dry_run)
        if r["status"] == "no_op":
            continue
        counts[r["status"]] = counts.get(r["status"], 0) + 1
        print(f"  {r['file']:42} {r['status']}")
    print(f"  totals: {counts}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
