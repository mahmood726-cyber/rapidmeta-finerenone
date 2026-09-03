r"""Gate 21 must be able to REFUSE, and these tests fire against the real module.

WHY THIS FILE EXISTS. Gate 21 is RATCHETED: the two findings that exist today are frozen
by name, so the gate reports PASS. A gate that has only ever been observed to pass is not
known to be able to fail, and "it passed" is exactly what a broken gate says too. So:

    test_gate_refuses_when_nothing_is_frozen   runs THE REAL gate, end to end, with the
        freeze list emptied, and requires exit FAIL. This is the negative test: the only
        thing standing between this corpus and a refusal is the freeze file, and that is
        demonstrated rather than asserted.

    test_ratchet_catches_a_new_instance        proves the ratchet does not swallow new
        findings -- freeze ONE of the two, and the other must come back as NEW and FAIL.
        A ratchet that froze a class rather than its members would pass this corpus
        forever, which is the failure mode a ratchet is most likely to have.

    test_apixaban_pages_decide_as_unreported   pins TODAY'S verdict on the two real
        objects through the real decide(). It is expected to CHANGE when the pages are
        fixed, and it says so, so that nobody reads its later failure as a regression.

    test_affirmed_poolability_is_not_a_refusal is the regression test for the defect this
        gate shipped with: `poolable: True` beside a long `poolable_reason` read as a
        reasoned refusal, and the gate reported 0 findings where there were 2.

⛔ NO MOCKS. Every test loads the real objects from ssot/ and calls the real functions.
   A test that asserted on a mock here would verify the mock.
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


def test_gate_refuses_when_nothing_is_frozen():
    """THE NEGATIVE TEST. The real gate, the real corpus, an empty freeze -> FAIL."""
    with _freeze_containing([]):
        rc = G.main([])
    assert rc == H.FAIL, (
        "gate 21 returned %s over a corpus holding %d unreported promised harms with an "
        "EMPTY freeze list. A gate that cannot refuse is not a gate."
        % (H.VERDICT_NAME[rc], len(TODAYS_FINDINGS)))


def test_ratchet_catches_a_new_instance():
    """Freeze one of the two; the other must come back NEW and the gate must refuse."""
    with _freeze_containing(TODAYS_FINDINGS[:1]):
        rc = G.main([])
    assert rc == H.FAIL, (
        "with %s frozen and %s NOT frozen, gate 21 returned %s. A ratchet that freezes a "
        "CLASS rather than its named members would pass here forever."
        % (TODAYS_FINDINGS[0], TODAYS_FINDINGS[1], H.VERDICT_NAME[rc]))


def test_gate_passes_with_the_real_freeze_in_place():
    """And it must PASS as shipped -- otherwise the two tests above prove nothing about
    the ratchet, only that the gate is red."""
    rc = G.main([])
    assert rc == H.PASS, (
        "gate 21 returned %s with its shipped freeze file. Either a NEW finding has "
        "appeared -- read the output, it is named -- or the gate is broken."
        % H.VERDICT_NAME[rc])


@pytest.mark.parametrize("app_id", TODAYS_FINDINGS)
def test_apixaban_pages_decide_as_unreported(app_id):
    """TODAY'S verdict, pinned through the real decide().

    ⚠️ THIS TEST IS EXPECTED TO FAIL WHEN THE PAGES ARE FIXED, and that failure is the
    fix landing, not a regression. Delete the app_id from TODAYS_FINDINGS when its
    bleeding outcome is published -- do NOT relax the assertion.
    """
    obj = _load(app_id)
    verdict, _where = G.decide(obj, "NAMED_AND_ABSENT")
    assert verdict == "PROMISED_NOT_REPORTED", (
        "%s decided %s. If its harms outcome has landed, remove it from TODAYS_FINDINGS "
        "and from the freeze file rather than loosening this." % (app_id, verdict))


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
