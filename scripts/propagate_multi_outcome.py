#!/usr/bin/env python3
# sentinel:skip-file — developer tool; hardcoded ROOT is intentional (local Finrenone checkout only)
"""Propagate the multi-outcome NMA refactor (CFTR commit b84ba3f) to the 21
other NMA apps. Three byte-exact substitutions per file (idempotent — skips
if _getNetworkOutcomeKeys is already present):

  1. NMAEngine: insert _getNetworkOutcomeKeys + _getTrialEffectForOutcome
     above the existing _getTrialEffect, and refactor _getTrialEffect to a
     backward-compatible delegate.
  2. NMAEngine: refactor _poolEffects to accept optional outcomeKey.
  3. NMAEngine: refactor _getAllPairwise to accept optional outcomeKey.
  4. Refactor generateNMAManuscriptText into outer (loops detected outcomes)
     + inner _buildNMABlockForOutcome (returns {methods, results, outcomeLabel}).
"""
import argparse, pathlib, sys

ROOT = pathlib.Path(r"C:\Projects\Finrenone")

# Edit 1: insert helpers + replace _getTrialEffect with a delegate.
EDIT1_OLD = (
    "            _getTrialEffect(nctId) {\n"
    "                const trial = (RapidMeta.state.trials ?? []).find(t => t.id === nctId);\n"
    "                const d = trial?.data ?? RapidMeta.realData?.[nctId];\n"
    "                if (!d || !d.tN || !d.cN) return null;\n"
    "                if (d.publishedHR && d.hrLCI && d.hrUCI) {\n"
    "                    const logHR = Math.log(d.publishedHR);\n"
    "                    const se = (Math.log(d.hrUCI) - Math.log(d.hrLCI)) / 3.92;\n"
    "                    return { logEffect: logHR, se, measure: 'HR', n: d.tN + d.cN };\n"
    "                }\n"
    "                if (d.tE > 0 || d.cE > 0) {\n"
    "                    const hasZero = (d.tE === 0 || d.cE === 0 || d.tN - d.tE === 0 || d.cN - d.cE === 0);\n"
    "                    const tE = hasZero ? d.tE + 0.5 : d.tE, tN = hasZero ? d.tN + 1 : d.tN;\n"
    "                    const cE = hasZero ? d.cE + 0.5 : d.cE, cN = hasZero ? d.cN + 1 : d.cN;\n"
    "                    const logRR = Math.log((tE / tN) / (cE / cN));\n"
    "                    const se = Math.sqrt(1/tE - 1/tN + 1/cE - 1/cN);\n"
    "                    return { logEffect: logRR, se, measure: 'RR', n: d.tN + d.cN };\n"
    "                }\n"
    "                return null;\n"
    "            },\n"
    "\n"
    "            _poolEffects(trialIds) {\n"
    "                const effects = trialIds.map(id => this._getTrialEffect(id)).filter(Boolean);\n"
    "                if (effects.length === 0) return null;\n"
    "                if (effects.length === 1) return effects[0];\n"
    "                const weights = effects.map(e => 1 / (e.se * e.se));\n"
    "                const wSum = weights.reduce((a, b) => a + b, 0);\n"
    "                const logEffect = effects.reduce((s, e, i) => s + weights[i] * e.logEffect, 0) / wSum;\n"
    "                const se = Math.sqrt(1 / wSum);\n"
    "                const n = effects.reduce((s, e) => s + e.n, 0);\n"
    "                return { logEffect, se, measure: effects[0].measure, n };\n"
    "            },"
)

