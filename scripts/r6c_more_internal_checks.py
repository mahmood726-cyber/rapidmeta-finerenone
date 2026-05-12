"""R6c — five more internal-consistency checks.

C10 — NAME_ON_DIFFERENT_NCTS
  Same trial name (acronym, ≥3 chars, non-generic) appearing on DIFFERENT
  NCTs across the corpus. Real trials have one NCT — disagreement means
  at least one (NCT,name) pair is wrong. Keep the most-common name→NCT
  mapping (mode); null PMID on minority occurrences.

C13 — EFFECT_OUT_OF_BOUNDS
  publishedHR < 0.01 or > 100. Even pre-correction zero-cell-inflated
  ORs rarely exceed 100; values below 0.01 mean a 99% reduction which
  is nearly always a transcription error. ACTION: null HR + CI.

C14 — YEAR_INCONSISTENT_ACROSS_REVIEWS
  Same NCT appears in ≥2 reviews with DIFFERENT publication years
  (|Δ| ≥ 2). Same trial → one true year. Keep modal year; null
  divergent year(s).

C16 — HR_DISAGREEMENT_ACROSS_REVIEWS
  Same NCT appears in ≥2 reviews with HR values disagreeing by >2× (i.e.,
  |log ratio| > log 2). Different outcomes can legitimately give different
  HRs (R5 confirmed FIDELIO-renal vs FIDELIO-CV is valid), so we don't
  null. Instead we FLAG for human re-review — no auto-fix. (Internal check
  with FLAG-only output; no destructive action.)

C19 — NCT_ACRONYMS_VS_NAME
  Within a single review, `nctAcronyms` dict maps NCT→acronym separately
  from `realData[NCT].name`. If they disagree, one is wrong. Keep the
  name field (more authoritative); null the nctAcronyms entry.
"""
from __future__ import annotations
import json, re, sys, io, math
from pathlib import Path
from collections import defaultdict, Counter

if hasattr(sys.stdout, "buffer") and getattr(sys.stdout, "encoding", "").lower() != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

HERE = Path(__file__).resolve().parent.parent
OUT = HERE / "outputs" / "extraction_audit"
DATA = OUT / "data"
DRY = "--dry-run" in sys.argv


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


def f(v):
    try: return float(v) if v is not None else None
    except: return None


def i_(v):
    try: return int(v) if v is not None else None
    except: return None


# Load
all_trials = []
review_data = {}
for json_p in sorted(DATA.glob("*.json")):
    if json_p.name.startswith("_"): continue
    rv = json_p.stem
    try: d = json.loads(json_p.read_text(encoding="utf-8"))
    except: continue
    review_data[rv] = d
    rd = d.get("realData") or {}
    if not isinstance(rd, dict): continue
    for nct, t in rd.items():
        if not isinstance(t, dict): continue
        if nct.startswith("NULLED:"): continue
        all_trials.append((rv, nct, t))

print(f"Total trials: {len(all_trials)}  reviews: {len(review_data)}")

GENERIC_NAME_RE = re.compile(
    r"^(NCT\d|Study|Trial \d|Phase \d|C\d{3}|N0\d|PER-\d|[A-Z]+-\d+)$",
    re.IGNORECASE)


# ─── C10: Name on different NCTs ───
def check_c10():
    findings = []
    name_to_ncts = defaultdict(list)  # name (canonical lower) → [(rv, nct, original_name)]
    for rv, nct, t in all_trials:
        name = (t.get("name") or "").strip()
        if not name or len(name) < 3: continue
        if GENERIC_NAME_RE.match(name): continue
        norm = name.lower()
        name_to_ncts[norm].append((rv, nct, name))
    for norm, entries in name_to_ncts.items():
        distinct_ncts = {e[1] for e in entries}
        if len(distinct_ncts) < 2: continue
        # Find modal NCT
        nct_counter = Counter(e[1] for e in entries)
        modal_nct, modal_count = nct_counter.most_common(1)[0]
        # Anything not the modal NCT is suspect
        for rv, nct, orig_name in entries:
            if nct == modal_nct: continue
            findings.append({
                "check": "C10_NAME_DIFFERENT_NCTS",
                "review": rv, "nct": nct, "name": orig_name,
                "modal_nct": modal_nct, "modal_count": modal_count,
                "fix": "NULL_PMID",  # conservative — don't null NCT, just provenance
            })
    return findings


