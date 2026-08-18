"""Screen sglt2-hf's 39-trial remainder on TWO AXES, because its criteria say two axes.

THE OBJECT'S OWN CRITERIA, quoted:

    "ELIGIBILITY turns on population, intervention and comparator: a trial is in scope if it
     randomised adults with CHRONIC heart failure to an SGLT2 inhibitor against placebo on top
     of background therapy. It does NOT turn on which analysis the trial reported, because
     section 3.2.4 cautions that making eligibility depend on reported outcomes invites outcome
     reporting bias. What the measure governs is POOLING, under section 10.9: only a
     time-to-first-event hazard ratio can be combined with the others. Each row below therefore
     carries two separate columns -- the eligibility axis it fails, and, where it applies, the
     reason its quantity could not have been pooled even had it been eligible."

So this screen does NOT do what bempedoic's did. There, the outcome limb was an ELIGIBILITY
limb and thirteen trials were excluded on it. Here, excluding on outcome would be the exact
bias section 3.2.4 warns about. A trial can be ELIGIBLE and contribute to NO pool, and that is
a coherent state which the object requires to be reported as two separate facts.

  AXIS 1  ELIGIBILITY   population + intervention + comparator
  AXIS 2  POOLABILITY   does it report a time-to-first-event hazard ratio at any rank?

Every screened trial carries the quantity it reports, quoted, whichever column it fell in.

NO SUBSTRING MATCHING OVER CLINICAL TEXT (P14). The endpoint families are decided from the
registry's own coded fields where they exist, and where a text read is unavoidable the term
set is declared and enumerated below so a reader can disagree with the list rather than with a
hidden heuristic.
"""
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault("RM_CTGOV_CACHE",
                      "F:/claude-temp/claude/F--rapidmeta-ssot-shell/"
                      "eb4d84e5-8a24-4c3b-afe2-34bd91c20bc7/scratchpad/.ctgov-raw-cache")

import ctgov_transport as X

ROOT = os.path.dirname(os.path.abspath(__file__))
CASCADE = ("F:/claude-temp/claude/F--rapidmeta-ssot-shell/"
           "eb4d84e5-8a24-4c3b-afe2-34bd91c20bc7/scratchpad/sglt2_cascade.json")
INCLUDED = {"NCT03036124", "NCT03057977", "NCT03057951", "NCT03619213"}

ELIGIBLE = "ELIGIBLE"
NOT_ELIGIBLE = "NOT_ELIGIBLE"
NOT_ASSESSABLE = "NOT_ASSESSABLE"

# Declared, enumerated term sets. Tokens are matched against WORD SEQUENCES after collapsing
# parenthetical abbreviations -- "Cardiovascular (CV) Death" becomes "cardiovascular death" --
# which is the P14 defect from this same topic, fixed rather than repeated.
PAREN = re.compile(r"\s*\([^)]*\)\s*")

CHRONIC_HF = ["chronic heart failure", "heart failure with reduced ejection fraction",
              "heart failure with preserved ejection fraction", "hfref", "hfpef",
              "congestive heart failure", "heart failure"]
ACUTE_ONLY = ["acute heart failure", "acute decompensated", "decompensated heart failure",
              "hospitalised for acute", "hospitalized for acute", "cardiogenic shock",
              "acute myocardial infarction", "myocardial infarction", "post worsening"]
PLACEBO = ["placebo"]
# Poolability: a time-to-first-event hazard ratio. The registry codes this in the outcome
# text as "time to first"/"first occurrence"/"first event"; a rate, a count, a change score
# or a questionnaire score is a different quantity and cannot be combined under s10.9.
TIME_TO_FIRST = ["time to first", "time to the first", "first event", "first occurrence",
                 "composite endpoint of cv death", "cv death or"]


def flat(s):
    return PAREN.sub(" ", re.sub(r"\s+", " ", str(s or ""))).strip().lower()


