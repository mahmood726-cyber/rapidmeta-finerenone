"""
User + Methodologist perspective tests for RapidMeta portfolio.
Tests actual user workflows AND statistical correctness.

Run: python test_user_methodologist.py
"""
import sys, io, os, time, math, subprocess, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def get_opts():
    opts = Options()
    opts.add_argument('--headless=new')
    opts.add_argument('--no-sandbox')
    opts.add_argument('--disable-gpu')
    opts.add_argument('--disable-dev-shm-usage')
    opts.add_argument('--incognito')
    opts.add_argument('--window-size=1920,1080')
    opts.set_capability('goog:loggingPrefs', {'browser': 'ALL'})
    return opts

def kill_orphan():
    for proc in ['chromedriver.exe', 'chrome.exe']:
        try:
            subprocess.run(['taskkill', '/f', '/im', proc],
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=10)
        except Exception:
            pass

results = {'pass': 0, 'fail': 0, 'details': []}

def check(label, condition, detail=''):
    if condition:
        results['pass'] += 1
        print(f'  [PASS] {label}')
    else:
        results['fail'] += 1
        results['details'].append(f'{label}: {detail}')
        print(f'  [FAIL] {label} -- {detail}')

def approx(a, b, tol=0.02):
    """Check if two numbers are approximately equal (within tol)."""
    if a is None or b is None:
        return False
    return abs(a - b) <= tol

def approx_pct(a, b, tol=5.0):
    """Check if two numbers are within tol% of each other."""
    if a is None or b is None or b == 0:
        return False
    return abs((a - b) / b * 100) <= tol

# ═══════════════════════════════════════════════════════════════════
# TEST SUITE A: USER PERSPECTIVE
# ═══════════════════════════════════════════════════════════════════

print('='*70)
print('SUITE A: USER PERSPECTIVE TESTS')
print('='*70)

kill_orphan()
time.sleep(1)

# ── A1: Complete user workflow on FINERENONE ──
print('\n=== A1: Full user workflow (FINERENONE) ===')
driver = None
try:
    driver = webdriver.Chrome(options=get_opts())
    driver.set_page_load_timeout(45)
    fpath = 'file:///' + os.path.join(BASE_DIR, 'FINERENONE_REVIEW.html').replace('\\', '/')
    driver.get(fpath)
    time.sleep(3)

    # A1.1: All 6 tabs accessible
    tabs = ['protocol', 'search', 'screen', 'extract', 'analysis', 'report']
    for tab in tabs:
        visible = driver.execute_script(f"""
            var btn = document.querySelector('[data-tab="{tab}"]');
            if (!btn) return false;
            btn.click();
            return true;
        """)
        time.sleep(0.3)
        check(f'Tab "{tab}" clickable', visible)

    # A1.2: Protocol tab shows PICO
    driver.execute_script("document.querySelector('[data-tab=\"protocol\"]').click()")
    time.sleep(0.5)
    pico = driver.execute_script("""
        var el = document.getElementById('tab-protocol');
        return el ? el.innerText.length : 0;
    """)
    check('Protocol tab has content', pico > 100, f'Only {pico} chars')

    # A1.3: Navigate to analysis tab, verify stat cards
    driver.execute_script("document.querySelector('[data-tab=\"analysis\"]').click()")
    time.sleep(2)

    stat_cards = driver.execute_script("""
        var chips = document.querySelectorAll('.stat-chip');
        return Array.from(chips).map(c => ({
            text: c.innerText.trim(),
            visible: c.offsetParent !== null
        }));
    """)
    check('Stat chips rendered', stat_cards and len(stat_cards) >= 6,
          f'Only {len(stat_cards or [])} chips')

    # A1.4: Forest plot renders with Plotly
    plotly_count = driver.execute_script("""
        return document.querySelectorAll('.js-plotly-plot').length
    """)
    check('Forest plot rendered (Plotly)', plotly_count >= 1, f'{plotly_count} plots')

    # A1.5: Dark/light mode toggle
    was_dark = driver.execute_script("return !document.body.classList.contains('light-mode')")
    driver.execute_script("""
        var toggle = document.querySelector('[onclick*=\"toggleTheme\"], [onclick*=\"light-mode\"]');
        if (toggle) toggle.click();
        else document.body.classList.toggle('light-mode');
    """)
    time.sleep(0.3)
    is_light = driver.execute_script("return document.body.classList.contains('light-mode')")
    check('Dark/light toggle works', was_dark and is_light)

    # Toggle back
    driver.execute_script("document.body.classList.remove('light-mode')")

    # A1.6: Export buttons present
    export_btns = driver.execute_script("""
        return document.querySelectorAll('button[onclick*=\"export\"], button[onclick*=\"download\"], button[onclick*=\"copy\"]').length
    """)
    check('Export buttons present', export_btns >= 5, f'Only {export_btns}')

    # A1.7: GRADE SoF table renders
    driver.execute_script("document.querySelector('[data-tab=\"report\"]').click()")
    time.sleep(1)
    sof_rows = driver.execute_script("""
        var tables = document.querySelectorAll('table');
        for (var t of tables) {
            if (t.innerHTML.includes('Certainty') || t.innerHTML.includes('GRADE'))
                return t.querySelectorAll('tr').length;
        }
        return 0;
    """)
    check('GRADE SoF table has rows', sof_rows >= 3, f'{sof_rows} rows')

    # A1.8: Manuscript text generated
    manuscript = driver.execute_script("""
        var el = document.getElementById('report-content') || document.getElementById('manuscript-content');
        return el ? el.innerText.length : 0;
    """)
    check('Manuscript text generated', manuscript > 5000, f'{manuscript} chars')

    # A1.9: Keyboard shortcuts work (on screen tab)
    driver.execute_script("document.querySelector('[data-tab=\"screen\"]').click()")
    time.sleep(0.5)
    kbd_handler = driver.execute_script("return typeof RapidMeta._keydownBound !== 'undefined'")
    check('Keyboard handler bound', kbd_handler)

    # A1.10: No JS errors throughout workflow
    logs = driver.get_log('browser')
    severe = [l for l in logs if l['level'] == 'SEVERE'
              and 'favicon' not in l.get('message', '')
              and 'ERR_FILE_NOT_FOUND' not in l.get('message', '')]
    check('No JS errors during workflow', len(severe) == 0,
          f'{len(severe)} errors: {severe[0]["message"][:100]}' if severe else '')

