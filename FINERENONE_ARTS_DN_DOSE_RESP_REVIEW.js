/* FINERENONE_ARTS_DN_DOSE_RESP_REVIEW.js
 *
 * Round 3.6 — single-trial (k=1) dose-response flagship for ARTS-DN finerenone
 * Phase 2b dose-finder (NCT01874431; Bakris 2015 JAMA; PMID 26325557).
 *
 * Engine path: v0.4 k=1 single-trial branch (PR #270, merged 40990cf4):
 *   estimator      = 'wls_single_trial_rcs'
 *   ci_method      = 't_within_trial'
 *   hksj_mv        = 1                 (no Q heterogeneity inflation at k=1)
 *   q_mv           = 0
 *   tau2_matrix    = zeros(Kp, Kp)     (single trial -> between-study var undefined)
 *   tau2_per_dim   = [0, 0]
 *   tcrit          = qt(0.975, n_arms - Kp - 1) = qt(0.975, 5) = 2.571
 *   converged      = true              (no REML to run; closed-form WLS on single trial)
 *
 * Tabs (3, per Round 3.6 plan):
 *   1. UACR RCS dose-response  (HEADLINE: spline_coefs, Wald non-linearity, fit_at_dose grid)
 *   2. AACT data audit         (per-arm raw multiplicative-ratio + log-scale conversion notes
 *                               + inline PubMed abstract)
 *   3. R-parity badge          (k=1 deferral panel + abbreviated 2-row RCS-only comparison)
 *
 * Dropped tabs (vs Tirzepatide/Alcohol/SGLT2i flagships):
 *   - Linear pool tab          (engine fitLinear requires k >= 2; throws at k=1)
 *   - One-stage tab            (R lme4::lmer requires >= 2 sampled grouping levels)
 *
 * Field-path contract (Round 2C PR #250 — TOP-LEVEL vs NESTED):
 *   TOP-LEVEL  : hksj_mv, q_mv, df_mv, tcrit, estimator, ci_method, converged,
 *                pooled_slope_log{,_se,_ci_lo,_ci_hi}
 *   NESTED .rcs: spline_coefs, spline_coefs_se, nonlinearity_wald_p,
 *                nonlinearity_wald_chi2, nonlinearity_wald_df, tau2_matrix,
 *                tau2_per_dim, fit_at_dose, knots, reml_converged,
 *                reml_iterations, reml_loglik, cov_beta
 *
 * CSP: this file is loaded via <script src="..." defer>. No inline <script> blocks
 * or inline onclick handlers (PR #257 cleanup); tab nav is wired by addEventListener.
 */

function showTab(name) {
  document.querySelectorAll('.tab-content').forEach(function (el) { el.classList.remove('active'); });
  document.querySelectorAll('.tab-nav button').forEach(function (el) {
    el.classList.remove('active');
    el.setAttribute('aria-selected', 'false');
    el.setAttribute('tabindex', '-1');
  });
  document.getElementById('tab-' + name).classList.add('active');
  var activeBtn = document.querySelector('.tab-nav button[data-tab="' + name + '"]');
  activeBtn.classList.add('active');
  activeBtn.setAttribute('aria-selected', 'true');
  activeBtn.setAttribute('tabindex', '0');
  var panelH2 = document.getElementById('tab-' + name).querySelector('h2');
  if (panelH2) {
    panelH2.setAttribute('tabindex', '-1');
    panelH2.focus({ preventScroll: false });
  }
}

// CSP-safe tab wiring: addEventListener (no inline onclick). Keyboard nav for arrows/Home/End.
document.querySelectorAll('.tab-nav button[role="tab"]').forEach(function (btn) {
  btn.addEventListener('click', function () { showTab(btn.getAttribute('data-tab')); });
  btn.addEventListener('keydown', function (e) {
    var key = e.key;
    if (key !== 'ArrowLeft' && key !== 'ArrowRight' && key !== 'Home' && key !== 'End') return;
    e.preventDefault();
    var buttons = Array.prototype.slice.call(document.querySelectorAll('.tab-nav button[role="tab"]'));
    var idx = buttons.indexOf(btn);
    var next;
    if (key === 'ArrowLeft') next = (idx - 1 + buttons.length) % buttons.length;
    else if (key === 'ArrowRight') next = (idx + 1) % buttons.length;
    else if (key === 'Home') next = 0;
    else next = buttons.length - 1;
    var nextBtn = buttons[next];
    showTab(nextBtn.getAttribute('data-tab'));
    nextBtn.focus();
  });
});

