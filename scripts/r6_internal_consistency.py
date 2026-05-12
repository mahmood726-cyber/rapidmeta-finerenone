"""Round 6 — internal-consistency-only audit + auto-fix.

No external lookups. No human review needed. Each check fires only when
the extracted data is internally contradictory, so the fix is unambiguous.

Checks:

C1 — DIRECTION_INCONSISTENT
  For binary outcomes (estimandType ∈ {OR, RR, HR}) with valid tE/tN/cE/cN,
  compute crude_RR = (tE/tN) / (cE/cN). If sign(log(crude_RR)) ≠
  sign(log(publishedHR)) AND both magnitudes are non-trivial (|log| > 0.1),
  the direction is inconsistent. ACTION: null publishedHR + CI.

C2 — COPY_PASTE_ARMS
  Same (tE, tN, cE, cN) integer 4-tuple appearing across ≥2 distinct NCTs
  (across all reviews). The first occurrence (by alphabetical review) keeps;
  others get effect fields nulled. ACTION: null publishedHR + CI on duplicates.

C3 — CONSECUTIVE_NCT_RUN
  Within a single review, ≥3 NCTs whose integer suffix is consecutive
  (NCT05000294, ...295, ...296). Statistically improbable for genuine
  trial enumeration. ACTION: null pmid on all members of the run.

C4 — CI_ASYMMETRY
  For log-scale effects (HR/OR/RR), check ratio of log-distances
  (log UCI − log HR) vs (log HR − log LCI). Ratio > 5 OR < 0.2 implies
  transcription error. ACTION: null CI (keep HR; CI bounds are likely wrong).

C5 — YEAR_NCT_ERA
  NCT integer suffix vs year. NCT01xxxxxx registered ~2010; NCT02xxxxxx
  ~2014; NCT03xxxxxx ~2017; NCT04xxxxxx ~2020; NCT05xxxxxx ~2022;
  NCT06xxxxxx ~2024. If publication year is >7 years off the NCT era,
  the year is suspicious. ACTION: null year (keep NCT).

C6 — WITHIN_REVIEW_NAME_DUPLICATE
  Same trial name (acronym) attached to ≥2 different NCTs in the same review.
  The lower-NCT entry keeps; others get NCT and HR/CI nulled.
  ACTION: null key on duplicates.

Output:
  outputs/extraction_audit/r6_internal_consistency.json
"""
from __future__ import annotations
import json, re, sys, io, math
from pathlib import Path
from collections import defaultdict

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


def null_key(txt, nct):
    nulled = f"NULLED:{nct}"
    if nulled in txt: return txt, 0
    pat = re.compile(r'(["\'])(' + re.escape(nct) + r')(\1)(\s*:)')
    new_txt, n = pat.subn(
        lambda m: f'{m.group(1)}NULLED:{m.group(2)}{m.group(3)}{m.group(4)}', txt)
    return new_txt, n


# Load all trial data
all_trials = []  # list of (review, nct, trial_dict)
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

# Helper: numeric extraction
def f(v):
    try:
        return float(v) if v is not None else None
    except: return None


def i(v):
    try:
        return int(v) if v is not None else None
    except: return None


# ─────── C1: Direction inconsistent ───────
def check_c1():
    findings = []
    for rv, nct, t in all_trials:
        et = (t.get("estimandType") or "").upper()
        if et not in ("OR", "RR", "HR"): continue
        tE, tN, cE, cN = (i(t.get("tE")), i(t.get("tN")),
                           i(t.get("cE")), i(t.get("cN")))
        hr = f(t.get("publishedHR"))
        if not all(v is not None for v in (tE, tN, cE, cN, hr)): continue
        if tN <= 0 or cN <= 0: continue
        if cE == 0 or tE == 0: continue  # zero cells need correction; skip
        if hr <= 0: continue
        rate_t = tE / tN; rate_c = cE / cN
        if rate_c <= 0: continue
        crude_rr = rate_t / rate_c
        log_crude = math.log(crude_rr); log_hr = math.log(hr)
        # Both directions must be non-trivial AND opposite-signed
        if abs(log_crude) > 0.10 and abs(log_hr) > 0.10:
            if (log_crude > 0) != (log_hr > 0):
                findings.append({
                    "check": "C1_DIRECTION_INCONSISTENT",
                    "review": rv, "nct": nct,
                    "crude_RR": round(crude_rr, 3),
                    "publishedHR": hr,
                    "log_crude": round(log_crude, 3),
                    "log_hr": round(log_hr, 3),
                    "fix": "NULL_HR_AND_CI",
                })
    return findings


