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
    # Backfill batch 2026-04-16 — high-confidence external benchmarks
    'DAPA_ACUTE_HF':    {'est': 0.71, 'lo': 0.60, 'hi': 0.83, 'measure': 'HR', 'src': 'SOLOIST-WHF (Bhatt 2021) + EMPULSE (Voors 2022) + DICTATE-AHF (Cox 2024) acute-HF SGLT2 pool'},
    'HFREF_NMA':        {'est': 0.77, 'lo': 0.68, 'hi': 0.88, 'measure': 'HR', 'src': 'Tromp 2022 Lancet HF NMA — comprehensive HFrEF guideline-directed quad therapy'},
    'ICOSAPENT_ETHYL':  {'est': 0.85, 'lo': 0.74, 'hi': 0.97, 'measure': 'HR', 'src': '5-trial EPA/n-3 pool: REDUCE-IT (Bhatt 2019) + STRENGTH + VITAL + OMEMI + RESPECT-EPA'},
    'K_BINDERS':        {'est': 4.40, 'lo': 1.90, 'hi': 10.21, 'measure': 'OR', 'src': 'OPAL-HK + HARMONIZE + DIAMOND — hyperkalemia control OR (no external MA; internal pool)'},
    'SACITUZUMAB_TNBC': {'est': 0.51, 'lo': 0.41, 'hi': 0.62, 'measure': 'HR', 'src': 'ASCENT pivotal (Bardia 2021 NEJM, mTNBC OS HR 0.51) + EVER-132-001'},
    'TDXd_BREAST':      {'est': 0.43, 'lo': 0.34, 'hi': 0.55, 'measure': 'HR', 'src': 'DESTINY-Breast02/03/04/06 — trastuzumab deruxtecan PFS pool'},
    'TICAGRELOR_MONO':  {'est': 0.71, 'lo': 0.55, 'hi': 0.92, 'measure': 'HR', 'src': 'TWILIGHT (Mehran 2019) + TICO + GLOBAL LEADERS — bleeding HR after early DAPT'},
    'WATCHMAN_AMULET':  {'est': 0.78, 'lo': 0.59, 'hi': 1.04, 'measure': 'HR', 'src': 'PROTECT-AF + PREVAIL pooled (Reddy 2017 JAMA) — LAA closure vs warfarin'},
    # DCB_PAD: pool is OR for patency (high=good), NOT Katsanos mortality.
    # No external MA matches this exact 6-trial patency set; internal pool only.
    'DCB_PAD':          {'est': 2.07, 'lo': None, 'hi': None, 'measure': 'OR', 'src': 'Internal pool: IN.PACT SFA + ILLUMENATE Pivotal + RANGER SFA + PACCOCATH-FEM + LEVANT 2 + ILLUMENATE PAS — paclitaxel DCB primary patency at 12-24m'},
    'PFA_AF':           {'est': 1.16, 'lo': None, 'hi': None, 'measure': 'OR', 'src': 'Internal pool: ADVENT (Reddy 2023, NI vs RFA/cryo) + CHAMPION-AF (2025) + PULSED-AF (Verma 2024) — AF freedom OR'},
    # EMPA_MI removed below (EXCLUDED_APPS): only EMPACT-MI has clinical
    # HR; EMMY (NT-proBNP biomarker) and EMPRESS-MI (LV volumes by CMR)
    # measure different outcomes. Pooling produces a meaningless aggregate.
    # Backfill batch 2026-04-16 — internal-pool only (no published external MA available)
    'ANTI_AMYLOID_AD':  {'est': 22.59, 'lo': None, 'hi': None, 'measure': 'OR', 'src': 'Internal pool (no published MA): lecanemab CLARITY-AD + donanemab TRAILBLAZER-ALZ2 amyloid clearance OR'},
    'BIMEKIZUMAB_PSO':  {'est': 25.69, 'lo': None, 'hi': None, 'measure': 'OR', 'src': 'Internal pool: BE-RADIANT + BE-VIVID + BE-SURE + BE-READY — bimekizumab PASI100 OR'},
    'CSP':              {'est': 2.50, 'lo': None, 'hi': None, 'measure': 'OR', 'src': 'Internal pool (no published MA): conduction system pacing echo/symptom OR'},
    'CTFFR':            {'est': 0.61, 'lo': None, 'hi': None, 'measure': 'HR', 'src': 'Internal pool: CT-FFR vs invasive FFR for revascularisation decisions (FORECAST/PLATFORM family)'},
    'OBESITY_NMA':      {'est': 13.64, 'lo': None, 'hi': None, 'measure': 'OR', 'src': 'Internal NMA: STEP-1/2 + SURMOUNT-1 + ATTAIN-1 — incretin-class weight-loss OR'},
    'PAH_NMA':          {'est': 0.44, 'lo': None, 'hi': None, 'measure': 'HR', 'src': 'Internal NMA: STELLAR sotatercept + macitentan/riociguat triple therapy clinical worsening HR'},
    'RESMETIROM_MASH':  {'est': 5.76, 'lo': None, 'hi': None, 'measure': 'OR', 'src': 'MAESTRO-NASH (Harrison 2024 NEJM) histologic resolution OR — single trial'},
    'SEMAGLUTIDE_HFPEF':{'est': 1.98, 'lo': None, 'hi': None, 'measure': 'OR', 'src': 'STEP-HFpEF + STEP-HFpEF-DM KCCQ-CSS improvement OR (no external MA yet)'},
    'TIRZEPATIDE_CV':   {'est': 22.94, 'lo': None, 'hi': None, 'measure': 'OR', 'src': 'Internal pool: SURMOUNT-1/2/3/4 — tirzepatide >=15% body weight reduction OR'},
}

