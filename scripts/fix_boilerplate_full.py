#!/usr/bin/env python3
# sentinel:skip-file - developer tool; hardcoded ROOT is intentional (local Finrenone checkout only)
"""Full clone-template boilerplate cleanup across 97+ apps.

Fixes sacubitril/valsartan + HFrEF + PARADIGM-HF text that leaked from the
ARNI_HF template into every derived app. Targets:
  1. Main h2/h3 report headings (va-header h2, nyt-headline h3)
  2. Forest plot caption (nyt-figure-caption)
  3. benchmark-summary + benchmark-footnote paragraph text
  4. Subgroup-plan input value (<input id='p-subgroup'>)
  5. Eligibility table Participants + Intervention rows
  6. Extraction row "Intervention details"
  7. Search query URLs (CT.gov / PubMed / OpenAlex) x2 locations each
  8. Default state protocol object { pop, int, comp, out, subgroup }
  9. Auto-screen note reference to 'sacubitril/valsartan'

Each app gets:
  - drug_short    (e.g. 'T-DXd')
  - drug_display  (e.g. 'Trastuzumab Deruxtecan')
  - pop_brief     (e.g. 'HER2-Low Breast Cancer', for headings)
  - search_term   (e.g. 'trastuzumab deruxtecan')
  - subgroup      (e.g. 'HR status, prior lines, liver metastases')
  - plus the PICO (pop, int, comp, out) already in fix_pico_boilerplate.py

ARNI_HF_REVIEW.html left intact (it is the source template).
"""
import argparse, pathlib, re, sys

ROOT = pathlib.Path(r"C:\Projects\Finrenone")

