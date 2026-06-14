# Unified truth-recovery — flagged published numbers (for Mahmood's decision)
> **Nothing here has been changed.** Read-only diff: each poolable published app's
> *own* study-level inputs were re-pooled through the Unified truth-recovery engine
> and compared to the **published** OR/RR/HR. Listed = where the engine WOULD
> change the headline. Mahmood decides what, if anything, to change.

## Read this first — why the engine diverges so often here, and what to trust
- **This corpus is the engine's out-of-distribution regime.** Published pooling is on
  a **log-OR / log-RR / log-HR** scale with often-large effects; the engine's NPE
  component is amortized on a simulation DGP (generic effect scale, mu~0.3, tau2~0.05).
  So the NPE **point** is systematically pulled toward its training prior here -- a
  *flag for review*, **NOT** a verified de-biasing. On this domain the **published /
  classical point is the more trustworthy one**; the engine's trustworthy output is
  the honest **interval** (which leans on the Manski partial-ID backstop), not the point.
- **Do not read the raw flag count as 'N published results are wrong.'** It mostly
  reflects the expected NPE OOD point pull, plus small-k instability in any classical
  comparator (at k=2 the DL-HKSJ t1 CI explodes to e.g. [0, 1e12], so a 'gains
  significance' there is the comparator blowing up, not a real change). Significance
  flips are therefore only asserted at **k>=5** with a non-degenerate comparator.
- `gate_fired` = the partial-ID backstop actively widened the interval (genuine
  selection/ambiguity signal -- most worth a look). `NPE=fallback` = the NPE could
  not run and the engine fell back (treat with extra care).

## Counts
- Poolable apps re-pooled: **1158** / 1158 considered (skipped 0, engine failures 0).
- **Tier A -- actionable (k>=5, published number present, real divergence): 111**, of which significance flips: **46**.
- Tier B -- lower-priority (small-k and/or point-only, NPE-OOD-dominated): **595**.
- The remaining ~452 apps agree within 10% of the published point (interval may still widen by design).
- Full per-app audit (all 1158 apps, machine-readable): `outputs/truth_recovery_repool.json`.

## Tier A -- actionable, review these first (111)
| App | k | Published | Unified [honest 95%] | Flag | gate | NPE |
|---|---|---|---|---|---|---|
| IL_PSORIASIS_NMA_REVIEW | 18 | 24.58 | 4.350 [0.908, 84.267] | **SIG-FLIP** (loses sig); point +465% vs published | yes | ok |
| SECUKINUMAB_PSORIASIS_AUTO_FULL_REVIEW | 5 | 1.12 | 2.352 [1.281, 3.275] | **SIG-FLIP** (gains sig); point +110% vs published | · | ok |
| PCSK9_INHIBITORS_CV_REVIEW | 10 | 2.90 | 1.468 [0.096, 6.343] | **SIG-FLIP** (loses sig); point +97% vs published | yes | ok |
| CHRONIC_URTICARIA_BIOLOGICS_REVIEW | 10 | 3.17 | 1.608 [0.936, 2.649] | **SIG-FLIP** (loses sig); point +97% vs published | · | ok |
| POEM_ACHALASIA_NMA_REVIEW | 6 | 2.14 | 1.136 [0.752, 1.507] | **SIG-FLIP** (loses sig); point +88% vs published | · | ok |
| GALCANEZUMAB_MIGRAINE_AUTO_REVIEW | 5 | 0.69 | 0.380 [0.007, 0.849] | **SIG-FLIP** (gains sig); point +82% vs published | yes | ok |
| BARIATRIC_RYGB_VS_SG_REVIEW | 10 | 2.30 | 1.334 [0.881, 1.893] | **SIG-FLIP** (loses sig); point +72% vs published | · | ok |
| STROKE_THROMBECTOMY_BROAD_REVIEW | 11 | 2.77 | 1.653 [0.944, 2.465] | **SIG-FLIP** (loses sig); point +68% vs published | · | ok |
| UPADACITINIB_RA_AUTO_FULL_REVIEW | 5 | 0.59 | 0.387 [0.220, 0.747] | **SIG-FLIP** (gains sig); point +52% vs published | · | ok |
| UPADACITINIB_RA_AUTO_REVIEW | 5 | 0.59 | 0.434 [0.210, 0.713] | **SIG-FLIP** (gains sig); point +36% vs published | · | ok |
| PERIPHERAL_DCB_PAD_NMA_REVIEW | 9 | 1.30 | 0.985 [0.631, 1.731] | **SIG-FLIP** (loses sig); point +32% vs published | · | ok |
| IXEKIZUMAB_AXIAL_AUTO_REVIEW | 5 | 0.39 | 0.312 [0.225, 0.507] | **SIG-FLIP** (gains sig); point +25% vs published | · | ok |
| SEVERE_ASTHMA_BIOLOGICS_REVIEW | 12 | 0.77 | 0.624 [0.425, 0.888] | **SIG-FLIP** (gains sig); point +23% vs published | · | ok |
| MYASTHENIA_GRAVIS_BIOLOGICS_REVIEW | 10 | 1.81 | 1.467 [0.840, 2.267] | **SIG-FLIP** (loses sig); point +23% vs published | · | ok |
| JAK_RA_REVIEW | 12 | 1.71 | 1.397 [0.828, 1.994] | **SIG-FLIP** (loses sig); point +22% vs published | · | ok |
| DRY_EYE_NEW_NMA_REVIEW | 8 | 1.70 | 1.396 [0.815, 2.231] | **SIG-FLIP** (loses sig); point +22% vs published | · | ok |
| IBD_BIOLOGICS_REVIEW | 12 | 2.04 | 1.677 [0.998, 2.370] | **SIG-FLIP** (loses sig); point +22% vs published | · | ok |
| EPILEPSY_NEW_AEDS_REVIEW | 10 | 1.90 | 1.575 [0.888, 2.585] | **SIG-FLIP** (loses sig); point +21% vs published | · | ok |
| DEPRESSION_NEW_RAPID_REVIEW | 10 | 1.43 | 1.186 [0.731, 1.782] | **SIG-FLIP** (loses sig); point +21% vs published | · | ok |
| CABP_NEW_ABX_NMA_REVIEW | 10 | 1.21 | 1.007 [0.840, 1.268] | **SIG-FLIP** (loses sig); point +20% vs published | · | ok |
| GALCANEZUMAB_MIGRAINE_AUTO_FULL_REVIEW | 5 | 0.69 | 0.583 [0.361, 0.960] | **SIG-FLIP** (gains sig); point +18% vs published | · | ok |
| GLOMERULONEPHRITIS_BIOLOGICS_REVIEW | 8 | 1.70 | 1.448 [0.819, 2.213] | **SIG-FLIP** (loses sig); point +17% vs published | · | ok |
| POSTOP_AKI_PREVENTION_REVIEW | 6 | 0.62 | 0.726 [0.420, 1.032] | **SIG-FLIP** (loses sig); point +17% vs published | · | ok |
| MYELOFIBROSIS_NEW_JAKI_REVIEW | 9 | 1.92 | 1.645 [0.886, 2.567] | **SIG-FLIP** (loses sig); point +17% vs published | · | ok |
| LUPUS_NEW_BIOLOGICS_REVIEW | 9 | 1.41 | 1.274 [0.826, 1.807] | **SIG-FLIP** (loses sig); point +11% vs published | · | ok |
| OAB_BETA3_NMA_REVIEW | 5 | 1.17 | 1.085 [0.685, 1.628] | **SIG-FLIP** (loses sig) | · | ok |
| MALARIA_ACT_REVIEW | 5 | 0.68 | 0.640 [0.400, 0.996] | **SIG-FLIP** (gains sig) | · | ok |
| CABG_VS_PCI_LEFT_MAIN_NMA_REVIEW | 8 | 1.30 | 1.241 [0.890, 1.758] | **SIG-FLIP** (loses sig) | · | ok |
| RSV_PROPHY_INFANT_BROAD_NMA_REVIEW | 5 | 0.40 | 0.418 [0.254, 0.772] | **SIG-FLIP** (gains sig) | · | ok |
| ANTIFUNGAL_NEWER_RESISTANT_REVIEW | 9 | 1.32 | 1.275 [0.739, 1.623] | **SIG-FLIP** (loses sig) | · | ok |
| ANTI_TIGIT_TUMORS_REVIEW | 8 | 0.88 | 0.850 [0.549, 1.010] | **SIG-FLIP** (loses sig) | · | ok |
| HFNC_NIV_RESP_FAILURE_REVIEW | 9 | 0.81 | 0.793 [0.497, 1.027] | **SIG-FLIP** (loses sig) | · | ok |
| GASTRIC_FRONTLINE_IO_NMA_REVIEW | 5 | 0.80 | 0.785 [0.569, 1.116] | **SIG-FLIP** (loses sig) | · | ok |
| SGLT2I_HF_NMA_REVIEW | 6 | 0.77 | 0.756 [0.444, 1.025] | **SIG-FLIP** (loses sig) | · | ok |
| DENOSUMAB_BONE_MET_AUTO_REVIEW | 5 | 1.13 | 1.148 [0.595, 1.799] | **SIG-FLIP** (loses sig) | · | ok |
| NEOADJUVANT_IO_BREAST_REVIEW | 10 | 1.14 | 1.157 [0.789, 1.737] | **SIG-FLIP** (loses sig) | · | ok |
| COPD_BIOLOGICS_BROAD_REVIEW | 7 | 0.82 | 0.809 [0.513, 1.010] | **SIG-FLIP** (loses sig) | · | ok |
| GLP1_CVOT_NMA_REVIEW | 8 | 0.86 | 0.854 [0.551, 1.047] | **SIG-FLIP** (loses sig) | · | ok |
| SGLT2_HF_REVIEW | 5 | 0.77 | 0.765 [0.467, 1.015] | **SIG-FLIP** (loses sig) | · | ok |
| TXA_NONCARDIAC_SURGERY_REVIEW | 5 | 0.82 | 0.816 [0.568, 1.159] | **SIG-FLIP** (loses sig) | · | ok |
| HF_QUADRUPLE_NMA_REVIEW | 6 | 0.79 | 0.793 [0.518, 1.002] | **SIG-FLIP** (loses sig) | · | ok |
| INTENSIVE_BP_REVIEW | 5 | 0.79 | 0.787 [0.463, 1.050] | **SIG-FLIP** (loses sig) | · | ok |
| LASMIDITAN_ACUTE_AUTO_REVIEW | 5 | — | 2.385 [1.412, 3.478] | **SIG-FLIP** (gains sig) | · | ok |
| LASMIDITAN_MIGRAINE_AUTO_REVIEW | 5 | — | 2.385 [1.412, 3.478] | **SIG-FLIP** (gains sig) | · | ok |
| LASMIDITAN_MIG_AUTO_REVIEW | 5 | — | 2.385 [1.412, 3.478] | **SIG-FLIP** (gains sig) | · | ok |
| PROSTATE_MRI_PSMA_DIAG_NMA_REVIEW | 8 | — | 1.267 [0.849, 1.852] | **SIG-FLIP** (loses sig) | · | ok |
| EOE_BIOLOGIC_NMA_REVIEW | 6 | 31.77 | 4.513 [2.778, 6.650] | point +604% vs published | · | ok |
| HEP_D_BULEVIRTIDE_NMA_REVIEW | 6 | 16.12 | 2.951 [1.874, 3.779] | point +446% vs published | · | ok |
| ICODEC_DIABETES_MELLITUS_AUTO_FULL_REVIEW | 5 | 0.48 | 0.164 [0.096, 1.351] | point +193% vs published | yes | ok |
| ICODEC_DIABETES_MELLITUS_AUTO_REVIEW | 5 | 0.48 | 0.187 [0.108, 1.418] | point +156% vs published | yes | ok |
| BOCOCIZUMAB_LIPID_AUTO_FULL_REVIEW | 5 | 0.29 | 0.129 [0.034, 0.197] | point +125% vs published | yes | ok |
| OBESITY_DUAL_TRIPLE_AGONIST_REVIEW | 7 | 6.56 | 3.134 [1.785, 3.665] | point +109% vs published | · | ok |
| PBC_NEW_AGENTS_REVIEW | 7 | 9.20 | 4.555 [3.245, 6.070] | point +102% vs published | · | ok |
| TRICUSPID_TEER_TMVR_NMA_REVIEW | 5 | 3.48 | 1.758 [1.028, 2.481] | point +98% vs published | · | ok |
| ELAGOLIX_FIBROIDS_AUTO_REVIEW | 6 | 0.41 | 0.209 [0.023, 1.292] | point +97% vs published | yes | ok |
| PRIMROSE_ELAGOLIX_AUTO_REVIEW | 6 | 0.41 | 0.209 [0.023, 1.292] | point +97% vs published | yes | ok |
| ELAGOLIX_FIBROIDS_AUTO_FULL_REVIEW | 6 | 0.41 | 0.213 [0.024, 1.207] | point +92% vs published | yes | ok |
| PRIMROSE_ELAGOLIX_AUTO_FULL_REVIEW | 6 | 0.41 | 0.213 [0.024, 1.207] | point +92% vs published | yes | ok |
| TANEZUMAB_OA_AUTO_REVIEW | 7 | 0.81 | 0.438 [0.268, 0.736] | point +85% vs published | · | ok |
| PREVNAR15_PNEUMO_AUTO_REVIEW | 7 | 1.17 | 0.636 [0.393, 1.029] | point +84% vs published | · | ok |
| CRYO_AF_ABLATION_NMA_REVIEW | 7 | 1.90 | 1.188 [0.747, 1.810] | point +60% vs published | · | ok |
| CTEPH_NMA_REVIEW | 6 | 46.57 | 29.279 [18.322, 56.691] | point +59% vs published | yes | ok |
| SECUKINUMAB_PSORIASIS_AUTO_REVIEW | 5 | 1.12 | 1.694 [0.889, 3.189] | point +51% vs published | · | ok |
| COMPLEMENT_C5_BROAD_NMA_REVIEW | 6 | 0.51 | 0.760 [0.051, 1.869] | point +49% vs published | yes | ok |
| HBV_FUNCTIONAL_CURE_REVIEW | 9 | 7.75 | 5.214 [3.545, 6.943] | point +49% vs published | · | ok |
| OMARIGLIPTIN_TYPE_2_AUTO_REVIEW | 7 | 1.00 | 0.673 [0.416, 1.122] | point +49% vs published | · | ok |
| ATOPIC_DERM_NMA_REVIEW | 7 | 5.54 | 3.777 [2.819, 9.110] | point +47% vs published | yes | ok |
| AD_PEDIATRIC_BIOLOGIC_NMA_REVIEW | 5 | 5.42 | 3.783 [2.650, 7.275] | point +43% vs published | yes | ok |
| NMOSD_BIOLOGICS_REVIEW | 6 | 0.19 | 0.272 [0.230, 0.379] | point +43% vs published | · | ok |
| PEDIATRIC_PSORIASIS_BIOLOGIC_NMA_REVIEW | 5 | 6.36 | 4.461 [3.179, 6.696] | point +43% vs published | · | ok |
| OUD_NEW_AGENTS_NMA_REVIEW | 5 | 2.93 | 2.059 [0.920, 2.814] | point +42% vs published | · | ok |
| IXEKIZUMAB_AXIAL_AUTO_FULL_REVIEW | 5 | 0.39 | 0.554 [0.327, 1.044] | point +42% vs published | · | ok |
| ITP_NEW_THERAPY_NMA_REVIEW | 8 | 5.53 | 3.909 [3.133, 5.532] | point +41% vs published | · | ok |
| COVID19_VACCINES_REVIEW | 12 | 0.22 | 0.311 [0.140, 0.389] | point +41% vs published | yes | ok |
| MS_S1P_BROAD_REVIEW | 7 | 1.14 | 0.809 [0.514, 1.311] | point +41% vs published | · | ok |
| RELUGOLIX_FIBROIDS_AUTO_2_FULL_REVIEW | 6 | 3.79 | 5.317 [4.096, 7.500] | point +40% vs published | · | ok |
| OSTEOPOROSIS_BROAD_NMA_REVIEW | 7 | 0.55 | 0.763 [0.460, 1.496] | point +39% vs published | · | ok |
| HYPERKALEMIA_K_BINDER_NMA_REVIEW | 6 | 2.20 | 1.598 [0.812, 2.639] | point +38% vs published | · | ok |
| DUCHENNE_GENE_THERAPY_REVIEW | 8 | 0.89 | 1.179 [0.709, 1.854] | point +32% vs published | · | ok |
| TOTAL_NEOADJ_RECTAL_NMA_REVIEW | 8 | 0.65 | 0.855 [0.510, 1.227] | point +32% vs published | · | ok |
| PREVNAR15_PNEUMO_AUTO_FULL_REVIEW | 7 | 1.17 | 1.538 [0.840, 2.362] | point +31% vs published | · | ok |
| SIRUKUMAB_ARTHRITIS_RHEUMATOID_AUTO_REVIEW | 5 | 0.93 | 0.710 [0.434, 1.218] | point +31% vs published | · | ok |
| HEAD_NECK_CRT_NEW_NMA_REVIEW | 8 | 1.08 | 0.833 [0.543, 1.338] | point +30% vs published | · | ok |
| MM_1L_DARA_REVIEW | 8 | 0.99 | 0.776 [0.460, 1.213] | point +28% vs published | · | ok |
| SIMEPREVIR_HCV_AUTO_FULL_REVIEW | 5 | 1.05 | 1.317 [0.050, 6.299] | point +25% vs published | yes | ok |
| SIMEPREVIR_HCV_AUTO_REVIEW | 5 | 1.05 | 1.317 [0.050, 6.299] | point +25% vs published | yes | ok |
| PNH_NEW_COMPLEMENT_REVIEW | 5 | 1.58 | 1.273 [0.594, 2.666] | point +24% vs published | · | ok |
| HEMOPHILIA_FACTOR_PROPHYLAXIS_REVIEW | 9 | 0.24 | 0.297 [0.233, 0.390] | point +24% vs published | · | ok |
| MDS_NEW_AGENTS_REVIEW | 7 | 1.46 | 1.179 [0.780, 1.782] | point +24% vs published | · | ok |
| SIRUKUMAB_ARTHRITIS_RHEUMATOID_AUTO_FULL_REVIEW | 5 | 0.93 | 0.769 [0.449, 1.366] | point +21% vs published | · | ok |
| CD_BIOLOGICS_NMA_REVIEW | 7 | 2.31 | 1.918 [1.109, 3.066] | point +20% vs published | · | ok |
| CGRP_MIGRAINE_PREVENT_REVIEW | 15 | 2.18 | 1.852 [1.283, 2.596] | point +18% vs published | · | ok |
| MIS_PANCREATIC_WHIPPLE_NMA_REVIEW | 5 | 1.08 | 0.918 [0.462, 1.541] | point +18% vs published | · | ok |
| ACUTE_HF_DIURESIS_NEW_REVIEW | 10 | 1.18 | 1.007 [0.658, 1.457] | point +17% vs published | · | ok |
| OMARIGLIPTIN_TYPE_2_AUTO_FULL_REVIEW | 7 | 1.00 | 0.858 [0.460, 1.280] | point +17% vs published | · | ok |
| VITAMIN_C_THIAMINE_SEPSIS_REVIEW | 8 | 1.12 | 0.971 [0.588, 1.349] | point +15% vs published | · | ok |
| BOCOCIZUMAB_LIPID_AUTO_REVIEW | 5 | 0.29 | 0.333 [0.014, 1.014] | point +15% vs published | yes | ok |
| TANEZUMAB_OA_AUTO_FULL_REVIEW | 7 | 0.81 | 0.711 [0.428, 1.036] | point +14% vs published | · | ok |
| ANCA_VASCULITIS_NMA_REVIEW | 9 | 0.97 | 0.853 [0.493, 1.347] | point +14% vs published | · | ok |
| EOSINOPHILIC_DISEASES_BROAD_REVIEW | 11 | 2.66 | 2.340 [1.387, 3.221] | point +14% vs published | · | ok |
| COVID19_HOSPITALIZED_TX_REVIEW | 9 | 0.57 | 0.504 [0.328, 0.901] | point +13% vs published | · | ok |
| AML_TARGETED_NEW_REVIEW | 9 | 0.66 | 0.742 [0.581, 0.909] | point +12% vs published | · | ok |
| MASH_DRUGS_REVIEW | 10 | 2.00 | 1.780 [1.065, 2.704] | point +12% vs published | · | ok |
| SBRT_PROSTATE_LOCAL_NMA_REVIEW | 7 | 0.72 | 0.807 [0.519, 1.083] | point +12% vs published | · | ok |
| NORMOTHERMIC_TRANSPLANT_NMA_REVIEW | 5 | 0.55 | 0.615 [0.374, 0.947] | point +12% vs published | · | ok |
| BRONCHIECTASIS_BROAD_NMA_REVIEW | 9 | 0.83 | 0.743 [0.506, 1.152] | point +12% vs published | · | ok |
| UC_BIOLOGICS_NMA_REVIEW | 9 | 2.92 | 2.626 [1.651, 3.783] | point +11% vs published | · | ok |
| ARDS_PRONE_POSITIONING_REVIEW | 9 | 0.64 | 0.707 [0.469, 0.925] | point +11% vs published | · | ok |
| ESOPHAGEAL_PERIOP_IO_NMA_REVIEW | 5 | 0.78 | 0.860 [0.548, 1.212] | point +10% vs published | · | ok |
| PAH_SOTATERCEPT_BROAD_REVIEW | 10 | 0.83 | 0.914 [0.618, 1.356] | point +10% vs published | · | ok |
| JAKI_RA_NMA_REVIEW | 5 | 3.30 | 2.997 [1.664, 3.682] | point +10% vs published | · | ok |

## Tier B -- lower priority (595 total; top 40 by divergence shown)
_Small-k and/or point-only divergences, dominated by the NPE OOD pull described above. The published/classical point is usually the more reliable one here._

| App | k | Published | Unified [honest 95%] | Flag | gate | NPE |
|---|---|---|---|---|---|---|
| ANDEXANET_BLEEDING_AUTO_FULL_REVIEW | 3 | 0.06 | 38.942 [0.000, 75.613] | point +64803% vs published | yes | ok |
| TIRZEPATIDE_ARDS_AUTO_FULL_REVIEW | 3 | 0.06 | 38.942 [0.000, 75.613] | point +64803% vs published | yes | ok |
| DABIGATRAN_VTE_AUTO_REVIEW | 4 | 4.19 | 630.005 [0.008, 1298.918] | point +14936% vs published | yes | ok |
| SELADELPAR_PBC_AUTO_FULL_REVIEW | 2 | 0.27 | 27.407 [16.653, 56.957] | point +10051% vs published | yes | ok |
| MENACWY_BOOSTER_AUTO_FULL_REVIEW | 3 | 2.80 | 235.514 [0.002, 510.762] | point +8311% vs published | yes | ok |
| AZACITIDINE_MDS_AUTO_REVIEW | 2 | 0.52 | 13.495 [0.010, 218.788] | point +2495% vs published | yes | ok |
| EVINACUMAB_HOFH_AUTO_FULL_REVIEW | 2 | 1.66 | 31.302 [0.002, 1273.708] | point +1786% vs published | yes | ok |
| RAVULIZUMAB_PNH_AUTO_REVIEW | 4 | 0.87 | 15.618 [0.004, 87.190] | point +1695% vs published | yes | ok |
| GUSELKUMAB_ARTHRITIS_PSORIATIC_AUTO_FULL_REVIEW | 3 | 0.65 | 10.003 [0.001, 70.969] | point +1439% vs published | yes | ok |
| BIMEKIZUMAB_PSORIASIS_2_AUTO_FULL_REVIEW | 3 | 0.31 | 4.665 [0.003, 22.347] | point +1405% vs published | yes | ok |
| BIMEKIZUMAB_PSORIASIS_AUTO_FULL_REVIEW | 3 | 0.31 | 4.665 [0.003, 22.347] | point +1405% vs published | yes | ok |
| LESINURAD_GOUT_AUTO_FULL_REVIEW | 2 | 5.16 | 0.352 [0.007, 44.841] | point +1364% vs published | yes | ok |
| ZOLBETUXIMAB_GASTRIC_AUTO_FULL_REVIEW | 2 | 9.00 | 0.810 [0.525, 1.236] | point +1011% vs published | · | ok |
| APIXABAN_AF_AUTO_REVIEW | 2 | 1.50 | 0.136 [0.103, 0.239] | point +1001% vs published | · | ok |
| HEPATITIS_HCV_DAA_REVIEW | 2 | 10.70 | 0.980 [0.000, 6033.312] | point +991% vs published | yes | ok |
| DORIPENEM_AUTO_REVIEW | 2 | 5.56 | 0.529 [0.336, 0.876] | point +951% vs published | · | ok |
| DORIPENEM_AUTO_FULL_REVIEW | 2 | 5.56 | 0.545 [0.009, 229.180] | point +919% vs published | yes | ok |
| CIPROFLOXACIN_UTI_AUTO_REVIEW | 2 | 0.97 | 0.099 [0.002, 1.366] | point +880% vs published | yes | ok |
| MITAPIVAT_PYRUVATE_AUTO_REVIEW | 2 | 1.13 | 10.722 [0.024, 125.944] | point +849% vs published | yes | ok |
| EVINACUMAB_HOFH_AUTO_REVIEW | 2 | 1.66 | 0.175 [0.135, 0.300] | point +849% vs published | · | ok |
| ATOGEPANT_MIGRAINE_AUTO_REVIEW | 2 | 3.96 | 0.420 [0.023, 161.843] | point +844% vs published | yes | ok |
| ATOGEPANT_PREVENT_AUTO_REVIEW | 2 | 3.96 | 0.420 [0.023, 161.843] | point +844% vs published | yes | ok |
| ALECTINIB_ALK_NSCLC_AUTO_REVIEW | 2 | 2.55 | 0.275 [0.017, 149.372] | point +827% vs published | yes | ok |
| MIRIKIZUMAB_PSO_AUTO_REVIEW | 3 | 0.08 | 0.724 [0.008, 1.863] | point +804% vs published | yes | ok |
| EPTINEZUMAB_CHRONIC_AUTO_REVIEW | 3 | 7.28 | 0.808 [0.006, 83.154] | point +801% vs published | yes | ok |
| EPTINEZUMAB_MIGRAINE_AUTO_REVIEW | 3 | 7.28 | 0.808 [0.006, 83.154] | point +801% vs published | yes | ok |
| MEN_ACWY_AUTO_REVIEW | 4 | 0.69 | 0.082 [0.041, 0.120] | point +746% vs published | · | ok |
| ANDEXANET_BLEEDING_AUTO_REVIEW | 3 | 0.06 | 0.007 [0.004, 0.012] | point +720% vs published | · | ok |
| TIRZEPATIDE_ARDS_AUTO_REVIEW | 3 | 0.06 | 0.007 [0.004, 0.012] | point +720% vs published | · | ok |
| ETRASIMOD_UC_AUTO_FULL_REVIEW | 3 | 1.16 | 9.215 [0.012, 23.141] | point +694% vs published | yes | ok |
| WARFARIN_AF_AUTO_REVIEW | 2 | 1.41 | 0.194 [0.135, 0.295] | point +628% vs published | · | ok |
| RUXOLITINIB_AD_AUTO_REVIEW | 2 | 0.36 | 2.549 [0.001, 48.173] | point +608% vs published | yes | ok |
| ALIROCUMAB_LIPID_AUTO_FULL_REVIEW | 2 | 0.29 | 0.041 [0.029, 0.066] | point +600% vs published | · | ok |
| MEN_ACWY_AUTO_FULL_REVIEW | 4 | 0.69 | 0.099 [0.032, 4.029] | point +594% vs published | yes | ok |
| RUCAPARIB_PROSTATE2_AUTO_REVIEW | 3 | 2.04 | 0.295 [0.004, 3.408] | point +590% vs published | yes | ok |
| RUCAPARIB_PROSTATE_AUTO_REVIEW | 3 | 2.04 | 0.295 [0.004, 3.408] | point +590% vs published | yes | ok |
| DINUTUXIMAB_NEUROBLASTOMA_AUTO_REVIEW | 2 | 0.89 | 6.005 [0.009, 75.305] | point +575% vs published | yes | ok |
| OFATUMUMAB_CLL_AUTO_REVIEW | 2 | 1.23 | 7.756 [0.008, 35.823] | point +531% vs published | yes | ok |
| GOSERELIN_PROSTATE_AUTO_FULL_REVIEW | 2 | 5.59 | 0.896 [0.528, 1.584] | point +524% vs published | · | ok |
| TOFACITINIB_PSA_AUTO_FULL_REVIEW | 2 | 1.30 | 7.882 [5.376, 10.313] | point +506% vs published | · | ok |

_Engine: truth_recovery v3.0.0, config {'mode': 'gated', 'npe_scale': 1.15, 'coverage_target': 0.9}. Comparator: published OR/RR/HR (fallback: poolcheck py_est). Generated read-only; no published artifact modified._
