"""
Fix GRADE imprecision-width computation to handle negative MDs.

Original: const ciWidth = (_gLCI > 0 && _gUCI > 0) ? Math.log(_gUCI) - Math.log(_gLCI) : Infinity;

This sets ciWidth = Infinity for any continuous MD whose CI crosses 0 or
contains negatives, which then auto-downgrades GRADE imprecision regardless
of actual width. Wrong for MD-scale outcomes.

Fix: if both bounds positive, use log-ratio width (binary OR/RR convention).
Otherwise, use absolute width (MD convention). Cochrane Handbook §14.2 OIS
addresses imprecision; the absolute-difference convention is appropriate for
non-ratio scales.

Idempotent: skipped if "Math.abs(_gUCI - _gLCI)" already in src.

Usage: python scripts/fix_grade_imprecision_md.py [--dry-run]
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

REPLACEMENTS = [
    # Top-level renderGRADE (assigned function)
    (
        "            const ciWidth = (Number.isFinite(_gLCI) && Number.isFinite(_gUCI) && _gLCI > 0 && _gUCI > 0) ? Math.log(_gUCI) - Math.log(_gLCI) : Infinity;",
        "            // Use log-ratio width for OR/RR (both bounds positive); absolute width for MD/SMD.\n"
        "            const ciWidth = (Number.isFinite(_gLCI) && Number.isFinite(_gUCI))\n"
        "                ? ((_gLCI > 0 && _gUCI > 0) ? Math.log(_gUCI) - Math.log(_gLCI) : Math.abs(_gUCI - _gLCI))\n"
        "                : Infinity;",
    ),
    # Method-style renderGRADE (inside an object)
    (
        "                const ciWidth = (_gLCI > 0 && _gUCI > 0) ? Math.log(_gUCI) - Math.log(_gLCI) : Infinity;",
        "                // Use log-ratio width for OR/RR (both bounds positive); absolute width for MD/SMD.\n"
        "                const ciWidth = (Number.isFinite(_gLCI) && Number.isFinite(_gUCI))\n"
        "                    ? ((_gLCI > 0 && _gUCI > 0) ? Math.log(_gUCI) - Math.log(_gLCI) : Math.abs(_gUCI - _gLCI))\n"
        "                    : Infinity;",
    ),
]

FIXED_MARKER = "Math.abs(_gUCI - _gLCI)"


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
        if FIXED_MARKER in src:
            summary['unchanged'] += 1
            continue
        out = src
        for old, new in REPLACEMENTS:
            if old in out:
                out = out.replace(old, new, 1)
        if out != src:
            if not args.dry_run:
                open(path, 'w', encoding='utf-8').write(out)
            summary['changed'] += 1
        else:
            summary['unchanged'] += 1
    print(f'Summary: {summary}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
