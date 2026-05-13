"""Audit-first topic-add pipeline — auto-discovery edition.

Same 6 gates as scripts/add_topic_audit_first.py but the candidate NCT list
is generated automatically from AACT by searching interventions.txt for
the drug pattern + filtering to NCTs whose conditions contain the topic
pattern.

This scales the pipeline to dozens of topics per run.

Input: TOPICS list = [(stem, name, drug_patterns, condition_patterns)]
Auto-fills NCTs from AACT.

Output: outputs/new_topics/<STEM>.json with the same shape as before.
"""
from __future__ import annotations
import json, csv, re, sys, io, time, urllib.request, urllib.parse
from pathlib import Path
from collections import defaultdict
import xml.etree.ElementTree as ET

if hasattr(sys.stdout, "buffer") and getattr(sys.stdout, "encoding", "").lower() != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

HERE = Path(__file__).resolve().parent.parent
OUT = HERE / "outputs" / "new_topics"
OUT.mkdir(parents=True, exist_ok=True)
AACT = Path("C:/Users/user/AACT/2026-04-12")

# Topic specs (drug + disease patterns; NCTs auto-discovered from AACT)
# Format: (stem, display name, drug_patterns, condition_patterns, [phase_min=2])
TOPICS = [
    # Cardiology — newer drugs / endpoint variations
    ("DAPAGLIFLOZIN_CKD_AUTO", "Dapagliflozin in CKD",
     ["dapagliflozin"], ["chronic kidney"]),
    ("EMPAGLIFLOZIN_CKD_AUTO", "Empagliflozin in CKD",
     ["empagliflozin"], ["chronic kidney"]),
    ("CANAGLIFLOZIN_DKD_AUTO", "Canagliflozin in diabetic kidney",
     ["canagliflozin"], ["diabetic nephropathy", "diabetic kidney"]),
    ("EMPAGLIFLOZIN_T2D_CV_AUTO", "Empagliflozin in T2D CVOT",
     ["empagliflozin"], ["type 2 diabetes"]),
    ("DAPAGLIFLOZIN_T2D_CV_AUTO", "Dapagliflozin in T2D CVOT",
     ["dapagliflozin"], ["type 2 diabetes"]),
    ("INCLISIRAN_LIPID_AUTO", "Inclisiran for hyperlipidaemia",
     ["inclisiran"], ["hyperlipidemia", "cholesterol"]),
    ("ICOSAPENT_CVD_AUTO", "Icosapent ethyl in CV prevention",
     ["icosapent"], ["cardiovascular"]),
    ("OLPASIRAN_LPA_AUTO", "Olpasiran for Lp(a) lowering",
     ["olpasiran"], ["lipoprotein"]),
    ("PELACARSEN_LPA_AUTO", "Pelacarsen for Lp(a) lowering",
     ["pelacarsen", "tqj230"], ["lipoprotein"]),
    ("OBICETRAPIB_LIPID_AUTO", "Obicetrapib (CETP inhibitor) for lipids",
     ["obicetrapib"], ["hypercholesterol", "atherosclerot"]),
    ("ALIROCUMAB_LIPID_AUTO", "Alirocumab for hyperlipidaemia/CV prevention",
     ["alirocumab"], ["hypercholesterol", "cardiovascular"]),
    ("EVOLOCUMAB_LIPID_AUTO", "Evolocumab for hyperlipidaemia/CV prevention",
     ["evolocumab"], ["hypercholesterol", "cardiovascular"]),
    ("RIVAROXABAN_PERIPHERAL_AUTO", "Rivaroxaban in peripheral artery disease",
     ["rivaroxaban"], ["peripheral artery"]),
    ("EDOXABAN_CANCER_VTE_AUTO", "Edoxaban in cancer-associated VTE",
     ["edoxaban"], ["venous thromboembolism", "neoplasm"]),
    ("APIXABAN_CANCER_VTE_AUTO", "Apixaban in cancer-associated VTE",
     ["apixaban"], ["venous thromboembolism", "neoplasm"]),
    # Oncology — IO/ADC/TKI
    ("PEMBROLIZUMAB_NSCLC_1L_AUTO", "Pembrolizumab 1L NSCLC",
     ["pembrolizumab"], ["non-small cell lung", "nsclc"]),
    ("NIVOLUMAB_RCC_AUTO", "Nivolumab in renal cell carcinoma",
     ["nivolumab"], ["renal cell"]),
    ("NIVOLUMAB_GASTRIC_AUTO", "Nivolumab in gastric/GEJ",
     ["nivolumab"], ["gastric"]),
    ("PEMBROLIZUMAB_BLADDER_AUTO", "Pembrolizumab in bladder/urothelial",
     ["pembrolizumab"], ["urothelial", "bladder"]),
    ("ATEZOLIZUMAB_LUNG_AUTO", "Atezolizumab in NSCLC/SCLC",
     ["atezolizumab"], ["lung"]),
    ("DURVALUMAB_LUNG_AUTO", "Durvalumab in NSCLC (stage III)",
     ["durvalumab"], ["non-small cell lung"]),
    ("OSIMERTINIB_EGFR_NSCLC_AUTO", "Osimertinib in EGFR+ NSCLC",
     ["osimertinib"], ["non-small cell lung", "egfr"]),
    ("ALECTINIB_ALK_NSCLC_AUTO", "Alectinib in ALK+ NSCLC",
     ["alectinib"], ["non-small cell lung", "anaplastic lymphoma kinase"]),
    ("LORLATINIB_ALK_NSCLC_AUTO", "Lorlatinib in ALK+ NSCLC",
     ["lorlatinib"], ["non-small cell lung"]),
    ("BRIGATINIB_ALK_NSCLC_AUTO", "Brigatinib in ALK+ NSCLC",
     ["brigatinib"], ["non-small cell lung"]),
    ("TRASTUZUMAB_DERUXTECAN_AUTO", "Trastuzumab deruxtecan",
     ["trastuzumab deruxtecan", "ds-8201", "fam-trastuzumab"], ["neoplasm"]),
    ("OLAPARIB_OVARIAN_AUTO", "Olaparib in ovarian",
     ["olaparib"], ["ovarian"]),
    ("NIRAPARIB_OVARIAN_AUTO", "Niraparib in ovarian",
     ["niraparib"], ["ovarian"]),
    ("RUCAPARIB_OVARIAN_AUTO", "Rucaparib in ovarian",
     ["rucaparib"], ["ovarian"]),
    ("OLAPARIB_BREAST_AUTO", "Olaparib in BRCA+ breast",
     ["olaparib"], ["breast"]),
    ("PALBOCICLIB_BREAST_AUTO", "Palbociclib in HR+ breast",
     ["palbociclib"], ["breast"]),
    ("RIBOCICLIB_BREAST_AUTO", "Ribociclib in HR+ breast",
     ["ribociclib"], ["breast"]),
    ("ABEMACICLIB_BREAST_AUTO", "Abemaciclib in HR+ breast",
     ["abemaciclib"], ["breast"]),
    ("VENETOCLAX_AML_AUTO", "Venetoclax in AML",
     ["venetoclax"], ["acute myeloid leukemia"]),
    ("VENETOCLAX_CLL_AUTO", "Venetoclax in CLL",
     ["venetoclax"], ["chronic lymphocytic"]),
    ("ACALABRUTINIB_CLL_2L_AUTO", "Acalabrutinib in R/R CLL",
     ["acalabrutinib"], ["chronic lymphocytic"]),
    ("ZANUBRUTINIB_LYMPHOMA_AUTO", "Zanubrutinib in lymphoma",
     ["zanubrutinib"], ["lymphoma"]),
    ("DARATUMUMAB_MM_AUTO", "Daratumumab in multiple myeloma",
     ["daratumumab"], ["multiple myeloma"]),
    ("ISATUXIMAB_MM_AUTO", "Isatuximab in multiple myeloma",
     ["isatuximab"], ["multiple myeloma"]),
    ("CARFILZOMIB_MM_AUTO", "Carfilzomib in multiple myeloma",
     ["carfilzomib"], ["multiple myeloma"]),
    # Diabetes / metabolic / endocrine
    ("TIRZEPATIDE_OBESITY_AUTO", "Tirzepatide for obesity",
     ["tirzepatide"], ["obesity", "overweight"]),
    ("TIRZEPATIDE_NASH_AUTO", "Tirzepatide in NASH/MASH",
     ["tirzepatide"], ["nonalcoholic", "steatohepatitis"]),
    ("RETATRUTIDE_OBESITY_AUTO", "Retatrutide (triple agonist) obesity",
     ["retatrutide"], ["obesity"]),
    ("ORFORGLIPRON_T2D_AUTO", "Orforglipron oral GLP-1 in T2D",
     ["orforglipron"], ["type 2 diabetes"]),
    ("SEMAGLUTIDE_NASH_AUTO", "Semaglutide in NASH",
     ["semaglutide"], ["nonalcoholic", "steatohepatitis"]),
    ("SEMAGLUTIDE_OBESITY_AUTO", "Semaglutide for obesity (STEP)",
     ["semaglutide"], ["obesity"]),
    ("LIRAGLUTIDE_OBESITY_AUTO", "Liraglutide for obesity (SCALE)",
     ["liraglutide"], ["obesity"]),
    ("DAPAGLIFLOZIN_MASH_AUTO", "Dapagliflozin/SGLT2 in MASH",
     ["dapagliflozin", "empagliflozin"], ["nonalcoholic", "steatohepatitis"]),
    # Dermatology / Rheumatology / GI biologics
    ("RISANKIZUMAB_PSORIASIS_AUTO", "Risankizumab in psoriasis",
     ["risankizumab"], ["psoriasis"]),
    ("GUSELKUMAB_PSORIASIS_AUTO", "Guselkumab in psoriasis",
     ["guselkumab"], ["psoriasis"]),
    ("IXEKIZUMAB_PSORIASIS_AUTO", "Ixekizumab in psoriasis",
     ["ixekizumab"], ["psoriasis"]),
    ("SECUKINUMAB_AXSPA_AUTO", "Secukinumab in axial spondyloarthritis",
     ["secukinumab"], ["spondyl"]),
    ("UPADACITINIB_RA_AUTO", "Upadacitinib in rheumatoid arthritis",
     ["upadacitinib"], ["rheumatoid arthritis"]),
    ("UPADACITINIB_AS_AUTO", "Upadacitinib in ankylosing spondylitis",
     ["upadacitinib"], ["ankylosing", "axial spondyl"]),
    ("UPADACITINIB_PSA_AUTO", "Upadacitinib in psoriatic arthritis",
     ["upadacitinib"], ["psoriatic arthritis"]),
    ("UPADACITINIB_AD_AUTO", "Upadacitinib in atopic dermatitis",
     ["upadacitinib"], ["dermatitis"]),
    ("DEUCRAVACITINIB_PSORIASIS_AUTO", "Deucravacitinib (Sotyktu) psoriasis",
     ["deucravacitinib"], ["psoriasis"]),
    ("FILGOTINIB_RA_AUTO", "Filgotinib in rheumatoid arthritis",
     ["filgotinib"], ["rheumatoid arthritis"]),
    ("FILGOTINIB_UC_AUTO", "Filgotinib in ulcerative colitis",
     ["filgotinib"], ["ulcerative colitis"]),
    ("USTEKINUMAB_CD_AUTO", "Ustekinumab in Crohn disease",
     ["ustekinumab"], ["crohn"]),
    ("VEDOLIZUMAB_IBD_AUTO", "Vedolizumab in IBD",
     ["vedolizumab"], ["inflammatory bowel", "ulcerative", "crohn"]),
    ("DUPILUMAB_AD_AUTO", "Dupilumab in atopic dermatitis",
     ["dupilumab"], ["atopic", "dermatitis"]),
    ("DUPILUMAB_ASTHMA_AUTO", "Dupilumab in asthma",
     ["dupilumab"], ["asthma"]),
    ("DUPILUMAB_CRSwNP_AUTO", "Dupilumab in CRSwNP",
     ["dupilumab"], ["chronic rhinosinusitis", "nasal polyp"]),
    ("DUPILUMAB_EOE_AUTO", "Dupilumab in eosinophilic esophagitis",
     ["dupilumab"], ["eosinophilic esophagitis"]),
    ("MEPOLIZUMAB_ASTHMA_AUTO", "Mepolizumab in severe eosinophilic asthma",
     ["mepolizumab"], ["asthma"]),
    ("BENRALIZUMAB_ASTHMA_AUTO", "Benralizumab in severe asthma",
     ["benralizumab"], ["asthma"]),
    ("RESLIZUMAB_ASTHMA_AUTO", "Reslizumab in eosinophilic asthma",
     ["reslizumab"], ["asthma"]),
    ("OMALIZUMAB_URTICARIA_AUTO", "Omalizumab in chronic urticaria",
     ["omalizumab"], ["urticaria"]),
    # Migraine / neuro
    ("ATOGEPANT_MIGRAINE_AUTO", "Atogepant (CGRP small molecule) migraine prevention",
     ["atogepant"], ["migraine"]),
    ("RIMEGEPANT_MIGRAINE_AUTO", "Rimegepant acute + prevention migraine",
     ["rimegepant"], ["migraine"]),
    ("UBROGEPANT_MIGRAINE_AUTO", "Ubrogepant acute migraine",
     ["ubrogepant"], ["migraine"]),
    ("ZAVEGEPANT_MIGRAINE_AUTO", "Zavegepant intranasal acute migraine",
     ["zavegepant"], ["migraine"]),
    ("FREMANEZUMAB_MIGRAINE_AUTO", "Fremanezumab for migraine prevention",
     ["fremanezumab"], ["migraine"]),
    ("EPTINEZUMAB_MIGRAINE_AUTO", "Eptinezumab for migraine prevention",
     ["eptinezumab"], ["migraine"]),
    # Hepatology / GI
    ("RESMETIROM_NASH_AUTO", "Resmetirom for MASH",
     ["resmetirom"], ["nonalcoholic", "steatohepatitis"]),
    ("OBETICHOLIC_NASH_AUTO", "Obeticholic acid in NASH",
     ["obeticholic"], ["nonalcoholic", "steatohepatitis"]),
    ("BULEVIRTIDE_HEPD_AUTO", "Bulevirtide in hepatitis D",
     ["bulevirtide"], ["hepatitis"]),
    # Infectious / vaccines
    ("MOLNUPIRAVIR_COVID_AUTO", "Molnupiravir for outpatient COVID-19",
     ["molnupiravir"], ["covid"]),
    ("NIRMATRELVIR_COVID_AUTO", "Nirmatrelvir/ritonavir Paxlovid",
     ["nirmatrelvir"], ["covid"]),
    ("REMDESIVIR_COVID_AUTO", "Remdesivir for hospitalized COVID-19",
     ["remdesivir"], ["covid"]),
    ("BARICITINIB_COVID_AUTO", "Baricitinib for hospitalized COVID-19",
     ["baricitinib"], ["covid"]),
    ("TOCILIZUMAB_COVID_AUTO", "Tocilizumab for hospitalized COVID-19",
     ["tocilizumab"], ["covid"]),
    # Endocrine
    ("OSILODROSTAT_CUSHING_AUTO", "Osilodrostat in Cushing disease",
     ["osilodrostat"], ["cushing"]),
    ("PASIREOTIDE_CUSHING_AUTO", "Pasireotide in Cushing",
     ["pasireotide"], ["cushing"]),
    ("PEGVISOMANT_ACROMEGALY_AUTO", "Pegvisomant in acromegaly",
     ["pegvisomant"], ["acromegaly"]),
    # ATTR / cardiac
    ("PATISIRAN_ATTR_PN_AUTO", "Patisiran in ATTR polyneuropathy",
     ["patisiran"], ["amyloid"]),
    ("INOTERSEN_ATTR_PN_AUTO", "Inotersen in ATTR polyneuropathy",
     ["inotersen"], ["amyloid"]),
    # Newer haem
    ("CRIZANLIZUMAB_SCD_AUTO", "Crizanlizumab in sickle cell",
     ["crizanlizumab"], ["sickle"]),
    ("VOXELOTOR_SCD_AUTO", "Voxelotor in sickle cell",
     ["voxelotor"], ["sickle"]),
    ("LUSPATERCEPT_BETA_THAL_AUTO", "Luspatercept in beta-thalassemia",
     ["luspatercept"], ["thalassemia"]),
    ("LUSPATERCEPT_MDS_AUTO", "Luspatercept in MDS",
     ["luspatercept"], ["myelodysplastic"]),
    # AML / MDS targeted
    ("IVOSIDENIB_AML_AUTO", "Ivosidenib in IDH1+ AML",
     ["ivosidenib"], ["acute myeloid leukemia"]),
    ("ENASIDENIB_AML_AUTO", "Enasidenib in IDH2+ AML",
     ["enasidenib"], ["acute myeloid leukemia"]),
    ("MIDOSTAURIN_AML_AUTO", "Midostaurin in FLT3+ AML",
     ["midostaurin"], ["acute myeloid leukemia"]),
    ("GILTERITINIB_AML_AUTO", "Gilteritinib in FLT3+ R/R AML",
     ["gilteritinib"], ["acute myeloid leukemia"]),
    # Cardio / nephrology novel
    ("FINERENONE_HFpEF_AUTO", "Finerenone in HFpEF (FINEARTS-HF)",
     ["finerenone"], ["heart failure"]),
    ("VERICIGUAT_HFREF_AUTO", "Vericiguat in HFrEF (VICTORIA)",
     ["vericiguat"], ["heart failure"]),
    ("OMECAMTIV_HF_AUTO", "Omecamtiv mecarbil in HFrEF",
     ["omecamtiv"], ["heart failure"]),
    # Renal-protective
    ("CANAGLIFLOZIN_CKD_AUTO", "Canagliflozin in CKD",
     ["canagliflozin"], ["chronic kidney"]),
    # HIV
    ("CABOTEGRAVIR_HIV_TX_AUTO", "Cabotegravir long-acting HIV treatment",
     ["cabotegravir"], ["hiv"]),
    ("DOLUTEGRAVIR_HIV_AUTO", "Dolutegravir-based HIV regimens",
     ["dolutegravir"], ["hiv"]),
    ("LENACAPAVIR_HIV_AUTO", "Lenacapavir long-acting HIV",
     ["lenacapavir"], ["hiv"]),
    # IBD / kidney newer
    ("BIMEKIZUMAB_PSORIATIC_AUTO", "Bimekizumab in psoriatic arthritis",
     ["bimekizumab"], ["psoriatic"]),
    ("ETROLIZUMAB_UC_AUTO", "Etrolizumab in ulcerative colitis",
     ["etrolizumab"], ["ulcerative colitis"]),
    # Batch 2 — additional newer drugs (2026-05-13 +95 push)
    ("OFATUMUMAB_MS_AUTO", "Ofatumumab in multiple sclerosis",
     ["ofatumumab"], ["multiple sclerosis"]),
    ("OZANIMOD_MS_AUTO", "Ozanimod in MS",
     ["ozanimod"], ["multiple sclerosis"]),
    ("PONESIMOD_MS_AUTO", "Ponesimod in MS",
     ["ponesimod"], ["multiple sclerosis"]),
    ("SIPONIMOD_MS_AUTO", "Siponimod in MS",
     ["siponimod"], ["multiple sclerosis"]),
    ("OCRELIZUMAB_MS_AUTO", "Ocrelizumab in MS",
     ["ocrelizumab"], ["multiple sclerosis"]),
    ("CLADRIBINE_MS_AUTO", "Cladribine in MS",
     ["cladribine"], ["multiple sclerosis"]),
    ("ISAVUCONAZOLE_FUNGAL_AUTO", "Isavuconazole for invasive fungal",
     ["isavuconazole"], ["aspergillosis", "mucormycosis"]),
    ("POSACONAZOLE_FUNGAL_AUTO", "Posaconazole prophylaxis",
     ["posaconazole"], ["fungal", "candidiasis"]),
    ("ANIDULAFUNGIN_CANDIDA_AUTO", "Anidulafungin in candidemia",
     ["anidulafungin"], ["candidiasis", "candidemia"]),
    ("RSV_VACCINE_AREXVY_AUTO", "RSV vaccine in older adults (AREXVY/ABRYSVO)",
     ["rsvpref", "rsv vaccine", "rsv subunit"], ["respiratory syncytial"]),
    ("NIRSEVIMAB_INFANT_AUTO", "Nirsevimab for infant RSV prevention",
     ["nirsevimab"], ["respiratory syncytial"]),
    ("DENGUE_VACCINE_TAK003_AUTO", "Dengue vaccine TAK-003",
     ["tak-003", "qdenga"], ["dengue"]),
    ("MALARIA_R21_AUTO", "Malaria R21/Matrix-M vaccine",
     ["r21", "matrix-m"], ["malaria"]),
    ("BELIMUMAB_LUPUS_AUTO", "Belimumab in SLE",
     ["belimumab"], ["lupus"]),
    ("ANIFROLUMAB_LUPUS_AUTO", "Anifrolumab in SLE",
     ["anifrolumab"], ["lupus"]),
    ("VOCLOSPORIN_LN_AUTO", "Voclosporin in lupus nephritis",
     ["voclosporin"], ["lupus nephritis"]),
    ("RITUXIMAB_RA_AUTO", "Rituximab in RA",
     ["rituximab"], ["rheumatoid arthritis"]),
    ("TOFACITINIB_AS_AUTO", "Tofacitinib in ankylosing spondylitis",
     ["tofacitinib"], ["ankylosing", "axial spondyl"]),
    ("BARICITINIB_AA_AUTO", "Baricitinib in alopecia areata",
     ["baricitinib"], ["alopecia"]),
    ("RITLECITINIB_AA_AUTO", "Ritlecitinib in alopecia areata",
     ["ritlecitinib"], ["alopecia"]),
    ("RUXOLITINIB_VITILIGO_AUTO", "Ruxolitinib topical in vitiligo",
     ["ruxolitinib"], ["vitiligo"]),
    ("ENSIFENTRINE_COPD_AUTO", "Ensifentrine in COPD",
     ["ensifentrine"], ["pulmonary disease"]),
    ("DAROLUTAMIDE_PROSTATE_AUTO", "Darolutamide in prostate cancer",
     ["darolutamide"], ["prostat"]),
    ("APALUTAMIDE_PROSTATE_AUTO", "Apalutamide in prostate cancer",
     ["apalutamide"], ["prostat"]),
    ("ENZALUTAMIDE_PROSTATE_AUTO", "Enzalutamide in prostate cancer",
     ["enzalutamide"], ["prostat"]),
    ("ROXADUSTAT_RENAL_ANEMIA_AUTO", "Roxadustat in renal anaemia",
     ["roxadustat"], ["anemia"]),
    ("VADADUSTAT_RENAL_ANEMIA_AUTO", "Vadadustat in renal anaemia",
     ["vadadustat"], ["anemia"]),
    ("DAPRODUSTAT_RENAL_ANEMIA_AUTO", "Daprodustat in renal anaemia",
     ["daprodustat"], ["anemia"]),
    ("BEPIROVIRSEN_HBV_AUTO", "Bepirovirsen ASO HBV functional cure",
     ["bepirovirsen"], ["hepatitis b"]),
    ("NIRSEVIMAB_INFANT_AUTO", "Nirsevimab infant RSV",
     ["nirsevimab"], ["respiratory syncytial"]),
    # Batch 3 — final push to cross 300
    ("FOSTAMATINIB_ITP_AUTO", "Fostamatinib in chronic ITP",
     ["fostamatinib"], ["thrombocytopenic purpura"]),
    ("AVATROMBOPAG_ITP_AUTO", "Avatrombopag in ITP",
     ["avatrombopag"], ["thrombocytopen"]),
    ("ELTROMBOPAG_AA_AUTO", "Eltrombopag in aplastic anemia",
     ["eltrombopag"], ["aplastic anemia"]),
    ("ROMIPLOSTIM_ITP_AUTO", "Romiplostim in chronic ITP",
     ["romiplostim"], ["thrombocytopen"]),
    ("GIVOSIRAN_PORPHYRIA_AUTO", "Givosiran in acute hepatic porphyria",
     ["givosiran"], ["porphyria"]),
    ("LUMASIRAN_PH1_AUTO", "Lumasiran in primary hyperoxaluria 1",
     ["lumasiran"], ["hyperoxaluria"]),
    ("NUSINERSEN_SMA_AUTO", "Nusinersen in spinal muscular atrophy",
     ["nusinersen"], ["spinal muscular atrophy"]),
    ("RISDIPLAM_SMA_AUTO", "Risdiplam in spinal muscular atrophy",
     ["risdiplam"], ["spinal muscular atrophy"]),

    # Batch 4 — push to 400 (k≥2 required)
    # Cardio / lipid / antiplatelet
    ("TICAGRELOR_NSTEMI_AUTO", "Ticagrelor in NSTE-ACS",
     ["ticagrelor"], ["coronary syndrome", "myocardial infarction"]),
    ("PRASUGREL_ACS_AUTO", "Prasugrel in ACS",
     ["prasugrel"], ["coronary syndrome"]),
    ("CANGRELOR_PCI_AUTO", "Cangrelor in PCI",
     ["cangrelor"], ["coronary intervention"]),
    ("ASUNDEXIAN_AF_AUTO", "Asundexian factor XIa for AF",
     ["asundexian"], ["atrial fibrillation"]),
    ("ABELACIMAB_VTE_AUTO", "Abelacimab factor XI for VTE",
     ["abelacimab"], ["thromboembolism"]),
    ("MILVEXIAN_AF_AUTO", "Milvexian factor XIa for AF",
     ["milvexian"], ["atrial fibrillation", "stroke"]),
    ("BAXDROSTAT_HTN_AUTO", "Baxdrostat in resistant hypertension",
     ["baxdrostat", "cin-107"], ["hypertension"]),
    ("LORUNDROSTAT_HTN_AUTO", "Lorundrostat in hypertension",
     ["lorundrostat"], ["hypertension"]),
    ("ZILEBESIRAN_HTN_AUTO", "Zilebesiran siRNA for hypertension",
     ["zilebesiran"], ["hypertension"]),
    ("MAVACAMTEN_OHCM_AUTO", "Mavacamten in obstructive HCM",
     ["mavacamten"], ["hypertrophic cardiomyopathy"]),
    ("AFICAMTEN_HCM2_AUTO", "Aficamten in obstructive HCM",
     ["aficamten"], ["hypertrophic cardiomyopathy"]),
    ("CSL112_ACS_AUTO", "CSL112 apoA1 infusion post-MI",
     ["csl112", "csl 112"], ["myocardial infarction"]),
    ("OLEZARSEN_TG_AUTO", "Olezarsen for hypertriglyceridemia",
     ["olezarsen"], ["hypertriglyceridemia"]),
    ("VOLANESORSEN_FCS_AUTO", "Volanesorsen in familial chylomicronemia",
     ["volanesorsen"], ["chylomicronemia"]),
    ("EVINACUMAB_HOFH_AUTO", "Evinacumab in homozygous FH",
     ["evinacumab"], ["hypercholesterolemia"]),

    # Oncology — IO/TKI/ADC variations
    ("CILTACABTAGENE_MM_AUTO", "Ciltacabtagene autoleucel BCMA CAR-T MM",
     ["ciltacabtagene", "cilta-cel", "jnj-68284528"], ["multiple myeloma"]),
    ("IDECABTAGENE_MM_AUTO", "Idecabtagene vicleucel BCMA CAR-T MM",
     ["idecabtagene", "ide-cel", "bb2121"], ["multiple myeloma"]),
    ("LIFILEUCEL_MELANOMA_AUTO", "Lifileucel TIL melanoma",
     ["lifileucel"], ["melanoma"]),
    ("RELATLIMAB_MELANOMA_AUTO", "Relatlimab + nivolumab melanoma",
     ["relatlimab"], ["melanoma"]),
    ("SOTORASIB_KRAS_AUTO", "Sotorasib KRAS-G12C NSCLC",
     ["sotorasib", "amg 510"], ["non-small cell lung"]),
    ("ADAGRASIB_KRAS_AUTO", "Adagrasib KRAS-G12C NSCLC",
     ["adagrasib", "mrtx849"], ["non-small cell lung"]),
    ("LAROTRECTINIB_NTRK_AUTO", "Larotrectinib NTRK+ solid tumors",
     ["larotrectinib"], ["neoplasm", "lung", "colorect"]),
    ("ENTRECTINIB_ROS1_AUTO", "Entrectinib ROS1+ NSCLC",
     ["entrectinib"], ["non-small cell lung"]),
    ("REPOTRECTINIB_ROS1_AUTO", "Repotrectinib ROS1+ NSCLC",
     ["repotrectinib"], ["non-small cell lung"]),
    ("CRIZOTINIB_ALK_AUTO", "Crizotinib ALK+ NSCLC",
     ["crizotinib"], ["non-small cell lung"]),
    ("CERITINIB_ALK_AUTO", "Ceritinib ALK+ NSCLC",
     ["ceritinib"], ["non-small cell lung"]),
    ("DABRAFENIB_TRAMETINIB_AUTO", "Dabrafenib + trametinib BRAF+",
     ["dabrafenib"], ["melanoma", "non-small cell lung", "thyroid"]),
    ("VEMURAFENIB_MELANOMA_AUTO", "Vemurafenib BRAF+ melanoma",
     ["vemurafenib"], ["melanoma"]),
    ("ENCORAFENIB_CRC_AUTO", "Encorafenib BRAF+ CRC",
     ["encorafenib"], ["colorect"]),
    ("PERTUZUMAB_BREAST_AUTO", "Pertuzumab in HER2+ breast",
     ["pertuzumab"], ["breast"]),
    ("TRASTUZUMAB_EMTANSINE_AUTO", "T-DM1 in HER2+ breast",
     ["ado-trastuzumab emtansine", "trastuzumab emtansine", "t-dm1"], ["breast"]),
    ("MARGETUXIMAB_BREAST_AUTO", "Margetuximab in HER2+ breast",
     ["margetuximab"], ["breast"]),
    ("TUCATINIB_BREAST_AUTO", "Tucatinib in HER2+ breast",
     ["tucatinib"], ["breast"]),
    ("ENHERTU_GASTRIC_AUTO", "T-DXd in HER2+ gastric",
     ["trastuzumab deruxtecan", "ds-8201", "fam-trastuzumab"], ["gastric"]),
    ("PEMBROLIZUMAB_ESOPHAGEAL_AUTO", "Pembrolizumab in esophageal/GEJ",
     ["pembrolizumab"], ["esophageal"]),
    ("NIVOLUMAB_HCC_AUTO", "Nivolumab in HCC",
     ["nivolumab"], ["hepatocellular"]),
    ("ATEZOLIZUMAB_BEVACIZUMAB_HCC_AUTO", "Atezolizumab + bevacizumab HCC",
     ["atezolizumab"], ["hepatocellular"]),
    ("DURVALUMAB_BILIARY_AUTO", "Durvalumab in biliary tract",
     ["durvalumab"], ["biliary", "cholangiocarcinoma"]),
    ("NIVOLUMAB_ESOPHAGEAL_AUTO", "Nivolumab in esophageal",
     ["nivolumab"], ["esophageal"]),
    ("PEMBROLIZUMAB_HNSCC_AUTO", "Pembrolizumab in HNSCC",
     ["pembrolizumab"], ["head and neck"]),
    ("CEMIPLIMAB_CSCC_AUTO", "Cemiplimab in cutaneous SCC",
     ["cemiplimab"], ["squamous cell"]),
    ("AVELUMAB_MCC_AUTO", "Avelumab in Merkel cell",
     ["avelumab"], ["merkel"]),
    ("PEMBROLIZUMAB_TNBC_AUTO", "Pembrolizumab in TNBC",
     ["pembrolizumab"], ["triple negative", "triple-negative"]),
    ("AXICABTAGENE_LBCL_AUTO", "Axicabtagene ciloleucel CD19 CAR-T LBCL",
     ["axicabtagene", "axi-cel", "kte-c19"], ["large b-cell"]),
    ("LISOCABTAGENE_LBCL_AUTO", "Lisocabtagene maraleucel CD19 CAR-T LBCL",
     ["lisocabtagene", "liso-cel"], ["large b-cell"]),
    ("TISAGENLECLEUCEL_LBCL_AUTO", "Tisagenlecleucel CD19 CAR-T LBCL/ALL",
     ["tisagenlecleucel", "tisa-cel"], ["large b-cell", "lymphoblastic"]),
    ("BLINATUMOMAB_ALL_AUTO", "Blinatumomab CD19 BiTE ALL",
     ["blinatumomab"], ["lymphoblastic"]),
    ("INOTUZUMAB_ALL_AUTO", "Inotuzumab ozogamicin ALL",
     ["inotuzumab"], ["lymphoblastic"]),
    ("CAPLACIZUMAB_TTP_AUTO", "Caplacizumab in immune TTP",
     ["caplacizumab"], ["thrombotic thrombocytopenic"]),
    ("MOSUNETUZUMAB_FL_AUTO", "Mosunetuzumab in R/R follicular lymphoma",
     ["mosunetuzumab"], ["follicular lymphoma", "lymphoma"]),
    ("POLATUZUMAB_LBCL_AUTO", "Polatuzumab vedotin in LBCL",
     ["polatuzumab"], ["large b-cell", "lymphoma"]),
    ("LONCASTUXIMAB_LBCL_AUTO", "Loncastuximab tesirine in LBCL",
     ["loncastuximab"], ["large b-cell", "lymphoma"]),
    ("TAFASITAMAB_LBCL_AUTO", "Tafasitamab + lenalidomide LBCL",
     ["tafasitamab"], ["large b-cell", "lymphoma"]),
    ("OBINUTUZUMAB_LYMPHOMA_AUTO", "Obinutuzumab in CD20+ lymphoma",
     ["obinutuzumab"], ["lymphoma", "lymphocytic leukemia"]),
    ("BENDAMUSTINE_LYMPHOMA_AUTO", "Bendamustine in indolent lymphoma",
     ["bendamustine"], ["lymphoma"]),
    ("LENALIDOMIDE_MM_AUTO", "Lenalidomide in multiple myeloma",
     ["lenalidomide"], ["multiple myeloma"]),
    ("POMALIDOMIDE_MM_AUTO", "Pomalidomide in R/R MM",
     ["pomalidomide"], ["multiple myeloma"]),
    ("IXAZOMIB_MM_AUTO", "Ixazomib in MM",
     ["ixazomib"], ["multiple myeloma"]),
    ("SELINEXOR_MM_AUTO", "Selinexor in R/R MM",
     ["selinexor"], ["multiple myeloma"]),
    ("ZANUBRUTINIB_CLL_AUTO", "Zanubrutinib in CLL",
     ["zanubrutinib"], ["chronic lymphocytic"]),
    ("IBRUTINIB_CLL_AUTO", "Ibrutinib in CLL",
     ["ibrutinib"], ["chronic lymphocytic"]),
    ("IBRUTINIB_MCL_AUTO", "Ibrutinib in MCL",
     ["ibrutinib"], ["mantle"]),

    # Endocrine / metabolic
    ("TEPROTUMUMAB_TED_AUTO", "Teprotumumab in thyroid eye disease",
     ["teprotumumab"], ["graves", "thyroid"]),
    ("PALOPEGTERIPARATIDE_HPP_AUTO", "Palopegteriparatide hypoparathyroidism",
     ["palopegteriparatide", "transcon pth"], ["hypoparathyroid"]),
    ("BURATEKINOL_HYPONA_AUTO", "Tolvaptan in hyponatremia",
     ["tolvaptan"], ["hyponatremia"]),
    ("TOLVAPTAN_ADPKD_AUTO", "Tolvaptan in ADPKD",
     ["tolvaptan"], ["polycystic kidney"]),

    # GI/Liver
    ("VONOPRAZAN_GERD_AUTO", "Vonoprazan in GERD",
     ["vonoprazan"], ["gastroesophageal reflux"]),
    ("LINACLOTIDE_IBS_AUTO", "Linaclotide in IBS-C",
     ["linaclotide"], ["irritable bowel"]),
    ("PLECANATIDE_IBS_AUTO", "Plecanatide in CIC/IBS-C",
     ["plecanatide"], ["constipation"]),
    ("VIBEGRON_OAB_AUTO", "Vibegron in overactive bladder",
     ["vibegron"], ["overactive bladder", "bladder"]),
    ("MIRABEGRON_OAB_AUTO", "Mirabegron in OAB",
     ["mirabegron"], ["overactive bladder", "bladder"]),

    # Vaccines / ID
    ("GLECAPREVIR_PIBRENTASVIR_HCV_AUTO", "Glecaprevir/pibrentasvir HCV",
     ["glecaprevir"], ["hepatitis c"]),
    ("SOFOSBUVIR_VELPATASVIR_HCV_AUTO", "Sofosbuvir/velpatasvir HCV",
     ["sofosbuvir"], ["hepatitis c"]),
    ("MARIBAVIR_CMV_AUTO", "Maribavir in resistant CMV",
     ["maribavir"], ["cytomegalovirus"]),
    ("LETERMOVIR_CMV_AUTO", "Letermovir in CMV prevention HCT",
     ["letermovir"], ["cytomegalovirus"]),
    ("CEFTAZIDIME_AVIBACTAM_AUTO", "Ceftazidime-avibactam CRE",
     ["ceftazidime-avibactam", "avycaz"], ["gram-negative", "carbapenem"]),
    ("MEROPENEM_VABORBACTAM_AUTO", "Meropenem-vaborbactam CRE",
     ["meropenem-vaborbactam", "meropenem/vaborbactam"], ["gram-negative"]),
    ("CEFIDEROCOL_GRAM_AUTO", "Cefiderocol multidrug-resistant gram-",
     ["cefiderocol"], ["gram-negative"]),
    ("ERAVACYCLINE_INFECTION_AUTO", "Eravacycline complicated intra-abdominal",
     ["eravacycline"], ["intra-abdominal"]),
    ("LEFAMULIN_CABP_AUTO", "Lefamulin CABP",
     ["lefamulin"], ["pneumonia"]),
    ("OMADACYCLINE_INFECTION_AUTO", "Omadacycline ABSSSI/CABP",
     ["omadacycline"], ["skin infection", "pneumonia"]),
    ("DELAFLOXACIN_INFECTION_AUTO", "Delafloxacin in ABSSSI",
     ["delafloxacin"], ["skin"]),
    ("DALBAVANCIN_ABSSSI_AUTO", "Dalbavancin in ABSSSI",
     ["dalbavancin"], ["skin"]),
    ("ORITAVANCIN_ABSSSI_AUTO", "Oritavancin in ABSSSI",
     ["oritavancin"], ["skin"]),
    ("LASCUFLOXACIN_PNEUMONIA_AUTO", "Lascufloxacin in CABP",
     ["lascufloxacin"], ["pneumonia"]),
    ("FOSFOMYCIN_UTI_AUTO", "Fosfomycin in UTI",
     ["fosfomycin"], ["urinary tract infection"]),

    # Respiratory / pulm
    ("REVEFENACIN_COPD_AUTO", "Revefenacin LAMA in COPD",
     ["revefenacin"], ["pulmonary disease"]),
    ("UMECLIDINIUM_VILANTEROL_AUTO", "Umeclidinium/vilanterol COPD",
     ["umeclidinium"], ["pulmonary disease"]),
    ("FLUTICASONE_UMECLIDINIUM_VILANTEROL_AUTO", "Triple therapy FF/UMEC/VI COPD",
     ["fluticasone furoate"], ["pulmonary disease"]),
    ("PIRFENIDONE_IPF_AUTO", "Pirfenidone in IPF",
     ["pirfenidone"], ["pulmonary fibrosis"]),
    ("NINTEDANIB_IPF_AUTO", "Nintedanib in IPF/SSc-ILD/PPF",
     ["nintedanib"], ["pulmonary fibrosis", "interstitial lung"]),
    ("BREZTRI_COPD_AUTO", "Budesonide/glycopyrrolate/formoterol COPD",
     ["budesonide"], ["pulmonary disease"]),

    # Pediatric / SMA
    ("ONASEMNOGENE_SMA_AUTO", "Onasemnogene abeparvovec in SMA",
     ["onasemnogene"], ["spinal muscular atrophy"]),

    # Hematology / blood
    ("CRIZANLIZUMAB_SCD2_AUTO", "Crizanlizumab in SCD VOC",
     ["crizanlizumab"], ["sickle"]),
    ("LUSPATERCEPT_MDS2_AUTO", "Luspatercept transfusion-dep MDS-RS",
     ["luspatercept"], ["myelodysplastic"]),
    ("DECITABINE_CEDAZURIDINE_AUTO", "Oral decitabine-cedazuridine MDS",
     ["decitabine", "cedazuridine"], ["myelodysplastic"]),
    ("PEGCETACOPLAN_PNH_AUTO", "Pegcetacoplan in PNH",
     ["pegcetacoplan"], ["paroxysmal nocturnal hemoglobinuria"]),
    ("RAVULIZUMAB_PNH_AUTO", "Ravulizumab in PNH",
     ["ravulizumab"], ["paroxysmal nocturnal hemoglobinuria"]),
    ("ECULIZUMAB_PNH_AUTO", "Eculizumab in PNH",
     ["eculizumab"], ["paroxysmal nocturnal hemoglobinuria"]),

    # Ophthalmology
    ("PEGCETACOPLAN_GA_AUTO", "Pegcetacoplan in geographic atrophy",
     ["pegcetacoplan"], ["geographic atrophy"]),
    ("AVACINCAPTAD_GA_AUTO", "Avacincaptad pegol GA",
     ["avacincaptad"], ["geographic atrophy"]),
    ("BROLUCIZUMAB_NAMD_AUTO", "Brolucizumab nAMD",
     ["brolucizumab"], ["macular degeneration"]),
    ("BIMATOPROST_GLAUCOMA_AUTO", "Bimatoprost SR implant glaucoma",
     ["bimatoprost"], ["glaucoma"]),
    ("LATANOPROSTENE_GLAUCOMA_AUTO", "Latanoprostene bunod glaucoma",
     ["latanoprostene"], ["glaucoma"]),
    ("ROCKLATAN_GLAUCOMA_AUTO", "Netarsudil-latanoprost glaucoma",
     ["netarsudil"], ["glaucoma"]),

    # Newer biologics
    ("AVALGLUCOSIDASE_POMPE_AUTO", "Avalglucosidase alfa in Pompe",
     ["avalglucosidase"], ["pompe", "glycogen storage"]),
    ("OLIPUDASE_NPB_AUTO", "Olipudase alfa in Niemann-Pick B",
     ["olipudase"], ["niemann-pick"]),
    ("PEGUNIGALSIDASE_FABRY_AUTO", "Pegunigalsidase alfa Fabry",
     ["pegunigalsidase"], ["fabry"]),
    ("CIPAGLUCOSIDASE_POMPE_AUTO", "Cipaglucosidase alfa + miglustat Pompe",
     ["cipaglucosidase"], ["pompe"]),
    ("TIVERVEND_HEMOPHILIA_AUTO", "Etranacogene gene therapy hemophilia B",
     ["etranacogene"], ["hemophilia"]),
    ("VALOCTOCOGENE_HEMA_AUTO", "Valoctocogene gene therapy hemophilia A",
     ["valoctocogene"], ["hemophilia"]),
    ("EMICIZUMAB_HEMA_AUTO", "Emicizumab in hemophilia A",
     ["emicizumab"], ["hemophilia"]),
    ("FITUSIRAN_HEM_AUTO", "Fitusiran siRNA in hemophilia",
     ["fitusiran"], ["hemophilia"]),
    ("CONCIZUMAB_HEM_AUTO", "Concizumab anti-TFPI hemophilia",
     ["concizumab"], ["hemophilia"]),

    # Dermatology / immunology
    ("ABROCITINIB_AD_AUTO", "Abrocitinib in atopic dermatitis",
     ["abrocitinib"], ["dermatitis", "atopic"]),
    ("TRALOKINUMAB_AD_AUTO", "Tralokinumab in atopic dermatitis",
     ["tralokinumab"], ["dermatitis"]),
    ("DELGOCITINIB_AD_AUTO", "Delgocitinib topical AD",
     ["delgocitinib"], ["dermatitis"]),
    ("ROFLUMILAST_PSORIASIS_AUTO", "Topical roflumilast psoriasis/AD",
     ["roflumilast"], ["psoriasis", "dermatitis"]),
    ("TAPINAROF_PSORIASIS_AUTO", "Tapinarof in psoriasis",
     ["tapinarof"], ["psoriasis"]),

    # Renal
    ("FERIC_CITRATE_HYPERPHOS_AUTO", "Ferric citrate phosphate binder",
     ["ferric citrate"], ["hyperphosphatemia", "chronic kidney"]),
    ("TENAPANOR_HYPERPHOS_AUTO", "Tenapanor in hyperphosphatemia",
     ["tenapanor"], ["hyperphosphatemia"]),
    ("DIFELIKEFALIN_PRURITUS_AUTO", "Difelikefalin in HD pruritus",
     ["difelikefalin"], ["pruritus"]),

    # Vasculitis / nephro
    ("BELIMUMAB_LN_AUTO", "Belimumab in lupus nephritis",
     ["belimumab"], ["lupus nephritis"]),
    ("OBINUTUZUMAB_LN_AUTO", "Obinutuzumab in lupus nephritis",
     ["obinutuzumab"], ["lupus nephritis"]),

    # Psychiatry / addiction
    ("BUPRENORPHINE_OUD_AUTO", "Buprenorphine MOUD",
     ["buprenorphine"], ["opioid"]),
    ("NALTREXONE_OUD_AUTO", "Naltrexone XR in OUD",
     ["naltrexone"], ["opioid"]),
    ("PSILOCYBIN_TRD_AUTO", "Psilocybin in TRD",
     ["psilocybin"], ["depress"]),
    ("KARXT_SCHIZO_AUTO", "Xanomeline-trospium (KarXT) schizophrenia",
     ["xanomeline"], ["schizophrenia"]),
    ("BREXPIPRAZOLE_AGITATION_AUTO", "Brexpiprazole AD agitation",
     ["brexpiprazole"], ["alzheimer", "dementia"]),
    ("CARIPRAZINE_DEPRESSION_AUTO", "Cariprazine adjunct MDD",
     ["cariprazine"], ["depress"]),

    # Batch 5 — push past 400 final stretch
    ("AGRYLIN_ET_AUTO", "Anagrelide in essential thrombocythemia",
     ["anagrelide"], ["thrombocythemia", "myeloproliferative"]),
    ("RUXOLITINIB_PV_AUTO", "Ruxolitinib in polycythemia vera",
     ["ruxolitinib"], ["polycythemia vera"]),
    ("RUXOLITINIB_GVHD_AUTO", "Ruxolitinib in steroid-refractory GVHD",
     ["ruxolitinib"], ["graft versus host", "graft-versus-host"]),
    ("FEDRATINIB_MF_AUTO", "Fedratinib in myelofibrosis",
     ["fedratinib"], ["myelofibrosis"]),
    ("PACRITINIB_MF_AUTO", "Pacritinib in myelofibrosis",
     ["pacritinib"], ["myelofibrosis"]),
    ("MOMELOTINIB_MF_AUTO", "Momelotinib in myelofibrosis with anemia",
     ["momelotinib"], ["myelofibrosis"]),
    ("ZOLBETUXIMAB_GASTRIC_AUTO", "Zolbetuximab CLDN18.2 gastric",
     ["zolbetuximab"], ["gastric"]),
    ("NIRAPARIB_PROSTATE_AUTO", "Niraparib in mCRPC",
     ["niraparib"], ["prostat"]),
    ("OLAPARIB_PROSTATE_AUTO", "Olaparib in mCRPC",
     ["olaparib"], ["prostat"]),
    ("TALAZOPARIB_BREAST_AUTO", "Talazoparib in BRCA+ breast",
     ["talazoparib"], ["breast"]),
    ("REGORAFENIB_CRC_AUTO", "Regorafenib in mCRC",
     ["regorafenib"], ["colorect"]),
    ("CABOZANTINIB_RCC_AUTO", "Cabozantinib in advanced RCC",
     ["cabozantinib"], ["renal cell"]),
    ("CABOZANTINIB_HCC_AUTO", "Cabozantinib in HCC",
     ["cabozantinib"], ["hepatocellular"]),
    ("SUNITINIB_RCC_AUTO", "Sunitinib in advanced RCC",
     ["sunitinib"], ["renal cell"]),
    ("AXITINIB_RCC_AUTO", "Axitinib in advanced RCC",
     ["axitinib"], ["renal cell"]),
    ("LENVATINIB_HCC_AUTO", "Lenvatinib in HCC",
     ["lenvatinib"], ["hepatocellular"]),
    ("LENVATINIB_THYROID_AUTO", "Lenvatinib in differentiated thyroid",
     ["lenvatinib"], ["thyroid"]),
    ("SORAFENIB_HCC_AUTO", "Sorafenib in HCC",
     ["sorafenib"], ["hepatocellular"]),
    ("BEVACIZUMAB_CRC_AUTO", "Bevacizumab in mCRC",
     ["bevacizumab"], ["colorect"]),
    ("BEVACIZUMAB_OVARIAN_AUTO", "Bevacizumab in ovarian",
     ["bevacizumab"], ["ovarian"]),
    ("CETUXIMAB_CRC_AUTO", "Cetuximab in RAS-WT mCRC",
     ["cetuximab"], ["colorect"]),
    ("PANITUMUMAB_CRC_AUTO", "Panitumumab in RAS-WT mCRC",
     ["panitumumab"], ["colorect"]),
    ("AFLIBERCEPT_CRC_AUTO", "Aflibercept in mCRC",
     ["aflibercept"], ["colorect"]),
    ("RAMUCIRUMAB_GASTRIC_AUTO", "Ramucirumab in gastric",
     ["ramucirumab"], ["gastric"]),
    ("RIPRETINIB_GIST_AUTO", "Ripretinib in advanced GIST",
     ["ripretinib"], ["gastrointestinal stromal"]),
    ("AVAPRITINIB_GIST_AUTO", "Avapritinib in PDGFRA-mut GIST",
     ["avapritinib"], ["gastrointestinal stromal", "mast cell"]),
    ("PALAZESTRANT_BREAST_AUTO", "Palazestrant in HR+ breast",
     ["palazestrant", "elacestrant"], ["breast"]),
    ("ELACESTRANT_BREAST_AUTO", "Elacestrant in ESR1-mut HR+ breast",
     ["elacestrant"], ["breast"]),
    ("CAPIVASERTIB_BREAST_AUTO", "Capivasertib in HR+ breast",
     ["capivasertib"], ["breast"]),
    ("ALPELISIB_BREAST_AUTO", "Alpelisib in PIK3CA+ breast",
     ["alpelisib"], ["breast"]),

    # Newer cardiology / lipid / heart failure
    ("OMECAMTIV_HFREF_AUTO", "Omecamtiv mecarbil in HFrEF (GALACTIC-HF)",
     ["omecamtiv"], ["heart failure"]),
    ("ELAMIPRETIDE_AUTO", "Elamipretide in primary mitochondrial",
     ["elamipretide"], ["mitochondrial", "cardiomyopath"]),
    ("REZAFUNGIN_CANDIDIASIS_AUTO", "Rezafungin in candidemia/invasive candidiasis",
     ["rezafungin"], ["candidemia", "candidiasis"]),
    ("CINPANEMAB_ALPHASYN_AUTO", "Cinpanemab in PD α-synuclein",
     ["cinpanemab"], ["parkinson"]),
    ("PRASINEZUMAB_PD_AUTO", "Prasinezumab in Parkinson disease",
     ["prasinezumab"], ["parkinson"]),
    ("DAXIBOTULINUM_AUTO", "DaxibotulinumtoxinA in cervical dystonia",
     ["daxibotulinumtoxin"], ["dystonia", "glabellar"]),

    # Migraine / pain
    ("FENFLURAMINE_DRAVET_AUTO", "Fenfluramine in Dravet syndrome",
     ["fenfluramine"], ["dravet", "lennox", "epilep"]),
    ("CENOBAMATE_EPILEPSY_AUTO", "Cenobamate in focal epilepsy",
     ["cenobamate"], ["epilep", "seizure"]),
    ("PERAMPANEL_EPILEPSY_AUTO", "Perampanel in focal/generalised epilepsy",
     ["perampanel"], ["epilep", "seizure"]),
    ("BRIVARACETAM_EPILEPSY_AUTO", "Brivaracetam in focal epilepsy",
     ["brivaracetam"], ["epilep", "seizure"]),
    ("EVERAPLAY_PD_AUTO", "Foslevodopa-foscarbidopa Parkinson",
     ["foslevodopa", "foscarbidopa"], ["parkinson"]),
    ("OPICAPONE_PD_AUTO", "Opicapone COMT-inhibitor PD",
     ["opicapone"], ["parkinson"]),
    ("SAFINAMIDE_PD_AUTO", "Safinamide adjunct PD",
     ["safinamide"], ["parkinson"]),
    ("ISTRADEFYLLINE_PD_AUTO", "Istradefylline A2A in PD",
     ["istradefylline"], ["parkinson"]),

    # Headache / pain newer
    ("ATOGEPANT_PREVENT_AUTO", "Atogepant migraine prevention QUARTET",
     ["atogepant"], ["migraine"]),
    ("LASMIDITAN_ACUTE_AUTO", "Lasmiditan acute migraine",
     ["lasmiditan"], ["migraine"]),

    # Diabetes / metabolic
    ("LIRAGLUTIDE_T2D_CV_AUTO", "Liraglutide T2D CVOT (LEADER)",
     ["liraglutide"], ["type 2 diabetes"]),
    ("DULAGLUTIDE_T2D_CV_AUTO", "Dulaglutide T2D CVOT (REWIND)",
     ["dulaglutide"], ["type 2 diabetes"]),
    ("ALBIGLUTIDE_T2D_AUTO", "Albiglutide T2D CVOT",
     ["albiglutide"], ["type 2 diabetes"]),
    ("EXENATIDE_T2D_CV_AUTO", "Exenatide T2D CVOT EXSCEL",
     ["exenatide"], ["type 2 diabetes"]),
    ("LIXISENATIDE_T2D_AUTO", "Lixisenatide T2D ELIXA",
     ["lixisenatide"], ["type 2 diabetes"]),
    ("PIOGLITAZONE_STROKE_AUTO", "Pioglitazone post-stroke IRIS",
     ["pioglitazone"], ["stroke", "transient ischemic"]),

    # GU / oncology pivotals
    ("RUCAPARIB_PROSTATE_AUTO", "Rucaparib in BRCA+ prostate",
     ["rucaparib"], ["prostat"]),
    ("ABIRATERONE_PROSTATE_AUTO", "Abiraterone in mCRPC/mHSPC",
     ["abiraterone"], ["prostat"]),
    ("OLAPARIB_PANCREATIC_AUTO", "Olaparib in BRCA+ pancreatic",
     ["olaparib"], ["pancreatic"]),

    # Newer biologics
    ("ROZANOLIXIZUMAB_MG_AUTO", "Rozanolixizumab in myasthenia gravis",
     ["rozanolixizumab"], ["myasthenia"]),
    ("ZILUCOPLAN_MG_AUTO", "Zilucoplan in MG",
     ["zilucoplan"], ["myasthenia"]),
    ("RITUXIMAB_MG_AUTO", "Rituximab in MG",
     ["rituximab"], ["myasthenia"]),
    ("BURIMAB_NMOSD_AUTO", "Inebilizumab in NMOSD",
     ["inebilizumab"], ["neuromyelitis"]),
    ("SATRALIZUMAB_NMOSD_AUTO", "Satralizumab in NMOSD",
     ["satralizumab"], ["neuromyelitis"]),
    ("ECULIZUMAB_NMOSD_AUTO", "Eculizumab in NMOSD",
     ["eculizumab"], ["neuromyelitis"]),

    # Hepatology / GI newer
    ("LIRIRELVIR_HCV_AUTO", "Sofosbuvir/velpatasvir/voxilaprevir",
     ["sofosbuvir"], ["hepatitis c"]),
    ("EFRUXIFERMIN_NASH_AUTO", "Efruxifermin FGF21 in NASH/MASH",
     ["efruxifermin"], ["steatohepatitis", "nonalcoholic"]),
    ("PEGOZAFERMIN_NASH_AUTO", "Pegozafermin in NASH",
     ["pegozafermin"], ["steatohepatitis"]),
    ("SEMAGLUTIDE_PCOS_AUTO", "Semaglutide in PCOS",
     ["semaglutide"], ["polycystic ovary"]),

    # Antithrombotic / cardiology newer
    ("CLOPIDOGREL_ACS_NEW_AUTO", "Clopidogrel monotherapy short DAPT",
     ["clopidogrel"], ["coronary syndrome"]),
    ("BETRIXABAN_VTE_AUTO", "Betrixaban extended VTE prophylaxis",
     ["betrixaban"], ["thromboembolism"]),

    # Newer cardio device approaches
    ("EVOLOCUMAB_HOFH_AUTO", "Evolocumab in homozygous FH",
     ["evolocumab"], ["hypercholesterolemia familial", "homozygous"]),

    # COVID/ID newer
    ("ENSITRELVIR_COVID_AUTO", "Ensitrelvir oral COVID-19",
     ["ensitrelvir", "xocova"], ["covid"]),
    ("SOTROVIMAB_COVID_AUTO", "Sotrovimab monoclonal COVID",
     ["sotrovimab"], ["covid"]),
    ("BAMLANIVIMAB_COVID_AUTO", "Bamlanivimab COVID",
     ["bamlanivimab"], ["covid"]),
    ("CASIRIVIMAB_COVID_AUTO", "Casirivimab/imdevimab COVID",
     ["casirivimab"], ["covid"]),
    ("TIXAGEVIMAB_COVID_AUTO", "Tixagevimab/cilgavimab Evusheld",
     ["tixagevimab"], ["covid"]),

    # Pediatric / rare
    ("ELIGLUSTAT_GAUCHER_AUTO", "Eliglustat in Gaucher disease",
     ["eliglustat"], ["gaucher"]),
    ("MIGLUSTAT_GAUCHER_AUTO", "Miglustat in Gaucher",
     ["miglustat"], ["gaucher", "niemann"]),
    ("VELAGLUCERASE_GAUCHER_AUTO", "Velaglucerase alfa Gaucher",
     ["velaglucerase"], ["gaucher"]),
    ("AGALSIDASE_FABRY_AUTO", "Agalsidase in Fabry",
     ["agalsidase"], ["fabry"]),
    ("MIGALASTAT_FABRY_AUTO", "Migalastat oral in Fabry",
     ["migalastat"], ["fabry"]),
    ("CIPAGLUCOSIDASE_POMPE_AUTO", "Cipaglucosidase + miglustat Pompe",
     ["cipaglucosidase"], ["pompe"]),

    # Newer respiratory
    ("EFGARTIGIMOD_MG_AUTO", "Efgartigimod in generalized MG",
     ["efgartigimod"], ["myasthenia"]),

    # Final cardio fillers
    ("SOTAGLIFLOZIN_T2D_AUTO", "Sotagliflozin in T2D + CKD",
     ["sotagliflozin"], ["type 2 diabetes", "chronic kidney"]),
    ("ERTUGLIFLOZIN_T2D_AUTO", "Ertugliflozin in T2D VERTIS-CV",
     ["ertugliflozin"], ["type 2 diabetes"]),

    # Batch 6 — final 29+
    ("METFORMIN_PCOS_AUTO", "Metformin in PCOS",
     ["metformin"], ["polycystic ovary"]),
    ("MELATONIN_INSOMNIA_AUTO", "Melatonin agonists in insomnia",
     ["ramelteon", "tasimelteon"], ["insomnia"]),
    ("DAR_INSOMNIA_AUTO", "DORAs (suvorexant, lemborexant, daridorexant) insomnia",
     ["suvorexant", "lemborexant", "daridorexant"], ["insomnia"]),
    ("PIMAVANSERIN_PSYCH_AUTO", "Pimavanserin in PD psychosis/AD psychosis",
     ["pimavanserin"], ["parkinson", "psychosis"]),
    ("VALBENAZINE_TD_AUTO", "Valbenazine in tardive dyskinesia",
     ["valbenazine"], ["tardive", "dyskinesia"]),
    ("DEUTETRABENAZINE_HUNTINGTON_AUTO", "Deutetrabenazine in Huntington/TD",
     ["deutetrabenazine"], ["huntington", "tardive"]),
    ("TETRABENAZINE_HUNTINGTON_AUTO", "Tetrabenazine in Huntington",
     ["tetrabenazine"], ["huntington"]),
    ("EDARAVONE_ALS_AUTO", "Edaravone in ALS",
     ["edaravone"], ["amyotrophic"]),
    ("RILUZOLE_ALS_AUTO", "Riluzole in ALS",
     ["riluzole"], ["amyotrophic"]),
    ("INOTERSEN_FAP_AUTO", "Inotersen in hereditary ATTR-PN",
     ["inotersen"], ["amyloidosis"]),
    ("VOSORITIDE_ACH_AUTO", "Vosoritide in achondroplasia",
     ["vosoritide"], ["achondroplasia"]),
    ("SETMELANOTIDE_OBESITY_AUTO", "Setmelanotide in MC4R-pathway obesity",
     ["setmelanotide"], ["obesity"]),
    ("METRELEPTIN_LIPODYSTROPHY_AUTO", "Metreleptin in lipodystrophy",
     ["metreleptin"], ["lipodystrophy"]),
    ("BURATEKINOL_AUTO", "Tolvaptan in hyponatraemia SIADH",
     ["tolvaptan"], ["hyponatremia", "siadh"]),
    ("MITOTANE_ACC_AUTO", "Mitotane in adrenocortical carcinoma",
     ["mitotane"], ["adrenocortical"]),
    ("PASIREOTIDE_ACROMEGALY_AUTO", "Pasireotide in acromegaly",
     ["pasireotide"], ["acromegaly"]),
    ("LANREOTIDE_NET_AUTO", "Lanreotide in neuroendocrine tumors",
     ["lanreotide"], ["neuroendocrine"]),
    ("OCTREOTIDE_NET_AUTO", "Octreotide in NETs/acromegaly",
     ["octreotide"], ["neuroendocrine", "acromegaly"]),
    ("LUTETIUM_DOTATATE_NET_AUTO", "Lutetium-DOTATATE in midgut NETs",
     ["lutetium dotatate", "177lu-dotatate"], ["neuroendocrine"]),
    ("LUTETIUM_PSMA_PROSTATE_AUTO", "Lu-PSMA in mCRPC",
     ["lutetium psma", "lu-177-psma", "177lu-psma"], ["prostat"]),
    ("RADIUM_PROSTATE_AUTO", "Radium-223 in mCRPC",
     ["radium-223", "radium 223", "ra-223"], ["prostat"]),
    ("HISTRELIN_PROSTATE_AUTO", "Histrelin acetate in prostate",
     ["histrelin"], ["prostat"]),
    ("LEUPROLIDE_PROSTATE_AUTO", "Leuprolide in prostate cancer",
     ["leuprolide"], ["prostat"]),
    ("RELUGOLIX_PROSTATE_AUTO", "Relugolix oral GnRH antagonist prostate",
     ["relugolix"], ["prostat"]),
    ("RELUGOLIX_FIBROIDS_AUTO", "Relugolix combination uterine fibroids",
     ["relugolix"], ["fibroid", "uterine leiomyoma"]),
    ("ULIPRISTAL_FIBROIDS_AUTO", "Ulipristal in fibroids",
     ["ulipristal"], ["fibroid"]),
    ("ELAGOLIX_ENDO_AUTO", "Elagolix in endometriosis",
     ["elagolix"], ["endometriosis"]),
    ("PRIMROSE_ELAGOLIX_AUTO", "Elagolix in fibroids",
     ["elagolix"], ["fibroid"]),
    ("DENOSUMAB_BONE_MET_AUTO", "Denosumab in bone metastases",
     ["denosumab"], ["bone neoplasm", "bone metasta"]),
    ("ROMOSOZUMAB_OSTEO_AUTO", "Romosozumab in osteoporosis",
     ["romosozumab"], ["osteoporosis"]),
    ("ABALOPARATIDE_OSTEO_AUTO", "Abaloparatide in osteoporosis",
     ["abaloparatide"], ["osteoporosis"]),
    ("TERIPARATIDE_OSTEO_AUTO", "Teriparatide in osteoporosis",
     ["teriparatide"], ["osteoporosis"]),
    ("DENOSUMAB_OSTEO_AUTO", "Denosumab in postmenopausal osteoporosis",
     ["denosumab"], ["osteoporosis"]),

    # Final additional
    ("RILZABRUTINIB_ITP_AUTO", "Rilzabrutinib BTK in ITP",
     ["rilzabrutinib"], ["thrombocytopenic"]),
    ("MEZAGITAMAB_ITP_AUTO", "Mezagitamab CD38 ITP",
     ["mezagitamab"], ["thrombocytopen"]),
    ("OFATUMUMAB_RA_AUTO", "Ofatumumab in RA",
     ["ofatumumab"], ["rheumatoid arthritis"]),
    ("BARICITINIB_AD_AUTO", "Baricitinib in AD",
     ["baricitinib"], ["atopic", "dermatitis"]),
    ("ABROCITINIB_PED_AUTO", "Abrocitinib pediatric AD",
     ["abrocitinib"], ["dermatitis"]),
    ("BIMEKIZUMAB_AS_AUTO", "Bimekizumab in ankylosing spondylitis",
     ["bimekizumab"], ["ankylosing", "spondyloarthritis"]),
    ("BIMEKIZUMAB_HS_AUTO", "Bimekizumab in hidradenitis suppurativa",
     ["bimekizumab"], ["hidradenitis"]),
    ("SECUKINUMAB_HS_AUTO", "Secukinumab in HS",
     ["secukinumab"], ["hidradenitis"]),
    ("SECUKINUMAB_PSA_AUTO", "Secukinumab in PsA",
     ["secukinumab"], ["psoriatic"]),
    ("IXEKIZUMAB_PSA_AUTO", "Ixekizumab in PsA",
     ["ixekizumab"], ["psoriatic"]),
    ("IXEKIZUMAB_AS_AUTO", "Ixekizumab in AS/axSpA",
     ["ixekizumab"], ["ankylosing", "axial spondyl"]),
    ("BAMUL_HS_AUTO", "Adalimumab in HS",
     ["adalimumab"], ["hidradenitis"]),

    # Batch 7 — push to 500: anesthesia, pain, pediatric, reproductive, surgical, newer rare
    # Anesthesia / pain / sedation
    ("REMIMAZOLAM_SED_AUTO", "Remimazolam for procedural sedation",
     ["remimazolam"], ["sedation", "anesthesia"]),
    ("OLICERIDINE_PAIN_AUTO", "Oliceridine in acute pain",
     ["oliceridine", "trv130"], ["pain"]),
    ("METHOXYFLURANE_PAIN_AUTO", "Methoxyflurane (Penthrox) acute pain",
     ["methoxyflurane"], ["pain"]),
    ("LIPOSOMAL_BUPIVACAINE_AUTO", "Liposomal bupivacaine postoperative",
     ["liposomal bupivacaine", "exparel"], ["postoperative pain", "surgical"]),
    ("KETAMINE_DEPRESSION_AUTO", "Ketamine intranasal/IV depression",
     ["ketamine"], ["depress"]),
    ("DEXMEDETOMIDINE_ICU_AUTO", "Dexmedetomidine in ICU sedation",
     ["dexmedetomidine"], ["sedation", "intensive care"]),
    ("LIDOCAINE_PERIOP_AUTO", "Lidocaine perioperative IV",
     ["lidocaine"], ["postoperative", "surgical"]),
    # Diabetes / endocrine new
    ("CAGRILINTIDE_OBESITY_AUTO", "Cagrilintide-semaglutide CagriSema obesity",
     ["cagrilintide"], ["obesity"]),
    ("BIMAGRUMAB_OBESITY_AUTO", "Bimagrumab in obesity/myopathy",
     ["bimagrumab"], ["obesity", "muscle"]),
    ("SURVODUTIDE_OBESITY_AUTO", "Survodutide GLP-1/glucagon obesity",
     ["survodutide"], ["obesity"]),
    ("MAZDUTIDE_OBESITY_AUTO", "Mazdutide GLP-1/glucagon (Innovent) obesity",
     ["mazdutide"], ["obesity"]),
    ("TIRZEPATIDE_HF_AUTO", "Tirzepatide in HF with obesity (SUMMIT)",
     ["tirzepatide"], ["heart failure"]),
    ("TIRZEPATIDE_CKD_AUTO", "Tirzepatide in CKD",
     ["tirzepatide"], ["chronic kidney"]),
    # MASH / NASH newer
    ("PEMVIDUTIDE_NASH_AUTO", "Pemvidutide in MASH",
     ["pemvidutide"], ["steatohepatitis"]),
    ("LANIFIBRANOR_NASH_AUTO", "Lanifibranor pan-PPAR MASH",
     ["lanifibranor"], ["steatohepatitis"]),
    ("ARAMCHOL_NASH_AUTO", "Aramchol in NASH",
     ["aramchol"], ["steatohepatitis"]),
    ("CILOFEXOR_NASH_AUTO", "Cilofexor FXR-agonist MASH",
     ["cilofexor"], ["steatohepatitis"]),
    # Newer oncology
    ("LIBTAYO_NSCLC_AUTO", "Cemiplimab in 1L NSCLC",
     ["cemiplimab"], ["non-small cell lung"]),
    ("TIVDAK_CERVICAL_AUTO", "Tisotumab vedotin in cervical cancer",
     ["tisotumab"], ["cervic"]),
    ("BELZUTIFAN_RCC_AUTO", "Belzutifan in VHL-associated RCC",
     ["belzutifan"], ["renal cell", "von hippel"]),
    ("PRALSETINIB_RET_AUTO", "Pralsetinib in RET+ NSCLC/MTC",
     ["pralsetinib"], ["non-small cell lung", "thyroid"]),
    ("MOBOCERTINIB_EGFR_AUTO", "Mobocertinib EGFR ex20ins NSCLC",
     ["mobocertinib"], ["non-small cell lung"]),
    ("AMIVANTAMAB_NSCLC_AUTO", "Amivantamab in EGFR ex20ins NSCLC",
     ["amivantamab"], ["non-small cell lung"]),
    ("INFIGRATINIB_BTC_AUTO", "Infigratinib FGFR2-fusion CCA",
     ["infigratinib"], ["cholangiocarcinoma"]),
    ("FUTIBATINIB_BTC_AUTO", "Futibatinib in CCA",
     ["futibatinib"], ["cholangiocarcinoma"]),
    ("PEMIGATINIB_BTC_AUTO", "Pemigatinib in CCA",
     ["pemigatinib"], ["cholangiocarcinoma"]),
    ("IVOSIDENIB_BTC_AUTO", "Ivosidenib in IDH1+ CCA (ClarIDHy)",
     ["ivosidenib"], ["cholangiocarcinoma"]),
    ("ENFORTUMAB_BLADDER_AUTO", "Enfortumab vedotin in UC",
     ["enfortumab"], ["urothelial"]),
    ("SACITUZUMAB_TNBC_AUTO", "Sacituzumab govitecan in TNBC",
     ["sacituzumab"], ["triple-negative", "triple negative", "breast"]),
    ("SACITUZUMAB_HR_AUTO", "Sacituzumab govitecan in HR+ breast",
     ["sacituzumab"], ["breast"]),
    ("PEMBROLIZUMAB_ENDOMETRIAL_AUTO", "Pembrolizumab in endometrial",
     ["pembrolizumab"], ["endometrial"]),
    ("DOSTARLIMAB_ENDOMETRIAL_AUTO", "Dostarlimab in endometrial",
     ["dostarlimab"], ["endometrial"]),
    ("DOSTARLIMAB_CRC_AUTO", "Dostarlimab in dMMR rectal",
     ["dostarlimab"], ["colorect", "rectal"]),
    ("PEMBROLIZUMAB_DMMR_CRC_AUTO", "Pembrolizumab in dMMR CRC (KEYNOTE-177)",
     ["pembrolizumab"], ["colorect"]),
    ("PEMBROLIZUMAB_CERVICAL_AUTO", "Pembrolizumab in cervical",
     ["pembrolizumab"], ["cervic"]),
    ("PEMBROLIZUMAB_OVARIAN_AUTO", "Pembrolizumab in ovarian",
     ["pembrolizumab"], ["ovarian"]),
    ("PEMBROLIZUMAB_BREAST_NEOADJ_AUTO", "Pembrolizumab neoadjuvant TNBC",
     ["pembrolizumab"], ["triple-negative", "triple negative", "breast"]),
    ("PEMBROLIZUMAB_RCC_AUTO", "Pembrolizumab + axitinib RCC",
     ["pembrolizumab"], ["renal cell"]),
    ("NIVOLUMAB_MELANOMA_ADJUVANT_AUTO", "Nivolumab adjuvant melanoma",
     ["nivolumab"], ["melanoma"]),
    ("PEMBROLIZUMAB_GASTRIC_AUTO", "Pembrolizumab in gastric",
     ["pembrolizumab"], ["gastric"]),
    ("BCG_BLADDER_AUTO", "BCG in NMIBC",
     ["bcg", "bacillus calmette"], ["bladder"]),
    # Newer hematology
    ("VENETOCLAX_MM_AUTO", "Venetoclax in t(11;14) MM",
     ["venetoclax"], ["multiple myeloma"]),
    ("BENDAMUSTINE_RITUXIMAB_AUTO", "Bendamustine + rituximab in CLL",
     ["bendamustine"], ["chronic lymphocytic"]),
    ("ARSENIC_TRIOXIDE_APL_AUTO", "Arsenic trioxide + ATRA in APL",
     ["arsenic trioxide"], ["promyelocytic leukemia"]),
    ("CPX_351_AML_AUTO", "CPX-351 (Vyxeos) in AML",
     ["cpx-351", "cpx 351", "daunorubicin and cytarabine"], ["acute myeloid leukemia"]),
    ("GLASDEGIB_AML_AUTO", "Glasdegib + LDAC in AML",
     ["glasdegib"], ["acute myeloid leukemia"]),
    ("AZACITIDINE_VEN_AML_AUTO", "Azacitidine + venetoclax AML",
     ["azacitidine"], ["acute myeloid leukemia"]),
    # Neuro / psych newer
    ("APOMORPHINE_PD_AUTO", "Apomorphine SC infusion Parkinson",
     ["apomorphine"], ["parkinson"]),
    ("SAFINAMIDE_FLUCT_AUTO", "Safinamide on-off PD",
     ["safinamide"], ["parkinson"]),
    ("LECANEMAB_AD_AUTO", "Lecanemab in early AD (CLARITY-AD)",
     ["lecanemab"], ["alzheimer"]),
    ("DONANEMAB_AD_AUTO", "Donanemab in early AD (TRAILBLAZER)",
     ["donanemab"], ["alzheimer"]),
    ("ADUCANUMAB_AD_AUTO", "Aducanumab in early AD",
     ["aducanumab"], ["alzheimer"]),
    ("GANTENERUMAB_AD_AUTO", "Gantenerumab in AD",
     ["gantenerumab"], ["alzheimer"]),
    ("BEPRANEMAB_AD_AUTO", "Bepranemab anti-tau in AD",
     ["bepranemab"], ["alzheimer"]),
    # Pediatric / pediatric oncology
    ("CARFILZOMIB_REL_AUTO", "Carfilzomib in R/R lymphoma",
     ["carfilzomib"], ["lymphoma"]),
    ("DINUTUXIMAB_NEUROBLASTOMA_AUTO", "Dinutuximab in neuroblastoma",
     ["dinutuximab"], ["neuroblastoma"]),
    # GU / male health
    ("DUTASTERIDE_BPH_AUTO", "Dutasteride in BPH",
     ["dutasteride"], ["prostatic hyperplasia"]),
    ("TADALAFIL_BPH_AUTO", "Tadalafil daily for BPH/ED",
     ["tadalafil"], ["prostatic hyperplasia", "erectile dysfunction"]),
    ("VARDENAFIL_ED_AUTO", "Vardenafil in ED",
     ["vardenafil"], ["erectile dysfunction"]),
    ("AVANAFIL_ED_AUTO", "Avanafil in ED",
     ["avanafil"], ["erectile dysfunction"]),
    # Renal / GU oncology
    ("TIVOZANIB_RCC_AUTO", "Tivozanib in advanced RCC",
     ["tivozanib"], ["renal cell"]),
    ("CABOZANTINIB_PROSTATE_AUTO", "Cabozantinib in mCRPC",
     ["cabozantinib"], ["prostat"]),
    ("PEMBROLIZUMAB_NMIBC_AUTO", "Pembrolizumab in NMIBC BCG-unresp",
     ["pembrolizumab"], ["bladder"]),
    # Inflammation / immune
    ("ADALIMUMAB_UC_AUTO", "Adalimumab in UC",
     ["adalimumab"], ["ulcerative colitis"]),
    ("INFLIXIMAB_CD_AUTO", "Infliximab in CD",
     ["infliximab"], ["crohn"]),
    ("GOLIMUMAB_UC_AUTO", "Golimumab in UC",
     ["golimumab"], ["ulcerative colitis"]),
    ("CERTOLIZUMAB_RA_AUTO", "Certolizumab pegol in RA",
     ["certolizumab"], ["rheumatoid arthritis"]),
    ("ABATACEPT_RA_AUTO", "Abatacept in RA",
     ["abatacept"], ["rheumatoid arthritis"]),
    ("TOCILIZUMAB_RA_AUTO", "Tocilizumab in RA",
     ["tocilizumab"], ["rheumatoid arthritis"]),
    ("SARILUMAB_RA_AUTO", "Sarilumab in RA",
     ["sarilumab"], ["rheumatoid arthritis"]),
    ("ANIFROLUMAB_LUPUS_2_AUTO", "Anifrolumab IFN-AR in SLE",
     ["anifrolumab"], ["lupus"]),
    ("BARICITINIB_SLE_AUTO", "Baricitinib in SLE",
     ["baricitinib"], ["lupus"]),
    # Newer IO / vaccine
    ("RSVPREF3_VACCINE_AUTO", "RSVPreF3 Older Adult vaccine",
     ["rsvpref3", "respiratory syncytial virus vaccine"], ["respiratory syncytial"]),
    ("PREVNAR20_PNEUMO_AUTO", "Pneumococcal 20-valent",
     ["pneumococcal 20-valent", "prevnar 20", "pcv20"], ["pneumococc"]),
    ("PREVNAR15_PNEUMO_AUTO", "Pneumococcal 15-valent",
     ["pneumococcal 15-valent", "vaxneuvance", "v114"], ["pneumococc"]),
    # GI / liver
    ("INFLIXIMAB_UC_AUTO", "Infliximab in UC",
     ["infliximab"], ["ulcerative colitis"]),
    ("LINACLOTIDE_CIC_AUTO", "Linaclotide in chronic constipation",
     ["linaclotide"], ["constipation"]),
    ("PRUCALOPRIDE_CIC_AUTO", "Prucalopride in CIC",
     ["prucalopride"], ["constipation"]),
    ("LUBIPROSTONE_CIC_AUTO", "Lubiprostone in CIC/IBS-C",
     ["lubiprostone"], ["constipation"]),
    # Pulm / respiratory new
    ("MACITENTAN_PAH_AUTO", "Macitentan in PAH",
     ["macitentan"], ["pulmonary arterial hypertension"]),
    ("RIOCIGUAT_PAH_AUTO", "Riociguat in PAH/CTEPH",
     ["riociguat"], ["pulmonary arterial hypertension", "thromboembolic"]),
    ("SELEXIPAG_PAH_AUTO", "Selexipag in PAH",
     ["selexipag"], ["pulmonary arterial hypertension"]),
    ("AMBRISENTAN_PAH_AUTO", "Ambrisentan in PAH",
     ["ambrisentan"], ["pulmonary arterial hypertension"]),
    ("BOSENTAN_PAH_AUTO", "Bosentan in PAH",
     ["bosentan"], ["pulmonary arterial hypertension"]),
    ("TADALAFIL_PAH_AUTO", "Tadalafil in PAH",
     ["tadalafil"], ["pulmonary arterial hypertension"]),
    ("SILDENAFIL_PAH_AUTO", "Sildenafil in PAH",
     ["sildenafil"], ["pulmonary arterial hypertension"]),
    ("SOTATERCEPT_PAH_AUTO", "Sotatercept in PAH (STELLAR)",
     ["sotatercept"], ["pulmonary arterial hypertension"]),
    # Hepatology newer
    ("CILOFEXOR_FXR_PSC_AUTO", "Cilofexor in primary sclerosing cholangitis",
     ["cilofexor"], ["sclerosing cholangitis"]),
    ("OBETICHOLIC_PSC_AUTO", "Obeticholic acid PSC",
     ["obeticholic"], ["sclerosing cholangitis"]),
    ("BUDESONIDE_AIH_AUTO", "Budesonide in autoimmune hepatitis",
     ["budesonide"], ["autoimmune hepatitis"]),
    # Newer ID / antibacterial
    ("PLAZOMICIN_AMINO_AUTO", "Plazomicin in CRE",
     ["plazomicin"], ["gram-negative"]),
    ("IMIPENEM_RELEBACTAM_AUTO", "Imipenem-cilastatin-relebactam",
     ["imipenem-relebactam", "imipenem/cilastatin/relebactam"], ["gram-negative", "pneumonia"]),
    # Dermatology newer
    ("OZANIMOD_UC_AUTO", "Ozanimod in UC",
     ["ozanimod"], ["ulcerative colitis"]),
    ("ETROLIZUMAB_CD_AUTO", "Etrolizumab in Crohn",
     ["etrolizumab"], ["crohn"]),
    # Surgery / device
    ("ARGATROBAN_HIT_AUTO", "Argatroban in HIT",
     ["argatroban"], ["heparin-induced"]),
    ("DEFEROXAMINE_IRON_AUTO", "Deferoxamine in iron overload",
     ["deferoxamine"], ["iron overload"]),
    ("DEFERASIROX_IRON_AUTO", "Deferasirox in iron overload",
     ["deferasirox"], ["iron overload"]),
    ("DEFERIPRONE_IRON_AUTO", "Deferiprone in iron overload",
     ["deferiprone"], ["iron overload"]),
    # Newer neuro
    ("TOFACITINIB_UC_AUTO", "Tofacitinib in UC",
     ["tofacitinib"], ["ulcerative colitis"]),
    ("RUXIENCE_RA_AUTO", "Rituximab biosimilar in RA",
     ["rituximab"], ["rheumatoid arthritis"]),

    # Newer asthma / pulm biologic
    ("RELDESEMTIV_SMA_AUTO", "Reldesemtiv in SMA",
     ["reldesemtiv"], ["spinal muscular atrophy"]),

    # Various more
    ("LEMBOREXANT_INSOMNIA_AUTO", "Lemborexant insomnia",
     ["lemborexant"], ["insomnia"]),
    ("SUVOREXANT_INSOMNIA_AUTO", "Suvorexant insomnia",
     ["suvorexant"], ["insomnia"]),
    ("DARIDOREXANT_INSOMNIA_AUTO", "Daridorexant insomnia",
     ["daridorexant"], ["insomnia"]),
    ("RAMELTEON_INSOMNIA_AUTO", "Ramelteon insomnia",
     ["ramelteon"], ["insomnia"]),
    ("TASIMELTEON_AUTO", "Tasimelteon non-24 / smith-magenis",
     ["tasimelteon"], ["non-24", "smith-magenis", "circadian"]),

    # Various depression / anxiety
    ("SERTRALINE_AUTO", "Sertraline in depression",
     ["sertraline"], ["depress"]),
    ("ESCITALOPRAM_DEPRESSION_AUTO", "Escitalopram in depression/anxiety",
     ["escitalopram"], ["depress", "anxiety"]),
    ("VORTIOXETINE_DEPRESSION_AUTO", "Vortioxetine in MDD",
     ["vortioxetine"], ["depress"]),
    ("VILAZODONE_DEPRESSION_AUTO", "Vilazodone in MDD",
     ["vilazodone"], ["depress"]),
    ("LURASIDONE_BIPOLAR_AUTO", "Lurasidone in bipolar depression",
     ["lurasidone"], ["bipolar"]),
    ("QUETIAPINE_BIPOLAR_AUTO", "Quetiapine in bipolar",
     ["quetiapine"], ["bipolar"]),
    ("LITHIUM_BIPOLAR_AUTO", "Lithium in bipolar",
     ["lithium"], ["bipolar"]),
    ("ARIPIPRAZOLE_SCHIZO_AUTO", "Aripiprazole LAI schizophrenia",
     ["aripiprazole"], ["schizophrenia"]),
    ("BREXPIPRAZOLE_SCHIZO_AUTO", "Brexpiprazole schizophrenia",
     ["brexpiprazole"], ["schizophrenia"]),
    ("OLANZAPINE_SCHIZO_AUTO", "Olanzapine LAI in schizophrenia",
     ["olanzapine"], ["schizophrenia"]),
    ("CLOZAPINE_SCHIZO_AUTO", "Clozapine in TRS",
     ["clozapine"], ["schizophrenia"]),
    ("RISPERIDONE_SCHIZO_AUTO", "Risperidone LAI in schizophrenia",
     ["risperidone"], ["schizophrenia"]),
    ("PALIPERIDONE_SCHIZO_AUTO", "Paliperidone palmitate LAI",
     ["paliperidone"], ["schizophrenia"]),

    # Surgical / non-pharm
    ("CARDIAC_REHAB_AUTO", "Cardiac rehab post-MI",
     ["cardiac rehab", "exercise"], ["myocardial infarction", "coronary"]),
    ("PULMONARY_REHAB_AUTO", "Pulmonary rehab in COPD",
     ["pulmonary rehab"], ["pulmonary disease"]),
    # Various more cardio
    ("EPLERENONE_HF_AUTO", "Eplerenone in HF post-MI",
     ["eplerenone"], ["heart failure", "myocardial infarction"]),
    ("SPIRONOLACTONE_HFpEF_AUTO", "Spironolactone in HFpEF (TOPCAT)",
     ["spironolactone"], ["heart failure"]),
    ("FERIC_CARBOXYMALTOSE_HF_AUTO", "Ferric carboxymaltose in HF iron def",
     ["ferric carboxymaltose"], ["heart failure", "iron deficiency"]),
    ("ICATIBANT_HAE_AUTO", "Icatibant in HAE attacks",
     ["icatibant"], ["hereditary angioedema"]),
    ("DONIDALORSEN_HAE_AUTO", "Donidalorsen in HAE prophylaxis",
     ["donidalorsen"], ["hereditary angioedema"]),
    ("BEROTRALSTAT_HAE_AUTO", "Berotralstat in HAE prophylaxis",
     ["berotralstat"], ["hereditary angioedema"]),
    ("LANADELUMAB_HAE_AUTO", "Lanadelumab in HAE prophylaxis",
     ["lanadelumab"], ["hereditary angioedema"]),
    # Newer ENT / allergy
    ("OMALIZUMAB_FOOD_ALLERGY_AUTO", "Omalizumab in food allergy",
     ["omalizumab"], ["food allergy", "peanut allergy"]),
    ("PALFORZIA_PEANUT_AUTO", "Palforzia peanut OIT",
     ["palforzia", "ar101"], ["peanut allergy"]),
    # Various more rare diseases
    ("ELRANATAMAB_MM_2_AUTO", "Elranatamab in R/R MM",
     ["elranatamab"], ["multiple myeloma"]),
    ("EFLAPEGRASTIM_NEUTROPENIA_AUTO", "Eflapegrastim CIN",
     ["eflapegrastim"], ["neutropenia"]),
    ("AVATROMBOPAG_CTCP_AUTO", "Avatrombopag in CIT post-chemo",
     ["avatrombopag"], ["thrombocytopen"]),
    ("PLEDIBIRX_THROMB_AUTO", "Romiplostim post-chemo CIT",
     ["romiplostim"], ["thrombocytopen"]),

    # Misc rare disease
    ("EFANESOCTOCOG_HEMA_AUTO", "Efanesoctocog (Altuviiio) hemophilia A",
     ["efanesoctocog"], ["hemophilia"]),
    ("DAMOCTOCOG_HEMA_AUTO", "Damoctocog alfa pegol hemophilia A",
     ["damoctocog"], ["hemophilia"]),
    ("NONACOG_BETA_HEMB_AUTO", "Nonacog beta pegol hemophilia B",
     ["nonacog"], ["hemophilia"]),

    # Batch 8 — final 77+ push to 500
    # More cardio
    ("DAPAGLIFLOZIN_HF_AUTO", "Dapagliflozin in HFrEF/HFpEF",
     ["dapagliflozin"], ["heart failure"]),
    ("EMPAGLIFLOZIN_HF_AUTO", "Empagliflozin in HFrEF/HFpEF",
     ["empagliflozin"], ["heart failure"]),
    ("SACUBITRIL_VALSARTAN_HF_AUTO", "Sacubitril/valsartan in HF",
     ["sacubitril"], ["heart failure"]),
    ("AMIODARONE_AF_AUTO", "Amiodarone in AF",
     ["amiodarone"], ["atrial fibrillation"]),
    ("DRONEDARONE_AF_AUTO", "Dronedarone in AF",
     ["dronedarone"], ["atrial fibrillation"]),
    ("FLECAINIDE_AF_AUTO", "Flecainide in AF",
     ["flecainide"], ["atrial fibrillation"]),
    ("PROPAFENONE_AF_AUTO", "Propafenone in AF",
     ["propafenone"], ["atrial fibrillation"]),
    ("DAPAGLIFLOZIN_HFPEF_AUTO", "Dapagliflozin HFpEF DELIVER",
     ["dapagliflozin"], ["preserved ejection"]),
    ("EMPAGLIFLOZIN_HFPEF_AUTO", "Empagliflozin HFpEF EMPEROR-Preserved",
     ["empagliflozin"], ["preserved ejection"]),
    ("METOPROLOL_HF_AUTO", "Metoprolol in HF",
     ["metoprolol"], ["heart failure"]),
    ("CARVEDILOL_HF_AUTO", "Carvedilol in HF",
     ["carvedilol"], ["heart failure"]),
    ("BISOPROLOL_HF_AUTO", "Bisoprolol in HF",
     ["bisoprolol"], ["heart failure"]),
    ("DIGOXIN_HF_AUTO", "Digoxin in HF",
     ["digoxin"], ["heart failure"]),
    ("IVABRADINE_HF_AUTO", "Ivabradine in HFrEF",
     ["ivabradine"], ["heart failure"]),
    # GI/IBD biologics
    ("VEDOLIZUMAB_CD_AUTO", "Vedolizumab in CD",
     ["vedolizumab"], ["crohn"]),
    ("VEDOLIZUMAB_UC_AUTO", "Vedolizumab in UC",
     ["vedolizumab"], ["ulcerative colitis"]),
    ("USTEKINUMAB_UC_AUTO", "Ustekinumab in UC",
     ["ustekinumab"], ["ulcerative colitis"]),
    ("USTEKINUMAB_PSO_AUTO", "Ustekinumab in psoriasis",
     ["ustekinumab"], ["psoriasis"]),
    ("ADALIMUMAB_RA_AUTO", "Adalimumab in RA",
     ["adalimumab"], ["rheumatoid arthritis"]),
    ("ADALIMUMAB_PSO_AUTO", "Adalimumab in psoriasis",
     ["adalimumab"], ["psoriasis"]),
    ("ADALIMUMAB_AS_AUTO", "Adalimumab in AS",
     ["adalimumab"], ["ankylosing", "spondyl"]),
    ("ADALIMUMAB_PSA_AUTO", "Adalimumab in PsA",
     ["adalimumab"], ["psoriatic"]),
    ("ADALIMUMAB_UVEITIS_AUTO", "Adalimumab in non-infectious uveitis",
     ["adalimumab"], ["uveitis"]),
    ("INFLIXIMAB_RA_AUTO", "Infliximab in RA",
     ["infliximab"], ["rheumatoid arthritis"]),
    ("ETANERCEPT_RA_AUTO", "Etanercept in RA",
     ["etanercept"], ["rheumatoid arthritis"]),
    ("ETANERCEPT_AS_AUTO", "Etanercept in AS",
     ["etanercept"], ["ankylosing"]),
    ("ETANERCEPT_PSO_AUTO", "Etanercept in psoriasis",
     ["etanercept"], ["psoriasis"]),
    # Pulmonary newer
    ("INDACATEROL_GLYCOPYR_COPD_AUTO", "IND/GLY in COPD",
     ["indacaterol"], ["pulmonary disease"]),
    ("TIOTROPIUM_COPD_AUTO", "Tiotropium in COPD",
     ["tiotropium"], ["pulmonary disease"]),
    ("ACLIDINIUM_COPD_AUTO", "Aclidinium in COPD",
     ["aclidinium"], ["pulmonary disease"]),
    ("FORMOTEROL_COPD_AUTO", "Formoterol in COPD",
     ["formoterol"], ["pulmonary disease"]),
    # Newer GI
    ("PRUCALOPRIDE_AUTO", "Prucalopride for chronic constipation",
     ["prucalopride"], ["constipation"]),
    ("OCTREOTIDE_DUMP_AUTO", "Octreotide LAR in carcinoid",
     ["octreotide"], ["carcinoid"]),
    ("CABOZANTINIB_NETS_AUTO", "Cabozantinib in NETs (CABINET)",
     ["cabozantinib"], ["neuroendocrine"]),
    # Newer oncology subgroups
    ("LENVATINIB_RCC_AUTO", "Lenvatinib + everolimus RCC",
     ["lenvatinib"], ["renal cell"]),
    ("LENVATINIB_ENDO_AUTO", "Lenvatinib + pembrolizumab endometrial",
     ["lenvatinib"], ["endometrial"]),
    ("PEMBROLIZUMAB_HCC_AUTO", "Pembrolizumab in HCC",
     ["pembrolizumab"], ["hepatocellular"]),
    ("RAMUCIRUMAB_HCC_AUTO", "Ramucirumab in HCC (REACH-2)",
     ["ramucirumab"], ["hepatocellular"]),
    ("PEMBROLIZUMAB_CSCC_AUTO", "Pembrolizumab in cutaneous SCC",
     ["pembrolizumab"], ["squamous cell"]),
    ("NIVOLUMAB_HNSCC_AUTO", "Nivolumab in HNSCC",
     ["nivolumab"], ["head and neck"]),
    ("PEMBROLIZUMAB_BCS_AUTO", "Pembrolizumab + chemo TNBC neoadjuvant",
     ["pembrolizumab"], ["breast"]),
    ("ENTRECTINIB_NTRK_AUTO", "Entrectinib NTRK+ solid",
     ["entrectinib"], ["neoplasm"]),
    ("LAROTRECTINIB_NTRK_2_AUTO", "Larotrectinib in NTRK+",
     ["larotrectinib"], ["neoplasm"]),
    ("DOSTARLIMAB_LUNG_AUTO", "Dostarlimab in NSCLC",
     ["dostarlimab"], ["non-small cell lung"]),
    ("PEMBROLIZUMAB_MELANOMA_NEO_AUTO", "Pembrolizumab neoadjuvant melanoma",
     ["pembrolizumab"], ["melanoma"]),
    # Newer rare/orphan
    ("MIDOSTAURIN_MASTOCYTOSIS_AUTO", "Midostaurin in advanced mastocytosis",
     ["midostaurin"], ["mastocytosis", "mast cell"]),
    ("AVAPRITINIB_MASTOCYTOSIS_AUTO", "Avapritinib in advanced systemic mastocytosis",
     ["avapritinib"], ["mastocytosis"]),
    ("BURSEMOL_HEM_AUTO", "Marstacimab anti-TFPI hemophilia",
     ["marstacimab"], ["hemophilia"]),
    # Newer cardio
    ("INCLISIRAN_HOFH_AUTO", "Inclisiran in HoFH",
     ["inclisiran"], ["homozygous", "familial hypercholesterolemia"]),
    ("VOLANESORSEN_LIPID_AUTO", "Volanesorsen severe hypertriglyc",
     ["volanesorsen"], ["hypertriglyceridemia"]),
    # Newer ID
    ("FIDAXOMICIN_CDIFF_AUTO", "Fidaxomicin in C. difficile",
     ["fidaxomicin"], ["clostridium difficile", "clostridioides difficile"]),
    ("BEZLOTOXUMAB_CDIFF_AUTO", "Bezlotoxumab to prevent CDI recurrence",
     ["bezlotoxumab"], ["clostridium", "clostridioides"]),
    ("FMT_CDIFF_AUTO", "FMT for recurrent C. difficile",
     ["fecal microbiota", "rebyota", "vowst"], ["clostridium", "clostridioides"]),
    ("RIFAXIMIN_HE_AUTO", "Rifaximin in hepatic encephalopathy",
     ["rifaximin"], ["hepatic encephalopathy"]),
    ("LACTULOSE_HE_AUTO", "Lactulose in HE",
     ["lactulose"], ["hepatic encephalopathy"]),
    # Pediatric / vaccines
    ("MENINGOCOCCAL_B_VACCINE_AUTO", "Meningococcal B vaccine (Bexsero, Trumenba)",
     ["meningococcal b", "men-b", "bexsero", "trumenba"], ["meningococc"]),
    ("EBOLA_VACCINE_AUTO", "Ebola vaccine (Ervebo, rVSV)",
     ["ervebo", "rvsv-zebov", "rvsv zebov"], ["ebola"]),
    ("ZOSTER_RECOMBINANT_AUTO", "Recombinant zoster vaccine (Shingrix)",
     ["shingrix", "recombinant zoster"], ["herpes zoster"]),
    # Surgical / device comparisons
    ("WATCHMAN_LAA_AUTO", "Watchman LAA occlusion in AF",
     ["watchman"], ["atrial fibrillation"]),
    ("AMULET_LAA_AUTO", "Amplatzer Amulet LAA occlusion",
     ["amulet"], ["atrial fibrillation"]),
    ("TAVR_HIGH_LOW_AUTO", "TAVR vs SAVR in various risk",
     ["transcatheter aortic valve", "tavr", "tavi"], ["aortic stenosis", "aortic valve"]),
    ("MITRACLIP_FMR_AUTO", "MitraClip in functional MR",
     ["mitraclip"], ["mitral regurgitation"]),
    ("PFA_AF_AUTO", "Pulsed field ablation in AF",
     ["pulsed field ablation"], ["atrial fibrillation"]),
    # Newer renal
    ("APABETALONE_CKD_AUTO", "Apabetalone in CV/T2D BETonMACE",
     ["apabetalone"], ["coronary syndrome", "type 2 diabetes"]),
    ("MITAPIVAT_SCD_AUTO", "Mitapivat in sickle cell",
     ["mitapivat"], ["sickle"]),
    # Newer derm
    ("APREMILAST_PSORIASIS_AUTO", "Apremilast in psoriasis",
     ["apremilast"], ["psoriasis"]),
    ("APREMILAST_PSA_AUTO", "Apremilast in PsA",
     ["apremilast"], ["psoriatic"]),
    ("APREMILAST_BEHCET_AUTO", "Apremilast in Behçet oral ulcers",
     ["apremilast"], ["behcet", "behçet"]),
    # Newer endocrine
    ("DESMOPRESSIN_NOCTURIA_AUTO", "Desmopressin nocturia",
     ["desmopressin"], ["nocturia"]),

    # Newer kidney transplant
    ("BELATACEPT_KT_AUTO", "Belatacept post kidney transplant",
     ["belatacept"], ["kidney transplant"]),

    # Various antiviral combinations
    ("DOLUTEGRAVIR_LAMIVUDINE_HIV_AUTO", "Dolutegravir/lamivudine 2DR HIV",
     ["dolutegravir"], ["hiv"]),
    ("BIKTARVY_HIV_AUTO", "Bictegravir/F/TAF in HIV",
     ["bictegravir"], ["hiv"]),
    ("DARUNAVIR_HIV_AUTO", "Darunavir-based HIV regimens",
     ["darunavir"], ["hiv"]),
    ("RILPIVIRINE_HIV_AUTO", "Rilpivirine in HIV",
     ["rilpivirine"], ["hiv"]),
    ("DORAVIRINE_HIV_AUTO", "Doravirine in HIV",
     ["doravirine"], ["hiv"]),

    # Newer bone health
    ("ZOLEDRONIC_OSTEO_AUTO", "Zoledronic acid in osteoporosis",
     ["zoledronic"], ["osteoporosis", "fracture"]),

    # Cardio post-MI
    ("SPIRONOLACTONE_HFREF_AUTO", "Spironolactone in HFrEF",
     ["spironolactone"], ["heart failure"]),
    ("EPLERENONE_AMI_AUTO", "Eplerenone post-AMI EPHESUS/REMINDER",
     ["eplerenone"], ["myocardial infarction"]),
    # Vacs
    ("MENVEO_MEN_AUTO", "Quadrivalent meningococcal vaccines",
     ["meningococcal", "menveo", "menquadfi"], ["meningococc"]),

    # Newer hepatology
    ("ELAFIBRANOR_PBC_AUTO", "Elafibranor in PBC",
     ["elafibranor"], ["biliary cholangitis", "biliary cirrhosis"]),
    ("SELADELPAR_PBC_AUTO", "Seladelpar in PBC",
     ["seladelpar"], ["biliary cholangitis"]),
    ("OBETICHOLIC_PBC_AUTO", "Obeticholic in PBC",
     ["obeticholic"], ["biliary cholangitis"]),

    # Cardio non-pharma
    ("ABLATION_HFREF_AUTO", "Ablation for AF in HFrEF",
     ["catheter ablation"], ["heart failure", "atrial fibrillation"]),

    # Newer pediatric
    ("MOMELOTINIB_AUTO", "Momelotinib in anemic MF",
     ["momelotinib"], ["myelofibrosis"]),

    # Newer oncology supportive
    ("DOSTARLIMAB_OVARIAN_AUTO", "Dostarlimab in ovarian",
     ["dostarlimab"], ["ovarian"]),
    ("NIRAPARIB_BREAST_AUTO", "Niraparib in breast",
     ["niraparib"], ["breast"]),
    ("ATEZOLIZUMAB_TNBC_AUTO", "Atezolizumab in TNBC",
     ["atezolizumab"], ["triple-negative", "triple negative", "breast"]),
    ("NIVOLUMAB_ESCC_AUTO", "Nivolumab in esophageal SCC",
     ["nivolumab"], ["esophageal"]),
    ("PEMBROLIZUMAB_BIL_AUTO", "Pembrolizumab in biliary tract",
     ["pembrolizumab"], ["biliary", "cholangiocarcinoma"]),

    # Newer cardio combos
    ("AMLODIPINE_VALSARTAN_HTN_AUTO", "Amlodipine/valsartan HTN",
     ["amlodipine"], ["hypertension"]),
    ("LOSARTAN_HTN_AUTO", "Losartan in HTN/nephropathy",
     ["losartan"], ["hypertension", "diabetic nephropathy"]),
    ("PERINDOPRIL_HTN_AUTO", "Perindopril/indapamide in HTN",
     ["perindopril"], ["hypertension"]),
    ("AZILSARTAN_HTN_AUTO", "Azilsartan in HTN",
     ["azilsartan"], ["hypertension"]),
    # Newer pulmonary
    ("BREZTRI_TRIPLE_AUTO", "Budesonide/glycopyrrolate/formoterol",
     ["budesonide"], ["pulmonary disease"]),
    # Renal newer
    ("LANTHANUM_HYPERPHOS_AUTO", "Lanthanum in hyperphosphatemia",
     ["lanthanum"], ["hyperphosphatemia"]),
    ("SUCROFERRIC_OXY_AUTO", "Sucroferric oxyhydroxide in hyperphos",
     ["sucroferric"], ["hyperphosphatemia"]),
    # Newer ophth
    ("DEXAMETHASONE_INTRAVITREAL_AUTO", "Dexamethasone implant for DME/uveitis",
     ["dexamethasone"], ["macular edema", "uveitis"]),
    ("RANIBIZUMAB_RVO_AUTO", "Ranibizumab in RVO",
     ["ranibizumab"], ["retinal vein"]),
    ("BEVACIZUMAB_AMD_AUTO", "Bevacizumab in AMD",
     ["bevacizumab"], ["macular degeneration"]),

    # Newer surgical/non-pharm
    ("RENAL_DENERVATION_HTN_AUTO", "Renal denervation in resistant HTN",
     ["renal denervation"], ["hypertension"]),
    # Newer rheum
    ("ABATACEPT_PSA_AUTO", "Abatacept in PsA",
     ["abatacept"], ["psoriatic"]),
    # Cardio device
    ("ICD_PRIMARY_AUTO", "ICD for primary prevention",
     ["implantable cardioverter", "icd"], ["heart failure", "ventricular"]),
    ("CRT_HEART_AUTO", "Cardiac resynchronisation therapy",
     ["cardiac resynchronization", "crt"], ["heart failure"]),
    # PAH newer
    ("TREPROSTINIL_PAH_AUTO", "Treprostinil in PAH",
     ["treprostinil"], ["pulmonary arterial hypertension"]),
    ("EPOPROSTENOL_PAH_AUTO", "Epoprostenol in PAH",
     ["epoprostenol"], ["pulmonary arterial hypertension"]),
    ("ILOPROST_PAH_AUTO", "Iloprost in PAH",
     ["iloprost"], ["pulmonary arterial hypertension"]),
    # Newer immune
    ("BURATIO_AUTO", "Aldesleukin IL-2 in melanoma",
     ["aldesleukin"], ["melanoma"]),

    # Batch 9 — Final 51+ push: maximize NCT-coverage drugs
    # Antibiotics & ID — varied populations
    ("AZITHROMYCIN_RESPI_AUTO", "Azithromycin in respiratory infections",
     ["azithromycin"], ["pneumonia", "exacerbation"]),
    ("CIPROFLOXACIN_UTI_AUTO", "Ciprofloxacin in UTI",
     ["ciprofloxacin"], ["urinary tract infection"]),
    ("LEVOFLOXACIN_RESPI_AUTO", "Levofloxacin in respiratory infections",
     ["levofloxacin"], ["pneumonia"]),
    ("MOXIFLOXACIN_RESPI_AUTO", "Moxifloxacin in CABP",
     ["moxifloxacin"], ["pneumonia"]),
    ("PIPERACILLIN_TAZ_AUTO", "Piperacillin-tazobactam vs alternatives",
     ["piperacillin-tazobactam", "piperacillin/tazobactam"], ["pneumonia", "intra-abdominal", "bacteremia"]),
    ("CEFTAROLINE_AUTO", "Ceftaroline in pneumonia/skin",
     ["ceftaroline"], ["pneumonia", "skin"]),
    ("CEFTOLOZANE_TAZ_AUTO", "Ceftolozane-tazobactam pneumonia",
     ["ceftolozane-tazobactam", "ceftolozane/tazobactam"], ["pneumonia", "urinary"]),
    ("DAPTOMYCIN_AUTO", "Daptomycin in MRSA bacteremia",
     ["daptomycin"], ["bacteremia", "endocarditis"]),
    ("VANCOMYCIN_MRSA_AUTO", "Vancomycin in MRSA",
     ["vancomycin"], ["staphylococcus aureus"]),
    ("LINEZOLID_MRSA_AUTO", "Linezolid in MRSA",
     ["linezolid"], ["staphylococcus aureus", "pneumonia"]),

    # Newer cardio combinations
    ("ATORVASTATIN_AUTO", "Atorvastatin in dyslipidemia/CV",
     ["atorvastatin"], ["hypercholesterolemia", "coronary"]),
    ("ROSUVASTATIN_AUTO", "Rosuvastatin in CV prevention",
     ["rosuvastatin"], ["coronary", "hypercholesterolemia"]),
    ("SIMVASTATIN_AUTO", "Simvastatin in CV prevention",
     ["simvastatin"], ["coronary", "hypercholesterolemia"]),
    ("PRAVASTATIN_AUTO", "Pravastatin in CV prevention",
     ["pravastatin"], ["coronary", "hypercholesterolemia"]),
    ("PITAVASTATIN_AUTO", "Pitavastatin in CV prevention",
     ["pitavastatin"], ["hypercholesterolemia"]),
    ("EZETIMIBE_AUTO", "Ezetimibe in CV prevention",
     ["ezetimibe"], ["hypercholesterolemia", "coronary"]),
    ("NIACIN_AUTO", "Niacin extended-release in dyslipidemia",
     ["niacin"], ["hypercholesterolemia", "atherosclerot"]),

    # Antibiotics — additional
    ("AMPICILLIN_SULBACTAM_AUTO", "Ampicillin-sulbactam",
     ["ampicillin-sulbactam", "ampicillin/sulbactam"], ["pneumonia", "intra-abdominal"]),
    ("ERTAPENEM_AUTO", "Ertapenem in CABP/intra-abdominal",
     ["ertapenem"], ["pneumonia", "intra-abdominal", "urinary"]),

    # Diabetes various
    ("SITAGLIPTIN_T2D_AUTO", "Sitagliptin in T2D",
     ["sitagliptin"], ["type 2 diabetes"]),
    ("SAXAGLIPTIN_T2D_AUTO", "Saxagliptin in T2D",
     ["saxagliptin"], ["type 2 diabetes"]),
    ("LINAGLIPTIN_T2D_AUTO", "Linagliptin in T2D",
     ["linagliptin"], ["type 2 diabetes"]),
    ("ALOGLIPTIN_T2D_AUTO", "Alogliptin in T2D CVOT",
     ["alogliptin"], ["type 2 diabetes"]),
    ("VILDAGLIPTIN_T2D_AUTO", "Vildagliptin in T2D",
     ["vildagliptin"], ["type 2 diabetes"]),
    ("DEGLUDEC_INSULIN_AUTO", "Insulin degludec in T2D",
     ["insulin degludec"], ["type 2 diabetes"]),
    ("GLARGINE_300_AUTO", "Glargine U300 in T2D",
     ["insulin glargine"], ["type 2 diabetes"]),

    # Renal / fluid
    ("FUROSEMIDE_HF_AUTO", "Furosemide in HF",
     ["furosemide"], ["heart failure"]),
    ("BUMETANIDE_HF_AUTO", "Bumetanide in HF",
     ["bumetanide"], ["heart failure"]),
    ("TORASEMIDE_HF_AUTO", "Torsemide vs furosemide HF",
     ["torsemide", "torasemide"], ["heart failure"]),

    # Antiemetics
    ("APREPITANT_CINV_AUTO", "Aprepitant for CINV",
     ["aprepitant"], ["chemotherapy-induced nausea"]),
    ("FOSAPREPITANT_CINV_AUTO", "Fosaprepitant for CINV",
     ["fosaprepitant"], ["chemotherapy-induced nausea"]),
    ("PALONOSETRON_CINV_AUTO", "Palonosetron for CINV",
     ["palonosetron"], ["chemotherapy-induced nausea"]),
    ("OLANZAPINE_CINV_AUTO", "Olanzapine for CINV",
     ["olanzapine"], ["chemotherapy-induced nausea"]),

    # Anticoagulation various populations
    ("WARFARIN_AF_AUTO", "Warfarin in AF",
     ["warfarin"], ["atrial fibrillation"]),
    ("ENOXAPARIN_VTE_AUTO", "Enoxaparin for VTE prophy/treatment",
     ["enoxaparin"], ["venous thromboembolism"]),
    ("FONDAPARINUX_AUTO", "Fondaparinux in VTE/ACS",
     ["fondaparinux"], ["venous thromboembolism", "coronary syndrome"]),
    ("BIVALIRUDIN_PCI_AUTO", "Bivalirudin in PCI",
     ["bivalirudin"], ["coronary intervention"]),

    # Neuro various
    ("PREGABALIN_PAIN_AUTO", "Pregabalin in neuropathic pain",
     ["pregabalin"], ["neuropathic pain", "fibromyalgia"]),
    ("GABAPENTIN_PAIN_AUTO", "Gabapentin in pain",
     ["gabapentin"], ["neuropathic pain"]),
    ("DULOXETINE_PAIN_AUTO", "Duloxetine in chronic pain",
     ["duloxetine"], ["fibromyalgia", "neuropathic pain"]),
    ("MILNACIPRAN_FIBRO_AUTO", "Milnacipran in fibromyalgia",
     ["milnacipran"], ["fibromyalgia"]),

    # Various dermatology
    ("CALCIPOTRIENE_PSORIASIS_AUTO", "Calcipotriene/betamethasone topical psoriasis",
     ["calcipotriene", "calcipotriol"], ["psoriasis"]),
    ("CRISABOROLE_AD_AUTO", "Crisaborole in atopic dermatitis",
     ["crisaborole"], ["atopic", "dermatitis"]),
    ("HALOBETASOL_PSORIASIS_AUTO", "Halobetasol/tazarotene psoriasis",
     ["halobetasol"], ["psoriasis"]),
    ("BREZ_PSORIASIS_AUTO", "Brodalumab in psoriasis",
     ["brodalumab"], ["psoriasis"]),

    # Vaccine combos
    ("COVID19_BIVALENT_AUTO", "Bivalent COVID-19 mRNA booster",
     ["bivalent", "ba.4/ba.5"], ["covid"]),
    ("INFLUENZA_HIGH_DOSE_AUTO", "High-dose influenza in elderly",
     ["fluzone high-dose", "high-dose influenza"], ["influenza"]),
    ("INFLUENZA_RECOMBINANT_AUTO", "Recombinant influenza vaccine (Flublok)",
     ["flublok", "recombinant influenza"], ["influenza"]),

    # More pediatric / SMA / DMD
    ("EDARAVONE_ALS_2_AUTO", "Edaravone IV in ALS",
     ["edaravone"], ["amyotrophic lateral sclerosis"]),
    ("TOFERSEN_ALS_AUTO", "Tofersen in SOD1 ALS",
     ["tofersen"], ["amyotrophic"]),

    # GI various
    ("OMEPRAZOLE_GERD_AUTO", "Omeprazole in GERD",
     ["omeprazole"], ["gastroesophageal reflux", "esophagitis"]),
    ("ESOMEPRAZOLE_GERD_AUTO", "Esomeprazole in GERD",
     ["esomeprazole"], ["gastroesophageal reflux"]),
    ("LANSOPRAZOLE_GERD_AUTO", "Lansoprazole in GERD/PUD",
     ["lansoprazole"], ["gastroesophageal reflux", "peptic ulcer"]),
    ("PANTOPRAZOLE_GERD_AUTO", "Pantoprazole in GERD",
     ["pantoprazole"], ["gastroesophageal reflux"]),
    ("RABEPRAZOLE_GERD_AUTO", "Rabeprazole in GERD",
     ["rabeprazole"], ["gastroesophageal reflux"]),
    ("DEXLANSOPRAZOLE_GERD_AUTO", "Dexlansoprazole in GERD",
     ["dexlansoprazole"], ["gastroesophageal reflux"]),

    # Newer derm
    ("ROFLUMILAST_TOP_PSO_AUTO", "Roflumilast topical PsO",
     ["roflumilast"], ["psoriasis"]),

    # Cardio prevention various
    ("ASPIRIN_PRIM_AUTO", "Aspirin primary CV prevention",
     ["aspirin"], ["cardiovascular"]),
    ("ASPIRIN_SECOND_AUTO", "Aspirin secondary CV prevention",
     ["aspirin"], ["coronary syndrome", "myocardial infarction"]),

    # Cancer cachexia / supportive
    ("ANAMORELIN_CACHEXIA_AUTO", "Anamorelin in cancer cachexia",
     ["anamorelin"], ["cachexia"]),
    ("LASMIDITAN_MIG_AUTO", "Lasmiditan in acute migraine",
     ["lasmiditan"], ["migraine"]),

    # Various rare
    ("AGALSIDASE_BETA_FABRY_AUTO", "Agalsidase beta in Fabry",
     ["agalsidase beta"], ["fabry"]),
    ("EFANESOCTOCOG_HEMA_2_AUTO", "Efanesoctocog alfa in hemophilia A",
     ["efanesoctocog"], ["hemophilia"]),
    ("TARALITAMAB_PROSTATE_AUTO", "Tarlatamab in prostate (Phase 2)",
     ["tarlatamab"], ["prostat"]),

    # COVID outpatient
    ("CASIRIVIMAB_OUTP_AUTO", "Casirivimab outpatient COVID",
     ["casirivimab"], ["covid-19", "sars-cov-2"]),
    ("BAMLANIVIMAB_OUTP_AUTO", "Bamlanivimab outpatient COVID",
     ["bamlanivimab"], ["covid"]),

    # Newer biologic combos
    ("BIMEKIZUMAB_AS_2_AUTO", "Bimekizumab in axSpA",
     ["bimekizumab"], ["axial spondyloarthritis"]),
    ("BIMEKIZUMAB_PSORIASIS_2_AUTO", "Bimekizumab in PsO",
     ["bimekizumab"], ["psoriasis"]),

    # Newer rare hemato
    ("BURATIO_NK_AUTO", "Magrolimab CD47 in MDS/AML",
     ["magrolimab"], ["myelodysplastic", "acute myeloid"]),

    # More obesity
    ("LIRAGLUTIDE_DIABESITY_AUTO", "Liraglutide 3 mg in obesity",
     ["liraglutide"], ["obesity"]),
    ("PHENTERMINE_TOPIRAMATE_OBESITY_AUTO", "Phentermine/topiramate obesity",
     ["phentermine"], ["obesity"]),
    ("NALTREXONE_BUPROPION_OBESITY_AUTO", "Naltrexone/bupropion in obesity",
     ["naltrexone"], ["obesity"]),
    ("ORLISTAT_OBESITY_AUTO", "Orlistat in obesity",
     ["orlistat"], ["obesity"]),

    # Pulm
    ("MONTELUKAST_ASTHMA_AUTO", "Montelukast in asthma",
     ["montelukast"], ["asthma"]),
    ("FORMOTEROL_ASTHMA_AUTO", "Formoterol-budesonide MART",
     ["formoterol"], ["asthma"]),

    # More renal
    ("PATIROMER_HYPER_AUTO", "Patiromer in hyperkalemia",
     ["patiromer"], ["hyperkalemia"]),
    ("ZIRCONIUM_HYPER_AUTO", "Sodium zirconium cyclosilicate hyperK",
     ["zirconium cyclosilicate", "sodium zirconium"], ["hyperkalemia"]),

    # PED neuro
    ("AVALGLUCOSIDASE_AUTO", "Avalglucosidase alfa Pompe",
     ["avalglucosidase"], ["pompe"]),

    # Newer GI
    ("MESALAMINE_UC_AUTO", "Mesalamine in UC",
     ["mesalamine", "mesalazine"], ["ulcerative colitis"]),
    ("BUDESONIDE_IBD_AUTO", "Budesonide in IBD",
     ["budesonide"], ["crohn", "ulcerative colitis"]),

    # Vacs
    ("HPV_NONA_AUTO", "9-valent HPV vaccine",
     ["gardasil 9", "9-valent hpv", "hpv 9-valent"], ["papillomavirus"]),
    ("HEPB_VACCINE_AUTO", "Hepatitis B vaccines",
     ["hepatitis b vaccine", "engerix", "heplisav"], ["hepatitis b"]),
    # Newer ophth
    ("DEXAMETHASONE_DME_AUTO", "Dexamethasone implant in DME",
     ["dexamethasone"], ["macular edema", "diabetic"]),
    ("RANIBIZUMAB_DME_AUTO", "Ranibizumab in DME",
     ["ranibizumab"], ["macular edema", "diabetic"]),

    # Newer cardio devices/surgical
    ("CABG_VS_PCI_AUTO", "CABG vs PCI various",
     ["coronary artery bypass", "cabg"], ["coronary artery disease"]),

    # Cancer additional
    ("PEMBROLIZUMAB_KIDNEY_ADJ_AUTO", "Pembrolizumab adjuvant RCC",
     ["pembrolizumab"], ["renal cell"]),
    ("ATEZOLIZUMAB_NSCLC_ADJ_AUTO", "Atezolizumab adjuvant NSCLC",
     ["atezolizumab"], ["non-small cell lung"]),
    ("DURVALUMAB_NSCLC_PERIOP_AUTO", "Durvalumab perioperative NSCLC AEGEAN",
     ["durvalumab"], ["non-small cell lung"]),

    # Various more
    ("MEROPENEM_AUTO", "Meropenem in severe infections",
     ["meropenem"], ["pneumonia", "intra-abdominal", "meningitis"]),
    ("DORIPENEM_AUTO", "Doripenem in CABP/nosocomial",
     ["doripenem"], ["pneumonia"]),

    # Batch 10 — final push
    ("ASPIRIN_PERIPHERAL_AUTO", "Aspirin for peripheral artery disease",
     ["aspirin"], ["peripheral artery"]),
    ("CLOPIDOGREL_STROKE_AUTO", "Clopidogrel in stroke/TIA",
     ["clopidogrel"], ["stroke", "transient ischemic"]),
    ("RIVAROXABAN_STROKE_AUTO", "Rivaroxaban in stroke prevention",
     ["rivaroxaban"], ["stroke"]),
    ("RIVAROXABAN_VTE_AUTO", "Rivaroxaban in VTE",
     ["rivaroxaban"], ["thromboembolism"]),
    ("APIXABAN_VTE_AUTO", "Apixaban in VTE",
     ["apixaban"], ["thromboembolism"]),
    ("APIXABAN_AF_AUTO", "Apixaban in AF",
     ["apixaban"], ["atrial fibrillation"]),
    ("DABIGATRAN_AF_AUTO", "Dabigatran in AF",
     ["dabigatran"], ["atrial fibrillation"]),
    ("DABIGATRAN_VTE_AUTO", "Dabigatran in VTE",
     ["dabigatran"], ["thromboembolism"]),
    ("EDOXABAN_VTE_AUTO", "Edoxaban in VTE",
     ["edoxaban"], ["thromboembolism"]),
    ("EDOXABAN_AF_AUTO", "Edoxaban in AF",
     ["edoxaban"], ["atrial fibrillation"]),
    ("BETRIXABAN_PROPH_AUTO", "Betrixaban extended VTE prophylaxis",
     ["betrixaban"], ["thromboembolism"]),
    ("METFORMIN_T2D_AUTO", "Metformin in T2D",
     ["metformin"], ["type 2 diabetes"]),
    ("INSULIN_GLARGINE_T2D_AUTO", "Insulin glargine in T2D",
     ["insulin glargine"], ["type 2 diabetes"]),
    ("LIRAGLUTIDE_T2D_AUTO", "Liraglutide in T2D",
     ["liraglutide"], ["type 2 diabetes"]),
    ("SEMAGLUTIDE_T2D_AUTO", "Semaglutide in T2D",
     ["semaglutide"], ["type 2 diabetes"]),
    ("DULAGLUTIDE_T2D_AUTO", "Dulaglutide in T2D",
     ["dulaglutide"], ["type 2 diabetes"]),
    ("EXENATIDE_T2D_AUTO", "Exenatide in T2D",
     ["exenatide"], ["type 2 diabetes"]),
    ("TIRZEPATIDE_T2D_AUTO", "Tirzepatide in T2D (SURPASS)",
     ["tirzepatide"], ["type 2 diabetes"]),
    ("LISINOPRIL_HTN_AUTO", "Lisinopril in HTN",
     ["lisinopril"], ["hypertension"]),
    ("VALSARTAN_HTN_AUTO", "Valsartan in HTN",
     ["valsartan"], ["hypertension"]),
    ("AMLODIPINE_HTN_AUTO", "Amlodipine in HTN",
     ["amlodipine"], ["hypertension"]),
    ("HYDROCHLOROTHIAZIDE_HTN_AUTO", "HCTZ in HTN",
     ["hydrochlorothiazide"], ["hypertension"]),
    ("ALBUTEROL_ASTHMA_AUTO", "Albuterol/salbutamol in asthma",
     ["albuterol", "salbutamol"], ["asthma"]),
    ("FLUTICASONE_ASTHMA_AUTO", "Fluticasone in asthma",
     ["fluticasone"], ["asthma"]),
    ("BUDESONIDE_ASTHMA_AUTO", "Budesonide in asthma",
     ["budesonide"], ["asthma"]),
    ("MONTELUKAST_RHIN_AUTO", "Montelukast in allergic rhinitis",
     ["montelukast"], ["rhinitis"]),
    ("LORATADINE_RHIN_AUTO", "Loratadine in allergic rhinitis",
     ["loratadine"], ["rhinitis"]),
    ("CETIRIZINE_RHIN_AUTO", "Cetirizine in allergic rhinitis",
     ["cetirizine"], ["rhinitis"]),
    ("DICLOFENAC_OA_AUTO", "Diclofenac in OA",
     ["diclofenac"], ["osteoarthritis"]),
    ("CELECOXIB_OA_AUTO", "Celecoxib in OA/RA",
     ["celecoxib"], ["osteoarthritis", "rheumatoid arthritis"]),
    ("MELOXICAM_OA_AUTO", "Meloxicam in OA",
     ["meloxicam"], ["osteoarthritis"]),
    ("NAPROXEN_PAIN_AUTO", "Naproxen in pain/RA",
     ["naproxen"], ["osteoarthritis", "rheumatoid arthritis"]),
    ("IBUPROFEN_PAIN_AUTO", "Ibuprofen in pain",
     ["ibuprofen"], ["osteoarthritis", "pain"]),
    ("FENTANYL_PAIN_AUTO", "Fentanyl transdermal in chronic pain",
     ["fentanyl"], ["chronic pain", "cancer pain"]),

    # Batch 11 — final 2-trustworthy push (post-2010 drugs, broad RCT footprint)
    ("PEMBROLIZUMAB_LUNG_AUTO", "Pembrolizumab in NSCLC",
     ["pembrolizumab"], ["lung", "nsclc", "non-small cell"]),
    ("NIVOLUMAB_LUNG_AUTO", "Nivolumab in NSCLC",
     ["nivolumab"], ["lung", "nsclc", "non-small cell"]),
    ("APIXABAN_STROKE_AUTO", "Apixaban for stroke prevention",
     ["apixaban"], ["stroke"]),
    ("DABIGATRAN_STROKE_AUTO", "Dabigatran for stroke prevention",
     ["dabigatran"], ["stroke"]),
    ("EDOXABAN_STROKE_AUTO", "Edoxaban for stroke prevention",
     ["edoxaban"], ["stroke"]),
    ("RIVAROXABAN_AF_AUTO", "Rivaroxaban in AF",
     ["rivaroxaban"], ["atrial fibrillation"]),
    ("RIVAROXABAN_ACS_AUTO", "Rivaroxaban in ACS",
     ["rivaroxaban"], ["acute coronary"]),
    ("APIXABAN_ACS_AUTO", "Apixaban in ACS",
     ["apixaban"], ["acute coronary"]),
    ("EMPAGLIFLOZIN_KIDNEY_AUTO", "Empagliflozin in CKD",
     ["empagliflozin"], ["kidney", "renal"]),
    ("DAPAGLIFLOZIN_KIDNEY_AUTO", "Dapagliflozin in CKD",
     ["dapagliflozin"], ["kidney", "renal"]),
]