EDIT1_NEW = (
    "            /* List distinct outcome shortLabels reported across trials in the network.\n"
    "               Returns [] if no trial has allOutcomes[]; the caller can then fall back\n"
    "               to the network's declared cfg.outcome / cfg.outcome_label. */\n"
    "            _getNetworkOutcomeKeys() {\n"
    "                const cfg = this._getConfig();\n"
    "                if (!cfg) return [];\n"
    "                const trialIdSet = new Set();\n"
    "                (cfg.comparisons ?? []).forEach(c => (c.trials ?? []).forEach(id => trialIdSet.add(id)));\n"
    "                const labels = new Set();\n"
    "                for (const id of trialIdSet) {\n"
    "                    const trial = (RapidMeta.state.trials ?? []).find(t => t.id === id);\n"
    "                    const d = trial?.data ?? RapidMeta.realData?.[id];\n"
    "                    for (const oc of (d?.allOutcomes ?? [])) {\n"
    "                        if (oc?.shortLabel) labels.add(oc.shortLabel);\n"
    "                    }\n"
    "                }\n"
    "                return [...labels];\n"
    "            },\n"
    "\n"
    "            /* Per-outcome effect extraction. If outcomeKey is non-null, look up the\n"
    "               matching entry in data.allOutcomes[] by shortLabel and use its\n"
    "               pubHR/pubHR_LCI/pubHR_UCI. If outcomeKey is null OR no match exists,\n"
    "               fall back to the trial-level publishedHR (the legacy primary-only path). */\n"
    "            _getTrialEffectForOutcome(nctId, outcomeKey) {\n"
    "                const trial = (RapidMeta.state.trials ?? []).find(t => t.id === nctId);\n"
    "                const d = trial?.data ?? RapidMeta.realData?.[nctId];\n"
    "                if (!d || !d.tN || !d.cN) return null;\n"
    "\n"
    "                /* Path 1: outcome-specific extraction from allOutcomes[i] */\n"
    "                if (outcomeKey) {\n"
    "                    const oc = (d.allOutcomes ?? []).find(o => o?.shortLabel === outcomeKey);\n"
    "                    if (oc && oc.pubHR && oc.pubHR_LCI && oc.pubHR_UCI) {\n"
    "                        const logHR = Math.log(oc.pubHR);\n"
    "                        const se = (Math.log(oc.pubHR_UCI) - Math.log(oc.pubHR_LCI)) / 3.92;\n"
    "                        return { logEffect: logHR, se, measure: 'HR', n: d.tN + d.cN, outcomeKey };\n"
    "                    }\n"
    "                    /* If a specific outcome was requested but the trial doesn't report\n"
    "                       it with a usable point estimate, return null so this trial is\n"
    "                       excluded from the per-outcome network. */\n"
    "                    return null;\n"
    "                }\n"
    "\n"
    "                /* Path 2: legacy trial-level extraction (network primary outcome) */\n"
    "                if (d.publishedHR && d.hrLCI && d.hrUCI) {\n"
    "                    const logHR = Math.log(d.publishedHR);\n"
    "                    const se = (Math.log(d.hrUCI) - Math.log(d.hrLCI)) / 3.92;\n"
    "                    return { logEffect: logHR, se, measure: 'HR', n: d.tN + d.cN };\n"
    "                }\n"
    "                if (d.tE > 0 || d.cE > 0) {\n"
    "                    const hasZero = (d.tE === 0 || d.cE === 0 || d.tN - d.tE === 0 || d.cN - d.cE === 0);\n"
    "                    const tE = hasZero ? d.tE + 0.5 : d.tE, tN = hasZero ? d.tN + 1 : d.tN;\n"
    "                    const cE = hasZero ? d.cE + 0.5 : d.cE, cN = hasZero ? d.cN + 1 : d.cN;\n"
    "                    const logRR = Math.log((tE / tN) / (cE / cN));\n"
    "                    const se = Math.sqrt(1/tE - 1/tN + 1/cE - 1/cN);\n"
    "                    return { logEffect: logRR, se, measure: 'RR', n: d.tN + d.cN };\n"
    "                }\n"
    "                return null;\n"
    "            },\n"
    "\n"
    "            _getTrialEffect(nctId) {\n"
    "                /* Backward-compatible delegate — returns the trial-level primary effect. */\n"
    "                return this._getTrialEffectForOutcome(nctId, null);\n"
    "            },\n"
    "\n"
    "            _poolEffects(trialIds, outcomeKey) {\n"
    "                const effects = trialIds.map(id => this._getTrialEffectForOutcome(id, outcomeKey ?? null)).filter(Boolean);\n"
    "                if (effects.length === 0) return null;\n"
    "                if (effects.length === 1) return effects[0];\n"
    "                const weights = effects.map(e => 1 / (e.se * e.se));\n"
    "                const wSum = weights.reduce((a, b) => a + b, 0);\n"
    "                const logEffect = effects.reduce((s, e, i) => s + weights[i] * e.logEffect, 0) / wSum;\n"
    "                const se = Math.sqrt(1 / wSum);\n"
    "                const n = effects.reduce((s, e) => s + e.n, 0);\n"
    "                return { logEffect, se, measure: effects[0].measure, n, outcomeKey: outcomeKey ?? null };\n"
    "            },"
)

