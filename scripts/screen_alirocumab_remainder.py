#!/usr/bin/env python3
"""Screen alirocumab-lipid's 81-trial remainder on the three-way disposition.

EIGHTY-ONE IS TOO MANY TO HAND-WRITE AND STILL BE AUDITABLE. So the first pass is MECHANICAL,
keyed to named registry fields, and every rule is stated below with the field it reads. What the
rules cannot settle is reported as NEEDS_ADJUDICATION rather than guessed -- a screening decision
with no named field is an opinion, and 81 opinions are worse than one.

THE CRITERIA. This object records NO eligibility block ("not recorded on the page this object was
extracted from"), so the criteria are DERIVED POST HOC from its own recorded question and
estimand, exactly as bempedoic-acid-review's were, and carry that status on their face:

    question : "In adults treated for hypercholesterolaemia, how much does alirocumab change
                calculated LDL cholesterol from baseline to week 24 compared with placebo?"
    estimand : outcomes[0].id == "ldlc_pct_change_wk24"

    P  adults treated for hypercholesterolaemia
    I  alirocumab
    C  PLACEBO
    O  LDL cholesterol change, at week 24

TWO AXES, KEPT SEPARATE. Eligibility is P/I/C. Poolability is the estimand: a trial reporting a
cardiovascular-event endpoint, or a lipid endpoint at another timepoint, is not pooling the same
quantity. Collapsing them is how eligible evidence gets recorded as though it failed a criterion.

THE THIRD STATE. A trial recruiting, not yet recruiting, suspended or withdrawn before enrolling
has NOT been assessed and rejected. Status is checked FIRST, so no trial is decided on a
contestable limb when an uncontestable one is available -- the stronger-ground rule, which an
independent adjudicator confirmed was necessary on EMPA-REPAIR.
"""
import io
import json
import os
import re
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OBJ = os.path.join(REPO, "ssot", "alirocumab-lipid", "alirocumab-lipid.json")
REM = os.environ.get("ALI_REMAINDER", os.path.join(
    "F:/claude-temp/claude/F--rapidmeta-ssot-shell/"
    "eb4d84e5-8a24-4c3b-afe2-34bd91c20bc7/scratchpad", "ali_rem.json"))

NO_RESULTS = {"RECRUITING", "NOT_YET_RECRUITING", "ACTIVE_NOT_RECRUITING",
              "SUSPENDED", "WITHDRAWN", "UNKNOWN"}

PLACEBO = re.compile(r"^\s*(matching\s+)?(placebo|sham|vehicle|dummy)\b", re.I)
# Population terms that are NOT "adults treated for hypercholesterolaemia". Read from
# conditionsModule; each is a different randomised population, not a wording variant.
OFF_POPULATION = re.compile(
    r"acute coronary|myocardial infarction|\bstroke\b|heart failure|"
    r"diabetes mellitus type 1|hiv|renal impairment|hepatic impairment|healthy",
    re.I)
# LDL-C at week 24 is the pooled quantity. Anything else is a different estimand.
LDL_MEASURE = re.compile(r"ldl|low[- ]density", re.I)
WEEK24 = re.compile(r"week\s*24|24\s*weeks?|w24", re.I)


