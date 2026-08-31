r"""Tests for the absolute-effect arithmetic.

Every expected value here is hand-computable and written out in the test, so
a failure says which step is wrong rather than only that something moved.

These are REQUIREMENT assertions, not snapshots of what the code happened to
produce. Each one states why the value is the right one. A test that merely
pins current behaviour would defend a defect instead of catching it.
"""
from __future__ import annotations
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))), "scripts"))

from absolute_effects import (absolute_effect, risk_from_relative,
                              store_refusal, evaluate, _pairs_from_row,
                              _resolve_control)


# ------------------------------------------------------------ the conversion

def test_rr_applied_to_baseline_is_multiplication():
    # A risk ratio multiplies the baseline risk. Baseline 0.20, RR 0.50 ->
    # treated risk 0.10.
    assert risk_from_relative("RR", 0.5, 0.20) == pytest.approx(0.10)


def test_or_is_converted_through_the_odds_not_multiplied():
    # THE defect this guards: treating an odds ratio as if it were a risk
    # ratio. At baseline 0.20 the odds are 0.25; an OR of 0.5 gives treated
    # odds 0.125, so treated risk = 0.125/1.125 = 0.111111.
    # Multiplying instead would give 0.10 -- a different, wrong answer.
    got = risk_from_relative("OR", 0.5, 0.20)
    assert got == pytest.approx(0.1111111, rel=1e-6)
    assert got != pytest.approx(0.10, rel=1e-3)


def test_a_hazard_ratio_is_not_convertible_here():
    with pytest.raises(ValueError):
        risk_from_relative("HR", 0.8, 0.2)


# -------------------------------------------------------- risk difference/NNT

def test_risk_difference_and_nnt_are_plain_arithmetic():
    # baseline 0.20, RR 0.50 -> treated 0.10 -> ARD -0.10 -> NNT 10.
    out = absolute_effect("RR", 0.5, None, None, 0.20)
    assert out["treated_risk"] == pytest.approx(0.10)
    assert out["risk_difference"] == pytest.approx(-0.10)
    assert out["nnt"] == pytest.approx(10.0)
    assert out["direction"] == "FEWER_EVENTS"


def test_direction_is_arithmetic_not_clinical_valence():
    # An RR above 1 produces MORE events. Whether more events is good or bad
    # depends on whether the outcome is death or cure, which this module
    # does not decide. `cure_toc_me` in this store counts CURES.
    out = absolute_effect("RR", 1.25, None, None, 0.20)
    assert out["direction"] == "MORE_EVENTS"
    assert out["risk_difference"] == pytest.approx(0.05)
    assert out["nnt"] == pytest.approx(20.0)


def test_no_interval_is_manufactured_when_the_store_has_none():
    out = absolute_effect("RR", 0.5, None, None, 0.20)
    assert out["interval"] is None
    assert "risk_difference_ci_low" not in out
    assert "manufactured" in out["interval_absent_reason"]


# ---------------------------------------------------------- Altman intervals

def test_finite_nnt_interval_when_the_risk_difference_excludes_zero():
    # baseline 0.20, RR 0.5 (0.4 to 0.6):
    #   ARD      = 0.20*(0.5-1) = -0.10  -> NNT 10
    #   ARD low  = 0.20*(0.4-1) = -0.12  -> NNT 8.3333
    #   ARD high = 0.20*(0.6-1) = -0.08  -> NNT 12.5
    out = absolute_effect("RR", 0.5, 0.4, 0.6, 0.20)
    assert out["nnt_ci_kind"] == "FINITE"
    assert out["nnt_ci"]["low"] == pytest.approx(1 / 0.12, rel=1e-9)
    assert out["nnt_ci"]["high"] == pytest.approx(1 / 0.08, rel=1e-9)
    assert out["nnt_ci"]["low"] < out["nnt"] < out["nnt_ci"]["high"]


def test_nnt_interval_spanning_no_difference_is_not_a_finite_range():
    # THE defect this guards: when the risk-difference interval includes
    # zero, the NNT interval runs out to infinity (Altman BMJ 1998). Quoting
    # a tidy finite range there is a fabrication -- it asserts an upper bound
    # on the number needed to treat that the data do not support.
    # baseline 0.20, RR 0.9 (0.8 to 1.1):
    #   ARD low  = 0.20*(0.8-1) = -0.04
    #   ARD high = 0.20*(1.1-1) = +0.02   -> spans zero
    out = absolute_effect("RR", 0.9, 0.8, 1.1, 0.20)
    assert out["nnt_ci_kind"] == "SPANS_NO_DIFFERENCE"
    assert out["nnt_ci"]["to"] == "infinity"
    assert out["nnt_ci"]["nnt_fewer_events_bound"] == pytest.approx(25.0)
    assert out["nnt_ci"]["nnt_more_events_bound"] == pytest.approx(50.0)
    # and it must NOT present itself as an ordinary low/high pair
    assert "low" not in out["nnt_ci"] and "high" not in out["nnt_ci"]


