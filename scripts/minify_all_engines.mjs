// Portfolio-wide engine-block minification. For every *_REVIEW.html in the
// repo root, find the first inline <script>BODY</script> with BODY >= 100 KB,
// minify it via terser (mangle: false, see minify_engine_block.mjs for
// rationale), and rewrite the file in place.
//
// Idempotent: re-running on an already-minified page is fine — terser will
// just produce roughly the same output, and the byte delta will be ~0.
//
// Usage: node scripts/minify_all_engines.mjs [--limit N] [--dry-run]

import { minify } from 'terser';
import { readFile, writeFile, readdir, stat } from 'node:fs/promises';
import { fileURLToPath } from 'node:url';
import { dirname, join } from 'node:path';

const __dirname = dirname(fileURLToPath(import.meta.url));
const ROOT = join(__dirname, '..');

const args = new Set(process.argv.slice(2));
const dryRun = args.has('--dry-run');
const limitIdx = process.argv.indexOf('--limit');
const limit = limitIdx > -1 ? parseInt(process.argv[limitIdx + 1], 10) : Infinity;

const TERSER_OPTS = {
    mangle: false,
    compress: {
        booleans: true, collapse_vars: true, comparisons: true, conditionals: true,
        dead_code: true, evaluate: true, if_return: true, join_vars: true,
        keep_fnames: true, keep_classnames: true, loops: true,
        properties: false, sequences: true, unused: false,
        drop_console: false, drop_debugger: true,
    },
    format: { comments: false, beautify: false, ecma: 2020 },
    ecma: 2020,
    sourceMap: false,
};

const SCRIPT_RE = /<script\b([^>]*)>([\s\S]*?)<\/script>/g;

async function processOne(path) {
    const html = await readFile(path, 'utf-8');
    SCRIPT_RE.lastIndex = 0;
    let target = null;
    let m;
    while ((m = SCRIPT_RE.exec(html)) !== null) {
        if (m[2].length >= 100000) {
            target = { attrs: m[1], body: m[2], start: m.index, end: m.index + m[0].length };
            break;
        }
    }
    if (!target) return { path, skip: 'no-large-block', before: html.length, after: html.length };

    const before = target.body.length;
    let result;
    try {
        result = await minify(target.body, TERSER_OPTS);
    } catch (e) {
        return { path, skip: 'terser-failed', error: e.message.split('\n')[0], before, after: before };
    }
    const minified = result.code;
    const after = minified.length;
    if (after >= before * 0.97) {
        // Already minified-ish (< 3% reduction) — skip rewrite to avoid pointless churn
        return { path, skip: 'already-minified', before, after };
    }

    const newScript = `<script${target.attrs}>${minified}</script>`;
    const newHtml = html.slice(0, target.start) + newScript + html.slice(target.end);

    if (!dryRun) await writeFile(path, newHtml, 'utf-8');
    return { path, before, after, savedBytes: before - after, savedPct: ((1 - after / before) * 100).toFixed(1) };
}

// Find every *_REVIEW.html in the repo root
const entries = await readdir(ROOT);
const targets = entries.filter(f => /_REVIEW\.html$/.test(f)).sort();
console.error(`${targets.length} candidate pages`);

// Concurrency: terser is CPU-bound; 4 workers keep all cores busy.
const CONCURRENCY = 4;
let totalBefore = 0, totalAfter = 0, ok = 0, skipped = 0;
const skippedReasons = {};
const total = Math.min(targets.length, limit);
let next = 0;
let done = 0;

async function worker() {
    while (true) {
        const i = next++;
        if (i >= total) return;
        const r = await processOne(join(ROOT, targets[i]));
        totalBefore += r.before;
        totalAfter += r.after;
        if (r.skip) {
            skipped++;
            skippedReasons[r.skip] = (skippedReasons[r.skip] || 0) + 1;
        } else {
            ok++;
        }
        done++;
        if (done % 100 === 0 || done === total) {
            console.error(`[${done}/${total}]  ok=${ok}  skipped=${skipped}  saved so far: ${(totalBefore - totalAfter).toLocaleString()} bytes (${((1 - totalAfter / totalBefore) * 100).toFixed(1)}%)`);
        }
    }
}

await Promise.all(Array.from({ length: CONCURRENCY }, () => worker()));

console.log(JSON.stringify({
    pages: targets.length,
    processed: Math.min(targets.length, limit),
    minified: ok,
    skipped,
    skippedReasons,
    totalBefore,
    totalAfter,
    savedBytes: totalBefore - totalAfter,
    savedPct: totalBefore > 0 ? ((1 - totalAfter / totalBefore) * 100).toFixed(2) : '0',
    dryRun,
}, null, 2));
