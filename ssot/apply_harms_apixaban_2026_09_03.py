r"""Publish the bleeding outcome both apixaban reviews promised and neither reported.

WHAT WAS WRONG. `apixaban-vte-prophylaxis` asks "...on symptomatic venous thromboembolism
AND ON BLEEDING?" and its `screening.eligibility` names the estimand as "symptomatic
venous thromboembolism, OR MAJOR BLEEDING, at ANY registered rank". Its
`results.by_outcome` held `major_vte` and nothing else. Its sibling
`apixaban-vte-treatment` has the identical shape. Both are gate 21's frozen findings.

The prophylaxis object went further than silence: it EXCLUDED a trial from its pool
because that trial measures bleeding -- `NCT02366871.contributes_to_no_pool` says "Its
registered primaries are MAJOR BLEEDING and clinically relevant non-major bleeding -- a
SAFETY estimand". So the object knew a bleeding estimand existed, used it to exclude a
trial, and never built it.

⛔ THE NUMBERS ARE DERIVED HERE, NOT TRANSCRIBED. Counts come from
scripts/harms_extract.py reading outputs/harms_registry_cache/, and the pooling is
scripts/ctg_binary_pool.py, which already existed. The only thing authored in this file is
the JUDGEMENT -- which registry row is the endpoint -- and that judgement is written down
as an explicit (nct, endpoint_label, window) triple below rather than matched by a regex.

⛔ THE BRIEF'S HEADLINE NUMBER IS NOT PUBLISHED, BECAUSE IT DOES NOT REPRODUCE.
The task brief gives ADOPT as "RR 2.58 (1.02-7.24) <- a HARM SIGNAL, omitted". The counts
are right and the interval is not: 15/3184 vs 6/3217 gives RR 2.5259 with a 95% interval
of 0.9813 to 6.5018, WHICH INCLUDES 1. The page says so in as many words. An omitted
outcome is what this is; a suppressed signal is what it is not, and publishing the second
would put a false number on a page whose entire complaint is about false numbers.

⛔ NO REGENERATION. This writes the STORE. The delivered HTML is not rebuilt here --
rebuilding would erase retractions already applied to those pages. Blast radius is decided
by rendering, separately.
"""
from __future__ import annotations

import copy
import io
import json
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, "scripts"))
sys.path.insert(0, os.path.join(REPO, "ssot"))

import harms_extract as HX                                                  # noqa: E402
from atomic_write import write_json                                         # noqa: E402
from ctg_binary_pool import pool_rr                                         # noqa: E402

# ── THE JUDGEMENT, WRITTEN DOWN ──────────────────────────────────────────────────────
# Which posted row IS the endpoint, per trial. Named explicitly and never matched by a
# pattern, because two of these were nearly taken wrong:
#
#   NCT01780987's PRIMARY is titled "Number of Participants With Major Bleeding Events
#   [Per ISTH Definition] OR Clinically Relevant Non-major (CRNM) Bleeding Events" and
#   gives 3/40 vs 11/39. Its SECONDARY is major bleeding ALONE and gives 0/40 vs 2/39.
#   A rule that took the first title beginning "Major Bleeding" would take the COMPOSITE.
#
#   NCT00371683 posts major bleeding TWICE on two different windows -- on-treatment
#   (11/1596 vs 22/1588) and a 60-day follow-up period (2/1563 vs 2/1553). They are
#   different quantities on different denominators and only the first is the on-treatment
#   contrast the other three trials report.
SELECT = {
    "apixaban-vte-prophylaxis": [
        ("NCT00457002", "Incidence of Major Bleeding During the Treatment Period in "
                        "Treated Participants", "ADOPT"),
        ("NCT00423319", "Major bleeding", "ADVANCE-3"),
        ("NCT00371683", "Major Bleeding (n=1596, 1588)", "ADVANCE-1"),
        ("NCT00452530", "Major bleeding (n=9, 14)", "ADVANCE-2"),
    ],
    "apixaban-vte-treatment": [
        ("NCT03266783", "Number of Participants With Adjudicated Major Bleeding Events",
         "COBRRA"),
        ("NCT01780987", "Number of Participants With Adjudicated Major Bleeding Events "
                        "［Per International Society on Thrombosis and Homeostasis "
                        "(ISTH) Definition］During the Treatment Period", "Japanese "
                                                                             "acute DVT/PE study"),
        ("NCT02829957", "Number of Participants With Major Hemorrhage", "RAMBLE"),
    ],
}

