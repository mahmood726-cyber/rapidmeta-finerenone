#!/usr/bin/env python
"""Append trial(s) to a config file's realData_block.

Usage:
  python append_trial_to_config.py <config.json> <additions.json>

additions.json format:
  [
    {
      "nct": "NCT03094715",
      "name": "TENSION",
      "phase": "III",
      "year": 2024,
      "tE": 91, "tN": 124, "cE": 31, "cN": 129,
      "group": "Large-core AIS 6-12h (ASPECTS 3-5), EVT vs medical",
      "publishedHR": 2.57, "hrLCI": 1.79, "uci": 3.69,
      "snippet": "Source: Bendszus M et al. Lancet 2023;402:1753-1763 (TENSION).",
      "sourceUrl": "...",
      "outcome_label": "MACE",
      "outcome_title": "Functional independence 90-d mRS 0-2",
      "estimand": "RR"
    },
    ...
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
    ctgov = f'https://clinicaltrials.gov/study/{nct}'
    evidence = t.get('evidence_raw') or "[]"
    # Return the realData entry as a JSON-escapable JS literal string
    block = (
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
    # The realData_block value in config JSON is a JSON-escaped string. Escape \n → \\n and ' keep, { → {
    # Since it will be re-encoded when saved, just return the literal; escaping happens on json.dump
    return block


def main(cfg_path, add_path):
    cfg = json.load(open(cfg_path, encoding='utf-8'))
    adds = json.load(open(add_path, encoding='utf-8'))

    # Current realData_block is a string of JS; it ends with `}` (closing the last trial) without trailing comma
    current = cfg['realData_block']

    for t in adds:
        block = build_trial_block(t)
        # Insert a comma after the current last `}`, then add new block
        current = current.rstrip() + ',\n' + block

    cfg['realData_block'] = current

    # Extend auto_include + acronyms
    if 'auto_include' not in cfg: cfg['auto_include'] = []
    if 'acronyms' not in cfg: cfg['acronyms'] = {}
    for t in adds:
        if t['nct'] not in cfg['auto_include']:
            cfg['auto_include'].append(t['nct'])
        cfg['acronyms'][t['nct']] = t['name']

    with open(cfg_path, 'w', encoding='utf-8') as f:
        json.dump(cfg, f, indent=2, ensure_ascii=False)

    print(f'appended {len(adds)} trial(s) to {cfg_path}')


if __name__ == '__main__':
    if len(sys.argv) != 3:
        print('usage: python append_trial_to_config.py <config.json> <additions.json>', file=sys.stderr)
        sys.exit(1)
    main(sys.argv[1], sys.argv[2])
