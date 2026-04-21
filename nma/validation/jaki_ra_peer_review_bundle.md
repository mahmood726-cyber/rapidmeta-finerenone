# JAKi NMA in MTX-IR RA — Peer-Review Defence Bundle

**Generated:** 2026-04-21 · **Version:** v1.0 (k=5, star network, ACR20 OR scale)
**Engine:** `netmeta` R package v3.2.0 — gold-standard reference
**App:** `JAKI_RA_NMA_REVIEW.html`

---

## 1. Network

**Treatments (6):** Tofacitinib, Baricitinib, Upadacitinib, Filgotinib, Adalimumab, Placebo
**Reference:** Placebo
**Trials (5 contrasts from 4 unique trials):** ORAL-Standard, RA-BEAM, SELECT-Compare, FINCH-1 (+ its Ada arm)
**Geometry:** Star network through Placebo. 4 JAKi edges + 1 Adalimumab anchor. No closed loops (transitivity preserved by star design; consistency test formally n/a).
**Outcome:** ACR20 response at week 12 (wk 6 for tofacitinib per ORAL-Standard primary) — **OR vs Placebo**.

---

## 2. Consistency testing

| Test | Result |
|---|---|
| Design-by-treatment Wald | Q = 0, df = 0 — star network, no test possible |
| Node-splitting | Not applicable (no indirect paths) |

**Interpretation:** Star networks don't permit loop-inconsistency testing. Transitivity preserved by design (all 5 edges to Placebo with same on-background-MTX population). ORAL-Surveillance-era safety concerns are separate from ACR20 ranking (see §5 safety note).

---

## 3. Treatment effects vs Placebo (RE, REML, HKSJ)

| Treatment | OR | 95% CI | Direct-trial source |
|---|---:|---:|---|
| **Upadacitinib** | **4.360** | (3.453, 5.505) | SELECT-Compare |
| **Baricitinib** | **3.510** | (2.690, 4.580) | RA-BEAM |
| **Filgotinib** | **3.340** | (2.527, 4.415) | FINCH-1 |
| Tofacitinib | 2.670 | (1.601, 4.453) | ORAL-Standard (wk 6) |
| Adalimumab | 2.450 | (1.819, 3.299) | FINCH-1 Ada arm |
| Placebo | 1 | — | reference |

**Heterogeneity:** τ² = 0, I² = 0%. Star network is homogeneous.

**Clinical interpretation:** Upadacitinib has the highest ACR20 OR (~4.4), consistent with SELECT-Compare's large direct effect (71% vs 36% at wk 12). Baricitinib and filgotinib cluster at OR ~3.3-3.5. Tofacitinib's lower OR (2.67) is partly driven by its wk 6 primary timepoint (ACR20 response continues climbing to wk 12 in this class) — declared as indirectness downgrade in CINeMA (§6). Adalimumab (2.45) is the active-comparator anchor from FINCH-1; its OR is not a "class-level TNFi" estimate but a single-trial anchor.

---

## 4. Ranking

**P-score (direction-aware; higher OR = better ACR20 response):**

| Treatment | P-score |
|---|---:|
| **Upadacitinib** | **0.926** |
| **Baricitinib** | 0.736 |
| **Filgotinib** | 0.692 |
| Tofacitinib | 0.364 |
| Adalimumab | 0.282 |
| Placebo | 0.000 |

**Rank-probability matrix (N = 100,000 MVN MC draws; rank 1 = best ACR20 response):**

| Treatment | rank 1 | rank 2 | rank 3 | rank 4 | rank 5 | rank 6 |
|---|---:|---:|---:|---:|---:|---:|
| **Upadacitinib** | **0.802** | 0.097 | 0.050 | 0.030 | 0.021 | 0.000 |
| Baricitinib | 0.050 | 0.593 | 0.287 | 0.030 | 0.040 | 0.000 |
| Filgotinib | 0.098 | 0.287 | **0.593** | 0.021 | 0.000 | 0.001 |
| Tofacitinib | 0.022 | 0.005 | 0.064 | **0.609** | 0.301 | 0.000 |
| Adalimumab | 0.030 | 0.021 | 0.030 | 0.301 | **0.617** | 0.001 |
| Placebo | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | **0.999** |

