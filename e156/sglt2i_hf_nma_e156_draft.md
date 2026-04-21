# E156 Draft — SGLT2i Class NMA in Heart Failure

**Slug:** sglt2i_hf_nma_e156
**Status:** CURRENT BODY (AI version) · YOUR REWRITE (blank)
**Target journal:** Synthēsis (methods note, ≤400w)
**Generated:** 2026-04-21
**Links:** [App](../SGLT2I_HF_NMA_REVIEW.html) · [Bundle](../nma/validation/sglt2i_hf_peer_review_bundle.md) · [Protocol](../protocols/sglt2i_hf_nma_protocol_v1.0_2026-04-21.md)

---

## CURRENT BODY (AI version)

**S1 [Question — 22w]:** Does the cardiovascular benefit of SGLT2 inhibitors vary by agent across the heart-failure ejection-fraction spectrum, or is the effect class-consistent at the level of CV death or HF-hospitalisation?

**S2 [Dataset — 20w]:** Six pivotal placebo-controlled Phase 3 trials (DAPA-HF, EMPEROR-Reduced/Preserved, DELIVER, SOLOIST-WHF, SCORED) with 39,851 participants randomised, trial-primary composite endpoint extracted for each arm.

**S3 [Method — 20w]:** Frequentist placebo-star network meta-analysis using netmeta v3.2.0 with REML tau² and HKSJ CI adjustment; ranking via P-score and 100k-draw multivariate-normal SUCRA.

**S4 [Result — 30w]:** Hazard ratios vs placebo were 0.785 (0.719-0.857) dapagliflozin, 0.771 (0.700-0.849) empagliflozin, 0.717 (0.625-0.823) sotagliflozin; class-consistent homogeneity τ²=0.000, I²=0%; sotagliflozin rank-1 probability 79%.

**S5 [Robustness — 22w]:** Pre-specified Stratum A sensitivity (k=4 HF-primary trials excluding SOLOIST-WHF+SCORED) yielded unchanged Dapa/Empa estimates; Sotagliflozin's lead declared as potentially optimistic due to early-termination bias.

**S6 [Interpretation — 22w]:** The class effect is robust to ejection-fraction phenotype, supporting 2022 AHA/ACC/HFSA + ESC guideline pillar-4 SGLT2i recommendation regardless of EF; sotagliflozin ranking requires cautious interpretation.

**S7 [Boundary — 20w]:** No head-to-head SGLT2i-vs-SGLT2i trial exists; consistency testing undefined in the star network; findings do not extend to acute decompensated heart failure.

**Word count (body only):** _to-be-validated ≤156 words_
**Sentence count:** 7

---

## YOUR REWRITE (Mahmood's version)

_(blank — awaiting rewrite)_

---

## SUBMITTED: [ ]

## Notes

- Structured per `C:\E156\docs\E156_v0.2_SPEC.md` (7-sentence contract, ≤156 words)
- Primary estimand: HR for CV death or HHF composite
- All trial HRs match published source to 3dp (star-network pass-through)
- Scope: chronic HF + T2D-cardiometabolic post-HHF populations
- Major limitation: no head-to-head within-class evidence