print(f"Total topics to test: {len(TOPICS)}")

# ─── Auto-discover NCTs from AACT ───
print("Indexing AACT interventions.txt by drug pattern...")
intv_by_nct = defaultdict(list)
with open(AACT / "interventions.txt", "r", encoding="utf-8", errors="replace") as f:
    reader = csv.DictReader(f, delimiter="|")
    for row in reader:
        nct = (row.get("nct_id") or "").strip().upper()
        name = (row.get("name") or "").strip().lower()
        if nct and name:
            intv_by_nct[nct].append(name)

print(f"  NCTs with interventions: {len(intv_by_nct):,}")

print("Indexing conditions.txt...")
cond_by_nct = defaultdict(list)
with open(AACT / "conditions.txt", "r", encoding="utf-8", errors="replace") as f:
    reader = csv.DictReader(f, delimiter="|")
    for row in reader:
        nct = (row.get("nct_id") or "").strip().upper()
        cond = (row.get("downcase_name") or "").strip().lower()
        if nct and cond:
            cond_by_nct[nct].append(cond)
print(f"  NCTs with conditions: {len(cond_by_nct):,}")

# For each topic, find candidate NCTs
def find_ncts(drug_patterns, condition_patterns, max_per_topic=8):
    """Return list of NCTs whose interventions contain a drug pattern
    AND whose conditions contain a condition pattern."""
    matches = []
    for nct, intvs in intv_by_nct.items():
        intv_blob = " | ".join(intvs)
        if not any(p in intv_blob for p in drug_patterns): continue
        cond_blob = " | ".join(cond_by_nct.get(nct, []))
        if not any(p in cond_blob for p in condition_patterns): continue
        matches.append(nct)
        if len(matches) >= max_per_topic: break
    return matches


