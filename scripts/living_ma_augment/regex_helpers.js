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
        // GAP CLASS = [^\d,.;:\n] (NOT [\w\s]). This is the key anti-fabrication
        // guard: the run of text between the number and the keyword may NOT
        // contain another DIGIT (so a match can never leap OVER an intervening
        // number to grab an unrelated one — "1234 screened then 567 randomized"
        // must yield 567, never 1234), and may not cross a comma or a
        // sentence/clause boundary (`. ; :` newline) — which preserves the
        // Verquvo VICTORIA negation behaviour ("Of 7,061 enrolled, Not
        // Randomized 1,807 ... 5,050 randomized" -> 5,050, the comma after
        // "enrolled" blocks 7,061 from pairing with the keyword).
        const GAP = '[^\\d,.;:\\n]{0,40}?';
        // number is capture group 1 in every pattern. `gapGroup` (when present)
        // is the inter-token gap, used for confidence calibration.
        const patterns = [
            // n = 5050 [words] randomized        (tight: explicit n= anchor)
            { re: new RegExp(`\\bn\\s*=\\s*([\\d,]+)${GAP}${kw}`, 'gi'), tight: true },
            // 5050 [words] randomized            (loose: distance-based)
            { re: new RegExp(`([\\d,]+)(${GAP})${kw}`, 'gi'), tight: false, gapGroup: 2 },
            // randomized: 5050  |  randomized 5050 (tight: keyword-adjacent)
            { re: new RegExp(`${kw}\\s*[:=]?\\s*([\\d,]+)`, 'gi'), tight: true },
        ];
        for (const p of patterns) {
            let m;
            while ((m = p.re.exec(text)) !== null) {
                const numStr = m[1];
                const numPos = m.index + m[0].indexOf(numStr);
                if (!negationGuard(text, numPos)) continue;
                const value = parseInt(numStr.replace(/,/g, ''), 10);
                if (!Number.isFinite(value) || value <= 0) continue;
                let confidence = 'MEDIUM';
                const flags = { negationChecked: true };
                // A long, multi-word gap means the number is only loosely bound
                // to the keyword -> downgrade so the user reviews the pick.
                if (p.gapGroup) {
                    const gapWords = ((m[p.gapGroup] || '').match(/\b\w+\b/g) || []).length;
                    if (gapWords > 3) { confidence = 'LOW'; flags.looseGap = true; }
                }
                // Year-range number preceded by a temporal preposition is more
                // likely a publication/start YEAR than a patient count -> LOW
                // (don't drop it; let the user confirm — "better to ask").
                if (value >= 1900 && value <= 2100) {
                    const before = text.slice(Math.max(0, numPos - 12), numPos);
                    if (/\b(in|by|since|during|year|of)\s*$/i.test(before)) {
                        confidence = 'LOW';
                        flags.yearAmbiguous = true;
                    }
                }
                const sourceStart = Math.max(0, numPos - 40);
                const sourceEnd = Math.min(text.length, numPos + 60);
                return {
                    value,
                    confidence,
                    source: text.slice(sourceStart, sourceEnd).trim(),
                    ...flags,
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
            if (!(lci < uci)) continue;           // reject degenerate/zero-width or inverted CI (lci must be < uci)
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
