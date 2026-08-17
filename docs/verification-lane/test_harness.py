"""Self-tests for the harness -- including tests that the harness can fail.

These are the meta-tests. It is not enough that the thirteen detectors fire on
their fixtures; the machinery that admits and runs them must itself be shown to
reject the things it claims to reject. A harness whose own tests cannot fail is
the check-that-cannot-fail one layer up.

Run:  python -m unittest test_harness -v
"""

from __future__ import annotations

import copy
import os
import tempfile
import unittest

from nafis_harness import (Case, Check, Dataset, Fixture, InadmissibleDetector,
                           Instrument, Ledger, Registry, Result, Verdict,
                           Witness, build_registry, diff_baseline, make_fail,
                           make_invalid, make_pass, run_dataset, save_baseline,
                           load_baseline, tally)
from nafis_harness.dataset import historical_dataset


# =============================================================================
# 1. The witness rule
# =============================================================================

class TestWitnessRule(unittest.TestCase):

    def test_pass_without_witness_is_coerced_to_invalid(self):
        r = Result(check_id="X", verdict=Verdict.PASS, instrument="i")
        self.assertIs(r.verdict, Verdict.INVALID)
        self.assertIn("no witness supplied", r.reason)

    def test_pass_without_opposite_declaration_is_coerced_to_invalid(self):
        r = Result(check_id="X", verdict=Verdict.PASS, instrument="i",
                   witness=Witness(observed="saw it", locator="here",
                                   opposite_would_be=""))
        self.assertIs(r.verdict, Verdict.INVALID)
        self.assertIn("instrument declaration missing", r.reason)

    def test_complete_witness_survives(self):
        r = make_pass("X", "i", observed="o", locator="l", opposite_would_be="w")
        self.assertIs(r.verdict, Verdict.PASS)

    def test_fail_now_requires_a_witness_too(self):
        """The symmetric obligation. Instance 5 is the reason.

        The lane's first version of this rule "was written asymmetrically: it
        demanded a positive-detection story before recording a NEGATIVE. Within
        the hour it failed in the other direction" -- a LibKey button read as
        proof of entitlement. A FAIL asserted from an instrument that could not
        have cleared the subject is as void as a PASS from one that could not
        have failed it.
        """
        r = Result(check_id="X", verdict=Verdict.FAIL, instrument="i",
                   reason="bad")
        self.assertIs(r.verdict, Verdict.INVALID)
        self.assertIn("FAIL refused", r.reason)

        ok = make_fail("X", "i", "bad", observed="o", locator="l",
                       opposite_would_be="what a PASS would have looked like")
        self.assertIs(ok.verdict, Verdict.FAIL)

    def test_invalid_needs_no_witness(self):
        self.assertIs(make_invalid("X", "i", "blind").verdict, Verdict.INVALID)

    def test_result_refuses_to_be_a_boolean(self):
        # `if result:` would make INVALID truthy -- the exact collapse this
        # harness exists to prevent.
        with self.assertRaises(TypeError):
            bool(make_invalid("X", "i", "blind"))

    def test_tally_keeps_invalid_out_of_the_reportable_denominator(self):
        t = tally([make_pass("A", "i", "o", "l", "w"),
                   make_fail("B", "i", "r", observed="o", locator="l",
                             opposite_would_be="w"),
                   make_invalid("C", "i", "r")])
        self.assertEqual(t["reportable"], 2)
        self.assertEqual(t["total"], 3)
        self.assertNotIn("clean", t)


# =============================================================================
# 2. Admissibility -- a detector that has never fired cannot be registered
# =============================================================================

def _always_pass(_p):
    return make_pass("NEVER_FIRES", "constant", observed="fine", locator="nowhere",
                     opposite_would_be="not fine")


class TestAdmissibility(unittest.TestCase):

    def test_detector_without_fixtures_is_rejected(self):
        chk = Check(check_id="NEVER_FIRES",
                    instrument=Instrument("constant", reads=()),
                    fn=_always_pass)
        with self.assertRaises(InadmissibleDetector) as ctx:
            Registry().register(chk)
        msg = str(ctx.exception)
        self.assertIn("never been demonstrated firing", msg)
        self.assertIn("never been demonstrated silent", msg)
        self.assertIn("no observation_terms", msg)

    def test_the_ok_1_evaluator_cannot_be_registered(self):
        """The LangSmith failure mode, made unrepresentable.

        An evaluator that returns {"ok": 1} for everything shows 100% green on a
        LangSmith dashboard with no warning. Here it cannot be registered at all:
        it has no fixture it fires on, because there is none.
        """
        chk = Check(check_id="OK_1", instrument=Instrument("constant", reads=()),
                    fn=_always_pass,
                    must_fire_on=[Fixture("a_real_defect", {"defect": True},
                                          Verdict.FAIL)],
                    must_be_silent_on=[Fixture("a_real_clean", {"defect": False},
                                               Verdict.PASS)],
                    observation_terms={"defect": lambda p: {**p, "defect": True}})
        reg = Registry()
        reg.register(chk)                      # admissible on paper
        report = reg.self_test()               # but not in fact
        self.assertFalse(report["ok"])
        self.assertIn("OK_1", report["unfit"])
        # and any run through it is void, not green
        self.assertIs(reg.run("OK_1", {"defect": True}).verdict, Verdict.INVALID)

    def test_unregistered_check_returns_invalid_not_pass(self):
        self.assertIs(Registry().run("NOPE", {}).verdict, Verdict.INVALID)


# =============================================================================
# 3. Controls -- the dead-plate rule
# =============================================================================

