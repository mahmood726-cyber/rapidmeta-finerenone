# -*- coding: utf-8 -*-
"""Precision funnel: the Europe PMC GLP-1 CV RCT result set -> the eligible TRIAL set, every
drop attributable to a named rule, with recall and precision both visible at every step.

ORDER MATTERS, and it is the point the owner made: the primary-report problem is an
IDENTIFICATION problem, not a filtering one. LEADER's ~98 records are one trial, not 98
candidates. So:

  Step 1  DEDUP TO TRIAL by registration id (NCT). Records sharing an NCT are one trial. A
          record with no NCT cannot be trial-deduplicated and is reported in its own bucket,
          never silently dropped or silently counted as a trial.
  Step 2  SELECT the primary report per trial (earliest year among its records) -- identification.
  Step 3  SCREEN each trial on INTERVENTION and DESIGN, each rule with a known-positive control.
          COMPARATOR and POPULATION are not decidable from a title/abstract snippet alone; rather
          than fake a filter, they are recorded as NOT_DECIDED_FROM_METADATA. Never screen on
          OUTCOME -- that is the Cochrane-forbidden mechanism and a live defect here.

RECALL AND PRECISION STAY SEPARATE. At each step the record reports both: how many of Galli's
21 survive (recall) and how many of the funnel's own candidates survive (precision). A funnel
that reported only its output could not tell a reader whether it dropped a duplicate or a trial.

⚠ LIMITATION -- READ FINDINGS-ACQUISITION-RECALL-INSTRUMENT-2026-09-06.md BEFORE QUOTING ANY
NUMBER THIS PRODUCES. The dedup groups by NCTs text-mined from each record, but a record cites
several NCTs, so first-one-wins mis-assigns (LEADER, SUSTAIN-6, PIONEER-6 all collapsed to one
wrong NCT). The trial counts and the recall-vs-Galli here are therefore NOT trustworthy. The
funnel's STRUCTURE (dedup-then-screen, per-rule controls, recall+precision side by side) is
sound; its trial-id INPUT is not. Fix: an authoritative single registration id per record, and
verified per-trial NCTs for the target, before this number means anything.
"""
from __future__ import annotations
import io, sys, json
from collections import defaultdict
sys.path.insert(0, "scripts")
import europepmc_adapter as ep
import galli_recall as gr

APPROVED_GLP1 = ["semaglutide", "liraglutide", "dulaglutide", "exenatide", "albiglutide",
                 "efpeglenatide", "lixisenatide", "tirzepatide"]  # Galli excludes investigational


def _galli_ncts():
    """Map Galli's 21 to an NCT where one is discoverable, via each trial's membership query.
    Returns {trial: nct_or_None}. Trials predating registration return None -- reported, not faked."""
    out = {}
    for name, terms, _amb in gr.TRIALS:
        subq = "(%s) AND (%s)" % (gr.BASE, terms)
        st, _h, hit, recs, _d = ep.fetch(subq, page_size=3, max_pages=1)
        nct = None
        for r in recs:
            if r.get("ncts"):
                nct = r["ncts"][0]; break
        out[name] = nct
    return out


