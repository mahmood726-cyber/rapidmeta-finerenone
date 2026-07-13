#!/usr/bin/env python
"""Protocol pre-registration by git commit (STAGED — not deployed).

Turns the discipline registries impose on trialists onto the REVIEWER: a
RapidMeta review's protocol (PICO, eligibility, pre-specified primary outcome,
planned analysis, search strategy) is content-hashed and COMMITTED to git
**before the search and extraction run**, so outcome-switching and post-hoc PICO
drift become tamper-evident and diffable (see protocol_diff.py).

Prior art (credited, not overclaimed): git-commit + external-timestamp
pre-registration is established (git-timestamp; OSF/Zenodo trusted timestamps);
PROSPERO registers MA protocols but >20% drift and it is not machine-diffable.
What is fresh here is (a) the lock is committed *before* search in the same repo
that builds the app and (b) the app surfaces a machine-computed
protocol-as-registered vs analysis-as-run diff. NOTE: a raw git timestamp is
self-asserted; for a defensible audit trail, additionally anchor the lock commit
to an external trusted timestamp (Zenodo DOI / OpenTimestamps) — recorded in the
lock's `external_anchor` field.

Usage:
  python scripts/preregister_protocol.py protocol/<REVIEW>.json           # lock it
  python scripts/preregister_protocol.py protocol/<REVIEW>.json --check    # verify lock still matches
"""
from __future__ import annotations
import sys, io, os, json, hashlib, subprocess, datetime

REQUIRED = ['review_id', 'pico', 'primary_outcome', 'planned_analysis', 'search']
PICO_REQ = ['population', 'intervention', 'comparator', 'outcomes']


def _sha256_canonical(doc):
    """Hash the protocol content (excluding the lock-injected fields) so the
    hash is stable regardless of registration metadata."""
    body = {k: v for k, v in doc.items() if k not in ('_lock',)}
    canon = json.dumps(body, sort_keys=True, ensure_ascii=False, separators=(',', ':'))
    return hashlib.sha256(canon.encode('utf-8')).hexdigest()


def validate(doc):
    errs = []
    for k in REQUIRED:
        if k not in doc or doc[k] in (None, '', [], {}):
            errs.append(f'missing required field: {k}')
    if isinstance(doc.get('pico'), dict):
        for k in PICO_REQ:
            if not doc['pico'].get(k):
                errs.append(f'pico.{k} missing')
    pa = doc.get('planned_analysis') or {}
    for k in ('model', 'effect_measure'):
        if not pa.get(k):
            errs.append(f'planned_analysis.{k} missing')
    return errs


def _git(*args):
    try:
        return subprocess.run(['git', *args], cwd=os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                              capture_output=True, text=True).stdout.strip()
    except Exception:
        return ''


def lock(path, now_utc=None):
    doc = json.load(open(path, encoding='utf-8'))
    errs = validate(doc)
    if errs:
        return {'ok': False, 'errors': errs}
    sha = _sha256_canonical(doc)
    # Is the CURRENT protocol content actually committed at HEAD? `git ls-files`
    # only proves the path is tracked — a tracked file can be edited after the
    # results and still look "committed". So we compare the working-copy content
    # hash to the HEAD blob's content hash (Codex objection 2026-07-12).
    committed = False
    top = _git('rev-parse', '--show-toplevel')
    rel = None
    try:
        rel = os.path.relpath(path, top) if top else path
        if rel.startswith('..'):
            rel = None
    except ValueError:
        rel = None
    if rel:
        rel_posix = rel.replace(os.sep, '/')
        head_content = _git('show', f'HEAD:{rel_posix}')
        if head_content:
            try:
                head_doc = json.loads(head_content)
                committed = (_sha256_canonical(head_doc) == sha)
            except Exception:
                committed = False
    head = _git('rev-parse', 'HEAD') or 'UNCOMMITTED'
    now = now_utc or datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
    lockdoc = {
        'review_id': doc['review_id'],
        'protocol_file': os.path.basename(path),
        'protocol_sha256': sha,
        'git_commit_at_lock': head,
        'locked_utc': now,
        'committed_before_search': committed,   # current content IS at HEAD, not merely tracked
        'external_anchor': None,   # fill with Zenodo DOI / OpenTimestamps proof
        'note': ('Commit protocol/<REVIEW>.json to git BEFORE running the search. '
                 'The commit hash + timestamp is the registration; anchor it '
                 'externally (Zenodo/OpenTimestamps) for a neutral timestamp.'),
    }
    lockpath = os.path.join(os.path.dirname(path), doc['review_id'] + '.LOCK.json')
    json.dump(lockdoc, open(lockpath, 'w', encoding='utf-8'), indent=2, ensure_ascii=False)
    return {'ok': True, 'lock': lockdoc, 'lockpath': lockpath}


def check(path):
    doc = json.load(open(path, encoding='utf-8'))
    lockpath = os.path.join(os.path.dirname(path), doc['review_id'] + '.LOCK.json')
    if not os.path.exists(lockpath):
        return {'ok': False, 'reason': 'no LOCK file — protocol was never registered'}
    lockdoc = json.load(open(lockpath, encoding='utf-8'))
    cur = _sha256_canonical(doc)
    if cur != lockdoc['protocol_sha256']:
        return {'ok': False, 'reason': 'protocol CHANGED since registration',
                'registered_sha': lockdoc['protocol_sha256'], 'current_sha': cur}
    return {'ok': True, 'lock': lockdoc}


def main(argv):
    if len(argv) < 2:
        print(__doc__); return 2
    path = argv[1]
    if '--check' in argv:
        r = check(path)
    else:
        r = lock(path)
    print(json.dumps(r, indent=2, ensure_ascii=False))
    return 0 if r.get('ok') else 1


if __name__ == '__main__':
    if hasattr(sys.stdout, 'buffer') and getattr(sys.stdout, 'encoding', '').lower() != 'utf-8':
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.exit(main(sys.argv))
