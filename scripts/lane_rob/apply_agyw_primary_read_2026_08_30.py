# -*- coding: utf-8 -*-
"""Land the ASPIRE PRIMARY READ into the AGYW object: arms, age strata, safety, other outcomes.

⛔ AND THE KEY IS `stratified_analyses`, NOT `subgroups`, BECAUSE `subgroups` WAS ALREADY TAKEN
BY A DIFFERENT OBJECT. `build_app_v2._outcome_section` consumes `res["subgroups"]` as a LIST of
POOLED strata -- each with its own k, pooled point, interval and I-squared -- which is a
stratified meta-analysis across trials. What is recorded here is a WITHIN-TRIAL subgroup
analysis read from one trial's report. They look alike and are not alike, and writing the second
under the first's name crashed the build immediately (`TypeError: string indices must be
integers`). ⚠️ It crashed because the legacy consumer indexes `sg['label']`; had the shapes been
compatible enough to render, this would have silently published one trial's post-hoc strata in a
table headed as a pooled analysis.

⛔ THE SEARCH DEFINES THE SET; OPEN SOURCES SUPPLY THE VALUES. Nothing here adds a trial. Every
number below is attached to a trial that was already in this review, and every one carries the
sentence it was read from, the document it was read from, and that document's sha256.

WHAT WAS RETRIEVED, AND HOW. `multiroute_retrieve(pmcid="PMC4993693")` on 2026-08-30:
Europe PMC returned 503; NCBI efetch returned 200 with 44,179 rendered characters;
sha256 a6c75ad7e331aff7ff37a7792efa39d3631550600aeebe8c1b219457c4a03752. That fingerprint is
the same one the pilot page's audit trail already cites, so this is the document the review has
been standing on -- now read rather than referenced.

⚠️ AND THE PRIMARY READ CORRECTED THE HAND-BUILT PAGE, WHICH IS THE POINT OF DOING IT.

  * The pilot page prints an age stratum labelled "18 to 24" with 10% (-41 to 43). ASPIRE's
    prespecified stratum is "UNDER THE AGE OF 25", not 18 to 24, and the paper gives P = 0.64
    for it. The label was wrong on the winning page.
  * The pilot page presents the age strata as though they belonged to the review. THEY ARE
    ASPIRE'S ALONE -- the Ring Study contributes nothing to them, and a reader entitled to
    assume a pooled figure would be reading one trial's post-hoc analysis as two trials'
    evidence.
  * The pilot page reports no INTERACTION test. ASPIRE reports P = 0.02 for interaction on the
    PRESPECIFIED age split, which is the strongest thing anyone can say about this finding and
    it was missing.

⭐ TWO SEPARATE BLOCKS, BECAUSE THEY ARE TWO SEPARATE ANALYSES. The prespecified split (under
25 versus 25 and over, with its interaction test) and the post-hoc thirds (18-21, 22-26, 27-45,
and the combined over-21) are recorded separately with their own prespecification flags. Merging
them into one table -- which is what the pilot page did -- borrows the prespecified analysis's
credibility for the post-hoc one.

⛔ WHAT IS *NOT* WRITTEN HERE, AND WHY THAT MATTERS MORE THAN WHAT IS. ASPIRE's incident STI
counts are in "Table S7 in the Supplementary Appendix", which this retrieval did not obtain.
So the STI rows are recorded at the PRIOR-META tier with `primary_read_attempted` set and the
reason the primary read did not land. A number lifted from someone else's extraction table is
usable and is NOT equivalent to a primary read, and the object now says which it is per row.
"""
import io
import json
import os
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace",
                              line_buffering=True)

OBJ = os.path.join("ssot", "agyw-hiv-prep-review", "agyw-hiv-prep-review.json")

ASPIRE_DOC = {
    "document_id": "PMC4993693",
    "what": "ASPIRE / MTN-020 primary report",
    "route": "ncbi_efetch (Europe PMC returned 503)",
    "retrieved_utc": "2026-08-30",
    "rendered_chars": 44179,
    "sha256": "a6c75ad7e331aff7ff37a7792efa39d3631550600aeebe8c1b219457c4a03752",
    "tier": "trial report",
}