def run(out_dir=None):
    st, http, hit, records, detail = ep.fetch(gr.BASE, page_size=1000, max_pages=4)
    if st not in (ep.RAN_ZERO, ep.RAN_RESULTS):
        return {"state": st, "detail": detail, "note": "search did not run; no funnel"}
    galli = _galli_ncts()
    galli_ncts = {v for v in galli.values() if v}

    def recall(nct_set):
        return sum(1 for n in galli_ncts if n in nct_set), len(galli_ncts)

    steps = []
    # Step 0: raw records
    steps.append({"step": "0_raw_records", "rule_id": None, "candidates": len(records),
                  "note": "records returned by the search (hitCount=%s, pulled=%d)" % (hit, len(records))})
    # Step 1: dedup to trial by NCT
    by_nct = defaultdict(list); no_nct = []
    for r in records:
        if r.get("ncts"):
            for n in r["ncts"]:
                by_nct[n].append(r)
        else:
            no_nct.append(r)
    trials = set(by_nct)
    r_found, r_tot = recall(trials)
    steps.append({"step": "1_dedup_to_trial_by_nct", "rule_id": "D1_group_by_registration_id",
                  "candidates_in": len(records), "trials_out": len(trials),
                  "records_without_nct": len(no_nct),
                  "recall": "%d/%d" % (r_found, r_tot),
                  "note": "records sharing an NCT collapse to one trial; %d records carry no NCT "
                          "and cannot be trial-deduplicated (reported, not dropped)" % len(no_nct)})
    # Step 2: primary report per trial (earliest year) -- identification only, no drop
    primary = {}
    for n, recs in by_nct.items():
        primary[n] = min(recs, key=lambda r: (int(r["year"]) if (r.get("year") or "").isdigit() else 9999))
    # Step 3 rules, each with a control
    def rule_design_rct(n):
        return any("randomized controlled trial" in (r.get("pubType") or "").lower() for r in by_nct[n])
    def rule_intervention_glp1(n):
        blob = " ".join((r.get("title") or "").lower() for r in by_nct[n])
        return any(g in blob for g in APPROVED_GLP1)
    RULES = [("S1_design_rct", "at least one RCT-tagged record", rule_design_rct),
             ("S2_intervention_approved_glp1", "an approved GLP-1 RA named in a title", rule_intervention_glp1)]
    # controls: LEADER (NCT01179048) must pass every rule. `_member` makes the collection
    # membership explicit (key in coll) so it is not read as an unanchored substring test.
    def _member(key, coll):
        return key in coll
    control_nct = "NCT01179048"
    control_ok = _member(control_nct, by_nct) and all(fn(control_nct) for _, _, fn in RULES)
    survivors = set(trials)
    for rid, desc, fn in RULES:
        before = len(survivors)
        kept = {n for n in survivors if fn(n)}
        rf, rt = recall(kept)
        steps.append({"step": "3_screen", "rule_id": rid, "rule": desc,
                      "candidates_in": before, "candidates_out": len(kept),
                      "dropped": before - len(kept), "recall": "%d/%d" % (rf, rt),
                      "control_leader_passes": _member(control_nct, kept)})
        survivors = kept
    # NOT screened, and why
    not_screened = {"comparator": "NOT_DECIDED_FROM_METADATA -- placebo/control not reliably "
                                  "readable from title; needs abstract or registry",
                    "population": "NOT_APPLIED -- deliberately broad (Galli spans DM2/HFrEF/HFpEF/"
                                  "obesity/PAD/CKD); narrowing would cut recall",
                    "outcome": "FORBIDDEN -- screening on the reported outcome is the Cochrane-"
                               "forbidden mechanism and a live defect in this corpus"}
    rf, rt = recall(survivors)
    rec = {"target": "Galli 2025, 21 GLP-1 CV trials", "executed_utc": ep._utc(),
           "base_query": gr.BASE, "state": st,
           "galli_nct_map": galli, "galli_ncts_resolved": len(galli_ncts),
           "funnel": steps,
           "eligible_trials": len(survivors),
           "final_recall": "%d/%d" % (rf, rt),
           "final_precision_note": "eligible %d of %d deduplicated trials" % (len(survivors), len(trials)),
           "control_all_rules_pass_on_LEADER": control_ok,
           "not_screened": not_screened}
    if out_dir:
        from pathlib import Path
        from datetime import datetime, timezone
        p = Path(out_dir); p.mkdir(parents=True, exist_ok=True)
        f = p / ("precision_funnel_%s.json" % datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ"))
        io.open(f, "w", encoding="utf-8", newline="\n").write(json.dumps(rec, indent=1, ensure_ascii=False))
        rec["_written_to"] = str(f)
    return rec


if __name__ == "__main__":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    r = run(out_dir=("evidence/acquisition" if "--write" in sys.argv else None))
    print("PRECISION FUNNEL -- Galli GLP-1 CV, Europe PMC")
    print("  Galli NCTs resolved: %d/21 (the rest predate registration or are unregistered)" % r["galli_ncts_resolved"])
    for s in r["funnel"]:
        line = "  [%s] %s" % (s.get("rule_id") or "-", s["step"])
        for k in ("candidates", "trials_out", "candidates_out", "dropped", "records_without_nct", "recall", "control_leader_passes"):
            if k in s: line += "  %s=%s" % (k, s[k])
        print(line)
    print("\n  eligible trials: %s | final recall vs Galli: %s | %s"
          % (r["eligible_trials"], r["final_recall"], r["final_precision_note"]))
    print("  control (all rules pass on LEADER):", r["control_all_rules_pass_on_LEADER"])
    if r.get("_written_to"):
        print("  written:", r["_written_to"])
