"""ITEM 20, row 1 of 22: arni-hfref -- the flagship's three unread endpoint definitions.

WHAT THIS RECORDS, and it is not what was expected
    An earlier lane recorded `pool_uniformity.outcome_definition = ["identical",
    ...]` on this object. That is an ASSERTION about four trials. Three of the
    four trial rows carried no `outcome_definition` at all, so the assertion
    stood on nothing a reader could check, and the page said so on its face:
    three rows reading "No endpoint definition is recorded for this trial. Its
    effect was pooled without one."

    Reading the four registrations word for word confirms the assertion for
    THREE of the four trials and REFUTES the object's claim about the fourth.

    PARADIGM-HF and PARALLEL-HF register this composite as their PRIMARY.
    PARACHUTE-HF registers it as its FIRST SECONDARY. Both facts were already
    claimed by the object and both are now confirmed from the registry text.

    ANSWER-HF DOES NOT REGISTER THIS ENDPOINT AT ANY RANK. NCT04853758 carries
    two primary outcomes (change in LVEF; a four-level hierarchical win ratio)
    and eighteen secondary outcomes, and none of the twenty is a first-event
    union of cardiovascular death and heart-failure hospitalisation. The object
    recorded its rank as "a secondary endpoint" and that is FALSE.

WHAT THIS DELIBERATELY DOES NOT DO
    It does not remove ANSWER-HF and it does not change one published number.
    Removing it would move the pooled hazard ratio from 0.8715 (0.7461-1.0181),
    which crosses one, to 0.8333 (0.7473-0.9292), which does not -- a null
    converted into a positive result by dropping the trial that disagrees. A
    withdrawal needs the same evidence as a claim. What an unregistered endpoint
    justifies is DISCLOSURE and a risk-of-bias entry, not deletion; and whether
    an unregistered publication-only endpoint should be ELIGIBLE at all is an
    eligibility-rule change, which is parked, not decided here.

USAGE  python scripts/item20_arni_endpoint_definitions.py
"""
from __future__ import annotations
import io
import json
import os
import sys

if __name__ == "__main__":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
OBJ = os.path.join(ROOT, "ssot", "arni-hfref", "arni-hfref.json")
OID = "cvdeath_or_hfh_first"
READ = "2026-08-18"

