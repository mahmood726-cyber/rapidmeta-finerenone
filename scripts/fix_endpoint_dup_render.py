"""
Fix the trialSurveillance table's duplicate-looking 'Current Endpoint' column.

Problem: Both 'Registered Primary' and 'Current Endpoint' cells render the
same outcome text by default (when the user has not switched outcomes),
making the primary outcome appear twice per row.

Fix: When currentEndpoint === registeredPrimary, render an italic
'— matches registered' indicator instead of repeating the text.

Idempotent: only applies when the unfixed pattern is present.

Usage: python scripts/fix_endpoint_dup_render.py [--dry-run]
"""
import argparse
import io
import os
import sys

if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

ROOT = os.environ.get(
    'RAPIDMETA_REPO_ROOT',
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
)

OLD = '<td class="p-3">${escapeHtml(row.currentEndpoint)}</td>'
NEW = (
    '<td class="p-3">${row.currentEndpoint === row.registeredPrimary '
    '? \'<span class="text-slate-500 italic text-[10px]">&mdash; matches registered</span>\' '
    ': escapeHtml(row.currentEndpoint)}</td>'
)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--dry-run', action='store_true')
    args = ap.parse_args()
    print(f'Mode: {"DRY-RUN" if args.dry_run else "APPLY"}')
    files = sorted(
        f for f in os.listdir(ROOT)
        if f.endswith('_REVIEW.html') and not f.endswith('.bak.html')
    )
    summary = {'changed': 0, 'unchanged': 0}
    for fname in files:
        path = os.path.join(ROOT, fname)
        src = open(path, 'r', encoding='utf-8').read()
        if OLD in src and NEW not in src:
            out = src.replace(OLD, NEW, 1)
            if not args.dry_run:
                open(path, 'w', encoding='utf-8').write(out)
            summary['changed'] += 1
        else:
            summary['unchanged'] += 1
    print(f'Summary: {summary}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
