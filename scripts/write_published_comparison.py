"""PUBLISHED COMPARISON -- reconcile this review against the published literature.

WHY EVERY PAGE OWES ONE
    A synthesis that reports only its own result asks a reader to take the field
    on trust. One that reconciles itself against the syntheses on the same
    question -- naming what they got RIGHT as prominently as what they got wrong,
    and showing the denominator -- can be checked.

THE THREE RULES THIS ENFORCES BY CONSTRUCTION
    1. A DENOMINATOR OR IT IS NOT A FINDING. A list of failures with no count of
       what was examined is a selection, not a result. `denominator` is required
       and is computed from the checks, never typed.
    2. CONFIRMATIONS IN THE SAME TABLE, IN THE SAME DETAIL, AS ERRORS. The
       running result across this lane is that where a defect existed it was
       OURS, and the literature was right. A comparison that only had room for
       the literature's errors could not have discovered that.
    3. AN UNRESOLVED LAYER IS NAMED, NOT SILENTLY DROPPED. Where an abstract
       cannot establish what a synthesis pooled, the check says UNRESOLVED and
       says why. It is never counted as agreement.

REPLACES A HARDCODED ONE-OFF
    `add_comparison.py` was ARNI's comparison with ARNI's absolute path inside
    it. The second topic would have been a copy, and a copy is where two records
    drift. The comparisons live in DATA here; this file is only the writer.

WHAT WRITING ONE DOES NOT ESTABLISH -- written in advance
    - NOT that our value is right. Where ours and a published one differ, both
      are candidates, and each check names which side was checked against source.
    - NOT that the literature was searched completely. The denominator is one
      database and one query, and it says so.
    - NOT that a synthesis which does not name our trials excluded them.

USAGE  python scripts/write_published_comparison.py <app_id>
"""
from __future__ import annotations
import collections, io, json, os, sys

if __name__ == "__main__":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
O = collections.OrderedDict


def C(**k):
    return O(k)


