/* rapidmeta-prediction-engine-v1.js — v1.0.0 (2026-05-11)
 *
 * Self-contained frequentist prediction-model meta-analysis engine for RapidMeta.
 * Pools four canonical performance metrics across validation cohorts of a single
 * clinical risk score (PCE, SCORE2, KFRE, MAGGIC, …):
 *
 *   1. Discrimination          — logit-C pool with Fisher / delta-method
 *                                back-transform (Snell 2018; Debray 2017 IPDMA)
 *   2. Calibration-in-the-large — raw-scale REML pool of calibration intercept
 *   3. Calibration slope       — raw-scale REML pool (1 = perfect)
 *   4. O/E ratio               — log-scale REML pool, back-transform via exp
 *
 * Optional: Brier score (raw-scale pool).
 *
 * Heterogeneity uses REML τ² with HKSJ small-sample CI and a Cochrane v6.5
 * prediction interval (t_{k-1} × √(τ² + SE_µ²)). Default per advanced-stats.md
 * "Never use DL for k<10 — REML or PM"; "HKSJ floor = max(1, Q/(k-1)) and
 * df = qt(α/2, k-1)"; PI t_{k-1} convention.
 *
 * Inputs:
 *   cohorts: [{
 *     studlab:   string,
 *     // discrimination
 *     C:         number in (0.5, 1),       // C-statistic / AUC
 *     C_se?:     number,                   // SE(C) on raw scale; if omitted,
 *                                          //   uses Hanley-McNeil with n_events/n_nonevents
 *     n_events?: number, n_nonevents?: number,
 *     // calibration
 *     calib_int?:    number,               // calibration-in-the-large (0 = perfect)
 *     calib_int_se?: number,
 *     calib_slope?:    number,             // calibration slope (1 = perfect)
 *     calib_slope_se?: number,
 *     // O/E
 *     OE?:        number,                  // observed/expected events
 *     OE_se_log?: number,                  // SE(log OE); else derived from n_observed
 *     n_observed?: number,
 *     // optional
 *     brier?: number, brier_se?: number,
 *     cohort_type?: 'derivation' | 'external',
 *     // PROBAST domain risk-of-bias (low|high|unclear)
 *     probast?: {
 *       participants?: 'low'|'high'|'unclear',
 *       predictors?:   'low'|'high'|'unclear',
 *       outcome?:      'low'|'high'|'unclear',
 *       analysis?:     'low'|'high'|'unclear'
 *     }
 *   }, …]
 *
 *   opts:    { tol: 1e-7, max_iter: 100, …}
 *
 * Outputs: see fit() — { k, C_pool, calib_int_pool, calib_slope_pool,
 *                       OE_pool, brier_pool, probast, dev_vs_external,
 *                       per_cohort_rows, _fitInternal }
 *
 * Load as <script src="rapidmeta-prediction-engine-v1.js" defer></script>;
 * exposes window.RapidMetaPrediction.{ fit, validate, forest, exportResults,
 *                                       probastSummary, devVsExternalSplit }.
 *
 * MIT license. No external dependencies.
 */
