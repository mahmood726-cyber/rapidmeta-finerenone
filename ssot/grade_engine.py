# -*- coding: utf-8 -*-
"""DERIVE a GRADE certainty rating PER POOLED RESULT from the SSOT object, or REFUSE.

WHY THIS FILE EXISTS. Six blinded judges, three model families, both presentation
positions, chose this project's review over a Cochrane review on every axis but one. The
axis they did not give us was formal certainty: we print a pooled estimate and, for most
of them, no rating of how much confidence it deserves.

⚠️ THE DENOMINATOR, AND AN EARLIER VERSION OF THIS FILE GOT IT WRONG. This docstring first
said "27 of 154 pooled results -- 17.5%", counting every `by_outcome` record that held a
pooled block. 103 of those 157 records are WITHDRAWN pools, and a withdrawn estimate is
not something a certainty rating can be ABOUT, so it cannot be in the denominator. The
live figure is 29 of 54 (54%), and one withdrawn pool still carries a rating it should
not. The wrong number was not a typo: it came from counting the presence of a field
instead of enumerating the KINDS of thing being counted, which is this project's most
repeated measurement defect and is worth carrying at the top of the module that exists to
count things carefully.

The 27 that exist are GOOD. They are also HAND-WRITTEN, one `apply_<topic>_grade.py`
script at a time. A hand-written twenty-eighth would move the number by 0.6 points and
would not survive a regeneration, which is the acceptance test that matters here: a page
that cannot be rebuilt into its winning state was never really won. So this module
DERIVES the same structure the hand-written records use, from the object, for every
pooled result, every build.

⚠️ WHAT IT WILL NOT DO, AND THIS IS THE WHOLE POINT.

It never defaults. A domain whose input this object does not hold returns REFUSED, and a
result with any REFUSED domain gets NO overall certainty -- not "moderate", not "low",
not an em dash. A default is an assertion the object never made, and this project found
35 sites making one. `LOW` is not a safe default either: rating an unassessed body of
evidence DOWN is still inventing a finding, it merely invents a modest-sounding one.

FOUR DOMAIN STATES, BECAUSE THREE IS NOT ENOUGH.

    NO_DOWNGRADE    assessed, nothing found. A claim.
    DOWNGRADE       assessed, rated down N levels, with the reason.
    NOT_ASSESSABLE  the assessment is STRUCTURALLY impossible here and that is a settled
                    methodological fact, not a gap in our data -- funnel-plot asymmetry
                    below ten studies is the standing case. It carries no downgrade and
                    it does NOT block an overall rating.
    REFUSED         WE do not hold the input. It blocks the overall rating.

⭐ THE DISTINCTION BETWEEN THE LAST TWO IS THE MODULE'S REASON FOR EXISTING. "Cannot be
assessed by anyone" and "was not assessed by us" are different sentences about the world,
and collapsing them is how a limitation becomes a finding. Published reviews routinely
say "no evidence of publication bias" where the honest statement is that no test with
power to find it was available; we say which one it is.

HANDBOOK AUTHORITY, VERIFIED RATHER THAN RECALLED.

    Cochrane Handbook for Systematic Reviews of Interventions, version 6.5.1 (2025)
    ch 14  Completing 'Summary of findings' tables and grading the certainty of the
           evidence                                        [last updated March 2025]
    ch 13  Assessing risk of bias due to missing evidence in a meta-analysis
    ch 10  Analysing data and undertaking meta-analyses     [last updated Nov 2024]
    ch 8   Assessing risk of bias in a randomized trial

    s13.3.4.4  "Tests for funnel plot asymmetry", which carries the rule this module
               leans on hardest, verbatim from the publisher on 2026-08-30:

        "As a rule of thumb, tests for funnel plot asymmetry should be used only when
         there are at least 10 studies included in the meta-analysis, because when there
         are fewer studies the power of the tests is low."

⚠️ THAT SECTION NUMBER IS A CORRECTION. Sixteen stored objects and eight apply-scripts
in this corpus cite s13.3.5.4 for that rule -- 26 files, and NOT ONE cites 13.3.4.4.
There is no s13.3.5.4; s13.3.5 is "Reaching an overall judgement about risk of bias due
to missing evidence" and has no subsections. The rule is real and the citation attached
to it corpus-wide is not, which is the same defect class this project already recorded
against s23.1 and s23.3.4 in `preconditions.py`. It was found by FETCHING the chapter
while writing this file, not by re-reading the text that carried it.

RATING UP IS NOT IMPLEMENTED, DELIBERATELY. Rating up for a large effect, a dose-response
gradient or opposing plausible confounding applies to evidence that started below HIGH --
observational evidence. Every body of evidence in this corpus is randomized trials, which
start HIGH and cannot be rated above it. A module that offered the move would be offering
one that is never legitimate here.
"""
from __future__ import annotations

try:
    from rob_block import rob_block, rob_adjudication_state
except ImportError:  # imported as a package from outside ssot/
    from .rob_block import rob_block, rob_adjudication_state

HANDBOOK_VERSION = "6.5.1"
HANDBOOK_REF = ("Higgins JPT, Thomas J, Chandler J, Cumpston M, Li T, Page MJ, Welch VA "
                "(editors). Cochrane Handbook for Systematic Reviews of Interventions "
                "version 6.5.1. Cochrane, 2025.")
HANDBOOK_VERIFIED_ON = "2026-08-30"
HANDBOOK_VERIFIED_HOW = (
    "Chapter 13 was fetched from the publisher on 2026-08-30 and its section numbering "
    "read off the chapter itself. That check corrected the section this corpus cites for "
    "the ten-study rule, from 13.3.5.4 (which does not exist) to 13.3.4.4.")

FUNNEL_MIN_K = 10
FUNNEL_RULE = ("Handbook ch 13 s13.3.4.4: \"As a rule of thumb, tests for funnel plot "
               "asymmetry should be used only when there are at least 10 studies "
               "included in the meta-analysis, because when there are fewer studies the "
               "power of the tests is low.\"")

DOMAINS = ("risk_of_bias", "inconsistency", "indirectness", "imprecision",
           "publication_bias")

# ⚠️ SEPARATOR-INSENSITIVE, AND THIS IS NOT FUSSINESS. The first version of the verdict
# guard tested membership against the literal "SOME_CONCERNS", and `arni-hfref` stores
# "SOME CONCERNS" with a space. Twenty fully assessed results were reported as holding an
# unreadable verdict -- a FALSE REFUSAL, in the exact direction this project's detectors
# are measurably biased. It is also the SECOND time this corpus has produced this defect:
# an earlier verdict guard read 0 hits on 107 of 107 packets because its separator class
# was `[_ ]` while the corpus wrote hyphens. Normalise, then compare.
NO_INFO = "NO_INFORMATION"
KNOWN_VERDICTS = {"LOW", "SOME_CONCERNS", "HIGH", NO_INFO}


