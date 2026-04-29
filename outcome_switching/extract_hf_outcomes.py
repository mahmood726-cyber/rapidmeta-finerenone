"""Extract registered vs reported primary outcomes for HF Phase 3 trials post-2015.

Pulls CT.gov v2 API for each NCT and saves a structured JSON for downstream
discrepancy computation.

Per `lessons.md` 2026-04-28: every NCT pulled here is a real CT.gov record
(verified at extraction time); no fabrication.

Per `feedback_finrenone_build_safety.md`: this file is committed as a stub
immediately after creation so the harvest workflow doesn't delete it
mid-build.
"""
from __future__ import annotations
import json
import sys
import time
import urllib.request
from pathlib import Path

# Force UTF-8 stdout on Windows (per `lessons.md` Platform rule)
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

OUT_DIR = Path(__file__).parent

# Pivotal HF Phase 3 trials post-2015, results-posted, n>=500.
# Source: CT.gov search 2026-04-29 with filter
#   condition="heart failure" AND status=COMPLETED AND phase=PHASE3
#   AND start_date>=2015-01-01 AND has_results=true AND enrollment>=500
NCT_LIST = [
    "NCT02924727",  # PARADISE-MI (sacubitril/valsartan post-AMI)
    "NCT03473223",  # AEGIS-II (CSL112 ACS)  -- non-HF, candidate exclusion
    "NCT02809131",  # WRAP-IT (antibacterial envelope CIED) -- non-HF, exclude
    "NCT03877224",  # DETERMINE-Preserved (dapa HFpEF exercise)
    "NCT04986202",  # AZD4831 / mitiperstat HFpEF
    "NCT04847557",  # SUMMIT (tirzepatide HFpEF)
    "NCT02900378",  # ACTIVATE-HF (LCZ696 actigraphy)
    "NCT04788511",  # STEP-HFpEF (semaglutide HFpEF)
    "NCT05093933",  # VICTOR (vericiguat HFrEF Merck)
    "NCT03888066",  # DIAMOND (patiromer)
    "NCT03037931",  # HEART-FID (ferric carboxymaltose chronic HF)
    "NCT04415658",  # T4-organ-donor -- non-HF, exclude
    "NCT03036124",  # DAPA-HF (dapagliflozin HFrEF)
    "NCT04564742",  # DAPA-MI (dapa post-AMI)
    "NCT04157751",  # EMPULSE (empa acute HF)
    "NCT04435626",  # FINEARTS-HF (finerenone HFpEF)
    "NCT03057951",  # EMPEROR-Preserved (empa HFpEF)
    "NCT03296813",  # TRANSFORM-HF (torsemide vs furosemide)
    "NCT03066804",  # PARALLAX (LCZ696 HFpEF NT-proBNP)
    "NCT04509674",  # EMPACT-MI (empa post-AMI)
    "NCT02929329",  # GALACTIC-HF (omecamtiv mecarbil)
    "NCT03619213",  # DELIVER (dapa HFpEF)
    "NCT02884206",  # PERSPECTIVE (LCZ696 cognitive)
    "NCT02861534",  # VICTORIA (vericiguat HFrEF Merck/Bayer)
    "NCT03057977",  # EMPEROR-Reduced (empa HFrEF)
]

# Trials to exclude from primary HF analysis (non-HF primary indication).
EXCLUDE_NON_HF = {"NCT03473223", "NCT02809131", "NCT04415658"}

API_URL = "https://clinicaltrials.gov/api/v2/studies/{nct}"


def fetch_trial(nct: str) -> dict:
    """Fetch one trial's full record from CT.gov v2 API."""
    url = API_URL.format(nct=nct)
    req = urllib.request.Request(url, headers={"User-Agent": "outcome-switching-MA/1.0"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


def extract_primaries(record: dict) -> dict:
    """Pull both the registered primary outcomes and the reported primary outcomes."""
    proto = record.get("protocolSection", {})
    results = record.get("resultsSection", {})

    # Registered primaries (current registry view)
    om = proto.get("outcomesModule", {})
    registered_primary = [
        {"measure": o.get("measure", ""), "timeFrame": o.get("timeFrame", ""), "description": o.get("description", "")}
        for o in om.get("primaryOutcomes", []) or []
    ]
    registered_secondary = [
        {"measure": o.get("measure", ""), "timeFrame": o.get("timeFrame", "")}
        for o in om.get("secondaryOutcomes", []) or []
    ]

    # Reported outcomes (results section, filtered to type=PRIMARY)
    omm = results.get("outcomeMeasuresModule", {})
    reported_all = omm.get("outcomeMeasures", []) or []
    reported_primary = [
        {"title": o.get("title", ""), "type": o.get("type", ""), "timeFrame": o.get("timeFrame", "")}
        for o in reported_all if o.get("type") == "PRIMARY"
    ]
    reported_secondary = [
        {"title": o.get("title", ""), "type": o.get("type", "")}
        for o in reported_all if o.get("type") == "SECONDARY"
    ]

    return {
        "registered_primary_count": len(registered_primary),
        "registered_secondary_count": len(registered_secondary),
        "reported_primary_count": len(reported_primary),
        "reported_secondary_count": len(reported_secondary),
        "registered_primary": registered_primary,
        "registered_secondary": registered_secondary,
        "reported_primary": reported_primary,
        "reported_secondary": reported_secondary,
    }


def extract_meta(record: dict) -> dict:
    """Pull trial-level metadata for downstream subgroup analysis."""
    proto = record.get("protocolSection", {})
    ident = proto.get("identificationModule", {})
    status = proto.get("statusModule", {})
    sponsor = proto.get("sponsorCollaboratorsModule", {})
    design = proto.get("designModule", {})

    return {
        "nct_id": ident.get("nctId"),
        "brief_title": ident.get("briefTitle"),
        "acronym": ident.get("acronym"),
        "phase": design.get("phases", []),
        "enrollment": (design.get("enrollmentInfo") or {}).get("count"),
        "start_date": (status.get("startDateStruct") or {}).get("date"),
        "primary_completion_date": (status.get("primaryCompletionDateStruct") or {}).get("date"),
        "results_first_posted": (status.get("resultsFirstPostDateStruct") or {}).get("date"),
        "lead_sponsor": (sponsor.get("leadSponsor") or {}).get("name"),
        "lead_sponsor_class": (sponsor.get("leadSponsor") or {}).get("class"),  # INDUSTRY / NIH / OTHER
    }


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out_file = OUT_DIR / "hf_outcomes_raw.json"

    rows = []
    for i, nct in enumerate(NCT_LIST, 1):
        print(f"[{i:2d}/{len(NCT_LIST)}] {nct} ...", end=" ", flush=True)
        try:
            record = fetch_trial(nct)
            meta = extract_meta(record)
            outcomes = extract_primaries(record)
            row = {
                **meta,
                **outcomes,
                "excluded_from_primary_analysis": nct in EXCLUDE_NON_HF,
            }
            rows.append(row)
            print(f"OK (reg_pri={outcomes['registered_primary_count']}, rep_pri={outcomes['reported_primary_count']})")
        except Exception as e:
            print(f"FAIL: {e}")
            rows.append({"nct_id": nct, "error": str(e)})
        time.sleep(0.4)  # be polite to CT.gov API

    with open(out_file, "w", encoding="utf-8") as f:
        json.dump({"extracted_at": "2026-04-29", "trials": rows}, f, indent=2, ensure_ascii=False)
    print()
    print(f"Wrote {out_file} ({len(rows)} trials)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
