#!/usr/bin/env python3
"""EXTRACT THE PERICARDITIS NUMBERS FROM THE PUBLISHED REPORTS -- the first literature limb.

WHY THIS IS A METHOD PROOF AND NOT A ROUTINE EXTRACTION. Every estimate in this corpus so far
rests on registry-POSTED results. Reading a published report is a different provenance with
different failure modes, so the first one is done cell by cell: each number records WHERE IN THE
PAPER it came from, and NOTHING is computed from another cell. A percentage is not turned into a
count, and a count is not turned into a denominator.

AND THE FIRST THING IT DID WAS REFUTE A CLAIM I MADE FROM THE REGISTRY.

I reported that three of the five pericarditis trials -- NCT00128414, NCT00128453, NCT00235079 --
register the IDENTICAL primary verbatim, "Recurrence rate at 18 months", all against placebo, and
called that "a k=3 pool blocked by nothing except the registry's silence". THE REGISTERED TITLES
DO MATCH. THE TRIALS DO NOT.

    NCT00128453 is ICAP, and it is not a recurrence trial at all: 240 adults with a FIRST
    ATTACK OF ACUTE PERICARDITIS, and its published primary outcome is "incessant or recurrent
    pericarditis" -- a composite that counts INCESSANT disease, which the other two do not.

    NCT00128414 is CORP: 120 patients with a FIRST RECURRENCE.
    NCT00235079 is CORP-2: 240 patients with MULTIPLE recurrences (>=2).

THREE DIFFERENT DISEASE STAGES, and the registry's primary-outcome title carries none of that.
The population is the axis, and it is invisible in the field I matched on. A pool across these is
a judgement about whether disease stage is poolable -- it must be DECLARED, never assumed from a
title match.

  THE LESSON IS THE SHAPE, NOT THE INSTANCE. Exact title matching was already labelled a LOWER
  BOUND for false negatives -- two trials measuring one thing under different names. This is the
  other direction: A FALSE POSITIVE, three trials measuring different things under one name.
  P37 says composite names are not definitions. This says REGISTERED TITLES ARE NOT ESTIMANDS,
  because the estimand includes the population and the title does not.

WHAT IS EXTRACTED. Only what the source states in the words quoted beside it. Where the abstract
gives a percentage without its arm denominator, THE DENOMINATOR IS RECORDED AS NOT STATED rather
than divided out of the total -- CORP is exactly that case and is left incomplete on purpose.

ALL BIBLIOGRAPHIC DETAIL ACCORDING TO PUBMED, retrieved 2026-08-19.
"""
import io
import json
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(REPO, "evidence", "2026-08-19-batch1",
                   "pericarditis_publication_extraction.json")

NOT_STATED = "NOT_STATED_IN_THE_SOURCE_READ"

