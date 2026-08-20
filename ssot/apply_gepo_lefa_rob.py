"""gepotidacin and lefamulin: risk of bias per result. P46 limb 1.

ESTABLISHED FROM THE REGISTRATIONS, ClinicalTrials.gov API v2, 2026-08-21. Identity before
judgement: every domain is scored against a field read on the registry, and where the
registry does not carry the field the domain is NO_INFORMATION rather than LOW.

    NCT04020341  EAGLE-2   n=1531  RANDOMIZED  masking DOUBLE [PARTICIPANT, INVESTIGATOR]
                 arms: Gepotidacin (experimental) | Nitrofurantoin (ACTIVE comparator)
                 TWO primary outcomes registered, both "Therapeutic Response (TR)"
    NCT04187144  EAGLE-3   n=1606  RANDOMIZED  masking DOUBLE [PARTICIPANT, INVESTIGATOR]
                 arms: Gepotidacin (experimental) | Nitrofurantoin (ACTIVE comparator)
                 TWO primary outcomes registered

    NCT02559310  LEAP 1    n=551   RANDOMIZED  masking QUADRUPLE
                 [PARTICIPANT, CARE_PROVIDER, INVESTIGATOR, OUTCOMES_ASSESSOR]
                 arms: Lefamulin | Moxifloxacin +/- Linezolid (ACTIVE comparator)
    NCT02813694  LEAP 2    n=738   RANDOMIZED  masking QUADRUPLE (same four roles)
                 arms: lefamulin | Moxifloxacin (ACTIVE comparator)

TWO DOMAINS SEPARATE THESE TOPICS AND BOTH ARE READ FROM THE REGISTRY, NOT ASSUMED.

D4, MEASUREMENT OF THE OUTCOME. Lefamulin's trials mask the OUTCOMES ASSESSOR; gepotidacin's
do not -- masking is DOUBLE, participant and investigator only. Gepotidacin's endpoint is a
COMBINED clinical AND microbiological therapeutic response, and the clinical half is a
judgement. An unmasked assessor has something to decide, so D4 is SOME_CONCERNS there and
LOW for lefamulin. THE JUDGEMENT RESTS ON THE ENDPOINT AND THE MASKED ROLES TOGETHER.

D5, SELECTION OF THE REPORTED RESULT. Each gepotidacin trial registers TWO primary outcomes,
both named "Therapeutic Response", and this review pools one without recording the choice --
the same shape as inclisiran's two co-primaries and DECLARE-TIMI 58's dropped one. Lefamulin
registers ONE primary, Early Clinical Response, and that is what is pooled.

AND A COMPARATOR DIFFERENCE THAT THE OBJECT ALREADY DISCLOSES. LEAP 1's comparator is
moxifloxacin WITH OR WITHOUT LINEZOLID and LEAP 2's is moxifloxacin alone. That is recorded
here as a fact of the registrations; this object's own question already states it, so it is
corroborated rather than newly found.
"""
import io
import json
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, "ssot"))
import atomic_write

TODAY = "2026-08-21"
STAMP = TODAY.replace("-", "_")

CEILING = {
    "statement": ("A domain that cannot be judged from the sources READ is NO_INFORMATION, "
                  "never LOW. Low-by-default asserts a fact; high-by-default invents a "
                  "defect. Overall is capped at SOME_CONCERNS wherever a domain is "
                  "NO_INFORMATION."),
    "shape_note": ("A DICT, NOT A STRING. paper_projector does ceil.get('statement'), so a "
                   "bare string raises AttributeError and the manuscript collapses to a "
                   "projector-failed banner -- registry class 70."),
}

D1 = {"judgement": "LOW", "basis": "REGISTRATION DESIGN MODULE, READ",
      "reason": "allocation is recorded as RANDOMIZED on the design module.",
      "what_is_NOT_established": (
          "The concealment MECHANISM is not on the registry and no publication was read. LOW "
          "is scored on the recorded allocation, not on a mechanism nobody here has seen.")}
