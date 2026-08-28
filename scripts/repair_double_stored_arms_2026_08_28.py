"""Repair `inputs.trials[].arms` where a fix was applied to the OTHER copy of the same fact.

THE SHAPE. hepatitis-b-taf-tdf stores its arms TWICE:

    inputs.trials[].arms                    the extraction  -- UNCORRECTED
    results...per_trial[].as_posted         repaired 2026-08-18 from CT.gov

A repair applied to one copy and not the other satisfies whichever checker reads the mended
one and lies to whichever reads the other. Both are true statements about the object and they
disagree, so "is this object correct?" has no answer until they are reconciled.

  This is why my own three-source check reported that the OBJECT and its stored REASON agreed
  while the REGISTRY disagreed. They did agree -- I was reading the uncorrected copy. The
  repaired copy had agreed with the registry since 2026-08-18.

THE ERROR IS THE LABEL ONLY, AND THAT IS ESTABLISHED, NOT ASSUMED. On both trials the stored
control arm's participants and events match the as_posted TDF comparator exactly:

    NCT01940341  control n=140  events=130   as_posted TDF n=140 pct=92.9 -> 130.1
    NCT01940471  control n=292  events=195   as_posted TDF n=292 pct=66.8 -> 195.1

and the pinned registry record marks `TDF 300 mg` ACTIVE_COMPARATOR while `Open-label TAF` is
a third EXPERIMENTAL arm. So the control arm holds the TDF arm's numbers under a TAF label.
The counts are right; only the name is wrong. THIS SCRIPT CHANGES NO NUMBER -- if a count
disagreed it would refuse, because that would be a different and much larger defect.

WHY NOT JUST DELETE THE UNCORRECTED COPY. Because other code reads it. The two copies are
reconciled, and the repair records where the corrected value came from so the next reader
does not have to re-derive it.
"""
import io
import json
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(REPO, "outputs", "double_stored_arms_2026_08_28.json")
TOL = 1.0          # events implied by a posted percentage, rounded


def main():
    apply_ = "--apply" in sys.argv
    raw = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace",
                           write_through=True)

    def say(s):
        raw.write(s + chr(10))
        raw.flush()

    pm = json.load(io.open(os.path.join(REPO, "ssot", "PAGE_MAP.json"), encoding="utf-8"))
    rel = pm["HEPATITIS_B_TAF_TDF_REVIEW.html"]
    path = os.path.join(REPO, rel)
    obj = json.load(io.open(path, encoding="utf-8"))

    trials = dict((t.get("nct"), t) for t in (obj.get("inputs") or {}).get("trials") or [])
    changes, refusals = [], []

    for oid, blk in ((obj.get("results") or {}).get("by_outcome") or {}).items():
        if not isinstance(blk, dict):
            continue
        for row in blk.get("per_trial") or []:
            ap = row.get("as_posted")
            nct = row.get("nct")
            if not ap or nct not in trials:
                continue
            arms = trials[nct].get("arms") or []
            ctl = [a for a in arms if a.get("role") == "control"]
            trt = [a for a in arms if a.get("role") == "treatment"]
            if len(ctl) != 1 or len(trt) != 1:
                refusals.append((nct, "expected exactly one control and one treatment arm"))
                continue
            ctl, trt = ctl[0], trt[0]

            # the counts must already agree; this repairs a NAME, never a number
            for arm, n_key, pct_key, who in ((ctl, "comparator_n", "comparator_pct",
                                              "comparator"),
                                             (trt, "intervention_n", "intervention_pct",
                                              "intervention")):
                n_posted = ap.get(n_key)
                pct = ap.get(pct_key)
                if n_posted is None or pct is None:
                    refusals.append((nct, "as_posted lacks %s/%s" % (n_key, pct_key)))
                    continue
                if float(arm.get("participants") or -1) != float(n_posted):
                    refusals.append((nct, "%s participants %s != as_posted %s -- NOT a "
                                          "label-only error" % (who, arm.get("participants"),
                                                                n_posted)))
                    continue
                implied = n_posted * pct / 100.0
                if abs(float(arm.get("events") or -1) - implied) > TOL:
                    refusals.append((nct, "%s events %s != implied %.1f -- NOT a label-only "
                                          "error" % (who, arm.get("events"), implied)))

            if refusals and refusals[-1][0] == nct:
                continue

            posted_label = ap.get("comparator")
            if ctl.get("label") != posted_label:
                changes.append({"nct": nct, "field": "inputs.trials[].arms[control].label",
                                "from": ctl.get("label"), "to": posted_label,
                                "why": "the repaired copy (as_posted, read %s from %s) names "
                                       "this arm %s, and its participants and events match "
                                       "that arm exactly"
                                       % (ap.get("read_utc"), ap.get("source"),
                                          posted_label)})
                if apply_:
                    ctl["label"] = posted_label
                    ctl["label_repaired_2026_08_28"] = (
                        "was %r. The same fact was stored twice and only the as_posted copy "
                        "was repaired on %s; this reconciles the extraction copy to it. "
                        "Counts were already correct and are unchanged."
                        % ("Open-label TAF", ap.get("read_utc")))

    say("object: %s" % rel)
    say("")
    say("REPAIRS (label only, counts unchanged): %d" % len(changes))
    for c in changes:
        say("   %s  %s" % (c["nct"], c["field"]))
        say("      %r -> %r" % (c["from"], c["to"]))
    say("")
    say("REFUSALS: %d" % len(refusals))
    for n, why in refusals:
        say("   %s  %s" % (n, why))

    if refusals:
        say("")
        say("REFUSED to write: a count disagreed, so this is not a label-only error.")
        return 2
    if not apply_:
        say("")
        say("(dry run -- nothing written; pass --apply)")
        return 0

    io.open(path, "w", encoding="utf-8").write(
        json.dumps(obj, indent=1, ensure_ascii=False))
    json.dump({"object": rel, "copies": ["inputs.trials[].arms (repaired here)",
                                         "results.by_outcome[].per_trial[].as_posted "
                                         "(already repaired 2026-08-18)"],
               "changes": changes,
               "counts_changed": 0,
               "note": "a repair applied to one copy of a twice-stored fact satisfies "
                       "whichever checker reads the mended one and lies to the other"},
              io.open(OUT, "w", encoding="utf-8"), indent=1)
    say("")
    say("wrote %s" % os.path.relpath(OUT, REPO))
    return 0


if __name__ == "__main__":
    sys.exit(main())