class TestControls(unittest.TestCase):

    def test_control_failure_voids_the_run(self):
        state = {"broken": False}

        def fn(p):
            if state["broken"]:
                return make_pass("DP", "i", observed="o", locator="l",
                                 opposite_would_be="w")   # always passes now
            return (make_fail("DP", "i", "defect", observed="o", locator="l",
                              opposite_would_be="w") if p.get("defect")
                    else make_pass("DP", "i", "o", "l", "w"))

        chk = Check("DP", Instrument("i", reads=("defect",)), fn,
                    must_fire_on=[Fixture("pos", {"defect": True}, Verdict.FAIL)],
                    must_be_silent_on=[Fixture("neg", {"defect": False}, Verdict.PASS)],
                    observation_terms={"defect": lambda p: {**p, "defect": True}})
        reg = Registry(); reg.register(chk)

        self.assertIs(reg.run("DP", {"defect": False}).verdict, Verdict.PASS)

        state["broken"] = True          # the plate dies mid-campaign
        r = reg.run("DP", {"defect": False})
        self.assertIs(r.verdict, Verdict.INVALID)
        self.assertIn("control failure", r.reason)


# =============================================================================
# 4. Vacuity
# =============================================================================

class TestVacuity(unittest.TestCase):

    def test_a_check_that_ignores_its_observation_term_is_vacuous(self):
        """The caption checker that read the downloads block.

        `fn` claims to observe `captions` but actually reads `downloads`. It
        passes a document with broken captions. Forcing `captions` to broken
        leaves the PASS standing, so the PASS never depended on captions.
        """
        def fn(p):
            return (make_fail("CAP", "i", "downloads block malformed",
                              observed="downloads block malformed", locator="doc",
                              opposite_would_be="a well-formed downloads block")
                    if p.get("downloads") == "broken"
                    else make_pass("CAP", "i", observed="captions fine",
                                   locator="doc", opposite_would_be="a bad caption"))

        chk = Check("CAP", Instrument("i", reads=("captions",)), fn,
                    must_fire_on=[Fixture("pos", {"downloads": "broken",
                                                  "captions": "ok"}, Verdict.FAIL)],
                    must_be_silent_on=[Fixture("neg", {"downloads": "ok",
                                                       "captions": "ok"}, Verdict.PASS)],
                    observation_terms={"captions": lambda p: {**p, "captions": "broken"}})
        reg = Registry(); reg.register(chk)

        r = reg.run("CAP", {"downloads": "ok", "captions": "ok"})
        self.assertIs(r.verdict, Verdict.INVALID)
        self.assertIn("vacuous", r.reason)
        self.assertIn("captions", r.vacuity["vacuous_terms"])

    def test_every_shipped_detector_is_non_vacuous_on_its_clean_fixture(self):
        for chk in build_registry()._checks.values():
            for f in chk.must_be_silent_on:
                with self.subTest(check=chk.check_id, fixture=f.name):
                    vac = chk.run_vacuity(f.payload)
                    self.assertTrue(vac["ok"],
                                    f"{chk.check_id} vacuous in "
                                    f"{vac['vacuous_terms']}")


# =============================================================================
# 5. The thirteen detectors, on the record
# =============================================================================

