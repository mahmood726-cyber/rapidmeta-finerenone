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
        JUDGED FROM THE TRIAL'S OWN SELECTION, NOT FROM OURS -- see `_d5`, which declares the
        position and cites the section it rests on. An earlier version of this paragraph said
        the opposite, and said it confidently: that a result taken from a SECONDARY rank,
        selected by US because it harmonises across trials, "is exactly the situation D5
        exists to flag. It is flagged." That was a position on a contested question, taken
        without declaring that the question was contested, and it is withdrawn.
        OUR OWN SELECTION IS STILL A RISK AND IT IS STILL REPORTED -- as a DECLARATION beside
        the estimate (`our_selection_declared_not_rated`), never as a domain judgement, which
        would misdescribe a property of this review as a property of the trial.

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


D5_POSITION = (
    "DOMAIN 5 ASSESSES THE TRIAL'S SELECTION AMONG ITS OWN RESULTS, NOT THIS REVIEW'S "
    "SELECTION AMONG THE TRIAL'S REPORTED RESULTS. Cochrane Handbook 6.5.1 section 8.7 "
    "scopes domain 5 to selective reporting BY THE TRIAL AUTHORS; selection performed by a "
    "review in assembling its synthesis is a review-level matter and RoB 2 has no domain "
    "for it, because the tool assesses trials and not reviews. This review's own selection "
    "among the results a trial reported is therefore DECLARED beside the estimate and is "
    "NOT folded into any domain judgement. Folding it in would record a property of this "
    "review as though it were a property of the trial, which is a factual error about the "
    "trial in the accusing direction.")

D5_POSITION_WITHDRAWN = (
    "An earlier version of this function implemented the opposite position WITHOUT "
    "DECLARING IT: it set signalling question 5.2 to PROBABLY_YES whenever the result used "
    "here sat at SECONDARY or OTHER rank, on the ground that the rank was chosen by this "
    "review -- while stating in its own evidence text that the selection was 'the "
    "reviewers', not the trialists''. That is question 5.2 answered about the reviewers and "
    "then attributed to the trial. It reached 4 stored records, all in `iv-iron-hf`, and "
    "reached ZERO bytes of any delivered page. It is withdrawn here, and the withdrawal is "
    "recorded rather than the code quietly changing under an unchanged docstring.")


