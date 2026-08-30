# -*- coding: utf-8 -*-
"""KNOWN-ANSWER control for ssot/grade_engine.py.

⭐ THE ASSERTION THIS CONTROL EXISTS TO MAKE, in Mahmood's words on 2026-08-29:

    "A control must assert the refusal STAYS refused -- if a control ever creates
     pressure to publish a rating instead of withholding one, the control is wrong."

So the controls below are not symmetric, deliberately. There is ONE test that a complete
object earns a letter. There are SEVEN that an incomplete one earns nothing, one per way
of being incomplete, and each names the input it removed. A suite that only checked the
happy path would reward an engine that guessed, and guessing is the whole defect.

EVERY FIXTURE IS SYNTHETIC AND NAMED `__control_*`. Nothing here points at a live object.
A control anchored to real corpus data retires itself the moment that data is fixed: it
then either fails and looks like a regression, or passes for the wrong reason. Both
happened on this project before the rule was written down.

THE POSITIVE CONTROL IS KEYED OUTSIDE THIS CODE. Its expected answer is not a number this
module chose -- it is the GRADE ladder itself, HIGH -> MODERATE -> LOW -> VERY LOW, one
step per level of downgrade, as set out in Cochrane Handbook ch 14. A control whose
expected value came from running the thing it checks is a tautology.

BOTH DIRECTIONS, EVERY CHECK. `test_plant_detects_a_broken_engine` deliberately breaks the
publication-bias domain -- making it report "no downgrade" at k=2, which is the single
most common false claim in published meta-analyses -- and asserts the suite NOTICES.
A control that has never been seen to fail has not been shown to measure anything.
"""
import io
import json
import os
import sys
import traceback

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "ssot"))

import grade_engine as ge  # noqa: E402

CONTROL_PREFIX = "__control_"

# --------------------------------------------------------------------------- fixtures


NCT = "NCT00000001"


def _rob(outcome, overall="LOW", agreed=True, second=None):
    """A risk-of-bias store in the REAL canonical shape, not an invented one.

    ⚠️ THE FIRST VERSION OF THIS HELPER INVENTED A SHAPE. It wrote `overall` as a list of
    per-assessor verdicts directly, which is what `rob_block` RETURNS but not what the
    corpus STORES. `rob_block` builds the second assessor by parsing a flat
    `SECOND_ASSESSOR_<date>.verbatim_reply` string, so the invented store produced one
    assessor and a nested `[["LOW","HIGH"]]`, and the control tested a shape no object has.

    That is this project's own rule arriving from the other direction: a control keyed to
    something other than the real artefact measures the control. The fixture now builds
    what the store actually contains and lets `rob_block` do the normalising.
    """
    # ⚠️ SECOND FIXTURE CORRECTION, AND IT MATTERS FOR WHAT THE CONTROL CAN SEE.
    # The per-domain judgements live under a `domains` DICT keyed by the full domain name,
    # each holding {'judgement': ...} -- not as flat "D1"/"D2" keys on the record. The
    # flat-key version this fixture first used was silently ignored by `rob_block`, so
    # every control ran against a store with ZERO domains and could not have noticed if
    # the per-domain inputs never reached the record at all. A fixture that omits the
    # thing under test passes for the wrong reason, which is the failure mode the
    # standing rules call a vacuous pass.
    DOMS = [("D1_randomisation_process", "LOW"),
            ("D2_deviations_from_intended_intervention", "LOW"),
            ("D3_missing_outcome_data", "LOW"),
            ("D4_measurement_of_the_outcome", "LOW"),
            ("D5_selection_of_the_reported_result", "LOW")]
    store = {
        "tool": "RoB 2",
        "by_outcome": {
            outcome: {
                NCT: {
                    "trial": "__control_trial_1",
                    "id": NCT,
                    "outcome": outcome,
                    "domains": {k: {"judgement": v, "reason": "__control_ fixture"}
                                for k, v in DOMS},
                    "overall": overall,
                }
            }
        },
    }
    if second is not None:
        store["SECOND_ASSESSOR_2026_08_21"] = {
            "assessor": "__control_assessor_2",
            "verbatim_reply": "%s__%s D1=LOW D2=LOW D3=LOW D4=LOW D5=LOW OVERALL=%s"
                              % (NCT, outcome, second),
        }
    return store


