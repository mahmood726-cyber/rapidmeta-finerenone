# mpMRI (PI-RADS) for Clinically Significant Prostate Cancer — DTA Extraction Audit

- **Build date:** 2026-04-28
- **Engine:** RapidMeta DTA engine v1.0.0 (rapidmeta-dta-engine-v1.js, shared with the GeneXpert MTB/RIF Ultra and SARS-CoV-2 rapid antigen reviews)
- **Index test:** Multiparametric MRI of the prostate, scored with PI-RADS v2 / v2.1
- **Reference standard:** Targeted biopsy (MRI-fusion or cognitive) ± systematic biopsy, OR template-prostate-mapping (TPM) biopsy, OR radical-prostatectomy histology in the cancer-positive subset
- **Target condition:** Clinically significant prostate cancer (csPCa) — ISUP grade group ≥2 / Gleason ≥3+4 in most studies; Gleason ≥4+3 / ISUP ≥3 in PROMIS

## Acceptance gate result

| Tier | Gate | Outcome |
| --- | --- | --- |
| Biopsy-naïve, PI-RADS ≥3 (default headline) | k ≥ 3 | **k = 3** ✓ (PROMIS + MRI-FIRST + PRIMARY) |
| Mixed biopsy-history (all primary) | k ≥ 5 | **k = 5** ✓ |
| Combined all-tier (with sensitivity tier) | k ≥ 8 | k = 6 — **coverage warning** |

## Per-study extraction & back-compute

