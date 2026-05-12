# Round 1A → Round 1B Follow-Ups

> Captured 2026-05-12 from the final-review audit at end of Round 1A (commit `2fea100d`).
> Round 1A shipped 33 tests passing, R-parity confirmed on the linear component, Sentinel BLOCK=0.
> These items are pre-HTML work for Round 1B (the flagship SGLT2I_DOSE_RESP_REVIEW.html plan).

## Required before Round 1B HTML lands

### F-1 (P1) — Zero-cell NaN propagation in fitLinear

**Risk:** Any non-reference arm with `events = 0` produces `log(0/p) = -Infinity`, which propagates through WLS to NaN in `pooled_slope_log`. Engine ships the corrupted result silently with no error.

**Trigger condition:** Any real SGLT2i trial with a zero-event arm (rare but plausible for hyperkalemia outcomes at lowest dose).

**Fix:** Implement the conditional +0.5 continuity correction at the marked TODO in `fitLinear` (around line 424 of `rapidmeta-dose-response-engine-v1.js`). Apply ONLY when ≥1 cell is zero (per advanced-stats.md: unconditional correction biases OR→1).

**Test gate:** add a fixture with a zero-event arm; assert `fitLinear` returns finite values rather than NaN.

### F-2 (P1) — `predict()` CI method inconsistency

**Risk:** `predict(linearResult, dose)` applies `est ± 1.96 * |dose| * se`. But `fitLinear` computes its own `pooled_slope_log_ci_lo/hi` using `qt(0.975, k-1)` (t-critical). For k=5 the discrepancy is ~30% — the predict-based curve CI will be narrower than the forest CI in the flagship HTML, producing visual disagreement.

**Fix:** in `predict()`, for `result.layer === 'linear'`, use `qt(0.975, result.pi_df)` instead of the literal `1.96`. Same idea for the RCS grid lookup (the grid currently uses 1.96 internally).

**Test gate:** new test `predict CI width matches fitLinear CI width at the per-study dose`.

### F-3 (P1) — `forest()` on RCS result uses FE weights

**Risk:** `fitRCS` does NOT set `result.tau2` at the root (it sets `rcs.tau2_per_dim`). In `forest()`, `var tau2 = result.tau2 || 0` falls back to 0, making weights pure FE for the RCS forest panel.

**Fix:** Either (a) add `tau2: tau2_per_dim[0]` to the `fitRCS` return root, or (b) in `forest()`, detect RCS and read from `result.rcs.tau2_per_dim[0]`.

**Test gate:** new test `forest weight_pct on RCS result uses RE weighting`.

### F-4 (P1) — Hardcoded R interpreter path in Python wrapper

**Path:** `scripts/r_validate_doseresp.py:28` uses `r"C:\Program Files\R\R-4.5.2\bin\Rscript.exe"`.

**Fix:** Use `shutil.which('Rscript')` with the hardcoded path as fallback; per the no-hardcoded-local-paths lesson.

### F-5 (P2) — Test count below spec target

Spec §8 targets ≥40 tests; Round 1A shipped 33. Missing categories:
1. `validate()` rejects mismatched `outcome_type` across trials
2. `validate()` rejects a 2-arm trial with no reference flag set
3. `fitLinear` k=2 with HKSJ floor firing (Q < df=1 case)
4. `fitOneStage` precomputed JSON with `converged: false`
5. `predict()` on RCS result (the RCS-grid branch)

Add ~7 tests to reach the target. Round 1B reasonable.

### F-6 (P2) — Plan file structure stale

`tests/dose_response_baselines/r_parity.json` listed in the plan's File Structure table but never created. The parity baseline was absorbed into `outputs/r_validation/doseresp/`. Update the plan's table for Round 1B clarity (avoid Round 1B implementers creating a duplicate baselines dir).

## P2/P3 deferrals captured in engine source

These have explicit `// P2 hardening` or `// P1 hardening TODO` comments in `rapidmeta-dose-response-engine-v1.js`:

- Q-profile τ² CI (`tau2_lo`, `tau2_hi` currently null in `fitLinear` return).
- Full multivariate REML for `fitRCS` (currently diagonal-PM-per-dim approximation; documented divergence from R on non-linearity p).
- HKSJ-multivariate + t_{k-1} for `fitRCS` CI (currently raw z=1.96 with honest `estimator: 'pm_diagonal_z'`, `ci_method: 'z_1.96'` labels).
- Negation-word check in `validate()` (lessons.md "Not Randomized 1,807" incident).

## Notes for Round 1B implementer

- **DO NOT revert the `fitRCS` basis centering.** The plan's code sketch used `rcsBasis(arm.dose - ref.dose, knots)`. The shipped engine uses `rcsBasis(arm.dose, knots) - rcsBasis(ref.dose, knots)`. These are equivalent only when reference dose = 0 (true for GL-1992; NOT true for SGLT2i if the reference arm is placebo+SOC at a non-zero baseline). The shipped form is correct.
- **`fitRCS` non-linearity p-value will diverge from R `dosresmeta`'s reported value** by a lot (≈0.05 engine vs ≈0.7 R on GL-1992). This is the documented diagonal-PM design tradeoff. The Round 1B R-parity badge must either exclude non-linearity p from the green-threshold check or use a tolerance ≥0.8.
- `vendor/r-validation-doseresp.js` (the collapsible badge UI) was deferred from Round 1A because it has no HTML host to mount on. Build it alongside the SGLT2I_DOSE_RESP_REVIEW.html in Round 1B.
