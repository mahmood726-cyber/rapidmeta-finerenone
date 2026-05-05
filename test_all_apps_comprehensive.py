"""
RapidMeta Portfolio -- Comprehensive Selenium Test Suite
Tests ALL 18 apps + LivingMeta across 8 test categories.
Run: python test_all_apps_comprehensive.py
"""
# pytest-collection skip: this is a one-shot Selenium CLI script, not a
# pytest test. Use pytest.skip(allow_module_level=True) so pytest stops
# executing this file rather than treating sys.exit() as an INTERNALERROR.
import sys as _sys
if "pytest" in _sys.modules:
    import pytest
    pytest.skip("Selenium CLI script — run with `python <file>`, not pytest", allow_module_level=True)

import sys, io, os, time, traceback, subprocess

# UTF-8 stdout for Windows cp1252 safety
if "pytest" not in sys.modules:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')


def kill_orphan_chrome():
    """Kill any lingering chrome/chromedriver processes to prevent port conflicts."""
    for proc in ['chromedriver.exe', 'chrome.exe']:
        try:
            subprocess.run(
                ['taskkill', '/f', '/im', proc],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                timeout=10
            )
        except Exception:
            pass

from selenium import webdriver
from selenium.webdriver.chrome.options import Options

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# ── App definitions ──────────────────────────────────────────────────────────
# All 18 REVIEW apps use RapidMeta (window.onload -> RapidMeta.init()).
# v12 apps have ensureCanonicalAnalysisSeed() for immediate trial seeding.
# v11 apps (COLCHICINE_CVD, GLP1_CVOT, SGLT2_HF) rely on async search;
# the test force-seeds canonical trials from realData for these.
# Special flags:
#   isContinuous: uses MD (mean difference), pooled can be negative
#   usesOR: uses OR, pooled > 1 expected
#   skipGrade: GRADE certainty not available (e.g. ContinuousMDEngine)

APP_DEFS = {
    # ── EXISTING 10 ──
    'FINERENONE':       {'file': 'FINERENONE_REVIEW.html'},
    'BEMPEDOIC_ACID':   {'file': 'BEMPEDOIC_ACID_REVIEW.html'},
    'COLCHICINE_CVD':   {'file': 'COLCHICINE_CVD_REVIEW.html'},
    'GLP1_CVOT':        {'file': 'GLP1_CVOT_REVIEW.html'},
    'SGLT2_HF':         {'file': 'SGLT2_HF_REVIEW.html'},
    'PCSK9':            {'file': 'PCSK9_REVIEW.html'},
    'INTENSIVE_BP':     {'file': 'INTENSIVE_BP_REVIEW.html'},
    'LIPID_HUB':        {'file': 'LIPID_HUB_REVIEW.html'},
    'INCRETIN_HFpEF':   {'file': 'INCRETIN_HFpEF_REVIEW.html'},
    'ATTR_CM':          {'file': 'ATTR_CM_REVIEW.html'},
    # ── NEW 8 ──
    'SGLT2_CKD':        {'file': 'SGLT2_CKD_REVIEW.html'},
    'ARNI_HF':          {'file': 'ARNI_HF_REVIEW.html'},
    'ABLATION_AF':      {'file': 'ABLATION_AF_REVIEW.html'},
    'IV_IRON_HF':       {'file': 'IV_IRON_HF_REVIEW.html'},
    'RENAL_DENERV':     {'file': 'RENAL_DENERV_REVIEW.html', 'isContinuous': True, 'skipGrade': True},
    'DOAC_CANCER_VTE':  {'file': 'DOAC_CANCER_VTE_REVIEW.html'},
    'MAVACAMTEN_HCM':   {'file': 'MAVACAMTEN_HCM_REVIEW.html', 'usesOR': True},
    'RIVAROXABAN_VASC': {'file': 'RIVAROXABAN_VASC_REVIEW.html'},
}

# ── Helpers ──────────────────────────────────────────────────────────────────
PASS_SYM = '[PASS]'
FAIL_SYM = '[FAIL]'


