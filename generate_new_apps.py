#!/usr/bin/env python
"""
Generate 8 new RapidMeta cardiology HTML apps by cloning BEMPEDOIC_ACID_REVIEW.html
and replacing trial data, metadata, and drug-specific references.
"""

import re
import os

TEMPLATE_PATH = r"C:\Users\user\Downloads\Finrenone\BEMPEDOIC_ACID_REVIEW.html"
OUTPUT_DIR = r"C:\Users\user\Downloads\Finrenone"


# ═══════════════════════════════════════════════════════════════
# APP DEFINITIONS
# ═══════════════════════════════════════════════════════════════

APPS = [
    # ── 1. SGLT2 in CKD ──
    {
        "filename": "SGLT2_CKD_REVIEW.html",
        "title_short": "SGLT2 Inhibitors in CKD",
        "title_long": "SGLT2 Inhibitors for Kidney Outcomes in Chronic Kidney Disease: A Living Systematic Review and Meta-Analysis of Randomized Controlled Trials",
        "drug_name": "SGLT2 Inhibitors",
        "drug_name_lower": "sglt2 inhibitors",
        "drug_regex_pattern": r"\bsglt2\s*inhibitor|dapagliflozin|canagliflozin|empagliflozin\b",
        "drug_class": "SGLT2 Inhibitor",
        "va_heading": "SGLT2 Inhibitors in Chronic Kidney Disease",
        "nyt_heading": "The SGLT2 Inhibitor Evidence in CKD",
        "storage_key": "sglt2_ckd",
        "protocol": {
            "pop": "Adults with CKD (eGFR 20-75 mL/min/1.73m2)",
            "int": "SGLT2 Inhibitors (Canagliflozin, Dapagliflozin, Empagliflozin)",
            "comp": "Placebo",
            "out": "Kidney Composite (40% eGFR Decline, ESKD, Renal/CV Death)",
            "subgroup": "Drug (Canagliflozin vs Dapagliflozin vs Empagliflozin), Baseline eGFR, Diabetes status",
            "secondary": "All-cause mortality; cardiovascular death; ESKD; eGFR slope; HF hospitalization",
        },
        "search_term": "sglt2 inhibitor",
        "search_term_ctgov": "sglt2 inhibitor AND chronic kidney disease",
        "effect_measure": "HR",
        "effect_measure_buttons": "HR",  # default buttons
        "population_desc": "Adults with CKD (eGFR 20-75), with or without diabetes",
        "eligibility_intervention": "SGLT2 Inhibitor (any approved agent) as primary experimental drug",
        "eligibility_intervention_exclude": "SGLT2 inhibitor as concomitant/background only; T2DM-only CVOT trials",
        "eligibility_participants": "Adults >=18 years with CKD stages 3-4 (eGFR 20-75)",
        "nct_acronyms": {"NCT02065791": "CREDENCE", "NCT03036150": "DAPA-CKD", "NCT03594110": "EMPA-KIDNEY"},
        "auto_include_ids": ["NCT02065791", "NCT03036150", "NCT03594110"],
        "known_trial_aliases": {
            "NCT02065791": ["credence"],
            "NCT03036150": ["dapa-ckd", "dapa ckd"],
            "NCT03594110": ["empa-kidney", "empa kidney"],
        },
        "trials": {
            "NCT02065791": {
                "name": "CREDENCE", "phase": "III", "year": 2019,
                "tE": 245, "tN": 2202, "cE": 340, "cN": 2199, "group": "CKD+T2DM",
                "publishedHR": 0.70, "hrLCI": 0.59, "hrUCI": 0.82,
                "baseline": {"n": 4401, "age": 63.0, "female": 33.9, "dm": 100.0, "egfr": 56.2},
                "allOutcomes": [
                    {"shortLabel": "KidneyComp", "title": "Kidney composite (doubling SCr, ESKD, renal/CV death)", "tE": 245, "cE": 340, "type": "PRIMARY", "pubHR": 0.70, "pubHR_LCI": 0.59, "pubHR_UCI": 0.82},
                    {"shortLabel": "ACM", "title": "All-cause mortality", "tE": 168, "cE": 201, "type": "SECONDARY", "pubHR": 0.83, "pubHR_LCI": 0.68, "pubHR_UCI": 1.02},
                    {"shortLabel": "CVD", "title": "Cardiovascular death", "tE": 110, "cE": 140, "type": "SECONDARY", "pubHR": 0.78, "pubHR_LCI": 0.61, "pubHR_UCI": 1.00},
                ],
                "rob": ["low", "low", "low", "low", "low"],
                "snippet": "N Engl J Med 2019; 380:2295-2306",
                "sourceUrl": "https://www.nejm.org/doi/full/10.1056/NEJMoa1811744",
                "evidence": [
                    {"label": "Primary Kidney Composite", "source": "NEJM 2019; 380:2295-2306 (Table 2)", "text": "The primary outcome occurred in 245 of 2202 (11.1%) in the canagliflozin group vs 340 of 2199 (15.5%) in the placebo group (HR 0.70; 95% CI, 0.59 to 0.82; P=0.00001).", "highlights": ["245", "2202", "340", "2199", "0.70"], "sourceUrl": "https://www.nejm.org/doi/full/10.1056/NEJMoa1811744"},
                ],
            },
            "NCT03036150": {
                "name": "DAPA-CKD", "phase": "III", "year": 2020,
                "tE": 197, "tN": 2152, "cE": 312, "cN": 2152, "group": "CKD+/-DM",
                "publishedHR": 0.61, "hrLCI": 0.51, "hrUCI": 0.72,
                "baseline": {"n": 4304, "age": 61.8, "female": 33.1, "dm": 67.5, "egfr": 43.1},
                "allOutcomes": [
                    {"shortLabel": "KidneyComp", "title": "Kidney composite (>=50% eGFR decline, ESKD, renal/CV death)", "tE": 197, "cE": 312, "type": "PRIMARY", "pubHR": 0.61, "pubHR_LCI": 0.51, "pubHR_UCI": 0.72},
                    {"shortLabel": "ACM", "title": "All-cause mortality", "tE": 101, "cE": 146, "type": "SECONDARY", "pubHR": 0.69, "pubHR_LCI": 0.53, "pubHR_UCI": 0.88},
                ],
                "rob": ["low", "low", "low", "low", "low"],
                "snippet": "N Engl J Med 2020; 383:1436-1446",
                "sourceUrl": "https://www.nejm.org/doi/full/10.1056/NEJMoa2024816",
                "evidence": [
                    {"label": "Primary Kidney Composite", "source": "NEJM 2020; 383:1436-1446", "text": "A primary outcome event occurred in 197 participants (9.2%) in the dapagliflozin group and 312 (14.5%) in the placebo group (HR 0.61; 95% CI, 0.51 to 0.72; P<0.001).", "highlights": ["197", "2152", "312", "2152", "0.61"], "sourceUrl": "https://www.nejm.org/doi/full/10.1056/NEJMoa2024816"},
                ],
            },
            "NCT03594110": {
                "name": "EMPA-KIDNEY", "phase": "III", "year": 2023,
                "tE": 432, "tN": 3304, "cE": 558, "cN": 3305, "group": "CKD broad",
                "publishedHR": 0.72, "hrLCI": 0.64, "hrUCI": 0.82,
                "baseline": {"n": 6609, "age": 63.8, "female": 33.0, "dm": 46.0, "egfr": 37.3},
                "allOutcomes": [
                    {"shortLabel": "KidneyComp", "title": "Kidney disease progression or CV death", "tE": 432, "cE": 558, "type": "PRIMARY", "pubHR": 0.72, "pubHR_LCI": 0.64, "pubHR_UCI": 0.82},
                    {"shortLabel": "ACM", "title": "All-cause mortality", "tE": 312, "cE": 349, "type": "SECONDARY", "pubHR": 0.87, "pubHR_LCI": 0.75, "pubHR_UCI": 1.02},
                ],
                "rob": ["low", "low", "low", "low", "low"],
                "snippet": "N Engl J Med 2023; 388:117-127",
                "sourceUrl": "https://www.nejm.org/doi/full/10.1056/NEJMoa2204233",
                "evidence": [
                    {"label": "Primary Composite", "source": "NEJM 2023; 388:117-127", "text": "Kidney disease progression or death from cardiovascular causes occurred in 432 of 3304 (13.1%) in the empagliflozin group and 558 of 3305 (16.9%) in the placebo group (HR 0.72; 95% CI, 0.64 to 0.82; P<0.001).", "highlights": ["432", "3304", "558", "3305", "0.72"], "sourceUrl": "https://www.nejm.org/doi/full/10.1056/NEJMoa2204233"},
                ],
            },
        },
        "benchmarks": {
            "KidneyComp": [
                {"label": "Nuffield Dept meta-analysis", "citation": "Nuffield 2022", "year": 2022, "measure": "HR", "estimate": 0.63, "lci": 0.56, "uci": 0.71, "k": 13, "n": 90413, "scope": "SGLT2i kidney outcomes across all populations"},
            ],
        },
        "ctgov_registry": {},
        "nma_ids": ["NCT02065791", "NCT03036150", "NCT03594110"],
        "nma_label": "SGLT2 Inhibitors vs Placebo",
        "nma_indirect_label": "SGLT2i vs GLP-1 RA (Indirect)",
    },

    # ── 2. ARNI in HF ──
    {
        "filename": "ARNI_HF_REVIEW.html",
        "title_short": "Sacubitril/Valsartan (ARNI) in HF",
        "title_long": "Sacubitril/Valsartan for Heart Failure: A Living Systematic Review and Meta-Analysis of Randomized Controlled Trials",
        "drug_name": "Sacubitril/Valsartan",
        "drug_name_lower": "sacubitril/valsartan",
        "drug_regex_pattern": r"\bsacubitril|valsartan|arni|entresto\b",
        "drug_class": "ARNI",
        "va_heading": "Sacubitril/Valsartan in Heart Failure",
        "nyt_heading": "The Sacubitril/Valsartan Evidence",
        "storage_key": "arni_hf",
        "protocol": {
            "pop": "Adults with Heart Failure (HFrEF, HFpEF, or post-MI)",
            "int": "Sacubitril/Valsartan (ARNI)",
            "comp": "RAAS Inhibitor (Enalapril or Valsartan)",
            "out": "CV Death or HF Hospitalization",
            "subgroup": "HF phenotype (HFrEF vs HFpEF vs post-MI), LVEF, Baseline NT-proBNP",
            "secondary": "All-cause mortality; CV death; HF hospitalization; renal composite; quality of life",
        },
        "search_term": "sacubitril valsartan",
        "search_term_ctgov": "sacubitril AND valsartan",
        "effect_measure": "HR",
        "effect_measure_buttons": "HR",
        "population_desc": "Adults with heart failure across the EF spectrum",
        "eligibility_intervention": "Sacubitril/Valsartan (any dose) as primary experimental drug",
        "eligibility_intervention_exclude": "Sacubitril/valsartan as background only; open-label extensions without comparator",
        "eligibility_participants": "Adults >=18 years with HFrEF, HFpEF, or recent MI with LV dysfunction",
        "nct_acronyms": {"NCT01035255": "PARADIGM-HF", "NCT01920711": "PARAGON-HF", "NCT02924727": "PARADISE-MI", "NCT03988634": "PARAGLIDE-HF"},
        "auto_include_ids": ["NCT01035255", "NCT01920711", "NCT02924727"],
        "known_trial_aliases": {
            "NCT01035255": ["paradigm-hf", "paradigm"],
            "NCT01920711": ["paragon-hf", "paragon"],
            "NCT02924727": ["paradise-mi", "paradise"],
            "NCT03988634": ["paraglide-hf", "paraglide"],
        },
        "trials": {
            "NCT01035255": {
                "name": "PARADIGM-HF", "phase": "III", "year": 2014,
                "tE": 914, "tN": 4187, "cE": 1117, "cN": 4212, "group": "HFrEF",
                "publishedHR": 0.80, "hrLCI": 0.73, "hrUCI": 0.87,
                "baseline": {"n": 8442, "age": 63.8, "female": 21.0, "dm": 34.7, "lvef": 29.6},
                "allOutcomes": [
                    {"shortLabel": "CVD_HFH", "title": "CV death or HF hospitalization", "tE": 914, "cE": 1117, "type": "PRIMARY", "pubHR": 0.80, "pubHR_LCI": 0.73, "pubHR_UCI": 0.87},
                    {"shortLabel": "CVD", "title": "Cardiovascular death", "tE": 558, "cE": 693, "type": "SECONDARY", "pubHR": 0.80, "pubHR_LCI": 0.71, "pubHR_UCI": 0.89},
                    {"shortLabel": "ACM", "title": "All-cause mortality", "tE": 711, "cE": 835, "type": "SECONDARY", "pubHR": 0.84, "pubHR_LCI": 0.76, "pubHR_UCI": 0.93},
                ],
                "rob": ["low", "low", "low", "low", "low"],
                "snippet": "N Engl J Med 2014; 371:993-1004",
                "sourceUrl": "https://www.nejm.org/doi/full/10.1056/NEJMoa1409077",
                "evidence": [
                    {"label": "Primary CVD/HFH", "source": "NEJM 2014; 371:993-1004", "text": "The primary outcome occurred in 914 patients (21.8%) in the sacubitril-valsartan group and 1117 (26.5%) in the enalapril group (HR 0.80; 95% CI, 0.73 to 0.87; P<0.001).", "highlights": ["914", "4187", "1117", "4212", "0.80"], "sourceUrl": "https://www.nejm.org/doi/full/10.1056/NEJMoa1409077"},
                ],
            },
            "NCT01920711": {
                "name": "PARAGON-HF", "phase": "III", "year": 2019,
                "tE": 526, "tN": 2407, "cE": 557, "cN": 2389, "group": "HFpEF",
                "publishedHR": 0.87, "hrLCI": 0.75, "hrUCI": 1.01,
                "baseline": {"n": 4822, "age": 73.0, "female": 51.6, "dm": 43.2, "lvef": 57.0},
                "allOutcomes": [
                    {"shortLabel": "CVD_HFH", "title": "CV death or total HF hospitalizations", "tE": 526, "cE": 557, "type": "PRIMARY", "pubHR": 0.87, "pubHR_LCI": 0.75, "pubHR_UCI": 1.01},
                    {"shortLabel": "ACM", "title": "All-cause mortality", "tE": 244, "cE": 263, "type": "SECONDARY", "pubHR": 0.97, "pubHR_LCI": 0.81, "pubHR_UCI": 1.16},
                ],
                "rob": ["low", "low", "low", "low", "low"],
                "snippet": "N Engl J Med 2019; 381:1609-1620",
                "sourceUrl": "https://www.nejm.org/doi/full/10.1056/NEJMoa1901907",
                "evidence": [
                    {"label": "Primary CVD/HFH", "source": "NEJM 2019; 381:1609-1620", "text": "Total primary events were 894 in the sacubitril-valsartan group and 1009 in the valsartan group (rate ratio 0.87; 95% CI, 0.75 to 1.01; P=0.06).", "highlights": ["526", "2407", "557", "2389", "0.87"], "sourceUrl": "https://www.nejm.org/doi/full/10.1056/NEJMoa1901907"},
                ],
            },
            "NCT02924727": {
                "name": "PARADISE-MI", "phase": "III", "year": 2021,
                "tE": 338, "tN": 2830, "cE": 373, "cN": 2831, "group": "Post-MI",
                "publishedHR": 0.90, "hrLCI": 0.78, "hrUCI": 1.04,
                "baseline": {"n": 5669, "age": 63.4, "female": 24.0, "dm": 31.5, "lvef": 37.0},
                "allOutcomes": [
                    {"shortLabel": "CVD_HFH", "title": "CV death or HF events", "tE": 338, "cE": 373, "type": "PRIMARY", "pubHR": 0.90, "pubHR_LCI": 0.78, "pubHR_UCI": 1.04},
                    {"shortLabel": "ACM", "title": "All-cause mortality", "tE": 191, "cE": 205, "type": "SECONDARY", "pubHR": 0.93, "pubHR_LCI": 0.76, "pubHR_UCI": 1.13},
                ],
                "rob": ["low", "low", "low", "low", "low"],
                "snippet": "N Engl J Med 2021; 385:1845-1855",
                "sourceUrl": "https://www.nejm.org/doi/full/10.1056/NEJMoa2104508",
                "evidence": [
                    {"label": "Primary CVD/HF", "source": "NEJM 2021; 385:1845-1855", "text": "The primary outcome occurred in 338 patients (11.9%) in the sacubitril-valsartan group and 373 (13.2%) in the ramipril group (HR 0.90; 95% CI, 0.78 to 1.04; P=0.17).", "highlights": ["338", "2830", "373", "2831", "0.90"], "sourceUrl": "https://www.nejm.org/doi/full/10.1056/NEJMoa2104508"},
                ],
            },
            "NCT03988634": {
                "name": "PARAGLIDE-HF", "phase": "III", "year": 2023,
                "tE": None, "tN": 233, "cE": None, "cN": 233, "group": "Decompensated HFpEF",
                "publishedHR": None, "hrLCI": None, "hrUCI": None,
                "baseline": {"n": 466, "age": 73.0, "female": 52.0, "dm": 55.0, "lvef": 55.0},
                "allOutcomes": [
                    {"shortLabel": "NTproBNP", "title": "NT-proBNP change (time-averaged AUC)", "md": -223, "se": 85, "type": "CONTINUOUS"},
                ],
                "rob": ["low", "low", "some", "low", "low"],
                "snippet": "JAMA 2023; 329(12):990-1002",
                "sourceUrl": "https://jamanetwork.com/journals/jama/fullarticle/2802730",
                "evidence": [
                    {"label": "NT-proBNP", "source": "JAMA 2023; 329(12):990-1002", "text": "Sacubitril-valsartan resulted in a greater time-averaged reduction in NT-proBNP than valsartan (ratio of change 0.85; 95% CI, 0.74 to 0.98).", "highlights": ["0.85", "466"], "sourceUrl": "https://jamanetwork.com/journals/jama/fullarticle/2802730"},
                ],
                "_supplementary": True,
            },
        },
        "benchmarks": {},
        "ctgov_registry": {},
        "nma_ids": ["NCT01035255", "NCT01920711", "NCT02924727"],
        "nma_label": "Sacubitril/Valsartan vs RAAS Inhibitor",
        "nma_indirect_label": "ARNI vs Other HF Therapies (Indirect)",
    },

    # ── 3. Ablation for AF ──
    {
        "filename": "ABLATION_AF_REVIEW.html",
        "title_short": "Catheter Ablation for AF",
        "title_long": "Catheter Ablation for Atrial Fibrillation: A Living Systematic Review and Meta-Analysis of Randomized Controlled Trials",
        "drug_name": "Catheter Ablation",
        "drug_name_lower": "catheter ablation",
        "drug_regex_pattern": r"\bcatheter ablation|pulmonary vein isolation|pvi|rhythm control\b",
        "drug_class": "Ablation",
        "va_heading": "Catheter Ablation in Atrial Fibrillation",
        "nyt_heading": "The Catheter Ablation Evidence in AF",
        "storage_key": "ablation_af",
        "protocol": {
            "pop": "Adults with Atrial Fibrillation (paroxysmal or persistent)",
            "int": "Catheter Ablation (PVI-based strategies)",
            "comp": "Medical Therapy or Rate Control",
            "out": "Composite CV Death, Stroke, or HF Hospitalization",
            "subgroup": "AF type (paroxysmal vs persistent), HF status, Follow-up duration",
            "secondary": "All-cause mortality; stroke/TIA; AF recurrence; quality of life",
        },
        "search_term": "catheter ablation atrial fibrillation",
        "search_term_ctgov": "catheter ablation AND atrial fibrillation",
        "effect_measure": "HR",
        "effect_measure_buttons": "HR",
        "population_desc": "Adults with AF, with or without heart failure",
        "eligibility_intervention": "Catheter ablation (radiofrequency or cryoballoon PVI) as primary intervention",
        "eligibility_intervention_exclude": "Surgical ablation (MAZE); ablation as concomitant to cardiac surgery",
        "eligibility_participants": "Adults >=18 years with documented atrial fibrillation",
        "nct_acronyms": {"NCT00643188": "CASTLE-AF", "NCT00911508": "CABANA", "NCT01288352": "EAST-AFNET 4", "NCT01420393": "RAFT-AF"},
        "auto_include_ids": ["NCT00643188", "NCT00911508", "NCT01288352", "NCT01420393"],
        "known_trial_aliases": {
            "NCT00643188": ["castle-af", "castle"],
            "NCT00911508": ["cabana"],
            "NCT01288352": ["east-afnet", "east afnet 4"],
            "NCT01420393": ["raft-af", "raft af"],
        },
        "trials": {
            "NCT00643188": {
                "name": "CASTLE-AF", "phase": "III", "year": 2018,
                "tE": 51, "tN": 179, "cE": 82, "cN": 184, "group": "AF+HF",
                "publishedHR": 0.62, "hrLCI": 0.43, "hrUCI": 0.87,
                "baseline": {"n": 363, "age": 64.0, "female": 14.0, "dm": 32.0, "lvef": 32.0},
                "allOutcomes": [
                    {"shortLabel": "CVD_HFH", "title": "All-cause death or HF hospitalization", "tE": 51, "cE": 82, "type": "PRIMARY", "pubHR": 0.62, "pubHR_LCI": 0.43, "pubHR_UCI": 0.87},
                    {"shortLabel": "ACM", "title": "All-cause mortality", "tE": 24, "cE": 46, "type": "SECONDARY", "pubHR": 0.53, "pubHR_LCI": 0.32, "pubHR_UCI": 0.86},
                ],
                "rob": ["low", "some", "low", "low", "low"],
                "snippet": "N Engl J Med 2018; 378:417-427",
                "sourceUrl": "https://www.nejm.org/doi/full/10.1056/NEJMoa1707855",
                "evidence": [
                    {"label": "Primary Death/HFH", "source": "NEJM 2018; 378:417-427", "text": "The primary end point occurred in 51 of 179 patients (28.5%) in the ablation group and in 82 of 184 (44.6%) in the medical-therapy group (HR 0.62; 95% CI, 0.43 to 0.87).", "highlights": ["51", "179", "82", "184", "0.62"], "sourceUrl": "https://www.nejm.org/doi/full/10.1056/NEJMoa1707855"},
                ],
            },
            "NCT00911508": {
                "name": "CABANA", "phase": "III", "year": 2019,
                "tE": 89, "tN": 1108, "cE": 101, "cN": 1096, "group": "General AF",
                "publishedHR": 0.86, "hrLCI": 0.65, "hrUCI": 1.13,
                "baseline": {"n": 2204, "age": 67.5, "female": 37.0, "dm": 25.0, "lvef": 58.0},
                "allOutcomes": [
                    {"shortLabel": "Composite", "title": "Death, disabling stroke, serious bleeding, or cardiac arrest", "tE": 89, "cE": 101, "type": "PRIMARY", "pubHR": 0.86, "pubHR_LCI": 0.65, "pubHR_UCI": 1.13},
                    {"shortLabel": "ACM", "title": "All-cause mortality", "tE": 58, "cE": 67, "type": "SECONDARY", "pubHR": 0.85, "pubHR_LCI": 0.60, "pubHR_UCI": 1.21},
                ],
                "rob": ["low", "some", "low", "low", "low"],
                "snippet": "JAMA 2019; 321(13):1261-1274",
                "sourceUrl": "https://jamanetwork.com/journals/jama/fullarticle/2728676",
                "evidence": [
                    {"label": "Primary Composite", "source": "JAMA 2019; 321(13):1261-1274", "text": "The primary composite end point occurred in 89 patients (8.0%) randomized to ablation and 101 (9.2%) to drug therapy (HR 0.86; 95% CI, 0.65 to 1.13; P=0.30).", "highlights": ["89", "1108", "101", "1096", "0.86"], "sourceUrl": "https://jamanetwork.com/journals/jama/fullarticle/2728676"},
                ],
            },
            "NCT01288352": {
                "name": "EAST-AFNET 4", "phase": "III", "year": 2020,
                "tE": 249, "tN": 1395, "cE": 316, "cN": 1394, "group": "Early rhythm control",
                "publishedHR": 0.79, "hrLCI": 0.66, "hrUCI": 0.94,
                "baseline": {"n": 2789, "age": 70.5, "female": 45.8, "dm": 30.0, "lvef": 58.0},
                "allOutcomes": [
                    {"shortLabel": "CVD_Stroke_HFH", "title": "CV death, stroke, or HF worsening", "tE": 249, "cE": 316, "type": "PRIMARY", "pubHR": 0.79, "pubHR_LCI": 0.66, "pubHR_UCI": 0.94},
                    {"shortLabel": "ACM", "title": "All-cause mortality", "tE": 138, "cE": 164, "type": "SECONDARY", "pubHR": 0.84, "pubHR_LCI": 0.67, "pubHR_UCI": 1.07},
                ],
                "rob": ["low", "some", "low", "low", "low"],
                "snippet": "N Engl J Med 2020; 383:1305-1316",
                "sourceUrl": "https://www.nejm.org/doi/full/10.1056/NEJMoa2019422",
                "evidence": [
                    {"label": "Primary Composite", "source": "NEJM 2020; 383:1305-1316", "text": "A primary-outcome event occurred in 249 of 1395 patients (3.9%/year) in early rhythm control and 316 of 1394 (5.0%/year) in usual care (HR 0.79; 96% CI, 0.66 to 0.94; P=0.005).", "highlights": ["249", "1395", "316", "1394", "0.79"], "sourceUrl": "https://www.nejm.org/doi/full/10.1056/NEJMoa2019422"},
                ],
            },
            "NCT01420393": {
                "name": "RAFT-AF", "phase": "III", "year": 2022,
                "tE": 44, "tN": 214, "cE": 55, "cN": 197, "group": "AF+HF",
                "publishedHR": 0.71, "hrLCI": 0.49, "hrUCI": 1.03,
                "baseline": {"n": 411, "age": 65.0, "female": 20.0, "dm": 26.0, "lvef": 35.0},
                "allOutcomes": [
                    {"shortLabel": "ACM_HFH", "title": "All-cause mortality or HF hospitalization", "tE": 44, "cE": 55, "type": "PRIMARY", "pubHR": 0.71, "pubHR_LCI": 0.49, "pubHR_UCI": 1.03},
                    {"shortLabel": "ACM", "title": "All-cause mortality", "tE": 18, "cE": 25, "type": "SECONDARY", "pubHR": 0.64, "pubHR_LCI": 0.34, "pubHR_UCI": 1.20},
                ],
                "rob": ["low", "some", "low", "low", "low"],
                "snippet": "N Engl J Med 2022; 388:1-11",
                "sourceUrl": "https://www.nejm.org/doi/full/10.1056/NEJMoa2204164",
                "evidence": [
                    {"label": "Primary ACM/HFH", "source": "NEJM 2022; 388:1-11", "text": "The primary outcome occurred in 44 (20.5%) in the ablation group and 55 (27.8%) in the rate-control group (HR 0.71; 95% CI, 0.49 to 1.03; P=0.066).", "highlights": ["44", "214", "55", "197", "0.71"], "sourceUrl": "https://www.nejm.org/doi/full/10.1056/NEJMoa2204164"},
                ],
            },
        },
        "benchmarks": {},
        "ctgov_registry": {},
        "nma_ids": ["NCT00643188", "NCT00911508", "NCT01288352", "NCT01420393"],
        "nma_label": "Ablation vs Medical Therapy",
        "nma_indirect_label": "Ablation vs Surgical MAZE (Indirect)",
    },

    # ── 4. IV Iron in HF ──
    {
        "filename": "IV_IRON_HF_REVIEW.html",
        "title_short": "IV Iron in Heart Failure",
        "title_long": "Intravenous Iron Therapy for Heart Failure with Iron Deficiency: A Living Systematic Review and Meta-Analysis of Randomized Controlled Trials",
        "drug_name": "IV Iron",
        "drug_name_lower": "iv iron",
        "drug_regex_pattern": r"\bferric carboxymaltose|ferric derisomaltose|iv iron|intravenous iron\b",
        "drug_class": "IV Iron Supplementation",
        "va_heading": "IV Iron Therapy in Heart Failure",
        "nyt_heading": "The IV Iron Evidence in Heart Failure",
        "storage_key": "iv_iron_hf",
        "protocol": {
            "pop": "Adults with Heart Failure and Iron Deficiency",
            "int": "IV Iron (Ferric Carboxymaltose or Ferric Derisomaltose)",
            "comp": "Placebo or Standard of Care",
            "out": "CV Death or HF Hospitalization",
            "subgroup": "Iron formulation (FCM vs FDI), Acute vs Chronic HF, Baseline ferritin",
            "secondary": "All-cause mortality; HF hospitalization; 6-minute walk distance; quality of life",
        },
        "search_term": "ferric carboxymaltose heart failure",
        "search_term_ctgov": "intravenous iron AND heart failure",
        "effect_measure": "HR",
        "effect_measure_buttons": "HR",
        "population_desc": "Adults with HF and confirmed iron deficiency",
        "eligibility_intervention": "IV Iron (ferric carboxymaltose or derisomaltose) as primary experimental drug",
        "eligibility_intervention_exclude": "Oral iron supplementation; IV iron as background only",
        "eligibility_participants": "Adults >=18 years with HF (any EF) and iron deficiency (ferritin <100 or 100-300 + TSAT<20%)",
        "nct_acronyms": {"NCT01453608": "CONFIRM-HF", "NCT02937454": "AFFIRM-AHF", "NCT02642562": "IRONMAN", "NCT03037931": "HEART-FID"},
        "auto_include_ids": ["NCT01453608", "NCT02937454", "NCT02642562", "NCT03037931"],
        "known_trial_aliases": {
            "NCT01453608": ["confirm-hf", "confirm"],
            "NCT02937454": ["affirm-ahf", "affirm"],
            "NCT02642562": ["ironman"],
            "NCT03037931": ["heart-fid", "heartfid"],
        },
        "trials": {
            "NCT01453608": {
                "name": "CONFIRM-HF", "phase": "III", "year": 2015,
                "tE": 25, "tN": 150, "cE": 36, "cN": 151, "group": "Chronic HF",
                "publishedHR": 0.69, "hrLCI": 0.41, "hrUCI": 1.17,
                "baseline": {"n": 304, "age": 68.8, "female": 45.0, "dm": 41.0, "lvef": 37.0},
                "allOutcomes": [
                    {"shortLabel": "CVD_HFH", "title": "CV death or HF hospitalization", "tE": 25, "cE": 36, "type": "SECONDARY", "pubHR": 0.69, "pubHR_LCI": 0.41, "pubHR_UCI": 1.17},
                ],
                "rob": ["low", "low", "low", "low", "low"],
                "snippet": "Eur Heart J 2015; 36(11):657-668",
                "sourceUrl": "https://academic.oup.com/eurheartj/article/36/11/657/2293315",
                "evidence": [
                    {"label": "CVD/HFH Secondary", "source": "Eur Heart J 2015; 36:657-668", "text": "CV death or worsening HF occurred in 25 (16.7%) FCM vs 36 (24.2%) placebo patients (HR 0.69; 95% CI, 0.41 to 1.17).", "highlights": ["25", "150", "36", "151", "0.69"], "sourceUrl": "https://academic.oup.com/eurheartj/article/36/11/657/2293315"},
                ],
            },
            "NCT02937454": {
                "name": "AFFIRM-AHF", "phase": "III", "year": 2021,
                "tE": 293, "tN": 558, "cE": 372, "cN": 550, "group": "Acute HF",
                "publishedHR": 0.79, "hrLCI": 0.62, "hrUCI": 1.01,
                "baseline": {"n": 1132, "age": 71.0, "female": 46.0, "dm": 42.0, "lvef": 33.0},
                "allOutcomes": [
                    {"shortLabel": "CVD_HFH", "title": "Total HF hospitalizations and CV death", "tE": 293, "cE": 372, "type": "PRIMARY", "pubHR": 0.79, "pubHR_LCI": 0.62, "pubHR_UCI": 1.01},
                    {"shortLabel": "ACM", "title": "All-cause mortality", "tE": 65, "cE": 74, "type": "SECONDARY", "pubHR": 0.84, "pubHR_LCI": 0.60, "pubHR_UCI": 1.18},
                ],
                "rob": ["low", "low", "low", "low", "low"],
                "snippet": "Lancet 2021; 396(10266):1895-1904",
                "sourceUrl": "https://www.thelancet.com/journals/lancet/article/PIIS0140-6736(20)32339-4/fulltext",
                "evidence": [
                    {"label": "Primary HFH/CVD", "source": "Lancet 2021; 396:1895-1904", "text": "The primary endpoint events totalled 293 (rate ratio 0.79; 95% CI, 0.62 to 1.01; P=0.059) in the FCM group and 372 in the placebo group.", "highlights": ["293", "558", "372", "550", "0.79"], "sourceUrl": "https://www.thelancet.com/journals/lancet/article/PIIS0140-6736(20)32339-4/fulltext"},
                ],
            },
            "NCT02642562": {
                "name": "IRONMAN", "phase": "III", "year": 2022,
                "tE": 336, "tN": 569, "cE": 411, "cN": 568, "group": "Chronic HF",
                "publishedHR": 0.82, "hrLCI": 0.66, "hrUCI": 1.02,
                "baseline": {"n": 1137, "age": 73.0, "female": 26.0, "dm": 36.0, "lvef": 30.0},
                "allOutcomes": [
                    {"shortLabel": "CVD_HFH", "title": "HF hospitalization or CV death", "tE": 336, "cE": 411, "type": "PRIMARY", "pubHR": 0.82, "pubHR_LCI": 0.66, "pubHR_UCI": 1.02},
                    {"shortLabel": "ACM", "title": "All-cause mortality", "tE": 166, "cE": 180, "type": "SECONDARY", "pubHR": 0.93, "pubHR_LCI": 0.75, "pubHR_UCI": 1.15},
                ],
                "rob": ["low", "some", "low", "low", "low"],
                "snippet": "Lancet 2022; 400(10369):2199-2209",
                "sourceUrl": "https://www.thelancet.com/journals/lancet/article/PIIS0140-6736(22)02083-9/fulltext",
                "evidence": [
                    {"label": "Primary HFH/CVD", "source": "Lancet 2022; 400:2199-2209", "text": "The primary endpoint occurred in 336 FDI (22.4/100 patient-years) vs 411 usual care (27.5/100 patient-years) (rate ratio 0.82; 95% CI, 0.66 to 1.02; P=0.070).", "highlights": ["336", "569", "411", "568", "0.82"], "sourceUrl": "https://www.thelancet.com/journals/lancet/article/PIIS0140-6736(22)02083-9/fulltext"},
                ],
            },
            "NCT03037931": {
                "name": "HEART-FID", "phase": "III", "year": 2023,
                "tE": 560, "tN": 1532, "cE": 581, "cN": 1533, "group": "Chronic HF",
                "publishedHR": 0.93, "hrLCI": 0.81, "hrUCI": 1.06,
                "baseline": {"n": 3065, "age": 68.0, "female": 36.0, "dm": 46.0, "lvef": 30.0},
                "allOutcomes": [
                    {"shortLabel": "HierComp", "title": "Hierarchical composite (death, HF hosp, 6MWD)", "tE": 560, "cE": 581, "type": "PRIMARY", "pubHR": 0.93, "pubHR_LCI": 0.81, "pubHR_UCI": 1.06},
                    {"shortLabel": "ACM", "title": "All-cause mortality", "tE": 232, "cE": 244, "type": "SECONDARY", "pubHR": 0.95, "pubHR_LCI": 0.79, "pubHR_UCI": 1.14},
                ],
                "rob": ["low", "low", "low", "low", "low"],
                "snippet": "Lancet 2023; 402(10411):1655-1665",
                "sourceUrl": "https://www.thelancet.com/journals/lancet/article/PIIS0140-6736(23)02003-8/fulltext",
                "evidence": [
                    {"label": "Hierarchical Composite", "source": "Lancet 2023; 402:1655-1665", "text": "The hierarchical composite was not significantly different: win ratio 1.02 (99% CI, 0.87 to 1.18; P=0.78). CV death or HF hosp: HR 0.93 (95% CI, 0.81 to 1.06).", "highlights": ["560", "1532", "581", "1533", "0.93"], "sourceUrl": "https://www.thelancet.com/journals/lancet/article/PIIS0140-6736(23)02003-8/fulltext"},
                ],
            },
        },
        "benchmarks": {},
        "ctgov_registry": {},
        "nma_ids": ["NCT01453608", "NCT02937454", "NCT02642562", "NCT03037931"],
        "nma_label": "IV Iron vs Placebo/Usual Care",
        "nma_indirect_label": "FCM vs FDI (Indirect)",
    },

    # ── 5. Renal Denervation ── (MD, not HR)
    {
        "filename": "RENAL_DENERV_REVIEW.html",
        "title_short": "Renal Denervation for HTN",
        "title_long": "Renal Denervation for Resistant Hypertension: A Living Systematic Review and Meta-Analysis of Randomized Sham-Controlled Trials",
        "drug_name": "Renal Denervation",
        "drug_name_lower": "renal denervation",
        "drug_regex_pattern": r"\brenal denervation|rdn|symplicity|paradise|spyral|radiance\b",
        "drug_class": "Device (Renal Denervation)",
        "va_heading": "Renal Denervation for Resistant Hypertension",
        "nyt_heading": "The Renal Denervation Evidence",
        "storage_key": "renal_denerv",
        "protocol": {
            "pop": "Adults with Resistant or Uncontrolled Hypertension",
            "int": "Renal Denervation (Radiofrequency or Ultrasound)",
            "comp": "Sham Procedure",
            "out": "Office Systolic Blood Pressure Change (mmHg)",
            "subgroup": "RDN modality (RF vs Ultrasound), Medication status (on vs off meds), Geography",
            "secondary": "24h ambulatory SBP; office DBP; ambulatory DBP; medication burden; safety",
        },
        "search_term": "renal denervation hypertension",
        "search_term_ctgov": "renal denervation AND hypertension",
        "effect_measure": "MD",
        "effect_measure_buttons": "MD",
        "population_desc": "Adults with resistant/uncontrolled hypertension",
        "eligibility_intervention": "Renal Denervation (RF or ultrasound catheter) as primary intervention",
        "eligibility_intervention_exclude": "Non-sham-controlled designs; surgical denervation",
        "eligibility_participants": "Adults >=18 years with resistant or uncontrolled hypertension (office SBP >=140 or >=150 mmHg)",
        "nct_acronyms": {"NCT02439749": "SPYRAL HTN-ON MED", "NCT02649426": "RADIANCE-HTN SOLO", "NCT03614260": "RADIANCE II", "NCT02918305": "REQUIRE"},
        "auto_include_ids": ["NCT02439749", "NCT02649426", "NCT03614260", "NCT02918305"],
        "known_trial_aliases": {
            "NCT02439749": ["spyral htn", "spyral"],
            "NCT02649426": ["radiance-htn solo", "radiance solo"],
            "NCT03614260": ["radiance ii", "radiance 2"],
            "NCT02918305": ["require"],
        },
        "trials": {
            "NCT02439749_ON": {
                "name": "SPYRAL HTN-ON MED", "phase": "III", "year": 2018,
                "tE": None, "tN": 38, "cE": None, "cN": 42, "group": "On meds",
                "publishedHR": None, "hrLCI": None, "hrUCI": None,
                "baseline": {"n": 80, "age": 52.0, "female": 30.0, "sbp_office": 164.0},
                "allOutcomes": [
                    {"shortLabel": "OfficeSBP", "title": "Change in office SBP (mmHg)", "md": -7.0, "se": 2.5, "type": "CONTINUOUS"},
                ],
                "rob": ["low", "low", "low", "some", "low"],
                "snippet": "Lancet 2018; 391(10137):2346-2355",
                "sourceUrl": "https://www.thelancet.com/journals/lancet/article/PIIS0140-6736(18)31082-1/fulltext",
                "evidence": [
                    {"label": "Office SBP change", "source": "Lancet 2018; 391:2346-2355", "text": "RDN reduced office SBP by 7.0 mmHg vs sham at 6 months (Bayesian posterior probability of superiority >0.99).", "highlights": ["-7.0", "80"], "sourceUrl": "https://www.thelancet.com/journals/lancet/article/PIIS0140-6736(18)31082-1/fulltext"},
                ],
            },
            "NCT02649426": {
                "name": "RADIANCE-HTN SOLO", "phase": "III", "year": 2018,
                "tE": None, "tN": 74, "cE": None, "cN": 72, "group": "Off meds",
                "publishedHR": None, "hrLCI": None, "hrUCI": None,
                "baseline": {"n": 146, "age": 53.9, "female": 34.0, "sbp_office": 153.0},
                "allOutcomes": [
                    {"shortLabel": "OfficeSBP", "title": "Change in daytime ambulatory SBP (mmHg)", "md": -6.3, "se": 2.1, "type": "CONTINUOUS"},
                ],
                "rob": ["low", "low", "low", "low", "low"],
                "snippet": "Lancet 2018; 391(10137):2335-2345",
                "sourceUrl": "https://www.thelancet.com/journals/lancet/article/PIIS0140-6736(18)31084-5/fulltext",
                "evidence": [
                    {"label": "Daytime Ambulatory SBP", "source": "Lancet 2018; 391:2335-2345", "text": "Daytime ambulatory SBP was reduced by 6.3 mmHg more with ultrasound RDN vs sham (P=0.0001).", "highlights": ["-6.3", "146"], "sourceUrl": "https://www.thelancet.com/journals/lancet/article/PIIS0140-6736(18)31084-5/fulltext"},
                ],
            },
            "NCT02439749_OFF": {
                "name": "SPYRAL HTN-OFF MED", "phase": "III", "year": 2020,
                "tE": None, "tN": 166, "cE": None, "cN": 165, "group": "Off meds",
                "publishedHR": None, "hrLCI": None, "hrUCI": None,
                "baseline": {"n": 331, "age": 51.5, "female": 33.0, "sbp_office": 156.0},
                "allOutcomes": [
                    {"shortLabel": "OfficeSBP", "title": "Change in 24h ambulatory SBP (mmHg)", "md": -3.9, "se": 1.5, "type": "CONTINUOUS"},
                ],
                "rob": ["low", "low", "low", "low", "low"],
                "snippet": "Lancet 2020; 395(10234):1444-1451",
                "sourceUrl": "https://www.thelancet.com/journals/lancet/article/PIIS0140-6736(20)30554-7/fulltext",
                "evidence": [
                    {"label": "24h Ambulatory SBP", "source": "Lancet 2020; 395:1444-1451", "text": "The 24h ambulatory SBP reduction was 3.9 mmHg greater with RDN vs sham (P<0.001).", "highlights": ["-3.9", "331"], "sourceUrl": "https://www.thelancet.com/journals/lancet/article/PIIS0140-6736(20)30554-7/fulltext"},
                ],
            },
            "NCT03614260": {
                "name": "RADIANCE II", "phase": "III", "year": 2023,
                "tE": None, "tN": 150, "cE": None, "cN": 74, "group": "On meds",
                "publishedHR": None, "hrLCI": None, "hrUCI": None,
                "baseline": {"n": 224, "age": 54.0, "female": 38.0, "sbp_office": 155.0},
                "allOutcomes": [
                    {"shortLabel": "OfficeSBP", "title": "Change in daytime ambulatory SBP (mmHg)", "md": -6.3, "se": 1.8, "type": "CONTINUOUS"},
                ],
                "rob": ["low", "low", "low", "low", "low"],
                "snippet": "Lancet 2023; 401(10378):727-735",
                "sourceUrl": "https://www.thelancet.com/journals/lancet/article/PIIS0140-6736(23)00150-4/fulltext",
                "evidence": [
                    {"label": "Daytime Ambulatory SBP", "source": "Lancet 2023; 401:727-735", "text": "Daytime ambulatory SBP was reduced by 6.3 mmHg more with ultrasound RDN vs sham (P<0.0001).", "highlights": ["-6.3", "224"], "sourceUrl": "https://www.thelancet.com/journals/lancet/article/PIIS0140-6736(23)00150-4/fulltext"},
                ],
            },
            "NCT02918305": {
                "name": "REQUIRE", "phase": "III", "year": 2021,
                "tE": None, "tN": 72, "cE": None, "cN": 71, "group": "Japan",
                "publishedHR": None, "hrLCI": None, "hrUCI": None,
                "baseline": {"n": 143, "age": 56.0, "female": 29.0, "sbp_office": 162.0},
                "allOutcomes": [
                    {"shortLabel": "OfficeSBP", "title": "Change in 24h ambulatory SBP (mmHg)", "md": -6.6, "se": 2.3, "type": "CONTINUOUS"},
                ],
                "rob": ["low", "low", "low", "some", "low"],
                "snippet": "Circ Cardiovasc Interv 2021; 14:e009972",
                "sourceUrl": "https://www.ahajournals.org/doi/full/10.1161/CIRCINTERVENTIONS.120.009972",
                "evidence": [
                    {"label": "24h Ambulatory SBP", "source": "Circ Cardiovasc Interv 2021; 14:e009972", "text": "24h ambulatory SBP reduction was 6.6 mmHg greater with RDN vs sham procedure.", "highlights": ["-6.6", "143"], "sourceUrl": "https://www.ahajournals.org/doi/full/10.1161/CIRCINTERVENTIONS.120.009972"},
                ],
            },
        },
        "benchmarks": {},
        "ctgov_registry": {},
        "nma_ids": ["NCT02439749_ON", "NCT02649426", "NCT02439749_OFF", "NCT03614260", "NCT02918305"],
        "nma_label": "Renal Denervation vs Sham",
        "nma_indirect_label": "RDN modalities (Indirect comparison)",
        "is_continuous": True,
    },

    # ── 6. DOACs for Cancer VTE ──
    {
        "filename": "DOAC_CANCER_VTE_REVIEW.html",
        "title_short": "DOACs for Cancer-Associated VTE",
        "title_long": "Direct Oral Anticoagulants for Cancer-Associated Venous Thromboembolism: A Living Systematic Review and Meta-Analysis of Randomized Controlled Trials",
        "drug_name": "DOACs",
        "drug_name_lower": "doacs",
        "drug_regex_pattern": r"\bdoac|apixaban|edoxaban|rivaroxaban|direct oral anticoagulant\b",
        "drug_class": "Direct Oral Anticoagulant",
        "va_heading": "DOACs in Cancer-Associated VTE",
        "nyt_heading": "The DOAC Evidence in Cancer VTE",
        "storage_key": "doac_cancer_vte",
        "protocol": {
            "pop": "Adults with Active Cancer and Acute VTE",
            "int": "DOAC (Apixaban, Edoxaban, or Rivaroxaban)",
            "comp": "LMWH (Dalteparin or Enoxaparin)",
            "out": "Recurrent VTE",
            "subgroup": "DOAC type (Apixaban vs Edoxaban vs Rivaroxaban), Cancer type (GI vs non-GI), VTE type (PE vs DVT)",
            "secondary": "Major bleeding; clinically relevant non-major bleeding; all-cause mortality; GI bleeding",
        },
        "search_term": "doac cancer venous thromboembolism",
        "search_term_ctgov": "direct oral anticoagulant AND cancer AND thromboembolism",
        "effect_measure": "HR",
        "effect_measure_buttons": "HR",
        "population_desc": "Adults with active cancer and acute venous thromboembolism",
        "eligibility_intervention": "DOAC (apixaban, edoxaban, or rivaroxaban) as primary anticoagulant",
        "eligibility_intervention_exclude": "Dabigatran; DOAC for primary VTE prevention; non-cancer populations",
        "eligibility_participants": "Adults >=18 years with active cancer and objectively confirmed acute DVT or PE",
        "nct_acronyms": {"NCT02073682": "HOKUSAI VTE-Cancer", "NCT02583191": "SELECT-D", "NCT02585713": "ADAM VTE", "NCT03045406": "CARAVAGGIO"},
        "auto_include_ids": ["NCT02073682", "NCT02583191", "NCT02585713", "NCT03045406"],
        "known_trial_aliases": {
            "NCT02073682": ["hokusai vte-cancer", "hokusai"],
            "NCT02583191": ["select-d", "select d"],
            "NCT02585713": ["adam vte", "adam"],
            "NCT03045406": ["caravaggio"],
        },
        "trials": {
            "NCT02073682": {
                "name": "HOKUSAI VTE-Cancer", "phase": "III", "year": 2018,
                "tE": 67, "tN": 522, "cE": 71, "cN": 524, "group": "Edoxaban",
                "publishedHR": 0.97, "hrLCI": 0.70, "hrUCI": 1.36,
                "baseline": {"n": 1046, "age": 63.9, "female": 47.0, "cancer_gi": 26.0},
                "allOutcomes": [
                    {"shortLabel": "RecVTE", "title": "Recurrent VTE", "tE": 67, "cE": 71, "type": "PRIMARY", "pubHR": 0.97, "pubHR_LCI": 0.70, "pubHR_UCI": 1.36},
                    {"shortLabel": "MajBleed", "title": "Major bleeding", "tE": 36, "cE": 21, "type": "SAFETY", "pubHR": 1.77, "pubHR_LCI": 1.03, "pubHR_UCI": 3.04},
                ],
                "rob": ["low", "low", "low", "low", "low"],
                "snippet": "N Engl J Med 2018; 378:615-624",
                "sourceUrl": "https://www.nejm.org/doi/full/10.1056/NEJMoa1711948",
                "evidence": [
                    {"label": "Recurrent VTE", "source": "NEJM 2018; 378:615-624", "text": "Recurrent VTE occurred in 67 (12.8%) edoxaban vs 71 (13.5%) dalteparin patients (HR 0.97; 95% CI, 0.70 to 1.36; P=0.006 for noninferiority).", "highlights": ["67", "522", "71", "524", "0.97"], "sourceUrl": "https://www.nejm.org/doi/full/10.1056/NEJMoa1711948"},
                ],
            },
            "NCT02583191": {
                "name": "SELECT-D", "phase": "II", "year": 2018,
                "tE": 8, "tN": 101, "cE": 18, "cN": 102, "group": "Rivaroxaban",
                "publishedHR": 0.43, "hrLCI": 0.19, "hrUCI": 0.99,
                "baseline": {"n": 203, "age": 67.0, "female": 43.0, "cancer_gi": 12.0},
                "allOutcomes": [
                    {"shortLabel": "RecVTE", "title": "Recurrent VTE at 6 months", "tE": 8, "cE": 18, "type": "PRIMARY", "pubHR": 0.43, "pubHR_LCI": 0.19, "pubHR_UCI": 0.99},
                    {"shortLabel": "MajBleed", "title": "Major bleeding", "tE": 6, "cE": 4, "type": "SAFETY", "pubHR": 1.83, "pubHR_LCI": 0.68, "pubHR_UCI": 4.96},
                ],
                "rob": ["low", "some", "low", "low", "low"],
                "snippet": "J Clin Oncol 2018; 36(20):2017-2023",
                "sourceUrl": "https://ascopubs.org/doi/full/10.1200/JCO.2018.78.8034",
                "evidence": [
                    {"label": "Recurrent VTE", "source": "J Clin Oncol 2018; 36:2017-2023", "text": "VTE recurrence at 6 months: 8 (7.9%) rivaroxaban vs 18 (17.6%) dalteparin (HR 0.43; 95% CI, 0.19 to 0.99).", "highlights": ["8", "101", "18", "102", "0.43"], "sourceUrl": "https://ascopubs.org/doi/full/10.1200/JCO.2018.78.8034"},
                ],
            },
            "NCT02585713": {
                "name": "ADAM VTE", "phase": "III", "year": 2020,
                "tE": 1, "tN": 145, "cE": 9, "cN": 142, "group": "Apixaban",
                "publishedHR": 0.26, "hrLCI": 0.09, "hrUCI": 0.80,
                "baseline": {"n": 300, "age": 64.4, "female": 50.0, "cancer_gi": 16.0},
                "allOutcomes": [
                    {"shortLabel": "RecVTE", "title": "Recurrent VTE", "tE": 1, "cE": 9, "type": "PRIMARY", "pubHR": 0.26, "pubHR_LCI": 0.09, "pubHR_UCI": 0.80},
                    {"shortLabel": "MajBleed", "title": "Major bleeding", "tE": 0, "cE": 2, "type": "SAFETY"},
                ],
                "rob": ["low", "some", "low", "low", "low"],
                "snippet": "Blood 2020; 136(suppl 1):8-9 / J Thromb Haemost 2020; 18:3208-3217",
                "sourceUrl": "https://onlinelibrary.wiley.com/doi/full/10.1111/jth.15089",
                "evidence": [
                    {"label": "Recurrent VTE", "source": "J Thromb Haemost 2020; 18:3208-3217", "text": "Recurrent VTE: 1 (0.7%) apixaban vs 9 (6.3%) dalteparin (HR 0.26; 95% CI, 0.09 to 0.80; P=0.02).", "highlights": ["1", "145", "9", "142", "0.26"], "sourceUrl": "https://onlinelibrary.wiley.com/doi/full/10.1111/jth.15089"},
                ],
            },
            "NCT03045406": {
                "name": "CARAVAGGIO", "phase": "III", "year": 2020,
                "tE": 32, "tN": 576, "cE": 46, "cN": 579, "group": "Apixaban",
                "publishedHR": 0.63, "hrLCI": 0.37, "hrUCI": 1.07,
                "baseline": {"n": 1155, "age": 67.2, "female": 56.5, "cancer_gi": 31.0},
                "allOutcomes": [
                    {"shortLabel": "RecVTE", "title": "Recurrent VTE", "tE": 32, "cE": 46, "type": "PRIMARY", "pubHR": 0.63, "pubHR_LCI": 0.37, "pubHR_UCI": 1.07},
                    {"shortLabel": "MajBleed", "title": "Major bleeding", "tE": 22, "cE": 23, "type": "SAFETY", "pubHR": 0.82, "pubHR_LCI": 0.40, "pubHR_UCI": 1.69},
                ],
                "rob": ["low", "low", "low", "low", "low"],
                "snippet": "N Engl J Med 2020; 382:1599-1607",
                "sourceUrl": "https://www.nejm.org/doi/full/10.1056/NEJMoa1915103",
                "evidence": [
                    {"label": "Recurrent VTE", "source": "NEJM 2020; 382:1599-1607", "text": "Recurrent VTE occurred in 32 (5.6%) apixaban vs 46 (7.9%) dalteparin (HR 0.63; 95% CI, 0.37 to 1.07; P<0.001 for noninferiority).", "highlights": ["32", "576", "46", "579", "0.63"], "sourceUrl": "https://www.nejm.org/doi/full/10.1056/NEJMoa1915103"},
                ],
            },
        },
        "benchmarks": {},
        "ctgov_registry": {},
        "nma_ids": ["NCT02073682", "NCT02583191", "NCT02585713", "NCT03045406"],
        "nma_label": "DOACs vs LMWH",
        "nma_indirect_label": "Apixaban vs Edoxaban vs Rivaroxaban (NMA)",
    },

    # ── 7. Mavacamten for HCM ──
    {
        "filename": "MAVACAMTEN_HCM_REVIEW.html",
        "title_short": "Mavacamten for Obstructive HCM",
        "title_long": "Mavacamten for Hypertrophic Obstructive Cardiomyopathy: A Living Systematic Review and Meta-Analysis of Randomized Controlled Trials",
        "drug_name": "Mavacamten",
        "drug_name_lower": "mavacamten",
        "drug_regex_pattern": r"\bmavacamten|camzyos|myk-461\b",
        "drug_class": "Cardiac Myosin Inhibitor",
        "va_heading": "Mavacamten in Obstructive HCM",
        "nyt_heading": "The Mavacamten Evidence in oHCM",
        "storage_key": "mavacamten_hcm",
        "protocol": {
            "pop": "Adults with Symptomatic Obstructive HCM (NYHA II-III)",
            "int": "Mavacamten (Cardiac Myosin Inhibitor)",
            "comp": "Placebo",
            "out": "Composite Functional Response (pVO2 + NYHA Improvement or LVOT Gradient Reduction)",
            "subgroup": "Baseline LVOT gradient, NYHA class, Background therapy (beta-blocker vs CCB)",
            "secondary": "pVO2 improvement >=1.5 mL/kg/min; post-exercise LVOT gradient; KCCQ-CSS; SRT eligibility avoidance",
        },
        "search_term": "mavacamten hypertrophic cardiomyopathy",
        "search_term_ctgov": "mavacamten AND hypertrophic cardiomyopathy",
        "effect_measure": "OR",
        "effect_measure_buttons": "OR",
        "population_desc": "Adults with symptomatic obstructive HCM (LVOT gradient >=50 mmHg)",
        "eligibility_intervention": "Mavacamten (any dose) as primary experimental drug",
        "eligibility_intervention_exclude": "Open-label extensions without placebo control; aficamten studies",
        "eligibility_participants": "Adults >=18 years with obstructive HCM, NYHA class II-III, LVOT gradient >=50 mmHg",
        "nct_acronyms": {"NCT03470545": "EXPLORER-HCM", "NCT04349072": "VALOR-HCM", "NCT03723655": "MAVA-LTE", "NCT05174416": "Chinese Phase 3"},
        "auto_include_ids": ["NCT03470545", "NCT04349072", "NCT05174416"],
        "known_trial_aliases": {
            "NCT03470545": ["explorer-hcm", "explorer"],
            "NCT04349072": ["valor-hcm", "valor"],
            "NCT03723655": ["mava-lte"],
            "NCT05174416": ["chinese phase 3 mavacamten"],
        },
        "trials": {
            "NCT03470545": {
                "name": "EXPLORER-HCM", "phase": "III", "year": 2020,
                "tE": 45, "tN": 123, "cE": 22, "cN": 128, "group": "oHCM",
                "publishedHR": None, "hrLCI": None, "hrUCI": None,
                "baseline": {"n": 251, "age": 58.5, "female": 45.0, "nyha_iii": 27.0, "lvot_gradient": 74.0},
                "allOutcomes": [
                    {"shortLabel": "CompositeResp", "title": "Composite response (pVO2 + NYHA or pVO2 + LVOT gradient)", "tE": 45, "cE": 22, "type": "PRIMARY", "pubOR": 2.80, "pubOR_LCI": 1.50, "pubOR_UCI": 5.30},
                ],
                "rob": ["low", "low", "low", "low", "low"],
                "snippet": "Lancet 2020; 396(10261):759-769",
                "sourceUrl": "https://www.thelancet.com/journals/lancet/article/PIIS0140-6736(20)31792-X/fulltext",
                "evidence": [
                    {"label": "Primary Composite Response", "source": "Lancet 2020; 396:759-769", "text": "The primary endpoint was met by 45 (36.6%) mavacamten vs 22 (17.2%) placebo patients (difference 19.4 percentage points; 95% CI, 8.7 to 30.1; P=0.0005).", "highlights": ["45", "123", "22", "128", "2.80"], "sourceUrl": "https://www.thelancet.com/journals/lancet/article/PIIS0140-6736(20)31792-X/fulltext"},
                ],
            },
            "NCT04349072": {
                "name": "VALOR-HCM", "phase": "III", "year": 2022,
                "tE": 48, "tN": 56, "cE": 10, "cN": 56, "group": "Pre-SRT",
                "publishedHR": None, "hrLCI": None, "hrUCI": None,
                "baseline": {"n": 112, "age": 60.0, "female": 50.0, "nyha_iii": 65.0, "lvot_gradient": 83.0},
                "allOutcomes": [
                    {"shortLabel": "SRT_Avoid", "title": "Remaining eligible for or proceeding to SRT", "tE": 48, "cE": 10, "type": "PRIMARY", "pubOR": 17.9, "pubOR_LCI": 6.5, "pubOR_UCI": 49.0},
                ],
                "rob": ["low", "low", "low", "low", "low"],
                "snippet": "Lancet 2022; 400(10358):1109-1119",
                "sourceUrl": "https://www.thelancet.com/journals/lancet/article/PIIS0140-6736(22)01379-5/fulltext",
                "evidence": [
                    {"label": "SRT Avoidance", "source": "Lancet 2022; 400:1109-1119", "text": "At 16 weeks, 48 of 56 (85.7%) mavacamten vs 10 of 56 (17.9%) placebo patients no longer met SRT guidelines (OR 17.9; 95% CI, 6.5 to 49.0).", "highlights": ["48", "56", "10", "56", "17.9"], "sourceUrl": "https://www.thelancet.com/journals/lancet/article/PIIS0140-6736(22)01379-5/fulltext"},
                ],
            },
            "NCT03723655": {
                "name": "MAVA-LTE", "phase": "III", "year": 2023,
                "tE": None, "tN": 314, "cE": None, "cN": 0, "group": "Open-label extension",
                "publishedHR": None, "hrLCI": None, "hrUCI": None,
                "baseline": {"n": 314, "age": 58.0, "female": 45.0},
                "allOutcomes": [],
                "rob": ["low", "low", "low", "low", "some"],
                "snippet": "JACC 2023; 81(18):1759-1770",
                "sourceUrl": "https://www.jacc.org/doi/full/10.1016/j.jacc.2023.03.009",
                "evidence": [
                    {"label": "Long-term safety", "source": "JACC 2023; 81:1759-1770", "text": "Long-term mavacamten treatment over 84 weeks maintained reductions in LVOT gradient and improved functional capacity.", "highlights": ["314"], "sourceUrl": "https://www.jacc.org/doi/full/10.1016/j.jacc.2023.03.009"},
                ],
                "_supplementary": True,
            },
            "NCT05174416": {
                "name": "Chinese Phase 3", "phase": "III", "year": 2023,
                "tE": 31, "tN": 54, "cE": 5, "cN": 27, "group": "Chinese oHCM",
                "publishedHR": None, "hrLCI": None, "hrUCI": None,
                "baseline": {"n": 81, "age": 47.0, "female": 35.0, "lvot_gradient": 78.0},
                "allOutcomes": [
                    {"shortLabel": "CompositeResp", "title": "Composite functional response", "tE": 31, "cE": 5, "type": "PRIMARY", "pubOR": 6.9, "pubOR_LCI": 2.2, "pubOR_UCI": 21.5},
                ],
                "rob": ["low", "low", "low", "low", "low"],
                "snippet": "JACC 2023 (Chinese Phase 3 trial report)",
                "sourceUrl": "https://clinicaltrials.gov/study/NCT05174416",
                "evidence": [
                    {"label": "Composite Response", "source": "JACC 2023 (Chinese Phase 3)", "text": "31/54 (57.4%) mavacamten vs 5/27 (18.5%) placebo achieved the primary composite response endpoint (OR 6.9; 95% CI, 2.2 to 21.5).", "highlights": ["31", "54", "5", "27", "6.9"], "sourceUrl": "https://clinicaltrials.gov/study/NCT05174416"},
                ],
            },
        },
        "benchmarks": {},
        "ctgov_registry": {},
        "nma_ids": ["NCT03470545", "NCT04349072", "NCT05174416"],
        "nma_label": "Mavacamten vs Placebo",
        "nma_indirect_label": "Mavacamten vs Aficamten (Indirect)",
    },

    # ── 8. Rivaroxaban Vascular Protection ──
    {
        "filename": "RIVAROXABAN_VASC_REVIEW.html",
        "title_short": "Rivaroxaban Vascular Protection",
        "title_long": "Low-Dose Rivaroxaban for Vascular Protection in Atherosclerotic Disease: A Living Systematic Review and Meta-Analysis of Randomized Controlled Trials",
        "drug_name": "Rivaroxaban (Low-Dose)",
        "drug_name_lower": "rivaroxaban",
        "drug_regex_pattern": r"\brivaroxaban|xarelto\b",
        "drug_class": "Factor Xa Inhibitor (Low-Dose)",
        "va_heading": "Rivaroxaban Vascular Protection",
        "nyt_heading": "The Rivaroxaban Vascular Evidence",
        "storage_key": "rivaroxaban_vasc",
        "protocol": {
            "pop": "Adults with Stable Atherosclerotic Vascular Disease (CAD, PAD, or Recent ACS)",
            "int": "Rivaroxaban 2.5 mg BID + Aspirin",
            "comp": "Aspirin Alone (or Placebo)",
            "out": "MACE (CV Death, MI, Stroke)",
            "subgroup": "Disease type (CAD vs PAD vs ACS vs HF), Rivaroxaban dose (2.5 mg vs 5 mg), Concomitant antiplatelet",
            "secondary": "All-cause mortality; stroke; MI; major limb events; major bleeding",
        },
        "search_term": "rivaroxaban vascular protection",
        "search_term_ctgov": "rivaroxaban AND atherosclerotic disease",
        "effect_measure": "HR",
        "effect_measure_buttons": "HR",
        "population_desc": "Adults with stable atherosclerotic cardiovascular disease",
        "eligibility_intervention": "Rivaroxaban (low-dose 2.5 mg BID) + aspirin as primary experimental combination",
        "eligibility_intervention_exclude": "Full-dose rivaroxaban (20 mg); VTE treatment doses; no aspirin co-administration",
        "eligibility_participants": "Adults >=18 years with CAD, PAD, recent ACS, or HF with atherosclerotic disease",
        "nct_acronyms": {"NCT01776424": "COMPASS", "NCT02504216": "VOYAGER-PAD", "NCT01877915": "COMMANDER HF", "NCT00809965": "ATLAS ACS 2"},
        "auto_include_ids": ["NCT01776424", "NCT02504216", "NCT01877915", "NCT00809965"],
        "known_trial_aliases": {
            "NCT01776424": ["compass"],
            "NCT02504216": ["voyager-pad", "voyager pad"],
            "NCT01877915": ["commander hf", "commander"],
            "NCT00809965": ["atlas acs 2", "atlas acs"],
        },
        "trials": {
            "NCT01776424": {
                "name": "COMPASS", "phase": "III", "year": 2017,
                "tE": 379, "tN": 9152, "cE": 496, "cN": 9126, "group": "Stable CAD/PAD",
                "publishedHR": 0.76, "hrLCI": 0.66, "hrUCI": 0.86,
                "baseline": {"n": 27395, "age": 68.2, "female": 21.8, "dm": 38.0, "cad_pct": 91.0},
                "allOutcomes": [
                    {"shortLabel": "MACE", "title": "CV death, stroke, or MI", "tE": 379, "cE": 496, "type": "PRIMARY", "pubHR": 0.76, "pubHR_LCI": 0.66, "pubHR_UCI": 0.86},
                    {"shortLabel": "ACM", "title": "All-cause mortality", "tE": 313, "cE": 378, "type": "SECONDARY", "pubHR": 0.82, "pubHR_LCI": 0.71, "pubHR_UCI": 0.96},
                    {"shortLabel": "Stroke", "title": "Stroke", "tE": 83, "cE": 142, "type": "SECONDARY", "pubHR": 0.58, "pubHR_LCI": 0.44, "pubHR_UCI": 0.76},
                ],
                "rob": ["low", "low", "low", "low", "low"],
                "snippet": "N Engl J Med 2017; 377:1319-1330",
                "sourceUrl": "https://www.nejm.org/doi/full/10.1056/NEJMoa1709118",
                "evidence": [
                    {"label": "Primary MACE", "source": "NEJM 2017; 377:1319-1330", "text": "The primary outcome occurred in 379 (4.1%) in the rivaroxaban+aspirin group and 496 (5.4%) in the aspirin-alone group (HR 0.76; 95% CI, 0.66 to 0.86; P<0.001).", "highlights": ["379", "9152", "496", "9126", "0.76"], "sourceUrl": "https://www.nejm.org/doi/full/10.1056/NEJMoa1709118"},
                ],
            },
            "NCT02504216": {
                "name": "VOYAGER-PAD", "phase": "III", "year": 2020,
                "tE": 508, "tN": 3286, "cE": 584, "cN": 3278, "group": "Post-revasc PAD",
                "publishedHR": 0.85, "hrLCI": 0.76, "hrUCI": 0.96,
                "baseline": {"n": 6564, "age": 67.0, "female": 26.0, "dm": 40.0},
                "allOutcomes": [
                    {"shortLabel": "MACE_ALI", "title": "MACE, ALI, or major amputation", "tE": 508, "cE": 584, "type": "PRIMARY", "pubHR": 0.85, "pubHR_LCI": 0.76, "pubHR_UCI": 0.96},
                    {"shortLabel": "ACM", "title": "All-cause mortality", "tE": 240, "cE": 259, "type": "SECONDARY", "pubHR": 0.93, "pubHR_LCI": 0.78, "pubHR_UCI": 1.10},
                ],
                "rob": ["low", "low", "low", "low", "low"],
                "snippet": "N Engl J Med 2020; 382:1994-2004",
                "sourceUrl": "https://www.nejm.org/doi/full/10.1056/NEJMoa2000052",
                "evidence": [
                    {"label": "Primary Composite", "source": "NEJM 2020; 382:1994-2004", "text": "The primary end point occurred in 508 (15.5%) rivaroxaban+aspirin vs 584 (17.8%) placebo+aspirin (HR 0.85; 95% CI, 0.76 to 0.96; P=0.009).", "highlights": ["508", "3286", "584", "3278", "0.85"], "sourceUrl": "https://www.nejm.org/doi/full/10.1056/NEJMoa2000052"},
                ],
            },
            "NCT01877915": {
                "name": "COMMANDER HF", "phase": "III", "year": 2018,
                "tE": 626, "tN": 2507, "cE": 658, "cN": 2515, "group": "HF+CAD",
                "publishedHR": 0.94, "hrLCI": 0.84, "hrUCI": 1.05,
                "baseline": {"n": 5022, "age": 66.4, "female": 23.0, "dm": 41.0, "lvef": 34.0},
                "allOutcomes": [
                    {"shortLabel": "MACE", "title": "All-cause death, MI, or stroke", "tE": 626, "cE": 658, "type": "PRIMARY", "pubHR": 0.94, "pubHR_LCI": 0.84, "pubHR_UCI": 1.05},
                    {"shortLabel": "ACM", "title": "All-cause mortality", "tE": 476, "cE": 478, "type": "SECONDARY", "pubHR": 0.98, "pubHR_LCI": 0.87, "pubHR_UCI": 1.12},
                ],
                "rob": ["low", "low", "low", "low", "low"],
                "snippet": "N Engl J Med 2018; 379:1332-1342",
                "sourceUrl": "https://www.nejm.org/doi/full/10.1056/NEJMoa1808848",
                "evidence": [
                    {"label": "Primary MACE", "source": "NEJM 2018; 379:1332-1342", "text": "The primary outcome occurred in 626 (25.0%) rivaroxaban vs 658 (26.2%) placebo patients (HR 0.94; 95% CI, 0.84 to 1.05; P=0.27).", "highlights": ["626", "2507", "658", "2515", "0.94"], "sourceUrl": "https://www.nejm.org/doi/full/10.1056/NEJMoa1808848"},
                ],
            },
            "NCT00809965": {
                "name": "ATLAS ACS 2", "phase": "III", "year": 2012,
                "tE": 313, "tN": 5174, "cE": 376, "cN": 5176, "group": "Recent ACS",
                "publishedHR": 0.84, "hrLCI": 0.72, "hrUCI": 0.97,
                "baseline": {"n": 15526, "age": 61.7, "female": 25.0, "dm": 32.0},
                "allOutcomes": [
                    {"shortLabel": "MACE", "title": "CV death, MI, or stroke (2.5 mg arm)", "tE": 313, "cE": 376, "type": "PRIMARY", "pubHR": 0.84, "pubHR_LCI": 0.72, "pubHR_UCI": 0.97},
                    {"shortLabel": "ACM", "title": "All-cause mortality", "tE": 103, "cE": 153, "type": "SECONDARY", "pubHR": 0.68, "pubHR_LCI": 0.53, "pubHR_UCI": 0.87},
                ],
                "rob": ["low", "low", "low", "low", "low"],
                "snippet": "N Engl J Med 2012; 366:9-19",
                "sourceUrl": "https://www.nejm.org/doi/full/10.1056/NEJMoa1112277",
                "evidence": [
                    {"label": "Primary MACE", "source": "NEJM 2012; 366:9-19", "text": "In the 2.5 mg rivaroxaban arm, the primary end point occurred in 313 (9.1%) vs 376 (10.7%) placebo (HR 0.84; 95% CI, 0.72 to 0.97; P=0.02).", "highlights": ["313", "5174", "376", "5176", "0.84"], "sourceUrl": "https://www.nejm.org/doi/full/10.1056/NEJMoa1112277"},
                ],
            },
        },
        "benchmarks": {},
        "ctgov_registry": {},
        "nma_ids": ["NCT01776424", "NCT02504216", "NCT01877915", "NCT00809965"],
        "nma_label": "Rivaroxaban+Aspirin vs Aspirin Alone",
        "nma_indirect_label": "Rivaroxaban vs Ticagrelor (Indirect)",
    },
]