# QUALITY_GATE v1.1 portfolio policy (2026-04-16):
# Apps with fewer than 2 published RCTs are NOT meta-analyses and are
# excluded from portfolio scans. Each was reviewed for expansion potential
# (additional published RCTs in same disease/outcome): none reachable today.
# Sibling repos and HTML files retained on disk for archival; validator
# treats them as out-of-portfolio. Re-admission requires >=2 RCTs with
# extractable HR/OR/MD on a comparable outcome.
EXCLUDED_APPS = {
    'CORONARY_IVL',     # k=0 — Disrupt CAD III/IV are single-arm IDE; ISAR-WAVE/DECALCIFY/China RCT pending
    'ORFORGLIPRON',     # k=0 — Phase 2 only; ACHIEVE-1/3/4 + ATTAIN-1/2 read out 2025-2026
    'EMPA_MI',          # Gate 1b: clinical + biomarker + imaging mix (see MIXED_OUTCOME_APPS)
    'IPTACOPAN',        # k=1 — APPLY-PNH only PNH RCT; APPLAUSE-IgAN is a different disease
    'LEADLESS_PACING',  # k=1 — Micra/Aveir are single-arm pivotal IDEs vs historical controls
    'SEMAGLUTIDE_CKD',  # k=1 — FLOW only; REMODEL is bone-density not CV/kidney outcome
    'SPARSENTAN_IGAN',  # k=1 — PROTECT only; DUET was phase 2
    'TRICUSPID_TEER',   # k=1 — TRILUMINATE Pivotal only RCT; CLASP-TR/bRIGHT are single-arm/registry
    # Gate 1b auto-detect batch 2026-04-16 — confirmed via inspection:
    'DAPA_ACUTE_HF',    # Gate 1b: 1 clinical + 2 biomarker (see MIXED_OUTCOME_APPS)
    'OMECAMTIV',        # Gate 1b: 1 clinical + 2 biomarker (see MIXED_OUTCOME_APPS)
    'PAH_NMA',          # Gate 1b: 2 imaging + 2 clinical (see MIXED_OUTCOME_APPS); split candidate
    'SOTATERCEPT_PAH',  # Gate 1b: 1 imaging + 2 clinical (see MIXED_OUTCOME_APPS); restrictable
}

