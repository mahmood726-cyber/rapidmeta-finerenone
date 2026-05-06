#!/usr/bin/env python3
# sentinel:skip-file - developer tool; hardcoded ROOT is intentional (local Finrenone checkout only)
"""Replace the clone-template PICO boilerplate (Sacubitril/Valsartan intervention,
'Heart Failure' population, 'CV Death or HF Hospitalization' outcome) with
drug-appropriate values per app.

Affects <input id="p-pop"|"p-int"|"p-comp"|"p-out"> defaults in 80+ apps.

Keeps the original ARNI_HF_REVIEW.html intact (it's the source drug).
"""
import argparse, pathlib, re, sys

ROOT = pathlib.Path(__file__).resolve().parent.parent

# (population, intervention, comparator, outcome)
PICO = {
    "ABLATION_AF_REVIEW.html":             ("Adults with symptomatic atrial fibrillation",                        "Catheter ablation",                   "Antiarrhythmic drug therapy",               "Recurrent AF or major cardiovascular events"),
    "ACALABRUTINIB_CLL_REVIEW.html":       ("Adults with CLL or SLL",                                              "Acalabrutinib",                       "Chemoimmunotherapy or placebo",             "Progression-free survival"),
    "ADC_HER2_ADJUVANT_NMA_REVIEW.html":   ("HER2+ early breast cancer with residual disease after neoadjuvant",   "Trastuzumab emtansine (T-DM1) adjuvant", "Trastuzumab or placebo",                 "Invasive disease-free survival (iDFS)"),
    "ADC_HER2_LOW_NMA_REVIEW.html":        ("HER2-low metastatic breast cancer",                                   "Trastuzumab deruxtecan (T-DXd)",       "Physician's-choice chemotherapy",            "Progression-free survival (PFS)"),
    "ADC_HER2_NMA_REVIEW.html":            ("HER2+ metastatic breast cancer",                                      "HER2-directed ADC (T-DXd, T-DM1, etc.)", "T-DM1 or chemotherapy",                    "Progression-free survival (PFS)"),
    "AFLIBERCEPT_HD_REVIEW.html":          ("Adults with neovascular AMD or DME",                                  "Aflibercept 8 mg (high-dose)",         "Aflibercept 2 mg or ranibizumab",            "BCVA change (letters)"),
    "ANIFROLUMAB_SLE_REVIEW.html":         ("Adults with moderate-to-severe systemic lupus erythematosus",         "Anifrolumab",                          "Placebo + standard of care",                 "BICLA response at week 52"),
    "ANTIAMYLOID_AD_NMA_REVIEW.html":      ("Early Alzheimer's disease (MCI or mild AD with confirmed amyloid)",   "Anti-amyloid monoclonal antibody",     "Placebo",                                    "CDR-SB change at 18 months"),
    "ANTIAMYLOID_AD_REVIEW.html":          ("Early Alzheimer's disease (MCI or mild AD with confirmed amyloid)",   "Anti-amyloid monoclonal antibody (lecanemab, donanemab)", "Placebo",                   "CDR-SB change at 18 months"),
    "ANTIPSYCHOTICS_SCHIZO_NMA_REVIEW.html": ("Adults with acute schizophrenia",                                    "Oral antipsychotic",                   "Placebo",                                    "PANSS total / overall symptoms change"),
    "ANTIVEGF_NAMD_NMA_REVIEW.html":       ("Adults with neovascular age-related macular degeneration",            "Anti-VEGF (ranibizumab, aflibercept, faricimab)", "Sham / reference anti-VEGF",       "BCVA change (ETDRS letters)"),
    "ARPI_mHSPC_REVIEW.html":              ("Men with metastatic hormone-sensitive prostate cancer",               "Androgen-receptor pathway inhibitor + ADT", "ADT alone",                             "Overall survival"),
    "ATOPIC_DERM_NMA_REVIEW.html":         ("Adults and adolescents with moderate-to-severe atopic dermatitis",    "Systemic immunomodulator (dupilumab, JAKi, etc.)", "Placebo",                       "EASI75 at 16 weeks"),
    "ATTR_CM_REVIEW.html":                 ("Adults with transthyretin amyloid cardiomyopathy",                    "TTR stabilizer (tafamidis, acoramidis)", "Placebo",                                 "All-cause mortality or CV hospitalization"),
    "BELIMUMAB_SLE_REVIEW.html":           ("Adults with seropositive systemic lupus erythematosus",               "Belimumab",                            "Placebo + standard of care",                 "SRI-4 response at week 52"),
    "BEMPEDOIC_ACID_REVIEW.html":          ("Adults with ASCVD (statin-intolerant or statin-treated)",             "Bempedoic acid",                       "Placebo",                                    "MACE-4 composite"),
    "BIOLOGIC_ASTHMA_REVIEW.html":         ("Adults with severe asthma",                                           "Biologic (mepolizumab, benralizumab, dupilumab)", "Placebo",                         "Annual exacerbation rate"),
    "BTKI_CLL_NMA_REVIEW.html":            ("Adults with CLL or SLL",                                              "BTK inhibitor (ibrutinib, acalabrutinib, zanubrutinib)", "BTK comparator or chemoimmunotherapy", "Progression-free survival"),
    "CAB_PREP_HIV_REVIEW.html":            ("Adults at risk of HIV acquisition",                                   "Long-acting cabotegravir (PrEP)",      "Daily oral TDF/FTC",                         "HIV incidence"),
    "CANGRELOR_PCI_REVIEW.html":           ("Adults undergoing PCI",                                               "Cangrelor",                            "Clopidogrel loading dose",                   "Death, MI, ischemia-driven revasc or stent thrombosis at 48 h"),
    "CARDIORENAL_DKD_NMA_REVIEW.html":     ("Adults with type 2 diabetes and CKD",                                 "SGLT2i / finerenone / GLP-1 RA",       "Placebo + standard RAS blockade",            "Renal composite (failure, eGFR decline, renal death)"),
    "CART_DLBCL_REVIEW.html":              ("Adults with relapsed/refractory large B-cell lymphoma",               "CAR-T cell therapy (axi-cel, liso-cel)", "Standard-of-care 2nd-line therapy",         "Event-free survival"),
    "CART_MM_REVIEW.html":                 ("Adults with relapsed/refractory multiple myeloma",                    "CAR-T cell therapy (cilta-cel, ide-cel)", "Physician's-choice regimen",              "Progression-free survival"),
    "CBD_SEIZURE_REVIEW.html":             ("Children / adolescents with Dravet or Lennox-Gastaut syndrome",       "Cannabidiol",                          "Placebo",                                    "Convulsive seizure frequency reduction"),
    "CDK46_MBC_REVIEW.html":               ("HR+/HER2- metastatic breast cancer (1L)",                             "CDK4/6 inhibitor + endocrine therapy", "Endocrine therapy alone",                    "Progression-free survival"),
    "CD_BIOLOGICS_NMA_REVIEW.html":        ("Adults with moderate-to-severe Crohn's disease",                      "Biologic or small molecule",           "Placebo",                                    "Clinical remission at induction"),
    "CFTR_CF_REVIEW.html":                 ("Patients with cystic fibrosis (F508del-eligible)",                    "CFTR modulator (ELX/TEZ/IVA, TEZ/IVA)", "Placebo",                                   "Absolute ppFEV1 change"),
    "CFTR_MODULATORS_NMA_REVIEW.html":     ("Patients with cystic fibrosis",                                       "CFTR modulator (any generation)",      "Placebo",                                    "ppFEV1 and pulmonary exacerbation rate"),
    "CGRP_MIGRAINE_NMA_REVIEW.html":       ("Adults with episodic or chronic migraine",                            "Anti-CGRP monoclonal antibody",        "Placebo",                                    "Monthly migraine days reduction"),
    "CGRP_MIGRAINE_REVIEW.html":           ("Adults with episodic or chronic migraine",                            "Anti-CGRP monoclonal antibody (erenumab, fremanezumab, galcanezumab, eptinezumab)", "Placebo", "Monthly migraine days reduction"),
    "COLCHICINE_CVD_REVIEW.html":          ("Adults with stable CAD or recent MI",                                 "Low-dose colchicine (0.5 mg)",         "Placebo",                                    "MACE composite"),
    "COPD_TRIPLE_REVIEW.html":             ("Adults with COPD and exacerbation history",                           "Triple therapy (ICS/LABA/LAMA)",       "Dual ICS/LABA or LAMA/LABA",                 "Moderate/severe exacerbation rate"),
    "COVID_ORAL_ANTIVIRALS_REVIEW.html":   ("Outpatients with COVID-19 at risk for severe disease",                "Oral antiviral (nirmatrelvir/r, molnupiravir)", "Placebo",                          "Hospitalization or death"),
    "DOAC_AF_NMA_REVIEW.html":             ("Adults with non-valvular atrial fibrillation",                        "DOAC (apixaban, dabigatran, edoxaban, rivaroxaban)", "Warfarin",                       "Stroke or systemic embolism"),
    "DOAC_AF_REVIEW.html":                 ("Adults with non-valvular atrial fibrillation",                        "Direct oral anticoagulant (DOAC)",     "Warfarin",                                   "Stroke or systemic embolism"),
    "DOAC_CANCER_VTE_REVIEW.html":         ("Patients with cancer-associated VTE",                                 "DOAC (apixaban, edoxaban, rivaroxaban)", "LMWH (dalteparin)",                        "Recurrent VTE"),
    "DOAC_VTE_NMA_REVIEW.html":            ("Adults with acute venous thromboembolism",                            "Direct oral anticoagulant",            "Vitamin K antagonist",                       "VTE recurrence"),
    "DUPILUMAB_AD_REVIEW.html":            ("Adults and adolescents with moderate-to-severe atopic dermatitis",    "Dupilumab",                            "Placebo",                                    "EASI75 at 16 weeks"),
    "DUPILUMAB_COPD_REVIEW.html":          ("Adults with COPD and type-2 inflammation",                            "Dupilumab",                            "Placebo",                                    "Annual moderate-severe exacerbation rate"),
    "ESKETAMINE_TRD_REVIEW.html":          ("Adults with treatment-resistant depression",                          "Intranasal esketamine + oral antidepressant", "Placebo spray + oral antidepressant",  "MADRS change"),
    "EVT_BASILAR_REVIEW.html":             ("Adults with acute basilar-artery occlusion",                          "Endovascular thrombectomy",            "Best medical management",                    "mRS 0-3 at 90 days"),
    "EVT_EXTENDED_WINDOW_REVIEW.html":     ("Adults with anterior-circulation stroke in 6-24 h window",            "Endovascular thrombectomy",            "Medical management",                         "Functional independence (mRS 0-2) at 90 days"),
    "EVT_LARGECORE_REVIEW.html":           ("Adults with large-core ischemic stroke (ASPECTS 3-5)",                "Endovascular thrombectomy",            "Medical management",                         "mRS 0-3 at 90 days"),
    "FARICIMAB_NAMD_REVIEW.html":          ("Adults with neovascular AMD",                                         "Faricimab",                            "Aflibercept",                                "BCVA change (ETDRS letters)"),
    "FENFLURAMINE_SEIZURE_REVIEW.html":    ("Children / adolescents with Dravet syndrome",                         "Fenfluramine",                         "Placebo",                                    "Convulsive seizure frequency reduction"),
    "FEZOLINETANT_VMS_REVIEW.html":        ("Postmenopausal women with moderate-severe vasomotor symptoms",        "Fezolinetant",                         "Placebo",                                    "VMS frequency reduction"),
    "GLP1_CVOT_NMA_REVIEW.html":           ("Adults with type 2 diabetes at elevated cardiovascular risk",         "GLP-1 receptor agonist",               "Placebo",                                    "3-point MACE"),
    "GLP1_CVOT_REVIEW.html":               ("Adults with type 2 diabetes at elevated cardiovascular risk",         "GLP-1 receptor agonist",               "Placebo",                                    "3-point MACE"),
    "HIGH_EFFICACY_MS_REVIEW.html":        ("Adults with relapsing-remitting multiple sclerosis",                  "High-efficacy DMT (ocrelizumab, natalizumab, etc.)", "Interferon or moderate DMT",     "Annualized relapse rate"),
    "IL23_PSORIASIS_REVIEW.html":          ("Adults with moderate-to-severe plaque psoriasis",                     "IL-23 inhibitor (risankizumab, guselkumab, tildrakizumab)", "Placebo or comparator biologic", "PASI90 at week 16"),
    "IL_PSORIASIS_NMA_REVIEW.html":        ("Adults with moderate-to-severe plaque psoriasis",                     "Systemic biologic / small molecule",   "Placebo",                                    "PASI90 at induction"),
    "INCLISIRAN_REVIEW.html":              ("Adults with ASCVD or heterozygous FH on maximally tolerated statin",  "Inclisiran",                           "Placebo",                                    "LDL-C percent change"),
    "INCRETINS_T2D_NMA_REVIEW.html":       ("Adults with type 2 diabetes",                                         "GLP-1 RA or DPP-4 inhibitor",          "Placebo or other glucose-lowering agent",    "HbA1c change"),
    "INCRETIN_HFpEF_REVIEW.html":          ("Adults with HFpEF and obesity",                                       "Semaglutide or tirzepatide",           "Placebo",                                    "KCCQ-CSS change"),
    "INSULIN_ICODEC_REVIEW.html":          ("Adults with type 2 diabetes",                                         "Once-weekly insulin icodec",           "Daily basal insulin",                        "HbA1c change (non-inferiority)"),
    "INTENSIVE_BP_REVIEW.html":            ("Adults at elevated cardiovascular risk",                              "Intensive BP control (SBP < 120-130)", "Standard BP control (SBP < 140)",            "MACE composite"),
    "IO_CHEMO_NSCLC_1L_REVIEW.html":       ("Adults with advanced NSCLC (1L)",                                     "Anti-PD-(L)1 + chemotherapy",          "Chemotherapy alone",                         "Overall survival"),
    "IV_IRON_HF_REVIEW.html":              ("Adults with HFrEF and iron deficiency",                               "IV ferric carboxymaltose",             "Placebo",                                    "CV death or HF hospitalization"),
    "JAKI_AD_REVIEW.html":                 ("Adults with moderate-to-severe atopic dermatitis",                    "JAK inhibitor (upadacitinib, abrocitinib)", "Placebo",                                "EASI75 at 16 weeks"),
    "JAKI_RA_NMA_REVIEW.html":             ("Adults with moderate-to-severe rheumatoid arthritis",                 "JAK inhibitor",                        "Placebo or active comparator",               "ACR20 at 12-24 weeks"),
    "JAK_RA_REVIEW.html":                  ("Adults with moderate-to-severe rheumatoid arthritis",                 "JAK inhibitor (tofacitinib, baricitinib, upadacitinib, filgotinib)", "Placebo", "ACR20 at 12-24 weeks"),
    "JAK_UC_REVIEW.html":                  ("Adults with moderate-to-severe ulcerative colitis",                   "JAK inhibitor (tofacitinib, upadacitinib)", "Placebo",                               "Clinical remission at 8 weeks"),
    "KARXT_SCZ_REVIEW.html":               ("Adults with acute schizophrenia",                                     "Xanomeline + trospium (KarXT)",        "Placebo",                                    "PANSS total change at week 5"),
    "LENACAPAVIR_PREP_REVIEW.html":        ("Adults at risk of HIV acquisition",                                   "Lenacapavir SC twice-yearly",          "Daily oral TDF/FTC",                         "HIV incidence"),
    "LIPID_HUB_REVIEW.html":               ("Adults with ASCVD or high cardiovascular risk",                       "Lipid-lowering therapy (statin, PCSK9i, etc.)", "Placebo or less-intensive therapy",   "MACE composite"),
    "LU_PSMA_MCRPC_REVIEW.html":           ("Men with PSMA+ mCRPC post-ARPI and taxane",                           "177Lu-PSMA-617 + standard of care",    "Standard of care alone",                     "Overall survival"),
    "MAVACAMTEN_HCM_REVIEW.html":          ("Adults with symptomatic obstructive HCM",                             "Mavacamten",                           "Placebo",                                    "Composite functional/pVO2 response"),
    "MIRIKIZUMAB_UC_REVIEW.html":          ("Adults with moderate-to-severe ulcerative colitis",                   "Mirikizumab",                          "Placebo",                                    "Clinical remission at induction"),
    "MITRAL_FUNCMR_REVIEW.html":           ("Adults with severe secondary mitral regurgitation",                   "Transcatheter mitral edge-to-edge repair + GDMT", "GDMT alone",                      "CV death or HF hospitalization"),
    "NIRSEVIMAB_INFANT_RSV_REVIEW.html":   ("Healthy term / late-preterm infants",                                 "Nirsevimab (single IM dose)",          "Placebo",                                    "Medically-attended RSV LRTI"),
    "PARP_ARPI_MCRPC_REVIEW.html":         ("Men with mCRPC (1L)",                                                 "PARP inhibitor + androgen-receptor pathway inhibitor", "ARPI + placebo",                 "Radiographic progression-free survival"),
    "PARP_OVARIAN_REVIEW.html":            ("Women with advanced ovarian cancer (maintenance)",                    "PARP inhibitor (olaparib, niraparib)", "Placebo",                                    "Progression-free survival"),
    "PATISIRAN_POLYNEUROPATHY_REVIEW.html": ("Adults with hereditary transthyretin amyloidosis with polyneuropathy", "Patisiran",                            "Placebo",                                    "mNIS+7 change at 18 months"),
    "PBC_PPAR_REVIEW.html":                ("Adults with primary biliary cholangitis with inadequate UDCA response", "PPAR agonist (elafibranor, seladelpar)", "Placebo + UDCA",                        "Biochemical response (composite ALP / bilirubin)"),
    "PCSK9_LIPID_NMA_REVIEW.html":         ("Adults with ASCVD or very-high cardiovascular risk",                  "PCSK9 inhibitor (alirocumab, evolocumab, inclisiran)", "Placebo",                  "MACE or LDL-C change"),
    "PCSK9_REVIEW.html":                   ("Adults with ASCVD or heterozygous FH",                                "PCSK9 inhibitor",                      "Placebo",                                    "MACE composite"),
    "PEGCETACOPLAN_GA_REVIEW.html":        ("Adults with geographic atrophy secondary to AMD",                     "Intravitreal pegcetacoplan",           "Sham",                                       "GA lesion-area change"),
    "RENAL_DENERV_REVIEW.html":            ("Adults with uncontrolled hypertension on medication",                 "Catheter-based renal denervation",     "Sham procedure",                             "24-h ambulatory SBP change"),
    "RISANKIZUMAB_CD_REVIEW.html":         ("Adults with moderate-to-severe Crohn's disease",                      "Risankizumab",                         "Placebo",                                    "Clinical remission at induction"),
    "RIVAROXABAN_VASC_REVIEW.html":        ("Adults with stable ASCVD or PAD",                                     "Rivaroxaban 2.5 mg BID + aspirin",     "Aspirin alone",                              "MACE composite"),
    "ROMOSOZUMAB_OP_REVIEW.html":          ("Postmenopausal women with osteoporosis",                              "Romosozumab",                          "Alendronate or placebo",                     "New vertebral fracture"),
    "RSV_VACCINE_OLDER_REVIEW.html":       ("Adults aged >=60 years",                                              "RSV prefusion-F vaccine",              "Placebo",                                    "RSV-associated lower respiratory tract disease"),
    "SEMAGLUTIDE_OBESITY_REVIEW.html":     ("Adults with overweight/obesity and established CVD (without diabetes)", "Semaglutide 2.4 mg weekly",          "Placebo",                                    "3-point MACE"),
    "SEVERE_ASTHMA_NMA_REVIEW.html":       ("Adults with severe eosinophilic asthma",                              "Biologic (mepolizumab, benralizumab, dupilumab, tezepelumab)", "Placebo",            "Annual exacerbation rate"),
    "SGLT2I_HF_NMA_REVIEW.html":           ("Adults with heart failure across EF spectrum",                        "SGLT2 inhibitor",                      "Placebo",                                    "CV death or HF hospitalization"),
    "SGLT2_CKD_REVIEW.html":               ("Adults with CKD (with or without type 2 diabetes)",                   "SGLT2 inhibitor (dapagliflozin, empagliflozin)", "Placebo",                          "Renal composite"),
    "SGLT2_HF_REVIEW.html":                ("Adults with heart failure",                                           "SGLT2 inhibitor",                      "Placebo",                                    "CV death or HF hospitalization"),
    "SGLT2_MACE_CVOT_REVIEW.html":         ("Adults with type 2 diabetes at cardiovascular risk",                  "SGLT2 inhibitor",                      "Placebo",                                    "3-point MACE"),
    "SOTAGLIFLOZIN_HF_REVIEW.html":        ("Adults with T2D recently hospitalized for worsening HF",              "Sotagliflozin",                        "Placebo",                                    "CV death, HHF, or urgent HF visit"),
    "TAVR_LOWRISK_REVIEW.html":            ("Adults with severe aortic stenosis at low surgical risk",             "TAVR",                                 "Surgical aortic valve replacement",          "Death, stroke, or rehospitalization at 1 yr"),
    "TDXD_HER2LOW_BC_REVIEW.html":         ("HER2-low metastatic breast cancer",                                   "Trastuzumab deruxtecan (T-DXd)",       "Physician's-choice chemotherapy",            "Progression-free survival"),
    "TIRZEPATIDE_OBESITY_REVIEW.html":     ("Adults with overweight/obesity without diabetes",                     "Tirzepatide",                          "Placebo",                                    "Body-weight percent change"),
    "TIRZEPATIDE_T2D_REVIEW.html":         ("Adults with type 2 diabetes",                                         "Tirzepatide",                          "Semaglutide or placebo",                     "HbA1c change"),
    "TNK_VS_TPA_STROKE_REVIEW.html":       ("Adults with acute ischemic stroke within 4.5 h",                      "Tenecteplase",                         "Alteplase",                                  "mRS 0-1 at 90 days"),
    "UC_BIOLOGICS_NMA_REVIEW.html":        ("Adults with moderate-to-severe ulcerative colitis",                   "Biologic or small molecule",           "Placebo",                                    "Clinical remission at induction"),
    "UPADACITINIB_CD_REVIEW.html":         ("Adults with moderate-to-severe Crohn's disease",                      "Upadacitinib",                         "Placebo",                                    "Clinical remission at induction"),
    "VENETOCLAX_AML_REVIEW.html":          ("Adults with newly-diagnosed AML ineligible for intensive chemo",      "Venetoclax + azacitidine",             "Placebo + azacitidine",                      "Overall survival"),
}