D2 = {"judgement": "NO_INFORMATION",
      "basis": "NOT ESTABLISHED -- THE REGISTRY DOES NOT CARRY THE FIELD",
      "reason": ("Deviations from intended intervention and the analysis population actually "
                 "used are not on the registration. The exit is the trial reports, which "
                 "were not read.")}
D3 = {"judgement": "NO_INFORMATION",
      "basis": "NOT ESTABLISHED -- THE REGISTRY DOES NOT CARRY THE FIELD",
      "reason": ("Neither registration states how many participants were missing from the "
                 "analysed population or how they were handled.")}

SPEC = {
    "gepotidacin-urinary-tract-auto-full-review": {
        "outcome": "primary",
        "trials": {
            "NCT04020341": ("EAGLE-2", 1531),
            "NCT04187144": ("EAGLE-3", 1606),
        },
        "masking": "DOUBLE -- participant and investigator; THE OUTCOMES ASSESSOR IS NOT "
                   "AMONG THE MASKED ROLES",
        "result": ("therapeutic response, combined per-participant CLINICAL AND "
                   "MICROBIOLOGICAL response -- ONE OF TWO REGISTERED PRIMARY OUTCOMES"),
        "d4": {"judgement": "SOME_CONCERNS",
               "basis": "REGISTRATION DESIGN MODULE AND THE ENDPOINT'S NATURE",
               "reason": (
                   "The endpoint COMBINES a microbiological result with a CLINICAL response, "
                   "and the clinical half is a judgement. THE OUTCOMES ASSESSOR IS NOT MASKED "
                   "on either registration -- masking is DOUBLE, participant and investigator "
                   "-- so an unmasked assessor has something to decide. Not HIGH: nothing "
                   "read shows assessment differed by arm, and asserting that would be the "
                   "accusing-direction error.")},
        "d5": {"judgement": "SOME_CONCERNS",
               "basis": "REGISTRATION COMPARED WITH WHAT THIS OBJECT POOLS",
               "reason": (
                   "EACH TRIAL REGISTERS TWO PRIMARY OUTCOMES, both named 'Therapeutic "
                   "Response (TR)'. This review pools one and records no reason for the "
                   "choice. Same shape as inclisiran's two co-primaries. NOT HIGH: nothing "
                   "read shows the choice was made after seeing the data.")},
        "overall": "SOME_CONCERNS",
        "overall_reason": (
            "D4 and D5 SOME_CONCERNS; D2 and D3 NO_INFORMATION. Overall cannot be LOW while "
            "a domain is SOME_CONCERNS, and cannot be judged further while two are unread."),
    },
    "lefamulin-cabp-auto-full-review": {
        "outcome": "primary",
        "trials": {
            "NCT02559310": ("LEAP 1", 551),
            "NCT02813694": ("LEAP 2", 738),
        },
        "masking": "QUADRUPLE -- participant, care provider, investigator AND OUTCOMES "
                   "ASSESSOR",
        "result": "Early Clinical Response (ECR) -- THE SINGLE REGISTERED PRIMARY OUTCOME",
        "d4": {"judgement": "LOW",
               "basis": "REGISTRATION DESIGN MODULE, READ",
               "reason": (
                   "Masking is QUADRUPLE on both registrations and the OUTCOMES ASSESSOR IS "
                   "EXPLICITLY AMONG THE MASKED ROLES. Early clinical response is an "
                   "assessed judgement, so the masked assessor is what makes this LOW -- the "
                   "judgement rests on the masking, not on the endpoint being objective.")},
        "d5": {"judgement": "LOW",
               "basis": "REGISTRATION COMPARED WITH WHAT THIS OBJECT POOLS",
               "reason": (
                   "ONE primary outcome is registered on each trial -- Early Clinical "
                   "Response -- and that is the result pooled here. There is no set to "
                   "choose from, so the selection found on gepotidacin cannot arise.")},
        "overall": "SOME_CONCERNS",
        "overall_reason": (
            "D1, D4 and D5 LOW on read registrations; D2 and D3 NO_INFORMATION. Under RoB 2 "
            "an unjudgeable domain cannot yield LOW overall, and SOME_CONCERNS is the "
            "ceiling this project applies where a domain is unread rather than adverse."),
        "comparator_note": (
            "LEAP 1's comparator is moxifloxacin WITH OR WITHOUT LINEZOLID and LEAP 2's is "
            "moxifloxacin alone -- read from the registered arm groups. This object's own "
            "question already states it, so the registrations CORROBORATE a disclosure "
            "rather than revealing a new one."),
    },
}


