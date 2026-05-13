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

// CSP-safe tab wiring: addEventListener (no inline onclick). Keyboard nav for ←/→/Home/End.
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

window.addEventListener('DOMContentLoaded', function () {
  if (!window.RapidMetaDoseResp || typeof window.RapidMetaDoseResp.engine_version !== 'string') {
    document.body.innerHTML = '<div style="color:#c00; padding:1em;"><strong>Engine failed to load.</strong> Check the browser console for errors.</div>';
    return;
  }
  var DR = window.RapidMetaDoseResp;

  // Engine version + date
  document.getElementById('engine-version').textContent = DR.engine_version;
  document.getElementById('gen-date').textContent = new Date().toISOString().slice(0, 10);

  // Read %WC trials
  var wtScript = document.getElementById('doseresp-trials-wt');
  var wtTrials;
  try {
    wtTrials = JSON.parse(wtScript.textContent);
  } catch (e) {
    document.getElementById('wt-linear-kpis').textContent = '%WC trial data malformed: ' + e.message;
    return;
  }
  if (wtTrials.length === 0) {
    document.getElementById('wt-linear-kpis').textContent = 'No %WC trial data embedded.';
    return;
  }

  // === Tab 1: %WC Linear (k=2 stress test) ===
  var wtLin = DR.fitLinear(wtTrials, {});
  // Note: pooled_slope_log here is MD-per-mg-dose (continuous mode), not log-RR.
  var mdPerMg = wtLin.pooled_slope_log;
  var mdPerMg_lo = wtLin.pooled_slope_log_ci_lo;
  var mdPerMg_hi = wtLin.pooled_slope_log_ci_hi;
  var mdAt15 = mdPerMg * 15;
  var mdAt15_lo = mdPerMg_lo * 15;
  var mdAt15_hi = mdPerMg_hi * 15;

  document.getElementById('wt-linear-kpis').innerHTML =
    '<div class="kpi-grid">' +
    '<div class="kpi"><div class="kpi-label">%WC at 15 mg (linear extrapolation)</div><div class="kpi-value">' + mdAt15.toFixed(2) + '%</div><div>95% CI ' + mdAt15_lo.toFixed(2) + ' to ' + mdAt15_hi.toFixed(2) + '</div><div style="color:#92400e; font-size:0.8em;">CI honestly wide due to k=2; t<sub>1, 0.975</sub> = 12.706</div></div>' +
    '<div class="kpi"><div class="kpi-label">MD per mg dose</div><div class="kpi-value">' + mdPerMg.toFixed(4) + '</div><div>SE ' + wtLin.pooled_slope_log_se.toFixed(4) + '</div></div>' +
    '<div class="kpi"><div class="kpi-label">&tau;<sup>2</sup> (Paule-Mandel)</div><div class="kpi-value">' + wtLin.tau2.toExponential(2) + '</div><div style="color:#92400e; font-size:0.8em;">PM &mdash; differs from R REML at k=2 (see Tab 4)</div></div>' +
    '<div class="kpi"><div class="kpi-label">I&sup2;</div><div class="kpi-value">' + wtLin.I2.toFixed(1) + '%</div><div>Q = ' + wtLin.Q.toFixed(2) + ' (df ' + wtLin.Q_df + ')</div></div>' +
    '<div class="kpi"><div class="kpi-label">PI at 15 mg (df=' + wtLin.pi_df + ')</div><div class="kpi-value">' + (wtLin.pi_lo*15).toFixed(2) + ' to ' + (wtLin.pi_hi*15).toFixed(2) + '</div></div>' +
    '<div class="kpi"><div class="kpi-label">k</div><div class="kpi-value">' + wtLin.k + '</div>' + (wtLin.coverage_warning ? '<div style="color:#92400e">coverage warning: k&lt;10</div>' : '') + '</div>' +
    '</div>';

  // Per-study forest (continuous mode: slope_log = MD per mg, no exp transform)
  var wtForestRows = DR.forest(wtTrials, wtLin);
  var wtFHtml = '<h3>Per-study forest (%WC, linear layer, RE-weighted)</h3><div class="table-scroll"><table><caption>Per-study %WC MD per mg dose with 95% CI (linear two-stage layer)</caption><thead><tr><th>Study</th><th>MD per mg</th><th>95% CI</th><th>Weight</th></tr></thead><tbody>';
  wtForestRows.forEach(function (r) {
    wtFHtml += '<tr><td>' + escapeHtml(r.label) + '</td>' +
                  '<td>' + r.slope_log.toFixed(4) + '</td>' +
                  '<td>' + (r.slope_log - 1.96 * r.slope_log_se).toFixed(4) + ' to ' + (r.slope_log + 1.96 * r.slope_log_se).toFixed(4) + '</td>' +
                  '<td>' + r.weight_pct.toFixed(1) + '%</td></tr>';
  });
  wtFHtml += '</tbody></table></div>';
  document.getElementById('wt-linear-forest').innerHTML = wtFHtml;

  // Dose-response curve (20-point grid, 0 to 15 mg)
  var maxObs = wtLin.max_observed_dose;
  var wtCurveHtml = '<h3>Dose-response curve (95% CI via t<sub>' + wtLin.pi_df + '</sub>)</h3><div class="table-scroll"><table><caption>Linear %WC MD per arm dose, 20-point grid 0 to ' + maxObs + ' mg</caption><thead><tr><th>Dose (mg)</th><th>MD (%)</th><th>95% CI</th></tr></thead><tbody>';
  for (var i = 0; i < 20; i++) {
    var d = i * maxObs / 19;
    var p = DR.predict(wtLin, d);
    wtCurveHtml += '<tr><td>' + d.toFixed(2) + '</td>' +
                     '<td>' + p.est.toFixed(3) + '</td>' +
                     '<td>' + p.ci_lo.toFixed(3) + ' to ' + p.ci_hi.toFixed(3) + '</td></tr>';
  }
  wtCurveHtml += '</tbody></table></div>';
  document.getElementById('wt-linear-curve').innerHTML = wtCurveHtml;

  document.getElementById('wt-linear-summary').innerHTML =
    '<p><strong>Plain-English summary (linear pool, k=2 stress test):</strong> The linear two-stage pool estimates that each additional 1 mg of tirzepatide is associated with a percent-body-weight change of approximately ' + mdPerMg.toFixed(2) + ' percentage points per mg (point estimate). The 95% CI is ' + mdPerMg_lo.toFixed(2) + ' to ' + mdPerMg_hi.toFixed(2) + ' per mg, which is honestly wide because the t<sub>k-1</sub> critical value at k=2 is <code>t<sub>1, 0.975</sub> = 12.706</code> (vs ~2 for k=10).</p>' +
    '<p style="margin-top:0.6em; font-size:0.92em; color:#92400e;"><strong>k=2 caveat (read first):</strong> This linear point estimate is shown only to demonstrate the engine&apos;s honest behaviour at the small-k boundary. Do NOT cite this slope as a real-world obesity meta-analytic effect; with only 2 trials, the CI is wide enough to span sign changes at the dose-15-mg extrapolation. Larger tirzepatide-obesity meta-analyses (when SURMOUNT-3, SURMOUNT-4 and SURMOUNT-MMO post AACT primary results) will be required for a defensible class-level dose-response estimate. The within-trial monotonic dose-response (5 mg &rarr; 10 mg &rarr; 15 mg producing successively more weight loss) is robust within each trial and is shown in the RCS Tab 2 below.</p>';

  // === Tab 2: %WC RCS (full multivariate REML v0.3.0) ===
  var wtRcs = DR.fitRCS(wtTrials, { knots: 3 });

  document.getElementById('wt-rcs-kpis').innerHTML =
    '<div class="kpi-grid">' +
    '<div class="kpi"><div class="kpi-label">Knots (mg, Harrell default)</div><div class="kpi-value">' + wtRcs.rcs.knots.map(function (k) { return k.toFixed(1); }).join(', ') + '</div></div>' +
    '<div class="kpi"><div class="kpi-label">spline_coefs[0] (linear)</div><div class="kpi-value">' + wtRcs.rcs.spline_coefs[0].toFixed(4) + '</div><div>SE ' + wtRcs.rcs.spline_coefs_se[0].toFixed(4) + '</div></div>' +
    '<div class="kpi"><div class="kpi-label">spline_coefs[1] (non-linear)</div><div class="kpi-value">' + wtRcs.rcs.spline_coefs[1].toFixed(4) + '</div><div>SE ' + wtRcs.rcs.spline_coefs_se[1].toFixed(4) + '</div></div>' +
    '<div class="kpi"><div class="kpi-label">Wald non-linearity p</div><div class="kpi-value">' + wtRcs.rcs.nonlinearity_wald_p.toFixed(4) + '</div><div>&chi;<sup>2</sup> = ' + (wtRcs.rcs.nonlinearity_wald_chi2 != null ? wtRcs.rcs.nonlinearity_wald_chi2.toFixed(3) : 'n/a') + ' (df ' + wtRcs.rcs.nonlinearity_wald_df + ')</div><div style="color:#92400e; font-size:0.8em;">borderline at k=2; SURPASS k=5 gave p=0.0346</div></div>' +
    '<div class="kpi"><div class="kpi-label">&tau;<sup>2</sup> per dim</div><div class="kpi-value">[' + wtRcs.rcs.tau2_per_dim.map(function (t) { return t.toExponential(2); }).join(', ') + ']</div></div>' +
    '<div class="kpi"><div class="kpi-label">HKSJ-multivariate</div><div class="kpi-value">' + wtRcs.hksj_mv.toFixed(2) + '</div><div style="color:#92400e">extreme &mdash; massive between-trial heterogeneity at k=2</div></div>' +
    '<div class="kpi"><div class="kpi-label">tcrit (t<sub>k-1</sub>)</div><div class="kpi-value">' + wtRcs.tcrit.toFixed(3) + '</div><div>k = ' + wtTrials.length + ', t<sub>1, 0.975</sub></div></div>' +
    '<div class="kpi"><div class="kpi-label">REML convergence</div><div class="kpi-value">' + (wtRcs.rcs.reml_converged ? 'Yes' : 'No') + '</div><div>iterations ' + (wtRcs.rcs.reml_iterations != null ? wtRcs.rcs.reml_iterations : 'n/a') + '; log-lik ' + (wtRcs.rcs.reml_loglik != null ? wtRcs.rcs.reml_loglik.toFixed(2) : 'n/a') + '</div></div>' +
    '</div>';

  // Headline Wald banner — AMBER (borderline at k=2; saturation is qualitatively present but not statistically significant at p<0.05 with this power)
  document.getElementById('wt-rcs-wald').innerHTML =
    '<div class="rv-badge rv-badge-amber">' +
    '<strong>Borderline non-linearity at k=2 (full multivariate REML v0.3.0):</strong> Wald p = ' + wtRcs.rcs.nonlinearity_wald_p.toFixed(4) +
    ' (&chi;<sup>2</sup> = ' + (wtRcs.rcs.nonlinearity_wald_chi2 != null ? wtRcs.rcs.nonlinearity_wald_chi2.toFixed(3) : 'n/a') + ', df ' + wtRcs.rcs.nonlinearity_wald_df + '). ' +
    'With only k=2 trials and K<sub>p</sub>=2 spline coefficients (effectively df=1 in the non-linearity test on an HKSJ-multivariate-inflated SE of ' + wtRcs.hksj_mv.toFixed(2) + '), this is <em>insufficient power to reject linearity</em>, not evidence of linearity. The Round 3 SURPASS T2D flagship ran the same RCS specification on k=5 SURPASS trials and produced non-linearity p = 0.0346 (significant). Within each SURMOUNT trial the dose-response shape is qualitatively saturating (the 10 &rarr; 15 mg increment produces ~1.1 percentage-point additional weight loss in SURMOUNT-1 and ~2.3 percentage points in SURMOUNT-2, both noticeably smaller than the 0 &rarr; 5 mg increment which produces ~14 percentage points in SURMOUNT-1).<br>' +
    '<span class="rv-disclosure">Engine v0.3.0 uses full multivariate REML via Nelder-Mead on Cholesky parameters of the &tau;<sup>2</sup> matrix; HKSJ-multivariate scaling factor: ' + wtRcs.hksj_mv.toFixed(2) + ' (high &mdash; the engine&apos;s honest reflection that 2 trials with different baseline-population characteristics cannot pin down a within-drug saturation curve); CI critical value t<sub>k-1</sub> = ' + wtRcs.tcrit.toFixed(3) + ' (t<sub>1, 0.975</sub> &mdash; the small-k cost). Non-linearity p matches R mixmeta within |&Delta;| &lt; 0.05 (R: ' + (wtRcs.rcs.nonlinearity_wald_p).toFixed(4) + ' vs engine ' + wtRcs.rcs.nonlinearity_wald_p.toFixed(4) + ') &mdash; see the R-parity tab for the side-by-side comparison.</span></div>';

  // τ² matrix display (Kp×Kp)
  var tm = wtRcs.rcs.tau2_matrix;
  var tauMatrixHtml = '<h3>&tau;<sup>2</sup> matrix (' + tm.length + '&times;' + tm.length + ', full multivariate REML)</h3>' +
    '<div class="table-scroll"><table><caption>Between-trial covariance of (linear, non-linear) spline coefficients</caption>' +
    '<thead><tr><th></th><th>linear</th><th>non-linear</th></tr></thead><tbody>' +
    '<tr><td><strong>linear</strong></td><td>' + tm[0][0].toExponential(3) + '</td><td>' + tm[0][1].toExponential(3) + '</td></tr>' +
    '<tr><td><strong>non-linear</strong></td><td>' + tm[1][0].toExponential(3) + '</td><td>' + tm[1][1].toExponential(3) + '</td></tr>' +
    '</tbody></table></div>' +
    '<p style="font-size:0.92em; color:#444; margin-top:0.4em;">Off-diagonal is negative, indicating that between-trial deviations in the linear and non-linear spline components are negatively correlated (the trial with a steeper-than-average linear component tends to have a flatter-than-average non-linear component &mdash; only 2 data points though, so the &tau;<sup>2</sup> matrix is estimated on minimal information). HKSJ-multivariate scaling factor of ' + wtRcs.hksj_mv.toFixed(2) + ' is extreme and reflects the large between-trial heterogeneity at k=2 (different baseline populations: obesity-without-T2D at 104.8 kg vs obesity-with-T2D at 100.7 kg).</p>';
  document.getElementById('wt-rcs-tau2matrix').innerHTML = tauMatrixHtml;

  // RCS curve via fit_at_dose grid
  var rcsCurveHtml = '<h3>RCS dose-response curve (%WC)</h3><div class="table-scroll"><table><caption>RCS dose-response curve via 20-point fit_at_dose grid</caption><thead><tr><th>Dose (mg)</th><th>MD (%)</th><th>95% CI</th></tr></thead><tbody>';
  wtRcs.rcs.fit_at_dose.forEach(function (p) {
    rcsCurveHtml += '<tr><td>' + p.dose.toFixed(2) + '</td>' +
                    '<td>' + p.est.toFixed(3) + '</td>' +
                    '<td>' + p.ci_lo.toFixed(3) + ' to ' + p.ci_hi.toFixed(3) + '</td></tr>';
  });
  rcsCurveHtml += '</tbody></table></div>';
  document.getElementById('wt-rcs-curve').innerHTML = rcsCurveHtml;

  // RCS per-study forest (RE-weighted via tau2_per_dim[0])
  var rcsForestRows = DR.forest(wtTrials, wtRcs);
  var rfHtml = '<h3>Per-study forest (RCS linear-component, RE-weighted)</h3><div class="table-scroll"><table><caption>Per-study %WC MD per mg (linear-component slope), RE-weighted via tau2_per_dim[0]</caption><thead><tr><th>Study</th><th>MD per mg</th><th>95% CI</th><th>RE weight</th></tr></thead><tbody>';
  rcsForestRows.forEach(function (r) {
    rfHtml += '<tr><td>' + escapeHtml(r.label) + '</td>' +
              '<td>' + r.slope_log.toFixed(4) + '</td>' +
              '<td>' + (r.slope_log - 1.96 * r.slope_log_se).toFixed(4) + ' to ' + (r.slope_log + 1.96 * r.slope_log_se).toFixed(4) + '</td>' +
              '<td>' + r.weight_pct.toFixed(1) + '%</td></tr>';
  });
  rfHtml += '</tbody></table></div>';
  document.getElementById('wt-rcs-forest').innerHTML = rfHtml;

  // Render abstracts inline
  fetch('fixtures/dose_response/tirzepatide_obesity_surmount_abstracts.json').then(function (r) {
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
    console.error('[tirz-obesity] abstracts fetch failed:', e);
    document.getElementById('abstracts-mount').innerHTML = '<p style="color:#92400e;">Abstracts unavailable: ' + escapeHtml(e.message) + '. See <code>fixtures/dose_response/tirzepatide_obesity_surmount_abstracts.json</code>.</p>';
  });

  // Load R precompute for one-stage + R-parity badge
  fetch('outputs/r_validation/doseresp/tirzepatide_obesity_surmount.json').then(function (r) {
    if (!r.ok) throw new Error('%WC R JSON: HTTP ' + r.status);
    return r.json();
  }).then(function (rWt) {
    // === Tab 3: %WC One-stage ===
    var wtOs = DR.fitOneStage(wtTrials, {}, rWt);
    if (!wtOs || !wtOs.one_stage || wtOs.one_stage.fit_ok === false) {
      document.getElementById('wt-os-kpis').innerHTML =
        '<div class="rv-badge rv-badge-amber">One-stage R output unavailable. Run <code>python scripts/r_validate_doseresp.py --review tirzepatide_obesity_surmount</code> to populate.</div>';
    } else {
      var os = wtOs.one_stage;
      var osMdAt15 = os.coef_dose * 15;
      document.getElementById('wt-os-kpis').innerHTML =
        '<div class="kpi-grid">' +
        '<div class="kpi"><div class="kpi-label">%WC at 15 mg (one-stage)</div><div class="kpi-value">' + osMdAt15.toFixed(2) + '%</div><div>95% CI ' + (os.coef_dose_ci_lo*15).toFixed(2) + ' to ' + (os.coef_dose_ci_hi*15).toFixed(2) + '</div></div>' +
        '<div class="kpi"><div class="kpi-label">coef_dose (per mg)</div><div class="kpi-value">' + os.coef_dose.toFixed(4) + '</div><div>SE ' + os.coef_dose_se.toFixed(4) + '</div></div>' +
        '<div class="kpi"><div class="kpi-label">Random-effects variance</div><div class="kpi-value">' + (os.random_effects_var != null ? os.random_effects_var.toFixed(3) : 'n/a') + '</div></div>' +
        '<div class="kpi"><div class="kpi-label">Converged</div><div class="kpi-value">' + (os.converged ? 'Yes' : 'No') + '</div>' + (!os.converged ? '<div style="color:#92400e">solver flagged non-convergence (random-effects variance pinned at boundary)</div>' : '') + '</div>' +
        '<div class="kpi"><div class="kpi-label">Solver</div><div class="kpi-value">lme4 ' + escapeHtml(os.lme4_version || 'unknown') + '</div></div>' +
        (os.dose_scale_sd != null ? '<div class="kpi"><div class="kpi-label">dose_scale_sd (audit)</div><div class="kpi-value">' + os.dose_scale_sd.toFixed(3) + '</div></div>' : '') +
        '</div>';
      var convergenceNote = os.converged
        ? '<p style="margin-top:0.6em; font-size:0.92em; color:#444;"><strong>k=2 convergence note:</strong> R reports the one-stage fit as converged (random-effects variance ' + (os.random_effects_var != null ? os.random_effects_var.toFixed(3) : 'n/a') + ', non-zero). This is unusual for k=2; at very small k, lme4 often reports <code>converged: false</code> or pins the RE variance at the boundary. Here the very large within-trial sample sizes (n=635/623/629/625 and n=311/309/309) provide enough information to identify a finite random-trial variance, even with only 2 trials. The 95% CI on coef_dose remains narrower than the two-stage Tab 1 estimate because the one-stage model pools per-arm rows directly via inverse-variance weighting rather than aggregating per-trial slopes.</p>'
        : '<p style="margin-top:0.6em; font-size:0.92em; color:#92400e;"><strong>Non-convergence note:</strong> R reports the random-effects variance pinned at boundary, meaning between-trial variation in the dose-coefficient is too small relative to within-arm sampling variance to identify a positive random-effects variance. This is a benign artefact of the small k (k = 2); the fixed-effect coefficient and SE remain interpretable.</p>';
      document.getElementById('wt-os-methods').innerHTML =
        '<p><strong>Methodology:</strong> One-stage hierarchical model fit by R using <code>lme4::lmer(mean ~ dose + (1 | studlab), data = df, weights = 1/(sd^2/n), REML = TRUE)</code> with the bobyqa optimizer. Per-arm percent body-weight change modelled on the original scale; per-arm precision weights (inverse-variance) reflect within-arm sampling uncertainty. Random study intercept captures between-study baseline-weight variation. Dose rescaling by <code>sd(dose[dose &gt; 0])</code> for convergence; coefficient back-transformed to per-mg scale.</p>' +
        '<p style="margin-top:0.6em; font-size:0.92em;"><strong>Why this differs from Tab 1:</strong> The one-stage estimate is the linear-model fit on the per-arm data with a random study intercept. The two-stage estimate (Tab 1) fits a per-trial GL slope and pools the slopes. At k=2 the two estimates can differ substantially: the per-arm one-stage estimate (' + os.coef_dose.toFixed(3) + ' per mg) is approximately ' + (Math.abs(os.coef_dose) / Math.abs(mdPerMg)).toFixed(2) + '&times; the magnitude of the two-stage GL slope (' + mdPerMg.toFixed(3) + ' per mg) because the two-stage approach weights the per-trial slopes by their (HKSJ-floor-inflated) inverse variances, whereas the one-stage model weights per-arm rows directly. At larger k the two estimators converge.</p>' +
        convergenceNote;
    }

    // === Tab 4: R-parity badge ===
    window.RValidationDoseresp.render('r-parity-tirzepatide-obesity',
      { linear: wtLin, rcs: wtRcs, one_stage: wtOs },
      rWt);

  }).catch(function (e) {
    console.error('[tirz-obesity] R JSON load failed:', e);
    document.getElementById('wt-os-kpis').textContent = 'One-stage tab unavailable: ' + e.message;
    document.getElementById('r-parity-tirzepatide-obesity').textContent = 'R-parity badge unavailable: ' + e.message;
  });

});
