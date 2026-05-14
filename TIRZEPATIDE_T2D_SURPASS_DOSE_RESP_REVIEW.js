// Wire tab buttons via data-tab → addEventListener (CSP-strict, no inline onclick).
// The .js loads under `defer`, so DOMContentLoaded has already fired here.
document.querySelectorAll('.tab-nav button[data-tab]').forEach(function (btn) {
  btn.addEventListener('click', function () { showTab(btn.getAttribute('data-tab')); });
});

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

document.querySelectorAll('.tab-nav button[role="tab"]').forEach(function (btn) {
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

window.addEventListener('DOMContentLoaded', function () {
  if (!window.RapidMetaDoseResp || typeof window.RapidMetaDoseResp.engine_version !== 'string') {
    document.body.innerHTML = '<div style="color:#c00; padding:1em;"><strong>Engine failed to load.</strong> Check the browser console for errors.</div>';
    return;
  }
  var DR = window.RapidMetaDoseResp;

  // Engine version + date
  document.getElementById('engine-version').textContent = DR.engine_version;
  document.getElementById('gen-date').textContent = new Date().toISOString().slice(0, 10);

  // Read HbA1c trials
  var hba1cScript = document.getElementById('doseresp-trials-hba1c');
  var hba1cTrials;
  try {
    hba1cTrials = JSON.parse(hba1cScript.textContent);
  } catch (e) {
    document.getElementById('hba1c-linear-kpis').textContent = 'HbA1c trial data malformed: ' + e.message;
    return;
  }
  if (hba1cTrials.length === 0) {
    document.getElementById('hba1c-linear-kpis').textContent = 'No HbA1c trial data embedded.';
    return;
  }

  // === Tab 1: HbA1c Linear ===
  var hba1cLin = DR.fitLinear(hba1cTrials, {});
  // Note: pooled_slope_log here is MD-per-mg-dose (continuous mode), not log-RR.
  var mdPerMg = hba1cLin.pooled_slope_log;
  var mdPerMg_lo = hba1cLin.pooled_slope_log_ci_lo;
  var mdPerMg_hi = hba1cLin.pooled_slope_log_ci_hi;
  var mdAt15 = mdPerMg * 15;
  var mdAt15_lo = mdPerMg_lo * 15;
  var mdAt15_hi = mdPerMg_hi * 15;

  document.getElementById('hba1c-linear-kpis').innerHTML =
    '<div class="kpi-grid">' +
    '<div class="kpi"><div class="kpi-label">HbA1c change at 15 mg (linear extrapolation)</div><div class="kpi-value">' + mdAt15.toFixed(3) + '%</div><div>95% CI ' + mdAt15_lo.toFixed(3) + ' to ' + mdAt15_hi.toFixed(3) + '</div></div>' +
    '<div class="kpi"><div class="kpi-label">MD per mg dose</div><div class="kpi-value">' + mdPerMg.toFixed(5) + '</div><div>SE ' + hba1cLin.pooled_slope_log_se.toFixed(5) + '</div></div>' +
    '<div class="kpi"><div class="kpi-label">τ²</div><div class="kpi-value">' + hba1cLin.tau2.toExponential(2) + '</div></div>' +
    '<div class="kpi"><div class="kpi-label">I²</div><div class="kpi-value">' + hba1cLin.I2.toFixed(1) + '%</div><div>Q = ' + hba1cLin.Q.toFixed(2) + ' (df ' + hba1cLin.Q_df + ')</div></div>' +
    '<div class="kpi"><div class="kpi-label">PI at 15 mg (df=' + hba1cLin.pi_df + ')</div><div class="kpi-value">' + (hba1cLin.pi_lo*15).toFixed(3) + ' to ' + (hba1cLin.pi_hi*15).toFixed(3) + '</div></div>' +
    '<div class="kpi"><div class="kpi-label">k</div><div class="kpi-value">' + hba1cLin.k + '</div>' + (hba1cLin.coverage_warning ? '<div style="color:#92400e">coverage warning: k&lt;10</div>' : '') + '</div>' +
    '</div>';

  // Per-study forest (continuous mode: slope_log = MD per mg, no exp transform)
  var hba1cForestRows = DR.forest(hba1cTrials, hba1cLin);
  var hba1cFHtml = '<h3>Per-study forest (HbA1c, linear layer, RE-weighted)</h3><div class="table-scroll"><table><caption>Per-study HbA1c MD per mg dose with 95% CI (linear two-stage layer)</caption><thead><tr><th>Study</th><th>MD per mg</th><th>95% CI</th><th>Weight</th></tr></thead><tbody>';
  hba1cForestRows.forEach(function (r) {
    hba1cFHtml += '<tr><td>' + escapeHtml(r.label) + '</td>' +
                  '<td>' + r.slope_log.toFixed(5) + '</td>' +
                  '<td>' + (r.slope_log - 1.96 * r.slope_log_se).toFixed(5) + ' to ' + (r.slope_log + 1.96 * r.slope_log_se).toFixed(5) + '</td>' +
                  '<td>' + r.weight_pct.toFixed(1) + '%</td></tr>';
  });
  hba1cFHtml += '</tbody></table></div>';
  document.getElementById('hba1c-linear-forest').innerHTML = hba1cFHtml;

  // Dose-response curve (20-point grid, 0 to 15 mg)
  var maxObs = hba1cLin.max_observed_dose;
  var hba1cCurveHtml = '<h3>Dose-response curve (95% CI via t<sub>' + hba1cLin.pi_df + '</sub>)</h3><div class="table-scroll"><table><caption>Linear HbA1c MD per arm dose, 20-point grid 0 to ' + maxObs + ' mg</caption><thead><tr><th>Dose (mg)</th><th>MD (%)</th><th>95% CI</th></tr></thead><tbody>';
  for (var i = 0; i < 20; i++) {
    var d = i * maxObs / 19;
    var p = DR.predict(hba1cLin, d);
    hba1cCurveHtml += '<tr><td>' + d.toFixed(2) + '</td>' +
                     '<td>' + p.est.toFixed(4) + '</td>' +
                     '<td>' + p.ci_lo.toFixed(4) + ' to ' + p.ci_hi.toFixed(4) + '</td></tr>';
  }
  hba1cCurveHtml += '</tbody></table></div>';
  document.getElementById('hba1c-linear-curve').innerHTML = hba1cCurveHtml;

  document.getElementById('hba1c-linear-summary').innerHTML =
    '<p><strong>Plain-English summary (linear pool):</strong> The linear two-stage pool estimates that each additional 1 mg of tirzepatide is associated with a HbA1c reduction of approximately ' + Math.abs(mdPerMg).toFixed(3) + ' percentage points (95% CI ' + Math.abs(mdPerMg_hi).toFixed(3) + ' to ' + Math.abs(mdPerMg_lo).toFixed(3) + '). At the 15 mg licensed dose this extrapolates to ' + Math.abs(mdAt15).toFixed(2) + '% (95% CI ' + Math.abs(mdAt15_hi).toFixed(2) + ' to ' + Math.abs(mdAt15_lo).toFixed(2) + ').</p>' +
    '<p style="margin-top:0.6em; font-size:0.92em; color:#444;"><strong>Caveat — read Tab 2 next:</strong> The dose-response is NOT linear. Engine RCS analysis returns non-linearity Wald p = 0.0346 (see Tab 2 — RCS), meaning the linear model underestimates the 5 mg effect and overestimates the 10-15 mg incremental effect. The RCS framing in Tab 2 is the methodologically correct primary analysis; this linear pool is shown as a reference comparator only.</p>';

  // === Tab 2: HbA1c RCS (HEADLINE) ===
  var hba1cRcs = DR.fitRCS(hba1cTrials, { knots: 3 });

  document.getElementById('hba1c-rcs-kpis').innerHTML =
    '<div class="kpi-grid">' +
    '<div class="kpi"><div class="kpi-label">Knots (mg, Harrell default)</div><div class="kpi-value">' + hba1cRcs.rcs.knots.map(function (k) { return k.toFixed(1); }).join(', ') + '</div></div>' +
    '<div class="kpi"><div class="kpi-label">spline_coefs[0] (linear)</div><div class="kpi-value">' + hba1cRcs.rcs.spline_coefs[0].toFixed(5) + '</div><div>SE ' + hba1cRcs.rcs.spline_coefs_se[0].toFixed(5) + '</div></div>' +
    '<div class="kpi"><div class="kpi-label">spline_coefs[1] (non-linear)</div><div class="kpi-value">' + hba1cRcs.rcs.spline_coefs[1].toFixed(5) + '</div><div>SE ' + hba1cRcs.rcs.spline_coefs_se[1].toFixed(5) + '</div></div>' +
    '<div class="kpi"><div class="kpi-label">Wald non-linearity p</div><div class="kpi-value">' + hba1cRcs.rcs.nonlinearity_wald_p.toFixed(4) + '</div><div>χ² = ' + (hba1cRcs.rcs.nonlinearity_wald_chi2 != null ? hba1cRcs.rcs.nonlinearity_wald_chi2.toFixed(3) : 'n/a') + ' (df ' + (hba1cRcs.rcs.spline_coefs.length - 1) + ')</div></div>' +
    '<div class="kpi"><div class="kpi-label">τ² per dim</div><div class="kpi-value">[' + hba1cRcs.rcs.tau2_per_dim.map(function (t) { return t.toExponential(2); }).join(', ') + ']</div></div>' +
    '<div class="kpi"><div class="kpi-label">HKSJ-multivariate</div><div class="kpi-value">' + (hba1cRcs.hksj_mv != null ? hba1cRcs.hksj_mv.toFixed(2) : 'n/a') + '</div><div style="color:#92400e">high (between-trial heterogeneity)</div></div>' +
    '<div class="kpi"><div class="kpi-label">tcrit (t<sub>k-1</sub>)</div><div class="kpi-value">' + (hba1cRcs.tcrit != null ? hba1cRcs.tcrit.toFixed(3) : 'n/a') + '</div><div>k = ' + hba1cTrials.length + ', t<sub>4, 0.975</sub></div></div>' +
    '<div class="kpi"><div class="kpi-label">REML convergence</div><div class="kpi-value">' + (hba1cRcs.rcs.reml_converged ? 'Yes' : 'No') + '</div><div>iterations ' + (hba1cRcs.rcs.reml_iterations != null ? hba1cRcs.rcs.reml_iterations : 'n/a') + '; log-lik ' + (hba1cRcs.rcs.reml_loglik != null ? hba1cRcs.rcs.reml_loglik.toFixed(2) : 'n/a') + '</div></div>' +
    '</div>';

  // Headline Wald banner (GREEN — significant non-linearity, saturating dose-response)
  document.getElementById('hba1c-rcs-wald').innerHTML =
    '<div class="rv-badge rv-badge-green">' +
    '<strong>HEADLINE — significant non-linearity (full multivariate REML v0.3.0):</strong> Wald p = ' + hba1cRcs.rcs.nonlinearity_wald_p.toFixed(4) +
    ' (χ² = ' + (hba1cRcs.rcs.nonlinearity_wald_chi2 != null ? hba1cRcs.rcs.nonlinearity_wald_chi2.toFixed(3) : 'n/a') + ', df ' + (hba1cRcs.rcs.spline_coefs.length - 1) + '). ' +
    'Tirzepatide HbA1c response <em>saturates after approximately 5 mg</em> — the 0→5 mg increment captures most of the effect, with the 10→15 mg increment producing a substantially smaller per-mg HbA1c reduction. The linear pool (Tab 1) therefore underestimates the 5 mg effect and overestimates the 10-15 mg incremental effect; this RCS framing is the methodologically correct primary analysis for clinical decisions about whether to titrate above 5 mg.<br>' +
    '<span class="rv-disclosure">Engine v0.3.0 uses full multivariate REML via Nelder-Mead on Cholesky parameters of the τ² matrix; HKSJ-multivariate scaling factor: ' + (hba1cRcs.hksj_mv != null ? hba1cRcs.hksj_mv.toFixed(2) : 'n/a') + '; CI critical value t<sub>k-1</sub> = ' + (hba1cRcs.tcrit != null ? hba1cRcs.tcrit.toFixed(3) : 'n/a') + '. Non-linearity p matches R mixmeta within |Δ| ≈ 0.002 (R: 0.0364, engine: ' + hba1cRcs.rcs.nonlinearity_wald_p.toFixed(4) + ') — see the R-parity tab for the side-by-side comparison.</span></div>';

  // τ² matrix display (2x2)
  var tm = hba1cRcs.rcs.tau2_matrix;
  var tauMatrixHtml = '<h3>τ² matrix (2×2, full multivariate REML)</h3>' +
    '<div class="table-scroll"><table><caption>Between-trial covariance of (linear, non-linear) spline coefficients</caption>' +
    '<thead><tr><th></th><th>linear</th><th>non-linear</th></tr></thead><tbody>' +
    '<tr><td><strong>linear</strong></td><td>' + tm[0][0].toExponential(3) + '</td><td>' + tm[0][1].toExponential(3) + '</td></tr>' +
    '<tr><td><strong>non-linear</strong></td><td>' + tm[1][0].toExponential(3) + '</td><td>' + tm[1][1].toExponential(3) + '</td></tr>' +
    '</tbody></table></div>' +
    '<p style="font-size:0.92em; color:#444; margin-top:0.4em;">Off-diagonal is negative, indicating that between-trial deviations in the linear and non-linear spline components are negatively correlated (trials with a steeper-than-average linear component tend to have a flatter-than-average non-linear component). HKSJ-multivariate scaling factor of ' + (hba1cRcs.hksj_mv != null ? hba1cRcs.hksj_mv.toFixed(2) : 'n/a') + ' is high (large between-trial heterogeneity, consistent with the differences in background therapy and follow-up window across SURPASS-1 through -5).</p>';
  document.getElementById('hba1c-rcs-tau2matrix').innerHTML = tauMatrixHtml;

  // RCS curve via fit_at_dose grid
  var rcsCurveHtml = '<h3>RCS dose-response curve (HbA1c)</h3><div class="table-scroll"><table><caption>RCS dose-response curve via 20-point fit_at_dose grid</caption><thead><tr><th>Dose (mg)</th><th>MD (%)</th><th>95% CI</th></tr></thead><tbody>';
  hba1cRcs.rcs.fit_at_dose.forEach(function (p) {
    rcsCurveHtml += '<tr><td>' + p.dose.toFixed(2) + '</td>' +
                    '<td>' + p.est.toFixed(4) + '</td>' +
                    '<td>' + p.ci_lo.toFixed(4) + ' to ' + p.ci_hi.toFixed(4) + '</td></tr>';
  });
  rcsCurveHtml += '</tbody></table></div>';
  document.getElementById('hba1c-rcs-curve').innerHTML = rcsCurveHtml;

  // RCS per-study forest (RE-weighted via tau2_per_dim[0])
  var rcsForestRows = DR.forest(hba1cTrials, hba1cRcs);
  var rfHtml = '<h3>Per-study forest (RCS linear-component, RE-weighted)</h3><div class="table-scroll"><table><caption>Per-study HbA1c MD per mg (linear-component slope), RE-weighted via tau2_per_dim[0]</caption><thead><tr><th>Study</th><th>MD per mg</th><th>95% CI</th><th>RE weight</th></tr></thead><tbody>';
  rcsForestRows.forEach(function (r) {
    rfHtml += '<tr><td>' + escapeHtml(r.label) + '</td>' +
              '<td>' + r.slope_log.toFixed(5) + '</td>' +
              '<td>' + (r.slope_log - 1.96 * r.slope_log_se).toFixed(5) + ' to ' + (r.slope_log + 1.96 * r.slope_log_se).toFixed(5) + '</td>' +
              '<td>' + r.weight_pct.toFixed(1) + '%</td></tr>';
  });
  rfHtml += '</tbody></table></div>';
  document.getElementById('hba1c-rcs-forest').innerHTML = rfHtml;

  // === Tab 3: LOO sensitivity (v0.5.0) ===
  // Run leave-one-out RCS sensitivity over the 5-trial SURPASS pool.  fitLOO
  // orchestrates fitRCS(subset) for each k-1=4 subset and computes per-trial
  // delta vs the full pool.  The headline tirzepatide finding (nonlin Wald
  // p = 0.0346) is the full-pool result; LOO surfaces which trial drives it
  // most and whether dropping any one trial flips the significance verdict.
  var hba1cLoo;
  try {
    hba1cLoo = DR._internal.fitLOO(hba1cTrials, { layer: 'rcs', knots: 3 });
  } catch (e) {
    console.error('[tirz] fitLOO failed:', e);
    document.getElementById('hba1c-loo-kpis').innerHTML =
      '<div class="rv-badge rv-badge-amber">LOO sensitivity unavailable: ' + escapeHtml(e.message) + '</div>';
    hba1cLoo = null;
  }
  if (hba1cLoo) {
    var fullNlP = hba1cLoo.full_pool.rcs ? hba1cLoo.full_pool.rcs.nonlinearity_wald_p : null;
    // Max-swing nlP = LOO entry whose nlP differs most from the full-pool nlP.
    var maxSwingP = null, maxSwingTrial = null, maxSwingDelta = 0;
    hba1cLoo.loo.forEach(function (e) {
      if (e.nonlinearity_wald_p != null && fullNlP != null) {
        var d = Math.abs(e.nonlinearity_wald_p - fullNlP);
        if (d > maxSwingDelta) {
          maxSwingDelta = d;
          maxSwingP = e.nonlinearity_wald_p;
          maxSwingTrial = e.dropped_studlab;
        }
      }
    });

    document.getElementById('hba1c-loo-kpis').innerHTML =
      '<div class="kpi-grid">' +
      '<div class="kpi"><div class="kpi-label">Full-pool nonlin Wald p</div><div class="kpi-value">' + (fullNlP != null ? fullNlP.toFixed(4) : 'n/a') + '</div><div>headline finding (' + hba1cLoo.k_full + ' trials)</div></div>' +
      '<div class="kpi"><div class="kpi-label">Max-swing nonlin p (LOO)</div><div class="kpi-value">' + (maxSwingP != null ? maxSwingP.toFixed(4) : 'n/a') + '</div><div>when dropping ' + (maxSwingTrial ? escapeHtml(String(maxSwingTrial).split(' ')[0]) : 'n/a') + '</div></div>' +
      '<div class="kpi"><div class="kpi-label">Most influential trial</div><div class="kpi-value">' + (hba1cLoo.summary.most_influential_trial ? escapeHtml(String(hba1cLoo.summary.most_influential_trial).split(' ')[0]) : 'n/a') + '</div><div>max |Δslope| = ' + hba1cLoo.summary.max_abs_delta_slope.toFixed(5) + '</div></div>' +
      '<div class="kpi"><div class="kpi-label">Significance flips</div><div class="kpi-value">' + (hba1cLoo.summary.any_significance_flip ? 'YES' : 'No') + '</div><div>any subset crosses p=0.05</div></div>' +
      '<div class="kpi"><div class="kpi-label">Sign flips</div><div class="kpi-value">' + (hba1cLoo.summary.any_sign_flip ? 'YES' : 'No') + '</div><div>any subset flips slope CI sign</div></div>' +
      '<div class="kpi"><div class="kpi-label">Degenerated subsets</div><div class="kpi-value">' + hba1cLoo.summary.n_degenerated + ' / ' + hba1cLoo.loo.length + '</div><div>RCS-fallback fires</div></div>' +
      '</div>';

    // Headline banner — what the LOO actually tells us about the v0.3.0 finding
    var hlClass = hba1cLoo.summary.any_significance_flip ? 'rv-badge-amber' : 'rv-badge-green';
    var hlText = hba1cLoo.summary.any_significance_flip
      ? 'AMBER — at least one LOO subset crosses the p=0.05 boundary. The headline non-linearity finding is sensitive to the removal of the indicated trial(s); read the per-trial delta table below.'
      : 'GREEN — no LOO subset flips the significance verdict; the headline non-linearity finding is robust to dropping any single trial.';
    document.getElementById('hba1c-loo-headline').innerHTML =
      '<div class="rv-badge ' + hlClass + '">' +
      '<strong>LOO headline:</strong> Most influential trial: <em>' + escapeHtml(String(hba1cLoo.summary.most_influential_trial || 'n/a')) + '</em> (max |Δslope| = ' + hba1cLoo.summary.max_abs_delta_slope.toFixed(5) + '). ' + hlText + '<br>' +
      '<span class="rv-disclosure">Each row below drops one SURPASS trial and re-fits the RCS pool on the remaining k-1=4 trials.  The full-pool RCS finding is non-linearity Wald p = ' + (fullNlP != null ? fullNlP.toFixed(4) : 'n/a') + ' (Tab 2 headline).  Engine: ' + escapeHtml(DR.engine_version) + '; LOO orchestrated by <code>DR._internal.fitLOO({layer:&#39;rcs&#39;, knots:3})</code>.</span></div>';

    // Per-LOO table
    var looTblHtml = '<h3>Per-trial leave-one-out re-fit (RCS layer)</h3>' +
      '<div class="table-scroll"><table>' +
      '<caption>Each row drops one SURPASS trial and re-fits the RCS pool on the remaining 4 trials.  Δslope = LOO pooled_slope_log − full-pool pooled_slope_log (negative = drop made the slope steeper).</caption>' +
      '<thead><tr><th>Dropped trial</th><th>k<sub>loo</sub></th><th>Pooled slope (log)</th><th>95% CI</th><th>Nonlin p</th><th>Δslope</th><th>Sign flip</th><th>Sig flip</th><th>Degenerated</th></tr></thead><tbody>';
    hba1cLoo.loo.forEach(function (e) {
      var rowCls = e.significance_flip ? ' class="rv-row-amber"' : (e.sign_flip ? ' class="rv-row-amber"' : '');
      looTblHtml += '<tr' + rowCls + '>' +
        '<td>' + escapeHtml(String(e.dropped_studlab)) + '</td>' +
        '<td>' + e.k_loo + '</td>' +
        '<td>' + (Number.isFinite(e.pooled_slope_log) ? e.pooled_slope_log.toFixed(5) : 'n/a') + '</td>' +
        '<td>' + (Number.isFinite(e.pooled_slope_log_ci_lo) ? e.pooled_slope_log_ci_lo.toFixed(5) : 'n/a') + ' to ' + (Number.isFinite(e.pooled_slope_log_ci_hi) ? e.pooled_slope_log_ci_hi.toFixed(5) : 'n/a') + '</td>' +
        '<td>' + (e.nonlinearity_wald_p != null ? e.nonlinearity_wald_p.toFixed(4) : 'n/a') + '</td>' +
        '<td>' + (Number.isFinite(e.delta_slope) ? e.delta_slope.toFixed(5) : 'n/a') + '</td>' +
        '<td>' + (e.sign_flip ? 'YES' : 'no') + '</td>' +
        '<td>' + (e.significance_flip ? 'YES' : 'no') + '</td>' +
        '<td>' + (e.degenerated ? 'YES' : 'no') + '</td>' +
        '</tr>';
    });
    looTblHtml += '</tbody></table></div>';
    document.getElementById('hba1c-loo-table').innerHTML = looTblHtml;

    // Δslope bar (text-bar visualisation: one row per LOO subset showing magnitude
    // of Δslope as a unicode-block bar; avoids SVG so CSP stays strict).  Max bar
    // width 40 chars; scale relative to max_abs_delta_slope.
    var maxAbs = hba1cLoo.summary.max_abs_delta_slope || 1e-12;
    var barHtml = '<h3>Δslope visual (per LOO subset)</h3>' +
      '<div class="table-scroll"><table><caption>Bar chart: width proportional to |Δslope| relative to max swing across the 5 LOO subsets.  Direction marker: ▲ = LOO slope steeper than full pool (more negative); ▼ = LOO slope flatter than full pool.</caption>' +
      '<thead><tr><th>Dropped trial</th><th>Δslope</th><th>Bar</th></tr></thead><tbody>';
    hba1cLoo.loo.forEach(function (e) {
      var d = e.delta_slope;
      var w = Number.isFinite(d) ? Math.round(40 * Math.abs(d) / maxAbs) : 0;
      var bar = (d < 0 ? '▲ ' : '▼ ') + '█'.repeat(Math.max(0, w));
      barHtml += '<tr><td>' + escapeHtml(String(e.dropped_studlab)) + '</td>' +
        '<td>' + (Number.isFinite(d) ? d.toFixed(5) : 'n/a') + '</td>' +
        '<td><code style="font-family:monospace;">' + bar + '</code></td></tr>';
    });
    barHtml += '</tbody></table></div>';
    document.getElementById('hba1c-loo-deltabar').innerHTML = barHtml;

    document.getElementById('hba1c-loo-methods').innerHTML =
      '<p><strong>Methodology:</strong> Leave-one-out (LOO) sensitivity is a standard meta-analysis robustness check: re-fit the pooled model k times, each time leaving out one trial, and inspect how the headline quantity moves.  Here the headline is the RCS non-linearity Wald p-value (full pool: ' + (fullNlP != null ? fullNlP.toFixed(4) : 'n/a') + ').  Engine v0.5.0 adds <code>DR._internal.fitLOO(trials, {layer, knots})</code> which orchestrates the k re-fits using the same fitRCS / fitLinear primitives that produce the full-pool fit; no new statistical machinery is introduced.  Per-trial delta = LOO_pooled_slope − full_pool_slope; sign_flip fires when the LOO CI-lower-bound sign differs from the full-pool sign; significance_flip fires when the LOO nonlin Wald p crosses 0.05.</p>' +
      '<p style="margin-top:0.6em; font-size:0.92em; color:#444;"><strong>Interpretation for SURPASS:</strong> The full-pool finding (Wald p = ' + (fullNlP != null ? fullNlP.toFixed(4) : 'n/a') + ', headline of Tab 2) is sensitive to dropping either of the two placebo-anchored trials (SURPASS-1, SURPASS-5) — without one of those, the non-linearity p rises above 0.05 and the saturation finding is no longer significant at the 5% threshold.  The 3 active-comparator trials (SURPASS-2/-3/-4, where 5 mg serves as the reference per Option A) carry less weight for the non-linearity test because they contribute no information at the 0-to-5 mg interval where the saturation curve is steepest.  The LOO sensitivity is therefore a leading indicator that the full-pool finding is borderline-significant and would benefit from a future trial measuring sub-5 mg tirzepatide.  This LOO output is shown as a sensitivity check for the Tab 2 headline, not as a replacement primary analysis.</p>';
  }

  // Render abstracts inline
  fetch('fixtures/dose_response/tirzepatide_t2d_surpass_abstracts.json').then(function (r) {
    if (!r.ok) throw new Error('abstracts JSON: HTTP ' + r.status);
    return r.json();
  }).then(function (abs) {
    var mount = document.getElementById('abstracts-mount');
    var html = '';
    abs.publications.forEach(function (p) {
      html += '<details>' +
        '<summary>' + escapeHtml(p.trial_label) + ' — ' + escapeHtml(p.first_author) + ', ' + escapeHtml(p.journal) + ' ' + p.year + ' (PMID ' + escapeHtml(p.pmid) + ')</summary>' +
        '<div class="abstract-block">' +
        '<p class="abstract-meta"><strong>' + escapeHtml(p.title) + '</strong></p>' +
        '<p class="abstract-meta">' + escapeHtml(p.authors_short) + ' · <em>' + escapeHtml(p.journal) + '</em> ' + p.year + ';' + escapeHtml(p.volume) + (p.issue ? '(' + escapeHtml(p.issue) + ')' : '') + ':' + escapeHtml(p.pages) + ' · ' +
        '<a href="' + escapeHtml(p.doi_link) + '" target="_blank" rel="noopener noreferrer">doi:' + escapeHtml(p.doi) + '</a> · ' +
        '<a href="https://pubmed.ncbi.nlm.nih.gov/' + escapeHtml(p.pmid) + '/" target="_blank" rel="noopener noreferrer">PubMed ' + escapeHtml(p.pmid) + '</a> · ' +
        '<a href="https://clinicaltrials.gov/ct2/show/' + escapeHtml(p.nct_id) + '" target="_blank" rel="noopener noreferrer">' + escapeHtml(p.nct_id) + '</a>' +
        '</p>' +
        '<p><strong>Abstract (according to PubMed):</strong> ' + escapeHtml(p.abstract) + '</p>' +
        '<p style="font-size:0.92em; color:#444;"><strong>Dose-response summary:</strong> ' + escapeHtml(p.primary_endpoint_text) + '</p>' +
        '</div>' +
        '</details>';
    });
    mount.innerHTML = html;
  }).catch(function (e) {
    console.error('[tirz] abstracts fetch failed:', e);
    document.getElementById('abstracts-mount').innerHTML = '<p style="color:#92400e;">Abstracts unavailable: ' + escapeHtml(e.message) + '. See <code>fixtures/dose_response/tirzepatide_t2d_surpass_abstracts.json</code>.</p>';
  });

  // Load R precompute for one-stage + R-parity badge
  fetch('outputs/r_validation/doseresp/tirzepatide_t2d_surpass.json').then(function (r) {
    if (!r.ok) throw new Error('HbA1c R JSON: HTTP ' + r.status);
    return r.json();
  }).then(function (rHba1c) {
    // === Tab 3: HbA1c One-stage ===
    var hba1cOs = DR.fitOneStage(hba1cTrials, {}, rHba1c);
    if (!hba1cOs || !hba1cOs.one_stage || hba1cOs.one_stage.fit_ok === false) {
      document.getElementById('hba1c-os-kpis').innerHTML =
        '<div class="rv-badge rv-badge-amber">One-stage R output unavailable. Run <code>python scripts/r_validate_doseresp.py --review tirzepatide_t2d_surpass</code> to populate.</div>';
    } else {
      var os = hba1cOs.one_stage;
      var osMdAt15 = os.coef_dose * 15;
      document.getElementById('hba1c-os-kpis').innerHTML =
        '<div class="kpi-grid">' +
        '<div class="kpi"><div class="kpi-label">MD at 15 mg (one-stage)</div><div class="kpi-value">' + osMdAt15.toFixed(3) + '%</div><div>95% CI ' + (os.coef_dose_ci_lo*15).toFixed(3) + ' to ' + (os.coef_dose_ci_hi*15).toFixed(3) + '</div></div>' +
        '<div class="kpi"><div class="kpi-label">coef_dose (per mg)</div><div class="kpi-value">' + os.coef_dose.toFixed(5) + '</div><div>SE ' + os.coef_dose_se.toFixed(5) + '</div></div>' +
        '<div class="kpi"><div class="kpi-label">Random-effects variance</div><div class="kpi-value">' + (os.random_effects_var != null ? os.random_effects_var.toFixed(5) : 'n/a') + '</div></div>' +
        '<div class="kpi"><div class="kpi-label">Converged</div><div class="kpi-value">' + (os.converged ? 'Yes' : 'No') + '</div>' + (!os.converged ? '<div style="color:#92400e">solver flagged non-convergence (random-effects variance pinned at boundary)</div>' : '') + '</div>' +
        '<div class="kpi"><div class="kpi-label">Solver</div><div class="kpi-value">lme4 ' + escapeHtml(os.lme4_version || 'unknown') + '</div></div>' +
        (os.dose_scale_sd != null ? '<div class="kpi"><div class="kpi-label">dose_scale_sd (audit)</div><div class="kpi-value">' + os.dose_scale_sd.toFixed(3) + '</div></div>' : '') +
        '</div>';
      document.getElementById('hba1c-os-methods').innerHTML =
        '<p><strong>Methodology:</strong> One-stage hierarchical model fit by R using <code>lme4::lmer(mean ~ dose + (1 | studlab), data = df, weights = 1/(sd^2/n), REML = TRUE)</code> with the bobyqa optimizer. Per-arm HbA1c change modelled on the original scale; per-arm precision weights (inverse-variance) reflect within-arm sampling uncertainty. Random study intercept captures between-study baseline-HbA1c variation. Dose rescaling by <code>sd(dose[dose &gt; 0])</code> for convergence; coefficient back-transformed to per-mg scale.</p>' +
        '<p style="margin-top:0.6em; font-size:0.92em;"><strong>Why this differs from Tab 1:</strong> The one-stage estimate is the linear-model fit on the per-arm data with a random study intercept. The two-stage estimate (Tab 1) fits a per-trial GL slope and pools the slopes. With 3 same-molecule dose levels per trial, the two-stage GL slope is heavily dominated by the within-trial 5-to-15 mg incremental contrast, while the one-stage estimate is dominated by the overall mean-vs-dose-level fit. The qualitative agreement (both ≈ -0.07 per mg, both close to the unweighted naive arithmetic) is reassuring.</p>' +
        '<p style="margin-top:0.6em; font-size:0.92em; color:#92400e;"><strong>Non-convergence note:</strong> R reports the random-effects variance pinned at 0 (boundary), meaning between-trial variation in the dose-coefficient is too small relative to within-arm sampling variance to identify a positive random-effects variance. This is a benign artefact of the small k (k = 5); the fixed-effect coefficient and SE remain interpretable.</p>';
    }

    // === Tab 4: R-parity badge ===
    window.RValidationDoseresp.render('r-parity-tirzepatide-hba1c',
      { linear: hba1cLin, rcs: hba1cRcs, one_stage: hba1cOs },
      rHba1c);

  }).catch(function (e) {
    console.error('[tirz] R JSON load failed:', e);
    document.getElementById('hba1c-os-kpis').textContent = 'One-stage tab unavailable: ' + e.message;
    document.getElementById('r-parity-tirzepatide-hba1c').textContent = 'R-parity badge unavailable: ' + e.message;
  });

});
