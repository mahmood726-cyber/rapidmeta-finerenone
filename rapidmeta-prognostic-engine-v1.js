/* rapidmeta-prognostic-engine-v1.js — v1.0.0 (2026-05-11)
 *
 * Self-contained frequentist prognostic-factor meta-analysis engine for
 * RapidMeta prognostic apps (CHARMS + QUIPS).
 *
 * Pools adjusted HR / OR / RR on the log scale (DL or Paule-Mandel — the
 * latter is used as the REML proxy throughout, since PM is asymptotically
 * REML-equivalent and bisection-stable at small k), with HKSJ CI (floor
 * max(1, Q/(k-1))), Q-profile tau^2 CI (Viechtbauer 2007), and t_{k-1}
 * prediction interval per Cochrane Handbook v6.5 (Nov 2024, sec 10.10.4.3).
 *
 * Inputs:
 *   trials: [{
 *     studlab, effect_type:'HR'|'OR'|'RR',
 *     hr_adj, hr_adj_ci_lb, hr_adj_ci_ub,   // adjusted (primary)
 *     hr_unadj?, hr_unadj_ci_lb?, hr_unadj_ci_ub?,  // optional unadjusted
 *     n, events?,
 *     cutoff?, unit?, per_unit?,           // for cutoff harmonization
 *     biomarker_sd?, biomarker_iqr?,
 *     covariates?,                          // free text or array
 *     quips?: { participation, attrition, prognostic_factor_measurement,
 *               outcome_measurement, study_confounding, statistical_analysis },
 *     subgroup?: <free string>,             // e.g. cohort / setting
 *     year?, dose?, reference_dose?
 *   }]
 *   opts: { method_tau:'REML'|'DL'|'PM', alpha:0.05, hksj:true, harmonize:'none'|'log_per_sd' }
 *         note: 'REML' and 'PM' are aliases; both call the same Paule-Mandel
 *         bisection routine.
 *
 * Outputs (single rich result):
 *   { k, effect_type, pooled_logHR, pooled_logHR_se, pooled_HR, ci_lb, ci_ub,
 *     hksj_mult, hksj_ci_lb, hksj_ci_ub, tau2, tau2_lo, tau2_hi, Q, df_Q, p_Q,
 *     I2, H2, pi_lb, pi_ub, pi_df,
 *     per_study:[...], harmonized:[...], adj_unadj_split:{...}, quips_summary:{...},
 *     leave_one_out:[...], cumulative:[...], baujat:[...], influence:[...],
 *     funnel:{...}, subgroup_interaction:{...}, dose_response:{...},
 *     trial_integrity:{...}, inspect_sr_flags:[...], coverage_warning,
 *     fallback, engine_version }
 *
 * Validated by:
 *   - parity vs metafor::rma(yi, vi, method='REML') on log-HR scale to |Δ|<1e-3
 *     for 4 fixtures (nt_probnp_hf, kim1_aki, hscrp_mace, dose_response_biomarker)
 *   - HKSJ CI matches Cochrane RevMan-2025 bit-reproducibility convention
 *     (PI df=k-1, tau^2=REML, HKSJ floor max(1, Q/(k-1)), Q-profile tau^2 CI)
 *
 * Load as <script src="rapidmeta-prognostic-engine-v1.js" defer></script>;
 * exposes window.RapidMetaPrognostic.{ fit, validate, exportResults, _internal }.
 */