def clean_object(k=4, i2=0.0, tau2=0.0, lo=0.40, hi=0.70, measure="RR",
                 rob_overall="LOW", indirect_state=ge.NO_DOWNGRADE):
    """A synthetic object on which ALL FIVE domains resolve.

    k is 4, so publication bias is NOT_ASSESSABLE -- a resolved state that carries no
    downgrade and must NOT block a rating. That is itself part of what this fixture
    checks: if NOT_ASSESSABLE ever started blocking, every rating in the corpus would
    vanish and the engine would look 'safe' while saying nothing.
    """
    return {
        "app_id": CONTROL_PREFIX + "clean",
        "question": "Does the control intervention reduce the control outcome?",
        "risk_of_bias": _rob("primary", overall=rob_overall),
        "results": {
            "by_outcome": {
                "primary": {
                    "k": k,
                    "pooled": {"point": (lo * hi) ** 0.5, "ci_low": lo, "ci_high": hi,
                               "ci_level": 95, "measure": measure},
                    "heterogeneity": {"i2": i2, "tau2": tau2, "q": 1.0, "df": k - 1},
                    "grade": {"indirectness": {"state": indirect_state, "levels": 0,
                                               "reason": "Control fixture: the contributing trials match the question on population, intervention, comparator and outcome."}},
                    "per_trial": [],
                }
            }
        },
    }


def _strip(obj, path):
    """Remove one input by dotted path, returning a modified deep copy."""
    o = json.loads(json.dumps(obj))
    cur = o
    parts = path.split(".")
    for p in parts[:-1]:
        cur = cur.get(p) if isinstance(cur, dict) else None
        if cur is None:
            return o
    if isinstance(cur, dict):
        cur.pop(parts[-1], None)
    return o


# ------------------------------------------------------------------------------ tests

FAILURES = []


def check(name, cond, detail=""):
    if cond:
        print("  PASS  %s" % name)
    else:
        print("  FAIL  %s   %s" % (name, detail))
        FAILURES.append(name)


def test_positive_control_earns_a_letter():
    """A complete object is rated, and the letter follows the Handbook ladder."""
    print("\n[1] POSITIVE CONTROL -- a complete object earns a rating")
    # 0 downgrades -> HIGH
    r = ge.derive(clean_object(), "primary")
    check("clean object is RATED", r["rated"] is True, r.get("reason", "")[:120])
    check("0 downgrades -> HIGH (Handbook ch 14 ladder)",
          r.get("certainty") == "HIGH", "got %s" % r.get("certainty"))
    check("publication bias NOT_ASSESSABLE at k=4 does NOT block the rating",
          [d for d in r["domains"] if d["domain"] == "publication_bias"][0]["state"]
          == ge.NOT_ASSESSABLE)

    # 1 downgrade (risk of bias SOME_CONCERNS) -> MODERATE
    r2 = ge.derive(clean_object(rob_overall="SOME_CONCERNS"), "primary")
    check("1 downgrade -> MODERATE", r2.get("certainty") == "MODERATE",
          "got %s" % r2.get("certainty"))

    # 2 downgrades (RoB + imprecision via a null-crossing interval) -> LOW
    r3 = ge.derive(clean_object(rob_overall="SOME_CONCERNS", lo=0.7, hi=1.4), "primary")
    check("2 downgrades -> LOW", r3.get("certainty") == "LOW",
          "got %s" % r3.get("certainty"))

    # 4 downgrades cannot fall below VERY_LOW
    r4 = ge.derive(clean_object(rob_overall="HIGH", lo=0.7, hi=1.4, i2=90.0, tau2=0.4),
                   "primary")
    check("the ladder floors at VERY_LOW", r4.get("certainty") == "VERY_LOW",
          "got %s" % r4.get("certainty"))