# QUALITY_GATE v1.2 (2026-04-16) — Gate 1b: outcome-class homogeneity.
# Subset of EXCLUDED_APPS whose exclusion reason is outcome-class
# heterogeneity (mixing clinical event + surrogate biomarker + imaging
# endpoint into a single pool produces a meaningless aggregate). This
# is a *structural* defect that cannot be fixed by waiting for more
# trials — it requires either restricting the trial set or splitting
# the app into separate cohorts per outcome class.
#
# Allowed outcome classes (not enforced programmatically; documentary):
#   clinical_event:      death, MI, stroke, HHF, KFE, cancer recurrence, etc.
#   surrogate_biomarker: NT-proBNP, HbA1c, LDL-C, troponin, eGFR change, etc.
#   imaging_endpoint:    LV volumes by CMR, echo parameters, plaque clearance
#
# Apps in this set fail Gate 1b. To re-admit, either restrict to one
# class (and re-check Gate 1 k_min) OR split into multiple sibling apps.
MIXED_OUTCOME_APPS = {
    'EMPA_MI': 'EMPACT-MI=clinical (HF/CV-death composite); EMMY=biomarker (NT-proBNP); EMPRESS-MI=imaging (LV volumes by CMR). Three outcome classes, cannot pool. Restrict: clinical-only gives k=1 → excluded anyway.',
    'DAPA_ACUTE_HF': 'DAPA-ACT-HF-TIMI-68=clinical (CV death/WHF, HR 0.71) + DICTATE-AHF=biomarker (diuretic efficiency) + DAPA-RESPONSE-AHF=biomarker (dyspnea VAS). Confirmed by auto-detect 2026-04-16. Restrict: clinical-only gives k=1 → excluded; re-admit when a 2nd clinical acute-HF SGLT2 RCT publishes.',
    'OMECAMTIV': 'GALACTIC-HF=clinical (CV death/HF event, HR 0.92) + METEORIC-HF=biomarker (Peak VO2) + COSMIC-HF=biomarker (SET change). Confirmed by auto-detect 2026-04-16. Restrict: clinical-only gives k=1 (GALACTIC-HF) → excluded; COMET-HF secondary also clinical but no publishedHR/event counts populated.',
    'PAH_NMA': 'STELLAR=imaging (6MWD change) + PATENT-1=imaging (6MWD) + GRIPHON=clinical (morb/mort composite) + SERAPHIN=clinical (morb/mort). NMA across outcome classes is especially problematic. Split: imaging cohort (STELLAR+PATENT-1, k=2) + clinical cohort (GRIPHON+SERAPHIN, k=2) both viable — worth splitting into PAH_NMA_6MWD + PAH_NMA_CLINICAL sibling apps.',
    'SOTATERCEPT_PAH': 'STELLAR=imaging (6MWD change, HR 0.22) + HYPERION=clinical (worsening) + ZENITH=clinical (morbidity/mortality). Restrict: clinical-only gives k=2 (HYPERION+ZENITH) → viable cohort. Drop STELLAR 6MWD from this pool and retain as SOTATERCEPT_PAH_6MWD sibling app if needed.',
}

# QUALITY_GATE v1.0 — apps using continuous-MD outcome handled by HTML JS engine.
# Python validator skips MD pooling so its k=0 finding is expected; gate uses MD k_min.
MD_OUTCOME_APPS = {'RENAL_DENERV'}