class TestShippedDetectors(unittest.TestCase):

    def setUp(self):
        self.reg = build_registry()

    def test_registry_is_fit(self):
        rep = self.reg.self_test()
        self.assertTrue(rep["ok"], rep["unfit"])
        self.assertEqual(rep["n_checks"], 30)

    def test_correction_reinterpreting_held_material_fails(self):
        """The rule that corrections must come from a newly retrieved source.

        EB-021 -> EB-022: the rule correcting the bash false zeros re-interpreted
        the same mount and was itself wrong for ~7 hours.
        """
        r = self.reg.run("CHK011_CORRECTION_BURDEN",
                         {"original_source_id": "src-A",
                          "correcting_source_id": "src-A-reread",
                          "original_rechecked_at_source": True,
                          "states_what_original_got_right": True,
                          "evidence_is_newly_retrieved_source": False})
        self.assertIs(r.verdict, Verdict.FAIL)
        self.assertIn("not a newly retrieved", r.reason)

    def test_unconfirmed_domain_filter_is_unfiltered(self):
        r = self.reg.run("CHK014_FILTER_FIRED",
                         {"query": "q", "declared_filter": "ema.europa.eu",
                          "returned_urls": []})
        self.assertIs(r.verdict, Verdict.INVALID)
        self.assertIn("UNFILTERED", r.reason)

    def test_saturating_hit_count_is_a_degenerate_pattern(self):
        r = self.reg.run("CHK015_HIT_COUNT_SANITY",
                         {"query": "grep 1406", "hits": 1009,
                          "expected_order_of_magnitude": 5, "corpus_size": 1243})
        self.assertIs(r.verdict, Verdict.FAIL)
        self.assertIn("degenerate", r.reason)

    def test_token_match_negative_fixture_is_corpus_derived(self):
        """protocol Sec 6: this class is caught 'only if the negative fixture is
        derived from real corpus material containing the same confounding digits.
        A synthetic negative will not contain them.'"""
        chk = self.reg.get("CHK002_TOKEN_MATCH")
        fx = chk.must_be_silent_on[0]
        self.assertIn("corpus_source", fx.payload)
        self.assertTrue(any("Nonfatal" in s
                            for s in fx.payload["field_contents_verbatim"]),
                        "the clean fixture must retain the confounder")

    def test_429_is_invalid_not_absence(self):
        r = self.reg.run("CHK001_RETRIEVAL_ABSENCE",
                         {"endpoint": "api/x", "http_status": 429, "result_count": 0})
        self.assertIs(r.verdict, Verdict.INVALID)
        self.assertIn("not about the record", r.reason)

    def test_pgrep_on_windows_is_invalid_not_exited(self):
        r = self.reg.run("CHK004_LIVENESS",
                         {"probe": "pgrep", "host_os": "Windows", "stdout": "",
                          "corroborated": False})
        self.assertIs(r.verdict, Verdict.INVALID)
        self.assertIn("same empty output for a live process and a dead one", r.reason)

    def test_self_consistent_row_without_referent_is_invalid(self):
        r = self.reg.run("CHK005_EXTERNAL_REFERENT",
                         {"row": {"tE": 172, "cE": 168, "tN": 4614, "cN": 4603},
                          "external_referent": None})
        self.assertIs(r.verdict, Verdict.INVALID)
        self.assertIn("cannot distinguish a correct row from a fabricated one",
                      r.reason)

    def test_twilight_location_b_fails_against_the_registry(self):
        r = self.reg.run("CHK005_EXTERNAL_REFERENT",
                         {"referent_name": "NCT02270242 participant flow",
                          "referent_document_id": "NCT02270242",
                          "row": {"tN": 4614, "cN": 4603},
                          "external_referent": {
                              "tN": {"value": 3555, "locator": "participantFlow arm1"},
                              "cN": {"value": 3564,
                                     "locator": "participantFlow arm2"}}})
        self.assertIs(r.verdict, Verdict.FAIL)

    # --- the three defects found by mutation testing, not by review ----------

    def test_flat_number_bag_referent_is_invalid_not_pass(self):
        """DEFECT 1 -- the interface hole.

        The detector killed all five value mutants when handed a keyed referent
        and PASSED all five when handed a flat number-bag: the encoding
        validate_v2.py used, and the historical failure. A bag has nowhere to put
        a locator, so requiring per-key provenance closes it structurally.
        """
        r = self.reg.run("CHK005_EXTERNAL_REFERENT",
                         {"referent_name": "NCT02270242", "referent_document_id":
                          "NCT02270242", "row": {"tN": 3555, "cN": 3564},
                          "external_referent": {"tN": 3555, "cN": 3564}})
        self.assertIs(r.verdict, Verdict.INVALID)
        self.assertIn("Agreement authenticates nothing", r.reason)

    def test_unprovenanced_referent_still_reports_a_disagreement(self):
        """The over-correction, caught by the benchmark lane's mutant set.

        Requiring provenance before ANY verdict closed the number-bag hole and
        broke the honest caller: arm A fell 7/7 -> 2/7, five real kills becoming
        five refusals. Provenance now gates the AGREEMENT path only, because
        'agreement authenticates nothing. Only disagreement is informative.'
        """
        r = self.reg.run("CHK005_EXTERNAL_REFERENT",
                         {"referent_name": "Cochrane SoF", "row": {"ve": 95.1},
                          "external_referent": {"ve": 91.1}})   # no provenance
        self.assertIs(r.verdict, Verdict.FAIL)
        self.assertIn("disagrees", r.reason)

    def test_referent_without_document_id_cannot_clear_a_row(self):
        r = self.reg.run("CHK005_EXTERNAL_REFERENT",
                         {"referent_name": "somewhere", "row": {"tN": 3555},
                          "external_referent": {
                              "tN": {"value": 3555, "locator": "x"}}})
        self.assertIs(r.verdict, Verdict.INVALID)
        self.assertIn("no referent_document_id", r.reason)

    def test_key_with_value_but_no_locator_cannot_clear_a_row(self):
        r = self.reg.run("CHK005_EXTERNAL_REFERENT",
                         {"referent_document_id": "NCT1", "row": {"tN": 3555},
                          "external_referent": {"tN": {"value": 3555,
                                                       "locator": "  "}}})
        self.assertIs(r.verdict, Verdict.INVALID)
        self.assertIn("no locator on ['tN']", r.reason)

    def test_enrolment_delta_below_resolution_is_not_certified(self):
        """M5b -- found by the benchmark lane's set, not by mine.

        registry_enrolment 33758 -> 33759 returned PASS, because 1 is far inside
        max(0.1*enrol, 50). The tolerance is right; certifying inside it is not.
        A tolerance says the instrument cannot resolve differences of that size.
        """
        base = {"claimed_name": "Sputnik-V-phase3",
                "registration_id": "NCT04530396",
                "source_document": "NCT04530396.ctgov.json",
                "source_document_ids": ["NCT04530396"],
                "registry_acronym": "Sputnik-V-phase3"}
        r = self.reg.run("CHK006_IDENTITY_KEY",
                         {**base, "registry_enrolment": 33759, "row_weight": 33758})
        self.assertIs(r.verdict, Verdict.INVALID)
        self.assertIn("below its resolution", r.reason)

        # an explained delta clears it, as CHK002 does for PARAGON-HF
        r2 = self.reg.run("CHK006_IDENTITY_KEY",
                          {**base, "registry_enrolment": 33759, "row_weight": 33758,
                           "enrolment_delta_explained": "1 post-randomisation "
                                                        "withdrawal excluded from FAS"})
        self.assertIs(r2.verdict, Verdict.PASS)

        # an exact match needs no explanation
        r3 = self.reg.run("CHK006_IDENTITY_KEY",
                          {**base, "registry_enrolment": 33758, "row_weight": 33758})
        self.assertIs(r3.verdict, Verdict.PASS)

    def test_key_under_test_missing_from_referent_is_invalid_not_skipped(self):
        """DEFECT 2 -- a field nobody checked must not read as a field that passed."""
        r = self.reg.run("CHK005_EXTERNAL_REFERENT",
                         {"referent_document_id": "NCT02270242",
                          "row": {"tN": 3555, "cN": 3564, "tE": 172},
                          "external_referent": {
                              "tN": {"value": 3555, "locator": "flow arm1"},
                              "cN": {"value": 3564, "locator": "flow arm2"}}})
        self.assertIs(r.verdict, Verdict.INVALID)
        self.assertIn("['tE']", r.reason)
        self.assertIn("unchecked is not clean", r.reason)

    def test_vacuity_sweeps_every_key_not_the_alphabetically_first(self):
        """DEFECT 3 -- coverage that depends on key spelling is not coverage.

        Renaming a key must not change what the sweep covers. Both spellings
        must be swept, and the report must name the specific sub-mutant.
        """
        chk = self.reg.get("CHK005_EXTERNAL_REFERENT")
        base = dict(chk.must_be_silent_on[0].payload)
        vac = chk.run_vacuity(base)
        self.assertTrue(vac["ok"], vac["vacuous_terms"])
        labels = [o["mutant"] for o in vac["terms"]["row"]]
        self.assertEqual(sorted(labels), ["row[cN]", "row[tN]"])

        # rename so the previously-swept key is no longer alphabetically first
        renamed = copy.deepcopy(base)
        renamed["row"] = {"zz_tN": base["row"]["tN"], "cN": base["row"]["cN"]}
        renamed["external_referent"] = {
            "zz_tN": base["external_referent"]["tN"],
            "cN": base["external_referent"]["cN"]}
        vac2 = chk.run_vacuity(renamed)
        self.assertTrue(vac2["ok"], vac2["vacuous_terms"])
        self.assertEqual(sorted(o["mutant"] for o in vac2["terms"]["row"]),
                         ["row[cN]", "row[zz_tN]"])

    def test_stripping_referent_provenance_is_a_swept_term(self):
        chk = self.reg.get("CHK005_EXTERNAL_REFERENT")
        vac = chk.run_vacuity(dict(chk.must_be_silent_on[0].payload))
        self.assertEqual(vac["terms"]["referent_provenance"], "INVALID")

    def test_identity_from_a_label_is_invalid(self):
        r = self.reg.run("CHK006_IDENTITY_KEY",
                         {"claimed_name": "PARACHUTE-HF", "registration_id": None,
                          "source_document_ids": []})
        self.assertIs(r.verdict, Verdict.INVALID)
        self.assertIn("Names are not keys", r.reason)

    def test_none_found_from_prose_is_not_screened(self):
        r = self.reg.run("CHK007_ABSENCE_SCREEN", {"screen": None, "findings": []})
        self.assertIs(r.verdict, Verdict.INVALID)
        self.assertIn("NOT SCREENED", r.reason)

    def test_k3_panel_under_k4_headline_fails(self):
        rows = [{"id": f"T{i}", "outcome": "acm", "population": "randomised",
                 "window": "full"} for i in range(3)]
        r = self.reg.run("CHK009_POOL_IDENTITY",
                         {"panel_name": "p", "headline_k": 4,
                          "headline_outcome": "acm", "panel_rows": rows})
        self.assertIs(r.verdict, Verdict.FAIL)
        self.assertIn("headline states k=4, panel carries 3 rows", r.reason)

    def test_chain_abandoned_at_hop_zero_fails(self):
        r = self.reg.run("CHK010_CHAIN_EXHAUSTION",
                         {"target": "t", "declared_hops": 4, "conclusion": "blocked",
                          "hop_log": [{"hop": 0, "outcome": "failed"}]})
        self.assertIs(r.verdict, Verdict.FAIL)
        self.assertIn("3 hop(s) never attempted", r.reason)

    def test_correction_from_the_same_instrument_is_invalid(self):
        r = self.reg.run("CHK011_CORRECTION_BURDEN",
                         {"original_source_id": "db:x", "correcting_source_id": "db:x",
                          "original_rechecked_at_source": True,
                          "states_what_original_got_right": True})
        self.assertIs(r.verdict, Verdict.INVALID)

    def test_holdings_read_as_entitlement_fails_when_layers_are_labelled(self):
        r = self.reg.run("CHK012_LAYER_MATCH",
                         {"claim_layer": "entitlement", "observation_layer": "holdings",
                          "observed": "title in holdings table"})
        self.assertIs(r.verdict, Verdict.FAIL)

    def test_holdings_case_is_invalid_when_the_layers_are_not_labelled(self):
        """The known blind spot, asserted rather than hidden.

        The historical error was not a mislabelled layer; it was a failure to see
        that there were two layers. Unlabelled, the best this detector can do is
        refuse to answer -- which is better than a false PASS, and is not the
        same as catching it.
        """
        r = self.reg.run("CHK012_LAYER_MATCH",
                         {"claim_layer": "access", "observation_layer": "holdings",
                          "observed": "title in holdings table"})
        self.assertIs(r.verdict, Verdict.INVALID)


