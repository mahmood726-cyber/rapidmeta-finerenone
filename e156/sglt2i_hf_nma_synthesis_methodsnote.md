---
title: "SGLT2 Inhibitor Class Effect on Cardiovascular Death or Hospitalisation for Heart Failure: A Placebo-Star Network Meta-Analysis of Six Pivotal Phase 3 Trials"
short_title: "SGLT2i class effect on CV death/HHF: a star-network meta-analysis"
article_type: Methods Note
target_journal: Synthēsis
word_count_target: ≤400
format: A4, 1.5 line-spacing, 11-pt Calibri (body) / 12-pt Times New Roman (headings acceptable)
refs: Vancouver numeric, up to 15
authors:
  - name: Mahmood Ahmad
    role: middle-author-only on E156 (per feedback_e156_authorship policy; retired COI re editorial board)
    email: drmahmoodclinic@pm.me
    affiliation: (see author block)
keywords: [network meta-analysis, SGLT2 inhibitors, heart failure, HFrEF, HFpEF, netmeta, living review]
artifact_links:
  - https://mahmood726-cyber.github.io/rapidmeta-finerenone/SGLT2I_HF_NMA_REVIEW.html
  - https://github.com/mahmood726-cyber/rapidmeta-finerenone/blob/main/nma/validation/sglt2i_hf_peer_review_bundle.md
  - https://github.com/mahmood726-cyber/rapidmeta-finerenone/blob/main/protocols/sglt2i_hf_nma_protocol_v1.0_2026-04-21.md
---

# SGLT2 Inhibitor Class Effect on Cardiovascular Death or Hospitalisation for Heart Failure: A Placebo-Star Network Meta-Analysis of Six Pivotal Phase 3 Trials

## Abstract (Methods Note, ≤400 words)

**Question.** Does the cardiovascular benefit of sodium-glucose co-transporter-2 (SGLT2) inhibitors vary by individual agent across the heart-failure ejection-fraction spectrum, or is the effect class-consistent when measured on the standard composite of cardiovascular death or hospitalisation for heart failure (HHF)?

**Dataset.** We assembled the six pivotal placebo-controlled Phase 3 trials of SGLT2 inhibitors in heart failure or at elevated heart-failure risk: DAPA-HF (dapagliflozin in HFrEF) [1], EMPEROR-Reduced (empagliflozin in HFrEF) [2], EMPEROR-Preserved (empagliflozin in HFpEF/HFmrEF) [3], DELIVER (dapagliflozin in HFpEF/HFmrEF) [4], SOLOIST-WHF (sotagliflozin in type 2 diabetes with recent HHF) [5], and SCORED (sotagliflozin in type 2 diabetes with chronic kidney disease and cardiovascular risk) [6]. The combined sample was 39 851 participants. The trial-primary composite of cardiovascular death or HHF was extracted from each publication.

**Method.** We fitted a frequentist placebo-star network meta-analysis using the `netmeta` R package (v3.2.0) with the restricted maximum-likelihood estimator for between-trial heterogeneity (τ²) and the Hartung–Knapp–Sidik–Jonkman adjustment for random-effects confidence intervals. Ranking used P-score and multivariate-normal Monte-Carlo SUCRA with 100 000 draws from the random-effects contrast variance-covariance matrix.

**Result.** Against placebo, pooled hazard ratios were 0.785 (95% CI 0.719–0.857) for dapagliflozin, 0.771 (0.700–0.849) for empagliflozin, and 0.717 (0.625–0.823) for sotagliflozin. The class showed remarkable between-trial homogeneity (τ² = 0.000, I² = 0%). Ranking placed sotagliflozin first (SUCRA 0.887), empagliflozin second (0.594), dapagliflozin third (0.519), and placebo last (0.001); sotagliflozin's rank-1 probability was 79%.

**Robustness.** A pre-specified Stratum A sensitivity analysis (k = 4 HF-primary trials, excluding SOLOIST-WHF and SCORED) left the dapagliflozin and empagliflozin estimates unchanged because star-network indirect contrasts do not inform same-drug-versus-placebo estimates. The sotagliflozin rank-1 finding is declared as potentially optimistic due to sponsor-driven early termination of both SOLOIST-WHF and SCORED (Montori 2005 bias).

**Interpretation.** The cardiovascular benefit of SGLT2 inhibitors is class-consistent across the ejection-fraction spectrum, supporting the 2022 AHA/ACC/HFSA [7] and ESC [8] guideline recommendation of SGLT2 inhibitors as pillar-4 heart-failure therapy regardless of ejection fraction. Within-class ranking is dominated by sotagliflozin's two early-terminated trials and warrants cautious interpretation.

**Boundary.** No head-to-head SGLT2-inhibitor-versus-SGLT2-inhibitor trial exists; the design-by-treatment consistency test is therefore not defined in this star network. Findings do not extend to acute decompensated heart failure (SOLOIST-WHF enrolled during or just after a hospitalisation but a dedicated acute-setting class network is absent).

## Availability

Interactive living-review app, protocol v1.0 (2026-04-21), and the full netmeta-validation peer-review bundle are open-source at `github.com/mahmood726-cyber/rapidmeta-finerenone`.

## References (Vancouver; selected)

1. McMurray JJV, Solomon SD, Inzucchi SE, et al. Dapagliflozin in patients with heart failure and reduced ejection fraction. N Engl J Med. 2019;381:1995–2008.
2. Packer M, Anker SD, Butler J, et al. Cardiovascular and renal outcomes with empagliflozin in heart failure. N Engl J Med. 2020;383:1413–24.
3. Anker SD, Butler J, Filippatos G, et al. Empagliflozin in heart failure with a preserved ejection fraction. N Engl J Med. 2021;385:1451–61.
4. Solomon SD, McMurray JJV, Claggett B, et al. Dapagliflozin in heart failure with mildly reduced or preserved ejection fraction. N Engl J Med. 2022;387:1089–98.
5. Bhatt DL, Szarek M, Steg PG, et al. Sotagliflozin in patients with diabetes and recent worsening heart failure. N Engl J Med. 2021;384:117–28.
6. Bhatt DL, Szarek M, Pitt B, et al. Sotagliflozin in patients with diabetes and chronic kidney disease. N Engl J Med. 2021;384:129–39.
7. Heidenreich PA, Bozkurt B, Aguilar D, et al. 2022 AHA/ACC/HFSA Guideline for the management of heart failure. J Am Coll Cardiol. 2022;79:e263–421.
8. McDonagh TA, Metra M, Adamo M, et al. 2021 ESC Guidelines for the diagnosis and treatment of acute and chronic heart failure. Eur Heart J. 2021;42:3599–726.

## OJS Submission Notes

- Upload: single `.docx` of body above; protocol as supplement; CSV data dump from the living-review app.
- Step-3 metadata: match "Methods Note" article type if available; else "Short Communication".
- CRediT: middle-author-only per feedback_e156_authorship policy (retired MA COI; no role in editorial handling).

## SUBMITTED: [ ]
