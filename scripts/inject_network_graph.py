"""Inject vendor/network-graph.js script tag into all NMA review HTMLs.
Idempotent.
"""
from __future__ import annotations
import sys, io, re
from pathlib import Path
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

REPO = Path(__file__).resolve().parent.parent
SCRIPT_TAG = '<script src="vendor/network-graph.js" defer></script>'

def patch(text):
    if "vendor/network-graph.js" in text:
        return text, False
    # Insert before closing </body>
    if "</body>" not in text:
        return text, False
    new = text.replace("</body>", f"  {SCRIPT_TAG}\n</body>", 1)
    return new, True


def main():
    files = sorted(REPO.glob("*_REVIEW.html"))
    eligible = []
    for hp in files:
        t = hp.read_text(encoding="utf-8", errors="replace")
        if 'id="nma-network-plot"' in t:
            eligible.append(hp)
    print(f"NMA reviews with network plot container: {len(eligible)}")

    n_changed = 0
    for hp in eligible:
        t = hp.read_text(encoding="utf-8", errors="replace")
        new, changed = patch(t)
        if changed:
            hp.write_text(new, encoding="utf-8")
            n_changed += 1
    print(f"Files updated: {n_changed}")


if __name__ == "__main__":
    main()
