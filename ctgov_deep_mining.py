#!/usr/bin/env python
"""
CT.gov Deep Mining for the Cardiology Mortality Atlas

For each NCT in the cardiology portfolio, fetches the full CT.gov v2 record
and extracts ALL mortality-related outcomes:
  - All-cause mortality (ACM)
  - Cardiovascular death
  - Heart failure hospitalization
  - Composite CV death or HF hospitalization
  - Primary endpoint HR

For each outcome, extracts the HR/RR/OR analysis with CI, p-value, method,
and provenance (outcome measure ID, group IDs).

Output:
  ctgov_mining_results.json  — per-trial structured results
  ctgov_mining_gaps.md       — gaps in current atlas data
  ctgov_mining_new_trials.md — trials found in CT.gov not yet in atlas

Run: python ctgov_deep_mining.py [--only APP] [--resume]
"""
import datetime
import json
import math
import os
import re
import subprocess
import sys
import time
from urllib.request import urlopen, Request
from urllib.error import URLError, HTTPError

from _io_utils import BASE_DIR, ensure_utf8_stdout, is_valid_nct, md_cell

ensure_utf8_stdout()

# ─── Constants (extracted from magic numbers per code review) ───
CT_GOV_API = 'https://clinicaltrials.gov/api/v2/studies/'
USER_AGENT = 'RapidMeta-MortalityMining/1.0'

# Network / rate-limiting
REQUEST_TIMEOUT_S = 30
REQUEST_DELAY_S = 0.3        # base delay between CT.gov calls
MAX_RETRIES = 2              # network retries per study
RETRY_BASE_DELAY_S = 1.0     # exponential backoff base
CHECKPOINT_EVERY = 10        # save partial results every N studies

# Statistical guards
MIN_ARM_SIZE = 5              # below this, Peto variance is unreliable
MAX_MORTALITY_RATE = 0.5      # event rate >50% means it's NOT a mortality outcome
DISCREPANCY_PCT_THRESHOLD = 5.0  # atlas vs CT.gov diff threshold

# Resolved file paths (cwd-independent)
RESULTS_PATH = BASE_DIR / 'ctgov_mining_results.json'
INVENTORY_PATH = BASE_DIR / 'ctgov_mining_inventory.json'
GAPS_REPORT_PATH = BASE_DIR / 'ctgov_mining_gaps.md'
ATLAS_JSON_PATH = BASE_DIR / 'cardiology_mortality_atlas.json'

# Outcome title patterns — normalized lowercase matching
OUTCOME_PATTERNS = {
    'ACM': [
        'all-cause mortality', 'all cause mortality', 'all-cause death',
        'death from any cause', 'total mortality', 'overall mortality',
        'all-cause survival',
        # Pre-2010 CT.gov shorthand titles. NOTE: bare 'death'/'deaths' would
        # match "Cardiovascular Death" too — handled by ordered classification
        # below (CV_death is checked first) and word-boundary matching.
        'number of deaths', 'deaths (all causes)', 'all deaths',
    ],
    'CV_death': [
        'cardiovascular death', 'cardiovascular mortality', 'cv death',
        'cardiovascular-related death', 'death from cardiovascular',
        'cv mortality', 'death due to cardiovascular',
        'death from cardiovascular causes',
    ],
    'HF_hosp': [
        'heart failure hospitalization', 'heart failure hospitalisation',
        'hf hospitalization', 'hf hospitalisation',
        'hospitalization for heart failure', 'hospitalisation for heart failure',
        'hospitalization for hf', 'hospitalisation for hf',
        'hospitalization for worsening heart failure',
        'hospitalisation for worsening heart failure',
        'heart failure requiring hospitalization',
        'heart failure requiring hospitalisation',
    ],
    'CV_composite': [
        'cardiovascular death or heart failure',
        'cv death or hf hospitalization',
        'composite of cv death',
        'cardiovascular death or hospitalization',
        'cv death or worsening heart failure',
    ],
}

