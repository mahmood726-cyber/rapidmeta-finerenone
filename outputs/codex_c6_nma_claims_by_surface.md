# NMA Claims By Surface

- Files scanned: 1919 `.html` files under repo root and subdirectories, excluding `.git` and names matching `._rm_hook_identity_*`.
- Surface extraction read a 384 KB prefix per file (452.8 MB total); 1562 files had `</head>` inside that window, and 357 did not. Static `<h1>` extraction used only content outside `<script>`/`<style>` in that same prefix.
- Network validation full-read 175 candidate files (131.4 MB): every page claiming on at least one surface plus pages with concrete network-data markers. `rg` marker scan timeout: False.
- JSON-LD blocks parsed: 965; JSON parse failures: 0.

## Claim Predicate

A surface claims an NMA if its extracted text matches any of these predicates:

| Counted predicate | Regex used |
|---|---|
| network meta-analysis | `\bnetwork\s+meta[-\s]?analys(?:is|es)\b` case-insensitive |
| network meta | `\bnetwork\s+meta\b` case-insensitive |
| NMA acronym | `(?<![A-Za-z0-9])NMA(?![A-Za-z0-9])` case-sensitive standalone acronym |
| mixed treatment comparison | `\bmixed[-\s]+treatment\s+comparison(?:s)?\b` case-insensitive |
| indirect comparison | `\bindirect\s+comparison(?:s)?\b` case-insensitive |

I deliberately did not count generic `meta-analysis`, `network` alone, `treatment network` alone, `league table` alone, `network graph` alone, `netmeta` package mentions alone, GRADE `indirectness`, filenames, or URL/path fields. For schema.org JSON-LD I counted claim-bearing string values such as `headline`, `name`, `description`, and `keywords`, but excluded URL/identifier/image fields so `_NMA_REVIEW.html` paths do not become claims by themselves.

## Network Definition

A page has a network only if page data exposes more than two distinct treatment nodes and direct-comparison edges that support at least one indirect comparison path. Detection accepted data-bearing `NMA_CONFIG={treatments:[...], comparisons:[...]}` objects, JSON `nma_config` payloads, or Bucher/netmeta star-league data, then validated node count, nonempty trial-backed edges, and an indirect path. Empty configs, two-node pairwise configs, NMA UI stubs, and vendor/plugin names were not counted as networks.

## Counts

| Surface | Claims NMA | Claiming pages with network | Claiming pages without network |
|---|---:|---:|---:|
| TITLE (`<title>` and static `<h1>`) | 171 | 25 | 146 |
| SCHEMA.ORG JSON-LD | 172 | 26 | 146 |
| META DESCRIPTION | 103 | 0 | 103 |

- UNION, claims on at least one surface: 172
- INTERSECTION, claims on all three surfaces: 103
- Pages claiming on exactly one surface: 1
- Pages claiming on any surface and without a network: 146
- Pages claiming on any surface and with a network: 26

## Pages Claiming On Exactly One Surface

| Page | Surface |
|---|---|
| `HFREF_NMA_AUTO_FULL_REVIEW.html` | schema |

## Claiming Pages Without A Network

