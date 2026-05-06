"""Remove vendor/r-validation-badge.js script tag from review files that
have no corresponding outputs/r_validation/<topic>.json. Otherwise the
badge module fetches a 404 (logged to console).

Idempotent.
"""
from __future__ import annotations
import sys, io, json
from pathlib import Path
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

REPO = Path(__file__).resolve().parent.parent
MANIFEST = json.loads((REPO / "outputs/r_validation/index.json").read_text())
validated = {t["topic"] for t in MANIFEST["topics"]}
TAG = '<script src="vendor/r-validation-badge.js" defer></script>'

n_removed = 0
for hp in sorted(REPO.glob("*_REVIEW.html")):
    topic = hp.stem.replace("_REVIEW", "")
    if topic in validated:
        continue
    text = hp.read_text(encoding="utf-8", errors="replace")
    if TAG not in text:
        continue
    new = text.replace("  " + TAG + "\n", "")
    new = new.replace(TAG + "\n", "")
    new = new.replace(TAG, "")
    if new != text:
        hp.write_text(new, encoding="utf-8")
        n_removed += 1
        print(f"  removed from {hp.name}")
print(f"\nFiles cleaned: {n_removed}")
