// sentinel:skip-file
// Harvest real peer-review outputs. Every discovered page has an auditable outcome.
import { readdirSync, readFileSync, writeFileSync, mkdirSync, existsSync, renameSync } from 'node:fs';
import { join, resolve } from 'node:path';
import { pathToFileURL } from 'node:url';

export function unsupportedReason(source) {
    if (/<meta\b[^>]*name=["']rm-orphan-redirect["']/i.test(source)) return 'redirect-to-canonical-review';
    // These explicit formats do not provide the legacy RapidMeta peer-review API.
    if (/<html\b[^>]*data-store=/i.test(source) && !/window\.RapidMeta\s*=|(?:const|let|var)\s+RapidMeta\s*=/.test(source)) return 'static-store-review-no-peer-review-api';
    if (/src=["'][^"']*rapidmeta-dose-response-engine-v1\.js/.test(source) && !/window\.RapidMeta\s*=|(?:const|let|var)\s+RapidMeta\s*=/.test(source)) return 'dose-response-review-no-peer-review-api';
    return null;
}

export function validateFindings(findings) {
    if (!findings || typeof findings !== 'object' || Array.isArray(findings) ||
        !findings.editor || typeof findings.editor.decision !== 'string' || !findings.editor.decision ||
        !Array.isArray(findings.reviewers)) throw new Error('Invalid peer-review output: expected editor.decision and reviewers array');
    for (const [i, rv] of findings.reviewers.entries()) {
        if (!rv || typeof rv.role !== 'string' || !rv.role || !Array.isArray(rv.concerns) ||
            rv.concerns.some(c => typeof c !== 'string')) throw new Error(`Invalid peer-review output: reviewers[${i}] requires role and concerns string array`);
    }
    return findings;
}

async function diagnostics(page, captured) {
    const result = { ...captured, url: page?.url() || null };
    if (page) {
        try {
            result.runtime = await page.evaluate(() => ({
                readyState: document.readyState,
                hasRapidMeta: !!window.RapidMeta,
                hasAnalysis: typeof window.AnalysisEngine?.run === 'function',
                hasPeerReview: typeof window.RapidMeta?.runPeerReview === 'function',
                hasResults: !!window.RapidMeta?.state?.results,
            }));
        } catch (error) { result.diagnosticError = String(error); }
    }
    return result;
}

export async function harvestPage(browser, app, options = {}) {
    const { base = 'http://localhost:8080/', navigationTimeoutMs = 30000, readinessTimeoutMs = 15000,
        maxAttempts = 2, source = '' } = options;
    const start = Date.now();
    const attempts = [];
    const reason = unsupportedReason(source);
    const record = { app, timestamp: new Date().toISOString(), state: null, findings: null, attempts };
    if (reason) return { ...record, status: 'skipped', reason, durationMs: Date.now() - start };
    for (let attempt = 1; attempt <= maxAttempts; attempt++) {
        let page;
        let phase = 'browser-page';
        const captured = { pageErrors: [], requestFailures: [], httpErrors: [] };
        try {
            page = await browser.newPage();
            page.on('pageerror', error => captured.pageErrors.push(String(error)));
            page.on('requestfailed', request => captured.requestFailures.push({ url: request.url(), error: request.failure()?.errorText }));
            page.on('response', response => { if (response.status() >= 400) captured.httpErrors.push({ url: response.url(), status: response.status() }); });
            phase = 'navigation';
            const response = await page.goto(new URL(app, base).href, { waitUntil: 'domcontentloaded', timeout: navigationTimeoutMs });
            if (!response || !response.ok()) throw new Error(`Review page HTTP ${response?.status() ?? 'no-response'}`);
            if (new URL(page.url()).pathname !== new URL(app, base).pathname) {
                attempts.push({ attempt, phase, ...await diagnostics(page, captured) });
                return { ...record, status: 'skipped', reason: 'redirected-page-not-reviewed-under-alias', durationMs: Date.now() - start };
            }
            phase = 'runtime-readiness';
            // Playwright's options are the THIRD argument; the old second-argument
            // timeout was an evaluation argument and left the default 30s in force.
            await page.waitForFunction(() => window.RapidMeta != null, null, { timeout: readinessTimeoutMs });
            phase = 'analysis';
            await page.evaluate(async () => {
                if (typeof window.AnalysisEngine?.run === 'function') await window.AnalysisEngine.run();
            });
            phase = 'analysis-readiness';
            try {
                await page.waitForFunction(() => {
                    const r = window.RapidMeta?.state?.results;
                    return r && r.or != null && r.or !== '--';
                }, null, { timeout: readinessTimeoutMs });
            } catch (error) {
                if (error.name !== 'TimeoutError') throw error;
                attempts.push({ attempt, phase, error: String(error), ...await diagnostics(page, captured) });
                return { ...record, status: 'skipped', reason: 'no-populated-analysis-results', durationMs: Date.now() - start };
            }
            phase = 'peer-review-readiness';
            try {
                await page.waitForFunction(() => typeof window.RapidMeta?.runPeerReview === 'function', null, { timeout: readinessTimeoutMs });
            } catch (error) {
                if (error.name !== 'TimeoutError') throw error;
                attempts.push({ attempt, phase, error: String(error), ...await diagnostics(page, captured) });
                return { ...record, status: 'skipped', reason: 'peer-review-api-unavailable', durationMs: Date.now() - start };
            }
            phase = 'peer-review';
            const findings = await page.evaluate(async () => await window.RapidMeta.runPeerReview());
            validateFindings(findings); // malformed outputs and reviewer exceptions are failures, never empty reviews
            phase = 'state-capture';
            record.state = await page.evaluate(() => {
                const r = window.RapidMeta.state.results;
                return {
                    k: r.k, or: r.or, i2: r.i2, tau2: r.tau2, grade: r.gradeCertainty,
                    remlSensitivity: !!r.remlSensitivity, robSummary: r.robSummary ?? null,
                    isCompleteUniverse: r.isCompleteUniverse ?? false,
                    totalAvailable: r.totalAvailable ?? null, includedCount: r.includedCount ?? null,
                    searchResultCount: r.searchResultCount ?? null, nnt: r.nnt ?? null,
                    absoluteRisk: r.absoluteRisk ?? null, patientReportedOutcomes: r.patientReportedOutcomes ?? null,
                };
            });
            attempts.push({ attempt, phase: 'complete', ...await diagnostics(page, captured) });
            return { ...record, status: 'ok', findings, durationMs: Date.now() - start };
        } catch (error) {
            attempts.push({ attempt, phase, error: String(error), ...await diagnostics(page, captured) });
            const retry = error.name === 'TimeoutError' && ['navigation', 'runtime-readiness'].includes(phase) && attempt < maxAttempts;
            if (!retry) return { ...record, status: 'failed', error: String(error), phase, durationMs: Date.now() - start };
        } finally {
            if (page) await page.close();
        }
    }
}

export function summarize(pages, scope, finishedAt) {
    const counts = { total: pages.length, ok: 0, skipped: 0, failed: 0, pending: 0 };
    for (const page of pages) {
        if (!Object.hasOwn(counts, page.status) || page.status === 'total') throw new Error(`Unknown page status: ${page.status}`);
        counts[page.status]++;
    }
    return { ...counts, complete: scope === 'full' && !!finishedAt && counts.total > 0 && counts.ok === counts.total };
}

export async function runHarvest({ browserFactory, apps, outDir, base, sourceRoot = '.', scope = 'full', pageOptions = {} }) {
    if (resolve(outDir) === resolve('findings')) throw new Error('OUT_DIR must be an isolated run directory, not the mixed findings/ root');
    if (existsSync(outDir) && readdirSync(outDir).length) throw new Error(`Refusing to overwrite existing harvest directory: ${outDir}`);
    if (new Set(apps).size !== apps.length || apps.some(app => !/^[\w.-]+_REVIEW\.html$/.test(app))) throw new Error('Expected unique review-page filenames');
    mkdirSync(outDir, { recursive: true });
    const manifest = {
        schemaVersion: 1, startedAt: new Date().toISOString(), finishedAt: null, scope,
        runId: process.env.GITHUB_RUN_ID || null, runAttempt: process.env.GITHUB_RUN_ATTEMPT || null,
        sourceSha: process.env.GITHUB_SHA || null, baseUrl: base,
        pages: apps.map(app => ({ app, status: 'pending' })),
    };
    function saveManifest() {
        Object.assign(manifest, summarize(manifest.pages, scope, manifest.finishedAt));
        const file = join(outDir, '_harvest.json');
        writeFileSync(`${file}.tmp`, JSON.stringify(manifest, null, 2));
        renameSync(`${file}.tmp`, file);
    }
    saveManifest();
    console.log(`Harvesting ${apps.length} apps from ${base} -> ${outDir} (${scope})`);
    let browser;
    try {
        browser = await browserFactory();
        for (const [i, app] of apps.entries()) {
            const record = await harvestPage(browser, app, { base, source: readFileSync(join(sourceRoot, app), 'utf8'), ...pageOptions });
            writeFileSync(join(outDir, app.replace(/\.html$/, '.json')), JSON.stringify(record, null, 2));
            manifest.pages[i] = { app, status: record.status, reason: record.reason, error: record.error, attempts: record.attempts.length };
            saveManifest();
            console.log(`  ${record.status.toUpperCase()} ${app}: ${record.reason || record.error || record.findings.editor.decision}`);
        }
    } catch (error) {
        manifest.fatalError = String(error);
        throw error;
    } finally {
        try { if (browser) await browser.close(); }
        finally {
            manifest.finishedAt = new Date().toISOString();
            saveManifest();
            console.log(`Harvest summary: ${manifest.ok} ok / ${manifest.skipped} skipped / ${manifest.failed} failed / ${manifest.pending} pending; complete=${manifest.complete}`);
        }
    }
    return manifest;
}

async function main() {
    const { chromium } = await import('playwright');
    const all = readdirSync('.').filter(file => file.endsWith('_REVIEW.html')).sort();
    const selected = process.env.HARVEST_APPS?.split(',').filter(Boolean);
    if (selected?.some(app => !all.includes(app))) throw new Error('HARVEST_APPS includes an unknown review page');
    await runHarvest({
        browserFactory: () => chromium.launch(), apps: selected || all,
        base: process.env.SMOKE_BASE || 'http://localhost:8080/',
        outDir: process.env.OUT_DIR || `findings/${new Date().toISOString().replaceAll(':', '-')}`,
        scope: selected ? 'subset' : 'full',
    });
    // Executed partial harvests are retained; the workflow's completeness gate
    // reports failure after uploading evidence. They never become trusted baselines.
}

if (process.argv[1] && import.meta.url === pathToFileURL(resolve(process.argv[1])).href) {
    main().catch(error => { console.error(error); process.exitCode = 1; });
}