def test_every_missing_input_refuses():
    """⭐ THE CONTROL THAT MATTERS. Remove one input; a letter must NOT appear."""
    print("\n[2] REFUSAL CONTROLS -- remove one input, no rating may be issued")
    cases = [
        ("risk_of_bias",     "risk_of_bias",     "risk_of_bias"),
        ("heterogeneity",    "results.by_outcome.primary.heterogeneity", "inconsistency"),
        ("pooled interval",  "results.by_outcome.primary.pooled",  "imprecision"),
        ("k",                "results.by_outcome.primary.k",       "inconsistency"),
    ]
    for label, path, domain in cases:
        obj = _strip(clean_object(), path)
        r = ge.derive(obj, "primary")
        check("removing %-16s -> no letter" % label,
              r["rated"] is False and r.get("certainty") is None,
              "rated=%s certainty=%s" % (r["rated"], r.get("certainty")))
        check("removing %-16s -> %s REFUSED" % (label, domain),
              domain in (r.get("refused_domains") or []),
              "refused=%s" % (r.get("refused_domains"),))

    # indirectness has no derivation at all: absent judgement must refuse
    obj = _strip(clean_object(), "results.by_outcome.primary.grade")
    r = ge.derive(obj, "primary")
    check("absent indirectness judgement -> no letter",
          r["rated"] is False and r.get("certainty") is None)
    check("absent indirectness judgement -> indirectness REFUSED",
          "indirectness" in (r.get("refused_domains") or []))

    # an unrecognised summary measure must refuse rather than assume where the null is
    obj = clean_object(measure="WEIRD_UNIT")
    r = ge.derive(obj, "primary")
    check("unrecognised measure -> imprecision REFUSED (null not assumed)",
          "imprecision" in (r.get("refused_domains") or []),
          "refused=%s" % (r.get("refused_domains"),))


def test_refusal_is_never_a_falsy_render():
    """A refusal must SAY it refused. `None`, '', '?' and an em dash are not refusals.

    This is the defect that turned a repair into a worse defect twice on this project:
    a refusal that renders as a falsy value reads to a reader as 'nothing to report'.
    """
    print("\n[3] A REFUSAL MUST BE SAYABLE -- never a falsy or empty render")
    r = ge.derive(_strip(clean_object(), "risk_of_bias"), "primary")
    check("refusal carries a non-empty reason",
          isinstance(r.get("reason"), str) and len(r["reason"]) > 80)
    check("refusal reason contains no em dash", "—" not in r.get("reason", ""))
    for d in r["domains"]:
        check("domain %-17s has a non-empty reason" % d["domain"],
              isinstance(d.get("reason"), str) and len(d["reason"]) > 20)
        check("domain %-17s move is not falsy" % d["domain"],
              bool(d.get("move")) and d["move"] not in ("-", "?", "—"))


def test_refusal_stays_refused_under_restoration():
    """⭐ MAHMOOD'S CONSTRAINT, STATED AS A TEST.

    Strip an input, confirm the refusal. Put it back, confirm the rating returns. Strip it
    AGAIN, and confirm the refusal returns unchanged. An engine that 'remembered' a rating
    across the restore -- through a cache, a stored field, a default filled in on the way
    past -- would pass the first two steps and fail this one.
    """
    print("\n[4] RESTORE-AND-RE-STRIP -- the refusal must come back identically")
    base = clean_object()
    before = ge.derive(base, "primary")
    stripped = ge.derive(_strip(base, "risk_of_bias"), "primary")
    restored = ge.derive(base, "primary")
    again = ge.derive(_strip(base, "risk_of_bias"), "primary")

    check("baseline is rated", before["rated"] is True)
    check("stripped refuses", stripped["rated"] is False)
    check("restored is rated again", restored["rated"] is True)
    check("re-stripped refuses AGAIN", again["rated"] is False)
    check("the two refusals are identical",
          again.get("refused_domains") == stripped.get("refused_domains")
          and again.get("reason") == stripped.get("reason"))
    check("no rating leaked into the refusal", again.get("certainty") is None)


def test_withdrawn_pool_never_carries_a_letter():
    """A withdrawn estimate has nothing for a certainty to be ABOUT."""
    print("\n[5] WITHDRAWN POOLS -- never a letter, even when one is stored")
    obj = clean_object()
    obj["results"]["by_outcome"]["primary"]["pooled"]["withdrawn"] = True
    obj["results"]["by_outcome"]["primary"]["grade"]["certainty"] = "HIGH"
    r = ge.derive(obj, "primary")
    check("withdrawn -> state WITHDRAWN", r["state"] == "WITHDRAWN")
    check("withdrawn -> no letter even though one is stored",
          r["rated"] is False and r.get("certainty") is None)