(function (root) {
  'use strict';

  // ---------- Numeric helpers ----------
  function logit(p) { return Math.log(p / (1 - p)); }
  function invLogit(x) { return 1 / (1 + Math.exp(-x)); }
  function clamp(v, lo, hi) { return Math.max(lo, Math.min(hi, v)); }
  function isFiniteNum(v) { return typeof v === 'number' && isFinite(v); }

  // Beasley-Springer-Moro inverse normal (Wichura 1988 AS241; good to ~7 digits)
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
      return (((((c[0]*q+c[1])*q+c[2])*q+c[3])*q+c[4])*q+c[5]) /
             ((((d[0]*q+d[1])*q+d[2])*q+d[3])*q+1);
    }
    if (p <= ph) {
      q = p - 0.5; r = q*q;
      return (((((a[0]*r+a[1])*r+a[2])*r+a[3])*r+a[4])*r+a[5])*q /
             (((((b[0]*r+b[1])*r+b[2])*r+b[3])*r+b[4])*r+1);
    }
    q = Math.sqrt(-2 * Math.log(1-p));
    return -(((((c[0]*q+c[1])*q+c[2])*q+c[3])*q+c[4])*q+c[5]) /
            ((((d[0]*q+d[1])*q+d[2])*q+d[3])*q+1);
  }

  // lnGamma / regularized incomplete beta (for tinv via beta-inversion)
  function lnGamma(z) {
    var c = [76.18009172947146,-86.50532032941677,24.01409824083091,
             -1.231739572450155,1.208650973866179e-3,-5.395239384953e-6];
    var x=z, y=z, tmp=x+5.5; tmp -= (x+0.5)*Math.log(tmp);
    var ser=1.000000000190015;
    for(var j=0;j<6;j++) ser+=c[j]/++y;
    return -tmp + Math.log(2.5066282746310005*ser/x);
  }
  function betacf(a, b, x) {
    var fpmin=1e-30, qab=a+b, qap=a+1, qam=a-1, c=1, d=1-qab*x/qap;
    if(Math.abs(d)<fpmin) d=fpmin; d=1/d; var h=d;
    for(var m=1;m<=200;m++){
      var m2=2*m, aa=m*(b-m)*x/((qam+m2)*(a+m2));
      d=1+aa*d; if(Math.abs(d)<fpmin) d=fpmin;
      c=1+aa/c; if(Math.abs(c)<fpmin) c=fpmin; d=1/d; h*=d*c;
      aa=-(a+m)*(qab+m)*x/((a+m2)*(qap+m2));
      d=1+aa*d; if(Math.abs(d)<fpmin) d=fpmin;
      c=1+aa/c; if(Math.abs(c)<fpmin) c=fpmin; d=1/d;
      var del=d*c; h*=del; if(Math.abs(del-1)<3e-7) break;
    }
    return h;
  }
  function ibeta(a, b, x) {
    if (x <= 0) return 0; if (x >= 1) return 1;
    var bt = Math.exp(lnGamma(a+b) - lnGamma(a) - lnGamma(b)
                    + a*Math.log(x) + b*Math.log(1-x));
    if (x < (a+1)/(a+b+2)) return bt*betacf(a,b,x)/a;
    return 1 - bt*betacf(b,a,1-x)/b;
  }
  function qbeta(p, a, b) {
    var lo = 0, hi = 1, mid;
    for(var i=0;i<60;i++){ mid=(lo+hi)/2; if (ibeta(a,b,mid) < p) lo=mid; else hi=mid; }
    return mid;
  }

  // Student-t inverse CDF via beta inversion
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

  // Chi-square quantile (Wilson-Hilferty for df>=3; closed form df=1,2)
  function qchisq(p, df) {
    if (df <= 0 || p <= 0) return 0;
    if (p >= 1) return Infinity;
    if (df === 1) { var z = _qnormApprox((1 + p) / 2); return z * z; }
    if (df === 2) return -2 * Math.log(1 - p);
    var z2 = _qnormApprox(p);
    var v = 1 - 2/(9*df) + z2 * Math.sqrt(2/(9*df));
    return Math.max(0, df * v * v * v);
  }

  // Chi-square upper tail probability (1-CDF) via Wilson-Hilferty
  function chi2UpperP(x, df) {
    if (x <= 0) return 1;
    if (df <= 0) return 1;
    var h = Math.pow(x/df, 1/3);
    var z = (h - (1 - 2/(9*df))) / Math.sqrt(2/(9*df));
    var phi = 0.5 * (1 + _erf(z / Math.SQRT2));
    return 1 - phi;
  }
  function _erf(x) {
    var sign = x < 0 ? -1 : 1; x = Math.abs(x);
    var a1 = 0.254829592, a2 = -0.284496736, a3 = 1.421413741,
        a4 = -1.453152027, a5 = 1.061405429, p = 0.3275911;
    var t = 1/(1+p*x);
    var y = 1 - (((((a5*t + a4)*t) + a3)*t + a2)*t + a1)*t * Math.exp(-x*x);
    return sign*y;
  }

  // ---------- Hanley-McNeil 1982 variance for C-statistic (AUC) ----------
  // var(C) when only (C, n_events, n_nonevents) are provided.
  function hanleyMcNeilVar(C, n_events, n_nonevents) {
    if (!isFiniteNum(C) || !isFiniteNum(n_events) || !isFiniteNum(n_nonevents)) return NaN;
    if (n_events <= 0 || n_nonevents <= 0) return NaN;
    if (C <= 0 || C >= 1) return NaN;
    var Q1 = C / (2 - C);
    var Q2 = 2 * C * C / (1 + C);
    var num = C*(1-C) + (n_events - 1)*(Q1 - C*C) + (n_nonevents - 1)*(Q2 - C*C);
    var v = num / (n_events * n_nonevents);
    return v > 0 ? v : NaN;
  }

  // Delta method: var(logit C) ≈ var(C) / (C*(1-C))^2
  function logitCSE(C, C_se) {
    if (!isFiniteNum(C) || !isFiniteNum(C_se)) return NaN;
    if (C <= 0 || C >= 1) return NaN;
    var d = C * (1 - C);
    if (d <= 0) return NaN;
    return C_se / d;
  }

  // Royston-Sauerbrei / Debray 2017 approximation:
  //   var(log O/E) ≈ (1 - O/N) / O   when n_observed events O reported on N participants.
  // For simplicity when only n_observed is given without N, fall back to 1/O (Snell 2018).
  function oeLogVar(n_observed, n_total) {
    if (!isFiniteNum(n_observed) || n_observed <= 0) return NaN;
    if (isFiniteNum(n_total) && n_total > n_observed) {
      return (1 - n_observed / n_total) / n_observed;
    }
    return 1 / n_observed;
  }

  // ---------- Validation ----------
  function validate(cohorts) {
    var issues = [];
    if (!Array.isArray(cohorts)) { issues.push('cohorts must be an array'); return issues; }
    if (cohorts.length === 0) { issues.push('cohorts array must be non-empty'); return issues; }
    for (var i = 0; i < cohorts.length; i++) {
      var c = cohorts[i];
      var lbl = (c && c.studlab) ? c.studlab : ('cohort_' + i);
      if (c === null || typeof c !== 'object' || Array.isArray(c)) {
        issues.push(lbl + ': must be a plain object'); continue;
      }
      // C-statistic is the only required field; everything else is optional
      if (!isFiniteNum(c.C)) {
        issues.push(lbl + ': C (C-statistic) must be a finite number');
      } else if (c.C <= 0 || c.C >= 1) {
        issues.push(lbl + ': C must be in (0, 1); got ' + c.C);
      } else if (c.C < 0.5) {
        issues.push(lbl + ': C < 0.5 — model performs worse than chance; verify direction');
      }
      // If C_se is missing, must have n_events and n_nonevents for Hanley-McNeil
      if (!isFiniteNum(c.C_se)) {
        if (!isFiniteNum(c.n_events) || c.n_events <= 0) {
          issues.push(lbl + ': missing C_se requires n_events > 0 for Hanley-McNeil variance');
        }
        if (!isFiniteNum(c.n_nonevents) || c.n_nonevents <= 0) {
          issues.push(lbl + ': missing C_se requires n_nonevents > 0 for Hanley-McNeil variance');
        }
      } else if (c.C_se <= 0) {
        issues.push(lbl + ': C_se must be > 0');
      }
      // Optional metric checks
      if (c.calib_int != null && !isFiniteNum(c.calib_int)) {
        issues.push(lbl + ': calib_int must be a finite number when provided');
      }
      if (c.calib_int_se != null && (!isFiniteNum(c.calib_int_se) || c.calib_int_se <= 0)) {
        issues.push(lbl + ': calib_int_se must be > 0 when provided');
      }
      if (c.calib_slope != null && !isFiniteNum(c.calib_slope)) {
        issues.push(lbl + ': calib_slope must be a finite number when provided');
      }
      if (c.calib_slope_se != null && (!isFiniteNum(c.calib_slope_se) || c.calib_slope_se <= 0)) {
        issues.push(lbl + ': calib_slope_se must be > 0 when provided');
      }
      if (c.OE != null) {
        if (!isFiniteNum(c.OE) || c.OE <= 0) {
          issues.push(lbl + ': OE (observed/expected) must be > 0 when provided');
        }
        if (!isFiniteNum(c.OE_se_log) && !isFiniteNum(c.n_observed)) {
          issues.push(lbl + ': OE provided but missing OE_se_log and n_observed');
        }
      }
      if (c.brier != null && (!isFiniteNum(c.brier) || c.brier < 0 || c.brier > 1)) {
        issues.push(lbl + ': brier must be in [0, 1] when provided');
      }
    }
    return issues;
  }

  // ---------- Per-cohort logit-C row ----------
  function perCohortDiscrimination(c) {
    var Cc = clamp(c.C, 1e-6, 1 - 1e-6);
    var logitC = logit(Cc);
    var varC;
    if (isFiniteNum(c.C_se) && c.C_se > 0) {
      varC = c.C_se * c.C_se;
    } else {
      varC = hanleyMcNeilVar(Cc, c.n_events, c.n_nonevents);
    }
    var seLogit;
    if (isFiniteNum(varC) && varC > 0) {
      var d = Cc * (1 - Cc);
      seLogit = Math.sqrt(varC) / d;
    } else {
      seLogit = NaN;
    }
    var z = 1.959963984540054;
    var ci_lo = invLogit(logitC - z * seLogit);
    var ci_hi = invLogit(logitC + z * seLogit);
    return {
      studlab: c.studlab,
      C: Cc,
      C_ci_lo: ci_lo,
      C_ci_hi: ci_hi,
      logitC: logitC,
      logitC_se: seLogit,
      varLogitC: seLogit * seLogit,
      cohort_type: c.cohort_type || 'external'
    };
  }

  function perCohortOE(c) {
    if (c.OE == null) return null;
    var logOE = Math.log(c.OE);
    var seLog;
    if (isFiniteNum(c.OE_se_log) && c.OE_se_log > 0) {
      seLog = c.OE_se_log;
    } else {
      var v = oeLogVar(c.n_observed, c.n_total);
      seLog = isFiniteNum(v) && v > 0 ? Math.sqrt(v) : NaN;
    }
    var z = 1.959963984540054;
    return {
      studlab: c.studlab,
      OE: c.OE,
      logOE: logOE,
      logOE_se: seLog,
      OE_ci_lo: Math.exp(logOE - z * seLog),
      OE_ci_hi: Math.exp(logOE + z * seLog),
      cohort_type: c.cohort_type || 'external'
    };
  }

  // ---------- REML τ² via Paule-Mandel iteration ----------
  // Paule-Mandel (1982) is an exact REML estimator for a single-axis random-effects
  // meta-analysis: solve Σ w_i² (y_i - μ_w)² / Σ w_i = (k-1) where w_i = 1/(v_i+τ²).
  // For k<10 advanced-stats.md prefers REML/PM over DL — PM is a robust REML solver
  // that converges without derivatives.
  function paule_mandel(yi, vi) {
    if (yi.length < 2) return { tau2: 0, mu: yi[0] || 0, se_mu: Math.sqrt(vi[0] || 0),
                                Q: 0, df: 0, sumW: 0, w: [], converged: true, iter: 0 };
    var k = yi.length;
    var tau2 = 0;
    var iter, converged = false;
    for (iter = 0; iter < 100; iter++) {
      var w = vi.map(function(v){ return 1/(v + tau2); });
      var sumW = w.reduce(function(a,b){ return a+b; }, 0);
      var muw = 0; for (var i=0; i<k; i++) muw += w[i]*yi[i]; muw /= sumW;
      var Q = 0; for (var i=0; i<k; i++) Q += w[i]*Math.pow(yi[i]-muw, 2);
      // PM update: solve for τ² such that Q = k-1
      if (k <= 1) break;
      var f = Q - (k - 1);
      if (Math.abs(f) < 1e-7) { converged = true; break; }
      // Derivative dQ/dτ² ≈ -Σ w_i² * (y_i - μ_w)² (negative)
      var dQ = 0;
      for (var j=0; j<k; j++) dQ -= w[j]*w[j] * Math.pow(yi[j]-muw, 2);
      if (Math.abs(dQ) < 1e-12) { converged = true; break; }
      var step = f / dQ;
      var next = tau2 - step;
      if (next < 0) next = tau2 / 2;
      if (Math.abs(next - tau2) < 1e-9) { tau2 = next; converged = true; break; }
      tau2 = next;
    }
    tau2 = Math.max(0, tau2);
    var w_final = vi.map(function(v){ return 1/(v + tau2); });
    var sumW_final = w_final.reduce(function(a,b){ return a+b; }, 0);
    var mu = 0; for (var i=0; i<k; i++) mu += w_final[i]*yi[i]; mu /= sumW_final;
    var se_mu = Math.sqrt(1 / sumW_final);
    // FE Q for I²
    var w_FE = vi.map(function(v){ return 1/v; });
    var sumW_FE = w_FE.reduce(function(a,b){ return a+b; }, 0);
    var mu_FE = 0; for (var i=0; i<k; i++) mu_FE += w_FE[i]*yi[i]; mu_FE /= sumW_FE;
    var Q_FE = 0; for (var i=0; i<k; i++) Q_FE += w_FE[i]*Math.pow(yi[i]-mu_FE, 2);
    return {
      tau2: tau2, mu: mu, se_mu: se_mu,
      Q: Q_FE, df: k - 1, sumW: sumW_final, w: w_final,
      converged: converged, iter: iter
    };
  }

  // HKSJ (Hartung-Knapp-Sidik-Jonkman) scale, with Cochrane v6.5 floor max(1, Q/(k-1)).
  // Uses t_{k-1} per advanced-stats.md "HKSJ df: qt(α/2, k-1) NOT qnorm".
  function hksjCI(pm, alpha) {
    if (pm.df < 1) return { ci_lo: NaN, ci_hi: NaN, hksj_factor: NaN };
    var qFactor = pm.Q / pm.df;
    var floor = Math.max(1, qFactor);
    var seAdj = pm.se_mu * Math.sqrt(floor);
    var t = tinv(1 - alpha/2, pm.df);
    return {
      ci_lo: pm.mu - t * seAdj,
      ci_hi: pm.mu + t * seAdj,
      hksj_factor: floor,
      se_adj: seAdj,
      t: t
    };
  }

  // Cochrane v6.5 PI: t_{k-1} × √(τ² + SE_µ²) — undefined for k < 3
  function predictionInterval(pm, alpha) {
    if (pm.df < 2) return { pi_lo: NaN, pi_hi: NaN, df: pm.df, defined: false };
    var t = tinv(1 - alpha/2, pm.df);
    var se = Math.sqrt(pm.tau2 + pm.se_mu * pm.se_mu);
    return {
      pi_lo: pm.mu - t * se,
      pi_hi: pm.mu + t * se,
      df: pm.df,
      defined: true,
      pi_se: se,
      t: t
    };
  }

  // ---------- Generic single-axis pool used by every metric ----------
  // yi, vi on the analysis scale (logit-C, raw calib int, raw slope, log OE, raw Brier).
  // Returns { mu, se_mu, ci_lo, ci_hi, pi_lo, pi_hi, tau2, I2, Q, k, hksj_factor }.
  function poolGeneric(yi, vi, opts) {
    opts = opts || {};
    var alpha = opts.alpha || 0.05;
    var k = yi.length;
    if (k === 0) return null;
    if (k === 1) {
      // Single cohort: report Wald CI on the analysis scale; no τ², no PI.
      var se0 = Math.sqrt(vi[0]);
      var z = 1.959963984540054;
      return {
        k: 1, mu: yi[0], se_mu: se0,
        ci_lo: yi[0] - z * se0, ci_hi: yi[0] + z * se0,
        pi_lo: NaN, pi_hi: NaN, pi_defined: false,
        tau2: NaN, I2: NaN, Q: 0, df_Q: 0,
        hksj_factor: NaN, t_crit: NaN,
        method: 'single_cohort_wald'
      };
    }
    var pm = paule_mandel(yi, vi);
    var hksj = hksjCI(pm, alpha);
    var pi = predictionInterval(pm, alpha);
    var I2 = (pm.Q > pm.df && pm.Q > 0) ? Math.max(0, (pm.Q - pm.df) / pm.Q) * 100 : 0;
    return {
      k: k,
      mu: pm.mu,
      se_mu: pm.se_mu,
      ci_lo: hksj.ci_lo,
      ci_hi: hksj.ci_hi,
      pi_lo: pi.pi_lo,
      pi_hi: pi.pi_hi,
      pi_defined: pi.defined,
      tau2: pm.tau2,
      I2: I2,
      Q: pm.Q,
      df_Q: pm.df,
      p_Q: chi2UpperP(pm.Q, pm.df),
      hksj_factor: hksj.hksj_factor,
      t_crit: hksj.t,
      weights: pm.w.map(function(w){ return w / pm.sumW; }),
      method: 'reml_pm_hksj',
      converged: pm.converged,
      iterations: pm.iter
    };
  }

  // ---------- PROBAST per-domain summary ----------
  // Domains: participants, predictors, outcome, analysis. Each: low|high|unclear.
  // Overall judgement per Wolff 2019 PROBAST manual:
  //   - low overall      if all four domains low
  //   - high overall     if at least one domain high
  //   - unclear otherwise
  function probastSummary(cohorts) {
    var domains = ['participants', 'predictors', 'outcome', 'analysis'];
    var levels = ['low', 'high', 'unclear'];
    var byDomain = {};
    var byCohort = [];
    domains.forEach(function(d){
      byDomain[d] = { low: 0, high: 0, unclear: 0 };
    });
    var overall = { low: 0, high: 0, unclear: 0 };
    cohorts.forEach(function(c, idx){
      var p = c.probast || {};
      var row = { studlab: c.studlab || ('cohort_' + idx), domains: {}, overall: null };
      var anyHigh = false, anyUnclear = false, anyKnown = false;
      domains.forEach(function(d){
        var v = (p[d] || '').toLowerCase();
        if (levels.indexOf(v) >= 0) {
          row.domains[d] = v;
          byDomain[d][v]++;
          anyKnown = true;
          if (v === 'high') anyHigh = true;
          if (v === 'unclear') anyUnclear = true;
        } else {
          row.domains[d] = 'unclear';
          byDomain[d].unclear++;
          anyUnclear = true;
        }
      });
      if (!anyKnown) row.overall = 'unclear';
      else if (anyHigh) row.overall = 'high';
      else if (anyUnclear) row.overall = 'unclear';
      else row.overall = 'low';
      overall[row.overall]++;
      byCohort.push(row);
    });
    return {
      domains: byDomain,
      overall: overall,
      per_cohort: byCohort,
      n_cohorts: cohorts.length
    };
  }

  // ---------- Derivation vs external-validation split ----------
  // Subgroup analysis with Q_between (Cochran's Q on subgroup means).
  function devVsExternalSplit(cohorts, fitResult) {
    if (!fitResult || !fitResult.C_pool) return null;
    var dev = [], ext = [];
    fitResult.per_cohort_rows.forEach(function(r){
      var ct = (r.cohort_type || 'external').toLowerCase();
      var bucket = ct === 'derivation' ? dev : ext;
      bucket.push(r);
    });
    function poolBucket(rows) {
      var yi = [], vi = [];
      rows.forEach(function(r){
        if (isFiniteNum(r.logitC) && isFiniteNum(r.varLogitC) && r.varLogitC > 0) {
          yi.push(r.logitC); vi.push(r.varLogitC);
        }
      });
      if (yi.length === 0) return null;
      var pool = poolGeneric(yi, vi);
      if (!pool) return null;
      return {
        k: pool.k,
        C_pool: invLogit(pool.mu),
        C_ci_lo: invLogit(pool.ci_lo),
        C_ci_hi: invLogit(pool.ci_hi),
        tau2: pool.tau2, I2: pool.I2, Q: pool.Q
      };
    }
    var devPool = poolBucket(dev);
    var extPool = poolBucket(ext);
    // Q_between via fixed-effect contrast of subgroup means on logit-C scale
    var Q_b = null, df_b = null, p_b = null;
    if (devPool && extPool && devPool.k > 0 && extPool.k > 0) {
      var mu_d = logit(devPool.C_pool), mu_e = logit(extPool.C_pool);
      // SEs on logit scale need recomputation — derive from CI brackets symmetrically
      var se_d = (logit(devPool.C_ci_hi) - logit(devPool.C_ci_lo)) / (2 * 1.959963984540054);
      var se_e = (logit(extPool.C_ci_hi) - logit(extPool.C_ci_lo)) / (2 * 1.959963984540054);
      var pooled_var = se_d * se_d + se_e * se_e;
      if (pooled_var > 0) {
        Q_b = Math.pow(mu_d - mu_e, 2) / pooled_var;
        df_b = 1;
        p_b = chi2UpperP(Q_b, df_b);
      }
    }
    return {
      derivation: devPool,
      external: extPool,
      Q_between: Q_b,
      df_between: df_b,
      p_between: p_b,
      note: 'Q_between is a fixed-effect contrast of subgroup means on logit-C scale; ' +
            'interpret with caution when either subgroup is small.'
    };
  }

  // ---------- Forest plot row layouts ----------
  // Returns SVG-friendly per-cohort rows for each metric, plus pooled diamond row.
  // The host panel renders SVG.
  function forest(fitResult) {
    function metricRows(perCohortKey, pooledKey, backTransform) {
      var rows = [];
      fitResult.per_cohort_rows.forEach(function(r, i){
        if (!r[perCohortKey] || r[perCohortKey].skip) return;
        rows.push({
          idx: i,
          studlab: r.studlab,
          point: r[perCohortKey].point,
          ci_lo: r[perCohortKey].ci_lo,
          ci_hi: r[perCohortKey].ci_hi,
          weight: r[perCohortKey].weight,
          cohort_type: r.cohort_type
        });
      });
      var p = fitResult[pooledKey];
      if (p && isFiniteNum(p.mu)) {
        rows.push({
          idx: -1, studlab: 'Pooled (' + p.k + ')', is_pooled: true,
          point: backTransform ? backTransform(p.mu) : p.mu,
          ci_lo: backTransform ? backTransform(p.ci_lo) : p.ci_lo,
          ci_hi: backTransform ? backTransform(p.ci_hi) : p.ci_hi,
          pi_lo: backTransform && p.pi_defined ? backTransform(p.pi_lo) : p.pi_lo,
          pi_hi: backTransform && p.pi_defined ? backTransform(p.pi_hi) : p.pi_hi,
          tau2: p.tau2, I2: p.I2
        });
      }
      return rows;
    }
    return {
      discrimination: metricRows('discrimination_row', 'C_pool', invLogit),
      calib_int: metricRows('calib_int_row', 'calib_int_pool', null),
      calib_slope: metricRows('calib_slope_row', 'calib_slope_pool', null),
      OE: metricRows('OE_row', 'OE_pool', Math.exp),
      brier: metricRows('brier_row', 'brier_pool', null)
    };
  }

  // ---------- Main fit ----------
  function fit(cohorts, opts) {
    opts = opts || {};
    var issues = validate(cohorts);
    if (issues.length > 0) throw new Error('invalid input: ' + issues.join('; '));

    var rows = [];
    // Discrimination per-cohort
    var disc = cohorts.map(function(c){ return perCohortDiscrimination(c); });

    // Pool discrimination (logit-C scale)
    var yi_disc = [], vi_disc = [];
    disc.forEach(function(d){
      if (isFiniteNum(d.logitC) && isFiniteNum(d.varLogitC) && d.varLogitC > 0) {
        yi_disc.push(d.logitC); vi_disc.push(d.varLogitC);
      }
    });
    var discPool = poolGeneric(yi_disc, vi_disc);
    var C_pool = null;
    if (discPool) {
      C_pool = {
        k: discPool.k,
        mu: discPool.mu,                // on logit-C scale
        se_mu: discPool.se_mu,
        ci_lo: discPool.ci_lo,
        ci_hi: discPool.ci_hi,
        pi_lo: discPool.pi_lo,
        pi_hi: discPool.pi_hi,
        pi_defined: discPool.pi_defined,
        C_pool: invLogit(discPool.mu),
        C_ci_lo: invLogit(discPool.ci_lo),
        C_ci_hi: invLogit(discPool.ci_hi),
        C_pi_lo: discPool.pi_defined ? invLogit(discPool.pi_lo) : NaN,
        C_pi_hi: discPool.pi_defined ? invLogit(discPool.pi_hi) : NaN,
        tau2: discPool.tau2,
        I2: discPool.I2,
        Q: discPool.Q,
        df_Q: discPool.df_Q,
        p_Q: discPool.p_Q,
        hksj_factor: discPool.hksj_factor,
        weights: discPool.weights,
        method: discPool.method,
        converged: discPool.converged
      };
    }

    // Calibration intercept pool
    var yi_int = [], vi_int = [], idx_int = [];
    cohorts.forEach(function(c, i){
      if (isFiniteNum(c.calib_int) && isFiniteNum(c.calib_int_se) && c.calib_int_se > 0) {
        yi_int.push(c.calib_int);
        vi_int.push(c.calib_int_se * c.calib_int_se);
        idx_int.push(i);
      }
    });
    var calib_int_pool = poolGeneric(yi_int, vi_int);

    // Calibration slope pool
    var yi_sl = [], vi_sl = [], idx_sl = [];
    cohorts.forEach(function(c, i){
      if (isFiniteNum(c.calib_slope) && isFiniteNum(c.calib_slope_se) && c.calib_slope_se > 0) {
        yi_sl.push(c.calib_slope);
        vi_sl.push(c.calib_slope_se * c.calib_slope_se);
        idx_sl.push(i);
      }
    });
    var calib_slope_pool = poolGeneric(yi_sl, vi_sl);

    // O/E pool (log scale)
    var oe_per = cohorts.map(function(c){ return perCohortOE(c); });
    var yi_oe = [], vi_oe = [];
    oe_per.forEach(function(o){
      if (o && isFiniteNum(o.logOE) && isFiniteNum(o.logOE_se) && o.logOE_se > 0) {
        yi_oe.push(o.logOE); vi_oe.push(o.logOE_se * o.logOE_se);
      }
    });
    var oePool = poolGeneric(yi_oe, vi_oe);
    var OE_pool = null;
    if (oePool) {
      OE_pool = Object.assign({}, oePool, {
        OE_pool: Math.exp(oePool.mu),
        OE_ci_lo: Math.exp(oePool.ci_lo),
        OE_ci_hi: Math.exp(oePool.ci_hi),
        OE_pi_lo: oePool.pi_defined ? Math.exp(oePool.pi_lo) : NaN,
        OE_pi_hi: oePool.pi_defined ? Math.exp(oePool.pi_hi) : NaN
      });
    }

    // Brier pool (raw scale)
    var yi_br = [], vi_br = [];
    cohorts.forEach(function(c){
      if (isFiniteNum(c.brier) && isFiniteNum(c.brier_se) && c.brier_se > 0) {
        yi_br.push(c.brier); vi_br.push(c.brier_se * c.brier_se);
      }
    });
    var brier_pool = poolGeneric(yi_br, vi_br);

    // Per-cohort rows for forest (each with point, ci, weight per metric)
    var z95 = 1.959963984540054;
    cohorts.forEach(function(c, i){
      var d = disc[i];
      var o = oe_per[i];
      var row = {
        studlab: c.studlab || ('cohort_' + i),
        cohort_type: c.cohort_type || 'external',
        discrimination_row: null,
        calib_int_row: null,
        calib_slope_row: null,
        OE_row: null,
        brier_row: null,
        // Internal — used by devVsExternalSplit + tests
        logitC: d.logitC,
        varLogitC: d.varLogitC,
        C: d.C
      };
      if (isFiniteNum(d.logitC) && isFiniteNum(d.logitC_se)) {
        // Weight uses 1/(v_i + tau2) from pool when available
        var w = NaN;
        if (C_pool && isFiniteNum(C_pool.tau2)) {
          var wRaw = 1 / (d.varLogitC + C_pool.tau2);
          var sumW = C_pool.weights ? C_pool.weights.reduce(function(a){ return a + 1/(d.varLogitC + C_pool.tau2); }, 0) : 0;
          // simpler: pull weight from pool's weights array by matching order
          var slot = -1;
          for (var s = 0; s < disc.length; s++) {
            if (disc[s] === d) { slot = s; break; }
          }
          if (slot >= 0 && C_pool.weights && C_pool.weights[slot] != null) {
            w = C_pool.weights[slot];
          }
        }
        row.discrimination_row = {
          point: d.C,
          ci_lo: d.C_ci_lo,
          ci_hi: d.C_ci_hi,
          weight: isFiniteNum(w) ? w : null,
          skip: false
        };
      }
      if (isFiniteNum(c.calib_int) && isFiniteNum(c.calib_int_se)) {
        row.calib_int_row = {
          point: c.calib_int,
          ci_lo: c.calib_int - z95 * c.calib_int_se,
          ci_hi: c.calib_int + z95 * c.calib_int_se,
          skip: false
        };
      }
      if (isFiniteNum(c.calib_slope) && isFiniteNum(c.calib_slope_se)) {
        row.calib_slope_row = {
          point: c.calib_slope,
          ci_lo: c.calib_slope - z95 * c.calib_slope_se,
          ci_hi: c.calib_slope + z95 * c.calib_slope_se,
          skip: false
        };
      }
      if (o && isFiniteNum(o.logOE) && isFiniteNum(o.logOE_se)) {
        row.OE_row = {
          point: o.OE,
          ci_lo: o.OE_ci_lo,
          ci_hi: o.OE_ci_hi,
          skip: false
        };
      }
      if (isFiniteNum(c.brier) && isFiniteNum(c.brier_se)) {
        row.brier_row = {
          point: c.brier,
          ci_lo: c.brier - z95 * c.brier_se,
          ci_hi: c.brier + z95 * c.brier_se,
          skip: false
        };
      }
      rows.push(row);
    });

    var probast = probastSummary(cohorts);

    var result = {
      engine: 'rapidmeta-prediction',
      engine_version: '1.0.0',
      k: cohorts.length,
      k_C: discPool ? discPool.k : 0,
      k_calib_int: calib_int_pool ? calib_int_pool.k : 0,
      k_calib_slope: calib_slope_pool ? calib_slope_pool.k : 0,
      k_OE: oePool ? oePool.k : 0,
      k_brier: brier_pool ? brier_pool.k : 0,
      C_pool: C_pool,
      calib_int_pool: calib_int_pool,
      calib_slope_pool: calib_slope_pool,
      OE_pool: OE_pool,
      brier_pool: brier_pool,
      probast: probast,
      per_cohort_rows: rows,
      coverage_warning: cohorts.length < 5
    };

    // Derivation vs external split
    result.dev_vs_external = devVsExternalSplit(cohorts, result);

    return result;
  }

  // ---------- Export ----------
  function exportResults(fitResult) {
    var out = JSON.parse(JSON.stringify(fitResult));
    out.exported_at = new Date().toISOString();
    return out;
  }

  // ---------- Public API ----------
  root.RapidMetaPrediction = {
    fit: fit,
    validate: validate,
    forest: forest,
    probastSummary: probastSummary,
    devVsExternalSplit: devVsExternalSplit,
    exportResults: exportResults,
    _version: '1.0.0',
    _internal: {
      logit: logit, invLogit: invLogit, clamp: clamp,
      hanleyMcNeilVar: hanleyMcNeilVar,
      logitCSE: logitCSE,
      oeLogVar: oeLogVar,
      tinv: tinv, qchisq: qchisq, chi2UpperP: chi2UpperP, _qnormApprox: _qnormApprox,
      lnGamma: lnGamma, ibeta: ibeta, qbeta: qbeta,
      paule_mandel: paule_mandel,
      hksjCI: hksjCI,
      predictionInterval: predictionInterval,
      poolGeneric: poolGeneric,
      perCohortDiscrimination: perCohortDiscrimination,
      perCohortOE: perCohortOE
    }
  };
})(typeof window !== 'undefined' ? window : globalThis);