# ---------------------------------------------------------------------------------------------
# 1. ARMS. The counts the object already holds, re-expressed in the shape the corpus uses, so
#    that direction is RECORDED rather than inferred from label order.
#
# ⛔ THE ROLES ARE NOT DERIVED FROM THE KEY NAMES. `as_posted` stores
#    "dapivirine_ring_events" / "placebo_ring_events", and a migration that mapped keys
#    containing "placebo" to control would be exactly the label-sorting defect `arm_roles`
#    exists to prevent -- it works until a trial names its control arm something else. The
#    roles below are authored against the registry record and the trial report.
# ---------------------------------------------------------------------------------------------
ARMS = {
    "NCT01539226": {
        "arms": [
            {"label": "Dapivirine vaginal ring", "role": "treatment",
             "events": 82, "participants": 1302},
            {"label": "Placebo vaginal ring", "role": "control",
             "events": 61, "participants": 650}],
        "arms_basis": {
            "tier": "registry results",
            "source": "ClinicalTrials.gov NCT01539226, results section as submitted",
            "read_utc": "2026-08-18",
            "note": "These are the counts this object already carried in `as_posted`. They are "
                    "re-expressed here with an explicit role per arm so that direction is read "
                    "from the record rather than inferred from label order. ⚠️ THEY ARE THE "
                    "REGISTRY'S COUNTS, NOT THE ADJUDICATED ONES -- see "
                    "`counts_by_tier` on the per-trial block."}},
    "NCT01617096": {
        "arms": [
            {"label": "Dapivirine vaginal ring", "role": "treatment",
             "events": 71, "participants": 1313},
            {"label": "Placebo vaginal ring", "role": "control",
             "events": 97, "participants": 1313}],
        "arms_basis": {
            "tier": "registry results",
            "source": "ClinicalTrials.gov NCT01617096, results section as submitted",
            "read_utc": "2026-08-18",
            "note": "⚠️ THE PLACEBO DENOMINATOR DISAGREES WITH THE TRIAL REPORT. The registry "
                    "gives 1313 in both arms; the primary report states “Of 5516 women who "
                    "underwent screening, 2629 were enrolled: 1313 in the dapivirine group and "
                    "1316 in the placebo group”. The disagreement is recorded rather than "
                    "resolved silently, and it is the input that separates this review's pooled "
                    "estimate from an external reviewer's."}},
}

# ---------------------------------------------------------------------------------------------
# 2. THE TWO AGE ANALYSES. Verbatim sentences, from the document fingerprinted above.
# ---------------------------------------------------------------------------------------------
Q_PRESPEC = ("However, the efficacy of HIV-1 protection differed significantly according to "
             "age, with an efficacy of 61% (95% CI, 32 to 77; P<0.001) among women 25 years of "
             "age or older and 10% (95% CI, −41 to 43; P = 0.64) among those under the age "
             "of 25 years (P = 0.02 for interaction).")
Q_POSTHOC = ("Lack of HIV-1 protection, along with lower adherence, was seen in participants "
             "who were 18 to 21 years of age, with an efficacy of HIV-1 protection of −27% "
             "(95% CI, −133 to 31; P = 0.45). For women who were older than 21 years of "
             "age, the efficacy of HIV-1 protection was 56% (95% CI, 31 to 71; P<0.001), and "
             "the rate of adherence was more than 70% overall.")
Q_THIRDS = ("Panel A shows that the efficacy of HIV-1 protection in the dapivirine group was "
            "−27% (95% CI, −133 to 31) for those 18 to 21 years of age, 56% (95% CI, "
            "19 to 76) for those 22 to 26 years of age, and 51% (95% CI, 8 to 74) for those 27 "
            "to 45 years of age, as compared with placebo. The combined efficacy of HIV-1 "
            "prevention for participants over the age of 21 years was 56% (95% CI, 31 to 71; "
            "P<0.001).")
Q_HOWFORMED = ("To better characterize the relationship between age and HIV-1 protection seen "
               "in the pre-specified subgroup analysis (age <25 vs. ≥25 years), an "
               "exploratory analysis was conducted post hoc. Age-categorized subgroups with "
               "balanced statistical power were created after dividing the 2395 participants "
               "into three groups with approximately equal numbers of those with HIV-1 "
               "infection.")