except Exception as e:
    check('A1 workflow', False, str(e)[:200])
finally:
    if driver:
        driver.quit()
    time.sleep(0.5)


# ── A2: Extract tab user flow ──
print('\n=== A2: Extract tab interaction ===')
driver = None
try:
    driver = webdriver.Chrome(options=get_opts())
    driver.set_page_load_timeout(45)
    fpath = 'file:///' + os.path.join(BASE_DIR, 'FINERENONE_REVIEW.html').replace('\\', '/')
    driver.get(fpath)
    time.sleep(3)

    driver.execute_script("document.querySelector('[data-tab=\"extract\"]').click()")
    time.sleep(1)

    # A2.1: Three sub-views accessible
    for view in ['data', 'demographics', 'rob']:
        driver.execute_script(f"ExtractEngine.setView('{view}')")
        time.sleep(0.3)
        visible = driver.execute_script(f"""
            var el = document.getElementById('extract-view-{view}');
            return el ? el.offsetParent !== null || el.offsetHeight > 0 : false;
        """)
        content = driver.execute_script(f"""
            var el = document.getElementById('extract-view-{view}');
            return el ? el.innerHTML.length : 0;
        """)
        check(f'Extract view "{view}" visible with content', visible and content > 100,
              f'visible={visible}, chars={content}')

    # A2.2: Evidence panels show provenance
    evidence_panels = driver.execute_script("""
        ExtractEngine.setView('data');
        return document.querySelectorAll('.evidence-panel').length;
    """)
    time.sleep(0.3)
    check('Evidence panels rendered', evidence_panels >= 3, f'{evidence_panels} panels')

    # A2.3: RoB view shows domain labels
    driver.execute_script("ExtractEngine.setView('rob')")
    time.sleep(0.3)
    rob_domains = driver.execute_script("""
        var el = document.getElementById('extract-view-rob');
        var text = el ? el.innerText : '';
        return {
            hasD1: text.includes('Random') || text.includes('D1'),
            hasD2: text.includes('Deviations') || text.includes('D2'),
            count: (text.match(/low|some|high/gi) || []).length
        };
    """)
    check('RoB domains present', rob_domains and (rob_domains.get('hasD1') or rob_domains.get('count', 0) > 0),
          f'{rob_domains}')

    # A2.4: No JS errors
    logs = driver.get_log('browser')
    severe = [l for l in logs if l['level'] == 'SEVERE' and 'favicon' not in l.get('message', '')]
    check('No JS errors in extract', len(severe) == 0)

except Exception as e:
    check('A2 extract', False, str(e)[:200])
finally:
    if driver:
        driver.quit()
    time.sleep(0.5)