# ═══════════════════════════════════════════════════════════════
# TEMPLATE TRANSFORMATION
# ═══════════════════════════════════════════════════════════════

import json

def js_val(v):
    """Convert Python value to JS literal."""
    if v is None:
        return "null"
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, str):
        # Escape single quotes and backslashes for JS
        escaped = v.replace("\\", "\\\\").replace("'", "\\'").replace("\n", "\\n")
        return f"'{escaped}'"
    if isinstance(v, (int, float)):
        return str(v)
    if isinstance(v, list):
        return "[" + ", ".join(js_val(x) for x in v) + "]"
    if isinstance(v, dict):
        items = ", ".join(f"{k}: {js_val(vv)}" for k, vv in v.items())
        return "{" + items + "}"
    return str(v)


def build_real_data_js(trials_dict):
    """Build the realData JS object from trial definitions."""
    lines = []
    for nct_id, t in trials_dict.items():
        if t.get("_supplementary"):
            # Supplementary trials still get included in realData but without poolable data
            pass
        baseline_js = json.dumps(t.get("baseline", {}))
        outcomes_js = build_outcomes_js(t.get("allOutcomes", []))
        rob_js = json.dumps(t.get("rob", ["low","low","low","low","low"]))
        evidence_js = build_evidence_js(t.get("evidence", []))

        pub_hr = t.get("publishedHR")
        hr_lci = t.get("hrLCI")
        hr_uci = t.get("hrUCI")

        line = f"""    '{nct_id}': {{
                    baseline: {baseline_js},
        name: '{t["name"]}', phase: '{t["phase"]}', year: {t["year"]}, """

        # Add event counts if present
        if t.get("tE") is not None:
            line += f"tE: {t['tE']}, "
        else:
            line += "tE: null, "

        line += f"tN: {t['tN']}, "

        if t.get("cE") is not None:
            line += f"cE: {t['cE']}, "
        else:
            line += "cE: null, "

        line += f"cN: {t['cN']}, "
        line += f"group: '{t['group']}', "

        if pub_hr is not None:
            line += f"publishedHR: {pub_hr}, hrLCI: {hr_lci}, hrUCI: {hr_uci},"
        else:
            line += "publishedHR: null,"

        line += f"""
        allOutcomes: {outcomes_js},
        rob: {rob_js},
        snippet: '{escape_js_str(t.get("snippet", ""))}',
        sourceUrl: '{escape_js_str(t.get("sourceUrl", ""))}'"""

        if evidence_js:
            line += f""",
        evidence: {evidence_js}"""

        line += """
    }"""
        lines.append(line)

    return "{\n" + ",\n".join(lines) + "\n}"