topic_specs = []
for t in TOPICS:
    if len(t) == 4:
        stem, name, drugs, conds = t
    else:
        stem, name, drugs, conds, _ = t
    drugs = [d.lower() for d in drugs]
    conds = [c.lower() for c in conds]
    ncts = find_ncts(drugs, conds)
    topic_specs.append({"stem": stem, "name": name, "ncts": ncts,
                         "drug_patterns": drugs, "condition_patterns": conds})

print(f"\nNCT discovery summary:")
n_with_ncts = sum(1 for t in topic_specs if t["ncts"])
print(f"  Topics with ≥1 NCT discovered: {n_with_ncts}/{len(topic_specs)}")
print(f"  Total candidate NCTs: {sum(len(t['ncts']) for t in topic_specs)}")

# ─── Load remaining AACT tables ───
all_ncts = sorted({nct for t in topic_specs for nct in t["ncts"]})
nct_set = set(all_ncts)
print(f"  Unique NCTs across all topics: {len(all_ncts)}")

def load_aact_filtered(filename, key_col, want_cols, filter_set):
    out = defaultdict(list)
    with open(AACT / filename, "r", encoding="utf-8", errors="replace") as f:
        reader = csv.DictReader(f, delimiter="|")
        for row in reader:
            k = (row.get(key_col) or "").strip().upper()
            if k in filter_set:
                out[k].append({c: (row.get(c) or "").strip() for c in want_cols})
    return out

