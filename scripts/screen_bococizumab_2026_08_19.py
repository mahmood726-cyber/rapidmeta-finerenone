#!/usr/bin/env python3
"""EXECUTE THE SEARCH `bococizumab-lipid-review` HAS NEVER HAD, AND SCREEN ITS REMAINDER TO ZERO.

WHAT WAS ALREADY DONE, AND WHAT WAS NOT. The re-analysis is complete and sound: the page once
carried an ODDS RATIO built from an undocumented dichotomisation of a continuous endpoint --
its stored counts implied a 91 per cent 'event' rate in placebo -- and it was replaced by the
registry's own least-squares mean differences on the primary all five trials actually register,
MD -55.46 (-58.84 to -52.07) percentage points. That work stands and is not repeated here.

WHAT THE OBJECT SAYS ABOUT EVERYTHING ELSE IS THE REASON THIS SCRIPT EXISTS:

    "search":    "not recorded on the page this object was built from"
    "screening": "not recorded on the page this object was built from"
    "eligibility": "not recorded on the page this object was built from"

A REVIEW WITH A CORRECTED ESTIMATE AND NO SEARCH IS NOT A CORRECTED REVIEW. Its five trials
are the five somebody once put on a page; nothing establishes that they are the five the
question has. This runs the search, counts k at every stage, and screens the whole candidate
pool to a disposition.

THE WITHHOLDING QUESTION, DETECTED STRUCTURALLY AND NOT BY KEYWORD (P33). A percent-change-in-
LDL outcome is *an LDL term plus a change term*, which is what the endpoint IS. Searching for
the phrase "Percent Change From Baseline in Fasting Low Density Lipoprotein Cholesterol (LDL-C)
at Week 12" would find the five trials that already agree and nothing else -- the method that
made eight apixaban trials look poolable when three were.

AND IDENTITY IS DECIDED BY A DECLARED TERM SET, NEVER BY SUBSTRING CONTAINMENT OVER CLINICAL
TEXT (P14). `topic_identity.TOPIC_SYNONYMS['bococizumab']` carries the development codes --
`pf-04950615`, `rn316` -- because ELEVEN of the twenty-two surfaced registrations name the drug
by a code and not by its name. A screen matching "bococizumab" would have found half of them.

USAGE:  python scripts/screen_bococizumab_2026_08_19.py
        python scripts/screen_bococizumab_2026_08_19.py --selftest
"""
import io
import json
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, "ssot"))
import ctgov_transport as X                                              # noqa: E402
import topic_identity as TI                                             # noqa: E402

DEST = os.path.join(REPO, "evidence", "2026-08-19-batch1", "bococizumab_screening.json")

# The 22 surfaced by the executed search, named individually so the list is a RECORD rather
# than a query result that could change under us between runs.
SURFACED = [
    "NCT00991159", "NCT01163851", "NCT01243151", "NCT01342211", "NCT01350141",
    "NCT01435382", "NCT01592240", "NCT01720537", "NCT01968954", "NCT01968967",
    "NCT01968980", "NCT01975376", "NCT01975389", "NCT02043301", "NCT02055976",
    "NCT02100514", "NCT02135029", "NCT02458209", "NCT02458287", "NCT02524106",
    "NCT02667223", "NCT02947334",
]
INCLUDED = ["NCT01968967", "NCT02100514", "NCT01968954", "NCT02458287", "NCT02135029"]

# ---- DECLARED TERM SETS. Enumerated, not inferred, and each is a criterion limb. -----------
# POPULATION: the lipid disorder this review is about. `Healthy` is NOT in it, and that is the
# limb that removes the pharmacology programme.
LIPID_CONDITION = {
    "hypercholesterolemia", "hypercholesterolaemia", "dyslipidemia", "dyslipidaemia",
    "dyslipidemias", "hyperlipidemia", "hyperlipidaemia", "hyperlipidemias",
    "primary hyperlipidemia or mixed dyslipidemia", "mixed dyslipidemia",
    "heterozygous familial hypercholesterolemia", "lipid metabolism disorders",
}
# A trial whose ONLY condition is one of these is not in this review's population.
NON_LIPID_ONLY = {"healthy", "cardiovascular disease"}

# ESTIMAND, structurally: an LDL term AND a change term, in one outcome measure.
LDL_TERMS = ("ldl", "low density lipoprotein", "low-density lipoprotein")
CHANGE_TERMS = ("percent change", "percentage change", "change from baseline", "% change",
                "percent reduction")


