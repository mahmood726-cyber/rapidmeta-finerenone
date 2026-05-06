"""Extract Age, %Female, and follow-up for the 554 corpus NCTs from AACT
2026-04-12 snapshot. Outputs JSON keyed by NCT.

AACT tables used:
  - baseline_measurements.txt   age + sex
  - design_outcomes.txt         follow-up duration (time_frame)
  - studies.txt                 enrollment as fallback n

Aggregation: weighted by number_analyzed across arms (BG001, BG002, ...).
The 'B000' / 'BG000' code is usually overall; if present, prefer it.
"""
from __future__ import annotations
import sys, io, json, csv
from pathlib import Path
from collections import defaultdict

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

REPO = Path(__file__).resolve().parent.parent
AACT = Path("D:/AACT-storage/AACT/2026-04-12")

ncts = set((REPO / "outputs/corpus_ncts.txt").read_text().split())
print(f"Loaded {len(ncts)} NCTs from corpus.")

# Per-NCT containers
age_rows = defaultdict(list)     # NCT -> [(value, weight, code)]
sex_rows = defaultdict(list)     # NCT -> [(female_count, total, code)]


def to_float(s):
    try:
        return float(s) if s.strip() else None
    except (ValueError, AttributeError):
        return None


def to_int(s):
    try:
        return int(s) if s.strip() else None
    except (ValueError, AttributeError):
        return None


bm = AACT / "baseline_measurements.txt"
print(f"Streaming {bm.stat().st_size/1e9:.2f} GB ...")
with bm.open("r", encoding="utf-8", errors="replace") as f:
    header = f.readline().rstrip("\n").split("|")
    col = {n: i for i, n in enumerate(header)}
    n_rows = 0
    n_kept = 0
    for line in f:
        n_rows += 1
        parts = line.rstrip("\n").split("|")
        if len(parts) < len(header):
            continue
        nct = parts[col["nct_id"]]
        if nct not in ncts:
            continue
        title = parts[col["title"]]
        category = parts[col["category"]]
        ctgov_group = parts[col["ctgov_group_code"]]
        param_value_num = to_float(parts[col["param_value_num"]])
        number_analyzed = to_int(parts[col["number_analyzed"]])

        title_l = title.lower()
        cat_l = (category or "").lower()
        if title_l.startswith("age") and "continuous" in title_l:
            if param_value_num is not None and number_analyzed:
                age_rows[nct].append((param_value_num, number_analyzed, ctgov_group, cat_l))
                n_kept += 1
        elif title_l.startswith("sex") or title_l.startswith("gender"):
            if cat_l in ("female", "women", "f"):
                if param_value_num is not None and number_analyzed:
                    sex_rows[nct].append((param_value_num, number_analyzed, ctgov_group))
                    n_kept += 1
    print(f"  scanned {n_rows:,} rows, kept {n_kept:,}")


def best_age(rows):
    """Pick overall (BG000/Total) if present, else weighted mean across arms."""
    if not rows:
        return None
    # Prefer overall ctgov_group_code 'BG000' or category like 'Total'
    overall = [r for r in rows if r[2] == "BG000" or "total" in r[3]]
    if overall:
        # If multiple, take first
        return round(overall[0][0], 1)
    # Weighted mean by number_analyzed
    num = sum(v * w for v, w, _, _ in rows)
    den = sum(w for _, w, _, _ in rows)
    return round(num / den, 1) if den else None


def best_pct_female(rows):
    """Aggregate female counts across arms, divide by total."""
    if not rows:
        return None
    overall = [r for r in rows if r[2] == "BG000"]
    if overall:
        v, w, _ = overall[0]
        if 0 < v <= w:
            return round(100 * v / w, 1)
        # Sometimes param_value_num is already a percentage
        if 0 <= v <= 100 and w > 100:
            return round(v, 1) if v > 1 else None
    fem = sum(v for v, _, _ in rows)
    tot = sum(w for _, w, _ in rows)
    if tot == 0:
        return None
    pct = 100 * fem / tot
    if 0 <= pct <= 100:
        return round(pct, 1)
    return None


baselines = {}
for nct in ncts:
    age = best_age(age_rows.get(nct, []))
    pf = best_pct_female(sex_rows.get(nct, []))
    if age is not None or pf is not None:
        rec = {}
        if age is not None: rec["age"] = age
        if pf is not None: rec["pct_female"] = pf
        baselines[nct] = rec

print(f"\nNCTs with age/female from AACT: {len(baselines)}")
out = REPO / "outputs/aact_baselines.json"
out.write_text(json.dumps(baselines, indent=2))
print(f"Written: {out}")
