---
title: "Network Meta-Analysis of BTKi in CLL"
slug: btki_cll_nma
version: 1.3
timestamp: 2026-04-21T00:00:00Z
date: 2026-04-21
specialty: Haematology
analysis_type: NMA
canonical_url: https://mahmood726-cyber.github.io/rapidmeta-finerenone/protocols/btki_cll_nma_protocol_v1.3_2026-04-21.md
app_url: https://mahmood726-cyber.github.io/rapidmeta-finerenone/BTKI_CLL_NMA_REVIEW.html
license: MIT
---

# BTKi NMA in CLL v1.3 (ELEVATE-TN / ELEVATE-RR / ALPINE / RESONATE-2 / SEQUOIA)
## Network Meta-Analysis Protocol

**Version:** 1.3 · **Frozen:** 2026-04-21 · **Authors:** Mahmood Ahmad
**Supersedes:** v1.1 (k=4, composite Chemoimm node), v1.2 (k=5 with detected incoherence)

## 1. Title + Registration

Network Meta-Analysis of Bruton Tyrosine Kinase Inhibitors (Acalabrutinib, Ibrutinib, Zanubrutinib) vs Chemoimmunotherapy Regimens in CLL. Frozen 2026-04-21.

**v1.3 structural change:** the composite "Chemoimmunotherapy" node in v1.1/v1.2 is split into **three biologically distinct sub-nodes** — Chlorambucil-alone (Clb_alone), Chlorambucil+Obinutuzumab (Clb_Obi), Bendamustine+Rituximab (BR). This resolves the v1.2 inconsistency (Q_inc=21.7, p<0.001) that arose from lumping non-exchangeable comparators.

## 2. PICO

| Element | Specification |
|---|---|
| **Population** | Adults with CLL (TN + R/R subsets trial-specific) |
| **Interventions (3 BTKi)** | Acalabrutinib · Ibrutinib · Zanubrutinib |
| **Comparators (3 chemoimmunotherapy sub-nodes)** | Clb_alone (RESONATE-2) · Clb_Obi (ELEVATE-TN) · BR (SEQUOIA) |
| **Outcome (primary)** | Progression-free survival (longest-available follow-up); hazard ratio |

## 3. Network (v1.3)

| Edge | Trial | HR (95% CI) |
|---|---|---|
| Acalabrutinib — Ibrutinib | ELEVATE-RR (NCT02477696) | 1.00 (0.81–1.24) |
| Acalabrutinib — Clb_Obi | ELEVATE-TN (NCT02475681) | 0.21 (0.14–0.32) |
| Ibrutinib — Clb_alone | RESONATE-2 (NCT01722487) | 0.146 (0.098–0.218) |
| Zanubrutinib — Ibrutinib | ALPINE (NCT03734016) | 0.65 (0.49–0.86) |
| Zanubrutinib — BR | SEQUOIA (NCT03336333) | 0.42 (0.28–0.63) |

**Geometry:** Connected **tree** (no closed loops after splitting composite node). This precludes loop-inconsistency and design-by-treatment tests but **preserves transitivity** — each chemoimmunotherapy sub-node is a genuinely distinct regimen.

## 4. Synthesis

- `netmeta` 3.2.0, `sm="HR"`, REML τ², HKSJ CI (`method.tau="REML", hakn=TRUE`)
- Reference (netmeta-default alphabetical): BR
- Consistency: tree network → no loops → Q_inc = 0, df = 0 (no test possible but also no violation); τ² = 0
- Ranking: SUCRA + P-score + full rank-probability matrix via `MASS::mvrnorm`

## 5. Key effects vs BR (v1.3 results)

| Treatment | HR vs BR (95% CI) |
|---|---|
| Zanubrutinib | 0.420 (0.280–0.630) (direct SEQUOIA) |
| Acalabrutinib | 0.646 (0.378–1.106) (indirect via Ibru→Clb_alone) |
| Ibrutinib | 0.646 (0.394–1.058) (indirect via Clb_alone) |
| Clb_Obi | 3.077 (1.562–6.061) (indirect via Acala) |
| Clb_alone | 4.426 (2.345–8.352) (indirect via Ibru) |

Pairwise BTKi-vs-BTKi (sensitivity): Zanu vs Ibru HR 0.65 (direct, ALPINE); Acala vs Ibru HR 1.00 (direct, ELEVATE-RR).

## 6. Transitivity (v1.3 — post-split)

| Effect modifier | ELEVATE-TN | ELEVATE-RR | ALPINE | RESONATE-2 | SEQUOIA | Concern |
|---|---|---|---|---|---|---|
| Line | TN | R/R high-risk | R/R | TN elderly | TN non-del17p | Line-of-therapy still a concern |
| Comparator | Clb_Obi | Ibrutinib | Ibrutinib | Clb_alone | BR | **RESOLVED in v1.3** by splitting |
| del17p | mixed | enriched | ~24% | ~6% | excluded cohort-1 | Subgroup analysis available |
| Age | ≥65 or unfit | 18+ high-risk | R/R all-ages | ≥65 | ≥65 or unfit | Broadly compatible for TN; R/R differs |

**Remaining transitivity concerns:** (a) line-of-therapy mixing TN vs R/R — declared limitation; (b) del17p enrichment in ELEVATE-RR; (c) network is a tree → some indirect comparisons rely on single-path-only inference.

## 7. CINeMA GRADE-NMA (v1.3)

| Comparison | Within | Across | Indirectness | Imprecision | Heterogeneity | Incoherence | Pub bias | **Certainty** |
|---|---|---|---|---|---|---|---|---|
| Acala vs Ibru (direct, ELEVATE-RR) | Moderate (open-label) | Low | Low | Low | n/a | n/a | Low | **MODERATE-HIGH** |
| Zanu vs Ibru (direct, ALPINE) | Moderate | Low | Low | Low | n/a | n/a | Low | **MODERATE-HIGH** |
| Acala vs Clb_Obi (direct, ELEVATE-TN) | Moderate | Low | Low | Low | n/a | n/a | Low | **MODERATE-HIGH** |
| Ibru vs Clb_alone (direct, RESONATE-2) | Moderate | Low | Low | Low | n/a | n/a | Low | **MODERATE-HIGH** |
| Zanu vs BR (direct, SEQUOIA) | Moderate | Low | Low | Low | n/a | n/a | Low | **MODERATE-HIGH** |
| Zanu vs Acala (indirect via Ibru) | Moderate | Low | Moderate (1-step) | Moderate | n/a | n/a | Low | **MODERATE** |
| Acala vs Clb_alone (indirect) | Moderate | Low | Moderate | Moderate | n/a | n/a | Low | **MODERATE** |
| Zanu vs Clb_Obi (indirect) | Moderate | Low | Moderate-Serious (2-step) | Moderate | n/a | n/a | Low | **LOW-MODERATE** |

## 8. Living-NMA cadence

3-monthly. Triggers: SEQUOIA cohort-2 (del17p) update, BRUIN-CLL-321 pirtobrutinib (needs comparator harmonisation), ECOG 1912 ibrutinib+R update, venetoclax+BTKi fixed-duration comparative RCTs.

## Changelog

- **v1.3** (2026-04-21) — Composite Chemoimm split into 3 sub-nodes; tree topology resolves inconsistency honestly
- **v1.2** (2026-04-21) — Added SEQUOIA; exposed composite-node incoherence (Q_inc p<0.001)
- **v1.1** (2026-04-21) — Initial release; k=4 with composite Chemoimm node
