#!/usr/bin/env python3
"""DO THE SECOND OF THE FOUR: RoB 2, PER OUTCOME AND PER RESULT, NEVER PER TRIAL.

WHY PER OUTCOME. RoB 2 assesses a RESULT, not a study: the same trial can be at low risk for
all-cause mortality and at high risk for a subjective endpoint measured by an unblinded
assessor. This corpus's whole character is that outcomes differ WITHIN trials -- one trial's
three-component composite is another's two-component secondary -- so a per-trial judgement
would be the wrong unit even if it were convenient.

    THE DEFAULT IS THE WHOLE POINT. Where a domain cannot be judged from the registration and
    the published report, IT IS "NO INFORMATION", NEVER "LOW". Low-by-default is precisely the
    manufacturing caught in paper-studio's `c.rob = ... || "RoB 2"` -- a default that asserts a
    fact -- and the withholding direction is no safer: HIGH-by-default would invent a defect.
    A domain we could not assess is not a domain that passed and not a domain that failed.

THE FIVE DOMAINS, and the evidence each is judged from HERE:

  D1 randomisation process
        judged from: the trial's `design` string and the registry's allocation field.
        ALLOCATION CONCEALMENT AND BASELINE IMBALANCE ARE NOT IN EITHER, so D1 can reach at
        best SOME CONCERNS on this evidence -- and that is a fact about what we can reach, not
        a criticism of the trials. Recorded as such.
  D2 deviations from intended interventions
        judged from: blinding in `design`, and `analysed_scope` for the analysis principle.
  D3 missing outcome data
        judged from: `analysed` against the randomised total. Numerically decidable, which is
        why this is the one domain that regularly reaches LOW here.
  D4 measurement of the outcome
        judged from: blinding, whether the endpoint text says ADJUDICATED, and whether the
        components are objective (death, hospitalisation) or assessor-dependent.
  D5 selection of the reported result
        judged from: `endpoint_rank_in_its_own_trial`. THIS PROJECT HAS UNUSUALLY GOOD EVIDENCE
        HERE and it cuts against us as often as for us: a result taken from a SECONDARY rank,
        selected by us because it harmonises across trials, is exactly the situation D5 exists
        to flag. It is flagged. A review that recovered a pool from secondary endpoints and
        then rated D5 low would be marking its own homework.

NO OVERALL JUDGEMENT IS SYNTHESISED WHERE ANY DOMAIN IS NO INFORMATION. RoB 2's algorithm maps
domain judgements to an overall one, but an overall rating computed over unknowns would present
absence as a result. Overall is reported as NO INFORMATION with the blocking domains named.
"""
import io
import json
import os
import re
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEST = os.path.join(REPO, "evidence", "2026-08-19-batch1", "rob2.json")

LOW, SOME, HIGH, NOINFO = "LOW", "SOME_CONCERNS", "HIGH", "NO_INFORMATION"

AUTHORITY = {
    "tool": "RoB 2 (Cochrane risk-of-bias tool for randomized trials)",
    "version": "22 August 2019 version, as reproduced in the Cochrane Handbook",
    "handbook": ("Higgins JPT, Savovic J, Page MJ, Elbers RG, Sterne JAC. Chapter 8: Assessing "
                 "risk of bias in a randomized trial. In: Cochrane Handbook for Systematic "
                 "Reviews of Interventions version 6.5.1"),
    "unit_of_assessment": ("A RESULT, not a study -- Handbook 8.2: 'risk of bias is assessed "
                           "for a specific result'. Every judgement below names its outcome."),
    "checked_on": "2026-08-19",
    "how_checked": ("The version string and chapter number were read from the object's own "
                    "`methodological_authority` block, which records the edition and the date "
                    "it was checked, rather than recalled."),
}

OBJECTIVE = ("death", "mortality", "hospitali", "stroke", "infarction", "amputation")


def _d1(trial):
    d = (trial.get("design") or "").lower()
    ev, q = [], {}
    q["allocation_sequence_random"] = "PROBABLY_YES" if "randomis" in d or "randomiz" in d else "NO_INFORMATION"
    if q["allocation_sequence_random"] != "NO_INFORMATION":
        ev.append("`design` states the trial was randomised: %r" % (trial.get("design") or "")[:90])
    # THE TWO SIGNALLING QUESTIONS WE CANNOT REACH. Named, not skipped.
    q["allocation_concealed"] = "NO_INFORMATION"
    q["baseline_imbalance_suggesting_a_problem"] = "NO_INFORMATION"
    ev.append("Allocation concealment and baseline-imbalance data are in neither the "
              "registration nor the fields this object holds.")
    return (SOME if q["allocation_sequence_random"] != "NO_INFORMATION" else NOINFO), q, ev


