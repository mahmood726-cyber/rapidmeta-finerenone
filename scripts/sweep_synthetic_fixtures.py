"""
Corpus-wide sweep for LLM-fabricated synthetic trials in extracted realData.

Fingerprint (from Agent 1 finding, 28 trials in 9 reviews):
  C1: NCT in NCT05000000-NCT05000999 range (placeholder block)
  C2: NCT prefix NCT06xxxxxxx (any 06 prefix)
  C3: empty/null pmid
  C4: year in {2024, 2025, 2026}
  C5: baseline.n exactly == 2 * tN

Outputs:
  - Single-criterion counts
  - Combined fingerprint counts (3, 4, 5 criteria)
  - Top 15 reviews by 4-or-5-criterion match
  - 5 spot-check trials (4-of-5 with real PMID)

Run: python C:/Projects/Finrenone/scripts/sweep_synthetic_fixtures.py
"""

from __future__ import annotations

import io
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

# Force UTF-8 stdout on Windows (cp1252 default crashes on box-drawing).
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

DATA_DIR = Path("C:/Projects/Finrenone/outputs/extraction_audit/data")
INDEX = DATA_DIR / "_index.json"

NCT05_PLACEHOLDER = re.compile(r"^NCT05000\d{3}$")
NCT06_ANY = re.compile(r"^NCT06\d{8}$")
PMID_VALID = re.compile(r"^\d{6,9}$")
YEARS_SUSPECT = {2024, 2025, 2026}


def is_empty_pmid(pmid) -> bool:
    if pmid is None:
        return True
    if not isinstance(pmid, str):
        # numeric pmid -> treat as present
        return False
    s = pmid.strip()
    if not s:
        return True
    if s.lower() in {"null", "none", "n/a", "na", "tbd", "pending", "unknown"}:
        return True
    return not PMID_VALID.match(s)


def classify_trial(nct: str, trial: dict) -> dict:
    c1 = bool(NCT05_PLACEHOLDER.match(nct or ""))
    c2 = bool(NCT06_ANY.match(nct or ""))
    pmid = trial.get("pmid")
    c3 = is_empty_pmid(pmid)
    year = trial.get("year")
    c4 = isinstance(year, int) and year in YEARS_SUSPECT
    baseline = trial.get("baseline") or {}
    bN = baseline.get("n") if isinstance(baseline, dict) else None
    tN = trial.get("tN")
    c5 = (
        isinstance(bN, (int, float))
        and isinstance(tN, (int, float))
        and tN > 0
        and bN == 2 * tN
    )
    return {
        "C1_NCT05_placeholder": c1,
        "C2_NCT06_any": c2,
        "C3_empty_pmid": c3,
        "C4_year_2024_2026": c4,
        "C5_baseline_double_tN": c5,
    }