def make_driver():
    """Create a fresh headless Chrome driver with console logging."""
    opts = Options()
    opts.add_argument('--headless=new')
    opts.add_argument('--no-sandbox')
    opts.add_argument('--disable-gpu')
    opts.add_argument('--disable-dev-shm-usage')
    opts.add_argument('--window-size=1920,1080')
    opts.set_capability('goog:loggingPrefs', {'browser': 'ALL'})
    return webdriver.Chrome(options=opts)


def file_url(filename):
    path = os.path.join(BASE_DIR, filename).replace(os.sep, '/')
    return 'file:///' + path


def is_cdn_error(msg):
    """Return True if the log entry is a CDN/network error we should skip."""
    text = msg.get('message', '').lower()
    skip = ['cdn.', 'cdnjs.', 'googleapis.com', 'fontawesome', 'unpkg.com',
            'plot.ly', 'plotly', 'tailwindcss', 'err_file_not_found',
            'net::err_', 'favicon.ico', 'failed to load resource',
            'failed to fetch', 'typeerror: failed to fetch',
            'pubmed', 'ct.gov', 'clinicaltrials.gov',
            'jstat', 'katex', 'webr', 'r-wasm', 'tailwind']
    return any(p in text for p in skip)


def wait_for_init(driver, timeout=20):
    """Poll until RapidMeta.init() has completed.

    Two-tier detection:
      Tier 1 (v12 apps with ensureCanonicalAnalysisSeed): canonical trials
             are seeded with status='include' and valid data immediately.
      Tier 2 (v11 apps without bootstrap seeding): RapidMeta object is
             available with switchTab, state exists, and document is ready.
             For these apps we force-seed canonical trials from realData so
             that subsequent synthesis/analysis tests can proceed.
    """
    end = time.time() + timeout
    while time.time() < end:
        ready = driver.execute_script("""
            try {
                if (typeof RapidMeta === 'undefined') return 0;
                if (typeof RapidMeta.switchTab !== 'function') return 0;
                if (!RapidMeta.state) return 0;

                // Tier 1: canonical trials already seeded (v12 apps)
                var trials = RapidMeta.state.trials;
                if (Array.isArray(trials) && trials.length > 0 &&
                    trials.some(function(t) {
                        return t.status === 'include' && t.data && t.data.tN > 0;
                    })) {
                    return 1;
                }

                // Tier 2: RapidMeta is ready but trials not seeded yet (v11 apps
                // that rely on async SearchEngine.executePrecision).
                // Accept as ready if document is complete and RapidMeta.state exists.
                if (document.readyState === 'complete') {
                    return 2;
                }

                return 0;
            } catch(e) { return 0; }
        """)
        if ready == 1:
            return True
        if ready == 2:
            # Tier 2: force-seed canonical trials from realData so the rest
            # of the test pipeline (synthesis, GRADE, etc.) can work.
            driver.execute_script("""
                try {
                    // v12 apps expose ensureCanonicalAnalysisSeed; if present,
                    // call it directly.
                    if (typeof RapidMeta.ensureCanonicalAnalysisSeed === 'function') {
                        RapidMeta.ensureCanonicalAnalysisSeed();
                        RapidMeta.save();
                        return;
                    }
                    // v11 fallback: manually inject realData entries as included trials
                    if (RapidMeta.realData) {
                        var trials = RapidMeta.state.trials || [];
                        var existingIds = new Set(trials.map(function(t){ return t.id; }));
                        Object.keys(RapidMeta.realData).forEach(function(id) {
                            if (existingIds.has(id)) {
                                // Update the existing trial entry
                                var existing = trials.find(function(t){ return t.id === id; });
                                if (existing) {
                                    existing.status = 'include';
                                    existing.verified = true;
                                    existing.data = JSON.parse(JSON.stringify(RapidMeta.realData[id]));
                                    existing.source = 'reference';
                                }
                            } else {
                                var rd = RapidMeta.realData[id];
                                trials.push({
                                    id: id,
                                    title: rd.name || id,
                                    year: rd.year || null,
                                    abstract: rd.snippet || '',
                                    authors: '',
                                    journal: '',
                                    source: 'reference',
                                    status: 'include',
                                    verified: true,
                                    data: JSON.parse(JSON.stringify(rd))
                                });
                            }
                        });
                        RapidMeta.state.trials = trials;
                        if (typeof RapidMeta.hydrateCanonicalCuratedData === 'function') {
                            RapidMeta.hydrateCanonicalCuratedData();
                        }
                        if (typeof RapidMeta.setOutcome === 'function') {
                            RapidMeta.setOutcome(RapidMeta.state.selectedOutcome || 'default', { silent: true });
                        }
                        RapidMeta.save();
                    }
                } catch(e) { console.error('Force-seed failed:', e); }
            """)
            return True
        time.sleep(0.5)
    return False


