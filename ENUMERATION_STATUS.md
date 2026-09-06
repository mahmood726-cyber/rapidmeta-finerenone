# Enumeration: trials before and after the bound was raised

STATUS at commit `5b53fb62`, all seven lane commits verified on `origin/main`.
Every number below is MEASURED against AACT `2026-08-30` (interventions.txt 217,740,084 bytes, 2026-08-30T18:01:33Z).
Reproduce: `AACT_DIR=<snapshot> python scripts/measure_cap_cost_by_topic_2026_09_03.py`

## The number Mahmood asked for

| | |
|---|---|
| topics measured (N named below) | **53** |
| trials BEFORE — sum of delivered `n_total` | **368** |
| trials AFTER — sum of the pools the matcher finds | **1805** |
| discarded unrecorded at the corpus bound (8) | **1453** |
| discarded unrecorded at the old default (20) | **1168** |
| topics delivered pinned at exactly 8 | **38 of 53** |

`n_total` is the count AFTER the slice, so for the 38 pinned topics the delivered
figure is the cap wearing the costume of a count. The bound is now `MAX_PER_TOPIC=500`
(`RM_MAX_PER_TOPIC` overrides), chosen because it truncated 0 of these 53.

## Per topic, all 53 named

`defs` marks a stem defined more than once in TOPICS: the LAST definition wins and both
write the same `outputs/new_topics/<STEM>.json`, so an earlier question can be replaced.

