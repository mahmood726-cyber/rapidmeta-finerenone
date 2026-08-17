"""Permanent mutation test — planted defects, three caller encodings, two implementations.

WHY THIS EXISTS, AND WHY IT IS NOT test_harness.py
--------------------------------------------------
34/34 unit tests passed while the harness scored 2/7 on planted errors. The unit
tests were written by whoever wrote the detectors, and they tested the
propositions the detectors state about themselves. Mutation testing asks a
different question: *if the world were wrong in a specific way, would this thing
notice?* Only the second question has an answer the author cannot arrange.

So: no change to `nafis_harness` is accepted on unit tests alone. This module
runs on every `python -m unittest`, and `python -m nafis_harness` runs it as
arm 4.

PROVENANCE, STATED PLAINLY
--------------------------
⚠️ **This suite is author-inherited and is therefore WEAKER EVIDENCE than the
benchmark lane's `mutation_test_current_harness.py`, which I could not reach.**
The benchmark lane's outputs folder is a sibling session path I do not have, and
requests above the `local_<id>\\outputs` level are refused. I reconstructed these
arms from the reported behaviour (7/7, 2/7, 2/7; five value mutants killed under
a keyed referent and passed under a flat number-bag). Reconstructing a test to
grade my own fixes is exactly the authorship blind spot TAXONOMY.md §4.1 names.
**Treat the numbers below as provisional until the benchmark lane's script is
run against this harness.** That run is the real acceptance.

SCORING — three-way, because two-way scoring hides the whole point
-----------------------------------------------------------------
    KILLED      verdict FAIL     the defect was identified
    NOT-BANKED  verdict INVALID  the detector refused to certify: the defect was
                                 not identified, but neither was it banked
    SURVIVED    verdict PASS     the planted defect was certified as clean

A binary killed/survived score would count INVALID as a miss and read a refusal
to answer as a failure. That is the same collapse the harness exists to prevent,
one level up. **The acceptance criterion is SURVIVED == 0 in every arm.**
"""

from __future__ import annotations

import copy
import unittest
from typing import Any, Mapping

from nafis_harness.probes import build_registry
from nafis_harness.verdict import Verdict, make_fail, make_invalid, make_pass

# =============================================================================
# The subject: TWILIGHT / NCT02270242, DEFECT-01
# =============================================================================
# Registry truth: participantFlow STARTED 3555 / 3564. Location A matches it
# exactly; Location B carries 4614 / 4603 and 172 / 168 and reproduces its own
# hazard ratio of 0.99 to three decimals.

TRUE_ROW = {"tN": 3555, "cN": 3564, "tE": 34, "cE": 45, "hr": 0.99}

REFERENT_LOCATORS = {
    "tN": "participantFlow.STARTED, ticagrelor+placebo",
    "cN": "participantFlow.STARTED, ticagrelor+aspirin",
    "tE": "adverseEvents.deathsNumAffected, ticagrelor+placebo, 1y",
    "cE": "adverseEvents.deathsNumAffected, ticagrelor+aspirin, 1y",
    "hr": "outcomeMeasures.keySecondary, hazard ratio",
}


# --- the seven planted defects ------------------------------------------------
# Five value mutants (the extraction disagrees with the registry) and two
# structural mutants (the extraction is unauditable rather than wrong).

MUTANTS = {
    "MUT-01_tN_inflated":   {"kind": "value",      "row": {"tN": 4614}},
    "MUT-02_cN_inflated":   {"kind": "value",      "row": {"cN": 4603}},
    "MUT-03_tE_swapped":    {"kind": "value",      "row": {"tE": 172}},
    "MUT-04_cE_swapped":    {"kind": "value",      "row": {"cE": 168}},
    "MUT-05_hr_altered":    {"kind": "value",      "row": {"hr": 0.87}},
    "MUT-06_referent_gone": {"kind": "structural", "strip_referent": True},
    "MUT-07_unsourced_key": {"kind": "structural", "row": {"tE2": 9999}},
}


# --- the three caller encodings ----------------------------------------------

def _arm_a(row):
    """KEYED + PROVENANCED — the interface the fixed detector requires."""
    return {
        "referent_name": "ClinicalTrials.gov NCT02270242 participant flow",
        "referent_document_id": "NCT02270242",
        "row": dict(row),
        "external_referent": {k: {"value": v, "locator": REFERENT_LOCATORS[k]}
                              for k, v in TRUE_ROW.items()},
    }


