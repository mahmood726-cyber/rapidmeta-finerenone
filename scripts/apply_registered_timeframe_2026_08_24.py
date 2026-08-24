"""Write each trial's REGISTERED primary-outcome time frame onto its object.

WHY THIS ONE AND NOT THE OTHER TWO. Five blind reviewers, both model families, named the same
three things as what stopped them acting on these reviews: arm-level event counts, harms, and
how long participants were followed. The first two need a results posting, which 110 of 137
registrations have and 27 do not. The third does not depend on that split at all -- it lives
on the PROTOCOL record, which every registration has, and 135 of 137 carry it. It is the one
of the three that is nearly free, so it is taken now rather than waiting on a decision about
the other two.

STORED AS THE REGISTRY'S OWN WORDS, DELIBERATELY. The field is free text and it varies:
"4.9 years", "Mean follow up of 4 years", "36 months", "Randomization up to 15 months",
"From 2 weeks after the last vaccine or placebo dose up to 1 year of age". Parsing that into
a number would produce a tidy column and would quietly assert things the source does not say
-- that "up to 5 years" is 5 years, that a mean is a median, that a vaccine schedule window
is a follow-up duration. For an audience of medical students who cannot tell our derivations
from the trials' own statements, a verbatim string they can check against the registry is
worth more than a normalised one they cannot.

It is also labelled for what it is: the time frame of the PRIMARY OUTCOME as registered, not
the trial's overall follow-up, which can differ and is not what this field records.

READ-ONLY SOURCE, ALREADY FETCHED. Everything here comes from the probe cache written by
`probe_results_postings_2026_08_24.py`, so this applier makes no network call and can be
re-run without touching the registry.
"""
import glob
import io
import json
import os

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CACHE = os.path.join(REPO, "outputs", "ctgov_results_probe_cache.json")
STAMP = "registered_primary_timeframe"


def main():
    cache = json.load(io.open(CACHE, encoding="utf-8"))
    timeframes = {}
    for nct, rec in cache.items():
        if "_error" in rec:
            continue
        prim = (((rec.get("protocolSection") or {}).get("outcomesModule") or {})
                .get("primaryOutcomes") or [])
        tfs = [" ".join(str(o.get("timeFrame")).split())
               for o in prim if isinstance(o, dict) and o.get("timeFrame")]
        if tfs:
            # ONE PRIMARY OUTCOME CAN HAVE SEVERAL TIME FRAMES, and where they differ that
            # difference is itself information. Joined rather than reduced to the first.
            uniq = []
            for t in tfs:
                if t not in uniq:
                    uniq.append(t)
            timeframes[nct] = "; ".join(uniq)

    touched_objects = 0
    touched_trials = 0
    for p in sorted(glob.glob(os.path.join(REPO, "ssot", "*", "*.json"))):
        slug = os.path.basename(os.path.dirname(p))
        if os.path.basename(p) != slug + ".json":
            continue
        try:
            with io.open(p, encoding="utf-8") as fh:
                obj = json.load(fh)
        except Exception:
            continue
        changed = False
        # POSITIVE FORM: iterate the records that ARE trials. `audit_exclusion_by_absence
        # --gate` refuses a corpus-wide loop that defines its subject by what it skips, and
        # the rule earns its keep here -- an applier that silently `continue`s past malformed
        # records cannot tell you how many it declined to touch.
        trials = [t for t in ((obj.get("inputs") or {}).get("trials") or [])
                  if isinstance(t, dict)]
        for t in trials:
            nct = str(t.get("nct") or "")
            if nct in timeframes and t.get(STAMP) != timeframes[nct]:
                t[STAMP] = timeframes[nct]
                t[STAMP + "_basis"] = (
                    "The time frame of this trial's REGISTERED PRIMARY OUTCOME, quoted "
                    "verbatim from its ClinicalTrials.gov protocol record, read 2026-08-24. "
                    "It is not necessarily the trial's overall follow-up, and it is not "
                    "parsed into a number: the registry's wording varies and normalising it "
                    "would assert precision the source does not carry.")
                changed = True
                touched_trials += 1
        if changed:
            # indent=1, matching the corpus. Re-serialising 130 objects at a different
            # indent once buried a semantic change under 119,000 lines of diff.
            io.open(p, "w", encoding="utf-8").write(
                json.dumps(obj, ensure_ascii=False, indent=1))
            touched_objects += 1

    print("registrations with a time frame in the cache : %d" % len(timeframes))
    print("objects updated                              : %d" % touched_objects)
    print("trial records given a time frame             : %d" % touched_trials)


main()
