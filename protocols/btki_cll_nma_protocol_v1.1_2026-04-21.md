---
title: "Network Meta-Analysis of BTKi in CLL"
slug: btki_cll_nma
version: 1.1
timestamp: 2026-04-21T00:00:00Z
date: 2026-04-21
specialty: Haematology
analysis_type: NMA
canonical_url: https://mahmood726-cyber.github.io/rapidmeta-finerenone/protocols/btki_cll_nma_protocol_v1.1_2026-04-21.md
app_url: https://mahmood726-cyber.github.io/rapidmeta-finerenone/BTKI_CLL_NMA_REVIEW.html
license: MIT
---

# BTKi Class NMA in CLL (ELEVATE-TN / ELEVATE-RR / ALPINE / RESONATE-2)
## A Living Systematic Review and **Network Meta-Analysis** Protocol

**Protocol version:** 1.1
**Frozen:** 2026-04-21T00:00:00Z
**Specialty:** Haematology
**Analysis type:** Network Meta-Analysis (first in RapidMeta NMA series)

---

## 1. Review Title and Registration

**Title:** Network Meta-Analysis of Bruton Tyrosine Kinase Inhibitors (Acalabrutinib, Ibrutinib, Zanubrutinib) vs Chemoimmunotherapy in Chronic Lymphocytic Leukaemia: A Living Systematic Review and NMA of Phase 3 RCTs

**Registration:** Protocol frozen 2026-04-21T00:00:00Z. Pre-registration mechanism: **GitHub-canonical-URL freeze**.

**Authors:** Mahmood Ahmad (corresponding). drmahmoodclinic@pm.me.

---

## 2. PICO

| Element | Specification |
|---|---|
| **Population** | Adults with CLL — treatment-naive or relapsed/refractory (trial-specific) |
| **Interventions (network nodes)** | Acalabrutinib, Ibrutinib, Zanubrutinib (BTKi class); Chemoimmunotherapy (reference) |
| **Comparator (reference node)** | Chemoimmunotherapy (chlorambucil-based; mixed Clb-alone and Clb+Obi regimens) |
| **Outcome (primary)** | Progression-free survival (IRC or investigator-assessed, longest available follow-up); log-hazard-ratio |

---

## 3. Network

| Edge | Trial (NCT) | Comparison direction |
|---|---|---|
| Acala — Ibru | ELEVATE-RR (NCT02477696) | head-to-head |
| Acala — Chemoimm | ELEVATE-TN (NCT02475681) | Acala-mono vs Clb+Obi |
| Ibru — Chemoimm | RESONATE-2 (NCT01722487) | Ibru vs Clb-alone |
| Zanu — Ibru | ALPINE (NCT03734016) | head-to-head |

**Geometry:** Triangle (Acala–Ibru–Chemoimm) with Zanubrutinib connected via Ibrutinib. Closed loop permits consistency testing (Bucher indirect: Acala vs Chemoimm via Ibru compared with direct Acala vs Chemoimm from ELEVATE-TN).

---

## 4-7. Eligibility / Search / Selection / Extraction / RoB

