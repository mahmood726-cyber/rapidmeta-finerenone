"""The abstract's heterogeneity sentence must be gated on the VALUE of I-squared.

The sentence "no statistical heterogeneity was detected (I-squared X%)" used to be
emitted whenever the object stored an i2 AT ALL. The condition tested three things --
that an i2 exists, that a pool exists, and how many trials there were -- and none of
them was the i2's value, so the sentence asserted the absence of heterogeneity and then
printed the falsifying number in the same parenthesis.

On APIXABAN_VTE_PROPHYLAXIS the abstract denied heterogeneity at I-squared 71.5% while
the body of the same page, reading the same field through `_i2_words`, called the trials
"loosely consistent" and printed tau-squared 0.204 and Q 9.31 on 3 degrees of freedom.

These tests call the REAL projector -- `project()` and `render()` from
ssot/paper_projector.py -- against the REAL stores. Nothing here reimplements the
sentence; a fixture that reimplemented the defect would only test its own copy.

Run:  python scripts/test_heterogeneity_sentence_gated_on_value.py   (standalone)
  or: pytest scripts/test_heterogeneity_sentence_gated_on_value.py
"""
import io
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)

# ssot/ goes on the path rather than loading the file by location: the projector
# imports its siblings (`grade_authority`) by bare name, exactly as `main()` runs it.
_SSOT = os.path.join(REPO, "ssot")
if _SSOT not in sys.path:
    sys.path.insert(0, _SSOT)
import paper_projector as pp  # noqa: E402  (path must be set first)

ABSENCE = "no statistical heterogeneity was detected"
CAVEAT = "cannot be reliably assessed with two trials"

# The Handbook 10.10.2 boundary `_i2_words` already uses to stop saying the trials
# agreed "closely". Below it the absence sentence stands; at or above it, it is false.
BAND_FLOOR = 30.0


def _store(topic):
    """The real store for a topic. Missing is a hard failure, never a silent skip."""
    path = os.path.join(REPO, "ssot", topic, topic + ".json")
    assert os.path.exists(path), "fixture store missing: %s" % path
    with io.open(path, encoding="utf-8") as fh:
        return json.load(fh)


def abstract_results(topic):
    """EVERY abstract Results sentence carrying an I-squared, as the projector renders it.

    Returning the FIRST match and stopping is what this function did to begin with, and
    it hid a real offender: ARNI's abstract holds two Results paragraphs -- a stored,
    hand-authored one that already says "Heterogeneity was moderate ... I-squared 32.9
    percent", and the projected one that said heterogeneity was not detected at that
    same 32.9%. The stored paragraph comes first and contains the string "I-squared", so
    a first-match scan read the sentence that was already correct, reported ARNI clean,
    and never looked at the one that was wrong. A scan reports where it LOOKED.
    """
    text = pp.render(pp.project(_store(topic)))
    section, found = None, []
    for line in text.split("\n"):
        if line.startswith("## "):
            section = line
        stripped = line.strip()
        if (section or "").startswith("## Abstract") and \
                stripped.startswith("Results.") and "I-squared" in stripped:
            found.append(stripped)
    if not found:
        raise AssertionError(
            "no abstract Results sentence carrying an I-squared for %s -- the fixture "
            "no longer exercises the defect and must be repointed, not deleted" % topic)
    return found


def stored_i2(topic):
    """The largest i2 the store holds, for reporting the denominator of a sweep."""
    best = None
    for blk in ((_store(topic).get("results") or {}).get("by_outcome") or {}).values():
        if isinstance(blk, dict):
            value = (blk.get("heterogeneity") or {}).get("i2")
            try:
                value = float(value)
            except (TypeError, ValueError):
                continue
            best = value if best is None else max(best, value)
    return best


# ---------------------------------------------------------------------------
# THE DEFECT. Each assertion is separate: a compound one that failed for the
# wrong half would be indistinguishable from one that failed for the right half.
# ---------------------------------------------------------------------------

def test_high_i2_does_not_assert_absence_of_heterogeneity():
    """I-squared 71.5%, Q 9.31 on df 3, k 4 -- heterogeneity is present and large."""
    sentences = abstract_results("apixaban-vte-prophylaxis")
    assert any("71.5" in s for s in sentences), (
        "fixture drifted off the 71.5%% case: %s" % sentences)
    offenders = [s for s in sentences if ABSENCE in s]
    assert not offenders, (
        "the abstract asserts heterogeneity was not detected at I-squared 71.5%%: %s"
        % offenders)


def test_high_i2_states_the_heterogeneity_it_found():
    """Not asserting absence is not enough; the sentence must say what was found."""
    sentences = abstract_results("apixaban-vte-prophylaxis")
    assert any("heterogeneity was substantial" in s for s in sentences), (
        "I-squared 71.5%% is 'substantial' on the boundaries `_i2_words` already "
        "uses (60-75); the abstract says: %s" % sentences)


