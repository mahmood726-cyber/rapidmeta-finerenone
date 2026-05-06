"""Inject vendor/r-validation-badge.js into all reviews that have a matching
outputs/r_validation/<topic>.json file. Idempotent.
"""
from __future__ import annotations
import sys, io, json
from pathlib import Path
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

REPO = Path(__file__).resolve().parent.parent
TAG = '<script src="vendor/r-validation-badge.js" defer></script>'

manifest = json.loads((REPO / "outputs/r_validation/index.json").read_text())
topics = {t["topic"] for t in manifest["topics"]}

n_changed = 0
for hp in sorted(REPO.glob("*_REVIEW.html")):
    topic = hp.stem.replace("_REVIEW", "")
    if topic not in topics:
        continue
    text = hp.read_text(encoding="utf-8", errors="replace")
    if "vendor/r-validation-badge.js" in text:
        continue
    if "</body>" not in text:
        continue
    new = text.replace("</body>", f"  {TAG}\n</body>", 1)
    hp.write_text(new, encoding="utf-8")
    n_changed += 1

print(f"R validation badge injected in {n_changed}/{len(topics)} reviews.")
