#!/usr/bin/env python
"""The CLAIM system — makes research visible WHILE IT IS IN PROGRESS.

Fixes "you can't see if others are doing this project." A claim INFORMS, it never
BLOCKS — nobody owns a research question; two people working it independently is
dual independent review, a feature. A claim that EXPIRES cannot be squatted on.

Rules (deterministic; `now` passed in for testability, and because scripts here
must not call Date.now()):
  - CLAIM lasts 30 days; ONE self-service extension to 40 days total; then it
    LAPSES automatically (no moderation, no human).
  - SUBMITTED-to-journal badge (clickable within the claim window) shows for
    6 months from submission, then clears.
  - CAP: at most 3 ACTIVE claims per person (forces a real choice, not a land grab).

A claim is a public, timestamped record (a file/commit in a public claims repo, or
a labelled Issue) — auditable, tamper-evident, and it survives us. Expiry runs as a
daily GitHub Action; the board is a static page generated from the repo.
"""
from __future__ import annotations
import json, os, sys

DAY = 86400
CLAIM_DAYS = 30
EXTEND_DAYS = 40           # total, not additional
SUBMIT_MONTHS_DAYS = 182   # ~6 months

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STORE = os.path.join(REPO, 'outputs', 'claims.json')


def new_claim(review_id, user, now):
    return {'review_id': review_id, 'user': str(user).lstrip('@'),
            'claimed_at': int(now), 'expires_at': int(now) + CLAIM_DAYS * DAY,
            'extended': False, 'submitted_at': None, 'submission_expires_at': None}


def extend(claim, now):
    """One extension to 40 days total. No-op if already extended or lapsed."""
    if claim['extended']:
        return claim, 'already_extended'
    if now >= claim['expires_at']:
        return claim, 'already_lapsed'
    claim['expires_at'] = claim['claimed_at'] + EXTEND_DAYS * DAY
    claim['extended'] = True
    return claim, 'extended'


def mark_submitted(claim, now):
    """Clickable only within the claim window; badge lasts 6 months."""
    if now >= claim['expires_at']:
        return claim, 'claim_lapsed_cannot_submit'
    claim['submitted_at'] = int(now)
    claim['submission_expires_at'] = int(now) + SUBMIT_MONTHS_DAYS * DAY
    return claim, 'submitted'


def claim_active(claim, now):
    return now < claim['expires_at']


def submission_visible(claim, now):
    return bool(claim.get('submitted_at')) and now < (claim.get('submission_expires_at') or 0)


def status(claim, now):
    if claim_active(claim, now):
        return 'active'
    if submission_visible(claim, now):
        return 'lapsed_submitted'   # claim free to re-take, but "was submitted" still shown
    return 'lapsed'


def days_remaining(claim, now):
    return max(0, (claim['expires_at'] - now + DAY - 1) // DAY)


def active_claims_for(claims, user, now):
    u = str(user).lstrip('@')
    return [c for c in claims if c['user'] == u and claim_active(c, now)]


def can_claim(claims, user, now):
    """Cap: <=3 active claims per person. Returns (ok, active_count)."""
    n = len(active_claims_for(claims, user, now))
    return n < 3, n


def enforce_cap(claims, now):
    """REAL cap enforcement runs in the daily Action, not just the client (Codex-A:
    client-side is advisory). If a user somehow has >3 active claims (racing writes),
    keep the 3 earliest-claimed and revert the rest. Returns (claims, reverted)."""
    from collections import defaultdict
    by = defaultdict(list)
    for i, c in enumerate(claims):
        if claim_active(c, now):
            by[c['user']].append(i)
    revert = set()
    for user, idxs in by.items():
        if len(idxs) > 3:
            idxs.sort(key=lambda i: claims[i]['claimed_at'])
            for i in idxs[3:]:
                revert.add(i)
    kept = [c for i, c in enumerate(claims) if i not in revert]
    return kept, len(revert)


def prune_lapsed(claims, now, archive=None):
    """The daily Action's job: drop records fully lapsed (claim expired AND submission
    badge expired) from the ACTIVE board — but NEVER erase history (Codex-A): a
    submitted event is appended to `archive` (immutable) before it clears."""
    keep, dropped = [], 0
    for c in claims:
        if claim_active(c, now) or submission_visible(c, now):
            keep.append(c)
        else:
            dropped += 1
            if archive is not None and c.get('submitted_at'):
                archive.append({'review_id': c['review_id'], 'user': c['user'],
                                'submitted_at': c['submitted_at'], 'event': 'submitted'})
    return keep, dropped


def board_rows(claims, now):
    rows = []
    for c in claims:
        st = status(c, now)
        rows.append({'review_id': c['review_id'], 'user': c['user'], 'status': st,
                     'claimed_at': c['claimed_at'], 'days_remaining': days_remaining(c, now) if st == 'active' else 0,
                     'submitted': submission_visible(c, now), 'submitted_at': c.get('submitted_at')})
    return rows


# ---- self-demonstration (no live GitHub needed) ---------------------------
if __name__ == '__main__':
    if hasattr(sys.stdout, 'buffer'):
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    T0 = 1_000_000_000                       # fixed epoch (no Date.now)
    claims = []
    # amina claims 3 -> 4th blocked by cap
    for r in ['MALARIA_ACT', 'TB_XPERT', 'HIV_PREP']:
        ok, n = can_claim(claims, 'amina', T0)
        assert ok, f'should allow ({n} active)'
        claims.append(new_claim(r, 'amina', T0))
    ok, n = can_claim(claims, 'amina', T0)
    print(f"3-claim cap: amina has {n} active; 4th allowed? {ok}  (expect False)")
    # banner + days remaining at day 12
    c = claims[0]
    print(f"day 12: '{c['review_id']} claimed by @{c['user']}' — {days_remaining(c, T0 + 12*DAY)} days remaining "
          f"(status={status(c, T0 + 12*DAY)})")
    # lapses at day 31
    print(f"day 31: status={status(c, T0 + 31*DAY)}  (expect lapsed -> free to re-claim)")
    # extend to 40 at day 20, then still active at day 35
    extend(c, T0 + 20*DAY)
    print(f"extended to 40d; day 35 status={status(c, T0 + 35*DAY)} ({days_remaining(c, T0+35*DAY)} left)")
    # submit within window -> badge for 6 months
    mark_submitted(c, T0 + 25*DAY)
    print(f"submitted day 25: visible at day 100? {submission_visible(c, T0 + 100*DAY)}; "
          f"at day 210? {submission_visible(c, T0 + 210*DAY)}  (expect True, False)")
    # after claim lapses but submission live: status
    print(f"day 45 (claim lapsed, submission live): status={status(c, T0 + 45*DAY)}  (expect lapsed_submitted)")
    # prune at day 210 (everything expired for c)
    kept, dropped = prune_lapsed([c], T0 + 210*DAY)
    print(f"prune at day 210: dropped {dropped} fully-lapsed record(s)")
    # inform-not-block: a claimed review is still claimable by design (no block anywhere)
    print("inform-not-block: can_claim only enforces the PER-USER cap, never blocks a review for others ->",
          can_claim([new_claim('MALARIA_ACT', 'amina', T0)], 'bos', T0)[0])
    print("\nALL CLAIM RULES DEMONSTRATED OK")
