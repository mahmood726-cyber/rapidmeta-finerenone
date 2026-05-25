---
title: "RapidMeta Precision v12.0"
slug: brexpiprazole_agitation
version: 1.1
date: 2026-04-20
registration: post-hoc
registration_note: |
  Auto-generated post-hoc from AACT-verified extraction; NOT a
  pre-registered PROSPERO/OSF protocol. Use the per-topic curated
  *_REVIEW.html when one exists for analyses requiring formal
  pre-registration.
canonical_url: https://mahmood726-cyber.github.io/rapidmeta-finerenone/protocols/brexpiprazole_agitation_auto_protocol_v1.1_2026-04-20.md
app_url: https://mahmood726-cyber.github.io/rapidmeta-finerenone/BREXPIPRAZOLE_AGITATION_AUTO_FULL_REVIEW.html
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

**Population.** Adults randomised in trials registered on ClinicalTrials.gov for Alzheimer

**Intervention.** Brexpiprazole (AACT-verified intervention name)

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

## 3. Included trials (k = 6)

| NCT | Name | Year | Primary outcome (AACT) | PMID |
|-----|------|------|------------------------|------|
| [NCT03594123](https://clinicaltrials.gov/study/NCT03594123) | NCT03594123 | 2025 | Percentage of Participants With Treatment-emergent Adverse Events (TEAEs) by Sev | [39534972](https://pubmed.ncbi.nlm.nih.gov/39534972/) |
| [NCT03620981](https://clinicaltrials.gov/study/NCT03620981) | NCT03620981 | 2025 | Change From Baseline in Cohen-Manfield Agitation Inventory(CMAI) Score at 10 Wee | [40717666](https://pubmed.ncbi.nlm.nih.gov/40717666/) |
| [NCT03548584](https://clinicaltrials.gov/study/NCT03548584) | NCT03548584 | 2026 | Change From Baseline to Week 12 in the CMAI Total Score (primary) | [37930669](https://pubmed.ncbi.nlm.nih.gov/37930669/) |
| [NCT01922258](https://clinicaltrials.gov/study/NCT01922258) | NCT01922258 | 2026 | Change From Baseline to Week 12/Early Termination in the Cohen-Mansfield Agitati | [31708380](https://pubmed.ncbi.nlm.nih.gov/31708380/) |
| [NCT03724942](https://clinicaltrials.gov/study/NCT03724942) | NCT03724942 | 2025 | The Frequency of Subjects With Treatment-Emergent Adverse Events (TEAEs) (primar | [40290781](https://pubmed.ncbi.nlm.nih.gov/40290781/) |
| [NCT01862640](https://clinicaltrials.gov/study/NCT01862640) | NCT01862640 | 2026 | Change From Baseline In The Cohen-Mansfield Agitation Inventory (CMAI) Total Sco | [31708380](https://pubmed.ncbi.nlm.nih.gov/31708380/) |

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
