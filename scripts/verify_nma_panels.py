"""Spot-check that NMA-only panels render on a sample of NMA review files."""
from __future__ import annotations
import sys, io, time
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
from playwright.sync_api import sync_playwright

NMAS = ['UC_BIOLOGICS_NMA_REVIEW.html', 'ADC_HER2_NMA_REVIEW.html', 'BTKI_CLL_NMA_REVIEW.html']

SCRIPT = r"""() => {
    var all = ['nnt-panel','leave-one-out-panel','grade-sof-panel','cumulative-ma-panel','baujat-plot-panel','tsa-panel','nma-league-table-panel','nma-forest-all-treatments-panel'];
    return all.map(function(id) {
        var el = document.getElementById(id);
        var text = '';
        if (el) {
            var inner = el.querySelector('div');
            text = inner ? inner.innerText : '';
            text = text.split(/\s+/).join(' ').slice(0, 100);
        }
        return { id: id, present: !!el, summary: text };
    });
}"""

def main():
    with sync_playwright() as p:
        b = p.chromium.launch(headless=True)
        page = b.new_page()
        for f in NMAS:
            page.goto('http://127.0.0.1:8767/' + f, wait_until='load', timeout=20000)
            time.sleep(3)
            out = page.evaluate(SCRIPT)
            print(f)
            for x in out:
                mark = '+' if x['present'] else '-'
                print(f"  {mark} {x['id']}: {x['summary'] or 'absent'}")
            print()
        b.close()

if __name__ == "__main__":
    main()
