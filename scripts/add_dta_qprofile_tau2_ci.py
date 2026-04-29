"""
Port Cochrane v6.5 Q-profile tau2 CI to the DTA bivariate engine.

The DTA engine fits Reitsma REML and returns tau2_sens / tau2_spec point
estimates but no CIs. Per Cochrane v6.5 / RevMan-2025: tau2 CI by Q-profile
(Viechtbauer 2007). For DTA bivariate, we apply per-axis univariate
Q-profile (marginal approximation) on the per-study logit-Sens / logit-Spec
data, since the proper bivariate Q-profile is a much larger lift.

Changes to rapidmeta-dta-engine-v1.js:
1. Add qchisq + qProfileTau2CI helpers near tinv.
2. In fit(), after fitObj, compute per-axis tau2 CI from per-study (y_i, v_i).
3. Return tau2_sens_lo, tau2_sens_hi, tau2_spec_lo, tau2_spec_hi.

Idempotent: skipped if 'qProfileTau2CI' already in src.

Usage: python scripts/add_dta_qprofile_tau2_ci.py [--dry-run]
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

ENGINE_PATH = os.path.join(ROOT, 'rapidmeta-dta-engine-v1.js')

# 1. Insert helpers AFTER the tinv function declaration block.
HELPERS_OLD = (
    "  // ---------- Prediction Interval (Higgins 2009 / Riley 2011, t_{k-2} on logit scale) ----------\n"
)
HELPERS_NEW = (
    "  // ---------- Chi-square quantile (Cochrane v6.5 / Q-profile support) ----------\n"
    "  function qchisq(p, df) {\n"
    "    if (df <= 0 || p <= 0) return 0;\n"
    "    if (p >= 1) return Infinity;\n"
    "    if (df === 1) {\n"
    "      // Inverse normal at (1+p)/2, squared\n"
    "      var z = _qnormApprox((1 + p) / 2);\n"
    "      return z * z;\n"
    "    }\n"
    "    if (df === 2) return -2 * Math.log(1 - p);\n"
    "    // Wilson-Hilferty for df>=3\n"
    "    var z2 = _qnormApprox(p);\n"
    "    var v = 1 - 2/(9*df) + z2 * Math.sqrt(2/(9*df));\n"
    "    return Math.max(0, df * v * v * v);\n"
    "  }\n"
    "  // Beasley-Springer-Moro inverse normal (good to ~7 digits in [1e-9, 1-1e-9])\n"
    "  function _qnormApprox(p) {\n"
    "    if (p <= 0) return -Infinity;\n"
    "    if (p >= 1) return Infinity;\n"
    "    var a = [-3.969683028665376e+01, 2.209460984245205e+02, -2.759285104469687e+02,\n"
    "             1.383577518672690e+02, -3.066479806614716e+01, 2.506628277459239e+00];\n"
    "    var b = [-5.447609879822406e+01, 1.615858368580409e+02, -1.556989798598866e+02,\n"
    "             6.680131188771972e+01, -1.328068155288572e+01];\n"
    "    var c = [-7.784894002430293e-03, -3.223964580411365e-01, -2.400758277161838e+00,\n"
    "             -2.549732539343734e+00, 4.374664141464968e+00, 2.938163982698783e+00];\n"
    "    var d = [7.784695709041462e-03, 3.224671290700398e-01, 2.445134137142996e+00,\n"
    "             3.754408661907416e+00];\n"
    "    var pl = 0.02425, ph = 1 - pl, q, r;\n"
    "    if (p < pl) { q = Math.sqrt(-2 * Math.log(p));\n"
    "      return (((((c[0]*q+c[1])*q+c[2])*q+c[3])*q+c[4])*q+c[5]) / ((((d[0]*q+d[1])*q+d[2])*q+d[3])*q+1); }\n"
    "    if (p <= ph) { q = p - 0.5; r = q*q;\n"
    "      return (((((a[0]*r+a[1])*r+a[2])*r+a[3])*r+a[4])*r+a[5])*q / (((((b[0]*r+b[1])*r+b[2])*r+b[3])*r+b[4])*r+1); }\n"
    "    q = Math.sqrt(-2 * Math.log(1-p));\n"
    "    return -(((((c[0]*q+c[1])*q+c[2])*q+c[3])*q+c[4])*q+c[5]) / ((((d[0]*q+d[1])*q+d[2])*q+d[3])*q+1);\n"
    "  }\n"
    "\n"
    "  // ---------- Q-profile tau2 CI (univariate, Viechtbauer 2007) ----------\n"
    "  // Applied per-axis (sens, spec) as marginal approximation of the bivariate CI.\n"
    "  function qProfileTau2CI(yi, vi, df, alpha) {\n"
    "    if (df < 1 || yi.length < 2) return { tau2_lo: NaN, tau2_hi: NaN };\n"
    "    function qGen(tau2) {\n"
    "      var sW = 0, sWY = 0, sW_Y2 = 0;\n"
    "      for (var i = 0; i < yi.length; i++) {\n"
    "        var w = 1 / (vi[i] + tau2);\n"
    "        sW += w; sWY += w * yi[i]; sW_Y2 += w * yi[i] * yi[i];\n"
    "      }\n"
    "      if (sW === 0) return 0;\n"
    "      return Math.max(0, sW_Y2 - (sWY * sWY) / sW);\n"
    "    }\n"
    "    var cutHi = qchisq(1 - alpha/2, df);\n"
    "    var cutLo = qchisq(alpha/2, df);\n"
    "    var Q0 = qGen(0);\n"
    "    function bisect(target) {\n"
    "      if (Q0 <= target) return 0;\n"
    "      var lo = 0, hi = 100;\n"
    "      for (var _e = 0; _e < 30 && qGen(hi) > target && hi < 1e8; _e++) hi *= 2;\n"
    "      for (var _i = 0; _i < 60; _i++) {\n"
    "        var mid = (lo + hi) / 2;\n"
    "        if (qGen(mid) > target) lo = mid; else hi = mid;\n"
    "      }\n"
    "      return (lo + hi) / 2;\n"
    "    }\n"
    "    return { tau2_lo: bisect(cutHi), tau2_hi: bisect(cutLo) };\n"
    "  }\n"
    "\n"
    "  // ---------- Prediction Interval (Higgins 2009 / Riley 2011, t_{k-2} on logit scale) ----------\n"
)

# 2. Inside fit(), inject Q-profile per-axis after the fitObj branch but before backCI.
FIT_OLD = (
    "    var z = 1.959963984540054;\n"
    "    function backCI(mu, se){\n"
)
FIT_NEW = (
    "    var z = 1.959963984540054;\n"
    "\n"
    "    // Q-profile tau2 CI per-axis (Cochrane v6.5 / RevMan-2025; univariate marginal)\n"
    "    var tau2SensCI = { tau2_lo: NaN, tau2_hi: NaN };\n"
    "    var tau2SpecCI = { tau2_lo: NaN, tau2_hi: NaN };\n"
    "    if (k_raw >= 2 && fitObj.estimator !== 'single_study_clopper_pearson') {\n"
    "      var ySens = [], vSens = [], ySpec = [], vSpec = [];\n"
    "      for (var qi = 0; qi < working.length; qi++) {\n"
    "        var qt = working[qi], qpos = qt.TP + qt.FN, qneg = qt.TN + qt.FP;\n"
    "        var qs = qt.TP / qpos, qsp = qt.TN / qneg;\n"
    "        ySens.push(Math.log(qs / (1 - qs))); vSens.push(1/qt.TP + 1/qt.FN);\n"
    "        ySpec.push(Math.log(qsp / (1 - qsp))); vSpec.push(1/qt.TN + 1/qt.FP);\n"
    "      }\n"
    "      tau2SensCI = qProfileTau2CI(ySens, vSens, k_raw - 1, 0.05);\n"
    "      tau2SpecCI = qProfileTau2CI(ySpec, vSpec, k_raw - 1, 0.05);\n"
    "    }\n"
    "\n"
    "    function backCI(mu, se){\n"
)

# 3. Update return to include the new fields.
RET_OLD = (
    "      tau2_sens: fitObj.tau2_sens, tau2_spec: fitObj.tau2_spec, rho: fitObj.rho,\n"
)
RET_NEW = (
    "      tau2_sens: fitObj.tau2_sens, tau2_spec: fitObj.tau2_spec, rho: fitObj.rho,\n"
    "      tau2_sens_lo: tau2SensCI.tau2_lo, tau2_sens_hi: tau2SensCI.tau2_hi,\n"
    "      tau2_spec_lo: tau2SpecCI.tau2_lo, tau2_spec_hi: tau2SpecCI.tau2_hi,\n"
)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--dry-run', action='store_true')
    args = ap.parse_args()
    print(f'Mode: {"DRY-RUN" if args.dry_run else "APPLY"}')
    src = open(ENGINE_PATH, 'r', encoding='utf-8').read()
    if 'qProfileTau2CI' in src:
        print('Already patched.')
        return 0
    if HELPERS_OLD not in src:
        print('FAIL: HELPERS_OLD anchor not found.')
        return 2
    if FIT_OLD not in src:
        print('FAIL: FIT_OLD anchor not found.')
        return 2
    if RET_OLD not in src:
        print('FAIL: RET_OLD anchor not found.')
        return 2
    out = src.replace(HELPERS_OLD, HELPERS_NEW, 1) \
             .replace(FIT_OLD, FIT_NEW, 1) \
             .replace(RET_OLD, RET_NEW, 1)
    if not args.dry_run:
        open(ENGINE_PATH, 'w', encoding='utf-8').write(out)
        print('Patched rapidmeta-dta-engine-v1.js')
    else:
        print('[dry-run] would patch')
    return 0


if __name__ == '__main__':
    sys.exit(main())
