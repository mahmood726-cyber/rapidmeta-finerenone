// sentinel:skip-file
// Capture peer-review QA findings across representative apps.
// Run analysis with real included trials, then dump console findings.
import puppeteer from 'file:///C:/Users/user/AppData/Local/Temp/smoke/node_modules/puppeteer-core/lib/esm/puppeteer/puppeteer-core.js';

const BASE = process.env.RAPIDMETA_SMOKE_BASE || 'http://localhost:8766/';
const TARGETS = [
  'FINERENONE_REVIEW.html',
  'ARNI_HF_REVIEW.html',
  'PCSK9_REVIEW.html',
  'SGLT2I_HF_NMA_REVIEW.html',
  'COLCHICINE_CVD_REVIEW.html',
];

const browser = await puppeteer.launch({
  executablePath: 'C:/Program Files/Google/Chrome/Application/chrome.exe',
  headless: 'new',
  args: ['--no-sandbox'],
});

const aggregateConcerns = new Map();

for (const f of TARGETS) {
  const page = await browser.newPage();
  const findings = [];
  page.on('console', m => {
    if (m.type() === 'warning') findings.push(m.text());
  });

  try {
    await page.goto(BASE + f, { waitUntil: 'networkidle2', timeout: 30000 });
    await page.waitForFunction(() => window.RapidMeta != null, { timeout: 10000 });

    // Try to run the app's natural analysis first (all trials included by default)
    await page.evaluate(() => {
      if (typeof window.AnalysisEngine?.run === 'function') {
        try { window.AnalysisEngine.run(); } catch (e) {}
      }
    });
    await new Promise(r => setTimeout(r, 2000));

    const result = await page.evaluate(() => {
      const RM = window.RapidMeta;
      if (!RM) return { err: 'no-RapidMeta' };
      const r = RM.state && RM.state.results;
      if (!r) return { err: 'no-state.results' };

      // Run peer review explicitly
      if (typeof RM.runPeerReview === 'function') {
        const findings = RM.runPeerReview();
        return {
          hasResults: true,
          k: r.k, or: r.or,
          findings: findings,
          resultsFields: Object.keys(r),
        };
      }
      return { hasResults: true, k: r.k, or: r.or, findings: null, resultsFields: Object.keys(r) };
    });

    console.log('\n=== ' + f + ' ===');
    console.log('k=' + result.k + ' or=' + result.or);
    if (result.resultsFields) console.log('state.results fields: ' + result.resultsFields.join(', '));
    if (result.findings) {
      console.log('Editor: ' + result.findings.editor.decision);
      result.findings.reviewers.forEach(rv => {
        console.log('  ' + rv.role + ' [' + rv.recommendation + ']');
        rv.concerns.forEach(c => {
          console.log('    - ' + c);
          const key = c.substring(0, 60);
          aggregateConcerns.set(key, (aggregateConcerns.get(key) || 0) + 1);
        });
      });
    }
    if (result.err) console.log('ERR: ' + result.err);
  } catch (e) {
    console.log(f + ' FAIL: ' + e.message);
  } finally {
    await page.close();
  }
}

console.log('\n=== Aggregate concerns across apps ===');
const sorted = [...aggregateConcerns.entries()].sort((a,b) => b[1]-a[1]);
for (const [k, v] of sorted) console.log(v + 'x  ' + k);

await browser.close();