# ─── C13: HR out of bounds (only for ratio-scale estimands) ───
def check_c13():
    """For ratio-scale estimands (HR/RR/OR), publishedHR must be in (0, 1000].
    Specific actions:
      - hr == 0 with et in {RR, HR}: legitimate zero-events case → no action
      - hr > 100 with empty estimandType: OR mislabel → set estimandType=OR
      - 0 < hr < 0.01: transcription error → null HR + CI
      - hr > 100 with et != OR: transcription or OR mislabel → set estimandType=OR
    """
    findings = []
    for rv, nct, t in all_trials:
        hr = f(t.get("publishedHR"))
        et = (t.get("estimandType") or "").upper()
        if hr is None: continue
        if et in ("MD", "SMD", "RD", "WMD"): continue
        if hr == 0:
            # Zero events in active arm — legitimate for some outcomes
            continue
        if 0 < hr < 0.01:
            findings.append({
                "check": "C13_EFFECT_OUT_OF_BOUNDS",
                "review": rv, "nct": nct,
                "publishedHR": hr, "estimandType": et,
                "fix": "NULL_HR_AND_CI",
            })
        elif hr > 100 and et != "OR":
            # Likely OR mislabel — set estimandType=OR (don't null value)
            findings.append({
                "check": "C13_EFFECT_OUT_OF_BOUNDS_OR_MISLABEL",
                "review": rv, "nct": nct,
                "publishedHR": hr, "estimandType": et,
                "fix": "SET_ESTIMAND_OR",
            })
        elif hr > 1000:
            # Even OR shouldn't exceed 1000; transcription error
            findings.append({
                "check": "C13_EFFECT_OUT_OF_BOUNDS",
                "review": rv, "nct": nct,
                "publishedHR": hr, "estimandType": et,
                "fix": "NULL_HR_AND_CI",
            })
    return findings


# ─── C14: year inconsistent across reviews ───
def check_c14():
    findings = []
    nct_years = defaultdict(list)  # nct → [(rv, year)]
    for rv, nct, t in all_trials:
        y = i_(t.get("year"))
        if y is None or y < 1990 or y > 2030: continue
        nct_years[nct].append((rv, y))
    for nct, ys in nct_years.items():
        if len({y for _, y in ys}) < 2: continue
        y_counter = Counter(y for _, y in ys)
        modal_year, modal_count = y_counter.most_common(1)[0]
        for rv, y in ys:
            if y == modal_year: continue
            if abs(y - modal_year) < 2: continue  # small drift OK
            findings.append({
                "check": "C14_YEAR_INCONSISTENT",
                "review": rv, "nct": nct, "year": y,
                "modal_year": modal_year, "delta": abs(y - modal_year),
                "fix": "NULL_YEAR",
            })
    return findings


# ─── C16: HR disagreement across reviews (flag only — no auto-fix) ───
def check_c16():
    findings = []
    nct_hrs = defaultdict(list)
    for rv, nct, t in all_trials:
        hr = f(t.get("publishedHR"))
        et = (t.get("estimandType") or "").upper()
        if hr is None or hr <= 0: continue
        nct_hrs[nct].append((rv, hr, et))
    for nct, hrs in nct_hrs.items():
        if len(hrs) < 2: continue
        # Compare each pair
        same_estimand_hrs = defaultdict(list)
        for rv, hr, et in hrs:
            same_estimand_hrs[et].append((rv, hr))
        for et, lst in same_estimand_hrs.items():
            if len(lst) < 2: continue
            log_hrs = [(rv, math.log(hr)) for rv, hr in lst if hr > 0]
            if not log_hrs: continue
            min_lhr = min(l for _, l in log_hrs)
            max_lhr = max(l for _, l in log_hrs)
            if max_lhr - min_lhr > math.log(2):  # >2× ratio
                for rv, l in log_hrs:
                    findings.append({
                        "check": "C16_HR_DISAGREEMENT_FLAG_ONLY",
                        "review": rv, "nct": nct, "estimandType": et,
                        "log_HR": round(l, 3),
                        "log_range": round(max_lhr - min_lhr, 3),
                        "fix": "FLAG_ONLY",
                    })
    return findings


# ─── C19: nctAcronyms vs realData.name ───
def check_c19():
    findings = []
    for rv, d in review_data.items():
        ac = d.get("nctAcronyms") or {}
        rd = d.get("realData") or {}
        if not isinstance(ac, dict) or not isinstance(rd, dict): continue
        for nct, acronym_in_dict in ac.items():
            if nct.startswith("NULLED:"): continue
            t = rd.get(nct)
            if not isinstance(t, dict): continue
            name = (t.get("name") or "").strip()
            if not name or not acronym_in_dict: continue
            if name.lower() != str(acronym_in_dict).strip().lower():
                findings.append({
                    "check": "C19_ACRONYMS_VS_NAME",
                    "review": rv, "nct": nct,
                    "nctAcronyms_says": acronym_in_dict,
                    "realData_name": name,
                    "fix": "FLAG_ONLY",  # nctAcronyms is auxiliary, don't auto-modify
                })
    return findings


