#!/usr/bin/env python3
"""THE ESTIMAND DECISION for `apixaban-vte-treatment`, made the way the other four were.

THE FIFTH INSTANCE, AND IT IS THE SHARPEST OF THE FIVE. Eleven trials, ONE DRUG, ONE INDICATION,
and their registered primaries decompose into FIVE DISTINCT COMPONENT SETS:

    {bleeding}                    4   a SAFETY endpoint as the primary -- not efficacy trials
    {vte}                         3
    {vte, death_vte_related}      2   AMPLIFY, APIDULCIS
    {dvt, pe}                     1   HI-PRO
    {vte, death_all_cause}        1   AMPLIFY-EXT

AND THE PAIR THAT SETTLES THE ARGUMENT:

    AMPLIFY      NCT00643201  n=5614  recurrent VTE or VTE-RELATED death
    AMPLIFY-EXT  NCT00633893  n=2711  recurrent VTE or ALL-CAUSE death

SAME SPONSOR, SAME PROGRAMME, SAME DRUG, SEQUENTIAL TRIALS, NAMES DIFFERING BY A HYPHENATED
SUFFIX -- AND DIFFERENT COMPOSITES. If two trials from one programme with almost the same name
do not share a definition, then a reviewer matching endpoints by NAME across independent
sponsors is not making an occasional error; they are using a method that does not work.

    FIVE INSTANCES IN ONE NIGHT ACROSS THREE DRUG CLASSES -- ablation-af-heart-failure (2),
    ablation-af-medical-therapy (3), early-rhythm-control-af (4), apixaban prophylaxis (4),
    apixaban treatment (11 into 5). THIS IS NO LONGER A FINDING ABOUT OUR TOPICS. IT IS A
    FINDING ABOUT COMPOSITE ENDPOINTS IN REGISTERED TRIALS.

THE WITHHOLDING QUESTION IS THEN ASKED AT EVERY REGISTERED RANK, because on two topics tonight
the harmonisable estimand was a SECONDARY and asking is the only thing that found it -- and on
a third the answer was a decisive no. Its answer is not predictable, which is what makes it a
check rather than a bias.
"""
import io
import json
import os
import re
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, "ssot"))
sys.path.insert(0, os.path.join(REPO, "scripts"))
import ctgov_transport as X                                        # noqa: E402
from lint_composite_by_components import components                # noqa: E402

SRC = os.path.join(REPO, "evidence", "2026-08-19-batch1",
                   "apixaban_treatment_extraction.json")
DEST = os.path.join(REPO, "evidence", "2026-08-19-batch1",
                    "apixaban_treatment_estimand.json")

# A RECURRENT-VTE EFFICACY OUTCOME, detected STRUCTURALLY rather than by the word "composite"
# (P33): a recurrence term plus a VTE term, at any rank.
RECUR = re.compile(r"recurr|new\s+episode|symptomatic", re.I)
VTE = re.compile(r"\bvte\b|venous thromboemboli|deep vein thrombos|\bdvt\b|"
                 r"pulmonary emboli|\bpe\b", re.I)


def all_ranks(nct):
    state, study, _d = X.fetch_raw(nct, fields="protocolSection,hasResults")
    if state != X.OK:
        return None
    om = ((study.get("protocolSection") or {}).get("outcomesModule") or {})
    out = []
    for rank, key in (("PRIMARY", "primaryOutcomes"), ("SECONDARY", "secondaryOutcomes"),
                      ("OTHER", "otherOutcomes")):
        for o in (om.get(key) or []):
            out.append((rank, o.get("measure") or ""))
    return out


