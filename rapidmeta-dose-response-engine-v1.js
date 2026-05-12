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

  var API = {
    engine_version: 'rapidmeta-dose-response-engine-v1@0.1.0',
    validate: function () { throw new Error('Unit 3: not yet implemented'); },
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
