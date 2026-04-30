"""v2.0 cross-therapeutic-area expansion: oncology Phase 3 trials.

Pulls all P3 oncology trials post-2015 with results posted, then scrapes v1
history. Gate kept to results-posted to keep pool size manageable; can be
expanded to all-status later. Replicates the n=269 HF methodology on a
different therapeutic area to test if the 7.1% substantive-drift rate
generalises.
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
NCT_LIST_OUT = OUT_DIR / "oncology_p3_nct_list.json"
RAW_OUT = OUT_DIR / "oncology_p3_v1_history.json"
CURRENT_OUT = OUT_DIR / "oncology_p3_current.json"


def fetch_all_ncts() -> list[dict]:
    base = "https://clinicaltrials.gov/api/v2/studies"
    params = {
        "query.cond": "cancer",
        "filter.overallStatus": "COMPLETED",
        "filter.advanced": "AREA[Phase]COVERAGE[FullMatch]PHASE3 AND AREA[StudyType]Interventional AND AREA[StartDate]RANGE[2015-01-01,MAX] AND AREA[ResultsFirstPostDate]EXIST",
        "fields": "NCTId,BriefTitle,Acronym,Phase,EnrollmentCount,LeadSponsorClass,LeadSponsorName,StartDate,OverallStatus,HasResults",
        "pageSize": "100",
        "format": "json",
    }
    rows = []
    next_token = None
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
            })
        next_token = data.get("nextPageToken")
        if not next_token:
            break
        time.sleep(0.3)
    return rows


def fetch_current_primary(nct: str) -> dict:
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
                row = {"nct_id": nct, "version_title": title, "primary_outcome_block": block, "ok": block is not None}
                if i % 50 == 0:
                    print(f"[{i:4d}/{len(nct_list)}] {nct} OK", flush=True)
            except Exception as e:
                row = {"nct_id": nct, "error": str(e)}
                print(f"[{i:4d}/{len(nct_list)}] {nct} FAIL {str(e)[:60]}", flush=True)
            rows.append(row)
            time.sleep(0.3)
        browser.close()
    return rows


def main() -> int:
    print("=== Stage 1: paginate CT.gov for oncology P3 post-2015 with results ===", flush=True)
    nct_meta = fetch_all_ncts()
    json.dump({"extracted_at": "2026-04-30", "n": len(nct_meta), "trials": nct_meta},
              open(NCT_LIST_OUT, "w", encoding="utf-8"), indent=2, ensure_ascii=False)
    print(f"Got {len(nct_meta)} trials. Wrote {NCT_LIST_OUT}", flush=True)

    if len(nct_meta) > 600:
        print(f"WARNING: pool size {len(nct_meta)} is large; consider filtering further", flush=True)

    print()
    print(f"=== Stage 2: Playwright scrape v1 for {len(nct_meta)} trials ===", flush=True)
    nct_list = [r["nct_id"] for r in nct_meta if r["nct_id"]]
    rows = scrape_v1(nct_list)
    json.dump({"extracted_at": "2026-04-30", "n": len(rows), "trials": rows},
              open(RAW_OUT, "w", encoding="utf-8"), indent=2, ensure_ascii=False)
    n_ok = sum(1 for r in rows if r.get("ok"))
    print(f"Stage 2 wrote {RAW_OUT} ({n_ok}/{len(rows)} OK)", flush=True)

    print()
    print(f"=== Stage 3: fetch current primaries for {len(nct_list)} ===", flush=True)
    cur_rows = []
    for i, nct in enumerate(nct_list, 1):
        try:
            ex = fetch_current_primary(nct)
            cur_rows.append({"nct_id": nct, "registered_primary": ex["primary"]})
        except Exception as e:
            cur_rows.append({"nct_id": nct, "error": str(e)})
        if i % 50 == 0:
            print(f"[{i:4d}/{len(nct_list)}] current OK", flush=True)
        time.sleep(0.3)
    json.dump({"extracted_at": "2026-04-30", "n": len(cur_rows), "trials": cur_rows},
              open(CURRENT_OUT, "w", encoding="utf-8"), indent=2, ensure_ascii=False)
    print(f"Stage 3 wrote {CURRENT_OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
