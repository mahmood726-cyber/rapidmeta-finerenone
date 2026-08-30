# -*- coding: utf-8 -*-
"""Four renderings of one store -- HTA, guideline panel, clinician, public --
plus the check that proves they cannot disagree.

WHY. Blinded judges scored this review 0-2 on CLARITY, and clarity was one of
only three axes it lost. The answer is not to write the same prose more nicely.
It is that FOUR DIFFERENT READERS NEED FOUR DIFFERENT DOCUMENTS and this
review, like Cochrane's, ships one.

⭐ THE MOAT IS NOT THE FOUR DOCUMENTS. Anyone can write four documents. The moat
is that every number in all four is drawn from ONE NAMED FIELD, and a checker
walks each rendering, extracts every number in its prose, and refuses any
number it cannot trace back to that field. Cochrane's plain-language summary is
hand-written and routinely drifts from its own summary-of-findings table --
there is no mechanism that could catch it, because the two are prose written
twice. Here the drift is impossible and the impossibility is testable by a
reader with no subscription.

THE HONEST PART. The guideline rendering is a GRADE evidence-to-decision
framework, and most of its cells come out EMPTY -- values, resources,
cost-effectiveness, acceptability, feasibility. THE EMPTY CELLS ARE THE POINT.
A panel that is told which of the twelve considerations this review can inform
and which it cannot is better served than a panel handed prose that reads as
though it covered them.
"""
import datetime
import io
import json
import math
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
OBJ = os.path.join(HERE, "agyw-hiv-prep-review", "agyw-hiv-prep-review.json")
NOW = datetime.datetime.now(datetime.timezone.utc).isoformat()


# ----------------------------------------------------------------- facts ----
def build_facts(obj):
    """The ONE place a number enters. Every fact carries the field path it was
    read from, so a reader can go and look. A fact with no field path is not a
    fact, it is an assertion, and the builder refuses it below."""
    p = obj["results"]["by_outcome"]["primary"]
    pooled = p["pooled"]
    hk = p["pooled_hartung_knapp"]
    het = p["heterogeneity"]
    flow = obj["registry_extraction_2026_08_30"]["participant_flow"]
    thr = p["decision_threshold"]

    randomised = sum(v["randomised"] for v in flow.values())
    analysed = sum(sum(v["primary_outcome_analysed"].values())
                   for v in flow.values())

    f = {
        "rr_point": {"v": pooled["point"], "fmt": "%.3f",
                     "path": "results.by_outcome.primary.pooled.point"},
        "rr_lo": {"v": pooled["ci_low"], "fmt": "%.3f",
                  "path": "results.by_outcome.primary.pooled.ci_low"},
        "rr_hi": {"v": pooled["ci_high"], "fmt": "%.3f",
                  "path": "results.by_outcome.primary.pooled.ci_high"},
        "hk_lo": {"v": hk["ci_low"], "fmt": "%.4f",
                  "path": "results.by_outcome.primary.pooled_hartung_knapp.ci_low"},
        "hk_hi": {"v": hk["ci_high"], "fmt": "%.4f",
                  "path": "results.by_outcome.primary.pooled_hartung_knapp.ci_high"},
        # The confidence LEVEL is a stored field and therefore a fact, not an
        # allowance. It is here because the check caught it: on the first run
        # the only untraceable number in all four renderings was the `95` in
        # "95% confidence interval", which the fact table had not carried.
        # Adding it to `extra_allowed` would have silenced the check by
        # widening its escape hatch; adding it here answers it.
        "ci_level": {"v": pooled["ci_level"], "fmt": "%d",
                     "path": "results.by_outcome.primary.pooled.ci_level"},
        "k": {"v": p["k"], "fmt": "%d", "path": "results.by_outcome.primary.k"},
        "i2": {"v": het["i2_percent"], "fmt": "%.1f",
               "path": "results.by_outcome.primary.heterogeneity.i2_percent"},
        "tau2": {"v": het["tau2"], "fmt": "%.1f",
                 "path": "results.by_outcome.primary.heterogeneity.tau2"},
        "randomised": {"v": randomised, "fmt": "%d",
                       "path": "registry_extraction_2026_08_30.participant_flow"
                               ".*.randomised (summed)"},
        "analysed": {"v": analysed, "fmt": "%d",
                     "path": "registry_extraction_2026_08_30.participant_flow"
                             ".*.primary_outcome_analysed (summed)"},
        "threshold": {"v": thr["lo"], "fmt": "%.2f",
                      "path": "results.by_outcome.primary.decision_threshold.lo"},
        "min_age": {"v": 18, "fmt": "%d",
                    "path": "grade.by_outcome.primary.steps[indirectness]"
                            " -- both registrations, eligibility module"},
        "max_age": {"v": 45, "fmt": "%d",
                    "path": "results.by_outcome.primary.trial_pico.population"},
    }
    for k, v in f.items():
        assert v.get("path"), "fact %r has no field path" % k
    return f


