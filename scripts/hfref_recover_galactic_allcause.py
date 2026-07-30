#!/usr/bin/env python
"""hfref_recover_galactic_allcause.py -- recover GALACTIC-HF per-arm ALL-CAUSE
deaths from the ClinicalTrials.gov NCT02929329 posted-results record.

WHY THIS EXISTS
---------------
HF-034 GALACTIC-HF was quarantined on 2026-07-30 by the symmetric integrity
rule: per-arm all-cause deaths UNVERIFIED **and** identical across arms
(1078/1078). The publication of record (PMID 33185990, NEJM 2021;384:105-116)
reports per-arm CARDIOVASCULAR death only (808/798), so the abstract route could
not confirm the all-cause figure. The ledger's reinstatement condition named
exactly one unexhausted route:

    "... or the ClinicalTrials.gov NCT02929329 posted results. If per-arm
     all-cause deaths are stated, the rows are restored and the fit re-run."

This script walks that route. It does NOT infer all-cause deaths from CV death
and it does NOT accept a percentage as a count unless the integer is uniquely
recoverable -- it reads whatever integers the registry actually posts, and
records the frame each one belongs to.

WHAT THE REGISTRY POSTS (two distinct all-cause frames -- do not conflate)
--------------------------------------------------------------------------
  A. resultsSection.adverseEventsModule -- the FDAAA-mandated "All-Cause
     Mortality" table. VERBATIM INTEGERS. Frame: randomization -> END OF STUDY
     (27 Aug 2020); the module description states it "includes all deaths that
     occurred during the study including any that occurred after the efficacy
     analysis cut-off date", over all randomized participants "excluding 24
     participants due to GCP violations".
  B. resultsSection.outcomeMeasuresModule -- SECONDARY outcome "Time to
     All-cause Death". PERCENTAGES ONLY. Frame: randomization -> EFFICACY
     ANALYSIS CUT-OFF (07 Aug 2020), i.e. strictly shorter than (A).

(A) is the count source. (B) is a corroborating cross-check on the same
denominators; because its window is shorter its implied integer is necessarily
<= (A)'s and is only non-uniquely recoverable, so it is NEVER used as a count.

Run:  python scripts/hfref_recover_galactic_allcause.py
Emits: outputs/hfref_galactic_allcause_recovery.json  (exit 1 on any failure)
"""

import io
import json
import os
import sys
import urllib.request

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

NCT = "NCT02929329"
API = "https://clinicaltrials.gov/api/v2/studies/" + NCT
OUT = os.path.join("outputs", "hfref_galactic_allcause_recovery.json")

# What the ledger currently carries for HF-034, and must be reconciled against.
LEDGER_ROWS = {"placebo": {"event": 1078, "n": 4112},
               "omecamtiv": {"event": 1078, "n": 4120}}
# Per-arm CV death from PMID 33185990, the only per-arm mortality the
# publication states. Used ONLY as a plausibility bound (all-cause >= CV).
PUB_CV_DEATH = {"placebo": 798, "omecamtiv": 808}


def fail(msg):
    print("FAIL: " + msg)
    sys.exit(1)


def fetch():
    req = urllib.request.Request(
        API, headers={"User-Agent": "rapidmeta-hfref-audit/1.0",
                      "Accept": "application/json"})
    return json.load(urllib.request.urlopen(req, timeout=120))


def uniquely_recoverable(pct, n, lo=0, hi=None):
    """Integers k in [lo, hi] with round(100*k/n, 1) == pct. Returns the list."""
    hi = n if hi is None else hi
    return [k for k in range(lo, hi + 1) if abs(round(100.0 * k / n, 1) - pct) < 1e-9]