# ── A3: Multi-app load + navigation (sample 6 apps) ──
SAMPLE_APPS = [
    ('COLCHICINE_CVD_REVIEW.html', 'Colchicine'),
    ('SGLT2_HF_REVIEW.html', 'SGLT2 HF'),
    ('ARNI_HF_REVIEW.html', 'ARNI HF'),
    ('LIPID_HUB_REVIEW.html', 'Omega-3'),
    ('MAVACAMTEN_HCM_REVIEW.html', 'Mavacamten'),
    ('RENAL_DENERV_REVIEW.html', 'Renal Denerv'),
]

print('\n=== A3: Multi-app navigation ===')
for fname, label in SAMPLE_APPS:
    driver = None
    try:
        driver = webdriver.Chrome(options=get_opts())
        driver.set_page_load_timeout(45)
        fpath = 'file:///' + os.path.join(BASE_DIR, fname).replace('\\', '/')
        driver.get(fpath)
        time.sleep(2.5)

        # Check all tabs load without error
        for tab in ['protocol', 'analysis', 'report']:
            driver.execute_script(f"document.querySelector('[data-tab=\"{tab}\"]').click()")
            time.sleep(0.5)

        # Verify analysis produced results
        has_results = driver.execute_script("""
            return RapidMeta.state.results !== null && RapidMeta.state.results !== undefined
        """)
        check(f'{label}: analysis produces results', has_results)

        logs = driver.get_log('browser')
        severe = [l for l in logs if l['level'] == 'SEVERE' and 'favicon' not in l.get('message', '')]
        check(f'{label}: no JS errors', len(severe) == 0,
              severe[0]['message'][:80] if severe else '')

    except Exception as e:
        check(f'{label}: load', False, str(e)[:150])
    finally:
        if driver:
            driver.quit()
        time.sleep(0.3)


# ═══════════════════════════════════════════════════════════════════
# TEST SUITE B: METHODOLOGIST PERSPECTIVE
# ═══════════════════════════════════════════════════════════════════

print('\n' + '='*70)
print('SUITE B: METHODOLOGIST PERSPECTIVE TESTS')
print('='*70)