def build_outcomes_js(outcomes):
    """Build allOutcomes JS array."""
    if not outcomes:
        return "[]"
    items = []
    for o in outcomes:
        parts = [f"shortLabel: '{o['shortLabel']}'", f"title: '{escape_js_str(o['title'])}'"]
        if "tE" in o and o["tE"] is not None:
            parts.append(f"tE: {o['tE']}")
        if "cE" in o and o["cE"] is not None:
            parts.append(f"cE: {o['cE']}")
        parts.append(f"type: '{o['type']}'")
        if "pubHR" in o and o["pubHR"] is not None:
            parts.append(f"pubHR: {o['pubHR']}, pubHR_LCI: {o['pubHR_LCI']}, pubHR_UCI: {o['pubHR_UCI']}")
        if "pubOR" in o and o["pubOR"] is not None:
            parts.append(f"pubHR: {o['pubOR']}, pubHR_LCI: {o['pubOR_LCI']}, pubHR_UCI: {o['pubOR_UCI']}")
        if "md" in o and o["md"] is not None:
            parts.append(f"md: {o['md']}, se: {o['se']}")
        items.append("{ " + ", ".join(parts) + " }")
    return "[\n            " + ",\n            ".join(items) + "\n        ]"


def build_evidence_js(evidence_list):
    """Build evidence array JS."""
    if not evidence_list:
        return ""
    items = []
    for e in evidence_list:
        highlights = json.dumps(e.get("highlights", []))
        items.append(f"""{{ label: '{escape_js_str(e["label"])}', source: '{escape_js_str(e["source"])}', text: '{escape_js_str(e["text"])}', highlights: {highlights}, sourceUrl: '{escape_js_str(e.get("sourceUrl", ""))}' }}""")
    return "[\n            " + ",\n            ".join(items) + "\n        ]"


