r"""The estimator is proven against an EXTERNAL ORACLE, not against itself.

Every expected value in tests/fixtures/metafor_oracle.json was produced by
metafor 5.0.1 under R 4.6.0 (scripts/metafor_oracle.R). None was typed by a
person. That matters: an earlier control tonight was hand-typed, two of its
four variances were about half their true values, and it sent a delegated
lane chasing a target that did not exist.

This is the test that fails if anyone reverts scripts/build_binary_sidecar.py
::reml_tau2 to the increment form that omitted the 1/sum(w) term.
"""
from __future__ import annotations
import json
import os
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))

from build_binary_sidecar import reml_tau2  # noqa: E402

FIXTURE = os.path.join(ROOT, "tests", "fixtures", "metafor_oracle.json")
# The 31 cases where our fixed-point iteration did NOT settle within its
# iteration cap. metafor uses Fisher scoring with step-halving and converges
# on all of them, so they are the cases most able to catch a solver that
# stops early -- which is exactly what happened: on the OMECAMTIV rows the
# plain fixed point returned 0.0030576 against metafor's 0.4893.
NONCONV_IN = os.path.join(ROOT, "tests", "fixtures",
                          "nonconverged_oracle_inputs.json")
NONCONV_OUT = os.path.join(ROOT, "tests", "fixtures",
                           "nonconverged_oracle_r_output.json")


def _oracle():
    with open(FIXTURE, encoding="utf-8") as fh:
        return json.load(fh)


def _nonconverged():
    """The hard cases, joined to metafor's answer for each."""
    if not (os.path.exists(NONCONV_IN) and os.path.exists(NONCONV_OUT)):
        return []
    with open(NONCONV_IN, encoding="utf-8") as fh:
        inputs = {i["id"]: i for i in json.load(fh)}
    out = []
    with open(NONCONV_OUT, encoding="utf-8") as fh:
        for r in json.load(fh):
            if r.get("ok") and r["id"] in inputs:
                i = inputs[r["id"]]
                out.append({"id": r["id"], "scale": "logOR", "yi": i["yi"],
                            "vi": i["vi"], "metafor_tau2": r["tau2"],
                            "metafor_version": "5.0.1"})
    return out


def test_the_oracle_fixture_exists_and_is_not_empty():
    """A fixture that silently went missing would turn every test below into
    a vacuous pass over an empty list."""
    o = _oracle()
    assert len(o) >= 15
    assert all(f.get("metafor_version") == "5.0.1" for f in o)


def test_the_oracle_spans_more_than_one_scale_and_more_than_one_dataset():
    """The defect was SCALE-SENSITIVE -- it returned exactly 0.0 on the
    risk-difference scale, where variances are ~1e-4. An oracle on one scale
    would not have caught it, and an oracle on one dataset would not either.
    """
    o = _oracle()
    assert {f["scale"] for f in o} >= {"rd", "rr", "or"}
    assert len({f["id"].split(":")[0] for f in o}) >= 2


def test_the_oracle_contains_genuine_zeros():
    """tau2 = 0 is a legitimate result, and the broken estimator returned it
    always. So the oracle must contain real zeros: an estimator is only
    proven if it returns zero WHEN IT SHOULD and non-zero when it should not.
    """
    o = _oracle()
    zeros = [f for f in o if f["metafor_tau2"] == 0.0]
    nonzeros = [f for f in o if f["metafor_tau2"] > 0.0]
    assert zeros, "no genuine zero in the oracle"
    assert nonzeros, "no non-zero in the oracle"


@pytest.mark.parametrize("item", _oracle(), ids=lambda f: f["id"])
def test_reml_tau2_reproduces_metafor(item):
    got = reml_tau2(item["yi"], item["vi"])
    want = item["metafor_tau2"]
    if want == 0.0:
        assert got == pytest.approx(0.0, abs=1e-12), (
            "metafor finds no heterogeneity here; the estimator must agree, "
            "not invent some")
    else:
        assert got == pytest.approx(want, rel=1e-4)


@pytest.mark.parametrize("item", _nonconverged(), ids=lambda f: f["id"])
def test_reml_tau2_reproduces_metafor_on_the_hard_cases(item):
    """The cases where a plain fixed point does not settle.

    These caught a real defect in the CORRECTED estimator: on the OMECAMTIV
    rows it returned 0.0030576 where metafor returns 0.4893, a factor of 160
    -- and it erred LOW, the same direction as the original bug and equally
    invisible. The bisection fallback exists because of these, so they are
    the tests that defend it.
    """
    got = reml_tau2(item["yi"], item["vi"])
    assert got == pytest.approx(item["metafor_tau2"], rel=1e-3)


def test_the_hard_case_fixture_is_present_and_covers_omecamtiv():
    """A fixture that silently vanished would make the test above vacuous."""
    hard = _nonconverged()
    assert len(hard) >= 25
    assert any("OMECAMTIV" in h["id"] for h in hard), (
        "the case that exposed the convergence defect must stay in the set")


def test_a_plain_fixed_point_would_fail_the_hard_cases():
    """Pins WHY the fallback is there, so removing it is a red test.

    Reimplements the iterate-only form and requires it to disagree with
    metafor on at least one hard case. If this ever passes, the fallback has
    become unnecessary and can be reconsidered -- but not before.
    """
    def iterate_only(ys, vs, max_iter=1000, tol=1e-16):
        t = 0.0
        for _ in range(max_iter):
            w = [1.0 / (v + t) for v in vs]
            sw = sum(w)
            mu = sum(a * y for a, y in zip(w, ys)) / sw
            den = sum(a ** 2 for a in w)
            num = sum((a ** 2) * ((y - mu) ** 2 - v)
                      for a, y, v in zip(w, ys, vs))
            nxt = max(0.0, num / den + 1.0 / sw)
            if abs(nxt - t) < tol:
                return nxt
            t = nxt
        return t

    hard = _nonconverged()
    if not hard:
        pytest.skip("hard-case fixture absent")
    disagreements = [h for h in hard
                     if abs(iterate_only(h["yi"], h["vi"]) - h["metafor_tau2"])
                     > 1e-3 * max(abs(h["metafor_tau2"]), 1e-12)]
    assert disagreements, (
        "the iterate-only form now agrees everywhere; the bisection fallback "
        "may no longer be load-bearing")


def test_the_old_increment_form_would_fail_this_suite():
    """Pins the defect itself, so a revert is caught as a failure rather than
    quietly restoring the old behaviour.

    Reimplemented here exactly as it stood, and asserted to DISAGREE with
    metafor on the risk-difference case -- where it returns 0.0 against
    metafor's 0.0007252899298732.
    """
    def old_form(yis, vis, max_iter=200, tol=1e-10):
        k = len(yis)
        if k < 2:
            return 0.0
        tau2 = 0.0
        for _ in range(max_iter):
            ws = [1.0 / (v + tau2) for v in vis]
            sw = sum(ws)
            mu = sum(w * y for w, y in zip(ws, yis)) / sw
            num = sum((w ** 2) * ((y - mu) ** 2 - v)
                      for w, y, v in zip(ws, yis, vis))
            den = sum(w ** 2 for w in ws)
            new = max(0.0, tau2 + num / den)
            if abs(new - tau2) < tol:
                return new
            tau2 = new
        return tau2

    rd = next(f for f in _oracle() if f["id"].endswith(":rd"))
    assert rd["metafor_tau2"] > 0.0
    assert old_form(rd["yi"], rd["vi"]) == 0.0
    assert reml_tau2(rd["yi"], rd["vi"]) == pytest.approx(
        rd["metafor_tau2"], rel=1e-4)
