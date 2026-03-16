"""
validate_all_apps.py — Compare RapidMeta app synthesis results to published meta-analyses
Runs each app one by one, extracts pooled estimates, compares to gold standard.
"""
import sys, io, os, time, json, traceback
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

from selenium import webdriver
from selenium.webdriver.chrome.options import Options

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Published meta-analysis gold standards
GOLD_STANDARDS = {
    'FINERENONE_REVIEW.html': {
        'MACE': { 'hr': 0.86, 'lo': 0.78, 'hi': 0.95, 'source': 'FIDELITY pooled (Agarwal 2022)', 'k': 2 },
    },
    'BEMPEDOIC_ACID_REVIEW.html': {
        'MACE': { 'hr': 0.87, 'lo': 0.79, 'hi': 0.96, 'source': 'CLEAR Outcomes (Nissen 2023)', 'k': 1 },
    },
    'COLCHICINE_CVD_REVIEW.html': {
        'MACE': { 'hr': 0.75, 'lo': 0.61, 'hi': 0.91, 'source': 'COLCOT+LoDoCo2 pooled', 'k': 2 },
    },
    'GLP1_CVOT_REVIEW.html': {
        'MACE': { 'hr': 0.88, 'lo': 0.84, 'hi': 0.94, 'source': 'Sattar 2021 Lancet Diab Endocrinol', 'k': 8 },
    },
    'SGLT2_HF_REVIEW.html': {
        'MACE': { 'hr': 0.77, 'lo': 0.71, 'hi': 0.84, 'source': 'Vaduganathan 2022 Lancet', 'k': 2 },
    },
    'PCSK9_REVIEW.html': {
        'MACE': { 'hr': 0.85, 'lo': 0.79, 'hi': 0.92, 'source': 'FOURIER+ODYSSEY (Guedeney 2020)', 'k': 2 },
    },
    'INTENSIVE_BP_REVIEW.html': {
        'MACE': { 'hr': 0.83, 'lo': 0.72, 'hi': 0.95, 'source': 'SPRINT (Wright 2015)', 'k': 1 },
    },
    'INCRETIN_HFpEF_REVIEW.html': {
        'MACE': { 'hr': None, 'lo': None, 'hi': None, 'source': 'No published pooled HR (novel topic)', 'k': 0 },
    },
}


def get_driver():
    opts = Options()
    opts.add_argument('--headless=new')
    opts.add_argument('--no-sandbox')
    opts.add_argument('--disable-gpu')
    opts.add_argument('--disable-dev-shm-usage')
    opts.set_capability('goog:loggingPrefs', {'browser': 'ALL'})
    d = webdriver.Chrome(options=opts)
    d.set_page_load_timeout(30)
    return d


def extract_v12_results(driver):
    """Extract results from v12 template apps (FINERENONE, BEMPEDOIC, PCSK9, INTENSIVE_BP, LIPID_HUB)."""
    # Switch to analysis tab which triggers AnalysisEngine.run()
    driver.execute_script("""
        try {
            if (typeof RapidMeta !== 'undefined') {
                RapidMeta.switchTab('analysis');
            }
        } catch(e) { console.log('switchTab error:', e); }
    """)
    time.sleep(3)

    # Also try direct AnalysisEngine.run()
    driver.execute_script("""
        try {
            if (typeof AnalysisEngine !== 'undefined' && AnalysisEngine.run) {
                AnalysisEngine.run();
            }
        } catch(e) { console.log('AnalysisEngine.run error:', e); }
    """)
    time.sleep(2)

    return driver.execute_script("""
        try {
            if (typeof RapidMeta === 'undefined' || !RapidMeta.state) return { error: 'No RapidMeta' };
            var r = RapidMeta.state.results;
            if (!r) return { error: 'No results in state (after switchTab+run)' };
            // The pooled estimate is stored as 'or' (string), lci/uci also strings
            var pooled = parseFloat(r.or || r.pOR || r.pooledOR || 0);
            var lci = parseFloat(r.lci || 0);
            var uci = parseFloat(r.uci || 0);
            return {
                pooledOR: pooled > 0 ? pooled : null,
                lci: lci > 0 ? lci : null,
                uci: uci > 0 ? uci : null,
                I2: r.i2 != null ? parseFloat(r.i2) : null,
                k: r.k != null ? parseInt(r.k) : null,
                hksjLCI: r.hksjLCI != null ? parseFloat(r.hksjLCI) : null,
                hksjUCI: r.hksjUCI != null ? parseFloat(r.hksjUCI) : null
            };
        } catch(e) { return { error: e.message }; }
    """)


