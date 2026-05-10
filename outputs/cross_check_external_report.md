# External cross-check: extracted pooled estimates vs published claims

Sample: 30 reviews (>= 3 valid trials in realData; tE<=tN & cE<=cN; landing-card claim preferred over inline benchmark when both exist).

Pool method: random-effects DerSimonian-Laird on log-OR; Haldane 0.5 only when at least one cell is zero.

| Review | k | Claim (src/measure/est [lci-uci], k) | Our re-pool OR (95% CI), tau^2 | |dlog| | Suspected cause |
|---|---:|---|---|---:|---|
| ABLATION_AF_REVIEW | 4 | [i] HR 0.62 (0.43-0.87), k=1 | OR 0.72 (0.59-0.86), tau2=0.012 | 0.143 | scale-mismatch (HR vs OR); k differs (1->4) |
| ACS_ANTIPLATELET_REVIEW | 4 | [i] HR 0.84 (0.77-0.92), k=1 | OR 0.84 (0.66-1.07), tau2=0.053 | 0.003 | converge |
| ACUTE_HF_DIURESIS_NEW_REVIEW | 10 | [i] HR 0.77 (0.72-0.82), k=5 | OR 1.59 (1.10-2.31), tau2=0.298 | 0.727 | stale card text (Vaduganathan/Jhund SGLT2i placeholder bled into unrelated review) |
| ADC_HER2_NMA_REVIEW | 4 | [i] HR 0.28 (0.22-0.37), k=1 | OR 0.41 (0.21-0.80), tau2=0.335 | 0.374 | scale-mismatch (HR vs OR); k differs (1->4) |
| ADHD_NEW_NMA_REVIEW | 10 | [i] HR 0.77 (0.72-0.82), k=5 | OR 4.58 (3.78-5.53), tau2=0.000 | 1.782 | stale card text (Vaduganathan/Jhund SGLT2i placeholder bled into unrelated review) |
| ADJUVANT_IO_MELANOMA_REVIEW | 3 | [i] HR 0.49 (0.38-0.64), k=1 | OR 0.51 (0.42-0.62), tau2=0.009 | 0.042 | converge |
| ADJUVANT_IO_PAN_TUMOR_REVIEW | 11 | [i] HR 0.77 (0.72-0.82), k=5 | OR 0.64 (0.59-0.71), tau2=0.007 | 0.177 | stale card text (Vaduganathan/Jhund SGLT2i placeholder bled into unrelated review) |
| AD_PEDIATRIC_BIOLOGIC_NMA_REVIEW | 10 | [i] HR 0.77 (0.72-0.82), k=5 | OR 14.61 (8.14-26.20), tau2=0.764 | 2.943 | stale card text (Vaduganathan/Jhund SGLT2i placeholder bled into unrelated review) |
| ALK_NSCLC_REVIEW | 4 | [i] HR 0.49 (0.38-0.64), k=1 | OR 0.34 (0.24-0.48), tau2=0.064 | 0.365 | scale-mismatch (HR vs OR); k differs (1->4) |
| ALOPECIA_JAKI_REVIEW | 5 | [i] RR 8.50 (4.50-16.00), k=2 | OR 21.43 (10.48-43.82), tau2=0.218 | 0.925 | scale-mismatch (RR vs OR); k differs (2->5) |
| ALS_NEW_AGENTS_NMA_REVIEW | 10 | [i] HR 0.77 (0.72-0.82), k=5 | OR 1.28 (0.94-1.75), tau2=0.145 | 0.508 | stale card text (Vaduganathan/Jhund SGLT2i placeholder bled into unrelated review) |
| AML_TARGETED_NEW_REVIEW | 9 | [i] HR 0.77 (0.72-0.82), k=5 | OR 0.68 (0.48-0.97), tau2=0.213 | 0.121 | stale card text (Vaduganathan/Jhund SGLT2i placeholder bled into unrelated review) |
| AML_VEN_FLT3_NMA_REVIEW | 10 | [i] HR 0.77 (0.72-0.82), k=5 | OR 0.61 (0.42-0.89), tau2=0.300 | 0.229 | stale card text (Vaduganathan/Jhund SGLT2i placeholder bled into unrelated review) |
| ANCA_VASCULITIS_NMA_REVIEW | 10 | [i] HR 0.77 (0.72-0.82), k=5 | OR 1.09 (0.62-1.93), tau2=0.678 | 0.352 | stale card text (Vaduganathan/Jhund SGLT2i placeholder bled into unrelated review) |
| ANTIFUNGAL_NEWER_RESISTANT_REVIEW | 7 | [i] HR 0.77 (0.72-0.82), k=5 | OR 2.80 (2.01-3.92), tau2=0.109 | 1.292 | stale card text (Vaduganathan/Jhund SGLT2i placeholder bled into unrelated review) |
| ANTI_CD20_MS_REVIEW | 6 | [i] RR 0.53 (0.40-0.71), k=2 | OR 0.42 (0.36-0.49), tau2=0.004 | 0.233 | scale-mismatch (RR vs OR); k differs (2->6) |
| ANTI_PD1_GASTRIC_REVIEW | 10 | [i] HR 0.77 (0.72-0.82), k=5 | OR 0.70 (0.64-0.77), tau2=0.000 | 0.096 | stale card text (Vaduganathan/Jhund SGLT2i placeholder bled into unrelated review) |
| ANTI_PDL1_BLADDER_REVIEW | 9 | [i] HR 0.77 (0.72-0.82), k=5 | OR 0.67 (0.55-0.81), tau2=0.065 | 0.145 | stale card text (Vaduganathan/Jhund SGLT2i placeholder bled into unrelated review) |
| ANTI_TIGIT_TUMORS_REVIEW | 11 | [i] HR 0.77 (0.72-0.82), k=5 | OR 0.68 (0.60-0.77), tau2=0.000 | 0.126 | stale card text (Vaduganathan/Jhund SGLT2i placeholder bled into unrelated review) |
| ARDS_PRONE_POSITIONING_REVIEW | 9 | [i] HR 0.77 (0.72-0.82), k=5 | OR 0.65 (0.57-0.74), tau2=0.000 | 0.175 | stale card text (Vaduganathan/Jhund SGLT2i placeholder bled into unrelated review) |
| ARNI_HF_REVIEW | 3 | [i] HR 0.80 (0.73-0.87), k=1 | OR 0.85 (0.76-0.96), tau2=0.006 | 0.062 | converge |
| ARPI_NMCRPC_REVIEW | 3 | [i] HR 0.67 (0.61-0.74), k=6 | OR 0.36 (0.28-0.47), tau2=0.038 | 0.608 | scale-mismatch (HR vs OR); k differs (6->3) |
| ARPI_mHSPC_REVIEW | 5 | [i] HR 0.67 (0.61-0.74), k=6 | OR 0.62 (0.55-0.69), tau2=0.000 | 0.085 | converge |
| ATOPIC_DERM_NMA_REVIEW | 7 | [i] RR 3.30 (2.90-3.80), k=97 | OR 5.38 (3.41-8.48), tau2=0.306 | 0.488 | scale-mismatch (RR vs OR); k differs (97->7) |
| ATTR_CM_REVIEW | 4 | [i] RR 0.72 (0.58-0.88), k=4 | OR 0.64 (0.51-0.79), tau2=0.000 | 0.124 | scale-mismatch (RR vs OR) |
| AXSPA_BIOLOGICS_REVIEW | 10 | [i] HR 0.77 (0.72-0.82), k=5 | OR 3.47 (2.68-4.49), tau2=0.073 | 1.506 | stale card text (Vaduganathan/Jhund SGLT2i placeholder bled into unrelated review) |
| AZITHROMYCIN_CHILD_MORTALITY_REVIEW | 3 | [i] RR 0.25 (0.13-0.46), k=1 | OR 0.86 (0.82-0.89), tau2=0.000 | 1.232 | scale-mismatch (RR vs OR); k differs (1->3) |
| BARIATRIC_RYGB_VS_SG_REVIEW | 10 | [i] HR 0.77 (0.72-0.82), k=5 | OR 2.30 (1.42-3.74), tau2=0.439 | 1.095 | stale card text (Vaduganathan/Jhund SGLT2i placeholder bled into unrelated review) |
| BELIMUMAB_SLE_REVIEW | 4 | [i] OR 1.55 (1.22-1.98), k=2 | OR 1.63 (1.37-1.95), tau2=0.000 | 0.053 | converge |
| BEMPEDOIC_ACID_REVIEW | 4 | [i] HR 0.87 (0.79-0.96), k=1 | OR 1.15 (0.79-1.66), tau2=0.079 | 0.276 | scale-mismatch (HR vs OR); k differs (1->4) |

