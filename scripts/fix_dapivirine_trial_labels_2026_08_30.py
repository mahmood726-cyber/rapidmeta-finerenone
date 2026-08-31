# -*- coding: utf-8 -*-
"""The two dapivirine trials are labelled the wrong way round, and I propagated it.

⛔ THE DEFECT, VERIFIED AGAINST THE REGISTRY RATHER THAN THE OBJECT.

    NCT01539226   orgStudyId IPM 027    n=1959 ACTUAL   -> THE RING STUDY
    NCT01617096   acronym ASPIRE, MTN-020, n=2629 ACTUAL -> ASPIRE

The object labels them the OPPOSITE way in TWO places -- `inputs.trials[].label` and
`risk_of_bias.by_outcome[..][..].trial`. That is a pre-existing corpus defect.

⚠️ AND I INHERITED IT AND MADE IT WORSE. Reading the object's label rather than the
registry, I recorded Baeten's ASPIRE paper (PMC4993693) as evidence against NCT01539226 --
which is The Ring Study. A real finding attached to the wrong trial. That is precisely the
error I avoided an hour earlier with FIGARO, by checking coverage before writing, and then
committed here by trusting a label I had not checked.

⇒ **A LABEL ON THE OBJECT IS NOT AN IDENTITY. THE REGISTRY IS.** Same rule as "a name match
is a filter, not an identity", arriving from inside our own data instead of someone else's.

⭐ THE ANALYSIS IS UNAFFECTED, AND THAT WAS CHECKED RATHER THAN ASSUMED. The effect
estimates are keyed correctly to the NCTs:

    NCT01539226 -> 0.6711 (0.4884-0.9221)   matches the published Ring Study (~0.69)
    NCT01617096 -> 0.7320 (0.5442-0.9845)   matches published ASPIRE (~0.73)

So the pooled estimate never depended on the labels. What was wrong is every sentence that
NAMES a trial -- which is most of what a reader reads.

WHAT THIS SCRIPT DOES
  1. Corrects both label sites to match ClinicalTrials.gov, keeping the wrong value.
  2. Re-assigns the risk-of-bias evidence to the trial whose paper it actually came from,
     and adds The Ring Study's answers from its own free full text.

⭐ AND BOTH PAPERS TURNED OUT FREE, so no access exception was needed after all. The Ring
Study's primary has no PMC record and `isOpenAccess=N` -- three signals saying "not free" --
while Europe PMC's fullTextUrlList says `availability: Free` and Unpaywall says `is_oa:
true`. The PDF fetched: 590,022 bytes. Checking dissolved the request twice.
"""
import datetime
import io
import json
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, "..", "ssot"))

import atomic_write as aw          # noqa: E402
import regulatory_evidence as R    # noqa: E402

TOPIC = "agyw-hiv-prep-review"
UTC = datetime.datetime.now(datetime.timezone.utc).isoformat()

# Verified from ClinicalTrials.gov on 2026-08-30, not from the object.
TRUTH = {
    "NCT01539226": {"label": "The Ring Study / IPM 027",
                    "org_study_id": "IPM 027", "enrolment": 1959},
    "NCT01617096": {"label": "ASPIRE / MTN-020",
                    "org_study_id": "MTN-020", "acronym": "ASPIRE", "enrolment": 2629},
}

ASPIRE_DOC = ("Baeten JM et al. Use of a Vaginal Ring Containing Dapivirine for HIV-1 "
              "Prevention in Women. N Engl J Med 2016. PMID 26900902, PMC4993693.")
ASPIRE_URL = "https://pmc.ncbi.nlm.nih.gov/articles/PMC4993693/"
ASPIRE_ANSWERS = [
    ("1.2", "YES", R.INFERRED, "Study Procedures",
     "with the exception of staff members at the central statistical and data management "
     "center, investigators and participants were unaware of the randomization "
     "assignments"),
    ("2.6", "YES", R.STATED, "Statistical Analysis",
     "The primary analysis of HIV-1 protection was performed according to the "
     "intention-to-treat principle"),
    ("3.1", "YES", R.STATED, "Follow-up and Adherence",
     "with 2614 participants (99.4%) completing at least one post-randomization HIV-1 "
     "test"),
]

RING_DOC = ("Nel A et al. Safety and Efficacy of a Dapivirine Vaginal Ring for HIV "
            "Prevention in Women. N Engl J Med 2016. PMID 27959766, "
            "doi 10.1056/NEJMoa1602046. Free at the publisher.")
RING_URL = "https://www.nejm.org/doi/pdf/10.1056/NEJMoa1602046"
RING_ANSWERS = [
    # ⚠️ NO_INFORMATION is recorded as an answer, not omitted. The paper does not describe a
    # concealment mechanism, and the assessor refused rather than stretching an unrelated
    # sentence -- which is the behaviour that makes the other two answers worth anything.
    ("1.2", "NO_INFORMATION", R.INFERRED,
     "Trial Population, Design, and Oversight", ""),
    ("2.6", "PROBABLY_YES", R.STATED, "Statistical Analysis",
     "The primary analysis was performed in the modified intention-to-treat population"),
    ("3.1", "PROBABLY_YES", R.STATED, "Results; Trial Participants",
     "A total of 61 of 1959 participants (3.1%) were lost to follow-up."),
]