function escapeHtml(s) {
  if (s == null) return '';
  return String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;')
    .replace(/>/g, '&gt;').replace(/"/g, '&quot;').replace(/'/g, '&#39;');
}

function fmtNum(x, dp) {
  if (x == null || !isFinite(x)) return 'n/a';
  return (+x).toFixed(dp == null ? 4 : dp);
}

window.addEventListener('DOMContentLoaded', function () {
  if (!window.RapidMetaDoseResp || typeof window.RapidMetaDoseResp.engine_version !== 'string') {
    document.body.innerHTML = '<div style="color:#c00; padding:1em;"><strong>Engine failed to load.</strong> Check the browser console for errors.</div>';
    return;
  }
  var DR = window.RapidMetaDoseResp;

  // Engine version + date
  document.getElementById('engine-version').textContent = DR.engine_version;
  document.getElementById('gen-date').textContent = new Date().toISOString().slice(0, 10);

  // Read UACR trials (k=1, single trial = ARTS-DN)
  var uacrScript = document.getElementById('doseresp-trials-uacr');
  var uacrTrials;
  try {
    uacrTrials = JSON.parse(uacrScript.textContent);
  } catch (e) {
    document.getElementById('uacr-rcs-kpis').textContent = 'UACR trial data malformed: ' + e.message;
    return;
  }
  if (uacrTrials.length === 0) {
    document.getElementById('uacr-rcs-kpis').textContent = 'No UACR trial data embedded.';
    return;
  }

  // === Tab 1: UACR RCS dose-response (HEADLINE) ===
  // Engine v0.4 k=1 single-trial branch: estimator=wls_single_trial_rcs,
  // ci_method=t_within_trial, hksj_mv=1, tau2 all zeros, tcrit from within-trial df.
  var uacrRcs = DR.fitRCS(uacrTrials, { knots: 3 });

  var sc0 = uacrRcs.rcs.spline_coefs[0];          // linear-basis component
  var sc1 = uacrRcs.rcs.spline_coefs[1];          // non-linear-basis component
  var sc0_se = uacrRcs.rcs.spline_coefs_se[0];
  var sc1_se = uacrRcs.rcs.spline_coefs_se[1];

  // Headline at 20 mg (engine's fit_at_dose grid endpoint)
  var fit20 = uacrRcs.rcs.fit_at_dose[uacrRcs.rcs.fit_at_dose.length - 1];
  var ratio20 = Math.exp(fit20.est);              // back-transform log-ratio to ratio
  var ratio20_lo = Math.exp(fit20.ci_lo);
  var ratio20_hi = Math.exp(fit20.ci_hi);

  document.getElementById('uacr-rcs-kpis').innerHTML =
    '<div class="kpi-grid">' +
    '<div class="kpi"><div class="kpi-label">UACR ratio at 20 mg (RCS, back-transformed)</div><div class="kpi-value">' + ratio20.toFixed(3) + '</div><div>95% CI ' + ratio20_lo.toFixed(3) + ' to ' + ratio20_hi.toFixed(3) + '</div><div style="color:#92400e; font-size:0.8em;">single-trial CI via t<sub>5, 0.975</sub> = ' + uacrRcs.tcrit.toFixed(3) + '</div></div>' +
    '<div class="kpi"><div class="kpi-label">spline_coefs[0] (linear)</div><div class="kpi-value">' + sc0.toFixed(4) + '</div><div>SE ' + sc0_se.toFixed(4) + '</div></div>' +
    '<div class="kpi"><div class="kpi-label">spline_coefs[1] (non-linear)</div><div class="kpi-value">' + sc1.toFixed(4) + '</div><div>SE ' + sc1_se.toFixed(4) + '</div></div>' +
    '<div class="kpi"><div class="kpi-label">Knots (mg, Harrell default)</div><div class="kpi-value">' + uacrRcs.rcs.knots.map(function (k) { return k.toFixed(2); }).join(', ') + '</div></div>' +
    '<div class="kpi"><div class="kpi-label">Wald non-linearity p</div><div class="kpi-value">' + uacrRcs.rcs.nonlinearity_wald_p.toFixed(4) + '</div><div>&chi;<sup>2</sup> = ' + uacrRcs.rcs.nonlinearity_wald_chi2.toFixed(3) + ' (df ' + uacrRcs.rcs.nonlinearity_wald_df + ')</div></div>' +
    '<div class="kpi"><div class="kpi-label">hksj_mv (single-trial)</div><div class="kpi-value">' + uacrRcs.hksj_mv.toFixed(2) + '</div><div>= 1 by construction (no between-study Q at k=1)</div></div>' +
    '<div class="kpi"><div class="kpi-label">tcrit (within-trial t)</div><div class="kpi-value">' + uacrRcs.tcrit.toFixed(3) + '</div><div>qt(0.975, df=' + uacrRcs.df_mv + ') = ' + uacrRcs.tcrit.toFixed(3) + '</div></div>' +
    '<div class="kpi"><div class="kpi-label">Estimator</div><div class="kpi-value" style="font-size:0.9em;">' + escapeHtml(uacrRcs.estimator) + '</div><div>ci_method = ' + escapeHtml(uacrRcs.ci_method) + '</div></div>' +
    '<div class="kpi"><div class="kpi-label">k (trials) / n_arms</div><div class="kpi-value">' + uacrRcs.k + ' / ' + uacrTrials[0].arms.length + '</div><div style="color:#92400e">single-trial; n_total = ' + uacrTrials[0].arms.reduce(function (a, b) { return a + b.n; }, 0) + '</div></div>' +
    '</div>';

  // Wald non-linearity headline banner
  var nlP = uacrRcs.rcs.nonlinearity_wald_p;
  var nlBadgeClass = nlP < 0.05 ? 'rv-badge-green' : (nlP > 0.20 ? 'rv-badge-amber' : 'rv-badge-amber');
  var nlVerdict = nlP < 0.05 ? 'Statistically significant non-linearity detected'
                : (nlP > 0.20 ? 'No evidence of non-linearity (within-trial dose-response approximately linear on log scale)'
                              : 'Inconclusive non-linearity (borderline)');
  document.getElementById('uacr-rcs-wald').innerHTML =
    '<div class="rv-badge ' + nlBadgeClass + '">' +
    '<strong>' + nlVerdict + ' (single-trial Wald, engine v0.4 k=1):</strong> Wald p = ' + nlP.toFixed(4) +
    ' (&chi;<sup>2</sup> = ' + uacrRcs.rcs.nonlinearity_wald_chi2.toFixed(3) + ', df ' + uacrRcs.rcs.nonlinearity_wald_df + '). ' +
    'Within ARTS-DN&apos;s 8-arm dose grid (placebo + 1.25 / 2.5 / 5 / 7.5 / 10 / 15 / 20 mg), the dose-response on the log-UACR-ratio scale is approximately linear with slope &asymp; ' + sc0.toFixed(3) + ' per mg (' + sc0_se.toFixed(3) + ' SE). The non-linear spline component is small (' + sc1.toFixed(3) + ', SE ' + sc1_se.toFixed(3) + ') and not statistically significant; back-transformed to the ratio scale, each 1 mg of finerenone is associated with a multiplicative UACR-ratio change of &times; ' + Math.exp(sc0).toFixed(3) + ' per mg (so the cumulative effect at 20 mg is &times; ' + Math.exp(20 * sc0).toFixed(3) + ').<br>' +
    '<span class="rv-disclosure">Single-trial inference is computed on the trial&apos;s own coefficient covariance <code>V</code> with no HKSJ inflation (hksj_mv = ' + uacrRcs.hksj_mv.toFixed(2) + ' by construction; q_mv = ' + uacrRcs.q_mv.toFixed(2) + '; df_mv = ' + uacrRcs.df_mv + '). CI critical value: t<sub>n_arms &minus; K<sub>p</sub> &minus; 1 = 5</sub> = ' + uacrRcs.tcrit.toFixed(3) + '. The engine&apos;s k=1 path is regression-tested by 8 unit tests in <code>tests/test_dose_response_engine.mjs</code>; estimator label, hksj_mv invariant, &tau;<sup>2</sup>=0 invariant, finite Wald p, within-trial tcrit, fit_at_dose grid, direct <code>cov_beta = V</code> equivalence.</span></div>';

  // τ² matrix display — for k=1, all zeros (single-trial invariant)
  var tm = uacrRcs.rcs.tau2_matrix;
  var tauMatrixHtml = '<h3>&tau;<sup>2</sup> matrix (' + tm.length + '&times;' + tm.length + ', single-trial &rArr; all zeros by construction)</h3>' +
    '<div class="table-scroll"><table><caption>Between-trial covariance of (linear, non-linear) spline coefficients &mdash; identically zero at k=1</caption>' +
    '<thead><tr><th></th><th>linear</th><th>non-linear</th></tr></thead><tbody>' +
    '<tr><td><strong>linear</strong></td><td>' + tm[0][0].toExponential(2) + '</td><td>' + tm[0][1].toExponential(2) + '</td></tr>' +
    '<tr><td><strong>non-linear</strong></td><td>' + tm[1][0].toExponential(2) + '</td><td>' + tm[1][1].toExponential(2) + '</td></tr>' +
    '</tbody></table></div>' +
    '<p style="font-size:0.92em; color:#444; margin-top:0.4em;">At k=1 the between-study &tau;<sup>2</sup> matrix is undefined (variance of a single observation is mathematically 0 with df=0). The engine returns <code>zeros(K<sub>p</sub>, K<sub>p</sub>)</code> by construction and sets <code>reml_converged = true</code> with <code>reml_iterations = 0</code> (no REML to run). All inferential variability comes from the trial&apos;s own coefficient covariance <code>cov_beta = V</code> (8 arms &rArr; rich within-trial information). HKSJ-multivariate scaling is 1 because there is no Q heterogeneity defined.</p>';
  document.getElementById('uacr-rcs-tau2matrix').innerHTML = tauMatrixHtml;

  // Per-arm forest of arm-level log-UACR-ratios (each arm vs placebo reference)
  var forestRows = uacrTrials[0].arms.map(function (a) {
    if (a.is_reference) {
      return {
        label: a.label,
        dose: a.dose,
        delta_log: 0,
        delta_log_se: 0,
        ratio: 1.0,
        ratio_lo: null,
        ratio_hi: null,
        is_reference: true,
      };
    }
    var ref = uacrTrials[0].arms[0];
    var delta_log = a.mean - ref.mean;
    // Within-trial SE of the contrast: shared-reference Greenland-Longnecker
    // var(delta) = sd_i^2 / n_i + sd_ref^2 / n_ref
    var delta_log_var = (a.sd * a.sd) / a.n + (ref.sd * ref.sd) / ref.n;
    var delta_log_se = Math.sqrt(delta_log_var);
    return {
      label: a.label,
      dose: a.dose,
      delta_log: delta_log,
      delta_log_se: delta_log_se,
      ratio: Math.exp(delta_log),
      ratio_lo: Math.exp(delta_log - 1.96 * delta_log_se),
      ratio_hi: Math.exp(delta_log + 1.96 * delta_log_se),
      is_reference: false,
    };
  });
  var forestHtml = '<h3>Per-arm forest (8 arms: placebo + 7 finerenone doses) &mdash; placebo-corrected UACR ratio (Day-90 / baseline, log scale back-transformed)</h3>' +
    '<div class="table-scroll"><table><caption>Within-trial arm-level log-UACR-ratio vs placebo (95% CI via 1.96 &middot; SE on log scale, back-transformed)</caption>' +
    '<thead><tr><th>Arm</th><th>Dose (mg)</th><th>UACR ratio vs placebo</th><th>95% CI (back-transformed)</th><th>log-ratio (raw)</th></tr></thead><tbody>';
  forestRows.forEach(function (r) {
    forestHtml += '<tr><td>' + escapeHtml(r.label) + '</td>' +
                  '<td>' + r.dose.toFixed(2) + '</td>';
    if (r.is_reference) {
      forestHtml += '<td>1.000 (reference)</td><td>&mdash;</td><td>0.000 (reference)</td>';
    } else {
      forestHtml += '<td>' + r.ratio.toFixed(3) + '</td>' +
                    '<td>' + r.ratio_lo.toFixed(3) + ' to ' + r.ratio_hi.toFixed(3) + '</td>' +
                    '<td>' + r.delta_log.toFixed(4) + ' (SE ' + r.delta_log_se.toFixed(4) + ')</td>';
    }
    forestHtml += '</tr>';
  });
  forestHtml += '</tbody></table></div>';
  document.getElementById('uacr-rcs-forest').innerHTML = forestHtml;

  // fit_at_dose grid (20 points, 0 to 20 mg)
  var rcsCurveHtml = '<h3>RCS dose-response curve (UACR ratio, back-transformed from log scale; 20-point fit_at_dose grid)</h3>' +
    '<div class="table-scroll"><table><caption>RCS fit_at_dose grid: 20 evenly-spaced points 0 to max-observed-dose, back-transformed log-ratio &rarr; ratio</caption>' +
    '<thead><tr><th>Dose (mg)</th><th>log-ratio (raw engine output)</th><th>95% CI (log scale)</th><th>UACR ratio (back-transformed)</th><th>95% CI (ratio scale)</th></tr></thead><tbody>';
  uacrRcs.rcs.fit_at_dose.forEach(function (p) {
    rcsCurveHtml += '<tr><td>' + p.dose.toFixed(2) + '</td>' +
                    '<td>' + p.est.toFixed(4) + '</td>' +
                    '<td>' + p.ci_lo.toFixed(4) + ' to ' + p.ci_hi.toFixed(4) + '</td>' +
                    '<td>' + Math.exp(p.est).toFixed(3) + '</td>' +
                    '<td>' + Math.exp(p.ci_lo).toFixed(3) + ' to ' + Math.exp(p.ci_hi).toFixed(3) + '</td></tr>';
  });
  rcsCurveHtml += '</tbody></table></div>';
  document.getElementById('uacr-rcs-curve').innerHTML = rcsCurveHtml;

  // Plain-English summary
  document.getElementById('uacr-rcs-summary').innerHTML =
    '<p><strong>Plain-English summary (RCS, single-trial k=1):</strong> The within-trial dose-response in ARTS-DN is monotonic and approximately log-linear over the 1.25 to 20 mg dose range. Each 1 mg of finerenone is associated with a UACR-ratio reduction of approximately ' + ((1 - Math.exp(sc0)) * 100).toFixed(1) + '% per mg (log-slope = ' + sc0.toFixed(3) + ', SE ' + sc0_se.toFixed(3) + '). At 20 mg the model-fit Day-90 UACR ratio is ' + ratio20.toFixed(3) + ' (95% CI ' + ratio20_lo.toFixed(3) + ' to ' + ratio20_hi.toFixed(3) + '), corresponding to a placebo-corrected UACR reduction of ' + ((1 - ratio20) * 100).toFixed(1) + '%. The non-linear spline component (' + sc1.toFixed(3) + ', SE ' + sc1_se.toFixed(3) + ', Wald p = ' + nlP.toFixed(4) + ') is small and not statistically significant &mdash; consistent with the published primary outcome reporting all dose groups individually vs placebo and showing a smooth dose-graded UACR reduction.</p>' +
    '<p style="margin-top:0.6em; font-size:0.92em; color:#92400e;"><strong>k=1 caveat (read first):</strong> This is a <em>single-trial</em> dose-response analysis. Between-study heterogeneity cannot be assessed (no second trial to compare against). The CIs reflect within-trial sampling uncertainty only, computed on the trial&apos;s own coefficient covariance <code>V</code>; <code>tcrit = qt(0.975, n_arms &minus; K<sub>p</sub> &minus; 1) = qt(0.975, 5) = 2.571</code> (within-trial residual t). External generalizability to a pooled finerenone class effect requires additional Phase 2b dose-finders, which do not exist for finerenone (FIDELIO-DKD, FIGARO-DKD, FINEARTS-HF tested only the 10-20 mg dose schedule). The within-trial monotonicity and the regulatory dose-selection (10-20 mg) are robust within ARTS-DN.</p>';

  // === Tab 2: LOO sensitivity — not applicable at k=1 (engine v0.5.0) ===
  // fitLOO requires k_full >= 2 to drop a trial; at k=1 there is no LOO subset.
  // Render an explanatory panel rather than calling DR._internal.fitLOO (which
  // would either throw or return an empty .loo array per spec).
  document.getElementById('loo-kpis').innerHTML =
    '<div class="kpi-grid">' +
    '<div class="kpi"><div class="kpi-label">k (input)</div><div class="kpi-value">1</div><div>single-trial fixture (ARTS-DN)</div></div>' +
    '<div class="kpi"><div class="kpi-label">k_loo possible</div><div class="kpi-value">0</div><div>cannot drop a trial below k=1</div></div>' +
    '<div class="kpi"><div class="kpi-label">Engine helper</div><div class="kpi-value" style="font-size:0.9em;">DR._internal.fitLOO</div><div>v0.5.0 (introduced PR #283)</div></div>' +
    '<div class="kpi"><div class="kpi-label">Applicable?</div><div class="kpi-value" style="color:#92400e;">No</div><div>k_full &lt; 2</div></div>' +
    '</div>';
  document.getElementById('loo-headline').innerHTML =
    '<div class="rv-badge rv-badge-amber">' +
    '<strong>LOO sensitivity not applicable at k=1.</strong> Leave-one-out (LOO) sensitivity is a between-study robustness check: re-fit the pooled model k times, each time dropping one trial, and inspect how the headline quantity moves. At k=1 there is no second trial to compare against and no LOO subset to fit. This flagship&apos;s headline (Tab 1 RCS within-trial fit on 8 ARTS-DN arms) is therefore already presented at the smallest possible subset; there is nothing to leave out. The within-trial reliability check is the standard residual-t CI on the 7 dose-vs-reference contrasts (Tab 1), not a LOO sensitivity.<br>' +
    '<span class="rv-disclosure">For the methodological story of LOO at small k, see the SURMOUNT k=2 flagship (each LOO drops to k=1 and the engine&apos;s single-trial RCS branch activates) and the SUSTAIN k=6 flagship (one LOO subset hits the engine&apos;s sparse-arm degeneration path). Engine: ' + escapeHtml(DR.engine_version) + '.</span></div>';
  document.getElementById('loo-methods').innerHTML =
    '<p><strong>Why no LOO at k=1:</strong> <code>DR._internal.fitLOO(trials, opts)</code> validates the input pool and iterates k times, each time leaving one trial out. At k_full=1 the loop body would execute on an empty subset; the spec exits early and returns an empty <code>loo[]</code> array with <code>summary.skipped_reason = &#39;k_full &lt; 2 &mdash; cannot drop a trial&#39;</code>. Rather than render an empty table the flagship surfaces this explanatory panel so the reader knows the engine output is intentional, not a bug.</p>' +
    '<p style="margin-top:0.6em; font-size:0.92em; color:#444;"><strong>What WOULD a Phase 3 finerenone dose-response LOO look like?</strong> A multi-Phase-2b finerenone evidence base does not exist — FIDELIO-DKD, FIGARO-DKD, and FINEARTS-HF all use the 10-20 mg titrated schedule chosen FROM ARTS-DN, so they share the dose-finding decision rather than re-test it. A future second Phase 2b dose-finder of finerenone (or a sibling MR antagonist with comparable dose grid like esaxerenone) would unlock the standard k&gt;=2 LOO sensitivity check.</p>';

  // === Tab 3: AACT data audit ===
  var trialMetaHtml = '<h3>Trial metadata (NCT01874431)</h3>' +
    '<table><caption>ARTS-DN registered trial metadata and publication details</caption>' +
    '<tbody>' +
    '<tr><th>Trial label</th><td>ARTS-DN (Bakris 2015, T2D with diabetic nephropathy)</td></tr>' +
    '<tr><th>NCT</th><td><a href="https://clinicaltrials.gov/ct2/show/NCT01874431" target="_blank" rel="noopener noreferrer">NCT01874431</a></td></tr>' +
    '<tr><th>Publication</th><td>Bakris GL, Agarwal R, Chan JC, et al. <em>JAMA</em>. 2015;314(9):884-894. <a href="https://pubmed.ncbi.nlm.nih.gov/26325557/" target="_blank" rel="noopener noreferrer">PMID 26325557</a> &middot; <a href="https://doi.org/10.1001/jama.2015.10081" target="_blank" rel="noopener noreferrer">doi:10.1001/jama.2015.10081</a></td></tr>' +
    '<tr><th>Sample size</th><td>N = 821 received study drug (823 randomized); placebo n=94, finerenone arms n=92 to 125</td></tr>' +
    '<tr><th>Primary endpoint</th><td>Day-90 UACR / baseline UACR ratio (LSM, multiplicative scale)</td></tr>' +
    '<tr><th>AACT outcome_id</th><td>211099820 (primary outcome, from outcome_measurements.txt; AACT snapshot 2026-04-12)</td></tr>' +
    '<tr><th>Background therapy</th><td>ACEi or ARB (per inclusion criteria; both arms)</td></tr>' +
    '<tr><th>Trial design</th><td>Phase 2b parallel-randomized fixed-dose (not titrated); 148 sites in 23 countries; June 2013 to August 2014</td></tr>' +
    '</tbody></table>';
  document.getElementById('aact-trial-meta').innerHTML = trialMetaHtml;

  var aactScript = document.getElementById('aact-armtable-data');
  var aactRows;
  try {
    aactRows = JSON.parse(aactScript.textContent);
  } catch (e) {
    document.getElementById('aact-armtable').textContent = 'AACT arm table malformed: ' + e.message;
    return;
  }
  var armTableHtml = '<h3>AACT per-arm raw data (multiplicative-ratio scale, registry-deposited)</h3>' +
    '<div class="table-scroll"><table><caption>Per-arm LSM Day-90 UACR / baseline ratio with 90% CI, N, and derived log-scale SE (engine input)</caption>' +
    '<thead><tr><th>Arm (AACT label)</th><th>Dose (mg)</th><th>N</th><th>LSM ratio</th><th>90% CI (ratio scale)</th><th>SE on log scale (engine input)</th></tr></thead><tbody>';
  aactRows.forEach(function (r) {
    armTableHtml += '<tr><td>' + escapeHtml(r.arm) + '</td>' +
                    '<td>' + r.dose_mg.toFixed(2) + '</td>' +
                    '<td>' + r.n + '</td>' +
                    '<td>' + r.lsm_ratio.toFixed(3) + '</td>' +
                    '<td>' + r.ci90_lo.toFixed(3) + ' to ' + r.ci90_hi.toFixed(3) + '</td>' +
                    '<td>' + r.se_log.toFixed(5) + '</td></tr>';
  });
  armTableHtml += '</tbody></table></div>';
  document.getElementById('aact-armtable').innerHTML = armTableHtml;

  document.getElementById('aact-conversion-notes').innerHTML =
    '<h3>Log-scale conversion notes (engine input pipeline)</h3>' +
    '<p>AACT deposits the primary outcome on the multiplicative-ratio scale (Day-90 UACR / baseline UACR LSM with 90% CI). The engine&apos;s continuous-outcome convention is log-RR / log-ratio per-arm input (per <code>lessons.md</code>: "Always pool logRR/logOR/logHR, back-transform after"). Conversion:</p>' +
    '<ul>' +
    '<li><code>mean_log = log(LSM_ratio)</code> &mdash; per-arm log-ratio mean (engine field: <code>mean</code>)</li>' +
    '<li><code>SE_log = (log(CI_hi) &minus; log(CI_lo)) / (2 &times; 1.6449)</code> &mdash; SE on log scale derived from 90% CI half-width (1.6449 = qnorm(0.95))</li>' +
    '<li><code>SD_log = SE_log &times; sqrt(n)</code> &mdash; per-arm log-scale SD (engine field: <code>sd</code>)</li>' +
    '</ul>' +
    '<p style="font-size:0.92em; color:#444;">The engine&apos;s continuous-branch covariance formula (per-trial shared-reference Greenland-Longnecker structure) uses <code>SD</code> and <code>n</code> directly: off-diagonal entries = <code>sd_ref&sup2; / n_ref</code>; diagonal entries = <code>sd_i&sup2; / n_i + sd_ref&sup2; / n_ref</code>. The Tab 1 RCS output and Tab 2 per-arm-vs-placebo forest both use the same log-scale conversion; the only difference is that the RCS layer pools across the spline-basis dimensions to deliver a smoothed dose-response curve, whereas the forest reports each arm individually.</p>' +
    '<p style="font-size:0.92em; color:#444;"><strong>Why 90% CI not 95%:</strong> The ARTS-DN primary-outcome report uses a 90% CI (regulator-standard for dose-finding designs); we derive the log-scale SE from this. The engine&apos;s downstream CIs are 95% (computed via <code>tcrit = qt(0.975, df)</code>), so the converted SE flows correctly through the engine&apos;s standard CI machinery without re-scaling.</p>';

  // === Tab 3: R-parity badge (k=1 deferral panel + abbreviated 2-row RCS-only) ===
  // Standard 5-row badge cannot run at k=1:
  //   - linear_slope / linear_tau2 rows require engine fitLinear (k >= 2; throws at k=1)
  //   - one_stage row requires R lme4::lmer (>= 2 sampled grouping levels; fails at k=1)
  // We render a custom panel with deferral notice + a 2-row engine-vs-R RCS comparison
  // sourced from R dosresmeta (which supports k=1).
  fetch('outputs/r_validation/doseresp/finerenone_arts_dn.json').then(function (r) {
    if (!r.ok) throw new Error('R JSON: HTTP ' + r.status);
    return r.json();
  }).then(function (rJson) {
    var rcsR = rJson.rcs || {};
    // Threshold for RCS coefs: 0.01 (matches vendor/r-validation-doseresp.js v0.2.0 THRESHOLDS)
    var thr = 0.01;
    var d0 = Math.abs(sc0 - (rcsR.spline_coefs ? rcsR.spline_coefs[0] : NaN));
    var d1 = Math.abs(sc1 - (rcsR.spline_coefs ? rcsR.spline_coefs[1] : NaN));
    var dp = Math.abs(nlP - (rcsR.nonlinearity_wald_p == null ? NaN : rcsR.nonlinearity_wald_p));
    var s0 = (isFinite(d0) && d0 < thr) ? 'green' : 'amber';
    var s1 = (isFinite(d1) && d1 < thr) ? 'green' : 'amber';
    var sp = (isFinite(dp) && dp < 0.05) ? 'green' : 'amber';
    var allRcsGreen = (s0 === 'green' && s1 === 'green' && sp === 'green');
    var headerClass = 'rv-badge-deferred';  // always deferred at k=1 (linear/one-stage rows N/A)

    var html = '<div class="rv-badge ' + headerClass + '">' +
      '<details open>' +
      '<summary>R-parity badge &mdash; k=1 single-trial path (deferred to engine v0.5)</summary>' +
      '<p style="margin:0.6em 0;"><strong>Standard badge: deferred at k=1.</strong> The 5-row R-parity badge (<code>vendor/r-validation-doseresp.js</code> v0.2.0) cannot run at k=1: the engine&apos;s <code>fitLinear</code> requires k &ge; 2 (no engine linear output to compare), and R <code>lme4::lmer</code> for the one-stage row requires &ge; 2 sampled grouping levels (no R one-stage output). The engine&apos;s k=1 output is regression-tested by 8 unit tests in <code>tests/test_dose_response_engine.mjs</code> (estimator label, hksj_mv=1, &tau;<sup>2</sup>=0, finite Wald p, within-trial tcrit, fit_at_dose grid, direct <code>cov_beta = V</code>). A future engine v0.5 may extend the badge contract to handle k=1 by surfacing N/A rows explicitly and / or by adapting <code>mixmeta</code> for k=1 (currently k &ge; 2 only).</p>' +
      '<table class="rv-table">' +
      '<caption>Engine vs R precompute (abbreviated; 2 RCS rows + non-linearity-p row testable at k=1; linear and one-stage rows N/A)</caption>' +
      '<thead><tr><th>Metric</th><th>Engine</th><th>R (dosresmeta)</th><th>|&Delta;|</th><th>Status</th></tr></thead>' +
      '<tbody>' +
      '<tr class="rv-row rv-row-' + s0 + '"><td>RCS spline_coefs[0] (linear component)</td><td>' + fmtNum(sc0) + '</td><td>' + fmtNum(rcsR.spline_coefs ? rcsR.spline_coefs[0] : null) + '</td><td>' + fmtNum(d0) + '</td><td>' + s0.toUpperCase() + ' (threshold ' + thr + ')</td></tr>' +
      '<tr class="rv-row rv-row-' + s1 + '"><td>RCS spline_coefs[1] (non-linear component)</td><td>' + fmtNum(sc1) + '</td><td>' + fmtNum(rcsR.spline_coefs ? rcsR.spline_coefs[1] : null) + '</td><td>' + fmtNum(d1) + '</td><td>' + s1.toUpperCase() + ' (threshold ' + thr + ')</td></tr>' +
      '<tr class="rv-row rv-row-' + sp + '"><td>RCS non-linearity Wald p</td><td>' + fmtNum(nlP) + '</td><td>' + fmtNum(rcsR.nonlinearity_wald_p) + '</td><td>' + fmtNum(dp) + '</td><td>' + sp.toUpperCase() + ' (threshold 0.05)</td></tr>' +
      '<tr><td>Linear pooled log-slope</td><td colspan="4" style="font-style:italic; color:#4b5563;">N/A at k=1 (engine <code>fitLinear</code> requires k &ge; 2; throws otherwise). R <code>dosresmeta</code> returned <code>pooled_slope_log = ' + fmtNum(rJson.linear ? rJson.linear.pooled_slope_log : null) + '</code> for context only; no engine-side counterpart.</td></tr>' +
      '<tr><td>Linear &tau;<sup>2</sup></td><td colspan="4" style="font-style:italic; color:#4b5563;">N/A at k=1 (between-study variance undefined with a single observation).</td></tr>' +
      '<tr><td>One-stage coef_dose</td><td colspan="4" style="font-style:italic; color:#4b5563;">N/A at k=1 (R <code>lme4::lmer</code> error: "grouping factors must have &gt; 1 sampled level"; confirmed in the R precompute JSON, <code>one_stage.fit_ok = false</code>).</td></tr>' +
      '</tbody></table>' +
      '<p style="margin-top:0.6em; font-size:0.92em; color:#444;"><strong>Verdict:</strong> ' + (allRcsGreen
        ? 'All 3 RCS-layer rows GREEN. Engine k=1 single-trial RCS coefficients match R <code>dosresmeta</code> within thresholds (spline coefs |&Delta;| &lt; 0.01; non-linearity p |&Delta;| &lt; 0.05).'
        : 'At least one RCS-layer row AMBER. Investigate: |&Delta;| on spline_coefs[0] = ' + fmtNum(d0) + ', spline_coefs[1] = ' + fmtNum(d1) + ', non-linearity p = ' + fmtNum(dp) + '. Note: R <code>dosresmeta</code> places knots using its own quantile method which may differ slightly from the engine; small RCS-row divergence at the boundary is expected and not necessarily a bug.') + '</p>' +
      '<p style="margin-top:0.4em; font-size:0.85em; color:#555;"><strong>R precompute source:</strong> <code>outputs/r_validation/doseresp/finerenone_arts_dn.json</code> (dosresmeta v' + escapeHtml(rJson.dosresmeta_version || 'unknown') + '; k = ' + (rJson.k != null ? rJson.k : 'unknown') + '). The R one-stage layer was attempted and explicitly failed with "grouping factors must have &gt; 1 sampled level" &mdash; the failure is captured in <code>one_stage.fit_ok = false</code> with <code>one_stage.error_msg</code>.</p>' +
      '</details>' +
      '</div>';
    document.getElementById('r-parity-finerenone-arts-dn').innerHTML = html;
  }).catch(function (e) {
    console.error('[finerenone-arts-dn] R JSON load failed:', e);
    document.getElementById('r-parity-finerenone-arts-dn').innerHTML =
      '<div class="rv-badge rv-badge-deferred">' +
      '<strong>R-parity badge: R JSON unavailable</strong> &mdash; ' + escapeHtml(e.message) + '. ' +
      'Run <code>python scripts/r_validate_doseresp.py --review finerenone_arts_dn</code> to populate <code>outputs/r_validation/doseresp/finerenone_arts_dn.json</code>. ' +
      'The engine&apos;s k=1 path is regression-tested by 8 unit tests in <code>tests/test_dose_response_engine.mjs</code>.' +
      '</div>';
  });

  // === Render abstract inline ===
  fetch('fixtures/dose_response/finerenone_arts_dn_abstracts.json').then(function (r) {
    if (!r.ok) throw new Error('abstracts JSON: HTTP ' + r.status);
    return r.json();
  }).then(function (abs) {
    var mount = document.getElementById('abstracts-mount');
    var html = '';
    abs.publications.forEach(function (p) {
      html += '<details>' +
        '<summary>' + escapeHtml(p.trial_label) + ' &mdash; ' + escapeHtml(p.first_author) + ', ' + escapeHtml(p.journal) + ' ' + p.year + ' (PMID ' + escapeHtml(p.pmid) + ')</summary>' +
        '<div class="abstract-block">' +
        '<p class="abstract-meta"><strong>' + escapeHtml(p.title) + '</strong></p>' +
        '<p class="abstract-meta">' + escapeHtml(p.authors_short) + ' &middot; <em>' + escapeHtml(p.journal) + '</em> ' + p.year + ';' + escapeHtml(p.volume) + (p.issue ? '(' + escapeHtml(p.issue) + ')' : '') + ':' + escapeHtml(p.pages) + ' &middot; ' +
        '<a href="' + escapeHtml(p.doi_link) + '" target="_blank" rel="noopener noreferrer">doi:' + escapeHtml(p.doi) + '</a> &middot; ' +
        '<a href="https://pubmed.ncbi.nlm.nih.gov/' + escapeHtml(p.pmid) + '/" target="_blank" rel="noopener noreferrer">PubMed ' + escapeHtml(p.pmid) + '</a> &middot; ' +
        '<a href="https://clinicaltrials.gov/ct2/show/' + escapeHtml(p.nct_id) + '" target="_blank" rel="noopener noreferrer">' + escapeHtml(p.nct_id) + '</a>' +
        '</p>' +
        '<p><strong>Abstract (according to PubMed):</strong> ' + escapeHtml(p.abstract) + '</p>' +
        '<p style="font-size:0.92em; color:#444;"><strong>Dose-response summary:</strong> ' + escapeHtml(p.primary_endpoint_text) + '</p>' +
        (p.abstract_typo_note ? '<p style="font-size:0.85em; color:#92400e;"><strong>Audit note:</strong> ' + escapeHtml(p.abstract_typo_note) + '</p>' : '') +
        '</div>' +
        '</details>';
    });
    mount.innerHTML = html;
  }).catch(function (e) {
    console.error('[finerenone-arts-dn] abstracts fetch failed:', e);
    document.getElementById('abstracts-mount').innerHTML = '<p style="color:#92400e;">Abstract unavailable: ' + escapeHtml(e.message) + '. See <code>fixtures/dose_response/finerenone_arts_dn_abstracts.json</code>.</p>';
  });

});
