"""MEASURE, SEPARATELY FROM ITS EXISTENCE, how far two count-gate faults reach.

TWO FAULTS, BOTH FOUND ON ARNI_HF ON 2026-08-18, BOTH IN THE FETCHER AND NOT THE GATE

  A. A VALUE THAT IS NOT A COUNT IS STORED IN A FIELD CALLED `counts`.
     The registry's outcome measures carry a unit. PARACHUTE-HF's contributed
     endpoint is posted as "Percentage of Participants With First Hospitalization
     Due to Heart Failure or Death From Cardiovascular Causes", 33.5 against 36.7.
     Those are percentages. They sit in `registration_other_outcome_counts[].counts`
     beside real participant counts, mean changes (-2.99, -4.63), exposure-adjusted
     incidence rates (25.266, 21.729) and events-per-patient-year (0.1734), with no
     unit recorded for any of them.

     What it cost: `count_provenance_gate` matched PARACHUTE-HF's row to the right
     registry outcome -- correctly, on the title -- then compared 155 and 169
     against 33.5 and 36.7 and reported "the events differ by a factor of 5". The
     row is right. 155/462 IS 33.5% and 169/460 IS 36.7%; the registry confirms the
     object digit for digit. The gate impugned a correct row.

     The dangerous direction is the other one. The FAIL branch names a row's
     numerators as some OTHER outcome when they land within 1 of that outcome's
     stored pair. A percentage in the 0-100 range can coincide with an event count
     and produce a FAIL that names a wrong source outcome.

  B. CLASSES ARE SUMMED WHEN THEY ARE A TOTAL AND ITS PARTS.
     PARADIGM-HF's posted primary carries three classes: "Primary Composite" 914
     against 1117, "CV death" 558/693, "1st HF Hospitalization" 537/658. The last
     two DECOMPOSE the first. Summing gives 2009 and 2468 -- every composite event
     counted up to three times -- and that is what is stored. The gate then said
     "events differ modestly (914/1117 against the registry's 2009/2468)". The
     object's 914 and 1117 are the registry's own Primary Composite row, exactly.

     Summing is right for a genuinely categorical outcome (causes of death, NYHA
     class) and wrong for total-plus-parts, and nothing recorded which this was.

WHAT THIS SCRIPT DOES
    Counts, across every SSOT object, how many stored count pairs are NOT plausibly
    counts, and how many stored outcomes carry more than one class. It reports the
    two separately and it does NOT fix anything: the scope of a defect is measured
    before it is described, because this project has twice described a blast radius
    it had not measured.

    Not-a-count is judged three ways, all conservative:
      - the title begins "Percentage"/"Percent" or "Change From Baseline" or
        contains "Rate" / "Number of Days" / "Score"
      - a stored value is negative
      - a stored value is not an integer

USAGE  python scripts/measure_count_units_defect.py
"""
from __future__ import annotations
import io
import json
import os
import re
import sys

if __name__ == "__main__":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SSOT = os.path.join(ROOT, "ssot")

NOT_A_COUNT_TITLE = re.compile(
    r"^\s*(percentage|percent|change from baseline|mean |median )"
    r"|\brate\b|\bratio\b|number of days|\bscore\b|per patient|per 100",
    re.I)


def is_not_a_count(title, values):
    why = []
    if title and NOT_A_COUNT_TITLE.search(title):
        why.append("title")
    for v in values:
        if isinstance(v, (int, float)) and not isinstance(v, bool):
            if v < 0:
                why.append("negative")
                break
            if float(v) != int(v):
                why.append("non-integer")
                break
    return why


def main():
    objs = []
    for d in sorted(os.listdir(SSOT)):
        p = os.path.join(SSOT, d, d + ".json")
        if os.path.isfile(p):
            objs.append((d, p))

    tot_pairs = tot_bad = 0
    tot_prim = bad_prim = 0
    objects_hit = set()
    prim_hits, other_hits = [], []

    for app, path in objs:
        try:
            with io.open(path, encoding="utf-8") as fh:
                obj = json.load(fh)
        except Exception as ex:                       # noqa: BLE001
            print("  %-46s UNREADABLE: %s" % (app, ex))
            continue
        for t in ((obj.get("inputs") or {}).get("trials") or []):
            prim = t.get("registration_primary_counts")
            if isinstance(prim, dict):
                tot_prim += 1
                vals = [prim.get("treatment_events"), prim.get("control_events")]
                why = is_not_a_count(prim.get("title") or "", vals)
                if why:
                    bad_prim += 1
                    objects_hit.add(app)
                    prim_hits.append((app, t.get("id") or t.get("nct"),
                                      (prim.get("title") or "")[:64], vals, why))
            for o in (t.get("registration_other_outcome_counts") or []):
                cts = o.get("counts") or []
                if not cts:
                    continue
                tot_pairs += 1
                why = is_not_a_count(o.get("title") or "", cts)
                if why:
                    tot_bad += 1
                    objects_hit.add(app)
                    other_hits.append((app, t.get("id") or t.get("nct"),
                                       (o.get("title") or "")[:64], cts[:2], why))

    print("STORED REGISTRY VALUES THAT ARE NOT COUNTS, in fields named `counts`")
    print("  objects scanned                       : %d" % len(objs))
    print("  primary-count rows stored             : %d" % tot_prim)
    print("  of those, NOT plausibly counts        : %d  (%.1f%%)"
          % (bad_prim, 100.0 * bad_prim / tot_prim if tot_prim else 0.0))
    print("  other-outcome count pairs stored      : %d" % tot_pairs)
    print("  of those, NOT plausibly counts        : %d  (%.1f%%)"
          % (tot_bad, 100.0 * tot_bad / tot_pairs if tot_pairs else 0.0))
    print("  objects carrying at least one         : %d" % len(objects_hit))
    print("")
    print("THE ROWS THE GATE COMPARES DIRECTLY -- primary-count rows -- are the ones")
    print("that can produce a verdict, and they are listed in full:")
    for h in prim_hits:
        print("  %-30s %-16s %-64s %s  [%s]"
              % (h[0][:30], str(h[1])[:16], h[2], h[3], ",".join(h[4])))
    if not prim_hits:
        print("  none")
    print("")
    print("A SAMPLE of the other-outcome pairs, which the gate consults when")
    print("diagnosing where a row's numerators came from:")
    for h in other_hits[:15]:
        print("  %-30s %-16s %-64s %s  [%s]"
              % (h[0][:30], str(h[1])[:16], h[2], h[3], ",".join(h[4])))
    if len(other_hits) > 15:
        print("  ... and %d more" % (len(other_hits) - 15))
    print("")
    print("NOT MEASURED HERE, and it is the second fault: how many stored primary")
    print("rows were SUMMED across classes that are a total and its parts. That")
    print("needs a re-fetch per trial to see the class structure, and a count of")
    print("rows that merely LOOK summed would be an inference, not a measurement.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
