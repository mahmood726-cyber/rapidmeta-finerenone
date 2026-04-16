#!/usr/bin/env python
"""
Automated validation of all Living MA apps against published benchmarks.
Parses HTML files directly (no browser), extracts realData, pools via DL,
and compares against known published meta-analysis results.

Run: python validate_living_ma_portfolio.py [--json] [--strict]
"""
import sys, io, os, re, math, json, glob

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

# ═══════════════════════════════════════════════════════════
# PUBLISHED BENCHMARKS
# ═══════════════════════════════════════════════════════════

BENCHMARKS = {
    # Finrenone portfolio (original 18 apps)
    'FINERENONE':       {'est': 0.86, 'lo': 0.78, 'hi': 0.95, 'measure': 'HR', 'src': 'FIDELITY (Agarwal 2022)'},
    'BEMPEDOIC_ACID':   {'est': 0.87, 'lo': 0.79, 'hi': 0.96, 'measure': 'HR', 'src': 'CLEAR (Nissen 2023)'},
    'GLP1_CVOT':        {'est': 0.88, 'lo': 0.84, 'hi': 0.94, 'measure': 'HR', 'src': 'Sattar 2021 IPD'},
    'SGLT2_HF':         {'est': 0.77, 'lo': 0.71, 'hi': 0.84, 'measure': 'HR', 'src': 'Vaduganathan 2022'},
    'PCSK9':            {'est': 0.85, 'lo': 0.79, 'hi': 0.92, 'measure': 'HR', 'src': 'Guedeney 2020'},
    'SGLT2_CKD':        {'est': 0.68, 'lo': 0.60, 'hi': 0.77, 'measure': 'HR', 'src': 'CREDENCE+DAPA-CKD+EMPA-KIDNEY'},
    'ARNI_HF':          {'est': 0.84, 'lo': 0.77, 'hi': 0.91, 'measure': 'HR', 'src': 'PARADIGM+PARAGON+PARADISE'},
    'ABLATION_AF':      {'est': 0.77, 'lo': 0.64, 'hi': 0.93, 'measure': 'HR', 'src': 'CASTLE-AF+CABANA+EAST+RAFT'},
    'IV_IRON_HF':       {'est': 0.84, 'lo': 0.74, 'hi': 0.96, 'measure': 'HR', 'src': 'CONFIRM+AFFIRM+IRONMAN+HEART-FID'},
    'COLCHICINE_CVD':   {'est': 0.85, 'lo': 0.74, 'hi': 0.97, 'measure': 'HR', 'src': 'Updated 5-trial pool: COLCOT+LoDoCo2+COPS+CLEAR-SYNERGY+CONVINCE'},
    'RIVAROXABAN_VASC': {'est': 0.85, 'lo': 0.77, 'hi': 0.94, 'measure': 'HR', 'src': 'COMPASS+VOYAGER+ATLAS'},
    'ATTR_CM':          {'est': 0.71, 'lo': 0.59, 'hi': 0.86, 'measure': 'HR', 'src': 'ATTR-ACT+ATTRibute+HELIOS-B + APOLLO-B Peto (4-trial DL)'},
    'INTENSIVE_BP':     {'est': 0.79, 'lo': 0.71, 'hi': 0.87, 'measure': 'HR', 'src': '5-trial DL: SPRINT-SENIOR/CKD strata + ACCORD-BP+STEP+SPS3'},
    'INCRETIN_HFpEF':   {'est': 0.41, 'lo': 0.22, 'hi': 0.79, 'measure': 'HR', 'src': 'Internal DL: SUMMIT (Cox) + STEP-HFpEF/DM (Peto)'},
    'DOAC_CANCER_VTE':  {'est': 0.55, 'lo': 0.30, 'hi': 1.00, 'measure': 'HR', 'src': 'HOKUSAI+SELECT-D+ADAM+CARAVAGGIO'},
    'LIPID_HUB':        {'est': 0.89, 'lo': 0.76, 'hi': 1.04, 'measure': 'HR', 'src': '5-trial DL: REDUCE-IT+STRENGTH+VITAL+OMEMI+RESPECT-EPA (high heterogeneity I^2~78%)'},
    'MAVACAMTEN_HCM':   {'est': 6.67, 'lo': 2.09, 'hi': 21.30, 'measure': 'OR', 'src': 'EXPLORER+VALOR+China-Phase3 (NYHA improvement)'},
    # RENAL_DENERV: continuous-MD outcome, not poolable by this Python validator (handled in HTML JS engine).
    # New LivingMeta apps
    'OMECAMTIV':        {'est': 0.92, 'lo': 0.86, 'hi': 0.99, 'measure': 'HR', 'src': 'GALACTIC-HF+COSMIC-HF'},
    'SOTAGLIFLOZIN':    {'est': 0.72, 'lo': 0.62, 'hi': 0.83, 'measure': 'HR', 'src': 'SOLOIST+SCORED'},
    'TEZEPELUMAB_ASTHMA': {'est': 0.44, 'lo': 0.36, 'hi': 0.54, 'measure': 'RR', 'src': 'NAVIGATOR+PATHWAY+SOURCE'},
    'SOTATERCEPT_PAH':  {'est': 0.20, 'lo': 0.13, 'hi': 0.31, 'measure': 'HR', 'src': 'STELLAR+HYPERION+ZENITH'},
    'DUPILUMAB_COPD':   {'est': 0.70, 'lo': 0.58, 'hi': 0.86, 'measure': 'RR', 'src': 'BOREAS+NOTUS'},
    'PEMBRO_ADJ_MEL':   {'est': 0.64, 'lo': 0.50, 'hi': 0.84, 'measure': 'HR', 'src': 'KEYNOTE-054+716'},
    'OSIMERTINIB_NSCLC': {'est': 0.38, 'lo': 0.26, 'hi': 0.56, 'measure': 'HR', 'src': 'FLAURA+ADAURA+FLAURA-2'},
    'ENFORTUMAB_UC':    {'est': 0.55, 'lo': 0.43, 'hi': 0.70, 'measure': 'HR', 'src': 'EV-301+EV-302'},
    'KRAS_G12C_NSCLC':  {'est': 0.64, 'lo': 0.52, 'hi': 0.78, 'measure': 'HR', 'src': 'CodeBreaK 200+KRYSTAL-12'},
    'INCLISIRAN':       {'est': 0.80, 'lo': 0.50, 'hi': 1.27, 'measure': 'HR', 'src': 'ORION-4'},
    'ANTIPLATELET_NMA': {'est': 0.70, 'lo': 0.57, 'hi': 0.85, 'measure': 'HR', 'src': 'HOST-EXAM+TICO+TWILIGHT'},
    'VERICIGUAT':       {'est': 0.90, 'lo': 0.82, 'hi': 0.98, 'measure': 'HR', 'src': 'VICTORIA'},
}


