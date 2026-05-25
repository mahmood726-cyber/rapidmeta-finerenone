"""Add aria-label to PICO input elements that lack an associated <label>.

Lighthouse reported (across FULL_REVIEW dashboards) that the editable PICO
inputs in the Protocol tab fail WCAG 1.3.1 / 4.1.2 because they have no
associated <label> element, no aria-label, no aria-labelledby, and no
title attribute. Screen-reader users hear only "edit text" with no clue
what field they're editing.

The inputs are stable IDs: p-pop, p-int, p-comp, p-out, p-subgroup. Plus
a few sibling fields (p-design, p-query). We add aria-label to each by
the input's id; idempotent (skips inputs that already have aria-label).
"""
from __future__ import annotations
import re
import sys
import io
from pathlib import Path

if "pytest" not in sys.modules and hasattr(sys.stdout, "buffer"):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

HERE = Path(__file__).resolve().parent.parent

LABELS = {
    "p-pop":      "Population (PICO)",
    "p-int":      "Intervention (PICO)",
    "p-comp":     "Comparator (PICO)",
    "p-out":      "Outcome (PICO)",
    "p-subgroup": "Subgroup analyses",
    "p-design":   "Study design",
    "p-query":    "Search query",
}


def patch_file(p: Path) -> int:
    txt = p.read_text(encoding="utf-8", errors="replace")
    n = 0
    for input_id, label in LABELS.items():
        # Match input with this id that does NOT already have aria-label.
        pat = re.compile(
            rf'(<input\b(?:(?!aria-label)[^>])*?\bid="{re.escape(input_id)}"(?:(?!aria-label)[^>])*?)(/?>)'
        )

        def add_label(m):
            nonlocal n
            n += 1
            return f'{m.group(1)} aria-label="{label}"{m.group(2)}'

        txt = pat.sub(add_label, txt)
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
    print(f"\nFiles changed: {files:,}  aria-labels added: {subs:,}")


if __name__ == "__main__":
    main()