### 1. PROMIS — Ahmed 2017 (Lancet)
- PMID 28110982 · DOI [10.1016/S0140-6736(16)32401-1](https://doi.org/10.1016/S0140-6736(16)32401-1) · NCT01292291
- **Design:** UK multicentre paired-cohort, biopsy-naïve, TPM-biopsy reference standard
- **Population:** Men with PSA ≤15 ng/mL and no previous biopsy (N=576 with all 3 tests)
- **csPCa definition:** Gleason ≥4+3 OR maximum cancer core length ≥6 mm (more stringent than ISUP ≥2 used elsewhere)
- **Reported numbers:** csPCa in 230/576 (40%); MP-MRI Sens **93%** (88-96%), Spec **41%** (36-46%)
- **Back-compute:**
  - n+ = 230, n− = 576 − 230 = 346
  - TP = round(0.93 × 230) = 213.9 → **214**; FN = 230 − 214 = **16**
  - TN = round(0.41 × 346) = 141.86 → **142**; FP = 346 − 142 = **204**
  - Sanity: TP+FP+FN+TN = 214 + 204 + 16 + 142 = 576 ✓
- **Caveats logged:** (a) more stringent csPCa definition than other primaries — flagged on Subgroups (csPCa_definition axis); (b) TPM reference is gold-standard, no verification bias.

### 2. MRI-FIRST — Rouvière 2019 (Lancet Oncol)
- PMID 30470502 · DOI [10.1016/S1470-2045(18)30569-2](https://doi.org/10.1016/S1470-2045(18)30569-2) · NCT02485379
- **Design:** France 16-centre prospective paired diagnostic study, biopsy-naïve
- **Population:** N=251 analysed (275 enrolled, 24 excluded); PSA ≤20 ng/mL, T2c or lower
- **Reference standard:** Combined targeted + systematic biopsy with central pathology review
- **Reported numbers:** csPCa-A (ISUP ≥2) in 94/251 (37%); 53 (21%) had negative MRI (Likert ≤2); 13 of 94 csPCa+ patients were MRI-negative (detected by systematic biopsy only)
- **Back-compute:**
  - n+ = 94, n− = 157
  - FN (MRI− ∩ csPCa+) = **13** (explicitly stated)
  - TP = 94 − 13 = **81**
  - TN (MRI− ∩ csPCa−) = 53 − 13 = **40**
  - FP (MRI+ ∩ csPCa−) = 198 − 81 = **117**
  - Sanity: 81+117+13+40 = 251 ✓
  - Implied Sens = 81/94 = 86.2%; Spec = 40/157 = 25.5%
- **Caveats logged:** (a) Likert score not strict PI-RADS v2 in 2018; (b) MRI-negative patients received systematic biopsy only — partial verification; (c) low specificity reflects high MRI-positive rate at Likert ≥3 trigger.

### 3. PRIMARY (MRI-alone arm) — Emmett 2021 (Eur Urol)
- PMID 34465492 · DOI [10.1016/j.eururo.2021.08.002](https://doi.org/10.1016/j.eururo.2021.08.002)
- **Design:** Australia phase II prospective multicentre, biopsy-naïve
- **Population:** N=291, csPCa = 162 (56%)
- **Reference standard:** Systematic ± targeted biopsy
- **Reported numbers:** MRI-alone Sens **83%**, Spec **53%** (combined PSMA+MRI Sens 97%, Spec 40% — not used)
- **Back-compute:**
  - n+ = 162, n− = 129
  - TP = round(0.83 × 162) = 134.46 → **134**; FN = 162 − 134 = **28**
  - TN = round(0.53 × 129) = 68.37 → **68**; FP = 129 − 68 = **61**
  - Sanity: 134+61+28+68 = 291 ✓
- **Caveats logged:** (a) MRI arm extracted from within-patient PSMA-vs-MRI comparison; (b) PI-RADS v2 not v2.1.

### 4. Bao 2020 (J Magn Reson Imaging)
- PMID 33075177 · DOI [10.1002/jmri.27394](https://doi.org/10.1002/jmri.27394)
- **Design:** China 2-centre STARD-compliant retrospective, mixed biopsy-history
- **Population:** N=638 (346 + 292); ground truth from biopsy and/or prostatectomy histology
- **Reported numbers (senior radiologist arm):** Mp-MRI Sens **92.3% [265/287]**, Spec **67.8% [238/351]** — **direct counts given** in abstract
- **Direct extraction (no back-compute):**
  - TP = **265**, FN = 287 − 265 = **22**
  - TN = **238**, FP = 351 − 238 = **113**
  - Sanity: 265+113+22+238 = 638 ✓
- **Caveats logged:** retrospective design; senior-radiologist arm extracted (junior arm available as a sensitivity check).

### 5. PI-CAI radiologists — Saha 2024 (Lancet Oncol)
- PMID 38876123 · DOI [10.1016/S1470-2045(24)00220-1](https://doi.org/10.1016/S1470-2045(24)00220-1) · NCT05489341
- **Design:** International multireader paired study, retrospective testing cohort
- **Population:** 1000 testing cases (from 10,207 total cohort); PI-RADS v2.1
- **Reference standard:** Histopathology + ≥3 years follow-up
- **Reported numbers:** Radiology readings during multidisciplinary practice — Sens **96.1%** (94.0-98.2), Spec **69.0%** (65.5-72.5) at the PI-RADS ≥3 operating point. Full cohort csPCa prevalence = 2440/10207 = **23.9%**.
- **Back-compute (with prevalence inferred from full cohort):**
  - Assumed n+ in 1000-case test split ≈ 0.239 × 1000 = 240, n− ≈ 760
  - TP = round(0.961 × 240) = 230.64 → **231**; FN = 240 − 231 = **9**
  - TN = round(0.69 × 760) = 524.4 → **524**; FP = 760 − 524 = **236**
  - Sanity: 231+236+9+524 = 1000 ✓
- **Caveats logged:** (a) **n+ inferred from full-cohort prevalence** (not directly stated for 1000-case split — the most uncertain back-compute in the dataset); (b) reference standard includes ≥3y clinical follow-up plus histology — composite design.

### 6. Metser 2021 — sensitivity tier (Eur J Nucl Med Mol Imaging)
- PMID 33846845 · DOI [10.1007/s00259-021-05355-7](https://doi.org/10.1007/s00259-021-05355-7) · NCT03149861
- **Design:** Canada single-centre prospective, prior-negative-biopsy or focal-therapy candidates
- **Population:** N=55 patients, 114 lesions; csPCa in 49/114 lesions (43%)
- **Reference standard:** PET/MR-ultrasound fusion biopsy of all suspicious lesions
- **Reported numbers (mpMR arm, lesion-level):** Sens **67%**, Spec **85%**
- **Back-compute (lesion-level):**
  - n_pos lesions = 49, n_neg lesions = 65
  - TP = round(0.67 × 49) = 32.83 → **33**; FN = 49 − 33 = **16**
  - TN = round(0.85 × 65) = 55.25 → **55**; FP = 65 − 55 = **10**
  - Sanity: 33+10+16+55 = 114 ✓
- **Caveats logged:** **lesion-level not patient-level** — within-patient clustering not modelled; small N; placed in sensitivity tier with explicit data_caveats flag.

## Excluded studies (with rationale)

| Study | PMID | Reason for exclusion |
| --- | --- | --- |
| PRECISION (Kasivisvanathan 2018) | 29552975 | Detection-rate paired-RCT design — abstract gives proportion-detected but not Sens/Spec for csPCa against a single composite reference. |
| Maxeiner 2018 (BJU Int) | 29569320 | Only PI-RADS ≥3 men underwent biopsy → no MRI-negative denominator → Spec unobtainable. |
| VISIONING (Wetterauer 2024) | 38402105 | Opportunistic screening with discordant reference (template biopsy only on suspicious DRE/PSA in negative-bpMRI patients). |
| Oerther 2024 systematic review | 39136561 | Meta-analysis pooling primary studies; cited as benchmark in Discussion. Pooled csPCa Sens 96% / Spec 43% at PI-RADS ≥3 (k=70 studies, n=13,330). |
| Mahajan 2022 (J Cancer Res Ther) | 36412424 | Very small N=36; bp-MRI vs mp-MRI within-patient; Spec denominator not given. |

## Heterogeneity axes (exposed in Subgroups tab)

- `prior_biopsy_history`: biopsy_naive (PROMIS, MRI-FIRST, PRIMARY) vs prior_negative (Metser) vs mixed (Bao, PI-CAI)
- `pirads_threshold`: ge3 (all) vs ge4 (none in current dataset; placeholder for v1.1)
- `reference_standard_specific`: TPM_biopsy (PROMIS) vs targeted_plus_systematic (MRI-FIRST, PRIMARY) vs biopsy_or_prostatectomy_histology (Bao) vs histology_plus_3y_followup (PI-CAI) vs PET_MR_ultrasound_fusion_biopsy (Metser)
- `csPCa_definition`: Gleason ≥4+3 / ISUP ≥3 (PROMIS) vs Gleason ≥3+4 / ISUP ≥2 (all others) — **structural heterogeneity axis** — drives PROMIS Sens/Spec divergence

## Honest flags surfaced in the headline

- **PROMIS Spec = 41% drives the headline number low** — PROMIS uses both a more stringent csPCa definition (Gleason ≥4+3) and a TPM-biopsy gold-standard reference, both of which inflate the denominator of MRI-positive non-csPCa cases. This is the largest single-study influence in the leave-one-out — flagged in the engine output and in the Discussion.
- **Cross-study Spec range is wide: 26% (MRI-FIRST) to 85% (Metser lesion-level)** — driven by reference-standard heterogeneity, csPCa-definition stringency, and lesion-level vs patient-level analysis. Subgroup analyses by reference_standard_specific quantify the spread.
- **PI-CAI n+ inferred from full-cohort prevalence**, not directly stated for the 1000-case test split. Most uncertain back-compute in the dataset; sensitivity-analysis re-includes the row with the prevalence pinned to 30% as an alternative — does not change the headline.
- **Combined tier k=6 falls below the spec-defined k≥8 ceiling** — coverage banner surfaces; consistent with methods-paper framing.

## Engine cross-validation

The shared `rapidmeta-dta-engine-v1.js` was cross-validated against R `mada::reitsma` 7/7 EXACT on the GeneXpert Ultra fixtures (`r_validation_log.json`). On-demand WebR validation is wired via the "Validate pool with R (mada)" button on the Methods tab; a topic-specific `r_validation_log_mpmri_prostate.json` is planned for v1.1.

## Next planned search

2026-07-28 (3 months). PROSPERO registration deferred to v1.1; canonical evidence base for clinical inference is the Oerther 2024 *Radiology* systematic review (k=70, n=13,330) and the EAU 2024 guideline.
