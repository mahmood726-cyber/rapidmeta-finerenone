"""
Resolve the DTA engine's "T16-T17 R mada cross-validation" TODO: per-axis
HKSJ adjustment on the bivariate marginal SEs.

Hartung-Knapp-Sidik-Jonkman per-axis adaptation:
  q*_axis = (1/df) Σ wr_i * (y_i - mu_axis)^2     (df = k-1)
  adj_axis = max(1, q*_axis)
  se_HKSJ_axis = sqrt(adj_axis) * se_marginal_axis    (scales bivariate SE)
  HKSJ CI: mu ± qt(1-α/2, df) * se_HKSJ_axis on logit, back-transformed.

Note: this is a univariate-marginal HKSJ that scales the bivariate's
cross-axis-aware se_marginal — preserving the bivariate variance
structure rather than re-deriving from per-axis weights alone.

Engine changes (rapidmeta-dta-engine-v1.js):
- Add hksjScaleAxis(yi, vi, tau2, mu, df) helper.
- After Q-profile block, compute per-axis HKSJ adjustment + CIs.
- Return pooled_sens_hksj_ci_lb/ub, pooled_spec_hksj_ci_lb/ub,
  hksj_sens_adj, hksj_spec_adj.

Idempotent: skipped if 'hksjScaleAxis' already in src.

Usage: python scripts/add_dta_hksj.py [--dry-run]
"""
import argparse
import io
import os
import sys

if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