| topic | before (`n_total`) | after (pool) | cut@8 | cut@20 | defs |
|---|---:|---:|---:|---:|---:|
| `VENETOCLAX_CLL_AUTO` | 8 | 460 | 452 | 440 | x2 |
| `CPAP_OSA_AUTO` | 8 | 294 | 286 | 274 |  |
| `FORMOTEROL_COPD_AUTO` | 8 | 177 | 169 | 157 | x2 |
| `PIOGLITAZONE_T2D_AUTO` | 8 | 116 | 108 | 96 |  |
| `PEMBROLIZUMAB_KIDNEY_ADJ_AUTO_2` | 8 | 110 | 102 | 90 |  |
| `PALONOSETRON_CINV_AUTO` | 8 | 59 | 51 | 39 | x2 |
| `LIPOSOMAL_BUPIVACAINE_AUTO` | 8 | 48 | 40 | 28 | x2 |
| `MONTELUKAST_RHIN_AUTO` | 8 | 41 | 33 | 21 |  |
| `LURASIDONE_SCHIZ_AUTO` | 8 | 37 | 29 | 17 |  |
| `AMIVANTAMAB_LUNG_AUTO` | 8 | 26 | 18 | 6 |  |
| `MILNACIPRAN_FIBRO_AUTO` | 8 | 20 | 12 | 0 | x2 |
| `CARIPRAZINE_DEPRESSION_AUTO` | 8 | 18 | 10 | 0 |  |
| `EZETIMIBE_LIPID_AUTO` | 8 | 18 | 10 | 0 |  |
| `CARIPRAZINE_BIPOLAR_AUTO` | 8 | 17 | 9 | 0 |  |
| `NETARSUDIL_GLAUCOMA_AUTO` | 8 | 17 | 9 | 0 |  |
| `ROCKLATAN_GLAUCOMA_AUTO` | 8 | 17 | 9 | 0 | x2 |
| `SOTATERCEPT_PAH_AUTO_2` | 8 | 17 | 9 | 0 |  |
| `VADADUSTAT_ANEMIA_AUTO` | 8 | 17 | 9 | 0 |  |
| `VADADUSTAT_RENAL_ANEMIA_AUTO` | 8 | 17 | 9 | 0 |  |
| `VRAYLAR_BIPOLAR_DEPRESSION_AUTO` | 8 | 17 | 9 | 0 |  |
| `CARIPRAZINE_SCHIZ_AUTO` | 8 | 16 | 8 | 0 |  |
| `HDM_AIT_AUTO` | 8 | 16 | 8 | 0 |  |
| `VOXELOTOR_SCD_AUTO_2` | 8 | 16 | 8 | 0 |  |
| `PACRITINIB_MF_AUTO_2` | 8 | 15 | 7 | 0 |  |
| `PEGVISOMANT_ACROMEGALY_AUTO` | 8 | 14 | 6 | 0 | x2 |
| `DACOMITINIB_LUNG_AUTO_2` | 8 | 13 | 5 | 0 |  |
| `DUTASTERIDE_BPH_AUTO` | 8 | 13 | 5 | 0 | x2 |
| `ASFOTASE_HPP_AUTO` | 8 | 12 | 4 | 0 |  |
| `ELINZANETANT_HOT_FLASHES_AUTO` | 8 | 12 | 4 | 0 |  |
| `ICOSAPENT_LIPID_AUTO` | 8 | 12 | 4 | 0 |  |
| `MOMELOTINIB_MF_AUTO_2` | 8 | 12 | 4 | 0 |  |
| `NETARSUDIL_OCULAR_HYPERTENSION_AUTO` | 8 | 11 | 3 | 0 |  |
| `BEPIROVIRSEN_HBV_AUTO` | 8 | 10 | 2 | 0 | x2 |
| `EVOLOCUMAB_ASCVD_AUTO_2` | 8 | 10 | 2 | 0 |  |
| `AVACINCAPTAD_GA_AUTO` | 8 | 8 | 0 | 0 | x2 |
| `LIGELIZUMAB_URTICARIA_AUTO_2` | 8 | 8 | 0 | 0 |  |
| `RELUGOLIX_FIBROIDS_AUTO_2` | 8 | 8 | 0 | 0 |  |
| `LUMATEPERONE_BIPOLAR_DEPRESSION_AUTO` | 5 | 7 | 0 | 0 |  |
| `LUMATEPERONE_MAJOR_DEPRESSIVE_AUTO` | 5 | 7 | 0 | 0 |  |
| `CRINECERFONT_CAH_AUTO` | 4 | 5 | 0 | 0 |  |
| `TALIGLUCERASE_GAUCHER_AUTO` | 5 | 5 | 0 | 0 |  |
| `AVACINCAPTAD_GA_AUTO_2` | 7 | 4 | 0 | 0 |  |
| `ICLEPERTIN_SCHIZOPHRENIA_AUTO` | 4 | 4 | 0 | 0 |  |
| `ICOSAPENT_CVD_AUTO` | 6 | 4 | 0 | 0 |  |
| `TASIMELTEON_AUTO` | 4 | 4 | 0 | 0 | x2 |
| `DALBAVANCIN_ABSSSI_AUTO` | 2 | 3 | 0 | 0 | x2 |
| `ENSIFENTRINE_COPD_AUTO` | 3 | 3 | 0 | 0 | x2 |
| `FOSTAMATINIB_ITP_AUTO` | 6 | 3 | 0 | 0 | x2 |
| `METOCLOPRAMIDE_GASTRO_AUTO` | 4 | 3 | 0 | 0 |  |
| `DEXLANSOPRAZOLE_GERD_AUTO` | 2 | 2 | 0 | 0 | x2 |
| `FLUTICASONE_UMECLIDINIUM_VILANTEROL_AUTO` | 5 | 1 | 0 | 0 | x2 |
| `OCTREOTIDE_DUMP_AUTO` | 2 | 1 | 0 | 0 | x2 |
| `OBICETRAPIB_LIPID_AUTO` | 8 | 0 | 0 | 0 | x2 |

## What this does NOT claim

The extra candidates passed the drug, condition, trial-identity and study-type gates and
NOTHING ELSE. The six per-trial gates have not been applied to them and nothing downstream
has seen them. The claim is only that they were retrieved, screened, confirmed eligible,
and then discarded by an array bound without being counted.

Seven topics have pools SMALLER than their delivered `n_total`; all are named in the
instrument output with their condition patterns and definition counts. A smaller pool is
not a cap effect — it is either the trial-identity gate added in `8b41493b`, or a collided
duplicate definition asking a different question.
