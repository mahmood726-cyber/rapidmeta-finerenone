"""Check which dashboards have qchisq WITHOUT the df===1 closed-form branch."""
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent

QCHISQ_BODY_RE = re.compile(
    r"const\s+qchisq\s*=\s*\([^)]*\)\s*=>\s*\{(?P<body>[\s\S]{0,3000}?)\};"
)

missing = []
present = []
for p in HERE.glob("*_REVIEW.html"):
    if not p.is_file() or "AUTO" in p.name or "FULL_REVIEW" in p.name:
        continue
    txt = p.read_text(encoding="utf-8", errors="replace")
    m = QCHISQ_BODY_RE.search(txt)
    if not m:
        continue
    body = m.group("body")
    if "df === 1" in body or "df===1" in body or "df==1" in body or "df == 1" in body:
        present.append(p.name)
    else:
        missing.append(p.name)

print(f"qchisq with df=1 closed-form: {len(present)}")
print(f"qchisq missing df=1 branch:   {len(missing)}")
if missing:
    print("\nSamples needing patch:")
    for f in missing[:15]:
        print(f"  {f}")
