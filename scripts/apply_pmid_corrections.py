"""
Apply UNAMBIGUOUS PMID corrections proposed by
propose_pmid_corrections.py.

What it changes per row:
  - Replaces the trial's `pmid: 'OLD'` with `pmid: 'NEW'`.
  - Replaces the trial's `sourceUrl: '...'` with the canonical
    PubMed URL `https://pubmed.ncbi.nlm.nih.gov/NEW/` (guaranteed
    to resolve to the right paper; user can swap to journal full-
    text URL later).
  - LEAVES snippet text unchanged. The snippet was always
    describing the right paper -- it's the PMID that pointed to
    the wrong one. After the swap, snippet + PMID + URL all agree.

What it does NOT change:
  - Page numbers in the snippet (audit may still flag if old
    snippet pages were copy-paste from a sibling trial).
  - Trial values (tE/tN/cE/cN/HR). The audit is citation-only.
  - PROBABLE / AMBIGUOUS / NO_PUBMED_HITS rows (those need human
    review via verification cards).

Idempotent: re-runs are no-ops if the dashboard already has the
new PMID. Anchors on `name: 'TRIAL_NAME'` + `pmid: 'OLD_PMID'` so
trial-name disambiguates when the same PMID appears in multiple
trial-rows.

Usage:
  python scripts/apply_pmid_corrections.py --dry-run
  python scripts/apply_pmid_corrections.py --apply
"""
from __future__ import annotations

import argparse
import csv
import io
import re
import sys
from pathlib import Path

ROOT = Path(r"C:\Projects\Finrenone")
CORRECTIONS_CSV = ROOT / "outputs" / "pmid_corrections.csv"


def patch_dashboard(path: Path, edits: list[dict], dry_run: bool) -> dict:
    """Apply all edits for one dashboard. Returns {applied, skipped, missing}."""
    text = path.read_text(encoding="utf-8")
    orig = text
    applied = 0
    skipped = 0
    missing = 0
    for edit in edits:
        old_pmid = edit["current_pmid"]
        new_pmid = edit["proposed_pmid"]
        trial_name = edit["trial_name"]

        # Find the trial entry: anchor on `name: 'TRIAL_NAME'` ... `pmid: 'OLD'`
        # within ~200 chars (single-line trial-row pattern).
        # If the dashboard ALREADY has the new pmid (idempotent), skip.
        idempotent_anchor = (
            f"name: '{trial_name}'" if "'" not in trial_name else None
        )
        if idempotent_anchor is None:
            # Trial name has an apostrophe; we can't safely match. Skip.
            missing += 1
            continue

        # Already correct?
        already_correct_pattern = re.compile(
            rf"name:\s*'{re.escape(trial_name)}'(?:[^{{}}]{{0,400}}?)pmid:\s*'{new_pmid}'",
            re.DOTALL,
        )
        if already_correct_pattern.search(text):
            skipped += 1
            continue

        # Match name + old pmid pair.
        match_pattern = re.compile(
            rf"(name:\s*'{re.escape(trial_name)}'(?:[^{{}}]{{0,400}}?)pmid:\s*')"
            rf"{old_pmid}"
            rf"(')",
            re.DOTALL,
        )
        m = match_pattern.search(text)
        if not m:
            # Either name or old pmid no longer present. Could be already
            # patched OR trial renamed. Mark missing for user review.
            missing += 1
            continue
        text = text[:m.start()] + m.group(1) + new_pmid + m.group(2) + text[m.end():]
        applied += 1

        # Update sourceUrl in the same trial block.
        # Find the next sourceUrl: '...' after the trial name -- replace with
        # canonical PubMed URL.
        url_pattern = re.compile(
            rf"(name:\s*'{re.escape(trial_name)}'(?:.{{0,3000}}?))(sourceUrl:\s*')([^']*)(')",
            re.DOTALL,
        )
        new_url = f"https://pubmed.ncbi.nlm.nih.gov/{new_pmid}/"
        text2 = url_pattern.sub(rf"\g<1>\g<2>{new_url}\g<4>", text, count=1)
        if text2 != text:
            text = text2

    if applied > 0 and not dry_run:
        path.write_text(text, encoding="utf-8", newline="")
    return {"applied": applied, "skipped": skipped, "missing": missing}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--corrections", type=Path, default=CORRECTIONS_CSV)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()

    if not (args.dry_run or args.apply):
        print("Specify --dry-run or --apply.")
        return 2

    if hasattr(sys.stdout, "buffer"):
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace", line_buffering=True)

    with args.corrections.open(encoding="utf-8") as fh:
        all_props = list(csv.DictReader(fh))
    unamb = [r for r in all_props if r["status"] == "UNAMBIGUOUS"]
    print(f"Mode: {'DRY-RUN' if args.dry_run else 'APPLY'}")
    print(f"Loaded {len(unamb)} UNAMBIGUOUS proposals")

    by_dashboard: dict[str, list[dict]] = {}
    for r in unamb:
        by_dashboard.setdefault(r["dashboard"], []).append(r)
    print(f"Spread across {len(by_dashboard)} dashboards")

    totals = {"applied": 0, "skipped": 0, "missing": 0}
    for name, edits in sorted(by_dashboard.items()):
        path = ROOT / name
        if not path.exists():
            print(f"  MISSING dashboard: {name}")
            totals["missing"] += len(edits)
            continue
        r = patch_dashboard(path, edits, dry_run=args.dry_run)
        totals["applied"] += r["applied"]
        totals["skipped"] += r["skipped"]
        totals["missing"] += r["missing"]
        if r["applied"] or r["missing"]:
            print(f"  {name:42} applied={r['applied']:2} skipped={r['skipped']:2} missing={r['missing']:2}")
    print()
    print(f"Totals: {totals}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
