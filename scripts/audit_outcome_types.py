"""
Audit dashboards for outcome-type integrity. Per trial:
- If PRIMARY outcome has estimandType: 'HR' -> trial header must have publishedHR
- If PRIMARY outcome has type: 'CONTINUOUS' -> outcome entry must have md AND se
- If PRIMARY outcome has estimandType: 'OR'/'RR' -> outcome entry must have tE AND cE

Reports per-dashboard distribution by PRIMARY estimand + flags real mismatches.

Usage: python scripts/audit_outcome_types.py [--detail]
"""
import argparse
import io
import os
import re
import sys
from collections import defaultdict

if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

ROOT = os.environ.get(
    'RAPIDMETA_REPO_ROOT',
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
)

ENTRY_RE = re.compile(
    r"['\"](NCT\d+)['\"]\s*:\s*\{(.*?)allOutcomes:\s*\[(.*?)\]\s*,\s*rob:",
    re.DOTALL,
)

PRIMARY_OUTCOME_RE = re.compile(
    r"\{[^{}]*?type:\s*'PRIMARY'[^{}]*?\}",
)

# Fallback for older dashboards that use type='CONTINUOUS' as the primary marker
# (no separate PRIMARY entry). Match the FIRST CONTINUOUS outcome per trial.
CONTINUOUS_OUTCOME_RE = re.compile(
    r"\{[^{}]*?type:\s*'CONTINUOUS'[^{}]*?\}",
)


def parse_outcome(s):
    out = {'type': None, 'estimandType': None, 'has_md': False, 'has_se': False,
           'has_tE': False, 'has_cE': False, 'has_pubHR': False}
    m = re.search(r"type:\s*'([A-Z_]+)'", s)
    if m: out['type'] = m.group(1)
    m = re.search(r"estimandType:\s*'([A-Z]+)'", s)
    if m: out['estimandType'] = m.group(1)
    out['has_md'] = bool(re.search(r"\bmd:\s*-?[\d.]+", s))
    out['has_se'] = bool(re.search(r"\bse:\s*[\d.]+", s))
    out['has_tE'] = bool(re.search(r"\btE:\s*\d+", s))
    out['has_cE'] = bool(re.search(r"\bcE:\s*\d+", s))
    out['has_pubHR'] = bool(re.search(r"pubHR:\s*-?[\d.]+", s))
    # Fallback: if estimandType not set but pubHR is, treat as HR
    if not out['estimandType'] and out['has_pubHR']:
        out['estimandType'] = 'HR(legacy)'
    return out


def audit_file(path):
    src = open(path, 'r', encoding='utf-8').read()
    flags = []
    primary_estimands = []
    primary_types = []
    trial_count = 0
    for m in ENTRY_RE.finditer(src):
        trial_count += 1
        nct = m.group(1)
        header = m.group(2)
        outcomes_text = m.group(3)
        has_pubHR = bool(re.search(r"publishedHR:\s*-?[\d.]+", header))
        primary_matches = list(PRIMARY_OUTCOME_RE.finditer(outcomes_text))
        if not primary_matches:
            primary_matches = list(CONTINUOUS_OUTCOME_RE.finditer(outcomes_text))[:1]
        for om in primary_matches:
            o = parse_outcome(om.group(0))
            primary_estimands.append(o['estimandType'])
            primary_types.append(o['type'])
            if o['estimandType'] == 'HR' and not has_pubHR:
                flags.append((nct, "HR PRIMARY but no publishedHR on trial header"))
            if o['type'] == 'CONTINUOUS' and not (o['has_md'] and o['has_se']):
                flags.append((nct, "CONTINUOUS PRIMARY but missing md or se"))
            if o['estimandType'] in {'OR', 'RR'} and not (o['has_tE'] and o['has_cE']):
                flags.append((nct, f"{o['estimandType']} PRIMARY but missing tE or cE"))
    return {
        'trial_count': trial_count,
        'primary_estimands': primary_estimands,
        'primary_types': primary_types,
        'flags': flags,
    }


def shape_label(result):
    if result['trial_count'] == 0:
        return 'no-pairwise-data'
    estimands = result['primary_estimands']
    types = result['primary_types']
    has_continuous = 'CONTINUOUS' in types
    has_hr = 'HR' in estimands
    has_hr_legacy = 'HR(legacy)' in estimands
    has_or = 'OR' in estimands
    has_rr = 'RR' in estimands
    bits = []
    if has_or: bits.append('OR')
    if has_rr: bits.append('RR')
    if has_hr: bits.append('HR')
    if has_hr_legacy: bits.append('HR(legacy)')
    if has_continuous: bits.append('continuous')
    if not bits:
        # Could be HR-stored-as-publishedHR with no allOutcomes estimandType set
        return 'untyped'
    return '+'.join(bits)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--detail', action='store_true')
    args = ap.parse_args()
    files = sorted(
        f for f in os.listdir(ROOT)
        if f.endswith('_REVIEW.html') and not f.endswith('.bak.html')
    )
    by_shape = defaultdict(list)
    all_flags = []
    for fname in files:
        path = os.path.join(ROOT, fname)
        result = audit_file(path)
        shape = shape_label(result)
        by_shape[shape].append((fname, result['trial_count']))
        for nct, msg in result['flags']:
            all_flags.append((fname, nct, msg))
    print('Dashboards by primary-outcome shape:')
    for shape in sorted(by_shape):
        items = by_shape[shape]
        print(f'  {shape:25s} : {len(items)} dashboards')
        if args.detail:
            for f, n in items[:10]:
                print(f'      {f} ({n} trials)')
            if len(items) > 10:
                print(f'      ... +{len(items)-10} more')
    print()
    if all_flags:
        print(f'REAL flags ({len(all_flags)}):')
        for f, nct, msg in all_flags:
            print(f'  {f} :: {nct} :: {msg}')
    else:
        print('No data-shape vs estimand mismatches found.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
