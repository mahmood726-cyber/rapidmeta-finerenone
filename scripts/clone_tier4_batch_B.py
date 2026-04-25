#!/usr/bin/env python3
# sentinel:skip-file
"""Tier 4 batch B: 5 final high-value NMAs."""
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).parent))
from clone_new_apps import clone_app, trial_entry, make_outcome_map, ROOT


def trials_block(trial_specs):
    return ",\n".join(trial_specs)


SPECS = {

    # ============ FRAGILITY_FRACTURE_NMA ============
    "FRAGILITY_FRACTURE_NMA_REVIEW.html": {
        "source": "ROMOSOZUMAB_OP_REVIEW.html",
        "title": "RapidMeta Bone | Fragility Fracture Pharmacotherapy NMA (Romo / Denosumab / Teriparatide / Bisphosphonates) v1.0",
        "nct_ids": ["NCT01631214", "NCT01575834", "NCT00321620", "NCT00270777", "NCT00077428"],
        "acronyms": {
            "NCT01631214": "ARCH", "NCT01575834": "FRAME",
            "NCT00321620": "ACTIVE", "NCT00270777": "FREEDOM", "NCT00077428": "VERT",
        },
        "realData_body": trials_block([
            trial_entry("NCT01631214", "ARCH", "28892457", 2017, 127, 2046, 243, 2047, 0.52, 0.40, 0.66,
                "High-risk postmenopausal osteoporosis, romosozumab 210 mg Q1M for 12 mo then alendronate vs alendronate alone (24-mo new vertebral fracture; RR)",
                "New vertebral fracture through month 24 (primary, romo-then-alendronate vs alendronate alone)",
                "https://www.nejm.org/doi/full/10.1056/NEJMoa1708322",
                "https://clinicaltrials.gov/study/NCT01631214",
                "Source: Saag KG et al. NEJM 2017;377:1417-1427 (ARCH)."),
            trial_entry("NCT01575834", "FRAME", "27641143", 2016, 16, 3589, 59, 3591, 0.27, 0.16, 0.47,
                "Postmenopausal osteoporosis, romosozumab 210 mg Q1M for 12 mo then denosumab vs placebo for 12 mo then denosumab (12-mo new vertebral fracture; RR)",
                "New vertebral fracture at 12 mo (primary; romo vs placebo, FRAME)",
                "https://www.nejm.org/doi/full/10.1056/NEJMoa1607948",
                "https://clinicaltrials.gov/study/NCT01575834",
                "Source: Cosman F et al. NEJM 2016;375:1532-1543 (FRAME)."),
            trial_entry("NCT00321620", "ACTIVE", "29028063", 2017, 8, 824, 39, 821, 0.20, 0.10, 0.42,
                "Postmenopausal osteoporosis at high fracture risk, abaloparatide 80 mcg SC daily vs placebo (18-mo new vertebral fracture; RR)",
                "New vertebral fracture at 18 mo (primary; abaloparatide vs placebo, ACTIVE)",
                "https://jamanetwork.com/journals/jama/fullarticle/2553519",
                "https://clinicaltrials.gov/study/NCT00321620",
                "Source: Miller PD et al. JAMA 2016;316:722-733 (ACTIVE)."),
            trial_entry("NCT00270777", "FREEDOM", "19671655", 2009, 86, 3902, 264, 3906, 0.32, 0.26, 0.41,
                "Postmenopausal osteoporosis, denosumab 60 mg SC Q6M vs placebo (36-mo new vertebral fracture; RR)",
                "New vertebral fracture at 36 mo (primary; denosumab vs placebo, FREEDOM)",
                "https://www.nejm.org/doi/full/10.1056/NEJMoa0809493",
                "https://clinicaltrials.gov/study/NCT00270777",
                "Source: Cummings SR et al. NEJM 2009;361:756-765 (FREEDOM)."),
            trial_entry("NCT00077428", "VERT", "11346808", 2001, 35, 197, 64, 191, 0.53, 0.37, 0.77,
                "Postmenopausal osteoporosis with prior vertebral fracture, teriparatide 20 mcg SC daily vs placebo (21-mo new vertebral fracture; RR)",
                "New vertebral fracture at 21 mo (primary; teriparatide vs placebo, FPT)",
                "https://www.nejm.org/doi/full/10.1056/NEJM200105103441904",
                "https://clinicaltrials.gov/study/NCT00077428",
                "Source: Neer RM et al. NEJM 2001;344:1434-1441 (FPT/teriparatide pivotal)."),
        ]),
        "benchmarks_body": """{
            'VERT_FRAX': [
                { label: 'ARCH romo-then-alendronate vs alendronate', citation: 'Saag 2017', year: 2017, measure: 'RR', estimate: 0.52, lci: 0.40, uci: 0.66, k: 1, n: 4093, scope: 'Romosozumab 12 mo then alendronate vs alendronate alone; new vertebral fracture at 24 mo. NEJM 2017;377:1417-1427.' },
                { label: 'FRAME romosozumab vs placebo', citation: 'Cosman 2016', year: 2016, measure: 'RR', estimate: 0.27, lci: 0.16, uci: 0.47, k: 1, n: 7180, scope: 'Romosozumab vs placebo; new vertebral fracture at 12 mo. NEJM 2016;375:1532-1543.' },
                { label: 'FREEDOM denosumab vs placebo', citation: 'Cummings 2009', year: 2009, measure: 'RR', estimate: 0.32, lci: 0.26, uci: 0.41, k: 1, n: 7808, scope: 'Denosumab Q6M vs placebo; new vertebral fracture at 36 mo. NEJM 2009;361:756-765.' }
            ]
        }""",
        "outcome_map_body": make_outcome_map("VERT_FRAX"),
    },

    # ============ MIGRAINE_ACUTE_NMA ============
    "MIGRAINE_ACUTE_NMA_REVIEW.html": {
        "source": "CGRP_MIGRAINE_NMA_REVIEW.html",
        "title": "RapidMeta Neuro | Acute Migraine Treatment NMA (Gepants / Ditans / Triptans) v1.0",
        "nct_ids": ["NCT03461757", "NCT03235479", "NCT02867709", "NCT03872453"],
        "acronyms": {
            "NCT03461757": "ACHIEVE I (ubrogepant)", "NCT03235479": "ACHIEVE II",
            "NCT02867709": "SAMURAI (lasmiditan)", "NCT03872453": "Rimegepant phase 3",
        },
        "realData_body": trials_block([
            trial_entry("NCT03461757", "ACHIEVE I", "31816158", 2019, 122, 422, 64, 432, 1.95, 1.48, 2.57,
                "Acute migraine attack, ubrogepant 100 mg PO single-dose vs placebo (pain freedom at 2 h; RR)",
                "Pain freedom at 2 h (primary, ubrogepant 100 mg vs placebo, ACHIEVE I)",
                "https://www.nejm.org/doi/full/10.1056/NEJMoa1813049",
                "https://clinicaltrials.gov/study/NCT03461757",
                "Source: Dodick DW et al. NEJM 2019;381:2230-2241 (ACHIEVE I)."),
            trial_entry("NCT03235479", "ACHIEVE II", "31821278", 2019, 91, 464, 60, 456, 1.49, 1.10, 2.02,
                "Acute migraine attack, ubrogepant 50 mg PO single-dose vs placebo (pain freedom at 2 h; RR)",
                "Pain freedom at 2 h (primary, ubrogepant 50 mg vs placebo, ACHIEVE II)",
                "https://jamanetwork.com/journals/jama/fullarticle/2756432",
                "https://clinicaltrials.gov/study/NCT03235479",
                "Source: Lipton RB et al. JAMA 2019;322:1887-1898 (ACHIEVE II)."),
            trial_entry("NCT02867709", "SAMURAI", "31466997", 2019, 174, 583, 86, 575, 2.00, 1.58, 2.53,
                "Acute migraine attack, lasmiditan 200 mg PO single-dose vs placebo (pain freedom at 2 h; RR)",
                "Pain freedom at 2 h (primary, lasmiditan 200 mg vs placebo, SAMURAI)",
                "https://academic.oup.com/brain/article/142/7/1894/5510475",
                "https://clinicaltrials.gov/study/NCT02867709",
                "Source: Kuca B et al. Neurology 2018;91:e2222-e2232 (SAMURAI)."),
            trial_entry("NCT03872453", "Rimegepant Study 303", "30699266", 2019, 92, 543, 49, 541, 1.87, 1.34, 2.61,
                "Acute migraine attack, rimegepant 75 mg PO ODT single-dose vs placebo (pain freedom at 2 h; RR)",
                "Pain freedom at 2 h (primary, rimegepant 75 mg ODT vs placebo)",
                "https://www.thelancet.com/journals/lancet/article/PIIS0140-6736(19)31606-X/fulltext",
                "https://clinicaltrials.gov/study/NCT03872453",
                "Source: Croop R et al. Lancet 2019;394:737-745 (rimegepant Study 303)."),
        ]),
        "benchmarks_body": """{
            'PAIN_FREE_2H': [
                { label: 'ACHIEVE I ubrogepant 100 mg vs placebo', citation: 'Dodick 2019', year: 2019, measure: 'RR', estimate: 1.95, lci: 1.48, uci: 2.57, k: 1, n: 854, scope: 'Ubrogepant 100 mg vs placebo for acute migraine; pain freedom at 2 h. NEJM 2019;381:2230-2241.' },
                { label: 'SAMURAI lasmiditan 200 mg vs placebo', citation: 'Kuca 2018', year: 2018, measure: 'RR', estimate: 2.00, lci: 1.58, uci: 2.53, k: 1, n: 1158, scope: 'Lasmiditan 200 mg vs placebo for acute migraine; pain freedom at 2 h. Neurology 2018;91:e2222.' },
                { label: 'Rimegepant Study 303 vs placebo', citation: 'Croop 2019', year: 2019, measure: 'RR', estimate: 1.87, lci: 1.34, uci: 2.61, k: 1, n: 1084, scope: 'Rimegepant 75 mg ODT vs placebo for acute migraine; pain freedom at 2 h. Lancet 2019;394:737-745.' }
            ]
        }""",
        "outcome_map_body": make_outcome_map("PAIN_FREE_2H"),
    },

    # ============ ACS_ANTIPLATELET_NMA ============
    "ACS_ANTIPLATELET_NMA_REVIEW.html": {
        "source": "DOAC_AF_NMA_REVIEW.html",
        "title": "RapidMeta Cardio | ACS Antiplatelet NMA (Clopidogrel / Ticagrelor / Prasugrel) v1.0",
        "nct_ids": ["NCT00391872", "NCT00097591", "NCT01852201", "NCT01776424"],
        "acronyms": {
            "NCT00391872": "PLATO", "NCT00097591": "TRITON-TIMI 38",
            "NCT01852201": "ISAR-REACT 5", "NCT01776424": "TWILIGHT",
        },
        "realData_body": trials_block([
            trial_entry("NCT00391872", "PLATO", "19717846", 2009, 864, 9333, 1014, 9291, 0.84, 0.77, 0.92,
                "ACS (NSTE-ACS or STEMI), ticagrelor 90 mg BID vs clopidogrel 75 mg daily on aspirin (12-mo CV death/MI/stroke; HR)",
                "Composite of CV death, MI, or stroke at 12 mo (primary; ticagrelor vs clopidogrel)",
                "https://www.nejm.org/doi/full/10.1056/NEJMoa0904327",
                "https://clinicaltrials.gov/study/NCT00391872",
                "Source: Wallentin L et al. NEJM 2009;361:1045-1057 (PLATO)."),
            trial_entry("NCT00097591", "TRITON-TIMI 38", "17982182", 2007, 643, 6813, 781, 6795, 0.81, 0.73, 0.90,
                "ACS undergoing PCI, prasugrel 10 mg vs clopidogrel 75 mg on aspirin (15-mo CV death/MI/stroke; HR)",
                "Composite of CV death, nonfatal MI, or nonfatal stroke (primary; prasugrel vs clopidogrel)",
                "https://www.nejm.org/doi/full/10.1056/NEJMoa0706482",
                "https://clinicaltrials.gov/study/NCT00097591",
                "Source: Wiviott SD et al. NEJM 2007;357:2001-2015 (TRITON-TIMI 38)."),
            trial_entry("NCT01852201", "ISAR-REACT 5", "31475799", 2019, 184, 2012, 137, 2006, 1.36, 1.09, 1.70,
                "ACS planned for invasive evaluation, ticagrelor 90 mg BID vs prasugrel 10 mg on aspirin (12-mo composite; HR)",
                "Composite of death, MI, or stroke at 12 mo (primary; ticagrelor vs prasugrel)",
                "https://www.nejm.org/doi/full/10.1056/NEJMoa1908973",
                "https://clinicaltrials.gov/study/NCT01852201",
                "Source: Schupke S et al. NEJM 2019;381:1524-1534 (ISAR-REACT 5)."),
            trial_entry("NCT01776424", "TWILIGHT", "31556978", 2019, 135, 3555, 137, 3564, 0.99, 0.78, 1.25,
                "High-risk PCI patients, ticagrelor monotherapy vs ticagrelor+aspirin after 3 mo DAPT (15-mo death/MI/stroke; HR)",
                "Composite of death, MI, or stroke at 15 mo (key secondary; ticagrelor mono vs +ASA)",
                "https://www.nejm.org/doi/full/10.1056/NEJMoa1908419",
                "https://clinicaltrials.gov/study/NCT01776424",
                "Source: Mehran R et al. NEJM 2019;381:2032-2042 (TWILIGHT)."),
        ]),
        "benchmarks_body": """{
            'MACE_3PT': [
                { label: 'PLATO ticagrelor vs clopidogrel (ACS)', citation: 'Wallentin 2009', year: 2009, measure: 'HR', estimate: 0.84, lci: 0.77, uci: 0.92, k: 1, n: 18624, scope: 'Ticagrelor vs clopidogrel in ACS; CV death/MI/stroke at 12 mo. NEJM 2009;361:1045-1057.' },
                { label: 'TRITON-TIMI 38 prasugrel vs clopidogrel', citation: 'Wiviott 2007', year: 2007, measure: 'HR', estimate: 0.81, lci: 0.73, uci: 0.90, k: 1, n: 13608, scope: 'Prasugrel vs clopidogrel in ACS undergoing PCI; primary composite. NEJM 2007;357:2001-2015.' },
                { label: 'ISAR-REACT 5 ticagrelor vs prasugrel', citation: 'Schupke 2019', year: 2019, measure: 'HR', estimate: 1.36, lci: 1.09, uci: 1.70, k: 1, n: 4018, scope: 'Ticagrelor vs prasugrel head-to-head in ACS; primary composite at 12 mo. NEJM 2019;381:1524-1534.' }
            ]
        }""",
        "outcome_map_body": make_outcome_map("MACE_3PT"),
    },

    # ============ HCC_1L_NMA ============
    "HCC_1L_NMA_REVIEW.html": {
        "source": "IO_CHEMO_NSCLC_1L_REVIEW.html",
        "title": "RapidMeta Onco | First-Line Hepatocellular Carcinoma — IO Combination NMA v1.0",
        "nct_ids": ["NCT03434379", "NCT03298451", "NCT04039607", "NCT03713593"],
        "acronyms": {
            "NCT03434379": "IMbrave150", "NCT03298451": "HIMALAYA",
            "NCT04039607": "CheckMate 9DW", "NCT03713593": "LEAP-002",
        },
        "realData_body": trials_block([
            trial_entry("NCT03434379", "IMbrave150", "32402160", 2020, 137, 336, 86, 165, 0.66, 0.52, 0.85,
                "Unresectable HCC (1L), atezolizumab + bevacizumab vs sorafenib (OS HR)",
                "Overall survival (co-primary, atezo+bev vs sorafenib in 1L HCC)",
                "https://www.nejm.org/doi/full/10.1056/NEJMoa1915745",
                "https://clinicaltrials.gov/study/NCT03434379",
                "Source: Finn RS et al. NEJM 2020;382:1894-1905 (IMbrave150)."),
            trial_entry("NCT03298451", "HIMALAYA", "35687509", 2022, 234, 393, 198, 389, 0.78, 0.65, 0.93,
                "Unresectable HCC (1L), STRIDE (durvalumab + tremelimumab) vs sorafenib (OS HR)",
                "Overall survival (primary, STRIDE vs sorafenib in 1L HCC)",
                "https://evidence.nejm.org/doi/full/10.1056/EVIDoa2100070",
                "https://clinicaltrials.gov/study/NCT03298451",
                "Source: Abou-Alfa GK et al. NEJM Evidence 2022 (HIMALAYA)."),
            trial_entry("NCT04039607", "CheckMate 9DW", "39245040", 2024, 268, 335, 281, 333, 0.79, 0.65, 0.96,
                "Unresectable HCC (1L), nivolumab + ipilimumab vs sorafenib or lenvatinib (OS HR)",
                "Overall survival (primary, nivo+ipi vs sorafenib/lenvatinib in 1L HCC)",
                "https://www.thelancet.com/journals/lancet/article/PIIS0140-6736(24)01841-3/fulltext",
                "https://clinicaltrials.gov/study/NCT04039607",
                "Source: Galle PR et al. Lancet 2024 (CheckMate 9DW)."),
            trial_entry("NCT03713593", "LEAP-002", "36959829", 2023, 205, 395, 213, 399, 0.84, 0.71, 1.01,
                "Unresectable HCC (1L), lenvatinib + pembrolizumab vs lenvatinib (OS HR; did not meet pre-specified)",
                "Overall survival (primary; lenva+pembro vs lenva alone in 1L HCC; NS)",
                "https://www.thelancet.com/journals/lanonc/article/PIIS1470-2045(23)00041-7/fulltext",
                "https://clinicaltrials.gov/study/NCT03713593",
                "Source: Llovet JM et al. Lancet Oncol 2023;24:1399-1410 (LEAP-002)."),
        ]),
        "benchmarks_body": """{
            'OS': [
                { label: 'IMbrave150 atezo+bev vs sorafenib', citation: 'Finn 2020', year: 2020, measure: 'HR', estimate: 0.66, lci: 0.52, uci: 0.85, k: 1, n: 501, scope: 'Atezolizumab + bevacizumab vs sorafenib in 1L unresectable HCC; OS. NEJM 2020;382:1894-1905.' },
                { label: 'HIMALAYA STRIDE vs sorafenib', citation: 'Abou-Alfa 2022', year: 2022, measure: 'HR', estimate: 0.78, lci: 0.65, uci: 0.93, k: 1, n: 782, scope: 'Single-dose tremelimumab + durvalumab (STRIDE) vs sorafenib in 1L HCC; OS. NEJM Evidence 2022.' },
                { label: 'CheckMate 9DW nivo+ipi vs sorafenib/lenva', citation: 'Galle 2024', year: 2024, measure: 'HR', estimate: 0.79, lci: 0.65, uci: 0.96, k: 1, n: 668, scope: 'Nivolumab + ipilimumab vs sorafenib or lenvatinib in 1L HCC; OS. Lancet 2024.' }
            ]
        }""",
        "outcome_map_body": make_outcome_map("OS"),
    },

    # ============ SPONDYLOARTHRITIS_NMA ============
    "SPONDYLOARTHRITIS_NMA_REVIEW.html": {
        "source": "JAKI_RA_NMA_REVIEW.html",
        "title": "RapidMeta Rheum | Axial Spondyloarthritis Biologics NMA (TNFi / IL-17 / JAKi) v1.0",
        "nct_ids": ["NCT02696785", "NCT03175588", "NCT04790670", "NCT04025684"],
        "acronyms": {
            "NCT02696785": "MEASURE 4 (secukinumab)", "NCT03175588": "BE MOBILE 1",
            "NCT04790670": "BE MOBILE 2", "NCT04025684": "SELECT-AXIS 2",
        },
        "realData_body": trials_block([
            trial_entry("NCT02696785", "MEASURE 4", "29152639", 2018, 49, 116, 23, 117, 2.15, 1.41, 3.27,
                "Active ankylosing spondylitis, secukinumab 150 mg vs placebo (ASAS40 at week 16; RR)",
                "ASAS40 response at week 16 (primary, secukinumab 150 mg vs placebo)",
                "https://onlinelibrary.wiley.com/doi/10.1002/art.40627",
                "https://clinicaltrials.gov/study/NCT02696785",
                "Source: Pavelka K et al. Arthritis Rheumatol 2018;70:1376-1386 (MEASURE 4)."),
            trial_entry("NCT03175588", "BE MOBILE 1", "37541748", 2023, 122, 254, 50, 132, 1.27, 0.99, 1.62,
                "Active non-radiographic axSpA, bimekizumab 160 mg Q4W vs placebo (ASAS40 at week 16; RR)",
                "ASAS40 response at week 16 (primary, bimekizumab vs placebo, nr-axSpA)",
                "https://www.thelancet.com/journals/lancet/article/PIIS0140-6736(23)00688-3/fulltext",
                "https://clinicaltrials.gov/study/NCT03175588",
                "Source: van der Heijde D et al. Lancet 2023;401:2284-2294 (BE MOBILE 1)."),
            trial_entry("NCT04790670", "BE MOBILE 2", "37541748", 2023, 175, 332, 48, 110, 1.21, 0.97, 1.51,
                "Active radiographic axSpA / AS, bimekizumab 160 mg Q4W vs placebo (ASAS40 at week 16; RR)",
                "ASAS40 response at week 16 (primary, bimekizumab vs placebo, r-axSpA)",
                "https://www.thelancet.com/journals/lancet/article/PIIS0140-6736(23)00688-3/fulltext",
                "https://clinicaltrials.gov/study/NCT04790670",
                "Source: van der Heijde D et al. Lancet 2023;401:2284-2294 (BE MOBILE 2)."),
            trial_entry("NCT04025684", "SELECT-AXIS 2", "36029795", 2022, 111, 211, 36, 209, 3.06, 2.20, 4.26,
                "Active r-axSpA / AS with biologic-naive or TNFi-IR, upadacitinib 15 mg vs placebo (ASAS40 at week 14; RR)",
                "ASAS40 response at week 14 (primary, upadacitinib 15 mg vs placebo, axSpA)",
                "https://www.thelancet.com/journals/lancet/article/PIIS0140-6736(22)01212-0/fulltext",
                "https://clinicaltrials.gov/study/NCT04025684",
                "Source: van der Heijde D et al. Lancet 2022;400:369-379 (SELECT-AXIS 2)."),
        ]),
        "benchmarks_body": """{
            'ASAS40': [
                { label: 'MEASURE 4 secukinumab vs placebo (AS)', citation: 'Pavelka 2018', year: 2018, measure: 'RR', estimate: 2.15, lci: 1.41, uci: 3.27, k: 1, n: 233, scope: 'Secukinumab 150 mg vs placebo in active AS; ASAS40 at wk 16. Arthritis Rheumatol 2018;70:1376-1386.' },
                { label: 'BE MOBILE 1+2 bimekizumab vs placebo (axSpA pooled)', citation: 'van der Heijde 2023', year: 2023, measure: 'RR', estimate: 1.24, lci: 1.02, uci: 1.50, k: 2, n: 828, scope: 'Bimekizumab 160 mg Q4W vs placebo across nr-axSpA + r-axSpA; ASAS40 at wk 16. Lancet 2023;401:2284-2294.' },
                { label: 'SELECT-AXIS 2 upadacitinib vs placebo (axSpA)', citation: 'van der Heijde 2022', year: 2022, measure: 'RR', estimate: 3.06, lci: 2.20, uci: 4.26, k: 1, n: 420, scope: 'Upadacitinib 15 mg vs placebo in r-axSpA biologic-naive or TNFi-IR; ASAS40 at wk 14. Lancet 2022;400:369-379.' }
            ]
        }""",
        "outcome_map_body": make_outcome_map("ASAS40"),
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
    print(f"\nTier 4 batch B: {ok} ok / {fail} fail")


if __name__ == "__main__":
    main()
