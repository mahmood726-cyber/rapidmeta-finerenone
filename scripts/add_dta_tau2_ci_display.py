"""
Wire DTA Q-profile tau2 CI into the heterogeneity panel display.

Updates the metric-ci sub-line on the tau2_sens / tau2_spec cards to show
the Q-profile 95% CI when available (k>=2 and not single_study).

Idempotent: skipped if 'Q-profile 95% CI' already in the file.

Usage: python scripts/add_dta_tau2_ci_display.py [--dry-run]
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

SENS_OLD = (
    "          '<div class=\"metric-card\"><div class=\"metric-label\">tau&sup2; (Sens, logit)</div>' +\n"
    "          '<div class=\"metric-value\">' + fmtNum(fit.tau2_sens, 4) + '</div>' +\n"
    "          '<div class=\"metric-ci\">between-study variance on logit scale</div></div>' +\n"
)
SENS_NEW = (
    "          '<div class=\"metric-card\"><div class=\"metric-label\">tau&sup2; (Sens, logit)</div>' +\n"
    "          '<div class=\"metric-value\">' + fmtNum(fit.tau2_sens, 4) + '</div>' +\n"
    "          '<div class=\"metric-ci\">' + (Number.isFinite(fit.tau2_sens_lo) && Number.isFinite(fit.tau2_sens_hi) ? 'Q-profile 95% CI: ' + fmtNum(fit.tau2_sens_lo, 4) + ' &mdash; ' + fmtNum(fit.tau2_sens_hi, 4) : 'between-study variance on logit scale') + '</div></div>' +\n"
)

SPEC_OLD = (
    "          '<div class=\"metric-card\"><div class=\"metric-label\">tau&sup2; (Spec, logit)</div>' +\n"
    "          '<div class=\"metric-value\">' + fmtNum(fit.tau2_spec, 4) + '</div>' +\n"
    "          '<div class=\"metric-ci\">between-study variance on logit scale</div></div>' +\n"
)
SPEC_NEW = (
    "          '<div class=\"metric-card\"><div class=\"metric-label\">tau&sup2; (Spec, logit)</div>' +\n"
    "          '<div class=\"metric-value\">' + fmtNum(fit.tau2_spec, 4) + '</div>' +\n"
    "          '<div class=\"metric-ci\">' + (Number.isFinite(fit.tau2_spec_lo) && Number.isFinite(fit.tau2_spec_hi) ? 'Q-profile 95% CI: ' + fmtNum(fit.tau2_spec_lo, 4) + ' &mdash; ' + fmtNum(fit.tau2_spec_hi, 4) : 'between-study variance on logit scale') + '</div></div>' +\n"
)

FIXED_MARKER = "Q-profile 95% CI"


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
        out = src
        if SENS_OLD in out:
            out = out.replace(SENS_OLD, SENS_NEW, 1)
        if SPEC_OLD in out:
            out = out.replace(SPEC_OLD, SPEC_NEW, 1)
        if out == src:
            summary['no_anchor'] += 1
            continue
        if not args.dry_run:
            open(path, 'w', encoding='utf-8').write(out)
        summary['changed'] += 1
    print(f'Summary: {summary}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
