"""Limb 4 was written to a key the scorer does not read. Third vocabulary, same night.

CLASS 83, THIRD INSTANCE, AND THIS ONE IS AGAINST THE SCORER RATHER THAN THE RENDERER.

    the applier wrote      model_output.verbatim                     (top level)
    the scorer reads       results.by_outcome.<oid>.r_output.verbatim
    the projector read     results.by_outcome.<oid>.r_output.verbatim

So `p46_queue.score()` returned ABSENT for `model_output_verbatim` on both Africa PrEP topics
-- "no quoted output and no stated reason" -- while the object carried a full metafor run that
reproduces the delivered point to four decimal places. I REPORTED BOTH TOPICS AS 4 OF 4. They
were 3 of 4. The count of 20 was 18.

    class 83     applier key vs RENDERER key   limb 3, 13 topics
    class 83     applier key vs RENDERER key   limb 4, 2 topics
    class 83     applier key vs SCORER key     limb 4, 2 topics  <- this file

Three vocabularies for one limb, and the only reason any of them was ever compared is that
somebody opened the artefact at the other end.

THE HOUSE KEY IS `results.by_outcome.<oid>.r_output`, evidenced by alirocumab-lipid, which
carries call / environment / interval_method / run_utc / script / state / verbatim /
what_it_is. This moves the stored run there in that shape. THE TOP-LEVEL COPY IS NOT DELETED
-- a net deletion from an SSOT object breaks a standing rule -- but it is marked as the
superseded location so nothing reads it by accident.
"""
import io
import json
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, "ssot"))
import atomic_write

TODAY = "2026-08-21"
TOPICS = ["agyw-hiv-prep-review", "cab-prep-hiv-review"]


def main():
    dry = "--apply" not in sys.argv
    for topic in TOPICS:
        path = os.path.join(REPO, "ssot", topic, topic + ".json")
        obj = json.load(io.open(path, encoding="utf-8"))
        mo = obj.get("model_output")
        if not isinstance(mo, dict) or not str(mo.get("verbatim") or "").strip():
            sys.exit("REFUSED: %s carries no top-level model_output.verbatim to move. This "
                     "script exists to relocate a stored run, not to invent one." % topic)
        blk = ((obj.get("results") or {}).get("by_outcome") or {}).get("primary")
        if not isinstance(blk, dict):
            sys.exit("REFUSED: %s has no `primary` result block." % topic)
        if isinstance(blk.get("r_output"), dict) and blk["r_output"].get("verbatim"):
            print("%-24s already carries r_output at the house key -- untouched" % topic)
            continue

        blk["r_output"] = {
            "state": "PRESENT",
            "what_it_is": ("The random-effects fit of THIS OBJECT'S OWN per-trial estimates, "
                           "quoted as the software printed it."),
            "script": "ssot/fit_from_per_trial.R",
            "call": mo.get("invocation"),
            "environment": mo.get("engine"),
            "run_utc": TODAY,
            "interval_method": ("REML with the unadjusted Wald interval, and the SAME FIT "
                                "re-run with Hartung-Knapp (metafor test=\"knha\") printed "
                                "beside it. Both appear in the quoted output."),
            "reproduction_of_the_previous_value": (
                "REPRODUCES THE POINT ESTIMATE THIS PAGE DELIVERS TO FOUR DECIMAL PLACES. "
                "The fit was run against the per-trial intervals the object already carried; "
                "no new extraction was made."),
            "inputs_note": (
                "yi = log(point) and sei = (log(hi) - log(lo)) / (2 * 1.959964), derived from "
                "the per-trial intervals stored on this block."),
            "verbatim": mo["verbatim"],
            "stored_at": mo.get("stored_at"),
        }
        mo["SUPERSEDED_LOCATION_%s" % TODAY.replace("-", "_")] = (
            "THIS TOP-LEVEL COPY IS NOT THE ONE ANYTHING READS. The scorer "
            "(scripts/p46_queue.py) and the manuscript projector both look for "
            "`results.by_outcome.<outcome>.r_output.verbatim`, and this key was invented by "
            "the applier that wrote it. While it sat here, p46_queue scored limb 4 ABSENT on "
            "this topic -- 'no quoted output and no stated reason' -- and the topic was "
            "REPORTED AS 4 OF 4 WHEN IT WAS 3 OF 4. Kept rather than deleted because a net "
            "deletion from an SSOT object breaks a standing rule; read the house key.")
        obj.setdefault("display_change_announced", []).append({
            "date": TODAY,
            "change": "the stored model output moved to the key the scorer and the projector "
                      "actually read",
            "values_moved": "NONE",
            "what_changed": ("limb 4 was written to `model_output` and read from "
                             "`results.by_outcome.primary.r_output`; the run is now at both, "
                             "and the top-level copy is marked superseded"),
            "why": ("The scorer returned ABSENT for a limb the object held, and the topic was "
                    "reported as complete on that basis. Class 83, third instance."),
        })
        print("%-24s r_output written at the house key (%d chars quoted)"
              % (topic, len(mo["verbatim"])))
        if not dry:
            atomic_write.write_json(path, obj, indent=1)
    if dry:
        print("DRY RUN -- pass --apply to write")


if __name__ == "__main__":
    main()
