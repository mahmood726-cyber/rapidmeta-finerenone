#!/usr/bin/env python3
"""THE PERI-PROCEDURAL LITERATURE LIMB -- and it settles the question the title match could not.

THE QUESTION. Five trials in this reading have posted results and they register four different
primary outcomes. THREE of them are plainly about post-procedural ATRIAL FIBRILLATION under
three different titles, and exact normalised title matching -- correctly labelled a LOWER BOUND
-- could not decide whether they measure one thing. Only reading the definitions can.

ANSWER ONE: THEY DO NOT MEASURE ONE THING, and the differences are not cosmetic.

    NCT01985425  COP-AF Pilot   "Clinically Significant Atrial Fibrillation" -- new AF that
                                RESULTS IN angina, congestive heart failure, symptomatic
                                hypotension, or REQUIRES treatment. A CONSEQUENCE requirement.
                                Comparator: Placebo Colchicine.

    NCT03021343  END-AF         "documented AF lasting MORE THAN 5 MINUTES". A DURATION
                                threshold with no consequence requirement, and the trial is
                                OPEN-LABEL against NO COLCHICINE -- not placebo.

    NCT02177266  (no acronym)   "Post Cardiac Surgery Atrial Fibrillation OR
                                POST-PERICARDIOTOMY SYNDROME" -- a COMPOSITE, not AF alone.
                                Comparator: Placebo. Enrolment 2.

    So: a consequence-defined endpoint, a duration-defined endpoint, and a composite -- across
    two comparator families. THE TITLE MATCHER WAS RIGHT TO KEEP THEM APART. What it could not
    do is say WHY, and "we could not tell" is a different statement from "they differ", which
    is why the reading carried it as a lower bound until now.

ANSWER TWO, AND IT WAS NOT THE QUESTION ASKED: TWO OF THE FIVE REPORTERS ARE ONE TRIAL.

    PMID 32295417 (COLCHICINE-PCI, Circ Cardiovasc Interv 2020) closes its abstract:
        "Unique Identifiers: NCT02594111, NCT01709981."

    NCT01709981 (n=280, primary: percent change in IL-6) is the NESTED INFLAMMATORY BIOMARKER
    SUBSTUDY of NCT02594111 (n=714, primary: peri-procedural myocardial necrosis). One trial,
    one paper, TWO REGISTRATIONS -- and this reading counts them as two eligible trials.

    THE SCREEN'S DUPLICATE DETECTOR DID NOT CATCH IT, and could not have: it pairs registrations
    on identical official title and enrolment, and these differ on both (280 against 714). The
    relationship is PARENT AND SUBSTUDY, which looks nothing like a duplicate registration in
    the registry and is visible only in the publication that names both.

        k IS AN OVERCOUNT WHEREVER A TRIAL REGISTERS ITS SUBSTUDY SEPARATELY, and no
        registry-only method can see it.

ALL BIBLIOGRAPHIC DETAIL AND ABSTRACTS ACCORDING TO PUBMED, retrieved 2026-08-19. Cells are
recorded with the quote they came from; nothing is computed from another cell.
"""
import io
import json
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import build_colchicine_readings_2026_08_19 as B                        # noqa: E402

TOPIC = "colchicine-periprocedural"
PATH = os.path.join(REPO, "ssot", TOPIC, TOPIC + ".json")
OUT = os.path.join(REPO, "evidence", "2026-08-19-batch1",
                   "periprocedural_literature_extraction.json")

