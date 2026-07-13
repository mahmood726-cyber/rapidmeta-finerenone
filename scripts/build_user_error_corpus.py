#!/usr/bin/env python
"""Assemble the USER-CAUGHT ERROR CORPUS — a labelled dataset we already own.

The differentiator vs a dead competitor (Trialstreamer) is that our users became
auditors: they read the source, found our number wrong, and told us. Every such
report is a labelled example — "our extractor said X; a human who read the source
said Y" — in-domain, real, free, already collected. This script assembles what we
can EVIDENCE into one structured corpus for the extraction lanes and the fact store.

DISCIPLINE: it records provenance tier per row (attributed-user vs machine-surfaced-
by-a-user-report vs internal) and does NOT inflate. If the evidenced count is thin,
the corpus shows exactly that.

Schema per row:
  app, trial, field, our_value, corrected_value, source, caught_by, caught_date,
  error_class, tier, gate_flagged (did our gate catch it? — for flag-recall)

Output: outputs/user_error_corpus.json  (+ .md summary)
"""
from __future__ import annotations
import json, os, sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(REPO, 'outputs')

# --- Tier 1: ATTRIBUTED user reports (a human who read the source told us) ------
# The only error in the git history explicitly attributed to a user report.
ATTRIBUTED = [
    {
        'app': 'GLP1_CVOT_NMA_REVIEW.html', 'trial': 'LEADER (NCT01179048)',
        'field': 'binary event counts (tE/tN)',
        'our_value': '0/4668 (blank cells rendered as zero)',
        'corrected_value': '608/4668',
        'source': 'LEADER primary publication (NEJM 2016) — reader read it',
        'caught_by': 'user', 'caught_date': '2026-06-01',
        'error_class': 'blank/missing 2x2 count cells',
        'tier': 'attributed-user',
        'gate_flagged': False,   # validator skipped 0/0 silently — user caught what gate did not
    },
]

# --- Tier 2: MACHINE-SURFACED by the user report (the 1->128 cascade) ----------
# The single report triggered a portfolio scan that found the same defect class
# across the corpus. These are labelled "our value = blank; correct value needs
# source re-extraction" — a real work-list, seeded by a real user.
CASCADE_FILES = {
    'zero_count_blank.json': ('blank/zero 2x2 count cells (N>=30)', 'both tE and cE blank/zero while trial has real N'),
    'binary_blank_glp1style.json': ('real effect (HR) + blank binary counts', 'HR present but 2x2 cells blank'),
    'nohr_blank.json': ('no effect + blank counts (under-extraction)', 'neither effect nor counts extracted'),
}


def _load(name):
    try:
        return json.load(open(os.path.join(OUT, name), encoding='utf-8'))
    except Exception:
        return []


def build():
    rows = list(ATTRIBUTED)
    cascade_n = 0
    for fn, (cls, desc) in CASCADE_FILES.items():
        recs = _load(fn)
        cascade_n += len(recs)
        for r in recs:
            rows.append({
                'app': r.get('f', ''), 'trial': f"{r.get('name','')} ({r.get('nct','')})",
                'field': 'binary event counts (tE/cE)',
                'our_value': f"blank (tN={r.get('tN')}, cN={r.get('cN')}, hr={r.get('hr')})",
                'corrected_value': 'UNKNOWN — needs source re-extraction',
                'source': 'pending', 'caught_by': 'portfolio-scan (seeded by user report 2026-06-01)',
                'caught_date': '2026-06-01', 'error_class': cls, 'tier': 'machine-surfaced-by-user-report',
                'gate_flagged': False,
            })
    return rows, cascade_n


def main():
    rows, cascade_n = build()
    json.dump(rows, open(os.path.join(OUT, 'user_error_corpus.json'), 'w', encoding='utf-8'),
              indent=1, ensure_ascii=True)
    attributed = [r for r in rows if r['tier'] == 'attributed-user']
    # flag-recall: of attributed user-caught errors, how many did our gate flag?
    flagged = sum(1 for r in attributed if r['gate_flagged'])
    from collections import Counter
    cls = Counter(r['error_class'] for r in rows)
    md = [
        '# User-caught error corpus (RapidMeta)', '',
        'Assembled from every artifact we can evidence. **Counted, not assumed.**', '',
        f'- **Attributed user reports (a human read the source and told us): {len(attributed)}**',
        f'- **Machine-surfaced by that report (the 1→{cascade_n} cascade): {cascade_n}**',
        f'- **Total labelled rows: {len(rows)}**', '',
        '## Flag-recall on user-caught errors (the metric that decides the project)',
        f'- Of the {len(attributed)} attributed user-caught error(s), our gates had already flagged: '
        f'**{flagged}/{len(attributed)}**.',
        f'- **n={len(attributed)} is far too thin to be a real flag-recall number — say so.** The one '
        'evidenced case, our gate did NOT catch (it silently skipped blank 0/0 cells and used the HR). '
        'That is a **missing gate**, now added (see scripts/build_gate.py blank_counts_with_effect).', '',
        '## Error classes', ''] + [f'- {c}: {n}' for c, n in cls.most_common()] + [
        '', '## The honest headline',
        '"Tons of user-reported errors" is **NOT evidenced in artifacts** beyond ONE attributed report — '
        'because **zero apps have an error-reporting mechanism**, so reports arrived out-of-band '
        '(email/verbal to the owner) and were never captured. The ONE evidenced report DID demonstrate the '
        f'loop (it cascaded to {cascade_n} defects, 5 fixed immediately) — so the mechanism is real, but the '
        '**volume is unmeasured**. Fix: the in-app "Report an error" capture (scripts/add_error_report_button.py) '
        'so every future report becomes a counted, labelled corpus row.',
    ]
    open(os.path.join(OUT, 'user_error_corpus.md'), 'w', encoding='utf-8').write('\n'.join(md))
    if hasattr(sys.stdout, 'buffer'):
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    print(f"corpus: {len(rows)} rows ({len(attributed)} attributed-user, {cascade_n} machine-surfaced)")
    print(f"flag-recall on attributed user errors: {flagged}/{len(attributed)}")
    print(f"-> outputs/user_error_corpus.json + .md")


if __name__ == '__main__':
    main()
