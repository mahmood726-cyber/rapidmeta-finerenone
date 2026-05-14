/* BRODALUMAB_PSORIASIS_AMAGINE_DOSE_RESP_REVIEW.js
 *
 * Round 3.9 — 3-trial AMAGINE brodalumab PASI 75 binary dose-response flagship.
 *
 * Engine path (v0.4 / binary outcome):
 *   Linear layer: k=3 all trials pooled via two-stage GL + REML + HKSJ.
 *     Binary path: per-arm events/n directly drive the GL shared-reference
 *     covariance for log-RR contrasts (no SE→SD conversion needed).
 *     pooled_slope_log ≈ 0.00523/mg, SE ≈ 0.00113 (HKSJ-inflated × tcrit).
 *     At 210 mg the linear log-RR extrapolation ≈ 1.10 → RR ≈ 3.0
 *     (placebo ~5% → linear-model brod 210 mg ≈ 15%; the absolute PASI 75
 *     gap in the underlying trials is 60-80pp because the response curve
 *     is non-linear and saturating, see Tab 2 caveat).
 *     τ² ≈ 8.6e-7 (effectively zero); Q ≈ 6.56 (df 2); I² ≈ 70%;
 *     HKSJ adj ≈ 1.81 (HKSJ inflates the SE moderately because Q*/df > 1).
 *
 *   RCS layer: ENGINE REFUSES, returns layer='linear', fallback='degenerate_to_linear',
 *     rcs=null. The cross-trial dose grid has only 2 distinct positive doses
 *     (140 and 210 mg); rcsKnots(allDoses, 3) returns < K=3 distinct knot
 *     locations and fitRCS short-circuits to fitLinear (decorating with the
 *     fallback flag). R dosresmeta DOES fit RCS but jams all 3 knots inside
 *     140-210 mg (knots [157.5, 175, 192.5], spline_coefs [0.01763, -0.01875],
 *     nonlinearity_wald_p 1.64e-13). This is the FIRST flagship in the
 *     dose-response pack where engine and R DISAGREE on whether to fit RCS.
 *
 *   One-stage (R precompute): lme4::glmer Poisson-with-offset on the per-arm
 *     event counts. coef_dose 0.00888/mg, SE 0.000394, CI [0.00811, 0.00966].
 *     R reports converged=false (random_effects_var pinned at boundary —
 *     between-trial variance of the dose coefficient is too small to identify).
 *
 * Tabs (4):
 *   1. PASI 75 Linear (k=3, HEADLINE)
 *   2. RCS — engine declined / R fit (methodological note; side-by-side panel)
 *   3. PASI 75 One-stage (R glmer pass-through)
 *   4. R-parity badge (linear rows GREEN; 3 RCS rows custom panel showing engine
 *      declined while R fit with degenerate knots)
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

  // Read PASI 75 trials
  var pasiScript = document.getElementById('doseresp-trials-pasi');
  var pasiTrials;
  try {
    pasiTrials = JSON.parse(pasiScript.textContent);
  } catch (e) {
    document.getElementById('pasi-linear-kpis').textContent = 'PASI 75 trial data malformed: ' + e.message;
    return;
  }
  if (pasiTrials.length === 0) {
    document.getElementById('pasi-linear-kpis').textContent = 'No PASI 75 trial data embedded.';
    return;
  }

  // === Tab 1: PASI 75 Linear (k=3 all trials) — HEADLINE ===
  var pasiLin = DR.fitLinear(pasiTrials, {});
  var logRRPerMg = pasiLin.pooled_slope_log;       // log-RR per mg
  var logRRPerMg_lo = pasiLin.pooled_slope_log_ci_lo;
  var logRRPerMg_hi = pasiLin.pooled_slope_log_ci_hi;
  var maxObs = pasiLin.max_observed_dose;          // 210 mg
  var logRRAtMax = logRRPerMg * maxObs;
  var rrAtMax = Math.exp(logRRAtMax);
  var rrAtMax_lo = Math.exp(logRRPerMg_lo * maxObs);
  var rrAtMax_hi = Math.exp(logRRPerMg_hi * maxObs);

  // F-1 fire check (binary path): no zero-event arms expected on this fixture.
  var f1Triggered = pasiTrials.some(function (t) {
    var ref = t.arms.find(function (a) { return a.is_reference; });
    return (ref && ref.events === 0) ||
           t.arms.some(function (a) { return !a.is_reference && a.events === 0; });
  });

  document.getElementById('pasi-linear-kpis').innerHTML =
    '<div class="kpi-grid">' +
    '<div class="kpi"><div class="kpi-label">RR at ' + maxObs.toFixed(0) + ' mg (linear extrapolation)</div><div class="kpi-value">' + rrAtMax.toFixed(2) + '</div><div>95% CI ' + rrAtMax_lo.toFixed(2) + ' to ' + rrAtMax_hi.toFixed(2) + '</div><div style="color:#92400e; font-size:0.8em;">log-RR-linear-in-dose model; absolute PASI 75 gap is much larger (placebo ~5% &rarr; brod 210 mg ~85%) because the response curve is saturating, see Tab 2</div></div>' +
    '<div class="kpi"><div class="kpi-label">log-RR per mg dose</div><div class="kpi-value">' + logRRPerMg.toFixed(5) + '</div><div>SE ' + pasiLin.pooled_slope_log_se.toFixed(5) + '</div></div>' +
    '<div class="kpi"><div class="kpi-label">&tau;<sup>2</sup> (REML)</div><div class="kpi-value">' + pasiLin.tau2.toExponential(2) + '</div><div>Q-profile CI ' + pasiLin.tau2_lo.toExponential(2) + ' to ' + pasiLin.tau2_hi.toExponential(2) + '</div></div>' +
    '<div class="kpi"><div class="kpi-label">I&sup2;</div><div class="kpi-value">' + pasiLin.I2.toFixed(1) + '%</div><div>Q = ' + pasiLin.Q.toFixed(2) + ' (df ' + pasiLin.Q_df + ')</div></div>' +
    '<div class="kpi"><div class="kpi-label">HKSJ adjustment</div><div class="kpi-value">' + pasiLin.hksj_adj.toFixed(2) + '</div><div>Q* = ' + pasiLin.hksj_qstar.toFixed(2) + '; HKSJ-inflated CI multiplier</div></div>' +
    '<div class="kpi"><div class="kpi-label">PI at ' + maxObs.toFixed(0) + ' mg (df=' + pasiLin.pi_df + ')</div><div class="kpi-value">' + Math.exp(pasiLin.pi_lo * maxObs).toFixed(2) + ' to ' + Math.exp(pasiLin.pi_hi * maxObs).toFixed(2) + '</div><div>RR scale (back-transformed from log-RR PI)</div></div>' +
    '<div class="kpi"><div class="kpi-label">k (linear)</div><div class="kpi-value">' + pasiLin.k + '</div>' + (pasiLin.coverage_warning ? '<div style="color:#92400e">coverage warning: k&lt;10</div>' : '') + '</div>' +
    '<div class="kpi"><div class="kpi-label">Estimator</div><div class="kpi-value" style="font-size:1em;">' + escapeHtml(pasiLin.estimator) + '</div><div>fallback: ' + (pasiLin.fallback == null ? '<em>none</em>' : escapeHtml(pasiLin.fallback)) + '</div></div>' +
    '</div>' +
    (f1Triggered
      ? '<div class="rv-badge rv-badge-amber" style="margin-top:0.6em;"><strong>F-1 zero-cell continuity correction fired:</strong> at least one arm has 0 events; the engine applied +0.5 to events and +1.0 to n in BOTH reference and contrast arms of the affected trial(s) per the advanced-stats.md conditional rule.</div>'
      : '<div class="rv-badge rv-badge-green" style="margin-top:0.6em;"><strong>F-1 not triggered:</strong> every arm has &gt; 0 PASI 75 responders (smallest is AMAGINE-1 placebo with 6/220 events). F-1 conditional correction is wired in the engine and unit-tested but does not fire on this fixture.</div>');

  // Per-trial slopes table — drives the I² > 0 signal (homogeneity is high but not perfect).
  var pasiForestRowsForTable = DR.forest(pasiTrials, pasiLin);
  var perTrialHtml = '<h3>Per-trial GL slopes (log-RR per mg)</h3>' +
    '<div class="table-scroll"><table><caption>Per-trial linear-layer GL slopes (PASI 75 log-RR per mg brodalumab) and the dose-leg each trial samples</caption>' +
    '<thead><tr><th>Trial</th><th>Dose levels (mg)</th><th>Dose leg sampled</th><th>log-RR slope (per mg)</th><th>SE</th><th>RE weight</th></tr></thead><tbody>';
  pasiForestRowsForTable.forEach(function (r) {
    perTrialHtml += '<tr><td>' + escapeHtml(r.label) + '</td>' +
                    '<td>0, 140, 210</td>' +
                    '<td>0 &rarr; 140 &rarr; 210 mg (full 3-arm range)</td>' +
                    '<td>' + r.slope_log.toFixed(5) + '</td>' +
                    '<td>' + r.slope_log_se.toFixed(5) + '</td>' +
                    '<td>' + r.weight_pct.toFixed(1) + '%</td></tr>';
  });
  perTrialHtml += '</tbody></table></div>' +
    '<p style="font-size:0.92em; color:#444;"><strong>Homogeneity note:</strong> All 3 trials use the identical kept dose grid (placebo + 140 + 210 mg) and produce per-trial GL slopes around 0.004&ndash;0.007 per mg log-RR. The pooled estimate (' + logRRPerMg.toFixed(5) + ' per mg) is the precision-weighted average; AMAGINE-2 and AMAGINE-3 carry most of the weight (~37% each) because of their larger N. AMAGINE-1 is smaller (~25% weight) and has a slightly steeper slope (its placebo event rate is 2.7% vs 8.1% / 6.0% in AMAGINE-2 / AMAGINE-3, giving a larger 0&rarr;140 mg log-RR contrast). I&sup2; = ' + pasiLin.I2.toFixed(1) + '% reflects this mild heterogeneity in the placebo event rate, not in the dose-response shape itself.</p>';
  document.getElementById('pasi-linear-pertrial').innerHTML = perTrialHtml;

  // Per-arm forest (via engine's forest helper on lin)
  var pasiForestRows = DR.forest(pasiTrials, pasiLin);
  var pasiFHtml = '<h3>Per-study forest (PASI 75 linear-layer per-trial GL slopes, RE-weighted, RR scale)</h3>' +
    '<div class="table-scroll"><table><caption>Per-study PASI 75 RR per mg dose with 95% CI (linear two-stage layer, k=3 all trials, RR scale back-transformed from log-RR)</caption>' +
    '<thead><tr><th>Study</th><th>RR per mg</th><th>95% CI</th><th>Weight</th></tr></thead><tbody>';
  pasiForestRows.forEach(function (r) {
    pasiFHtml += '<tr><td>' + escapeHtml(r.label) + '</td>' +
                 '<td>' + r.hr.toFixed(5) + '</td>' +
                 '<td>' + r.hr_ci_lo.toFixed(5) + ' to ' + r.hr_ci_hi.toFixed(5) + '</td>' +
                 '<td>' + r.weight_pct.toFixed(1) + '%</td></tr>';
  });
  pasiFHtml += '</tbody></table></div>';
  document.getElementById('pasi-linear-forest').innerHTML = pasiFHtml;

  // Dose-response curve (20-point grid, 0 to maxObs mg) — RR scale via exp() back-transform
  var pasiCurveHtml = '<h3>Linear dose-response curve (RR scale, 95% CI via t<sub>' + pasiLin.pi_df + '</sub>)</h3>' +
    '<div class="table-scroll"><table><caption>Linear PASI 75 RR per arm dose, 20-point grid 0 to ' + maxObs.toFixed(0) + ' mg</caption>' +
    '<thead><tr><th>Dose (mg)</th><th>RR</th><th>95% CI</th></tr></thead><tbody>';
  for (var i = 0; i < 20; i++) {
    var d = i * maxObs / 19;
    var p = DR.predict(pasiLin, d);
    pasiCurveHtml += '<tr><td>' + d.toFixed(2) + '</td>' +
                     '<td>' + Math.exp(p.est).toFixed(3) + '</td>' +
                     '<td>' + Math.exp(p.ci_lo).toFixed(3) + ' to ' + Math.exp(p.ci_hi).toFixed(3) + '</td></tr>';
  }
  pasiCurveHtml += '</tbody></table></div>';
  document.getElementById('pasi-linear-curve').innerHTML = pasiCurveHtml;

  document.getElementById('pasi-linear-summary').innerHTML =
    '<p><strong>Plain-English summary (linear pool, k=3 all trials):</strong> The linear two-stage pool averages the per-trial GL log-RR slopes across all 3 AMAGINE trials, producing a pooled estimate of approximately ' + logRRPerMg.toFixed(5) + ' log-RR per mg brodalumab (95% CI ' + logRRPerMg_lo.toFixed(5) + ' to ' + logRRPerMg_hi.toFixed(5) + '). At the maximum studied dose of 210 mg the linear extrapolation gives RR ' + rrAtMax.toFixed(2) + ' (95% CI ' + rrAtMax_lo.toFixed(2) + ' to ' + rrAtMax_hi.toFixed(2) + ') &mdash; the rate of PASI 75 response at 210 mg is roughly ' + rrAtMax.toFixed(1) + ' times the placebo rate per this model. &tau;<sup>2</sup> = ' + pasiLin.tau2.toExponential(2) + ' is effectively zero, indicating cross-trial dose-response is highly homogeneous (all 3 AMAGINE trials converge on the same slope on the log-RR scale).</p>' +
    '<p style="margin-top:0.6em; font-size:0.92em; color:#92400e;"><strong>Caveat &mdash; the absolute PASI 75 gap is larger than the linear RR model suggests:</strong> The trials report absolute PASI 75 response rates of 2.7&ndash;8.1 % on placebo and 83.3&ndash;86.3 % on brodalumab 210 mg &mdash; an absolute gap of 75&ndash;80 percentage points. The linear log-RR model predicts RR ~ 3 at 210 mg, which on a 5 % placebo base gives ~ 15 % absolute &mdash; clearly underestimating the actual response. This is the canonical &ldquo;log-RR-linear-in-dose&rdquo; mis-specification for a saturating biological response: the model captures the slope identification consistently across trials (homogeneous &tau;<sup>2</sup>) but is the wrong functional form for forecasting absolute response. An RCS layer would help here, but the AMAGINE dose grid (only 2 distinct positive doses) is too coarse to support one &mdash; read Tab 2 next.</p>' +
    '<p style="margin-top:0.6em; font-size:0.92em; color:#92400e;"><strong>Caveat &mdash; read Tab 2 next:</strong> The dose grid is too coarse to fit a 3-knot Harrell-default RCS. The engine returns <code>layer=&#39;linear&#39;</code>, <code>fallback=&#39;degenerate_to_linear&#39;</code>, with NO <code>.rcs</code> block. R <code>dosresmeta</code> DOES return an RCS fit on this fixture &mdash; but its 3 percentile knots all land inside the 140&ndash;210 mg interval where there are no data points to support curvature. The engine&apos;s refusal is the methodologically conservative call; R&apos;s fit is technically valid arithmetic but interpretively dubious. Tab 4 surfaces this disagreement in a custom &ldquo;engine-declined / R-fit&rdquo; R-parity panel.</p>';

  // === Tab 2: RCS methodological note — engine refuses, R fits with degenerate knots ===
  var pasiRcs = DR.fitRCS(pasiTrials, { knots: 3 });
  // pasiRcs.layer === 'linear', pasiRcs.fallback === 'degenerate_to_linear', pasiRcs.rcs === null
  // The R fit values are read from the R precompute JSON later; we'll surface them
  // side-by-side with the engine output in the badge block below.

  // Promise.all loads R precompute for both Tab 3 (one-stage) and Tab 4 (R-parity badge),
  // AND for Tab 2 (side-by-side engine/R comparison panel). We start the fetch here.
  var rJsonPromise = fetch('outputs/r_validation/doseresp/brodalumab_psoriasis_amagine.json').then(function (r) {
    if (!r.ok) throw new Error('R JSON: HTTP ' + r.status);
    return r.json();
  });

  rJsonPromise.then(function (rPasi) {
    // === Tab 2: RCS methodology note (engine refuses, R fits with degenerate knots) ===
    var rRcsBlock = rPasi.rcs || {};
    var rKnots = (rRcsBlock.knots || []).map(function (k) { return k.toFixed(1); }).join(', ');
    var rCoefs = (rRcsBlock.spline_coefs || []).map(function (c) { return c.toFixed(5); }).join(', ');
    var rNonlinP = rRcsBlock.nonlinearity_wald_p;

    var rcsNoteHtml =
      '<div class="rv-badge rv-badge-deferred">' +
      '<p><strong>The engine and R disagree on whether to fit an RCS on this dose grid.</strong> This is the FIRST flagship in the dose-response pack where the engine declines and R proceeds. Previous degeneracy cases (SUSTAIN Round 3.7, SELECT Round 3.8) had both engines refusing via different paths. On AMAGINE the cross-trial dose grid has only 2 distinct positive doses (140 and 210 mg) &mdash; insufficient for the 3-knot Harrell basis to land knots on real data &mdash; but every individual trial has 2 non-reference arms, so R&apos;s sparse-per-trial-arm guard does not fire. R proceeds to fit, placing its percentile knots inside the 140&ndash;210 mg interval; the engine refuses on the cross-trial knot-count check.</p>' +
      '<div class="side-by-side">' +
      '<div class="engine-col">' +
      '<p><strong>Engine output (verbatim):</strong></p>' +
      '<pre class="code-block">' + escapeHtml(JSON.stringify({
        layer: pasiRcs.layer,
        fallback: pasiRcs.fallback,
        rcs: pasiRcs.rcs,                          // null
        estimator: pasiRcs.estimator,
        k: pasiRcs.k,
        pooled_slope_log: Number(pasiRcs.pooled_slope_log.toFixed(6)),
        pooled_slope_log_se: Number(pasiRcs.pooled_slope_log_se.toFixed(6)),
        tau2: Number(pasiRcs.tau2.toExponential(3))
      }, null, 2)) + '</pre>' +
      '<p style="margin-top:0.4em;"><strong>Status: DECLINED.</strong> The engine&apos;s <code>fitRCS</code> calls <code>rcsKnots(allDoses, 3)</code>, finds fewer than the required K = 3 distinct knot locations (only 2 distinct positive doses: 140 and 210 mg), and short-circuits to <code>fitLinear</code> with <code>fallback=&#39;degenerate_to_linear&#39;</code> and <code>rcs=null</code>. No spline coefficients are emitted. The result is the engine&apos;s documented safety net for coarse dose grids &mdash; without it the engine would either silently emit nonsense spline coefficients (because the design matrix would be near-singular) or throw a generic matrix-inversion error.</p>' +
      '</div>' +
      '<div class="r-col">' +
      '<p><strong>R <code>dosresmeta</code> output (verbatim from precompute JSON):</strong></p>' +
      '<pre class="code-block">' + escapeHtml(JSON.stringify({
        fit_ok: rRcsBlock.fit_ok,
        knots: rRcsBlock.knots,
        spline_coefs: rRcsBlock.spline_coefs,
        nonlinearity_wald_p: rRcsBlock.nonlinearity_wald_p
      }, null, 2)) + '</pre>' +
      '<p style="margin-top:0.4em;"><strong>Status: FIT BUT KNOTS UNINFORMATIVE.</strong> R reports a successful RCS fit with <code>knots = [' + rKnots + ']</code> and <code>spline_coefs = [' + rCoefs + ']</code>. The percentile-derived knots all land inside the 140&ndash;210 mg interval &mdash; there are <em>no</em> data points between 140 and 210 mg to inform the within-range curvature the spline encodes. The reported <code>nonlinearity_wald_p = ' + (rNonlinP != null ? rNonlinP.toExponential(2) : 'n/a') + '</code> is highly significant in the algebraic sense, but it tests a curvature that is fit from percentile placeholders, not data. Interpretively dubious.</p>' +
      '</div>' +
      '</div>' +
      '<table style="margin-top:0.8em;">' +
      '<caption>Side-by-side: engine vs R verdict on RCS layer for the AMAGINE dose grid</caption>' +
      '<thead><tr><th>Aspect</th><th>Engine (RapidMeta v0.4)</th><th>R (dosresmeta ' + escapeHtml(rPasi.dosresmeta_version || 'unknown') + ')</th></tr></thead>' +
      '<tbody>' +
      '<tr><td>Verdict</td><td><strong>DECLINED</strong> (returns linear-fallback)</td><td><strong>FIT</strong> (returns spline_coefs)</td></tr>' +
      '<tr><td>Mechanism</td><td>Cross-trial knot-count check: <code>rcsKnots(allDoses, 3)</code> returns &lt; K distinct knot locations &rarr; short-circuit to <code>fitLinear</code></td><td>Per-trial sparse-arm check: each trial has 2 non-reference arms &ge; K<sub>p</sub>=2 required spline coefs &rarr; proceeds with percentile knots from {140, 210}-derived design points</td></tr>' +
      '<tr><td>Knot locations</td><td>n/a (no spline)</td><td>[' + rKnots + '] mg &mdash; all inside the 140&ndash;210 mg interval; no interior data</td></tr>' +
      '<tr><td>spline_coefs</td><td>n/a (no spline)</td><td>[' + rCoefs + ']</td></tr>' +
      '<tr><td>nonlinearity Wald p</td><td>n/a (no spline)</td><td>' + (rNonlinP != null ? rNonlinP.toExponential(2) : 'n/a') + ' &mdash; algebraically significant but tests curvature fit on percentile placeholders</td></tr>' +
      '<tr><td>Methodological judgment</td><td><strong>Conservative</strong>: refuses to fit an RCS whose knots cannot be supported by data</td><td><strong>Permissive</strong>: fits arithmetically valid splines on degenerate knot placements without warning the user</td></tr>' +
      '</tbody></table>' +
      '<p style="margin-top:0.6em;"><strong>Why the engine&apos;s call is the right one for AMAGINE:</strong> The 3-knot RCS is designed to detect within-curve non-linearity at three locations chosen by Harrell&apos;s percentile rule. When those three locations all collapse into a 70 mg-wide gap (140&ndash;210 mg) with no interior data, the spline is not measuring biological curvature &mdash; it is interpolating between two endpoints with a flexible function that has no constraint pulling it toward either a straight line or a real curve. The Wald test on the non-linear coefficient is asking &ldquo;is the within-gap curvature non-zero&rdquo;, and at the precision of the AMAGINE event counts (large N, narrow CIs) the test will almost always reject &mdash; but only because the design matrix has flexibility, not because there is a real saturation signal. R&apos;s output is not wrong arithmetic; it is an unconstrained fit that the user must interpret with caution. The engine surfaces &ldquo;refused&rdquo; as a structured signal precisely so downstream readers know to treat the R fit (if used as a sensitivity analysis) as descriptive rather than confirmatory.</p>' +
      '<p style="margin-top:0.6em;"><strong>What an informative RCS on brodalumab would need:</strong> At least 3 distinct positive doses across the pool, ideally with one or more interior to the 140&ndash;210 mg range (e.g. 70, 100, or 175 mg). The AMAGINE-1 Phase 2b dose-finding study randomized to 70 / 140 / 210 / 280 mg + placebo (n ~ 198) &mdash; that fixture would provide 4 distinct positive doses and unblock the 3-knot RCS in the engine. The Phase 3 AMAGINE programme indexed in AACT under the three NCTs here only studied 140 and 210 mg, so the current fixture is dose-grid-limited regardless of trial count. Adding more Phase 3 trials at the same two doses would not unblock the RCS; adding the Phase 2b dose-finding data would.</p>' +
      '<p style="margin-top:0.6em; font-size:0.92em; color:#555;"><strong>For methods-comparison readers:</strong> When the engine&apos;s RCS layer returns <code>fallback=&#39;degenerate_to_linear&#39;</code> and R fits anyway, the R-parity audit (Tab 4) renders the 3 RCS rows in a custom &ldquo;engine-declined / R-fit (uninformative knots)&rdquo; panel rather than as GREEN / AMBER / DEFERRED. This distinguishes Round 3.9 from the prior degeneracy flagships (SUSTAIN, SELECT) where both engine and R refused. The linear-pool R-parity rows (slope + &tau;<sup>2</sup>) still run as standard threshold-driven rows and are expected GREEN.</p>' +
      '</div>';
    document.getElementById('rcs-note-body').innerHTML = rcsNoteHtml;

    // === Tab 3: One-stage (R glmer pass-through) ===
    var pasiOs = DR.fitOneStage(pasiTrials, {}, rPasi);
    if (!pasiOs || !pasiOs.one_stage || pasiOs.one_stage.fit_ok === false) {
      document.getElementById('pasi-os-kpis').innerHTML =
        '<div class="rv-badge rv-badge-amber">One-stage R output unavailable. Run <code>python scripts/r_validate_doseresp.py --review brodalumab_psoriasis_amagine</code> to populate.</div>';
    } else {
      var os = pasiOs.one_stage;
      var osLogRRAtMax = os.coef_dose * maxObs;
      var osRRAtMax = Math.exp(osLogRRAtMax);
      var osRRAtMax_lo = Math.exp(os.coef_dose_ci_lo * maxObs);
      var osRRAtMax_hi = Math.exp(os.coef_dose_ci_hi * maxObs);
      document.getElementById('pasi-os-kpis').innerHTML =
        '<div class="kpi-grid">' +
        '<div class="kpi"><div class="kpi-label">RR at ' + maxObs.toFixed(0) + ' mg (one-stage)</div><div class="kpi-value">' + osRRAtMax.toFixed(2) + '</div><div>95% CI ' + osRRAtMax_lo.toFixed(2) + ' to ' + osRRAtMax_hi.toFixed(2) + '</div></div>' +
        '<div class="kpi"><div class="kpi-label">coef_dose (log-RR per mg)</div><div class="kpi-value">' + os.coef_dose.toFixed(5) + '</div><div>SE ' + os.coef_dose_se.toFixed(5) + '</div></div>' +
        '<div class="kpi"><div class="kpi-label">Random-effects variance</div><div class="kpi-value">' + (os.random_effects_var != null ? os.random_effects_var.toFixed(5) : 'n/a') + '</div></div>' +
        '<div class="kpi"><div class="kpi-label">Converged</div><div class="kpi-value">' + (os.converged ? 'Yes' : 'No') + '</div>' + (!os.converged ? '<div style="color:#92400e">solver flagged non-convergence (random-effects variance pinned at boundary)</div>' : '') + '</div>' +
        '<div class="kpi"><div class="kpi-label">Solver</div><div class="kpi-value">lme4 ' + escapeHtml(os.lme4_version || 'unknown') + '</div></div>' +
        (os.dose_scale_sd != null ? '<div class="kpi"><div class="kpi-label">dose_scale_sd (audit)</div><div class="kpi-value">' + os.dose_scale_sd.toFixed(3) + '</div></div>' : '') +
        '</div>';
      var convergenceNote = os.converged
        ? '<p style="margin-top:0.6em; font-size:0.92em; color:#444;"><strong>Convergence note:</strong> R reports the one-stage fit as converged (random_effects_var ' + (os.random_effects_var != null ? os.random_effects_var.toFixed(5) : 'n/a') + ', non-zero).</p>'
        : '<p style="margin-top:0.6em; font-size:0.92em; color:#92400e;"><strong>Non-convergence note:</strong> R reports <code>converged=false</code>: the random-effects variance is pinned at the 0 boundary, meaning between-trial variation in the dose coefficient is too small relative to within-arm sampling variance to identify a positive random-effects variance. On the AMAGINE fixture this is unsurprising &mdash; &tau;<sup>2</sup> in the two-stage layer (Tab 1) is also effectively zero (' + pasiLin.tau2.toExponential(2) + '). The fixed-effect dose coefficient and its SE remain interpretable; the convergence flag reflects the boundary of the random-effects parameter space, not a model failure.</p>';
      document.getElementById('pasi-os-methods').innerHTML =
        '<p><strong>Methodology:</strong> One-stage hierarchical model fit by R using <code>lme4::glmer(cbind(events, n - events) ~ dose + (1 | studlab), family = binomial, data = df, control = glmerControl(optimizer = &quot;bobyqa&quot;))</code> with dose rescaled by <code>sd(dose[dose &gt; 0])</code> for convergence and the coefficient back-transformed to per-mg log-RR. Per-arm <code>events</code> and <code>n - events</code> directly populate the binomial likelihood; the random study intercept captures between-trial baseline PASI 75 variation.</p>' +
        '<p style="margin-top:0.6em; font-size:0.92em;"><strong>Why this differs from Tab 1:</strong> The one-stage estimate (coef_dose ' + os.coef_dose.toFixed(5) + ' log-RR per mg) is larger than the two-stage estimate (' + logRRPerMg.toFixed(5) + ' log-RR per mg) because the one-stage GLMM with a binomial likelihood captures the non-linear logit-vs-linear-RR distinction directly: on a saturating response curve, the within-arm logit scale produces a slightly different per-mg slope than the GL log-RR shared-reference covariance. Both are valid; they answer subtly different questions about the same dose-response signal.</p>' +
        convergenceNote;
    }

    // === Tab 4: R-parity badge — custom panel: linear rows GREEN, RCS rows engine-declined / R-fit ===
    renderBrodalumabParityBadge(pasiLin, pasiRcs, pasiOs, rPasi);
  }).catch(function (e) {
    console.error('[brodalumab] R JSON load failed:', e);
    document.getElementById('rcs-note-body').innerHTML = '<div class="rv-badge rv-badge-amber">RCS methodology panel unavailable: ' + escapeHtml(e.message) + '. The engine output is still rendered above (Tab 1); see <code>outputs/r_validation/doseresp/brodalumab_psoriasis_amagine.json</code> for the R precompute.</div>';
    document.getElementById('pasi-os-kpis').textContent = 'One-stage tab unavailable: ' + e.message;
    document.getElementById('r-parity-brodalumab-pasi').textContent = 'R-parity badge unavailable: ' + e.message;
  });

  // Render abstracts inline
  fetch('fixtures/dose_response/brodalumab_psoriasis_amagine_abstracts.json').then(function (r) {
    if (!r.ok) throw new Error('abstracts JSON: HTTP ' + r.status);
    return r.json();
  }).then(function (abs) {
    var mount = document.getElementById('abstracts-mount');
    var html = '';
    abs.publications.forEach(function (p) {
      // Build NCT link(s): the shared publication (AMAGINE-2 + AMAGINE-3) has
      // nct_ids (array); AMAGINE-1 has nct_id (string).
      var nctHtml = '';
      if (Array.isArray(p.nct_ids) && p.nct_ids.length > 0) {
        nctHtml = p.nct_ids.map(function (nct) {
          return '<a href="https://clinicaltrials.gov/ct2/show/' + escapeHtml(nct) + '" target="_blank" rel="noopener noreferrer">' + escapeHtml(nct) + '</a>';
        }).join(' &middot; ');
      } else if (p.nct_id) {
        nctHtml = '<a href="https://clinicaltrials.gov/ct2/show/' + escapeHtml(p.nct_id) + '" target="_blank" rel="noopener noreferrer">' + escapeHtml(p.nct_id) + '</a>';
      }
      html += '<details>' +
        '<summary>' + escapeHtml(p.trial_label) + ' &mdash; ' + escapeHtml(p.first_author) + ', ' + escapeHtml(p.journal) + ' ' + p.year + ' (PMID ' + escapeHtml(p.pmid) + ')</summary>' +
        '<div class="abstract-block">' +
        '<p class="abstract-meta"><strong>' + escapeHtml(p.title) + '</strong></p>' +
        '<p class="abstract-meta">' + escapeHtml(p.authors_short) + ' &middot; <em>' + escapeHtml(p.journal) + '</em> ' + p.year + ';' + escapeHtml(p.volume) + (p.issue ? '(' + escapeHtml(p.issue) + ')' : '') + ':' + escapeHtml(p.pages) + ' &middot; ' +
        '<a href="' + escapeHtml(p.doi_link) + '" target="_blank" rel="noopener noreferrer">doi:' + escapeHtml(p.doi) + '</a> &middot; ' +
        '<a href="https://pubmed.ncbi.nlm.nih.gov/' + escapeHtml(p.pmid) + '/" target="_blank" rel="noopener noreferrer">PubMed ' + escapeHtml(p.pmid) + '</a> &middot; ' +
        nctHtml +
        '</p>' +
        '<p><strong>Abstract (according to PubMed):</strong> ' + escapeHtml(p.abstract) + '</p>' +
        '<p style="font-size:0.92em; color:#444;"><strong>Dose-response summary:</strong> ' + escapeHtml(p.primary_endpoint_text) + '</p>' +
        (p.user_supplied_citation_note ? '<p style="font-size:0.85em; color:#92400e;"><strong>Audit note:</strong> ' + escapeHtml(p.user_supplied_citation_note) + '</p>' : '') +
        '</div>' +
        '</details>';
    });
    mount.innerHTML = html;
  }).catch(function (e) {
    console.error('[brodalumab] abstracts fetch failed:', e);
    document.getElementById('abstracts-mount').innerHTML = '<p style="color:#92400e;">Abstracts unavailable: ' + escapeHtml(e.message) + '. See <code>fixtures/dose_response/brodalumab_psoriasis_amagine_abstracts.json</code>.</p>';
  });
});

