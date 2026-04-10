#!/usr/bin/env python
"""
Living Update Scanner

For each app in the RapidMeta portfolio, queries ClinicalTrials.gov API v2
using the app's stored search term, compares against the current trial set,
and reports new candidate trials that should be considered for inclusion.

This is a *proposal* tool — it identifies candidates but never modifies apps
without human review.

Output:
- Console report of new trials per app
- JSON file: living_update_candidates.json (machine-readable)
- Markdown file: LIVING_UPDATE_CANDIDATES.md (human review)

Run: python living_update_scanner.py [--app NAME] [--json] [--md]

Requires: requests (pip install requests)
"""
import sys, io, os, re, json, time
from urllib.parse import urlencode
from urllib.request import urlopen, Request
from urllib.error import URLError, HTTPError

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

CT_GOV_API = 'https://clinicaltrials.gov/api/v2/studies'
USER_AGENT = 'RapidMeta-LivingUpdateScanner/1.0 (mahmood726@example.com)'


# ═══════════════════════════════════════════════════════════
# APP REGISTRY: search criteria for each living MA
# ═══════════════════════════════════════════════════════════

APP_REGISTRY = [
    # name, search_term, current_NCTs, min_phase, status_filter
    ('FINERENONE', 'finerenone',
     ['NCT02540993', 'NCT02545049', 'NCT04435626', 'NCT01874431'],
     'PHASE3', 'COMPLETED'),
    ('GLP1_CVOT', 'liraglutide OR semaglutide OR dulaglutide OR exenatide OR lixisenatide OR albiglutide OR efpeglenatide',
     ['NCT01179048', 'NCT01720446', 'NCT03574597', 'NCT01394952', 'NCT02465515',
      'NCT01147250', 'NCT01144338', 'NCT01107886', 'NCT03496298', 'NCT01755364'],
     'PHASE3', 'COMPLETED'),
    ('SGLT2_HF', 'dapagliflozin OR empagliflozin OR canagliflozin OR ertugliflozin AND heart failure',
     ['NCT03036124', 'NCT03057977', 'NCT03057951', 'NCT03619213', 'NCT03521934'],
     'PHASE3', 'COMPLETED'),
    ('SGLT2_CKD', 'dapagliflozin OR empagliflozin OR canagliflozin AND chronic kidney disease',
     ['NCT03036150', 'NCT02065791', 'NCT03594110'],
     'PHASE3', 'COMPLETED'),
    ('ARNI_HF', 'sacubitril valsartan',
     ['NCT01035255', 'NCT01920711', 'NCT02924727'],
     'PHASE3', 'COMPLETED'),
    ('ABLATION_AF', 'catheter ablation atrial fibrillation',
     ['NCT00643188', 'NCT00911508', 'NCT01288352', 'NCT01420393'],
     'PHASE3', 'COMPLETED'),
    ('IV_IRON_HF', 'ferric carboxymaltose OR ferric derisomaltose AND heart failure',
     ['NCT01453608', 'NCT02937454', 'NCT02642562', 'NCT03037931'],
     'PHASE3', 'COMPLETED'),
    ('COLCHICINE_CVD', 'colchicine cardiovascular',
     ['NCT02551094', 'ACTRN-LODOCO2', 'ACTRN-COPS', 'NCT03048825', 'NCT02898610'],
     'PHASE3', 'COMPLETED'),
    ('RIVAROXABAN_VASC', 'rivaroxaban',
     ['NCT01776424', 'NCT02504216', 'NCT01877915', 'NCT00809965'],
     'PHASE3', 'COMPLETED'),
    ('BEMPEDOIC_ACID', 'bempedoic acid',
     ['NCT02993406'],
     'PHASE3', 'COMPLETED'),
    ('PCSK9', 'evolocumab OR alirocumab',
     ['NCT01764633', 'NCT01663402'],
     'PHASE3', 'COMPLETED'),
    ('OMECAMTIV', 'omecamtiv mecarbil',
     ['NCT02929329', 'NCT01300013', 'NCT01300013'],
     'PHASE3', 'COMPLETED'),
    ('VERICIGUAT', 'vericiguat',
     ['NCT02861534', 'NCT03547583', 'NCT01951625'],
     'PHASE3', 'COMPLETED'),
    ('SOTAGLIFLOZIN', 'sotagliflozin',
     ['NCT03521934', 'NCT03315143'],
     'PHASE3', 'COMPLETED'),
    ('INCLISIRAN', 'inclisiran',
     ['NCT03397121', 'NCT03399370', 'NCT03400800'],
     'PHASE3', 'COMPLETED'),
    ('OSIMERTINIB_NSCLC', 'osimertinib',
     ['NCT02296125', 'NCT02511106', 'NCT04035486', 'NCT03521154'],
     'PHASE3', 'COMPLETED'),
    ('ENFORTUMAB_UC', 'enfortumab vedotin',
     ['NCT03474107', 'NCT04223856'],
     'PHASE3', 'COMPLETED'),
    ('KRAS_G12C_NSCLC', 'sotorasib OR adagrasib AND lung',
     ['NCT04303780', 'NCT04685135'],
     'PHASE3', 'COMPLETED'),
    ('PEMBRO_ADJ_MEL', 'pembrolizumab adjuvant melanoma',
     ['NCT02362594', 'NCT03553836'],
     'PHASE3', 'COMPLETED'),
    ('TEZEPELUMAB_ASTHMA', 'tezepelumab',
     ['NCT03347279', 'NCT02054130', 'NCT03406078'],
     'PHASE3', 'COMPLETED'),
    ('DUPILUMAB_COPD', 'dupilumab COPD',
     ['NCT03930732', 'NCT04456673'],
     'PHASE3', 'COMPLETED'),
    ('SOTATERCEPT_PAH', 'sotatercept pulmonary',
     ['NCT04576988', 'NCT04811092', 'NCT04896008'],
     'PHASE3', 'COMPLETED'),
]


