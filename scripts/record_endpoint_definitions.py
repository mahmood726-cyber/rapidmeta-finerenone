"""RECORD ENDPOINT DEFINITIONS -- what each trial COUNTED, read from the registry.

WHY THIS FILE EXISTS AT ALL, RATHER THAN A HAND EDIT
    SGLT2_HF pooled two different endpoints as one and passed every check in this
    repository, because the object stored RESULT sentences as provenance and no
    endpoint definition anywhere. A quote that says what HAPPENED is not a quote
    that says what was COUNTED.

    So the definitions are recorded HERE, in a tracked file, beside the field they
    were read from and the date they were read. A hand edit of a 300 KB object
    leaves no record of WHERE the sentence came from, and a definition whose
    source cannot be named is worth about as much as an assumed one.

WHAT THIS RECORDS -- AND THE ONE DISTINCTION THAT MATTERS
    `text`     the definition, verbatim, from the named field.
    `source`   registry / publication / regulator, with the exact field or page.
    `read_utc` when a human read it.

    Where the registry posts no such outcome -- an analysis that exists only in a
    regulator's review, or an endpoint that was CHANGED during the trial so the
    current posting no longer contains it -- that is recorded as
    `registry_does_not_post`, WITH the reason. It is never left blank: a blank
    field beside a trial name reads as "no endpoint", which is a different and
    much stronger claim than "the registry is not where this one lives".

WHAT THIS DOES NOT ESTABLISH -- written in advance
    - NOT that the definitions being identical licenses a pool. Populations,
      follow-up, analysis sets and ascertainment can still differ, and on
      SOTAGLIFLOZIN the populations differ more than anything else in the object.
    - NOT that the registry text is the trial's true endpoint. Registries are
      amended. Where a publication states the endpoint changed, both were read,
      and that is recorded on the cell rather than resolved silently.
    - NOT that a definition exists for every cell. Cells with no definition
      remain without one and the gate keeps failing them; this script writes
      only what was actually read.

USAGE  python scripts/record_endpoint_definitions.py <app_id> [--dry-run]
"""
from __future__ import annotations
import io, json, os, sys

if __name__ == "__main__":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

_CTG = "protocolSection.outcomesModule.primaryOutcomes[0].measure"

