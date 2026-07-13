#!/usr/bin/env python
"""Assemble the CORRECTIONS CORPUS — the RLHF-analog labelled dataset.

Every correction we ever made is a labelled example: "we said X; the truth was Y;
here is the source." This is the third training stage (the human-correction stage)
the ChatGPT recipe says is worth the most per example — and the object a flag
predictor (== a reward model) is trained on.

THE ONE DISTINCTION THAT DECIDES EVERYTHING (kept explicit per record):
  gate_independent = True  -> a human found this by reading the source, NO rule
                             fired first. These are the ONLY labels that can show
                             a flag predictor catching a class the gates MISS.
  gate_independent = False -> our own gate/audit produced this label. Training a
                             predictor on these and scoring flag-recall is CIRCULAR
                             (label leakage): it can only relearn the gates.

Sources merged: count/year/label-pmid provenance JSONs (our audit), the user-error
corpus (the 1 attributed user report + its cascade), and this-session source-reads.

Output: outputs/corrections_corpus.json  (+ .md)
"""
from __future__ import annotations
import json, os, re, sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(REPO, 'outputs')
H = os.path.join(OUT, 'handoff_local_7ac07271')


def _load(p):
    try:
        return json.load(open(p, encoding='utf-8'))
    except Exception:
        return []


def _caught_by(reason):
    r = (reason or '').lower()
    if 'codex' in r or 'agy' in r or 'cross-vendor' in r or 'two-vendor' in r or 'two-lane' in r:
        return 'cross-vendor', False
    if any(g in r for g in ('magnitude_extreme', 'hard ->', 'direction', 'nonpositive',
                            'coverage', 'additive_ratio', 'year_contradicts', 'gate')):
        return 'gate', False
    if 'ct.gov' in r or 'pubmed' in r or 'full text' in r or 'source' in r or 'registry' in r:
        return 'source-read', True     # a human/registry read settled it, gate-independent
    return 'internal-logic', False     # estimand/HR-TTE reasoning — still not gate-independent


def build():
    rows = []
    # 1) count corrections (our-value 'reported' -> corrected 'recomputed')
    for r in _load(os.path.join(H, 'count_provenance_2026-07-12.json')):
        cb, gi = _caught_by(r.get('reason'))
        cls = ('estimand-mixing' if 'hr/time' in (r.get('reason') or '').lower()
               else 'transcription' if r.get('action') in ('fix', 'fix-unblank', 'rd-to-or')
               else 'transcription-blank')
        rows.append({'app': r.get('app'), 'trial': r.get('nct'), 'field': 'event counts / measure',
                     'our_value': r.get('reported'), 'corrected_value': r.get('recomputed'),
                     'source': r.get('reason'), 'error_class': cls, 'caught_by': cb,
                     'gate_independent': gi})
    # 2) year corrections (was -> now) — all from the year-vs-PubMed gate
    for r in _load(os.path.join(H, 'year_provenance_2026-07-12.json')):
        rows.append({'app': r.get('app'), 'trial': r.get('nct'), 'field': 'year',
                     'our_value': r.get('was'), 'corrected_value': r.get('now'),
                     'source': 'PubMed publication year', 'error_class': 'year',
                     'caught_by': 'gate', 'gate_independent': False})
    # 3) label / pmid corrections (corrected value only; old value not recorded)
    for r in _load(os.path.join(H, 'label_pmid_provenance_2026-07-12.json')):
        f = r.get('field')
        rows.append({'app': r.get('app'), 'trial': r.get('nct'), 'field': f,
                     'our_value': None, 'corrected_value': r.get('now'),
                     'source': 'CT.gov/PubMed identity resolver', 'error_class':
                     'label' if f == 'name' else 'pmid', 'caught_by': 'gate', 'gate_independent': False})
    # 4) the user-error corpus (1 attributed user + 128 cascade)
    for r in _load(os.path.join(OUT, 'user_error_corpus.json')):
        rows.append({'app': r.get('app'), 'trial': r.get('trial'), 'field': r.get('field'),
                     'our_value': r.get('our_value'), 'corrected_value': r.get('corrected_value'),
                     'source': r.get('source'), 'error_class': 'transcription-blank',
                     'caught_by': r.get('caught_by', 'user'),
                     'gate_independent': r.get('tier') == 'attributed-user'})
    return rows


def main():
    rows = build()
    json.dump(rows, open(os.path.join(OUT, 'corrections_corpus.json'), 'w', encoding='utf-8'),
              indent=1, ensure_ascii=True)
    from collections import Counter
    gi = [r for r in rows if r['gate_independent']]
    cb = Counter(r['caught_by'] for r in rows)
    cls = Counter(r['error_class'] for r in rows)
    if hasattr(sys.stdout, 'buffer'):
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    print(f"corrections corpus: {len(rows)} labelled examples")
    print(f"  by caught_by: {dict(cb)}")
    print(f"  by error_class: {dict(cls)}")
    print(f"  GATE-INDEPENDENT (the labels that matter for a flag predictor): {len(gi)}")
    for r in gi[:8]:
        print(f"     - {r['app']} / {r['trial']} / {r['error_class']} / {r['caught_by']}")
    md = [
        '# Corrections corpus (the RLHF-analog labelled dataset)', '',
        f'**{len(rows)} labelled correction examples** (our-value -> corrected-value -> source).', '',
        '## By who/what caught it', ''] + [f'- {k}: {v}' for k, v in cb.most_common()] + [
        '', '## By error class', ''] + [f'- {k}: {v}' for k, v in cls.most_common()] + [
        '', '## The number that decides whether a flag predictor is trainable TODAY',
        f'- **Gate-independent labels (human read the source, no rule fired first): {len(gi)}.**',
        '- These are the ONLY labels that can show a learned flag catching a class the hand-written '
        'gates MISS. Every other label was produced by a gate/audit, so training on them and scoring '
        'flag-recall is CIRCULAR — the predictor can only relearn the rules it was trained from.',
        f'- With {len(gi)} gate-independent example(s), a flag predictor **cannot yet be trained for its '
        'stated purpose**. The in-app "Report a data issue" capture (built this session) is the funnel '
        'that produces gate-independent labels going forward. This is a **wait-for-data**, not a '
        '**train-now**, situation — and saying so is the honest result.',
    ]
    open(os.path.join(OUT, 'corrections_corpus.md'), 'w', encoding='utf-8').write('\n'.join(md))
    print(f"-> outputs/corrections_corpus.json + .md")


if __name__ == '__main__':
    main()
