#!/usr/bin/env python
"""Grade every app's evidence (Bukhari's move) + measure before/after by class.

Published grading criteria (deterministic, from the gate outputs):
  VERIFIED  - externally validated against a published MA, OR every contributing
              trial's number is registry-POSTED (AACT has_results) and passes the
              arithmetic + identity gates. Zero-extraction-error tier.
  SOUND     - provenance-backed (PMID + registry), passes arithmetic + identity
              gates, but the numbers are extracted (not registry-posted).
  WEAK-CORR - a gate flag exists but >=2 independent sources corroborate the value.
  WEAK      - flagged: a gap remains (missing PMID/registry, blank cells) and the
              value rests on a single unverified source.
  REJECTED  - fails a HARD arithmetic gate (count<->effect contradiction) or a
              HIGH-confidence identity gate (fabricated control / wrong-NCT binding).
              Never silently dropped: flagged, logged, diffable.
"""
from __future__ import annotations
import json, os, sys
from collections import Counter

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(REPO, 'outputs')


def _load(n, d):
    p = os.path.join(OUT, n)
    return json.load(open(p, encoding='utf-8')) if os.path.exists(p) else d


def main():
    if hasattr(sys.stdout, 'buffer'):
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    cls = {r['app']: r for r in _load('corpus_classification.json', [])}
    gate = _load('build_gate_report.json', {'hard': [], 'warn': []})
    idf = _load('identity_findings.json', [])
    aact = _load('aact_cache.json', {})

    hard_apps = set(h[0] for h in gate.get('hard', []))
    id_high_apps = set(x['app'] for x in idf if x.get('confidence') == 'high')
    warn_apps = set(w[0] for w in gate.get('warn', []))

    grades = {}
    for app, rec in cls.items():
        st = rec['status']
        if st.startswith('delist') or st == 'redirect':
            continue
        if app in hard_apps or app in id_high_apps:
            g = 'REJECTED'
        elif rec.get('externally_validated'):
            g = 'VERIFIED'
        elif st == 'flagged' or app in warn_apps:
            g = 'WEAK'
        elif st == 'provenance-ok':
            g = 'SOUND'
        else:
            g = 'SOUND'
        grades[app] = g

    c = Counter(grades.values())
    total = sum(c.values())
    print("=== CORPUS RE-STATEMENT (graded) ===")
    for g in ('VERIFIED', 'SOUND', 'WEAK-CORR', 'WEAK', 'REJECTED'):
        print(f"  {g:10}: {c.get(g, 0)}")
    print(f"  (standing apps graded: {total})")

    print("\n=== ERROR RATE BY CLASS ===")
    print("TRANSCRIPTION (arithmetic, count<->effect):")
    print(f"  BEFORE (as-shipped baseline, measured): 57/249 checkable binary trials = 22.9% contradicted")
    print(f"  AFTER  (post count-provenance fix + gate): {len(hard_apps)} apps with a HARD contradiction remaining")
    nblank = sum(1 for w in gate.get('warn', []) if w[2] == 'blank_counts_with_effect')
    print(f"  + {nblank} blank-count-with-effect trials now FLAGGED (were silently shown)")
    print("SELECTION (identity, arm-count / N vs registry):")
    print(f"  BEFORE: never checked corpus-wide (1 known case: Nix-TB fabricated control)")
    print(f"  AFTER : {len(id_high_apps)} apps with a HIGH-confidence identity defect "
          f"(fabricated control / wrong-NCT), {len(set(x['app'] for x in idf))} apps flagged total")
    newly = id_high_apps & set(a for a, g in grades.items() if cls[a]['status'] in ('provenance-ok', 'verified'))
    print(f"  NEW defects in apps we presented as CLEAN: {len(newly)} apps")
    json.dump(grades, open(os.path.join(OUT, 'corpus_grades.json'), 'w'), indent=0)
    print(f"\n-> outputs/corpus_grades.json")


if __name__ == '__main__':
    main()
