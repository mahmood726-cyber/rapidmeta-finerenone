"""
Wire DTA HKSJ CI into the dashboard display.

Changes to each *_DTA_REVIEW.html:
1. renderSummary() — show HKSJ CI on pooled-sens-ci / pooled-spec-ci when
   available; suffix with "(HKSJ)" or "(Wald)" tag for clarity.
2. Coverage-warning banner — replace "HKSJ-style adjustments are not
   applied" with the new "HKSJ adjustment applied" wording.

Idempotent: skipped if 'hksj_sens_adj' is referenced in the dashboard's
HTML/JS (i.e., the wiring has been done).

Usage: python scripts/add_dta_hksj_display.py [--dry-run]
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

# 1. renderSummary update (Sens)
SUMMARY_OLD_SENS = (
    "        document.getElementById('pooled-sens').textContent = fmt(fit.pooled_sens);\n"
    "        document.getElementById('pooled-sens-ci').textContent = fmtCI(fit.pooled_sens_ci_lb, fit.pooled_sens_ci_ub);\n"
    "        document.getElementById('pooled-spec').textContent = fmt(fit.pooled_spec);\n"
    "        document.getElementById('pooled-spec-ci').textContent = fmtCI(fit.pooled_spec_ci_lb, fit.pooled_spec_ci_ub);\n"
)
SUMMARY_NEW_SENS = (
    "        document.getElementById('pooled-sens').textContent = fmt(fit.pooled_sens);\n"
    "        // Cochrane v6.5: prefer HKSJ CI when available (k>=2 + REML/FE bivariate path)\n"
    "        var _useHKSJSens = isFinite(fit.pooled_sens_hksj_ci_lb) && isFinite(fit.pooled_sens_hksj_ci_ub);\n"
    "        document.getElementById('pooled-sens-ci').textContent = _useHKSJSens\n"
    "          ? fmtCI(fit.pooled_sens_hksj_ci_lb, fit.pooled_sens_hksj_ci_ub) + ' (HKSJ)'\n"
    "          : fmtCI(fit.pooled_sens_ci_lb, fit.pooled_sens_ci_ub) + ' (Wald)';\n"
    "        document.getElementById('pooled-spec').textContent = fmt(fit.pooled_spec);\n"
    "        var _useHKSJSpec = isFinite(fit.pooled_spec_hksj_ci_lb) && isFinite(fit.pooled_spec_hksj_ci_ub);\n"
    "        document.getElementById('pooled-spec-ci').textContent = _useHKSJSpec\n"
    "          ? fmtCI(fit.pooled_spec_hksj_ci_lb, fit.pooled_spec_hksj_ci_ub) + ' (HKSJ)'\n"
    "          : fmtCI(fit.pooled_spec_ci_lb, fit.pooled_spec_ci_ub) + ' (Wald)';\n"
)

# 2. Coverage banner update
BANNER_OLD = (
    "          notes += '<div class=\"banner banner-amber\"><strong>Coverage warning (k&lt;10):</strong> ' +\n"
    "            'With only ' + fit.k + ' studies, Wald-based 95% CIs may under-cover the nominal rate. ' +\n"
    "            'HKSJ-style adjustments are not applied to the bivariate marginal SEs in this v1 release; ' +\n"
    "            'planned upgrade T16-T17 (R mada cross-validation).</div>';\n"
)
BANNER_NEW = (
    "          var _hkInfo = (isFinite(fit.hksj_sens_adj) && isFinite(fit.hksj_spec_adj))\n"
    "            ? ' HKSJ adjustment applied (q*_sens=' + fit.hksj_sens_adj.toFixed(2) +\n"
    "              ', q*_spec=' + fit.hksj_spec_adj.toFixed(2) + '; floored at 1 per Cochrane v6.5).'\n"
    "            : ' HKSJ unavailable for this fit (single study).';\n"
    "          notes += '<div class=\"banner banner-amber\"><strong>Coverage warning (k&lt;10):</strong> ' +\n"
    "            'With only ' + fit.k + ' studies, Wald-based 95% CIs may under-cover the nominal rate.' +\n"
    "            _hkInfo + '</div>';\n"
)

FIXED_MARKER = "_useHKSJSens"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--dry-run', action='store_true')
    args = ap.parse_args()
    print(f'Mode: {"DRY-RUN" if args.dry_run else "APPLY"}')
    files = sorted(
        f for f in os.listdir(ROOT)
        if f.endswith('_DTA_REVIEW.html') and not f.endswith('.bak.html')
    )
    summary = {'changed': 0, 'unchanged': 0, 'no_anchor': 0}
    for fname in files:
        path = os.path.join(ROOT, fname)
        src = open(path, 'r', encoding='utf-8').read()
        if FIXED_MARKER in src:
            summary['unchanged'] += 1
            continue
        if SUMMARY_OLD_SENS not in src or BANNER_OLD not in src:
            summary['no_anchor'] += 1
            continue
        out = src.replace(SUMMARY_OLD_SENS, SUMMARY_NEW_SENS, 1).replace(BANNER_OLD, BANNER_NEW, 1)
        if not args.dry_run:
            open(path, 'w', encoding='utf-8').write(out)
        summary['changed'] += 1
    print(f'Summary: {summary}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
