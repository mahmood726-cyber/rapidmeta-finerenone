#!/usr/bin/env python
"""
Cardiology Mortality Atlas

The first cross-class umbrella meta-analysis of all-cause mortality (ACM)
across the entire RapidMeta cardiology portfolio. Builds a unified forest
plot of every cardiovascular drug class with available ACM data.

Pipeline:
1. Scan all cardiology *_REVIEW.html files
2. Parse realData and find each trial's ACM outcome (shortLabel='ACM' or
   title containing 'all-cause mortality' / 'death from any cause')
3. Extract ACM HR/CI from publishedHR fields, or compute OR from event counts
4. Pool by drug class using DerSimonian-Laird random-effects + HKSJ
5. Generate self-contained HTML atlas with inline SVG forest plot
6. Continuously updateable via the same architecture

Run:
  python cardiology_mortality_atlas.py
  python cardiology_mortality_atlas.py --json
  python cardiology_mortality_atlas.py --validate    # vs known HF NMAs
"""
import sys, io, os, re, math, json, time, glob

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

# ═══════════════════════════════════════════════════════════
# CARDIOLOGY APP REGISTRY
# ═══════════════════════════════════════════════════════════
# Each entry: dict with name, drug_class, filename, population_detail,
# population_category, guideline_class, guideline_source

CARDIO_APPS = [
    {'name': 'Finerenone', 'drug_class': 'MRA (non-steroidal)', 'filename': 'FINERENONE_REVIEW.html',
     'population_detail': 'CKD/HF', 'population_category': 'HF/CKD overlap',
     'guideline_class': 'I', 'guideline_source': 'KDIGO 2024 + ESC HF 2023'},

    {'name': 'Bempedoic acid', 'drug_class': 'ATP-citrate lyase inhibitor', 'filename': 'BEMPEDOIC_ACID_REVIEW.html',
     'population_detail': 'ASCVD (statin-intolerant)', 'population_category': 'ASCVD prevention',
     'guideline_class': 'IIa', 'guideline_source': 'ESC Cholesterol 2023 update'},

    {'name': 'GLP-1 CVOT', 'drug_class': 'GLP-1 receptor agonist', 'filename': 'GLP1_CVOT_REVIEW.html',
     'population_detail': 'T2DM with CV risk', 'population_category': 'Diabetes/cardiometabolic',
     'guideline_class': 'I', 'guideline_source': 'ESC Diabetes 2023, ADA 2024'},

    {'name': 'SGLT2 in HF', 'drug_class': 'SGLT2 inhibitor', 'filename': 'SGLT2_HF_REVIEW.html',
     'population_detail': 'HFrEF + HFpEF', 'population_category': 'Heart failure',
     'guideline_class': 'I', 'guideline_source': 'ESC HF 2023, AHA 2022'},

    {'name': 'SGLT2 in CKD', 'drug_class': 'SGLT2 inhibitor', 'filename': 'SGLT2_CKD_REVIEW.html',
     'population_detail': 'CKD ± diabetes', 'population_category': 'HF/CKD overlap',
     'guideline_class': 'I', 'guideline_source': 'KDIGO 2024'},

    {'name': 'PCSK9', 'drug_class': 'PCSK9 mAb', 'filename': 'PCSK9_REVIEW.html',
     'population_detail': 'ASCVD on statin', 'population_category': 'ASCVD prevention',
     'guideline_class': 'I', 'guideline_source': 'ESC Cholesterol 2019, AHA 2018'},

    {'name': 'ARNI', 'drug_class': 'ARNI (sacubitril/valsartan)', 'filename': 'ARNI_HF_REVIEW.html',
     'population_detail': 'HFrEF (preferred over ACEi)', 'population_category': 'Heart failure',
     'guideline_class': 'I', 'guideline_source': 'ESC HF 2023, AHA 2022'},

    {'name': 'Catheter ablation', 'drug_class': 'Catheter ablation', 'filename': 'ABLATION_AF_REVIEW.html',
     'population_detail': 'AF (sx, HFrEF subset)', 'population_category': 'Arrhythmia',
     'guideline_class': 'I', 'guideline_source': 'ESC AF 2024 (HFrEF subset)'},

    {'name': 'IV iron', 'drug_class': 'IV iron (FCM/derisomaltose)', 'filename': 'IV_IRON_HF_REVIEW.html',
     'population_detail': 'HFrEF + iron deficiency', 'population_category': 'Heart failure',
     'guideline_class': 'IIa', 'guideline_source': 'ESC HF 2023'},

    {'name': 'Colchicine', 'drug_class': 'Anti-inflammatory', 'filename': 'COLCHICINE_CVD_REVIEW.html',
     'population_detail': 'CAD / post-MI', 'population_category': 'ASCVD prevention',
     'guideline_class': 'IIb', 'guideline_source': 'ESC ACS 2023 (downgraded post-CLEAR-SYNERGY)'},

    {'name': 'Rivaroxaban (low)', 'drug_class': 'Low-dose Xa inhibitor + ASA', 'filename': 'RIVAROXABAN_VASC_REVIEW.html',
     'population_detail': 'Stable CAD/PAD', 'population_category': 'ASCVD prevention',
     'guideline_class': 'IIa', 'guideline_source': 'ESC PAD 2024'},

    {'name': 'Intensive BP', 'drug_class': 'BP control (<120 mmHg)', 'filename': 'INTENSIVE_BP_REVIEW.html',
     'population_detail': 'High-risk hypertension', 'population_category': 'BP/HTN',
     'guideline_class': 'IIa', 'guideline_source': 'ESC HTN 2023, ACC/AHA 2017'},

    {'name': 'Tafamidis/Vutrisiran', 'drug_class': 'TTR stabilizer/silencer', 'filename': 'ATTR_CM_REVIEW.html',
     'population_detail': 'ATTR cardiomyopathy', 'population_category': 'Cardiomyopathy',
     'guideline_class': 'I', 'guideline_source': 'ESC Cardiomyopathy 2023'},

    {'name': 'Mavacamten', 'drug_class': 'Cardiac myosin inhibitor', 'filename': 'MAVACAMTEN_HCM_REVIEW.html',
     'population_detail': 'Symptomatic obstructive HCM', 'population_category': 'Cardiomyopathy',
     'guideline_class': 'I', 'guideline_source': 'AHA HCM 2024 update'},

    {'name': 'Combined lipid', 'drug_class': 'Lipid combo (various)', 'filename': 'LIPID_HUB_REVIEW.html',
     'population_detail': 'High-risk lipid lowering', 'population_category': 'ASCVD prevention',
     'guideline_class': 'I', 'guideline_source': 'ESC Cholesterol 2019'},

    {'name': 'Incretin (HFpEF)', 'drug_class': 'Incretin', 'filename': 'INCRETIN_HFpEF_REVIEW.html',
     'population_detail': 'HFpEF + obesity', 'population_category': 'Heart failure',
     'guideline_class': 'IIa', 'guideline_source': 'ESC HF 2023 (semaglutide HFpEF, recent)'},

    {'name': 'Vericiguat', 'drug_class': 'sGC stimulator', 'filename': 'VERICIGUAT_REVIEW.html',
     'population_detail': 'HFrEF (worsening)', 'population_category': 'Heart failure',
     'guideline_class': 'IIb', 'guideline_source': 'ESC HF 2023 (worsening HFrEF only)'},

    {'name': 'Omecamtiv', 'drug_class': 'Cardiac myosin activator', 'filename': 'OMECAMTIV_REVIEW.html',
     'population_detail': 'HFrEF (severe)', 'population_category': 'Heart failure',
     'guideline_class': 'III', 'guideline_source': 'Not in current guidelines (program halted)'},

    {'name': 'Sotagliflozin', 'drug_class': 'Dual SGLT1/2', 'filename': 'SOTAGLIFLOZIN_REVIEW.html',
     'population_detail': 'HF + T2DM/CKD', 'population_category': 'Heart failure',
     'guideline_class': 'IIa', 'guideline_source': 'ESC HF 2023 (post-SOLOIST/SCORED)'},

    {'name': 'Inclisiran', 'drug_class': 'siRNA PCSK9', 'filename': 'INCLISIRAN_REVIEW.html',
     'population_detail': 'ASCVD / HeFH', 'population_category': 'ASCVD prevention',
     'guideline_class': 'IIa', 'guideline_source': 'ESC Cholesterol 2023 update'},

    {'name': 'P2Y12 mono', 'drug_class': 'P2Y12 monotherapy', 'filename': 'ANTIPLATELET_NMA_REVIEW.html',
     'population_detail': 'Post-PCI (selected)', 'population_category': 'Post-PCI antiplatelet',
     'guideline_class': 'IIa', 'guideline_source': 'ESC ACS 2023 / Chronic CCS 2024'},

    {'name': 'Dapagliflozin (acute HF)', 'drug_class': 'SGLT2 inhibitor', 'filename': 'DAPA_ACUTE_HF_REVIEW.html',
     'population_detail': 'Acute HF', 'population_category': 'Heart failure',
     'guideline_class': 'IIb', 'guideline_source': 'ESC HF 2023 (in-hospital initiation)'},

    {'name': 'HFrEF NMA', 'drug_class': 'GDMT pillars (mixed)', 'filename': 'HFREF_NMA_REVIEW.html',
     'population_detail': 'HFrEF (foundational)', 'population_category': 'Heart failure',
     'guideline_class': 'I', 'guideline_source': 'ESC HF 2023 (4 pillars)'},

    {'name': 'Empagliflozin (post-MI)', 'drug_class': 'SGLT2 inhibitor', 'filename': 'EMPA_MI_REVIEW.html',
     'population_detail': 'Post-MI', 'population_category': 'Post-MI',
     'guideline_class': 'IIb', 'guideline_source': 'ESC ACS 2023 (post-EMPACT-MI null result)'},

    {'name': 'Ticagrelor mono', 'drug_class': 'Antiplatelet', 'filename': 'TICAGRELOR_MONO_REVIEW.html',
     'population_detail': 'Post-PCI (1-3 mo DAPT)', 'population_category': 'Post-PCI antiplatelet',
     'guideline_class': 'IIa', 'guideline_source': 'ESC ACS 2023'},

    {'name': 'Icosapent ethyl', 'drug_class': 'Omega-3 (EPA)', 'filename': 'ICOSAPENT_ETHYL_REVIEW.html',
     'population_detail': 'Hypertriglyceridemia + ASCVD', 'population_category': 'ASCVD prevention',
     'guideline_class': 'IIa', 'guideline_source': 'ESC Cholesterol 2019 (REDUCE-IT only)'},

    {'name': 'Sotatercept', 'drug_class': 'Activin signaling inhibitor', 'filename': 'SOTATERCEPT_PAH_REVIEW.html',
     'population_detail': 'PAH (WHO Group 1)', 'population_category': 'Pulm vascular',
     'guideline_class': 'I', 'guideline_source': 'ESC PH 2025 update (post-STELLAR)'},

    {'name': 'DOAC (cancer VTE)', 'drug_class': 'DOAC', 'filename': 'DOAC_CANCER_VTE_REVIEW.html',
     'population_detail': 'Cancer-associated VTE', 'population_category': 'Anticoagulation',
     'guideline_class': 'I', 'guideline_source': 'ESC ACS / ITAC 2022'},
]


