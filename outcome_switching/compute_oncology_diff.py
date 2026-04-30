"""v1-vs-current diff for the oncology Phase 3 pool. Mirrors compute_v1_vs_current_269.py
applied to the oncology dataset (oncology_p3_v1_history.json + oncology_p3_current.json
+ oncology_p3_nct_list.json metadata).

Same drift typology as HF: timeframe_change, statistical_framework_change,
title_rewrite, primary_count_change. Plus content-change candidate detection
via the same FRAMEWORK_TOKENS-stripped Jaccard.

Output breakdowns by sponsor class to compare against HF's v0.3 finding
("all 5 framework changes are industry-sponsored").
"""
from __future__ import annotations
import json
import re
import sys
import io
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

OUT_DIR = Path(__file__).parent
V1 = OUT_DIR / "oncology_p3_v1_history.json"
CURRENT = OUT_DIR / "oncology_p3_current.json"
NCT_META = OUT_DIR / "oncology_p3_nct_list.json"
RESULT = OUT_DIR / "oncology_p3_v1_vs_current.json"

STOPWORDS = set("of the and or to in on at by for with a an from as is".split())
FRAMEWORK_TOKENS = set("""
time occurrence number subjects participants included first cumulative incidence
rate count change baseline week month year day from until between within during
mean median total all-cause primary secondary outcome endpoint composite measure
hierarchical assessed measured determined evaluated proportion percentage
duration follow-up follow up baseline-to randomization randomisation up
analysis cutoff date through approximately approximatley study completion
group treatment arm placebo
""".split())


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
    if any(s in t for s in ["time to first", "time to the first", "time-to-first", "time to event", "time to progression", "progression-free survival", "overall survival",
                            "time to first occurrence", "median survival", "hazard ratio"]):
        return "time_to_event"
    if any(s in t for s in ["subjects included", "participants with", "number of subjects", "number of participants",
                            "objective response rate", "response rate", "response evaluation", "complete response", "partial response",
                            "occurrence of the composite", "occurrence of total", "rate of"]):
        return "rate_or_count"
    return "other"


def tokens_raw(s: str) -> set[str]:
    s = re.sub(r"[^a-z0-9\s]", " ", (s or "").lower())
    return {t for t in s.split() if t and t not in STOPWORDS and len(t) > 2}


def tokens_content(s: str) -> set[str]:
    return tokens_raw(s) - FRAMEWORK_TOKENS


def jaccard(A: set[str], B: set[str]) -> float:
    if not A or not B:
        return 0.0
    return len(A & B) / len(A | B)


def main() -> int:
    v1 = json.load(open(V1, "r", encoding="utf-8"))
    cur = json.load(open(CURRENT, "r", encoding="utf-8"))
    meta = json.load(open(NCT_META, "r", encoding="utf-8"))

    v1_by = {t["nct_id"]: t for t in v1["trials"]}
    meta_by = {t["nct_id"]: t for t in meta["trials"]}

    rows = []
    for c in cur["trials"]:
        nct = c["nct_id"]
        v1_row = v1_by.get(nct, {})
        m = meta_by.get(nct, {})
        if "error" in c or "error" in v1_row or not v1_row.get("ok"):
            rows.append({"nct_id": nct, "error": c.get("error") or v1_row.get("error") or "no v1 block"})
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

        title_jac = jaccard(tokens_raw(v1_measure or ""), tokens_raw(cur_measure or ""))
        content_jac = jaccard(tokens_content(v1_measure or ""), tokens_content(cur_measure or ""))

        flags = []
        if v1_tf_months and cur_tf_months and abs(v1_tf_months - cur_tf_months) / v1_tf_months > 0.05:
            flags.append("timeframe_change")
        if framework_change:
            flags.append("statistical_framework_change")
        if 0 < title_jac < 0.85:
            flags.append("title_rewrite")
        if len(cur_primaries) != 1 and v1_measure:
            flags.append("primary_count_change")
        is_content_candidate = content_jac < 0.30 and title_jac < 0.50
        if is_content_candidate:
            flags.append("content_change_candidate")

        tf_pct = round((cur_tf_months - v1_tf_months) / v1_tf_months * 100, 1) if (v1_tf_months and cur_tf_months) else None

        rows.append({
            "nct_id": nct,
            "acronym": m.get("acronym"),
            "lead_sponsor_class": m.get("lead_sponsor_class"),
            "lead_sponsor": m.get("lead_sponsor"),
            "enrollment": m.get("enrollment"),
            "v1_measure": (v1_measure or "")[:200],
            "current_measure": (cur_measure or "")[:200],
            "v1_framework": v1_framework,
            "current_framework": cur_framework,
            "title_jaccard": round(title_jac, 3),
            "content_jaccard": round(content_jac, 3),
            "tf_change_pct": tf_pct,
            "drift_flags": flags,
            "any_drift": bool(flags),
        })

    valid = [r for r in rows if "error" not in r]
    summary = {
        "n": len(rows),
        "n_valid": len(valid),
        "any_drift": sum(1 for r in valid if r.get("any_drift")),
        "timeframe_change": sum(1 for r in valid if "timeframe_change" in r.get("drift_flags", [])),
        "framework_change": sum(1 for r in valid if "statistical_framework_change" in r.get("drift_flags", [])),
        "title_rewrite": sum(1 for r in valid if "title_rewrite" in r.get("drift_flags", [])),
        "primary_count_change": sum(1 for r in valid if "primary_count_change" in r.get("drift_flags", [])),
        "content_change_candidate": sum(1 for r in valid if "content_change_candidate" in r.get("drift_flags", [])),
    }

    by_sponsor = {}
    for r in valid:
        cls = r.get("lead_sponsor_class") or "?"
        by_sponsor.setdefault(cls, {"n": 0, "any_drift": 0, "framework_change": 0, "content_change_candidate": 0})
        by_sponsor[cls]["n"] += 1
        if r.get("any_drift"):
            by_sponsor[cls]["any_drift"] += 1
        if "statistical_framework_change" in r.get("drift_flags", []):
            by_sponsor[cls]["framework_change"] += 1
        if "content_change_candidate" in r.get("drift_flags", []):
            by_sponsor[cls]["content_change_candidate"] += 1
    summary["by_sponsor_class"] = by_sponsor

    json.dump({"computed_at": "2026-04-30", "summary": summary, "trials": rows},
              open(RESULT, "w", encoding="utf-8"), indent=2, ensure_ascii=False)

    print(f"=== Oncology P3 (n={len(rows)}) v1-vs-current drift summary ===")
    for k, v in summary.items():
        if k == "by_sponsor_class":
            print(f"  {k}:")
            for cls, vv in v.items():
                drift_pct = vv["any_drift"] / vv["n"] * 100 if vv["n"] else 0
                fc_pct = vv["framework_change"] / vv["n"] * 100 if vv["n"] else 0
                cc_pct = vv["content_change_candidate"] / vv["n"] * 100 if vv["n"] else 0
                print(f"    {cls}: {vv['any_drift']}/{vv['n']} ({drift_pct:.1f}%) any; "
                      f"{vv['framework_change']} ({fc_pct:.1f}%) framework; "
                      f"{vv['content_change_candidate']} ({cc_pct:.1f}%) content-candidate")
        else:
            print(f"  {k}: {v}")
    print()
    print(f"Wrote {RESULT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
