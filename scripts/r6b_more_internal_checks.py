"""R6b — additional internal consistency checks.

C7 — PMID_USED_ACROSS_DISTINCT_NCTS
  Same PMID appearing as the primary citation for ≥2 distinct NCTs in the
  corpus is suspicious — a PMID typically corresponds to one trial.
  Exception: pooled-analyses publish results for multiple NCTs in one paper,
  but that's rare for individual-trial-primary citation. ACTION: null PMID
  on all but the first occurrence (keep alphabetical first; null others).

C8 — BASELINE_N_VS_ARM_SUM
  baseline.n should be ≈ tN + cN. If |baseline.n − (tN + cN)| / baseline.n
  > 0.10 (10% mismatch), the baseline.n is wrong. Common pattern: baseline.n
  is the ITT N but tN/cN are PP arms.
  ACTION: null baseline.n (preserve arm data which is more useful for pooling).

C9 — HR_OUTSIDE_CI
  publishedHR not in [hrLCI, hrUCI]. (Already partially covered by C4 but C4
  required lci < hr < uci; this catches the case where hr is OUTSIDE the
  interval, which IS impossible.)
  ACTION: null HR + CI (we cannot tell which is the transcription error).
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


def null_nested_baseline_n(txt, body_start, body_end):
    """Null baseline.n which is inside a nested object."""
    body = txt[body_start:body_end]
    # Find baseline: { ... n: VALUE ... } and null the n inside
    m = re.search(r'(["\']?)baseline\1\s*:\s*\{([^{}]*)\}', body, re.IGNORECASE)
    if not m: return txt, False
    inner = m.group(2)
    new_inner, n = re.subn(
        r'((["\']?)n\2\s*:\s*)(?:[0-9.eE+-]+)(?=\s*[,}])',
        r'\1null', inner, flags=re.IGNORECASE)
    if n == 0: return txt, False
    new_body = body[:m.start(2)] + new_inner + body[m.end(2):]
    return txt[:body_start] + new_body + txt[body_end:], True


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


def f(v):
    try: return float(v) if v is not None else None
    except: return None


def i(v):
    try: return int(v) if v is not None else None
    except: return None


# ───── C7: PMID used across distinct NCTs ─────
def check_c7():
    findings = []
    pmid_index = defaultdict(list)  # pmid → [(rv, nct)]
    for rv, nct, t in all_trials:
        pmid = (t.get("pmid") or "")
        try:
            int(pmid)
        except (TypeError, ValueError):
            continue
        if not pmid or len(pmid) < 6 or len(pmid) > 9: continue
        pmid_index[pmid].append((rv, nct))
    for pmid, occurrences in pmid_index.items():
        distinct_ncts = {o[1] for o in occurrences}
        if len(distinct_ncts) < 2: continue
        # Keep alphabetical first (rv, nct); flag others
        occurrences.sort()
        keeper = occurrences[0]
        already_seen_nct = {keeper[1]}
        for rv, nct in occurrences[1:]:
            if nct in already_seen_nct: continue
            already_seen_nct.add(nct)
            findings.append({
                "check": "C7_PMID_ACROSS_NCT",
                "review": rv, "nct": nct, "pmid": pmid,
                "keeper": {"review": keeper[0], "nct": keeper[1]},
                "fix": "NULL_PMID",
            })
    return findings


# ───── C8: baseline.n vs tN + cN ─────
def check_c8():
    findings = []
    for rv, nct, t in all_trials:
        baseline = t.get("baseline") or {}
        if not isinstance(baseline, dict): continue
        bn = i(baseline.get("n"))
        tN, cN = i(t.get("tN")), i(t.get("cN"))
        if bn is None or tN is None or cN is None: continue
        if bn <= 0: continue
        arm_sum = tN + cN
        if arm_sum <= 0: continue
        ratio = abs(bn - arm_sum) / bn
        if ratio > 0.10:  # 10% mismatch
            findings.append({
                "check": "C8_BASELINE_N_MISMATCH",
                "review": rv, "nct": nct,
                "baseline_n": bn, "arm_sum": arm_sum,
                "ratio": round(ratio, 3),
                "fix": "NULL_BASELINE_N",
            })
    return findings


# ───── C9: HR outside CI ─────
def check_c9():
    findings = []
    for rv, nct, t in all_trials:
        hr, lci, uci = f(t.get("publishedHR")), f(t.get("hrLCI")), f(t.get("hrUCI"))
        if not all(v is not None and v > 0 for v in (hr, lci, uci)): continue
        if hr < lci or hr > uci:
            findings.append({
                "check": "C9_HR_OUTSIDE_CI",
                "review": rv, "nct": nct,
                "hr": hr, "lci": lci, "uci": uci,
                "fix": "NULL_HR_AND_CI",
            })
    return findings


all_findings = []
for chk in [check_c7, check_c8, check_c9]:
    all_findings.extend(chk())

by_check = Counter(f["check"] for f in all_findings)
print(f"\nFindings:")
for c, n in by_check.most_common():
    print(f"  {c}: {n}")


# Apply
log = []
n_pmid = n_baseline = n_hr = 0
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
    elif fix == "NULL_BASELINE_N":
        new_txt, ok = null_nested_baseline_n(txt, bs, be)
        if ok:
            if not DRY: html_path.write_text(new_txt, encoding="utf-8")
            log.append({**finding, "status": "NULLED_BASELINE_N"})
            n_baseline += 1
        else:
            log.append({**finding, "status": "BASELINE_NOT_NULLED"})
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

out_p = OUT / "r6b_internal_consistency.json"
out_p.write_text(json.dumps({"findings": all_findings, "fixes": log,
                              "counts": {"PMID_nulls": n_pmid,
                                         "baseline_N_nulls": n_baseline,
                                         "HR_CI_nulls": n_hr}},
                             indent=2, ensure_ascii=False), encoding="utf-8")

print(f"\n{'DRY-RUN ' if DRY else ''}Fixes:")
print(f"  PMID nulls (C7):       {n_pmid}")
print(f"  baseline.n nulls (C8): {n_baseline}")
print(f"  HR+CI nulls (C9):      {n_hr}")
