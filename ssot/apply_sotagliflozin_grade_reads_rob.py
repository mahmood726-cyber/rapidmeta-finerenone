"""P19: the RoB assessment must reach the GRADE domain that reads it, in the same pass.

BEFORE THIS, on both pooled outcomes:

    grade.certainty_derivation = "start high; risk_of_bias serious (-1), imprecision
                                  serious (-1); total -2 -> low"
    grade.risk_of_bias         = null
    grade.imprecision          = null
    grade.inconsistency        = null

The derivation NAMES two domains as the reason for the rating and the domain fields hold
nothing. That is the shape this project keeps meeting: a summary and a detail that do not
disagree because only one of them exists. A reader cannot check "risk_of_bias serious"
against anything, and until today neither could we -- there was no risk-of-bias assessment
on this object at all.

There is one now, and it says something specific: THREE OF THE FOUR RESULTS ARE HIGH on
RoB 2 domain 5. So the domain field is filled from it, with the evidence named.

THE CERTAINTY LEVEL IS NOT CHANGED, AND THAT IS A DECISION RATHER THAN AN OMISSION.

The rating already reads risk_of_bias serious (-1) and lands at LOW. The new assessment
supports that -1 rather than contradicting it. A case exists for -2 on hfcv_first
specifically -- BOTH contributing results are HIGH there, and neither trial ever
registered a time-to-first-event analysis, so the whole weight of that pool rests on
results selected after the fact. GRADE cautions against mechanical downgrading, moving a
published certainty from LOW to VERY LOW is a judgement rather than a computation, and
this script promotes evidence into a rating without making the rating for anyone. THE
CASE IS WRITTEN ONTO THE OBJECT so it is a decision waiting rather than a thing nobody
noticed.
"""
import io
import json
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOPIC = "sotagliflozin-hf"
TODAY = "2026-08-20"
OBJ = os.path.join(REPO, "ssot", TOPIC, TOPIC + ".json")

HB = "Cochrane Handbook 6.5 chapter 14 (GRADE); risk of bias per chapter 8."


