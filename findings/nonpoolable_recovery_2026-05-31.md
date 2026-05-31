# Non-poolable recovery — 2026-05-31

`validate_living_ma_portfolio.py --local --strict` (exit 0).

## Portfolio movement

| Metric | Before | After | Δ |
|---|---|---|---|
| Non-poolable | 1,082 | **273** | −809 (−75%) |
| Apps that pool (k≥2) | 499 | **1,075** | +576 |
| Single-trial | 570 | 803 | +233 |
| Benchmarked within 10% | 17/18 | 17/19 | +1 app, net-new coverage |

## Root causes fixed

1. **pool_dl HR/counts fall-through** — a present-but-unusable `publishedHR`
   (≤0, e.g. a mislabelled mean difference, or missing CI) shadowed the
   event-count fallback. (+137)
2. **Lite-JSON parser** — `extract_real_data` only understood the flagship
   single-quoted JS-object format; it extracted zero trials from the 794 lite
   `*_AUTO_REVIEW` apps that emit realData as double-quoted JSON. Added a
   JSON-first path. (+~450)
3. **Quote-agnostic regex fallback + brace-matched block** — recovered the
   hybrid blocks (double-quoted data keys mixed with unquoted JS keys like
   `evidence:`), mostly NMA-structured apps. (+81)

Flagship benchmark pools are byte-for-byte unchanged (they hit the regex
fallback); zero benchmark regressions.

## Residual 273 non-poolable (legitimate / out-of-scope)

| Bucket | ~count | Why it stays non-poolable |
|---|---|---|
| Continuous / MD outcomes (≥2 trials) | ~120 | Mean-difference endpoints (e.g. ANTIAMYLOID CDR-SB, CARIPRAZINE PANSS, CGRP migraine-days). The HTML MD engine handles these; the ratio-only Python validator correctly skips them. Would need an MD-pooling path in the validator. |
| Single-trial-with-data | ~110 | Genuinely one trial — not meta-analysable. |
| No realData block | 18 | Narrative / non-quantitative apps. |
| Hybrid still unparsed | ~25 | Network structures the pairwise extractor can't normalise. |

## Data-quality flags surfaced (benchmark mismatches — need source verification, NOT parser bugs)

- **CANGRELOR_PCI** — per-trial `publishedHR` pools to 0.89; app displays 0.81
  (Steg 2013 pooled mITT primary). Outcome-definition mismatch.
- **TEZEPELUMAB_ASTHMA** — pairwise count pool 2.01 vs published rate-ratio
  0.44; per-trial event counts likely swapped or represent a different
  responder definition.
- **BIMEKIZUMAB_PSO** — pool 0.58 vs PASI90 benchmark ~25.7; outcome/direction
  mismatch.

These three are now *visible* because the parser can finally read the apps;
each needs its per-trial counts checked against the source paper.

### Resolution (source-checked 2026-05-31)

- **CANGRELOR_PCI** — DATA VALID. Real CHAMPION-PCI/PLATFORM/PHOENIX counts; the
  per-trial 48 h primary endpoints pool to 0.89, while the 0.81 benchmark is
  Steg 2013's patient-level pooled mITT primary. Fix = clarify the benchmark
  note, not the data.
- **TEZEPELUMAB_ASTHMA** — INVALID POOL. NAVIGATOR carries exacerbation-rate
  counts (4/528 vs 18/531, OR≈0.22, correct) but SOURCE (71/74) and PATH-HOME
  (110/111) carry *responder/completer* counts (OR≫1); SOURCE also has a
  negative "publishedHR" (−13.04 = the MD-in-HR bug). Three incompatible
  outcomes pooled → 2.01. Needs outcome harmonisation or trial exclusion.
- **BIMEKIZUMAB_PSO** — INVALID POOL. BE RADIANT is vs *secukinumab* (active
  comparator); the other arms are placebo. Benchmark 25.69 is placebo PASI90.
  Mixed comparators → meaningless 0.58.

## SYSTEMIC DATA-INTEGRITY FINDING (escalation — needs a decision)

The benchmark probe led to a portfolio-wide scan. Beyond the 8 Sentinel
`P0-denominator-logic` BLOCKs, **154 apps have arithmetically impossible counts
(tE>tN or cE>cN)** in their source realData, e.g. ABATACEPT_PSA NCT00534313
tE=57 > tN=43. A further 165 apps carry implausible N≤5 denominators. These are
pre-existing extraction corruptions (NOT introduced by the parser fix; the
parser merely made them visible).

Worse, several Sentinel-flagged trials are the **wrong trial type** — ctgov
confirms they are single-arm phase I/II studies, not the RCTs the apps claim:
  - NCT01959698 (CARFILZOMIB_REL) — single-arm phase 1, N=29
  - NCT01902173 (DABRAFENIB + TRAMETINIB melanoma, 2 apps) — single-arm ph1/2, N=27
  - NCT03332498 (PEMBROLIZUMAB CRC, 2 apps) — pembro+ibrutinib single-arm ph1/2, N=40
  - NCT01761292 (GIVINOSTAT_DMD) — single-arm ph1/2, N=20
The 6-gate "audit-first" pipeline was meant to exclude non-RCTs; these slipped
through and the FULL clones fabricated 2-arm counts on top.

These cannot be repaired by patching numbers (no control arm exists to patch
to) and there is no local AACT snapshot. Recommended remediation (pending
decision): quarantine the single-arm/wrong-trial apps; null the impossible
counts on the remainder so they read as honestly data-unavailable rather than
wrongly poolable; schedule a source-backed re-extraction (AACT or ctgov API)
for the salvageable RCTs.
