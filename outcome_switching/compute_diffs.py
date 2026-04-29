"""Compute outcome-switching discrepancy metrics from the extracted CT.gov data.

Discrepancy types per Cochrane Handbook on outcome reporting bias + medRxiv 2025.11.06:
1. count_diff: registered_primary count != reported_primary count (silent drop or addition)
2. silent_drop: a registered primary measure has no matching reported primary
3. addition: a reported primary has no matching registered primary
4. promotion: a registered SECONDARY appears as a reported PRIMARY (elevation)
5. demotion: a registered PRIMARY appears as reported SECONDARY (de-prioritisation)
6. timeframe_change: matched primary kept the same measure but changed timeframe materially
7. rename_only: matched primary kept the same intent but renamed the measure cosmetically

Matching uses normalized substring + Jaccard token overlap (>=0.55) — flags any
near-match. Unmatched gets the harder 'silent_drop' / 'addition' label.

Output: hf_outcomes_diffs.json (per-trial flags + summary table).
"""
from __future__ import annotations
import json
import re
import sys
import io
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

OUT_DIR = Path(__file__).parent
RAW = OUT_DIR / "hf_outcomes_raw.json"
DIFFS = OUT_DIR / "hf_outcomes_diffs.json"

STOPWORDS = set("of the and or to in on at by for with a an from as is".split())


