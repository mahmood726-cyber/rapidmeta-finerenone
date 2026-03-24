"""
cross_validate_dashboard.py — Verify META_DASHBOARD.html hardcoded values
match each app's actual computed synthesis results.

For each DRUG_CLASSES entry in the dashboard, this script:
  1. Parses the hardcoded values (hr, lci, uci, k, n, i2, grade, nnt)
  2. Opens the corresponding app in headless Chrome
  3. Triggers synthesis (init -> force-seed if v11 -> switchTab -> AnalysisEngine.run)
  4. Extracts the actual computed values from RapidMeta.state.results
  5. Compares dashboard vs app, flagging discrepancies > 1%

Run:  python cross_validate_dashboard.py
"""
import sys
import io
import os
import re
import time
import json
import traceback

# UTF-8 stdout for Windows cp1252 safety
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

from selenium import webdriver
from selenium.webdriver.chrome.options import Options

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DASHBOARD_FILE = os.path.join(BASE_DIR, 'META_DASHBOARD.html')

# v11 apps that need force-seeding of canonical trials from realData
V11_APPS = {'COLCHICINE_CVD_REVIEW.html', 'GLP1_CVOT_REVIEW.html', 'SGLT2_HF_REVIEW.html'}

# Tolerance for numeric comparison (percentage)
TOLERANCE_PCT = 1.0


# ── Parse DRUG_CLASSES from META_DASHBOARD.html ────────────────────────────
def parse_drug_classes(html_path):
    """Extract all DRUG_CLASSES entries from the dashboard HTML using regex."""
    with open(html_path, 'r', encoding='utf-8') as f:
        text = f.read()

    # Find the DRUG_CLASSES array block
    m = re.search(r'const\s+DRUG_CLASSES\s*=\s*\[', text)
    if not m:
        print('ERROR: Could not find DRUG_CLASSES in dashboard HTML.')
        return []

    start = m.start()
    # Find the matching closing bracket by counting brackets
    depth = 0
    idx = text.index('[', start)
    for i in range(idx, len(text)):
        if text[i] == '[':
            depth += 1
        elif text[i] == ']':
            depth -= 1
            if depth == 0:
                block = text[idx:i + 1]
                break
    else:
        print('ERROR: Could not find closing bracket for DRUG_CLASSES.')
        return []

    # Parse each object entry from the JS array
    # We use regex to find each { ... } object block
    entries = []
    obj_pattern = re.compile(r'\{([^{}]+)\}', re.DOTALL)
    for obj_match in obj_pattern.finditer(block):
        body = obj_match.group(1)
        entry = {}

        # Extract string fields
        for field in ('name', 'file', 'indication', 'source', 'area', 'grade', 'color', 'unit'):
            m2 = re.search(rf"{field}\s*:\s*'([^']*)'", body)
            if m2:
                entry[field] = m2.group(1)

        # Extract numeric fields (including negative values)
        for field in ('hr', 'lci', 'uci', 'k', 'n', 'i2', 'nnt'):
            m2 = re.search(rf'{field}\s*:\s*(-?[\d.]+)', body)
            if m2:
                val = m2.group(1)
                entry[field] = float(val) if '.' in val else int(val)
            else:
                # Check for null
                m_null = re.search(rf'{field}\s*:\s*null', body)
                if m_null:
                    entry[field] = None

        # Extract boolean flags
        for flag in ('isOR', 'isMD'):
            m2 = re.search(rf'{flag}\s*:\s*true', body)
            if m2:
                entry[flag] = True

        if 'name' in entry and 'file' in entry:
            entries.append(entry)

    return entries


# ── Chrome driver factory ──────────────────────────────────────────────────
def make_driver():
    """Create a fresh headless Chrome driver with console logging."""
    opts = Options()
    opts.add_argument('--headless=new')
    opts.add_argument('--no-sandbox')
    opts.add_argument('--disable-gpu')
    opts.add_argument('--disable-dev-shm-usage')
    opts.add_argument('--window-size=1920,1080')
    opts.set_capability('goog:loggingPrefs', {'browser': 'ALL'})
    d = webdriver.Chrome(options=opts)
    d.set_page_load_timeout(30)
    d.set_script_timeout(30)
    return d


