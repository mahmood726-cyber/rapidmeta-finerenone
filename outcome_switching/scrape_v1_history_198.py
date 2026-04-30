"""Scale v1 history scraping to all 198 P3/P4 HF trials post-2015.

Drops the n>=500 + has_results gates from the v0.2 sweep. Includes
TERMINATED + WITHDRAWN trials (where prereg drift is likely highest).

Pagination: CT.gov v2 API search endpoint with pageToken cursor.
Then Playwright Python for each NCT's ?tab=history&a=1 page.

PREREQUISITES (already installed): playwright + chromium

USAGE:
    python outcome_switching/scrape_v1_history_198.py
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
NCT_LIST_OUT = OUT_DIR / "hf_p3p4_198_nct_list.json"
RAW_OUT = OUT_DIR / "hf_history_v1_198.json"


def fetch_all_ncts() -> list[dict]:
    """Paginate the CT.gov v2 search endpoint to get all P3/P4 HF post-2015 trials."""
    base = "https://clinicaltrials.gov/api/v2/studies"
    params = {
        "query.cond": '"heart failure"',
        "filter.overallStatus": "COMPLETED|TERMINATED|WITHDRAWN",
        "filter.advanced": "AREA[Phase]COVERAGE[FullMatch](PHASE3 OR PHASE4) AND AREA[StudyType]Interventional AND AREA[StartDate]RANGE[2015-01-01,MAX]",
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
                print(f"[{i:3d}/{len(nct_list)}] {nct} {'OK' if block else 'NO_PRIMARY'} ({len(block or '')} chars)", flush=True)
            except Exception as e:
                row = {"nct_id": nct, "error": str(e)}
                print(f"[{i:3d}/{len(nct_list)}] {nct} FAIL {str(e)[:80]}", flush=True)
            rows.append(row)
            time.sleep(0.4)
        browser.close()
    return rows


def main() -> int:
    print("=== Stage 1: paginate CT.gov for full HF P3/P4 post-2015 list ===", flush=True)
    nct_meta = fetch_all_ncts()
    json.dump({"extracted_at": "2026-04-30", "n": len(nct_meta), "trials": nct_meta},
              open(NCT_LIST_OUT, "w", encoding="utf-8"), indent=2, ensure_ascii=False)
    print(f"Got {len(nct_meta)} trials. Wrote {NCT_LIST_OUT}", flush=True)

    print()
    print(f"=== Stage 2: Playwright scrape v1 history for {len(nct_meta)} trials ===", flush=True)
    nct_list = [r["nct_id"] for r in nct_meta if r["nct_id"]]
    rows = scrape_v1(nct_list)
    json.dump({"extracted_at": "2026-04-30", "n": len(rows), "trials": rows},
              open(RAW_OUT, "w", encoding="utf-8"), indent=2, ensure_ascii=False)
    n_ok = sum(1 for r in rows if r.get("ok"))
    print()
    print(f"Wrote {RAW_OUT} ({n_ok}/{len(rows)} OK)", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
