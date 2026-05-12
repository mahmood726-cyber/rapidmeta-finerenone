"""Fix the one real R5 finding: ROCKET-AF in DOAC_AF_NMA_REVIEW has tE/cE
from the per-protocol primary analysis but HR/CI from the ITT secondary
analysis. Per Patel NEJM 2011 PMID 21830957, the ITT-full-period
analysis (which gave HR 0.88 [0.74-1.03]) had 269 events on rivaroxaban
vs 306 on warfarin. Update event counts to match the HR/CI."""
from __future__ import annotations
import json, re, sys, io
from pathlib import Path

if hasattr(sys.stdout, "buffer") and getattr(sys.stdout, "encoding", "").lower() != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

HERE = Path(__file__).resolve().parent.parent
DRY = "--dry-run" in sys.argv

# Target: ROCKET-AF in DOAC_AF_NMA_REVIEW
rv = "DOAC_AF_NMA_REVIEW"
nct = "NCT00403767"
html_path = HERE / f"{rv}.html"

txt = html_path.read_text(encoding="utf-8")
key_pat = re.compile(r'(["\'])' + re.escape(nct) + r'\1\s*:\s*\{')
m = key_pat.search(txt)
if not m:
    print(f"NCT not found")
    sys.exit(1)

start = m.end(); depth = 1; i = start; in_str = None
while i < len(txt) and depth > 0:
    ch = txt[i]
    if in_str:
        if ch == "\\": i += 2; continue
        if ch == in_str: in_str = None
    else:
        if ch in ('"',"'"): in_str = ch
        elif ch == "{": depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0: break
    i += 1
body_start, body_end = start, i
body = txt[body_start:body_end]

# Update tE: 188 → 269, cE: 241 → 306 (ITT full-period analysis matching HR 0.88)
changes = []
for field, old, new in [("tE", "188", "269"), ("cE", "241", "306")]:
    pat = re.compile(
        r'((["\']?)' + re.escape(field) + r'\2\s*:\s*)' + re.escape(old) + r'(?=\s*[,}])',
        re.IGNORECASE
    )
    new_body, n = pat.subn(r"\g<1>" + new, body)
    if n > 0:
        body = new_body
        changes.append(f"{field}: {old} → {new}")
    else:
        changes.append(f"{field}: pattern not matched (already changed?)")

# Add a comment to record provenance
# Find the publishedHR position and add inline note
new_txt = txt[:body_start] + body + txt[body_end:]

if not DRY:
    html_path.write_text(new_txt, encoding="utf-8")
print(f"{'DRY-RUN ' if DRY else ''}ROCKET-AF in {rv}:")
for c in changes:
    print(f"  {c}")
print("\nReason: tE/cE were extracted from per-protocol PRIMARY analysis (188/241)")
print("but HR/CI 0.88/[0.74-1.03] was extracted from ITT full-period SECONDARY.")
print("Updated event counts to match the analysis-set of the HR (ITT 269/306).")
print("Per Patel NEJM 2011 PMID 21830957 DOI 10.1056/NEJMoa1009638.")