def decide(t):
    """Return (verdict, axis, criterion, field, reason)."""
    status = (t.get("status") or "").upper()
    ivs = [str(x) for x in (t.get("ivs") or [])]
    po = " ; ".join(t.get("po") or [])
    cond = t.get("cond") or ""

    # 1. STATUS FIRST -- the stronger ground, never argued past.
    if status in NO_RESULTS:
        return ("ELIGIBLE_NO_RESULTS_YET", "STATUS", "NOT YET REPORTED",
                "statusModule.overallStatus",
                "status %s, enrolment %s -- no results to assess. Its P/I/C limbs are not "
                "argued, because an uncontestable ground is available." % (status, t.get("n")))

    # 2. COMPARATOR -- read from the CONTROL ARM, never from the intervention list.
    #
    # THE FIRST VERSION OF THIS RULE ASKED ONLY WHETHER A PLACEBO INTERVENTION EXISTED, and it
    # passed four DOUBLE-DUMMY trials as placebo-controlled. ODYSSEY MONO (NCT01644474)
    # randomises alirocumab + placebo-for-ezetimibe against ezetimibe + placebo-for-alirocumab.
    # A placebo is present in both arms -- as the BLINDING DEVICE. The comparator is EZETIMIBE.
    #
    #     THE PRESENCE OF A PLACEBO DOES NOT MEAN THE COMPARATOR IS PLACEBO.
    #
    # Same shape as the defect that caused this whole topic to be misclassified: the answer is
    # in the ARM, not in the flat list of intervention names. `active_comparators` holds every
    # control-arm drug that is neither a placebo nor also present in the experimental arm
    # (which would make it background), computed per trial rather than asserted.
    active = t.get("active_comparators") or []
    if active:
        return ("EXCLUDED", "ELIGIBILITY", "COMPARATOR",
                "armsInterventionsModule.armGroups",
                "the control arm gives %s, an ACTIVE drug absent from the experimental arm. "
                "The contrast is alirocumab vs %s, not vs placebo -- a placebo is present as "
                "the blinding device in a double-dummy design." % (active[:3], active[0]))
    has_placebo = any(PLACEBO.match(x.strip()) for x in ivs)
    if ivs and not has_placebo:
        return ("EXCLUDED", "ELIGIBILITY", "COMPARATOR",
                "armsInterventionsModule.interventions",
                "no placebo intervention is declared; interventions are %s." % (ivs[:3],))

    # 3. POPULATION.
    if OFF_POPULATION.search(cond):
        return ("EXCLUDED", "ELIGIBILITY", "POPULATION", "conditionsModule.conditions",
                "registered population is %r -- not adults treated for hypercholesterolaemia."
                % cond[:70])

    # 4. POOLABILITY -- the estimand is LDL-C change at week 24.
    if not po:
        return ("NEEDS_ADJUDICATION", "POOLABILITY", "ESTIMAND",
                "outcomesModule.primaryOutcomes",
                "no primary outcome recorded in the payload; poolability cannot be decided "
                "from a field, and is not guessed.")
    if not LDL_MEASURE.search(po):
        return ("ELIGIBLE_NOT_POOLABLE", "POOLABILITY", "ESTIMAND",
                "outcomesModule.primaryOutcomes",
                "meets P/I/C; primary is %r, which is not an LDL-cholesterol quantity."
                % po[:80])
    if not WEEK24.search(po):
        return ("ELIGIBLE_NOT_POOLABLE", "POOLABILITY", "TIMEPOINT",
                "outcomesModule.primaryOutcomes",
                "meets P/I/C and reports LDL cholesterol, but not at week 24: %r. A different "
                "timepoint is a different estimand and s10.9 bars combining them." % po[:80])
    return ("ELIGIBLE_POOLABLE_NOT_INCLUDED", "POOLABILITY", "ESTIMAND MATCHES",
            "outcomesModule.primaryOutcomes",
            "meets P/I/C AND reports LDL cholesterol at week 24: %r. THIS TRIAL COULD JOIN THE "
            "POOL and is not in the object -- flagged for review, never silently dropped."
            % po[:80])


def main():
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    with io.open(REM, encoding="utf-8") as fh:
        rem = json.load(fh)
    rows, tally = [], {}
    for t in rem:
        v, axis, crit, field, why = decide(t)
        tally[v] = tally.get(v, 0) + 1
        rows.append({"nct": t["nct"], "acronym": t.get("acr"), "verdict": v, "axis": axis,
                     "criterion": crit, "field_read": field, "reason": why})
    for k in sorted(tally):
        print("  %-32s %d" % (k, tally[k]))
    print("  %-32s %d" % ("TOTAL", len(rows)))

    flagged = [r for r in rows if r["verdict"] in
               ("ELIGIBLE_POOLABLE_NOT_INCLUDED", "NEEDS_ADJUDICATION")]
    if flagged:
        print()
        print("REQUIRING A HUMAN LOOK -- reported, never folded into a tally:")
        for r in flagged:
            print("   %s %-14s %s" % (r["nct"], r["acronym"] or "-", r["verdict"]))

    with io.open(OBJ, encoding="utf-8") as fh:
        obj = json.load(fh)
    scr = obj.setdefault("screening_of_remainder", {})
    before = set(scr.keys())
    scr["alirocumab_2026_08_19"] = {
        "screened_utc": "2026-08-19",
        "criteria_status": "DERIVED POST HOC on 2026-08-19 from this object's own recorded "
                           "question and estimand; NOT pre-specified. This object records no "
                           "eligibility block.",
        "method": "mechanical first pass keyed to named registry fields "
                  "(scripts/screen_alirocumab_remainder.py); anything the rules could not "
                  "settle is NEEDS_ADJUDICATION rather than guessed.",
        "axes_kept_separate": "ELIGIBILITY is P/I/C. POOLABILITY is the estimand "
                              "(LDL-C change at week 24). A trial can be fully eligible and "
                              "report a different quantity.",
        "status_checked_first": "The stronger-ground rule: a trial with no results is settled "
                                "on status and its contestable limbs are not argued.",
        "tally": tally,
        "trials": rows,
    }
    assert before <= set(scr.keys()), "ADDS only"
    with io.open(OBJ, "w", encoding="utf-8", newline="") as fh:
        fh.write(json.dumps(obj, indent=1, ensure_ascii=False) + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