# ─────── C2: Copy-paste arms ───────
def check_c2():
    findings = []
    tuple_index = defaultdict(list)  # (tE,tN,cE,cN) → [(rv, nct, hr)]
    for rv, nct, t in all_trials:
        tE, tN, cE, cN = (i(t.get("tE")), i(t.get("tN")),
                           i(t.get("cE")), i(t.get("cN")))
        if not all(v is not None and v > 0 for v in (tN, cN)): continue
        # Require all 4 present; skip pure single-arm
        if tE is None or cE is None: continue
        # Skip tiny-N tuples (likely coincidence)
        if tN < 30 or cN < 30: continue
        tuple_index[(tE, tN, cE, cN)].append((rv, nct, f(t.get("publishedHR"))))

    for tup, occurrences in tuple_index.items():
        if len(occurrences) < 2: continue
        # Distinct NCTs only (multi-review for same NCT is normal)
        ncts = {o[1] for o in occurrences}
        if len(ncts) < 2: continue
        # First (review, nct) alphabetically keeps; others flagged
        occurrences.sort()
        keeper = occurrences[0]
        for rv, nct, hr in occurrences[1:]:
            if nct == keeper[1]: continue
            findings.append({
                "check": "C2_COPY_PASTE_ARMS",
                "review": rv, "nct": nct,
                "tuple": list(tup),
                "keeper": {"review": keeper[0], "nct": keeper[1]},
                "fix": "NULL_HR_AND_CI",
            })
    return findings


# ─────── C3: Consecutive NCT runs ───────
def check_c3():
    findings = []
    by_review = defaultdict(list)
    for rv, nct, t in all_trials:
        m = re.match(r"NCT(\d{8})$", nct)
        if not m: continue
        by_review[rv].append((int(m.group(1)), nct))
    for rv, lst in by_review.items():
        lst.sort()
        # Find runs of ≥3 consecutive integers
        run = [lst[0]] if lst else []
        for j in range(1, len(lst)):
            if lst[j][0] == lst[j-1][0] + 1:
                run.append(lst[j])
            else:
                if len(run) >= 3:
                    for _, n in run:
                        findings.append({
                            "check": "C3_CONSECUTIVE_NCT",
                            "review": rv, "nct": n,
                            "run_length": len(run),
                            "fix": "NULL_PMID",
                        })
                run = [lst[j]]
        if len(run) >= 3:
            for _, n in run:
                findings.append({
                    "check": "C3_CONSECUTIVE_NCT",
                    "review": rv, "nct": n,
                    "run_length": len(run),
                    "fix": "NULL_PMID",
                })
    return findings


# ─────── C4: CI asymmetry ───────
def check_c4():
    findings = []
    for rv, nct, t in all_trials:
        et = (t.get("estimandType") or "").upper()
        if et not in ("OR", "RR", "HR"): continue
        hr, lci, uci = f(t.get("publishedHR")), f(t.get("hrLCI")), f(t.get("hrUCI"))
        if not all(v is not None and v > 0 for v in (hr, lci, uci)): continue
        if not (lci < hr < uci): continue  # let other check handle
        log_hr = math.log(hr); log_lci = math.log(lci); log_uci = math.log(uci)
        upper_half = log_uci - log_hr
        lower_half = log_hr - log_lci
        if upper_half <= 0 or lower_half <= 0: continue
        ratio = max(upper_half / lower_half, lower_half / upper_half)
        if ratio > 5:
            findings.append({
                "check": "C4_CI_ASYMMETRY",
                "review": rv, "nct": nct,
                "hr": hr, "lci": lci, "uci": uci,
                "log_asymmetry_ratio": round(ratio, 2),
                "fix": "NULL_CI",
            })
    return findings


# ─────── C5: Year vs NCT era ───────
NCT_ERA_LOWER_BOUND_YEAR = {
    "01": 2009, "02": 2013, "03": 2016, "04": 2019, "05": 2022, "06": 2024,
}
NCT_ERA_UPPER_BOUND_YEAR = {
    "01": 2018, "02": 2022, "03": 2025, "04": 2026, "05": 2026, "06": 2026,
}
def check_c5():
    findings = []
    for rv, nct, t in all_trials:
        year = i(t.get("year"))
        if year is None or year < 1990 or year > 2030: continue
        m = re.match(r"NCT(\d{2})\d{6}$", nct)
        if not m: continue
        prefix = m.group(1)
        lower = NCT_ERA_LOWER_BOUND_YEAR.get(prefix)
        upper = NCT_ERA_UPPER_BOUND_YEAR.get(prefix)
        if not lower or not upper: continue
        # NCT prefix gives a registration era; publication is typically 2-7 years later
        # Allow generous window: year >= lower - 1
        if year < lower - 1:
            findings.append({
                "check": "C5_YEAR_NCT_ERA",
                "review": rv, "nct": nct, "year": year,
                "expected_year_range": [lower, upper + 8],
                "fix": "NULL_YEAR",
            })
        elif year > upper + 8:
            findings.append({
                "check": "C5_YEAR_NCT_ERA",
                "review": rv, "nct": nct, "year": year,
                "expected_year_range": [lower, upper + 8],
                "fix": "NULL_YEAR",
            })
    return findings