def extract_v1_results(driver, app_type):
    """Extract results from v1 template apps (COLCHICINE, SGLT2, GLP1, INCRETIN)."""
    # These apps have different synthesis entry points
    if app_type == 'colchicine':
        driver.execute_script("""
            try {
                if (typeof SynthesisEngine !== 'undefined') SynthesisEngine.run();
                else if (typeof UI !== 'undefined' && UI.runAnalysis) UI.runAnalysis();
            } catch(e) {}
        """)
    elif app_type == 'glp1':
        driver.execute_script("""
            try {
                if (typeof RapidMeta !== 'undefined') RapidMeta.runAnalysis();
            } catch(e) {}
        """)
    elif app_type == 'sglt2':
        driver.execute_script("""
            try {
                if (typeof SynthesisEngine !== 'undefined') SynthesisEngine.run();
                else if (typeof UI !== 'undefined' && UI.runAnalysis) UI.runAnalysis();
            } catch(e) {}
        """)
    elif app_type == 'incretin':
        driver.execute_script("""
            try {
                if (typeof UI !== 'undefined' && UI.runAnalysis) UI.runAnalysis();
            } catch(e) {}
        """)
    time.sleep(2)

    # Try multiple extraction patterns
    return driver.execute_script("""
        try {
            // Pattern 1: RapidMeta.state.results (GLP1, etc.)
            if (typeof RapidMeta !== 'undefined' && RapidMeta.state && RapidMeta.state.results) {
                var r = RapidMeta.state.results;
                return {
                    pooledOR: r.pOR || r.pooledOR || null,
                    pooledLogOR: r.pLogOR || null,
                    lci: r.lci || null,
                    uci: r.uci || null,
                    I2: r.I2 || null,
                    k: r.k || null,
                    effectMeasure: r.effectMeasure || null
                };
            }
            // Pattern 2: global synthesisResult
            if (typeof synthesisResult !== 'undefined' && synthesisResult) {
                return {
                    pooledOR: synthesisResult.pooledEffect || synthesisResult.pOR || null,
                    lci: synthesisResult.lci || null,
                    uci: synthesisResult.uci || null,
                    I2: synthesisResult.I2 || null,
                    k: synthesisResult.k || null
                };
            }
            // Pattern 3: AppState.results (LivingMeta)
            if (typeof AppState !== 'undefined' && AppState && AppState.results) {
                var r = AppState.results;
                var tb = r.trackB;
                if (tb && tb.primary) {
                    return {
                        pooledOR: Math.exp(tb.primary.estimate),
                        lci: Math.exp(tb.primary.ci[0]),
                        uci: Math.exp(tb.primary.ci[1]),
                        I2: tb.primary.I2 || null,
                        k: tb.k || null
                    };
                }
            }
            // Pattern 4: Project.state (ATTR_CM)
            if (typeof Project !== 'undefined' && Project.state) {
                return { pooledRR: Project.state.pooledRR || null };
            }
            return { error: 'No results pattern matched' };
        } catch(e) { return { error: e.message }; }
    """)


