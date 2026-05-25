---
title: "RapidMeta Precision v12.0"
slug: olokizumab_ra
version: 1.1
date: 2026-04-20
registration: post-hoc
registration_note: |
  Auto-generated post-hoc from AACT-verified extraction; NOT a
  pre-registered PROSPERO/OSF protocol. Use the per-topic curated
  *_REVIEW.html when one exists for analyses requiring formal
  pre-registration.
canonical_url: https://mahmood726-cyber.github.io/rapidmeta-finerenone/protocols/olokizumab_ra_auto_protocol_v1.1_2026-04-20.md
app_url: https://mahmood726-cyber.github.io/rapidmeta-finerenone/OLOKIZUMAB_RA_AUTO_FULL_REVIEW.html
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

**Population.** Adults randomised in trials registered on ClinicalTrials.gov for Rheumatoid Arthritis

**Intervention.** Olokizumab (AACT-verified intervention name)

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

## 3. Included trials (k = 3)

| NCT | Name | Year | Primary outcome (AACT) | PMID |
|-----|------|------|------------------------|------|
| [NCT02760368](https://clinicaltrials.gov/study/NCT02760368) | CREDO 1 | 2022 | Percentage of Subjects Achieving American College of Rheumatology 20% (ACR20) Re | [34344706](https://pubmed.ncbi.nlm.nih.gov/34344706/) |
| [NCT02760407](https://clinicaltrials.gov/study/NCT02760407) | CREDO 2 | 2022 | Percentage of Subjects Achieving American College of Rheumatology 20% (ACR20) Re | [36001712](https://pubmed.ncbi.nlm.nih.gov/36001712/) |
| [NCT02760433](https://clinicaltrials.gov/study/NCT02760433) | CREDO 3 | 2022 | Percentage of Subjects Achieving American College of Rheumatology 20% (ACR20) Re | [36109142](https://pubmed.ncbi.nlm.nih.gov/36109142/) |

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