def test_high_i2_at_two_trials_keeps_the_caveat_and_drops_the_denial():
    """ROSUVASTATIN: I-squared 80.2% on k=2. Both halves matter, so both are asserted."""
    sentences = abstract_results("rosuvastatin-auto-full-review")
    assert not [s for s in sentences if ABSENCE in s], (
        "absence asserted at I-squared 80.2%%: %s" % sentences)
    assert any(CAVEAT in s for s in sentences), (
        "the two-trial caveat was dropped -- it matters MORE at a high I-squared on "
        "two trials, not less: %s" % sentences)


def test_arni_projected_sentence_agrees_with_its_own_stored_one():
    """ARNI is the case a first-match scan hides, and the reason this reads them all.

    Its abstract carries a stored, hand-authored sentence -- "Heterogeneity was moderate
    and estimator-dependent, with I-squared 32.9 percent" -- and, beside it, a projected
    one that said heterogeneity was not detected at that same 32.9%. One page, one
    number, two opposite claims.
    """
    sentences = abstract_results("arni-hfref")
    assert len(sentences) >= 2, (
        "ARNI should carry both a stored and a projected Results sentence; found %d"
        % len(sentences))
    assert any("Heterogeneity was moderate and estimator-dependent" in s
               for s in sentences), "the stored ARNI sentence is gone: %s" % sentences
    offenders = [s for s in sentences if ABSENCE in s]
    assert not offenders, (
        "the projected sentence denies the heterogeneity the stored one beside it "
        "reports, at I-squared 32.9%%: %s" % offenders)
    assert any("heterogeneity was moderate (I-squared 32.9%)" in s for s in sentences), (
        "the projected sentence should land on the same band as the stored one: %s"
        % sentences)


# ---------------------------------------------------------------------------
# THE CONTROLS. A fix that silenced the sentence everywhere would clear the
# tests above and destroy 15 pages that say something true. These must stay green
# BOTH BEFORE AND AFTER the fix.
# ---------------------------------------------------------------------------

def test_low_i2_still_reports_the_absence_it_measured():
    """SGLT2-HF: I-squared 0% on k=4. The sentence is true here and must survive."""
    sentences = abstract_results("sglt2-hf")
    assert any(ABSENCE in s for s in sentences), (
        "the fix silenced a true sentence at I-squared 0%%: %s" % sentences)
    assert any("(I-squared 0%)" in s for s in sentences), sentences


def test_low_i2_at_two_trials_keeps_both_clause_and_caveat():
    """FINERENONE-CV: I-squared 0% on k=2 -- the pre-existing k<=2 wording, unchanged."""
    sentences = abstract_results("finerenone-cv")
    assert any(ABSENCE in s for s in sentences), sentences
    assert any(CAVEAT in s for s in sentences), (
        "the pre-existing two-trial caveat was lost: %s" % sentences)


def test_highest_low_band_store_is_untouched():
    """TIGECYCLINE-CIAI: I-squared 7.29%, the largest value that must NOT change."""
    sentences = abstract_results("tigecycline-ciai")
    assert any(ABSENCE in s for s in sentences), (
        "the boundary moved below 7.29%% and silenced a true sentence: %s" % sentences)


# ---------------------------------------------------------------------------
# THE SWEEP. Named fixtures prove the two ends; this proves no store in the
# corpus is left asserting absence at a value that contradicts it. It reports
# its own denominator, because a sweep that looked at nothing passes silently.
# ---------------------------------------------------------------------------

def test_no_store_in_the_corpus_asserts_absence_above_the_band_floor():
    root = os.path.join(REPO, "ssot")
    topics = sorted(
        name for name in os.listdir(root)
        if os.path.exists(os.path.join(root, name, name + ".json")))
    assert len(topics) >= 100, (
        "only %d stores visible -- this sweep reports where it LOOKED, and a "
        "truncated corpus would pass it for the wrong reason" % len(topics))

    examined, offenders = 0, []
    for topic in topics:
        try:
            sentences = abstract_results(topic)
        except AssertionError:
            continue  # no heterogeneity clause in this abstract; nothing to gate
        examined += 1
        i2 = stored_i2(topic)
        if i2 is not None and i2 >= BAND_FLOOR and any(ABSENCE in s for s in sentences):
            offenders.append((topic, i2))

    assert examined >= 20, (
        "only %d abstracts carried a heterogeneity clause; expected ~25" % examined)
    assert not offenders, (
        "%d of %d abstracts assert heterogeneity was not detected at I-squared >= %g:\n%s"
        % (len(offenders), examined, BAND_FLOOR,
           "\n".join("    %-44s I-squared %.4g%%" % (t, v) for t, v in offenders)))


if __name__ == "__main__":
    failed = 0
    for _name, _fn in sorted(globals().items()):
        if _name.startswith("test_") and callable(_fn):
            try:
                _fn()
                print("PASS  %s" % _name)
            except AssertionError as exc:
                failed += 1
                print("FAIL  %s\n      %s" % (_name, exc))
    print("\n%d failed" % failed)
    raise SystemExit(1 if failed else 0)
