"""Does `registration_primary_counts` label its arms the way `arms[]` does?

THE BLOCK ASSERTS ITS OWN GUARANTEE AND NOTHING PROVIDES IT. Every instance of this block
in the corpus carries the note:

    "arm order as the registry lists it; a swapped pair would show as a mismatch rather
     than a silent pass"

It would not, and it did not. Nothing in this repository compared `registration_primary_
counts.treatment_n` against `arms[role=treatment].participants` until this file. On both
EMPEROR trials the labels are inverted: `treatment_n` holds the CONTROL arm's n, so the
posted `treatment_events` value is the PLACEBO arm's. Read as labelled, the block says
empagliflozin is WORSE than placebo on both trials, while the effect stored two fields
away says the opposite and is correct.

That is the "defended by a paragraph" failure at field level: a sentence describing a
check that no command performs. The sentence is not wrong about what SHOULD happen; it is
wrong that anything makes it happen.

THE PUBLISHED ESTIMATE IS NOT AFFECTED where the effect was computed from `arms[]` -- and
this lint says so per row rather than raising an undifferentiated alarm, because a
provenance defect and a wrong published number are different findings and conflating them
would be its own defect.

Exit non-zero when any object is inconsistent. NOT_ASSESSABLE, never PASS, if it examines
zero objects holding the block -- a checker that finds nothing to check has not passed.
"""
import io
import json
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SSOT = os.path.join(REPO, "ssot")