print("Loading studies / baseline / outcomes / design_outcomes…")
studies = load_aact_filtered("studies.txt", "nct_id",
                              ["brief_title", "official_title", "enrollment",
                               "acronym", "start_date", "primary_completion_date"], nct_set)
baseline = load_aact_filtered("baseline_counts.txt", "nct_id",
                               ["ctgov_group_code", "count", "scope", "units"], nct_set)
outcomes = load_aact_filtered("outcome_measurements.txt", "nct_id",
                               ["ctgov_group_code", "title", "param_type",
                                "param_value_num", "param_value"], nct_set)
design_outs = load_aact_filtered("design_outcomes.txt", "nct_id",
                                  ["outcome_type", "measure"], nct_set)

# Get primary PMIDs
nct_pmids = defaultdict(list)
ref_file = AACT / "study_references.txt"
if ref_file.exists():
    with open(ref_file, "r", encoding="utf-8", errors="replace") as f:
        reader = csv.DictReader(f, delimiter="|")
        for row in reader:
            nct = (row.get("nct_id") or "").strip().upper()
            if nct not in nct_set: continue
            pmid = (row.get("pmid") or "").strip()
            rtype = (row.get("reference_type") or "").lower()
            if pmid and pmid.isdigit():
                if "result" in rtype or "primary" in rtype:
                    nct_pmids[nct].insert(0, pmid)
                else:
                    nct_pmids[nct].append(pmid)