def norm(s):
    return " ".join((s or "").lower().replace("–", "-").split())


def ranks(ps):
    """[(rank, measure, description)] over EVERY registered rank.

    CORRECTED 2026-09-04. THIS RETURNED (rank, measure) AND NOTHING ELSE, AND THAT COST A ROW.
    B-HIVE (NCT02524106) registers its primary under the TITLE "Change of LDL-C From Baseline to
    Week 12" -- an LDL term, but no contiguous change term, so `is_ldl_pct_change` said no. The
    `description` on the same record reads "The primary endpoint for the study is the percent
    change from baseline in fasting LDL-C at week 12", which is EXACTLY this object's estimand.
    The row was stored as ELIGIBLE_NOT_POOLABLE on "no LDL percent-change outcome at ANY of 2
    registered ranks" -- an assertion that the record itself contradicts, in the withholding
    direction.

        A REGISTERED OUTCOME IS THE TITLE **AND** THE DESCRIPTION. Reading one of them and
        reporting an absence is reporting an absence you did not look for.

    The docstring below used to say "STRUCTURAL ... not the registered phrase (P33)". That was
    true and insufficient: it de-phrased the match INSIDE the title and left the title as the
    only text it ever saw. Structural about the wrong string is still structural.
    """
    om = ps.get("outcomesModule") or {}
    out = []
    for rank, key in (("PRIMARY", "primaryOutcomes"), ("SECONDARY", "secondaryOutcomes"),
                      ("OTHER", "otherOutcomes")):
        for o in (om.get(key) or []):
            out.append((rank, o.get("measure") or "", o.get("description") or ""))
    return out


def is_ldl_pct_change(measure, description=""):
    """STRUCTURAL: an LDL term plus a change term, over TITLE **AND** DESCRIPTION together.

    Joined with a separator so a term cannot be manufactured across the boundary between the
    two fields -- an LDL term in the title plus a change term in the description is a real hit,
    but neither is allowed to complete a phrase that spans them.
    """
    m = norm(measure) + " || " + norm(description)
    return any(t in m for t in LDL_TERMS) and any(t in m for t in CHANGE_TERMS)


