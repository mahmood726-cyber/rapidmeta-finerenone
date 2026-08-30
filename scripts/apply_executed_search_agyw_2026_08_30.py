# -*- coding: utf-8 -*-
"""Write the EXECUTED search into agyw-hiv-prep-review, replacing the convenience sample.

⭐ THIS IS A CORRECTION, NOT A CHANGE OF CLAIM. The object records five SEEDED registrations
read on 2026-08-18 and no search. A blinded judge read the page and wrote: "A explicitly
states it used a convenience sample without a primary search." That statement is now FALSE
-- the search has been run -- and leaving it would mean knowingly serving a page that
understates its own method.

⛔ THE TWO FACTS ARE KEPT APART IN THE OBJECT, NOT ONLY IN THE NOTES.

    the SEARCH is complete            2 of 2 eligible trials, zero misses
    the RISK OF BIAS is NOT complete  D1.2, D2 and D3 remain NO_INFORMATION

Closing one gap must not be allowed to imply the other closed with it. They are written as
separate keys with separate wording, and the search block says in terms that it makes no
claim about risk of bias. This is exactly the drift we would catch in someone else's page.

⚠️ AND THE LIMITS TRAVEL WITH THE CLAIM. The panel scores this project 4-1 on transparency
BECAUSE its limits are named; a search block that recorded only the 2-of-2 would trade the
axis we win for the axis we lost. Every limit measured today is written in beside it.

Written with `atomic_write`, which preserves the file's existing newline. An earlier
applier used a plain open() and flipped two objects from LF to CRLF, turning a 713-line
addition into a 9,256-line diff.
"""
import datetime
import io
import json
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, "..", "ssot"))

import atomic_write as aw  # noqa: E402

TOPIC = "agyw-hiv-prep-review"
UTC = datetime.datetime.now(datetime.timezone.utc).isoformat()

SEARCH = {
    "executed_utc": UTC,
    "search_date": "2026-08-30",
    "supersedes": (
        "The five SEEDED registrations read on 2026-08-18. Those were a convenience "
        "sample and this object said so; a blinded reviewer identified it as such. A "
        "primary search has now been executed and the earlier basis is superseded rather "
        "than deleted -- the seeded set is still recorded under `inputs`."),
    "scope_rule": (
        "FREE SOURCES ONLY. No subscription database is used in the method, because a "
        "search the reader cannot reproduce is not verifiable by the reader it is for. "
        "Embase is used once, separately, as a calibration ruler and never as a source."),
    "concept_block": ["dapivirine", "dapavirine", "TMC 120", "TMC-120", "TMC120",
                      "R 147681", "R-147681", "R147681"],
    "no_and_block_because": (
        "dapivirine and its development codes are specific to one compound, so an "
        "AND-block for HIV, vaginal rings or study design can only REMOVE records. On a "
        "set this size precision is not the binding constraint and the whole set is "
        "screened instead."),
    "development_codes_included_because": (
        "TMC 120 and R 147681 are the MeSH entry terms, verified against the NLM browser "
        "on 2026-08-30 rather than recalled. The phase 1/2 and IPM programme literature "
        "uses the development codes rather than the INN, so a query without them silently "
        "loses that end of the record."),
    "sources": [
        {"source": "PubMed (NCBI E-utilities)", "status": "OK",
         "reported": 374, "retrieved": 374},
        {"source": "Europe PMC", "status": "TRUNCATED",
         "reported": 1443, "retrieved": 1000,
         "note": ("The page cap. The remaining 443 were NOT fetched and are NOT recorded "
                  "as absent. Paging is required before any Europe PMC figure enters a "
                  "denominator.")},
        {"source": "ClinicalTrials.gov API v2", "status": "OK", "retrieved": 63,
         "note": ("Union of an intervention query and a free-text query, because a drug "
                  "can be an intervention on one record and only a summary mention on "
                  "another; either alone loses trials.")},
        {"source": "ISRCTN (/api/query, the robots-permitted path)", "status": "OK",
         "reported": 1, "retrieved": 1},
        {"source": "EU-CTR", "status": "EMPTY", "note": "browser-verified 2026-08-30"},
        {"source": "DRKS", "status": "EMPTY", "note": "browser-verified 2026-08-30"},
    ],
    "screen": {
        "candidates_screened": 63,
        "passed_screen": 5,
        "excluded_not_dapivirine": 16,
        "excluded_not_a_ring": 20,
        "excluded_not_randomised": 4,
        "excluded_not_phase3_efficacy": 16,
        "excluded_withdrawn_zero_participants": 2,
        "withdrawn_named": ["NCT01337570", "NCT01337583"],
        "withdrawn_named_because": (
            "Both are 'A Safety and Efficacy Trial of Dapivirine Vaginal Ring in Africa', "
            "both double-blind randomised placebo-controlled phase 3 BY DESIGN, both "
            "WITHDRAWN with enrolment 0 (ACTUAL). Eligible in design, no participants and "
            "no data, so they cannot contribute to a synthesis. Named rather than dropped: "
            "an eligibility exclusion is a decision and a decision should be visible."),
    },
    "adjudication_of_non_included_that_passed_screen": [
        {"nct": "NCT03965923", "comparator": "oral Truvada, open label",
         "primary_outcome": "safety adverse events; pregnancy outcomes",
         "verdict": "ELIGIBILITY"},
        {"nct": "NCT04140266", "comparator": "oral Truvada",
         "primary_outcome": "serious adverse events",
         "verdict": "ELIGIBILITY"},
        {"nct": "NCT06250504", "comparator": "enhanced standard of care",
         "primary_outcome": "PrEP uptake and retention",
         "verdict": "ELIGIBILITY"},
    ],
    "adjudication_rule": (
        "The screen tests phase and randomisation; it does NOT test the comparator or the "
        "outcome. A raw set difference is therefore never reported as a recall figure -- "
        "each difference is attributed to a search miss, an eligibility difference or a "
        "source boundary, and only the first measures recall."),
    "coverage_fraction": {
        "eligible_trials_identified": 2,
        "eligible_trials_held": 2,
        "recall": "2 of 2",
        "search_misses": 0,
        "means": ("Of the trials this search identifies as eligible for this question, "
                  "this review holds both. Both were FOUND by the search rather than "
                  "merely confirmed by it, and nothing in the included set failed the "
                  "screen."),
    },
    "limits": [
        ("Six chemical-name forms. Ovid showed Emtree expanding `dapivirine` to variants "
         "such as 4-[[4-[(2,4,6-trimethylphenyl)amino]pyrimidin-2-yl]amino]benzonitrile. "
         "A record indexed ONLY under such a form is invisible to every query used here. "
         "This is the one named mechanism by which a free-source search could miss a "
         "trial."),
        "Europe PMC truncated at 1,000 of 1,443 reported records.",
        ("Non-US registries: 2 of the 18 WHO ICTRP primary registries returned a "
         "determinate answer by script, plus DRKS verified in a browser. CRiS refuses by "
         "robots.txt; jRCT forbids automated download in its page text; ten have no free "
         "query endpoint established. THIS REVIEW DOES NOT CLAIM TO HAVE SEARCHED ICTRP."),
        ("Guideline bodies are NOT enumerated. GIN's member directory sits behind a "
         "member login and cannot serve as a free denominator. Not claimed."),
    ],
    "makes_no_claim_about": (
        "⚠️ THIS BLOCK CONCERNS THE SEARCH ONLY. It says nothing about the completeness of "
        "the risk-of-bias assessment, which is recorded separately and is NOT complete. A "
        "complete search and a complete appraisal are different claims and this review "
        "makes only the first."),
    "reproduce_with": ["scripts/systematic_search_dapivirine.py",
                       "scripts/registry_search.py"],
}

