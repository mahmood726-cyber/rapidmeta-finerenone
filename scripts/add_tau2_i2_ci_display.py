"""
Add a τ² (95% CI) stat card and update the I² card to use Q-profile CI.

HTML changes:
1. Change `<div class="grid grid-cols-3 gap-8">` (the row containing HKSJ /
   PI / Q-test) to `grid-cols-4` and append a new τ² card with id
   `res-tau2-ci` and tooltip referencing Q-profile / Viechtbauer 2007.

JS changes (inside updateStatCards):
2. Add population for `res-tau2-ci` (formatted as `tau2 (lo - hi)`).
3. Update I² card to prefer Q-profile CI (`I2_lo_qp` / `I2_hi_qp`) over
   the test-based Higgins-Thompson (`I2_lo` / `I2_hi`) when available.

Idempotent: skipped if `res-tau2-ci` already in src.

Usage: python scripts/add_tau2_i2_ci_display.py [--dry-run]
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

# 1. HTML: insert new τ² card after the Q-test card; widen the grid
HTML_OLD = (
    '                <div class="grid grid-cols-3 gap-8">\n'
    '\n'
    '\n'
    '                    <div class="glass p-6 rounded-[30px] border border-slate-800 text-center" title="Hartung-Knapp-Sidik-Jonkman adjustment uses t-distribution with k-1 df, accounting for uncertainty in tau-squared estimation. More reliable than Wald for small k."><div class="text-[10px] opacity-50 uppercase font-bold mb-2 tracking-[0.2em]">HKSJ-Adjusted CI</div><div id="res-hksj" aria-label="HKSJ-adjusted confidence interval" class="text-lg font-bold font-mono tracking-tight text-cyan-400">--</div></div>\n'
    '\n'
    '\n'
    '                    <div class="glass p-6 rounded-[30px] border border-slate-800 text-center"><div class="text-[10px] opacity-50 uppercase font-bold mb-2 tracking-[0.2em]">Prediction Interval</div><div id="res-pi" aria-label="Prediction interval" class="text-lg font-bold font-mono tracking-tight text-purple-400">--</div></div>\n'
    '\n'
    '\n'
    '                    <div class="glass p-6 rounded-[30px] border border-slate-800 text-center"><div class="text-[10px] opacity-50 uppercase font-bold mb-2 tracking-[0.2em]">Q-test (Cochran)</div><div id="res-qtest" aria-label="Cochran Q test for heterogeneity" class="text-lg font-bold font-mono tracking-tight text-amber-400">--</div></div>\n'
)

HTML_NEW = (
    '                <div class="grid grid-cols-4 gap-8">\n'
    '\n'
    '\n'
    '                    <div class="glass p-6 rounded-[30px] border border-slate-800 text-center" title="Hartung-Knapp-Sidik-Jonkman adjustment uses t-distribution with k-1 df, accounting for uncertainty in tau-squared estimation. More reliable than Wald for small k."><div class="text-[10px] opacity-50 uppercase font-bold mb-2 tracking-[0.2em]">HKSJ-Adjusted CI</div><div id="res-hksj" aria-label="HKSJ-adjusted confidence interval" class="text-lg font-bold font-mono tracking-tight text-cyan-400">--</div></div>\n'
    '\n'
    '\n'
    '                    <div class="glass p-6 rounded-[30px] border border-slate-800 text-center"><div class="text-[10px] opacity-50 uppercase font-bold mb-2 tracking-[0.2em]">Prediction Interval</div><div id="res-pi" aria-label="Prediction interval" class="text-lg font-bold font-mono tracking-tight text-purple-400">--</div></div>\n'
    '\n'
    '\n'
    '                    <div class="glass p-6 rounded-[30px] border border-slate-800 text-center"><div class="text-[10px] opacity-50 uppercase font-bold mb-2 tracking-[0.2em]">Q-test (Cochran)</div><div id="res-qtest" aria-label="Cochran Q test for heterogeneity" class="text-lg font-bold font-mono tracking-tight text-amber-400">--</div></div>\n'
    '\n'
    '\n'
    '                    <div class="glass p-6 rounded-[30px] border border-slate-800 text-center" title="Tau-squared (between-study variance) with Q-profile 95% CI (Viechtbauer 2007); Cochrane v6.5 / RevMan-2025 default."><div class="text-[10px] opacity-50 uppercase font-bold mb-2 tracking-[0.2em]">τ² (95% CI)</div><div id="res-tau2-ci" aria-label="Tau-squared with Q-profile CI" class="text-lg font-bold font-mono tracking-tight text-emerald-400">--</div></div>\n'
)

# 2. JS: extend updateStatCards to populate res-tau2-ci and prefer Q-profile I² CI.
# Anchor: the "if no result, set placeholders" block inside updateStatCards.
JS_OLD_PLACEHOLDER = (
    "                    document.getElementById('res-qtest').innerText = '--';\n"
)
JS_NEW_PLACEHOLDER = (
    "                    document.getElementById('res-qtest').innerText = '--';\n"
    "\n"
    "\n"
    "                    const _tau2El = document.getElementById('res-tau2-ci');\n"
    "                    if (_tau2El) _tau2El.innerText = '--';\n"
)

# Update the I² display to prefer Q-profile CI; add τ² (CI) population.
# Anchor: the existing res-i2 line (will become a small block).
JS_OLD_I2 = (
    "                document.getElementById('res-i2').innerText = c.I2_hi > 0 && c.k >= 2\n"
    "\n"
    "\n"
    "                    ? `${c.I2.toFixed(0)}% (${c.I2_lo.toFixed(0)}-${c.I2_hi.toFixed(0)}%)`\n"
    "\n"
    "\n"
    "                    : `${c.I2.toFixed(1)}%`;\n"
)

JS_NEW_I2 = (
    "                // Prefer Q-profile-derived I² CI when available (Cochrane v6.5).\n"
    "                const _i2lo = (typeof c.I2_lo_qp === 'number' && Number.isFinite(c.I2_lo_qp)) ? c.I2_lo_qp : c.I2_lo;\n"
    "                const _i2hi = (typeof c.I2_hi_qp === 'number' && Number.isFinite(c.I2_hi_qp)) ? c.I2_hi_qp : c.I2_hi;\n"
    "                document.getElementById('res-i2').innerText = (Number.isFinite(_i2hi) && _i2hi > 0 && c.k >= 2)\n"
    "                    ? `${c.I2.toFixed(0)}% (${_i2lo.toFixed(0)}-${_i2hi.toFixed(0)}%)`\n"
    "                    : `${c.I2.toFixed(1)}%`;\n"
    "\n"
    "                // τ² with Q-profile CI (added by Cochrane v6.5 alignment commit).\n"
    "                const _tau2El = document.getElementById('res-tau2-ci');\n"
    "                if (_tau2El) {\n"
    "                    const _tau2 = Number.isFinite(c.tau2) ? c.tau2 : 0;\n"
    "                    if (c.k >= 2 && Number.isFinite(c.tau2Lo) && Number.isFinite(c.tau2Hi)) {\n"
    "                        _tau2El.innerText = `${_tau2.toFixed(3)} (${c.tau2Lo.toFixed(3)}-${c.tau2Hi.toFixed(3)})`;\n"
    "                    } else {\n"
    "                        _tau2El.innerText = `${_tau2.toFixed(3)}`;\n"
    "                    }\n"
    "                }\n"
)

FIXED_MARKER = "res-tau2-ci"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--dry-run', action='store_true')
    args = ap.parse_args()
    print(f'Mode: {"DRY-RUN" if args.dry_run else "APPLY"}')
    files = sorted(
        f for f in os.listdir(ROOT)
        if f.endswith('_REVIEW.html') and not f.endswith('.bak.html')
    )
    summary = {'changed': 0, 'unchanged': 0, 'no_html_anchor': 0, 'no_js_anchor': 0}
    for fname in files:
        path = os.path.join(ROOT, fname)
        src = open(path, 'r', encoding='utf-8').read()
        if FIXED_MARKER in src:
            summary['unchanged'] += 1
            continue
        if HTML_OLD not in src:
            summary['no_html_anchor'] += 1
            continue
        out = src.replace(HTML_OLD, HTML_NEW, 1)
        if JS_OLD_PLACEHOLDER in out:
            out = out.replace(JS_OLD_PLACEHOLDER, JS_NEW_PLACEHOLDER, 1)
        if JS_OLD_I2 in out:
            out = out.replace(JS_OLD_I2, JS_NEW_I2, 1)
        else:
            summary['no_js_anchor'] += 1
        if not args.dry_run:
            open(path, 'w', encoding='utf-8').write(out)
        summary['changed'] += 1
    print(f'Summary: {summary}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