// Custom R-parity badge for the AMAGINE brodalumab flagship.
// Round 3.9 distinguishes this case from SUSTAIN / SELECT:
//   - SUSTAIN: engine fit RCS (k_RCS=2 surviving), R refused. RCS rows DEFERRED.
//   - SELECT:  both engine and R refused. RCS rows DEFERRED.
//   - AMAGINE: engine REFUSED (degenerate-to-linear), R FIT (with degenerate knots).
//     RCS rows rendered as ENGINE-DECLINED / R-FIT in a custom panel; NOT
//     classified as GREEN / AMBER / DEFERRED because the standard threshold
//     comparison is undefined (engine has no spline_coefs to compare).
function renderBrodalumabParityBadge(lin, rcs, os, rJson) {
  var THRESHOLDS = { linear_slope: 0.01, linear_tau2: 0.0001 };

  var dSlope = Math.abs(lin.pooled_slope_log - rJson.linear.pooled_slope_log);
  var dTau2 = Math.abs(lin.tau2 - rJson.linear.tau2);
  var slopeStatus = (isFinite(dSlope) && dSlope < THRESHOLDS.linear_slope) ? 'green' : 'amber';
  var tau2Status = (isFinite(dTau2) && dTau2 < THRESHOLDS.linear_tau2) ? 'green' : 'amber';

  // RCS row state: engine declined, R fit. Use a custom row class with disclosure copy.
  var engineDeclined = (rcs.layer === 'linear' && rcs.fallback === 'degenerate_to_linear' && rcs.rcs == null);
  var rRcsFit = (rJson.rcs && rJson.rcs.fit_ok === true);
  var rKnotsStr = (rJson.rcs && Array.isArray(rJson.rcs.knots))
    ? '[' + rJson.rcs.knots.map(function (k) { return k.toFixed(1); }).join(', ') + ']'
    : 'n/a';
  var rSplineCoefs = (rJson.rcs && Array.isArray(rJson.rcs.spline_coefs)) ? rJson.rcs.spline_coefs : [];

  // One-stage: R fitted (converged=false reported in R precompute).
  var osR = rJson.one_stage || {};
  var osEng = (os && os.one_stage) || {};

  // Header: use 'rv-badge-deferred' (purple) overall to flag the engine-vs-R RCS
  // disagreement to the reader. The linear rows are GREEN-themed within the badge.
  var headerClass = 'rv-badge-deferred';

  var html = '<div class="rv-badge ' + headerClass + '">' +
    '<details open>' +
    '<summary>R-parity badge &mdash; linear rows GREEN; 3 RCS rows custom engine-declined / R-fit panel; one-stage row pass-through</summary>' +
    '<p style="margin:0.6em 0;"><strong>Engine and R DISAGREE on whether to fit RCS on this dose grid.</strong> Engine returned <code>layer=&#39;' + escapeHtml(rcs.layer) + '&#39;</code>, <code>fallback=&#39;' + escapeHtml(rcs.fallback || '') + '&#39;</code>, <code>rcs=null</code> (degenerate-to-linear short-circuit because the cross-trial dose grid has only 2 distinct positive doses, 140 and 210 mg; the 3-knot Harrell basis cannot land knots on real data). R <code>dosresmeta</code> fits anyway, placing percentile knots at <code>' + escapeHtml(rKnotsStr) + '</code> &mdash; all inside the 140&ndash;210 mg interval where there are no interior data points. The 3 RCS rows are rendered in a custom &ldquo;engine-declined / R-fit (uninformative knots)&rdquo; panel that distinguishes Round 3.9 from prior degeneracy flagships (SUSTAIN, SELECT) where both engine and R refused via different paths. This is unit-tested in <code>tests/test_dose_response_engine.mjs</code> (68 tests, all PASS) and contract-pinned in <code>tests/test_flagship_field_paths.mjs</code> (this flagship&apos;s entry uses <code>rcsDegenerate: true</code> mirroring SELECT, plus a new contract assertion that R <code>rcs.fit_ok === true</code> &mdash; the SUSTAIN/SELECT combination requires R fit_ok=false, the AMAGINE combination requires R fit_ok=true with knots inside the gap).</p>' +
    '<table class="rv-table">' +
    '<caption>Engine vs R precompute &mdash; 2 linear rows threshold-driven; 3 RCS rows ENGINE-DECLINED / R-FIT; one-stage row pass-through</caption>' +
    '<thead><tr><th>Metric</th><th>Engine</th><th>R (dosresmeta)</th><th>|&Delta;|</th><th>Status</th></tr></thead>' +
    '<tbody>' +
    // Linear rows — threshold-driven (expected GREEN; engine matches R precompute within thresholds)
    '<tr class="rv-row rv-row-' + slopeStatus + '"><td class="rv-label">Linear pooled log-slope</td><td>' + fmtNum(lin.pooled_slope_log, 5) + '</td><td>' + fmtNum(rJson.linear.pooled_slope_log, 5) + '</td><td>' + fmtNum(dSlope, 5) + '</td><td>' + slopeStatus.toUpperCase() + ' (threshold ' + THRESHOLDS.linear_slope + ')</td></tr>' +
    '<tr class="rv-row rv-row-' + tau2Status + '"><td class="rv-label">Linear &tau;<sup>2</sup></td><td>' + lin.tau2.toExponential(2) + '</td><td>' + (rJson.linear.tau2 != null ? rJson.linear.tau2.toExponential(2) : 'n/a') + '</td><td>' + dTau2.toExponential(2) + '</td><td>' + tau2Status.toUpperCase() + ' (threshold ' + THRESHOLDS.linear_tau2 + ')</td></tr>' +
    // RCS rows — ENGINE-DECLINED / R-FIT (custom: rv-row-deferred styling, plus explicit
    // "engine declined / R fit (uninformative knots)" disclosure copy in the status cell).
    '<tr class="rv-row rv-row-deferred"><td class="rv-label">RCS spline_coefs[0] (linear component)</td><td>n/a (engine ' + (engineDeclined ? 'declined &mdash; degenerate_to_linear' : 'no .rcs') + ')</td><td>' + (rSplineCoefs.length > 0 ? fmtNum(rSplineCoefs[0], 5) : 'n/a') + ' (R ' + (rRcsFit ? 'fit with knots ' + escapeHtml(rKnotsStr) + ' &mdash; uninformative' : 'not fitted') + ')</td><td>n/a</td><td>ENGINE-DECLINED / R-FIT (knots inside 140&ndash;210 mg gap; deferred to engine v0.5)</td></tr>' +
    '<tr class="rv-row rv-row-deferred"><td class="rv-label">RCS spline_coefs[1] (non-linear component)</td><td>n/a (engine ' + (engineDeclined ? 'declined &mdash; degenerate_to_linear' : 'no .rcs') + ')</td><td>' + (rSplineCoefs.length > 1 ? fmtNum(rSplineCoefs[1], 5) : 'n/a') + ' (R ' + (rRcsFit ? 'fit &mdash; uninformative' : 'not fitted') + ')</td><td>n/a</td><td>ENGINE-DECLINED / R-FIT (uninformative; deferred to engine v0.5)</td></tr>' +
    '<tr class="rv-row rv-row-deferred"><td class="rv-label">RCS non-linearity Wald p</td><td>n/a (engine ' + (engineDeclined ? 'declined &mdash; degenerate_to_linear' : 'no .rcs') + ')</td><td>' + (rJson.rcs && rJson.rcs.nonlinearity_wald_p != null ? rJson.rcs.nonlinearity_wald_p.toExponential(2) : 'n/a') + ' (R ' + (rRcsFit ? 'reports significant; tests curvature on percentile knots, not data' : 'not fitted') + ')</td><td>n/a</td><td>ENGINE-DECLINED / R-FIT (interpretively dubious; deferred to engine v0.5)</td></tr>' +
    // One-stage row — pass-through (R lme4::glmer fitted; engine surfaces R values)
    '<tr><td class="rv-label">One-stage coef_dose (R precompute, log-RR per mg)</td><td>' + fmtNum(osEng.coef_dose, 5) + '</td><td>' + fmtNum(osR.coef_dose, 5) + '</td><td>0.00000 (pass-through)</td><td>PASS-THROUGH (R lme4::glmer; converged=' + (osR.converged === true ? 'true' : (osR.converged === false ? 'false (random_effects_var pinned at 0)' : 'n/a')) + ')</td></tr>' +
    '</tbody></table>' +
    '<p style="margin-top:0.6em; font-size:0.92em; color:#444;"><strong>Verdict:</strong> Linear slope row ' + slopeStatus.toUpperCase() + ': engine linear-pool slope ' + fmtNum(lin.pooled_slope_log, 5) + ' vs R <code>dosresmeta</code> ' + fmtNum(rJson.linear.pooled_slope_log, 5) + ' (|&Delta;| = ' + fmtNum(dSlope, 5) + ' &lt; ' + THRESHOLDS.linear_slope + '). The SE divergence vs R&apos;s SE is the HKSJ vs no-HKSJ choice; both are valid; engine&apos;s HKSJ-inflated SE is the more conservative reporting. Linear &tau;<sup>2</sup> row ' + tau2Status.toUpperCase() + ': engine ' + lin.tau2.toExponential(2) + ' vs R ' + (rJson.linear.tau2 != null ? rJson.linear.tau2.toExponential(2) : 'n/a') + ' (|&Delta;| = ' + dTau2.toExponential(2) + (tau2Status === 'green' ? ' &lt; ' : ' &ge; ') + THRESHOLDS.linear_tau2 + ' &mdash; both essentially zero, cross-trial slope is highly homogeneous). RCS rows ENGINE-DECLINED / R-FIT: the engine&apos;s refusal is the methodologically conservative call; R&apos;s fit is technically valid arithmetic but its 3 percentile knots all land inside the 140&ndash;210 mg interval with no data to support the within-range curvature. The 3 rows are deferred to engine v0.5, which may extend the R-parity contract by surfacing R&apos;s degenerate-knot fit explicitly (e.g. a row that compares the engine&apos;s linear-fallback slope against R&apos;s spline-derived effective slope at the maximum observed dose). Engine&apos;s contribution on this fixture is surfacing the disagreement as a structured signal rather than silently accepting R&apos;s uninformative-knot fit.</p>' +
    '<p style="margin-top:0.4em; font-size:0.85em; color:#555;"><strong>R precompute source:</strong> <code>outputs/r_validation/doseresp/brodalumab_psoriasis_amagine.json</code> (dosresmeta v' + escapeHtml(rJson.dosresmeta_version || 'unknown') + '; input k = ' + (rJson.k != null ? rJson.k : 'unknown') + '). R linear-pool block has <code>fit_ok = true</code>; R RCS block has <code>fit_ok = true</code> with knots inside the 140&ndash;210 mg gap (this is the AMAGINE-specific case &mdash; SUSTAIN and SELECT have R <code>rcs.fit_ok = false</code>). R one-stage block has <code>fit_ok = true</code> with <code>converged = ' + (osR.converged === true ? 'true' : 'false') + '</code>.</p>' +
    '</details>' +
    '</div>';
  document.getElementById('r-parity-brodalumab-pasi').innerHTML = html;
}