DEFS = {
    "paradigm-hf": {
        "outcome_definition": (
            "Number of Participants That Had First Occurrence of the Composite "
            "Endpoint, Which is Defined as Either Cardiovascular (CV) Death or "
            "Heart Failure (HF) Hospitalization"),
        "outcome_definition_source": {
            "description_verbatim": (
                "Number of participants that had first occurrence of the composite "
                "endpoint, which is defined as either CV death or HF hospitalization "
                "due to HF."),
            "time_frame": "up to 51 months",
            "endpoint_rank": "PRIMARY",
            "source": "registry",
            "source_field": "protocolSection.outcomesModule.primaryOutcomes[0].measure",
            "source_url": "https://clinicaltrials.gov/study/NCT01035255",
            "read_utc": READ,
            "agrees_with_the_others": (
                "Cardiovascular death or heart-failure hospitalisation, counted at "
                "the FIRST occurrence. The registry's own title says “First "
                "Occurrence” in words, so this row establishes the first-event "
                "structure of the pooled estimand rather than assuming it. Identical "
                "in components and in first-event structure to PARALLEL-HF and to "
                "PARACHUTE-HF's first secondary. The row previously stood on a "
                "publication sentence, which happened to say the same thing; the "
                "registry says it in the record that fixes what was counted."),
        },
    },
    "parachute-hf": {
        "outcome_definition": (
            "Percentage of Participants With First Hospitalization Due to Heart "
            "Failure or Death From Cardiovascular Causes"),
        "outcome_definition_source": {
            "description_verbatim": (
                "NO DESCRIPTION IS RECORDED IN THIS REGISTRY FIELD. The registration "
                "carries a description for its primary win-ratio endpoint and none "
                "for this secondary. The title and the time frame are the whole of "
                "what the registry states, and they are quoted here in full rather "
                "than supplemented from the publication."),
            "time_frame": (
                "From the date of randomization to the first occurrence (total follow "
                "up time up to approximately 36 months)"),
            "endpoint_rank": "SECONDARY (the first of six secondary outcomes)",
            "source": "registry",
            "source_field": "protocolSection.outcomesModule.secondaryOutcomes[0].measure",
            "source_url": "https://clinicaltrials.gov/study/NCT04023227",
            "read_utc": READ,
            "agrees_with_the_others": (
                "Cardiovascular death or heart-failure hospitalisation, counted to "
                "the first occurrence -- which the time frame states in words. Same "
                "components and same first-event structure as PARADIGM-HF and "
                "PARALLEL-HF. The registry's MEASURE is a percentage of participants "
                "and this object stores a hazard ratio taken from the publication; "
                "those are two analyses of the same registered endpoint, not two "
                "endpoints. The registry's posted results give 33.5% against 36.7%, "
                "which is 155/462 and 169/460 -- the counts this object already "
                "held, confirmed digit for digit against a source it had not used."),
            "registry_results_confirm_the_stored_counts": (
                "resultsSection outcome “Percentage of Participants With First "
                "Hospitalization Due to Heart Failure or Death From Cardiovascular "
                "Causes”: 33.5 in the sacubitril/valsartan group, 36.7 in the "
                "enalapril group. 155/462 = 33.55% and 169/460 = 36.74%. The stored "
                "arm sizes and event counts are the registry's own."),
        },
    },
    "answer-hf": {
        "outcome_definition": (
            "NOT REGISTERED. NCT04853758 registers no outcome measure -- primary, "
            "secondary or other -- that is a first-event union of cardiovascular "
            "death and heart-failure hospitalisation. The quantity this object "
            "pools from this trial exists only in the publication."),
        "outcome_definition_source": {
            "description_verbatim": (
                "There is no field to quote. The registration's TWO primary outcome "
                "measures are “Change of left ventricular ejection fraction "
                "(LVEF)” and “Win Ratio Analysis”, the latter "
                "described as “Hierarchical composite analysis composed of: 1. "
                "Time to cardiovascular death; 2. Time to first heart failure "
                "hospitalization; 3. Relative change in NT-proBNP from baseline to "
                "final visit; 4. Relative change in left ventricular ejection "
                "fraction from baseline to final visit”. Its EIGHTEEN secondary "
                "outcome measures are Holter, echocardiographic, functional-class and "
                "biomarker measures: premature ventricular beats (count and "
                "percentage), ventricular arrhythmia density, sustained ventricular "
                "tachycardia rate, NYHA class, six ventricular-remodelling "
                "measurements, urea, creatinine, potassium, sodium, systemic "
                "cytokines, microRNA and NT-proBNP. There are no “other” "
                "outcome measures. None of the twenty is the endpoint pooled here."),
            "time_frame": "not applicable -- the endpoint is not registered",
            "endpoint_rank": "NOT REGISTERED AT ANY RANK",
            "source": "registry",
            "source_field": (
                "protocolSection.outcomesModule -- primaryOutcomes (2), "
                "secondaryOutcomes (18), otherOutcomes (0), enumerated in full and "
                "none matching"),
            "source_url": "https://clinicaltrials.gov/study/NCT04853758",
            "read_utc": READ,
            "registry_state_when_read": (
                "overallStatus UNKNOWN, hasResults false, enrolment 200 (ESTIMATED), "
                "last update 2024-04-03. No results are posted, so the registry "
                "cannot be asked for this trial's counts the way PARACHUTE-HF's were."),
            "agrees_with_the_others": (
                "IT CANNOT BE ASKED TO. The other three trials' endpoint definitions "
                "agree with each other in the registry; this one has no registry "
                "definition to agree or disagree. The publication's Table 2 row is "
                "“Cardiovascular death and heart failure hospitalization 12/95 "
                "(12.6) 8/95 (8.4) 1.83 (0.72-4.67) 0.205”, and the row is a "
                "first-event UNION despite the caption's “and”: Table 2's "
                "own arithmetic gives cardiovascular death 7 plus heart-failure "
                "hospitalisation 7 against a composite of 12, so two patients had "
                "both and are counted once. The COMPONENTS therefore match the other "
                "three and the STRUCTURE matches them. What does not match is the "
                "status of the endpoint: theirs were fixed before the data, this one "
                "was not."),
            "what_this_costs_the_pool": (
                "This is a selective-reporting exposure, not an estimand mismatch. "
                "An endpoint absent from the registration cannot be shown to have "
                "been specified before the results were seen, and the protection "
                "every other row in this table has, this row does not. It is carried "
                "into risk of bias and stated on the face of the page. It is NOT "
                "treated as grounds for removing the trial: removing it moves the "
                "pooled hazard ratio from 0.8715 (0.7461-1.0181) to 0.8333 (0.7473-"
                "0.9292), turning a result that crosses one into one that does not. "
                "Dropping the only trial that disagrees, on a defect that argues for "
                "disclosure, would manufacture the positive finding this review does "
                "not have."),
        },
    },
}