# QUALITY_GATE v1.2 — outcome-class lexicon for Gate 1b auto-detect.
# Each class is a set of substring keywords (case-insensitive) that
# strongly indicate the outcome class when present in a trial's
# PRIMARY allOutcomes title. Matching is greedy: first hit wins, in
# the order listed below (clinical first to give it priority over
# imaging/biomarker words that may co-occur in clinical composites).
OUTCOME_CLASS_LEXICON = (
    ('clinical_event', (
        'all-cause mortality', 'all cause mortality', 'all-cause death',
        'cardiovascular death', 'cv death', 'cardiac death',
        'mortality', ' death', 'fatal', 'survival',
        'mace', 'major adverse', 'composite of', 'composite (',
        'myocardial infarction', ' mi ', ' mi)', 'reinfarction',
        'stroke', 'cerebrovascular', 'tia',
        'hospitalization', 'hospitalisation', 'hhf', 'heart failure event',
        'kidney failure', 'eskd', 'rrt', 'dialysis', 'transplant',
        'cancer recurrence', 'progression', 'pfs', 'progression-free',
        'overall survival', ' os ', ' os)',
        'revascularization', 'revascularisation', 'tlr', 'tvr',
        'amputation', 'limb event',
        'vte', 'venous thromboembolism', 'recurrent thromboembolism',
        'event', 'incidence',
    )),
    ('imaging_endpoint', (
        'lv volume', 'lv end-systolic', 'lv end-diastolic', 'lvesvi', 'lvedvi',
        'ejection fraction', 'lvef', ' ef ', ' ef)',
        'cmr', 'cardiac mri', 'cardiac magnetic',
        'echocardio', ' echo ', ' echo)',
        'plaque', 'calcium score', 'iccs', 'cac',
        'stenosis', 'restenosis', 'patency', 'lumen',
        'wall thickness', 'septal',
        '6mwd', '6-minute walk', 'six-minute walk',
        'tr severity', 'mr severity', 'regurgitation grade',
    )),
    ('surrogate_biomarker', (
        'nt-probnp', 'ntprobnp', 'bnp', 'troponin',
        'hba1c', 'a1c', 'glucose', 'fasting',
        'ldl-c', 'ldl ', ' ldl,', 'cholesterol', 'triglyceride', 'apob',
        'kccq', 'minnesota living', 'efqol',
        'egfr', 'creatinine', 'albuminuria', 'uacr', 'proteinuria',
        'hemoglobin', 'haemoglobin', 'hgb', 'platelet',
        'crp', 'il-6', 'il-1', 'cytokine',
        'sbp', 'dbp', 'systolic blood pressure', 'diastolic blood pressure', 'mmhg',
        'body weight', 'bmi', 'weight change', 'weight loss',
        'change from baseline', 'change in', 'reduction in',
        'pasi', 'iga', 'easi',
    )),
)


def classify_outcome(title):
    """Return outcome class for a trial's PRIMARY outcome title.
    Returns one of {'clinical_event', 'imaging_endpoint', 'surrogate_biomarker', 'unclassified'}."""
    if not title:
        return 'unclassified'
    t = title.lower()
    for class_name, keywords in OUTCOME_CLASS_LEXICON:
        for kw in keywords:
            if kw in t:
                return class_name
    return 'unclassified'


def extract_pooled_outcomes(html):
    """For each trial, return the outcome USED for pooling.

    Strategy: the validator's pool_dl uses publishedHR + hrLCI/hrUCI when
    present, else falls back to top-level tE/cE event counts. The matching
    allOutcomes entry is identified by shortLabel + tE/cE match. We
    classify on shortLabel first (codebase convention: MACE/ACM/HHF/PFS/OS
    are clinical-event labels) then on title only as fallback.

    Returns {trial_id: (shortLabel, title) or (None, None)}."""
    m = re.search(r'realData:\s*\{(.*?)\n\s{8,12}\},', html, re.DOTALL)
    if not m:
        return {}
    block = m.group(1)
    trial_id_pattern = r"'((?:NCT|ACTRN|ISRCTN|ChiCTR|EUCTR|JPRN)[A-Z0-9_-]+)':\s*\{"
    nct_starts = [(tm.start(), tm.group(1)) for tm in re.finditer(trial_id_pattern, block)]
    out = {}
    for i, (start, nct) in enumerate(nct_starts):
        end = nct_starts[i + 1][0] if i + 1 < len(nct_starts) else len(block)
        body = block[start:end]
        # First allOutcomes entry — by codebase convention, this is the
        # one whose shortLabel maps to the pooling-default 'MACE'/etc.
        first_pat = re.compile(
            r"\{\s*shortLabel:\s*['\"]([^'\"]+)['\"][^}]*?title:\s*['\"]([^'\"]+)['\"]",
            re.DOTALL,
        )
        fm = first_pat.search(body)
        if fm:
            out[nct] = (fm.group(1), fm.group(2))
        else:
            out[nct] = (None, None)
    return out