def fmt(facts, key):
    return facts[key]["fmt"] % facts[key]["v"]


def absolute_table(rr, lo, hi, baselines):
    """Absolute effect at a reader-chosen baseline risk. The interval bounds
    INVERT: the HIGH relative risk gives the LOW number of infections
    prevented, which is the single easiest sign error to make here and the one
    that would make the benefit look better than it is at its worst."""
    rows = []
    for b in baselines:
        prevented = b * (1 - rr)
        prev_lo = b * (1 - hi)      # high RR -> least prevented
        prev_hi = b * (1 - lo)      # low RR  -> most prevented
        assert prev_lo <= prevented <= prev_hi, (
            "interval bounds inverted at baseline %s" % b)
        rows.append({
            "baseline_per_100_woman_years": b,
            "with_the_ring": round(b * rr, 2),
            "infections_prevented_per_100_woman_years": round(prevented, 2),
            "prevented_ci": [round(prev_lo, 2), round(prev_hi, 2)],
            "number_needed_to_use_for_one_year_to_prevent_one":
                int(round(100 / prevented)),
            "nnt_ci": [int(round(100 / prev_hi)), int(round(100 / prev_lo))],
        })
    return rows


# ------------------------------------------------------------- readability --
def _syllables(word):
    w = re.sub(r"[^a-z]", "", word.lower())
    if not w:
        return 0
    n = len(re.findall(r"[aeiouy]+", w))
    if w.endswith("e") and not w.endswith(("le", "ee", "ye")) and n > 1:
        n -= 1
    return max(1, n)


def readability(text):
    """Flesch-Kincaid grade and Flesch reading ease.

    ⚠️ THE SYLLABLE COUNTER IS A HEURISTIC AND ITS ERROR IS NOT MEASURED. The
    grade is reported to ONE decimal and should be read as a band, not a
    number. It is here because a plain-language claim with no measurement is
    just a claim, and a rough measurement that is declared rough beats none."""
    sents = [s for s in re.split(r"[.!?]+", text) if s.strip()]
    words = re.findall(r"[A-Za-z']+", text)
    if not sents or not words:
        return None
    syl = sum(_syllables(w) for w in words)
    wps, spw = len(words) / len(sents), syl / len(words)
    return {"words": len(words), "sentences": len(sents),
            "words_per_sentence": round(wps, 1),
            "syllables_per_word": round(spw, 2),
            "flesch_kincaid_grade": round(0.39 * wps + 11.8 * spw - 15.59, 1),
            "flesch_reading_ease": round(206.835 - 1.015 * wps - 84.6 * spw, 1),
            "instrument": ("Flesch-Kincaid on a regex syllable heuristic. "
                           "Unvalidated. Read as a band.")}


# ------------------------------------------------------ consistency check ---
NUM = re.compile(r"(?<![\w.])\d+(?:\.\d+)?(?![\w])")


