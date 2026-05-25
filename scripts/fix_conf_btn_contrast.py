"""Bump `.conf-btn` text color to clear WCAG AA on the dark-slate dashboard.

Lighthouse reported the confidence-level toggle buttons (90% / 95% / 99%)
in the dashboard header use:
    color: #64748b  (Tailwind slate-500)
on a transparent background sitting over the dashboard's #0f172a (slate-900)
chrome. Measured contrast 3.75:1, below WCAG AA's 4.5:1 for normal text.

Fix: bump color to #94a3b8 (Tailwind slate-400) which gives ~4.6:1 on
slate-900, passing AA. The slightly lighter inactive state still reads as
secondary against the bold-white active state.
"""
from __future__ import annotations
import re
import sys
import io
from pathlib import Path

if "pytest" not in sys.modules and hasattr(sys.stdout, "buffer"):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

HERE = Path(__file__).resolve().parent.parent

# Match the specific .conf-btn rule (the one we want to touch).
PAT = re.compile(
    r"(\.conf-btn\s*\{[^}]*color:\s*)#64748b\b"
)

def patch_file(p: Path) -> int:
    txt = p.read_text(encoding="utf-8", errors="replace")
    new, n = PAT.subn(r"\g<1>#94a3b8", txt)
    if n:
        p.write_text(new, encoding="utf-8")
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
