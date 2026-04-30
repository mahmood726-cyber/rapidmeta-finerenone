/* eslint-disable */
/**
 * Living-MA augment: defensive regex helpers.
 *
 * Pure functions only -- no DOM, no fetch, no state. Each helper
 * returns { value, confidence, source } so the caller (validation
 * modal) can show the source snippet next to the auto-extracted
 * value.
 *
 * Confidence levels:
 *   "HIGH"   - structural CT.gov field; user trusts but verifies
 *   "MEDIUM" - regex match passing a defensive guard; user reviews
 *   "LOW"    - regex match with no guard, OR fallback from a miss
 *   "NONE"   - field not extractable, user must enter manually
 *
 * Guards encoded here come from `~/.claude/rules/lessons.md`:
 *   - 30-char negation lookbehind on counts (Verquvo VICTORIA EPAR)
 *   - mITT phrase preference for denominators
 *   - multi-HR disambiguator by primary-endpoint anchor proximity
 *   - LSMD/MMRM detector for continuous outcomes
 *   - apostrophe screen for any string injected into JS literals
 *
 * Tests: see scripts/living_ma_augment/regex_helpers.test.html.
 */
(function (root) {
    'use strict';

    const NEGATION_TOKENS = /\b(not|non|never|excluded?|withdrawn|withdrew)\b/i;

    /**
     * Negation lookbehind: a regex match for "<keyword> <number>" or
     * "<number> <keyword>" must NOT have a negation word in the
     * IMMEDIATE preceding clause (stops at `;` `.` `\n` to avoid
     * cross-sentence false positives).
     *
     * Returns false if the match should be DROPPED (negation found),
     * true if the match is safe to keep.
     *
     * Source incident (lessons.md 2026-04-15): DossierGap Verquvo
     * VICTORIA EPAR — "Not Randomized 1,807" was extracted where the
     * real value was 5,050 (in a different sentence).
     */
    function negationGuard(text, matchStartIndex) {
        const start = Math.max(0, matchStartIndex - 30);
        let window = text.slice(start, matchStartIndex);
        // Stop at the most recent sentence/clause boundary so a
        // benign "Excluded 234 subjects; total 1500 randomized."
        // doesn't false-flag the post-semicolon number.
        const lastBoundary = Math.max(
            window.lastIndexOf('. '),
            window.lastIndexOf('; '),
            window.lastIndexOf('\n'),
        );
        if (lastBoundary >= 0) {
            window = window.slice(lastBoundary + 1);
        }
        return !NEGATION_TOKENS.test(window);
    }

    /**
     * mITT detector: scan a window of text for analytic-population
     * declaration. Returns one of "mITT" / "ITT" / "completer" /
     * "perProtocol" / "unknown".
     */
    function detectAnalyticPopulation(text) {
        const t = (text || '').toLowerCase();
        // "intent" / "intention" both common in literature.
        if (/(modified intent(?:ion)?[\- ]to[\- ]treat|modified itt|m\s*itt)/.test(t)) return 'mITT';
        if (/(full analysis set|fas\b)/.test(t)) return 'mITT';
        if (/(intent(?:ion)?[\- ]to[\- ]treat|itt analysis|by itt|on itt|itt population)/.test(t)) return 'ITT';
        if (/(per[\- ]protocol|pp population|pp analysis)/.test(t)) return 'perProtocol';
        if (/(completer|completed analysis|observed[\- ]case)/.test(t)) return 'completer';
        return 'unknown';
    }

    /**
     * LSMD/MMRM/ANCOVA detector: returns the named method if a
     * known phrase appears, else null.
     */
    function detectAnalyticMethod(text) {
        const t = (text || '').toLowerCase();
        if (/\bmmrm\b|mixed[\- ]?effect[s]? model[s]? for repeated|repeated[\- ]measures?/.test(t)) return 'MMRM';
        if (/\bancova\b|analysis of covariance/.test(t)) return 'ANCOVA';
        if (/\blsmd\b|least[\- ]squares? mean|ls[\- ]?mean/.test(t)) return 'LSMD';
        return null;
    }

    /**
     * Number extraction with negation guard. Matches:
     *   "<number> <kw>"   e.g. "1807 randomized"
     *   "<kw>: <number>"  e.g. "randomized: 5050"
     *   "n=<number>"      e.g. "n=5050"
     * with optional thousands commas (1,807). Returns null if the
     * negation guard rejects the match.
     */
    function extractCount(text, keyword) {
        if (!text) return null;
        const kw = keyword.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
        // Build patterns. /g flag so we can iterate over multiple
        // candidates; first that passes the negation guard wins.
        // Patterns tolerate up to ~3 short words between number and
        // keyword (e.g. "5,050 patients randomized") via [\w\s]{0,40}?.
        const patterns = [
            // n = 5050 [optional words] randomized
            new RegExp(`\\b(n\\s*=\\s*)([\\d,]+)[\\w\\s]{0,40}?${kw}`, 'gi'),
            // 5050 [optional words] randomized
            new RegExp(`([\\d,]+)[\\w\\s]{0,40}?${kw}`, 'gi'),
            // randomized: 5050  |  randomized 5050
            new RegExp(`${kw}\\s*[:=]?\\s*([\\d,]+)`, 'gi'),
        ];
        for (const re of patterns) {
            let m;
            while ((m = re.exec(text)) !== null) {
                const numStr = m[m.length - 1];
                const numPos = text.indexOf(numStr, m.index);
                if (!negationGuard(text, numPos)) continue;
                const value = parseInt(numStr.replace(/,/g, ''), 10);
                if (!Number.isFinite(value)) continue;
                const sourceStart = Math.max(0, numPos - 40);
                const sourceEnd = Math.min(text.length, numPos + 60);
                return {
                    value,
                    confidence: 'MEDIUM',
                    source: text.slice(sourceStart, sourceEnd).trim(),
                    negationChecked: true,
                };
            }
        }
        return null;
    }

    /**
     * HR/RR/OR with 95% CI from text.
     *
     * Multi-HR disambiguator: if `endpointAnchor` is provided
     * (e.g. "ACR20 at week 12" or "primary endpoint"), prefer
     * matches within ANCHOR_WINDOW chars of the anchor. Falls back
     * to the first match if no anchor or no anchor-near match.
     */
    const ANCHOR_WINDOW = 200;
    function extractEffectAndCI(text, endpointAnchor) {
        if (!text) return null;
        // Robust HR/RR/OR + 95% CI matcher.
        // Examples it covers:
        //   HR 0.86 (95% CI 0.79-0.93)
        //   HR=0.86, 95% CI 0.79 to 0.93
        //   hazard ratio 0.86 (0.79-0.93)
        //   relative risk 1.62 (95% confidence interval 1.38, 1.91)
        const re = /(hazard ratio|relative risk|risk ratio|odds ratio|HR|RR|OR)\s*[=:]?\s*([0-9]+\.?[0-9]*)\s*[\(,;\s]*\s*(?:95\s*%\s*(?:CI|confidence interval)\s*[=:]?\s*)?\s*([0-9]+\.?[0-9]*)\s*(?:[-–to,]+)\s*([0-9]+\.?[0-9]*)/gi;
        const matches = [];
        let m;
        while ((m = re.exec(text)) !== null) {
            const eff = parseFloat(m[2]);
            const lci = parseFloat(m[3]);
            const uci = parseFloat(m[4]);
            if (!Number.isFinite(eff) || !Number.isFinite(lci) || !Number.isFinite(uci)) continue;
            if (lci > eff || uci < eff) continue; // sanity: CI must bracket point estimate
            matches.push({
                kind: m[1],
                value: eff,
                lci,
                uci,
                index: m.index,
                snippet: text.slice(Math.max(0, m.index - 30), Math.min(text.length, m.index + 100)).trim(),
            });
        }
        if (matches.length === 0) return null;

        // Multi-HR disambiguation: prefer matches near the anchor.
        let chosen = matches[0];
        if (endpointAnchor) {
            const anchorIdx = text.toLowerCase().indexOf(endpointAnchor.toLowerCase());
            if (anchorIdx >= 0) {
                let bestDist = Infinity;
                for (const cand of matches) {
                    const dist = Math.abs(cand.index - anchorIdx);
                    if (dist < bestDist && dist <= ANCHOR_WINDOW) {
                        bestDist = dist;
                        chosen = cand;
                    }
                }
            }
        }

        return {
            value: chosen.value,
            lci: chosen.lci,
            uci: chosen.uci,
            kind: chosen.kind,
            confidence: matches.length === 1 ? 'MEDIUM' : 'LOW', // LOW if multiple; user must verify pick
            source: chosen.snippet,
            multipleMatches: matches.length > 1,
            allMatches: matches.map(c => ({ value: c.value, lci: c.lci, uci: c.uci, kind: c.kind, snippet: c.snippet })),
        };
    }

    /**
     * Apostrophe screen. ANY string that will be injected into a JS
     * single-quoted literal MUST pass this. Returns the input
     * unchanged if safe; throws if an unescaped apostrophe is
     * detected.
     *
     * Per lessons.md 2026-04-30: literal apostrophe inside `'...'`
     * terminates the string and breaks parsing. The
     * add_lsmd_disclaimer.py incident broke 27 dashboards this way.
     */
    function screenForApostrophe(s, fieldName) {
        if (typeof s !== 'string') return s;
        // Allow already-escaped \' but flag bare '
        // Strategy: replace \' with a placeholder, then check for ',
        // then restore.
        const placeholder = ' ESCAPED_APOS ';
        const cleaned = s.replace(/\\'/g, placeholder);
        if (cleaned.indexOf("'") >= 0) {
            throw new Error(
                `Apostrophe trap: unescaped \' in ${fieldName || 'string'} ` +
                `would break a JS single-quoted literal. ` +
                `Either escape as \\' OR rephrase to avoid possessive. ` +
                `Value: ${JSON.stringify(s.slice(0, 80))}`
            );
        }
        return s;
    }

    // ---- public API ----
    const api = {
        negationGuard,
        detectAnalyticPopulation,
        detectAnalyticMethod,
        extractCount,
        extractEffectAndCI,
        screenForApostrophe,
    };

    if (typeof module !== 'undefined' && module.exports) {
        module.exports = api;
    } else {
        root.LivingMARegex = api;
    }
})(typeof window !== 'undefined' ? window : globalThis);
