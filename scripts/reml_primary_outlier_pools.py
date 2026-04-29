"""
Add REML iteration + REML primary tau2 to the 3 outlier binary pools that
use a simpler `(Q > df && sW > 0)` guard format.

Currently these 3 dashboards (COLCHICINE_CVD, GLP1_CVOT, SGLT2_HF) use a
DL-only pool. After this script, primary tau2 = REML when k>=2.

Anchors are line-by-line, idempotent.

Usage: python scripts/reml_primary_outlier_pools.py [--dry-run]
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
    "                const tau2 = (Q > df && sW > 0) ? (Q - df) / (sW - (sW2 / sW)) : 0;\n"
)
NEW = (
    "                // DL tau2 (kept as sensitivity sidecar, exposed via tau2_dl)\n"
    "                const tau2_dl = (Q > df && sW > 0) ? (Q - df) / (sW - (sW2 / sW)) : 0;\n"
    "\n"
    "                // REML iteration starting from DL (Cochrane v6.5 / RevMan-2025: REML primary).\n"
    "                let tau2_reml = tau2_dl;\n"
    "                if (k >= 2) {\n"
    "                    const _yi = plotData.map(d => d.logOR);\n"
    "                    const _vi = plotData.map(d => d.vi);\n"
    "                    for (let _it = 0; _it < 100; _it++) {\n"
    "                        const _w = _vi.map(v => 1 / (v + tau2_reml));\n"
    "                        const _sW = _w.reduce((a, b) => a + b, 0);\n"
    "                        const _mu = _w.reduce((a, wi, i) => a + wi * _yi[i], 0) / _sW;\n"
    "                        const _sW2 = _w.reduce((a, wi) => a + wi * wi, 0);\n"
    "                        const _sW3 = _w.reduce((a, wi) => a + wi * wi * wi, 0);\n"
    "                        const _trP = _sW - _sW2 / _sW;\n"
    "                        const _yP2y = _w.reduce((a, wi, i) => a + wi * wi * Math.pow(_yi[i] - _mu, 2), 0);\n"
    "                        const _trP2 = _sW2 - 2 * _sW3 / _sW + _sW2 * _sW2 / (_sW * _sW);\n"
    "                        if (_trP2 < 1e-15) break;\n"
    "                        const _delta = (_yP2y - _trP) / _trP2;\n"
    "                        const _new = Math.max(0, tau2_reml + _delta);\n"
    "                        if (Math.abs(_new - tau2_reml) < 1e-10) { tau2_reml = _new; break; }\n"
    "                        tau2_reml = _new;\n"
    "                    }\n"
    "                }\n"
    "                // Primary tau2 = REML when k>=2 (Cochrane v6.5 default), else DL.\n"
    "                const tau2 = (k >= 2) ? tau2_reml : tau2_dl;\n"
)

FIXED_MARKER = "                const tau2_dl = (Q > df && sW > 0)"


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
        if OLD not in src:
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