def _d2(trial, blinded):
    q = {"participants_aware": "PROBABLY_NO" if blinded else "NO_INFORMATION",
         "carers_aware": "PROBABLY_NO" if blinded else "NO_INFORMATION",
         "appropriate_analysis_used": "NO_INFORMATION"}
    ev = []
    if blinded:
        ev.append("`design` states double-blind, so participants and carers were probably "
                  "unaware of assignment.")
    scope = ""
    for blk in (trial.get("by_outcome") or {}).values():
        scope = (blk.get("analysed_scope") or "")
        if scope:
            break
    if re.search(r"full analysis set|intention.to.treat|randomised total", scope, re.I):
        q["appropriate_analysis_used"] = "PROBABLY_YES"
        ev.append("`analysed_scope`: %r" % scope[:110])
    return (LOW if blinded and q["appropriate_analysis_used"] == "PROBABLY_YES"
            else SOME if blinded else NOINFO), q, ev


def _d3(trial, blk):
    an = blk.get("analysed") or {}
    rand = trial.get("enrolled") or trial.get("registration_enrolment")
    q, ev = {}, []
    if an.get("treatment") is not None and an.get("control") is not None and rand:
        tot = an["treatment"] + an["control"]
        pct = 100.0 * (rand - tot) / float(rand)
        q["data_available_for_all_randomised"] = "YES" if tot >= rand else "NO"
        ev.append("analysed %d of %d randomised (%.2f%% not analysed)" % (tot, rand, pct))
        return (LOW if tot >= rand else SOME if pct < 5 else HIGH), q, ev
    q["data_available_for_all_randomised"] = "NO_INFORMATION"
    ev.append("The analysed denominators or the randomised total are not held for this result.")
    return NOINFO, q, ev


def _d4(blk, blinded):
    txt = ((blk.get("outcome_definition") or "") + " " +
           (blk.get("composite_as_this_trial_defines_it") or "")).lower()
    q, ev = {}, []
    adjudicated = "adjudicat" in txt
    objective = any(w in txt for w in OBJECTIVE)
    q["method_inappropriate"] = "PROBABLY_NO" if txt else "NO_INFORMATION"
    q["assessors_aware_of_intervention"] = "PROBABLY_NO" if (blinded or adjudicated) else "NO_INFORMATION"
    q["assessment_could_be_influenced_by_knowledge"] = "PROBABLY_NO" if objective else "NO_INFORMATION"
    if adjudicated:
        ev.append("the endpoint text states the events were ADJUDICATED")
    if objective:
        ev.append("components are objective (death and/or hospitalisation), which limits the "
                  "scope for assessor influence")
    if not txt:
        ev.append("No outcome definition is held for this result, so the measurement method "
                  "cannot be judged.")
        return NOINFO, q, ev
    return (LOW if (objective and (blinded or adjudicated)) else SOME), q, ev


def _d5(blk):
    """SELECTION OF THE REPORTED RESULT -- where this project's evidence is strongest, and
    where it most often counts AGAINST the review rather than for it."""
    rank = (blk.get("endpoint_rank_in_its_own_trial") or "").upper()
    q, ev = {}, []
    # The first signalling question asks whether the analysis was per a PRE-SPECIFIED plan. We
    # do not hold any trial's statistical analysis plan, so this is NO INFORMATION -- always,
    # and stating it is not a formality: it is the reason D5 cannot reach LOW here.
    q["analysed_per_prespecified_plan"] = "NO_INFORMATION"
    ev.append("No trial's statistical analysis plan is held, so whether this analysis was "
              "pre-specified cannot be established. D5 therefore cannot reach LOW.")
    if not rank:
        q["selected_from_multiple_eligible_measurements"] = "NO_INFORMATION"
        return NOINFO, q, ev
    q["selected_from_multiple_eligible_measurements"] = (
        "PROBABLY_YES" if "SECONDARY" in rank or "OTHER" in rank else "PROBABLY_NO")
    if "SECONDARY" in rank or "OTHER" in rank:
        ev.append("THE RESULT USED HERE IS AT %s RANK IN ITS OWN TRIAL. It was selected by "
                  "this review because it harmonises across trials -- which is exactly the "
                  "situation D5 exists to flag, and it is flagged rather than argued away. "
                  "The selection is documented in the object and is the reviewers', not the "
                  "trialists'." % rank)
        return SOME, q, ev
    ev.append("The result used here is the trial's own registered PRIMARY, so no selection "
              "among ranks was made by this review.")
    return SOME, q, ev


