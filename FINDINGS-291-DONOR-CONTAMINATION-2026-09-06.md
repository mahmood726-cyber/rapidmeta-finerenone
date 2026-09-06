# Finding: template-donor contamination across the 291 object-less review pages

**Date:** 2026-09-06  **Scope:** the 291 indexed `*_REVIEW.html` pages that have no
`ssot` source object (added in a July 2026 batch by `scripts/propagate_nma_generator.py`
/ `propagate_multi_outcome.py`, now dormant and wired to nothing). Read-only audit; **no
page was modified.** The audit/mark/withdraw decision on the 291 is the owner's.

## Headline

**122 of 291 object-less pages (42%) cite a heart-failure / cardio-renal template's
trials under a clearly foreign title** — 100 with the donor block as the *majority* of
their cited evidence. This is not "unbacked-but-honest"; it is a foreign review's
evidence base presented under another review's title.

| Bucket | Count |
|---|---|
| Cite **no** donor trial (clean of the block) | 153 |
| Cite the donor block on a **foreign topic** -> contamination | 122 |
| -- **SEVERE** (donor trials >= own) | 100 |
| -- **CONTAMINATED** (donor present, own-majority) | 22 |
| Cardio/renal/metabolic topic (donor *may* be on-topic) -> **needs review** | 16 |
| **Total** | 291 |

## Method, and the first pass I retract

**Retracted first pass (title-vs-condition matching).** I first scored each page by
whether its cited trials' AACT conditions shared vocabulary with the page title. That
gave clean/contaminated/severe = 17/58/148/68 — and it is **unreliable**: it counts a
trial as "foreign" whenever my synonym map lacks the page's condition vocabulary, so
`OBESITY_DRUGS` scored "23 of 28 foreign" when the donor block is only ~9 trials. The
matcher's gaps, not contamination, produced most of that 148. Do not use those numbers.

**Method used here (matcher-independent).** A template donor injects the *same* trials
into many unrelated pages, so donor trials betray themselves by cross-page ubiquity.
Citation frequency has a clean gap: real trials appear on <=6 pages; then 9 NCTs jump to
42-138 pages. That set of 9 *is* the donor block, found without any vocabulary of mine —
it surfaced the finerenone/CKD trials I never hand-coded, so a different donor would be
caught the same way. A page is contamination if it cites the donor block on a topic the
block does not belong to.

**Donor block (9 NCTs), by page-count:**

- `NCT05901831` — cited by **138** pages — chronic kidney disease
- `NCT01035255` — cited by **90** pages — heart failure with reduced ejection fraction
- `NCT01920711` — cited by **89** pages — heart failure with preserved ejection fraction
- `NCT02924727` — cited by **89** pages — acute myocardial infarction
- `NCT04435626` — cited by **42** pages — heart failure
- `NCT01874431` — cited by **42** pages — diabetic nephropathies
- `NCT02545049` — cited by **42** pages — diabetic kidney disease
- `NCT02540993` — cited by **42** pages — chronic kidney disease
- `NCT05254002` — cited by **42** pages — type 2 diabetes mellitus

## Caveats

- **Fuzzy metabolic boundary.** The cardio/renal/metabolic bucket (16, donor may be
  on-topic) is drawn by a keyword on the title; a few pages sit on the edge (e.g.
  `TIRZEPATIDE_T2D` is metabolic but landed in "foreign"). The oncology/ID/neuro/derm
  pages in the SEVERE/CONTAMINATED lists are unambiguous.
- **Scope of the instrument.** This catches *this* template's contamination (the
  ubiquitous 9). A one-off clone with unique donor trials would be missed — but the
  frequency data shows the template injected the same block every time.
- Contamination of the **cited trial set** (+ drug names + displayed outcomes) is
  established; individual pooled numbers were not each reproduced.

## n of N

- Citations pulled from **290 of 291** pages; 1 cites none: `PNEUMONIA_AMOXICILLIN_DURATION`.
- **1,460 of 1,595** distinct cited NCTs resolve in the AACT 2026-08-30 snapshot; **135**
  do not — characterised separately (well-formed-but-absent vs not a real registration).
