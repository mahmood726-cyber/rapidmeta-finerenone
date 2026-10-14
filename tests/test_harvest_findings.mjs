// sentinel:skip-file
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { mkdtempSync, writeFileSync, readFileSync, rmSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { harvestPage, runHarvest, summarize, unsupportedReason, validateFindings } from '../scripts/workflow/harvest_findings.mjs';

const findings = { editor: { decision: 'Minor revision' }, reviewers: [{ role: 'Methods', concerns: ['unaltered concern'] }] };
const timeout = () => Object.assign(new Error('fixture timeout'), { name: 'TimeoutError' });

function fakePage({ navigationError, readinessError, analysisError, peerError, peerOutput = findings } = {}) {
    const calls = { waits: [], navigation: null, closed: false };
    const page = {
        calls, on() {}, url: () => 'http://localhost:8080/A_REVIEW.html',
        async goto(url, options) {
            calls.navigation = { url, options };
            if (navigationError) throw navigationError;
            return { ok: () => true, status: () => 200 };
        },
        async waitForFunction(fn, arg, options) {
            calls.waits.push({ arg, options });
            if (readinessError) throw readinessError;
        },
        async evaluate(fn) {
            const text = fn.toString();
            if (text.includes('readyState')) return { hasRapidMeta: true };
            if (text.includes('runPeerReview()')) { if (peerError) throw peerError; return peerOutput; }
            if (text.includes('AnalysisEngine.run()')) { if (analysisError) throw analysisError; return; }
            return { k: 3, or: '0.9', nnt: 0, absoluteRisk: 0 };
        },
        async close() { calls.closed = true; },
    };
    return page;
}

test('successful harvest preserves reviewer strings and passes actual timeout options', async () => {
    const page = fakePage();
    const result = await harvestPage({ newPage: async () => page }, 'A_REVIEW.html', { readinessTimeoutMs: 123 });
    assert.equal(result.status, 'ok');
    assert.deepEqual(result.findings, findings);
    assert.equal(page.calls.navigation.options.waitUntil, 'domcontentloaded');
    assert.equal(page.calls.waits.length, 3);
    for (const call of page.calls.waits) {
        assert.equal(call.arg, null);
        assert.equal(call.options.timeout, 123);
    }
    assert.equal(page.calls.closed, true);
});

test('navigation timeout retries in a fresh page and retains the failed attempt', async () => {
    const first = fakePage({ navigationError: timeout() }), second = fakePage();
    const pages = [first, second];
    const result = await harvestPage({ newPage: async () => pages.shift() }, 'A_REVIEW.html');
    assert.equal(result.status, 'ok');
    assert.equal(result.attempts.length, 2);
    assert.equal(result.attempts[0].phase, 'navigation');
    assert.match(result.attempts[0].error, /fixture timeout/);
    assert.equal(first.calls.closed, true);
    assert.equal(second.calls.closed, true);
});

test('persistent runtime timeout is bounded and retains diagnostics', async () => {
    let pages = 0;
    const result = await harvestPage({ newPage: async () => { pages++; return fakePage({ readinessError: timeout() }); } }, 'A_REVIEW.html');
    assert.equal(pages, 2);
    assert.equal(result.status, 'failed');
    assert.equal(result.phase, 'runtime-readiness');
    assert.equal(result.attempts.length, 2);
    assert.equal(result.attempts[1].runtime.hasRapidMeta, true);
});

test('analysis or peer-review exceptions fail instead of becoming skipped or empty reviews', async () => {
    for (const option of ['analysisError', 'peerError']) {
        let pages = 0;
        const result = await harvestPage({ newPage: async () => { pages++; return fakePage({ [option]: new Error('real failure') }); } }, 'A_REVIEW.html');
        assert.equal(result.status, 'failed');
        assert.match(result.error, /real failure/);
        assert.equal(pages, 1);
    }
});

test('malformed findings fail visibly', async () => {
    const result = await harvestPage({ newPage: async () => fakePage({ peerOutput: ['unexpected'] }) }, 'A_REVIEW.html');
    assert.equal(result.status, 'failed');
    assert.match(result.error, /Invalid peer-review output/);
    for (const value of [null, [], { editor: { decision: 'Accept' }, reviewers: [{ role: 'M' }] }]) {
        assert.throws(() => validateFindings(value), /Invalid peer-review output/);
    }
});

test('explicit unsupported formats have a reason and are never counted as success', async () => {
    for (const source of [
        '<meta name="rm-orphan-redirect" content="A_REVIEW.html">',
        '<html data-store="ssot/a.json" data-artefact="review">',
        '<script src="rapidmeta-dose-response-engine-v1.js"></script>',
    ]) {
        const result = await harvestPage({ newPage: () => { throw new Error('must not launch for known unsupported format'); } }, 'A_REVIEW.html', { source });
        assert.equal(result.status, 'skipped');
        assert.equal(result.reason, unsupportedReason(source));
        assert.equal(summarize([result], 'full', 'finished').complete, false);
    }
    assert.equal(unsupportedReason('<html data-store="s"><script>window.RapidMeta = {};</script>'), null);
});

test('subset, empty, skipped, failed and pending harvests cannot be complete', () => {
    assert.equal(summarize([{ status: 'ok' }], 'full', 'finished').complete, true);
    assert.equal(summarize([{ status: 'ok' }], 'subset', 'finished').complete, false);
    assert.equal(summarize([{ status: 'ok' }], 'full', null).complete, false);
    assert.equal(summarize([], 'full', 'finished').complete, false);
    for (const status of ['skipped', 'failed', 'pending']) assert.equal(summarize([{ status: 'ok' }, { status }], 'full', 'finished').complete, false);
});

test('manifest and page records preserve exact successful, skipped and failed counts', async () => {
    const root = mkdtempSync(join(tmpdir(), 'harvest-test-'));
    try {
        const apps = ['A_REVIEW.html', 'B_REVIEW.html', 'C_REVIEW.html'];
        writeFileSync(join(root, apps[0]), '<html>');
        writeFileSync(join(root, apps[1]), '<html>');
        writeFileSync(join(root, apps[2]), '<html data-store="ssot/c.json">');
        const pages = [fakePage(), fakePage({ peerError: new Error('review error') })];
        pages[1].url = () => 'http://localhost:8080/B_REVIEW.html';
        const outDir = join(root, 'run');
        const manifest = await runHarvest({ apps, outDir, base: 'http://localhost:8080/', sourceRoot: root,
            browserFactory: async () => ({ newPage: async () => pages.shift(), close: async () => {} }) });
        assert.deepEqual([manifest.ok, manifest.skipped, manifest.failed, manifest.pending], [1, 1, 1, 0]);
        assert.equal(manifest.complete, false);
        assert.deepEqual(JSON.parse(readFileSync(join(outDir, '_harvest.json'))), JSON.parse(JSON.stringify(manifest)));
        assert.deepEqual(JSON.parse(readFileSync(join(outDir, 'A_REVIEW.json'))).findings, findings);
        await assert.rejects(runHarvest({ apps, outDir }), /Refusing to overwrite/);
        await assert.rejects(runHarvest({ apps, outDir: 'findings' }), /isolated run directory/);
    } finally { rmSync(root, { recursive: true, force: true }); }
});

test('browser launch failure leaves an incomplete manifest with all pages pending', async () => {
    const root = mkdtempSync(join(tmpdir(), 'harvest-fatal-'));
    try {
        await assert.rejects(runHarvest({ apps: ['A_REVIEW.html'], outDir: join(root, 'run'), base: 'http://localhost/',
            browserFactory: async () => { throw new Error('browser unavailable'); } }), /browser unavailable/);
        const manifest = JSON.parse(readFileSync(join(root, 'run', '_harvest.json')));
        assert.equal(manifest.complete, false);
        assert.equal(manifest.pending, 1);
        assert.match(manifest.fatalError, /browser unavailable/);
    } finally { rmSync(root, { recursive: true, force: true }); }
});