def main():
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    with io.open(SRC, encoding="utf-8") as fh:
        ext = json.load(fh)

    print("THE WITHHOLDING QUESTION, AT EVERY REGISTERED RANK")
    print("Is a recurrent-VTE efficacy outcome present at ANY rank, in trials whose PRIMARY is "
          "something else?\n")
    found, absent, na = [], [], []
    for t in ext["trials"]:
        nct = t["nct"]
        rk = all_ranks(nct)
        if rk is None:
            na.append(nct)
            continue
        hits = [(r, m) for (r, m) in rk if RECUR.search(m) and VTE.search(m)]
        prim_set = frozenset(components((t.get("registered_primaries") or [""])[0]))
        row = {"nct": nct, "acronym": t.get("acronym"), "enrolment": t.get("enrolment"),
               "hasResults": t.get("hasResults"),
               "primary_components": sorted(prim_set),
               "recurrent_vte_at_ranks": [{"rank": r, "measure": m[:130]} for r, m in hits[:4]],
               "ranks_read": len(rk)}
        (found if hits else absent).append(row)
        print("   %-13s %-12s ranks=%-3d primary={%s}  recurrent-VTE at: %s"
              % (nct, (t.get("acronym") or "")[:12], len(rk),
                 ", ".join(sorted(prim_set)) or "UNDECOMPOSED",
                 ", ".join(sorted({r for r, _m in hits})) or "NOWHERE"))

    with_results = [r for r in found if r["hasResults"]]
    print("\n   trials with a recurrent-VTE outcome at SOME rank      %d of %d"
          % (len(found), len(ext["trials"])))
    print("   of those, with posted results                         %d" % len(with_results))
    print("   trials with NO recurrent-VTE outcome at any rank      %d" % len(absent))
    for r in absent:
        print("      %-13s primary={%s} -- this trial does not measure the review's question "
              "at any rank" % (r["nct"], ", ".join(r["primary_components"])))

    out = {
        "decided_utc": "2026-08-19",
        "topic": "apixaban-vte-treatment",
        "the_fifth_instance": {
            "n_trials": len(ext["trials"]),
            "n_distinct_primary_component_sets": 5,
            "sets": {"{bleeding}": 4, "{vte}": 3, "{vte, death_vte_related}": 2,
                     "{dvt, pe}": 1, "{vte, death_all_cause}": 1},
            "the_pair_that_settles_it": (
                "AMPLIFY (NCT00643201, n=5614) counts recurrent VTE or VTE-RELATED death. "
                "AMPLIFY-EXT (NCT00633893, n=2711) counts recurrent VTE or ALL-CAUSE death. "
                "SAME SPONSOR, SAME PROGRAMME, SAME DRUG, SEQUENTIAL TRIALS, NAMES DIFFERING BY "
                "A HYPHENATED SUFFIX -- AND DIFFERENT COMPOSITES. If two trials from one "
                "programme with almost the same name do not share a definition, a reviewer "
                "matching endpoints by NAME across independent sponsors is not making an "
                "occasional error; they are using a method that does not work."),
            "why_this_stops_being_about_our_topics": (
                "Five instances in one night across THREE drug classes and two specialties: "
                "ablation-af-heart-failure (2 trials), ablation-af-medical-therapy (3), "
                "early-rhythm-control-af (4), apixaban prophylaxis (4), apixaban treatment (11 "
                "into 5 sets). It is a finding about COMPOSITE ENDPOINTS IN REGISTERED TRIALS, "
                "not about this corpus's topic selection."),
        },
        "four_of_eleven_register_a_SAFETY_primary": {
            "which": ["NCT01780987", "NCT02585713", "NCT03196349", "NCT03266783"],
            "note": ("Their registered primary is a BLEEDING endpoint. They are eligible trials "
                     "of this drug in this population, and their PRIMARY does not answer this "
                     "review's efficacy question. That is exactly the shape that made the "
                     "prophylaxis review's previous k=1 figure not an estimate of its own "
                     "question -- a 400-patient trial reporting bleeding."),
        },
        "withholding_question": {
            "asked_on": "2026-08-19",
            "question": ("does each trial report a recurrent-VTE efficacy outcome at ANY "
                         "registered rank -- primary, secondary or other -- before concluding "
                         "which trials can be combined?"),
            "detected_structurally_not_by_keyword": (
                "A recurrence term plus a VTE term, at any rank -- P33. Not the word "
                "'composite', which CASTLE-AF's primary does not contain either."),
            "n_with_the_outcome_at_some_rank": len(found),
            "n_of_those_with_posted_results": len(with_results),
            "n_without_it_at_any_rank": len(absent),
        },
        "trials_with_the_shared_outcome": found,
        "trials_without_it_at_any_rank": absent,
        "not_assessable": na,
        "NOT_DONE_next_step": (
            "The arm-level event counts for the harmonised outcome have NOT been extracted and "
            "the pool has NOT been computed. That is the next unit and it is named rather than "
            "implied, because a decision recorded without its arithmetic is a decision, not a "
            "result."),
    }
    with io.open(DEST, "w", encoding="utf-8") as fh:
        fh.write(json.dumps(out, indent=1))
    print("\nwrote %s" % DEST)
    return 0


if __name__ == "__main__":
    sys.exit(main())
