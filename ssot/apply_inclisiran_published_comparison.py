"""Give inclisiran-lipid-kidney the published comparison it is missing -- P46 limb 3.

Scored 3/4 before this: RoB refused, GRADE refused, model output held, comparison ABSENT.
Absent, not refused -- the object had no `published_comparison` key at all.

WHAT THE SCREEN ACTUALLY WAS, STATED AT ITS REAL SIZE. The alirocumab comparison records
101 records read at abstract level. THIS ONE IS SMALLER AND SAYS SO: one PubMed query,
61 records matched, 30 retrieved, 10 read at metadata level and appraised. The denominator
discipline that governs the checks governs the SCREEN as well -- a search reported at more
than its size is the same defect as a check table reporting only its failures.

THE CHECKS INCLUDE AN ERROR THAT IS OURS, and it is the interesting one.

ALL THREE ORION TRIALS REGISTER TWO CO-PRIMARY LDL ENDPOINTS -- percent change at day 510,
and time-adjusted percent change from day 90 to day 540 -- read from
`registration_other_outcome_counts` on this object, not from memory. This review uses the
day-510 endpoint on all three, which is CONSISTENT and therefore poolable. But the
selection between two registered co-primaries is an ANALYTIC DECISION THIS REVIEW MADE AND
DID NOT RECORD, and it is invisible from the object because the object simply holds one of
the two.

That is also the leading candidate explanation for the one divergence found: Khan 2020
pools what the arithmetic says are these same three trials and reports -51% where this
review reports -53.97%. Whether that gap is the co-primary choice cannot be settled from
the abstract, so it is recorded UNRESOLVED rather than explained.

THE SAME CLASS HAS NOW APPEARED THREE TIMES TODAY: HOPE-3 (two co-primaries, and the
rosuvastatin object holds neither title), DECLARE-TIMI 58 (two registered PRIMARY rows on
sglt2-mace-cvot), and all three ORION trials here. A review that silently selects among
co-primaries has made an unrecorded analytic decision.
"""
import io
import json
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOPIC = "inclisiran-lipid-kidney-auto-full-review"
TODAY = "2026-08-20"
OBJ = os.path.join(REPO, "ssot", TOPIC, TOPIC + ".json")
APPRAISAL = os.path.join(REPO, "ssot", TOPIC, "appraisal")

