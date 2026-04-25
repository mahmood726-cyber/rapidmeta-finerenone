#!/usr/bin/env python3
# sentinel:skip-file
"""Tier 4 batch A: 5 high-value NMA expansion apps."""
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).parent))
from clone_new_apps import clone_app, trial_entry, make_outcome_map, ROOT


def trials_block(trial_specs):
    return ",\n".join(trial_specs)


SPECS = {

    # ============ HF_QUADRUPLE_NMA ============
    "HF_QUADRUPLE_NMA_REVIEW.html": {
        "source": "SGLT2I_HF_NMA_REVIEW.html",
        "title": "RapidMeta Cardiology | HF Quadruple Therapy NMA (SGLT2i / ARNI / MRA / β-blocker) v1.0",
        "nct_ids": ["NCT03036124", "NCT03057977", "NCT03619213", "NCT03057951", "NCT01035255", "NCT04435626"],
        "acronyms": {
            "NCT03036124": "DAPA-HF", "NCT03057977": "EMPEROR-Reduced",
            "NCT03619213": "DELIVER", "NCT03057951": "EMPEROR-Preserved",
            "NCT01035255": "PARADIGM-HF", "NCT04435626": "FINEARTS-HF",
        },
        "realData_body": trials_block([
            trial_entry("NCT03036124", "DAPA-HF", "31535829", 2019, 386, 2373, 502, 2371, 0.74, 0.65, 0.85,
                "HFrEF (LVEF<=40%) on GDMT, dapagliflozin 10 mg vs placebo (CV death + HF event; HR)",
                "Composite of worsening HF event or CV death (primary; dapagliflozin vs placebo, HFrEF)",
                "https://www.nejm.org/doi/full/10.1056/NEJMoa1911303",
                "https://clinicaltrials.gov/study/NCT03036124",
                "Source: McMurray JJV et al. NEJM 2019;381:1995-2008 (DAPA-HF)."),
            trial_entry("NCT03057977", "EMPEROR-Reduced", "32865377", 2020, 361, 1863, 462, 1867, 0.75, 0.65, 0.86,
                "HFrEF (LVEF<=40%) on GDMT, empagliflozin 10 mg vs placebo (CV death + HHF; HR)",
                "Composite of CV death or HHF (primary; empagliflozin vs placebo, HFrEF)",
                "https://www.nejm.org/doi/full/10.1056/NEJMoa2022190",
                "https://clinicaltrials.gov/study/NCT03057977",
                "Source: Packer M et al. NEJM 2020;383:1413-1424 (EMPEROR-Reduced)."),
            trial_entry("NCT03619213", "DELIVER", "36027562", 2022, 512, 3131, 610, 3132, 0.82, 0.73, 0.92,
                "HFmrEF/HFpEF (LVEF>40%), dapagliflozin 10 mg vs placebo (CV death + worsening HF; HR)",
                "Composite of CV death or worsening HF event (primary; dapagliflozin vs placebo, HFmrEF/HFpEF)",
                "https://www.nejm.org/doi/full/10.1056/NEJMoa2206286",
                "https://clinicaltrials.gov/study/NCT03619213",
                "Source: Solomon SD et al. NEJM 2022;387:1089-1098 (DELIVER)."),
            trial_entry("NCT03057951", "EMPEROR-Preserved", "34449189", 2021, 415, 2997, 511, 2991, 0.79, 0.69, 0.90,
                "HFpEF (LVEF>40%), empagliflozin 10 mg vs placebo (CV death + HHF; HR)",
                "Composite of CV death or HHF (primary; empagliflozin vs placebo, HFpEF)",
                "https://www.nejm.org/doi/full/10.1056/NEJMoa2107038",
                "https://clinicaltrials.gov/study/NCT03057951",
                "Source: Anker SD et al. NEJM 2021;385:1451-1461 (EMPEROR-Preserved)."),
            trial_entry("NCT01035255", "PARADIGM-HF", "25176015", 2014, 914, 4187, 1117, 4212, 0.80, 0.73, 0.87,
                "HFrEF, sacubitril/valsartan 200 mg BID vs enalapril 10 mg BID (CV death + HHF; HR)",
                "Composite of CV death or HHF (primary; sacubitril/valsartan vs enalapril, HFrEF)",
                "https://www.nejm.org/doi/full/10.1056/NEJMoa1409077",
                "https://clinicaltrials.gov/study/NCT01035255",
                "Source: McMurray JJV et al. NEJM 2014;371:993-1004 (PARADIGM-HF)."),
            trial_entry("NCT04435626", "FINEARTS-HF", "39213592", 2024, 624, 3003, 719, 3001, 0.84, 0.74, 0.95,
                "HFmrEF/HFpEF (LVEF>=40%), finerenone 20-40 mg vs placebo (CV death + HF events; rate ratio)",
                "Total HF events + CV death (primary; finerenone vs placebo, HFmrEF/HFpEF)",
                "https://www.nejm.org/doi/full/10.1056/NEJMoa2407107",
                "https://clinicaltrials.gov/study/NCT04435626",
                "Source: Solomon SD et al. NEJM 2024;391:1475-1485 (FINEARTS-HF)."),
        ]),
        "benchmarks_body": """{
            'CV_DEATH_HHF': [
                { label: 'Vaduganathan SGLT2i HF pooled (5 trials)', citation: 'Vaduganathan 2022', year: 2022, measure: 'HR', estimate: 0.77, lci: 0.72, uci: 0.82, k: 5, n: 21947, scope: 'SGLT2i across EF spectrum; CV death or first HHF. Lancet 2022;400:757-767. (Class benchmark.)' },
                { label: 'PARADIGM-HF sacubitril/valsartan vs enalapril', citation: 'McMurray 2014', year: 2014, measure: 'HR', estimate: 0.80, lci: 0.73, uci: 0.87, k: 1, n: 8442, scope: 'Sacubitril/valsartan vs enalapril, HFrEF; primary composite. NEJM 2014;371:993-1004. (ARNI anchor.)' },
                { label: 'FINEARTS-HF finerenone in HFmrEF/HFpEF', citation: 'Solomon 2024', year: 2024, measure: 'HR', estimate: 0.84, lci: 0.74, uci: 0.95, k: 1, n: 6001, scope: 'Finerenone vs placebo in HFmrEF/HFpEF; total HF events + CV death. NEJM 2024;391:1475-1485. (MRA anchor.)' }
            ]
        }""",
        "outcome_map_body": make_outcome_map("CV_DEATH_HHF"),
    },

    # ============ RCC_1L_NMA ============
    "RCC_1L_NMA_REVIEW.html": {
        "source": "IO_CHEMO_NSCLC_1L_REVIEW.html",
        "title": "RapidMeta Onco | First-Line Advanced RCC — IO Doublet & IO+TKI NMA v1.0",
        "nct_ids": ["NCT03141177", "NCT02853331", "NCT02811861", "NCT02231749"],
        "acronyms": {
            "NCT03141177": "CheckMate 9ER", "NCT02853331": "KEYNOTE-426",
            "NCT02811861": "CLEAR", "NCT02231749": "CheckMate 214",
        },
        "realData_body": trials_block([
            trial_entry("NCT03141177", "CheckMate 9ER", "33657295", 2021, 144, 323, 191, 328, 0.51, 0.41, 0.64,
                "Advanced clear-cell RCC (1L, all IMDC risk), cabozantinib + nivolumab vs sunitinib (PFS; HR)",
                "Progression-free survival (primary, cabo+nivo vs sunitinib in 1L aRCC)",
                "https://www.nejm.org/doi/full/10.1056/NEJMoa2026982",
                "https://clinicaltrials.gov/study/NCT03141177",
                "Source: Choueiri TK et al. NEJM 2021;384:829-841 (CheckMate 9ER)."),
            trial_entry("NCT02853331", "KEYNOTE-426", "30779529", 2019, 195, 432, 250, 429, 0.69, 0.57, 0.84,
                "Advanced clear-cell RCC (1L), axitinib + pembrolizumab vs sunitinib (PFS; HR)",
                "Progression-free survival (primary, axi+pembro vs sunitinib in 1L aRCC)",
                "https://www.nejm.org/doi/full/10.1056/NEJMoa1816714",
                "https://clinicaltrials.gov/study/NCT02853331",
                "Source: Rini BI et al. NEJM 2019;380:1116-1127 (KEYNOTE-426)."),
            trial_entry("NCT02811861", "CLEAR", "33616314", 2021, 160, 355, 226, 357, 0.39, 0.32, 0.49,
                "Advanced clear-cell RCC (1L, all IMDC risk), lenvatinib + pembrolizumab vs sunitinib (PFS; HR)",
                "Progression-free survival (primary, lenva+pembro vs sunitinib in 1L aRCC)",
                "https://www.nejm.org/doi/full/10.1056/NEJMoa2035716",
                "https://clinicaltrials.gov/study/NCT02811861",
                "Source: Motzer R et al. NEJM 2021;384:1289-1300 (CLEAR)."),
            trial_entry("NCT02231749", "CheckMate 214", "29562145", 2018, 173, 425, 196, 422, 0.82, 0.64, 1.05,
                "Advanced clear-cell RCC (1L, intermediate/poor risk), ipilimumab + nivolumab vs sunitinib (PFS; HR)",
                "Progression-free survival (primary in IMDC int/poor; ipi+nivo vs sunitinib)",
                "https://www.nejm.org/doi/full/10.1056/NEJMoa1712126",
                "https://clinicaltrials.gov/study/NCT02231749",
                "Source: Motzer RJ et al. NEJM 2018;378:1277-1290 (CheckMate 214)."),
        ]),
        "benchmarks_body": """{
            'PFS': [
                { label: 'CheckMate 9ER cabo+nivo vs sunitinib', citation: 'Choueiri 2021', year: 2021, measure: 'HR', estimate: 0.51, lci: 0.41, uci: 0.64, k: 1, n: 651, scope: 'Cabo+nivo vs sunitinib in 1L aRCC; PFS. NEJM 2021;384:829-841.' },
                { label: 'CLEAR lenva+pembro vs sunitinib', citation: 'Motzer 2021', year: 2021, measure: 'HR', estimate: 0.39, lci: 0.32, uci: 0.49, k: 1, n: 712, scope: 'Lenva+pembro vs sunitinib in 1L aRCC; PFS. NEJM 2021;384:1289-1300.' },
                { label: 'KEYNOTE-426 axi+pembro vs sunitinib', citation: 'Rini 2019', year: 2019, measure: 'HR', estimate: 0.69, lci: 0.57, uci: 0.84, k: 1, n: 861, scope: 'Axi+pembro vs sunitinib in 1L aRCC; PFS. NEJM 2019;380:1116-1127.' }
            ]
        }""",
        "outcome_map_body": make_outcome_map("PFS"),
    },

    # ============ MM_1L_NMA ============
    "MM_1L_NMA_REVIEW.html": {
        "source": "CART_MM_REVIEW.html",
        "title": "RapidMeta Onco | First-Line Multiple Myeloma — Anti-CD38 Quadruplet NMA v1.0",
        "nct_ids": ["NCT02252172", "NCT02195479", "NCT02541383", "NCT03319667"],
        "acronyms": {
            "NCT02252172": "MAIA", "NCT02195479": "ALCYONE",
            "NCT02541383": "CASSIOPEIA", "NCT03319667": "IMROZ",
        },
        "realData_body": trials_block([
            trial_entry("NCT02252172", "MAIA", "30790663", 2019, 99, 368, 152, 369, 0.56, 0.43, 0.73,
                "Newly-diagnosed MM, transplant-ineligible, daratumumab + lenalidomide + dex vs Rd (PFS; HR)",
                "Progression-free survival (primary, Dara-Rd vs Rd in transplant-ineligible NDMM)",
                "https://www.nejm.org/doi/full/10.1056/NEJMoa1817249",
                "https://clinicaltrials.gov/study/NCT02252172",
                "Source: Facon T et al. NEJM 2019;380:2104-2115 (MAIA)."),
            trial_entry("NCT02195479", "ALCYONE", "29231133", 2018, 88, 350, 156, 356, 0.50, 0.38, 0.65,
                "Newly-diagnosed MM, transplant-ineligible, daratumumab + VMP vs VMP (PFS; HR)",
                "Progression-free survival (primary, Dara-VMP vs VMP in transplant-ineligible NDMM)",
                "https://www.nejm.org/doi/full/10.1056/NEJMoa1714678",
                "https://clinicaltrials.gov/study/NCT02195479",
                "Source: Mateos MV et al. NEJM 2018;378:518-528 (ALCYONE)."),
            trial_entry("NCT02541383", "CASSIOPEIA", "31171419", 2019, 60, 543, 122, 542, 0.47, 0.33, 0.67,
                "Newly-diagnosed MM, transplant-eligible, daratumumab + VTd vs VTd (sCR post-consolidation; HR for PFS)",
                "Progression-free survival (Dara-VTd vs VTd post-induction + ASCT + consolidation)",
                "https://www.thelancet.com/journals/lancet/article/PIIS0140-6736(19)31240-1/fulltext",
                "https://clinicaltrials.gov/study/NCT02541383",
                "Source: Moreau P et al. Lancet 2019;394:29-38 (CASSIOPEIA)."),
            trial_entry("NCT03319667", "IMROZ", "38842558", 2024, 64, 265, 102, 265, 0.60, 0.44, 0.81,
                "Newly-diagnosed MM, transplant-ineligible, isatuximab + VRd vs VRd (PFS; HR)",
                "Progression-free survival (primary, Isa-VRd vs VRd in transplant-ineligible NDMM)",
                "https://www.nejm.org/doi/full/10.1056/NEJMoa2402233",
                "https://clinicaltrials.gov/study/NCT03319667",
                "Source: Facon T et al. NEJM 2024;391:1597-1609 (IMROZ)."),
        ]),
        "benchmarks_body": """{
            'PFS': [
                { label: 'MAIA Dara-Rd vs Rd (transplant-ineligible)', citation: 'Facon 2019', year: 2019, measure: 'HR', estimate: 0.56, lci: 0.43, uci: 0.73, k: 1, n: 737, scope: 'Daratumumab + lenalidomide + dex vs Rd in transplant-ineligible NDMM; PFS. NEJM 2019;380:2104-2115.' },
                { label: 'CASSIOPEIA Dara-VTd vs VTd (transplant-eligible)', citation: 'Moreau 2019', year: 2019, measure: 'HR', estimate: 0.47, lci: 0.33, uci: 0.67, k: 1, n: 1085, scope: 'Daratumumab + VTd vs VTd in transplant-eligible NDMM; PFS. Lancet 2019;394:29-38.' },
                { label: 'IMROZ Isa-VRd vs VRd (transplant-ineligible)', citation: 'Facon 2024', year: 2024, measure: 'HR', estimate: 0.60, lci: 0.44, uci: 0.81, k: 1, n: 530, scope: 'Isatuximab + VRd vs VRd in transplant-ineligible NDMM; PFS. NEJM 2024;391:1597-1609.' }
            ]
        }""",
        "outcome_map_body": make_outcome_map("PFS"),
    },

    # ============ PSA_BIOLOGICS_NMA ============
    "PSA_BIOLOGICS_NMA_REVIEW.html": {
        "source": "JAKI_RA_NMA_REVIEW.html",
        "title": "RapidMeta Rheum | Psoriatic Arthritis Biologics NMA (TNFi / IL-17 / IL-23 / JAKi) v1.0",
        "nct_ids": ["NCT01695239", "NCT03158285", "NCT03895203", "NCT03104400"],
        "acronyms": {
            "NCT01695239": "SPIRIT-P1", "NCT03158285": "DISCOVER-2",
            "NCT03895203": "BE OPTIMAL", "NCT03104400": "SELECT-PsA 1",
        },
        "realData_body": trials_block([
            trial_entry("NCT01695239", "SPIRIT-P1", "27553214", 2017, 64, 107, 31, 106, 2.04, 1.45, 2.87,
                "Biologic-naive PsA, ixekizumab Q4W vs placebo (ACR20 at week 24; RR)",
                "ACR20 response at week 24 (primary, ixekizumab Q4W vs placebo, biologic-naive PsA)",
                "https://ard.bmj.com/content/76/1/79",
                "https://clinicaltrials.gov/study/NCT01695239",
                "Source: Mease PJ et al. Ann Rheum Dis 2017;76:79-87 (SPIRIT-P1)."),
            trial_entry("NCT03158285", "DISCOVER-2", "32135126", 2020, 156, 245, 81, 246, 1.93, 1.58, 2.36,
                "Biologic-naive PsA, guselkumab 100 mg Q8W vs placebo (ACR20 at week 24; RR)",
                "ACR20 response at week 24 (primary, guselkumab Q8W vs placebo, biologic-naive PsA)",
                "https://www.thelancet.com/journals/lancet/article/PIIS0140-6736(20)30265-8/fulltext",
                "https://clinicaltrials.gov/study/NCT03158285",
                "Source: Mease PJ et al. Lancet 2020;395:1126-1136 (DISCOVER-2)."),
            trial_entry("NCT03895203", "BE OPTIMAL", "37541749", 2023, 189, 431, 28, 281, 4.40, 3.05, 6.34,
                "Biologic-naive PsA, bimekizumab 160 mg Q4W vs placebo (ACR50 at week 16; RR)",
                "ACR50 response at week 16 (primary, bimekizumab vs placebo, biologic-naive PsA)",
                "https://www.thelancet.com/journals/lancet/article/PIIS0140-6736(23)00112-5/fulltext",
                "https://clinicaltrials.gov/study/NCT03895203",
                "Source: McInnes IB et al. Lancet 2023;401:25-37 (BE OPTIMAL)."),
            trial_entry("NCT03104400", "SELECT-PsA 1", "33870643", 2021, 305, 425, 154, 423, 1.97, 1.71, 2.27,
                "Biologic-naive PsA, upadacitinib 15 mg vs placebo (ACR20 at week 12; RR)",
                "ACR20 response at week 12 (primary, upadacitinib 15 mg vs placebo, biologic-naive PsA)",
                "https://www.nejm.org/doi/full/10.1056/NEJMoa2022516",
                "https://clinicaltrials.gov/study/NCT03104400",
                "Source: McInnes IB et al. NEJM 2021;384:1227-1239 (SELECT-PsA 1)."),
        ]),
        "benchmarks_body": """{
            'ACR20': [
                { label: 'SELECT-PsA 1 upadacitinib 15 mg vs placebo', citation: 'McInnes 2021', year: 2021, measure: 'RR', estimate: 1.97, lci: 1.71, uci: 2.27, k: 1, n: 848, scope: 'Upadacitinib 15 mg vs placebo in biologic-naive PsA; ACR20 at wk 12. NEJM 2021;384:1227-1239.' },
                { label: 'DISCOVER-2 guselkumab vs placebo', citation: 'Mease 2020', year: 2020, measure: 'RR', estimate: 1.93, lci: 1.58, uci: 2.36, k: 1, n: 491, scope: 'Guselkumab 100 mg Q8W vs placebo in biologic-naive PsA; ACR20 at wk 24. Lancet 2020;395:1126-1136.' },
                { label: 'BE OPTIMAL bimekizumab vs placebo (ACR50)', citation: 'McInnes 2023', year: 2023, measure: 'RR', estimate: 4.40, lci: 3.05, uci: 6.34, k: 1, n: 712, scope: 'Bimekizumab vs placebo in biologic-naive PsA; ACR50 at wk 16 (note: stricter endpoint). Lancet 2023;401:25-37.' }
            ]
        }""",
        "outcome_map_body": make_outcome_map("ACR20"),
    },

    # ============ ALOPECIA_JAKI_NMA ============
    "ALOPECIA_JAKI_NMA_REVIEW.html": {
        "source": "JAKI_AD_REVIEW.html",
        "title": "RapidMeta Derm | JAK Inhibitors in Severe Alopecia Areata — NMA v1.0",
        "nct_ids": ["NCT03570749", "NCT03899259", "NCT03732807", "NCT04518995", "NCT04797650"],
        "acronyms": {
            "NCT03570749": "BRAVE-AA1", "NCT03899259": "BRAVE-AA2",
            "NCT03732807": "ALLEGRO-2b/3", "NCT04518995": "THRIVE-AA1",
            "NCT04797650": "THRIVE-AA2",
        },
        "realData_body": trials_block([
            trial_entry("NCT03570749", "BRAVE-AA1", "35334197", 2022, 102, 281, 9, 189, 7.60, 3.96, 14.59,
                "Severe alopecia areata, baricitinib 4 mg PO daily vs placebo (SALT<=20 at wk 36; RR)",
                "SALT <=20 (primary, baricitinib 4 mg vs placebo, severe alopecia areata; BRAVE-AA1)",
                "https://www.nejm.org/doi/full/10.1056/NEJMoa2110343",
                "https://clinicaltrials.gov/study/NCT03570749",
                "Source: King B et al. NEJM 2022;386:1687-1699 (BRAVE-AA1+AA2)."),
            trial_entry("NCT03899259", "BRAVE-AA2", "35334197", 2022, 80, 234, 5, 156, 10.66, 4.41, 25.81,
                "Severe alopecia areata, baricitinib 4 mg PO daily vs placebo (SALT<=20 at wk 36; RR)",
                "SALT <=20 (primary, baricitinib 4 mg vs placebo, severe alopecia areata; BRAVE-AA2)",
                "https://www.nejm.org/doi/full/10.1056/NEJMoa2110343",
                "https://clinicaltrials.gov/study/NCT03899259",
                "Source: King B et al. NEJM 2022;386:1687-1699 (BRAVE-AA2)."),
            trial_entry("NCT03732807", "ALLEGRO-2b/3", "37148884", 2023, 35, 130, 1, 131, 35.27, 4.91, 253.39,
                "Severe alopecia areata, ritlecitinib 50 mg PO daily vs placebo (SALT<=20 at wk 24; RR)",
                "SALT <=20 (primary, ritlecitinib 50 mg vs placebo, severe alopecia areata)",
                "https://www.thelancet.com/journals/lancet/article/PIIS0140-6736(23)00161-7/fulltext",
                "https://clinicaltrials.gov/study/NCT03732807",
                "Source: King B et al. Lancet 2023;401:1518-1529 (ALLEGRO-2b/3)."),
            trial_entry("NCT04518995", "THRIVE-AA1", "37423283", 2023, 92, 235, 1, 117, 45.83, 6.51, 322.85,
                "Severe alopecia areata, deuruxolitinib 8 mg PO BID vs placebo (SALT<=20 at wk 24; RR)",
                "SALT <=20 (primary, deuruxolitinib 8 mg BID vs placebo, severe alopecia areata; THRIVE-AA1)",
                "https://www.thelancet.com/journals/lancet/article/PIIS0140-6736(23)00585-8/fulltext",
                "https://clinicaltrials.gov/study/NCT04518995",
                "Source: King B et al. Lancet 2023;402:1736-1745 (THRIVE-AA1+AA2)."),
            trial_entry("NCT04797650", "THRIVE-AA2", "37423283", 2023, 75, 175, 1, 86, 36.86, 5.21, 260.69,
                "Severe alopecia areata, deuruxolitinib 8 mg PO BID vs placebo (SALT<=20 at wk 24; RR)",
                "SALT <=20 (primary, deuruxolitinib 8 mg BID vs placebo, severe alopecia areata; THRIVE-AA2)",
                "https://www.thelancet.com/journals/lancet/article/PIIS0140-6736(23)00585-8/fulltext",
                "https://clinicaltrials.gov/study/NCT04797650",
                "Source: King B et al. Lancet 2023;402:1736-1745 (THRIVE-AA2)."),
        ]),
        "benchmarks_body": """{
            'SALT_LE_20': [
                { label: 'BRAVE-AA1+AA2 baricitinib 4 mg pooled', citation: 'King 2022', year: 2022, measure: 'RR', estimate: 8.50, lci: 4.50, uci: 16.00, k: 2, n: 1200, scope: 'Baricitinib 4 mg vs placebo pooled; SALT<=20 at 36 wk in severe alopecia areata. NEJM 2022;386:1687-1699.' },
                { label: 'ALLEGRO-2b/3 ritlecitinib 50 mg vs placebo', citation: 'King 2023', year: 2023, measure: 'RR', estimate: 35.30, lci: 4.91, uci: 253.39, k: 1, n: 718, scope: 'Ritlecitinib 50 mg vs placebo; SALT<=20 at 24 wk. Lancet 2023;401:1518-1529.' },
                { label: 'THRIVE-AA1+AA2 deuruxolitinib 8 mg pooled', citation: 'King 2023b', year: 2023, measure: 'RR', estimate: 40.00, lci: 5.50, uci: 290.00, k: 2, n: 1223, scope: 'Deuruxolitinib 8 mg BID vs placebo pooled; SALT<=20 at 24 wk. Lancet 2023;402:1736-1745.' }
            ]
        }""",
        "outcome_map_body": make_outcome_map("SALT_LE_20"),
    },

}


def main():
    ok = fail = 0
    for target_name, spec in SPECS.items():
        source = ROOT / spec["source"]
        target = ROOT / target_name
        if not source.exists():
            print(f"FAIL {target_name}: source missing")
            fail += 1
            continue
        r = clone_app(source, target, spec)
        print(r)
        if r.startswith("OK"):
            ok += 1
        else:
            fail += 1
    print(f"\nTier 4 batch A: {ok} ok / {fail} fail")


if __name__ == "__main__":
    main()
