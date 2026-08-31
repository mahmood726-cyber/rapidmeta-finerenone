r"""Tests for the sidecar absolute-effect sweep.

The first test is the one that matters: a KNOWN-ANSWER CONTROL against
metafor. Everything else in this module is arithmetic that could be talked
into looking right; that one cannot, because the answer was produced by a
different program in a different language.
"""
from __future__ import annotations
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))), "scripts"))

from absolute_effects_sidecar import (  # noqa: E402
    reml_tau2, reml_tau2_as_shipped, rd_and_variance, pool_rd, nnt_from_rd,
    adjudicate, candidate_topics,
)

# The four arni-hfref trials, pooled by metafor 5.0.1 under R 4.6.0 and
# stored in ssot/arni-hfref/arni-hfref.json at
# results.by_outcome.cvdeath_or_hfh_first.count_panels.rd
ARNI = [("paradigm-hf", 914, 4187, 1117, 4212),
        ("parachute-hf", 155, 462, 169, 460),
        ("parallel-hf", 30, 111, 28, 112),
        ("answer-hf", 12, 95, 8, 95)]
METAFOR_TAU2 = 0.0007252899298732
METAFOR_POINT = -0.02305292779417
METAFOR_Q = 5.071365427063
METAFOR_PER_TRIAL_RD = [-0.04689996010353, -0.03189346884999,
                        0.02027027027027, 0.04210526315789]


def _arni_rows():
    rows = []
    for name, tE, tN, cE, cN in ARNI:
        got = rd_and_variance(tE, tN, cE, cN)
        assert got is not None, name
        rows.append((name, got[0], got[1]))
    return rows


# ------------------------------------------------- the known-answer control

def test_per_trial_risk_differences_reproduce_metafor():
    got = [r[1] for r in _arni_rows()]
    for a, b in zip(got, METAFOR_PER_TRIAL_RD):
        assert a == pytest.approx(b, rel=1e-11)


def test_reml_tau2_reproduces_metafor():
    """THE CONTROL. If this fails, the estimator is wrong -- not the control.

    metafor returns 0.0007252899298732 on this input. Agreement here is the
    only evidence that our pooling is the same procedure R performed.
    """
    tau2 = reml_tau2([r[1] for r in _arni_rows()], [r[2] for r in _arni_rows()])
    assert tau2 == pytest.approx(METAFOR_TAU2, rel=1e-3)


def test_the_shipped_estimator_returns_zero_on_the_same_input():
    """Pins the defect, so nobody 'simplifies' back to the imported function.

    scripts/build_binary_sidecar.py::reml_tau2 uses an increment form and
    omits the 1/sum(w) term that separates REML from ML. On this input it
    returns exactly 0.0 where metafor returns 0.00072529 -- and it generated
    every binary sidecar in outputs/r_validation/.
    """
    shipped = reml_tau2_as_shipped([r[1] for r in _arni_rows()],
                                   [r[2] for r in _arni_rows()])
    assert shipped == 0.0
    assert reml_tau2([r[1] for r in _arni_rows()],
                     [r[2] for r in _arni_rows()]) > 0.0


def test_pooled_point_and_Q_reproduce_metafor():
    p = pool_rd(_arni_rows())
    assert p["Q"] == pytest.approx(METAFOR_Q, rel=1e-9)
    assert p["point"] == pytest.approx(METAFOR_POINT, rel=1e-3)


# ------------------------------------------------------------- the cells

def test_continuity_correction_only_when_a_cell_is_zero():
    # no zero cell -> untouched: 10/100 vs 20/100 is exactly -0.10
    rd, _v = rd_and_variance(10, 100, 20, 100)
    assert rd == pytest.approx(-0.10, rel=1e-12)
    # a zero cell -> corrected, so the estimate must NOT be the raw -0.20
    rd0, v0 = rd_and_variance(0, 100, 20, 100)
    assert rd0 != pytest.approx(-0.20, rel=1e-9)
    assert v0 > 0


def test_impossible_cells_are_refused_not_silently_coerced():
    assert rd_and_variance(101, 100, 5, 100) is None   # events exceed arm
    assert rd_and_variance(5, 0, 5, 100) is None       # empty arm
    assert rd_and_variance(-1, 100, 5, 100) is None    # negative
    assert rd_and_variance(5.5, 100, 5, 100) is None   # not an integer count


# -------------------------------------------------------------- the NNT

def test_nnt_interval_spanning_zero_is_not_a_finite_range():
    out = nnt_from_rd(-0.01, -0.04, 0.02)
    assert out["nnt_ci_kind"] == "SPANS_NO_DIFFERENCE"
    assert out["nnt_ci"]["to"] == "infinity"
    assert "low" not in out["nnt_ci"]


def test_finite_nnt_interval():
    out = nnt_from_rd(-0.10, -0.12, -0.08)
    assert out["nnt_ci_kind"] == "FINITE"
    assert out["nnt_magnitude"] == pytest.approx(10.0)
    assert out["nnt_ci"]["low"] == pytest.approx(1 / 0.12)
    assert out["nnt_ci"]["high"] == pytest.approx(1 / 0.08)


def test_direction_is_arithmetic_not_valence():
    assert nnt_from_rd(0.05, 0.01, 0.09)["direction"] == "MORE_EVENTS"
    assert nnt_from_rd(-0.05, -0.09, -0.01)["direction"] == "FEWER_EVENTS"


# ------------------------------------------ identity, not name, decides

def test_a_name_match_with_no_trial_overlap_is_not_an_adjudication():
    """THE defect this guards, observed live on two real sidecars.

    CEFTOLOZANE_INFECTION_AUTO_FULL and the store object of the same name
    share no NCT at all -- NCT02266706/NCT03217136 against
    NCT01345929/NCT01445665/NCT02070757. Binding a store ruling to a sidecar
    on the strength of a matching name would apply a judgement to evidence
    it was never made about.
    """
    store = {"widget-review": {"ncts": {"NCT00000001", "NCT00000002"},
                               "outcomes": {"primary": (True, "refused", None)}}}
    state, detail = adjudicate("WIDGET", {"NCT99999999"}, store)
    assert state == "NAME_MATCH_WITHOUT_TRIAL_OVERLAP"
    assert "NCT99999999" in detail["sidecar_ncts"]


def test_a_name_match_WITH_trial_overlap_does_adjudicate():
    store = {"widget-review": {"ncts": {"NCT00000001", "NCT00000002"},
                               "outcomes": {"primary": (True, "because", None)}}}
    state, detail = adjudicate("WIDGET", {"NCT00000001"}, store)
    assert state == "REFUSED_BY_STORE"
    assert detail["store_reason_verbatim"] == "because"


def test_absence_of_a_store_object_is_silence_not_permission():
    state, detail = adjudicate("NOTHING_LIKE_THIS", {"NCT00000001"}, {})
    assert state == "NO_STORE_ADJUDICATION"
    assert "Silence is not permission" in detail["note"]


def test_candidate_topics_covers_the_review_suffix():
    assert "ablation-af-review" in candidate_topics("ABLATION_AF")
