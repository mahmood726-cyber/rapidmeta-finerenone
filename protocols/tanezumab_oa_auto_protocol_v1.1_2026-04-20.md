---
title: "RapidMeta Precision v12.0"
slug: tanezumab_oa
version: 1.1
date: 2026-04-20
registration: post-hoc
registration_note: |
  Auto-generated post-hoc from AACT-verified extraction; NOT a
  pre-registered PROSPERO/OSF protocol. Use the per-topic curated
  *_REVIEW.html when one exists for analyses requiring formal
  pre-registration.
canonical_url: https://mahmood726-cyber.github.io/rapidmeta-finerenone/protocols/tanezumab_oa_auto_protocol_v1.1_2026-04-20.md
app_url: https://mahmood726-cyber.github.io/rapidmeta-finerenone/TANEZUMAB_OA_AUTO_FULL_REVIEW.html
license: MIT
---

# RapidMeta Precision v12.0
## Auto-generated Protocol (post-hoc, AACT-verified extraction)

> **Notice — Auto-generated.** This protocol was rendered from the live
> interactive review at the App URL above using the structured PICO and
> trial data extracted from AACT 2026-04-12 + AACT-verified primary
> publications. It is **not** a pre-registered PROSPERO/OSF protocol.
> Authors targeting journals that require a PROSPERO number should
> register the protocol before the first formal update cycle.

---

## 1. PICO

**Population.** Adults randomised in trials registered on ClinicalTrials.gov for Osteoarthritis

**Intervention.** Tanezumab (AACT-verified intervention name)

**Comparator.** Active comparator or placebo as registered on AACT

**Outcome.** Trial-declared primary outcome (AACT design_outcomes); event counts from AACT outcome_measurements

**Subgroups.** Subgroup analyses per parent trial protocol

---

## 2. Eligibility (6-gate audit, applied at extraction time)

1. **GATE-A.** NCT exists in AACT 2026-04-12 snapshot.
2. **GATE-B.** Drug pattern present in AACT `interventions` for the NCT.
3. **GATE-C.** Condition pattern present in AACT `conditions`.
4. **GATE-D.** Primary PMID's PubMed title or abstract mentions the drug
   or condition.
5. **GATE-E.** AACT `baseline_counts` reports ≥2 per-arm participant rows.
6. **GATE-F.** AACT `design_outcomes` declares a primary outcome with
   measure text.

Trials below all passed all 6 gates.

---

## 3. Included trials (k = 7)

| NCT | Name | Year | Primary outcome (AACT) | PMID |
|-----|------|------|------------------------|------|
| [NCT02528188](https://clinicaltrials.gov/study/NCT02528188) | NCT02528188 | 2024 | Percentage of Participants With Adjudicated Primary Composite Joint Safety Outco | [33538113](https://pubmed.ncbi.nlm.nih.gov/33538113/) |
| [NCT00864097](https://clinicaltrials.gov/study/NCT00864097) | NCT00864097 | 2019 | Change From Baseline in Western Ontario and McMaster Universities Osteoarthritis | [23852695](https://pubmed.ncbi.nlm.nih.gov/23852695/) |
| [NCT00744471](https://clinicaltrials.gov/study/NCT00744471) | NCT00744471 | 2023 | Change From Baseline in Western Ontario and McMaster Universities Osteoarthritis | [23553790](https://pubmed.ncbi.nlm.nih.gov/23553790/) |
| [NCT00809354](https://clinicaltrials.gov/study/NCT00809354) | NCT00809354 | 2019 | Change From Baseline in the Western Ontario and McMaster Universities Osteoarthr | [24625625](https://pubmed.ncbi.nlm.nih.gov/24625625/) |
| [NCT00863304](https://clinicaltrials.gov/study/NCT00863304) | NCT00863304 | 2023 | Change From Baseline in Western Ontario and McMaster Universities Osteoarthritis | [25274899](https://pubmed.ncbi.nlm.nih.gov/25274899/) |
| [NCT00809783](https://clinicaltrials.gov/study/NCT00809783) | NCT00809783 | 2016 | Number of Participants With Treatment Emergent Adverse Events (AEs) And Serious  | [26554876](https://pubmed.ncbi.nlm.nih.gov/26554876/) |
| [NCT00985621](https://clinicaltrials.gov/study/NCT00985621) | NCT00985621 | 2023 | Change From Baseline in Western Ontario and McMaster Universities Osteoarthritis | [23707270](https://pubmed.ncbi.nlm.nih.gov/23707270/) |

---

## 4. Statistical methods

Pre-specified pooling = inverse-variance random-effects DerSimonian–Laird
τ², with Hartung–Knapp–Sidik–Jonkman (HKSJ) variance correction and
t<sub>k-1</sub> critical value (Cochrane Handbook v6.5). Effect scale is
the trial-published metric (HR / OR / RR / MD) when available from AACT
`outcome_analyses`, else an inverse-variance OR computed from AACT event
counts via the Woolf estimator.

Sensitivity analyses: leave-one-out, Baujat, cumulative MA, Bayesian
posterior with weakly-informative prior μ ~ N(0, 1.0²) on the log scale,
trim-and-fill, Egger/Peters publication-bias tests (k ≥ 3), prediction
interval at α = 0.10 (Cochrane v6.5 t<sub>k-1</sub>), Trial Sequential
Analysis with O'Brien–Fleming alpha-spending. See the live app for the
full 28-panel statistics tab.

---

## 5. Risk of bias

RoB-2 per trial is derived from AACT `designs` allocation + masking +
outcomes_assessor_masked fields (D1 randomization, D2 deviations, D4
measurement). D3 (missing data) and D5 (selective reporting) default to
`some-concerns` because the registry cannot judge them. Each trial card
ships a `robSource:` attribution string listing the exact AACT inputs.

---

## 6. Provenance & reproducibility

- **AACT snapshot:** 2026-04-12 (Clinical Trials Transformation Initiative)
- **PubMed bridge:** NCBI E-utilities + idconv API
- **Repo:** https://github.com/mahmood726-cyber/rapidmeta-finerenone
- **Scripts:** `scripts/bulk_clone_audit_first.py` (initial build),
  `scripts/build_aact_pmid_and_design_maps.py` (PMID/RoB enrichment),
  `scripts/build_aact_counts_with_param_type.py` (count extraction),
  `scripts/build_aact_continuous.py` (continuous-outcome effects).