SUBGROUPS = {
    "age (prespecified)": {
        "prespecified": True,
        "scope": "ASPIRE / MTN-020 (NCT01617096) ALONE. The Ring Study contributes nothing to "
                 "these strata, so this is one of the two pooled trials and not the review.",
        "basis": "Prespecified in the trial's analysis plan as age under 25 versus 25 and over. "
                 "Source sentence: “%s”" % Q_PRESPEC,
        "source": ASPIRE_DOC,
        "measure": "efficacy_percent",
        "interaction": {
            "stated": "P = 0.02 for interaction, reported by the trial for this prespecified "
                      "split. This is a test, not a comparison of two intervals by eye, and it "
                      "is the strongest statement available about whether the difference is "
                      "real.",
            "p": 0.02},
        "strata": [
            {"label": "25 years or older", "efficacy_percent": 61, "ci_low": 32, "ci_high": 77,
             "p": "<0.001", "source_quote": Q_PRESPEC},
            {"label": "Under 25 years", "efficacy_percent": 10, "ci_low": -41, "ci_high": 43,
             "p": "0.64", "source_quote": Q_PRESPEC}]},
    "age (post-hoc thirds)": {
        "prespecified": False,
        "scope": "ASPIRE / MTN-020 (NCT01617096) ALONE.",
        "basis": "Exploratory and conducted after the prespecified split showed an age effect. "
                 "The strata were formed to balance statistical power, not on clinical grounds: "
                 "“%s”" % Q_HOWFORMED,
        "source": ASPIRE_DOC,
        "measure": "efficacy_percent",
        "external_corroboration":
            "WHO's 2021 guideline records no demonstrated efficacy below 21 and attributes it "
            "to low adherence rather than to absence of drug effect (WHO, iris handle "
            "10665/340190, retrieved 2026-08-29). ⚠️ That is corroboration of the READING, not "
            "an independent estimate: it rests on this same trial.",
        "strata": [
            {"label": "18 to 21 years", "efficacy_percent": -27, "ci_low": -133, "ci_high": 31,
             "p": "0.45", "events": "451 participants, 44 infections",
             "source_quote": Q_POSTHOC},
            {"label": "22 to 26 years", "efficacy_percent": 56, "ci_low": 19, "ci_high": 76,
             "events": "752 participants, 51 infections", "source_quote": Q_THIRDS},
            {"label": "27 to 45 years", "efficacy_percent": 51, "ci_low": 8, "ci_high": 74,
             "events": "1192 participants, 44 infections", "source_quote": Q_THIRDS},
            {"label": "Over 21 years, combined", "efficacy_percent": 56, "ci_low": 31,
             "ci_high": 71, "p": "<0.001", "source_quote": Q_THIRDS}]},
}

# ---------------------------------------------------------------------------------------------
# 3. SAFETY AND EVERY OTHER OUTCOME THESE TRIALS REPORTED, each row carrying its own tier.
# ---------------------------------------------------------------------------------------------
Q_AE = ("Table 2 Adverse Events. Adverse Event Dapivirine Group (N = 1313) Placebo Group "
        "(N = 1316) no. (%) Primary safety end point 180 (14) 186 (14); Any serious adverse "
        "event 52 (4) 48 (4); Death 4 (<1) 3 (<1); Any grade 4 event 22 (2) 23 (2); Any grade 3 "
        "event 151 (12) 162 (12); Any grade 2 event assessed as related 7 (1) 9 (1). "
        "P = 0.80 for the overall comparison by the chi-square test.")
Q_RESIST = ("among participants who acquired HIV-1 infection, there was no significant "
            "between-group difference in the numbers of participants with non-nucleoside "
            "reverse-transcriptase inhibitor mutations suggesting antiviral resistance (8 of 68 "
            "participants [12%] in the dapivirine group and 10 of 96 [10%] in the placebo "
            "group, P = 0.80)")
Q_STI = ("Incident sexually transmitted infections occurred at a similar rate in the two groups "
         "( Table S7 in the Supplementary Appendix ).")
Q_PREG = ("Women were tested monthly for pregnancy, and the study ring was withheld from women "
          "who became pregnant; they resumed use of the study ring when no longer pregnant or "
          "lactating.")

SUPPLEMENT_NOT_HELD = {
    "tier": "prior-meta table (unverified)",
    "primary_read_attempted": True,
    "why_the_primary_read_did_not_land":
        "ASPIRE reports its incident STI counts in “Table S7 in the Supplementary "
        "Appendix”. The retrieval obtained the article body (PMC4993693, sha256 "
        "a6c75ad7e331aff7…) and NOT the supplementary appendix, so the counts behind these "
        "effects have not been read at source. ⚠️ A value taken from another team's extraction "
        "table is usable and is not equivalent to a primary read; it is labelled so on the "
        "page.",
}