def assess(topic):
    p = os.path.join(REPO, "ssot", topic, topic + ".json")
    with io.open(p, encoding="utf-8") as fh:
        obj = json.load(fh)
    out = {}
    pooled_ids = {oid for oid, b in ((obj.get("results") or {}).get("by_outcome") or {}).items()
                  if ((b or {}).get("pooled") or {}).get("point") is not None}
    for t in ((obj.get("inputs") or {}).get("trials") or []):
        ident = t.get("nct") or t.get("id")
        blinded = bool(re.search(r"double.blind|triple.blind|quadruple", t.get("design") or "", re.I))
        for oid, blk in (t.get("by_outcome") or {}).items():
            doms = {}
            for name, fn in (("D1_randomisation", lambda: _d1(t)),
                             ("D2_deviations", lambda: _d2(t, blinded)),
                             ("D3_missing_outcome_data", lambda: _d3(t, blk)),
                             ("D4_measurement", lambda: _d4(blk, blinded)),
                             ("D5_selection_of_result", lambda: _d5(blk))):
                j, q, ev = fn()
                doms[name] = {"judgement": j, "signalling_questions": q, "evidence": ev}
            blockers = [k for k, v in doms.items() if v["judgement"] == NOINFO]
            overall = (NOINFO if blockers else
                       HIGH if any(v["judgement"] == HIGH for v in doms.values()) else
                       SOME if any(v["judgement"] == SOME for v in doms.values()) else LOW)
            out.setdefault(oid, {})[ident] = {
                "trial": t.get("name") or ident,
                "domains": doms,
                "overall": overall,
                "overall_note": (
                    ("NO OVERALL JUDGEMENT IS SYNTHESISED because %s could not be assessed. "
                     "RoB 2's algorithm maps domains to an overall rating, but an overall "
                     "computed over unknowns would present absence as a result."
                     % ", ".join(blockers)) if blockers else
                    "Synthesised from the five domain judgements, none of which is NO_INFORMATION."),
                "contributes_to_a_pooled_estimate": oid in pooled_ids,
            }
    return out


def main():
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    topics = sys.argv[1:] or ["sglt2-hf", "iv-iron-hf", "alirocumab-lipid", "attr-cm-review",
                              "bempedoic-acid-review", "ablation-af-heart-failure",
                              "ablation-af-medical-therapy"]
    all_out, tally = {}, {}
    for t in topics:
        try:
            r = assess(t)
        except Exception as exc:                    # noqa: BLE001 - reported, never silent
            print("%-30s NOT_ASSESSABLE (%s)" % (t, exc))
            continue
        all_out[t] = r
        n = sum(len(v) for v in r.values())
        for oid, per in r.items():
            for _i, rec in per.items():
                tally[rec["overall"]] = tally.get(rec["overall"], 0) + 1
                for dn, dv in rec["domains"].items():
                    tally[dn + ":" + dv["judgement"]] = tally.get(dn + ":" + dv["judgement"], 0) + 1
        print("%-30s %d outcome(s), %d result-level assessments" % (t, len(r), n))
    print("\nOVERALL, ACROSS ALL RESULT-LEVEL ASSESSMENTS")
    for k in (LOW, SOME, HIGH, NOINFO):
        print("   %-16s %d" % (k, tally.get(k, 0)))
    print("\nPER DOMAIN")
    for d in ("D1_randomisation", "D2_deviations", "D3_missing_outcome_data",
              "D4_measurement", "D5_selection_of_result"):
        row = "   %-26s" % d
        for k in (LOW, SOME, HIGH, NOINFO):
            row += " %s=%-3d" % (k[:4], tally.get(d + ":" + k, 0))
        print(row)
    payload = {"assessed_utc": "2026-08-19", "authority": AUTHORITY,
               "default_rule": ("A domain that cannot be judged from the registration and the "
                                "published report is NO_INFORMATION, never LOW. Low-by-default "
                                "asserts a fact; high-by-default invents a defect."),
               "by_topic": all_out}
    with io.open(DEST, "w", encoding="utf-8") as fh:
        fh.write(json.dumps(payload, indent=1))
    print("\nwrote %s" % DEST)
    return 0


if __name__ == "__main__":
    sys.exit(main())
