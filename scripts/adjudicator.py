#!/usr/bin/env python
"""Auto-adjudicator — the user's report TRIGGERS verification; it never BYPASSES it.

A user disputes a number with ONE TAP (+ an optional one-tap reason class). This
engine adjudicates the claim against the SOURCE, deterministically and offline:
  - the registry's posted value (AACT),
  - the arithmetic gate (effect<->cells, events<=N),
  - the identity gate (arm count, N vs enrolment, wrong-NCT).
Three honest outcomes (never auto-accept an unverified claim):
  USER_RIGHT_FIX          source agrees with the user -> fix + PROPAGATE to every
                          app containing that trial (the O(trials) advantage).
  SOURCE_CONTRADICTS_KEEP source backs OUR value -> keep, explain WITH the locator,
                          stay flagged for a human (the user may still be right and
                          the source wrong).
  CANNOT_SETTLE_FLAG      source cannot settle it -> stays flagged, queued.
A disputed number is FAIL-CLOSED: never used in a pooled estimate until resolved.

Reason class routes the adjudicator (Mahmood's one-tap list):
  wrong_number -> arithmetic + registry posted value
  wrong_trial / wrong_arm / trial_shouldnt_be_here -> identity gate
  wrong_outcome_timepoint -> registered outcome/timepoint
  something_else -> human queue (no auto-verdict)
"""
from __future__ import annotations
import json, math, os, sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, 'scripts'))
import count_consistency as cc  # noqa


def _load(n, d):
    p = os.path.join(REPO, 'outputs', n)
    return json.load(open(p, encoding='utf-8')) if os.path.exists(p) else d


AACT = _load('aact_cache.json', {})
IDENT = _load('identity_findings.json', [])
NCT2APPS = _load('nct_to_apps.json', {})
CONFIRMED = {(x['app'], x['nct']) for x in _load('registry_confirmed_trials.json', [])}
_IDENT_BY = {}
for _x in IDENT:
    _IDENT_BY.setdefault((_x['app'], _x['nct']), []).append(_x)


