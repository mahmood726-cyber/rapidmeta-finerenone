"""
Add REML + HKSJ + PI computation to ContinuousMDEngine.pool().

Currently the engine returns:
    hksjLCI: NaN, hksjUCI: NaN, piLCI: NaN, piUCI: NaN

Patch:
1. Insert a REML iteration + HKSJ + PI computation block after the
   `const uci = pMD + zCrit * pSE;` line.
2. Replace the four `NaN` fields in the return with the computed values.
3. Add tau2_reml to the return for downstream consumers.

Formulas (matching binary engine convention):
- REML: Newton-Raphson iteration starting from DL tau²; max 100 iters
- HKSJ: q* = (1/df) Σ wr*(yi - mu)², adjFactor = max(1, q*),
  hksjSE = sqrt(adjFactor / Σwr), tCrit = qt(1-alpha/2, df=k-1),
  CI = pMD ± tCrit * hksjSE
- PI: piSE = sqrt(tau2 + pSE²), tCritPI = qt(1-alpha/2, df=k-2),
  PI = pMD ± tCritPI * piSE  (continuous: NO exp)

Idempotency: skipped if the file already contains "tau2_reml" inside
ContinuousMDEngine OR doesn't contain the exact NaN line.

Usage: python scripts/add_continuous_reml_hksj_pi.py [--dry-run]
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

# Anchor: end of the existing pSE-based CI computation in pool()
ANCHOR_OLD = (
    "        const uci = pMD + zCrit * pSE;\n"
    "\n"
    "\n"
    "\n"
    "\n"
    "\n"
    "        \n"
    "\n"
    "\n"
    "        \n"
    "\n"
    "\n"
    "        return {"
)

# REML + HKSJ + PI block, then return
ANCHOR_NEW = (
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
    "\n"
    "        // HKSJ adjustment (Hartung-Knapp-Sidik-Jonkman) on DL random-effects weights.\n"
    "        // Floor q* at 1 (max(1, q*)) to prevent CI narrowing below DL when Q < df.\n"
    "        let hksjLCI = NaN, hksjUCI = NaN;\n"
    "        if (k >= 2) {\n"
    "            let qStar = 0;\n"
    "            plotData.forEach(d => { qStar += d.w_random * Math.pow(d.md - pMD, 2); });\n"
    "            qStar = qStar / df;\n"
    "            const hksjAdj = Math.max(1, qStar);\n"
    "            const hksjSE = Math.sqrt(hksjAdj / sWR);\n"
    "            const tCritHKSJ = tQuantile(1 - (1 - confLevel) / 2, df);\n"
    "            hksjLCI = pMD - tCritHKSJ * hksjSE;\n"
    "            hksjUCI = pMD + tCritHKSJ * hksjSE;\n"
    "        }\n"
    "\n"
    "        // Prediction interval (Higgins 2009, t_{k-2}). NaN for k < 3.\n"
    "        const piSE = Math.sqrt(tau2 + pSE * pSE);\n"
    "        const tCritPI = (k >= 3) ? tQuantile(1 - (1 - confLevel) / 2, k - 2) : NaN;\n"
    "        const piLCI = (k >= 3) ? (pMD - tCritPI * piSE) : NaN;\n"
    "        const piUCI = (k >= 3) ? (pMD + tCritPI * piSE) : NaN;\n"
    "\n"
    "\n"
    "        return {"
)

# Replace the NaN line with real values + tau2_reml addition
NAN_LINE_OLD = "            hksjLCI: NaN, hksjUCI: NaN, piLCI: NaN, piUCI: NaN,"
NAN_LINE_NEW = "            hksjLCI, hksjUCI, piLCI, piUCI, tau2_reml,"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--dry-run', action='store_true')
    args = ap.parse_args()
    print(f'Mode: {"DRY-RUN" if args.dry_run else "APPLY"}')
    files = sorted(
        f for f in os.listdir(ROOT)
        if f.endswith('_REVIEW.html') and not f.endswith('.bak.html')
    )
    summary = {'changed': 0, 'unchanged': 0, 'no_anchor': 0, 'no_nan_line': 0}
    for fname in files:
        path = os.path.join(ROOT, fname)
        src = open(path, 'r', encoding='utf-8').read()
        # Skip if no ContinuousMDEngine in this file
        if 'const ContinuousMDEngine = {' not in src:
            summary['unchanged'] += 1
            continue
        # Idempotent
        if 'tau2_reml' in src and NAN_LINE_OLD not in src:
            summary['unchanged'] += 1
            continue
        if NAN_LINE_OLD not in src:
            summary['no_nan_line'] += 1
            continue
        if ANCHOR_OLD not in src:
            summary['no_anchor'] += 1
            continue
        out = src.replace(ANCHOR_OLD, ANCHOR_NEW, 1)
        out = out.replace(NAN_LINE_OLD, NAN_LINE_NEW, 1)
        if not args.dry_run:
            open(path, 'w', encoding='utf-8').write(out)
        summary['changed'] += 1
    print(f'Summary: {summary}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