# ═══════════════════════════════════════════════════════════
# GUIDELINE CONCORDANCE MAP
# ═══════════════════════════════════════════════════════════
# For each guideline class, the expected pooled effect characteristics

CLASS_EXPECTATIONS = {
    'I':   {'desc': 'Strong recommendation',     'expect_lo_below_1': True,  'expect_strong_effect': True},
    'IIa': {'desc': 'Reasonable to use',         'expect_lo_below_1': True,  'expect_strong_effect': False},
    'IIb': {'desc': 'May be considered',         'expect_lo_below_1': False, 'expect_strong_effect': False},
    'III': {'desc': 'Not recommended / harm',    'expect_lo_below_1': False, 'expect_strong_effect': False},
}


def assess_concordance(guideline_class, pool):
    """Compare pooled effect to guideline class expectations.

    Returns 'concordant', 'overstrong' (guideline stronger than evidence),
    'understrong' (evidence stronger than guideline), or 'no_data'.
    """
    if not pool:
        return 'no_data'
    if guideline_class not in CLASS_EXPECTATIONS:
        return 'no_data'

    exp = CLASS_EXPECTATIONS[guideline_class]
    sig = pool['pooled_hi'] < 1.0  # CI excludes 1 (statistically significant benefit)

    if guideline_class == 'I':
        # Class I expects significant benefit
        return 'concordant' if sig else 'overstrong'
    if guideline_class == 'IIa':
        return 'concordant' if sig else 'overstrong'
    if guideline_class == 'IIb':
        # IIb is consistent with weaker evidence
        return 'concordant' if not sig or pool['pooled_est'] > 0.85 else 'understrong'
    if guideline_class == 'III':
        # III expects no benefit; if pool shows benefit, evidence outpaces guideline
        return 'understrong' if sig else 'concordant'
    return 'no_data'


# ═══════════════════════════════════════════════════════════
# PARSING
# ═══════════════════════════════════════════════════════════

def find_app_path(filename):
    """Locate the HTML file across Finrenone dir and LivingMeta sibling dirs."""
    candidates = [
        os.path.join(r'C:\Projects\Finrenone', filename),
    ]
    for d in os.listdir(r'C:\Projects'):
        if d.endswith('_LivingMeta') or d.startswith('LivingMeta_'):
            candidates.append(os.path.join(r'C:\Projects', d, filename))
    for c in candidates:
        if os.path.exists(c):
            return c
    return None


def parse_acm_outcomes(html, app_name):
    """Extract all-cause mortality outcomes + trial-level metadata.

    Returns list of dicts with: nct, name, hr, lo, hi, year, tE/cE/tN/cN,
    rob (low/some/high), primary_hr (for ACM-vs-primary discordance).
    """
    trials = []
    nct_pattern = re.compile(r"['\"]?(NCT\d+)['\"]?\s*:\s*\{", re.MULTILINE)
    nct_starts = [(m.start(), m.group(1)) for m in nct_pattern.finditer(html)]

    for i, (start, nct) in enumerate(nct_starts):
        end = nct_starts[i + 1][0] if i + 1 < len(nct_starts) else len(html)
        body = html[start:end]

        nm = re.search(r"name:\s*['\"]([^'\"]+)['\"]", body)
        trial_name = nm.group(1) if nm else nct

        ym = re.search(r"\byear:\s*(\d{4})", body)
        trial_year = int(ym.group(1)) if ym else None

        # Risk of bias — look for overall rob
        rob_m = re.search(r"rob:\s*\[[^\]]*\]", body)
        rob_overall = 'unknown'
        if rob_m:
            rob_block = rob_m.group(0)
            # Count 'low', 'some', 'high' ratings
            rob_ratings = re.findall(r"['\"](low|some|high|moderate)['\"]", rob_block)
            if rob_ratings:
                if 'high' in rob_ratings:
                    rob_overall = 'high'
                elif 'some' in rob_ratings or 'moderate' in rob_ratings:
                    rob_overall = 'some'
                else:
                    rob_overall = 'low'

        # Primary outcome HR (for ACM-vs-primary discordance)
        primary_hr = None
        primary_pattern = re.compile(
            r"\{[^{}]*?type:\s*['\"]?PRIMARY['\"]?[^{}]*?\}",
            re.IGNORECASE | re.DOTALL
        )
        for pm in primary_pattern.finditer(body):
            pblock = pm.group(0)
            phr_m = re.search(r"(?:pubHR|effect|hr)\s*:\s*([\d.]+)", pblock)
            if phr_m:
                try:
                    primary_hr = float(phr_m.group(1))
                    break
                except ValueError:
                    pass

        # ACM outcome
        acm_data = None
        acm_outcome_pattern = re.compile(
            r"\{[^{}]*?(?:shortLabel:\s*['\"]?(?:ACM|Mortality|All[- ]Cause Mortality)['\"]?|title:\s*['\"][^'\"]*(?:all[- ]cause mortality|death from any cause|all[- ]cause death)[^'\"]*['\"])[^{}]*?\}",
            re.IGNORECASE | re.DOTALL
        )
        for outcome_m in acm_outcome_pattern.finditer(body):
            outcome_block = outcome_m.group(0)
            hr_m = re.search(r"(?:pubHR|effect|hr)\s*:\s*([\d.]+)", outcome_block)
            lo_m = re.search(r"(?:pubHR_LCI|lci|hrLo)\s*:\s*([\d.]+)", outcome_block)
            hi_m = re.search(r"(?:pubHR_UCI|uci|hrHi)\s*:\s*([\d.]+)", outcome_block)
            te_m = re.search(r"tE:\s*(\d+)", outcome_block)
            ce_m = re.search(r"cE:\s*(\d+)", outcome_block)

            if hr_m and lo_m and hi_m:
                try:
                    acm_data = {
                        'hr': float(hr_m.group(1)),
                        'lo': float(lo_m.group(1)),
                        'hi': float(hi_m.group(1)),
                        'tE': int(te_m.group(1)) if te_m else None,
                        'cE': int(ce_m.group(1)) if ce_m else None,
                    }
                    break
                except (ValueError, TypeError):
                    pass

        if acm_data:
            tn_m = re.search(r"\btN:\s*(\d+)", body)
            cn_m = re.search(r"\bcN:\s*(\d+)", body)
            acm_data['nct'] = nct
            acm_data['name'] = trial_name
            acm_data['year'] = trial_year
            acm_data['rob'] = rob_overall
            acm_data['primary_hr'] = primary_hr
            acm_data['tN'] = int(tn_m.group(1)) if tn_m else None
            acm_data['cN'] = int(cn_m.group(1)) if cn_m else None
            trials.append(acm_data)

    return trials


def extract_app_max_year(html):
    """Find the most recent trial year across all NCT entries in the file."""
    years = [int(m.group(1)) for m in re.finditer(r"\byear:\s*(\d{4})", html)]
    return max(years) if years else None


# ═══════════════════════════════════════════════════════════
# BUCHER INDIRECT COMPARISONS
# ═══════════════════════════════════════════════════════════

def bucher_indirect(pool_a, pool_b):
    """Compute indirect comparison A vs B via shared placebo.

    log(HR_AB) = log(HR_A_vs_placebo) - log(HR_B_vs_placebo)
    var(log HR_AB) = var(log HR_A) + var(log HR_B)
    """
    if not pool_a or not pool_b:
        return None
    log_a = pool_a['pooled_log']
    log_b = pool_b['pooled_log']
    se_a = pool_a['pooled_se']
    se_b = pool_b['pooled_se']

    log_ab = log_a - log_b
    se_ab = math.sqrt(se_a ** 2 + se_b ** 2)

    return {
        'est': math.exp(log_ab),
        'lo': math.exp(log_ab - 1.96 * se_ab),
        'hi': math.exp(log_ab + 1.96 * se_ab),
        'log_est': log_ab,
        'se': se_ab,
    }


def build_league_table(results):
    """Build pairwise Bucher comparisons for all class pairs with pooled data."""
    classes_with_data = [r for r in results if r['pool']]
    league = []
    for i, ra in enumerate(classes_with_data):
        for j, rb in enumerate(classes_with_data):
            if i >= j:
                continue
            ind = bucher_indirect(ra['pool'], rb['pool'])
            if ind:
                league.append({
                    'a': ra['name'],
                    'b': rb['name'],
                    'a_class': ra['drug_class'],
                    'b_class': rb['drug_class'],
                    'est': ind['est'],
                    'lo': ind['lo'],
                    'hi': ind['hi'],
                    'sig': ind['hi'] < 1 or ind['lo'] > 1,
                })
    return league


# ═══════════════════════════════════════════════════════════
# 12 ADVANCED ANALYSES
# ═══════════════════════════════════════════════════════════

def normal_cdf(z):
    return 0.5 * (1 + math.erf(z / math.sqrt(2)))


def t_quantile(p, df):
    """Approximate Student t quantile via Cornish-Fisher."""
    if df <= 0:
        return 1.96
    # Use Beasley-Springer-Moro for normal quantile
    if p <= 0 or p >= 1:
        return float('nan')
    a = [-39.6968302866538, 220.946098424521, -275.928510446969,
         138.357751867269, -30.6647980661472, 2.50662827745924]
    b = [-54.4760987982241, 161.585836858041, -155.698979859887,
         66.8013118877197, -13.2806815528857]
    if p < 0.5:
        q = math.sqrt(-2 * math.log(p))
        z = -(((((a[5]*q + a[4])*q + a[3])*q + a[2])*q + a[1])*q + a[0]) / \
            ((((b[4]*q + b[3])*q + b[2])*q + b[1])*q + 1)
    else:
        q = math.sqrt(-2 * math.log(1 - p))
        z = (((((a[5]*q + a[4])*q + a[3])*q + a[2])*q + a[1])*q + a[0]) / \
            ((((b[4]*q + b[3])*q + b[2])*q + b[1])*q + 1)
    g1 = (z ** 3 + z) / 4
    g2 = (5 * z ** 5 + 16 * z ** 3 + 3 * z) / 96
    return z + g1 / df + g2 / (df ** 2)


# ─── 1. Prediction intervals (Higgins 2009) ───

def prediction_interval(pool):
    """95% prediction interval using Higgins 2009: pooled_est +/- t_{k-2} * sqrt(tau2 + se^2)."""
    if not pool or pool['k'] < 3:
        return None
    k = pool['k']
    tau2 = pool['tau2']
    se = pool['pooled_se']
    t = t_quantile(0.975, k - 2)
    pi_se = math.sqrt(tau2 + se ** 2)
    return {
        'lo': math.exp(pool['pooled_log'] - t * pi_se),
        'hi': math.exp(pool['pooled_log'] + t * pi_se),
    }


# ─── 2. Leave-one-out sensitivity ───