# ═══════════════════════════════════════════════════════════
# PARSING & POOLING
# ═══════════════════════════════════════════════════════════

def extract_real_data(html):
    """Extract realData JS object from HTML. Handles both v16 multi-line and original single-line formats."""
    # Find the realData block
    m = re.search(r'realData:\s*\{(.*?)\n\s{8,12}\},', html, re.DOTALL)
    if not m:
        return {}
    block = m.group(1)
    trials = {}

    # Match NCT, ACTRN, ISRCTN, ChiCTR, EUCTR, JPRN registry IDs with optional suffix.
    # Suffixes like _SENIOR/_CKD/_ON/_OFF appear for stratified subgroups of a single parent trial.
    trial_id_pattern = r"'((?:NCT|ACTRN|ISRCTN|ChiCTR|EUCTR|JPRN)[A-Z0-9_-]+)':\s*\{"
    nct_starts = [(tm.start(), tm.group(1)) for tm in re.finditer(trial_id_pattern, block)]
    if not nct_starts:
        return {}

    for i, (start, nct) in enumerate(nct_starts):
        # Body extends from this NCT to next NCT (or end of block)
        end = nct_starts[i + 1][0] if i + 1 < len(nct_starts) else len(block)
        body = block[start:end]
        d = {}
        for field in ['tE', 'tN', 'cE', 'cN', 'publishedHR', 'hrLCI', 'hrUCI']:
            # Match field followed by number or null
            fm = re.search(rf'\b{field}:\s*([-\d.]+|null)', body)
            if fm and fm.group(1) != 'null':
                try:
                    d[field] = float(fm.group(1))
                except ValueError:
                    pass
        nm = re.search(r"name:\s*['\"]([^'\"]+)['\"]", body)
        if nm:
            d['name'] = nm.group(1)
        trials[nct] = d
    return trials


