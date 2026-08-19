#!/usr/bin/env python3
"""EXECUTE THE SEARCH `azilsartan-chlorthalidone-vs-olmesartan-hctz` HAS NEVER HAD.

THIS OBJECT IS THE OPPOSITE SHAPE TO THE LAST FOUR. Its question is a REAL QUESTION -- a named
head-to-head with a named estimand at a named timepoint -- and its two trials genuinely share
both arms. What it has never had is any evidence that those two are the only two.

    "search": absent.  "screening": absent.  "k_cascade": absent.

THE CRITERIA ARE UNUSUALLY NARROW AND THAT IS THE QUESTION'S DOING, NOT OURS. This review asks
about ONE fixed-dose combination against ONE other fixed-dose combination. A trial of azilsartan
monotherapy against valsartan is a perfectly good trial and is not this review's contrast, and
neither is azilsartan plus amlodipine. Narrow criteria are legitimate when the QUESTION is
narrow; what would not be legitimate is deriving them backwards from the two trials already
present, which is why every limb below is auditable against a registry field rather than
against the included set.

IDENTITY IS BY DECLARED TERM SET (P14). Takeda's registrations name this drug `TAK-491`,
`TAK-536`, `azilsartan medoxomil` and `azilsartan` interchangeably, and eight of the
fifty-seven surfaced records name it ONLY by a development code.

USAGE:  python scripts/screen_azilsartan_2026_08_19.py
        python scripts/screen_azilsartan_2026_08_19.py --selftest
"""
import io
import json
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, "ssot"))
import ctgov_transport as X                                              # noqa: E402
import topic_identity as TI                                             # noqa: E402

DEST = os.path.join(REPO, "evidence", "2026-08-19-batch1", "azilsartan_screening.json")

# The 57 surfaced by the executed search of 2026-08-19, named individually so the list is a
# RECORD rather than a query result that could change under us between runs.
SURFACED = [
    "NCT00362115", "NCT00376181", "NCT00591253", "NCT00591266", "NCT00591578",
    "NCT00591773", "NCT00695955", "NCT00696241", "NCT00696384", "NCT00696436",
    "NCT00759551", "NCT00760214", "NCT00762736", "NCT00818883", "NCT00846365",
    "NCT00847626", "NCT00996281", "NCT01033071", "NCT01078376", "NCT01124656",
    "NCT01289132", "NCT01309828", "NCT01456169", "NCT01496430", "NCT01609959",
    "NCT01715584", "NCT01762501", "NCT01774591", "NCT01985152", "NCT02072330",
    "NCT02079805", "NCT02203916", "NCT02235519", "NCT02235909", "NCT02277691",
    "NCT02401464", "NCT02400775", "NCT02407210", "NCT02451150", "NCT02480764",
    "NCT02517866", "NCT02541669", "NCT02609490", "NCT02786082", "NCT02791438",
    "NCT03042299", "NCT03434977", "NCT03652792", "NCT04606563", "NCT04668157",
    "NCT05002244", "NCT05753696", "NCT05841654", "NCT06618079", "NCT06990204",
    "NCT07547878", "NCT07683585",
]
INCLUDED = ["NCT00846365", "NCT01033071"]

# ---- DECLARED TERM SETS, each a criterion limb, enumerated and never inferred. -------------
HYPERTENSION = ("hypertension", "essential hypertension", "primary hypertension",
                "grade i or ii essential hypertension", "pediatric hypertension",
                "essential hypertension with stable angina and dyslipidemia",
                "essential hypertension complicated by type 2 diabetes mellitus")
# The two halves of THIS review's contrast. Both must be present, on opposite sides.
AZL_TERMS = ("azilsartan", "tak-491", "tak 491", "tak-536", "tak 536")
CLD_TERMS = ("chlorthalidone", "chlortalidone")
OLM_TERMS = ("olmesartan", "benicar")
HCTZ_TERMS = ("hydrochlorothiazide", "hctz", "benicar hct")
# A CONDITION THAT NAMES A STUDY OBJECTIVE IS NOT A STATEMENT ABOUT THE POPULATION.
#
# NCT01309828 -- "Long-Term Safety of Azilsartan Medoxomil and Chlorthalidone Compared to
# Olmesartan Medoxomil and Hydrochlorothiazide in Hypertensive Subjects With Moderate Renal
# Impairment" -- declares `conditionsModule.conditions = ["Safety"]`. It carries BOTH arms of
# this review's contrast and four registered ranks, and the population limb EXCLUDED it,
# because "safety" is not a hypertension term.
#
#     THE FIELD IS NOT ABSENT AND IT IS NOT NEGATIVE. It is UNINFORMATIVE: the registrant put
#     a study OBJECTIVE where the disease goes. Excluding on it asserts the trial is not in
#     this population, which the record nowhere says -- the withholding direction again, on a
#     head-to-head this review would otherwise want.
#
# So: where every declared condition names an objective rather than a clinical state, the
# coded field is NOT_ASSESSABLE for this limb and the verdict falls back to the TITLE -- and
# SAYS SO ON ITS FACE (P11: where the code is absent and the verdict falls back to text, the
# verdict says so). The fallback still excludes: NCT03652792 declares
# `["Bioequivalence of Two Azilsartan Formulations"]` and its title says "in Chinese Healthy
# Volunteers", so it stays out on the text.
NON_DISEASE_CONDITION = ("safety", "tolerability", "efficacy", "efficacy and safety",
                         "pharmacokinetics", "bioequivalence", "bioavailability")


