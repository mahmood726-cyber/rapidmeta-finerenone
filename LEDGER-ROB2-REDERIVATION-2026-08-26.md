# Ledger: RoB 2 domain judgements re-derived, 2026-08-26

Published judgements changed, so they are recorded here rather than only in a diff.
**Nothing was written in place.** Every re-derivation sits beside the original under
`rob2_algorithm_2026_08_26`; the stored `judgement` is untouched and no reader sees the
re-derived value yet.

**Authority.** RoB 2, Revised Cochrane risk-of-bias tool for randomized trials, Higgins/Savovic/Page/Sterne (eds), RoB2 Development Group, 22 August 2019.
Tables 4 (D1), 6 (D2, effect of assignment), 10 (D3), 12 (D4), 14 (D5), 1 (overall).
The transcription is controlled by `scripts/plant_rob2_algorithm_tables.py` -- one case
per published table row plus four negative controls, 50 of 50.

**Why.** Cochrane Handbook v6.5 §8.2.3: domain judgements are Low / Some concerns /
High. "No information" is one of the five *signalling-question* responses, not a domain
judgement. This corpus used it as one 191 times.

## Counts

| | n |
|---|---|
| domains examined | 191 |
| **re-derived** | **131** |
| **UNDERIVABLE -- reported, nothing proposed** | **60** |
| results touched | 71 |
| topics touched | 22 |

### Direction

| move | n |
|---|---|
| NO_INFORMATION -> HIGH | 67 |
| NO_INFORMATION -> SOME_CONCERNS | 64 |
| **toward LOW (the flattering direction)** | **0** |

Every re-derivation moves away from Low. None flatters us. Had the direction been
one-sided the other way, that would have been a finding about the algorithm as
implemented rather than about the evidence.

## Reach or conduct -- the distinction this ledger exists to keep

A domain whose signalling responses are **all "No information"** says what *we could
reach*. A domain with at least one substantive response says something about *the
trial*. Both are valid RoB 2 outputs. Printing the first as though it were the second
defames a trial for our missing information.

| | n |
|---|---|
| re-derivations from an ALL-NO-INFORMATION domain (reach) | 128 |
| re-derivations using at least one substantive response (conduct) | 3 |
| results with a derivable overall | 24 of 87 |
| ...of those, overall HIGH | 9 |
| ...of those HIGH results, driven ENTIRELY by an all-no-information domain | **9 of 9** |

**All 9 of the 9 results the algorithm rates HIGH are rated HIGH because of a domain on which we reached no information at all** -- in every case D2, where Table 6 routes 2.6 = NI to 2.7, and 2.7 = NI to High. Not one is rated HIGH by anything we know about how the trial was run.

And 128 of the 131 re-derivations are reach. Only three come from a substantive response, all of them D2 on iv-iron-hf.

### Display: the two must not be printed the same way

A reach-derived domain must never appear as a bare verdict. Proposed wording, which states the algorithm faithfully without transferring the deficit to the trial:

> **Domain 2 (deviations from intended intervention): no information reached.** We did not retrieve this trial's analysis-population statement, so RoB 2 signalling questions 2.6 and 2.7 are both "No information", and the published algorithm (Table 6) proposes **High** on that basis. *This records what this review could reach, not a finding about how the trial was conducted.* Closing it needs the primary publication's analysis-population statement or the SAP.

The result-level line follows the same rule: *"Rated High by the RoB 2 algorithm because no information was reached on domain 2"*, never *"High risk of bias"* alone.

### What would close it, per domain

| domain | the questions we cannot answer | what would answer them |
|---|---|---|
| D1 | 1.1 sequence generation, 1.2 allocation concealment | the trial protocol, or the randomisation paragraph of the primary publication. A registry `allocation: RANDOMIZED` field does not answer either -- RoB 2 guidance Box 4 says so explicitly |
| D2 | 2.6 appropriate analysis, 2.7 impact of switching | the analysis-population statement (ITT / mITT) in the publication Methods, the CONSORT flow, or the SAP. For approved drugs, an FDA review or EPAR carries both |
| D3 | 3.2 evidence the result was not biased by missing data | the CONSORT flow diagram and the analysed N per arm. **This is the one that blocks 60 domains and 63 overall ratings**, and 3.1 alone would unblock most of them: Table 10 row 1 gives Low from 3.1 = Y/PY without needing 3.2 |
| D5 | 5.1 pre-specified plan | the SAP or protocol. The registered outcome list, which we already hold, answers 5.2 and 5.3 but not 5.1 |

This is the open-full-text argument applied to risk of bias: "we could not reach it" is only honest while we also say what reaching would take, and for 60 of these domains it takes one figure from one paper.

## The 60 underivable domains -- first-class rows, not a footnote

Every one is D3. Table 10 has no row for 3.2 = No information: each of its five rows
requires 3.2 in {Y/PY, N/PN}, and Table 9 cannot be met either. **The published
algorithm defines no output**, so none was written. An underivable domain is a result.

