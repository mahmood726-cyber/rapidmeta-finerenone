"""rosuvastatin-auto-full-review: the pool is over an estimand that does not exist.

NOT a published-comparison unit. This topic was on that queue and came off it, because a
published comparison compares THIS REVIEW'S ESTIMATE against the literature, and this
review does not have an estimate of a stated quantity.

WHAT THE OBJECT HELD BEFORE THIS. A pooled odds ratio of 0.6561 (0.484 to 0.8894) over
JUPITER and HOPE-3, with `estimand_established: False` and, as its reason,
"not recorded on the page this object was extracted from" -- which is the never-checked
state, written as though it were the checked-and-failed one. And the registered primary
outcome of one of its two trials WAS NOT ON THE OBJECT AT ALL.

WHAT WAS FETCHED, 2026-08-20, from ClinicalTrials.gov NCT00468923:

  HOPE-3 registers TWO CO-PRIMARY OUTCOMES.
    1. "The composite of; Cardiovascular death, non-fatal myocardial infarction,
        non-fatal stroke."
    2. "The composite of; cardiovascular death, resuscitated cardiac arrest, non-fatal
        myocardial infarction, non-fatal stroke, heart failure, arterial
        revascularizations"

  JUPITER (NCT00239681), already on the object, registers ONE:
    "Time to Major Cardiac Event (Cardiovascular Death, Stroke, Myocardial Infarction,
     Hospitalization Due to Unstable Angina or Arterial Revascularization)"

NEITHER HOPE-3 CO-PRIMARY IS JUPITER'S COMPOSITE, and the mismatch is not marginal:

  * JUPITER counts ANY stroke and ANY myocardial infarction; both HOPE-3 composites count
    NON-FATAL stroke and NON-FATAL myocardial infarction only.
  * JUPITER counts HOSPITALISATION FOR UNSTABLE ANGINA; neither HOPE-3 composite does.
  * HOPE-3's second composite counts RESUSCITATED CARDIAC ARREST and HEART FAILURE;
    JUPITER's does not.
  * HOPE-3's first composite is three components, JUPITER's is five, and HOPE-3's second
    is six. There is no ordering in which one contains the other.

AND HOPE-3 HAS POSTED NO RESULTS TO THE REGISTRY AT ALL -- `has_results: false` on the
API response. So the stored HOPE-3 effect, OR 0.7622 (0.6405 to 0.9070), did not come
from the registry, the object records it as "extractor recovery from the published page",
and the object cannot say WHICH of the two co-primaries it is a recovery of.

THIS IS THE SHARPEST FORM OF THE COMPOSITE PROBLEM THIS CORPUS HAS PRODUCED. Elsewhere
two definitions differ and a judgement is needed. Here ONE DEFINITION IS ABSENT WHILE THE
POOL EXISTS: the object publishes a pooled estimate over an outcome it does not hold the
definition of, on one of its two trials, and could not have checked because it never had
the text to check against.

WHAT THIS SCRIPT DOES AND DOES NOT DO. It records the finding, fetched and quoted, and
sets `estimand_established` to False WITH A REAL REASON in place of the never-checked
placeholder. IT DOES NOT WITHDRAW THE POOL. Withdrawal is a published-number decision on a
delivered artefact, and it is referred rather than taken -- with the note that the
delivered page is a legacy build that never rendered this pooled estimate, so nothing a
reader can see currently depends on it.
"""
import io
import json
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOPIC = "rosuvastatin-auto-full-review"
TODAY = "2026-08-20"
OBJ = os.path.join(REPO, "ssot", TOPIC, TOPIC + ".json")

HOPE3_PRIMARIES = [
    "The composite of; Cardiovascular death, non-fatal myocardial infarction, non-fatal stroke.",
    "The composite of; cardiovascular death, resuscitated cardiac arrest, non-fatal "
    "myocardial infarction, non-fatal stroke, heart failure, arterial revascularizations",
]
JUPITER_PRIMARY = ("Time to Major Cardiac Event (Cardiovascular Death, Stroke, Myocardial "
                   "Infarction, Hospitalization Due to Unstable Angina or Arterial "
                   "Revascularization)")