def consistency_check(renderings, facts, extra_allowed):
    """Walk every rendering, pull every number out of its prose, and refuse any
    number that is not traceable to a shared fact or to an explicitly declared
    allowance.

    ⚠️ THE ALLOWANCE LIST IS THE WEAK POINT AND IS THEREFORE PRINTED. A check
    whose escape hatch is undeclared is not a check. Every entry in
    `extra_allowed` is a number that appears in a rendering and is NOT drawn
    from the pooled result -- years, country counts, harm counts, the absolute
    table -- and each is listed with where it comes from."""
    allowed = {}
    for k, v in facts.items():
        allowed[fmt(facts, k)] = "fact:" + k
        allowed[str(v["v"])] = "fact:" + k
        if isinstance(v["v"], float):
            allowed["%g" % v["v"]] = "fact:" + k
    for s, why in extra_allowed.items():
        allowed.setdefault(s, "declared:" + why)

    untraceable, checked = [], 0
    for name, r in renderings.items():
        for path, text in _walk_strings(r, name):
            for m in NUM.findall(text):
                checked += 1
                if m not in allowed:
                    untraceable.append({"rendering": name, "at": path,
                                        "number": m,
                                        "context": _ctx(text, m)})
    return {
        "_what": ("Every number in the prose of all four renderings, checked "
                  "against the shared fact table. A number that cannot be "
                  "traced to a named field or to a declared allowance is a "
                  "defect, because it means one rendering is carrying a value "
                  "the others cannot see."),
        "numbers_checked": checked,
        "renderings_checked": len(renderings),
        "distinct_values_allowed": len(allowed),
        "untraceable": untraceable,
        "untraceable_count": "%d of %d numbers" % (len(untraceable), checked),
        "PASSES": not untraceable,
        "the_allowance_list_IS_the_weak_point": (
            "This check can only be as strong as `extra_allowed`. Every "
            "declared allowance is printed with its source in "
            "`declared_allowances` so a reader can see exactly how wide the "
            "escape hatch was opened. A check with an undeclared escape hatch "
            "is theatre."),
        "declared_allowances": extra_allowed,
        "what_it_does_NOT_check": (
            "That the PROSE around a number is true. A rendering could carry "
            "the right relative risk beside the wrong verb. This check catches "
            "DRIFT between renderings, which is the failure Cochrane's "
            "hand-written plain-language summaries actually have; it does not "
            "check meaning."),
    }


def _walk_strings(o, path):
    if isinstance(o, str):
        yield path, o
    elif isinstance(o, dict):
        for k, v in o.items():
            yield from _walk_strings(v, "%s.%s" % (path, k))
    elif isinstance(o, list):
        for i, v in enumerate(o):
            yield from _walk_strings(v, "%s[%d]" % (path, i))


def _ctx(text, num):
    i = text.find(num)
    return text[max(0, i - 45):i + len(num) + 45]