def test_publication_bias_says_not_assessable_not_undetected():
    """The domain most often given a false clean bill of health in published reviews."""
    print("\n[6] PUBLICATION BIAS -- 'not assessable', never 'undetected'")
    for k in (2, 5, 9):
        d = ge.d_publication_bias({}, "primary", {"k": k})
        check("k=%d -> NOT_ASSESSABLE" % k, d["state"] == ge.NOT_ASSESSABLE)
        check("k=%d -> reason cites the ten-study rule" % k, "10 studies" in d["reason"])
        check("k=%d -> reason cites s13.3.4.4 (not the corpus's 13.3.5.4)" % k,
              "13.3.4.4" in d["reason"] and "13.3.5.4" not in d["reason"])
        check("k=%d -> carries no downgrade" % k, d["levels"] == 0)
    d10 = ge.d_publication_bias({}, "primary", {"k": 10})
    check("k=10 with no asymmetry test -> REFUSED (the test is what would settle it)",
          d10["state"] == ge.REFUSED)


def test_dual_assessors_agreeing_is_not_pending():
    """Two assessors who AGREE have nothing to adjudicate; refusing there is a false
    refusal, and this project's detectors are measurably biased in that direction."""
    print("\n[7] DUAL ASSESSORS -- agreement is rateable, disagreement is not")
    agree = clean_object()
    agree["risk_of_bias"] = _rob("primary", overall="LOW", agreed=True, second="LOW")
    r = ge.derive(agree, "primary")
    check("two assessors agreeing -> rated", r["rated"] is True,
          "refused=%s" % (r.get("refused_domains"),))

    disagree = clean_object()
    disagree["risk_of_bias"] = _rob("primary", overall="LOW", agreed=False,
                                    second="HIGH")
    r2 = ge.derive(disagree, "primary")
    check("two assessors disagreeing, unadjudicated -> REFUSED",
          "risk_of_bias" in (r2.get("refused_domains") or []))
    check("the disagreement is named in the reason",
          "PENDING" in [d for d in r2["domains"]
                        if d["domain"] == "risk_of_bias"][0]["reason"])


def test_plant_detects_a_broken_engine():
    """⭐ BOTH DIRECTIONS. Break the engine on purpose; the suite must notice.

    The planted defect is the realistic one: publication bias reporting 'no downgrade'
    at k=2, i.e. a clean bill of health from a test that was never run. If the suite
    passes with this in place, the suite is decoration.
    """
    print("\n[8] PLANT -- break publication bias, the suite must FAIL")
    original = ge.d_publication_bias

    def broken(canon, oid, res):
        return ge._dom("publication_bias", ge.NO_DOWNGRADE,
                       "No evidence of publication bias was found.")

    ge.d_publication_bias = broken
    ge.DERIVERS = (ge.d_risk_of_bias, ge.d_inconsistency, ge.d_indirectness,
                   ge.d_imprecision, ge.d_publication_bias)
    before = len(FAILURES)
    try:
        test_publication_bias_says_not_assessable_not_undetected()
    finally:
        ge.d_publication_bias = original
        ge.DERIVERS = (ge.d_risk_of_bias, ge.d_inconsistency, ge.d_indirectness,
                       ge.d_imprecision, ge.d_publication_bias)
    detected = len(FAILURES) > before
    # The planted failures are EXPECTED, so remove them and record the real verdict.
    del FAILURES[before:]
    check("the plant was DETECTED (suite is not decoration)", detected,
          "the broken engine passed every publication-bias check")

    # ...and assert the restoration, per the standing rule.
    after = ge.d_publication_bias({}, "primary", {"k": 2})
    check("engine RESTORED after the plant", after["state"] == ge.NOT_ASSESSABLE)


