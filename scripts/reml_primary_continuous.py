"""
Switch primary tau2 estimator from DL to REML in ContinuousMDEngine.pool().

Per Cochrane Handbook v6.5 / RevMan-2025: REML is the default tau-squared
estimator for random-effects pooling. The current engine has REML as a
sidecar (tau2_reml) but uses DL for primary sWR weights.

Restructure: compute REML BEFORE sWR/pMD/pSE/lci/uci, then use REML tau2
for all weight-dependent quantities. DL preserved as tau2_dl for sensitivity.

Idempotent: skipped if `const tau2_dl =` already present.

Usage: python scripts/reml_primary_continuous.py [--dry-run]
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
    "        const tau2 = (Q > df) ? (Q - df) / (sW - (sW2 / sW)) : 0;\n"
    "\n"
    "\n"
    "        \n"
    "\n"
    "\n"
    "        let sWR = 0, sWRY = 0;\n"
    "\n"
    "\n"
    "        plotData.forEach(d => { const wr = 1 / (d.vi + tau2); d.w_random = wr; sWR += wr; sWRY += wr * d.md; });\n"
    "\n"
    "\n"
    "        const pMD = sWRY / sWR;\n"
    "\n"
    "\n"
    "        const pSE = Math.sqrt(1/sWR);\n"
    "\n"
    "\n"
    "        \n"
    "\n"
    "\n"
    "        const lci = pMD - zCrit * pSE;\n"
    "\n"
    "\n"
    "        const uci = pMD + zCrit * pSE;\n"
    "\n"
    "\n"
    "        // REML iteration starting from DL tau2\n"
    "        let tau2_reml = tau2;\n"
    "        if (k >= 2) {\n"
    "            const _yi = plotData.map(d => d.md);\n"
    "            const _vi = plotData.map(d => d.vi);\n"
    "            for (let _it = 0; _it < 100; _it++) {\n"
    "                const _w = _vi.map(v => 1 / (v + tau2_reml));\n"
    "                const _sW = _w.reduce((a, b) => a + b, 0);\n"
    "                const _mu = _w.reduce((a, wi, i) => a + wi * _yi[i], 0) / _sW;\n"
    "                const _sW2 = _w.reduce((a, wi) => a + wi * wi, 0);\n"
    "                const _sW3 = _w.reduce((a, wi) => a + wi * wi * wi, 0);\n"
    "                const _trP = _sW - _sW2 / _sW;\n"
    "                const _yP2y = _w.reduce((a, wi, i) => a + wi * wi * Math.pow(_yi[i] - _mu, 2), 0);\n"
    "                const _trP2 = _sW2 - 2 * _sW3 / _sW + _sW2 * _sW2 / (_sW * _sW);\n"
    "                if (_trP2 < 1e-15) break;\n"
    "                const _delta = (_yP2y - _trP) / _trP2;\n"
    "                const _new = Math.max(0, tau2_reml + _delta);\n"
    "                if (Math.abs(_new - tau2_reml) < 1e-10) { tau2_reml = _new; break; }\n"
    "                tau2_reml = _new;\n"
    "            }\n"
    "        }\n"
)

NEW = (
    "        // DL tau2 (kept as sensitivity sidecar, exposed via tau2_dl)\n"
    "        const tau2_dl = (Q > df) ? (Q - df) / (sW - (sW2 / sW)) : 0;\n"
    "\n"
    "        // REML iteration starting from DL (Viechtbauer 2005 Fisher scoring).\n"
    "        // Cochrane Handbook v6.5 / RevMan-2025: REML is the primary tau2 estimator.\n"
    "        let tau2_reml = tau2_dl;\n"
    "        if (k >= 2) {\n"
    "            const _yi = plotData.map(d => d.md);\n"
    "            const _vi = plotData.map(d => d.vi);\n"
    "            for (let _it = 0; _it < 100; _it++) {\n"
    "                const _w = _vi.map(v => 1 / (v + tau2_reml));\n"
    "                const _sW = _w.reduce((a, b) => a + b, 0);\n"
    "                const _mu = _w.reduce((a, wi, i) => a + wi * _yi[i], 0) / _sW;\n"
    "                const _sW2 = _w.reduce((a, wi) => a + wi * wi, 0);\n"
    "                const _sW3 = _w.reduce((a, wi) => a + wi * wi * wi, 0);\n"
    "                const _trP = _sW - _sW2 / _sW;\n"
    "                const _yP2y = _w.reduce((a, wi, i) => a + wi * wi * Math.pow(_yi[i] - _mu, 2), 0);\n"
    "                const _trP2 = _sW2 - 2 * _sW3 / _sW + _sW2 * _sW2 / (_sW * _sW);\n"
    "                if (_trP2 < 1e-15) break;\n"
    "                const _delta = (_yP2y - _trP) / _trP2;\n"
    "                const _new = Math.max(0, tau2_reml + _delta);\n"
    "                if (Math.abs(_new - tau2_reml) < 1e-10) { tau2_reml = _new; break; }\n"
    "                tau2_reml = _new;\n"
    "            }\n"
    "        }\n"
    "        // Primary tau2 = REML when k>=2, else DL (which equals 0 anyway when Q<=df).\n"
    "        const tau2 = (k >= 2) ? tau2_reml : tau2_dl;\n"
    "\n"
    "        // Random-effects pooling using REML weights (Cochrane v6.5 default)\n"
    "        let sWR = 0, sWRY = 0;\n"
    "        plotData.forEach(d => { const wr = 1 / (d.vi + tau2); d.w_random = wr; sWR += wr; sWRY += wr * d.md; });\n"
    "        const pMD = sWRY / sWR;\n"
    "        const pSE = Math.sqrt(1/sWR);\n"
    "        const lci = pMD - zCrit * pSE;\n"
    "        const uci = pMD + zCrit * pSE;\n"
)

FIXED_MARKER = "const tau2_dl ="

# Variant 2: alias-style ContinuousMDEngine (22 files) — has an alias forEach
# between pSE and lci. Preserve the alias.
OLD_ALIAS = (
    "        const tau2 = (Q > df) ? (Q - df) / (sW - (sW2 / sW)) : 0;\n"
    "\n"
    "\n"
    "        \n"
    "\n"
    "\n"
    "        let sWR = 0, sWRY = 0;\n"
    "\n"
    "\n"
    "        plotData.forEach(d => { const wr = 1 / (d.vi + tau2); d.w_random = wr; sWR += wr; sWRY += wr * d.md; });\n"
    "\n"
    "\n"
    "        const pMD = sWRY / sWR;\n"
    "\n"
    "\n"
    "        const pSE = Math.sqrt(1/sWR);\n"
    "\n"
    "\n"
    "        // Alias md->logOR, name->id so existing OR/HR-shaped consumers (renderPlots\n"
    "        // forest/subgroup/cumulative) read MD values without rewriting their schema.\n"
    "        // Linear-scale renderers must check r.isContinuous and skip exp() back-transforms.\n"
    "        plotData.forEach(d => { d.logOR = d.md; d.id = d.name; d.group = d.group ?? 'Treatment vs comparator'; d.tE = d.tE ?? 0; d.cE = d.cE ?? 0; d.tN = d.tN ?? 0; d.cN = d.cN ?? 0; });\n"
    "\n"
    "\n"
    "\n"
    "\n"
    "\n"
    "        const lci = pMD - zCrit * pSE;\n"
    "\n"
    "\n"
    "        const uci = pMD + zCrit * pSE;\n"
    "\n"
    "\n"
    "        // REML iteration starting from DL tau2\n"
    "        let tau2_reml = tau2;\n"
    "        if (k >= 2) {\n"
    "            const _yi = plotData.map(d => d.md);\n"
    "            const _vi = plotData.map(d => d.vi);\n"
    "            for (let _it = 0; _it < 100; _it++) {\n"
    "                const _w = _vi.map(v => 1 / (v + tau2_reml));\n"
    "                const _sW = _w.reduce((a, b) => a + b, 0);\n"
    "                const _mu = _w.reduce((a, wi, i) => a + wi * _yi[i], 0) / _sW;\n"
    "                const _sW2 = _w.reduce((a, wi) => a + wi * wi, 0);\n"
    "                const _sW3 = _w.reduce((a, wi) => a + wi * wi * wi, 0);\n"
    "                const _trP = _sW - _sW2 / _sW;\n"
    "                const _yP2y = _w.reduce((a, wi, i) => a + wi * wi * Math.pow(_yi[i] - _mu, 2), 0);\n"
    "                const _trP2 = _sW2 - 2 * _sW3 / _sW + _sW2 * _sW2 / (_sW * _sW);\n"
    "                if (_trP2 < 1e-15) break;\n"
    "                const _delta = (_yP2y - _trP) / _trP2;\n"
    "                const _new = Math.max(0, tau2_reml + _delta);\n"
    "                if (Math.abs(_new - tau2_reml) < 1e-10) { tau2_reml = _new; break; }\n"
    "                tau2_reml = _new;\n"
    "            }\n"
    "        }\n"
)

NEW_ALIAS = (
    "        // DL tau2 (kept as sensitivity sidecar, exposed via tau2_dl)\n"
    "        const tau2_dl = (Q > df) ? (Q - df) / (sW - (sW2 / sW)) : 0;\n"
    "\n"
    "        // REML iteration starting from DL (Viechtbauer 2005 Fisher scoring).\n"
    "        // Cochrane Handbook v6.5 / RevMan-2025: REML is the primary tau2 estimator.\n"
    "        let tau2_reml = tau2_dl;\n"
    "        if (k >= 2) {\n"
    "            const _yi = plotData.map(d => d.md);\n"
    "            const _vi = plotData.map(d => d.vi);\n"
    "            for (let _it = 0; _it < 100; _it++) {\n"
    "                const _w = _vi.map(v => 1 / (v + tau2_reml));\n"
    "                const _sW = _w.reduce((a, b) => a + b, 0);\n"
    "                const _mu = _w.reduce((a, wi, i) => a + wi * _yi[i], 0) / _sW;\n"
    "                const _sW2 = _w.reduce((a, wi) => a + wi * wi, 0);\n"
    "                const _sW3 = _w.reduce((a, wi) => a + wi * wi * wi, 0);\n"
    "                const _trP = _sW - _sW2 / _sW;\n"
    "                const _yP2y = _w.reduce((a, wi, i) => a + wi * wi * Math.pow(_yi[i] - _mu, 2), 0);\n"
    "                const _trP2 = _sW2 - 2 * _sW3 / _sW + _sW2 * _sW2 / (_sW * _sW);\n"
    "                if (_trP2 < 1e-15) break;\n"
    "                const _delta = (_yP2y - _trP) / _trP2;\n"
    "                const _new = Math.max(0, tau2_reml + _delta);\n"
    "                if (Math.abs(_new - tau2_reml) < 1e-10) { tau2_reml = _new; break; }\n"
    "                tau2_reml = _new;\n"
    "            }\n"
    "        }\n"
    "        // Primary tau2 = REML when k>=2, else DL.\n"
    "        const tau2 = (k >= 2) ? tau2_reml : tau2_dl;\n"
    "\n"
    "        // Random-effects pooling using REML weights (Cochrane v6.5 default)\n"
    "        let sWR = 0, sWRY = 0;\n"
    "        plotData.forEach(d => { const wr = 1 / (d.vi + tau2); d.w_random = wr; sWR += wr; sWRY += wr * d.md; });\n"
    "        const pMD = sWRY / sWR;\n"
    "        const pSE = Math.sqrt(1/sWR);\n"
    "\n"
    "        // Alias md->logOR, name->id so existing OR/HR-shaped consumers (renderPlots\n"
    "        // forest/subgroup/cumulative) read MD values without rewriting their schema.\n"
    "        plotData.forEach(d => { d.logOR = d.md; d.id = d.name; d.group = d.group ?? 'Treatment vs comparator'; d.tE = d.tE ?? 0; d.cE = d.cE ?? 0; d.tN = d.tN ?? 0; d.cN = d.cN ?? 0; });\n"
    "\n"
    "        const lci = pMD - zCrit * pSE;\n"
    "        const uci = pMD + zCrit * pSE;\n"
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
    summary = {'changed': 0, 'unchanged': 0, 'no_anchor': 0}
    for fname in files:
        path = os.path.join(ROOT, fname)
        src = open(path, 'r', encoding='utf-8').read()
        if FIXED_MARKER in src:
            summary['unchanged'] += 1
            continue
        if 'const ContinuousMDEngine = {' not in src:
            summary['unchanged'] += 1
            continue
        if OLD in src:
            out = src.replace(OLD, NEW, 1)
        elif OLD_ALIAS in src:
            out = src.replace(OLD_ALIAS, NEW_ALIAS, 1)
        else:
            # Variant 3: alias-style with arbitrary d.group fallback string
            import re
            esc = re.escape(OLD_ALIAS)
            search_token = re.escape("'Treatment vs comparator'")
            alias_re = re.compile(esc.replace(search_token, r"'[^']+'"))
            m = alias_re.search(src)
            if not m:
                summary['no_anchor'] += 1
                continue
            mg = re.search(r"d\.group = d\.group \?\? '([^']+)';", m.group(0))
            group_str = mg.group(1) if mg else 'Treatment vs comparator'
            new_alias_specific = NEW_ALIAS.replace(
                "'Treatment vs comparator'",
                f"'{group_str}'",
                1,
            )
            out = src.replace(m.group(0), new_alias_specific, 1)
        if not args.dry_run:
            open(path, 'w', encoding='utf-8').write(out)
        summary['changed'] += 1
    print(f'Summary: {summary}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