# Fetch PubMed metadata (just primary PMIDs)
unique_pmids = list({nct_pmids[n][0] for n in nct_pmids if nct_pmids[n]})
print(f"  Unique primary PMIDs to fetch: {len(unique_pmids)}")

pubmed_meta = {}
if unique_pmids:
    BATCH = 50
    for i in range(0, len(unique_pmids), BATCH):
        batch = unique_pmids[i:i+BATCH]
        params = {"db": "pubmed", "id": ",".join(batch), "rettype": "abstract", "retmode": "xml"}
        url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?" + urllib.parse.urlencode(params)
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "rapidmeta/1.0"})
            with urllib.request.urlopen(req, timeout=60) as r:
                xml_data = r.read()
            root = ET.fromstring(xml_data)
            for art in root.findall(".//PubmedArticle"):
                pmid_el = art.find(".//PMID")
                if pmid_el is None: continue
                pmid = pmid_el.text.strip()
                title_el = art.find(".//ArticleTitle")
                title = "".join(title_el.itertext()).strip() if title_el is not None else ""
                abs_pieces = []
                for at in art.findall(".//Abstract/AbstractText"):
                    txt = "".join(at.itertext()).strip()
                    if txt: abs_pieces.append(txt)
                abstract = " ".join(abs_pieces)
                year_el = art.find(".//PubDate/Year")
                year = year_el.text if year_el is not None else None
                doi = ""
                for aid in art.findall(".//ArticleId"):
                    if aid.get("IdType") == "doi":
                        doi = (aid.text or "").strip(); break
                pubmed_meta[pmid] = {"title": title, "abstract": abstract,
                                      "year": int(year) if year and year.isdigit() else None,
                                      "doi": doi}
        except Exception as e:
            print(f"  efetch error: {e}")
        time.sleep(0.4)
    print(f"  fetched: {len(pubmed_meta)}")


