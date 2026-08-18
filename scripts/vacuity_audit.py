"""How many of each gate's results were ACTUALLY ADJUDICATED, on the population it runs on.

WHY THIS EXISTS. CHK024 emitted 115 results on this corpus, passed all 115, and decided
nothing in any of them -- it adjudicates only NETWORK method claims and every artefact here
claims `pairwise`. WE FOUND IT BECAUSE A CEILING MOVED, not because anyone asked. Fifteen
new artefacts pushed the INVALID share past 50% and made visible a defect that had been
counted as coverage the entire time.

That is not a CHK024 problem. It is a question owed by every check in the registry, and it
has never been asked of any of them.

THREE COLUMNS, and the third is the one that matters:

  EMITTED       how many payloads this corpus actually hands the check. Zero means the
                check has never run here at all, whatever the ledger says about it.

  ADJUDICATED   how many of those produced a verdict that DEPENDED on what the check reads.
                A PASS that survives forcing its own observation terms to their flipping
                values did not depend on them, and it is not evidence of anything.

  FAILABLE      is there a CONSTRUCTIBLE FAILING INPUT IN THIS CORPUS -- can a real payload
                from a real object be mutated into a FAIL? "In principle" does not count.
                A check that cannot fail on anything we hold cannot protect anything we hold.

A gate with zero adjudications is NOT PASSING. Every green it contributed to is worth
exactly what the gate is worth, which is nothing. That includes tonight's "all preconditions
clean" on the fifteen.
"""
from __future__ import annotations
import glob
import io
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
if __name__ == "__main__":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

from nafis_harness.artefact import ARTEFACT_DECIDABLE, payloads_for  # noqa: E402
from nafis_harness import Verdict, build_registry  # noqa: E402

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def main() -> int:
    reg = build_registry()
    all_ids = reg.ids()

    stat = {c: {"emit": 0, "adj": 0, "vac": 0, "fail": 0, "failable": False}
            for c in all_ids}

    arts = sorted(glob.glob(os.path.join(REPO, "build-artefacts", "*.json")))
    for path in arts:
        try:
            art = json.load(io.open(path, encoding="utf-8"))
        except Exception:
            continue
        for check_id, payload in payloads_for(art):
            s = stat.setdefault(check_id, {"emit": 0, "adj": 0, "vac": 0,
                                           "fail": 0, "failable": False})
            s["emit"] += 1
            try:
                chk = reg.get(check_id)
            except KeyError:
                continue
            try:
                r = chk.fn(payload)
            except Exception:
                continue
            if r.verdict is Verdict.FAIL:
                s["adj"] += 1
                s["fail"] += 1
                s["failable"] = True
                continue
            if r.verdict is Verdict.INVALID:
                continue
            # PASS -- did it depend on anything?
            #
            # CALL THE HARNESS'S OWN run_vacuity RATHER THAN REIMPLEMENTING IT.
            # My first version reimplemented the mutation loop and got a different
            # answer from the gate on the same payloads -- 118 vacuous against the
            # gate's 8 -- because it missed two things the real one handles:
            # list-valued mutators, and the rule that A MUTATION WHICH CHANGES
            # NOTHING TESTS NOTHING. Forcing a field to a value the payload already
            # holds produces a byte-identical "mutant", and the surviving PASS is
            # evidence of nothing at all. An audit of the instruments that
            # reimplements one of them is the same error it exists to find.
            rep = chk.run_vacuity(payload)
            if rep.get("vacuous_terms"):
                s["vac"] += 1
            else:
                s["adj"] += 1
            if not s["failable"]:
                for term, mut in (chk.observation_terms or {}).items():
                    try:
                        produced = mut(payload)
                    except Exception:
                        continue
                    for m in (produced if isinstance(produced, list) else [produced]):
                        if not isinstance(m, dict) or m == payload:
                            continue
                        m.pop("_mutant_label", None)
                        try:
                            if chk.fn(m).verdict is Verdict.FAIL:
                                s["failable"] = True
                        except Exception:
                            pass

    print("=" * 92)
    print("VACUITY AUDIT -- every gate against the population it actually runs on")
    print("=" * 92)
    print("%-38s %8s %12s %10s %10s" %
          ("CHECK", "EMITTED", "ADJUDICATED", "VACUOUS", "FAILABLE"))
    print("-" * 92)

    never, vacuous_only, unfailable, healthy = [], [], [], []
    for c in sorted(stat):
        s = stat[c]
        f = "yes" if s["failable"] else "NO"
        print("%-38s %8d %12d %10d %10s" % (c[:38], s["emit"], s["adj"], s["vac"], f))
        if s["emit"] == 0:
            never.append(c)
        elif s["adj"] == 0:
            vacuous_only.append(c)
        elif not s["failable"]:
            unfailable.append(c)
        else:
            healthy.append(c)

    print()
    print("=" * 92)
    print("NEVER EMITTED ON THIS CORPUS (%d) -- these have never run here at all."
          % len(never))
    print("Whatever the ledger says about them is a claim about code, not about coverage.")
    for c in never:
        print("   %s" % c)
    print()
    print("EMITTED BUT NEVER ADJUDICATED (%d) -- the CHK024 shape." % len(vacuous_only))
    print("Every pass these produced was a pass about nothing, and every one was counted.")
    for c in vacuous_only:
        print("   %-38s %d emissions, 0 adjudicated" % (c, stat[c]["emit"]))
    print()
    print("ADJUDICATED BUT NOT FAILABLE HERE (%d) -- no constructible failing input"
          % len(unfailable))
    print("IN THIS CORPUS. It may fail somewhere; it cannot protect anything we hold.")
    for c in unfailable:
        print("   %-38s %d emissions, %d adjudicated, 0 reachable failures"
              % (c, stat[c]["emit"], stat[c]["adj"]))
    print()
    print("HEALTHY -- emitted, adjudicated, and failable on real payloads (%d)"
          % len(healthy))
    for c in healthy:
        print("   %-38s %d/%d adjudicated%s"
              % (c, stat[c]["adj"], stat[c]["emit"],
                 ", %d real FAILs" % stat[c]["fail"] if stat[c]["fail"] else ""))
    print()
    tot_e = sum(s["emit"] for s in stat.values())
    tot_a = sum(s["adj"] for s in stat.values())
    print("=" * 92)
    print("TOTAL: %d emissions, %d adjudicated (%.0f%%), %d checks defined, %d that ever "
          "ran here" % (tot_e, tot_a, 100.0 * tot_a / tot_e if tot_e else 0.0,
                        len(stat), len(stat) - len(never)))
    print()
    print("A GATE WITH ZERO ADJUDICATIONS IS NOT PASSING. Reporting one as a pass is the")
    print("same error as reporting a SKIP as a pass, one layer further out.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
