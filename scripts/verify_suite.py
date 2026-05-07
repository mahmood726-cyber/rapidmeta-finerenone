"""Verify the advanced-stats-suite consolidates all panels."""
from __future__ import annotations
import sys, io, time
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
from playwright.sync_api import sync_playwright

FILES = [
    'UC_BIOLOGICS_NMA_REVIEW.html',
    'COLCHICINE_CVD_REVIEW.html',
    'BTKI_CLL_NMA_REVIEW.html',
]

SCRIPT = r"""() => {
    var suite = document.getElementById('advanced-stats-suite');
    var body = document.getElementById('advanced-stats-suite-body');
    var head = document.getElementById('advanced-stats-suite-head');
    var stranded = [];
    var children = [];
    if (body) {
        for (var i = 0; i < body.children.length; i++) children.push(body.children[i].id);
    }
    var ids = ['r-validation-badge','nnt-panel','leave-one-out-panel','grade-sof-panel','cumulative-ma-panel','baujat-plot-panel','tsa-panel','nma-league-table-panel','nma-forest-all-treatments-panel'];
    ids.forEach(function(id) {
        var el = document.getElementById(id);
        if (el && el.parentNode !== body) stranded.push(id);
    });
    return {
        suite_present: !!suite,
        suite_height_px: suite ? suite.offsetHeight : 0,
        body_visible: body ? body.style.display !== 'none' : null,
        n_in_body: children.length,
        in_body: children,
        stranded_outside_suite: stranded,
        head_summary: head ? (head.innerText || '').replace(/\s+/g, ' ').slice(0, 200) : null,
    };
}"""

def main():
    with sync_playwright() as p:
        b = p.chromium.launch(headless=True)
        page = b.new_page()
        for f in FILES:
            page.goto('http://127.0.0.1:8767/' + f, wait_until='load', timeout=20000)
            time.sleep(4)
            out = page.evaluate(SCRIPT)
            print(f)
            for k, v in out.items():
                print(f'  {k}: {v}')
            print()
        b.close()

if __name__ == "__main__":
    main()