# ═══════════════════════════════════════════════════════════
# CT.gov API client
# ═══════════════════════════════════════════════════════════

def fetch_ctgov(search_term, status='COMPLETED', phase='PHASE3', max_results=50):
    """Query CT.gov API v2 and return list of study dicts."""
    params = {
        'query.intr': search_term,
        'pageSize': str(max_results),
        'format': 'json',
    }
    if status:
        params['filter.overallStatus'] = status
    if phase:
        params['filter.advanced'] = f'AREA[Phase]{phase}'
    url = f'{CT_GOV_API}?{urlencode(params)}'
    req = Request(url, headers={'User-Agent': USER_AGENT, 'Accept': 'application/json'})
    try:
        with urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode('utf-8'))
        return data.get('studies', [])
    except HTTPError as e:
        return {'error': f'HTTP {e.code}: {e.reason}'}
    except URLError as e:
        return {'error': f'URL error: {e.reason}'}
    except Exception as e:
        return {'error': str(e)}


def parse_study(study):
    """Extract key fields from a CT.gov study record."""
    proto = study.get('protocolSection', {})
    ident = proto.get('identificationModule', {})
    status = proto.get('statusModule', {})
    design = proto.get('designModule', {})
    sponsor = proto.get('sponsorCollaboratorsModule', {})
    return {
        'nctId': ident.get('nctId'),
        'briefTitle': ident.get('briefTitle', ''),
        'acronym': ident.get('acronym', ''),
        'status': status.get('overallStatus', ''),
        'phase': ', '.join(design.get('phases', [])),
        'enrollment': design.get('enrollmentInfo', {}).get('count'),
        'startDate': status.get('startDateStruct', {}).get('date', ''),
        'completionDate': status.get('completionDateStruct', {}).get('date', ''),
        'primaryCompletionDate': status.get('primaryCompletionDateStruct', {}).get('date', ''),
        'sponsor': sponsor.get('leadSponsor', {}).get('name', ''),
        'hasResults': bool(study.get('hasResults')),
    }


# ═══════════════════════════════════════════════════════════
# SCANNER
# ═══════════════════════════════════════════════════════════

def scan_app(app_entry):
    """Scan one app for new candidate trials."""
    name, search, current_ncts, phase, status = app_entry
    current_set = set(current_ncts)

    print(f'  Querying CT.gov for: {name}', end='', flush=True)
    studies = fetch_ctgov(search, status=status, phase=phase, max_results=100)
    if isinstance(studies, dict) and 'error' in studies:
        print(f'  ERROR: {studies["error"]}')
        return {'name': name, 'error': studies['error'], 'new_trials': []}

    parsed = [parse_study(s) for s in studies]
    new_trials = [t for t in parsed if t['nctId'] and t['nctId'] not in current_set]
    # Sort by completion date descending (newest first)
    new_trials.sort(key=lambda t: t.get('primaryCompletionDate') or '', reverse=True)

    print(f'  ({len(parsed)} found, {len(new_trials)} new)')
    return {
        'name': name,
        'search_term': search,
        'current_trial_count': len(current_set),
        'ctgov_total': len(parsed),
        'new_count': len(new_trials),
        'new_trials': new_trials[:10],  # top 10 newest
    }


