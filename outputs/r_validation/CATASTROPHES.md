# Catastrophic parity failures

Five `outputs/r_validation/*.json` sidecars produce a pooled OR diff > 1.0 vs.
a fresh `metafor` REML+HKSJ re-pool. These are **real divergences**, not
numerical drift — most reflect upstream AACT extraction errors that pulled
the wrong outcome (e.g. adverse-event counts instead of the trial's primary
exacerbation-rate ratio).

Surfaced by `scripts/parity_test_all_sidecars.R` on 2026-05-25.

| Sidecar | max diff | Likely cause |
|---|---|---|
| `COPD_TRIPLE.json` | 8.46 | KRONOS extracted with tE=385/639, cE=619/625 — that's ~99% control event rate, biologically implausible for a 24-week COPD trial; AACT pulled an AE count instead of the primary exacerbation rate-ratio outcome. Re-extract from the published KRONOS exacerbation Δ. |
| `FGFR_INHIBITORS_SOLID.json` | 25.1 | Per-trial yi/vi values appear to mix HR-scale and OR-scale rows; needs scale harmonisation before re-pool. |
| `HEPATITIS_HCV_DAA.json` | 4.20e+24 | Variance estimate near-zero on one trial creates numerical blow-up in random-effects pool. Needs continuity correction or HKSJ floor (`tau2/(k-1) >= 1`). |
| `HPV_DOSE_REDUCTION.json` | 1.03e+05 | One trial's extracted event count is plausibly off by 100x (decimal-place shift). Re-check vs source paper. |
| `MDRTB_BPAL.json` | 10.5 | TB-PRACTECAL extracted counts disagree with published unfavorable-outcome RR; AACT row likely from a different outcome group than the published primary. |

## Action
Each needs **manual per-review re-extraction** from the source paper (not
mechanical fix). Until then, the parity gate continues to log these
failures into `outputs/r_parity/portfolio_failures.txt` without blocking CI.

Recommendation for each:
1. Read the source paper's published primary outcome estimate + CI
2. Replace the trial's yi/vi in the sidecar with `log(HR)` ± `(log(uci) - log(lci))/(2*1.96)`
3. Re-run `scripts/_r_parity_finerenone.R` style for that topic
4. Confirm at 1e-6 then check the FULL_REVIEW page renders consistent pool

## Sidecar regeneration template (R)

```r
# outputs/r_validation/<TOPIC>.json
library(metafor)
trials <- data.frame(
  name = c("<NAME>", ...),
  yi   = log(c(<published_HR>, ...)),
  lci  = log(c(<published_lci>, ...)),
  uci  = log(c(<published_uci>, ...))
)
trials$sei <- (trials$uci - trials$lci) / (2 * qnorm(0.975))
trials$vi  <- trials$sei^2
fit <- rma(yi = yi, vi = vi, data = trials,
           method = "REML", test = "knha")
# Write sidecar with the new pooled fields
```
