/*!
 * rapidmeta-guards.js — fail-closed validation guards for the shared RapidMeta base engine.
 *
 * Every guard in this file exists because a specific defect shipped. Each is keyed to an id in
 * RAPIDMETA_ERROR_REGISTRY.md. The contract is uniform and deliberate:
 *
 *   FAIL CLOSED. A guard that cannot decide BLOCKS. It never resolves an unknown to the
 *   favourable value, never substitutes a neighbouring value, and never returns a number it
 *   could not justify. `null`, `undefined`, `''` and NaN are UNKNOWN, not zero.
 *
 * Guards throw `GuardBlock` (an Error subclass carrying {guard, code, detail}). Callers that
 * must not throw use the `try*` wrappers, which return {ok:false, block} instead.
 *
 * No DOM, no globals, no I/O — so the same code runs in the app and under `node --test`.
 *
 * Registry: RAPIDMETA_ERROR_REGISTRY.md   Version 1.0   2026-07-30
 */
(function (root, factory) {
  var api = factory();
  if (typeof module === "object" && module.exports) module.exports = api;
  if (root) root.RapidMetaGuards = api;
})(typeof globalThis !== "undefined" ? globalThis : this, function () {
  "use strict";

  /* ------------------------------------------------------------------ core */

  function GuardBlock(guard, code, detail) {
    var e = new Error("[" + guard + "] " + code + (detail ? " — " + detail : ""));
    e.name = "GuardBlock";
    e.guard = guard;
    e.code = code;
    e.detail = detail || "";
    Object.setPrototypeOf(e, GuardBlock.prototype);
    return e;
  }
  GuardBlock.prototype = Object.create(Error.prototype);
  GuardBlock.prototype.constructor = GuardBlock;

  function block(guard, code, detail) { throw GuardBlock(guard, code, detail); }

  /** Wrap any guard call so a caller in a render path can degrade instead of throwing. */
  function attempt(fn) {
    try { return { ok: true, value: fn() }; }
    catch (e) {
      if (e && e.name === "GuardBlock") return { ok: false, block: e, reason: e.message };
      throw e;
    }
  }

  /** UNKNOWN test. `0` is a value; null/undefined/''/NaN are not. This is the RM-F05 fix. */
  function isPresent(x) {
    if (x === null || x === undefined) return false;
    if (typeof x === "string" && x.trim() === "") return false;
    if (typeof x === "number") return Number.isFinite(x);
    if (typeof x === "boolean") return true;
    return true;
  }

  var NA = Object.freeze({ na: true, toString: function () { return "NA"; } });

  function norm(s) { return String(s === null || s === undefined ? "" : s).trim().toLowerCase(); }

  /* ------------------------------------------------------- estimand taxonomy */

  var ESTIMANDS = Object.freeze({
    HR:               { scale: "ratio",  poolsWith: "HR",               label: "hazard ratio" },
    OR:               { scale: "ratio",  poolsWith: "OR",               label: "odds ratio" },
    RR:               { scale: "ratio",  poolsWith: "RR",               label: "risk ratio" },
    RATE_RATIO:       { scale: "rate",   poolsWith: "RATE_RATIO",       label: "rate ratio (recurrent events)" },
    WIN_RATIO:        { scale: "hier",   poolsWith: "WIN_RATIO",        label: "win ratio" },
    RATIO_CONTINUOUS: { scale: "cont",   poolsWith: "RATIO_CONTINUOUS", label: "ratio of change" },
    MD:               { scale: "cont",   poolsWith: "MD",               label: "mean difference" },
    SMD:              { scale: "cont",   poolsWith: "SMD",              label: "standardised mean difference" }
  });

  /** Models that consume a ratio-of-risks scale. A continuous or hierarchical estimate may never enter one. */
  var RATIO_MODELS = Object.freeze(["HR", "OR", "RR"]);

  /** Plausible bounds for any reported ratio effect. Outside this, the value is not a ratio. */
  var RATIO_MIN = 0.01, RATIO_MAX = 100;          // hard: outside this it is not a ratio
  var RATIO_IMPLAUSIBLE_LO = 0.02, RATIO_IMPLAUSIBLE_HI = 25;   // soft: outside this no trial reports it

  var ESTIMAND_ALIASES = Object.freeze({
    "hazard ratio": "HR", "hr": "HR",
    "odds ratio": "OR", "or": "OR", "peto": "OR", "peto or": "OR",
    "risk ratio": "RR", "relative risk": "RR", "rr": "RR",
    "rate ratio": "RATE_RATIO", "rateratio": "RATE_RATIO", "incidence rate ratio": "RATE_RATIO",
    "irr": "RATE_RATIO", "recurrent": "RATE_RATIO", "recurrent event": "RATE_RATIO",
    "win ratio": "WIN_RATIO", "winratio": "WIN_RATIO",
    "ratio of change": "RATIO_CONTINUOUS", "ratio_continuous": "RATIO_CONTINUOUS",
    "geometric mean ratio": "RATIO_CONTINUOUS", "gmr": "RATIO_CONTINUOUS",
    "mean difference": "MD", "md": "MD", "continuous": "MD",
    "standardised mean difference": "SMD", "standardized mean difference": "SMD", "smd": "SMD"
  });

  /**
   * G00 — resolve an estimand tag. FAIL CLOSED: an unrecognised tag blocks. There is deliberately
   * no default to "HR"; defaulting to HR is precisely the RM-A02 denylist bug.
   */
  function resolveEstimand(tag) {
    if (!isPresent(tag)) block("G00", "ESTIMAND_MISSING", "no estimandType on the record");
    var raw = String(tag).trim();
    if (Object.prototype.hasOwnProperty.call(ESTIMANDS, raw.toUpperCase())) return raw.toUpperCase();
    var alias = ESTIMAND_ALIASES[norm(raw)];
    if (alias) return alias;
    block("G00", "ESTIMAND_UNKNOWN", JSON.stringify(raw));
  }

  /* ============================ G01 · continuous cannot enter a ratio model ============================
   * Registry: RM-A05, RM-A01, RM-A07, RM-A09
   * Two symmetric failures this closes:
   *   (a) a continuous / win-ratio / rate-ratio estimate admitted to an HR/OR/RR pool;
   *   (b) a non-ratio quantity (percent change from baseline) written into a ratio field —
   *       proved a mistype, not an implausible value, by pubHR 73.83 and a CI lower bound of -0.5509.
   */
  var CHANGE_FROM_BASELINE_RE = /(percent|percentage|%)\s*change|change\s+from\s+baseline|absolute\s+change/i;

  function assertRatioModelInput(trial, modelMeasure) {
    var G = "G01";
    var model = String(modelMeasure || "").toUpperCase();
    if (RATIO_MODELS.indexOf(model) === -1) block(G, "MODEL_NOT_RATIO", model || "(none)");

    var est = resolveEstimand(trial && trial.estimandType);
    var spec = ESTIMANDS[est];
    if (spec.scale !== "ratio") {
      block(G, "ESTIMAND_NOT_ADMISSIBLE",
        est + " (" + spec.label + ") cannot enter a " + model + " model; hold it out and name it");
    }
    if (est !== model) {
      block(G, "ESTIMAND_MODEL_MISMATCH", est + " into a " + model + " model");
    }

    // (b) the ratio field must actually hold a ratio.
    var fields = ["effect", "publishedHR", "pubHR", "lci", "uci", "hrLCI", "hrUCI", "pubHR_LCI", "pubHR_UCI"];
    for (var i = 0; i < fields.length; i++) {
      var v = trial ? trial[fields[i]] : undefined;
      if (!isPresent(v)) continue;
      var n = Number(v);
      if (!Number.isFinite(n)) block(G, "RATIO_FIELD_NOT_FINITE", fields[i] + "=" + v);
      // A ratio of positive rates is strictly positive, and no reported clinical effect sits
      // outside ~0.01-100. The bempedoic LDL-C panel rendered "Pooled Hazard Ratio = -19.50 /
      // 2050% lower hazard" - a continuous mean difference forced through the HR template.
      if (n <= 0) block(G, "RATIO_FIELD_NON_POSITIVE", fields[i] + "=" + n + " — a ratio of positive rates cannot be <= 0");
      // Two tiers, because they fail differently. IMPOSSIBLE is the hard bound Mahmood specified
      // (~0.01-100): nothing outside it is a ratio at all. IMPLAUSIBLE is the softer bound that
      // catches a percent-change (73.83) sitting inside the hard bound but far outside any
      // reported effect.
      if (n < RATIO_MIN || n > RATIO_MAX) {
        block(G, "RATIO_FIELD_IMPOSSIBLE",
          fields[i] + "=" + n + " — outside [" + RATIO_MIN + ", " + RATIO_MAX +
          "]; a value this size is a different quantity wearing a ratio label");
      }
      if (n < RATIO_IMPLAUSIBLE_LO || n > RATIO_IMPLAUSIBLE_HI) {
        block(G, "RATIO_FIELD_IMPLAUSIBLE",
          fields[i] + "=" + n + " — outside any reported ratio range [" + RATIO_IMPLAUSIBLE_LO +
          ", " + RATIO_IMPLAUSIBLE_HI + "]");
      }
    }
    var title = (trial && (trial.title || trial.outcomeTitle)) || "";
    if (CHANGE_FROM_BASELINE_RE.test(title) && isPresent(trial && (trial.publishedHR || trial.pubHR))) {
      block(G, "CHANGE_SCORE_IN_RATIO_FIELD", JSON.stringify(String(title).slice(0, 80)));
    }
    return { ok: true, estimand: est, model: model };
  }

  /* ============================ G02 · Peto output is labelled OR ============================
   * Registry: RM-A04, RM-A03.  "Peto HR" is a contradiction; Peto is an odds-ratio method.
   */
  var ESTIMATOR_MEASURE = Object.freeze({
    peto: "OR", "peto-or": "OR", mh: "OR", "mantel-haenszel": "OR",
    iv: null, reml: null, dl: null, pm: null, "paule-mandel": null
  });

  function labelForEstimator(estimator, requestedMeasure) {
    var G = "G02";
    var key = norm(estimator);
    if (!Object.prototype.hasOwnProperty.call(ESTIMATOR_MEASURE, key)) {
      block(G, "ESTIMATOR_UNKNOWN", estimator === undefined ? "(none)" : String(estimator));
    }
    var forced = ESTIMATOR_MEASURE[key];
    if (forced === null) {
      // scale-agnostic estimator: the caller's measure stands, but must be a known one
      return { measure: resolveEstimand(requestedMeasure), forced: false, estimator: key };
    }
    if (isPresent(requestedMeasure) && resolveEstimand(requestedMeasure) !== forced) {
      block(G, "ESTIMATOR_MEASURE_MISLABEL",
        key + " produces " + forced + ", not " + resolveEstimand(requestedMeasure));
    }
    return {
      measure: forced, forced: true, estimator: key,
      caveat: key === "peto" ? "Peto is biased at large effects and unbalanced allocation." : ""
    };
  }

  /* ============================ G03 · no silent endpoint fallback ============================
   * Registry: RM-B01, RM-B03.  Replaces the `outcomes[0]` heuristic in the selector, the pool and
   * the paper module. When the selected scope has no row, BLOCK — never substitute.
   */
  function resolveOutcomeScope(trial, scopeKey) {
    var G = "G03";
    if (!isPresent(scopeKey)) block(G, "SCOPE_MISSING", "a scope key is required; there is no 'default' endpoint");
    var rows = (trial && (trial.allOutcomes || trial.outcomes)) || [];
    if (!Array.isArray(rows)) block(G, "OUTCOME_ROWS_MALFORMED", typeof rows);

    var want = norm(scopeKey);
    var hits = rows.filter(function (r) {
      return norm(r && r.scopeClass) === want || norm(r && r.shortLabel) === want;
    });
    if (hits.length === 0) {
      return {
        ok: false, blocked: true, row: null,
        reason: "not available for this outcome",
        detail: "trial " + ((trial && (trial.name || trial.nct)) || "(unnamed)") +
                " has no row in scope '" + scopeKey + "'; it is excluded, not substituted"
      };
    }
    if (hits.length > 1) {
      block(G, "SCOPE_AMBIGUOUS",
        hits.length + " rows match scope '" + scopeKey + "' — resolve at extraction, do not pick one");
    }
    var row = hits[0];
    if (!isPresent(row.scopeClass)) block(G, "ROW_UNTYPED", "outcome row carries no scopeClass");
    return { ok: true, blocked: false, row: row, reason: "" };
  }

  /* ============================ G04 · component counts cannot pair with a composite effect ======
   * Registry: RM-A08, RM-A09.  Counts and effect must resolve to the SAME outcome key, and the
   * crude 2x2 must not point the opposite way to the published effect.
   */
  function assertCountsMatchEffect(row, opts) {
    var G = "G04";
    var o = opts || {};
    var countKey = row && (row.countOutcomeKey || row.shortLabel);
    var effectKey = row && (row.effectOutcomeKey || row.shortLabel);
    var hasCounts = isPresent(row && row.tE) && isPresent(row && row.cE);
    var hasEffect = isPresent(row && (row.effect !== undefined ? row.effect : row.publishedHR));
    if (!hasCounts || !hasEffect) return { ok: true, checked: false };

    if (norm(countKey) !== norm(effectKey)) {
      block(G, "COUNT_EFFECT_KEY_MISMATCH",
        "counts from '" + countKey + "' beside an effect for '" + effectKey + "'");
    }
    if (isPresent(row.tN) && isPresent(row.cN)) {
      var tE = Number(row.tE), tN = Number(row.tN), cE = Number(row.cE), cN = Number(row.cN);
      if (tE > tN || cE > cN) block(G, "EVENTS_EXCEED_DENOMINATOR", tE + "/" + tN + ", " + cE + "/" + cN);
      if (tN > 0 && cN > 0 && cE > 0 && tE > 0) {
        var crudeRR = (tE / tN) / (cE / cN);
        var eff = Number(row.effect !== undefined ? row.effect : row.publishedHR);
        var tol = o.tolerance === undefined ? 0 : o.tolerance;
        if ((crudeRR - 1) * (eff - 1) < -tol) {
          block(G, "DIRECTION_CONTRADICTION",
            "crude RR " + crudeRR.toFixed(3) + " and published effect " + eff + " point in opposite directions");
        }
      }
    }
    return { ok: true, checked: true };
  }

  /* ============================ G05 · missing is NA, never 0 ============================
   * Registry: RM-F05, RM-F06, RM-C01.
   */
  function naOrNumber(x) {
    if (!isPresent(x)) return NA;
    var n = Number(x);
    return Number.isFinite(n) ? n : NA;
  }

  function renderPercent(events, denom, digits) {
    var e = naOrNumber(events), d = naOrNumber(denom);
    if (e === NA || d === NA) return "NA";
    if (d <= 0) return "NA";
    return (100 * e / d).toFixed(digits === undefined ? 1 : digits) + "%";
  }

  /** PRISMA stages: an unrecorded stage renders "not recorded". A 0 asserts a search that returned nothing. */
  function renderPrismaStage(count) {
    return isPresent(count) ? String(Number(count)) : "not recorded";
  }

  function assertPrismaCoherent(stages) {
    var G = "G05";
    var order = ["identified", "screened", "eligible", "included"];
    // The impossible case is checked FIRST: "0 identified" asserts that a search ran and returned
    // nothing, which is a different and stronger false claim than a monotonicity violation.
    if (isPresent(stages && stages.included) && Number(stages.included) > 0 &&
        isPresent(stages && stages.identified) && Number(stages.identified) === 0) {
      block(G, "PRISMA_IMPOSSIBLE", "0 identified with " + stages.included + " included");
    }
    var prev = null, prevName = "";
    for (var i = 0; i < order.length; i++) {
      var v = stages ? stages[order[i]] : undefined;
      if (!isPresent(v)) { prev = null; prevName = ""; continue; }
      var n = Number(v);
      if (!Number.isFinite(n) || n < 0) block(G, "PRISMA_STAGE_INVALID", order[i] + "=" + v);
      if (prev !== null && n > prev) {
        block(G, "PRISMA_STAGE_INCREASES", order[i] + "(" + n + ") > " + prevName + "(" + prev + ")");
      }
      prev = n; prevName = order[i];
    }
    return { ok: true };
  }

  /** Denominators must be labelled. RM-C01: randomised and analysed are different numbers. */
  function assertDenominatorLabelled(arm) {
    var G = "G05";
    var hasR = isPresent(arm && arm.nRandomised), hasA = isPresent(arm && arm.nAnalysed);
    if (!hasR && !hasA) block(G, "DENOMINATOR_UNLABELLED", "neither nRandomised nor nAnalysed present");
    if (hasR && hasA && Number(arm.nRandomised) !== Number(arm.nAnalysed) && !isPresent(arm.attritionReason)) {
      block(G, "ATTRITION_UNEXPLAINED",
        arm.nRandomised + " randomised vs " + arm.nAnalysed + " analysed with no stated reason");
    }
    return { ok: true, randomised: naOrNumber(arm.nRandomised), analysed: naOrNumber(arm.nAnalysed) };
  }

  /* ============================ G06 · block analysis until >=2 SAME-ESTIMAND estimates =========
   * Registry: RM-A02, RM-A01.
   */
  function assertPoolable(trials, opts) {
    var G = "G06";
    var o = opts || {}, min = o.minK === undefined ? 2 : o.minK;
    if (!Array.isArray(trials)) block(G, "TRIALS_MALFORMED", typeof trials);

    var strata = {};
    trials.forEach(function (t) {
      var est = resolveEstimand(t && t.estimandType);      // fail-closed: untagged trial blocks
      (strata[est] = strata[est] || []).push(t);
    });
    var keys = Object.keys(strata);
    if (keys.length === 0) block(G, "NO_ESTIMANDS", "empty trial set");

    var poolable = keys.filter(function (k) { return strata[k].length >= min; });
    if (poolable.length === 0) {
      block(G, "NO_POOLABLE_STRATUM",
        "largest stratum has k=" + Math.max.apply(null, keys.map(function (k) { return strata[k].length; })) +
        " (< " + min + "); report per-trial, do not pool");
    }
    if (o.pooledEstimand !== undefined) {
      var want = resolveEstimand(o.pooledEstimand);
      if (poolable.indexOf(want) === -1) block(G, "REQUESTED_STRATUM_NOT_POOLABLE", want);
      var foreign = keys.filter(function (k) { return k !== want && strata[k].length > 0; });
      return {
        ok: true, pooledEstimand: want, k: strata[want].length,
        heldOut: foreign.map(function (k) {
          return { estimand: k, k: strata[k].length,
                   trials: strata[k].map(function (t) { return (t && (t.name || t.nct)) || "(unnamed)"; }) };
        })
      };
    }
    if (poolable.length > 1) {
      block(G, "MULTIPLE_POOLABLE_STRATA",
        poolable.join(", ") + " — choose one; a single pooled number across strata is not an estimate of anything");
    }
    return { ok: true, pooledEstimand: poolable[0], k: strata[poolable[0]].length, heldOut: [] };
  }

  /* ============================ G07 · clear stale outcome state on selector change ============
   * Registry: RM-B02.  Every scoped field is CLEARED before rebinding. No `??` fallback survives.
   */
  var SCOPED_FIELDS = Object.freeze([
    "tE", "tN", "cE", "cN", "effect", "lci", "uci", "publishedHR", "pubHR",
    "hrLCI", "hrUCI", "md", "se", "estimandType", "scopeClass", "unit",
    "outcomeTitle", "title", "shortLabel", "polarity", "countOutcomeKey", "effectOutcomeKey"
  ]);

  function clearScopedState(data) {
    var out = {};
    Object.keys(data || {}).forEach(function (k) {
      if (SCOPED_FIELDS.indexOf(k) === -1) out[k] = data[k];
    });
    SCOPED_FIELDS.forEach(function (k) { out[k] = null; });
    return out;
  }

  function applyOutcomeScope(trial, scopeKey) {
    var G = "G07";
    var cleared = clearScopedState(trial && trial.data);
    var res = resolveOutcomeScope(trial, scopeKey);
    if (res.blocked) {
      return { data: cleared, included: false, reason: res.reason, detail: res.detail };
    }
    var row = res.row;
    SCOPED_FIELDS.forEach(function (k) {
      cleared[k] = isPresent(row[k]) ? row[k] : null;      // explicit copy, never `??` to the old value
    });
    // Percentages are computed only for patient-count units. RM-A01.
    var unit = norm(cleared.unit);
    cleared.percentagesValid = (unit === "patients");
    if (unit === "events" || unit === "continuous" || unit === "hierarchical") {
      cleared.percentagesValid = false;
    } else if (unit !== "patients") {
      block(G, "UNIT_UNKNOWN", "outcome row unit '" + row.unit + "' is not one of patients|events|continuous|hierarchical");
    }
    return { data: cleared, included: true, reason: "" };
  }

  /* ============================ G08 · safeRob — unknown resolves to "some" ====================
   * Registry: RM-G01, RM-G02.  The shipped sanitiser resolved every unknown to "low", so
   * "some-concerns" (the curated vocabulary) rendered as Low Risk corpus-wide.
   */
  var ROB_ALIASES = Object.freeze({
    "low": "low", "low risk": "low", "l": "low",
    "some": "some", "some-concerns": "some", "some concerns": "some", "someconcerns": "some",
    "unclear": "some", "moderate": "some", "medium": "some", "m": "some",
    "high": "high", "high risk": "high", "serious": "high", "critical": "high", "h": "high"
  });

  function safeRob(rob) {
    if (!Array.isArray(rob)) return ["some", "some", "some", "some", "some"];
    return rob.map(function (r) {
      var v = ROB_ALIASES[norm(r)];
      return v === undefined ? "some" : v;                  // UNKNOWN -> "some", never "low"
    });
  }

  function overallRob(rob) {
    var s = safeRob(rob);
    return s.indexOf("high") !== -1 ? "high" : s.indexOf("some") !== -1 ? "some" : "low";
  }

  /** RM-G02: a RoB judgement requires stored domain answers, not registry design fields. */
  function assertRobAssessed(record) {
    var G = "G08";
    var domains = record && record.rob2Domains;
    if (!Array.isArray(domains) || domains.length === 0) {
      return { ok: false, render: "not assessed", reason: "no RoB 2 domain answers stored" };
    }
    return { ok: true, render: overallRob(domains.map(function (d) { return d && d.judgement; })) };
  }

  /* ============================ G09 · registry concordance ====================================
   * Registry: RM-D01, RM-B06, RM-B07.  NCT must match the trial, and the trial's condition must
   * match the review topic. A registry that could not be reached is NOT CHECKED, never concordant.
   */
  var NCT_RE = /^NCT\d{8}$/;

  function assertRegistryConcordance(row, registry, topicTokens) {
    var G = "G09";
    var nct = row && row.nct;
    if (!isPresent(nct)) return { ok: true, status: "N/A", reason: "no registry identifier — nothing to concord with" };
    if (!NCT_RE.test(String(nct))) block(G, "NCT_MALFORMED", String(nct));
    if (registry === null || registry === undefined) {
      block(G, "REGISTRY_NOT_REACHED", nct + " — 'not checked', never 'concordant'");
    }
    var findings = [];
    var regTitle = norm(registry.briefTitle) + " " + norm(registry.officialTitle);
    var name = norm(row.name);
    if (name && regTitle && regTitle.indexOf(name) === -1) {
      var acronym = name.split(/[^a-z0-9-]+/).filter(function (w) { return w.length > 3; })[0];
      if (!acronym || regTitle.indexOf(acronym) === -1) {
        findings.push({ field: "name", ledger: row.name, registry: registry.briefTitle });
      }
    }
    if (isPresent(row.phase) && isPresent(registry.phases)) {
      var lp = norm(row.phase).replace(/^phase\s*/, "").replace(/i{1,3}|iv/g, function (m) {
        return { i: "1", ii: "2", iii: "3", iv: "4" }[m] || m;
      });
      var rp = [].concat(registry.phases).map(function (p) { return norm(p).replace(/[^0-9]/g, ""); }).join(",");
      if (rp && lp && rp.indexOf(lp) === -1) findings.push({ field: "phase", ledger: row.phase, registry: registry.phases });
    }
    if (Array.isArray(topicTokens) && topicTokens.length && isPresent(registry.conditions)) {
      var conds = [].concat(registry.conditions).map(norm).join(" ");
      var match = topicTokens.some(function (t) { return conds.indexOf(norm(t)) !== -1; });
      if (!match) findings.push({ field: "condition", ledger: topicTokens.join("|"), registry: registry.conditions });
    }
    if (isPresent(registry.armGroupCount) && isPresent(row.armsFitted) &&
        Number(registry.armGroupCount) > Number(row.armsFitted) && !isPresent(row.armDropDisclosure)) {
      findings.push({ field: "arms", ledger: row.armsFitted + " fitted",
                      registry: registry.armGroupCount + " randomised — undisclosed drop" });
    }
    if (findings.length) block(G, "REGISTRY_DISCORDANT", JSON.stringify(findings));
    return { ok: true, status: "CONCORDANT", findings: [] };
  }

  /* ============================ G10 · k-threshold gate on machinery ===========================
   * Registry: RM-H01, RM-H02, RM-H03.  Suppress with an on-panel reason; keep forest + pooled estimate.
   */
  var MACHINERY = Object.freeze({
    funnel:        { minK: 10, scales: null },
    egger:         { minK: 10, scales: null },
    peters:        { minK: 10, scales: ["OR", "RR"] },
    trimfill:      { minK: 10, scales: null },
    copas:         { minK: 15, scales: null },
    metaregression:{ minK: 10, scales: null },
    tsa:           { minK: 5,  scales: null },
    ris:           { minK: 5,  scales: null },
    nma:           { minK: 3,  scales: null, requiresNetwork: true },
    nodesplit:     { minK: 3,  scales: null, requiresNetwork: true, requiresLoop: true },
    cinema:        { minK: 3,  scales: null, requiresNetwork: true },
    leaguetable:   { minK: 3,  scales: null, requiresNetwork: true },
    labbe:         { minK: 2,  scales: ["OR", "RR"], requiresCounts: true },
    nnt:           { minK: 1,  scales: ["OR", "RR"], requiresBaselineRisk: true },
    subgroup:      { minK: 4,  scales: null, minPerSubgroup: 2 },
    prediction:    { minK: 3,  scales: null },
    fragility:     { minK: 1,  scales: ["OR", "RR"], requiresCounts: true, requiresDirect: true, requiresSignificant: true },
    benford:       { minK: 1,  scales: null, minDigits: 30 },
    grim:          { minK: 1,  scales: null, requiresBoundedMean: true }
  });

  function gateMachinery(panel, ctx) {
    var G = "G10";
    var key = norm(panel);
    if (!Object.prototype.hasOwnProperty.call(MACHINERY, key)) block(G, "PANEL_UNKNOWN", String(panel));
    var spec = MACHINERY[key];
    var c = ctx || {};
    if (!isPresent(c.k)) block(G, "K_UNKNOWN", key + " — k must be known before a panel renders");
    var k = Number(c.k);

    function suppress(reason) { return { render: false, panel: key, reason: reason }; }

    if (k < spec.minK) {
      return suppress(spec.minK === 15
        ? "Copas selection modelling requires k >= 15; k = " + k
        : key + " requires k >= " + spec.minK + "; k = " + k + " — not estimable, suppressed rather than shown");
    }
    if (spec.scales && (!isPresent(c.estimand) || spec.scales.indexOf(resolveEstimand(c.estimand)) === -1)) {
      return suppress(key + " is defined for " + spec.scales.join("/") + " only; this analysis is on " +
                      (isPresent(c.estimand) ? resolveEstimand(c.estimand) : "an unresolved") + " scale");
    }
    if (spec.requiresNetwork && !c.hasNetwork) return suppress("no network — this is a pairwise review");
    if (spec.requiresLoop && !c.hasClosedLoop) return suppress("no closed loop — inconsistency is not estimable");
    if (spec.requiresCounts && !c.hasCounts) return suppress(key + " requires an observed 2x2");
    if (spec.requiresDirect && !c.isDirect) {
      return suppress("the fragility index is UNDEFINED for an indirect estimate — unmeasurable, not favourable");
    }
    if (spec.requiresSignificant && !c.isSignificant) return suppress("fragility index undefined: the contrast is not significant");
    if (spec.requiresBaselineRisk && !isPresent(c.baselineRisk)) {
      return suppress("NNT requires an observed baseline risk; deriving one from an assumed rate is not an estimate");
    }
    if (spec.requiresBoundedMean && !c.hasBoundedMean) {
      return { render: false, panel: key, reason: "N/A — no mean of a bounded integer scale to reconstruct", na: true };
    }
    if (spec.minDigits && (!isPresent(c.digits) || Number(c.digits) < spec.minDigits)) {
      return { render: false, panel: key, na: true,
               reason: "UNDERPOWERED — " + (isPresent(c.digits) ? c.digits : 0) + " digits, needs >= " +
                       spec.minDigits + "; cannot test, not 'no signal'" };
    }
    if (spec.minPerSubgroup && isPresent(c.minSubgroupK) && Number(c.minSubgroupK) < spec.minPerSubgroup) {
      return suppress("an interaction test with " + c.minSubgroupK + " trial(s) in a subgroup is not a test");
    }
    return { render: true, panel: key, reason: "" };
  }

  /** RM-H02: estimator admissibility. DL is inadmissible below k=10; tau2/I2 are uninterpretable at k<3. */
  function assertEstimatorAdmissible(estimator, k) {
    var G = "G10";
    if (!isPresent(k)) block(G, "K_UNKNOWN", "estimator admissibility needs k");
    var e = norm(estimator);
    if ((e === "dl" || e === "dersimonian-laird") && Number(k) < 10) {
      block(G, "ESTIMATOR_INADMISSIBLE", "DerSimonian-Laird at k=" + k + "; use REML or Paule-Mandel");
    }
    return { ok: true, reportHeterogeneity: Number(k) >= 3,
             heterogeneityNote: Number(k) < 3 ? "tau^2 and I^2 are not interpretable at k=" + k : "" };
  }

  /* ============================ G11 · no verification claim over an unsourced field ===========
   * Registry: RM-F07, RM-H05, RM-J01, RM-J02.
   */
  var DASH_SOURCE_RE = /^\s*(--|—|–|n\/?a|tbd|unknown|\?+)\s*$/i;

  function assertVerificationClaim(record) {
    var G = "G11";
    var src = record && record.source;
    var claim = record && record.verificationClaim;
    if (!isPresent(claim)) return { ok: true, tier: record && record.tier };
    if (!isPresent(src) || DASH_SOURCE_RE.test(String(src))) {
      block(G, "UNEARNED_VERIFICATION", "'" + claim + "' on a field whose source is " + JSON.stringify(src));
    }
    if (/100\s*%|\bverified\b|\bvalidated\b/i.test(String(claim)) && !isPresent(record.quotedSourceText)) {
      block(G, "VERIFICATION_WITHOUT_QUOTE", "'" + claim + "' without a quoted source field");
    }
    return { ok: true, tier: record.tier };
  }

  var VALID_TIERS = Object.freeze(["VERIFIED_FULL", "VERIFIED_DENOM_ONLY", "SECONDARY_CORROBORATED", "UNSOURCED", "FINDING"]);
  function assertTier(tier) {
    if (!isPresent(tier) || VALID_TIERS.indexOf(String(tier)) === -1) {
      block("G11", "TIER_MISSING_OR_UNKNOWN", String(tier));
    }
    return String(tier);
  }

  /** RM-H05: a benchmark may only validate the scope it actually covers. */
  function assertBenchmarkScope(benchmark, selectedScope) {
    var G = "G11";
    if (!benchmark) block(G, "BENCHMARK_MISSING", "external-validation claim with no benchmark record");
    if (!isPresent(benchmark.scope)) block(G, "BENCHMARK_SCOPE_MISSING", "benchmark carries no declared scope");
    if (norm(benchmark.scope) !== norm(selectedScope)) {
      block(G, "BENCHMARK_SCOPE_MISMATCH",
        "benchmark scope '" + benchmark.scope + "' cannot validate the '" + selectedScope + "' analysis");
    }
    if (isPresent(benchmark.k) && Array.isArray(benchmark.trials) && Number(benchmark.k) !== benchmark.trials.length) {
      block(G, "BENCHMARK_SELF_INCONSISTENT",
        "benchmark k=" + benchmark.k + " against " + benchmark.trials.length + " trials named in its own scope string");
    }
    return { ok: true };
  }

  /**
   * RM-J01 / RM-J02 — protocol-provenance text.
   * Mahmood's ruling: KEEP the git-timestamp mechanism as a tamper-evident public-push protocol
   * record. Drop ONLY the false ICMJE attribution and the literal PROSPERO-equivalence label.
   * This guard therefore BLOCKS the false parts AND BLOCKS deletion of the mechanism.
   */
  var ICMJE_ATTRIBUTION_RE = /\bICMJE\b/i;
  var PROSPERO_EQUIV_RE = /(equivalent\s+to|constitutes?\s+a[^.]{0,40}equivalent|same\s+as)[^.]{0,60}PROSPERO|PROSPERO[^.]{0,30}\bequivalent\b/i;
  var MECHANISM_RE = /(tamper[- ]evident|merkle|public\s+push|publicly[- ]push)/i;
  // A NEGATED occurrence ("NOT prospectively registered") is the honest statement we require, so it
  // is stripped before the positive claim is tested. A lookahead cannot do this — the negation sits
  // BEFORE the phrase.
  var NEGATED_PROSPECTIVE_RE = /\b(not|never|no(?:t)?\s+been|is\s+not|was\s+not)\s+prospectively\s+registered\b/gi;
  var PROSPECTIVE_CLAIM_RE = /\bprospectively\s+registered\b/i;

  function assertProtocolProvenance(text, opts) {
    var G = "G11";
    var t = String(text || "");
    var o = opts || {};
    if (ICMJE_ATTRIBUTION_RE.test(t)) {
      block(G, "FALSE_ICMJE_ATTRIBUTION",
        "ICMJE has no systematic-review registration requirement; the claim must stand on its own merits");
    }
    if (PROSPERO_EQUIV_RE.test(t)) {
      block(G, "FALSE_PROSPERO_EQUIVALENCE", "a git record is a different mechanism, not an equivalent one");
    }
    if (o.requireMechanism !== false && !MECHANISM_RE.test(t)) {
      block(G, "MECHANISM_DELETED",
        "the tamper-evident public-push mechanism must survive; deleting it over-corrects (see ARNI 554b6f2a2 -> ce187425e)");
    }
    if (o.retrospective === true && PROSPECTIVE_CLAIM_RE.test(t.replace(NEGATED_PROSPECTIVE_RE, ""))) {
      block(G, "RETROSPECTIVE_FRAMED_AS_PROSPECTIVE",
        "this protocol was written alongside the analysis; no mechanism, git included, makes it prospective");
    }
    return { ok: true };
  }

  /* ============================ G12 · verdict-badge parity ====================================
   * Registry: RM-F01, RM-F02, RM-F03, RM-F04, RM-H04.
   * Both surfaces or neither. A green badge over a non-STABLE verdict, a non-zero P1/P2 counter,
   * a non-empty reasons[], or an empty ledger is a BLOCK.
   */
  var GREEN_HEXES = Object.freeze(["#15803d", "#0a7d33", "#166534", "#14532d"]);
  var PASS_PHRASES = Object.freeze(["checks passed", "internal checks passed", "evidence grade: verified", "✓ verified"]);

  /**
   * Strip a badge's AUDIT TRAIL before reading it as a live claim.
   *
   * An honest badge QUOTES the claim it replaced - "It read <<INTERNAL CHECKS PASSED ... Trials: 2>>
   * on a green background, and the page's own verdict said STABLE". Reading that as an assertion
   * makes the guard flag the corrected app instead of the broken one, which is what happened on
   * LISINOPRIL_HTN in the render test. The HFrEF precedent: a superseded value is gone EXCEPT
   * where the correction itself is documented.
   */
  var RETENTION_MARKER_RE = new RegExp(
    "(what this badge used to say|used to say|previously read|it read|the previous (visible )?badge read"
    + "|this badge previously|was wrong|replaced the claim|quoted verbatim|round[_ ]?1[_ ]?error)", "i");

  function stripAuditTrail(text) {
    var t = String(text || "");
    var m = RETENTION_MARKER_RE.exec(t);
    if (m) t = t.slice(0, m.index);                 // narrative is appended; drop from the marker on
    t = t.replace(/[\u201C\u2018][^\u201D\u2019]{0,400}[\u201D\u2019]/g, " ");  // curly-quoted spans
    t = t.replace(/&ldquo;[\s\S]{0,400}?&rdquo;/gi, " ");
    return t;
  }

  function summariseVerdict(verdict) {
    var v = verdict || {};
    var counts = v.counts || {};
    var open = 0;
    Object.keys(counts).forEach(function (k) {
      if (/^P[012]_/.test(k) && Number(counts[k]) > 0) open += Number(counts[k]);
    });
    return {
      word: String(v.verdict || "").toUpperCase(),
      openFindings: open,
      reasons: Array.isArray(v.reasons) ? v.reasons.length : 0,
      trials: isPresent(counts.n_trials_seen) ? Number(counts.n_trials_seen) : null
    };
  }

  function assertVerdictParity(verdict, badge, ledger) {
    var G = "G12";
    var s = summariseVerdict(verdict);
    var b = badge || {};
    var bg = norm(b.background);
    var text = norm(stripAuditTrail(b.text));       // quoted prior claims are not live claims
    var isGreen = GREEN_HEXES.indexOf(bg) !== -1;
    var claimsPass = PASS_PHRASES.some(function (p) { return text.indexOf(p) !== -1; });
    var ledgerTrials = ledger && isPresent(ledger.trialCount) ? Number(ledger.trialCount) : null;

    if ((isGreen || claimsPass)) {
      if (s.word !== "STABLE") block(G, "FALSE_GREEN_VERDICT", "badge asserts a pass over verdict '" + s.word + "'");
      if (s.openFindings > 0) block(G, "FALSE_GREEN_FINDINGS", "badge asserts a pass over " + s.openFindings + " open finding(s)");
      if (s.reasons > 0) block(G, "FALSE_GREEN_REASONS", "badge asserts a pass over " + s.reasons + " verdict reason(s)");
      if (s.trials === 0 || ledgerTrials === 0) block(G, "FALSE_GREEN_EMPTY", "badge asserts a pass over an empty ledger");
    }
    if (s.trials !== null && ledgerTrials !== null && s.trials !== ledgerTrials) {
      block(G, "TRIAL_COUNT_DISAGREEMENT", "__verdict says " + s.trials + ", ledger holds " + ledgerTrials);
    }
    if (isPresent(b.trialCount)) {
      if (s.trials !== null && Number(b.trialCount) !== s.trials) {
        block(G, "TRIAL_COUNT_DISAGREEMENT", "badge says " + b.trialCount + ", __verdict says " + s.trials);
      }
      if (ledgerTrials !== null && Number(b.trialCount) !== ledgerTrials) {
        block(G, "TRIAL_COUNT_DISAGREEMENT", "badge says " + b.trialCount + ", ledger holds " + ledgerTrials);
      }
    }
    // RM-F03: the badge must not contradict itself.
    var self = assertBadgeSelfConsistent(b.text);
    // RM-H04: an N/A gate must not be reported as a zero.
    if (b.naGates && b.naGates.length) {
      b.naGates.forEach(function (g) {
        if (!isPresent(b.naReasons && b.naReasons[g])) {
          block(G, "NA_REPORTED_AS_PASS", g + " is N/A and must be printed with its reason, not as 0");
        }
      });
    }
    return { ok: true, verdict: s, selfConsistent: self.ok };
  }

  function assertBadgeSelfConsistent(text) {
    var G = "G12";
    var t = stripAuditTrail(text);
    function uniqueNumbers(re) {
      var set = {}, m, n = 0;
      var r = new RegExp(re.source, re.flags.indexOf("g") === -1 ? re.flags + "g" : re.flags);
      while ((m = r.exec(t)) !== null) { if (!set[m[1]]) { set[m[1]] = true; n++; } }
      return { count: n, values: Object.keys(set) };
    }
    var trials = uniqueNumbers(/Trials?\s*:?\s*<?\/?[a-z]*>?\s*(\d+)/i);
    if (trials.count > 1) block(G, "BADGE_SELF_CONTRADICTION", "two trial counts in one badge: " + trials.values.join(" vs "));
    var rounds = uniqueNumbers(/(\d+)\s+internal-consistency rounds/i);
    if (rounds.count > 1) block(G, "BADGE_SELF_CONTRADICTION", "two round counts in one badge: " + rounds.values.join(" vs "));
    var ks = uniqueNumbers(/\bk\s*=\s*(\d+)/i);
    if (ks.count > 1) block(G, "BADGE_SELF_CONTRADICTION", "two k values in one badge: " + ks.values.join(" vs "));
    return { ok: true };
  }

  /* ============================ G13 · app identity ============================================
   * Registry: RM-D06.  Filename, title and ledger group must describe the same subject.
   */
  function tokenise(s) {
    return norm(s).split(/[^a-z0-9]+/).filter(function (w) { return w.length > 3; });
  }

  function assertAppIdentity(filenameStem, title, ledgerGroup) {
    var G = "G13";
    if (!isPresent(title)) block(G, "TITLE_MISSING", "an app must declare its subject in <title>");
    var stem = tokenise(String(filenameStem).replace(/_(auto)?_?(full)?_?review$/i, ""));
    var haystack = norm(title) + " " + norm(ledgerGroup || "");
    var hit = stem.some(function (tok) { return haystack.indexOf(tok) !== -1; });
    if (!hit && stem.length) {
      block(G, "IDENTITY_MISMATCH",
        "filename tokens [" + stem.join(", ") + "] appear in neither the title nor the ledger group — " +
        "the published URL would cite a different subject from the content");
    }
    return { ok: true };
  }

  /* ============================ G14 · template-contamination blocklist ========================
   * Registry: RM-E01, RM-E02, RM-D05.
   */
  var CONTAMINATION_CLASSES = Object.freeze([
    { id: "sglt2", tokens: ["sglt2", "sglt-2", "dapagliflozin", "empagliflozin", "sotagliflozin",
                            "dapa-hf", "emperor-reduced", "emperor-preserved", "empa-reg", "deliver trial"] },
    { id: "sglt2_ae", tokens: ["fournier", "genital mycotic", "diabetic ketoacidosis"] },
    { id: "mra", tokens: ["finerenone", "fidelio", "figaro", "spironolactone", "eplerenone",
                          "mineralocorticoid receptor antagonist"] },
    { id: "ckd", tokens: ["egfr slope", "uacr", "kidney failure composite"] },
    { id: "arni", tokens: ["sacubitril", "paradigm-hf", "paragon-hf", "paradise-mi", "paraglide-hf", "entresto"] },
    { id: "mace", tokens: ["3-point mace", "4-point mace"] }
  ]);

  // The sacubitril/valsartan alias table baked into 526 apps (RM-E02).
  var FOREIGN_ALIAS_NCTS = Object.freeze(["NCT01035255", "NCT01920711", "NCT02924727", "NCT03988634"]);

  function assertNoContamination(text, topicTokens, opts) {
    var G = "G14";
    var t = norm(text);
    var o = opts || {};
    var topic = (Array.isArray(topicTokens) ? topicTokens : []).map(norm);
    var findings = [];

    CONTAMINATION_CLASSES.forEach(function (cls) {
      // A class is legitimate when the app's own topic names it.
      var owned = cls.tokens.some(function (tok) {
        return topic.some(function (tt) { return tt.indexOf(tok) !== -1 || tok.indexOf(tt) !== -1; });
      });
      if (owned) return;
      cls.tokens.forEach(function (tok) {
        if (t.indexOf(tok) !== -1) findings.push({ cls: cls.id, token: tok });
      });
    });

    var ownsArni = topic.some(function (tt) {
      return ["sacubitril", "arni", "entresto", "valsartan"].some(function (a) { return tt.indexOf(a) !== -1; });
    });
    if (!ownsArni) {
      FOREIGN_ALIAS_NCTS.forEach(function (n) {
        if (String(text || "").indexOf(n) !== -1) findings.push({ cls: "foreign_trial_registry", token: n });
      });
    }

    // The repo's own asset/URL namespace is not contamination.
    findings = findings.filter(function (f) {
      if (f.token !== "finerenone") return true;
      return !(o.allowRepoUrl !== false && /rapidmeta-finerenone/i.test(String(text || "")));
    });

    if (findings.length) block(G, "TEMPLATE_CONTAMINATION", JSON.stringify(findings.slice(0, 12)));
    return { ok: true, findings: [] };
  }

  /* ============================ G15 · registry value extraction ===============================
   * Registry: RM-A06 (rate read as a proportion), RM-C03 (arm orientation).
   */
  var RATE_UNIT_RE = /(per|\/)\s*100[- ]?(pt|patient|person)[- ]?year|percentage\s+per\s+year|per\s+100\s+person[- ]?years|events?\s*\/\s*(pt|patient|person)[- ]?year/i;
  var PROPORTION_UNIT_RE = /^percentage of participants$|^percent of participants$|^proportion of participants$/i;

  function countFromPostedOutcome(value, unitOfMeasure, denominator) {
    var G = "G15";
    if (!isPresent(unitOfMeasure)) block(G, "UNIT_OF_MEASURE_MISSING", "read unitOfMeasure before using a posted value");
    var u = String(unitOfMeasure).trim();
    if (RATE_UNIT_RE.test(u)) {
      block(G, "RATE_IS_NOT_A_PROPORTION",
        "'" + u + "' is an incidence rate over person-time; value x denominator / 100 fabricates a count");
    }
    if (/^count of participants$|^participants$|^number of participants$/i.test(u)) {
      if (!isPresent(value)) block(G, "VALUE_MISSING", u);
      return { count: Number(value), derivation: "posted directly as a participant count", unit: u };
    }
    if (PROPORTION_UNIT_RE.test(u)) {
      if (!isPresent(value) || !isPresent(denominator)) block(G, "VALUE_OR_DENOMINATOR_MISSING", u);
      return {
        count: Number(value) * Number(denominator) / 100,
        derivation: Number(value) + "% x " + denominator + " / 100",
        unit: u
      };
    }
    block(G, "UNIT_NOT_RECOGNISED", "'" + u + "' — refusing to guess whether this is a proportion or a rate");
  }

  function bindArmByTitle(registryGroups, wantTitleFragment) {
    var G = "G15";
    if (!Array.isArray(registryGroups) || !registryGroups.length) block(G, "REGISTRY_GROUPS_MISSING", "");
    if (!isPresent(wantTitleFragment)) block(G, "ARM_TITLE_REQUIRED", "arms bind by title, never by index");
    var want = norm(wantTitleFragment);
    var hits = registryGroups.filter(function (g) { return norm(g && g.title).indexOf(want) !== -1; });
    if (hits.length === 0) block(G, "ARM_TITLE_NOT_FOUND", wantTitleFragment);
    if (hits.length > 1) block(G, "ARM_TITLE_AMBIGUOUS", wantTitleFragment + " matches " + hits.length + " groups");
    return hits[0];
  }

  /* ============================ G16 · co-render the sensitivity interval ======================
   * Registry: RM-F08.
   */
  function assertIntervalCoRender(headline, sensitivity, surfaceText) {
    var G = "G16";
    if (!sensitivity || !isPresent(sensitivity.lci) || !isPresent(sensitivity.uci)) return { ok: true, required: false };
    var crossesNull = Number(sensitivity.lci) <= 1 && Number(sensitivity.uci) >= 1;
    var headlineCrosses = headline && isPresent(headline.lci) && isPresent(headline.uci) &&
                          Number(headline.lci) <= 1 && Number(headline.uci) >= 1;
    if (!crossesNull || headlineCrosses) return { ok: true, required: false };
    var t = String(surfaceText || "");
    var shown = t.indexOf(String(sensitivity.lci)) !== -1 && t.indexOf(String(sensitivity.uci)) !== -1;
    if (!shown) {
      block(G, "SENSITIVITY_INTERVAL_HIDDEN",
        (sensitivity.label || "the sensitivity interval") + " (" + sensitivity.lci + "-" + sensitivity.uci +
        ") crosses 1 while the headline does not, and is not rendered on the same surface");
    }
    return { ok: true, required: true };
  }

  /* ============================ G17 · direction awareness ====================================
   * Registry: RM-I01, RM-I02.  Every outcome carries an explicit polarity; direction words are
   * DERIVED, never hardcoded. A pool of mixed polarity blocks.
   */
  var POLARITIES = Object.freeze(["benefit", "harm", "neutral"]);

  function assertPolarity(row) {
    var G = "G17";
    var p = norm(row && row.polarity);
    if (POLARITIES.indexOf(p) === -1) {
      block(G, "POLARITY_MISSING",
        "outcome '" + ((row && (row.title || row.shortLabel)) || "?") +
        "' has no polarity; an OR<1 on a GOOD outcome means the intervention is WORSE");
    }
    return p;
  }

  /**
   * polarity "benefit"  = the event is bad, so effect < 1 favours the intervention (death, bleeding).
   * polarity "harm"     = the event is good, so effect < 1 means the intervention is WORSE
   *                       (culture conversion, treatment completion).
   */
  function directionWord(effect, polarity) {
    var G = "G17";
    var p = assertPolarity({ polarity: polarity, title: "(direct call)" });
    if (!isPresent(effect)) block(G, "EFFECT_MISSING", "no direction without an effect");
    var e = Number(effect);
    if (!Number.isFinite(e) || e <= 0) block(G, "EFFECT_NOT_A_RATIO", String(effect));
    if (p === "neutral") return "no directional interpretation declared";
    var favoursIntervention = (p === "benefit") ? (e < 1) : (e > 1);
    if (Math.abs(e - 1) < 1e-12) return "no difference";
    return favoursIntervention ? "favours the intervention" : "favours the comparator";
  }

  /** NNH may only be rendered for a harm-direction result. RM-I01. */
  function assertNntNnhLabel(kind, effect, polarity) {
    var G = "G17";
    var word = directionWord(effect, polarity);
    var k = norm(kind);
    if (k !== "nnt" && k !== "nnh") block(G, "NNT_KIND_UNKNOWN", String(kind));
    if (k === "nnh" && word === "favours the intervention") {
      block(G, "NNH_ON_A_BENEFIT", "an NNH cannot be rendered for a result that favours the intervention");
    }
    if (k === "nnt" && word === "favours the comparator") {
      block(G, "NNT_ON_A_HARM", "an NNT cannot be rendered for a result that favours the comparator");
    }
    return { ok: true, direction: word };
  }

  function assertPoolPolarityConsistent(rows) {
    var G = "G17";
    if (!Array.isArray(rows) || !rows.length) block(G, "ROWS_MISSING", "");
    var seen = {};
    rows.forEach(function (r) { seen[assertPolarity(r)] = true; });
    var keys = Object.keys(seen).filter(function (k) { return k !== "neutral"; });
    if (keys.length > 1) {
      block(G, "MIXED_POLARITY_POOL",
        "a good outcome and a bad outcome on one scale: " + keys.join(" + ") + " — no sign reconciliation exists");
    }
    return { ok: true, polarity: keys[0] || "neutral" };
  }

  /* ============================ G18 · FAIL-CLOSED INTEGRITY GATE ==============================
   * Registry: RM-J07, RM-D10.
   * Adopted verbatim from the bempedoic reviewer's recommendation #9. The gate must FAIL, not
   * warn, whenever any of these hold. A "checks passed / 100-100 integrity / fabrication-risk
   * 0.200" rendered over any of them is itself the bug.
   */
  function assertIntegrityGate(state) {
    var G = "G18";
    var s = state || {};
    var fails = [];

    // 1. any trial id null, empty or NULLED
    (s.trialIds || []).forEach(function (id) {
      var v = String(id === null || id === undefined ? "" : id).trim();
      if (!v) fails.push("a trial id is null/empty");
      else if (/^NULLED/i.test(v)) fails.push("trial id '" + v + "' is a NULLED placeholder");
    });

    // 2. a composite endpoint mismatched across pooled rows
    if (Array.isArray(s.pooledRows) && s.pooledRows.length > 1) {
      var sets = {};
      s.pooledRows.forEach(function (r) {
        var comps = (r && r.components) || null;
        var key = Array.isArray(comps) ? comps.map(norm).slice().sort().join("|") : "(undeclared)";
        (sets[key] = sets[key] || []).push((r && r.trial) || "(unnamed)");
      });
      var keys = Object.keys(sets);
      if (keys.indexOf("(undeclared)") !== -1) {
        fails.push("a pooled row declares no composite component set");
      }
      if (keys.length > 1) {
        fails.push("composite component sets differ across pooled rows: " +
          keys.map(function (k) { return "[" + k + "] " + sets[k].join(","); }).join(" vs "));
      }
    }

    // 3. any analysis output NaN or an impossible value
    (s.outputs || []).forEach(function (o) {
      var name = (o && o.name) || "(unnamed)";
      var v = o && o.value;
      if (v === null || v === undefined || (typeof v === "number" && !Number.isFinite(v))) {
        fails.push(name + " is NaN/undefined");
        return;
      }
      if (o && o.isRatio) {
        var n = Number(v);
        if (!Number.isFinite(n) || n <= 0 || n < RATIO_MIN || n > RATIO_MAX) {
          fails.push(name + " = " + v + " is not a possible ratio");
        }
      }
      if (o && Array.isArray(o.interval) &&
          o.interval.some(function (x) { return x === null || !Number.isFinite(Number(x)); })) {
        fails.push(name + " interval contains NaN");
      }
    });

    // 4. trial counts or N disagreeing across surfaces
    ["trialCounts", "participantCounts"].forEach(function (field) {
      var vals = (s[field] || []).filter(isPresent).map(Number);
      var uniq = vals.filter(function (v, i) { return vals.indexOf(v) === i; });
      if (uniq.length > 1) {
        fails.push(field + " disagree across surfaces: " + uniq.join(" vs "));
      }
    });

    if (fails.length) {
      block(G, "INTEGRITY_GATE_FAILED", fails.join("; "));
    }
    if (s.claimsPass && s.untested) {
      block(G, "UNEARNED_PASS", "the gate claims a pass without having run: " + s.untested);
    }
    return { ok: true, checked: 4 };
  }

  /* ============================ G19 · composite component sets must match ====================
   * Registry: RM-A13. MACE-3 and MACE-4 are different constructs; so are CV-death and CHD-death
   * composites. Each pooled row must DECLARE its components, and they must be identical.
   */
  function assertCompositeComponentsMatch(rows) {
    var G = "G19";
    if (!Array.isArray(rows) || rows.length < 2) return { ok: true, checked: false };
    var first = null, firstTrial = "";
    for (var i = 0; i < rows.length; i++) {
      var r = rows[i] || {};
      if (!Array.isArray(r.components) || !r.components.length) {
        block(G, "COMPONENTS_UNDECLARED",
          (r.trial || "row " + i) + " does not declare its composite component set; " +
          "an undeclared composite cannot be shown to match another");
      }
      var key = r.components.map(norm).slice().sort().join("|");
      if (first === null) { first = key; firstTrial = r.trial || ("row " + i); }
      else if (key !== first) {
        block(G, "COMPONENT_SET_MISMATCH",
          (r.trial || "row " + i) + " [" + key + "] vs " + firstTrial + " [" + first + "]");
      }
    }
    return { ok: true, checked: true, components: first.split("|") };
  }

  /* ============================ G20 · the watchlist must be the app's own topic ===============
   * Registry: RM-E03. Distinct from G14: this is the LIVE monitoring surface — the trials the
   * app says it is watching for new evidence — not prose residue.
   */
  function assertWatchlistOnTopic(watchlist, topicTokens) {
    var G = "G20";
    if (!Array.isArray(watchlist) || !watchlist.length) return { ok: true, checked: false };
    var topic = (Array.isArray(topicTokens) ? topicTokens : []).map(norm);
    if (!topic.length) block(G, "TOPIC_UNKNOWN", "cannot check a watchlist without the app's topic");
    var foreign = watchlist.filter(function (w) {
      var hay = norm((w && (w.label || w.name)) || w) + " " + norm((w && w.drug) || "");
      return !topic.some(function (t) { return hay.indexOf(t) !== -1 || t.indexOf(hay) !== -1; });
    });
    if (foreign.length === watchlist.length) {
      block(G, "WATCHLIST_WRONG_TOPIC",
        "every monitored trial is off-topic: " +
        foreign.map(function (w) { return (w && (w.label || w.name)) || w; }).slice(0, 8).join(", "));
    }
    if (foreign.length) {
      block(G, "WATCHLIST_PARTIALLY_FOREIGN",
        foreign.length + " of " + watchlist.length + " monitored trials are off-topic: " +
        foreign.map(function (w) { return (w && (w.label || w.name)) || w; }).slice(0, 6).join(", "));
    }
    return { ok: true, checked: true };
  }
  /* ============================ G21 · PERSISTED STATE MAY NOT RESURRECT A WITHDRAWN ROW =======
   * Registry: RM-B09.
   *
   * Found by RENDERING, not by reading the file (commit 9d37dce08). Emptying `realData` stops a
   * FRESH visitor pooling withdrawn rows, but the engine persists `state.trials` to localStorage:
   * a reader who opened the page BEFORE the fix keeps the old auto-seeded rows and is still shown
   * the withdrawn pooled estimate. Reproduced in the browser - a stale profile still rendered
   * RR 0.03 (0.00-0.52) after realData was emptied.
   *
   * The per-app remedy was a one-off migration (_migrated_v123_quarantine_purge). That does not
   * generalise: it only purges ids the app already knows are quarantined. This guard is the
   * general form - persisted state is RECONCILED against the current authoritative ledger on
   * every hydrate, and a ledger that has changed forces a re-derivation rather than a restore.
   */
  function reconcilePersistedState(persisted, authoritative) {
    var G = "G21";
    var p = persisted || {};
    var a = authoritative || {};
    if (!isPresent(a.ledgerFingerprint)) {
      block(G, "LEDGER_FINGERPRINT_MISSING",
        "the authoritative ledger must carry a fingerprint, or a stale profile cannot be detected");
    }
    var realIds = {}, quarantinedIds = {};
    (a.realDataIds || []).forEach(function (id) { realIds[String(id).toUpperCase()] = true; });
    (a.quarantinedIds || []).forEach(function (id) { quarantinedIds[String(id).toUpperCase()] = true; });

    var rows = Array.isArray(p.trials) ? p.trials : [];
    var dropped = [], purged = [], kept = [];
    rows.forEach(function (t) {
      var id = String((t && t.id) || "").toUpperCase();
      if (!id) { dropped.push({ id: "(none)", why: "persisted row has no id" }); return; }
      if (quarantinedIds[id]) {
        purged.push({ id: id, why: "quarantined in the authoritative ledger" });
        return;
      }
      if (!realIds[id]) {
        dropped.push({ id: id, why: "absent from the authoritative ledger" });
        return;
      }
      kept.push(id);
    });

    var stale = String(p.ledgerFingerprint || "") !== String(a.ledgerFingerprint);
    var changed = dropped.length > 0 || purged.length > 0 || stale;

    // A persisted RESULT may never be restored once anything changed - it must be re-derived.
    var mustRederive = changed || isPresent(p.pooledResult);

    return {
      ok: true,
      trials: rows.filter(function (t) {
        return kept.indexOf(String((t && t.id) || "").toUpperCase()) !== -1;
      }),
      dropped: dropped,
      purged: purged,
      staleLedger: stale,
      mustRederive: mustRederive,
      // never carry a persisted pooled estimate forward
      pooledResult: null,
      ledgerFingerprint: a.ledgerFingerprint,
      reason: changed
        ? ("persisted profile reconciled against the current ledger: " +
           purged.length + " quarantined row(s) purged, " + dropped.length +
           " unknown row(s) dropped" + (stale ? ", ledger fingerprint changed" : "") +
           "; the analysis is re-derived, not restored")
        : ""
    };
  }

  /**
   * The assertion form, for a verifier: a corrected app MUST NOT be able to show a withdrawn
   * estimate to a returning visitor.
   */
  function assertNoResurrection(persisted, authoritative) {
    var G = "G21";
    var r = reconcilePersistedState(persisted, authoritative);
    if (r.purged.length && !r.mustRederive) {
      block(G, "WITHDRAWN_ROW_RESURRECTED",
        r.purged.map(function (x) { return x.id; }).join(", "));
    }
    if (isPresent((persisted || {}).pooledResult) && r.pooledResult !== null) {
      block(G, "PERSISTED_RESULT_RESTORED", "a stored pooled estimate was carried forward");
    }
    return r;
  }

  /** A stable fingerprint of the authoritative ledger. Any change invalidates a saved profile. */
  function ledgerFingerprint(realDataIds, quarantinedIds, version) {
    var src = (realDataIds || []).map(String).sort().join(",") + "|" +
              (quarantinedIds || []).map(String).sort().join(",") + "|" + String(version || "");
    var h = 2166136261;
    for (var i = 0; i < src.length; i++) {
      h ^= src.charCodeAt(i);
      h = (h * 16777619) >>> 0;
    }
    return "lf1_" + h.toString(36);
  }
  /* ------------------------------------------------------------------ export */

  return {
    // core
    GuardBlock: GuardBlock, attempt: attempt, isPresent: isPresent, NA: NA,
    ESTIMANDS: ESTIMANDS, RATIO_MODELS: RATIO_MODELS, resolveEstimand: resolveEstimand,
    // guards
    G01_assertRatioModelInput: assertRatioModelInput,
    G02_labelForEstimator: labelForEstimator,
    G03_resolveOutcomeScope: resolveOutcomeScope,
    G04_assertCountsMatchEffect: assertCountsMatchEffect,
    G05_naOrNumber: naOrNumber,
    G05_renderPercent: renderPercent,
    G05_renderPrismaStage: renderPrismaStage,
    G05_assertPrismaCoherent: assertPrismaCoherent,
    G05_assertDenominatorLabelled: assertDenominatorLabelled,
    G06_assertPoolable: assertPoolable,
    G07_clearScopedState: clearScopedState,
    G07_applyOutcomeScope: applyOutcomeScope,
    G08_safeRob: safeRob,
    G08_overallRob: overallRob,
    G08_assertRobAssessed: assertRobAssessed,
    G09_assertRegistryConcordance: assertRegistryConcordance,
    G10_gateMachinery: gateMachinery,
    G10_assertEstimatorAdmissible: assertEstimatorAdmissible,
    G11_assertVerificationClaim: assertVerificationClaim,
    G11_assertTier: assertTier,
    G11_assertBenchmarkScope: assertBenchmarkScope,
    G11_assertProtocolProvenance: assertProtocolProvenance,
    G12_assertVerdictParity: assertVerdictParity,
    G12_assertBadgeSelfConsistent: assertBadgeSelfConsistent,
    G12_stripAuditTrail: stripAuditTrail,
    G13_assertAppIdentity: assertAppIdentity,
    G14_assertNoContamination: assertNoContamination,
    G15_countFromPostedOutcome: countFromPostedOutcome,
    G15_bindArmByTitle: bindArmByTitle,
    G16_assertIntervalCoRender: assertIntervalCoRender,
    G17_assertPolarity: assertPolarity,
    G17_directionWord: directionWord,
    G17_assertNntNnhLabel: assertNntNnhLabel,
    G17_assertPoolPolarityConsistent: assertPoolPolarityConsistent,
    G18_assertIntegrityGate: assertIntegrityGate,
    G19_assertCompositeComponentsMatch: assertCompositeComponentsMatch,
    G20_assertWatchlistOnTopic: assertWatchlistOnTopic,
    G21_reconcilePersistedState: reconcilePersistedState,
    G21_assertNoResurrection: assertNoResurrection,
    G21_ledgerFingerprint: ledgerFingerprint
  };
});