def test_interval_bounds_are_ordered_even_if_the_inputs_are_not():
    a = absolute_effect("RR", 0.5, 0.4, 0.6, 0.20)
    b = absolute_effect("RR", 0.5, 0.6, 0.4, 0.20)
    assert a["risk_difference_ci_low"] == pytest.approx(
        b["risk_difference_ci_low"])


# ------------------------------------------------------ the store's refusal

def _entry(**kw):
    base = {"poolable": True, "pooled": {"measure": "RR", "point": 0.5,
                                         "ci_low": 0.4, "ci_high": 0.6}}
    base.update(kw)
    return base


def test_withdrawn_pool_is_refused_and_its_reason_is_carried_verbatim():
    e = _entry(pooled={"measure": "RR", "point": 0.5, "withdrawn": True,
                       "withdrawn_reason": "the arms are not comparable"})
    refused, reason = store_refusal(e)
    assert refused is True
    assert reason == "the arms are not comparable"


def test_poolable_false_is_refused():
    e = _entry(poolable=False, poolable_reason="three limbs differ at once")
    refused, reason = store_refusal(e)
    assert refused is True
    assert reason == "three limbs differ at once"


def test_a_refusal_without_a_written_reason_still_refuses():
    # The refusal must never be silently dropped just because the store
    # failed to record why. Losing the refusal is far worse than losing
    # the reason.
    refused, reason = store_refusal({"pooled": {"withdrawn": True}})
    assert refused is True
    assert "no reason recorded" in reason


def test_refusal_is_checked_before_the_measure_and_before_the_baseline():
    # A withdrawn pool that WOULD otherwise compute must still be refused.
    obj = {"outcomes": [{"id": "primary", "comparator": "placebo"}],
           "inputs": {"trials": [{"id": "T1", "by_outcome": {"primary": {
               "control": {"events": 40, "n": 200},
               "treatment": {"events": 20, "n": 200}}}}]}}
    entry = {"poolable": True, "k": 1,
             "pooled": {"measure": "RR", "point": 0.5, "ci_low": 0.4,
                        "ci_high": 0.6, "withdrawn": True,
                        "withdrawn_reason": "withdrawn on purpose"}}
    row = evaluate(os.path.join("ssot", "x", "x.json"), obj, "primary", entry)
    assert row["state"] == "REFUSED_BY_STORE"
    assert row["store_reason_verbatim"] == "withdrawn on purpose"
    assert "nnt" not in row and "baseline_value" not in row


# ----------------------------------------------------------- named-state exit

def test_missing_baseline_is_a_named_state_never_a_blank_or_a_zero():
    obj = {"outcomes": [{"id": "primary", "comparator": "placebo"}],
           "inputs": {"trials": []}}
    entry = {"poolable": True, "k": 2,
             "pooled": {"measure": "RR", "point": 0.5, "ci_low": 0.4,
                        "ci_high": 0.6}}
    row = evaluate(os.path.join("ssot", "x", "x.json"), obj, "primary", entry)
    assert row["state"] == "NNT_NOT_COMPUTABLE"
    assert row["reason"].startswith("NO_CONTROL_ARM_RISK")
    assert "baseline_value" not in row
    assert row.get("nnt", "absent") == "absent"


@pytest.mark.parametrize("measure", ["HR", "MD", "MEAN_DIFFERENCE",
                                     "RATE_RATIO", "IRR"])
def test_non_risk_measures_are_refused_with_a_named_reason(measure):
    obj = {"outcomes": [], "inputs": {"trials": [{"id": "T1", "by_outcome": {
        "primary": {"control": {"events": 40, "n": 200},
                    "treatment": {"events": 20, "n": 200}}}}]}}
    entry = {"poolable": True, "pooled": {"measure": measure, "point": 0.8}}
    row = evaluate(os.path.join("ssot", "x", "x.json"), obj, "primary", entry)
    assert row["state"] == "NNT_NOT_COMPUTABLE"
    assert "MEASURE_NOT_CONVERTIBLE:%s" % measure in row["reason"]


def test_a_baseline_of_zero_is_refused_not_divided_by():
    obj = {"outcomes": [], "inputs": {"trials": [{"id": "T1", "by_outcome": {
        "primary": {"control": {"events": 0, "n": 200},
                    "treatment": {"events": 0, "n": 200}}}}]}}
    entry = {"poolable": True, "pooled": {"measure": "RR", "point": 0.5}}
    row = evaluate(os.path.join("ssot", "x", "x.json"), obj, "primary", entry)
    assert row["state"] == "NNT_NOT_COMPUTABLE"
    assert row["reason"].startswith("BASELINE_DEGENERATE")