def _selection_declaration(blk, row=None):
    """PROJECT this review's own selection from what the object already holds. NEVER RATE IT.

    THIS IS A PROJECTION AND A LOOKUP, NOT A JUDGEMENT. It reads one stored field,
    `endpoint_rank_in_its_own_trial`, and reports what it says. Where the field is absent
    the state is COULD_NOT_DETERMINE and the absence is named as A MISSING FIELD, because
    the alternative -- writing a sentence about which result was selected and why, from an
    object that records neither -- is invention with a declaration's authority.

    THREE STATES, NEVER TWO. A row whose rank field is missing is not a row where no
    selection happened. It is a row where the selection is unrecorded.

    THE CORPUS RECORDS THIS RANK ON TWO LAYERS AND THE FIRST VERSION OF THIS READ ONE.
    `inputs.trials[].by_outcome[]` is what the assessor walks; `results.by_outcome[].per_trial[]`
    is what the page renders. Reading only the first declared 11 of 29 records
    COULD_NOT_DETERMINE while the object held the answer one layer away -- and one of the 11
    was `alirocumab-lipid` / NCT01507831, a genuine SECONDARY, so a real selection risk was
    reported as unknown. That is the worst available direction for this particular error.

    Both layers are now read. Where both hold a value they are COMPARED, not merged: the
    layers agree on all 14 records where both are present today, and an instrument that
    silently prefers one would not tell anybody the day they stop agreeing.
    """
    rank = blk.get("endpoint_rank_in_its_own_trial")
    row_rank = (row or {}).get("endpoint_rank_in_its_own_trial")
    d = {"assessed_by_rob2": False,
         "why_not_rated": (
             "This is a selection made by THIS REVIEW. Under the position declared in "
             "`D5_POSITION` it is reported and not rated, because RoB 2 assesses trials.")}
    if rank is not None and row_rank is not None and str(rank).strip() != str(row_rank).strip():
        d["state"] = "LAYERS_DISAGREE"
        d["read_from"] = "both layers, which do not agree"
        d["rank_verbatim_inputs_layer"] = rank
        d["rank_verbatim_rendered_layer"] = row_rank
        d["statement"] = (
            "THIS OBJECT RECORDS TWO DIFFERENT ANSWERS to which of the trial's results this "
            "row uses. The layer the assessor walks says %r; the layer the page renders says "
            "%r. NO DECLARATION IS COMPOSED FROM EITHER. One of them is wrong and this "
            "instrument cannot tell which, so it reports the disagreement, which is a finding "
            "about the object rather than a statement about the trial."
            % (str(rank)[:200], str(row_rank)[:200]))
        return d
    if rank is None and row_rank is not None:
        rank, layer = row_rank, ("results.by_outcome[].per_trial[] -- the layer the page "
                                 "renders; absent from the layer the assessor walks")
    elif rank is not None and row_rank is None:
        layer = ("inputs.trials[].by_outcome[] -- the layer the assessor walks; absent from "
                 "the layer the page renders")
    elif rank is not None:
        layer = "both layers, which agree"
    else:
        layer = None
    if rank is not None:
        d["read_from"] = layer
    if rank is None:
        d["state"] = "COULD_NOT_DETERMINE"
        d["statement"] = (
            "WHICH OF THE TRIAL'S RESULTS THIS ROW USES IS NOT RECORDED ON THIS OBJECT. The "
            "field that would say so, `endpoint_rank_in_its_own_trial`, is absent from this "
            "result's block. That is a MISSING FIELD, reported as missing. It is not a "
            "statement that no selection was made, and no statement about the selection is "
            "composed from anything else.")
        d["missing_field"] = ("endpoint_rank_in_its_own_trial, absent from BOTH layers that "
                              "carry it: inputs.trials[].by_outcome[] and "
                              "results.by_outcome[].per_trial[]")
        return d
    low = str(rank).strip().lower()
    # The corpus writes this rank two ways -- a bare token and a sentence. Both are read.
    # Matching only one attributed 23 of the trials' own primary endpoints to this review's
    # selection in a sibling instrument; the bare token is matched EXACTLY because
    # "SECONDARY -- this trial's only primary outcome is ..." contains the word "primary".
    theirs = low in ("primary", "primary endpoint", "primary outcome") or "own primary" in low
    d["rank_verbatim"] = rank
    if theirs:
        d["state"] = "NO_SELECTION_BY_THIS_REVIEW"
        d["statement"] = (
            "THE RESULT ON THIS ROW IS THE TRIAL'S OWN PRIMARY, as the object records its "
            "rank: %r. This review selected no result the trial did not itself designate "
            "first, so there is nothing on this axis to declare." % rank)
        return d
    d["state"] = "SELECTED_BY_THIS_REVIEW"
    d["statement"] = (
        "THE RESULT ON THIS ROW IS NOT THE TRIAL'S OWN PRIMARY. The object records its rank "
        "in its own trial as: %r. This review used it because it is the quantity that "
        "harmonises across the trials pooled here. THAT CHOICE IS OURS, it carries a real "
        "risk that a differently-chosen result would give a different answer, and it is "
        "stated here rather than rated, because rating it under domain 5 would record it as "
        "something the trial did." % rank)
    d["what_would_bound_it"] = (
        "Extracting every result this trial reports for this outcome domain and showing what "
        "the pool does under each. That is not held for any trial in this object, so the "
        "size of this risk is UNMEASURED rather than small.")
    return d