def escape_js_str(s):
    """Escape a string for embedding in JS single-quoted string."""
    if not s:
        return ""
    return s.replace("\\", "\\\\").replace("'", "\\'").replace("\n", "\\n").replace("\r", "")


def build_auto_include_ids_js(ids_list):
    return "new Set([" + ", ".join(f"'{id}'" for id in ids_list) + "])"


def build_known_aliases_js(aliases_dict):
    lines = []
    for nct_id, aliases in aliases_dict.items():
        alias_strs = ", ".join(f"'{a}'" for a in aliases)
        lines.append(f"            {nct_id}: [{alias_strs}]")
    return "{\n" + ",\n".join(lines) + "\n        }"


def build_nct_acronyms_js(acronyms_dict):
    items = ", ".join(f"'{k}': '{v}'" for k, v in acronyms_dict.items())
    return "{ " + items + " }"


def build_benchmarks_js(benchmarks_dict):
    if not benchmarks_dict:
        return "{}"
    parts = []
    for outcome_key, entries in benchmarks_dict.items():
        entry_strs = []
        for e in entries:
            entry_strs.append(f"{{ label: '{escape_js_str(e['label'])}', citation: '{escape_js_str(e['citation'])}', year: {e['year']}, measure: '{e['measure']}', estimate: {e['estimate']}, lci: {e['lci']}, uci: {e['uci']}, k: {e['k']}, n: {e['n']}, scope: '{escape_js_str(e['scope'])}' }}")
        parts.append(f"            {outcome_key}: [\n                " + ",\n                ".join(entry_strs) + "\n            ]")
    return "{\n" + ",\n".join(parts) + "\n        }"


