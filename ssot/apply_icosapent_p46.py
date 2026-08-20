"""icosapent-lipid: establish the estimand and add the published comparison. P46 limbs 3.

IDENTITY BEFORE NUMBERS. MARINE is NCT01047683 and ANCHOR is NCT01047501, and both carry
the registry's own posted primary-outcome title on this object -- BYTE-IDENTICAL strings:

    "Difference Between AMR101 (Ethyl Icosapentate) and Placebo Treatment Groups in
     Triglyceride Lowering Effect"

Not similar. Identical. So the estimand is established by reading rather than assumed, and
`estimand_established` moves False -> True with a checked reason replacing the never-checked
placeholder -- the same inversion found on rosuvastatin and empagliflozin today, where the
NEVER-CHECKED state was written as though it were a negative finding.

WHAT THE IDENTICAL TITLES DO NOT ESTABLISH, and it is the whole heterogeneity: THE
POPULATIONS DIFFER. MARINE enrolled severe hypertriglyceridaemia; ANCHOR enrolled
statin-treated patients with triglycerides in a lower band. Same registered quantity, two
different populations, and I-squared of 64.2% on two trials is what that looks like. The
pool answers "how much does 4 g/day lower triglycerides" across two settings, not within
one, and the object says so rather than letting the identical titles imply more than they
carry.

THE PUBLISHED SETS ARE INFERRED, NOT READ -- the line held on inclisiran and empagliflozin.
No included-study table was opened for any appraised synthesis.
"""
import io
import json
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOPIC = "icosapent-lipid-auto-full-review"
TODAY = "2026-08-20"
STAMP = TODAY.replace("-", "_")
OBJ = os.path.join(REPO, "ssot", TOPIC, TOPIC + ".json")
APPRAISAL = os.path.join(REPO, "ssot", TOPIC, "appraisal")

TITLE = ("Difference Between AMR101 (Ethyl Icosapentate) and Placebo Treatment Groups in "
         "Triglyceride Lowering Effect")

SCREEN = {
    "_what_this_is": "The search behind `published_comparison`, at its real size.",
    "run_utc": TODAY,
    "transport": "PubMed E-utilities via the bio-research MCP server",
    "query": ("(icosapent ethyl OR AMR101 OR eicosapentaenoic acid) AND triglyceride AND "
              "(meta-analysis[Publication Type] OR meta-analysis[Title])"),
    "records_matched": 35,
    "records_retrieved": 20,
    "records_appraised_at_metadata_level": 4,
    "records_not_appraised": 31,
    "why_not_all_were_appraised": (
        "The 4 appraised were the highest-relevance records. THE REMAINING 31 WERE NOT "
        "READ, and the headline finding -- that no identified synthesis pools MARINE with "
        "ANCHOR on this endpoint -- is bounded by that."),
    "no_included_study_table_was_read": (
        "None of the four. Trial sets are INFERRED from abstract text, participant totals "
        "and stated scope."),
    "appraised": [
        {"pmid": "32114706", "decision": "INCLUDED",
         "why": "Cochrane review of omega-3 for cardiovascular disease, 86 RCTs, 162,796 "
                "participants; reports a triglyceride reduction with high-certainty "
                "evidence and is the largest identified synthesis touching this endpoint"},
        {"pmid": "37264945", "decision": "INCLUDED",
         "why": "dose-response meta-analysis over 90 RCTs and 72,598 participants, "
                "reporting the shape of the triglyceride relationship with dose"},
        {"pmid": "33750272", "decision": "EXCLUDED",
         "why": "lower-extremity arterial disease; a different population and the "
                "triglyceride result is a secondary outcome graded very low"},
        {"pmid": "28161092", "decision": "EXCLUDED",
         "why": "non-alcoholic fatty liver disease; reports triglyceride change in mg/dL, "
                "not percent change, and is not convertible without their baselines"},
    ],
}