# Control-arm title markers (case-insensitive substring match)
CONTROL_MARKERS = (
    'placebo', 'control', 'standard of care', 'standard care',
    'usual care', 'sham', 'comparator', 'best supportive',
)

# "Pooled" / collapsed experimental arm markers — for multi-dose trials
# where CT.gov reports an aggregate "All [Drug]" group alongside dose arms.
POOLED_MARKERS = ('all ', 'total ', 'pooled', 'combined')


def peto_hr_from_counts(events_e, n_e, events_c, n_c):
    """Peto 1-step log-rank HR from a 2x2 event table.

    Returns (hr, lci, uci, se_log) or None if computation infeasible.

    Formula (Peto 1977 / Yusuf 1985):
        O_e = events in experimental arm (observed)
        E_e = (events_total) * n_e / n_total                (expected)
        V_e = (events_total * (n_total - events_total) * n_e * n_c)
              / (n_total^2 * (n_total - 1))                 (hypergeometric var)
        logHR ≈ (O_e - E_e) / V_e
        SE(logHR) = 1 / sqrt(V_e)

    Validated against EMPA-REG HF hosp:
        96/2333 vs 127/4687 → HR 0.63 (0.48-0.84)  vs reported 0.65 (0.50-0.85)
    """
    import math
    try:
        events_e = int(round(events_e))
        events_c = int(round(events_c))
        n_e = int(n_e)
        n_c = int(n_c)
    except (TypeError, ValueError):
        return None

    if min(n_e, n_c) < 5:
        return None
    events_total = events_e + events_c
    n_total = n_e + n_c
    if events_total == 0 or events_total >= n_total:
        return None
    if n_total < 2:
        return None

    e_expected = events_total * n_e / n_total
    variance = (events_total * (n_total - events_total) * n_e * n_c
                / (n_total * n_total * (n_total - 1)))
    if variance <= 0:
        return None

    log_hr = (events_e - e_expected) / variance
    se = 1.0 / math.sqrt(variance)
    hr = math.exp(log_hr)
    lci = math.exp(log_hr - 1.96 * se)
    uci = math.exp(log_hr + 1.96 * se)
    return (hr, lci, uci, se)


def extract_arm_counts(outcome_measure):
    """From an outcomeMeasure, return list of {id, title, events, n}.

    Handles 'percentage of participants', 'number of participants',
    'participants' unit-of-measure variants. Multiplies/rounds correctly.
    """
    om = outcome_measure
    unit = (om.get('unitOfMeasure') or '').lower()
    is_percent = 'percent' in unit or '%' in unit

    # Build group_id → n mapping from denoms
    denom_map = {}
    for d in om.get('denoms', []) or []:
        d_units = (d.get('units') or '').lower()
        if 'participant' not in d_units:
            continue
        for c in d.get('counts', []) or []:
            try:
                denom_map[c.get('groupId')] = int(c.get('value'))
            except (TypeError, ValueError):
                pass

    # Build group_id → title from groups
    group_titles = {g.get('id'): g.get('title', '') for g in om.get('groups', []) or []}

    # Read measurements from first class/category (mortality outcomes are flat)
    arm_counts = {}
    classes = om.get('classes', []) or []
    if not classes:
        return []
    for cl in classes:
        for cat in cl.get('categories', []) or []:
            for m in cat.get('measurements', []) or []:
                gid = m.get('groupId')
                try:
                    val = float(m.get('value'))
                except (TypeError, ValueError):
                    continue
                # Reject NaN/inf — would propagate into Peto computation
                if not math.isfinite(val):
                    continue
                n_arm = denom_map.get(gid)
                if n_arm is None or n_arm <= 0:
                    continue
                if is_percent:
                    events = round(val / 100.0 * n_arm)
                else:
                    # treat as count
                    events = round(val)
                # Only keep first measurement per group (don't overwrite)
                if gid not in arm_counts:
                    arm_counts[gid] = {
                        'id': gid,
                        'title': group_titles.get(gid, ''),
                        'events': events,
                        'n': n_arm,
                    }
    return list(arm_counts.values())