TRIALS = [
    {
        "nct": "NCT00128414", "acronym": "CORP",
        "pmid": "21873705", "doi": "10.7326/0003-4819-155-7-201110040-00359",
        "citation": ("Imazio M, Brucato A, Cemin R, et al. Colchicine for recurrent "
                     "pericarditis (CORP): a randomized trial. Ann Intern Med "
                     "2011;155(7):409-14."),
        "source_read": "PubMed abstract, retrieved 2026-08-19",
        "population_as_the_paper_states_it": {
            "value": "120 patients with a first recurrence of pericarditis",
            "quote": "120 patients with a first recurrence of pericarditis",
            "where": "abstract, PATIENTS section",
        },
        "primary_outcome_as_the_paper_states_it": {
            "value": "recurrence rate at 18 months",
            "quote": "The primary study end point was the recurrence rate at 18 months.",
            "where": "abstract, MEASUREMENTS section",
        },
        "comparator_as_the_paper_states_it": {
            "value": "placebo, in addition to conventional treatment",
            "quote": ("In addition to conventional treatment, patients were randomly assigned "
                      "to receive either placebo or colchicine"),
            "where": "abstract, INTERVENTION section",
        },
        "cells": {
            "colchicine_recurrence_percent": {
                "value": 24.0, "quote": "the recurrence rate was 24% in the colchicine group",
                "where": "abstract, RESULTS"},
            "placebo_recurrence_percent": {
                "value": 55.0, "quote": "55% in the placebo group",
                "where": "abstract, RESULTS"},
            "colchicine_events": {
                "value": None, "state": NOT_STATED,
                "why": ("The abstract gives a PERCENTAGE and no arm-level count. Multiplying "
                        "24% by an assumed 60 would be computing a cell from other cells, "
                        "which is the one thing this extraction does not do.")},
            "placebo_events": {"value": None, "state": NOT_STATED, "why": "as above"},
            "colchicine_n": {
                "value": None, "state": NOT_STATED,
                "why": ("The abstract states 120 patients TOTAL and does not give the "
                        "randomised split per arm. 60/60 is the obvious guess and is not "
                        "stated. The full text is required.")},
            "placebo_n": {"value": None, "state": NOT_STATED, "why": "as above"},
            "total_randomised": {
                "value": 120, "quote": "120 patients with a first recurrence of pericarditis",
                "where": "abstract, PATIENTS"},
        },
        "extraction_state": "INCOMPLETE_BY_DESIGN",
        "what_is_needed": ("Arm-level counts and denominators from the full text. Reported as "
                           "missing rather than derived."),
    },
    {
        "nct": "NCT00128453", "acronym": "ICAP",
        "pmid": "23992557", "doi": "10.1056/NEJMoa1208536",
        "citation": ("Imazio M, Brucato A, Cemin R, et al. A randomized trial of colchicine "
                     "for acute pericarditis. N Engl J Med 2013;369(16):1522-8."),
        "source_read": "PubMed abstract, retrieved 2026-08-19",
        "population_as_the_paper_states_it": {
            "value": "adults with ACUTE pericarditis -- a FIRST attack, not a recurrence",
            "quote": "eligible adults with acute pericarditis were randomly assigned",
            "where": "abstract, METHODS",
        },
        "primary_outcome_as_the_paper_states_it": {
            "value": "incessant OR recurrent pericarditis",
            "quote": "The primary study outcome was incessant or recurrent pericarditis.",
            "where": "abstract, METHODS",
            "note": ("THIS IS NOT THE SAME ENDPOINT AS CORP OR CORP-2. It counts INCESSANT "
                     "disease as well as recurrence, and the registry title for this "
                     "registration nevertheless reads 'Recurrence rate at 18 months'."),
        },
        "comparator_as_the_paper_states_it": {
            "value": ("placebo, in addition to conventional anti-inflammatory therapy with "
                      "aspirin or ibuprofen"),
            "quote": ("either colchicine ... or placebo in addition to conventional "
                      "antiinflammatory therapy with aspirin or ibuprofen"),
            "where": "abstract, METHODS",
        },
        "cells": {
            "colchicine_events": {
                "value": 20, "quote": "occurred in 20 patients (16.7%) in the colchicine group",
                "where": "abstract, RESULTS"},
            "colchicine_n": {
                "value": 120, "quote": "120 were randomly assigned to each of the two study "
                                       "groups",
                "where": "abstract, RESULTS"},
            "placebo_events": {
                "value": 45, "quote": "45 patients (37.5%) in the placebo group",
                "where": "abstract, RESULTS"},
            "placebo_n": {
                "value": 120, "quote": "120 were randomly assigned to each of the two study "
                                       "groups",
                "where": "abstract, RESULTS"},
            "total_randomised": {
                "value": 240, "quote": "A total of 240 patients were enrolled",
                "where": "abstract, RESULTS"},
        },
        "extraction_state": "COMPLETE_FROM_THE_ABSTRACT",
    },
    {
        "nct": "NCT00235079", "acronym": "CORP-2",
        "pmid": "24694983", "doi": "10.1016/S0140-6736(13)62709-9",
        "citation": ("Imazio M, Belli R, Brucato A, et al. Efficacy and safety of colchicine "
                     "for treatment of multiple recurrences of pericarditis (CORP-2). Lancet "
                     "2014;383(9936):2232-7."),
        "source_read": "PubMed abstract, retrieved 2026-08-19",
        "population_as_the_paper_states_it": {
            "value": "adult patients with MULTIPLE recurrences of pericarditis (>=2)",
            "quote": "Adult patients with multiple recurrences of pericarditis",
            "where": "abstract, METHODS",
        },
        "primary_outcome_as_the_paper_states_it": {
            "value": "recurrent pericarditis, in the intention-to-treat population",
            "quote": ("The primary outcome was recurrent pericarditis in the "
                      "intention-to-treat population."),
            "where": "abstract, METHODS",
        },
        "comparator_as_the_paper_states_it": {
            "value": ("placebo, in addition to conventional anti-inflammatory treatment with "
                      "aspirin, ibuprofen, or indometacin"),
            "quote": ("randomly assigned (1:1) to placebo or colchicine ... in addition to "
                      "conventional anti-inflammatory treatment"),
            "where": "abstract, METHODS",
        },
        "cells": {
            "colchicine_events": {
                "value": 26, "quote": "26 (21.6%) of 120 in the colchicine group",
                "where": "abstract, FINDINGS"},
            "colchicine_n": {
                "value": 120, "quote": "26 (21.6%) of 120 in the colchicine group",
                "where": "abstract, FINDINGS"},
            "placebo_events": {
                "value": 51, "quote": "51 (42.5%) of 120 in the placebo group",
                "where": "abstract, FINDINGS"},
            "placebo_n": {
                "value": 120, "quote": "51 (42.5%) of 120 in the placebo group",
                "where": "abstract, FINDINGS"},
            "total_randomised": {
                "value": 240, "quote": "240 patients were enrolled and 120 were assigned to "
                                       "each group",
                "where": "abstract, FINDINGS"},
        },
        "extraction_state": "COMPLETE_FROM_THE_ABSTRACT",
    },
    {
        "nct": "NCT01266694", "acronym": "POPE-2",
        "pmid": "26076938", "doi": "10.1136/heartjnl-2015-307827",
        "citation": ("Meurin P, Lelay-Kubas S, Pierre B, et al. Colchicine for postoperative "
                     "pericardial effusion: a multicentre, double-blind, randomised controlled "
                     "trial. Heart 2015;101(21):1711-6."),
        "source_read": "PubMed abstract, retrieved 2026-08-19",
        "population_as_the_paper_states_it": {
            "value": ("197 patients at high risk of tamponade with persistent pericardial "
                      "effusion 7-30 days AFTER CARDIAC SURGERY"),
            "quote": ("included 197 patients at high risk of tamponade ... at 7-30 days after "
                      "cardiac surgery"),
            "where": "abstract, METHODS",
        },
        "primary_outcome_as_the_paper_states_it": {
            "value": "change in pericardial effusion GRADE after 14-day treatment",
            "quote": ("The main end point was change in pericardial effusion grade after "
                      "14-day treatment."),
            "where": "abstract, METHODS",
            "note": ("A CONTINUOUS echocardiographic grade, not a recurrence count. It shares "
                     "no measurable endpoint with the other three whatever the population."),
        },
        "cells": {
            "mean_difference_in_grade_decrease": {
                "value": -0.19, "ci_low": -0.55, "ci_high": 0.16,
                "quote": ("The mean difference in grade decrease between groups was -0.19 "
                          "(95% CI -0.55 to 0.16, p=0.23)"),
                "where": "abstract, RESULTS"},
            "colchicine_n": {"value": 98, "quote": "colchicine, 1 mg daily (n=98)",
                             "where": "abstract, METHODS"},
            "placebo_n": {"value": 99, "quote": "a matching placebo (n=99)",
                          "where": "abstract, METHODS"},
        },
        "extraction_state": "COMPLETE_FROM_THE_ABSTRACT",
        "poolable_with_the_others": False,
        "why_not": ("A continuous effusion GRADE is not a recurrence count. Different "
                    "population, different construct, different measure."),
    },
]