# ---------------------------------------------------------------------------
# app_id -> the comparison. `checks` carry a verdict in
# CONFIRMED / ERROR / ABSENT / UNRESOLVED, and the denominator is derived.
# ---------------------------------------------------------------------------
COMPARISONS = {
 "sotagliflozin-hf": O(
  _why="This review pools two trials on a total-occurrence composite reported as a "
       "hazard ratio. The question a reader needs answered is whether the published "
       "literature reports that quantity, and whether anyone -- them or us -- got it "
       "wrong. Both halves are reported below, with the number of records screened.",
  _how_identified="PubMed E-utilities, query and counts recorded in "
       "ssot/sotagliflozin-hf/appraisal/PUBLISHED_SYNTHESIS_SCREEN.json, which "
       "carries a decision for every record. This layer is machine-screened at "
       "ABSTRACT level and the limitation is stated there and in the checks below.",
  reviews=[
   O(id="PM_BANTOUNOU2025",
     citation="Bantounou MA, et al. Meta-analysis of sotagliflozin, a dual "
              "sodium-glucose-cotransporter 1/2 inhibitor, for heart failure in type 2 "
              "diabetes. ESC Heart Fail 2025;12(2):968-979.",
     pmid="39257196", prospero="CRD42023432732",
     their_k=9, their_n=15320, their_search_closed="2023-06-02",
     scope="sotagliflozin in type 2 diabetes, any randomised design reporting heart "
           "failure events",
     how_it_differs_from_ours="It pools RELATIVE RISKS across nine studies of mixed "
       "design and reports neither trial's own primary -- a total-occurrence composite "
       "as a hazard ratio -- as a separate row. Its abstract does not name its included "
       "studies, so a trial-by-trial reconciliation against it cannot be done at this "
       "layer."),
   O(id="PM_CUREUS2024",
     citation="Sotagliflozin vs Dapagliflozin: A Systematic Review Comparing "
              "Cardiovascular Mortality. Cureus 2024.",
     pmid="37868384",
     scope="narrative systematic review comparing sotagliflozin and dapagliflozin",
     how_it_differs_from_ours="It NAMES both trials we pool -- the only record in 112 "
       "that does -- but reports no pooled estimate of its own. It therefore supplies "
       "no number to reconcile against, and is counted as located rather than as "
       "agreeing."),
  ],
  checks=[
   C(id="soloist-hr-vs-registry-results",
     what="Our SOLOIST-WHF input against the registry's POSTED RESULT",
     verdict="CONFIRMED",
     detail="The registry's results section posts, on the primary outcome whose "
            "definition we read, a hazard ratio of 0.67 with a 95% interval of 0.52 to "
            "0.85. This object stores 0.67 (0.52 to 0.85). Identical, and read from the "
            "registry's own analysis record rather than from the publication that "
            "reports it -- two independent surfaces agreeing.",
     quote="Hazard Ratio (HR) 0.67, CI 0.52 to 0.85",
     location="ClinicalTrials.gov NCT03521934, resultsSection, primary outcome analysis"),
   C(id="scored-hr-vs-registry-results",
     what="Our SCORED input against the registry's POSTED RESULT",
     verdict="CONFIRMED",
     detail="The registry posts a hazard ratio of 0.74 with a 95% interval of 0.63 to "
            "0.88 on the same primary outcome. This object stores 0.74 (0.63 to 0.88). "
            "Identical.",
     quote="Hazard Ratio (HR) 0.74, CI 0.63 to 0.88",
     location="ClinicalTrials.gov NCT03315143, resultsSection, primary outcome analysis"),
   C(id="endpoint-definitions-identical",
     what="Whether the two trials counted the same events",
     verdict="CONFIRMED",
     detail="Both registry records give the primary outcome measure in identical words, "
            "and both descriptions specify the total number of occurrences, first and "
            "potentially subsequent. This is the check SGLT2_HF failed -- there, two "
            "trials counted urgent heart-failure visits and two did not -- and here it "
            "comes back clean, on text read from the registry rather than inferred from "
            "a result sentence.",
     quote="Number of Total Occurrences of Cardiovascular (CV) Death, Hospitalizations "
           "for Heart Failure (HHF) and Urgent Visits for Heart Failure (HF)",
     location="ClinicalTrials.gov NCT03521934 and NCT03315143, primary outcome measure"),
   C(id="scored-endpoint-was-changed",
     what="Whether the amended SCORED endpoint is the one our estimate belongs to",
     verdict="CONFIRMED",
     detail="SCORED's primary end point was changed during the trial. The registry "
            "record read here is the AMENDED one, and the posted hazard ratio 0.74 sits "
            "on that amended outcome, which is the one we pool. The superseded original "
            "coprimary -- first occurrence of CV death, non-fatal myocardial infarction "
            "or non-fatal stroke -- is carried separately in this object at k=1 and is "
            "pooled with nothing. A reader who worried that an amended endpoint had been "
            "quietly substituted can see that both halves are recorded.",
     quote="The primary end point was changed during the trial to the composite of the "
           "total number of deaths from cardiovascular causes, hospitalizations for "
           "heart failure, and urgent visits for heart failure.",
     location="SCORED publication; and the amended measure on the registry record"),
   C(id="no-synthesis-reports-this-estimand",
     what="Whether any published synthesis reports the quantity we pool",
     verdict="ABSENT",
     detail="112 records matched the query and all 112 were read at abstract level. One "
            "names both trials we pool and reports no pooled estimate of its own. The "
            "drug-specific meta-analysis pools relative risks over nine mixed-design "
            "studies. No located synthesis reports a hazard ratio for the "
            "total-occurrence composite, so this pooled value cannot be checked against "
            "an external number. THAT IS A STATEMENT ABOUT THE LITERATURE, NOT A CLAIM "
            "OF NOVELTY.",
     quote=None,
     location="PUBLISHED_SYNTHESIS_SCREEN.json, 112 of 112 records read"),
   C(id="what-the-abstract-layer-cannot-settle",
     what="Whether the 107 syntheses that name no trial included ours",
     verdict="UNRESOLVED",
     detail="107 of 112 records do not name any trial we pool, and four have no indexed "
            "abstract. Abstract-level screening cannot establish what a synthesis "
            "pooled. Reporting '0 syntheses affected' from this would be absence of "
            "evidence dressed as evidence of absence -- the same error the first version "
            "of this topic's search record made, when it concluded no synthesis existed "
            "and one was found in a single step the same day. Settling it needs full "
            "text.",
     quote=None,
     location="PUBLISHED_SYNTHESIS_SCREEN.json, tally"),
   C(id="bantounou-precision-query",
     what="An unexplained precision gap in the drug-specific meta-analysis",
     verdict="UNRESOLVED",
     detail="Its printed interval 0.64 to 0.69 implies a standard error on the log scale "
            "of about 0.0192; our two-trial pool over 11,806 participants implies 0.0705. "
            "With 8,040 and 7,280 participants, an event in 10% of each arm gives 0.0485, "
            "20% gives 0.0324, and even 30% in both arms gives 0.0247 -- all wider than "
            "printed. THE STRONGEST INNOCENT EXPLANATION IS PLAUSIBLE AND IS STATED: if "
            "the pool counts total recurrent events rather than participants, counts can "
            "exceed the participant number and that precision is attainable. The abstract "
            "does not state the unit of analysis, so this is recorded for a reader and "
            "NOT asserted as an error. Full text or the PROSPERO record would settle it.",
     quote="sotagliflozin significantly reduced the risk of HF [n = 8 studies; "
           "RR = 0.66 (0.64, 0.69)]",
     location="PMID 39257196, abstract"),
  ],
  divergence_decomposed=O(
   ours="HR 0.7171 (0.6246 to 0.8234) for the total number of occurrences of CV death, "
        "HF hospitalisation and urgent HF visit, k=2, both pivotal trials.",
   theirs="RR 0.66 (0.64 to 0.69) for heart failure over 8 studies, and RR 0.73 (0.66 to "
          "0.81) for MACE over 8 studies.",
   why_they_differ="A different quantity (a relative risk of experiencing an event is "
     "not a hazard ratio for the total number of events), a different eligible set (nine "
     "mixed-design studies against the two pivotal trials), and a different question. "
     "Same direction, but direction agreement is worth little across estimands: a close "
     "answer to a different question is the most persuasive kind of wrong. NEITHER SIDE "
     "IS SHOWN TO BE IN ERROR HERE, and that is the finding."),
 ),
}


