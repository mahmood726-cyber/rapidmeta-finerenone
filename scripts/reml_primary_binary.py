"""
Switch primary tau2 estimator from DL to REML in the binary main pool.

Per Cochrane Handbook v6.5 / RevMan-2025: REML is the default tau2 estimator.
Currently the binary engine has REML as a sidecar (tau2_reml) but uses DL
for primary sWR weights, lci, uci, HKSJ, and PI.

Patch:
1. Rename `const tau2 = DL` -> `const tau2_dl = DL`
2. Change `let tau2_reml = tau2` -> `let tau2_reml = tau2_dl`
3. After REML iteration block, insert `const tau2 = (k >= 2) ? tau2_reml : tau2_dl`

All existing downstream code that uses `tau2` automatically gets REML.

Idempotent: skipped if `const tau2_dl =` already in src (binary path).
Limited to once per file at the binary main-pool location.

Usage: python scripts/reml_primary_binary.py [--dry-run]
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

# Anchor block: from DL tau2 declaration through end of REML iteration if-block,
# then the sWR pool start. We replace with renamed tau2_dl + post-REML primary tau2.
OLD = (
    "                const tau2 = (Q > df) ? (Q - df) / (sW - (sW2 / sW)) : 0;\n"
    "\n"
    "\n"
    "                /* REML tau-squared via Fisher scoring (Viechtbauer 2005) */\n"
    "\n"
    "\n"
    "                let tau2_reml = tau2; /* start from DL estimate */\n"
)
NEW = (
    "                // DL tau2 (kept as sensitivity sidecar, exposed via tau2_dl)\n"
    "                const tau2_dl = (Q > df) ? (Q - df) / (sW - (sW2 / sW)) : 0;\n"
    "\n"
    "\n"
    "                /* REML tau-squared via Fisher scoring (Viechtbauer 2005). */\n"
    "                /* Cochrane Handbook v6.5 / RevMan-2025: REML is the primary tau2. */\n"
    "\n"
    "\n"
    "                let tau2_reml = tau2_dl; /* start from DL estimate */\n"
)

# After the REML iteration's closing brace, insert primary tau2 declaration.
# Anchor: the closing `}` of `if (k >= 2) { ... }` followed by `let sWR = 0, sWRY = 0;`.
OLD_POST = (
    "                }\n"
    "\n"
    "\n"
    "                let sWR = 0, sWRY = 0;\n"
    "\n"
    "\n"
    "                plotData.forEach(d => { const wr = 1 / (d.vi + tau2); d.w_random = wr; sWR += wr; sWRY += wr * d.logOR; });"
)
NEW_POST = (
    "                }\n"
    "\n"
    "\n"
    "                // Primary tau2 = REML when k>=2 (Cochrane v6.5 default), else DL.\n"
    "                const tau2 = (k >= 2) ? tau2_reml : tau2_dl;\n"
    "\n"
    "\n"
    "                let sWR = 0, sWRY = 0;\n"
    "\n"
    "\n"
    "                plotData.forEach(d => { const wr = 1 / (d.vi + tau2); d.w_random = wr; sWR += wr; sWRY += wr * d.logOR; });"
)

FIXED_MARKER = "                const tau2_dl ="


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
        if OLD not in src or OLD_POST not in src:
            summary['no_anchor'] += 1
            continue
        out = src.replace(OLD, NEW, 1).replace(OLD_POST, NEW_POST, 1)
        if not args.dry_run:
            open(path, 'w', encoding='utf-8').write(out)
        summary['changed'] += 1
    print(f'Summary: {summary}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