def main():
    dry = "--apply" not in sys.argv
    for topic, spec in sorted(SPEC.items()):
        path = os.path.join(REPO, "ssot", topic, topic + ".json")
        obj = json.load(io.open(path, encoding="utf-8"))
        ncts = set(t.get("nct") for t in (obj.get("inputs") or {}).get("trials") or [])
        for n in spec["trials"]:
            if n not in ncts:
                sys.exit("REFUSED: %s not on %s (%r)" % (n, topic, sorted(ncts)))

        by_outcome = {spec["outcome"]: {}}
        for nct, (name, enrol) in sorted(spec["trials"].items()):
            by_outcome[spec["outcome"]][nct] = {
                "nct": nct, "trial": name, "registered_enrolment": enrol,
                "registered_masking": spec["masking"],
                "result_assessed": spec["result"],
                "domains": {
                    "D1_randomisation_process": D1,
                    "D2_deviations_from_intended_intervention": D2,
                    "D3_missing_outcome_data": D3,
                    "D4_measurement_of_the_outcome": spec["d4"],
                    "D5_selection_of_the_reported_result": spec["d5"],
                },
                "overall": spec["overall"],
                "overall_reason": spec["overall_reason"],
            }

        rob = {
            "tool": "RoB 2 (Cochrane risk-of-bias tool for randomized trials)",
            "assessed_utc": TODAY,
            "assessed_per": "RESULT, not trial -- Handbook 8.2",
            "by_outcome": by_outcome,
            "sources_read": [
                "ClinicalTrials.gov API v2 %s -- design module, arm groups and registered "
                "primary outcomes" % n for n in sorted(spec["trials"])],
            "sources_NOT_read": (
                "The trial publications. D2 and D3 are the domains that depend on them, and "
                "both are NO_INFORMATION for that reason."),
            "ceiling": CEILING,
            "ONE_ASSESSOR_ONLY": (
                "ASSESSED BY ONE ASSESSOR. Under the standing specification that risk of "
                "bias 2 must be complete and done by TWO AIs from different model families, "
                "THIS ASSESSMENT IS INCOMPLETE. It is recorded as such rather than presented "
                "as finished, and `rob2.assessors` is deliberately NOT written."),
        }
        if spec.get("comparator_note"):
            rob["comparator_read_from_the_registrations"] = spec["comparator_note"]

        atomic_write.merge_not_overwrite(obj, "risk_of_bias", rob, STAMP)
        obj.setdefault("display_change_announced", []).append({
            "date": TODAY,
            "change": "risk of bias assessed per result from the registrations (P46 limb 1)",
            "values_moved": "NONE",
            "what_changed": "%d results assessed; overall %s"
                            % (len(spec["trials"]), spec["overall"]),
            "why": "The limb was ABSENT.",
        })
        print("%-44s %d results, overall %s" % (topic, len(spec["trials"]), spec["overall"]))
        if not dry:
            atomic_write.write_json(path, obj, indent=1)
    if dry:
        print("DRY RUN -- pass --apply to write")


if __name__ == "__main__":
    main()