def _d5(blk):
    """SELECTION OF THE REPORTED RESULT -- THE TRIAL'S SELECTION. The position is declared in
    `D5_POSITION`; the position this replaces is recorded in `D5_POSITION_WITHDRAWN`.

    All three signalling questions are emitted, including 5.3, which no earlier version
    collected at all. An uncollected question that is simply absent is indistinguishable
    from one that was answered reassuringly; emitted as NO_INFORMATION it is neither.
    """
    q, ev = {}, []
    # 5.1 -- was the analysis per a PRE-SPECIFIED plan. No trial's statistical analysis plan
    # is held, so this is NO INFORMATION, always. Stating it is not a formality: it is the
    # reason D5 cannot reach LOW here, and the reason is a fact about our reach.
    q["analysed_per_prespecified_plan"] = "NO_INFORMATION"
    ev.append("No trial's statistical analysis plan or protocol is held, so whether this "
              "analysis followed a pre-specified plan cannot be established. D5 therefore "
              "cannot reach LOW, and that is a bound on our access rather than a finding "
              "about the trial.")
    # 5.2 -- did THE TRIAL select this result from among multiple eligible MEASUREMENTS, on
    # the basis of the results. The object holds what the trial REGISTERED; it does not hold
    # what the trial REPORTED for this outcome domain, and the question turns on the gap
    # between those two. Answering it would be a reading of the trial's report that nobody
    # has done, so it is NO INFORMATION and the missing input is named.
    q["trial_selected_from_multiple_eligible_measurements"] = "NO_INFORMATION"
    ev.append("Whether THE TRIAL selected this result from among several measurements it "
              "could have reported for this outcome domain is not established. The object "
              "holds the trial's REGISTERED outcome list; it does not hold which of those "
              "the trial's own report presents, and the question turns on that gap. "
              "Establishing it requires reading the trial's report against its "
              "registration -- work that has not been done for any trial here.")
    # 5.3 -- did THE TRIAL select from among multiple eligible ANALYSES. Not collected
    # anywhere in this corpus. Emitted so that its absence is visible.
    q["trial_selected_from_multiple_eligible_analyses"] = "NO_INFORMATION"
    ev.append("Whether THE TRIAL selected this result from among several eligible analyses "
              "of the same data is not collected anywhere in this corpus for any trial. It "
              "is emitted as NO INFORMATION rather than omitted, because an omitted "
              "question cannot be told apart from a reassuringly answered one.")
    ev.append(D5_POSITION)
    # Table 14 of the tool. No answer is Y/PY, so the HIGH rows (5.2 Y/PY, or 5.3 Y/PY) do
    # not fire; 5.1 is not Y/PY, so LOW is unavailable. SOME CONCERNS is what the table
    # gives. This is the same value the withdrawn implementation returned on both of its
    # branches -- it was accidentally right for this position and wrong for its own.
    return SOME, q, ev


