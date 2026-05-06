#!/usr/bin/env python3
# sentinel:skip-file — developer tool; hardcoded ROOT is intentional (local Finrenone checkout only)
"""Propagate the NMA-specific journal-text generator (introduced in CFTR at
6d3a8a0) to the 21 remaining NMA apps. Three edits per app, idempotent:
  1. Populate the empty `<div id="nma-summary-container" class="mb-8"></div>`
     with an indigo-bordered "Auto-Generated NMA Manuscript Text" panel.
  2. Add generateNMAManuscriptText() + copyNMAManuscriptText() functions
     immediately before the existing `function copyManuscriptText() {`.
  3. Hook the call into NMAEngine.render() after `this.renderOutput();`.
"""
import argparse, pathlib, sys

ROOT = pathlib.Path(__file__).resolve().parent.parent

EDIT1_OLD = '                            <div id="nma-summary-container" class="mb-8"></div>'
EDIT1_NEW = (
    '                            <div id="nma-summary-container" class="mb-8"></div>\n'
    '\n'
    '                            <!-- NMA Auto-Generated Manuscript Text (Methods + Results) -->\n'
    '                            <div class="glass p-8 rounded-[30px] border border-indigo-500/20 bg-indigo-500/5 mb-8">\n'
    '                                <div class="flex items-center justify-between mb-4">\n'
    '                                    <h4 class="text-xs font-bold opacity-60 uppercase tracking-[0.3em]"><i class="fa-solid fa-pen-nib mr-1"></i> Auto-Generated NMA Manuscript Text</h4>\n'
    '                                    <button onclick="copyNMAManuscriptText()" class="text-[11px] font-bold text-indigo-400 uppercase bg-indigo-400/10 px-4 py-1.5 rounded-full border border-indigo-400/20 hover:bg-indigo-400/20 transition-all"><i class="fa-solid fa-copy mr-1"></i> Copy All</button>\n'
    '                                </div>\n'
    '                                <div id="nma-manuscript-text" class="space-y-6 text-sm text-slate-300 leading-relaxed" style="font-family: Georgia, serif;" aria-live="polite">\n'
    '                                    <p class="text-slate-500 italic">Click "Run NMA" to generate Methods + Results text describing this network.</p>\n'
    '                                </div>\n'
    '                            </div>'
)

EDIT2_OLD = (
    '                this.renderNetwork();\n'
    '                this.renderLeagueTable();\n'
    '                this.renderRankings();\n'
    '                this.renderConsistency();\n'
    '                this.renderOutput();\n'
    "                showToast('NMA complete: '"
)
EDIT2_NEW = (
    '                this.renderNetwork();\n'
    '                this.renderLeagueTable();\n'
    '                this.renderRankings();\n'
    '                this.renderConsistency();\n'
    '                this.renderOutput();\n'
    '                try { if (typeof generateNMAManuscriptText === \'function\') generateNMAManuscriptText(); } catch (e) {}\n'
    "                showToast('NMA complete: '"
)

