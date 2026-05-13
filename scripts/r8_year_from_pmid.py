"""R8 — year-from-PMID consistency check.

Each cached PubMed entry's metadata typically includes publication_date.year
(we didn't capture this explicitly in fetch_pubmed_batch.py but the PMID
itself is a strong proxy: PubMed assigns PMIDs roughly chronologically at
~1.5M/year). For a more reliable signal we re-parse the abstract for the
publication-date if it was retained.

For now: compare extracted year to PMID's known approximate era using a
calibrated PMID→year function. If |Δ| > 3 years, null the extracted year.

PMID era anchors (approximate, valid for monotonic PubMed indexing):
  PMID  5,000,000  ≈ year 1995
  PMID 10,000,000  ≈ year 2000
  PMID 15,000,000  ≈ year 2005
  PMID 20,000,000  ≈ year 2010
  PMID 25,000,000  ≈ year 2014
  PMID 30,000,000  ≈ year 2018
  PMID 35,000,000  ≈ year 2022
  PMID 38,000,000  ≈ year 2024
  PMID 40,000,000  ≈ year 2025

Source: https://pubmed.ncbi.nlm.nih.gov/ historical PMID counts; widely
documented in bibliometric literature.
"""
from __future__ import annotations
import json, re, sys, io
from pathlib import Path
from collections import defaultdict, Counter

if hasattr(sys.stdout, "buffer") and getattr(sys.stdout, "encoding", "").lower() != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

HERE = Path(__file__).resolve().parent.parent
OUT = HERE / "outputs" / "extraction_audit"
DATA = OUT / "data"
DRY = "--dry-run" in sys.argv

# Calibrated PMID → year (piecewise linear)
ANCHORS = [
    (1, 1975),
    (5_000_000, 1995),
    (10_000_000, 2000),
    (15_000_000, 2005),
    (20_000_000, 2010),
    (25_000_000, 2014),
    (30_000_000, 2018),
    (33_000_000, 2020),
    (35_000_000, 2022),
    (38_000_000, 2024),
    (40_000_000, 2025),
    (42_000_000, 2026),
]


def pmid_to_year(pmid_int):
    """Linear interpolation between anchors."""
    for i in range(len(ANCHORS) - 1):
        lo_pmid, lo_y = ANCHORS[i]
        hi_pmid, hi_y = ANCHORS[i+1]
        if lo_pmid <= pmid_int <= hi_pmid:
            frac = (pmid_int - lo_pmid) / (hi_pmid - lo_pmid)
            return lo_y + frac * (hi_y - lo_y)
    # Past anchors
    if pmid_int > ANCHORS[-1][0]: return ANCHORS[-1][1]
    return ANCHORS[0][1]


# Load all trials
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
        all_trials.append((rv, nct, t))

print(f"Total trials: {len(all_trials)}")


def f_(v):
    try: return float(v) if v is not None else None
    except: return None


def i_(v):
    try: return int(v) if v is not None else None
    except: return None


findings = []
for rv, nct, t in all_trials:
    pmid_str = (t.get("pmid") or "").strip()
    year = i_(t.get("year"))
    if year is None or year < 1990 or year > 2030: continue
    if not pmid_str.isdigit(): continue
    if not (6 <= len(pmid_str) <= 9): continue
    pmid = int(pmid_str)
    if pmid < 1_000_000: continue
    expected = pmid_to_year(pmid)
    delta = abs(year - expected)
    if delta > 3:
        findings.append({
            "review": rv, "nct": nct, "pmid": pmid, "year_extracted": year,
            "year_implied_by_PMID": round(expected, 1),
            "delta_years": round(delta, 1),
        })

print(f"PMID-year mismatches (|Δ| > 3y): {len(findings)}")


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
n_year = n_pmid = 0
seen_year = seen_pmid = set()
for f in findings:
    rv, nct = f["review"], f["nct"]
    html_path = HERE / f"{rv}.html"
    if not html_path.exists():
        applied.append({**f, "status": "FILE_MISSING"}); continue
    txt = html_path.read_text(encoding="utf-8")
    block = find_block(txt, nct)
    if not block:
        applied.append({**f, "status": "BLOCK_NOT_FOUND"}); continue
    _, _, bs, be = block
    # If delta is HUGE (>10y), the PMID is likely wrong (recall PubMed
    # misattribution pattern); null PMID. If delta is moderate (3-10y),
    # the year is more likely off; null year.
    if f["delta_years"] > 10:
        new_txt, ok = null_field_in_block(txt, bs, be, "pmid")
        if ok:
            if not DRY: html_path.write_text(new_txt, encoding="utf-8")
            applied.append({**f, "status": "NULLED_PMID"}); n_pmid += 1
        else:
            applied.append({**f, "status": "PMID_ALREADY_NULL"})
    else:
        new_txt, ok = null_field_in_block(txt, bs, be, "year")
        if ok:
            if not DRY: html_path.write_text(new_txt, encoding="utf-8")
            applied.append({**f, "status": "NULLED_YEAR"}); n_year += 1
        else:
            applied.append({**f, "status": "YEAR_ALREADY_NULL"})

out_p = OUT / "r8_year_from_pmid.json"
out_p.write_text(json.dumps({"findings": findings, "applied": applied,
                              "counts": {"year_nulls": n_year, "pmid_nulls_for_huge_delta": n_pmid}},
                             indent=2, ensure_ascii=False), encoding="utf-8")
print(f"\n{'DRY-RUN ' if DRY else ''}Fixes:")
print(f"  Year nulls (|Δ| 3-10y): {n_year}")
print(f"  PMID nulls (|Δ| > 10y):  {n_pmid}")
