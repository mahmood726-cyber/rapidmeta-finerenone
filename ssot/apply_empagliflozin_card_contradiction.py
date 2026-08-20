"""The card directly above the estimate said the estimand was not recorded.

FOUND BY BUILDING THE PAGE, AFTER THE OBJECT WAS CORRECT. The previous pass established
the estimand and wrote `results.by_outcome.primary.pool_uniformity.estimand =
["ESTABLISHED", ...]`. Building the page showed this, in the "What was measured" card
rendered IMMEDIATELY ABOVE the pooled estimate:

    Comparator   not recorded on the page this object was extracted from
    Estimand     not recorded on the page this object was extracted from -- random-effects

ssot/build_app_v2.py builds that card from `outcomes[].estimand.family` and
`outcomes[].comparator`, NOT from `results.by_outcome.<oid>.pool_uniformity`. Two fields,
one question, and the pass corrected the one the reader does not see. A reader met "the
estimand is not recorded" and then the estimate, on a topic whose object says the estimand
is established.

THE LESSON IS THE ONE FROM THIS MORNING, AT A DIFFERENT ADDRESS. 36 risk-of-bias
assessments were counted by P46 and rendered by nothing, because the counter and the
renderer read different keys. Here the counter and the renderer read different keys again
and the renderer won, because the renderer is what the reader gets. WRITE THE OBJECT, THEN
BUILD THE PAGE AND GREP IT -- asserting the write is not the test.

AND THE DISCLOSURE IS PULLED INTO THE CARD. The summary-measure limitation rendered ~1,700
characters after the first estimate, with only a pointer beside it. "A reader must not be
able to reach the estimate without meeting it" is not satisfied by a cross-reference, so
the operative sentence now sits in `heterogeneity_status`, which renders INSIDE the pooled
result card.
"""
import io
import json
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOPIC = "empagliflozin-hf-auto-full-review"
TODAY = "2026-08-20"
STAMP = TODAY.replace("-", "_")
OBJ = os.path.join(REPO, "ssot", TOPIC, TOPIC + ".json")
PLACEHOLDER = "not recorded on the page this object was extracted from"

KEY = ("AN ODDS RATIO OVER UNEQUAL FOLLOW-UP IS NOT A HAZARD RATIO and does not become one "
       "by being pooled")


