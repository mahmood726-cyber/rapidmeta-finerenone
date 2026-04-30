"""Generic v3.0 cross-area scraper. Parametrised by therapy area.

USAGE:
    python outcome_switching/scrape_area.py nephrology
    python outcome_switching/scrape_area.py endocrinology

Replicates the oncology v2.0 3-stage pipeline.
"""
from __future__ import annotations
import json
import sys
import time
import io
import urllib.request
import urllib.parse
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

OUT_DIR = Path(__file__).parent

AREAS = {
    "nephrology": {
        "query": "(\"chronic kidney disease\" OR \"end stage renal disease\" OR \"chronic renal failure\" OR \"diabetic nephropathy\")",
        "slug": "nephrology",
    },
    "endocrinology": {
        "query": "(\"type 2 diabetes\" OR \"obesity\" OR \"hypothyroidism\" OR \"osteoporosis\")",
        "slug": "endocrinology",
    },
}


def fetch_all_ncts(query: str) -> list[dict]:
    base = "https://clinicaltrials.gov/api/v2/studies"
    params = {
        "query.cond": query,
        "filter.overallStatus": "COMPLETED",
        "filter.advanced": "AREA[Phase]COVERAGE[FullMatch]PHASE3 AND AREA[StudyType]Interventional AND AREA[StartDate]RANGE[2015-01-01,MAX] AND AREA[EnrollmentCount]RANGE[500,MAX]",
        "aggFilters": "results:with",
        "fields": "NCTId,BriefTitle,Acronym,Phase,EnrollmentCount,LeadSponsorClass,LeadSponsorName,StartDate,OverallStatus,HasResults,LastUpdatePostDate,StudyFirstPostDate",
        "pageSize": "100",
        "format": "json",
    }
    rows, next_token = [], None
    while True:
        if next_token:
            params["pageToken"] = next_token
        elif "pageToken" in params:
            del params["pageToken"]
        url = base + "?" + urllib.parse.urlencode(params)
        req = urllib.request.Request(url, headers={"User-Agent": "outcome-switching-MA/1.0"})
        with urllib.request.urlopen(req, timeout=30) as r:
            data = json.load(r)
        for s in data.get("studies", []):
            proto = s.get("protocolSection", {})
            ident = proto.get("identificationModule", {})
            status = proto.get("statusModule", {})
            sponsor = proto.get("sponsorCollaboratorsModule", {})
            design = proto.get("designModule", {})
            rows.append({
                "nct_id": ident.get("nctId"),
                "brief_title": ident.get("briefTitle"),
                "acronym": ident.get("acronym"),
                "phase": design.get("phases", []),
                "enrollment": (design.get("enrollmentInfo") or {}).get("count"),
                "start_date": (status.get("startDateStruct") or {}).get("date"),
                "overall_status": status.get("overallStatus"),
                "has_results": s.get("hasResults", False),
                "lead_sponsor": (sponsor.get("leadSponsor") or {}).get("name"),
                "lead_sponsor_class": (sponsor.get("leadSponsor") or {}).get("class"),
                "study_first_post": (status.get("studyFirstPostDateStruct") or {}).get("date"),
                "last_update_post": (status.get("lastUpdatePostDateStruct") or {}).get("date"),
            })
        next_token = data.get("nextPageToken")
        if not next_token:
            break
        time.sleep(0.3)
    return rows


def fetch_current(nct: str) -> dict:
    url = f"https://clinicaltrials.gov/api/v2/studies/{nct}"
    req = urllib.request.Request(url, headers={"User-Agent": "outcome-switching-MA/1.0"})
    with urllib.request.urlopen(req, timeout=30) as r:
        rec = json.load(r)
    om = rec.get("protocolSection", {}).get("outcomesModule", {}) or {}
    return {
        "primary": [{"measure": o.get("measure", ""), "timeFrame": o.get("timeFrame", "")}
                    for o in (om.get("primaryOutcomes") or [])],
    }


