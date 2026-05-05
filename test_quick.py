"""Quick test: all tabs, extraction views, GRADE — with driver restart per file."""
# pytest-collection skip: this is a one-shot Selenium CLI script, not a
# pytest test. Use pytest.skip(allow_module_level=True) so pytest stops
# executing this file rather than treating sys.exit() as an INTERNALERROR.
import sys as _sys
if "pytest" in _sys.modules:
    import pytest
    pytest.skip("Selenium CLI script — run with `python <file>`, not pytest", allow_module_level=True)

import sys, io, os, time
if "pytest" not in sys.modules:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

from selenium import webdriver
from selenium.webdriver.chrome.options import Options

REVIEW_FILES = [
    'ABLATION_AF_REVIEW.html', 'ARNI_HF_REVIEW.html', 'ATTR_CM_REVIEW.html',
    'BEMPEDOIC_ACID_REVIEW.html', 'COLCHICINE_CVD_REVIEW.html', 'DOAC_CANCER_VTE_REVIEW.html',
    'FINERENONE_REVIEW.html', 'GLP1_CVOT_REVIEW.html', 'INCRETIN_HFpEF_REVIEW.html',
    'INTENSIVE_BP_REVIEW.html', 'IV_IRON_HF_REVIEW.html', 'LIPID_HUB_REVIEW.html',
    'MAVACAMTEN_HCM_REVIEW.html', 'PCSK9_REVIEW.html', 'RENAL_DENERV_REVIEW.html',
    'RIVAROXABAN_VASC_REVIEW.html', 'SGLT2_CKD_REVIEW.html', 'SGLT2_HF_REVIEW.html',
]
BASE = os.path.dirname(os.path.abspath(__file__))

def make_driver():
    opts = Options()
    opts.add_argument('--headless=new')
    opts.add_argument('--no-sandbox')
    opts.add_argument('--disable-gpu')
    opts.add_argument('--incognito')
    opts.set_capability('goog:loggingPrefs', {'browser': 'ALL'})
    return webdriver.Chrome(options=opts)

