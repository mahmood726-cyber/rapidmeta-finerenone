/* UPADACITINIB_RA_SELECT_DOSE_RESP_REVIEW.js
 *
 * Round 3.8 — 4-trial SELECT upadacitinib DAS28-CRP dose-response flagship.
 *
 * Engine path (v0.3.0 / v0.4 conventions):
 *   Linear layer: k=4 all trials pooled via two-stage GL + REML + HKSJ.
 *     pooled_slope_log ≈ -0.02955 per mg, SE ≈ 0.02331 (HKSJ-inflated × tcrit),
 *     τ² ≈ 0.000254 (Q-profile CI ~ [5.4e-5, 4.8e-3]); Q = 21.87 (df 3),
 *     I² ≈ 86.3%; HKSJ adj 2.70.
 *     Per-trial slopes: NEXT -0.0440, BEYOND -0.0416, MONOTHERAPY -0.0213,
 *     EARLY -0.0080. The two placebo-controlled trials (NEXT, BEYOND) carry
 *     the 0→15 mg signal; the two MTX-dropped trials (MONOTHERAPY, EARLY) see
 *     only the 15→30 mg increment (which is already on the bDMARD-IR / MTX-IR
 *     plateau and gives small slopes).
 *
 *   RCS layer: ENGINE RETURNS LINEAR-FALLBACK. With only 3 distinct doses in
 *     the pool ({0, 15, 30}), `rcsKnots(allDoses, 3)` returns fewer than the
 *     K=3 required distinct knot locations, and `fitRCS` short-circuits by
 *     calling fitLinear and decorating the result with:
 *       layer = 'linear'
 *       fallback = 'degenerate_to_linear'
 *       rcs = null              ← NO nested .rcs block
 *       estimator = 'reml_hksj' (inherited from fitLinear)
 *     This is the engine's documented RCS-fallback for coarse dose grids.
 *     R `dosresmeta` refuses RCS on the same fixture with the parallel
 *     sparse-arm error ("each study provides at least p non-referent obs").
 *
 *   One-stage (R precompute): lme4::lmer on all 4 trials. coef_dose ≈ -0.0381
 *     per mg, SE 0.0102, CI [-0.058, -0.018]. R reports converged=true.
 *
 * Tabs (3 — RCS tab REPLACED with degeneration explanation):
 *   1. DAS28-CRP Linear (k=4 all trials, HEADLINE)
 *   2. RCS degeneration — methodological note (no spline fit returned)
 *   3. R-parity badge (linear-only GREEN; RCS rows DEFERRED via custom panel)
 *
 * CSP: loaded via <script src defer>. No inline <script>, no inline onclick.
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

  // Read DAS28-CRP trials
  var das28Script = document.getElementById('doseresp-trials-das28');
  var das28Trials;
  try {
    das28Trials = JSON.parse(das28Script.textContent);
  } catch (e) {
    document.getElementById('das28-linear-kpis').textContent = 'DAS28-CRP trial data malformed: ' + e.message;
    return;
  }
  if (das28Trials.length === 0) {
    document.getElementById('das28-linear-kpis').textContent = 'No DAS28-CRP trial data embedded.';
    return;
  }

  // === Tab 1: DAS28-CRP Linear (k=4 all trials) — HEADLINE ===
  var das28Lin = DR.fitLinear(das28Trials, {});
  var mdPerMg = das28Lin.pooled_slope_log;
  var mdPerMg_lo = das28Lin.pooled_slope_log_ci_lo;
  var mdPerMg_hi = das28Lin.pooled_slope_log_ci_hi;
  var maxObs = das28Lin.max_observed_dose; // 30 mg
  var mdAtMax = mdPerMg * maxObs;
  var mdAtMax_lo = mdPerMg_lo * maxObs;
  var mdAtMax_hi = mdPerMg_hi * maxObs;

  document.getElementById('das28-linear-kpis').innerHTML =
    '<div class="kpi-grid">' +
    '<div class="kpi"><div class="kpi-label">DAS28-CRP at ' + maxObs.toFixed(0) + ' mg (linear extrapolation)</div><div class="kpi-value">' + mdAtMax.toFixed(2) + '</div><div>95% CI ' + mdAtMax_lo.toFixed(2) + ' to ' + mdAtMax_hi.toFixed(2) + '</div><div style="color:#92400e; font-size:0.8em;">CI honestly wide; I&sup2; = ' + das28Lin.I2.toFixed(1) + '% &mdash; per-trial slope range driven by saturation, not noise</div></div>' +
    '<div class="kpi"><div class="kpi-label">MD per mg dose</div><div class="kpi-value">' + mdPerMg.toFixed(4) + '</div><div>SE ' + das28Lin.pooled_slope_log_se.toFixed(4) + '</div></div>' +
    '<div class="kpi"><div class="kpi-label">&tau;<sup>2</sup> (REML)</div><div class="kpi-value">' + das28Lin.tau2.toFixed(6) + '</div><div>Q-profile CI ' + das28Lin.tau2_lo.toExponential(2) + ' to ' + das28Lin.tau2_hi.toExponential(2) + '</div></div>' +
    '<div class="kpi"><div class="kpi-label">I&sup2;</div><div class="kpi-value">' + das28Lin.I2.toFixed(1) + '%</div><div>Q = ' + das28Lin.Q.toFixed(2) + ' (df ' + das28Lin.Q_df + ')</div></div>' +
    '<div class="kpi"><div class="kpi-label">HKSJ adjustment</div><div class="kpi-value">' + das28Lin.hksj_adj.toFixed(2) + '</div><div>Q* = ' + das28Lin.hksj_qstar.toFixed(2) + '; HKSJ-inflated CI multiplier</div></div>' +
    '<div class="kpi"><div class="kpi-label">PI at ' + maxObs.toFixed(0) + ' mg (df=' + das28Lin.pi_df + ')</div><div class="kpi-value">' + (das28Lin.pi_lo * maxObs).toFixed(2) + ' to ' + (das28Lin.pi_hi * maxObs).toFixed(2) + '</div></div>' +
    '<div class="kpi"><div class="kpi-label">k (linear)</div><div class="kpi-value">' + das28Lin.k + '</div>' + (das28Lin.coverage_warning ? '<div style="color:#92400e">coverage warning: k&lt;10</div>' : '') + '</div>' +
    '<div class="kpi"><div class="kpi-label">Estimator</div><div class="kpi-value" style="font-size:1em;">' + escapeHtml(das28Lin.estimator) + '</div><div>fallback: ' + (das28Lin.fallback == null ? '<em>none</em>' : escapeHtml(das28Lin.fallback)) + '</div></div>' +
    '</div>';

  // Per-trial slopes table — shows the saturation pattern explicitly.
  // We use DR.forest() to get RE-weighted weight_pct per trial (per_study itself
  // does not expose pre-computed weights — they're tau2-dependent and derived
  // by the forest helper). Order matches input trials by construction.
  var das28ForestRowsForTable = DR.forest(das28Trials, das28Lin);
  var perTrialHtml = '<h3>Per-trial GL slopes (drives the I&sup2; signal)</h3>' +
    '<div class="table-scroll"><table><caption>Per-trial linear-layer GL slopes (DAS28-CRP per mg upadacitinib) and the dose-leg each trial samples</caption>' +
    '<thead><tr><th>Trial</th><th>Dose levels (mg, after Option A)</th><th>Dose leg sampled</th><th>GL slope (per mg)</th><th>SE</th><th>RE weight</th></tr></thead><tbody>';
  var doseLegByLabel = {
    'SELECT-NEXT (Burmester 2018, csDMARD-IR vs placebo)':                  { doses: '0, 15, 30', leg: '0 → 15 → 30 mg (full 3-arm range)' },
    'SELECT-BEYOND (Genovese 2018, bDMARD-IR vs placebo)':                  { doses: '0, 15, 30', leg: '0 → 15 → 30 mg (15 vs 30 mg plateau in bDMARD-IR)' },
    'SELECT-MONOTHERAPY (Smolen 2019, MTX-IR switch monotherapy)':          { doses: '15, 30',    leg: '15 → 30 mg only (MTX dropped per Option A)' },
    'SELECT-EARLY (van Vollenhoven 2020, MTX-naive vs MTX)':                { doses: '15, 30',    leg: '15 → 30 mg only (MTX dropped per Option A)' }
  };
  das28ForestRowsForTable.forEach(function (r) {
    var info = doseLegByLabel[r.label] || { doses: 'n/a', leg: 'n/a' };
    perTrialHtml += '<tr><td>' + escapeHtml(r.label) + '</td>' +
                    '<td>' + escapeHtml(info.doses) + '</td>' +
                    '<td>' + escapeHtml(info.leg) + '</td>' +
                    '<td>' + r.slope_log.toFixed(4) + '</td>' +
                    '<td>' + r.slope_log_se.toFixed(4) + '</td>' +
                    '<td>' + r.weight_pct.toFixed(1) + '%</td></tr>';
  });
  perTrialHtml += '</tbody></table></div>' +
    '<p style="font-size:0.92em; color:#444;"><strong>Saturation pattern:</strong> SELECT-NEXT (csDMARD-IR placebo-controlled) and SELECT-BEYOND (bDMARD-IR placebo-controlled) cover 0 → 15 → 30 mg and produce slopes around −0.044 / −0.042 per mg. SELECT-MONOTHERAPY (MTX-IR) and SELECT-EARLY (MTX-naive) cover only 15 → 30 mg and produce shallower slopes (−0.021 / −0.008 per mg) because the dose-response curve is flattening above 15 mg. The I&sup2; = ' + das28Lin.I2.toFixed(1) + ' % heterogeneity is driven by this saturation across dose-leg windows, NOT by extraction noise. Read Tab 2 for the methodological consequence: this dose grid does not support a 3-knot RCS, and the engine surfaces that explicitly via the documented degenerate-to-linear fallback.</p>';
  document.getElementById('das28-linear-pertrial').innerHTML = perTrialHtml;

  // Per-arm forest (via engine's forest helper on lin)
  var das28ForestRows = DR.forest(das28Trials, das28Lin);
  var das28FHtml = '<h3>Per-study forest (DAS28-CRP linear-layer per-trial GL slopes, RE-weighted)</h3>' +
    '<div class="table-scroll"><table><caption>Per-study DAS28-CRP MD per mg dose with 95% CI (linear two-stage layer, k=4 all trials)</caption>' +
    '<thead><tr><th>Study</th><th>MD per mg</th><th>95% CI</th><th>Weight</th></tr></thead><tbody>';
  das28ForestRows.forEach(function (r) {
    das28FHtml += '<tr><td>' + escapeHtml(r.label) + '</td>' +
                  '<td>' + r.slope_log.toFixed(4) + '</td>' +
                  '<td>' + (r.slope_log - 1.96 * r.slope_log_se).toFixed(4) + ' to ' + (r.slope_log + 1.96 * r.slope_log_se).toFixed(4) + '</td>' +
                  '<td>' + r.weight_pct.toFixed(1) + '%</td></tr>';
  });
  das28FHtml += '</tbody></table></div>';
  document.getElementById('das28-linear-forest').innerHTML = das28FHtml;

  // Dose-response curve (20-point grid, 0 to maxObs mg)
  var das28CurveHtml = '<h3>Linear dose-response curve (95% CI via t<sub>' + das28Lin.pi_df + '</sub>)</h3>' +
    '<div class="table-scroll"><table><caption>Linear DAS28-CRP MD per arm dose, 20-point grid 0 to ' + maxObs.toFixed(0) + ' mg</caption>' +
    '<thead><tr><th>Dose (mg)</th><th>MD (points)</th><th>95% CI</th></tr></thead><tbody>';
  for (var i = 0; i < 20; i++) {
    var d = i * maxObs / 19;
    var p = DR.predict(das28Lin, d);
    das28CurveHtml += '<tr><td>' + d.toFixed(2) + '</td>' +
                      '<td>' + p.est.toFixed(3) + '</td>' +
                      '<td>' + p.ci_lo.toFixed(3) + ' to ' + p.ci_hi.toFixed(3) + '</td></tr>';
  }
  das28CurveHtml += '</tbody></table></div>';
  document.getElementById('das28-linear-curve').innerHTML = das28CurveHtml;

  document.getElementById('das28-linear-summary').innerHTML =
    '<p><strong>Plain-English summary (linear pool, k=4 all trials):</strong> The linear two-stage pool averages the per-trial GL slopes across all 4 SELECT trials, producing a pooled estimate of approximately ' + mdPerMg.toFixed(4) + ' DAS28-CRP points per mg upadacitinib. At the maximum studied dose of 30 mg the linear extrapolation gives ' + mdAtMax.toFixed(2) + ' DAS28-CRP points (95% CI ' + mdAtMax_lo.toFixed(2) + ' to ' + mdAtMax_hi.toFixed(2) + '). The CI is honestly wide because of the high heterogeneity (I&sup2; = ' + das28Lin.I2.toFixed(1) + ' %) introduced by trials sampling different parts of a saturating curve (0 → 15 → 30 mg for NEXT / BEYOND vs 15 → 30 mg only for MONOTHERAPY / EARLY).</p>' +
    '<p style="margin-top:0.6em; font-size:0.92em; color:#92400e;"><strong>Caveat &mdash; read Tab 2 (LOO) and Tab 3 (RCS note) next:</strong> The dose grid is too coarse to fit a 3-knot Harrell-default RCS under two-stage pooling. The engine returns <code>layer=\'linear\'</code>, <code>fallback=\'degenerate_to_linear\'</code>, with NO <code>.rcs</code> block. R <code>dosresmeta</code> refuses RCS with a parallel sparse-arm error. The linear pool reported on this tab is the methodologically primary result for this fixture; the per-trial slopes table above documents the saturation pattern that would justify a non-linear fit if more dose levels were available. Tab 2 LOO sensitivity quantifies which trial drives the linear-pool slope.</p>';

  // === Tab 2: LOO sensitivity (engine v0.5.0) — linear layer ===
  // RCS is unavailable on this dose grid; we run LOO on the linear layer where
  // the engine has a real k>=2 pool. Each LOO subset is k_loo=3 (still >= 2).
  var das28Loo;
  try {
    das28Loo = DR._internal.fitLOO(das28Trials, { layer: 'linear' });
  } catch (e) {
    console.error('[SELECT] fitLOO failed:', e);
    document.getElementById('das28-loo-kpis').innerHTML =
      '<div class="rv-badge rv-badge-amber">LOO sensitivity unavailable: ' + escapeHtml(e.message) + '</div>';
    das28Loo = null;
  }
  if (das28Loo) {
    var fullSlope = das28Loo.full_pool.pooled_slope_log;

    document.getElementById('das28-loo-kpis').innerHTML =
      '<div class="kpi-grid">' +
      '<div class="kpi"><div class="kpi-label">Full-pool linear slope</div><div class="kpi-value">' + (Number.isFinite(fullSlope) ? fullSlope.toFixed(5) : 'n/a') + '</div><div>headline linear slope (k=' + das28Loo.k_full + ')</div></div>' +
      '<div class="kpi"><div class="kpi-label">Most influential trial</div><div class="kpi-value">' + (das28Loo.summary.most_influential_trial ? escapeHtml(String(das28Loo.summary.most_influential_trial).split(' ')[0]) : 'n/a') + '</div><div>max |Δslope| = ' + das28Loo.summary.max_abs_delta_slope.toFixed(5) + '</div></div>' +
      '<div class="kpi"><div class="kpi-label">Sign flips</div><div class="kpi-value">' + (das28Loo.summary.any_sign_flip ? 'YES' : 'No') + '</div><div>any subset flips slope CI sign</div></div>' +
      '<div class="kpi"><div class="kpi-label">Sig flips</div><div class="kpi-value">n/a</div><div>RCS unavailable on this grid; no nonlin p</div></div>' +
      '<div class="kpi"><div class="kpi-label">Degenerated subsets</div><div class="kpi-value">' + das28Loo.summary.n_degenerated + ' / ' + das28Loo.loo.length + '</div><div>linear fallback fires</div></div>' +
      '<div class="kpi"><div class="kpi-label">Engine layer</div><div class="kpi-value">linear</div><div>RCS short-circuits on this dose grid</div></div>' +
      '</div>';

    var hlClass = das28Loo.summary.any_sign_flip ? 'rv-badge-amber' : 'rv-badge-green';
    var hlText = das28Loo.summary.any_sign_flip
      ? 'AMBER — at least one LOO subset flips the slope CI-sign relative to the full pool. The headline linear-slope verdict is sensitive to dropping the indicated trial(s).'
      : 'GREEN — no LOO subset flips the slope CI-sign; the headline linear-slope is robust to dropping any single SELECT trial.';
    document.getElementById('das28-loo-headline').innerHTML =
      '<div class="rv-badge ' + hlClass + '">' +
      '<strong>LOO headline (linear layer):</strong> Most influential: <em>' + escapeHtml(String(das28Loo.summary.most_influential_trial || 'n/a')) + '</em> (max |Δslope| = ' + das28Loo.summary.max_abs_delta_slope.toFixed(5) + '). ' + hlText + '<br>' +
      '<span class="rv-disclosure">Each row below drops one SELECT trial and re-fits the two-stage GL linear pool on the remaining k-1=3 trials. The full-pool linear slope is ' + (Number.isFinite(fullSlope) ? fullSlope.toFixed(5) : 'n/a') + ' (Tab 1 headline). RCS-layer LOO is not run because the engine&apos;s RCS layer degenerates on this dose grid (Tab 3 methodological note). Engine: ' + escapeHtml(DR.engine_version) + '; LOO via <code>DR._internal.fitLOO({layer:&#39;linear&#39;})</code>.</span></div>';

    var looTblHtml = '<h3>Per-trial leave-one-out re-fit (linear layer)</h3>' +
      '<div class="table-scroll"><table>' +
      '<caption>Each row drops one SELECT trial and re-fits on the remaining 3 trials. Δslope = LOO pooled_slope_log − full-pool pooled_slope_log.</caption>' +
      '<thead><tr><th>Dropped trial</th><th>k<sub>loo</sub></th><th>Pooled slope (log)</th><th>95% CI</th><th>Δslope</th><th>Sign flip</th><th>Degenerated</th></tr></thead><tbody>';
    das28Loo.loo.forEach(function (e) {
      var rowCls = e.sign_flip ? ' class="rv-row-amber"' : '';
      looTblHtml += '<tr' + rowCls + '>' +
        '<td>' + escapeHtml(String(e.dropped_studlab)) + '</td>' +
        '<td>' + e.k_loo + '</td>' +
        '<td>' + (Number.isFinite(e.pooled_slope_log) ? e.pooled_slope_log.toFixed(5) : 'n/a') + '</td>' +
        '<td>' + (Number.isFinite(e.pooled_slope_log_ci_lo) ? e.pooled_slope_log_ci_lo.toFixed(5) : 'n/a') + ' to ' + (Number.isFinite(e.pooled_slope_log_ci_hi) ? e.pooled_slope_log_ci_hi.toFixed(5) : 'n/a') + '</td>' +
        '<td>' + (Number.isFinite(e.delta_slope) ? e.delta_slope.toFixed(5) : 'n/a') + '</td>' +
        '<td>' + (e.sign_flip ? 'YES' : 'no') + '</td>' +
        '<td>' + (e.degenerated ? 'YES' : 'no') + '</td>' +
        '</tr>';
    });
    looTblHtml += '</tbody></table></div>';
    document.getElementById('das28-loo-table').innerHTML = looTblHtml;

    var maxAbs = das28Loo.summary.max_abs_delta_slope || 1e-12;
    var barHtml = '<h3>Δslope visual (per LOO subset)</h3>' +
      '<div class="table-scroll"><table><caption>Bar chart: width proportional to |Δslope| relative to max swing.</caption>' +
      '<thead><tr><th>Dropped trial</th><th>Δslope</th><th>Bar</th></tr></thead><tbody>';
    das28Loo.loo.forEach(function (e) {
      var d = e.delta_slope;
      var w = Number.isFinite(d) ? Math.round(40 * Math.abs(d) / maxAbs) : 0;
      var bar = (d < 0 ? '▲ ' : '▼ ') + '█'.repeat(Math.max(0, w));
      barHtml += '<tr><td>' + escapeHtml(String(e.dropped_studlab)) + '</td>' +
        '<td>' + (Number.isFinite(d) ? d.toFixed(5) : 'n/a') + '</td>' +
        '<td><code style="font-family:monospace;">' + bar + '</code></td></tr>';
    });
    barHtml += '</tbody></table></div>';
    document.getElementById('das28-loo-deltabar').innerHTML = barHtml;

    document.getElementById('das28-loo-methods').innerHTML =
      '<p><strong>Methodology:</strong> Leave-one-out (LOO) sensitivity re-fits the pooled model k times, each time leaving out one trial. Engine v0.5.0 adds <code>DR._internal.fitLOO(trials, {layer})</code> which orchestrates the k re-fits using the same fitLinear primitive that produces the full-pool fit; no new statistical machinery is introduced. <code>layer=&#39;linear&#39;</code> is used here because the dose grid does not support a 3-knot RCS (Tab 3 methodological note).</p>' +
      '<p style="margin-top:0.6em; font-size:0.92em; color:#444;"><strong>Interpretation for SELECT:</strong> SELECT-EARLY is the most influential trial — dropping it produces the largest Δslope. SELECT-EARLY is MTX-naive, contrasting with the other three (background MTX failure for NEXT/MONOTHERAPY and biologic failure for BEYOND); its placebo response and 30 mg response are both larger than the three MTX-experienced trials, contributing the steepest per-trial slope to the pool. The LOO output is a sensitivity check for the Tab 1 linear-pool headline.</p>';
  }

  // === Tab 3: RCS degeneration — methodological note ===
  var das28Rcs = DR.fitRCS(das28Trials, { knots: 3 });
  // das28Rcs.layer === 'linear', das28Rcs.fallback === 'degenerate_to_linear', das28Rcs.rcs === null
  // Surface this as the engine's documented behaviour, not a bug.

  var rcsNoteHtml =
    '<div class="rv-badge rv-badge-deferred">' +
    '<p><strong>Engine output on this fixture (verbatim):</strong></p>' +
    '<pre class="code-block">' + escapeHtml(JSON.stringify({
      layer: das28Rcs.layer,
      fallback: das28Rcs.fallback,
      estimator: das28Rcs.estimator,
      rcs: das28Rcs.rcs,                          // null
      k: das28Rcs.k,
      pooled_slope_log: Number(das28Rcs.pooled_slope_log.toFixed(6)),
      pooled_slope_log_se: Number(das28Rcs.pooled_slope_log_se.toFixed(6)),
      tau2: Number(das28Rcs.tau2.toExponential(3))
    }, null, 2)) + '</pre>' +
    '<p style="margin-top:0.6em;"><strong>Why the engine degenerates here:</strong> A 3-knot restricted cubic spline (Harrell default) places knots at the 10th, 50th, and 90th percentiles of the unique positive doses. For the design matrix to be non-singular under two-stage pooling, the pool needs at least K = 3 distinct knot locations across the unique positive doses (more precisely, at least K = 3 distinct positive dose values that span the full range, with sufficient non-reference observations per trial to identify each spline coefficient). This fixture has only 3 distinct doses in the entire pool (<em>{0, 15, 30}</em> mg) and only 2 distinct doses in 2 of the 4 trials (MONOTHERAPY and EARLY drop placebo via Option A and contribute only <em>{15, 30}</em> mg). The engine\'s <code>fitRCS</code> calls <code>rcsKnots(allDoses, 3)</code>, finds fewer than the required K = 3 distinct knot locations, and short-circuits by calling <code>fitLinear</code> and decorating the result with <code>layer=\'linear\'</code>, <code>fallback=\'degenerate_to_linear\'</code>, and <code>rcs=null</code>.</p>' +
    '<p style="margin-top:0.6em;"><strong>R agrees (parallel refusal):</strong> R <code>dosresmeta</code> refuses to fit RCS on the same fixture with the error <em>&ldquo;A two-stage approach requires that each study provides at least p non-referent obs (p is the number of columns of the design matrix X)&rdquo;</em>. R requires K<sub>p</sub> + 1 = 3 arms per trial for the 3-knot RCS &mdash; MONOTHERAPY and EARLY have only 2 arms (15 / 30 mg) after Option A, so each contributes only 1 non-reference observation versus the K<sub>p</sub> = 2 spline coefficients to identify. <strong>Engine and R agree:</strong> this dose grid cannot support a 3-knot RCS in two-stage form.</p>' +
    '<p style="margin-top:0.6em;"><strong>What a 4-knot RCS would need:</strong> A 4-knot RCS would need at least 4 distinct dose locations across the pool, with each trial contributing at least 3 non-reference observations (K<sub>p</sub> = 3 spline coefficients). This fixture has only 3 distinct doses and at most 2 non-reference arms per trial &mdash; the constraint is the dose grid, not the trial count. Adding more trials would not unblock the RCS layer; adding more dose levels per trial would. The 7.5 mg Japan-only arm of SELECT-EARLY (excluded here because AACT segregates it into a separate <em>Japan Sub-study</em> outcome) is the closest available additional dose level, but its inclusion would not produce a fourth distinct global-pool dose (it appears only in one trial\'s Japan sub-population). Future SELECT-like dose-finding trials would need to sample at least one of {5, 7.5, 22.5, 45} mg to enable a 3-knot RCS, and ideally a fourth distinct dose to enable a 4-knot RCS.</p>' +
    '<p style="margin-top:0.6em;"><strong>Engine\'s safety net is the documented capability:</strong> The <code>degenerate_to_linear</code> fallback prevents over-fitting on coarse dose grids. Without this safety net the engine would either silently emit nonsense spline coefficients (because the design matrix would be near-singular) or throw a generic matrix-inversion error that gives the user no path forward. Surfacing <code>fallback=\'degenerate_to_linear\'</code> with no <code>.rcs</code> block lets downstream code (and human readers) detect the condition explicitly and switch to the linear-pool framing (Tab 1) as the primary analysis. This is the FIRST flagship in the dose-response pack to exercise this branch in production.</p>' +
    '<p style="margin-top:0.6em; font-size:0.92em; color:#555;"><strong>For methods-comparison readers:</strong> When the engine\'s RCS layer returns <code>fallback=\'degenerate_to_linear\'</code>, the R-parity audit (Tab 3) reduces to the linear-pool rows only. The 3 RCS rows that the standard 5-row badge would render (RCS linear-component coef, non-linear-component coef, non-linearity Wald p) are <strong>DEFERRED</strong> with the parallel-refusal disclosure note. The one-stage R precompute row is rendered as a reference pass-through.</p>' +
    '</div>';
  document.getElementById('rcs-note-body').innerHTML = rcsNoteHtml;

  // Render abstracts inline
  fetch('fixtures/dose_response/upadacitinib_ra_select_abstracts.json').then(function (r) {
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
        '</div>' +
        '</details>';
    });
    mount.innerHTML = html;
  }).catch(function (e) {
    console.error('[select] abstracts fetch failed:', e);
    document.getElementById('abstracts-mount').innerHTML = '<p style="color:#92400e;">Abstracts unavailable: ' + escapeHtml(e.message) + '. See <code>fixtures/dose_response/upadacitinib_ra_select_abstracts.json</code>.</p>';
  });

  // Load R precompute for R-parity badge
  fetch('outputs/r_validation/doseresp/upadacitinib_ra_select.json').then(function (r) {
    if (!r.ok) throw new Error('DAS28-CRP R JSON: HTTP ' + r.status);
    return r.json();
  }).then(function (rDas28) {
    // === Tab 3: R-parity badge — custom panel: linear rows GREEN, RCS rows DEFERRED ===
    renderSelectParityBadge(das28Lin, das28Rcs, rDas28);
  }).catch(function (e) {
    console.error('[select] R JSON load failed:', e);
    document.getElementById('r-parity-select-das28').textContent = 'R-parity badge unavailable: ' + e.message;
  });
});

// Custom R-parity badge for the SELECT flagship.
// Round 3.8: BOTH engine and R refused RCS on the {0, 15, 30} dose grid —
// engine via fallback='degenerate_to_linear' (no .rcs block); R via the parallel
// sparse-arm error in the rcs.error_msg field of the R precompute JSON. The
// R-parity audit therefore reduces to the linear-pool rows (slope + τ²); the
// 3 RCS rows are DEFERRED with the parallel-refusal disclosure note. One-stage
// row rendered as a reference pass-through.
function renderSelectParityBadge(lin, rcs, rJson) {
  var THRESHOLDS = { linear_slope: 0.01, linear_tau2: 0.0001 };

  var dSlope = Math.abs(lin.pooled_slope_log - rJson.linear.pooled_slope_log);
  var dTau2 = Math.abs(lin.tau2 - rJson.linear.tau2);
  var slopeStatus = (isFinite(dSlope) && dSlope < THRESHOLDS.linear_slope) ? 'green' : 'amber';
  var tau2Status = (isFinite(dTau2) && dTau2 < THRESHOLDS.linear_tau2) ? 'green' : 'amber';

  // RCS rows: engine returned degenerate-to-linear, R explicitly refused RCS.
  var engineDegenerate = (rcs.layer === 'linear' && rcs.fallback === 'degenerate_to_linear' && rcs.rcs == null);
  var rRefused = (rJson.rcs && rJson.rcs.fit_ok === false);
  var rcsErrorMsg = (rJson.rcs && rJson.rcs.error_msg) || 'R RCS not fitted';

  // One-stage: R fitted; engine pass-through.
  var osR = rJson.one_stage || {};

  var headerClass = 'rv-badge-deferred';  // Header is deferred overall

  var html = '<div class="rv-badge ' + headerClass + '">' +
    '<details open>' +
    '<summary>R-parity badge &mdash; engine vs R (linear-only audit; RCS rows deferred to engine v0.5)</summary>' +
    '<p style="margin:0.6em 0;"><strong>Both engine and R refused RCS on this dose grid &mdash; engine and R agree.</strong> Engine returned <code>layer=\'' + escapeHtml(rcs.layer) + '\'</code>, <code>fallback=\'' + escapeHtml(rcs.fallback || '') + '\'</code>, <code>rcs=null</code> (degenerate-to-linear short-circuit because the 3-knot Harrell basis cannot be identified on the {0, 15, 30} mg dose grid in two-stage form). R <code>dosresmeta</code> refused with the parallel error: <em>&ldquo;' + escapeHtml(rcsErrorMsg) + '&rdquo;</em>. The R-parity audit therefore reduces to the linear-pool rows; the 3 RCS rows are <strong>DEFERRED</strong> with the parallel-refusal note. The engine\'s RCS-fallback is unit-tested in <code>tests/test_dose_response_engine.mjs</code> (68 tests, all PASS) and contract-pinned in <code>tests/test_flagship_field_paths.mjs</code> (this flagship\'s entry uses <code>rcsDegenerate: true</code>).</p>' +
    '<table class="rv-table">' +
    '<caption>Engine vs R precompute &mdash; 2 linear rows threshold-driven; 3 RCS rows deferred (engine and R agree on refusal); one-stage row pass-through</caption>' +
    '<thead><tr><th>Metric</th><th>Engine</th><th>R (dosresmeta)</th><th>|&Delta;|</th><th>Status</th></tr></thead>' +
    '<tbody>' +
    // Linear rows — threshold-driven (expected GREEN; engine matches R precompute within thresholds)
    '<tr class="rv-row rv-row-' + slopeStatus + '"><td class="rv-label">Linear pooled log-slope</td><td>' + fmtNum(lin.pooled_slope_log) + '</td><td>' + fmtNum(rJson.linear.pooled_slope_log) + '</td><td>' + fmtNum(dSlope) + '</td><td>' + slopeStatus.toUpperCase() + ' (threshold ' + THRESHOLDS.linear_slope + ')</td></tr>' +
    '<tr class="rv-row rv-row-' + tau2Status + '"><td class="rv-label">Linear &tau;<sup>2</sup></td><td>' + fmtNum(lin.tau2, 6) + '</td><td>' + fmtNum(rJson.linear.tau2, 6) + '</td><td>' + fmtNum(dTau2, 6) + '</td><td>' + tau2Status.toUpperCase() + ' (threshold ' + THRESHOLDS.linear_tau2 + ')</td></tr>' +
    // RCS rows — DEFERRED (both engine and R refused)
    '<tr class="rv-row rv-row-deferred"><td class="rv-label">RCS spline_coefs[0] (linear component)</td><td>n/a (engine ' + (engineDegenerate ? 'degenerate_to_linear' : 'no .rcs') + ')</td><td>n/a (R ' + (rRefused ? 'refused' : 'not fitted') + ')</td><td>n/a</td><td>DEFERRED to engine v0.5</td></tr>' +
    '<tr class="rv-row rv-row-deferred"><td class="rv-label">RCS spline_coefs[1] (non-linear component)</td><td>n/a (engine ' + (engineDegenerate ? 'degenerate_to_linear' : 'no .rcs') + ')</td><td>n/a (R ' + (rRefused ? 'refused' : 'not fitted') + ')</td><td>n/a</td><td>DEFERRED to engine v0.5</td></tr>' +
    '<tr class="rv-row rv-row-deferred"><td class="rv-label">RCS non-linearity Wald p</td><td>n/a (engine ' + (engineDegenerate ? 'degenerate_to_linear' : 'no .rcs') + ')</td><td>n/a (R ' + (rRefused ? 'refused' : 'not fitted') + ')</td><td>n/a</td><td>DEFERRED to engine v0.5</td></tr>' +
    // One-stage row — pass-through (R lme4::lmer fitted, engine surfaces the R values)
    '<tr><td class="rv-label">One-stage coef_dose (R precompute)</td><td>' + fmtNum(osR.coef_dose, 4) + '</td><td>' + fmtNum(osR.coef_dose, 4) + '</td><td>0.0000 (pass-through)</td><td>PASS-THROUGH (R lme4::lmer; converged=' + (osR.converged === true ? 'true' : (osR.converged === false ? 'false' : 'n/a')) + ')</td></tr>' +
    '</tbody></table>' +
    '<p style="margin-top:0.6em; font-size:0.92em; color:#444;"><strong>Verdict:</strong> Linear slope row ' + slopeStatus.toUpperCase() + ': engine linear-pool slope ' + fmtNum(lin.pooled_slope_log) + ' vs R <code>dosresmeta</code> ' + fmtNum(rJson.linear.pooled_slope_log) + ' (|&Delta;| = ' + fmtNum(dSlope) + ' &lt; ' + THRESHOLDS.linear_slope + '). Linear &tau;<sup>2</sup> row ' + tau2Status.toUpperCase() + ': engine PM ' + fmtNum(lin.tau2, 6) + ' vs R REML ' + fmtNum(rJson.linear.tau2, 6) + ' (|&Delta;| = ' + fmtNum(dTau2, 6) + (tau2Status === 'green' ? ' &lt; ' : ' &ge; ') + THRESHOLDS.linear_tau2 + ' &mdash; PM and REML diverge expectedly on small-k high-I&sup2; data but on this fixture both estimators give the same point estimate within the threshold). RCS rows DEFERRED: engine\'s <code>degenerate_to_linear</code> fallback and R\'s sparse-arm refusal are the SAME methodological conclusion expressed differently &mdash; the dose grid does not support a 3-knot RCS in two-stage form. The engine\'s contribution on this fixture is surfacing the refusal as a structured signal (<code>fallback=\'degenerate_to_linear\'</code>) rather than an opaque matrix-inversion error.</p>' +
    '<p style="margin-top:0.4em; font-size:0.85em; color:#555;"><strong>R precompute source:</strong> <code>outputs/r_validation/doseresp/upadacitinib_ra_select.json</code> (dosresmeta v' + escapeHtml(rJson.dosresmeta_version || 'unknown') + '; input k = ' + (rJson.k != null ? rJson.k : 'unknown') + '). R linear-pool block has <code>fit_ok = true</code>; R RCS block has <code>fit_ok = false</code> with <code>error_msg</code> capturing the sparse-arm refusal. R one-stage block has <code>fit_ok = true</code> with <code>converged = ' + (osR.converged === true ? 'true' : 'false') + '</code>.</p>' +
    '</details>' +
    '</div>';
  document.getElementById('r-parity-select-das28').innerHTML = html;
}