def transform_template(template_html, app_config):
    """Apply all replacements to the template for a given app config."""
    html = template_html

    cfg = app_config
    drug = cfg["drug_name"]
    drug_lower = cfg["drug_name_lower"]
    storage = cfg["storage_key"]
    proto = cfg["protocol"]

    # ── 1. Title ──
    html = re.sub(
        r'<title>.*?</title>',
        f'<title>RapidMeta Cardiology | {cfg["title_short"]} Ultra-Precision v12.5</title>',
        html
    )

    # ── 2. Review Title in protocol table ──
    html = html.replace(
        'Bempedoic Acid for Cardiovascular Risk Reduction: A Living Systematic Review and Meta-Analysis of Randomized Controlled Trials',
        cfg["title_long"]
    )

    # ── 3. PICO inputs ──
    html = re.sub(
        r'value="Adults with ASCVD or high CV risk, including statin-intolerant patients"',
        f'value="{proto["pop"]}"',
        html
    )
    html = re.sub(
        r'value="Bempedoic Acid \(ACL Inhibitor\)"',
        f'value="{proto["int"]}"',
        html
    )
    html = re.sub(
        r'value="Placebo or standard of care"',
        f'value="{proto["comp"]}"',
        html
    )
    html = re.sub(
        r'value="MACE Composite \(CV Death, Nonfatal MI, Nonfatal Stroke, HFH\)"',
        f'value="{proto["out"]}"',
        html
    )
    html = re.sub(
        r'value="Indication \(HF vs CKD\), Phase \(III vs IV\), Baseline eGFR"',
        f'value="{proto["subgroup"]}"',
        html
    )

    # Secondary outcomes
    html = re.sub(
        r'All-cause mortality; renal composite \(eGFR decline, ESKD, renal death\); individual MACE components; hyperkalemia',
        proto.get("secondary", "All-cause mortality; individual endpoint components"),
        html
    )

    # ── 4. Protocol state defaults ──
    html = re.sub(
        r"protocol: \{ pop: 'Heart Failure or CKD', int: 'Bempedoic Acid', comp: 'Placebo', out: 'MACE Composite', subgroup: 'Indication \(HF vs CKD\), Phase \(III vs IV\), Baseline eGFR'",
        f"protocol: {{ pop: '{escape_js_str(proto['pop'])}', int: '{escape_js_str(proto['int'])}', comp: '{escape_js_str(proto['comp'])}', out: '{escape_js_str(proto['out'])}', subgroup: '{escape_js_str(proto['subgroup'])}'",
        html
    )

    # ── 5. localStorage keys ──
    html = html.replace("rapid_meta_bempedoic acid_v12_0", f"rapid_meta_{storage}_v12_0")
    html = html.replace("rapid_meta_bempedoic acid_v11_0", f"rapid_meta_{storage}_v11_0")
    html = html.replace("rapid_meta_bempedoic acid_v10_0", f"rapid_meta_{storage}_v10_0")
    html = html.replace("rapid_meta_bempedoic acid_v9_3", f"rapid_meta_{storage}_v9_3")
    html = html.replace("rapid_meta_bempedoic acid_theme", f"rapid_meta_{storage}_theme")

    # ── 6. realData block ──
    real_data_js = build_real_data_js(cfg["trials"])
    html = re.sub(
        r'realData:\s*\{.*?\n\},',
        f'realData: {real_data_js},',
        html,
        count=1,
        flags=re.DOTALL
    )

    # ── 7. AUTO_INCLUDE_TRIAL_IDS ──
    auto_ids_js = build_auto_include_ids_js(cfg["auto_include_ids"])
    html = re.sub(
        r"const AUTO_INCLUDE_TRIAL_IDS = new Set\(\[.*?\]\);",
        f"const AUTO_INCLUDE_TRIAL_IDS = {auto_ids_js};",
        html
    )

    # ── 8. KNOWN_TRIAL_ALIASES ──
    aliases_js = build_known_aliases_js(cfg["known_trial_aliases"])
    html = re.sub(
        r"const KNOWN_TRIAL_ALIASES = \{.*?\};",
        f"const KNOWN_TRIAL_ALIASES = {aliases_js};",
        html,
        flags=re.DOTALL
    )

    # ── 9. nctAcronyms ──
    acronyms_js = build_nct_acronyms_js(cfg["nct_acronyms"])
    html = re.sub(
        r"nctAcronyms:\s*\{[^}]*\}",
        f"nctAcronyms: {acronyms_js}",
        html,
        count=1
    )

    # ── 10. Search queries ──
    search = cfg["search_term"]
    search_ctgov = cfg.get("search_term_ctgov", search)

    # CT.gov API URL
    html = re.sub(
        r"query\.intr=bempedoic\+?acid",
        f"query.intr={search_ctgov.replace(' ', '+')}",
        html
    )
    html = re.sub(
        r"query\.intr=bempedoic acid",
        f"query.intr={search_ctgov}",
        html
    )

    # PubMed / Europe PMC query
    html = re.sub(
        r"bempedoic acid AND \(TITLE:randomized OR PUB_TYPE",
        f"{search} AND (TITLE:randomized OR PUB_TYPE",
        html
    )
    html = re.sub(
        r"bempedoic acid AND SRC:MED",
        f"{search} AND SRC:MED",
        html
    )

    # OpenAlex
    html = re.sub(
        r"search=bempedoic acid",
        f"search={search}",
        html
    )
    html = re.sub(
        r"search=bempedoic\+acid",
        f"search={search.replace(' ', '+')}",
        html
    )

    # ── 11. Drug name references (case-insensitive replacements) ──
    # Visual Abstract heading
    html = html.replace(
        'Bempedoic Acid in Cardio-Kidney-Metabolic Disease',
        cfg["va_heading"]
    )
    # NYT headline
    html = html.replace(
        'The Bempedoic Acid Evidence',
        cfg["nyt_heading"]
    )

    # Drug detection regex in auto-screener
    html = html.replace(
        r"const hasDrug = /\bbempedoic acid\b|bay\s*94/i.test(text);",
        f"const hasDrug = /{cfg['drug_regex_pattern']}/i.test(text);"
    )

    # Auto-screen note
    html = html.replace(
        'Auto-screen proposed INCLUDE for canonical bempedoic acid trial.',
        f'Auto-screen proposed INCLUDE for canonical {drug_lower} trial.'
    )

    # RapidMeta app label
    html = html.replace(
        "app: 'RapidMeta Bempedoic Acid v12.0'",
        f"app: 'RapidMeta {drug} v12.0'"
    )

    # Plotly download filename
    html = re.sub(
        r"filename: 'bempedoic acid_'",
        f"filename: '{storage}_'",
        html
    )

    # Stale banner text
    html = html.replace(
        'no new completed bempedoic acid trials found',
        f'no new completed {drug_lower} trials found'
    )

    # ── 12. Eligibility criteria table ──
    html = html.replace(
        'Bempedoic Acid (any dose) as primary experimental drug',
        cfg["eligibility_intervention"]
    )
    html = html.replace(
        'Bempedoic Acid as concomitant/background only',
        cfg["eligibility_intervention_exclude"]
    )
    html = re.sub(
        r"Adults &ge;18 years with HF \(EF &ge;40%\) or CKD \(stages 1&ndash;4\) associated with T2DM",
        cfg["eligibility_participants"],
        html
    )
    html = html.replace(
        'Bempedoic Acid dose, trial phase, treatment duration',
        f'{drug} dose/regimen, trial phase, treatment duration'
    )

    # ── 13. PUBLISHED_META_BENCHMARKS ──
    benchmarks_js = build_benchmarks_js(cfg["benchmarks"])
    html = re.sub(
        r"const PUBLISHED_META_BENCHMARKS = \{.*?\};",
        f"const PUBLISHED_META_BENCHMARKS = {benchmarks_js};",
        html,
        flags=re.DOTALL
    )

    # Benchmark summary text
    html = re.sub(
        r"published bempedoic acid pooled analyses",
        f"published {drug_lower} pooled analyses",
        html
    )

    # ── 14. CTGOV_EVIDENCE_REGISTRY ──
    html = re.sub(
        r"const CTGOV_EVIDENCE_REGISTRY = \{.*?\};",
        "const CTGOV_EVIDENCE_REGISTRY = {};",
        html,
        flags=re.DOTALL
    )

    # ── 15. NMA Engine ──
    nma_ids_js = json.dumps(cfg["nma_ids"])
    html = re.sub(
        r"const bempedoicIds = \[.*?\]\.filter",
        f"const bempedoicIds = {nma_ids_js}.filter",
        html
    )
    html = html.replace(
        "direct: { label: 'Bempedoic Acid vs Placebo'",
        f"direct: {{ label: '{cfg['nma_label']}'"
    )
    html = html.replace(
        "indirect: { label: 'Bempedoic Acid vs Ezetimibe (Indirect)'",
        f"indirect: {{ label: '{cfg['nma_indirect_label']}'"
    )
    html = html.replace(
        "// Indirect comparison logic: Bempedoic Acid vs Ezetimibe",
        f"// Indirect comparison logic: {cfg['nma_label']}"
    )

    # ── 16. BENCHMARK_OUTCOME_NOTES ──
    html = re.sub(
        r"Published bempedoic acid meta-analyses usually report",
        f"Published {drug_lower} meta-analyses usually report",
        html
    )

    # ── 17. Arabic translations (replace bempedoic-specific ones generically) ──
    # Keep the Arabic keys but replace English references
    html = html.replace(
        "'Bempedoic Acid in Cardio-Kidney-Metabolic Disease': ",
        f"'{cfg['va_heading']}': "
    )
    html = html.replace(
        "'The Bempedoic Acid Evidence': ",
        f"'{cfg['nyt_heading']}': "
    )
    html = re.sub(
        r"'Bempedoic Acid for Cardiovascular Risk Reduction: A Living Systematic Review and Meta-Analysis of Randomized Controlled Trials': ",
        f"'{escape_js_str(cfg['title_long'])}': ",
        html
    )
    html = re.sub(
        r"'Bempedoic Acid \(ACL Inhibitor\)': ",
        f"'{escape_js_str(proto['int'])}': ",
        html
    )

    # ── 18. rReference (R validation baselines) - clear for new apps ──
    # This block has nested {} so we need to match balanced braces
    rref_start = html.find("rReference: {")
    if rref_start >= 0:
        # Find the matching closing brace
        brace_start = html.index("{", rref_start)
        depth = 0
        pos = brace_start
        while pos < len(html):
            if html[pos] == "{":
                depth += 1
            elif html[pos] == "}":
                depth -= 1
                if depth == 0:
                    html = html[:rref_start] + "rReference: {}" + html[pos+1:]
                    break
            pos += 1

    # ── 19. Outcome selector default ──
    html = re.sub(
        r'<option value="default">Matched CV Composite \(default\)</option>',
        f'<option value="default">{proto["out"]} (default)</option>',
        html
    )

    # ── 20. Population-specific relevance regex ──
    # The hasRelevantPop regex needs updating per topic
    pop_patterns = {
        "sglt2_ckd": r"\\bchronic kidney disease\\b|\\bckd\\b|\\beGFR\\b|\\bkidney\\b|\\besrd\\b|\\beskd\\b",
        "arni_hf": r"\\bheart failure\\b|\\bhfref\\b|\\bhfpef\\b|\\bhfmref\\b|\\bejection fraction\\b",
        "ablation_af": r"\\batrial fibrillation\\b|\\baf\\b|\\brhythm control\\b|\\bablation\\b|\\bpulmonary vein\\b",
        "iv_iron_hf": r"\\bheart failure\\b|\\biron deficiency\\b|\\bferritin\\b|\\btsat\\b|\\bhfref\\b",
        "renal_denerv": r"\\bhypertension\\b|\\bresistant hypertension\\b|\\bblood pressure\\b|\\bsystolic\\b|\\bsbp\\b",
        "doac_cancer_vte": r"\\bcancer\\b|\\bvenous thromboembolism\\b|\\bvte\\b|\\bpulmonary embolism\\b|\\bdeep vein\\b",
        "mavacamten_hcm": r"\\bhypertrophic cardiomyopathy\\b|\\bhcm\\b|\\blvot\\b|\\bobstructive\\b|\\bseptal\\b",
        "rivaroxaban_vasc": r"\\batherosclerotic\\b|\\bvascular\\b|\\bcoronary\\b|\\bperipheral arterial\\b|\\bpad\\b|\\bcad\\b",
    }

    pop_pat = pop_patterns.get(storage, r"\\bcardiovascular\\b|\\bheart\\b")
    html = re.sub(
        r"const hasRelevantPop = /.*?/\.test\(text\);",
        f"const hasRelevantPop = /{pop_pat}/.test(text);",
        html,
        count=1
    )

    # ── 21. Effect measure for OR-based or MD-based apps ──
    em = cfg["effect_measure"]
    if em == "OR":
        # For mavacamten: default to OR
        html = re.sub(
            r"effectMeasure: 'HR'",
            "effectMeasure: 'OR'",
            html,
            count=1
        )
        # Also make OR the default active button
        html = re.sub(
            r'data-em="AUTO" role="radio" aria-checked="true"',
            'data-em="AUTO" role="radio" aria-checked="false"',
            html
        )
        html = re.sub(
            r'data-em="OR" role="radio" aria-checked="false"',
            'data-em="OR" role="radio" aria-checked="true"',
            html
        )

    # ── 22. For continuous (MD) apps, set effectMeasure to AUTO and
    # ensure all trials use ContinuousMDEngine ──
    if cfg.get("is_continuous"):
        # The ContinuousMDEngine is already in the template and triggers
        # automatically when outcomes have type: 'CONTINUOUS'.
        # We just need to make sure default effectMeasure is set sensibly.
        # Replace the effect measure selector label
        html = re.sub(
            r"title=\"Primary analysis: use published hazard ratios when available, otherwise risk ratios\">Primary</button>",
            'title="Primary analysis: mean difference (continuous outcome)">Primary</button>',
            html
        )

    # ── 23. NMA variable names ──
    html = html.replace("bempedoicIds", "trialIds")
    html = html.replace("bempData", "trialData")

    # ── 24. Screening relevance regex ──
    # Replace the bempedoic-specific screening regex with topic-specific one
    screen_regex = cfg.get("drug_regex_pattern", drug_lower).replace("\\b", "")
    html = html.replace(
        "[/bempedoic/i, 10, 'Bempedoic acid intervention']",
        f"[/{screen_regex}/i, 10, '{drug} intervention']"
    )

    # ── 25. Catch-all: remaining "bempedoic acid" strings ──
    # First handle occurrences inside JS regex literals where / in drug names would break the regex
    # Pattern: /bempedoic acid.../i  -> need to escape / in the replacement
    drug_lower_regex_safe = drug_lower.replace("/", "\\/")
    drug_regex_safe = drug.replace("/", "\\/")

    # Replace occurrences that are inside JS regex patterns (preceded by / or | in a regex context)
    # These patterns match: /bempedoic acid|... or /\bbempedoic acid\b
    import re as _re
    html = _re.sub(
        r'(/[^/]*?)bempedoic acid([^/]*/)',
        lambda m: m.group(1) + drug_lower_regex_safe + m.group(2),
        html
    )

    # Now safe to do plain string replacements for non-regex contexts
    html = html.replace("bempedoic acid", drug_lower)
    html = html.replace("Bempedoic Acid", drug)
    html = html.replace("bempedoic_acid", storage)

    return html


