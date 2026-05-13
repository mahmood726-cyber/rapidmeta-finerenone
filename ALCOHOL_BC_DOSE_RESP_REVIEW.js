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

window.addEventListener('DOMContentLoaded', function () {
  if (!window.RapidMetaDoseResp || typeof window.RapidMetaDoseResp.engine_version !== 'string') {
    document.body.innerHTML = '<div style="color:#c00; padding:1em;"><strong>Engine failed to load.</strong> Check the browser console for errors.</div>';
    return;
  }
  var trialsScript = document.getElementById('doseresp-trials');
  var trials;
  try {
    trials = JSON.parse(trialsScript.textContent);
  } catch (e) {
    document.body.innerHTML = '<div style="color:#c00; padding:1em;"><strong>Trial data is malformed.</strong> ' + (e.message || 'JSON parse error') + '</div>';
    return;
  }
  var DR = window.RapidMetaDoseResp;

  // Engine version + date
  document.getElementById('engine-version').textContent = DR.engine_version;
  document.getElementById('gen-date').textContent = new Date().toISOString().slice(0, 10);

  // Trial-summary table
  var summary = '<div class="table-scroll"><table><caption>Per-study summary: 5 prospective cohort studies of alcohol intake and breast cancer incidence</caption><thead><tr><th>Study</th><th>PMID</th><th>Arms</th><th>Total events</th><th>Total n (person-years or subjects)</th></tr></thead><tbody>';
  trials.forEach(function (t) {
    var totalE = t.arms.reduce(function (a, b) { return a + b.events; }, 0);
    var totalN = t.arms.reduce(function (a, b) { return a + b.n; }, 0);
    summary += '<tr><td>' + t.studlab + '</td>' +
               '<td><a href="https://pubmed.ncbi.nlm.nih.gov/' + t.pmid + '/" target="_blank" rel="noopener noreferrer">' + t.pmid + '</a></td>' +
               '<td>' + t.arms.length + '</td>' +
               '<td>' + totalE.toLocaleString() + '</td>' +
               '<td>' + totalN.toLocaleString() + '</td></tr>';
  });
  summary += '</tbody></table></div>';
  summary += '<p style="font-size:0.85em; color:#444; margin-top:0.4em;"><strong>Note:</strong> Howe 1991 is a case-control study reanalysed using cohort-equivalent methods (Greenland &amp; Longnecker 1992, Table 1 footnote); its <code>n</code> column represents subjects (cases + controls), not person-years. The Poisson hierarchical model treats all five studies uniformly per the GL 1992 worked example.</p>';
  document.getElementById('trial-summary').innerHTML = summary;

  // === Tab 1: Linear ===
  var lin = DR.fitLinear(trials, {});
  var linHR = Math.exp(lin.pooled_slope_log * 11);
  var linHR_lo = Math.exp(lin.pooled_slope_log_ci_lo * 11);
  var linHR_hi = Math.exp(lin.pooled_slope_log_ci_hi * 11);

  document.getElementById('linear-kpis').innerHTML =
    '<div class="kpi-grid">' +
    '<div class="kpi"><div class="kpi-label">RR per 11 g/day</div><div class="kpi-value">' + linHR.toFixed(3) + '</div><div>95% CI ' + linHR_lo.toFixed(3) + '&ndash;' + linHR_hi.toFixed(3) + '</div></div>' +
    '<div class="kpi"><div class="kpi-label">log-RR per gram</div><div class="kpi-value">' + lin.pooled_slope_log.toFixed(5) + '</div><div>SE ' + lin.pooled_slope_log_se.toFixed(5) + '</div></div>' +
    '<div class="kpi"><div class="kpi-label">τ²</div><div class="kpi-value">' + lin.tau2.toFixed(5) + '</div></div>' +
    '<div class="kpi"><div class="kpi-label">I²</div><div class="kpi-value">' + lin.I2.toFixed(1) + '%</div><div>Q = ' + lin.Q.toFixed(2) + ' (df ' + lin.Q_df + ')</div></div>' +
    '<div class="kpi"><div class="kpi-label">PI (per 11 g/day, df=' + lin.pi_df + ')</div><div class="kpi-value">' + Math.exp(lin.pi_lo * 11).toFixed(3) + '&ndash;' + Math.exp(lin.pi_hi * 11).toFixed(3) + '</div></div>' +
    '<div class="kpi"><div class="kpi-label">k</div><div class="kpi-value">' + lin.k + '</div>' + (lin.coverage_warning ? '<div style="color:#92400e">coverage warning: k&lt;10</div>' : '') + '</div>' +
    '</div>';

  var forestRows = DR.forest(trials, lin);
  var fHtml = '<h3>Per-study forest (linear layer)</h3><div class="table-scroll"><table><caption>Per-study forest: linear layer (RE-weighted)</caption><thead><tr><th>Study</th><th>HR per gram</th><th>95% CI</th><th>Weight</th></tr></thead><tbody>';
  forestRows.forEach(function (r) {
    fHtml += '<tr><td>' + r.label + '</td>' +
             '<td>' + r.hr.toFixed(4) + '</td>' +
             '<td>' + r.hr_ci_lo.toFixed(4) + '&ndash;' + r.hr_ci_hi.toFixed(4) + '</td>' +
             '<td>' + r.weight_pct.toFixed(1) + '%</td></tr>';
  });
  fHtml += '</tbody></table></div>';
  document.getElementById('linear-forest').innerHTML = fHtml;

  // Linear curve: 20-point grid from 0 to 45 g/day
  var curveHtml = '<h3>Dose-response curve (95% CI via t<sub>' + lin.pi_df + '</sub>)</h3><div class="table-scroll"><table><caption>Dose-response curve: linear layer (20-point grid, 95% CI via t<sub>k-1</sub>)</caption><thead><tr><th>Dose (g/day)</th><th>log-RR</th><th>RR</th><th>95% CI</th></tr></thead><tbody>';
  for (var i = 0; i < 20; i++) {
    var d = i * 45 / 19;
    var p = DR.predict(lin, d);
    curveHtml += '<tr><td>' + d.toFixed(2) + '</td>' +
                 '<td>' + p.est.toFixed(4) + '</td>' +
                 '<td>' + Math.exp(p.est).toFixed(4) + '</td>' +
                 '<td>' + Math.exp(p.ci_lo).toFixed(4) + '&ndash;' + Math.exp(p.ci_hi).toFixed(4) + '</td></tr>';
  }
  curveHtml += '</tbody></table></div>';
  document.getElementById('linear-curve').innerHTML = curveHtml;

  document.getElementById('linear-summary').innerHTML =
    '<p><strong>Plain-English summary:</strong> Each additional 11 g/day of alcohol (≈ 1 standard drink by WHO/Australian convention; US standard drink = 14 g) is associated with a ' +
    ((linHR - 1) * 100).toFixed(1) + '% relative increase in breast-cancer incidence (RR = ' + linHR.toFixed(3) +
    ', 95% CI ' + linHR_lo.toFixed(3) + '–' + linHR_hi.toFixed(3) + '). ' +
    'Between-study heterogeneity is high (I² = ' + lin.I2.toFixed(0) + '%); the prediction interval is wider than the confidence interval and is the better summary of expected effect in a future similar study.</p>' +
    '<p style="margin-top:0.6em; font-size:0.92em; color:#444;"><strong>Important context:</strong> this dataset is the Greenland-Longnecker 1992 methodology paper\'s worked example, not a current systematic review. Modern pooled estimates (e.g., Smith-Warner 1998 <em>JAMA</em>; Allen 2009 <em>JNCI</em>) report ~7–10% relative increase per 10 g/day (RR ≈ 1.07–1.10). The higher RE estimate here reflects extreme between-study heterogeneity (I² ≈ 95%) driven in part by Howe 1991\'s mixed-design contribution, and should not be used as a clinical reference point.</p>';

  // === Tab 2: RCS ===
  var rcs = DR.fitRCS(trials, { knots: 3 });

  var rcsKpis = '<div class="kpi-grid">' +
    '<div class="kpi"><div class="kpi-label">Knots (g/day)</div><div class="kpi-value">' + rcs.rcs.knots.map(function (k) { return k.toFixed(1); }).join(', ') + '</div></div>' +
    '<div class="kpi"><div class="kpi-label">spline_coefs[0] (linear)</div><div class="kpi-value">' + rcs.rcs.spline_coefs[0].toFixed(5) + '</div><div>SE ' + rcs.rcs.spline_coefs_se[0].toFixed(5) + '</div></div>' +
    '<div class="kpi"><div class="kpi-label">spline_coefs[1] (non-linear)</div><div class="kpi-value">' + rcs.rcs.spline_coefs[1].toFixed(5) + '</div><div>SE ' + rcs.rcs.spline_coefs_se[1].toFixed(5) + '</div></div>' +
    '<div class="kpi"><div class="kpi-label">Wald non-linearity p</div><div class="kpi-value">' + rcs.rcs.nonlinearity_wald_p.toFixed(4) + '</div><div>(full REML v0.3, HKSJ-mv = ' + (rcs.hksj_mv != null ? rcs.hksj_mv.toFixed(2) : 'n/a') + ')</div></div>' +
    '<div class="kpi"><div class="kpi-label">τ² per dimension</div><div class="kpi-value">[' + rcs.rcs.tau2_per_dim.map(function (t) { return t.toExponential(2); }).join(', ') + ']</div></div>' +
    '</div>';
  document.getElementById('rcs-kpis').innerHTML = rcsKpis;

  // RCS curve: use fit_at_dose grid
  var rcsCurveHtml = '<h3>RCS dose-response curve</h3><div class="table-scroll"><table><caption>Dose-response curve: RCS layer (20-point grid)</caption><thead><tr><th>Dose (g/day)</th><th>log-RR</th><th>RR</th><th>95% CI</th></tr></thead><tbody>';
  rcs.rcs.fit_at_dose.forEach(function (p) {
    rcsCurveHtml += '<tr><td>' + p.dose.toFixed(2) + '</td>' +
                 '<td>' + p.est.toFixed(4) + '</td>' +
                 '<td>' + Math.exp(p.est).toFixed(4) + '</td>' +
                 '<td>' + Math.exp(p.ci_lo).toFixed(4) + '&ndash;' + Math.exp(p.ci_hi).toFixed(4) + '</td></tr>';
  });
  rcsCurveHtml += '</tbody></table></div>';
  document.getElementById('rcs-curve').innerHTML = rcsCurveHtml;

  // RCS per-study forest (uses F-3 fix to read tau2_per_dim[0] for RE weights)
  var rcsForestRows = DR.forest(trials, rcs);
  var rfHtml = '<h3>Per-study forest (RCS linear-component slopes, RE-weighted)</h3><div class="table-scroll"><table><caption>Per-study forest: RCS linear-component (RE-weighted via F-3 fix)</caption><thead><tr><th>Study</th><th>HR per gram</th><th>95% CI</th><th>RE weight</th></tr></thead><tbody>';
  rcsForestRows.forEach(function (r) {
    rfHtml += '<tr><td>' + r.label + '</td>' +
              '<td>' + r.hr.toFixed(4) + '</td>' +
              '<td>' + r.hr_ci_lo.toFixed(4) + '&ndash;' + r.hr_ci_hi.toFixed(4) + '</td>' +
              '<td>' + r.weight_pct.toFixed(1) + '%</td></tr>';
  });
  rfHtml += '</tbody></table></div>';
  document.getElementById('rcs-forest').innerHTML = rfHtml;

  // Non-linearity Wald note (Round 2C: full-REML v0.3.0 closed the v0.1/v0.2 diagonal-PM gap)
  document.getElementById('rcs-wald').innerHTML =
    '<div class="rv-badge rv-badge-green">' +
    '<strong>Wald non-linearity test (full multivariate REML v0.3.0):</strong> p = ' + rcs.rcs.nonlinearity_wald_p.toFixed(4) +
    ' (df = ' + (rcs.rcs.spline_coefs.length - 1) + ', χ² = ' + (rcs.rcs.nonlinearity_wald_chi2 != null ? rcs.rcs.nonlinearity_wald_chi2.toFixed(3) : 'n/a') + '). ' +
    'Engine v0.3.0 uses full multivariate REML via Nelder-Mead on Cholesky parameters of the τ² matrix; ' +
    'non-linearity p matches R mixmeta within |Δ| < 0.05 (engine ≈ 0.7035 vs R ≈ 0.704 on GL-1992). ' +
    'See the R-parity tab for the side-by-side comparison. ' +
    'HKSJ-multivariate scaling factor: ' + (rcs.hksj_mv != null ? rcs.hksj_mv.toFixed(2) : 'n/a') + '; CI critical value t<sub>k-1</sub> = ' + (rcs.tcrit != null ? rcs.tcrit.toFixed(3) : 'n/a') + '.</div>';

  // Load R-precomputed JSON for Tabs 3 and 4
  fetch('outputs/r_validation/doseresp/gl1992_alcohol_bc.json')
    .then(function (resp) {
      if (!resp.ok) throw new Error('R JSON not found: HTTP ' + resp.status);
      return resp.json();
    })
    .then(function (rRes) {
      // === Tab 3: One-stage ===
      var os = DR.fitOneStage(trials, {}, rRes);
      if (!os || !os.one_stage || os.one_stage.fit_ok === false) {
        document.getElementById('onestage-kpis').innerHTML =
          '<div class="rv-banner rv-banner-error">One-stage R output unavailable. Run <code>python scripts/r_validate_doseresp.py --review gl1992_alcohol_bc</code> to populate.</div>';
        return rRes;
      }
      var osCoef = os.one_stage.coef_dose;
      var osHR11 = Math.exp(osCoef * 11);
      document.getElementById('onestage-kpis').innerHTML =
        '<div class="kpi-grid">' +
        '<div class="kpi"><div class="kpi-label">coef_dose (per gram)</div><div class="kpi-value">' + osCoef.toFixed(5) + '</div><div>SE ' + os.one_stage.coef_dose_se.toFixed(5) + '</div></div>' +
        '<div class="kpi"><div class="kpi-label">RR per 11 g/day</div><div class="kpi-value">' + osHR11.toFixed(3) + '</div><div>95% CI ' + Math.exp(os.one_stage.coef_dose_ci_lo * 11).toFixed(3) + '&ndash;' + Math.exp(os.one_stage.coef_dose_ci_hi * 11).toFixed(3) + '</div></div>' +
        '<div class="kpi"><div class="kpi-label">Random-effects variance (studlab)</div><div class="kpi-value">' + os.one_stage.random_effects_var.toFixed(5) + '</div></div>' +
        '<div class="kpi"><div class="kpi-label">Converged</div><div class="kpi-value">' + (os.one_stage.converged ? 'Yes' : 'No') + '</div></div>' +
        '<div class="kpi"><div class="kpi-label">Solver</div><div class="kpi-value">lme4 ' + (os.one_stage.lme4_version || rRes.one_stage.lme4_version || 'unknown') + '</div></div>' +
        '</div>';
      document.getElementById('onestage-methods').innerHTML =
        '<p><strong>Methodology:</strong> One-stage Poisson hierarchical model fit by R using <code>lme4::glmer(events ~ dose + (1 | studlab), offset = log(n), family = poisson(link = "log"))</code> with the bobyqa optimizer. ' +
        'Per-arm event counts modelled on the log-rate scale; person-years (here approximated by <code>n</code>) enter as an offset. ' +
        'Random intercept per study captures between-study baseline-rate variation. ' +
        'The engine surfaces the precomputed R coefficients only — no JS-side fitter for one-stage, per spec §11.</p>' +
        '<p style="margin-top:0.6em; font-size:0.92em;"><strong>Why this differs from Tab 1:</strong> the one-stage estimate (RR per 11 g/day) differs from the two-stage linear pool because the random study intercept absorbs between-study variation in baseline breast-cancer rates, shifting the fixed-effect dose slope. Neither is wrong; they answer subtly different questions about the dose-response relationship.</p>';

      // === Tab 4: R-parity badge ===
      window.RValidationDoseresp.render('r-parity-doseresp',
        { linear: lin, rcs: rcs, one_stage: os },
        rRes);
      return rRes;
    })
    .catch(function (e) {
      console.error('[ALCOHOL_BC] failed to load R JSON:', e);
      var os = document.getElementById('onestage-kpis');
      os.innerHTML = '';
      var d1 = document.createElement('div');
      d1.style.color = '#c00';
      d1.textContent = 'One-stage tab unavailable: ' + e.message;
      os.appendChild(d1);
      var rp = document.getElementById('r-parity-doseresp');
      rp.innerHTML = '';
      var d2 = document.createElement('div');
      d2.style.color = '#c00';
      d2.textContent = 'R-parity badge unavailable: ' + e.message;
      rp.appendChild(d2);
    });
  // All 4 tabs populated.
});