def screen(nct, study):
    """(disposition, failing_limbs, evidence) -- EVERY failing limb, never the first (P15)."""
    ps = study.get("protocolSection") or {}
    ident = ps.get("identificationModule") or {}
    dm = ps.get("designModule") or {}
    conds = [norm(c) for c in ((ps.get("conditionsModule") or {}).get("conditions") or [])]
    rk = ranks(ps)
    hits = [(r, m, d) for (r, m, d) in rk if is_ldl_pct_change(m, d)]
    ev = {
        "brief_title": (ident.get("briefTitle") or "")[:120],
        "conditions": conds,
        "phase": dm.get("phases"),
        "allocation": (dm.get("designInfo") or {}).get("allocation"),
        "primary_purpose": (dm.get("designInfo") or {}).get("primaryPurpose"),
        "enrolment": (dm.get("enrollmentInfo") or {}).get("count"),
        "status": (ps.get("statusModule") or {}).get("overallStatus"),
        "has_results": bool(study.get("hasResults")),
        "n_ranks_read": len(rk),
        # `found_in` records WHICH field carried the match, so a reader can see at a glance
        # whether a title-only detector would have found it. On B-HIVE it is "description".
        "ldl_pct_change_at_ranks": [
            {"rank": r, "measure": m[:140], "description": d[:240],
             "found_in": ("title" if is_ldl_pct_change(m) else "description")}
            for r, m, d in hits],
    }

    fails = []
    # POPULATION -- a lipid disorder, read from the coded conditions list.
    if not any(c in LIPID_CONDITION for c in conds):
        fails.append(("POPULATION",
                      "declares no lipid-disorder condition; conditions are %r" % conds))
    # INTERVENTION -- bococizumab in the randomised contrast, by the declared synonym set and
    # the placebo discriminator. `Placebo for Bococizumab` is NOT the drug.
    #
    # THE SYNONYM **LIST**, NEVER THE TOPIC NAME. `locate(study, syns)` tests
    # `any(s in blob for s in syns)`, and a STRING is a sequence of characters -- so
    # `locate(study, "bococizumab")` asks whether the arm text contains the letter "b", or
    # "o", or "c". Every arm in every trial matched. It raised nothing, returned no null and
    # produced a complete, plausible set of verdicts:
    #
    #     17 experimental / 0 comparator / 0 background / 5 not-assessable, and SPIRE-SI --
    #     one of this review's own five included trials -- EXCLUDED on INTERVENTION, because
    #     the ATORVASTATIN arm "contained bococizumab" on the strength of its letters.
    #
    # A wrong answer wearing a correct answer's shape, running toward WITHHOLDING, and caught
    # only because a known included trial fell out. It is the E1 family -- substring is not
    # identity -- one level below the level E1 describes: not a substring of a drug NAME, a
    # substring of nothing at all.
    role = TI.locate(study, TI.TOPIC_SYNONYMS["bococizumab"])
    role_name = role[0] if isinstance(role, (list, tuple)) else role
    ev["arm_role"] = role_name
    ev["arm_role_evidence"] = (role[1] if isinstance(role, (list, tuple)) and len(role) > 1
                               else None)
    # AN UNREADABLE ROLE IS NOT A FAILED ROLE. The first version appended an INTERVENTION
    # failure whenever the role was not experimental-or-comparator, which swept
    # `not_assessable` into EXCLUDED and put NCT01243151 out of this review on the strength of
    # a field nobody could read. Absent / empty / unreadable is NOT_ASSESSABLE, never FAIL.
    if role_name == "not_assessable":
        ev["role_unreadable"] = True
    elif role_name not in ("experimental", "comparator"):
        fails.append(("INTERVENTION",
                      "bococizumab is not in the randomised contrast: arm role %r"
                      % role_name))

    # COMPARATOR -- IS THERE ANYTHING IN THIS TRIAL THAT IS NOT THE TOPIC DRUG?
    #
    # THE FIRST VERSION READ ARM `type` AND THAT IS A REGISTRANT'S CONVENTION, which this
    # project has now been bitten by four times in two directions. NCT01592240 is a
    # placebo-controlled dose-ranging trial whose TWO arms are BOTH typed EXPERIMENTAL, each
    # carrying `Drug: PBO` beside the active doses -- the placebo is inside both arms because
    # the registrant collapsed a dosing-schedule factor into the arm structure. Read by type it
    # has no comparator; read by what the arms RECEIVE it plainly does.
    #
    # So the limb asks what is received, and it still excludes: NCT01435382 attaches
    # `Biological: PF-04950615` to all four of its arms and NOTHING ELSE. That trial really is
    # uncontrolled, and a comparator limb that stopped excluding it would not be a fixed limb.
    arms = (ps.get("armsInterventionsModule") or {}).get("armGroups") or []
    intr_names = [str(i.get("name") or "")
                  for i in ((ps.get("armsInterventionsModule") or {}).get("interventions")
                            or [])]
    types = {a.get("type") for a in arms}
    ev["arm_types"] = sorted(t for t in types if t)
    ev["intervention_names"] = intr_names
    # A PLACEBO FOR THE TOPIC DRUG IS NOT THE TOPIC DRUG -- IT IS THE COMPARATOR.
    #
    # SPIRE-AI names its control interventions `Bococizumab 150mg placebo` and
    # `Bococizumab 75mg placebo` -- the TRAILING-placebo convention. Testing whether a synonym
    # is a substring of the name calls those records the drug, so every intervention in the
    # trial "is bococizumab", the trial has nothing to be compared against, and ANOTHER of this
    # review's own five included trials falls out. E1 again, in the same script, two limbs
    # apart: the first was a substring of nothing, this one is a substring of the drug's own
    # name inside the name of its placebo.
    #
    # AND THE FIRST DISCRIMINATOR REACHED FOR WAS THE WRONG ONE, which the known-answer suite
    # caught and the RESULT did not. `_name_is_placebo_record` implements the LEADING anchor
    # only -- `Placebo for Bococizumab` yes, `Bococizumab 150mg placebo` NO -- and SPIRE-AI
    # passed anyway, on the arm-TYPE half of the disjunction below. The verdict was right and
    # the reason written beside it was false. `_names_a_placebo` is the function that carries
    # the trailing convention, and it is the one this limb needs.
    syns = TI.TOPIC_SYNONYMS["bococizumab"]
    non_topic = [n for n in intr_names
                 if TI._names_a_placebo(n.split(":", 1)[-1])
                 or not any(s in norm(n) for s in syns)]
    typed_control = sorted(t for t in types
                           if t and any(k in t.upper() for k in
                                        ("COMPARATOR", "PLACEBO", "SHAM", "NO_INTERVENTION")))
    ev["non_topic_interventions"] = non_topic
    ev["comparator_typed_arms"] = typed_control
    # EITHER signal is enough, and it takes BOTH to fail. Read by TYPE alone, NCT01592240 --
    # placebo-controlled, `Drug: PBO` in both its arms -- has no comparator, because the
    # registrant typed both arms EXPERIMENTAL. Read by INTERVENTION NAME alone, NCT01243151 --
    # "Placebo-controlled" in its own title -- has none either, because its placebo arm carries
    # no intervention record at all. Each limb is blind to a real design the other sees.
    if not arms:
        ev["comparator"] = "NOT_ASSESSABLE -- the registration declares no armGroups at all"
        ev["comparator_unreadable"] = True
    elif not non_topic and not typed_control:
        fails.append(("COMPARATOR",
                      "no arm is typed as a comparator AND every intervention record is the "
                      "topic drug (%r). Neither reading finds anything for it to be compared "
                      "against." % intr_names))
    # ESTIMAND -- poolability, NOT eligibility. Reported separately, and it never excludes.
    if not hits:
        ev["estimand"] = "no LDL percent-change outcome at ANY of %d registered ranks" % len(rk)
    else:
        ev["estimand"] = "LDL percent-change outcome at %s" % ", ".join(
            sorted({r for r, _m in hits}))

    if fails:
        return "EXCLUDED", fails, ev
    if ev.get("role_unreadable") or ev.get("comparator_unreadable"):
        return "NOT_ASSESSABLE", [], ev
    # POOLABILITY, WHICH IS NOT ELIGIBILITY, and both are reported.
    #
    # A PHASE-1 DOSE-ESCALATION OR PHARMACOKINETIC DESIGN IS IN SCOPE AND CONTRIBUTES NO
    # EFFECT ESTIMATE. This is not a criterion written backwards from a wanted included set:
    # it is the same rule `apixaban-vte-treatment` applied to NCT01195727, a 13-patient
    # paediatric multiple-dose study -- "in scope by population; a dose-finding design that
    # will not contribute an effect estimate". Stated as poolability, so the trial stays
    # visible as eligible rather than disappearing into the exclusions.
    phases = ev.get("phase") or []
    if "PHASE1" in phases:
        ev["poolability"] = ("PHASE 1 dose-escalation / pharmacokinetic design. In scope by "
                             "population and by intervention; it does not estimate an effect "
                             "on this review's endpoint.")
        return "ELIGIBLE_NOT_POOLABLE", [], ev
    if not hits:
        return "ELIGIBLE_NOT_POOLABLE", [], ev
    if not study.get("hasResults"):
        return "ELIGIBLE_NO_RESULTS_YET", [], ev
    if nct in INCLUDED:
        return "INCLUDED", [], ev
    return "ELIGIBLE_POOLABLE_NOT_INCLUDED", [], ev


