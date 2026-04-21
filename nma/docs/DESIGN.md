# RapidMeta NMA Engine — Design

**Version:** 0.1.0 (scaffold)
**Date:** 2026-04-21
**Author:** Mahmood Ahmad

## Purpose

A browser-native Network Meta-Analysis (NMA) engine that complements the 77-app pairwise RapidMeta portfolio. Core mandate: **pass journal-editor peer review** for submission to stats-methods journals (Stats in Med, Res Syn Meth, BMC Med Res Methodol) and the clinical journals that host individual NMAs (NEJM, Lancet, BMJ, JAMA).

## Non-negotiable requirements (peer-review gate)

1. **Statistical correctness**
   - Frequentist NMA via multivariate meta-regression on the contrast basis (Lu & Ades 2004; White 2012 via netmeta)
   - REML τ² (not DL — per `advanced-stats.md` rule: no DL for k<10)
   - HKSJ t-df=(k-1) CI adjustment with `max(1, Q/(k-1))` floor
   - Multi-arm trial handling: off-diagonal covariance = `τ²/2` for shared control
   - Match `netmeta` (R) output to 1e-6 tolerance on point estimates
2. **Consistency testing** (ALWAYS before interpreting)
   - Design-by-treatment interaction (Higgins 2012, Jackson 2014)
   - Node-splitting / SIDE (Dias 2010)
   - Loop-specific inconsistency for closed loops
   - Report global + local inconsistency with p-values
3. **Ranking discipline**
   - SUCRA with credible intervals, NOT point estimates alone
   - P-score as frequentist analog
   - Always plot full rank-distribution, never a ranked list alone
4. **Assumption checking**
   - Connectivity: BFS on the treatment graph — fail closed if disconnected
   - Transitivity: pre-specified similarity check across effect modifiers (age, severity, follow-up)
5. **Heterogeneity**: global τ² + I² + PI (k-appropriate)
6. **Publication bias**: comparison-adjusted funnel (Chaimani 2012) + Egger's for k≥10 comparisons
7. **GRADE for NMA**: CINeMA-style domains (within-study bias, across-study bias, indirectness, imprecision, heterogeneity, incoherence, publication bias) per comparison
8. **PRISMA-NMA 2020** reporting checklist — all 27 items

## Architecture decisions

### Frontend
- **Browser-native JS, single-file HTML** — matches the 77-app portfolio architecture
- Rendering: SVG network plot, SVG forest, SVG comparison-adjusted funnel, HTML league table
- LocalStorage-backed state for resumable sessions

### Computation
- **Pure JS core** for interactive response (<50 ms recompute on node toggle)
- **WebR + netmeta fallback** for gold-standard validation (user-triggered, ~5-10 s)
- Why dual: JS for UX, R for peer-review-defence ("results match netmeta to 1e-6")

### Data model

```js
trial = {
  study: "acalabrutinib-NCT02475681",
  treatments: ["acala", "clb_obi"],   // 2-arm (most), 3-arm (some)
  effects: { "acala-vs-clb_obi": -1.5606 },  // log-HR for HR outcomes
  variances: { "acala-vs-clb_obi": 0.04178 },
  covariances: {}  // populated for 3+ arm trials
}
network = {
  treatments: ["acala", "clb_obi", "ibrutinib", "zanubrutinib"],
  trials: [...],
  reference: "clb_obi",
  outcome: { scale: "log-HR", direction: "lower-better" }
}
```

### Validation harness

- **Canonical benchmarks** (peer-reviewers will know these):
  - Hasselblad 1998 smoking cessation (24 studies, 4 treatments) — canonical NMA test case
  - Lu-Ades 2004 thrombolytics (28 studies, 8 treatments)
  - Dias 2013 smoking + revascularisation
- **Validation pipeline**: for each benchmark, compute in JS + compute in R/netmeta; diff must be <1e-6 for point estimates, <1e-4 for SE
- **Coverage simulation**: MC simulation to verify 95% CI coverage ≥ 94% (per CLT + MC variance)

### Inconsistency tests

1. **Design-by-treatment** (Higgins 2012): global Wald test comparing consistent vs inconsistency model; df = n_designs - n_treatments + 1
2. **Node-splitting** (Dias 2010): for each direct-indirect comparison that has both, compute the 2-sided p-value on the difference
3. **Loop-specific** inconsistency plot: show all closed loops with their inconsistency factors + 95% CI

### Ranking

- Draw N=100,000 multivariate normal samples from the fitted NMA (mean, vcov)
- Compute rank distribution for each treatment on the target outcome
- SUCRA = mean(1 - (rank-1)/(T-1))
- Report: SUCRA point + 95% CrI + full rank-probability distribution
- **Never present a ranked list without the rank-probability matrix** (Mbuagbaw 2017 rule)

## Acceptance tests (must pass before peer-review submission)

1. **Hasselblad benchmark**: pool ORs within 1e-6 of Dias 2013 reported values
2. **Node-split power**: Monte Carlo on 2-loop network with seeded inconsistency; detect inconsistency at α=0.05 with ≥80% power at effect size Δ=0.3
3. **Multi-arm handling**: 3-arm trial with known τ²/2 off-diagonal covariance returns correct pooled SE
4. **Disconnected-network guard**: script exits with clear error before fitting
5. **SUCRA coverage**: 10,000 MC replicates, SUCRA 95% CrI covers true rank 94-96% of the time
6. **R cross-check**: full Hasselblad + Lu-Ades + 1 clinical benchmark all match `netmeta` to tolerance

## What this engine does NOT do (yet)

- Individual-patient-data (IPD) NMA — separate roadmap
- Component NMA (CNMA) — adds regression on components
- Surv-NMA with RMST or Guyot-IPD — add later
- Dose-response NMA (drmeta) — distinct module
- Subgroup/meta-regression NMA — distinct module

## Implementation phases

- **Phase 0** (this session): scaffold + DESIGN + basic JS engine for fixed-effects NMA + Hasselblad benchmark
- **Phase 1**: random-effects (REML τ²) + HKSJ + single-node-split + R validation loop
- **Phase 2**: design-by-treatment + loop inconsistency + comparison-adjusted funnel
- **Phase 3**: ranking (SUCRA + P-score + rank distribution viz)
- **Phase 4**: network plot + forest + league table + PRISMA-NMA export
- **Phase 5**: first demonstrator app (BTKi CLL) + peer-review submission bundle
- **Phase 6**: additional demonstrator apps (anti-VEGF nAMD, IL-pathway psoriasis, BTKi network expansions)
