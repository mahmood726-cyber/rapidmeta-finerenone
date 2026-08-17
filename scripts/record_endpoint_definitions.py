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

 # ------------------------------------------------------------------ IV IRON
 # Five trials, four pooled outcomes, and the interesting reads are the two
 # where the registry does NOT hold the cell: CONFIRM-HF posts no results at all
 # and IRONMAN's primary is worded a component apart from AFFIRM-AHF's.
 "iv-iron-hf": {
  "NCT02937454": {          # AFFIRM-AHF
   "hfh_cvd_recurrent": {
    "text": "HF Hospitalizations and CV Death",
    "description_verbatim": "The composite of recurrent HF hospitalizations and "
            "CV death up to 52 weeks after randomization. Total hospitalisations "
            "included first and recurrent events. If a participant was "
            "hospitalised for heart failure and died within 24 h from any "
            "cardiovascular event, this was counted as one event.",
    "time_frame": "up to 52 weeks after randomization",
    "endpoint_rank": "PRIMARY",
    "source": "registry",
    "source_field": _CTG,
    "source_url": "https://clinicaltrials.gov/study/NCT02937454",
    "read_utc": "2026-08-17",
   },
   "hfh_cvd_first": {
    "text": "Composite of HF Hospitalisations or CV Death",
    "description_verbatim": "Analysed as time to first event at 52 weeks after "
            "randomisation. The number of participants with at least one HF "
            "Hospitalisation or CV Death is presented below.",
    "time_frame": "at 52 weeks after randomisation",
    "endpoint_rank": "SECONDARY",
    "source": "registry",
    "source_field": "protocolSection.outcomesModule.secondaryOutcomes[].measure",
    "source_url": "https://clinicaltrials.gov/study/NCT02937454",
    "read_utc": "2026-08-17",
   },
   "hfh_recurrent": {
    "text": "HF Hospitalisations",
    "description_verbatim": "HF hospitalisations up to 52 weeks after "
            "randomisation analysed as recurrent event.",
    "time_frame": "up to 52 weeks after randomisation",
    "endpoint_rank": "SECONDARY",
    "source": "registry",
    "source_field": "protocolSection.outcomesModule.secondaryOutcomes[].measure",
    "source_url": "https://clinicaltrials.gov/study/NCT02937454",
    "read_utc": "2026-08-17",
   },
   "acm": {
    "text": "All-cause Mortality",
    "description_verbatim": "Number of participants who died up to 52 weeks "
            "after randomisation",
    "endpoint_rank": "OTHER PRE-SPECIFIED, as the registry's own record "
                     "classifies it; this trial's publication does not report "
                     "this outcome at all",
    "source": "registry",
    "source_field": "resultsSection.outcomeMeasuresModule, all-cause mortality",
    "source_url": "https://clinicaltrials.gov/study/NCT02937454",
    "read_utc": "2026-08-17",
   },
  },
  "NCT02642562": {          # IRONMAN
   "hfh_cvd_recurrent": {
    "text": "CV mortality or hospitalisation for worsening heart failure "
            "(analysis will include first and recurrent hospitalisations)",
    "time_frame": "Minimum of 3 months follow-up from last patient recruited",
    "endpoint_rank": "PRIMARY",
    "source": "registry",
    "source_field": _CTG,
    "source_url": "https://clinicaltrials.gov/study/NCT02642562",
    "same_events_different_words": "This counts the same two event classes as "
            "AFFIRM-AHF's primary, written differently: 'CV mortality' for 'CV "
            "Death', and 'hospitalisation for worsening heart failure' for 'HF "
            "Hospitalizations'. Both readings were checked against the canon "
            "rather than assumed -- an earlier version of the component reader "
            "saw neither the CV-mortality component nor the hospitalisation as "
            "one event, and would have reported two trials that count the same "
            "thing as counting different things.",
    "read_utc": "2026-08-17",
   },
  },
  "NCT03036462": {          # FAIR-HF2
   "hfh_cvd_first": {
    "text": "Time-to-first event of CV death or HF hospitalisation",
    "description_verbatim": "Show that treatment of patients with systolic heart "
            "failure (HF) and iron deficiency (ID) with i.v. iron (Ferric "
            "Carboxymaltose, FCM) versus placebo (i.v. NaCl) can extend the "
            "time-to-first-event of heart failure hospitalisations and "
            "cardiovascular (CV) death.",
    "time_frame": "The whole follow-up period. We aim for a minimum average "
                  "follow-up of >2 years.",
    "endpoint_rank": "PRIMARY -- the first of three, under a Hochberg procedure",
    "source": "registry",
    "source_field": _CTG,
    "source_url": "https://clinicaltrials.gov/study/NCT03036462",
    "read_utc": "2026-08-17",
   },
   "hfh_recurrent": {
    "text": "Rate of total (first and recurrent) events of hospitalisations for "
            "heart failure (HF)",
    "description_verbatim": "Show that treatment of patients with systolic heart "
            "failure (HF) and iron deficiency (ID) with i.v. iron (Ferric "
            "Carboxymaltose, FCM) versus placebo (i.v. NaCl) reduces the rate of "
            "recurrent events of heart failure hospitalisations.",
    "endpoint_rank": "PRIMARY -- the second of three, under a Hochberg procedure",
    "source": "registry",
    "source_field": "protocolSection.outcomesModule.primaryOutcomes[1].measure",
    "source_url": "https://clinicaltrials.gov/study/NCT03036462",
    "read_utc": "2026-08-17",
   },
  },
  "NCT03037931": {          # HEART-FID
   "hierarchical_primary": {
    "text": "Number of Deaths; Number of Hospitalizations for Heart Failure; "
            "Change in 6MWT (Six Minute Walk Test) Distance -- the registry "
            "posts these as THREE separate primary outcome measures, and the "
            "publication reports them combined as one hierarchical composite "
            "analysed by unmatched win ratio",
    "description_verbatim": "The number of participants who died out of the "
            "total treated group. / The number of participants who were "
            "hospitalized for heart failure out of the total treated group. / "
            "The change in meters walked at baseline compared to 6 months later.",
    "time_frame": "1 year for death and hospitalisation; 6 months for the walk "
                  "distance",
    "endpoint_rank": "PRIMARY, all three",
    "source": "registry",
    "source_field": "protocolSection.outcomesModule.primaryOutcomes[0..2]",
    "source_url": "https://clinicaltrials.gov/study/NCT03037931",
    "read_utc": "2026-08-17",
   },
  },
  "NCT01453608": {          # CONFIRM-HF
   "acm": {
    "text": "all-cause death, analysed as time to first event",
    "description_verbatim": "The incidence of all-cause death was similar in "
            "both groups",
    "measure_established_by": "The column header of the trial's own Table 2 "
            "reads 'Time to first event hazard ratio  95% CI  P-value'. THIS IS "
            "THE HALF THE STORED QUOTE WAS MISSING: the object held the row "
            "('Death 12 12 (8.9) 14 14 (9.9) 0.89 (0.41-1.93) 0.77') and a row "
            "of numbers does not say what the numbers are. The header does, and "
            "it confirms the object's claim that this is a hazard ratio -- the "
            "same class of question that is currently open on ARNI, asked here "
            "and answered.",
    "endpoint_rank": "a designated secondary outcome-related endpoint, "
                     "adjudicated by the trial's independent endpoint committee",
    "source": "publication",
    "source_field": "Eur Heart J 2015, Table 2 'Hospitalizations and deaths "
                    "(full-analysis set)', row 'Death'",
    "source_url": "https://pubmed.ncbi.nlm.nih.gov/25176939/",
    "add_source_quote": "Table 2 Hospitalizations and deaths (full-analysis "
            "set) -- column header: End-point or event | FCM (n = 150) Total "
            "number of events | Incidence/100 patient-years at risk | Placebo "
            "(n = 151) Total number of events | Incidence/100 patient-years at "
            "risk | TIME TO FIRST EVENT HAZARD RATIO | 95% CI | P-value",
    "registry_does_not_post": "This trial's registry record posts ONE outcome "
            "measure -- the six-minute walk test at week 24 -- and no results "
            "section at all. There is no registry text for this endpoint to "
            "read, and its absence was established by reading the record rather "
            "than inferred from the trial being old.",
    "read_utc": "2026-08-17",
   },
   "six_min_walk_24w": {
    "text": "Change in six minute walk test from baseline to week 24",
    "time_frame": "24 weeks",
    "endpoint_rank": "PRIMARY",
    "source": "registry",
    "source_field": _CTG,
    "source_url": "https://clinicaltrials.gov/study/NCT01453608",
    "read_utc": "2026-08-17",
   },
  },
 },

 # --------------------------------------------------------------- ALIROCUMAB
 # Six trials, one endpoint, and the registry states it in almost exactly the
 # same words on all six records. The differences are orthographic -- one writes
 # "Intent--to--Treat" with two double hyphens, one closes the bracket after
 # "ITT Analysis" instead of before it -- which is the case a fragment test gets
 # wrong in both directions. Recorded whole, compared whole.
 "alirocumab-lipid": {
  "NCT01507831": {"ldlc_pct_change_wk24": {
    "text": "Percent Change From Baseline in Calculated LDL-C at Week 24 - "
            "Intent-to-Treat (ITT) Analysis",
    "time_frame": "From Baseline to Week 52",
    "endpoint_rank": "SECONDARY -- this trial's only PRIMARY outcome is the "
        "proportion of participants with adverse events, because it was "
        "designed as a long-term safety study. An earlier build EXCLUDED this "
        "trial for posting no LDL result, which came from reading primary "
        "outcomes only; it is the largest trial in the set.",
    "source": "registry", "source_field": _CTG,
    "source_url": "https://clinicaltrials.gov/study/NCT01507831",
    "read_utc": "2026-08-17"}},
  "NCT01617655": {"ldlc_pct_change_wk24": {
    "text": "Percent Change From Baseline in Calculated LDL-C at Week 24 - ITT "
            "Analysis",
    "time_frame": "From Baseline to Week 52", "endpoint_rank": "PRIMARY",
    "source": "registry", "source_field": _CTG,
    "source_url": "https://clinicaltrials.gov/study/NCT01617655",
    "read_utc": "2026-08-17"}},
  "NCT01623115": {"ldlc_pct_change_wk24": {
    "text": "Percent Change From Baseline in Calculated LDL-C at Week 24 - "
            "Intent-to-Treat (ITT) Analysis",
    "time_frame": "From Baseline to Week 52", "endpoint_rank": "PRIMARY",
    "source": "registry", "source_field": _CTG,
    "source_url": "https://clinicaltrials.gov/study/NCT01623115",
    "read_utc": "2026-08-17"}},
  "NCT01644175": {"ldlc_pct_change_wk24": {
    "text": "Percent Change From Baseline in Calculated LDL-C at Week 24 - "
            "Intent-to-Treat (ITT) Analysis",
    "time_frame": "From Baseline to Week 52", "endpoint_rank": "PRIMARY",
    "source": "registry", "source_field": _CTG,
    "source_url": "https://clinicaltrials.gov/study/NCT01644175",
    "read_utc": "2026-08-17"}},
  "NCT01709500": {"ldlc_pct_change_wk24": {
    "text": "Percent Change From Baseline in Calculated LDL-C at Week 24 - "
            "Intent--to--Treat (ITT) Analysis",
    "time_frame": "From Baseline to Week 52", "endpoint_rank": "PRIMARY",
    "source": "registry", "source_field": _CTG,
    "source_url": "https://clinicaltrials.gov/study/NCT01709500",
    "orthography_note": "The double hyphens in 'Intent--to--Treat' are the "
        "registry's own. Quoted as posted rather than tidied: a definition "
        "compared whole must be recorded whole.",
    "read_utc": "2026-08-17"}},
  "NCT02107898": {"ldlc_pct_change_wk24": {
    "text": "Percent Change From Baseline in Calculated LDL-C at Week 24 - "
            "Intent-to-Treat (ITT Analysis)",
    "time_frame": "From Baseline to Week 52", "endpoint_rank": "PRIMARY",
    "source": "registry", "source_field": _CTG,
    "source_url": "https://clinicaltrials.gov/study/NCT02107898",
    "read_utc": "2026-08-17"}},
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
                k: v for k, v in rec.items()
                if k not in ("text", "add_source_quote")}
            # A QUOTE THAT ESTABLISHES THE MEASURE BELONGS IN THE AUDIT SURFACE,
            # not only in this record. CONFIRM-HF's stored provenance was the
            # TABLE ROW -- a line of numbers, which does not say what the numbers
            # are. The column header does, and a reader checking us needs to see
            # it on the extraction tab. Appended idempotently: re-running must
            # not grow the list.
            q = rec.get("add_source_quote")
            if q:
                prov = bo.setdefault("provenance", {})
                quotes = prov.setdefault("source_quotes", [])
                if q not in quotes:
                    quotes.append(q)
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