def write(app_id):
    path = os.path.join(REPO, "ssot", app_id, "%s.json" % app_id)
    if not os.path.exists(path):
        print("no object at %s -- NOT RUN" % path, file=sys.stderr)
        return 2
    cmp_ = COMPARISONS.get(app_id)
    if not cmp_:
        print("no comparison recorded for %s -- NOT RUN. This writer emits only what "
              "was actually reconciled." % app_id, file=sys.stderr)
        return 2
    checks = cmp_["checks"]
    ver = collections.Counter(c["verdict"] for c in checks)
    n = len(checks)
    # DERIVED, NEVER TYPED. A denominator typed by hand is a number that stops
    # matching the table under it the first time a row is added.
    cmp_ = O(cmp_)
    cmp_["denominator"] = O(
        rows_checked=n,
        confirmed=ver["CONFIRMED"], errors=ver["ERROR"],
        absent=ver["ABSENT"], unresolved=ver["UNRESOLVED"],
        statement="%d checks were applied and %d came back clean, %d found an error, "
                  "%d found something absent and %d could not be settled at the layer "
                  "available. The denominator is stated because a list of only the "
                  "failures is not a finding, it is a selection."
                  % (n, ver["CONFIRMED"], ver["ERROR"], ver["ABSENT"], ver["UNRESOLVED"]),
        symmetry="Confirmations are listed in the same table, in the same detail, as "
                 "errors. Across the cardiology topics reconciled so far the published "
                 "literature has been implicated in none of them: where a defect "
                 "existed it was ours. A comparison with room only for their errors "
                 "could not have found that out.")
    obj = json.loads(open(path, encoding="utf-8").read())
    obj["published_comparison"] = cmp_
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=1)
        f.write("\n")
    print("published_comparison written to %s" % path)
    print("  %d checks -> %d CONFIRMED, %d ERROR, %d ABSENT, %d UNRESOLVED"
          % (n, ver["CONFIRMED"], ver["ERROR"], ver["ABSENT"], ver["UNRESOLVED"]))
    if ver["ERROR"] == 0:
        print("  the published literature is implicated in NONE of these checks -- "
              "stated as prominently as the opposite finding would be")
    return 0


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if not args:
        print("usage: write_published_comparison.py <app_id>\nknown: %s"
              % ", ".join(sorted(COMPARISONS)), file=sys.stderr)
        return 2
    rc = 0
    for a in args:
        rc |= write(a)
    return rc


if __name__ == "__main__":
    sys.exit(main())
