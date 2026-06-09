"""Fix structurally-wrong trial PMIDs found by audit_citation_consistency.py.

Each fix is (file, exact trial name, old_pmid, new_pmid, note). The NEW pmid was
verified against PubMed (journal+volume+pages+author+title match the trial the
dashboard intends to cite). Replacement anchors on the FULL minified token
`name:"<exact name>",pmid:"<old>"`, which is unique even when the same wrong
pmid was copied onto two trials (e.g. 29803590 is the CORRECT pmid for
RADIANCE-HTN SOLO but was also wrongly used for SPYRAL HTN-ON MED in the same
file -- name-anchoring touches only the SPYRAL block).

Idempotent: if the old token is absent and the new token already present, skip.

Usage:
    python scripts/fix_wrong_pmids.py --dry-run
    python scripts/fix_wrong_pmids.py --apply
"""
from __future__ import annotations
import argparse, io, os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# (file, exact trial name, OLD pmid, NEW pmid, verified-source note)
FIXES = [
    ("ATTR_CM_REVIEW.html", "ATTRibute-CM", "33725199", "38197816",
     "Gillmore JD NEJM 2024;390:132-142 acoramidis (was Curr Oncol Rep review)"),
    ("CRYPTOCOCCAL_MENINGITIS_AFRICA_REVIEW.html", "ACTA (Molloy 2018)", "29539276", "29539274",
     "Molloy SF NEJM 2018;378:1004-1017 (was NEJMicm lithium case report; 2-digit transposition)"),
    ("CRYPTOCOCCAL_MENINGITIS_AFRICA_REVIEW.html", "AMBITION-cm (Jarvis 2022)", "35320648", "35320642",
     "Jarvis JN NEJM 2022;386:1109-1120 AMBITION-cm"),
    ("CD_BIOLOGICS_NMA_REVIEW.html", "CLASSIC-1", "19201775", "16472588",
     "Hanauer SB Gastroenterology 2006;130:323-33 CLASSIC-I (was Colombel Gut 2009)"),
    ("DOAC_CANCER_VTE_REVIEW.html", "HOKUSAI VTE-Cancer", "26271200", "29231094",
     "Raskob GE NEJM 2018;378:615-624 Hokusai VTE-Cancer"),
    ("DOAC_CANCER_VTE_REVIEW.html", "SELECT-D", "34172290", "29746227",
     "Young AM JCO 2018;36:2017-2023 SELECT-D"),
    ("DOAC_CANCER_VTE_REVIEW.html", "ADAM VTE", "28837207", "31630479",
     "McBane RD JTH 2020;18:411-421 ADAM VTE results (was design paper)"),
    ("INCRETIN_HFpEF_REVIEW.html", "STEP-HFpEF", "38599221", "37622681",
     "Kosiborod MN NEJM 2023;389:1069-1084 STEP-HFpEF"),
    ("RIVAROXABAN_VASC_REVIEW.html", "ATLAS ACS 2", "21570509", "22077192",
     "Mega JL NEJM 2012;366:9-19 ATLAS ACS 2-TIMI 51 (was ATLAS ACS-TIMI 46)"),
    ("RIVAROXABAN_VASC_REVIEW.html", "COMPASS", "28754388", "28844192",
     "Eikelboom JW NEJM 2017;377:1319-1330 COMPASS results (was design paper)"),
    ("RENAL_DENERV_REVIEW.html", "SPYRAL HTN-ON MED", "29803590", "29803589",
     "Kandzari DE Lancet 2018;391:2346-2355 SPYRAL HTN-ON MED (was RADIANCE-HTN SOLO pmid)"),
    ("RENAL_DENERV_REVIEW.html", "SPYRAL HTN-OFF MED", "32411742", "32234534",
     "Bohm M Lancet 2020;395:1444-1451 SPYRAL HTN-OFF MED Pivotal"),
    ("TYVAC_TYPHOID_REVIEW.html", "TyVAC Nepal", "31800954", "31800986",
     "Shakya M NEJM 2019;381:2209-2218 TyVAC Nepal"),
    ("TYVAC_TYPHOID_REVIEW.html", "TyVAC Bangladesh", "34384550", "34384540",
     "Qadri F Lancet 2021;398:675-684 TyVAC Bangladesh"),
    ("PEDIATRIC_HIV_ART_REVIEW.html", "CHAPAS-3 (NRTI backbone in paeds)", "26718098", "26481928",
     "Mulenga V Lancet Infect Dis 2015;16:169-79 CHAPAS-3"),
]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    if not (args.apply or args.dry_run):
        args.dry_run = True

    applied = skipped = errors = 0
    for fname, name, old, new, note in FIXES:
        path = os.path.join(ROOT, fname)
        if not os.path.exists(path):
            print(f"ERROR  {fname}: file not found"); errors += 1; continue
        t = open(path, encoding="utf-8", errors="replace").read()
        old_tok = f'name:"{name}",pmid:"{old}"'
        new_tok = f'name:"{name}",pmid:"{new}"'
        n_old = t.count(old_tok)
        if n_old == 0:
            if new_tok in t:
                print(f"SKIP   {fname} [{name}]: already {new} (idempotent)"); skipped += 1
            else:
                print(f"ERROR  {fname} [{name}]: token not found (old {old} nor new {new})"); errors += 1
            continue
        if n_old != 1:
            print(f"ERROR  {fname} [{name}]: anchor occurs {n_old}x (expected 1)"); errors += 1
            continue
        if args.apply:
            open(path, "w", encoding="utf-8").write(t.replace(old_tok, new_tok))
        print(f"{'FIX  ' if args.apply else 'WOULD'} {fname} [{name}]: {old} -> {new}  ({note})")
        applied += 1

    mode = "APPLIED" if args.apply else "DRY-RUN"
    print(f"\n[{mode}] fixed={applied} skipped(idempotent)={skipped} errors={errors}")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    raise SystemExit(main())