AF_TRIALS = {
    "NCT01985425": {
        "acronym": "COP-AF Pilot", "publication": None,
        "publication_state": ("NO_PUBLICATION_RESOLVED -- the registration carries no reference "
                              "and PubMed by registration identifier returned nothing. NOT "
                              "evidence that none exists."),
        "endpoint_definition_VERBATIM": (
            "New atrial fibrillation that results in angina, congestive heart failure, "
            "symptomatic hypotension, or that requires treatment with a rate controlling drug, "
            "antiarrhythmic drug, or electrical cardioversion"),
        "endpoint_kind": "CONSEQUENCE-DEFINED",
        "where": "ClinicalTrials.gov primaryOutcomes[0].description, read 2026-08-19",
        "comparator": "Placebo Colchicine",
    },
    "NCT03021343": {
        "acronym": "END-AF", "publication": {
            "pmid": "27502857", "doi": "10.1016/j.ahj.2016.05.006",
            "citation": ("Tabbalat RA, Hamad NM, Alhaddad IA, et al. Effect of ColchiciNe on "
                         "the InciDence of Atrial Fibrillation in Open Heart Surgery Patients: "
                         "END-AF Trial. Am Heart J 2016;178:102-7."),
            "route": "registration referencesModule, type RESULT; confirmed against PubMed"},
        "endpoint_definition_VERBATIM": "documented AF lasting more than 5 minutes",
        "endpoint_kind": "DURATION-DEFINED, no consequence requirement",
        "where": "PMID 27502857 abstract, METHODS",
        "comparator": "no-colchicine, OPEN-LABEL -- not placebo",
        "cells": {
            "colchicine_events": {"value": 26, "quote": "26 (14.5%) in the colchicine group",
                                  "where": "abstract, RESULTS"},
            "colchicine_n": {"value": 179, "quote": "randomized to colchicine (n = 179)",
                             "where": "abstract, METHODS"},
            "comparator_events": {"value": 37, "quote": "37 (20.5%) in the no-colchicine group",
                                  "where": "abstract, RESULTS"},
            "comparator_n": {"value": 181, "quote": "or no-colchicine (n = 181)",
                             "where": "abstract, METHODS"},
            "total_randomised": {"value": 360, "quote": "elective cardiac surgery (n = 360)",
                                 "where": "abstract, METHODS"},
        },
    },
    "NCT02177266": {
        "acronym": None, "publication": None,
        "publication_state": ("NO_PUBLICATION_RESOLVED -- no reference on the registration and "
                              "PubMed by registration identifier returned nothing."),
        "endpoint_definition_VERBATIM": ("Number of Patients With Post Cardiac Surgery Atrial "
                                         "Fibrillation or Post-pericardiotomy Syndrome."),
        "endpoint_kind": "COMPOSITE -- AF **or** post-pericardiotomy syndrome",
        "where": "ClinicalTrials.gov primaryOutcomes[0].measure, read 2026-08-19",
        "comparator": "Placebo",
        "note": "Enrolment 2.",
    },
}

ONE_TRIAL = {
    "registrations": ["NCT02594111", "NCT01709981"],
    "one_publication": {
        "pmid": "32295417", "doi": "10.1161/CIRCINTERVENTIONS.119.008717",
        "citation": ("Shah B, Pillinger M, Zhong H, et al. Effects of Acute Colchicine "
                     "Administration Prior to Percutaneous Coronary Intervention: "
                     "COLCHICINE-PCI Randomized Trial. Circ Cardiovasc Interv "
                     "2020;13(4):e008717."),
        "the_sentence_that_settles_it": "Unique Identifiers: NCT02594111, NCT01709981.",
        "where": "abstract, closing registration statement",
    },
    "relationship": ("NCT01709981 (n=280, primary: percent change in IL-6) is the NESTED "
                     "INFLAMMATORY BIOMARKER SUBSTUDY of NCT02594111 (n=714, primary: "
                     "peri-procedural myocardial necrosis). One trial, one paper, two "
                     "registrations."),
    "why_the_duplicate_detector_missed_it": (
        "It pairs registrations on identical official title AND identical enrolment. These "
        "differ on both -- 280 against 714. PARENT AND SUBSTUDY looks nothing like a duplicate "
        "registration in the registry and is visible only in the publication naming both."),
    "consequence": ("This reading's k counts them as two eligible trials. k IS AN OVERCOUNT "
                    "WHEREVER A TRIAL REGISTERS ITS SUBSTUDY SEPARATELY, and no registry-only "
                    "method can see it."),
    "primary_result_as_published": {
        "quote": ("the primary outcome of PCI-related myocardial injury did not differ between "
                  "colchicine (n=206) and placebo (n=194) groups (57.3% versus 64.2%)"),
        "where": "PMID 32295417 abstract, RESULTS",
        "note": "Among the 400 subjects who underwent PCI, of 714 randomised.",
    },
}


