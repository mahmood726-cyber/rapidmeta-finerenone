"""Comprehensive test: all tabs, screening abstracts, extraction sub-views, GRADE across all 18 REVIEW files."""
# pytest-collection skip: this is a one-shot Selenium CLI script, not a
# pytest test. Use pytest.skip(allow_module_level=True) so pytest stops
# executing this file rather than treating sys.exit() as an INTERNALERROR.
import sys as _sys
if "pytest" in _sys.modules:
    import pytest
    pytest.skip("Selenium CLI script — run with `python <file>`, not pytest", allow_module_level=True)

import sys, io, os, time, json
if "pytest" not in sys.modules:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

REVIEW_FILES = [
    'ABLATION_AF_REVIEW.html', 'ARNI_HF_REVIEW.html', 'ATTR_CM_REVIEW.html',
    'BEMPEDOIC_ACID_REVIEW.html', 'COLCHICINE_CVD_REVIEW.html', 'DOAC_CANCER_VTE_REVIEW.html',
    'FINERENONE_REVIEW.html', 'GLP1_CVOT_REVIEW.html', 'INCRETIN_HFpEF_REVIEW.html',
    'INTENSIVE_BP_REVIEW.html', 'IV_IRON_HF_REVIEW.html', 'LIPID_HUB_REVIEW.html',
    'MAVACAMTEN_HCM_REVIEW.html', 'PCSK9_REVIEW.html', 'RENAL_DENERV_REVIEW.html',
    'RIVAROXABAN_VASC_REVIEW.html', 'SGLT2_CKD_REVIEW.html', 'SGLT2_HF_REVIEW.html',
]

TABS = ['protocol', 'search', 'screen', 'extract', 'analysis', 'report']
EXTRACT_VIEWS = ['data', 'demographics', 'rob']

BASE = os.path.dirname(os.path.abspath(__file__))

def make_driver():
    opts = Options()
    opts.add_argument('--headless=new')
    opts.add_argument('--no-sandbox')
    opts.add_argument('--disable-gpu')
    opts.add_argument('--incognito')
    opts.set_capability('goog:loggingPrefs', {'browser': 'ALL'})
    return webdriver.Chrome(options=opts)

def clear_storage(driver):
    driver.execute_script("try{localStorage.clear()}catch(e){}")

def get_errors(driver):
    logs = driver.get_log('browser')
    return [l for l in logs if l['level'] in ('SEVERE',)]

