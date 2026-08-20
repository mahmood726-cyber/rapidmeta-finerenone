"""attr-pn-review: the pool combines contrasts that are not the same kind of comparison.

THE PRIMARY DEFECT IS THE UNIT OF ANALYSIS, NOT THE FRAMING. A published network
meta-analysis of this exact question exists and separates the drugs rather than pooling
them, and reasonable people could argue about that. THIS IS NOT THAT ARGUMENT.

WHAT THE OBJECT HOLDS, and what each contrast actually is:

    APOLLO (NCT01960348)            patisiran   vs  sterile normal saline
                                    -- its own randomised placebo. Correct.
    HELIOS-A (NCT03759379)          arms recorded as "Vutrisiran + Vutrisiran" (treatment)
                                    vs "Patisiran + Vutrisiran" (control)
    NEURO-TTRansform (NCT04136184)  arms recorded as "Inotersen" (TREATMENT)
                                    vs "Eplontersen" (CONTROL)

ESTABLISHED FROM THE REGISTRATION ON 2026-08-20, NOT INFERRED. ClinicalTrials.gov NCT04136184:

  * Its brief title is "A Study to Evaluate the Efficacy and Safety of EPLONTERSEN ...".
    EPLONTERSEN IS THE EXPERIMENTAL AGENT AND INOTERSEN IS THE REFERENCE ARM. THE OBJECT
    HAS THEM THE WRONG WAY ROUND -- inotersen is recorded as the treatment.
  * "Participants included in the inotersen reference arm crossed over to eplontersen at
    Week 37 after completing the Week 35 assessments."
  * And the primary outcome's own description, verbatim: "As pre-specified in the protocol,
    the efficacy of eplontersen was to be assessed by comparing participants enrolled in
    the eplontersen arm only with the EXTERNAL PLACEBO GROUP. There was no statistical
    comparison planned between the inotersen arm and the eplontersen-treated/external
    placebo group arms."

SO THE STORED EFFECT IS NOT THE RANDOMISED CONTRAST AT ALL. It is eplontersen against the
placebo cohort of a DIFFERENT TRIAL -- NEURO-TTR, NCT01737398. The randomised comparison
this trial actually made has no planned statistical test.

The same is true of HELIOS-A, whose vutrisiran effect is reported against APOLLO's external
placebo rather than against its own randomised patisiran arm.

TWO OF THE THREE POOLED VALUES ARE NON-RANDOMISED EXTERNAL-CONTROL COMPARISONS, AND THE
OBJECT RECORDS ALL THREE AS RANDOMISED ARM CONTRASTS. Patisiran is the intervention in one
row and the comparator in another, inside one pooled number. No framing defends that.

AND NOTE WHAT DID NOT CATCH IT.

`estimand_established` is TRUE on this object and correctly so: all three trials measure
CHANGE FROM BASELINE IN mNIS+7, the same instrument and the same construct, with the
timepoint difference stated. I-squared is 88.1% -- exactly the signal a reader is taught to
distrust -- and it has been sitting on a live page.

A TOPIC CAN CARRY AN ESTABLISHED ESTIMAND, A VISIBLE I-SQUARED, AND A COMPARATOR SET THAT
MAKES THE POOL MEANINGLESS. `estimand_established` is being read as though it certifies the
CONTRAST. IT CERTIFIES THE MEASUREMENT. Every topic that passes estimand establishment
inherits that gap, and it is named here and in the standard rather than left implicit.

THE POOL IS REFERRED, NOT WITHDRAWN. Withdrawing a published estimate is Mahmood's
decision. The finding is complete and stated.
"""
import io
import json
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOPIC = "attr-pn-review"
TODAY = "2026-08-20"
STAMP = TODAY.replace("-", "_")
OBJ = os.path.join(REPO, "ssot", TOPIC, TOPIC + ".json")


