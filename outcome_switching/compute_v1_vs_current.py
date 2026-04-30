"""Compute v1-vs-current outcome drift across the full n=22 HF P3 pool.

Reads:
- hf_history_v1_full.json (Playwright-scraped v1 primary outcomes)
- hf_outcomes_raw.json (v2 API current registered primary outcomes)

For each trial, extracts the v1 timeframe (regex on the rendered text),
compares to current timeframe, and flags drift types: timeframe_change,
statistical_framework_change (time-to-event vs cumulative-incidence),
title_rewrite, primary_count_change.

Output: hf_v1_vs_current_full.json + summary table to stdout.
"""
from __future__ import annotations
import json
import re
import sys
import io
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

OUT_DIR = Path(__file__).parent
V1 = OUT_DIR / "hf_history_v1_full.json"
CURRENT = OUT_DIR / "hf_outcomes_raw.json"
RESULT = OUT_DIR / "hf_v1_vs_current_full.json"

# Regex to extract a numerical month value from timeFrame strings.
# Captures patterns like "42 months", "approximately 3 years", "208 weeks", "1040 days"
TF_PATTERNS = [
    (re.compile(r"(\d+(?:\.\d+)?)\s*month", re.I), 1.0),
    (re.compile(r"(\d+(?:\.\d+)?)\s*year", re.I), 12.0),
    (re.compile(r"(\d+)\s*week", re.I), 1.0 / 4.345),
    (re.compile(r"(\d+)\s*day", re.I), 1.0 / 30.44),
]


def parse_tf_months(text: str) -> float | None:
    """Extract the LARGEST month-equivalent number from a timeFrame string.

    v0.3 fix: previous version returned the FIRST match, which broke on
    timeFrames like 'baseline (week 0) to end of treatment (week 52)' —
    where 'week 0' parsed to 0 instead of the meaningful endpoint at
    week 52. Also handles 'Week16' (no space) by relaxing the \\s*
    constraint to allow zero whitespace.
    """
    if not text:
        return None
    # Patterns with relaxed whitespace (accept 'Week16' as 16 weeks)
    PATTERNS = [
        (re.compile(r"(\d+(?:\.\d+)?)\s*month", re.I), 1.0),
        (re.compile(r"(\d+(?:\.\d+)?)\s*year", re.I), 12.0),
        (re.compile(r"(?:^|\W)(\d+)\s*-?\s*(?:week|wk)", re.I), 1.0 / 4.345),
        (re.compile(r"week\s*(\d+(?:\.\d+)?)", re.I), 1.0 / 4.345),  # "Week 16" or "Week16"
        (re.compile(r"(\d+)\s*day", re.I), 1.0 / 30.44),
    ]
    candidates = []
    for pat, mult in PATTERNS:
        for m in pat.finditer(text):
            try:
                v = float(m.group(1)) * mult
                if v > 0:
                    candidates.append(v)
            except (TypeError, ValueError):
                continue
    return max(candidates) if candidates else None


def detect_stat_framework(text: str) -> str:
    """Classify primary-outcome statistical framework from the measure wording."""
    t = (text or "").lower()
    if any(s in t for s in ["time to first", "time to the first", "time-to-first", "time to cardiovascular", "time to first event", "time to first occurrence", "measure time to"]):
        return "time_to_event"
    if any(s in t for s in ["subjects included", "participants with", "occurrence of the composite", "occurrence of total", "number of subjects", "number of participants", "number of cardiovascular"]):
        return "cumulative_incidence_or_count"
    return "other"


# Stopwords for Jaccard token overlap on titles
STOPWORDS = set("of the and or to in on at by for with a an from as is".split())


def jaccard_tokens(a: str, b: str) -> float:
    def toks(s):
        s = re.sub(r"[^a-z0-9\s]", " ", (s or "").lower())
        return {t for t in s.split() if t and t not in STOPWORDS and len(t) > 2}
    A, B = toks(a), toks(b)
    if not A or not B:
        return 0.0
    return len(A & B) / len(A | B)


