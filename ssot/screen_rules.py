# -*- coding: utf-8 -*-
"""Two screening rules every topic inherits, as code rather than as folklore.

Both came out of other lanes as TOPIC FACTS. They are not topic facts. They are
harness rules, and a rule that lives in one topic's commit message protects one
topic.

=============================================================================
RULE 1 -- A PHASE FILTER MUST DECLARE WHAT `NA` DOES, AND THE DEFAULT IS KEEP.
=============================================================================
ClinicalTrials.gov records `phases: ["NA"]` for interventional studies that are
not drug-phase studies -- and for some that plainly are. NCT01539226, The Ring
Study, is a 1,959-participant double-blind placebo-controlled efficacy trial of
a dapivirine vaginal ring. Its registered phase is NA. Its companion
NCT01617096 is PHASE3.

⛔ A REGISTRY-FIRST SCREEN THAT FILTERS ON `PHASE3` DROPS ONE OF THE TWO TRIALS
IN A TWO-TRIAL META-ANALYSIS, halves the evidence base, and reports a clean
count while doing it. Nothing in the output says a trial was removed for a
field the sponsor left blank.

So: `phase_keep()` is the only sanctioned phase filter. It KEEPS `NA` by
default, records every exclusion by NCT, and refuses to run at all unless the
caller has said in words what NA means for this screen.

=============================================================================
RULE 2 -- THE EXECUTED QUERY IS THE SENSITIVE ONE. TIDYING IT IS A REGRESSION.
=============================================================================
The dapivirine concept block, unquoted, returns 63 ClinicalTrials.gov records.
The same block rewritten with quoted phrases -- which looks tidier and reads
like a correction -- returns 56. SEVEN RECORDS DISAPPEAR and nothing in the
rewrite announces it.

Quoting narrows: an unquoted multi-word term matches records where the words
appear apart or in another form, and the registry's own tokeniser is doing work
a quoted phrase forbids. On a screen where precision is not the binding
constraint -- and on a single-compound block it never is -- narrowing is pure
recall loss.

So: `assert_query_not_narrowed()` compares a proposed query against the
executed one and REFUSES a rewrite that returns fewer records, unless the
caller passes an explicit justification. A correction that loses records is a
regression wearing the word "fix".

NO NETWORK IN THIS MODULE. The counts are supplied by the caller, so the rules
are testable offline and the same function guards a live run and a fixture.
"""
import io
import sys


class ScreenRuleViolation(Exception):
    """Raised rather than returned. A caller that could ignore a flag would."""


# ---------------------------------------------------------------- RULE 1 ----
NA_TOKENS = ("NA", "N/A", "NOT_APPLICABLE", "NOTAPPLICABLE", "", "NONE", "NULL")


def phase_keep(records, wanted_phases, na_policy=None, phase_key="phases",
               id_key="nct"):
    """Filter registry records on phase, KEEPING `NA` unless told otherwise.

    records      -- iterable of dicts
    wanted_phases-- e.g. ("PHASE3",) ; case-insensitive
    na_policy    -- REQUIRED, and it must be a SENTENCE, not a boolean. The
                    caller has to say what NA means for this screen and that
                    sentence is returned with the result so it reaches the
                    page. Pass na_policy="DROP: ..." to drop them.

    Returns {kept, dropped, na_kept, na_policy, ...} -- every exclusion named.
    """
    if not na_policy or not isinstance(na_policy, str) or len(na_policy) < 20:
        raise ScreenRuleViolation(
            "REFUSED: a phase filter must DECLARE what `NA` does, in a "
            "sentence, before it runs. NCT01539226 -- a 1,959-participant "
            "double-blind placebo-controlled efficacy trial -- is registered "
            "phase NA, and a PHASE3 filter drops it while reporting a clean "
            "count. Pass na_policy='KEEP: ...' or na_policy='DROP: ...' with "
            "the reason.")
    drop_na = na_policy.strip().upper().startswith("DROP")
    want = {str(p).replace(" ", "").replace("-", "").upper()
            for p in (wanted_phases or [])}

    kept, dropped, na_kept, na_dropped = [], [], [], []
    for r in records:
        rid = r.get(id_key) or r.get("nct_id") or r.get("id") or "?"
        raw = r.get(phase_key)
        if isinstance(raw, (list, tuple)):
            phases = [str(x).replace(" ", "").replace("-", "").upper() for x in raw]
        elif raw is None:
            phases = [""]
        else:
            phases = [str(raw).replace(" ", "").replace("-", "").upper()]
        is_na = all(p in NA_TOKENS for p in phases)

        if is_na:
            if drop_na:
                na_dropped.append({"id": rid, "phases": phases,
                                   "why": "phase NA and na_policy says DROP"})
                dropped.append(rid)
            else:
                na_kept.append({"id": rid, "phases": phases})
                kept.append(r)
            continue
        if not want or (set(phases) & want):
            kept.append(r)
        else:
            dropped.append(rid)

    total = len(kept) + len(dropped)
    return {
        "kept": kept,
        "n_kept": "%d of %d" % (len(kept), total),
        "n_dropped": "%d of %d" % (len(dropped), total),
        "dropped_ids": dropped,
        "na_policy": na_policy,
        "na_kept": na_kept,
        "na_dropped": na_dropped,
        "n_na": "%d of %d records carry no usable phase"
                % (len(na_kept) + len(na_dropped), total),
        "⚠️_why_NA_is_kept_by_default": (
            "ClinicalTrials.gov records phase NA for interventional studies "
            "that are not drug-phase studies AND for some that plainly are. "
            "NCT01539226 is one: a 1,959-participant double-blind "
            "placebo-controlled efficacy trial of a vaginal ring, registered "
            "NA, whose companion NCT01617096 is PHASE3. A PHASE3 filter drops "
            "one of the two trials in a two-trial meta-analysis and reports a "
            "clean count while doing it."),
        "_rule": "ssot/screen_rules.py phase_keep()",
    }