- **138** distinct pages cite >=1 donor-block trial.

## SEVERE — foreign topic, donor block >= own trials (100)

| page | own | donor |
|---|---|---|
| ACALABRUTINIB_CLL | 2 | 4 |
| ADC_HER2_ADJUVANT | 1 | 6 |
| ADC_HER2_LOW | 2 | 6 |
| ADC_HER2_NMA | 4 | 6 |
| ADJUVANT_IO_MELANOMA | 3 | 4 |
| AFLIBERCEPT_HD | 2 | 4 |
| ALK_NSCLC | 4 | 4 |
| ANTIAMYLOID_AD | 4 | 4 |
| ARPI_NMCRPC | 3 | 4 |
| AVACINCAPTAD_GA | 3 | 4 |
| AZITHROMYCIN_CHILD_MORTALITY | 3 | 4 |
| BELIMUMAB_SLE | 4 | 4 |
| BIMEKIZUMAB_PSORIASIS | 4 | 4 |
| BIOLOGIC_ASTHMA | 4 | 4 |
| CABOTEGRAVIR_HIV_ART | 3 | 4 |
| CAPIVASERTIB_BC | 1 | 4 |
| CART_DLBCL | 3 | 4 |
| CART_MM | 2 | 4 |
| CBD_SEIZURE | 4 | 4 |
| CDK46_MBC | 3 | 4 |
| CD_BIOLOGICS_NMA | 5 | 6 |
| CFTR_CF | 3 | 4 |
| CFTR_MODULATORS_NMA | 3 | 6 |
| CGRP_MIGRAINE_NMA | 4 | 6 |
| CGRP_MIGRAINE | 3 | 4 |
| COPD_TRIPLE | 3 | 4 |
| DELANDISTROGENE_DMD | 2 | 4 |
| DOAC_VTE_NMA | 4 | 6 |
| DOLUTEGRAVIR_ART_SSA | 3 | 4 |
| DONANEMAB_AD_SOLO | 2 | 4 |
| DUPILUMAB_AD | 3 | 4 |
| DUPILUMAB_COPD | 2 | 4 |
| ELACESTRANT_BC | 1 | 4 |
| ENSIFENTRINE_COPD | 2 | 4 |
| ESKETAMINE_TRD | 2 | 4 |
| ETRASIMOD_UC | 2 | 4 |
| EVT_BASILAR | 3 | 4 |
| EVT_EXTENDED_WINDOW | 3 | 4 |
| FARICIMAB_NAMD | 2 | 4 |
| FENFLURAMINE_SEIZURE | 3 | 4 |
| FEZOLINETANT_VMS | 2 | 4 |
| HCC_1L | 4 | 4 |
| HEMOPHILIA_GENE_THERAPY | 3 | 6 |
| HEPATITIS_HCV_DAA | 3 | 4 |
| HER2_LOW_ADC | 5 | 6 |
| HIDRADENITIS_SUPPURATIVA | 3 | 6 |
| HIGH_EFFICACY_MS | 4 | 4 |
| HIV_ART_FIRSTLINE | 1 | 4 |
| HPV_DOSE_REDUCTION | 2 | 4 |
| HPV_VACCINE_SCHEDULES | 3 | 6 |
| HYDROCORTISONE_SEPTIC_SHOCK | 3 | 6 |
| ICU_SEDATION | 3 | 6 |
| IL23_PSA | 4 | 4 |
| IL23_PSORIASIS | 3 | 4 |
| INAVOLISIB_BC | 1 | 4 |
| IO_CHEMO_NSCLC_1L | 4 | 4 |
| IPTACOPAN_IGAN | 1 | 4 |
| JAKI_RA_NMA | 4 | 6 |
| JAK_UC | 3 | 4 |
| KARXT_SCZ | 2 | 4 |
| KRAS_G12C | 2 | 4 |
| LEBRIKIZUMAB_AD | 4 | 4 |
| LU_PSMA_MCRPC | 2 | 4 |
| MEDITERRANEAN_DIET_CV | 1 | 6 |
| MIRIKIZUMAB_UC | 2 | 4 |
| MITAPIVAT_THALASSEMIA | 1 | 4 |
| MM_1L | 4 | 4 |
| NEOADJUVANT_IO_NSCLC | 3 | 4 |
| OSIMERTINIB_EGFR_NSCLC | 4 | 4 |
| PARP_ARPI_MCRPC | 3 | 4 |
| PARP_OVARIAN | 3 | 4 |
| PATISIRAN_POLYNEUROPATHY | 2 | 4 |
| PBC_PPAR | 2 | 4 |
| PEGCETACOPLAN_GA | 3 | 4 |
| PHYSICAL_REHAB_OLDER | 3 | 6 |
| PI3K_AKT_BC | 3 | 4 |
| POLYCYTHEMIA_VERA | 3 | 6 |
| POSTPARTUM_HEMORRHAGE | 1 | 6 |
| PPH_BUNDLE | 3 | 4 |
| RCC_1L | 4 | 4 |
| RESMETIROM_MASH | 1 | 4 |
| RISANKIZUMAB_CD | 3 | 4 |
| ROMOSOZUMAB_OP | 3 | 4 |
| RSV_VACCINE_OLDER | 3 | 4 |
| RUSFERTIDE_PV | 1 | 4 |
| SCD_DISEASE_MOD | 3 | 4 |
| SEVERE_ASTHMA_NMA | 5 | 6 |
| SEVERE_PEDIATRIC_FEBRILE_AFRICA | 0 | 6 |
| SPARSENTAN_IGAN | 1 | 4 |
| TEPLIZUMAB_T1D | 1 | 4 |
| TOFACITINIB_UC | 3 | 4 |
| TYVAC_TYPHOID | 1 | 4 |
| UPADACITINIB_CD | 3 | 4 |
| VENETOCLAX_AML | 2 | 4 |
| VENETOCLAX_CLL | 3 | 4 |
| VITAMIN_D_FRACTURE_FALL | 1 | 6 |
| VITILIGO | 3 | 6 |
| VOCLOSPORIN_LN | 1 | 4 |
| VORASIDENIB_GLIOMA | 1 | 4 |
| ZOLBETUXIMAB_GASTRIC | 2 | 4 |