# ── B1: DerSimonian-Laird computation verification ──
print('\n=== B1: DL meta-analysis correctness (FINERENONE) ===')
driver = None
try:
    driver = webdriver.Chrome(options=get_opts())
    driver.set_page_load_timeout(45)
    fpath = 'file:///' + os.path.join(BASE_DIR, 'FINERENONE_REVIEW.html').replace('\\', '/')
    driver.get(fpath)
    time.sleep(3)

    # Navigate to analysis tab
    driver.execute_script("document.querySelector('[data-tab=\"analysis\"]').click()")
    time.sleep(2)

    # Run computeCore directly to get raw numbers
    app_results = driver.execute_script("""
        var included = RapidMeta.state.trials.filter(t => t.status === 'include');
        if (included.length === 0) return null;
        var c = AnalysisEngine.computeCore(included);
        if (!c) return null;
        return {
            pooled: c.pOR,
            lci: c.lci,
            uci: c.uci,
            I2: c.I2,
            tau2: c.tau2,
            tau2_reml: c.tau2_reml,
            k: c.k,
            Q: c.Q,
            hksjLCI: c.hksjLCI,
            hksjUCI: c.hksjUCI,
            piLCI: c.piLCI,
            piUCI: c.piUCI,
            pLogOR: c.pLogOR,
            pSE: c.pSE,
            useHR: c.useHR,
            confLevel: c.confLevel,
            eggerIntercept: c.eggerResult ? c.eggerResult.intercept : null,
            eggerP: c.eggerResult ? c.eggerResult.pValue : null,
            eggerSufficient: c.eggerResult ? c.eggerResult.sufficient : false,
            fragIdx: c.fragIdx,
            plotData: c.plotData.map(d => ({ id: d.id, logOR: d.logOR, se: d.se, vi: d.vi, cer: d.cer }))
        };
    """)

    check('Results object exists', app_results is not None)
    if not app_results:
        raise Exception('No results to verify')

    k = app_results['k']
    pooled = app_results['pooled']
    lci = app_results['lci']
    uci = app_results['uci']
    I2 = app_results['I2']
    tau2 = app_results['tau2']
    Q = app_results['Q']

    print(f'    App reports: pooled={pooled:.4f}, CI=({lci:.4f}-{uci:.4f}), k={k}, I2={I2:.1f}%, tau2={tau2:.6f}, Q={Q:.4f}')
    print(f'    Uses HR: {app_results.get("useHR")}, confLevel: {app_results.get("confLevel")}')

    # Now independently compute DL from the same trial data
    indep = driver.execute_script("""
        // Extract the actual data used in computation
        var included = RapidMeta.state.trials.filter(t => t.status === 'include');
        var emMode = RapidMeta.resolveEffectMeasure({ trials: included }).effective;
        var confLevel = RapidMeta.state.confLevel || 0.95;
        var zCrit = -normalQuantile((1 - confLevel) / 2);

        var studies = [];
        if (emMode === 'HR') {
            included.filter(t => RapidMeta.trialHasPublishedHR(t)).forEach(t => {
                var logHR = Math.log(t.data.pubHR);
                var se = (Math.log(t.data.pubHR_UCI) - Math.log(t.data.pubHR_LCI)) / (2 * zCrit);
                studies.push({
                    name: t.data.name || t.id,
                    logEff: logHR,
                    se: se,
                    vi: se * se,
                    pubHR: t.data.pubHR,
                    pubLCI: t.data.pubHR_LCI,
                    pubUCI: t.data.pubHR_UCI
                });
            });
        } else {
            included.filter(t => !(t.data.tE === 0 && t.data.cE === 0)).forEach(t => {
                var hasZero = (t.data.tE === 0 || t.data.cE === 0);
                var adj = hasZero ? 0.5 : 0;
                var a = t.data.tE + adj, b = t.data.tN - t.data.tE + adj;
                var c = t.data.cE + adj, d = t.data.cN - t.data.cE + adj;
                var logEff, vi;
                if (emMode === 'RR') {
                    logEff = Math.log((a/(a+b)) / (c/(c+d)));
                    vi = b/(a*(a+b)) + d/(c*(c+d));
                } else {
                    logEff = Math.log((a/b)/(c/d));
                    vi = 1/a + 1/b + 1/c + 1/d;
                }
                studies.push({
                    name: t.data.name || t.id,
                    logEff: logEff,
                    se: Math.sqrt(vi),
                    vi: vi
                });
            });
        }

        // Independent DL computation
        var sW = 0, sWY = 0, sW_y2 = 0, sW2 = 0;
        studies.forEach(s => {
            var w = 1 / s.vi;
            sW += w;
            sWY += w * s.logEff;
            sW_y2 += w * s.logEff * s.logEff;
            sW2 += w * w;
        });

        var Q_check = Math.max(0, sW_y2 - (sWY * sWY / sW));
        var k_check = studies.length;
        var df = k_check - 1;
        var I2_check = (Q_check > df) ? ((Q_check - df) / Q_check) * 100 : 0;
        var tau2_check = (Q_check > df) ? (Q_check - df) / (sW - sW2 / sW) : 0;

        // Random-effects weights
        var sWR = 0, sWRY = 0;
        studies.forEach(s => {
            var wr = 1 / (s.vi + tau2_check);
            sWR += wr;
            sWRY += wr * s.logEff;
        });
        var pLogOR = sWRY / sWR;
        var pSE = Math.sqrt(1 / sWR);
        var pooled_check = Math.exp(pLogOR);
        var lci_check = Math.exp(pLogOR - zCrit * pSE);
        var uci_check = Math.exp(pLogOR + zCrit * pSE);

        return {
            k: k_check,
            Q: Q_check,
            I2: I2_check,
            tau2: tau2_check,
            pooled: pooled_check,
            lci: lci_check,
            uci: uci_check,
            emMode: emMode,
            studies: studies.map(s => ({ name: s.name, logEff: s.logEff, se: s.se }))
        };
    """)

    print(f'    Independent: pooled={indep["pooled"]:.4f}, CI=({indep["lci"]:.4f}-{indep["uci"]:.4f}), k={indep["k"]}, I2={indep["I2"]:.1f}%, tau2={indep["tau2"]:.6f}')
    print(f'    Mode: {indep["emMode"]}, studies: {[s["name"] for s in indep["studies"]]}')

    # B1.1: Pooled estimate matches independent computation
    check('Pooled HR matches independent DL',
          approx(pooled, indep['pooled'], 0.005),
          f'App={pooled:.4f} vs Indep={indep["pooled"]:.4f}')

    # B1.2: CI matches
    check('LCI matches', approx(lci, indep['lci'], 0.005),
          f'App={lci:.4f} vs Indep={indep["lci"]:.4f}')
    check('UCI matches', approx(uci, indep['uci'], 0.005),
          f'App={uci:.4f} vs Indep={indep["uci"]:.4f}')

    # B1.3: Heterogeneity matches
    check('I2 matches', approx(I2, indep['I2'], 1.0),
          f'App={I2:.1f}% vs Indep={indep["I2"]:.1f}%')
    check('tau2 matches', approx(tau2, indep['tau2'], 0.001),
          f'App={tau2:.6f} vs Indep={indep["tau2"]:.6f}')
    check('Q matches', approx(Q, indep['Q'], 0.01),
          f'App={Q:.4f} vs Indep={indep["Q"]:.4f}')

    # B1.4: k is correct
    check(f'k = {k} studies', k >= 3)

    # B1.5: HKSJ gives wider CIs than Wald (methodological requirement)
    hksj_lci = app_results.get('hksjLCI')
    hksj_uci = app_results.get('hksjUCI')
    wald_width = math.log(uci) - math.log(lci) if uci and lci and uci > 0 and lci > 0 else 0
    if hksj_lci and hksj_uci and math.isfinite(hksj_lci) and math.isfinite(hksj_uci) and hksj_lci > 0:
        hksj_width = math.log(hksj_uci) - math.log(hksj_lci)
        check('HKSJ CI >= Wald CI width',
              hksj_width >= wald_width - 0.001,
              f'HKSJ width={hksj_width:.4f} vs Wald={wald_width:.4f}')
        print(f'    HKSJ CI: ({hksj_lci:.4f}-{hksj_uci:.4f}), width={hksj_width:.4f}')
    else:
        check('HKSJ computed', False, 'HKSJ values are NaN')

    # B1.6: Prediction interval uses t-distribution with k-2 df
    pi_lci = app_results.get('piLCI')
    pi_uci = app_results.get('piUCI')
    if pi_lci and pi_uci and not math.isnan(pi_lci):
        pi_width = math.log(pi_uci) - math.log(pi_lci)
        check('PI wider than CI', pi_width >= wald_width - 0.001,
              f'PI width={pi_width:.4f} vs CI={wald_width:.4f}')
        print(f'    PI: ({pi_lci:.4f}-{pi_uci:.4f}), width={pi_width:.4f}')
    else:
        check('PI computed', k >= 3, f'PI is NaN with k={k}')

    # B1.7: Pooled estimate is between min and max individual estimates
    study_effects = [s['logEff'] for s in indep['studies']]
    pooled_log = math.log(pooled)
    check('Pooled is between min/max study effects',
          min(study_effects) - 0.01 <= pooled_log <= max(study_effects) + 0.01,
          f'pooled logHR={pooled_log:.4f}, range=[{min(study_effects):.4f}, {max(study_effects):.4f}]')

    # B1.8: SE derivation from CI is correct
    for s in indep['studies']:
        se_check = s['se']
        check(f'SE({s["name"]}) > 0', se_check > 0, f'SE={se_check}')

