/* webr-survival-validator.js — optional R/metafor cross-validation in browser via WebR.
 *
 * Mirrors webr-dta-validator.js. Loaded by *_SURV_REVIEW.html with
 *   <script src="webr-survival-validator.js" defer></script>
 * Zero-cost at page load. First click triggers ~40 MB WebR + metafor install (one-time).
 *
 * Mirrors the engine's REML+HKSJ pooled log-HR:
 *   library(metafor); fit <- rma(yi, vi, method="REML", test="knha"); summary(fit)
 *
 * Public API (via window.RapidMetaSurvivalValidator):
 *   - ensureWebR(): boots WebR + installs metafor; idempotent; resolves to {webR, pkg}.
 *   - validateAgainstR(engineFit, trials): runs metafor::rma on log-HR scale and returns
 *     a flat JS object with mu_logHR, se_logHR, tau2, Q, I2, pi_lo, pi_hi (on log scale).
 *
 * Tolerances are the consumer's responsibility (Cochrane v6.5 §10.10.4: |Delta| < 1e-3
 * on log-HR scale at REML+HKSJ).
 */

(function () {
  'use strict';

  var WEBR_CDN = 'https://webr.r-wasm.org/latest/webr.mjs';

  var webR = null;
  var packageInstalled = null; /* 'metafor' */
  var rVersion = null;
  var bootPromise = null;

  function status(msg) {
    var el = document.getElementById('webr-survival-status');
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
    if (webR && packageInstalled) return { webR: webR, pkg: packageInstalled };
    if (bootPromise) return bootPromise;
    bootPromise = (async function () {
      status('Loading WebR (~40 MB, first-time only)…');
      var WebRClass;
      try {
        var mod = await import(WEBR_CDN);
        WebRClass = mod.WebR;
      } catch (e) {
        status('Could not load WebR module from ' + WEBR_CDN);
        throw new Error('WebR module load failed: ' + (e && e.message ? e.message : String(e)));
      }
      var W = new WebRClass();
      try { await W.init(); }
      catch (e) {
        status('WebR init failed: ' + (e && e.message ? e.message : String(e)));
        throw e;
      }
      webR = W;
      try {
        var verObj = await webR.evalR('paste(R.version$major, R.version$minor, sep=".")');
        var verJs = await verObj.toJs();
        rVersion = (verJs && verJs.values && verJs.values[0]) || null;
      } catch (_e) { rVersion = null; }

      status('Installing metafor via webr::install…');
      try {
        await webR.evalR('webr::install("metafor")');
        await webR.evalR('suppressPackageStartupMessages(library(metafor))');
        packageInstalled = 'metafor';
        status('WebR + metafor ready.');
      } catch (e) {
        status('metafor install failed. WebR validation unavailable.');
        throw new Error('metafor failed to install: ' + (e && e.message ? e.message : String(e)));
      }
      return { webR: webR, pkg: packageInstalled };
    })();
    return bootPromise;
  }

  function buildNumList(name, arr) {
    return name + ' <- c(' + arr.map(function (x) { return String(x); }).join(', ') + ')';
  }

  async function validateAgainstR(engineFit, trials) {
    if (!Array.isArray(trials) || trials.length === 0) {
      throw new Error('No trials supplied to validateAgainstR');
    }
    // Build yi (log-HR) and vi (var-log-HR) from trial.HR + CI
    var Z975 = 1.959963984540054;
    var yi = [], vi = [];
    for (var i = 0; i < trials.length; i++) {
      var t = trials[i] || {};
      if (typeof t.HR !== 'number' || typeof t.HR_ci_lo !== 'number' || typeof t.HR_ci_hi !== 'number') {
        throw new Error('Trial at index ' + i + ' missing HR/HR_ci_lo/HR_ci_hi');
      }
      yi.push(Math.log(t.HR));
      var se = (Math.log(t.HR_ci_hi) - Math.log(t.HR_ci_lo)) / (2 * Z975);
      vi.push(se * se);
    }

    await ensureWebR();
    status('Running metafor::rma (REML+HKSJ, k=' + trials.length + ')…');

    var dataPrefix = [
      buildNumList('yi', yi),
      buildNumList('vi', vi)
    ].join('\n');

    var rCode = dataPrefix + '\n' + [
      'fit <- metafor::rma(yi = yi, vi = vi, method = "REML", test = "knha")',
      'pi <- metafor::predict(fit, level = 95)',
      'list(',
      '  mu_logHR     = unname(fit$beta[1,1]),',
      '  se_logHR     = unname(fit$se),',
      '  tau2         = unname(fit$tau2),',
      '  Q            = unname(fit$QE),',
      '  I2           = unname(fit$I2),',
      '  H2           = unname(fit$H2),',
      '  ci_logHR_lo  = unname(fit$ci.lb),',
      '  ci_logHR_hi  = unname(fit$ci.ub),',
      '  pi_logHR_lo  = unname(pi$pi.lb),',
      '  pi_logHR_hi  = unname(pi$pi.ub),',
      '  k            = unname(fit$k),',
      '  test         = "knha",',
      '  pkg          = "metafor"',
      ')'
    ].join('\n');

    var rObj;
    try { rObj = await webR.evalR(rCode); }
    catch (e) {
      status('R fit failed: ' + (e && e.message ? e.message : String(e)));
      throw e;
    }

    var rJsRaw;
    try { rJsRaw = await rObj.toJs(); }
    catch (e) { throw new Error('Could not convert R result to JS: ' + (e && e.message ? e.message : String(e))); }

    var flat = flattenNamedList(rJsRaw);

    var numericKeys = ['mu_logHR', 'se_logHR', 'tau2', 'Q', 'I2', 'H2',
                       'ci_logHR_lo', 'ci_logHR_hi', 'pi_logHR_lo', 'pi_logHR_hi', 'k'];
    for (var j = 0; j < numericKeys.length; j++) {
      var k = numericKeys[j];
      if (flat[k] != null) flat[k] = Number(flat[k]);
    }
    // Convenience: HR-scale CI/PI
    if (isFinite(flat.ci_logHR_lo)) {
      flat.ci_HR_lo = Math.exp(flat.ci_logHR_lo);
      flat.ci_HR_hi = Math.exp(flat.ci_logHR_hi);
      flat.pooled_HR = Math.exp(flat.mu_logHR);
    }
    if (isFinite(flat.pi_logHR_lo)) {
      flat.pi_HR_lo = Math.exp(flat.pi_logHR_lo);
      flat.pi_HR_hi = Math.exp(flat.pi_logHR_hi);
    }

    flat.r_version = rVersion;
    flat.timestamp = new Date().toISOString();
    if (!flat.pkg) flat.pkg = 'metafor';

    status('Validation complete (' + flat.pkg + ', k=' + trials.length + ').');
    return flat;
  }

  window.RapidMetaSurvivalValidator = {
    ensureWebR: ensureWebR,
    validateAgainstR: validateAgainstR
  };
})();
