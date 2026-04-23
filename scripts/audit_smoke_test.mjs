#!/usr/bin/env node
// sentinel:skip-file — developer tool; hardcoded paths are intentional (local Finrenone checkout only)
// Runtime smoke test — launches headless Chrome against every _REVIEW.html
// and records any `pageerror` or `console.error` fired during the first 1.5s
// after DOMContentLoaded. Catches runtime bugs that static analysis misses
// (undefined references in monkey-patches, typos that only fire when init()
// runs, etc.). Re-run after any major portfolio migration in ~90 seconds.
//
// Prerequisites:
//   1. HTTP server running on :8766 serving C:/Projects/Finrenone
//        cd C:/Projects/Finrenone && python -m http.server 8766
//   2. puppeteer-core installed (e.g. `cd /tmp/smoke && npm install puppeteer-core`)
//
// Usage:
//   node scripts/audit_smoke_test.mjs           # tests all _REVIEW.html
//   node scripts/audit_smoke_test.mjs --file X  # tests one file by basename
//
// Configuration via env var:
//   RAPIDMETA_ROOT        default C:/Projects/Finrenone
//   RAPIDMETA_SMOKE_BASE  default http://localhost:8766/
//   RAPIDMETA_CHROME      default C:/Program Files/Google/Chrome/Application/chrome.exe

import puppeteer from 'puppeteer-core';
import { readdirSync } from 'fs';

const ROOT   = process.env.RAPIDMETA_ROOT       || 'C:/Projects/Finrenone';
const BASE   = process.env.RAPIDMETA_SMOKE_BASE || 'http://localhost:8766/';
const CHROME = process.env.RAPIDMETA_CHROME     || 'C:/Program Files/Google/Chrome/Application/chrome.exe';

const fileArg = (() => {
    const i = process.argv.indexOf('--file');
    return i > -1 ? process.argv[i + 1] : null;
})();

const files = fileArg
    ? [fileArg]
    : readdirSync(ROOT).filter(f => f.endsWith('_REVIEW.html')).sort();

const browser = await puppeteer.launch({
    executablePath: CHROME,
    headless: 'new',
    args: ['--no-sandbox', '--disable-gpu']
});

const results = [];
for (const f of files) {
    const page = await browser.newPage();
    const errors = [];
    page.on('pageerror', e => errors.push(`[pageerror] ${e.message}`));
    page.on('console', m => { if (m.type() === 'error') errors.push(`[console.error] ${m.text()}`); });
    try {
        await page.goto(BASE + f, { waitUntil: 'domcontentloaded', timeout: 20000 });
        await new Promise(r => setTimeout(r, 1500));  // let init() + hydrators fire
    } catch (e) {
        errors.push(`[navigate] ${e.message}`);
    }
    results.push({ f, errors });
    await page.close();
}

await browser.close();

const clean = results.filter(r => r.errors.length === 0);
const bad   = results.filter(r => r.errors.length > 0);

console.log(`Runtime smoke test`);
console.log(`  ${clean.length}/${files.length} clean, ${bad.length} with console/page errors`);

if (bad.length > 0) {
    console.log();
    for (const r of bad) {
        console.log(`\n${r.f} (${r.errors.length} error${r.errors.length !== 1 ? 's' : ''}):`);
        for (const e of r.errors.slice(0, 5)) console.log(`  ${e.slice(0, 240)}`);
        if (r.errors.length > 5) console.log(`  ... +${r.errors.length - 5} more`);
    }
    process.exit(1);  // non-zero exit for CI integration
}
