r"""Gate 21 must be able to REFUSE, and these tests fire against the real module.

WHY THIS FILE EXISTS. Gate 21 now reports PASS over a clean corpus with an EMPTY freeze
list. A gate that has only ever been observed to pass is not known to be able to fail, and
"it passed" is exactly what a broken gate says too.

    test_gate_refuses_a_promised_unreported_harm   runs THE REAL gate over a SYNTHETIC
        corpus built to hold one promised-and-unreported harm, and requires exit FAIL.

    test_gate_passes_a_corpus_whose_only_topic_reports_its_harm   the same machinery with
        the harm present, requiring PASS -- without it the test above shows only that the
        gate is red, not that it discriminates.

    test_ratchet_admits_a_new_instance_rather_than_swallowing_it   a freeze naming OTHER
        topics must not excuse this one.

    test_gate_passes_over_the_real_corpus_as_shipped   and it asserts the freeze is EMPTY
        first, so it cannot pass on frozen findings.

    test_the_two_fixed_pages_report_major_bleeding   pins the repair forward: both pages
        must decide REPORTED, and every per-trial row must carry a window and a population.

    test_the_adopt_row_is_the_posted_counts_and_its_interval_includes_one   pins the number
        the task brief got wrong -- 2.5259 (0.9813-6.5018), not 2.58 (1.02-7.24).

    test_affirmed_poolability_is_not_a_refusal   the regression test for the defect this
        gate shipped with: `poolable: True` beside a long `poolable_reason` read as a
        reasoned refusal, and the gate reported 0 findings where there were 2.

⛔ THE CONTROLS ARE SYNTHETIC AND THE REGRESSIONS ARE REAL, WHICH IS THE RIGHT WAY ROUND.
   An earlier draft made "the gate must flag apixaban-vte-prophylaxis" its negative test.
   That control retired itself the moment the page was fixed -- in this same lane, hours
   later -- and would then have read as a regression. Controls are built in memory;
   assertions about the corpus assert the REPAIRED state, which does not retire.

⛔ NO MOCKS. Every test either builds a real object on disk and runs the real gate over it,
   or loads the real objects from ssot/. A test that asserted on a mock would verify it.
"""
from __future__ import annotations

import io
import json
import os
import shutil
import sys
import tempfile

import pytest

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, "gates"))
sys.path.insert(0, os.path.join(REPO, "scripts"))

# ⛔ BEFORE importing _harness. It reassigns sys.stdout at module level unless this is
# already "1", and a module-level stdout reassignment destroys pytest's capture state --
# the whole session dies with "I/O operation on closed file" and reports NO TESTS RAN,
# which reads as a clean collection rather than as a suite that never executed. The
# harness sets this variable itself to avoid double-wrapping; setting it here uses its
# own affordance instead of editing shared code that other gates depend on.
os.environ["_GATE_WRAPPED"] = "1"

import _harness as H                                                        # noqa: E402
import gate21_harms_promised_not_reported as G                              # noqa: E402

FREEZE_PATH = os.path.join(REPO, "gates", G.FREEZE)
TODAYS_FINDINGS = ["apixaban-vte-prophylaxis", "apixaban-vte-treatment"]


def _load(app_id):
    p = os.path.join(REPO, "ssot", app_id, app_id + ".json")
    with io.open(p, encoding="utf-8") as fh:
        return json.load(fh)


