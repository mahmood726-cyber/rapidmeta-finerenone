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
import sys, io, os, re, glob, argparse, collections
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
    # match both unquoted (tE:4) and quoted ("tE":4 / 'tE':4) JS/JSON keys so a
    # formatter change can't silently bypass the checks (cross-vendor 2026-07-12).
    # Also match leading-dot decimals (publishedHR:.25) — missing these silently
    # skipped the count/effect check for HR/VE trials written that way (2026-07-13).
    m = re.search(r'''(?<![A-Za-z_])["']?''' + k + r'''["']?\s*:\s*(-?(?:\d+\.?\d*|\.\d+)|null)''', o)
    if not m: return None
    return None if m.group(1) == 'null' else float(m.group(1))

def _sval(o, k):
    m = re.search(r'''(?<![A-Za-z_])["']?''' + k + r'''["']?\s*:\s*(?:"([^"]*)"|'([^']*)')''', o)
    if not m: return None
    return m.group(1) if m.group(1) is not None else m.group(2)

def _new_stats():
    """Trial-level accounting. The gate used to report only len(paths) -- the
    FILE denominator -- which reads as full coverage. It is not: most trials
    are skipped, and `cc.consistent` returns None ("cannot verify") far more
    often than False. count_consistency.py:69-74 states explicitly that callers
    must NOT treat None as a pass; this accounting is what makes that possible.
    """
    return {
        'trials': 0,
        'checked_pass': 0,
        'checked_violation': 0,
        'skipped_missing_field': 0,
        'skipped_undetermined': 0,
        'missing_by_field': collections.Counter(),
    }


def check_file(path, stats=None):
    """Return list of violation dicts for one app file.

    If `stats` is given, trial-level counters are accumulated into it so the
    caller can report what was actually adjudicated rather than how many files
    were opened.
    """
    if stats is None:
        stats = _new_stats()
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
        stats['trials'] += 1
        tE, tN, cE, cN = _num(o,'tE'), _num(o,'tN'), _num(o,'cE'), _num(o,'cN')
        pubHR = _num(o,'publishedHR')
        est = _sval(o,'estimandType') or ('HR' if pubHR is not None else '')
        if None in (tE,tN,cE,cN,pubHR):
            # NOT a pass -- this trial carries no adjudicable count/effect pair.
            stats['skipped_missing_field'] += 1
            for fname, fval in (('tE',tE),('tN',tN),('cE',cE),('cN',cN),
                                ('publishedHR',pubHR)):
                if fval is None:
                    stats['missing_by_field'][fname] += 1
            continue
        verdict = cc.consistent(tE,tN,cE,cN, est or 'OR', pubHR)
        if verdict is None:
            # Contract (count_consistency.py:69-74): None is "cannot verify",
            # NOT a pass. Typically one side lands in the neutral band
            # (0.87-1.15) or the measure is non-ratio.
            stats['skipped_undetermined'] += 1
            continue
        if verdict is not False:
            stats['checked_pass'] += 1
        else:
            stats['checked_violation'] += 1
        if verdict is False:
            viol.append({'file': os.path.basename(path), 'nct': key,
                         'name': _sval(o,'name'), 'tE':tE,'tN':tN,'cE':cE,'cN':cN,
                         'effect': pubHR, 'measure': est,
                         'impliedRR': round(cc.implied_rr(tE,tN,cE,cN),3)})
    return viol

def scan(paths, stats=None):
    """Return the list of violations.

    Returns a plain list, NOT a tuple -- `tests/test_count_effect_consistency.py`
    and any other caller does `viol = gate.scan(...)` and indexes the result.
    Trial-level accounting is returned via the optional `stats` out-parameter
    instead, so adding coverage reporting cannot break existing callers.
    """
    if stats is None:
        stats = _new_stats()
    all_v = []
    for p in paths:
        all_v.extend(check_file(p, stats))
    return all_v


def _report_coverage(stats, n_files):
    adjudicated = stats['checked_pass'] + stats['checked_violation']
    trials = stats['trials']
    pct = (100.0 * adjudicated / trials) if trials else 0.0
    print(f"  files scanned            {n_files}")
    print(f"  trials found             {trials}")
    print(f"    ADJUDICATED            {adjudicated}  ({pct:.1f}% of trials)")
    print(f"      pass                 {stats['checked_pass']}")
    print(f"      violation            {stats['checked_violation']}")
    print(f"    NOT ADJUDICATED        {trials - adjudicated}  "
          f"({100.0 - pct:.1f}%)  <- NOT a pass")
    print(f"      missing field        {stats['skipped_missing_field']}")
    if stats['missing_by_field']:
        detail = ', '.join(f"{k} {v}" for k, v in
                           stats['missing_by_field'].most_common())
        print(f"        by field:          {detail}")
    print(f"      undetermined (None)  {stats['skipped_undetermined']}")
    return pct


def main(argv):
    ap = argparse.ArgumentParser(
        description="Assert stored per-arm counts do not contradict the stored "
                    "effect direction. Reports the TRIAL-level denominator.")
    ap.add_argument('paths', nargs='*',
                    help="app files to check (default: all *_REVIEW.html)")
    ap.add_argument('--min-coverage', type=float, default=None, metavar='PCT',
                    help="fail (exit 1) if fewer than PCT%% of trials were "
                         "actually adjudicated. Without this the gate can only "
                         "fail on a positive contradiction, never on blindness.")
    args = ap.parse_args(argv[1:])

    paths = args.paths or sorted(glob.glob(os.path.join(ROOT, '*_REVIEW.html')))
    stats = _new_stats()
    viol = scan(paths, stats)

    if viol:
        print(f"[BLOCK] count/effect direction contradictions: {len(viol)} "
              f"trial(s) in {len(set(v['file'] for v in viol))} app(s)")
        for v in viol[:40]:
            print(f"   {v['file']}  {v['nct']} {str(v['name'])[:14]:14} "
                  f"tE{v['tE']:.0f}/{v['tN']:.0f} cE{v['cE']:.0f}/{v['cN']:.0f} "
                  f"effect={v['effect']}({v['measure']}) impliedRR={v['impliedRR']}")
        print()
        _report_coverage(stats, len(paths))
        return 1

    print("[OK] no count/effect contradiction found among the trials this gate "
          "was ABLE to adjudicate.")
    print("     This is NOT a clean-corpus claim -- see the denominator below.")
    print()
    pct = _report_coverage(stats, len(paths))

    if args.min_coverage is not None and pct < args.min_coverage:
        print()
        print(f"[BLOCK] adjudicated only {pct:.1f}% of trials, "
              f"below --min-coverage {args.min_coverage:.1f}%")
        return 1
    return 0

if __name__ == '__main__':
    _utf8_stdout()
    sys.exit(main(sys.argv))