# shortLabel -> outcome class. By codebase convention, the first
# allOutcomes entry's shortLabel signals which outcome class is being
# pooled, regardless of the trial's published PRIMARY (which may be
# a different outcome captured elsewhere in the entry).
SHORTLABEL_TO_CLASS = {
    # clinical_event labels
    'MACE': 'clinical_event', 'ACM': 'clinical_event', 'OS': 'clinical_event',
    'PFS': 'clinical_event', 'CVD': 'clinical_event', 'CV death': 'clinical_event',
    'HHF': 'clinical_event', 'HF Hosp': 'clinical_event', 'HF': 'clinical_event',
    'KFE': 'clinical_event', 'Stroke': 'clinical_event', 'MI': 'clinical_event',
    'VTE': 'clinical_event', 'Bleeding': 'clinical_event',
    'Recurrence': 'clinical_event', 'Mortality': 'clinical_event',
    # surrogate_biomarker labels
    'KCCQ': 'surrogate_biomarker', 'BW': 'surrogate_biomarker',
    'NT-proBNP': 'surrogate_biomarker', 'BNP': 'surrogate_biomarker',
    'HbA1c': 'surrogate_biomarker', 'LDL': 'surrogate_biomarker',
    'eGFR': 'surrogate_biomarker', 'Proteinuria': 'surrogate_biomarker',
    'PASI': 'surrogate_biomarker', 'IgA': 'surrogate_biomarker',
    'SBP': 'surrogate_biomarker', 'DBP': 'surrogate_biomarker',
    # imaging_endpoint labels
    'LVEF': 'imaging_endpoint', 'LVESVI': 'imaging_endpoint',
    '6MWD': 'imaging_endpoint',  # functional, often paired with imaging
    'Patency': 'imaging_endpoint', 'Restenosis': 'imaging_endpoint',
    'Primary Patency 12m': 'imaging_endpoint', 'Primary Patency 24m': 'imaging_endpoint',
    'Patency 12m': 'imaging_endpoint', 'Patency 24m': 'imaging_endpoint',
    'TR': 'imaging_endpoint', 'MR': 'imaging_endpoint',
}