| Page | Claim surfaces |
|---|---|
| `AD_PEDIATRIC_BIOLOGIC_NMA_REVIEW.html` | title, schema, meta_description |
| `ADC_HER2_ADJUVANT_REVIEW.html` | title, schema |
| `ADC_HER2_LOW_REVIEW.html` | title, schema |
| `ALDO_SYNTHASE_REVIEW.html` | title, schema |
| `ALOPECIA_JAKI_REVIEW.html` | title, schema |
| `ALS_NEW_AGENTS_NMA_REVIEW.html` | title, schema, meta_description |
| `AML_VEN_FLT3_NMA_REVIEW.html` | title, schema, meta_description |
| `ANCA_VASCULITIS_NMA_REVIEW.html` | title, schema, meta_description |
| `BLADDER_NMIBC_NEW_NMA_REVIEW.html` | title, schema, meta_description |
| `BLADDER_UROTHEL_FRONTLINE_IO_NMA_REVIEW.html` | title, schema, meta_description |
| `BRONCHIECTASIS_BROAD_NMA_REVIEW.html` | title, schema, meta_description |
| `CABG_VS_PCI_LEFT_MAIN_NMA_REVIEW.html` | title, schema, meta_description |
| `CABP_NEW_ABX_NMA_REVIEW.html` | title, schema, meta_description |
| `CAR_T_LBCL_BROAD_NMA_REVIEW.html` | title, schema, meta_description |
| `CARDIAC_CONTRACTILITY_MOD_NMA_REVIEW.html` | title, schema, meta_description |
| `CMV_HCT_LETERMOVIR_NMA_REVIEW.html` | title, schema, meta_description |
| `COMPLEMENT_C5_BROAD_NMA_REVIEW.html` | title, schema, meta_description |
| `CONGENITAL_ADRENAL_HYPER_NMA_REVIEW.html` | title, schema, meta_description |
| `CRYO_AF_ABLATION_NMA_REVIEW.html` | title, schema, meta_description |
| `CTEPH_NMA_REVIEW.html` | title, schema, meta_description |
| `DCD_HEART_TRANSPLANT_NMA_REVIEW.html` | title, schema, meta_description |
| `DENGUE_VACCINE_NEW_NMA_REVIEW.html` | title, schema, meta_description |
| `DEPRESSION_PSYCHEDELIC_NMA_REVIEW.html` | title, schema, meta_description |
| `DERMATOMYOSITIS_NMA_REVIEW.html` | title, schema, meta_description |
| `DIABETIC_MACULAR_EDEMA_REVIEW.html` | title, schema, meta_description |
| `DIABETIC_RETINOPATHY_REVIEW.html` | title, schema, meta_description |
| `DRY_EYE_NEW_NMA_REVIEW.html` | title, schema, meta_description |
| `EOE_BIOLOGIC_NMA_REVIEW.html` | title, schema, meta_description |
| `ESOPHAGEAL_PERIOP_IO_NMA_REVIEW.html` | title, schema, meta_description |
| `FCRN_AGONIST_BROAD_NMA_REVIEW.html` | title, schema, meta_description |
| `GASTRIC_FRONTLINE_IO_NMA_REVIEW.html` | title, schema, meta_description |
| `GERD_PCAB_NEW_NMA_REVIEW.html` | title, schema, meta_description |
| `HAP_VAP_NEW_ABX_NMA_REVIEW.html` | title, schema, meta_description |
| `HBV_NEW_AGENTS_NMA_REVIEW.html` | title, schema, meta_description |
| `HCC_1L_REVIEW.html` | title, schema |
| `HCV_DAA_NEW_NMA_REVIEW.html` | title, schema, meta_description |
| `HEMODIALYSIS_AV_ACCESS_DCB_NMA_REVIEW.html` | title, schema, meta_description |
| `HEMOPHILIA_GENE_THERAPY_REVIEW.html` | title, schema, meta_description |
| `HEMOPHILIA_NEW_AGENTS_NMA_REVIEW.html` | title, schema, meta_description |
| `HEP_D_BULEVIRTIDE_NMA_REVIEW.html` | title, schema, meta_description |
| `HEPATITIS_HCV_DAA_REVIEW.html` | title, schema |
| `HER2_LOW_ADC_REVIEW.html` | title, schema |
| `HIDRADENITIS_SUPPURATIVA_REVIEW.html` | title, schema, meta_description |
| `HIFPH_CKD_ANEMIA_REVIEW.html` | title, schema |
| `HIPEC_PERITONEAL_NMA_REVIEW.html` | title, schema, meta_description |
| `HIV_ART_FIRSTLINE_REVIEW.html` | title, schema |
| `HPV_DOSE_REDUCTION_REVIEW.html` | title, schema |
| `HPV_VACCINE_SCHEDULES_REVIEW.html` | title, schema, meta_description |
| `HYDROCORTISONE_SEPTIC_SHOCK_REVIEW.html` | title, schema, meta_description |
| `HYPERKALEMIA_K_BINDER_NMA_REVIEW.html` | title, schema, meta_description |
| `HYPOFRAC_BREAST_RT_NMA_REVIEW.html` | title, schema, meta_description |
| `ICU_SEDATION_REVIEW.html` | title, schema, meta_description |
| `IGAN_TARGETED_BROAD_NMA_REVIEW.html` | title, schema, meta_description |
| `IL23_PSA_REVIEW.html` | title, schema |
| `INTRAVASCULAR_LITHOTRIPSY_NMA_REVIEW.html` | title, schema, meta_description |
| `ITP_NEW_THERAPY_NMA_REVIEW.html` | title, schema, meta_description |
| `KNEE_OA_INTRAARTICULAR_NMA_REVIEW.html` | title, schema, meta_description |
| `KRAS_G12C_REVIEW.html` | title, schema |
| `MASTOCYTOSIS_NEW_NMA_REVIEW.html` | title, schema, meta_description |
| `MEDITERRANEAN_DIET_CV_REVIEW.html` | title, schema, meta_description |
| `MIS_COLECTOMY_VS_OPEN_NMA_REVIEW.html` | title, schema, meta_description |
| `MIS_GASTRECTOMY_NMA_REVIEW.html` | title, schema, meta_description |
| `MIS_PANCREATIC_WHIPPLE_NMA_REVIEW.html` | title, schema, meta_description |
| `MM_1L_REVIEW.html` | title, schema |
| `MPOX_VACCINE_NMA_REVIEW.html` | title, schema, meta_description |
| `MS_ANTI_CD20_NMA_REVIEW.html` | title, schema, meta_description |
| `MS_BTK_INHIB_NMA_REVIEW.html` | title, schema, meta_description |
| `NEONATAL_NEC_NMA_REVIEW.html` | title, schema, meta_description |
| `NEUROENDOCRINE_PITUITARY_NMA_REVIEW.html` | title, schema, meta_description |
| `NF1_MEKi_NMA_REVIEW.html` | title, schema, meta_description |
| `NICOTINE_CYTISINICLINE_NMA_REVIEW.html` | title, schema, meta_description |
| `NMA_INDEX.html` | title, schema, meta_description |
| `NORMOTHERMIC_TRANSPLANT_NMA_REVIEW.html` | title, schema, meta_description |
| `OSTEOPOROSIS_BROAD_NMA_REVIEW.html` | title, schema, meta_description |
| `OUD_NEW_AGENTS_NMA_REVIEW.html` | title, schema, meta_description |
| `PEDIATRIC_HF_DAPA_NMA_REVIEW.html` | title, schema, meta_description |
| `PEDIATRIC_OBESITY_GLP1_NMA_REVIEW.html` | title, schema, meta_description |
| `PEDIATRIC_PSORIASIS_BIOLOGIC_NMA_REVIEW.html` | title, schema, meta_description |
| `PERIPHERAL_DCB_PAD_NMA_REVIEW.html` | title, schema, meta_description |
| `PFIC_CHOLESTATIC_PRURITUS_NMA_REVIEW.html` | title, schema, meta_description |
| `PFO_STROKE_CLOSURE_NMA_REVIEW.html` | title, schema, meta_description |
| `PHYSICAL_REHAB_OLDER_REVIEW.html` | title, schema, meta_description |
| `PI3K_AKT_BC_REVIEW.html` | title, schema |
| `POEM_ACHALASIA_NMA_REVIEW.html` | title, schema, meta_description |
| `POLYCYTHEMIA_VERA_REVIEW.html` | title, schema, meta_description |
| `POSTPARTUM_HEMORRHAGE_NEW_NMA_REVIEW.html` | title, schema, meta_description |
| `POSTPARTUM_HEMORRHAGE_REVIEW.html` | title, schema, meta_description |
| `PPH_BUNDLE_REVIEW.html` | title, schema |
| `PRESBYOPIA_NEW_NMA_REVIEW.html` | title, schema, meta_description |
| `PROSTATE_MRI_PSMA_DIAG_NMA_REVIEW.html` | title, schema, meta_description |
| `PROTON_RADIOTHERAPY_NMA_REVIEW.html` | title, schema, meta_description |
| `PRURIGO_NODULARIS_NMA_REVIEW.html` | title, schema, meta_description |
| `RCC_1L_REVIEW.html` | title, schema |
| `RECURRENT_PERICARDITIS_NMA_REVIEW.html` | title, schema, meta_description |
| `removed/CHOLANGIO_TARGETED_NMA_REVIEW.html` | title, schema, meta_description |
| `removed/ENDOMETRIOSIS_NEW_GNRH_NMA_REVIEW.html` | title, schema, meta_description |
| `removed/EPILEPSY_NEW_AGENTS_NMA_REVIEW.html` | title, schema, meta_description |
| `removed/FRAGILITY_FRACTURE_REVIEW.html` | title, schema |
| `removed/HCC_LOCAL_THERAPY_NMA_REVIEW.html` | title, schema, meta_description |
| `removed/HFpEF_DRUGS_NMA_REVIEW.html` | title, schema |
| `removed/HIV_TB_COINFECTION_ART_TIMING_REVIEW.html` | title, schema, meta_description |
| `removed/ICH_MIS_HEMATOMA_NMA_REVIEW.html` | title, schema, meta_description |
| `removed/OAB_BETA3_NMA_REVIEW.html` | title, schema, meta_description |
| `removed/RNA_INTERFERENCE_BROAD_NMA_REVIEW.html` | title, schema, meta_description |
| `removed/SBRT_OLIGOMETS_NMA_REVIEW.html` | title, schema, meta_description |
| `removed/SEPSIS_RESUSCITATION_REVIEW.html` | title, schema, meta_description |
| `removed/SGLT2_BROAD_OUTCOMES_NMA_REVIEW.html` | title, schema |
| `removed/STROKE_THROMBECTOMY_LATE_NMA_REVIEW.html` | title, schema, meta_description |
| `removed/T1D_CLOSED_LOOP_NMA_REVIEW.html` | title, schema, meta_description |
| `retired/ADHD_NEW_NMA_REVIEW.html` | title, schema |
| `retired/BIPOLAR_DEPRESSION_NEW_NMA_REVIEW.html` | title, schema |
| `retired/BISPECIFIC_LYMPHOMA_NMA_REVIEW.html` | title, schema |
| `retired/BPH_PROCEDURAL_NMA_REVIEW.html` | title, schema |
| `retired/CHRONIC_COUGH_REFRACTORY_NMA_REVIEW.html` | title, schema |
| `retired/CML_TFR_TKI_NMA_REVIEW.html` | title, schema |
| `retired/CRSWNP_BIOLOGIC_NMA_REVIEW.html` | title, schema |
| `retired/DRUG_RESISTANT_HTN_NEW_NMA_REVIEW.html` | title, schema |
| `retired/DRY_AMD_GA_BROAD_NMA_REVIEW.html` | title, schema |
| `retired/GENICULAR_RFA_KNEE_OA_NMA_REVIEW.html` | title, schema |
| `retired/GLAUCOMA_NEW_NMA_REVIEW.html` | title, schema |
| `retired/HoFH_LIPID_NEW_NMA_REVIEW.html` | title, schema |
| `retired/HOT_FLASH_NK3R_BROAD_NMA_REVIEW.html` | title, schema |
| `retired/INSOMNIA_DORA_NMA_REVIEW.html` | title, schema |
| `retired/LIVER_TRANSPLANT_HCV_NMA_REVIEW.html` | title, schema |
| `retired/MM_BISPECIFIC_BROAD_NMA_REVIEW.html` | title, schema |
| `retired/MR_FUS_TREMOR_NMA_REVIEW.html` | title, schema |
| `retired/MYOPIA_PROGRESSION_NMA_REVIEW.html` | title, schema |
| `retired/OBESITY_ENDOSCOPIC_NMA_REVIEW.html` | title, schema |
| `retired/OBESITY_NEXT_GEN_NMA_REVIEW.html` | title, schema |
| `retired/OSA_BROAD_NEW_NMA_REVIEW.html` | title, schema |
| `retired/PARKINSON_NEW_AGENTS_NMA_REVIEW.html` | title, schema |
| `retired/TTP_NEW_AGENTS_NMA_REVIEW.html` | title, schema |
| `ROP_ANTI_VEGF_NMA_REVIEW.html` | title, schema, meta_description |
| `RSV_PROPHY_INFANT_BROAD_NMA_REVIEW.html` | title, schema, meta_description |
| `SBRT_PROSTATE_LOCAL_NMA_REVIEW.html` | title, schema, meta_description |
| `SCD_DISEASE_MOD_REVIEW.html` | title, schema |
| `SCD_NEW_THERAPY_BROAD_NMA_REVIEW.html` | title, schema, meta_description |
| `SEVERE_PEDIATRIC_FEBRILE_AFRICA_REVIEW.html` | title, schema, meta_description |
| `TB_BPaL_NEW_NMA_REVIEW.html` | title, schema, meta_description |
| `TOTAL_NEOADJ_RECTAL_NMA_REVIEW.html` | title, schema, meta_description |
| `TRICUSPID_TEER_TMVR_NMA_REVIEW.html` | title, schema, meta_description |
| `TT_FIELDS_BROAD_NMA_REVIEW.html` | title, schema, meta_description |
| `VATS_SUBLOBAR_NSCLC_NMA_REVIEW.html` | title, schema, meta_description |
| `VITAMIN_D_FRACTURE_FALL_REVIEW.html` | title, schema, meta_description |
| `VITILIGO_REVIEW.html` | title, schema, meta_description |
| `VT_ABLATION_NEW_NMA_REVIEW.html` | title, schema, meta_description |