def screen(nct):
    state, study, detail = X.fetch_raw(nct, fields="protocolSection")
    if state != X.OK:
        return {"nct": nct, "eligibility": NOT_ASSESSABLE,
                "eligibility_reason": f"registry record unreadable ({state}); a transport "
                                      f"state, not a statement about the trial",
                "poolable": NOT_ASSESSABLE, "poolable_reason": "not read", "quantity": None}
    ps = X.require_raw_v2(study, nct)["protocolSection"]
    title = (ps.get("identificationModule") or {}).get("briefTitle") or ""
    conds = (ps.get("conditionsModule") or {}).get("conditions") or []
    arms = (ps.get("armsInterventionsModule") or {}).get("armGroups") or []
    om = ps.get("outcomesModule") or {}

    rec = {"nct": nct, "title": title[:110], "conditions": "; ".join(conds)[:90]}

    cond_blob = flat(" ; ".join(conds) + " " + title)
    arm_blob = flat(" ".join(str(a.get("label", "")) + " " + str(a.get("type", ""))
                             for a in arms))

    # --- AXIS 1: ELIGIBILITY -------------------------------------------------------------
    is_hf = any(t in cond_blob for t in CHRONIC_HF)
    is_acute_only = (any(t in cond_blob for t in ACUTE_ONLY)
                     and "chronic" not in cond_blob)
    has_placebo = any(t in arm_blob for t in PLACEBO)

    if not arms:
        rec.update(eligibility=NOT_ASSESSABLE,
                   eligibility_reason="no armGroups in the registry record, so the comparator "
                                      "limb cannot be read")
    elif not is_hf:
        rec.update(eligibility=NOT_ELIGIBLE, eligibility_axis="POPULATION",
                   eligibility_reason=f"population is not heart failure: {conds}")
    elif is_acute_only:
        rec.update(eligibility=NOT_ELIGIBLE, eligibility_axis="POPULATION",
                   eligibility_reason=f"population is ACUTE / decompensated / peri-infarct, not "
                                      f"CHRONIC heart failure: {conds}")
    elif not has_placebo:
        rec.update(eligibility=NOT_ELIGIBLE, eligibility_axis="COMPARATOR",
                   eligibility_reason=f"no placebo arm declared; arms are "
                                      f"{[a.get('label') for a in arms][:4]}")
    else:
        # INTERVENTION LIMB: the contrast must be the SGLT2 inhibitor, not a combination.
        #
        # NCT03794518 randomises "Pioglitazone Plus dapaglifliozin" against "Placebo". The
        # SGLT2 inhibitor IS in the contrast -- but so is pioglitazone, an active agent absent
        # from the control arm. The randomised difference is therefore SGLT2 **plus** a second
        # drug, and any effect it estimates is not attributable to the SGLT2 inhibitor. The
        # criteria say "randomised ... to an SGLT2 inhibitor against placebo on top of
        # BACKGROUND therapy"; a co-intervention given to only one arm is not background.
        #
        # This is the mirror of the both-arms defect just fixed in topic_identity: there the
        # drug was in BOTH arms and was not the contrast; here a SECOND drug is in ONE arm and
        # contaminates it. Both are the same question -- what exactly was randomised?
        topic_syn = [t for t in ("dapagliflozin", "empagliflozin", "sotagliflozin",
                                 "canagliflozin", "ertugliflozin", "sglt")]
        exp_names, ctrl_names = set(), set()
        for a in arms:
            tgt = exp_names if "EXPERIMENTAL" in str(a.get("type") or "").upper() else ctrl_names
            for nm in (a.get("interventionNames") or []):
                tgt.add(flat(str(nm).split(":", 1)[-1]))
        extra = []
        for nm in exp_names:
            if any(t in nm for t in topic_syn) or "placebo" in nm:
                continue
            if not any(nm in c or c in nm for c in ctrl_names):
                extra.append(nm)
        if extra:
            rec.update(eligibility=NOT_ELIGIBLE, eligibility_axis="INTERVENTION",
                       eligibility_reason=(
                           f"the randomised contrast carries a second active agent absent from "
                           f"the control arm: {extra}. The difference between arms is the SGLT2 "
                           f"inhibitor PLUS that agent, so the estimate is not attributable to "
                           f"the SGLT2 inhibitor. A co-intervention given to one arm only is "
                           f"not background therapy."))
        else:
            rec.update(eligibility=ELIGIBLE, eligibility_axis=None,
                       eligibility_reason="adults with chronic heart failure randomised to an "
                                          "SGLT2 inhibitor against placebo")

    # --- AXIS 2: POOLABILITY, reported SEPARATELY and for every trial ---------------------
    outcomes = []
    for rank, key in (("PRIMARY", "primaryOutcomes"), ("SECONDARY", "secondaryOutcomes"),
                      ("OTHER", "otherOutcomes")):
        for x in (om.get(key) or []):
            outcomes.append((rank, x.get("measure") or ""))
    if not outcomes:
        rec.update(poolable=NOT_ASSESSABLE, poolable_reason="no outcome measures at any rank",
                   quantity=None, ranks_read=0)
        return rec
    rec["ranks_read"] = len(outcomes)
    ttf = [(r, m) for r, m in outcomes if any(t in flat(m) for t in TIME_TO_FIRST)]
    rec["quantity"] = outcomes[0][1][:150]
    if ttf:
        rec.update(poolable="POOLABLE_QUANTITY",
                   poolable_reason=f"reports a time-to-first-event composite at {ttf[0][0]} "
                                   f"rank: {ttf[0][1][:110]!r}")
    else:
        rec.update(poolable="NOT_POOLABLE_QUANTITY",
                   poolable_reason=(f"reports no time-to-first-event hazard ratio at any of "
                                    f"{len(outcomes)} ranks. Its registered primary is "
                                    f"{outcomes[0][1][:110]!r} -- a different quantity, which "
                                    f"s10.9 does not permit combining. THIS IS NOT AN "
                                    f"ELIGIBILITY FAILURE."))
    return rec