def test_threshold_is_named_and_sensitivity_can_move():
    """⭐ THE SENSITIVITY REPORT MUST BE ABLE TO FIRE.

    A sensitivity analysis that never moves is indistinguishable from one that is broken,
    and this suite has already caught that once: the first band rule asked whether the
    interval reached past BOTH edges of 0.75-1.25, which a null-excluding interval never
    can, so every rating came back "not threshold-sensitive". It looked like a reassuring
    result and it was a dead branch. So this asserts BOTH directions -- one interval whose
    letter moves with the threshold, and one whose letter does not.
    """
    print("\n[9] NAMED THRESHOLD + SENSITIVITY -- and it must be able to move")
    r = ge.derive(clean_object(lo=0.40, hi=0.70), "primary")
    imp = [d for d in r["domains"] if d["domain"] == "imprecision"][0]
    check("imprecision names its threshold",
          imp["thresholds"]["chosen"] == "appreciable_benefit_or_harm_0.75_1.25")
    check("the threshold cites the Handbook section it comes from",
          "14.2.2" in imp["thresholds"]["chosen_source"])
    check("the threshold is declared a DEFAULT, not a clinical finding",
          imp["thresholds"]["chosen_kind"] == "DECLARED_DEFAULT")
    check("absence of a topic-specific threshold is RECORDED, not passed over",
          "topic_specific_threshold_absent" in imp["thresholds"])
    check("optimal information size is declared NOT evaluated",
          "NOT evaluated" in imp["thresholds"]["ois"])
    check("a clear interval is NOT threshold-sensitive",
          r["sensitivity"]["letter_is_threshold_sensitive"] is False,
          r["sensitivity"]["statement"][:90])

    # An interval that excludes the null but still admits a trivially small effect.
    r2 = ge.derive(clean_object(lo=0.70, hi=0.98), "primary")
    check("an interval admitting a trivial effect IS threshold-sensitive",
          r2["sensitivity"]["letter_is_threshold_sensitive"] is True,
          r2["sensitivity"]["statement"][:90])
    check("and it names the letter it would carry instead",
          any(a["certainty_would_be"] == "HIGH"
              for a in r2["sensitivity"]["alternatives"]))
    check("sensitivity does not soften the rating actually issued",
          r2["certainty"] == "MODERATE", "got %s" % r2.get("certainty"))

    # A topic-specific margin must OUTRANK the declared default.
    o = clean_object(lo=0.70, hi=0.98)
    o["results"]["by_outcome"]["primary"]["noninferiority_margin"] = {
        "lo": 0.90, "hi": 1.11, "source": "__control_ synthetic margin"}
    r3 = ge.derive(o, "primary")
    imp3 = [d for d in r3["domains"] if d["domain"] == "imprecision"][0]
    check("a topic-specific margin OUTRANKS the declared default",
          imp3["thresholds"]["chosen_kind"] == "TOPIC_SPECIFIC"
          and imp3["thresholds"]["topic_specific_threshold_held"] is True)


def test_domain_inputs_are_printed_not_summarised():
    """⭐⭐ The inputs must reach the record, or the audit trail is still a footnote."""
    print("\n[10] DOMAIN INPUTS -- the rating must carry what it was rated FROM")
    o = clean_object()
    r = ge.derive(o, "primary")
    rob = [d for d in r["domains"] if d["domain"] == "risk_of_bias"][0]
    check("risk of bias carries per-result inputs", "per_result_inputs" in rob)
    pri = rob.get("per_result_inputs") or {}
    check("inputs name the tool", bool(pri.get("tool")))
    check("inputs list the assessors as an ORDERED LIST, not lab-named keys",
          isinstance(pri.get("assessors"), list))
    check("inputs carry one row per contributing RESULT", pri.get("n_results", 0) >= 1)
    check("each result carries its five RoB 2 domains",
          len((pri["results"][0].get("domains") or [])) == 5)
    check("the unit of assessment is declared PER RESULT",
          "PER RESULT" in rob.get("unit_of_assessment", ""))
    imp = [d for d in r["domains"] if d["domain"] == "imprecision"][0]
    check("imprecision carries the interval it was rated from",
          isinstance(imp.get("interval"), dict) and imp["interval"].get("ci_low") is not None)
    inc = [d for d in r["domains"] if d["domain"] == "inconsistency"][0]
    check("inconsistency names the statistics it read",
          any("heterogeneity" in x for x in inc.get("inputs_read") or []))


