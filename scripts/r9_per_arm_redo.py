"""R9 (redo) — per-arm enrollment check using corrected schema.

baseline_counts.txt with scope=overall + units=Participants gives per-arm
participant counts. Each BGxxx ctgov_group_code is one arm; AACT often
also has a "Total" row whose count equals sum-of-arms (we exclude it).

For each NCT with exactly 2 distinct per-arm BG codes after filtering:
  - AACT pair = (n1, n2)
  - Our extracted = (tN, cN)
  - If neither (tN≈n1 AND cN≈n2) nor (tN≈n2 AND cN≈n1) within 5%,
    → null tE/tN/cE/cN (arms misextracted).
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

# Load target trials (with both tN+cN populated)
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
            tN = int(t.get("tN") or 0); cN = int(t.get("cN") or 0)
        except: continue
        if tN <= 0 or cN <= 0: continue
        all_trials.append((rv, nct, t, tN, cN))

target_ncts = sorted({nct for _, nct, _, _, _ in all_trials})
print(f"Trials with tN+cN > 0: {len(all_trials)}  unique NCTs: {len(target_ncts)}")

target_set = set(target_ncts)
nct_arms = defaultdict(list)  # nct → list of (bg_code, count)
print("Loading baseline_counts.txt...")
with open(AACT / "baseline_counts.txt", "r", encoding="utf-8", errors="replace") as f:
    reader = csv.DictReader(f, delimiter="|")
    for row in reader:
        nct = (row.get("nct_id") or "").strip().upper()
        if nct not in target_set: continue
        if (row.get("scope") or "").lower() != "overall": continue
        if (row.get("units") or "") != "Participants": continue
        try: cnt = int(row.get("count") or 0)
        except: continue
        bg = (row.get("ctgov_group_code") or "").strip()
        if cnt > 0 and bg:
            nct_arms[nct].append((bg, cnt))

# For each NCT: drop the "total" row (whose count = sum of others)
def get_per_arm(arm_list):
    """Drop the total-row if present. Return list of per-arm counts."""
    if not arm_list: return []
    counts = [c for _, c in arm_list]
    total = sum(counts)
    # If a single row equals (sum-of-others), that's the total — drop it
    filtered = [(bg, c) for bg, c in arm_list if c * 2 != total]
    if not filtered: return []
    return filtered

per_arm_dict = {nct: get_per_arm(arms) for nct, arms in nct_arms.items()}
two_arm = {nct: sorted([c for _, c in arms], reverse=True)
            for nct, arms in per_arm_dict.items()
            if len(arms) == 2}
print(f"NCTs with exactly 2 per-arm AACT counts (post-total-filter): {len(two_arm)}")


def within_pct(a, b, pct=0.15):
    """15% tolerance — covers ITT-vs-PP analysis-set differences which are
    common (~5-10%). Only egregious mismatches (>15%) get flagged."""
    if a is None or b is None or b == 0: return False
    return abs(a - b) / b <= pct


findings = []
for rv, nct, t, tN, cN in all_trials:
    if nct not in two_arm: continue
    n1, n2 = two_arm[nct]
    match_a = within_pct(tN, n1) and within_pct(cN, n2)
    match_b = within_pct(tN, n2) and within_pct(cN, n1)
    if not (match_a or match_b):
        findings.append({
            "review": rv, "nct": nct,
            "extracted_tN": tN, "extracted_cN": cN,
            "AACT_arm_counts": [n1, n2],
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
    if (f["review"], f["nct"]) in seen: continue
    seen.add((f["review"], f["nct"]))
    html_path = HERE / f"{f['review']}.html"
    if not html_path.exists(): continue
    txt = html_path.read_text(encoding="utf-8")
    block = find_block(txt, f["nct"])
    if not block: continue
    _, _, bs, be = block
    changes = 0
    for fld in ("tE", "tN", "cE", "cN"):
        new_txt, ok = null_field_in_block(txt, bs, be, fld)
        if ok:
            txt = new_txt
            block = find_block(txt, f["nct"])
            if not block: break
            _, _, bs, be = block
            changes += 1
    if changes:
        if not DRY: html_path.write_text(txt, encoding="utf-8")
        applied.append({**f, "status": "NULLED_ARMS"})
        n_fix += 1

out_p = OUT / "r9_per_arm.json"
out_p.write_text(json.dumps({"findings": findings, "applied": applied,
                              "summary": {"arms_nulled": n_fix,
                                           "two_arm_aact_resolved": len(two_arm)}},
                             indent=2, ensure_ascii=False), encoding="utf-8")
print(f"\n{'DRY-RUN ' if DRY else ''}Per-arm fixes: {n_fix} trials nulled")