def select_2arm_pair(arms):
    """Pick (control, experimental) from a list of arms.

    Strategy:
      1. Find control arm by title keyword match.
      2. For experimental: prefer a sponsor-supplied 'pooled/all' collapsed
         arm if present, else the single non-control arm.

    REFUSES (returns None) when there are multiple non-control non-pooled
    dose arms with no sponsor-supplied collapsed group. Ad-hoc summing of
    independent dose arms breaks randomization preservation and biases
    the marginal HR — caller should fall back to a different outcome.
    """
    if len(arms) < 2:
        return None
    controls = []
    others = []
    for a in arms:
        title = (a.get('title') or '').lower()
        if any(m in title for m in CONTROL_MARKERS):
            controls.append(a)
        else:
            others.append(a)

    if not controls or not others:
        return None
    # Use the largest control (in case of multiple)
    control = max(controls, key=lambda a: a['n'])

    # Look for sponsor-supplied pooled/collapsed experimental
    pooled = [a for a in others if any(m in (a.get('title') or '').lower() for m in POOLED_MARKERS)]
    if pooled:
        experimental = max(pooled, key=lambda a: a['n'])
    elif len(others) == 1:
        experimental = others[0]
    else:
        # Multi-dose trial without a sponsor-supplied collapsed arm.
        # Refuse rather than fabricate one (would break randomization
        # preservation and shared-control variance accounting).
        return None
    return control, experimental


EFFECT_MAP = {
    'hazard ratio': 'HR',
    'hazard ratio (hr)': 'HR',
    'risk ratio': 'RR',
    'risk ratio (rr)': 'RR',
    'odds ratio': 'OR',
    'odds ratio (or)': 'OR',
    'relative risk': 'RR',
}


# "X or Y" composite detector — only flags as composite when "or" is followed
# by a clinical endpoint, not stylistic uses like "deaths or censoring".
_COMPOSITE_OR_RE = re.compile(
    r'\bor\s+(hosp|mi|myocardial|stroke|rehosp|hf|heart failure|revasc|'
    r'amputation|worsening|nonfatal|non-fatal|cardiovascular|death|mortality)',
    re.IGNORECASE,
)

# Standalone "death" or "deaths" — used as ACM fallback for pre-2010 trials
# where the outcome is just titled "Death". Does NOT match phrases like
# "cardiovascular death" (which is checked first in the ordered classifier).
_BARE_DEATH_RE = re.compile(r'^\s*deaths?\s*$', re.IGNORECASE)


def classify_outcome(title):
    """Return tag (ACM, CV_death, HF_hosp, CV_composite, primary, other).

    STRICT MODE: rejects composite outcomes (MACE-type) that happen to
    mention all-cause death as a component. Only matches outcomes whose
    title is a clean ACM / CV death / HF hosp report.
    """
    if not title:
        return None
    t = title.lower().strip()

    # Composite markers — if present, this is not a pure single outcome.
    # NOTE: ' or ' substring is too greedy (catches "deaths or censoring");
    # use _COMPOSITE_OR_RE below to require a clinical second endpoint.
    composite_markers = [
        'composite', 'first occurrence', 'time to first',
        'mace', 'non-fatal', 'nonfatal',
        'stroke', 'myocardial infarction',
        '3-point', '4-point', 'three-point', 'four-point',
        '3p-mace', '4p-mace',
        # Hierarchical / win-ratio composites (Finkelstein-Schoenfeld, Pocock)
        'hierarchical', 'win ratio', 'win-ratio', 'finkelstein',
        'change from baseline', 'cumulative frequency',
        # Recurrent-event / composite-with-death markers
        'hf event', 'hf events', 'heart failure event',
        'recurrent', 'and all-cause death', 'and death',
        'number of events', 'total events',
    ]

    is_composite = any(m in t for m in composite_markers) or bool(_COMPOSITE_OR_RE.search(t))

    # CV composite is allowed to contain "or"
    if any(p in t for p in OUTCOME_PATTERNS['CV_composite']):
        return 'CV_composite'

    if is_composite:
        return None

    # ORDER MATTERS: check more specific tags before ACM. "Cardiovascular Death"
    # should match CV_death, not ACM via the bare-'death' fallback patterns.
    if any(p in t for p in OUTCOME_PATTERNS['CV_death']):
        return 'CV_death'
    if any(p in t for p in OUTCOME_PATTERNS['HF_hosp']):
        return 'HF_hosp'
    # ACM patterns last — includes generic 'death' / 'deaths' fallback
    if any(p in t for p in OUTCOME_PATTERNS['ACM']):
        return 'ACM'
    # Fallback word-boundary match for older CT.gov titles like just "Death"
    if _BARE_DEATH_RE.search(t):
        return 'ACM'

    return None