def _verdict(v):
    """Normalise a stored RoB 2 overall judgement. Unknown values stay unknown."""
    t = str(v or "").strip().upper().replace("-", "_").replace(" ", "_")
    while "__" in t:
        t = t.replace("__", "_")
    if t in ("NI", "NO_INFO", "NOINFORMATION"):
        return NO_INFO
    if t in ("SOME_CONCERNS", "SOMECONCERNS", "SOME_CONCERN"):
        return "SOME_CONCERNS"
    return t

NO_DOWNGRADE = "NO_DOWNGRADE"
DOWNGRADE = "DOWNGRADE"
NOT_ASSESSABLE = "NOT_ASSESSABLE"
REFUSED = "REFUSED"

LADDER = ["HIGH", "MODERATE", "LOW", "VERY_LOW"]

# Measures whose null is 1 rather than 0. Read from the stored measure string; an
# unrecognised measure REFUSES rather than assuming a scale, because guessing the null
# is guessing the direction of the finding.
RATIO_MEASURES = {"RR", "OR", "HR", "IRR", "RATE_RATIO", "RISK_RATIO", "ODDS_RATIO",
                  "HAZARD_RATIO", "PETO_OR", "ROM"}
DIFF_MEASURES = {"MD", "SMD", "RD", "MEAN_DIFFERENCE", "RISK_DIFFERENCE",
                 "STANDARDISED_MEAN_DIFFERENCE", "STANDARDIZED_MEAN_DIFFERENCE"}


def coherence_violations(res):
    """⚠️ INPUTS THAT CANNOT ALL BE TRUE. Found by an adversarial pass, 2026-08-30.

    The engine was built around "derive or refuse", and the refuse branch only ever fired
    for a MISSING input. A set of inputs that are all PRESENT and mutually impossible went
    straight through: a confidence interval stored as 1.4 to 0.8 -- transposed -- was rated
    HIGH certainty, with imprecision recorded as no downgrade, because every value the
    rating needed was there and nothing asked whether they could all hold at once.

    ⭐ THAT IS A THIRD STATE THIS MODULE DID NOT HAVE. "We hold it" and "we do not hold it"
    are not the whole space; "we hold something that cannot be right" is a different fact
    from both, and rating it is worse than refusing for absence, because the output looks
    fully supported. An incoherent input refused is a data finding; an incoherent input
    rated is a false claim with a full audit trail underneath it.

    Credit where due: this class was found by an adversarial case set written by a
    different model against the engine's public behaviour. Eleven of its nineteen cases
    disagreed with the engine; on adjudication, six were this defect and five were the
    other model mis-predicting the named-threshold rule. Both halves are recorded, because
    a report that kept only the hits would overstate what the pass was worth.
    """
    v = []
    k = _num(res.get("k"))
    pooled = res.get("pooled") if isinstance(res.get("pooled"), dict) else {}
    lo, hi = _num(pooled.get("ci_low")), _num(pooled.get("ci_high"))
    pt = _num(pooled.get("point"))
    measure = str(pooled.get("measure") or res.get("measure") or "").strip().upper()
    ratio = measure.replace(" ", "_").replace("-", "_") in RATIO_MEASURES
    has_estimate = pt is not None or lo is not None or hi is not None

    if lo is not None and hi is not None and lo > hi:
        v.append("the confidence interval is TRANSPOSED: ci_low %g is greater than "
                 "ci_high %g" % (lo, hi))
    if pt is not None and lo is not None and hi is not None and lo <= hi:
        if not (lo <= pt <= hi):
            v.append("the point estimate %g lies OUTSIDE its own interval %g to %g"
                     % (pt, lo, hi))
    if ratio:
        for nm, val in (("ci_low", lo), ("ci_high", hi), ("point", pt)):
            if val is not None and val <= 0:
                v.append("%s is %g on a RATIO measure (%s), where every value must be "
                         "strictly positive" % (nm, val, measure))
    if k is not None and k < 0:
        v.append("k is %g -- a pool cannot contain a negative number of studies" % k)
    if k is not None and k == 0 and has_estimate:
        v.append("k is 0 while a pooled estimate is stored: an estimate cannot be "
                 "computed from no contributing studies")

    het = res.get("heterogeneity") if isinstance(res.get("heterogeneity"), dict) else {}
    i2 = _num(het.get("i2"))
    if i2 is None:
        i2 = _num(het.get("i2_percent"))
    if i2 is None:
        i2 = _num(het.get("i2_pct"))
    tau2 = _num(het.get("tau2"))
    if i2 is not None and tau2 is not None:
        i2p = i2 * 100.0 if i2 <= 1.0 else i2
        # tau-squared and I-squared are two readings of the same quantity: I-squared is
        # the share of total variance that tau-squared accounts for. One being exactly
        # zero while the other is large is not a borderline call, it is a contradiction,
        # and it usually means the two were written by different code paths.
        if tau2 == 0 and i2p >= 50:
            v.append("tau-squared is exactly 0 while I-squared is %.0f%%: I-squared is the "
                     "share of variance tau-squared accounts for, so these cannot both "
                     "hold" % i2p)
        if i2p == 0 and tau2 > 0.05:
            v.append("I-squared is 0%% while tau-squared is %g: the same contradiction "
                     "in the other direction" % tau2)
    if i2 is not None:
        i2p = i2 * 100.0 if i2 <= 1.0 else i2
        if i2p < 0 or i2p > 100:
            v.append("I-squared is %g%%, outside the 0 to 100 range it is defined on"
                     % i2p)
    return v


def _dom(domain, state, reason, levels=0, move=None, inputs_read=None,
         inputs_missing=None):
    return {"domain": domain, "state": state, "levels": levels,
            "move": move or _move_text(state, levels),
            "reason": reason,
            "inputs_read": sorted(inputs_read or []),
            "inputs_missing": sorted(inputs_missing or [])}


def _move_text(state, levels):
    if state == NO_DOWNGRADE:
        return "no downgrade"
    if state == DOWNGRADE:
        return "down %d level(s)" % levels
    if state == NOT_ASSESSABLE:
        return "NOT ASSESSABLE -- no rating applied"
    return "REFUSED -- input not held by this object"


def _num(v):
    return v if isinstance(v, (int, float)) and not isinstance(v, bool) else None


# --------------------------------------------------------------------------- domains