# ─────── C6: Within-review name duplicate ───────
def check_c6():
    findings = []
    by_review_name = defaultdict(list)
    for rv, nct, t in all_trials:
        name = (t.get("name") or "").strip()
        if not name or len(name) < 3: continue
        # Skip generic/placeholder names
        if re.match(r"NCT\d|Study|Trial \d|Phase \d|C\d{3}|N0\d", name): continue
        by_review_name[(rv, name)].append(nct)
    for (rv, name), ncts in by_review_name.items():
        if len(set(ncts)) < 2: continue
        # Multiple NCTs same name in same review — suspicious
        # Keep lowest-NCT, flag others
        sorted_ncts = sorted(ncts)
        keeper = sorted_ncts[0]
        for nct in sorted_ncts[1:]:
            if nct == keeper: continue
            findings.append({
                "check": "C6_NAME_DUPLICATE",
                "review": rv, "nct": nct, "name": name,
                "keeper_nct": keeper,
                "fix": "NULL_KEY",
            })
    return findings


# Run all checks
all_findings = []
for chk in [check_c1, check_c2, check_c3, check_c4, check_c5, check_c6]:
    all_findings.extend(chk())

from collections import Counter
by_check = Counter(f["check"] for f in all_findings)
print(f"\nFindings by check:")
for c, n in by_check.most_common():
    print(f"  {c}: {n}")


# Apply fixes
log = []
n_hr = n_pmid = n_key = n_ci = n_year = 0
# dedupe per (review, nct, fix) — same trial may be hit by multiple checks
seen = set()
for finding in all_findings:
    rv, nct, fix = finding["review"], finding["nct"], finding["fix"]
    key = (rv, nct, fix)
    if key in seen: continue
    seen.add(key)
    html_path = HERE / f"{rv}.html"
    if not html_path.exists():
        log.append({**finding, "status": "FILE_MISSING"})
        continue
    txt = html_path.read_text(encoding="utf-8")

    if fix == "NULL_HR_AND_CI":
        block = find_block(txt, nct)
        if not block:
            log.append({**finding, "status": "BLOCK_NOT_FOUND"})
            continue
        _, _, bs, be = block
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
    elif fix == "NULL_PMID":
        block = find_block(txt, nct)
        if not block:
            log.append({**finding, "status": "BLOCK_NOT_FOUND"})
            continue
        _, _, bs, be = block
        new_txt, ok = null_field_in_block(txt, bs, be, "pmid")
        if ok:
            if not DRY: html_path.write_text(new_txt, encoding="utf-8")
            log.append({**finding, "status": "NULLED_PMID"})
            n_pmid += 1
        else:
            log.append({**finding, "status": "PMID_ALREADY_NULL"})
    elif fix == "NULL_KEY":
        new_txt, n = null_key(txt, nct)
        if n > 0:
            if not DRY: html_path.write_text(new_txt, encoding="utf-8")
            log.append({**finding, "status": "NULLED_KEY"})
            n_key += 1
        elif f"NULLED:{nct}" in txt:
            log.append({**finding, "status": "ALREADY_NULLED"})
    elif fix == "NULL_CI":
        block = find_block(txt, nct)
        if not block:
            log.append({**finding, "status": "BLOCK_NOT_FOUND"})
            continue
        _, _, bs, be = block
        for fld in ("hrLCI", "hrUCI"):
            new_txt, ok = null_field_in_block(txt, bs, be, fld)
            if ok:
                txt = new_txt
                block = find_block(txt, nct)
                if not block: break
                _, _, bs, be = block
        if not DRY: html_path.write_text(txt, encoding="utf-8")
        log.append({**finding, "status": "NULLED_CI"})
        n_ci += 1
    elif fix == "NULL_YEAR":
        block = find_block(txt, nct)
        if not block:
            log.append({**finding, "status": "BLOCK_NOT_FOUND"})
            continue
        _, _, bs, be = block
        new_txt, ok = null_field_in_block(txt, bs, be, "year")
        if ok:
            if not DRY: html_path.write_text(new_txt, encoding="utf-8")
            log.append({**finding, "status": "NULLED_YEAR"})
            n_year += 1

out_p = OUT / "r6_internal_consistency.json"
out_p.write_text(json.dumps({"findings": all_findings, "fixes": log,
                              "counts": {"HR_CI_nulls": n_hr, "PMID_nulls": n_pmid,
                                         "NCT_key_nulls": n_key, "CI_nulls": n_ci,
                                         "year_nulls": n_year}},
                             indent=2, ensure_ascii=False), encoding="utf-8")

print(f"\n{'DRY-RUN ' if DRY else ''}Fixes applied:")
print(f"  HR+CI nulls (C1, C2):   {n_hr}")
print(f"  PMID nulls (C3):        {n_pmid}")
print(f"  NCT key nulls (C6):     {n_key}")
print(f"  CI-only nulls (C4):     {n_ci}")
print(f"  Year nulls (C5):        {n_year}")
print(f"\nLog → {out_p}")