## Network-Positive Claiming Pages

| Page | Claim surfaces | Network evidence | Nodes | Edges |
|---|---|---|---:|---:|
| `ADC_HER2_NMA_REVIEW.html` | title, schema | literal NMA_CONFIG | 5 | 4 |
| `ANTI_CD20_MS_REVIEW.html` | title, schema | literal NMA_CONFIG | 6 | 5 |
| `ANTIAMYLOID_AD_NMA_REVIEW.html` | title, schema | literal NMA_CONFIG | 6 | 7 |
| `ANTIVEGF_NAMD_NMA_REVIEW.html` | title, schema | literal NMA_CONFIG | 8 | 11 |
| `ATOPIC_DERM_NMA_REVIEW.html` | title, schema | literal NMA_CONFIG | 8 | 7 |
| `BTKI_CLL_NMA_REVIEW.html` | title, schema | literal NMA_CONFIG | 8 | 7 |
| `CARDIORENAL_DKD_NMA_REVIEW.html` | title, schema | literal NMA_CONFIG | 6 | 5 |
| `CD_BIOLOGICS_NMA_REVIEW.html` | title, schema | literal NMA_CONFIG | 8 | 7 |
| `CFTR_MODULATORS_NMA_REVIEW.html` | title, schema | literal NMA_CONFIG | 4 | 3 |
| `CGRP_MIGRAINE_NMA_REVIEW.html` | title, schema | literal NMA_CONFIG | 5 | 4 |
| `DOAC_VTE_NMA_REVIEW.html` | title, schema | literal NMA_CONFIG | 5 | 4 |
| `GLP1_CVOT_NMA_REVIEW.html` | title, schema | literal NMA_CONFIG | 9 | 8 |
| `GLP1_MASH_REVIEW.html` | title, schema | literal NMA_CONFIG | 11 | 15 |
| `HF_QUADRUPLE_NMA_REVIEW.html` | title, schema | literal NMA_CONFIG | 3 | 2 |
| `HFREF_NMA_AUTO_FULL_REVIEW.html` | schema | json nma_config | 15 | 16 |
| `IL_PSORIASIS_NMA_REVIEW.html` | title, schema | literal NMA_CONFIG | 11 | 14 |
| `INCRETINS_T2D_NMA_REVIEW.html` | title, schema | literal NMA_CONFIG | 11 | 15 |
| `MIGRAINE_ACUTE_REVIEW.html` | title, schema | literal NMA_CONFIG | 5 | 4 |
| `OBESITY_DRUGS_REVIEW.html` | title, schema | literal NMA_CONFIG | 11 | 15 |
| `PAH_THERAPY_REVIEW.html` | title, schema | literal NMA_CONFIG | 6 | 5 |
| `PSA_BIOLOGICS_REVIEW.html` | title, schema | literal NMA_CONFIG | 6 | 5 |
| `retired/ANTIPSYCHOTICS_SCHIZO_REVIEW.html` | title, schema | literal NMA_CONFIG | 9 | 8 |
| `SEVERE_ASTHMA_NMA_REVIEW.html` | title, schema | literal NMA_CONFIG | 6 | 5 |
| `SGLT2I_HF_NMA_REVIEW.html` | title, schema | literal NMA_CONFIG | 4 | 3 |
| `SPONDYLOARTHRITIS_REVIEW.html` | title, schema | literal NMA_CONFIG | 6 | 5 |
| `UC_BIOLOGICS_NMA_REVIEW.html` | title, schema | literal NMA_CONFIG | 10 | 9 |

_Generated by enumeration only in 57.4 seconds._
