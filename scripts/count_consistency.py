"""Shared count/effect consistency contract for RapidMeta.

Root-cause context (2026-07-12): the AACT results-table selector in
`bulk_clone_audit_first.py` populated tE/cE from arbitrary outcome rows,
independently of the separately-sourced effect estimate — it (a) included
param_type='NUMBER' rows (AACT stores *percentages* that way, so a 17.3%
responder rate became "17 events"), (b) flattened rows across *all* outcomes
instead of the primary, and (c) assigned treatment/comparator by sorting the
group ids, so placebo (usually the first group) was frequently labelled the
treatment. The net effect: for ~23% of checkable binary trials the displayed
arm counts implied the OPPOSITE direction to the plotted effect.

This module is the single source of truth for the invariant that closes the
class: **a trial's displayed arm counts must imply the same direction as its
displayed ratio effect, or the counts must not be shown.** It is imported by
the generator (fail-safe at build) and by the standalone ship-gate.
"""
from __future__ import annotations

# Neutral band: |RR-1| within this is "no direction" (matches the audit's
# 0.87/1.15 tolerance used to measure the 57/249 baseline).
_LO, _HI = 0.87, 1.15


def _num(x):
    try:
        f = float(x)
        return f if f == f else None  # drop NaN
    except (TypeError, ValueError):
        return None


def implied_rr(tE, tN, cE, cN):
    """Empirical risk ratio (tE/tN)/(cE/cN); None if not computable.

    A zero event cell is NOT a reason to give up on DIRECTION (that let a
    contradicting zero-cell trial slip the gate — cross-vendor objection
    2026-07-12). When exactly one arm has zero events we apply a Haldane-Anscombe
    0.5 continuity correction so the direction is still assessable; genuine
    double-zero (no events either arm) stays None (no direction)."""
    tE, tN, cE, cN = _num(tE), _num(tN), _num(cE), _num(cN)
    if None in (tE, tN, cE, cN):
        return None
    if tN <= 0 or cN <= 0:
        return None
    if tE > tN or cE > cN or tE < 0 or cE < 0:
        return None
    if tE == 0 and cE == 0:
        return None
    if tE == 0 or cE == 0:
        return ((tE + 0.5) / (tN + 1)) / ((cE + 0.5) / (cN + 1))
    return (tE / tN) / (cE / cN)


def side(x, lo=_LO, hi=_HI):
    """+1 (>1), -1 (<1), 0 (neutral band) — or None if x is None."""
    if x is None:
        return None
    if x > hi:
        return 1
    if x < lo:
        return -1
    return 0


def consistent(tE, tN, cE, cN, measure, effect):
    """Is the counts-implied direction compatible with the effect direction?

    Returns:
      True   — both sides defined and equal
      False  — both sides defined and OPPOSITE (the trust-breaking case)
      None   — undetermined (missing counts/effect, non-ratio measure, or either
               side lands in the neutral band); callers treat None as "cannot
               verify" — NOT as a pass.
    Only ratio measures (OR/RR/HR/IRR) are checkable; MD/LSMD/continuous return
    None.
    """
    if (measure or '').upper() not in ('OR', 'RR', 'HR', 'IRR'):
        return None
    eff = _num(effect)
    if eff is None or eff <= 0:
        return None
    rr = implied_rr(tE, tN, cE, cN)
    s_counts, s_eff = side(rr), side(eff)
    if s_counts is None or s_eff is None or s_counts == 0 or s_eff == 0:
        return None
    return s_counts == s_eff


def orient_to_effect(tE, tN, cE, cN, measure, effect):
    """Return (tE,tN,cE,cN, status) where counts are oriented so their implied
    direction matches the effect. status in {'ok','swapped','blank','asis'}.

    - If counts already consistent -> ('ok').
    - If swapping arms makes them consistent -> ('swapped') with arms swapped.
    - If neither orientation is consistent (or undetermined with a real effect
      that has a direction) -> ('blank') with all four set to None.
    - If the effect has no direction to check against -> ('asis') unchanged.
    """
    c = consistent(tE, tN, cE, cN, measure, effect)
    if c is True:
        return tE, tN, cE, cN, 'ok'
    if c is False:
        cS = consistent(cE, cN, tE, tN, measure, effect)
        if cS is True:
            return cE, cN, tE, tN, 'swapped'
        return None, None, None, None, 'blank'
    # c is None: if the effect itself has a direction but counts can't confirm,
    # do NOT show a possibly-wrong table — blank. If the effect is non-ratio /
    # directionless, leave as-is (nothing to contradict).
    if (measure or '').upper() in ('OR', 'RR', 'HR', 'IRR') and side(_num(effect)) in (1, -1):
        # counts missing or neutral: only blank when counts are actually present
        if implied_rr(tE, tN, cE, cN) is not None:
            return None, None, None, None, 'blank'
    return tE, tN, cE, cN, 'asis'