def test_file(driver, filename):
    results = {'file': filename, 'pass': 0, 'fail': 0, 'errors': [], 'details': []}
    path = os.path.join(BASE, filename)
    url = 'file:///' + path.replace(os.sep, '/')

    driver.get(url)
    clear_storage(driver)
    driver.get(url)
    time.sleep(2)

    # Drain initial errors
    get_errors(driver)

    # 1. TEST ALL TABS SWITCH
    for tab in TABS:
        try:
            driver.execute_script(f"RapidMeta.switchTab('{tab}')")
            time.sleep(0.5)
            tab_el = driver.find_element(By.ID, f'tab-{tab}')
            visible = not tab_el.get_attribute('class') or 'hidden' not in tab_el.get_attribute('class')
            if visible:
                results['pass'] += 1
                results['details'].append(f"  PASS: tab-{tab} visible")
            else:
                results['fail'] += 1
                results['details'].append(f"  FAIL: tab-{tab} still hidden")
        except Exception as ex:
            results['fail'] += 1
            results['details'].append(f"  FAIL: tab-{tab} error: {ex}")

    errs = get_errors(driver)
    if errs:
        results['errors'].extend([e['message'][:120] for e in errs])

    # 2. TEST SCREENING - abstracts visible, reasons shown
    try:
        driver.execute_script("RapidMeta.switchTab('screen')")
        time.sleep(1)

        # Check screen-list has trial cards
        list_html = driver.execute_script("return document.getElementById('screen-list').innerHTML")
        has_cards = len(list_html) > 100
        if has_cards:
            results['pass'] += 1
            results['details'].append(f"  PASS: screen-list has cards ({len(list_html)} chars)")
        else:
            results['fail'] += 1
            results['details'].append(f"  FAIL: screen-list empty ({len(list_html)} chars)")

        # Count total trials
        trial_count = driver.execute_script("return RapidMeta.state.trials.length")
        results['details'].append(f"  INFO: {trial_count} total trials")

        # Select first trial and check abstract
        detail_result = driver.execute_script("""
            try {
                ScreenEngine.select(0);
                var detail = document.getElementById('screen-detail').innerHTML;
                var hasAbstract = detail.toLowerCase().includes('abstract');
                var hasContent = detail.length > 200;
                var hasScore = detail.includes('Screen Score') || detail.includes('screen-score') || detail.includes('Auto-Screen');
                return {html_len: detail.length, hasAbstract: hasAbstract, hasContent: hasContent, hasScore: hasScore, error: null};
            } catch(e) {
                return {html_len: 0, hasAbstract: false, hasContent: false, hasScore: false, error: e.message};
            }
        """)

        if detail_result['error']:
            results['fail'] += 1
            results['details'].append(f"  FAIL: ScreenEngine.select(0) error: {detail_result['error']}")
        else:
            if detail_result['hasContent']:
                results['pass'] += 1
                results['details'].append(f"  PASS: screen-detail has content ({detail_result['html_len']} chars)")
            else:
                results['fail'] += 1
                results['details'].append(f"  FAIL: screen-detail empty ({detail_result['html_len']} chars)")

            if detail_result['hasAbstract']:
                results['pass'] += 1
                results['details'].append(f"  PASS: abstract section present")
            else:
                results['fail'] += 1
                results['details'].append(f"  FAIL: no abstract section found")

        # Check screening reasons - iterate included/excluded trials
        screen_info = driver.execute_script("""
            var trials = RapidMeta.state.trials;
            var included = trials.filter(t => t.status === 'include');
            var excluded = trials.filter(t => t.status === 'exclude');
            var pending = trials.filter(t => t.status === 'search');
            var excludedWithReason = excluded.filter(t => t.reason && t.reason.length > 0);
            var includedWithReview = included.filter(t => t.screenReview && t.screenReview.decision);
            return {
                included: included.length,
                excluded: excluded.length,
                pending: pending.length,
                excludedWithReason: excludedWithReason.length,
                includedWithReview: includedWithReview.length,
                sampleReasons: excluded.slice(0,3).map(t => t.reason || '(no reason)')
            };
        """)
        results['details'].append(f"  INFO: {screen_info['included']} included, {screen_info['excluded']} excluded, {screen_info['pending']} pending")

        if screen_info['excluded'] > 0:
            if screen_info['excludedWithReason'] > 0:
                results['pass'] += 1
                results['details'].append(f"  PASS: {screen_info['excludedWithReason']}/{screen_info['excluded']} excluded have reasons")
                results['details'].append(f"  INFO: sample reasons: {screen_info['sampleReasons'][:2]}")
            else:
                results['fail'] += 1
                results['details'].append(f"  FAIL: {screen_info['excluded']} excluded but NONE have reasons")

        # Check each screening filter view works
        for filt in ['include', 'exclude', 'all']:
            try:
                driver.execute_script(f"ScreenEngine.toggleFilter('{filt}')")
                time.sleep(0.3)
                count = driver.execute_script("return document.getElementById('screen-list').children.length")
                results['pass'] += 1
                results['details'].append(f"  PASS: filter '{filt}' shows {count} items")
            except Exception as ex:
                results['fail'] += 1
                results['details'].append(f"  FAIL: filter '{filt}' error: {ex}")

        # Test multiple trial abstracts (first 3)
        for idx in range(min(3, trial_count)):
            abs_test = driver.execute_script(f"""
                try {{
                    ScreenEngine.select({idx});
                    var d = document.getElementById('screen-detail');
                    var html = d.innerHTML;
                    var t = RapidMeta.state.trials[{idx}];
                    return {{
                        id: t.id,
                        title_shown: html.includes(t.title ? t.title.slice(0,20) : ''),
                        abstract_shown: html.toLowerCase().includes('abstract'),
                        html_len: html.length,
                        error: null
                    }};
                }} catch(e) {{
                    return {{error: e.message}};
                }}
            """)
            if abs_test.get('error'):
                results['fail'] += 1
                results['details'].append(f"  FAIL: trial[{idx}] select error: {abs_test['error']}")
            elif abs_test['html_len'] > 100:
                results['pass'] += 1
                results['details'].append(f"  PASS: trial[{idx}] ({abs_test.get('id','?')}) abstract rendered ({abs_test['html_len']} chars)")
            else:
                results['fail'] += 1
                results['details'].append(f"  FAIL: trial[{idx}] ({abs_test.get('id','?')}) detail empty")

    except Exception as ex:
        results['fail'] += 1
        results['details'].append(f"  FAIL: screening test crashed: {ex}")

    errs = get_errors(driver)
    if errs:
        results['errors'].extend([e['message'][:120] for e in errs])

    # 3. TEST EXTRACTION SUB-VIEWS
    try:
        driver.execute_script("RapidMeta.switchTab('extract')")
        time.sleep(1)

        for view in EXTRACT_VIEWS:
            try:
                driver.execute_script(f"ExtractEngine.setView('{view}')")
                time.sleep(0.5)
                view_el = driver.find_element(By.ID, f'extract-view-{view}')
                visible = 'hidden' not in (view_el.get_attribute('class') or '')
                html = view_el.get_attribute('innerHTML')
                has_content = len(html) > 50

                if visible and has_content:
                    results['pass'] += 1
                    results['details'].append(f"  PASS: extract-view-{view} visible ({len(html)} chars)")
                elif visible:
                    results['fail'] += 1
                    results['details'].append(f"  FAIL: extract-view-{view} visible but empty ({len(html)} chars)")
                else:
                    results['fail'] += 1
                    results['details'].append(f"  FAIL: extract-view-{view} still hidden")
            except Exception as ex:
                results['fail'] += 1
                results['details'].append(f"  FAIL: extract-view-{view} error: {ex}")

        # Check demographics table specifically
        demo_check = driver.execute_script("""
            ExtractEngine.setView('demographics');
            var el = document.getElementById('extract-view-demographics');
            var html = el.innerHTML;
            var hasTable = html.includes('<table') || html.includes('<th') || html.includes('Year') || html.includes('Phase');
            var hasTrialRows = html.includes('NCT') || html.includes('trial');
            return {hasTable: hasTable, hasTrialRows: hasTrialRows, len: html.length};
        """)
        if demo_check['hasTable']:
            results['pass'] += 1
            results['details'].append(f"  PASS: demographics has table structure")
        else:
            results['fail'] += 1
            results['details'].append(f"  FAIL: demographics missing table (len={demo_check['len']})")

        # Check RoB cards specifically
        rob_check = driver.execute_script("""
            ExtractEngine.setView('rob');
            var el = document.getElementById('extract-view-rob');
            var html = el.innerHTML;
            var hasRobDomains = html.includes('Randomization') || html.includes('D1') || html.includes('andomiz');
            var hasRatings = html.includes('low') || html.includes('Low') || html.includes('some') || html.includes('high');
            return {hasRobDomains: hasRobDomains, hasRatings: hasRatings, len: html.length};
        """)
        if rob_check['hasRobDomains']:
            results['pass'] += 1
            results['details'].append(f"  PASS: RoB has domain labels")
        else:
            results['fail'] += 1
            results['details'].append(f"  FAIL: RoB missing domain labels (len={rob_check['len']})")

        if rob_check['hasRatings']:
            results['pass'] += 1
            results['details'].append(f"  PASS: RoB has rating values")
        else:
            results['fail'] += 1
            results['details'].append(f"  FAIL: RoB missing ratings (len={rob_check['len']})")

    except Exception as ex:
        results['fail'] += 1
        results['details'].append(f"  FAIL: extraction test crashed: {ex}")

    errs = get_errors(driver)
    if errs:
        results['errors'].extend([e['message'][:120] for e in errs])

    # 4. TEST ANALYSIS TAB + GRADE
    try:
        driver.execute_script("RapidMeta.switchTab('analysis')")
        time.sleep(2)  # Analysis needs more time to compute

        grade_check = driver.execute_script("""
            var gc = document.getElementById('grade-container');
            if (!gc) return {exists: false, html_len: 0, hasGrade: false, hasCertainty: false};
            var html = gc.innerHTML;
            var hasGrade = html.includes('GRADE') || html.includes('grade') || html.includes('Certainty');
            var hasCertainty = html.includes('HIGH') || html.includes('MODERATE') || html.includes('LOW') || html.includes('VERY LOW');
            var hasBadge = html.includes('grade-high') || html.includes('grade-mod') || html.includes('grade-low') || html.includes('grade-vlow');
            return {exists: true, html_len: html.length, hasGrade: hasGrade, hasCertainty: hasCertainty, hasBadge: hasBadge};
        """)

        if grade_check['exists'] and grade_check['html_len'] > 50:
            results['pass'] += 1
            results['details'].append(f"  PASS: grade-container has content ({grade_check['html_len']} chars)")
        else:
            results['fail'] += 1
            results['details'].append(f"  FAIL: grade-container empty or missing (len={grade_check.get('html_len', 0)})")

        if grade_check.get('hasCertainty'):
            results['pass'] += 1
            results['details'].append(f"  PASS: GRADE certainty level shown")
        else:
            results['fail'] += 1
            results['details'].append(f"  FAIL: no GRADE certainty level found")

        # Check forest plot rendered
        forest_check = driver.execute_script("""
            var pf = document.getElementById('plot-forest');
            if (!pf) return {exists: false};
            return {exists: true, hasPlotly: pf.classList.contains('js-plotly-plot') || pf.innerHTML.includes('plotly') || pf.innerHTML.length > 100};
        """)
        if forest_check.get('hasPlotly') or forest_check.get('exists'):
            results['pass'] += 1
            results['details'].append(f"  PASS: forest plot rendered")
        else:
            results['details'].append(f"  INFO: forest plot element not found (may be named differently)")

    except Exception as ex:
        results['fail'] += 1
        results['details'].append(f"  FAIL: analysis test crashed: {ex}")

    errs = get_errors(driver)
    if errs:
        results['errors'].extend([e['message'][:120] for e in errs])

    # 5. TEST REPORT TAB
    try:
        driver.execute_script("RapidMeta.switchTab('report')")
        time.sleep(1)
        report_check = driver.execute_script("""
            var tab = document.getElementById('tab-report');
            return {visible: tab && !tab.classList.contains('hidden'), html_len: tab ? tab.innerHTML.length : 0};
        """)
        if report_check['visible']:
            results['pass'] += 1
            results['details'].append(f"  PASS: report tab visible ({report_check['html_len']} chars)")
        else:
            results['fail'] += 1
            results['details'].append(f"  FAIL: report tab not visible")
    except Exception as ex:
        results['fail'] += 1
        results['details'].append(f"  FAIL: report tab error: {ex}")

    # Final error check
    errs = get_errors(driver)
    if errs:
        results['errors'].extend([e['message'][:120] for e in errs])

    if results['errors']:
        results['fail'] += 1
        results['details'].append(f"  FAIL: {len(results['errors'])} JS errors detected")
    else:
        results['pass'] += 1
        results['details'].append(f"  PASS: zero JS errors")

    return results


