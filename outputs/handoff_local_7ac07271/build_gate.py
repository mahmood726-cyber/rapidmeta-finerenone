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


def _magnitude_findings(path):
    """Split counts-vs-effect magnitude gaps into HARD (internally inconsistent —
    the displayed effect and the counts cannot both be right) and WARN (a large
    but explicable OR/RR/HR divergence). HARD when the effect is ~null but the
    counts imply a strong effect (the neutral-band contradiction Codex flagged),
    or when the fold-gap is beyond any legitimate OR/RR/HR difference (>=10x)."""
    txt = open(path, encoding='utf-8', errors='replace').read()
    m = re.search(r'realData\s*:\s*\{', txt)
    if not m: return [], []
    body = ceg._objbody(txt, m.end()-1); fn = os.path.basename(path)
    hard, warn = [], []
    for key, o in ceg._top_entries(body):
        tE, tN, cE, cN = ceg._num(o,'tE'), ceg._num(o,'tN'), ceg._num(o,'cE'), ceg._num(o,'cN')
        eff = ceg._num(o, 'publishedHR')
        if None in (tE, tN, cE, cN, eff) or eff <= 0: continue
        rr = cc.implied_rr(tE, tN, cE, cN)
        if rr is None or rr <= 0: continue
        fold = max(rr/eff, eff/rr)
        eff_neutral = 0.90 <= eff <= 1.11
        counts_strong = rr >= 1.5 or rr <= 0.67
        if (eff_neutral and counts_strong) or fold >= 10.0:
            hard.append((fn, key, 'magnitude_extreme',
                         f'counts imply {rr:.2f} but displayed effect is {eff} '
                         f'({fold:.1f}x gap; effect ~null while counts strong)' if eff_neutral
                         else f'counts imply {rr:.2f} but displayed effect is {eff} ({fold:.1f}x gap)'))
        elif fold >= 5.0:
            warn.append((fn, key, 'magnitude_divergence',
                         f'counts imply {rr:.2f} but displayed effect is {eff} ({fold:.1f}x gap)'))
    return hard, warn


def gate_file(path):
    hard, warn = [], []
    # direction + coverage (from the count gate) — HARD, internal-consistency only
    for v in ceg.check_file(path):
        code = 'coverage' if v.get('measure') == 'COVERAGE' else 'direction'
        hard.append((v['file'], v['nct'], code,
                     v.get('coverage_failure') or f"counts imply {v['impliedRR']} vs effect {v['effect']}"))
    hard += _nonpositive_ratio(path)        # a ratio <=0 is impossible -> HARD
    mh, mw = _magnitude_findings(path)
    hard += mh; warn += mw
    # additive_ratio_ci + year are NOT false-positive-free (a legit rounded ratio
    # CI can look additive; `year` semantics vary trial/completion/epub/print) ->
    # WARN, not HARD, to keep the HARD set genuinely blockable (Codex 2026-07-12).
    for f in comg.check_file(path):
        if f[2] in ('additive_ratio_ci', 'surrogate_pooled', 'mixed_estimand_pool'):
            warn.append(f)
    warn += _year_findings(path)
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