def file_url(filename):
    path = os.path.join(BASE_DIR, filename).replace(os.sep, '/')
    return 'file:///' + path


# ── Wait helpers (from test_all_apps_comprehensive.py) ─────────────────────
def wait_for_init(driver, timeout=15):
    """Poll until RapidMeta.init() has completed.

    Tier 1: v12 apps with canonical trials already seeded.
    Tier 2: v11 apps where we force-seed from realData.
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

                // Tier 2: RapidMeta ready but trials not seeded (v11 apps)
                if (document.readyState === 'complete') {
                    return 2;
                }

                return 0;
            } catch(e) { return 0; }
        """)
        if ready == 1:
            return True
        if ready == 2:
            # Force-seed canonical trials from realData
            driver.execute_script("""
                try {
                    if (typeof RapidMeta.ensureCanonicalAnalysisSeed === 'function') {
                        RapidMeta.ensureCanonicalAnalysisSeed();
                        RapidMeta.save();
                        return;
                    }
                    if (RapidMeta.realData) {
                        var trials = RapidMeta.state.trials || [];
                        var existingIds = new Set(trials.map(function(t){ return t.id; }));
                        Object.keys(RapidMeta.realData).forEach(function(id) {
                            if (existingIds.has(id)) {
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


def wait_for_results(driver, timeout=8):
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


# ── Trigger synthesis and extract results ──────────────────────────────────
def run_synthesis_and_extract(driver):
    """Trigger synthesis via switchTab('analysis') + AnalysisEngine.run(),
    then extract the full results object.

    Returns a dict with keys: hr, lci, uci, k, n, i2, grade, nnt, isContinuous
    or a dict with key 'error'.
    """
    # Force outcome selection (handles multi-outcome apps)
    driver.execute_script("""
        try {
            if (typeof RapidMeta.setOutcome === 'function') {
                var outcome = RapidMeta.state.selectedOutcome || 'default';
                RapidMeta.setOutcome(outcome, { silent: true });
            }
            if (typeof RapidMeta.applyOutcomeScope === 'function') {
                RapidMeta.applyOutcomeScope(RapidMeta.state.selectedOutcome || 'default');
            }
            RapidMeta.switchTab('analysis');
        } catch(e) {
            console.error('switchTab error:', e);
        }
    """)
    time.sleep(3)

    # Wait for results
    wait_for_results(driver, timeout=8)

    # If still no results, force AnalysisEngine.run() directly
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
        time.sleep(3)
        wait_for_results(driver, timeout=6)

    # Extract the full results
    result = driver.execute_script("""
        try {
            var r = RapidMeta.state.results;
            if (!r) return { error: 'No results in RapidMeta.state.results' };

            // Parse pooled estimate: stored as 'or' (string "0.87") for HR/OR apps,
            // or as pOR (float) for continuous MD apps
            var hrRaw = r.or;
            var hr = (hrRaw != null) ? parseFloat(hrRaw) : null;
            var isCont = !!r.isContinuous;

            // lci/uci: string "0.79" in v12, float in ContinuousMDEngine
            var lci = (r.lci != null) ? parseFloat(r.lci) : null;
            var uci = (r.uci != null) ? parseFloat(r.uci) : null;

            // I2: stored as string "0.0" or float
            var i2 = (r.i2 != null) ? parseFloat(r.i2) : null;
            // Alias: I2 (some code paths use capital)
            if (i2 == null && r.I2 != null) i2 = parseFloat(r.I2);

            // k: integer
            var k = (r.k != null) ? parseInt(r.k) : null;

            // n: total patients, stored as string with commas like "13,026"
            var nStr = r.n || null;
            var nVal = null;
            if (nStr != null) {
                nVal = parseInt(String(nStr).replace(/,/g, ''));
                if (isNaN(nVal)) nVal = null;
            }

            // GRADE certainty
            var grade = r.gradeCertainty || null;

            // NNT: computed dynamically from average CER and pooled effect
            // We compute it the same way as updatePatientMode
            var nnt = null;
            try {
                var trials = RapidMeta.state.trials.filter(function(t) {
                    return t.status === 'include' && t.data && t.data.tN > 0;
                });
                if (trials.length > 0 && hr != null && !isCont) {
                    var avgCER = 0;
                    trials.forEach(function(t) {
                        avgCER += (t.data.cE || 0) / (t.data.cN || 1);
                    });
                    avgCER /= trials.length;

                    var emLabel = (typeof RapidMeta.emLabel === 'function')
                        ? RapidMeta.emLabel('short') : 'HR';

                    var ter = 0;
                    if (avgCER > 0) {
                        if (emLabel === 'HR') {
                            ter = 1 - Math.pow(1 - avgCER, hr);
                        } else if (emLabel === 'RR') {
                            ter = hr * avgCER;
                        } else {
                            // OR
                            ter = (hr * avgCER) / (1 - avgCER + hr * avgCER);
                        }
                    }
                    var ard = avgCER - ter;
                    if (ard > 1e-9) {
                        nnt = Math.ceil(1 / ard);
                    }
                }
            } catch(nntErr) {
                // NNT computation is best-effort
            }

            return {
                hr: hr,
                lci: lci,
                uci: uci,
                k: k,
                n: nVal,
                i2: i2,
                grade: grade,
                nnt: nnt,
                isContinuous: isCont
            };
        } catch(e) { return { error: e.message }; }
    """)

    return result


# ── Comparison logic ───────────────────────────────────────────────────────
def pct_diff(a, b):
    """Percentage difference between two values. Handles zero denominator."""
    if a is None or b is None:
        return None
    if a == 0 and b == 0:
        return 0.0
    denom = abs(b) if abs(b) > 1e-9 else abs(a)
    if denom < 1e-9:
        return 0.0 if abs(a - b) < 1e-9 else 999.0
    return abs(a - b) / denom * 100.0


def compare_entry(dash_entry, app_result):
    """Compare dashboard entry vs app synthesis result.

    Returns (status, detail_str, field_results).
    status: 'MATCH', 'MISMATCH', 'ERROR'
    field_results: list of (field, dash_val, app_val, pct, ok)
    """
    if app_result is None or 'error' in app_result:
        err = app_result.get('error', 'null result') if app_result else 'null'
        return 'ERROR', err, []

    fields = []
    mismatches = []
    is_continuous = dash_entry.get('isMD', False)
    is_or = dash_entry.get('isOR', False)

    # Effect label for display
    if is_continuous:
        effect_label = 'MD'
    elif is_or:
        effect_label = 'OR'
    else:
        effect_label = 'HR'

    # ── Compare numeric fields ──
    numeric_checks = [
        ('hr', dash_entry.get('hr'), app_result.get('hr'), effect_label),
        ('lci', dash_entry.get('lci'), app_result.get('lci'), 'LCI'),
        ('uci', dash_entry.get('uci'), app_result.get('uci'), 'UCI'),
        ('i2', dash_entry.get('i2'), app_result.get('i2'), 'I2'),
    ]

    for field, d_val, a_val, label in numeric_checks:
        if d_val is None and a_val is None:
            fields.append((label, d_val, a_val, 0.0, True))
            continue
        if d_val is None or a_val is None:
            fields.append((label, d_val, a_val, None, False))
            mismatches.append(f'{label}: dashboard={d_val} vs app={a_val}')
            continue

        # Round app value to same precision as dashboard
        if field in ('hr', 'lci', 'uci'):
            a_val_r = round(a_val, 2)
        elif field == 'i2':
            a_val_r = round(a_val, 1)
        else:
            a_val_r = a_val

        diff = pct_diff(d_val, a_val_r)
        ok = diff is not None and diff <= TOLERANCE_PCT
        fields.append((label, d_val, a_val_r, diff, ok))
        if not ok:
            mismatches.append(f'{label}: {d_val} vs {a_val_r} [{diff:.1f}%]')

    # ── Compare integer fields (exact match) ──
    int_checks = [
        ('k', dash_entry.get('k'), app_result.get('k')),
        ('n', dash_entry.get('n'), app_result.get('n')),
    ]

    for field, d_val, a_val in int_checks:
        if d_val is None and a_val is None:
            fields.append((field, d_val, a_val, 0.0, True))
            continue
        if d_val is None or a_val is None:
            fields.append((field, d_val, a_val, None, False))
            mismatches.append(f'{field}: dashboard={d_val} vs app={a_val}')
            continue
        ok = int(d_val) == int(a_val)
        diff = pct_diff(float(d_val), float(a_val))
        fields.append((field, d_val, a_val, diff, ok))
        if not ok:
            mismatches.append(f'{field}: {d_val} vs {a_val}')

    # ── Compare GRADE (string match, case-insensitive) ──
    d_grade = dash_entry.get('grade')
    a_grade = app_result.get('grade')
    if d_grade is not None and a_grade is not None:
        grade_ok = str(d_grade).upper().strip() == str(a_grade).upper().strip()
        fields.append(('grade', d_grade, a_grade, None, grade_ok))
        if not grade_ok:
            mismatches.append(f'grade: {d_grade} vs {a_grade}')
    elif d_grade is None and a_grade is None:
        fields.append(('grade', None, None, None, True))
    else:
        fields.append(('grade', d_grade, a_grade, None, d_grade is None))
        # Only flag if dashboard has a grade but app doesn't
        if d_grade is not None and a_grade is None:
            mismatches.append(f'grade: dashboard={d_grade} vs app=None')

    # ── Compare NNT (integer, exact match) ──
    d_nnt = dash_entry.get('nnt')
    a_nnt = app_result.get('nnt')
    if d_nnt is not None and a_nnt is not None:
        nnt_ok = int(d_nnt) == int(a_nnt)
        fields.append(('nnt', d_nnt, a_nnt, None, nnt_ok))
        if not nnt_ok:
            mismatches.append(f'nnt: {d_nnt} vs {a_nnt}')
    elif d_nnt is None and a_nnt is None:
        fields.append(('nnt', None, None, None, True))
    else:
        # NNT=null in dashboard means non-significant -> no NNT expected
        fields.append(('nnt', d_nnt, a_nnt, None, True))

    # ── Build result ──
    if mismatches:
        detail = '; '.join(mismatches)
        return 'MISMATCH', detail, fields
    else:
        d_hr = dash_entry.get('hr')
        a_hr = app_result.get('hr')
        d_k = dash_entry.get('k')
        a_k = app_result.get('k')
        d_i2 = dash_entry.get('i2')
        a_i2 = app_result.get('i2')
        hr_str = f'{effect_label} {d_hr} vs {round(a_hr, 2) if a_hr is not None else "?"}'
        k_str = f'k={d_k} vs {a_k}'
        i2_str = f'I2={d_i2} vs {round(a_i2, 1) if a_i2 is not None else "?"}'
        detail = f'{hr_str}, {k_str}, {i2_str}'
        return 'MATCH', detail, fields


# ── Validate one app ──────────────────────────────────────────────────────
def validate_app(dash_entry):
    """Open one app, trigger synthesis, extract and compare to dashboard values.

    Returns (status, detail, field_results).
    Uses a fresh Chrome driver to avoid session exhaustion.
    """
    html_file = dash_entry['file']
    html_path = os.path.join(BASE_DIR, html_file)

    if not os.path.exists(html_path):
        return 'ERROR', f'File not found: {html_file}', []

    driver = None
    try:
        driver = make_driver()

        # Load the app
        driver.get(file_url(html_file))
        time.sleep(3)

        # Wait for RapidMeta init (handles v11 force-seeding)
        init_ok = wait_for_init(driver, timeout=15)
        if not init_ok:
            return 'ERROR', 'RapidMeta.init() did not complete in 15s', []

        # Check for fatal JS errors (excluding CDN/network)
        try:
            logs = driver.get_log('browser')
            severe = [m for m in logs if m.get('level') == 'SEVERE'
                      and not _is_cdn_error(m)]
            if severe:
                err_msgs = [s['message'][:100] for s in severe[:2]]
                return 'ERROR', f'{len(severe)} JS errors: {"; ".join(err_msgs)}', []
        except Exception:
            pass

        # Run synthesis and extract results
        app_result = run_synthesis_and_extract(driver)

        # Compare
        return compare_entry(dash_entry, app_result)

    except Exception as e:
        return 'ERROR', f'Exception: {str(e)[:150]}', []
    finally:
        if driver:
            try:
                driver.quit()
            except Exception:
                pass


def _is_cdn_error(msg):
    """Return True if the log entry is a CDN/network error we should skip."""
    text = msg.get('message', '').lower()
    skip = ['cdn.', 'cdnjs.', 'googleapis.com', 'fontawesome', 'unpkg.com',
            'plot.ly', 'plotly', 'tailwindcss', 'err_file_not_found',
            'net::err_', 'favicon.ico', 'failed to load resource',
            'failed to fetch', 'typeerror: failed to fetch',
            'pubmed', 'ct.gov', 'clinicaltrials.gov',
            'jstat', 'katex', 'webr', 'r-wasm', 'tailwind']
    return any(p in text for p in skip)


# ── Main ──────────────────────────────────────────────────────────────────
def main():
    print()
    print('Cross-Validation: META_DASHBOARD vs App Synthesis')
    print('=' * 60)
    print()

    # Step 1: Parse dashboard DRUG_CLASSES
    if not os.path.exists(DASHBOARD_FILE):
        print(f'ERROR: Dashboard file not found: {DASHBOARD_FILE}')
        return False

    drug_classes = parse_drug_classes(DASHBOARD_FILE)
    if not drug_classes:
        print('ERROR: No DRUG_CLASSES entries parsed from dashboard.')
        return False

    print(f'Parsed {len(drug_classes)} drug classes from META_DASHBOARD.html')
    print()

    # Step 2: Validate each app
    results = []
    match_count = 0
    mismatch_count = 0
    error_count = 0

    for i, entry in enumerate(drug_classes):
        name = entry.get('name', '?')
        html_file = entry.get('file', '?')
        short = html_file.replace('_REVIEW.html', '').replace('.html', '')

        print(f'[{i+1}/{len(drug_classes)}] {short} ({name})...')

        status, detail, field_results = validate_app(entry)

        if status == 'MATCH':
            marker = 'MATCH'
            match_count += 1
        elif status == 'MISMATCH':
            marker = 'MISMATCH'
            mismatch_count += 1
        else:
            marker = 'ERROR'
            error_count += 1

        print(f'  {short + ":":<22} {marker} ({detail})')
        results.append((short, name, status, detail, field_results))
        print()

    # Step 3: Summary
    total = len(results)
    print()
    print('=' * 60)
    print('SUMMARY')
    print('=' * 60)
    print()

    for short, name, status, detail, field_results in results:
        if status == 'MATCH':
            sym = '[OK]'
        elif status == 'MISMATCH':
            sym = '[!!]'
        else:
            sym = '[ERR]'
        print(f'  {sym} {short:<22} {detail[:70]}')

    print()
    print(f'  {match_count}/{total} MATCH, {mismatch_count}/{total} MISMATCH, {error_count}/{total} ERROR')
    print()

    # Step 4: Detailed mismatch report
    if mismatch_count > 0:
        print('=' * 60)
        print('MISMATCH DETAILS')
        print('=' * 60)
        for short, name, status, detail, field_results in results:
            if status != 'MISMATCH':
                continue
            print(f'\n  {short} ({name}):')
            for label, d_val, a_val, diff, ok in field_results:
                sym = 'OK' if ok else '!!'
                diff_str = f' [{diff:.1f}%]' if diff is not None and not ok else ''
                print(f'    [{sym}] {label:<8} dashboard={d_val}  app={a_val}{diff_str}')
        print()

    return mismatch_count == 0 and error_count == 0


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
