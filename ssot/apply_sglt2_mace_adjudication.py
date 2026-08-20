"""sglt2-mace-cvot-review: the two trials do not share an endpoint, and the object says so.

ESTABLISHED FROM BOTH REGISTRATIONS ON 2026-08-20, VERBATIM, NOT INFERRED.

  EMPA-REG OUTCOME, NCT01131676, ONE primary:
      "Time to the First Occurrence of Any of the Following Adjudicated Components of the
       Primary Composite Endpoint (3-point MACE): CV Death (Including Fatal Stroke and
       Fatal MI), Non-fatal MI (Excluding Silent MI), and NON-FATAL STROKE."

  DECLARE-TIMI 58, NCT01730534, TWO co-primaries:
      1. "Subjects Included in the Composite Endpoint of CV Death, MI or ISCHEMIC STROKE"
      2. "Subjects Included in the Composite Endpoint of CV Death or Hospitalization Due to
          Heart Failure."

FINDING 1 -- THE STROKE COMPONENT IS NOT THE SAME COMPONENT. EMPA-REG counts NON-FATAL
STROKE OF ANY TYPE. DECLARE counts ISCHAEMIC STROKE ONLY. Haemorrhagic stroke is inside one
composite and outside the other. These are two different endpoints that share a name, and
pooling them combines quantities that are not the same quantity.

FINDING 2 -- DECLARE HAS TWO EQUALLY-RANKED PRIMARIES AND THIS REVIEW SILENTLY USED ONE.
CV death or hospitalisation for heart failure is registered at the SAME RANK as the MACE
composite. Choosing between co-primaries is an analytic decision; making it without
recording it is the unrecorded-decision class. The other primary would answer a different
question and is not obviously the worse one -- it is the endpoint on which DECLARE's result
was positive.

FINDING 3 -- AND THE OBJECT ALREADY SAID SO, IN THE FIELD THAT NAMES THE ESTIMAND. The
outcome's `name` begins "Multiple trial-declared outcomes:" and then CONCATENATES FOUR
DIFFERENT REGISTERED TITLES separated by pipes. THE MISMATCH WAS WRITTEN INTO THE ESTIMAND'S
OWN NAME AND NOBODY READ IT. `estimand_established` is FALSE here and correctly so, and
`estimand_id_means` says "not recorded on the page this object was extracted from" -- three
fields, all honest, all saying the same thing, and the pool published anyway.

FINDING 4 -- AN ARM LABEL THAT NAMES A DOSE AND CARRIES THE WHOLE ARM'S COUNTS. EMPA-REG's
treatment arm is labelled "BI 10773 low dose" with 490 events in 4,687 participants. 4,687
is the POOLED empagliflozin arm across both doses; the low-dose arm alone is about half
that. The label names a subgroup and the numbers are the whole. Registry class 55, recorded
and NOT corrected -- correcting an arm is a published-number decision.

THE POOL IS REFERRED, NOT WITHDRAWN. Withdrawing a published estimate belongs to Mahmood.
The obstacle is IN THE EVIDENCE: the registrations state different endpoints, which is a
fact about the trials and not about what we have got round to reading.
"""
import io
import json
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, "ssot"))
import atomic_write

TOPIC = "sglt2-mace-cvot-review"
TODAY = "2026-08-20"
STAMP = TODAY.replace("-", "_")
OBJ = os.path.join(REPO, "ssot", TOPIC, TOPIC + ".json")

EMPA = ("Time to the First Occurrence of Any of the Following Adjudicated Components of "
        "the Primary Composite Endpoint (3-point MACE): CV Death (Including Fatal Stroke "
        "and Fatal MI), Non-fatal MI (Excluding Silent MI), and Non-fatal Stroke.")
DECL_1 = "Subjects Included in the Composite Endpoint of CV Death, MI or Ischemic Stroke"
DECL_2 = ("Subjects Included in the Composite Endpoint of CV Death or Hospitalization Due "
          "to Heart Failure.")


