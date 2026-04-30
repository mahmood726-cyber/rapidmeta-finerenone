"""
Fix: DTA ROB-ME chip stays at '--' when Deeks is skipped (k<5).

The original add_dta_robme_chip.py placed the chip-update block AFTER the
'No funnel asymmetry detected' message, which is unreachable when
res.skipped is true (the function early-returns at the top).

This patch refactors the chip update into a separate helper called
right after the deeksAnalysis() result is computed, BEFORE any
early-return. The helper handles both skipped (k<5) and computed cases.

Idempotent: skipped if 'function _updateROBMEDTA' already in src.

Usage: python scripts/fix_dta_robme_chip_runs_when_skipped.py [--dry-run]
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

# Step 1: Remove the existing chip-update block that's after the "No funnel
# asymmetry detected" line and unreachable in the skipped branch.
REMOVE_OLD = (
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
REMOVE_NEW = (
    "          'No funnel asymmetry detected (p &ge; 0.10).');\n"
    "      }\n"
)

# Step 2: Insert the chip update inside renderDeeks, right after `var res =
# deeksAnalysis(rows);` and before the existing element-fetches. Anchor on
# the exact line that follows res= so we land at the correct spot.
INSERT_OLD = (
    "      function renderDeeks() {\n"
    "        var rows = trialsForTier(currentTier);\n"
    "        var res = deeksAnalysis(rows);\n"
    "        _lastDeeks = res;\n"
)
INSERT_NEW = (
    "      // ROB-ME chip update (Cochrane Ch.13 2024+) -- runs even when Deeks skipped\n"
    "      function _updateROBMEDTA(res) {\n"
    "        var robmeChip = document.getElementById('chip-robme-dta');\n"
    "        if (!robmeChip) return;\n"
    "        var rho = (currentFit && typeof currentFit.threshold_effect_spearman === 'number') ? currentFit.threshold_effect_spearman : null;\n"
    "        var q3level = (rho == null) ? 'manual' : (Math.abs(rho) > 0.8 ? 'high' : (Math.abs(rho) > 0.6 ? 'some' : 'low'));\n"
    "        var deeksP = (res && !res.skipped && isFinite(res.p)) ? res.p : null;\n"
    "        var q4level = (deeksP == null) ? 'manual' : (deeksP < 0.05 ? 'high' : (deeksP < 0.10 ? 'some' : 'low'));\n"
    "        var levels = ['manual', 'manual', q3level, q4level];\n"
    "        var overall = levels.indexOf('high') >= 0 ? 'high' : (levels.indexOf('some') >= 0 ? 'some' : (levels.every(function(l){return l === 'low';}) ? 'low' : 'manual'));\n"
    "        var palette = { low: '#10b981', some: '#f59e0b', high: '#ef4444', manual: '#6b7280' };\n"
    "        var verdict = { low: 'Low risk of missing evidence', some: 'Some concerns', high: 'High risk of missing evidence', manual: 'Pending manual judgements (Q1/Q2)' };\n"
    "        robmeChip.style.background = palette[overall] + '20';\n"
    "        robmeChip.style.color = palette[overall];\n"
    "        robmeChip.style.border = '1px solid ' + palette[overall];\n"
    "        var q4Note = (deeksP == null && (res && res.skipped))\n"
    "          ? ' (k<5: Deeks underpowered)'\n"
    "          : '';\n"
    "        robmeChip.title = 'Q1 (search): manual judgement required\\n'\n"
    "                        + 'Q2 (missing trials): manual judgement required\\n'\n"
    "                        + 'Q3 (selective reporting / threshold): Spearman rho = ' + (rho == null ? '--' : rho.toFixed(2)) + ' (' + q3level + ')\\n'\n"
    "                        + 'Q4 (small-study effects via Deeks): p = ' + (deeksP == null ? '--' : deeksP.toFixed(3)) + q4Note + ' (' + q4level + ')';\n"
    "        robmeChip.textContent = 'ROB-ME: ' + verdict[overall];\n"
    "      }\n"
    "\n"
    "      function renderDeeks() {\n"
    "        var rows = trialsForTier(currentTier);\n"
    "        var res = deeksAnalysis(rows);\n"
    "        _lastDeeks = res;\n"
    "        _updateROBMEDTA(res);\n"
)

FIXED_MARKER = "function _updateROBMEDTA"


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
        if REMOVE_OLD not in src or INSERT_OLD not in src:
            summary['no_anchor'] += 1
            continue
        out = src.replace(REMOVE_OLD, REMOVE_NEW, 1).replace(INSERT_OLD, INSERT_NEW, 1)
        if not args.dry_run:
            open(path, 'w', encoding='utf-8').write(out)
        summary['changed'] += 1
    print(f'Summary: {summary}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