def main():
    dry = "--apply" not in sys.argv
    obj = json.load(io.open(OBJ, encoding="utf-8"))
    blk = obj["results"]["by_outcome"]["primary"]
    if blk.get("estimand_established") is not True:
        sys.exit("REFUSED: the estimand is not established; this pass presumes it is.")
    # BY IDENTITY, NEVER BY POSITION. scripts/lint_primary_by_position.py refused the
    # first version of this file for reading obj["outcomes"][0], and it was right to:
    # element zero of an outcome collection is ADVANCE-2's SECONDARY and its three
    # companions' PRIMARY, and a pool built on it is wrong with nothing malformed
    # anywhere. This object happens to hold one outcome; that is not a reason to index
    # into it, because the next object this pattern is copied into will not.
    matches = [o for o in obj["outcomes"] if o.get("id") == "primary"]
    if len(matches) != 1:
        sys.exit("REFUSED: %d outcome(s) with id 'primary'; this pass edits exactly one "
                 "and will not guess which." % len(matches))
    out = matches[0]
    est = out["estimand"]
    changed = []

    if est.get("family") == PLACEHOLDER:
        est["family_superseded_%s" % STAMP] = est["family"]
        est["family"] = "time_to_first"
        est["family_basis_%s" % STAMP] = (
            "READ from both registrations, which this object holds: EMPEROR-Reduced "
            "registers 'Time to the First Event of Adjudicated Cardiovascular (CV) Death "
            "or Adjudicated Hospitalisation for Heart Failure (HHF)' and EMPEROR-Preserved "
            "registers the same string without the word 'the'. THE ESTIMAND FAMILY IS TIME "
            "TO FIRST EVENT. The SUMMARY MEASURE this pool uses is an odds ratio computed "
            "from cumulative arm counts, which is NOT the same thing and is disclosed "
            "beside the estimate. Recording the family honestly is what makes that "
            "mismatch visible; leaving it as 'not recorded' hid it.")
        changed.append("outcomes[0].estimand.family")
    if est.get("model") in (None, PLACEHOLDER):
        est["model"] = "random-effects, REML"
        changed.append("outcomes[0].estimand.model")
    if out.get("comparator") == PLACEHOLDER or out.get("comparator") is None:
        out["comparator_superseded_%s" % STAMP] = out.get("comparator")
        out["comparator"] = "placebo"
        out["comparator_basis_%s" % STAMP] = (
            "READ from arms[] on both trials, which label the control arm 'placebo'. Both "
            "trials randomised against a matching placebo on top of background therapy.")
        changed.append("outcomes[0].comparator")

    # The operative sentence, inside the card the estimate renders in.
    het = blk.get("heterogeneity") or {}
    prev = blk.get("heterogeneity_status")
    if isinstance(prev, str) and KEY[:40] in prev:
        sys.exit("REFUSED: the key sentence is already in heterogeneity_status.")
    blk["heterogeneity_status_superseded_%s" % STAMP] = prev
    blk["heterogeneity_status"] = (
        "Q = %s on %s df, I-squared %s per cent, tau-squared %s under REML: the two trials "
        "agree closely. THAT AGREEMENT IS NOT THE MAIN UNCERTAINTY HERE. Both trials "
        "registered this endpoint as TIME TO FIRST EVENT and this pool combines ODDS "
        "RATIOS computed from cumulative arm counts, over trials that ran for different "
        "lengths of time. %s: it depends on how long each trial ran, so the weights do not "
        "mean what a reader would assume. Both trials published a hazard ratio and those "
        "are the right inputs. Direction and rough magnitude are not in doubt -- both "
        "favour empagliflozin, both intervals exclude no effect -- but READ THE POOLED "
        "NUMBER AS AN APPROXIMATION TO THE QUANTITY THE TRIALS ESTIMATED, NOT AS THAT "
        "QUANTITY. Two trials agreeing about an odds ratio over unequal follow-up agree "
        "about something neither of them set out to measure."
        % (het.get("q"), het.get("df"), het.get("i2"), het.get("tau2"), KEY))
    changed.append("results.by_outcome.primary.heterogeneity_status")

    if not changed:
        sys.exit("REFUSED: nothing changed. Reporting success on a no-op is the failure "
                 "this project has met five times.")

    obj.setdefault("display_change_announced", []).append({
        "date": TODAY,
        "change": "the card above the estimate no longer contradicts the object",
        "values_moved": "NONE",
        "what_changed": ("%s. The 'What was measured' card is built from "
                         "`outcomes[].estimand.family` and `outcomes[].comparator`, not "
                         "from `pool_uniformity`, and both still held the extraction "
                         "placeholder -- so a reader met 'the estimand is not recorded' "
                         "and then the estimate." % ", ".join(changed)),
        "why": (
            "Two fields answer one question and the previous pass corrected the one the "
            "reader does not see. This is the same shape as the 36 risk-of-bias "
            "assessments counted by P46 and rendered by nothing, at a different address: "
            "THE RENDERER AND THE RECORD READ DIFFERENT KEYS, AND THE RENDERER IS WHAT THE "
            "READER GETS."),
        "how_it_was_found": (
            "By building the page to a scratch path and grepping the bytes, after the "
            "object was already correct. Asserting the write is not the test."),
    })

    print("changed %d field(s):" % len(changed))
    for c in changed:
        print("   ", c)
    if dry:
        print("DRY RUN -- pass --apply to write")
        return
    with io.open(OBJ, "rb") as fh:
        raw = fh.read()
    nl = "\r\n" if b"\r\n" in raw.split(b"\n", 3)[0] + b"\n" else "\n"
    with io.open(OBJ, "w", encoding="utf-8", newline=nl) as fh:
        json.dump(obj, fh, indent=1, ensure_ascii=False)
        fh.write("\n")
    print("wrote %s -- NOW BUILD AND GREP" % OBJ)


if __name__ == "__main__":
    main()