def pool_dl(trials):
    """DerSimonian-Laird pooling on log scale. Returns dict or None."""
    data = []
    for nct, t in trials.items():
        if t.get('publishedHR') and t.get('hrLCI') and t.get('hrUCI'):
            hr, lo, hi = t['publishedHR'], t['hrLCI'], t['hrUCI']
            if hr > 0 and lo > 0 and hi > 0:
                logHR = math.log(hr)
                se = (math.log(hi) - math.log(lo)) / (2 * 1.96)
                if se > 0:
                    data.append((logHR, se, t.get('name', nct)))
        elif t.get('tE') is not None and t.get('tN') and t.get('cN'):
            tE = int(t.get('tE', 0))
            tN = int(t.get('tN', 0))
            cE = int(t.get('cE', 0))
            cN = int(t.get('cN', 0))
            if tN > 0 and cN > 0 and (tE > 0 or cE > 0):
                adj = 0.5 if (tE == 0 or cE == 0 or tE == tN or cE == cN) else 0
                a, b, c, d2 = tE + adj, tN - tE + adj, cE + adj, cN - cE + adj
                if a > 0 and b > 0 and c > 0 and d2 > 0:
                    logOR = math.log((a / b) / (c / d2))
                    vi = 1 / a + 1 / b + 1 / c + 1 / d2
                    data.append((logOR, math.sqrt(vi), t.get('name', '')))

    if len(data) < 2:
        if len(data) == 1:
            return {'k': 1, 'est': round(math.exp(data[0][0]), 2),
                    'lo': None, 'hi': None, 'i2': 0, 'single': True}
        return None

    k = len(data)
    sW = sum(1 / (s ** 2) for _, s, _ in data)
    sWY = sum(y / (s ** 2) for y, s, _ in data)
    sWY2 = sum(y ** 2 / (s ** 2) for y, s, _ in data)
    sW2 = sum(1 / (s ** 4) for _, s, _ in data)

    Q = max(0, sWY2 - sWY ** 2 / sW)
    df = k - 1
    tau2 = max(0, (Q - df) / (sW - sW2 / sW)) if Q > df else 0

    sWR = sum(1 / (s ** 2 + tau2) for _, s, _ in data)
    sWRY = sum(y / (s ** 2 + tau2) for y, s, _ in data)
    pooled_log = sWRY / sWR if sWR > 0 else 0
    pooled_se = math.sqrt(1 / sWR) if sWR > 0 else 1

    est = math.exp(pooled_log)
    lo = math.exp(pooled_log - 1.96 * pooled_se)
    hi = math.exp(pooled_log + 1.96 * pooled_se)
    i2 = ((Q - df) / Q) * 100 if Q > df else 0

    return {'k': k, 'est': round(est, 2), 'lo': round(lo, 2), 'hi': round(hi, 2), 'i2': round(i2, 1)}


def check_dose_response(html):
    """Check if DR_CONFIG is populated (not null)."""
    return bool(re.search(r'const DR_CONFIG = \{', html))


# ═══════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════

def find_all_apps(local_only=False):
    """Find all living MA HTML files. If local_only, only the current directory."""
    apps = []
    if local_only:
        here = os.path.dirname(os.path.abspath(__file__))
        for f in sorted(glob.glob(os.path.join(here, '*_REVIEW.html'))):
            name = os.path.basename(f).replace('_REVIEW.html', '')
            apps.append((f, name))
        return apps

    # Finrenone dir + sibling LivingMeta dirs (override roots via env vars)
    finrenone_dir = os.environ.get('LIVINGMA_FINRENONE_DIR', here)
    portfolio_root = os.environ.get('LIVINGMA_PORTFOLIO_ROOT', os.path.dirname(finrenone_dir))
    for f in sorted(glob.glob(os.path.join(finrenone_dir, '*_REVIEW.html'))):
        name = os.path.basename(f).replace('_REVIEW.html', '')
        apps.append((f, name))
    # LivingMeta dirs
    if os.path.isdir(portfolio_root):
        for d in sorted(os.listdir(portfolio_root)):
            full = os.path.join(portfolio_root, d)
            if not os.path.isdir(full):
                continue
            if not (d.endswith('_LivingMeta') or d.startswith('LivingMeta_')):
                continue
            for f in os.listdir(full):
                if f.endswith('_REVIEW.html'):
                    apps.append((os.path.join(full, f), f.replace('_REVIEW.html', '')))
    return apps