def normalize(s: str) -> str:
    s = (s or "").lower()
    s = re.sub(r"[^a-z0-9\s]", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s


def tokens(s: str) -> set[str]:
    return {t for t in normalize(s).split() if t and t not in STOPWORDS and len(t) > 2}


def jaccard(a: set[str], b: set[str]) -> float:
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


def best_match(target: dict, candidates: list[dict], target_field: str, cand_field: str) -> tuple[int, float]:
    """Find best-matching candidate by Jaccard token overlap. Returns (idx, score)."""
    target_tokens = tokens(target.get(target_field, ""))
    if not target_tokens:
        return (-1, 0.0)
    best_idx, best_score = -1, 0.0
    for i, c in enumerate(candidates):
        cand_tokens = tokens(c.get(cand_field, ""))
        s = jaccard(target_tokens, cand_tokens)
        if s > best_score:
            best_score, best_idx = s, i
    return (best_idx, best_score)


MATCH_THRESHOLD = 0.55  # Jaccard >= 0.55 considered same outcome


def compute_trial_diff(trial: dict) -> dict:
    """Per-trial discrepancy flags."""
    if "error" in trial:
        return {"nct_id": trial.get("nct_id"), "error": trial["error"]}

    nct = trial["nct_id"]
    rp = trial.get("registered_primary", []) or []
    rs = trial.get("registered_secondary", []) or []
    pp = trial.get("reported_primary", []) or []
    ps = trial.get("reported_secondary", []) or []

    flags = {
        "nct_id": nct,
        "acronym": trial.get("acronym"),
        "lead_sponsor": trial.get("lead_sponsor"),
        "lead_sponsor_class": trial.get("lead_sponsor_class"),
        "registered_primary_count": len(rp),
        "reported_primary_count": len(pp),
        "count_diff": len(rp) != len(pp),
        "silent_drops": [],
        "additions": [],
        "promotions": [],
        "demotions": [],
        "timeframe_changes": [],
        "rename_only": [],
        "any_switching": False,
        "excluded_from_primary_analysis": trial.get("excluded_from_primary_analysis", False),
    }

    # Match each registered primary to a reported primary (silent_drop if no match)
    matched_reported_idx = set()
    for r in rp:
        idx, score = best_match(r, pp, "measure", "title")
        if score >= MATCH_THRESHOLD:
            matched_reported_idx.add(idx)
            # Within matched pair: check timeframe
            r_tf = normalize(r.get("timeFrame", ""))
            p_tf = normalize(pp[idx].get("timeFrame", ""))
            if r_tf and p_tf and jaccard(set(r_tf.split()), set(p_tf.split())) < 0.5:
                flags["timeframe_changes"].append({
                    "registered": r.get("measure"),
                    "registered_timeframe": r.get("timeFrame"),
                    "reported": pp[idx].get("title"),
                    "reported_timeframe": pp[idx].get("timeFrame"),
                })
            # If wording differs but Jaccard < 0.95, log as cosmetic rename
            if 0.55 <= score < 0.95:
                flags["rename_only"].append({
                    "registered": r.get("measure"),
                    "reported": pp[idx].get("title"),
                    "score": round(score, 3),
                })
        else:
            # Silent drop: was the missing primary instead PROMOTED to secondary in results?
            sec_idx, sec_score = best_match(r, ps, "measure", "title")
            if sec_score >= MATCH_THRESHOLD:
                flags["demotions"].append({
                    "registered": r.get("measure"),
                    "reported_as_secondary": ps[sec_idx].get("title"),
                    "score": round(sec_score, 3),
                })
            else:
                flags["silent_drops"].append({"registered": r.get("measure")})

    # Reported primaries that didn't match any registered primary
    for i, p in enumerate(pp):
        if i in matched_reported_idx:
            continue
        # Was it elevated from registered secondary?
        sec_idx, sec_score = best_match(p, rs, "title", "measure")
        if sec_score >= MATCH_THRESHOLD:
            flags["promotions"].append({
                "registered_as_secondary": rs[sec_idx].get("measure"),
                "reported": p.get("title"),
                "score": round(sec_score, 3),
            })
        else:
            flags["additions"].append({"reported": p.get("title")})

    flags["any_switching"] = bool(
        flags["silent_drops"] or flags["additions"] or flags["promotions"] or flags["demotions"] or flags["timeframe_changes"]
    )
    return flags


def main() -> int:
    with open(RAW, "r", encoding="utf-8") as f:
        data = json.load(f)

    diffs = []
    for trial in data["trials"]:
        diffs.append(compute_trial_diff(trial))

    # Aggregate summary
    primary_pool = [d for d in diffs if not d.get("excluded_from_primary_analysis") and "error" not in d]
    n_primary = len(primary_pool)

    summary = {
        "n_total": len(diffs),
        "n_primary_pool": n_primary,
        "n_excluded_non_hf": sum(1 for d in diffs if d.get("excluded_from_primary_analysis")),
        "any_switching": sum(1 for d in primary_pool if d.get("any_switching")),
        "count_diff": sum(1 for d in primary_pool if d.get("count_diff")),
        "silent_drops": sum(len(d.get("silent_drops", [])) for d in primary_pool),
        "additions": sum(len(d.get("additions", [])) for d in primary_pool),
        "promotions": sum(len(d.get("promotions", [])) for d in primary_pool),
        "demotions": sum(len(d.get("demotions", [])) for d in primary_pool),
        "timeframe_changes": sum(len(d.get("timeframe_changes", [])) for d in primary_pool),
        "rename_only": sum(len(d.get("rename_only", [])) for d in primary_pool),
    }

    # Sponsor breakdown
    sponsor_breakdown = {}
    for d in primary_pool:
        cls = d.get("lead_sponsor_class") or "UNKNOWN"
        sponsor_breakdown.setdefault(cls, {"n": 0, "any_switching": 0})
        sponsor_breakdown[cls]["n"] += 1
        if d.get("any_switching"):
            sponsor_breakdown[cls]["any_switching"] += 1
    summary["sponsor_breakdown"] = sponsor_breakdown

    output = {
        "computed_at": "2026-04-29",
        "match_threshold_jaccard": MATCH_THRESHOLD,
        "summary": summary,
        "trials": diffs,
    }

    with open(DIFFS, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    # Print summary to stdout
    print(f"=== HF Phase 3 outcome-switching summary (k={n_primary} primary pool) ===")
    for k, v in summary.items():
        if k == "sponsor_breakdown":
            print(f"  sponsor_breakdown:")
            for cls, vals in v.items():
                rate = vals["any_switching"] / vals["n"] * 100 if vals["n"] else 0
                print(f"    {cls}: {vals['any_switching']}/{vals['n']} ({rate:.1f}%)")
        else:
            print(f"  {k}: {v}")

    print()
    print("=== Per-trial flags (any_switching=True) ===")
    for d in primary_pool:
        if d.get("any_switching"):
            print(f"  {d['nct_id']} ({d.get('acronym') or '?'}): drops={len(d.get('silent_drops',[]))}, "
                  f"adds={len(d.get('additions',[]))}, prom={len(d.get('promotions',[]))}, "
                  f"dem={len(d.get('demotions',[]))}, tf={len(d.get('timeframe_changes',[]))}")

    print()
    print(f"Wrote {DIFFS}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
