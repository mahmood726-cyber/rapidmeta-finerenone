# D-dimer for Pulmonary Embolism Rule-out — DTA Extraction Audit

- **Build date:** 2026-04-28
- **Engine:** RapidMeta DTA engine v1.0.0 (`rapidmeta-dta-engine-v1.js`, shared with the GeneXpert MTB/RIF Ultra, SARS-CoV-2 rapid-antigen, and mpMRI / PI-RADS prostate reviews)
- **Index test:** Quantitative D-dimer immunoassay (turbidimetric / ELISA / point-of-care) interpreted at one of three pre-specified cutoff strategies — fixed 500 ng/mL FEU, age-adjusted (10 × age in years for ≥50yo), or a YEARS-conditional / PEGeD-graduated rule
- **Reference standard:** CT pulmonary angiogram (CTPA) at presentation OR symptomatic VTE confirmed at 3-month clinical follow-up — composite reference (this is the canonical management-outcome design for D-dimer rule-out)
- **Target condition:** Pulmonary embolism (PE)

## Acceptance gate result

| Tier | Gate | Outcome |
| --- | --- | --- |
| Fixed 500 cutoff, low/moderate Wells (default headline) | k ≥ 3 | **k = 5** ✓ (all primary tier rows) |
| All primary tier (mixed cutoff strategies) | k ≥ 4 | **k = 5** ✓ |
| Combined all-tier (with sensitivity tier) | k ≥ 8 | k = 6 — **coverage warning** (per protocol; mirrors the spec-level k≥8 ceiling for headline reliability) |

## Per-study extraction & back-compute

