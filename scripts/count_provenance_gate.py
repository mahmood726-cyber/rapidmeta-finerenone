"""COUNT PROVENANCE -- do the numerator and the denominator describe the same outcome?

WHY THIS EXISTS -- THE MOST DANGEROUS CLASS FOUND IN THIS PROGRAMME
    CANGRELOR_PCI published OR 0.81 (0.71-0.91) over three CHAMPION trials. Each
    row carried the primary composite's participant denominators, EXACT TO THE
    PATIENT -- 3,889 and 3,865; 2,654 and 2,641; 5,470 and 5,469 -- against event
    counts of 8 and 5, 6 and 18, and 18 and 18.

    Those numerators were ALL-CAUSE MORTALITY, a named SECONDARY outcome in the
    same registry record. The primary composite's own counts are 290 and 276, 185
    and 210, 257 and 322: one to two ORDERS OF MAGNITUDE larger.

    Correcting it reversed the conclusion. The registry's counts pool to OR 0.8955
    (0.7526 to 1.0656), which crosses no effect; the published interval did not.

    NOTHING INTERNAL CAN SEE THIS. Five of the six numbers in each 2x2 were
    correct: both denominators, both arm labels, both roles, the trial identity.
    Only the two numerators came from elsewhere, and the odds ratio they produce
    is a perfectly well-formed number. Every consistency check in this repository
    passed it.

    SOMETHING EXTERNAL CAN: an event count must be reconcilable to the outcome it
    claims. This compares each row's counts against the registry's own counts FOR
    THE OUTCOME THE ROW NAMES, and -- when they disagree -- looks for the row's
    numbers among the OTHER outcomes in the same record, because naming the
    outcome the numbers really came from is what turns a discrepancy into a
    diagnosis.

WHAT THIS DOES NOT ESTABLISH -- written in advance
    - NOT that a matching count is the right one. A row can match the registry and
      still pool the wrong trials for the wrong question.
    - NOT that a mismatch is an error. Publications legitimately report analysis
      populations the registry does not, and adjudicated counts can differ from
      registry entries. The verdict on a bare mismatch is REVIEW, not FAIL.
    - IT IS ONLY A `FAIL` WHEN THE ROW'S NUMBERS ARE FOUND UNDER A DIFFERENT NAMED
      OUTCOME IN THE SAME RECORD. That is not a discrepancy, it is a provenance
      error with a return address, and it cannot arise by rounding or by a
      different analysis set.
    - NOTHING without stored registry counts. UNCHECKABLE, never a pass, per the
      rule in scripts/gate_integrity.py.

KNOWN FALSE ALARM, NAMED SO NOBODY RE-INVESTIGATES IT
    FIDELIO-DKD in finerenone-cv reports FAIL and IS NOT A DEFECT. That review pools
    the trial's CARDIOVASCULAR composite, 367 and 420, which FIDELIO-DKD registers
    as a SECONDARY outcome because its primary is the KIDNEY composite (504 and
    600). The row is correct. The gate matches the row's recorded
    outcome_definition against the registry's outcome TITLES, and on this object the
    two strings do not match closely enough for that lookup to fire, so it falls
    back to the primary and disagrees.

    THE FIX IS A BETTER TITLE MATCH, NOT A LOOSER VERDICT, and it is not attempted
    here: loosening the comparison to make a known-good row pass is how a check
    stops being able to fail. Recorded as a limitation with its cause.

CORPUS SCREEN, 37 objects, 2026-08-18: 4 FAIL, 2 PASS, 13 REVIEW, 18 UNCHECKABLE.
    One of the four FAILs is the FIDELIO false alarm above. The other three name the
    outcome the numbers actually came from, which is the diagnosis this gate exists
    to produce. The 18 UNCHECKABLE are objects with no complete 2x2 or no stored
    registry counts and are NOT passes.

USAGE
    python scripts/count_provenance_gate.py <object.json> [...]
    python scripts/count_provenance_gate.py --selftest
    python scripts/count_provenance_gate.py --fetch <object.json>
"""
from __future__ import annotations
import io
import json
import os
import sys

if __name__ == "__main__":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

# A row whose events differ from the registry's by more than this factor is not a
# rounding difference or an analysis-set difference. Deliberately loose: the
# founding case is off by a factor of 36.
FACTOR = 3.0


