"""
Dedupe consecutive duplicate `pmid: 'X'` declarations in trial-entry headers.

The Sentinel rule P0-rapidmeta-data-integrity flagged 12 entries across 2 files
where the same pmid was declared 2-3 times in a row (template copy-paste
bug). JS keeps the last one silently; the duplicates are dead but block
push under the new rule.

Idempotent: collapses any sequence of identical `pmid: 'X', pmid: 'X', ...`
into a single `pmid: 'X',`.

Usage:
    python scripts/dedupe_pmid_fields.py --dry-run
    python scripts/dedupe_pmid_fields.py
"""
import argparse, os, re, sys

ROOT = r'C:\Projects\Finrenone'

# Match 2+ consecutive identical pmid declarations and replace with a single one.
# Capture the first declaration; backreference enforces "same value".
DUP_PMID_RE = re.compile(
    r"(pmid:\s*'([^']*)',\s+)pmid:\s*'\2',(?:\s+pmid:\s*'\2',)*",
)


def patch_file(path, dry=False):
    src = open(path, 'r', encoding='utf-8').read()
    new_src, n = DUP_PMID_RE.subn(r'\1', src)
    if n == 0:
        return False, 'no_dupes'
    if not dry:
        open(path, 'w', encoding='utf-8').write(new_src)
    return True, f'collapsed {n} dup-pmid run(s)'


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--dry-run', action='store_true')
    args = ap.parse_args()
    print(f'Mode: {"DRY-RUN" if args.dry_run else "APPLY"}')

    files = sorted([f for f in os.listdir(ROOT) if f.endswith('_REVIEW.html') and not f.endswith('.bak.html')])
    summary = {'changed': 0, 'unchanged': 0}
    for fname in files:
        path = os.path.join(ROOT, fname)
        try:
            changed, info = patch_file(path, dry=args.dry_run)
            if changed:
                print(f'  [CHANGED] {fname}: {info}')
                summary['changed'] += 1
            else:
                summary['unchanged'] += 1
        except Exception as e:
            print(f'  [ERROR] {fname}: {e}')
    print(f'\nSummary: {summary}')


if __name__ == '__main__':
    sys.exit(main())