def d_risk_of_bias(canon, oid, res):
    """Reads the SAME normalised RoB store the risk-of-bias section renders.

    It does not re-implement RoB 2. `rob_block` already resolves the two container
    schemas and the assessor identity, and `rob_adjudication_state` already answers which
    outcomes the assessment actually covers -- a set that is NOT the set of outcomes
    GRADE rates, which is precisely the trap this reads it to avoid.
    """
    st = rob_adjudication_state(canon)
    if not st.get("assessed"):
        return _dom("risk_of_bias", REFUSED,
                    "This object holds no risk-of-bias assessment, so the domain cannot "
                    "be rated. GRADE rates certainty per outcome by aggregating the "
                    "risk-of-bias judgements of the results contributing to it "
                    "(Handbook ch 14, on ch 8), and there are none here to aggregate.",
                    inputs_missing=["risk_of_bias"])

    covered = st.get("outcomes_assessed") or set()
    b = rob_block(canon) or {}
    trials = [t for t in (b.get("trials") or []) if t.get("outcome") == oid]
    if not trials and oid not in covered:
        # The single-outcome topics store RoB rows without an outcome key. Only treat the
        # assessment as covering this result when the object holds exactly one outcome --
        # otherwise attributing it here is the assumption, not the data.
        n_out = len((canon.get("results") or {}).get("by_outcome") or {})
        if n_out == 1 and (b.get("trials") or []):
            trials = list(b.get("trials") or [])
        else:
            return _dom("risk_of_bias", REFUSED,
                        "A risk-of-bias assessment exists on this object but it does not "
                        "cover this outcome (%s). It covers: %s. Carrying a neighbouring "
                        "outcome's judgement across would be a rating this review never "
                        "made." % (oid, ", ".join(sorted(covered)) or "no named outcome"),
                        inputs_missing=["risk_of_bias.by_outcome[%s]" % oid])

    # `rob_block` normalises each result to an ORDERED LIST of per-assessor overall
    # judgements in `overall`, with `overall_agreed` saying whether they match. Read that
    # shape rather than a per-judgement key: the first version of this function looked for
    # `judgements[].OVERALL`, found nothing, and refused two results that are fully
    # assessed. A refusal produced by reading the wrong field is a false refusal, and this
    # project's detectors have a measured bias in exactly that direction.
    verdicts, unresolved, malformed, no_info = [], [], [], []
    for t in trials:
        # ⚠️ FLATTEN AND TYPE-CHECK. `overall` is a list of per-assessor strings, but a
        # store that nests it one level deeper arrives as [["LOW","HIGH"]] -- and
        # str() of that list contains the substring "HIGH", so a naive read returns a
        # confident two-level downgrade from a value it never understood. The control
        # found exactly that. Anything that is not a recognised verdict string is
        # collected as MALFORMED and refused, never coerced.
        ov = t.get("overall")
        ov = [ov] if isinstance(ov, str) else list(ov or [])
        flat = []
        for v in ov:
            if isinstance(v, str):
                flat.append(_verdict(v))
            elif isinstance(v, (list, tuple)):
                flat.extend(_verdict(x) for x in v if isinstance(x, str))
            elif v is not None:
                malformed.append((t.get("id") or t.get("trial"), repr(v)[:60]))
        bad = [v for v in flat if v not in KNOWN_VERDICTS]
        if bad:
            malformed.extend((t.get("id") or t.get("trial"), b[:60]) for b in bad)
        ov = [v for v in flat if v not in bad]
        if not ov:
            continue
        # NO_INFORMATION is a RoB 2 response, not a verdict. An assessor who records it
        # has said they could not tell -- which is a fact about the evidence available,
        # and it is not a level GRADE can aggregate.
        if any(v == NO_INFO for v in ov):
            no_info.append((t.get("id") or t.get("trial"), "/".join(ov)))
            continue
        if len(ov) > 1 and not t.get("overall_agreed") and len(set(ov)) > 1:
            unresolved.append((t.get("id") or t.get("trial"), ov))
        else:
            verdicts.append(ov[0])
    if malformed:
        return _dom("risk_of_bias", REFUSED,
                    "This object holds risk-of-bias rows for this outcome whose OVERALL "
                    "judgement is not a recognised RoB 2 verdict: %s. A value that cannot "
                    "be read is refused rather than interpreted -- reading it loosely is "
                    "how a store nobody understood becomes a rating somebody trusted."
                    % "; ".join("%s=%s" % (i, v) for i, v in malformed[:4]),
                    inputs_missing=["a readable risk_of_bias OVERALL judgement"])

    # NO_INFORMATION IS A FINDING, NOT A FAULT, AND IT IS ITS OWN REFUSAL. An assessor
    # who records it has said the source documents do not answer the question. That is a
    # limit on what could be REACHED, not a judgement against the trial -- a distinction
    # this project exists to make -- and it is not a level GRADE can aggregate.
    if no_info:
        return _dom("risk_of_bias", REFUSED,
                    "An assessor recorded NO INFORMATION as the overall risk-of-bias "
                    "judgement for %d contributing result(s) (%s). That is a statement "
                    "about what the source documents contain, not a finding against the "
                    "trial, and it is not a verdict this domain can aggregate. Rating the "
                    "domain anyway would convert 'we could not find out' into 'we found "
                    "out and it was acceptable'."
                    % (len(no_info), "; ".join("%s: %s" % (i, v) for i, v in no_info[:4])),
                    inputs_missing=["a risk-of-bias judgement that is not NO_INFORMATION"])

    if not verdicts and not unresolved:
        return _dom("risk_of_bias", REFUSED,
                    "Risk-of-bias rows exist for this outcome but none carries an OVERALL "
                    "judgement, so there is nothing to aggregate.",
                    inputs_missing=["risk_of_bias overall judgement"])

    # ⭐ THREE STATES, NOT TWO. "Two assessors, unadjudicated" is not automatically
    # PENDING: where both assessors reached the SAME overall verdict there is nothing to
    # adjudicate, and refusing there would withhold a rating this review has in fact
    # earned. It is PENDING only where they DISAGREE and no adjudication record exists --
    # and then it is refused, because a certainty rating cannot be more final than the
    # risk-of-bias assessment it reads.
    if unresolved and not st.get("adjudicated"):
        return _dom("risk_of_bias", REFUSED,
                    "Two assessors reached DIFFERENT overall risk-of-bias verdicts on %d "
                    "contributing result(s) (%s) and the disagreement has not been "
                    "adjudicated. This is PENDING, which is a different fact from 'not "
                    "assessed': the work was done, it is on the object, and it is not "
                    "final." % (len(unresolved),
                                "; ".join("%s: %s" % (i, "/".join(v))
                                          for i, v in unresolved)),
                    inputs_missing=["risk_of_bias adjudication"])

    n = len(verdicts)
    high = sum(1 for v in verdicts if "HIGH" in v)
    some = sum(1 for v in verdicts if "SOME" in v)
    low = sum(1 for v in verdicts if v.startswith("LOW"))
    read = ["risk_of_bias", "%d result-level judgement(s)" % n]

    def _out(state, levels, why):
        d = _dom("risk_of_bias", state, why, levels=levels, inputs_read=read)
        d["per_result_inputs"] = _rob_inputs(b, trials)
        d["unit_of_assessment"] = (
            "PER RESULT. RoB 2 asks for a judgement about a specific RESULT, not about a "
            "trial and not about an outcome in general, because a trial can be at low risk "
            "for one of its results and high for another. The judgements below are "
            "therefore listed one per contributing result, each with the five domain "
            "responses that produced it and each assessor's answer shown separately. A "
            "reader can disagree with D3 on one trial without discarding the rating.")
        return d

    if high:
        return _out(DOWNGRADE, 2 if high == n else 1,
                    "%d of %d contributing result(s) are at HIGH risk of bias (%d some "
                    "concerns, %d low). Handbook ch 14 rates the domain on the results "
                    "that contribute to this estimate." % (high, n, some, low))
    if some:
        return _out(DOWNGRADE, 1,
                    "%d of %d contributing result(s) carry SOME CONCERNS and none is at "
                    "high risk of bias (%d low)." % (some, n, low))
    return _out(NO_DOWNGRADE, 0,
                "All %d contributing result(s) are at LOW risk of bias on RoB 2." % n)