def normalize_param(s):
    if not s:
        return None
    return EFFECT_MAP.get(s.lower().strip())


def fetch_study(nct_id, retries=MAX_RETRIES):
    """Fetch a CT.gov v2 study record. Validates NCT format, honors HTTP 429."""
    if not is_valid_nct(nct_id):
        return {'error': f'invalid_nct: {nct_id!r}'}
    url = f'{CT_GOV_API}{nct_id}?format=json'
    req = Request(url, headers={'User-Agent': USER_AGENT, 'Accept': 'application/json'})
    for attempt in range(retries + 1):
        try:
            with urlopen(req, timeout=REQUEST_TIMEOUT_S) as resp:
                return json.loads(resp.read().decode('utf-8'))
        except HTTPError as e:
            # Honor Retry-After on 429 / 503
            if e.code in (429, 503):
                retry_after = e.headers.get('Retry-After') if e.headers else None
                try:
                    delay = float(retry_after) if retry_after else RETRY_BASE_DELAY_S * (2 ** attempt)
                except (TypeError, ValueError):
                    delay = RETRY_BASE_DELAY_S * (2 ** attempt)
                if attempt < retries:
                    time.sleep(min(delay, 60))
                    continue
            elif attempt < retries and e.code >= 500:
                time.sleep(RETRY_BASE_DELAY_S * (2 ** attempt))
                continue
            return {'error': f'HTTP {e.code}: {e.reason}'}
        except (URLError, TimeoutError, OSError, json.JSONDecodeError) as e:
            if attempt < retries:
                time.sleep(RETRY_BASE_DELAY_S * (2 ** attempt))
                continue
            return {'error': str(e)}
    return {'error': 'retry_exhausted'}