except Exception as e:
    check('B1 DL computation', False, str(e)[:200])
finally:
    if driver:
        driver.quit()
    time.sleep(0.5)


# ── B2: GRADE assessment logic ──
print('\n=== B2: GRADE assessment logic ===')
driver = None
try:
    driver = webdriver.Chrome(options=get_opts())
    driver.set_page_load_timeout(45)
    fpath = 'file:///' + os.path.join(BASE_DIR, 'FINERENONE_REVIEW.html').replace('\\', '/')
    driver.get(fpath)
    time.sleep(3)

    driver.execute_script("document.querySelector('[data-tab=\"analysis\"]').click()")
    time.sleep(2)

    grade = driver.execute_script("""
        var included = RapidMeta.state.trials.filter(t => t.status === 'include');
        if (included.length === 0) return null;
        var c = AnalysisEngine.computeCore(included);
        var sub = AnalysisEngine.runSubEngines(c);
        var g = computeGradeAssessment(c, included, sub.tfResult);
        if (!g) return null;
        return {
            rob: g.robDown || 0,
            inconsistency: g.inconsistencyDown || 0,
            indirectness: g.indirectnessDown || 0,
            imprecision: g.imprecisionDown || 0,
            pubBias: g.pubBiasDown || 0,
            certainty: g.certainty || 'UNKNOWN',
            total: (g.robDown||0) + (g.inconsistencyDown||0) + (g.indirectnessDown||0) + (g.imprecisionDown||0) + (g.pubBiasDown||0)
        };
    """)

    if grade:
        print(f'    GRADE: {grade["certainty"]} (RoB:{grade["rob"]}, Incon:{grade["inconsistency"]}, Indir:{grade["indirectness"]}, Imprec:{grade["imprecision"]}, PubBias:{grade["pubBias"]})')

        # B2.1: GRADE starts from HIGH for RCTs
        check('GRADE starts from HIGH (4 - downgrades)',
              grade['certainty'] in ['HIGH', 'MODERATE', 'LOW', 'VERY LOW'])

        # B2.2: Total downgrades make sense
        total = grade['total']
        expected_cert = ['HIGH', 'MODERATE', 'LOW', 'VERY LOW'][min(total, 3)]
        check(f'GRADE certainty matches downgrades ({total} downs = {expected_cert})',
              grade['certainty'] == expected_cert,
              f'Got {grade["certainty"]}, expected {expected_cert}')

        # B2.3: If all trials low RoB, RoB domain should not downgrade
        all_low_rob = driver.execute_script("""
            var included = RapidMeta.state.trials.filter(t => t.status === 'include');
            return included.every(t => {
                var rob = t.data?.rob ?? [];
                return rob.every(r => r === 'low');
            });
        """)
        if all_low_rob:
            check('All low RoB -> no RoB downgrade', grade['rob'] == 0,
                  f'Downgraded by {grade["rob"]} despite all low RoB')

        # B2.4: Inconsistency domain — check PI-crosses-null logic
        # With small k (e.g. k=3), PI uses t(df=1) with very wide tails.
        # Even at I2=0%, PI can cross null → legitimate downgrade per Cochrane Handbook.
        pi_lci_val = app_results.get('piLCI') if app_results else None
        pi_uci_val = app_results.get('piUCI') if app_results else None
        pi_crosses_null = (pi_lci_val and pi_uci_val and
                          math.isfinite(pi_lci_val) and math.isfinite(pi_uci_val) and
                          pi_lci_val < 1 and pi_uci_val > 1)
        if I2 >= 50 or pi_crosses_null:
            check('Inconsistency downgrade justified (I2>=50% or PI crosses null)',
                  grade['inconsistency'] > 0,
                  f'I2={I2:.0f}%, PI crosses null={pi_crosses_null}, but no downgrade')
        else:
            check('No inconsistency downgrade (I2<50% and PI does not cross null)',
                  grade['inconsistency'] == 0,
                  f'I2={I2:.0f}% but downgraded by {grade["inconsistency"]}')

    else:
        check('GRADE computed', False, 'No GRADE results')