def main() -> int:
    v1 = json.load(open(V1, "r", encoding="utf-8"))
    cur = json.load(open(CURRENT, "r", encoding="utf-8"))

    cur_by_nct = {t["nct_id"]: t for t in cur["trials"]}
    EXCLUDE = {"NCT03473223", "NCT02809131", "NCT04415658"}  # non-HF excludes

    rows = []
    for v1_row in v1["trials"]:
        nct = v1_row["nct_id"]
        if nct in EXCLUDE:
            continue
        if not v1_row.get("ok"):
            rows.append({"nct_id": nct, "error": v1_row.get("error", "no v1")})
            continue
        c = cur_by_nct.get(nct)
        if not c:
            rows.append({"nct_id": nct, "error": "no current"})
            continue

        v1_block = v1_row["primary_outcome_block"] or ""
        # Parse v1 measure (first non-header line) and timeframe
        v1_lines = [l.strip() for l in v1_block.splitlines() if l.strip()]
        v1_measure = v1_lines[1] if len(v1_lines) > 1 else None
        v1_tf_match = re.search(r"\[Time Frame:\s*([^\]]+)\]", v1_block)
        v1_tf = v1_tf_match.group(1).strip() if v1_tf_match else None

        # Current primaries (use the FIRST primary as representative when there are >1)
        cur_primaries = c.get("registered_primary", []) or []
        cur_measure = cur_primaries[0]["measure"] if cur_primaries else None
        cur_tf = cur_primaries[0]["timeFrame"] if cur_primaries else None

        v1_tf_months = parse_tf_months(v1_tf or "")
        cur_tf_months = parse_tf_months(cur_tf or "")

        v1_framework = detect_stat_framework(v1_measure)
        cur_framework = detect_stat_framework(cur_measure)
        framework_change = (
            v1_framework != "other"
            and cur_framework != "other"
            and v1_framework != cur_framework
        )

        title_score = jaccard_tokens(v1_measure or "", cur_measure or "")

        flags = []
        if v1_tf_months and cur_tf_months and abs(v1_tf_months - cur_tf_months) / v1_tf_months > 0.05:
            flags.append("timeframe_change")
        if framework_change:
            flags.append("statistical_framework_change")
        if 0 < title_score < 0.85:
            flags.append("title_rewrite")
        if len(cur_primaries) != 1 and v1_measure:
            # v1 typically has a single primary; flag count change
            flags.append("primary_count_change")

        rows.append({
            "nct_id": nct,
            "acronym": c.get("acronym"),
            "v1_measure": v1_measure,
            "v1_timeframe": v1_tf,
            "v1_timeframe_months": v1_tf_months,
            "v1_framework": v1_framework,
            "current_measure": cur_measure,
            "current_timeframe": cur_tf,
            "current_timeframe_months": cur_tf_months,
            "current_framework": cur_framework,
            "current_primary_count": len(cur_primaries),
            "title_jaccard": round(title_score, 3),
            "tf_change_pct": round((cur_tf_months - v1_tf_months) / v1_tf_months * 100, 1) if (v1_tf_months and cur_tf_months) else None,
            "drift_flags": flags,
            "any_drift": bool(flags),
        })

    summary = {
        "n": len(rows),
        "any_drift": sum(1 for r in rows if r.get("any_drift")),
        "timeframe_change": sum(1 for r in rows if "timeframe_change" in r.get("drift_flags", [])),
        "framework_change": sum(1 for r in rows if "statistical_framework_change" in r.get("drift_flags", [])),
        "title_rewrite": sum(1 for r in rows if "title_rewrite" in r.get("drift_flags", [])),
        "primary_count_change": sum(1 for r in rows if "primary_count_change" in r.get("drift_flags", [])),
    }

    # Median tf change pct (compression)
    tf_changes = [r["tf_change_pct"] for r in rows if r.get("tf_change_pct") is not None]
    if tf_changes:
        tf_changes_sorted = sorted(tf_changes)
        n = len(tf_changes_sorted)
        median_tf = tf_changes_sorted[n // 2] if n % 2 else (tf_changes_sorted[n // 2 - 1] + tf_changes_sorted[n // 2]) / 2
        summary["timeframe_change_median_pct"] = round(median_tf, 1)
        summary["timeframe_change_min_pct"] = round(min(tf_changes), 1)
        summary["timeframe_change_max_pct"] = round(max(tf_changes), 1)
        summary["timeframe_compression_n"] = sum(1 for t in tf_changes if t < 0)
        summary["timeframe_extension_n"] = sum(1 for t in tf_changes if t > 0)

    output = {"computed_at": "2026-04-30", "summary": summary, "trials": rows}
    json.dump(output, open(RESULT, "w", encoding="utf-8"), indent=2, ensure_ascii=False)

    # Print summary
    print("=== n=22 HF Phase 3 v1-vs-current drift summary ===")
    for k, v in summary.items():
        print(f"  {k}: {v}")
    print()
    print("=== Per-trial summary (drift only) ===")
    print(f"  {'NCT':<12} {'acro':<20} {'TF Δ%':>8}  flags")
    for r in rows:
        if not r.get("any_drift"):
            continue
        tf = f"{r.get('tf_change_pct'):>+.1f}%" if r.get("tf_change_pct") is not None else "?"
        print(f"  {r['nct_id']:<12} {(r.get('acronym') or '?'):<20} {tf:>8}  {','.join(r.get('drift_flags', []))}")
    print()
    print(f"Wrote {RESULT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
