/* webr-prognostic-validator.js — optional R/metafor cross-validation in browser via WebR.
 *
 * Loaded by prognostic-factor review HTMLs with <script src="webr-prognostic-validator.js" defer></script>.
 * Zero-cost at page load. First click triggers ~40 MB WebR + metafor install (one-time).
 *
 * Mirrors the engine's Paule-Mandel random-effects fit:
 *   library(metafor); fit <- rma(yi = log_HR, vi = seLog^2, method = "PM"); summary(fit)
 *
 * Computes per-quantity Delta vs the engine output; consumer renders EXACT/CLOSE/DIFFER table.
 *
 * Public API (via window.RapidMetaPrognosticValidator):
 *   - ensureWebR(): boots WebR + installs metafor; idempotent; resolves to { webR, pkg }.
 *   - validateAgainstR(engineFit, trials): runs the R-side fit on the given trial set and
 *     returns a flat JS object with the same field names as engineFit (pooled_logHR,
 *     pooled_logHR_se, tau2, Q, df_Q, I2) plus pkg='metafor', r_version, and rma_method='PM'.
 *
 * Tolerances:
 *   - |Δ pooled_logHR| < 1e-6 expected (PM bisection is deterministic, metafor PM iterates
 *     a slightly different Newton step but converges to the same fixed point).
 *   - |Δ tau2| < 1e-4 expected (PM is well-conditioned at the converged μ̂).
 *   - |Δ Q| < 1e-6 expected (Q is a closed-form sum given tau2, μ̂).
 *
 * This file does NOT render the result panel — that lives in the review HTML's <script> block.
 *
 * Architectural mirror: parallels webr-dta-validator.js. DTA validates against mada::reitsma;
 * prognostic validates against metafor::rma(method='PM'). Both modules expose the same shape
 * so the consumer's render code can be templated.
 */