# ─── Run gates per topic ───
def audit_nct(nct, topic):
    gates = {}; extracted = {"nct": nct}
    s = studies.get(nct, [])
    gates["A_aact_exists"] = bool(s)
    if not s: return {"gates": gates, "extracted": extracted}
    aact = s[0]
    extracted["aact_title"] = aact.get("brief_title", "")
    extracted["aact_acronym"] = aact.get("acronym", "")
    extracted["start_date"] = aact.get("start_date", "")
    extracted["primary_completion_date"] = aact.get("primary_completion_date", "")
    intv_text = " | ".join(intv_by_nct.get(nct, []))
    cond_text = " | ".join(cond_by_nct.get(nct, []))
    gates["B_drug_in_intvs"] = any(p in intv_text for p in topic["drug_patterns"])
    gates["C_condition_in_aact"] = any(p in cond_text for p in topic["condition_patterns"])
    extracted["aact_intvs"] = intv_by_nct.get(nct, [])[:3]
    extracted["aact_conditions"] = sorted(set(cond_by_nct.get(nct, [])))[:3]
    primary_pmid = nct_pmids.get(nct, [None])[0]
    extracted["pmid"] = primary_pmid
    pmid_topic_ok = False
    if primary_pmid and primary_pmid in pubmed_meta:
        m = pubmed_meta[primary_pmid]
        blob = (m.get("title", "") + " " + m.get("abstract", "")).lower()
        pmid_topic_ok = (any(p in blob for p in topic["drug_patterns"]) or
                          any(p in blob for p in topic["condition_patterns"]))
        extracted["pubmed_year"] = m.get("year")
        extracted["pubmed_doi"] = m.get("doi", "")
    gates["D_pmid_topic_match"] = pmid_topic_ok
    bg_counts = {b["ctgov_group_code"]: int(b["count"])
                  for b in baseline.get(nct, [])
                  if b.get("scope", "").lower() == "overall"
                  and b.get("units", "") == "Participants"
                  and b.get("count", "").isdigit()}
    total_n = sum(bg_counts.values())
    per_arm = {k: v for k, v in bg_counts.items() if v * 2 != total_n}
    gates["E_two_arms"] = len(per_arm) >= 2
    extracted["aact_per_arm_counts"] = per_arm
    primary_outs = [o for o in design_outs.get(nct, [])
                     if o["outcome_type"].lower() == "primary"]
    gates["F_primary_outcome_known"] = bool(primary_outs)
    extracted["aact_primary_outcome_measure"] = primary_outs[0]["measure"][:200] if primary_outs else ""
    om_counts = [(o["ctgov_group_code"], o.get("param_value_num") or o.get("param_value", ""))
                  for o in outcomes.get(nct, [])
                  if (o.get("param_type") or "").upper() in ("COUNT_OF_PARTICIPANTS", "NUMBER", "COUNT")]
    extracted["aact_outcome_count_rows"] = om_counts[:10]
    return {"gates": gates, "extracted": extracted}