## CONTAMINATED — foreign topic, donor present but own-majority (22)

| page | own | donor |
|---|---|---|
| AFICAMTEN_HCM | 4 | 1 |
| ALDO_SYNTHASE | 6 | 1 |
| ALOPECIA_JAKI | 5 | 4 |
| ANTIAMYLOID_AD_NMA | 7 | 6 |
| ANTIVEGF_NAMD_NMA | 10 | 6 |
| ANTI_CD20_MS | 10 | 6 |
| ARPI_mHSPC | 5 | 4 |
| ATOPIC_DERM_NMA | 7 | 6 |
| BTKI_CLL_NMA | 7 | 6 |
| EVT_LARGECORE | 6 | 4 |
| IL_PSORIASIS_NMA | 18 | 6 |
| INCLISIRAN | 3 | 1 |
| JAKI_AD | 6 | 4 |
| MIGRAINE_ACUTE | 8 | 6 |
| PAH_THERAPY | 8 | 6 |
| PSA_BIOLOGICS | 8 | 6 |
| SOTATERCEPT_PAH | 4 | 1 |
| SPONDYLOARTHRITIS | 8 | 6 |
| TIRZEPATIDE_T2D | 5 | 4 |
| TNK_VS_TPA_STROKE | 6 | 4 |
| UC_BIOLOGICS_NMA | 9 | 6 |
| VUTRISIRAN_ATTR | 6 | 1 |

## Needs review — cardio/renal/metabolic topic (donor may be on-topic) (16)

Includes `HFREF_NMA_AUTO_FULL` (a protected page). For these the donor trials are HF/CKD/
T2D trials that can legitimately belong; each needs a per-page look at whether the
foreign trial's data feeds a pooled estimate.

