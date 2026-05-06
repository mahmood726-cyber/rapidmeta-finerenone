"""Inject outcome-switching audit panel into Extraction tab. Idempotent."""
from __future__ import annotations
import sys, io, argparse, re
from pathlib import Path
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

REPO = Path("C:/Projects/Finrenone")

PRISMA_INCLUDE_RE = re.compile(r'<script\s+src="vendor/prisma-flow\.js"\s*></script>')

SCRIPT_TAG = (
    '\n    <!-- Outcome-switching audit (Goldacre COMPare 2019) -->\n'
    '    <script src="vendor/outcome-switching.js"></script>\n'
)

EXTRACT_TAB_END_RE = re.compile(
    r'(<section id="tab-extract"[^>]*>[\s\S]*?</section>)'
)

PANEL = '''

                <div class="bg-slate-900/50 mt-4 p-4 rounded-lg border border-slate-800">
                    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:10px;">
                        <h4 class="text-xs font-bold uppercase text-blue-400 tracking-widest">Outcome-Switching Audit (registry vs paper)</h4>
                        <button onclick="window.OutcomeSwitching && window.OutcomeSwitching.render('#osAudit')"
                            style="padding:4px 10px;background:#0891b2;color:#fff;border:none;border-radius:4px;font-size:10px;font-weight:700;cursor:pointer;">
                            Run audit
                        </button>
                    </div>
                    <div id="osAudit"><span style="color:#64748b;font-size:11px;font-style:italic;">Click "Run audit" to compare each trial's reported endpoint against the AACT-registered primary outcome (COMPare-style; Goldacre 2019).</span></div>
                </div>
                '''


def patch(text):
    if 'vendor/outcome-switching.js' in text:
        return text, "ALREADY"
    pm = PRISMA_INCLUDE_RE.search(text)
    if pm:
        text = text[:pm.end()] + SCRIPT_TAG + text[pm.end():]
    else:
        head = text.find("</head>")
        if head < 0:
            return text, "NO_HEAD"
        text = text[:head] + SCRIPT_TAG + text[head:]
    sm = EXTRACT_TAB_END_RE.search(text)
    if not sm:
        return text, "NO_EXTRACT_SECTION"
    section_text = sm.group(1)
    insertion = section_text[:section_text.rfind('</section>')] + PANEL + '</section>'
    text = text[:sm.start()] + insertion + text[sm.end():]
    return text, "PATCHED"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    files = sorted(REPO.glob("*_REVIEW.html"))
    print(f"Patching {len(files)} review HTMLs ...")
    counts = {}
    for hp in files:
        text = hp.read_text(encoding="utf-8", errors="replace")
        new_text, status = patch(text)
        counts[status] = counts.get(status, 0) + 1
        if status == "PATCHED" and not args.dry_run:
            hp.write_text(new_text, encoding="utf-8")

    print(f"\n=== Summary ===")
    for k, v in sorted(counts.items(), key=lambda x: -x[1]):
        print(f"  {k:25s} {v}")
    if args.dry_run:
        print("  DRY RUN — nothing written.")


if __name__ == "__main__":
    main()