def run(apply_it):
    doc = {
        "extracted_utc": "2026-08-19",
        "topic": "colchicine-pericarditis",
        "provenance": ("PUBLISHED REPORTS, not registry-posted results. Bibliographic detail "
                       "and abstracts ACCORDING TO PUBMED, retrieved 2026-08-19. This is the "
                       "first literature-limb extraction in this corpus and is treated as a "
                       "method proof."),
        "rules_followed": [
            "Every cell records the QUOTE it came from and WHERE in the source.",
            "NOTHING is computed from another cell. A percentage is not turned into a count "
            "and a total is not split into arms.",
            "A cell the source does not state is recorded NOT_STATED_IN_THE_SOURCE_READ with "
            "the reason, never derived.",
        ],
        "the_claim_this_refuted": {
            "what_I_said": ("Three trials register the identical primary verbatim, 'Recurrence "
                            "rate at 18 months', all against placebo -- a k=3 pool blocked by "
                            "nothing except the registry's silence."),
            "what_is_true": ("The registered TITLES match and the TRIALS do not. NCT00128453 is "
                             "ICAP, a FIRST-ATTACK acute pericarditis trial whose published "
                             "primary is 'incessant OR recurrent pericarditis'. NCT00128414 is "
                             "CORP, a FIRST-RECURRENCE trial. NCT00235079 is CORP-2, a "
                             "MULTIPLE-RECURRENCE trial. Three disease stages, and the "
                             "registry's outcome-title field carries none of that."),
            "the_shape": ("Exact title matching was already labelled a LOWER BOUND -- it misses "
                          "trials measuring one thing under different names. This is the other "
                          "direction: a FALSE POSITIVE, three trials measuring different things "
                          "under one name. REGISTERED TITLES ARE NOT ESTIMANDS, because the "
                          "estimand includes the population and the title does not."),
            "found_by": "reading the published reports, which is what the literature limb is for",
        },
        "trials": TRIALS,
        "what_is_NOT_done_here": (
            "NO POOL IS COMPUTED. Whether ICAP, CORP and CORP-2 may be combined across disease "
            "stage is a judgement that must be DECLARED on a named axis, not assumed from a "
            "title match -- and ICAP's endpoint additionally counts INCESSANT disease, which "
            "the other two do not. That is an estimand decision and it is owed separately."),
    }

    for t in TRIALS:
        n_stated = sum(1 for c in t["cells"].values() if c.get("value") is not None)
        n_missing = sum(1 for c in t["cells"].values() if c.get("state") == NOT_STATED)
        print("  %-13s %-8s PMID %-9s %-26s cells stated=%d NOT_STATED=%d"
              % (t["nct"], t["acronym"], t["pmid"], t["extraction_state"], n_stated, n_missing))
        for k, c in t["cells"].items():
            if c.get("state") == NOT_STATED:
                print("        %-28s NOT STATED -- %s" % (k, c["why"][:70]))

    if not apply_it:
        print("\nDRY RUN -- nothing written. Re-run with --apply.")
        return 0
    with io.open(OUT, "w", encoding="utf-8", newline="") as fh:
        fh.write(json.dumps(doc, indent=1, ensure_ascii=False))
    print("\nwrote %s" % os.path.relpath(OUT, REPO))
    return 0


