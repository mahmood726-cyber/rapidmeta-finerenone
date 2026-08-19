#!/usr/bin/env python3
"""ASSIGN THE 57 SURFACED BOSENTAN RECORDS TO THE FOUR READINGS, AND COUNT THEM.

`BLOCKED-bosentan-pah-2026-08-19.md` named four readings and REFUSED to quote a count for any of
them, because `topic_identity.locate()` had not been run over this set and an uncomputed number
is UNKNOWN, never zero. This computes them.

THE DECISION THE COUNTS FEED. P21 says build each legitimate reading as its own review rather
than choosing between them. It does not say build a page with nothing on it:

    a reading with NO eligible trial is not a review, it is an EMPTY QUESTION, and the honest
    outcome is to name it as a BOUNDARY on the other readings' pages;
    a reading with ONE UNCONTROLLED trial IS a review, and it publishes a sourced verdict.

PRECEDENCE, STATED RATHER THAN DISCOVERED. A trial can be paediatric AND group-1 AND an add-on
design, so the readings are not mutually exclusive by construction and an assignment rule is
required. It is applied in this order and each step names the field it reads:

    D  CHILDREN            eligibilityModule -- minimumAge under 18, or stdAges contains CHILD
    C  NOT WHO GROUP 1     conditionsModule  -- CTEPH, sickle cell, sarcoidosis, fibrotic lung
                                                disease, left-heart/diastolic, hypoxia/altitude
    B  ADD-ON              armsInterventionsModule -- a second PAH-specific drug present in the
                                                     randomised contrast on either side
    A  MONOTHERAPY         everything else that places bosentan in the randomised contrast

Children first because a paediatric trial's evidence does not transfer to adults whatever its
contrast; disease group next because a CTEPH trial is not a PAH trial whatever its comparator.
BOTH CHOICES ARE ARGUABLE AND BOTH ARE WRITTEN DOWN, which is the part that matters: a different
precedence would move trials between readings and the counts below would change with it.

USAGE:  python scripts/screen_bosentan_split_2026_08_19.py
        python scripts/screen_bosentan_split_2026_08_19.py --selftest
"""
import io
import json
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, "ssot"))
import ctgov_transport as X                                              # noqa: E402
import topic_identity as TI                                             # noqa: E402

DEST = os.path.join(REPO, "evidence", "2026-08-19-batch1", "bosentan_split_screening.json")

SURFACED = [
    "NCT00080457", "NCT00082186", "NCT00086463", "NCT00091715", "NCT00120380",
    "NCT00260819", "NCT00266162", "NCT00302211", "NCT00303459", "NCT00310830",
    "NCT00313196", "NCT00313222", "NCT00317486", "NCT00319020", "NCT00319111",
    "NCT00319267", "NCT00323297", "NCT00360087", "NCT00367770", "NCT00377455",
    "NCT00432978", "NCT00433329", "NCT00581607", "NCT00595049", "NCT00625469",
    "NCT00637065", "NCT00679068", "NCT00780728", "NCT00820352", "NCT00825266",
    "NCT00864201", "NCT00909337", "NCT00926627", "NCT01100736", "NCT01223352",
    "NCT01270750", "NCT01330108", "NCT01338415", "NCT01352065", "NCT01389856",
    "NCT01392469", "NCT01449253", "NCT01508780", "NCT01548950", "NCT01712997",
    "NCT01721564", "NCT01824290", "NCT01827059", "NCT02885012", "NCT03053739",
    "NCT03236818", "NCT04039464", "NCT04273945", "NCT04991207", "NCT06317805",
    "NCT06484673", "NCT01864863",
]
IN_OBJECT = ["NCT00303459", "NCT00319020"]

