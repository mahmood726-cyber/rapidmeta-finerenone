"""Inject PRISMA-NMA flow diagram component after Search Strategy.
Idempotent.
"""
from __future__ import annotations
import sys, io, argparse, re
from pathlib import Path
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

REPO = Path("C:/Projects/Finrenone")

LIVING_INCLUDE_RE = re.compile(r'<script\s+src="vendor/living-review\.js"\s*></script>')

SCRIPT_TAG = (
    '\n    <!-- PRISMA-NMA flow diagram (Page 2021 BMJ) -->\n'
    '    <script src="vendor/prisma-flow.js"></script>\n'
)

# Find a stable landmark in Search tab. Use the Search Strategy section's closing </div>.
# Simpler: insert at end of search-strategy table. Look for the search-strategy table content.
SEARCH_TAB_END_RE = re.compile(
    r'(<section id="tab-search"[^>]*>[\s\S]*?</section>)'
)

PRISMA_PANEL = '''

                <div class="bg-slate-900/50 mt-4 p-4 rounded-lg border border-slate-800">
                    <h4 class="text-xs font-bold uppercase text-blue-400 tracking-widest mb-3">PRISMA-NMA Flow Diagram</h4>
                    <div id="prismaFlowContainer"></div>
                </div>
                '''


def patch(text):
    if 'vendor/prisma-flow.js' in text:
        return text, "ALREADY"
    # Script tag
    lr = LIVING_INCLUDE_RE.search(text)
    if lr:
        text = text[:lr.end()] + SCRIPT_TAG + text[lr.end():]
    else:
        head = text.find("</head>")
        if head < 0:
            return text, "NO_HEAD"
        text = text[:head] + SCRIPT_TAG + text[head:]
    # Container — inject before the closing tag of tab-search section
    sm = SEARCH_TAB_END_RE.search(text)
    if not sm:
        return text, "NO_SEARCH_SECTION"
    section_text = sm.group(1)
    # Insert PRISMA panel before the section's closing </section>
    insertion = section_text[:section_text.rfind('</section>')] + PRISMA_PANEL + '</section>'
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
