"""
Fix the second PRISMA (SVG version) showing zeros for PubMed/CT.gov/OpenAlex
on seeded dashboards.

Cause: PrismaEngine.generate() reads from `state.searchLog` (entries added
when user runs actual CT.gov/PubMed/OpenAlex search). Seeded dashboards
(realData populated at init) have empty searchLog -> counts are zero.

Fix: use Math.max of (searchLog yield, trials count by source). For
dashboards that ran real searches, the searchLog total is preserved (it's
the pre-dedup search yield, methodologically correct for PRISMA top-level).
For seeded dashboards, the trials-by-source count fills in.

Idempotent regex replacement.

Usage: python scripts/fix_prisma_svg_zeros.py
"""
import argparse, os, re, sys

ROOT = os.environ.get('RAPIDMETA_REPO_ROOT', os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


PATTERNS = [
    (
        "const ctgovN = searchLog.filter(l => l.source === 'registry').reduce((a, l) => a + (l.count ?? 0), 0);",
        "const ctgovN = Math.max(searchLog.filter(l => l.source === 'registry').reduce((a, l) => a + (l.count ?? 0), 0), trials.filter(t => t.source === 'registry').length);",
    ),
    (
        "const pubmedN = searchLog.filter(l => l.source === 'pubmed').reduce((a, l) => a + (l.count ?? 0), 0);",
        "const pubmedN = Math.max(searchLog.filter(l => l.source === 'pubmed').reduce((a, l) => a + (l.count ?? 0), 0), trials.filter(t => t.source === 'pubmed').length);",
    ),
    (
        "const oaN = searchLog.filter(l => l.source === 'openalex').reduce((a, l) => a + (l.count ?? 0), 0);",
        "const oaN = Math.max(searchLog.filter(l => l.source === 'openalex').reduce((a, l) => a + (l.count ?? 0), 0), trials.filter(t => t.source === 'openalex').length);",
    ),
]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--dry-run', action='store_true')
    args = ap.parse_args()
    print(f'Mode: {"DRY-RUN" if args.dry_run else "APPLY"}')
    files = sorted(f for f in os.listdir(ROOT) if f.endswith('_REVIEW.html') and not f.endswith('.bak.html'))
    summary = {'changed': 0, 'unchanged': 0}
    for fname in files:
        path = os.path.join(ROOT, fname)
        src = open(path, 'r', encoding='utf-8').read()
        original = src
        for old, new in PATTERNS:
            if old in src and new not in src:
                src = src.replace(old, new, 1)
        if src != original:
            if not args.dry_run:
                open(path, 'w', encoding='utf-8').write(src)
            summary['changed'] += 1
        else:
            summary['unchanged'] += 1
    print(f'Summary: {summary}')


if __name__ == '__main__':
    sys.exit(main())
