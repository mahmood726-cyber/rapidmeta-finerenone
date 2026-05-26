// Minify the large inline RapidMeta engine block in a single HTML file.
// CLI: node scripts/minify_engine_block.mjs <input.html> <output.html>
//
// Reads stdin/argv, finds the first <script>...</script> body >= 100 KB,
// minifies it via terser with mangle disabled (preserves the global
// RapidMeta API consumed by inline HTML onclick handlers + button refs),
// writes the result back with the block replaced.
//
// terser settings rationale:
//   mangle: false       — preserves window.RapidMeta and member-named
//                         entry points referenced from HTML strings
//   compress: { ... }   — strips whitespace, comments, dead code; keeps
//                         observable behaviour
//   format.comments: false — drops licence comments inside the engine
//   format.beautify: false — single-line output

import { minify } from 'terser';
import { readFile, writeFile } from 'node:fs/promises';

const [, , inPath, outPath] = process.argv;
if (!inPath || !outPath) {
    console.error('Usage: node minify_engine_block.mjs <input.html> <output.html>');
    process.exit(2);
}

const html = await readFile(inPath, 'utf-8');

// Find the first <script>BODY</script> whose body is >= 100 KB. There's
// only one such block per FULL_REVIEW page (the engine).
const re = /<script\b([^>]*)>([\s\S]*?)<\/script>/g;
let match;
let target = null;
while ((match = re.exec(html)) !== null) {
    if (match[2].length >= 100000) {
        target = { attrs: match[1], body: match[2], start: match.index, end: match.index + match[0].length };
        break;
    }
}
if (!target) {
    console.error(`No engine block found in ${inPath}`);
    process.exit(3);
}

const before = target.body.length;
console.error(`Engine block: ${before.toLocaleString()} bytes`);

let result;
try {
    result = await minify(target.body, {
        mangle: false,
        compress: {
            booleans: true,
            collapse_vars: true,
            comparisons: true,
            conditionals: true,
            dead_code: true,
            evaluate: true,
            if_return: true,
            join_vars: true,
            keep_fnames: true,     // preserve fn names for stack traces
            keep_classnames: true,
            loops: true,
            negate_iife: false,
            properties: false,     // do NOT rewrite obj.prop -> obj["prop"]
            sequences: true,
            unused: false,         // do NOT drop unused locals — too risky
            // Drop console.log calls? Engine uses some for telemetry; keep
            // them so behaviour is unchanged.
            drop_console: false,
            drop_debugger: true,
        },
        format: {
            comments: false,
            beautify: false,
            ecma: 2020,
        },
        ecma: 2020,
        sourceMap: false,
    });
} catch (e) {
    console.error(`terser failed on ${inPath}: ${e.message}`);
    process.exit(4);
}

const minified = result.code;
const after = minified.length;
console.error(`Minified: ${after.toLocaleString()} bytes  (saved ${(before - after).toLocaleString()} / ${((1 - after / before) * 100).toFixed(1)}%)`);

const newScript = `<script${target.attrs}>${minified}</script>`;
const newHtml = html.slice(0, target.start) + newScript + html.slice(target.end);

await writeFile(outPath, newHtml, 'utf-8');
console.error(`Wrote ${outPath} (${newHtml.length.toLocaleString()} bytes)`);
