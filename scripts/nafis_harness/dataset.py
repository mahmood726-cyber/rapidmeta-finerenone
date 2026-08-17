"""The regression corpus: every fixture, plus the INVALID cases the fixtures
cannot express.

Controls can only be two-sided (must fire / must stay silent). The third state
is the whole point of this harness, so the INVALID cases live here and are run
on every build. Each one is a dead plate: an instrument that could not see. If
any of them starts returning PASS or FAIL, the harness has lost the distinction
it exists to keep.
"""

from __future__ import annotations

from .baseline import Case, Dataset
from .probes import ALL_CHECKS
from .verdict import Verdict


def _from_fixtures() -> list[Case]:
    cases = []
    for chk in ALL_CHECKS:
        for f in list(chk.must_fire_on) + list(chk.must_be_silent_on):
            cases.append(Case(case_id=f"{chk.check_id}::{f.name}",
                              check_id=chk.check_id, payload=f.payload,
                              expect=f.expect, provenance=f.provenance))
    return cases


# --- the dead plates ---------------------------------------------------------

INVALID_CASES = [
    Case("CHK001::rate_limit_429_is_not_absence", "CHK001_RETRIEVAL_ABSENCE",
         {"endpoint": "api/records?q=X", "http_status": 429, "result_count": 0},
         Verdict.INVALID,
         "a rate-limit 429 read as 'no record exists'"),

    Case("CHK002::unscoped_substring_grep", "CHK002_TOKEN_MATCH",
         {"pattern": "1406", "field": None, "field_scoped": False,
          "hits": ["[1406,1407,1408]"] * 3},
         Verdict.INVALID,
         "grep '1406' matching 1009 of 1243 pages because the digits sit inside "
         "data arrays"),

    Case("CHK003::no_error_no_observation", "CHK003_ACTION_EFFECT",
         {"action": "click(LibKey button)", "error": None,
          "observed_effect_field": None, "pre_state": None, "post_state": None},
         Verdict.INVALID,
         "a LibKey button rendering read as proof of delivery"),

    Case("CHK004::pgrep_on_windows", "CHK004_LIVENESS",
         {"probe": "pgrep", "host_os": "Windows", "stdout": "",
          "corroborated": False},
         Verdict.INVALID,
         "pgrep on Windows always returning nothing, so a liveness check always "
         "reported 'exited'"),

    Case("CHK004::single_empty_probe_no_corroboration", "CHK004_LIVENESS",
         {"probe": "psutil", "host_os": "Linux", "stdout": "",
          "corroborated": False},
         Verdict.INVALID,
         "a daemon reported killed that ran for hours afterwards, double-launching "
         "lanes and burning quota"),

    Case("CHK005::self_consistency_only", "CHK005_EXTERNAL_REFERENT",
         {"referent_name": None, "row": {"tE": 172, "cE": 168, "tN": 4614,
                                         "cN": 4603, "hr": 0.99},
          "external_referent": None},
         Verdict.INVALID,
         "DEFECT-01 -- 'Any check that validates a row by reproducing its own "
         "effect estimate passes it. Consistency does not authenticate a row.'"),

    Case("CHK005::flat_number_bag_referent", "CHK005_EXTERNAL_REFERENT",
         {"referent_name": "registry", "referent_document_id": "NCT02270242",
          "row": {"tN": 3555, "cN": 3564},
          "external_referent": {"tN": 3555, "cN": 3564}},
         Verdict.INVALID,
         "the interface hole -- validate_v2.py's flat number-bag encoding, which "
         "passed all five value mutants before per-key provenance was required"),

    Case("CHK005::key_under_test_absent_from_referent", "CHK005_EXTERNAL_REFERENT",
         {"referent_document_id": "NCT02270242",
          "row": {"tN": 3555, "cN": 3564, "tE": 172},
          "external_referent": {
              "tN": {"value": 3555, "locator": "participantFlow arm1"},
              "cN": {"value": 3564, "locator": "participantFlow arm2"}}},
         Verdict.INVALID,
         "a key present in the row and absent from the referent was silently "
         "skipped; unchecked is not clean"),

    Case("CHK006::identity_from_covering_label", "CHK006_IDENTITY_KEY",
         {"claimed_name": "PARACHUTE-HF", "registration_id": None,
          "source_document": "covering label",
          "source_document_ids": []},
         Verdict.INVALID,
         "a trial identity taken from a covering label rather than a registration "
         "number, conflating PARACHUTE-HF with ANSWER-HF"),

    Case("CHK007::none_found_from_prose", "CHK007_ABSENCE_SCREEN",
         {"screen": None, "findings": []},
         Verdict.INVALID,
         "Rule 4 v1 would have licensed 'M10: screened for, none found' with no "
         "screen having run"),

    Case("CHK008::typed_literal_denominator", "CHK008_FRAME_DENOMINATOR",
         {"frame_name": "syntheses", "numerator": 44, "denominator": 44,
          "denominator_source": "typed_literal", "claim_scope": "complete"},
         Verdict.INVALID,
         "N3 -- a proportion quoted against a number nobody maintained"),

    Case("CHK009::rows_without_outcome_field", "CHK009_POOL_IDENTITY",
         {"panel_name": "classes[24] Ticagrelor mono", "headline_k": 1,
          "headline_outcome": "all_cause_mortality",
          "panel_rows": [{"id": "NCT02270242", "outcome": None,
                          "population": None, "window": None}]},
         Verdict.INVALID,
         "DEFECT-02 -- 'populating outcome on every row would prevent this class "
         "of defect entirely'"),

    Case("CHK010::no_route_log", "CHK010_CHAIN_EXHAUSTION",
         {"target": "supplement chase", "declared_hops": 4, "conclusion": "blocked",
          "hop_log": []},
         Verdict.INVALID,
         "a blocked verdict indistinguishable from an unattempted one"),

    Case("CHK011::correction_from_same_instrument", "CHK011_CORRECTION_BURDEN",
         {"original_value": "ANSWER-HF", "corrected_value": "PARACHUTE-HF",
          "original_source_id": "db:citation_string",
          "correcting_source_id": "db:citation_string",
          "original_rechecked_at_source": True,
          "states_what_original_got_right": True},
         Verdict.INVALID,
         "ANSWER-HF episode -- the original extraction was right and three "
         "separate corrections were wrong"),

    Case("CHK012::unlabelled_layer", "CHK012_LAYER_MATCH",
         {"claim_layer": "access", "observation_layer": "holdings",
          "observed": "title present in host database"},
         Verdict.INVALID,
         "the holdings-table case -- the layers were never labelled, which is the "
         "condition under which this error occurs"),

    Case("CHK013::undocumented_field", "CHK013_FIELD_SEMANTICS",
         {"source": "bibliographic db", "source_field": "year",
          "field_semantics": {}, "target_semantics": "print_publication_year"},
         Verdict.INVALID,
         "a citation year taken from a field whose semantics were never read"),

    Case("CHK014::filter_declared_but_urls_never_inspected", "CHK014_FILTER_FIRED",
         {"query": "site-restricted sweep", "declared_filter": "ema.europa.eu",
          "returned_urls": []},
         Verdict.INVALID,
         "EC-001 -- an unconfirmed filter is UNFILTERED; a negative from it is "
         "not a negative"),

    Case("CHK015::no_declared_expectation", "CHK015_HIT_COUNT_SANITY",
         {"query": "unbounded sweep", "hits": 471547,
          "expected_order_of_magnitude": None, "corpus_size": None},
         Verdict.INVALID,
         "EC-002 -- without a prior expectation any count looks reasonable"),
]