def _rob_inputs(block, trials):
    """⭐⭐ THE DOMAIN INPUTS, PRINTED.

    A Cochrane certainty rating is a letter and a footnote, and a reader cannot check it:
    the footnote says "downgraded for risk of bias" and the evidence for that sits in a
    supplementary file or nowhere. This returns what the judgement was made FROM -- every
    contributing result, every RoB 2 domain, every assessor's answer, and whether they
    agreed -- so the audit trail becomes the thing a reader scores rather than something
    they have to take on trust.

    Assessors are returned as an ORDERED LIST with their model families, never under
    lab-named keys: the identity bug that rendered a partial two-assessor panel cannot
    recur if no lab name is a key.
    """
    assessors = [{"n": a.get("n"), "name": a.get("name"),
                  "model_family": a.get("model_family")}
                 for a in (block.get("assessors") or [])]
    rows = []
    for t in trials:
        doms = []
        for d in (t.get("domains") or []):
            js = [x for x in (d.get("judgements") or []) if x]
            doms.append({"domain": d.get("domain"),
                         "domain_name": d.get("domain_name"),
                         "per_assessor": js,
                         "agreed": d.get("agreed"),
                         "reason": d.get("reason")})
        ov = t.get("overall")
        ov = [ov] if isinstance(ov, str) else list(ov or [])
        rows.append({"result": t.get("trial") or t.get("id"),
                     "id": t.get("id"),
                     "outcome": t.get("outcome"),
                     "domains": doms,
                     "overall_per_assessor": [str(x) for x in ov if x],
                     "overall_agreed": t.get("overall_agreed")})
    return {"tool": block.get("tool"), "version": block.get("version"),
            "assessors": assessors, "n_assessors": len(assessors),
            "results": rows, "n_results": len(rows)}


def d_inconsistency(canon, oid, res):
    k = _num(res.get("k"))
    if k is None:
        return _dom("inconsistency", REFUSED,
                    "The number of contributing studies is not recorded, so consistency "
                    "between them cannot be assessed.", inputs_missing=["k"])
    if k < 2:
        return _dom("inconsistency", NOT_ASSESSABLE,
                    "k = %d. Consistency is a property of two or more estimates; with "
                    "fewer there is nothing to be consistent with. This is a structural "
                    "fact, not a gap in this review's data." % k,
                    inputs_read=["k"])

    het = res.get("heterogeneity")
    if not isinstance(het, dict):
        return _dom("inconsistency", REFUSED,
                    "k = %d but this object holds no heterogeneity statistics for this "
                    "pool, so inconsistency cannot be rated." % k,
                    inputs_missing=["heterogeneity"])

    i2 = _num(het.get("i2"))
    if i2 is None:
        i2 = _num(het.get("i2_percent"))
    if i2 is None:
        i2 = _num(het.get("i2_pct"))
    tau2 = _num(het.get("tau2"))
    q, df = _num(het.get("q")), _num(het.get("df"))
    if i2 is None and tau2 is None:
        return _dom("inconsistency", REFUSED,
                    "A heterogeneity block exists but holds neither I-squared nor "
                    "tau-squared, so there is no statistic to rate.",
                    inputs_missing=["heterogeneity.i2", "heterogeneity.tau2"])

    # I2 is stored on two scales in this corpus -- 0-1 and 0-100. Normalise explicitly
    # rather than letting a 0.85 be read as 0.85% or an 85 as 8500%.
    i2_pct = None
    if i2 is not None:
        i2_pct = i2 * 100.0 if i2 <= 1.0 else i2

    read = ["k"] + ["heterogeneity." + x for x in ("i2", "tau2", "q", "df")
                    if _num(het.get(x)) is not None]
    stat = "I-squared %s, tau-squared %s, Q %s on %s df" % (
        ("%.1f%%" % i2_pct) if i2_pct is not None else "not held",
        ("%.4f" % tau2) if tau2 is not None else "not held",
        ("%.4f" % q) if q is not None else "not held",
        ("%d" % df) if df is not None else "?")

    low_k_caveat = ""
    if k <= 3:
        low_k_caveat = (" AT k = %d THE STATISTIC IS NEARLY POWERLESS: I-squared and Q "
                        "have very little ability to detect heterogeneity with this few "
                        "studies, so a low value is weak evidence of consistency rather "
                        "than evidence of it (Handbook s10.10.1, which distinguishes "
                        "clinical and methodological diversity from the statistic)." % k)

    if (tau2 is not None and tau2 == 0) or (i2_pct is not None and i2_pct < 40):
        return _dom("inconsistency", NO_DOWNGRADE,
                    "%s. No downgrade: the contributing estimates do not disagree beyond "
                    "chance.%s" % (stat, low_k_caveat), inputs_read=read)
    if i2_pct is not None and i2_pct >= 75:
        return _dom("inconsistency", DOWNGRADE,
                    "%s. Considerable heterogeneity.%s" % (stat, low_k_caveat),
                    levels=2, inputs_read=read)
    return _dom("inconsistency", DOWNGRADE,
                "%s. Substantial heterogeneity between the contributing estimates.%s"
                % (stat, low_k_caveat), levels=1, inputs_read=read)


