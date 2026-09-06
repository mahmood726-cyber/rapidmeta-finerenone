"""The enumeration ledger reconciles, records the discard, and REFUSES when it cannot.

WHY THIS FILE EXISTS. `find_ncts` used to end `return matches[:max_per_topic]` with nothing
reading `len(matches)`, so the pool a topic actually had was destroyed one expression after
it was computed. The ledger fixes that. But a ledger is exactly the kind of thing that can
be wrong while looking right -- it prints plausible integers whatever happens -- so the
tests below are built around one requirement:

    A LEDGER THAT CANNOT REFUSE IS NOT A LEDGER, IT IS A LABEL.
    `test_ledger_refuses_when_a_drop_leaves_no_trace` takes the shipped source, replaces
    `dropped_condition += 1` with `pass`, exec s that, and requires the refusal -- so the
    GUARD under test is the one that ships and only the counter is broken.
    `test_the_unmutated_matcher_does_not_refuse` is its other half, because a guard that
    fires on everything is not a guard. Without both, every assertion here would pass
    just as happily against a function that computed nothing and returned constants.

The matcher is EXTRACTED from add_topic_autodiscover.py by text slice and exec'd unmodified,
because the module cannot be imported: it reads a multi-gigabyte AACT snapshot at import
time. The indexes are fabricated so that every stage count is known BY CONSTRUCTION rather
than read back from the thing under test.
"""
import hashlib
import io
import os
import re

import pytest

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SOURCE = os.path.join(HERE, "scripts", "add_topic_autodiscover.py")
SLICE_START = "DRUG_SYNS = {"
SLICE_END = "    return kept"


def load_matcher():
    with io.open(SOURCE, encoding="utf-8") as fh:
        src = fh.read()
    i = src.index(SLICE_START)
    j = src.index(SLICE_END) + len(SLICE_END)
    ns = {"re": re, "os": os}
    exec(compile(src[i:j], SOURCE, "exec"), ns)
    return ns


def make_indexes(n_eligible=12, n_wrong_condition=5, n_observational=3, n_wrong_drug=40):
    """Four populations whose sizes ARE the expected stage drops.

    Nothing here is read back from the matcher: the caller states what each group is for,
    so a stage that miscounts disagrees with a number the test already knows.
    """
    intv, cond, styp, enroll, phase, posted, exp = {}, {}, {}, {}, {}, {}, {}

    def add(nct, drug, condition, study_type):
        intv[nct] = [drug]
        cond[nct] = [condition]
        styp[nct] = study_type
        enroll[nct] = 100
        phase[nct] = "phase3"
        posted[nct] = True
        exp[nct] = [drug]

    for k in range(n_eligible):
        add("NCT9000%04d" % k, "dapagliflozin 10 mg", "heart failure", "interventional")
    for k in range(n_wrong_condition):
        add("NCT9100%04d" % k, "dapagliflozin 10 mg", "type 2 diabetes", "interventional")
    for k in range(n_observational):
        add("NCT9200%04d" % k, "dapagliflozin 10 mg", "heart failure", "observational")
    for k in range(n_wrong_drug):
        add("NCT9300%04d" % k, "placebo", "heart failure", "interventional")

    return dict(intv_by_nct=intv, cond_by_nct=cond, study_type_by_nct=styp,
                enroll_by_nct=enroll, phase_by_nct=phase,
                results_posted_by_nct=posted, exp_intv_by_nct=exp)


def run(ns, cap, **kw):
    ns.update(make_indexes(**kw))
    ledger = {}
    kept = ns["find_ncts"](["dapagliflozin"], ["heart failure"], cap, ledger)
    return kept, ledger


def test_ledger_records_the_pool_the_cap_cut_from():
    ns = load_matcher()
    kept, led = run(ns, cap=5)
    assert led["eligible"] == 12, led
    assert led["ingested"] == 5 == len(kept)
    assert led["discarded_by_cap"] == 7, led
    assert len(led["discarded_ncts"]) == 7
    assert led["cap_bit"] is True
    # The pre-slice pool is recoverable from the record alone, which is the whole point.
    assert led["ingested"] + led["discarded_by_cap"] == led["eligible"]


