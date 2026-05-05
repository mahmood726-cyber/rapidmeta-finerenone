"""Codemod: inject per-topic verdict-badge data + render script into reviews.

Idempotent. Skips files already containing `vendor/verdict-badge.js`.
Runs scripts/compute_verdict_badges.py FIRST internally to refresh
outputs/verdict_badges.json.

For each review HTML:
  1. Insert `<script src="vendor/verdict-badge.js"></script>` before </head>.
  2. Insert `<script>window.__verdict = {...}</script>` immediately after,
     with the per-file verdict object inlined (no fetch needed — works for
     file:// and GitHub Pages alike).
  3. Insert a `<div id="verdictBadgeContainer"></div>` BEFORE the
     "Registration & Administrative Information" section so the badge is
     the first thing readers see on the Protocol tab.
  4. Insert a render-on-DOMContentLoaded script.

Use --dry-run for preview. Use --refresh to re-run the aggregator before
patching (otherwise we trust an existing outputs/verdict_badges.json).
"""
from __future__ import annotations
import sys, io, argparse, json, re, subprocess
from pathlib import Path
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

REPO = Path("C:/Projects/Finrenone")
JSON_PATH = REPO / "outputs" / "verdict_badges.json"

SCRIPT_TAG = '\n    <!-- Verdict badge: per-topic data-integrity rollup of 7 gates -->\n    <script src="vendor/verdict-badge.js"></script>\n'

INLINE_DATA_TPL = '\n<script>window.__verdict = {data};</script>\n'

CONTAINER_TPL = '<div id="verdictBadgeContainer"></div>\n                    '

RENDER_SCRIPT = '''
<script>
(function () {
    function ready(fn) {
        if (document.readyState !== 'loading') fn();
        else document.addEventListener('DOMContentLoaded', fn);
    }
    ready(function () {
        if (window.VerdictBadge && document.getElementById('verdictBadgeContainer')) {
            window.VerdictBadge.render('#verdictBadgeContainer');
        }
    });
})();
</script>
'''

# Match the registration-section header (the existing landmark in every review).
REG_LANDMARK = re.compile(
    r'<div class="bg-slate-900/80 p-4 border-b border-slate-800"><h3 class="text-xs font-bold uppercase text-blue-400 tracking-widest"><i class="fa-solid fa-id-card mr-2"></i>1\. Registration'
)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--refresh", action="store_true",
                    help="Re-run scripts/compute_verdict_badges.py before patching")
    args = ap.parse_args()

    if args.refresh or not JSON_PATH.exists():
        print("Running compute_verdict_badges.py to refresh", JSON_PATH)
        subprocess.check_call([sys.executable, str(REPO / "scripts" / "compute_verdict_badges.py")])

    badges = json.loads(JSON_PATH.read_text(encoding="utf-8"))

    files = sorted(REPO.glob("*_REVIEW.html"))
    print(f"Patching {len(files)} review HTMLs ...")

    patched, skip_already, skip_no_landmark, skip_no_data = 0, 0, 0, 0
    for hp in files:
        text = hp.read_text(encoding="utf-8", errors="replace")

        if 'vendor/verdict-badge.js' in text:
            skip_already += 1
            continue

        data = badges.get(hp.name)
        if not data:
            skip_no_data += 1
            continue

        # 1. Find </head>
        head_close = text.find("</head>")
        if head_close == -1:
            skip_no_landmark += 1
            continue

        # 2. Find Registration section landmark
        m = REG_LANDMARK.search(text)
        if not m:
            skip_no_landmark += 1
            continue

        # Build replacements
        json_blob = json.dumps(data, ensure_ascii=False)
        # Escape </script in JSON to prevent script-block break
        json_blob = json_blob.replace('</', '<\\/')
        head_inject = SCRIPT_TAG + INLINE_DATA_TPL.format(data=json_blob)

        # Apply later position FIRST so earlier offsets remain valid.
        new_text = text[:m.start()] + CONTAINER_TPL + text[m.start():]
        # Append render script before </body>
        body_close = new_text.rfind("</body>")
        if body_close != -1:
            new_text = new_text[:body_close] + RENDER_SCRIPT + new_text[body_close:]
        # Now insert script tag + inline data before </head>
        head_close2 = new_text.find("</head>")
        new_text = new_text[:head_close2] + head_inject + new_text[head_close2:]

        if not args.dry_run:
            hp.write_text(new_text, encoding="utf-8")
        patched += 1
        print(f"  PATCH {hp.name}  [{data['verdict']}]")

    print(f"\n=== Summary ===")
    print(f"  Patched:        {patched}")
    print(f"  Already done:   {skip_already}")
    print(f"  No landmark:    {skip_no_landmark}")
    print(f"  No verdict:     {skip_no_data}")
    if args.dry_run:
        print("  DRY RUN — no files written.")


if __name__ == "__main__":
    main()
