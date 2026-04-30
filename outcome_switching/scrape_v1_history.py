"""Scale the n=5 v1-vs-current outcome-switching audit to the full n=22 HF P3 pool.

Uses Playwright Python (not the MCP variant — runs its own Chromium) to fetch
each trial's `?tab=history&a=1` page and extract the Primary Outcome Measures
block from the rendered DOM.

PREREQUISITES:
    pip install playwright
    playwright install chromium

USAGE:
    python outcome_switching/scrape_v1_history.py

Per `feedback_finrenone_build_safety.md`: this script is committed before
running so the harvest peer-review workflow can't delete it mid-run.
"""
from __future__ import annotations
import json
import sys
import time
import io
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

OUT_DIR = Path(__file__).parent
RAW_OUT = OUT_DIR / "hf_history_v1_full.json"

# 22-trial primary pool (the 25 from extract_hf_outcomes minus 3 non-HF excludes).
# Already-scraped 5 are included so we get a single complete v1 corpus.
NCT_LIST = [
    "NCT02924727",  # PARADISE-MI
    "NCT03877224",  # DETERMINE-Preserved
    "NCT04986202",  # AZD4831 / mitiperstat
    "NCT04847557",  # SUMMIT
    "NCT02900378",  # ACTIVATE-HF
    "NCT04788511",  # STEP-HFpEF
    "NCT05093933",  # VICTOR
    "NCT03888066",  # DIAMOND
    "NCT03037931",  # HEART-FID
    "NCT03036124",  # DAPA-HF (already in v0.1)
    "NCT04564742",  # DAPA-MI
    "NCT04157751",  # EMPULSE
    "NCT04435626",  # FINEARTS-HF (already in v0.1)
    "NCT03057951",  # EMPEROR-Preserved
    "NCT03296813",  # TRANSFORM-HF
    "NCT03066804",  # PARALLAX
    "NCT04509674",  # EMPACT-MI
    "NCT02929329",  # GALACTIC-HF (already in v0.1)
    "NCT03619213",  # DELIVER
    "NCT02884206",  # PERSPECTIVE
    "NCT02861534",  # VICTORIA (already in v0.1)
    "NCT03057977",  # EMPEROR-Reduced (already in v0.1)
]


def extract_primary_block(page) -> tuple[str | None, str]:
    """Pull the Primary Outcome Measures block + page title."""
    title = page.title()
    text = page.evaluate(
        """() => {
            const t = document.body.innerText;
            const i = t.indexOf('Primary Outcome Measures');
            const j = t.indexOf('Secondary Outcome Measures', i);
            return i >= 0 ? t.slice(i, j > 0 ? j : i + 2000) : null;
        }"""
    )
    return text, title


def main() -> int:
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("ERROR: playwright not installed.")
        print("Run: pip install playwright && playwright install chromium")
        return 1

    rows = []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        for i, nct in enumerate(NCT_LIST, 1):
            url = f"https://clinicaltrials.gov/study/{nct}?tab=history&a=1"
            try:
                page.goto(url, wait_until="domcontentloaded", timeout=30_000)
                page.wait_for_selector("body", timeout=15_000)
                # Wait for client-side render
                page.wait_for_function(
                    "document.body.innerText.includes('Primary Outcome Measures') || document.title.includes('Error')",
                    timeout=20_000,
                )
                block, title = extract_primary_block(page)
                row = {
                    "nct_id": nct,
                    "version_title": title,
                    "primary_outcome_block": block,
                    "ok": block is not None,
                }
                print(f"[{i:2d}/{len(NCT_LIST)}] {nct} OK ({len(block or '')} chars)")
            except Exception as e:
                row = {"nct_id": nct, "error": str(e)}
                print(f"[{i:2d}/{len(NCT_LIST)}] {nct} FAIL {e}")
            rows.append(row)
            time.sleep(0.6)
        browser.close()

    with open(RAW_OUT, "w", encoding="utf-8") as f:
        json.dump({"extracted_at": "2026-04-30", "trials": rows}, f, indent=2, ensure_ascii=False)
    print()
    n_ok = sum(1 for r in rows if r.get("ok"))
    print(f"Wrote {RAW_OUT} ({n_ok}/{len(rows)} OK)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