# ---- DECLARED TERM SETS. Enumerated, never inferred. ---------------------------------------
# WHO group 1 is PULMONARY ARTERIAL hypertension. These name the OTHER groups.
NOT_GROUP1 = ("chronic thromboembolic", "cteph", "sickle cell", "sarcoidosis",
              "interstitial lung", "pulmonary fibrosis", "fibrotic", "nonspecific interstitial",
              "diastolic", "heart failure", "mitral", "hypoxia", "altitude",
              "persistent pulmonary hypertension of the newborn", "eisenmenger")
# PAH-specific drugs OTHER than bosentan. A second one in the contrast makes it an ADD-ON or a
# head-to-head, not monotherapy against an inactive control.
OTHER_PAH_DRUG = ("sildenafil", "tadalafil", "iloprost", "treprostinil", "epoprostenol",
                  "ambrisentan", "macitentan", "sitaxsentan", "riociguat", "selexipag",
                  "beraprost", "imatinib")
BOSENTAN = ("bosentan", "tracleer", "traclear")


def norm(s):
    return " ".join((s or "").lower().replace("–", "-").split())


def _years(age):
    """Registry age string -> years, or None. `3 Months` and `2 Years` both occur here."""
    a = norm(age)
    if not a:
        return None
    try:
        n = float(a.split()[0])
    except (ValueError, IndexError):
        return None
    unit = a.split()[-1]
    if unit.startswith("year"):
        return n
    if unit.startswith("month"):
        return n / 12.0
    if unit.startswith("week"):
        return n / 52.0
    if unit.startswith("day"):
        return n / 365.0
    return None


def is_paediatric(ps):
    """A PAEDIATRIC trial is one whose POPULATION IS CHILDREN. Read from eligibility, never
    from the title.

    THE FIRST RULE HERE WAS `minimumAge < 18` AND IT WAS WRONG IN THE DIRECTION THAT MATTERS.
    EARLY (NCT00091715) and COMPASS-2 (NCT00303459) are adult PAH trials that ADMIT
    ADOLESCENTS -- `minimumAge: 12 Years`, `stdAges: [CHILD, ADULT, OLDER_ADULT]` -- and the
    rule assigned both to the paediatric reading, taking the anchor trial of reading A and the
    object's own reading-B trial out of their reviews entirely. A precedence rule applied
    FIRST is the most damaging place to be wrong: everything downstream inherits it silently.

    ADMITTING A CHILD IS NOT BEING A PAEDIATRIC TRIAL. What separates them is whether adults
    are admitted at all:
        stdAges = ['CHILD']                          -> paediatric
        maximumAge under 18                          -> paediatric
        stdAges = ['CHILD','ADULT','OLDER_ADULT']    -> an adult trial with an adolescent floor
    """
    el = ps.get("eligibilityModule") or {}
    ages = [str(a).upper() for a in (el.get("stdAges") or [])]
    if ages and "CHILD" in ages and not ({"ADULT", "OLDER_ADULT"} & set(ages)):
        return True, "stdAges = %r -- no adult stratum at all" % ages
    mx = _years(el.get("maximumAge"))
    if mx is not None and mx < 18:
        return True, "maximumAge = %r" % el.get("maximumAge")
    return False, None