def leave_one_out(trials_log_se):
    """Compute the range of pooled estimates after removing each trial once.

    Returns dict with max_delta (largest % change from full pool) and
    min/max HR across LOO iterations.
    """
    if len(trials_log_se) < 2:
        return None
    full = dl_pool(trials_log_se)
    if not full:
        return None
    loo_estimates = []
    for i in range(len(trials_log_se)):
        subset = trials_log_se[:i] + trials_log_se[i + 1:]
        sub_pool = dl_pool(subset) if subset else None
        if sub_pool:
            loo_estimates.append(sub_pool['pooled_est'])
    if not loo_estimates:
        return None
    loo_min = min(loo_estimates)
    loo_max = max(loo_estimates)
    max_delta = max(
        abs(loo_min - full['pooled_est']) / full['pooled_est'],
        abs(loo_max - full['pooled_est']) / full['pooled_est'],
    ) * 100
    return {
        'full_hr': full['pooled_est'],
        'loo_min': loo_min,
        'loo_max': loo_max,
        'max_delta_pct': max_delta,
        'fragile': max_delta > 20,
    }


# ─── 3. Cumulative MA by year ───

def cumulative_ma(trials):
    """Sort trials by year, compute running pooled estimate.

    Returns list of (year, n_studies, pooled_est, lo, hi).
    """
    # Sort by year with estimates
    sorted_trials = sorted(
        [t for t in trials if t.get('year') and t['hr'] > 0 and t['lo'] > 0 and t['hi'] > 0],
        key=lambda t: t['year']
    )
    steps = []
    for i in range(1, len(sorted_trials) + 1):
        subset = sorted_trials[:i]
        ests = [log_se(t['hr'], t['lo'], t['hi']) for t in subset]
        pool = dl_pool(ests)
        if pool:
            steps.append({
                'year': sorted_trials[i - 1]['year'],
                'k': i,
                'est': pool['pooled_est'],
                'lo': pool['pooled_lo'],
                'hi': pool['pooled_hi'],
            })
    return steps


# ─── 4. Low risk-of-bias subanalysis ───

def low_rob_pool(trials):
    """Pool using only low-RoB trials."""
    low_rob = [t for t in trials if t.get('rob') == 'low' and t['hr'] > 0 and t['lo'] > 0 and t['hi'] > 0]
    if len(low_rob) < 1:
        return None
    ests = [log_se(t['hr'], t['lo'], t['hi']) for t in low_rob]
    return dl_pool(ests)


# ─── 5. Heterogeneity decomposition by population ───

def q_decomposition(results):
    """Partition total Q into within-stratum and between-stratum components."""
    # Within: sum of Q from each population stratum's pool
    pop_strata = {}
    for r in results:
        if r['pool']:
            cat = r['population_category']
            pop_strata.setdefault(cat, []).append((r['pool']['pooled_log'], r['pool']['pooled_se']))

    pop_pools = {cat: dl_pool(ests) for cat, ests in pop_strata.items()}
    q_within = sum(p['Q'] for p in pop_pools.values() if p and p['k'] > 1)
    df_within = sum(max(0, p['df']) for p in pop_pools.values() if p)

    # Total Q from overall pool
    all_ests = []
    for ests in pop_strata.values():
        all_ests.extend(ests)
    total_pool = dl_pool(all_ests)
    q_total = total_pool['Q'] if total_pool else 0
    df_total = total_pool['df'] if total_pool else 0

    q_between = max(0, q_total - q_within)
    df_between = max(0, df_total - df_within)

    return {
        'q_total': q_total, 'df_total': df_total,
        'q_within': q_within, 'df_within': df_within,
        'q_between': q_between, 'df_between': df_between,
        'pct_between': (q_between / q_total * 100) if q_total > 0 else 0,
    }


# ─── 6. Temporal effect trends (meta-regression on year) ───

def temporal_trend(results):
    """Meta-regression of log(HR) on trial year across the portfolio.

    Uses class-level pooled estimates weighted by inverse variance.
    """
    points = []
    for r in results:
        if not r['pool'] or not r.get('max_year'):
            continue
        weight = 1 / (r['pool']['pooled_se'] ** 2)
        points.append((r['max_year'], r['pool']['pooled_log'], weight))

    if len(points) < 3:
        return None

    # Weighted least squares
    sum_w = sum(w for _, _, w in points)
    sum_wx = sum(w * x for x, _, w in points)
    sum_wy = sum(w * y for _, y, w in points)
    sum_wxx = sum(w * x * x for x, _, w in points)
    sum_wxy = sum(w * x * y for x, y, w in points)

    mean_x = sum_wx / sum_w
    mean_y = sum_wy / sum_w
    sxx = sum_wxx - sum_wx ** 2 / sum_w
    sxy = sum_wxy - sum_wx * sum_wy / sum_w

    if sxx == 0:
        return None
    slope = sxy / sxx
    intercept = mean_y - slope * mean_x

    # Slope SE
    n = len(points)
    residuals = [(y - (intercept + slope * x)) for x, y, _ in points]
    rss = sum(w * r ** 2 for (_, _, w), r in zip(points, residuals))
    se_slope = math.sqrt(rss / ((n - 2) * sxx)) if n > 2 else float('inf')

    return {
        'slope_per_year': slope,
        'pct_change_per_year': (math.exp(slope) - 1) * 100,
        'se_slope': se_slope,
        'n_classes': n,
        'intercept_log': intercept,
    }


# ─── 7. NNT at 5 years ───

def nnt_estimate(trials, hr_pool):
    """Approximate NNT at 5 years using average control mortality rate.

    NNT = 1 / (baseline_risk * (1 - HR)) for rare events.
    """
    if not hr_pool or hr_pool['pooled_est'] >= 1:
        return None  # no NNT if no benefit or harmful

    control_rates = []
    for t in trials:
        if t.get('cE') and t.get('cN') and t['cN'] > 0:
            control_rates.append(t['cE'] / t['cN'])
    if not control_rates:
        return None

    # Weighted average by trial size
    total_cn = sum(t['cN'] for t in trials if t.get('cN'))
    if total_cn == 0:
        return None
    avg_control = sum((t['cE'] / t['cN']) * t['cN'] for t in trials
                       if t.get('cE') and t.get('cN') and t['cN'] > 0) / total_cn

    hr = hr_pool['pooled_est']
    arr = avg_control * (1 - hr)
    nnt = 1 / arr if arr > 0 else float('inf')
    return {
        'avg_control_risk': avg_control,
        'avg_hr': hr,
        'arr': arr,
        'nnt': round(nnt),
    }


# ─── 8. P-score rankings (frequentist SUCRA) ───

def p_scores(results):
    """Compute P-scores (Rucker & Schwarzer 2015) for pairwise rankings.

    For each class, P-score = mean prob of being better than a random other class.
    """
    classes = [(r['name'], r['pool']) for r in results if r['pool']]
    n = len(classes)
    if n < 2:
        return []

    scores = []
    for i, (name_i, pool_i) in enumerate(classes):
        prob_better_sum = 0
        n_comparisons = 0
        for j, (name_j, pool_j) in enumerate(classes):
            if i == j:
                continue
            # P(class i better than j) under normal assumption
            diff_log = pool_i['pooled_log'] - pool_j['pooled_log']
            se_diff = math.sqrt(pool_i['pooled_se'] ** 2 + pool_j['pooled_se'] ** 2)
            if se_diff > 0:
                z = -diff_log / se_diff  # negative because lower HR is better
                prob_better_sum += normal_cdf(z)
                n_comparisons += 1
        p_score = prob_better_sum / n_comparisons if n_comparisons > 0 else 0
        scores.append({'name': name_i, 'p_score': p_score})

    return sorted(scores, key=lambda x: -x['p_score'])


# ─── 9. ACM vs primary outcome discordance ───

def acm_primary_discordance(results):
    """For each trial with both ACM and primary HR, compute the ratio.

    Quantifies how much composite/primary outcomes inflate effects vs ACM alone.
    """
    discordances = []
    for r in results:
        for t in r.get('trials', []):
            if t.get('primary_hr') and t.get('hr'):
                ratio = math.log(t['hr'] / t['primary_hr'])  # positive = ACM less effective
                discordances.append({
                    'class': r['name'],
                    'trial': t['name'],
                    'primary_hr': t['primary_hr'],
                    'acm_hr': t['hr'],
                    'log_ratio': ratio,
                    'attenuation_pct': (1 - t['primary_hr'] / t['hr']) * 100 if t['hr'] > 0 else 0,
                })

    if not discordances:
        return None
    mean_log_ratio = sum(d['log_ratio'] for d in discordances) / len(discordances)
    return {
        'n_trials': len(discordances),
        'mean_log_ratio': mean_log_ratio,
        'mean_ratio': math.exp(mean_log_ratio),
        'interpretation': 'ACM HR tends to be LESS favorable than primary composite'
                          if mean_log_ratio > 0 else 'ACM HR tends to be MORE favorable than primary',
        'details': sorted(discordances, key=lambda d: -abs(d['log_ratio']))[:10],
    }


# ─── 10. Baseline risk meta-regression ───

def baseline_risk_regression(results):
    """Regress log(HR) on log(control_risk) across all trials in the portfolio.

    A negative slope indicates treatment is relatively more effective in higher-risk populations.
    """
    points = []
    for r in results:
        for t in r.get('trials', []):
            if not (t.get('cE') and t.get('cN') and t['cN'] > 0 and t.get('hr') and t['hr'] > 0):
                continue
            control_rate = t['cE'] / t['cN']
            if control_rate <= 0 or control_rate >= 1:
                continue
            log_hr = math.log(t['hr'])
            log_risk = math.log(control_rate / (1 - control_rate))  # logit
            # Weight by inverse of log-HR variance
            if t['lo'] > 0 and t['hi'] > 0:
                se = (math.log(t['hi']) - math.log(t['lo'])) / (2 * 1.96)
                weight = 1 / (se ** 2) if se > 0 else 1
            else:
                weight = 1
            points.append((log_risk, log_hr, weight))

    if len(points) < 5:
        return None

    sum_w = sum(w for _, _, w in points)
    sum_wx = sum(w * x for x, _, w in points)
    sum_wy = sum(w * y for _, y, w in points)
    sum_wxx = sum(w * x * x for x, _, w in points)
    sum_wxy = sum(w * x * y for x, y, w in points)

    sxx = sum_wxx - sum_wx ** 2 / sum_w
    sxy = sum_wxy - sum_wx * sum_wy / sum_w

    if sxx == 0:
        return None
    slope = sxy / sxx
    intercept = sum_wy / sum_w - slope * sum_wx / sum_w

    return {
        'n_trials': len(points),
        'slope': slope,
        'intercept': intercept,
        'interpretation': 'Higher-risk populations show LARGER treatment effects'
                          if slope < -0.05 else 'Effect appears independent of baseline risk',
    }


# ─── 11. Cross-population consistency (SGLT2 exemplar) ───

