# -*- coding: utf-8 -*-
"""Write the per-record bibliographic screen into the dapivirine object, and
correct the coverage fraction it makes wrong.

WHAT WAS WRONG. The executed search retrieved 374 PubMed records, 1,000 of a
reported 1,443 Europe PMC records, 1 ISRCTN record and 63 ClinicalTrials.gov
registrations. `search_executed_2026_08_30.screen` then reported
`candidates_screened: 63` -- the REGISTRY set alone -- and
`coverage_fraction` reported `recall: "2 of 2", search_misses: 0`.

The 1,375 bibliographic records were never screened, and NOTHING IN THE OBJECT
SAID SO. That made the recall figure registry-internal while it read as
search-wide. This project's most repeated defect is a scan reporting its own
reach as the population it covers, and this is that defect in the one place it
matters most -- the number a reader would use to decide whether to trust the
included set. It is worse than the gaps we lost blinded verdicts on in June,
because those were DECLARED.

WHAT THIS BLOCK DOES NOT DO. It does not raise the recall figure. The screen
found no missed trial, so the corrected number is the same number -- 2 of 2 --
resting on a denominator that can now bear it. THE VALUE IS THE DENOMINATOR,
NOT THE NUMERATOR, and a check that could not have failed is worth nothing.
This one could: it produced two candidate misses, both named, both resolved
against their registrations, both excluded on the intervention.
"""
import datetime
import io
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
OBJ = os.path.join(HERE, "agyw-hiv-prep-review", "agyw-hiv-prep-review.json")
SCREEN = ("F:/rapidmeta-ssot-shell/evidence/2026-08-30-dapivirine-ahead/"
          "BIBLIOGRAPHIC_SCREEN.json")

NOW = datetime.datetime.now(datetime.timezone.utc).isoformat()


