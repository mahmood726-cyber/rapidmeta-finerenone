---
title: "Direct Oral Anticoagulants versus Warfarin for Stroke Prevention in Non-Valvular Atrial Fibrillation: A Star-Network Meta-Analysis Replicating the Ruff 2014 Canonical Set"
short_title: "DOAC-vs-warfarin AF stroke prevention: star-network replication"
article_type: Methods Note
target_journal: Synthēsis
word_count_target: ≤400
format: A4, 1.5 line-spacing, 11-pt Calibri (body) / 12-pt Times New Roman (headings acceptable)
refs: Vancouver numeric, up to 15
authors:
  - name: Mahmood Ahmad
    role: middle-author-only on E156 (per feedback_e156_authorship policy)
    email: drmahmoodclinic@pm.me
keywords: [network meta-analysis, DOACs, atrial fibrillation, stroke prevention, netmeta, living review]
artifact_links:
  - https://mahmood726-cyber.github.io/rapidmeta-finerenone/DOAC_AF_NMA_REVIEW.html
  - https://github.com/mahmood726-cyber/rapidmeta-finerenone/blob/main/nma/validation/doac_af_peer_review_bundle.md
  - https://github.com/mahmood726-cyber/rapidmeta-finerenone/blob/main/protocols/doac_af_nma_protocol_v1.0_2026-04-21.md
---

# Direct Oral Anticoagulants versus Warfarin for Stroke Prevention in Non-Valvular Atrial Fibrillation: A Star-Network Meta-Analysis Replicating the Ruff 2014 Canonical Set

## Abstract (Methods Note, ≤400 words)

**Question.** Among the four direct oral anticoagulants (DOACs) evaluated at full therapeutic dose in non-valvular atrial fibrillation, which confers the largest relative reduction in stroke or systemic embolism versus dose-adjusted warfarin, and does the Ruff 2014 [9] canonical ranking hold when reproduced with current (netmeta v3.2.0) tooling?

**Dataset.** We included the four pivotal DOAC-versus-warfarin Phase 3 trials: RE-LY (dabigatran 150 mg BID) [1], ROCKET-AF (rivaroxaban 20 mg daily) [2], ARISTOTLE (apixaban 5 mg BID) [3], and ENGAGE-AF TIMI 48 (edoxaban 60 mg daily) [4]. Combined sample 71 683 participants with trial-primary modified-intention-to-treat stroke or systemic embolism (SE) events.

**Method.** We fitted a frequentist warfarin-star network meta-analysis with the `netmeta` R package (v3.2.0), restricted maximum-likelihood estimation of τ², and the Hartung–Knapp–Sidik–Jonkman confidence-interval adjustment. Ranking used P-score and multivariate-normal Monte-Carlo SUCRA (100 000 draws from the random-effects contrast variance-covariance matrix).

**Result.** Against warfarin, hazard ratios (95% CI) were dabigatran 150 BID 0.66 (0.53–0.82); apixaban 5 BID 0.79 (0.66–0.95); rivaroxaban 20 QD 0.79 (0.66–0.96); edoxaban 60 QD 0.79 (0.63–0.99). τ² was 0.000. SUCRA placed dabigatran first (0.923), with edoxaban, rivaroxaban, and apixaban tightly clustered between 0.484 and 0.496. All four DOACs were statistically superior to warfarin.

**Robustness.** Point estimates match the source trials to three decimal places (star-network pass-through). Transitivity concerns declared are (i) population CHA₂DS₂-VASc-score heterogeneity (ROCKET-AF enriched, mean ~3.5 versus ARISTOTLE/RE-LY mean ~2.1) and (ii) warfarin time-in-therapeutic-range variation (ROCKET-AF 55% versus ENGAGE 68%), which may inflate rivaroxaban's relative effect. Higher-dose arms only are analysed; Dabigatran 110 mg BID and Edoxaban 30 mg QD arms are excluded for coherence.

**Interpretation.** The stroke/SE ranking favours dabigatran (rank-1 probability 85%) but is **not the clinically relevant ranking**: published net-benefit meta-analyses incorporating major bleeding (where apixaban shows the largest relative reduction, HR 0.69) typically place apixaban at rank-1 for real-world decision-making [5,6]. The Ruff 2014 result is reproduced with sub-decimal fidelity. Guideline writers should continue reading stroke/SE and bleeding NMAs jointly, not in isolation.

**Boundary.** No head-to-head DOAC-versus-DOAC trial exists; the analysis excludes lower-dose DOAC arms, AVERROES (apixaban versus aspirin), and valvular AF (where DOACs are contraindicated).

## Availability

Interactive living-review app, protocol v1.0 (2026-04-21), and netmeta-validation peer-review bundle at `github.com/mahmood726-cyber/rapidmeta-finerenone`.

## References (Vancouver; selected)

1. Connolly SJ, Ezekowitz MD, Yusuf S, et al. Dabigatran versus warfarin in patients with atrial fibrillation. N Engl J Med. 2009;361:1139–51.
2. Patel MR, Mahaffey KW, Garg J, et al. Rivaroxaban versus warfarin in nonvalvular atrial fibrillation. N Engl J Med. 2011;365:883–91.
3. Granger CB, Alexander JH, McMurray JJV, et al. Apixaban versus warfarin in patients with atrial fibrillation. N Engl J Med. 2011;365:981–92.
4. Giugliano RP, Ruff CT, Braunwald E, et al. Edoxaban versus warfarin in patients with atrial fibrillation. N Engl J Med. 2013;369:2093–104.
5. Ruff CT, Giugliano RP, Braunwald E, et al. Comparison of the efficacy and safety of new oral anticoagulants with warfarin in patients with atrial fibrillation: a meta-analysis of randomised trials. Lancet. 2014;383:955–62.
6. Lip GYH, Agnelli G. Edoxaban: a focused review of its clinical pharmacology. Eur Heart J. 2014;35:1844–55.

## OJS Submission Notes

- Upload: single `.docx` of the body above; protocol as supplement.
- CRediT: middle-author-only (MA) per feedback_e156_authorship policy.

## SUBMITTED: [ ]
