"""
Add Cochrane Ch.13 (2024+) ROB-ME framework: per-MA reporting-bias assessment
that supersedes Egger-as-verdict.

Components added:
1. HTML: new `chip-robme` element next to `chip-egger`.
2. JS: `_assessROBME(c)` method inside RapidMeta (returns Q1-Q4 flags + overall).
3. JS: chip-population block right after the Egger chip update.

Five signaling questions per Cochrane Ch.13:
- Q1 Search comprehensiveness (manual)
- Q2 Trials missing from synthesis vs registered (manual)
- Q3 Selective non-reporting within studies (auto from CT.gov surveillance)
- Q4 Small-study effects (auto from Egger + trim-fill + k>=10)
- Overall (Q5) verdict: low / some / high / manual

Egger remains a single input among many; the verdict is a structured
judgement, not a p-value threshold.

Idempotent: skipped if `chip-robme` already in src.

Usage: python scripts/add_robme_framework.py [--dry-run]
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

# 1. HTML chip: add after chip-egger
HTML_OLD = (
    '                    <div class="stat-chip stat-chip-blue" id="chip-egger"><i class="fa-solid fa-chart-line" style="font-size:10px"></i> Egger\'s: --</div>\n'
)
HTML_NEW = (
    HTML_OLD
    + '\n'
    + '                    <div class="stat-chip stat-chip-blue" id="chip-robme" title="Cochrane Ch.13 ROB-ME: per-MA risk of missing evidence (Q1 search, Q2 missing trials, Q3 selective reporting, Q4 small-study effects)."><i class="fa-solid fa-eye-slash" style="font-size:10px"></i> ROB-ME: --</div>\n'
)

# 2. JS: insert _assessROBME method right before updateStatCards.
# Anchor: the line right above updateStatCards definition.
JS_METHOD_OLD = (
    "            updateStatCards(c) {\n"
)
JS_METHOD_NEW = (
    "            _assessROBME(c) {\n"
    "                if (!c) return null;\n"
    "                const k = c.k || 0;\n"
    "                const eggerP = (c.eggerResult && c.eggerResult.sufficient) ? c.eggerResult.pValue : null;\n"
    "                const k0 = (c.tfResult && c.tfResult.available) ? c.tfResult.k0 : 0;\n"
    "                const drift = (typeof c.primaryEndpointDrift === 'number') ? c.primaryEndpointDrift : null;\n"
    "                // Q1 Search comprehensiveness -- manual\n"
    "                const q1 = { level: 'manual', text: 'Manual: assess search comprehensiveness (databases, grey literature, registries, language coverage).' };\n"
    "                // Q2 Trials missing from synthesis vs registered -- manual\n"
    "                const q2 = { level: 'manual', text: 'Manual: identify registered trials without published or posted results.' };\n"
    "                // Q3 Selective non-reporting within studies -- from endpoint drift signal\n"
    "                let q3;\n"
    "                if (drift == null) {\n"
    "                    q3 = { level: 'manual', text: 'Manual: review individual trial outcome drift / selective reporting.' };\n"
    "                } else if (drift === 0) {\n"
    "                    q3 = { level: 'low', text: 'No analyzed trials pooled on a non-primary endpoint (CT.gov surveillance).' };\n"
    "                } else if (drift <= 1) {\n"
    "                    q3 = { level: 'some', text: drift + ' analyzed trial pooled on a non-primary endpoint.' };\n"
    "                } else {\n"
    "                    q3 = { level: 'high', text: drift + ' analyzed trials pooled on non-primary endpoints.' };\n"
    "                }\n"
    "                // Q4 Small-study effects -- Egger + trim-fill + k>=10 threshold\n"
    "                let q4;\n"
    "                if (k < 10) {\n"
    "                    q4 = { level: 'manual', text: 'k<10: Egger / trim-fill underpowered; visual funnel inspection insufficient on its own.' };\n"
    "                } else if (eggerP != null && eggerP < 0.05) {\n"
    "                    q4 = { level: 'high', text: 'Egger p=' + eggerP.toFixed(3) + ' (<0.05) suggests asymmetric funnel.' };\n"
    "                } else if (eggerP != null && eggerP < 0.10) {\n"
    "                    q4 = { level: 'some', text: 'Egger p=' + eggerP.toFixed(3) + ' (<0.10).' };\n"
    "                } else if (k0 >= 3) {\n"
    "                    q4 = { level: 'some', text: 'Trim-and-fill imputes ' + k0 + ' missing studies.' };\n"
    "                } else {\n"
    "                    q4 = { level: 'low', text: 'Egger p=' + (eggerP != null ? eggerP.toFixed(3) : '--') + ', trim-fill k0=' + k0 + '.' };\n"
    "                }\n"
    "                const flags = { q1, q2, q3, q4 };\n"
    "                const levels = Object.values(flags).map(f => f.level);\n"
    "                let overall;\n"
    "                if (levels.includes('high')) overall = { level: 'high', text: 'High risk of missing evidence' };\n"
    "                else if (levels.includes('some')) overall = { level: 'some', text: 'Some concerns' };\n"
    "                else if (levels.every(l => l === 'low')) overall = { level: 'low', text: 'Low risk of missing evidence' };\n"
    "                else overall = { level: 'manual', text: 'Pending manual judgements (Q1/Q2)' };\n"
    "                return { flags, overall };\n"
    "            },\n"
    "\n"
    "\n"
    "            updateStatCards(c) {\n"
)

# 3. JS: chip update block right after the Egger chip update closing brace.
# Anchor: the existing fragility-chip lookup.
JS_CHIP_OLD = (
    "                // Sensitivity concordance summary\n"
    "\n"
    "\n"
    "                const sensEl = document.getElementById('sensitivity-concordance');\n"
)
JS_CHIP_NEW = (
    "                // ROB-ME chip (Cochrane Ch.13 per-MA reporting-bias verdict)\n"
    "                const robmeChip = document.getElementById('chip-robme');\n"
    "                if (robmeChip) {\n"
    "                    const _r = this._assessROBME(c);\n"
    "                    if (_r) {\n"
    "                        const _cmap = { low: 'stat-chip-green', some: 'stat-chip-amber', high: 'stat-chip-red', manual: 'stat-chip-blue' };\n"
    "                        robmeChip.className = 'stat-chip ' + (_cmap[_r.overall.level] || 'stat-chip-blue');\n"
    "                        robmeChip.title = 'Q1 (search): ' + _r.flags.q1.text + '\\n'\n"
    "                                        + 'Q2 (missing trials): ' + _r.flags.q2.text + '\\n'\n"
    "                                        + 'Q3 (selective reporting): ' + _r.flags.q3.text + '\\n'\n"
    "                                        + 'Q4 (small-study effects): ' + _r.flags.q4.text;\n"
    "                        robmeChip.innerHTML = '<i class=\"fa-solid fa-eye-slash\" style=\"font-size:10px\"></i> ROB-ME: ' + _r.overall.text;\n"
    "                    }\n"
    "                }\n"
    "\n"
    "                // Sensitivity concordance summary\n"
    "\n"
    "\n"
    "                const sensEl = document.getElementById('sensitivity-concordance');\n"
)

FIXED_MARKER = "chip-robme"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--dry-run', action='store_true')
    args = ap.parse_args()
    print(f'Mode: {"DRY-RUN" if args.dry_run else "APPLY"}')
    files = sorted(
        f for f in os.listdir(ROOT)
        if f.endswith('_REVIEW.html') and not f.endswith('.bak.html')
    )
    summary = {'changed': 0, 'unchanged': 0, 'no_anchor': 0}
    for fname in files:
        path = os.path.join(ROOT, fname)
        src = open(path, 'r', encoding='utf-8').read()
        if FIXED_MARKER in src:
            summary['unchanged'] += 1
            continue
        if HTML_OLD not in src:
            summary['no_anchor'] += 1
            continue
        out = src.replace(HTML_OLD, HTML_NEW, 1)
        if JS_METHOD_OLD in out:
            out = out.replace(JS_METHOD_OLD, JS_METHOD_NEW, 1)
        if JS_CHIP_OLD in out:
            out = out.replace(JS_CHIP_OLD, JS_CHIP_NEW, 1)
        if not args.dry_run:
            open(path, 'w', encoding='utf-8').write(out)
        summary['changed'] += 1
    print(f'Summary: {summary}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
