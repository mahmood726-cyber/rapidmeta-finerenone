// sentinel:skip-file
// Real browser fixtures test execution/readiness; they are not scientific inputs.
import { before, after, test } from 'node:test';
import assert from 'node:assert/strict';
import { createServer } from 'node:http';
import { chromium } from 'playwright';
import { harvestPage } from '../scripts/workflow/harvest_findings.mjs';

let browser, server, base, retryRequests = 0;
const timers = [];
const finding = { editor: { decision: 'Accept' }, reviewers: [{ role: 'Methods', concerns: ['fixture concern, unchanged'] }] };
const runtime = `window.RapidMeta = {state:{results:null},runPeerReview:()=>(${JSON.stringify(finding)})};
window.AnalysisEngine = {run:()=>{window.RapidMeta.state.results={k:3,or:'0.9',nnt:0,absoluteRisk:0,totalAvailable:0}}};`;

before(async () => {
    server = createServer((req, res) => {
        if (req.url === '/long-poll') { res.writeHead(200); res.write('pending'); return; }
        res.setHeader('Content-Type', 'text/html');
        const page = code => res.end(`<!doctype html><html><body><script>${code}</script></body></html>`);
        switch (req.url) {
            case '/A_REVIEW.html': page(`fetch('/long-poll');setTimeout(()=>{${runtime}},30);`); break;
            case '/RETRY_REVIEW.html':
                retryRequests++;
                if (retryRequests === 1) timers.push(setTimeout(() => page(runtime), 500));
                else page(runtime);
                break;
            case '/NO_RUNTIME_REVIEW.html': page('throw new Error("fixture script failure")'); break;
            case '/NO_ANALYSIS_REVIEW.html': page('window.RapidMeta={state:{results:null},runPeerReview:()=>null};'); break;
            case '/NO_REVIEW_REVIEW.html': page(runtime + 'delete window.RapidMeta.runPeerReview;'); break;
            case '/THROW_REVIEW.html': page(runtime + 'window.RapidMeta.runPeerReview=()=>{throw new Error("fixture reviewer failure")};'); break;
            case '/MALFORMED_REVIEW.html': page(runtime + 'window.RapidMeta.runPeerReview=()=>["unexpected"]'); break;
            default: res.writeHead(404); res.end('missing');
        }
    });
    await new Promise(resolve => server.listen(0, '127.0.0.1', resolve));
    base = `http://127.0.0.1:${server.address().port}/`;
    browser = await chromium.launch(process.env.HARVEST_TEST_CHROME ? {
        executablePath: process.env.HARVEST_TEST_CHROME,
        args: ['--no-sandbox', '--disable-dev-shm-usage', '--disable-gpu'],
    } : {});
});

after(async () => {
    for (const timer of timers) clearTimeout(timer);
    if (browser) await browser.close();
    if (server) {
        server.closeAllConnections();
        await new Promise(resolve => server.close(resolve));
    }
});

test('delayed runtime and persistent network traffic harvest without networkidle', async () => {
    const result = await harvestPage(browser, 'A_REVIEW.html', { base, readinessTimeoutMs: 1000 });
    assert.equal(result.status, 'ok');
    assert.deepEqual(result.findings, finding);
    assert.equal(result.state.nnt, 0);
    assert.equal(result.state.absoluteRisk, 0);
    assert.equal(result.state.totalAvailable, 0);
});

test('real navigation timeout retries and retains both attempts', async () => {
    const result = await harvestPage(browser, 'RETRY_REVIEW.html', { base, navigationTimeoutMs: 150, readinessTimeoutMs: 1000 });
    assert.equal(result.status, 'ok');
    assert.equal(result.attempts.length, 2);
    assert.equal(result.attempts[0].phase, 'navigation');
    assert.match(result.attempts[0].error, /Timeout/);
});

test('missing runtime has bounded timeout, failing script diagnostics and no findings', async () => {
    const result = await harvestPage(browser, 'NO_RUNTIME_REVIEW.html', { base, readinessTimeoutMs: 80 });
    assert.equal(result.status, 'failed');
    assert.equal(result.attempts.length, 2);
    assert.equal(result.attempts[1].runtime.hasRapidMeta, false);
    assert.ok(result.attempts[1].pageErrors.some(error => /fixture script failure/.test(error)));
    assert.equal(result.findings, null);
});

test('no real analysis is explicitly skipped without fabricated state', async () => {
    const result = await harvestPage(browser, 'NO_ANALYSIS_REVIEW.html', { base, readinessTimeoutMs: 80 });
    assert.equal(result.status, 'skipped');
    assert.equal(result.reason, 'no-populated-analysis-results');
    assert.equal(result.findings, null);
    assert.equal(result.state, null);
});

test('missing review API is explicitly skipped', async () => {
    const result = await harvestPage(browser, 'NO_REVIEW_REVIEW.html', { base, readinessTimeoutMs: 80 });
    assert.equal(result.status, 'skipped');
    assert.equal(result.reason, 'peer-review-api-unavailable');
});

test('reviewer exceptions and malformed outputs fail without reporting empty concerns', async () => {
    for (const app of ['THROW_REVIEW.html', 'MALFORMED_REVIEW.html']) {
        const result = await harvestPage(browser, app, { base, readinessTimeoutMs: 1000 });
        assert.equal(result.status, 'failed');
        assert.equal(result.attempts.length, 1);
        assert.equal(result.phase, 'peer-review');
        assert.match(result.error, /fixture reviewer failure|Invalid peer-review output/);
    }
});

test('missing HTTP page is a failure with its status preserved', async () => {
    const result = await harvestPage(browser, 'MISSING_REVIEW.html', { base });
    assert.equal(result.status, 'failed');
    assert.match(result.error, /HTTP 404/);
    assert.equal(result.attempts[0].httpErrors[0].status, 404);
});
