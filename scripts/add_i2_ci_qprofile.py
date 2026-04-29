"""
Add Q-profile-derived I² CI alongside the existing Higgins-Thompson test-based
CI in the binary engine, and add I² CI to the continuous engine.

I² = tau²/(tau² + s²) where s² is the typical within-study variance:
  s² = (k-1) * Σwᵢ / [(Σwᵢ)² - Σwᵢ²]   (Higgins-Thompson 2002 typical s²,
  with wᵢ = 1/vᵢ the fixed-effect weights).

I² CI from Q-profile tau² CI:
  I²_lo_qp = 100 * tau2_lo / (tau2_lo + s²)
  I²_hi_qp = 100 * tau2_hi / (tau2_hi + s²)

Per advanced-stats.md: "I² CI: Use Q-profile method (Viechtbauer 2007) for
small k." This is the RevMan-2025 default.

This script adds:
- Binary main pool: emits I2_lo_qp, I2_hi_qp alongside existing I2_lo, I2_hi.
- Continuous engine: emits I2_lo, I2_hi (Q-profile-derived; engine had none).

Idempotent: skipped if 'I2_lo_qp' already in src for the relevant engine.

Usage: python scripts/add_i2_ci_qprofile.py [--dry-run]
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

# Continuous engine: append I² CI computation right after Q-profile tau² block.
# Insert before the HKSJ block (which uses sWR; we need s² from fixed-effect weights).
CONT_OLD = (
    "        // Q-profile tau2 CI (Cochrane v6.5 / RevMan-2025: tau2 CI by Q-profile).\n"
    "        const _qpYi = plotData.map(d => d.md);\n"
    "        const _qpVi = plotData.map(d => d.vi);\n"
    "        const { tau2_lo: tau2Lo, tau2_hi: tau2Hi } = qProfileTau2CI(_qpYi, _qpVi, df, 1 - confLevel);\n"
)
CONT_NEW = (
    CONT_OLD
    + "\n"
    + "        // I² CI via Q-profile tau² CI (Cochrane v6.5; Viechtbauer 2007).\n"
    + "        // Higgins-Thompson typical within-study variance s² used to map tau² -> I².\n"
    + "        let I2_lo = 0, I2_hi = 0;\n"
    + "        if (k >= 2) {\n"
    + "            const _wfx = _qpVi.map(v => 1 / v);\n"
    + "            const _sWfx = _wfx.reduce((a, b) => a + b, 0);\n"
    + "            const _sWfx2 = _wfx.reduce((a, w) => a + w * w, 0);\n"
    + "            const _denom = (_sWfx * _sWfx) - _sWfx2;\n"
    + "            const _s2 = (_denom > 0) ? ((k - 1) * _sWfx) / _denom : 0;\n"
    + "            if (_s2 > 0) {\n"
    + "                I2_lo = Number.isFinite(tau2Lo) ? Math.max(0, 100 * tau2Lo / (tau2Lo + _s2)) : 0;\n"
    + "                I2_hi = Number.isFinite(tau2Hi) ? Math.min(100, 100 * tau2Hi / (tau2Hi + _s2)) : 0;\n"
    + "            }\n"
    + "        }\n"
)
CONT_RETURN_OLD = (
    "            hksjLCI, hksjUCI, piLCI, piUCI, tau2_reml, tau2Lo, tau2Hi,"
)
CONT_RETURN_NEW = (
    "            hksjLCI, hksjUCI, piLCI, piUCI, tau2_reml, tau2Lo, tau2Hi, I2_lo, I2_hi,"
)

# Binary main pool: append I2_lo_qp, I2_hi_qp before the existing return.
# Anchor the pre-existing test-based block; insert Q-profile lines just before
# the return statement.
BIN_OLD = (
    "                // Q-profile tau2 CI (Cochrane v6.5 / RevMan-2025: tau2 CI by Q-profile).\n"
    "                const _qpYi = plotData.map(d => d.logOR);\n"
    "                const _qpVi = plotData.map(d => d.vi);\n"
    "                const { tau2_lo: tau2Lo, tau2_hi: tau2Hi } = qProfileTau2CI(_qpYi, _qpVi, df, 1 - confLevel);\n"
)
BIN_NEW = (
    BIN_OLD
    + "\n"
    + "                // I² CI via Q-profile tau² CI (Cochrane v6.5).\n"
    + "                let I2_lo_qp = 0, I2_hi_qp = 0;\n"
    + "                if (k >= 2) {\n"
    + "                    const _wfx = _qpVi.map(v => 1 / v);\n"
    + "                    const _sWfx = _wfx.reduce((a, b) => a + b, 0);\n"
    + "                    const _sWfx2 = _wfx.reduce((a, w) => a + w * w, 0);\n"
    + "                    const _denom = (_sWfx * _sWfx) - _sWfx2;\n"
    + "                    const _s2 = (_denom > 0) ? ((k - 1) * _sWfx) / _denom : 0;\n"
    + "                    if (_s2 > 0) {\n"
    + "                        I2_lo_qp = Number.isFinite(tau2Lo) ? Math.max(0, 100 * tau2Lo / (tau2Lo + _s2)) : 0;\n"
    + "                        I2_hi_qp = Number.isFinite(tau2Hi) ? Math.min(100, 100 * tau2Hi / (tau2Hi + _s2)) : 0;\n"
    + "                    }\n"
    + "                }\n"
)
BIN_RETURN_OLD = (
    "                return { plotData, Q, k, df, I2, tau2, tau2_dl, tau2_reml, tau2Lo, tau2Hi, sWR, pLogOR, pSE, confLevel, zCrit, pOR, lci, uci, hksjLCI, hksjUCI, piLCI, piUCI, qPvalue, eggerResult, fragIdx, fragQuot, useHR, I2_lo, I2_hi };"
)
BIN_RETURN_NEW = (
    "                return { plotData, Q, k, df, I2, tau2, tau2_dl, tau2_reml, tau2Lo, tau2Hi, sWR, pLogOR, pSE, confLevel, zCrit, pOR, lci, uci, hksjLCI, hksjUCI, piLCI, piUCI, qPvalue, eggerResult, fragIdx, fragQuot, useHR, I2_lo, I2_hi, I2_lo_qp, I2_hi_qp };"
)

FIXED_MARKER = "I2_lo_qp"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--dry-run', action='store_true')
    args = ap.parse_args()
    print(f'Mode: {"DRY-RUN" if args.dry_run else "APPLY"}')
    files = sorted(
        f for f in os.listdir(ROOT)
        if f.endswith('_REVIEW.html') and not f.endswith('.bak.html')
    )
    summary = {'cont_changed': 0, 'bin_changed': 0, 'unchanged': 0}
    for fname in files:
        path = os.path.join(ROOT, fname)
        src = open(path, 'r', encoding='utf-8').read()
        out = src
        cont_done = bin_done = False
        if 'I2_lo_qp' not in out and BIN_OLD in out:
            out = out.replace(BIN_OLD, BIN_NEW, 1)
            if BIN_RETURN_OLD in out:
                out = out.replace(BIN_RETURN_OLD, BIN_RETURN_NEW, 1)
            bin_done = True
        # Continuous I² CI: skip if continuous return already has I2_lo, I2_hi
        if 'tau2_reml, tau2Lo, tau2Hi, I2_lo, I2_hi,' not in out and CONT_OLD in out:
            out = out.replace(CONT_OLD, CONT_NEW, 1)
            if CONT_RETURN_OLD in out:
                out = out.replace(CONT_RETURN_OLD, CONT_RETURN_NEW, 1)
            cont_done = True
        if cont_done:
            summary['cont_changed'] += 1
        if bin_done:
            summary['bin_changed'] += 1
        if not (cont_done or bin_done):
            summary['unchanged'] += 1
            continue
        if not args.dry_run:
            open(path, 'w', encoding='utf-8').write(out)
    print(f'Summary: {summary}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