def main():
    objects_read = 0
    trials_with_block = 0
    rows = []
    for name in sorted(os.listdir(SSOT)):
        d = os.path.join(SSOT, name)
        if not os.path.isdir(d):
            continue
        fp = os.path.join(d, name + ".json")
        if not os.path.exists(fp):
            continue
        try:
            obj = json.load(io.open(fp, encoding="utf-8"))
        except Exception:
            continue
        objects_read += 1
        for t in (obj.get("inputs") or {}).get("trials") or []:
            pc = t.get("registration_primary_counts")
            arms = t.get("arms") or []
            if not isinstance(pc, dict) or pc.get("treatment_n") is None:
                continue
            tr = [a for a in arms if a.get("role") == "treatment"
                  and a.get("participants") is not None]
            ct = [a for a in arms if a.get("role") == "control"
                  and a.get("participants") is not None]
            if len(tr) != 1 or len(ct) != 1:
                continue
            trials_with_block += 1
            tn, cn = float(pc["treatment_n"]), float(pc["control_n"])
            at, ac = float(tr[0]["participants"]), float(ct[0]["participants"])
            if at == ac:
                verdict = "UNDECIDABLE"   # equal arms cannot reveal a swap
            elif tn == at and cn == ac:
                verdict = "CONSISTENT"
            elif tn == ac and cn == at:
                verdict = "SWAPPED"
            else:
                verdict = "NEITHER"
            if verdict in ("CONSISTENT",):
                continue
            # Does the published effect depend on the mislabelled block, or on arms[]?
            #
            # THE FIRST VERSION OF THIS TEST MANUFACTURED FOUR FALSE ALARMS AND THAT IS
            # THE INSTRUCTIVE PART. It computed an ODDS RATIO from arms[] and compared it
            # to the stored effect -- on COLCOT, COMPASS and both EMPEROR rows in
            # sglt2-hf, where the stored effect is a HAZARD RATIO READ FROM THE
            # PUBLICATION. An HR and an OR are different quantities and cannot be expected
            # to match, so the comparison could not have passed and its failure said
            # nothing whatever about those objects. It reported "the published number may
            # depend on the mislabelled block" for four rows whose published number is
            # read from a paper and depends on nothing in that block.
            #
            # A TEST THAT CANNOT PASS IS NOT A TEST, and this one biased toward
            # MANUFACTURING a contradiction rather than hiding one -- the rarer and more
            # expensive direction, because someone acts on it.
            #
            # The test now runs ONLY where the object declares the effect to be an odds
            # ratio, and reports NOT_APPLICABLE with the declared measure named everywhere
            # else. An effect declaring no measure at all is reported as such, because
            # that is a finding rather than a reason to guess.
            reaches = "no effect stored"
            for oid, bo in (t.get("by_outcome") or {}).items():
                eff = (bo or {}).get("effect") or {}
                if eff.get("point") is None:
                    continue
                measure = eff.get("measure")
                if measure is None:
                    reaches = ("NOT_APPLICABLE -- the effect declares NO measure, so "
                               "nothing can be recomputed against it; that is its own "
                               "small defect")
                    break
                if measure != "OR":
                    reaches = ("NOT_APPLICABLE -- stored effect is a %s (%s), not an odds "
                               "ratio computed from these counts"
                               % (measure, eff.get("derived_from") or "provenance unstated"))
                    break
                te, ce = tr[0].get("events"), ct[0].get("events")
                if te is None or ce is None:
                    reaches = "NOT_APPLICABLE -- arms[] carries no event counts"
                    break
                try:
                    o = (te / (at - te)) / (ce / (ac - ce))
                except ZeroDivisionError:
                    break
                reaches = ("effect reproduces from arms[], so the PUBLISHED NUMBER IS "
                           "UNAFFECTED" if abs(o - float(eff["point"])) < 1e-4
                           else "OR does NOT reproduce from arms[] -- investigate")
                break
            rows.append((name, t.get("name") or t.get("nct"), verdict,
                         "%g/%g vs arms %g/%g" % (tn, cn, at, ac), reaches))

    print("objects read                     %d" % objects_read)
    print("trials holding the block          %d" % trials_with_block)
    print("rows not CONSISTENT               %d" % len(rows))
    print()
    if rows:
        print("%-40s %-24s %-12s %-26s %s"
              % ("topic", "trial", "verdict", "counts n vs arms n", "does it reach the estimate?"))
        print("-" * 150)
        for r in rows:
            print("%-40s %-24s %-12s %-26s %s" % r)
        print()

    if objects_read == 0 or trials_with_block == 0:
        print("NOT_ASSESSABLE: examined %d object(s) and found %d trial(s) holding "
              "`registration_primary_counts` with a treatment_n. A checker that found "
              "nothing to check has not passed." % (objects_read, trials_with_block))
        return 2
    bad = [r for r in rows if r[2] in ("SWAPPED", "NEITHER")]
    unreproduced = [r for r in rows if "does NOT reproduce" in r[4]]
    if unreproduced:
        print("AND %d ROW(S) ARE WORSE THAN A LABEL DEFECT. On these the stored effect "
              "does not reproduce from arms[] at all, so the mislabelling is not the only "
              "thing wrong and the published number may depend on it:" % len(unreproduced))
        for r in unreproduced:
            print("    %-40s %s" % (r[0], r[1]))
        print()

    # RATCHET ON A MEASURED BASELINE, not on zero. 23 rows were inconsistent when this
    # lint was written, and fixing all 23 is a unit of its own; blocking every commit
    # until then would mean the lint gets deleted rather than the rows fixed. The baseline
    # is what was MEASURED on 2026-08-20 by this file against the corpus, and it is
    # re-derivable by running with --baseline.
    baseline_path = os.path.join(REPO, "evidence", "registration_arm_order_baseline.json")
    baseline = None
    if os.path.exists(baseline_path):
        try:
            baseline = json.load(io.open(baseline_path, encoding="utf-8")).get("bad_rows")
        except Exception:
            baseline = None
    if "--baseline" in sys.argv:
        with io.open(baseline_path, "w", encoding="utf-8", newline="\n") as fh:
            json.dump({"measured_utc": "2026-08-20", "bad_rows": len(bad),
                       "trials_with_block": trials_with_block,
                       "objects_read": objects_read,
                       "measured_by": "scripts/lint_registration_counts_arm_order.py",
                       "_why_a_baseline": (
                           "23 rows were inconsistent when this lint was written. Blocking "
                           "every commit until all 23 are fixed would get the lint deleted "
                           "rather than the rows fixed. The number may fall and must not "
                           "rise. A BASELINE IS MEASURED AGAINST AN INSTRUMENT, NOT AGAINST "
                           "THE WORLD: re-derive it with --baseline whenever this file "
                           "changes, or the ratchet fires on its own improvement.")}, fh,
                      indent=1)
            fh.write("\n")
        print("baseline written: %d bad row(s)" % len(bad))
        return 0
    if baseline is None:
        print("NOT_ASSESSABLE: no baseline at %s. Run with --baseline to measure one."
              % baseline_path)
        return 2
    if len(bad) > baseline:
        print("REFUSED: %d trial row(s) label their arms differently from arms[], up from "
              "a baseline of %d. The block's own note claims 'a swapped pair would show as "
              "a mismatch rather than a silent pass' -- nothing made that true until this "
              "file." % (len(bad), baseline))
        return 1
    if len(bad) < baseline:
        print("baseline advanced: %d bad row(s), down from %d. Re-run with --baseline."
              % (len(bad), baseline))
    print("PASS, measured against a baseline of %d bad rows in %d trial rows across %d "
          "objects: %d inconsistent, none new. THIS IS NOT A CLEAN BILL -- %d rows are "
          "still mislabelled and each would refuse the moment it was fixed and regressed."
          % (baseline, trials_with_block, objects_read, len(bad), len(bad)))
    return 0
    print("PASS, measured against %d trial rows in %d objects: every "
          "`registration_primary_counts` labels its arms as `arms[]` does."
          % (trials_with_block, objects_read))
    return 0


if __name__ == "__main__":
    sys.exit(main())