def build(obj):
    blk = obj["results"]["by_outcome"]["primary"]
    p = blk["pooled"]
    het = blk.get("heterogeneity") or {}
    trials = {t["nct"]: t for t in obj["inputs"]["trials"]}
    checks = []

    for nct, name in (("NCT01047683", "MARINE"), ("NCT01047501", "ANCHOR")):
        t = trials[nct]
        pc = t["registration_primary_counts"]
        eff = t["by_outcome"]["primary"]["effect"]
        checks.append({
            "id": "identity-%s" % name.lower(),
            "what": "%s keyed to a verified registration BEFORE any count is compared" % name,
            "verdict": "CONFIRMED",
            "whose": "ours",
            "detail": ("%s is keyed to %s, carrying the registry's own posted primary "
                       "outcome title on this object. Its contributed value is %s%% "
                       "(%s to %s). IDENTITY BEFORE NUMBERS: the trial is fixed by "
                       "registration, not by an author string."
                       % (name, nct, eff["point"], eff["ci_low"], eff["ci_high"])),
            "quote": pc["title"],
            "location": "https://clinicaltrials.gov/study/%s" % nct,
        })

    checks.append({
        "id": "estimand-titles-are-byte-identical",
        "what": "Whether both trials registered the SAME primary outcome",
        "verdict": "CONFIRMED",
        "whose": "ours",
        "detail": ("BYTE-IDENTICAL, not merely similar: both registrations post %r word for "
                   "word. There is no orthographic gap to adjudicate here, which is worth "
                   "recording because two topics reconciled today turned on exactly such a "
                   "gap -- 'Percent' against 'Percentage' on the ORION trials, and one word "
                   "'the' on the EMPEROR trials, the second of which had been written up on "
                   "the object as the trials measuring DIFFERENT things." % TITLE),
        "quote": TITLE,
        "location": "inputs.trials[].registration_primary_counts.title",
    })
    checks.append({
        "id": "identical-titles-do-not-make-identical-populations",
        "what": "What the shared estimand does NOT establish",
        "verdict": "ABSENT",
        "whose": "ours -- a limit, stated",
        "detail": ("THE POPULATIONS DIFFER AND THAT IS THE HETEROGENEITY. MARINE enrolled "
                   "severe hypertriglyceridaemia; ANCHOR enrolled statin-treated patients "
                   "in a lower triglyceride band. The registered QUANTITY is the same in "
                   "both; the PATIENTS are not. I-squared is %s%% on two trials, tau-squared "
                   "%s, and the per-trial values are %s%% and %s%% -- an eleven-point "
                   "spread. This pool answers 'how much does 4 g/day lower triglycerides' "
                   "ACROSS two settings, not within one. Recorded because identical titles "
                   "invite a reader to assume more than they carry."
                   % (het.get("i2"), het.get("tau2"),
                      trials["NCT01047683"]["by_outcome"]["primary"]["effect"]["point"],
                      trials["NCT01047501"]["by_outcome"]["primary"]["effect"]["point"])),
        "quote": None,
        "location": "results.by_outcome.primary.heterogeneity",
    })
    checks.append({
        "id": "no-synthesis-pools-marine-with-anchor",
        "what": "Whether any identified synthesis pools MARINE with ANCHOR on this endpoint",
        "verdict": "ABSENT",
        "whose": "neither -- a fact about the literature",
        "detail": ("NONE OF THE FOUR APPRAISED DOES. Every identified synthesis is CLASS-WIDE "
                   "omega-3 -- eicosapentaenoic acid pooled with docosahexaenoic acid and "
                   "alpha-linolenic acid, across supplement trials, dietary-advice trials "
                   "and enriched foods. Not one is an AMR101-specific pool of these two "
                   "registrations. So this review's estimate is NEITHER CORROBORATED NOR "
                   "CONTRADICTED by the identified literature -- IT IS UNREPLICATED, the "
                   "same result as empagliflozin-hf reached the same night by a different "
                   "route. Bounded by the 31 records the screen retrieved and did not read."),
        "quote": None,
        "location": "ssot/%s/appraisal/PUBLISHED_SYNTHESIS_SCREEN.json" % TOPIC,
    })
    checks.append({
        "id": "ours-vs-cochrane-2020",
        "what": "This review against the largest identified synthesis touching this endpoint",
        "verdict": "UNRESOLVED",
        "whose": "neither -- it cannot be settled at the layer available",
        "detail": ("Abdelhamid et al. 2020 (Cochrane) pool 86 RCTs with 162,796 participants "
                   "and report that increasing long-chain omega-3 'reduced triglycerides by "
                   "about 15%% in a dose-dependent way', high-certainty. This review reports "
                   "%s%% (%s to %s). THE NUMBERS ARE FAR APART AND THAT IS EXPECTED, NOT A "
                   "DISAGREEMENT: theirs spans every dose from 0.5 g to over 5 g a day, "
                   "every omega-3 species, and populations at varying cardiovascular risk; "
                   "this is 4 g/day of purified EPA in hypertriglyceridaemia, which is the "
                   "high end of their dose range in the population where the effect is "
                   "largest. THEIR OWN DOSE-DEPENDENCE FINDING PREDICTS THE DIRECTION OF "
                   "THE GAP. Whether it predicts its SIZE cannot be decided without their "
                   "included-study table and a dose-stratified estimate, so this is left "
                   "unresolved rather than reported as agreement."
                   % (p["point"], p["ci_low"], p["ci_high"])),
        "quote": "increasing LCn3 reduced triglycerides by ~15% in a dose-dependent way "
                 "(high-certainty evidence)",
        "location": "PMID 32114706, doi 10.1002/14651858.CD003177.pub5",
        "what_would_settle_it": "A dose-stratified triglyceride estimate restricted to EPA "
                                "at 4 g/day in hypertriglyceridaemia, from their data.",
    })
    checks.append({
        "id": "ours-vs-dose-response-2023",
        "what": "This review against a continuous dose-response synthesis",
        "verdict": "CONFIRMED",
        "whose": "neither -- they are consistent",
        "detail": ("Wang et al. 2023 pool 90 RCTs with 72,598 participants and find an "
                   "approximately LINEAR dose-response for triglyceride lowering, most "
                   "evident 'in populations with hyperlipidemia and overweight/obesity who "
                   "were given medium to high doses (>2 g/d)'. This review's trials give "
                   "4 g/day in hypertriglyceridaemia -- inside exactly that stratum -- and "
                   "report a reduction well beyond the class-wide average. THAT IS "
                   "CONSISTENT, and consistency with a dose-response shape is a weaker "
                   "claim than agreement between two estimates of one quantity. It is "
                   "recorded as consistency and not as corroboration."),
        "quote": "an approximately linear dose-response relationship for triglyceride ... "
                 "who were given medium to high doses (>2 g/d)",
        "location": "PMID 37264945, doi 10.1161/JAHA.123.029512",
    })

    v = [c["verdict"] for c in checks]
    return {
        "_why": ("Two trials, one drug, one registered endpoint word for word -- and no "
                 "AMR101-specific synthesis of them in the identified literature."),
        "_how_identified": (
            "PubMed E-utilities; query, counts and a per-record decision in "
            "ssot/%s/appraisal/PUBLISHED_SYNTHESIS_SCREEN.json. 35 matched, 20 retrieved, "
            "4 appraised, 31 NOT READ. NO INCLUDED-STUDY TABLE WAS READ: trial sets are "
            "INFERRED from abstract text and stated scope." % TOPIC),
        "identity_basis": (
            "MARINE keyed to NCT01047683 and ANCHOR to NCT01047501, each carrying the "
            "registry's own posted primary-outcome title, BEFORE any count was compared."),
        "reviews": [
            {"id": "PM_COCHRANE_OMEGA3_2020", "pmid": "32114706",
             "citation": "Abdelhamid AS, et al. Omega-3 fatty acids for the primary and "
                         "secondary prevention of cardiovascular disease. Cochrane Database "
                         "Syst Rev 2020;3:CD003177. doi 10.1002/14651858.CD003177.pub5",
             "their_k": 86, "their_n": 162796,
             "scope": "all long-chain omega-3 and alpha-linolenic acid, every dose, "
                      "supplements and diet",
             "trial_set_read": False,
             "how_it_differs_from_ours": (
                 "Class-wide across species, dose and delivery. Its ~15%% is an average over "
                 "a dose range whose top end is where this review's trials sit.")},
            {"id": "PM_DOSE_RESPONSE_2023", "pmid": "37264945",
             "citation": "Wang T, et al. Association Between Omega-3 Fatty Acid Intake and "
                         "Dyslipidemia: A Continuous Dose-Response Meta-Analysis. J Am "
                         "Heart Assoc 2023;12(11):e029512. doi 10.1161/JAHA.123.029512",
             "their_k": 90, "their_n": 72598,
             "scope": "dose-response shape rather than a single pooled effect",
             "trial_set_read": False,
             "how_it_differs_from_ours": (
                 "Reports a SHAPE, not an estimate of this quantity. Consistency with a "
                 "shape is weaker than agreement between two estimates.")},
        ],
        "divergence_decomposed": {
            "ours": ("Mean difference %s%% (%s to %s) in triglyceride lowering against "
                     "placebo, 4 g/day AMR101, k=2, random effects, REML, I-squared %s%%."
                     % (p["point"], p["ci_low"], p["ci_high"], het.get("i2"))),
            "theirs": ("~15%% class-wide across 86 RCTs at every dose; and a "
                       "near-linear dose-response over 90 RCTs, strongest above 2 g/day in "
                       "hyperlipidaemia."),
            "why_they_differ": (
                "BY DOSE, SPECIES AND POPULATION -- not by disagreement. The published "
                "figures average across omega-3 species and the whole dose range; this "
                "review is purified EPA at the top of that range in the population where "
                "the effect is largest. THEIR OWN DOSE-DEPENDENCE PREDICTS THE DIRECTION OF "
                "THE GAP, and nothing available predicts its size. NO IDENTIFIED SYNTHESIS "
                "POOLS THESE TWO TRIALS, so none of them is an independent check on this "
                "estimate."),
        },
        "denominator": {
            "rows_checked": len(checks),
            "confirmed": v.count("CONFIRMED"),
            "errors": v.count("ERROR"),
            "errors_in_the_literature": 0,
            "errors_in_this_review": v.count("ERROR"),
            "absent": v.count("ABSENT"),
            "unresolved": v.count("UNRESOLVED"),
            "statement": (
                "%d checks were applied and %d came back clean, %d found an error, %d found "
                "something absent and %d could not be settled at the layer available. The "
                "denominator is stated because a list of only the failures is not a "
                "finding, it is a selection."
                % (len(checks), v.count("CONFIRMED"), v.count("ERROR"), v.count("ABSENT"),
                   v.count("UNRESOLVED"))),
            "symmetry": (
                "Confirmations are listed in the same table, in the same detail, as the "
                "absences. NO ERROR WAS FOUND ON EITHER SIDE HERE, and that is reported as "
                "plainly as an error would be: two of the six rows are ABSENCES rather than "
                "clean passes -- no synthesis pools this pair, and identical titles do not "
                "make identical populations."),
            "what_this_denominator_does_not_cover": (
                "The 31 records retrieved and not read, and the included-study table of "
                "every one of the four appraised. No published trial set here was read."),
        },
    }