# --- historical FAILs that are not anyone's control fixture -------------------

EXTRA_FAIL_CASES = [
    Case("CHK015::grep_1406_saturates_the_corpus", "CHK015_HIT_COUNT_SANITY",
         {"query": "grep 1406", "hits": 1009, "expected_order_of_magnitude": 5,
          "corpus_size": 1243},
         Verdict.FAIL,
         "grep '1406' matching 1009 of 1243 pages because the digits sit inside "
         "data arrays -- 81% of the corpus is a statement about the pattern"),

    Case("CHK011::correction_reinterpreting_held_material", "CHK011_CORRECTION_BURDEN",
         {"original_value": "x", "corrected_value": "y",
          "original_source_id": "src-A", "correcting_source_id": "src-A-reread",
          "original_rechecked_at_source": True,
          "states_what_original_got_right": True,
          "evidence_is_newly_retrieved_source": False},
         Verdict.FAIL,
         "EB-022 -- the corrections that failed were re-interpretations of "
         "already-held material"),
]


# --- CHK016..CHK025: the dead plates of the ten corpus classes ---------------

CORPUS_INVALID_CASES = [
    Case("CHK016::declared_variance_adjustment", "CHK016_PRECISION_SAMPLE_MISMATCH",
         {"row_id": "hksj-row", "ci_low": 2.09, "ci_high": 21.30,
          "events_t": 45, "n_t": 123, "events_c": 22, "n_c": 128,
          "variance_adjustment_declared": "HKSJ"},
         Verdict.INVALID,
         "HKSJ and random-effects inflation move the interval legitimately; the "
         "check cannot resolve a declared adjustment from a wrong population"),

    Case("CHK016::no_arm_counts", "CHK016_PRECISION_SAMPLE_MISMATCH",
         {"row_id": "no-arms", "ci_low": 2.09, "ci_high": 21.30},
         Verdict.INVALID,
         "without arm sizes there is no second standard error to compare against"),

    Case("CHK016::zero_cell", "CHK016_PRECISION_SAMPLE_MISMATCH",
         {"row_id": "zero-cell", "ci_low": 0.5, "ci_high": 2.0,
          "events_t": 0, "n_t": 100, "events_c": 5, "n_c": 100},
         Verdict.INVALID,
         "a zero cell makes the Woolf SE undefined without a continuity correction"),

    Case("CHK017::single_entry", "CHK017_DUP1_BIT_EQUALITY",
         {"pool_id": "k1", "entries": [{"id": "a", "estimate": 0.5}]},
         Verdict.INVALID,
         "duplication is undefined below two entries"),

    Case("CHK018::direction_not_declared", "CHK018_MIXED_POOLING",
         {"pool_id": "undeclared",
          "entries": [{"id": "a", "measure": "HR"},
                      {"id": "b", "measure": "HR"}]},
         Verdict.INVALID,
         "mixed pooling cannot be seen unless each entry declares its measure and "
         "its direction of benefit"),

    Case("CHK019::no_engine_ids", "CHK019_INERT_ENGINE",
         {"page_id": "p", "engine_trial_ids": [], "data_trial_ids": ["NCT1"]},
         Verdict.INVALID,
         "an empty engine list is a different defect and must not read as inert"),

    Case("CHK020::engine_capability_unknown", "CHK020_ORPHAN_POOLED_RESULT",
         {"page_id": "p", "displayed_pooled_estimate": 0.87,
          "engine_can_pool": None},
         Verdict.INVALID,
         "an orphan cannot be distinguished from a computed result until the "
         "engine's capability is determined"),

    Case("CHK021::scale_not_declared", "CHK021_MEASURE_SCALE_MISMATCH",
         {"row_id": "r", "measure": "MD", "stored_scale": None},
         Verdict.INVALID,
         "the back-transform bug is invisible unless the stored scale is declared"),

    Case("CHK022::no_source_text", "CHK022_RATIO_FROM_PERCENTAGE",
         {"row_id": "r", "extracted_measure": "RR", "source_text": None},
         Verdict.INVALID,
         "MORDOR-I -- without the source wording there is nothing to check the "
         "ratio against"),

    Case("CHK023::intervention_unnamed", "CHK023_CROSS_AGENT_POOLING",
         {"pool_id": "p", "entries": [{"id": "a"}, {"id": "b"}]},
         Verdict.INVALID,
         "entries that do not name their intervention cannot be tested for "
         "cross-agent pooling"),

    Case("CHK024::no_method_claimed", "CHK024_FALSE_METHOD_CLAIM",
         {"page_id": "p", "claimed_method": None, "network_edges": []},
         Verdict.INVALID,
         "no method claimed, so there is no claim to falsify"),

    Case("CHK025::single_surface", "CHK025_MULTI_SURFACE_DISAGREEMENT",
         {"claim_id": "c", "surfaces": {"card": {"value": 1.0, "status": "live"}}},
         Verdict.INVALID,
         "disagreement is undefined on one surface"),
]