# (pop_brief, drug_display, drug_short, search_term, subgroup, elig_pop, elig_int_short, pop_full, int_full, comp_full, out_full)
SPEC = {
    "ABLATION_AF_REVIEW.html":             ("Atrial Fibrillation",                  "Catheter Ablation",             "Ablation",        "catheter ablation atrial fibrillation",     "Paroxysmal vs persistent AF, HF presence, age", "Adults with AF",                    "Catheter ablation",                  "Adults with symptomatic atrial fibrillation", "Catheter ablation", "Antiarrhythmic drug therapy", "Recurrent AF or major cardiovascular events"),
    "ACALABRUTINIB_CLL_REVIEW.html":       ("Chronic Lymphocytic Leukemia",          "Acalabrutinib",                 "Acalabrutinib",   "acalabrutinib CLL",                          "del(17p) status, treatment-naive vs R/R, age", "Adults with CLL/SLL",               "Acalabrutinib",                      "Adults with CLL or SLL", "Acalabrutinib", "Chemoimmunotherapy or placebo", "Progression-free survival"),
    "ADC_HER2_ADJUVANT_NMA_REVIEW.html":   ("HER2+ Early Breast Cancer",             "HER2 ADC (adjuvant)",            "HER2 ADC",       "HER2 ADC adjuvant breast cancer",           "HR status, nodal status, residual disease size", "HER2+ early BC post-neoadjuvant", "T-DM1 / T-DXd (adjuvant)",          "HER2+ early breast cancer with residual disease after neoadjuvant", "Trastuzumab emtansine (T-DM1) adjuvant", "Trastuzumab or placebo", "Invasive disease-free survival (iDFS)"),
    "ADC_HER2_LOW_NMA_REVIEW.html":        ("HER2-Low Breast Cancer",                "Trastuzumab Deruxtecan",        "T-DXd",           "trastuzumab deruxtecan HER2-low",           "HR status, prior lines, liver metastases",     "HER2-low metastatic BC",           "T-DXd",                              "HER2-low metastatic breast cancer", "Trastuzumab deruxtecan (T-DXd)", "Physician's-choice chemotherapy", "Progression-free survival (PFS)"),
    "ADC_HER2_NMA_REVIEW.html":            ("HER2+ Metastatic Breast Cancer",        "HER2-Directed ADCs",             "HER2 ADC",       "HER2 ADC metastatic breast cancer",         "Line of therapy, brain mets, HR status",        "HER2+ metastatic BC",              "HER2-directed ADC",                  "HER2+ metastatic breast cancer", "HER2-directed ADC (T-DXd, T-DM1, etc.)", "T-DM1 or chemotherapy", "Progression-free survival (PFS)"),
    "AFLIBERCEPT_HD_REVIEW.html":          ("Neovascular AMD / DME",                 "Aflibercept 8 mg",               "Aflibercept HD", "aflibercept 8 mg nAMD",                     "Baseline BCVA, fluid, treatment-naive vs experienced", "Adults with nAMD or DME",       "Aflibercept 8 mg",                   "Adults with neovascular AMD or DME", "Aflibercept 8 mg (high-dose)", "Aflibercept 2 mg or ranibizumab", "BCVA change (letters)"),
    "ANIFROLUMAB_SLE_REVIEW.html":         ("Systemic Lupus Erythematosus",          "Anifrolumab",                   "Anifrolumab",     "anifrolumab SLE",                            "IFN signature, disease activity, prior biologics", "Adults with SLE",                 "Anifrolumab",                        "Adults with moderate-to-severe systemic lupus erythematosus", "Anifrolumab", "Placebo + standard of care", "BICLA response at week 52"),
    "ANTIAMYLOID_AD_NMA_REVIEW.html":      ("Alzheimer's Disease",                    "Anti-Amyloid Antibodies",       "Anti-Aβ mAb",     "anti-amyloid antibody Alzheimer",           "APOE4 status, baseline CDR, amyloid burden",   "MCI or mild AD with amyloid+",      "Anti-amyloid mAb",                   "Early Alzheimer's disease (MCI or mild AD with confirmed amyloid)", "Anti-amyloid monoclonal antibody", "Placebo", "CDR-SB change at 18 months"),
    "ANTIAMYLOID_AD_REVIEW.html":          ("Alzheimer's Disease",                    "Anti-Amyloid Antibodies",       "Anti-Aβ mAb",     "anti-amyloid antibody Alzheimer",           "APOE4 status, baseline CDR, amyloid burden",   "MCI or mild AD with amyloid+",      "Anti-amyloid mAb",                   "Early Alzheimer's disease (MCI or mild AD with confirmed amyloid)", "Anti-amyloid monoclonal antibody (lecanemab, donanemab)", "Placebo", "CDR-SB change at 18 months"),
    "ANTIPSYCHOTICS_SCHIZO_NMA_REVIEW.html": ("Schizophrenia",                         "Oral Antipsychotics",           "Antipsychotic",   "oral antipsychotic schizophrenia",          "First-episode vs chronic, negative symptoms",  "Adults with acute schizophrenia",   "Oral antipsychotic",                 "Adults with acute schizophrenia", "Oral antipsychotic", "Placebo", "PANSS total / overall symptoms change"),
    "ANTIVEGF_NAMD_NMA_REVIEW.html":       ("Neovascular AMD",                        "Anti-VEGF",                      "Anti-VEGF",       "anti-VEGF neovascular AMD",                 "Baseline BCVA, lesion type, treatment history", "Adults with nAMD",                 "Anti-VEGF",                          "Adults with neovascular age-related macular degeneration", "Anti-VEGF (ranibizumab, aflibercept, faricimab)", "Sham / reference anti-VEGF", "BCVA change (ETDRS letters)"),
    "ARPI_mHSPC_REVIEW.html":              ("Metastatic Hormone-Sensitive Prostate Cancer", "ARPI + ADT",                   "ARPI",            "androgen receptor pathway inhibitor mHSPC", "Volume of disease, M1a/b/c, Gleason score",    "Men with mHSPC",                    "ARPI + ADT",                         "Men with metastatic hormone-sensitive prostate cancer", "Androgen-receptor pathway inhibitor + ADT", "ADT alone", "Overall survival"),
    "ATOPIC_DERM_NMA_REVIEW.html":         ("Atopic Dermatitis",                      "Systemic Immunomodulators",     "Systemic AD tx",  "atopic dermatitis systemic",                "Prior systemic therapy, baseline severity",    "Adults/adolescents with mod-severe AD", "Systemic immunomodulator",       "Adults and adolescents with moderate-to-severe atopic dermatitis", "Systemic immunomodulator (dupilumab, JAKi, etc.)", "Placebo", "EASI75 at 16 weeks"),
    "ATTR_CM_REVIEW.html":                 ("Transthyretin Cardiomyopathy",           "TTR Stabilizers",               "TTR stabilizer",  "transthyretin cardiomyopathy",              "Wild-type vs hereditary, NYHA class, NT-proBNP", "Adults with ATTR-CM",             "TTR stabilizer",                     "Adults with transthyretin amyloid cardiomyopathy", "TTR stabilizer (tafamidis, acoramidis)", "Placebo", "All-cause mortality or CV hospitalization"),
    "BELIMUMAB_SLE_REVIEW.html":           ("Systemic Lupus Erythematosus",           "Belimumab",                     "Belimumab",       "belimumab SLE",                              "Anti-dsDNA status, complement, disease activity", "Adults with seropositive SLE",    "Belimumab",                          "Adults with seropositive systemic lupus erythematosus", "Belimumab", "Placebo + standard of care", "SRI-4 response at week 52"),
    "BEMPEDOIC_ACID_REVIEW.html":          ("Cardiovascular Prevention",              "Bempedoic Acid",                "Bempedoic acid",  "bempedoic acid cardiovascular",             "Statin status, baseline LDL-C, ASCVD history", "Adults with ASCVD or high risk",    "Bempedoic acid",                     "Adults with ASCVD (statin-intolerant or statin-treated)", "Bempedoic acid", "Placebo", "MACE-4 composite"),
    "BIOLOGIC_ASTHMA_REVIEW.html":         ("Severe Asthma",                          "Asthma Biologics",              "Biologic",        "severe asthma biologic",                    "Blood eosinophils, IgE, exacerbation history", "Adults with severe asthma",        "Asthma biologic",                    "Adults with severe asthma", "Biologic (mepolizumab, benralizumab, dupilumab)", "Placebo", "Annual exacerbation rate"),
    "BTKI_CLL_NMA_REVIEW.html":            ("Chronic Lymphocytic Leukemia",           "BTK Inhibitors",                "BTKi",            "BTK inhibitor CLL",                          "del(17p), TP53, IGHV, prior lines",             "Adults with CLL/SLL",              "BTK inhibitor",                      "Adults with CLL or SLL", "BTK inhibitor (ibrutinib, acalabrutinib, zanubrutinib)", "BTK comparator or chemoimmunotherapy", "Progression-free survival"),
    "CAB_PREP_HIV_REVIEW.html":            ("HIV Pre-Exposure Prophylaxis",           "Long-Acting Cabotegravir",      "CAB-LA",          "cabotegravir PrEP HIV",                     "Population (MSM/TGW/cis-women), adherence",     "Adults at risk of HIV",            "CAB-LA",                             "Adults at risk of HIV acquisition", "Long-acting cabotegravir (PrEP)", "Daily oral TDF/FTC", "HIV incidence"),
    "CANGRELOR_PCI_REVIEW.html":           ("Percutaneous Coronary Intervention",     "Cangrelor",                     "Cangrelor",       "cangrelor PCI",                              "Stable vs ACS, clopidogrel-naive vs pre-treated", "Adults undergoing PCI",           "Cangrelor",                          "Adults undergoing PCI", "Cangrelor", "Clopidogrel loading dose", "Death, MI, ischemia-driven revasc or stent thrombosis at 48 h"),
    "CARDIORENAL_DKD_NMA_REVIEW.html":     ("Diabetic Kidney Disease",                "Cardiorenal Agents",            "SGLT2i/MRA/GLP1", "diabetic kidney disease cardiorenal",       "eGFR strata, UACR, diabetes duration",          "Adults with T2D + CKD",            "SGLT2i / MRA / GLP-1",               "Adults with type 2 diabetes and CKD", "SGLT2i / finerenone / GLP-1 RA", "Placebo + standard RAS blockade", "Renal composite (failure, eGFR decline, renal death)"),
    "CART_DLBCL_REVIEW.html":              ("Large B-Cell Lymphoma",                  "CAR-T Therapy",                 "CAR-T",           "CAR-T lymphoma",                             "Age, prior therapy, LDH, IPI score",            "Adults with R/R LBCL",             "CAR-T",                              "Adults with relapsed/refractory large B-cell lymphoma", "CAR-T cell therapy (axi-cel, liso-cel)", "Standard-of-care 2nd-line therapy", "Event-free survival"),
    "CART_MM_REVIEW.html":                 ("Multiple Myeloma",                       "CAR-T Therapy",                 "CAR-T",           "CAR-T multiple myeloma",                     "Lines of prior therapy, high-risk cyto, refractory status", "Adults with R/R MM",      "CAR-T",                              "Adults with relapsed/refractory multiple myeloma", "CAR-T cell therapy (cilta-cel, ide-cel)", "Physician's-choice regimen", "Progression-free survival"),
    "CBD_SEIZURE_REVIEW.html":             ("Refractory Epilepsy",                    "Cannabidiol",                   "CBD",             "cannabidiol Dravet Lennox-Gastaut",         "Syndrome (Dravet vs LGS), age, CLB co-therapy", "Children/adolescents with Dravet/LGS", "Cannabidiol",                      "Children / adolescents with Dravet or Lennox-Gastaut syndrome", "Cannabidiol", "Placebo", "Convulsive seizure frequency reduction"),
    "CDK46_MBC_REVIEW.html":               ("HR+ HER2- Metastatic Breast Cancer",     "CDK4/6 Inhibitors",             "CDK4/6i",         "CDK4/6 inhibitor metastatic breast cancer", "Endocrine-sensitive vs resistant, menopausal status, visceral disease", "HR+/HER2- MBC 1L", "CDK4/6i + endocrine tx",             "HR+/HER2- metastatic breast cancer (1L)", "CDK4/6 inhibitor + endocrine therapy", "Endocrine therapy alone", "Progression-free survival"),
    "CD_BIOLOGICS_NMA_REVIEW.html":        ("Crohn's Disease",                        "CD Biologics",                  "CD biologic",     "Crohn biologic",                             "Biologic-naive vs experienced, disease duration, phenotype", "Adults with mod-severe CD", "Biologic / small molecule",         "Adults with moderate-to-severe Crohn's disease", "Biologic or small molecule", "Placebo", "Clinical remission at induction"),
    "CFTR_CF_REVIEW.html":                 ("Cystic Fibrosis",                        "CFTR Modulators",               "CFTR modulator",  "CFTR modulator cystic fibrosis",            "Genotype (F508del het/hom), age, baseline ppFEV1", "Patients with CF",              "CFTR modulator",                     "Patients with cystic fibrosis (F508del-eligible)", "CFTR modulator (ELX/TEZ/IVA, TEZ/IVA)", "Placebo", "Absolute ppFEV1 change"),
    "CFTR_MODULATORS_NMA_REVIEW.html":     ("Cystic Fibrosis",                        "CFTR Modulators",               "CFTR modulator",  "CFTR modulator cystic fibrosis network",    "Genotype, age group, modulator generation",    "Patients with CF",                  "CFTR modulator (any)",               "Patients with cystic fibrosis", "CFTR modulator (any generation)", "Placebo", "ppFEV1 and pulmonary exacerbation rate"),
    "CGRP_MIGRAINE_NMA_REVIEW.html":       ("Migraine Prevention",                    "Anti-CGRP Antibodies",          "CGRP mAb",        "anti-CGRP migraine",                        "Episodic vs chronic migraine, prior preventives, medication overuse", "Adults with migraine", "CGRP mAb",                           "Adults with episodic or chronic migraine", "Anti-CGRP monoclonal antibody", "Placebo", "Monthly migraine days reduction"),
    "CGRP_MIGRAINE_REVIEW.html":           ("Migraine Prevention",                    "Anti-CGRP Antibodies",          "CGRP mAb",        "anti-CGRP migraine",                        "Episodic vs chronic, prior preventives, MoH",  "Adults with migraine",              "CGRP mAb",                           "Adults with episodic or chronic migraine", "Anti-CGRP monoclonal antibody (erenumab, fremanezumab, galcanezumab, eptinezumab)", "Placebo", "Monthly migraine days reduction"),
    "COLCHICINE_CVD_REVIEW.html":          ("Cardiovascular Prevention",              "Low-Dose Colchicine",           "Colchicine",      "colchicine cardiovascular",                  "Stable CAD vs post-MI, diabetes, CRP level",   "Adults with stable CAD or post-MI", "Low-dose colchicine",               "Adults with stable CAD or recent MI", "Low-dose colchicine (0.5 mg)", "Placebo", "MACE composite"),
    "COPD_TRIPLE_REVIEW.html":             ("Chronic Obstructive Pulmonary Disease",  "Triple Therapy",                "Triple ICS/LABA/LAMA", "triple therapy COPD",                  "Eosinophils, exacerbation history, GOLD stage", "Adults with COPD + exacerbation hx", "Triple (ICS/LABA/LAMA)",          "Adults with COPD and exacerbation history", "Triple therapy (ICS/LABA/LAMA)", "Dual ICS/LABA or LAMA/LABA", "Moderate/severe exacerbation rate"),
    "COVID_ORAL_ANTIVIRALS_REVIEW.html":   ("COVID-19 Outpatient Care",               "Oral Antivirals",               "Oral antiviral",  "COVID-19 oral antiviral",                   "Vaccination status, risk factors, time from symptom onset", "Outpatients with COVID-19 at risk", "Oral antiviral",                    "Outpatients with COVID-19 at risk for severe disease", "Oral antiviral (nirmatrelvir/r, molnupiravir)", "Placebo", "Hospitalization or death"),
    "DOAC_AF_NMA_REVIEW.html":             ("Atrial Fibrillation",                    "DOACs",                         "DOAC",            "DOAC atrial fibrillation network",          "CHA2DS2-VASc, HAS-BLED, age, CrCl",            "Adults with NVAF",                  "DOAC",                               "Adults with non-valvular atrial fibrillation", "DOAC (apixaban, dabigatran, edoxaban, rivaroxaban)", "Warfarin", "Stroke or systemic embolism"),
    "DOAC_AF_REVIEW.html":                 ("Atrial Fibrillation",                    "DOACs",                         "DOAC",            "DOAC atrial fibrillation",                  "CHA2DS2-VASc, HAS-BLED, age, CrCl",            "Adults with NVAF",                  "DOAC",                               "Adults with non-valvular atrial fibrillation", "Direct oral anticoagulant (DOAC)", "Warfarin", "Stroke or systemic embolism"),
    "DOAC_CANCER_VTE_REVIEW.html":         ("Cancer-Associated VTE",                  "DOACs (Cancer)",                "DOAC",            "DOAC cancer-associated VTE",                "Cancer type (GI vs other), bleeding risk, platelets", "Patients with cancer-associated VTE", "DOAC",                          "Patients with cancer-associated VTE", "DOAC (apixaban, edoxaban, rivaroxaban)", "LMWH (dalteparin)", "Recurrent VTE"),
    "DOAC_VTE_NMA_REVIEW.html":            ("Venous Thromboembolism",                 "DOACs",                         "DOAC",            "DOAC venous thromboembolism",               "Provoked vs unprovoked, cancer status, renal function", "Adults with acute VTE",        "DOAC",                               "Adults with acute venous thromboembolism", "Direct oral anticoagulant", "Vitamin K antagonist", "VTE recurrence"),
    "DUPILUMAB_AD_REVIEW.html":            ("Atopic Dermatitis",                      "Dupilumab",                     "Dupilumab",       "dupilumab atopic dermatitis",               "Baseline EASI, age, allergic comorbidities",   "Mod-severe AD (adults/adolescents)", "Dupilumab",                        "Adults and adolescents with moderate-to-severe atopic dermatitis", "Dupilumab", "Placebo", "EASI75 at 16 weeks"),
    "DUPILUMAB_COPD_REVIEW.html":          ("COPD with Type-2 Inflammation",          "Dupilumab",                     "Dupilumab",       "dupilumab COPD",                             "Blood eosinophils, smoking status, ICS use",   "COPD + T2 inflammation",            "Dupilumab",                          "Adults with COPD and type-2 inflammation", "Dupilumab", "Placebo", "Annual moderate-severe exacerbation rate"),
    "ESKETAMINE_TRD_REVIEW.html":          ("Treatment-Resistant Depression",         "Esketamine",                    "Esketamine",      "esketamine treatment-resistant depression", "Prior antidepressant failures, suicidality",    "Adults with TRD",                  "Esketamine",                         "Adults with treatment-resistant depression", "Intranasal esketamine + oral antidepressant", "Placebo spray + oral antidepressant", "MADRS change"),
    "EVT_BASILAR_REVIEW.html":             ("Basilar-Artery Stroke",                  "Endovascular Thrombectomy",     "EVT",             "endovascular thrombectomy basilar stroke",  "Time from onset, NIHSS, posterior-circulation ASPECTS", "Basilar occlusion within 12-24 h", "EVT",                              "Adults with acute basilar-artery occlusion", "Endovascular thrombectomy", "Best medical management", "mRS 0-3 at 90 days"),
    "EVT_EXTENDED_WINDOW_REVIEW.html":     ("Extended-Window Stroke EVT",             "Endovascular Thrombectomy",     "EVT",             "endovascular thrombectomy extended window", "Time window, imaging selection, age, NIHSS",   "Anterior-circulation stroke 6-24h",  "EVT",                               "Adults with anterior-circulation stroke in 6-24 h window", "Endovascular thrombectomy", "Medical management", "Functional independence (mRS 0-2) at 90 days"),
    "EVT_LARGECORE_REVIEW.html":           ("Large-Core Stroke",                      "Endovascular Thrombectomy",     "EVT",             "endovascular thrombectomy large core",      "ASPECTS 3-5, infarct volume, NIHSS",           "Large ischemic core stroke",         "EVT",                               "Adults with large-core ischemic stroke (ASPECTS 3-5)", "Endovascular thrombectomy", "Medical management", "mRS 0-3 at 90 days"),
    "FARICIMAB_NAMD_REVIEW.html":          ("Neovascular AMD",                        "Faricimab",                     "Faricimab",       "faricimab nAMD",                             "Baseline BCVA, CRT, treatment-naive vs experienced", "Adults with nAMD",             "Faricimab",                          "Adults with neovascular AMD", "Faricimab", "Aflibercept", "BCVA change (ETDRS letters)"),
    "FENFLURAMINE_SEIZURE_REVIEW.html":    ("Refractory Epilepsy",                    "Fenfluramine",                  "Fenfluramine",    "fenfluramine Dravet seizure",               "Age, baseline seizure frequency, co-medications", "Children/adolescents with Dravet", "Fenfluramine",                      "Children / adolescents with Dravet syndrome", "Fenfluramine", "Placebo", "Convulsive seizure frequency reduction"),
    "FEZOLINETANT_VMS_REVIEW.html":        ("Vasomotor Symptoms",                     "Fezolinetant",                  "Fezolinetant",    "fezolinetant vasomotor menopause",          "Baseline VMS frequency, menopause duration",    "Postmenopausal women with VMS",    "Fezolinetant",                       "Postmenopausal women with moderate-severe vasomotor symptoms", "Fezolinetant", "Placebo", "VMS frequency reduction"),
    "FINERENONE_REVIEW.html":              ("CKD + Type 2 Diabetes",                  "Finerenone",                    "Finerenone",      "finerenone CKD T2D",                        "eGFR, UACR, baseline HbA1c",                   "Adults with CKD + T2D",             "Finerenone",                         "Adults with CKD and type 2 diabetes", "Finerenone", "Placebo", "CV composite (MACE) or renal composite"),
    "GLP1_CVOT_NMA_REVIEW.html":           ("Type 2 Diabetes - CVOT",                 "GLP-1 Receptor Agonists",       "GLP-1 RA",        "GLP-1 receptor agonist cardiovascular outcomes", "Baseline CV risk, diabetes duration",    "Adults with T2D at CV risk",       "GLP-1 RA",                           "Adults with type 2 diabetes at elevated cardiovascular risk", "GLP-1 receptor agonist", "Placebo", "3-point MACE"),
    "GLP1_CVOT_REVIEW.html":               ("Type 2 Diabetes - CVOT",                 "GLP-1 Receptor Agonists",       "GLP-1 RA",        "GLP-1 receptor agonist cardiovascular",     "Baseline CV risk, diabetes duration",          "Adults with T2D at CV risk",        "GLP-1 RA",                           "Adults with type 2 diabetes at elevated cardiovascular risk", "GLP-1 receptor agonist", "Placebo", "3-point MACE"),
    "HIGH_EFFICACY_MS_REVIEW.html":        ("Multiple Sclerosis",                     "High-Efficacy DMTs",            "HE DMT",          "high-efficacy DMT multiple sclerosis",       "Baseline EDSS, relapse rate, MRI activity",    "Adults with RRMS",                  "High-efficacy DMT",                  "Adults with relapsing-remitting multiple sclerosis", "High-efficacy DMT (ocrelizumab, natalizumab, etc.)", "Interferon or moderate DMT", "Annualized relapse rate"),
    "IL23_PSORIASIS_REVIEW.html":          ("Psoriasis",                              "IL-23 Inhibitors",              "IL-23i",          "IL-23 inhibitor psoriasis",                 "Prior biologic, baseline PASI, BMI",           "Mod-severe plaque psoriasis",        "IL-23 inhibitor",                   "Adults with moderate-to-severe plaque psoriasis", "IL-23 inhibitor (risankizumab, guselkumab, tildrakizumab)", "Placebo or comparator biologic", "PASI90 at week 16"),
    "IL_PSORIASIS_NMA_REVIEW.html":        ("Psoriasis",                              "Psoriasis Biologics",           "Biologic",        "psoriasis biologic network",                "Biologic-naive vs experienced, PASI, BMI",     "Mod-severe plaque psoriasis",        "Systemic biologic",                 "Adults with moderate-to-severe plaque psoriasis", "Systemic biologic / small molecule", "Placebo", "PASI90 at induction"),
    "INCLISIRAN_REVIEW.html":              ("LDL Cholesterol Lowering",               "Inclisiran",                    "Inclisiran",      "inclisiran LDL",                             "Baseline LDL-C, statin status, ASCVD history", "ASCVD or HeFH on max statin",        "Inclisiran",                        "Adults with ASCVD or heterozygous FH on maximally tolerated statin", "Inclisiran", "Placebo", "LDL-C percent change"),
    "INCRETINS_T2D_NMA_REVIEW.html":       ("Type 2 Diabetes - Glycemic Control",     "GLP-1 / DPP-4",                  "Incretin",        "GLP-1 DPP-4 type 2 diabetes",               "Baseline HbA1c, background metformin, BMI",     "Adults with T2D",                   "GLP-1 RA / DPP-4i",                 "Adults with type 2 diabetes", "GLP-1 RA or DPP-4 inhibitor", "Placebo or other glucose-lowering agent", "HbA1c change"),
    "INCRETIN_HFpEF_REVIEW.html":          ("HFpEF + Obesity",                        "Incretin-Based Therapy",        "Incretin",        "incretin HFpEF obesity",                    "Baseline KCCQ, BMI, diabetes status",           "HFpEF + obesity",                  "Semaglutide / tirzepatide",         "Adults with HFpEF and obesity", "Semaglutide or tirzepatide", "Placebo", "KCCQ-CSS change"),
    "INSULIN_ICODEC_REVIEW.html":          ("Type 2 Diabetes",                        "Once-Weekly Insulin Icodec",   "Icodec",          "insulin icodec type 2 diabetes",            "Baseline HbA1c, prior insulin use",            "Adults with T2D",                   "Insulin icodec QW",                 "Adults with type 2 diabetes", "Once-weekly insulin icodec", "Daily basal insulin", "HbA1c change (non-inferiority)"),
    "INTENSIVE_BP_REVIEW.html":            ("Intensive BP Control",                   "Intensive BP Targeting",        "Intensive BP",    "intensive blood pressure control",          "Age, CKD, diabetes, baseline SBP",             "Adults at elevated CV risk",         "Intensive BP (<120-130)",           "Adults at elevated cardiovascular risk", "Intensive BP control (SBP < 120-130)", "Standard BP control (SBP < 140)", "MACE composite"),
    "IO_CHEMO_NSCLC_1L_REVIEW.html":       ("Advanced NSCLC (1L)",                    "IO + Chemotherapy",             "IO+chemo",        "immunotherapy chemotherapy NSCLC 1L",       "Histology, PD-L1 status, smoking",              "Advanced NSCLC 1L",                 "PD-(L)1 + chemo",                   "Adults with advanced NSCLC (1L)", "Anti-PD-(L)1 + chemotherapy", "Chemotherapy alone", "Overall survival"),
    "IV_IRON_HF_REVIEW.html":              ("Heart Failure with Iron Deficiency",     "IV Iron",                       "IV FCM",          "intravenous iron heart failure",            "Baseline TSAT, ferritin, NYHA class",           "HFrEF + iron deficiency",          "IV FCM",                            "Adults with HFrEF and iron deficiency", "IV ferric carboxymaltose", "Placebo", "CV death or HF hospitalization"),
    "JAKI_AD_REVIEW.html":                 ("Atopic Dermatitis",                      "JAK Inhibitors (AD)",           "JAKi",            "JAK inhibitor atopic dermatitis",           "Prior systemic therapy, EASI, age",             "Mod-severe AD",                     "JAK inhibitor",                     "Adults with moderate-to-severe atopic dermatitis", "JAK inhibitor (upadacitinib, abrocitinib)", "Placebo", "EASI75 at 16 weeks"),
    "JAKI_RA_NMA_REVIEW.html":             ("Rheumatoid Arthritis",                   "JAK Inhibitors (RA)",           "JAKi",            "JAK inhibitor rheumatoid arthritis",        "Prior DMARD, concomitant MTX, age",             "Mod-severe RA",                     "JAK inhibitor",                     "Adults with moderate-to-severe rheumatoid arthritis", "JAK inhibitor", "Placebo or active comparator", "ACR20 at 12-24 weeks"),
    "JAK_RA_REVIEW.html":                  ("Rheumatoid Arthritis",                   "JAK Inhibitors",                "JAKi",            "JAK inhibitor rheumatoid arthritis",        "Prior DMARD, concomitant MTX, age",             "Mod-severe RA",                     "JAK inhibitor",                     "Adults with moderate-to-severe rheumatoid arthritis", "JAK inhibitor (tofacitinib, baricitinib, upadacitinib, filgotinib)", "Placebo", "ACR20 at 12-24 weeks"),
    "JAK_UC_REVIEW.html":                  ("Ulcerative Colitis",                     "JAK Inhibitors",                "JAKi",            "JAK inhibitor ulcerative colitis",          "Biologic-naive vs experienced, Mayo score",     "Mod-severe UC",                     "JAK inhibitor",                     "Adults with moderate-to-severe ulcerative colitis", "JAK inhibitor (tofacitinib, upadacitinib)", "Placebo", "Clinical remission at 8 weeks"),
    "KARXT_SCZ_REVIEW.html":               ("Schizophrenia",                          "KarXT",                         "KarXT",           "xanomeline trospium KarXT schizophrenia",   "Acute vs maintenance, baseline PANSS",          "Adults with schizophrenia",         "KarXT",                             "Adults with acute schizophrenia", "Xanomeline + trospium (KarXT)", "Placebo", "PANSS total change at week 5"),
    "LENACAPAVIR_PREP_REVIEW.html":        ("HIV Pre-Exposure Prophylaxis",           "Lenacapavir",                   "Lenacapavir",     "lenacapavir PrEP",                          "Population (MSM/TGW/cis women), adherence",     "Adults at risk of HIV",            "Lenacapavir SC Q26W",                "Adults at risk of HIV acquisition", "Lenacapavir SC twice-yearly", "Daily oral TDF/FTC", "HIV incidence"),
    "LIPID_HUB_REVIEW.html":               ("Lipid Lowering",                         "Lipid-Lowering Therapy",        "LLT",             "lipid-lowering therapy",                    "Baseline LDL-C, statin intensity, ASCVD",      "ASCVD or high CV risk",             "Lipid-lowering tx",                 "Adults with ASCVD or high cardiovascular risk", "Lipid-lowering therapy (statin, PCSK9i, etc.)", "Placebo or less-intensive therapy", "MACE composite"),
    "LU_PSMA_MCRPC_REVIEW.html":           ("Metastatic CRPC (PSMA+)",                "177Lu-PSMA-617",                "Lu-PSMA",         "177Lu-PSMA-617 mCRPC",                      "Prior taxane, PSMA PET uptake, visceral disease", "PSMA+ mCRPC post-ARPI and taxane", "177Lu-PSMA-617",                    "Men with PSMA+ mCRPC post-ARPI and taxane", "177Lu-PSMA-617 + standard of care", "Standard of care alone", "Overall survival"),
    "MAVACAMTEN_HCM_REVIEW.html":          ("Obstructive HCM",                        "Mavacamten",                    "Mavacamten",      "mavacamten hypertrophic cardiomyopathy",    "LVOT gradient, NYHA, age",                      "Symptomatic oHCM",                  "Mavacamten",                        "Adults with symptomatic obstructive HCM", "Mavacamten", "Placebo", "Composite functional/pVO2 response"),
    "MIRIKIZUMAB_UC_REVIEW.html":          ("Ulcerative Colitis",                     "Mirikizumab",                   "Mirikizumab",     "mirikizumab ulcerative colitis",            "Biologic-naive vs experienced, Mayo score",     "Mod-severe UC",                     "Mirikizumab",                       "Adults with moderate-to-severe ulcerative colitis", "Mirikizumab", "Placebo", "Clinical remission at induction"),
    "MITRAL_FUNCMR_REVIEW.html":           ("Functional Mitral Regurgitation",        "TEER for MR",                   "M-TEER",          "MitraClip functional mitral regurgitation", "LVEF, regurgitant volume, GDMT optimization",   "Severe secondary MR",               "M-TEER + GDMT",                     "Adults with severe secondary mitral regurgitation", "Transcatheter mitral edge-to-edge repair + GDMT", "GDMT alone", "CV death or HF hospitalization"),
    "NIRSEVIMAB_INFANT_RSV_REVIEW.html":   ("Infant RSV Prevention",                  "Nirsevimab",                    "Nirsevimab",      "nirsevimab infant RSV",                     "Gestational age, birth season, comorbidities",  "Healthy term/late-preterm infants", "Nirsevimab",                        "Healthy term / late-preterm infants", "Nirsevimab (single IM dose)", "Placebo", "Medically-attended RSV LRTI"),
    "PARP_ARPI_MCRPC_REVIEW.html":         ("Metastatic CRPC (1L)",                   "PARP + ARPI",                   "PARP+ARPI",       "PARP ARPI mCRPC 1L",                        "HRR status, visceral disease, prior ADT",       "mCRPC 1L",                          "PARP + ARPI",                       "Men with mCRPC (1L)", "PARP inhibitor + androgen-receptor pathway inhibitor", "ARPI + placebo", "Radiographic progression-free survival"),
    "PARP_OVARIAN_REVIEW.html":            ("Advanced Ovarian Cancer",                "PARP Inhibitors",               "PARPi",           "PARP inhibitor ovarian cancer",             "BRCA status, HRD score, prior response",        "Advanced ovarian cancer",           "PARP inhibitor",                    "Women with advanced ovarian cancer (maintenance)", "PARP inhibitor (olaparib, niraparib)", "Placebo", "Progression-free survival"),
    "PATISIRAN_POLYNEUROPATHY_REVIEW.html": ("hATTR Polyneuropathy",                   "Patisiran",                     "Patisiran",       "patisiran hereditary transthyretin",        "V30M vs other mutations, baseline mNIS+7",      "hATTR-PN adults",                   "Patisiran",                         "Adults with hereditary transthyretin amyloidosis with polyneuropathy", "Patisiran", "Placebo", "mNIS+7 change at 18 months"),
    "PBC_PPAR_REVIEW.html":                ("Primary Biliary Cholangitis",            "PPAR Agonists",                 "PPAR agonist",    "seladelpar elafibranor PBC",                "Baseline ALP, bilirubin, UDCA response",        "PBC inadequate UDCA response",       "PPAR agonist",                      "Adults with primary biliary cholangitis with inadequate UDCA response", "PPAR agonist (elafibranor, seladelpar)", "Placebo + UDCA", "Biochemical response (composite ALP / bilirubin)"),
    "PCSK9_LIPID_NMA_REVIEW.html":         ("PCSK9 Therapy (Lipid)",                  "PCSK9 Inhibitors",              "PCSK9i",          "PCSK9 inhibitor network",                   "ASCVD, baseline LDL-C, statin intensity",       "ASCVD or very high CV risk",        "PCSK9i",                            "Adults with ASCVD or very-high cardiovascular risk", "PCSK9 inhibitor (alirocumab, evolocumab, inclisiran)", "Placebo", "MACE or LDL-C change"),
    "PCSK9_REVIEW.html":                   ("PCSK9 Therapy (CV Outcomes)",            "PCSK9 Inhibitors",              "PCSK9i",          "PCSK9 inhibitor cardiovascular",            "ASCVD, baseline LDL-C, statin intensity",       "ASCVD or HeFH",                     "PCSK9i",                            "Adults with ASCVD or heterozygous FH", "PCSK9 inhibitor", "Placebo", "MACE composite"),
    "PEGCETACOPLAN_GA_REVIEW.html":        ("Geographic Atrophy (AMD)",               "Pegcetacoplan",                 "Pegcetacoplan",   "pegcetacoplan geographic atrophy",          "Subfoveal vs extrafoveal, baseline GA area",    "GA secondary to AMD",               "Intravitreal pegcetacoplan",        "Adults with geographic atrophy secondary to AMD", "Intravitreal pegcetacoplan", "Sham", "GA lesion-area change"),
    "RENAL_DENERV_REVIEW.html":            ("Uncontrolled Hypertension",              "Renal Denervation",             "RDN",             "renal denervation hypertension",            "Baseline SBP, med adherence, eGFR",             "Uncontrolled HTN on meds",          "Renal denervation",                 "Adults with uncontrolled hypertension on medication", "Catheter-based renal denervation", "Sham procedure", "24-h ambulatory SBP change"),
    "RISANKIZUMAB_CD_REVIEW.html":         ("Crohn's Disease",                        "Risankizumab",                  "Risankizumab",    "risankizumab Crohn",                         "Biologic-naive vs experienced, disease activity", "Mod-severe CD",                    "Risankizumab",                       "Adults with moderate-to-severe Crohn's disease", "Risankizumab", "Placebo", "Clinical remission at induction"),
    "RIVAROXABAN_VASC_REVIEW.html":        ("Vascular Protection",                    "Rivaroxaban 2.5 mg + ASA",     "Riva + ASA",     "rivaroxaban vascular protection",            "Baseline CAD vs PAD, diabetes, renal fx",       "Stable ASCVD or PAD",               "Riva 2.5 mg + ASA",                 "Adults with stable ASCVD or PAD", "Rivaroxaban 2.5 mg BID + aspirin", "Aspirin alone", "MACE composite"),
    "ROMOSOZUMAB_OP_REVIEW.html":          ("Osteoporosis",                           "Romosozumab",                   "Romosozumab",     "romosozumab osteoporosis",                  "Prior vertebral fracture, BMD T-score, age",    "Postmenopausal osteoporosis",       "Romosozumab",                       "Postmenopausal women with osteoporosis", "Romosozumab", "Alendronate or placebo", "New vertebral fracture"),
    "RSV_VACCINE_OLDER_REVIEW.html":       ("RSV Prevention (Older Adults)",          "RSV Vaccines",                  "RSV vaccine",     "RSV vaccine older adult",                   "Age, comorbidities, prior vaccination",         "Adults >=60",                       "RSV prefusion-F vaccine",            "Adults aged >=60 years", "RSV prefusion-F vaccine", "Placebo", "RSV-associated lower respiratory tract disease"),
    "SEMAGLUTIDE_OBESITY_REVIEW.html":     ("Obesity + CV Disease",                   "Semaglutide 2.4 mg",            "Semaglutide",     "semaglutide obesity cardiovascular",        "Baseline BMI, CVD status, sex",                 "Overweight/obese + CVD (no DM)",    "Semaglutide 2.4 mg",                "Adults with overweight/obesity and established CVD (without diabetes)", "Semaglutide 2.4 mg weekly", "Placebo", "3-point MACE"),
    "SEVERE_ASTHMA_NMA_REVIEW.html":       ("Severe Eosinophilic Asthma",             "Severe-Asthma Biologics",       "Asthma biologic", "severe asthma biologic",                    "Blood eosinophils, IgE, exacerbation history",  "Severe eos asthma",                 "Biologic",                          "Adults with severe eosinophilic asthma", "Biologic (mepolizumab, benralizumab, dupilumab, tezepelumab)", "Placebo", "Annual exacerbation rate"),
    "SGLT2I_HF_NMA_REVIEW.html":           ("Heart Failure",                          "SGLT2 Inhibitors",              "SGLT2i",          "SGLT2 inhibitor heart failure",             "EF strata, diabetes status, NYHA",              "HF across EF spectrum",             "SGLT2i",                            "Adults with heart failure across EF spectrum", "SGLT2 inhibitor", "Placebo", "CV death or HF hospitalization"),
    "SGLT2_CKD_REVIEW.html":               ("Chronic Kidney Disease",                 "SGLT2 Inhibitors (CKD)",        "SGLT2i",          "SGLT2 inhibitor CKD",                       "Diabetes status, eGFR strata, UACR",            "Adults with CKD",                   "SGLT2i",                            "Adults with CKD (with or without type 2 diabetes)", "SGLT2 inhibitor (dapagliflozin, empagliflozin)", "Placebo", "Renal composite"),
    "SGLT2_HF_REVIEW.html":                ("Heart Failure",                          "SGLT2 Inhibitors",              "SGLT2i",          "SGLT2 inhibitor heart failure",             "EF strata, diabetes status, NYHA",              "Adults with HF",                    "SGLT2i",                            "Adults with heart failure", "SGLT2 inhibitor", "Placebo", "CV death or HF hospitalization"),
    "SGLT2_MACE_CVOT_REVIEW.html":         ("Type 2 Diabetes - CVOT",                 "SGLT2 Inhibitors",              "SGLT2i",          "SGLT2 inhibitor MACE CVOT",                 "Baseline CV risk, diabetes duration",           "T2D at CV risk",                    "SGLT2i",                            "Adults with type 2 diabetes at cardiovascular risk", "SGLT2 inhibitor", "Placebo", "3-point MACE"),
    "SOTAGLIFLOZIN_HF_REVIEW.html":        ("Worsening HF",                           "Sotagliflozin",                 "Sotagliflozin",   "sotagliflozin heart failure",               "Diabetes status, EF, NT-proBNP",                 "T2D recently hospitalized for HF", "Sotagliflozin",                      "Adults with T2D recently hospitalized for worsening HF", "Sotagliflozin", "Placebo", "CV death, HHF, or urgent HF visit"),
    "TAVR_LOWRISK_REVIEW.html":            ("Aortic Stenosis (Low Risk)",             "TAVR vs SAVR",                  "TAVR",            "TAVR low-risk aortic stenosis",             "STS score, anatomy, access site",              "Severe AS low risk",               "TAVR",                              "Adults with severe aortic stenosis at low surgical risk", "TAVR", "Surgical aortic valve replacement", "Death, stroke, or rehospitalization at 1 yr"),
    "TDXD_HER2LOW_BC_REVIEW.html":         ("HER2-Low Breast Cancer",                 "Trastuzumab Deruxtecan",        "T-DXd",           "trastuzumab deruxtecan HER2-low",           "HR status, prior lines, liver metastases",      "HER2-low metastatic BC",           "T-DXd",                             "HER2-low metastatic breast cancer", "Trastuzumab deruxtecan (T-DXd)", "Physician's-choice chemotherapy", "Progression-free survival"),
    "TIRZEPATIDE_OBESITY_REVIEW.html":     ("Obesity (No Diabetes)",                  "Tirzepatide",                   "Tirzepatide",     "tirzepatide obesity",                       "Baseline BMI, CV risk factors, sex",            "Overweight/obese no DM",            "Tirzepatide",                       "Adults with overweight/obesity without diabetes", "Tirzepatide", "Placebo", "Body-weight percent change"),
    "TIRZEPATIDE_T2D_REVIEW.html":         ("Type 2 Diabetes - Glycemic",             "Tirzepatide",                   "Tirzepatide",     "tirzepatide type 2 diabetes",               "Baseline HbA1c, background therapy, BMI",       "Adults with T2D",                   "Tirzepatide",                       "Adults with type 2 diabetes", "Tirzepatide", "Semaglutide or placebo", "HbA1c change"),
    "TNK_VS_TPA_STROKE_REVIEW.html":       ("Acute Ischemic Stroke",                  "Tenecteplase vs Alteplase",     "TNK",             "tenecteplase alteplase stroke",             "Time from onset, NIHSS, eligibility for EVT",   "Acute ischemic stroke <4.5 h",     "Tenecteplase",                      "Adults with acute ischemic stroke within 4.5 h", "Tenecteplase", "Alteplase", "mRS 0-1 at 90 days"),
    "UC_BIOLOGICS_NMA_REVIEW.html":        ("Ulcerative Colitis",                     "UC Biologics",                  "UC biologic",     "ulcerative colitis biologic network",        "Biologic-naive vs experienced, Mayo score",     "Mod-severe UC",                     "Biologic / small molecule",         "Adults with moderate-to-severe ulcerative colitis", "Biologic or small molecule", "Placebo", "Clinical remission at induction"),
    "UPADACITINIB_CD_REVIEW.html":         ("Crohn's Disease",                        "Upadacitinib",                  "Upadacitinib",    "upadacitinib Crohn",                         "Biologic-naive vs experienced, disease activity", "Mod-severe CD",                    "Upadacitinib",                      "Adults with moderate-to-severe Crohn's disease", "Upadacitinib", "Placebo", "Clinical remission at induction"),
    "VENETOCLAX_AML_REVIEW.html":          ("AML (Ineligible for Intensive Chemo)",   "Venetoclax + Azacitidine",      "Ven + aza",       "venetoclax azacitidine AML",                "Age, cytogenetic risk, FLT3/IDH mutation",      "Newly-diagnosed AML unfit",        "Ven + aza",                         "Adults with newly-diagnosed AML ineligible for intensive chemo", "Venetoclax + azacitidine", "Placebo + azacitidine", "Overall survival"),
}