def main():
    dry = "--apply" not in sys.argv
    obj = json.load(io.open(OBJ, encoding="utf-8"))
    if obj.get("published_comparison") is not None:
        sys.exit("REFUSED: published_comparison already present.")
    blk = obj["results"]["by_outcome"]["primary"]
    trials = {t["nct"]: t for t in obj["inputs"]["trials"]}
    for nct in ("NCT01047683", "NCT01047501"):
        held = (trials[nct].get("registration_primary_counts") or {}).get("title")
        if held != TITLE:
            sys.exit("REFUSED: %s holds %r, not the title this script was written "
                     "against. Re-read before writing." % (nct, held))

    blk["estimand_established"] = True
    blk["estimand_established_reason_%s" % STAMP] = (
        "CHECKED ON %s AND ESTABLISHED. Both registrations post the SAME primary outcome "
        "title, BYTE-IDENTICAL: %r. What that does NOT establish is a shared population -- "
        "MARINE enrolled severe hypertriglyceridaemia and ANCHOR statin-treated patients in "
        "a lower band, which is what I-squared of %s%% on two trials is measuring. The pool "
        "estimates the effect ACROSS two settings and the object says so." % (
            TODAY, TITLE, (blk.get("heterogeneity") or {}).get("i2")))
    blk["pool_uniformity"] = {
        "effect_measure": ["ESTABLISHED", "both are mean differences in percent change in "
                           "triglycerides against placebo, read from each registry record"],
        "estimand": ["ESTABLISHED", blk["estimand_established_reason_%s" % STAMP]],
        "population": ["NOT UNIFORM, AND STATED", "MARINE severe hypertriglyceridaemia; "
                       "ANCHOR statin-treated, lower triglyceride band. Same quantity, "
                       "different patients."],
        "superseded_%s" % STAMP: (
            "Both limbs previously read NOT ESTABLISHED with the reason 'not recorded on "
            "the page this object was extracted from' -- the NEVER-CHECKED state written as "
            "though it were a negative finding, the same inversion found on rosuvastatin "
            "and empagliflozin the same day."),
    }

    pc = build(obj)
    d = pc["denominator"]
    if d["rows_checked"] < 5:
        sys.exit("REFUSED: only %d checks." % d["rows_checked"])
    obj["published_comparison"] = pc
    obj.setdefault("display_change_announced", []).append({
        "date": TODAY,
        "change": "estimand established; published comparison added with its denominator",
        "values_moved": "NONE",
        "what_changed": ("`estimand_established` False -> True on byte-identical registered "
                         "titles, with the population difference stated separately. P46 "
                         "limb 3 was ABSENT and now holds 2 identified syntheses and %d "
                         "checks." % d["rows_checked"]),
        "why": ("A pooled estimate published with no comparison cannot be checked by a "
                "reader against anything, and an estimand recorded as NOT ESTABLISHED "
                "because nobody looked is not a negative finding."),
        "what_it_found": (
            "That NO identified synthesis pools MARINE with ANCHOR on this endpoint -- every "
            "one is class-wide omega-3 across species and dose. This review's estimate is "
            "UNREPLICATED. The Cochrane ~15%% is not a disagreement: their own "
            "dose-dependence finding predicts the direction of the gap, and nothing "
            "available predicts its size."),
    })
    print("estimand established; built %d checks: %s" % (d["rows_checked"], d["statement"]))
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
