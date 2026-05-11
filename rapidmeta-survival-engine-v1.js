/* rapidmeta-survival-engine-v1.js — v1.0.0 (2026-05-11)
 *
 * Self-contained frequentist survival meta-analysis engine for RapidMeta SURV apps.
 * Mirrors the API surface of rapidmeta-dta-engine-v1.js.
 *
 * Layers:
 *   1. Pooled log-HR via REML + HKSJ (Cochrane v6.5 §10.10.4 stack)
 *   2. Non-PH detection (Schoenfeld p<0.05 OR curve_crosses)
 *   3. RMST-difference pool at fixed tau* (Karrison/Royston-Parmar)
 *   4. Interval-HR pool from published per-window HRs
 *   5. NNT-for-HR conversion (Altman 2002)
 *
 * Validated against metafor::rma at |Delta| < 1e-3 via webr-survival-validator.js.
 *
 * Load as <script src="rapidmeta-survival-engine-v1.js" defer></script>;
 * exposes window.RapidMetaSurvival.{fit, validate, exportResults, predict, forest,
 *   rmstAtTau, poolRMSTDiff, intervalHRPool, nonPHDetect, nntForHR}.
 */
(function (root) {
  'use strict';

  // ============================================================
  // Numerical helpers (copied / adapted from rapidmeta-dta-engine-v1.js)
  // ============================================================

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
    var fpmin = 1e-30, qab = a + b, qap = a + 1, qam = a - 1, cc = 1, d = 1 - qab * x / qap;
    if (Math.abs(d) < fpmin) d = fpmin;
    d = 1 / d; var h = d;
    for (var m = 1; m <= 200; m++) {
      var m2 = 2 * m, aa = m * (b - m) * x / ((qam + m2) * (a + m2));
      d = 1 + aa * d; if (Math.abs(d) < fpmin) d = fpmin;
      cc = 1 + aa / cc; if (Math.abs(cc) < fpmin) cc = fpmin;
      d = 1 / d; h *= d * cc;
      aa = -(a + m) * (qab + m) * x / ((a + m2) * (qap + m2));
      d = 1 + aa * d; if (Math.abs(d) < fpmin) d = fpmin;
      cc = 1 + aa / cc; if (Math.abs(cc) < fpmin) cc = fpmin;
      d = 1 / d;
      var del = d * cc; h *= del;
      if (Math.abs(del - 1) < 3e-7) break;
    }
    return h;
  }
  function ibeta(a, b, x) {
    if (x <= 0) return 0; if (x >= 1) return 1;
    var bt = Math.exp(lnGamma(a + b) - lnGamma(a) - lnGamma(b) + a * Math.log(x) + b * Math.log(1 - x));
    if (x < (a + 1) / (a + b + 2)) return bt * betacf(a, b, x) / a;
    return 1 - bt * betacf(b, a, 1 - x) / b;
  }
  function qbeta(p, a, b) {
    var lo = 0, hi = 1, mid;
    for (var i = 0; i < 60; i++) {
      mid = (lo + hi) / 2;
      if (ibeta(a, b, mid) < p) lo = mid; else hi = mid;
    }
    return mid;
  }
  function _qnormApprox(p) {
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
  function qchisq(p, df) {
    if (df <= 0 || p <= 0) return 0;
    if (p >= 1) return Infinity;
    if (df === 1) {
      var z = _qnormApprox((1 + p) / 2);
      return z * z;
    }
    if (df === 2) return -2 * Math.log(1 - p);
    var z2 = _qnormApprox(p);
    var v = 1 - 2 / (9 * df) + z2 * Math.sqrt(2 / (9 * df));
    return Math.max(0, df * v * v * v);
  }
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

  var Z975 = 1.959963984540054;

  // ============================================================
  // Per-study log-HR
  // ============================================================

  function perStudy(trial) {
    var HR = +trial.HR;
    var lo = +trial.HR_ci_lo, hi = +trial.HR_ci_hi;
    var logHR = Math.log(HR);
    var seLogHR = (Math.log(hi) - Math.log(lo)) / (2 * Z975);
    return {
      studlab: trial.studlab,
      HR: HR,
      HR_ci: [lo, hi],
      logHR: logHR,
      seLogHR: seLogHR,
      varLogHR: seLogHR * seLogHR
    };
  }

  // ============================================================
  // Validation
  // ============================================================

  function validate(trials) {
    var issues = [];
    if (!Array.isArray(trials)) { issues.push('trials must be an array'); return issues; }
    if (trials.length === 0) { issues.push('trials array must be non-empty'); return issues; }
    for (var i = 0; i < trials.length; i++) {
      var t = trials[i];
      if (t === null || typeof t !== 'object' || Array.isArray(t)) {
        issues.push('trial ' + i + ': must be a plain object'); continue;
      }
      var sl = t.studlab || ('#' + i);
      if (typeof t.HR !== 'number' || !isFinite(t.HR) || t.HR <= 0) {
        issues.push('trial ' + i + ' (' + sl + '): HR must be a positive finite number');
        continue;
      }
      if (t.HR_ci_lo == null || t.HR_ci_hi == null) {
        issues.push('trial ' + i + ' (' + sl + '): HR_ci_lo and HR_ci_hi required');
        continue;
      }
      var lo = +t.HR_ci_lo, hi = +t.HR_ci_hi;
      if (!isFinite(lo) || !isFinite(hi) || lo <= 0 || hi <= 0) {
        issues.push('trial ' + i + ' (' + sl + '): HR_ci_lo/HR_ci_hi must be positive');
        continue;
      }
      if (lo > hi) {
        issues.push('trial ' + i + ' (' + sl + '): HR_ci_lo > HR_ci_hi (' + lo + ' > ' + hi + ')');
        continue;
      }
      if (lo === hi) {
        issues.push('trial ' + i + ' (' + sl + '): HR_ci_lo === HR_ci_hi gives zero-width CI ' +
                    '(seLogHR=0 → infinite weight); a CI of width 0 is not interpretable');
        continue;
      }
      // CI-brackets-HR sanity (catches transcription errors where HR is outside its own CI).
      // Allow a tiny rounding tolerance (0.5% on log scale).
      var logHR = Math.log(t.HR);
      var logLo = Math.log(lo), logHi = Math.log(hi);
      if (logHR < logLo - 5e-3 || logHR > logHi + 5e-3) {
        issues.push('trial ' + i + ' (' + sl + '): HR ' + t.HR +
                    ' lies outside its own 95% CI [' + lo + ', ' + hi + '] — ' +
                    'likely transcription error in source data');
      }
    }
    return issues;
  }

  // ============================================================
  // Inverse-variance pool at given tau2
  // ============================================================

  function ivPool(yi, vi, tau2) {
    if (yi.length === 0) return { mu: NaN, se: NaN, k: 0 };
    var sumW = 0, sumWY = 0;
    for (var i = 0; i < yi.length; i++) {
      var w = 1 / (vi[i] + (tau2 || 0));
      sumW += w; sumWY += w * yi[i];
    }
    return {
      mu: sumWY / sumW,
      se: Math.sqrt(1 / sumW),
      k: yi.length,
      sumW: sumW
    };
  }

  // ============================================================
  // Q statistic
  // ============================================================

  function computeQ(yi, vi, mu) {
    var Q = 0;
    for (var i = 0; i < yi.length; i++) {
      var w = 1 / vi[i];
      Q += w * (yi[i] - mu) * (yi[i] - mu);
    }
    return Q;
  }

  // ============================================================
  // DerSimonian-Laird tau2 (used as REML warm-start)
  // ============================================================

  function dlTau2(yi, vi) {
    var k = yi.length;
    if (k < 2) return 0;
    var feMu = ivPool(yi, vi, 0).mu;
    var Q = computeQ(yi, vi, feMu);
    var sumW = 0, sumW2 = 0;
    for (var i = 0; i < k; i++) {
      var w = 1 / vi[i];
      sumW += w; sumW2 += w * w;
    }
    var c = sumW - sumW2 / sumW;
    if (c <= 0) return 0;
    return Math.max(0, (Q - (k - 1)) / c);
  }

  // ============================================================
  // REML tau2 (Fisher scoring, Viechtbauer 2005 §3.1)
  // ============================================================

  function remlTau2(yi, vi, opts) {
    opts = opts || {};
    var max_iter = opts.max_iter || 200;
    var tol = opts.tol || 1e-10;
    var k = yi.length;
    if (k < 2) return { tau2: 0, iterations: 0, converged: true };

    // Warm-start with DL clamped to positive
    var tau2 = Math.max(0.0001, dlTau2(yi, vi));
    var iter = 0, converged = false, dampening = 1.0;

    for (iter = 0; iter < max_iter; iter++) {
      // Recompute weights and pooled mean at current tau2
      var sumW = 0, sumWY = 0;
      var ws = new Array(k);
      for (var i = 0; i < k; i++) {
        ws[i] = 1 / (vi[i] + tau2);
        sumW += ws[i];
        sumWY += ws[i] * yi[i];
      }
      var muHat = sumWY / sumW;
      // REML score: U(tau2) = sum( w_i^2 * ((y_i - mu)^2 - v_i - tau2 + 1/sumW) )
      //   (the 1/sumW term is the REML correction vs ML)
      var U = 0, I = 0;
      for (var i = 0; i < k; i++) {
        var w = ws[i];
        var resid = yi[i] - muHat;
        U += w * w * (resid * resid - vi[i] - tau2);
        I += w * w * w * (resid * resid - 0.5 * (vi[i] + tau2));
      }
      // REML correction: + (1/sumW) * sum(w_i^2)
      var sumW2 = 0;
      for (var i = 0; i < k; i++) sumW2 += ws[i] * ws[i];
      U += sumW2 / sumW;
      // Information matrix (positive semi-definite). Cap from below.
      var info = 0;
      for (var i = 0; i < k; i++) info += ws[i] * ws[i];
      info = 0.5 * info;
      if (info < 1e-12) break;
      var delta = U / (2 * info);
      var tau2_new = tau2 + dampening * delta;
      if (tau2_new < 0) tau2_new = 0;
      if (Math.abs(tau2_new - tau2) < tol) { tau2 = tau2_new; converged = true; break; }
      tau2 = tau2_new;
    }
    return { tau2: tau2, iterations: iter, converged: converged };
  }

  // ============================================================
  // Q-profile tau2 CI (Viechtbauer 2007)
  // ============================================================

  function qProfileTau2CI(yi, vi, df, alpha) {
    if (df < 1 || yi.length < 2) return { tau2_lo: NaN, tau2_hi: NaN };
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
      for (var _e = 0; _e < 30 && qGen(hi) > target && hi < 1e8; _e++) hi *= 2;
      for (var _i = 0; _i < 60; _i++) {
        var mid = (lo + hi) / 2;
        if (qGen(mid) > target) lo = mid; else hi = mid;
      }
      return (lo + hi) / 2;
    }
    return { tau2_lo: bisect(cutHi), tau2_hi: bisect(cutLo) };
  }

  // ============================================================
  // HKSJ adjustment (Hartung-Knapp 2001, Roever 2015 with floor)
  // ============================================================

  function hksjAdjust(yi, vi, tau2, muAxis, df) {
    if (df < 1 || yi.length < 2) return { adj: NaN, qstar: NaN };
    var t2 = (typeof tau2 === 'number' && isFinite(tau2)) ? tau2 : 0;
    var sumW = 0, qStar = 0;
    for (var i = 0; i < yi.length; i++) {
      var w = 1 / (vi[i] + t2);
      sumW += w;
      qStar += w * (yi[i] - muAxis) * (yi[i] - muAxis);
    }
    qStar /= df;
    // Cochrane v6.5 floor (advanced-stats.md): max(1, Q/(k-1)) to avoid narrowing
    return { adj: Math.max(1, qStar), qstar: qStar };
  }

  // ============================================================
  // Prediction interval (Higgins-Riley, Cochrane v6.5 §10.10.4.3, df=k-1)
  // ============================================================

  function predictionInterval(yi, vi, tau2, df, alpha) {
    if (df < 1 || yi.length < 3) return { pi_lo: null, pi_hi: null, df: df };
    var pool = ivPool(yi, vi, tau2);
    var t = tinv(1 - alpha / 2, df);
    if (!isFinite(t)) return { pi_lo: null, pi_hi: null, df: df };
    var pi_se = Math.sqrt(tau2 + pool.se * pool.se);
    return {
      pi_lo: pool.mu - t * pi_se,
      pi_hi: pool.mu + t * pi_se,
      df: df
    };
  }

  // ============================================================
  // poolLogHR: orchestrate REML + HKSJ
  // ============================================================

  function poolLogHR(yi, vi, opts) {
    opts = opts || {};
    var method = opts.tau2_method || 'reml';
    var k = yi.length;
    var tau2 = 0, iterations = 0, converged = true;
    if (k >= 2) {
      if (method === 'reml') {
        var reml = remlTau2(yi, vi);
        tau2 = reml.tau2; iterations = reml.iterations; converged = reml.converged;
      } else {
        tau2 = dlTau2(yi, vi);
      }
    }
    var pool = ivPool(yi, vi, tau2);
    var fePool = ivPool(yi, vi, 0);
    var Q = computeQ(yi, vi, fePool.mu);
    var Q_df = Math.max(0, k - 1);
    var I2 = Q_df > 0 ? Math.max(0, Math.min(100, (Q - Q_df) / Q * 100)) : 0;
    var H2 = Q_df > 0 ? Math.max(1, Q / Q_df) : 1;
    return {
      mu: pool.mu, se: pool.se, k: k, tau2: tau2,
      Q: Q, Q_df: Q_df, I2: I2, H2: H2,
      iterations: iterations, converged: converged
    };
  }

  // ============================================================
  // Non-PH detector
  // ============================================================

  function nonPHDetect(trials) {
    var k = trials.length;
    var flagged = [];
    var minP = null;
    var n_schoenfeld_reported = 0;
    var n_curve_crosses_reported = 0;
    for (var i = 0; i < k; i++) {
      var t = trials[i];
      var p = (typeof t.schoenfeld_p === 'number' && isFinite(t.schoenfeld_p)) ? t.schoenfeld_p : null;
      var crosses = (t.curve_crosses === true);
      var crosses_reported = (typeof t.curve_crosses === 'boolean');
      var hit = (p !== null && p < 0.05) || crosses;
      if (hit) flagged.push({ studlab: t.studlab, schoenfeld_p: p, curve_crosses: crosses });
      if (p !== null) {
        n_schoenfeld_reported++;
        if (minP === null || p < minP) minP = p;
      }
      if (crosses_reported) n_curve_crosses_reported++;
    }
    // "data_available" distinguishes "all trials report PH-supported" from "no trials
    // report Schoenfeld at all". Same flag=false outcome, very different evidential weight.
    var n_with_any_signal = 0;
    for (var j = 0; j < k; j++) {
      var tt = trials[j];
      var has_p = typeof tt.schoenfeld_p === 'number' && isFinite(tt.schoenfeld_p);
      var has_cc = typeof tt.curve_crosses === 'boolean';
      if (has_p || has_cc) n_with_any_signal++;
    }
    return {
      flag: flagged.length > 0,
      n_flagged: flagged.length,
      fraction_flagged: k > 0 ? flagged.length / k : 0,
      schoenfeld_p_min: minP,
      flagged_trials: flagged,
      n_schoenfeld_reported: n_schoenfeld_reported,
      n_curve_crosses_reported: n_curve_crosses_reported,
      n_trials_with_any_ph_signal: n_with_any_signal,
      data_completeness: k > 0 ? n_with_any_signal / k : 0,
      verdict_quality: k === 0 ? 'no_trials' :
                       n_with_any_signal === 0 ? 'no_data' :
                       n_with_any_signal < k ? 'partial_data' :
                       'complete_data'
    };
  }

  // ============================================================
  // RMST trapezoid integral
  // ============================================================

  function rmstAtTau(km_curve, tau) {
    if (!Array.isArray(km_curve) || km_curve.length < 2) {
      throw new Error('rmstAtTau: km_curve must be array of length >= 2');
    }
    // Sort by t_months
    var pts = km_curve.slice().sort(function (a, b) { return a.t_months - b.t_months; });
    var last_t = pts[pts.length - 1].t_months;
    var tau_eff = Math.min(tau, last_t);
    // Sum trapezoids 0..tau_eff
    var rmst = 0;
    var var_rmst = 0; // Greenwood-style approximation
    for (var i = 0; i < pts.length - 1; i++) {
      var t0 = pts[i].t_months, t1 = pts[i + 1].t_months;
      var s0 = pts[i].surv, s1 = pts[i + 1].surv;
      if (t0 >= tau_eff) break;
      var t1_eff = Math.min(t1, tau_eff);
      // Linear-interp survival at t1_eff if truncated
      var s_at = s1;
      if (t1_eff < t1) {
        var frac = (t1_eff - t0) / (t1 - t0);
        s_at = s0 + frac * (s1 - s0);
      }
      rmst += 0.5 * (t1_eff - t0) * (s0 + s_at);
      // Variance contribution (simplified — exact requires d_i events per interval)
      var n0 = pts[i].n_at_risk || null;
      if (n0 && n0 > 0) {
        // dS ~ s0 - s_at; per Karrison 2018 simplified
        var dS = s0 - s_at;
        if (dS > 0) {
          var width = t1_eff - t0;
          var w2 = 0.5 * (width * (last_t - t0) + (last_t - t1_eff) * (last_t - t1_eff));
          var n_eff = Math.max(n0 - dS * n0, 1);
          var_rmst += w2 * w2 * dS / (n0 * n_eff);
        }
      }
    }
    // SE here is a Karrison-style approximation only — the exact Karrison 1987 formula
    // needs per-interval events d_i, which the engine doesn't have unless reconstructed
    // IPD coordinates are supplied. The point estimate (rmst) is exact via trapezoid.
    return {
      rmst: rmst,
      se_approximate: var_rmst > 0 ? Math.sqrt(var_rmst) : null,
      se: var_rmst > 0 ? Math.sqrt(var_rmst) : null,  // kept for backward compatibility
      tau_effective: tau_eff,
      se_method: 'karrison_finite_difference_approx',
      se_caveat: 'Approximation; exact Karrison requires per-interval event counts d_i'
    };
  }

  // ============================================================
  // Pool RMST differences
  // ============================================================

  function poolRMSTDiff(trials, tau, opts) {
    opts = opts || {};
    var yi = [], vi = [], per_study = [];
    for (var i = 0; i < trials.length; i++) {
      var t = trials[i];
      if (!t.km_curve) continue;
      var trt_curve = t.km_curve.map(function (p) {
        return { t_months: p.t_months, surv: p.surv_trt, n_at_risk: p.n_at_risk_trt };
      });
      var ctl_curve = t.km_curve.map(function (p) {
        return { t_months: p.t_months, surv: p.surv_ctl, n_at_risk: p.n_at_risk_ctl };
      });
      var trt_rmst = rmstAtTau(trt_curve, tau);
      var ctl_rmst = rmstAtTau(ctl_curve, tau);
      var diff = trt_rmst.rmst - ctl_rmst.rmst;
      var var_trt = trt_rmst.se ? trt_rmst.se * trt_rmst.se : 0;
      var var_ctl = ctl_rmst.se ? ctl_rmst.se * ctl_rmst.se : 0;
      var v = var_trt + var_ctl;
      // If variance unavailable, use a rough proxy from N at midpoint
      if (v <= 0) {
        var n_proxy = (trt_curve[0].n_at_risk || 100) + (ctl_curve[0].n_at_risk || 100);
        v = (tau * tau) / n_proxy;
      }
      yi.push(diff); vi.push(v);
      per_study.push({
        studlab: t.studlab,
        rmst_trt: trt_rmst.rmst, rmst_ctl: ctl_rmst.rmst,
        rmst_diff: diff, se: Math.sqrt(v),
        tau_effective: trt_rmst.tau_effective
      });
    }
    if (yi.length === 0) return null;
    if (yi.length === 1) {
      return {
        k: 1, pooled_diff: yi[0], se: Math.sqrt(vi[0]),
        ci_lo: yi[0] - Z975 * Math.sqrt(vi[0]),
        ci_hi: yi[0] + Z975 * Math.sqrt(vi[0]),
        tau2: null, tau_star: tau,
        per_study: per_study,
        fallback: 'single_study'
      };
    }
    var pool = poolLogHR(yi, vi, { tau2_method: yi.length >= 5 ? 'reml' : 'dl' });
    return {
      k: pool.k, pooled_diff: pool.mu, se: pool.se,
      ci_lo: pool.mu - Z975 * pool.se,
      ci_hi: pool.mu + Z975 * pool.se,
      tau2: pool.tau2, Q: pool.Q, I2: pool.I2,
      tau_star: tau,
      per_study: per_study,
      fallback: yi.length < 5 ? 'fixed_effect_k_lt_5' : null
    };
  }

  // ============================================================
  // Interval-HR pool
  // ============================================================

  function intervalHRPool(trials, breakpoints) {
    if (!Array.isArray(breakpoints) || breakpoints.length < 2) {
      throw new Error('intervalHRPool: breakpoints array of length >= 2 required');
    }
    var any_intervals = false;
    for (var i = 0; i < trials.length; i++) {
      if (Array.isArray(trials[i].intervals) && trials[i].intervals.length > 0) {
        any_intervals = true; break;
      }
    }
    if (!any_intervals) return null;
    var out_intervals = [];
    for (var b = 0; b < breakpoints.length - 1; b++) {
      var t0 = breakpoints[b], t1 = breakpoints[b + 1];
      var yi = [], vi = [];
      for (var j = 0; j < trials.length; j++) {
        var t = trials[j];
        if (!Array.isArray(t.intervals)) continue;
        for (var k = 0; k < t.intervals.length; k++) {
          var iv = t.intervals[k];
          if (iv.t0 === t0 && iv.t1 === t1 && typeof iv.HR === 'number' &&
              isFinite(iv.HR) && iv.HR > 0 && iv.HR_ci_lo > 0 && iv.HR_ci_hi > 0) {
            var lnHR = Math.log(iv.HR);
            var seLnHR = (Math.log(iv.HR_ci_hi) - Math.log(iv.HR_ci_lo)) / (2 * Z975);
            yi.push(lnHR); vi.push(seLnHR * seLnHR);
            break;
          }
        }
      }
      if (yi.length === 0) continue;
      if (yi.length === 1) {
        out_intervals.push({
          label: t0 + '-' + t1 + 'm', t0: t0, t1: t1,
          HR: Math.exp(yi[0]),
          HR_ci_lo: Math.exp(yi[0] - Z975 * Math.sqrt(vi[0])),
          HR_ci_hi: Math.exp(yi[0] + Z975 * Math.sqrt(vi[0])),
          k: 1, tau2: null, fallback: 'single_study'
        });
        continue;
      }
      var pool = poolLogHR(yi, vi, { tau2_method: yi.length >= 5 ? 'reml' : 'dl' });
      out_intervals.push({
        label: t0 + '-' + t1 + 'm', t0: t0, t1: t1,
        HR: Math.exp(pool.mu),
        HR_ci_lo: Math.exp(pool.mu - Z975 * pool.se),
        HR_ci_hi: Math.exp(pool.mu + Z975 * pool.se),
        k: pool.k, tau2: pool.tau2, I2: pool.I2,
        fallback: pool.k < 5 ? 'fixed_effect_k_lt_5' : null
      });
    }
    return out_intervals.length > 0 ? { intervals: out_intervals } : null;
  }

  // ============================================================
  // NNT from HR (Altman 2002)
  //   ARR = baseline_risk - (1 - (1-baseline_risk)^HR)
  //   NNT = 1 / |ARR|; NNTB if ARR > 0, NNTH if ARR < 0
  // ============================================================

  function nntForHR(HR, baseline_risk) {
    if (typeof HR !== 'number' || !isFinite(HR) || HR <= 0) {
      return { nnt: null, direction: null, error: 'HR must be positive finite number' };
    }
    if (typeof baseline_risk !== 'number' || baseline_risk < 0 || baseline_risk > 1) {
      return { nnt: null, direction: null, error: 'baseline_risk must be in [0,1]' };
    }
    if (Math.abs(HR - 1) < 1e-9) return { nnt: null, direction: 'no_effect', arr: 0 };
    var tx_risk = 1 - Math.pow(1 - baseline_risk, HR);
    var arr = baseline_risk - tx_risk;
    if (Math.abs(arr) < 1e-12) return { nnt: null, direction: 'no_effect', arr: 0 };
    return {
      nnt: 1 / Math.abs(arr),
      direction: arr > 0 ? 'NNTB' : 'NNTH',
      arr: arr,
      tx_risk: tx_risk,
      baseline_risk: baseline_risk
    };
  }

  // ============================================================
  // Forest layout (paired HR / RMST rows)
  // ============================================================

  function forest(trials, fitResult) {
    var rows = trials.map(function (t, i) {
      var ps = perStudy(t);
      return {
        idx: i, studlab: t.studlab,
        HR: ps.HR, HR_ci: ps.HR_ci,
        logHR: ps.logHR, seLogHR: ps.seLogHR
      };
    });
    rows.push({
      idx: -1, studlab: 'Pooled',
      HR: fitResult.pooled_HR,
      HR_ci: [fitResult.pooled_HR_ci_lo, fitResult.pooled_HR_ci_hi],
      HR_ci_hksj: [fitResult.pooled_HR_hksj_ci_lo, fitResult.pooled_HR_hksj_ci_hi],
      is_pooled: true
    });
    return rows;
  }

  // ============================================================
  // Top-level fit
  // ============================================================

  function fit(trials, opts) {
    opts = opts || {};
    var issues = validate(trials);
    if (issues.length > 0) throw new Error('invalid input: ' + issues.join('; '));

    var k = trials.length;
    var per_study_full = trials.map(perStudy);
    var yi = per_study_full.map(function (p) { return p.logHR; });
    var vi = per_study_full.map(function (p) { return p.varLogHR; });

    // Estimator selection
    var estimator, fallback = null;
    var poolResult;
    if (k === 1) {
      estimator = 'single_study'; fallback = 'single_study';
      poolResult = { mu: yi[0], se: Math.sqrt(vi[0]), k: 1, tau2: null,
                     Q: 0, Q_df: 0, I2: 0, H2: 1, iterations: 0, converged: true };
    } else if (k < 5) {
      estimator = 'fixed_effect'; fallback = 'fixed_effect_k_lt_5';
      var fe = ivPool(yi, vi, 0);
      var Q_fe = computeQ(yi, vi, fe.mu);
      poolResult = { mu: fe.mu, se: fe.se, k: k, tau2: 0,
                     Q: Q_fe, Q_df: k - 1,
                     I2: k > 1 ? Math.max(0, Math.min(100, (Q_fe - (k - 1)) / Q_fe * 100)) : 0,
                     H2: k > 1 ? Math.max(1, Q_fe / (k - 1)) : 1,
                     iterations: 0, converged: true };
    } else {
      estimator = 'reml_hksj';
      poolResult = poolLogHR(yi, vi, { tau2_method: 'reml' });
    }

    // Wald CI on log scale
    var pooled_HR = Math.exp(poolResult.mu);
    var pooled_HR_ci_lo = Math.exp(poolResult.mu - Z975 * poolResult.se);
    var pooled_HR_ci_hi = Math.exp(poolResult.mu + Z975 * poolResult.se);

    // HKSJ adjustment + CI
    var hksjAdj = NaN, hksjQstar = NaN;
    var hksjLo = NaN, hksjHi = NaN;
    if (k >= 2 && estimator !== 'single_study') {
      var hksjOut = hksjAdjust(yi, vi, poolResult.tau2 || 0, poolResult.mu, k - 1);
      hksjAdj = hksjOut.adj; hksjQstar = hksjOut.qstar;
      var seHksj = Math.sqrt(hksjAdj) * poolResult.se;
      var t975 = tinv(0.975, k - 1);
      if (isFinite(t975)) {
        hksjLo = Math.exp(poolResult.mu - t975 * seHksj);
        hksjHi = Math.exp(poolResult.mu + t975 * seHksj);
      }
    }

    // Q-profile tau2 CI
    var tau2CI = { tau2_lo: NaN, tau2_hi: NaN };
    if (k >= 2 && estimator !== 'single_study') {
      tau2CI = qProfileTau2CI(yi, vi, k - 1, 0.05);
    }

    // Prediction interval (PI), Cochrane v6.5 df=k-1
    var pi_HR_lo = null, pi_HR_hi = null, pi_df = null;
    if (k >= 3 && estimator !== 'single_study') {
      var pi = predictionInterval(yi, vi, poolResult.tau2 || 0, k - 1, 0.05);
      if (pi.pi_lo !== null) {
        pi_HR_lo = Math.exp(pi.pi_lo);
        pi_HR_hi = Math.exp(pi.pi_hi);
        pi_df = pi.df;
      }
    }

    // Non-PH detection
    var nonph = nonPHDetect(trials);

    // RMST pool (if any trials have km_curve)
    var rmst_block = null;
    var trialsWithKM = trials.filter(function (t) { return Array.isArray(t.km_curve) && t.km_curve.length >= 2; });
    if (trialsWithKM.length > 0 && opts.rmst_tau) {
      rmst_block = poolRMSTDiff(trialsWithKM, opts.rmst_tau);
    }

    // Interval-HR pool (if any trials have intervals)
    var interval_hr_block = null;
    if (opts.interval_breakpoints) {
      interval_hr_block = intervalHRPool(trials, opts.interval_breakpoints);
    }

    var fitInternal = {
      yi: yi, vi: vi, mu_logHR: poolResult.mu, se_logHR: poolResult.se,
      tau2: poolResult.tau2, Q: poolResult.Q, Q_df: poolResult.Q_df,
      I2: poolResult.I2, H2: poolResult.H2,
      estimator: estimator
    };

    return {
      k: k,
      pooled_HR: pooled_HR,
      pooled_logHR: poolResult.mu,
      pooled_logHR_se: poolResult.se,
      pooled_HR_ci_lo: pooled_HR_ci_lo,
      pooled_HR_ci_hi: pooled_HR_ci_hi,
      hksj_adj: hksjAdj,
      hksj_qstar: hksjQstar,
      pooled_HR_hksj_ci_lo: hksjLo,
      pooled_HR_hksj_ci_hi: hksjHi,
      tau2: poolResult.tau2,
      tau2_lo: tau2CI.tau2_lo,
      tau2_hi: tau2CI.tau2_hi,
      Q: poolResult.Q, Q_df: poolResult.Q_df,
      I2: poolResult.I2, H2: poolResult.H2,
      pi_HR_lo: pi_HR_lo, pi_HR_hi: pi_HR_hi, pi_df: pi_df,
      nonph: nonph,
      rmst: rmst_block,
      interval_hr: interval_hr_block,
      per_study: per_study_full,
      coverage_warning: k < 10,
      fallback: fallback,
      estimator: estimator,
      converged: poolResult.converged,
      iterations: poolResult.iterations,
      _fitInternal: fitInternal
    };
  }

  function predict(fitResult) {
    if (!fitResult || !fitResult._fitInternal) {
      return { pi_HR_lo: null, pi_HR_hi: null, df: null };
    }
    var k = fitResult.k;
    if (k < 3 || fitResult.estimator === 'single_study') {
      return { pi_HR_lo: null, pi_HR_hi: null, df: null };
    }
    var fi = fitResult._fitInternal;
    var pi = predictionInterval(fi.yi, fi.vi, fi.tau2 || 0, k - 1, 0.05);
    return {
      pi_HR_lo: pi.pi_lo !== null ? Math.exp(pi.pi_lo) : null,
      pi_HR_hi: pi.pi_hi !== null ? Math.exp(pi.pi_hi) : null,
      df: pi.df
    };
  }

  function exportResults(fitResult) {
    var out = JSON.parse(JSON.stringify(fitResult));
    delete out._fitInternal;
    out.exported_at = new Date().toISOString();
    out.engine_version = '1.0.0';
    return out;
  }

  // ============================================================
  // Public API
  // ============================================================

  root.RapidMetaSurvival = {
    fit: fit,
    validate: validate,
    exportResults: exportResults,
    predict: predict,
    forest: forest,
    rmstAtTau: rmstAtTau,
    poolRMSTDiff: poolRMSTDiff,
    intervalHRPool: intervalHRPool,
    nonPHDetect: nonPHDetect,
    nntForHR: nntForHR,
    _version: '1.0.0',
    _internal: {
      perStudy: perStudy,
      lnGamma: lnGamma, qbeta: qbeta, qchisq: qchisq, tinv: tinv,
      ivPool: ivPool, computeQ: computeQ,
      dlTau2: dlTau2, remlTau2: function (yi, vi, opts) { var r = remlTau2(yi, vi, opts); return r.tau2; },
      qProfileTau2CI: qProfileTau2CI,
      hksjAdjust: hksjAdjust,
      predictionInterval: predictionInterval,
      poolLogHR: poolLogHR
    }
  };
})(typeof window !== 'undefined' ? window : globalThis);