def d_indirectness(canon, oid, res):
    """⚠️ THIS DOMAIN ALMOST ALWAYS REFUSES, AND THAT IS THE CORRECT ANSWER.

    Indirectness asks whether the population, intervention, comparator and outcome of the
    contributing trials match the question being asked. That is a comparison between two
    PICOs, and a machine that has only one of them cannot make it. The corpus's own best
    hand-written example is the proof: rating `agyw-hiv-prep-review` DOWN for indirectness
    required noticing that a review named for adolescent girls contained two trials whose
    registrations both set a minimum age of 18. Nothing in the pooled result says that.

    So this reads an EXPLICIT stored indirectness judgement if the object carries one, and
    otherwise refuses by name. Returning "no downgrade" here would be the single most
    dangerous default available, because it reads as a finding of directness.
    """
    for loc, blk in (("results.by_outcome.%s.grade.indirectness" % oid,
                      (res.get("grade") or {}).get("indirectness")),
                     ("grade.by_outcome.%s.indirectness" % oid,
                      ((canon.get("grade") or {}).get("by_outcome") or {})
                      .get(oid, {}).get("indirectness"))):
        if isinstance(blk, dict) and blk.get("state") in (NO_DOWNGRADE, DOWNGRADE):
            return _dom("indirectness", blk["state"],
                        blk.get("reason") or "Stored judgement.",
                        levels=int(blk.get("levels") or 0), inputs_read=[loc])
    # ⭐ THE REFUSAL CARRIES THE MATERIAL THAT WOULD SETTLE IT.
    #
    # Where the contributing trials hold their registry-quoted eligibility, the refusal
    # names the review's question and quotes that eligibility, so a reader can make the
    # comparison this review has not formally made. That is strictly more than a bare
    # refusal and strictly less than a rating, which is exactly what is true.
    #
    # ⚠️ AND IT IS NOT PARSED. Registered eligibility is free registry prose, and deciding
    # directness from it by pattern-matching would be a judgement over an open vocabulary
    # dressed as a derivation -- the defect this project has already met in a regex, a
    # path list, a label matcher, a proxy join and an estimand check. The one case that
    # motivates the domain proves the point: `agyw-hiv-prep-review` is named for
    # adolescent girls and both its trials register a MINIMUM AGE OF 18, which is a
    # mismatch between the trials and the TITLE while the stored question says only
    # "in women". No regex settles which of those the rating should answer to.
    q = canon.get("question")
    q = q if isinstance(q, str) else None
    quoted = []
    for t in (res.get("per_trial") or []):
        if isinstance(t, dict) and t.get("registered_eligibility"):
            quoted.append({"trial": t.get("trial_id") or t.get("trial"),
                           "nct": t.get("nct"),
                           "registered_conditions": t.get("registered_conditions"),
                           "registered_eligibility": t.get("registered_eligibility"),
                           "basis": t.get("registered_population_basis")})
    d = _dom("indirectness", REFUSED,
             "Indirectness compares the population, intervention, comparator and outcome "
             "of the contributing trials against the question this review asks. That "
             "comparison is a judgement, not a computation, and this object holds no "
             "recorded indirectness judgement for this outcome. It is REFUSED rather "
             "than rated 'no downgrade', because 'no downgrade' would assert the "
             "evidence is directly applicable -- a claim nobody here made.%s"
             % (" The question and the contributing trials' registry-quoted eligibility "
                "are attached below so a reader can make the comparison this review has "
                "not." if quoted else ""),
             inputs_missing=["explicit indirectness judgement for %s" % oid])
    if q:
        d["question_asked"] = q
    if quoted:
        d["registered_eligibility_of_contributing_trials"] = quoted
    return d


    # ------------------------------------------------------------------ thresholds
#
# ⭐⭐ THE DECISION THRESHOLD, NAMED. THIS IS THE LEVER MOST REVIEWS LEAVE UNPULLED.
#
# Almost every published review downgrades for imprecision without ever saying what
# threshold it judged the interval against. "The confidence interval was wide" is not a
# criterion; it is an impression. A rating produced that way cannot be disagreed with,
# because there is nothing specific to disagree WITH -- which is exactly why it survives
# peer review and exactly why it is worth less than it looks.
#
# So every imprecision rating here names its threshold, cites where the threshold comes
# from, and is reported UNDER EVERY THRESHOLD, not just the chosen one.
#
# AUTHORITY, verified from the publisher on 2026-08-30:
#   Handbook 6.5.1 ch 14 s14.2.2, Domain (4) "Imprecision of results" -- which names the
#   optimal information size and says of appreciable benefit or harm that "an RR of under
#   0.75 or over 1.25 is often suggested as a very rough guide", and that where the
#   interval includes appreciable benefit or harm "downgrading for imprecision may be
#   appropriate even if OIS criteria are met".
#
# ⚠️ "VERY ROUGH GUIDE" IS THE HANDBOOK'S OWN PHRASE AND IT IS CARRIED THROUGH TO THE
# READER. A default dressed as a clinical threshold would be worse than no threshold: it
# would look like this review had decided what matters clinically for this outcome, which
# it has not. Where a topic-specific threshold exists -- a non-inferiority margin, a
# minimal important difference -- it OUTRANKS the default and is named as topic-specific.

APPRECIABLE_RATIO = (0.75, 1.25)
THRESHOLD_AUTHORITY = (
    "Handbook 6.5.1 ch 14 s14.2.2 Domain (4), Imprecision of results: \"an RR of under "
    "0.75 or over 1.25 is often suggested as a very rough guide\" to appreciable benefit "
    "or harm. The Handbook's own words are 'a very rough guide', and this review does not "
    "upgrade that into a clinical threshold it has not established.")

OIS_NOT_EVALUATED = (
    "Optimal information size is NOT evaluated. Handbook s14.2.2 rates precision on the "
    "interval AND on whether the accrued events or participants exceed the OIS, and this "
    "object does not hold the pooled sample size and event count for this outcome. So no "
    "rating here may claim precision is adequate on OIS grounds; a downgrade rests on the "
    "interval alone and could only ever be MORE severe once OIS were known, never less.")


def _thresholds(canon, oid, res, null):
    """The thresholds this result is judged against, strongest provenance first.

    Returns a list of dicts, each with name, lo, hi, source and whether it is a
    topic-specific claim or a declared default. A topic-specific threshold is looked for
    and, when absent, its absence is RECORDED rather than passed over -- a review that
    silently falls back to a default has hidden the most important line on the page.
    """
    out = []
    # 1. A topic-specific threshold, if the object holds one. Non-inferiority margins and
    #    minimal important differences are the two that count.
    for key in ("noninferiority_margin", "ni_margin", "margin",
                "minimal_important_difference", "mid", "decision_threshold"):
        v = res.get(key)
        if isinstance(v, dict):
            lo, hi = _num(v.get("lo")), _num(v.get("hi"))
            if lo is not None or hi is not None:
                out.append({"name": key, "lo": lo, "hi": hi, "kind": "TOPIC_SPECIFIC",
                            "source": str(v.get("source") or "stored on this result")})
        elif _num(v) is not None:
            m = _num(v)
            out.append({"name": key, "lo": (1.0 / m if null == 1.0 and m > 1 else m),
                        "hi": m, "kind": "TOPIC_SPECIFIC",
                        "source": "stored on this result"})
    # 2. The line of no effect. Always applicable, never in dispute.
    out.append({"name": "line_of_no_effect", "lo": null, "hi": null,
                "kind": "STRUCTURAL",
                "source": "The null value of the summary measure. Not a clinical "
                          "judgement -- it is where 'no difference' sits."})
    # 3. The Handbook's rough guide, for ratio measures only. It is meaningless on a
    #    difference scale, and applying it there would be a category error.
    if null == 1.0:
        out.append({"name": "appreciable_benefit_or_harm_0.75_1.25",
                    "lo": APPRECIABLE_RATIO[0], "hi": APPRECIABLE_RATIO[1],
                    "kind": "DECLARED_DEFAULT", "source": THRESHOLD_AUTHORITY})
    return out