ROB_STATUS = {
    "complete": False,
    "as_at": UTC,
    "what_is_missing": (
        "Signalling questions 1.2 (allocation concealment), 2.6 (appropriate analysis to "
        "estimate the effect of assignment) and 3.1 (outcome data available for all or "
        "nearly all participants) are NO_INFORMATION for the contributing results, "
        "because the assessment was made from ClinicalTrials.gov registration records and "
        "a registration does not report them."),
    "why_the_regulatory_route_does_not_close_it": (
        "The FDA Integrated Review route that completes RoB 2 domains D1-D4 elsewhere in "
        "this corpus does not apply here: NO FDA APPLICATION EXISTS for dapivirine, which "
        "is a fact about the drug rather than a retrieval failure -- the ring was never "
        "FDA-approved and holds an EMA Article 58 positive scientific opinion and WHO "
        "prequalification instead. The EMA site presents a bot-detection challenge, which "
        "was NOT bypassed. WHO prequalification documents have not yet been located and "
        "no claim is made about them either way."),
    "what_would_close_it": (
        "ASPIRE/MTN-020's primary report is FREE TO READ at PMC4993693 and states its "
        "analysis population in terms, so that trial needs no special access. The Ring "
        "Study/IPM 027 primary report (PMID 27959766, N Engl J Med) has no PMC record and "
        "is the only document for which access is in question."),
    "must_not_be_read_as": (
        "⚠️ THE SEARCH BEING COMPLETE DOES NOT MAKE THIS COMPLETE. They are separate "
        "claims about separate things and this review asserts only the first."),
}


def main(apply_changes=False):
    path = os.path.join(_HERE, "..", "ssot", TOPIC, "%s.json" % TOPIC)
    if not os.path.exists(path):
        print("OBJECT NOT FOUND: %s" % path)
        return 1
    with open(path, encoding="utf-8") as fh:
        obj = json.load(fh)

    before_keys = set(obj)
    obj["search_executed_2026_08_30"] = SEARCH
    obj["risk_of_bias_completeness_2026_08_30"] = ROB_STATUS
    # The superseded basis is corrected in place, and the old wording is preserved rather
    # than deleted -- a claim that was true when written should not vanish silently.
    if isinstance(obj.get("verification_basis"), str):
        obj["verification_basis_superseded_2026_08_30"] = obj["verification_basis"]
        obj["verification_basis"] = (
            "A PRIMARY SEARCH was executed on 2026-08-30 across PubMed, Europe PMC, "
            "ClinicalTrials.gov and the ICTRP primary registries reachable freely; see "
            "`search_executed_2026_08_30`. It identifies 2 eligible trials and this review "
            "holds both. The five seeded registrations read on 2026-08-18 -- the earlier "
            "basis, preserved in `verification_basis_superseded_2026_08_30` -- are no "
            "longer the basis for inclusion. ⚠️ The risk-of-bias assessment is NOT "
            "complete; see `risk_of_bias_completeness_2026_08_30`.")

    added = sorted(set(obj) - before_keys)
    print("keys added: %s" % ", ".join(added))
    print("search block: %d sources, coverage %s, %d limits"
          % (len(SEARCH["sources"]), SEARCH["coverage_fraction"]["recall"],
             len(SEARCH["limits"])))
    print("rob completeness: complete=%s" % ROB_STATUS["complete"])
    if not apply_changes:
        print("dry run -- pass --apply to write")
        return 0
    n = aw.write_json(path, obj)
    print("WRITTEN %d bytes, newline preserved" % n)
    return 0


if __name__ == "__main__":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.exit(main(apply_changes="--apply" in sys.argv))
