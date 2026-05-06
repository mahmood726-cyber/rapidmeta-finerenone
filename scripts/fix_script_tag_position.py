"""Repair: my recent inject_network_graph.py and inject_r_validation.py used
text.replace('</body>', ..., 1) which fired on the FIRST '</body>' which in
some files is inside an inline-JS HTML-report-builder string. The literal
'</script>' inside the resulting outer <script> block prematurely closes the
script and breaks `window.RapidMeta` registration.

Fix:
  1. Remove '<script src="vendor/network-graph.js" defer></script>' and
     '<script src="vendor/r-validation-badge.js" defer></script>' that
     appear BEFORE the actual final </body> tag.
  2. Re-inject both, but only at the FINAL </body> (text.rfind).

Idempotent. Safe to re-run.
"""
from __future__ import annotations
import sys, io, re
from pathlib import Path
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

REPO = Path(__file__).resolve().parent.parent
TAGS = [
    '<script src="vendor/network-graph.js" defer></script>',
    '<script src="vendor/r-validation-badge.js" defer></script>',
]


def repair(text):
    final_body = text.rfind("</body>")
    if final_body < 0:
        return text, 0, 0

    n_removed = 0
    n_added = 0

    # Step 1: remove tags appearing BEFORE the final </body>
    for tag in TAGS:
        # First, count the tag occurrences in the prefix
        prefix = text[:final_body]
        # Match with optional surrounding whitespace and newline
        pattern = re.compile(r"\s*" + re.escape(tag) + r"\s*\n?")
        new_prefix, n = pattern.subn("", prefix)
        if n > 0:
            text = new_prefix + text[final_body:]
            n_removed += n
            final_body = text.rfind("</body>")  # recompute

    # Step 2: ensure each tag exists somewhere; if not, add at final </body>
    suffix = text[final_body:]
    for tag in TAGS:
        if tag not in text:
            text = text[:final_body] + "  " + tag + "\n" + text[final_body:]
            final_body = text.rfind("</body>")
            n_added += 1

    return text, n_removed, n_added


def main():
    files = sorted(REPO.glob("*_REVIEW.html"))
    n_files = 0
    total_removed = 0
    total_added = 0
    for hp in files:
        text = hp.read_text(encoding="utf-8", errors="replace")
        new, n_rm, n_add = repair(text)
        if n_rm > 0 or n_add > 0:
            hp.write_text(new, encoding="utf-8")
            n_files += 1
            total_removed += n_rm
            total_added += n_add
    print(f"Files repaired: {n_files}")
    print(f"  Bad tags removed: {total_removed}")
    print(f"  Tags re-added at final </body>: {total_added}")


if __name__ == "__main__":
    main()