# =============================================================================
# 6. The baseline runner -- the LangSmith pattern, with the guard
# =============================================================================

class TestBaseline(unittest.TestCase):

    def test_historical_dataset_runs_clean(self):
        reg = build_registry()
        rec = run_dataset(reg, historical_dataset())
        self.assertEqual(rec.counts["mismatch"], 0,
                         [k for k, v in rec.results.items() if v["status"] != "match"])
        self.assertEqual(rec.counts["invalid"], 0)
        self.assertTrue(rec.discriminating)
        self.assertEqual(rec.notes, [])

    def test_dataset_with_no_failing_case_is_refused(self):
        ds = Dataset("all-green", cases=[
            Case("c1", "CHK001_RETRIEVAL_ABSENCE",
                 {"endpoint": "e", "http_status": 200, "result_count": 0},
                 Verdict.PASS)])
        problems = ds.discrimination_problems()
        self.assertTrue(any("no case expects FAIL" in p for p in problems))

    def test_a_run_that_returns_one_verdict_everywhere_is_non_discriminating(self):
        reg = build_registry()
        ds = Dataset("constant", cases=[
            Case("a", "CHK001_RETRIEVAL_ABSENCE",
                 {"endpoint": "e", "http_status": 200, "result_count": 0},
                 Verdict.PASS),
            Case("b", "CHK001_RETRIEVAL_ABSENCE",
                 {"endpoint": "e", "http_status": 200, "result_count": 0},
                 Verdict.FAIL)])
        rec = run_dataset(reg, ds)
        self.assertFalse(rec.discriminating)
        self.assertTrue(any("NON-DISCRIMINATING" in n for n in rec.notes))

    def test_diff_flags_a_case_that_went_blind(self):
        reg = build_registry()
        with tempfile.TemporaryDirectory() as td:
            path = os.path.join(td, "b.json")
            rec = run_dataset(reg, historical_dataset())
            save_baseline(rec, path)
            base = load_baseline(path)
            # simulate an instrument losing its sight between runs
            key = "CHK005_EXTERNAL_REFERENT::twilight_location_a"
            rec.results[key]["got"] = "INVALID"
            diff = diff_baseline(rec, base)
            self.assertEqual(len(diff["went_blind"]), 1)
            self.assertEqual(diff["went_blind"][0]["case"], key)


