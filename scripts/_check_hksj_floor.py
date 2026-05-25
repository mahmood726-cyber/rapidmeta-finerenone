"""Check HKSJ floor (max(1, q*)) presence across curated REVIEW pages.

When Q < k-1 (under-dispersion), the raw HKSJ adjustment q* can be < 1,
which produces a CI NARROWER than the fixed-effect CI. Wrong. The fix is
to floor q* at 1, matching the metafor `rma(test='knha')` default behavior
since v3+.

advanced-stats.md rule:
  HKSJ floor: If Q < k-1, HKSJ narrows CI below DL — set floor:
  max(1, Q/(k-1)).
"""
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent

# Patterns:
HAS_HKSJ_RE = re.compile(r"\bhksjAdj\b|\bhksjSE\b|HKSJ", re.IGNORECASE)
HAS_FLOOR_RE = re.compile(r"Math\.max\s*\(\s*1\s*,\s*[_a-zA-Z]*[qQ][sS]tar")
HAS_QSTAR_RE = re.compile(r"\b_?qStar[A-Za-z_]*\b")

has_hksj_no_floor = []
has_hksj_with_floor = []
no_hksj = []

for p in HERE.glob("*_REVIEW.html"):
    if not p.is_file() or "AUTO" in p.name or "FULL_REVIEW" in p.name:
        continue
    txt = p.read_text(encoding="utf-8", errors="replace")
    if not HAS_HKSJ_RE.search(txt) or not HAS_QSTAR_RE.search(txt):
        no_hksj.append(p.name)
        continue
    if HAS_FLOOR_RE.search(txt):
        has_hksj_with_floor.append(p.name)
    else:
        has_hksj_no_floor.append(p.name)

print(f"HKSJ engines: {len(has_hksj_with_floor) + len(has_hksj_no_floor)}")
print(f"  with floor    : {len(has_hksj_with_floor)}")
print(f"  WITHOUT floor : {len(has_hksj_no_floor)}")
print(f"  no HKSJ       : {len(no_hksj)}")
if has_hksj_no_floor:
    print("\nFiles missing floor (sample):")
    for f in has_hksj_no_floor[:15]:
        print(f"  {f}")
