"""Fetch current registered primary outcomes for all 269 P3/P4 HF trials.

Reuses extract_hf_outcomes.py logic but loops the 269 NCT list from
hf_p3p4_198_nct_list.json. Output: hf_outcomes_269_current.json.
"""
from __future__ import annotations
import json
import sys
import time
import io
import urllib.request
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

OUT_DIR = Path(__file__).parent
NCT_LIST_IN = OUT_DIR / "hf_p3p4_198_nct_list.json"
OUT = OUT_DIR / "hf_outcomes_269_current.json"

API_URL = "https://clinicaltrials.gov/api/v2/studies/{nct}"


def fetch(nct: str) -> dict:
    url = API_URL.format(nct=nct)
    req = urllib.request.Request(url, headers={"User-Agent": "outcome-switching-MA/1.0"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


def extract(record: dict) -> dict:
    proto = record.get("protocolSection", {})
    om = proto.get("outcomesModule", {}) or {}
    primary = [
        {"measure": o.get("measure", ""), "timeFrame": o.get("timeFrame", "")}
        for o in (om.get("primaryOutcomes") or [])
    ]
    secondary = [
        {"measure": o.get("measure", ""), "timeFrame": o.get("timeFrame", "")}
        for o in (om.get("secondaryOutcomes") or [])
    ]
    return {"primary": primary, "secondary": secondary}


def main() -> int:
    nct_meta = json.load(open(NCT_LIST_IN, "r", encoding="utf-8"))["trials"]
    rows = []
    for i, m in enumerate(nct_meta, 1):
        nct = m["nct_id"]
        try:
            rec = fetch(nct)
            ex = extract(rec)
            row = {**m, "registered_primary": ex["primary"], "registered_secondary": ex["secondary"]}
            print(f"[{i:3d}/{len(nct_meta)}] {nct} OK (k_pri={len(ex['primary'])})", flush=True)
        except Exception as e:
            row = {**m, "error": str(e)}
            print(f"[{i:3d}/{len(nct_meta)}] {nct} FAIL {e}", flush=True)
        rows.append(row)
        time.sleep(0.3)
    json.dump({"extracted_at": "2026-04-30", "n": len(rows), "trials": rows},
              open(OUT, "w", encoding="utf-8"), indent=2, ensure_ascii=False)
    print(f"Wrote {OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
