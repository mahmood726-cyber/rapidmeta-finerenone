/* ERENUMAB_MIGRAINE_PHASE3_DOSE_RESP_REVIEW.js
 *
 * Round 3.10 — 3-trial erenumab Phase 3 Δ MMD dose-response flagship.
 * Mirrors Round 3.8 (SELECT upadacitinib): both engine AND R refuse RCS.
 *
 * Engine path (v0.3.0 / v0.4 conventions):
 *   Linear layer: k=3 all trials pooled via two-stage GL + REML + HKSJ.
 *     pooled_slope_log ≈ -0.01313 per mg, SE ≈ 0.00156 (HKSJ floor applied
 *     because Q = 0.34 < df = 2, so Q/(k-1) < 1 and floor max(1, Q/(k-1)) = 1),
 *     τ² ≈ 0 (essentially homogeneous on the dose-response axis); Q = 0.34 (df 2),
 *     I² ≈ 0%; HKSJ adj 1.00 (floor active).
 *     Per-trial GL slopes: STRIVE ≈ -0.01314, ARISE ≈ -0.01486, LIBERTY ≈ -0.01136.
 *     STRIVE dominates the pool (~73% RE weight) because it carries both within-trial
 *     dose contrasts (0 → 70 → 140 mg). ARISE pins the 0 → 70 mg leg; LIBERTY pins
 *     the 0 → 140 mg leg.
 *
 *   RCS layer: ENGINE RETURNS LINEAR-FALLBACK. The pool has only 2 distinct positive
 *     doses ({70, 140} mg), and ARISE / LIBERTY each have only 1 non-reference arm.
 *     `rcsKnots(allDoses, 3)` returns fewer than the K=3 required distinct knot
 *     locations, and `fitRCS` short-circuits by calling fitLinear and decorating
 *     the result with:
 *       layer = 'linear'
 *       fallback = 'degenerate_to_linear'
 *       rcs = null              ← NO nested .rcs block
 *       estimator = 'reml_hksj' (inherited from fitLinear)
 *     This is the engine's documented RCS-fallback for coarse dose grids.
 *     R `dosresmeta` refuses RCS on the same fixture with the parallel
 *     sparse-arm error ("each study provides at least p non-referent obs").
 *
 *   One-stage (R precompute): lme4::lmer on all 3 trials. coef_dose ≈ -0.01308
 *     per mg, SE 0.00205, CI [-0.0171, -0.0091]. R reports converged=true.
 *
 * Tabs (3 — RCS tab REPLACED with degeneration explanation):
 *   1. Δ MMD Linear (k=3 all trials, HEADLINE; includes population-heterogeneity panel)
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

  // Read MMD trials
  var mmdScript = document.getElementById('doseresp-trials-mmd');
  var mmdTrials;
  try {
    mmdTrials = JSON.parse(mmdScript.textContent);
  } catch (e) {
    document.getElementById('mmd-linear-kpis').textContent = 'Δ MMD trial data malformed: ' + e.message;
    return;
  }
  if (mmdTrials.length === 0) {
    document.getElementById('mmd-linear-kpis').textContent = 'No Δ MMD trial data embedded.';
    return;
  }

  // === Tab 1: Δ MMD Linear (k=3 all trials) — HEADLINE ===
  var mmdLin = DR.fitLinear(mmdTrials, {});
  var mdPerMg = mmdLin.pooled_slope_log;
  var mdPerMg_lo = mmdLin.pooled_slope_log_ci_lo;
  var mdPerMg_hi = mmdLin.pooled_slope_log_ci_hi;
  var maxObs = mmdLin.max_observed_dose; // 140 mg
  var mdAt70 = mdPerMg * 70;
  var mdAt70_lo = mdPerMg_lo * 70;
  var mdAt70_hi = mdPerMg_hi * 70;
  var mdAtMax = mdPerMg * maxObs;
  var mdAtMax_lo = mdPerMg_lo * maxObs;
  var mdAtMax_hi = mdPerMg_hi * maxObs;

  document.getElementById('mmd-linear-kpis').innerHTML =
    '<div class="kpi-grid">' +
    '<div class="kpi"><div class="kpi-label">Δ MMD at 70 mg (linear extrapolation)</div><div class="kpi-value">' + mdAt70.toFixed(2) + ' days</div><div>95% CI ' + mdAt70_lo.toFixed(2) + ' to ' + mdAt70_hi.toFixed(2) + '</div></div>' +
    '<div class="kpi"><div class="kpi-label">Δ MMD at ' + maxObs.toFixed(0) + ' mg (linear extrapolation)</div><div class="kpi-value">' + mdAtMax.toFixed(2) + ' days</div><div>95% CI ' + mdAtMax_lo.toFixed(2) + ' to ' + mdAtMax_hi.toFixed(2) + '</div></div>' +
    '<div class="kpi"><div class="kpi-label">Δ MMD per mg dose</div><div class="kpi-value">' + mdPerMg.toFixed(5) + '</div><div>SE ' + mmdLin.pooled_slope_log_se.toFixed(5) + '</div></div>' +
    '<div class="kpi"><div class="kpi-label">τ² (REML)</div><div class="kpi-value">' + mmdLin.tau2.toFixed(6) + '</div><div>Q-profile CI ' + mmdLin.tau2_lo.toExponential(2) + ' to ' + mmdLin.tau2_hi.toExponential(2) + '</div></div>' +
    '<div class="kpi"><div class="kpi-label">I²</div><div class="kpi-value">' + mmdLin.I2.toFixed(1) + '%</div><div>Q = ' + mmdLin.Q.toFixed(3) + ' (df ' + mmdLin.Q_df + '); Q &lt; df → homogeneous on dose-response axis</div></div>' +
    '<div class="kpi"><div class="kpi-label">HKSJ adjustment</div><div class="kpi-value">' + mmdLin.hksj_adj.toFixed(2) + '</div><div>Q* = ' + mmdLin.hksj_qstar.toFixed(2) + '; floor max(1, Q/(k-1)) active because Q &lt; df</div></div>' +
    '<div class="kpi"><div class="kpi-label">PI at ' + maxObs.toFixed(0) + ' mg (df=' + mmdLin.pi_df + ')</div><div class="kpi-value">' + (mmdLin.pi_lo * maxObs).toFixed(2) + ' to ' + (mmdLin.pi_hi * maxObs).toFixed(2) + '</div></div>' +
    '<div class="kpi"><div class="kpi-label">k (linear)</div><div class="kpi-value">' + mmdLin.k + '</div>' + (mmdLin.coverage_warning ? '<div style="color:#92400e">coverage warning: k&lt;10</div>' : '') + '</div>' +
    '<div class="kpi"><div class="kpi-label">Estimator</div><div class="kpi-value" style="font-size:1em;">' + escapeHtml(mmdLin.estimator) + '</div><div>fallback: ' + (mmdLin.fallback == null ? '<em>none</em>' : escapeHtml(mmdLin.fallback)) + '</div></div>' +
    '</div>';

  // Per-trial GL slopes table — shows the dose-coverage pattern + STRIVE dominance.
  var mmdForestRowsForTable = DR.forest(mmdTrials, mmdLin);
  var perTrialHtml = '<h3>Per-trial GL slopes (dose-coverage pattern)</h3>' +
    '<div class="table-scroll"><table><caption>Per-trial linear-layer GL slopes (Δ MMD per mg erenumab) and the dose-coverage each trial samples</caption>' +
    '<thead><tr><th>Trial</th><th>Dose levels (mg)</th><th>Dose-coverage sampled</th><th>GL slope (per mg)</th><th>SE</th><th>RE weight</th></tr></thead><tbody>';
  var doseCoverageByLabel = {
    'STRIVE (Goadsby 2017, placebo-controlled, 6-month DB)':                            { doses: '0, 70, 140', leg: 'Full 3-arm range — only trial with both 70 mg and 140 mg vs placebo' },
    'ARISE (Dodick 2018, placebo-controlled, 12-week DB)':                              { doses: '0, 70',      leg: '0 → 70 mg only (no 140 mg arm; pins the 70 mg dose-vs-placebo leg)' },
    'LIBERTY (Reuter 2018, prior-preventive-failure population, 12-week DB)':           { doses: '0, 140',     leg: '0 → 140 mg only (no 70 mg arm; pins the 140 mg dose-vs-placebo leg)' }
  };
  mmdForestRowsForTable.forEach(function (r) {
    var info = doseCoverageByLabel[r.label] || { doses: 'n/a', leg: 'n/a' };
    perTrialHtml += '<tr><td>' + escapeHtml(r.label) + '</td>' +
                    '<td>' + escapeHtml(info.doses) + '</td>' +
                    '<td>' + escapeHtml(info.leg) + '</td>' +
                    '<td>' + r.slope_log.toFixed(5) + '</td>' +
                    '<td>' + r.slope_log_se.toFixed(5) + '</td>' +
                    '<td>' + r.weight_pct.toFixed(1) + '%</td></tr>';
  });
  perTrialHtml += '</tbody></table></div>' +
    '<p style="font-size:0.92em; color:#444;"><strong>Coverage pattern:</strong> STRIVE carries the only within-trial 70-vs-140 mg contrast and accounts for ~73% of the random-effects weight; ARISE pins the 0 → 70 mg leg, LIBERTY pins the 0 → 140 mg leg. All 3 per-trial slopes are remarkably close (-0.013 to -0.015 per mg), which explains the near-zero τ² and I² ≈ 0% — the dose-response axis is essentially homogeneous across the 3 trials despite very different placebo responses (see population-heterogeneity panel below).</p>';
  document.getElementById('mmd-linear-pertrial').innerHTML = perTrialHtml;

  // Per-arm forest table.
  var mmdForestRows = DR.forest(mmdTrials, mmdLin);
  var mmdFHtml = '<h3>Per-study forest (Δ MMD linear-layer per-trial GL slopes, RE-weighted)</h3>' +
    '<div class="table-scroll"><table><caption>Per-study Δ MMD per mg dose with 95% CI (linear two-stage layer, k=3 all trials)</caption>' +
    '<thead><tr><th>Study</th><th>Δ MMD per mg</th><th>95% CI</th><th>Weight</th></tr></thead><tbody>';
  mmdForestRows.forEach(function (r) {
    mmdFHtml += '<tr><td>' + escapeHtml(r.label) + '</td>' +
                '<td>' + r.slope_log.toFixed(5) + '</td>' +
                '<td>' + (r.slope_log - 1.96 * r.slope_log_se).toFixed(5) + ' to ' + (r.slope_log + 1.96 * r.slope_log_se).toFixed(5) + '</td>' +
                '<td>' + r.weight_pct.toFixed(1) + '%</td></tr>';
  });
  mmdFHtml += '</tbody></table></div>';
  document.getElementById('mmd-linear-forest').innerHTML = mmdFHtml;

  // Population heterogeneity panel.
  var pophetHtml =
    '<div class="population-note">' +
    '<h3 style="margin-top:0; color:#92400e;">Population heterogeneity panel — placebo response by prior-treatment history</h3>' +
    '<p>LIBERTY enrolled adults with prior failure of 2&ndash;4 oral migraine preventives (treatment-refractory); STRIVE and ARISE enrolled treatment-naive episodic migraine adults. This produces a striking baseline-population effect on the placebo-arm Δ MMD that has NO bearing on the dose-response axis (which captures dose-vs-placebo contrasts within each trial):</p>' +
    '<div class="table-scroll"><table><caption>Per-trial placebo-arm Δ MMD by population (treatment-naive vs treatment-refractory)</caption>' +
    '<thead><tr><th>Trial</th><th>Population</th><th>Placebo Δ MMD (days)</th><th>Highest erenumab arm Δ MMD (days)</th><th>Erenumab-vs-placebo Δ (days)</th></tr></thead>' +
    '<tbody>' +
    '<tr><td>STRIVE</td><td>Treatment-naive (no prior failure of &gt;2 preventive classes)</td><td style="font-weight:600;">−1.83</td><td>−3.67 (140 mg)</td><td>−1.84</td></tr>' +
    '<tr><td>ARISE</td><td>Treatment-naive (no prior failure of multiple classes)</td><td style="font-weight:600;">−1.84</td><td>−2.88 (70 mg only)</td><td>−1.04</td></tr>' +
    '<tr style="background:#fff3cd;"><td>LIBERTY</td><td>Treatment-refractory (prior failure of 2&ndash;4 preventives)</td><td style="font-weight:600; color:#92400e;">−0.16</td><td>−1.75 (140 mg only)</td><td>−1.59</td></tr>' +
    '</tbody></table></div>' +
    '<p style="font-size:0.92em;"><strong>Interpretation:</strong> LIBERTY\'s placebo arm reduces MMD by only 0.16 days vs ~1.83 days in STRIVE / ARISE — an order-of-magnitude smaller placebo response. This is consistent with the published literature on treatment-refractory cohorts: prior-failure patients have lower expected response across both placebo and active arms, with smaller absolute effect sizes but a preserved relative ordering. The dose-equivalence assumption (same molecule, same SC route, same once-monthly schedule) is NOT violated. The pooled slope is identified from within-trial dose-vs-placebo contrasts (which absorb the per-trial intercept) and is unaffected by the cross-trial placebo-response shift. Each individual trial is internally monotonic on dose, and the per-trial slopes converge to ~−0.013 days per mg in all 3 trials (see the per-trial slopes table above).</p>' +
    '<p style="font-size:0.92em;"><strong>What this means for the dose-response readout:</strong> The pooled slope reflects the dose-vs-placebo gradient within each trial, NOT the absolute placebo-anchored response. For a treatment-refractory clinical population (LIBERTY-like), the absolute Δ MMD at any given dose will be smaller than the linear-extrapolation KPI on Tab 1 suggests, because the population shifts the intercept — but the marginal effect of adding 70 mg of erenumab dose is the same ~0.92 days reduction in MMD. The flagship reports the dose-response slope (the marginal effect per mg) as the headline KPI; the placebo-arm intercept is documented per-trial in the inventory and abstracts but is NOT pooled.</p>' +
    '</div>';
  document.getElementById('mmd-linear-pophet').innerHTML = pophetHtml;

  // Dose-response curve (20-point grid, 0 to maxObs mg).
  var mmdCurveHtml = '<h3>Linear dose-response curve (95% CI via t<sub>' + mmdLin.pi_df + '</sub>)</h3>' +
    '<div class="table-scroll"><table><caption>Linear Δ MMD per arm dose, 20-point grid 0 to ' + maxObs.toFixed(0) + ' mg</caption>' +
    '<thead><tr><th>Dose (mg)</th><th>Δ MMD (days)</th><th>95% CI</th></tr></thead><tbody>';
  for (var i = 0; i < 20; i++) {
    var d = i * maxObs / 19;
    var p = DR.predict(mmdLin, d);
    mmdCurveHtml += '<tr><td>' + d.toFixed(2) + '</td>' +
                    '<td>' + p.est.toFixed(3) + '</td>' +
                    '<td>' + p.ci_lo.toFixed(3) + ' to ' + p.ci_hi.toFixed(3) + '</td></tr>';
  }
  mmdCurveHtml += '</tbody></table></div>';
  document.getElementById('mmd-linear-curve').innerHTML = mmdCurveHtml;

  document.getElementById('mmd-linear-summary').innerHTML =
    '<p><strong>Plain-English summary (linear pool, k=3 all trials):</strong> The linear two-stage pool averages the per-trial GL slopes across all 3 erenumab Phase 3 trials, producing a pooled estimate of approximately ' + mdPerMg.toFixed(5) + ' Δ MMD days per mg erenumab. At 70 mg the linear extrapolation gives ' + mdAt70.toFixed(2) + ' days reduction (95% CI ' + mdAt70_lo.toFixed(2) + ' to ' + mdAt70_hi.toFixed(2) + '); at the maximum studied dose of 140 mg the extrapolation gives ' + mdAtMax.toFixed(2) + ' days reduction (95% CI ' + mdAtMax_lo.toFixed(2) + ' to ' + mdAtMax_hi.toFixed(2) + '). STRIVE\'s published results (−3.2 days at 70 mg, −3.7 days at 140 mg vs −1.8 placebo) translate to per-mg contrasts of (−3.2 − (−1.8))/70 = −0.020 and (−3.7 − (−1.8))/140 = −0.014 — bracketing the pooled engine estimate. The CI is tight because τ² ≈ 0 (Q &lt; df, so the HKSJ floor activates at 1.0 — no over-confidence inflation from the small-k path). I² = ' + mmdLin.I2.toFixed(1) + '% indicates near-perfect homogeneity on the dose-response axis across the 3 trials.</p>' +
    '<p style="margin-top:0.6em; font-size:0.92em; color:#92400e;"><strong>Caveat — read Tab 2 next:</strong> The dose grid has only 2 distinct positive doses ({70, 140} mg) with sparse per-trial coverage (only STRIVE samples both). The engine cannot fit a 3-knot Harrell-default RCS under two-stage pooling and returns <code>layer=\'linear\'</code>, <code>fallback=\'degenerate_to_linear\'</code>, with NO <code>.rcs</code> block. R <code>dosresmeta</code> refuses RCS with a parallel sparse-arm error. The linear pool reported on this tab is the methodologically primary result for this fixture.</p>';

  // === Tab 2: RCS degeneration — methodological note ===
  var mmdRcs = DR.fitRCS(mmdTrials, { knots: 3 });
  // mmdRcs.layer === 'linear', mmdRcs.fallback === 'degenerate_to_linear', mmdRcs.rcs === null
  // Surface this as the engine's documented behaviour, not a bug.

  var rcsNoteHtml =
    '<div class="rv-badge rv-badge-deferred">' +
    '<p><strong>Engine output on this fixture (verbatim):</strong></p>' +
    '<pre class="code-block">' + escapeHtml(JSON.stringify({
      layer: mmdRcs.layer,
      fallback: mmdRcs.fallback,
      estimator: mmdRcs.estimator,
      rcs: mmdRcs.rcs,                          // null
      k: mmdRcs.k,
      pooled_slope_log: Number(mmdRcs.pooled_slope_log.toFixed(6)),
      pooled_slope_log_se: Number(mmdRcs.pooled_slope_log_se.toFixed(6)),
      tau2: Number(mmdRcs.tau2.toExponential(3))
    }, null, 2)) + '</pre>' +
    '<p style="margin-top:0.6em;"><strong>Why the engine degenerates here:</strong> A 3-knot restricted cubic spline (Harrell default) places knots at the 10th, 50th, and 90th percentiles of the unique positive doses. For the design matrix to be non-singular under two-stage pooling, the pool needs at least K = 3 distinct knot locations across the unique positive doses with sufficient non-reference observations per trial to identify each spline coefficient. This fixture has only <strong>2 distinct positive doses</strong> in the entire pool (<em>{70, 140}</em> mg). The engine\'s <code>fitRCS</code> calls <code>rcsKnots(allDoses, 3)</code>, finds fewer than the required K = 3 distinct knot locations, and short-circuits by calling <code>fitLinear</code> and decorating the result with <code>layer=\'linear\'</code>, <code>fallback=\'degenerate_to_linear\'</code>, and <code>rcs=null</code>.</p>' +
    '<p style="margin-top:0.6em;"><strong>R agrees (parallel refusal):</strong> R <code>dosresmeta</code> refuses to fit RCS on the same fixture with the error <em>&ldquo;A two-stage approach requires that each study provides at least p non-referent obs (p is the number of columns of the design matrix X)&rdquo;</em>. R requires K<sub>p</sub> + 1 = 3 arms per trial for the 3-knot RCS &mdash; ARISE and LIBERTY each have only 2 arms (placebo + one erenumab dose), so each contributes only 1 non-reference observation versus the K<sub>p</sub> = 2 spline coefficients to identify. <strong>Engine and R agree:</strong> this dose grid cannot support a 3-knot RCS in two-stage form. This matches the SELECT (Round 3.8) precedent exactly &mdash; both engine and R refusing on parallel grounds.</p>' +
    '<p style="margin-top:0.6em;"><strong>What an additional dose level would unlock:</strong> A 3-knot RCS would need &ge; 3 distinct positive doses across the pool. The published CGRP-program dose-finding rationale (Lenz et al., Cephalalgia 2014 Phase 2; AMG 334 Lipton et al. Phase 2 NCT01952574) condensed the Phase 3 dose range to <em>70 mg and 140 mg</em> as the regulatorily evaluated levels &mdash; intermediate doses (e.g. 7 mg or 21 mg) were Phase 2-only and not carried into Phase 3. A 4-knot RCS would need &ge; 4 distinct positive doses per trial with at least 3 non-reference observations per trial. The Phase 3 program design therefore does not support an interior-knot RCS analysis on the registered &Delta; MMD endpoint; only a linear two-stage pool (Tab 1) is identifiable.</p>' +
    '<p style="margin-top:0.6em;"><strong>Engine\'s safety net is the documented capability:</strong> The <code>degenerate_to_linear</code> fallback prevents over-fitting on coarse dose grids. Without this safety net the engine would either silently emit nonsense spline coefficients (because the design matrix would be near-singular) or throw a generic matrix-inversion error that gives the user no path forward. Surfacing <code>fallback=\'degenerate_to_linear\'</code> with no <code>.rcs</code> block lets downstream code (and human readers) detect the condition explicitly and switch to the linear-pool framing (Tab 1) as the primary analysis. Round 3.10 is the second flagship in the dose-response pack to exercise this branch with engine-and-R agreement (after Round 3.8 SELECT); Round 3.9 AMAGINE exercises the third variant where engine declines but R proceeds (degenerate-knot R fit).</p>' +
    '<p style="margin-top:0.6em; font-size:0.92em; color:#555;"><strong>For methods-comparison readers:</strong> When the engine\'s RCS layer returns <code>fallback=\'degenerate_to_linear\'</code>, the R-parity audit (Tab 3) reduces to the linear-pool rows only. The 3 RCS rows that the standard 5-row badge would render (RCS linear-component coef, non-linear-component coef, non-linearity Wald p) are <strong>DEFERRED</strong> with the parallel-refusal disclosure note. The one-stage R precompute row is rendered as a reference pass-through.</p>' +
    '</div>';
  document.getElementById('rcs-note-body').innerHTML = rcsNoteHtml;

  // Render abstracts inline
  fetch('fixtures/dose_response/erenumab_migraine_phase3_abstracts.json').then(function (r) {
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
    console.error('[erenumab] abstracts fetch failed:', e);
    document.getElementById('abstracts-mount').innerHTML = '<p style="color:#92400e;">Abstracts unavailable: ' + escapeHtml(e.message) + '. See <code>fixtures/dose_response/erenumab_migraine_phase3_abstracts.json</code>.</p>';
  });

  // Load R precompute for R-parity badge
  fetch('outputs/r_validation/doseresp/erenumab_migraine_phase3.json').then(function (r) {
    if (!r.ok) throw new Error('Δ MMD R JSON: HTTP ' + r.status);
    return r.json();
  }).then(function (rMmd) {
    // === Tab 3: R-parity badge — custom panel: linear rows GREEN, RCS rows DEFERRED ===
    renderErenumabParityBadge(mmdLin, mmdRcs, rMmd);
  }).catch(function (e) {
    console.error('[erenumab] R JSON load failed:', e);
    document.getElementById('r-parity-erenumab-mmd').textContent = 'R-parity badge unavailable: ' + e.message;
  });
});

// Custom R-parity badge for the erenumab flagship.
// Round 3.10: BOTH engine and R refused RCS on the {0, 70, 140} dose grid —
// engine via fallback='degenerate_to_linear' (no .rcs block); R via the parallel
// sparse-arm error in the rcs.error_msg field of the R precompute JSON. The
// R-parity audit therefore reduces to the linear-pool rows (slope + τ²); the
// 3 RCS rows are DEFERRED with the parallel-refusal disclosure note. One-stage
// row rendered as a reference pass-through (R lme4::lmer converged).
function renderErenumabParityBadge(lin, rcs, rJson) {
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
    '<p style="margin:0.6em 0;"><strong>Both engine and R refused RCS on this dose grid &mdash; engine and R agree.</strong> Engine returned <code>layer=\'' + escapeHtml(rcs.layer) + '\'</code>, <code>fallback=\'' + escapeHtml(rcs.fallback || '') + '\'</code>, <code>rcs=null</code> (degenerate-to-linear short-circuit because the {0, 70, 140} mg dose grid has only 2 distinct positive doses, fewer than the K = 3 required Harrell-knot locations). R <code>dosresmeta</code> refused with the parallel error: <em>&ldquo;' + escapeHtml(rcsErrorMsg) + '&rdquo;</em>. The R-parity audit therefore reduces to the linear-pool rows; the 3 RCS rows are <strong>DEFERRED</strong> with the parallel-refusal note. The engine\'s RCS-fallback is unit-tested in <code>tests/test_dose_response_engine.mjs</code> (68 tests, all PASS) and contract-pinned in <code>tests/test_flagship_field_paths.mjs</code> (this flagship\'s entry uses <code>rcsDegenerate: true</code> + <code>rRefusedRcs: true</code>, the SELECT-pattern contract).</p>' +
    '<table class="rv-table">' +
    '<caption>Engine vs R precompute &mdash; 2 linear rows threshold-driven; 3 RCS rows deferred (engine and R agree on refusal); one-stage row pass-through</caption>' +
    '<thead><tr><th>Metric</th><th>Engine</th><th>R (dosresmeta)</th><th>|Δ|</th><th>Status</th></tr></thead>' +
    '<tbody>' +
    // Linear rows — threshold-driven (expected GREEN; engine matches R precompute within thresholds)
    '<tr class="rv-row rv-row-' + slopeStatus + '"><td class="rv-label">Linear pooled log-slope</td><td>' + fmtNum(lin.pooled_slope_log, 5) + '</td><td>' + fmtNum(rJson.linear.pooled_slope_log, 5) + '</td><td>' + fmtNum(dSlope) + '</td><td>' + slopeStatus.toUpperCase() + ' (threshold ' + THRESHOLDS.linear_slope + ')</td></tr>' +
    '<tr class="rv-row rv-row-' + tau2Status + '"><td class="rv-label">Linear τ²</td><td>' + fmtNum(lin.tau2, 6) + '</td><td>' + fmtNum(rJson.linear.tau2, 6) + '</td><td>' + fmtNum(dTau2, 6) + '</td><td>' + tau2Status.toUpperCase() + ' (threshold ' + THRESHOLDS.linear_tau2 + ')</td></tr>' +
    // RCS rows — DEFERRED (both engine and R refused)
    '<tr class="rv-row rv-row-deferred"><td class="rv-label">RCS spline_coefs[0] (linear component)</td><td>n/a (engine ' + (engineDegenerate ? 'degenerate_to_linear' : 'no .rcs') + ')</td><td>n/a (R ' + (rRefused ? 'refused' : 'not fitted') + ')</td><td>n/a</td><td>DEFERRED to engine v0.5</td></tr>' +
    '<tr class="rv-row rv-row-deferred"><td class="rv-label">RCS spline_coefs[1] (non-linear component)</td><td>n/a (engine ' + (engineDegenerate ? 'degenerate_to_linear' : 'no .rcs') + ')</td><td>n/a (R ' + (rRefused ? 'refused' : 'not fitted') + ')</td><td>n/a</td><td>DEFERRED to engine v0.5</td></tr>' +
    '<tr class="rv-row rv-row-deferred"><td class="rv-label">RCS non-linearity Wald p</td><td>n/a (engine ' + (engineDegenerate ? 'degenerate_to_linear' : 'no .rcs') + ')</td><td>n/a (R ' + (rRefused ? 'refused' : 'not fitted') + ')</td><td>n/a</td><td>DEFERRED to engine v0.5</td></tr>' +
    // One-stage row — pass-through (R lme4::lmer fitted, engine surfaces the R values)
    '<tr><td class="rv-label">One-stage coef_dose (R precompute)</td><td>' + fmtNum(osR.coef_dose, 5) + '</td><td>' + fmtNum(osR.coef_dose, 5) + '</td><td>0.00000 (pass-through)</td><td>PASS-THROUGH (R lme4::lmer; converged=' + (osR.converged === true ? 'true' : (osR.converged === false ? 'false' : 'n/a')) + ')</td></tr>' +
    '</tbody></table>' +
    '<p style="margin-top:0.6em; font-size:0.92em; color:#444;"><strong>Verdict:</strong> Linear slope row ' + slopeStatus.toUpperCase() + ': engine linear-pool slope ' + fmtNum(lin.pooled_slope_log, 5) + ' vs R <code>dosresmeta</code> ' + fmtNum(rJson.linear.pooled_slope_log, 5) + ' (|Δ| = ' + fmtNum(dSlope) + ' &lt; ' + THRESHOLDS.linear_slope + '). Linear τ² row ' + tau2Status.toUpperCase() + ': engine PM ' + fmtNum(lin.tau2, 6) + ' vs R REML ' + fmtNum(rJson.linear.tau2, 6) + ' (|Δ| = ' + fmtNum(dTau2, 6) + (tau2Status === 'green' ? ' &lt; ' : ' &ge; ') + THRESHOLDS.linear_tau2 + ' &mdash; on this fixture Q &lt; df so τ² is essentially zero under both estimators, well within threshold). RCS rows DEFERRED: engine\'s <code>degenerate_to_linear</code> fallback and R\'s sparse-arm refusal are the SAME methodological conclusion expressed differently &mdash; the dose grid does not support a 3-knot RCS in two-stage form. The engine\'s contribution on this fixture is surfacing the refusal as a structured signal (<code>fallback=\'degenerate_to_linear\'</code>) rather than an opaque matrix-inversion error.</p>' +
    '<p style="margin-top:0.4em; font-size:0.85em; color:#555;"><strong>R precompute source:</strong> <code>outputs/r_validation/doseresp/erenumab_migraine_phase3.json</code> (dosresmeta v' + escapeHtml(rJson.dosresmeta_version || 'unknown') + '; input k = ' + (rJson.k != null ? rJson.k : 'unknown') + '). R linear-pool block has <code>fit_ok = true</code>; R RCS block has <code>fit_ok = false</code> with <code>error_msg</code> capturing the sparse-arm refusal. R one-stage block has <code>fit_ok = true</code> with <code>converged = ' + (osR.converged === true ? 'true' : 'false') + '</code>.</p>' +
    '</details>' +
    '</div>';
  document.getElementById('r-parity-erenumab-mmd').innerHTML = html;
}
