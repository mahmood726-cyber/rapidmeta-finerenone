#!/usr/bin/env python
"""RapidMeta MANDATORY build gate.

Since RapidMeta is now the OUTPUT LAYER of the evidence pipeline (a Makerere
researcher's synthesis TERMINATES in a RapidMeta app), a wrong number that looks
right is the worst possible failure — the researcher has no library to catch it.
So an app that fails an OBJECTIVE provenance/consistency check MUST NOT BUILD.

This gate exits NON-ZERO on any HARD (objectively-wrong, false-positive-free)
violation, so it can be the blocking pre-ship / pre-push check. WARN findings
(incomplete but not provably wrong) are printed and never block — keeping the
HARD list false-positive-free is what makes blocking safe (the staging
provenance_gate's own design principle).

  HARD (BLOCK):
    * count/effect DIRECTION contradiction  (counts imply the opposite of effect)
    * coverage failure                       (non-empty realData parses 0 entries)
    * additive_ratio_ci                      (a ratio CI that is additively
                                              symmetric -> an RD/MD mislabeled as
                                              a ratio; impossible for a real ratio)
    * nonpositive_ratio                      (value <= 0 in a ratio-typed slot)
    * year_contradicts_pubmed                (|displayed year - PubMed year| >= 2)

  WARN (advisory, never blocks):
    * missing_pmid, surrogate_pooled, mixed_estimand_pool, magnitude_divergence

Usage:
  python scripts/build_gate.py                 # whole corpus, exit 1 if any HARD
  python scripts/build_gate.py FILE ...        # given files
  python scripts/build_gate.py --warn-as-error # also fail on WARN (strict CI)
"""
from __future__ import annotations
import sys, io, os, re, glob, json, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import count_consistency as cc
import assert_count_effect_consistency as ceg
import commensurability_gate as comg

ROOT = os.environ.get('RAPIDMETA_REPO_ROOT',
                      os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_YEAR_CACHE = os.path.join(ROOT, 'outputs', 'provenance_cache', 'pmid_year.json')
PMID_YEAR = json.load(open(_YEAR_CACHE, encoding='utf-8')) if os.path.exists(_YEAR_CACHE) else {}


def _year_findings(path):
    """HARD: displayed year must be within 1 of the PMID's PubMed year."""
    txt = open(path, encoding='utf-8', errors='replace').read()
    m = re.search(r'realData\s*:\s*\{', txt)
    if not m: return []
    body = ceg._objbody(txt, m.end()-1); fn = os.path.basename(path); out = []
    for key, o in ceg._top_entries(body):
        pmid = ceg._sval(o, 'pmid'); yr = ceg._num(o, 'year')
        if not (pmid and pmid.isdigit()) or yr is None: continue
        py = PMID_YEAR.get(pmid)
        if py is None: continue
        if abs(int(yr) - int(py)) >= 2:
            out.append((fn, key, 'year_contradicts_pubmed',
                        f'displayed year {int(yr)} vs PubMed {int(py)} (gap {abs(int(yr)-int(py))})'))
    return out


def _nonpositive_ratio(path):
    txt = open(path, encoding='utf-8', errors='replace').read()
    m = re.search(r'realData\s*:\s*\{', txt)
    if not m: return []
    body = ceg._objbody(txt, m.end()-1); fn = os.path.basename(path); out = []
    for key, o in ceg._top_entries(body):
        est = (ceg._sval(o, 'estimandType') or '').upper()
        hr = ceg._num(o, 'publishedHR')
        if est in ('OR', 'RR', 'HR', 'IRR') and hr is not None and hr <= 0:
            out.append((fn, key, 'nonpositive_ratio', f'{hr} in ratio slot (estimandType {est})'))
    return out


HARD_CODES = {'direction', 'coverage', 'additive_ratio_ci', 'nonpositive_ratio',
              'year_contradicts_pubmed'}


def gate_file(path):
    hard, warn = [], []
    # direction + coverage (from the count gate)
    for v in ceg.check_file(path):
        code = 'coverage' if v.get('measure') == 'COVERAGE' else 'direction'
        hard.append((v['file'], v['nct'], code,
                     v.get('coverage_failure') or f"counts imply {v['impliedRR']} vs effect {v['effect']}"))
    # additive-ratio-CI (objective, from commensurability check_file)
    for f in comg.check_file(path):
        if f[2] == 'additive_ratio_ci':
            hard.append(f)
        elif f[2] in ('surrogate_pooled', 'mixed_estimand_pool'):
            warn.append(f)
    hard += _nonpositive_ratio(path)
    hard += _year_findings(path)
    warn += comg.check_magnitude(path)
    return hard, warn


def main(argv):
    warn_as_error = '--warn-as-error' in argv
    args = [a for a in argv[1:] if not a.startswith('-')]
    paths = args or sorted(glob.glob(os.path.join(ROOT, '*_REVIEW.html')))
    HARD, WARN = [], []
    for p in paths:
        h, w = gate_file(p)
        HARD += h; WARN += w
    from collections import Counter
    hc, wc = Counter(f[2] for f in HARD), Counter(f[2] for f in WARN)
    print(f"=== RapidMeta MANDATORY build gate — {len(paths)} files ===")
    print(f"HARD (BLOCK): {len(HARD)} in {len(set(f[0] for f in HARD))} apps  {dict(hc)}")
    for f in HARD[:40]:
        print(f"   [BLOCK] {f[0]}  {f[1]}  {f[2]}: {f[3][:80]}")
    print(f"WARN (advisory): {len(WARN)} in {len(set(f[0] for f in WARN))} apps  {dict(wc)}")
    json.dump({'hard': [list(f) for f in HARD], 'warn': [list(f) for f in WARN]},
              open(os.path.join(ROOT, 'outputs', 'build_gate_report.json'), 'w'), indent=1)
    if HARD:
        print(f"\nBUILD BLOCKED: {len(HARD)} hard violation(s). Fix or the apps must not ship.")
        return 1
    if warn_as_error and WARN:
        print(f"\nBUILD BLOCKED (--warn-as-error): {len(WARN)} advisory finding(s).")
        return 1
    print("\nBUILD OK: 0 hard violations.")
    return 0


if __name__ == '__main__':
    if hasattr(sys.stdout, 'buffer') and getattr(sys.stdout, 'encoding', '').lower() != 'utf-8':
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.exit(main(sys.argv))