# Edit 2: refactor _getAllPairwise to accept outcomeKey.
EDIT2_OLD = (
    "            _getAllPairwise() {\n"
    "                const cfg = this._getConfig();\n"
    "                if (!cfg) return {};\n"
    "                const treatments = cfg.treatments;\n"
    "                const results = {};\n"
    "                for (let i = 0; i < treatments.length; i++) {\n"
    "                    for (let j = i + 1; j < treatments.length; j++) {\n"
    "                        const t1 = treatments[i], t2 = treatments[j];\n"
    "                        const key = `${t1}|${t2}`;\n"
    "                        const comp = (cfg.comparisons ?? []).find(c =>\n"
    "                            (c.t1 === t1 && c.t2 === t2) || (c.t1 === t2 && c.t2 === t1));\n"
    "                        const trials = comp?.trials ?? [];\n"
    "                        const flipped = comp && comp.t1 === t2;\n"
    "                        let direct = null;\n"
    "                        if (trials.length > 0) {\n"
    "                            direct = this._poolEffects(trials);\n"
    "                            if (direct && flipped) direct = { ...direct, logEffect: -direct.logEffect };\n"
    "                        }\n"
    "                        let indirect = null;\n"
    "                        for (const common of treatments) {\n"
    "                            if (common === t1 || common === t2) continue;\n"
    "                            const compAC = (cfg.comparisons ?? []).find(c =>\n"
    "                                (c.t1 === t1 && c.t2 === common) || (c.t1 === common && c.t2 === t1));\n"
    "                            const compBC = (cfg.comparisons ?? []).find(c =>\n"
    "                                (c.t1 === t2 && c.t2 === common) || (c.t1 === common && c.t2 === t2));\n"
    "                            if (!compAC?.trials?.length || !compBC?.trials?.length) continue;\n"
    "                            let effAC = this._poolEffects(compAC.trials);\n"
    "                            let effBC = this._poolEffects(compBC.trials);\n"
    "                            if (!effAC || !effBC) continue;\n"
    "                            if (compAC.t1 === common) effAC = { ...effAC, logEffect: -effAC.logEffect };\n"
    "                            if (compBC.t1 === common) effBC = { ...effBC, logEffect: -effBC.logEffect };\n"
    "                            indirect = this._bucher(effAC, effBC);\n"
    "                            break;\n"
    "                        }\n"
    "                        const best = direct ?? indirect ?? null;\n"
    "                        results[key] = { direct, indirect, combined: best, t1, t2 };\n"
    "                    }\n"
    "                }\n"
    "                return results;\n"
    "            },"
)

EDIT2_NEW = (
    "            _getAllPairwise(outcomeKey) {\n"
    "                const cfg = this._getConfig();\n"
    "                if (!cfg) return {};\n"
    "                const treatments = cfg.treatments;\n"
    "                const results = {};\n"
    "                for (let i = 0; i < treatments.length; i++) {\n"
    "                    for (let j = i + 1; j < treatments.length; j++) {\n"
    "                        const t1 = treatments[i], t2 = treatments[j];\n"
    "                        const key = `${t1}|${t2}`;\n"
    "                        const comp = (cfg.comparisons ?? []).find(c =>\n"
    "                            (c.t1 === t1 && c.t2 === t2) || (c.t1 === t2 && c.t2 === t1));\n"
    "                        const trials = comp?.trials ?? [];\n"
    "                        const flipped = comp && comp.t1 === t2;\n"
    "                        let direct = null;\n"
    "                        if (trials.length > 0) {\n"
    "                            direct = this._poolEffects(trials, outcomeKey ?? null);\n"
    "                            if (direct && flipped) direct = { ...direct, logEffect: -direct.logEffect };\n"
    "                        }\n"
    "                        let indirect = null;\n"
    "                        for (const common of treatments) {\n"
    "                            if (common === t1 || common === t2) continue;\n"
    "                            const compAC = (cfg.comparisons ?? []).find(c =>\n"
    "                                (c.t1 === t1 && c.t2 === common) || (c.t1 === common && c.t2 === t1));\n"
    "                            const compBC = (cfg.comparisons ?? []).find(c =>\n"
    "                                (c.t1 === t2 && c.t2 === common) || (c.t1 === common && c.t2 === t2));\n"
    "                            if (!compAC?.trials?.length || !compBC?.trials?.length) continue;\n"
    "                            let effAC = this._poolEffects(compAC.trials, outcomeKey ?? null);\n"
    "                            let effBC = this._poolEffects(compBC.trials, outcomeKey ?? null);\n"
    "                            if (!effAC || !effBC) continue;\n"
    "                            if (compAC.t1 === common) effAC = { ...effAC, logEffect: -effAC.logEffect };\n"
    "                            if (compBC.t1 === common) effBC = { ...effBC, logEffect: -effBC.logEffect };\n"
    "                            indirect = this._bucher(effAC, effBC);\n"
    "                            break;\n"
    "                        }\n"
    "                        const best = direct ?? indirect ?? null;\n"
    "                        results[key] = { direct, indirect, combined: best, t1, t2, outcomeKey: outcomeKey ?? null };\n"
    "                    }\n"
    "                }\n"
    "                return results;\n"
    "            },"
)