| topic | outcome | result | domain | stored |
|---|---|---|---|---|
| agyw-hiv-prep-review | primary | NCT01539226 | D3_missing_outcome_data | NO_INFORMATION |
| agyw-hiv-prep-review | primary | NCT01617096 | D3_missing_outcome_data | NO_INFORMATION |
| apixaban-vte-treatment | recurrent_vte | NCT01780987 | D3_missing_outcome_data | NO_INFORMATION |
| apixaban-vte-treatment | recurrent_vte | NCT03045406 | D3_missing_outcome_data | NO_INFORMATION |
| apixaban-vte-treatment | recurrent_vte | NCT03266783 | D3_missing_outcome_data | NO_INFORMATION |
| attr-cm-review | primary | NCT01994889 | D3_missing_outcome_data | NO_INFORMATION |
| attr-cm-review | primary | NCT03860935 | D3_missing_outcome_data | NO_INFORMATION |
| bococizumab-lipid-review | ldlc_pct_change_wk12 | NCT01968954 | D3_missing_outcome_data | NO_INFORMATION |
| bococizumab-lipid-review | ldlc_pct_change_wk12 | NCT01968967 | D3_missing_outcome_data | NO_INFORMATION |
| bococizumab-lipid-review | ldlc_pct_change_wk12 | NCT01968980 | D3_missing_outcome_data | NO_INFORMATION |
| bococizumab-lipid-review | ldlc_pct_change_wk12 | NCT02100514 | D3_missing_outcome_data | NO_INFORMATION |
| bococizumab-lipid-review | ldlc_pct_change_wk12 | NCT02135029 | D3_missing_outcome_data | NO_INFORMATION |
| bococizumab-lipid-review | ldlc_pct_change_wk12 | NCT02458287 | D3_missing_outcome_data | NO_INFORMATION |
| cab-prep-hiv-review | primary | NCT02720094 | D3_missing_outcome_data | NO_INFORMATION |
| cab-prep-hiv-review | primary | NCT03164564 | D3_missing_outcome_data | NO_INFORMATION |
| ceftaroline-auto-full-review | primary | NCT00509106 | D3_missing_outcome_data | NO_INFORMATION |
| ceftaroline-auto-full-review | primary | NCT00621504 | D3_missing_outcome_data | NO_INFORMATION |
| ceftaroline-auto-full-review | primary | NCT01371838 | D3_missing_outcome_data | NO_INFORMATION |
| finerenone-cv | cv_composite_first | NCT02540993 | D3_missing_outcome_data | NO_INFORMATION |
| finerenone-cv | cv_composite_first | NCT02545049 | D3_missing_outcome_data | NO_INFORMATION |
| gepotidacin-urinary-tract-auto-full-review | primary | NCT04020341 | D3_missing_outcome_data | NO_INFORMATION |
| gepotidacin-urinary-tract-auto-full-review | primary | NCT04187144 | D3_missing_outcome_data | NO_INFORMATION |
| icosapent-lipid-auto-full-review | primary | NCT01047683 | D3_missing_outcome_data | NO_INFORMATION |
| icosapent-lipid-auto-full-review | primary | NCT01047501 | D3_missing_outcome_data | NO_INFORMATION |
| inclisiran-lipid-kidney-auto-full-review | primary | NCT03397121 | D3_missing_outcome_data | NO_INFORMATION |
| inclisiran-lipid-kidney-auto-full-review | primary | NCT03399370 | D3_missing_outcome_data | NO_INFORMATION |
| inclisiran-lipid-kidney-auto-full-review | primary | NCT03400800 | D3_missing_outcome_data | NO_INFORMATION |
| iv-iron-hf | hfh_cvd_first | NCT02937454 | D3_missing_outcome_data | NO_INFORMATION |
| iv-iron-hf | hfh_recurrent | NCT02937454 | D3_missing_outcome_data | NO_INFORMATION |
| iv-iron-hf | hfh_recurrent | NCT03036462 | D3_missing_outcome_data | NO_INFORMATION |
| iv-iron-hf | acm | NCT02937454 | D3_missing_outcome_data | NO_INFORMATION |
| iv-iron-hf | acm | NCT01453608 | D3_missing_outcome_data | NO_INFORMATION |
| lefamulin-cabp-auto-full-review | primary | NCT02559310 | D3_missing_outcome_data | NO_INFORMATION |
| lefamulin-cabp-auto-full-review | primary | NCT02813694 | D3_missing_outcome_data | NO_INFORMATION |
| malaria-vaccines | exploratory_recurrent_rate | NCT00866619::rtss-phase3-children | D3_missing_outcome_data | NO_INFORMATION |
| malaria-vaccines | exploratory_recurrent_rate | NCT04704830::datoo-2024-phase3 | D3_missing_outcome_data | NO_INFORMATION |
| malaria-vaccines | r21_seasonal_first_12m | NCT03896724::datoo-2021-phase2b | D3_missing_outcome_data | NO_INFORMATION |
| malaria-vaccines | r21_seasonal_first_12m | NCT04704830::datoo-2024-phase3 | D3_missing_outcome_data | NO_INFORMATION |
| malaria-vaccines | r21_standard_first_12m | NCT04704830::datoo-2024-phase3 | D3_missing_outcome_data | NO_INFORMATION |
| malaria-vaccines | rtss_first_episode_rate_12m | NCT00866619::rtss-phase3-children | D3_missing_outcome_data | NO_INFORMATION |
| malaria-vaccines | rtss_first_episode_short | NCT00380393::bejon-2008-phase2b | D3_missing_outcome_data | NO_INFORMATION |
| malaria-vaccines | rtss_recurrent_children_final | NCT00866619::rtss-phase3-children | D3_missing_outcome_data | NO_INFORMATION |
| malaria-vaccines | rtss_recurrent_children_final | NCT03276962::rtss-fractional-dose-phase2b | D3_missing_outcome_data | NO_INFORMATION |
| malaria-vaccines | rtss_recurrent_infants_epi_19m | NCT00436007::asante-2011-epi-phase2 | D3_missing_outcome_data | NO_INFORMATION |
| malaria-vaccines | rtss_recurrent_infants_final | NCT00866619::rtss-phase3-infants | D3_missing_outcome_data | NO_INFORMATION |
| malaria-vaccines | rtss_versus_chemoprevention | NCT03143218::chandramohan-2021-phase3 | D3_missing_outcome_data | NO_INFORMATION |
| nirsevimab-infant-rsv-review | primary | NCT02878330 | D3_missing_outcome_data | NO_INFORMATION |
| nirsevimab-infant-rsv-review | primary | NCT03979313 | D3_missing_outcome_data | NO_INFORMATION |
| sglt2-hf | harmonised_cvdeath_or_hhf | NCT03036124 | D3_missing_outcome_data | NO_INFORMATION |
| sglt2-hf | harmonised_cvdeath_or_hhf | NCT03057951 | D3_missing_outcome_data | NO_INFORMATION |
| sglt2-hf | harmonised_cvdeath_or_hhf | NCT03057977 | D3_missing_outcome_data | NO_INFORMATION |
| sglt2-hf | threecomp_cvdeath_hhf_urgent | NCT03036124 | D3_missing_outcome_data | NO_INFORMATION |
| sglt2-hf | threecomp_cvdeath_hhf_urgent | NCT03619213 | D3_missing_outcome_data | NO_INFORMATION |
| sotagliflozin-hf | hfcv_total | NCT03521934 | D3_missing_outcome_data | NO_INFORMATION |
| sotagliflozin-hf | hfcv_total | NCT03315143 | D3_missing_outcome_data | NO_INFORMATION |
| sotagliflozin-hf | hfcv_first | NCT03521934 | D3_missing_outcome_data | NO_INFORMATION |
| sotagliflozin-hf | hfcv_first | NCT03315143 | D3_missing_outcome_data | NO_INFORMATION |
| tigecycline-ciai | cure_toc_me | NCT00081744 | D3_missing_outcome_data | NO_INFORMATION |
| tigecycline-ciai | cure_toc_me | NCT00136201 | D3_missing_outcome_data | NO_INFORMATION |
| tigecycline-ciai | cure_toc_me | NCT01721408 | D3_missing_outcome_data | NO_INFORMATION |

