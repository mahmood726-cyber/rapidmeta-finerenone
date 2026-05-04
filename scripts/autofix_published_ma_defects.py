"""Auto-fix the 15 clear-cut per-trial transcription defects identified by
compare_to_published_mas.py. User directive 2026-05-04: "autofix for now, they
will all be checked before publication".

NOT included (require manual scope verification):
- BPAL_MDRTB TB-PRACTECAL (favorable vs unfavorable framing, both correct)
- DONANEMAB TRAILBLAZER-ALZ 2 (different outcome, binary vs continuous)
- LIPID_HUB VITAL (different outcome scope)
- INCRETINS_T2D EXSCEL (HbA1c MD structural field-name issue)
- BTKI_CLL_NMA RESONATE (timepoint difference)
- ELEVATE-TN in 2 files (arm-selection difference)
- UC_BIOLOGICS / CD_BIOLOGICS / JAK_UC / TOFACITINIB_UC RD-vs-RR label confusion
  (numbers > 1 with RD label — fix requires recalc not substitution)
- TNK_VS_TPA AcT/EXTEND-IA TNK (RD-vs-RR label confusion)

Idempotent: each fix uses unique (name + old_value) substring to avoid double-application.
"""
from __future__ import annotations
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
from pathlib import Path

REPO = Path("C:/Projects/Finrenone")

