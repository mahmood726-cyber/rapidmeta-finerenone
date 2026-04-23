// sentinel:skip-file
// Headless Playwright reproduction of the "Generate Output" bug.
// Walks through: load -> include trials -> AnalysisEngine.run -> ReportEngine.generate.
// Captures ALL pageerror and console.error events + the exact exception stack.
import pup from 'file:///C:/Users/user/AppData/Local/Temp/smoke/node_modules/puppeteer-core/lib/esm/puppeteer/puppeteer-core.js';

const BASE = process.env.BASE || 'http://localhost:8766/';
const APP = process.argv[2] || 'FINERENONE_REVIEW.html';

const browser = await pup.launch({
    executablePath: 'C:/Program Files/Google/Chrome/Application/chrome.exe',
    headless: 'new',
    args: ['--no-sandbox'],
});
const page = await browser.newPage();

const pageErrors = [];
const consoleErrors = [];
page.on('pageerror', e => pageErrors.push({ msg: e.message, stack: e.stack }));
page.on('console', m => {
    if (m.type() === 'error') consoleErrors.push(m.text());
});

console.log(`Loading ${BASE}${APP}...`);
await page.goto(BASE + APP, { waitUntil: 'networkidle2', timeout: 30000 });
await page.waitForFunction(() => window.RapidMeta != null, { timeout: 15000 });

// Give auto-analysis a moment
await new Promise(r => setTimeout(r, 2000));

// EXPLICITLY run analysis (what a user would have done before clicking Generate Output)
const runResult = await page.evaluate(() => {
    try {
        window.AnalysisEngine.run();
        return { ok: true, hasResults: !!(window.RapidMeta.state && window.RapidMeta.state.results) };
    } catch (e) {
        return { ok: false, err: e.message, stack: (e.stack || '').split('\n').slice(0, 5).join('\n') };
    }
});
console.log('\nAnalysisEngine.run():');
console.log(JSON.stringify(runResult, null, 2));
await new Promise(r => setTimeout(r, 2000));

// State before Generate Output
const before = await page.evaluate(() => ({
    hasResults: !!(window.RapidMeta && window.RapidMeta.state && window.RapidMeta.state.results),
    hasReportEngine: typeof window.ReportEngine === 'object',
    generateExists: !!(window.ReportEngine && typeof window.ReportEngine.generate === 'function'),
    trialsCount: (window.RapidMeta && window.RapidMeta.state && window.RapidMeta.state.trials || []).length,
    includedCount: (window.RapidMeta && window.RapidMeta.state && window.RapidMeta.state.trials || []).filter(t => t && t.data && t.included !== false).length,
}));
console.log('\nBefore Generate Output:');
console.log(JSON.stringify(before, null, 2));

// Directly invoke ReportEngine.generate() and capture the outcome.
const result = await page.evaluate(() => {
    try {
        const r = window.ReportEngine.generate();
        return { ok: true, ret: typeof r === 'object' ? '<object>' : String(r) };
    } catch (e) {
        return {
            ok: false,
            name: e.name,
            message: e.message,
            stack: (e.stack || '').split('\n').slice(0, 10).join('\n'),
        };
    }
});

console.log('\nReportEngine.generate() result:');
console.log(JSON.stringify(result, null, 2));

// Wait a bit in case it's async
await new Promise(r => setTimeout(r, 2000));

// Also try clicking the actual button
const btnClick = await page.evaluate(() => {
    const btn = document.querySelector('button[onclick*="ReportEngine.generate"]');
    if (!btn) return { found: false };
    try { btn.click(); return { found: true, clicked: true }; }
    catch (e) { return { found: true, clicked: false, error: e.message }; }
});
console.log('\nButton click:');
console.log(JSON.stringify(btnClick, null, 2));
await new Promise(r => setTimeout(r, 2000));

console.log('\n=== Captured pageerror events ===');
pageErrors.forEach(e => {
    console.log('\nMSG:', e.msg);
    console.log('STACK:\n', (e.stack || '').split('\n').slice(0, 8).join('\n'));
});
if (pageErrors.length === 0) console.log('(none)');

console.log('\n=== Captured console.error events ===');
consoleErrors.forEach(e => console.log(' - ' + e.split('\n')[0]));
if (consoleErrors.length === 0) console.log('(none)');

// Check what visible output appeared
const reportVisible = await page.evaluate(() => {
    const el = document.getElementById('report-content');
    return {
        exists: !!el,
        hidden: el ? el.classList.contains('hidden') : null,
        innerLength: el ? el.innerHTML.length : 0,
        firstChildTag: el && el.firstElementChild ? el.firstElementChild.tagName : null,
    };
});
console.log('\nReport content DOM state:');
console.log(JSON.stringify(reportVisible, null, 2));

await browser.close();
