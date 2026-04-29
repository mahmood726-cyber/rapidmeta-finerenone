"""
Fix the HKSJ display path to handle continuous (MD) results correctly.

Pre-existing display logic assumes binary OR/RR-centered values:
- Clamps lower bound at 0.001 (wrong for negative MDs)
- Caps upper at 999 with '>10' label (wrong for absolute MDs)
- Significance check uses (lci > 1) || (uci < 1) (null at 1, not 0)

For continuous results, c.isContinuous === true, and the null is 0.

Patch: add an isContinuous branch that prints the raw HKSJ MD CI without
clamping, and use null=0 for the significance comparison.

Idempotent: skipped if file already contains the new conditional.

Usage: python scripts/fix_continuous_hksj_display.py [--dry-run]
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

OLD = (
    "                    const _hkLo = Math.max(0.001, c.hksjLCI);\n"
    "\n"
    "\n"
    "                    const _hkHi = Math.min(999, c.hksjUCI);\n"
    "\n"
    "\n"
    "                    const _hkCapped = c.hksjLCI < 0.001 || c.hksjUCI > 999;\n"
    "\n"
    "\n"
    "                    hksjEl.innerText = `${_hkLo.toFixed(2)} \\u2014 ${_hkHi > 10 ? '>10' : _hkHi.toFixed(2)}${_hkCapped ? ' *' : ''}`;\n"
    "\n"
    "\n"
    "                    const waldSig = (c.lci > 1) || (c.uci < 1);\n"
    "\n"
    "\n"
    "                    const hksjSig = (c.hksjLCI > 1) || (c.hksjUCI < 1);"
)

NEW = (
    "                    const _isCont = !!c.isContinuous;\n"
    "                    if (_isCont) {\n"
    "                        hksjEl.innerText = `${c.hksjLCI.toFixed(2)} \\u2014 ${c.hksjUCI.toFixed(2)}`;\n"
    "                    } else {\n"
    "                        const _hkLo = Math.max(0.001, c.hksjLCI);\n"
    "                        const _hkHi = Math.min(999, c.hksjUCI);\n"
    "                        const _hkCapped = c.hksjLCI < 0.001 || c.hksjUCI > 999;\n"
    "                        hksjEl.innerText = `${_hkLo.toFixed(2)} \\u2014 ${_hkHi > 10 ? '>10' : _hkHi.toFixed(2)}${_hkCapped ? ' *' : ''}`;\n"
    "                    }\n"
    "                    const _nullVal = _isCont ? 0 : 1;\n"
    "                    const waldSig = (c.lci > _nullVal) || (c.uci < _nullVal);\n"
    "                    const hksjSig = (c.hksjLCI > _nullVal) || (c.hksjUCI < _nullVal);"
)

FIXED_MARKER = "const _isCont = !!c.isContinuous;"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--dry-run', action='store_true')
    args = ap.parse_args()
    print(f'Mode: {"DRY-RUN" if args.dry_run else "APPLY"}')
    files = sorted(
        f for f in os.listdir(ROOT)
        if f.endswith('_REVIEW.html') and not f.endswith('.bak.html')
    )
    summary = {'changed': 0, 'unchanged': 0, 'no_anchor': 0}
    for fname in files:
        path = os.path.join(ROOT, fname)
        src = open(path, 'r', encoding='utf-8').read()
        if FIXED_MARKER in src:
            summary['unchanged'] += 1
            continue
        if OLD not in src:
            if 'res-hksj' in src:
                summary['no_anchor'] += 1
            else:
                summary['unchanged'] += 1
            continue
        out = src.replace(OLD, NEW, 1)
        if not args.dry_run:
            open(path, 'w', encoding='utf-8').write(out)
        summary['changed'] += 1
    print(f'Summary: {summary}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
