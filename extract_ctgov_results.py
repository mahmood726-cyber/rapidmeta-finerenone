#!/usr/bin/env python
"""
CT.gov Auto-Extractor

For each new candidate trial detected by living_update_scanner.py, fetches
the full results JSON from ClinicalTrials.gov API v2 and extracts:
- Primary outcome HR (or RR/OR) with 95% CI and p-value
- Group sizes (n_treatment, n_control)
- Event counts where reported
- Provenance (CT.gov outcome ID, group IDs, paramType)

Output: extraction_proposals.json — a structured queue of trials with
extracted values, ready for human review via review_extractions.py.

Run:
  python extract_ctgov_results.py                    # all candidates
  python extract_ctgov_results.py NCT05093933 ...    # specific NCTs
  python extract_ctgov_results.py --from-scanner     # use latest scan
"""
import sys, io, os, json, re, time
from urllib.parse import urlencode
from urllib.request import urlopen, Request
from urllib.error import URLError, HTTPError

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

CT_GOV_API_STUDY = 'https://clinicaltrials.gov/api/v2/studies/'
USER_AGENT = 'RapidMeta-AutoExtractor/1.0'


# ═══════════════════════════════════════════════════════════
# CT.gov fetch
# ═══════════════════════════════════════════════════════════

def fetch_study(nct_id):
    """Fetch full study record (protocol + results) from CT.gov v2."""
    url = f'{CT_GOV_API_STUDY}{nct_id}?format=json'
    req = Request(url, headers={'User-Agent': USER_AGENT, 'Accept': 'application/json'})
    try:
        with urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode('utf-8'))
    except HTTPError as e:
        return {'error': f'HTTP {e.code}: {e.reason}'}
    except URLError as e:
        return {'error': f'URL error: {e.reason}'}
    except Exception as e:
        return {'error': str(e)}


# ═══════════════════════════════════════════════════════════
# Result extraction
# ═══════════════════════════════════════════════════════════

EFFECT_PARAM_MAP = {
    'hazard ratio': 'HR',
    'hazard ratio (hr)': 'HR',
    'risk ratio': 'RR',
    'risk ratio (rr)': 'RR',
    'odds ratio': 'OR',
    'odds ratio (or)': 'OR',
    'mean difference': 'MD',
    'least squares mean difference': 'LSMD',
}


def normalize_param_type(s):
    if not s:
        return None
    return EFFECT_PARAM_MAP.get(s.lower().strip())


def extract_primary_outcome(study):
    """Extract primary outcome HR/RR/OR from results section.

    Returns dict with extracted values or None if not extractable.
    """
    proto = study.get('protocolSection', {})
    ident = proto.get('identificationModule', {})
    nct_id = ident.get('nctId')
    title = ident.get('briefTitle', '')
    acronym = ident.get('acronym', '')

    out = {
        'nctId': nct_id,
        'title': title,
        'acronym': acronym,
        'phase': ', '.join(proto.get('designModule', {}).get('phases', [])),
        'enrollment': proto.get('designModule', {}).get('enrollmentInfo', {}).get('count'),
        'sponsor': proto.get('sponsorCollaboratorsModule', {}).get('leadSponsor', {}).get('name', ''),
        'status': proto.get('statusModule', {}).get('overallStatus', ''),
        'completionDate': proto.get('statusModule', {}).get('completionDateStruct', {}).get('date', ''),
        'primaryCompletionDate': proto.get('statusModule', {}).get('primaryCompletionDateStruct', {}).get('date', ''),
        'extracted': None,
        'extraction_status': 'unknown',
    }

    if not study.get('hasResults'):
        out['extraction_status'] = 'no_results_posted'
        return out

    results = study.get('resultsSection', {})
    om = results.get('outcomeMeasuresModule', {}).get('outcomeMeasures', [])

    # Find first PRIMARY outcome
    primary = next((o for o in om if o.get('type') == 'PRIMARY'), None)
    if not primary:
        out['extraction_status'] = 'no_primary_outcome'
        return out

    out['primary_outcome_title'] = primary.get('title', '')
    out['primary_outcome_id'] = primary.get('id')

    # Extract group info
    groups = primary.get('groups', [])
    out['groups'] = [{'id': g.get('id'), 'title': g.get('title'), 'description': g.get('description', '')[:200]}
                     for g in groups]

    # Find HR/RR/OR analysis
    analyses = primary.get('analyses', [])
    for a in analyses:
        param = normalize_param_type(a.get('paramType'))
        if param in ('HR', 'RR', 'OR'):
            try:
                pv = float(a.get('paramValue'))
                lo = float(a.get('ciLowerLimit'))
                hi = float(a.get('ciUpperLimit'))
            except (TypeError, ValueError):
                continue
            out['extracted'] = {
                'measure': param,
                'estimate': pv,
                'lci': lo,
                'uci': hi,
                'pValue': a.get('pValue'),
                'paramType_raw': a.get('paramType'),
                'ciPctLevel': a.get('ciPctLevel'),
                'ciNumSides': a.get('ciNumSides'),
                'groupIds': a.get('groupIds', []),
                'method': a.get('statisticalMethod', ''),
            }
            out['extraction_status'] = 'extracted'
            break

    # Get denoms (group sizes)
    denoms = primary.get('denoms', [])
    if denoms:
        denom = denoms[0]  # first denomination block
        out['n_per_group'] = {c.get('groupId'): int(c.get('value', 0))
                              for c in denom.get('counts', [])}

    # Try to get event counts from class measurements
    classes = primary.get('classes', [])
    if classes:
        out['class_measurements'] = []
        for cls in classes:
            for cat in cls.get('categories', []):
                for m in cat.get('measurements', []):
                    out['class_measurements'].append({
                        'groupId': m.get('groupId'),
                        'value': m.get('value'),
                        'spread': m.get('spread'),
                        'category': cat.get('title', ''),
                    })

    if out['extraction_status'] == 'unknown':
        out['extraction_status'] = 'no_hr_analysis'

    return out