## Every re-derivation

`reach` marks a domain whose responses were all "No information".

| topic | outcome | result | domain | stored | re-derived | reach | table row |
|---|---|---|---|---|---|---|---|
| ablation-af-heart-failure | primary | NCT00643188 | D2_deviations | NO_INFORMATION | **HIGH** | reach | effect of ASSIGNMENT variant / Part 1 row 3: 2.3 = NI -> Some concerns / Part 2  |
| ablation-af-heart-failure | primary | NCT01420393 | D2_deviations | NO_INFORMATION | **HIGH** | reach | effect of ASSIGNMENT variant / Part 1 row 3: 2.3 = NI -> Some concerns / Part 2  |
| ablation-af-medical-therapy | primary | NCT00643188 | D2_deviations | NO_INFORMATION | **HIGH** | reach | effect of ASSIGNMENT variant / Part 1 row 3: 2.3 = NI -> Some concerns / Part 2  |
| ablation-af-medical-therapy | primary | NCT00911508 | D2_deviations | NO_INFORMATION | **HIGH** | reach | effect of ASSIGNMENT variant / Part 1 row 3: 2.3 = NI -> Some concerns / Part 2  |
| ablation-af-medical-therapy | primary | NCT01420393 | D2_deviations | NO_INFORMATION | **HIGH** | reach | effect of ASSIGNMENT variant / Part 1 row 3: 2.3 = NI -> Some concerns / Part 2  |
| agyw-hiv-prep-review | primary | NCT01539226 | D1_randomisation_process | NO_INFORMATION | **SOME_CONCERNS** | reach | Table 4: 1.2 = NI AND 1.3 = N/PN/NI -> Some concerns. Table 3 states the same in |
| agyw-hiv-prep-review | primary | NCT01539226 | D2_deviations_from_intended_intervention | NO_INFORMATION | **HIGH** | reach | effect of ASSIGNMENT variant / Part 1 row 3: 2.3 = NI -> Some concerns / Part 2  |
| agyw-hiv-prep-review | primary | NCT01617096 | D1_randomisation_process | NO_INFORMATION | **SOME_CONCERNS** | reach | Table 4: 1.2 = NI AND 1.3 = N/PN/NI -> Some concerns. Table 3 states the same in |
| agyw-hiv-prep-review | primary | NCT01617096 | D2_deviations_from_intended_intervention | NO_INFORMATION | **HIGH** | reach | effect of ASSIGNMENT variant / Part 1 row 3: 2.3 = NI -> Some concerns / Part 2  |
| apixaban-vte-treatment | recurrent_vte | NCT01780987 | D1_randomisation_process | NO_INFORMATION | **SOME_CONCERNS** | reach | Table 4: 1.2 = NI AND 1.3 = N/PN/NI -> Some concerns. Table 3 states the same in |
| apixaban-vte-treatment | recurrent_vte | NCT01780987 | D2_deviations_from_intended_intervention | NO_INFORMATION | **HIGH** | reach | effect of ASSIGNMENT variant / Part 1 row 3: 2.3 = NI -> Some concerns / Part 2  |
| apixaban-vte-treatment | recurrent_vte | NCT03045406 | D1_randomisation_process | NO_INFORMATION | **SOME_CONCERNS** | reach | Table 4: 1.2 = NI AND 1.3 = N/PN/NI -> Some concerns. Table 3 states the same in |
| apixaban-vte-treatment | recurrent_vte | NCT03045406 | D2_deviations_from_intended_intervention | NO_INFORMATION | **HIGH** | reach | effect of ASSIGNMENT variant / Part 1 row 3: 2.3 = NI -> Some concerns / Part 2  |
| apixaban-vte-treatment | recurrent_vte | NCT03266783 | D1_randomisation_process | NO_INFORMATION | **SOME_CONCERNS** | reach | Table 4: 1.2 = NI AND 1.3 = N/PN/NI -> Some concerns. Table 3 states the same in |
| apixaban-vte-treatment | recurrent_vte | NCT03266783 | D2_deviations_from_intended_intervention | NO_INFORMATION | **HIGH** | reach | effect of ASSIGNMENT variant / Part 1 row 3: 2.3 = NI -> Some concerns / Part 2  |
| attr-cm-review | primary | NCT01994889 | D1_randomisation | NO_INFORMATION | **SOME_CONCERNS** | reach | Table 4: 1.2 = NI AND 1.3 = N/PN/NI -> Some concerns. Table 3 states the same in |
| attr-cm-review | primary | NCT01994889 | D2_deviations | NO_INFORMATION | **HIGH** | reach | effect of ASSIGNMENT variant / Part 1 row 3: 2.3 = NI -> Some concerns / Part 2  |
| attr-cm-review | primary | NCT03860935 | D1_randomisation | NO_INFORMATION | **SOME_CONCERNS** | reach | Table 4: 1.2 = NI AND 1.3 = N/PN/NI -> Some concerns. Table 3 states the same in |
| attr-cm-review | primary | NCT03860935 | D2_deviations | NO_INFORMATION | **HIGH** | reach | effect of ASSIGNMENT variant / Part 1 row 3: 2.3 = NI -> Some concerns / Part 2  |
| bempedoic-acid-review | primary | NCT02993406 | D1_randomisation | NO_INFORMATION | **SOME_CONCERNS** | reach | Table 4: 1.2 = NI AND 1.3 = N/PN/NI -> Some concerns. Table 3 states the same in |
| bempedoic-acid-review | primary | NCT02993406 | D2_deviations | NO_INFORMATION | **HIGH** | reach | effect of ASSIGNMENT variant / Part 1 row 3: 2.3 = NI -> Some concerns / Part 2  |
| bococizumab-lipid-review | ldlc_pct_change_wk12 | NCT01968954 | D1_randomisation_process | NO_INFORMATION | **SOME_CONCERNS** | reach | Table 4: 1.2 = NI AND 1.3 = N/PN/NI -> Some concerns. Table 3 states the same in |
| bococizumab-lipid-review | ldlc_pct_change_wk12 | NCT01968954 | D2_deviations_from_intended_intervention | NO_INFORMATION | **HIGH** | reach | effect of ASSIGNMENT variant / Part 1 row 3: 2.3 = NI -> Some concerns / Part 2  |
| bococizumab-lipid-review | ldlc_pct_change_wk12 | NCT01968967 | D1_randomisation_process | NO_INFORMATION | **SOME_CONCERNS** | reach | Table 4: 1.2 = NI AND 1.3 = N/PN/NI -> Some concerns. Table 3 states the same in |
| bococizumab-lipid-review | ldlc_pct_change_wk12 | NCT01968967 | D2_deviations_from_intended_intervention | NO_INFORMATION | **HIGH** | reach | effect of ASSIGNMENT variant / Part 1 row 3: 2.3 = NI -> Some concerns / Part 2  |
| bococizumab-lipid-review | ldlc_pct_change_wk12 | NCT01968980 | D1_randomisation_process | NO_INFORMATION | **SOME_CONCERNS** | reach | Table 4: 1.2 = NI AND 1.3 = N/PN/NI -> Some concerns. Table 3 states the same in |
| bococizumab-lipid-review | ldlc_pct_change_wk12 | NCT01968980 | D2_deviations_from_intended_intervention | NO_INFORMATION | **HIGH** | reach | effect of ASSIGNMENT variant / Part 1 row 3: 2.3 = NI -> Some concerns / Part 2  |
| bococizumab-lipid-review | ldlc_pct_change_wk12 | NCT02100514 | D1_randomisation_process | NO_INFORMATION | **SOME_CONCERNS** | reach | Table 4: 1.2 = NI AND 1.3 = N/PN/NI -> Some concerns. Table 3 states the same in |
| bococizumab-lipid-review | ldlc_pct_change_wk12 | NCT02100514 | D2_deviations_from_intended_intervention | NO_INFORMATION | **HIGH** | reach | effect of ASSIGNMENT variant / Part 1 row 3: 2.3 = NI -> Some concerns / Part 2  |
| bococizumab-lipid-review | ldlc_pct_change_wk12 | NCT02135029 | D1_randomisation_process | NO_INFORMATION | **SOME_CONCERNS** | reach | Table 4: 1.2 = NI AND 1.3 = N/PN/NI -> Some concerns. Table 3 states the same in |
| bococizumab-lipid-review | ldlc_pct_change_wk12 | NCT02135029 | D2_deviations_from_intended_intervention | NO_INFORMATION | **HIGH** | reach | effect of ASSIGNMENT variant / Part 1 row 3: 2.3 = NI -> Some concerns / Part 2  |
| bococizumab-lipid-review | ldlc_pct_change_wk12 | NCT02458287 | D1_randomisation_process | NO_INFORMATION | **SOME_CONCERNS** | reach | Table 4: 1.2 = NI AND 1.3 = N/PN/NI -> Some concerns. Table 3 states the same in |
| bococizumab-lipid-review | ldlc_pct_change_wk12 | NCT02458287 | D2_deviations_from_intended_intervention | NO_INFORMATION | **HIGH** | reach | effect of ASSIGNMENT variant / Part 1 row 3: 2.3 = NI -> Some concerns / Part 2  |
| cab-prep-hiv-review | primary | NCT02720094 | D1_randomisation_process | NO_INFORMATION | **SOME_CONCERNS** | reach | Table 4: 1.2 = NI AND 1.3 = N/PN/NI -> Some concerns. Table 3 states the same in |
| cab-prep-hiv-review | primary | NCT02720094 | D2_deviations_from_intended_intervention | NO_INFORMATION | **HIGH** | reach | effect of ASSIGNMENT variant / Part 1 row 3: 2.3 = NI -> Some concerns / Part 2  |
| cab-prep-hiv-review | primary | NCT03164564 | D1_randomisation_process | NO_INFORMATION | **SOME_CONCERNS** | reach | Table 4: 1.2 = NI AND 1.3 = N/PN/NI -> Some concerns. Table 3 states the same in |
| cab-prep-hiv-review | primary | NCT03164564 | D2_deviations_from_intended_intervention | NO_INFORMATION | **HIGH** | reach | effect of ASSIGNMENT variant / Part 1 row 3: 2.3 = NI -> Some concerns / Part 2  |
| ceftaroline-auto-full-review | primary | NCT00509106 | D1_randomisation_process | NO_INFORMATION | **SOME_CONCERNS** | reach | Table 4: 1.2 = NI AND 1.3 = N/PN/NI -> Some concerns. Table 3 states the same in |
| ceftaroline-auto-full-review | primary | NCT00509106 | D2_deviations_from_intended_intervention | NO_INFORMATION | **HIGH** | reach | effect of ASSIGNMENT variant / Part 1 row 3: 2.3 = NI -> Some concerns / Part 2  |
| ceftaroline-auto-full-review | primary | NCT00621504 | D1_randomisation_process | NO_INFORMATION | **SOME_CONCERNS** | reach | Table 4: 1.2 = NI AND 1.3 = N/PN/NI -> Some concerns. Table 3 states the same in |
| ceftaroline-auto-full-review | primary | NCT00621504 | D2_deviations_from_intended_intervention | NO_INFORMATION | **HIGH** | reach | effect of ASSIGNMENT variant / Part 1 row 3: 2.3 = NI -> Some concerns / Part 2  |
| ceftaroline-auto-full-review | primary | NCT01371838 | D1_randomisation_process | NO_INFORMATION | **SOME_CONCERNS** | reach | Table 4: 1.2 = NI AND 1.3 = N/PN/NI -> Some concerns. Table 3 states the same in |
| ceftaroline-auto-full-review | primary | NCT01371838 | D2_deviations_from_intended_intervention | NO_INFORMATION | **HIGH** | reach | effect of ASSIGNMENT variant / Part 1 row 3: 2.3 = NI -> Some concerns / Part 2  |
| early-rhythm-control-af | primary | NCT01288352 | D2_deviations | NO_INFORMATION | **HIGH** | reach | effect of ASSIGNMENT variant / Part 1 row 3: 2.3 = NI -> Some concerns / Part 2  |
| empagliflozin-hf-auto-full-review | primary | NCT03057977 | D1_randomisation_process | NO_INFORMATION | **SOME_CONCERNS** | reach | Table 4: 1.2 = NI AND 1.3 = N/PN/NI -> Some concerns. Table 3 states the same in |
| empagliflozin-hf-auto-full-review | primary | NCT03057977 | D2_deviations_from_intended_intervention | NO_INFORMATION | **HIGH** | reach | effect of ASSIGNMENT variant / Part 1 row 3: 2.3 = NI -> Some concerns / Part 2  |
| empagliflozin-hf-auto-full-review | primary | NCT03057951 | D1_randomisation_process | NO_INFORMATION | **SOME_CONCERNS** | reach | Table 4: 1.2 = NI AND 1.3 = N/PN/NI -> Some concerns. Table 3 states the same in |
| empagliflozin-hf-auto-full-review | primary | NCT03057951 | D2_deviations_from_intended_intervention | NO_INFORMATION | **HIGH** | reach | effect of ASSIGNMENT variant / Part 1 row 3: 2.3 = NI -> Some concerns / Part 2  |
| finerenone-cv | cv_composite_first | NCT02540993 | D1_randomisation_process | NO_INFORMATION | **SOME_CONCERNS** | reach | Table 4: 1.2 = NI AND 1.3 = N/PN/NI -> Some concerns. Table 3 states the same in |
| finerenone-cv | cv_composite_first | NCT02540993 | D2_deviations_from_intended_intervention | NO_INFORMATION | **HIGH** | reach | effect of ASSIGNMENT variant / Part 1 row 3: 2.3 = NI -> Some concerns / Part 2  |
| finerenone-cv | cv_composite_first | NCT02545049 | D1_randomisation_process | NO_INFORMATION | **SOME_CONCERNS** | reach | Table 4: 1.2 = NI AND 1.3 = N/PN/NI -> Some concerns. Table 3 states the same in |
| finerenone-cv | cv_composite_first | NCT02545049 | D2_deviations_from_intended_intervention | NO_INFORMATION | **HIGH** | reach | effect of ASSIGNMENT variant / Part 1 row 3: 2.3 = NI -> Some concerns / Part 2  |
| gepotidacin-urinary-tract-auto-full-review | primary | NCT04020341 | D1_randomisation_process | NO_INFORMATION | **SOME_CONCERNS** | reach | Table 4: 1.2 = NI AND 1.3 = N/PN/NI -> Some concerns. Table 3 states the same in |
| gepotidacin-urinary-tract-auto-full-review | primary | NCT04020341 | D2_deviations_from_intended_intervention | NO_INFORMATION | **HIGH** | reach | effect of ASSIGNMENT variant / Part 1 row 3: 2.3 = NI -> Some concerns / Part 2  |
| gepotidacin-urinary-tract-auto-full-review | primary | NCT04187144 | D1_randomisation_process | NO_INFORMATION | **SOME_CONCERNS** | reach | Table 4: 1.2 = NI AND 1.3 = N/PN/NI -> Some concerns. Table 3 states the same in |
| gepotidacin-urinary-tract-auto-full-review | primary | NCT04187144 | D2_deviations_from_intended_intervention | NO_INFORMATION | **HIGH** | reach | effect of ASSIGNMENT variant / Part 1 row 3: 2.3 = NI -> Some concerns / Part 2  |
| icosapent-lipid-auto-full-review | primary | NCT01047683 | D1_randomisation_process | NO_INFORMATION | **SOME_CONCERNS** | reach | Table 4: 1.2 = NI AND 1.3 = N/PN/NI -> Some concerns. Table 3 states the same in |
| icosapent-lipid-auto-full-review | primary | NCT01047683 | D2_deviations_from_intended_intervention | NO_INFORMATION | **HIGH** | reach | effect of ASSIGNMENT variant / Part 1 row 3: 2.3 = NI -> Some concerns / Part 2  |
| icosapent-lipid-auto-full-review | primary | NCT01047501 | D1_randomisation_process | NO_INFORMATION | **SOME_CONCERNS** | reach | Table 4: 1.2 = NI AND 1.3 = N/PN/NI -> Some concerns. Table 3 states the same in |
| icosapent-lipid-auto-full-review | primary | NCT01047501 | D2_deviations_from_intended_intervention | NO_INFORMATION | **HIGH** | reach | effect of ASSIGNMENT variant / Part 1 row 3: 2.3 = NI -> Some concerns / Part 2  |
| inclisiran-lipid-kidney-auto-full-review | primary | NCT03397121 | D1_randomisation_process | NO_INFORMATION | **SOME_CONCERNS** | reach | Table 4: 1.2 = NI AND 1.3 = N/PN/NI -> Some concerns. Table 3 states the same in |
| inclisiran-lipid-kidney-auto-full-review | primary | NCT03397121 | D2_deviations_from_intended_intervention | NO_INFORMATION | **HIGH** | reach | effect of ASSIGNMENT variant / Part 1 row 3: 2.3 = NI -> Some concerns / Part 2  |
| inclisiran-lipid-kidney-auto-full-review | primary | NCT03399370 | D1_randomisation_process | NO_INFORMATION | **SOME_CONCERNS** | reach | Table 4: 1.2 = NI AND 1.3 = N/PN/NI -> Some concerns. Table 3 states the same in |
| inclisiran-lipid-kidney-auto-full-review | primary | NCT03399370 | D2_deviations_from_intended_intervention | NO_INFORMATION | **HIGH** | reach | effect of ASSIGNMENT variant / Part 1 row 3: 2.3 = NI -> Some concerns / Part 2  |
| inclisiran-lipid-kidney-auto-full-review | primary | NCT03400800 | D1_randomisation_process | NO_INFORMATION | **SOME_CONCERNS** | reach | Table 4: 1.2 = NI AND 1.3 = N/PN/NI -> Some concerns. Table 3 states the same in |
| inclisiran-lipid-kidney-auto-full-review | primary | NCT03400800 | D2_deviations_from_intended_intervention | NO_INFORMATION | **HIGH** | reach | effect of ASSIGNMENT variant / Part 1 row 3: 2.3 = NI -> Some concerns / Part 2  |
| iv-iron-hf | hfh_cvd_recurrent | NCT02642562 | D2_deviations | NO_INFORMATION | **SOME_CONCERNS** | conduct | effect of ASSIGNMENT variant / Part 1 row 3: 2.3 = NI -> Some concerns / Part 2  |
| iv-iron-hf | hfh_cvd_first | NCT03036462 | D2_deviations | NO_INFORMATION | **SOME_CONCERNS** | conduct | effect of ASSIGNMENT variant / Part 1 row 3: 2.3 = NI -> Some concerns / Part 2  |
| iv-iron-hf | hfh_recurrent | NCT03036462 | D2_deviations | NO_INFORMATION | **SOME_CONCERNS** | conduct | effect of ASSIGNMENT variant / Part 1 row 3: 2.3 = NI -> Some concerns / Part 2  |
| lefamulin-cabp-auto-full-review | primary | NCT02559310 | D1_randomisation_process | NO_INFORMATION | **SOME_CONCERNS** | reach | Table 4: 1.2 = NI AND 1.3 = N/PN/NI -> Some concerns. Table 3 states the same in |
| lefamulin-cabp-auto-full-review | primary | NCT02559310 | D2_deviations_from_intended_intervention | NO_INFORMATION | **HIGH** | reach | effect of ASSIGNMENT variant / Part 1 row 3: 2.3 = NI -> Some concerns / Part 2  |
| lefamulin-cabp-auto-full-review | primary | NCT02813694 | D1_randomisation_process | NO_INFORMATION | **SOME_CONCERNS** | reach | Table 4: 1.2 = NI AND 1.3 = N/PN/NI -> Some concerns. Table 3 states the same in |
| lefamulin-cabp-auto-full-review | primary | NCT02813694 | D2_deviations_from_intended_intervention | NO_INFORMATION | **HIGH** | reach | effect of ASSIGNMENT variant / Part 1 row 3: 2.3 = NI -> Some concerns / Part 2  |
| malaria-vaccines | exploratory_recurrent_rate | NCT00866619::rtss-phase3-children | D1_randomisation_process | NO_INFORMATION | **SOME_CONCERNS** | reach | Table 4: 1.2 = NI AND 1.3 = N/PN/NI -> Some concerns. Table 3 states the same in |
| malaria-vaccines | exploratory_recurrent_rate | NCT00866619::rtss-phase3-children | D2_deviations_from_intended_intervention | NO_INFORMATION | **HIGH** | reach | effect of ASSIGNMENT variant / Part 1 row 3: 2.3 = NI -> Some concerns / Part 2  |
| malaria-vaccines | exploratory_recurrent_rate | NCT04704830::datoo-2024-phase3 | D1_randomisation_process | NO_INFORMATION | **SOME_CONCERNS** | reach | Table 4: 1.2 = NI AND 1.3 = N/PN/NI -> Some concerns. Table 3 states the same in |
| malaria-vaccines | exploratory_recurrent_rate | NCT04704830::datoo-2024-phase3 | D2_deviations_from_intended_intervention | NO_INFORMATION | **HIGH** | reach | effect of ASSIGNMENT variant / Part 1 row 3: 2.3 = NI -> Some concerns / Part 2  |
| malaria-vaccines | r21_seasonal_first_12m | NCT03896724::datoo-2021-phase2b | D1_randomisation_process | NO_INFORMATION | **SOME_CONCERNS** | reach | Table 4: 1.2 = NI AND 1.3 = N/PN/NI -> Some concerns. Table 3 states the same in |
| malaria-vaccines | r21_seasonal_first_12m | NCT03896724::datoo-2021-phase2b | D2_deviations_from_intended_intervention | NO_INFORMATION | **HIGH** | reach | effect of ASSIGNMENT variant / Part 1 row 3: 2.3 = NI -> Some concerns / Part 2  |
| malaria-vaccines | r21_seasonal_first_12m | NCT04704830::datoo-2024-phase3 | D1_randomisation_process | NO_INFORMATION | **SOME_CONCERNS** | reach | Table 4: 1.2 = NI AND 1.3 = N/PN/NI -> Some concerns. Table 3 states the same in |
| malaria-vaccines | r21_seasonal_first_12m | NCT04704830::datoo-2024-phase3 | D2_deviations_from_intended_intervention | NO_INFORMATION | **HIGH** | reach | effect of ASSIGNMENT variant / Part 1 row 3: 2.3 = NI -> Some concerns / Part 2  |
| malaria-vaccines | r21_standard_first_12m | NCT04704830::datoo-2024-phase3 | D1_randomisation_process | NO_INFORMATION | **SOME_CONCERNS** | reach | Table 4: 1.2 = NI AND 1.3 = N/PN/NI -> Some concerns. Table 3 states the same in |
| malaria-vaccines | r21_standard_first_12m | NCT04704830::datoo-2024-phase3 | D2_deviations_from_intended_intervention | NO_INFORMATION | **HIGH** | reach | effect of ASSIGNMENT variant / Part 1 row 3: 2.3 = NI -> Some concerns / Part 2  |
| malaria-vaccines | rtss_first_episode_rate_12m | NCT00866619::rtss-phase3-children | D1_randomisation_process | NO_INFORMATION | **SOME_CONCERNS** | reach | Table 4: 1.2 = NI AND 1.3 = N/PN/NI -> Some concerns. Table 3 states the same in |
| malaria-vaccines | rtss_first_episode_rate_12m | NCT00866619::rtss-phase3-children | D2_deviations_from_intended_intervention | NO_INFORMATION | **HIGH** | reach | effect of ASSIGNMENT variant / Part 1 row 3: 2.3 = NI -> Some concerns / Part 2  |
| malaria-vaccines | rtss_first_episode_short | NCT00380393::bejon-2008-phase2b | D1_randomisation_process | NO_INFORMATION | **SOME_CONCERNS** | reach | Table 4: 1.2 = NI AND 1.3 = N/PN/NI -> Some concerns. Table 3 states the same in |
| malaria-vaccines | rtss_first_episode_short | NCT00380393::bejon-2008-phase2b | D2_deviations_from_intended_intervention | NO_INFORMATION | **HIGH** | reach | effect of ASSIGNMENT variant / Part 1 row 3: 2.3 = NI -> Some concerns / Part 2  |
| malaria-vaccines | rtss_recurrent_children_final | NCT00866619::rtss-phase3-children | D1_randomisation_process | NO_INFORMATION | **SOME_CONCERNS** | reach | Table 4: 1.2 = NI AND 1.3 = N/PN/NI -> Some concerns. Table 3 states the same in |
| malaria-vaccines | rtss_recurrent_children_final | NCT00866619::rtss-phase3-children | D2_deviations_from_intended_intervention | NO_INFORMATION | **HIGH** | reach | effect of ASSIGNMENT variant / Part 1 row 3: 2.3 = NI -> Some concerns / Part 2  |
| malaria-vaccines | rtss_recurrent_children_final | NCT03276962::rtss-fractional-dose-phase2b | D1_randomisation_process | NO_INFORMATION | **SOME_CONCERNS** | reach | Table 4: 1.2 = NI AND 1.3 = N/PN/NI -> Some concerns. Table 3 states the same in |
| malaria-vaccines | rtss_recurrent_children_final | NCT03276962::rtss-fractional-dose-phase2b | D2_deviations_from_intended_intervention | NO_INFORMATION | **HIGH** | reach | effect of ASSIGNMENT variant / Part 1 row 3: 2.3 = NI -> Some concerns / Part 2  |
| malaria-vaccines | rtss_recurrent_infants_epi_19m | NCT00436007::asante-2011-epi-phase2 | D1_randomisation_process | NO_INFORMATION | **SOME_CONCERNS** | reach | Table 4: 1.2 = NI AND 1.3 = N/PN/NI -> Some concerns. Table 3 states the same in |
| malaria-vaccines | rtss_recurrent_infants_epi_19m | NCT00436007::asante-2011-epi-phase2 | D2_deviations_from_intended_intervention | NO_INFORMATION | **HIGH** | reach | effect of ASSIGNMENT variant / Part 1 row 3: 2.3 = NI -> Some concerns / Part 2  |
| malaria-vaccines | rtss_recurrent_infants_final | NCT00866619::rtss-phase3-infants | D1_randomisation_process | NO_INFORMATION | **SOME_CONCERNS** | reach | Table 4: 1.2 = NI AND 1.3 = N/PN/NI -> Some concerns. Table 3 states the same in |
| malaria-vaccines | rtss_recurrent_infants_final | NCT00866619::rtss-phase3-infants | D2_deviations_from_intended_intervention | NO_INFORMATION | **HIGH** | reach | effect of ASSIGNMENT variant / Part 1 row 3: 2.3 = NI -> Some concerns / Part 2  |
| malaria-vaccines | rtss_versus_chemoprevention | NCT03143218::chandramohan-2021-phase3 | D1_randomisation_process | NO_INFORMATION | **SOME_CONCERNS** | reach | Table 4: 1.2 = NI AND 1.3 = N/PN/NI -> Some concerns. Table 3 states the same in |
| malaria-vaccines | rtss_versus_chemoprevention | NCT03143218::chandramohan-2021-phase3 | D2_deviations_from_intended_intervention | NO_INFORMATION | **HIGH** | reach | effect of ASSIGNMENT variant / Part 1 row 3: 2.3 = NI -> Some concerns / Part 2  |
| nirsevimab-infant-rsv-review | primary | NCT02878330 | D1_randomisation_process | NO_INFORMATION | **SOME_CONCERNS** | reach | Table 4: 1.2 = NI AND 1.3 = N/PN/NI -> Some concerns. Table 3 states the same in |
| nirsevimab-infant-rsv-review | primary | NCT02878330 | D2_deviations_from_intended_intervention | NO_INFORMATION | **HIGH** | reach | effect of ASSIGNMENT variant / Part 1 row 3: 2.3 = NI -> Some concerns / Part 2  |
| nirsevimab-infant-rsv-review | primary | NCT03979313 | D1_randomisation_process | NO_INFORMATION | **SOME_CONCERNS** | reach | Table 4: 1.2 = NI AND 1.3 = N/PN/NI -> Some concerns. Table 3 states the same in |
| nirsevimab-infant-rsv-review | primary | NCT03979313 | D2_deviations_from_intended_intervention | NO_INFORMATION | **HIGH** | reach | effect of ASSIGNMENT variant / Part 1 row 3: 2.3 = NI -> Some concerns / Part 2  |
| sglt2-hf | harmonised_cvdeath_or_hhf | NCT03036124 | D1_randomisation_process | NO_INFORMATION | **SOME_CONCERNS** | reach | Table 4: 1.2 = NI AND 1.3 = N/PN/NI -> Some concerns. Table 3 states the same in |
| sglt2-hf | harmonised_cvdeath_or_hhf | NCT03036124 | D2_deviations_from_intended_intervention | NO_INFORMATION | **HIGH** | reach | effect of ASSIGNMENT variant / Part 1 row 3: 2.3 = NI -> Some concerns / Part 2  |
| sglt2-hf | harmonised_cvdeath_or_hhf | NCT03057951 | D1_randomisation_process | NO_INFORMATION | **SOME_CONCERNS** | reach | Table 4: 1.2 = NI AND 1.3 = N/PN/NI -> Some concerns. Table 3 states the same in |
| sglt2-hf | harmonised_cvdeath_or_hhf | NCT03057951 | D2_deviations_from_intended_intervention | NO_INFORMATION | **HIGH** | reach | effect of ASSIGNMENT variant / Part 1 row 3: 2.3 = NI -> Some concerns / Part 2  |
| sglt2-hf | harmonised_cvdeath_or_hhf | NCT03057977 | D1_randomisation_process | NO_INFORMATION | **SOME_CONCERNS** | reach | Table 4: 1.2 = NI AND 1.3 = N/PN/NI -> Some concerns. Table 3 states the same in |
| sglt2-hf | harmonised_cvdeath_or_hhf | NCT03057977 | D2_deviations_from_intended_intervention | NO_INFORMATION | **HIGH** | reach | effect of ASSIGNMENT variant / Part 1 row 3: 2.3 = NI -> Some concerns / Part 2  |
| sglt2-hf | threecomp_cvdeath_hhf_urgent | NCT03036124 | D1_randomisation_process | NO_INFORMATION | **SOME_CONCERNS** | reach | Table 4: 1.2 = NI AND 1.3 = N/PN/NI -> Some concerns. Table 3 states the same in |
| sglt2-hf | threecomp_cvdeath_hhf_urgent | NCT03036124 | D2_deviations_from_intended_intervention | NO_INFORMATION | **HIGH** | reach | effect of ASSIGNMENT variant / Part 1 row 3: 2.3 = NI -> Some concerns / Part 2  |
| sglt2-hf | threecomp_cvdeath_hhf_urgent | NCT03619213 | D1_randomisation_process | NO_INFORMATION | **SOME_CONCERNS** | reach | Table 4: 1.2 = NI AND 1.3 = N/PN/NI -> Some concerns. Table 3 states the same in |
| sglt2-hf | threecomp_cvdeath_hhf_urgent | NCT03619213 | D2_deviations_from_intended_intervention | NO_INFORMATION | **HIGH** | reach | effect of ASSIGNMENT variant / Part 1 row 3: 2.3 = NI -> Some concerns / Part 2  |
| sotagliflozin-hf | hfcv_total | NCT03521934 | D1_randomisation | NO_INFORMATION | **SOME_CONCERNS** | reach | Table 4: 1.2 = NI AND 1.3 = N/PN/NI -> Some concerns. Table 3 states the same in |
| sotagliflozin-hf | hfcv_total | NCT03521934 | D2_deviations | NO_INFORMATION | **HIGH** | reach | effect of ASSIGNMENT variant / Part 1 row 3: 2.3 = NI -> Some concerns / Part 2  |
| sotagliflozin-hf | hfcv_total | NCT03521934 | D4_measurement | NO_INFORMATION | **HIGH** | reach | Table 12 row 8: 4.2 = NI, 4.5 = Y/PY/NI -> High |
| sotagliflozin-hf | hfcv_total | NCT03315143 | D1_randomisation | NO_INFORMATION | **SOME_CONCERNS** | reach | Table 4: 1.2 = NI AND 1.3 = N/PN/NI -> Some concerns. Table 3 states the same in |
| sotagliflozin-hf | hfcv_total | NCT03315143 | D2_deviations | NO_INFORMATION | **HIGH** | reach | effect of ASSIGNMENT variant / Part 1 row 3: 2.3 = NI -> Some concerns / Part 2  |
| sotagliflozin-hf | hfcv_total | NCT03315143 | D4_measurement | NO_INFORMATION | **HIGH** | reach | Table 12 row 8: 4.2 = NI, 4.5 = Y/PY/NI -> High |
| sotagliflozin-hf | hfcv_first | NCT03521934 | D1_randomisation | NO_INFORMATION | **SOME_CONCERNS** | reach | Table 4: 1.2 = NI AND 1.3 = N/PN/NI -> Some concerns. Table 3 states the same in |
| sotagliflozin-hf | hfcv_first | NCT03521934 | D2_deviations | NO_INFORMATION | **HIGH** | reach | effect of ASSIGNMENT variant / Part 1 row 3: 2.3 = NI -> Some concerns / Part 2  |
| sotagliflozin-hf | hfcv_first | NCT03315143 | D1_randomisation | NO_INFORMATION | **SOME_CONCERNS** | reach | Table 4: 1.2 = NI AND 1.3 = N/PN/NI -> Some concerns. Table 3 states the same in |
| sotagliflozin-hf | hfcv_first | NCT03315143 | D2_deviations | NO_INFORMATION | **HIGH** | reach | effect of ASSIGNMENT variant / Part 1 row 3: 2.3 = NI -> Some concerns / Part 2  |
| sotagliflozin-hf | hfcv_first | NCT03315143 | D4_measurement | NO_INFORMATION | **HIGH** | reach | Table 12 row 8: 4.2 = NI, 4.5 = Y/PY/NI -> High |
| tigecycline-ciai | cure_toc_me | NCT00081744 | D1_randomisation_process | NO_INFORMATION | **SOME_CONCERNS** | reach | Table 4: 1.2 = NI AND 1.3 = N/PN/NI -> Some concerns. Table 3 states the same in |
| tigecycline-ciai | cure_toc_me | NCT00081744 | D2_deviations_from_intended_intervention | NO_INFORMATION | **HIGH** | reach | effect of ASSIGNMENT variant / Part 1 row 3: 2.3 = NI -> Some concerns / Part 2  |
| tigecycline-ciai | cure_toc_me | NCT00081744 | D5_selection_of_the_reported_result | NO_INFORMATION | **SOME_CONCERNS** | reach | Table 14 row 5: 5.2 = NI, 5.3 = NI -> Some concerns |
| tigecycline-ciai | cure_toc_me | NCT00136201 | D1_randomisation_process | NO_INFORMATION | **SOME_CONCERNS** | reach | Table 4: 1.2 = NI AND 1.3 = N/PN/NI -> Some concerns. Table 3 states the same in |
| tigecycline-ciai | cure_toc_me | NCT00136201 | D2_deviations_from_intended_intervention | NO_INFORMATION | **HIGH** | reach | effect of ASSIGNMENT variant / Part 1 row 3: 2.3 = NI -> Some concerns / Part 2  |
| tigecycline-ciai | cure_toc_me | NCT00136201 | D5_selection_of_the_reported_result | NO_INFORMATION | **SOME_CONCERNS** | reach | Table 14 row 5: 5.2 = NI, 5.3 = NI -> Some concerns |
| tigecycline-ciai | cure_toc_me | NCT01721408 | D1_randomisation_process | NO_INFORMATION | **SOME_CONCERNS** | reach | Table 4: 1.2 = NI AND 1.3 = N/PN/NI -> Some concerns. Table 3 states the same in |
| tigecycline-ciai | cure_toc_me | NCT01721408 | D2_deviations_from_intended_intervention | NO_INFORMATION | **HIGH** | reach | effect of ASSIGNMENT variant / Part 1 row 3: 2.3 = NI -> Some concerns / Part 2  |
| tigecycline-ciai | cure_toc_me | NCT01721408 | D5_selection_of_the_reported_result | NO_INFORMATION | **SOME_CONCERNS** | reach | Table 14 row 5: 5.2 = NI, 5.3 = NI -> Some concerns |

