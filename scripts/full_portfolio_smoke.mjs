// sentinel:skip-file
// Full portfolio smoke: load every *_REVIEW.html, run analysis, click
// Generate Output, capture pageerrors. Fails any app where generate() throws
// or report-content stays hidden after Generate click.
import pup from 'file:///C:/Users/user/AppData/Local/Temp/smoke/node_modules/puppeteer-core/lib/esm/puppeteer/puppeteer-core.js';
import { readdirSync, writeFileSync } from 'node:fs';

const BASE = process.env.BASE || 'http://localhost:8766/';
const apps = readdirSync('.').filter(f => f.endsWith('_REVIEW.html')).sort();
console.log(`Smoke-testing ${apps.length} apps @ ${BASE}`);

const browser = await pup.launch({
    executablePath: 'C:/Program Files/Google/Chrome/Application/chrome.exe',
    headless: 'new',
    args: ['--no-sandbox'],
});

const results = [];
let ok = 0, generateFail = 0, hiddenFail = 0, loadFail = 0;

for (const app of apps) {
    const page = await browser.newPage();
    const errors = [];
    page.on('pageerror', e => errors.push(e.message.split('\n')[0]));

    try {
        await page.goto(BASE + app, { waitUntil: 'networkidle2', timeout: 25000 });
        await page.waitForFunction(() => window.RapidMeta != null, { timeout: 8000 });
        await page.evaluate(() => {
            try { window.AnalysisEngine?.run?.(); } catch (e) {}
        });
        await new Promise(r => setTimeout(r, 800));

        const state = await page.evaluate(() => {
            const RM = window.RapidMeta;
            return {
                hasResults: !!(RM && RM.state && RM.state.results),
                hasReport: typeof window.ReportEngine?.generate === 'function',
            };
        });
        if (!state.hasReport) {
            results.push({ app, status: 'no-report-engine' });
            await page.close();
            continue;
        }

        // Invoke Generate Output
        const gen = await page.evaluate(() => {
            try { window.ReportEngine.generate(); return { ok: true }; }
            catch (e) { return { ok: false, err: e.message.split('\n')[0] }; }
        });
        await new Promise(r => setTimeout(r, 400));

        const dom = await page.evaluate(() => {
            const el = document.getElementById('report-content');
            return {
                exists: !!el,
                hidden: el ? el.classList.contains('hidden') : null,
                innerLen: el ? el.innerHTML.length : 0,
            };
        });

        const pageErrs = errors.filter(e =>
            !e.includes('fetch') && !e.includes('CORS') && !e.includes('PubMed') &&
            !e.includes('Europe PMC') && !e.includes('Access to fetch')
        );

        let status;
        if (!gen.ok) {
            status = 'generate-threw';
            generateFail++;
        } else if (dom.exists && dom.hidden) {
            status = 'report-hidden';
            hiddenFail++;
        } else if (pageErrs.length > 0) {
            status = 'pageerror';
            generateFail++;
        } else {
            status = 'ok';
            ok++;
        }
        results.push({
            app, status, gen, dom, errors: pageErrs.slice(0, 3), hasResults: state.hasResults
        });
    } catch (e) {
        loadFail++;
        results.push({ app, status: 'load-fail', err: e.message.split('\n')[0] });
    } finally {
        try { await page.close(); } catch (e) { /* ignore */ }
    }
}

await browser.close();

writeFileSync('scripts/full_portfolio_smoke_results.json', JSON.stringify(results, null, 2));

const byStatus = {};
for (const r of results) byStatus[r.status] = (byStatus[r.status] || 0) + 1;
console.log('\n=== Summary ===');
console.log(`Total:          ${results.length}`);
for (const [k, v] of Object.entries(byStatus)) console.log(`  ${k.padEnd(16)}: ${v}`);
console.log('');
if (generateFail + hiddenFail + loadFail > 0) {
    console.log('\n=== Failures ===');
    for (const r of results) {
        if (r.status !== 'ok' && r.status !== 'no-report-engine') {
            console.log(`${r.app}: ${r.status}`);
            if (r.gen && !r.gen.ok) console.log(`  generate err: ${r.gen.err}`);
            if (r.errors && r.errors.length) r.errors.forEach(e => console.log(`  pageerror: ${e}`));
            if (r.err) console.log(`  load err: ${r.err}`);
        }
    }
}
process.exit((generateFail + hiddenFail + loadFail) > 0 ? 1 : 0);