RANK_FIX = {
    "answer-hf": (
        "NOT REGISTERED AT ANY RANK. NCT04853758 registers two primary outcomes "
        "-- change in left ventricular ejection fraction, and a four-level "
        "hierarchical win ratio -- and eighteen secondary outcomes, none of which "
        "is this composite. The endpoint pooled here appears only in the "
        "publication. The object previously recorded this row as “a secondary "
        "endpoint”, which the registration refutes."),
}

UNIFORMITY = {
    "effect_measure": [
        "identical",
        "All FOUR report a hazard ratio for the time to a first event of the same "
        "composite. No conversion is performed and none would be valid: the trials "
        "excluded from this pool are excluded largely because their quantities "
        "cannot be converted into this one. This row read “all three” "
        "until 2026-08-18, when the pool had been k=4 for a day; the whole of this "
        "table described the pool as it stood before ANSWER-HF was resolved into "
        "it, which is the table that justifies the pool describing a different "
        "pool from the one published.",
    ],
    "comparator": [
        "identical",
        "All four randomised against enalapril at a target of 10 mg twice daily. "
        "ANSWER-HF's own registration names enalapril as the comparator. This is "
        "the axis on which PARAGON-HF, PARAGLIDE-HF and PARADISE-MI fail, and it "
        "is checked rather than assumed.",
    ],
    "outcome_definition": [
        "identical in the three that register it",
        "Cardiovascular death or hospitalization for heart failure, whichever "
        "comes first. PARADIGM-HF's registered title says “First Occurrence "
        "of the Composite Endpoint, Which is Defined as Either Cardiovascular (CV) "
        "Death or Heart Failure (HF) Hospitalization”; PARALLEL-HF's "
        "registered description says “either cardiovascular (CV) death or "
        "heart failure (HF) hospitalization”; PARACHUTE-HF's registered "
        "secondary says “First Hospitalization Due to Heart Failure or Death "
        "From Cardiovascular Causes”, counted “to the first "
        "occurrence”. All three are read from the registry and quoted in full "
        "in the endpoint-definition table. ANSWER-HF REGISTERS NO SUCH ENDPOINT, "
        "so on that trial there is nothing to compare and this row does not claim "
        "there is. Its publication reports the same two components in the same "
        "first-event structure, which is agreement of the reported quantity and "
        "not of the registered one.",
    ],
    "endpoint_registered_in_its_own_trial": [
        "differs",
        "THREE OF THE FOUR TRIALS REGISTERED THIS ENDPOINT BEFORE THEY RAN; ONE DID "
        "NOT. PARADIGM-HF and PARALLEL-HF register it as their primary outcome and "
        "PARACHUTE-HF as the first of six secondaries. ANSWER-HF registers neither "
        "it nor anything equivalent, at any rank, and its registration is not "
        "silent by omission -- it declares twenty outcome measures and this is not "
        "among them. A quarter of this pool therefore has no protection against "
        "selective outcome reporting, and the trial concerned is the one whose "
        "estimate is furthest from the rest. It stays in, because removing it "
        "would convert a null into a positive result, and a withdrawal needs the "
        "same evidence as a claim.",
    ],
    "aetiology_of_heart_failure": [
        "differs",
        "PARACHUTE-HF and ANSWER-HF admitted only chronic Chagas cardiomyopathy, "
        "confirmed serologically at entry -- a distinct disease with a different "
        "natural history and a high burden of conduction disease. Neither "
        "PARADIGM-HF nor PARALLEL-HF restricted aetiology at all, so the pool "
        "crosses two narrow-aetiology trials with two unrestricted ones, and that "
        "is the most substantive thing it crosses. It is also HALF the pool rather "
        "than a third, which is what this row said before ANSWER-HF was counted "
        "into it. What the contributing trials' own sources say about their "
        "aetiology MIX differs in how much they say, and this row says only what "
        "they support: the EPAR records ischaemic cardiac disease as the primary "
        "cause of heart failure in the majority of PARADIGM-HF participants, and "
        "the staged sources for PARALLEL-HF characterise its population by "
        "ejection fraction and functional class without describing its aetiology "
        "mix at all. An earlier version of this row described both unrestricted "
        "trials as largely ischaemic or idiopathic; a review leg was right that "
        "the second half of that had no basis in anything staged, and it is the "
        "more serious kind of over-claim for sitting inside the table that "
        "justifies pooling across aetiology.",
    ],
    "ejection_fraction_ceiling": [
        "differs",
        "40% or less in PARADIGM-HF and PARACHUTE-HF; 35% or less in PARALLEL-HF; "
        "ANSWER-HF enrolled Chagas cardiomyopathy with reduced ejection fraction. "
        "All are within the reduced-ejection-fraction population the question "
        "fixes, and they are not the same entry criterion.",
    ],
    "blinding": [
        "differs",
        "PARADIGM-HF and PARALLEL-HF were double-blind. PARACHUTE-HF was "
        "OPEN-LABEL with blinded endpoint adjudication. Blinded adjudication "
        "protects the outcome ascertainment and does not protect the management "
        "decisions that lead to a hospitalization, so the difference is carried "
        "into the GRADE risk-of-bias domain rather than dismissed here.",
    ],
    "endpoint_rank_within_its_own_trial": [
        "differs",
        "This composite is the PRIMARY endpoint of PARADIGM-HF and of PARALLEL-HF. "
        "In PARACHUTE-HF it is the first SECONDARY endpoint, the primary there "
        "being a hierarchical composite analysed by win ratio. A trial is not "
        "powered for its secondary endpoints, and the pool crosses that. IN "
        "ANSWER-HF IT HAS NO RANK, because it is not registered: that trial's "
        "registered primaries are change in ejection fraction and a four-level "
        "hierarchical win ratio. “Unregistered” is a fourth state on "
        "this axis and not a third kind of secondary.",
    ],
    "follow_up_length": [
        "differs",
        "Medians of 27 months, 25.2 months and 33.9 months in the three trials "
        "that report one; ANSWER-HF's registered outcome window is 6 months, the "
        "shortest in the pool by a factor of four. PARADIGM-HF's follow-up ended "
        "early by prespecified rule when a boundary for overwhelming benefit was "
        "crossed, which is a different reason for a follow-up length than the "
        "others have. A composite counted to first event over 6 months and the "
        "same composite counted over 34 months are not the same exposure to risk, "
        "and this is the dimension on which the pool's shortest trial is also its "
        "most discrepant estimate.",
    ],
    "analysis_population": [
        "differs",
        "All four use the trial's own full analysis set. In PARACHUTE-HF and "
        "ANSWER-HF that equals the randomised total; in PARADIGM-HF and PARALLEL-HF "
        "it is smaller, and each cell shows the arithmetic from the randomised "
        "total rather than leaving the difference unexplained.",
    ],
}