def extract_all_mortality_outcomes(study):
    """Parse a CT.gov v2 study and extract all mortality-related outcomes.

    Returns dict:
      {
        'nct': ...,
        'title': ...,
        'has_results': bool,
        'outcomes': {
          'ACM': {measure, est, lci, uci, pValue, method, outcome_id, outcome_title},
          'CV_death': {...},
          'HF_hosp': {...},
          'CV_composite': {...},
          'primary': {...},
        },
        'enrollment': int,
        'groups': [...],
      }
    """
    proto = study.get('protocolSection', {})
    ident = proto.get('identificationModule', {})
    nct = ident.get('nctId')
    status_module = proto.get('statusModule', {})
    out = {
        'nct': nct,
        'title': ident.get('briefTitle', ''),
        'acronym': ident.get('acronym', ''),
        'phase': ', '.join(proto.get('designModule', {}).get('phases', [])),
        'enrollment': proto.get('designModule', {}).get('enrollmentInfo', {}).get('count'),
        'sponsor': proto.get('sponsorCollaboratorsModule', {}).get('leadSponsor', {}).get('name', ''),
        'status': status_module.get('overallStatus', ''),
        'completion_date': status_module.get('primaryCompletionDateStruct', {}).get('date', ''),
        # CT.gov last update timestamp — drives change detection on re-runs
        'last_update_post': status_module.get('lastUpdatePostDateStruct', {}).get('date', ''),
        # ISO-8601 retrieval timestamp — required for PRISMA 2020 item 7
        'retrieved_at': datetime.datetime.utcnow().isoformat() + 'Z',
        'has_results': bool(study.get('hasResults')),
        'outcomes': {},
    }

    if not out['has_results']:
        return out

    results = study.get('resultsSection', {})
    om_list = results.get('outcomeMeasuresModule', {}).get('outcomeMeasures', [])

    # Find primary outcome (first PRIMARY)
    primary_idx = None
    for i, om in enumerate(om_list):
        if om.get('type') == 'PRIMARY':
            primary_idx = i
            break

    # Walk all outcomes — collect ALL matches then pick the most specific per tag
    candidates_by_tag = {}  # tag -> list of (specificity_score, extracted dict)

    for i, om in enumerate(om_list):
        title = om.get('title', '')
        tag = classify_outcome(title)

        extracted = None
        # First try CT.gov-supplied analyses (HR/RR/OR with CI)
        for analysis in om.get('analyses', []):
            param = normalize_param(analysis.get('paramType'))
            if param in ('HR', 'RR', 'OR'):
                try:
                    extracted = {
                        'measure': param,
                        'est': float(analysis.get('paramValue')),
                        'lci': float(analysis.get('ciLowerLimit')),
                        'uci': float(analysis.get('ciUpperLimit')),
                        'pValue': analysis.get('pValue'),
                        'method': analysis.get('statisticalMethod', ''),
                        'source': 'analyses',
                        'outcome_id': om.get('id'),
                        'outcome_title': title,
                        'outcome_type': om.get('type'),
                    }
                    break
                except (TypeError, ValueError):
                    continue

        # Peto gap-fill: if outcome was tagged ACM/CV_death/HF_hosp but no
        # CT.gov analysis HR exists, derive HR from arm-level event counts
        if extracted is None and tag in ('ACM', 'CV_death', 'HF_hosp'):
            arms = extract_arm_counts(om)
            pair = select_2arm_pair(arms)
            if pair:
                control, experimental = pair
                # Sanity check: ACM/CV-death event rate >MAX_MORTALITY_RATE
                # means this isn't really a mortality outcome (cardiology
                # trials typically <30% even at long follow-up). Reject — usually
                # a mis-tagged composite/hierarchical endpoint.
                rate_e = experimental['events'] / max(1, experimental['n'])
                rate_c = control['events'] / max(1, control['n'])
                if rate_e > MAX_MORTALITY_RATE or rate_c > MAX_MORTALITY_RATE:
                    pair = None
            if pair:
                control, experimental = pair
                peto = peto_hr_from_counts(
                    experimental['events'], experimental['n'],
                    control['events'], control['n'],
                )
                if peto:
                    hr, lci, uci, se = peto
                    extracted = {
                        'measure': 'HR',
                        'est': round(hr, 4),
                        'lci': round(lci, 4),
                        'uci': round(uci, 4),
                        'pValue': None,
                        'method': 'Peto 1-step log-rank from arm counts',
                        'source': 'peto_logrank',
                        'events_e': experimental['events'],
                        'n_e': experimental['n'],
                        'events_c': control['events'],
                        'n_c': control['n'],
                        'control_arm': control['title'],
                        'experimental_arm': experimental['title'],
                        'outcome_id': om.get('id'),
                        'outcome_title': title,
                        'outcome_type': om.get('type'),
                    }

        if i == primary_idx and extracted:
            out['outcomes']['primary'] = extracted

        if tag and extracted:
            # Specificity score: shorter, cleaner titles score higher
            # Prefer titles starting with the target phrase
            title_lower = title.lower().strip()
            score = 100 - len(title_lower)  # shorter wins
            if tag == 'ACM' and title_lower.startswith(('all-cause', 'all cause', 'overall')):
                score += 50
            if tag == 'CV_death' and title_lower.startswith(('cardiovascular death', 'cv death')):
                score += 50
            # Slight penalty for Peto-derived (prefer adjudicated CT.gov HR)
            if extracted.get('source') == 'peto_logrank':
                score -= 5
            candidates_by_tag.setdefault(tag, []).append((score, extracted))

    # Pick the highest-scoring match per tag (deterministic tie-break by outcome_id)
    for tag, candidates in candidates_by_tag.items():
        best = max(candidates, key=lambda x: (x[0], x[1].get('outcome_id') or ''))
        out['outcomes'][tag] = best[1]

    # Also get group sizes from the first outcome's denoms
    if om_list:
        denoms = om_list[0].get('denoms', [])
        if denoms:
            out['groups'] = [{'id': c.get('groupId'), 'n': int(c.get('value', 0))}
                             for c in denoms[0].get('counts', [])]

    return out


