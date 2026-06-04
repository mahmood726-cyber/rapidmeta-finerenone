#!/usr/bin/env python
"""Round 4: BREEZE-AD and IMvigor130 -- primaries found via citation lookup /
NCT verification, with app effect values cross-checked to the target trial.

  BREEZE-AD1/AD2 baricitinib (NCT03334396) -> 31995838
    Simpson et al, Br J Dermatol 2020 (10.1111/bjd.18898), "results from two
    randomized monotherapy phase III trials"; primary vIGA-AD (0,1) at wk 16
    (BREEZE-AD1 4 mg 16.8% vs placebo 4.8%) matches the app outcome. Found via
    lookup_article_by_citation after keyword search failed (the paper's PubMed
    record is not tagged with the NCT). Was citing a PRO sub-paper (33222559)
    and a review (34437922).
  IMvigor130 atezolizumab (NCT02807636) -> 32416780
    Galsky et al, Lancet 2020 (10.1016/S0140-6736(20)30230-0); NCT02807636
    confirmed in abstract. The dedicated app's record is name="IMvigor130",
    PFS HR 0.82 [0.70-0.96] == IMvigor130 PFS; the NMA app is name="IMvigor-130",
    OS HR 0.83 [0.69-1.00] == IMvigor130 OS -- both genuine IMvigor130 records
    that cited the wrong paper: the IMvigor210 paper (27939400, which is actually
    registered under NCT02108652) and a COVID-vaccine comment (32861315).

Still DEFERRED (true NCT/identity mismatch, NOT a citation swap):
  nirsevimab/MEDLEY (NCT02878330) -- the NMA record is name="MEDLEY" with a
  MEDLEY-specific effect (0.33 [0.14-0.81]) but assigned the Phase-2b NCT
  (NCT02878330, real value 0.30 [0.19-0.48]). Needs the NCT corrected to MEDLEY's
  NCT03959488 (+ its primary paper), not a PMID swap. Left for manual review.

Object-scoped, idempotent, binary-safe, dry-run-first, asserting.
"""
from __future__ import annotations
import argparse
import glob
import importlib.util
import os
import re
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_spec = importlib.util.spec_from_file_location(
    "dia", os.path.join(REPO, "scripts", "data_integrity_audit.py"))
dia = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(dia)

FIXES = {
    "NCT03334396": {"33222559": "31995838", "34437922": "31995838"},  # BREEZE-AD1/2
    "NCT02807636": {"27939400": "32416780", "32861315": "32416780"},  # IMvigor130
}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    changes = []
    apps_changed = 0
    for path in sorted(glob.glob(os.path.join(REPO, "*_REVIEW*.html"))):
        if "backup" in path:
            continue
        data = open(path, "rb").read().decode("utf-8", "replace")
        new_data = data
        app_changed = False
        for key, obj in dia.find_trial_objects(new_data):
            nct = key.split("_")[0]
            fixmap = FIXES.get(nct)
            if not fixmap:
                continue
            cur = str(dia.str_field(obj, "pmid"))
            if cur not in fixmap:
                continue
            new_pmid = fixmap[cur]
            new_obj = re.sub(r'(pmid"?\s*:\s*")' + re.escape(cur) + r'(")',
                             r"\g<1>" + new_pmid + r"\g<2>", obj, count=1)
            assert new_obj != obj, f"{os.path.basename(path)}:{key} pmid not matched"
            assert new_data.count(obj) == 1, f"{os.path.basename(path)}:{key} not unique"
            new_data = new_data.replace(obj, new_obj, 1)
            changes.append((os.path.basename(path), nct, cur, new_pmid))
            app_changed = True
        if app_changed:
            apps_changed += 1
            if not args.dry_run:
                open(path, "wb").write(new_data.encode("utf-8"))

    verb = "WOULD fix" if args.dry_run else "fixed"
    print(f"{verb} {len(changes)} pmid miscitations across {apps_changed} apps:\n")
    for app, nct, old, new in sorted(changes):
        print(f"  {nct}  {old} -> {new}  {app}")
    miss = set(FIXES) - {c[1] for c in changes}
    if miss:
        print(f"\nNOTE: no matching record for {sorted(miss)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