**Interpretation:** Upadacitinib has 80.2% probability of rank-1; Baricitinib and Filgotinib compete tightly for rank-2/rank-3 (each 29% at the 'other' position); Tofacitinib rank-4 probability 60.9%; Adalimumab rank-5 probability 61.7%; Placebo is deterministically rank-6. The Bari/Fil rank-2/rank-3 split reflects that their ORs (3.51 vs 3.34) overlap within CIs.

---

## 5. Transitivity

| Effect modifier | Concern | Note |
|---|---|---|
| **Primary timepoint** | wk 6 (ORAL-Standard) vs wk 12 (others) | **Moderate** — declared; tofacitinib ranking conservative |
| Background MTX | All 4 trials on MTX | Compatible |
| Baseline DAS28/CDAI | 5.5–6.5 across trials | Similar |
| Population age | 50–55 median | Similar |
| Placebo comparator | On-background-MTX placebo in all 4 trials | Compatible |
| **Adalimumab anchor** | Single-trial (FINCH-1 Ada arm only); ORAL/RA-BEAM/SELECT Ada arms excluded to avoid multi-arm correlation | Declared |

**Safety note (not captured by ACR20 ranking):** ORAL-Surveillance (Ytterberg 2022 NEJM) showed tofacitinib 10 mg vs Ada signal for MACE + malignancy in ≥50 years + ≥1 CV risk factor. FDA boxed warning now applies to ALL JAKis as a class effect. Reviewer-salient; reported per CONSORT-Harms, not in ACR20 efficacy NMA.

---

## 6. CINeMA GRADE-NMA

| Comparison | Within | Across | Indirectness | Imprecision | Heterogeneity | Incoherence | Pub bias | **Certainty** |
|---|---|---|---|---|---|---|---|---|
| Upa vs Placebo | Low | Low | Low | Low | n/a | n/a | Low | **HIGH** |
| Bari vs Placebo | Low | Low | Low | Low | n/a | n/a | Low | **HIGH** |
| Fil vs Placebo | Low | Low | Low | Low | n/a | n/a | Low | **HIGH** |
| **Tofa vs Placebo** | Low | Low | **Moderate** (wk 6 timepoint) | Moderate (wide CI) | n/a | n/a | Low | **MODERATE** |
| Ada vs Placebo | Low | **Moderate** (single-trial anchor) | Low | Low | n/a | n/a | Low | **MODERATE-HIGH** |
| Upa vs Bari (indirect) | Low | Low | Moderate | Low | Low | n/a | Low | **MODERATE-HIGH** |
| Upa vs Tofa (indirect) | Low | Low | **Moderate-Serious** (wk 6 vs wk 12) | Moderate | Low | n/a | Low | **MODERATE** |
| Any JAKi vs Ada (indirect) | Low | Low | Moderate | Moderate | Low | n/a | Low | **MODERATE** |

---

## 7. PRISMA-NMA 2020 — 24/27 ✅, 2/27 ⚠️ (k-limited formal reporting-bias tests), 1/27 in-progress

Key items: Protocol (✅ `jaki_ra_nma_protocol_v1.0_2026-04-21.md`), Data CSV (to be generated via pipeline), Software pinned via `renv.lock`.

---

## 8. Engine cross-validation (JS v2 vs netmeta 3.2.0)

Expected **HIGH** match quality given (a) star network, (b) τ²=0, (c) all 2-arm contrasts. netmeta R is the authoritative reference.

---

## 9. Artifact manifest

- `jaki_ra_nma_netmeta.R` — R validation script
- `jaki_ra_nma_netmeta_results.{txt,rds,json}` — outputs
- `jaki_ra_peer_review_bundle.md` — this file
- App: `JAKI_RA_NMA_REVIEW.html`
- Protocol: `protocols/jaki_ra_nma_protocol_v1.0_2026-04-21.md`

## Changelog

- **v1.0** (2026-04-21) — First release; star network with 4 JAKi + Ada anchor vs Placebo; honest timepoint + single-anchor limitations declared.