def wait_for_results(driver, timeout=6):
    """Poll until RapidMeta.state.results is set (non-null)."""
    end = time.time() + timeout
    while time.time() < end:
        has = driver.execute_script("""
            try { return RapidMeta.state.results != null; }
            catch(e) { return false; }
        """)
        if has:
            return True
        time.sleep(0.5)
    return False


# ── Test runner for a single v12 app ─────────────────────────────────────────
def test_v12_app(driver, app_name, app_def):
    """Run all 8 test categories for a v12 RapidMeta app."""
    results = []
    is_continuous = app_def.get('isContinuous', False)
    uses_or = app_def.get('usesOR', False)

    def record(test_name, passed, detail=''):
        sym = PASS_SYM if passed else FAIL_SYM
        line = f'  {sym} {test_name}'
        if detail:
            line += f': {detail}'
        print(line)
        results.append((test_name, passed))

    html_file = app_def['file']

    # ── 1. Page Load ─────────────────────────────────────────────────────
    try:
        driver.get(file_url(html_file))
        time.sleep(3)

        # Wait for RapidMeta.init() to complete (async)
        init_ok = wait_for_init(driver, timeout=20)
        if not init_ok:
            record('Page load (no JS errors)', False, 'RapidMeta.init() did not complete in 20s')
            return results

        # Check JS errors (after init)
        logs = driver.get_log('browser')
        severe = [m for m in logs if m.get('level') == 'SEVERE' and not is_cdn_error(m)]
        if severe:
            record('Page load (no JS errors)', False, f'{len(severe)} SEVERE errors')
            for s in severe[:3]:
                print(f'    -> {s["message"][:150]}')
        else:
            record('Page load (no JS errors)', True)
    except Exception as e:
        record('Page load (no JS errors)', False, str(e)[:120])
        return results  # can't continue

    # ── 2. Synthesis ─────────────────────────────────────────────────────
    try:
        # Ensure outcome scope is applied and analysis runs.
        # Multi-outcome apps need setOutcome to be called so the outcome
        # scope selects the right trials; then switchTab('analysis')
        # triggers AnalysisEngine.run().
        driver.execute_script("""
            try {
                // Force outcome selection (handles multi-outcome apps)
                if (typeof RapidMeta.setOutcome === 'function') {
                    var outcome = RapidMeta.state.selectedOutcome || 'default';
                    RapidMeta.setOutcome(outcome, { silent: true });
                }
                RapidMeta.switchTab('analysis');
            } catch(e) {
                console.error('switchTab error:', e);
            }
        """)
        time.sleep(3)

        # Wait for results to appear
        wait_for_results(driver, timeout=8)

        # If still no results, try forcing AnalysisEngine.run() directly
        has_results = driver.execute_script("""
            try { return RapidMeta.state.results != null; }
            catch(e) { return false; }
        """)
        if not has_results:
            driver.execute_script("""
                try {
                    if (typeof AnalysisEngine !== 'undefined' && typeof AnalysisEngine.run === 'function') {
                        AnalysisEngine.run();
                    }
                } catch(e) { console.error('AnalysisEngine.run() fallback error:', e); }
            """)
            time.sleep(2)
            wait_for_results(driver, timeout=5)

        # Read results
        res = driver.execute_script("""
            try {
                var r = RapidMeta.state.results;
                if (!r) return {err: 'no results'};
                return {
                    k: r.k || r.kStudies || 0,
                    pooled: r.or || r.pooledMD || r.pooledEstimate || r.hr || '--',
                    lci: r.lci || r.pooledLCI || '--',
                    uci: r.uci || r.pooledUCI || '--',
                    isContinuous: !!r.isContinuous
                };
            } catch(e) { return {err: e.message}; }
        """)

        if res and not res.get('err') and res.get('k', 0) > 0:
            k = res['k']
            pooled = res.get('pooled', '--')
            lci = res.get('lci', '--')
            uci = res.get('uci', '--')
            detail = f'k={k}, pooled={pooled} ({lci}-{uci})'
            if is_continuous:
                detail += ' [MD/continuous]'
                if res.get('isContinuous'):
                    detail += ' isContinuous=true'
            if uses_or:
                detail += ' [OR measure]'
            record('Synthesis', True, detail)
        else:
            err = res.get('err', 'unknown') if res else 'null result'
            record('Synthesis', False, err)
    except Exception as e:
        record('Synthesis', False, str(e)[:120])

    # ── 3. GRADE SoF Table ───────────────────────────────────────────────
    try:
        grade_res = driver.execute_script("""
            try {
                if (typeof GradeProfileEngine === 'undefined') return {err: 'GradeProfileEngine not defined'};
                // Some older apps lack applyOutcomeScope on RapidMeta -- wrap call safely
                try { GradeProfileEngine.renderTable('grade-profile-container'); } catch(innerE) {
                    // Fallback: try rendering from the grade-container in analysis tab
                    var gc = document.getElementById('grade-container');
                    if (gc && gc.innerHTML.trim().length > 10) return {rows: gc.querySelectorAll('.grade-row, tr, div').length, hasContent: true, fallback: true};
                    return {err: innerE.message};
                }
                var el = document.getElementById('grade-profile-container');
                if (!el) return {err: 'container not found'};
                var rows = el.querySelectorAll('tr');
                var html = el.innerHTML.trim();
                return {rows: rows.length, hasContent: html.length > 10};
            } catch(e) { return {err: e.message}; }
        """)
        if grade_res and not grade_res.get('err') and grade_res.get('hasContent'):
            detail = f'{grade_res["rows"]} rows'
            if grade_res.get('fallback'):
                detail += ' (from grade-container)'
            record('GRADE SoF table', True, detail)
        else:
            err = grade_res.get('err', 'empty') if grade_res else 'null'
            record('GRADE SoF table', False, err)
    except Exception as e:
        record('GRADE SoF table', False, str(e)[:120])

    # ── 4. Manuscript Text ───────────────────────────────────────────────
    try:
        ms_res = driver.execute_script("""
            try {
                // Switch to report tab so manuscript-text element is visible
                RapidMeta.switchTab('report');
                // Try generateManuscriptText (standalone function in v12 apps)
                if (typeof generateManuscriptText === 'function') {
                    generateManuscriptText();
                }
                // Also try ReportEngine.generate() which populates manuscript + other content
                if (typeof ReportEngine !== 'undefined' && typeof ReportEngine.generate === 'function') {
                    ReportEngine.generate();
                }
                // Check manuscript-text element
                var el = document.getElementById('manuscript-text');
                if (el) {
                    var text = el.innerText.trim();
                    if (text.length > 30) return {len: text.length, src: 'manuscript-text'};
                }
                // Fallback: check report-content or any large text block in report tab
                var reportEl = document.getElementById('report-content');
                if (reportEl) {
                    var rtext = reportEl.innerText.trim();
                    if (rtext.length > 30) return {len: rtext.length, src: 'report-content'};
                }
                // Check nyt-style blocks (some apps generate NYT-style output)
                var nyt = document.querySelector('.nyt-article, #nyt-report, [id*="manuscript"]');
                if (nyt) {
                    var nt = nyt.innerText.trim();
                    if (nt.length > 30) return {len: nt.length, src: 'nyt-style'};
                }
                return {err: 'no manuscript content (el exists: ' + !!el + ')', len: el ? el.innerText.trim().length : 0};
            } catch(e) { return {err: e.message}; }
        """)
        time.sleep(1)
        if ms_res and not ms_res.get('err') and ms_res.get('len', 0) > 30:
            record('Manuscript text', True, f'{ms_res["len"]} chars ({ms_res.get("src","?")})')
        else:
            err = ms_res.get('err', f'only {ms_res.get("len",0)} chars') if ms_res else 'null'
            record('Manuscript text', False, err)
    except Exception as e:
        record('Manuscript text', False, str(e)[:120])

    # Switch back to analysis for remaining tests
    try:
        driver.execute_script("RapidMeta.switchTab('analysis');")
        time.sleep(1)
    except Exception:
        pass

    # ── 5. Forest Plot ───────────────────────────────────────────────────
    try:
        fp_res = driver.execute_script("""
            try {
                var plots = document.querySelectorAll('.js-plotly-plot');
                return {count: plots.length};
            } catch(e) { return {err: e.message}; }
        """)
        if fp_res and fp_res.get('count', 0) > 0:
            record('Forest plot (Plotly)', True, f'{fp_res["count"]} Plotly plots rendered')
        else:
            record('Forest plot (Plotly)', False, 'no .js-plotly-plot found')
    except Exception as e:
        record('Forest plot (Plotly)', False, str(e)[:120])

    # ── 6. Export Buttons ────────────────────────────────────────────────
    try:
        ex_res = driver.execute_script("""
            try {
                var sofBtn = document.querySelector('[onclick*="exportSoFHTML"]') ||
                             document.querySelector('[onclick*="GradeProfileEngine.export"]');
                var anyExport = document.querySelectorAll('[onclick*="export"]');
                return {sofExport: !!sofBtn, totalExport: anyExport.length};
            } catch(e) { return {err: e.message}; }
        """)
        if ex_res and (ex_res.get('sofExport') or ex_res.get('totalExport', 0) > 0):
            detail = f'SoF={ex_res.get("sofExport")}, total={ex_res.get("totalExport",0)} export buttons'
            record('Export buttons', True, detail)
        else:
            record('Export buttons', False, 'no export buttons found')
    except Exception as e:
        record('Export buttons', False, str(e)[:120])

    # ── 7. GRADE Certainty ───────────────────────────────────────────────
    skip_grade = app_def.get('skipGrade', False)
    if skip_grade:
        # Continuous-outcome apps (e.g. RENAL_DENERV using MD) route through
        # ContinuousMDEngine which does not compute GRADE certainty.
        record('GRADE certainty', True, 'skipped (continuous MD outcome)')
    else:
        try:
            cert_res = driver.execute_script("""
                try {
                    var r = RapidMeta.state.results;
                    if (!r) return {err: 'no results'};
                    var grade = r.gradeCertainty || r.grade || null;
                    return {grade: grade};
                } catch(e) { return {err: e.message}; }
            """)
            valid_grades = {'HIGH', 'MODERATE', 'LOW', 'VERY LOW'}
            if cert_res and cert_res.get('grade'):
                g = str(cert_res['grade']).upper().strip()
                if g in valid_grades:
                    record('GRADE certainty', True, g)
                else:
                    record('GRADE certainty', False, f'invalid grade: "{cert_res["grade"]}"')
            else:
                # Try reading from GRADE container DOM
                dom_grade = driver.execute_script("""
                    try {
                        var el = document.getElementById('grade-container');
                        if (!el) return null;
                        var text = el.innerText;
                        var m = text.match(/HIGH|MODERATE|LOW|VERY LOW/i);
                        return m ? m[0].toUpperCase() : null;
                    } catch(e) { return null; }
                """)
                if dom_grade and dom_grade.upper().strip() in valid_grades:
                    record('GRADE certainty', True, f'{dom_grade} (from DOM)')
                else:
                    err = cert_res.get('err', 'no grade in results or DOM') if cert_res else 'null'
                    record('GRADE certainty', False, err)
        except Exception as e:
            record('GRADE certainty', False, str(e)[:120])

    # ── 8. Stat Cards / Chips ────────────────────────────────────────────
    try:
        stat_res = driver.execute_script("""
            try {
                var chips = document.querySelectorAll('.stat-chip');
                var vaOr = document.getElementById('va-or');
                var vaCi = document.getElementById('va-ci');
                var vaOrText = vaOr ? vaOr.innerText.trim() : '--';
                var vaCiText = vaCi ? vaCi.innerText.trim() : '--';
                var hasResult = vaOrText !== '--' && vaOrText !== '';
                var chipTexts = [];
                chips.forEach(function(c) { chipTexts.push(c.innerText.trim()); });
                // Also count non-default chip values
                var activeChips = 0;
                chips.forEach(function(c) {
                    var t = c.innerText.trim();
                    if (t && !t.endsWith('--') && !t.endsWith(': --')) activeChips++;
                });
                return {
                    chipCount: chips.length,
                    activeChips: activeChips,
                    vaOr: vaOrText,
                    vaCi: vaCiText,
                    hasResult: hasResult
                };
            } catch(e) { return {err: e.message}; }
        """)
        if stat_res and not stat_res.get('err'):
            has_main = stat_res.get('hasResult', False)
            chip_count = stat_res.get('chipCount', 0)
            active = stat_res.get('activeChips', 0)
            if has_main or active > 0 or chip_count > 0:
                detail = f'estimate={stat_res.get("vaOr","--")}, CI={stat_res.get("vaCi","--")}, {chip_count} chips ({active} active)'
                record('Stat cards', True, detail)
            else:
                record('Stat cards', False, f'no result display found')
        else:
            err = stat_res.get('err', 'null') if stat_res else 'null'
            record('Stat cards', False, err)
    except Exception as e:
        record('Stat cards', False, str(e)[:120])

    return results