# =============================================================================
# 7. The interrupt ledger
# =============================================================================

class TestLedger(unittest.TestCase):

    def test_pending_interrupt_blocks_reporting_and_resolution_is_read_not_rederived(self):
        with tempfile.TemporaryDirectory() as td:
            led = Ledger(os.path.join(td, "ledger.jsonl"))
            led.raise_interrupt("TWILIGHT-01",
                                "classes[20].pool is invalid until the composite row "
                                "is resolved; do not guess",
                                ["remove row", "replace with true ACM"],
                                nct="NCT02270242")
            ok, blockers = led.may_report()
            self.assertFalse(ok)
            self.assertEqual(len(blockers), 1)

            led.resolve("TWILIGHT-01", "remove row", "Mahmood",
                        "true ACM not recovered; do not substitute the AE module")
            ok, blockers = led.may_report()
            self.assertTrue(ok)
            self.assertEqual(blockers, [])

            # resumption reads the record; it does not re-derive the decision
            state = Ledger(os.path.join(td, "ledger.jsonl")).state()
            self.assertEqual(state["TWILIGHT-01"].decision, "remove row")
            self.assertEqual(state["TWILIGHT-01"].resolved_by, "Mahmood")


# =============================================================================
# 8. Fixture provenance -- every fixture points at a real incident
# =============================================================================

class TestProvenance(unittest.TestCase):

    def test_every_shipped_fixture_names_the_incident_it_encodes(self):
        for chk in build_registry()._checks.values():
            for f in list(chk.must_fire_on) + list(chk.must_be_silent_on):
                with self.subTest(check=chk.check_id, fixture=f.name):
                    self.assertTrue(f.provenance.strip(),
                                    "a fixture with no provenance will be deleted "
                                    "as noise by the next person")


# =============================================================================
# 9. The ten corpus classes -- CHK016..CHK025
# =============================================================================