# Edit 3: refactor generateNMAManuscriptText into outer loop + inner block builder.
# OLD = the function header line + entire body up to the container.innerHTML close.
EDIT3_OLD_HEADER = (
    "        function generateNMAManuscriptText() {\n"
    "            const cfg = (typeof NMA_CONFIG !== 'undefined') ? NMA_CONFIG : null;\n"
    "            if (!cfg || !cfg.treatments) return;\n"
    "            const container = document.getElementById('nma-manuscript-text');\n"
    "            if (!container) return;\n"
    "\n"
    "            const treatments = cfg.treatments || [];"
)
EDIT3_NEW_HEADER = (
    "        /* Build one Methods+Results block for a specific outcome on the network.\n"
    "           If outcomeKey is null, uses the network's declared primary\n"
    "           (cfg.outcome_label) and the legacy trial-level publishedHR path.\n"
    "           If outcomeKey is provided, uses per-outcome NMA pool via\n"
    "           NMAEngine._getAllPairwise(outcomeKey). Returns { methods, results }. */\n"
    "        function _buildNMABlockForOutcome(cfg, outcomeKey, displayLabel) {\n"
    "            const treatments = cfg.treatments || [];"
)

EDIT4_OLD = (
    "            const outcomeLabel = cfg.outcome_label || cfg.outcome || 'the primary outcome';\n"
    "            const refTreatment = hub || treatments[treatments.length - 1] || 'the reference';\n"
    "\n"
    "            // Build network estimate sentences from NMAEngine._getAllPairwise() if available\n"
    "            let pairwiseSentence = '';\n"
    "            try {\n"
    "                if (typeof NMAEngine !== 'undefined' && typeof NMAEngine._getAllPairwise === 'function') {\n"
    "                    const all = NMAEngine._getAllPairwise() || {};"
)
EDIT4_NEW = (
    "            const outcomeLabel = displayLabel || cfg.outcome_label || cfg.outcome || 'the primary outcome';\n"
    "            const refTreatment = hub || treatments[treatments.length - 1] || 'the reference';\n"
    "\n"
    "            // Build network estimate sentences from NMAEngine._getAllPairwise() — pass outcomeKey\n"
    "            // so the per-outcome path is used when this block represents a non-primary outcome.\n"
    "            let pairwiseSentence = '';\n"
    "            try {\n"
    "                if (typeof NMAEngine !== 'undefined' && typeof NMAEngine._getAllPairwise === 'function') {\n"
    "                    const all = NMAEngine._getAllPairwise(outcomeKey) || {};"
)