(function () {
  'use strict';

  var WEBR_CDN = 'https://webr.r-wasm.org/latest/webr.mjs';
  // metafor is precompiled for r-wasm at https://repo.r-wasm.org; install via webr::install("metafor").

  var webR = null;
  var packageInstalled = null; /* 'metafor' */
  var rVersion = null;
  var bootPromise = null;

  function status(msg) {
    var el = document.getElementById('webr-prognostic-status');
    if (el) el.textContent = msg;
  }

  function flattenNamedList(rJs) {
    if (!rJs || !rJs.names || !rJs.values) return rJs;
    var out = {};
    for (var i = 0; i < rJs.names.length; i++) {
      var name = rJs.names[i];
      var v = rJs.values[i];
      if (v && Object.prototype.hasOwnProperty.call(v, 'values') && Array.isArray(v.values)) {
        out[name] = v.values.length === 1 ? v.values[0] : v.values;
      } else {
        out[name] = v;
      }
    }
    return out;
  }

  async function ensureWebR() {
    if (bootPromise) return bootPromise;
    bootPromise = (async function () {
      status('Loading WebR runtime…');
      var mod = await import(WEBR_CDN);
      webR = new mod.WebR();
      await webR.init();
      var v = await webR.evalRString('paste(R.version$major, R.version$minor, sep=".")');
      rVersion = v;
      status('R ' + v + ' ready. Installing metafor…');
      try {
        await webR.evalRVoid('webr::install("metafor")');
        await webR.evalRVoid('library(metafor)');
        packageInstalled = 'metafor';
        status('R ' + v + ' + metafor ready.');
      } catch (e) {
        packageInstalled = null;
        status('metafor install failed: ' + (e && e.message ? e.message : e));
        throw e;
      }
      return { webR: webR, pkg: packageInstalled };
    })();
    return bootPromise;
  }

  function deriveLogEffects(trials) {
    var Z975 = 1.959963984540054;
    var yi = [], vi = [], labels = [];
    for (var i = 0; i < trials.length; i++) {
      var t = trials[i];
      var yi_i = Math.log(t.hr_adj);
      var seLog = (Math.log(t.hr_adj_ci_ub) - Math.log(t.hr_adj_ci_lb)) / (2 * Z975);
      yi.push(yi_i);
      vi.push(seLog * seLog);
      labels.push(t.studlab || ('study_' + i));
    }
    return { yi: yi, vi: vi, labels: labels };
  }

  async function validateAgainstR(engineFit, trials) {
    var boot = await ensureWebR();
    if (boot.pkg !== 'metafor') throw new Error('metafor not installed; cannot validate');

    var derived = deriveLogEffects(trials);
    status('Running R metafor::rma(method="PM")…');

    // Build the R command. Pass yi and vi as numeric vectors via WebR's eval interface.
    var rCmd =
      'yi <- c(' + derived.yi.map(function (v) { return v.toExponential(15); }).join(',') + '); ' +
      'vi <- c(' + derived.vi.map(function (v) { return v.toExponential(15); }).join(',') + '); ' +
      'fit <- rma(yi = yi, vi = vi, method = "PM"); ' +
      'list(' +
      '  pooled_logHR    = as.numeric(fit$b)[1],' +
      '  pooled_logHR_se = as.numeric(fit$se)[1],' +
      '  tau2            = as.numeric(fit$tau2),' +
      '  Q               = as.numeric(fit$QE),' +
      '  df_Q            = as.numeric(fit$k - 1),' +
      '  I2              = as.numeric(fit$I2) / 100,' +
      '  H2              = as.numeric(fit$H2),' +
      '  ci_lb_logHR     = as.numeric(fit$ci.lb),' +
      '  ci_ub_logHR     = as.numeric(fit$ci.ub),' +
      '  k               = as.numeric(fit$k),' +
      '  r_version       = paste(R.version$major, R.version$minor, sep=".")' +
      ')';

    var raw = await webR.evalR(rCmd);
    var js = await raw.toJs();
    var flat = flattenNamedList(js);

    flat.pkg = 'metafor';
    flat.rma_method = 'PM';

    // Compute deltas vs engine
    flat.delta_pooled_logHR = (engineFit && typeof engineFit.pooled_logHR === 'number')
      ? Math.abs(engineFit.pooled_logHR - flat.pooled_logHR) : null;
    flat.delta_pooled_logHR_se = (engineFit && typeof engineFit.pooled_logHR_se === 'number')
      ? Math.abs(engineFit.pooled_logHR_se - flat.pooled_logHR_se) : null;
    flat.delta_tau2 = (engineFit && typeof engineFit.tau2 === 'number')
      ? Math.abs(engineFit.tau2 - flat.tau2) : null;
    flat.delta_Q = (engineFit && typeof engineFit.Q === 'number')
      ? Math.abs(engineFit.Q - flat.Q) : null;
    flat.delta_I2 = (engineFit && typeof engineFit.I2 === 'number')
      ? Math.abs(engineFit.I2 - flat.I2) : null;

    // Verdict: all deltas under threshold → EXACT; pooled_logHR + tau2 under loose → CLOSE; else DIFFER
    var allTight = (flat.delta_pooled_logHR != null && flat.delta_pooled_logHR < 1e-6) &&
                   (flat.delta_tau2 != null && flat.delta_tau2 < 1e-4) &&
                   (flat.delta_Q != null && flat.delta_Q < 1e-4);
    var someTight = (flat.delta_pooled_logHR != null && flat.delta_pooled_logHR < 1e-3) &&
                    (flat.delta_tau2 != null && flat.delta_tau2 < 1e-2);
    flat.verdict = allTight ? 'EXACT' : (someTight ? 'CLOSE' : 'DIFFER');

    status('Done. Verdict: ' + flat.verdict);
    return flat;
  }

  window.RapidMetaPrognosticValidator = {
    ensureWebR: ensureWebR,
    validateAgainstR: validateAgainstR,
    deriveLogEffects: deriveLogEffects
  };
})();