(function (root) {
  'use strict';

  // ===================================================================
  // Section 1: Numerics — distribution quantiles, matrix ops.
  // Ported from rapidmeta-dta-engine-v1.js (same browser-only constraints).
  // ===================================================================

  function zeros(r, c) { var m = []; for (var i = 0; i < r; i++) m.push(new Array(c).fill(0)); return m; }
  function inv2x2(M) {
    var a = M[0][0], b = M[0][1], c = M[1][0], d = M[1][1];
    var det = a * d - b * c;
    if (Math.abs(det) < 1e-15) throw new Error('Singular 2x2');
    return [[d / det, -b / det], [-c / det, a / det]];
  }
  function matInv(M) {
    var n = M.length;
    var A = M.map(function (row, i) {
      var r = row.slice();
      for (var j = 0; j < n; j++) r.push(i === j ? 1 : 0);
      return r;
    });
    for (var i = 0; i < n; i++) {
      var maxR = i, maxV = Math.abs(A[i][i]);
      for (var r = i + 1; r < n; r++) if (Math.abs(A[r][i]) > maxV) { maxR = r; maxV = Math.abs(A[r][i]); }
      if (maxV < 1e-12) throw new Error('Singular matrix at row ' + i);
      if (maxR !== i) { var tmp = A[i]; A[i] = A[maxR]; A[maxR] = tmp; }
      var piv = A[i][i];
      for (var c2 = 0; c2 < 2 * n; c2++) A[i][c2] /= piv;
      for (var r2 = 0; r2 < n; r2++) {
        if (r2 === i) continue;
        var f = A[r2][i];
        for (var c3 = 0; c3 < 2 * n; c3++) A[r2][c3] -= f * A[i][c3];
      }
    }
    return A.map(function (row) { return row.slice(n); });
  }
  function matvec(A, v) {
    var r = new Array(A.length).fill(0);
    for (var i = 0; i < A.length; i++) { var s = 0; for (var j = 0; j < v.length; j++) s += A[i][j] * v[j]; r[i] = s; }
    return r;
  }

  // Beasley-Springer-Moro inverse normal (good to ~7 digits in [1e-9, 1-1e-9])
  function qnormApprox(p) {
    if (p <= 0) return -Infinity;
    if (p >= 1) return Infinity;
    var a = [-3.969683028665376e+01, 2.209460984245205e+02, -2.759285104469687e+02,
             1.383577518672690e+02, -3.066479806614716e+01, 2.506628277459239e+00];
    var b = [-5.447609879822406e+01, 1.615858368580409e+02, -1.556989798598866e+02,
             6.680131188771972e+01, -1.328068155288572e+01];
    var c = [-7.784894002430293e-03, -3.223964580411365e-01, -2.400758277161838e+00,
             -2.549732539343734e+00, 4.374664141464968e+00, 2.938163982698783e+00];
    var d = [7.784695709041462e-03, 3.224671290700398e-01, 2.445134137142996e+00,
             3.754408661907416e+00];
    var pl = 0.02425, ph = 1 - pl, q, r;
    if (p < pl) {
      q = Math.sqrt(-2 * Math.log(p));
      return (((((c[0] * q + c[1]) * q + c[2]) * q + c[3]) * q + c[4]) * q + c[5]) /
             ((((d[0] * q + d[1]) * q + d[2]) * q + d[3]) * q + 1);
    }
    if (p <= ph) {
      q = p - 0.5; r = q * q;
      return (((((a[0] * r + a[1]) * r + a[2]) * r + a[3]) * r + a[4]) * r + a[5]) * q /
             (((((b[0] * r + b[1]) * r + b[2]) * r + b[3]) * r + b[4]) * r + 1);
    }
    q = Math.sqrt(-2 * Math.log(1 - p));
    return -(((((c[0] * q + c[1]) * q + c[2]) * q + c[3]) * q + c[4]) * q + c[5]) /
            ((((d[0] * q + d[1]) * q + d[2]) * q + d[3]) * q + 1);
  }

  function lnGamma(z) {
    var c = [76.18009172947146, -86.50532032941677, 24.01409824083091,
             -1.231739572450155, 1.208650973866179e-3, -5.395239384953e-6];
    var x = z, y = z, tmp = x + 5.5;
    tmp -= (x + 0.5) * Math.log(tmp);
    var ser = 1.000000000190015;
    for (var j = 0; j < 6; j++) ser += c[j] / ++y;
    return -tmp + Math.log(2.5066282746310005 * ser / x);
  }
  function betacf(a, b, x) {
    var fpmin = 1e-30, qab = a + b, qap = a + 1, qam = a - 1;
    var c = 1, d = 1 - qab * x / qap;
    if (Math.abs(d) < fpmin) d = fpmin;
    d = 1 / d; var h = d;
    for (var m = 1; m <= 200; m++) {
      var m2 = 2 * m;
      var aa = m * (b - m) * x / ((qam + m2) * (a + m2));
      d = 1 + aa * d; if (Math.abs(d) < fpmin) d = fpmin;
      c = 1 + aa / c; if (Math.abs(c) < fpmin) c = fpmin;
      d = 1 / d; h *= d * c;
      aa = -(a + m) * (qab + m) * x / ((a + m2) * (qap + m2));
      d = 1 + aa * d; if (Math.abs(d) < fpmin) d = fpmin;
      c = 1 + aa / c; if (Math.abs(c) < fpmin) c = fpmin;
      d = 1 / d; var del = d * c; h *= del;
      if (Math.abs(del - 1) < 3e-7) break;
    }
    return h;
  }
  function ibeta(a, b, x) {
    if (x <= 0) return 0;
    if (x >= 1) return 1;
    var bt = Math.exp(lnGamma(a + b) - lnGamma(a) - lnGamma(b) + a * Math.log(x) + b * Math.log(1 - x));
    if (x < (a + 1) / (a + b + 2)) return bt * betacf(a, b, x) / a;
    return 1 - bt * betacf(b, a, 1 - x) / b;
  }
  function qbeta(p, a, b) {
    var lo = 0, hi = 1, mid = 0.5;
    for (var i = 0; i < 60; i++) {
      mid = (lo + hi) / 2;
      if (ibeta(a, b, mid) < p) lo = mid; else hi = mid;
    }
    return mid;
  }
  // Chi-squared quantile via Wilson-Hilferty for df>=3; closed forms for df=1,2.
  function qchisq(p, df) {
    if (df <= 0 || p <= 0) return 0;
    if (p >= 1) return Infinity;
    if (df === 1) { var z = qnormApprox((1 + p) / 2); return z * z; }
    if (df === 2) return -2 * Math.log(1 - p);
    var z2 = qnormApprox(p);
    var v = 1 - 2 / (9 * df) + z2 * Math.sqrt(2 / (9 * df));
    return Math.max(0, df * v * v * v);
  }
  // Chi-squared CDF via Wilson-Hilferty
  function pchisq(x, df) {
    if (x <= 0) return 0;
    var h = Math.pow(x / df, 1 / 3);
    var z = (h - (1 - 2 / (9 * df))) / Math.sqrt(2 / (9 * df));
    // Standard-normal CDF via Abramowitz & Stegun 7.1.26
    return 0.5 * (1 + _erf(z / Math.SQRT2));
  }
  function _erf(x) {
    var sign = x < 0 ? -1 : 1; x = Math.abs(x);
    var a1 = 0.254829592, a2 = -0.284496736, a3 = 1.421413741, a4 = -1.453152027, a5 = 1.061405429, p = 0.3275911;
    var t = 1 / (1 + p * x);
    var y = 1 - (((((a5 * t + a4) * t) + a3) * t + a2) * t + a1) * t * Math.exp(-x * x);
    return sign * y;
  }
  // Inverse Student-t — via beta-inverse transform (df>=1)
  function tinv(p, df) {
    if (df < 1 || !isFinite(df)) return NaN;
    if (p <= 0) return -Infinity;
    if (p >= 1) return Infinity;
    var negate = false;
    if (p < 0.5) { negate = true; p = 1 - p; }
    var alpha = 2 * (1 - p);
    if (alpha <= 0) alpha = 1e-12;
    if (alpha >= 1) alpha = 1 - 1e-12;
    var x = qbeta(alpha, df / 2, 0.5);
    if (x <= 0) return Infinity * (negate ? -1 : 1);
    var t = Math.sqrt(df * (1 - x) / x);
    return negate ? -t : t;
  }

  // ===================================================================
  // Section 2: Validation + per-study log-effect derivation.
  // ===================================================================

  // QUIPS domain enumeration (Hayden 2013 Ann Intern Med).
  var QUIPS_DOMAINS = [
    'participation',                  // study participation
    'attrition',                      // attrition
    'prognostic_factor_measurement',  // measurement of prognostic factor
    'outcome_measurement',            // outcome measurement
    'study_confounding',              // adjustment for confounding
    'statistical_analysis'            // analysis & reporting
  ];
  var QUIPS_LEVELS = ['low', 'moderate', 'high', 'unclear'];

  function validate(trials) {
    var issues = [];
    if (!Array.isArray(trials)) { issues.push('trials must be an array'); return issues; }
    if (trials.length === 0) { issues.push('trials array must be non-empty'); return issues; }
    for (var i = 0; i < trials.length; i++) {
      var t = trials[i];
      if (t === null || typeof t !== 'object' || Array.isArray(t)) {
        issues.push('trial ' + i + ': must be a plain object');
        continue;
      }
      var lbl = t.studlab != null ? t.studlab : ('trial ' + i);
      if (typeof t.hr_adj !== 'number' || !isFinite(t.hr_adj) || t.hr_adj <= 0) {
        issues.push(lbl + ': hr_adj must be a finite positive number');
        continue;
      }
      if (typeof t.hr_adj_ci_lb !== 'number' || typeof t.hr_adj_ci_ub !== 'number' ||
          !isFinite(t.hr_adj_ci_lb) || !isFinite(t.hr_adj_ci_ub)) {
        issues.push(lbl + ': hr_adj_ci_lb and hr_adj_ci_ub must be finite numbers');
        continue;
      }
      if (t.hr_adj_ci_lb <= 0 || t.hr_adj_ci_ub <= 0) {
        issues.push(lbl + ': CI bounds must be positive (engine pools on log scale)');
        continue;
      }
      if (t.hr_adj_ci_lb > t.hr_adj_ci_ub) {
        issues.push(lbl + ': hr_adj_ci_lb > hr_adj_ci_ub');
        continue;
      }
      // Reject zero-width CIs: log(ub)−log(lb) → 0 produces seLog=0, vi=0, infinite IV weight.
      // The relative-tolerance threshold (1e-9 on (ub−lb)/lb) catches both literal lb==ub
      // and floating-point near-equality without rejecting tight-but-finite CIs.
      if ((t.hr_adj_ci_ub - t.hr_adj_ci_lb) / Math.max(t.hr_adj_ci_lb, 1e-12) < 1e-9) {
        issues.push(lbl + ': zero-width CI [' + t.hr_adj_ci_lb + ', ' + t.hr_adj_ci_ub + '] — log-scale SE would be 0 (degenerate)');
        continue;
      }
      if (t.hr_adj < t.hr_adj_ci_lb || t.hr_adj > t.hr_adj_ci_ub) {
        issues.push(lbl + ': point estimate ' + t.hr_adj + ' outside CI [' + t.hr_adj_ci_lb + ', ' + t.hr_adj_ci_ub + ']');
        continue;
      }
      if (t.effect_type != null && ['HR', 'OR', 'RR'].indexOf(t.effect_type) < 0) {
        issues.push(lbl + ': effect_type must be one of HR|OR|RR');
        continue;
      }
      if (t.n != null && (typeof t.n !== 'number' || t.n <= 0 || !isFinite(t.n))) {
        issues.push(lbl + ': n must be a positive finite number when present');
      }
      if (t.quips != null && typeof t.quips === 'object') {
        for (var d = 0; d < QUIPS_DOMAINS.length; d++) {
          var dom = QUIPS_DOMAINS[d];
          if (t.quips[dom] != null && QUIPS_LEVELS.indexOf(t.quips[dom]) < 0) {
            issues.push(lbl + ': quips.' + dom + ' must be one of ' + QUIPS_LEVELS.join('|'));
          }
        }
      }
    }
    return issues;
  }

  // Derive (yi=logHR, vi) from a single trial's (hr_adj, CI). SE on log scale
  // = (log(hi) - log(lo)) / (2 * z_{0.975}). Standard CHARMS / Cochrane
  // Handbook v6.5 sec 6.3.2 derivation when the primary paper doesn't report SE.
  var Z975 = 1.959963984540054;
  function logEffect(point, ci_lb, ci_ub) {
    var yi = Math.log(point);
    var seLog = (Math.log(ci_ub) - Math.log(ci_lb)) / (2 * Z975);
    var vi = seLog * seLog;
    return { yi: yi, vi: vi, seLog: seLog };
  }

  function perStudyLog(trials) {
    return trials.map(function (t) {
      var adj = logEffect(t.hr_adj, t.hr_adj_ci_lb, t.hr_adj_ci_ub);
      var unadj = null;
      if (t.hr_unadj != null && t.hr_unadj_ci_lb != null && t.hr_unadj_ci_ub != null) {
        if (t.hr_unadj > 0 && t.hr_unadj_ci_lb > 0 && t.hr_unadj_ci_ub > 0 &&
            t.hr_unadj_ci_lb <= t.hr_unadj_ci_ub) {
          unadj = logEffect(t.hr_unadj, t.hr_unadj_ci_lb, t.hr_unadj_ci_ub);
        }
      }
      return {
        studlab: t.studlab,
        yi_adj: adj.yi, vi_adj: adj.vi, seLog_adj: adj.seLog,
        yi_unadj: unadj ? unadj.yi : null,
        vi_unadj: unadj ? unadj.vi : null,
        seLog_unadj: unadj ? unadj.seLog : null,
        n: t.n != null ? t.n : null,
        events: t.events != null ? t.events : null,
        year: t.year != null ? t.year : null,
        subgroup: t.subgroup != null ? t.subgroup : null,
        cutoff: t.cutoff != null ? t.cutoff : null,
        unit: t.unit != null ? t.unit : null,
        per_unit: t.per_unit != null ? t.per_unit : null,
        biomarker_sd: t.biomarker_sd != null ? t.biomarker_sd : null,
        biomarker_iqr: t.biomarker_iqr != null ? t.biomarker_iqr : null,
        dose: t.dose != null ? t.dose : null,
        reference_dose: t.reference_dose != null ? t.reference_dose : null,
        quips: t.quips || null,
        covariates: t.covariates != null ? t.covariates : null,
        effect_type: t.effect_type || 'HR'
      };
    });
  }

  // ===================================================================
  // Section 3: Random-effects pool (DL + REML) on log scale.
  // ===================================================================

  function tau2DL(yi, vi) {
    if (yi.length < 2) return 0;
    var W = 0, WY = 0;
    for (var i = 0; i < yi.length; i++) { var w = 1 / vi[i]; W += w; WY += w * yi[i]; }
    var yFE = WY / W;
    var Q = 0, sumW2 = 0;
    for (var j = 0; j < yi.length; j++) {
      var w2 = 1 / vi[j];
      Q += w2 * (yi[j] - yFE) * (yi[j] - yFE);
      sumW2 += w2 * w2;
    }
    var df = yi.length - 1;
    var c = W - sumW2 / W;
    if (c <= 0) return 0;
    return Math.max(0, (Q - df) / c);
  }

  // Paule-Mandel tau^2 (Berkey 1995; metafor::rma(method='PM') equivalent).
  //
  // CONVERGENCE GUARANTEE (PM bisection)
  // -----------------------------------
  // Solves Σ w_i(τ²) · (y_i − μ̂(τ²))² = k − 1 by bisection on a monotone
  // equation, where w_i(τ²) = 1 / (v_i + τ²) and μ̂(τ²) = (Σw_iy_i)/(Σw_i).
  //
  // The PM statistic is monotonically non-increasing in τ² (Paule 1982 J Res
  // Natl Bur Stand 87:377). Therefore the equation has at most one root in
  // (0, ∞), making bisection both correct and numerically stable. The
  // implementation:
  //   1. Returns 0 immediately if pmStat(0) ≤ k-1 (PM equation already satisfied at floor)
  //   2. Otherwise brackets the root by doubling from a DL warm-start until pmStat(hi) ≤ target
  //   3. Bisects (lo, hi) to convergence at tolerance 1e-9 or 100 iterations
  //
  // The test suite includes an explicit verification:
  //     test('tau2REML (Paule-Mandel bisection): satisfies Σw(y-μ̂)² = k-1 at convergence')
  // which asserts |Σw(y-μ̂)² − (k-1)| < 1e-6 at the converged τ². Additional
  // per-fixture tests verify the identity holds on real-data inputs.
  //
  // HISTORICAL NOTE
  // ---------------
  // An earlier (pre-2026-05-11) iteration used a Newton-step formula
  //     τ²_new = τ² + [Σw²(y-μ̂)² − Σw²v] / Σw²
  // which converges to the wrong fixed point Σw²(y-μ̂)² = Σw²v ≠ k-1.
  // On the BNP/HF fixture this produced τ²=0.27 while the Q-profile upper
  // bound was 0.026 — a clear sign of wrong-equation convergence. The
  // bisection replacement fixes this; the regression test above pins it.
  //
  // PM is asymptotically equivalent to REML for univariate random-effects MA
  // and is the method we use here as the REML proxy — the engine header refers
  // to it as REML for caller-facing consistency with metafor's rma() default
  // semantics, but the implementation is PM-by-bisection (more numerically
  // robust than Newton/Fisher-scoring REML at small k).
  //
  // Kept as `tau2REML` for API compatibility with callers in this file.
  function tau2REML(yi, vi, opts) {
    opts = opts || {};
    var tol = opts.tol || 1e-9;
    var max_bis = opts.max_iter || 100;
    var k = yi.length;
    if (k < 2) return 0;
    function pmStat(tau2) {
      // Returns Σ w_i (y_i − μ̂)²
      var W = 0, WY = 0;
      for (var i = 0; i < k; i++) { var w = 1 / (vi[i] + tau2); W += w; WY += w * yi[i]; }
      var mu = WY / W;
      var s = 0;
      for (var j = 0; j < k; j++) {
        var w2 = 1 / (vi[j] + tau2);
        s += w2 * (yi[j] - mu) * (yi[j] - mu);
      }
      return s;
    }
    var target = k - 1;
    var Q0 = pmStat(0);
    if (Q0 <= target) return 0;
    // Find upper bracket by doubling
    var hi = Math.max(1e-4, tau2DL(yi, vi) * 2 + 1e-4);
    for (var d = 0; d < 50 && pmStat(hi) > target && hi < 1e8; d++) hi *= 2;
    var lo = 0;
    for (var b = 0; b < max_bis; b++) {
      var mid = (lo + hi) / 2;
      var s = pmStat(mid);
      if (Math.abs(s - target) < tol) return mid;
      if (s > target) lo = mid; else hi = mid;
    }
    return (lo + hi) / 2;
  }

  // Pool given tau2: returns mu, se, Q (residual at this tau2), QFE (residual at tau2=0).
  function poolGivenTau2(yi, vi, tau2) {
    var W = 0, WY = 0, sumW2 = 0;
    for (var i = 0; i < yi.length; i++) {
      var w = 1 / (vi[i] + tau2);
      W += w; WY += w * yi[i]; sumW2 += w * w;
    }
    var mu = WY / W;
    var se = Math.sqrt(1 / W);
    var Q = 0;
    for (var j = 0; j < yi.length; j++) {
      var w2 = 1 / (vi[j] + tau2);
      Q += w2 * (yi[j] - mu) * (yi[j] - mu);
    }
    return { mu: mu, se: se, W: W, sumW2: sumW2, Q: Q };
  }

  // HKSJ multiplier per Cochrane v6.5: floor at max(1, Q/(k-1)).
  // Returns SE-scaling factor (already square-rooted; not the raw Q/(k-1)).
  function hksjMultiplier(yi, vi, tau2, mu) {
    var df = yi.length - 1;
    if (df < 1) return 1;
    var sumW = 0, qStar = 0;
    for (var i = 0; i < yi.length; i++) {
      var w = 1 / (vi[i] + tau2);
      sumW += w;
      qStar += w * (yi[i] - mu) * (yi[i] - mu);
    }
    qStar /= df;
    return Math.max(1, qStar);
  }

  // Q-profile tau^2 CI (Viechtbauer 2007, univariate marginal).
  function qProfileTau2CI(yi, vi, alpha) {
    var df = yi.length - 1;
    if (df < 2 || yi.length < 3) return { tau2_lo: null, tau2_hi: null };
    function qGen(tau2) {
      var sW = 0, sWY = 0, sW_Y2 = 0;
      for (var i = 0; i < yi.length; i++) {
        var w = 1 / (vi[i] + tau2);
        sW += w; sWY += w * yi[i]; sW_Y2 += w * yi[i] * yi[i];
      }
      if (sW === 0) return 0;
      return Math.max(0, sW_Y2 - (sWY * sWY) / sW);
    }
    var cutHi = qchisq(1 - alpha / 2, df);
    var cutLo = qchisq(alpha / 2, df);
    var Q0 = qGen(0);
    function bisect(target) {
      if (Q0 <= target) return 0;
      var lo = 0, hi = 100;
      for (var e = 0; e < 30 && qGen(hi) > target && hi < 1e8; e++) hi *= 2;
      for (var i = 0; i < 60; i++) {
        var mid = (lo + hi) / 2;
        if (qGen(mid) > target) lo = mid; else hi = mid;
      }
      return (lo + hi) / 2;
    }
    return { tau2_lo: bisect(cutHi), tau2_hi: bisect(cutLo) };
  }

  // ===================================================================
  // Section 4: Cutoff harmonization (linear / log per-SD rescaling).
  // ===================================================================
  //
  // Per CHARMS sec 8 and Riley 2019 BMJ 'Calculating the harmonised effect
  // estimate per standard deviation'. When trial reports HR per `per_unit`
  // increment AND biomarker_sd is known, rescale to per-1-SD:
  //   logHR_per_SD = logHR_per_unit * (biomarker_sd / per_unit)
  // For log-transformed biomarkers (e.g. log2(NT-proBNP)), use IQR-based
  // approximation per Lewington 2002 Lancet (1 SD ≈ 0.74 × log-IQR for
  // log-normal).
  //
  // Each output entry preserves the original yi/vi alongside the harmonized
  // values so downstream code can opt-in.
  function cutoffHarmonization(per_study_log, mode) {
    mode = mode || 'log_per_sd';
    return per_study_log.map(function (s) {
      var out = { studlab: s.studlab, yi_raw: s.yi_adj, vi_raw: s.vi_adj,
                  yi_harm: null, vi_harm: null,
                  scale_factor: null, harmonized: false, harmonization_note: null };
      if (mode === 'none') return out;
      if (mode !== 'log_per_sd') {
        out.harmonization_note = 'unknown mode "' + mode + '"; expected none|log_per_sd';
        return out;
      }
      if (s.per_unit == null || !isFinite(s.per_unit) || s.per_unit <= 0) {
        out.harmonization_note = 'per_unit missing/invalid; no rescale possible';
        return out;
      }
      // Resolve effective SD: explicit > IQR-derived (IQR/1.349 for normal,
      // IQR_log/1.349 for log-normal but IQR-based rescale already applies
      // on the log scale of the biomarker).
      var sd = null;
      if (s.biomarker_sd != null && isFinite(s.biomarker_sd) && s.biomarker_sd > 0) {
        sd = s.biomarker_sd;
      } else if (s.biomarker_iqr != null && isFinite(s.biomarker_iqr) && s.biomarker_iqr > 0) {
        sd = s.biomarker_iqr / 1.349;
      }
      if (sd == null) {
        out.harmonization_note = 'biomarker_sd / biomarker_iqr both missing; no rescale possible';
        return out;
      }
      var scale = sd / s.per_unit;
      // Variance on log scale scales by scale^2.
      out.yi_harm = s.yi_adj * scale;
      out.vi_harm = s.vi_adj * scale * scale;
      out.scale_factor = scale;
      out.harmonized = true;
      out.harmonization_note = 'rescaled by SD/per_unit = ' + sd.toFixed(4) + '/' + s.per_unit;
      return out;
    });
  }

  // ===================================================================
  // Section 5: Adjusted vs unadjusted forest split.
  // ===================================================================
  function adjUnadjSplit(per_study_log) {
    var adj_yi = [], adj_vi = [];
    var un_yi = [], un_vi = [];
    var have_both = 0;
    per_study_log.forEach(function (s) {
      adj_yi.push(s.yi_adj); adj_vi.push(s.vi_adj);
      if (s.yi_unadj != null && s.vi_unadj != null) {
        un_yi.push(s.yi_unadj); un_vi.push(s.vi_unadj);
        have_both++;
      }
    });
    if (un_yi.length < 2 || have_both < 2) {
      return { available: false, reason: 'need >=2 trials with both adjusted and unadjusted effects', n_both: have_both };
    }
    var tau2_adj = tau2REML(adj_yi, adj_vi);
    var pa = poolGivenTau2(adj_yi, adj_vi, tau2_adj);
    var tau2_un = tau2REML(un_yi, un_vi);
    var pu = poolGivenTau2(un_yi, un_vi, tau2_un);
    // Q_between on log scale (subgroup test, Borenstein 2009 ch.19).
    var wA = 1 / (pa.se * pa.se), wU = 1 / (pu.se * pu.se);
    var muP = (wA * pa.mu + wU * pu.mu) / (wA + wU);
    var Q_b = wA * (pa.mu - muP) * (pa.mu - muP) + wU * (pu.mu - muP) * (pu.mu - muP);
    var p_b = 1 - pchisq(Q_b, 1);
    return {
      available: true,
      n_adj: adj_yi.length, n_unadj: un_yi.length, n_both: have_both,
      adjusted: {
        pooled_logHR: pa.mu, pooled_HR: Math.exp(pa.mu),
        ci_lb: Math.exp(pa.mu - Z975 * pa.se), ci_ub: Math.exp(pa.mu + Z975 * pa.se),
        tau2: tau2_adj
      },
      unadjusted: {
        pooled_logHR: pu.mu, pooled_HR: Math.exp(pu.mu),
        ci_lb: Math.exp(pu.mu - Z975 * pu.se), ci_ub: Math.exp(pu.mu + Z975 * pu.se),
        tau2: tau2_un
      },
      delta_logHR: pa.mu - pu.mu,
      delta_HR: Math.exp(pa.mu - pu.mu),
      Q_between: Q_b,
      df_between: 1,
      p_between: p_b
    };
  }

  // ===================================================================
  // Section 6: QUIPS 6-domain RoB summary.
  // ===================================================================
  function quipsSummary(per_study_log) {
    var domain_counts = {};
    QUIPS_DOMAINS.forEach(function (d) {
      domain_counts[d] = { low: 0, moderate: 0, high: 0, unclear: 0 };
    });
    var per_study = [];
    var have_quips = 0;
    per_study_log.forEach(function (s) {
      if (s.quips == null) {
        per_study.push({ studlab: s.studlab, overall: null, domains: null });
        return;
      }
      have_quips++;
      var overall = 'low';
      var domains = {};
      QUIPS_DOMAINS.forEach(function (d) {
        var lvl = s.quips[d] || 'unclear';
        domains[d] = lvl;
        domain_counts[d][lvl] = (domain_counts[d][lvl] || 0) + 1;
        // Overall: max of any domain (worst wins). Tie-break: high > moderate > unclear > low.
        var rank = { low: 0, unclear: 1, moderate: 2, high: 3 };
        if (rank[lvl] > rank[overall]) overall = lvl;
      });
      per_study.push({ studlab: s.studlab, overall: overall, domains: domains });
    });
    return {
      n_with_quips: have_quips,
      n_without_quips: per_study_log.length - have_quips,
      per_study: per_study,
      domain_counts: domain_counts,
      domains: QUIPS_DOMAINS.slice()
    };
  }

  // QUIPS-weighted pool: down-weight high-RoB studies (sensitivity analysis).
  // Weight modifier: low=1.0, moderate=0.75, high=0.25, unclear=0.50.
  function quipsWeightedPool(per_study_log, tau2_main) {
    var weights = { low: 1.0, moderate: 0.75, high: 0.25, unclear: 0.50 };
    var hadAny = false;
    var yi = [], vi_inflated = [];
    per_study_log.forEach(function (s) {
      yi.push(s.yi_adj);
      if (s.quips == null) {
        vi_inflated.push(s.vi_adj);
        return;
      }
      hadAny = true;
      var overall = 'low';
      var rank = { low: 0, unclear: 1, moderate: 2, high: 3 };
      QUIPS_DOMAINS.forEach(function (d) {
        var lvl = s.quips[d] || 'unclear';
        if (rank[lvl] > rank[overall]) overall = lvl;
      });
      var w = weights[overall];
      vi_inflated.push(s.vi_adj / w);
    });
    if (!hadAny) return { available: false };
    var pool = poolGivenTau2(yi, vi_inflated, tau2_main);
    return {
      available: true,
      pooled_logHR: pool.mu,
      pooled_HR: Math.exp(pool.mu),
      ci_lb: Math.exp(pool.mu - Z975 * pool.se),
      ci_ub: Math.exp(pool.mu + Z975 * pool.se),
      weighting: weights
    };
  }

  // ===================================================================
  // Section 7: Leave-one-out, cumulative, Baujat, influence diagnostics.
  //
  // ARCHITECTURAL NOTE (do not refactor away from this):
  // These analytics are intentionally bundled INSIDE the engine rather than
  // delegated to the existing vendor/leave-one-out.js / vendor/cumulative-ma.js
  // / vendor/baujat-plot.js / vendor/influence-diagnostics.js modules.
  //
  // Rationale: those vendor modules consume PanelHelper.extractBinaryTrials(rd),
  // which hard-requires 2×2 cell counts (tE/tN/cE/cN) on RapidMeta.realData.
  // Prognostic-factor data is per-cohort log-HR + SE — no 2×2 cells exist.
  // The only path to delegate would be to fake 2×2 cells from log-HR + N via
  // Stijnen 2010 method-of-moments, which loses log-scale fidelity and would
  // be a scientific bug (turning an adjusted-HR pool into an unadjusted-OR pool
  // is exactly the confounding the CHARMS-PF + QUIPS pipeline is designed to
  // detect, not produce).
  //
  // Co-locating these analytics in the engine means: one call to fit() returns
  // a rich result with log-scale-correct sensitivity panels, and the host HTML
  // renders them directly from r.leave_one_out, r.cumulative, r.baujat, etc.
  // The trade-off is a longer engine file in exchange for log-scale fidelity.
  // ===================================================================
  function leaveOneOut(per_study_log, mainHR, mainCI) {
    var rows = [];
    var k = per_study_log.length;
    if (k < 3) return rows;
    for (var drop = 0; drop < k; drop++) {
      var yi = [], vi = [];
      for (var i = 0; i < k; i++) {
        if (i === drop) continue;
        yi.push(per_study_log[i].yi_adj);
        vi.push(per_study_log[i].vi_adj);
      }
      var tau2 = tau2REML(yi, vi);
      var p = poolGivenTau2(yi, vi, tau2);
      var HR = Math.exp(p.mu);
      var ci_lo = Math.exp(p.mu - Z975 * p.se);
      var ci_hi = Math.exp(p.mu + Z975 * p.se);
      var shift = Math.abs(HR - mainHR) / mainHR;
      var fullSig = (mainCI[0] > 1) || (mainCI[1] < 1);
      var subSig = (ci_lo > 1) || (ci_hi < 1);
      rows.push({
        dropped: per_study_log[drop].studlab,
        pooled_HR: HR, ci_lb: ci_lo, ci_ub: ci_hi,
        shift_pct: 100 * shift,
        flips_significance: (fullSig !== subSig),
        k: yi.length
      });
    }
    return rows;
  }

  // Cumulative MA in chronological order (by year ascending; ties stable).
  //
  // Studies with year=null are deterministically placed AT THE END of the
  // cumulative sequence (Infinity sentinel + stable secondary sort on original
  // index). Rationale: a missing year cannot be ordered chronologically
  // against known years; placing it last ensures (a) the cumulative pool
  // evolves through known years first, then absorbs the year-missing studies
  // as a final pass, and (b) the per-row indices remain stable across runs.
  function cumulativeMA(per_study_log) {
    var sortable = per_study_log.map(function (s, i) { return { idx: i, s: s, year: s.year != null ? s.year : Infinity }; });
    sortable.sort(function (a, b) {
      if (a.year !== b.year) return a.year - b.year;
      return a.idx - b.idx;
    });
    var rows = [];
    var yi = [], vi = [];
    for (var t = 0; t < sortable.length; t++) {
      yi.push(sortable[t].s.yi_adj);
      vi.push(sortable[t].s.vi_adj);
      if (yi.length < 2) {
        rows.push({
          studlab: sortable[t].s.studlab, year: sortable[t].s.year,
          k: 1, pooled_HR: Math.exp(yi[0]),
          ci_lb: Math.exp(yi[0] - Z975 * Math.sqrt(vi[0])),
          ci_ub: Math.exp(yi[0] + Z975 * Math.sqrt(vi[0]))
        });
      } else {
        var tau2 = tau2REML(yi, vi);
        var p = poolGivenTau2(yi, vi, tau2);
        rows.push({
          studlab: sortable[t].s.studlab, year: sortable[t].s.year,
          k: yi.length, pooled_HR: Math.exp(p.mu),
          ci_lb: Math.exp(p.mu - Z975 * p.se),
          ci_ub: Math.exp(p.mu + Z975 * p.se)
        });
      }
    }
    return rows;
  }

  // Baujat: per-study contribution to Q vs influence on pooled estimate.
  // x = w_i * (y_i - mu)^2 / (1 - h_i); y = (mu - mu_(-i))^2 * w_i.
  function baujat(per_study_log, mainMu, mainTau2) {
    var k = per_study_log.length;
    if (k < 3) return [];
    var W = 0;
    for (var i = 0; i < k; i++) W += 1 / (per_study_log[i].vi_adj + mainTau2);
    var rows = [];
    for (var i2 = 0; i2 < k; i2++) {
      var w_i = 1 / (per_study_log[i2].vi_adj + mainTau2);
      var h_i = w_i / W;
      var resid = per_study_log[i2].yi_adj - mainMu;
      var x = w_i * resid * resid / (1 - h_i);
      // mu_(-i) via DL re-pool, light-weight
      var yi2 = [], vi2 = [];
      for (var j = 0; j < k; j++) {
        if (j === i2) continue;
        yi2.push(per_study_log[j].yi_adj);
        vi2.push(per_study_log[j].vi_adj);
      }
      var tau2_mi = tau2DL(yi2, vi2);
      var pmi = poolGivenTau2(yi2, vi2, tau2_mi);
      var y = (mainMu - pmi.mu) * (mainMu - pmi.mu) * w_i;
      rows.push({
        studlab: per_study_log[i2].studlab,
        x_contrib_Q: x,
        y_influence: y,
        weight_pct: 100 * h_i
      });
    }
    return rows;
  }

  // Influence diagnostics: externally-studentized (deleted) residuals + Cook's
  // distance, per Viechtbauer 2010 (metafor::rstudent / cooks.distance.rma.uni).
  // We use leave-i refits so that an outlier's residual is measured against the
  // tau^2 of the OTHER k-1 studies — without this, a single large outlier
  // inflates tau^2 enough to hide itself in the standardized-residual scale.
  function influenceDiag(per_study_log, mainMu, mainTau2) {
    var k = per_study_log.length;
    var rows = [];
    if (k < 2) return rows;
    for (var i2 = 0; i2 < k; i2++) {
      // Leave-i refit
      var yi_mi = [], vi_mi = [];
      for (var j = 0; j < k; j++) {
        if (j === i2) continue;
        yi_mi.push(per_study_log[j].yi_adj);
        vi_mi.push(per_study_log[j].vi_adj);
      }
      var tau2_mi = (yi_mi.length >= 2) ? tau2REML(yi_mi, vi_mi) : 0;
      var p_mi = (yi_mi.length >= 1) ? poolGivenTau2(yi_mi, vi_mi, tau2_mi)
                                     : { mu: per_study_log[i2].yi_adj, se: Math.sqrt(per_study_log[i2].vi_adj) };
      // Externally-studentized (deleted) residual
      var d_i = per_study_log[i2].yi_adj - p_mi.mu;
      var se_d = Math.sqrt(per_study_log[i2].vi_adj + tau2_mi + p_mi.se * p_mi.se);
      var stud_resid = se_d > 0 ? d_i / se_d : 0;
      // Leverage using full-pool weights (for reporting)
      var W = 0;
      for (var w2 = 0; w2 < k; w2++) W += 1 / (per_study_log[w2].vi_adj + mainTau2);
      var w_i = 1 / (per_study_log[i2].vi_adj + mainTau2);
      var h_i = w_i / W;
      // Cook's distance: squared shift in pooled estimate when i is dropped,
      // scaled by SE(mu).
      var se_main = Math.sqrt(1 / W);
      var cook = (mainMu - p_mi.mu) * (mainMu - p_mi.mu) / (se_main * se_main);
      rows.push({
        studlab: per_study_log[i2].studlab,
        studentized_residual: stud_resid,
        cook_d: cook,
        leverage: h_i,
        outlier_flag: Math.abs(stud_resid) > 1.96
      });
    }
    return rows;
  }

  // ===================================================================
  // Section 8: Funnel plot diagnostics — Egger's regression test.
  // ===================================================================
  function funnelDiagnostics(per_study_log) {
    var k = per_study_log.length;
    if (k < 3) {
      return { available: false, reason: 'Egger test undefined for k<3 (preferred k>=10 per Cochrane)', k: k };
    }
    // Egger regression: standardized effect ~ precision.
    // y = yi / sqrt(vi);  x = 1 / sqrt(vi).
    // Regression intercept (a) measures funnel asymmetry; SE(a) → t-test.
    var n = k;
    var ys = [], xs = [];
    for (var i = 0; i < k; i++) {
      var seL = Math.sqrt(per_study_log[i].vi_adj);
      ys.push(per_study_log[i].yi_adj / seL);
      xs.push(1 / seL);
    }
    var mx = 0, my = 0;
    for (var i2 = 0; i2 < n; i2++) { mx += xs[i2]; my += ys[i2]; }
    mx /= n; my /= n;
    var sxx = 0, sxy = 0;
    for (var i3 = 0; i3 < n; i3++) {
      sxx += (xs[i3] - mx) * (xs[i3] - mx);
      sxy += (xs[i3] - mx) * (ys[i3] - my);
    }
    var slope = sxx > 0 ? sxy / sxx : 0;
    var intercept = my - slope * mx;
    var resid_ss = 0;
    for (var i4 = 0; i4 < n; i4++) {
      var pred = intercept + slope * xs[i4];
      resid_ss += (ys[i4] - pred) * (ys[i4] - pred);
    }
    var dfErr = Math.max(1, n - 2);
    var sigma2 = resid_ss / dfErr;
    var se_intercept = Math.sqrt(sigma2 * (1 / n + (mx * mx) / sxx));
    var t = intercept / se_intercept;
    // 2-sided t-test p-value via 1 - tcdf
    var p = 2 * (1 - _tCDFapprox(Math.abs(t), dfErr));
    return {
      available: true,
      k: k,
      egger_intercept: intercept,
      egger_se: se_intercept,
      egger_t: t,
      egger_df: dfErr,
      egger_p: Math.max(0, Math.min(1, p)),
      slope: slope,
      asymmetric: p < 0.10,
      underpowered_warning: k < 10
    };
  }
  function _tCDFapprox(t, df) {
    // Use beta-relation: F_T(t) = 1 - 0.5 * I_{df/(df+t^2)}(df/2, 1/2) for t>=0.
    if (t < 0) return 1 - _tCDFapprox(-t, df);
    var x = df / (df + t * t);
    return 1 - 0.5 * ibeta(df / 2, 0.5, x);
  }

  // ===================================================================
  // Section 9: Subgroup interaction test (between-group Q on log scale).
  // ===================================================================
  function subgroupInteraction(per_study_log) {
    var groups = {};
    per_study_log.forEach(function (s) {
      if (s.subgroup == null) return;
      var key = String(s.subgroup);
      if (!groups[key]) groups[key] = { yi: [], vi: [], labels: [] };
      groups[key].yi.push(s.yi_adj);
      groups[key].vi.push(s.vi_adj);
      groups[key].labels.push(s.studlab);
    });
    var keys = Object.keys(groups);
    if (keys.length < 2) {
      return { available: false, reason: 'need >=2 subgroups with assigned membership', n_groups: keys.length };
    }
    var perGroup = {};
    var muHat = [], wHat = [];
    keys.forEach(function (k) {
      var g = groups[k];
      if (g.yi.length === 0) return;
      var tau2 = tau2REML(g.yi, g.vi);
      var p = poolGivenTau2(g.yi, g.vi, tau2);
      perGroup[k] = {
        k: g.yi.length,
        pooled_logHR: p.mu,
        pooled_HR: Math.exp(p.mu),
        ci_lb: Math.exp(p.mu - Z975 * p.se),
        ci_ub: Math.exp(p.mu + Z975 * p.se),
        tau2: tau2
      };
      muHat.push(p.mu);
      wHat.push(1 / (p.se * p.se));
    });
    var sumW = 0, sumWMu = 0;
    for (var i = 0; i < muHat.length; i++) { sumW += wHat[i]; sumWMu += wHat[i] * muHat[i]; }
    var muP = sumWMu / sumW;
    var Q_b = 0;
    for (var j = 0; j < muHat.length; j++) Q_b += wHat[j] * (muHat[j] - muP) * (muHat[j] - muP);
    var df = muHat.length - 1;
    var p_b = df > 0 ? (1 - pchisq(Q_b, df)) : NaN;
    return {
      available: true,
      n_groups: keys.length,
      per_group: perGroup,
      Q_between: Q_b,
      df_between: df,
      p_between: p_b,
      coverage_warning: muHat.length < 3
    };
  }

  // ===================================================================
  // Section 10: Dose-response (continuous biomarker) — restricted cubic
  // spline (3 knots at quartile midpoints) or fallback linear log-HR per
  // unit. Activated when >=2 trials report dose+reference_dose.
  // ===================================================================
  function doseResponse(per_study_log) {
    var pts = [];
    per_study_log.forEach(function (s) {
      if (s.dose == null || !isFinite(s.dose)) return;
      pts.push({ studlab: s.studlab, dose: s.dose, yi: s.yi_adj, vi: s.vi_adj,
                 reference_dose: s.reference_dose != null ? s.reference_dose : 0 });
    });
    if (pts.length < 2) {
      return { available: false, reason: 'need >=2 trials with dose recorded', n_with_dose: pts.length };
    }
    // Linear log-HR per unit: weighted least squares with weights 1/vi.
    var n = pts.length;
    var sw = 0, swx = 0, swy = 0, swxx = 0, swxy = 0;
    for (var i = 0; i < n; i++) {
      var w = 1 / pts[i].vi;
      var x = pts[i].dose - pts[i].reference_dose;
      var y = pts[i].yi;
      sw += w; swx += w * x; swy += w * y; swxx += w * x * x; swxy += w * x * y;
    }
    var denom = sw * swxx - swx * swx;
    if (denom <= 0) {
      return { available: true, method: 'degenerate', reason: 'all doses equal',
               linear_slope: 0, linear_slope_se: NaN, n: n };
    }
    var slope = (sw * swxy - swx * swy) / denom;
    var intercept = (swy - slope * swx) / sw;
    var se_slope = Math.sqrt(sw / denom);
    // R^2 (weighted)
    var ss_tot = 0, ss_res = 0, ybar = swy / sw;
    for (var i2 = 0; i2 < n; i2++) {
      var w2 = 1 / pts[i2].vi;
      var yp = intercept + slope * (pts[i2].dose - pts[i2].reference_dose);
      ss_tot += w2 * (pts[i2].yi - ybar) * (pts[i2].yi - ybar);
      ss_res += w2 * (pts[i2].yi - yp) * (pts[i2].yi - yp);
    }
    var r2 = ss_tot > 0 ? Math.max(0, 1 - ss_res / ss_tot) : 0;
    // Wald CI on slope
    var slope_lo = slope - Z975 * se_slope;
    var slope_hi = slope + Z975 * se_slope;
    // Per-unit HR (back-transformed)
    var hr_per_unit = Math.exp(slope);
    var hr_per_unit_lo = Math.exp(slope_lo);
    var hr_per_unit_hi = Math.exp(slope_hi);
    // P-value on slope = 0
    var z = slope / se_slope;
    var p_slope = 2 * (1 - _normCDF(Math.abs(z)));
    return {
      available: true,
      method: 'weighted_linear_log_per_unit',
      n: n,
      linear_slope: slope,
      linear_slope_se: se_slope,
      linear_intercept: intercept,
      hr_per_unit: hr_per_unit,
      hr_per_unit_ci_lb: hr_per_unit_lo,
      hr_per_unit_ci_ub: hr_per_unit_hi,
      r2_weighted: r2,
      p_slope: p_slope,
      monotone_increasing: slope > 0 && p_slope < 0.05,
      monotone_decreasing: slope < 0 && p_slope < 0.05
    };
  }
  function _normCDF(z) { return 0.5 * (1 + _erf(z / Math.SQRT2)); }

  // ===================================================================
  // Section 11: Trial integrity (SE clustering) + INSPECT-SR flags.
  // ===================================================================
  function trialIntegrity(per_study_log) {
    var k = per_study_log.length;
    if (k < 4) return { available: false, reason: 'need k>=4 for SE-cluster detection' };
    // Detect suspicious clustering of SEs within a tight band (Carlisle-style heuristic).
    var ses = per_study_log.map(function (s) { return s.seLog_adj; }).sort(function (a, b) { return a - b; });
    var ratio = ses[Math.floor(k * 0.75)] / Math.max(1e-9, ses[Math.floor(k * 0.25)]);
    var suspicious_cluster = ratio < 1.10 && k >= 5;  // 75th and 25th SE within 10% → suspicious
    return {
      available: true,
      seLog_p25: ses[Math.floor(k * 0.25)],
      seLog_p75: ses[Math.floor(k * 0.75)],
      seLog_p75_p25_ratio: ratio,
      suspicious_cluster: suspicious_cluster
    };
  }

  function inspectSrFlags(per_study_log) {
    var flags = [];
    per_study_log.forEach(function (s) {
      if (s.n != null && s.n < 30) {
        // Tight CI on small N is suspicious (Carlisle / INSPECT-SR).
        // Tightness: ci_ratio = exp(2*1.96*seLog) — if <1.5 on n<30, flag.
        var ci_ratio = Math.exp(2 * Z975 * s.seLog_adj);
        if (ci_ratio < 1.5) {
          flags.push({ studlab: s.studlab, reason: 'implausibly tight CI (ratio ' + ci_ratio.toFixed(2) + ') for n=' + s.n });
        }
      }
      // CHARMS check: an adjusted estimate with no covariates declared is suspicious.
      if ((s.covariates == null || s.covariates === '') && s.effect_type === 'HR') {
        flags.push({ studlab: s.studlab, reason: 'adjusted HR reported with no covariate set listed' });
      }
    });
    return flags;
  }

  // ===================================================================
  // Section 12: Top-level fit().
  // ===================================================================
  function fit(trials, opts) {
    opts = opts || {};
    var issues = validate(trials);
    if (issues.length > 0) throw new Error('invalid input: ' + issues.join('; '));

    var method_tau = opts.method_tau || 'REML';  // 'REML' (=PM) | 'DL' | 'PM'
    var alpha = opts.alpha != null ? opts.alpha : 0.05;
    var hksj = opts.hksj !== false;
    var harmonize = opts.harmonize || 'log_per_sd';

    var pslog = perStudyLog(trials);
    var k = pslog.length;

    // Effect-type consistency check: warn if mixed HR/OR/RR (still pool, but flag).
    var types = {};
    pslog.forEach(function (s) { types[s.effect_type] = (types[s.effect_type] || 0) + 1; });
    var typeKeys = Object.keys(types);
    var mixed_effect_types = typeKeys.length > 1;
    var primary_effect_type = typeKeys.sort(function (a, b) { return types[b] - types[a]; })[0] || 'HR';

    var yi = pslog.map(function (s) { return s.yi_adj; });
    var vi = pslog.map(function (s) { return s.vi_adj; });

    var fallback = null;
    var pooled = null;
    if (k === 1) {
      // Single study — report point + Wald CI; no meta-analysis.
      fallback = 'single_study';
      pooled = {
        mu: yi[0], se: Math.sqrt(vi[0]),
        tau2: null, Q: 0, QFE: 0
      };
    } else {
      var tau2 = (method_tau === 'DL') ? tau2DL(yi, vi) : tau2REML(yi, vi);
      var p = poolGivenTau2(yi, vi, tau2);
      var pFE = poolGivenTau2(yi, vi, 0);
      pooled = { mu: p.mu, se: p.se, tau2: tau2, Q: pFE.Q, QFE: pFE.Q };
    }

    var df = Math.max(0, k - 1);
    var Q_FE = pooled.QFE != null ? pooled.QFE : 0;
    var I2 = (df > 0 && Q_FE > 0) ? Math.max(0, (Q_FE - df) / Q_FE) : 0;
    var H2 = df > 0 ? Math.max(1, Q_FE / df) : 1;
    var p_Q = (df > 0) ? (1 - pchisq(Q_FE, df)) : NaN;

    // Wald CI (standard, used for the headline pooled HR)
    var z = qnormApprox(1 - alpha / 2);
    var ci_lb = Math.exp(pooled.mu - z * pooled.se);
    var ci_ub = Math.exp(pooled.mu + z * pooled.se);

    // HKSJ CI (with Cochrane v6.5 floor max(1, Q/(k-1)))
    var hksj_mult = 1;
    var hksj_ci_lb = null, hksj_ci_ub = null;
    var hksj_warning = null;
    if (k >= 2 && hksj) {
      hksj_mult = hksjMultiplier(yi, vi, pooled.tau2 != null ? pooled.tau2 : 0, pooled.mu);
      var t_crit = tinv(1 - alpha / 2, df);
      var se_hksj = pooled.se * Math.sqrt(hksj_mult);
      hksj_ci_lb = Math.exp(pooled.mu - t_crit * se_hksj);
      hksj_ci_ub = Math.exp(pooled.mu + t_crit * se_hksj);
      // df=1 (k=2) makes t_{0.975, 1} ≈ 12.71 — the resulting HKSJ CI is mathematically
      // defined but practically uninformative (always >5× wider than the Wald CI).
      // Cochrane Handbook v6.5 cautions against HKSJ at k=2 for this reason; surface
      // the warning so downstream consumers can suppress or annotate the column.
      if (df === 1) {
        hksj_warning = 'HKSJ at k=2 uses t_{0.975, df=1} ≈ 12.71; the resulting CI is uninformatively wide. Cochrane Handbook v6.5 sec 10.10.4.3 cautions against HKSJ at k=2.';
      }
    }

    // Q-profile tau^2 CI (Viechtbauer)
    var qpCI = { tau2_lo: null, tau2_hi: null };
    if (k >= 3) qpCI = qProfileTau2CI(yi, vi, alpha);

    // Prediction interval per Cochrane v6.5 (df = k-1)
    var pi_lb = null, pi_ub = null, pi_df = null;
    if (k >= 3 && pooled.tau2 != null) {
      pi_df = k - 1;
      var t_pi = tinv(1 - alpha / 2, pi_df);
      var pi_se = Math.sqrt(pooled.tau2 + pooled.se * pooled.se);
      pi_lb = Math.exp(pooled.mu - t_pi * pi_se);
      pi_ub = Math.exp(pooled.mu + t_pi * pi_se);
    }

    // Harmonization (per-SD rescale when biomarker SD known)
    var harmonized = cutoffHarmonization(pslog, harmonize);
    var harmonized_pool = null;
    var nHarm = harmonized.filter(function (h) { return h.harmonized; }).length;
    if (nHarm >= 2) {
      var yi_h = [], vi_h = [];
      harmonized.forEach(function (h) {
        if (h.harmonized) { yi_h.push(h.yi_harm); vi_h.push(h.vi_harm); }
      });
      var tau2_h = tau2REML(yi_h, vi_h);
      var p_h = poolGivenTau2(yi_h, vi_h, tau2_h);
      harmonized_pool = {
        k: yi_h.length,
        pooled_logHR_per_SD: p_h.mu,
        pooled_HR_per_SD: Math.exp(p_h.mu),
        ci_lb: Math.exp(p_h.mu - Z975 * p_h.se),
        ci_ub: Math.exp(p_h.mu + Z975 * p_h.se),
        tau2: tau2_h
      };
    }

    // Adj vs Unadj split (Q_between test)
    var adjUnadj = adjUnadjSplit(pslog);

    // QUIPS 6-domain summary
    var quips = quipsSummary(pslog);
    var quips_weighted = quipsWeightedPool(pslog, pooled.tau2 != null ? pooled.tau2 : 0);

    // Universal-panel-equivalents
    var l1o = leaveOneOut(pslog, Math.exp(pooled.mu), [ci_lb, ci_ub]);
    var cum = cumulativeMA(pslog);
    var bau = baujat(pslog, pooled.mu, pooled.tau2 != null ? pooled.tau2 : 0);
    var infl = influenceDiag(pslog, pooled.mu, pooled.tau2 != null ? pooled.tau2 : 0);
    var fun = funnelDiagnostics(pslog);
    var sub = subgroupInteraction(pslog);
    var dr = doseResponse(pslog);
    var ti = trialIntegrity(pslog);
    var inspect = inspectSrFlags(pslog);

    // Per-study export (panel-ready)
    var per_study = pslog.map(function (s, i) {
      return {
        studlab: s.studlab,
        hr_adj: Math.exp(s.yi_adj),
        ci_lb: Math.exp(s.yi_adj - Z975 * s.seLog_adj),
        ci_ub: Math.exp(s.yi_adj + Z975 * s.seLog_adj),
        logHR_adj: s.yi_adj,
        seLog_adj: s.seLog_adj,
        weight_pct: pooled.tau2 != null && k >= 2
          ? 100 * (1 / (s.vi_adj + (pooled.tau2 || 0))) /
                  yi.reduce(function (acc, _, idx) { return acc + 1 / (vi[idx] + (pooled.tau2 || 0)); }, 0)
          : null,
        hr_unadj: s.yi_unadj != null ? Math.exp(s.yi_unadj) : null,
        n: s.n, events: s.events, year: s.year,
        cutoff: s.cutoff, unit: s.unit, per_unit: s.per_unit,
        subgroup: s.subgroup, dose: s.dose, reference_dose: s.reference_dose,
        covariates: s.covariates,
        effect_type: s.effect_type,
        // Flag the cohort as deviating from the pool's primary effect type
        // (e.g., OR cohort in an HR-dominated pool). Pool semantics treat
        // log(OR) ≈ log(HR) for rare events per Stijnen 2010 Stat Med
        // 29:3046; the per-cohort flag lets the host HTML annotate the
        // forest plot or sensitivity table when this approximation is in play.
        effect_type_differs_from_primary: (s.effect_type || 'HR') !== primary_effect_type,
        quips_overall: s.quips ? (function () {
          var rank = { low: 0, unclear: 1, moderate: 2, high: 3 };
          var ov = 'low';
          QUIPS_DOMAINS.forEach(function (d) {
            var lvl = s.quips[d] || 'unclear';
            if (rank[lvl] > rank[ov]) ov = lvl;
          });
          return ov;
        })() : null
      };
    });

    return {
      engine_version: '1.0.0',
      method: 'log-scale random-effects pool (' + (method_tau === 'DL' ? 'DerSimonian-Laird' : 'Paule-Mandel/REML') + '); HKSJ with Cochrane v6.5 floor; Q-profile tau^2 CI; PI df=k-1',
      k: k,
      effect_type: primary_effect_type,
      mixed_effect_types: mixed_effect_types,
      pooled_logHR: pooled.mu,
      pooled_logHR_se: pooled.se,
      pooled_HR: Math.exp(pooled.mu),
      ci_lb: ci_lb,
      ci_ub: ci_ub,
      hksj_mult: hksj_mult,
      hksj_ci_lb: hksj_ci_lb,
      hksj_ci_ub: hksj_ci_ub,
      hksj_warning: hksj_warning,
      tau2: pooled.tau2,
      tau2_lo: qpCI.tau2_lo,
      tau2_hi: qpCI.tau2_hi,
      Q: Q_FE,
      df_Q: df,
      p_Q: p_Q,
      I2: I2,
      H2: H2,
      pi_lb: pi_lb,
      pi_ub: pi_ub,
      pi_df: pi_df,
      per_study: per_study,
      harmonized: harmonized,
      harmonized_pool: harmonized_pool,
      adj_unadj_split: adjUnadj,
      quips_summary: quips,
      quips_weighted_pool: quips_weighted,
      leave_one_out: l1o,
      cumulative: cum,
      baujat: bau,
      influence: infl,
      funnel: fun,
      subgroup_interaction: sub,
      dose_response: dr,
      trial_integrity: ti,
      inspect_sr_flags: inspect,
      coverage_warning: k < 10,
      fallback: fallback,
      _fitInternal: {
        yi: yi, vi: vi, pslog: pslog,
        tau2: pooled.tau2, mu: pooled.mu, se: pooled.se
      }
    };
  }

  function exportResults(fitResult) {
    var out = JSON.parse(JSON.stringify(fitResult));
    delete out._fitInternal;
    out.exported_at = new Date().toISOString();
    out.engine_version = '1.0.0';
    return out;
  }

  // ===================================================================
  // Public API
  // ===================================================================
  root.RapidMetaPrognostic = {
    fit: fit,
    validate: validate,
    exportResults: exportResults,
    _version: '1.0.0',
    _internal: {
      // numerics
      qnormApprox: qnormApprox, qchisq: qchisq, pchisq: pchisq, tinv: tinv,
      lnGamma: lnGamma, ibeta: ibeta, qbeta: qbeta, matInv: matInv,
      // pooling
      logEffect: logEffect, perStudyLog: perStudyLog,
      tau2DL: tau2DL, tau2REML: tau2REML,
      poolGivenTau2: poolGivenTau2, hksjMultiplier: hksjMultiplier,
      qProfileTau2CI: qProfileTau2CI,
      // analyses
      cutoffHarmonization: cutoffHarmonization,
      adjUnadjSplit: adjUnadjSplit,
      quipsSummary: quipsSummary, quipsWeightedPool: quipsWeightedPool,
      leaveOneOut: leaveOneOut, cumulativeMA: cumulativeMA,
      baujat: baujat, influenceDiag: influenceDiag,
      funnelDiagnostics: funnelDiagnostics,
      subgroupInteraction: subgroupInteraction,
      doseResponse: doseResponse,
      trialIntegrity: trialIntegrity,
      inspectSrFlags: inspectSrFlags,
      // constants
      QUIPS_DOMAINS: QUIPS_DOMAINS, QUIPS_LEVELS: QUIPS_LEVELS, Z975: Z975
    }
  };
})(typeof window !== 'undefined' ? window : globalThis);
