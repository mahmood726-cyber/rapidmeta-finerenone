"""
Add Q-profile tau2 CI (Viechtbauer 2007) to ContinuousMDEngine and binary
main pool. Required for Cochrane Handbook v6.5 / RevMan-2025 reproducibility.

Helpers added (once per file):
- qchisq(p, df): chi-square quantile via Wilson-Hilferty cube-root inverse
- qProfileTau2CI(yi, vi, df, alpha): bisection on Q_GEN(tau^2) = chi-square cutoff

Integration:
- Continuous engine: compute tau2_lo/tau2_hi after REML iteration; expose in
  return (`tau2Lo`, `tau2Hi`).
- Binary engine: same.

Idempotent: skipped if 'qProfileTau2CI' already in file.

Usage: python scripts/add_qprofile_tau2_ci.py [--dry-run]
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

# ---- Helpers to insert AFTER tQuantile and BEFORE chi2Pvalue ----
HELPERS_ANCHOR_OLD = (
    "        const tPvalue2tail = (t, df) => {\n"
    "\n"
    "\n"
    "            if (df <= 0) return 2 * (1 - normalCDF(Math.abs(t)));\n"
    "\n"
    "\n"
    "            return betaIncomplete(df / (df + t * t), df / 2, 0.5);\n"
    "\n"
    "\n"
    "        };\n"
)

HELPERS_ANCHOR_NEW = (
    HELPERS_ANCHOR_OLD
    + "\n"
    + "\n"
    + "\n"
    + "\n"
    + "        // Chi-square quantile via Wilson-Hilferty inverse (sufficient for df >= 1).\n"
    + "        const qchisq = (p, df) => {\n"
    + "            if (df <= 0) return NaN;\n"
    + "            const z = normalQuantile(p);\n"
    + "            const v = 1 - 2/(9*df) + z * Math.sqrt(2/(9*df));\n"
    + "            return Math.max(0, df * v * v * v);\n"
    + "        };\n"
    + "\n"
    + "\n"
    + "\n"
    + "\n"
    + "        // Q-profile tau-squared CI (Viechtbauer 2007).\n"
    + "        // Q_GEN(tau2) = sum w_i(tau2) (y_i - mu_w(tau2))^2.\n"
    + "        // tau2_lo: largest tau2 with Q_GEN(tau2) >= qchisq(1-alpha/2, df).\n"
    + "        // tau2_hi: largest tau2 with Q_GEN(tau2) >= qchisq(alpha/2, df).\n"
    + "        const qProfileTau2CI = (yi, vi, df, alpha) => {\n"
    + "            if (df < 1 || yi.length < 2) return { tau2_lo: NaN, tau2_hi: NaN };\n"
    + "            const qGen = (tau2) => {\n"
    + "                let sW = 0, sWY = 0, sW_Y2 = 0;\n"
    + "                for (let i = 0; i < yi.length; i++) {\n"
    + "                    const w = 1 / (vi[i] + tau2);\n"
    + "                    sW += w;\n"
    + "                    sWY += w * yi[i];\n"
    + "                    sW_Y2 += w * yi[i] * yi[i];\n"
    + "                }\n"
    + "                if (sW === 0) return 0;\n"
    + "                return Math.max(0, sW_Y2 - (sWY * sWY) / sW);\n"
    + "            };\n"
    + "            const cutHi = qchisq(1 - alpha/2, df);\n"
    + "            const cutLo = qchisq(alpha/2, df);\n"
    + "            const Q0 = qGen(0);\n"
    + "            const bisect = (target) => {\n"
    + "                if (Q0 <= target) return 0;\n"
    + "                let lo = 0, hi = 100;\n"
    + "                for (let _e = 0; _e < 30 && qGen(hi) > target && hi < 1e8; _e++) hi *= 2;\n"
    + "                for (let _i = 0; _i < 60; _i++) {\n"
    + "                    const mid = (lo + hi) / 2;\n"
    + "                    if (qGen(mid) > target) lo = mid; else hi = mid;\n"
    + "                }\n"
    + "                return (lo + hi) / 2;\n"
    + "            };\n"
    + "            return { tau2_lo: bisect(cutHi), tau2_hi: bisect(cutLo) };\n"
    + "        };\n"
)

# ---- Continuous engine integration ----
# Insert Q-profile call after the REML iteration block (using the post-fix structure).
CONT_OLD = (
    "        // Primary tau2 = REML when k>=2, else DL (which equals 0 anyway when Q<=df).\n"
    "        const tau2 = (k >= 2) ? tau2_reml : tau2_dl;\n"
)
CONT_NEW = (
    "        // Primary tau2 = REML when k>=2, else DL (which equals 0 anyway when Q<=df).\n"
    "        const tau2 = (k >= 2) ? tau2_reml : tau2_dl;\n"
    "\n"
    "        // Q-profile tau2 CI (Cochrane v6.5 / RevMan-2025: tau2 CI by Q-profile).\n"
    "        const _qpYi = plotData.map(d => d.md);\n"
    "        const _qpVi = plotData.map(d => d.vi);\n"
    "        const { tau2_lo: tau2Lo, tau2_hi: tau2Hi } = qProfileTau2CI(_qpYi, _qpVi, df, 1 - confLevel);\n"
)

# Variant 2 (alias-style): same pattern but inside the alias variant
CONT_OLD_ALIAS = (
    "        // Primary tau2 = REML when k>=2, else DL.\n"
    "        const tau2 = (k >= 2) ? tau2_reml : tau2_dl;\n"
)
CONT_NEW_ALIAS = (
    "        // Primary tau2 = REML when k>=2, else DL.\n"
    "        const tau2 = (k >= 2) ? tau2_reml : tau2_dl;\n"
    "\n"
    "        // Q-profile tau2 CI (Cochrane v6.5 / RevMan-2025: tau2 CI by Q-profile).\n"
    "        const _qpYi = plotData.map(d => d.md);\n"
    "        const _qpVi = plotData.map(d => d.vi);\n"
    "        const { tau2_lo: tau2Lo, tau2_hi: tau2Hi } = qProfileTau2CI(_qpYi, _qpVi, df, 1 - confLevel);\n"
)

# Continuous return: add tau2Lo, tau2Hi
CONT_RETURN_OLD = "            hksjLCI, hksjUCI, piLCI, piUCI, tau2_reml,"
CONT_RETURN_NEW = "            hksjLCI, hksjUCI, piLCI, piUCI, tau2_reml, tau2Lo, tau2Hi,"

# ---- Binary engine integration ----
BIN_OLD = (
    "                // Primary tau2 = REML when k>=2 (Cochrane v6.5 default), else DL.\n"
    "                const tau2 = (k >= 2) ? tau2_reml : tau2_dl;\n"
)
BIN_NEW = (
    "                // Primary tau2 = REML when k>=2 (Cochrane v6.5 default), else DL.\n"
    "                const tau2 = (k >= 2) ? tau2_reml : tau2_dl;\n"
    "\n"
    "                // Q-profile tau2 CI (Cochrane v6.5 / RevMan-2025: tau2 CI by Q-profile).\n"
    "                const _qpYi = plotData.map(d => d.logOR);\n"
    "                const _qpVi = plotData.map(d => d.vi);\n"
    "                const { tau2_lo: tau2Lo, tau2_hi: tau2Hi } = qProfileTau2CI(_qpYi, _qpVi, df, 1 - confLevel);\n"
)

# Binary return: add tau2Lo, tau2Hi to existing return object
BIN_RETURN_OLD = "                return { plotData, Q, k, df, I2, tau2, tau2_reml, sWR, pLogOR, pSE, confLevel, zCrit, pOR, lci, uci, hksjLCI, hksjUCI, piLCI, piUCI, qPvalue, eggerResult, fragIdx, fragQuot, useHR, I2_lo, I2_hi };"
BIN_RETURN_NEW = "                return { plotData, Q, k, df, I2, tau2, tau2_dl, tau2_reml, tau2Lo, tau2Hi, sWR, pLogOR, pSE, confLevel, zCrit, pOR, lci, uci, hksjLCI, hksjUCI, piLCI, piUCI, qPvalue, eggerResult, fragIdx, fragQuot, useHR, I2_lo, I2_hi };"

FIXED_MARKER = "qProfileTau2CI"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--dry-run', action='store_true')
    args = ap.parse_args()
    print(f'Mode: {"DRY-RUN" if args.dry_run else "APPLY"}')
    files = sorted(
        f for f in os.listdir(ROOT)
        if f.endswith('_REVIEW.html') and not f.endswith('.bak.html')
    )
    summary = {'changed': 0, 'unchanged': 0, 'no_helpers_anchor': 0}
    for fname in files:
        path = os.path.join(ROOT, fname)
        src = open(path, 'r', encoding='utf-8').read()
        if FIXED_MARKER in src:
            summary['unchanged'] += 1
            continue
        if HELPERS_ANCHOR_OLD not in src:
            summary['no_helpers_anchor'] += 1
            continue
        out = src.replace(HELPERS_ANCHOR_OLD, HELPERS_ANCHOR_NEW, 1)
        if CONT_OLD in out:
            out = out.replace(CONT_OLD, CONT_NEW, 1)
        if CONT_OLD_ALIAS in out:
            out = out.replace(CONT_OLD_ALIAS, CONT_NEW_ALIAS, 1)
        if CONT_RETURN_OLD in out:
            out = out.replace(CONT_RETURN_OLD, CONT_RETURN_NEW, 1)
        if BIN_OLD in out:
            out = out.replace(BIN_OLD, BIN_NEW, 1)
        if BIN_RETURN_OLD in out:
            out = out.replace(BIN_RETURN_OLD, BIN_RETURN_NEW, 1)
        if not args.dry_run:
            open(path, 'w', encoding='utf-8').write(out)
        summary['changed'] += 1
    print(f'Summary: {summary}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
