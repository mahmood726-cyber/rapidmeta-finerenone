"""Codemod: inject Living Review button + vendor/living-review.js script.

Idempotent. Skips files that already contain `vendor/living-review.js`.

Inserts:
  1. <script src="vendor/living-review.js"></script> after the
     attestation-badges.js include in <head>.
  2. A "Run Living Update" button next to the Search Strategy section
     header. Clicking opens the LivingReview modal.
"""
from __future__ import annotations
import sys, io, argparse, re
from pathlib import Path
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

REPO = Path(__file__).resolve().parent.parent

ATTEST_INCLUDE_RE = re.compile(r'<script\s+src="vendor/attestation-badges\.js"\s*></script>')
HEAD_CLOSE_RE = re.compile(r'</head>')

SCRIPT_TAG = (
    '\n    <!-- Living-review user-triggered re-search workflow -->\n'
    '    <script src="vendor/living-review.js"></script>\n'
)

# Look for the Search Strategy section header and inject a button
SEARCH_HEADER_RE = re.compile(
    r'(<h3 class="text-xs font-bold uppercase text-blue-400 tracking-widest">'
    r'<i class="fa-solid fa-magnifying-glass mr-2"></i>'
    r'4\. Information Sources &amp; Search Strategy '
    r'<span class="text-slate-500 ml-2">\[PRISMA #7&ndash;8, AMSTAR #4&ndash;5\]</span>'
    r'</h3>)'
)

LIVING_BUTTON = (
    '\\1'
    '<button onclick="window.LivingReview && window.LivingReview.open()" '
    'style="margin-left:12px;padding:4px 12px;background:#0891b2;color:#fff;'
    'border:1px solid #0891b2;border-radius:6px;font-size:10px;'
    'font-weight:700;cursor:pointer;text-transform:uppercase;letter-spacing:0.06em;" '
    'title="User-triggered living update — fetch new abstracts from PubMed and attest each new candidate">'
    '🔄 Run Living Update</button>'
)


def patch(text):
    if 'vendor/living-review.js' in text:
        return text, "ALREADY"
    # Script tag
    am = ATTEST_INCLUDE_RE.search(text)
    if am:
        text = text[:am.end()] + SCRIPT_TAG + text[am.end():]
    else:
        head = HEAD_CLOSE_RE.search(text)
        if not head:
            return text, "NO_HEAD"
        text = text[:head.start()] + SCRIPT_TAG + text[head.start():]
    # Button
    new_text, n = SEARCH_HEADER_RE.subn(LIVING_BUTTON, text, count=1)
    if n == 0:
        return text, "NO_SEARCH_HEADER"
    return new_text, "PATCHED"


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
        print("  DRY RUN — no files written.")


if __name__ == "__main__":
    main()
