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
