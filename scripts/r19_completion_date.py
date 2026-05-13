"""R19 — AACT primary_completion_date vs extracted year.

If extracted publication year is significantly EARLIER than the AACT
primary_completion_date (year), the extraction is wrong: publications
appear after completion, not before. Allow 1y leeway for retrospective/
interim publications.

If extracted_year < (AACT_completion_year - 1) → null year.
"""
from __future__ import annotations
import json, csv, re, sys, io
from pathlib import Path
from collections import defaultdict

if hasattr(sys.stdout, "buffer") and getattr(sys.stdout, "encoding", "").lower() != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

HERE = Path(__file__).resolve().parent.parent
OUT = HERE / "outputs" / "extraction_audit"
DATA = OUT / "data"
AACT = Path("D:/AACT-storage/AACT/2026-04-12")
DRY = "--dry-run" in sys.argv

all_trials = []
for json_p in sorted(DATA.glob("*.json")):
    if json_p.name.startswith("_"): continue
    rv = json_p.stem
    try: d = json.loads(json_p.read_text(encoding="utf-8"))
    except: continue
    rd = d.get("realData") or {}
    if not isinstance(rd, dict): continue
    for nct, t in rd.items():
        if not isinstance(t, dict): continue
        if nct.startswith("NULLED:"): continue
        if not re.match(r"^NCT\d{8}$", nct): continue
        try: y = int(t.get("year") or 0)
        except: continue
        if y < 1990 or y > 2030: continue
        all_trials.append((rv, nct, y))

print(f"Trials with valid year: {len(all_trials)}")
ncts = sorted({nct for _, nct, _ in all_trials})
target = set(ncts)

# Load primary_completion_date from studies.txt
nct_compl = {}
print("Loading studies.txt primary_completion_date…")
with open(AACT / "studies.txt", "r", encoding="utf-8", errors="replace") as f:
    reader = csv.DictReader(f, delimiter="|")
    for row in reader:
        nct = (row.get("nct_id") or "").strip().upper()
        if nct not in target: continue
        cd = (row.get("primary_completion_date") or row.get("completion_date") or "").strip()
        # date format YYYY-MM-DD
        m = re.match(r"^(\d{4})", cd)
        if m: nct_compl[nct] = int(m.group(1))
print(f"  NCTs with completion year: {len(nct_compl)}")

findings = []
for rv, nct, year in all_trials:
    cy = nct_compl.get(nct)
    if cy is None: continue
    # Allow 1y leeway for early-publication or retrospective dating
    if year < cy - 1:
        findings.append({"review": rv, "nct": nct,
                          "extracted_year": year, "aact_completion_year": cy,
                          "delta": cy - year, "fix": "NULL_YEAR"})

print(f"Year-before-completion violations: {len(findings)}")


def find_block(txt, nct):
    key_pat = re.compile(r'(["\'])' + re.escape(nct) + r'\1\s*:\s*\{')
    m = key_pat.search(txt)
    if not m: return None
    start = m.end(); depth = 1; i = start; in_str = None
    while i < len(txt) and depth > 0:
        ch = txt[i]
        if in_str:
            if ch == "\\": i += 2; continue
            if ch == in_str: in_str = None
        else:
            if ch in ('"', "'"): in_str = ch
            elif ch == "{": depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0: return (m.start(), i+1, start, i)
        i += 1
    return None


def null_field_in_block(txt, body_start, body_end, field):
    body = txt[body_start:body_end]
    new_body, n = re.subn(
        r'((["\']?)' + re.escape(field) + r'\2\s*:\s*)(?:["\'][^"\']*["\']|[0-9.eE+-]+|true|false)(?=\s*[,}])',
        r'\1null', body, flags=re.IGNORECASE)
    if n == 0: return txt, False
    return txt[:body_start] + new_body + txt[body_end:], True


applied = []
n_fix = 0
seen = set()
for f in findings:
    if (f["review"], f["nct"]) in seen: continue
    seen.add((f["review"], f["nct"]))
    html_path = HERE / f"{f['review']}.html"
    if not html_path.exists(): continue
    txt = html_path.read_text(encoding="utf-8")
    block = find_block(txt, f["nct"])
    if not block: continue
    _, _, bs, be = block
    new_txt, ok = null_field_in_block(txt, bs, be, "year")
    if ok:
        if not DRY: html_path.write_text(new_txt, encoding="utf-8")
        applied.append({**f, "status": "NULLED_YEAR"})
        n_fix += 1
    else:
        applied.append({**f, "status": "ALREADY_NULL"})

out_p = OUT / "r19_completion_date.json"
out_p.write_text(json.dumps({"findings": findings, "applied": applied,
                              "summary": {"year_nulls": n_fix}},
                             indent=2, ensure_ascii=False), encoding="utf-8")
print(f"\n{'DRY-RUN ' if DRY else ''}Year nulls (year < completion-1): {n_fix}")
