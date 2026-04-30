/* eslint-disable */
/**
 * Unit tests for pubmed_fetch.js parseEfetchXml (pure function).
 * Run: node test_pubmed_fetch.js.
 */
const assert = require('assert');

global.localStorage = { getItem: () => null, setItem: () => {}, removeItem: () => {} };
global.fetch = () => { throw new Error('fetch not stubbed'); };
global.crypto = { subtle: { digest: async () => new ArrayBuffer(32) } };

const PM = require('./pubmed_fetch.js');

let passed = 0, failed = 0;
function test(name, fn) {
    try { fn(); console.log(`  ok  ${name}`); passed++; }
    catch (e) { console.log(`  FAIL ${name}\n      ${e.message}`); failed++; }
}

test('parseEfetchXml: single AbstractText', () => {
    const xml = `<?xml version="1.0"?>
<PubmedArticleSet>
<PubmedArticle><MedlineCitation><Article>
<ArticleTitle>A trial of TestDrug</ArticleTitle>
<Abstract><AbstractText>This is the abstract.</AbstractText></Abstract>
</Article></MedlineCitation></PubmedArticle>
</PubmedArticleSet>`;
    const r = PM.parseEfetchXml(xml);
    assert.strictEqual(r.title, 'A trial of TestDrug');
    assert.strictEqual(r.abstract, 'This is the abstract.');
});

test('parseEfetchXml: structured abstract with labels', () => {
    const xml = `<Article>
<ArticleTitle>Phase 3 of TestDrug in MACE</ArticleTitle>
<Abstract>
<AbstractText Label="BACKGROUND">Background text.</AbstractText>
<AbstractText Label="METHODS">Methods text.</AbstractText>
<AbstractText Label="RESULTS">HR 0.86 (95% CI 0.79-0.93)</AbstractText>
<AbstractText Label="CONCLUSIONS">Conclusion text.</AbstractText>
</Abstract>
</Article>`;
    const r = PM.parseEfetchXml(xml);
    assert.strictEqual(r.title, 'Phase 3 of TestDrug in MACE');
    assert.ok(r.abstract.includes('BACKGROUND: Background text.'));
    assert.ok(r.abstract.includes('METHODS: Methods text.'));
    assert.ok(r.abstract.includes('RESULTS: HR 0.86 (95% CI 0.79-0.93)'));
    assert.ok(r.abstract.includes('CONCLUSIONS: Conclusion text.'));
});

test('parseEfetchXml: missing abstract returns empty string (no throw)', () => {
    const xml = `<Article><ArticleTitle>No-abstract paper</ArticleTitle></Article>`;
    const r = PM.parseEfetchXml(xml);
    assert.strictEqual(r.title, 'No-abstract paper');
    assert.strictEqual(r.abstract, '');
});

test('parseEfetchXml: empty input does not throw', () => {
    const r = PM.parseEfetchXml('');
    assert.strictEqual(r.title, '');
    assert.strictEqual(r.abstract, '');
});

test('parseEfetchXml: handles inline tags within AbstractText', () => {
    const xml = `<Article>
<ArticleTitle>Inline tags</ArticleTitle>
<Abstract><AbstractText>Result was <i>significant</i> at <b>p</b>&lt;0.001.</AbstractText></Abstract>
</Article>`;
    const r = PM.parseEfetchXml(xml);
    assert.ok(/significant/.test(r.abstract));
    assert.ok(!/<i>|<b>/.test(r.abstract), 'should strip inline HTML/XML tags');
});

console.log(`\n${passed} passed, ${failed} failed`);
process.exit(failed === 0 ? 0 : 1);
