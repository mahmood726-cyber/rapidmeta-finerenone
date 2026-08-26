#!/usr/bin/env python
"""Sweep every visual abstract for a page-level total standing in for the
pool's own denominator.

LAYER: this is a RENDER-layer defect. The stored object may hold correct
per-outcome analysed denominators; the graphic composes its own caption. A
check that reads the store therefore PASSES while every graphic is wrong.
This script reads the rendered caption text, not the store.

DETECTOR: two or more visual abstracts on one page that cover DIFFERENT
outcomes but display an IDENTICAL participant count. Distinct outcomes pooling
distinct trial sets essentially never share an exact denominator, so a repeat
is a page-level total substituted for a per-outcome one.

This is a HIGH-PRECISION, NOT-COMPLETE detector: a page whose abstracts all
share one outcome, or a page with a single abstract, cannot be judged by it.
Those are reported separately as NOT-ASSESSABLE rather than as clean -- an
uncounted page is not a clean page.
"""
import os, re, json, sys, collections

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CAP = re.compile(r'(\d+)\s+trials?,\s*([\d,]+)\s*participants\.\s*'
                 r'Outcome:\s*([^<]{0,120})', re.I)

def captions(text):
    out = []
    for m in CAP.finditer(text):
        out.append({'trials': int(m.group(1)),
                    'n': int(m.group(2).replace(',', '')),
                    'outcome': re.sub(r'\s+', ' ', m.group(3)).strip()})
    return out

def judge(caps):
    """-> ('SUSPECT'|'OK'|'NOT_ASSESSABLE', detail)"""
    if len(caps) < 2:
        return 'NOT_ASSESSABLE', 'fewer than 2 abstracts'
    by_n = collections.defaultdict(set)
    for c in caps:
        by_n[c['n']].add(c['outcome'][:40])
    repeats = {n: sorted(o) for n, o in by_n.items() if len(o) > 1}
    if repeats:
        return 'SUSPECT', repeats
    if len({c['outcome'][:40] for c in caps}) < 2:
        return 'NOT_ASSESSABLE', 'all abstracts share one outcome'
    return 'OK', 'distinct outcomes carry distinct denominators'

if __name__ == '__main__':
    root = sys.argv[1] if len(sys.argv) > 1 else ROOT
    res = {'SUSPECT': {}, 'OK': [], 'NOT_ASSESSABLE': {}}
    pages = abstracts = 0
    for rt, dirs, fs in os.walk(root):
        dirs[:] = [d for d in dirs if d not in {'.git', 'node_modules',
                                                'pytest_tmp', 'build-artefacts'}]
        for f in (x for x in fs if x.endswith('.html')):
            p = os.path.join(rt, f)
            rel = os.path.relpath(p, root).replace(os.sep, '/')
            caps = captions(open(p, 'rb').read().decode('utf-8', 'replace'))
            # Positive property: act on pages that CARRY a visual abstract.
            # (pre-commit exclusion-by-absence gate)
            if caps:
                pages += 1
                abstracts += len(caps)
                v, d = judge(caps)
                if v == 'SUSPECT':
                    res['SUSPECT'][rel] = {'repeated_denominators': d,
                                           'captions': caps}
                elif v == 'OK':
                    res['OK'].append(rel)
                else:
                    res['NOT_ASSESSABLE'][rel] = d
    print(f'pages carrying visual abstracts : {pages}')
    print(f'visual abstracts found          : {abstracts}')
    print(f'  SUSPECT (repeated denominator): {len(res["SUSPECT"])}')
    print(f'  OK (distinct denominators)    : {len(res["OK"])}')
    print(f'  NOT ASSESSABLE by this test   : {len(res["NOT_ASSESSABLE"])}')
    # Output path must follow the SCAN ROOT. Writing to a fixed path let a
    # fixture control-run overwrite the corpus result -- the control destroyed
    # the measurement it was validating. (2026-08-26)
    tag = '' if os.path.abspath(root) == os.path.abspath(ROOT) else '_' + os.path.basename(os.path.normpath(root))
    os.makedirs(os.path.join(ROOT, 'outputs'), exist_ok=True)
    with open(os.path.join(ROOT, 'outputs', 'abstract_denominator_sweep%s.json' % tag),
              'w', encoding='utf-8', newline='') as fh:
        json.dump(res, fh, indent=1)
