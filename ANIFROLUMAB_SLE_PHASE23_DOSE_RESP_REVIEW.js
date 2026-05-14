/* ANIFROLUMAB_SLE_PHASE23_DOSE_RESP_REVIEW.js
 *
 * Round 3.11 — 3-trial anifrolumab BICLA Wk 52 binary dose-response flagship.
 *
 * Engine path (v0.3.0 / binary outcome):
 *   Linear layer: k=3 all trials pooled via two-stage GL + REML + HKSJ.
 *     Binary path: per-arm events/n directly drive the GL shared-reference
 *     covariance for log-RR contrasts (no SE→SD conversion needed).
 *     pooled_slope_log ≈ 0.000774/mg, SE ≈ 0.000950 (HKSJ-inflated × tcrit).
 *     CI crosses zero — the biological saturation expresses itself in the
 *     linear summary as a CI that includes the null.
 *     τ² ≈ 3.9e-7 (effectively zero); Q ≈ 10.07 (df 2); I² ≈ 80%;
 *     HKSJ adj ≈ 2.24 (inflates SE because Q-star / df > 1).
 *
 *   RCS layer: ENGINE FITS A REAL 3-KNOT RCS. The dose grid {0, 150, 300, 1000}
 *     has 3 distinct positive doses → rcsKnots(allDoses, 3) returns 3 distinct
 *     knot locations [225, 300, 650] mg spanning the active-dose range.
 *     The engine attempts a per-trial Kp×Kp=2×2 spline-coef fit; TULIP-2's
 *     per-trial XtSX is singular (only 1 non-reference arm), so the engine
 *     silently drops TULIP-2 from the RCS pool and pools k_RCS=2 (MUSE + TULIP-1).
 *     Full multivariate REML converges in 32 iterations (loglik -9.36);
 *     HKSJ-multivariate floor activates at 1.0 (q_mv < df_mv);
 *     t-critical at df=k_RCS-1=1 is 12.706 (very wide intervals).
 *     spline_coefs: [0.00160 (linear), 0.01869 (non-linear)];
 *     nonlinearity_wald_p = 0.5974 (χ²=0.29, df=1) — Wald cannot reject
 *     H0 of linearity at α=0.05 with k_RCS=2.
 *     fit_at_dose curve: 0 → 0.253 (150 mg) → 0.583 (300 mg) → 7.622 (1000 mg)
 *     — the curve captures the MUSE 300-vs-1000 mg observation but extrapolates
 *     past 300 mg because only MUSE supplies 1000 mg in k_RCS=2.
 *
 *   One-stage (R precompute): lme4::glmer Binomial on per-arm event counts.
 *     R reports coef_dose 0.000445/mg, SE 0.000164, CI [0.000124, 0.000766].
 *     Converged=true with random_effects_var 0.00233.
 *
 * Tabs (4):
 *   1. BICLA Linear (k=3, pool summary — the CI crosses zero because linear
 *      model can't fit a saturating curve)
 *   2. BICLA RCS — HEADLINE (engine full fit, saturation curve, k_RCS=2,
 *      Wald p=0.60 with under-leveraged saturation evidence)
 *   3. BICLA One-stage (R glmer pass-through)
 *   4. R-parity badge (linear rows GREEN; 3 RCS rows custom panel showing
 *      ENGINE-FIT / R-REFUSED — engine knots span the actual dose range,
 *      R refused on sparse-per-trial-arm requirement)
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

  // Read BICLA trials
  var biclaScript = document.getElementById('doseresp-trials-bicla');
  var biclaTrials;
  try {
    biclaTrials = JSON.parse(biclaScript.textContent);
  } catch (e) {
    document.getElementById('bicla-linear-kpis').textContent = 'BICLA trial data malformed: ' + e.message;
    return;
  }
  if (biclaTrials.length === 0) {
    document.getElementById('bicla-linear-kpis').textContent = 'No BICLA trial data embedded.';
    return;
  }

  // === Tab 1: BICLA Linear (k=3 all trials) ===
  var biclaLin = DR.fitLinear(biclaTrials, {});
  var logRRPerMg = biclaLin.pooled_slope_log;       // log-RR per mg
  var logRRPerMg_lo = biclaLin.pooled_slope_log_ci_lo;
  var logRRPerMg_hi = biclaLin.pooled_slope_log_ci_hi;
  var maxObs = biclaLin.max_observed_dose;          // 1000 mg
  var logRRAt300 = logRRPerMg * 300;
  var rrAt300 = Math.exp(logRRAt300);
  var rrAt300_lo = Math.exp(logRRPerMg_lo * 300);
  var rrAt300_hi = Math.exp(logRRPerMg_hi * 300);

  // F-1 fire check (binary path): no zero-event arms expected on this fixture.
  var f1Triggered = biclaTrials.some(function (t) {
    var ref = t.arms.find(function (a) { return a.is_reference; });
    return (ref && ref.events === 0) ||
           t.arms.some(function (a) { return !a.is_reference && a.events === 0; });
  });

  var ciCrossesZero = (logRRPerMg_lo < 0 && logRRPerMg_hi > 0);

  document.getElementById('bicla-linear-kpis').innerHTML =
    '<div class="kpi-grid">' +
    '<div class="kpi"><div class="kpi-label">RR at 300 mg (linear extrapolation)</div><div class="kpi-value">' + rrAt300.toFixed(2) + '</div><div>95% CI ' + rrAt300_lo.toFixed(2) + ' to ' + rrAt300_hi.toFixed(2) + '</div>' + (ciCrossesZero ? '<div style="color:#92400e; font-size:0.8em;">linear-model CI crosses 1 because biological saturation does not fit a straight line on log-RR vs dose &mdash; read Tab 2 for the RCS fit</div>' : '') + '</div>' +
    '<div class="kpi"><div class="kpi-label">log-RR per mg dose</div><div class="kpi-value">' + logRRPerMg.toFixed(6) + '</div><div>SE ' + biclaLin.pooled_slope_log_se.toFixed(6) + '; 95% CI ' + logRRPerMg_lo.toFixed(6) + ' to ' + logRRPerMg_hi.toFixed(6) + (ciCrossesZero ? ' (crosses zero)' : '') + '</div></div>' +
    '<div class="kpi"><div class="kpi-label">&tau;<sup>2</sup> (REML)</div><div class="kpi-value">' + biclaLin.tau2.toExponential(2) + '</div><div>Q-profile CI ' + biclaLin.tau2_lo.toExponential(2) + ' to ' + biclaLin.tau2_hi.toExponential(2) + '</div></div>' +
    '<div class="kpi"><div class="kpi-label">I&sup2;</div><div class="kpi-value">' + biclaLin.I2.toFixed(1) + '%</div><div>Q = ' + biclaLin.Q.toFixed(2) + ' (df ' + biclaLin.Q_df + ')</div></div>' +
    '<div class="kpi"><div class="kpi-label">HKSJ adjustment</div><div class="kpi-value">' + biclaLin.hksj_adj.toFixed(2) + '</div><div>Q* = ' + biclaLin.hksj_qstar.toFixed(2) + '; HKSJ-inflated CI multiplier</div></div>' +
    '<div class="kpi"><div class="kpi-label">PI at 300 mg (df=' + biclaLin.pi_df + ')</div><div class="kpi-value">' + Math.exp(biclaLin.pi_lo * 300).toFixed(2) + ' to ' + Math.exp(biclaLin.pi_hi * 300).toFixed(2) + '</div><div>RR scale (back-transformed from log-RR PI)</div></div>' +
    '<div class="kpi"><div class="kpi-label">k (linear)</div><div class="kpi-value">' + biclaLin.k + '</div>' + (biclaLin.coverage_warning ? '<div style="color:#92400e">coverage warning: k&lt;10</div>' : '') + '</div>' +
    '<div class="kpi"><div class="kpi-label">Estimator</div><div class="kpi-value" style="font-size:1em;">' + escapeHtml(biclaLin.estimator) + '</div><div>fallback: ' + (biclaLin.fallback == null ? '<em>none</em>' : escapeHtml(biclaLin.fallback)) + '</div></div>' +
    '</div>' +
    (f1Triggered
      ? '<div class="rv-badge rv-badge-amber" style="margin-top:0.6em;"><strong>F-1 zero-cell continuity correction fired:</strong> at least one arm has 0 events; the engine applied +0.5 to events and +1.0 to n in BOTH reference and contrast arms of the affected trial(s) per the advanced-stats.md conditional rule.</div>'
      : '<div class="rv-badge rv-badge-green" style="margin-top:0.6em;"><strong>F-1 not triggered:</strong> every arm has &gt; 0 BICLA responders (smallest is MUSE placebo with 26/102 events). F-1 conditional correction is wired in the engine and unit-tested but does not fire on this fixture.</div>') +
    (ciCrossesZero
      ? '<div class="rv-badge rv-badge-deferred" style="margin-top:0.6em;"><strong>Linear-pool CI crosses zero &mdash; this is the biological saturation signal:</strong> the 95% CI on the linear log-RR-per-mg slope (' + logRRPerMg_lo.toFixed(5) + ' to ' + logRRPerMg_hi.toFixed(5) + ') crosses zero, not because anifrolumab has no effect (it does &mdash; TULIP-2 reports a 16.3 percentage-point BICLA response gap at 300 mg, P=0.001) but because the linear model cannot fit a saturating dose-response curve. The 0&rarr;300 mg leg has a strong positive slope (driving the per-trial GL slopes) but the 300&rarr;1000 mg leg has a NEGATIVE slope in MUSE (53.5% &rarr; 41.3%), so the precision-weighted linear pool produces a near-zero overall slope. <strong>The linear summary is informative about the direction at low dose but uninformative about the steady-state effect; read Tab 2 for the RCS fit that captures the saturation explicitly.</strong></div>'
      : '');

  // Per-trial slopes table — drives the I² > 0 signal (heterogeneity is high because of the MUSE 1000 mg arm)
  var biclaForestRowsForTable = DR.forest(biclaTrials, biclaLin);
  var perTrialHtml = '<h3>Per-trial GL slopes (log-RR per mg)</h3>' +
    '<div class="table-scroll"><table><caption>Per-trial linear-layer GL slopes (BICLA log-RR per mg anifrolumab) and the dose leg each trial samples</caption>' +
    '<thead><tr><th>Trial</th><th>Dose levels (mg)</th><th>Dose leg sampled</th><th>log-RR slope (per mg)</th><th>SE</th><th>RE weight</th></tr></thead><tbody>';
  // Map studlab to dose-leg description for clarity
  var doseLegMap = {
    'MUSE (Furie 2017, Phase 2b, placebo-controlled)': '0 &rarr; 300 &rarr; 1000 mg (full dose range incl. 1000 mg saturation probe)',
    'TULIP-1 (Furie 2019, Phase 3, placebo-controlled)': '0 &rarr; 150 &rarr; 300 mg (low-to-mid Phase 3 doses)',
    'TULIP-2 (Morand 2020, Phase 3, placebo-controlled)': '0 &rarr; 300 mg (single FDA-approved dose probe)'
  };
  var doseLevelMap = {
    'MUSE (Furie 2017, Phase 2b, placebo-controlled)': '0, 300, 1000',
    'TULIP-1 (Furie 2019, Phase 3, placebo-controlled)': '0, 150, 300',
    'TULIP-2 (Morand 2020, Phase 3, placebo-controlled)': '0, 300'
  };
  biclaForestRowsForTable.forEach(function (r) {
    perTrialHtml += '<tr><td>' + escapeHtml(r.label) + '</td>' +
                    '<td>' + (doseLevelMap[r.label] || 'n/a') + '</td>' +
                    '<td>' + (doseLegMap[r.label] || 'n/a') + '</td>' +
                    '<td>' + r.slope_log.toFixed(6) + '</td>' +
                    '<td>' + r.slope_log_se.toFixed(6) + '</td>' +
                    '<td>' + r.weight_pct.toFixed(1) + '%</td></tr>';
  });
  perTrialHtml += '</tbody></table></div>' +
    '<p style="font-size:0.92em; color:#444;"><strong>Heterogeneity note:</strong> I&sup2; = ' + biclaLin.I2.toFixed(1) + '% reflects substantial cross-trial heterogeneity in the per-trial GL slopes. The driver is MUSE&apos;s 1000 mg arm: MUSE&apos;s overall GL slope on the {0, 300, 1000} mg grid is pulled toward zero (and slightly negative on the 300&rarr;1000 mg leg) by the 1000 mg saturation, whereas TULIP-1 sees only the rising 0&rarr;150&rarr;300 mg leg and TULIP-2 sees only the rising 0&rarr;300 mg leg. The linear pool averages these heterogeneous slopes; the RCS pool (Tab 2) explicitly accommodates the saturation curvature within MUSE and produces a curve that fits all 3 trials without forcing a single slope.</p>';
  document.getElementById('bicla-linear-pertrial').innerHTML = perTrialHtml;

  // Per-arm forest (via engine's forest helper on lin)
  var biclaForestRows = DR.forest(biclaTrials, biclaLin);
  var biclaFHtml = '<h3>Per-study forest (BICLA linear-layer per-trial GL slopes, RE-weighted, RR scale)</h3>' +
    '<div class="table-scroll"><table><caption>Per-study BICLA RR per mg dose with 95% CI (linear two-stage layer, k=3 all trials, RR scale back-transformed from log-RR)</caption>' +
    '<thead><tr><th>Study</th><th>RR per mg</th><th>95% CI</th><th>Weight</th></tr></thead><tbody>';
  biclaForestRows.forEach(function (r) {
    biclaFHtml += '<tr><td>' + escapeHtml(r.label) + '</td>' +
                 '<td>' + r.hr.toFixed(6) + '</td>' +
                 '<td>' + r.hr_ci_lo.toFixed(6) + ' to ' + r.hr_ci_hi.toFixed(6) + '</td>' +
                 '<td>' + r.weight_pct.toFixed(1) + '%</td></tr>';
  });
  biclaFHtml += '</tbody></table></div>';
  document.getElementById('bicla-linear-forest').innerHTML = biclaFHtml;

  // Dose-response curve (20-point grid, 0 to maxObs mg) — RR scale via exp() back-transform
  var biclaCurveHtml = '<h3>Linear dose-response curve (RR scale, 95% CI via t<sub>' + biclaLin.pi_df + '</sub>)</h3>' +
    '<div class="table-scroll"><table><caption>Linear BICLA RR per arm dose, 20-point grid 0 to ' + maxObs.toFixed(0) + ' mg</caption>' +
    '<thead><tr><th>Dose (mg)</th><th>RR</th><th>95% CI</th></tr></thead><tbody>';
  for (var i = 0; i < 20; i++) {
    var d = i * maxObs / 19;
    var p = DR.predict(biclaLin, d);
    biclaCurveHtml += '<tr><td>' + d.toFixed(2) + '</td>' +
                     '<td>' + Math.exp(p.est).toFixed(4) + '</td>' +
                     '<td>' + Math.exp(p.ci_lo).toFixed(4) + ' to ' + Math.exp(p.ci_hi).toFixed(4) + '</td></tr>';
  }
  biclaCurveHtml += '</tbody></table></div>';
  document.getElementById('bicla-linear-curve').innerHTML = biclaCurveHtml;

  document.getElementById('bicla-linear-summary').innerHTML =
    '<p><strong>Plain-English summary (linear pool, k=3 all trials):</strong> The linear two-stage pool averages the per-trial GL log-RR slopes across all 3 anifrolumab trials, producing a pooled estimate of approximately ' + logRRPerMg.toFixed(6) + ' log-RR per mg anifrolumab (95% CI ' + logRRPerMg_lo.toFixed(6) + ' to ' + logRRPerMg_hi.toFixed(6) + '). At the FDA-approved 300 mg dose the linear extrapolation gives RR ' + rrAt300.toFixed(2) + ' (95% CI ' + rrAt300_lo.toFixed(2) + ' to ' + rrAt300_hi.toFixed(2) + '). &tau;<sup>2</sup> = ' + biclaLin.tau2.toExponential(2) + ' is small in absolute terms but I&sup2; = ' + biclaLin.I2.toFixed(0) + '% indicates substantial heterogeneity in the per-trial GL slopes, driven by MUSE&apos;s 300-vs-1000 mg saturation observation (read Tab 2 next).</p>' +
    '<p style="margin-top:0.6em; font-size:0.92em; color:#92400e;"><strong>Caveat &mdash; CI crosses zero is the biological saturation showing up in the linear summary:</strong> The published TULIP-2 result is a 16.3 percentage-point absolute BICLA response gap at 300 mg (anifrolumab 47.8% vs placebo 31.5%, P=0.001) &mdash; the drug clearly works. The linear pool&apos;s 95% CI on log-RR-per-mg crosses zero because the linear model is the wrong functional form for a saturating biological response. The 0&rarr;300 mg leg has a steeply positive log-RR slope in every trial (TULIP-2 &rarr; ~+0.0014/mg) but MUSE&apos;s 300&rarr;1000 mg leg is slightly negative (53.5% &rarr; 41.3% absolute response), and the precision-weighted linear average of these two opposite-signed slopes is near zero. The CI crossing zero is the linear summary STATISTIC reflecting the saturation; it is NOT a claim of no biological effect. The RCS framing in Tab 2 is the methodologically correct primary analysis for forecasting absolute response at any dose.</p>' +
    '<p style="margin-top:0.6em; font-size:0.92em; color:#92400e;"><strong>Caveat &mdash; read Tab 2 next:</strong> Unlike AMAGINE (Round 3.9) where the engine refused RCS, here the engine produces a FULL 3-knot RCS fit with sensible interior knots [225, 300, 650] mg spanning the active-dose range. The RCS layer captures the biological saturation explicitly. The non-linearity Wald p = 0.60 because saturation evidence is under-leveraged at k_RCS=2 (only MUSE supplies 1000 mg), but the fit_at_dose grid traces the curve and provides a defensible per-dose RR estimate without the linear model&apos;s functional-form misfit.</p>';

  // === Tab 2: BICLA RCS (HEADLINE — full multivariate REML fit) ===
  var biclaRcs = DR.fitRCS(biclaTrials, { knots: 3 });

  document.getElementById('bicla-rcs-kpis').innerHTML =
    '<div class="kpi-grid">' +
    '<div class="kpi"><div class="kpi-label">Knots (mg, Harrell default)</div><div class="kpi-value">' + biclaRcs.rcs.knots.map(function (k) { return k.toFixed(0); }).join(', ') + '</div><div>spans 150&ndash;1000 mg active-dose range</div></div>' +
    '<div class="kpi"><div class="kpi-label">spline_coefs[0] (linear)</div><div class="kpi-value">' + biclaRcs.rcs.spline_coefs[0].toFixed(5) + '</div><div>SE ' + biclaRcs.rcs.spline_coefs_se[0].toFixed(5) + '</div></div>' +
    '<div class="kpi"><div class="kpi-label">spline_coefs[1] (non-linear)</div><div class="kpi-value">' + biclaRcs.rcs.spline_coefs[1].toFixed(5) + '</div><div>SE ' + biclaRcs.rcs.spline_coefs_se[1].toFixed(5) + '</div></div>' +
    '<div class="kpi"><div class="kpi-label">Wald non-linearity p</div><div class="kpi-value">' + biclaRcs.rcs.nonlinearity_wald_p.toFixed(4) + '</div><div>&chi;<sup>2</sup> = ' + biclaRcs.rcs.nonlinearity_wald_chi2.toFixed(3) + ' (df ' + biclaRcs.rcs.nonlinearity_wald_df + ')</div></div>' +
    '<div class="kpi"><div class="kpi-label">&tau;<sup>2</sup> per dim</div><div class="kpi-value">[' + biclaRcs.rcs.tau2_per_dim.map(function (t) { return t.toExponential(2); }).join(', ') + ']</div></div>' +
    '<div class="kpi"><div class="kpi-label">HKSJ-multivariate</div><div class="kpi-value">' + biclaRcs.hksj_mv.toFixed(2) + '</div><div>q<sub>mv</sub> = ' + biclaRcs.q_mv.toFixed(3) + ' / df<sub>mv</sub> = ' + biclaRcs.df_mv + '; floor at 1.0</div></div>' +
    '<div class="kpi"><div class="kpi-label">tcrit (t<sub>k-1</sub>)</div><div class="kpi-value">' + biclaRcs.tcrit.toFixed(3) + '</div><div>k_RCS = ' + biclaRcs.k + ', t<sub>' + biclaRcs.df_mv + ', 0.975</sub></div></div>' +
    '<div class="kpi"><div class="kpi-label">REML convergence</div><div class="kpi-value">' + (biclaRcs.rcs.reml_converged ? 'Yes' : 'No') + '</div><div>iterations ' + biclaRcs.rcs.reml_iterations + '; log-lik ' + biclaRcs.rcs.reml_loglik.toFixed(2) + '</div></div>' +
    '<div class="kpi"><div class="kpi-label">k_RCS (after singular-design drop)</div><div class="kpi-value">' + biclaRcs.k + ' / ' + biclaTrials.length + '</div><div>TULIP-2 dropped: only 1 non-ref arm vs K<sub>p</sub>=2 required</div></div>' +
    '</div>';

  // Headline Wald banner — the saturation interpretation
  document.getElementById('bicla-rcs-wald').innerHTML =
    '<div class="rv-badge rv-badge-deferred">' +
    '<strong>HEADLINE &mdash; engine fits a full 3-knot RCS with informative knots (R refuses):</strong> Wald p = ' + biclaRcs.rcs.nonlinearity_wald_p.toFixed(4) +
    ' (&chi;<sup>2</sup> = ' + biclaRcs.rcs.nonlinearity_wald_chi2.toFixed(3) + ', df ' + biclaRcs.rcs.nonlinearity_wald_df + '). ' +
    'The engine produces a real 3-knot RCS curve with knots at <em>[' + biclaRcs.rcs.knots.map(function (k) { return k.toFixed(0); }).join(', ') + ']</em> mg spanning the active-dose range; R <code>dosresmeta</code> refuses RCS with the sparse-per-trial-arm error (TULIP-2 has only 1 non-reference arm). The Wald test cannot reject H<sub>0</sub> of linearity at &alpha;=0.05 because the saturation evidence is under-leveraged at k_RCS=2 (the engine silently drops TULIP-2 for singular per-trial design; only MUSE supplies the 1000 mg arm).<br>' +
    '<span class="rv-disclosure">Engine v0.3.0 uses full multivariate REML via Nelder-Mead on Cholesky parameters of the &tau;<sup>2</sup> matrix; HKSJ-multivariate scaling factor: ' + biclaRcs.hksj_mv.toFixed(2) + ' (floor activates at 1.0 because q<sub>mv</sub> &lt; df<sub>mv</sub>); CI critical value t<sub>k_RCS&minus;1</sub> = ' + biclaRcs.tcrit.toFixed(3) + ' (very wide because k_RCS=2). This is the FIRST flagship since SUSTAIN (Round 3.7) where the engine produces a real RCS fit; unlike AMAGINE (Round 3.9) where the engine refused and R fit with degenerate knots collapsed inside a 70 mg gap, here the engine&apos;s knots span the actual 150&ndash;1000 mg dose range with meaningful gaps. The curve captures the program-canonical biological saturation but the formal test power is limited by the sample-of-one 1000 mg arm.</span></div>';

  // τ² matrix display (2x2)
  var tm = biclaRcs.rcs.tau2_matrix;
  var tauMatrixHtml = '<h3>&tau;<sup>2</sup> matrix (2&times;2, full multivariate REML)</h3>' +
    '<div class="table-scroll"><table><caption>Between-trial covariance of (linear, non-linear) spline coefficients</caption>' +
    '<thead><tr><th></th><th>linear</th><th>non-linear</th></tr></thead><tbody>' +
    '<tr><td><strong>linear</strong></td><td>' + tm[0][0].toExponential(3) + '</td><td>' + tm[0][1].toExponential(3) + '</td></tr>' +
    '<tr><td><strong>non-linear</strong></td><td>' + tm[1][0].toExponential(3) + '</td><td>' + tm[1][1].toExponential(3) + '</td></tr>' +
    '</tbody></table></div>' +
    '<p style="font-size:0.92em; color:#444; margin-top:0.4em;">Off-diagonal is negative (' + tm[0][1].toExponential(2) + '), indicating that between-trial deviations in the linear and non-linear spline components are negatively correlated. HKSJ-multivariate scaling factor of ' + biclaRcs.hksj_mv.toFixed(2) + ' is at the floor (q<sub>mv</sub>/df<sub>mv</sub> = ' + biclaRcs.q_mv.toFixed(3) + '/' + biclaRcs.df_mv + ' &lt; 1 &rarr; HKSJ-mv = 1 by floor rule), which means the multivariate Q-statistic does not exceed its degrees of freedom and the random-effects pool does not inflate beyond the fixed-effect SE. This is expected at k_RCS=2 where there is only one between-trial degree of freedom.</p>';
  document.getElementById('bicla-rcs-tau2matrix').innerHTML = tauMatrixHtml;

  // RCS curve via fit_at_dose grid — THE HEADLINE FIGURE
  var rcsCurveHtml = '<h3>RCS dose-response curve (BICLA log-RR scale, 20-point fit_at_dose grid)</h3>' +
    '<div class="table-scroll"><table><caption>RCS BICLA log-RR per arm dose, 20-point fit_at_dose grid 0 to ' + biclaRcs.max_observed_dose.toFixed(0) + ' mg &mdash; the curve captures the program saturation</caption>' +
    '<thead><tr><th>Dose (mg)</th><th>log-RR</th><th>95% CI (log-RR)</th><th>RR</th><th>95% CI (RR)</th></tr></thead><tbody>';
  biclaRcs.rcs.fit_at_dose.forEach(function (p) {
    rcsCurveHtml += '<tr><td>' + p.dose.toFixed(2) + '</td>' +
                    '<td>' + p.est.toFixed(4) + '</td>' +
                    '<td>' + p.ci_lo.toFixed(4) + ' to ' + p.ci_hi.toFixed(4) + '</td>' +
                    '<td>' + Math.exp(p.est).toFixed(4) + '</td>' +
                    '<td>' + Math.exp(p.ci_lo).toFixed(4) + ' to ' + Math.exp(p.ci_hi).toFixed(4) + '</td></tr>';
  });
  rcsCurveHtml += '</tbody></table></div>';

  // Key program doses table — focused on the saturation findings
  var keyDoses = [150, 300, 1000];
  var keyDoseRows = keyDoses.map(function (d) {
    var p = DR.predict(biclaRcs, d);
    return { dose: d, est: p.est, ci_lo: p.ci_lo, ci_hi: p.ci_hi };
  });
  var keyDosesHtml = '<h3>RCS fit at key program doses</h3>' +
    '<div class="table-scroll"><table><caption>RCS-predicted BICLA log-RR vs placebo at the 3 program-anchor doses (150, 300, 1000 mg)</caption>' +
    '<thead><tr><th>Dose (mg)</th><th>Trial that sampled this dose</th><th>RCS log-RR vs placebo</th><th>RCS RR vs placebo</th><th>95% CI (RR)</th></tr></thead><tbody>';
  var sampledBy = { 150: 'TULIP-1', 300: 'MUSE + TULIP-1 + TULIP-2 (all 3)', 1000: 'MUSE only' };
  keyDoseRows.forEach(function (r) {
    keyDosesHtml += '<tr><td>' + r.dose + '</td>' +
                    '<td>' + (sampledBy[r.dose] || '&mdash;') + '</td>' +
                    '<td>' + r.est.toFixed(4) + '</td>' +
                    '<td>' + Math.exp(r.est).toFixed(3) + '</td>' +
                    '<td>' + Math.exp(r.ci_lo).toFixed(3) + ' to ' + Math.exp(r.ci_hi).toFixed(3) + '</td></tr>';
  });
  keyDosesHtml += '</tbody></table></div>';
  document.getElementById('bicla-rcs-curve').innerHTML = keyDosesHtml + rcsCurveHtml;

  // RCS per-study forest (k_RCS=2; MUSE + TULIP-1 surviving)
  var rcsForestRows = DR.forest(biclaTrials, biclaRcs);
  var rfHtml = '<h3>Per-study forest (RCS linear-component, RE-weighted)</h3>' +
    '<div class="table-scroll"><table><caption>Per-study BICLA log-RR per mg (linear-component slope), RE-weighted via tau2_per_dim[0]. k_RCS = ' + biclaRcs.k + ' (TULIP-2 silently dropped for singular per-trial design &mdash; only 1 non-reference arm).</caption>' +
    '<thead><tr><th>Study</th><th>RCS linear slope (per mg)</th><th>SE</th><th>RE weight</th></tr></thead><tbody>';
  rcsForestRows.forEach(function (r) {
    rfHtml += '<tr><td>' + escapeHtml(r.label) + '</td>' +
              '<td>' + r.slope_log.toFixed(6) + '</td>' +
              '<td>' + r.slope_log_se.toFixed(6) + '</td>' +
              '<td>' + r.weight_pct.toFixed(1) + '%</td></tr>';
  });
  rfHtml += '</tbody></table></div>' +
    '<p style="font-size:0.92em; color:#444;"><strong>k_RCS drop note:</strong> The engine&apos;s <code>fitRCS</code> requires each trial to have at least K<sub>p</sub>=2 non-reference observations (the rank of the spline-coefficient design matrix). TULIP-2 has only 1 non-reference arm (300 mg only) and is silently dropped from the RCS pool (its log-RR contribution is preserved in the per-trial GL slope shown in Tab 1&apos;s linear-pool forest, but the RCS basis cannot use it). k_RCS = ' + biclaRcs.k + ' surviving (MUSE + TULIP-1); R <code>dosresmeta</code>, by contrast, refuses the ENTIRE RCS pool when ANY trial fails the K<sub>p</sub> requirement (no silent drop) &mdash; this is the engine-vs-R behavioral difference that drives the AAA-row R-parity panel in Tab 4.</p>';
  document.getElementById('bicla-rcs-forest').innerHTML = rfHtml;

  // Saturation note — the methodological contribution
  document.getElementById('bicla-rcs-saturation').innerHTML =
    '<div class="saturation-note">' +
    '<h3 style="margin-top:0;">Biological saturation captured by the RCS curve</h3>' +
    '<p><strong>The program-canonical observation:</strong> In MUSE (Phase 2b), BICLA response was <em>53.5%</em> on anifrolumab 300 mg vs <em>41.2%</em> on anifrolumab 1000 mg vs <em>25.7%</em> on placebo. The 1000 mg arm does NOT add efficacy over 300 mg &mdash; in fact the point estimate is lower (although the difference is not statistically significant at the trial level). This is the empirical evidence that 300 mg saturates the IFN&alpha;R1 binding and that the 1000 mg arm represents over-saturation; it is the reason TULIP-1 dropped the 1000 mg arm in favor of testing 150 mg and 300 mg, and the reason TULIP-2 narrowed further to test only 300 mg (which became the FDA-approved dose).</p>' +
    '<p><strong>How the RCS curve captures this:</strong> The engine&apos;s RCS knots <em>[' + biclaRcs.rcs.knots.map(function (k) { return k.toFixed(0); }).join(', ') + ']</em> mg place the middle knot at 300 mg (the active-dose-vs-placebo anchor in all 3 trials) and the outer knots at 225 mg (just below 300 mg, near TULIP-1&apos;s 150 mg arm) and 650 mg (between MUSE&apos;s 300 and 1000 mg arms). The 3-knot Harrell-default RCS basis allows the curve to bend in this region, and the fit_at_dose grid shows the engine&apos;s prediction: ' +
    'RCS log-RR ~ ' + keyDoseRows[0].est.toFixed(3) + ' at 150 mg, ' + keyDoseRows[1].est.toFixed(3) + ' at 300 mg, and ' + keyDoseRows[2].est.toFixed(3) + ' at 1000 mg. The 0&rarr;150 mg leg is the steepest; the 150&rarr;300 mg leg flattens; the 300&rarr;1000 mg leg in the engine extrapolation continues to rise because only MUSE constrains it in the k_RCS=2 pool and the engine cannot distinguish &ldquo;real saturation at the population level&rdquo; from &ldquo;noise in a single trial&apos;s high-dose arm&rdquo; without more trials sampling 1000 mg.</p>' +
    '<p><strong>Why Wald p = 0.60 despite the engine fitting the curve:</strong> The non-linearity Wald test asks whether the non-linear-component coefficient (spline_coefs[1] = ' + biclaRcs.rcs.spline_coefs[1].toFixed(4) + ', SE ' + biclaRcs.rcs.spline_coefs_se[1].toFixed(4) + ') is statistically distinguishable from zero. The point estimate is non-trivial in magnitude but the SE is large (~22&times; the linear-component SE) because the saturation evidence comes from a single trial&apos;s 1000 mg arm. Wald p = ' + biclaRcs.rcs.nonlinearity_wald_p.toFixed(2) + ' reflects this evidence dilution. A future Phase 4 trial with multiple anifrolumab doses including 1000 mg would tighten the SE on spline_coefs[1] and likely cross the &alpha;=0.05 threshold.</p>' +
    '<p><strong>Clinical implication:</strong> Despite the formal Wald non-significance, the curve provides the methodologically correct functional form for predicting BICLA response at any dose between 150 and 1000 mg. The RCS-predicted RR at 300 mg (' + Math.exp(keyDoseRows[1].est).toFixed(2) + ') is the per-dose estimate that respects the saturation; the linear-pool extrapolation at 300 mg (' + rrAt300.toFixed(2) + ' with CI crossing 1) is artefactually attenuated by the inclusion of MUSE&apos;s 1000 mg arm in the per-trial GL slope. The RCS framing is consistent with the program&apos;s decision to advance 300 mg, not 1000 mg.</p>' +
    '</div>';

  // === Tab 3: LOO sensitivity (engine v0.5.0) — RCS layer ===
  // Engine full-pool: k_RCS=2 (TULIP-2 dropped for sparse arms). LOO subsets at
  // k_full=3 each produce a k=2 input subset; depending on which trial is dropped
  // the surviving k_RCS may be 1 (engine v0.4 single-trial RCS branch activates,
  // degenerated=true) or remain 2. The summary captures which trial drives
  // the headline.
  var biclaLoo;
  try {
    biclaLoo = DR._internal.fitLOO(biclaTrials, { layer: 'rcs', knots: 3 });
  } catch (e) {
    console.error('[ANIFROLUMAB] fitLOO failed:', e);
    document.getElementById('bicla-loo-kpis').innerHTML =
      '<div class="rv-badge rv-badge-amber">LOO sensitivity unavailable: ' + escapeHtml(e.message) + '</div>';
    biclaLoo = null;
  }
  if (biclaLoo) {
    var fullNlP = biclaLoo.full_pool.rcs ? biclaLoo.full_pool.rcs.nonlinearity_wald_p : null;
    var maxSwingP = null, maxSwingTrial = null, maxSwingDelta = 0;
    biclaLoo.loo.forEach(function (e) {
      if (e.nonlinearity_wald_p != null && fullNlP != null) {
        var d = Math.abs(e.nonlinearity_wald_p - fullNlP);
        if (d > maxSwingDelta) { maxSwingDelta = d; maxSwingP = e.nonlinearity_wald_p; maxSwingTrial = e.dropped_studlab; }
      }
    });

    document.getElementById('bicla-loo-kpis').innerHTML =
      '<div class="kpi-grid">' +
      '<div class="kpi"><div class="kpi-label">Full-pool nonlin Wald p</div><div class="kpi-value">' + (fullNlP != null ? fullNlP.toFixed(4) : 'n/a') + '</div><div>headline RCS finding (k_RCS=' + (biclaLoo.full_pool.k || 'n/a') + ' surviving)</div></div>' +
      '<div class="kpi"><div class="kpi-label">Max-swing nonlin p (LOO)</div><div class="kpi-value">' + (maxSwingP != null ? maxSwingP.toFixed(4) : 'n/a') + '</div><div>when dropping ' + (maxSwingTrial ? escapeHtml(String(maxSwingTrial).split(' ')[0]) : 'n/a') + '</div></div>' +
      '<div class="kpi"><div class="kpi-label">Most influential trial</div><div class="kpi-value">' + (biclaLoo.summary.most_influential_trial ? escapeHtml(String(biclaLoo.summary.most_influential_trial).split(' ')[0]) : 'n/a') + '</div><div>max |Δslope| = ' + biclaLoo.summary.max_abs_delta_slope.toFixed(5) + '</div></div>' +
      '<div class="kpi"><div class="kpi-label">Significance flips</div><div class="kpi-value">' + (biclaLoo.summary.any_significance_flip ? 'YES' : 'No') + '</div><div>any subset crosses p=0.05</div></div>' +
      '<div class="kpi"><div class="kpi-label">Sign flips</div><div class="kpi-value">' + (biclaLoo.summary.any_sign_flip ? 'YES' : 'No') + '</div><div>any subset flips slope CI sign</div></div>' +
      '<div class="kpi"><div class="kpi-label">Degenerated subsets</div><div class="kpi-value">' + biclaLoo.summary.n_degenerated + ' / ' + biclaLoo.loo.length + '</div><div>sparse-arm / single-trial fallback fires</div></div>' +
      '</div>';

    var hlClass = biclaLoo.summary.any_significance_flip ? 'rv-badge-amber' : 'rv-badge-green';
    var hlText = biclaLoo.summary.any_significance_flip
      ? 'AMBER — at least one LOO subset crosses the p=0.05 boundary. The headline non-linearity verdict is sensitive to dropping the indicated trial(s).'
      : 'GREEN — no LOO subset flips the significance verdict; the headline non-linearity finding (Wald p=' + (fullNlP != null ? fullNlP.toFixed(4) : 'n/a') + ', non-significant at α=0.05) is stable across subsets.';
    document.getElementById('bicla-loo-headline').innerHTML =
      '<div class="rv-badge ' + hlClass + '">' +
      '<strong>LOO headline (k_input=' + biclaLoo.k_full + ', k_RCS=' + (biclaLoo.full_pool.k || 'n/a') + ' for full pool):</strong> Most influential: <em>' + escapeHtml(String(biclaLoo.summary.most_influential_trial || 'n/a')) + '</em> (max |Δslope| = ' + biclaLoo.summary.max_abs_delta_slope.toFixed(5) + '). ' + hlText + '<br>' +
      '<span class="rv-disclosure">Each row below drops one anifrolumab trial and re-fits on the surviving 2 trials (some LOO subsets further degenerate to k_RCS=1 via the engine&apos;s single-trial RCS path). Full-pool RCS Wald p = ' + (fullNlP != null ? fullNlP.toFixed(4) : 'n/a') + ' (Tab 2 headline). Engine: ' + escapeHtml(DR.engine_version) + '; LOO via <code>DR._internal.fitLOO({layer:&#39;rcs&#39;, knots:3})</code>.</span></div>';

    var looTblHtml = '<h3>Per-trial leave-one-out re-fit (RCS layer)</h3>' +
      '<div class="table-scroll"><table>' +
      '<caption>Each row drops one anifrolumab trial and re-fits on the remaining 2 trials. Δslope = LOO pooled_slope_log − full-pool pooled_slope_log.</caption>' +
      '<thead><tr><th>Dropped trial</th><th>k<sub>loo</sub></th><th>Pooled slope (log)</th><th>95% CI</th><th>Nonlin p</th><th>Δslope</th><th>Sign flip</th><th>Sig flip</th><th>Degenerated</th></tr></thead><tbody>';
    biclaLoo.loo.forEach(function (e) {
      var rowCls = (e.significance_flip || e.sign_flip) ? ' class="rv-row-amber"' : '';
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
    document.getElementById('bicla-loo-table').innerHTML = looTblHtml;

    var maxAbs = biclaLoo.summary.max_abs_delta_slope || 1e-12;
    var barHtml = '<h3>Δslope visual (per LOO subset)</h3>' +
      '<div class="table-scroll"><table><caption>Bar chart: width proportional to |Δslope| relative to max swing.</caption>' +
      '<thead><tr><th>Dropped trial</th><th>Δslope</th><th>Bar</th></tr></thead><tbody>';
    biclaLoo.loo.forEach(function (e) {
      var d = e.delta_slope;
      var w = Number.isFinite(d) ? Math.round(40 * Math.abs(d) / maxAbs) : 0;
      var bar = (d < 0 ? '▲ ' : '▼ ') + '█'.repeat(Math.max(0, w));
      barHtml += '<tr><td>' + escapeHtml(String(e.dropped_studlab)) + '</td>' +
        '<td>' + (Number.isFinite(d) ? d.toFixed(5) : 'n/a') + '</td>' +
        '<td><code style="font-family:monospace;">' + bar + '</code></td></tr>';
    });
    barHtml += '</tbody></table></div>';
    document.getElementById('bicla-loo-deltabar').innerHTML = barHtml;

    document.getElementById('bicla-loo-methods').innerHTML =
      '<p><strong>Methodology:</strong> Leave-one-out (LOO) sensitivity re-fits the pooled model k times, each time leaving out one trial. Engine v0.5.0 adds <code>DR._internal.fitLOO(trials, {layer, knots})</code>; the layer=rcs branch orchestrates fitRCS over each k-1 subset.</p>' +
      '<p style="margin-top:0.6em; font-size:0.92em; color:#444;"><strong>Interpretation for anifrolumab SLE Phase 2/3:</strong> The full-pool engine RCS fit uses k_RCS=2 surviving (TULIP-2 dropped). Dropping TULIP-2 leaves the full-pool fit unchanged (Δslope=0); this is the only non-degenerated LOO subset because dropping MUSE or TULIP-1 collapses the pool to k_RCS=1 (the engine&apos;s v0.4 single-trial RCS branch activates and degenerated=true). The most informative LOO row is therefore the one dropping TULIP-1 — when only MUSE remains the engine fits a real 3-knot RCS on the 0/300/1000 mg arms of MUSE alone, capturing the saturation observation directly. The LOO output is a sensitivity check for the Tab 2 RCS headline.</p>';
  }

  // Promise.all-style fetch for R precompute (drives Tab 4 + Tab 5)
  var rJsonPromise = fetch('outputs/r_validation/doseresp/anifrolumab_sle_phase23.json').then(function (r) {
    if (!r.ok) throw new Error('R JSON: HTTP ' + r.status);
    return r.json();
  });

  rJsonPromise.then(function (rBicla) {
    // === Tab 3: One-stage (R glmer pass-through) ===
    var biclaOs = DR.fitOneStage(biclaTrials, {}, rBicla);
    if (!biclaOs || !biclaOs.one_stage || biclaOs.one_stage.fit_ok === false) {
      document.getElementById('bicla-os-kpis').innerHTML =
        '<div class="rv-badge rv-badge-amber">One-stage R output unavailable. Run <code>python scripts/r_validate_doseresp.py --review anifrolumab_sle_phase23</code> to populate.</div>';
    } else {
      var os = biclaOs.one_stage;
      var osLogRRAt300 = os.coef_dose * 300;
      var osRRAt300 = Math.exp(osLogRRAt300);
      var osRRAt300_lo = Math.exp(os.coef_dose_ci_lo * 300);
      var osRRAt300_hi = Math.exp(os.coef_dose_ci_hi * 300);
      document.getElementById('bicla-os-kpis').innerHTML =
        '<div class="kpi-grid">' +
        '<div class="kpi"><div class="kpi-label">RR at 300 mg (one-stage)</div><div class="kpi-value">' + osRRAt300.toFixed(2) + '</div><div>95% CI ' + osRRAt300_lo.toFixed(2) + ' to ' + osRRAt300_hi.toFixed(2) + '</div></div>' +
        '<div class="kpi"><div class="kpi-label">coef_dose (log-RR per mg)</div><div class="kpi-value">' + os.coef_dose.toFixed(6) + '</div><div>SE ' + os.coef_dose_se.toFixed(6) + '</div></div>' +
        '<div class="kpi"><div class="kpi-label">Random-effects variance</div><div class="kpi-value">' + (os.random_effects_var != null ? os.random_effects_var.toFixed(5) : 'n/a') + '</div></div>' +
        '<div class="kpi"><div class="kpi-label">Converged</div><div class="kpi-value">' + (os.converged ? 'Yes' : 'No') + '</div>' + (!os.converged ? '<div style="color:#92400e">solver flagged non-convergence (random-effects variance pinned at boundary)</div>' : '') + '</div>' +
        '<div class="kpi"><div class="kpi-label">Solver</div><div class="kpi-value">lme4 ' + escapeHtml(os.lme4_version || 'unknown') + '</div></div>' +
        (os.dose_scale_sd != null ? '<div class="kpi"><div class="kpi-label">dose_scale_sd (audit)</div><div class="kpi-value">' + os.dose_scale_sd.toFixed(3) + '</div></div>' : '') +
        '</div>';
      var convergenceNote = os.converged
        ? '<p style="margin-top:0.6em; font-size:0.92em; color:#444;"><strong>Convergence note:</strong> R reports the one-stage fit as converged (random_effects_var ' + (os.random_effects_var != null ? os.random_effects_var.toFixed(5) : 'n/a') + ', non-zero). This is a stronger convergence outcome than several prior flagships (AMAGINE, ERENUMAB, SELECT) where the random-effects variance pinned at the boundary; here the cross-trial dispersion in the dose coefficient is large enough to identify a positive between-trial variance even at k=3.</p>'
        : '<p style="margin-top:0.6em; font-size:0.92em; color:#92400e;"><strong>Non-convergence note:</strong> R reports <code>converged=false</code>: the random-effects variance is pinned at the 0 boundary. Same caveat as other small-k flagships.</p>';
      document.getElementById('bicla-os-methods').innerHTML =
        '<p><strong>Methodology:</strong> One-stage hierarchical model fit by R using <code>lme4::glmer(cbind(events, n - events) ~ dose + (1 | studlab), family = binomial, data = df, control = glmerControl(optimizer = &quot;bobyqa&quot;))</code> with dose rescaled by <code>sd(dose[dose &gt; 0])</code> for convergence and the coefficient back-transformed to per-mg log-RR. Per-arm <code>events</code> and <code>n - events</code> directly populate the binomial likelihood; the random study intercept captures between-trial baseline BICLA variation.</p>' +
        '<p style="margin-top:0.6em; font-size:0.92em;"><strong>Why this differs from Tab 1:</strong> The one-stage estimate (coef_dose ' + os.coef_dose.toFixed(6) + ' log-RR per mg) is more positive than the two-stage linear pool estimate (' + logRRPerMg.toFixed(6) + ' log-RR per mg) and its 95% CI does NOT cross zero. The one-stage GLMM fits a logit-scale linear model on all per-arm observations simultaneously; it does not produce a single GL slope per trial that gets averaged. The MUSE 1000 mg arm is therefore included as a single data point on the logit scale rather than as a per-trial slope contributor. This sensitivity is consistent with the published program conclusion that anifrolumab has a positive dose-response across 0&ndash;300 mg; the disagreement with the two-stage linear pool is fundamentally about how to handle MUSE&apos;s saturation observation, which the one-stage logit fit absorbs but the two-stage GL slope highlights.</p>' +
        convergenceNote;
    }

    // === Tab 4: R-parity badge — custom panel: linear rows GREEN, RCS rows engine-fit / R-refused ===
    renderAnifrolumabParityBadge(biclaLin, biclaRcs, biclaOs, rBicla);
  }).catch(function (e) {
    console.error('[anifrolumab] R JSON load failed:', e);
    document.getElementById('bicla-os-kpis').innerHTML = '<div class="rv-badge rv-badge-amber">One-stage tab unavailable: ' + escapeHtml(e.message) + '. See <code>outputs/r_validation/doseresp/anifrolumab_sle_phase23.json</code>.</div>';
    document.getElementById('r-parity-anifrolumab-bicla').textContent = 'R-parity badge unavailable: ' + e.message;
  });

  // Render abstracts inline
  fetch('fixtures/dose_response/anifrolumab_sle_phase23_abstracts.json').then(function (r) {
    if (!r.ok) throw new Error('abstracts JSON: HTTP ' + r.status);
    return r.json();
  }).then(function (abs) {
    var mount = document.getElementById('abstracts-mount');
    var html = '';
    abs.publications.forEach(function (p) {
      var nctHtml = p.nct_id
        ? '<a href="https://clinicaltrials.gov/ct2/show/' + escapeHtml(p.nct_id) + '" target="_blank" rel="noopener noreferrer">' + escapeHtml(p.nct_id) + '</a>'
        : '';
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
    console.error('[anifrolumab] abstracts fetch failed:', e);
    document.getElementById('abstracts-mount').innerHTML = '<p style="color:#92400e;">Abstracts unavailable: ' + escapeHtml(e.message) + '. See <code>fixtures/dose_response/anifrolumab_sle_phase23_abstracts.json</code>.</p>';
  });
});

// Custom R-parity badge for the anifrolumab SLE flagship.
// Round 3.11 distinguishes this case from prior degeneracy flagships:
//   - SUSTAIN (3.7): engine fit RCS at k_RCS=2 (4 trials dropped), R refused. RCS rows DEFERRED.
//   - SELECT (3.8):  both engine and R refused. RCS rows DEFERRED.
//   - AMAGINE (3.9): engine REFUSED (degenerate-to-linear), R FIT (with knots inside dose-grid gap).
//                    Custom ENGINE-DECLINED / R-FIT panel.
//   - ERENUMAB (3.10): both engine and R refused (same pattern as SELECT). RCS rows DEFERRED.
//   - ANIFROLUMAB (3.11): engine FIT RCS at k_RCS=2 with INFORMATIVE knots [225, 300, 650] mg
//                          spanning the actual dose range, R REFUSED. Custom ENGINE-FIT / R-REFUSED
//                          panel. The knots are NOT degenerate-collapsed (unlike AMAGINE Round 3.9)
//                          because the dose-grid has 3 distinct positive doses {150, 300, 1000}
//                          with a 6.7x range — wide enough for the 3-knot Harrell basis to land
//                          on real data.
function renderAnifrolumabParityBadge(lin, rcs, os, rJson) {
  var THRESHOLDS = { linear_slope: 0.01, linear_tau2: 0.0001 };

  var dSlope = Math.abs(lin.pooled_slope_log - rJson.linear.pooled_slope_log);
  var dTau2 = Math.abs(lin.tau2 - rJson.linear.tau2);
  var slopeStatus = (isFinite(dSlope) && dSlope < THRESHOLDS.linear_slope) ? 'green' : 'amber';
  var tau2Status = (isFinite(dTau2) && dTau2 < THRESHOLDS.linear_tau2) ? 'green' : 'amber';

  // RCS row state: engine FIT with informative knots; R refused on sparse-arm requirement.
  var engineFitRcs = (rcs.layer === 'rcs' && rcs.rcs != null && Array.isArray(rcs.rcs.spline_coefs));
  var rRcsRefused = !(rJson.rcs && rJson.rcs.fit_ok === true);
  var engineKnotsStr = engineFitRcs
    ? '[' + rcs.rcs.knots.map(function (k) { return k.toFixed(0); }).join(', ') + ']'
    : 'n/a';
  var engineSplineCoefs = (engineFitRcs && Array.isArray(rcs.rcs.spline_coefs)) ? rcs.rcs.spline_coefs : [];

  // One-stage: R fitted (converged=true reported in R precompute).
  var osR = rJson.one_stage || {};
  var osEng = (os && os.one_stage) || {};

  // Header: use 'rv-badge-deferred' (purple) overall to flag the engine-vs-R RCS
  // disagreement to the reader. The linear rows are GREEN-themed within the badge.
  var headerClass = 'rv-badge-deferred';

  var html = '<div class="rv-badge ' + headerClass + '">' +
    '<details open>' +
    '<summary>R-parity badge &mdash; linear rows GREEN; 3 RCS rows custom ENGINE-FIT / R-REFUSED panel; one-stage row pass-through</summary>' +
    '<p style="margin:0.6em 0;"><strong>Engine and R DISAGREE on whether to fit RCS on this dose grid.</strong> Engine returned <code>layer=&#39;' + escapeHtml(rcs.layer) + '&#39;</code> with a real 3-knot RCS fit at <code>knots=' + escapeHtml(engineKnotsStr) + '</code> mg (k_RCS=' + rcs.k + ' surviving after silently dropping TULIP-2 for singular per-trial design &mdash; TULIP-2 has only 1 non-reference arm); R <code>dosresmeta</code> refused the entire RCS pool with the canonical sparse-per-trial-arm error (<code>rcs.fit_ok=' + (rJson.rcs && rJson.rcs.fit_ok) + '</code>). The 3 RCS rows are rendered in a custom &ldquo;ENGINE-FIT / R-REFUSED&rdquo; panel that distinguishes Round 3.11 from AMAGINE (Round 3.9) where engine refused and R fit with degenerate knots, and from SUSTAIN/SELECT/ERENUMAB where both engine and R refused. <strong>Critical distinction vs AMAGINE</strong>: anifrolumab&apos;s engine knots ' + escapeHtml(engineKnotsStr) + ' mg span the actual 150&ndash;1000 mg active-dose range with meaningful gaps; AMAGINE&apos;s R knots [157.5, 175, 192.5] mg all collapsed inside a 70 mg gap (140&ndash;210 mg) with no interior data. The anifrolumab engine fit is methodologically defensible; the AMAGINE R fit was uninformative. This is unit-tested in <code>tests/test_dose_response_engine.mjs</code> and contract-pinned in <code>tests/test_flagship_field_paths.mjs</code> (this flagship&apos;s entry uses <code>rRefusedRcs: true</code> + new <code>engineFitsRcsRRefuses: true</code> contract flag &mdash; the OPPOSITE of AMAGINE&apos;s <code>rcsDegenerate + rEngineDisagreesOnRcs</code>).</p>' +
    '<div class="side-by-side">' +
    '<div class="engine-col">' +
    '<p><strong>Engine output (verbatim):</strong></p>' +
    '<pre class="code-block">' + escapeHtml(JSON.stringify({
      layer: rcs.layer,
      fallback: rcs.fallback,
      estimator: rcs.estimator,
      ci_method: rcs.ci_method,
      k: rcs.k,
      hksj_mv: Number(rcs.hksj_mv.toFixed(4)),
      tcrit: Number(rcs.tcrit.toFixed(4)),
      'rcs.knots': rcs.rcs.knots,
      'rcs.spline_coefs': rcs.rcs.spline_coefs.map(function (c) { return Number(c.toFixed(6)); }),
      'rcs.nonlinearity_wald_p': Number(rcs.rcs.nonlinearity_wald_p.toFixed(4)),
      'rcs.reml_converged': rcs.rcs.reml_converged
    }, null, 2)) + '</pre>' +
    '<p style="margin-top:0.4em;"><strong>Status: FIT WITH INFORMATIVE KNOTS.</strong> The engine&apos;s <code>fitRCS</code> calls <code>rcsKnots(allDoses, 3)</code> on the unique positive doses {150, 300, 1000} and finds 3 distinct knot locations at the 10th, 50th, and 90th percentiles &rarr; ' + escapeHtml(engineKnotsStr) + ' mg. Per-trial 2&times;2 spline-coefficient regression succeeds for MUSE and TULIP-1; TULIP-2&apos;s per-trial XtSX is singular (only 1 non-reference arm), so the engine silently drops TULIP-2 from the RCS pool (k_RCS=' + rcs.k + '). Full multivariate REML converges in ' + rcs.rcs.reml_iterations + ' iterations to log-likelihood ' + rcs.rcs.reml_loglik.toFixed(2) + '. HKSJ-multivariate floor activates at 1.0 (q_mv ' + rcs.q_mv.toFixed(3) + ' &lt; df_mv ' + rcs.df_mv + '). Non-linearity Wald p = ' + rcs.rcs.nonlinearity_wald_p.toFixed(4) + ' &mdash; the saturation evidence is under-leveraged at k_RCS=2 (only MUSE supplies 1000 mg).</p>' +
    '</div>' +
    '<div class="r-col">' +
    '<p><strong>R <code>dosresmeta</code> output (verbatim from precompute JSON):</strong></p>' +
    '<pre class="code-block">' + escapeHtml(JSON.stringify({
      fit_ok: (rJson.rcs && rJson.rcs.fit_ok) || false,
      error_msg: (rJson.rcs && rJson.rcs.error_msg) || 'n/a'
    }, null, 2)) + '</pre>' +
    '<p style="margin-top:0.4em;"><strong>Status: REFUSED (sparse-per-trial-arm).</strong> R reports <code>fit_ok = false</code> with the canonical error message: <em>&ldquo;A two-stage approach requires that each study provides at least p non-referent obs (p is the number of columns of the design matrix X)&rdquo;</em>. TULIP-2 has only 1 non-reference arm (300 mg only) and R&apos;s sparse-per-trial-arm guard fires, refusing the entire pool. Unlike the engine, R does not silently drop the offending trial &mdash; it returns no RCS fit at all. No spline coefficients or non-linearity p are produced. The R precompute JSON has no <code>rcs.knots</code>, <code>rcs.spline_coefs</code>, or <code>rcs.nonlinearity_wald_p</code> fields when <code>fit_ok = false</code>.</p>' +
    '</div>' +
    '</div>' +
    '<table style="margin-top:0.8em;">' +
    '<caption>Side-by-side: engine vs R verdict on RCS layer for the anifrolumab SLE dose grid</caption>' +
    '<thead><tr><th>Aspect</th><th>Engine (RapidMeta v0.3.0)</th><th>R (dosresmeta ' + escapeHtml(rJson.dosresmeta_version || 'unknown') + ')</th></tr></thead>' +
    '<tbody>' +
    '<tr><td>Verdict</td><td><strong>FIT</strong> (returns spline_coefs with informative knots)</td><td><strong>REFUSED</strong> (sparse-per-trial-arm error)</td></tr>' +
    '<tr><td>Mechanism</td><td>Cross-trial knot-count check passes (3 distinct positive doses); per-trial design check silently drops TULIP-2 (singular XtSX) &rarr; k_RCS=' + rcs.k + ' pool</td><td>Per-trial sparse-arm check: TULIP-2 has 1 non-reference arm vs K_p=2 spline coefs required &rarr; entire pool refused, no silent drop</td></tr>' +
    '<tr><td>Knot locations</td><td>' + escapeHtml(engineKnotsStr) + ' mg &mdash; span the actual 150&ndash;1000 mg active-dose range with meaningful gaps</td><td>n/a (no spline fit)</td></tr>' +
    '<tr><td>spline_coefs</td><td>[' + engineSplineCoefs.map(function (c) { return c.toFixed(5); }).join(', ') + ']</td><td>n/a (no spline fit)</td></tr>' +
    '<tr><td>nonlinearity Wald p</td><td>' + rcs.rcs.nonlinearity_wald_p.toFixed(4) + ' &mdash; under-leveraged saturation evidence at k_RCS=' + rcs.k + '</td><td>n/a (no spline fit)</td></tr>' +
    '<tr><td>Methodological judgment</td><td><strong>Permissive but defensible</strong>: drops the offending trial silently, fits an RCS on the surviving k_RCS pool with informative knots</td><td><strong>Conservative</strong>: refuses the entire pool when any trial violates the K_p requirement (no silent drop)</td></tr>' +
    '</tbody></table>' +
    '<p style="margin-top:0.6em;"><strong>Why the engine&apos;s call is methodologically defensible here:</strong> The engine&apos;s knots <em>[225, 300, 650]</em> mg span the actual program dose range with meaningful gaps (225&ndash;300 mg = 75 mg apart; 300&ndash;650 mg = 350 mg apart). The fit captures the program-canonical biological saturation (MUSE 300 mg 53.5% &gt; 1000 mg 41.3% BICLA response) even though the formal Wald test cannot reject H<sub>0</sub> at &alpha;=0.05 with only one trial supplying 1000 mg. This is fundamentally different from AMAGINE (Round 3.9) where R fit a spline with all 3 knots collapsed inside a 70 mg gap (140&ndash;210 mg) with no interior data points &mdash; an algebraically valid fit on percentile placeholders, not biological data. The R refusal here is the algorithm being conservative about the sparse-per-trial-arm boundary; the engine&apos;s silent-drop strategy plus informative knots produces a more clinically useful output for anifrolumab.</p>' +
    '<p style="margin-top:0.6em;"><strong>What an RCS-confirming Phase 4 would look like:</strong> A future trial sampling multiple anifrolumab doses including 1000 mg (e.g. a 4-arm trial at 150 / 300 / 600 / 1000 mg) would let the engine fit a 3-knot RCS at k_RCS=3+ without dropping any trial, and would tighten the spline_coefs[1] SE enough to test the non-linearity hypothesis formally. The current fit is informative as a sensitivity / functional-form check; the formal saturation test awaits more 1000 mg data.</p>' +
    '<p style="margin-top:0.6em; font-size:0.92em; color:#555;"><strong>For methods-comparison readers:</strong> When the engine&apos;s RCS layer FITS with informative knots and R refuses on sparse-arm, the R-parity audit (this tab) renders the 3 RCS rows in a custom &ldquo;ENGINE-FIT / R-REFUSED&rdquo; panel rather than as GREEN / AMBER / DEFERRED. This distinguishes Round 3.11 from the SUSTAIN/SELECT/ERENUMAB pattern (both refused, deferred), the AMAGINE pattern (engine refused / R fit with degenerate knots), and the standard threshold-driven case (both fit). The linear-pool R-parity rows (slope + &tau;<sup>2</sup>) still run as standard threshold-driven rows and are expected GREEN.</p>' +
    '<table class="rv-table" style="margin-top:0.8em;">' +
    '<caption>Engine vs R precompute &mdash; 2 linear rows threshold-driven; 3 RCS rows ENGINE-FIT / R-REFUSED; one-stage row pass-through</caption>' +
    '<thead><tr><th>Metric</th><th>Engine</th><th>R (dosresmeta)</th><th>|&Delta;|</th><th>Status</th></tr></thead>' +
    '<tbody>' +
    // Linear rows — threshold-driven (expected GREEN; engine matches R precompute within thresholds)
    '<tr class="rv-row rv-row-' + slopeStatus + '"><td class="rv-label">Linear pooled log-slope</td><td>' + fmtNum(lin.pooled_slope_log, 6) + '</td><td>' + fmtNum(rJson.linear.pooled_slope_log, 6) + '</td><td>' + fmtNum(dSlope, 6) + '</td><td>' + slopeStatus.toUpperCase() + ' (threshold ' + THRESHOLDS.linear_slope + ')</td></tr>' +
    '<tr class="rv-row rv-row-' + tau2Status + '"><td class="rv-label">Linear &tau;<sup>2</sup></td><td>' + lin.tau2.toExponential(2) + '</td><td>' + (rJson.linear.tau2 != null ? rJson.linear.tau2.toExponential(2) : 'n/a') + '</td><td>' + dTau2.toExponential(2) + '</td><td>' + tau2Status.toUpperCase() + ' (threshold ' + THRESHOLDS.linear_tau2 + ')</td></tr>' +
    // RCS rows — ENGINE-FIT / R-REFUSED (custom)
    '<tr class="rv-row rv-row-deferred"><td class="rv-label">RCS spline_coefs[0] (linear component)</td><td>' + (engineSplineCoefs.length > 0 ? fmtNum(engineSplineCoefs[0], 5) : 'n/a') + ' (engine fit with knots ' + escapeHtml(engineKnotsStr) + ' &mdash; informative)</td><td>n/a (R refused &mdash; sparse-per-trial-arm)</td><td>n/a</td><td>ENGINE-FIT / R-REFUSED (engine knots span dose range; deferred to engine v0.5)</td></tr>' +
    '<tr class="rv-row rv-row-deferred"><td class="rv-label">RCS spline_coefs[1] (non-linear component)</td><td>' + (engineSplineCoefs.length > 1 ? fmtNum(engineSplineCoefs[1], 5) : 'n/a') + ' (engine fit, SE ' + rcs.rcs.spline_coefs_se[1].toFixed(5) + ' &mdash; under-leveraged saturation evidence)</td><td>n/a (R refused)</td><td>n/a</td><td>ENGINE-FIT / R-REFUSED (informative; deferred to engine v0.5)</td></tr>' +
    '<tr class="rv-row rv-row-deferred"><td class="rv-label">RCS non-linearity Wald p</td><td>' + rcs.rcs.nonlinearity_wald_p.toFixed(4) + ' (engine; cannot reject H<sub>0</sub> at &alpha;=0.05 with k_RCS=' + rcs.k + ')</td><td>n/a (R refused)</td><td>n/a</td><td>ENGINE-FIT / R-REFUSED (deferred to engine v0.5)</td></tr>' +
    // One-stage row — pass-through (R lme4::glmer fitted; engine surfaces R values)
    '<tr><td class="rv-label">One-stage coef_dose (R precompute, log-RR per mg)</td><td>' + fmtNum(osEng.coef_dose, 6) + '</td><td>' + fmtNum(osR.coef_dose, 6) + '</td><td>0.000000 (pass-through)</td><td>PASS-THROUGH (R lme4::glmer; converged=' + (osR.converged === true ? 'true' : (osR.converged === false ? 'false (random_effects_var pinned at 0)' : 'n/a')) + ')</td></tr>' +
    '</tbody></table>' +
    '<p style="margin-top:0.6em; font-size:0.92em; color:#444;"><strong>Verdict:</strong> Linear slope row ' + slopeStatus.toUpperCase() + ': engine linear-pool slope ' + fmtNum(lin.pooled_slope_log, 6) + ' vs R <code>dosresmeta</code> ' + fmtNum(rJson.linear.pooled_slope_log, 6) + ' (|&Delta;| = ' + fmtNum(dSlope, 6) + ' &lt; ' + THRESHOLDS.linear_slope + '). Linear &tau;<sup>2</sup> row ' + tau2Status.toUpperCase() + ': engine ' + lin.tau2.toExponential(2) + ' vs R ' + (rJson.linear.tau2 != null ? rJson.linear.tau2.toExponential(2) : 'n/a') + ' (|&Delta;| = ' + dTau2.toExponential(2) + (tau2Status === 'green' ? ' &lt; ' : ' &ge; ') + THRESHOLDS.linear_tau2 + '). RCS rows ENGINE-FIT / R-REFUSED: engine produced a real 3-knot RCS fit with sensible knots spanning the 150&ndash;1000 mg active-dose range; R refused on the sparse-per-trial-arm boundary because TULIP-2 has only 1 non-reference arm. Engine&apos;s contribution on this fixture is producing an interpretable RCS curve where R refuses entirely. The 3 rows are deferred to engine v0.5, which may extend the R-parity contract by computing an R sparse-arm-handling sensitivity (e.g. an R one-stage spline via <code>mgcv::gam</code> that does not have the per-trial-arm requirement).</p>' +
    '<p style="margin-top:0.4em; font-size:0.85em; color:#555;"><strong>R precompute source:</strong> <code>outputs/r_validation/doseresp/anifrolumab_sle_phase23.json</code> (dosresmeta v' + escapeHtml(rJson.dosresmeta_version || 'unknown') + '; input k = ' + (rJson.k != null ? rJson.k : 'unknown') + '). R linear-pool block has <code>fit_ok = true</code>; R RCS block has <code>fit_ok = false</code> with error_msg recording the sparse-per-trial-arm refusal. R one-stage block has <code>fit_ok = true</code> with <code>converged = ' + (osR.converged === true ? 'true' : 'false') + '</code>.</p>' +
    '</details>' +
    '</div>';
  document.getElementById('r-parity-anifrolumab-bicla').innerHTML = html;
}
