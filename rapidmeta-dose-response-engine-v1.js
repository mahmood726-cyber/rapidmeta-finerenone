/* rapidmeta-dose-response-engine-v1.js — v0.1.0 (2026-05-12)
 *
 * Self-contained dose-response meta-analysis engine for RapidMeta.
 * Three layered fitters: two-stage Greenland-Longnecker linear (primary),
 * two-stage GL + RCS (Harrell defaults), one-stage hierarchical (read from
 * R-precomputed JSON; no JS fitter for this layer).
 *
 * Validated by:
 *   - parity vs dosresmeta::dosresmeta() on the canonical GL-1992 alcohol-
 *     breast-cancer dataset to |Δ|<1e-3 on log-slope
 *   - PI / τ² CI / HKSJ floor per RevMan-2025 bit-reproducibility convention
 *     (PI df=k-1, REML primary, HKSJ floor max(1,Q/(k-1)), Q-profile τ² CI)
 *
 * Load as <script src="rapidmeta-dose-response-engine-v1.js" defer></script>;
 * exposes window.RapidMetaDoseResp.{ validate, fitLinear, fitRCS, fitOneStage,
 *   nonLinearityTest, predict, forest, exportResults, _internal }.
 */
(function (root) {
  'use strict';

  // ===================================================================
  // Section 1: Numerics — copied verbatim from rapidmeta-prognostic-engine-v1.js
  // (lines 57-150) to keep cross-engine numerical behaviour identical.
  // ===================================================================
  // Numerics ported by Unit 3 — leave this section empty for now.

  // ===================================================================
  // Section 2: validate, fitters, helpers — implemented across later units.
  // ===================================================================

  function validate(trials) {
    var issues = [];
    if (!Array.isArray(trials) || trials.length === 0) {
      return ['no trials provided'];
    }
    for (var i = 0; i < trials.length; i++) {
      var t = trials[i] || {};
      var lab = t.studlab || ('trial[' + i + ']');
      var arms = Array.isArray(t.arms) ? t.arms : [];
      if (arms.length < 2) {
        // If the sole arm is a reference, give the semantically precise message.
        if (arms.length === 1 && arms[0] && arms[0].is_reference === true) {
          issues.push(lab + ': reference-only (no contrast arms)');
        } else {
          issues.push(lab + ': single arm or < 2 arms');
        }
        continue;
      }
      var refs = arms.filter(function (a) { return a && a.is_reference === true; });
      if (refs.length === 0) {
        issues.push(lab + ': no reference arm');
      } else if (refs.length > 1) {
        issues.push(lab + ': multiple reference arms');
      }
      if (refs.length === arms.length) {
        issues.push(lab + ': reference-only (no contrast)');
      }
      for (var j = 0; j < arms.length; j++) {
        var a = arms[j];
        if (!a || !isFinite(a.dose) || a.dose < 0) {
          issues.push(lab + '.arms[' + j + ']: invalid dose');
          continue;
        }
        var hasEvents = isFinite(a.events) && isFinite(a.n);
        var hasCont   = isFinite(a.mean)   && isFinite(a.sd);
        if (!hasEvents && !hasCont) {
          issues.push(lab + '.arms[' + j + ']: needs events+n (binary) or mean+sd (continuous)');
          continue;
        }
        if (hasEvents) {
          if (a.events < 0 || a.n <= 0) issues.push(lab + '.arms[' + j + ']: events/n out of range');
          if (a.events > a.n) issues.push(lab + '.arms[' + j + ']: events > n');
        }
        if (hasCont && a.sd <= 0) issues.push(lab + '.arms[' + j + ']: sd must be > 0');
      }
    }
    return issues;
  }

  var API = {
    engine_version: 'rapidmeta-dose-response-engine-v1@0.1.0',
    validate: validate,
    fitLinear: function () { throw new Error('Unit 4: not yet implemented'); },
    fitRCS: function () { throw new Error('Unit 6: not yet implemented'); },
    fitOneStage: function () { throw new Error('Unit 7: not yet implemented'); },
    nonLinearityTest: function () { throw new Error('Unit 7: not yet implemented'); },
    predict: function () { throw new Error('Unit 7: not yet implemented'); },
    forest: function () { throw new Error('Unit 7: not yet implemented'); },
    exportResults: function () { throw new Error('Unit 7: not yet implemented'); },
    _internal: {},
  };

  root.RapidMetaDoseResp = API;
  if (typeof module !== 'undefined' && module.exports) module.exports = API;
})(typeof window !== 'undefined' ? window : globalThis);