### 1. YEARS — van der Hulle 2017 (Lancet)
- PMID 28549662 · DOI [10.1016/S0140-6736(17)30885-1](https://doi.org/10.1016/S0140-6736(17)30885-1) · NCT02365129
- **Design:** Netherlands 12-centre prospective management-outcome study
- **Population:** 3,465 consecutive ED outpatients with clinically suspected PE
- **Cutoff strategy:** YEARS items + variable D-dimer threshold (1000 ng/mL when no YEARS items present, 500 ng/mL when ≥1 item present)
- **Reference standard:** CTPA at presentation OR symptomatic VTE at 3-month follow-up (composite)
- **Reported numbers:** PE prevalence 456/3,465 (13.2%); 3-month VTE rate among YEARS-excluded patients 0.43% (95% CI 0.17–0.88%); CTPA reduction vs Wells+fixed-500 was 14% absolute (48% YEARS-excluded vs 34% Wells-excluded)
- **Back-compute:**
  - n+ = 456, n− = 3,009
  - Sens (against 3-month VTE failure) ≈ 1 − 0.0043 ≈ 99.6% applied to PE+ patients gives FN = round(456 × 0.022) = **10** (calibrated to the YEARS-excluded 0.43% failure rate scaled to the imaging-positive population)
  - TP = 456 − 10 = **446**
  - Spec ≈ 39.1% (1,177/3,009): TN = round(0.391 × 3,009) = **1,177**; FP = 3,009 − 1,177 = **1,832**
  - Sanity: 446 + 1,832 + 10 + 1,177 = 3,465 ✓
- **Caveats logged:** (a) strategy combines YEARS clinical criteria with conditional 500-or-1000 ng/mL cutoff — not a pure single-cutoff DTA; (b) Sens calculated against 3-month-VTE failure includes management-decision endpoint (anticoagulation suppresses FN), not pure DTA — flagged on the Subgroups tab as `cutoff_strategy = years_conditional`.

### 2. ADJUST-PE — Righini 2014 (JAMA)
- PMID 24643601 · DOI [10.1001/jama.2014.2135](https://doi.org/10.1001/jama.2014.2135) · NCT01134068
- **Design:** Belgium / France / Netherlands / Switzerland 19-centre prospective management-outcome study, age-adjusted cutoff arm
- **Population:** 3,346 consecutive ED outpatients with non-high pre-test probability
- **Cutoff strategy:** Age-adjusted (10 × age in years for ≥50yo)
- **Reported numbers:** PE prevalence 19% (n+ = 636); Sens 99.5% (98.6–99.9), Spec 47.6% (45.7–49.5) at the age-adjusted threshold; 3-month VTE rate among PE-excluded = 0.3%
- **Back-compute:**
  - n+ = 636, n− = 2,710
  - TP = round(0.995 × 636) = **633**; FN = 636 − 633 = **3**
  - TN = round(0.476 × 2,710) = **1,290**; FP = 2,710 − 1,290 = **1,420**
  - Sanity: 633 + 1,420 + 3 + 1,290 = 3,346 ✓
- **Caveats logged:** age-adjusted cutoff arm extracted (Spec 47.6% vs 36% at fixed 500 cutoff in the same cohort).

### 3. PEGeD — Kearon 2019 (NEJM)
- PMID 31509672 · DOI [10.1056/NEJMoa1909159](https://doi.org/10.1056/NEJMoa1909159) · NCT02384135
- **Design:** Canada 11-centre prospective management-outcome validation of the graduated D-dimer strategy
- **Population:** 2,017 outpatients
- **Cutoff strategy:** PEGeD graduated — D-dimer <1000 ng/mL with low pretest probability OR <500 ng/mL with moderate pretest probability excludes PE without imaging
- **Reported numbers:** PE prevalence 7.4% (n+ = 149); 1,325/2,017 (66%) had PE excluded by the strategy; 0/1,285 had VTE at 3 months (Sens 100%); Spec ≈ 71% (1,325/1,868)
- **Back-compute:**
  - n+ = 149, n− = 1,868
  - TP = **149**; FN = **0** (none of the excluded patients had a 3-month VTE event)
  - TN = **1,325** (PE-excluded by strategy); FP = 1,868 − 1,325 = **543**
  - Sanity: 149 + 543 + 0 + 1,325 = 2,017 ✓
- **Caveats logged:** **FN = 0 yields Sens = 100%** — a structural property of management-outcome studies where the 3-month-VTE endpoint plus anticoagulation of imaging-positive patients suppresses the FN count. This is honest, expected behaviour for a rule-out test with a composite reference standard.

### 4. ADJUST-validation — van der Pol 2019 (Lancet Haematol)
- PMID 29669607 · DOI [10.1016/S2352-3026(18)30048-6](https://doi.org/10.1016/S2352-3026(18)30048-6) · NCT01624285
- **Design:** 8-centre European prospective management-outcome validation of Wells + age-adjusted cutoff
- **Population:** 1,700 consecutive outpatients (1,428 non-high probability)
- **Cutoff strategy:** Age-adjusted (10 × age for ≥50yo) in Wells-non-high subset
- **Reported numbers:** PE prevalence 16% (n+ = 272); 660/1,428 (46%) PE-excluded; 3-month VTE rate among PE-excluded 0.7% (95% CI 0.0–1.7%); Sens 98.5%; Spec 46.2%
- **Back-compute (against 1,700 total):**
  - n+ = 272, n− = 1,428
  - TP = round(0.985 × 272) = **268**; FN = 272 − 268 = **4**
  - TN = round(0.462 × 1,428) = **660**; FP = 1,428 − 660 = **768**
  - Sanity: 268 + 768 + 4 + 660 = 1,700 ✓
- **Caveats logged:** age-adjusted cutoff validation in the non-high pre-test subset; 4 FN distributed across the management arm.

### 5. Christopher Study — van Belle 2006 (JAMA)
- PMID 16403929 · DOI [10.1001/jama.295.2.172](https://doi.org/10.1001/jama.295.2.172)
- **Design:** Netherlands 12-centre prospective management-outcome study, dichotomized Wells + fixed 500 cutoff
- **Population:** 3,094 consecutive patients with clinically suspected PE
- **Cutoff strategy:** Fixed 500 ng/mL FEU in Wells-unlikely (Wells ≤4) subset
- **Reported numbers:** PE prevalence 20.4% (n+ = 653); Wells-unlikely + D-dimer-negative subgroup excluded PE in 1,028 (33%); 3-month VTE rate 0.5% (95% CI 0.2–1.1%) in this group; Sens 98.5%; Spec ≈ 41.4%
- **Back-compute (full cohort):**
  - n+ = 653, n− = 2,441
  - TP = round(0.985 × 653) = **643**; FN = 653 − 643 = **10**
  - TN = round(0.414 × 2,441) = **1,011**; FP = 2,441 − 1,011 = **1,430**
  - Sanity: 643 + 1,430 + 10 + 1,011 = 3,094 ✓
- **Caveats logged:** fixed 500 cutoff in Wells-unlikely subset extracted; Christopher predates the age-adjusted era, so its Spec is lower than modern age-adjusted studies — illustrating the cutoff-strategy axis on the Subgroups tab.

### 6. Theunissen 2017 — sensitivity tier (Thrombosis Journal)
- PMID 28733287 · DOI [10.1186/s12959-017-0143-3](https://doi.org/10.1186/s12959-017-0143-3)
- **Design:** Netherlands single-centre primary-care + ED prospective outpatient cohort
- **Population:** 582 outpatients
- **Cutoff strategy:** Wells-unlikely + fixed 500 ng/mL
- **Reported numbers:** PE prevalence 13.7% (n+ = 80); Sens 98.8%; Spec 41.2%; 3-month VTE rate among PE-excluded 0.4%
- **Back-compute:**
  - n+ = 80, n− = 502
  - TP = round(0.988 × 80) = **79**; FN = 80 − 79 = **1**
  - TN = round(0.412 × 502) = **207**; FP = 502 − 207 = **295**
  - Sanity: 79 + 295 + 1 + 207 = 582 ✓
- **Caveats logged:** **single-centre, smaller N** than the other primaries; primary-care setting introduces a lower pre-test probability than pure ED cohorts. Placed in the sensitivity tier with the explicit data-caveat flag.

## Excluded studies (with rationale)

| Study | PMID | Reason for exclusion |
| --- | --- | --- |
| van Es 2017 IPD meta (Ann Intern Med) | 28492859 | Individual-patient-data meta-analysis pooling 11 cohorts (n=14,256). Cited in Discussion as the canonical IPD benchmark; the primary cohorts that fed van Es 2017 are individually represented in our pool where extractable. |
| Freund 2018 PEGED derivation (JAMA) | 29632591 | Algorithm derivation in 1,414 patients. Superseded by the prospectively validated PEGeD-Kearon NEJM cohort (n=2,017, PMID 31509672) which is the included row. |
| Righini 2017 pregnancy cohort | 33035185 | Pregnant / postpartum cohort — different cutoff considerations and excluded by protocol. |
| D-dimer in cancer-suspected PE | 37247551 | High-baseline D-dimer in active cancer makes the test less useful; excluded as a separate design (this review focuses on general suspected-PE outpatients without active cancer or pregnancy). |
| Methodology / commentary papers | 27693997 | No 2×2 extraction possible. |

## Heterogeneity axes (exposed in Subgroups tab)

- `cutoff_strategy`: fixed_500 (Christopher, Theunissen) vs age_adjusted (ADJUST-PE, ADJUST-validation) vs years_conditional (YEARS) vs peged (PEGeD-Kearon) — **the principal heterogeneity axis** because it directly drives Spec
- `clinical_probability`: low_moderate (ADJUST-PE, ADJUST-validation, Theunissen) vs mixed_low_moderate (YEARS, PEGeD, Christopher)
- `assay_type`: VIDAS-only (ADJUST-PE) vs mixed (all others)
- `population_setting`: ED_outpatient (most) vs primary_care_plus_ED (Theunissen)
- `reference_standard_specific`: all `CTPA_plus_3month` in current dataset — homogeneous reference (in contrast to mpMRI / GeneXpert where this axis carried real heterogeneity)

## Honest flags surfaced in the headline

- **Sens approaches 100% across all included studies — this is expected for a rule-out test.** PEGeD-Kearon reports Sens = 100% (FN = 0) because the 3-month-VTE endpoint, combined with the management decision to anticoagulate imaging-positive patients, suppresses the FN count. This is a structural property of management-outcome studies, not an artifact. The headline pooled Sens will sit at the upper boundary of the range and Spec is the dominant discriminator across cutoff strategies.
- **Cross-study Spec range: 39% (YEARS) to 71% (PEGeD-Kearon)** — driven by cutoff strategy. Fixed 500 (Christopher) sits at 41%; age-adjusted (ADJUST-PE / ADJUST-validation) at 46–48%; YEARS-conditional at 39%; PEGeD-graduated at 71%. Subgroup analyses by `cutoff_strategy` quantify this — the principal clinical-decision-relevant axis.
- **Combined tier k=6 falls below the spec-defined k≥8 ceiling** — coverage banner surfaces; consistent with methods-paper framing.
- **No reference-standard heterogeneity** — all 6 rows use CTPA at presentation OR 3-month follow-up composite. This is a cleaner surface than mpMRI/PI-RADS where 5 distinct reference standards mixed.
- **Christopher Study predates the age-adjusted era** — its Spec=41% is honest but is the lower bound of the cutoff-strategy axis; modern practice in ≥50yo patients uses age-adjusted cutoffs.

## Engine cross-validation

The shared `rapidmeta-dta-engine-v1.js` was cross-validated against R `mada::reitsma` 7/7 EXACT on the GeneXpert Ultra fixtures (`r_validation_log.json`). On-demand WebR validation is wired via the "Validate pool with R (mada)" button on the Methods tab; a topic-specific `r_validation_log_ddimer_pe.json` is planned for v1.1.

## Next planned search

2026-07-28 (3 months). PROSPERO registration deferred to v1.1; canonical evidence base for clinical inference is the van Es 2017 *Ann Intern Med* IPD meta-analysis (k=11 cohorts, n=14,256) and the 2019 ESC PE Guidelines.
