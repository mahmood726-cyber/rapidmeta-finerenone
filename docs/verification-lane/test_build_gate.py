"""Proof that the wiring blocks -- by replaying real past defects through it.

    "wiring that has never blocked anything is a library with extra steps"

gate_integrity.py sets the bar and this file meets it:

    "A synthetic failing input proves a detector CAN fire. It does not prove the
     detector DISCRIMINATES: a rule that fires on everything also passes that
     test. Where a real past defect exists, replay it, and require the detector
     to fire on it AND stay silent on the parts that were genuinely fine."

So each replay below carries the defect AND several things that were fine, and
the test asserts both: the gate exits 1, and the clean artefact built from the
same shape exits 0.
"""

from __future__ import annotations

import json
import os
import tempfile
import unittest

import harness_gate
from nafis_harness.artefact import ARTEFACT_DECIDABLE, RETRIEVAL_SCOPED


def _run(artefacts: list[dict]) -> int:
    """Write artefacts to temp JSON and run the gate exactly as a hook would."""
    with tempfile.TemporaryDirectory() as td:
        paths = []
        for i, a in enumerate(artefacts):
            p = os.path.join(td, f"artefact_{i}.json")
            with open(p, "w", encoding="utf-8") as fh:
                json.dump(a, fh)
            paths.append(p)
        return harness_gate.main(paths + ["--quiet"])


# --- the clean artefact: every field populated, nothing wrong -----------------
# Built from values read verbatim from the corpus so the negative is real:
# classes[29] SGLT2 CVOT carries EMPA-REG, DECLARE-TIMI 58 and VERTIS-CV as its
# own rows, pooled under a declared class, on one outcome.
CLEAN = {
    "page_id": "SGLT2_CVOT_CLEAN",
    "page_provenance": "authored-reconciliation",
    "build_path": "author",
    "engine_trial_ids": ["NCT01131676", "NCT01730534"],
    "data_trial_ids": ["NCT01131676", "NCT01730534", "NCT01986881"],
    "engine_can_pool": True,
    "displayed_pooled_estimate": 0.87,
    "reader_text": "All-cause mortality, pooled across three SGLT2 outcome trials.",
    "claimed_method": "pairwise",
    "pools": [{
        "pool_id": "sglt2-acm", "headline_k": 2,
        "headline_outcome": "all_cause_mortality",
        "declared_class": "SGLT2 inhibitor",
        "panel_rows": [
            {"id": "NCT01131676", "outcome": "all_cause_mortality",
             "population": "randomised", "window": "full"},
            {"id": "NCT01730534", "outcome": "all_cause_mortality",
             "population": "randomised", "window": "full"}],
        "entries": [
            {"id": "EMPA-REG", "estimate": -0.3285, "variance": 0.0041,
             "measure": "HR", "direction_of_benefit": "efficacy",
             "intervention": "empagliflozin"},
            {"id": "DECLARE-TIMI 58", "estimate": -0.0619, "variance": 0.0038,
             "measure": "HR", "direction_of_benefit": "efficacy",
             "intervention": "dapagliflozin"}],
        "pooled_estimate": -0.1943,
    }],
    "rows": [{
        "row_id": "MITRAL_FUNCMR", "estimate": 0.6677, "ci_low": 0.4009,
        "ci_high": 1.1120, "events_t": 45, "n_t": 150, "events_c": 60,
        "n_c": 145, "measure": "OR", "stored_scale": "log",
        "back_transform": "exp"}],
    "numeric_fields": [{"field_id": "md", "raw": "-71.31", "naive_value": -71.31}],
}


def _clean() -> dict:
    return json.loads(json.dumps(CLEAN))