class TestCorpusDetectors(unittest.TestCase):

    def setUp(self):
        self.reg = build_registry()

    # --- CHK016, the strongest of the ten -----------------------------------

    def test_precision_sample_mismatch_arithmetic_is_correct(self):
        """The check is arithmetic, so its arithmetic is testable independently."""
        import math
        from nafis_harness.probes_corpus import _se_from_ci, _se_from_counts
        self.assertAlmostEqual(_se_from_ci(2.09, 21.30), 0.5922, places=4)
        self.assertAlmostEqual(_se_from_counts(45, 123, 22, 128), 0.2999, places=4)
        self.assertAlmostEqual(_se_from_ci(0.4009, 1.1120), 0.2603, places=4)
        # MITRAL's point estimate is the exact geometric mean of its own bounds
        self.assertAlmostEqual(math.sqrt(0.4009 * 1.1120), 0.6677, places=4)

    def test_mavacamten_estimate_came_from_a_different_sample(self):
        r = self.reg.run("CHK016_PRECISION_SAMPLE_MISMATCH",
                         {"row_id": "MAVACAMTEN_HCM", "estimate": 6.67,
                          "ci_low": 2.09, "ci_high": 21.30,
                          "events_t": 45, "n_t": 123, "events_c": 22, "n_c": 128})
        self.assertIs(r.verdict, Verdict.FAIL)
        self.assertAlmostEqual(r.evidence["ratio"], 1.975, places=2)
        self.assertAlmostEqual(r.evidence["implied_estimate"], 2.780, places=2)

    def test_declared_variance_adjustment_is_invalid_not_pass(self):
        """HKSJ and random-effects inflation move the interval legitimately.

        The check cannot resolve a declared adjustment from a wrong population,
        so it must refuse rather than clear. Same rule as CHK006's tolerance band.
        """
        r = self.reg.run("CHK016_PRECISION_SAMPLE_MISMATCH",
                         {"row_id": "x", "ci_low": 2.09, "ci_high": 21.30,
                          "events_t": 45, "n_t": 123, "events_c": 22, "n_c": 128,
                          "variance_adjustment_declared": "HKSJ"})
        self.assertIs(r.verdict, Verdict.INVALID)

    def test_missing_arms_is_invalid_not_pass(self):
        r = self.reg.run("CHK016_PRECISION_SAMPLE_MISMATCH",
                         {"row_id": "x", "ci_low": 2.09, "ci_high": 21.30})
        self.assertIs(r.verdict, Verdict.INVALID)

    # --- CHK017 --------------------------------------------------------------

    def test_bit_equality_is_a_proof_not_an_inference(self):
        r = self.reg.run("CHK017_DUP1_BIT_EQUALITY",
                         {"pool_id": "AZ",
                          "entries": [{"id": "a", "estimate": -0.15082288973458366,
                                       "variance": 0.0041},
                                      {"id": "b", "estimate": -0.15082288973458366,
                                       "variance": 0.0117}],
                          "pooled_estimate": -0.15082288973458366})
        self.assertIs(r.verdict, Verdict.FAIL)
        self.assertIn("inverse-variance pooling of one repeated value", r.reason)

    def test_near_miss_estimates_do_not_fire(self):
        """The stress case the shipped negative does not cover -- see FIXTURE_STATUS.

        Two entries agreeing to six decimals but not at full precision are two
        estimates, not one. If this ever fires, the check has become a
        similarity heuristic and stops being a proof.
        """
        r = self.reg.run("CHK017_DUP1_BIT_EQUALITY",
                         {"pool_id": "near",
                          "entries": [{"id": "a", "estimate": -0.150822889734,
                                       "variance": 0.004},
                                      {"id": "b", "estimate": -0.150822889735,
                                       "variance": 0.011}]})
        self.assertIs(r.verdict, Verdict.PASS)

    # --- CHK018 --------------------------------------------------------------

    def test_high_heterogeneity_single_endpoint_must_not_fire(self):
        """INCLISIRAN I^2 = 72%. The dismantled signature would have fired here."""
        r = self.reg.run("CHK018_MIXED_POOLING",
                         {"pool_id": "INCLISIRAN_LIPID", "i_squared": 72,
                          "entries": [{"id": f"ORION-{i}", "measure": "MD",
                                       "direction_of_benefit": "efficacy"}
                                      for i in (9, 10, 11)]})
        self.assertIs(r.verdict, Verdict.PASS)

    def test_declared_composite_may_mix_directions(self):
        r = self.reg.run("CHK018_MIXED_POOLING",
                         {"pool_id": "vte-or-bleed", "composite_endpoint": True,
                          "entries": [{"id": "a", "measure": "HR",
                                       "direction_of_benefit": "efficacy"},
                                      {"id": "b", "measure": "HR",
                                       "direction_of_benefit": "harm"}]})
        self.assertIs(r.verdict, Verdict.PASS)

    def test_bleeding_pooled_with_efficacy_fires(self):
        r = self.reg.run("CHK018_MIXED_POOLING",
                         {"pool_id": "cardio-7",
                          "entries": [{"id": "eff", "measure": "HR",
                                       "direction_of_benefit": "efficacy"},
                                      {"id": "bleed", "measure": "HR",
                                       "direction_of_benefit": "harm"}]})
        self.assertIs(r.verdict, Verdict.FAIL)
        self.assertIn("opposite directions of benefit", r.reason)

    def test_i_squared_is_not_an_input(self):
        """Guard on the guard: adding I^2 must not change any verdict."""
        base = {"pool_id": "p",
                "entries": [{"id": "a", "measure": "MD",
                             "direction_of_benefit": "efficacy"},
                            {"id": "b", "measure": "MD",
                             "direction_of_benefit": "efficacy"}]}
        for i2 in (0, 50, 91, 99):
            self.assertIs(self.reg.run("CHK018_MIXED_POOLING",
                                       {**base, "i_squared": i2}).verdict,
                          Verdict.PASS, f"I^2={i2} changed the verdict")

    # --- the rest ------------------------------------------------------------

    def test_inert_engine_fires_and_wired_page_does_not(self):
        self.assertIs(self.reg.run("CHK019_INERT_ENGINE",
                                   {"page_id": "p", "engine_trial_ids": ["NCT1"],
                                    "data_trial_ids": ["NCT2"]}).verdict,
                      Verdict.FAIL)
        self.assertIs(self.reg.run("CHK019_INERT_ENGINE",
                                   {"page_id": "p", "engine_trial_ids": ["NCT1"],
                                    "data_trial_ids": ["NCT1", "NCT2"]}).verdict,
                      Verdict.PASS)

    def test_orphan_pooled_result(self):
        self.assertIs(self.reg.run("CHK020_ORPHAN_POOLED_RESULT",
                                   {"page_id": "p", "displayed_pooled_estimate": 0.87,
                                    "engine_can_pool": False}).verdict, Verdict.FAIL)
        self.assertIs(self.reg.run("CHK020_ORPHAN_POOLED_RESULT",
                                   {"page_id": "p", "displayed_pooled_estimate": 0.87,
                                    "engine_can_pool": None}).verdict, Verdict.INVALID)

    def test_md_exponentiated(self):
        r = self.reg.run("CHK021_MEASURE_SCALE_MISMATCH",
                         {"row_id": "r", "measure": "MD", "stored_scale": "natural",
                          "back_transform": "exp", "rendered_value": 0.0})
        self.assertIs(r.verdict, Verdict.FAIL)

    def test_ratio_from_percentage(self):
        self.assertIs(self.reg.run("CHK022_RATIO_FROM_PERCENTAGE",
                                   {"row_id": "MORDOR-I", "extracted_measure": "RR",
                                    "source_text": "Mortality was 13.5% lower "
                                                   "overall."}).verdict, Verdict.FAIL)
        self.assertIs(self.reg.run("CHK022_RATIO_FROM_PERCENTAGE",
                                   {"row_id": "x", "extracted_measure": "HR",
                                    "source_text": "the hazard ratio was 0.91 "
                                                   "(0.73-1.13)"}).verdict,
                      Verdict.PASS)

    def test_cross_agent_pooling_respects_a_declared_class(self):
        entries = [{"id": "a", "intervention": "empagliflozin"},
                   {"id": "b", "intervention": "dapagliflozin"}]
        self.assertIs(self.reg.run("CHK023_CROSS_AGENT_POOLING",
                                   {"pool_id": "p", "entries": entries}).verdict,
                      Verdict.FAIL)
        self.assertIs(self.reg.run("CHK023_CROSS_AGENT_POOLING",
                                   {"pool_id": "p", "entries": entries,
                                    "declared_class": "SGLT2 inhibitor"}).verdict,
                      Verdict.PASS)

    def test_false_nma_claim(self):
        self.assertIs(self.reg.run("CHK024_FALSE_METHOD_CLAIM",
                                   {"page_id": "p", "claimed_method": "NMA",
                                    "network_edges": [["A", "B"]]}).verdict,
                      Verdict.FAIL)

    def test_multi_surface_disagreement(self):
        r = self.reg.run("CHK025_MULTI_SURFACE_DISAGREEMENT",
                         {"claim_id": "c",
                          "surfaces": {"card": {"value": 0.87, "status": "withdrawn"},
                                       "table_row": {"value": 0.87,
                                                     "status": "live"}}})
        self.assertIs(r.verdict, Verdict.FAIL)

    def test_multi_surface_known_weakness_is_asserted_not_hidden(self):
        """FIXTURE_STATUS marks this negative WEAK. Here is the case it fails.

        A card rounded to 2 dp against a full-precision table row is a legitimate
        difference, and this check currently FIRES on it. Asserting the false
        positive keeps it visible; if someone fixes it, this test tells them.
        """
        r = self.reg.run("CHK025_MULTI_SURFACE_DISAGREEMENT",
                         {"claim_id": "rounded",
                          "surfaces": {"card": {"value": 0.87, "status": "live"},
                                       "table_row": {"value": 0.8712,
                                                     "status": "live"}}})
        self.assertIs(r.verdict, Verdict.FAIL,
                      "known false positive -- rounding tolerance not implemented")

    def test_fixture_status_is_declared_for_every_corpus_detector(self):
        from nafis_harness.probes_corpus import CORPUS_CHECKS, FIXTURE_STATUS
        for chk in CORPUS_CHECKS:
            with self.subTest(check=chk.check_id):
                self.assertIn(chk.check_id, FIXTURE_STATUS)
                st = FIXTURE_STATUS[chk.check_id]
                self.assertIn(st["negative_strength"],
                              ("STRONG", "MODERATE", "WEAK", "NONE"))
                self.assertTrue(st["note"].strip())

    def test_constructed_fixtures_are_labelled_as_constructed(self):
        """A constructed fixture masquerading as corpus material is the fig leaf
        that defeated Rule 5 v1. There is exactly one here and it says so."""
        from nafis_harness.probes_corpus import CORPUS_CHECKS
        constructed = [(c.check_id, f.name)
                       for c in CORPUS_CHECKS
                       for f in list(c.must_fire_on) + list(c.must_be_silent_on)
                       if "CONSTRUCTED" in f.provenance.upper()]
        self.assertEqual(constructed,
                         [("CHK019_INERT_ENGINE", "wired_page_shares_identifiers")],
                         "the set of constructed fixtures changed without the "
                         "fixture register being updated")

    def test_detectors_with_no_defensible_negative_are_named(self):
        """The list Mahmood said matters more than the other one."""
        from nafis_harness.probes_corpus import FIXTURE_STATUS
        none_ = sorted(k for k, v in FIXTURE_STATUS.items()
                       if v["negative_strength"] == "NONE")
        weak = sorted(k for k, v in FIXTURE_STATUS.items()
                      if v["negative_strength"] == "WEAK")
        self.assertEqual(none_, ["CHK019_INERT_ENGINE"])
        self.assertEqual(weak, ["CHK017_DUP1_BIT_EQUALITY",
                                "CHK025_MULTI_SURFACE_DISAGREEMENT"])


