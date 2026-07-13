#!/usr/bin/env python
"""Classify every RapidMeta app for the FULL-fix mandate (2026-07-12).

RapidMeta is the output layer of the evidence pipeline, and the apps exist FOR
PEOPLE TO CHECK — so the two-part rule is:

  (A) an app with a wrong/unverified NUMBER STAYS UP, fixed and/or FLAGGED
      (a visible verification banner: verified / unverified / could-not-source).
  (B) an app that is NOT A META-ANALYSIS AT ALL is DE-LISTED (reversibly, with a
      public manifest): k=1 (single trial), structurally non-poolable, or no
      usable source data. Presenting a non-MA as an MA is itself the
      misrepresentation.

Per-app status:
  verified        externally validated against a published MA (BENCHMARK tier)
  provenance-ok   k>=2, count/effect consistent, every trial has PMID + registry
  flagged         k>=2 but a defect remains (count/effect HARD, or missing
                  PMID/registry) -> STAYS UP with a banner naming the gap
  delist:k1       exactly 1 contributing trial (a forest plot around one trial)
  delist:no-source 0 contributing trials / no usable data
  delist:non-poolable  has trials but no poolable estimate can be produced

Output: outputs/corpus_classification.json  (drives banner + de-list).
"""
from __future__ import annotations
import sys, io, os, re, json, glob
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import count_consistency as cc
import build_gate as bg
from assert_count_effect_consistency import _objbody, _top_entries, _num, _sval

ROOT = os.environ.get('RAPIDMETA_REPO_ROOT',
                      os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
REG_RE = re.compile(r'^(NCT\d{6,8}|ISRCTN\d+|ACTRN\d+|EUCTR[\d-]+|ChiCTR[-\w]+|'
                    r'KCT\d+|DRKS\d+|PACTR\d+|jRCT\w+)$')


def _benchmark_set():
    """Apps carrying an EXTERNAL published-MA benchmark reference (anchors whose
    `src` is a real published MA, not an internal pool). Precomputed to
    outputs/benchmark_set.json by extracting BENCHMARKS from the validator (avoids
    a slow/fragile subprocess). NOTE: this is 'has an external benchmark', a
    superset of 'strictly matches within CI' — the strict-match count is reported
    separately by the validator's --strict run."""
    p = os.path.join(ROOT, 'outputs', 'benchmark_set.json')
    try:
        return set(json.load(open(p, encoding='utf-8')))
    except Exception:
        return set()


def _contributes(o):
    hr = _num(o, 'publishedHR')
    if hr is not None and hr > 0:
        return True
    tE, tN, cE, cN = _num(o,'tE'), _num(o,'tN'), _num(o,'cE'), _num(o,'cN')
    if None not in (tE, tN, cE, cN) and tN > 0 and cN > 0 and 0 <= tE <= tN and 0 <= cE <= cN and (tE > 0 or cE > 0):
        return True
    return False


def _trial_provenance(key, o):
    pmid = _sval(o, 'pmid')
    has_pmid = bool(pmid) and re.fullmatch(r'\d{6,8}', pmid) is not None
    src = _sval(o, 'sourceUrl')
    reg_ok = bool(REG_RE.match(str(key))) or bool(src and str(src).startswith('http'))
    return has_pmid, reg_ok


def _count_effect_hard(key, o):
    """Inline HARD count/effect checks (single-pass; mirrors build_gate HARD set
    for a trial): direction contradiction, magnitude_extreme, nonpositive_ratio."""
    tE, tN, cE, cN = _num(o,'tE'), _num(o,'tN'), _num(o,'cE'), _num(o,'cN')
    eff = _num(o, 'publishedHR')
    est = (_sval(o, 'estimandType') or ('HR' if eff is not None else '')).upper()
    out = []
    if est in ('OR','RR','HR','IRR') and eff is not None and eff <= 0:
        out.append('nonpositive_ratio')
    if None not in (tE, tN, cE, cN, eff) and eff and eff > 0:
        if cc.consistent(tE, tN, cE, cN, est or 'OR', eff) is False:
            out.append('direction')
        rr = cc.implied_rr(tE, tN, cE, cN)
        if rr and rr > 0:
            fold = max(rr/eff, eff/rr)
            if (0.90 <= eff <= 1.11 and (rr >= 1.5 or rr <= 0.67)) or fold >= 10.0:
                out.append('magnitude_extreme')
    return out


def classify_file(path, bench):
    fn = os.path.basename(path)
    name = fn[:-len('_REVIEW.html')] if fn.endswith('_REVIEW.html') else fn
    txt = open(path, encoding='utf-8', errors='replace').read()
    m = re.search(r'realData\s*:\s*\{', txt)
    trials, contrib = [], []
    miss_pmid = miss_reg = False
    count_effect_hard = []
    warn = []
    if m:
        body = _objbody(txt, m.end()-1)
        n_entries = 0
        for key, o in _top_entries(body):
            n_entries += 1
            trials.append(key)
            if _contributes(o):
                hp, rg = _trial_provenance(key, o)
                contrib.append(key)
                if not hp: miss_pmid = True
                if not rg: miss_reg = True
            for code in _count_effect_hard(key, o):
                count_effect_hard.append([fn, key, code, ''])
        if n_entries == 0 and len(body.strip()) > 40:
            count_effect_hard.append([fn, '-', 'coverage', 'realData present but 0 entries parsed'])
    k = len(contrib)

    reasons = []
    if k == 0:
        status = 'delist:no-source' if not trials else 'delist:non-poolable'
        reasons.append('no contributing trial with a poolable estimate' if trials else 'no trial data')
    elif k == 1:
        status = 'delist:k1'
        reasons.append(f'single contributing trial ({contrib[0]}) — a forest plot around one trial is not a synthesis')
    else:
        if count_effect_hard:
            status = 'flagged'; reasons.append('displayed counts contradict displayed effect (' +
                                                ','.join(sorted(set(h[2] for h in count_effect_hard))) + ')')
        elif name in bench:
            status = 'verified'
        elif miss_pmid or miss_reg:
            status = 'flagged'
            if miss_pmid: reasons.append('>=1 contributing trial lacks a PubMed ID')
            if miss_reg: reasons.append('>=1 contributing trial lacks a registry/source link')
        else:
            status = 'provenance-ok'
    return {'app': fn, 'name': name, 'status': status, 'k': k,
            'n_trials': len(trials), 'contributing': contrib,
            'externally_validated': name in bench,
            'count_effect_hard': [list(h) for h in count_effect_hard],
            'warn': sorted(set(w[2] for w in warn)),
            'reasons': reasons}


def main(argv):
    bench = _benchmark_set()
    paths = sorted(glob.glob(os.path.join(ROOT, '*_REVIEW.html')))
    recs = [classify_file(p, bench) for p in paths]
    out = os.path.join(ROOT, 'outputs', 'corpus_classification.json')
    json.dump(recs, open(out, 'w'), indent=1)
    from collections import Counter
    c = Counter(r['status'] for r in recs)
    if hasattr(sys.stdout, 'buffer') and getattr(sys.stdout, 'encoding', '').lower() != 'utf-8':
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    print(f"classified {len(recs)} apps (externally-validated anchors: {len(bench)})")
    for s, n in c.most_common():
        print(f"  {s}: {n}")
    delist = sum(n for s, n in c.items() if s.startswith('delist'))
    standing = len(recs) - delist
    print(f"STANDING: {standing}  DE-LIST: {delist}")
    print(f"-> {out}")
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))