# --- CHK026..CHK030: build-path dead plates ----------------------------------

BUILD_INVALID_CASES = [
    Case("CHK026::blank_absence_panel_asserts_nothing",
         "CHK026_WRONG_REASON_ABSENCE_PANEL",
         {"page_id": "P", "page_provenance": "converted",
          "absence_reason_id": None},
         Verdict.INVALID,
         "a blank panel makes no claim -- it is neither a defect nor a pass"),

    Case("CHK026::reason_declares_no_valid_provenances",
         "CHK026_WRONG_REASON_ABSENCE_PANEL",
         {"page_id": "P", "page_provenance": "converted",
          "absence_reason_id": "no-database-search", "reason_valid_for": None},
         Verdict.INVALID,
         "an unconditioned reason cannot be checked against the page"),

    Case("CHK027::no_sentinel_vocabulary", "CHK027_SENTINEL_LEAK",
         {"surface_id": "s", "reader_text": "anything at all", "sentinels": []},
         Verdict.INVALID,
         "leakage is not decidable without the closed sentinel set"),

    Case("CHK028::card_without_a_source_citation",
         "CHK028_DISQUALIFIED_REFERENT_PROMOTED",
         {"claim_id": "x", "card": {"measure": "HR", "value": 0.55},
          "object": {"measure": "OR", "value": 0.7290}},
         Verdict.INVALID,
         "the sourced-value-wins rule needs a source; this is a plain conflict"),

    Case("CHK029::no_naive_parse_recorded", "CHK029_SIGN_NORMALISATION",
         {"field_id": "f", "raw": "&minus;71.31"},
         Verdict.INVALID,
         "nothing to compare the normalised parse against"),

    Case("CHK030::build_path_not_recorded", "CHK030_BUILD_MODE_BLIND_TEXT",
         {"string_id": "s", "text": "because X", "asserts_rationale": True,
          "valid_for_paths": ["author"], "build_path": None},
         Verdict.INVALID,
         "a rationale cannot be conditioned on a path that was not recorded"),
]

BUILD_FAIL_CASES = [
    Case("CHK029::en_dash_range_parsed_as_a_scalar", "CHK029_SIGN_NORMALISATION",
         {"field_id": "ci", "raw": "0.73–1.13", "naive_value": -1.13},
         Verdict.FAIL,
         "an en-dash range read as a negative number -- the inverse of the "
         "&minus; bug and the false positive the normaliser must avoid"),

    Case("CHK027::sentinel_visible_nine_times", "CHK027_SENTINEL_LEAK",
         {"surface_id": "converted-panel",
          "reader_text": " ".join(["NOT RECOVERABLE FROM THE PAGE"] * 9),
          "sentinels": ["NOT RECOVERABLE FROM THE PAGE"]},
         Verdict.FAIL,
         "the reported nine occurrences, as a count rather than a boolean"),
]


def historical_dataset() -> Dataset:
    return Dataset(name="nafis-historical-incidents",
                   cases=tuple(_from_fixtures() + INVALID_CASES
                               + EXTRA_FAIL_CASES + CORPUS_INVALID_CASES
                               + BUILD_INVALID_CASES + BUILD_FAIL_CASES))
