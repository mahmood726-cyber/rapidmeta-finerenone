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
# realData keys are heterogeneous (NCT, PMID:, KCT, ISRCTN, LEGACY-ISRCTN-...,
# NULLED:, ...), so we walk the TOP-LEVEL keys generically rather than matching
# a fixed key shape — a formatter/schema change can't silently drop coverage
# (cross-vendor objection 2026-07-12).
_KEY = re.compile(r"""\s*(?:"([^"]+)"|'([^']+)'|([A-Za-z_][\w:.\-]*))\s*:\s*""")

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

def _skip_value(s, i):
    """From index i (start of a value), return index just past it (top level)."""
    while i < len(s) and s[i] in ' \t\r\n': i += 1
    if i >= len(s): return i
    c = s[i]
    if c == '{':
        return i + len(_objbody(s, i))
    if c == '[':
        depth = 0
        while i < len(s):
            if s[i] == '[': depth += 1
            elif s[i] == ']':
                depth -= 1
                if depth == 0: return i + 1
            elif s[i] == '"':
                i += 1
                while i < len(s) and s[i] != '"':
                    if s[i] == '\\': i += 1
                    i += 1
            i += 1
        return i
    if c == '"':
        i += 1
        while i < len(s) and s[i] != '"':
            if s[i] == '\\': i += 1
            i += 1
        return i + 1
    # number / literal: read until top-level , or }
    while i < len(s) and s[i] not in ',}':
        i += 1
    return i

def _top_entries(body):
    """Yield (key, object_text) for each TOP-LEVEL key whose value is an object.
    body includes the outer { } of realData."""
    i = 1  # just inside the opening brace
    n = len(body)
    while i < n:
        while i < n and body[i] in ' \t\r\n,': i += 1
        if i >= n or body[i] == '}': break
        km = _KEY.match(body, i)
        if not km:
            i += 1; continue
        key = km.group(1) or km.group(2) or km.group(3)
        j = km.end()
        while j < n and body[j] in ' \t\r\n': j += 1
        if j < n and body[j] == '{':
            obj = _objbody(body, j)
            yield key, obj
            i = j + len(obj)
        else:
            i = _skip_value(body, j)

def _num(o, k):
    m = re.search(r'(?<![A-Za-z_])'+k+r':\s*(-?\d+\.?\d*|null)', o)
    if not m: return None
    return None if m.group(1) == 'null' else float(m.group(1))

def _sval(o, k):
    m = re.search(k+r'''\s*:\s*(?:"([^"]*)"|'([^']*)')''', o)
    if not m: return None
    return m.group(1) if m.group(1) is not None else m.group(2)

def check_file(path):
    """Return list of violation dicts for one app file."""
    txt = open(path, encoding='utf-8', errors='replace').read()
    # Tolerate a space after the colon (realData: {) so a formatter change can't
    # silently drop coverage (cross-vendor objection 2026-07-12).
    m = re.search(r'realData\s*:\s*\{', txt)
    if not m: return []
    body = _objbody(txt, m.end()-1)
    viol = []
    entries = list(_top_entries(body))
    # Fail closed: a NON-EMPTY realData block that parses ZERO entries is a
    # coverage failure (parser drift / corruption), not a clean pass. A
    # legitimately empty realData ({} -> tiny body) is fine.
    if not entries and len(body.strip()) > 40:
        return [{'file': os.path.basename(path), 'nct': '-', 'name': None,
                 'tE': 0, 'tN': 0, 'cE': 0, 'cN': 0, 'effect': None,
                 'measure': 'COVERAGE', 'impliedRR': None,
                 'coverage_failure': f'realData present ({len(body)} chars) but 0 entries parsed'}]
    for key, o in entries:
        tE, tN, cE, cN = _num(o,'tE'), _num(o,'tN'), _num(o,'cE'), _num(o,'cN')
        pubHR = _num(o,'publishedHR')
        est = _sval(o,'estimandType') or ('HR' if pubHR is not None else '')
        if None in (tE,tN,cE,cN,pubHR): continue
        if cc.consistent(tE,tN,cE,cN, est or 'OR', pubHR) is False:
            viol.append({'file': os.path.basename(path), 'nct': key,
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
