"""Verify trial-integrity and bayesian-sensitivity panels render."""
from __future__ import annotations
import sys, io, time
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
from playwright.sync_api import sync_playwright

FILES = ['UC_BIOLOGICS_NMA_REVIEW.html', 'COLCHICINE_CVD_REVIEW.html', 'ADC_HER2_NMA_REVIEW.html']

PROBE = r"""() => {
    var ti = document.getElementById('trial-integrity-panel');
    var bs = document.getElementById('bayesian-sensitivity-panel');
    var host = document.getElementById('stats-tab-host');
    function summ(el) {
        if (!el) return null;
        var inner = el.querySelector('div');
        return inner ? (inner.innerText || '').replace(/\s+/g, ' ').slice(0, 200) : null;
    }
    return {
        trial_integrity: !!ti,
        ti_in_tab: ti ? ti.parentNode === host : null,
        ti_summary: summ(ti),
        bayesian: !!bs,
        bs_in_tab: bs ? bs.parentNode === host : null,
        bs_summary: summ(bs),
        host_panel_count: host ? host.children.length : 0,
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
