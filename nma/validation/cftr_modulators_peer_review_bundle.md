# CFTR Modulator Ladder in F508del Cystic Fibrosis NMA — Peer-Review Defence Bundle

**Generated:** 2026-04-22 · **Version:** v1.0 (k=3, Pbo-star, Mean-Difference scale)
**Engine:** `netmeta` R package v3.2.0
**App:** `CFTR_MODULATORS_NMA_REVIEW.html`
**Outcome:** Absolute change in percent-predicted FEV₁ (ppFEV₁) at week 24 (MD, percentage points).
**Educational focus:** Post-2015 generational ladder of CFTR modulator combinations students will encounter in adult and paediatric CF clinics.

---

## 1. Network

| Trial | NCT | Drug / Mechanism | Genotype | Approved |
|---|---|---|---|---|
| TRAFFIC | NCT01807923 | Lumacaftor 400 mg + Ivacaftor 250 mg BID (corrector + potentiator) | F508del/F508del | 2015 (Orkambi) |
| EVOLVE | NCT02347657 | Tezacaftor 100 mg + Ivacaftor 150 mg (next-gen corrector + potentiator) | F508del/F508del | 2018 (Symdeko) |
| VX18-445-102 | NCT03525444 | Elexacaftor 200 mg + Tezacaftor 100 mg + Ivacaftor 150 mg (triple therapy) | F508del/MF | 2019 (Trikafta) |

**Geometry:** Placebo-star, k=3. No head-to-head modulator-vs-modulator Phase 3 RCT exists (the triple therapy's VX17-445-103 did include a tezacaftor/ivacaftor active-comparator arm but in F/F patients, outside this NMA's network). All effect estimates against active modulators are therefore indirect through the placebo node.

---

## 2. Results

**τ² = NA** (not estimable — k=1 per direct comparison).
**I² = NA** (star topology, no closed loops).
**Q-inconsistency not defined** (no loops to decompose).

| Drug vs Placebo | MD (ppFEV₁, pp) | 95% CI | z | p |
|---|---:|---:|---:|---:|
| **Elex/Tez/Iva** (Trikafta) | **13.80** | (12.15, 15.45) | 16.39 | < 0.0001 |
| Tezacaftor/Iva (Symdeko) | 4.00 | (3.15, 4.85) | 9.22 | < 0.0001 |
| Lumacaftor/Iva (Orkambi) | 2.70 | (1.40, 4.00) | 4.07 | < 0.0001 |
| Placebo | 0.00 | — | — | — |

CIs of the three modulator combinations do not overlap. The generational rank order (triple > dual-tez > dual-luma) is unambiguous on this outcome.

---

## 3. Transitivity

| Modifier | Concern |
|---|---|
| **CFTR genotype population** | **Moderate** — TRAFFIC and EVOLVE enrolled F508del **homozygous** patients (F/F); VX18-445-102 enrolled F508del **heterozygous** patients with a minimal-function (MF) second allele (F/MF). The indirect modulator-vs-modulator contrasts are therefore not within-identical-population. The concern is *mitigated but not eliminated* by VX17-445-103 (outside this network), which gave direct F/F evidence convergent with our indirect estimate — see *Interpretation for students* below. |
| Baseline disease severity | Moderate — mean baseline ppFEV₁ ~61 (TRAFFIC), 60 (EVOLVE), 61 (VX18-445-102). Comparable at the cohort mean, but F/MF patients have traditionally had faster decline. |
| Background therapy | Low — all trials required stable inhaled therapy (bronchodilators, hypertonic saline, dornase alfa, inhaled antibiotics) continued at randomisation. |
| Outcome definition | Low — ppFEV₁ harmonised: absolute change from baseline at week 24 via standardised CF Foundation spirometry protocols in all 3 trials. |
| Age range | Moderate — all adult-predominant (≥12 y); similar age distributions. |
| Era effects | Low-to-moderate — trials span 2015-2019; care standards evolved (e.g. increasing Pseudomonas eradication uptake) but the 4-year gap is short relative to the decade-scale CF-outcome improvements of the 2010s. |

**Interpretation for students — external sanity check of transitivity:** A star network cannot be tested for inconsistency with node-splitting or design-by-treatment interaction (no closed loops). The next-best empirical test of the transitivity assumption is to compare an indirect NMA contrast against *external* direct evidence from a trial outside the network. Here:

- NMA indirect estimate, Elex/Tez/Iva − Tezacaftor/Iva = **+13.80 − +4.00 = +9.80 pp**
- VX17-445-103 (excluded from this network because it was a modulator-vs-modulator head-to-head in F/F patients, not a placebo-controlled trial) reported a between-arm difference of **~10 pp** in F/F patients

These estimates converge within 0.2 pp. The population mismatch (F/F vs F/MF) therefore did *not* appreciably inflate the indirect Trikafta-over-Symdeko magnitude, and the clinical rank-order (triple > dual-tez > dual-luma) is supported from two independent angles. This is the correct pattern for students to learn: *when a star network cannot be internally consistency-tested, look for an external head-to-head trial that plays the role of a consistency witness.*

---

## 4. CINeMA

All 3 direct placebo-vs-modulator edges: **HIGH** certainty (pivotal Phase 3 RCTs with full primary-analysis reporting, harmonised ppFEV₁ outcome, tight CIs, no imprecision or inconsistency concerns).

Indirect modulator-vs-modulator contrasts: **MODERATE** certainty — downgraded once for indirectness due to the F/F-vs-F/MF population mismatch across trial-eligibility criteria. We do *not* downgrade a second level to LOW because the external direct comparison VX17-445-103 (Elex/Tez/Iva vs Tezacaftor/Iva in F/F patients, ~10 pp difference) converges with this NMA's indirect Trikafta-over-Symdeko estimate (+9.80 pp) within 0.2 pp, empirically validating transitivity for at least that contrast.

---

## 5. Changelog

- **v1.0** (2026-04-22) — First release. Third post-2015 respiratory NMA (joining SEVERE_ASTHMA and the earlier two-trial CFTR_CF benchmark). Star topology; F/F-vs-F/MF population mismatch flagged as Moderate transitivity concern. Indirect contrasts at MODERATE CINeMA certainty (downgraded once for indirectness; not twice, because VX17-445-103's external direct F/F evidence converges with the indirect Trikafta-over-Symdeko estimate within 0.2 pp).