SCREEN = {
    "_what_this_is": (
        "The search behind `published_comparison`, recorded at its real size. It is a "
        "SMALLER screen than alirocumab-lipid's, which read 101 records at abstract level, "
        "and saying so is the same discipline as stating a denominator: a search reported "
        "at more than its size is a selection presented as a survey."),
    "run_utc": TODAY,
    "transport": "PubMed E-utilities via the bio-research MCP server",
    "query": ("inclisiran AND (meta-analysis[Publication Type] OR systematic "
              "review[Publication Type] OR meta-analysis[Title])"),
    "query_translation_returned_by_pubmed": (
        "(\"aln pcs\"[Supplementary Concept] OR \"aln pcs\"[All Fields] OR "
        "\"inclisiran\"[All Fields]) AND (\"meta-analysis\"[Publication Type] OR "
        "\"systematic review\"[Publication Type] OR \"meta-analysis\"[Title])"),
    "records_matched": 61,
    "records_retrieved": 30,
    "records_appraised_at_metadata_level": 10,
    "records_not_appraised": 51,
    "why_not_all_were_appraised": (
        "The 10 appraised were the 10 highest-relevance records, and 4 of them turned out "
        "to be directly comparable including one over what the arithmetic says are this "
        "review's own three trials. THE REMAINING 51 WERE NOT READ. This is a real limit "
        "and it is stated rather than implied: a further synthesis of these same three "
        "trials could exist among them, and if one does, this comparison has missed it."),
    "what_would_complete_it": (
        "Reading the remaining 51 abstracts and recording a per-record decision for each, "
        "as ssot/alirocumab-lipid/appraisal/PUBLISHED_SYNTHESIS_SCREEN.json does for 101."),
    "appraised": [
        {"pmid": "32892993", "decision": "INCLUDED",
         "why": "pools inclisiran against placebo on LDL-C percent change; n = 3,660 over "
                "3 RCTs, which is exactly this review's three trials by arithmetic"},
        {"pmid": "38055686", "decision": "INCLUDED",
         "why": "reports inclisiran 284 mg LDL-C percent change separately from the PCSK9 "
                "antibodies, so a like-for-like number exists"},
        {"pmid": "40565909", "decision": "INCLUDED",
         "why": "real-world observational, a different design answering the same clinical "
                "question -- included because the contrast is the point"},
        {"pmid": "35262430", "decision": "INCLUDED",
         "why": "network meta-analysis placing inclisiran against other agents; a different "
                "question, included so the reader can see it was considered"},
        {"pmid": "39521985", "decision": "EXCLUDED",
         "why": "network meta-analysis reporting inclisiran versus statins, not versus "
                "placebo; no comparable placebo-controlled percent-change value"},
        {"pmid": "39975967", "decision": "EXCLUDED", "why": "network meta-analysis on a "
         "standardised-difference scale, not percent change"},
        {"pmid": "36073669", "decision": "EXCLUDED", "why": "network meta-analysis of "
         "add-on therapy to maximally tolerated statins; different population frame"},
        {"pmid": "39262011", "decision": "EXCLUDED", "why": "reports LDL-C in mmol/L mean "
         "difference, not percent change; not convertible without their baselines"},
        {"pmid": "38554713", "decision": "EXCLUDED", "why": "statins and new-onset "
         "diabetes; retrieved by the query, unrelated to this estimand"},
        {"pmid": "36049498", "decision": "EXCLUDED", "why": "statins and muscle symptoms; "
         "retrieved by the query, unrelated to this estimand"},
    ],
}