def _pair(trial, oid):
    bo = (trial.get("by_outcome") or {}).get(oid) or {}
    an = bo.get("analysed") or {}
    arms = {a.get("role"): a for a in (trial.get("arms") or [])}
    t = arms.get("treatment") or arms.get("intervention") or {}
    c = arms.get("control") or arms.get("comparator") or {}
    te, ce = t.get("events"), c.get("events")
    tn = t.get("participants") or an.get("treatment") or an.get("intervention")
    cn = c.get("participants") or an.get("control") or an.get("comparator")
    vals = [te, ce, tn, cn]
    if any(not isinstance(x, (int, float)) for x in vals):
        return None
    return tuple(float(x) for x in vals)


def assess(trial, oid="primary"):
    got = _pair(trial, oid)
    if got is None:
        return "UNCHECKABLE", "this row carries no complete 2x2"
    te, ce, tn, cn = got
    # MATCH THE OUTCOME THE ROW NAMES, NOT NECESSARILY THE REGISTRATION'S PRIMARY.
    # A review may legitimately synthesise a SECONDARY outcome: FINERENONE_CV pools
    # FIDELIO-DKD's cardiovascular composite, which that trial registers as a
    # secondary because its primary is the KIDNEY composite. Comparing against the
    # primary reported a correct row as a mismatched numerator -- the false-alarm
    # direction, and the one that kills a gate. The object records what the row
    # claims in outcome_definition; that is what gets compared.
    bo_def = (((trial.get("by_outcome") or {}).get(oid) or {}).get("outcome_definition") or "")
    def _norm(x):
        return "".join(ch for ch in str(x).lower() if ch.isalnum())[:90]
    prim = trial.get("registration_primary_counts")
    if bo_def:
        for o in (trial.get("registration_other_outcome_counts") or []):
            if _norm(o.get("title")) and _norm(o.get("title")) == _norm(bo_def):
                cts = o.get("counts") or []
                if len(cts) >= 2 and isinstance(prim, dict):
                    prim = dict(prim)
                    prim["treatment_events"], prim["control_events"] = cts[0], cts[1]
                    prim["title"] = o.get("title")
                    prim["matched_on"] = "the outcome this row names, not the registration's primary"
                break
    if not isinstance(prim, dict) or not prim:
        return "UNCHECKABLE", "no registration_primary_counts stored -- run --fetch"
    rte, rce = prim.get("treatment_events"), prim.get("control_events")
    rtn, rcn = prim.get("treatment_n"), prim.get("control_n")
    if not all(isinstance(x, (int, float)) for x in (rte, rce, rtn, rcn)):
        return ("UNCHECKABLE",
                "the registry record carries no complete 2x2 for its primary outcome")

    # THE REGISTRY DOES NOT PROMISE ARM ORDER. COLCOT lists placebo first, so a
    # naive positional comparison reported a perfect match as a mismatch -- 131/2366
    # against "170/2379, 131/2366", the same two pairs the other way round. Try both
    # orders and take the better; a genuinely swapped pair still fails on the
    # numbers, which is what matters.
    def _fit(a_e, a_n, b_e, b_n):
        return (abs(tn - a_n) <= 1 and abs(cn - b_n) <= 1,
                abs(te - a_e) <= 1 and abs(ce - b_e) <= 1)
    d1, n1 = _fit(rte, rtn, rce, rcn)
    d2, n2 = _fit(rce, rcn, rte, rtn)
    if (d2 and n2) and not (d1 and n1):
        rte, rce, rtn, rcn = rce, rte, rcn, rtn
        denom_ok, num_ok = d2, n2
    else:
        denom_ok, num_ok = d1, n1
    if denom_ok and num_ok:
        return "PASS", ("counts match the registry's primary outcome exactly: "
                        "%d/%d against %d/%d" % (te, tn, ce, cn))

    # The diagnosis: are this row's numerators some OTHER outcome in the record?
    others = trial.get("registration_other_outcome_counts") or []
    for o in others:
        pair = o.get("counts") or []
        if len(pair) >= 2 and abs(pair[0] - te) <= 1 and abs(pair[1] - ce) <= 1:
            if denom_ok:
                return ("FAIL",
                        "MISMATCHED NUMERATOR AND DENOMINATOR. The denominators %d and "
                        "%d ARE the registry's primary-outcome denominators, exactly. "
                        "The numerators %d and %d are NOT its primary counts (%d and "
                        "%d) -- they are this trial's outcome '%s'. A numerator from "
                        "one outcome over a denominator from another describes no "
                        "quantity at all."
                        % (tn, cn, te, ce, rte, rce, str(o.get("title"))[:70]))
            return ("FAIL",
                    "the counts %d and %d are this trial's outcome '%s', not the "
                    "primary this row claims" % (te, ce, str(o.get("title"))[:70]))

    if denom_ok and not num_ok:
        ratio = max((rte + 1) / (te + 1), (te + 1) / (rte + 1))
        if ratio >= FACTOR:
            return ("REVIEW",
                    "denominators match the registry exactly but the events differ by "
                    "a factor of %.0f: this row has %d and %d, the registry's primary "
                    "has %d and %d. No other outcome in the record matches the row's "
                    "numbers, so the source could not be named" % (ratio, te, ce, rte, rce))
        return ("REVIEW",
                "denominators match; events differ modestly (%d/%d against the "
                "registry's %d/%d) -- an analysis-set difference would look like this"
                % (te, ce, rte, rce))
    return ("REVIEW",
            "this row (%d/%d, %d/%d) does not match the registry's primary "
            "(%d/%d, %d/%d)" % (te, tn, ce, cn, rte, rtn, rce, rcn))