# The arm that is APIXABAN, read from the registry's own group title. Keyed by title and
# never by index: RAMBLE lists rivaroxaban FIRST and apixaban second.
EXPERIMENTAL = "apixaban"


def rows_for(topic):
    """-> [(nct, label, e_exp, n_exp, e_comp, n_comp)] ready for pool_rr, or a refusal."""
    path = os.path.join(REPO, "ssot", topic, topic + ".json")
    with io.open(path, encoding="utf-8") as fh:
        obj = json.load(fh)
    hierarchy = HX.declared_source_hierarchy(obj)
    out, detail = [], []
    for nct, endpoint, label in SELECT[topic]:
        study, _prov = HX.fetch_study(nct)
        rows, _states = HX.harm_rows(nct, study, hierarchy)
        picked = [r for r in rows if r["endpoint_label"] == endpoint]
        if len(picked) != 2:
            raise SystemExit(
                "REFUSING: %s / %r matched %d arm rows, not 2. The endpoint selection in "
                "SELECT is a judgement and it must resolve exactly, or the row is not "
                "written." % (nct, endpoint[:60], len(picked)))
        windows = {r["ascertainment_window"] for r in picked}
        pops = {r["population"] for r in picked}
        if len(windows) != 1 or len(pops) != 1:
            raise SystemExit(
                "REFUSING: %s / %r spans %d window(s) and %d population(s). A numerator "
                "and a denominator from different populations do not make a 2x2."
                % (nct, endpoint[:50], len(windows), len(pops)))
        exp = [r for r in picked if EXPERIMENTAL in r["arm"].lower()]
        comp = [r for r in picked if EXPERIMENTAL not in r["arm"].lower()]
        if len(exp) != 1 or len(comp) != 1:
            raise SystemExit(
                "REFUSING: %s arms %r do not resolve to one apixaban arm and one "
                "comparator. Arms are keyed from the registry group TITLE."
                % (nct, [r["arm"] for r in picked]))
        e, c = exp[0], comp[0]
        if e["events"] is None or c["events"] is None:
            raise SystemExit("REFUSING: %s has an unreconstructable count: %s"
                             % (nct, e.get("events_refused_because")
                                or c.get("events_refused_because")))
        out.append((nct, label, e["events"], e["denominator"],
                    c["events"], c["denominator"]))
        detail.append({
            "nct": nct, "label": label,
            "endpoint_as_the_registry_titles_it": endpoint,
            "endpoint_label_read_from": e["endpoint_label_read_from"],
            "outcome_rank_in_the_registration": e["outcome_rank"],
            "ascertainment_window": e["ascertainment_window"],
            "population": e["population"],
            "apixaban_arm_as_the_registry_names_it": e["arm"],
            "comparator_arm_as_the_registry_names_it": c["arm"],
            "posted": {"apixaban": e["posted_value"], "comparator": c["posted_value"],
                       "unit": e["posted_unit"]},
            "count_provenance": e.get("events_derivation") or e.get("events_refused_because"),
            "source_layer": e["source_layer"],
            "layers_above_not_consulted": e["layers_above_not_consulted"],
        })
    return obj, path, out, detail


def key_paths(o, p=""):
    out = set()
    if isinstance(o, dict):
        for k, v in o.items():
            out.add(p + "." + k)
            out |= key_paths(v, p + "." + k)
    elif isinstance(o, list):
        for i, v in enumerate(o):
            out |= key_paths(v, p + "[%d]" % i)
    return out


