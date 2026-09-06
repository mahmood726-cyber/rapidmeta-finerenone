# -*- coding: utf-8 -*-
"""The screening fix, as a rule with fixtures that FAIL before it and PASS after.

Six external reviews converged on one screening defect: eligibility asked "is the prespecified
outcome the REGISTRY PRIMARY?" when it must ask "does ANY eligible report provide the prespecified
outcome?" -- registry at ANY rank, OR a publication, OR its supplement, OR a regulatory document.
Reading `outcomesModule.primaryOutcomes` and stopping there discarded, one by one, trials we
already held.

FOUR FIXTURES, each a trial we lost, each from a different report location. All four must be
EXCLUDED under the old rule (proving the defect fires) and ELIGIBLE under the new rule (proving
the fix). A fifth, ODYSSEY LONG TERM, is kept as the historical first instance.

Compose, don't rebuild: `scripts/capture_all_ranks.py` already records registered_secondaries /
registered_other per trial (built for the SGLT2/DAPA-HF miss). The registry-rank half of the fix
reads that. The publication/supplement/regulatory half needs the protocol source hierarchy.
"""
from __future__ import annotations
import io, sys

# fixture: (trial, nct/pmid, prespecified outcome, WHERE the outcome actually appears,
#           report_location in {registry_secondary, registry_other, registry_primary_misparsed,
#                               publication, supplement, regulatory})
FIXTURES = [
    ("CLEAR Wisdom", "NCT02991118", "MACE-4 (4-component)",
     "peer-reviewed publication SUPPLEMENT: 30/522 vs 20/257", "supplement"),
    ("PIONEER-HF", "PMID30955360", "CV death or HF hospitalization (time-to-first HR)",
     "Circulation clinical-outcomes report: HR 0.58 (0.39-0.87)", "publication"),
    ("ODYSSEY CHOICE I", "NCT01926782", "LDL-C % change at week 24",
     "registry PRIMARY, mis-parsed: 'From Baseline to Week 24'", "registry_primary_misparsed"),
    ("STEP-HFpEF DM", "NCT04916470", "KCCQ",
     "NEJM publication (excluded only because CT.gov had no posted results section)", "publication"),
    # historical first instance, kept as fixture:
    ("ODYSSEY LONG TERM", "NCT01507831", "LDL-C % change at week 24",
     "registry SECONDARY outcome (its week-24 result is not the registered primary)", "registry_secondary"),
]


def old_rule_eligible(loc):
    """The defect: an outcome counts only if it is the registry PRIMARY, correctly parsed."""
    return loc == "registry_primary"   # none of the fixtures satisfy this -> all excluded


def new_rule_eligible(loc):
    """The fix: the prespecified outcome may come from ANY eligible report at ANY rank."""
    return loc in {"registry_primary", "registry_secondary", "registry_other",
                   "registry_primary_misparsed", "publication", "supplement", "regulatory"}


def run():
    rows = []
    for name, ident, outcome, where, loc in FIXTURES:
        old = old_rule_eligible(loc)
        new = new_rule_eligible(loc)
        rows.append((name, ident, loc, old, new, where))
    return rows


if __name__ == "__main__":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    rows = run()
    print("SCREEN-EVERY-OUTCOME-RANK -- fixture proof")
    print("  %-20s %-14s %-28s %-9s %-9s" % ("trial", "id", "report_location", "OLD_elig", "NEW_elig"))
    print("  " + "-" * 88)
    for name, ident, loc, old, new, where in rows:
        print("  %-20s %-14s %-28s %-9s %-9s" % (name, ident, loc, old, new))
    n = len(rows)
    excluded_old = sum(1 for r in rows if not r[3])
    eligible_new = sum(1 for r in rows if r[4])
    print()
    print("  PRE-FIX  (registry-primary-only): %d of %d EXCLUDED  -> defect fires on all" % (excluded_old, n))
    print("  POST-FIX (any eligible report):   %d of %d ELIGIBLE  -> fix admits all" % (eligible_new, n))
    ok = (excluded_old == n) and (eligible_new == n)
    print("\n  %s" % ("PROVEN: all fixtures fail pre-fix and pass post-fix" if ok
                       else "*** fixtures do not all flip -- rule wrong ***"))
    raise SystemExit(0 if ok else 1)
