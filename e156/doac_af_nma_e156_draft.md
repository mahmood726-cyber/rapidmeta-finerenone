# E156 Draft — DOAC Class NMA vs Warfarin for Stroke Prevention in AF

**Slug:** doac_af_nma_e156
**Status:** CURRENT BODY (AI version) · YOUR REWRITE (blank)
**Target journal:** Synthēsis (methods note, ≤400w)
**Generated:** 2026-04-21
**Links:** [App](../DOAC_AF_NMA_REVIEW.html) · [Bundle](../nma/validation/doac_af_peer_review_bundle.md) · [Protocol](../protocols/doac_af_nma_protocol_v1.0_2026-04-21.md)

---

## CURRENT BODY (AI version)

**S1 [Question — 22w]:** Among four direct oral anticoagulants at full therapeutic dose in non-valvular atrial fibrillation, which confers the largest relative reduction in stroke or systemic embolism versus dose-adjusted warfarin?

**S2 [Dataset — 20w]:** Four pivotal Phase 3 DOAC-versus-warfarin trials (RE-LY, ROCKET-AF, ARISTOTLE, ENGAGE-AF TIMI 48) with 71,683 randomised participants and trial-primary modified-intention-to-treat stroke/SE events.

**S3 [Method — 20w]:** Frequentist warfarin-star network meta-analysis (netmeta v3.2.0, REML tau², HKSJ confidence intervals); ranking via P-score and 100k-draw multivariate-normal SUCRA.

**S4 [Result — 30w]:** Hazard ratios versus warfarin were 0.66 (0.53-0.82) dabigatran-150, 0.79 (0.66-0.95) apixaban, 0.79 (0.66-0.96) rivaroxaban, 0.79 (0.63-0.99) edoxaban; τ²=0; dabigatran rank-1 probability approximately 85%.

**S5 [Robustness — 22w]:** Point estimates match source trials to three decimal places (star-network pass-through); CHA₂DS₂-VASc-profile and time-in-therapeutic-range heterogeneity across trials declared as moderate transitivity concerns.

**S6 [Interpretation — 22w]:** Dabigatran leads on stroke-alone ranking, but published net-benefit meta-analyses incorporating major bleeding (Apixaban major-bleeding HR 0.69) typically elevate apixaban to rank-1 for clinical decision-making.

**S7 [Boundary — 20w]:** No head-to-head DOAC trial exists; the analysis excludes lower-dose arms, AVERROES (vs aspirin), and valvular AF populations.

**Word count (body only):** _to-be-validated ≤156 words_
**Sentence count:** 7

---

## YOUR REWRITE (Mahmood's version)

_(blank — awaiting rewrite)_

---

## SUBMITTED: [ ]

## Notes

- Structured per `C:\E156\docs\E156_v0.2_SPEC.md` (7-sentence contract, ≤156 words)
- Primary estimand: HR for stroke or systemic embolism (ITT/mITT)
- All four trial HRs match published source exactly (star-network pass-through)
- Scope: non-valvular AF, higher-dose DOAC arms only
- Ruff 2014 Lancet canonical-set replication
- Net-benefit caveat (Apixaban #1 when bleeding factored) declared in S6 — keep if rewrite preserves clinical honesty
