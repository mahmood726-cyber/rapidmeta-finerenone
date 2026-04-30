"""
Port the Cochrane Ch.13 ROB-ME chip to the 6 DTA dashboards.

DTA-specific Q-mapping:
  Q1 search comprehensiveness  -> manual
  Q2 missing trials            -> manual
  Q3 selective reporting       -> threshold-effect Spearman rho (a strong
                                  rho indicates selective cutoff reporting)
  Q4 small-study effects       -> Deeks' funnel p-value (k>=5 required)
  Overall                      -> low / some / high / manual

Chip element added next to the Deeks summary line; populated at the tail
of renderDeeks() where both `currentFit` (for threshold spearman) and the
local `res` (Deeks output) are in scope.

Idempotent: skipped if `chip-robme-dta` already in src.

Usage: python scripts/add_dta_robme_chip.py [--dry-run]
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

# 1. HTML: insert chip right after the deeks-summary-line div.
HTML_OLD = '        <div id="deeks-summary-line" class="deeks-summary"></div>\n'
HTML_NEW = (
    HTML_OLD
    + '        <div id="chip-robme-dta" class="deeks-summary" style="margin-top:0.5rem;display:inline-block;padding:0.4rem 0.8rem;border-radius:9999px;font-size:0.85rem;font-weight:600;background:#e5e7eb;color:#374151;border:1px solid #d1d5db;" title="Cochrane Ch.13 ROB-ME: per-MA risk of missing evidence (Q1 search, Q2 missing trials, Q3 selective reporting via threshold-effect Spearman rho, Q4 small-study effects via Deeks\' funnel).">ROB-ME: --</div>\n'
)

# 2. JS: insert ROB-ME assessment block right before the closing brace of
# renderDeeks(). Anchor: the existing "No funnel asymmetry detected" message
# concatenation, which is the last statement before the closing brace.
JS_OLD = (
    "          'No funnel asymmetry detected (p &ge; 0.10).');\n"
    "      }\n"
)
JS_NEW = (
    "          'No funnel asymmetry detected (p &ge; 0.10).');\n"
    "\n"
    "        // ROB-ME chip (Cochrane Ch.13 2024+) -- DTA-specific Q-mapping\n"
    "        var robmeChip = document.getElementById('chip-robme-dta');\n"
    "        if (robmeChip) {\n"
    "          var rho = (currentFit && typeof currentFit.threshold_effect_spearman === 'number') ? currentFit.threshold_effect_spearman : null;\n"
    "          var q3level = (rho == null) ? 'manual' : (Math.abs(rho) > 0.8 ? 'high' : (Math.abs(rho) > 0.6 ? 'some' : 'low'));\n"
    "          var deeksP = res.skipped ? null : res.p;\n"
    "          var q4level = (!isFinite(deeksP) || deeksP == null) ? 'manual' : (deeksP < 0.05 ? 'high' : (deeksP < 0.10 ? 'some' : 'low'));\n"
    "          var levels = ['manual', 'manual', q3level, q4level];\n"
    "          var overall = levels.indexOf('high') >= 0 ? 'high' : (levels.indexOf('some') >= 0 ? 'some' : (levels.every(function(l){return l === 'low';}) ? 'low' : 'manual'));\n"
    "          var palette = { low: '#10b981', some: '#f59e0b', high: '#ef4444', manual: '#6b7280' };\n"
    "          var verdict = { low: 'Low risk of missing evidence', some: 'Some concerns', high: 'High risk of missing evidence', manual: 'Pending manual judgements (Q1/Q2)' };\n"
    "          robmeChip.style.background = palette[overall] + '20';\n"
    "          robmeChip.style.color = palette[overall];\n"
    "          robmeChip.style.border = '1px solid ' + palette[overall];\n"
    "          robmeChip.title = 'Q1 (search): manual judgement required\\n'\n"
    "                          + 'Q2 (missing trials): manual judgement required\\n'\n"
    "                          + 'Q3 (selective reporting / threshold): Spearman rho = ' + (rho == null ? '--' : rho.toFixed(2)) + ' (' + q3level + ')\\n'\n"
    "                          + 'Q4 (small-study effects via Deeks): p = ' + (deeksP == null || !isFinite(deeksP) ? '--' : deeksP.toFixed(3)) + ' (' + q4level + ')';\n"
    "          robmeChip.textContent = 'ROB-ME: ' + verdict[overall];\n"
    "        }\n"
    "      }\n"
)

FIXED_MARKER = "chip-robme-dta"


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
        if HTML_OLD not in src or JS_OLD not in src:
            summary['no_anchor'] += 1
            continue
        out = src.replace(HTML_OLD, HTML_NEW, 1).replace(JS_OLD, JS_NEW, 1)
        if not args.dry_run:
            open(path, 'w', encoding='utf-8').write(out)
        summary['changed'] += 1
    print(f'Summary: {summary}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