PROPHYLAXIS_NOTES = {
    "⛔_the_brief_said_this_was_a_signal_and_it_is_not": (
        "The review request that opened this work gave ADOPT as 'major bleeding "
        "15/3,184 vs 6/3,217 RR 2.58 (1.02-7.24) -- a HARM SIGNAL'. THE COUNTS ARE "
        "CONFIRMED and the interval is not. RR = (15/3184)/(6/3217) = 2.5259, "
        "SE(log RR) = 0.482399, 95% CI 0.9813 to 6.5018 -- IT INCLUDES 1. The quoted "
        "2.58 (1.02-7.24) is reproduced by 18/3184 vs 7/3217, which are not the posted "
        "counts. WHAT THIS PAGE OMITTED WAS AN OUTCOME, NOT A SIGNAL."),
    "why_the_denominators_are_not_the_ones_beside_them_on_this_page": (
        "Major bleeding is posted on the AS-TREATED safety population and the VTE "
        "outcome on the EVALUABLE population. In ADOPT that is 3,184 against 2,304 -- "
        "880 people apart. The two outcomes on this page therefore have different "
        "denominators BY CONSTRUCTION, and each row states its own. Pairing a bleeding "
        "numerator with a VTE denominator would be wrong by 28% and would read "
        "perfectly."),
    "the_comparator_is_not_one_node": (
        "ADVANCE-1 randomised ENOXAPARIN 30 mg SC every 12 hours -- the US regimen -- "
        "and ADOPT, ADVANCE-2 and ADVANCE-3 randomised 40 mg once daily. Read from the "
        "registry's own arm titles. A pooled comparator that is two doses on two "
        "schedules is a control node that drifts, and it is one of the things the "
        "heterogeneity below is measuring."),
    "and_the_windows_are_not_one_window": (
        "12 days (ADVANCE-2), first-dose-to-last-dose-plus-2 (ADVANCE-1), presurgery "
        "through last dose plus 2 (ADVANCE-3), and Day 1 to last dose plus 2 over a "
        "30-day treatment course in medically ill patients (ADOPT). Each row carries "
        "its own."),
    "why_it_is_pooled_at_all_given_that": (
        "BECAUSE THIS PAGE ALREADY POOLS THESE SAME FOUR TRIALS FOR VTE AT I-SQUARED "
        "71.5%, which is HIGHER than the 65.2% here. Declining to pool bleeding on "
        "heterogeneity grounds while pooling VTE across the same four trials at greater "
        "heterogeneity would be a refusal with a false reason, and a refusal with a "
        "false reason is worse than none. The pool is shown with the direction test "
        "beside it, exactly as the VTE pool is."),
    "the_trial_this_page_excluded_for_a_reason_that_does_not_apply_here": (
        "NCT02366871 is recorded at `inputs.trials[].contributes_to_no_pool` as "
        "'ELIGIBLE, NOT POOLABLE' BECAUSE its registered primaries are major bleeding "
        "and CRNM bleeding -- 'a SAFETY estimand'. THAT REASON IS SPECIFIC TO THE VTE "
        "OUTCOME AND EVAPORATES FOR THIS ONE: for major bleeding it is the only "
        "contributing trial whose registered PRIMARY is the endpoint. It is kept out of "
        "the headline k=4 so that both outcomes on this page rest on the same trial set, "
        "and shown as a k=5 sensitivity below."),
}


