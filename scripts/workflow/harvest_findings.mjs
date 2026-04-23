// sentinel:skip-file
// Launch headless Chromium against every *_REVIEW.html in the repo, run
// AnalysisEngine + the console-only peer-review, and write one JSON file
// per app under findings/<timestamp>/<app>.json.
//
// Designed for the 'findings-harvester' GitHub Actions workflow. Can also
// be run locally when a local server is serving the repo on port 8080.

import { chromium } from 'playwright';
import { readdirSync, writeFileSync, mkdirSync } from 'node:fs';
import { join } from 'node:path';

const BASE = process.env.SMOKE_BASE || 'http://localhost:8080/';
const OUT_DIR = process.env.OUT_DIR || `findings/${new Date().toISOString().slice(0, 10)}`;

mkdirSync(OUT_DIR, { recursive: true });
const apps = readdirSync('.').filter(f => f.endsWith('_REVIEW.html')).sort();
console.log(`Harvesting ${apps.length} apps from ${BASE} -> ${OUT_DIR}`);

const browser = await chromium.launch();
let ok = 0, skipped = 0, failed = 0;

for (const app of apps) {
    const page = await browser.newPage();
    const start = Date.now();
    try {
        await page.goto(BASE + app, { waitUntil: 'networkidle', timeout: 30000 });
        await page.waitForFunction(() => window.RapidMeta != null, { timeout: 15000 });

        // Ensure AnalysisEngine.run() has fired at least once.
        await page.evaluate(() => {
            try { window.AnalysisEngine && window.AnalysisEngine.run && window.AnalysisEngine.run(); } catch (e) {}
        });
        await page.waitForTimeout(1500);

        // Previously the harvester injected a mock state to force peer-review
        // to run even when headless analysis didn't populate state.results.
        // That produced spurious findings (e.g. benchmark-divergence concerns
        // against fake pool values). Now: only run peer-review when real
        // analysis produced real results. Otherwise emit {error: 'no-analysis'}
        // so aggregate statistics exclude these apps.
        const stateCheck = await page.evaluate(() => {
            const RM = window.RapidMeta;
            if (!RM || !RM.state || !RM.state.results) return { ok: false, why: 'no-state.results' };
            const r = RM.state.results;
            if (r.or == null || r.or === '--') return { ok: false, why: 'or-unpopulated' };
            return { ok: true };
        });

        const findings = stateCheck.ok ? await page.evaluate(() => {
            if (typeof window.RapidMeta.runPeerReview !== 'function') return null;
            try { return window.RapidMeta.runPeerReview(); } catch (e) { return { error: String(e) }; }
        }) : { skipped: true, reason: stateCheck.why };

        const state = await page.evaluate(() => {
            const RM = window.RapidMeta;
            if (!RM || !RM.state || !RM.state.results) return null;
            const r = RM.state.results;
            return {
                k: r.k, or: r.or, i2: r.i2, tau2: r.tau2,
                grade: r.gradeCertainty,
                remlSensitivity: !!r.remlSensitivity,
                robSummary: r.robSummary || null,
                isCompleteUniverse: r.isCompleteUniverse || false,
                totalAvailable: r.totalAvailable || null,
                includedCount: r.includedCount || null,
                searchResultCount: r.searchResultCount || null,
                nnt: r.nnt || null,
                absoluteRisk: r.absoluteRisk || null,
                patientReportedOutcomes: r.patientReportedOutcomes || null,
            };
        });

        const record = {
            app,
            timestamp: new Date().toISOString(),
            durationMs: Date.now() - start,
            state,
            findings,
        };
        const outPath = join(OUT_DIR, app.replace(/\.html$/, '.json'));
        writeFileSync(outPath, JSON.stringify(record, null, 2));
        if (findings && findings.editor) {
            console.log(`  OK  ${app}: ${findings.editor.decision} (${findings.reviewers?.reduce((a, b) => a + (b.concerns?.length || 0), 0) || 0} concerns)`);
            ok++;
        } else {
            console.log(`  SKIP ${app}: no findings`);
            skipped++;
        }
    } catch (e) {
        console.log(`  FAIL ${app}: ${String(e).slice(0, 120)}`);
        failed++;
        const outPath = join(OUT_DIR, app.replace(/\.html$/, '.json'));
        writeFileSync(outPath, JSON.stringify({ app, error: String(e), timestamp: new Date().toISOString() }, null, 2));
    } finally {
        await page.close();
    }
}

await browser.close();
console.log(`\nHarvest summary: ${ok} ok / ${skipped} skipped / ${failed} failed`);
process.exit(failed === apps.length ? 1 : 0);   // fail only if ALL apps errored