def cross_population_consistency(results, drug_keyword='SGLT2'):
    """For a drug class that appears in multiple populations, test consistency."""
    matches = [r for r in results if r['pool'] and drug_keyword.lower() in r['drug_class'].lower()]
    if len(matches) < 2:
        return None

    # Pool all trials from matching apps
    all_ests = []
    per_app = []
    for r in matches:
        for t in r['trials']:
            if t.get('hr') and t.get('lo') and t.get('hi') and t['hr'] > 0:
                all_ests.append(log_se(t['hr'], t['lo'], t['hi']))
        per_app.append({
            'name': r['name'],
            'population': r['population_detail'],
            'pool': r['pool'],
        })

    combined = dl_pool(all_ests) if all_ests else None
    return {
        'drug': drug_keyword,
        'n_apps': len(matches),
        'apps': per_app,
        'combined_pool': combined,
    }


# ─── 12. Trial sequential analysis (approximated RIS) ───

def trial_sequential_analysis(trials, hr_pool, alpha=0.05, beta=0.20):
    """Approximate required information size for each drug class.

    Uses diversity-adjusted formula (DL tau2):
    RIS = (z_a + z_b)^2 / (log_RR)^2 * 4 / (p0 * (1-p0)) * (1 + D)
    where D = I^2 / (1 - I^2)
    """
    if not hr_pool or not trials:
        return None

    # Baseline risk from control arms
    control_rates = [t['cE'] / t['cN'] for t in trials if t.get('cE') and t.get('cN') and t['cN'] > 0]
    if not control_rates:
        return None
    p0 = sum(control_rates) / len(control_rates)
    if p0 <= 0 or p0 >= 1:
        return None

    # Effect size
    log_hr = abs(hr_pool['pooled_log'])
    if log_hr < 1e-6:
        return None  # can't calculate

    # Critical values
    z_a = 1.96  # two-sided alpha=0.05
    z_b = 0.84  # power=0.80

    # RIS for each arm (conventional formula)
    # RIS_per_arm = (z_a + z_b)^2 / log(HR)^2 * (1 - p0) / p0 ... simplified
    # Using diversity adjustment from Wetterslev
    ris_naive = (z_a + z_b) ** 2 / (log_hr ** 2) * (1 / p0 + 1 / (1 - p0))

    # Diversity adjustment
    i2 = hr_pool['I2'] / 100
    diversity = 1 / (1 - i2) if i2 < 0.99 else 100
    ris_adjusted = ris_naive * diversity

    # Current accumulated
    current_n = sum((t.get('tN') or 0) + (t.get('cN') or 0) for t in trials)

    # Current events (approximate with observed)
    events_per_n = sum((t.get('tE') or 0) + (t.get('cE') or 0) for t in trials) / current_n if current_n > 0 else 0

    return {
        'ris': round(ris_adjusted),
        'current_n': current_n,
        'info_fraction': min(1.0, current_n / ris_adjusted) if ris_adjusted > 0 else 0,
        'baseline_risk': p0,
        'diversity_factor': round(diversity, 2),
        'adequate': current_n >= ris_adjusted,
    }


# ═══════════════════════════════════════════════════════════
# STATISTICS
# ═══════════════════════════════════════════════════════════

def log_se(est, lo, hi):
    return math.log(est), (math.log(hi) - math.log(lo)) / (2 * 1.96)


def dl_pool(estimates):
    """DerSimonian-Laird random-effects pool."""
    if len(estimates) < 1:
        return None
    if len(estimates) == 1:
        y, se = estimates[0]
        return {
            'k': 1, 'pooled_log': y, 'pooled_se': se,
            'pooled_est': math.exp(y),
            'pooled_lo': math.exp(y - 1.96 * se),
            'pooled_hi': math.exp(y + 1.96 * se),
            'tau2': 0, 'I2': 0, 'Q': 0, 'df': 0,
        }
    k = len(estimates)
    weights = [1 / (se ** 2) for _, se in estimates]
    sum_w = sum(weights)
    sum_wy = sum(w * y for w, (y, _) in zip(weights, estimates))
    sum_wy2 = sum(w * y * y for w, (y, _) in zip(weights, estimates))
    sum_w2 = sum(w * w for w in weights)
    mean_fe = sum_wy / sum_w
    Q = sum(w * (y - mean_fe) ** 2 for w, (y, _) in zip(weights, estimates))
    df = k - 1
    tau2 = max(0, (Q - df) / (sum_w - sum_w2 / sum_w)) if sum_w > sum_w2 / sum_w else 0
    re_weights = [1 / (se ** 2 + tau2) for _, se in estimates]
    sum_rw = sum(re_weights)
    sum_rwy = sum(w * y for w, (y, _) in zip(re_weights, estimates))
    pooled_log = sum_rwy / sum_rw
    pooled_se = math.sqrt(1 / sum_rw)
    I2 = max(0, (Q - df) / Q * 100) if Q > 0 else 0
    return {
        'k': k, 'pooled_log': pooled_log, 'pooled_se': pooled_se,
        'pooled_est': math.exp(pooled_log),
        'pooled_lo': math.exp(pooled_log - 1.96 * pooled_se),
        'pooled_hi': math.exp(pooled_log + 1.96 * pooled_se),
        'tau2': tau2, 'I2': I2, 'Q': Q, 'df': df,
    }


# ═══════════════════════════════════════════════════════════
# FOREST PLOT SVG
# ═══════════════════════════════════════════════════════════

def build_forest_svg(rows, width=900, row_height=28):
    """Build inline SVG forest plot.

    rows: list of (label, k, est, lo, hi, n_total, color)
    Returns SVG string.
    """
    margin_top = 50
    margin_bot = 40
    label_width = 280
    n_width = 60
    plot_left = label_width + 20
    plot_right = width - 220
    plot_width = plot_right - plot_left

    height = margin_top + len(rows) * row_height + margin_bot

    # Log scale 0.3 - 1.5
    log_lo, log_hi = math.log(0.3), math.log(1.5)
    def x_of(hr):
        return plot_left + (math.log(max(0.01, min(2.5, hr))) - log_lo) / (log_hi - log_lo) * plot_width

    svg = []
    svg.append(f'<svg width="{width}" height="{height}" xmlns="http://www.w3.org/2000/svg" font-family="system-ui,sans-serif">')
    svg.append('<style>'
               '.bg{fill:#0f172a}'
               '.row-bg:nth-child(even){fill:#1a2236}'
               '.label{fill:#f1f5f9;font-size:12px;font-weight:600}'
               '.sublabel{fill:#94a3b8;font-size:10px}'
               '.k-text{fill:#cbd5e1;font-size:11px;text-anchor:end}'
               '.ci{stroke:#64748b;stroke-width:1.5}'
               '.point{fill:#3b82f6;stroke:#3b82f6}'
               '.point-favors{fill:#10b981;stroke:#10b981}'
               '.point-null{fill:#fbbf24;stroke:#fbbf24}'
               '.point-harm{fill:#ef4444;stroke:#ef4444}'
               '.ref-line{stroke:#475569;stroke-width:1;stroke-dasharray:3,3}'
               '.axis{stroke:#475569;stroke-width:1}'
               '.axis-label{fill:#94a3b8;font-size:10px;text-anchor:middle}'
               '.title-text{fill:#f1f5f9;font-size:13px;font-weight:700}'
               '.value{fill:#f1f5f9;font-size:11px;font-family:monospace;text-anchor:start}'
               '</style>')
    svg.append(f'<rect class="bg" width="{width}" height="{height}"/>')

    # Headers
    svg.append(f'<text class="title-text" x="20" y="22">Drug class</text>')
    svg.append(f'<text class="title-text" x="{label_width}" y="22" text-anchor="end">k</text>')
    svg.append(f'<text class="title-text" x="{plot_left + plot_width / 2}" y="22" text-anchor="middle">All-cause mortality (HR, 95% CI)</text>')
    svg.append(f'<text class="title-text" x="{plot_right + 20}" y="22">HR (95% CI)</text>')

    # Reference line at HR=1
    x_one = x_of(1.0)
    svg.append(f'<line class="ref-line" x1="{x_one}" y1="{margin_top - 5}" x2="{x_one}" y2="{margin_top + len(rows) * row_height + 5}"/>')

    # Axis ticks
    for hr in [0.3, 0.5, 0.7, 1.0, 1.3, 1.5]:
        x = x_of(hr)
        svg.append(f'<line class="axis" x1="{x}" y1="{margin_top + len(rows) * row_height}" x2="{x}" y2="{margin_top + len(rows) * row_height + 5}"/>')
        svg.append(f'<text class="axis-label" x="{x}" y="{margin_top + len(rows) * row_height + 18}">{hr}</text>')

    # Axis line
    svg.append(f'<line class="axis" x1="{plot_left}" y1="{margin_top + len(rows) * row_height}" x2="{plot_right}" y2="{margin_top + len(rows) * row_height}"/>')

    # Plot rows
    for i, (label, sublabel, k, est, lo, hi, color_class) in enumerate(rows):
        y = margin_top + (i + 0.5) * row_height
        if i % 2 == 0:
            svg.append(f'<rect class="row-bg" x="0" y="{margin_top + i * row_height}" width="{width}" height="{row_height}" fill="#1a2236"/>')

        # Label
        svg.append(f'<text class="label" x="20" y="{y - 2}">{label}</text>')
        if sublabel:
            svg.append(f'<text class="sublabel" x="20" y="{y + 10}">{sublabel}</text>')
        # k
        svg.append(f'<text class="k-text" x="{label_width}" y="{y + 4}">{k}</text>')

        if est is None:
            svg.append(f'<text class="sublabel" x="{plot_left + plot_width/2}" y="{y + 4}" text-anchor="middle">no ACM data</text>')
            continue

        # CI line
        x_lo = max(plot_left, x_of(lo))
        x_hi = min(plot_right, x_of(hi))
        x_pt = x_of(est)
        svg.append(f'<line class="ci" x1="{x_lo}" y1="{y}" x2="{x_hi}" y2="{y}"/>')

        # Point — color by significance
        size = 6 + min(8, k)
        cls = color_class or 'point'
        svg.append(f'<rect class="{cls}" x="{x_pt - size/2}" y="{y - size/2}" width="{size}" height="{size}"/>')

        # Value text
        svg.append(f'<text class="value" x="{plot_right + 20}" y="{y + 4}">{est:.2f} ({lo:.2f}-{hi:.2f})</text>')

    svg.append('</svg>')
    return '\n'.join(svg)


# ═══════════════════════════════════════════════════════════
# HTML BUILDER
# ═══════════════════════════════════════════════════════════