def assess(topic):
    p = os.path.join(REPO, "ssot", topic, topic + ".json")
    with io.open(p, encoding="utf-8") as fh:
        obj = json.load(fh)
    out = {}
    # THE RENDERED LAYER, INDEXED SO THE DECLARATION CAN READ IT TOO. The rank this review's
    # selection turns on is recorded on two layers: the one walked below, and the `per_trial`
    # rows the page actually renders. Reading only the first reported 11 of 29 records as
    # "not recorded" while the object held the answer here.
    rendered_rows = {}
    for _oid, _b in ((obj.get("results") or {}).get("by_outcome") or {}).items():
        for _r in ((_b or {}).get("per_trial") or []):
            if isinstance(_r, dict):
                for _k in (_r.get("nct"), _r.get("trial_id")):
                    if _k:
                        rendered_rows[(_oid, _k)] = _r
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
                # OUR OWN SELECTION, DECLARED AND NOT RATED. It sits at RECORD level rather
                # than inside `domains` deliberately: a reader or a downstream projector that
                # walks `domains` must not be able to pick this up as a sixth domain, and a
                # tally over domain judgements must not be able to count it as one.
                "our_selection_declared_not_rated": _selection_declaration(
                    blk, rendered_rows.get((oid, ident)) or rendered_rows.get((oid, t.get("id")))),
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
               # THE D5 RULE, CARRIED IN THE ARTEFACT AND NOT ONLY IN THE SOURCE. A position
               # taken in a docstring is a position the reader of the output cannot see.
               "d5_scope_rule": {
                   "position": D5_POSITION,
                   "handbook_section": "8.7",
                   "review_level_selection_goes_to": (
                       "Chapter 13 (assessing risk of bias due to missing results in a "
                       "synthesis) for the synthesis-level question, and to an explicit "
                       "DECLARATION beside each affected estimate for the per-result "
                       "question, which is `our_selection_declared_not_rated` on every "
                       "record below."),
                   "position_withdrawn": D5_POSITION_WITHDRAWN,
                   "decided_by": "Mahmood, 2026-08-24, on escalation E1 from the RoB 2 lane.",
               },
               "default_rule": ("A domain that cannot be judged from the registration and the "
                                "published report is NO_INFORMATION, never LOW. Low-by-default "
                                "asserts a fact; high-by-default invents a defect."),
               # THE CEILING, STATED SO IT CANNOT BE MISREAD AS A VERDICT ON THE TRIALS.
               # Without this sentence every page implies these trials are worse than they may
               # be -- which is the SAME manufacturing as a low-by-default, pointed the other
               # way. A rating driven by our reach must say it is driven by our reach.
               "ceiling": {
                   "no_result_can_reach_LOW": True,
                   "statement": (
                       "NO RESULT IN THIS REVIEW CAN REACH LOW RISK OF BIAS ON THE EVIDENCE WE "
                       "CAN REACH, AND THAT IS A FACT ABOUT OUR ACCESS RATHER THAN ABOUT THE "
                       "TRIALS. The two domains that would distinguish LOW from SOME CONCERNS "
                       "need documents this review does not hold: D1 needs allocation "
                       "concealment and baseline data, which are in neither the registration "
                       "nor the published abstract; D5 needs the trial's statistical analysis "
                       "plan, which is not held for any trial. SOME CONCERNS IS THEREFORE THE "
                       "CEILING, NOT A FINDING. A trial rated SOME CONCERNS here may well be "
                       "at low risk of bias -- we cannot show it, and we do not imply the "
                       "opposite."),
                   "what_would_change_it": (
                       "Retrieving each trial's full published report and its statistical "
                       "analysis plan or protocol. Until then the rating is bounded by what we "
                       "read, and the bound is reported rather than the reader inferring it."),
                   "why_this_is_stated_rather_than_left_implicit": (
                       "A rating of SOME CONCERNS with no explanation reads as a judgement "
                       "against the trial. Omitting the reason would manufacture a criticism "
                       "exactly as a low-by-default manufactures a reassurance -- the same "
                       "defect pointed the other way."),
               },
               "by_topic": all_out}
    # MERGE, NEVER OVERWRITE. Running this with a single topic argument OVERWROTE the file with
    # that one topic and silently discarded the other seven -- committed by the author of the
    # merge-never-write rule, one hour after writing it, in the instrument that enforces it.
    # A rule you have written is not a rule you have applied.
    if os.path.exists(DEST):
        try:
            with io.open(DEST, encoding="utf-8") as fh:
                prev = json.load(fh)
            merged = dict(prev.get("by_topic") or {})
            merged.update(all_out)
            lost = set(prev.get("by_topic") or {}) - set(merged)
            if lost:
                print("REFUSED: merge would drop %s" % ", ".join(sorted(lost)))
                return 1
            payload["by_topic"] = merged
            print("merged with %d existing topic(s); %d now recorded"
                  % (len(prev.get("by_topic") or {}), len(merged)))
        except Exception as exc:                    # noqa: BLE001 - reported, never silent
            print("REFUSED: existing %s could not be read (%s). Not overwriting it."
                  % (DEST, exc))
            return 1
    with io.open(DEST, "w", encoding="utf-8") as fh:
        fh.write(json.dumps(payload, indent=1))
    print("\nwrote %s" % DEST)
    return 0


if __name__ == "__main__":
    sys.exit(main())