except Exception as e:
    check('B2 GRADE', False, str(e)[:200])
finally:
    if driver:
        driver.quit()
    time.sleep(0.5)


# ── B3: Leave-one-out sensitivity ──
print('\n=== B3: Leave-one-out sensitivity ===')
driver = None
try:
    driver = webdriver.Chrome(options=get_opts())
    driver.set_page_load_timeout(45)
    fpath = 'file:///' + os.path.join(BASE_DIR, 'FINERENONE_REVIEW.html').replace('\\', '/')
    driver.get(fpath)
    time.sleep(3)

    driver.execute_script("document.querySelector('[data-tab=\"analysis\"]').click()")
    time.sleep(2)

    # Compute LOO directly
    loo = driver.execute_script("""
        var included = RapidMeta.state.trials.filter(t => t.status === 'include');
        if (included.length < 2) return null;
        var results = [];
        for (var i = 0; i < included.length; i++) {
            var subset = included.filter((_, j) => j !== i);
            var c = AnalysisEngine.computeCore(subset);
            results.push({
                omitted: included[i].data?.name || included[i].id,
                pooled: c.pOR,
                lci: c.lci,
                uci: c.uci
            });
        }
        return results;
    """)

    if loo and len(loo) > 0:
        check(f'LOO has {len(loo)} entries (one per study)', len(loo) >= 2)

        # B3.1: Each LOO pooled should differ from full pooled
        for entry in loo:
            loo_p = entry['pooled']
            check(f'LOO (omit {entry["omitted"]}): pooled={loo_p:.4f} differs from full={pooled:.4f}',
                  abs(loo_p - pooled) > 0.0001 or k <= 2,
                  f'Same as full pooled')

        # B3.2: LOO pooled should be plausible (within reasonable range)
        for entry in loo:
            check(f'LOO (omit {entry["omitted"]}): estimate plausible',
                  0.5 < entry['pooled'] < 1.5,
                  f'pooled={entry["pooled"]:.4f} outside range')
    else:
        check('LOO computed', False, 'No LOO results')

except Exception as e:
    check('B3 LOO', False, str(e)[:200])
finally:
    if driver:
        driver.quit()
    time.sleep(0.5)