# --------------------------------------------------------- arm-role resolution

def test_drug_named_arm_keys_are_paired_structurally():
    # A fixed key list would miss these: the store names arms after drugs.
    pairs = _pairs_from_row({"events_apixaban": 60, "n_apixaban": 2211,
                             "events_comparator": 67, "n_comparator": 2283,
                             "point": 0.9247})
    assert pairs == {"apixaban": {"events": 60, "n": 2211},
                     "comparator": {"events": 67, "n": 2283}}


def test_control_arm_is_resolved_by_role_word():
    ctrl, why = _resolve_control({"apixaban", "comparator"}, "enoxaparin")
    assert ctrl == "comparator"
    assert "role word" in why


def test_control_arm_is_resolved_by_the_declared_comparator():
    ctrl, why = _resolve_control({"cabotegravir", "tdf_ftc"},
                                 "daily oral TDF/FTC")
    assert ctrl == "tdf_ftc"
    # the resolution must cite the comparator the object itself declared,
    # so the reader can audit why this arm was called the control
    assert "daily oral TDF/FTC" in why


def test_an_unresolvable_arm_pair_refuses_rather_than_guessing():
    # THE defect this guards: picking an arm by position. If the control
    # cannot be NAMED, guessing inverts the baseline and every number after
    # it, while still producing a plausible-looking NNT.
    ctrl, why = _resolve_control({"drug_a", "drug_b"}, "something else")
    assert ctrl is None
    assert "guessing inverts the baseline" in why


def test_three_arms_are_refused():
    ctrl, why = _resolve_control({"a", "b", "placebo"}, None)
    assert ctrl is None
    assert "exactly two arms" in why


# ------------------------------------------- the near-miss worth a test of its own

def test_registration_primary_counts_are_never_used_as_a_baseline():
    """A trial-level count block must not supply the baseline for an outcome.

    This is the most dangerous near-miss in this store, and the store itself
    documents why. On empagliflozin-hf-auto-full-review the block reads
    control_events 21.0 with control_n 1867 -- and its own
    `what_these_values_are` field says those are RATES PER 100 PATIENT-YEARS,
    not event counts, despite the field name ending in `_events`. The same
    block records that its arm labels were previously assigned BY REGISTRY
    POSITION and were wrong, repaired 2026-08-20.

    A reader that grabbed those two numbers would get a baseline of
    21.0/1867 = 0.0113: a plausible-looking risk, wrong in its units, wrong
    in its arm, and attached to the trial's REGISTERED PRIMARY rather than to
    the outcome being pooled. Nothing downstream would look odd.

    So the requirement is not "prefer outcome-linked counts". It is that a
    count block which is not keyed to this outcome is not a baseline at all.
    """
    obj = {
        "outcomes": [{"id": "primary", "comparator": "placebo"}],
        "inputs": {"trials": [{
            "id": "T1",
            # present, tempting, and NOT keyed to the outcome
            "registration_primary_counts": {
                "control_events": 21.0, "control_n": 1867.0,
                "treatment_events": 15.77, "treatment_n": 1863.0,
                "what_these_values_are": "RATES PER 100 PATIENT-YEARS",
            },
            # no by_outcome entry for `primary` at all
        }]},
    }
    entry = {"poolable": True, "k": 1,
             "pooled": {"measure": "RR", "point": 0.8, "ci_low": 0.7,
                        "ci_high": 0.9}}
    row = evaluate(os.path.join("ssot", "x", "x.json"), obj, "primary", entry)
    assert row["state"] == "NNT_NOT_COMPUTABLE"
    assert row["reason"].startswith("NO_CONTROL_ARM_RISK")
    assert "baseline_value" not in row
    # and specifically NOT the seductive wrong answer
    assert row.get("baseline_value") != pytest.approx(21.0 / 1867.0)


def test_arm_counts_are_only_read_from_the_outcome_being_pooled():
    """Counts filed under a DIFFERENT outcome must not leak into this one."""
    obj = {
        "outcomes": [{"id": "primary", "comparator": "placebo"}],
        "inputs": {"trials": [{"id": "T1", "by_outcome": {
            "some_other_endpoint": {"control": {"events": 40, "n": 200},
                                    "treatment": {"events": 20, "n": 200}}}}]},
    }
    entry = {"poolable": True, "k": 1,
             "pooled": {"measure": "RR", "point": 0.5, "ci_low": 0.4,
                        "ci_high": 0.6}}
    row = evaluate(os.path.join("ssot", "x", "x.json"), obj, "primary", entry)
    assert row["state"] == "NNT_NOT_COMPUTABLE"
    assert row["reason"].startswith("NO_CONTROL_ARM_RISK")
