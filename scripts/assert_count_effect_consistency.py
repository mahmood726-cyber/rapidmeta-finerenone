#!/usr/bin/env python
"""BUILD-TIME GATE: a shipped app must never display arm counts that contradict
its displayed ratio effect. This is the structural fix for the count-provenance
class (2026-07-12): the AACT row-selector sourced counts and effect independently
and never reconciled them, so ~23% of checkable binary trials showed a table that
implied the opposite of the plotted effect.

Scans one file, a list of files, or the whole corpus; exits non-zero (BLOCKS) if
any trial's counts imply the opposite direction to its effect. Callable as a
library (check_file / scan) or a CLI gate.

Usage:
  python scripts/assert_count_effect_consistency.py                # whole repo
  python scripts/assert_count_effect_consistency.py FILE ...        # given files
"""
from __future__ import annotations
import sys, io, os, re, glob
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import count_consistency as cc

# Reassign stdout only when run as a CLI. Doing it at import time corrupts
# pytest's capture tmpfile (lessons.md: module-level sys.stdout reassignment).
def _utf8_stdout():
    if hasattr(sys.stdout, 'buffer') and getattr(sys.stdout, 'encoding', '').lower() != 'utf-8':
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

ROOT = os.environ.get('RAPIDMETA_REPO_ROOT',
                      os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_TRIAL = re.compile(r'"?(NCT\d{6,8})"?\s*:\s*\{')

def _objbody(s, i):
    depth = 0; st = i
    while i < len(s):
        c = s[i]
        if c == '{': depth += 1
        elif c == '}':
            depth -= 1
            if depth == 0: return s[st:i+1]
        i += 1
    return s[st:]

def _num(o, k):
    m = re.search(r'(?<![A-Za-z_])'+k+r':\s*(-?\d+\.?\d*|null)', o)
    if not m: return None
    return None if m.group(1) == 'null' else float(m.group(1))

def _sval(o, k):
    m = re.search(k+r':"([^"]*)"', o)
    return m.group(1) if m else None

def check_file(path):
    """Return list of violation dicts for one app file."""
    txt = open(path, encoding='utf-8', errors='replace').read()
    m = re.search(r'realData:\{', txt)
    if not m: return []
    body = _objbody(txt, m.end()-1)
    viol = []
    for tm in _TRIAL.finditer(body):
        nct = tm.group(1)
        o = _objbody(body, tm.end()-1)
        tE, tN, cE, cN = _num(o,'tE'), _num(o,'tN'), _num(o,'cE'), _num(o,'cN')
        pubHR = _num(o,'publishedHR')
        est = _sval(o,'estimandType') or ('HR' if pubHR is not None else '')
        # only checkable when we have full counts + a ratio effect
        if None in (tE,tN,cE,cN,pubHR): continue
        if cc.consistent(tE,tN,cE,cN, est or 'OR', pubHR) is False:
            viol.append({'file': os.path.basename(path), 'nct': nct,
                         'name': _sval(o,'name'), 'tE':tE,'tN':tN,'cE':cE,'cN':cN,
                         'effect': pubHR, 'measure': est,
                         'impliedRR': round(cc.implied_rr(tE,tN,cE,cN),3)})
    return viol

def scan(paths):
    all_v = []
    for p in paths:
        all_v.extend(check_file(p))
    return all_v

def main(argv):
    args = [a for a in argv[1:] if not a.startswith('-')]
    if args:
        paths = args
    else:
        paths = sorted(glob.glob(os.path.join(ROOT, '*_REVIEW.html')))
    viol = scan(paths)
    checked = len(paths)
    if viol:
        print(f"[BLOCK] count/effect direction contradictions: {len(viol)} "
              f"trial(s) in {len(set(v['file'] for v in viol))} app(s) "
              f"across {checked} file(s) scanned")
        for v in viol[:40]:
            print(f"   {v['file']}  {v['nct']} {str(v['name'])[:14]:14} "
                  f"tE{v['tE']:.0f}/{v['tN']:.0f} cE{v['cE']:.0f}/{v['cN']:.0f} "
                  f"effect={v['effect']}({v['measure']}) impliedRR={v['impliedRR']}")
        return 1
    print(f"[OK] no count/effect contradictions across {checked} file(s) scanned")
    return 0

if __name__ == '__main__':
    _utf8_stdout()
    sys.exit(main(sys.argv))
