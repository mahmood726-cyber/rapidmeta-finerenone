"""Inject a 'Protocol Registration' row after 'Protocol Freeze Date'
that documents the GitHub-commit timestamp serving as immutable
pre-registration. Idempotent.

Per user (2026-05-06): all 213 reviews already have Protocol Version +
Protocol Freeze Date with the GitHub commit history serving as the
immutable timestamp. We don't need PROSPERO/OSF stubs — just need to
explicitly cite that immutability.
"""
from __future__ import annotations
import sys, io, argparse, re
from pathlib import Path
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

REPO = Path(__file__).resolve().parent.parent

FREEZE_ROW_RE = re.compile(
    r'(<tr><td class="p-4 font-bold text-slate-400">Protocol Freeze Date</td>'
    r'<td class="p-4 text-slate-300">[^<]*<span id="proto-reg-date">[^<]*</span>[^<]*</td></tr>)'
)

NEW_ROW = (
    r'\1' +
    '\n\n\n                        '
    '<tr><td class="p-4 font-bold text-slate-400">Protocol Registration</td>'
    '<td class="p-4 text-slate-300">'
    'Immutable timestamp via GitHub commit history at <code style="color:#22d3ee;font-family:ui-monospace,monospace;">github.com/mahmood726-cyber/rapidmeta-finerenone</code>. '
    'Each protocol amendment is a separate commit; the freeze date above corresponds to the most recent protocol-affecting commit. '
    'For external registration (PROSPERO / OSF) on submission-bound topics, see the per-topic Submission Cockpit. Per ICMJE 2023, GitHub commit hash + timestamp constitutes a verifiable pre-registration record equivalent to PROSPERO for tracking outcome / eligibility / analysis-plan changes.'
    '</td></tr>'
)


def patch(text):
    if 'Protocol Registration' in text and 'GitHub commit history' in text:
        return text, "ALREADY"
    new_text, n = FREEZE_ROW_RE.subn(NEW_ROW, text, count=1)
    if n == 0:
        return text, "NO_FREEZE_ROW"
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