def main():
    dry = "--apply" not in sys.argv
    obj = json.load(io.open(OBJ, encoding="utf-8"))
    blk = obj["results"]["by_outcome"]["primary"]
    trials = {t["nct"]: t for t in obj["inputs"]["trials"]}
    if "NCT04136184" not in trials:
        sys.exit("REFUSED: NEURO-TTRansform is not on this object.")

    t = trials["NCT04136184"]
    labels = [(a.get("label"), a.get("role")) for a in t.get("arms") or []]
    if not any("Inotersen" in str(l) and r == "treatment" for l, r in labels):
        sys.exit("REFUSED: NCT04136184's arms are not the reversal this script was written "
                 "against (%r). Re-read before writing." % labels)

    t["registration_read_%s" % STAMP] = {
        "source": "ClinicalTrials.gov API v2, NCT04136184",
        "read_utc": TODAY,
        "brief_title": ("NEURO-TTRansform: A Study to Evaluate the Efficacy and Safety of "
                        "Eplontersen (Formerly Known as ION-682884, IONIS-TTR-LRx and "
                        "AKCEA-TTR-LRx) in Participants With Hereditary "
                        "Transthyretin-Mediated Amyloid Polyneuropathy"),
        "interventions": ["Inotersen", "Eplontersen"],
        "THE_ARMS_ON_THIS_OBJECT_ARE_REVERSED": (
            "This object records Inotersen as the TREATMENT arm and Eplontersen as the "
            "CONTROL. The registration is unambiguous the other way: eplontersen is the "
            "experimental agent -- it is in the title -- and the detailed description says "
            "'Participants included in the INOTERSEN REFERENCE ARM crossed over to "
            "eplontersen at Week 37'. ESTABLISHED FROM THE REGISTRATION, NOT INFERRED FROM "
            "THE DRUG NAMES. The labels are NOT corrected here: correcting a randomised "
            "contrast is a change to what the object says the trial did, and the value "
            "stored is not that contrast anyway (below)."),
        "AND_THE_STORED_EFFECT_IS_NOT_THE_RANDOMISED_CONTRAST": (
            "The primary outcome's own description on the registry, verbatim: 'As "
            "pre-specified in the protocol, the efficacy of eplontersen was to be assessed "
            "by comparing participants enrolled in the eplontersen arm only with the "
            "external placebo group. There was no statistical comparison planned between "
            "the inotersen arm and the eplontersen-treated/external placebo group arms.' "
            "The external placebo group is the placebo cohort of NEURO-TTR, NCT01737398 -- "
            "A DIFFERENT TRIAL. So the value this review pools is a NON-RANDOMISED "
            "comparison against a historical control, and the randomised comparison this "
            "trial made has no planned statistical test at all."),
        "quote_primary_outcome": (
            "Change From Baseline in Modified Neuropathy Impairment Score Plus 7 (mNIS+7) "
            "at Week 66"),
        "url": "https://clinicaltrials.gov/study/NCT04136184",
    }

    blk["THE_POOL_IS_REFERRED_%s" % STAMP] = {
        "state": "REFERRED, NOT WITHDRAWN",
        "primary_defect": "UNIT OF ANALYSIS -- the three rows are not the same kind of comparison",
        "what_is_wrong": (
            "APOLLO contributes patisiran against its OWN randomised placebo. HELIOS-A "
            "contributes vutrisiran against APOLLO's placebo, an EXTERNAL control. "
            "NEURO-TTRansform contributes eplontersen against NEURO-TTR's placebo, a "
            "second external control -- and its arms are recorded on this object with "
            "inotersen as the treatment, which the registration contradicts. TWO OF THREE "
            "POOLED VALUES ARE NON-RANDOMISED EXTERNAL-CONTROL COMPARISONS RECORDED AS "
            "RANDOMISED ARM CONTRASTS, and PATISIRAN IS THE INTERVENTION IN ONE ROW AND THE "
            "COMPARATOR IN ANOTHER inside a single pooled number."),
        "why_this_is_not_a_framing_argument": (
            "A published network meta-analysis of this exact question exists -- Duarte et "
            "al. 2026, six trials, n=989, mNIS+7 as a primary outcome -- and it separates "
            "the drugs rather than pooling them, reporting that vutrisiran and patisiran "
            "improved compared with eplontersen and inotersen. WHETHER TO POOL ACROSS DRUGS "
            "IS A METHOD ARGUMENT AND REASONABLE PEOPLE DIFFER. Whether one number may "
            "contain a drug as both intervention and comparator is not."),
        "what_did_not_catch_it": (
            "`estimand_established` is TRUE here and correctly so -- all three measure "
            "change from baseline in mNIS+7, the same instrument and construct, with the "
            "timepoint difference stated. I-squared is 88.1%%, the signal a reader is "
            "taught to distrust, and it was live on the page. A TOPIC CAN CARRY AN "
            "ESTABLISHED ESTIMAND, A VISIBLE I-SQUARED AND A COMPARATOR SET THAT MAKES THE "
            "POOL MEANINGLESS. `estimand_established` CERTIFIES THE MEASUREMENT AND IS BEING "
            "READ AS THOUGH IT CERTIFIES THE CONTRAST."),
        "what_would_make_a_pool_defensible": (
            "Restricting to trials contributing a randomised comparison against a "
            "concurrent control on this instrument -- which on this trial set is APOLLO "
            "alone, k=1 -- or moving to the network the published literature already uses. "
            "Both are decisions, not relabellings."),
        "not_withdrawn_because": (
            "Withdrawing a published estimate is a published-number decision and belongs to "
            "Mahmood. The finding is complete and stated; the estimate is unchanged."),
    }
    blk["estimand_established_certifies_the_measurement_not_the_contrast_%s" % STAMP] = (
        "READ THIS BEFORE READING `estimand_established: true` ABOVE. It records that every "
        "contributing trial measures the SAME QUANTITY. It records NOTHING about whether "
        "they measure it against the same KIND OF COMPARATOR, and on this object they do "
        "not. The two questions were never separated, and every topic passing estimand "
        "establishment inherits the gap.")

    obj.setdefault("display_change_announced", []).append({
        "date": TODAY,
        "change": "the pool is referred: its three rows are not the same kind of comparison",
        "values_moved": "NONE -- the estimate is unchanged and is not withdrawn here",
        "what_changed": ("NEURO-TTRansform's registration was READ and written onto the "
                         "object. Its arms are recorded here with inotersen as the "
                         "treatment; the registration says eplontersen is the experimental "
                         "agent. And its stored effect is against an EXTERNAL placebo from "
                         "NCT01737398, not against its randomised comparator."),
        "why": ("A pooled estimate that contains a drug as both intervention and comparator "
                "is not estimating one quantity, and no framing defends it. Found while "
                "building a published comparison, which could not honestly be built on top "
                "of it."),
    })

    print("attr-pn: registration read, pool referred, estimand/contrast gap named")
    if dry:
        print("DRY RUN -- pass --apply to write")
        return
    with io.open(OBJ, "rb") as fh:
        raw = fh.read()
    nl = "\r\n" if b"\r\n" in raw.split(b"\n", 3)[0] + b"\n" else "\n"
    with io.open(OBJ, "w", encoding="utf-8", newline=nl) as fh:
        json.dump(obj, fh, indent=1, ensure_ascii=False)
        fh.write("\n")
    print("wrote %s" % OBJ)


if __name__ == "__main__":
    main()
