"""Fix: Python None leaked into JS realData blocks.

Pattern: `tE: None, cE: None, publishedHR: None` should be `null`.

Affects only known numeric/object value fields (not strings).
Idempotent: replaces only `None` after a known field colon.
"""
from __future__ import annotations
import sys, io, re
from pathlib import Path
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

REPO = Path(__file__).resolve().parent.parent

# Fields where None should be null
FIELDS = [
    'tE', 'tN', 'cE', 'cN', 'publishedHR', 'hrLCI', 'hrUCI',
    'tE_se', 'cE_se', 'md', 'smd', 'sd1', 'sd2', 'mean1', 'mean2',
    'or', 'rr', 'logHR', 'logOR', 'logRR', 'se', 'tau2',
    'pmid', 'doi', 'year',
]
PATTERN = re.compile(
    r'\b(' + '|'.join(FIELDS) + r')\s*:\s*None\b'
)


def main():
    n_files = 0
    n_total = 0
    for hp in sorted(REPO.glob("*_REVIEW.html")):
        t = hp.read_text(encoding="utf-8", errors="replace")
        new, n = PATTERN.subn(r'\1: null', t)
        if n > 0:
            hp.write_text(new, encoding="utf-8")
            n_files += 1
            n_total += n
            print(f"  {hp.name}: {n}")
    print(f"\nFiles fixed: {n_files}; replacements: {n_total}")


if __name__ == "__main__":
    main()