def main():
    print(f"Reading template: {TEMPLATE_PATH}")
    with open(TEMPLATE_PATH, 'r', encoding='utf-8') as f:
        template = f.read()

    print(f"Template: {len(template.splitlines())} lines, {len(template)} chars")

    for app in APPS:
        filename = app["filename"]
        output_path = os.path.join(OUTPUT_DIR, filename)

        print(f"\nGenerating {filename}...")
        result = transform_template(template, app)

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(result)

        line_count = len(result.splitlines())
        print(f"  -> {output_path} ({line_count} lines, {len(result)} chars)")

        # Basic validation
        div_open = len(re.findall(r'<div[\s>]', result))
        div_close = result.count('</div>')
        script_open = result.count('<script')
        script_close_safe = result.count("${'<'}/script>")
        script_close_real = result.count('</script>')

        print(f"  Div balance: {div_open} open, {div_close} close (delta={div_open - div_close})")
        print(f"  Script tags: {script_open} <script, {script_close_real} </script> (safe escapes: {script_close_safe})")

        # Check no leftover "bempedoic" references
        leftover = len(re.findall(r'bempedoic', result, re.IGNORECASE))
        if leftover > 0:
            print(f"  WARNING: {leftover} leftover 'bempedoic' references!")
        else:
            print(f"  No leftover 'bempedoic' references.")

        # Check unique storage key
        storage_hits = len(re.findall(re.escape(app["storage_key"]), result))
        print(f"  Storage key '{app['storage_key']}' found {storage_hits} times.")

    print("\n=== DONE: 8 apps generated ===")


if __name__ == "__main__":
    main()
