r"""The extraction path's two dangerous steps, tested against the real module.

The two steps that can be silently wrong are the ones tested here, because both produce a
plausible number rather than an error:

  1. RECONSTRUCTING A COUNT FROM A ROUNDED PERCENTAGE. Every bleeding row in the four
     apixaban prophylaxis trials is posted as an event rate. Rounding to the nearest
     candidate would look right and be unfalsifiable.

  2. PAIRING A NUMERATOR WITH A DENOMINATOR FROM A DIFFERENT POPULATION. In ADOPT the
     bleeding denominator is 3,184 As-Treated and the VTE denominator is 2,304 evaluable.
     A row that crosses them is wrong by 28% and reads perfectly.

⛔ NO MOCKS. The percentage cases are the REAL posted values from the four registrations.
"""
from __future__ import annotations

import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, "scripts"))
os.environ.setdefault("_GATE_WRAPPED", "1")

import harms_extract as HX                                                  # noqa: E402


def test_the_four_adopt_and_advance_counts_are_uniquely_determined():
    """The counts this lane publishes, each admitting exactly one integer."""
    cases = [("0.47", 3184, 15), ("0.19", 3217, 6),        # ADOPT major bleeding
             ("0.82", 2673, 22), ("0.68", 2659, 18),        # ADVANCE-3
             ("0.69", 1596, 11), ("1.39", 1588, 22),        # ADVANCE-1
             ("0.60", 1501, 9), ("0.93", 1508, 14)]         # ADVANCE-2
    for pct, n, want in cases:
        got = HX._counts_matching(pct, n)
        assert got == [want], (
            "%s%% of %d admits %s, not exactly [%d]. A count reconstructed from a "
            "rounded percentage is admissible ONLY when it is unique." % (pct, n, got, want))


def test_a_percentage_that_admits_more_than_one_count_is_refused():
    """The property that matters is the REFUSAL, not the successes above.

    1 decimal place on a large denominator is the ordinary case where reconstruction must
    fail: 0.5% of 3184 admits a whole range, and rounding to the nearest is how a
    fabricated count enters a table looking exactly like a read one.
    """
    candidates = HX._counts_matching("0.5", 3184)
    assert len(candidates) > 1, "expected an ambiguous case, got %s" % candidates
    # THROUGH THE REAL ROW BUILDER, not through a dict this test wrote itself. A test that
    # asserts on its own fixture verifies the fixture.
    study = {"resultsSection": {"outcomeMeasuresModule": {"outcomeMeasures": [{
        "title": "Incidence of Major Bleeding", "type": "PRIMARY",
        "unitOfMeasure": "Event Rate (%)", "timeFrame": "on treatment",
        "populationDescription": "As Treated",
        "groups": [{"id": "OG000", "title": "apixaban"}],
        "denoms": [{"counts": [{"groupId": "OG000", "value": "3184"}]}],
        "classes": [{"categories": [{"measurements": [
            {"groupId": "OG000", "value": "0.5"}]}]}]}]}}}
    rows, _states = HX.harm_rows("NCT00457002", study, [])
    assert len(rows) == 1
    assert rows[0]["events"] is None, (
        "an ambiguous percentage produced a count of %r. It must be refused, never "
        "rounded to the nearest candidate." % rows[0]["events"])
    assert "events_refused_because" in rows[0]
    assert str(candidates[0]) in rows[0]["events_refused_because"], (
        "the refusal must NAME the candidates it could not choose between; got %r"
        % rows[0]["events_refused_because"])


def test_precision_is_read_from_the_posted_string_not_assumed():
    """0.5 is one decimal place and 0.50 is two, and they admit different sets.

    Assuming two decimals everywhere would let "0.5" admit only the counts that round to
    0.50, which is a narrower and WRONG answer -- it would manufacture a unique count out
    of a value the registry never claimed that precisely.
    """
    one_dp = HX._counts_matching("0.5", 3184)
    two_dp = HX._counts_matching("0.50", 3184)
    assert len(one_dp) > len(two_dp), (
        "'0.5' (1 dp) must admit MORE candidates than '0.50' (2 dp); got %d and %d"
        % (len(one_dp), len(two_dp)))


def test_pair_arms_never_crosses_two_populations():
    """The ceftaroline rule, made mechanical: same endpoint, same window, SAME population
    or the rows do not meet."""
    rows = [
        {"nct": "NCT00457002", "endpoint_label": "Major bleeding", "arm": "apixaban",
         "events": 15, "denominator": 3184, "posted_value": "0.47", "posted_unit": "%",
         "ascertainment_window": "on treatment", "population": "As Treated"},
        {"nct": "NCT00457002", "endpoint_label": "Major bleeding", "arm": "enoxaparin",
         "events": 6, "denominator": 3217, "posted_value": "0.19", "posted_unit": "%",
         "ascertainment_window": "on treatment", "population": "As Treated"},
        # the trap: same trial, same endpoint name, same window -- DIFFERENT population
        {"nct": "NCT00457002", "endpoint_label": "Major bleeding", "arm": "apixaban",
         "events": 165, "denominator": 2304, "posted_value": "7.16", "posted_unit": "%",
         "ascertainment_window": "on treatment", "population": "evaluable ultrasound"},
    ]
    out = HX.pair_arms(rows, "Major bleeding")
    pops = {c["population"] for c in out}
    assert len(out) == 2 and pops == {"As Treated", "evaluable ultrasound"}, (
        "rows from two populations were merged into %d contrast(s) over %s" % (len(out), pops))
    as_treated = [c for c in out if c["population"] == "As Treated"][0]
    assert [(x["events"], x["n"]) for x in as_treated["arms"]] == [(15, 3184), (6, 3217)]


