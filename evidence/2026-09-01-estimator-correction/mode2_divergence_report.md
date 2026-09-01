# Mode 2 Divergence Report

## Acceptance Control

| check | expected | observed | result |
|---|---:|---:|---|
| control_1_correct | ~= 0.00072531 (1e-3 relative) | 0.000725309396123756 | PASS |
| control_1_historic | 0.0 exactly | 0 | PASS |
| control_2_stored | 155.7997177895 | 155.7997177895 | PASS |
| control_2_historic_iters | 200 and did not converge | 200 and did not converge | PASS |
| control_2_correct | < 10 | 1.63547618757985 | PASS |

Overall acceptance control: PASS

## A. Population

- Total target files: 746 files (denominator: non-underscore `outputs/r_validation/*.json`).
- Assessable: 708 files (denominator: 746 total target files).
- NOT_ASSESSABLE: 38 files (denominator: 746 total target files).

NOT_ASSESSABLE reasons:
- FEWER_THAN_2_NUMERIC_YI_POSITIVE_VI: 22 files (denominator: 38 NOT_ASSESSABLE files).
- NO_TRIALS_LIST: 16 files (denominator: 38 NOT_ASSESSABLE files).

Identity check: assessable + NOT_ASSESSABLE = total -> 708 + 38 = 746; HOLDS.

## B. Assessable States

- DIVERGED_AT_CAP: 331 files (denominator: 708 assessable files).
- COLLAPSED_TO_ZERO: 108 files (denominator: 708 assessable files).
- AGREES: 258 files (denominator: 708 assessable files).
- OTHER_DISAGREEMENT: 11 files (denominator: 708 assessable files).

Identity check: four states sum to assessable -> 708 = 708; HOLDS.

## C. Tau2 Distribution Within DIVERGED_AT_CAP

DIVERGED_AT_CAP denominator: 331 files.

| estimator | min | median | 90th percentile | max |
|---|---:|---:|---:|---:|
| historic tau2 | 0.0356194163094923 | 46.6950399077027 | 737.329744513737 | 3605.2259961779 |
| corrected tau2 | 0.00303354379744431 | 0.4298185386125 | 5.62986884064668 | 36.7998122706405 |

## D. Pooled Sign Reversal Within DIVERGED_AT_CAP

- POOLED SIGN REVERSAL: 11 files (denominator: 331 DIVERGED_AT_CAP files; ignores |mu| < 1e-9).

First 25 DIVERGED_AT_CAP sign reversals by filename:

| filename | mu_historic | mu_correct |
|---|---:|---:|
| APIXABAN_AF_AUTO_FULL.json | 0.119038771635608 | -0.174923627245011 |
| CASIRIVIMAB_COVID_AUTO_FULL.json | 0.0227586816537271 | -0.131246075066003 |
| ETEPLIRSEN_DMD_AUTO_FULL.json | -0.161631037798543 | 0.110161387944217 |
| FARICIMAB_DME_AUTO_FULL.json | -0.109578131435019 | 0.0051602388708655 |
| GEFAPIXANT_COUGH_AUTO_FULL.json | 0.505260178070293 | -0.152950336443952 |
| MELANOMA_NEOADJUVANT.json | 0.112251705506126 | -0.169473923112402 |
| NALDEMEDINE_OIC_AUTO_FULL.json | -0.162033047315578 | 0.137005404622686 |
| PACRITINIB_MF_AUTO_FULL.json | -0.131807358151015 | 0.17185730867456 |
| TEPLIZUMAB_T1D_AUTO_FULL.json | 0.0164115194363914 | -0.00595202765219167 |
| TERIFLUNOMIDE_MS_AUTO_FULL.json | 0.0163934396787726 | -0.131956773640139 |
| VANCOMYCIN_CDI_AUTO_FULL.json | 0.0347102367009299 | -0.0695052075547248 |

## E. Conclusion Flips Within DIVERGED_AT_CAP

- CLAIM_REMOVED: 0 files (denominator: 331 DIVERGED_AT_CAP files; historic interval excluded 0, corrected interval includes 0).
- CLAIM_CREATED: 90 files (denominator: 331 DIVERGED_AT_CAP files; historic interval included 0, corrected interval excludes 0).

## F. Whole Assessable Population Flips

- POOLED SIGN REVERSAL: 26 files (denominator: 708 assessable files; ignores |mu| < 1e-9).
- CLAIM_REMOVED: 3 files (denominator: 708 assessable files; historic interval excluded 0, corrected interval includes 0).
- CLAIM_CREATED: 90 files (denominator: 708 assessable files; historic interval included 0, corrected interval excludes 0).

## Errors And Resolutions

- Initial implementation audit found the agreement check used `max(abs(a), abs(b), 1.0)`, adding an absolute floor that was looser than the requested 1e-6 relative rule for tiny tau2 values; resolved by replacing it with a pure relative comparison and rerunning the full measurement.
- Initial implementation audit found `historic_iters == 200` alone was ambiguous because exact convergence on iteration 200 and cap exhaustion both return 200; resolved by tracking an explicit convergence flag while preserving the specified historic update exactly.
- Correct estimator hit its 1000-iteration cap in 31 assessable files; resolved by retaining the specified correct() return value and still classifying by the historic state as requested.
- Pre-existing dirty worktree and `.pytest_cache` permission warnings were observed before measurement; resolution: ignored as unrelated because the task is read-only except for this report.
- NOT_ASSESSABLE files were not dropped; resolution: each file with fewer than 2 trial rows carrying numeric `yi` and numeric positive `vi` was counted under `FEWER_THAN_2_NUMERIC_YI_POSITIVE_VI`; files without a `trials` array were counted separately as `NO_TRIALS_LIST`.

## Method Notes

- Population included every non-underscore JSON sidecar under `outputs/r_validation/`.
- Historic and corrected estimators were implemented exactly as specified in the task text; the extra convergence flag records which return path the historic loop took without changing its tau2 update.
- HKSJ intervals used `se = sqrt(max(q, 1.0)/sw)` and `scripts.build_binary_sidecar.t_quantile_975(k-1)`, not 1.96.
- `AGREES` used pure 1e-6 relative tolerance on tau2 after excluding `DIVERGED_AT_CAP` and `COLLAPSED_TO_ZERO`.