class TestGateBlocksOnRealPastDefects(unittest.TestCase):

    def test_the_clean_artefact_passes(self):
        """Required first. A gate that fails on everything also fails on defects."""
        self.assertEqual(_run([_clean()]), 0)

    def test_twilight_composite_in_a_mortality_pool_blocks(self):
        """DEFECT-01 escalation: 'a composite of death, MI and stroke
        masquerading as all-cause mortality', pooled at k=2."""
        a = _clean()
        a["page_id"] = "P2Y12_MONO"
        a["pools"][0]["panel_rows"][0] = {
            "id": "NCT02270242", "outcome": "death_mi_stroke_composite",
            "population": "per_protocol", "window": "12m"}
        self.assertEqual(_run([a]), 1)

    def test_arni_absence_reason_on_a_converted_page_blocks(self):
        """Would have shipped on 28 pages."""
        a = _clean()
        a["page_provenance"] = "converted"
        a["absence_panels"] = [{
            "absence_reason_id": "no-database-search",
            "reason_text": "the included set was reconciled against published "
                           "syntheses rather than produced by a database search",
            "reason_valid_for": ["authored-reconciliation"]}]
        self.assertEqual(_run([a]), 1)

    def test_unicode_minus_blocks(self):
        """&minus;71.31 read as +71.31 -- 2 of 7 reported conflicts."""
        a = _clean()
        a["numeric_fields"] = [{"field_id": "md", "raw": "&minus;71.31",
                                "naive_value": 71.31}]
        self.assertEqual(_run([a]), 1)

    def test_inert_engine_blocks(self):
        """612/651 pages; corroborated at 93.6-96.1% in 786 scanned."""
        a = _clean()
        a["engine_trial_ids"] = ["NCT01035255", "NCT01920711"]
        self.assertEqual(_run([a]), 1)

    def test_sentinel_leak_blocks(self):
        a = _clean()
        a["reader_text"] = "Per-arm counts: NOT RECOVERABLE FROM THE PAGE."
        self.assertEqual(_run([a]), 1)

    def test_bit_identical_duplicate_blocks(self):
        """AZITHROMYCIN: both entries carrying -0.15082288973458366."""
        a = _clean()
        v = -0.15082288973458366
        a["pools"][0]["entries"][0]["estimate"] = v
        a["pools"][0]["entries"][1]["estimate"] = v
        a["pools"][0]["pooled_estimate"] = v
        self.assertEqual(_run([a]), 1)

    def test_hazard_ratio_pooled_with_odds_ratio_blocks(self):
        """MITRAL: COAPT's HR pooled with MITRA-FR's OR."""
        a = _clean()
        a["pools"][0]["entries"][1]["measure"] = "OR"
        self.assertEqual(_run([a]), 1)

    def test_cross_agent_pool_without_a_declared_class_blocks(self):
        a = _clean()
        a["pools"][0].pop("declared_class")
        self.assertEqual(_run([a]), 1)

    def test_md_exponentiated_blocks(self):
        """The back-transform bug that turned MD -54 into 0.0000."""
        a = _clean()
        a["rows"][0].update({"measure": "MD", "stored_scale": "natural",
                             "back_transform": "exp"})
        self.assertEqual(_run([a]), 1)

    def test_precision_sample_mismatch_blocks(self):
        """MAVACAMTEN: claimed OR 6.67 (2.09-21.30) on 45/123 vs 22/128."""
        a = _clean()
        a["rows"][0].update({"row_id": "MAVACAMTEN_HCM", "estimate": 6.67,
                             "ci_low": 2.09, "ci_high": 21.30,
                             "events_t": 45, "n_t": 123, "events_c": 22,
                             "n_c": 128})
        self.assertEqual(_run([a]), 1)

    def test_orphan_pooled_result_blocks(self):
        a = _clean()
        a["engine_can_pool"] = False
        a["engine_block_reason"] = "no shared trial ids"
        self.assertEqual(_run([a]), 1)

    def test_false_nma_claim_blocks(self):
        a = _clean()
        a["claimed_method"] = "NMA"
        a["network_edges"] = [["A", "B"]]
        self.assertEqual(_run([a]), 1)


class TestGateHonesty(unittest.TestCase):

    def test_no_artefacts_is_a_scoped_pass_not_a_clean_bill(self):
        self.assertEqual(harness_gate.main(["--quiet"]), 0)

    def test_a_missing_artefact_file_is_exit_2_not_0(self):
        self.assertEqual(harness_gate.main(["/nonexistent/artefact.json"]), 2)

    def test_partition_is_disjoint_and_published(self):
        """A detector in neither list would be silently uncovered."""
        from nafis_harness import build_registry
        reg = build_registry()
        both = set(ARTEFACT_DECIDABLE) & set(RETRIEVAL_SCOPED)
        self.assertEqual(both, set())
        covered = set(ARTEFACT_DECIDABLE) | set(RETRIEVAL_SCOPED)
        self.assertEqual(covered, set(reg.ids()),
                         "every registered detector must be assigned to exactly "
                         "one wiring point")

    def test_gate_reports_what_it_does_not_run(self):
        """Silence from a retrieval-scoped detector must never read as coverage."""
        import io
        import contextlib
        buf = io.StringIO()
        with tempfile.TemporaryDirectory() as td:
            p = os.path.join(td, "a.json")
            with open(p, "w", encoding="utf-8") as fh:
                json.dump(_clean(), fh)
            with contextlib.redirect_stdout(buf):
                harness_gate.main([p])
        out = buf.getvalue()
        self.assertIn("NOT RUN HERE", out)
        self.assertIn("Silence from", out)


if __name__ == "__main__":
    unittest.main(verbosity=2)