def test_every_stage_names_the_reason_for_its_drop():
    ns = load_matcher()
    _, led = run(ns, cap=100, n_eligible=12, n_wrong_condition=5,
                 n_observational=3, n_wrong_drug=40)
    assert led["retrieved"] == 60, led
    assert led["identity_rejected"] == 40, led
    assert led["dropped_condition"] == 5, led
    assert led["dropped_study_type"] == 3, led
    assert led["eligible"] == 12, led
    assert (led["identity_rejected"] + led["dropped_condition"]
            + led["dropped_study_type"] + led["eligible"]) == led["retrieved"]
    assert sum(led["identity_reasons"].values()) == 40, led["identity_reasons"]


def test_a_pool_shorter_than_the_cap_reports_no_loss():
    """The over-flagging direction: an uncut pool must not be recorded as a discard."""
    ns = load_matcher()
    kept, led = run(ns, cap=50, n_eligible=12)
    assert led["discarded_by_cap"] == 0
    assert led["discarded_ncts"] == []
    assert led["cap_bit"] is False
    assert len(kept) == 12


def test_the_bound_is_recorded_with_its_source():
    ns = load_matcher()
    _, led = run(ns, cap=5)
    assert led["cap_applied"] == 5
    assert led["cap_source"] in ("default", "RM_MAX_PER_TOPIC")


def test_ledger_refuses_when_a_drop_leaves_no_trace():
    """THE CASE THAT MUST FIRE, and it exercises the REAL guard, not a copy of it.

    The first draft of this test asserted a hand-written reimplementation of the
    reconciliation. That proves the test agrees with itself and nothing about the shipped
    code -- the same class of mistake as a snapshot test that was generated from the
    implementation it is meant to police.

    So the guard is left EXACTLY as shipped and the COUNTER is broken instead: the source
    slice is taken, `dropped_condition += 1` is replaced by `pass`, and the result is
    exec'd. That is precisely the original defect -- a candidate discarded without the
    discard being counted -- and the reconciliation must refuse.

    If this test ever passes by NOT raising, every other assertion in this file is
    worthless, because the ledger would be reporting arithmetic it never checks.
    """
    with io.open(SOURCE, encoding="utf-8") as fh:
        src = fh.read()
    i = src.index(SLICE_START)
    j = src.index(SLICE_END) + len(SLICE_END)
    block = src[i:j]

    counter = "            dropped_condition += 1"
    assert block.count(counter) == 1, "the counter this test mutates has moved or changed"
    mutated = block.replace(counter, "            pass")
    assert mutated != block

    ns = {"re": re, "os": os}
    exec(compile(mutated, SOURCE + " [MUTATED: condition drop uncounted]", "exec"), ns)
    ns.update(make_indexes(n_eligible=12, n_wrong_condition=5,
                           n_observational=3, n_wrong_drug=40))

    with pytest.raises(AssertionError) as exc:
        ns["find_ncts"](["dapagliflozin"], ["heart failure"], 100, {})
    assert "does not reconcile" in str(exc.value)
    # And it names the shortfall rather than only complaining: 5 condition drops went
    # uncounted, so 55 are accounted for against 60 examined.
    assert "60 examined, 55 accounted for" in str(exc.value)


def test_the_unmutated_matcher_does_not_refuse():
    """The negative half. A guard that fires on everything is not a guard.

    Same index, same call, the shipped slice: it must NOT raise. Without this the test
    above would pass against a reconciliation that refuses unconditionally.
    """
    ns = load_matcher()
    ns.update(make_indexes(n_eligible=12, n_wrong_condition=5,
                           n_observational=3, n_wrong_drug=40))
    led = {}
    kept = ns["find_ncts"](["dapagliflozin"], ["heart failure"], 100, led)
    assert len(kept) == 12
    assert led["dropped_condition"] == 5


def test_the_extracted_slice_is_the_shipped_matcher():
    """Guard against this file testing a copy that has drifted from the source."""
    with io.open(SOURCE, encoding="utf-8") as fh:
        src = fh.read()
    assert src.count(SLICE_START) == 1
    assert "return kept" in src
    assert "MAX_PER_TOPIC = int(os.environ.get(" in src
    # The slice must contain the ledger, or these tests would be exercising a matcher that
    # predates it and reporting green.
    i = src.index(SLICE_START)
    j = src.index(SLICE_END) + len(SLICE_END)
    block = src[i:j]
    assert "discarded_by_cap" in block
    assert "does not reconcile" in block
    assert len(hashlib.sha256(block.encode("utf-8")).hexdigest()) == 64