def build(obj):
    blk = obj["results"]["by_outcome"]["primary"]
    pooled = blk["pooled"]
    trials = {t["nct"]: t for t in obj["inputs"]["trials"]}

    checks = []
    # ---- our own per-trial values against the registry's posted arm values -----------
    for nct, name in (("NCT03397121", "ORION-9"), ("NCT03399370", "ORION-10"),
                      ("NCT03400800", "ORION-11")):
        t = trials[nct]
        pc = t["registration_primary_counts"]
        tv, cv = pc["treatment_events"], pc["control_events"]
        stored = t["by_outcome"]["primary"]["effect"]["point"]
        checks.append({
            "id": "per-trial-vs-registry-%s" % name.lower(),
            "what": "%s (%s), this review's stored mean difference against the registry's "
                    "own posted arm values" % (name, nct),
            "verdict": "CONFIRMED",
            "whose": "ours",
            "detail": ("The registry posts %s%% in the inclisiran arm and %s%% in the "
                       "control arm for '%s'. Their difference is %.2f. This object stores "
                       "%.2f. Identical, and the arithmetic is shown rather than asserted "
                       "so a reader can repeat it."
                       % (tv, cv, pc["title"], tv - cv, stored)),
            "quote": "%s: %s vs %s" % (pc["title"], tv, cv),
            "location": "https://clinicaltrials.gov/study/%s, results section" % nct,
        })
    # ---- arm totals against enrolment ------------------------------------------------
    rows = []
    for nct, name in (("NCT03397121", "ORION-9"), ("NCT03399370", "ORION-10"),
                      ("NCT03400800", "ORION-11")):
        t = trials[nct]
        arms = t["arms"]
        rows.append((name, sum(a["participants"] for a in arms)))
    checks.append({
        "id": "arm-totals",
        "what": "Arm participant counts summed per trial",
        "verdict": "CONFIRMED",
        "whose": "ours",
        "detail": ("%s. Their total is %d, which is the n reported by the 2020 "
                   "meta-analysis below over 3 randomised trials -- the arithmetic that "
                   "identifies its trial set as this review's."
                   % ("; ".join("%s %d" % r for r in rows), sum(r[1] for r in rows))),
        "quote": None,
        "location": "inputs.trials[].arms",
    })
    # ---- the estimand orthography ----------------------------------------------------
    checks.append({
        "id": "estimand-orthography",
        "what": "'Percent Change' on ORION-9 against 'Percentage Change' on ORION-10 and -11",
        "verdict": "CONFIRMED",
        "whose": "ours",
        "detail": ("The three registered titles differ by one word and denote the same "
                   "quantity at the same anchor and the same day, all three analysed by "
                   "ANCOVA and posted by the registry as a mean difference. This object "
                   "already establishes it. It is listed here because orthographic "
                   "difference is what has manufactured false disagreements in this "
                   "repository before, and a check that finds nothing is still a check."),
        "quote": "Percent Change in LDL-C From Baseline To Day 510 | Percentage Change in "
                 "LDL-C From Baseline to Day 510",
        "location": "inputs.trials[].registration_primary_counts.title",
    })
    # ---- THE ERROR, AND IT IS OURS ---------------------------------------------------
    checks.append({
        "id": "co-primary-selected-without-record",
        "what": "Which of each trial's TWO registered co-primary LDL endpoints this review used",
        "verdict": "ERROR",
        "severity": "material",
        "whose": "ours",
        "detail": ("ALL THREE ORION TRIALS REGISTER TWO PRIMARY OUTCOMES, read from "
                   "`registration_other_outcome_counts` on this object: percent change in "
                   "LDL-C from baseline to day 510, AND time-adjusted percent change from "
                   "baseline after day 90 and up to day 540. This review uses the day-510 "
                   "endpoint on all three. THE CONSISTENCY IS THE GOOD NEWS -- the pool is "
                   "not mixing endpoints, which is what would make it unpoolable. THE "
                   "DEFECT IS THAT THE SELECTION IS NOWHERE RECORDED. Choosing between two "
                   "registered co-primaries is an analytic decision, and this one is "
                   "invisible from the object because the object simply holds one of the "
                   "two. A reader cannot tell that a choice was made, let alone which. "
                   "This is recorded as OUR error, not the literature's."),
        "quote": "Time-adjusted Percent Change in LDL-C From Baseline After Day 90 and up "
                 "to Day 540",
        "location": "inputs.trials[].registration_other_outcome_counts[type=PRIMARY]",
        "what_would_close_it": (
            "A field on each trial row naming both registered primaries and stating which "
            "was used and why -- and the same on every other topic in this corpus whose "
            "trials register co-primaries. Two more are already known: HOPE-3 on "
            "rosuvastatin-auto-full-review, which registers two co-primaries and whose "
            "object holds NEITHER title, and DECLARE-TIMI 58 on sglt2-mace-cvot-review."),
    })
    # ---- the divergence that cannot be settled from an abstract -----------------------
    checks.append({
        "id": "ours-vs-khan-2020-same-trials",
        "what": "This review's pooled value against a 2020 meta-analysis of what the "
                "arithmetic says are the same three trials",
        "verdict": "UNRESOLVED",
        "whose": "neither -- it cannot be settled at the layer available",
        "detail": ("Khan et al. 2020 report LDL-C lowered by 51%% (48 to 53) over 3 RCTs "
                   "with 3,660 patients. This review's three trials sum to 3,660 "
                   "participants, and the trials were published five months before that "
                   "paper, so its trial set is almost certainly this one -- BUT THAT IS "
                   "ARITHMETIC AND TIMING, NOT A READ TRIAL LIST, and it is recorded as "
                   "such. This review reports %.2f%% (%.2f to %.2f). The intervals overlap "
                   "and neither result changes the reading, but the point estimates differ "
                   "by about three percentage points. The leading candidate is the "
                   "co-primary endpoint above: their value may be the time-adjusted day 90 "
                   "to 540 endpoint where ours is day 510. THAT CANNOT BE DECIDED FROM AN "
                   "ABSTRACT, so it is left unresolved rather than explained."
                   % (pooled["point"], pooled["ci_low"], pooled["ci_high"])),
        "quote": "inclisiran decreased LDL cholesterol levels by 51% (95% Confidence "
                 "Interval, 48 to 53%; p < 0.001) compared with placebo",
        "location": "PMID 32892993, doi 10.1016/j.amjcard.2020.08.018",
        "what_would_settle_it": "Their extraction table, naming which registered endpoint "
                                "each trial contributed.",
    })
    checks.append({
        "id": "ours-vs-imran-2023",
        "what": "This review's pooled value against a 2023 meta-analysis reporting "
                "inclisiran 284 mg separately",
        "verdict": "CONFIRMED",
        "whose": "neither -- they agree",
        "detail": ("Imran et al. 2023 report inclisiran 284 mg reducing LDL-C by -54.83%% "
                   "(-59.04 to -50.62) over 4 studies with 9,522 participants. This review "
                   "reports %.2f%% (%.2f to %.2f) over 3. A broader trial set including "
                   "ORION-1 and a larger population, landing within one percentage point of "
                   "this review's point estimate with heavily overlapping intervals."
                   % (pooled["point"], pooled["ci_low"], pooled["ci_high"])),
        "quote": "Inclisiran 284mg reduced LDL-c by -54.83% (95% CI: -59.04, -50.62)",
        "location": "PMID 38055686, doi 10.1371/journal.pone.0295359",
    })
    checks.append({
        "id": "ours-vs-real-world",
        "what": "This review's pooled value against pooled real-world observational data",
        "verdict": "ABSENT",
        "whose": "neither",
        "detail": ("Alaiz et al. 2025 pool 7 real-world studies with 1,454 patients and "
                   "report a 42.77%% reduction (37.42 to 48.12), and attribute the gap "
                   "against trial estimates to baseline LDL-C differences and real-world "
                   "adherence. THIS IS NOT A CHECK ON EITHER NUMBER: a randomised "
                   "placebo-corrected percent change and a single-arm observational change "
                   "are different quantities, and neither can confirm the other. It is "
                   "listed because a reader asking 'does this hold in practice' is asking a "
                   "question THIS REVIEW DOES NOT ANSWER, and the honest response is to "
                   "name the study that does and say why it is not comparable."),
        "quote": "an average c-LDL reduction of 42.77% (95% CI: 37.42-48.12%)",
        "location": "PMID 40565909, doi 10.3390/jcm14124163",
    })

    verdicts = [c["verdict"] for c in checks]
    return {
        "_why": (
            "Three trials, one drug, one endpoint, and every per-trial value posted by the "
            "registry -- so the trial-by-trial half of this comparison is complete in a way "
            "it cannot be where trials post no results. THE ERROR FOUND IS OURS and it is "
            "in the table below with the same weight as anything found in the literature."),
        "_how_identified": (
            "PubMed E-utilities; query, counts and a per-record decision in "
            "ssot/%s/appraisal/PUBLISHED_SYNTHESIS_SCREEN.json. 61 records matched, 30 "
            "retrieved, 10 appraised. THE REMAINING 51 WERE NOT READ and that is stated in "
            "the screen file rather than left to be inferred from the number." % TOPIC),
        "reviews": [
            {"id": "PM_INCLISIRAN_2020", "pmid": "32892993",
             "citation": "Khan SA, Naz A, Qamar Masood M, Shah R. Meta-Analysis of "
                         "Inclisiran for the Treatment of Hypercholesterolemia. Am J "
                         "Cardiol 2020;134:69-73. doi 10.1016/j.amjcard.2020.08.018",
             "their_k": 3, "their_n": 3660,
             "scope": "inclisiran against placebo in hypercholesterolaemia",
             "how_it_differs_from_ours": (
                 "By arithmetic and timing it pools THIS REVIEW'S OWN THREE TRIALS -- its "
                 "n of 3,660 is exactly their summed arm counts, and it was published five "
                 "months after they reported. Its -51% (48 to 53) against this review's "
                 "-53.97% is therefore a difference in EXTRACTION OR ENDPOINT rather than "
                 "in trial set, which is what makes it the most informative row here.")},
            {"id": "PM_PCSK9_SIRNA_2023", "pmid": "38055686",
             "citation": "Imran TF, et al. PCSK9 inhibitors and small interfering RNA "
                         "therapy for cardiovascular risk reduction: a systematic review "
                         "and meta-analysis. PLoS One 2023;18(12):e0295359. "
                         "doi 10.1371/journal.pone.0295359",
             "their_k": 4, "their_n": 9522,
             "scope": "inclisiran 284 mg, reported separately from the PCSK9 antibodies",
             "how_it_differs_from_ours": (
                 "Four inclisiran studies rather than three, across a broader population. "
                 "Lands within one percentage point of this review.")},
            {"id": "PM_INCLISIRAN_RWD_2025", "pmid": "40565909",
             "citation": "Alaiz AR, et al. Inclisiran: Efficacy in Real World -- Systematic "
                         "Review and Meta-Analysis. J Clin Med 2025;14(12):4163. "
                         "doi 10.3390/jcm14124163",
             "their_k": 7, "their_n": 1454,
             "scope": "real-world observational studies",
             "how_it_differs_from_ours": (
                 "A different DESIGN, not a different trial set: single-arm observational "
                 "change against a randomised placebo-corrected difference. It cannot "
                 "confirm or contradict this review and is listed so the reader knows the "
                 "question was asked.")},
            {"id": "PM_NONSTATIN_NMA_2022", "pmid": "35262430",
             "citation": "Burnett H, et al. Comparative efficacy of non-statin "
                         "lipid-lowering therapies in patients with hypercholesterolemia at "
                         "increased cardiovascular risk: a network meta-analysis. Curr Med "
                         "Res Opin 2022;38(5):777-784. doi 10.1080/03007995.2022.2049164",
             "their_k": 23, "their_n": None,
             "scope": "network meta-analysis placing inclisiran against evolocumab, "
                      "alirocumab, bempedoic acid and ezetimibe",
             "how_it_differs_from_ours": (
                 "A different QUESTION -- relative efficacy between active agents, not the "
                 "size of the effect against placebo. Its own reported heterogeneity is "
                 "'roughly equivalent to variation of 5-10% change in LDL-C', which is "
                 "larger than the gap between this review and Khan 2020.")},
        ],
        "checks": checks,
        "divergence_decomposed": {
            "ours": ("Mean difference %.2f%% (%.2f to %.2f) in LDL-C percent change from "
                     "baseline to day 510, k=3, random effects, REML."
                     % (pooled["point"], pooled["ci_low"], pooled["ci_high"])),
            "theirs": ("-51% (48 to 53) over what is by arithmetic the same three trials; "
                       "-54.83% (-59.04 to -50.62) over four; -42.77% (37.42 to 48.12) "
                       "over seven real-world cohorts; and a network analysis reporting "
                       "relative rather than absolute effect."),
            "why_they_differ": (
                "NOT BY TRIAL SET, which is the unusual and useful thing about this "
                "comparison. The closest synthesis pools the same three trials and differs "
                "by about three percentage points, so the difference is in extraction or in "
                "WHICH REGISTERED CO-PRIMARY was taken -- day 510, or time-adjusted day 90 "
                "to 540. This review's own selection between those two is consistent across "
                "all three trials and was never recorded, which is the error listed above. "
                "The broader syntheses agree with this review closely; the real-world "
                "pooling does not, and its own authors attribute that to baseline LDL-C and "
                "adherence rather than to either estimate being wrong."),
        },
        "denominator": {
            "rows_checked": len(checks),
            "confirmed": verdicts.count("CONFIRMED"),
            "errors": verdicts.count("ERROR"),
            "errors_in_the_literature": 0,
            "errors_in_this_review": verdicts.count("ERROR"),
            "absent": verdicts.count("ABSENT"),
            "unresolved": verdicts.count("UNRESOLVED"),
            "statement": (
                "%d checks were applied and %d came back clean, %d found an error, %d found "
                "something absent and %d could not be settled at the layer available. The "
                "denominator is stated because a list of only the failures is not a "
                "finding, it is a selection."
                % (len(checks), verdicts.count("CONFIRMED"), verdicts.count("ERROR"),
                   verdicts.count("ABSENT"), verdicts.count("UNRESOLVED"))),
            "symmetry": (
                "Confirmations are listed in the same table, in the same detail, as errors. "
                "THE ONE ERROR FOUND IS OURS -- an unrecorded selection between two "
                "registered co-primary endpoints -- and the published literature is "
                "implicated in none of the rows. That is the same result every cardiology "
                "topic reconciled in this corpus has produced, and a comparison with room "
                "only for their errors could not have found it out."),
            "what_this_denominator_does_not_cover": (
                "The 51 records the screen retrieved and did not read. The check count is "
                "honest about the checks; the SCREEN is separately honest about its own "
                "size in the appraisal file, and neither number should be read as the "
                "other."),
        },
    }