def selftest():
    fails = []

    def ck(n, got, want):
        ok = got == want
        print("  %-66s %s  %r" % (n, "ok" if ok else "FAIL", got))
        if not ok:
            fails.append(n)

    print("1. EVERY STATED CELL CARRIES A QUOTE AND A LOCATION:")
    bad = []
    for t in TRIALS:
        for k, c in t["cells"].items():
            if c.get("value") is None:
                continue
            if not c.get("quote") or not c.get("where"):
                bad.append("%s.%s" % (t["acronym"], k))
    ck("no stated cell lacks provenance", bad, [])

    print("\n2. EVERY UNSTATED CELL SAYS SO AND SAYS WHY -- never a derived number:")
    bad = [("%s.%s" % (t["acronym"], k)) for t in TRIALS for k, c in t["cells"].items()
           if c.get("state") == NOT_STATED and (c.get("value") is not None or not c.get("why"))]
    ck("no unstated cell carries a value", bad, [])

    print("\n3. THE VALUE APPEARS IN ITS OWN QUOTE -- a cell cannot claim a number the quote")
    print("   does not contain:")
    bad = []
    for t in TRIALS:
        for k, c in t["cells"].items():
            v = c.get("value")
            if v is None or not c.get("quote"):
                continue
            s = ("%g" % v) if isinstance(v, float) else str(v)
            if s not in c["quote"] and s.rstrip("0").rstrip(".") not in c["quote"]:
                bad.append("%s.%s=%s not in %r" % (t["acronym"], k, s, c["quote"][:50]))
    ck("every value is present in its quote", bad, [])

    print("\n4. CORP IS INCOMPLETE ON PURPOSE, and 60/60 is not invented:")
    corp = [t for t in TRIALS if t["acronym"] == "CORP"][0]
    ck("state", corp["extraction_state"], "INCOMPLETE_BY_DESIGN")
    ck("colchicine_n is not stated", corp["cells"]["colchicine_n"]["value"], None)
    ck("...and the reason names the temptation",
       "60/60" in corp["cells"]["colchicine_n"]["why"], True)

    print("\n5. ICAP'S ENDPOINT IS RECORDED AS DIFFERENT FROM THE OTHER TWO:")
    icap = [t for t in TRIALS if t["acronym"] == "ICAP"][0]
    ck("its primary names incessant disease",
       "incessant" in icap["primary_outcome_as_the_paper_states_it"]["value"], True)
    ck("and the note says the registry title disagrees",
       "Recurrence rate at 18 months" in
       icap["primary_outcome_as_the_paper_states_it"]["note"], True)

    print("\n%s" % ("SELFTEST FAILED: %s" % fails if fails else "SELFTEST PASSED"))
    return 1 if fails else 0


if __name__ == "__main__":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    if "--selftest" in sys.argv:
        sys.exit(selftest())
    sys.exit(run("--apply" in sys.argv))
