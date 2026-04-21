#!/usr/bin/env python
"""Append trial(s) to an NMA config — extends realData_block AND treatments + comparisons.

Usage: python append_trial_to_nma_config.py <config.json> <additions.json>

additions.json format (NMA-specific):
  [
    {
      "nct": "NCT...",
      "name": "Trial name",
      "t1": "Active treatment",    # adds to treatments if new
      "t2": "Comparator treatment", # adds to treatments if new
      "phase": "III", "year": 2023,
      "tN": 100, "cN": 100, "tE": 0, "cE": 0,
      "group": "description",
      "publishedHR": 0.5, "hrLCI": 0.3, "hrUCI": 0.8,
      "outcome_label": "MACE",
      "outcome_title": "...",
      "estimand": "HR",  # or OR, RR, MD
      "snippet": "...", "sourceUrl": "...",
      "rob": "['low',...]"
    }
  ]
"""
import json, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

def build_trial_block(t):
    hr = t.get('publishedHR'); lci = t.get('hrLCI'); uci = t.get('hrUCI')
    est = t.get('estimand', 'RR')
    tE = t.get('tE', 0); tN = t.get('tN', 0)
    cE = t.get('cE', 0); cN = t.get('cN', 0)
    out_label = t.get('outcome_label', 'MACE')
    out_title = t.get('outcome_title', 'Primary outcome')
    rob = t.get('rob', "['low', 'some concerns', 'low', 'low', 'low']")
    snippet = t.get('snippet', '')
    src = t.get('sourceUrl', '')
    nct = t['nct']
    ctgov = f'https://clinicaltrials.gov/study/{nct.split("_")[0]}' if nct.startswith('NCT') else ''
    evidence = t.get('evidence_raw') or "[]"
    return (
        f"                '{nct}': {{\n"
        f"                    name: '{t['name']}', phase: '{t.get('phase','III')}', year: {t.get('year',2024)}, "
        f"tE: {tE}, tN: {tN}, cE: {cE}, cN: {cN}, "
        f"group: '{t.get('group','')}', "
        f"publishedHR: {hr}, hrLCI: {lci}, hrUCI: {uci},\n"
        f"                    allOutcomes: [\n"
        f"                        {{ shortLabel: '{out_label}', title: '{out_title}', tE: {tE}, cE: {cE}, type: 'PRIMARY', matchScore: 95, effect: {hr}, lci: {lci}, uci: {uci}, estimandType: '{est}' }}\n"
        f"                    ],\n"
        f"                    rob: {rob},\n"
        f"                    snippet: '{snippet}',\n"
        f"                    sourceUrl: '{src}',\n"
        f"                    ctgovUrl: '{ctgov}',\n"
        f"                    evidence: {evidence}\n"
        f"                }}"
    )

def main(cfg_path, add_path):
    cfg = json.load(open(cfg_path, encoding='utf-8'))
    adds = json.load(open(add_path, encoding='utf-8'))

    # Extend realData_block
    current = cfg['realData_block']
    for t in adds:
        block = build_trial_block(t)
        current = current.rstrip() + ',\n' + block
    cfg['realData_block'] = current

    # Extend auto_include + acronyms
    if 'auto_include' not in cfg: cfg['auto_include'] = []
    if 'acronyms' not in cfg: cfg['acronyms'] = {}
    for t in adds:
        if t['nct'] not in cfg['auto_include']:
            cfg['auto_include'].append(t['nct'])
        cfg['acronyms'][t['nct']] = t['name']

    # NMA-specific: extend treatments + comparisons
    for t in adds:
        if 't1' in t and t['t1'] not in cfg.get('treatments', []):
            cfg.setdefault('treatments', []).append(t['t1'])
        if 't2' in t and t['t2'] not in cfg.get('treatments', []):
            cfg.setdefault('treatments', []).append(t['t2'])
        if 't1' in t and 't2' in t:
            cfg.setdefault('comparisons', []).append({
                't1': t['t1'], 't2': t['t2'], 'trials': [t['nct']]
            })

    with open(cfg_path, 'w', encoding='utf-8') as f:
        json.dump(cfg, f, indent=2, ensure_ascii=False)
    print(f'appended {len(adds)} trial(s) to {cfg_path}')

if __name__ == '__main__':
    if len(sys.argv) != 3:
        print('usage: python append_trial_to_nma_config.py <config.json> <additions.json>', file=sys.stderr)
        sys.exit(1)
    main(sys.argv[1], sys.argv[2])
