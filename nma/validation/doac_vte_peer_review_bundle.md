# DOAC Class NMA vs LMWH/Warfarin for Acute VTE Treatment — Peer-Review Defence Bundle

**Generated:** 2026-04-21 · **Version:** v1.0 (k=4, LMWH/Warfarin-star, HR scale)
**Engine:** `netmeta` R package v3.2.0
**App:** `DOAC_VTE_NMA_REVIEW.html`
**Outcome:** Recurrent VTE or VTE-related death (trial-primary composite).

---

## 1. Network

| Trial | Drug | Regimen | N | Follow-up |
|---|---|---|---:|---|
| RE-COVER | Dabigatran 150 BID | LMWH lead-in then DOAC | 2539 | 6 mo |
| EINSTEIN-DVT | Rivaroxaban 15 BID → 20 QD | Single-drug no lead-in | 3449 | 3–12 mo |
| AMPLIFY | Apixaban 10 BID → 5 BID | Single-drug no lead-in | 5395 | 6 mo |
| HOKUSAI-VTE | Edoxaban 60 QD | LMWH lead-in then DOAC | 8240 | 12 mo |

**Geometry:** LMWH/Warfarin-star network. No head-to-head DOAC trials.

---

## 2. Results

| Drug | HR vs LMWH/Warfarin | 95% CI | Published |
|---|---:|---:|---|
| **Rivaroxaban** | **0.68** | (0.44, 1.04) | EINSTEIN-DVT |
| **Apixaban** | 0.84 | (0.60, 1.18) | AMPLIFY |
| **Edoxaban** | 0.89 | (0.70, 1.13) | HOKUSAI-VTE |
| **Dabigatran** | 1.10 | (0.65, 1.85) | RE-COVER |
| LMWH→Warfarin | 1.00 | — | (shared control) |

**Clinical interpretation:** All 4 DOACs met non-inferiority vs LMWH→warfarin for recurrent VTE. No DOAC statistically superior on recurrent VTE alone. **Rivaroxaban point estimate is the lowest but CI crosses 1.** Clinical choice depends on bleeding profile (AMPLIFY apixaban showed the most favourable major-bleeding outcome — declared separately) and regimen preference (single-drug vs LMWH lead-in).

τ² = 0.000 — class-consistent.

---

## 3. Ranking (stroke/SE-outcome-only — not net benefit)

| Drug | P-score / SUCRA |
|---|---:|
| Rivaroxaban | 0.798 |
| Apixaban | 0.614 |
| Edoxaban | 0.572 |
| Dabigatran | 0.356 |
| LMWH/Warfarin | 0.160 |

As with DOAC-AF, net-benefit ranking differs when major bleeding is factored: AMPLIFY apixaban major bleeding RR 0.31 vs warfarin — typically places apixaban rank-1 in net-benefit NMAs.

---

## 4. Transitivity

| Effect modifier | Concern |
|---|---|
| **Regimen design** | Moderate — RE-COVER + HOKUSAI-VTE required LMWH lead-in; EINSTEIN-DVT + AMPLIFY used single-drug initiation. Relative-effect magnitudes should not differ systematically. |
| **Follow-up duration** | Variable (3 mo flexible → 12 mo fixed). Outcome is time-to-event, handled by HR. |
| **Trial comparator** | All used INR-targeted warfarin (2–3) + therapeutic LMWH lead-in. Consistent. |
| **Population** | DVT, PE, or both. Subgroup analyses in each trial found no PE-vs-DVT effect-modification. |

---

## 5. CINeMA

All direct edges: **HIGH** certainty (well-conducted non-inferiority Phase 3 trials, large Ns).

---

## 6. Artifact manifest

- `doac_vte_nma_netmeta.R`
- `doac_vte_nma_netmeta_results.{txt,rds,json}`
- `doac_vte_peer_review_bundle.md`
- App: `DOAC_VTE_NMA_REVIEW.html`
- Protocol: `protocols/doac_vte_nma_protocol_v1.0_2026-04-21.md`

## Changelog

- **v1.0** (2026-04-21) — First release; 4 pivotal DOAC-vs-standard VTE treatment trials; class-level non-inferiority on recurrent VTE; ranking Rivaroxaban > Apixaban > Edoxaban > Dabigatran (SUCRA, recurrent-VTE outcome only). Companion to DOAC_AF_NMA (same drug class, different indication).
