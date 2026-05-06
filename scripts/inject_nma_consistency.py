"""Codemod: inject NMA Pro-style direct/indirect consistency panel into NMA
reviews.

Idempotent. Skips files already containing `vendor/nma-consistency.js`.

For each *_NMA_REVIEW.html file:
  1. Insert  `<script src="vendor/nma-consistency.js"></script>`  before
     </head> (right after the existing pairwise-pool.js include if present).
  2. Insert a "Network Consistency (Direct vs Indirect)" panel after the
     existing `<div id="nma-consistency-container">` (or at end of NMA tab
     if that container isn't found).
  3. Wire a render-on-NMA-tab-switch handler.

Run with --dry-run to preview.
"""
from __future__ import annotations
import sys, io, argparse, re
from pathlib import Path
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

REPO = Path(__file__).resolve().parent.parent

SCRIPT_TAG_AFTER_PAIRWISE = (
    '\n    <!-- NMA consistency: direct/indirect node-split + Fisher-combined inconsistency test (NMA Pro v8 transplant) -->\n'
    '    <script src="vendor/nma-consistency.js"></script>\n'
)

# Look for existing pairwise-pool.js include — insert nma-consistency right after.
PAIRWISE_INCLUDE_RE = re.compile(r'<script\s+src="vendor/pairwise-pool\.js"\s*></script>')

# Fallback: insert before </head>
HEAD_CLOSE_RE = re.compile(r'</head>')

# Existing landmark inside NMA tab
EXISTING_CONSISTENCY_CONTAINER = re.compile(
    r'<div id="nma-consistency-container">\s*</div>'
)

# New panel HTML (rendered after the existing container)
NEW_PANEL = '''
                            <div class="glass p-10 rounded-[40px] border border-slate-800 mt-10">
                                <h3 class="text-sm font-bold opacity-60 uppercase tracking-[0.3em] mb-2">Network Consistency (NMA Pro Transplant)</h3>
                                <p class="text-[11px] text-slate-400 mb-4">
                                    NMA-Pro-style direct/indirect node-splitting with Fisher-combined global inconsistency test (Dias et al. 2010 back-calculation).
                                    Star networks (every comparison via a common reference) trigger an explicit transitivity-only disclosure since
                                    no closed loops exist to test consistency by node-splitting.
                                </p>
                                <div class="flex gap-2 items-center mb-4">
                                    <button id="nmaConsBtn" class="px-4 py-2 text-xs font-bold bg-cyan-600 hover:bg-cyan-500 text-white rounded transition">Run consistency check</button>
                                    <select id="nmaConsMeasure" class="px-3 py-2 text-xs bg-slate-900 border border-slate-700 rounded text-slate-200">
                                        <option value="RR">Risk ratio (RR)</option>
                                        <option value="OR">Odds ratio (OR)</option>
                                    </select>
                                </div>
                                <div id="nmaConsResult"></div>
                            </div>

                            <script>
                            (function () {
                                function go() {
                                    var measure = document.getElementById('nmaConsMeasure').value;
                                    var rd = window.RapidMeta && window.RapidMeta.realData;
                                    var cfg = window.NMA_CONFIG;
                                    var container = document.getElementById('nmaConsResult');
                                    if (!rd) { container.innerHTML = '<div style="color:#f87171;font-size:12px;padding:1em;">No realData found.</div>'; return; }
                                    if (!cfg) { container.innerHTML = '<div style="color:#f87171;font-size:12px;padding:1em;">No NMA_CONFIG found.</div>'; return; }
                                    var res = window.NMAConsistency.analyze(rd, cfg, { measure: measure });
                                    window.NMAConsistency.render(container, res);
                                }
                                document.addEventListener('DOMContentLoaded', function () {
                                    var btn = document.getElementById('nmaConsBtn');
                                    if (btn) btn.addEventListener('click', go);
                                });
                            })();
                            </script>
'''


def patch(text: str) -> tuple[str, str]:
    """Returns (new_text, status_msg). status_msg is one of: PATCHED, ALREADY,
    NO_HEAD, NO_LANDMARK."""
    if 'vendor/nma-consistency.js' in text:
        return text, "ALREADY"
    # Step 1: inject script tag
    pw = PAIRWISE_INCLUDE_RE.search(text)
    if pw:
        new_text = text[:pw.end()] + SCRIPT_TAG_AFTER_PAIRWISE + text[pw.end():]
    else:
        head = HEAD_CLOSE_RE.search(text)
        if not head:
            return text, "NO_HEAD"
        new_text = text[:head.start()] + SCRIPT_TAG_AFTER_PAIRWISE + text[head.start():]

    # Step 2: insert new panel after existing consistency container
    landmark = EXISTING_CONSISTENCY_CONTAINER.search(new_text)
    if not landmark:
        return text, "NO_LANDMARK"
    new_text = new_text[:landmark.end()] + NEW_PANEL + new_text[landmark.end():]
    return new_text, "PATCHED"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    files = sorted(REPO.glob("*_NMA_REVIEW.html"))
    print(f"Patching {len(files)} *_NMA_REVIEW.html files ...")

    counts = {"PATCHED": 0, "ALREADY": 0, "NO_HEAD": 0, "NO_LANDMARK": 0}
    for hp in files:
        text = hp.read_text(encoding="utf-8", errors="replace")
        new_text, status = patch(text)
        counts[status] += 1
        if status == "PATCHED":
            print(f"  PATCH    {hp.name}")
            if not args.dry_run:
                hp.write_text(new_text, encoding="utf-8")
        elif status == "ALREADY":
            pass
        else:
            print(f"  {status}  {hp.name}")

    print(f"\n=== Summary ===")
    for k, v in counts.items():
        print(f"  {k:15s} {v}")
    if args.dry_run:
        print("  DRY RUN — nothing written.")


if __name__ == "__main__":
    main()
