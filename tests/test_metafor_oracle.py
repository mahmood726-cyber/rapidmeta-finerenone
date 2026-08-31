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


def _oracle():
    with open(FIXTURE, encoding="utf-8") as fh:
        return json.load(fh)


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