def main():
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    # THE CASCADE KEYS ARE `locate()`'s OWN VOCABULARY, NOT A PARAPHRASE OF IT.
    #
    # The first version keyed on "background" while locate returns
    # `background_or_coadministered`, and the counter's fallback swept every background trial
    # into `not_assessable`. It printed `background 0 / not_assessable 5` over a set containing
    # two genuine background trials -- MERGING TWO DIFFERENT ABSENCES, which this registry
    # already names as a class: "these three states must never be summed". The zero read as a
    # finding and it was an artefact of a key that did not exist.
    rows, tally = [], {}
    cascade = {"experimental": 0, "comparator": 0, "background_or_coadministered": 0,
               "not_assessable": 0}
    for nct in SURFACED:
        state, study, detail = X.fetch_raw(
            nct, fields="protocolSection,hasResults,resultsSection")
        if state != X.OK:
            rows.append({"nct": nct, "disposition": "NOT_ASSESSABLE",
                         "why": "transport: %s" % str(detail)[:140]})
            tally["NOT_ASSESSABLE"] = tally.get("NOT_ASSESSABLE", 0) + 1
            cascade["not_assessable"] += 1
            continue
        disp, fails, ev = screen(nct, study)
        r = ev.get("arm_role")
        if r not in cascade:
            # A role this counter does not know is NOT quietly folded into an existing bucket.
            raise SystemExit(
                "REFUSED: locate() returned role %r, which this cascade has no key for. "
                "Folding it into an existing bucket is how `background 0` was printed over "
                "two background trials. Add the key deliberately." % r)
        cascade[r] += 1
        rows.append({"nct": nct, "disposition": disp,
                     "failing_limbs": [f[0] for f in fails],
                     "why": "; ".join("%s: %s" % f for f in fails) or ev["estimand"],
                     "evidence": ev})
        tally[disp] = tally.get(disp, 0) + 1

    # THE WITHHOLDING QUESTION, over every eligible trial and every rank.
    wq = [{"nct": r["nct"], "acronym": r["evidence"]["brief_title"][:60],
           "enrolment": r["evidence"]["enrolment"],
           "hasResults": r["evidence"]["has_results"],
           "ranks_read": r["evidence"]["n_ranks_read"],
           "ldl_pct_change_at_ranks": r["evidence"]["ldl_pct_change_at_ranks"]}
          for r in rows if r.get("evidence") and r["disposition"] != "EXCLUDED"]

    print("SURFACED %d   arm-role cascade: %s"
          % (len(SURFACED), "  ".join("%s %d" % kv for kv in cascade.items())))
    for r in rows:
        print("  %-12s %-32s %s" % (r["nct"], r["disposition"], r["why"][:90]))
    print("\nTALLY  %s" % json.dumps(tally))
    print("recall of the executed search on this review's own included set: %d/%d"
          % (sum(1 for n in INCLUDED if n in SURFACED), len(INCLUDED)))

    out = {
        "topic": "bococizumab-lipid-review",
        "screened_utc": "2026-08-19",
        "surfaced": len(SURFACED),
        "arm_role_cascade": cascade,
        "tally": tally,
        "dispositions_reached_zero_times": [
            d for d in ("EXCLUDED", "ELIGIBLE_NOT_POOLABLE", "ELIGIBLE_NO_RESULTS_YET",
                        "ELIGIBLE_POOLABLE_NOT_INCLUDED", "INCLUDED", "NOT_ASSESSABLE")
            if d not in tally],
        "P24_note": ("Every disposition this screen can assign is listed above with its count, "
                     "including the ones reached ZERO times. A disposition that cannot be "
                     "reached is not a conservative default -- it looks cautious, so a zero "
                     "there invites no suspicion at all."),
        "withholding_question": {
            "asked_on": "2026-08-19",
            "question": ("does each eligible trial register a PERCENT CHANGE IN LDL-C outcome "
                         "at ANY rank -- primary, secondary or other -- before concluding "
                         "which trials can be combined?"),
            "detected_structurally_not_by_keyword": (
                "an LDL term AND a change term in one outcome measure, which is what the "
                "endpoint IS. Matching the five included trials' registered phrase would have "
                "found the five that already agree and nothing else."),
            "per_trial": wq,
        },
        "rows": rows,
    }
    with io.open(DEST, "w", encoding="utf-8") as fh:
        fh.write(json.dumps(out, indent=1))
    print("\nwrote %s" % DEST)
    return 0


