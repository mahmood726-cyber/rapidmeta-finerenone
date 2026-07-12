#!/usr/bin/env python
"""ADVISORY build gate: outcome commensurability + measure-provenance.

Companion to the (blocking) count/effect gate. This one is ADVISORY-first — the
app renderer already selects the display measure from `estimandType`, so these
are provenance/quality smells that need human review, not auto-mutations:

  * ratio_value_nonpositive : a value <= 0 sits in a ratio (publishedHR) slot
        (a ratio can't be <= 0 -> it's an MD/absolute mislabeled) [FIX 4]
  * additive_ratio_ci       : the CI around a ratio is additively (not
        multiplicatively) symmetric -> a proportion/MD CI mislabeled as a ratio
  * surrogate_pooled        : a biomarker/surrogate outcome (amyloid-PET, eGFR
        slope, SUVR, ...) carries a ratio effect or is pooled with clinical
        outcomes [FIX 4 — separate surrogate from clinical]
  * mixed_estimand_pool     : one app mixes MD with OR/RR/HR trials in a pool

Emits a findings report; returns findings from check_file() for wiring into the
ship path. Non-zero exit only with --strict.
"""
from __future__ import annotations
import sys, io, os, re, glob, math, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import count_consistency as cc
from assert_count_effect_consistency import _objbody, _top_entries, _num, _sval

ROOT = os.environ.get('RAPIDMETA_REPO_ROOT',
                      os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SURROGATE = re.compile(
    r'amyloid|suvr|pittsburgh compound|\bpet\b|egfr slope|biomarker|'
    r'hba1c|ldl|blood pressure|proteinuria|tumou?r size|ejection fraction|'
    r'viral load|cd4|bone mineral', re.I)
RATIO = ('OR', 'RR', 'HR', 'IRR')

def _additive_ratio_ci(hr, lci, uci):
    if None in (hr, lci, uci) or hr <= 0 or lci <= 0 or uci <= 0: return False
    if abs(hr - 1) <= 0.05: return False
    add_sym = abs((uci - hr) - (hr - lci)) < 0.02 * abs(hr)
    logmid = math.exp((math.log(lci) + math.log(uci)) / 2)
    mult_sym = abs(logmid - hr) <= 0.1 * abs(hr)
    return add_sym and not mult_sym

def check_file(path):
    txt = open(path, encoding='utf-8', errors='replace').read()
    m = re.search(r'realData\s*:\s*\{', txt)
    if not m: return []
    body = _objbody(txt, m.end()-1)
    fn = os.path.basename(path)
    findings = []
    estset = set()
    for key, o in _top_entries(body):
        hr = _num(o, 'publishedHR'); lci = _num(o, 'hrLCI'); uci = _num(o, 'hrUCI')
        est = (_sval(o, 'estimandType') or '').upper()
        title = _sval(o, 'title') or _sval(o, 'name') or ''
        if est: estset.add(est)
        if hr is not None and hr <= 0 and est in RATIO:
            findings.append((fn, key, 'ratio_value_nonpositive',
                             f'{hr} in ratio slot with estimandType {est}'))
        if _additive_ratio_ci(hr, lci, uci) and est in RATIO:
            findings.append((fn, key, 'additive_ratio_ci',
                             f'{est}={hr} CI[{lci},{uci}] additively symmetric (ratio impossible)'))
        # surrogate outcome carrying a ratio effect / pooled as clinical
        otitle = ''
        am = re.search(r'allOutcomes:\[\{([^}]*)\}', o)
        if am: otitle = am.group(1)
        if SURROGATE.search(title + ' ' + otitle):
            findings.append((fn, key, 'surrogate_pooled',
                             f'surrogate/biomarker outcome ("{(title or otitle)[:50]}") — verify it is not pooled or shown as a clinical effect'))
    if 'MD' in estset and (set(RATIO) & estset):
        findings.append((fn, '-', 'mixed_estimand_pool',
                         f'app mixes MD with {sorted(set(RATIO)&estset)} — verify pools are separated by outcome construct'))
    return findings

def main(argv):
    strict = '--strict' in argv
    args = [a for a in argv[1:] if not a.startswith('-')]
    paths = args or sorted(glob.glob(os.path.join(ROOT, '*_REVIEW.html')))
    allf = []
    for p in paths:
        allf.extend(check_file(p))
    from collections import Counter
    by = Counter(f[2] for f in allf)
    if hasattr(sys.stdout, 'buffer') and getattr(sys.stdout,'encoding','').lower()!='utf-8':
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    print(f"[commensurability ADVISORY] {len(allf)} findings in "
          f"{len(set(f[0] for f in allf))} apps across {len(paths)} files")
    for k, n in by.most_common():
        print(f"   {k}: {n}")
    outp = os.path.join(ROOT, 'outputs', 'commensurability_findings.json')
    os.makedirs(os.path.dirname(outp), exist_ok=True)
    json.dump([{'file':a,'key':b,'code':c,'detail':d} for a,b,c,d in allf],
              open(outp,'w'), indent=1)
    print(f"   -> {outp}")
    return 1 if (strict and allf) else 0

if __name__ == '__main__':
    sys.exit(main(sys.argv))
