"""Fix WCAG 1.3.1 heading-order violation on AUTO_REVIEW lite pages.

Lite pages currently jump from <h1> (page title) directly to <h3>
(subsection titles) — skipping <h2>. WCAG/Lighthouse flag this because
screen-reader users navigating by heading levels lose context.

Two viable fixes:
  A. Insert <h2> tab-name headings between <h1> and the per-tab <h3>s
  B. Promote every <h3> in the page body to <h2>

(A) needs per-page logic — it's the more semantically correct fix but
each tab section would need its own <h2>. (B) is mechanical and
preserves the visual layout (font-size set inline, not via tag).

Going with (B). The styled appearance is unchanged because every
<h3> has explicit inline `font-size:14px` and color — the heading-level
change is purely structural.

Only operates on *_AUTO_REVIEW.html pages (the lite template); curated
*_REVIEW.html pages have their own heading conventions and aren't flagged.
"""
from __future__ import annotations
import re
import sys
import io
from pathlib import Path

if "pytest" not in sys.modules and hasattr(sys.stdout, "buffer"):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

HERE = Path(__file__).resolve().parent.parent

H3_OPEN = re.compile(r"<h3(\b[^>]*)>")
H3_CLOSE = re.compile(r"</h3>")


def patch_file(p: Path) -> int:
    txt = p.read_text(encoding="utf-8", errors="replace")
    new_txt = H3_OPEN.sub(r"<h2\1>", txt)
    new_txt = H3_CLOSE.sub("</h2>", new_txt)
    if new_txt == txt:
        return 0
    p.write_text(new_txt, encoding="utf-8")
    return new_txt.count("<h2") - txt.count("<h2")


def main():
    # AUTO_REVIEW lite ONLY (not _AUTO_FULL_REVIEW.html, which uses the
    # cloned-from-DUPILUMAB template with its own heading structure).
    targets = sorted(
        p for p in HERE.glob("*_AUTO_REVIEW.html")
        if p.is_file() and "FULL_REVIEW" not in p.name
    )
    print(f"Targets: {len(targets):,} AUTO_REVIEW lite files")
    files = subs = 0
    for i, p in enumerate(targets, 1):
        n = patch_file(p)
        if n:
            files += 1
            subs += n
        if i % 200 == 0:
            print(f"  [{i}/{len(targets)}]")
    print(f"\nFiles changed: {files:,}  h3->h2 promotions: {subs:,}")


if __name__ == "__main__":
    main()