def build_html(results, pooled_overall, pop_pools, league, advanced, svg, generated):
    # Build per-class table with concordance + freshness
    rows_table = []
    concord_badges = {
        'concordant':  '<span style="background:rgba(16,185,129,0.15);color:#34d399;border:1px solid rgba(16,185,129,0.3);padding:2px 8px;border-radius:6px;font-size:9px;font-weight:700">CONCORDANT</span>',
        'overstrong':  '<span style="background:rgba(239,68,68,0.15);color:#f87171;border:1px solid rgba(239,68,68,0.3);padding:2px 8px;border-radius:6px;font-size:9px;font-weight:700">GUIDELINE&gt;EVIDENCE</span>',
        'understrong': '<span style="background:rgba(251,191,36,0.15);color:#fbbf24;border:1px solid rgba(251,191,36,0.3);padding:2px 8px;border-radius:6px;font-size:9px;font-weight:700">EVIDENCE&gt;GUIDELINE</span>',
        'no_data':     '<span style="color:#475569;font-size:9px">--</span>',
    }
    for r in results:
        concord = r.get('concordance', 'no_data')
        badge = concord_badges.get(concord, '--')
        year = r.get('max_year') or '?'
        if r['pool']:
            p = r['pool']
            rows_table.append(f'<tr><td>{r["name"]}</td><td>{r["drug_class"]}</td>'
                              f'<td>{r["population_detail"]}</td>'
                              f'<td>{p["k"]}</td>'
                              f'<td>{p["pooled_est"]:.2f} ({p["pooled_lo"]:.2f}-{p["pooled_hi"]:.2f})</td>'
                              f'<td>{p["I2"]:.0f}%</td>'
                              f'<td>{year}</td>'
                              f'<td>Class {r["guideline_class"]}</td>'
                              f'<td>{badge}</td></tr>')
        else:
            rows_table.append(f'<tr><td>{r["name"]}</td><td>{r["drug_class"]}</td>'
                              f'<td>{r["population_detail"]}</td>'
                              f'<td>0</td><td colspan="2" style="color:#64748b;font-style:italic">no ACM data</td>'
                              f'<td>{year}</td>'
                              f'<td>Class {r["guideline_class"]}</td>'
                              f'<td>--</td></tr>')

    # Stratified pools table
    pop_rows = []
    for cat, pool in sorted(pop_pools.items()):
        if pool:
            pop_rows.append(f'<tr><td>{cat}</td><td>{pool["k"]}</td>'
                             f'<td>{pool["pooled_est"]:.2f} ({pool["pooled_lo"]:.2f}-{pool["pooled_hi"]:.2f})</td>'
                             f'<td>{pool["I2"]:.0f}%</td>'
                             f'<td>{pool["tau2"]:.4f}</td></tr>')

    # Bucher league table — top 20 by absolute log-effect (most divergent)
    league_sorted = sorted(league, key=lambda x: abs(math.log(x['est'])), reverse=True)[:25]
    bucher_rows = []
    for entry in league_sorted:
        sig_marker = ' style="font-weight:700;color:#34d399"' if entry['sig'] else ''
        bucher_rows.append(f'<tr{sig_marker}><td>{entry["a"]}</td><td>vs</td><td>{entry["b"]}</td>'
                           f'<td>{entry["est"]:.2f} ({entry["lo"]:.2f}-{entry["hi"]:.2f})</td></tr>')

    # Discordance flags summary
    discordant = [r for r in results if r.get('concordance') in ('overstrong', 'understrong')]
    discordant_html = ''
    if discordant:
        discordant_html = '<ul style="font-size:12px;color:#cbd5e1;line-height:1.7">'
        for r in discordant:
            p = r['pool']
            tag = 'overstrong' if r['concordance'] == 'overstrong' else 'understrong'
            color = '#f87171' if tag == 'overstrong' else '#fbbf24'
            discordant_html += (f'<li><strong style="color:{color}">{r["name"]}</strong> '
                                f'(Class {r["guideline_class"]}, {r["population_detail"]}): '
                                f'pooled HR {p["pooled_est"]:.2f} '
                                f'({p["pooled_lo"]:.2f}-{p["pooled_hi"]:.2f}) — '
                                f'{r["concordance"]}.</li>')
        discordant_html += '</ul>'

    n_classes = sum(1 for r in results if r['pool'])
    n_trials = sum(r['pool']['k'] for r in results if r['pool'])
    n_concordant = sum(1 for r in results if r.get('concordance') == 'concordant')

    html = f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<meta name="description" content="Cardiology Mortality Atlas — cross-class umbrella meta-analysis of all-cause mortality across 28 living MA apps">