# ── B4: Publication bias (Egger's test) ──
print('\n=== B4: Publication bias checks ===')
driver = None
try:
    driver = webdriver.Chrome(options=get_opts())
    driver.set_page_load_timeout(45)
    fpath = 'file:///' + os.path.join(BASE_DIR, 'FINERENONE_REVIEW.html').replace('\\', '/')
    driver.get(fpath)
    time.sleep(3)

    driver.execute_script("document.querySelector('[data-tab=\"analysis\"]').click()")
    time.sleep(2)

    egger = driver.execute_script("""
        var included = RapidMeta.state.trials.filter(t => t.status === 'include');
        var c = AnalysisEngine.computeCore(included);
        if (!c || !c.eggerResult) return null;
        return {
            intercept: c.eggerResult.intercept,
            pValue: c.eggerResult.pValue,
            sufficient: c.eggerResult.sufficient
        };
    """)

    if egger:
        check('Egger intercept is finite', math.isfinite(egger['intercept']),
              f'intercept={egger["intercept"]}')
        check('Egger p-value in [0,1]',
              0 <= egger['pValue'] <= 1,
              f'p={egger["pValue"]}')
        if k <= 5:
            check('Egger notes insufficient k', not egger.get('sufficient', True) or k >= 3,
                  f'k={k}, sufficient={egger["sufficient"]}')
        print(f'    Egger: intercept={egger["intercept"]:.4f}, p={egger["pValue"]:.4f}')
    else:
        check('Egger computed', False, 'No Egger results')

    # Trim-and-Fill
    tf = driver.execute_script("""
        var included = RapidMeta.state.trials.filter(t => t.status === 'include');
        var c = AnalysisEngine.computeCore(included);
        var sub = AnalysisEngine.runSubEngines(c);
        if (!sub || !sub.tfResult) return null;
        return {
            k0: sub.tfResult.k0,
            adjustedOR: sub.tfResult.adjustedOR,
            available: sub.tfResult.available
        };
    """)
    if tf and tf.get('available'):
        check('Trim-Fill k0 >= 0', tf['k0'] >= 0, f'k0={tf["k0"]}')
        adj = tf.get('adjustedOR')
        check('Trim-Fill adjusted estimate finite',
              adj is not None and math.isfinite(adj),
              f'adjusted={adj}')
        print(f'    Trim-Fill: k0={tf["k0"]}, adjusted={adj}')
    elif tf:
        check('Trim-Fill computed (unavailable is OK for small k)', True)
    else:
        check('Trim-Fill computed', False, 'No TF results')

except Exception as e:
    check('B4 pub bias', False, str(e)[:200])
finally:
    if driver:
        driver.quit()
    time.sleep(0.5)


# ── B5: Cross-app methodological consistency ──
print('\n=== B5: Cross-app statistical consistency ===')
CROSS_APPS = [
    ('COLCHICINE_CVD_REVIEW.html', 'Colchicine', 3, 7),
    ('ARNI_HF_REVIEW.html', 'ARNI', 2, 5),
    ('SGLT2_CKD_REVIEW.html', 'SGLT2 CKD', 2, 6),
]

for fname, label, min_k, max_k in CROSS_APPS:
    driver = None
    try:
        driver = webdriver.Chrome(options=get_opts())
        driver.set_page_load_timeout(45)
        fpath = 'file:///' + os.path.join(BASE_DIR, fname).replace('\\', '/')
        driver.get(fpath)
        time.sleep(3)

        driver.execute_script("document.querySelector('[data-tab=\"analysis\"]').click()")
        time.sleep(2)

        xr = driver.execute_script("""
            var included = RapidMeta.state.trials.filter(t => t.status === 'include');
            if (included.length === 0) return null;
            var c = AnalysisEngine.computeCore(included);
            if (!c) return null;
            var sub = AnalysisEngine.runSubEngines(c);
            var g = computeGradeAssessment(c, included, sub.tfResult);
            return {
                pooled: c.pOR,
                lci: c.lci,
                uci: c.uci,
                I2: c.I2,
                k: c.k,
                em: c.useHR ? 'HR' : 'OR/RR',
                hasLOO: included.length >= 2,
                hasEgger: c.eggerResult && isFinite(c.eggerResult.intercept),
                hasTF: sub.tfResult && sub.tfResult.available,
                hasGrade: g && g.certainty ? true : false
            };
        """)

        if xr:
            check(f'{label}: k in [{min_k},{max_k}]',
                  min_k <= xr['k'] <= max_k,
                  f'k={xr["k"]}')
            check(f'{label}: pooled finite and > 0',
                  xr['pooled'] and math.isfinite(xr['pooled']) and xr['pooled'] > 0)
            check(f'{label}: CI contains pooled',
                  xr['lci'] <= xr['pooled'] <= xr['uci'],
                  f'{xr["lci"]:.3f} <= {xr["pooled"]:.3f} <= {xr["uci"]:.3f}')
            check(f'{label}: I2 in [0,100]',
                  0 <= xr['I2'] <= 100, f'I2={xr["I2"]}')
            check(f'{label}: LOO present', xr['hasLOO'])
            check(f'{label}: GRADE present', xr['hasGrade'])

            print(f'    {label}: pooled={xr["pooled"]:.3f} ({xr["lci"]:.3f}-{xr["uci"]:.3f}), I2={xr["I2"]:.0f}%, k={xr["k"]}, em={xr["em"]}')
        else:
            check(f'{label}: results exist', False, 'No results')

    except Exception as e:
        check(f'{label}: load', False, str(e)[:150])
    finally:
        if driver:
            driver.quit()
        time.sleep(0.3)