def _arm_b(row):
    """FLAT NUMBER-BAG — the encoding validate_v2.py used, and the historical failure.

    NOTE THE CRITICAL DETAIL, and it is the whole mechanism: the bag is populated
    from THE EXTRACTION, not from the registry. That is what "numbers echoed out
    of a bag" means. A bag built from registry values would still catch value
    mutants by accident; a bag echoing the row agrees with the row by
    construction, and the comparison is between a number and itself.

    This is M4 at the interface: the caller hands the detector a second copy of
    the extraction and calls it an external referent.
    """
    return {
        "referent_name": "ClinicalTrials.gov NCT02270242 participant flow",
        "referent_document_id": "NCT02270242",
        "row": dict(row),
        "external_referent": dict(row),          # echoed, not sourced
    }


def _arm_c(row):
    """PARTIAL — keyed and provenanced, but covering only two of the five keys.

    The silent-skip encoding: the referent is honest about what it holds, and the
    old comparison loop simply skipped everything it did not cover.
    """
    return {
        "referent_name": "ClinicalTrials.gov NCT02270242 participant flow",
        "referent_document_id": "NCT02270242",
        "row": dict(row),
        "external_referent": {k: {"value": TRUE_ROW[k], "locator": REFERENT_LOCATORS[k]}
                              for k in ("tN", "cN")},
    }


ARMS = {"A_keyed_provenanced": _arm_a,
        "B_flat_number_bag": _arm_b,
        "C_partial_referent": _arm_c}


def _apply(mutant: Mapping[str, Any], arm_fn):
    row = dict(TRUE_ROW)
    row.update(mutant.get("row", {}))
    payload = arm_fn(row)
    if mutant.get("strip_referent"):
        payload["external_referent"] = None
    return payload


# =============================================================================
# The legacy implementation, preserved verbatim so the diff is measurable
# =============================================================================

def legacy_external_referent(p: Mapping[str, Any]):
    """`_external_referent` as it stood before the mutation findings.

    Kept because a fix with no before-number is a claim, not a measurement.
    """
    cid, inst = "CHK005_EXTERNAL_REFERENT", "registry-crosscheck"
    ref = p.get("external_referent")
    if not ref:
        return make_invalid(cid, inst, "no external referent, no verdict.")
    row = dict(p.get("row", {}))

    def unwrap(v):
        # Legacy predates provenanced cells. Unwrapping them keeps the
        # comparison about the DEFECTS UNDER TEST (no provenance requirement,
        # silent skip) rather than about a type mismatch that would kill every
        # mutant for the wrong reason and flatter the baseline.
        return v["value"] if isinstance(v, Mapping) and "value" in v else v

    # the two defects, both visible here:
    #   - the referent's shape is never inspected, so a bag echoing the row is
    #     indistinguishable from a sourced extraction
    #   - `if k in row` silently skips anything the referent does not cover
    disagreements = {k: {"row": row.get(k), "referent": unwrap(v)}
                     for k, v in ref.items()
                     if k in row and row.get(k) != unwrap(v)}
    if disagreements:
        return make_fail(cid, inst,
                         f"row disagrees on {sorted(disagreements)}",
                         observed=str(disagreements), locator="legacy",
                         opposite_would_be="agreement")
    return make_pass(cid, inst, observed="row agrees", locator="legacy",
                     opposite_would_be="a disagreement on any keyed field")


# =============================================================================
# Runner
# =============================================================================

KILLED, NOT_BANKED, SURVIVED = "KILLED", "NOT-BANKED", "SURVIVED"


def _score(verdict: Verdict) -> str:
    return {Verdict.FAIL: KILLED, Verdict.INVALID: NOT_BANKED,
            Verdict.PASS: SURVIVED}[verdict]


def run_mutation_matrix() -> dict:
    """Returns {impl: {arm: {mutant: score}}}. Deterministic, CPU only, no I/O."""
    reg = build_registry()
    current = lambda payload: reg.run("CHK005_EXTERNAL_REFERENT", payload)

    out: dict = {}
    for impl_name, impl in (("legacy", legacy_external_referent),
                            ("current", current)):
        out[impl_name] = {}
        for arm_name, arm_fn in ARMS.items():
            out[impl_name][arm_name] = {}
            for mut_name, mut in MUTANTS.items():
                payload = _apply(mut, arm_fn)
                out[impl_name][arm_name][mut_name] = _score(impl(payload).verdict)
    return out


def summarise(matrix: dict) -> dict:
    s: dict = {}
    for impl, arms in matrix.items():
        s[impl] = {}
        for arm, muts in arms.items():
            vals = list(muts.values())
            s[impl][arm] = {KILLED: vals.count(KILLED),
                            NOT_BANKED: vals.count(NOT_BANKED),
                            SURVIVED: vals.count(SURVIVED),
                            "n": len(vals)}
    return s