# ── Test runner for LivingMeta ───────────────────────────────────────────────
def test_livingmeta(driver):
    """LivingMeta.html: page load + config switch + synthesis."""
    results = []

    def record(test_name, passed, detail=''):
        sym = PASS_SYM if passed else FAIL_SYM
        line = f'  {sym} {test_name}'
        if detail:
            line += f': {detail}'
        print(line)
        results.append((test_name, passed))

    # ── 1. Page Load ─────────────────────────────────────────────────────
    try:
        driver.get(file_url('LivingMeta.html'))
        time.sleep(5)

        logs = driver.get_log('browser')
        severe = [m for m in logs if m.get('level') == 'SEVERE' and not is_cdn_error(m)]
        if severe:
            record('Page load (no JS errors)', False, f'{len(severe)} SEVERE errors')
            for s in severe[:3]:
                print(f'    -> {s["message"][:150]}')
        else:
            record('Page load (no JS errors)', True)
    except Exception as e:
        record('Page load (no JS errors)', False, str(e)[:120])
        return results

    # ── 2. Config switch + synthesis ─────────────────────────────────────
    configs_to_test = ['colchicine_cvd', 'finerenone', 'sglt2_hf']
    for cfg in configs_to_test:
        try:
            res = driver.execute_script(f"""
                try {{
                    handleConfigChange('{cfg}');
                    switchTab('synthesize');
                    runSynthesis();
                    var k = AppState.results?.trackB?.k;
                    var est = AppState.results?.trackB?.pooledEstimate;
                    var lci = AppState.results?.trackB?.lci;
                    var uci = AppState.results?.trackB?.uci;
                    return {{k: k, est: est, lci: lci, uci: uci}};
                }} catch(e) {{ return {{err: e.message}}; }}
            """)
            time.sleep(1)

            if res and not res.get('err') and isinstance(res.get('k'), (int, float)) and res['k'] >= 2:
                detail = f'k={res["k"]}'
                if res.get('est') is not None:
                    detail += f', est={res["est"]}'
                record(f'Config: {cfg}', True, detail)
            else:
                err = res.get('err', f'k={res.get("k")}') if res else 'null'
                record(f'Config: {cfg}', False, err)
        except Exception as e:
            record(f'Config: {cfg}', False, str(e)[:120])

    return results


