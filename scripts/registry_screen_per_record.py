# -*- coding: utf-8 -*-
"""Re-run the REGISTRY screen recording ONE DECISION PER REGISTRATION.

WHY. `search_executed_2026_08_30.screen` reports counts by reason --
`excluded_not_dapivirine: 16`, `excluded_not_a_ring: 20`, and so on -- with
only the two withdrawn trials named. So 61 of 63 exclusions cannot be checked
by a reader: a count by reason says how many were dropped and never which.
That is the same defect as the bibliographic count-table, at a smaller scale,
and on the tab whose whole job is to show the working.

⭐ THE SPLIT THAT MATTERS. This SCRIPT is topic-specific -- its rules name a
drug and a formulation. The RENDERER is not: `projectors_evidence.
registry_screen_card` draws whatever per-record dispositions an object carries,
under the declared key `screen_per_record`, for any topic. Rules are per topic
because eligibility IS a per-topic judgement; rendering them is not.

⛔ AND THE PHASE FILTER GOES THROUGH THE HARNESS RULE. `screen_rules.phase_keep`
refuses to run until the caller states in a sentence what registry phase `NA`
means for this screen, and KEEPS `NA` by default -- because NCT01539226, a
1,959-participant double-blind placebo-controlled efficacy trial, is registered
phases:["NA"] and a PHASE3 filter drops half this review's evidence while
reporting a clean count.

    python scripts/registry_screen_per_record.py --apply
"""
import io
import json
import os
import re
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "ssot"))

import screen_rules as SR            # noqa: E402

UA = "rapidmeta-systematic-review/1.0 (mailto:mahmood726@gmail.com)"
OBJ = os.path.join(ROOT, "ssot", "agyw-hiv-prep-review",
                   "agyw-hiv-prep-review.json")
RAW = os.path.join(ROOT, "evidence", "2026-08-30-dapivirine-ahead",
                   "REGISTRY_SEARCH_RAW.json")

NA_POLICY = ("KEEP: a registry phase of NA is not evidence a study is out of "
             "scope. Eligibility here is decided on design, intervention, "
             "comparator and outcome -- never on a sponsor's phase field. "
             "NCT01539226 is registered NA and is one of the two trials this "
             "review pools.")

RX_DAPI = re.compile(r"dapivirine|TMC[\s\-]?120|R[\s\-]?147681", re.I)
RX_RING = re.compile(r"\bring\b|\brings\b|intravaginal ring|vaginal ring", re.I)
RX_HIVOUT = re.compile(r"HIV[\s\-]?1?\s*(infection|acquisition|incidence|"
                       r"seroconversion)|seroconvers", re.I)


def fetch(nct):
    u = "https://clinicaltrials.gov/api/v2/studies/%s" % nct
    r = subprocess.run(["curl", "-sL", "--max-time", "60", "-A", UA, u],
                       capture_output=True)
    raw = r.stdout.decode("utf-8", "replace")
    if not raw.strip():
        return None                       # NO_PAYLOAD -- nothing arrived
    try:
        return json.loads(raw)
    except Exception as exc:
        # RETRIEVED_CORRUPT: bytes arrived and did not parse. Announced with
        # its size rather than folded into the not-fetched bucket, because a
        # truncated write is a specimen and a missing response is a retry.
        print("   ⛔ RETRIEVED_CORRUPT %s: %d bytes did not parse (%s)"
              % (nct, len(raw), str(exc)[:60]))
        return None