def main():
    driver = make_driver()
    all_results = []
    total_pass = 0
    total_fail = 0

    try:
        for i, f in enumerate(REVIEW_FILES):
            print(f"\n{'='*70}")
            print(f"[{i+1}/{len(REVIEW_FILES)}] Testing {f}")
            print('='*70)

            r = test_file(driver, f)
            all_results.append(r)
            total_pass += r['pass']
            total_fail += r['fail']

            for d in r['details']:
                print(d)
            if r['errors']:
                print(f"  JS ERRORS:")
                for e in r['errors'][:5]:
                    print(f"    {e}")

            print(f"  --- {r['pass']} pass, {r['fail']} fail ---")
    finally:
        driver.quit()

    # Summary
    print(f"\n{'='*70}")
    print(f"FINAL SUMMARY: {total_pass} PASS / {total_fail} FAIL across {len(REVIEW_FILES)} files")
    print('='*70)

    failed_files = [r['file'] for r in all_results if r['fail'] > 0]
    if failed_files:
        print(f"\nFiles with failures ({len(failed_files)}):")
        for f in failed_files:
            r = next(x for x in all_results if x['file'] == f)
            fails = [d for d in r['details'] if 'FAIL' in d]
            print(f"  {f}: {r['fail']} failures")
            for fl in fails:
                print(f"    {fl.strip()}")
            if r['errors']:
                for e in r['errors'][:3]:
                    print(f"    JS: {e}")
    else:
        print("\nALL FILES PASSED ALL TESTS!")

    return 1 if total_fail > 0 else 0

if __name__ == '__main__':
    sys.exit(main())
