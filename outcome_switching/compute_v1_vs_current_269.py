"""v1-vs-current diff for the full 269-trial HF P3/P4 pool.

Reuses logic from compute_v1_vs_current.py but reads:
- hf_history_v1_198.json   (Playwright-scraped v1 for all 269)
- hf_outcomes_269_current.json (CT.gov v2 API current for all 269)

Outputs: hf_v1_vs_current_269.json + per-status / per-sponsor breakdowns
suitable for comparing the v0.2 22-trial pool to the broader 269-trial pool.
"""
from __future__ import annotations
import json
import re
import sys
import io
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

OUT_DIR = Path(__file__).parent
V1 = OUT_DIR / "hf_history_v1_198.json"
CURRENT = OUT_DIR / "hf_outcomes_269_current.json"
RESULT = OUT_DIR / "hf_v1_vs_current_269.json"

STOPWORDS = set("of the and or to in on at by for with a an from as is".split())


def parse_tf_months(text: str) -> float | None:
    if not text:
        return None
    PATTERNS = [
        (re.compile(r"(\d+(?:\.\d+)?)\s*month", re.I), 1.0),
        (re.compile(r"(\d+(?:\.\d+)?)\s*year", re.I), 12.0),
        (re.compile(r"(?:^|\W)(\d+)\s*-?\s*(?:week|wk)", re.I), 1.0 / 4.345),
        (re.compile(r"week\s*(\d+(?:\.\d+)?)", re.I), 1.0 / 4.345),
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
    t = (text or "").lower()
    if any(s in t for s in ["time to first", "time to the first", "time-to-first", "time to cardiovascular", "time to first event", "time to first occurrence", "measure time to"]):
        return "time_to_event"
    if any(s in t for s in ["subjects included", "participants with", "occurrence of the composite", "occurrence of total", "number of subjects", "number of participants", "number of cardiovascular"]):
        return "cumulative_incidence_or_count"
    return "other"


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
    v1_by = {t["nct_id"]: t for t in v1["trials"]}

    rows = []
    for c in cur["trials"]:
        nct = c["nct_id"]
        v1_row = v1_by.get(nct, {})
        if "error" in c or "error" in v1_row:
            rows.append({"nct_id": nct, "error": c.get("error") or v1_row.get("error")})
            continue
        if not v1_row.get("ok"):
            rows.append({"nct_id": nct, "error": "no v1 block"})
            continue

        v1_block = v1_row.get("primary_outcome_block") or ""
        v1_lines = [l.strip() for l in v1_block.splitlines() if l.strip()]
        v1_measure = v1_lines[1] if len(v1_lines) > 1 else None
        v1_tf_match = re.search(r"\[Time Frame:\s*([^\]]+)\]", v1_block)
        v1_tf = v1_tf_match.group(1).strip() if v1_tf_match else None

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
            flags.append("primary_count_change")

        tf_pct = round((cur_tf_months - v1_tf_months) / v1_tf_months * 100, 1) if (v1_tf_months and cur_tf_months) else None

        rows.append({
            "nct_id": nct,
            "acronym": c.get("acronym"),
            "overall_status": c.get("overall_status"),
            "has_results": c.get("has_results"),
            "lead_sponsor_class": c.get("lead_sponsor_class"),
            "phase": c.get("phase"),
            "enrollment": c.get("enrollment"),
            "v1_framework": v1_framework,
            "current_framework": cur_framework,
            "title_jaccard": round(title_score, 3),
            "tf_change_pct": tf_pct,
            "drift_flags": flags,
            "any_drift": bool(flags),
        })

    # Summary breakdowns
    valid = [r for r in rows if "error" not in r]
    summary = {
        "n": len(rows),
        "n_valid": len(valid),
        "n_with_error": len(rows) - len(valid),
        "any_drift": sum(1 for r in valid if r.get("any_drift")),
        "timeframe_change": sum(1 for r in valid if "timeframe_change" in r.get("drift_flags", [])),
        "framework_change": sum(1 for r in valid if "statistical_framework_change" in r.get("drift_flags", [])),
        "title_rewrite": sum(1 for r in valid if "title_rewrite" in r.get("drift_flags", [])),
        "primary_count_change": sum(1 for r in valid if "primary_count_change" in r.get("drift_flags", [])),
    }

    # By status
    by_status = {}
    for r in valid:
        st = r.get("overall_status") or "?"
        by_status.setdefault(st, {"n": 0, "any_drift": 0, "framework_change": 0})
        by_status[st]["n"] += 1
        if r.get("any_drift"):
            by_status[st]["any_drift"] += 1
        if "statistical_framework_change" in r.get("drift_flags", []):
            by_status[st]["framework_change"] += 1
    summary["by_status"] = by_status

    # By sponsor class
    by_sponsor = {}
    for r in valid:
        cls = r.get("lead_sponsor_class") or "?"
        by_sponsor.setdefault(cls, {"n": 0, "any_drift": 0, "framework_change": 0})
        by_sponsor[cls]["n"] += 1
        if r.get("any_drift"):
            by_sponsor[cls]["any_drift"] += 1
        if "statistical_framework_change" in r.get("drift_flags", []):
            by_sponsor[cls]["framework_change"] += 1
    summary["by_sponsor_class"] = by_sponsor

    # By has_results
    by_results = {True: {"n": 0, "any_drift": 0}, False: {"n": 0, "any_drift": 0}}
    for r in valid:
        hr = bool(r.get("has_results"))
        by_results[hr]["n"] += 1
        if r.get("any_drift"):
            by_results[hr]["any_drift"] += 1
    summary["by_has_results"] = {str(k): v for k, v in by_results.items()}

    output = {"computed_at": "2026-04-30", "summary": summary, "trials": rows}
    json.dump(output, open(RESULT, "w", encoding="utf-8"), indent=2, ensure_ascii=False)

    print("=== n=269 HF P3/P4 v1-vs-current drift summary ===")
    for k, v in summary.items():
        if k.startswith("by_"):
            print(f"  {k}:")
            for kk, vv in v.items():
                rate = vv["any_drift"] / vv["n"] * 100 if vv["n"] else 0
                fc_rate = (vv.get("framework_change", 0) / vv["n"] * 100) if vv["n"] else 0
                print(f"    {kk}: {vv['any_drift']}/{vv['n']} ({rate:.1f}%) any_drift; "
                      f"{vv.get('framework_change', 0)}/{vv['n']} ({fc_rate:.1f}%) framework_change")
        else:
            print(f"  {k}: {v}")
    print()
    print(f"Wrote {RESULT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