def test_no_information_is_not_a_verdict_and_separators_do_not_refuse():
    """Two false refusals this engine actually produced, kept as permanent regressions."""
    print("\n[11] FALSE-REFUSAL REGRESSIONS -- both were real, both are pinned")
    # 1. "SOME CONCERNS" with a space is a verdict, not garbage. `arni-hfref` writes it.
    o = clean_object(rob_overall="SOME CONCERNS")
    r = ge.derive(o, "primary")
    rob = [d for d in r["domains"] if d["domain"] == "risk_of_bias"][0]
    check("a space-separated verdict is READ, not called unreadable",
          rob["state"] == ge.DOWNGRADE, rob["reason"][:100])
    for variant in ("some concerns", "Some-Concerns", "SOME_CONCERNS"):
        rv = ge.derive(clean_object(rob_overall=variant), "primary")
        rb = [d for d in rv["domains"] if d["domain"] == "risk_of_bias"][0]
        check("verdict variant %-16r reads as SOME_CONCERNS" % variant,
              rb["state"] == ge.DOWNGRADE and rb["levels"] == 1)
    # 2. NO_INFORMATION is a RoB 2 response and must REFUSE, not be read as a level.
    rn = ge.derive(clean_object(rob_overall="NO_INFORMATION"), "primary")
    rbn = [d for d in rn["domains"] if d["domain"] == "risk_of_bias"][0]
    check("NO_INFORMATION refuses rather than rating", rbn["state"] == ge.REFUSED)
    check("and it is not called unreadable",
          "NO INFORMATION" in rbn["reason"] and "unreadable" not in rbn["reason"])
    check("and it says it is about the documents, not the trial",
          "not a finding against the trial" in rbn["reason"])


def test_bound_is_reported_but_never_becomes_a_rating():
    """⭐⭐⭐ THE BOUND MUST INFORM WITHOUT ASSERTING.

    A refusal is not the same as knowing nothing: with four domains resolved the certainty
    is bounded even though it is not determined. Reporting that bound is the
    methodologically consistent way to close a gap without manufacturing a letter.

    ⚠️ THE FAILURE MODE THIS GUARDS IS THE BOUND BEING PROMOTED TO A RATING. That is
    exactly the pressure Mahmood's constraint names -- a control that made it easier to
    publish a letter than to withhold one would be the wrong control -- so every assertion
    below checks that `rated` is still False and `certainty` is still None WHILE the bound
    is present.
    """
    print("\n[13] CERTAINTY BOUNDS -- informative, and still not a rating")
    o = _strip(clean_object(), "results.by_outcome.primary.grade")   # indirectness absent
    r = ge.derive(o, "primary")
    b = r.get("certainty_bounds") or {}
    check("a refusal carries a bound", bool(b))
    check("the bound does NOT become a rating",
          r["rated"] is False and r.get("certainty") is None,
          "rated=%s certainty=%s" % (r["rated"], r.get("certainty")))
    # ONE unresolved domain can cost AT MOST TWO LEVELS under GRADE, so the worst case
    # from HIGH is LOW, not VERY LOW. The first version of this check expected VERY_LOW
    # and the suite caught it -- the control was wrong and the engine was right, which is
    # the direction a control is supposed to be able to fail in.
    check("the bound names both ends",
          b.get("best_case") == "HIGH" and b.get("worst_case") == "LOW",
          "%s..%s" % (b.get("best_case"), b.get("worst_case")))
    check("one unresolved domain costs at most two levels",
          b.get("max_further_downgrade") == 2)
    check("the bound names which domains are unresolved",
          b.get("unresolved_domains") == ["indirectness"])
    check("the bound says explicitly it is not a rating",
          "not a certainty rating" in b.get("what_this_is_not", ""))
    check("an unentailed bound does NOT claim entailment", b.get("entailed") is False)

    # ⭐ ENTAILMENT: when the resolved domains already floor the ladder, the unresolved one
    # cannot change the answer. Three real corpus results are in this position.
    o2 = _strip(clean_object(rob_overall="HIGH", lo=0.7, hi=1.4, i2=90.0, tau2=0.4),
                "results.by_outcome.primary.grade")
    r2 = ge.derive(o2, "primary")
    b2 = r2.get("certainty_bounds") or {}
    check("floored evidence -> the letter is ENTAILED", b2.get("entailed") is True,
          "%s..%s" % (b2.get("best_case"), b2.get("worst_case")))
    check("entailment collapses the bound to one letter",
          b2.get("best_case") == b2.get("worst_case") == "VERY_LOW")
    check("EVEN ENTAILED, no letter is published",
          r2["rated"] is False and r2.get("certainty") is None,
          "rated=%s certainty=%s" % (r2["rated"], r2.get("certainty")))
    check("and the entailment says why the refusal cannot change it",
          "cannot change it" in b2.get("statement", ""))

    # And a fully resolved object must NOT carry a bound -- it carries a rating.
    r3 = ge.derive(clean_object(), "primary")
    check("a RATED result carries no bound (it has an answer)",
          not r3.get("certainty_bounds") and r3["rated"] is True)