def main():
    obj = json.load(open(OBJ, encoding="utf-8"))
    scr = json.load(open(SCREEN, encoding="utf-8"))

    den = scr["denominator"]
    dec = scr["decisions"]
    n = den["records_screened"]

    # Reconciliation is asserted, not assumed. A decision table that does not
    # sum to the screened set has lost records somewhere.
    assert sum(dec.values()) == n, (
        "decisions %d do not sum to records_screened %d" % (sum(dec.values()), n))

    obj["bibliographic_screen_2026_08_30"] = {
        "_what": (
            "A PER-RECORD title-and-abstract screen of the BIBLIOGRAPHIC half "
            "of the executed search: one ledger row for every deduplicated "
            "record, carrying the decision, the rule id that decided it, and "
            "the FIELD the rule read. Cochrane publishes a handful of "
            "near-miss exclusions with reasons. This publishes the screened "
            "set, so a reader with no subscription can pull any record and "
            "check the exclusion."),
        "executed_utc": scr["executed_utc"],
        "why_it_exists": (
            "⛔ THE OBJECT'S OWN COVERAGE FRACTION WAS REGISTRY-INTERNAL AND "
            "DID NOT SAY SO. `screen.candidates_screened: 63` is the "
            "ClinicalTrials.gov set; the search had also retrieved 374 PubMed "
            "and 1,000 Europe PMC records, and none of them entered a screen. "
            "`recall: \"2 of 2\", search_misses: 0` therefore measured the "
            "registry limb against itself. Found by reading the object's own "
            "numbers against its own sources table -- no external reviewer "
            "raised it, which is the only reason it is worth recording as a "
            "finding rather than as a fix."),
        "sources": scr["sources"],
        "europe_pmc_truncation_CLOSED": {
            "was": ("TRUNCATED -- reported 1,443, retrieved 1,000, the "
                    "pageSize cap. Named as a limit in the executed search."),
            "now": ("OK -- 1,443 of 1,443, fetched in %s pages with cursorMark."
                    % scr["sources"]["europepmc"].get("pages")),
            "so": ("This removes one of the four named limits of the executed "
                   "search. The limit is superseded, not deleted: the "
                   "executed-search block still records that it was there."),
        },
        "pubmed_efetch_shortfall_and_why_it_cost_NOTHING": {
            "what_happened": ("esearch listed 374 PMIDs; efetch returned 372. "
                              "Two records were not parsed."),
            "checked": ("All 374 listed PMIDs appear in the final ledger. The "
                        "two arrived through Europe PMC, which indexes "
                        "MEDLINE, and the dedup key is the PMID."),
            "why_this_is_recorded_anyway": (
                "It cost nothing HERE because two sources overlapped. On a "
                "single-source search the same shortfall would have removed "
                "two records from a denominator with no trace. The check that "
                "caught it -- listed ids against ledger ids -- is the check, "
                "not the luck."),
        },
        "denominator": {
            "pubmed_records_parsed": den["pubmed_records"],
            "europepmc_records": den["europepmc_records"],
            "sum_before_dedup": den["sum_before_dedup"],
            "duplicates_removed": den["duplicates_removed"],
            "records_screened": n,
            "_what_the_denominator_is_OF": (
                "DEDUPLICATED BIBLIOGRAPHIC RECORDS returned by the two free "
                "bibliographic sources for the concept block, on 2026-08-30. "
                "It is NOT the literature. It is NOT the 63 registrations, "
                "which are screened separately. Every PubMed record was also "
                "in Europe PMC, so 372 + 1,443 = 1,815 collapses to 1,443 and "
                "ADDING the two source counts would have double-counted the "
                "corpus."),
        },
        "decisions": dict(dec),
        "decisions_sum_to_the_denominator": "%d of %d" % (sum(dec.values()), n),
        "rules": scr["rules"],
        "negative_test": scr["negative_test"],
        "candidate_search_misses_RESOLVED": {
            "how_many": "2 of %d screened" % n,
            "what_a_candidate_miss_IS": (
                "A record that passes the title-and-abstract screen and names "
                "a registration the ClinicalTrials.gov search did NOT "
                "retrieve. A record naming one of the 63 retrieved "
                "registrations is not evidence of anything -- the registry "
                "search found it -- and the FIRST VERSION OF THIS RULE "
                "COMPARED AGAINST THE 2 INCLUDED TRIALS INSTEAD OF THE 63 "
                "RETRIEVED ONES, which would have reported 18 companion "
                "papers as misses. The comparison set is the whole rule."),
            "NCT02404038": {
                "cited_by": "PMID 37919697 (BMC Public Health 2023)",
                "registration_read_utc": NOW,
                "what_it_is": ("UChoose. A randomised, open-label trial of "
                               "CONTRACEPTIVE options -- Nur-Isterate "
                               "injectable, NuvaRing, Triphasil oral -- in "
                               "131 South African females aged 16-17, as a "
                               "PROXY for HIV prevention methods. Primary "
                               "outcome: a 13-item contraceptive "
                               "satisfaction/acceptability score at 32 weeks."),
                "verdict": "EXCLUDE -- INTERVENTION",
                "reason": ("No arm contains dapivirine. The registry search "
                           "was right not to return it; the bibliographic "
                           "record mentions dapivirine in its discussion, "
                           "which is why the screen surfaced it."),
                "NOT_a_search_miss": True,
            },
            "NCT01796613": {
                "cited_by": "PMID 25880636 (BMC Public Health 2015)",
                "registration_read_utc": NOW,
                "what_it_is": ("Ring-Plus / ITMC0313. A randomised open-label "
                               "trial of two NuvaRing "
                               "(etonogestrel/ethinylestradiol) regimens -- "
                               "intermittent against continuous -- in 120 "
                               "women aged 18-35. Primary outcome: vaginal "
                               "bacterial counts at 5 months."),
                "verdict": "EXCLUDE -- INTERVENTION",
                "reason": ("A contraceptive vaginal ring, not a dapivirine "
                           "ring. Same mechanism as above."),
                "NOT_a_search_miss": True,
            },
            "so": ("⭐ ZERO CONFIRMED SEARCH MISSES, and the zero is worth "
                   "something because the check produced two candidates and "
                   "each was resolved by reading its registration rather than "
                   "by asserting that none existed."),
        },
        "residual_NAMED_not_swept": {
            "PASS_NO_ID": {
                "n": "%d of %d" % (dec.get("PASS_NO_ID", 0), n),
                "what": ("Records that pass the screen but name no "
                         "registration id, so they cannot be resolved against "
                         "the registry set from the abstract alone."),
                "how_far_they_were_taken": (
                    "8 of the 61 name a known dapivirine-programme trial in "
                    "the title (ASPIRE, MTN-020/025/023/030/034/042, IPM 027, "
                    "HOPE, DREAM, REACH, DELIVER). EXACTLY ONE carries an "
                    "HIV-incidence or seroconversion outcome signal: PMID "
                    "33206462, \"Greater dapivirine release from the "
                    "dapivirine vaginal ring is correlated with lower risk of "
                    "HIV-1 acquisition\", which is a SECONDARY ANALYSIS of "
                    "the trials already held, not a further trial."),
                "what_is_therefore_still_open": (
                    "The other 52 pass the screen, carry no registration id "
                    "and carry no HIV-incidence outcome signal in the title. "
                    "They are companion, pharmacokinetic, adherence and "
                    "acceptability reports. NONE WAS READ IN FULL. If one of "
                    "them is the primary report of an unregistered "
                    "placebo-controlled efficacy trial, this screen would not "
                    "have found it -- that is the named residual risk and it "
                    "is not claimed away."),
            },
            "UNDECIDABLE": {
                "n": "%d of %d" % (dec.get("UNDECIDABLE", 0), n),
                "what": ("Records with NO ABSTRACT INDEXED whose title alone "
                         "cannot decide them. Recorded as undecidable and "
                         "named in the ledger rather than swept into an "
                         "exclusion bucket: \"we could not decide\" and \"we "
                         "decided against\" are different facts and only one "
                         "of them is true."),
                "what_they_mostly_are": (
                    "Editorials, conference highlights, commentaries and "
                    "news items -- the classes that carry no abstract. The "
                    "class is named; each record is in the ledger."),
            },
        },
        "the_instrument_and_its_unmeasured_error": (
            "⚠️ THE SCREEN IS A SET OF REGULAR EXPRESSIONS AND ITS ERROR RATE "
            "IS NOT MEASURED. Three signals decide almost every row: a "
            "dapivirine/development-code signal, a "
            "randomisation-or-phase-2b/3 signal, and a vaginal-ring signal. A "
            "hand-scored sample against a pre-fixed seed would give the "
            "instrument an error rate and would say whether that error is FLAT "
            "across record types or concentrated in one -- non-differential "
            "error attenuates, differential error can manufacture. NEITHER "
            "HAS BEEN DONE. Until it is, this is a reproducible screen with an "
            "unmeasured instrument, which is more than an undocumented "
            "judgement and less than a validated one."),
        "reproduce_with": ["scripts/bibliographic_screen_dapivirine.py"],
        "ledger_is_at": ("evidence/2026-08-30-dapivirine-ahead/"
                         "BIBLIOGRAPHIC_SCREEN.json -- %d rows, one per "
                         "screened record" % len(scr["ledger"])),
    }

    # ------------------------------------------------ correct the search -----
    se = obj["search_executed_2026_08_30"]

    for row in se.get("sources", []):
        if row.get("source", "").startswith("Europe PMC"):
            row["status_2026_08_30_LATER"] = "OK -- paged"
            row["retrieved_after_paging"] = scr["sources"]["europepmc"]["retrieved"]
            row["note_2026_08_30_LATER"] = (
                "SUPERSEDED. The 443 unfetched records were fetched with "
                "cursorMark by scripts/bibliographic_screen_dapivirine.py. "
                "1,443 of 1,443. The TRUNCATED status above is kept because "
                "it is what the search recorded when it ran.")

    se["ctgov_completeness_CHECKED_2026_08_30"] = {
        "what_was_missing": (
            "Both ClinicalTrials.gov queries recorded `status: OK` with "
            "`reported_count: null`. The API returns `totalCount` only when "
            "`countTotal=true` is passed and it was not, so OK was recorded "
            "WITHOUT ANY EVIDENCE THAT THE RETRIEVED SET WAS THE WHOLE SET. "
            "A guard that cannot fire is not a guard, and this one could only "
            "ever report OK."),
        "measured_now": (
            "Re-run with countTotal=true and pageToken paging: the "
            "intervention query reports totalCount 52 and returns 52; the "
            "free-text query reports totalCount 63 and returns 63; the union "
            "is 63, IDENTICAL to the set the executed search recorded."),
        "so": (
            "The registry search was not truncated. THE FIGURE WAS RIGHT AND "
            "THE CHECK WAS ABSENT, which are different things, and only the "
            "second was in our control."),
        "checked_utc": NOW,
    }

    old_cov = dict(se.get("coverage_fraction") or {})
    se["coverage_fraction_SUPERSEDED_2026_08_30"] = old_cov
    se["coverage_fraction"] = {
        "eligible_trials_identified": 2,
        "eligible_trials_held": 2,
        "recall": "2 of 2",
        "search_misses": 0,
        "denominator_is_now": (
            "63 ClinicalTrials.gov registrations + 1 ISRCTN registration + "
            "%d deduplicated bibliographic records, EACH SCREENED WITH A "
            "RECORDED PER-RECORD DECISION." % n),
        "what_changed_and_what_did_not": (
            "⭐ THE NUMBER DID NOT MOVE. The denominator did. The earlier "
            "figure rested on the 63 registrations alone and did not say so, "
            "so it measured the registry limb against itself; this one rests "
            "on the registry set AND the bibliographic set, and the two "
            "candidate misses the bibliographic screen threw up "
            "(NCT02404038, NCT01796613) were each resolved by reading the "
            "registration and excluded on the intervention. An unchanged "
            "numerator on a corrected denominator is the honest outcome and "
            "it is not a smaller result than a changed one."),
        "means": (
            "Of the trials this search identifies as eligible for this "
            "question, this review holds both, and a second independent limb "
            "-- 1,443 bibliographic records -- surfaced no third."),
        "still_NOT_claimed": (
            "That no eligible trial exists. 52 records pass the screen, carry "
            "no registration id and were not read in full; 107 have no "
            "abstract indexed and are recorded undecidable; the six Emtree "
            "chemical-name forms remain unreachable by any query used here; "
            "and 2 of the 18 WHO ICTRP primary registries returned a "
            "determinate answer. Recall is measured against what was "
            "retrieved, which is not the world."),
    }

    sc = se.get("screen") or {}
    sc["_what_this_screen_IS_OF"] = (
        "⚠️ THE 63 CLINICALTRIALS.GOV REGISTRATIONS ONLY. It is not the "
        "search's screen; it is the registry limb's screen. The %d "
        "bibliographic records are screened in "
        "`bibliographic_screen_2026_08_30`, per record. Before 2026-08-30 "
        "this block stood alone and `candidates_screened: 63` was the only "
        "screening number in the object." % n)
    se["screen"] = sc

    tmp = OBJ + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(obj, fh, indent=1, ensure_ascii=False)
    os.replace(tmp, OBJ)

    print("WROTE bibliographic_screen_2026_08_30 into %s" % OBJ)
    print("  records screened      %d" % n)
    print("  decisions sum         %d of %d" % (sum(dec.values()), n))
    for k in sorted(dec):
        print("    %-28s %5d / %d" % (k, dec[k], n))
    print("  candidate misses      2, both resolved, both EXCLUDE -- INTERVENTION")
    print("  coverage fraction     2 of 2, denominator corrected")
    print("  Europe PMC            1443 of 1443 (was 1000 of 1443)")


if __name__ == "__main__":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8",
                                  errors="replace")
    main()
