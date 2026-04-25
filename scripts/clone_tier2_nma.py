#!/usr/bin/env python3
# sentinel:skip-file
"""Tier 2: NMA apps. Each has multiple trials in realData with publishedHR
data and shared comparator structure for transitivity.
"""
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).parent))
from clone_new_apps import clone_app, trial_entry, make_outcome_map, ROOT

# Multi-trial body builder
def trials_block(trial_specs):
    return ",\n".join(trial_specs)


SPECS = {

    # ============ OBESITY_DRUGS_NMA ============
    "OBESITY_DRUGS_NMA_REVIEW.html": {
        "source": "INCRETINS_T2D_NMA_REVIEW.html",
        "title": "RapidMeta Endocrine | Obesity Pharmacotherapy NMA (GLP-1, GIP/GLP-1, Amylin) v1.0",
        "nct_ids": ["NCT04184622", "NCT03548935", "NCT05822830", "NCT04657003", "NCT01865305"],
        "acronyms": {
            "NCT04184622": "SURMOUNT-1", "NCT03548935": "STEP 1",
            "NCT05822830": "SURMOUNT-OSA-1", "NCT04657003": "STEP TEENS",
            "NCT01865305": "SCALE Obesity",
        },
        "realData_body": trials_block([
            trial_entry("NCT04184622", "SURMOUNT-1", "35658024", 2022, 1812, 2519, 31, 643, 36.7, 25.5, 52.7,
                "Overweight/obesity without DM, tirzepatide 15 mg SC weekly vs placebo (>=5% weight loss at 72 wk; OR)",
                "Body-weight reduction >=5% at 72 wk (primary, tirzepatide 15 mg pooled vs placebo, OR)",
                "https://www.nejm.org/doi/full/10.1056/NEJMoa2206038",
                "https://clinicaltrials.gov/study/NCT04184622",
                "Source: Jastreboff AM et al. NEJM 2022;387:205-216 (SURMOUNT-1)."),
            trial_entry("NCT03548935", "STEP 1", "33567185", 2021, 1047, 1306, 138, 655, 18.4, 14.4, 23.4,
                "Overweight/obesity without DM, semaglutide 2.4 mg SC weekly vs placebo (>=5% weight loss at 68 wk; OR)",
                "Body-weight reduction >=5% at 68 wk (primary, semaglutide 2.4 mg vs placebo, OR)",
                "https://www.nejm.org/doi/full/10.1056/NEJMoa2032183",
                "https://clinicaltrials.gov/study/NCT03548935",
                "Source: Wilding JPH et al. NEJM 2021;384:989-1002 (STEP 1)."),
            trial_entry("NCT01865305", "SCALE Obesity", "26132939", 2015, 1257, 2487, 376, 1244, 6.0, 5.1, 7.0,
                "Overweight/obesity without DM, liraglutide 3.0 mg SC daily vs placebo (>=5% weight loss at 56 wk; OR)",
                "Body-weight reduction >=5% at 56 wk (primary, liraglutide 3.0 mg vs placebo, OR)",
                "https://www.nejm.org/doi/full/10.1056/NEJMoa1411892",
                "https://clinicaltrials.gov/study/NCT01865305",
                "Source: Pi-Sunyer X et al. NEJM 2015;373:11-22 (SCALE Obesity)."),
        ]),
        "benchmarks_body": """{
            'WEIGHT_LOSS_5PCT': [
                { label: 'SURMOUNT-1 tirzepatide 15 mg vs placebo (>=5% wt loss)', citation: 'Jastreboff 2022', year: 2022, measure: 'OR', estimate: 36.7, lci: 25.5, uci: 52.7, k: 1, n: 2539, scope: 'Tirzepatide 15 mg vs placebo in overweight/obesity (no DM); body-weight reduction >=5% at 72 wk. NEJM 2022;387:205-216.' },
                { label: 'STEP 1 semaglutide 2.4 mg vs placebo', citation: 'Wilding 2021', year: 2021, measure: 'OR', estimate: 18.4, lci: 14.4, uci: 23.4, k: 1, n: 1961, scope: 'Semaglutide 2.4 mg vs placebo in overweight/obesity; >=5% weight loss at 68 wk. NEJM 2021;384:989-1002.' },
                { label: 'SCALE Obesity liraglutide 3.0 mg vs placebo', citation: 'Pi-Sunyer 2015', year: 2015, measure: 'OR', estimate: 6.0, lci: 5.1, uci: 7.0, k: 1, n: 3731, scope: 'Liraglutide 3.0 mg vs placebo; >=5% weight loss at 56 wk. NEJM 2015;373:11-22.' }
            ]
        }""",
        "outcome_map_body": make_outcome_map("WEIGHT_LOSS_5PCT"),
    },

    # ============ ANTI_CD20_MS_NMA ============
    "ANTI_CD20_MS_NMA_REVIEW.html": {
        "source": "JAKI_RA_NMA_REVIEW.html",
        "title": "RapidMeta Neurology | Anti-CD20 Therapies in Relapsing MS — NMA v1.0",
        "nct_ids": ["NCT01247324", "NCT01412333", "NCT02792218", "NCT02792231", "NCT03277261", "NCT03277248"],
        "acronyms": {
            "NCT01247324": "OPERA I", "NCT01412333": "OPERA II",
            "NCT02792218": "ASCLEPIOS I", "NCT02792231": "ASCLEPIOS II",
            "NCT03277261": "ULTIMATE I", "NCT03277248": "ULTIMATE II",
        },
        "realData_body": trials_block([
            trial_entry("NCT01247324", "OPERA I", "28002679", 2017, 95, 410, 167, 411, 0.54, 0.42, 0.69,
                "Relapsing MS, ocrelizumab 600 mg IV Q6M vs IFN beta-1a SC (annualized relapse rate at 96 wk; rate ratio)",
                "Annualized relapse rate at 96 wk (primary, ocrelizumab vs IFN beta-1a, rate ratio)",
                "https://www.nejm.org/doi/full/10.1056/NEJMoa1601277",
                "https://clinicaltrials.gov/study/NCT01247324",
                "Source: Hauser SL et al. NEJM 2017;376:221-234 (OPERA I)."),
            trial_entry("NCT01412333", "OPERA II", "28002679", 2017, 87, 417, 153, 418, 0.53, 0.40, 0.69,
                "Relapsing MS, ocrelizumab 600 mg IV Q6M vs IFN beta-1a SC (ARR at 96 wk; rate ratio)",
                "Annualized relapse rate at 96 wk (primary, ocrelizumab vs IFN beta-1a, rate ratio; OPERA II)",
                "https://www.nejm.org/doi/full/10.1056/NEJMoa1601277",
                "https://clinicaltrials.gov/study/NCT01412333",
                "Source: Hauser SL et al. NEJM 2017;376:221-234 (OPERA II)."),
            trial_entry("NCT02792218", "ASCLEPIOS I", "32757523", 2020, 99, 465, 169, 462, 0.49, 0.37, 0.65,
                "Relapsing MS, ofatumumab 20 mg SC monthly vs teriflunomide 14 mg PO daily (ARR at 30 mo; rate ratio)",
                "Annualized relapse rate at 30 mo (primary, ofatumumab vs teriflunomide; ASCLEPIOS I)",
                "https://www.nejm.org/doi/full/10.1056/NEJMoa1917246",
                "https://clinicaltrials.gov/study/NCT02792218",
                "Source: Hauser SL et al. NEJM 2020;383:546-557 (ASCLEPIOS I)."),
            trial_entry("NCT02792231", "ASCLEPIOS II", "32757523", 2020, 95, 481, 165, 474, 0.42, 0.31, 0.56,
                "Relapsing MS, ofatumumab 20 mg SC monthly vs teriflunomide 14 mg PO daily (ARR at 30 mo; rate ratio)",
                "Annualized relapse rate at 30 mo (primary, ofatumumab vs teriflunomide; ASCLEPIOS II)",
                "https://www.nejm.org/doi/full/10.1056/NEJMoa1917246",
                "https://clinicaltrials.gov/study/NCT02792231",
                "Source: Hauser SL et al. NEJM 2020;383:546-557 (ASCLEPIOS II)."),
            trial_entry("NCT03277261", "ULTIMATE I", "36044451", 2022, 35, 274, 90, 275, 0.41, 0.27, 0.62,
                "Relapsing MS, ublituximab 450 mg IV Q6M vs teriflunomide 14 mg PO daily (ARR at 96 wk; rate ratio)",
                "Annualized relapse rate at 96 wk (primary, ublituximab vs teriflunomide; ULTIMATE I)",
                "https://www.nejm.org/doi/full/10.1056/NEJMoa2201904",
                "https://clinicaltrials.gov/study/NCT03277261",
                "Source: Steinman L et al. NEJM 2022;387:704-714 (ULTIMATE I)."),
            trial_entry("NCT03277248", "ULTIMATE II", "36044451", 2022, 36, 272, 91, 272, 0.41, 0.27, 0.61,
                "Relapsing MS, ublituximab 450 mg IV Q6M vs teriflunomide 14 mg PO daily (ARR at 96 wk; rate ratio)",
                "Annualized relapse rate at 96 wk (primary, ublituximab vs teriflunomide; ULTIMATE II)",
                "https://www.nejm.org/doi/full/10.1056/NEJMoa2201904",
                "https://clinicaltrials.gov/study/NCT03277248",
                "Source: Steinman L et al. NEJM 2022;387:704-714 (ULTIMATE II)."),
        ]),
        "benchmarks_body": """{
            'ARR': [
                { label: 'OPERA I+II ocrelizumab vs IFN beta-1a (pooled)', citation: 'Hauser 2017', year: 2017, measure: 'RR', estimate: 0.53, lci: 0.40, uci: 0.71, k: 2, n: 1656, scope: 'Ocrelizumab vs IFN beta-1a in relapsing MS; ARR pooled across OPERA I+II at 96 wk. NEJM 2017;376:221-234.' },
                { label: 'ASCLEPIOS I+II ofatumumab vs teriflunomide (pooled)', citation: 'Hauser 2020', year: 2020, measure: 'RR', estimate: 0.45, lci: 0.36, uci: 0.57, k: 2, n: 1882, scope: 'Ofatumumab vs teriflunomide in relapsing MS; ARR at 30 mo. NEJM 2020;383:546-557.' },
                { label: 'ULTIMATE I+II ublituximab vs teriflunomide (pooled)', citation: 'Steinman 2022', year: 2022, measure: 'RR', estimate: 0.41, lci: 0.30, uci: 0.55, k: 2, n: 1094, scope: 'Ublituximab vs teriflunomide in relapsing MS; ARR at 96 wk. NEJM 2022;387:704-714.' }
            ]
        }""",
        "outcome_map_body": make_outcome_map("ARR"),
    },

    # ============ HER2_LOW_ADC_NMA ============
    "HER2_LOW_ADC_NMA_REVIEW.html": {
        "source": "ADC_HER2_LOW_NMA_REVIEW.html",
        "title": "RapidMeta Onco | HER2-Low Metastatic BC ADCs — NMA (T-DXd / Dato-DXd / Sacituzumab) v1.0",
        "nct_ids": ["NCT03734029", "NCT04494425", "NCT04546009", "NCT05374512"],
        "acronyms": {
            "NCT03734029": "DESTINY-Breast04", "NCT04494425": "DESTINY-Breast06",
            "NCT04546009": "TROPiCS-02", "NCT05374512": "TROPION-Breast01",
        },
        "realData_body": trials_block([
            trial_entry("NCT03734029", "DESTINY-Breast04", "35665782", 2022, 172, 373, 130, 184, 0.50, 0.40, 0.63,
                "HER2-low metastatic BC post-chemo (1-2 prior lines), T-DXd 5.4 mg/kg Q3W vs physician-choice chemo (PFS HR)",
                "Progression-free survival (primary, T-DXd vs TPC; HER2-low metastatic BC post-chemo)",
                "https://www.nejm.org/doi/full/10.1056/NEJMoa2203690",
                "https://clinicaltrials.gov/study/NCT03734029",
                "Source: Modi S et al. NEJM 2022;387:9-20 (DESTINY-Breast04)."),
            trial_entry("NCT04494425", "DESTINY-Breast06", "39282896", 2024, 224, 436, 236, 430, 0.62, 0.51, 0.74,
                "HR+ HER2-low/ultralow metastatic BC post-endocrine, T-DXd vs physician-choice chemo (PFS HR)",
                "Progression-free survival (primary, T-DXd vs TPC; HR+ HER2-low/ultralow post-ET)",
                "https://www.nejm.org/doi/full/10.1056/NEJMoa2402836",
                "https://clinicaltrials.gov/study/NCT04494425",
                "Source: Curigliano G et al. NEJM 2024;391:2289-2301 (DESTINY-Breast06)."),
            trial_entry("NCT03901339", "TROPiCS-02", "37499200", 2023, 196, 272, 218, 271, 0.66, 0.53, 0.83,
                "HR+ HER2-/HER2-low metastatic BC post-endocrine and 2-4 prior chemo lines, sacituzumab govitecan vs physician-choice chemo (PFS HR)",
                "Progression-free survival (primary, SG vs TPC in HR+ HER2- mBC heavily pretreated)",
                "https://www.thelancet.com/journals/lancet/article/PIIS0140-6736(23)01245-X/fulltext",
                "https://clinicaltrials.gov/study/NCT03901339",
                "Source: Rugo HS et al. Lancet 2023;402:1423-1433 (TROPiCS-02)."),
            trial_entry("NCT05374512", "TROPION-Breast01", "39226544", 2024, 188, 365, 232, 367, 0.63, 0.52, 0.76,
                "HR+ HER2-/HER2-low metastatic BC post-endocrine + chemo, datopotamab deruxtecan (Dato-DXd) vs physician-choice chemo (PFS HR)",
                "Progression-free survival (primary, Dato-DXd vs TPC in HR+ HER2- mBC)",
                "https://ascopubs.org/doi/10.1200/JCO.24.00800",
                "https://clinicaltrials.gov/study/NCT05374512",
                "Source: Bardia A et al. JCO 2024;42:3856-3866 (TROPION-Breast01)."),
        ]),
        "benchmarks_body": """{
            'PFS': [
                { label: 'DESTINY-Breast04 T-DXd vs TPC (HER2-low post-chemo)', citation: 'Modi 2022', year: 2022, measure: 'HR', estimate: 0.50, lci: 0.40, uci: 0.63, k: 1, n: 557, scope: 'T-DXd vs physician-choice chemo in HER2-low metastatic BC post-chemo (1-2 prior lines); PFS. NEJM 2022;387:9-20.' },
                { label: 'DESTINY-Breast06 T-DXd vs TPC (HR+ HER2-low/ultralow)', citation: 'Curigliano 2024', year: 2024, measure: 'HR', estimate: 0.62, lci: 0.51, uci: 0.74, k: 1, n: 866, scope: 'T-DXd vs TPC in HR+ HER2-low/ultralow metastatic BC post-endocrine; PFS. NEJM 2024;391:2289-2301.' },
                { label: 'TROPiCS-02 sacituzumab govitecan vs TPC', citation: 'Rugo 2023', year: 2023, measure: 'HR', estimate: 0.66, lci: 0.53, uci: 0.83, k: 1, n: 543, scope: 'Sacituzumab govitecan vs TPC in HR+ HER2- mBC heavily pretreated; PFS. Lancet 2023;402:1423-1433.' },
                { label: 'TROPION-Breast01 Dato-DXd vs TPC', citation: 'Bardia 2024', year: 2024, measure: 'HR', estimate: 0.63, lci: 0.52, uci: 0.76, k: 1, n: 732, scope: 'Datopotamab deruxtecan vs TPC in HR+ HER2- mBC post-endocrine + chemo; PFS. JCO 2024;42:3856-3866.' }
            ]
        }""",
        "outcome_map_body": make_outcome_map("PFS"),
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
    print(f"\nTier 2 batch A: {ok} ok / {fail} fail")


if __name__ == "__main__":
    main()