def main() -> int:
    with INDEX.open("r", encoding="utf-8") as f:
        manifest = json.load(f)

    n_reviews = 0
    n_trials = 0
    single_counts: Counter[str] = Counter()
    combined_dist: Counter[int] = Counter()
    by_review_4or5: Counter[str] = Counter()
    fourof5_with_real_pmid: list[tuple[str, str, dict, int]] = []
    fiveof5: list[tuple[str, str, dict]] = []

    for entry in manifest:
        if not entry.get("has_realData"):
            continue
        stem = entry["stem"]
        path = DATA_DIR / f"{stem}.json"
        if not path.exists():
            continue
        try:
            with path.open("r", encoding="utf-8") as f:
                doc = json.load(f)
        except Exception as e:
            print(f"[skip] {stem}: {e}", file=sys.stderr)
            continue

        real = doc.get("realData") or {}
        if not isinstance(real, dict):
            continue
        n_reviews += 1

        for nct, trial in real.items():
            if not isinstance(trial, dict):
                continue
            n_trials += 1
            flags = classify_trial(nct, trial)
            for k, v in flags.items():
                if v:
                    single_counts[k] += 1
            hits = sum(flags.values())
            combined_dist[hits] += 1
            # 4-criterion fingerprint: NCT-suspect (C1 OR C2) + C3 + C4 + C5
            nct_suspect = flags["C1_NCT05_placeholder"] or flags["C2_NCT06_any"]
            hits4 = (
                int(nct_suspect)
                + int(flags["C3_empty_pmid"])
                + int(flags["C4_year_2024_2026"])
                + int(flags["C5_baseline_double_tN"])
            )
            if hits4 >= 3:
                by_review_4or5[stem] += 1
            if hits4 == 4:
                fiveof5.append((stem, nct, trial))  # full 4/4 fingerprint
            # spot-check pool: 3-of-4 fingerprint with real pmid (so missing-pmid is the gap)
            if hits4 == 3 and not flags["C3_empty_pmid"]:
                pmid = trial.get("pmid")
                if isinstance(pmid, str) and PMID_VALID.match(pmid.strip()):
                    fourof5_with_real_pmid.append((stem, nct, trial, hits4))

    print("=" * 72)
    print(f"SCANNED: {n_reviews} reviews, {n_trials} trials")
    print("=" * 72)

    print("\n[1] Single-criterion counts:")
    for k in [
        "C1_NCT05_placeholder",
        "C2_NCT06_any",
        "C3_empty_pmid",
        "C4_year_2024_2026",
        "C5_baseline_double_tN",
    ]:
        c = single_counts[k]
        pct = 100.0 * c / n_trials if n_trials else 0.0
        print(f"  {k:30s}  {c:5d}  ({pct:5.2f}%)")

    print("\n[2] Combined fingerprint counts (k of 5 raw criteria; C1 and C2 are mutually exclusive):")
    for k in range(6):
        c = combined_dist.get(k, 0)
        pct = 100.0 * c / n_trials if n_trials else 0.0
        print(f"  {k} of 5   {c:5d}  ({pct:5.2f}%)")
    n_3plus = sum(combined_dist[k] for k in range(3, 6))
    n_4plus = sum(combined_dist[k] for k in range(4, 6))
    n_5 = combined_dist[5]
    print(f"  ----")
    print(f"  >=3 of 5  {n_3plus}")
    print(f"  >=4 of 5  {n_4plus}  (effective full fingerprint, since C1 xor C2)")
    print(f"  ==5 of 5  {n_5}    (impossible: C1 and C2 mutually exclusive)")

    print("\n[3] Top 15 reviews by 3-or-4 effective-criterion match (NCT-suspect+pmid+year+bN=2tN):")
    for stem, c in by_review_4or5.most_common(15):
        print(f"  {c:3d}  {stem}")

    print("\n[4] Spot-check up to 5 trials matching 3-of-4 effective with REAL pmid:")
    sample = fourof5_with_real_pmid[:5]
    for stem, nct, trial, hits in sample:
        flags = classify_trial(nct, trial)
        baseline = trial.get("baseline") or {}
        bN = baseline.get("n") if isinstance(baseline, dict) else None
        print(
            f"  {stem} :: {nct} :: pmid={trial.get('pmid')} year={trial.get('year')} "
            f"name={trial.get('name')!r} bN={bN} tN={trial.get('tN')} cN={trial.get('cN')}"
        )
        print(f"      flags: {flags}")

    print("\n[5] All 4-of-4 effective-fingerprint trials (full synthetic fingerprint):")
    for stem, nct, trial in fiveof5[:30]:
        baseline = trial.get("baseline") or {}
        bN = baseline.get("n") if isinstance(baseline, dict) else None
        print(
            f"  {stem} :: {nct} :: pmid={trial.get('pmid')!r} year={trial.get('year')} "
            f"name={trial.get('name')!r} bN={bN} tN={trial.get('tN')}"
        )
    if len(fiveof5) > 30:
        print(f"  ... and {len(fiveof5) - 30} more")

    # Save machine-readable output too
    out = {
        "scanned": {"reviews": n_reviews, "trials": n_trials},
        "single_counts": dict(single_counts),
        "combined_distribution": {str(k): combined_dist.get(k, 0) for k in range(6)},
        "ge3": n_3plus,
        "ge4": n_4plus,
        "eq5": n_5,
        "top15_reviews_4or5": by_review_4or5.most_common(15),
        "spotcheck_4of5_real_pmid": [
            {
                "review": s,
                "nct": n,
                "pmid": t.get("pmid"),
                "year": t.get("year"),
                "name": t.get("name"),
                "baseline_n": (t.get("baseline") or {}).get("n"),
                "tN": t.get("tN"),
                "cN": t.get("cN"),
            }
            for (s, n, t, _h) in fourof5_with_real_pmid
        ],
        "all_5of5": [
            {
                "review": s,
                "nct": n,
                "pmid": t.get("pmid"),
                "year": t.get("year"),
                "name": t.get("name"),
                "baseline_n": (t.get("baseline") or {}).get("n"),
                "tN": t.get("tN"),
                "cN": t.get("cN"),
            }
            for (s, n, t) in fiveof5
        ],
    }
    out_path = Path("C:/Projects/Finrenone/outputs/synthetic_fixture_sweep.json")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as f:
        json.dump(out, f, indent=2, ensure_ascii=False)
    print(f"\n[saved] {out_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
