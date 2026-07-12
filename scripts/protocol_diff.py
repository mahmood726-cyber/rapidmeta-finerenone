#!/usr/bin/env python
"""Protocol-as-registered vs analysis-as-run DIFF (STAGED — not deployed).

Compares a registered protocol (protocol/<REVIEW>.json, hash-locked by
preregister_protocol.py) against the analysis actually run — extracted from the
built app's realData/PICO — and reports outcome-switching and PICO drift. This
is the discipline registries impose on trialists, turned on the reviewer: a
living meta-analysis that quietly swaps its primary outcome or widens its PICO
can no longer hide it, because the app itself carries the diff.

The diff is deliberately conservative and text-normalised; it flags for HUMAN
review, it does not auto-fail (a legitimate protocol amendment is allowed — it
just must be visible and dated, per Cochrane's "differences between protocol and
review" section).

Usage:
  python scripts/protocol_diff.py protocol/<REVIEW>.json <APP>_REVIEW.html
"""
from __future__ import annotations
import sys, io, os, re, json

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from assert_count_effect_consistency import _objbody, _top_entries, _num, _sval


_STOP = {'of', 'or', 'for', 'a', 'the', 'and', 'to', 'in', 'with', 'composite',
         'time', 'first', 'event', 'events', 'endpoint'}
_SYN = {'hf': 'heartfailure', 'heart': '', 'failure': 'heartfailure',
        'hosp': 'hospitalization', 'hospitalisation': 'hospitalization',
        'mi': 'myocardialinfarction', 'cv': 'cardiovascular', 'egfr': 'egfr'}

def _norm(s):
    return re.sub(r'\s+', ' ', re.sub(r'[^a-z0-9 ]', ' ', (s or '').lower())).strip()

def _tokens(s):
    toks = []
    for w in _norm(s).split():
        w = _SYN.get(w, w)
        if w and w not in _STOP:
            toks.append(w)
    return set(toks)

def _outcome_match(a, b):
    """True if two outcome descriptions are the same concept (token overlap)."""
    ta, tb = _tokens(a), _tokens(b)
    if not ta or not tb:
        return False
    shared = len(ta & tb)
    return shared / min(len(ta), len(tb)) >= 0.6


def analysis_as_run(app_path):
    """Extract the analysis actually run from the app: the set of primary
    outcome titles, all outcome titles, and the effect measures used."""
    txt = open(app_path, encoding='utf-8', errors='replace').read()
    m = re.search(r'realData\s*:\s*\{', txt)
    out = {'primary_outcomes': set(), 'all_outcomes': set(), 'measures': set(), 'n_trials': 0}
    if not m:
        return out
    body = _objbody(txt, m.end()-1)
    for key, o in _top_entries(body):
        out['n_trials'] += 1
        for om in re.finditer(r'\{[^{}]*?title:"([^"]*)"[^{}]*?\}', o):
            seg = om.group(0); title = om.group(1)
            out['all_outcomes'].add(title)
            if re.search(r'type:"PRIMARY"', seg) or '(primary)' in title.lower():
                out['primary_outcomes'].add(re.sub(r'\s*\(primary\)\s*$', '', title, flags=re.I))
            mm = re.search(r'estimandType:"([^"]*)"', seg)
            if mm: out['measures'].add(mm.group(1).upper())
    return out


def diff(protocol_path, app_path):
    proto = json.load(open(protocol_path, encoding='utf-8'))
    run = analysis_as_run(app_path)
    reg_primary = proto.get('primary_outcome', '')
    reg_measure = (proto.get('planned_analysis') or {}).get('effect_measure', '').upper()

    findings = []
    # 1. primary-outcome switch: the registered primary must match a RUN PRIMARY
    # (not merely appear as some secondary outcome — that IS a switch).
    matched_primary = any(_outcome_match(reg_primary, p) for p in run['primary_outcomes'])
    demoted = (not matched_primary) and any(_outcome_match(reg_primary, t) for t in run['all_outcomes'])
    if reg_primary and not matched_primary:
        findings.append({'code': 'primary_outcome_switch', 'severity': 'HIGH',
                         'registered': reg_primary,
                         'run_primaries': sorted(run['primary_outcomes'])[:5],
                         'detail': ('registered primary was DEMOTED to a secondary in the run analysis'
                                    if demoted else
                                    'the registered primary outcome does not appear among the analysed primary outcomes')})
    # 2. effect-measure change
    if reg_measure and run['measures'] and reg_measure not in run['measures']:
        findings.append({'code': 'effect_measure_change', 'severity': 'MEDIUM',
                         'registered': reg_measure, 'run': sorted(run['measures']),
                         'detail': 'planned effect measure not among those used'})
    # 3. registration status (was the protocol locked before the run?)
    lockpath = os.path.join(os.path.dirname(protocol_path), proto.get('review_id', '') + '.LOCK.json')
    lock = json.load(open(lockpath, encoding='utf-8')) if os.path.exists(lockpath) else None
    if lock is None:
        findings.append({'code': 'unregistered', 'severity': 'HIGH',
                         'detail': 'no protocol lock — this analysis was never pre-registered'})
    elif not lock.get('committed_before_search'):
        findings.append({'code': 'lock_not_committed', 'severity': 'MEDIUM',
                         'detail': 'protocol lock exists but the protocol file is not git-committed (timestamp not tamper-evident)'})

    verdict = 'DRIFT' if any(f['severity'] == 'HIGH' for f in findings) else \
              ('MINOR-DRIFT' if findings else 'CONCORDANT')
    return {
        'review_id': proto.get('review_id'),
        'registered_primary_outcome': reg_primary,
        'run_primary_outcomes': sorted(run['primary_outcomes']),
        'protocol_sha256': (lock or {}).get('protocol_sha256'),
        'git_commit_at_lock': (lock or {}).get('git_commit_at_lock'),
        'locked_utc': (lock or {}).get('locked_utc'),
        'verdict': verdict,
        'findings': findings,
    }


def main(argv):
    if len(argv) < 3:
        print(__doc__); return 2
    r = diff(argv[1], argv[2])
    print(json.dumps(r, indent=2, ensure_ascii=False))
    return 0


if __name__ == '__main__':
    if hasattr(sys.stdout, 'buffer') and getattr(sys.stdout, 'encoding', '').lower() != 'utf-8':
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.exit(main(sys.argv))