def test_a_topic_with_no_declared_hierarchy_says_so():
    """Silence must not read as 'the best source was used'."""
    assert HX.declared_source_hierarchy({}) == []
    declared = {"sources": {"X": {"layer_rank": 1, "layer": "Trial primary report"}}}
    assert HX.declared_source_hierarchy(declared) == [(1, "Trial primary report", "X")]


def test_an_unlabelled_multi_class_table_is_refused_not_read_positionally():
    """The right-number-wrong-endpoint guard.

    ClinicalTrials.gov returns the four-row bleeding table as classes[] and the labels
    live at classes[].title. A four-row table with NO titles must produce no rows at all
    rather than four rows whose endpoint was inferred from their order.
    """
    study = {"resultsSection": {"outcomeMeasuresModule": {"outcomeMeasures": [{
        "title": "Rate of Major Bleeding, CRNM, Major or CRNM, and Any Bleeding",
        "type": "SECONDARY", "unitOfMeasure": "Percentage",
        "timeFrame": "on treatment", "populationDescription": "treated",
        "groups": [{"id": "OG000", "title": "apixaban"},
                   {"id": "OG001", "title": "enoxaparin"}],
        "denoms": [{"counts": [{"groupId": "OG000", "value": "2673"},
                               {"groupId": "OG001", "value": "2659"}]}],
        "classes": [{"categories": [{"measurements": [
                        {"groupId": "OG000", "value": "0.82"},
                        {"groupId": "OG001", "value": "0.68"}]}]},
                    {"categories": [{"measurements": [
                        {"groupId": "OG000", "value": "11.71"},
                        {"groupId": "OG001", "value": "12.56"}]}]}]}]}}}
    rows, states = HX.harm_rows("NCT00423319", study, [])
    assert rows == [], "unlabelled classes were read positionally into %d row(s)" % len(rows)
    assert any(s.startswith("REFUSED_UNLABELLED_CLASS") for s in states), states


def test_a_labelled_table_is_read_and_keyed_by_arm_title():
    """The same table WITH labels must produce rows, keyed from the group TITLE."""
    study = {"resultsSection": {"outcomeMeasuresModule": {"outcomeMeasures": [{
        "title": "Rate of Major Bleeding and Any Bleeding", "type": "SECONDARY",
        "unitOfMeasure": "Percentage", "timeFrame": "on treatment",
        "populationDescription": "treated",
        "groups": [{"id": "OG000", "title": "apixaban"},
                   {"id": "OG001", "title": "enoxaparin"}],
        "denoms": [{"counts": [{"groupId": "OG000", "value": "2673"},
                               {"groupId": "OG001", "value": "2659"}]}],
        "classes": [{"title": "Major bleeding", "categories": [{"measurements": [
                        {"groupId": "OG000", "value": "0.82"},
                        {"groupId": "OG001", "value": "0.68"}]}]},
                    {"title": "Any bleeding", "categories": [{"measurements": [
                        {"groupId": "OG000", "value": "11.71"},
                        {"groupId": "OG001", "value": "12.56"}]}]}]}]}}}
    rows, _states = HX.harm_rows("NCT00423319", study, [])
    major = [r for r in rows if r["endpoint_label"] == "Major bleeding"]
    assert [(r["arm"], r["events"], r["denominator"]) for r in major] == [
        ("apixaban", 22, 2673), ("enoxaparin", 18, 2659)]
    assert all(r["ascertainment_window"] == "on treatment" for r in major)
    assert all(r["population"] == "treated" for r in major)


def test_no_posted_results_is_its_own_state():
    """A registration with no results is NOT 'no harms found'. CARAVAGGIO posts one
    outcome measure -- recurrent VTE -- and no bleeding outcome at all, and the
    difference between those two states decides whether a pool may be assembled."""
    rows, states = HX.harm_rows("NCT_EMPTY", {}, [])
    assert rows == [] and states == ["NO_POSTED_RESULTS"]
    rows2, states2 = HX.harm_rows("NCT03045406", {"resultsSection": {
        "outcomeMeasuresModule": {"outcomeMeasures": [
            {"title": "Recurrent Venous Thromboembolism", "type": "PRIMARY"}]}}}, [])
    assert rows2 == []
    assert states2 == ["RESULTS_POSTED_BUT_NO_HARM_OUTCOME_MATCHED"], states2