# =============================================================================
# 10. Build-path and rendering classes -- CHK026..CHK030, and CHK031 held out
# =============================================================================

class TestBuildDetectors(unittest.TestCase):

    def setUp(self):
        self.reg = build_registry()

    def test_arni_reason_on_a_converted_page_fires(self):
        from nafis_harness.probes_build import _ARNI_REASON
        r = self.reg.run("CHK026_WRONG_REASON_ABSENCE_PANEL",
                         {"page_id": "CONV_07", "page_provenance": "converted",
                          "absence_reason_id": "no-database-search",
                          "reason_text": _ARNI_REASON,
                          "reason_valid_for": ["authored-reconciliation"]})
        self.assertIs(r.verdict, Verdict.FAIL)

    def test_a_blank_absence_panel_is_invalid_not_a_defect(self):
        """'The blank makes no claim, this makes a false one.'

        A panel with no reason asserts nothing -- INVALID, which is neither a
        pass nor a defect. Collapsing the two would make the harness punish the
        honest empty panel and the lying one identically.
        """
        r = self.reg.run("CHK026_WRONG_REASON_ABSENCE_PANEL",
                         {"page_id": "P", "page_provenance": "converted",
                          "absence_reason_id": None})
        self.assertIs(r.verdict, Verdict.INVALID)

    def test_sentinel_matching_is_exact_token_not_word_based(self):
        """Real prose using uppercase status language must not fire."""
        from nafis_harness.probes_build import _SENTINELS
        r = self.reg.run("CHK027_SENTINEL_LEAK",
                         {"surface_id": "route-log",
                          "reader_text": "Status: NOT YET OBTAINED. The counts are "
                                         "not obtainable through any open mechanism.",
                          "sentinels": _SENTINELS})
        self.assertIs(r.verdict, Verdict.PASS)

    def test_sourced_card_beats_object_and_the_block_is_hard(self):
        r = self.reg.run("CHK028_DISQUALIFIED_REFERENT_PROMOTED",
                         {"claim_id": "DOAC_CANCER_VTE",
                          "card": {"measure": "HR", "value": 0.55,
                                   "source_citation": "publication-verified"},
                          "object": {"measure": "OR", "value": 0.7290},
                          "object_disqualified": True})
        self.assertIs(r.verdict, Verdict.FAIL)
        self.assertIn("HARD BLOCK", r.reason)

    def test_unsourced_card_conflict_is_invalid_not_a_promotion(self):
        r = self.reg.run("CHK028_DISQUALIFIED_REFERENT_PROMOTED",
                         {"claim_id": "x",
                          "card": {"measure": "HR", "value": 0.55},
                          "object": {"measure": "OR", "value": 0.73}})
        self.assertIs(r.verdict, Verdict.INVALID)

    # --- CHK029: the sign normaliser, and the false positive it must avoid ---

    def test_unicode_and_entity_minus_normalise_to_the_same_value(self):
        from nafis_harness.probes_build import normalise_signed_number as n
        for raw in ("&minus;71.31", "−71.31", "–71.31", "‒71.31",
                    "-71.31", "－71.31"):
            with self.subTest(raw=raw):
                self.assertAlmostEqual(n(raw), -71.31, places=9)

    def test_an_en_dash_range_is_not_a_negative_number(self):
        """The false positive this check must avoid.

        '0.73-1.13' with an en-dash is an interval. A normaliser that rewrote
        every dash-like character would turn it into -1.13 and silently invent a
        negative bound.
        """
        from nafis_harness.probes_build import normalise_signed_number as n
        self.assertIsNone(n("0.73–1.13"))
        self.assertIsNone(n("0.73-1.13"))
        r = self.reg.run("CHK029_SIGN_NORMALISATION",
                         {"field_id": "ci", "raw": "0.73–1.13",
                          "naive_value": None})
        self.assertIs(r.verdict, Verdict.PASS)

    def test_a_range_parsed_as_a_scalar_fires(self):
        r = self.reg.run("CHK029_SIGN_NORMALISATION",
                         {"field_id": "ci", "raw": "0.73–1.13",
                          "naive_value": -1.13})
        self.assertIs(r.verdict, Verdict.FAIL)

    def test_mis_signed_parse_is_named_as_inverted(self):
        r = self.reg.run("CHK029_SIGN_NORMALISATION",
                         {"field_id": "md", "raw": "&minus;71.31",
                          "naive_value": 71.31})
        self.assertIs(r.verdict, Verdict.FAIL)
        self.assertTrue(r.evidence["sign_inverted"])

    def test_unconditioned_rationale_fires(self):
        r = self.reg.run("CHK030_BUILD_MODE_BLIND_TEXT",
                         {"string_id": "s", "text": "because X",
                          "asserts_rationale": True, "valid_for_paths": None,
                          "build_path": "convert"})
        self.assertIs(r.verdict, Verdict.FAIL)

    # --- CHK031: the admission rule, applied to me --------------------------

    def test_search_recall_is_inadmissible_and_stays_out_of_the_registry(self):
        """No real positive exists: confirmed breadth failures in our corpus = 0.

        Registering it on a constructed positive would make it a rule that has
        never fired on anything real -- M11 -- which is the mechanism
        Registry.register exists to refuse. This test asserts the refusal.
        """
        from nafis_harness.probes_build import CHK031_UNREGISTERED
        from nafis_harness import Registry, InadmissibleDetector
        self.assertNotIn("CHK031_SEARCH_RECALL", self.reg)
        with self.assertRaises(InadmissibleDetector) as ctx:
            Registry().register(CHK031_UNREGISTERED)
        self.assertIn("never been demonstrated firing", str(ctx.exception))

    def test_search_recall_still_works_when_called_directly(self):
        """Held out of the registry is not the same as broken."""
        from nafis_harness.probes_build import search_recall
        miss = search_recall({"review_id": "R",
                              "included_study_ids": ["A", "B"],
                              "retrieved_ids": ["A"]})
        self.assertIs(miss.verdict, Verdict.FAIL)
        not_run = search_recall({"review_id": "R",
                                 "included_study_ids": ["A"],
                                 "retrieved_ids": None})
        self.assertIs(not_run.verdict, Verdict.INVALID)
        self.assertIn("Not re-running it is not the same as it passing",
                      not_run.reason)

    def test_build_fixture_status_names_the_weak_and_absent_negatives(self):
        from nafis_harness.probes_build import FIXTURE_STATUS as BS
        self.assertIn("NO POSITIVE AT ALL", BS["CHK031_SEARCH_RECALL"]["note"])
        self.assertEqual(BS["CHK030_BUILD_MODE_BLIND_TEXT"]["negative_strength"],
                         "WEAK")
        self.assertIn("SAME INCIDENT",
                      BS["CHK030_BUILD_MODE_BLIND_TEXT"]["note"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