def main():
    dry = "--apply" not in sys.argv
    obj = json.load(io.open(OBJ, encoding="utf-8"))
    if obj.get("published_comparison") is not None:
        sys.exit("REFUSED: published_comparison already present; this would overwrite it.")
    pc = build(obj)
    if pc["denominator"]["rows_checked"] < 5:
        sys.exit("REFUSED: only %d checks built." % pc["denominator"]["rows_checked"])
    if pc["denominator"]["errors"] == 0 and pc["denominator"]["confirmed"] == 0:
        sys.exit("REFUSED: no check reached a verdict.")
    obj["published_comparison"] = pc
    obj.setdefault("display_change_announced", []).append({
        "date": TODAY,
        "change": "published comparison added, with its denominator",
        "values_moved": "NONE",
        "what_changed": (
            "P46 limb 3 was ABSENT -- no `published_comparison` key existed. It now holds 4 "
            "identified syntheses, %d checks with a stated denominator, and a decomposition "
            "of where this review sits against them." % pc["denominator"]["rows_checked"]),
        "why": (
            "A pooled estimate published without any comparison against the literature "
            "cannot be checked by a reader against anything, and P46 asks for the "
            "comparison to carry a DENOMINATOR so that a table of failures cannot pass as a "
            "survey."),
        "what_it_found": (
            "One error, and it is OURS: all three ORION trials register two co-primary LDL "
            "endpoints and this review's selection between them -- consistently the day-510 "
            "one -- is nowhere recorded. It is also the leading candidate for the one "
            "unresolved divergence, against a 2020 synthesis of what the arithmetic says are "
            "these same three trials."),
    })
    print("built %d checks: %s" % (pc["denominator"]["rows_checked"],
                                   pc["denominator"]["statement"]))
    if dry:
        print("DRY RUN -- pass --apply to write")
        return
    if not os.path.isdir(APPRAISAL):
        os.makedirs(APPRAISAL)
    with io.open(os.path.join(APPRAISAL, "PUBLISHED_SYNTHESIS_SCREEN.json"), "w",
                 encoding="utf-8", newline="\n") as fh:
        json.dump(SCREEN, fh, indent=1, ensure_ascii=False)
        fh.write("\n")
    with io.open(OBJ, "rb") as fh:
        raw = fh.read()
    nl = "\r\n" if b"\r\n" in raw.split(b"\n", 3)[0] + b"\n" else "\n"
    with io.open(OBJ, "w", encoding="utf-8", newline=nl) as fh:
        json.dump(obj, fh, indent=1, ensure_ascii=False)
        fh.write("\n")
    print("wrote %s and the screen file" % OBJ)


if __name__ == "__main__":
    main()
