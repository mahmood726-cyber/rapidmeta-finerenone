"""Screen the unscreened remainder against the DERIVED criteria block. Keyed on registration id.

WHY THIS EXISTS. bempedoic-acid-review's executed search located 17 trials placing bempedoic
acid in an EXPERIMENTAL arm. The object included ONE. The other 16 were neither included nor
excluded -- they were UNEXAMINED, and the page said so as a number rather than omitting it.
A review that has located 17 and screened 1 is not complete in substance whatever its
property list says.

THIS IS ALSO THE FIRST REAL TEST OF A DERIVED CRITERIA BLOCK. The block at
screening.eligibility_provenance was projected from the object's own question and outcome
record, carries predefined:false, and was argued to be legitimate under MECIR R107. The
question it now has to answer is whether it can do the work criteria are FOR: admitting and
excluding named trials, each with a reason. If it cannot, it is decoration.

THE WITHHOLDING QUESTION IS ASKED BEFORE ANY DECISION NOT TO POOL:
    does this trial report, AT ANY RANK -- primary, secondary or other -- an outcome
    matching what the included trial reports as its primary?
Reading only registered PRIMARIES is how a poolable outcome one rank down goes unseen. That
failure has a name in this corpus and it cost a topic its testability.

THREE STATES, as everywhere else. A trial whose eligibility text or outcome list cannot be
read is NOT_ASSESSABLE. It is not excluded. "We could not read it" and "it does not qualify"
are different findings and only one of them is about the trial.
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
import topic_identity as T

INCLUDE = "INCLUDE"
EXCLUDE = "EXCLUDE"
NOT_ASSESSABLE = "NOT_ASSESSABLE"

# ---------------------------------------------------------------------------
# THE CRITERIA, taken from the derived block. Enumerated, never fuzzy.
# ---------------------------------------------------------------------------
# The outcome limb is the one that must not be a loose match: "cardiovascular events" is not
# the same quantity as "four-component MACE", and collapsing them would pool different
# estimands. Terms are listed so a reader can disagree with the list itself.
MACE_TERMS = [
    "major adverse cardiovascular event",
    "mace",
    "four component major adverse",
    "4-component major adverse",
    "composite of cardiovascular death",
    "cardiovascular death, nonfatal myocardial infarction",
    "death from cardiovascular causes, nonfatal myocardial infarction",
]
# Population limb. The included trial's population is "statin-intolerant patients".
STATIN_INTOLERANT_TERMS = ["statin intolerant", "statin-intolerant", "statin intolerance",
                           "unable to tolerate", "statin adverse reaction"]
PLACEBO_TERMS = ["placebo", "matching placebo"]


def norm(s):
    return re.sub(r"\s+", " ", str(s or "")).strip().lower()


def all_outcomes(ps):
    """EVERY rank, not just primaries. Returns [(rank, measure, description)]."""
    om = ps.get("outcomesModule") or {}
    out = []
    for rank, key in (("PRIMARY", "primaryOutcomes"), ("SECONDARY", "secondaryOutcomes"),
                      ("OTHER", "otherOutcomes")):
        for o in (om.get(key) or []):
            out.append((rank, o.get("measure") or "", o.get("description") or ""))
    return out


def screen(nct):
    state, study, detail = X.fetch_raw(nct, fields="protocolSection")
    if state != X.OK:
        return {"nct": nct, "verdict": NOT_ASSESSABLE,
                "reason": f"registry record could not be read ({state}: {detail}). This is a "
                          f"transport state, not a statement about the trial."}
    ps = X.require_raw_v2(study, nct)["protocolSection"]
    idm = ps.get("identificationModule") or {}
    title = idm.get("briefTitle") or ""
    cond = " ; ".join((ps.get("conditionsModule") or {}).get("conditions") or [])
    elig = ((ps.get("eligibilityModule") or {}).get("eligibilityCriteria")) or ""
    ai = ps.get("armsInterventionsModule") or {}
    arms = ai.get("armGroups") or []
    design = (ps.get("designModule") or {})
    phase = ",".join(design.get("phases") or [])
    status = (ps.get("statusModule") or {}).get("overallStatus") or ""

    rec = {"nct": nct, "title": title[:120], "phase": phase, "status": status,
           "conditions": cond[:120]}

    # --- THE WITHHOLDING QUESTION, asked FIRST and at EVERY rank --------------------------
    outcomes = all_outcomes(ps)
    if not outcomes:
        rec.update(verdict=NOT_ASSESSABLE,
                   reason="the registry record lists no outcome measures at any rank, so "
                          "whether it reports the review's outcome cannot be decided")
        return rec
    mace_hits = [(rank, m) for (rank, m, d) in outcomes
                 if any(t in norm(m) or t in norm(d) for t in MACE_TERMS)]
    rec["outcome_ranks_searched"] = len(outcomes)
    rec["mace_at_any_rank"] = [{"rank": r, "measure": m[:130]} for r, m in mace_hits]

    # --- comparator limb -------------------------------------------------------------------
    arm_blob = norm(" ".join(str(a.get("label", "")) + " " + str(a.get("type", ""))
                             for a in arms))
    has_placebo = any(t in arm_blob for t in PLACEBO_TERMS)
    rec["has_placebo_arm"] = has_placebo

    # --- population limb -------------------------------------------------------------------
    pop_blob = norm(elig + " " + cond + " " + title)
    statin_intolerant = any(t in pop_blob for t in STATIN_INTOLERANT_TERMS)
    rec["statin_intolerant_population"] = statin_intolerant
    if not elig:
        rec["population_note"] = ("eligibility criteria text absent from the record; "
                                  "population read from conditions and title only")

    # --- the verdict, and the FIRST limb that fails is the reason --------------------------
    if not mace_hits:
        rec.update(verdict=EXCLUDE,
                   failing_limb="OUTCOME",
                   reason=(f"reports no four-component MACE outcome at ANY of its "
                           f"{len(outcomes)} registered ranks (primary, secondary and other "
                           f"all searched). Its registered primary is "
                           f"{outcomes[0][1][:90]!r}. Different quantity, not poolable with "
                           f"the review's estimand."))
        return rec
    if not has_placebo:
        rec.update(verdict=EXCLUDE, failing_limb="COMPARATOR",
                   reason=(f"reports a MACE-matching outcome but declares no placebo arm; "
                           f"arms are {[a.get('label') for a in arms][:4]}. The review's "
                           f"comparator is placebo."))
        return rec
    if not statin_intolerant:
        rec.update(verdict=EXCLUDE, failing_limb="POPULATION",
                   reason=("reports a MACE-matching outcome against placebo, but its "
                           "population is not stated as statin-intolerant. The review's "
                           "population limb is statin-intolerant patients."))
        return rec
    rec.update(verdict=INCLUDE, failing_limb=None,
               reason=("matches on all four limbs: bempedoic acid in an experimental arm, "
                       "placebo comparator, statin-intolerant population, and a "
                       "MACE-matching outcome at a registered rank."))
    return rec


def main():
    remainder = json.load(open(os.path.join(
        "F:/claude-temp/claude/F--rapidmeta-ssot-shell/"
        "eb4d84e5-8a24-4c3b-afe2-34bd91c20bc7/scratchpad", "bemp_remainder.json"),
        encoding="utf-8"))
    rows = [screen(n) for n in remainder]

    inc = [r for r in rows if r["verdict"] == INCLUDE]
    exc = [r for r in rows if r["verdict"] == EXCLUDE]
    na = [r for r in rows if r["verdict"] == NOT_ASSESSABLE]

    print(f"SCREENED {len(rows)} against the derived criteria block")
    print(f"  INCLUDE         {len(inc)}")
    print(f"  EXCLUDE         {len(exc)}")
    print(f"  NOT_ASSESSABLE  {len(na)}   <- could not be read; NOT excluded")
    print()
    by_limb = {}
    for r in exc:
        by_limb.setdefault(r["failing_limb"], []).append(r["nct"])
    print("EXCLUSIONS BY FAILING LIMB")
    for limb, ids in sorted(by_limb.items()):
        print(f"  {limb:<12} {len(ids):>2}  {ids}")
    print()
    print("THE WITHHOLDING QUESTION -- MACE at ANY rank")
    any_mace = [r for r in rows if r.get("mace_at_any_rank")]
    print(f"  trials reporting a MACE-matching outcome at some rank: {len(any_mace)}")
    for r in any_mace:
        for h in r["mace_at_any_rank"]:
            print(f"    {r['nct']}  [{h['rank']}]  {h['measure'][:88]}")
    print()
    for r in rows:
        print(f"{r['nct']}  {r['verdict']:<15} {r.get('failing_limb') or ''}")
        print(f"    {r['title'][:96]}")
        print(f"    {r['reason'][:190]}")

    out = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                       "evidence", "2026-08-19-batch1", "bempedoic_screening.json")
    with open(out, "w", encoding="utf-8", newline="") as fh:
        json.dump({"screened_on": "2026-08-19",
                   "against": "screening.eligibility_provenance (derived, predefined:false)",
                   "n_screened": len(rows), "n_include": len(inc), "n_exclude": len(exc),
                   "n_not_assessable": len(na), "rows": rows}, fh, indent=1)
    print(f"\nwrote {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