def _verdict_under(lo, hi, t):
    """Is the estimate imprecise WHEN JUDGED AGAINST THIS THRESHOLD?

    ⚠️ THE FIRST VERSION OF THIS FUNCTION WAS DEAD CODE AND THE SENSITIVITY REPORT MADE IT
    VISIBLE. It asked whether the interval reached past the threshold on BOTH sides, so for
    a band of 0.75 to 1.25 it could only fire for an interval that already included the
    null -- which the branch above catches first. Every rating therefore came out
    "not threshold-sensitive", which is what a check that cannot fire looks like from the
    outside. The alternative-threshold report is what exposed it: a sensitivity analysis
    that never moves is itself a finding.

    THE CORRECT QUESTION, and it is the one GRADE actually asks: is the interval
    COMPATIBLE WITH AN EFFECT TOO SMALL TO MATTER? A band threshold marks the zone of no
    appreciable effect, so the test is whether the confidence interval OVERLAPS that zone.
    An interval of RR 0.70 to 0.98 excludes the null and still admits a 2% reduction, and
    a rating that called that precise would be reading the point estimate, not the
    interval. A point threshold (the null) keeps the ordinary test: does the interval
    include it.
    """
    tl, th = t.get("lo"), t.get("hi")
    if tl is None and th is None:
        return None
    if tl is not None and th is not None and tl != th:
        overlaps = (lo <= th) and (hi >= tl)
        return {"threshold": t["name"], "kind": t["kind"], "lo": tl, "hi": th,
                "test": "interval overlaps the zone of no appreciable effect",
                "interval_reaches_below": bool(lo <= tl),
                "interval_reaches_above": bool(hi >= th),
                "downgrade": bool(overlaps)}
    point = tl if tl is not None else th
    return {"threshold": t["name"], "kind": t["kind"], "lo": tl, "hi": th,
            "test": "interval includes the threshold value",
            "interval_reaches_below": bool(lo <= point),
            "interval_reaches_above": bool(hi >= point),
            "downgrade": bool(lo <= point <= hi)}


def d_imprecision(canon, oid, res):
    k = _num(res.get("k"))
    pooled = res.get("pooled") if isinstance(res.get("pooled"), dict) else {}
    lo, hi = _num(pooled.get("ci_low")), _num(pooled.get("ci_high"))
    pt = _num(pooled.get("point"))
    if lo is None or hi is None or pt is None:
        return _dom("imprecision", REFUSED,
                    "No pooled point estimate with a confidence interval is held for this "
                    "outcome, so its precision cannot be assessed.",
                    inputs_missing=["pooled.point", "pooled.ci_low", "pooled.ci_high"])

    measure = str(pooled.get("measure") or res.get("measure") or "").strip().upper()
    m = measure.replace(" ", "_").replace("-", "_")
    if m in RATIO_MEASURES:
        null = 1.0
    elif m in DIFF_MEASURES:
        null = 0.0
    else:
        return _dom("imprecision", REFUSED,
                    "The summary measure for this pool is %s, which this module does not "
                    "recognise, so it cannot say where the line of no effect falls. "
                    "Assuming a null would be assuming the direction of the finding."
                    % (("'%s'" % measure) if measure else "not recorded"),
                    inputs_missing=["pooled.measure"])

    crosses = (lo <= null <= hi)
    read = ["pooled.point", "pooled.ci_low", "pooled.ci_high", "pooled.measure", "k"]
    ci_txt = "%s %.4g (%.4g to %.4g)" % (measure, pt, lo, hi)

    hk = res.get("pooled_hartung_knapp")
    hk_note = ""
    if isinstance(hk, dict):
        hlo, hhi = _num(hk.get("ci_low")), _num(hk.get("ci_high"))
        tcrit = _num(hk.get("t_critical"))
        if hlo is not None and hhi is not None:
            hk_crosses = (hlo <= null <= hhi)
            read.append("pooled_hartung_knapp")
            hk_note = (" The Hartung-Knapp interval is %.4g to %.4g%s and it %s the line "
                       "of no effect." % (hlo, hhi,
                                          (" on t = %.4f" % tcrit) if tcrit else "",
                                          "INCLUDES" if hk_crosses else "excludes"))
            if hk_crosses and not crosses:
                hk_note += (" THE TWO INTERVALS DISAGREE ABOUT WHETHER AN EFFECT IS "
                            "DEMONSTRATED, and that disagreement is disclosed rather than "
                            "resolved silently in either direction.")

    # ⭐ EVERY THRESHOLD IS EVALUATED, NOT ONLY THE ONE THAT DECIDES. The chosen threshold
    # sets the rating; the rest are reported beside it so a reader can see how much of the
    # verdict is the evidence and how much is the line we drew.
    ths = _thresholds(canon, oid, res, null)
    evals = [e for e in (_verdict_under(lo, hi, t) for t in ths) if e]
    topic = [t for t in ths if t["kind"] == "TOPIC_SPECIFIC"]
    chosen = (topic[0] if topic
              else next((t for t in ths if t["kind"] == "DECLARED_DEFAULT"), ths[0]))
    chosen_eval = next((e for e in evals if e["threshold"] == chosen["name"]), None)

    sens = {"evaluated_against": evals,
            "chosen": chosen["name"], "chosen_kind": chosen["kind"],
            "chosen_source": chosen["source"],
            "topic_specific_threshold_held": bool(topic),
            "ois": OIS_NOT_EVALUATED}
    if not topic:
        sens["topic_specific_threshold_absent"] = (
            "NO TOPIC-SPECIFIC DECISION THRESHOLD IS HELD for this outcome -- no "
            "non-inferiority margin and no minimal important difference. The rating "
            "therefore rests on a DECLARED DEFAULT and on the line of no effect, and says "
            "so. Supplying a margin for this outcome would make this domain a clinical "
            "judgement instead of a statistical one.")

    def _mk(state, levels, why):
        d = _dom("imprecision", state, why, levels=levels, inputs_read=read)
        d["thresholds"] = sens
        d["interval"] = {"measure": measure, "point": pt, "ci_low": lo, "ci_high": hi,
                         "ci_level": pooled.get("ci_level"), "null": null, "k": k}
        # ⭐ THE SENSITIVITY SENTENCE. What WOULD the rating be under the other lines?
        alt = []
        for e in evals:
            if e["threshold"] == chosen["name"]:
                continue
            alt.append("under %s (%s) it %s" % (
                e["threshold"], e["kind"].lower().replace("_", " "),
                "WOULD be rated down" if e["downgrade"] else "would NOT be rated down"))
        if alt:
            d["reason"] += (" SENSITIVITY OF THIS RATING TO THE THRESHOLD: %s. The rating "
                            "above uses %s. Naming the alternatives is how a reader "
                            "disagrees with a specific step rather than with a letter."
                            % ("; ".join(alt), chosen["name"]))
        return d

    if crosses:
        return _mk(DOWNGRADE, 1,
                   "%s. The interval INCLUDES the line of no effect (%g), so the evidence "
                   "is compatible with no difference.%s %s"
                   % (ci_txt, null, hk_note, OIS_NOT_EVALUATED))
    if chosen_eval and chosen_eval["downgrade"]:
        return _mk(DOWNGRADE, 1,
                   "%s. The interval excludes the line of no effect, but it spans "
                   "appreciable benefit AND appreciable harm as judged against %s "
                   "(%s to %s). Handbook s14.2.2: downgrading may be appropriate here even "
                   "if the optimal information size were met.%s %s"
                   % (ci_txt, chosen["name"], chosen.get("lo"), chosen.get("hi"),
                      hk_note, OIS_NOT_EVALUATED))
    if k is not None and k <= 2:
        return _mk(DOWNGRADE, 1,
                   "%s. The interval excludes the line of no effect and does not span "
                   "appreciable benefit and harm, but k = %d.%s At this k the interval is "
                   "itself estimated from almost no information about between-study "
                   "variance (Handbook s10.10.4.5, which is why the more conservative "
                   "interval is reported beside the ordinary one at small k). %s"
                   % (ci_txt, k, hk_note, OIS_NOT_EVALUATED))
    return _mk(NO_DOWNGRADE, 0,
               "%s. The interval excludes the line of no effect (%g) on k = %s studies "
               "and does not span appreciable benefit and harm under %s.%s %s"
               % (ci_txt, null, k if k is not None else "?", chosen["name"], hk_note,
                  OIS_NOT_EVALUATED))


