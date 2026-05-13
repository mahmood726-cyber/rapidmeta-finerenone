"""R10 — AACT outcome_measurements event-count verification.

For each trial in our corpus with both tE and cE populated, look up AACT's
posted outcome_measurements.txt and check whether our (tE, cE) pair matches
ANY OG000/OG001 pair across all outcomes for that NCT.

If NO outcome in AACT has values matching our (tE, cE), the event counts
are misextracted → null tE+cE.

This handles:
  - Trials with multiple primary outcomes posted
  - Trials with different timepoints (5y vs 6.5y follow-up)
  - Different event-count types (subjects-with-event, total-events)

Skip trials where AACT has NO outcome_measurements (FDAAA: not all trials
post results).
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
        try:
            tE = int(t.get("tE") or -1); cE = int(t.get("cE") or -1)
        except: continue
        if tE < 0 or cE < 0: continue
        all_trials.append((rv, nct, t, tE, cE))

target_ncts = sorted({nct for _, nct, _, _, _ in all_trials})
print(f"Trials with tE,cE present: {len(all_trials)}  unique NCTs: {len(target_ncts)}")

# Load outcome_measurements per NCT
target_set = set(target_ncts)
nct_outcomes = defaultdict(list)  # nct → list of (og_code, param_value_int, title)
print("Loading outcome_measurements.txt …")
with open(AACT / "outcome_measurements.txt", "r", encoding="utf-8", errors="replace") as f:
    reader = csv.DictReader(f, delimiter="|")
    for row in reader:
        nct = (row.get("nct_id") or "").strip().upper()
        if nct not in target_set: continue
        param_type = (row.get("param_type") or "").upper()
        if param_type not in ("COUNT_OF_PARTICIPANTS", "NUMBER", "COUNT"):
            continue
        val_str = (row.get("param_value_num") or row.get("param_value") or "").strip()
        try: v = int(float(val_str))
        except: continue
        if v < 0: continue
        og = (row.get("ctgov_group_code") or "").strip()
        title = (row.get("title") or "")[:80]
        nct_outcomes[nct].append((og, v, title))

print(f"NCTs with usable outcome_measurements: {len(nct_outcomes)}")


def within_pct(a, b, pct=0.10):
    if b == 0: return a == 0
    return abs(a - b) / b <= pct


def match_pair(tE, cE, outcomes):
    """Check whether (tE, cE) appears as a valid pair across any AACT outcome.
    Returns True if any pair of (OG000_val, OG001_val) is within 10% of (tE, cE)
    or (cE, tE).
    """
    # Group by outcome_id is implicit (rows of same outcome appear consecutively)
    # Simpler: get all distinct OG values that have a corresponding "other-arm" value
    by_og = defaultdict(list)
    for og, v, title in outcomes:
        by_og[og].append(v)
    if len(by_og) < 2: return False, []
    # For each pair of OG codes, check if any v1 (from OG_a) and v2 (from OG_b)
    # together match our (tE, cE)
    og_codes = list(by_og.keys())
    matched_pairs = []
    for i in range(len(og_codes)):
        for j in range(len(og_codes)):
            if i == j: continue
            for v1 in by_og[og_codes[i]]:
                for v2 in by_og[og_codes[j]]:
                    if within_pct(tE, v1) and within_pct(cE, v2):
                        matched_pairs.append((v1, v2, og_codes[i], og_codes[j]))
                    elif within_pct(tE, v2) and within_pct(cE, v1):
                        matched_pairs.append((v2, v1, og_codes[j], og_codes[i]))
    return bool(matched_pairs), matched_pairs[:3]


findings = []
n_skip_no_aact = 0
n_match = 0
for rv, nct, t, tE, cE in all_trials:
    outs = nct_outcomes.get(nct, [])
    if not outs:
        n_skip_no_aact += 1
        continue
    matched, samples = match_pair(tE, cE, outs)
    if matched:
        n_match += 1
    else:
        findings.append({
            "review": rv, "nct": nct,
            "extracted_tE": tE, "extracted_cE": cE,
            "aact_outcome_count": len(outs),
            "fix": "NULL_EVENTS",
        })

print(f"\nResults:")
print(f"  Matched (within 10%):   {n_match}")
print(f"  Mismatched (flag):       {len(findings)}")
print(f"  No AACT outcomes posted: {n_skip_no_aact}")


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
    changes = 0
    for fld in ("tE", "cE"):
        new_txt, ok = null_field_in_block(txt, bs, be, fld)
        if ok:
            txt = new_txt
            block = find_block(txt, f["nct"])
            if not block: break
            _, _, bs, be = block
            changes += 1
    if changes:
        if not DRY: html_path.write_text(txt, encoding="utf-8")
        applied.append({**f, "status": "NULLED_EVENTS"})
        n_fix += 1

out_p = OUT / "r10_outcome_events.json"
out_p.write_text(json.dumps({
    "matched": n_match,
    "mismatched": len(findings),
    "no_aact_outcomes": n_skip_no_aact,
    "findings": findings[:200],  # cap for readability
    "applied": applied,
    "summary": {"events_nulled": n_fix},
}, indent=2, ensure_ascii=False), encoding="utf-8")
print(f"\n{'DRY-RUN ' if DRY else ''}Events nulled: {n_fix}")