def test_file(filename):
    """Test one file with its own driver instance."""
    results = {'file': filename, 'pass': 0, 'fail': 0, 'details': []}
    driver = make_driver()
    try:
        path = os.path.join(BASE, filename)
        url = 'file:///' + path.replace(os.sep, '/')
        driver.get(url)
        driver.execute_script("try{localStorage.clear()}catch(e){}")
        driver.get(url)
        time.sleep(3)
        driver.get_log('browser')  # drain

        # 1. Tab sweep — all 6 tabs must work
        for tab in ['protocol', 'search', 'screen', 'extract', 'analysis', 'report']:
            try:
                driver.execute_script(f"RapidMeta.switchTab('{tab}')")
                time.sleep(0.5 if tab != 'analysis' else 2)
                el = driver.find_element('id', f'tab-{tab}')
                if 'hidden' not in (el.get_attribute('class') or ''):
                    results['pass'] += 1
                else:
                    results['fail'] += 1; results['details'].append(f'tab-{tab} hidden')
            except Exception as ex:
                results['fail'] += 1; results['details'].append(f'tab-{tab}: {str(ex)[:60]}')

        errors = [l for l in driver.get_log('browser') if l['level'] == 'SEVERE']
        if errors:
            results['fail'] += 1; results['details'].append(f'{len(errors)} JS errors after tab sweep')
        else:
            results['pass'] += 1

        # 2. Screening: abstracts + reasons
        driver.execute_script("RapidMeta.switchTab('screen')")
        time.sleep(1)
        screen_check = driver.execute_script("""
            try {
                ScreenEngine.select(0);
                var d = document.getElementById('screen-detail').innerHTML;
                var hasAbstract = d.toLowerCase().includes('abstract');
                var trials = RapidMeta.state.trials;
                var excluded = trials.filter(t => t.status === 'exclude');
                var withReason = excluded.filter(t => t.reason && t.reason.length > 0);
                return {
                    detailLen: d.length,
                    hasAbstract: hasAbstract,
                    excludedCount: excluded.length,
                    withReasonCount: withReason.length,
                    error: null
                };
            } catch(e) { return {error: e.message}; }
        """)
        if screen_check.get('error'):
            results['fail'] += 1; results['details'].append(f"screen: {screen_check['error'][:60]}")
        else:
            if screen_check['detailLen'] > 200 and screen_check['hasAbstract']:
                results['pass'] += 1
            else:
                results['fail'] += 1; results['details'].append(f"screen: no abstract ({screen_check['detailLen']} chars)")

            if screen_check['excludedCount'] > 0:
                if screen_check['withReasonCount'] > 0:
                    results['pass'] += 1
                else:
                    results['fail'] += 1; results['details'].append(f"excluded have no reasons")
            else:
                results['pass'] += 1  # no excluded = OK

        # 3. Extraction: data, demographics, rob
        driver.execute_script("RapidMeta.switchTab('extract')")
        time.sleep(1)
        for view in ['data', 'demographics', 'rob']:
            check = driver.execute_script(f"""
                try {{
                    ExtractEngine.setView('{view}');
                    var el = document.getElementById('extract-view-{view}');
                    var html = el ? el.innerHTML : '';
                    return {{len: html.length, error: null}};
                }} catch(e) {{ return {{len: 0, error: e.message}}; }}
            """)
            time.sleep(0.3)
            if check.get('error'):
                results['fail'] += 1; results['details'].append(f"extract-{view}: {check['error'][:60]}")
            elif check['len'] > 100:
                results['pass'] += 1
            else:
                results['fail'] += 1; results['details'].append(f"extract-{view} empty ({check['len']})")

        # RoB domain check
        rob_check = driver.execute_script("""
            var el = document.getElementById('extract-view-rob');
            if (!el) return {ok: false};
            var h = el.innerHTML;
            return {ok: h.includes('Randomization') || h.includes('D1') || h.includes('low') || h.includes('Low')};
        """)
        if rob_check.get('ok'):
            results['pass'] += 1
        else:
            results['fail'] += 1; results['details'].append('RoB missing domain labels/ratings')

        # Demographics check
        demo_check = driver.execute_script("""
            ExtractEngine.setView('demographics');
            var el = document.getElementById('extract-view-demographics');
            if (!el) return {ok: false};
            var h = el.innerHTML;
            return {ok: h.includes('<table') || h.includes('Year') || h.includes('Phase') || h.includes('N =')};
        """)
        if demo_check.get('ok'):
            results['pass'] += 1
        else:
            results['fail'] += 1; results['details'].append('demographics missing table')

        # 4. GRADE
        driver.execute_script("RapidMeta.switchTab('analysis')")
        time.sleep(4)
        grade_check = driver.execute_script("""
            var gc = document.getElementById('grade-container');
            if (!gc) return {len: 0, hasCert: false};
            var h = gc.innerHTML;
            return {len: h.length, hasCert: h.includes('HIGH') || h.includes('MODERATE') || h.includes('LOW') || h.includes('VERY LOW')};
        """)
        if grade_check['len'] > 50 and grade_check['hasCert']:
            results['pass'] += 1
        else:
            results['fail'] += 1; results['details'].append(f"GRADE empty/no certainty (len={grade_check['len']})")

        # Final error check
        errors2 = [l for l in driver.get_log('browser') if l['level'] == 'SEVERE']
        if errors2:
            results['fail'] += 1; results['details'].append(f'{len(errors2)} JS errors at end')
        else:
            results['pass'] += 1

    except Exception as ex:
        results['fail'] += 1; results['details'].append(f'CRASH: {str(ex)[:80]}')
    finally:
        try: driver.quit()
        except: pass
    return results

def main():
    total_pass = 0
    total_fail = 0
    all_results = []

    for i, f in enumerate(REVIEW_FILES):
        r = test_file(f)
        all_results.append(r)
        total_pass += r['pass']
        total_fail += r['fail']
        status = 'PASS' if r['fail'] == 0 else 'FAIL'
        details = '; '.join(r['details'][:3]) if r['details'] else ''
        print(f"[{i+1:2d}/18] {status} {r['pass']:2d}/{r['pass']+r['fail']:2d} {f:<35s} {details}")

    print(f"\nFINAL: {total_pass} PASS / {total_fail} FAIL across {len(REVIEW_FILES)} files")
    failed = [r for r in all_results if r['fail'] > 0]
    if failed:
        print(f"\n{len(failed)} files with failures:")
        for r in failed:
            print(f"  {r['file']}: {', '.join(r['details'])}")
    else:
        print("\nALL 18 FILES PASSED!")
    return 1 if total_fail > 0 else 0

if __name__ == '__main__':
    sys.exit(main())