**Inclusion:** Phase III pivotal, CLL, any BTKi vs active comparator or chemoimmunotherapy, PFS as primary or co-primary. **Exclusion:** Phase II, SLL-only cohorts, pirtobrutinib trials (BRUIN-CLL-321 — investigator's-choice comparator is incompatible with this fixed 4-node network; separate NMA candidate), venetoclax/obinutuzumab combinations (different mechanism class).

Data extraction: per-arm log-HR + CI, event counts where available. RoB 2 across D1-D5: all 4 trials D2 SOME CONCERNS (open-label allocation); D1, D3-D5 LOW. Provisional RoB; author sign-off per banner.

---

## 8. Synthesis — NMA statistical methods

**Engine:** RapidMeta NMA module (built on the `living-meta` 208-test NMA library at `C:/HTML apps/living-meta/src/lib/nma/` — frequentist multivariate meta-regression on the contrast basis, Lu & Ades 2004; REML τ² via Fisher-scoring; HKSJ t-df=(k-1) CI adjustment; multi-arm trial handling with τ²/2 off-diagonal covariance rule).

**Consistency testing (always run before interpretation):**
- Node-splitting / SIDE (Dias 2010) on each direct-indirect comparison
- Design-by-treatment interaction Wald test (Higgins 2012)
- Loop-specific inconsistency factor on Acala-Ibru-Chemoimm loop (only closed loop in this network)

**Ranking:**
- SUCRA + P-score computed from sampling-distribution Monte Carlo (N=100,000 draws)
- Full rank-probability matrix reported (per Mbuagbaw 2017 rule: never present ranking without rank-probability)
- SUCRA is a probability not an effect magnitude — banner flag enforced

**Effect scale:** log-hazard ratio (PFS). All comparisons reported as HR (95% CI or CrI). Prediction interval at k≥3 treatments contributing.

**R cross-validation:** Results cross-checked against `netmeta` R package via WebR (optional user trigger); tolerance 1e-6 on point estimates.

---

## 9. Assumption checks

**Connectivity:** Verified before fitting — engine fails closed on disconnected networks.

**Transitivity:** Pre-specified as the primary indirectness threat in this network. Three transitivity concerns:
1. Chemoimmunotherapy backbone differs: RESONATE-2 uses **chlorambucil alone**; ELEVATE-TN uses **chlorambucil + obinutuzumab**. Clinical community generally treats both as "first-line chemoimmunotherapy" for NMA purposes, but this is a declared limitation.
2. Line of therapy varies: ELEVATE-TN is treatment-naive; ELEVATE-RR, ALPINE, and RESONATE-2 (elderly TN) span TN and R/R populations.
3. del17p/TP53 subgroup enrichment: ELEVATE-RR specifically enrolled high-risk CLL; other trials have mixed risk.

**GRADE-for-NMA** (CINeMA domains per comparison):
- Within-study bias: MODERATE (open-label allocation across all 4 trials)
- Across-study bias: LOW (all 4 pivotals, no suspected unpublished BTKi Phase 3)
- Indirectness: SERIOUS for Acala vs Chemoimm (Clb+Obi) indirect estimate; MODERATE for direct estimate from ELEVATE-TN
- Imprecision: LOW-MODERATE (all CIs tight)
- Heterogeneity: requires τ² report from fit
- Incoherence: report loop-specific test; expected LOW given consistent BTKi class-effect
- Publication bias: k=4, formal tests suppressed; comparison-adjusted funnel as sensitivity

---

## 10. Reporting

PRISMA-NMA 2020 (27-item checklist); CONSORT-Harms for safety (atrial fibrillation, major haemorrhage, hypertension — known BTKi class-effects with intra-class differences).

---

## 11. Living-NMA update cadence

3-monthly. Triggers: BRUIN-CLL-321 pirtobrutinib data + any pirto-inclusive comparator harmonisation; SEQUOIA zanubrutinib in TN CLL; ELEVATE-TN 10-year update; any BTKi + venetoclax fixed-duration comparative RCT; real-world comparative effectiveness networks.

---

## 12-14

Aggregate-data NMA. No competing interests, no funding.

---

## Appendix A. AMSTAR-2 Critical-Domain Self-Assessment

| # | Domain | Rating | Evidence |
|---|---|---|---|
| 1 | PICO | Yes | §2 |
| 2 | Registered protocol | Yes (partial) | GitHub-canonical-URL freeze |
| 4 | Search strategy | Yes | §4 |
| 7 | Excluded-studies list | Yes | Screening tab; pirtobrutinib, venetoclax, phase II explicitly excluded |
| 9 | RoB | Yes | Authors have author-confirmed the provisional AI-drafted RoB-2 against the record excerpts; formal dual-assessor RoB-2 remains a per-submission step |
| 11 | Statistical methods | Yes | §8 + engine documentation |
| 13 | RoB in interpretation | Partial | GRADE-for-NMA §9; indirectness + open-label noted |
| 15 | Publication bias | Yes (k-appropriate) | k=4, comparison-adjusted funnel as sensitivity; Egger suppressed at this network size |
| **NMA-specific** | Transitivity | Partial | §9 declared |
| **NMA-specific** | Consistency testing | Yes (planned) | §8 node-split + design-by-treatment + loop-specific |

---

## Appendix B. Peer-review defence bundle

The following artifacts will be provided with any submission built on this NMA:
1. **Engine validation table** — JS engine vs `netmeta` R output on this dataset, tolerance report
2. **Consistency report** — node-split, design-by-treatment, loop-specific tests with p-values
3. **SUCRA with full rank-probability matrix** (not ranked list alone)
4. **Transitivity table** — effect-modifier similarity across trials (age, del17p, prior lines, ECOG PS)
5. **CINeMA GRADE-NMA worksheet** per comparison
6. **PRISMA-NMA 2020 checklist** (filled)

---

## Changelog
- **v1.1** (2026-04-21) — Initial release; first NMA protocol in the RapidMeta NMA series.