def apply_to_file(path: pathlib.Path, pop, intv, comp, out, dry_run: bool) -> str:
    raw = path.read_bytes()
    crlf = b"\r\n" in raw
    text = raw.decode("utf-8")

    # Each input is a one-liner with id="p-X" and value="..."
    # Four substitutions per file, targeted narrowly.
    replacements = [
        (re.compile(r'(<input id="p-pop"[^>]*value=")[^"]*(")'),  pop),
        (re.compile(r'(<input id="p-int"[^>]*value=")[^"]*(")'),  intv),
        (re.compile(r'(<input id="p-comp"[^>]*value=")[^"]*(")'), comp),
        (re.compile(r'(<input id="p-out"[^>]*value=")[^"]*(")'),  out),
    ]
    changes = 0
    for pat, val in replacements:
        new_text, n = pat.subn(lambda m: m.group(1) + val + m.group(2), text, count=1)
        if n > 0:
            changes += n
            text = new_text
    if changes == 0:
        return f"MISS {path.name}: no PICO inputs found"
    if not dry_run:
        path.write_bytes(text.encode("utf-8"))
    return f"OK   {path.name}: {changes}/4 inputs updated"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()
    if not (args.dry_run or args.apply):
        ap.error("pass --dry-run or --apply")

    ok = miss = 0
    for name, pico in PICO.items():
        p = ROOT / name
        if not p.exists():
            continue
        r = apply_to_file(p, *pico, dry_run=args.dry_run)
        if r.startswith("OK"):
            ok += 1
        else:
            miss += 1
        if miss < 10 or r.startswith("OK"):
            print(r)
    print(f"\n{'dry-run' if args.dry_run else 'apply'}: {ok} ok / {miss} miss")


if __name__ == "__main__":
    main()
