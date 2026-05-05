"""Apply the 8 agent-confirmed PMID corrections from the n=40 stratified
random sample (Agent 7), plus emit outputs/pmid_likely_wrong.csv listing
the remaining 110 v3-classified WRONG_PMIDs for manual review.

Agent 7 confirmed via WebFetch on PubMed that these 8 PMIDs resolve to
topically unrelated papers and provided the correct PMIDs:

  BrigHTN         36302086 -> 36342143  (Freeman MW NEJM 2023)
  WOMAN-2         37499666 -> 37516131  (Brenner A Lancet 2023)
  EXPEDITION-1    28728681 -> 28818546  (Forns X Lancet Infect Dis 2017)
  PURPOSE-1       39046957 -> 39046268  (one-digit-off transcription)
  KEN-SHE         35143335 -> 35693867  (Barnabas RV NEJM Evid 2022)
  EMBARK          39320319 -> 38978283  (Mendell JR Nat Med 2024)
  HPTN 082        32298430 -> 33513145  (Celum C PLoS Med 2021)
  ACHIEVE I       31816158 -> 31800988  (Dodick DW NEJM 2019)
"""
from __future__ import annotations
import sys, io, csv
from pathlib import Path
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

REPO = Path("C:/Projects/Finrenone")

CONFIRMED_FIXES = [
    ("ALDO_SYNTHASE_REVIEW.html", "BrigHTN", "36302086", "36342143"),
    ("PPH_BUNDLE_REVIEW.html", "WOMAN-2", "37499666", "37516131"),
    ("HEPATITIS_HCV_DAA_REVIEW.html", "EXPEDITION-1", "28728681", "28818546"),
    ("HIV_LA_PREP_REVIEW.html", "PURPOSE-1", "39046957", "39046268"),
    ("HPV_DOSE_REDUCTION_REVIEW.html", "KEN-SHE", "35143335", "35693867"),
    ("DELANDISTROGENE_DMD_REVIEW.html", "EMBARK", "39320319", "38978283"),
    ("AGYW_HIV_PREP_REVIEW.html", "HPTN 082", "32298430", "33513145"),
    ("MIGRAINE_ACUTE_REVIEW.html", "ACHIEVE I", "31816158", "31800988"),
]


def main():
    print("Applying 8 agent-confirmed PMID corrections ...")
    fixed = 0
    not_found = 0
    for fname, claim, old_pmid, new_pmid in CONFIRMED_FIXES:
        path = REPO / fname
        if not path.exists():
            # File may have been renamed (e.g., HIV_LA_PREP_NMA -> HIV_LA_PREP)
            # Look for any file containing the old PMID
            cand = list(REPO.glob(f"*{fname.split('_')[0]}*_REVIEW.html"))
            if cand:
                path = cand[0]
                print(f"  redirected {fname} -> {path.name}")
            else:
                print(f"  MISSING file {fname}")
                not_found += 1
                continue
        text = path.read_text(encoding="utf-8", errors="replace")
        old_str = f"pmid: '{old_pmid}'"
        new_str = f"pmid: '{new_pmid}'"
        if old_str not in text:
            print(f"  PMID {old_pmid} not in {path.name} (already fixed?)")
            continue
        new_text = text.replace(old_str, new_str)
        path.write_text(new_text, encoding="utf-8")
        fixed += 1
        print(f"  FIXED {path.name}: {claim}  PMID {old_pmid} -> {new_pmid}")

    print(f"\n  Fixed: {fixed}/{len(CONFIRMED_FIXES)} ({not_found} files missing)")

    # Emit pmid_likely_wrong.csv from v3 audit for manual review
    print("\nEmitting outputs/pmid_likely_wrong.csv ...")
    src = REPO / "outputs" / "pmid_audit_v3.csv"
    dst = REPO / "outputs" / "pmid_likely_wrong.csv"
    rows = list(csv.DictReader(open(src, encoding="utf-8")))
    confirmed_keys = {(f, c) for f, c, _, _ in CONFIRMED_FIXES}
    likely_wrong = [
        r for r in rows
        if r["status_v3"] == "WRONG_PMID"
        and not any(r["claimed_name"].startswith(c) and r["file"] == f for f, c in confirmed_keys)
    ]
    if likely_wrong:
        with dst.open("w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=list(likely_wrong[0].keys()))
            w.writeheader()
            w.writerows(likely_wrong)
        print(f"  {len(likely_wrong)} rows for manual review")


if __name__ == "__main__":
    main()