def apply_to_file(path: pathlib.Path, spec: tuple, dry_run: bool) -> str:
    (pop_brief, drug_display, drug_short, search_term, subgroup,
     elig_pop, elig_int_short, pop_full, int_full, comp_full, out_full) = spec

    raw = path.read_bytes()
    crlf = b"\r\n" in raw
    text = raw.decode("utf-8")

    original = text
    drug_lower = drug_short.lower()

    # -------- Main report headings --------
    text = re.sub(
        r'<h2 class="text-2xl font-bold uppercase tracking-tight">Sacubitril/Valsartan in Heart Failure</h2>\s*<p class="text-xs opacity-80 mt-1 font-mono uppercase font-bold tracking-widest">Multi-source meta-analysis of landmark RCTs</p>',
        f'<h2 class="text-2xl font-bold uppercase tracking-tight">{drug_display} in {pop_brief}</h2><p class="text-xs opacity-80 mt-1 font-mono uppercase font-bold tracking-widest">Multi-source meta-analysis of landmark RCTs</p>',
        text, count=1,
    )
    text = text.replace(
        '<h3 class="nyt-headline text-white mb-4">The Sacubitril/Valsartan Evidence</h3>',
        f'<h3 class="nyt-headline text-white mb-4">The {drug_display} Evidence</h3>',
    )

    # -------- Forest caption --------
    text = re.sub(
        r'sacubitril\\/valsartan vs placebo',
        f'{drug_lower} vs {comp_full.split(" ")[0].lower() if comp_full else "placebo"}',
        text,
    )
    text = re.sub(
        r'sacubitril/valsartan vs placebo',
        f'{drug_lower} vs {comp_full.split(" ")[0].lower() if comp_full else "placebo"}',
        text,
    )

    # -------- Benchmark summary / footnote --------
    text = text.replace(
        'compare the current pooled estimate against published sacubitril/valsartan pooled analyses.',
        f'compare the current pooled estimate against published {drug_lower} pooled analyses.',
    )
    text = text.replace(
        'locked local comparator database of published sacubitril/valsartan pooled analyses.',
        f'locked local comparator database of published {drug_lower} pooled analyses.',
    )

    # -------- Subgroup-plan input --------
    text = re.sub(
        r'(<input id="p-subgroup"[^>]*value=")[^"]*(")',
        lambda m: m.group(1) + subgroup + m.group(2),
        text, count=1,
    )

    # -------- Eligibility Participants row --------
    text = re.sub(
        r'(<tr><td class="p-3 font-bold text-slate-400">Participants</td><td class="p-3 text-slate-300">)[^<]+(</td>)',
        lambda m: m.group(1) + elig_pop + m.group(2),
        text, count=1,
    )
    # -------- Eligibility Intervention row --------
    text = re.sub(
        r'(<tr><td class="p-3 font-bold text-slate-400">Intervention</td><td class="p-3 text-slate-300">)[^<]+(</td><td class="p-3 text-slate-400">)[^<]+(</td>)',
        lambda m: m.group(1) + elig_int_short + ' as primary experimental drug' + m.group(2) + f'{elig_int_short} as background only; open-label extensions without comparator' + m.group(3),
        text, count=1,
    )
    # -------- Extraction Intervention details row --------
    text = re.sub(
        r'(<tr><td class="p-3 font-bold text-slate-400">Intervention details</td><td class="p-3 text-slate-300">)[^<]+(</td>)',
        lambda m: m.group(1) + f'{elig_int_short} dose/regimen, trial phase, treatment duration' + m.group(2),
        text, count=1,
    )

    # -------- Search query URLs (appear twice each) --------
    text = text.replace(
        'query.intr=sacubitril AND valsartan',
        f'query.intr={search_term.replace(" ", " AND ")}',
    )
    text = text.replace(
        'sacubitril valsartan AND (TITLE:randomized',
        f'{search_term} AND (TITLE:randomized',
    )
    text = text.replace(
        'search=sacubitril valsartan&amp;filter=concepts.id:C71924100',
        f'search={search_term}&amp;filter=concepts.id:C71924100',
    )

    # -------- Default state protocol object --------
    text = re.sub(
        r"protocol: \{ pop: 'Adults with Heart Failure \(HFrEF, HFpEF, or post-MI\)', int: 'Sacubitril/Valsartan \(ARNI\)', comp: 'RAAS Inhibitor \(Enalapril or Valsartan\)', out: 'CV Death or HF Hospitalization', subgroup: 'HF phenotype \(HFrEF vs HFpEF vs post-MI\), LVEF, Baseline NT-proBNP'",
        lambda m: f"protocol: {{ pop: '{pop_full.replace(chr(39), chr(92)+chr(39))}', int: '{int_full.replace(chr(39), chr(92)+chr(39))}', comp: '{comp_full.replace(chr(39), chr(92)+chr(39))}', out: '{out_full.replace(chr(39), chr(92)+chr(39))}', subgroup: '{subgroup.replace(chr(39), chr(92)+chr(39))}'",
        text, count=1,
    )

    # -------- Auto-screen note --------
    text = text.replace(
        "'Auto-screen proposed INCLUDE for canonical sacubitril/valsartan trial. Awaiting dual-review confirmation.'",
        f"'Auto-screen proposed INCLUDE for canonical {drug_lower} trial. Awaiting dual-review confirmation.'",
    )

    # -------- Direct-comparison label --------
    _esc = lambda s: s.replace(chr(39), chr(92)+chr(39))
    text = text.replace(
        "label: 'Sacubitril/Valsartan vs RAAS Inhibitor'",
        f"label: '{_esc(drug_display)} vs {_esc(comp_full)}'",
    )

    if text == original:
        return f"NOOP {path.name}"
    if not dry_run:
        path.write_bytes(text.encode("utf-8"))
    return f"OK   {path.name}"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()
    if not (args.dry_run or args.apply):
        ap.error("pass --dry-run or --apply")
    ok = miss = noop = 0
    for name, spec in SPEC.items():
        if name == "ARNI_HF_REVIEW.html":
            continue  # source template, leave intact
        p = ROOT / name
        if not p.exists():
            miss += 1; continue
        r = apply_to_file(p, spec, args.dry_run)
        if r.startswith("OK"): ok += 1
        elif r.startswith("NOOP"): noop += 1
        else: miss += 1
    print(f"{'dry-run' if args.dry_run else 'apply'}: ok={ok} noop={noop} miss={miss}")


if __name__ == "__main__":
    main()
