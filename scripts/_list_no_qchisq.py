"""List curated REVIEW files that lack the qchisq helper anchor."""
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
QCHISQ_RE = re.compile(r"const\s+qchisq\s*=\s*\(")
SUBSTANTIVE_RE = re.compile(r"const\s+(?:rma|computeForestPool|sWR|tau2)", re.IGNORECASE)

without = []
without_no_engine = []
for p in HERE.glob("*_REVIEW.html"):
    if not p.is_file() or "AUTO" in p.name or "FULL_REVIEW" in p.name:
        continue
    txt = p.read_text(encoding="utf-8", errors="replace")
    if not QCHISQ_RE.search(txt):
        if "tQuantile" in txt or "tau2" in txt:
            without.append(p.name)
        else:
            without_no_engine.append(p.name)

print(f"Lacks qchisq but has stat engine: {len(without)}")
for f in without:
    print(f"  {f}")
print(f"\nLacks qchisq AND no stat engine (utility pages): {len(without_no_engine)}")
for f in without_no_engine[:10]:
    print(f"  {f}")
