"""Regression test for the Paule-Mandel tau^2 Newton-step SIGN BUG.

The bundle's plausibility gate caught a runaway tau^2 (~5.7e9) in the PM
sensitivity panel. Root cause: the Newton update solving Q(tau2)-(k-1)=0 was
written `tau2 + diff/slope` instead of `tau2 - diff/slope`. With slope = dQ/dtau2
< 0, the wrong sign (a) collapses tau2 to 0 under real heterogeneity and (b)
DIVERGES (runaway) in low-heterogeneity data.

This test:
  1. proves the FIXED sign reproduces the PM root (independent bisection ref),
  2. proves the OLD sign fails (so a re-introduction is caught),
  3. asserts NO shipped app still carries the buggy substring.

Pure-Python port of scripts/propagate_reml_retrofit.py::pauleMandelTau2 — kept in
lockstep with the injected JS. If you change the JS, change this.
"""
import glob
import os
import re

import pytest

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _Q(y, v, t2):
    w = [1.0 / (vi + t2) for vi in v]
    sw = sum(w)
    yb = sum(yi * wi for yi, wi in zip(y, w)) / sw
    return sum(wi * (yi - yb) ** 2 for yi, wi in zip(y, w))


def _slope(y, v, t2):
    w = [1.0 / (vi + t2) for vi in v]
    sw = sum(w)
    yb = sum(yi * wi for yi, wi in zip(y, w)) / sw
    return sum(-wi * wi * (yi - yb) ** 2 for yi, wi in zip(y, w))


def pm_tau2(y, v, sign):
    """Port of the injected Newton iteration. sign=-1 is the FIXED code."""
    if len(y) < 2:
        return 0.0
    t2 = 0.0
    target = len(y) - 1
    for _ in range(200):
        d = _Q(y, v, t2) - target
        if abs(d) < 1e-5:
            break
        s = _slope(y, v, t2)
        if not (abs(s) > 1e-14):
            break
        t2new = max(0.0, t2 + sign * d / s)
        if t2new > 1e6:            # runaway sentinel (the 5.7e9 failure)
            return float("inf")
        if abs(t2new - t2) < 1e-9:
            t2 = t2new
            break
        t2 = t2new
    return t2


def pm_tau2_reference(y, v):
    """Independent PM root by bisection on Q(tau2)=k-1 (no Newton)."""
    target = len(y) - 1
    if _Q(y, v, 0.0) <= target:
        return 0.0
    lo, hi = 0.0, 1e6
    for _ in range(300):
        mid = (lo + hi) / 2
        if _Q(y, v, mid) > target:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2


# (y=log-effect, v=variance) datasets
HETERO = ([-0.7, -0.3, 0.1, -1.2, -0.5], [0.05, 0.08, 0.06, 0.12, 0.04])
LOW_HET = ([-0.5, -0.48, -0.52, -0.49], [0.05, 0.05, 0.05, 0.05])
MODERATE = ([0.2, -0.4, 0.9, -0.1, 0.5, -0.7], [0.1, 0.15, 0.09, 0.2, 0.12, 0.08])


@pytest.mark.parametrize("y,v", [HETERO, LOW_HET, MODERATE])
def test_fixed_sign_matches_reference(y, v):
    ref = pm_tau2_reference(y, v)
    got = pm_tau2(y, v, sign=-1)
    assert got == pytest.approx(ref, abs=1e-3), f"PM tau2 {got} != reference {ref}"


def test_old_sign_is_broken():
    # Heterogeneous: old sign collapses to 0 (should be > 0.1)
    assert pm_tau2_reference(*HETERO) > 0.1
    assert pm_tau2(*HETERO, sign=+1) == 0.0
    # Low-het: old sign runs away to infinity (the 5.7e9 the harness caught)
    assert pm_tau2(*LOW_HET, sign=+1) == float("inf")
    # Fixed sign never runs away
    for y, v in (HETERO, LOW_HET, MODERATE):
        assert pm_tau2(y, v, sign=-1) < 1e6


def test_no_app_carries_the_buggy_substring():
    bad = [f for f in glob.glob(os.path.join(REPO, "*.html"))
           if "tau2 + diff / slope" in open(f, encoding="utf-8", errors="replace").read()]
    assert not bad, f"{len(bad)} app(s) still carry the buggy PM Newton step: {bad[:5]}"


def test_source_script_is_fixed():
    src = open(os.path.join(REPO, "scripts", "propagate_reml_retrofit.py"),
               encoding="utf-8").read()
    assert "tau2 - diff / slope" in src
    assert "tau2 + diff / slope" not in src
