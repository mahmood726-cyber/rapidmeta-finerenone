#!/usr/bin/env python
"""IDENTITY GATE, corpus-wide — the class nothing in RapidMeta has ever checked.

For every trial in every app, compare what the app SHOWS to what the registry
REGISTERED (AACT, offline). Two deterministic checks:

  A. arm-count / Nix-TB fabricated-control: the app shows a populated comparator
     arm (cN>0) for a trial the registry registered as SINGLE-ARM (design_groups
     == 1). The control arm is fabricated or an undisclosed external control.
     A pool that mixes a fabricated control silently corrupts the estimate.
  B. N-vs-enrollment: the app's total N (tN+cN) exceeds the registry enrollment
     by >50%. Either the wrong trial is bound to this NCT, or N is inflated.

Honest caveat: A can be a LEGITIMATE external-control comparison (a known MA move)
— so it is a FLAG for review, never an auto-delete. We report, we don't quietly
fix. Output: outputs/identity_findings.json  (each tagged new-vs-already-flagged).
"""
from __future__ import annotations
import glob, json, os, re, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from assert_count_effect_consistency import _objbody, _top_entries, _num  # noqa
import aact_lookup

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def sweep():
    aact = aact_lookup.load()
    cls = {r['app']: r['status'] for r in json.load(
        open(os.path.join(REPO, 'outputs', 'corpus_classification.json'), encoding='utf-8'))}
    findings = []
    for f in sorted(glob.glob(os.path.join(REPO, '*_REVIEW.html'))):
        fn = os.path.basename(f)
        txt = open(f, encoding='utf-8', errors='replace').read()
        m = re.search(r'realData\s*:\s*\{', txt)
        if not m:
            continue
        for key, o in _top_entries(_objbody(txt, m.end() - 1)):
            nct = key if re.match(r'NCT\d{8}', str(key)) else None
            if not nct:
                mm = re.search(r'NCT\d{8}', str(key))
                nct = mm.group(0) if mm else None
            if not nct or nct not in aact:
                continue
            reg = aact[nct]
            tN, cE, cN = _num(o,'tN'), _num(o,'cE'), _num(o,'cN')
            shows_comparator = cN is not None and cN > 0
            # A. arm-count / Nix-TB. HIGH-confidence: verified 2/2 on live CT.gov
            # (fabricated control on single-arm extension; wrong-NCT binding).
            if shows_comparator and reg.get('arms') == 1:
                findings.append({'app': fn, 'nct': nct, 'check': 'arm_count_single_but_comparator',
                                 'shown': f'comparator arm cN={int(cN)}', 'registry': 'single-arm (design_groups=1)',
                                 'severity': 'flag-review', 'confidence': 'high', 'app_status': cls.get(fn, '?')})
            # B. N vs enrollment
            try:
                enr = float(reg.get('enrollment')) if reg.get('enrollment') not in (None, '') else None
            except (TypeError, ValueError):
                enr = None
            if tN is not None and cN is not None and enr and enr > 0:
                shown_n = tN + cN
                if shown_n > enr * 1.5 and shown_n - enr > 30:
                    findings.append({'app': fn, 'nct': nct, 'check': 'N_exceeds_enrollment',
                                     'shown': f'N={int(shown_n)}', 'registry': f'enrollment={int(enr)}',
                                     'severity': 'flag-review', 'app_status': cls.get(fn, '?')})
    return findings


def main():
    if hasattr(sys.stdout, 'buffer'):
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    findings = sweep()
    json.dump(findings, open(os.path.join(REPO, 'outputs', 'identity_findings.json'), 'w',
                             encoding='utf-8'), indent=1)
    from collections import Counter
    by_check = Counter(x['check'] for x in findings)
    apps = set(x['app'] for x in findings)
    # NEW = in an app NOT already flagged/de-listed (i.e., a provenance-ok/verified app
    # we would otherwise present as clean)
    new = [x for x in findings if x['app_status'] in ('provenance-ok', 'verified')]
    new_apps = set(x['app'] for x in new)
    print(f"IDENTITY GATE — {len(findings)} findings across {len(apps)} apps")
    for c, n in by_check.most_common():
        print(f"  {c}: {n}")
    print(f"\nNEW defects (in apps currently presented as CLEAN provenance-ok/verified): "
          f"{len(new)} findings in {len(new_apps)} apps")
    print("  — nothing else in RapidMeta had flagged these.")
    for x in new[:12]:
        print(f"     {x['app'][:40]:40} {x['nct']} {x['check']} ({x['shown']} vs {x['registry']})")
    return findings


if __name__ == '__main__':
    main()