def assign(nct, study):
    """(reading, why, evidence) -- D > C > B > A, precedence applied in that order."""
    ps = study.get("protocolSection") or {}
    ident = ps.get("identificationModule") or {}
    dm = ps.get("designModule") or {}
    conds = [norm(c) for c in ((ps.get("conditionsModule") or {}).get("conditions") or [])]
    arms = (ps.get("armsInterventionsModule") or {}).get("armGroups") or []
    intrs = (ps.get("armsInterventionsModule") or {}).get("interventions") or []
    intr_names = [norm(i.get("name")) for i in intrs]
    arm_blob = norm(" ; ".join(
        [str(a.get("label") or "") + " " + str(a.get("description") or "") + " " +
         " ".join(str(n) for n in (a.get("interventionNames") or [])) for a in arms]))

    role = TI.locate(study, TI.TOPIC_SYNONYMS["bosentan"])
    rname = role[0] if isinstance(role, (list, tuple)) else role

    ev = {
        "brief_title": (ident.get("briefTitle") or "")[:110],
        "conditions": conds,
        "enrolment": (dm.get("enrollmentInfo") or {}).get("count"),
        "status": (ps.get("statusModule") or {}).get("overallStatus"),
        "allocation": (dm.get("designInfo") or {}).get("allocation"),
        "n_arms": len(arms),
        "has_results": bool(study.get("hasResults")),
        "arm_role": rname,
        "arm_types": sorted({str(a.get("type") or "") for a in arms if a.get("type")}),
        "interventions": intr_names,
    }

    paed, paed_why = is_paediatric(ps)
    ev["paediatric_basis"] = paed_why
    if paed:
        return "D_children", "eligibility: %s" % paed_why, ev
    hit = [t for t in NOT_GROUP1 if any(t in c for c in conds)]
    if hit:
        ev["group_basis"] = "CODED -- conditionsModule.conditions"
        return "C_not_group1", "conditions name %s" % ", ".join(hit), ev
    # THE CODED CONDITION NAMES THE SYNDROME AND THE TITLE NAMES THE CAUSE. Third instance of
    # this shape in one day, after azilsartan's `conditions: ["Safety"]`. ASSET-1 and ASSET-2
    # (NCT00310830, NCT00313196) declare `conditions: ["Pulmonary Hypertension"]` and are
    # titled "...in Sickle Cell Disease (SCD) Patients", so the coded field is TRUE and
    # UNINFORMATIVE -- it says the syndrome, not the WHO group -- and reading it alone put two
    # sickle-cell trials into the WHO-group-1 monotherapy reading.
    ident_blob = norm(" ".join([str(ident.get("officialTitle") or ""),
                                str(ident.get("briefTitle") or "")]))
    thit = [t for t in NOT_GROUP1 if t in ident_blob]
    if thit:
        ev["group_basis"] = ("TEXT -- the coded conditions field names only the syndrome (%r); "
                             "the WHO group is named in the trial's own title." % conds)
        return "C_not_group1", "title names %s" % ", ".join(thit), ev
    ev["group_basis"] = "CODED -- conditionsModule.conditions, and the title agrees"
    others = sorted({d for d in OTHER_PAH_DRUG
                     if d in arm_blob or any(d in n for n in intr_names)})
    if others:
        ev["add_on_basis"] = "CODED -- armsInterventionsModule"
        return ("B_add_on",
                "a second PAH-specific drug is in the randomised contrast: %s"
                % ", ".join(others), ev)

    # AN ADD-ON DESIGN CAN BE INVISIBLE IN THE ARMS. COMPASS-2 (NCT00303459) declares exactly
    # what EARLY (NCT00091715) declares -- `armGroups: bosentan | placebo`,
    # `interventions: ['bosentan','placebo']` -- because its sildenafil is BACKGROUND THERAPY
    # and background therapy is not a registered intervention. Read from the arms alone the two
    # trials are indistinguishable, and COMPASS-2 was assigned to MONOTHERAPY, which is the
    # reading it most specifically is not.
    #
    # The design IS declared, in the officialTitle and briefSummary:
    #     "Effects of Combination of Bosentan and Sildenafil Versus Sildenafil Monotherapy..."
    # So the limb falls back to TEXT and RECORDS THAT IT DID (P11). The fallback still
    # separates: EARLY's own title and summary name no second PAH drug at all, so it stays in A.
    desc = ps.get("descriptionModule") or {}
    text_blob = norm(" ".join([str(ident.get("officialTitle") or ""),
                               str(ident.get("briefTitle") or ""),
                               str(desc.get("briefSummary") or "")]))
    named = sorted({d for d in OTHER_PAH_DRUG if d in text_blob})
    if named:
        ev["add_on_basis"] = (
            "TEXT -- the arms declare only bosentan and placebo, because the background drug is "
            "not a registered intervention. The design is named in the officialTitle and "
            "briefSummary: %s." % ", ".join(named))
        return ("B_add_on",
                "background PAH therapy named in the trial's own title/summary: %s"
                % ", ".join(named), ev)
    ev["add_on_basis"] = "CODED -- no second PAH drug in the arms, and none named in the text"
    return "A_monotherapy", "no second PAH-specific drug in the contrast or in the text", ev


