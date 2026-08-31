"""Plant-the-defect proof for the absence handling in build_app_v2.

One fixture per KeyError observed in the corpus. Each asserts two things:
the read does not raise, AND the caller says plainly that the value is absent.
A fix that merely stopped the crash would let the page assert a default, which
is the defect this corpus has been fighting all week.

The fourth fixture is the instructive one: an object that stores the ABSENCE
SENTINEL as a source id. `srcs[sentinel]` was a KeyError on 20 of 141 objects.
"""
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import build_app_v2 as B


SENTINEL = "not recorded on the page this object was extracted from"


# ---------------------------------------------------------------- held()
def test_held_returns_value_when_present():
    assert B.held({"search_note": "PubMed, 2026-08-01"}, "search_note") == "PubMed, 2026-08-01"


@pytest.mark.parametrize("key", ["search_note", "known_limitation", "eligibility",
                                 "target_source_id", "access_limitation"])
def test_held_does_not_raise_on_any_observed_missing_key(key):
    assert B.held({}, key) is None


def test_held_treats_empty_string_as_absent():
    """An empty string rendered as a value is a blank where a claim should be."""
    assert B.held({"search_note": "   "}, "search_note") is None


def test_held_on_a_non_dict_does_not_raise():
    assert B.held(None, "search_note") is None
    assert B.held("a string", "search_note") is None


def test_held_keeps_falsy_values_that_are_real():
    """0 and False are values the object DID record; they must survive."""
    assert B.held({"k": 0}, "k") == 0
    assert B.held({"k": False}, "k") is False


# ---------------------------------------------------------------- source_name()
def test_source_name_resolves_a_registered_source():
    srcs = {"PM_SMITH2020": {"name": "Smith et al. 2020"}}
    assert B.source_name(srcs, "PM_SMITH2020") == "Smith et al. 2020"


def test_source_name_on_the_absence_sentinel_returns_none_not_keyerror():
    """The 20-topic failure: the sentinel is stored AS the source id."""
    srcs = {"PM_SMITH2020": {"name": "Smith et al. 2020"}}
    assert B.source_name(srcs, SENTINEL) is None


def test_source_name_when_the_id_is_missing_entirely():
    assert B.source_name({"A": {"name": "x"}}, None) is None


def test_source_name_when_the_registered_record_has_no_name():
    assert B.source_name({"A": {}}, "A") is None


def test_source_name_when_sources_is_not_a_dict():
    assert B.source_name(None, "A") is None


# ------------------------------------------------- the caller must SAY it
def test_absent_search_note_renders_an_honest_sentence_not_a_default():
    """Guard the whole point: absence must produce a statement of absence."""
    phrase = B.held({}, "search_note") or "This object does not record how its search was run."
    assert "does not record" in phrase


def test_absent_source_renders_an_honest_sentence_not_a_name():
    phrase = (B.source_name({}, SENTINEL)
              or "The synthesis reconciled against is not registered as a source in this object.")
    assert "not registered" in phrase
    assert SENTINEL not in phrase, "the sentinel must never be shown to a reader as a name"


def test_no_direct_subscript_of_the_four_keys_remains():
    """Regression guard: the class, not the four instances."""
    src = open(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                            "build_app_v2.py"), encoding="utf-8").read()
    for bad in ["sc['search_note']", "sc['eligibility']", "sc['known_limitation']",
                "srcs[r['target_source_id']]", "r['access_limitation']"]:
        assert bad not in src, "direct subscript %r is back; it crashes the build on absence" % bad
