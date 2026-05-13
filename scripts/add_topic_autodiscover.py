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
AACT = Path("D:/AACT-storage/AACT/2026-04-12")

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