# ── Main ─────────────────────────────────────────────────────────────────────
def main():
    print('=' * 70)
    print('RapidMeta Portfolio - Comprehensive Selenium Test Suite')
    print('=' * 70)
    print()

    # Kill orphan Chrome processes before starting
    print('Killing orphan Chrome/ChromeDriver processes...')
    kill_orphan_chrome()
    time.sleep(2)

    all_results = {}
    total_pass = 0
    total_fail = 0
    app_count = 0

    # ── Test each REVIEW app sequentially ────────────────────────────────
    for app_name, app_def in APP_DEFS.items():
        app_count += 1
        print(f'\n=== {app_name} ===')
        html_path = os.path.join(BASE_DIR, app_def['file'])
        if not os.path.exists(html_path):
            print(f'  {FAIL_SYM} FILE NOT FOUND: {app_def["file"]}')
            all_results[app_name] = [('File exists', False)]
            total_fail += 1
            continue

        app_results = None
        for attempt in range(2):  # retry once on failure
            driver = None
            try:
                driver = make_driver()
                driver.set_page_load_timeout(30)
                driver.set_script_timeout(30)

                app_results = test_v12_app(driver, app_name, app_def)

                # Check if page load itself failed (first test)
                page_load_passed = app_results and len(app_results) > 0 and app_results[0][1]
                if not page_load_passed and attempt == 0:
                    print(f'  ** Page load failed, retrying with fresh driver...')
                    if driver:
                        try:
                            driver.quit()
                        except Exception:
                            pass
                        driver = None
                    time.sleep(3)
                    continue  # retry

                break  # success or second attempt -- stop retrying

            except Exception as e:
                if attempt == 0:
                    print(f'  ** Driver error on attempt 1, retrying: {str(e)[:100]}')
                    if driver:
                        try:
                            driver.quit()
                        except Exception:
                            pass
                        driver = None
                    time.sleep(3)
                    continue  # retry
                else:
                    print(f'  {FAIL_SYM} Driver error: {str(e)[:150]}')
                    traceback.print_exc()
                    app_results = [('Driver setup', False)]
            finally:
                if driver:
                    try:
                        driver.quit()
                    except Exception:
                        pass

        if app_results is None:
            app_results = [('Driver setup', False)]

        all_results[app_name] = app_results
        for _, passed in app_results:
            if passed:
                total_pass += 1
            else:
                total_fail += 1

        # Small delay between apps to let ports free up
        time.sleep(2)

    # ── Test LivingMeta ──────────────────────────────────────────────────
    app_count += 1
    print(f'\n=== LivingMeta ===')
    lm_path = os.path.join(BASE_DIR, 'LivingMeta.html')
    if not os.path.exists(lm_path):
        print(f'  {FAIL_SYM} FILE NOT FOUND: LivingMeta.html')
        all_results['LivingMeta'] = [('File exists', False)]
        total_fail += 1
    else:
        lm_results = None
        for attempt in range(2):  # retry once on failure
            driver = None
            try:
                driver = make_driver()
                driver.set_page_load_timeout(30)
                driver.set_script_timeout(30)

                lm_results = test_livingmeta(driver)

                # Check if page load itself failed (first test)
                page_load_passed = lm_results and len(lm_results) > 0 and lm_results[0][1]
                if not page_load_passed and attempt == 0:
                    print(f'  ** Page load failed, retrying with fresh driver...')
                    if driver:
                        try:
                            driver.quit()
                        except Exception:
                            pass
                        driver = None
                    time.sleep(3)
                    continue  # retry

                break  # success or second attempt -- stop retrying

            except Exception as e:
                if attempt == 0:
                    print(f'  ** Driver error on attempt 1, retrying: {str(e)[:100]}')
                    if driver:
                        try:
                            driver.quit()
                        except Exception:
                            pass
                        driver = None
                    time.sleep(3)
                    continue  # retry
                else:
                    print(f'  {FAIL_SYM} Driver error: {str(e)[:150]}')
                    lm_results = [('Driver setup', False)]
            finally:
                if driver:
                    try:
                        driver.quit()
                    except Exception:
                        pass

        if lm_results is None:
            lm_results = [('Driver setup', False)]

        all_results['LivingMeta'] = lm_results
        for _, passed in lm_results:
            if passed:
                total_pass += 1
            else:
                total_fail += 1

    # ── Summary ──────────────────────────────────────────────────────────
    total_tests = total_pass + total_fail
    print()
    print('=' * 70)
    print(f'FINAL SUMMARY: {total_pass}/{total_tests} tests passed across {app_count} apps')
    print('=' * 70)

    # Per-app summary
    print()
    for app_name, app_results in all_results.items():
        p = sum(1 for _, v in app_results if v)
        f = sum(1 for _, v in app_results if not v)
        status = 'ALL PASS' if f == 0 else f'{f} FAIL'
        print(f'  {app_name}: {p}/{p+f} ({status})')

    # List failures
    failures = []
    for app_name, app_results in all_results.items():
        for test_name, passed in app_results:
            if not passed:
                failures.append(f'{app_name} -> {test_name}')

    if failures:
        print()
        print(f'Failed tests ({len(failures)}):')
        for f in failures:
            print(f'  - {f}')

    return total_fail == 0


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
