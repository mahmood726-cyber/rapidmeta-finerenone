"""For trials a review names but publishes no numbers for, can WE publish numbers?

ROSALIND'S FRAMING, and it is the one that survives scrutiny:

    "If a review doesn't print per-trial numbers, that's a REPORTING choice -- they
    extracted them, they just didn't publish them. So the honest claim isn't 'we have data
    they didn't have', it's 'we PUBLISH per-trial data for trials where the review that used
    them published none'. That's about TRANSPARENCY rather than access."

So nothing here claims superior access. A review team holding a paywalled PDF has the
numbers. The measurable difference is what reaches a reader.

MEASURED AS A PROPORTION OF *THEIR* INCLUDED TRIALS, not of ours, because that is the
comparison a reader would make: of the trials this review names and publishes no per-trial
numbers for, for how many can per-trial numbers be put on a page from open sources?

THE MEASURABLE SET IS SMALL AND THE REASON IS ITSELF THE FINDING. Of 331 full-text reviews,
246 print no per-trial table -- but only 13 of those also name a trial registration. The two
auditability failures are CORRELATED: a review that does not print its numbers usually does
not name its trials either, so there is no way to know which trials to recover data for.

    331  full-text reviews
    246  print no per-trial table
     13  ...and name at least one registration   <- the only set where this is measurable

That 13 is not a sampling limitation to be scaled away. It is the population, and it means
the exceeding claim can only be made about reviews that are already half-auditable.

THREE STATES PER TRIAL, and the third is not a success:
  RECOVERABLE     the registry posts per-arm results for this trial
  NO_RESULTS      the trial exists and posted nothing -- nobody can publish its numbers
  NOT_FOUND       the registration could not be read
"""
import collections
import io
import json
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, "scripts"))
import instrument_controls
import measure_data_recovery_v2_2026_08_25 as V2

OUT = os.path.join(REPO, "outputs", "exceed_2026_08_25.json")
NAMING = [os.path.join(REPO, "outputs", "review_registration_naming_2026_08_25.jsonl"),
          os.path.join(REPO, "outputs", "cochrane_registration_naming_2026_08_25.jsonl")]
TABLES = os.path.join(REPO, "outputs", "per_trial_tables_2026_08_25.jsonl")


def load(path):
    out = {}
    if not os.path.exists(path):
        return out
    for line in io.open(path, encoding="utf-8"):
        try:
            d = json.loads(line)
        except ValueError:
            continue
        if d.get("status") == "ok":
            out[d["pmcid"]] = d
    return out


def control():
    """The classifier must separate a trial with posted results from one without."""
    withres = {"has": True, "outcomes": [{"title": "AE: x", "groups": {},
                                          "values": {"G0": ["3", "776"]}}]}
    without = {"has": False, "outcomes": []}
    instrument_controls.require_controls(
        "exceed",
        ("a trial with posted per-arm results is RECOVERABLE",
         bool(withres["has"] and withres["outcomes"]), True),
        ("a trial with no posted results must NOT be RECOVERABLE",
         bool(without["has"] and without["outcomes"]), True))
    return True


def main():
    control()
    naming = {}
    for p in NAMING:
        naming.update(load(p))
    tables = load(TABLES)
    targets = [p for p in tables
               if p in naming and not tables[p].get("per_trial")
               and naming[p].get("n_nct", 0) > 0]
    print("reviews printing NO per-trial table AND naming >=1 registration: %d"
          % len(targets))
    if not targets:
        print("NO RATE IS PRINTED.")
        return 1

    rows = []
    for pid in targets:
        _t, _r, ncts = V2.review_rows(pid)
        if not ncts:
            continue
        per = []
        for n in ncts:
            rec = V2.trial_record(n)
            if rec is None:
                per.append((n, "NOT_FOUND"))
            elif rec["has"] and rec["outcomes"]:
                per.append((n, "RECOVERABLE"))
            else:
                per.append((n, "NO_RESULTS"))
        rows.append({"pmcid": pid, "n_named": len(ncts), "trials": per})
        c = collections.Counter(s for _n, s in per)
        print("  PMC%-10s named %2d  recoverable %2d  no_results %2d  not_found %2d"
              % (pid, len(ncts), c.get("RECOVERABLE", 0), c.get("NO_RESULTS", 0),
                 c.get("NOT_FOUND", 0)))

    allt = [s for r in rows for _n, s in r["trials"]]
    c = collections.Counter(allt)
    n = len(allt)
    print()
    print("trials named across these reviews : %d" % n)
    print("  RECOVERABLE  %3d  (%.0f%%)  -- per-arm results are posted; we could publish them"
          % (c.get("RECOVERABLE", 0), 100.0*c.get("RECOVERABLE", 0)/max(n, 1)))
    print("  NO_RESULTS   %3d  (%.0f%%)  -- posted nothing; NOBODY can publish these"
          % (c.get("NO_RESULTS", 0), 100.0*c.get("NO_RESULTS", 0)/max(n, 1)))
    print("  NOT_FOUND    %3d  (%.0f%%)  -- registration unreadable; a failure, not an absence"
          % (c.get("NOT_FOUND", 0), 100.0*c.get("NOT_FOUND", 0)/max(n, 1)))
    print()
    print("THE CLAIM THIS SUPPORTS is about transparency, not access: for %d of %d trials that"
          % (c.get("RECOVERABLE", 0), n))
    print("these reviews included and published no per-trial numbers for, per-trial numbers")
    print("could be put on a page from a free source. The review teams had the numbers; the")
    print("difference is what reaches a reader.")
    json.dump({"rows": rows, "counts": dict(c)}, io.open(OUT, "w", encoding="utf-8"), indent=1)
    print()
    print("written: %s" % os.path.relpath(OUT, REPO))
    return 0


if __name__ == "__main__":
    sys.exit(main())