def load_inventory():
    with open(INVENTORY_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)


def compare_with_atlas(mining_results):
    """Compare mined data against current atlas values; flag discrepancies and gaps."""
    # Load atlas JSON; rebuild it via subprocess (no shell) if missing
    if not ATLAS_JSON_PATH.exists():
        subprocess.run(
            [sys.executable, str(BASE_DIR / 'cardiology_mortality_atlas.py'), '--json'],
            cwd=str(BASE_DIR),
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            check=False,
        )
    if not ATLAS_JSON_PATH.exists():
        return None

    with open(ATLAS_JSON_PATH, 'r', encoding='utf-8') as f:
        atlas = json.load(f)

    gaps = []
    verifications = []

    for cls in atlas.get('classes', []):
        app_name = cls['name']
        for trial in cls.get('trials', []):
            nct = trial.get('nct')
            if not nct:
                continue
            mined = mining_results.get(nct)
            if not mined or not mined.get('has_results'):
                continue
            mined_acm = mined['outcomes'].get('ACM')
            atlas_hr = trial.get('hr')
            # Use `is not None` so HR == 0.0 (impossible but principled) isn't dropped
            if mined_acm is not None and atlas_hr is not None and atlas_hr > 0:
                pct_diff = abs(mined_acm['est'] - atlas_hr) / atlas_hr * 100
                if pct_diff > DISCREPANCY_PCT_THRESHOLD:
                    verifications.append({
                        'app': app_name, 'nct': nct,
                        'atlas_hr': atlas_hr,
                        'ctgov_hr': mined_acm['est'],
                        'pct_diff': pct_diff,
                    })
            # Check for NEW ACM data where atlas has none
            if atlas_hr is None and mined_acm is not None:
                gaps.append({
                    'app': app_name, 'nct': nct, 'trial': trial.get('name', nct),
                    'new_acm_hr': mined_acm['est'],
                    'new_acm_ci': f'{mined_acm["lci"]}-{mined_acm["uci"]}',
                    'source': mined_acm.get('outcome_title', '')[:60],
                })

    return {'verifications': verifications, 'gaps': gaps}


# ═══════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════