class _freeze_containing:
    """Run the real gate with a chosen freeze list, and put the real one back.

    The original file is COPIED to a temp path and restored in `finally`, so an assertion
    failure cannot leave the repository's freeze file rewritten. A test that can corrupt
    the artefact it is testing is worse than no test.
    """

    def __init__(self, keys):
        self.keys = keys

    def __enter__(self):
        self.backup = None
        if os.path.exists(FREEZE_PATH):
            self.backup = tempfile.mktemp(prefix="__control_freeze_")
            shutil.copy2(FREEZE_PATH, self.backup)
            with io.open(FREEZE_PATH, encoding="utf-8") as fh:
                doc = json.load(fh)
        else:
            doc = {"frozen_utc": "2026-09-03", "what": "test", "escalated_to": "test"}
        doc["keys"] = list(self.keys)
        doc["count"] = len(self.keys)
        with io.open(FREEZE_PATH, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(json.dumps(doc, indent=1))
        return self

    def __exit__(self, *exc):
        if self.backup:
            shutil.copy2(self.backup, FREEZE_PATH)
            os.remove(self.backup)
        elif os.path.exists(FREEZE_PATH):
            os.remove(FREEZE_PATH)
        return False


class _synthetic_corpus:
    """A whole temporary repository, which the REAL gate is pointed at.

    ⛔ WHY NOT "the gate must flag apixaban-vte-prophylaxis". Because that page no longer
    holds the defect -- this lane published its bleeding outcome on 2026-09-03 -- and A
    TEST ANCHORED TO A LIVE DEFECT RETIRES ITSELF AT THE MOMENT OF SUCCESS. The first
    draft of this file did exactly that, in the same commit as a gate docstring warning
    against it, which is why the gate's own probes were already in memory and why these
    are now too.

    So the negative test builds its own corpus: one topic whose PICO names bleeding, plus
    the adjudication row that makes it a promise. The real `G.main()` runs over it and
    must refuse. This holds forever, on any corpus, and no page fix can make it pass.
    """

    def __init__(self, include_defect):
        self.include_defect = include_defect

    @staticmethod
    def _topic(reports_the_harm):
        outcomes = [{"id": "eff", "name": "efficacy", "definition": "efficacy"}]
        by_outcome = {"eff": {"k": 2}}
        if reports_the_harm:
            outcomes.append({"id": "bleed", "name": "major bleeding",
                             "definition": "major bleeding"})
            by_outcome["bleed"] = {"k": 2}
        return {"question": "does it work, and what about major bleeding?",
                "outcomes": outcomes, "results": {"by_outcome": by_outcome}}

    def __enter__(self):
        self.tmp = tempfile.mkdtemp(prefix="__control_gate21_")
        os.makedirs(os.path.join(self.tmp, "gates"))
        # ALWAYS a known-negative in the corpus. The harness refuses `control(0, 0)` --
        # "a control with no negatives measures nothing" -- and it is right to: a corpus
        # consisting only of the defect cannot show that the gate DISCRIMINATES, only
        # that it fires. The clean topic is what makes the FAIL below meaningful.
        plan = [("__control_reports_the_harm", True, "NAMED_AND_SYNTHESISED")]
        if self.include_defect:
            plan.append(("__control_promises_bleeding", False, "NAMED_AND_ABSENT"))
        rows = []
        for topic, reports, disposition in plan:
            os.makedirs(os.path.join(self.tmp, "ssot", topic))
            obj = dict(self._topic(reports), app_id=topic)
            with io.open(os.path.join(self.tmp, "ssot", topic, topic + ".json"), "w",
                         encoding="utf-8", newline="\n") as fh:
                fh.write(json.dumps(obj, indent=1))
            rows.append({"app_id": topic, "disposition": disposition,
                         "quote": "and what about major bleeding?",
                         "reason": "synthetic control"})
        with io.open(os.path.join(self.tmp, "gates", "HARMS_PICO_ADJUDICATION.json"), "w",
                     encoding="utf-8", newline="\n") as fh:
            fh.write(json.dumps({"rows": rows}, indent=1))
        # AN EMPTY FREEZE, WRITTEN DELIBERATELY. H.ratchet FREEZES ON FIRST SIGHT when no
        # freeze file exists -- "FROZEN for the first time at 1 known findings" -- and
        # returns no NEW keys, so the gate would PASS on a corpus built to make it fail.
        # That is correct behaviour for a first run and it makes the absence of this file
        # a silent way to defeat the negative test.
        with io.open(os.path.join(self.tmp, "gates", G.FREEZE), "w",
                     encoding="utf-8", newline="\n") as fh:
            fh.write(json.dumps({"frozen_utc": "2026-09-03",
                                 "what": "synthetic control corpus",
                                 "escalated_to": "n/a", "count": 0, "keys": []}, indent=1))
        self.real_repo_root = H.repo_root
        H.repo_root = lambda: self.tmp
        return self

    def __exit__(self, *exc):
        H.repo_root = self.real_repo_root
        shutil.rmtree(self.tmp, ignore_errors=True)
        return False


def test_gate_refuses_a_promised_unreported_harm():
    """THE NEGATIVE TEST. The real gate, over a corpus built to hold exactly one
    promised-and-unreported harm, must return FAIL."""
    with _synthetic_corpus(include_defect=True):
        rc = G.main([])
    assert rc == H.FAIL, (
        "gate 21 returned %s over a corpus holding one topic whose PICO names major "
        "bleeding and whose results carry no harm outcome. A gate that cannot refuse is "
        "not a gate." % H.VERDICT_NAME[rc])


def test_gate_passes_a_corpus_whose_only_topic_reports_its_harm():
    """And it must PASS on the clean topic ALONE -- otherwise the test above shows only
    that the gate is red, not that it discriminates."""
    with _synthetic_corpus(include_defect=False):
        rc = G.main([])
    assert rc == H.PASS, (
        "gate 21 returned %s over a corpus whose only topic names a harm AND reports "
        "one. It is accusing a clean page." % H.VERDICT_NAME[rc])


def test_ratchet_admits_a_new_instance_rather_than_swallowing_it():
    """A freeze file naming OTHER topics must not excuse this one.

    A ratchet that froze a CLASS rather than its named members would pass any corpus
    forever, which is the failure mode a ratchet is most likely to have.
    """
    with _synthetic_corpus(include_defect=True) as c:
        with io.open(os.path.join(c.tmp, "gates", G.FREEZE), "w",
                     encoding="utf-8", newline="\n") as fh:
            fh.write(json.dumps({"frozen_utc": "2026-09-03", "what": "t",
                                 "escalated_to": "t", "count": 1,
                                 "keys": ["some-unrelated-topic"]}, indent=1))
        rc = G.main([])
    assert rc == H.FAIL, (
        "with an unrelated topic frozen, gate 21 returned %s on a genuinely new "
        "instance." % H.VERDICT_NAME[rc])


def test_gate_passes_over_the_real_corpus_as_shipped():
    """The corpus itself, with the freeze at ZERO keys.

    Until 2026-09-03 this could only pass because two findings were frozen by name. They
    are now fixed and the freeze holds nothing, so this assertion means what it appears
    to mean.
    """
    with io.open(FREEZE_PATH, encoding="utf-8") as fh:
        frozen = json.load(fh)["keys"]
    assert frozen == [], (
        "the freeze file still names %s. This test asserts a CLEAN corpus and it must "
        "not be allowed to pass on frozen findings." % frozen)
    rc = G.main([])
    assert rc == H.PASS, (
        "gate 21 returned %s over the real corpus with an empty freeze. A NEW finding has "
        "appeared -- read the output, it is named." % H.VERDICT_NAME[rc])


@pytest.mark.parametrize("app_id", ["apixaban-vte-prophylaxis", "apixaban-vte-treatment"])
def test_the_two_fixed_pages_report_major_bleeding(app_id):
    """The fix, pinned forward. Not a control -- a regression test.

    This does NOT retire on success, because it asserts the REPAIRED state. If either
    page loses its bleeding outcome this fails, which is what it is for.
    """
    obj = _load(app_id)
    verdict, where = G.decide(obj, "NAMED_AND_ABSENT")
    assert verdict == "REPORTED", (
        "%s decided %s. Its PICO names major bleeding; results.by_outcome must carry it."
        % (app_id, verdict))
    assert any("major_bleeding" in w for w in where), where
    rows = obj["results"]["by_outcome"]["major_bleeding"]["per_trial"]
    for r in rows:
        assert r.get("ascertainment_window"), "%s %s has no window" % (app_id, r["nct"])
        assert r.get("population") is not None, "%s %s has no population" % (app_id, r["nct"])


def test_the_adopt_row_is_the_posted_counts_and_its_interval_includes_one():
    """The number the brief got wrong, pinned so it cannot drift back.

    The brief gave ADOPT as RR 2.58 (1.02-7.24), an interval EXCLUDING the null. The
    posted counts give 2.5259 (0.9813-6.5018), which includes it.
    """
    obj = _load("apixaban-vte-prophylaxis")
    row = [r for r in obj["results"]["by_outcome"]["major_bleeding"]["per_trial"]
           if r["nct"] == "NCT00457002"][0]
    assert row["as_posted"] == {"apixaban_events": 15, "apixaban_n": 3184,
                                "comparator_events": 6, "comparator_n": 3217}
    assert abs(row["point"] - 2.5259) < 0.0005, row["point"]
    assert row["ci_low"] < 1.0 < row["ci_high"], (
        "ADOPT's major-bleeding interval is %s to %s. If it ever excludes 1 the counts "
        "have changed and the claim must be re-derived, not restated."
        % (row["ci_low"], row["ci_high"]))


def test_affirmed_poolability_is_not_a_refusal():
    """REGRESSION. `poolable: True` is an affirmation; reading it as a refusal made the
    gate report 0 findings where there were 2."""
    obj = {"results": {"by_outcome": {"eff": {
        "poolable": True,
        "poolable_reason": "All four register the same composite at secondary rank and "
                           "each title was read rather than matched by name."}}}}
    refused, where = G.published_refusal(obj)
    assert refused is False, (
        "an outcome declaring itself POOLABLE, with a long reason saying why it is, was "
        "read as a published refusal at %s. A field is not a value." % where)


def test_a_refusal_still_needs_a_reason():
    """The other polarity: a refusal flag with no reason beside it is a blank, not a
    reasoned refusal, and must not excuse a missing harm."""
    bare = {"results": {"by_outcome": {"eff": {"pooled": {"withdrawn": True}}}}}
    assert G.published_refusal(bare)[0] is False
    reasoned = {"results": {"by_outcome": {"eff": {"pooled": {
        "withdrawn": True,
        "withdrawn_reason": "k=1: a single registration cannot be pooled, Cochrane "
                            "Handbook 6.5 section 10.10.3."}}}}}
    assert G.published_refusal(reasoned)[0] is True


def test_a_topic_whose_pico_names_no_harm_is_never_a_finding():
    """The rule this lane was given explicitly, made mechanical: not naming a harm is not
    a defect, and must never enter the count."""
    obj = _load("sglt2-hf")
    assert not G.harm_mentions(obj), "fixture drifted: sglt2-hf now names a harm"
    for disposition in ("MENTION_IS_NOT_AN_OUTCOME", "COMPONENT_OF_SYNTHESISED_COMPOSITE"):
        assert G.decide(obj, disposition)[0] == "NOT_POLICED"
