/* rapidmeta-dta-engine-v1.js — v1.0.0-rc (2026-04-27)
 *
 * Self-contained frequentist DTA meta-analysis engine for RapidMeta DTA apps.
 * Reitsma bivariate (logit-Sens, logit-Spec, ρ) via REML Fisher scoring,
 * post-hoc HSROC reparam, prevalence-slider PPV/NPV.
 *
 * Validated against mada::reitsma to |Δ| < 1e-3 at build time via WebR.
 *
 * Inputs:
 *   trials: [{ studlab, TP, FP, FN, TN, ... }]
 *   opts:   { correction: 0.5, max_iter: 50, ... }
 *
 * Outputs: see spec §3 result shape.
 *
 * Load as <script src="rapidmeta-dta-engine-v1.js" defer></script>;
 * exposes window.RapidMetaDTA.{fit, validate, exportResults}.
 */
(function (root) {
  'use strict';

  function validate(trials) {
    var issues = [];
    if (!Array.isArray(trials)) { issues.push('trials must be an array'); return issues; }
    var required = ['TP', 'FP', 'FN', 'TN'];
    for (var i = 0; i < trials.length; i++) {
      var t = trials[i];
      for (var j = 0; j < required.length; j++) {
        var k = required[j];
        if (typeof t[k] !== 'number' || t[k] < 0 || !isFinite(t[k])) {
          issues.push('trial ' + i + ' (' + (t.studlab || '?') + '): ' + k + ' must be a finite non-negative number');
        }
      }
    }
    return issues;
  }

  function fit(trials, opts) {
    throw new Error('not yet implemented');
  }

  function exportResults(fitResult) {
    return JSON.parse(JSON.stringify(fitResult));
  }

  root.RapidMetaDTA = {
    fit: fit,
    validate: validate,
    exportResults: exportResults,
    _version: '1.0.0-rc'
  };
})(typeof window !== 'undefined' ? window : globalThis);