def validate_one_app(driver, filename, gold):
    """Validate a single app against gold standard."""
    filepath = os.path.join(BASE_DIR, filename)
    if not os.path.exists(filepath):
        return 'SKIP', 'File not found', None

    url = 'file:///' + filepath.replace(os.sep, '/')
    try:
        driver.get(url)
    except Exception as e:
        return 'ERROR', f'Failed to load: {e}', None
    time.sleep(5)

    # Check for JS errors
    try:
        logs = driver.get_log('browser')
        errors = [l for l in logs if l['level'] == 'SEVERE'
                  and 'favicon' not in l.get('message', '').lower()
                  and 'PubMed' not in l.get('message', '')
                  and 'CT.gov' not in l.get('message', '')]
        if errors:
            print(f'    JS errors: {len(errors)}')
            for e in errors[:2]:
                print(f'      {e["message"][:120]}')
    except:
        pass

    # All apps except ATTR_CM use the v12 RapidMeta pattern
    if 'ATTR_CM' in filename:
        result = extract_v1_results(driver, 'attr')
    else:
        result = extract_v12_results(driver)

    if not result or 'error' in result:
        return 'ERROR', str(result), None

    # Get pooled estimate
    app_hr = result.get('pooledOR') or result.get('pooledRR')
    app_lci = result.get('lci')
    app_uci = result.get('uci')
    app_k = result.get('k')

    if app_hr is None:
        return 'ERROR', f'No pooled estimate. Raw: {result}', result

    if gold['hr'] is None:
        return 'INFO', f'App HR={app_hr:.3f} (k={app_k}), no published benchmark', result

    # Compare
    pct_diff = abs(app_hr - gold['hr']) / gold['hr'] * 100
    within_ci = gold['lo'] <= app_hr <= gold['hi']

    detail = f"App={app_hr:.3f}"
    if app_lci and app_uci:
        detail += f" ({app_lci:.3f}-{app_uci:.3f})"
    detail += f", Gold={gold['hr']:.2f} ({gold['lo']:.2f}-{gold['hi']:.2f}), diff={pct_diff:.1f}%"

    if pct_diff < 5:
        return 'MATCH', detail, result
    elif pct_diff < 10:
        return 'CLOSE', detail, result
    elif within_ci:
        return 'WITHIN_CI', detail, result
    else:
        return 'MISMATCH', detail, result


def main():
    print('=' * 75)
    print('  RapidMeta Validation vs Published Meta-Analyses')
    print('  One app at a time, sequential testing')
    print('=' * 75)

    all_results = []

    for filename, outcomes in GOLD_STANDARDS.items():
        short = filename.replace('_REVIEW.html', '').replace('.html', '')
        print(f'\n{"=" * 60}')
        print(f'  {short}')
        print(f'{"=" * 60}')

        driver = get_driver()  # Fresh driver per app to avoid state leaks
        try:
            for outcome_name, gold in outcomes.items():
                print(f'  Outcome: {outcome_name}')
                print(f'  Gold: {gold["source"]}')
                if gold['hr']:
                    print(f'  Expected: HR {gold["hr"]:.2f} ({gold["lo"]:.2f}-{gold["hi"]:.2f})')

                try:
                    status, detail, raw = validate_one_app(driver, filename, gold)
                except Exception as e:
                    status, detail, raw = 'ERROR', str(e), None

                marker = {'MATCH': 'OK', 'CLOSE': '~OK', 'WITHIN_CI': 'CI',
                          'MISMATCH': '!!', 'ERROR': 'ERR', 'SKIP': '--', 'INFO': 'i'}.get(status, '??')
                print(f'  >>> [{marker}] {status}: {detail}')
                all_results.append((short, outcome_name, status, detail))
        finally:
            driver.quit()

    # Summary table
    print(f'\n{"=" * 75}')
    print('  VALIDATION SUMMARY')
    print(f'{"=" * 75}')
    for app, outcome, status, detail in all_results:
        marker = {'MATCH': '[OK]', 'CLOSE': '[~]', 'WITHIN_CI': '[CI]',
                  'MISMATCH': '[!!]', 'ERROR': '[ERR]', 'SKIP': '[--]', 'INFO': '[i]'}.get(status, '[??]')
        print(f'  {marker} {app:<30} {outcome:<10} {detail[:60]}')

    matches = sum(1 for _, _, s, _ in all_results if s in ('MATCH', 'CLOSE', 'WITHIN_CI'))
    errors = sum(1 for _, _, s, _ in all_results if s == 'ERROR')
    total = len(all_results)
    print(f'\n  {matches}/{total} validated | {errors} errors')


if __name__ == '__main__':
    main()
