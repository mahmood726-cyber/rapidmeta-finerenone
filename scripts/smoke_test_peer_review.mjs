// sentinel:skip-file
// Runtime smoke test: open representative apps, run analysis, verify peer-review panel renders.
import puppeteer from 'file:///C:/Users/user/AppData/Local/Temp/smoke/node_modules/puppeteer-core/lib/esm/puppeteer/puppeteer-core.js';
import path from 'path';
import fs from 'fs';

const BASE = process.env.RAPIDMETA_SMOKE_BASE || 'http://localhost:8766/';
const TARGETS = [
  'FINERENONE_REVIEW.html',           // modern template
  'CFTR_MODULATORS_NMA_REVIEW.html',  // NMA template (injected via </body>)
  'COLCHICINE_CVD_REVIEW.html',       // legacy with retrofit
];

const CHROME_CANDIDATES = [
  'C:/Program Files/Google/Chrome/Application/chrome.exe',
  'C:/Program Files (x86)/Google/Chrome/Application/chrome.exe',
  process.env.LOCALAPPDATA + '/Google/Chrome/Application/chrome.exe',
];
const chromeExe = CHROME_CANDIDATES.find(p => { try { return fs.existsSync(p); } catch { return false; } });
if (!chromeExe) { console.error('Chrome not found'); process.exit(2); }

const browser = await puppeteer.launch({
  executablePath: chromeExe,
  headless: 'new',
  args: ['--no-sandbox'],
});

let overallFail = false;
for (const f of TARGETS) {
  const url = BASE + f;
  const page = await browser.newPage();
  const errors = [];
  page.on('pageerror', e => errors.push('pageerror: ' + e.message));
  page.on('console', m => { if (m.type() === 'error') errors.push('console.error: ' + m.text()); });

  try {
    await page.goto(url, { waitUntil: 'networkidle2', timeout: 30000 });

    // Wait for RapidMeta to initialize
    await page.waitForFunction(() => window.RapidMeta != null, { timeout: 10000 });

    // Click analysis tab if there is one
    const tabClicked = await page.evaluate(() => {
      const btn = Array.from(document.querySelectorAll('[data-tab],[onclick]')).find(el => {
        const t = (el.getAttribute('data-tab') || el.getAttribute('onclick') || '');
        return /analysis/i.test(t);
      });
      if (btn) { btn.click(); return true; }
      return false;
    });

    // Force-inject a minimal mock results state to test peer-review render.
    // Real AnalysisEngine.run() requires included trials; for a smoke test
    // we just need state.results populated so generateManuscriptText() fires.
    await page.evaluate(() => {
      const RM = window.RapidMeta;
      if (!RM) return;
      RM.state = RM.state || {};
      RM.state.results = {
        k: 5, or: '0.75', lci: '0.65', uci: '0.87', i2: 25, tau2: 0.01,
        qPvalue: '0.15', gradeCertainty: 'MODERATE', confLevel: 0.95,
      };
      RM.state.protocol = RM.state.protocol || { int: 'study intervention', comp: 'control', pop: 'target population', out: 'primary outcome' };
      RM.state.selectedOutcome = 'default';
    });

    // Ensure a #manuscript-text container exists (some apps may hide it)
    await page.evaluate(() => {
      let c = document.getElementById('manuscript-text');
      if (!c) { c = document.createElement('div'); c.id = 'manuscript-text'; document.body.appendChild(c); }
      c.style.display = 'block';
    });

    await page.evaluate(() => {
      if (typeof window.generateManuscriptText === 'function') window.generateManuscriptText();
    });

    await new Promise(r => setTimeout(r, 800));

    const check = await page.evaluate(() => {
      const container = document.getElementById('manuscript-text');
      const panel = container ? container.querySelector('.peer-review-panel') : null;
      const editor = panel ? panel.querySelector('.peer-review-editor') : null;
      const cards = panel ? panel.querySelectorAll('.peer-review-card').length : 0;
      const benchmark = container ? container.querySelector('.benchmark-retrofit') : null;
      const rmeta = !!window.RapidMeta;
      const gmt = typeof window.generateManuscriptText === 'function';
      const peerInstalled = !!(window.RapidMeta && window.RapidMeta.__peerReviewInstalled);
      const benchInstalled = !!(window.RapidMeta && window.RapidMeta.__benchmarkRetrofitInstalled);
      return {
        hasRapidMeta: rmeta,
        hasGenerate: gmt,
        peerInstalled,
        benchInstalled,
        hasContainer: !!container,
        hasPanel: !!panel,
        hasEditor: !!editor,
        reviewerCards: cards,
        hasBenchmarkRetrofit: !!benchmark,
      };
    });

    const ok = check.peerInstalled && check.hasPanel && check.reviewerCards >= 3 && errors.length === 0;
    console.log(`${ok ? 'OK  ' : 'FAIL'} ${f}`);
    console.log(`     peer=${check.peerInstalled} panel=${check.hasPanel} editor=${check.hasEditor} cards=${check.reviewerCards} bench=${check.benchInstalled}/${check.hasBenchmarkRetrofit} errors=${errors.length}`);
    if (errors.length) errors.slice(0, 3).forEach(e => console.log('     ' + e));
    if (!ok) overallFail = true;
  } catch (e) {
    console.log(`FAIL ${f}: ${e.message}`);
    overallFail = true;
  } finally {
    await page.close();
  }
}

await browser.close();
process.exit(overallFail ? 1 : 0);