def main():
    dry = "--apply" not in sys.argv
    obj = json.load(io.open(OBJ, encoding="utf-8"))
    rob = obj.get("risk_of_bias")
    if not isinstance(rob, dict) or not rob.get("by_outcome"):
        sys.exit("REFUSED: no risk_of_bias on this object. This script promotes an "
                 "assessment into GRADE and there is nothing to promote.")
    before = json.dumps(obj, sort_keys=True)
    touched = 0

    for oid in ("hfcv_total", "hfcv_first"):
        blk = obj["results"]["by_outcome"][oid]
        g = blk.get("grade")
        if not isinstance(g, dict):
            sys.exit("REFUSED: %s has no grade block." % oid)
        results = rob["by_outcome"][oid]
        highs = [nct for nct, r in results.items() if r["overall"] == "HIGH"]
        d5 = {nct: r["domains"]["D5_selection_of_reported_result"]["judgement"]
              for nct, r in results.items()}
        if g.get("risk_of_bias") is not None:
            sys.exit("REFUSED: %s.grade.risk_of_bias is already populated." % oid)

        g["risk_of_bias"] = {
            "rated_down": 1,
            "severity": "serious",
            "unchanged_from": ("the rating recorded before %s, which already read "
                               "'risk_of_bias serious (-1)' with no domain detail behind "
                               "it" % TODAY),
            "now_supported_by": (
                "A RoB 2 assessment of every result contributing to this pool, added "
                "%s. %d of %d results are HIGH overall, all of them on domain 5, "
                "selection of the reported result. Per-result domain-5 judgements: %s."
                % (TODAY, len(highs), len(results),
                   ", ".join("%s (%s) %s" % (results[n]["trial"], n, j)
                             for n, j in sorted(d5.items())))),
            "reason": (
                "The results this pool is built from were selected from among more "
                "analyses than were pre-specified. SCORED's primary endpoint was changed "
                "during the trial; neither trial registered a time-to-first-event "
                "analysis. Domains 1 to 3 are NO_INFORMATION on every result, which is a "
                "limit of this review's retrieval and is stated as one -- it is not "
                "counted as evidence of bias and it is not counted as evidence of its "
                "absence."),
            "why_not_two_levels": (
                "GRADE cautions against mechanical downgrading, and the -1 already stood "
                "before this assessment existed. The assessment SUPPORTS that level rather "
                "than forcing a further step."
                + ("  BUT SEE THE FLAG BELOW: on this outcome the case for -2 is real."
                   if oid == "hfcv_first" else
                   "  On this outcome the strongest contributing result -- SOLOIST-WHF's, "
                   "which is its registered primary word for word -- is LOW on domain 5, "
                   "so the pool is not uniformly at high risk and -1 is the right step.")),
            "evidence": "risk_of_bias.by_outcome.%s" % oid,
            "authority": HB,
        }
        if oid == "hfcv_first":
            g["risk_of_bias"]["A_DECISION_WAITING_%s" % TODAY.replace("-", "_")] = (
                "THE CASE FOR RATING THIS OUTCOME DOWN TWO LEVELS, TO VERY LOW, AND WHY IT "
                "WAS NOT TAKEN BY A SCRIPT. Unlike hfcv_total, BOTH contributing results "
                "are HIGH on domain 5 here, and the reason is the same on both: NEITHER "
                "TRIAL EVER REGISTERED A TIME-TO-FIRST-EVENT ANALYSIS. Both values come "
                "from the FDA integrated review. The entire weight of this pool therefore "
                "rests on analyses added to the results report after the fact, which is "
                "the situation Handbook 8.7 describes and a defensible reading of 'very "
                "serious'. Against that: both trials are large, double-blind and "
                "placebo-controlled; the first-event estimate agrees in direction and "
                "significance with the total-event one on the same trials; and the "
                "regulator, not the sponsor, is the source. MOVING A PUBLISHED CERTAINTY "
                "FROM LOW TO VERY LOW IS A JUDGEMENT, NOT A COMPUTATION. It is recorded "
                "here so it is a decision waiting rather than something nobody noticed.")
        g["certainty_rechecked_%s" % TODAY.replace("-", "_")] = (
            "Re-read against the risk-of-bias assessment added on %s. The certainty stands "
            "at %r and its derivation is unchanged: %s. What changed is that the "
            "risk_of_bias domain now HAS evidence behind it, where before it named a "
            "severity with an empty field beside it."
            % (TODAY, g.get("certainty"), g.get("certainty_derivation")))
        touched += 1

    obj.setdefault("display_change_announced", []).append({
        "date": TODAY,
        "change": "the risk-of-bias assessment promoted into the GRADE domain that reads it",
        "values_moved": "NONE -- no certainty rating changes and no estimate moves",
        "what_changed": (
            "`grade.risk_of_bias` was null on both pooled outcomes while "
            "`certainty_derivation` read 'risk_of_bias serious (-1)'. The domain is now "
            "filled from the per-result RoB 2 assessment added the same day, naming which "
            "results are HIGH and on which domain."),
        "why": (
            "P19: a promotion must reach every derived block in one pass. A GRADE domain "
            "that names a severity with nothing behind it cannot be checked by a reader, "
            "and until today could not be checked by us either -- there was no assessment "
            "on this object."),
        "what_was_deliberately_not_changed": (
            "The certainty level on hfcv_first. Both of its contributing results are HIGH "
            "on domain 5 and a case for VERY LOW exists; it is written onto the object "
            "under grade.risk_of_bias.A_DECISION_WAITING_%s rather than taken by a script."
            % TODAY.replace("-", "_")),
    })

    if touched != 2:
        sys.exit("REFUSED: touched %d grade blocks, expected 2." % touched)
    if json.dumps(obj, sort_keys=True) == before:
        sys.exit("REFUSED: the object is unchanged.")
    print("promoted the RoB assessment into %d GRADE risk_of_bias domain(s)" % touched)
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
