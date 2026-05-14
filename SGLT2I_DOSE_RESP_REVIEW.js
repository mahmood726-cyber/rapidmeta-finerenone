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

function escapeHtmlSglt(s) {
  if (s == null) return '';
  return String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;')
    .replace(/>/g, '&gt;').replace(/"/g, '&quot;').replace(/'/g, '&#39;');
}

// Render an LOO KPI bar + headline banner + per-trial table (and optional Δslope bar).
// loo = result of DR._internal.fitLOO; kpiId/headId/tableId are DOM mount ids;
// barId (optional) renders the unicode delta-bar visual; layerLabel is a short
// human-readable layer descriptor used in the headline disclosure.
function renderLooBlock(loo, kpiId, headId, tableId, barId, layerLabel, engineVersion) {
  var fullNlP = loo.full_pool.rcs ? loo.full_pool.rcs.nonlinearity_wald_p : null;
  var maxSwingP = null, maxSwingTrial = null, maxSwingDelta = 0;
  loo.loo.forEach(function (e) {
    if (e.nonlinearity_wald_p != null && fullNlP != null) {
      var d = Math.abs(e.nonlinearity_wald_p - fullNlP);
      if (d > maxSwingDelta) { maxSwingDelta = d; maxSwingP = e.nonlinearity_wald_p; maxSwingTrial = e.dropped_studlab; }
    }
  });
  document.getElementById(kpiId).innerHTML =
    '<div class="kpi-grid">' +
    '<div class="kpi"><div class="kpi-label">Full-pool nonlin Wald p</div><div class="kpi-value">' + (fullNlP != null ? fullNlP.toFixed(4) : 'n/a') + '</div><div>headline (' + loo.k_full + ' trials)</div></div>' +
    '<div class="kpi"><div class="kpi-label">Max-swing nonlin p (LOO)</div><div class="kpi-value">' + (maxSwingP != null ? maxSwingP.toFixed(4) : 'n/a') + '</div><div>when dropping ' + (maxSwingTrial ? escapeHtmlSglt(String(maxSwingTrial).split(' ')[0]) : 'n/a') + '</div></div>' +
    '<div class="kpi"><div class="kpi-label">Most influential trial</div><div class="kpi-value">' + (loo.summary.most_influential_trial ? escapeHtmlSglt(String(loo.summary.most_influential_trial).split(' ')[0]) : 'n/a') + '</div><div>max |Δslope| = ' + loo.summary.max_abs_delta_slope.toFixed(5) + '</div></div>' +
    '<div class="kpi"><div class="kpi-label">Significance flips</div><div class="kpi-value">' + (loo.summary.any_significance_flip ? 'YES' : 'No') + '</div><div>any subset crosses p=0.05</div></div>' +
    '<div class="kpi"><div class="kpi-label">Sign flips</div><div class="kpi-value">' + (loo.summary.any_sign_flip ? 'YES' : 'No') + '</div><div>any subset flips slope CI sign</div></div>' +
    '<div class="kpi"><div class="kpi-label">Degenerated subsets</div><div class="kpi-value">' + loo.summary.n_degenerated + ' / ' + loo.loo.length + '</div><div>RCS/linear fallback fires</div></div>' +
    '</div>';

  var hlClass = loo.summary.any_significance_flip ? 'rv-badge-amber' : (loo.summary.any_sign_flip ? 'rv-badge-amber' : 'rv-badge-green');
  var hlText = loo.summary.any_significance_flip
    ? 'AMBER — at least one LOO subset crosses the p=0.05 boundary. Headline non-linearity verdict is sensitive to dropping the indicated trial(s).'
    : (loo.summary.any_sign_flip ? 'AMBER — at least one LOO subset flips the slope CI-sign relative to the full pool.' : 'GREEN — no LOO subset flips the significance or sign verdict; headline is robust to dropping any single trial.');
  document.getElementById(headId).innerHTML =
    '<div class="rv-badge ' + hlClass + '">' +
    '<strong>LOO headline (' + escapeHtmlSglt(layerLabel) + '):</strong> Most influential: <em>' + escapeHtmlSglt(String(loo.summary.most_influential_trial || 'n/a')) + '</em> (max |Δslope| = ' + loo.summary.max_abs_delta_slope.toFixed(5) + '). ' + hlText + '<br>' +
    '<span class="rv-disclosure">Engine: ' + escapeHtmlSglt(engineVersion) + '; LOO via <code>DR._internal.fitLOO({layer:&#39;' + escapeHtmlSglt(loo.layer) + '&#39;, knots:3})</code>.</span></div>';

  var looTblHtml = '<div class="table-scroll"><table>' +
    '<caption>Each row drops one trial and re-fits on the remaining k-1 trials. Δslope = LOO pooled_slope_log − full-pool pooled_slope_log.</caption>' +
    '<thead><tr><th>Dropped trial</th><th>k<sub>loo</sub></th><th>Pooled slope (log)</th><th>95% CI</th><th>Nonlin p</th><th>Δslope</th><th>Sign flip</th><th>Sig flip</th><th>Degenerated</th></tr></thead><tbody>';
  loo.loo.forEach(function (e) {
    var rowCls = (e.significance_flip || e.sign_flip) ? ' class="rv-row-amber"' : '';
    looTblHtml += '<tr' + rowCls + '>' +
      '<td>' + escapeHtmlSglt(String(e.dropped_studlab)) + '</td>' +
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
  document.getElementById(tableId).innerHTML = looTblHtml;

  if (barId) {
    var maxAbs = loo.summary.max_abs_delta_slope || 1e-12;
    var barHtml = '<div class="table-scroll"><table><caption>Bar chart: width proportional to |Δslope| relative to max swing. ▲ = LOO slope steeper than full pool; ▼ = LOO slope flatter.</caption>' +
      '<thead><tr><th>Dropped trial</th><th>Δslope</th><th>Bar</th></tr></thead><tbody>';
    loo.loo.forEach(function (e) {
      var d = e.delta_slope;
      var w = Number.isFinite(d) ? Math.round(40 * Math.abs(d) / maxAbs) : 0;
      var bar = (d < 0 ? '▲ ' : '▼ ') + '█'.repeat(Math.max(0, w));
      barHtml += '<tr><td>' + escapeHtmlSglt(String(e.dropped_studlab)) + '</td>' +
        '<td>' + (Number.isFinite(d) ? d.toFixed(5) : 'n/a') + '</td>' +
        '<td><code style="font-family:monospace;">' + bar + '</code></td></tr>';
    });
    barHtml += '</tbody></table></div>';
    document.getElementById(barId).innerHTML = barHtml;
  }
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
  var mdPer10mg = hba1cLin.pooled_slope_log * 10;
  var mdPer10mg_lo = hba1cLin.pooled_slope_log_ci_lo * 10;
  var mdPer10mg_hi = hba1cLin.pooled_slope_log_ci_hi * 10;

  document.getElementById('hba1c-linear-kpis').innerHTML =
    '<div class="kpi-grid">' +
    '<div class="kpi"><div class="kpi-label">HbA1c change per 10 mg dose</div><div class="kpi-value">' + mdPer10mg.toFixed(3) + '%</div><div>95% CI ' + mdPer10mg_lo.toFixed(3) + ' to ' + mdPer10mg_hi.toFixed(3) + '</div></div>' +
    '<div class="kpi"><div class="kpi-label">MD per mg dose</div><div class="kpi-value">' + hba1cLin.pooled_slope_log.toFixed(5) + '</div><div>SE ' + hba1cLin.pooled_slope_log_se.toFixed(5) + '</div></div>' +
    '<div class="kpi"><div class="kpi-label">τ²</div><div class="kpi-value">' + hba1cLin.tau2.toExponential(2) + '</div></div>' +
    '<div class="kpi"><div class="kpi-label">I²</div><div class="kpi-value">' + hba1cLin.I2.toFixed(1) + '%</div><div>Q = ' + hba1cLin.Q.toFixed(2) + ' (df ' + hba1cLin.Q_df + ')</div></div>' +
    '<div class="kpi"><div class="kpi-label">PI (per 10 mg, df=' + hba1cLin.pi_df + ')</div><div class="kpi-value">' + (hba1cLin.pi_lo*10).toFixed(3) + ' to ' + (hba1cLin.pi_hi*10).toFixed(3) + '</div></div>' +
    '<div class="kpi"><div class="kpi-label">k</div><div class="kpi-value">' + hba1cLin.k + '</div>' + (hba1cLin.coverage_warning ? '<div style="color:#92400e">coverage warning: k&lt;10</div>' : '') + '</div>' +
    '</div>';

  // Per-study forest (continuous mode: slope_log = MD per mg, no exp transform)
  var hba1cForestRows = DR.forest(hba1cTrials, hba1cLin);
  var hba1cFHtml = '<h3>Per-study forest (HbA1c, linear layer, RE-weighted)</h3><div class="table-scroll"><table><caption>Per-study HbA1c MD per mg dose with 95% CI</caption><thead><tr><th>Study</th><th>MD per mg</th><th>95% CI</th><th>Weight</th></tr></thead><tbody>';
  hba1cForestRows.forEach(function (r) {
    hba1cFHtml += '<tr><td>' + r.label + '</td>' +
                  '<td>' + r.slope_log.toFixed(5) + '</td>' +
                  '<td>' + (r.slope_log - 1.96 * r.slope_log_se).toFixed(5) + ' to ' + (r.slope_log + 1.96 * r.slope_log_se).toFixed(5) + '</td>' +
                  '<td>' + r.weight_pct.toFixed(1) + '%</td></tr>';
  });
  hba1cFHtml += '</tbody></table></div>';
  document.getElementById('hba1c-linear-forest').innerHTML = hba1cFHtml;

  // Dose-response curve (20-point grid, 0 to max observed dose)
  var maxObs = hba1cLin.max_observed_dose;
  var hba1cCurveHtml = '<h3>Dose-response curve (95% CI via t<sub>' + hba1cLin.pi_df + '</sub>)</h3><div class="table-scroll"><table><caption>HbA1c MD per arm dose, 20-point grid 0 to ' + maxObs + ' mg</caption><thead><tr><th>Dose (mg)</th><th>MD (%)</th><th>95% CI</th></tr></thead><tbody>';
  for (var i = 0; i < 20; i++) {
    var d = i * maxObs / 19;
    var p = DR.predict(hba1cLin, d);
    hba1cCurveHtml += '<tr><td>' + d.toFixed(2) + '</td>' +
                     '<td>' + p.est.toFixed(4) + '</td>' +
                     '<td>' + p.ci_lo.toFixed(4) + ' to ' + p.ci_hi.toFixed(4) + '</td></tr>';
  }
  hba1cCurveHtml += '</tbody></table></div>';
  document.getElementById('hba1c-linear-curve').innerHTML = hba1cCurveHtml;

  // Plain-English summary
  document.getElementById('hba1c-linear-summary').innerHTML =
    '<p><strong>Plain-English summary:</strong> Each additional 10 mg of SGLT2 inhibitor (raw mg across 3 drugs at the pooled-class scale) is associated with a HbA1c reduction of approximately ' + Math.abs(mdPer10mg).toFixed(2) + ' percentage points (95% CI ' + Math.abs(mdPer10mg_hi).toFixed(2) + ' to ' + Math.abs(mdPer10mg_lo).toFixed(2) + '). The estimate combines 3 trials across 3 different SGLT2i drugs at the raw-mg dose scale; see Methods for the class-equivalence caveat.</p>' +
    '<p style="margin-top:0.6em; font-size:0.92em; color:#444;"><strong>Caveat:</strong> The raw-mg cross-drug pool assumes equipotent per-mg effects, which is methodologically debatable. Per-drug analyses or %-of-max-dose harmonization would be defensible alternatives.</p>';

  // === Tab 2: HbA1c RCS ===
  var hba1cRcs = DR.fitRCS(hba1cTrials, { knots: 3 });

  document.getElementById('hba1c-rcs-kpis').innerHTML =
    '<div class="kpi-grid">' +
    '<div class="kpi"><div class="kpi-label">Knots (mg)</div><div class="kpi-value">' + hba1cRcs.rcs.knots.map(function (k) { return k.toFixed(1); }).join(', ') + '</div></div>' +
    '<div class="kpi"><div class="kpi-label">spline_coefs[0] (linear)</div><div class="kpi-value">' + hba1cRcs.rcs.spline_coefs[0].toFixed(5) + '</div><div>SE ' + hba1cRcs.rcs.spline_coefs_se[0].toFixed(5) + '</div></div>' +
    '<div class="kpi"><div class="kpi-label">spline_coefs[1] (non-linear)</div><div class="kpi-value">' + hba1cRcs.rcs.spline_coefs[1].toFixed(5) + '</div><div>SE ' + hba1cRcs.rcs.spline_coefs_se[1].toFixed(5) + '</div></div>' +
    '<div class="kpi"><div class="kpi-label">Wald non-linearity p</div><div class="kpi-value">' + hba1cRcs.rcs.nonlinearity_wald_p.toFixed(4) + '</div><div>(full REML v0.3, HKSJ-mv = ' + (hba1cRcs.hksj_mv != null ? hba1cRcs.hksj_mv.toFixed(2) : 'n/a') + ')</div></div>' +
    '<div class="kpi"><div class="kpi-label">τ² per dim</div><div class="kpi-value">[' + hba1cRcs.rcs.tau2_per_dim.map(function (t) { return t.toExponential(2); }).join(', ') + ']</div></div>' +
    '</div>';

  // RCS curve via fit_at_dose grid
  var rcsCurveHtml = '<h3>RCS dose-response curve (HbA1c)</h3><div class="table-scroll"><table><caption>RCS dose-response curve via 20-point fit_at_dose grid</caption><thead><tr><th>Dose (mg)</th><th>MD (%)</th><th>95% CI</th></tr></thead><tbody>';
  hba1cRcs.rcs.fit_at_dose.forEach(function (p) {
    rcsCurveHtml += '<tr><td>' + p.dose.toFixed(2) + '</td>' +
                    '<td>' + p.est.toFixed(4) + '</td>' +
                    '<td>' + p.ci_lo.toFixed(4) + ' to ' + p.ci_hi.toFixed(4) + '</td></tr>';
  });
  rcsCurveHtml += '</tbody></table></div>';
  document.getElementById('hba1c-rcs-curve').innerHTML = rcsCurveHtml;

  // RCS per-study forest (F-3 RE-weighted via tau2_per_dim[0])
  var rcsForestRows = DR.forest(hba1cTrials, hba1cRcs);
  var rfHtml = '<h3>Per-study forest (RCS linear-component, RE-weighted)</h3><div class="table-scroll"><table><caption>Per-study HbA1c MD per mg (linear-component slope), RE-weighted via tau2_per_dim[0]</caption><thead><tr><th>Study</th><th>MD per mg</th><th>95% CI</th><th>RE weight</th></tr></thead><tbody>';
  rcsForestRows.forEach(function (r) {
    rfHtml += '<tr><td>' + r.label + '</td>' +
              '<td>' + r.slope_log.toFixed(5) + '</td>' +
              '<td>' + (r.slope_log - 1.96 * r.slope_log_se).toFixed(5) + ' to ' + (r.slope_log + 1.96 * r.slope_log_se).toFixed(5) + '</td>' +
              '<td>' + r.weight_pct.toFixed(1) + '%</td></tr>';
  });
  rfHtml += '</tbody></table></div>';
  document.getElementById('hba1c-rcs-forest').innerHTML = rfHtml;

  // Wald note (Round 2C: full-REML v0.3.0 closed the v0.1/v0.2 diagonal-PM gap)
  document.getElementById('hba1c-rcs-wald').innerHTML =
    '<div class="rv-badge rv-badge-green">' +
    '<strong>Wald non-linearity test (full multivariate REML v0.3.0):</strong> p = ' + hba1cRcs.rcs.nonlinearity_wald_p.toFixed(4) +
    ' (df = ' + (hba1cRcs.rcs.spline_coefs.length - 1) + ', χ² = ' + (hba1cRcs.rcs.nonlinearity_wald_chi2 != null ? hba1cRcs.rcs.nonlinearity_wald_chi2.toFixed(3) : 'n/a') + '). ' +
    'Engine v0.3.0 uses full multivariate REML via Nelder-Mead on Cholesky parameters of the τ² matrix; ' +
    'non-linearity p matches R mixmeta within |Δ| < 0.05 — see the R-parity tab for the side-by-side comparison. ' +
    'HKSJ-multivariate scaling factor: ' + (hba1cRcs.hksj_mv != null ? hba1cRcs.hksj_mv.toFixed(2) : 'n/a') + '; CI critical value t<sub>k-1</sub> = ' + (hba1cRcs.tcrit != null ? hba1cRcs.tcrit.toFixed(3) : 'n/a') + '.</div>';

  // === Tab 3a: HbA1c LOO sensitivity (engine v0.5.0) ===
  // RCS-layer LOO over the 3-trial HbA1c pool.
  var hba1cLoo;
  try {
    hba1cLoo = DR._internal.fitLOO(hba1cTrials, { layer: 'rcs', knots: 3 });
  } catch (e) {
    console.error('[SGLT2I-hba1c] fitLOO failed:', e);
    document.getElementById('hba1c-loo-kpis').innerHTML =
      '<div class="rv-badge rv-badge-amber">HbA1c LOO sensitivity unavailable: ' + escapeHtmlSglt(e.message) + '</div>';
    hba1cLoo = null;
  }
  if (hba1cLoo) {
    renderLooBlock(hba1cLoo, 'hba1c-loo-kpis', 'hba1c-loo-headline', 'hba1c-loo-table', null,
      'HbA1c RCS layer (k=' + hba1cLoo.k_full + ', cross-drug pool at raw mg scale)', DR.engine_version);
  }


  // Load R-precomputed JSON for HbA1c (Tabs 3 + 5a) and hHF (Tabs 4-secondary + 5b).
  Promise.all([
    fetch('outputs/r_validation/doseresp/sglt2i_hba1c.json').then(function (r) {
      if (!r.ok) throw new Error('HbA1c R JSON: HTTP ' + r.status);
      return r.json();
    }),
    fetch('outputs/r_validation/doseresp/sglt2i_hhf.json').then(function (r) {
      if (!r.ok) throw new Error('hHF R JSON: HTTP ' + r.status);
      return r.json();
    })
  ]).then(function (results) {
    var rHba1c = results[0];
    var rHhf = results[1];

    // === Tab 3: HbA1c One-stage ===
    var hba1cOs = DR.fitOneStage(hba1cTrials, {}, rHba1c);
    if (!hba1cOs || !hba1cOs.one_stage || hba1cOs.one_stage.fit_ok === false) {
      document.getElementById('hba1c-os-kpis').innerHTML =
        '<div class="rv-banner rv-banner-error">One-stage R output unavailable. Run <code>python scripts/r_validate_doseresp.py --review sglt2i_hba1c<\/code> to populate.<\/div>';
    } else {
      var os = hba1cOs.one_stage;
      var osMd10 = os.coef_dose * 10;
      document.getElementById('hba1c-os-kpis').innerHTML =
        '<div class="kpi-grid">' +
        '<div class="kpi"><div class="kpi-label">MD per 10 mg dose (one-stage)<\/div><div class="kpi-value">' + osMd10.toFixed(3) + '%<\/div><div>95% CI ' + (os.coef_dose_ci_lo*10).toFixed(3) + ' to ' + (os.coef_dose_ci_hi*10).toFixed(3) + '<\/div><\/div>' +
        '<div class="kpi"><div class="kpi-label">coef_dose (per mg)<\/div><div class="kpi-value">' + os.coef_dose.toFixed(5) + '<\/div><div>SE ' + os.coef_dose_se.toFixed(5) + '<\/div><\/div>' +
        '<div class="kpi"><div class="kpi-label">Random-effects variance<\/div><div class="kpi-value">' + (os.random_effects_var != null ? os.random_effects_var.toFixed(5) : 'n\/a') + '<\/div><\/div>' +
        '<div class="kpi"><div class="kpi-label">Converged<\/div><div class="kpi-value">' + (os.converged ? 'Yes' : 'No') + '<\/div><\/div>' +
        '<div class="kpi"><div class="kpi-label">Solver<\/div><div class="kpi-value">lme4 ' + (os.lme4_version || rHba1c.one_stage.lme4_version || 'unknown') + '<\/div><\/div>' +
        (os.dose_scale_sd != null ? '<div class="kpi"><div class="kpi-label">dose_scale_sd (audit)<\/div><div class="kpi-value">' + os.dose_scale_sd.toFixed(3) + '<\/div><\/div>' : '') +
        '<\/div>';
      document.getElementById('hba1c-os-methods').innerHTML =
        '<p><strong>Methodology:<\/strong> One-stage hierarchical model fit by R using <code>lme4::lmer(mean ~ dose + (1 | studlab), data = df, weights = 1\/(sd^2\/n), REML = TRUE)<\/code> with the bobyqa optimizer. Per-arm HbA1c change modelled on the original scale; per-arm precision weights (inverse-variance) reflect within-arm sampling uncertainty. Random study intercept captures between-study baseline-HbA1c variation. Dose rescaling by <code>sd(dose[dose > 0])<\/code> for convergence; coefficient back-transformed to per-mg scale.<\/p>' +
        '<p style="margin-top:0.6em; font-size:0.92em;"><strong>Why this differs from Tab 1:<\/strong> The one-stage estimate (MD per 10 mg) differs from the two-stage linear pool because the random study intercept absorbs between-study variation in baseline HbA1c, shifting the fixed-effect dose slope. Neither is wrong; they answer subtly different questions about the dose-response relationship.<\/p>';
    }

    // Read hHF trials (embedded JSON block in the page)
    var hhfScript = document.getElementById('doseresp-trials-hhf');
    var hhfTrials;
    try {
      hhfTrials = JSON.parse(hhfScript.textContent);
    } catch (e) {
      document.getElementById('hhf-kpis').textContent = 'hHF trial data malformed: ' + e.message;
      return;
    }

    // === Tab 4: hHF secondary (binary, k=2) ===
    var hhfLin = DR.fitLinear(hhfTrials, {});

    // Detect whether F-1 fired on any trial (zero-event arm anywhere)
    var f1Triggered = hhfTrials.some(function (t) {
      var ref = t.arms.find(function (a) { return a.is_reference; });
      return (ref && ref.events === 0) ||
             t.arms.some(function (a) { return !a.is_reference && a.events === 0; });
    });

    // RR per 10 mg back-transformed (binary mode: pooled_slope_log is log-RR)
    var hhfRR10 = Math.exp(hhfLin.pooled_slope_log * 10);
    var hhfRR10_lo = Math.exp(hhfLin.pooled_slope_log_ci_lo * 10);
    var hhfRR10_hi = Math.exp(hhfLin.pooled_slope_log_ci_hi * 10);

    document.getElementById('hhf-kpis').innerHTML =
      '<div class="kpi-grid">' +
      '<div class="kpi"><div class="kpi-label">RR per 10 mg dose</div><div class="kpi-value">' + hhfRR10.toFixed(3) + '</div><div>95% CI ' + hhfRR10_lo.toFixed(3) + ' to ' + hhfRR10_hi.toFixed(3) + '</div></div>' +
      '<div class="kpi"><div class="kpi-label">log-RR per mg</div><div class="kpi-value">' + hhfLin.pooled_slope_log.toFixed(5) + '</div><div>SE ' + hhfLin.pooled_slope_log_se.toFixed(5) + '</div></div>' +
      '<div class="kpi"><div class="kpi-label">τ²</div><div class="kpi-value">' + hhfLin.tau2.toExponential(2) + '</div></div>' +
      '<div class="kpi"><div class="kpi-label">I²</div><div class="kpi-value">' + hhfLin.I2.toFixed(1) + '%</div></div>' +
      '<div class="kpi"><div class="kpi-label">k</div><div class="kpi-value">' + hhfLin.k + '</div>' + (hhfLin.coverage_warning ? '<div style="color:#92400e">coverage warning: k&lt;10</div>' : '') + '</div>' +
      '</div>';

    document.getElementById('hhf-f1-badge').innerHTML = f1Triggered ?
      '<div class="rv-badge rv-badge-amber"><strong>F-1 zero-cell continuity correction:</strong> at least one trial has a zero-event arm; the engine applied +0.5 to events and +1.0 to n in BOTH reference and contrast arms of the affected trial(s). This is the conditional correction (only fires when ≥1 cell is zero) per advanced-stats.md. Without this correction the affected trial would produce log(0/p) = -Infinity and the pool would silently return NaN.</div>' :
      '<div class="rv-badge rv-badge-green"><strong>F-1 not triggered:</strong> all trials have ≥1 hHF event in every arm (EMPA-REG and CANVAS have nonzero placebo and dose-arm event counts). F-1 conditional correction is wired in the engine and tested via the regression test in <code>tests/test_dose_response_engine.mjs</code>; it does not fire on this real-world fixture.</div>';

    // Per-study forest (binary mode → use hr / hr_ci_lo / hr_ci_hi)
    var hhfForestRows = DR.forest(hhfTrials, hhfLin);
    var hhfFHtml = '<h3>Per-study forest (hHF, linear layer, RE-weighted)</h3><div class="table-scroll"><table><caption>Per-study hHF RR per mg dose with 95% CI</caption><thead><tr><th>Study</th><th>RR per mg</th><th>95% CI</th><th>Weight</th></tr></thead><tbody>';
    hhfForestRows.forEach(function (r) {
      hhfFHtml += '<tr><td>' + r.label + '</td>' +
                  '<td>' + r.hr.toFixed(4) + '</td>' +
                  '<td>' + r.hr_ci_lo.toFixed(4) + ' to ' + r.hr_ci_hi.toFixed(4) + '</td>' +
                  '<td>' + r.weight_pct.toFixed(1) + '%</td></tr>';
    });
    hhfFHtml += '</tbody></table></div>';
    document.getElementById('hhf-forest').innerHTML = hhfFHtml;

    document.getElementById('hhf-summary').innerHTML =
      '<p><strong>Plain-English summary:</strong> Across the 2 SGLT2i CVOTs with within-trial multi-dose randomization (EMPA-REG OUTCOME 10/25 mg empagliflozin; CANVAS Program 100/300 mg canagliflozin), each additional 10 mg of drug is associated with a relative-risk of ' + hhfRR10.toFixed(3) + ' for hospitalization for heart failure (95% CI ' + hhfRR10_lo.toFixed(3) + ' to ' + hhfRR10_hi.toFixed(3) + '). The estimate combines two drugs at the raw-mg dose scale — same class-equivalence caveat as the HbA1c tab. k = 2 (SOLOIST-WHF excluded as fixed-titration) < 10 triggers coverage_warning.</p>';

    // === Tab 3b: hHF LOO sensitivity (engine v0.5.0) — linear layer, k=2 ===
    // Each LOO subset drops to k=1; engine surfaces the surviving trial slope
    // with degenerated=true (no RCS layer at this layer).
    var hhfLoo;
    try {
      hhfLoo = DR._internal.fitLOO(hhfTrials, { layer: 'linear' });
    } catch (e) {
      console.error('[SGLT2I-hhf] fitLOO failed:', e);
      document.getElementById('hhf-loo-kpis').innerHTML =
        '<div class="rv-badge rv-badge-amber">hHF LOO sensitivity unavailable: ' + escapeHtmlSglt(e.message) + '</div>';
      hhfLoo = null;
    }
    if (hhfLoo) {
      renderLooBlock(hhfLoo, 'hhf-loo-kpis', 'hhf-loo-headline', 'hhf-loo-table', null,
        'hHF linear layer (k=' + hhfLoo.k_full + ', each LOO drops to k=1; engine single-trial fallback)', DR.engine_version);
      document.getElementById('loo-methods').innerHTML =
        '<p style="margin-top:1.6em;"><strong>Methodology:</strong> Leave-one-out (LOO) sensitivity re-fits the pooled model k times, each time leaving out one trial, and inspects how the headline quantity moves. The HbA1c block uses the RCS layer (3 knots, 3 trials); the hHF block uses the linear layer (k=2). At k=2, each LOO subset is k=1 and the engine reports the surviving trial&apos;s own slope with <code>degenerated=true</code>. Engine v0.5.0 helper: <code>DR._internal.fitLOO(trials, {layer, knots})</code>.</p>';
    }

    // === Tab 5: R-parity badges (Unit 7, Task 17) ===
    // Two mounts: HbA1c (continuous) + hHF (binary). hhfRcs may be null if fitRCS fails at k=2.
    window.RValidationDoseresp.render('r-parity-doseresp-hba1c',
      { linear: hba1cLin, rcs: hba1cRcs, one_stage: hba1cOs },
      rHba1c);

    // For hHF: compute fitRCS too (k=2 with 4 unique non-ref doses gives 3 knots; works)
    var hhfRcs = null;
    try {
      hhfRcs = DR.fitRCS(hhfTrials, {knots: 3});
    } catch (e) {
      console.warn('hHF fitRCS failed (likely k<2 after WLS):', e.message);
    }
    var hhfOs = DR.fitOneStage(hhfTrials, {}, rHhf);

    window.RValidationDoseresp.render('r-parity-doseresp-hhf',
      { linear: hhfLin, rcs: hhfRcs, one_stage: hhfOs },
      rHhf);

    // Populate trial-summary table (combines HbA1c and hHF fixtures; Task 17 Step 2)
    var summary = '<div class="table-scroll"><table><caption>Per-study summary across HbA1c + hHF outcomes</caption><thead><tr><th>Study</th><th>Drug</th><th>PMID</th><th>HbA1c arms</th><th>hHF arms</th></tr></thead><tbody>';
    var pmidSet = {};
    hba1cTrials.forEach(function (t) {
      pmidSet[t.pmid] = { studlab: t.studlab, drug: t.drug, hba1c: t.arms.length, hhf: 0 };
    });
    hhfTrials.forEach(function (t) {
      if (pmidSet[t.pmid]) {
        pmidSet[t.pmid].hhf = t.arms.length;
      } else {
        pmidSet[t.pmid] = { studlab: t.studlab, drug: t.drug, hba1c: 0, hhf: t.arms.length };
      }
    });
    Object.keys(pmidSet).forEach(function (pmid) {
      var s = pmidSet[pmid];
      summary += '<tr><td>' + s.studlab + '</td>' +
                 '<td>' + s.drug + '</td>' +
                 '<td><a href="https://pubmed.ncbi.nlm.nih.gov/' + pmid + '/" target="_blank" rel="noopener noreferrer">' + pmid + '</a></td>' +
                 '<td>' + s.hba1c + '</td>' +
                 '<td>' + s.hhf + '</td></tr>';
    });
    summary += '</tbody></table></div>';
    document.getElementById('trial-summary').innerHTML = summary;

  }).catch(function (e) {
    console.error('[SGLT2I] failed to load R JSON:', e);
    document.getElementById('hba1c-os-kpis').textContent = 'One-stage tab unavailable: ' + e.message;
    document.getElementById('r-parity-doseresp-hba1c').textContent = 'HbA1c R-parity unavailable: ' + e.message;
    document.getElementById('r-parity-doseresp-hhf').textContent = 'hHF R-parity unavailable: ' + e.message;
  });

});