# A PHARMACOKINETIC OR BIOEQUIVALENCE DESIGN IS IN SCOPE AND CONTRIBUTES NO EFFECT ESTIMATE --
# the same rule apixaban applied to NCT01195727 and bococizumab to its phase-1 programme.
PK_DESIGN = ("pharmacokinetic", "bioequivalence", "bioavailability", "healthy subjects",
             "healthy volunteers", "healthy male", "in healthy")


def eligible(reading, ev):
    """Could this trial's reading actually include it? Every limb reads a named field.

    THE FIRST VERSION TESTED ARM ROLE AND ALLOCATION AND NOTHING ELSE, and admitted a
    bioequivalence study of two bosentan tablet formulations in HEALTHY MALE VOLUNTEERS
    (NCT01864863) to the monotherapy reading's eligible set. Randomised, bosentan in the
    contrast, and not a trial of bosentan's effect on pulmonary hypertension in anybody.
    """
    if ev["arm_role"] not in ("experimental", "comparator"):
        return False, "bosentan is not in the randomised contrast (role %r)" % ev["arm_role"]
    if (ev["allocation"] or "").upper() != "RANDOMIZED":
        return False, "allocation is %r, not RANDOMIZED" % ev["allocation"]
    blob = norm(ev.get("brief_title"))
    if any(t in blob for t in PK_DESIGN):
        return False, ("a pharmacokinetic / bioequivalence design in healthy subjects. In "
                       "scope by drug and contributing no effect estimate on any reading's "
                       "question.")
    return True, "randomised, with bosentan in the contrast"


def main():
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    rows = []
    cascade = {"experimental": 0, "comparator": 0, "background_or_coadministered": 0,
               "not_assessable": 0, "not_eligible_other": 0}
    for nct in SURFACED:
        state, study, detail = X.fetch_raw(
            nct, fields="protocolSection,hasResults,resultsSection")
        if state != X.OK:
            rows.append({"nct": nct, "reading": "NOT_ASSESSABLE",
                         "why": "transport: %s" % str(detail)[:120]})
            cascade["not_assessable"] += 1
            continue
        reading, why, ev = assign(nct, study)
        if ev["arm_role"] not in cascade:
            raise SystemExit("REFUSED: unknown arm role %r." % ev["arm_role"])
        cascade[ev["arm_role"]] += 1
        ok, ewhy = eligible(reading, ev)
        rows.append({"nct": nct, "reading": reading, "why": why,
                     "eligible": ok, "eligible_why": ewhy,
                     "in_object": nct in IN_OBJECT, "evidence": ev})

    by = {}
    for r in rows:
        b = by.setdefault(r["reading"], {"n": 0, "eligible": 0, "with_results": 0,
                                         "randomised_controlled": 0, "ncts": []})
        b["n"] += 1
        b["ncts"].append(r["nct"])
        if r.get("eligible"):
            b["eligible"] += 1
            if (r.get("evidence") or {}).get("has_results"):
                b["with_results"] += 1

    print("SURFACED %d   arm-role cascade: %s"
          % (len(SURFACED), "  ".join("%s %d" % kv for kv in cascade.items())))
    print("")
    for k in sorted(by):
        b = by[k]
        print("  %-16s records %2d   ELIGIBLE %2d   of those with posted results %2d"
              % (k, b["n"], b["eligible"], b["with_results"]))
    print("")
    for k in sorted(by):
        elig = [r for r in rows if r["reading"] == k and r.get("eligible")]
        print("  %s -- eligible:" % k)
        for r in elig:
            e = r["evidence"]
            print("      %-12s n=%-6s %-10s %s"
                  % (r["nct"], e["enrolment"], "RESULTS" if e["has_results"] else "no results",
                     e["brief_title"][:58]))
        if not elig:
            print("      NONE. THIS READING IS AN EMPTY QUESTION, NOT A REVIEW.")

    out = {
        "topic": "bosentan-pah",
        "screened_utc": "2026-08-19",
        "surfaced": len(SURFACED),
        "arm_role_cascade": cascade,
        "precedence": "D children > C not-WHO-group-1 > B add-on > A monotherapy, applied in "
                      "that order and stated rather than discovered. A different precedence "
                      "would move trials between readings and these counts would change.",
        "by_reading": by,
        "readings_with_no_eligible_trial": sorted(k for k, b in by.items()
                                                  if b["eligible"] == 0),
        "what_an_empty_reading_means": (
            "A reading with NO eligible trial is not a review, it is an EMPTY QUESTION, and "
            "the honest outcome is to name it as a BOUNDARY on the other readings' pages "
            "rather than to build a page with nothing on it. A reading with ONE UNCONTROLLED "
            "trial IS a review and publishes a sourced verdict."),
        "rows": rows,
    }
    with io.open(DEST, "w", encoding="utf-8") as fh:
        fh.write(json.dumps(out, indent=1))
    print("\nwrote %s" % DEST)
    return 0


