/* webr-dta-validator.js — optional R/mada cross-validation in browser via WebR.
 *
 * Loaded by *_DTA_REVIEW.html with <script src="webr-dta-validator.js" defer></script>.
 * Zero-cost at page load. First click triggers ~40 MB WebR + mada install (one-time).
 *
 * Mirrors the engine's Reitsma bivariate fit:
 *   library(mada); fit <- reitsma(data); summary(fit)
 *
 * Computes per-quantity Delta vs the engine output; consumer renders EXACT/CLOSE/DIFFER table.
 * Falls back to metafor::rma.mv bivariate (UN structure) if mada is unavailable on r-wasm CRAN.
 *
 * Public API (via window.RapidMetaDTAValidator):
 *   - ensureWebR(): boots WebR + installs the R-side package; idempotent; resolves to {webR, pkg}.
 *   - validateAgainstR(engineFit, trials): runs the R-side fit on the given trial set and
 *     returns a flat JS object with the same field names as engineFit._fitInternal plus pkg
 *     and (when applicable) note / r_version.
 *
 * Tolerances are the consumer's responsibility (see plan §6 / §17). This file does NOT
 * render the result panel — that lives in the review HTML's <script> block.
 */

(function () {
  'use strict';

  var WEBR_CDN = 'https://webr.r-wasm.org/latest/webr.mjs';
  // Note: WebR's R 4.5.x does not run source install.packages() — non-base packages must
  // be installed via webr::install("<pkg>") which fetches a precompiled WASM binary from
  // https://repo.r-wasm.org under the hood. Using install.packages(repos=…) directly fails
  // with "This version of R is not set up to install source packages".

  var webR = null;
  var packageInstalled = null; /* 'mada' | 'metafor' */
  var rVersion = null;
  var bootPromise = null;

  function status(msg) {
    var el = document.getElementById('webr-status');
    if (el) el.textContent = msg;
  }

  /* Convert a WebR named-list `toJs()` payload into a flat {name: value} object.
   * WebR returns named lists as { type:'list', names:[...], values:[<RObject toJs results>...] }.
   * Each value is itself { type:'double'|'character'|..., values:[...] } (or {names:..., values:...} for nested).
   * We only need to handle scalar doubles and scalar characters here. */
  function flattenNamedList(rJs) {
    if (!rJs || !rJs.names || !rJs.values) return rJs;
    var out = {};
    for (var i = 0; i < rJs.names.length; i++) {
      var name = rJs.names[i];
      var v = rJs.values[i];
      if (v && Object.prototype.hasOwnProperty.call(v, 'values') && Array.isArray(v.values)) {
        // Scalar atomic: take first element
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
      try {
        await W.init();
      } catch (e) {
        status('WebR init failed: ' + (e && e.message ? e.message : String(e)));
        throw e;
      }
      webR = W;

      // Capture R version once (best-effort; non-fatal if it fails)
      try {
        var verObj = await webR.evalR('paste(R.version$major, R.version$minor, sep=".")');
        var verJs = await verObj.toJs();
        rVersion = (verJs && verJs.values && verJs.values[0]) || null;
      } catch (_e) {
        rVersion = null;
      }

      status('Installing mada via webr::install…');
      try {
        await webR.evalR('webr::install("mada")');
        await webR.evalR('suppressPackageStartupMessages(library(mada))');
        packageInstalled = 'mada';
        status('WebR + mada ready.');
      } catch (e) {
        status('mada install failed; trying metafor fallback via webr::install…');
        try {
          await webR.evalR('webr::install("metafor")');
          await webR.evalR('suppressPackageStartupMessages(library(metafor))');
          packageInstalled = 'metafor';
          status('WebR + metafor (fallback) ready. ρ row will be CLOSE-only.');
        } catch (e2) {
          status('Both mada and metafor failed to install. WebR validation unavailable.');
          throw new Error('mada and metafor both failed: ' + (e2 && e2.message ? e2.message : String(e2)));
        }
      }
      return { webR: webR, pkg: packageInstalled };
    })();
    return bootPromise;
  }

  function buildIntList(name, arr) {
    return name + ' <- c(' + arr.map(function (x) { return String(x | 0); }).join(', ') + ')';
  }

  async function validateAgainstR(engineFit, trials) {
    if (!Array.isArray(trials) || trials.length === 0) {
      throw new Error('No trials supplied to validateAgainstR');
    }
    // Sanity-check 2x2 cell presence
    for (var i = 0; i < trials.length; i++) {
      var t = trials[i] || {};
      if (typeof t.TP !== 'number' || typeof t.FP !== 'number' ||
          typeof t.FN !== 'number' || typeof t.TN !== 'number') {
        throw new Error('Trial at index ' + i + ' missing TP/FP/FN/TN');
      }
    }

    var booted = await ensureWebR();
    var pkg = booted.pkg;
    status('Running ' + pkg + ' fit (k=' + trials.length + ')…');

    var TPs = trials.map(function (t) { return t.TP; });
    var FPs = trials.map(function (t) { return t.FP; });
    var FNs = trials.map(function (t) { return t.FN; });
    var TNs = trials.map(function (t) { return t.TN; });

    var dataPrefix = [
      buildIntList('TP', TPs),
      buildIntList('FP', FPs),
      buildIntList('FN', FNs),
      buildIntList('TN', TNs),
      'd <- data.frame(TP=TP, FP=FP, FN=FN, TN=TN)'
    ].join('\n');

    var rCode;
    if (pkg === 'mada') {
      // mada::reitsma — bivariate Reitsma model.
      // Convention: mada parameterises the second component as logit(FPR) = logit(1 - spec),
      // i.e. -logit(spec). The engine's _fitInternal stores mu_spec_logit on the
      // logit(spec) scale (see lessons.md "SROC sign"). We negate fit$coefficients[2]
      // here so the comparison is convention-aligned (engine logit(spec) vs R logit(spec)).
      // Variances and rho sign-flip cancels: SE is unchanged, and Cov(sens, -fpr) = -Cov(sens, fpr)
      // so rho on the (sens, spec) scale = -rho on mada's (sens, fpr) scale.
      rCode = dataPrefix + '\n' + [
        'fit <- mada::reitsma(d)',
        's <- summary(fit)',
        'list(',
        '  mu_sens_logit = unname(fit$coefficients[1]),',
        '  mu_spec_logit = -unname(fit$coefficients[2]),',
        '  se_sens_logit = sqrt(unname(fit$vcov[1,1])),',
        '  se_spec_logit = sqrt(unname(fit$vcov[2,2])),',
        '  tau2_sens = unname(fit$Psi[1,1]),',
        '  tau2_spec = unname(fit$Psi[2,2]),',
        '  rho = -unname(fit$Psi[1,2] / sqrt(fit$Psi[1,1] * fit$Psi[2,2])),',
        '  pkg = "mada"',
        ')'
      ].join('\n');
    } else {
      // metafor::rma.mv bivariate fallback (per plan §17 Step 1).
      // Note: rho is approximate vs mada::reitsma; tolerance still 1e-2.
      rCode = dataPrefix + '\n' + [
        'd$study <- 1:nrow(d)',
        'd$logit_sens <- log((d$TP+0.5)/(d$FN+0.5))',
        'd$logit_spec <- log((d$TN+0.5)/(d$FP+0.5))',
        'd$var_sens <- 1/(d$TP+0.5) + 1/(d$FN+0.5)',
        'd$var_spec <- 1/(d$TN+0.5) + 1/(d$FP+0.5)',
        'd_long <- rbind(',
        '  data.frame(study=d$study, type="sens", yi=d$logit_sens, vi=d$var_sens),',
        '  data.frame(study=d$study, type="spec", yi=d$logit_spec, vi=d$var_spec)',
        ')',
        'fit <- metafor::rma.mv(yi, vi, mods = ~ type - 1, random = ~ type | study, struct = "UN", data = d_long)',
        'list(',
        '  mu_sens_logit = unname(fit$beta[1]),',
        '  mu_spec_logit = unname(fit$beta[2]),',
        '  se_sens_logit = sqrt(unname(fit$vb[1,1])),',
        '  se_spec_logit = sqrt(unname(fit$vb[2,2])),',
        '  tau2_sens = unname(fit$tau2[1]),',
        '  tau2_spec = unname(fit$tau2[2]),',
        '  rho = unname(fit$rho),',
        '  pkg = "metafor",',
        '  note = "Approximate; rho may differ from mada::reitsma at 1e-2 scale"',
        ')'
      ].join('\n');
    }

    var rObj;
    try {
      rObj = await webR.evalR(rCode);
    } catch (e) {
      status('R fit failed: ' + (e && e.message ? e.message : String(e)));
      throw e;
    }

    var rJsRaw;
    try {
      rJsRaw = await rObj.toJs();
    } catch (e) {
      throw new Error('Could not convert R result to JS: ' + (e && e.message ? e.message : String(e)));
    }

    var flat = flattenNamedList(rJsRaw);

    // Type-coerce numeric fields explicitly (toJs() may yield strings for character vectors)
    var numericKeys = ['mu_sens_logit', 'mu_spec_logit', 'se_sens_logit', 'se_spec_logit',
                       'tau2_sens', 'tau2_spec', 'rho'];
    for (var j = 0; j < numericKeys.length; j++) {
      var k = numericKeys[j];
      if (flat[k] != null) flat[k] = Number(flat[k]);
    }

    flat.r_version = rVersion;
    flat.timestamp = new Date().toISOString();
    if (!flat.pkg) flat.pkg = pkg;

    status('Validation complete (' + flat.pkg + ', k=' + trials.length + ').');
    return flat;
  }

  window.RapidMetaDTAValidator = {
    ensureWebR: ensureWebR,
    validateAgainstR: validateAgainstR
  };
})();