def d_publication_bias(canon, oid, res):
    """⭐ THE DOMAIN THAT MOST OFTEN GETS A FALSE 'UNDETECTED' IN PUBLISHED REVIEWS.

    With k below ten, a funnel plot and its asymmetry tests have almost no power. Writing
    "no evidence of publication bias" there states an absence that the method could not
    have detected had it been present. This says NOT ASSESSABLE and cites the rule.
    """
    k = _num(res.get("k"))
    if k is None:
        return _dom("publication_bias", REFUSED,
                    "The number of contributing studies is not recorded, so it cannot be "
                    "established whether an asymmetry test is even applicable.",
                    inputs_missing=["k"])
    if k < FUNNEL_MIN_K:
        return _dom("publication_bias", NOT_ASSESSABLE,
                    "k = %d, below the ten studies at which funnel-plot asymmetry can be "
                    "tested with any power. %s THIS IS 'NOT ASSESSABLE', NOT "
                    "'UNDETECTED': no test capable of detecting small-study effects was "
                    "available here, so their absence is not evidence of their absence."
                    % (k, FUNNEL_RULE), inputs_read=["k"])
    for key in ("egger", "peters", "funnel", "small_study_effects",
                "publication_bias_test"):
        blk = res.get(key)
        if isinstance(blk, dict) and blk.get("state") in (NO_DOWNGRADE, DOWNGRADE):
            return _dom("publication_bias", blk["state"],
                        blk.get("reason") or "Stored asymmetry assessment.",
                        levels=int(blk.get("levels") or 0),
                        inputs_read=["k", "results.by_outcome.%s.%s" % (oid, key)])
    return _dom("publication_bias", REFUSED,
                "k = %d, so an asymmetry test IS applicable under %s -- and this object "
                "holds no such test for this pool. The domain is refused rather than "
                "passed: at this k the test is the thing that would settle it, and it has "
                "not been run." % (k, FUNNEL_RULE),
                inputs_missing=["funnel/Egger asymmetry test for %s" % oid])


DERIVERS = (d_risk_of_bias, d_inconsistency, d_indirectness, d_imprecision,
            d_publication_bias)


# ----------------------------------------------------------------------------- rating

