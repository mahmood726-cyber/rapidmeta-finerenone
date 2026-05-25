"""Fix WCAG AA color-contrast on the rapidmeta-integrity-badge.

Lighthouse reports that the TRUSTWORTHY green badge at the top of every
AUTO_REVIEW + AUTO_FULL_REVIEW page fails WCAG AA contrast (4.5:1 for
normal text). The dominant problem combos:

  white text on #16a34a (Tailwind green-600)        -> 3.29:1
  #ecf8f1 (opacity-adjusted) on #16a34a             -> 3.02:1
  #f3faf6 (opacity-adjusted) on #16a34a             -> 3.10:1
  #c5e8d2 (opacity-adjusted) on #16a34a             -> 2.48:1

Fix: bump the background to a darker green that gives white text >=4.5:1
contrast, and drop the opacity attenuators on inner text:

  background  #16a34a -> #15803d  (Tailwind green-700, white contrast 4.86:1)
  border      #15803d -> #14532d  (Tailwind green-900, visual hierarchy)
  opacity:0.92|0.95|0.75 on text spans -> removed (full white)
  rgba(255,255,255,0.18) chip bg  -> rgba(255,255,255,0.32)
  rgba(255,255,255,0.15) code bg  -> rgba(255,255,255,0.28)

This is a single mechanical CSS swap across every page that ships the
badge. Idempotent — re-running on already-fixed badges is a no-op.
"""
from __future__ import annotations
import re
import sys
import io
from pathlib import Path

if "pytest" not in sys.modules and hasattr(sys.stdout, "buffer"):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

HERE = Path(__file__).resolve().parent.parent

BADGE_RE = re.compile(
    r'<div id="rapidmeta-integrity-badge"[^>]*>'
)

REPLACEMENTS = [
    # Background + border on the outer container.
    ("background:#16a34a;color:#fff;padding:12px 20px",
     "background:#15803d;color:#fff;padding:12px 20px"),
    ("border-bottom:3px solid #15803d;",
     "border-bottom:3px solid #14532d;"),
    # Inner text spans — drop the opacity attenuators that mute white on green.
    ('font-size:11.5px;opacity:0.92', 'font-size:11.5px'),
    ('font-size:12.5px;opacity:0.95', 'font-size:12.5px'),
    ('font-size:10.5px;opacity:0.75', 'font-size:10.5px'),
    # Translucent overlay chips: bump the white-alpha so the contrast lifts.
    ('background:rgba(255,255,255,0.18);padding:2px 6px',
     'background:rgba(255,255,255,0.32);padding:2px 6px'),
    ('background:rgba(255,255,255,0.15);padding:1px 4px',
     'background:rgba(255,255,255,0.28);padding:1px 4px'),
]


def patch_file(p: Path) -> int:
    txt = p.read_text(encoding="utf-8", errors="replace")
    if not BADGE_RE.search(txt):
        return 0
    n = 0
    for old, new in REPLACEMENTS:
        if old == new:
            continue
        new_txt = txt.replace(old, new)
        if new_txt != txt:
            # Count actual occurrences replaced (not all-text new-substring count,
            # which over-counts when `new` was already present as a partial match
            # in unrelated CSS like font-size:10.5px on a different element).
            n += txt.count(old)
            txt = new_txt
    if n > 0:
        p.write_text(txt, encoding="utf-8")
    return n


def main():
    targets = sorted(p for p in HERE.glob("*.html") if p.is_file())
    print(f"Targets: {len(targets):,} HTML files")
    files_changed = total = 0
    for i, p in enumerate(targets, 1):
        n = patch_file(p)
        if n:
            files_changed += 1
            total += n
        if i % 500 == 0:
            print(f"  [{i}/{len(targets)}]")
    print(f"\nFiles changed: {files_changed:,}")
    print(f"Total CSS substitutions: {total:,}")


if __name__ == "__main__":
    main()