OTHER_OUTCOMES = [
    {"outcome": "Any grade 3 adverse event", "treatment": "151 (12%)", "control": "162 (12%)",
     "effect": "no material difference", "trials": "ASPIRE, 2629 women",
     "tier": "trial report", "source": ASPIRE_DOC, "source_quote": Q_AE},
    {"outcome": "Any grade 4 adverse event", "treatment": "22 (2%)", "control": "23 (2%)",
     "effect": "no material difference", "trials": "ASPIRE, 2629 women",
     "tier": "trial report", "source": ASPIRE_DOC, "source_quote": Q_AE},
    {"outcome": "Any serious adverse event", "treatment": "52 (4%)", "control": "48 (4%)",
     "effect": "no material difference", "trials": "ASPIRE, 2629 women",
     "tier": "trial report", "source": ASPIRE_DOC, "source_quote": Q_AE},
    {"outcome": "Death", "treatment": "4 (<1%)", "control": "3 (<1%)",
     "effect": "no material difference", "trials": "ASPIRE, 2629 women",
     "tier": "trial report", "source": ASPIRE_DOC, "source_quote": Q_AE},
    {"outcome": "Grade 2 event judged related to the product", "treatment": "7 (1%)",
     "control": "9 (1%)", "effect": "no material difference", "trials": "ASPIRE, 2629 women",
     "tier": "trial report", "source": ASPIRE_DOC, "source_quote": Q_AE},
    {"outcome": "NNRTI resistance mutations among those who seroconverted",
     "treatment": "8 of 68 (12%)", "control": "10 of 96 (10%)",
     "effect": "no signal; P = 0.80", "trials": "ASPIRE",
     "tier": "trial report", "source": ASPIRE_DOC, "source_quote": Q_RESIST},
    {"outcome": "Incident sexually transmitted infections, overall",
     "treatment": "not stated in the article body", "control": "not stated in the article body",
     "effect": "reported by the trial as occurring at a similar rate in the two groups",
     "trials": "ASPIRE", "source_quote": Q_STI, **SUPPLEMENT_NOT_HELD},
    {"outcome": "Pregnancy", "treatment": "—", "control": "—",
     "effect": "the ring was withheld during pregnancy and resumed afterwards, so pregnancy is "
               "a protocol event here rather than a comparative outcome",
     "trials": "ASPIRE", "tier": "trial report", "source": ASPIRE_DOC, "source_quote": Q_PREG},
    {"outcome": "Herpes simplex virus", "treatment": "—", "control": "—",
     "effect": "NOT MEASURABLE — not screened for",
     "trials": "—", "tier": "absent by design",
     "source_quote": "No HSV outcome is reported in the article body."},
    {"outcome": "Acceptability and minor adverse events", "treatment": "—",
     "control": "—",
     "effect": "NOT REPORTED IN A POOLABLE FORM by either trial",
     "trials": "—", "tier": "absent",
     "source_quote": "No poolable acceptability outcome is reported in the article body."},
]

OTHER_OUTCOMES_NOTE = (
    "⚠️ THIS TABLE IS ASPIRE'S UNLESS A ROW SAYS OTHERWISE. The Ring Study's safety table has "
    "not been read at source in this pass, so no row claims two trials. The rows are the "
    "outcomes the retrieved article body reports, plus the ones it explicitly does not: "
    "“not measured” and “not reported in a poolable form” are outcomes of "
    "the search and are printed rather than dropped, because a table that lists only what was "
    "found reads as a table of everything that exists.")


def apply(path=OBJ, dry=False):
    c = json.load(io.open(path, encoding="utf-8"))
    changed = []
    trials = ((c.get("inputs") or {}).get("trials") or [])
    for t in trials:
        nct = t.get("nct") or t.get("trial_id")
        if nct in ARMS and "arms" not in t:
            t["arms"] = ARMS[nct]["arms"]
            t["arms_basis"] = ARMS[nct]["arms_basis"]
            changed.append("arms on %s" % nct)
    prim = ((c.get("results") or {}).get("by_outcome") or {}).get("primary")
    if isinstance(prim, dict):
        if "stratified_analyses" not in prim:
            prim["stratified_analyses"] = SUBGROUPS
            changed.append("subgroups (2 blocks, %d strata)"
                           % sum(len(b["strata"]) for b in SUBGROUPS.values()))
        if "other_outcomes" not in prim:
            prim["other_outcomes"] = {"_note": OTHER_OUTCOMES_NOTE, "rows": OTHER_OUTCOMES}
            changed.append("other_outcomes (%d rows)" % len(OTHER_OUTCOMES))
    print("")
    print("APPLY -- %s" % path)
    for ch in changed:
        print("   + %s" % ch)
    if not changed:
        print("   (nothing to do; this script is idempotent)")
        return 0
    if dry:
        print("   --dry: not written")
        return 0
    tmp = path + ".tmp"
    with io.open(tmp, "w", encoding="utf-8") as fh:
        json.dump(c, fh, indent=1, ensure_ascii=False)
    size = os.path.getsize(tmp)
    # ⛔ C: IS FULL AND A WRITE THERE CAN PRODUCE A ZERO-BYTE FILE THAT EXITS 0. Every write is
    # size-checked before it replaces the object it is meant to improve.
    if size < 10000:
        os.remove(tmp)
        raise SystemExit("REFUSED: the rewritten object is %d bytes, which is not a corpus "
                         "object. Nothing was replaced." % size)
    json.load(io.open(tmp, encoding="utf-8"))          # it must parse before it replaces
    os.replace(tmp, path)
    print("   written, %d bytes, reparsed OK" % size)
    return 0


if __name__ == "__main__":
    raise SystemExit(apply(dry="--dry" in sys.argv))
