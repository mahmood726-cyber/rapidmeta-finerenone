#!/usr/bin/env python3
"""Write attr-cm-review's P3 criteria provenance. Fourth distinct handling of `predefined`.

Across four topics this field has now been set four different ways, each correct for its case,
which is what a three-state field is for:

    sglt2-hf               null   criteria are the object's OWN, but no protocol exists, so
                                  pre-specification cannot be established EITHER WAY
    iv-iron-hf             null   same, and the object states no criterion refers to membership
                                  of a list -- the signature of criteria written backwards
    alirocumab-lipid       false  no eligibility block existed; the criteria were derived AFTER
                                  the included set, so the ORDER is known
    attr-cm-review         false  same order, and additionally the object's `question` field
                                  holds a FINDING rather than a question, so there was not even
                                  a stated question to derive from -- only an estimand
"""
import io
import json
import os

OBJ = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                   "ssot", "attr-cm-review", "attr-cm-review.json")

PROVENANCE = {
    "state": "DERIVED_POST_HOC",
    "predefined": False,
    "post_hoc": True,
    "derived": True,
    "predefined_is_false_because": (
        "screening.eligibility reads 'not recorded on the page this object was built from', so "
        "no eligibility block ever existed. The criteria below were derived on 2026-08-19 from "
        "the object's included set and its recorded estimand, AFTER both existed. `false` is "
        "asserted rather than left null because the ORDER is known: the trials came first. "
        "AND THIS TOPIC IS THE WEAKEST CASE OF THE FOUR -- its `question` field holds a FINDING "
        "('the two hierarchies are not the same hierarchy') rather than a question, so there "
        "was not even a stated question to derive from, only an estimand."),
    "authority_it_satisfies": "MECIR R29/R30/R31 -- the review STATES its eligibility criteria.",
    "authority_it_does_NOT_establish": "MECIR C5/C7 -- criteria DEFINED IN ADVANCE.",
    "what_would_settle_it": "a protocol record timestamped before the first executed query",
    "elements": [
        {"element": "POPULATION", "criterion": "adults with transthyretin amyloid CARDIOMYOPATHY",
         "auditable_against": "protocolSection.conditionsModule.conditions",
         "settles_it": True,
         "evidence": "Both included registrations name amyloid cardiomyopathy. The limb does "
                     "real work at screening: ATTR POLYNEUROPATHY trials share the same drugs "
                     "and are a different disease in a different population, and were excluded "
                     "on this ground."},
        {"element": "INTERVENTION", "criterion": "tafamidis or acoramidis",
         "auditable_against": "protocolSection.armsInterventionsModule.interventions[].name",
         "settles_it": True,
         "evidence": "Matched against the declared synonym set -- tafamidis, vyndaqel, "
                     "vyndamax, FX-1006A, PF-06291826, acoramidis, AG10, attruby."},
        {"element": "COMPARATOR", "criterion": "placebo",
         "auditable_against": "protocolSection.armsInterventionsModule.armGroups",
         "settles_it": True,
         "evidence": "Both included trials declare a placebo arm. THE LIMB CARRIES MOST OF THE "
                     "EXCLUSIONS: only 6 of the 46 screened remainder trials declare a placebo "
                     "arm at all -- this drug programme is dominated by open-label extension "
                     "and single-arm studies."},
        {"element": "OUTCOME / ESTIMAND",
         "criterion": "a hierarchical composite analysed by win ratio -- AND the SAME hierarchy",
         "auditable_against": "protocolSection.outcomesModule.primaryOutcomes[].measure",
         "settles_it": False,
         "evidence_and_why_it_does_not_settle": (
             "THIS IS THE LIMB THAT DECIDES THE TOPIC AND NO FIELD SETTLES IT. Both included "
             "trials pass 'hierarchical win ratio' -- and they still cannot be combined, "
             "because ATTR-ACT's hierarchy is mortality plus CV hospitalisation (2 tiers) "
             "while ATTRibute-CM's adds NT-proBNP and 6-minute-walk change (4 tiers). A win "
             "ratio's estimand IS its hierarchy. Comparing two hierarchies for identity is a "
             "READING of two verbatim strings, not a field lookup, so it is recorded as "
             "DERIVED. TWO DIFFERENT HIERARCHIES ARE TWO ESTIMANDS, NOT HETEROGENEITY."),
         "derived_by": "comparison of the two verbatim primaryOutcomes[0].measure strings, "
                       "read from the registry 2026-08-19"},
    ],
    "elements_summary": (
        "4 elements: 3 settled by a named registry field, 1 -- the one that decides whether "
        "this review can pool at all -- NOT settled by any field and labelled DERIVED. The "
        "unsettled count is stated because a provenance block listing only its auditable "
        "elements would report that everything is auditable."),
}


def main():
    with io.open(OBJ, encoding="utf-8") as fh:
        obj = json.load(fh)
    scr = obj.setdefault("screening", {})
    before = set(scr.keys())
    scr["eligibility_provenance"] = PROVENANCE
    assert before <= set(scr.keys()), "ADDS only"
    with io.open(OBJ, "w", encoding="utf-8", newline="") as fh:
        fh.write(json.dumps(obj, indent=1, ensure_ascii=False) + "\n")
    print("provenance written: %d elements, %d settled by a field"
          % (len(PROVENANCE["elements"]),
             sum(1 for e in PROVENANCE["elements"] if e["settles_it"])))


if __name__ == "__main__":
    main()