if __name__ == '__main__':
    output_json = '--json' in sys.argv
    strict = '--strict' in sys.argv
    local_only = '--local' in sys.argv

    apps = find_all_apps(local_only=local_only)
    results = []
    benchmarked = 0
    matched = 0

    if not output_json:
        print(f"{'App':30s} {'k':>3s}  {'Pooled':>7s} {'CI':>16s} {'I2':>5s}  {'Bench':>7s} {'Diff':>6s}  {'Status':>6s}  DR")
        print('-' * 105)

    for path, name in sorted(apps, key=lambda x: x[1]):
        html = open(path, encoding='utf-8').read()
        trials = extract_real_data(html)
        pool = pool_dl(trials)
        has_dr = check_dose_response(html)
        bench = BENCHMARKS.get(name)

        entry = {
            'name': name,
            'path': path,
            'trial_count': len(trials),
            'dose_response': has_dr,
        }

        if pool:
            entry['k'] = pool['k']
            entry['est'] = pool['est']
            entry['lo'] = pool.get('lo')
            entry['hi'] = pool.get('hi')
            entry['i2'] = pool.get('i2', 0)
            entry['single'] = pool.get('single', False)

            if bench:
                diff = abs(pool['est'] - bench['est']) / bench['est'] * 100
                ok = diff <= 10.01  # inclusive threshold with float tolerance
                entry['benchmark'] = bench['est']
                entry['diff_pct'] = round(diff, 1)
                entry['match'] = ok
                benchmarked += 1
                if ok:
                    matched += 1
                status = 'OK' if ok else '~' if diff < 20 else 'X'
            else:
                status = '--'
                diff = None

            if not output_json:
                ci = f"({pool.get('lo', '--')}-{pool.get('hi', '--')})" if not pool.get('single') else '(single)'
                bench_str = f"{bench['est']:.2f}" if bench else '--'
                diff_str = f"{diff:.1f}%" if diff is not None else '--'
                dr_str = 'DR' if has_dr else ''
                print(f"{name:30s} {pool['k']:3d}  {pool['est']:7.2f} {ci:>16s} {pool.get('i2', 0):5.1f}  {bench_str:>7s} {diff_str:>6s}  {status:>6s}  {dr_str}")
        else:
            entry['k'] = 0
            if not output_json:
                poolable = sum(1 for t in trials.values() if (t.get('publishedHR') or (t.get('tE', 0) > 0 or t.get('cE', 0) > 0)) and t.get('tN', 0) > 0)
                dr_str = 'DR' if has_dr else ''
                print(f"{name:30s}   0  {'--':>7s} {f'{poolable}/{len(trials)} poolable':>16s} {'--':>5s}  {'--':>7s} {'--':>6s}  {'--':>6s}  {dr_str}")

        results.append(entry)

    if output_json:
        print(json.dumps(results, indent=2))
    else:
        print(f"\n{'=' * 60}")
        print(f"PORTFOLIO VALIDATION SUMMARY")
        print(f"{'=' * 60}")
        print(f"  Total apps:          {len(results)}")
        print(f"  With pooled results: {sum(1 for r in results if r.get('k', 0) >= 2)}")
        print(f"  Single-trial:        {sum(1 for r in results if r.get('single'))}")
        print(f"  Non-poolable:        {sum(1 for r in results if r.get('k', 0) == 0)}")
        print(f"  Dose-response:       {sum(1 for r in results if r.get('dose_response'))}")
        print(f"  Benchmarked:         {benchmarked}")
        print(f"  Within 10%:          {matched}/{benchmarked}")
        if strict and matched < benchmarked:
            sys.exit(1)