def run(apply_it):
    doc = {
        "extracted_utc": "2026-08-19",
        "topic": TOPIC,
        "according_to": "PubMed, retrieved 2026-08-19",
        "what_this_enumerated_over": {
            "targets": ("the 5 trials in this reading with ELIGIBLE_WITH_RESULTS, from "
                        "evidence/2026-08-19-batch1/colchicine_split_screening.json"),
            "routes_run": ["ClinicalTrials.gov referencesModule, every type unfiltered",
                           "PubMed by registration identifier",
                           "PubMed article metadata for each resolved PMID"],
            "routes_NOT_run": ["publisher or journal search by trial name",
                               "grey literature and conference abstracts"],
        },
        "finding_1_the_three_AF_trials_do_not_measure_one_thing": AF_TRIALS,
        "finding_2_two_of_the_five_reporters_are_one_trial": ONE_TRIAL,
        "what_is_NOT_done": ("No pool is computed. The three AF endpoints are a consequence "
                             "definition, a duration definition and a composite, across two "
                             "comparator families; nothing here makes them one estimand."),
    }
    print("FINDING 1 -- the three AF trials, by endpoint kind:")
    for n, t in AF_TRIALS.items():
        print("   %-13s %-14s %-42s comparator=%s"
              % (n, t["acronym"] or "-", t["endpoint_kind"], t["comparator"]))
    print("\nFINDING 2 -- one trial, two registrations:")
    print("   %s  ->  PMID %s" % (" + ".join(ONE_TRIAL["registrations"]),
                                  ONE_TRIAL["one_publication"]["pmid"]))
    print("   %s" % ONE_TRIAL["one_publication"]["the_sentence_that_settles_it"])

    if not apply_it:
        print("\nDRY RUN -- nothing written.")
        return 0
    with io.open(OUT, "w", encoding="utf-8", newline="") as fh:
        fh.write(json.dumps(doc, indent=1, ensure_ascii=False))

    o = json.load(io.open(PATH, encoding="utf-8"))
    pr = o["results"]["by_outcome"]["primary"]
    pr["failing_limbs"].append({
        "property": "P37",
        "finding": ("SETTLED BY THE PUBLICATIONS, not by the title match. The three "
                    "post-procedural AF endpoints are a CONSEQUENCE definition (COP-AF Pilot), "
                    "a DURATION definition of >5 minutes (END-AF), and a COMPOSITE with "
                    "post-pericardiotomy syndrome (NCT02177266) -- across two comparator "
                    "families, END-AF being OPEN-LABEL against no colchicine.")})
    pr["failing_limbs"].append({
        "property": "P43",
        "finding": ("TWO OF THE FIVE REPORTERS ARE ONE TRIAL. PMID 32295417 names both "
                    "NCT02594111 and NCT01709981; the latter is the nested biomarker substudy "
                    "of the former. k COUNTS THEM TWICE, and no registry-only method can see "
                    "it -- the duplicate detector pairs on identical title and enrolment, and "
                    "these differ on both.")})
    pr["k_is_an_overcount_by"] = 1
    pr["k_overcount_reason"] = ONE_TRIAL["consequence"]
    pr["literature_limb"] = {
        "run_utc": "2026-08-19",
        "record": "evidence/2026-08-19-batch1/periprocedural_literature_extraction.json",
        "publications_resolved": 2,
        "publications_not_resolved": 2,
        "note": ("COP-AF Pilot and NCT02177266 resolved to NO PUBLICATION by two routes. That "
                 "is not evidence none exists."),
    }
    o["sources"]["literature_extraction"] = (
        "evidence/2026-08-19-batch1/periprocedural_literature_extraction.json")
    with io.open(PATH, "w", encoding="utf-8", newline="") as fh:
        fh.write(json.dumps(o, indent=1, ensure_ascii=False))

    scr = json.load(io.open(os.path.join(REPO, "evidence", "2026-08-19-batch1",
                                         "colchicine_split_screening.json"), encoding="utf-8"))
    disp = {r["nct"]: r["disposition"] for r in scr["rows"]}
    spec = B.READINGS["PERIPROC"]
    sibs = [(B.READINGS[r]["page"], B.READINGS[r]["title"])
            for r in B.READINGS if r != "PERIPROC"]
    html = B.page_html(spec, o, disp, sibs)
    with io.open(os.path.join(REPO, spec["page"]), "w", encoding="utf-8", newline="") as fh:
        fh.write(html)
    print("\nwrote the record, patched the object, rebuilt %s" % spec["page"])
    return 0


if __name__ == "__main__":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.exit(run("--apply" in sys.argv))