EDIT5_OLD = (
    "            const results = sentences.join(' ');\n"
    "\n"
    "            container.innerHTML =\n"
    "                '<div><div class=\"text-[10px] font-bold text-indigo-400 uppercase tracking-widest mb-2\">Methods (estimand: ' + escapeHtml(outcomeLabel) + ')</div>' +\n"
    "                '<p>' + escapeHtml(methods) + '</p></div>' +\n"
    "                '<div><div class=\"text-[10px] font-bold text-indigo-400 uppercase tracking-widest mb-2\">Results</div>' +\n"
    "                '<p>' + escapeHtml(results) + '</p></div>' +\n"
    "                '<div class=\"text-[9px] text-slate-600 italic mt-2\">Generated by RapidMeta NMA. Numbers reflect the most recent NMA run; click \"Run NMA\" again to refresh after changing trial inclusion. Verify against the league table before submission.</div>';\n"
    "        }\n"
    "\n"
    "        function copyNMAManuscriptText() {"
)
EDIT5_NEW = (
    "            const results = sentences.join(' ');\n"
    "            return { methods, results, outcomeLabel };\n"
    "        }\n"
    "\n"
    "        /* Outer entry point: detects per-outcome data via NMAEngine._getNetworkOutcomeKeys()\n"
    "           and renders one Methods+Results block per outcome. Falls back to a single block\n"
    "           using the network's declared primary if no per-outcome data is present\n"
    "           (which is the current state across the portfolio's NMA apps until secondary\n"
    "           outcomes are populated into realData[*].allOutcomes[]). */\n"
    "        function generateNMAManuscriptText() {\n"
    "            const cfg = (typeof NMA_CONFIG !== 'undefined') ? NMA_CONFIG : null;\n"
    "            if (!cfg || !cfg.treatments) return;\n"
    "            const container = document.getElementById('nma-manuscript-text');\n"
    "            if (!container) return;\n"
    "\n"
    "            // Detect per-outcome data (intersection of trial.allOutcomes[] across the network).\n"
    "            // If empty, render one block for the network's declared primary outcome.\n"
    "            let outcomeKeys = [];\n"
    "            try {\n"
    "                if (typeof NMAEngine !== 'undefined' && typeof NMAEngine._getNetworkOutcomeKeys === 'function') {\n"
    "                    outcomeKeys = NMAEngine._getNetworkOutcomeKeys();\n"
    "                }\n"
    "            } catch (e) { outcomeKeys = []; }\n"
    "\n"
    "            const blocks = [];\n"
    "            if (outcomeKeys.length === 0) {\n"
    "                // Single-block mode (legacy / no per-outcome data)\n"
    "                blocks.push(_buildNMABlockForOutcome(cfg, null, null));\n"
    "            } else {\n"
    "                // Multi-outcome mode: one block per detected outcome shortLabel\n"
    "                for (const key of outcomeKeys) {\n"
    "                    const block = _buildNMABlockForOutcome(cfg, key, key);\n"
    "                    if (block) blocks.push(block);\n"
    "                }\n"
    "            }\n"
    "\n"
    "            const blockHtml = blocks.map(b =>\n"
    "                '<div class=\"mb-6\">' +\n"
    "                '<div class=\"text-[10px] font-bold text-indigo-400 uppercase tracking-widest mb-2\">Methods (estimand: ' + escapeHtml(b.outcomeLabel) + ')</div>' +\n"
    "                '<p>' + escapeHtml(b.methods) + '</p>' +\n"
    "                '</div>' +\n"
    "                '<div class=\"mb-8\">' +\n"
    "                '<div class=\"text-[10px] font-bold text-indigo-400 uppercase tracking-widest mb-2\">Results</div>' +\n"
    "                '<p>' + escapeHtml(b.results) + '</p>' +\n"
    "                '</div>'\n"
    "            ).join('<hr class=\"border-slate-800 my-6\">');\n"
    "\n"
    "            const footer = '<div class=\"text-[9px] text-slate-600 italic mt-2\">Generated by RapidMeta NMA. ' +\n"
    "                blocks.length + ' outcome' + (blocks.length !== 1 ? 's' : '') + ' detected. ' +\n"
    "                'Numbers reflect the most recent NMA run; click \"Run NMA\" again to refresh after changing trial inclusion. ' +\n"
    "                'Verify against the league table before submission.</div>';\n"
    "\n"
    "            container.innerHTML = blockHtml + footer;\n"
    "        }\n"
    "\n"
    "        function copyNMAManuscriptText() {"
)


def apply_to_file(path: pathlib.Path, dry_run: bool) -> str:
    text = path.read_text(encoding="utf-8", newline="")
    if "_getNetworkOutcomeKeys" in text:
        return f"SKIP {path.name}: already-migrated"
    if "function generateNMAManuscriptText()" not in text:
        return f"SKIP {path.name}: no NMA generator (run propagate_nma_generator.py first)"

    crlf = "\r\n" in text
    work = text.replace("\r\n", "\n") if crlf else text

    for label, old, new in (
        ("EDIT1-engine-helpers", EDIT1_OLD, EDIT1_NEW),
        ("EDIT2-getAllPairwise", EDIT2_OLD, EDIT2_NEW),
        ("EDIT3-fn-rename",      EDIT3_OLD_HEADER, EDIT3_NEW_HEADER),
        ("EDIT4-outcomeLabel",   EDIT4_OLD, EDIT4_NEW),
        ("EDIT5-outer-fn",       EDIT5_OLD, EDIT5_NEW),
    ):
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

    targets = sorted(ROOT.glob("*_NMA_REVIEW.html"))
    ok = skip = fail = 0
    for p in targets:
        result = apply_to_file(p, dry_run=args.dry_run)
        if result.startswith("OK"): ok += 1
        elif result.startswith("SKIP"): skip += 1
        else: fail += 1
        if not result.startswith("SKIP"):
            print(result)
    print(f"\nSummary: {len(targets)} files | {ok} migrate | {skip} skip | {fail} fail | mode={'dry-run' if args.dry_run else 'apply'}")
    if fail:
        sys.exit(1)


if __name__ == "__main__":
    main()