ENGINE_PATH = os.path.join(
    os.environ.get('RAPIDMETA_REPO_ROOT', os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    'rapidmeta-dta-engine-v1.js',
)

# 1. Insert hksjScaleAxis helper right after qProfileTau2CI (before PI block).
HELPER_OLD = (
    "  // ---------- Prediction Interval (Higgins 2009 / Riley 2011, t_{k-2} on logit scale) ----------\n"
)
HELPER_NEW = (
    "  // ---------- HKSJ per-axis adjustment (Hartung-Knapp 2001 marginal adaptation) ----------\n"
    "  // Scales the bivariate's cross-axis-aware marginal SE by sqrt(max(1, q*))\n"
    "  // where q* = (1/df) Σ wr_i (y_i - mu_axis)^2. df = k-1.\n"
    "  function hksjScaleAxis(yi, vi, tau2, muAxis, df) {\n"
    "    if (df < 1 || yi.length < 2) return { adj: NaN, qstar: NaN };\n"
    "    var t2 = (typeof tau2 === 'number' && isFinite(tau2)) ? tau2 : 0;\n"
    "    var sumW = 0, qStar = 0;\n"
    "    for (var i = 0; i < yi.length; i++) {\n"
    "      var wr = 1 / (vi[i] + t2);\n"
    "      sumW += wr;\n"
    "      qStar += wr * Math.pow(yi[i] - muAxis, 2);\n"
    "    }\n"
    "    qStar /= df;\n"
    "    return { adj: Math.max(1, qStar), qstar: qStar };\n"
    "  }\n"
    "\n"
    "  // ---------- Prediction Interval (Higgins 2009 / Riley 2011, t_{k-2} on logit scale) ----------\n"
)

# 2. After Q-profile block (the if-block ending with `}`), insert HKSJ block.
# Anchor: the closing brace of the Q-profile if-block, then the line that
# starts the backCI inner-function declaration.
QP_OLD = (
    "      tau2SensCI = qProfileTau2CI(ySens, vSens, k_raw - 1, 0.05);\n"
    "      tau2SpecCI = qProfileTau2CI(ySpec, vSpec, k_raw - 1, 0.05);\n"
    "    }\n"
    "\n"
    "    function backCI(mu, se){\n"
)
QP_NEW = (
    "      tau2SensCI = qProfileTau2CI(ySens, vSens, k_raw - 1, 0.05);\n"
    "      tau2SpecCI = qProfileTau2CI(ySpec, vSpec, k_raw - 1, 0.05);\n"
    "    }\n"
    "\n"
    "    // HKSJ per-axis adjustment (Cochrane v6.5 default for small k; resolves\n"
    "    // the prior \"T16-T17\" TODO for HKSJ on bivariate marginal SEs).\n"
    "    var hksjSensAdj = NaN, hksjSpecAdj = NaN;\n"
    "    var hksjSensCI = [NaN, NaN], hksjSpecCI = [NaN, NaN];\n"
    "    if (k_raw >= 2 && fitObj.estimator !== 'single_study_clopper_pearson' && isFinite(fitObj.se_sens_logit) && isFinite(fitObj.se_spec_logit)) {\n"
    "      var ySensH = [], vSensH = [], ySpecH = [], vSpecH = [];\n"
    "      for (var hi = 0; hi < working.length; hi++) {\n"
    "        var ht = working[hi], hpos = ht.TP + ht.FN, hneg = ht.TN + ht.FP;\n"
    "        var hs = ht.TP / hpos, hsp = ht.TN / hneg;\n"
    "        ySensH.push(Math.log(hs / (1 - hs))); vSensH.push(1/ht.TP + 1/ht.FN);\n"
    "        ySpecH.push(Math.log(hsp / (1 - hsp))); vSpecH.push(1/ht.TN + 1/ht.FP);\n"
    "      }\n"
    "      var hsens = hksjScaleAxis(ySensH, vSensH, fitObj.tau2_sens || 0, fitObj.mu_sens_logit, k_raw - 1);\n"
    "      var hspec = hksjScaleAxis(ySpecH, vSpecH, fitObj.tau2_spec || 0, fitObj.mu_spec_logit, k_raw - 1);\n"
    "      hksjSensAdj = hsens.adj;\n"
    "      hksjSpecAdj = hspec.adj;\n"
    "      var t975h = tinv(0.975, k_raw - 1);\n"
    "      if (isFinite(t975h) && isFinite(hksjSensAdj)) {\n"
    "        var seSensH = Math.sqrt(hksjSensAdj) * fitObj.se_sens_logit;\n"
    "        hksjSensCI = [\n"
    "          1 / (1 + Math.exp(-(fitObj.mu_sens_logit - t975h * seSensH))),\n"
    "          1 / (1 + Math.exp(-(fitObj.mu_sens_logit + t975h * seSensH)))\n"
    "        ];\n"
    "      }\n"
    "      if (isFinite(t975h) && isFinite(hksjSpecAdj)) {\n"
    "        var seSpecH = Math.sqrt(hksjSpecAdj) * fitObj.se_spec_logit;\n"
    "        hksjSpecCI = [\n"
    "          1 / (1 + Math.exp(-(fitObj.mu_spec_logit - t975h * seSpecH))),\n"
    "          1 / (1 + Math.exp(-(fitObj.mu_spec_logit + t975h * seSpecH)))\n"
    "        ];\n"
    "      }\n"
    "    }\n"
    "\n"
    "    function backCI(mu, se){\n"
)

# 3. Update return object to expose HKSJ fields.
RET_OLD = (
    "      tau2_sens_lo: tau2SensCI.tau2_lo, tau2_sens_hi: tau2SensCI.tau2_hi,\n"
    "      tau2_spec_lo: tau2SpecCI.tau2_lo, tau2_spec_hi: tau2SpecCI.tau2_hi,\n"
)
RET_NEW = (
    "      tau2_sens_lo: tau2SensCI.tau2_lo, tau2_sens_hi: tau2SensCI.tau2_hi,\n"
    "      tau2_spec_lo: tau2SpecCI.tau2_lo, tau2_spec_hi: tau2SpecCI.tau2_hi,\n"
    "      hksj_sens_adj: hksjSensAdj, hksj_spec_adj: hksjSpecAdj,\n"
    "      pooled_sens_hksj_ci_lb: hksjSensCI[0], pooled_sens_hksj_ci_ub: hksjSensCI[1],\n"
    "      pooled_spec_hksj_ci_lb: hksjSpecCI[0], pooled_spec_hksj_ci_ub: hksjSpecCI[1],\n"
)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--dry-run', action='store_true')
    args = ap.parse_args()
    print(f'Mode: {"DRY-RUN" if args.dry_run else "APPLY"}')
    src = open(ENGINE_PATH, 'r', encoding='utf-8').read()
    if 'hksjScaleAxis' in src:
        print('Already patched.')
        return 0
    for name, anchor in [('HELPER_OLD', HELPER_OLD), ('QP_OLD', QP_OLD), ('RET_OLD', RET_OLD)]:
        if anchor not in src:
            print(f'FAIL: {name} anchor not found.')
            return 2
    out = src.replace(HELPER_OLD, HELPER_NEW, 1) \
             .replace(QP_OLD, QP_NEW, 1) \
             .replace(RET_OLD, RET_NEW, 1)
    if not args.dry_run:
        open(ENGINE_PATH, 'w', encoding='utf-8').write(out)
        print('Patched rapidmeta-dta-engine-v1.js')
    else:
        print('[dry-run] would patch')
    return 0


if __name__ == '__main__':
    sys.exit(main())
