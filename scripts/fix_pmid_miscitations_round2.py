#!/usr/bin/env python
"""Round 2 PMID miscitation fixes: wrong-trial / wrong-topic / design citations.

The round-1 DESIGN/SUB heuristic missed a worse class: records that cite a paper
on an ENTIRELY UNRELATED topic (e.g. RA-BEAM citing a blood-supply policy paper,
nirsevimab citing a carbon-chain physics comment, KEYNOTE-407 citing an adrenal
tumour classification). Detected via the same cross-app PMID conflict map; each
offending PMID was confirmed unrelated by its PubMed title, and the target is the
trial's primary-results paper already cited by a sibling app (title-verified) --
EXCEPT DELIVER and SELECT-EARLY, whose primaries (36027570, 32638504) were
verified by direct PubMed lookup because no app cited them.

Every target PMID's title was checked against the trial (outputs/pmid_meta.json).
Object-scoped to the matching NCT, only replaces the exact wrong value
(idempotent), binary-safe, dry-run-first, asserting.

Deferred (NO verified primary yet -- left for a follow-up search, NOT guessed):
  SIMPLIFY-1 momelotinib (NCT01969838), RHAPSODY rilonacept (NCT03737110),
  SEQUOIA-HCM aficamten (NCT05186818), BREEZE-AD baricitinib (NCT03334396),
  plus label-mismatch reviews IMvigor (NCT02807636) and nirsevimab/MEDLEY
  (NCT02878330). See outputs/pmid_miscitation_review.md.
"""
from __future__ import annotations
import argparse
import glob
import importlib.util
import json
import os
import re
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_spec = importlib.util.spec_from_file_location(
    "dia", os.path.join(REPO, "scripts", "data_integrity_audit.py"))
dia = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(dia)

# nct -> {wrong_pmid: correct_primary_pmid}  (comment: trial, target title)
FIXES = {
    "NCT00094302": {"19850207": "24716680"},  # TOPCAT (spironolactone HFpEF)
    "NCT01106014": {"24392948": "26699168"},  # GRIPHON (selexipag PAH)
    "NCT01710358": {"27959708": "28199814"},  # RA-BEAM (baricitinib RA)
    "NCT02193074": {"29091561": "27939059"},  # ENDEAR (nusinersen SMA)
    "NCT02333799": {"32197739": "32130813"},  # Nix-TB
    "NCT02589782": {"38842323": "36546625"},  # TB-PRACTECAL
    "NCT02614183": {"30143437": "29813147"},  # EVOLVE-1 (galcanezumab)
    "NCT02629159": {"30801990": "31362993"},  # SELECT-COMPARE (upadacitinib)
    "NCT02706873": {"31379081": "32638504", "31610021": "32638504"},  # SELECT-EARLY*
    "NCT02737501": {"28501139": "30280657"},  # ALTA-1L (brigatinib; was J-ALEX)
    "NCT02775435": {"30317745": "30280635"},  # KEYNOTE-407 (pembro NSCLC)
    "NCT02813694": {"31479135": "31560372"},  # LEAP (lefamulin)
    "NCT03036813": {"28337324": "31199090"},  # HOPE (voxelotor; was preclinical)
    "NCT03164616": {"36507972": "36327426"},  # POSEIDON (durvalumab NSCLC)
    "NCT03197935": {"32450725": "32966830"},  # IMpassion031 (atezo neoadjuvant)
    "NCT03315143": {"30819210": "33200891"},  # SCORED (sotagliflozin; was review)
    "NCT03347279": {"33050934": "33979488"},  # NAVIGATOR (tezepelumab; was design)
    "NCT03391466": {"33288485": "34891224"},  # ZUMA-7 (axi-cel; was ofatumumab)
    "NCT03417245": {"34922648": "37003278"},  # ATLAS (fitusiran; was ASH meeting)
    "NCT03425643": {"33661301": "37272513"},  # KEYNOTE-671 (perioperative pembro)
    "NCT03619213": {"38265835": "36027570", "36029465": "36027570"},  # DELIVER*
    "NCT03671148": {"35701011": "34815219"},  # KEEPsAKE (risankizumab; PRO sub)
    "NCT03759379": {"34843181": "35875890"},  # HELIOS-A (vutrisiran; was ECMO)
    "NCT03895203": {"39313302": "36493791"},  # BE OPTIMAL (bimekizumab; PRO sub)
    "NCT04003142": {"37990323": "36734148"},  # SKYLIGHT (fezolinetant; PRO instr)
    "NCT04349072": {"34038706": "37639243"},  # VALOR-HCM (mavacamten; was design)
    "NCT04435626": {"40916719": "39225278"},  # FINEARTS-HF (finerenone; subgroup)
    "NCT04437511": {"36934371": "37459141"},  # TRAILBLAZER-ALZ2 (donanemab)
    "NCT04460885": {"36106652": "37356066"},  # ONWARDS-1 (icodec; was design)
    "NCT04576988": {"36841494": "36877098"},  # STELLAR (sotatercept; was surgery)
    "NCT04649359": {"40000533": "37582952"},  # MagnetisMM-3 (elranatamab)
    "NCT04770532": {"36106652": "37148899", "37222481": "37148899"},  # ONWARDS-2
    "NCT02200770": {"26666258": "31495497"},  # N-MOmentum (inebilizumab; design)
    "NCT04847557": {"39551891": "39555826"},  # SUMMIT (tirzepatide; sub for KCCQ)
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
    hit = {c[1] for c in changes}
    miss = set(FIXES) - hit
    if miss:
        print(f"\nNOTE: no matching record for {sorted(miss)} (already fixed / value differs)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