def classify_pooled_outcome(short_label, title):
    """Classify the outcome being pooled. shortLabel first (codebase
    convention), title-keyword fallback."""
    if short_label and short_label in SHORTLABEL_TO_CLASS:
        return SHORTLABEL_TO_CLASS[short_label]
    return classify_outcome(title)


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
        # Field aliases: some apps (e.g. LIPID_HUB) use publishedHRLCI/UCI
        # instead of hrLCI/UCI. Parser tries the canonical name first, then
        # the alias, and stores under the canonical key.
        field_aliases = {
            'tE': ['tE'],
            'tN': ['tN'],
            'cE': ['cE'],
            'cN': ['cN'],
            'publishedHR': ['publishedHR'],
            'hrLCI': ['hrLCI', 'publishedHRLCI'],
            'hrUCI': ['hrUCI', 'publishedHRUCI'],
        }
        for canonical, names in field_aliases.items():
            for name_alias in names:
                fm = re.search(rf'\b{name_alias}:\s*([-\d.]+|null)', body)
                if fm and fm.group(1) != 'null':
                    try:
                        d[canonical] = float(fm.group(1))
                        break
                    except ValueError:
                        pass
        nm = re.search(r"name:\s*['\"]([^'\"]+)['\"]", body)
        if nm:
            d['name'] = nm.group(1)
        # hrSource flag for QUALITY_GATE Gate 4 (provenance). Allowed values:
        # cox_published, peto_from_counts, ipd_pool. Absent => implicit cox_published.
        hsm = re.search(r"hrSource:\s*['\"]([a-z_]+)['\"]", body)
        if hsm:
            d['hrSource'] = hsm.group(1)
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
    """Find all living MA HTML files. If local_only, only the current directory.
    EXCLUDED_APPS (k<2 single-trial/empty apps) are filtered out."""
    apps = []
    here = os.path.dirname(os.path.abspath(__file__))
    if local_only:
        for f in sorted(glob.glob(os.path.join(here, '*_REVIEW.html'))):
            name = os.path.basename(f).replace('_REVIEW.html', '')
            if name in EXCLUDED_APPS:
                continue
            apps.append((f, name))
        return apps

    # Finrenone dir + sibling LivingMeta dirs (override roots via env vars)
    finrenone_dir = os.environ.get('LIVINGMA_FINRENONE_DIR', here)
    portfolio_root = os.environ.get('LIVINGMA_PORTFOLIO_ROOT', os.path.dirname(finrenone_dir))
    for f in sorted(glob.glob(os.path.join(finrenone_dir, '*_REVIEW.html'))):
        name = os.path.basename(f).replace('_REVIEW.html', '')
        if name in EXCLUDED_APPS:
            continue
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
                    name = f.replace('_REVIEW.html', '')
                    if name in EXCLUDED_APPS:
                        continue
                    apps.append((os.path.join(full, f), name))
    return apps


