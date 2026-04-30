/* eslint-disable */
/**
 * Unit tests for regex_helpers.js. Run with `node test_regex_helpers.js`.
 *
 * Each test asserts a property of the helper. No test framework
 * dependency -- this is a single-file harness using built-in
 * `assert.strictEqual` / `assert.ok`.
 */
const assert = require('assert');
const RX = require('./regex_helpers.js');

let passed = 0;
let failed = 0;
function test(name, fn) {
    try {
        fn();
        console.log(`  ok  ${name}`);
        passed++;
    } catch (e) {
        console.log(`  FAIL ${name}\n      ${e.message}`);
        failed++;
    }
}

// ============================================================================
// negationGuard / extractCount
// ============================================================================

test('extractCount: simple match', () => {
    const r = RX.extractCount('5050 randomized', 'randomized');
    assert.ok(r);
    assert.strictEqual(r.value, 5050);
    assert.strictEqual(r.confidence, 'MEDIUM');
});

test('extractCount: thousands comma', () => {
    const r = RX.extractCount('Total: 5,050 patients randomized to treatment', 'randomized');
    assert.ok(r);
    assert.strictEqual(r.value, 5050);
});

test('extractCount: NEGATION TRAP — Verquvo VICTORIA case', () => {
    const text = 'Of 7,061 enrolled, Not Randomized 1,807 due to ineligibility; the remaining 5,050 randomized to treatment.';
    const r = RX.extractCount(text, 'randomized');
    assert.ok(r, 'expected a match');
    assert.notStrictEqual(r.value, 1807, 'must NOT match the negated count "Not Randomized 1,807"');
    assert.strictEqual(r.value, 5050, 'must match the real value 5,050');
});

test('extractCount: negation by "excluded"', () => {
    const text = 'Excluded 234 subjects; total 1500 randomized.';
    const r = RX.extractCount(text, 'randomized');
    assert.ok(r);
    assert.strictEqual(r.value, 1500);
});

test('extractCount: n= form', () => {
    const r = RX.extractCount('Population n=204 randomized to placebo arm', 'randomized');
    assert.ok(r);
    assert.strictEqual(r.value, 204);
});

test('extractCount: returns null when no match', () => {
    const r = RX.extractCount('no relevant text here', 'randomized');
    assert.strictEqual(r, null);
});

// ============================================================================
// detectAnalyticPopulation
// ============================================================================

test('detectAnalyticPopulation: mITT explicit', () => {
    assert.strictEqual(RX.detectAnalyticPopulation('analyzed in the modified intention-to-treat population'), 'mITT');
});

test('detectAnalyticPopulation: full analysis set -> mITT', () => {
    assert.strictEqual(RX.detectAnalyticPopulation('Full Analysis Set (FAS) used for primary'), 'mITT');
});

test('detectAnalyticPopulation: per-protocol', () => {
    assert.strictEqual(RX.detectAnalyticPopulation('per-protocol analysis'), 'perProtocol');
});

test('detectAnalyticPopulation: completer', () => {
    assert.strictEqual(RX.detectAnalyticPopulation('Completer analysis at 12 weeks'), 'completer');
});

test('detectAnalyticPopulation: ITT (not modified)', () => {
    assert.strictEqual(RX.detectAnalyticPopulation('intent-to-treat analysis'), 'ITT');
});

test('detectAnalyticPopulation: unknown', () => {
    assert.strictEqual(RX.detectAnalyticPopulation('no population information'), 'unknown');
});

// ============================================================================
// detectAnalyticMethod
// ============================================================================

test('detectAnalyticMethod: MMRM', () => {
    assert.strictEqual(RX.detectAnalyticMethod('MMRM with treatment-by-time interaction'), 'MMRM');
});

test('detectAnalyticMethod: ANCOVA', () => {
    assert.strictEqual(RX.detectAnalyticMethod('analyzed by ANCOVA-adjusted change from baseline'), 'ANCOVA');
});

test('detectAnalyticMethod: LSMD', () => {
    assert.strictEqual(RX.detectAnalyticMethod('least-squares mean difference'), 'LSMD');
});

test('detectAnalyticMethod: null when none', () => {
    assert.strictEqual(RX.detectAnalyticMethod('simple t-test'), null);
});

// ============================================================================
// extractEffectAndCI
// ============================================================================

test('extractEffectAndCI: basic HR with CI', () => {
    const r = RX.extractEffectAndCI('Primary endpoint: HR 0.86 (95% CI 0.79-0.93)');
    assert.ok(r);
    assert.strictEqual(r.value, 0.86);
    assert.strictEqual(r.lci, 0.79);
    assert.strictEqual(r.uci, 0.93);
});

test('extractEffectAndCI: hazard ratio long form', () => {
    const r = RX.extractEffectAndCI('hazard ratio 0.65 (95% confidence interval 0.50, 0.85)');
    assert.ok(r);
    assert.strictEqual(r.value, 0.65);
    assert.strictEqual(r.lci, 0.50);
    assert.strictEqual(r.uci, 0.85);
});

test('extractEffectAndCI: multi-HR disambiguator picks anchor-near', () => {
    const text = 'Subgroup analysis: HR 1.20 (95% CI 0.90-1.60). Primary endpoint ACR20 at week 12: HR 4.36 (95% CI 3.45-5.50).';
    const r = RX.extractEffectAndCI(text, 'ACR20 at week 12');
    assert.ok(r);
    assert.strictEqual(r.value, 4.36, 'should pick the HR near the anchor, not the subgroup HR');
});

test('extractEffectAndCI: returns multiple matches when present', () => {
    const text = 'HR 0.86 (95% CI 0.79-0.93). Subgroup HR 0.92 (0.81-1.04).';
    const r = RX.extractEffectAndCI(text);
    assert.ok(r);
    assert.strictEqual(r.multipleMatches, true);
    assert.strictEqual(r.allMatches.length, 2);
    assert.strictEqual(r.confidence, 'LOW', 'multiple matches without anchor = LOW confidence');
});

test('extractEffectAndCI: rejects HR with bad CI bracket', () => {
    // Synthetic case where CI does not bracket point estimate
    const text = 'HR 1.50 (95% CI 0.10-0.20)'; // 1.50 not in [0.10, 0.20]
    const r = RX.extractEffectAndCI(text);
    assert.strictEqual(r, null, 'should reject when CI does not bracket the point');
});

test('extractEffectAndCI: returns null when no match', () => {
    assert.strictEqual(RX.extractEffectAndCI('no HR here'), null);
});

// ============================================================================
// screenForApostrophe
// ============================================================================

test('screenForApostrophe: passes safe string', () => {
    const safe = 'the trial-published primary analytic method';
    assert.strictEqual(RX.screenForApostrophe(safe, 'test'), safe);
});

test('screenForApostrophe: passes already-escaped apostrophe', () => {
    const escaped = "O\\'Brien et al";
    assert.strictEqual(RX.screenForApostrophe(escaped, 'test'), escaped);
});

test('screenForApostrophe: REJECTS unescaped apostrophe (the trap)', () => {
    let threw = false;
    try {
        RX.screenForApostrophe("each trial's published primary", 'test');
    } catch (e) {
        threw = true;
        assert.ok(/Apostrophe trap/.test(e.message), 'error must mention Apostrophe trap');
    }
    assert.ok(threw, 'screenForApostrophe must throw on bare apostrophe');
});

// ============================================================================
console.log(`\n${passed} passed, ${failed} failed`);
process.exit(failed === 0 ? 0 : 1);