| page | own | donor |
|---|---|---|
| ACORAMIDIS_ATTR_CM | 5 | 1 |
| CARDIORENAL_DKD_NMA | 4 | 6 |
| DIABETIC_MACULAR_EDEMA | 3 | 6 |
| DIABETIC_RETINOPATHY | 3 | 6 |
| GLP1_CVOT_NMA | 8 | 6 |
| GLP1_MASH | 20 | 6 |
| HFREF_NMA_AUTO_FULL | 8 | 4 |
| HF_QUADRUPLE_NMA | 4 | 7 |
| HIFPH_CKD_ANEMIA | 6 | 4 |
| INCRETINS_T2D_NMA | 17 | 6 |
| INSULIN_ICODEC | 3 | 4 |
| OBESITY_DRUGS | 22 | 6 |
| RENAL_DENERV | 5 | 1 |
| SEMAGLUTIDE_OBESITY | 4 | 4 |
| SGLT2I_HF_NMA | 6 | 6 |
| TIRZEPATIDE_OBESITY | 3 | 4 |

---

## Appendix (2026-09-06): the 135 unresolved identifiers are fabricated

The contamination audit found 135 of the 1,595 cited NCTs did not resolve in the AACT
2026-08-30 snapshot. Absence from a snapshot is not fabrication -- a real trial can be
too new, withdrawn, or non-CT.gov -- so each was checked against **live**
ClinicalTrials.gov.

**Guarding the check against its own failure mode.** A per-id loop returned all `000`
(connection refused) under CT.gov's rate limiting -- a status about the reporter, not
the world. A `404` and a throttled nothing must not share a bucket. Two defences: the
check uses the batch `filter.ids=` endpoint (one request per ~40 ids, so the throttle
never triggers), and the split is three-way -- **confirmed-exists**, **confirmed-absent**,
**no-answer** -- with no-answer reported as its own number, never folded into either.
The method was validated with mixed real/fake controls: it returns the real NCTs
(`NCT05901831`, `NCT01035255`) and omits the fabricated ones.

**Result (n = 135):**

| | count |
|---|---|
| confirmed EXISTS on live CT.gov (real, absent from our snapshot) | **0** |
| confirmed ABSENT (404 -- not a real registration) | **135** |
| NO ANSWER obtained (throttled/failed -- not a verdict) | **0** |

So **all 135 are fabricated identifiers** -- well-formed `NCT########` numbers that do
not exist -- carried across **55 distinct served pages** (of the 291).

**Boundary check (does fabrication reach the vouched corpus?).** No. The 135 appear only
in the 291 object-less pages, with one exception: **3** (`NCT05305249`, `NCT05971644`,
`NCT06133752`) appear in `ssot/QUARANTINE_DECISIONS.md` -- a rejection log, where they are
recorded *as fabricated*, i.e. the system catching them, not accepting them. **`protocols/`,
`benchmarks/`, and all 55 object-backed review pages contain none.** Fabrication is
contained debt within the retired batch, not a breach of the part of the corpus with a
source object.

**Most-affected pages (fabricated-id count):**

- GERD_PCAB_NEW_NMA — 9
- PEDIATRIC_HF_DAPA_NMA — 9
- ROP_ANTI_VEGF_NMA — 9
- VT_ABLATION_NEW_NMA — 9
- HEP_D_BULEVIRTIDE_NMA — 6
- INTRAVASCULAR_LITHOTRIPSY_NMA — 6
- TB_BPaL_NEW_NMA — 6
- DERMATOMYOSITIS_NMA — 5
- AD_PEDIATRIC_BIOLOGIC_NMA — 4
- MASTOCYTOSIS_NEW_NMA — 4
- PEDIATRIC_OBESITY_GLP1_NMA — 4
- CABG_VS_PCI_LEFT_MAIN_NMA — 3
- CTEPH_NMA — 3
- ESOPHAGEAL_PERIOP_IO_NMA — 3
- OBESITY_DUAL_TRIPLE_AGONIST — 3