EDIT3_OLD = '        function copyManuscriptText() {'
EDIT3_NEW = (
    '        /* ── NMA Auto-Generated Manuscript Text ─────────────────────\n'
    '           Builds a Methods + Results paragraph that describes the network\n'
    '           (treatments, geometry, direct vs indirect contrasts, consistency,\n'
    '           transitivity) using the NMA_CONFIG declaration plus the live\n'
    '           pool from NMAEngine._getAllPairwise(). Called from NMAEngine.render()\n'
    '           after the network is computed. ──────────────────────────── */\n'
    '        function generateNMAManuscriptText() {\n'
    "            const cfg = (typeof NMA_CONFIG !== 'undefined') ? NMA_CONFIG : null;\n"
    '            if (!cfg || !cfg.treatments) return;\n'
    "            const container = document.getElementById('nma-manuscript-text');\n"
    '            if (!container) return;\n'
    '\n'
    '            const treatments = cfg.treatments || [];\n'
    '            const comparisons = cfg.comparisons || [];\n'
    '            const T = treatments.length;\n'
    '            const D = comparisons.length;\n'
    '            const trialIdSet = new Set();\n'
    '            comparisons.forEach(c => (c.trials || []).forEach(id => trialIdSet.add(id)));\n'
    '            const K = trialIdSet.size;\n'
    '\n'
    '            // Total N across all unique trials in the network\n'
    '            let totalN = 0;\n'
    '            for (const id of trialIdSet) {\n'
    '                const d = (RapidMeta.realData || {})[id];\n'
    '                if (d && d.tN && d.cN) totalN += (d.tN + d.cN);\n'
    '            }\n'
    '\n'
    '            // Network geometry detection: a star is when T-1 == D and the hub appears in every comparison\n'
    '            const degree = {};\n'
    '            treatments.forEach(t => degree[t] = 0);\n'
    '            comparisons.forEach(c => { degree[c.t1] = (degree[c.t1] || 0) + 1; degree[c.t2] = (degree[c.t2] || 0) + 1; });\n'
    '            const maxDeg = Math.max(0, ...Object.values(degree));\n'
    '            const hub = treatments.find(t => degree[t] === maxDeg) || null;\n'
    '            const isStar = (T - 1 === D) && hub && (degree[hub] === D);\n'
    '            const hasLoops = D >= T;\n'
    '\n'
    "            const outcomeLabel = cfg.outcome_label || cfg.outcome || 'the primary outcome';\n"
    "            const refTreatment = hub || treatments[treatments.length - 1] || 'the reference';\n"
    '\n'
    '            // Build network estimate sentences from NMAEngine._getAllPairwise() if available\n'
    "            let pairwiseSentence = '';\n"
    '            try {\n'
    "                if (typeof NMAEngine !== 'undefined' && typeof NMAEngine._getAllPairwise === 'function') {\n"
    '                    const all = NMAEngine._getAllPairwise() || {};\n'
    '                    const lines = [];\n'
    '                    for (const t of treatments) {\n'
    '                        if (t === refTreatment) continue;\n'
    "                        const direct = all[t + '|' + refTreatment] || all[refTreatment + '|' + t];\n"
    "                        const flipped = !!(all[refTreatment + '|' + t] && !all[t + '|' + refTreatment]);\n"
    '                        const result = direct;\n'
    '                        if (!result) continue;\n'
    '                        const candidate = result.network || result.direct || result.indirect;\n'
    '                        if (!candidate || !Number.isFinite(candidate.logEffect)) continue;\n'
    '                        const logEff = flipped ? -candidate.logEffect : candidate.logEffect;\n'
    "                        const measure = candidate.measure || result.measure || 'effect';\n"
    "                        const isLogScale = (measure === 'OR' || measure === 'RR' || measure === 'HR');\n"
    '                        const eff = isLogScale ? Math.exp(logEff) : logEff;\n'
    '                        const lo = isLogScale ? Math.exp(logEff - 1.96 * candidate.se) : (logEff - 1.96 * candidate.se);\n'
    '                        const hi = isLogScale ? Math.exp(logEff + 1.96 * candidate.se) : (logEff + 1.96 * candidate.se);\n'
    "                        lines.push(t + ' vs ' + refTreatment + ': ' + measure + ' ' +\n"
    "                            eff.toFixed(2) + ' (95% CI ' + lo.toFixed(2) + ' to ' + hi.toFixed(2) + ')');\n"
    '                    }\n'
    '                    if (lines.length > 0) {\n'
    "                        pairwiseSentence = ' Network estimates against ' + refTreatment + ' were: ' + lines.join('; ') + '.';\n"
    '                    }\n'
    '                }\n'
    '            } catch (e) { /* silent — pairwise sentence stays empty */ }\n'
    '\n'
    '            // Methods paragraph\n'
    "            const methods = 'We conducted a frequentist network meta-analysis combining direct and indirect treatment comparisons across ' +\n"
    "                K + ' randomized controlled trial' + (K !== 1 ? 's' : '') + ' covering ' + T + ' treatments (' + treatments.join(', ') + '). ' +\n"
    "                'Trial-level effects were pooled on the log scale by inverse-variance random-effects meta-analysis using the DerSimonian-Laird \\u03C4\\u00B2 estimator; ' +\n"
    "                'indirect contrasts were derived by Bucher subtraction through ' + refTreatment + ' as the common comparator. ' +\n"
    '                (hasLoops\n'
    "                    ? 'Design-by-treatment inconsistency was assessed by node-splitting on closed loops (P < 0.10 indicating possible inconsistency). '\n"
    "                    : 'The network has no closed loops, so internal inconsistency (node-splitting, design-by-treatment) is not testable; the transitivity assumption was therefore evaluated from clinical and methodological homogeneity across trials. ') +\n"
    "                'Treatment ranking was reported by P-score (the frequentist analogue of SUCRA), interpreted strictly as a ranking probability rather than a measure of effect magnitude. ' +\n"
    "                'The estimand is ' + outcomeLabel + '. ' +\n"
    "                'Reporting follows PRISMA-NMA 2020.';\n"
    '\n'
    '            // Results paragraph\n'
    '            const sentences = [];\n'
    "            sentences.push('The network comprised ' + T + ' treatments connected by ' + D + ' direct comparison' + (D !== 1 ? 's' : '') +\n"
    "                ' from ' + K + ' randomized trial' + (K !== 1 ? 's' : '') +\n"
    "                (totalN > 0 ? ' (n = ' + totalN.toLocaleString() + ' randomized participants in total)' : '') + '.');\n"
    '            sentences.push(isStar\n'
    "                ? 'The geometry is a placebo-anchored star with ' + refTreatment + ' as the common comparator and no closed loops; ' +\n"
    "                  'consistency cannot be tested by node-splitting and was assessed clinically.'\n"
    "                : 'The network contains closed loops permitting node-splitting consistency assessment; see the Consistency Assessment panel above for per-comparison results.');\n"
    '            if (pairwiseSentence) sentences.push(pairwiseSentence.trim());\n'
    "            if (cfg.note) sentences.push('Transitivity considerations: ' + cfg.note);\n"
    "            sentences.push('Treatment rankings via P-score should be interpreted as ranking probabilities, not as differences in effect magnitude — readers should always cross-reference the league table for the underlying contrasts.');\n"
    '\n'
    "            const results = sentences.join(' ');\n"
    '\n'
    '            container.innerHTML =\n'
    "                '<div><div class=\"text-[10px] font-bold text-indigo-400 uppercase tracking-widest mb-2\">Methods (estimand: ' + escapeHtml(outcomeLabel) + ')</div>' +\n"
    "                '<p>' + escapeHtml(methods) + '</p></div>' +\n"
    "                '<div><div class=\"text-[10px] font-bold text-indigo-400 uppercase tracking-widest mb-2\">Results</div>' +\n"
    "                '<p>' + escapeHtml(results) + '</p></div>' +\n"
    "                '<div class=\"text-[9px] text-slate-600 italic mt-2\">Generated by RapidMeta NMA. Numbers reflect the most recent NMA run; click \"Run NMA\" again to refresh after changing trial inclusion. Verify against the league table before submission.</div>';\n"
    '        }\n'
    '\n'
    '        function copyNMAManuscriptText() {\n'
    "            const el = document.getElementById('nma-manuscript-text');\n"
    '            if (!el) return;\n'
    '            const text = el.innerText;\n'
    "            navigator.clipboard.writeText(text).then(() => showToast('NMA manuscript text copied.')).catch(() => {\n"
    "                const ta = document.createElement('textarea'); ta.value = text; document.body.appendChild(ta); ta.select(); document.execCommand('copy'); ta.remove(); showToast('NMA manuscript text copied.');\n"
    '            });\n'
    '        }\n'
    '\n'
    '        function copyManuscriptText() {'
)