def check(obj):
    trials = ((obj.get("inputs") or {}).get("trials")) or []
    results = ((obj.get("results") or {}).get("by_outcome")) or {}
    if not trials or not results:
        return "UNCHECKABLE", ["object carries no trials or no outcome"]
    oid = (results.get("headline_outcome") if isinstance(results.get("headline_outcome"), str)
           else None) or sorted(results)[0]
    notes, worst = [], "UNCHECKABLE"
    order = {"PASS": 0, "UNCHECKABLE": 1, "REVIEW": 2, "FAIL": 3}
    seen = False
    for t in trials:
        v, why = assess(t, oid)
        notes.append("  %-22s %-13s %-12s %s"
                     % ((t.get("name") or "?")[:22], t.get("nct") or "", v, why[:170]))
        if not seen or order[v] > order[worst]:
            worst = v if not seen else (v if order[v] > order[worst] else worst)
            seen = True
    return worst, notes


def selftest() -> int:
    ok = True
    OTHERS = [{"title": "Individual Incidence of All-cause Mortality", "counts": [8, 5]},
              {"title": "Incidence of Major Bleeding", "counts": [22, 19]}]

    def row(te, ce, tn, cn, prim, others=OTHERS):
        return {"name": "CHAMPION-PCI", "nct": "NCT00305162",
                "arms": [{"role": "treatment", "label": "Cangrelor", "events": te, "participants": tn},
                         {"role": "control", "label": "Clopidogrel", "events": ce, "participants": cn}],
                "by_outcome": {"primary": {}},
                "registration_primary_counts": prim,
                "registration_other_outcome_counts": others}

    PRIM = {"treatment_events": 290, "treatment_n": 3889,
            "control_events": 276, "control_n": 3865}
    cases = [
        ("FOUNDING CANGRELOR-PCI as published: 8/3889 against 5/3865",
         row(8, 5, 3889, 3865, PRIM), "FAIL"),
        ("the SAME row with the registry's own primary counts",
         row(290, 276, 3889, 3865, PRIM), "PASS"),
        ("a big event mismatch whose source cannot be named is REVIEW, not FAIL",
         row(9, 6, 3889, 3865, PRIM, others=[]), "REVIEW"),
        ("a modest difference -- an analysis-set difference looks like this",
         row(288, 274, 3889, 3865, PRIM, others=[]), "REVIEW"),
        ("no registry counts stored is UNCHECKABLE, never a pass",
         row(8, 5, 3889, 3865, {}), "UNCHECKABLE"),
    ]
    for label, t, want in cases:
        v, why = assess(t)
        good = v == want
        ok &= good
        print("  %-60s -> %-12s (want %-12s) %s"
              % (label[:60], v, want, "correct" if good else "WRONG"))
        if not good:
            print("        " + why[:170])
    print("\nWHAT A FAILURE WOULD LOOK LIKE: the founding row passing. Its denominators are "
          "the registry's primary-outcome denominators exact to the patient, and its "
          "numerators are all-cause mortality -- and the odds ratio they produce is a "
          "perfectly well-formed number that every internal check in this repository "
          "accepted.")
    print("-> SELFTEST PASS" if ok else "-> SELFTEST FAILED")
    return 0 if ok else 1