def condition_is_uninformative(conds):
    """True when EVERY declared condition names a study objective, not a clinical state."""
    if not conds:
        return True
    return all(c in NON_DISEASE_CONDITION or c.startswith("bioequivalence")
               or c.startswith("pharmacokinetic") for c in conds)


# ESTIMAND, structurally: a blood-pressure term plus a change term.
BP_TERMS = ("systolic blood pressure", "sbp", "blood pressure")
CHANGE_TERMS = ("change from baseline", "change in", "percent change", "reduction in")


def norm(s):
    return " ".join((s or "").lower().replace("–", "-").split())


def ranks(ps):
    om = ps.get("outcomesModule") or {}
    out = []
    for rank, key in (("PRIMARY", "primaryOutcomes"), ("SECONDARY", "secondaryOutcomes"),
                      ("OTHER", "otherOutcomes")):
        for o in (om.get(key) or []):
            out.append((rank, o.get("measure") or ""))
    return out


def is_bp_change(measure):
    """STRUCTURAL: a blood-pressure term plus a change term. Not the registered phrase (P33)."""
    m = norm(measure)
    return any(t in m for t in BP_TERMS) and any(t in m for t in CHANGE_TERMS)


def arm_text(a):
    """Everything an arm DECLARES it receives -- label plus its intervention names."""
    return norm(" ; ".join([str(a.get("label") or ""), str(a.get("description") or "")]
                           + [str(n) for n in (a.get("interventionNames") or [])]))


def screen(nct, study):
    """(disposition, failing_limbs, evidence). EVERY failing limb, never the first (P15)."""
    ps = study.get("protocolSection") or {}
    ident = ps.get("identificationModule") or {}
    dm = ps.get("designModule") or {}
    conds = [norm(c) for c in ((ps.get("conditionsModule") or {}).get("conditions") or [])]
    arms = (ps.get("armsInterventionsModule") or {}).get("armGroups") or []
    rk = ranks(ps)
    hits = [(r, m) for (r, m) in rk if is_bp_change(m)]

    texts = [arm_text(a) for a in arms]
    azl_cld = [t for t in texts
               if any(x in t for x in AZL_TERMS) and any(x in t for x in CLD_TERMS)]
    olm_hctz = [t for t in texts
                if any(x in t for x in OLM_TERMS) and any(x in t for x in HCTZ_TERMS)]

    ev = {
        "brief_title": (ident.get("briefTitle") or "")[:120],
        "conditions": conds, "phase": dm.get("phases"),
        "allocation": (dm.get("designInfo") or {}).get("allocation"),
        "masking": ((dm.get("designInfo") or {}).get("maskingInfo") or {}).get("masking"),
        "enrolment": (dm.get("enrollmentInfo") or {}).get("count"),
        "status": (ps.get("statusModule") or {}).get("overallStatus"),
        "has_results": bool(study.get("hasResults")),
        "n_arms": len(arms), "n_ranks_read": len(rk),
        "arm_has_AZL_plus_CLD": len(azl_cld), "arm_has_OLM_plus_HCTZ": len(olm_hctz),
        "bp_change_at_ranks": [{"rank": r, "measure": m[:130]} for r, m in hits],
    }

    fails = []
    title_blob = norm(" ".join([str(ident.get("briefTitle") or ""),
                                str(ident.get("officialTitle") or "")]))
    if any(c in HYPERTENSION for c in conds):
        ev["population_basis"] = "CODED FIELD -- conditionsModule.conditions"
    elif condition_is_uninformative(conds):
        # The code says nothing about the disease. Fall back to the title, and record that the
        # verdict rests on TEXT rather than on the code.
        ev["population_basis"] = (
            "TEXT -- the coded conditions field names a study objective (%r) and not a "
            "clinical state, so it is NOT_ASSESSABLE for this limb and the verdict rests on "
            "the registered TITLE." % conds)
        if any(t in title_blob for t in ("hypertens", "blood pressure"))                 and "healthy" not in title_blob:
            ev["population_from_title"] = "hypertension named in the title"
        else:
            fails.append(("POPULATION",
                          "the coded conditions field names only a study objective (%r) and "
                          "the registered title does not name hypertension either" % conds))
    else:
        ev["population_basis"] = "CODED FIELD -- conditionsModule.conditions"
        fails.append(("POPULATION",
                      "declares no hypertension condition; conditions are %r" % conds))
    if not arms:
        ev["arms_unreadable"] = True
    elif not azl_cld:
        fails.append(("INTERVENTION",
                      "no arm declares azilsartan AND chlorthalidone together. This review's "
                      "intervention is the COMBINATION; azilsartan monotherapy, and azilsartan "
                      "with any other partner, are different contrasts."))
    if arms and not olm_hctz:
        fails.append(("COMPARATOR",
                      "no arm declares olmesartan AND hydrochlorothiazide together. This "
                      "review's comparator is that specific combination."))
    ev["estimand"] = ("blood-pressure change outcome at %s"
                      % ", ".join(sorted({r for r, _m in hits}))) if hits else (
        "no blood-pressure change outcome at ANY of %d registered ranks" % len(rk))

    if fails:
        return "EXCLUDED", fails, ev
    if ev.get("arms_unreadable"):
        return "NOT_ASSESSABLE", [], ev
    if not hits:
        return "ELIGIBLE_NOT_POOLABLE", [], ev
    if not study.get("hasResults"):
        return "ELIGIBLE_NO_RESULTS_YET", [], ev
    if nct in INCLUDED:
        return "INCLUDED", [], ev
    return "ELIGIBLE_POOLABLE_NOT_INCLUDED", [], ev


