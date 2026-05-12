# Round 1B → Round 2 Follow-Ups

> Captured 2026-05-12 from the final-review audit at end of Round 1B (close commit `9c4a8386`).
> Round 1B shipped 35 tests passing, R-parity confirmed, Sentinel BLOCK=0, all 4 flagship tabs wired.
> These items inform Round 2 (SGLT2i flagship + remaining P1/P2 engine hardening).

## Required before Round 2 SGLT2i flagship

### F-7 (P1 — closed in cleanup) — fitOneStage fit_ok propagation
Done in commit (this cleanup). Engine now passes `fit_ok` and `lme4_version` through. Two regression tests pin the propagation. Round 2 implementers can rely on the guard.

### F-8 (P1) — RCS knot computation divergence vs R
Engine uses `unique(non-reference doses)` for Harrell percentile knot placement (gives knots 10/20/27 for GL-1992). R `dosresmeta` uses raw quantile of the data column (gives knots 5/15/24). The divergence is documented in the amber non-linearity note in the flagship's RCS tab, but the engine source has no explicit comment. Round 2 should add a source comment in `rcsKnots()` documenting the design choice. Not blocking (the divergence is now visible to readers via the amber note + R-parity badge).

### F-9 (P1) — glmer dose rescaling for SGLT2i flagship
The Round 1B R script scales `dose` by `sd(dose[dose>0])` (= 14.09 for GL-1992) to avoid lme4 near-unidentifiability warnings, then back-transforms. Round 2 implementers building the SGLT2i R-validation script must use the same rescaling pattern OR detect convergence failure (now possible via the F-7 fit_ok propagation). Without rescaling, glmer often fails to converge cleanly on dose ranges spanning >1 order of magnitude.

## Carried over from Round 1A follow-ups (still open)

### F-1 (P1) — Zero-cell continuity correction
Not bitten by GL-1992 (no zero-event arms) but will bite SGLT2i (real-world trials often have zero-event placebo arms at lower doses, especially for rare CV outcomes). Engine `fitLinear` should implement the conditional +0.5 correction at the marked TODO before SGLT2i lands.

### F-4 (P1) — Hardcoded Rscript path
`scripts/r_validate_doseresp.py` line 28 hardcodes `r"C:\Program Files\R\R-4.5.2\bin\Rscript.exe"`. Replace with `shutil.which('Rscript')` + explicit-path fallback before any CI integration.

### F-5 (P2) — Test count to ≥40
Round 1B added 2 + 2 = 4 new tests (F-2 pin, F-3 pin, F-7 fit_ok propagation × 2), bringing the total to 37. The Round 1A audit target was ≥40; need ~3 more. Categories still missing: validate mismatched-outcome-type, validate two-arm-no-ref, fitLinear k=2 HKSJ-floor-fires.

### F-6 (P2) — Stale plan file structure
The Round 1A plan listed `tests/dose_response_baselines/r_parity.json` which was never created (the baseline went into `outputs/r_validation/doseresp/`). Update the Round 1A plan's File Structure table (or add a note) to avoid Round 2 confusion. Round 1B's plan does not have this issue.

## P2 deferrals (post-SGLT2i)

- **Full multivariate REML for fitRCS** — current diagonal-PM-per-dim approximation produces engine non-linearity p ≈ 0.05 vs R ≈ 0.70 on GL-1992. Documented in engine source. Round 2 SGLT2i flagship can ship under the same v0.1 approximation; P2 lifts to full REML (Jackson 2010).
- **Q-profile τ² CI for fitLinear** — currently returns `tau2_lo: null, tau2_hi: null`. Implement via `qchisq` bracket on Q distribution.
- **HKSJ-multivariate + t_{k-1} CI for fitRCS** — current uses raw z=1.96 (honest `estimator: 'pm_diagonal_z'` label). Lift when full multivariate REML lands.
- **Automated Playwright browser test** — current verification relies on Node-side simulation of the page's engine calls. Round 2 candidate.

## Notes for Round 2 implementer

- **DO NOT revert the basis-centering correction in `fitRCS`** (shipped Round 1A): the engine uses `rcsBasis(arm.dose, knots) - rcsBasis(ref.dose, knots)`, NOT `rcsBasis(arm.dose - ref.dose, knots)`. The two are equivalent only when ref.dose=0; for SGLT2i with non-zero baseline doses they differ. The shipped form is correct.
- **DO NOT remove the diagonal-PM amber row from the R-parity badge** — it's by design, not a defect.
- **The R-parity badge non-linearity p divergence is expected to persist for SGLT2i** until P2 lifts to full multivariate REML.
- **Use `python -m http.server` for browser smoke tests** — `file://` blocks the `fetch()` call to load the R-precomputed JSON.