# ---------------------------------------------------------------------------
# app_id -> nct -> outcome_id -> record
# ---------------------------------------------------------------------------
DEFINITIONS = {
 "sotagliflozin-hf": {
  "NCT03521934": {
   "hfcv_total": {
    "text": "Number of Total Occurrences of Cardiovascular (CV) Death, "
            "Hospitalizations for Heart Failure (HHF) and Urgent Visits for "
            "Heart Failure (HF)",
    "description_verbatim": "Combined endpoint of the total number of occurrences "
            "(first and potentially subsequent) of CV death, HHF, and urgent HF "
            "visits after randomization. Events that occurred during the study "
            "were calculated as the total number of events per 100 person-years "
            "of follow-up.",
    "time_frame": "Up to 21.9 months",
    "source": "registry",
    "source_field": _CTG,
    "source_url": "https://clinicaltrials.gov/study/NCT03521934",
    "read_utc": "2026-08-17",
   },
   "hfcv_first": {
    "text": "Cardiovascular (CV) Death, Hospitalizations for Heart Failure (HHF) "
            "and Urgent Visits for Heart Failure (HF) -- the same event class as "
            "this trial's registered primary endpoint, analysed as time to FIRST "
            "event instead of as total occurrences",
    "source": "regulator_fda",
    "source_field": "integrated review, statistical section, sensitivity analyses",
    "source_url": "https://www.accessdata.fda.gov/drugsatfda_docs/nda/2023/"
                  "216203Orig1s000IntegratedR.pdf",
    "registry_does_not_post": "The registry posts this trial's composite ONLY as "
            "total occurrences. The time-to-first analysis of the same composite "
            "exists in the regulator's review and nowhere in the registry, so the "
            "EVENT CLASS is quoted from the registry field above and the ANALYSIS "
            "is named from the review. Those are two different facts and they are "
            "recorded separately on purpose.",
    "read_utc": "2026-08-17",
   },
  },
  "NCT03315143": {
   "hfcv_total": {
    "text": "Number of Total Occurrences of Cardiovascular (CV) Death, "
            "Hospitalizations for Heart Failure (HHF) and Urgent Visits for "
            "Heart Failure (HF)",
    "description_verbatim": "Combined endpoint of the total number of occurrences "
            "(first and potentially subsequent) of CV death, HHF, and urgent HF "
            "visits after randomization. Events that occurred during the study "
            "were calculated as the total number of events per 100 person-years "
            "of follow-up.",
    "time_frame": "Up to 30 months",
    "source": "registry",
    "source_field": _CTG,
    "source_url": "https://clinicaltrials.gov/study/NCT03315143",
    "endpoint_was_changed_during_the_trial": "The publication states the primary "
            "end point was CHANGED during the trial. The registry record read "
            "here is the AMENDED one, and it is the endpoint the reported hazard "
            "ratio belongs to. The superseded original coprimary is carried "
            "separately in this object as mace3_first, from a single trial, and "
            "is not pooled.",
    "read_utc": "2026-08-17",
   },
   "hfcv_first": {
    "text": "Cardiovascular (CV) Death, Hospitalizations for Heart Failure (HHF) "
            "and Urgent Visits for Heart Failure (HF) -- the same event class as "
            "this trial's registered primary endpoint, analysed as time to FIRST "
            "event instead of as total occurrences",
    "source": "regulator_fda",
    "source_field": "integrated review, statistical section, sensitivity analyses",
    "source_url": "https://www.accessdata.fda.gov/drugsatfda_docs/nda/2023/"
                  "216203Orig1s000IntegratedR.pdf",
    "registry_does_not_post": "As for SOLOIST-WHF: the registry posts the "
            "composite only as total occurrences. NOTE the publication ALSO "
            "reports a first-occurrence composite for this trial, but of CV death "
            "OR hospitalisation for heart failure WITHOUT urgent visits -- a "
            "different event class, which is why it is held out rather than used "
            "here. That hold-out is recorded in this object's scope decisions.",
    "read_utc": "2026-08-17",
   },
   "mace3_first": {
    "text": "the first occurrence of death from cardiovascular causes, nonfatal "
            "myocardial infarction, or nonfatal stroke",
    "source": "publication",
    "source_field": "NEJM report of SCORED, describing the ORIGINAL coprimary "
                    "end point that was superseded during the trial",
    "source_url": "https://pubmed.ncbi.nlm.nih.gov/33200892/",
    "registry_does_not_post": "The current registry record does not post a "
            "FIRST-occurrence version of this composite. It posts a TOTAL-"
            "occurrence one ('Total Number of Occurrences of CV Death, Non-fatal "
            "Myocardial Infarction and Non-fatal Stroke') as a secondary outcome, "
            "which is a different quantity from the one stored here. The "
            "first-occurrence composite is the superseded original coprimary and "
            "survives only in the publication. This is exactly the case the "
            "registry read cannot settle alone, and it is why this outcome is "
            "reported from a single trial and pooled with nothing.",
    "read_utc": "2026-08-17",
   },
  },
 },
}


def apply(app_id, dry=False):
    path = os.path.join(REPO, "ssot", app_id, "%s.json" % app_id)
    if not os.path.exists(path):
        print("no object at %s -- NOT RUN" % path, file=sys.stderr)
        return 2
    spec = DEFINITIONS.get(app_id)
    if not spec:
        print("no definitions recorded for %s -- NOT RUN. This script writes only "
              "what was actually read." % app_id, file=sys.stderr)
        return 2
    obj = json.loads(open(path, encoding="utf-8").read())
    trials = ((obj.get("inputs") or {}).get("trials")) or []
    by_nct = {}
    for t in trials:
        if t.get("nct"):
            by_nct[t["nct"]] = t
    written, missing = 0, []
    for nct, outcomes in spec.items():
        t = by_nct.get(nct)
        if t is None:
            missing.append("%s is not a trial in this object" % nct)
            continue
        for oid, rec in outcomes.items():
            bo = (t.get("by_outcome") or {}).get(oid)
            if bo is None:
                missing.append("%s has no by_outcome[%r]" % (nct, oid))
                continue
            bo["outcome_definition"] = rec["text"]
            bo["outcome_definition_source"] = {
                k: v for k, v in rec.items() if k != "text"}
            written += 1
            print("  %-14s %-12s <- %s" % (nct, oid, rec["source"]))
    for m in missing:
        print("  UNWRITTEN: %s" % m)
    if missing:
        print("\nRefusing to write: the spec names cells this object does not have, "
              "so one of the two is wrong and guessing which is how a definition "
              "lands on the wrong trial.")
        return 1
    if dry:
        print("\n--dry-run: %d definition(s) would be written to %s" % (written, path))
        return 0
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=1)
        f.write("\n")
    print("\nwrote %d definition(s) to %s" % (written, path))
    return 0


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if not args:
        print("usage: record_endpoint_definitions.py <app_id> [--dry-run]\n"
              "known: %s" % ", ".join(sorted(DEFINITIONS)), file=sys.stderr)
        return 2
    rc = 0
    for a in args:
        rc |= apply(a, dry="--dry-run" in sys.argv)
    return rc


if __name__ == "__main__":
    sys.exit(main())
