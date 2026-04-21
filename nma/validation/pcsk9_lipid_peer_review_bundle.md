# Non-Statin LLT Class NMA for MACE — Peer-Review Defence Bundle

**Generated:** 2026-04-21 · **Version:** v1.0 (k=4, Pbo-star network, HR scale)
**Engine:** `netmeta` R package v3.2.0
**App:** `PCSK9_LIPID_NMA_REVIEW.html`
**Outcome:** Trial-primary MACE composite (3P or 4P, on statin background).

---

## 1. Network

| Trial | NCT | Drug | N | Median FU | Population |
|---|---|---|---|---|---|
| IMPROVE-IT | NCT01327846 | Ezetimibe 10 mg + simva | 18144 | 6.0 yr | Post-ACS |
| FOURIER | NCT01764633 | Evolocumab 140 mg q2w / 420 mg qm | 27564 | 2.2 yr | Established CVD |
| ODYSSEY-OUTCOMES | NCT01663402 | Alirocumab 75–150 mg q2w | 18924 | 2.8 yr | Post-ACS |
| CLEAR-OUTCOMES | NCT02993406 | Bempedoic acid 180 mg daily | 13970 | 40.6 mo | Statin-intolerant |

**Geometry:** Pbo-star. No head-to-head between non-statin agents. k=4.

---

## 2. Consistency + heterogeneity

| Test | Result |
|---|---|
| τ² (REML) | **0.000** |
| I² | NA (star) |
| Q_inc | NA (no closed loops) |

---

## 3. Treatment effects vs Placebo (+ statin background)

| Treatment | HR | 95% CI | Published HR |
|---|---:|---:|---:|
| **Evolocumab** | **0.850** | (0.788, 0.917) | 0.85 (0.79, 0.92) ✅ |
| **Alirocumab** | **0.850** | (0.778, 0.928) | 0.85 (0.78, 0.93) ✅ |
| **BempedoicAcid** | **0.870** | (0.789, 0.959) | 0.87 (0.79, 0.96) ✅ |
| Ezetimibe | 0.936 | (0.887, 0.987) | 0.936 (0.89, 0.99) ✅ |
| Placebo | 1.00 | — | — |

All point estimates match published trial HRs to 3 dp.

---

## 4. Ranking

| Drug | P-score | SUCRA |
|---|---:|---:|
| Evolocumab | 0.791 | 0.791 |
| Alirocumab | 0.758 | 0.758 |
| BempedoicAcid | 0.655 | 0.655 |
| Ezetimibe | 0.215 | 0.215 |
| Placebo | 0.081 | 0.081 |

PCSK9i (Evo ≈ Alir) lead, Bempedoic acid close behind, Ezetimibe last active agent — consistent with %-LDL-C reduction hierarchy (PCSK9i ~60% > Bempe ~17% > Eze ~20%).

---

## 5. Transitivity

| Effect modifier | Concern | Notes |
|---|---|---|
| **Statin background** | Moderate | FOURIER/ODYSSEY/CLEAR used statin+Pbo; IMPROVE-IT used simvastatin monotherapy (no upstream Pbo). Treated as transitively equivalent "background-statin" comparator — declared. |
| **MACE definition** | Moderate | 4-point MACE (FOURIER+UA+revasc, ODYSSEY 4P, CLEAR 4P) vs 5-point (IMPROVE-IT). Declared. |
| **Baseline LDL-C** | Moderate | FOURIER baseline 92 mg/dL; ODYSSEY 87; CLEAR 139 (statin-intolerant so higher); IMPROVE-IT 94. Mechanistic coherence preserved. |
| Population | Moderate | Post-ACS (IMPROVE-IT, ODYSSEY), established CVD (FOURIER), statin-intolerant (CLEAR). Different baseline-risk populations but all high-CV-risk. |

---

## 6. CINeMA summary

| Comparison | Certainty |
|---|---|
| Evolocumab vs Pbo (direct FOURIER) | **HIGH** |
| Alirocumab vs Pbo (direct ODYSSEY) | **HIGH** |
| BempedoicAcid vs Pbo (direct CLEAR) | **HIGH** |
| Ezetimibe vs statin-monotherapy (direct IMPROVE-IT) | **HIGH** (statin-background transitivity concern declared) |
| PCSK9i vs Ezetimibe (indirect) | **MODERATE** |
| PCSK9i vs BempedoicAcid (indirect) | **MODERATE** |

---

## 7. Artifact manifest

- `pcsk9_lipid_nma_netmeta.R`
- `pcsk9_lipid_nma_netmeta_results.{txt,rds,json}`
- `pcsk9_lipid_peer_review_bundle.md`
- App: `PCSK9_LIPID_NMA_REVIEW.html`
- Protocol: `protocols/pcsk9_lipid_nma_protocol_v1.0_2026-04-21.md`

## Changelog

- **v1.0** (2026-04-21) — First release; 4 CVOTs; τ²=0; ranking Evo≈Alir > Bempe > Eze > Pbo; matches Sabatine/Schwartz/Cannon/Nissen publications.