all_findings = []
for chk in [check_c10, check_c13, check_c14, check_c16, check_c19]:
    all_findings.extend(chk())

by_check = Counter(f["check"] for f in all_findings)
print(f"\nFindings:")
for c, n in by_check.most_common():
    print(f"  {c}: {n}")

# Apply (skip FLAG_ONLY)
def set_field_in_block(txt, body_start, body_end, field, value):
    body = txt[body_start:body_end]
    new_body, n = re.subn(
        r'((["\']?)' + re.escape(field) + r'\2\s*:\s*)(?:["\'][^"\']*["\']|[0-9.eE+-]+|true|false|null)(?=\s*[,}])',
        r'\1"' + value + '"', body, flags=re.IGNORECASE)
    if n == 0: return txt, False
    return txt[:body_start] + new_body + txt[body_end:], True


log = []
n_pmid = n_hr = n_year = n_estimand = 0
seen = set()
for finding in all_findings:
    rv, nct, fix = finding["review"], finding["nct"], finding["fix"]
    if fix == "FLAG_ONLY":
        log.append({**finding, "status": "FLAGGED_NO_FIX"})
        continue
    key = (rv, nct, fix)
    if key in seen: continue
    seen.add(key)
    html_path = HERE / f"{rv}.html"
    if not html_path.exists():
        log.append({**finding, "status": "FILE_MISSING"})
        continue
    txt = html_path.read_text(encoding="utf-8")
    block = find_block(txt, nct)
    if not block:
        log.append({**finding, "status": "BLOCK_NOT_FOUND"})
        continue
    _, _, bs, be = block

    if fix == "NULL_PMID":
        new_txt, ok = null_field_in_block(txt, bs, be, "pmid")
        if ok:
            if not DRY: html_path.write_text(new_txt, encoding="utf-8")
            log.append({**finding, "status": "NULLED_PMID"})
            n_pmid += 1
        else:
            log.append({**finding, "status": "PMID_ALREADY_NULL"})
    elif fix == "NULL_HR_AND_CI":
        for fld in ("publishedHR", "hrLCI", "hrUCI"):
            new_txt, ok = null_field_in_block(txt, bs, be, fld)
            if ok:
                txt = new_txt
                block = find_block(txt, nct)
                if not block: break
                _, _, bs, be = block
        if not DRY: html_path.write_text(txt, encoding="utf-8")
        log.append({**finding, "status": "NULLED_HR_CI"})
        n_hr += 1
    elif fix == "NULL_YEAR":
        new_txt, ok = null_field_in_block(txt, bs, be, "year")
        if ok:
            if not DRY: html_path.write_text(new_txt, encoding="utf-8")
            log.append({**finding, "status": "NULLED_YEAR"})
            n_year += 1
        else:
            log.append({**finding, "status": "YEAR_ALREADY_NULL"})
    elif fix == "SET_ESTIMAND_OR":
        new_txt, ok = set_field_in_block(txt, bs, be, "estimandType", "OR")
        if ok:
            if not DRY: html_path.write_text(new_txt, encoding="utf-8")
            log.append({**finding, "status": "SET_ESTIMAND_OR"})
            n_estimand += 1
        else:
            log.append({**finding, "status": "ESTIMAND_NOT_SET"})

n_flag = sum(1 for r in log if r["status"] == "FLAGGED_NO_FIX")
out_p = OUT / "r6c_internal_consistency.json"
out_p.write_text(json.dumps({"findings": all_findings, "fixes": log,
                              "counts": {"PMID_nulls": n_pmid,
                                         "HR_CI_nulls": n_hr,
                                         "year_nulls": n_year,
                                         "estimand_or_set": n_estimand,
                                         "flag_only": n_flag}},
                             indent=2, ensure_ascii=False), encoding="utf-8")
print(f"\n{'DRY-RUN ' if DRY else ''}Fixes:")
print(f"  PMID nulls (C10):        {n_pmid}")
print(f"  HR+CI nulls (C13):       {n_hr}")
print(f"  Year nulls (C14):        {n_year}")
print(f"  Estimand→OR (C13):       {n_estimand}")
print(f"  Flag-only (C16, C19):    {n_flag}")
