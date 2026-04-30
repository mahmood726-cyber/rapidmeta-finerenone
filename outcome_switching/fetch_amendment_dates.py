"""Fetch lastUpdatePostDate + studyFirstPostDate for HF + oncology pools.

Output: hf_oncology_amendment_proxy.json with one row per trial.
The "amendment proxy" is days between first-post and last-update — longer
intervals = more time for registry edits = higher correlation with
any_drift hypothesised.

Doesn't capture true amendment count (would require Playwright on each
?tab=history page) but the date interval is a reasonable proxy.
"""
from __future__ import annotations
import json
import sys
import time
import io
import urllib.request
from pathlib import Path
from datetime import datetime

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

OUT_DIR = Path(__file__).parent
OUT = OUT_DIR / "hf_oncology_amendment_proxy.json"


def fetch_dates(nct: str) -> dict:
    url = f"https://clinicaltrials.gov/api/v2/studies/{nct}?format=json&fields=protocolSection.statusModule"
    req = urllib.request.Request(url, headers={"User-Agent": "outcome-switching-MA/1.0"})
    with urllib.request.urlopen(req, timeout=20) as r:
        rec = json.load(r)
    sm = rec.get("protocolSection", {}).get("statusModule", {}) or {}
    return {
        "study_first_post": (sm.get("studyFirstPostDateStruct") or {}).get("date"),
        "results_first_post": (sm.get("resultsFirstPostDateStruct") or {}).get("date"),
        "last_update_post": (sm.get("lastUpdatePostDateStruct") or {}).get("date"),
    }


def days_between(a: str | None, b: str | None) -> int | None:
    if not a or not b:
        return None
    try:
        da = datetime.strptime(a, "%Y-%m-%d")
        db = datetime.strptime(b, "%Y-%m-%d")
        return abs((db - da).days)
    except (ValueError, TypeError):
        return None


def main() -> int:
    # Combined HF + oncology pool
    hf = json.load(open(OUT_DIR / "hf_p3p4_198_nct_list.json", "r", encoding="utf-8"))
    onc = json.load(open(OUT_DIR / "oncology_p3_nct_list.json", "r", encoding="utf-8"))
    hf_diff = json.load(open(OUT_DIR / "hf_v1_vs_current_269.json", "r", encoding="utf-8"))
    onc_diff = json.load(open(OUT_DIR / "oncology_p3_v1_vs_current.json", "r", encoding="utf-8"))

    hf_drift = {t["nct_id"]: t.get("any_drift", False) for t in hf_diff["trials"]}
    onc_drift = {t["nct_id"]: t.get("any_drift", False) for t in onc_diff["trials"]}

    rows = []
    pool = [(t, "HF") for t in hf["trials"]] + [(t, "Oncology") for t in onc["trials"]]
    for i, (m, area) in enumerate(pool, 1):
        nct = m["nct_id"]
        try:
            d = fetch_dates(nct)
            interval = days_between(d["study_first_post"], d["last_update_post"])
            any_drift = (hf_drift if area == "HF" else onc_drift).get(nct, False)
            rows.append({
                "nct_id": nct,
                "area": area,
                "lead_sponsor_class": m.get("lead_sponsor_class"),
                "study_first_post": d["study_first_post"],
                "last_update_post": d["last_update_post"],
                "results_first_post": d["results_first_post"],
                "first_to_last_days": interval,
                "any_drift": any_drift,
            })
        except Exception as e:
            rows.append({"nct_id": nct, "area": area, "error": str(e)})
        if i % 50 == 0:
            print(f"  [{i}/{len(pool)}]", flush=True)
        time.sleep(0.25)

    # Compute correlation: mean first-to-last days for any_drift=True vs False
    valid = [r for r in rows if r.get("first_to_last_days") is not None]
    drift_days = [r["first_to_last_days"] for r in valid if r.get("any_drift")]
    no_drift_days = [r["first_to_last_days"] for r in valid if not r.get("any_drift")]

    summary = {
        "n": len(valid),
        "n_with_drift": len(drift_days),
        "n_without_drift": len(no_drift_days),
        "mean_days_with_drift": round(sum(drift_days) / len(drift_days), 1) if drift_days else None,
        "mean_days_without_drift": round(sum(no_drift_days) / len(no_drift_days), 1) if no_drift_days else None,
        "median_days_with_drift": sorted(drift_days)[len(drift_days)//2] if drift_days else None,
        "median_days_without_drift": sorted(no_drift_days)[len(no_drift_days)//2] if no_drift_days else None,
    }

    # Per-area
    by_area = {}
    for area in ["HF", "Oncology"]:
        a_rows = [r for r in valid if r["area"] == area]
        a_drift = [r["first_to_last_days"] for r in a_rows if r.get("any_drift")]
        a_no = [r["first_to_last_days"] for r in a_rows if not r.get("any_drift")]
        by_area[area] = {
            "n": len(a_rows),
            "mean_days_with_drift": round(sum(a_drift)/len(a_drift), 1) if a_drift else None,
            "mean_days_without_drift": round(sum(a_no)/len(a_no), 1) if a_no else None,
            "n_with_drift": len(a_drift),
            "n_without_drift": len(a_no),
        }
    summary["by_area"] = by_area

    json.dump({"computed_at": "2026-04-30", "summary": summary, "trials": rows},
              open(OUT, "w", encoding="utf-8"), indent=2, ensure_ascii=False)

    print()
    print("=== Amendment-proxy (first-post to last-update days) vs any_drift ===")
    for k, v in summary.items():
        if k == "by_area":
            print(f"  by_area:")
            for a, av in v.items():
                print(f"    {a}: n={av['n']}  drifters={av['n_with_drift']} mean={av['mean_days_with_drift']}d  non-drifters={av['n_without_drift']} mean={av['mean_days_without_drift']}d")
        else:
            print(f"  {k}: {v}")
    print()
    print(f"Wrote {OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