ESTIMAND_POP = (
    "each trial's own full analysis set, which in two of the four is smaller than "
    "the randomised total for reasons the trial states and this object reproduces")


def main():
    with io.open(OBJ, encoding="utf-8") as fh:
        obj = json.load(fh)

    changed = []

    by_id = {t["id"]: t for t in obj["inputs"]["trials"]}
    for tid, payload in DEFS.items():
        bo = by_id[tid]["by_outcome"][OID]
        if bo.get("outcome_definition"):
            print("REFUSING to overwrite an existing definition on %s" % tid)
            return 1
        bo["outcome_definition"] = payload["outcome_definition"]
        bo["outcome_definition_source"] = payload["outcome_definition_source"]
        changed.append("definition recorded: %s" % tid)

    res = obj["results"]["by_outcome"][OID]
    for row in res["per_trial"]:
        fix = RANK_FIX.get(row.get("trial_id") or row.get("id"))
        if fix:
            row["endpoint_rank_in_its_own_trial_superseded"] = \
                row["endpoint_rank_in_its_own_trial"]
            row["endpoint_rank_in_its_own_trial"] = fix
            changed.append("rank corrected: %s" % (row.get("trial_id") or row.get("id")))

    old_uniformity = res["pool_uniformity"]
    res["pool_uniformity"] = UNIFORMITY
    res["pool_uniformity_superseded_2026_08_18"] = {
        "why": (
            "Every row of the previous table described THREE trials while the pool "
            "published FOUR. ANSWER-HF appeared in none of the nine rows. The table "
            "that justifies the pool was describing a different pool from the one on "
            "the page. Kept here so the change can be read rather than taken on "
            "trust; no pooled number changed."),
        "rows": old_uniformity,
    }
    changed.append("pool_uniformity rewritten k=3 -> k=4, one row added")

    est = obj["outcomes"][0]["estimand"]
    if "two of the three" in (est.get("analysis_population") or ""):
        est["analysis_population"] = ESTIMAND_POP
        changed.append("estimand.analysis_population: 'two of the three' -> 'two of the four'")

    with io.open(OBJ, "w", encoding="utf-8") as fh:
        json.dump(obj, fh, ensure_ascii=False, indent=1)
        fh.write("\n")

    for c in changed:
        print("  " + c)
    print("%d changes written to %s" % (len(changed), OBJ))
    return 0


if __name__ == "__main__":
    sys.exit(main())
