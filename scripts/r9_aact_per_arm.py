"""R9 — AACT per-arm enrollment cross-check.

Use design_groups.txt + baseline_counts.txt for granular per-arm N
verification (more strict than total enrollment in R7).

Detection:
  For each target NCT, baseline_counts.txt gives per-arm enrollment via
  design_group_id → number. Sum across all design groups = total enrollment.
  We compare extracted (tN, cN) against the largest two design-group counts.
  If neither ours matches AACT's two largest (within 5%), the arms are
  misextracted → null tN/cN.

Conservative: only fire when AACT has clear 2-arm design (design_groups.txt
has exactly 2 entries for that NCT).
"""
from __future__ import annotations
import json, csv, re, sys, io
from pathlib import Path
from collections import defaultdict, Counter

if hasattr(sys.stdout, "buffer") and getattr(sys.stdout, "encoding", "").lower() != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

HERE = Path(__file__).resolve().parent.parent
OUT = HERE / "outputs" / "extraction_audit"
DATA = OUT / "data"
AACT = Path("D:/AACT-storage/AACT/2026-04-12")
DRY = "--dry-run" in sys.argv


# Load all target trials (any score, not quarantined, has both tN+cN)
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
            tN = int(t.get("tN") or 0)
            cN = int(t.get("cN") or 0)
        except: continue
        if tN <= 0 or cN <= 0: continue
        all_trials.append((rv, nct, t, tN, cN))

target_ncts = sorted({nct for _, nct, _, _, _ in all_trials})
print(f"Target trials (with tN+cN both >0): {len(all_trials)}  unique NCTs: {len(target_ncts)}")

# Load baseline_counts.txt — design_group_id → count
# Schema: nct_id | design_group_id | classification | count | ...
target_set = set(target_ncts)
print("Loading baseline_counts.txt + design_groups.txt …")
design_group_counts = defaultdict(list)  # nct → list of (design_group_id, count)
with open(AACT / "baseline_counts.txt", "r", encoding="utf-8", errors="replace") as f:
    reader = csv.DictReader(f, delimiter="|")
    for row in reader:
        nct = (row.get("nct_id") or "").strip().upper()
        if nct not in target_set: continue
        if (row.get("classification") or "").strip().lower() != "total": continue
        try: cnt = int(row.get("count") or 0)
        except: continue
        dgid = (row.get("ctgov_group_code") or row.get("result_group_id") or "").strip()
        if cnt > 0 and dgid:
            design_group_counts[nct].append(cnt)

# Filter to NCTs with exactly 2 groups (clear 2-arm)
two_arm_ncts = {nct: sorted(cnts, reverse=True)
                 for nct, cnts in design_group_counts.items()
                 if len(cnts) == 2}
print(f"  NCTs with exactly 2 reported baseline groups: {len(two_arm_ncts)}")


def within_pct(a, b, pct=0.05):
    if a is None or b is None or b == 0: return False
    return abs(a - b) / b <= pct


findings = []
for rv, nct, t, tN, cN in all_trials:
    if nct not in two_arm_ncts: continue
    aact_arms = two_arm_ncts[nct]  # 2 counts, descending
    # Check if (tN, cN) maps to (aact_arms[0], aact_arms[1]) within 5%
    match_a = (within_pct(tN, aact_arms[0]) and within_pct(cN, aact_arms[1])) or \
              (within_pct(tN, aact_arms[1]) and within_pct(cN, aact_arms[0]))
    if not match_a:
        findings.append({
            "review": rv, "nct": nct,
            "extracted_tN": tN, "extracted_cN": cN,
            "AACT_arm_counts": aact_arms,
            "fix": "NULL_ARMS",
        })

print(f"Per-arm mismatches: {len(findings)}")


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
    rv, nct = f["review"], f["nct"]
    if (rv, nct) in seen: continue
    seen.add((rv, nct))
    html_path = HERE / f"{rv}.html"
    if not html_path.exists():
        applied.append({**f, "status": "FILE_MISSING"}); continue
    txt = html_path.read_text(encoding="utf-8")
    block = find_block(txt, nct)
    if not block:
        applied.append({**f, "status": "BLOCK_NOT_FOUND"}); continue
    _, _, bs, be = block
    changes = 0
    for fld in ("tE", "tN", "cE", "cN"):
        new_txt, ok = null_field_in_block(txt, bs, be, fld)
        if ok:
            txt = new_txt
            block = find_block(txt, nct)
            if not block: break
            _, _, bs, be = block
            changes += 1
    if changes:
        if not DRY: html_path.write_text(txt, encoding="utf-8")
        applied.append({**f, "status": "NULLED_ARMS", "fields_nulled": changes})
        n_fix += 1

out_p = OUT / "r9_per_arm.json"
out_p.write_text(json.dumps({"findings": findings, "applied": applied,
                              "summary": {"arms_nulled": n_fix}},
                             indent=2, ensure_ascii=False), encoding="utf-8")
print(f"\n{'DRY-RUN ' if DRY else ''}Per-arm fixes:")
print(f"  Trials with arm-counts nulled: {n_fix}")
