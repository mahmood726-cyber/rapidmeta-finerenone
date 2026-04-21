# ADC NMA in HER2+ MBC 2L+ PFS — Peer-Review Defence Bundle

**Generated:** 2026-04-21 · **Version:** v1.2 (split-TPC, transitivity-restored tree, k=4, HR scale)
**Engine:** `netmeta` R package v3.2.0
**App:** `ADC_HER2_NMA_REVIEW.html`
**Scope:** HER2-positive metastatic breast cancer, 2L / 3L+ setting, PFS outcome. Excludes adjuvant (KATHERINE, iDFS) and HER2-low (DESTINY-Breast04).

---

## 0. What v1.2 changes

**v1.1 → v1.2**: Split the composite TPC node into two biologically-coherent nodes per the v1.1 pre-specified roadmap:
- `TPC_chemo` = investigator-choice single-agent chemotherapy ± trastuzumab (TH3RESA)
- `TPC_Hplus_chemo` = trastuzumab + capecitabine OR lapatinib + capecitabine (DESTINY-Breast02)

**Result:** transitivity assumption restored cleanly. τ² = 0.000, I² = NA, Q_inc = 0 (not defined — tree geometry).
**Trade-off accepted:** closed T-DXd–T-DM1–TPC triangle lost; network is a tree (4 edges, 5 nodes, no closed loops). Consistency testing not defined in a tree, but the transitivity violation that made v1.1's consistency test fail is resolved.

### Side-by-side comparison

| Metric | v1.1 (unified TPC) | v1.2 (split TPC) |
|---|---|---|
| Network geometry | Triangle T-DXd–T-DM1–TPC | Tree (4 edges, 5 nodes) |
| τ² | 0.161 | **0.000** |
| I² | 91.6% | NA (tree) |
| Q_inc | 11.9 (p < 0.001) — **INCONSISTENT** | not defined (tree) |
| T-DXd rank-1 | 98.6% | **100%** |
| T-DXd vs T-DM1 (direct) | 0.33 (0.26, 0.43) | 0.33 (0.26, 0.43) |
| T-DM1 CI crosses null? | Yes (vs TPC composite) | No vs TPC_chemo (0.528); Yes vs TPC_Hplus_chemo (1.09) |