def derive(canon, oid):
    """Return a certainty record for one pooled result, or a refusal. Never raises."""
    res = ((canon.get("results") or {}).get("by_outcome") or {}).get(oid)
    if not isinstance(res, dict):
        return {"oid": oid, "rated": False, "state": REFUSED,
                "reason": "No result is stored under this outcome id.",
                "domains": [], "handbook_version": HANDBOOK_VERSION}

    pooled = res.get("pooled") if isinstance(res.get("pooled"), dict) else {}
    if pooled.get("withdrawn"):
        return {"oid": oid, "rated": False, "state": "WITHDRAWN",
                "reason": ("The pooled estimate for this outcome has been WITHDRAWN, so "
                           "there is no estimate for a certainty rating to be about. Any "
                           "rating this object still carries was made about the withdrawn "
                           "estimate and is not shown beside it."),
                "domains": [], "handbook_version": HANDBOOK_VERSION}

    # ⭐ COHERENCE BEFORE DERIVATION. An input set that cannot all be true is refused as a
    # whole, ahead of any domain, because a rating assembled from contradictory values
    # would carry a complete-looking audit trail underneath a false claim -- which is
    # strictly worse than a refusal for a missing field.
    bad = coherence_violations(res)
    if bad:
        return {"oid": oid, "rated": False, "state": "INCOHERENT_INPUT",
                "certainty": None,
                "coherence_violations": bad,
                "reason": (
                    "NO CERTAINTY RATING IS ISSUED, and the reason is not a missing input "
                    "-- it is that the inputs this object holds for this outcome cannot "
                    "all be true at once: %s. This is reported as a DATA DEFECT rather "
                    "than rated around, because every value a rating needs is present and "
                    "a letter derived from them would look fully supported while resting "
                    "on a contradiction." % "; ".join(bad)),
                "domains": [], "handbook_version": HANDBOOK_VERSION,
                "derived_by": "ssot/grade_engine.py"}

    domains = [f(canon, oid, res) for f in DERIVERS]
    refused = [d for d in domains if d["state"] == REFUSED]
    total = sum(d["levels"] for d in domains)

    rec = {"oid": oid,
           "k": _num(res.get("k")),
           "starting_certainty": "HIGH",
           "starting_certainty_because": (
               "The contributing studies are randomized trials, which begin at HIGH "
               "certainty under GRADE (Handbook ch 14)."),
           "domains": domains,
           "downgrade_levels": total,
           "handbook_version": HANDBOOK_VERSION,
           "handbook_reference": HANDBOOK_REF,
           "handbook_verified_on": HANDBOOK_VERIFIED_ON,
           "rating_up_not_applied": (
               "No domain is rated UP. Rating up for a large effect, a dose-response "
               "gradient or opposing plausible confounding applies to evidence that "
               "started below HIGH; randomized trials start at HIGH and cannot be rated "
               "above it."),
           "derived_by": "ssot/grade_engine.py",
           }

    if refused:
        # ⭐⭐⭐ THE BOUND. A refusal is not the same as knowing nothing.
        #
        # Mahmood, 2026-08-30: "if this is not possible then find another methodologically
        # consistent way of doing it." This is that. When four domains resolve and one does
        # not, the certainty is not unknown -- it is BOUNDED. It can be at best the letter
        # the resolved downgrades give, and at worst that letter plus the most the
        # unresolved domains could ever take away. Both ends are entailed by the domains
        # already assessed plus the ladder; neither is a guess.
        #
        # ⚠️ THIS IS NOT A RATING AND MUST NEVER BE READ AS ONE. `rated` stays False and
        # `certainty` stays None. The bound is an ADDITIONAL fact, never a substitute for
        # the letter, because a bound presented as a rating would be exactly the
        # manufactured verdict the whole module exists to refuse.
        #
        # ⭐ AND THE CASE THAT MATTERS: WHERE THE TWO ENDS MEET, THE LETTER IS ENTAILED.
        # If the resolved domains already carry three or more downgrades, the rating is
        # VERY LOW whatever the unresolved domains would have said, because the ladder has
        # a floor. That is not an assumption about the missing input -- it is the
        # observation that the missing input CANNOT CHANGE THE ANSWER. A review that
        # withheld a letter there would be withholding something it actually knows, which
        # is its own kind of dishonesty.
        MAX_PER_DOMAIN = 2
        worst = min(total + MAX_PER_DOMAIN * len(refused), len(LADDER) - 1)
        best = min(total, len(LADDER) - 1)
        entailed = (LADDER[best] == LADDER[worst])
        rec["certainty_bounds"] = {
            "best_case": LADDER[best],
            "worst_case": LADDER[worst],
            "resolved_downgrades": total,
            "unresolved_domains": [d["domain"] for d in refused],
            "max_further_downgrade": MAX_PER_DOMAIN * len(refused),
            "entailed": entailed,
            "statement": (
                ("THE LETTER IS ENTAILED DESPITE THE REFUSAL: the domains that WERE "
                 "assessed already carry %d downgrade(s), and the GRADE ladder floors at "
                 "VERY LOW, so %s is the answer whatever %s would have said. The "
                 "unresolved domain cannot change it."
                 % (total, LADDER[best],
                    " and ".join(d["domain"] for d in refused)))
                if entailed else
                ("Certainty lies between %s and %s. The %d domain(s) that WERE assessed "
                 "give %s; the %d unresolved domain(s) (%s) could take it as low as %s. "
                 "This is a BOUND, not a rating: no letter is published, because choosing "
                 "one inside the bound would be the judgement that has not been made."
                 % (LADDER[best], LADDER[worst], len(domains) - len(refused),
                    LADDER[best], len(refused),
                    ", ".join(d["domain"] for d in refused), LADDER[worst]))),
            "what_this_is_not": (
                "A bound is not a certainty rating and is not shown in the certainty "
                "column. It states what the assessed domains already establish and what "
                "the unassessed ones could still cost."),
        }
        rec.update({
            "rated": False,
            "state": REFUSED,
            "certainty": None,
            "refused_domains": [d["domain"] for d in refused],
            "reason": (
                "NO CERTAINTY RATING IS ISSUED for this pooled result, because %d of the "
                "five GRADE domains could not be assessed from what this review holds: "
                "%s. The domains that COULD be assessed are reported above with their "
                "reasons. A rating is withheld rather than issued from the remainder, "
                "because a certainty grade means all five domains were considered, and "
                "one assembled from a subset would carry a letter this review did not "
                "earn." % (len(refused), ", ".join(d["domain"] for d in refused))),
        })
        return rec

    idx = min(total, len(LADDER) - 1)
    rec.update({"rated": True, "state": "RATED",
                "certainty": LADDER[idx],
                "reason": "Started HIGH; %s." % (
                    "no domain was rated down" if total == 0
                    else "rated down %d level(s) across %s" % (
                        total, ", ".join(d["domain"] for d in domains
                                         if d["state"] == DOWNGRADE)))})
    rec["sensitivity"] = _rating_sensitivity(domains, total)
    return rec


def _rating_sensitivity(domains, total):
    """⭐ WHAT THE LETTER WOULD BE UNDER A DIFFERENT THRESHOLD.

    "MODERATE, and it becomes LOW if the imprecision threshold is the line of no effect
    rather than appreciable benefit and harm" is a sentence essentially no published
    review prints, and it is honest rather than clever: it separates how much of the
    verdict is the evidence from how much is the line we chose to draw.

    ⚠️ IT REPORTS THE ALTERNATIVE, IT DOES NOT ADOPT IT. The rating stands at the declared
    threshold. Offering the reader the range is not the same as refusing to commit, and a
    review that showed only the range would have made no judgement at all.
    """
    imp = next((d for d in domains if d["domain"] == "imprecision"), None)
    alts = []
    if imp and isinstance(imp.get("thresholds"), dict):
        chosen = imp["thresholds"].get("chosen")
        applied = 1 if imp["state"] == DOWNGRADE else 0
        for e in imp["thresholds"].get("evaluated_against") or []:
            if e["threshold"] == chosen:
                continue
            would = 1 if e["downgrade"] else 0
            t2 = total - applied + would
            alts.append({
                "threshold": e["threshold"], "kind": e["kind"],
                "imprecision_would_be": ("down 1 level" if would else "no downgrade"),
                "certainty_would_be": LADDER[min(t2, len(LADDER) - 1)],
                "changes_the_letter": LADDER[min(t2, len(LADDER) - 1)]
                                      != LADDER[min(total, len(LADDER) - 1)]})
    changed = [a for a in alts if a["changes_the_letter"]]
    return {
        "alternatives": alts,
        "letter_is_threshold_sensitive": bool(changed),
        "statement": (
            ("This letter DEPENDS on the imprecision threshold: %s."
             % "; ".join("under %s it would be %s" % (a["threshold"],
                                                      a["certainty_would_be"])
                         for a in changed))
            if changed else
            ("This letter does NOT change under any of the other thresholds evaluated, so "
             "it is not an artefact of where the decision line was drawn."
             if alts else
             "No alternative threshold was applicable to this summary measure.")),
        "what_this_is_not": (
            "Reporting the alternatives is not a refusal to commit. The rating above "
            "stands, at the threshold named with it; this says how much of it rests on "
            "that choice."),
    }


def derive_all(canon):
    """Every pooled result in one object, keyed by outcome id."""
    by = (canon.get("results") or {}).get("by_outcome") or {}
    return {oid: derive(canon, oid) for oid in by}