def selftest():
    """Known answers on REAL registrations from this review, never a synthetic fixture."""
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    fails = []

    def check(name, got, want):
        ok = got == want
        print("  %-62s %s  %r" % (name, "ok" if ok else "FAIL", got))
        if not ok:
            fails.append(name)

    # The structural estimand test must fire on the registered phrase AND on a differently
    # worded one, and must NOT fire on a total-cholesterol endpoint.
    check("SPIRE's registered primary is detected",
          is_ldl_pct_change("Percent Change From Baseline in Fasting Low Density Lipoprotein "
                            "Cholesterol (LDL-C) at Week 12"), True)
    check("a differently worded LDL change endpoint is detected",
          is_ldl_pct_change("Change From Baseline in LDL-C"), True)
    check("total cholesterol percent change is NOT detected",
          is_ldl_pct_change("Percent Change From Baseline in Total Cholesterol"), False)
    check("an absolute LDL level with no change term is NOT detected",
          is_ldl_pct_change("Fasting LDL-C at Week 12"), False)

    # The population limb must remove `Healthy` and keep `Hyperlipidemia`.
    check("Healthy is not this review's population",
          any(c in LIPID_CONDITION for c in ["healthy"]), False)
    check("Hyperlipidemia is", any(c in LIPID_CONDITION for c in ["hyperlipidemia"]), True)
    check("Heterozygous familial hypercholesterolemia is",
          any(c in LIPID_CONDITION for c in ["heterozygous familial hypercholesterolemia"]),
          True)

    # And the identity set must carry the development codes: ELEVEN of the twenty-two surfaced
    # registrations name the drug by a code. A screen matching only "bococizumab" finds half.
    syn = set(TI.TOPIC_SYNONYMS.get("bococizumab") or [])
    check("the declared synonym set carries the development codes",
          {"pf-04950615", "rn316"} <= syn, True)

    # ---- THE THREE DEFECTS THIS SCRIPT SHIPPED AND CORRECTED, each pinned to the REAL
    # registration that exposed it. Every one produced a complete, plausible verdict set.
    live = {}
    for nct in ("NCT02135029", "NCT02458287", "NCT01435382", "NCT01592240", "NCT01243151"):
        st, study, _d = X.fetch_raw(nct, fields="protocolSection,hasResults,resultsSection")
        if st != X.OK:
            print("  the registry is unreachable; these five cases CANNOT be run and are "
                  "NOT_ASSESSABLE, which is not a pass")
            return 1
        live[nct] = study

    # 1. THE SYNONYM LIST, NOT THE TOPIC NAME. Passing the string makes `any(s in blob ...)`
    #    iterate CHARACTERS, and SPIRE-SI's atorvastatin arm "contains bococizumab".
    good = TI.locate(live["NCT02135029"], TI.TOPIC_SYNONYMS["bococizumab"])[0]
    check("SPIRE-SI is experimental under the synonym LIST", good, "experimental")
    # The bare string no longer RETURNS a wrong verdict -- `topic_identity.require_terms()`
    # refuses it at the entry point as of 2026-08-19. This case used to assert the defect was
    # still reproducible; now it asserts the defect is UNREACHABLE, which is strictly stronger
    # and is what the runtime guard is for.
    bare = "bococizumab"          # through a VARIABLE: the path only the runtime guard sees
    try:
        TI.locate(live["NCT02135029"], bare)
        check("...and the bare STRING now RAISES rather than answering", False, True)
    except TI.TermsMustBeACollection:
        check("...and the bare STRING now RAISES rather than answering", True, True)

    # 2. A PLACEBO FOR THE DRUG IS THE COMPARATOR. SPIRE-AI's control records are named
    #    `Bococizumab 150mg placebo`.
    check("SPIRE-AI is not excluded", screen("NCT02458287", live["NCT02458287"])[0],
          "INCLUDED")
    # The LEADING-anchor function does NOT carry the trailing convention, and this pair is
    # here so nobody reaches for it again by name-similarity.
    check("_name_is_placebo_record does NOT catch the trailing convention",
          TI._name_is_placebo_record("Bococizumab 150mg placebo"), False)
    check("_names_a_placebo does -- it is the one this limb needs",
          TI._names_a_placebo("Bococizumab 150mg placebo"), True)

    # 3. AND THE COMPARATOR LIMB MUST STILL EXCLUDE. A limb that stopped excluding anything
    #    would pass every case above and be worthless.
    check("NCT01435382 -- four arms, all the drug, nothing else -- is EXCLUDED",
          screen("NCT01435382", live["NCT01435382"])[0], "EXCLUDED")
    check("...on the COMPARATOR limb specifically",
          [f[0] for f in screen("NCT01435382", live["NCT01435382"])[1]], ["COMPARATOR"])

    # 4. Each half of the disjunction sees a design the other is blind to.
    check("NCT01592240 -- placebo INSIDE both EXPERIMENTAL arms -- is not excluded",
          screen("NCT01592240", live["NCT01592240"])[0] != "EXCLUDED", True)
    check("NCT01243151 -- unreadable role -- is NOT_ASSESSABLE and never EXCLUDED",
          screen("NCT01243151", live["NCT01243151"])[0], "NOT_ASSESSABLE")

    print("\n%s" % ("ALL KNOWN ANSWERS HELD" if not fails else "FAILED: %s" % fails))
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(selftest() if "--selftest" in sys.argv else main())