# ---------------------------------------------------------------- RULE 2 ----
# VERIFIED BY EXECUTION 2026-08-30, not taken on trust from another lane's
# commit message. Both forms of the dapivirine concept block were run against
# the ClinicalTrials.gov API v2, intervention and free-text queries unioned:
#
#     unquoted (the executed block) : 63 NCT ids
#     quoted   (the tidier rewrite) : 56 NCT ids
#
# The quoted set is a STRICT SUBSET. The seven records only the unquoted query
# finds are named here so the evidence travels with the rule rather than
# sitting in a log:
QUOTING_LOSES_THESE = (
    "NCT01530399", "NCT01897896", "NCT02197130", "NCT02342548",
    "NCT03519737", "NCT03813238", "NCT04200352",
)


def assert_query_not_narrowed(executed_query, executed_n,
                              proposed_query, proposed_n,
                              justification=None):
    """Refuse a query rewrite that returns fewer records.

    ⭐ THE EXECUTED QUERY IS THE SENSITIVE ONE. The dapivirine concept block
    unquoted returns 63 ClinicalTrials.gov records; the tidier quoted rewrite
    returns 56. Seven records vanish and the rewrite looks like a correction.
    Quoting narrows -- a quoted phrase forbids the registry's own tokeniser
    from matching the words apart or in another form -- and on a single-compound
    block precision is never the binding constraint.
    """
    lost = int(executed_n) - int(proposed_n)
    if lost > 0 and not justification:
        raise ScreenRuleViolation(
            "REFUSED: the proposed query returns %d records where the "
            "EXECUTED query returns %d. That is %d LOST, and a rewrite that "
            "loses records is a regression however much tidier it reads.\n"
            "  executed : %s\n  proposed : %s\n"
            "If the loss is intended, pass a justification naming which "
            "records are dropped and why they are ineligible."
            % (proposed_n, executed_n, lost, executed_query, proposed_query))
    return {
        "executed_query": executed_query, "executed_n": executed_n,
        "proposed_query": proposed_query, "proposed_n": proposed_n,
        "delta": -lost if lost else 0,
        "verdict": ("NARROWER, ACCEPTED WITH JUSTIFICATION" if lost > 0 else
                    ("BROADER by %d" % -lost) if lost < 0 else "IDENTICAL YIELD"),
        "justification": justification,
        "_rule": "ssot/screen_rules.py assert_query_not_narrowed()",
    }


# ------------------------------------------------------------- selftest -----
def selftest():
    """Both rules must FIRE. A guard that has never fired is not proven."""
    out = {}

    # RULE 1: the real pair. NA must survive a PHASE3 filter.
    recs = [{"nct": "NCT01539226", "phases": ["NA"]},
            {"nct": "NCT01617096", "phases": ["PHASE3"]},
            {"nct": "NCT00000001", "phases": ["PHASE1"]}]
    r = phase_keep(recs, ("PHASE3",),
                   na_policy="KEEP: registry phase NA is not evidence a study "
                             "is out of scope; eligibility is decided on "
                             "design and outcome, not on a sponsor's field.")
    kept = {x["nct"] for x in r["kept"]}
    assert kept == {"NCT01539226", "NCT01617096"}, kept
    out["rule1_keeps_the_NA_trial"] = sorted(kept)

    # ...and the undeclared-policy refusal must fire.
    try:
        phase_keep(recs, ("PHASE3",))
        raise AssertionError("RULE 1 NEGATIVE TEST FAILED: an undeclared "
                             "na_policy was accepted.")
    except ScreenRuleViolation:
        out["rule1_refuses_an_undeclared_policy"] = True

    # ...and DROP must actually drop, so the policy is not decorative.
    r2 = phase_keep(recs, ("PHASE3",),
                    na_policy="DROP: this screen is drug-phase only and NA is "
                              "treated as out of scope for the stated reason.")
    assert {x["nct"] for x in r2["kept"]} == {"NCT01617096"}
    out["rule1_DROP_is_honoured"] = True

    # RULE 2: the real counts. 63 -> 56 must be refused.
    try:
        assert_query_not_narrowed("dapivirine OR TMC 120 OR R 147681", 63,
                                  '"dapivirine" OR "TMC 120" OR "R 147681"', 56)
        raise AssertionError("RULE 2 NEGATIVE TEST FAILED: a rewrite losing 7 "
                             "records was accepted.")
    except ScreenRuleViolation as exc:
        assert "7 LOST" in str(exc)
        out["rule2_refuses_the_63_to_56_rewrite"] = True

    assert len(QUOTING_LOSES_THESE) == 7
    out["rule2_the_seven_lost_ids_are_named"] = list(QUOTING_LOSES_THESE)

    ok = assert_query_not_narrowed("a", 56, "b", 63)
    assert ok["delta"] == 7 and "BROADER" in ok["verdict"]
    out["rule2_allows_a_broader_query"] = ok["verdict"]
    return out


if __name__ == "__main__":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8",
                                  errors="replace")
    import json
    print("SCREEN RULES -- SELFTEST")
    print(json.dumps(selftest(), indent=1, ensure_ascii=False))
    print()
    print("Both rules fire. Neither is folklore in a commit message any more.")
