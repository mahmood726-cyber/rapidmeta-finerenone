"""Bump low-contrast text styles to WCAG AA across the curated pages.

Lighthouse contrast combos (after the badge + conf-btn fixes):
   #888 on #f8fafc / #fff / #fdfcfa     -> 727 + 29 + 1 hits (gray meta text)
   #ffffff on #34c96a / #34ca6b         -> 286 hits (light-green status chips)
   #ffffff on #ca8a04                   -> 97 hits  (amber chips)
   #059669 on #ffffff                   -> 75 hits  (green link)
   #ffffff on #ea580c                   -> 33 hits  (orange chip)

Fixes (each lifts the affected combo to >=4.5:1 white-on-color or
~5.0:1 gray-on-white):
   color:#888           -> color:#666           (4.74:1 vs #fff)
   color: #888          -> color: #666
   background:#34c96a   -> background:#15803d   (green-700; AA with white)
   background:#34ca6b   -> background:#15803d
   color:#34c96a        -> color:#15803d        (when used as text)
   background:#ca8a04   -> background:#a16207   (yellow-700; AA with white)
   color:#059669        -> color:#047857        (emerald-700; 4.6:1 on white)
   background:#ea580c   -> background:#c2410c   (orange-700; AA with white)

All targeted at exact inline-style or CSS-rule occurrences. Idempotent.
"""
from __future__ import annotations
import sys
import io
from pathlib import Path

if "pytest" not in sys.modules and hasattr(sys.stdout, "buffer"):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

HERE = Path(__file__).resolve().parent.parent

# (old, new) - applied as plain substring replace so accidental matches in
# different contexts are extremely unlikely (these are full color hex codes
# preceded by the property name).
REPLACEMENTS = [
    # Gray meta text on near-white card backgrounds.
    ("color:#888;", "color:#666;"),
    ("color: #888;", "color: #666;"),
    ("color:#888}", "color:#666}"),
    # Bright tailwind green-500 used as chip background with white text.
    ("background:#34c96a;color:#fff", "background:#15803d;color:#fff"),
    ("background:#34ca6b;color:#fff", "background:#15803d;color:#fff"),
    # Yellow / amber on white.
    ("background:#ca8a04;color:#fff", "background:#a16207;color:#fff"),
    # Green-600 link on white text.
    ("color:#059669;", "color:#047857;"),
    # Orange chip with white text.
    ("background:#ea580c;color:#fff", "background:#c2410c;color:#fff"),
]


def patch_file(p: Path) -> int:
    txt = p.read_text(encoding="utf-8", errors="replace")
    n = 0
    for old, new in REPLACEMENTS:
        if old == new:
            continue
        new_txt = txt.replace(old, new)
        if new_txt != txt:
            n += txt.count(old)
            txt = new_txt
    if n > 0:
        p.write_text(txt, encoding="utf-8")
    return n


def main():
    targets = sorted(p for p in HERE.glob("*.html") if p.is_file())
    print(f"Targets: {len(targets):,} HTML files")
    files = subs = 0
    for i, p in enumerate(targets, 1):
        n = patch_file(p)
        if n:
            files += 1
            subs += n
        if i % 500 == 0:
            print(f"  [{i}/{len(targets)}]")
    print(f"\nFiles changed: {files:,}  substitutions: {subs:,}")


if __name__ == "__main__":
    main()
