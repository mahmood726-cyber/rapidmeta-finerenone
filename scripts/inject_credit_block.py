"""Inject a CRediT contributor-roles row + AI-assistance disclosure
after the existing 'Conflicts of Interest' row in the registration
table. Idempotent.

Existing rows:
  - Funding Source            (already populated)
  - Conflicts of Interest     (already populated)
  + ADD: Contributor Roles (CRediT)
  + ADD: AI Assistance (ICMJE 2023 disclosure)

Both new rows use a standard template editable per-topic later if
specific contributions differ.
"""
from __future__ import annotations
import sys, io, argparse, re
from pathlib import Path
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

REPO = Path(__file__).resolve().parent.parent

COI_ROW_RE = re.compile(
    r'(<tr><td class="p-4 font-bold text-slate-400">Conflicts of Interest</td>'
    r'<td class="p-4 text-slate-300">[^<]*</td></tr>)'
)

NEW_ROWS = (
    r'\1' +
    '\n\n\n                        '
    '<tr><td class="p-4 font-bold text-slate-400">Contributor Roles (CRediT)</td>'
    '<td class="p-4 text-slate-300">'
    'MA &mdash; Conceptualization, Methodology, Data Curation, Writing (Original Draft &amp; Review &amp; Editing), Supervision. '
    'Per ICMJE 2023: human author takes full responsibility for accuracy and integrity of the work, including all AI-assisted components.'
    '</td></tr>\n\n\n                        '
    '<tr><td class="p-4 font-bold text-slate-400">AI Assistance Disclosure</td>'
    '<td class="p-4 text-slate-300">'
    'AI tools (Claude / Anthropic) provided: (a) automated audit tooling implementation '
    '(internal-consistency, fragility-index, PI-gap, GRIM/Benford, AACT cross-check, PMID DataBankList verification), '
    '(b) statistical module implementation (DerSimonian-Laird+REML+HKSJ pooling, node-splitting, Doi/LFK, comparison-adjusted funnel, CINeMA-lite, POTH, Q-decomposition, contribution matrix), '
    '(c) initial drafts of summary text subject to human verification. AI is NOT listed as an author per ICMJE 2023; AI cannot take responsibility for a manuscript. '
    'All AI-generated content was reviewed and verified by the human author. The audit/extraction infrastructure is open-source at the GitHub repository for independent verification.'
    '</td></tr>'
)


def patch(text):
    if 'Contributor Roles (CRediT)' in text:
        return text, "ALREADY"
    new_text, n = COI_ROW_RE.subn(NEW_ROWS, text, count=1)
    if n == 0:
        return text, "NO_COI_ROW"
    return new_text, "PATCHED"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    files = sorted(REPO.glob("*_REVIEW.html"))
    print(f"Patching {len(files)} review HTMLs ...")
    counts = {}
    for hp in files:
        text = hp.read_text(encoding="utf-8", errors="replace")
        new_text, status = patch(text)
        counts[status] = counts.get(status, 0) + 1
        if status == "PATCHED" and not args.dry_run:
            hp.write_text(new_text, encoding="utf-8")

    print(f"\n=== Summary ===")
    for k, v in sorted(counts.items(), key=lambda x: -x[1]):
        print(f"  {k:25s} {v}")
    if args.dry_run:
        print("  DRY RUN — no files written.")


if __name__ == "__main__":
    main()