def main():
    dry = "--apply" not in sys.argv
    obj = json.load(io.open(OBJ, encoding="utf-8"))
    blk = obj["results"]["by_outcome"]["primary"]
    trials = dict((t.get("nct"), t) for t in obj["inputs"]["trials"])
    for nct in ("NCT01131676", "NCT01730534"):
        if nct not in trials:
            sys.exit("REFUSED: %s is not on this object." % nct)

    trials["NCT01131676"]["registration_read_%s" % STAMP] = {
        "source": "ClinicalTrials.gov API v2, NCT01131676, read %s" % TODAY,
        "primary_outcomes_registered": 1,
        "primary_verbatim": EMPA,
        "THE_STROKE_COMPONENT": (
            "NON-FATAL STROKE, of any type. The composite counts haemorrhagic stroke as "
            "well as ischaemic."),
    }
    trials["NCT01730534"]["registration_read_%s" % STAMP] = {
        "source": "ClinicalTrials.gov API v2, NCT01730534, read %s" % TODAY,
        "primary_outcomes_registered": 2,
        "primary_verbatim_1_used_by_this_review": DECL_1,
        "primary_verbatim_2_NOT_used_and_not_recorded": DECL_2,
        "THE_STROKE_COMPONENT": (
            "ISCHEMIC STROKE ONLY. Haemorrhagic stroke is NOT in this composite, and it IS "
            "in EMPA-REG's."),
        "AND_THIS_TRIAL_HAS_TWO_CO_PRIMARIES": (
            "CV death or hospitalisation for heart failure is registered at the SAME RANK. "
            "This review used the MACE composite and recorded no reason. Choosing between "
            "co-primaries is an analytic decision and an unrecorded one is not a "
            "methodological choice, it is an accident that happens to have a direction."),
    }

    blk["THE_POOL_IS_REFERRED_%s" % STAMP] = {
        "state": "REFERRED, NOT WITHDRAWN",
        "obstacle": "IN THE EVIDENCE",
        "obstacle_means": (
            "The registrations state DIFFERENT ENDPOINTS. That is a fact about the trials, "
            "not about what this project has got round to reading. Nothing further we do "
            "makes these two composites the same composite."),
        "primary_defect": (
            "THE STROKE COMPONENT IS NOT THE SAME COMPONENT. EMPA-REG's 3-point MACE counts "
            "NON-FATAL STROKE OF ANY TYPE; DECLARE's counts ISCHEMIC STROKE ONLY. "
            "Haemorrhagic stroke is inside one composite and outside the other. Two "
            "different endpoints sharing a name."),
        "second_defect": (
            "DECLARE registers TWO co-primaries and this review silently used one. The "
            "other -- CV death or hospitalisation for heart failure -- is at the same rank "
            "and is the endpoint on which DECLARE was positive. An unrecorded selection "
            "among co-primaries is an unrecorded analytic decision."),
        "AND_THE_OBJECT_ALREADY_SAID_SO": (
            "The outcome's own `name` begins 'Multiple trial-declared outcomes:' and then "
            "CONCATENATES FOUR DIFFERENT REGISTERED TITLES separated by pipes. "
            "`estimand_established` is FALSE. `estimand_id_means` says 'not recorded on the "
            "page this object was extracted from'. THREE FIELDS, ALL HONEST, ALL SAYING THE "
            "SAME THING -- AND THE POOL PUBLISHED ANYWAY. The defect was never that the "
            "object hid this; it is that a published estimate did not have to answer to it."),
        "what_would_make_a_pool_defensible": (
            "Either restrict to a component set both trials share -- CV death and non-fatal "
            "MI, dropping stroke, which is a different and smaller question -- or pool "
            "DECLARE's second co-primary against a matching endpoint elsewhere. Both are "
            "decisions, not relabellings, and neither is made here."),
        "not_withdrawn_because": (
            "Withdrawing a published estimate is a published-number decision and belongs to "
            "Mahmood. The estimate is unchanged; the finding is complete and stated."),
    }

    obj.setdefault("display_change_announced", []).append({
        "date": TODAY,
        "change": "the pool is referred: the two trials do not share an endpoint",
        "values_moved": "NONE -- the estimate is unchanged and is not withdrawn here",
        "what_changed": (
            "Both registrations were READ and written onto the object. EMPA-REG counts "
            "non-fatal stroke of any type; DECLARE counts ischaemic stroke only. DECLARE "
            "also registers a SECOND co-primary this review neither used nor recorded."),
        "why": ("A composite that includes haemorrhagic stroke and one that excludes it are "
                "not the same endpoint, and the object's own outcome name already said "
                "'Multiple trial-declared outcomes' with four titles concatenated."),
    })

    print("sglt2-mace-cvot: both registrations read; pool REFERRED, obstacle IN THE EVIDENCE")
    if dry:
        print("DRY RUN -- pass --apply to write")
        return
    atomic_write.write_json(OBJ, obj, indent=1)
    print("wrote %s" % OBJ)


if __name__ == "__main__":
    main()
