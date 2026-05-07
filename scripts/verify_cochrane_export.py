"""Verify the RevMan-compatible PDF export button is wired correctly."""
from __future__ import annotations
import sys, io, time
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
from playwright.sync_api import sync_playwright

FILES = ['UC_BIOLOGICS_NMA_REVIEW.html', 'COLCHICINE_CVD_REVIEW.html']

PROBE = r"""() => {
    var existing = document.querySelector('button[onclick=\"downloadPDFReport()\"]');
    var newBtn = document.getElementById('cochrane-export-btn');
    return {
        existing_pdf_btn: !!existing,
        existing_pdf_text: existing ? existing.textContent.trim().slice(0, 60) : null,
        cochrane_btn: !!newBtn,
        cochrane_btn_text: newBtn ? newBtn.textContent.trim() : null,
        cochrane_api: typeof window.CochraneExport,
        sibling_check: existing && newBtn ? (existing.nextSibling === newBtn || existing.nextElementSibling === newBtn) : null,
    };
}"""

CLICK_PROBE = r"""() => {
    if (typeof window.CochraneExport?.exportPDF !== 'function') return { error: 'no api' };
    // Don't actually print — just verify we can build the header/footer + CSS
    var stylesBefore = document.querySelectorAll('style#cochrane-export-print-style').length;
    // Manually invoke pre-print preparation
    var headerExists = !!document.getElementById('cochrane-export-header');
    var statsTab = document.getElementById('tab-statistics');
    var statsHasContent = statsTab ? statsTab.querySelectorAll('div[id$=\"-panel\"]').length : 0;
    return {
        styles_before: stylesBefore,
        header_built_yet: headerExists,
        stats_tab_panels: statsHasContent,
    };
}"""

def main():
    with sync_playwright() as p:
        b = p.chromium.launch(headless=True)
        page = b.new_page()
        for f in FILES:
            page.goto('http://127.0.0.1:8767/' + f, wait_until='load', timeout=20000)
            time.sleep(4)
            print(f)
            for k, v in page.evaluate(PROBE).items():
                print(f'  {k}: {v}')
            for k, v in page.evaluate(CLICK_PROBE).items():
                print(f'  {k}: {v}')
            print()
        b.close()

if __name__ == "__main__":
    main()