def selftest():
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    fails = []

    def check(name, got, want):
        ok = got == want
        print("  %-62s %s  %r" % (name, "ok" if ok else "FAIL", got))
        if not ok:
            fails.append(name)

    live = {}
    for nct in ("NCT00319020", "NCT00313222", "NCT00303459", "NCT00091715"):
        st, study, _d = X.fetch_raw(nct, fields="protocolSection,hasResults,resultsSection")
        if st != X.OK:
            print("  registry unreachable; NOT_ASSESSABLE, which is not a pass")
            return 1
        live[nct] = study

    # One real instance per reading, and the precedence must be visible in the answers.
    check("FUTURE-2 (paediatric extension) -> D", assign("NCT00319020", live["NCT00319020"])[0],
          "D_children")
    check("BENEFIT (inoperable CTEPH) -> C", assign("NCT00313222", live["NCT00313222"])[0],
          "C_not_group1")
    check("COMPASS-2 (bosentan + sildenafil vs sildenafil) -> B",
          assign("NCT00303459", live["NCT00303459"])[0], "B_add_on")
    check("EARLY (bosentan vs placebo, mildly symptomatic PAH) -> A",
          assign("NCT00091715", live["NCT00091715"])[0], "A_monotherapy")
    # THE TWO THAT THE FIRST PRECEDENCE RULE GOT WRONG, pinned so it cannot come back.
    # Both admit adolescents (minimumAge 12) and both are ADULT trials; `minimumAge < 18`
    # assigned them to the paediatric reading and took reading A's anchor and the object's own
    # reading-B trial out of their reviews.
    for nct in ("NCT00091715", "NCT00303459"):
        st, study, _d = X.fetch_raw(nct, fields="protocolSection")
        check("%s admits adolescents and is NOT paediatric" % nct,
              is_paediatric(study["protocolSection"])[0], False)
    for nct in ("NCT00319020", "NCT00319267"):
        st, study, _d = X.fetch_raw(nct, fields="protocolSection")
        check("%s has no adult stratum and IS paediatric" % nct,
              is_paediatric(study["protocolSection"])[0], True)

    # And the identity set must be a LIST, not the topic name -- class 19.
    bare = "bosentan"
    try:
        TI.locate(live["NCT00091715"], bare)
        check("locate refuses a bare string", False, True)
    except TI.TermsMustBeACollection:
        check("locate refuses a bare string", True, True)

    print("\n%s" % ("ALL KNOWN ANSWERS HELD" if not fails else "FAILED: %s" % fails))
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(selftest() if "--selftest" in sys.argv else main())