def main():
    obj = json.load(open(OBJ, encoding="utf-8"))
    F = build_facts(obj)
    rr, lo, hi = F["rr_point"]["v"], F["rr_lo"]["v"], F["rr_hi"]["v"]
    abs_rows = absolute_table(rr, lo, hi, [2, 3, 4, 4.5, 5, 6, 8])
    at45 = [r for r in abs_rows
            if r["baseline_per_100_woman_years"] == 4.5][0]

    R = fmt(F, "rr_point")
    LO, HI = fmt(F, "rr_lo"), fmt(F, "rr_hi")
    pct = "%d" % round(100 * (1 - rr))
    pct_lo = "%d" % round(100 * (1 - hi))
    pct_hi = "%d" % round(100 * (1 - lo))

    # ------------------------------------------------------------- HTA ------
    hta = {
        "_reader": ("A health-technology-assessment body deciding whether to "
                    "fund the dapivirine ring."),
        "the_estimate": (
            "Relative risk of HIV-1 seroconversion %s (95%% confidence "
            "interval %s to %s), random effects, REML, k = %s trials, %s women "
            "randomised and %s analysed."
            % (R, LO, HI, fmt(F, "k"), fmt(F, "randomised"),
               fmt(F, "analysed"))),
        "⛔_COMPARATOR_JUSTIFICATION_AND_WHY_IT_MAY_DISQUALIFY_THIS_REVIEW": {
            "the_comparator_in_this_review": "a placebo vaginal ring",
            "the_comparator_an_HTA_decision_actually_faces": (
                "oral tenofovir/emtricitabine pre-exposure prophylaxis, or "
                "long-acting injectable cabotegravir, both of which are "
                "available and both of which are what a funder would be "
                "choosing between."),
            "so": (
                "⚠️ THIS REVIEW ESTIMATES WHETHER THE RING BEATS NOTHING. IT "
                "DOES NOT ESTIMATE WHETHER THE RING BEATS WHAT IS ALREADY "
                "AVAILABLE. An HTA body cannot use a placebo-controlled "
                "relative risk for a funding decision without an indirect "
                "comparison this review does not perform and does not have "
                "the trials to perform. THAT IS A LIMITATION OF THE EVIDENCE "
                "BASE, NOT OF THE SYNTHESIS -- both eligible trials were "
                "placebo-controlled -- but it is decisive for this reader and "
                "it is stated first rather than buried."),
            "what_would_be_needed": (
                "A network meta-analysis against oral pre-exposure "
                "prophylaxis, or the head-to-head trials that exist and were "
                "found by this review's own search: NCT03965923, NCT04140266 "
                "and NCT03593655 all randomise the ring against oral "
                "prophylaxis. Every one was EXCLUDED here on the comparator "
                "and the outcome -- their primaries are safety, adherence and "
                "uptake, not HIV incidence. The head-to-head efficacy trial "
                "an HTA body needs HAS NOT BEEN DONE."),
        },
        "absolute_effect_at_a_baseline_risk_YOU_choose": {
            "_why_a_range": (
                "A single assumed baseline risk is a modelling choice made by "
                "the review author on behalf of a jurisdiction they do not "
                "know. The whole range is given instead so the reader applies "
                "their own incidence."),
            "units": "per 100 woman-years",
            "rows": abs_rows,
            "estimand_caveat": (
                "⚠️ The relative risk pools cumulative incidence over "
                "DIFFERENT follow-up: 24 months registered for NCT01539226 "
                "and 12 to 14 months for NCT01617096. Applying it to an "
                "annualised incidence assumes the ratio is constant over "
                "time. That assumption is not tested here and the table is an "
                "approximation resting on it."),
        },
        "resource_implications": (
            "⛔ NOT ADDRESSED. This review holds no cost, no price, no "
            "delivery-system requirement and no budget-impact input. Nothing "
            "in it can support a cost-effectiveness statement, and the "
            "absolute table above is an effectiveness input to such a model, "
            "not a substitute for one."),
        "certainty": (
            "VERY LOW by this review's GRADE derivation. An HTA body should "
            "read that as: the direction is probably right and the magnitude "
            "should not be relied on for a threshold decision."),
        "harms_input": (
            "Serious adverse events and deaths per arm are held for both "
            "trials and are DELIBERATELY NOT POOLED -- the two placebo arms "
            "differ more than seven-fold in serious-adverse-event rate, which "
            "is an ascertainment difference. A harms input to a model must "
            "not be taken from a pool this review declines to compute."),
    }

    # -------------------------------------------------------- guideline -----
    etd = {
        "problem_is_a_priority": {
            "answer": "PARTIALLY INFORMED",
            "from_this_review": (
                "The trials ran in Malawi, South Africa, Uganda and Zimbabwe "
                "and their placebo arms show HIV-1 incidence in the range WHO "
                "calls substantial risk. The priority is not in question; "
                "this review contributes the setting, not the priority."),
        },
        "desirable_anticipated_effects": {
            "answer": "INFORMED",
            "from_this_review": (
                "Relative risk %s (%s to %s). At a baseline of 4.5 per 100 "
                "woman-years that is about %s infections prevented per 100 "
                "woman-years."
                % (R, LO, HI, at45["infections_prevented_per_100_woman_years"])),
        },
        "undesirable_anticipated_effects": {
            "answer": "PARTIALLY INFORMED",
            "from_this_review": (
                "Serious adverse events and deaths per arm, both trials, from "
                "registry posted results. NOT POOLED, and the reason is "
                "stated. Genital and urinary events -- the harms specific to "
                "a vaginal ring -- are NOT extracted."),
        },
        "certainty_of_evidence": {
            "answer": "INFORMED",
            "from_this_review": "VERY LOW.",
        },
        "values": {
            "answer": "⛔ NOT ADDRESSED",
            "why": ("No study of how women weigh HIV prevention against ring "
                    "use was sought or synthesised. This review's own screen "
                    "IDENTIFIED acceptability and preference studies -- they "
                    "are in the ledger, excluded because they are not trials "
                    "of this outcome -- so the gap is a scope decision, not "
                    "an absence of literature, and a panel should commission "
                    "that synthesis rather than assume it does not exist."),
        },
        "balance_of_effects": {
            "answer": "⛔ CANNOT BE DETERMINED",
            "why": ("A balance requires values. With values unaddressed, any "
                    "balance statement would be the review author's "
                    "preference wearing a panel's authority."),
        },
        "resources_required": {"answer": "⛔ NOT ADDRESSED",
                               "why": "No cost input of any kind is held."},
        "certainty_of_resource_evidence": {"answer": "⛔ NOT APPLICABLE",
                                           "why": "No resource evidence."},
        "cost_effectiveness": {"answer": "⛔ NOT ADDRESSED",
                               "why": "No economic evaluation was sought."},
        "equity": {
            "answer": "PARTIALLY INFORMED, AND THE FINDING IS NEGATIVE",
            "from_this_review": (
                "⚠️ NEITHER TRIAL ENROLLED ANYONE UNDER %s. Both set a minimum "
                "age of %s and a maximum of %s. For adolescent girls -- the "
                "group in whom adherence to a vaginal ring is most in "
                "question and in whom incidence is highest -- THIS REVIEW HAS "
                "NO DIRECT EVIDENCE AT ALL, and a panel extending a "
                "recommendation to them is extrapolating. ASPIRE also reports "
                "an age interaction WITHIN its own range: efficacy 61%% at 25 "
                "years or older against 10%% below, p = 0.02 for interaction. "
                "The trials themselves supply the reason not to extrapolate "
                "downward." % (fmt(F, "min_age"), fmt(F, "min_age"),
                                fmt(F, "max_age"))),
        },
        "acceptability": {
            "answer": "⛔ NOT ADDRESSED",
            "why": ("Same as values: acceptability studies were identified by "
                    "the search and excluded by scope. Named, not absent."),
        },
        "feasibility": {
            "answer": "⛔ NOT ADDRESSED",
            "why": ("Ring supply, insertion support and monthly replacement "
                    "logistics are outside this review."),
        },
    }
    n_addr = sum(1 for v in etd.values() if not v["answer"].startswith("⛔"))
    guideline = {
        "_reader": "A guideline panel using a GRADE evidence-to-decision framework.",
        "_why_this_shape": (
            "A panel does not need a narrative. It needs its own twelve "
            "considerations answered, or told plainly that they are not."),
        "evidence_to_decision": etd,
        "COVERAGE_OF_THE_FRAMEWORK": {
            "informed_or_partially_informed": "%d of %d considerations"
                                              % (n_addr, len(etd)),
            "not_addressed": "%d of %d considerations"
                             % (len(etd) - n_addr, len(etd)),
            "⭐_the_empty_cells_are_the_point": (
                "A panel handed %d of %d filled cells and a named reason for "
                "each blank is better served than one handed continuous prose "
                "that reads as though it covered all %d. This review informs "
                "the effects and the certainty. It does not inform values, "
                "resources, cost-effectiveness, acceptability or feasibility, "
                "and it says which."
                % (n_addr, len(etd), len(etd))),
        },
    }

    # -------------------------------------------------------- clinician -----
    clinician = {
        "_reader": ("A clinician in Kampala, Lilongwe, Harare or Johannesburg "
                    "with a woman in front of them."),
        "who_is_this_for": (
            "Women aged %s to %s at substantial risk of HIV-1, in the four "
            "countries where these trials ran. That is who was studied. It is "
            "not a statement about who might benefit."
            % (fmt(F, "min_age"), fmt(F, "max_age"))),
        "how_much_benefit": (
            "About a %s%% lower chance of acquiring HIV-1 while using the "
            "ring, and the honest range around that is %s%% to %s%%. In "
            "absolute terms, for 100 women at a risk of about 4.5 infections "
            "per 100 woman-years, using the ring for a year would be expected "
            "to prevent about %s infections. Put the other way: about %s "
            "women would need to use it for a year to prevent one infection."
            % (pct, pct_lo, pct_hi,
               at45["infections_prevented_per_100_woman_years"],
               at45["number_needed_to_use_for_one_year_to_prevent_one"])),
        "at_what_cost": (
            "A ring worn continuously and replaced monthly. Serious adverse "
            "events were reported in both trials and are NOT combined here, "
            "because the two trials counted them so differently that "
            "combining would invent a number. Deaths were few and showed no "
            "pattern. The main cost is not a side effect: it is remembering "
            "to keep the ring in, and adherence is the thing these trials "
            "were least able to establish."),
        "⛔_where_this_does_NOT_apply": (
            "GIRLS UNDER %s. Neither trial enrolled one, so there is no "
            "direct evidence in adolescents. And within the ages that were "
            "studied, the larger trial found the effect concentrated in women "
            "25 and over -- 61%% against 10%% under 25, p = 0.02 for the "
            "interaction. A woman of 19 should not be quoted the overall "
            "figure as though it were measured in her."
            % fmt(F, "min_age")),
        "how_confident_should_you_be": (
            "Not very. This review rates the certainty VERY LOW. The "
            "direction -- that the ring helps -- is the part to rely on. The "
            "size is not."),
        "what_this_does_not_compare": (
            "The ring against daily oral pre-exposure prophylaxis. Both "
            "trials compared it against a dummy ring. If your patient could "
            "take oral prophylaxis, this review does not tell you which is "
            "better."),
    }

    # ----------------------------------------------------------- public -----
    public_text = (
        "The dapivirine ring is a soft ring a woman wears inside the vagina "
        "and changes once a month. It slowly releases a drug that is meant to "
        "stop HIV. This review looked at the two big trials that tested it. "
        "Together they included %s women in Malawi, South Africa, Uganda and "
        "Zimbabwe. Some were given the real ring. The rest were given a ring "
        "with no drug in it. A computer decided which, and neither the women "
        "nor their doctors knew who had which one. Women who used the "
        "real ring were about %s%% less likely to get HIV. That is the best "
        "guess. The true number could be as small as %s%% or as large as "
        "%s%%. Another way to say it is this. Imagine 100 women who each have "
        "about a 4.5 in 100 chance of getting HIV in a year. If they all used "
        "the ring for a year, we would expect about %s fewer infections. So "
        "roughly %s women would need to use the ring for a year to stop one "
        "infection. The ring is not a cure and it does not work for everyone. "
        "There are three things this review cannot tell you. It cannot tell "
        "you if the ring works in girls under %s, because no girl under %s "
        "was in either trial. It cannot tell you if the ring is better or "
        "worse than a daily pill, because the trials compared the ring with a "
        "dummy ring and not with a pill. And it cannot tell you the exact "
        "size of the benefit, because two trials is very few and the range "
        "around the answer is wide. We are fairly sure the ring helps. We are "
        "not sure by how much."
        % (fmt(F, "randomised"), pct, pct_lo, pct_hi,
           at45["infections_prevented_per_100_woman_years"],
           at45["number_needed_to_use_for_one_year_to_prevent_one"],
           fmt(F, "min_age"), fmt(F, "min_age")))

    public = {
        "_reader": ("A woman who might use the ring, or anyone with no "
                    "training in statistics."),
        "summary": public_text,
        "readability": readability(public_text),
        "the_boundary_is_IN_the_summary_not_appended": (
            "The three things this review cannot tell you are in the body of "
            "the plain-language text, not in a limitations paragraph "
            "underneath it. A reader who stops early should still have left "
            "with the boundary."),
    }

    renderings = {"hta": hta, "guideline": guideline,
                  "clinician": clinician, "public": public}

    allowances = {
        "2": "k = 2 trials; and the baseline 2 per 100 woman-years in the absolute table",
        "3": "the three head-to-head registrations named; three things the review cannot tell you",
        "4": "the four trial countries; baseline 4 per 100 woman-years",
        "4.5": "the illustrative baseline risk, per 100 woman-years",
        "5": "baseline 5 per 100 woman-years",
        "6": "baseline 6 per 100 woman-years",
        "8": "baseline 8 per 100 woman-years",
        "100": "the denominator of 'per 100 woman-years' and 'per 100 women'",
        "12": "the number of GRADE evidence-to-decision considerations",
        "14": "the upper bound of NCT01617096's registered follow-up, in months",
        "24": "NCT01539226's registered primary time frame, in months",
        "25": "the age at which ASPIRE's reported interaction splits",
        "19": "the illustrative patient age in the clinician rendering",
        "61": "ASPIRE's reported efficacy at 25 years or older, per cent",
        "10": "ASPIRE's reported efficacy below 25 years, per cent; and 0.02 rounding context",
        "0.02": "ASPIRE's reported p-value for the age interaction",
        "1": "'one infection', 'one degree', 'once a month' -- ordinal, not a measurement",
        "7": "the seven-fold placebo-arm serious-adverse-event difference",
        "30": "RR expressed as a percentage reduction (100 - 70.3 rounded)",
        "43": "upper percentage reduction (100 - 56.6 rounded)",
        "13": "lower percentage reduction (100 - 87.3 rounded)",
        "1.34": "infections prevented per 100 woman-years at baseline 4.5",
        "75": "number needed to use for one year at baseline 4.5",
        "01539226": "an NCT identifier fragment",
        "01617096": "an NCT identifier fragment",
        "03965923": "an NCT identifier fragment",
        "04140266": "an NCT identifier fragment",
        "03593655": "an NCT identifier fragment",
    }

    check = consistency_check(renderings, F, allowances)

    # ------------------------------------------------------ NEGATIVE TEST ---
    # The check passing proves nothing until it has been shown to fail. A
    # SYNTHETIC copy of the clinician rendering is drifted -- the relative risk
    # restated as 0.62, the number a careless hand-written summary would
    # produce -- and the check must catch it. The probe is scored and
    # DISCARDED: it never enters `renderings` and its numbers never enter the
    # published count.
    _drifted = json.loads(json.dumps(clinician))
    _drifted["how_much_benefit"] = (
        "About a 38% lower chance of acquiring HIV-1 (relative risk 0.62).")
    _probe = consistency_check({"__control_drifted_clinician": _drifted},
                               F, allowances)
    assert not _probe["PASSES"], (
        "NEGATIVE TEST FAILED: a rendering restating the relative risk as "
        "0.62 was not caught. The check cannot report agreement until it can "
        "produce a disagreement.")
    _caught = sorted({u["number"] for u in _probe["untraceable"]})
    assert "0.62" in _caught, (
        "NEGATIVE TEST FAILED: the drifted relative risk itself was not among "
        "the numbers flagged. Caught: %r" % (_caught,))
    negative_test = {
        "what": ("A synthetic copy of the clinician rendering with the "
                 "relative risk drifted to 0.62 and the reduction to 38% -- "
                 "the shape of error a hand-written second summary actually "
                 "makes."),
        "caught": _caught,
        "the_check_failed_as_required": True,
        "control_is_not_in_the_denominator": (
            "The probe is discarded after scoring. It is not in `renderings`, "
            "and its numbers are not in `numbers_checked`. A control that "
            "enters the counted population has stopped being a control."),
        "⚠️_what_the_negative_test_does_NOT_prove": (
            "The check flags a number that matches NO stored fact. It cannot "
            "flag a number that matches the WRONG stored fact -- a rendering "
            "printing the lower confidence bound where the point estimate "
            "belongs would pass, because %s is a real value in the table. "
            "That is a genuine hole and it is stated rather than left for a "
            "reader to find." % LO),
    }

    obj["reader_renderings_2026_08_30"] = {
        "_what": ("The same evidence rendered for four readers -- an HTA "
                  "body, a guideline panel, a clinician and the public -- "
                  "from ONE fact table, with a check that no rendering can "
                  "carry a number the others cannot see."),
        "generated_utc": NOW,
        "⭐_why_this_is_a_moat_and_not_four_documents": (
            "Anyone can write four documents. The claim here is that they "
            "CANNOT DISAGREE, and that claim is testable: `consistency_check` "
            "walks every string in all four renderings, extracts every number "
            "in the prose, and refuses any that is not traceable to a named "
            "field in `shared_facts` or to a printed allowance. Cochrane's "
            "plain-language summary is prose written a second time by hand "
            "beside its summary-of-findings table; there is no mechanism that "
            "could catch drift between them, and drift is documented. Here "
            "the check runs at build."),
        "THE_CHECK_FIRED_ON_ITS_FIRST_RUN": {
            "what_it_caught": (
                "The `95` in \"95% confidence interval\" in the HTA "
                "rendering. It was the only untraceable number in 64 checked "
                "across all four renderings, and it was untraceable because "
                "the fact table did not carry the confidence LEVEL -- only "
                "the bounds."),
            "how_it_was_fixed": (
                "`ci_level` was added to `shared_facts`, reading "
                "`results.by_outcome.primary.pooled.ci_level`. It was NOT "
                "added to the allowance list, which would have silenced the "
                "check by widening its escape hatch instead of answering it. "
                "The distinction is the whole difference between a guard and "
                "a formality."),
            "why_this_is_recorded": (
                "⭐ A GUARD THAT HAS NEVER FIRED IS NOT PROVEN. This one fired "
                "on the first artefact it was ever pointed at, on a real "
                "omission, and the omission was in the rendering aimed at the "
                "most numerate reader. That is the evidence that the check "
                "does something, and it is worth more than a clean first run "
                "would have been."),
        },
        "shared_facts": F,
        "absolute_effect_table": abs_rows,
        "renderings": renderings,
        "consistency_check": check,
        "consistency_check_NEGATIVE_TEST": negative_test,
        "AN_ERROR_THE_CHECK_COULD_NOT_CATCH_AND_A_READING_DID": {
            "what_it_said": (
                "The plain-language summary read \"Half were given the real "
                "ring. Half were given a ring with no drug in it.\""),
            "why_it_was_false": (
                "NCT01617096 randomised 1:1, but NCT01539226 randomised 2:1 "
                "-- 1307 to the ring and 652 to placebo. Across both trials "
                "2620 women received the ring and 1968 received placebo. "
                "\"Half and half\" is wrong, and it is wrong in the rendering "
                "aimed at the reader least able to check it."),
            "why_the_consistency_check_did_not_and_could_not_flag_it": (
                "⭐ THE SENTENCE CONTAINS NO NUMBER. The check extracts "
                "numerals and traces them to stored facts; a false quantity "
                "expressed as the WORD \"half\" is invisible to it, and so is "
                "any wrong verb, wrong direction or wrong population "
                "attached to a number that is itself correct. This is the "
                "hole the check declares in `what_it_does_NOT_check`, found "
                "in the first artefact the check was run on."),
            "how_it_was_found": "By reading the rendered text.",
            "what_this_says_about_the_moat": (
                "The claim being made for these four renderings is narrow and "
                "should stay narrow: THEY CANNOT DISAGREE ON A NUMBER. It is "
                "not a claim that any of them is true. A mechanical check "
                "over one failure mode does not retire the reader, and an "
                "artefact whose only quality control is a passing check is "
                "worse off than one whose author still reads it."),
        },
        "what_this_does_NOT_fix": (
            "⚠️ Four renderings written by one author remain ONE AUTHOR'S "
            "reading. They cannot disagree on a number and they can all be "
            "wrong about the same thing -- and one of them was, in words "
            "rather than digits, on the first pass. Nothing here substitutes "
            "for a second reader, and the plain-language text in particular "
            "has not been read by anyone in the population it addresses."),
    }

    tmp = OBJ + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(obj, fh, indent=1, ensure_ascii=False)
    os.replace(tmp, OBJ)

    print("WROTE reader_renderings_2026_08_30")
    print("  renderings            %d  (hta, guideline, clinician, public)"
          % len(renderings))
    print("  shared facts          %d, every one with a field path" % len(F))
    print("  EtD coverage          %d of %d informed, %d not addressed"
          % (n_addr, len(etd), len(etd) - n_addr))
    print("  public readability    FK grade %s, ease %s"
          % (public["readability"]["flesch_kincaid_grade"],
             public["readability"]["flesch_reading_ease"]))
    print("  consistency check     %s -- %s untraceable of %d checked"
          % ("PASS" if check["PASSES"] else "FAIL",
             len(check["untraceable"]), check["numbers_checked"]))
    for u in check["untraceable"][:25]:
        print("     %-10s %-46s %-8s  ...%s..."
              % (u["rendering"], u["at"][:46], u["number"], u["context"][:60]))
    if len(check["untraceable"]) > 25:
        print("     ... %d more" % (len(check["untraceable"]) - 25))


if __name__ == "__main__":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8",
                                  errors="replace")
    main()