def disposition(d):
    """(decision, reason) for one registration, from DECLARED criteria."""
    ps = (d or {}).get("protocolSection") or {}
    idm = ps.get("identificationModule") or {}
    des = ps.get("designModule") or {}
    arm = ps.get("armsInterventionsModule") or {}
    om = ps.get("outcomesModule") or {}
    st = ps.get("statusModule") or {}

    title = idm.get("briefTitle") or ""
    iv_text = " ".join(
        "%s %s" % (i.get("name") or "", " ".join(i.get("otherNames") or []))
        for i in (arm.get("interventions") or []))
    arms_text = " ".join("%s %s" % (a.get("label") or "", a.get("description") or "")
                         for a in (arm.get("armGroups") or []))
    blob = " ".join([title, iv_text, arms_text,
                     (ps.get("descriptionModule") or {}).get("briefSummary") or ""])
    prim = " ".join((o.get("measure") or "") for o in (om.get("primaryOutcomes") or []))
    alloc = ((des.get("designInfo") or {}).get("allocation") or "").upper()
    enroll = (des.get("enrollmentInfo") or {})
    status = (st.get("overallStatus") or "").upper()

    if not RX_DAPI.search(blob):
        return ("EXCLUDE — intervention",
                "No dapivirine or development code in the title, interventions, "
                "arms or summary.")
    if not RX_RING.search(blob):
        return ("EXCLUDE — formulation",
                "Dapivirine is present but no vaginal-ring signal; dapivirine "
                "was also trialled as a gel and a film, which are a different "
                "intervention for this question.")
    # ⛔ AN ABSENT ALLOCATION IS NOT EVIDENCE OF RANDOMISATION, AND THIS IS THE
    # MIRROR OF THE PHASE-NA RULE RATHER THAN A CONTRADICTION OF IT.
    #
    # Registry phase NA is a LABELLING gap: a sponsor left a field blank and the
    # trial is still a trial, so NA is KEPT. An observational study carries no
    # allocation field because it HAS no allocation -- that is a DESIGN FACT,
    # not a gap, so absent must EXCLUDE.
    #
    # The first version tested `if alloc and alloc != "RANDOMIZED"`, so an
    # empty allocation passed. It admitted NCT01618058 -- MTN-015, an
    # OBSERVATIONAL cohort of participants who seroconverted during the
    # dapivirine ring trials -- and returned INCLUDE = 3 against a review that
    # holds 2. The count disagreeing with the held set is what surfaced it; a
    # rule that had returned 2 by luck would have shipped.
    study_type = (des.get("studyType") or "").upper()
    if study_type and study_type != "INTERVENTIONAL":
        return ("EXCLUDE — design",
                "Study type is %s, not INTERVENTIONAL." % study_type)
    if alloc != "RANDOMIZED":
        return ("EXCLUDE — design",
                "Allocation is %s. An absent allocation field is not evidence "
                "of randomisation."
                % (("recorded as %s" % alloc) if alloc else "NOT RECORDED"))
    if status == "WITHDRAWN" and str(enroll.get("count") or "0") in ("0", "None"):
        return ("EXCLUDE — no participants",
                "WITHDRAWN with enrolment %s (%s). Eligible by design, no "
                "participants and no data, so it cannot contribute."
                % (enroll.get("count"), enroll.get("type")))
    if not RX_HIVOUT.search(prim):
        return ("EXCLUDE — outcome",
                "Registered primary outcome is %r, which is not HIV-1 "
                "infection or seroconversion."
                % (prim[:110] or "not recorded"))
    comp = " ".join((a.get("type") or "") for a in (arm.get("armGroups") or []))
    if "PLACEBO" not in comp.upper() and "placebo" not in blob.lower():
        return ("EXCLUDE — comparator",
                "No placebo arm recorded; this review's declared comparator is "
                "a placebo vaginal ring.")
    return ("INCLUDE", "Randomised, dapivirine vaginal ring against a placebo "
                       "ring, HIV-1 seroconversion as the registered primary.")


def main():
    ncts = sorted(json.load(open(RAW, encoding="utf-8"))["ctgov_union_ids"])
    print("registrations to screen: %d" % len(ncts))

    records, rows = [], []
    for i, n in enumerate(ncts, 1):
        d = fetch(n)
        if not d:
            records.append({"nct": n, "title": "", "decision": "UNRESOLVED",
                            "reason": "the registration could not be fetched"})
            continue
        ps = (d.get("protocolSection") or {})
        title = (ps.get("identificationModule") or {}).get("briefTitle") or ""
        phases = ((ps.get("designModule") or {}).get("phases")) or []
        rows.append({"nct": n, "phases": phases})
        dec, why = disposition(d)
        records.append({"nct": n, "title": title, "phases": phases,
                        "decision": dec, "reason": why})
        if i % 10 == 0:
            print("  %d/%d" % (i, len(ncts)))
        time.sleep(0.2)

    # THE PHASE RULE, THROUGH THE HARNESS FUNCTION, so the NA policy is stated
    # and the kept-NA registrations are named rather than assumed.
    ph = SR.phase_keep(rows, ("PHASE3",), na_policy=NA_POLICY)

    counts = {}
    for r in records:
        counts[r["decision"]] = counts.get(r["decision"], 0) + 1

    obj = json.load(open(OBJ, encoding="utf-8"))
    se = obj["search_executed_2026_08_30"]
    se["screen_per_record"] = records
    se["screen_per_record_note"] = {
        "_what": ("ONE ROW PER REGISTRATION the ClinicalTrials.gov search "
                  "returned, with the decision and the criterion that decided "
                  "it. Replaces a count-by-reason that named 2 of 63."),
        "n": "%d of %d registrations" % (len(records), len(ncts)),
        "decisions": counts,
        "why_this_replaces_a_count": (
            "`screen` reported excluded_not_dapivirine: 16, "
            "excluded_not_a_ring: 20 and so on, naming only the two withdrawn "
            "trials. A count by reason says how many were dropped and never "
            "which, so 61 of 63 exclusions could not be checked by a reader."),
        "phase_rule": {
            "applied": "ssot/screen_rules.py phase_keep()",
            "na_policy": ph["na_policy"],
            "kept_with_phase_NA": [x["id"] for x in ph["na_kept"]],
            "n_na": ph["n_na"],
            "⛔_why": ph["⚠️_why_NA_is_kept_by_default"],
        },
        "the_renderer_is_general_and_this_script_is_not": (
            "projectors_evidence.registry_screen_card draws "
            "`screen_per_record` for ANY topic. This script's RULES name a "
            "drug and a formulation because eligibility is a per-topic "
            "judgement -- that is the judgement register's ELIGIBILITY_RULE "
            "slot, and it is per topic by nature."),
        "recorded_utc": __import__("datetime").datetime.now(
            __import__("datetime").timezone.utc).isoformat(),
    }
    tmp = OBJ + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(obj, fh, indent=1, ensure_ascii=False)
    os.replace(tmp, OBJ)

    print()
    for k, v in sorted(counts.items(), key=lambda x: -x[1]):
        print("  %-28s %3d of %d" % (k, v, len(records)))
    print()
    print("  phase NA kept: %s" % ", ".join(x["id"] for x in ph["na_kept"]))
    print("  written to search_executed_2026_08_30.screen_per_record")


if __name__ == "__main__":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8",
                                  errors="replace")
    main()
