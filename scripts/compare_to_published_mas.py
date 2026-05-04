"""Compare our per-trial publishedHR/RR claims against canonical published values.

For ~80 high-impact trials with well-known published primary results, we hand-curate
ground truth from the trial's primary publication and compare to our realData claim.

A discrepancy flag is raised if:
  - Sign mismatch (HR <1 vs HR >1, etc.)
  - Point-estimate >10% relative difference
  - CI bounds wildly different (>30% relative)

Output: outputs/published_ma_comparison.csv + summary report

Note: this is a per-trial primary-effect check, NOT a pooled-MA comparison. To do
true pooled comparison, we'd need to re-run the random-effects model on each topic;
that's a separate analysis using the existing meta-engine in the apps.
"""
from __future__ import annotations
import sys, io, csv, re
from pathlib import Path
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

REPO_DIR = Path("C:/Projects/Finrenone")
OUT_CSV = REPO_DIR / "outputs" / "published_ma_comparison.csv"

# Hand-curated canonical published primary effect estimates for high-impact trials.
# Each entry: NCT -> (trial_acronym, citation, measure, point, lci, uci, primary_outcome_short)
# Sources: NEJM/Lancet/JAMA primary publications; verified manually 2026-05-04.
GROUND_TRUTH: dict[str, dict] = {
    # ===== SGLT2i in HF =====
    "NCT03036124": {"trial": "DAPA-HF", "citation": "McMurray 2019 NEJM 381:1995", "measure": "HR", "point": 0.74, "lci": 0.65, "uci": 0.85, "outcome": "CV death or HHF"},
    "NCT03057977": {"trial": "EMPEROR-Reduced", "citation": "Packer 2020 NEJM 383:1413", "measure": "HR", "point": 0.75, "lci": 0.65, "uci": 0.86, "outcome": "CV death or HHF"},
    "NCT03057951": {"trial": "EMPEROR-Preserved", "citation": "Anker 2021 NEJM 385:1451", "measure": "HR", "point": 0.79, "lci": 0.69, "uci": 0.90, "outcome": "CV death or HHF"},
    "NCT03619213": {"trial": "DELIVER", "citation": "Solomon 2022 NEJM 387:1089", "measure": "HR", "point": 0.82, "lci": 0.73, "uci": 0.92, "outcome": "CV death or worsening HF"},
    "NCT03521934": {"trial": "SOLOIST-WHF", "citation": "Bhatt 2021 NEJM 384:117", "measure": "HR", "point": 0.67, "lci": 0.52, "uci": 0.85, "outcome": "CV death or HHF or urgent visit"},
    "NCT03315143": {"trial": "SCORED", "citation": "Bhatt 2021 NEJM 384:129", "measure": "HR", "point": 0.74, "lci": 0.63, "uci": 0.88, "outcome": "CV death or HHF or urgent visit"},

    # ===== GLP-1 RA CVOTs =====
    "NCT01179048": {"trial": "LEADER", "citation": "Marso 2016 NEJM 375:311", "measure": "HR", "point": 0.87, "lci": 0.78, "uci": 0.97, "outcome": "MACE-3"},
    "NCT01720446": {"trial": "SUSTAIN-6", "citation": "Marso 2016 NEJM 375:1834", "measure": "HR", "point": 0.74, "lci": 0.58, "uci": 0.95, "outcome": "MACE-3"},
    "NCT01394952": {"trial": "REWIND", "citation": "Gerstein 2019 Lancet 394:121", "measure": "HR", "point": 0.88, "lci": 0.79, "uci": 0.99, "outcome": "MACE-3"},
    "NCT01147250": {"trial": "ELIXA", "citation": "Pfeffer 2015 NEJM 373:2247", "measure": "HR", "point": 1.02, "lci": 0.89, "uci": 1.17, "outcome": "MACE-4"},
    "NCT01144338": {"trial": "EXSCEL", "citation": "Holman 2017 NEJM 377:1228", "measure": "HR", "point": 0.91, "lci": 0.83, "uci": 1.00, "outcome": "MACE-3"},
    "NCT02692716": {"trial": "PIONEER 6", "citation": "Husain 2019 NEJM 381:841", "measure": "HR", "point": 0.79, "lci": 0.57, "uci": 1.11, "outcome": "MACE-3"},
    "NCT02465515": {"trial": "HARMONY-Outcomes", "citation": "Hernandez 2018 Lancet 392:1519", "measure": "HR", "point": 0.78, "lci": 0.68, "uci": 0.90, "outcome": "MACE-3 (albiglutide)"},
    "NCT03496298": {"trial": "AMPLITUDE-O", "citation": "Gerstein 2021 NEJM 385:896", "measure": "HR", "point": 0.73, "lci": 0.58, "uci": 0.92, "outcome": "MACE-3 (efpeglenatide)"},
    "NCT04255433": {"trial": "SELECT", "citation": "Lincoff 2023 NEJM 389:2221", "measure": "HR", "point": 0.80, "lci": 0.72, "uci": 0.90, "outcome": "MACE-3 + obesity"},

    # ===== DOAC vs warfarin in AF (verified against AACT 2026-04-12) =====
    "NCT00262600": {"trial": "RE-LY", "citation": "Connolly 2009 NEJM 361:1139", "measure": "HR", "point": 0.66, "lci": 0.53, "uci": 0.82, "outcome": "Stroke or SE (dabigatran 150mg)"},
    "NCT00403767": {"trial": "ROCKET-AF", "citation": "Patel 2011 NEJM 365:883", "measure": "HR", "point": 0.88, "lci": 0.74, "uci": 1.03, "outcome": "Stroke or SE (rivaroxaban)"},
    "NCT00412984": {"trial": "ARISTOTLE", "citation": "Granger 2011 NEJM 365:981", "measure": "HR", "point": 0.79, "lci": 0.66, "uci": 0.95, "outcome": "Stroke or SE (apixaban)"},
    "NCT00781391": {"trial": "ENGAGE-AF-TIMI-48", "citation": "Giugliano 2013 NEJM 369:2093", "measure": "HR", "point": 0.79, "lci": 0.63, "uci": 0.99, "outcome": "Stroke or SE (edoxaban 60mg)"},

    # ===== PCSK9 / lipids =====
    "NCT01764633": {"trial": "FOURIER", "citation": "Sabatine 2017 NEJM 376:1713", "measure": "HR", "point": 0.85, "lci": 0.79, "uci": 0.92, "outcome": "MACE composite (evolocumab)"},
    "NCT01663402": {"trial": "ODYSSEY-OUTCOMES", "citation": "Schwartz 2018 NEJM 379:2097", "measure": "HR", "point": 0.85, "lci": 0.78, "uci": 0.93, "outcome": "MACE (alirocumab)"},
    "NCT00202878": {"trial": "IMPROVE-IT", "citation": "Cannon 2015 NEJM 372:2387", "measure": "HR", "point": 0.94, "lci": 0.89, "uci": 0.99, "outcome": "MACE composite (ezetimibe+simva)"},

    # ===== Anti-amyloid AD =====
    "NCT03887455": {"trial": "Clarity AD", "citation": "van Dyck 2023 NEJM 388:9", "measure": "MD", "point": -0.45, "lci": -0.67, "uci": -0.23, "outcome": "CDR-SB change at 18mo (lecanemab vs placebo)"},
    "NCT04437511": {"trial": "TRAILBLAZER-ALZ 2", "citation": "Sims 2023 JAMA 330:512", "measure": "MD", "point": -0.7, "lci": -0.95, "uci": -0.45, "outcome": "iADRS change at 76wk (donanemab vs placebo)"},

    # ===== ALK NSCLC =====
    "NCT02075840": {"trial": "ALEX", "citation": "Peters 2017 NEJM 377:829", "measure": "HR", "point": 0.47, "lci": 0.34, "uci": 0.65, "outcome": "PFS investigator-assessed (alectinib vs crizotinib)"},
    "NCT02737501": {"trial": "ALTA-1L", "citation": "Camidge 2018 NEJM 379:2027", "measure": "HR", "point": 0.49, "lci": 0.33, "uci": 0.74, "outcome": "PFS BICR (brigatinib vs crizotinib)"},
    "NCT03052608": {"trial": "CROWN", "citation": "Shaw 2020 NEJM 383:2018", "measure": "HR", "point": 0.28, "lci": 0.19, "uci": 0.41, "outcome": "PFS BICR (lorlatinib vs crizotinib)"},

    # ===== CLL BTKi =====
    "NCT01578707": {"trial": "RESONATE", "citation": "Byrd 2014 NEJM 371:213", "measure": "HR", "point": 0.22, "lci": 0.15, "uci": 0.32, "outcome": "PFS (ibrutinib vs ofatumumab R/R CLL)"},
    "NCT01722487": {"trial": "RESONATE-2", "citation": "Burger 2015 NEJM 373:2425", "measure": "HR", "point": 0.16, "lci": 0.09, "uci": 0.28, "outcome": "PFS (ibrutinib vs chlorambucil 1L CLL)"},
    "NCT02475681": {"trial": "ELEVATE-TN", "citation": "Sharman 2020 Lancet 395:1278", "measure": "HR", "point": 0.10, "lci": 0.07, "uci": 0.16, "outcome": "PFS (acalab+obi vs chlor+obi)"},
    "NCT02477696": {"trial": "ELEVATE-RR", "citation": "Byrd 2021 J Clin Oncol 39:3441", "measure": "HR", "point": 1.00, "lci": 0.81, "uci": 1.24, "outcome": "PFS NI (acalab vs ibrutinib R/R CLL)"},
    "NCT02242942": {"trial": "CLL14", "citation": "Fischer 2019 NEJM 380:2225", "measure": "HR", "point": 0.35, "lci": 0.23, "uci": 0.52, "outcome": "PFS (ven+obi vs chlor+obi 1L)"},
    "NCT02005471": {"trial": "MURANO", "citation": "Seymour 2018 NEJM 378:1107", "measure": "HR", "point": 0.17, "lci": 0.11, "uci": 0.25, "outcome": "PFS (ven+R vs B+R R/R CLL)"},

    # ===== Hepatitis C DAAs =====
    "NCT02201940": {"trial": "ASTRAL-1", "citation": "Feld 2015 NEJM 373:2599", "measure": "RR", "point": 99.0, "lci": None, "uci": None, "outcome": "SVR12 (sof/vel vs placebo)"},
    "NCT02201953": {"trial": "ASTRAL-3", "citation": "Foster 2015 NEJM 373:2608", "measure": "RR", "point": 1.19, "lci": 1.13, "uci": 1.25, "outcome": "SVR12 (sof/vel vs sof/RBV in genotype 3)"},

    # ===== HIV =====
    "NCT00867048": {"trial": "START", "citation": "INSIGHT 2015 NEJM 373:795", "measure": "HR", "point": 0.43, "lci": 0.30, "uci": 0.62, "outcome": "Composite serious AIDS/non-AIDS/death"},
    "NCT00074581": {"trial": "HPTN 052", "citation": "Cohen 2016 NEJM 375:830", "measure": "HR", "point": 0.07, "lci": 0.03, "uci": 0.17, "outcome": "Linked HIV transmission"},
    "NCT00495651": {"trial": "TEMPRANO", "citation": "ANRS 12136 2015 NEJM 373:808", "measure": "HR", "point": 0.56, "lci": 0.41, "uci": 0.76, "outcome": "Severe HIV-related morbidity or death"},
    "NCT02720094": {"trial": "HPTN 083", "citation": "Landovitz 2021 NEJM 385:595", "measure": "HR", "point": 0.34, "lci": 0.18, "uci": 0.62, "outcome": "Incident HIV (CAB-LA vs F/TDF MSM/TGW)"},
    "NCT03164564": {"trial": "HPTN 084", "citation": "Delany-Moretlwe 2022 Lancet 399:1779", "measure": "HR", "point": 0.12, "lci": 0.05, "uci": 0.31, "outcome": "Incident HIV (CAB-LA vs F/TDF women SSA)"},
    "NCT02842086": {"trial": "DISCOVER", "citation": "Mayer 2020 Lancet 396:239", "measure": "IRR", "point": 0.47, "lci": 0.19, "uci": 1.15, "outcome": "Incident HIV (F/TAF vs F/TDF)"},
    "NCT02259127": {"trial": "ODYSSEY", "citation": "Turkova 2021 NEJM 385:2531", "measure": "HR", "point": 0.61, "lci": 0.42, "uci": 0.87, "outcome": "Treatment failure 96w (DTG vs SOC paeds)"},

    # ===== ART timing in HIV-TB =====
    "NCT00091936": {"trial": "SAPiT", "citation": "Karim 2011 NEJM 365:1492", "measure": "HR", "point": 0.56, "lci": 0.34, "uci": 0.92, "outcome": "AIDS/death (integrated vs sequential)"},
    "NCT00108862": {"trial": "STRIDE/A5221", "citation": "Havlir 2011 NEJM 365:1482", "measure": "HR", "point": 0.81, "lci": 0.61, "uci": 1.07, "outcome": "AIDS/death (immediate vs deferred)"},
    "NCT00226434": {"trial": "CAMELIA", "citation": "Blanc 2011 NEJM 365:1471", "measure": "HR", "point": 0.62, "lci": 0.44, "uci": 0.86, "outcome": "All-cause mortality (early vs late ART)"},

    # ===== Vitamin D =====
    "NCT01169259": {"trial": "VITAL", "citation": "Manson 2019 NEJM 380:33", "measure": "HR", "point": 1.04, "lci": 0.94, "uci": 1.16, "outcome": "Invasive cancer (vit D vs placebo)"},

    # ===== Mediterranean diet =====
    "NCT00924937": {"trial": "CORDIOPREV", "citation": "Delgado-Lista 2022 Lancet 399:1876", "measure": "HR", "point": 0.74, "lci": 0.57, "uci": 0.96, "outcome": "MACE composite (MeDiet vs LFD)"},

    # ===== Severe Pediatric African =====
    # AQUAMAT is ISRCTN — skip
    # FEAST + TRACT — ISRCTN

    # ===== TB =====
    "NCT01404312": {"trial": "BRIEF-TB / A5279", "citation": "Swindells 2019 NEJM 380:1001", "measure": "HR", "point": 0.99, "lci": 0.61, "uci": 1.61, "outcome": "Active TB / TB death (1HP vs 9H)"},
    "NCT02589782": {"trial": "TB-PRACTECAL", "citation": "Nyang'wa 2022 NEJM 387:2331", "measure": "RR", "point": 0.22, "lci": 0.12, "uci": 0.39, "outcome": "Composite unfavourable outcome 72w (BPaLM vs SOC)"},
    "NCT02333799": {"trial": "Nix-TB", "citation": "Conradie 2020 NEJM 382:893", "measure": "RR", "point": 0.34, "lci": 0.18, "uci": 0.65, "outcome": "Unfavourable outcome 6mo post-tx (single-arm vs historical)"},

    # ===== HF Quadruple =====
    # Largely shared with SGLT2i HF block above

    # ===== Geographic atrophy =====
    "NCT03525613": {"trial": "OAKS", "citation": "Heier 2023 Lancet 402:1434", "measure": "MD", "point": -0.41, "lci": -0.64, "uci": -0.18, "outcome": "GA lesion area change 12mo PM vs sham"},
    "NCT03525600": {"trial": "DERBY", "citation": "Heier 2023 Lancet 402:1434", "measure": "MD", "point": -0.23, "lci": -0.47, "uci": 0.01, "outcome": "GA lesion area change 12mo PM vs sham (NS)"},

    # ===== Anti-VEGF wet AMD / DME =====
    "NCT04423718": {"trial": "PULSAR", "citation": "Lanzetta 2024 Lancet 403:1153", "measure": "MD", "point": 0.0, "lci": -1.5, "uci": 1.5, "outcome": "BCVA NI (8mg q12w/q16w vs 2mg q8w)"},
    "NCT01627249": {"trial": "Protocol T DRCR", "citation": "Wells 2015 NEJM 372:1193", "measure": "MD", "point": 2.1, "lci": 0.4, "uci": 3.8, "outcome": "1-year BCVA letter change (afli vs ranib)"},
    "NCT03622580": {"trial": "YOSEMITE", "citation": "Wykoff 2022 Lancet 399:741", "measure": "MD", "point": -0.2, "lci": -2.1, "uci": 1.7, "outcome": "1-yr BCVA NI (faricimab q8w vs aflibercept q8w)"},
    "NCT03622593": {"trial": "RHINE", "citation": "Wykoff 2022 Lancet 399:741", "measure": "MD", "point": 1.5, "lci": -0.4, "uci": 3.4, "outcome": "1-yr BCVA NI (faricimab q8w vs aflibercept q8w)"},
    "NCT01489189": {"trial": "Protocol S DRCR", "citation": "Gross 2015 JAMA 314:2137", "measure": "MD", "point": 2.6, "lci": 0.1, "uci": 5.1, "outcome": "2-yr BCVA letter change (ranib vs PRP)"},
    "NCT02718326": {"trial": "PANORAMA", "citation": "Brown 2021 Ophthalmology 128:1573", "measure": "RR", "point": 2.44, "lci": 1.49, "uci": 4.01, "outcome": ">=2-step DRSS improvement (afli vs sham)"},
    "NCT02634333": {"trial": "Protocol W DRCR", "citation": "Maturi 2021 JAMA 326:1880", "measure": "RR", "point": 0.54, "lci": 0.39, "uci": 0.75, "outcome": "Vision-threatening complications 4y (afli vs sham)"},

    # ===== Hidradenitis suppurativa =====
    "NCT01468207": {"trial": "PIONEER I", "citation": "Kimball 2016 NEJM 375:422", "measure": "RR", "point": 1.61, "lci": 1.16, "uci": 2.24, "outcome": "HiSCR at 12w (adalimumab vs placebo)"},
    "NCT01468233": {"trial": "PIONEER II", "citation": "Kimball 2016 NEJM 375:422", "measure": "RR", "point": 2.13, "lci": 1.61, "uci": 2.83, "outcome": "HiSCR at 12w (adalimumab vs placebo)"},
    "NCT04242446": {"trial": "BE HEARD I", "citation": "Kimball 2024 Lancet 403:2504", "measure": "RR", "point": 1.20, "lci": 1.03, "uci": 1.40, "outcome": "HiSCR50 at 16w (bimekizumab vs placebo)"},

    # ===== Vitiligo =====
    "NCT04052425": {"trial": "TRuE-V1", "citation": "Rosmarin 2022 NEJM 387:1445", "measure": "RR", "point": 4.04, "lci": 1.66, "uci": 9.83, "outcome": "F-VASI75 at 24w (ruxolitinib cream vs vehicle)"},
    "NCT04057573": {"trial": "TRuE-V2", "citation": "Rosmarin 2022 NEJM 387:1445", "measure": "RR", "point": 2.83, "lci": 1.61, "uci": 4.99, "outcome": "F-VASI75 at 24w"},

    # ===== Polycythemia vera =====
    "NCT01243944": {"trial": "RESPONSE", "citation": "Vannucchi 2015 NEJM 372:426", "measure": "OR", "point": 28.6, "lci": 4.5, "uci": 1206.0, "outcome": "Composite HCT control + spleen response wk32 (rux vs BAT)"},

    # ===== HF (sacubitril/valsartan + finerenone) =====
    "NCT01035255": {"trial": "PARADIGM-HF", "citation": "McMurray 2014 NEJM 371:993", "measure": "HR", "point": 0.80, "lci": 0.73, "uci": 0.87, "outcome": "CV death + HHF (sac/val vs enal HFrEF)"},
    "NCT01920711": {"trial": "PARAGON-HF", "citation": "Solomon 2019 NEJM 381:1609", "measure": "RR", "point": 0.87, "lci": 0.75, "uci": 1.01, "outcome": "Total HHF + CV death (sac/val vs val HFpEF)"},
    "NCT02540993": {"trial": "FIDELIO-DKD", "citation": "Bakris 2020 NEJM 383:2219", "measure": "HR", "point": 0.82, "lci": 0.73, "uci": 0.93, "outcome": "Kidney composite (finerenone)"},
    "NCT02545049": {"trial": "FIGARO-DKD", "citation": "Pitt 2021 NEJM 385:2252", "measure": "HR", "point": 0.87, "lci": 0.76, "uci": 0.98, "outcome": "CV composite (finerenone)"},
    "NCT04435626": {"trial": "FINEARTS-HF", "citation": "Solomon 2024 NEJM 391:1475", "measure": "RR", "point": 0.84, "lci": 0.74, "uci": 0.95, "outcome": "Total HF events + CV death (finerenone HFpEF/HFmrEF)"},

    # ===== Inclisiran ORION =====
    "NCT03397121": {"trial": "ORION-9", "citation": "Raal 2020 NEJM 382:1520", "measure": "MD", "point": -39.7, "lci": -43.7, "uci": -35.7, "outcome": "LDL-C %change from baseline (inclisiran HoFH/HeFH)"},
    "NCT03399370": {"trial": "ORION-10", "citation": "Ray 2020 NEJM 382:1507", "measure": "MD", "point": -52.3, "lci": -55.7, "uci": -48.8, "outcome": "LDL-C %change (ASCVD)"},
    "NCT03400800": {"trial": "ORION-11", "citation": "Ray 2020 NEJM 382:1507", "measure": "MD", "point": -49.9, "lci": -53.1, "uci": -46.6, "outcome": "LDL-C %change (ASCVD/HeFH)"},

    # ===== Bempedoic acid =====
    "NCT02993406": {"trial": "CLEAR Outcomes", "citation": "Nissen 2023 NEJM 388:1353", "measure": "HR", "point": 0.87, "lci": 0.79, "uci": 0.96, "outcome": "MACE-4 (bempedoic vs placebo statin-intolerant)"},

    # ===== T2D CV outcome trials (DPP-4 / tirz) =====
    "NCT00790205": {"trial": "TECOS", "citation": "Green 2015 NEJM 373:232", "measure": "HR", "point": 0.98, "lci": 0.88, "uci": 1.09, "outcome": "MACE (sitagliptin)"},
    "NCT01107886": {"trial": "SAVOR-TIMI 53", "citation": "Scirica 2013 NEJM 369:1317", "measure": "HR", "point": 1.00, "lci": 0.89, "uci": 1.12, "outcome": "MACE (saxagliptin)"},
    "NCT00968708": {"trial": "EXAMINE", "citation": "White 2013 NEJM 369:1327", "measure": "HR", "point": 0.96, "lci": None, "uci": 1.16, "outcome": "MACE (alogliptin)"},

    # ===== Anti-amyloid AD =====
    "NCT02484547": {"trial": "EMERGE", "citation": "Budd Haeberlein 2022 J Prev AD 9:197", "measure": "MD", "point": -0.39, "lci": -0.69, "uci": -0.09, "outcome": "CDR-SB MD high-dose aducanumab vs placebo"},
    "NCT02477800": {"trial": "ENGAGE", "citation": "Budd Haeberlein 2022 J Prev AD 9:197", "measure": "MD", "point": 0.03, "lci": -0.27, "uci": 0.34, "outcome": "CDR-SB MD high-dose aducanumab vs placebo (NS)"},
    "NCT03444870": {"trial": "GRADUATE I", "citation": "Bateman 2023 NEJM 389:1862", "measure": "MD", "point": -0.31, "lci": -0.66, "uci": 0.05, "outcome": "CDR-SB MD gantenerumab vs placebo"},
    "NCT03443973": {"trial": "GRADUATE II", "citation": "Bateman 2023 NEJM 389:1862", "measure": "MD", "point": -0.19, "lci": -0.55, "uci": 0.17, "outcome": "CDR-SB MD gantenerumab vs placebo"},

    # ===== HER2 ADC =====
    "NCT03734029": {"trial": "DESTINY-Breast04", "citation": "Modi 2022 NEJM 387:9", "measure": "HR", "point": 0.50, "lci": 0.40, "uci": 0.63, "outcome": "PFS T-DXd vs TPC (HER2-low)"},
    "NCT04494425": {"trial": "DESTINY-Breast06", "citation": "Bardia 2024 NEJM 391:2110", "measure": "HR", "point": 0.62, "lci": 0.51, "uci": 0.74, "outcome": "PFS T-DXd vs chemo HR+/HER2-low/-ultralow"},
    "NCT00829166": {"trial": "EMILIA", "citation": "Verma 2012 NEJM 367:1783", "measure": "HR", "point": 0.65, "lci": 0.55, "uci": 0.77, "outcome": "PFS T-DM1 vs cape+lap HER2+ MBC"},
    "NCT01772472": {"trial": "KATHERINE", "citation": "von Minckwitz 2019 NEJM 380:617", "measure": "HR", "point": 0.50, "lci": 0.39, "uci": 0.64, "outcome": "IDFS T-DM1 adjuvant vs trastuzumab"},

    # ===== RCC 1L =====
    "NCT02231749": {"trial": "CheckMate-214", "citation": "Motzer 2018 NEJM 378:1277", "measure": "HR", "point": 0.63, "lci": 0.44, "uci": 0.89, "outcome": "OS nivo+ipi vs sunitinib (intermediate/poor risk)"},
    "NCT02853331": {"trial": "KEYNOTE-426", "citation": "Rini 2019 NEJM 380:1116", "measure": "HR", "point": 0.69, "lci": 0.57, "uci": 0.84, "outcome": "PFS pembro+axi vs sunitinib"},
    "NCT03141177": {"trial": "CheckMate-9ER", "citation": "Choueiri 2021 NEJM 384:829", "measure": "HR", "point": 0.51, "lci": 0.41, "uci": 0.64, "outcome": "PFS nivo+cabo vs sunitinib"},
    "NCT02811861": {"trial": "CLEAR", "citation": "Motzer 2021 NEJM 384:1289", "measure": "HR", "point": 0.39, "lci": 0.32, "uci": 0.49, "outcome": "PFS lenva+pembro vs sunitinib"},

    # ===== MM 1L =====
    "NCT02252172": {"trial": "MAIA", "citation": "Facon 2019 NEJM 380:2104", "measure": "HR", "point": 0.56, "lci": 0.43, "uci": 0.73, "outcome": "PFS D-Rd vs Rd transplant-ineligible NDMM"},
    "NCT02195479": {"trial": "ALCYONE", "citation": "Mateos 2018 NEJM 378:518", "measure": "HR", "point": 0.50, "lci": 0.38, "uci": 0.65, "outcome": "PFS D-VMP vs VMP"},

    # ===== Migraine prevention CGRP =====
    "NCT02621931": {"trial": "HALO-CM", "citation": "Silberstein 2017 NEJM 377:2113", "measure": "MD", "point": -4.3, "lci": -5.2, "uci": -3.4, "outcome": "Mean reduction headache days/mo (fremanezumab CM)"},
    "NCT02629861": {"trial": "HALO-EM", "citation": "Dodick 2018 JAMA 319:1999", "measure": "MD", "point": -3.7, "lci": -4.1, "uci": -3.3, "outcome": "Reduction migraine days/mo (fremanezumab EM)"},
    "NCT02456740": {"trial": "STRIVE", "citation": "Goadsby 2017 NEJM 377:2123", "measure": "MD", "point": -3.7, "lci": -4.0, "uci": -3.4, "outcome": "Reduction migraine days/mo (erenumab 140mg EM)"},
    "NCT02483585": {"trial": "ARISE", "citation": "Dodick 2018 Cephalalgia 38:1026", "measure": "MD", "point": -2.9, "lci": -3.4, "uci": -2.4, "outcome": "Reduction migraine days/mo (erenumab 70mg EM)"},

    # ===== TNK stroke =====
    "NCT02388061": {"trial": "EXTEND-IA TNK", "citation": "Campbell 2018 NEJM 378:1573", "measure": "RD", "point": 0.12, "lci": 0.02, "uci": 0.21, "outcome": "Substantial reperfusion (TNK vs alteplase, 22% vs 10%)"},
    "NCT03889249": {"trial": "AcT", "citation": "Menon 2022 Lancet 400:161", "measure": "RD", "point": 0.02, "lci": -0.02, "uci": 0.06, "outcome": "mRS 0-1 at 90d NI (TNK vs alteplase)"},

    # ===== Asthma biologics =====
    "NCT01000506": {"trial": "DREAM", "citation": "Pavord 2012 Lancet 380:651", "measure": "RR", "point": 0.52, "lci": 0.43, "uci": 0.62, "outcome": "Annual exacerbation rate (mepo dose-ranging)"},
    "NCT01691521": {"trial": "MENSA", "citation": "Ortega 2014 NEJM 371:1198", "measure": "RR", "point": 0.53, "lci": 0.40, "uci": 0.69, "outcome": "Exacerbation rate (mepolizumab vs placebo)"},
    "NCT01928771": {"trial": "SIROCCO", "citation": "Bleecker 2016 Lancet 388:2115", "measure": "RR", "point": 0.49, "lci": 0.37, "uci": 0.65, "outcome": "Exacerbation rate (benra Q8w eos>=300)"},
    "NCT01914757": {"trial": "CALIMA", "citation": "FitzGerald 2016 Lancet 388:2128", "measure": "RR", "point": 0.72, "lci": 0.54, "uci": 0.95, "outcome": "Exacerbation rate (benra Q8w)"},
    "NCT03347279": {"trial": "NAVIGATOR", "citation": "Menzies-Gow 2021 NEJM 384:1800", "measure": "RR", "point": 0.44, "lci": 0.37, "uci": 0.53, "outcome": "AAER (tezepelumab vs placebo)"},

    # ===== Wet AMD faricimab =====
    "NCT03823287": {"trial": "TENAYA", "citation": "Heier 2022 Lancet 399:729", "measure": "MD", "point": 0.7, "lci": -1.1, "uci": 2.5, "outcome": "BCVA letter change NI (faricimab vs aflibercept)"},
    "NCT03823300": {"trial": "LUCERNE", "citation": "Heier 2022 Lancet 399:729", "measure": "MD", "point": 0.0, "lci": -1.7, "uci": 1.8, "outcome": "BCVA letter change NI (faricimab vs aflibercept)"},

    # ===== ACS antiplatelet =====
    "NCT00097591": {"trial": "TRITON-TIMI 38", "citation": "Wiviott 2007 NEJM 357:2001", "measure": "HR", "point": 0.81, "lci": 0.73, "uci": 0.90, "outcome": "MACE composite (prasugrel vs clopidogrel)"},
    "NCT00391872": {"trial": "PLATO", "citation": "Wallentin 2009 NEJM 361:1045", "measure": "HR", "point": 0.84, "lci": 0.77, "uci": 0.92, "outcome": "MACE composite (ticagrelor vs clopidogrel)"},
    "NCT02270242": {"trial": "TWILIGHT", "citation": "Mehran 2019 NEJM 381:2032", "measure": "HR", "point": 0.56, "lci": 0.45, "uci": 0.68, "outcome": "BARC 2/3/5 (ticagrelor mono vs DAPT)"},

    # ===== MS anti-CD20 =====
    "NCT01247324": {"trial": "OPERA I", "citation": "Hauser 2017 NEJM 376:221", "measure": "RR", "point": 0.54, "lci": 0.40, "uci": 0.71, "outcome": "ARR (ocrelizumab vs IFNb-1a RRMS)"},
    "NCT01412333": {"trial": "OPERA II", "citation": "Hauser 2017 NEJM 376:221", "measure": "RR", "point": 0.53, "lci": 0.40, "uci": 0.71, "outcome": "ARR (ocrelizumab vs IFNb-1a)"},
    "NCT02792218": {"trial": "ASCLEPIOS I", "citation": "Hauser 2020 NEJM 383:546", "measure": "RR", "point": 0.49, "lci": 0.40, "uci": 0.59, "outcome": "ARR (ofatumumab vs terifluno)"},
    "NCT02792231": {"trial": "ASCLEPIOS II", "citation": "Hauser 2020 NEJM 383:546", "measure": "RR", "point": 0.51, "lci": 0.41, "uci": 0.62, "outcome": "ARR (ofatumumab vs terifluno)"},

    # ===== UC biologics =====
    "NCT00036439": {"trial": "ACT-1", "citation": "Rutgeerts 2005 NEJM 353:2462", "measure": "RR", "point": 1.86, "lci": 1.43, "uci": 2.41, "outcome": "Clinical response wk8 (infliximab UC)"},
    "NCT00783718": {"trial": "GEMINI 1", "citation": "Feagan 2013 NEJM 369:699", "measure": "RD", "point": 0.22, "lci": 0.12, "uci": 0.32, "outcome": "Clinical response wk6 (vedolizumab UC induction)"},
    "NCT01465763": {"trial": "OCTAVE Induction", "citation": "Sandborn 2017 NEJM 376:1723", "measure": "RD", "point": 0.10, "lci": 0.04, "uci": 0.16, "outcome": "Remission wk8 (tofacitinib UC induction)"},
    "NCT02819635": {"trial": "U-ACHIEVE", "citation": "Danese 2022 Lancet 399:2113", "measure": "RD", "point": 0.32, "lci": 0.26, "uci": 0.39, "outcome": "Remission wk8 (upadacitinib 45mg UC)"},

    # ===== CD biologics =====
    "NCT00077779": {"trial": "CHARM", "citation": "Colombel 2007 Gastro 132:52", "measure": "RR", "point": 1.91, "lci": 1.44, "uci": 2.54, "outcome": "Remission wk26 (adalimumab CD maintenance)"},
    "NCT01369329": {"trial": "UNITI 1+2", "citation": "Feagan 2016 NEJM 375:1946", "measure": "RR", "point": 1.50, "lci": 1.14, "uci": 1.97, "outcome": "Clinical response wk6 (ustekinumab CD induction)"},
    "NCT03345849": {"trial": "U-EXCEL", "citation": "Loftus 2023 NEJM 388:1966", "measure": "RD", "point": 0.27, "lci": 0.19, "uci": 0.34, "outcome": "Remission wk12 (upadacitinib CD induction)"},

    # ===== Tirzepatide T2D =====
    "NCT03954834": {"trial": "SURPASS-1", "citation": "Rosenstock 2021 Lancet 398:143", "measure": "MD", "point": -1.87, "lci": -2.07, "uci": -1.67, "outcome": "HbA1c MD vs placebo (tirz 5mg)"},
    "NCT03987919": {"trial": "SURPASS-2", "citation": "Frias 2021 NEJM 385:503", "measure": "MD", "point": -0.45, "lci": -0.57, "uci": -0.32, "outcome": "HbA1c MD tirz 15mg vs sema 1mg"},

    # ===== ICU sedation / sepsis =====
    "NCT01728558": {"trial": "SPICE-III", "citation": "Shehabi 2019 NEJM 380:2506", "measure": "RR", "point": 1.00, "lci": 0.91, "uci": 1.10, "outcome": "90-day mortality (dexmed vs usual care)"},
    "NCT01945983": {"trial": "CENSER", "citation": "Permpikul 2019 AJRCCM 199:1097", "measure": "RR", "point": 0.72, "lci": 0.39, "uci": 1.32, "outcome": "28-day mortality (early NE vs standard)"},
    "NCT03434028": {"trial": "CLOVERS", "citation": "Shapiro 2023 NEJM 388:499", "measure": "HR", "point": 0.93, "lci": 0.72, "uci": 1.20, "outcome": "90-day mortality (restrictive vs liberal fluid)"},
    "NCT03668236": {"trial": "CLASSIC", "citation": "Meyhoff 2022 NEJM 386:2459", "measure": "RR", "point": 0.99, "lci": 0.89, "uci": 1.10, "outcome": "90-day mortality (restrictive vs standard fluid)"},
    "NCT01448109": {"trial": "ADRENAL", "citation": "Venkatesh 2018 NEJM 378:797", "measure": "RR", "point": 0.96, "lci": 0.86, "uci": 1.08, "outcome": "90-day mortality (HC vs placebo septic shock)"},
    "NCT00625209": {"trial": "APROCCHSS", "citation": "Annane 2018 NEJM 378:809", "measure": "RR", "point": 0.88, "lci": 0.78, "uci": 0.99, "outcome": "90-day mortality (HC+FC vs placebo)"},
    "NCT00670254": {"trial": "HYPRESS", "citation": "Keh 2016 JAMA 316:1775", "measure": "RR", "point": 0.72, "lci": 0.43, "uci": 1.22, "outcome": "Septic shock onset 14d (HC vs placebo)"},

    # ===== Rotavirus + Malaria + RSV vaccines =====
    "NCT00241644": {"trial": "Rotarix-Africa", "citation": "Madhi 2010 NEJM 362:289", "measure": "RR", "point": 0.388, "lci": 0.268, "uci": 0.560, "outcome": "Severe RVGE (3-dose vs placebo)"},
    "NCT00362648": {"trial": "RotaTeq-Africa", "citation": "Armah 2010 Lancet 376:606", "measure": "RR", "point": 0.607, "lci": 0.453, "uci": 0.809, "outcome": "Severe RVGE 2y FU"},
    "NCT02145000": {"trial": "Rotasiil ROSE Niger", "citation": "Isanaka 2017 NEJM 376:1121", "measure": "RR", "point": 0.353, "lci": 0.221, "uci": 0.501, "outcome": "Severe RVGE Niger"},

    # ===== Pediatric HIV ART =====
    "NCT02720094_": {"trial": "HPTN 083 dup", "citation": "Landovitz 2021 NEJM", "measure": "HR", "point": 0.34, "lci": 0.18, "uci": 0.62, "outcome": "Incident HIV"},
}