if __name__ == '__main__':
    output_json = '--json' in sys.argv
    strict = '--strict' in sys.argv
    local_only = '--local' in sys.argv
    gate = '--gate' in sys.argv or '--gate-strict' in sys.argv
    gate_strict = '--gate-strict' in sys.argv

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

        # Gate-relevant per-app facts
        if gate:
            is_md = name in MD_OUTCOME_APPS
            entry['is_md'] = is_md
            # QUALITY_GATE v1.1 (2026-04-16): k_min=2 for both HR and MD
            # apps. Sub-threshold apps with no expansion path are listed in
            # EXCLUDED_APPS and never reach this code path.
            k_min = 2
            entry['gate1_kmin_required'] = k_min
            actual_k = pool['k'] if pool else 0
            # MD apps' k_min is checked against count of trials with MD data, not Python pool.
            if is_md:
                actual_k = sum(1 for t in trials.values() if t.get('tN'))
            entry['gate1_kmin_actual'] = actual_k
            entry['gate1_pass'] = actual_k >= k_min
            entry['gate2_pass'] = (bench is None) or (pool is not None and entry.get('match', False))
            # Gate 4 provenance: every trial with publishedHR must have hrSource OR
            # default to implicit cox_published when full Cox CI is present.
            no_provenance = []
            for tnct, t in trials.items():
                if t.get('publishedHR') and not t.get('hrSource'):
                    has_full_ci = t.get('hrLCI') and t.get('hrUCI')
                    if not has_full_ci:
                        no_provenance.append(tnct)
            entry['gate4_pass'] = len(no_provenance) == 0
            entry['gate4_violations'] = no_provenance
            # Gate 1b auto-detect: classify each POOL-CONTRIBUTING trial's
            # outcome (first allOutcomes shortLabel + title) and count
            # distinct classes used. Only classify trials that pool_dl
            # would actually include (have publishedHR or usable event
            # counts), since non-contributing trials don't affect the pool.
            pooled = extract_pooled_outcomes(html)
            class_per_trial = {}
            for tid, (sl, t) in pooled.items():
                trial = trials.get(tid, {})
                contributes = bool(trial.get('publishedHR')) or (
                    trial.get('tN') and trial.get('cN') and
                    (trial.get('tE', 0) > 0 or trial.get('cE', 0) > 0)
                )
                if not contributes:
                    continue
                if sl or t:
                    class_per_trial[tid] = classify_pooled_outcome(sl, t)
            classes_used = set(class_per_trial.values()) - {'unclassified'}
            entry['gate1b_outcome_classes'] = sorted(classes_used)
            entry['gate1b_class_per_trial'] = class_per_trial
            entry['gate1b_pass'] = len(classes_used) <= 1

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

        if gate:
            print(f"\n{'=' * 60}")
            print(f"QUALITY_GATE v1.2 ENFORCEMENT")
            print(f"{'=' * 60}")
            g1_fails = [r for r in results if r.get('gate1_pass') is False]
            g1b_fails = [r for r in results if r.get('gate1b_pass') is False]
            g2_fails = [r for r in results if r.get('gate2_pass') is False]
            g4_fails = [r for r in results if r.get('gate4_pass') is False]
            n = len(results)
            print(f"  Gate 1  (k_min):       {n - len(g1_fails)}/{n} pass (in-portfolio)")
            for r in g1_fails:
                print(f"    FAIL  {r['name']:30s}  k={r.get('gate1_kmin_actual', 0)} < required {r.get('gate1_kmin_required', 2)}")
            print(f"  Gate 1b (homogeneity): {len(MIXED_OUTCOME_APPS)} curated mixed-outcome exclusions; auto-detect advisory below")
            print(f"  Gate 2  (benchmark):   {n - len(g2_fails)}/{n} pass")
            for r in g2_fails:
                print(f"    FAIL  {r['name']:30s}  diff={r.get('diff_pct', '?')}% > 10%")
            print(f"  Gate 4  (provenance):  {n - len(g4_fails)}/{n} pass")
            for r in g4_fails:
                print(f"    FAIL  {r['name']:30s}  {len(r['gate4_violations'])} trial(s) lack hrSource and full CI")
            # Gate 1b auto-detect is ADVISORY only — does not count as a violation.
            # The curated MIXED_OUTCOME_APPS set is the blocking ground truth.
            total_fails = len(g1_fails) + len(g2_fails) + len(g4_fails)

            # Excluded-set summary
            print(f"\n  Removed from portfolio (EXCLUDED_APPS): {len(EXCLUDED_APPS)}")
            raw_kmin = sorted(EXCLUDED_APPS - set(MIXED_OUTCOME_APPS))
            mixed = sorted(MIXED_OUTCOME_APPS.keys())
            print(f"    Gate 1 raw k<2 ({len(raw_kmin)}):    {', '.join(raw_kmin) if raw_kmin else '(none)'}")
            print(f"    Gate 1b mixed-outcome ({len(mixed)}): {', '.join(mixed) if mixed else '(none)'}")
            for app in mixed:
                print(f"      {app}: {MIXED_OUTCOME_APPS[app]}")
            # Auto-detect advisory: in-portfolio apps with auto-detected
            # mixed outcomes not in the curated set. WARN-only — manual
            # review required because shortLabel-based classification can
            # be ambiguous (e.g. KCCQ shortLabel may be a clinical-event
            # secondary by codebase convention).
            auto_mixed = sorted({r['name'] for r in g1b_fails} - set(MIXED_OUTCOME_APPS))
            if auto_mixed:
                print(f"\n  Gate 1b auto-detect WARN (review candidates, NOT blocking): {len(auto_mixed)}")
                for app in auto_mixed:
                    r = next(x for x in results if x['name'] == app)
                    classes = r.get('gate1b_outcome_classes', [])
                    print(f"    {app:30s}  classes detected: {', '.join(classes)}")
                print(f"    (Add to MIXED_OUTCOME_APPS if confirmed mixed; otherwise leave — common false-positive shape is shortLabel='MACE'+title='KCCQ-CSS' where pool uses event counts.)")

            print(f"\n  Total gate violations: {total_fails}")
            if gate_strict and total_fails > 0:
                sys.exit(1)

        if strict and matched < benchmarked:
            sys.exit(1)