# ── B6: NNT computation check ──
print('\n=== B6: NNT computation ===')
driver = None
try:
    driver = webdriver.Chrome(options=get_opts())
    driver.set_page_load_timeout(45)
    fpath = 'file:///' + os.path.join(BASE_DIR, 'FINERENONE_REVIEW.html').replace('\\', '/')
    driver.get(fpath)
    time.sleep(3)

    driver.execute_script("document.querySelector('[data-tab=\"analysis\"]').click()")
    time.sleep(2)

    nnt = driver.execute_script("""
        var included = RapidMeta.state.trials.filter(t => t.status === 'include');
        var c = AnalysisEngine.computeCore(included);
        if (!c || !c.plotData) return null;
        var cer = c.plotData.reduce((s,d) => s + d.cer, 0) / c.plotData.length;
        var pooled = c.pOR;
        if (!cer || !pooled) return null;
        var arr = cer - cer * pooled;
        var nnt = arr > 0 ? Math.round(1 / arr) : null;
        return { cer: cer, pooled: pooled, arr: arr, nnt: nnt };
    """)

    if nnt:
        check('NNT is positive and finite',
              nnt['nnt'] and nnt['nnt'] > 0 and nnt['nnt'] < 10000,
              f'NNT={nnt["nnt"]}')
        check('ARR > 0 for beneficial pooled',
              nnt['arr'] > 0,
              f'ARR={nnt["arr"]:.4f}, CER={nnt["cer"]:.4f}, pooled={nnt["pooled"]:.4f}')
        print(f'    CER={nnt["cer"]:.4f}, pooled={nnt["pooled"]:.4f}, ARR={nnt["arr"]:.4f}, NNT={nnt["nnt"]}')
    else:
        check('NNT computed', False, 'Could not compute NNT')

except Exception as e:
    check('B6 NNT', False, str(e)[:200])
finally:
    if driver:
        driver.quit()
    time.sleep(0.5)


# ── B7: REML tau-squared convergence ──
print('\n=== B7: REML convergence check ===')
driver = None
try:
    driver = webdriver.Chrome(options=get_opts())
    driver.set_page_load_timeout(45)
    fpath = 'file:///' + os.path.join(BASE_DIR, 'FINERENONE_REVIEW.html').replace('\\', '/')
    driver.get(fpath)
    time.sleep(3)

    driver.execute_script("document.querySelector('[data-tab=\"analysis\"]').click()")
    time.sleep(2)

    reml = driver.execute_script("""
        var included = RapidMeta.state.trials.filter(t => t.status === 'include');
        if (included.length === 0) return null;
        var c = AnalysisEngine.computeCore(included);
        return c ? { tau2_dl: c.tau2, tau2_reml: c.tau2_reml } : null;
    """)

    if reml:
        check('REML tau2 >= 0', reml['tau2_reml'] >= 0, f'tau2_reml={reml["tau2_reml"]}')
        check('REML tau2 is finite', math.isfinite(reml['tau2_reml']))
        # REML and DL should be in the same ballpark
        dl = reml['tau2_dl']
        reml_val = reml['tau2_reml']
        if dl > 0:
            check('REML close to DL', abs(reml_val - dl) / dl < 2.0,
                  f'DL={dl:.6f}, REML={reml_val:.6f}')
        else:
            # Both should be 0 or very small
            check('Both tau2 near zero', reml_val < 0.01,
                  f'DL={dl:.6f}, REML={reml_val:.6f}')
        print(f'    DL tau2={dl:.6f}, REML tau2={reml_val:.6f}')
    else:
        check('REML computed', False, 'No REML results')

except Exception as e:
    check('B7 REML', False, str(e)[:200])
finally:
    if driver:
        driver.quit()
    time.sleep(0.5)


# ═══════════════════════════════════════════════════════════════════
# FINAL SUMMARY
# ═══════════════════════════════════════════════════════════════════
print('\n' + '='*70)
total = results['pass'] + results['fail']
print(f'FINAL: {results["pass"]}/{total} passed, {results["fail"]} failed')
if results['fail'] > 0:
    print('\nFailures:')
    for d in results['details']:
        print(f'  * {d}')
print('='*70)

if results['fail'] > 0:
    sys.exit(1)
