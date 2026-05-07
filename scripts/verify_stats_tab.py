"""Verify the new Statistics tab is wired correctly."""
from __future__ import annotations
import sys, io, time
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
from playwright.sync_api import sync_playwright

FILES = ['UC_BIOLOGICS_NMA_REVIEW.html', 'COLCHICINE_CVD_REVIEW.html']

PROBE = r"""() => {
    var btn = document.getElementById('btn-tab-statistics');
    var sec = document.getElementById('tab-statistics');
    var host = document.getElementById('stats-tab-host');
    var suite = document.getElementById('advanced-stats-suite');
    var panelIds = ['r-validation-badge','nnt-panel','leave-one-out-panel','grade-sof-panel','cumulative-ma-panel','baujat-plot-panel','tsa-panel','nma-league-table-panel','nma-forest-all-treatments-panel'];
    var inHost = [];
    var stranded = [];
    panelIds.forEach(function(id) {
        var el = document.getElementById(id);
        if (!el) return;
        if (host && el.parentNode === host) inHost.push(id);
        else stranded.push(id);
    });
    var navBtns = Array.from(document.querySelectorAll('button[onclick*=\"switchTab\"]')).map(function(b) {
        return (b.textContent || '').trim().slice(0, 30);
    });
    return {
        button_present: !!btn,
        button_text: btn ? btn.textContent.trim() : null,
        section_present: !!sec,
        section_hidden_initially: sec ? sec.classList.contains('hidden') : null,
        host_present: !!host,
        panels_in_host: inHost,
        panels_stranded: stranded,
        legacy_suite_hidden: suite ? suite.style.display === 'none' : 'no_suite',
        nav_buttons: navBtns,
    };
}"""

CLICK_AND_VERIFY = r"""() => {
    if (typeof window.RapidMeta?.switchTab !== 'function') return { error: 'no switchTab' };
    window.RapidMeta.switchTab('statistics');
    var sec = document.getElementById('tab-statistics');
    return {
        section_visible: sec ? !sec.classList.contains('hidden') : null,
        section_height: sec ? sec.offsetHeight : 0,
        first_panel_visible: !!document.getElementById('r-validation-badge')?.offsetHeight,
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
            probe = page.evaluate(PROBE)
            for k, v in probe.items():
                print(f'  {k}: {v}')
            click = page.evaluate(CLICK_AND_VERIFY)
            print('  -- clicked Statistics tab --')
            for k, v in click.items():
                print(f'  {k}: {v}')
            print()
        b.close()

if __name__ == "__main__":
    main()