def fetch_into(path):
    import urllib.request
    obj = json.load(open(path, encoding="utf-8"))
    n = 0
    for t in (obj.get("inputs") or {}).get("trials") or []:
        nct = (t.get("nct") or "").upper()
        if not nct.startswith("NCT"):
            continue
        url = "https://clinicaltrials.gov/api/v2/studies/%s?fields=resultsSection" % nct
        req = urllib.request.Request(url, headers={"User-Agent": "rapidmeta-registry-read"})
        with urllib.request.urlopen(req, timeout=90) as r:
            d = json.loads(r.read().decode("utf-8"))
        om = ((d.get("resultsSection") or {}).get("outcomeMeasuresModule") or {})
        others, prim = [], None
        for o in om.get("outcomeMeasures", []):
            # SUM BY ARM ACROSS CATEGORIES, never take the first two numbers.
            # ARISTOTLE's primary is reported in three category rows -- 159/173,
            # 38/76, 15/16 -- which total the 212 and 265 the trial actually
            # reports. Taking counts[0] and counts[1] read 159 and 173 and made a
            # correct row look like a mismatch. A multi-category outcome is the
            # normal shape, not an exception.
            by_group, order = {}, []
            for cls in (o.get("classes") or []):
                for cat in (cls.get("categories") or []):
                    for m in cat.get("measurements", []):
                        gid = m.get("groupId")
                        try:
                            val = float(m.get("value"))
                        except (TypeError, ValueError):
                            continue
                        if gid not in by_group:
                            by_group[gid] = 0.0
                            order.append(gid)
                        by_group[gid] += val
            counts = [by_group[g] for g in order]
            denoms = []
            for dn in (o.get("denoms") or []):
                for c in dn.get("counts", []):
                    try:
                        denoms.append(float(c.get("value")))
                    except (TypeError, ValueError):
                        pass
            # ONLY A PARTICIPANT-COUNT OUTCOME CAN BE COMPARED TO A 2x2.
            # RE-LY's registered primary is a yearly event RATE and EMPEROR's is a
            # rate too; picking their first two numbers gave "1 and 6015" and made
            # correct rows look wrong. A rate, a percentage or a hazard ratio is not
            # a numerator, and an outcome whose events exceed its denominators is not
            # a count either -- PARACHUTE-HF's 103,086 "events" over 460 patients are
            # patient-days.
            _unit = (o.get("unitOfMeasure") or "").lower()
            _is_count = ("participant" in _unit or "patient" in _unit
                         or "subjects" in _unit or _unit == "count of participants")
            if _is_count and len(counts) >= 2 and len(denoms) >= 2:
                _is_count = counts[0] <= denoms[0] + 1 and counts[1] <= denoms[1] + 1
            if o.get("type") == "PRIMARY" and prim is None and _is_count and len(counts) >= 2 and len(denoms) >= 2:
                prim = {"title": o.get("title"),
                        "treatment_events": counts[0], "control_events": counts[1],
                        "treatment_n": denoms[0], "control_n": denoms[1],
                        "note": ("arm order as the registry lists it; a swapped pair would "
                                 "show as a mismatch rather than a silent pass")}
            if len(counts) >= 2:
                others.append({"title": o.get("title"), "type": o.get("type"),
                               "counts": counts[:4]})
        if prim:
            t["registration_primary_counts"] = prim
        if others:
            t["registration_other_outcome_counts"] = others[:40]
        t["registration_counts_read_utc"] = "2026-08-18"
        n += 1
    json.dump(obj, open(path, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("read registry counts for %d trial(s) in %s" % (n, os.path.basename(path)))
    return 0


def main() -> int:
    if len(sys.argv) < 2 or sys.argv[1] == "--selftest":
        return selftest()
    if sys.argv[1] == "--fetch":
        rc = 0
        for p in sys.argv[2:]:
            rc |= fetch_into(p)
        return rc
    worst = 0
    for p in sys.argv[1:]:
        if not os.path.exists(p):
            continue
        v, notes = check(json.load(open(p, encoding="utf-8")))
        if v in ("FAIL", "REVIEW") or len(sys.argv) <= 2:
            print(os.path.basename(p))
            for n in notes:
                print(n)
            print("  -> %s" % v)
        worst = max(worst, {"PASS": 0, "UNCHECKABLE": 2, "REVIEW": 1, "FAIL": 1}.get(v, 2))
    return worst


if __name__ == "__main__":
    sys.exit(main())
