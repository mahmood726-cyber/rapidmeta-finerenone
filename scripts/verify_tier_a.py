"""Verify Tier A panels: subgroup, RR, meta-regression."""
from __future__ import annotations
import sys, io, time
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
from playwright.sync_api import sync_playwright

FILES = ['UC_BIOLOGICS_NMA_REVIEW.html', 'COLCHICINE_CVD_REVIEW.html', 'ADC_HER2_NMA_REVIEW.html']

PROBE = r"""() => {
    var ids = ['subgroup-interaction-panel','rr-sensitivity-panel','meta-regression-panel'];
    var host = document.getElementById('stats-tab-host');
    function summ(el) {
        if (!el) return null;
        var inner = el.querySelector('div');
        return inner ? (inner.innerText || '').replace(/\s+/g, ' ').slice(0, 180) : null;
    }
    return ids.map(function(id) {
        var el = document.getElementById(id);
        return { id: id, present: !!el, in_tab: el && host ? el.parentNode === host : null, summary: summ(el) };
    });
}"""

def main():
    with sync_playwright() as p:
        b = p.chromium.launch(headless=True)
        page = b.new_page()
        for f in FILES:
            page.goto('http://127.0.0.1:8767/' + f, wait_until='load', timeout=20000)
            time.sleep(5)
            print(f)
            for x in page.evaluate(PROBE):
                mark = '+' if x['present'] else '-'
                print(f"  {mark} {x['id']}: {x['summary']}")
            print()
        b.close()

if __name__ == "__main__":
    main()