def apply_to_file(path: pathlib.Path, dry_run: bool) -> str:
    text = path.read_text(encoding="utf-8", newline="")
    if "function generateNMAManuscriptText()" in text:
        return f"SKIP {path.name}: already-migrated"
    if "const NMA_CONFIG" not in text:
        return f"SKIP {path.name}: not an NMA app (no NMA_CONFIG)"
    if "const NMA_CONFIG = null" in text:
        return f"SKIP {path.name}: NMA_CONFIG=null (pairwise scaffold, no real network)"

    crlf = "\r\n" in text
    work = text.replace("\r\n", "\n") if crlf else text

    for label, old, new in (("EDIT1-panel", EDIT1_OLD, EDIT1_NEW),
                            ("EDIT2-render-hook", EDIT2_OLD, EDIT2_NEW),
                            ("EDIT3-functions", EDIT3_OLD, EDIT3_NEW)):
        if work.count(old) != 1:
            return f"FAIL {path.name}: {label} matched {work.count(old)} times (expected 1)"
        work = work.replace(old, new, 1)

    if not dry_run:
        out = work.replace("\n", "\r\n") if crlf else work
        path.write_text(out, encoding="utf-8", newline="")
    return f"OK   {path.name}: +{len(work) - len(text.replace(chr(13)+chr(10), chr(10)) if crlf else text)} chars"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()
    if not (args.dry_run or args.apply):
        ap.error("pass --dry-run or --apply")

    targets = sorted(ROOT.glob("*_REVIEW.html"))
    ok = skip = fail = 0
    for p in targets:
        result = apply_to_file(p, dry_run=args.dry_run)
        if result.startswith("OK"): ok += 1
        elif result.startswith("SKIP"): skip += 1
        else: fail += 1
        if not result.startswith("SKIP") or args.dry_run:
            print(result)
    print(f"\nSummary: {len(targets)} files | {ok} migrate | {skip} skip | {fail} fail | mode={'dry-run' if args.dry_run else 'apply'}")
    if fail:
        sys.exit(1)


if __name__ == "__main__":
    main()
