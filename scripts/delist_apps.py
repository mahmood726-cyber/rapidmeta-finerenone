#!/usr/bin/env python
"""Reversibly de-list apps that are NOT meta-analyses (2026-07-12 mandate).

Two NON-NEGOTIABLE conditions:
  1. REVERSIBLE — `git mv` to delisted/ . NEVER a hard delete. Nothing destroyed.
  2. A PUBLIC MANIFEST — every de-listed app named, with its reason and trial IDs,
     committed and visible. Even the removal is auditable.

De-listed = not a meta-analysis at all (there is nothing to check):
  delist:k1            single contributing trial (a forest plot around one trial)
  delist:no-source     no trial data at all
  delist:non-poolable  trials present but no poolable estimate can be produced

This is NOT concealment: presenting a k=1 app as a meta-analysis is itself the
misrepresentation. Apps with a wrong/unverified NUMBER are NOT de-listed — they
stay up, flagged (see inject_verification_banner.py).

Usage: python scripts/delist_apps.py [--apply]
"""
from __future__ import annotations
import sys, io, os, re, json, subprocess, glob

ROOT = os.environ.get('RAPIDMETA_REPO_ROOT',
                      os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DELISTED = os.path.join(ROOT, 'delisted')


def _git(*args):
    return subprocess.run(['git', *args], cwd=ROOT, capture_output=True, text=True)


def _stub_for(full_name):
    """A *_AUTO_FULL_REVIEW.html app usually has a *_AUTO_REVIEW.html redirect
    stub; move it too so no dangling redirect remains."""
    if full_name.endswith('_AUTO_FULL_REVIEW.html'):
        return full_name.replace('_AUTO_FULL_REVIEW.html', '_AUTO_REVIEW.html')
    return None


def main(argv):
    apply = '--apply' in argv
    recs = json.load(open(os.path.join(ROOT, 'outputs', 'corpus_classification.json'), encoding='utf-8'))
    delist = [r for r in recs if r['status'].startswith('delist')]
    os.makedirs(DELISTED, exist_ok=True)

    moved, manifest = [], []
    for r in delist:
        files = [r['app']]
        stub = _stub_for(r['app'])
        if stub and os.path.exists(os.path.join(ROOT, stub)):
            files.append(stub)
        for f in files:
            src = os.path.join(ROOT, f)
            if not os.path.exists(src):
                continue
            if apply:
                res = _git('mv', f, f'delisted/{f}')
                if res.returncode != 0:   # fall back to plain mv if not tracked
                    os.replace(src, os.path.join(DELISTED, f))
            moved.append(f)
        manifest.append({'app': r['app'], 'reason': r['status'],
                         'reason_detail': '; '.join(r.get('reasons', [])),
                         'k': r['k'], 'contributing_trials': r.get('contributing', []),
                         'all_trial_ids': None})

    # index.html: drop any links to de-listed apps so they are not surfaced
    idx = os.path.join(ROOT, 'index.html')
    idx_removed = 0
    if apply and os.path.exists(idx):
        html = open(idx, encoding='utf-8', errors='replace').read()
        names = set(m['app'] for m in manifest) | set(_stub_for(m['app']) or '' for m in manifest)
        for nm in names:
            if not nm:
                continue
            html, n = re.subn(r'<a\b[^>]*href="[^"]*' + re.escape(nm) + r'"[^>]*>.*?</a>', '', html, flags=re.S)
            idx_removed += n
        open(idx, 'w', encoding='utf-8').write(html)

    # public manifest (json + markdown)
    from collections import Counter
    by_reason = Counter(m['reason'] for m in manifest)
    json.dump(manifest, open(os.path.join(ROOT, 'outputs', 'DELISTED_MANIFEST.json'), 'w'), indent=1)
    md = ['# RapidMeta de-listing manifest (2026-07-12)',
          '',
          'These apps were **reversibly** moved to `delisted/` (via `git mv` — nothing deleted) '
          'because they are **not meta-analyses**: there is nothing for a reader to check. '
          'Presenting a single-trial or no-data app as a synthesis is itself a misrepresentation. '
          'Any entry can be restored with `git mv delisted/<file> <file>`.',
          '',
          f'**De-listed: {len(manifest)} apps** — ' +
          ', '.join(f'{k}={v}' for k, v in by_reason.most_common()),
          '',
          '| App | Reason | k | Contributing trials |',
          '|---|---|--:|---|']
    for m in sorted(manifest, key=lambda x: (x['reason'], x['app'])):
        trials = ', '.join(m['contributing_trials']) or '—'
        md.append(f"| {m['app']} | {m['reason']} ({m['reason_detail'][:60]}) | {m['k']} | {trials} |")
    open(os.path.join(ROOT, 'delisted', 'DELISTED_MANIFEST.md'), 'w', encoding='utf-8').write('\n'.join(md))

    if hasattr(sys.stdout, 'buffer') and getattr(sys.stdout, 'encoding', '').lower() != 'utf-8':
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    print(f"{'APPLIED' if apply else 'DRY-RUN'}: de-list {len(manifest)} apps "
          f"({dict(by_reason)}); files moved={len(moved)}; index links removed={idx_removed}")
    print("manifest -> outputs/DELISTED_MANIFEST.json + delisted/DELISTED_MANIFEST.md")
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))
