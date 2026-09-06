"""A screening gate must be able to say "I could not tell", and must not say it too often.

WHY THIS FILE EXISTS. `audit_nct` recorded six gates as booleans, so False meant BOTH "the
evidence disagrees" and "the evidence was never there". The second is not a failure of the
trial, it is a failure to look, and counting it as the first turns an unposted baseline table
or an unreachable PubMed into evidence about a trial.

THE TESTS ARE PAIRED THROUGHOUT, because this defect is symmetric and a one-sided suite
would certify the opposite error. For each gate: the same candidate is asserted EXCLUDED
when the evidence is present and disagrees, and UNDECIDABLE when the evidence is absent.
A classifier that answered UNDECIDABLE to everything would pass the second half of every
pair and fail the first, and vice versa; only the pair pins the behaviour.
"""
import os
import re
import sys

import pytest

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, "scripts"))

import screening_states as S  # noqa: E402

SOURCE = os.path.join(HERE, "scripts", "add_topic_autodiscover.py")


def match_blob_from_source():
    """Use the SHIPPED matcher, not a stand-in, so B and C are tested as they run."""
    with open(SOURCE, encoding="utf-8") as fh:
        src = fh.read()
    i = src.index("DRUG_SYNS = {")
    j = src.index("    return kept") + len("    return kept")
    ns = {"re": re, "os": os}
    exec(compile(src[i:j], SOURCE, "exec"), ns)
    return ns["_match_blob"], ns["DRUG_SYNS"], ns["COND_SYNS"]


MB, DS, CS = match_blob_from_source()
TOPIC = {"drug_patterns": ["dapagliflozin"], "condition_patterns": ["heart failure"]}

TWO_ARMS = [{"ctgov_group_code": "BG0", "count": "10", "scope": "overall",
             "units": "Participants"},
            {"ctgov_group_code": "BG1", "count": "20", "scope": "overall",
             "units": "Participants"}]
ONE_ARM = [{"ctgov_group_code": "BG0", "count": "30", "scope": "overall",
            "units": "Participants"}]
PRIMARY = [{"outcome_type": "Primary", "measure": "death"}]


def classify(pmids=("111",), pubmed_meta=None, baseline=None, outcomes=None,
             aact_rows=(("brief_title", "t"),)):
    return S.classify(
        nct="NCT00000001", topic=TOPIC,
        aact_rows=[dict(aact_rows)] if aact_rows else [],
        intvs=["dapagliflozin 10 mg"], conds=["heart failure"],
        pmids=list(pmids),
        pubmed_meta=pubmed_meta if pubmed_meta is not None else {},
        baseline_rows=TWO_ARMS if baseline is None else baseline,
        design_outcome_rows=PRIMARY if outcomes is None else outcomes,
        match_blob=MB, drug_syns=DS, cond_syns=CS)


def state_of(result, gate):
    """The gate state, unpacked by NAME rather than read out of position [0].

    `classify` returns (state, reason) pairs. Indexing the pair positionally is
    indistinguishable, to a reader and to lint_primary_by_position, from reaching into
    an outcome collection and taking whatever happens to be first -- the defect that
    lint exists to stop. Unpacking says which half is being used.
    """
    state, _reason = result["states"][gate]
    return state


# ---- gate D: the publication --------------------------------------------------------

def test_D_excludes_when_the_abstract_is_present_and_disagrees():
    r = classify(pubmed_meta={"111": {"title": "a trial of something else", "abstract": ""}})
    assert state_of(r, "D_pmid_topic_match") == S.EXCLUDE
    assert r["disposition"] == S.EXCLUDED


def test_D_is_undecidable_when_no_pmid_was_ever_linked():
    r = classify(pmids=())
    state, reason = r["states"]["D_pmid_topic_match"]
    assert state == S.UNDECIDABLE
    assert "never identified" in reason
    assert r["disposition"] == S.UNDECIDABLE


def test_D_is_undecidable_when_the_pmid_is_linked_but_nothing_was_fetched():
    """The unreachable-network case, which used to be recorded as a failed trial."""
    r = classify(pmids=("111",), pubmed_meta={})
    state, reason = r["states"]["D_pmid_topic_match"]
    assert state == S.UNDECIDABLE
    assert "never fetched" in reason
    assert r["disposition"] == S.UNDECIDABLE


def test_D_passes_when_the_abstract_mentions_the_drug():
    r = classify(pubmed_meta={"111": {"title": "Dapagliflozin in heart failure",
                                      "abstract": ""}})
    assert state_of(r, "D_pmid_topic_match") == S.PASS
    assert r["disposition"] == S.INCLUDED


# ---- gate E: the arms ---------------------------------------------------------------

def test_E_excludes_when_counts_are_posted_and_show_one_arm():
    r = classify(pubmed_meta={"111": {"title": "Dapagliflozin heart failure", "abstract": ""}},
                 baseline=ONE_ARM)
    assert state_of(r, "E_two_arms") == S.EXCLUDE
    assert r["disposition"] == S.EXCLUDED


def test_E_is_undecidable_when_no_counts_are_posted_at_all():
    """1,259 of 1,805 measured candidates are in exactly this state."""
    r = classify(pubmed_meta={"111": {"title": "Dapagliflozin heart failure", "abstract": ""}},
                 baseline=[])
    state, reason = r["states"]["E_two_arms"]
    assert state == S.UNDECIDABLE
    assert "not single-armed" in reason
    assert r["disposition"] == S.UNDECIDABLE


# ---- gate F: the outcome ------------------------------------------------------------

def test_F_is_undecidable_when_there_are_no_outcome_rows():
    r = classify(pubmed_meta={"111": {"title": "Dapagliflozin heart failure", "abstract": ""}},
                 outcomes=[])
    state, reason = r["states"]["F_primary_outcome_known"]
    assert state == S.UNDECIDABLE
    assert "unreported, not absent" in reason


def test_F_excludes_when_outcome_rows_exist_but_none_is_primary():
    r = classify(pubmed_meta={"111": {"title": "Dapagliflozin heart failure", "abstract": ""}},
                 outcomes=[{"outcome_type": "Secondary", "measure": "x"}])
    assert state_of(r, "F_primary_outcome_known") == S.EXCLUDE


# ---- the disposition rule -----------------------------------------------------------

def test_an_exclusion_beats_an_undecidable():
    """A candidate with a real exclusion is EXCLUDED even when other gates could not tell."""
    r = classify(pmids=(), baseline=ONE_ARM)
    assert state_of(r, "D_pmid_topic_match") == S.UNDECIDABLE
    assert state_of(r, "E_two_arms") == S.EXCLUDE
    assert r["disposition"] == S.EXCLUDED


def test_a_missing_registration_is_an_exclusion_not_an_undecidable():
    """Absence of the study row IS the answer: the pipeline just scanned that snapshot."""
    r = classify(aact_rows=None)
    assert state_of(r, "A_aact_exists") == S.EXCLUDE
    assert r["disposition"] == S.EXCLUDED


def test_tally_reports_every_state_even_at_zero():
    """A key missing from a tally reads as nothing to report; a present zero reads as looked."""
    t = S.tally([S.INCLUDED, S.INCLUDED])
    assert t == {S.INCLUDED: 2, S.EXCLUDED: 0, S.UNDECIDABLE: 0}
    assert S.EXCLUDED in t and S.UNDECIDABLE in t