def test_incoherent_inputs_refuse_rather_than_rate():
    """⭐ THE THIRD STATE: inputs that are all PRESENT and cannot all be TRUE.

    Found on 2026-08-30 by an adversarial case set written by a different model against
    the engine's behaviour. The engine rated a confidence interval stored as 1.4 to 0.8 --
    transposed -- as HIGH certainty, with imprecision recorded as no downgrade, because
    every field a rating needs was present and nothing asked whether they were consistent.

    ⚠️ Refusing for ABSENCE was already covered. This is the harder case and the more
    dangerous one: the output looks fully supported, with a complete audit trail sitting
    underneath a contradiction.
    """
    print("\n[12] INCOHERENT INPUT -- present, contradictory, and must not be rated")
    base = clean_object()

    def mutate(**kw):
        o = json.loads(json.dumps(base))
        r = o["results"]["by_outcome"]["primary"]
        for path, val in kw.items():
            if path.startswith("pooled_"):
                r["pooled"][path[len("pooled_"):]] = val
            elif path.startswith("het_"):
                r["heterogeneity"][path[len("het_"):]] = val
            else:
                r[path] = val
        return o

    cases = [
        ("transposed interval", dict(pooled_ci_low=1.4, pooled_ci_high=0.8)),
        ("point outside its interval", dict(pooled_point=2.0)),
        ("non-positive bound on a ratio", dict(pooled_ci_low=-0.2)),
        ("negative k", dict(k=-3)),
        ("k=0 with an estimate stored", dict(k=0)),
        ("tau2=0 with I2=90%", dict(het_tau2=0.0, het_i2=90.0)),
        ("I2=0 with tau2=0.4", dict(het_i2=0.0, het_tau2=0.4)),
        ("I2 above 100%", dict(het_i2=140.0)),
    ]
    for label, kw in cases:
        r = ge.derive(mutate(**kw), "primary")
        check("%-32s -> no letter" % label,
              r["rated"] is False and r.get("certainty") is None,
              "state=%s certainty=%s" % (r.get("state"), r.get("certainty")))
        check("%-32s -> named as a DATA DEFECT" % label,
              r.get("state") == "INCOHERENT_INPUT"
              and bool(r.get("coherence_violations")))

    # ⚠️ AND THE OTHER DIRECTION, which is what stops this becoming a gate that fires
    # everywhere: the clean fixture must still rate. A coherence check that refuses good
    # data is the same defect as one that passes bad data, wearing a safer-looking face.
    ok = ge.derive(base, "primary")
    check("a COHERENT object is still rated", ok["rated"] is True,
          "state=%s" % ok.get("state"))
    check("and carries no coherence violations",
          not ok.get("coherence_violations"))


def main():
    print("KNOWN-ANSWER CONTROL: ssot/grade_engine.py")
    print("fixtures are synthetic, namespaced %s*, and touch no corpus object"
          % CONTROL_PREFIX)
    for t in (test_positive_control_earns_a_letter,
              test_every_missing_input_refuses,
              test_refusal_is_never_a_falsy_render,
              test_refusal_stays_refused_under_restoration,
              test_withdrawn_pool_never_carries_a_letter,
              test_publication_bias_says_not_assessable_not_undetected,
              test_dual_assessors_agreeing_is_not_pending,
              test_threshold_is_named_and_sensitivity_can_move,
              test_domain_inputs_are_printed_not_summarised,
              test_no_information_is_not_a_verdict_and_separators_do_not_refuse,
              test_bound_is_reported_but_never_becomes_a_rating,
              test_incoherent_inputs_refuse_rather_than_rate,
              test_plant_detects_a_broken_engine):
        try:
            t()
        except Exception:
            FAILURES.append(t.__name__)
            print("  ERROR in %s" % t.__name__)
            traceback.print_exc()
    print("\n%s" % ("=" * 66))
    if FAILURES:
        print("RESULT: FAIL -- %d check(s) failed:" % len(FAILURES))
        for f in FAILURES:
            print("   - %s" % f)
        return 1
    print("RESULT: PASS -- all controls held, and the plant was detected.")
    return 0


if __name__ == "__main__":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.exit(main())