def main():
    dry = "--apply" not in sys.argv
    obj = json.load(io.open(OBJ, encoding="utf-8"))
    blk = obj["results"]["by_outcome"]["primary"]
    trials = {t["nct"]: t for t in obj["inputs"]["trials"]}
    if "NCT00468923" not in trials:
        sys.exit("REFUSED: HOPE-3 is not on this object; the finding does not apply.")
    h = trials["NCT00468923"]
    if h.get("registration_primary_counts") is not None:
        sys.exit("REFUSED: HOPE-3 already holds a registered primary; re-read before "
                 "writing, because this finding rests on its absence.")

    h["registered_primaries_fetched_%s" % TODAY.replace("-", "_")] = {
        "source": "ClinicalTrials.gov API v2, NCT00468923",
        "url": "https://clinicaltrials.gov/study/NCT00468923",
        "read_utc": TODAY,
        "co_primary_outcomes": HOPE3_PRIMARIES,
        "registry_has_results": False,
        "why_this_was_fetched": (
            "This object published a pooled estimate over HOPE-3 and JUPITER while holding "
            "NO registered primary outcome for HOPE-3. The definition was absent, not "
            "merely different, and it had to be fetched before anything else could be said "
            "about the pool."),
        "and_the_registry_posts_no_results": (
            "`has_results` is false on this registration, so the stored HOPE-3 effect -- OR "
            "0.7622 (0.6405 to 0.9070) -- cannot have come from the registry results "
            "section. The object records it as extractor recovery from the published page "
            "and cannot say WHICH of the two co-primaries it is a recovery of."),
    }

    blk["estimand_established"] = False
    blk["estimand_established_reason_%s" % TODAY.replace("-", "_")] = (
        "CHECKED ON %s AND FAILED, which is a different state from the "
        "'not recorded on the page this object was extracted from' this field carried "
        "before -- that was the NEVER-CHECKED state written as though it were a negative "
        "finding. It has now been checked. JUPITER registers a FIVE-component composite: "
        "%r. HOPE-3 registers TWO co-primaries, %r and %r. Neither is JUPITER's. JUPITER "
        "counts any stroke and any myocardial infarction where both HOPE-3 composites "
        "count non-fatal only; JUPITER counts hospitalisation for unstable angina and "
        "neither HOPE-3 composite does; HOPE-3's second adds resuscitated cardiac arrest "
        "and heart failure, which JUPITER's does not. Three, five and six components with "
        "no containment ordering between them."
        % (TODAY, JUPITER_PRIMARY, HOPE3_PRIMARIES[0], HOPE3_PRIMARIES[1]))
    blk["pool_uniformity"] = {
        "effect_measure": ["ESTABLISHED", "both stored as odds ratios derived from arm "
                           "counts, on the log scale"],
        "estimand": ["NOT ESTABLISHED, AND CHECKED", blk["estimand_established_reason_%s"
                                                        % TODAY.replace("-", "_")]],
        "superseded_%s" % TODAY.replace("-", "_"): (
            "This block previously read NOT ESTABLISHED with the reason 'not recorded on "
            "the page this object was extracted from' on both limbs -- the never-checked "
            "state. It has been checked."),
    }
    blk["THE_POOL_IS_REFERRED_%s" % TODAY.replace("-", "_")] = {
        "state": "REFERRED, NOT WITHDRAWN",
        "what_is_wrong": (
            "The pooled odds ratio 0.6561 (0.484 to 0.8894) averages JUPITER's five-component "
            "composite with one of HOPE-3's two co-primaries, and the object cannot say "
            "which. This is the estimand-mixing shape that caused sglt2-hf's k=4 pool to be "
            "withdrawn."),
        "why_it_is_referred_rather_than_withdrawn_here": (
            "Withdrawing a published estimate is a published-number decision and this pass "
            "was scoped to establish the estimand, not to take that decision. The finding "
            "is complete and stated; the decision is Mahmood's."),
        "what_a_reader_currently_sees": (
            "NOTHING. ROSUVASTATIN_AUTO_FULL_REVIEW.html is a legacy build that never "
            "rendered this pooled estimate -- established two ways on 2026-08-20, by "
            "building the object to a scratch path and comparing shape, and by probing the "
            "delivered bytes for the served number. So no reader currently depends on it, "
            "which sets the urgency without changing the correctness."),
        "what_would_make_a_pool_defensible": (
            "Restricting to a shared estimand. HOPE-3's FIRST co-primary -- cardiovascular "
            "death, non-fatal myocardial infarction, non-fatal stroke -- is a three-point "
            "MACE, and a JUPITER value for the same three components would have to be "
            "recovered from its publication rather than from its registered five-component "
            "primary. That is a real piece of work and it is not a re-labelling."),
    }

    obj.setdefault("display_change_announced", []).append({
        "date": TODAY,
        "change": "estimand checked and found not established; the pool is referred",
        "values_moved": "NONE -- the pooled estimate is unchanged and is not withdrawn here",
        "what_changed": (
            "HOPE-3's registered primary outcomes were FETCHED from ClinicalTrials.gov and "
            "written onto the object. It registers two co-primaries and neither matches "
            "JUPITER's five-component composite. `estimand_established` was already False "
            "but carried the never-checked placeholder as its reason; it now carries a "
            "checked one."),
        "why": (
            "This object published a pooled estimate over an outcome whose definition it "
            "did not hold for one of its two trials. A pool cannot be compared against the "
            "literature, or defended, while nobody can say what it estimates."),
    })

    print("HOPE-3 co-primaries written; estimand recorded as checked-and-failed; pool referred")
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