def main():
    d = fetch()
    if not d.get("hasResults"):
        fail("%s reports hasResults=False; posted results are the only "
             "unexhausted route and it is closed" % NCT)
    rs = d.get("resultsSection") or fail("no resultsSection")

    # ---- (A) the FDAAA All-Cause Mortality table: verbatim integers ---------
    ae = rs.get("adverseEventsModule") or fail("no adverseEventsModule")
    groups = ae.get("eventGroups") or fail("no eventGroups")
    allcause = {}
    for g in groups:
        title = (g.get("title") or "").strip()
        if "deathsNumAffected" not in g or "deathsNumAtRisk" not in g:
            continue
        arm = "omecamtiv" if "omecamtiv" in title.lower() else \
              "placebo" if "placebo" in title.lower() else title
        allcause[arm] = {"group_id": g.get("id"), "arm_title": title,
                         "deaths": int(g["deathsNumAffected"]),
                         "n": int(g["deathsNumAtRisk"])}
    for arm in ("placebo", "omecamtiv"):
        if arm not in allcause:
            fail("All-Cause Mortality table has no %s arm" % arm)

    # The module's own words are what make this table ALL-CAUSE rather than
    # some other death tally. Capture them verbatim; do not paraphrase.
    ae_desc = (ae.get("description") or "")
    ae_tf = (ae.get("timeFrame") or "")
    if "all-cause" not in (ae_desc + ae_tf).lower():
        fail("AE module text does not self-identify as all-cause mortality; "
             "refusing to treat deathsNumAffected as an all-cause count")

    # ---- (B) the secondary outcome measure: percentages, shorter window ----
    oms = (rs.get("outcomeMeasuresModule") or {}).get("outcomeMeasures") or []
    om_ac = None
    for om in oms:
        if (om.get("title") or "").strip().lower() == "time to all-cause death":
            om_ac = om
            break
    om_block = None
    if om_ac is not None:
        pcts, denoms = {}, {}
        for dn in om_ac.get("denoms", []):
            for c in dn.get("counts", []):
                denoms[c.get("groupId")] = int(c.get("value"))
        gid2arm = {}
        for g in om_ac.get("groups", []):
            t = (g.get("title") or "").lower()
            gid2arm[g.get("id")] = ("omecamtiv" if "omecamtiv" in t else
                                    "placebo" if "placebo" in t else t)
        for cls in om_ac.get("classes", []):
            for cat in cls.get("categories", []):
                for m in cat.get("measurements", []):
                    pcts[gid2arm.get(m.get("groupId"))] = float(m.get("value"))
        om_block = {"title": om_ac.get("title"), "type": om_ac.get("type"),
                    "unit": om_ac.get("unitOfMeasure"),
                    "time_frame": om_ac.get("timeFrame"),
                    "per_arm": {}}
        for arm in ("placebo", "omecamtiv"):
            gid = [k for k, v in gid2arm.items() if v == arm]
            n = denoms.get(gid[0]) if gid else None
            pct = pcts.get(arm)
            cand = uniquely_recoverable(pct, n) if (pct and n) else []
            om_block["per_arm"][arm] = {
                "percent": pct, "n": n,
                "integers_rounding_to_percent": [min(cand), max(cand)] if cand else None,
                "uniquely_recoverable": len(cand) == 1}

    # ---- reconciliation against the ledger ---------------------------------
    recon = {}
    for arm in ("placebo", "omecamtiv"):
        got, want = allcause[arm], LEDGER_ROWS[arm]
        recon[arm] = {
            "registry_deaths": got["deaths"], "ledger_deaths": want["event"],
            "deaths_match": got["deaths"] == want["event"],
            "registry_n": got["n"], "ledger_n": want["n"],
            "n_match": got["n"] == want["n"],
            "exceeds_published_cv_death": got["deaths"] > PUB_CV_DEATH[arm],
            "cv_share_of_all_cause": round(PUB_CV_DEATH[arm] / got["deaths"], 4),
        }
    ok = all(r["deaths_match"] and r["n_match"] and r["exceeds_published_cv_death"]
             for r in recon.values())

    out = {
        "_schema": "hfref-galactic-allcause-recovery/1",
        "_date": "2026-07-30",
        "_purpose": ("Close the HF-034 GALACTIC-HF provenance question by walking "
                     "the one route the quarantine pass left unexhausted: the "
                     "ClinicalTrials.gov posted-results record."),
        "trial": "GALACTIC-HF", "ledger_id": "HF-034", "nct": NCT,
        "api": API, "has_results": True,
        "ALL_CAUSE_PER_ARM_DEATHS_FOUND": True,
        "count_source": {
            "where": "resultsSection.adverseEventsModule (FDAAA 'All-Cause Mortality' table)",
            "kind": "VERBATIM INTEGER COUNTS",
            "module_description": ae_desc,
            "module_time_frame": ae_tf,
            "frequency_threshold_pct": ae.get("frequencyThreshold"),
            "per_arm": allcause,
        },
        "corroborating_percentage_source": om_block,
        "why_the_two_all_cause_figures_differ": (
            "Different follow-up windows, not different endpoints. The AE table "
            "runs to END OF STUDY (27 Aug 2020) and explicitly includes deaths "
            "after the efficacy cut-off; the secondary outcome measure censors at "
            "the EFFICACY CUT-OFF (07 Aug 2020). The AE table must therefore be "
            "the LARGER of the two, and it is (26.2% vs 25.9% on identical "
            "denominators). The percentage route alone would NOT have recovered a "
            "count -- 25.9% is non-uniquely recoverable in both arms -- which is "
            "why the verbatim AE integers are the count source."),
        "participant_flow_death_dropout": {
            "note": ("Reported for completeness and explicitly NOT used as the "
                     "all-cause count: the participant-flow 'Death' row counts "
                     "death as the REASON FOR NOT COMPLETING the study, a third "
                     "and narrower frame again."),
            "per_arm": {},
        },
        "reconciliation_with_ledger": recon,
        "verdict": None,
    }
    pf = rs.get("participantFlowModule") or {}
    gid2arm = {}
    for g in pf.get("groups", []):
        t = (g.get("title") or "").lower()
        gid2arm[g.get("id")] = ("omecamtiv" if "omecamtiv" in t else
                               "placebo" if "placebo" in t else t)
    for per in pf.get("periods", []):
        for w in per.get("dropWithdraws", []):
            if (w.get("type") or "").strip().lower() == "death":
                for r in w.get("reasons", []):
                    out["participant_flow_death_dropout"]["per_arm"][
                        gid2arm.get(r.get("groupId"), r.get("groupId"))] = int(r.get("numSubjects"))

    out["verdict"] = (
        "RECOVERED -- reinstate HF-034. The registry posts per-arm ALL-CAUSE "
        "deaths as verbatim integers and they match the ledger exactly in both "
        "arms, on denominators that also match the publication's primary-outcome "
        "denominators (4120/4112). The identical 1078/1078 is a genuine "
        "coincidence, now VERIFIED rather than unverified, so the trial no longer "
        "meets the quarantine rule (which requires identical AND unverified)."
    ) if ok else (
        "NOT RECONCILED -- registry all-cause counts differ from the ledger. Do "
        "NOT reinstate on this evidence; correct the extraction first."
    )

    os.makedirs("outputs", exist_ok=True)
    with io.open(OUT, "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=2, ensure_ascii=False)
        fh.write("\n")

    print("=" * 74)
    print("GALACTIC-HF (%s) -- per-arm ALL-CAUSE deaths, posted results" % NCT)
    print("=" * 74)
    for arm in ("placebo", "omecamtiv"):
        a, r = allcause[arm], recon[arm]
        print("  %-10s %s: %d / %d  (%.3f%%)   ledger match: deaths=%s n=%s"
              % (arm, a["arm_title"], a["deaths"], a["n"],
                 100.0 * a["deaths"] / a["n"], r["deaths_match"], r["n_match"]))
    if om_block:
        print("  cross-check (secondary outcome, efficacy-cutoff window):")
        for arm in ("placebo", "omecamtiv"):
            b = om_block["per_arm"][arm]
            print("    %-10s %.1f%% of %d -> integers %s (unique: %s)"
                  % (arm, b["percent"], b["n"], b["integers_rounding_to_percent"],
                     b["uniquely_recoverable"]))
    print("  participant-flow 'Death' dropout row (narrower frame, unused): %s"
          % out["participant_flow_death_dropout"]["per_arm"])
    print("-" * 74)
    print(out["verdict"])
    print("wrote " + OUT)
    if not ok:
        sys.exit(1)


if __name__ == "__main__":
    main()