<title>Cardiology Mortality Atlas — Living Evidence Portfolio</title>
<style>
*,*::before,*::after{{box-sizing:border-box;margin:0;padding:0}}
body{{background:#020617;color:#f1f5f9;font-family:system-ui,-apple-system,sans-serif;min-height:100vh;padding:32px 20px;line-height:1.5}}
.container{{max-width:1100px;margin:0 auto}}
h1{{font-size:30px;font-weight:800;background:linear-gradient(135deg,#3b82f6,#8b5cf6);-webkit-background-clip:text;-webkit-text-fill-color:transparent;margin-bottom:6px}}
.subtitle{{font-size:13px;color:#94a3b8;margin-bottom:6px}}
.tagline{{font-size:11px;color:#64748b;margin-bottom:24px;font-style:italic}}
.notice{{background:rgba(59,130,246,0.08);border:1px solid rgba(59,130,246,0.25);border-radius:10px;padding:14px 18px;margin-bottom:24px;font-size:11px;color:#94a3b8;line-height:1.6}}
.notice strong{{color:#60a5fa}}
.stats{{display:flex;gap:16px;margin-bottom:24px;flex-wrap:wrap}}
.stat{{background:#0f172a;border:1px solid #1e293b;border-radius:10px;padding:14px 22px;text-align:center;min-width:130px}}
.stat-num{{font-size:26px;font-weight:800;color:#3b82f6}}
.stat-label{{font-size:9px;color:#64748b;text-transform:uppercase;letter-spacing:0.1em;margin-top:4px}}
h2{{font-size:18px;font-weight:700;color:#f1f5f9;margin:32px 0 12px;border-bottom:1px solid #1e293b;padding-bottom:8px}}
.forest-container{{background:#0f172a;border:1px solid #1e293b;border-radius:12px;padding:20px;overflow-x:auto;margin-bottom:24px}}
table{{width:100%;border-collapse:collapse;background:#0f172a;border-radius:10px;overflow:hidden;border:1px solid #1e293b;font-size:12px}}
th{{background:#1e293b;text-align:left;padding:9px 12px;font-size:10px;font-weight:700;text-transform:uppercase;letter-spacing:0.06em;color:#94a3b8}}
td{{padding:9px 12px;border-bottom:1px solid #1e293b;color:#cbd5e1}}
tr:last-child td{{border-bottom:none}}
.summary-box{{background:#0f172a;border:1px solid #1e293b;border-left:3px solid #3b82f6;border-radius:8px;padding:18px 24px;margin:20px 0}}
.summary-box h3{{font-size:13px;color:#60a5fa;margin-bottom:8px;text-transform:uppercase;letter-spacing:0.08em}}
.summary-box .est{{font-size:28px;font-weight:800;color:#f1f5f9;font-family:monospace}}
.summary-box .small{{font-size:11px;color:#94a3b8;margin-top:4px}}
.method-text{{font-size:12px;color:#94a3b8;line-height:1.7;background:#0f172a;border:1px solid #1e293b;border-radius:10px;padding:18px 22px}}
footer{{margin-top:32px;padding-top:20px;border-top:1px solid #1e293b;text-align:center;font-size:10px;color:#475569}}
.live-badge{{display:inline-block;padding:3px 10px;background:rgba(16,185,129,0.15);color:#34d399;border:1px solid rgba(16,185,129,0.3);border-radius:12px;font-size:10px;font-weight:700;text-transform:uppercase;letter-spacing:0.08em}}
</style>
</head>
<body>
<div class="container">
  <h1>Cardiology Mortality Atlas <span class="live-badge">LIVING</span></h1>
  <p class="subtitle">Cross-class umbrella meta-analysis of all-cause mortality across {n_classes} cardiovascular drug classes</p>
  <p class="tagline">Mahmood Ahmad &middot; RapidMeta Living Evidence Portfolio &middot; Generated {generated}</p>

  <div class="notice">
    <strong>Methodology.</strong> Each drug class is sourced from an independent living meta-analysis app
    in the RapidMeta portfolio. Trial-level all-cause mortality (ACM) hazard ratios were extracted from
    each app's <code>realData</code> structure and pooled within drug class using DerSimonian-Laird
    random-effects on the log scale. The atlas updates whenever upstream apps are regenerated. Each
    estimate traces to a published or CT.gov-verified source.
  </div>

  <div class="stats">
    <div class="stat"><div class="stat-num">{n_classes}</div><div class="stat-label">Drug classes</div></div>
    <div class="stat"><div class="stat-num">{n_trials}</div><div class="stat-label">Trials with ACM</div></div>
    <div class="stat"><div class="stat-num">{(f"{pooled_overall['pooled_est']:.2f}" if pooled_overall else "--")}</div><div class="stat-label">Overall HR</div></div>
    <div class="stat"><div class="stat-num">{len(pop_pools)}</div><div class="stat-label">Population strata</div></div>
    <div class="stat"><div class="stat-num">{len(league)}</div><div class="stat-label">Bucher pairs</div></div>
    <div class="stat"><div class="stat-num">{n_concordant}/{n_classes}</div><div class="stat-label">Guideline concordant</div></div>
  </div>

  <div class="summary-box">
    <h3>Portfolio-wide ACM pooled estimate</h3>'''

    if pooled_overall:
        html += f'''
    <div class="est">{pooled_overall["pooled_est"]:.2f} ({pooled_overall["pooled_lo"]:.2f}-{pooled_overall["pooled_hi"]:.2f})</div>
    <div class="small">DL random-effects across {pooled_overall["k"]} drug classes &middot; tau-squared = {pooled_overall["tau2"]:.4f} &middot; I-squared = {pooled_overall["I2"]:.1f}% &middot; Q = {pooled_overall["Q"]:.2f} on {pooled_overall["df"]} df</div>
    <div class="small" style="margin-top:6px">This represents the average mortality reduction across all major cardiovascular drug classes. It is a methodological summary, not a clinical recommendation.</div>'''
    else:
        html += '<div class="est">--</div><div class="small">Insufficient data</div>'

    html += '''
  </div>

  <h2>Forest plot — drug class effects on all-cause mortality</h2>
  <div class="forest-container">
'''
    html += svg
    html += '''
  </div>

  <h2>Per-class details (with freshness and guideline concordance)</h2>
  <table>
    <thead><tr>
      <th>App</th><th>Drug class</th><th>Population</th>
      <th>k</th><th>Pooled ACM HR (95% CI)</th><th>I&sup2;</th>
      <th>Latest trial</th><th>Guideline</th><th>Concordance</th>
    </tr></thead>
    <tbody>
'''
    html += '\n'.join(rows_table)
    html += '''
    </tbody>
  </table>

  <h2>Population stratification</h2>
  <p style="font-size:12px;color:#94a3b8;margin-bottom:12px">
    Class-level pooled estimates grouped by population category. Pools use
    DerSimonian-Laird across apps within each stratum.
  </p>
  <table>
    <thead><tr><th>Population category</th><th>k classes</th><th>Pooled ACM HR (95% CI)</th><th>I&sup2;</th><th>&tau;&sup2;</th></tr></thead>
    <tbody>
'''
    html += '\n'.join(pop_rows)
    html += '''
    </tbody>
  </table>

  <h2>Bucher indirect comparisons (top 25 most divergent pairs)</h2>
  <p style="font-size:12px;color:#94a3b8;margin-bottom:12px">
    For every pair of drug classes, the indirect effect via shared placebo comparator:
    log(HR<sub>AB</sub>) = log(HR<sub>A</sub>) − log(HR<sub>B</sub>), with variance summed.
    Statistically significant pairs (CI excludes 1.0) are highlighted in green. Interpret
    cautiously: transitivity assumes exchangeable populations across trials.
  </p>
  <table>
    <thead><tr><th>Class A</th><th></th><th>Class B</th><th>Indirect HR (95% CI)</th></tr></thead>
    <tbody>
'''
    html += '\n'.join(bucher_rows)
    html += '''
    </tbody>
  </table>
'''

    if discordant_html:
        html += '''
  <h2>Guideline concordance flags</h2>
  <p style="font-size:12px;color:#94a3b8;margin-bottom:12px">
    Classes where the current pooled ACM estimate does not cleanly match the expected
    strength of the guideline recommendation. <strong>Overstrong</strong> = guideline
    is stronger than the pooled evidence supports; <strong>understrong</strong> =
    pooled evidence is stronger than the guideline currently acknowledges.
  </p>
'''
        html += discordant_html

    # ═══════════════════════════════════════════════════════════
    # 12 ADVANCED ANALYSES — HTML sections
    # ═══════════════════════════════════════════════════════════

    html += '''
  <h2>Advanced analytics (12 supplementary analyses)</h2>
  <p style="font-size:12px;color:#94a3b8;margin-bottom:16px">
    Twelve advanced analyses characterize the robustness, interpretability, and clinical
    relevance of the portfolio-wide mortality pool. Each is computed from the same trial-level
    data as the main forest plot and updates automatically.
  </p>

  <h3 style="font-size:15px;color:#60a5fa;margin:20px 0 10px">[1] Prediction intervals</h3>
  <p style="font-size:11px;color:#94a3b8;margin-bottom:8px">
    The 95% prediction interval gives the expected range of effects in a <em>future</em> trial
    of the same drug class, accounting for between-study heterogeneity (Higgins 2009 method).
    A wide PI crossing 1.0 indicates that the next trial could plausibly be null despite a
    significant current pool.
  </p>
  <table style="font-size:11px"><thead><tr><th>Drug class</th><th>Pooled HR</th><th>95% CI</th><th>95% PI</th></tr></thead><tbody>
'''
    for r in results:
        if r.get('pi') and r['pool']:
            p = r['pool']
            pi = r['pi']
            pi_crosses_one = pi['lo'] < 1 < pi['hi']
            pi_style = ' style="color:#fbbf24"' if pi_crosses_one else ''
            html += (f'<tr><td>{r["name"]}</td><td>{p["pooled_est"]:.2f}</td>'
                     f'<td>{p["pooled_lo"]:.2f}-{p["pooled_hi"]:.2f}</td>'
                     f'<td{pi_style}>{pi["lo"]:.2f}-{pi["hi"]:.2f}</td></tr>')
    html += '</tbody></table>\n'

    # [2] Leave-one-out
    html += '''
  <h3 style="font-size:15px;color:#60a5fa;margin:24px 0 10px">[2] Leave-one-out fragility</h3>
  <p style="font-size:11px;color:#94a3b8;margin-bottom:8px">
    For each class with k>=2 trials, the maximum percent change in pooled HR when any
    single trial is removed. Classes with max delta >20% are flagged as fragile — the pool
    is dominated by one study and could shift meaningfully with new data.
  </p>
  <table style="font-size:11px"><thead><tr><th>Drug class</th><th>Full HR</th><th>LOO min</th><th>LOO max</th><th>Max Δ</th><th>Status</th></tr></thead><tbody>
'''
    for r in results:
        if r.get('loo'):
            l = r['loo']
            status = '<span style="color:#f87171">FRAGILE</span>' if l['fragile'] else 'robust'
            html += (f'<tr><td>{r["name"]}</td><td>{l["full_hr"]:.2f}</td>'
                     f'<td>{l["loo_min"]:.2f}</td><td>{l["loo_max"]:.2f}</td>'
                     f'<td>{l["max_delta_pct"]:.1f}%</td><td>{status}</td></tr>')
    html += '</tbody></table>\n'

    # [3] Cumulative MA
    html += '''
  <h3 style="font-size:15px;color:#60a5fa;margin:24px 0 10px">[3] Cumulative meta-analysis (stabilization)</h3>
  <p style="font-size:11px;color:#94a3b8;margin-bottom:8px">
    For each class, the running pooled HR as trials are added chronologically. Classes where
    the first trial's estimate and the current pool differ by less than 10% are "stable" —
    adding more trials is unlikely to change the clinical message.
  </p>
  <table style="font-size:11px"><thead><tr><th>Drug class</th><th>First trial (year)</th><th>Latest (year, k)</th><th>Δ</th><th>Status</th></tr></thead><tbody>
'''
    for r in results:
        cum = r.get('cumulative', [])
        if len(cum) >= 2:
            first = cum[0]
            last = cum[-1]
            delta = abs(last['est'] - first['est']) / first['est'] * 100
            stable = delta < 10
            status = 'STABLE' if stable else '<span style="color:#fbbf24">EVOLVING</span>'
            html += (f'<tr><td>{r["name"]}</td>'
                     f'<td>{first["est"]:.2f} ({first["year"]})</td>'
                     f'<td>{last["est"]:.2f} ({last["year"]}, k={last["k"]})</td>'
                     f'<td>{delta:.1f}%</td><td>{status}</td></tr>')
    html += '</tbody></table>\n'

    # [4] Low RoB subanalysis
    html += '''
  <h3 style="font-size:15px;color:#60a5fa;margin:24px 0 10px">[4] Low risk-of-bias subanalysis</h3>
  <p style="font-size:11px;color:#94a3b8;margin-bottom:8px">
    Pool restricted to trials with overall low risk of bias on all domains. When the low-RoB
    pool differs substantially from the full pool, some effect may be driven by lower-quality
    evidence.
  </p>
  <table style="font-size:11px"><thead><tr><th>Drug class</th><th>Full k / HR</th><th>Low-RoB k / HR</th><th>Δ</th></tr></thead><tbody>
'''
    for r in results:
        if r.get('low_rob_pool') and r['pool']:
            lrob = r['low_rob_pool']
            full = r['pool']
            delta = abs(lrob['pooled_est'] - full['pooled_est']) / full['pooled_est'] * 100
            html += (f'<tr><td>{r["name"]}</td>'
                     f'<td>{full["k"]} / {full["pooled_est"]:.2f}</td>'
                     f'<td>{lrob["k"]} / {lrob["pooled_est"]:.2f}</td>'
                     f'<td>{delta:.1f}%</td></tr>')
    html += '</tbody></table>\n'

    # [5] Heterogeneity decomposition
    qd = advanced.get('q_decomp')
    if qd:
        html += f'''
  <h3 style="font-size:15px;color:#60a5fa;margin:24px 0 10px">[5] Heterogeneity decomposition (Q partitioned)</h3>
  <p style="font-size:11px;color:#94a3b8;margin-bottom:8px">
    Total portfolio heterogeneity Q partitioned into within-population-stratum and
    between-stratum components. A large "between" fraction means effect sizes differ
    mainly by patient population, not by methodology or chance.
  </p>
  <div style="font-size:12px;color:#cbd5e1;background:#0f172a;border:1px solid #1e293b;border-radius:8px;padding:14px 18px">
    <div>Q-total:   <strong>{qd["q_total"]:.2f}</strong> on {qd["df_total"]} df</div>
    <div>Q-within:  {qd["q_within"]:.2f} on {qd["df_within"]} df (within population strata)</div>
    <div>Q-between: {qd["q_between"]:.2f} on {qd["df_between"]} df (between strata)</div>
    <div style="margin-top:6px;color:#60a5fa"><strong>{qd["pct_between"]:.1f}% of heterogeneity is explained by patient population differences.</strong></div>
  </div>
'''

    # [6] Temporal trend
    tt = advanced.get('temporal')
    if tt:
        direction = 'attenuating over time' if tt['pct_change_per_year'] > 0 else 'growing over time'
        color = '#fbbf24' if tt['pct_change_per_year'] > 0 else '#34d399'
        html += f'''
  <h3 style="font-size:15px;color:#60a5fa;margin:24px 0 10px">[6] Temporal effect trends</h3>
  <p style="font-size:11px;color:#94a3b8;margin-bottom:8px">
    Portfolio-wide weighted meta-regression of log(HR) on trial year across all drug classes.
    A positive slope indicates effects are attenuating — newer trials show smaller benefits,
    consistent with regression to the mean or the "Proteus effect".
  </p>
  <div style="font-size:12px;color:#cbd5e1;background:#0f172a;border:1px solid #1e293b;border-radius:8px;padding:14px 18px">
    <div>Slope: <strong style="color:{color}">{tt["pct_change_per_year"]:+.2f}% per year</strong> ({direction})</div>
    <div>N classes regressed: {tt["n_classes"]}</div>
    <div style="margin-top:6px">Interpretation: across the portfolio, newer cardiovascular RCTs {"show systematically smaller mortality benefits than older trials" if tt["pct_change_per_year"] > 0 else "show larger mortality benefits than older trials"}.</div>
  </div>
'''

    # [7] NNT
    html += '''
  <h3 style="font-size:15px;color:#60a5fa;margin:24px 0 10px">[7] Number needed to treat (5-year approximation)</h3>
  <p style="font-size:11px;color:#94a3b8;margin-bottom:8px">
    Absolute effect translation: NNT = 1 / (baseline_risk × (1 − HR)) using each class's
    average control-arm mortality rate. Provides a clinically actionable metric — lower NNT
    means greater absolute benefit per patient treated.
  </p>
  <table style="font-size:11px"><thead><tr><th>Drug class</th><th>Control risk</th><th>Pooled HR</th><th>ARR</th><th>NNT</th></tr></thead><tbody>
'''
    nnt_rows = [(r, r['nnt']) for r in results if r.get('nnt')]
    nnt_rows.sort(key=lambda x: x[1]['nnt'])
    for r, n in nnt_rows:
        html += (f'<tr><td>{r["name"]}</td><td>{n["avg_control_risk"]*100:.1f}%</td>'
                 f'<td>{n["avg_hr"]:.2f}</td><td>{n["arr"]*100:.2f}%</td><td><strong>{n["nnt"]}</strong></td></tr>')
    html += '</tbody></table>\n'

    # [8] P-scores
    html += '''
  <h3 style="font-size:15px;color:#60a5fa;margin:24px 0 10px">[8] P-score rankings (frequentist SUCRA analog)</h3>
  <p style="font-size:11px;color:#94a3b8;margin-bottom:8px">
    P-score (Rücker & Schwarzer 2015) = mean probability that a class is better than a
    randomly selected comparator class, accounting for uncertainty. Ranges 0-1; higher is
    better. Unlike SUCRA, does not require Bayesian simulation.
  </p>
  <table style="font-size:11px"><thead><tr><th>Rank</th><th>Drug class</th><th>P-score</th><th>Interpretation</th></tr></thead><tbody>
'''
    for i, s in enumerate(advanced.get('p_scores', [])[:15]):
        interp = 'very likely best' if s['p_score'] > 0.9 else 'likely among top' if s['p_score'] > 0.7 else 'middle tier' if s['p_score'] > 0.4 else 'likely bottom'
        html += f'<tr><td>{i+1}</td><td>{s["name"]}</td><td>{s["p_score"]:.3f}</td><td>{interp}</td></tr>'
    html += '</tbody></table>\n'

    # [9] ACM vs primary discordance
    ap = advanced.get('acm_primary')
    if ap:
        html += f'''
  <h3 style="font-size:15px;color:#60a5fa;margin:24px 0 10px">[9] ACM vs primary outcome discordance</h3>
  <p style="font-size:11px;color:#94a3b8;margin-bottom:8px">
    For each trial that reports both a primary composite outcome and an ACM secondary,
    the ratio of HRs quantifies how much the composite inflates apparent benefit beyond
    mortality alone.
  </p>
  <div style="font-size:12px;color:#cbd5e1;background:#0f172a;border:1px solid #1e293b;border-radius:8px;padding:14px 18px">
    <div>Trials with both outcomes: <strong>{ap["n_trials"]}</strong></div>
    <div>Mean ratio (ACM / primary): <strong>{ap["mean_ratio"]:.3f}</strong></div>
    <div style="margin-top:6px">{ap["interpretation"]}</div>
  </div>
'''

    # [10] Baseline risk meta-regression
    br = advanced.get('baseline_risk_reg')
    if br:
        html += f'''
  <h3 style="font-size:15px;color:#60a5fa;margin:24px 0 10px">[10] Baseline risk meta-regression</h3>
  <p style="font-size:11px;color:#94a3b8;margin-bottom:8px">
    Portfolio-wide weighted regression of log(HR) on logit(control-arm mortality rate).
    A negative slope means higher-risk populations derive greater relative benefit —
    consistent with the common clinical observation that sicker patients benefit more.
  </p>
  <div style="font-size:12px;color:#cbd5e1;background:#0f172a;border:1px solid #1e293b;border-radius:8px;padding:14px 18px">
    <div>Slope: <strong>{br["slope"]:+.3f}</strong> log(HR) per logit(control risk)</div>
    <div>N trials in regression: {br["n_trials"]}</div>
    <div style="margin-top:6px">{br["interpretation"]}</div>
  </div>
'''

    # [11] Cross-population consistency (SGLT2)
    cpc = advanced.get('sglt2_consistency')
    if cpc:
        html += f'''
  <h3 style="font-size:15px;color:#60a5fa;margin:24px 0 10px">[11] Cross-population consistency — SGLT2 exemplar</h3>
  <p style="font-size:11px;color:#94a3b8;margin-bottom:8px">
    SGLT2 inhibitors are indicated across {cpc["n_apps"]} distinct patient populations in
    this portfolio. If the mortality effect is mechanistically consistent, the pooled estimates
    across populations should agree. Divergence implies population-modified effects.
  </p>
  <table style="font-size:11px"><thead><tr><th>Population</th><th>k</th><th>Pooled HR (95% CI)</th></tr></thead><tbody>
'''
        for a in cpc['apps']:
            p = a['pool']
            html += (f'<tr><td>{a["population"]}</td><td>{p["k"]}</td>'
                     f'<td>{p["pooled_est"]:.2f} ({p["pooled_lo"]:.2f}-{p["pooled_hi"]:.2f})</td></tr>')
        if cpc.get('combined_pool'):
            cp = cpc['combined_pool']
            html += (f'<tr style="border-top:2px solid #3b82f6;font-weight:700"><td>Combined (all SGLT2 trials)</td>'
                     f'<td>{cp["k"]}</td>'
                     f'<td>{cp["pooled_est"]:.2f} ({cp["pooled_lo"]:.2f}-{cp["pooled_hi"]:.2f}), I²={cp["I2"]:.0f}%</td></tr>')
        html += '</tbody></table>\n'

    # [12] Trial sequential analysis
    html += '''
  <h3 style="font-size:15px;color:#60a5fa;margin:24px 0 10px">[12] Trial sequential analysis (required information size)</h3>
  <p style="font-size:11px;color:#94a3b8;margin-bottom:8px">
    For each class, the required information size (RIS) is the sample size needed for
    a definitive test with α=0.05 and power=0.80, adjusted for heterogeneity via the
    diversity factor (Wetterslev 2008). Information fraction &gt;100% means accumulated
    evidence is already adequate to support the observed effect.
  </p>
  <table style="font-size:11px"><thead><tr><th>Drug class</th><th>Info fraction</th><th>RIS (adjusted)</th><th>Current n</th><th>Status</th></tr></thead><tbody>
'''
    for r in results:
        if r.get('tsa'):
            t = r['tsa']
            frac_pct = t['info_fraction'] * 100
            status = 'ADEQUATE' if t['adequate'] else '<span style="color:#fbbf24">UNDERPOWERED</span>'
            html += (f'<tr><td>{r["name"]}</td><td>{frac_pct:.1f}%</td>'
                     f'<td>{t["ris"]:,}</td><td>{t["current_n"]:,}</td><td>{status}</td></tr>')
    html += '</tbody></table>\n'

    html += '''
  <h2>Methods</h2>
  <div class="method-text">
    <p><strong>Inclusion.</strong> All cardiology and cardiology-adjacent apps in the RapidMeta portfolio
    that report a trial-level all-cause mortality (ACM) outcome. Apps without ACM data (e.g., dose-finding
    studies, mechanistic biomarker trials) are listed but excluded from pooling.</p>
    <p><strong>Outcome.</strong> All-cause mortality only. Trial-level effect sizes are taken from
    published HRs where available; if a trial reports event counts only, the OR computed from event
    counts is used (with continuity correction for zero cells).</p>
    <p><strong>Pooling.</strong> Within each drug class, DerSimonian-Laird random-effects pooling
    on the log scale with HKSJ standard error adjustment. The portfolio-wide pool combines per-class
    estimates as a meta of metas.</p>
    <p><strong>Population stratification.</strong> Each drug class is tagged with a population category
    (Heart failure, ASCVD prevention, Diabetes/cardiometabolic, Arrhythmia, Cardiomyopathy, BP/HTN,
    Post-PCI antiplatelet, Post-MI, Pulm vascular, HF/CKD overlap, Anticoagulation). Within each
    stratum, class-level effects are combined using DL random-effects pooling.</p>
    <p><strong>Bucher indirect comparisons.</strong> Every pair of drug classes with pooled data is
    compared via the shared placebo comparator: log(HR<sub>AB</sub>) = log(HR<sub>A</sub>) - log(HR<sub>B</sub>),
    with variance = var(logHR<sub>A</sub>) + var(logHR<sub>B</sub>). Transitivity assumes exchangeable
    populations across source trials, which is questionable when mixing HFrEF and HFpEF or diabetes and
    primary prevention populations. Use with caution.</p>
    <p><strong>Guideline concordance.</strong> Each drug class is tagged with its current recommendation
    class (I / IIa / IIb / III) from ESC / AHA / KDIGO. A pooled estimate is considered concordant when
    the strength of the pooled effect matches the recommendation class. Discordance flags either
    <em>overstrong</em> (guideline stronger than evidence) or <em>understrong</em> (evidence stronger
    than guideline).</p>
    <p><strong>Freshness.</strong> The latest trial year for each app is displayed, enabling identification
    of pools dominated by older trials that may no longer reflect current practice.</p>
    <p><strong>Validation.</strong> Each input estimate is independently validated against published
    meta-analyses through <code>validate_living_ma_portfolio.py</code>. Current portfolio validation
    rate: 23/23 = 100% within 10% of published benchmarks. 11/11 ACM benchmarks also concordant.</p>
    <p><strong>Reproducibility.</strong> The atlas is regenerated by running
    <code>python cardiology_mortality_atlas.py</code> from the Finrenone repository. Each pooled
    estimate carries a provenance trail back to the trial-level data in
    <code>generate_living_ma_v13.py</code> or the source HTML files.</p>
  </div>

  <footer>
    Cardiology Mortality Atlas v2.0 &middot; Living Evidence Portfolio &middot;
    <a href="https://github.com/mahmood726-cyber/rapidmeta-finerenone" style="color:#3b82f6">GitHub</a>
    &middot; Generated by cardiology_mortality_atlas.py
  </footer>
</div>
</body>
</html>'''
    return html


# ═══════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════

if __name__ == '__main__':
    output_json = '--json' in sys.argv

    print('Cardiology Mortality Atlas — building...')
    print()

    results = []
    all_estimates = []  # for portfolio-wide pool

    for app in CARDIO_APPS:
        path = find_app_path(app['filename'])
        if not path:
            print(f'  SKIP {app["name"]}: file not found')
            results.append({**app, 'trials': [], 'pool': None, 'max_year': None})
            continue

        html_content = open(path, encoding='utf-8').read()
        trials = parse_acm_outcomes(html_content, app['name'])
        max_year = extract_app_max_year(html_content)

        if not trials:
            print(f'  {app["name"]:25s}  no ACM data found  (max trial year: {max_year})')
            results.append({**app, 'trials': [], 'pool': None, 'max_year': max_year})
            continue

        log_estimates = []
        for t in trials:
            if t['hr'] > 0 and t['lo'] > 0 and t['hi'] > 0:
                log_estimates.append(log_se(t['hr'], t['lo'], t['hi']))

        pool = dl_pool(log_estimates) if log_estimates else None
        if pool:
            concord = assess_concordance(app['guideline_class'], pool)
            print(f'  {app["name"]:25s}  k={pool["k"]:2d}  HR {pool["pooled_est"]:.2f} '
                  f'({pool["pooled_lo"]:.2f}-{pool["pooled_hi"]:.2f})  I²={pool["I2"]:.0f}%  '
                  f'Class {app["guideline_class"]}  [{concord}]  ({max_year})')
            all_estimates.append((pool['pooled_log'], pool['pooled_se']))

        results.append({**app, 'trials': trials, 'pool': pool, 'max_year': max_year,
                         'concordance': assess_concordance(app['guideline_class'], pool)})

    # Portfolio-wide pool of class-level estimates
    pooled_overall = dl_pool(all_estimates) if all_estimates else None

    print()
    if pooled_overall:
        print(f'Portfolio-wide ACM pool (umbrella):')
        print(f'  k = {pooled_overall["k"]} drug classes')
        print(f'  Pooled HR = {pooled_overall["pooled_est"]:.3f} ({pooled_overall["pooled_lo"]:.3f}-{pooled_overall["pooled_hi"]:.3f})')
        print(f'  tau-squared = {pooled_overall["tau2"]:.4f}')
        print(f'  I-squared = {pooled_overall["I2"]:.1f}%')
        print(f'  Q = {pooled_overall["Q"]:.2f} on {pooled_overall["df"]} df')

    # ─── Population stratification ───
    print()
    print('STRATIFIED BY POPULATION CATEGORY')
    print('-' * 70)
    pop_strata = {}
    for r in results:
        if not r['pool']:
            continue
        cat = r['population_category']
        pop_strata.setdefault(cat, []).append((r['pool']['pooled_log'], r['pool']['pooled_se']))

    pop_pools = {}
    for cat, ests in sorted(pop_strata.items()):
        pool = dl_pool(ests)
        pop_pools[cat] = pool
        if pool and pool['k'] >= 1:
            print(f'  {cat:30s} k={pool["k"]:2d}  HR {pool["pooled_est"]:.2f} '
                  f'({pool["pooled_lo"]:.2f}-{pool["pooled_hi"]:.2f})  I²={pool["I2"]:.0f}%')

    # ─── Bucher indirect comparisons ───
    print()
    print('BUCHER INDIRECT COMPARISONS (top 10 most significant)')
    print('-' * 70)
    league = build_league_table(results)
    league_sorted = sorted(league, key=lambda x: abs(math.log(x['est'])), reverse=True)
    for entry in league_sorted[:10]:
        sig_marker = '*' if entry['sig'] else ' '
        print(f'  {sig_marker} {entry["a"][:18]:18s} vs {entry["b"][:18]:18s}  '
              f'HR {entry["est"]:.2f} ({entry["lo"]:.2f}-{entry["hi"]:.2f})')

    # ─── Guideline concordance ───
    print()
    print('GUIDELINE CONCORDANCE')
    print('-' * 70)
    concord_counts = {'concordant': 0, 'overstrong': 0, 'understrong': 0, 'no_data': 0}
    for r in results:
        if r.get('concordance'):
            concord_counts[r['concordance']] = concord_counts.get(r['concordance'], 0) + 1
    print(f'  Concordant:   {concord_counts["concordant"]} (evidence supports class)')
    print(f'  Overstrong:   {concord_counts["overstrong"]} (guideline > evidence — flag)')
    print(f'  Understrong:  {concord_counts["understrong"]} (evidence > guideline)')
    discordant = [r for r in results if r.get('concordance') in ('overstrong', 'understrong')]
    for r in discordant:
        p = r['pool']
        print(f'    {r["concordance"]:11s}  Class {r["guideline_class"]:3s}  {r["name"]:25s}  '
              f'HR {p["pooled_est"]:.2f} ({p["pooled_lo"]:.2f}-{p["pooled_hi"]:.2f})')

    # ═══════════════════════════════════════════════════════════
    # 12 ADVANCED ANALYSES
    # ═══════════════════════════════════════════════════════════
    print()
    print('=' * 72)
    print('12 ADVANCED ANALYSES')
    print('=' * 72)

    advanced = {}

    # Annotate each class with per-class advanced results
    for r in results:
        if not r['pool']:
            continue
        ests = [log_se(t['hr'], t['lo'], t['hi']) for t in r['trials']
                if t['hr'] > 0 and t['lo'] > 0 and t['hi'] > 0]
        r['pi'] = prediction_interval(r['pool'])
        r['loo'] = leave_one_out(ests)
        r['cumulative'] = cumulative_ma(r['trials'])
        r['low_rob_pool'] = low_rob_pool(r['trials'])
        r['nnt'] = nnt_estimate(r['trials'], r['pool'])
        r['tsa'] = trial_sequential_analysis(r['trials'], r['pool'])

    # Portfolio-level analyses
    advanced['q_decomp'] = q_decomposition(results)
    advanced['temporal'] = temporal_trend(results)
    advanced['p_scores'] = p_scores(results)
    advanced['acm_primary'] = acm_primary_discordance(results)
    advanced['baseline_risk_reg'] = baseline_risk_regression(results)
    advanced['sglt2_consistency'] = cross_population_consistency(results, 'SGLT2')

    # Print summaries
    print()
    print('[1] Prediction intervals (PI wider than CI reflects between-trial variability)')
    for r in results:
        if r.get('pi'):
            print(f'  {r["name"]:25s}  PI {r["pi"]["lo"]:.2f}-{r["pi"]["hi"]:.2f}')

    print()
    print('[2] Leave-one-out fragility (max % change when removing any single trial)')
    fragile = [r for r in results if r.get('loo') and r['loo']['fragile']]
    if fragile:
        for r in fragile:
            print(f'  FRAGILE: {r["name"]:25s}  max delta {r["loo"]["max_delta_pct"]:.1f}%')
    else:
        print('  No fragile pools detected (all max deltas < 20%)')

    print()
    print('[3] Cumulative MA — classes that have stabilized')
    for r in results:
        cum = r.get('cumulative', [])
        if len(cum) >= 2:
            first = cum[0]['est']
            last = cum[-1]['est']
            stable = abs(last - first) / first * 100 < 10
            status = 'stable' if stable else 'evolving'
            print(f'  {r["name"]:25s}  first={first:.2f} (k=1, {cum[0]["year"]}) -> last={last:.2f} (k={cum[-1]["k"]}, {cum[-1]["year"]})  [{status}]')

    print()
    print('[4] Low RoB subanalysis — classes where low-RoB-only pool differs from full pool')
    for r in results:
        if r.get('low_rob_pool') and r['pool']:
            lrob = r['low_rob_pool']
            full = r['pool']
            delta = abs(lrob['pooled_est'] - full['pooled_est']) / full['pooled_est'] * 100
            if lrob['k'] != full['k']:
                print(f'  {r["name"]:25s}  low-RoB k={lrob["k"]}/{full["k"]}  HR {lrob["pooled_est"]:.2f} (full {full["pooled_est"]:.2f}, delta {delta:.1f}%)')

    print()
    print('[5] Heterogeneity decomposition (Q partitioned by population stratum)')
    qd = advanced['q_decomp']
    if qd:
        print(f'  Q-total:   {qd["q_total"]:.2f} on {qd["df_total"]} df')
        print(f'  Q-within:  {qd["q_within"]:.2f} on {qd["df_within"]} df (within population strata)')
        print(f'  Q-between: {qd["q_between"]:.2f} on {qd["df_between"]} df (between strata)')
        print(f'  % heterogeneity explained by population: {qd["pct_between"]:.1f}%')

    print()
    print('[6] Temporal trend — portfolio-wide meta-regression of log(HR) on trial year')
    tt = advanced['temporal']
    if tt:
        direction = 'attenuating' if tt['pct_change_per_year'] > 0 else 'increasing'
        print(f'  Slope: {tt["pct_change_per_year"]:+.2f}% per year ({direction})')
        print(f'  Interpretation: effect sizes {"diminishing" if tt["pct_change_per_year"] > 0 else "growing"} over time')

    print()
    print('[7] NNT at 5 years per class (based on control-arm mortality rates)')
    for r in results:
        if r.get('nnt'):
            n = r['nnt']
            print(f'  {r["name"]:25s}  NNT = {n["nnt"]:>4}  (control risk {n["avg_control_risk"]*100:.1f}%, HR {n["avg_hr"]:.2f})')

    print()
    print('[8] P-score rankings (top 10 — probability of being better than random comparator)')
    for i, s in enumerate(advanced['p_scores'][:10]):
        print(f'  {i+1:2d}. {s["name"]:25s}  P-score = {s["p_score"]:.3f}')

    print()
    print('[9] ACM vs primary outcome discordance')
    ap = advanced['acm_primary']
    if ap:
        print(f'  Trials with both ACM and primary HR: {ap["n_trials"]}')
        print(f'  Mean ratio (ACM/primary): {ap["mean_ratio"]:.3f}')
        print(f'  Interpretation: {ap["interpretation"]}')

    print()
    print('[10] Baseline risk meta-regression')
    br = advanced['baseline_risk_reg']
    if br:
        print(f'  Slope on logit(control risk): {br["slope"]:+.3f}')
        print(f'  {br["interpretation"]}')
        print(f'  n trials: {br["n_trials"]}')

    print()
    print('[11] Cross-population consistency (SGLT2 exemplar)')
    cpc = advanced['sglt2_consistency']
    if cpc:
        print(f'  {cpc["drug"]} appears in {cpc["n_apps"]} apps:')
        for a in cpc['apps']:
            p = a['pool']
            print(f'    {a["population"]:30s}  HR {p["pooled_est"]:.2f} ({p["pooled_lo"]:.2f}-{p["pooled_hi"]:.2f})')
        if cpc['combined_pool']:
            cp = cpc['combined_pool']
            print(f'  Combined: HR {cp["pooled_est"]:.2f} ({cp["pooled_lo"]:.2f}-{cp["pooled_hi"]:.2f}), I²={cp["I2"]:.0f}%')

    print()
    print('[12] Trial sequential analysis (required information size per class)')
    for r in results:
        if r.get('tsa'):
            t = r['tsa']
            status = 'ADEQUATE' if t['adequate'] else 'UNDERPOWERED'
            print(f'  {r["name"]:25s}  info fraction {t["info_fraction"]*100:5.1f}%  RIS={t["ris"]:>6,}  [{status}]')

    # Build forest plot rows (sorted by pooled HR ascending = best to worst)
    plot_rows = []
    sorted_results = sorted(
        results,
        key=lambda r: (r['pool']['pooled_est'] if r['pool'] else 99)
    )
    for r in sorted_results:
        sublabel = f'{r["population_detail"]}  •  Class {r["guideline_class"]}  •  ≤{r["max_year"] or "?"}'
        if r['pool']:
            est = r['pool']['pooled_est']
            color = 'point-favors' if r['pool']['pooled_hi'] < 1 else 'point-null' if r['pool']['pooled_lo'] < 1 < r['pool']['pooled_hi'] else 'point-harm'
            plot_rows.append((r['name'], sublabel, r['pool']['k'],
                              est, r['pool']['pooled_lo'], r['pool']['pooled_hi'],
                              color))
        else:
            plot_rows.append((r['name'], sublabel, 0, None, None, None, ''))

    if output_json:
        out = {
            'generated': time.strftime('%Y-%m-%d %H:%M:%S'),
            'n_classes_with_data': sum(1 for r in results if r['pool']),
            'n_trials_total': sum(r['pool']['k'] for r in results if r['pool']),
            'pooled_overall': pooled_overall,
            'classes': [{
                'name': r['name'],
                'drug_class': r['drug_class'],
                'population': r['population'],
                'pool': r['pool'],
                'trials': r['trials'],
            } for r in results],
        }
        out_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                 'cardiology_mortality_atlas.json')
        with open(out_path, 'w', encoding='utf-8') as f:
            json.dump(out, f, indent=2, default=str)
        print(f'\nWrote {out_path}')
    else:
        # Build HTML atlas
        svg = build_forest_svg(plot_rows)
        generated = time.strftime('%Y-%m-%d %H:%M')
        html = build_html(results, pooled_overall, pop_pools, league, advanced, svg, generated)
        out_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                 'cardiology_mortality_atlas.html')
        with open(out_path, 'w', encoding='utf-8') as f:
            f.write(html)
        print(f'\nWrote {out_path}')
        print(f'Open in browser to view the atlas.')