def main():
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    rows, tally = [], {}
    cascade = {"experimental": 0, "comparator": 0, "background_or_coadministered": 0,
               "not_assessable": 0, "not_eligible_other": 0}
    for nct in SURFACED:
        state, study, detail = X.fetch_raw(
            nct, fields="protocolSection,hasResults,resultsSection")
        if state != X.OK:
            rows.append({"nct": nct, "disposition": "NOT_ASSESSABLE",
                         "why": "transport: %s" % str(detail)[:140]})
            tally["NOT_ASSESSABLE"] = tally.get("NOT_ASSESSABLE", 0) + 1
            cascade["not_assessable"] += 1
            continue
        role = TI.locate(study, TI.TOPIC_SYNONYMS["azilsartan"])
        rname = role[0] if isinstance(role, (list, tuple)) else role
        if rname not in cascade:
            raise SystemExit("REFUSED: unknown arm role %r; add the key deliberately." % rname)
        cascade[rname] += 1
        disp, fails, ev = screen(nct, study)
        ev["arm_role"] = rname
        rows.append({"nct": nct, "disposition": disp,
                     "failing_limbs": [f[0] for f in fails],
                     "why": "; ".join("%s: %s" % f for f in fails) or ev["estimand"],
                     "evidence": ev})
        tally[disp] = tally.get(disp, 0) + 1

    print("SURFACED %d   arm-role cascade: %s"
          % (len(SURFACED), "  ".join("%s %d" % kv for kv in cascade.items())))
    for r in sorted(rows, key=lambda x: x["disposition"]):
        if r["disposition"] != "EXCLUDED":
            print("  %-12s %-32s %s" % (r["nct"], r["disposition"], r["why"][:80]))
    print("  ... %d EXCLUDED, every one with its failing limb(s) in the record"
          % tally.get("EXCLUDED", 0))
    print("\nTALLY  %s" % json.dumps(tally))
    print("recall of the executed search on this review's own included set: %d/%d"
          % (sum(1 for n in INCLUDED if n in SURFACED), len(INCLUDED)))

    out = {
        "topic": "azilsartan-chlorthalidone-vs-olmesartan-hctz",
        "screened_utc": "2026-08-19",
        "surfaced": len(SURFACED), "arm_role_cascade": cascade, "tally": tally,
        "dispositions_reached_zero_times": [
            d for d in ("EXCLUDED", "ELIGIBLE_NOT_POOLABLE", "ELIGIBLE_NO_RESULTS_YET",
                        "ELIGIBLE_POOLABLE_NOT_INCLUDED", "INCLUDED", "NOT_ASSESSABLE")
            if d not in tally],
        "P24_note": ("Every disposition this screen can assign is listed with its count, "
                     "including any reached ZERO times."),
        "withholding_question": {
            "asked_on": "2026-08-19",
            "question": ("does each trial that shares BOTH arms register a blood-pressure "
                         "CHANGE outcome at ANY rank -- primary, secondary or other -- before "
                         "concluding which trials can be combined?"),
            "detected_structurally_not_by_keyword": (
                "a blood-pressure term plus a change term, at any rank. Not the incumbents' "
                "registered phrase, which would have found the two that already agree."),
            "per_trial": [
                {"nct": r["nct"], "acronym": r["evidence"]["brief_title"][:60],
                 "enrolment": r["evidence"]["enrolment"],
                 "hasResults": r["evidence"]["has_results"],
                 "ranks_read": r["evidence"]["n_ranks_read"],
                 "bp_change_at_ranks": r["evidence"]["bp_change_at_ranks"]}
                for r in rows if r.get("evidence") and r["disposition"] != "EXCLUDED"],
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
        print("  %-60s %s  %r" % (name, "ok" if ok else "FAIL", got))
        if not ok:
            fails.append(name)

    check("a registered SBP change endpoint is detected",
          is_bp_change("Change From Baseline in Trough, Sitting Clinic Systolic Blood "
                       "Pressure at Week 8"), True)
    check("a 24-hour ambulatory SBP change endpoint is detected too",
          is_bp_change("Change From Baseline in 24-hour Mean Ambulatory Systolic Blood "
                       "Pressure"), True)
    check("an adverse-event count is NOT detected",
          is_bp_change("Number of Participants With Treatment-Emergent Adverse Events"), False)
    check("a blood-pressure LEVEL with no change term is NOT detected",
          is_bp_change("Sitting Clinic Systolic Blood Pressure at Week 8"), False)

    check("the declared synonym set carries the Takeda development codes",
          {"tak-491", "tak-536"} <= set(TI.TOPIC_SYNONYMS["azilsartan"]), True)

    live = {}
    for nct in ("NCT00846365", "NCT00996281", "NCT00591578", "NCT00847626"):
        st, study, _d = X.fetch_raw(nct, fields="protocolSection,hasResults,resultsSection")
        if st != X.OK:
            print("  registry unreachable; these cases are NOT_ASSESSABLE, which is not a pass")
            return 1
        live[nct] = study

    # The two halves of the contrast must BOTH be required, and the limb must exclude.
    check("NCT00846365 -- AZL-CLD vs OLM-HCTZ -- is INCLUDED",
          screen("NCT00846365", live["NCT00846365"])[0], "INCLUDED")
    check("NCT00591578 -- azilsartan vs VALSARTAN monotherapy -- is EXCLUDED",
          screen("NCT00591578", live["NCT00591578"])[0], "EXCLUDED")
    check("...on BOTH the intervention and comparator limbs",
          sorted(f[0] for f in screen("NCT00591578", live["NCT00591578"])[1]),
          ["COMPARATOR", "INTERVENTION"])
    # A trial with the right INTERVENTION and the wrong COMPARATOR must fail on comparator
    # alone -- this is what proves the two limbs are independent rather than one test twice.
    d, f, _e = screen("NCT00847626", live["NCT00847626"])
    check("NCT00847626 -- AZL-CLD vs chlorthalidone alone -- fails COMPARATOR only",
          [x[0] for x in f], ["COMPARATOR"])

    # A CONDITION THAT NAMES AN OBJECTIVE IS NOT A STATEMENT ABOUT THE POPULATION, and the
    # fallback must admit exactly the trial that deserves it and no more. These two records
    # BOTH declare an objective in the conditions field and they must part company.
    more = {}
    for nct in ("NCT01309828", "NCT03652792"):
        st, study, _d = X.fetch_raw(nct, fields="protocolSection,hasResults,resultsSection")
        if st != X.OK:
            print("  registry unreachable; NOT_ASSESSABLE, not a pass")
            return 1
        more[nct] = study
    check("NCT01309828 -- conditions ['safety'], title says hypertensive -- is not EXCLUDED",
          screen("NCT01309828", more["NCT01309828"])[0] != "EXCLUDED", True)
    check("...and its verdict records that it rests on TEXT, not the code",
          screen("NCT01309828", more["NCT01309828"])[2]["population_basis"].startswith("TEXT"),
          True)
    check("NCT03652792 -- conditions name a bioequivalence objective, title says HEALTHY "
          "VOLUNTEERS -- stays EXCLUDED",
          screen("NCT03652792", more["NCT03652792"])[0], "EXCLUDED")

    print("\n%s" % ("ALL KNOWN ANSWERS HELD" if not fails else "FAILED: %s" % fails))
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(selftest() if "--selftest" in sys.argv else main())
