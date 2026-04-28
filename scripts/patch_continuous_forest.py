"""
Bulk-apply the continuous-outcome forest-plot fix across rapidmeta-finerenone
pairwise reviews.

Same 7 edits that fixed FARICIMAB_NAMD_REVIEW.html (commit 16a80e9, 20caf98)
and AFLIBERCEPT_HD_REVIEW.html (commit 69f2f92). Idempotent: re-running on
already-fixed files is a no-op.

Usage:
    python scripts/patch_continuous_forest.py --dry-run    # report only
    python scripts/patch_continuous_forest.py              # apply
"""
import argparse, os, re, sys

ROOT = os.environ.get('RAPIDMETA_REPO_ROOT', os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# The 20 pairwise reviews flagged NEEDS_FIX by the audit.
TARGETS = [
    'ANTIAMYLOID_AD_REVIEW.html', 'ARNI_HF_REVIEW.html', 'BEMPEDOIC_ACID_REVIEW.html',
    'BIOLOGIC_ASTHMA_REVIEW.html', 'CFTR_CF_REVIEW.html', 'CGRP_MIGRAINE_REVIEW.html',
    'COPD_TRIPLE_REVIEW.html', 'DUPILUMAB_COPD_REVIEW.html', 'ESKETAMINE_TRD_REVIEW.html',
    'FEZOLINETANT_VMS_REVIEW.html', 'INCLISIRAN_REVIEW.html', 'INSULIN_ICODEC_REVIEW.html',
    'KARXT_SCZ_REVIEW.html', 'PATISIRAN_POLYNEUROPATHY_REVIEW.html',
    'PEGCETACOPLAN_GA_REVIEW.html', 'RENAL_DENERV_REVIEW.html', 'ROMOSOZUMAB_OP_REVIEW.html',
    'SEMAGLUTIDE_OBESITY_REVIEW.html', 'TIRZEPATIDE_OBESITY_REVIEW.html',
    'TIRZEPATIDE_T2D_REVIEW.html',
]


# ---------- Edit 1: ContinuousMDEngine plotData alias ----------
EDIT1_OLD = "        const pSE = Math.sqrt(1/sWR);\n\n\n        \n"
EDIT1_NEW = (
    "        const pSE = Math.sqrt(1/sWR);\n\n\n"
    "        // Alias md->logOR, name->id so existing OR/HR-shaped consumers (renderPlots\n"
    "        // forest/subgroup/cumulative) read MD values without rewriting their schema.\n"
    "        // Linear-scale renderers must check r.isContinuous and skip exp() back-transforms.\n"
    "        plotData.forEach(d => { d.logOR = d.md; d.id = d.name; d.group = d.group ?? 'Treatment vs comparator'; d.tE = d.tE ?? 0; d.cE = d.cE ?? 0; d.tN = d.tN ?? 0; d.cN = d.cN ?? 0; });\n\n\n\n"
)

# ---------- Edit 2: pool() return shape ----------
EDIT2_OLD = "            or: pMD.toFixed(2), lci: lci, uci: uci,\n\n\n            pOR: pMD, I2: I2, Q: Q, df: df, tau2: tau2,"
EDIT2_NEW = (
    "            or: pMD.toFixed(2), lci: lci, uci: uci,\n\n\n"
    "            pOR: pMD, pLogOR: pMD, pSE: pSE, zCrit: zCrit,\n\n\n"
    "            I2: I2, Q: Q, df: df, tau2: tau2,"
)

# ---------- Edit 3: Engine.render() Math.exp bug ----------
EDIT3_OLD = "                    this.renderPlots(c.plotData, parseFloat(c.or), parseFloat(c.pSE), Math.exp(parseFloat(c.or)), parseFloat(c.zCrit ?? 1.96), parseFloat(c.tau2), {}, {}, {});"
EDIT3_NEW = (
    "                    // Continuous MD: pLogOR=MD, pOR=MD (no exp back-transform), pSE/zCrit\n"
    "                    // come straight from ContinuousMDEngine. The downstream forest plot is\n"
    "                    // linear-scale; reference line at 0 is handled inside renderAnnotatedForest.\n"
    "                    this.renderPlots(c.plotData, parseFloat(c.pLogOR ?? c.or), parseFloat(c.pSE), parseFloat(c.pOR ?? c.or), parseFloat(c.zCrit ?? 1.96), parseFloat(c.tau2), {}, {}, {});"
)

# ---------- Edit 4: renderAnnotatedForest CONTINUOUS routing ----------
EDIT4_OLD = (
    "            renderAnnotatedForest(r, included) {\n\n\n"
    "                const confLevel = RapidMeta.state.confLevel ?? 0.95;\n\n\n"
    "                const zCrit = normalQuantile(1 - (1 - confLevel) / 2);\n\n\n"
    "                const ciPct = (confLevel * 100).toFixed(0);"
)
EDIT4_NEW = (
    "            renderAnnotatedForest(r, included) {\n\n\n"
    "                const confLevel = RapidMeta.state.confLevel ?? 0.95;\n\n\n"
    "                const zCrit = normalQuantile(1 - (1 - confLevel) / 2);\n\n\n"
    "                const ciPct = (confLevel * 100).toFixed(0);\n\n\n"
    "                // CONTINUOUS (MD) branch — for outcomes pooled by ContinuousMDEngine.\n"
    "                // Linear x-axis, reference at 0, no exp() back-transform.\n"
    "                // Binary OR/RR/HR branch below is unchanged.\n"
    "                if (r && r.isContinuous) {\n"
    "                    return this.renderAnnotatedForestMD(r, included, zCrit, ciPct);\n"
    "                }"
)

# ---------- Edit 5: append renderAnnotatedForestMD function ----------
EDIT5_OLD = (
    "                Plotly.newPlot('plot-forest-nyt', [trace], layout, { displayModeBar: false, responsive: true });\n\n\n"
    "            },"
)
EDIT5_NEW = (
    "                Plotly.newPlot('plot-forest-nyt', [trace], layout, { displayModeBar: false, responsive: true });\n\n\n"
    "            },\n\n\n"
    "            // Headline forest plot for CONTINUOUS (mean-difference) outcomes.\n"
    "            // Routed from renderAnnotatedForest when r.isContinuous === true.\n"
    "            // Linear x-axis, reference line at 0, no exp() back-transform.\n"
    "            renderAnnotatedForestMD(r, included, zCrit, ciPct) {\n"
    "                const studies = (r.plotData ?? []).map(d => {\n"
    "                    const md = d.md;\n"
    "                    const se = d.se;\n"
    "                    const lo = md - zCrit * se;\n"
    "                    const hi = md + zCrit * se;\n"
    "                    const w  = 1 / (se * se);\n"
    "                    return { name: d.name ?? d.id, year: d.year ?? '', md, lo, hi, w };\n"
    "                });\n"
    "                if (studies.length === 0) {\n"
    "                    Plotly.newPlot('plot-forest-nyt', [], { paper_bgcolor: 'rgba(0,0,0,0)', plot_bgcolor: 'rgba(0,0,0,0)' });\n"
    "                    return;\n"
    "                }\n"
    "                const totalW = studies.reduce((a, s) => a + s.w, 0);\n"
    "\n"
    "                const yLabels = studies.map(s => s.name + (s.year ? ' (' + s.year + ')' : ''));\n"
    "                yLabels.push('Pooled (RE)');\n"
    "\n"
    "                const xVals = studies.map(s => s.md);\n"
    "                xVals.push(parseFloat(r.or));\n"
    "\n"
    "                const errLo = studies.map(s => s.md - s.lo);\n"
    "                errLo.push(parseFloat(r.or) - parseFloat(r.lci));\n"
    "\n"
    "                const errHi = studies.map(s => s.hi - s.md);\n"
    "                errHi.push(parseFloat(r.uci) - parseFloat(r.or));\n"
    "\n"
    "                const sizes = studies.map(s => 8 + 20 * (s.w / totalW));\n"
    "                sizes.push(18);\n"
    "\n"
    "                const colors = studies.map(() => '#3b82f6');\n"
    "                colors.push('#ef4444');\n"
    "\n"
    "                const symbols = studies.map(() => 'square');\n"
    "                symbols.push('diamond');\n"
    "\n"
    "                const _selOutcome = RapidMeta.state.selectedOutcome || 'default';\n"
    "                const _outcomeLabel = (typeof RapidMeta.continuousAxisLabel === 'function')\n"
    "                    ? RapidMeta.continuousAxisLabel(_selOutcome)\n"
    "                    : 'Mean difference (intervention - comparator)';\n"
    "\n"
    "                const hoverTexts = studies.map(s =>\n"
    "                    s.name + '<br>MD: ' + s.md.toFixed(2) + ' (' + s.lo.toFixed(2) + '–' + s.hi.toFixed(2) + ')'\n"
    "                    + '<br>Weight: ' + (s.w / totalW * 100).toFixed(1) + '%'\n"
    "                );\n"
    "                hoverTexts.push('Pooled<br>MD: ' + r.or + ' (' + (parseFloat(r.lci)).toFixed(2) + '–' + (parseFloat(r.uci)).toFixed(2) + ')');\n"
    "\n"
    "                const annotations = studies.map((s, i) => ({\n"
    "                    x: Math.max(s.hi + 0.4, parseFloat(r.uci) + 0.4),\n"
    "                    y: i,\n"
    "                    text: '<b>' + s.md.toFixed(2) + '</b> [' + s.lo.toFixed(2) + ', ' + s.hi.toFixed(2) + '] W=' + (s.w / totalW * 100).toFixed(0) + '%',\n"
    "                    showarrow: false,\n"
    "                    font: { size: 9, color: '#94a3b8', family: 'JetBrains Mono' },\n"
    "                    xanchor: 'left'\n"
    "                }));\n"
    "                annotations.push({\n"
    "                    x: Math.max(parseFloat(r.uci) + 0.4, parseFloat(r.or) + 0.4),\n"
    "                    y: studies.length,\n"
    "                    text: '<b>' + parseFloat(r.or).toFixed(2) + '</b> [' + parseFloat(r.lci).toFixed(2) + ', ' + parseFloat(r.uci).toFixed(2) + ']',\n"
    "                    showarrow: false,\n"
    "                    font: { size: 10, color: '#ef4444', family: 'JetBrains Mono' },\n"
    "                    xanchor: 'left'\n"
    "                });\n"
    "\n"
    "                const _niMargin = (typeof RapidMeta.continuousNIMargin === 'function')\n"
    "                    ? RapidMeta.continuousNIMargin(_selOutcome)\n"
    "                    : null;\n"
    "                const _shapes = [\n"
    "                    { type: 'line', x0: 0, x1: 0, y0: -0.5, y1: yLabels.length - 0.5, line: { color: '#ef4444', width: 1.5, dash: 'dot' } }\n"
    "                ];\n"
    "                if (_niMargin && Number.isFinite(_niMargin.value)) {\n"
    "                    _shapes.push({ type: 'line', x0: _niMargin.value, x1: _niMargin.value, y0: -0.5, y1: yLabels.length - 0.5, line: { color: '#f59e0b', width: 1.5, dash: 'dash' } });\n"
    "                    annotations.push({\n"
    "                        x: _niMargin.value, y: -0.5, yanchor: 'bottom',\n"
    "                        text: 'NI margin (' + _niMargin.value + ')',\n"
    "                        showarrow: false,\n"
    "                        font: { size: 9, color: '#f59e0b', family: 'JetBrains Mono' }\n"
    "                    });\n"
    "                }\n"
    "                if (_niMargin && _niMargin.favoursLeft && _niMargin.favoursRight) {\n"
    "                    annotations.push(\n"
    "                        { xref: 'paper', yref: 'paper', x: 0.0, y: -0.16, xanchor: 'left',  text: '← favours ' + _niMargin.favoursLeft,  showarrow: false, font: { size: 9, color: '#94a3b8' } },\n"
    "                        { xref: 'paper', yref: 'paper', x: 1.0, y: -0.16, xanchor: 'right', text: 'favours ' + _niMargin.favoursRight + ' →', showarrow: false, font: { size: 9, color: '#94a3b8' } }\n"
    "                    );\n"
    "                }\n"
    "\n"
    "                const trace = {\n"
    "                    x: xVals, y: yLabels, mode: 'markers', type: 'scatter',\n"
    "                    marker: { size: sizes, color: colors, symbol: symbols },\n"
    "                    error_x: { type: 'data', symmetric: false, array: errHi, arrayminus: errLo, visible: true, color: '#3b82f6', thickness: 2 },\n"
    "                    hovertext: hoverTexts, hoverinfo: 'text'\n"
    "                };\n"
    "\n"
    "                const layout = {\n"
    "                    paper_bgcolor: 'rgba(0,0,0,0)', plot_bgcolor: 'rgba(0,0,0,0)',\n"
    "                    xaxis: { title: _outcomeLabel + ' (' + ciPct + '% CI)', gridcolor: '#1e293b', color: '#94a3b8', zeroline: false },\n"
    "                    yaxis: { gridcolor: '#1e293b', color: '#94a3b8', autorange: 'reversed' },\n"
    "                    font: { color: '#94a3b8', size: 10 },\n"
    "                    margin: { t: 10, b: 70, l: 160, r: 200 },\n"
    "                    shapes: _shapes,\n"
    "                    annotations: annotations,\n"
    "                    showlegend: false\n"
    "                };\n"
    "\n"
    "                Plotly.newPlot('plot-forest-nyt', [trace], layout, { displayModeBar: false, responsive: true });\n"
    "\n"
    "                const cap = document.querySelector('#plot-forest-nyt')?.closest('section, div')?.querySelector('.nyt-figure-caption');\n"
    "                if (cap) cap.textContent = 'Fig. - Forest plot of ' + _outcomeLabel + ' (random-effects, DL estimator)';\n"
    "            },"
)

# ---------- Edit 6: insert helpers ----------
EDIT6_OLD = "                return map[format] ?? em;\n\n\n            },\n\n\n            outcomeLabel(key) {"
EDIT6_NEW = (
    "                return map[format] ?? em;\n\n\n"
    "            },\n\n\n"
    "            // Axis label for continuous (mean-difference) forest plots. Routed from\n"
    "            // renderAnnotatedForestMD. Override per dashboard to set domain-specific\n"
    "            // wording (units, contrast direction).\n"
    "            continuousAxisLabel(outcomeKey) {\n"
    "                return 'Mean difference (intervention - comparator)';\n"
    "            },\n\n\n"
    "            // Non-inferiority margin overlay. Returns {value, favoursLeft, favoursRight}\n"
    "            // or null. Default null (no overlay). Override per dashboard for NI trials\n"
    "            // (e.g. nAMD pivotals where margin is -4 ETDRS letters).\n"
    "            continuousNIMargin(outcomeKey) {\n"
    "                return null;\n"
    "            },\n\n\n"
    "            outcomeLabel(key) {"
)

# ---------- Edit 7: hardcoded MACE composite caption ----------
# Two known patterns observed across the template:
#   "Fig. — Forest plot of <something> vs <something> for MACE composite (random-effects, DL estimator)"
EDIT7_RE = re.compile(
    r'<p class="nyt-figure-caption mt-3">Fig\. [—-] Forest plot of [^<]*?for MACE composite \(random-effects, DL estimator\)</p>'
)
EDIT7_NEW = '<p class="nyt-figure-caption mt-3">Fig. - Forest plot of the registered primary continuous outcome (random-effects, DL estimator)</p>'


def apply_edit(src, old, new, label, sentinel=None):
    """Apply edit only if old still present and the unique sentinel isn't.

    Some edits' OLD anchors are prefixes of their NEW replacement (e.g. edit5
    keeps the original Plotly call line), which would re-fire on every run if
    we only checked `old in src`. Pass a `sentinel` string from NEW that does
    NOT appear in the original file - if present, the edit is already done.
    """
    if sentinel is not None and sentinel in src:
        return src, 'SKIP_already_applied'
    if new in src and old not in src:
        return src, 'SKIP_already_applied'
    if old not in src:
        return src, 'SKIP_anchor_not_found'
    if src.count(old) > 1:
        return src, f'SKIP_anchor_ambiguous ({src.count(old)} matches)'
    return src.replace(old, new, 1), 'APPLIED'


def apply_edit_re(src, regex, new, label):
    matches = regex.findall(src)
    if not matches:
        if new in src:
            return src, 'SKIP_already_applied'
        return src, 'SKIP_anchor_not_found'
    return regex.sub(new, src), f'APPLIED ({len(matches)} match(es))'


def patch_file(path, dry=False):
    src = open(path, 'r', encoding='utf-8').read()
    original = src
    log = []
    # Sentinel strings unique to each NEW that aren't in the original template.
    # Used for idempotency when OLD is a prefix of NEW (edit5).
    edits = [
        (EDIT1_OLD, EDIT1_NEW, 'plotData alias',     'd.logOR = d.md'),
        (EDIT2_OLD, EDIT2_NEW, 'pool() return shape','pLogOR: pMD, pSE: pSE, zCrit: zCrit'),
        (EDIT3_OLD, EDIT3_NEW, 'Math.exp() bug',     'pLogOR ?? c.or'),
        (EDIT4_OLD, EDIT4_NEW, 'forest routing',     'r && r.isContinuous'),
        (EDIT5_OLD, EDIT5_NEW, 'forestMD function',  'renderAnnotatedForestMD(r, included, zCrit, ciPct) {'),
        (EDIT6_OLD, EDIT6_NEW, 'helpers',            'continuousAxisLabel(outcomeKey) {'),
    ]
    for i, (old, new, label, sentinel) in enumerate(edits, start=1):
        src, status = apply_edit(src, old, new, label, sentinel=sentinel)
        log.append(f'  edit{i} ({label}): {status}')
    src, status = apply_edit_re(src, EDIT7_RE, EDIT7_NEW, 'caption')
    log.append(f'  edit7 (caption): {status}')

    changed = src != original
    if changed and not dry:
        open(path, 'w', encoding='utf-8').write(src)
    return changed, log


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--dry-run', action='store_true')
    args = ap.parse_args()
    print(f'Mode: {"DRY-RUN" if args.dry_run else "APPLY"}')
    summary = {'changed': 0, 'unchanged': 0, 'errors': 0}
    for fname in TARGETS:
        path = os.path.join(ROOT, fname)
        if not os.path.exists(path):
            print(f'\n[ERROR] {fname}: not found')
            summary['errors'] += 1
            continue
        try:
            changed, log = patch_file(path, dry=args.dry_run)
            tag = 'CHANGED' if changed else 'unchanged'
            print(f'\n[{tag}] {fname}')
            for line in log:
                print(line)
            summary['changed' if changed else 'unchanged'] += 1
        except Exception as e:
            print(f'\n[ERROR] {fname}: {e}')
            summary['errors'] += 1
    print(f'\nSummary: {summary}')
    return 0 if summary['errors'] == 0 else 1


if __name__ == '__main__':
    sys.exit(main())
