"""Inject vendor/_panel-helper.js + 5 analysis-panel scripts into every
*_REVIEW.html. Idempotent. Inserts immediately before the final </body>.

Modules added:
  _panel-helper.js  (loaded first; shared utilities)
  nnt-panel.js
  leave-one-out.js
  grade-sof.js
  cumulative-ma.js
  baujat-plot.js
  tsa-panel.js
"""
from __future__ import annotations
import sys, io
from pathlib import Path
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

REPO = Path(__file__).resolve().parent.parent

# Order matters: helper first, then panels (defer so they execute after helper loads)
TAGS = [
    '<script src="vendor/_panel-helper.js" defer></script>',
    '<script src="vendor/nnt-panel.js" defer></script>',
    '<script src="vendor/leave-one-out.js" defer></script>',
    '<script src="vendor/grade-sof.js" defer></script>',
    '<script src="vendor/cumulative-ma.js" defer></script>',
    '<script src="vendor/baujat-plot.js" defer></script>',
    '<script src="vendor/tsa-panel.js" defer></script>',
    # NMA-only modules — self-guard and exit silently in pairwise reviews,
    # so it's safe to inject everywhere.
    '<script src="vendor/nma-league-table.js" defer></script>',
    '<script src="vendor/nma-forest-all-treatments.js" defer></script>',
    # Master accordion: consolidates all of the above into one ~31 px
    # collapsed row so the RapidMeta tabs stay above the fold.
    '<script src="vendor/advanced-stats-suite.js" defer></script>',
]


def patch(text: str) -> tuple[str, int]:
    final_body = text.rfind("</body>")
    if final_body < 0:
        return text, 0
    n_added = 0
    block = ""
    for tag in TAGS:
        if tag in text:
            continue
        block += "  " + tag + "\n"
        n_added += 1
    if n_added == 0:
        return text, 0
    new_text = text[:final_body] + block + text[final_body:]
    return new_text, n_added


def main():
    files = sorted(REPO.glob("*_REVIEW.html"))
    n_files, n_total = 0, 0
    for hp in files:
        text = hp.read_text(encoding="utf-8", errors="replace")
        new, n = patch(text)
        if n > 0:
            hp.write_text(new, encoding="utf-8")
            n_files += 1
            n_total += n
    print(f"Files updated: {n_files}")
    print(f"Tags inserted: {n_total}")


if __name__ == "__main__":
    main()