def format_report(matrix: dict) -> str:
    s = summarise(matrix)
    lines = ["", "=" * 78,
             "MUTATION MATRIX -- 7 planted defects x 3 caller encodings x 2 implementations",
             "=" * 78,
             "  KILLED = FAIL (identified) | NOT-BANKED = INVALID (refused) | "
             "SURVIVED = PASS (certified)",
             ""]
    for impl in ("legacy", "current"):
        lines.append(f"--- {impl.upper()} ---")
        lines.append(f"  {'arm':26s} {'killed':>7s} {'not-banked':>11s} "
                     f"{'SURVIVED':>9s}")
        for arm in ARMS:
            c = s[impl][arm]
            lines.append(f"  {arm:26s} {c[KILLED]:>5d}/7 {c[NOT_BANKED]:>10d} "
                         f"{c[SURVIVED]:>9d}")
        lines.append("")
    lines.append("Per-mutant detail (current):")
    for arm in ARMS:
        lines.append(f"  {arm}:")
        for mut, sc in matrix["current"][arm].items():
            flag = "  <-- SURVIVED" if sc == SURVIVED else ""
            lines.append(f"    {mut:26s} {sc}{flag}")
    total_survived = sum(s["current"][a][SURVIVED] for a in ARMS)
    lines.append("")
    lines.append(f"ACCEPTANCE (SURVIVED == 0 in every arm): "
                 f"{'PASS' if total_survived == 0 else 'FAIL'} "
                 f"({total_survived} survivor(s))")
    lines.append("=" * 78)
    return "\n".join(lines)


# =============================================================================
# Permanent test case -- runs on every `python -m unittest`
# =============================================================================

class TestMutationMatrix(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.matrix = run_mutation_matrix()
        cls.summary = summarise(cls.matrix)

    def test_no_planted_defect_survives_in_any_arm(self):
        """THE acceptance criterion. A survivor is a defect certified as clean."""
        survivors = {(arm, mut)
                     for arm, muts in self.matrix["current"].items()
                     for mut, sc in muts.items() if sc == SURVIVED}
        self.assertEqual(survivors, set(),
                         f"planted defects certified as clean: {sorted(survivors)}")

    def test_arm_b_improved_over_legacy(self):
        """The criterion Mahmood named: Arm B must rise.

        Legacy certified every value mutant when handed a bag echoing the row.
        Current must certify none of them.

        The assertion is on the DIRECTION and on current==0, deliberately not on
        an exact legacy count. The benchmark lane reported 2/7 for this arm; my
        reconstructed mutant set gives a different figure because it is a
        different set. Asserting their number against my set would be
        manufacturing agreement with a report I cannot read -- M4, in a test.
        """
        legacy_b = self.summary["legacy"]["B_flat_number_bag"]
        current_b = self.summary["current"]["B_flat_number_bag"]
        self.assertGreaterEqual(legacy_b[SURVIVED], 5,
                                "the legacy baseline must reproduce the hole: a bag "
                                "echoing the row certifies the value mutants")
        self.assertEqual(current_b[SURVIVED], 0)
        self.assertGreater(current_b[KILLED] + current_b[NOT_BANKED],
                           legacy_b[KILLED] + legacy_b[NOT_BANKED])

    def test_arm_c_partial_referent_no_longer_silently_skips(self):
        """Legacy skipped the three uncovered keys; current refuses the run."""
        legacy_c = self.summary["legacy"]["C_partial_referent"]
        current_c = self.summary["current"]["C_partial_referent"]
        self.assertGreater(legacy_c[SURVIVED], 0)
        self.assertEqual(current_c[SURVIVED], 0)

    def test_arm_a_did_not_regress(self):
        """Necessary but NOT the acceptance criterion -- Arm A was already 7/7."""
        a = self.summary["current"]["A_keyed_provenanced"]
        self.assertEqual(a[SURVIVED], 0)
        self.assertGreaterEqual(a[KILLED], 5, "the five value mutants must be killed")

    def test_scoring_is_three_way_not_binary(self):
        """Guard on the guard: if INVALID ever collapses into a pass or a kill,
        this suite stops measuring what it claims to measure."""
        self.assertEqual(_score(Verdict.FAIL), KILLED)
        self.assertEqual(_score(Verdict.INVALID), NOT_BANKED)
        self.assertEqual(_score(Verdict.PASS), SURVIVED)
        self.assertEqual(len({KILLED, NOT_BANKED, SURVIVED}), 3)


if __name__ == "__main__":
    print(format_report(run_mutation_matrix()))