def print_text_report(results):
    print()
    print('=' * 75)
    print('LIVING UPDATE SCAN RESULTS')
    print('=' * 75)
    total_new = 0
    apps_with_updates = 0
    for r in results:
        if 'error' in r:
            print(f'\n{r["name"]:25s}  ERROR: {r["error"]}')
            continue
        if r['new_count'] > 0:
            apps_with_updates += 1
            total_new += r['new_count']
            print(f'\n{r["name"]:25s}  ({r["current_trial_count"]} current, {r["new_count"]} candidate updates)')
            for t in r['new_trials'][:5]:
                acr = f' [{t["acronym"]}]' if t["acronym"] else ''
                print(f'  + {t["nctId"]}{acr}  {t["briefTitle"][:60]}')
                print(f'    Sponsor: {t["sponsor"][:50]}  | Status: {t["status"]}  | n={t["enrollment"] or "?"}')
                if t['primaryCompletionDate']:
                    print(f'    Primary completion: {t["primaryCompletionDate"]}  | Results: {"YES" if t["hasResults"] else "no"}')
        else:
            print(f'\n{r["name"]:25s}  ({r["current_trial_count"]} current, no new candidates)')

    print()
    print('=' * 75)
    print(f'SUMMARY: {apps_with_updates}/{len(results)} apps have candidate updates ({total_new} total new trials)')
    print('=' * 75)
    print('\nAll candidates are PROPOSALS — review each before adding to app configs.')


def write_markdown_report(results):
    md = []
    md.append('# Living Update Candidates')
    md.append('')
    md.append(f'Generated: {time.strftime("%Y-%m-%d %H:%M")}')
    md.append('')
    total_new = sum(r.get('new_count', 0) for r in results)
    apps_with = sum(1 for r in results if r.get('new_count', 0) > 0)
    md.append(f'**{apps_with}/{len(results)} apps** have candidate trial updates ({total_new} total new trials).')
    md.append('')
    md.append('All candidates are **proposals**. Each must be reviewed manually for:')
    md.append('1. Relevance to the app PICO')
    md.append('2. Outcome alignment')
    md.append('3. Population eligibility')
    md.append('4. Risk-of-bias assessment')
    md.append('')
    md.append('---')
    md.append('')

    for r in results:
        md.append(f'## {r["name"]}')
        md.append('')
        if 'error' in r:
            md.append(f'**Error:** {r["error"]}')
            md.append('')
            continue
        md.append(f'Search term: `{r["search_term"]}`')
        md.append(f'Current trials: {r["current_trial_count"]}  |  CT.gov returned: {r["ctgov_total"]}  |  New candidates: {r["new_count"]}')
        md.append('')
        if r['new_trials']:
            md.append('| NCT | Acronym | Title | Sponsor | n | Completion | Results |')
            md.append('|-----|---------|-------|---------|---|-----------|---------|')
            for t in r['new_trials']:
                title = (t['briefTitle'][:60] + '...') if len(t['briefTitle']) > 60 else t['briefTitle']
                md.append(f'| {t["nctId"]} | {t["acronym"] or "-"} | {title} | '
                          f'{t["sponsor"][:30]} | {t["enrollment"] or "?"} | '
                          f'{t["primaryCompletionDate"] or "-"} | {"yes" if t["hasResults"] else "no"} |')
        else:
            md.append('*No new candidates.*')
        md.append('')

    return '\n'.join(md)


# ═══════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════

if __name__ == '__main__':
    output_json = '--json' in sys.argv
    output_md = '--md' in sys.argv

    target_app = None
    for i, arg in enumerate(sys.argv):
        if arg == '--app' and i + 1 < len(sys.argv):
            target_app = sys.argv[i + 1]

    apps_to_scan = APP_REGISTRY
    if target_app:
        apps_to_scan = [a for a in APP_REGISTRY if target_app.upper() in a[0]]
        if not apps_to_scan:
            print(f'No app matching: {target_app}')
            sys.exit(1)

    print(f'Scanning {len(apps_to_scan)} apps against ClinicalTrials.gov v2...')
    print()

    results = []
    for i, app in enumerate(apps_to_scan):
        result = scan_app(app)
        results.append(result)
        # Rate limit: 0.5s between calls
        if i < len(apps_to_scan) - 1:
            time.sleep(0.5)

    if output_json:
        out_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                 'living_update_candidates.json')
        with open(out_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2)
        print(f'Wrote {out_path}')
    elif output_md:
        md = write_markdown_report(results)
        out_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                 'LIVING_UPDATE_CANDIDATES.md')
        with open(out_path, 'w', encoding='utf-8') as f:
            f.write(md)
        print(f'Wrote {out_path}')
    else:
        print_text_report(results)