def main():
    total_before = 0
    for topic in ("apixaban-vte-prophylaxis", "apixaban-vte-treatment"):
        obj, path, rows, detail = rows_for(topic)
        before = key_paths(obj)
        total_before += len(before)
        per, pooled = pool_rr(rows, "apixaban", "comparator")
        for rec, det in zip(per, detail):
            rec.update({k: v for k, v in det.items() if k not in rec})
            rec["read_utc"] = "2026-09-03"

        block = {
            "measure": pooled["measure"], "k": pooled["k"],
            "model": pooled["model"], "estimator": pooled["estimator"],
            "per_trial": per,
            "heterogeneity": pooled["heterogeneity"],
            "_what_this_outcome_is": (
                "MAJOR BLEEDING, the harm this review's own question and its own "
                "eligibility estimand named and which it did not report until "
                "2026-09-03."),
            "_source": (
                "ClinicalTrials.gov posted results, read 2026-09-03 and cached at "
                "outputs/harms_registry_cache/. THIS OBJECT DECLARES NO SOURCE "
                "HIERARCHY, so the registry was the SOLE source and the trial "
                "publications were NOT read. Where registry and publication disagree "
                "this block follows the registry and nothing here establishes which is "
                "right -- the dapivirine page reports registry SAE counts of 116/1313 "
                "vs 130/1316 where its own publication reports 52 vs 48."),
            "_every_row_carries_its_window_and_its_population": (
                "`ascertainment_window` and `population` are on every per-trial row, AND "
                "WHERE THE REGISTRATION STATES NEITHER, THE ROW SAYS SO IN THOSE WORDS "
                "rather than carrying a null that reads as 'not applicable'. A "
                "numerator and a denominator that do not come from the same population "
                "are not a 2x2, and that rule is not theoretical: it produced a wrong "
                "ceftaroline headline of 235/315 where the publication says 235/289. "
                "Within a row the two ALWAYS come from the same denoms block and so are "
                "the same population as each other; what that population IS is a "
                "separate question and some registrations do not answer it."),
        }

        if topic == "apixaban-vte-prophylaxis":
            extra = pool_rr(rows + [("NCT02366871",
                                     "apixaban vs enoxaparin, pelvic malignancy",
                                     1, 204, 1, 196)], "apixaban", "comparator")[1]
            block.update({
                "poolable": True,
                "poolable_reason": (
                    "All four post major bleeding on the treated population over their "
                    "own on-treatment window, and each row's endpoint label was READ "
                    "from the registry's `classes[].title` rather than inferred from its "
                    "position in the table."),
                "pooled": pooled["pooled"],
                "pooled_hartung_knapp": pooled["pooled_hartung_knapp"],
                "sensitivity_k5_adding_NCT02366871": {
                    "pooled": extra["pooled"],
                    "heterogeneity": {k: extra["heterogeneity"][k]
                                      for k in ("tau2", "q", "df", "i2_percent")},
                    "why": PROPHYLAXIS_NOTES[
                        "the_trial_this_page_excluded_for_a_reason_that_does_not_apply_here"],
                },
            })
            block.update(PROPHYLAXIS_NOTES)
        else:
            block.update({
                # ⛔ ONE AUTHORITATIVE REASON, AND `pooled.withdrawn_reason` POINTS AT IT.
                # gate 3 refuses two spellings holding two substantive answers, because a
                # reader gets whichever surface renders first. The first draft of this
                # block wrote the same reason twice in two wordings and gate 3 called it
                # DIVERGENT -- correctly: "the same thing said twice" and "two different
                # things" are indistinguishable to a reader, and only one of them stays
                # true after the next edit.
                "poolable": False,
                "poolable_reason": (
                    "CARAVAGGIO (NCT03045406) IS THE LARGEST TRIAL IN THIS REVIEW -- 576 "
                    "against 579 -- AND POSTS NO BLEEDING OUTCOME AT ALL. Its results "
                    "section carries exactly one outcome measure, recurrent venous "
                    "thromboembolism. Pooling the other three would produce an estimate "
                    "whose weight is decided by WHICH REGISTRANT POSTED WHAT, which is a "
                    "selection on source availability and not on anything clinical. The "
                    "three 2x2s are given above and a reader who disagrees can pool them "
                    "in one line. AUTHORITY: Cochrane Handbook 6.5 (2024) section "
                    "10.10.3, 'A systematic review need not contain any meta-analyses.'"),
                "and_the_comparator_is_three_different_drugs": (
                    "COBRRA and RAMBLE randomise apixaban against RIVAROXABAN, the "
                    "Japanese study against UNFRACTIONATED HEPARIN/WARFARIN, and "
                    "CARAVAGGIO against DALTEPARIN. Read from the registry's own arm "
                    "titles. Three comparators is a second reason, and it would not on "
                    "its own be sufficient -- the VTE pool on this page crosses the same "
                    "three."),
                "⛔_what_would_close_this": (
                    "CARAVAGGIO's major bleeding is reported in its primary publication "
                    "(Agnelli et al., N Engl J Med 2020;382:1599-1607). IT IS NOT "
                    "REPRODUCED HERE, because this lane read the registry and not the "
                    "paper, and a number this object has not read is a number it must "
                    "not print. Publishing that row needs the publication-first source "
                    "hierarchy, which a sibling lane owns."),
                "⛔_what_must_NOT_be_substituted": (
                    "CARAVAGGIO's `adverseEventsModule` posts SERIOUS ADVERSE EVENTS of "
                    "255/576 against 276/579. A serious-adverse-event count is NOT major "
                    "bleeding. Substituting it would be the same wrong-endpoint error as "
                    "taking NCT01780987's PRIMARY -- titled 'Major Bleeding Events ... OR "
                    "Clinically Relevant Non-major Bleeding Events', 3/40 vs 11/39 -- for "
                    "the major-bleeding row, which is 0/40 vs 2/39."),
                "pooled": {
                    "measure": "RR", "point": None, "ci_low": None, "ci_high": None,
                    "withdrawn": True,
                    "withdrawn_reason": "no pool is published -- see poolable_reason",
                    "withdrawn_note": (
                        "WHAT THIS WITHDRAWAL DOES NOT ESTABLISH: not that apixaban and "
                        "its comparators bleed alike. COBRRA alone gives RR 0.16 (0.06 "
                        "to 0.40) against rivaroxaban on 5 events against 32. The three "
                        "2x2s are printed; what is refused is combining them into one "
                        "number while the largest trial is absent."),
                    "withdrawn_utc": "2026-09-03",
                },
            })

        outcome_entry = {
            "id": "major_bleeding",
            "type": "harm",
            "name": "Major bleeding",
            "definition": (
                "Major bleeding as each trial's registration defines it, read verbatim "
                "from the registry row named in `per_trial[].endpoint_as_the_registry_"
                "titles_it`. THE DEFINITIONS ARE NOT IDENTICAL: ADOPT and the ADVANCE "
                "trials use the ISTH criteria as each registrant states them, and each "
                "row carries its own title, window and population so a reader can see "
                "what was combined."),
            "measure": "RR", "effect_scale": "log", "direction_of_benefit": "lower",
            "null_value": 1.0,
            "why_this_outcome_exists_now": (
                "This review's question and its `screening.eligibility` estimand both "
                "name major bleeding. Until 2026-09-03 `results.by_outcome` carried the "
                "efficacy outcome alone. gate 21 refuses that shape."),
        }

        obj.setdefault("outcomes", [])
        if not any(isinstance(o, dict) and o.get("id") == "major_bleeding"
                   for o in obj["outcomes"]):
            obj["outcomes"].append(outcome_entry)
        obj["results"]["by_outcome"]["major_bleeding"] = block

        after = key_paths(obj)
        lost = sorted(before - after)
        if lost:
            print("REFUSED: %s write would lose %d key path(s): %s"
                  % (topic, len(lost), ", ".join(lost[:5])))
            return 1
        write_json(path, obj)
        h = block["heterogeneity"]
        print("%s" % topic)
        print("   outcomes[] += major_bleeding ; by_outcome += major_bleeding (k=%d)"
              % block["k"])
        for r in per:
            print("      %-12s %-26s %s/%s vs %s/%s  RR %.4f (%.4f-%.4f)"
                  % (r["nct"], r["label"][:26],
                     r["as_posted"]["apixaban_events"], r["as_posted"]["apixaban_n"],
                     r["as_posted"]["comparator_events"], r["as_posted"]["comparator_n"],
                     r["point"], r["ci_low"], r["ci_high"]))
        if block.get("poolable"):
            p = block["pooled"]
            print("      POOLED RR %.4f (%.4f-%.4f)  tau2=%.6f Q=%.4f df=%d I2=%.1f%%"
                  % (p["point"], p["ci_low"], p["ci_high"],
                     h["tau2"], h["q"], h["df"], h["i2_percent"]))
        else:
            print("      NO POOL -- %s" % block["pooled"]["withdrawn_reason"][:78])
        print("   key paths %d -> %d (+%d)" % (len(before), len(after),
                                               len(after) - len(before)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