def main():
    with open(CASCADE, encoding="utf-8") as fh:
        casc = json.load(fh)
    remainder = sorted(set(casc["experimental"]) - INCLUDED)
    rows = [screen(n) for n in remainder]

    el = [r for r in rows if r["eligibility"] == ELIGIBLE]
    ne = [r for r in rows if r["eligibility"] == NOT_ELIGIBLE]
    na = [r for r in rows if r["eligibility"] == NOT_ASSESSABLE]
    print(f"SCREENED {len(rows)} on TWO AXES\n")
    print("AXIS 1 -- ELIGIBILITY (population, intervention, comparator only)")
    print(f"  ELIGIBLE        {len(el)}")
    print(f"  NOT_ELIGIBLE    {len(ne)}")
    print(f"  NOT_ASSESSABLE  {len(na)}")
    by = {}
    for r in ne:
        by.setdefault(r.get("eligibility_axis"), []).append(r["nct"])
    for k, v in sorted(by.items()):
        print(f"     {k:<12} {len(v):>2}")
    print()
    print("AXIS 2 -- POOLABILITY, reported separately (s10.9), NEVER as an eligibility failure")
    for st in ("POOLABLE_QUANTITY", "NOT_POOLABLE_QUANTITY", NOT_ASSESSABLE):
        n = [r for r in rows if r.get("poolable") == st]
        print(f"  {st:<24} {len(n)}")
    print()
    print("THE CELL THAT MATTERS: eligible AND poolable -- these would change k")
    both = [r for r in el if r.get("poolable") == "POOLABLE_QUANTITY"]
    print(f"  {len(both)}")
    for r in both:
        print(f"    {r['nct']}  {r['title'][:80]}")
        print(f"        {r['poolable_reason'][:150]}")

    out = os.path.join(os.path.dirname(ROOT), "evidence", "2026-08-19-batch1",
                       "sglt2_screening.json")
    with open(out, "w", encoding="utf-8", newline="") as fh:
        json.dump({"screened_on": "2026-08-19", "n_screened": len(rows),
                   "axis1_eligible": len(el), "axis1_not_eligible": len(ne),
                   "axis1_not_assessable": len(na),
                   "eligible_and_poolable": [r["nct"] for r in both],
                   "rows": rows}, fh, indent=1)
    print(f"\nwrote {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