def scrape_v1(nct_list: list[str]) -> list[dict]:
    from playwright.sync_api import sync_playwright
    rows = []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        for i, nct in enumerate(nct_list, 1):
            url = f"https://clinicaltrials.gov/study/{nct}?tab=history&a=1"
            try:
                page.goto(url, wait_until="domcontentloaded", timeout=30_000)
                page.wait_for_function(
                    "document.body.innerText.includes('Primary Outcome Measures') || document.title.includes('Error')",
                    timeout=20_000,
                )
                title = page.title()
                block = page.evaluate(
                    """() => {
                        const t = document.body.innerText;
                        const i = t.indexOf('Primary Outcome Measures');
                        const j = t.indexOf('Secondary Outcome Measures', i);
                        return i >= 0 ? t.slice(i, j > 0 ? j : i + 2000) : null;
                    }"""
                )
                rows.append({"nct_id": nct, "version_title": title, "primary_outcome_block": block, "ok": block is not None})
                if i % 25 == 0:
                    print(f"  [{i:4d}/{len(nct_list)}] OK", flush=True)
            except Exception as e:
                rows.append({"nct_id": nct, "error": str(e)})
                print(f"  [{i:4d}/{len(nct_list)}] FAIL {str(e)[:60]}", flush=True)
            time.sleep(0.3)
        browser.close()
    return rows


def main() -> int:
    if len(sys.argv) < 2 or sys.argv[1] not in AREAS:
        print(f"USAGE: python {sys.argv[0]} {{nephrology,endocrinology}}")
        return 1
    area = sys.argv[1]
    cfg = AREAS[area]
    slug = cfg["slug"]

    nct_list_out = OUT_DIR / f"{slug}_p3_nct_list.json"
    v1_out = OUT_DIR / f"{slug}_p3_v1_history.json"
    cur_out = OUT_DIR / f"{slug}_p3_current.json"

    print(f"=== Stage 1: paginate CT.gov for {area} P3 post-2015 with results ===", flush=True)
    nct_meta = fetch_all_ncts(cfg["query"])
    json.dump({"area": area, "extracted_at": "2026-04-30", "n": len(nct_meta), "trials": nct_meta},
              open(nct_list_out, "w", encoding="utf-8"), indent=2, ensure_ascii=False)
    print(f"Got {len(nct_meta)} trials. Wrote {nct_list_out}", flush=True)

    print(f"\n=== Stage 2: Playwright scrape v1 for {len(nct_meta)} trials ===", flush=True)
    nct_list = [r["nct_id"] for r in nct_meta if r["nct_id"]]
    rows = scrape_v1(nct_list)
    json.dump({"area": area, "extracted_at": "2026-04-30", "n": len(rows), "trials": rows},
              open(v1_out, "w", encoding="utf-8"), indent=2, ensure_ascii=False)
    n_ok = sum(1 for r in rows if r.get("ok"))
    print(f"Stage 2 wrote {v1_out} ({n_ok}/{len(rows)} OK)", flush=True)

    print(f"\n=== Stage 3: fetch current primaries for {len(nct_list)} ===", flush=True)
    cur_rows = []
    for i, nct in enumerate(nct_list, 1):
        try:
            ex = fetch_current(nct)
            cur_rows.append({"nct_id": nct, "registered_primary": ex["primary"]})
        except Exception as e:
            cur_rows.append({"nct_id": nct, "error": str(e)})
        if i % 25 == 0:
            print(f"  [{i:4d}/{len(nct_list)}] OK", flush=True)
        time.sleep(0.3)
    json.dump({"area": area, "extracted_at": "2026-04-30", "n": len(cur_rows), "trials": cur_rows},
              open(cur_out, "w", encoding="utf-8"), indent=2, ensure_ascii=False)
    print(f"Stage 3 wrote {cur_out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