if __name__ == '__main__':
    target_app = None
    resume = '--resume' in sys.argv
    for i, arg in enumerate(sys.argv):
        if arg == '--only' and i + 1 < len(sys.argv):
            target_app = sys.argv[i + 1]

    inventory = load_inventory()

    # Flatten to NCT -> [apps that include it], skipping invalid NCT IDs
    nct_to_apps = {}
    skipped_invalid = []
    for app, ncts in inventory.items():
        if target_app and target_app.upper() not in app.upper():
            continue
        for nct in ncts:
            if not is_valid_nct(nct):
                skipped_invalid.append((app, nct))
                continue
            nct_to_apps.setdefault(nct, []).append(app)

    if skipped_invalid:
        print(f'Skipped {len(skipped_invalid)} invalid NCT IDs:')
        for app, nct in skipped_invalid:
            print(f'  {app}: {nct!r}')

    print(f'Mining {len(nct_to_apps)} unique NCT IDs across {len(inventory)} cardiology apps')
    print()

    # Resume support
    mining_results = {}
    if resume and RESULTS_PATH.exists():
        with open(RESULTS_PATH, 'r', encoding='utf-8') as f:
            mining_results = json.load(f)
        print(f'Resumed with {len(mining_results)} previously mined NCTs')

    # Mine each NCT
    to_mine = [n for n in sorted(nct_to_apps.keys()) if n not in mining_results]
    print(f'Mining {len(to_mine)} new NCTs...')
    print()

    acm_found = 0
    cvd_found = 0
    hfh_found = 0
    primary_found = 0
    no_results = 0
    errors = 0

    for i, nct in enumerate(to_mine):
        apps = nct_to_apps[nct]
        print(f'[{i+1}/{len(to_mine)}] {nct} ({apps[0]})...', end=' ', flush=True)

        study = fetch_study(nct)
        if 'error' in study:
            print(f'ERROR')
            mining_results[nct] = {'nct': nct, 'error': study['error'], 'apps': apps}
            errors += 1
            continue

        extracted = extract_all_mortality_outcomes(study)
        extracted['apps'] = apps
        mining_results[nct] = extracted

        if not extracted['has_results']:
            print('no results')
            no_results += 1
        else:
            tags = list(extracted['outcomes'].keys())
            if 'ACM' in tags:
                acm_found += 1
            if 'CV_death' in tags:
                cvd_found += 1
            if 'HF_hosp' in tags:
                hfh_found += 1
            if 'primary' in tags:
                primary_found += 1
            print(f'[{", ".join(tags)}]')

        # Save incrementally every CHECKPOINT_EVERY studies
        if (i + 1) % CHECKPOINT_EVERY == 0:
            with open(RESULTS_PATH, 'w', encoding='utf-8') as f:
                json.dump(mining_results, f, indent=2, default=str)

        time.sleep(REQUEST_DELAY_S)

    # Final save
    with open(RESULTS_PATH, 'w', encoding='utf-8') as f:
        json.dump(mining_results, f, indent=2, default=str)

    print()
    print('=' * 60)
    print('MINING SUMMARY')
    print('=' * 60)
    print(f'  Total NCTs mined:  {len(mining_results)}')
    print(f'  With results:      {len(mining_results) - no_results - errors}')
    print(f'  ACM extracted:     {acm_found}')
    print(f'  CV death:          {cvd_found}')
    print(f'  HF hosp:           {hfh_found}')
    print(f'  Primary endpoint:  {primary_found}')
    print(f'  No results posted: {no_results}')
    print(f'  Errors:            {errors}')
    print()

    # PRISMA exclusion log: NCTs with results posted but no extractable
    # mortality outcome (per PRISMA 2020 item 16b — exclusion reasons).
    prisma_exclusions = []
    for nct, info in mining_results.items():
        if info.get('error'):
            prisma_exclusions.append({
                'nct': nct, 'reason': 'fetch_error',
                'detail': info.get('error', ''),
            })
            continue
        if not info.get('has_results'):
            prisma_exclusions.append({
                'nct': nct, 'reason': 'no_results_posted',
                'detail': f'status={info.get("status","?")}',
            })
            continue
        outs = info.get('outcomes') or {}
        if not any(t in outs for t in ('ACM', 'CV_death', 'HF_hosp')):
            prisma_exclusions.append({
                'nct': nct, 'reason': 'no_mortality_outcome',
                'detail': f'has primary={"primary" in outs}, has CV_composite={"CV_composite" in outs}',
            })

    prisma_path = BASE_DIR / 'ctgov_prisma_exclusions.md'
    with open(prisma_path, 'w', encoding='utf-8') as f:
        f.write('# CT.gov Mining — PRISMA Exclusion Log\n\n')
        f.write(f'Generated: {time.strftime("%Y-%m-%d %H:%M:%S UTC")}\n\n')
        f.write(f'**Records identified:** {len(mining_results)}\n')
        f.write(f'**Records included (with extractable mortality outcome):** '
                f'{len(mining_results) - len(prisma_exclusions)}\n')
        f.write(f'**Records excluded:** {len(prisma_exclusions)}\n\n')
        f.write('## Exclusion reasons\n\n')
        from collections import Counter
        reason_counts = Counter(e['reason'] for e in prisma_exclusions)
        for reason, n in reason_counts.most_common():
            f.write(f'- **{reason}**: {n}\n')
        f.write('\n## Excluded NCTs\n\n| NCT | Reason | Detail |\n|---|---|---|\n')
        for e in prisma_exclusions:
            f.write(f'| {md_cell(e["nct"])} | {md_cell(e["reason"])} | {md_cell(e["detail"])} |\n')
    print(f'Wrote PRISMA exclusion log: {prisma_path} ({len(prisma_exclusions)} exclusions)')
    print()

    # Compare with atlas
    print('Comparing with current atlas...')
    comparison = compare_with_atlas(mining_results)
    if comparison:
        n_disc = len(comparison['verifications'])
        n_gaps = len(comparison['gaps'])
        print(f'  Verification discrepancies (>{DISCREPANCY_PCT_THRESHOLD:.0f}%): {n_disc}')
        print(f'  New ACM data for previously-missing trials: {n_gaps}')

        if comparison['verifications']:
            print()
            print('DISCREPANCIES:')
            for v in comparison['verifications'][:10]:
                print(f'  {v["app"]:20s}  {v["nct"]}  atlas={v["atlas_hr"]}  ctgov={v["ctgov_hr"]}  diff={v["pct_diff"]:.1f}%')

        if comparison['gaps']:
            print()
            print('NEW ACM DATA FOUND:')
            for g in comparison['gaps'][:20]:
                print(f'  {g["app"]:20s}  {g["nct"]} ({g["trial"][:20]})  HR {g["new_acm_hr"]} ({g["new_acm_ci"]})')

        # Write gap report — escape user-controlled fields via md_cell()
        with open(GAPS_REPORT_PATH, 'w', encoding='utf-8') as f:
            f.write('# CT.gov Mining Gap Report\n\n')
            f.write(f'Generated: {time.strftime("%Y-%m-%d %H:%M")}\n\n')
            f.write('## Summary\n\n')
            f.write(f'- Mined {len(mining_results)} NCTs from {len(inventory)} cardiology apps\n')
            f.write(f'- {acm_found} trials with ACM outcomes extracted\n')
            f.write(f'- {n_disc} verification discrepancies (atlas vs CT.gov >{DISCREPANCY_PCT_THRESHOLD:.0f}%)\n')
            f.write(f'- {n_gaps} new ACM values for previously-missing trials\n\n')

            f.write(f'## Verification discrepancies (atlas vs CT.gov >{DISCREPANCY_PCT_THRESHOLD:.0f}%)\n\n')
            if comparison['verifications']:
                f.write('| App | NCT | Atlas HR | CT.gov HR | Diff |\n|---|---|---|---|---|\n')
                for v in comparison['verifications']:
                    f.write(f'| {md_cell(v["app"])} | {md_cell(v["nct"])} | '
                            f'{v["atlas_hr"]} | {v["ctgov_hr"]} | {v["pct_diff"]:.1f}% |\n')
            else:
                f.write('_None — all existing atlas values match CT.gov within tolerance._\n')

            f.write('\n## New ACM data for trials currently missing it\n\n')
            if comparison['gaps']:
                f.write('| App | NCT | Trial | ACM HR | 95% CI | Source |\n|---|---|---|---|---|---|\n')
                for g in comparison['gaps']:
                    f.write(f'| {md_cell(g["app"])} | {md_cell(g["nct"])} | {md_cell(g["trial"])} | '
                            f'{g["new_acm_hr"]} | {md_cell(g["new_acm_ci"])} | {md_cell(g.get("source",""))} |\n')
            else:
                f.write('_None — no new ACM data found beyond what is already in the atlas._\n')

        print(f'\nWrote {GAPS_REPORT_PATH}')