# ═══════════════════════════════════════════════════════════
# Pretty printing
# ═══════════════════════════════════════════════════════════

def print_extraction(out):
    print('=' * 70)
    print(f'  {out["nctId"]}  {out.get("acronym", "") or ""}')
    print(f'  {out["title"][:65]}')
    print('=' * 70)
    print(f'  Sponsor:    {out["sponsor"][:55]}')
    print(f'  Phase:      {out["phase"]}')
    print(f'  Enrollment: {out["enrollment"]}')
    print(f'  Status:     {out["status"]}')
    print(f'  Completed:  {out["primaryCompletionDate"]}')
    print(f'  Extraction: {out["extraction_status"]}')
    print()
    if out.get('primary_outcome_title'):
        print(f'  Primary outcome: {out["primary_outcome_title"][:65]}')
    if out.get('extracted'):
        e = out['extracted']
        print(f'  ESTIMATE: {e["measure"]} = {e["estimate"]} ({e["lci"]}-{e["uci"]})')
        if e.get('pValue'):
            print(f'  p-value:  {e["pValue"]}')
        if e.get('method'):
            print(f'  Method:   {e["method"]}')
    if out.get('n_per_group'):
        print(f'  N per group:')
        for gid, n in out['n_per_group'].items():
            grp_title = next((g['title'] for g in out.get('groups', []) if g['id'] == gid), gid)
            print(f'    {gid} ({grp_title[:30]}): n={n}')
    print()


# ═══════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════

if __name__ == '__main__':
    here = os.path.dirname(os.path.abspath(__file__))
    use_scanner = '--from-scanner' in sys.argv

    if use_scanner:
        # Read latest scanner output
        scanner_json = os.path.join(here, 'living_update_candidates.json')
        if not os.path.exists(scanner_json):
            print('Run living_update_scanner.py --json first to generate the candidate list.')
            sys.exit(1)
        with open(scanner_json) as f:
            scan_results = json.load(f)
        ncts = []
        for r in scan_results:
            if 'new_trials' in r:
                ncts.extend(t['nctId'] for t in r['new_trials'])
        print(f'Loaded {len(ncts)} candidate NCTs from scanner output.')
    else:
        # Direct NCT IDs from command line, or hardcoded test set
        ncts = [arg for arg in sys.argv[1:] if arg.startswith('NCT')]
        if not ncts:
            # Default: extract for the trials we just added as placeholders
            ncts = [
                'NCT05093933',  # VICTOR (vericiguat)
                'NCT03814187',  # ORION-8 (inclisiran long-term)
                'NCT04873934',  # V-INCEPTION (inclisiran implementation)
                'NCT05047263',  # FIND-CKD (finerenone)
                'NCT03914326',  # SOUL (semaglutide CKD CVOT)
            ]
            print(f'No NCT IDs given — extracting default test set: {len(ncts)} trials')

    print()
    proposals = []
    for i, nct in enumerate(ncts):
        print(f'[{i+1}/{len(ncts)}] Fetching {nct}...', flush=True)
        study = fetch_study(nct)
        if 'error' in study:
            print(f'  ERROR: {study["error"]}')
            proposals.append({'nctId': nct, 'error': study['error']})
            continue
        out = extract_primary_outcome(study)
        proposals.append(out)
        print_extraction(out)
        if i < len(ncts) - 1:
            time.sleep(0.5)

    # Write proposals queue
    out_path = os.path.join(here, 'extraction_proposals.json')
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(proposals, f, indent=2)
    print(f'Wrote {out_path}')

    # Summary
    extracted = sum(1 for p in proposals if p.get('extraction_status') == 'extracted')
    print(f'\nSummary: {extracted}/{len(proposals)} trials had primary HR/RR/OR extractable')