def adjudicate(dispute):
    """dispute: {app, nct, field, our_value, proposed_value?, reason_class}.
    Returns a verdict dict — deterministic, offline, source-cited."""
    app, nct = dispute.get('app'), dispute.get('nct')
    rc = dispute.get('reason_class', 'something_else')
    reg = AACT.get(nct, {})
    out = {'dispute': dispute, 'nct': nct, 'checked': [], 'locator': None}

    # identity-class reasons -> identity gate
    if rc in ('wrong_trial', 'wrong_arm', 'trial_shouldnt_be_here'):
        finds = _IDENT_BY.get((app, nct), [])
        out['checked'].append('identity_gate(AACT design_groups/enrollment)')
        if finds:
            f = finds[0]
            out['verdict'] = 'USER_RIGHT_FIX'
            out['reason'] = (f"Registry confirms an identity problem: {f['check']} — "
                             f"{f['shown']} vs registry {f['registry']}.")
            out['locator'] = f"AACT design_groups/{nct}"
            out['subclass'] = f.get('subclass')
            return _with_propagation(out, nct)
        if reg.get('in_registry'):
            out['verdict'] = 'SOURCE_CONTRADICTS_KEEP'
            out['reason'] = (f"Registry ({nct}) shows arms={reg.get('arms')}, "
                             f"enrolment={reg.get('enrollment')} consistent with what we display. "
                             "Kept — but if you have a source we don't, it stays flagged for a human.")
            out['locator'] = f"clinicaltrials.gov/study/{nct}"
            return out
        out['verdict'] = 'CANNOT_SETTLE_FLAG'
        out['reason'] = f"{nct} is not in the registry snapshot — cannot settle from source. Flagged."
        return out

    # wrong_number -> arithmetic + registry posted value
    if rc == 'wrong_number':
        out['checked'].append('arithmetic_gate + registry outcome_measurements')
        ov, pv = dispute.get('our_value'), dispute.get('proposed_value')
        # arithmetic self-consistency on any counts the dispute carries
        tE, tN, cE, cN, eff = (dispute.get(k) for k in ('tE', 'tN', 'cE', 'cN', 'effect'))
        if None not in (tE, tN, cE, cN, eff):
            consistent = cc.consistent(tE, tN, cE, cN, dispute.get('measure', 'OR'), eff)
            if consistent is False:
                out['verdict'] = 'USER_RIGHT_FIX'
                out['reason'] = ("Arithmetic gate: the displayed counts imply the OPPOSITE direction "
                                 "to the displayed effect — internally inconsistent. The number is wrong.")
                out['locator'] = 'arithmetic (count<->effect)'
                return _with_propagation(out, nct)
        # registry posted-value confirmation (only where we already confirmed it)
        if (app, nct) in CONFIRMED:
            out['verdict'] = 'SOURCE_CONTRADICTS_KEEP'
            out['reason'] = ("The event counts we show were CONFIRMED against the sponsor's posted "
                             "registry results (both arms match a posted outcome). Kept; here is the "
                             "registry so you can check.")
            out['locator'] = f"clinicaltrials.gov/study/{nct}/results"
            return out
        out['verdict'] = 'CANNOT_SETTLE_FLAG'
        out['reason'] = ("The registry does not post a value we can match to this exact outcome/timepoint "
                         "(no stored outcome key), so the source cannot settle it automatically. Flagged for a human.")
        out['locator'] = f"clinicaltrials.gov/study/{nct}/results"
        return out

    if rc == 'wrong_outcome_timepoint':
        out['checked'].append('registered outcome + timepoint (AACT outcomes.time_frame)')
        out['verdict'] = 'CANNOT_SETTLE_FLAG'
        out['reason'] = ("Which outcome/timepoint this pool used is not stored in the app, so it cannot be "
                         "matched to the registry automatically. Flagged for a human — this is exactly the "
                         "class our timepoint rule surfaces.")
        out['locator'] = f"clinicaltrials.gov/study/{nct}"
        return out

    # something_else / unknown -> human queue, no auto-verdict
    out['verdict'] = 'CANNOT_SETTLE_FLAG'
    out['reason'] = "Free-text / unclassified report — queued for a human. Still flagged, never dismissed."
    return out


def _with_propagation(out, nct):
    apps = NCT2APPS.get(nct, [])
    out['propagation'] = {'nct': nct, 'apps': apps, 'count': len(apps)}
    out['note'] = (f"An accepted fix for {nct} propagates to all {len(apps)} app(s) containing this trial "
                   f"(the O(trials) advantage — fix once, fixed everywhere).")
    return out


if __name__ == '__main__':
    if hasattr(sys.stdout, 'buffer'):
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    # three real test cases end-to-end
    tests = [
        {'app': 'BEMPEDOIC_ACID_REVIEW.html', 'nct': 'NCT02973841', 'field': 'trial',
         'reason_class': 'wrong_trial', 'our_value': 'bempedoic acid trial'},
        {'app': 'CANAKINUMAB_SJIA_AUTO_FULL_REVIEW.html', 'nct': 'NCT00891046', 'field': 'arm',
         'reason_class': 'wrong_arm', 'our_value': 'comparator cN=63'},
        {'app': 'DEMO', 'nct': 'NCT03504397', 'field': 'counts', 'reason_class': 'wrong_number',
         'tE': 100, 'tN': 200, 'cE': 5, 'cN': 200, 'effect': 0.734, 'measure': 'OR'},
        {'app': 'GLP1_CVOT_NMA_REVIEW.html', 'nct': 'NCT01179048', 'field': 'counts',
         'reason_class': 'wrong_number', 'our_value': '608/4668'},
    ]
    for t in tests:
        v = adjudicate(t)
        print(f"\n=== DISPUTE: {t['app']} / {t['nct']} / reason={t['reason_class']} ===")
        print(f"  VERDICT: {v['verdict']}")
        print(f"  why: {v['reason'][:150]}")
        print(f"  source: {v.get('locator')}")
        if v.get('propagation'):
            print(f"  PROPAGATE: fix reaches {v['propagation']['count']} app(s)")