## Summary
- Converging (|dlog| <= 0.10): **5 / 30**
- Diverging on real claim (|dlog| > 0.10, non-placeholder): **10 / 30**
- Inline-placeholder bleed (Vaduganathan/Jhund SGLT2i in unrelated review): **15 / 30**
- Ambiguous (no-claim / repool-failed): **0 / 30**

## Highlighted cases (top |dlog|, excluding placeholder bleed)
- **AZITHROMYCIN_CHILD_MORTALITY_REVIEW** -- claim RR 0.25 (0.13-0.46, k=1); our OR 0.86 (0.82-0.89, k=3, tau2=0.000); |dlog|=1.232; cause: scale-mismatch (RR vs OR); k differs (1->3).
- **ALOPECIA_JAKI_REVIEW** -- claim RR 8.50 (4.50-16.00, k=2); our OR 21.43 (10.48-43.82, k=5, tau2=0.218); |dlog|=0.925; cause: scale-mismatch (RR vs OR); k differs (2->5).
- **ARPI_NMCRPC_REVIEW** -- claim HR 0.67 (0.61-0.74, k=6); our OR 0.36 (0.28-0.47, k=3, tau2=0.038); |dlog|=0.608; cause: scale-mismatch (HR vs OR); k differs (6->3).
- **ATOPIC_DERM_NMA_REVIEW** -- claim RR 3.30 (2.90-3.80, k=97); our OR 5.38 (3.41-8.48, k=7, tau2=0.306); |dlog|=0.488; cause: scale-mismatch (RR vs OR); k differs (97->7).
- **ADC_HER2_NMA_REVIEW** -- claim HR 0.28 (0.22-0.37, k=1); our OR 0.41 (0.21-0.80, k=4, tau2=0.335); |dlog|=0.374; cause: scale-mismatch (HR vs OR); k differs (1->4).
