"""Acquisition-lane identity gate.

Every RapidMeta app acquires candidate trials from three lanes, all merged into
one `trials` array by Promise.allSettled:

    ctgovUrl  -> clinicaltrials.gov/api/v2/studies?query.intr=...
    epmcUrl   -> europepmc  ...  encodeURIComponent('<drug> AND (TITLE:randomized ...
    oaUrl     -> api.openalex.org/works?search=<drug>

The lanes are parameterised independently by the generators, by literal
find-and-replace. `re.sub` returns its input unchanged and raises nothing when
the needle is absent, so a lane whose needle drifted keeps the *seed template's*
value while its siblings get the real topic. The observable signature is an app
whose CT.gov lane queries a different disease than its OpenAlex lane.

This gate is the identity witness for that: it asks whether THIS lane belongs to
THIS app, which no arithmetic check can see -- a heart-failure query returns
well-formed trials with correct event counts that pool without error.

Two rules, because either alone is insufficient:

  R1 cross-lane   Lanes must share >=1 drug token. Catches the common case where
                  one needle drifted and the others held.
  R2 seed-value   No app may carry a lane value identical to a known seed
                  template's value unless the app *is* that seed. Catches the
                  case R1 cannot see: when EVERY lane kept the seed value the
                  lanes agree with each other and are uniformly wrong. (Two
                  contaminated lanes agreeing is not correctness -- same shape as
                  the both-arms defect.)

Exit 1 on any violation, so it can be a pre-push witness. Read-only.

Usage:
    python scripts/acquisition_identity_gate.py [--root DIR] [--json OUT] [-v]
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import re
import sys

# ── lane extractors ────────────────────────────────────────────────────────
RE_CTGOV = re.compile(r'query\.intr=([^&"\']+)')
RE_OPENALEX = re.compile(r'api\.openalex\.org/works\?search=([^&"\']+)')
RE_EPMC = re.compile(r'encodeURIComponent\(\s*[\'"]([^\'"]+?)\s+AND\s+')

# Values belonging to a seed/template app. An app carrying one of these is only
# legitimate if it IS that seed -- see SEED_OWNERS.
SEED_CTGOV_VALUES = {
    'bempedoic acid',
    'bempedoic+acid',
    'dapagliflozin+OR+empagliflozin',
    'empagliflozin+OR+dapagliflozin+OR+sacubitril+AND+heart+failure+reduced',
    'sacubitril AND valsartan',
    'sacubitril+AND+valsartan',
}
# filename fragment -> the seed value that app is allowed to own
SEED_OWNERS = {
    'BEMPEDOIC': ('bempedoic acid', 'bempedoic+acid'),
    'DAPAGLIFLOZIN': ('dapagliflozin+OR+empagliflozin',),
    'EMPAGLIFLOZIN': ('dapagliflozin+OR+empagliflozin',),
    'SACUBITRIL': ('sacubitril AND valsartan', 'sacubitril+AND+valsartan'),
    'HFREF': ('empagliflozin+OR+dapagliflozin+OR+sacubitril+AND+heart+failure+reduced',),
    'HFPEF': ('dapagliflozin+OR+empagliflozin',),
}

# Query scaffolding, not drug identity.
STOPWORDS = {
    'randomized', 'randomised', 'clinical', 'trial', 'trials', 'study', 'studies',
    'patients', 'versus', 'placebo', 'controlled', 'phase', 'adults', 'treatment',
    'therapy', 'first', 'line', 'human', 'double', 'blind', 'metaanalysis',
}


def drug_tokens(raw: str) -> set[str]:
    """Identity-bearing tokens of a lane query."""
    if not raw:
        return set()
    s = re.sub(r'%20|\+', ' ', raw)
    return {w for w in re.findall(r'[a-z]{5,}', s.lower()) if w not in STOPWORDS}


def read_lanes(html: str) -> dict[str, str | None]:
    def first(rx):
        m = rx.search(html)
        return m.group(1) if m else None
    return {'ctgov': first(RE_CTGOV), 'openalex': first(RE_OPENALEX), 'epmc': first(RE_EPMC)}


def owns_seed(name: str, value: str) -> bool:
    up = name.upper()
    for frag, allowed in SEED_OWNERS.items():
        if frag in up and value in allowed:
            return True
    return False


def check_app(name: str, html: str) -> list[dict]:
    """Return violations for one app. Empty list == clean."""
    lanes = read_lanes(html)
    ct, oa, pm = lanes['ctgov'], lanes['openalex'], lanes['epmc']
    out: list[dict] = []

    # R2 -- seed value retained by a non-owner.
    if ct is not None and ct in SEED_CTGOV_VALUES and not owns_seed(name, ct):
        out.append({
            'app': name, 'rule': 'R2-seed-value', 'lane': 'ctgov', 'value': ct,
            'detail': ('CT.gov lane still holds seed-template value %r; this app does not own '
                       'that seed. The generator substitution silently no-opped.' % ct),
        })

    # R1 -- cross-lane drug identity.
    tc = drug_tokens(ct or '')
    peers = {'openalex': drug_tokens(oa or ''), 'epmc': drug_tokens(pm or '')}
    for peer, tp in peers.items():
        if not tc or not tp:
            continue
        if not (tc & tp):
            out.append({
                'app': name, 'rule': 'R1-cross-lane', 'lane': 'ctgov vs ' + peer,
                'value': ct, 'peer_value': (oa if peer == 'openalex' else pm),
                'detail': ('CT.gov lane and %s lane name disjoint drugs; the merged trial set '
                           'would mix two diseases.' % peer),
            })
            break
    return out


def scan(root: str) -> tuple[list[dict], int]:
    files = sorted(glob.glob(os.path.join(root, '*.html')))
    viol: list[dict] = []
    for fp in files:
        html = open(fp, 'rb').read().decode('latin-1')
        viol.extend(check_app(os.path.basename(fp), html))
    return viol, len(files)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('--root', default=str(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    ap.add_argument('--json', dest='json_out')
    ap.add_argument('-v', '--verbose', action='store_true')
    a = ap.parse_args()

    viol, n = scan(a.root)
    apps = sorted({v['app'] for v in viol})
    print('ACQUISITION IDENTITY GATE')
    print('  apps scanned          : %d' % n)
    print('  violations            : %d across %d apps' % (len(viol), len(apps)))
    for rule in ('R1-cross-lane', 'R2-seed-value'):
        print('    %-14s      : %d' % (rule, sum(1 for v in viol if v['rule'] == rule)))
    if a.verbose:
        for v in viol:
            print('  [%s] %s\n      %s' % (v['rule'], v['app'], v['detail']))
    if a.json_out:
        json.dump(viol, open(a.json_out, 'w'), indent=1)
        print('  wrote %s' % a.json_out)
    if viol:
        print('\nBLOCK: %d apps would acquire trials for a disease they are not about.' % len(apps))
        return 1
    print('\nPASS')
    return 0


if __name__ == '__main__':
    sys.exit(main())