# Each fix: (file, trial_name, old_HR_part, new_HR_part)
# old/new are the substring containing publishedHR + hrLCI + hrUCI to make unique.
FIXES = [
    # ACS_ANTIPLATELET_NMA TWILIGHT — published BARC 2/3/5 HR 0.56 (Mehran 2019)
    ("ACS_ANTIPLATELET_NMA_REVIEW.html", "TWILIGHT",
     "publishedHR: 0.99, hrLCI: 0.78, hrUCI: 1.25",
     "publishedHR: 0.56, hrLCI: 0.45, hrUCI: 0.68"),

    # ANTI_CD20_MS_NMA ASCLEPIOS II — published ARR ratio 0.51 (Hauser 2020)
    ("ANTI_CD20_MS_NMA_REVIEW.html", "ASCLEPIOS II",
     "publishedHR: 0.42, hrLCI: 0.31, hrUCI: 0.56",
     "publishedHR: 0.51, hrLCI: 0.41, hrUCI: 0.62"),

    # HIGH_EFFICACY_MS ASCLEPIOS II — same fix
    ("HIGH_EFFICACY_MS_REVIEW.html", "ASCLEPIOS II",
     "publishedHR: 0.41, hrLCI: 0.29, hrUCI: 0.58",
     "publishedHR: 0.51, hrLCI: 0.41, hrUCI: 0.62"),

    # ANTIAMYLOID_AD_NMA — EMERGE/ENGAGE swap. Two-step using markers to avoid clobber.
    # EMERGE published MD -0.39; current value 0.03. Use intermediate marker.
    ("ANTIAMYLOID_AD_NMA_REVIEW.html", "EMERGE_step1",
     "name: 'EMERGE', pmid: '32490830', phase: 'III', year: 2019, tE: 1340, tN: 1638, cE: 1376, cN: 1647, group: 'Aducanumab IV monthly vs placebo (EMERGE; primary CDR-SB at 78w MD)', publishedHR: 0.03, hrLCI: -0.27, hrUCI: 0.34",
     "name: 'EMERGE', pmid: '32490830', phase: 'III', year: 2019, tE: 1340, tN: 1638, cE: 1376, cN: 1647, group: 'Aducanumab IV monthly vs placebo (EMERGE; primary CDR-SB at 78w MD)', publishedHR: -0.39, hrLCI: -0.69, hrUCI: -0.09"),
    # ENGAGE published MD 0.03 (NS); current value -0.39
    ("ANTIAMYLOID_AD_NMA_REVIEW.html", "ENGAGE_swap",
     "name: 'ENGAGE', pmid: '32490830', phase: 'III', year: 2019, tE: 1322, tN: 1647, cE: 1313, cN: 1653, group: 'Aducanumab IV monthly vs placebo (ENGAGE; primary CDR-SB at 78w MD)', publishedHR: -0.39, hrLCI: -0.69, hrUCI: -0.09",
     "name: 'ENGAGE', pmid: '32490830', phase: 'III', year: 2019, tE: 1322, tN: 1647, cE: 1313, cN: 1653, group: 'Aducanumab IV monthly vs placebo (ENGAGE; primary CDR-SB at 78w MD)', publishedHR: 0.03, hrLCI: -0.27, hrUCI: 0.34"),

    # BIOLOGIC_ASTHMA MENSA — published exacerbation RR 0.53 (Ortega 2014)
    ("BIOLOGIC_ASTHMA_REVIEW.html", "MENSA",
     "publishedHR: 0.47, hrLCI: 0.35, hrUCI: 0.64",
     "publishedHR: 0.53, hrLCI: 0.40, hrUCI: 0.69"),

    # BIOLOGIC_ASTHMA CALIMA — published RR 0.72 (FitzGerald 2016)
    ("BIOLOGIC_ASTHMA_REVIEW.html", "CALIMA",
     "publishedHR: 0.64, hrLCI: 0.49, hrUCI: 0.85",
     "publishedHR: 0.72, hrLCI: 0.54, hrUCI: 0.95"),

    # SEVERE_ASTHMA_NMA MENSA — same as BIOLOGIC_ASTHMA
    ("SEVERE_ASTHMA_NMA_REVIEW.html", "MENSA",
     "publishedHR: 0.47, hrLCI: 0.35, hrUCI: 0.64",
     "publishedHR: 0.53, hrLCI: 0.40, hrUCI: 0.69"),

    # CD_BIOLOGICS UNITI 1+2 — published wk6 response RR 1.50 (Feagan 2016)
    ("CD_BIOLOGICS_NMA_REVIEW.html", "UNITI 1+2",
     "publishedHR: 1.99, hrLCI: 1.27, hrUCI: 3.13",
     "publishedHR: 1.50, hrLCI: 1.14, hrUCI: 1.97"),

    # CGRP_MIGRAINE_NMA STRIVE — published MD -3.7 days (Goadsby 2017)
    ("CGRP_MIGRAINE_NMA_REVIEW.html", "STRIVE",
     "publishedHR: -1.85, hrLCI: -2.47, hrUCI: -1.23",
     "publishedHR: -3.7, hrLCI: -4.0, hrUCI: -3.4"),

    # CGRP_MIGRAINE_NMA HALO-EM — published MD -3.7 days (Dodick 2018 JAMA)
    ("CGRP_MIGRAINE_NMA_REVIEW.html", "HALO-EM",
     "publishedHR: -1.3, hrLCI: -1.79, hrUCI: -0.82",
     "publishedHR: -3.7, hrLCI: -4.1, hrUCI: -3.3"),

    # INCRETINS_T2D SURPASS-1 — published HbA1c MD -1.87% (Rosenstock 2021)
    ("INCRETINS_T2D_NMA_REVIEW.html", "SURPASS-1",
     "publishedHR: -2.11, hrLCI: -2.35, hrUCI: -1.88",
     "publishedHR: -1.87, hrLCI: -2.07, hrUCI: -1.67"),

    # POLYCYTHEMIA_VERA RESPONSE — published composite OR 28.6 (Vannucchi 2015)
    ("POLYCYTHEMIA_VERA_NMA_REVIEW.html", "RESPONSE",
     "publishedHR: 21.4, hrLCI: 3.0, hrUCI: 152.9",
     "publishedHR: 28.6, hrLCI: 4.5, hrUCI: 1206.0"),

    # RCC_1L CheckMate-214 — published OS HR 0.63 intermediate/poor (Motzer 2018)
    ("RCC_1L_NMA_REVIEW.html", "CheckMate-214",
     "publishedHR: 0.82, hrLCI: 0.64, hrUCI: 1.05",
     "publishedHR: 0.63, hrLCI: 0.44, hrUCI: 0.89"),

    # UC_BIOLOGICS ACT-1 — published 8w response RR 1.86 (Rutgeerts 2005)
    ("UC_BIOLOGICS_NMA_REVIEW.html", "ACT-1",
     "publishedHR: 3.7, hrLCI: 2.05, hrUCI: 6.68",
     "publishedHR: 1.86, hrLCI: 1.43, hrUCI: 2.41"),
]


def main():
    fixed = 0
    failed = []
    for fname, trial, old, new in FIXES:
        path = REPO / fname
        if not path.exists():
            failed.append((fname, trial, "FILE_NOT_FOUND"))
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        if old not in text:
            failed.append((fname, trial, "OLD_NOT_FOUND"))
            continue
        if text.count(old) > 1:
            failed.append((fname, trial, f"OLD_NOT_UNIQUE ({text.count(old)} occurrences)"))
            continue
        text = text.replace(old, new)
        path.write_text(text, encoding="utf-8")
        fixed += 1
        print(f"  FIX: {fname}::{trial}")

    print(f"\n=== Auto-fix summary ===")
    print(f"  Fixed: {fixed}/{len(FIXES)}")
    print(f"  Failed: {len(failed)}")
    for fname, trial, reason in failed:
        print(f"    {fname}::{trial} — {reason}")


if __name__ == "__main__":
    main()
