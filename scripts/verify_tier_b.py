"""Verify Tier B panels: funnel-diagnostics, influence-diagnostics."""
from __future__ import annotations
import sys, io, time
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
from playwright.sync_api import sync_playwright

FILES = ['UC_BIOLOGICS_NMA_REVIEW.html', 'COLCHICINE_CVD_REVIEW.html', 'ADC_HER2_NMA_REVIEW.html']

PROBE = r"""() => {
    var ids = ['funnel-diagnostics-panel','influence-diagnostics-panel'];
    var host = document.getElementById('stats-tab-host');
    function summ(el) {
        if (!el) return null;
        var inner = el.querySelector('div');
        return inner ? (inner.innerText || '').replace(/\s+/g, ' ').slice(0, 200) : null;
    }
    var allInTab = host ? host.children.length : 0;
    return {
        total_panels_in_tab: allInTab,
        funnel: ids[0] ? !!document.getElementById(ids[0]) : false,
        funnel_summary: summ(document.getElementById(ids[0])),
        influence: !!document.getElementById(ids[1]),
        influence_summary: summ(document.getElementById(ids[1])),
    };
}"""

def main():
    with sync_playwright() as p:
        b = p.chromium.launch(headless=True)
        page = b.new_page()
        for f in FILES:
            page.goto('http://127.0.0.1:8767/' + f, wait_until='load', timeout=20000)
            time.sleep(5)
            print(f)
            for k, v in page.evaluate(PROBE).items():
                print(f'  {k}: {v}')
            print()
        b.close()

if __name__ == "__main__":
    main()