viable_count = 0
results = []
for topic in topic_specs:
    if not topic["ncts"]: continue
    topic_audit = {"topic": topic, "trials": [], "n_total": 0, "n_pass_all": 0}
    for nct in topic["ncts"]:
        r = audit_nct(nct, topic)
        topic_audit["trials"].append(r)
        topic_audit["n_total"] += 1
        if all(r["gates"].values()):
            topic_audit["n_pass_all"] += 1
    # k>=2 gate for new reviews per Mahmood 2026-05-13: single-trial reviews
    # display fine but provide no pooling. Require ≥2 trials passing all gates.
    topic_audit["verdict"] = "VIABLE" if topic_audit["n_pass_all"] >= 2 else "NOT_VIABLE"
    topic_audit["pass_rate"] = topic_audit["n_pass_all"] / max(topic_audit["n_total"], 1)
    out_p = OUT / f"{topic['stem']}.json"
    out_p.write_text(json.dumps(topic_audit, indent=2, ensure_ascii=False, default=str),
                      encoding="utf-8")
    if topic_audit["verdict"] == "VIABLE":
        viable_count += 1
    results.append((topic["stem"], topic_audit["n_pass_all"], topic_audit["n_total"], topic_audit["verdict"]))

print(f"\n=== Summary: {viable_count}/{len(topic_specs)} VIABLE ===")
for stem, n_pass, n_total, verdict in results:
    print(f"  {verdict[:8]:8s} {stem:40s} {n_pass}/{n_total}")