SOURCES = {
    "NCT01617096": (ASPIRE_DOC, ASPIRE_URL, ASPIRE_ANSWERS,
                    "F:/claude-temp/rm-dapivirine-2026-08-31/ft/ASPIRE_PMC4993693.txt"),
    "NCT01539226": (RING_DOC, RING_URL, RING_ANSWERS,
                    "F:/claude-temp/rm-dapivirine-2026-08-31/ft/RINGSTUDY_NEJMoa1602046.txt"),
}


def _norm(s):
    return " ".join(str(s or "").split()).lower()


def main(apply_changes=False):
    path = os.path.join(_HERE, "..", "ssot", TOPIC, "%s.json" % TOPIC)
    obj = json.load(open(path, encoding="utf-8"))

    # ---- 1. labels -------------------------------------------------------------
    fixed = []
    for t in ((obj.get("inputs") or {}).get("trials") or []):
        n = t.get("nct")
        if n in TRUTH and t.get("label") != TRUTH[n]["label"]:
            fixed.append(("inputs.trials", n, t.get("label"), TRUTH[n]["label"]))
            t["label_before_2026_08_30"] = t.get("label")
            t["label"] = TRUTH[n]["label"]
            t["label_corrected_because"] = (
                "ClinicalTrials.gov gives orgStudyId %r and enrolment %s for this NCT. The "
                "previous label named the other trial."
                % (TRUTH[n]["org_study_id"], TRUTH[n]["enrolment"]))
    for oc, per in ((obj.get("risk_of_bias") or {}).get("by_outcome") or {}).items():
        for rid, rec in (per or {}).items():
            if rid in TRUTH and isinstance(rec, dict) and rec.get("trial") != TRUTH[rid]["label"]:
                fixed.append(("risk_of_bias.by_outcome", rid, rec.get("trial"),
                              TRUTH[rid]["label"]))
                rec["trial_before_2026_08_30"] = rec.get("trial")
                rec["trial"] = TRUTH[rid]["label"]

    # ---- 2. evidence, re-assigned to the trial whose paper it came from ---------
    store = (obj.setdefault("risk_of_bias", {})).setdefault(R.STORE_KEY, {})
    store["by_trial"] = {}
    built_counts = {}
    for nct, (doc, url, answers, textfile) in SOURCES.items():
        if not os.path.exists(textfile):
            print("SOURCE TEXT MISSING for %s: %s" % (nct, textfile))
            return 1
        text = _norm(open(textfile, encoding="utf-8", errors="replace").read())
        built = {}
        for q, resp, tier, where, quote in answers:
            if quote and _norm(quote) not in text:
                print("REFUSED -- quote not in %s: %s %r" % (nct, q, quote[:60]))
                return 1
            built[q] = R.answer(q, resp, tier, quote, doc, section=where, url=url,
                                retrieved_utc=UTC, document_class="trial_publication")
        store["by_trial"][nct] = built
        built_counts[nct] = len(built)

    store.update({
        "recorded_utc": UTC, "n_assessors": 1, "adjudicated": False,
        "assessor": "GPT-5 Codex (openai family), via codex exec, one read per paper",
        "assignment_corrected_2026_08_30": (
            "An earlier version of this store put Baeten's ASPIRE paper against "
            "NCT01539226. That NCT is IPM 027, The Ring Study -- ClinicalTrials.gov gives "
            "its orgStudyId as IPM 027 and its enrolment as 1959, and the object's own "
            "labels had the two trials the wrong way round. The evidence is now keyed to "
            "the trial whose paper it came from, verified against the registry rather than "
            "against the label."),
        "both_papers_are_free": (
            "No access exception was needed. ASPIRE is readable at PMC4993693 (an NIH "
            "author manuscript: free to read, no reuse licence). The Ring Study has no PMC "
            "record and isOpenAccess=N, yet Europe PMC's fullTextUrlList reports "
            "availability Free and Unpaywall reports is_oa true; the publisher PDF fetched "
            "at 590,022 bytes."),
    })

    print("label corrections: %d" % len(fixed))
    for site, n, was, now in fixed:
        print("   %-26s %s  %r -> %r" % (site, n, was, now))
    print("evidence re-assigned: %s" % built_counts)
    if not apply_changes:
        print("dry run -- pass --apply to write")
        return 0
    n = aw.write_json(path, obj)
    print("WRITTEN %d bytes, newline preserved" % n)
    return 0


if __name__ == "__main__":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.exit(main(apply_changes="--apply" in sys.argv))
