"""Regression tests for three source-level defects found on SGLT2_HF_REVIEW.

Each assertion FAILED against the code as it stood before these fixes.

1. ssot/projectors_sof.py::_absolute_rows took `measure` and never read it, so
   a hazard ratio was multiplied by a baseline risk exactly as a risk ratio
   would be. A parameter that is accepted and ignored is worse than one that is
   absent, because the call site looks correct.

   THE COINCIDENCE THAT LET IT SURVIVE REVIEW: on the served page,
   200 x 0.7835 = 156.70 is Table 33's WRONG value, and 156.67 is Table 31's
   CORRECT value for HR 0.7636. A reviewer spot-checking one table against the
   other pool's ratio would have confirmed the page was fine. That is why this
   file carries a fixture and not an eyeball.

2. scripts/lane_rob/clinical_reading.py emitted "no other sexually transmitted
   infection outcome is recorded" on heart-failure pages. The `if` was gated on
   topic-relevant data; the `else` was gated on nothing, so it fired on every
   topic the claim was NOT written for -- and was invisible on the one topic it
   was tested against.

3. scripts/grade_assess_2026_08_19.py rated imprecision down on `k <= 3`.
   Cochrane ch.14 is explicit that the number of studies is not a reason for
   imprecision; optimal information size is.
"""
import os
import sys
import importlib.util

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _load(relpath, name):
    spec = importlib.util.spec_from_file_location(name, os.path.join(ROOT, relpath))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _surv(p0, ratio):
    return 1.0 - (1.0 - p0) ** ratio


# --------------------------------------------------------------------------
# 1. the effect measure must decide the ARITHMETIC, not only the caveat
# --------------------------------------------------------------------------
def test_hazard_ratio_is_not_multiplied_by_baseline():
    P = _load("ssot/projectors_sof.py", "projectors_sof")
    rows = dict((b, pt) for b, pt, lo, hi, d in
                P._absolute_rows("HR", 0.7636, 0.7062, 0.8258))
    # the named fixture from the finding
    assert rows[200] == 156.7, "HR 0.7636 at 200/1000: got %s, want 156.7" % rows[200]
    assert rows[200] != 152.7, "still multiplying HR by the baseline"
    for b, got in rows.items():
        want = round(_surv(b / 1000.0, 0.7636) * 1000, 1)
        assert abs(got - want) < 0.05, "baseline %s: got %s want %s" % (b, got, want)


def test_measure_is_not_inert():
    """RR, HR and OR of the same magnitude cannot give the same absolute risk."""
    P = _load("ssot/projectors_sof.py", "projectors_sof")
    rr = P._absolute_rows("RR", 0.7636, 0.7062, 0.8258)
    hr = P._absolute_rows("HR", 0.7636, 0.7062, 0.8258)
    orr = P._absolute_rows("OR", 0.7636, 0.7062, 0.8258)
    assert rr != hr, "`measure` is inert: RR and HR give identical tables"
    assert hr != orr, "`measure` is inert: HR and OR give identical tables"


def test_risk_ratio_still_multiplies():
    """The fix must not break the one measure multiplication IS correct for."""
    P = _load("ssot/projectors_sof.py", "projectors_sof")
    rows = dict((b, pt) for b, pt, lo, hi, d in
                P._absolute_rows("RR", 0.80, 0.70, 0.90))
    assert rows[200] == 160.0, "RR 0.80 at 200/1000 should be 160.0, got %s" % rows[200]


def test_hazard_caveat_does_not_justify_multiplication():
    """The old caveat said the multiplication 'assumes hazards are proportional'.

    Proportional hazards is what makes 1-(1-p)**HR correct; it never licensed
    the multiplication. A wrong justification for a wrong method is two defects.
    """
    src = open(os.path.join(ROOT, "ssot", "projectors_sof.py"),
               encoding="utf-8").read()
    assert "assumes the hazards are " not in src, \
        "the caveat still justifies multiplying an HR by a baseline risk"


# --------------------------------------------------------------------------
# 2. a topic-specific claim must be gated on BOTH branches
# --------------------------------------------------------------------------
def test_sti_claim_absent_from_non_infection_topics():
    C = _load("scripts/lane_rob/clinical_reading.py", "clinical_reading")
    hf = [{"outcome": "cardiovascular death or worsening heart failure"}]
    assert C._topic_is_infection_prevention(hf, []) is False
    assert C._topic_is_infection_prevention([], []) is False


def test_sti_claim_present_on_infection_topics():
    C = _load("scripts/lane_rob/clinical_reading.py", "clinical_reading")
    for outcome in ("HIV-1 seroconversion", "chlamydia incidence", "any STI diagnosis"):
        assert C._topic_is_infection_prevention([{"outcome": outcome}], []) is True, outcome


# --------------------------------------------------------------------------
# 3. imprecision is about information size, never about k
# --------------------------------------------------------------------------
def test_imprecision_does_not_rate_down_on_study_count():
    src = open(os.path.join(ROOT, "scripts", "grade_assess_2026_08_19.py"),
               encoding="utf-8").read()
    assert "elif k <= 3:" not in src, "imprecision still rated down on k alone"
    assert "Rated down for a small contributing set" not in src


def test_contributing_n_is_none_when_the_store_holds_no_rows():
    """An absent denominator must read as absent, not fall back to a total.

    Both Summary-of-Findings rows on SGLT2_HF printed 20,725 -- the topic total
    -- for pools of 14,462 and 11,007, because the two live pools have results
    but no `inputs.trials[*].by_outcome` rows.
    """
    G = _load("scripts/grade_assess_2026_08_19.py", "grade_assess")
    obj = {"inputs": {"trials": [
        {"by_outcome": {"a": {"analysed": {"treatment": 100, "control": 110}}}},
        {"by_outcome": {"a": {"analysed": {"treatment": 200, "control": 190}}}},
    ]}}
    assert G.contributing_n(obj, "a") == 600
    assert G.contributing_n(obj, "b") is None, \
        "an outcome with no per-trial rows must return None, not a fallback total"


if __name__ == "__main__":
    fails = []
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            try:
                fn()
                print("PASS %s" % name)
            except Exception as e:
                fails.append((name, e))
                print("FAIL %s -- %s" % (name, e))
    sys.exit(1 if fails else 0)