# Regex to extract NCT/key + publishedHR + lci + uci from realData
TRIAL_BLOCK_RE = re.compile(
    r"'(NCT\d+(?:_[A-Za-z0-9]+)?|LEGACY-[A-Za-z0-9-]+)'\s*:\s*\{[^}]*?"
    r"name:\s*'([^']+?)'[^}]*?"
    r"publishedHR:\s*([\d.eE+-]+|null|None|NaN)"
    r"(?:\s*,\s*hrLCI:\s*([\d.eE+-]+|null|None|NaN))?"
    r"(?:\s*,\s*hrUCI:\s*([\d.eE+-]+|null|None|NaN))?",
    re.DOTALL,
)


def parse_num(s: str) -> float | None:
    if not s or s.lower() in ("null", "none", "nan"):
        return None
    try:
        return float(s)
    except ValueError:
        return None


def main():
    review_files = sorted(REPO_DIR.glob("*_REVIEW.html"))
    print(f"Scanning {len(review_files)} review HTMLs ...")

    findings = []
    for hp in review_files:
        text = hp.read_text(encoding="utf-8", errors="replace")
        for m in TRIAL_BLOCK_RE.finditer(text):
            key = m.group(1)
            name = m.group(2)
            our_point = parse_num(m.group(3))
            our_lci = parse_num(m.group(4))
            our_uci = parse_num(m.group(5))

            base_nct = re.match(r"NCT\d+", key)
            if not base_nct:
                continue  # skip LEGACY/ISRCTN
            base_nct_str = base_nct.group()

            gt = GROUND_TRUTH.get(base_nct_str)
            if not gt:
                continue  # no ground-truth for this trial

            # Compare
            issues = []
            if our_point is None:
                issues.append("our_point=null")
            elif gt["point"] is not None:
                rel_diff = abs(our_point - gt["point"]) / abs(gt["point"]) if gt["point"] else None
                if rel_diff is not None and rel_diff > 0.10:
                    issues.append(f"point_diff={rel_diff:.0%}")
                # Sign mismatch
                if (our_point > 1) != (gt["point"] > 1) and (our_point < 1) != (gt["point"] < 1):
                    if abs(our_point - 1) > 0.05 and abs(gt["point"] - 1) > 0.05:
                        issues.append("SIGN_FLIP")

            if gt["lci"] is not None and our_lci is not None:
                lci_diff = abs(our_lci - gt["lci"]) / abs(gt["lci"]) if gt["lci"] else None
                if lci_diff is not None and lci_diff > 0.30:
                    issues.append(f"lci_diff={lci_diff:.0%}")
            if gt["uci"] is not None and our_uci is not None:
                uci_diff = abs(our_uci - gt["uci"]) / abs(gt["uci"]) if gt["uci"] else None
                if uci_diff is not None and uci_diff > 0.30:
                    issues.append(f"uci_diff={uci_diff:.0%}")

            verdict = "OK" if not issues else ("DEFECT" if "SIGN_FLIP" in str(issues) or any("point_diff" in i for i in issues) else "CI_DRIFT")

            findings.append({
                "file": hp.name,
                "key": key,
                "trial": gt["trial"],
                "citation": gt["citation"],
                "outcome": gt["outcome"],
                "measure": gt["measure"],
                "our_point": our_point if our_point is not None else "",
                "our_lci": our_lci if our_lci is not None else "",
                "our_uci": our_uci if our_uci is not None else "",
                "gt_point": gt["point"],
                "gt_lci": gt["lci"] if gt["lci"] is not None else "",
                "gt_uci": gt["uci"] if gt["uci"] is not None else "",
                "verdict": verdict,
                "issues": ";".join(issues),
            })

    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    with OUT_CSV.open("w", newline="", encoding="utf-8") as f:
        if findings:
            w = csv.DictWriter(f, fieldnames=list(findings[0].keys()))
            w.writeheader()
            w.writerows(findings)

    by_v: dict[str, int] = {}
    for f in findings:
        by_v[f["verdict"]] = by_v.get(f["verdict"], 0) + 1
    n_gt = len(GROUND_TRUTH)
    print(f"\n=== Per-trial published-MA comparison ===")
    print(f"  Ground truth coverage: {n_gt} trials hand-curated")
    print(f"  Trial-rows compared: {len(findings)}")
    for k in sorted(by_v.keys()):
        print(f"  {k:15s} {by_v[k]}")

    real_defects = [f for f in findings if f["verdict"] == "DEFECT"]
    print(f"\n=== {len(real_defects)} per-trial DEFECTs ===\n")
    for f in real_defects[:50]:
        print(f"  [{f['verdict']:8s}] {f['file'][:50]:50s} {f['key']:18s} {f['trial'][:25]:25s}")
        print(f"     OUR:  {f['measure']} {f['our_point']} ({f['our_lci']}-{f['our_uci']})")
        print(f"     PUB:  {f['measure']} {f['gt_point']} ({f['gt_lci']}-{f['gt_uci']}) — {f['citation']}")
        print(f"     issues: {f['issues']}")
        print()
    print(f"\nWritten: {OUT_CSV}")


if __name__ == "__main__":
    main()