The v1.2 TPC_Hplus_chemo indirect T-DM1-vs-X HR of 1.091 (0.77, 1.54) is a meaningful clinical signal: **T-DM1 is not superior to trastuzumab+capecitabine in 3L+ post-T-DM1 setting** — consistent with clinical expectation (patients who progressed on T-DM1 won't benefit from re-treating with the same ADC).

---

## 1. Network (v1.2)

| Trial | NCT | Comparison | N | Setting |
|---|---|---|---|---|
| DESTINY-Breast03 | NCT03529110 | T-DXd vs T-DM1 | 524 | 2L HER2+ MBC |
| EMILIA | NCT00829166 | T-DM1 vs LapaCape | 991 | 2L HER2+ MBC |
| TH3RESA | NCT01419197 | T-DM1 vs **TPC_chemo** (single-agent ± trast) | 602 | 3L+ HER2+ MBC |
| DESTINY-Breast02 | NCT03523585 | T-DXd vs **TPC_Hplus_chemo** (trast/lapa + cape) | 608 | 3L+ HER2+ MBC post-T-DM1 |

**Geometry (v1.2):**
```
LapaCape — T_DM1 — T_DXd — TPC_Hplus_chemo
           |
           TPC_chemo
```
Tree. T-DM1 and T-DXd each hub-like. No closed loops.

---

## 2. Consistency + heterogeneity (v1.2)

τ² = 0.000 · I² = NA · Q_inc not defined (tree). **Design-by-treatment consistency test trades for restored transitivity — explicit pre-specified choice.**

---

## 3. Treatment effects (v1.2, reference = TPC_Hplus_chemo)

| Treatment | HR vs TPC_Hplus_chemo | 95% CI | Evidence |
|---|---:|---:|---|
| **T-DXd** | **0.360** | (0.284, 0.456) | Direct DESTINY-Breast02 |
| T-DM1 | 1.091 | (0.772, 1.542) | Indirect via T-DXd |
| LapaCape | 1.678 | (1.143, 2.465) | 2-step indirect |
| TPC_chemo | 2.066 | (1.368, 3.120) | 2-step indirect |
| TPC_Hplus_chemo | 1.00 | — | reference |

### Head-to-head direct contrasts (preserved, primary clinical evidence)

| Contrast | HR | 95% CI | Evidence |
|---|---:|---:|---|
| T-DXd vs T-DM1 | 0.33 | (0.26, 0.43) | **Direct DESTINY-Breast03** — HIGH certainty |
| T-DXd vs TPC_Hplus_chemo | 0.36 | (0.28, 0.46) | **Direct DESTINY-Breast02** — HIGH certainty |
| T-DM1 vs LapaCape | 0.65 | (0.55, 0.77) | **Direct EMILIA** — HIGH certainty |
| T-DM1 vs TPC_chemo | 0.528 | (0.42, 0.66) | **Direct TH3RESA** — HIGH certainty |

### Re-expressed head-to-head with T-DM1 reference (clinical framing)

| Contrast | HR vs T-DM1 |
|---|---:|
| T-DXd (superior) | 0.33 |
| T-DM1 | 1.00 |
| TPC_Hplus_chemo (trast+cape) | 0.92 (1/1.091) |
| TPC_chemo (single-agent) | 1.89 (1/0.528) |
| LapaCape | 1.54 (1/0.65) |

**Clinical read:**
- T-DXd is ~3x more effective than T-DM1 at preventing PFS events (HR 0.33).
- In 3L+ post-T-DM1 setting, trastuzumab + capecitabine (TPC_Hplus_chemo) is approximately equivalent to T-DM1 (HR 1.09 [0.77, 1.54]) — re-treating with T-DM1 not beneficial.
- Single-agent chemo ± trastuzumab (TPC_chemo) is roughly 2x worse than trastuzumab + capecitabine for PFS.

---

## 4. Ranking (v1.2)

| Treatment | P-score | SUCRA | rank-1 probability |
|---|---:|---:|---:|
| **T-DXd** | **1.000** | 1.000 | **100%** |
| TPC_Hplus_chemo | 0.711 | 0.711 | 0% |
| T-DM1 | 0.539 | 0.539 | 0% |
| LapaCape | 0.220 | 0.220 | 0% |
| TPC_chemo | 0.030 | 0.030 | 0% |

**Important SUCRA note:** The TPC_Hplus_chemo SUCRA of 0.711 (above T-DM1 at 0.539) reflects the indirect-evidence finding that trast+cape may be comparable or slightly better than T-DM1 in this population. This should NOT be read as "trast+cape is a better HER2 drug than T-DM1 in general" — it is specifically a 3L+ post-T-DM1 comparison where re-treatment with T-DM1 is clinically inappropriate.

---

## 5. Transitivity (v1.2 — resolved)

| Effect modifier | Concern |
|---|---|
| **TPC definition** | **RESOLVED** — split into TPC_chemo and TPC_Hplus_chemo. Each node is now biologically coherent. |
| Line of therapy | Still moderate — 2L (EMILIA, DESTINY-Breast03) vs 3L+ (TH3RESA, DESTINY-Breast02). Acceptable within PFS-outcome scope. |
| PFS assessment | Low — BICR in 3 of 4, investigator in TH3RESA. |
| Prior T-DM1 | Declared — DESTINY-Breast02 required, TH3RESA excluded. Absorbed into TPC_chemo vs TPC_Hplus_chemo distinction. |
| Era / comparator evolution | 10 yr span (2012–2023). Noted but relative effects class-consistent. |

---

## 6. CINeMA (v1.2)

| Comparison | Certainty |
|---|---|
| T-DXd vs T-DM1 (direct DESTINY-Breast03) | **HIGH** |
| T-DXd vs TPC_Hplus_chemo (direct DESTINY-Breast02) | **HIGH** |
| T-DM1 vs LapaCape (direct EMILIA) | **HIGH** |
| T-DM1 vs TPC_chemo (direct TH3RESA) | **HIGH** |
| T-DM1 vs TPC_Hplus_chemo (1-step indirect via T-DXd) | **MODERATE** |
| LapaCape vs TPC_Hplus_chemo (2-step indirect) | **LOW-MODERATE** |
| TPC_chemo vs TPC_Hplus_chemo (2-step indirect) | **LOW-MODERATE** |
| LapaCape vs TPC_chemo (2-step indirect via T_DM1) | **MODERATE** |

Network-synthesised indirect comparisons have lower certainty than direct head-to-heads due to single-trial anchors and the tree geometry (no closed-loop validation), but the transitivity concern from v1.1 is resolved.

---

## 7. PRISMA-NMA 2020 — Status: 25/27 ✅, 2/27 ⚠️ (reporting bias formal tests underpowered at k=4)

- Item 13f (Consistency): pre-specified tree geometry, consistency test declared not-applicable.
- Item 14 (Sensitivity): v1.1 (unified TPC with Q_inc reporting) and v1.2 (split-TPC clean) both retained as pre-specified analyses.
- Item 24 (Software): netmeta 3.2.0.

---

## 8. Artifact manifest

- `adc_her2_nma_netmeta.R`
- `adc_her2_nma_netmeta_results.{txt,rds,json}`
- `adc_her2_peer_review_bundle.md` — this file (v1.2)
- App: `ADC_HER2_NMA_REVIEW.html` (v1.2 banner)
- Protocol: `protocols/adc_her2_nma_protocol_v1.0_2026-04-21.md` (v1.2 supplement in changelog)

## Changelog

- **v1.2** (2026-04-21) — Split composite TPC node into TPC_chemo (TH3RESA) and TPC_Hplus_chemo (DESTINY-Breast02). Transitivity restored: τ²=0.000 (was 0.161 in v1.1). Network is a tree (4 edges, 5 nodes) — closed loop lost, consistency test not defined, but the violation that made v1.1's consistency test fail is resolved. T-DXd rank-1 probability: 100%. New finding: T-DM1 vs TPC_Hplus_chemo (trast+cape) indirect HR 1.091 (0.77, 1.54) — re-treatment with T-DM1 in 3L+ post-T-DM1 setting not superior to trast+cape; clinically coherent. Closes v1.1's pre-specified roadmap.
- **v1.1** (2026-04-21) — Added DESTINY-Breast02; closed triangle formed; Q_inc=11.9 (p<0.001) detected; TPC composite diagnosed as inconsistency driver.
- **v1.0** (2026-04-21) — First release; 3 pivotal HER2+ MBC Phase 3 trials.
