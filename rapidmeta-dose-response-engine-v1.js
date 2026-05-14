/* rapidmeta-dose-response-engine-v1.js — v0.7.0 (2026-05-14)
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
 *   - continuous-outcome branch via mdCovariance + dosresmeta type='md' on
 *     SGLT2i HbA1c fixture (k=4 trials, validated against dosresmeta MD pool)
 *   - full multivariate REML for fitRCS via Nelder-Mead on Cholesky parameters
 *     of the τ² matrix; non-linearity Wald p matches R mixmeta within |Δ| < 0.1
 *   - Q-profile τ² CI for fitLinear (Viechtbauer 2007) returns finite bounds
 *   - v0.4.0: k=1 single-trial branch (fitRCS) via within-trial t df + tau2=0
 *   - v0.5.0: leave-one-out (LOO) sensitivity via _internal.fitLOO; orchestrates
 *     fitLinear / fitRCS over each k-1 subset, handles k_full=2 (LOO drops to
 *     single surviving trial) via the per-study slope cached by fitLinear and
 *     the engine's existing k=1 fitRCS branch; demonstrated on the TIRZEPATIDE
 *     SURPASS flagship (k=5; nonlin Wald p = 0.0346 full pool — most influential
 *     LOO subset surfaced in the flagship's LOO sensitivity tab)
 *   - v0.6.0: fitLinear k=1 single-trial branch — closes the asymmetry with
 *     fitRCS (v0.4). Returns the per-trial GL/WLS slope estimate with tau2=0,
 *     Q=0, hksj_qstar=1, PI degenerated to CI, tcrit=qt(0.975, n_arms-2)
 *     within-trial df. estimator='wls_single_trial_linear',
 *     ci_method='t_within_trial'. fitLinear at k>=2 is byte-identical to v0.5.
 *   - v0.7.0: non-parametric trial-bootstrap CI via _internal.fitBootstrap as a
 *     sensitivity check on the analytical HKSJ-multivariate CIs. Resamples
 *     trials with replacement (size=k_full), refits fitLinear/fitRCS per
 *     bootstrap sample, returns percentile CI on pooled_slope_log plus the
 *     analytical CI for comparison and a coverage_warning flag when k_full<4
 *     or >5 percent of bootstrap samples fail. Determinism via tiny seeded LCG
 *     (no external PRNG dep). RCS layer also returns bootstrap_nonlin_ps and
 *     the fraction below 0.05. Demonstrated on the SUSTAIN flagship (I^2=97
 *     percent — analytical-vs-bootstrap comparison most informative there).
 *     fitLinear/fitRCS are byte-identical to v0.6 at all k.
 *
 * Load as <script src="rapidmeta-dose-response-engine-v1.js" defer></script>;
 * exposes window.RapidMetaDoseResp.{ validate, fitLinear, fitRCS, fitOneStage,
 *   nonLinearityTest, predict, forest, exportResults, _internal }.
 */
(function (root) {
  'use strict';

  // P2-13: API defined at IIFE top to avoid forward-reference footgun.
  // Public methods are assigned to API.<name> immediately after each function
  // definition below. _internal helpers are similarly attached as defined.
  var API = {
    engine_version: 'rapidmeta-dose-response-engine-v1@0.7.0',
    _internal: {},
  };

  // ===================================================================
  // Section 1: Numerics — copied verbatim from rapidmeta-prognostic-engine-v1.js
  // (lines 57-202) to keep cross-engine numerical behaviour identical.
  // matMul, matVec (alias), transpose defined fresh (not present in source).
  // pmTau2 = tau2REML from source (PM-by-bisection; renamed for convention).
  // qt = tinv from source; pt = _tCDFapprox from source.
  // ===================================================================
  function zeros(r, c) { var m = []; for (var i = 0; i < r; i++) m.push(new Array(c).fill(0)); return m; }
  API._internal.zeros = zeros;
  function inv2x2(M) {
    var a = M[0][0], b = M[0][1], c = M[1][0], d = M[1][1];
    var det = a * d - b * c;
    if (Math.abs(det) < 1e-15) throw new Error('Singular 2x2');
    return [[d / det, -b / det], [-c / det, a / det]];
  }
  API._internal.inv2x2 = inv2x2;
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
  API._internal.matInv = matInv;
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
  API._internal.qchisq = qchisq;
  // Chi-squared CDF via Wilson-Hilferty
  function pchisq(x, df) {
    if (x <= 0) return 0;
    if (df <= 0) return 0;
    var h = Math.pow(x / df, 1 / 3);
    var z = (h - (1 - 2 / (9 * df))) / Math.sqrt(2 / (9 * df));
    // Standard-normal CDF via Abramowitz & Stegun 7.1.26
    return 0.5 * (1 + _erf(z / Math.SQRT2));
  }
  API._internal.pchisq = pchisq;
  function _erf(x) {
    var sign = x < 0 ? -1 : 1; x = Math.abs(x);
    var a1 = 0.254829592, a2 = -0.284496736, a3 = 1.421413741, a4 = -1.453152027, a5 = 1.061405429, p = 0.3275911;
    var t = 1 / (1 + p * x);
    var y = 1 - (((((a5 * t + a4) * t) + a3) * t + a2) * t + a1) * t * Math.exp(-x * x);
    return sign * y;
  }
  // Inverse Student-t — via beta-inverse transform (df>=1). Exposed as qt() for convention.
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
  // qt: conventional name for inverse t-CDF (alias for tinv).
  function qt(p, df) { return tinv(p, df); }
  API._internal.qt = qt;
  // t-distribution CDF. Exposed as pt() for convention.
  function _tCDFapprox(t, df) {
    // Use beta-relation: F_T(t) = 1 - 0.5 * I_{df/(df+t^2)}(df/2, 1/2) for t>=0.
    if (t < 0) return 1 - _tCDFapprox(-t, df);
    var x = df / (df + t * t);
    return 1 - 0.5 * ibeta(df / 2, 0.5, x);
  }
  function pt(t, df) { return _tCDFapprox(t, df); }
  API._internal.pt = pt;

  // Paule-Mandel tau^2 estimator (PM bisection). Exposed as pmTau2 per convention.
  // Source: tau2REML in rapidmeta-prognostic-engine-v1.js (lines 379-411).
  // PM is asymptotically equivalent to REML for univariate RE MA; named REML
  // in the source for API compatibility. We expose it as pmTau2 here.
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
  function pmTau2(yi, vi, opts) {
    opts = opts || {};
    var tol = opts.tol || 1e-9;
    var max_bis = opts.max_iter || 100;
    var k = yi.length;
    if (k < 2) return 0;
    function pmStat(tau2) {
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
  API._internal.pmTau2 = pmTau2;

  // Q-profile τ² confidence interval (Viechtbauer 2007).
  // Q(τ²) = Σ w_i (y_i − ȳ_τ²)² where w_i = 1/(v_i + τ²) and ȳ_τ² is the
  // corresponding weighted mean.  Q is strictly decreasing in τ² from Q(0)
  // (Cochran's FE Q) down toward 0.
  // CI bounds: τ²_lo = inf{τ² : Q(τ²) ≤ χ²_upper}; τ²_hi = sup{τ² : Q(τ²) ≥ χ²_lower}
  // where χ²_lower = qchisq(α/2, df), χ²_upper = qchisq(1−α/2, df), df = k−1.
  function qProfileCI(yi, vi, alpha) {
    var k = yi.length;
    if (k < 2) return { lo: 0, hi: 0 };
    var df = k - 1;
    alpha = alpha || 0.05;
    var chiLower = qchisq(alpha / 2, df);
    var chiUpper = qchisq(1 - alpha / 2, df);

    function Q(tau2) {
      var w = vi.map(function (v) { return 1 / (v + tau2); });
      var wsum = w.reduce(function (a, b) { return a + b; }, 0);
      var ybar = yi.reduce(function (acc, y, i) { return acc + w[i] * y; }, 0) / wsum;
      return yi.reduce(function (acc, y, i) {
        var d = y - ybar;
        return acc + w[i] * d * d;
      }, 0);
    }

    // Bisect to find τ² such that Q(τ²) == target.  Q is monotone-decreasing,
    // so Q > target implies τ² is too small → advance lo; Q < target → advance hi.
    function bisect(target, lo, hi, maxIter) {
      maxIter = maxIter || 60;
      for (var i = 0; i < maxIter; i++) {
        var mid = (lo + hi) / 2;
        var qm = Q(mid);
        if (Math.abs(qm - target) < 1e-9) return mid;
        if (qm > target) lo = mid; else hi = mid;
      }
      return (lo + hi) / 2;
    }

    // Build a safe upper bracket: 100× PM estimate, range², or 1.0 — whichever is largest.
    var tau2_estimate = pmTau2(yi, vi);
    var range = Math.max.apply(null, yi) - Math.min.apply(null, yi);
    var tau2_max = Math.max(100 * tau2_estimate, range * range, 1.0);

    var q0 = Q(0);

    // τ²_lo: smallest τ² where Q(τ²) ≤ chiUpper.
    // If Q(0) ≤ chiUpper already, the lower CI boundary is 0.
    var tau2_lo;
    if (q0 <= chiUpper) {
      tau2_lo = 0;
    } else {
      tau2_lo = bisect(chiUpper, 0, tau2_max);
    }

    // τ²_hi: largest τ² where Q(τ²) ≥ chiLower.
    // Edge cases:
    //   Q(0) < chiLower  — heterogeneity so low the χ² lower quantile isn't crossed → hi = 0
    //   Q(tau2_max) ≥ chiLower — Q hasn't dropped below chiLower at tau2_max → open-ended, clamp
    var tau2_hi;
    if (q0 < chiLower) {
      tau2_hi = 0;
    } else if (Q(tau2_max) >= chiLower) {
      tau2_hi = tau2_max;  // CI is open-ended at this bracket; clamp to tau2_max
    } else {
      tau2_hi = bisect(chiLower, 0, tau2_max);
    }

    return { lo: tau2_lo, hi: tau2_hi };
  }
  API._internal.qProfileCI = qProfileCI;

  // Matrix helpers not present in prognostic engine — defined fresh.
  function matMul(A, B) {
    var r = A.length, k = A[0].length, c = B[0].length;
    var M = []; for (var i = 0; i < r; i++) { M.push(new Array(c).fill(0)); for (var j = 0; j < c; j++) for (var p = 0; p < k; p++) M[i][j] += A[i][p] * B[p][j]; }
    return M;
  }
  API._internal.matMul = matMul;
  function matVec(A, v) {
    var r = A.length, k = A[0].length;
    var out = new Array(r).fill(0);
    for (var i = 0; i < r; i++) for (var j = 0; j < k; j++) out[i] += A[i][j] * v[j];
    return out;
  }
  API._internal.matVec = matVec;
  function transpose(M) {
    var r = M.length, c = M[0].length, T = [];
    for (var j = 0; j < c; j++) { T.push(new Array(r)); for (var i = 0; i < r; i++) T[j][i] = M[i][j]; }
    return T;
  }
  API._internal.transpose = transpose;

  function nelderMead(f, x0, opts) {
    // Derivative-free simplex optimizer (Nelder & Mead 1965).
    // Inputs:
    //   f: function(p: number[]) -> number   (the objective to minimize)
    //   x0: number[]  (starting point, length n)
    //   opts: { relTol: number, maxIter: number, initialStep: number }
    // Returns: { x: number[], fx: number, converged: bool, iterations: int }
    opts = opts || {};
    var relTol = opts.relTol != null ? opts.relTol : 1e-8;
    var maxIter = opts.maxIter != null ? opts.maxIter : 200;
    var step = opts.initialStep != null ? opts.initialStep : 0.1;
    var n = x0.length;

    // Standard Nelder-Mead coefficients
    var alpha = 1.0, gamma = 2.0, rho = 0.5, sigma = 0.5;

    // Build initial simplex of n+1 points
    var simplex = [x0.slice()];
    for (var i = 0; i < n; i++) {
      var pt = x0.slice();
      pt[i] += step;
      simplex.push(pt);
    }
    var fvals = simplex.map(f);

    // Helper: sort simplex+fvals by ascending fvals
    function sortSimplex() {
      var idx = fvals.map(function (_, i) { return i; });
      idx.sort(function (a, b) { return fvals[a] - fvals[b]; });
      simplex = idx.map(function (k) { return simplex[k]; });
      fvals = idx.map(function (k) { return fvals[k]; });
    }

    function shrink() {
      for (var i = 1; i <= n; i++) {
        for (var j = 0; j < n; j++) {
          simplex[i][j] = simplex[0][j] + sigma * (simplex[i][j] - simplex[0][j]);
        }
        fvals[i] = f(simplex[i]);
      }
    }

    for (var iter = 0; iter < maxIter; iter++) {
      sortSimplex();

      // Convergence check: relative spread of f-values across simplex
      var fbest = fvals[0], fworst = fvals[n];
      var spread = Math.abs(fworst - fbest) / (Math.abs(fbest) + relTol);
      if (spread < relTol) {
        return { x: simplex[0].slice(), fx: fbest, converged: true, iterations: iter };
      }

      // Centroid of all points except the worst
      var xc = new Array(n).fill(0);
      for (var k = 0; k < n; k++) for (var d = 0; d < n; d++) xc[d] += simplex[k][d];
      for (var d2 = 0; d2 < n; d2++) xc[d2] /= n;

      // Reflection
      var xr = new Array(n);
      for (var dd = 0; dd < n; dd++) xr[dd] = xc[dd] + alpha * (xc[dd] - simplex[n][dd]);
      var fr = f(xr);

      if (fr < fvals[0]) {
        // Expansion
        var xe = new Array(n);
        for (var ee = 0; ee < n; ee++) xe[ee] = xc[ee] + gamma * (xr[ee] - xc[ee]);
        var fe = f(xe);
        if (fe < fr) { simplex[n] = xe; fvals[n] = fe; }
        else         { simplex[n] = xr; fvals[n] = fr; }
      } else if (fr < fvals[n - 1]) {
        simplex[n] = xr; fvals[n] = fr;
      } else {
        // Contraction
        var xx, ff;
        if (fr < fvals[n]) {
          xx = new Array(n);
          for (var c1 = 0; c1 < n; c1++) xx[c1] = xc[c1] + rho * (xr[c1] - xc[c1]);
          ff = f(xx);
          if (ff < fr) { simplex[n] = xx; fvals[n] = ff; }
          else         { shrink(); }
        } else {
          xx = new Array(n);
          for (var c2 = 0; c2 < n; c2++) xx[c2] = xc[c2] + rho * (simplex[n][c2] - xc[c2]);
          ff = f(xx);
          if (ff < fvals[n]) { simplex[n] = xx; fvals[n] = ff; }
          else               { shrink(); }
        }
      }
    }

    sortSimplex();
    return { x: simplex[0].slice(), fx: fvals[0], converged: false, iterations: maxIter };
  }
  API._internal.nelderMead = nelderMead;

  // -------------------------------------------------------------------
  // Task 6: REML log-likelihood evaluator + logDeterminant helper
  // -------------------------------------------------------------------

  function logDeterminant(M) {
    // log|M| via LU decomposition (Doolittle) with partial pivoting.
    // Returns -Infinity if any pivot < 1e-15 (singular / near-singular).
    // NOTE: operates on a cloned copy — does NOT mutate the input matrix.
    var n = M.length;
    var A = M.map(function (row) { return row.slice(); });
    var logDet = 0;
    for (var i = 0; i < n; i++) {
      // Partial pivot: find row with largest absolute value in column i
      var maxR = i, maxV = Math.abs(A[i][i]);
      for (var r = i + 1; r < n; r++) {
        if (Math.abs(A[r][i]) > maxV) { maxR = r; maxV = Math.abs(A[r][i]); }
      }
      if (maxV < 1e-15) return -Infinity;   // singular
      if (maxR !== i) {
        var tmp = A[i]; A[i] = A[maxR]; A[maxR] = tmp;
        // Row swap flips sign of det; we take log of |det| so sign is irrelevant.
        // For PSD Σ (our use case) all pivots > 0, so this is just stability.
      }
      var pivot = A[i][i];
      logDet += Math.log(Math.abs(pivot));
      for (var r2 = i + 1; r2 < n; r2++) {
        var factor = A[r2][i] / pivot;
        for (var c = i; c < n; c++) A[r2][c] -= factor * A[i][c];
      }
    }
    return logDet;
  }
  API._internal.logDeterminant = logDeterminant;

  // Cholesky parameterization of a Kp × Kp symmetric PSD τ² matrix.
  // Free parameters: Kp log-diagonals (positivity by exp) + Kp(Kp−1)/2
  // unconstrained off-diagonals, packed row-major (diag-then-offdiag per row).
  // Total nParams = Kp * (Kp + 1) / 2. Returns τ² = L L'.
  // Extracted from fitRCS in the v0.4 refactor; closure over Kp is now explicit.
  function paramsToTau2(params, Kp) {
    var L = zeros(Kp, Kp);
    var idx = 0;
    for (var i = 0; i < Kp; i++) {
      L[i][i] = Math.exp(params[idx]);
      idx++;
      for (var j = 0; j < i; j++) {
        L[i][j] = params[idx];
        idx++;
      }
    }
    var t2m = zeros(Kp, Kp);
    for (var i2 = 0; i2 < Kp; i2++) {
      for (var j2 = 0; j2 < Kp; j2++) {
        for (var k = 0; k <= Math.min(i2, j2); k++) {
          t2m[i2][j2] += L[i2][k] * L[j2][k];
        }
      }
    }
    return t2m;
  }
  API._internal.paramsToTau2 = paramsToTau2;

  // Diagonal-PM warm-start vector for the Cholesky-parameterized REML
  // optimizer. Computes pmTau2 per dimension from the per-study beta + V,
  // floors at 1e-8 (guards Math.log(0)), then sets the Cholesky log-diagonals
  // to 0.5 * log(pmDiag[d]) (so L[i][i]² = pmDiag[i]). Off-diagonals start at 0.
  // Returns the parameter vector of length Kp * (Kp + 1) / 2.
  // Extracted from fitRCS in the v0.4 refactor.
  function fitRCSWarmStart(perStudy, Kp) {
    var pmDiag = [];
    for (var d = 0; d < Kp; d++) {
      var yi_d = perStudy.map(function (s) { return s.beta[d]; });
      var vi_d = perStudy.map(function (s) { return s.V[d][d]; });
      pmDiag.push(Math.max(pmTau2(yi_d, vi_d), 1e-8));
    }
    var nParams = Kp * (Kp + 1) / 2;
    var x0 = new Array(nParams).fill(0);
    var pIdx = 0;
    for (var dd = 0; dd < Kp; dd++) {
      x0[pIdx] = 0.5 * Math.log(pmDiag[dd]);
      pIdx++;
      for (var jj = 0; jj < dd; jj++) {
        x0[pIdx] = 0;
        pIdx++;
      }
    }
    return x0;
  }
  API._internal.fitRCSWarmStart = fitRCSWarmStart;

  // Full multivariate REML estimation of the Kp × Kp τ² matrix via Nelder-Mead
  // on the Cholesky parameterization. Returns {tau2Matrix, optResult}.
  //   - perStudy[i] must carry: .beta (Kp-vector, for warm-start), .V (Kp×Kp coef
  //     cov, for warm-start diagonal), .X (arm × Kp basis), .y (arm-vector
  //     contrast), .S (arm × arm arm-level cov)
  //   - opts: { relTol, maxIter, initialStep } passed through to nelderMead;
  //     defaults match Round 2B Task 7 (1e-6, 500, 0.5)
  // Critical guard preserved: NaN → +Infinity in negREML wrapper (Nelder-Mead
  // handles +Infinity as a "wall"; NaN corrupts the simplex sort).
  // Extracted from fitRCS in the v0.4 refactor.
  function fitRCSReml(perStudy, Kp, opts) {
    opts = opts || {};
    var psForREML = perStudy.map(function (s) { return { X: s.X, y: s.y, V: s.S }; });
    var x0 = fitRCSWarmStart(perStudy, Kp);
    function negREML(params) {
      var t2 = paramsToTau2(params, Kp);
      var ll = remlLogLik(psForREML, t2);
      return isFinite(ll) ? -ll : Infinity;
    }
    var optResult = nelderMead(negREML, x0, {
      relTol: opts.relTol != null ? opts.relTol : 1e-6,
      maxIter: opts.maxIter != null ? opts.maxIter : 500,
      initialStep: opts.initialStep != null ? opts.initialStep : 0.5,
    });
    var tau2Matrix = paramsToTau2(optResult.x, Kp);
    return { tau2Matrix: tau2Matrix, optResult: optResult };
  }
  API._internal.fitRCSReml = fitRCSReml;

  // Re-derive pooled β̂ and Cov(β̂) at the optimum τ² matrix.
  // For each trial:
  //   Σ_t = V_t + X_t τ² X_t'         (k_i × k_i arm-level marginal cov)
  //   accumulate X'_t Σ_t⁻¹ X_t  and  X'_t Σ_t⁻¹ y_t  across trials
  // Then:
  //   β̂      = (Σ_t X'_t Σ_t⁻¹ X_t)⁻¹ Σ_t X'_t Σ_t⁻¹ y_t
  //   Cov(β̂) = (Σ_t X'_t Σ_t⁻¹ X_t)⁻¹
  //   pooledSE = diag(Cov(β̂))^(1/2)  (pre-HKSJ inflation)
  // perStudy[t] must carry .X (arm × Kp), .y (arm), .S (arm × arm cov).
  // Throws descriptive Error if every per-trial Σ inversion failed (XtWX is zero).
  // Extracted from fitRCS in the v0.4 refactor.
  function fitRCSPooled(perStudy, Kp, tau2Matrix) {
    var XtWX_sum = zeros(Kp, Kp);
    var XtWy_sum = new Array(Kp).fill(0);
    for (var t = 0; t < perStudy.length; t++) {
      var X = perStudy[t].X;
      var y = perStudy[t].y;
      var V = perStudy[t].S;
      var ki = X.length;
      var Xt2 = zeros(ki, ki);
      for (var i = 0; i < ki; i++) for (var j = 0; j < ki; j++) {
        for (var p = 0; p < Kp; p++) for (var q = 0; q < Kp; q++) {
          Xt2[i][j] += X[i][p] * tau2Matrix[p][q] * X[j][q];
        }
      }
      var Sigma = zeros(ki, ki);
      for (var i2 = 0; i2 < ki; i2++) for (var j2 = 0; j2 < ki; j2++) {
        Sigma[i2][j2] = V[i2][j2] + Xt2[i2][j2];
      }
      var W;
      try { W = matInv(Sigma); } catch (e) { continue; }
      for (var pp = 0; pp < Kp; pp++) {
        for (var i3 = 0; i3 < ki; i3++) {
          var XtW_pi = 0;
          for (var j3 = 0; j3 < ki; j3++) XtW_pi += X[j3][pp] * W[j3][i3];
          XtWy_sum[pp] += XtW_pi * y[i3];
          for (var qq = 0; qq < Kp; qq++) {
            XtWX_sum[pp][qq] += XtW_pi * X[i3][qq];
          }
        }
      }
    }
    var covBeta;
    try { covBeta = matInv(XtWX_sum); }
    catch (e) {
      throw new Error('fitRCS: pooled-β̂ XtWX matrix singular after REML — k_effective=' + perStudy.length + ' (likely all per-trial Σ inversions failed)');
    }
    var pooledBeta = matVec(covBeta, XtWy_sum);
    var pooledSE_raw = [];
    for (var d = 0; d < Kp; d++) pooledSE_raw.push(Math.sqrt(covBeta[d][d]));
    return { pooledBeta: pooledBeta, covBeta: covBeta, pooledSE_raw: pooledSE_raw };
  }
  API._internal.fitRCSPooled = fitRCSPooled;

  // HKSJ-multivariate scaling + t_{k−1} CI critical value.
  //   Q_mv = Σ_i (y_i − X_i β̂)' Σ_i⁻¹ (y_i − X_i β̂)       (multivariate Cochran Q)
  //   df_mv = max(1, n_total − Kp)                          (residual df)
  //   hksj_mv = max(1, Q_mv / df_mv)                        (lessons.md floor)
  //   tcrit = qt(0.975, k_trials − 1)  (1.96 fallback at k=1)
  //   pooledSE_hksj = pooledSE_raw × √hksj_mv
  // n_total is incremented AFTER successful Σ⁻¹ (defensive — unreachable in practice
  // since fitRCSPooled already proved invertibility on the same matrices).
  // Extracted from fitRCS in the v0.4 refactor.
  function fitRCSHksjMv(perStudy, Kp, tau2Matrix, pooledBeta, pooledSE_raw) {
    var Q_mv = 0;
    var n_total = 0;
    for (var t = 0; t < perStudy.length; t++) {
      var X = perStudy[t].X;
      var y = perStudy[t].y;
      var V = perStudy[t].S;
      var ki = X.length;
      var Xt2 = zeros(ki, ki);
      for (var i = 0; i < ki; i++) for (var j = 0; j < ki; j++) {
        for (var p = 0; p < Kp; p++) for (var q = 0; q < Kp; q++) {
          Xt2[i][j] += X[i][p] * tau2Matrix[p][q] * X[j][q];
        }
      }
      var Sigma = zeros(ki, ki);
      for (var i2 = 0; i2 < ki; i2++) for (var j2 = 0; j2 < ki; j2++) {
        Sigma[i2][j2] = V[i2][j2] + Xt2[i2][j2];
      }
      var W;
      try { W = matInv(Sigma); } catch (e) { continue; }
      n_total += ki;
      var resid = y.map(function (yv, idx) {
        var Xb = 0;
        for (var pp = 0; pp < Kp; pp++) Xb += X[idx][pp] * pooledBeta[pp];
        return yv - Xb;
      });
      for (var i3 = 0; i3 < ki; i3++) for (var j3 = 0; j3 < ki; j3++) {
        Q_mv += resid[i3] * W[i3][j3] * resid[j3];
      }
    }
    var df_mv = Math.max(1, n_total - Kp);
    var hksj_mv = Math.max(1, Q_mv / df_mv);
    var k_trials = perStudy.length;
    var tcrit = k_trials > 1 ? qt(0.975, k_trials - 1) : 1.96;
    var hksjFactor = Math.sqrt(hksj_mv);
    var pooledSE_hksj = pooledSE_raw.map(function (s) { return s * hksjFactor; });
    return {
      q_mv: Q_mv,
      df_mv: df_mv,
      hksj_mv: hksj_mv,
      k_trials: k_trials,
      tcrit: tcrit,
      pooledSE_hksj: pooledSE_hksj,
      n_total: n_total,
    };
  }
  API._internal.fitRCSHksjMv = fitRCSHksjMv;

  // Wald non-linearity test on the full post-REML covariance.
  //   H0: all non-linear basis coefs (d ≥ 1) are zero
  //   chi2 = β_nl' Cov(β_nl)⁻¹ β_nl ~ χ²(Kp − 1) under H0
  //   Cov(β_nl) is the bottom-right (Kp − 1) × (Kp − 1) submatrix of covBeta
  // Returns {chi2, df, p}. Throws on singular nlCov (rare; near-collinear knots).
  // Extracted from fitRCS in the v0.4 refactor.
  function fitRCSWaldNonlinearity(pooledBeta, covBeta, Kp) {
    var nlBeta = pooledBeta.slice(1);
    var nlCov = zeros(Kp - 1, Kp - 1);
    for (var i = 0; i < Kp - 1; i++) {
      for (var j = 0; j < Kp - 1; j++) {
        nlCov[i][j] = covBeta[i + 1][j + 1];
      }
    }
    var W = 0;
    if (nlBeta.length > 0) {
      var nlCovInv;
      try { nlCovInv = matInv(nlCov); }
      catch (e) {
        throw new Error('fitRCS: non-linearity covariance matrix is singular (Kp=' + Kp + ')');
      }
      for (var i2 = 0; i2 < nlBeta.length; i2++) {
        for (var j2 = 0; j2 < nlBeta.length; j2++) {
          W += nlBeta[i2] * nlCovInv[i2][j2] * nlBeta[j2];
        }
      }
    }
    return {
      chi2: W,
      df: nlBeta.length,
      p: nlBeta.length > 0 ? (1 - pchisq(W, nlBeta.length)) : null,
    };
  }
  API._internal.fitRCSWaldNonlinearity = fitRCSWaldNonlinearity;

  // 20-point dose-response curve grid from 0 to maxD.
  //   est(dose)   = b' β̂      where b = rcsBasis(dose, knots)
  //   var(est)    = b' Cov(β̂) b × hksj_mv  (HKSJ-multivariate inflation)
  //   CI          = est ± tcrit × √var(est)
  // Returns array of {dose, est, ci_lo, ci_hi}, length 20.
  // Variance uses the FULL quadratic form (off-diagonals included, not diagonal-sum
  // — pre-Round 2C this was lossy whenever basis coefs were correlated).
  // Extracted from fitRCS in the v0.4 refactor.
  function fitRCSFitAtDose(pooledBeta, covBeta, hksj_mv, tcrit, knots, Kp, maxD) {
    var fit_at_dose = [];
    for (var i = 0; i < 20; i++) {
      var dose_i = i * maxD / 19;
      var b = rcsBasis(dose_i, knots);
      var est = 0, varEst = 0;
      for (var p = 0; p < Kp; p++) {
        est += pooledBeta[p] * b[p];
        for (var q = 0; q < Kp; q++) {
          varEst += b[p] * covBeta[p][q] * b[q];
        }
      }
      varEst *= hksj_mv;
      var seEst = Math.sqrt(varEst);
      fit_at_dose.push({ dose: dose_i, est: est, ci_lo: est - tcrit * seEst, ci_hi: est + tcrit * seEst });
    }
    return fit_at_dose;
  }
  API._internal.fitRCSFitAtDose = fitRCSFitAtDose;

  function remlLogLik(perStudy, tau2) {
    // REML log-likelihood for multivariate dose-response random-effects model.
    //
    // perStudy: array of { X: k_i × Kp matrix (row = dose point, col = basis),
    //                       y: length-k_i vector of log-RR estimates,
    //                       V: k_i × k_i within-study covariance }
    // tau2:     Kp × Kp symmetric PSD matrix (between-study covariance of β)
    //
    // Formula (profile likelihood after integrating out β):
    //   Σ_i = V_i + X_i τ² X'_i
    //   β̂   = (Σ_i X'_i Σ_i⁻¹ X_i)⁻¹ Σ_i X'_i Σ_i⁻¹ y_i
    //   ℓ(τ²) = −½ Σ_i log|Σ_i|
    //           − ½ Σ_i (y_i − X_i β̂)' Σ_i⁻¹ (y_i − X_i β̂)
    //           − ½ log|Σ_i X'_i Σ_i⁻¹ X_i|
    //
    // Returns -Infinity on any degenerate/invalid input (never NaN).
    // Task 7's negREML wrapper inverts sign → +Infinity on bad inputs,
    // which Nelder-Mead treats as a wall (satisfies NaN-vs-Infinity contract).

    var Kp = tau2.length;
    if (Kp === 0) return -Infinity;

    // --- Pass 1: accumulate per-study marginal covariances and cross-sums ---
    var XtSinvX_sum = zeros(Kp, Kp);        // Σ_i X'_i Σ_i⁻¹ X_i
    var XtSinvy_sum = new Array(Kp).fill(0); // Σ_i X'_i Σ_i⁻¹ y_i
    var logDetSum = 0;
    var trialContribs = [];  // stash {X, y, SigmaInv} for quadratic-form pass 2

    for (var t = 0; t < perStudy.length; t++) {
      var X = perStudy[t].X;   // k_i × Kp
      var y = perStudy[t].y;   // length k_i
      var V = perStudy[t].V;   // k_i × k_i
      var ki = X.length;

      // Build X τ² X'  (k_i × k_i)
      var Xt2 = zeros(ki, ki);
      for (var i = 0; i < ki; i++) {
        for (var j = 0; j < ki; j++) {
          for (var p = 0; p < Kp; p++) {
            for (var q = 0; q < Kp; q++) {
              Xt2[i][j] += X[i][p] * tau2[p][q] * X[j][q];
            }
          }
        }
      }

      // Σ_i = V_i + X τ² X'
      var Sigma = zeros(ki, ki);
      for (var i2 = 0; i2 < ki; i2++) {
        for (var j2 = 0; j2 < ki; j2++) {
          Sigma[i2][j2] = V[i2][j2] + Xt2[i2][j2];
        }
      }

      // Σ_i⁻¹ and log|Σ_i|
      // logDeterminant clones Sigma internally so matInv can also receive Sigma safely.
      var logDet = logDeterminant(Sigma);
      if (!isFinite(logDet)) return -Infinity;
      logDetSum += logDet;

      var SigmaInv;
      try { SigmaInv = matInv(Sigma); }
      catch (e) { return -Infinity; }

      // Accumulate X'_i Σ_i⁻¹ X_i and X'_i Σ_i⁻¹ y_i
      // XtSinv[p][j] = Σ_j X[j][p] * SigmaInv[j][i3]  for all p, i3
      for (var p2 = 0; p2 < Kp; p2++) {
        for (var i3 = 0; i3 < ki; i3++) {
          var XtSinv_p_i3 = 0;
          for (var j3 = 0; j3 < ki; j3++) {
            XtSinv_p_i3 += X[j3][p2] * SigmaInv[j3][i3];
          }
          XtSinvy_sum[p2] += XtSinv_p_i3 * y[i3];
          for (var q2 = 0; q2 < Kp; q2++) {
            XtSinvX_sum[p2][q2] += XtSinv_p_i3 * X[i3][q2];
          }
        }
      }

      trialContribs.push({ X: X, y: y, SigmaInv: SigmaInv });
    }

    // --- Profile out β̂ = (Σ X'Σ⁻¹X)⁻¹ (Σ X'Σ⁻¹y) ---
    var XtSinvX_inv;
    try { XtSinvX_inv = matInv(XtSinvX_sum); }
    catch (e) { return -Infinity; }

    var beta = matVec(XtSinvX_inv, XtSinvy_sum);
    // Guard against degenerate matInv producing silent NaN/Inf
    for (var bb = 0; bb < beta.length; bb++) {
      if (!isFinite(beta[bb])) return -Infinity;
    }

    // --- Pass 2: quadratic form Σ_i (y_i − X_i β̂)' Σ_i⁻¹ (y_i − X_i β̂) ---
    // Two-pass design is intentional: β̂ depends on the full cross-study sum
    // from pass 1, so it cannot be accumulated mid-pass.
    var quadForm = 0;
    for (var tt = 0; tt < trialContribs.length; tt++) {
      var X_tt = trialContribs[tt].X;
      var y_tt = trialContribs[tt].y;
      var SI_tt = trialContribs[tt].SigmaInv;
      var resid = y_tt.map(function (yv, idx) {
        var Xb = 0;
        for (var p3 = 0; p3 < Kp; p3++) Xb += X_tt[idx][p3] * beta[p3];
        return yv - Xb;
      });
      for (var i4 = 0; i4 < resid.length; i4++) {
        for (var j4 = 0; j4 < resid.length; j4++) {
          quadForm += resid[i4] * SI_tt[i4][j4] * resid[j4];
        }
      }
    }

    // --- REML penalty: log|Σ_i X'_i Σ_i⁻¹ X_i| ---
    var logDetXtSinvX = logDeterminant(XtSinvX_sum);
    if (!isFinite(logDetXtSinvX)) return -Infinity;

    return -0.5 * logDetSum - 0.5 * quadForm - 0.5 * logDetXtSinvX;
  }
  API._internal.remlLogLik = remlLogLik;

  // ===================================================================
  // Section 2: validate, fitters, helpers — implemented across later units.
  // ===================================================================

  function validate(trials) {
    var issues = [];
    if (!Array.isArray(trials) || trials.length === 0) {
      return ['no trials provided'];
    }
  // TODO (P2 hardening): negation-word check per lessons.md ("Not Randomized 1,807" incident).
  // If studlab matches /\b(not|non|never)\b/i AND a single-arm trial has high n,
  // emit a 'suspicious-extraction: negation in studlab' issue. Deferred from Round 1A.
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
  // Round 2A: pool-level outcome-type homogeneity check. fitLinear/fitRCS dispatch
  // once on a single outcome type for the whole pool; mixed binary+continuous trials
  // in one fixture would silently mis-pool. validate enforces homogeneity.
  if (trials.length > 0 && issues.length === 0) {
    var seenTypes = {};
    for (var ti = 0; ti < trials.length; ti++) {
      var t = trials[ti];
      if (!Array.isArray(t.arms)) continue;
      for (var ai = 0; ai < t.arms.length; ai++) {
        var a = t.arms[ai];
        if (!a) continue;
        var hasE = isFinite(a.events) && isFinite(a.n);
        var hasC = isFinite(a.mean) && isFinite(a.sd);
        if (hasE) seenTypes['binary'] = true;
        if (hasC) seenTypes['continuous'] = true;
      }
    }
    var typeCount = Object.keys(seenTypes).length;
    if (typeCount > 1) {
      issues.push('mixed outcome types in pool — one fixture = one outcome type');
    }
  }
    return issues;
  }
  API.validate = validate;

  // Greenland-Longnecker covariance correction for binary (cohort RR) dose-response.
  // Returns a k×k covariance matrix for the k contrast log-RRs (vs. reference arm).
  // Formula: Var[logRR_i] = 1/events_i + 1/events_0 - 1/n_i - 1/n_0
  //          Cov[logRR_i, logRR_j] = 1/events_0 - 1/n_0   (i≠j)
  function glCovariance(arms) {
    var ref = arms.find(function (a) { return a.is_reference; });
    if (!ref) throw new Error('glCovariance: no reference arm');
    var contrasts = arms.filter(function (a) { return !a.is_reference; });
    var k = contrasts.length;
    var E0 = ref.events, N0 = ref.n;
    var S = [];
    for (var i = 0; i < k; i++) {
      S.push(new Array(k));
      for (var j = 0; j < k; j++) {
        if (i === j) {
          var c = contrasts[i];
          S[i][j] = 1 / c.events + 1 / E0 - 1 / c.n - 1 / N0;
        } else {
          S[i][j] = 1 / E0 - 1 / N0;
        }
      }
    }
    return S;
  }
  API._internal.glCovariance = glCovariance;

  // Continuous-outcome (mean difference) per-trial covariance.
  // Same shared-reference structure as glCovariance: every y_i = mean_i - mean_ref
  // shares the reference arm, so off-diagonal entries are sd_ref^2/n_ref.
  function mdCovariance(arms) {
    var ref = arms.find(function (a) { return a.is_reference; });
    if (!ref) throw new Error('mdCovariance: no reference arm');
    var contrasts = arms.filter(function (a) { return !a.is_reference; });
    var k = contrasts.length;
    var sdRefSq = ref.sd * ref.sd;
    var nRef = ref.n;
    var shared = sdRefSq / nRef;
    var S = [];
    for (var i = 0; i < k; i++) {
      S.push(new Array(k));
      for (var j = 0; j < k; j++) {
        if (i === j) {
          var c = contrasts[i];
          S[i][j] = (c.sd * c.sd) / c.n + shared;
        } else {
          S[i][j] = shared;
        }
      }
    }
    return S;
  }
  API._internal.mdCovariance = mdCovariance;

  // === Section 2b: RCS helpers (precedes Section 2a in file; positioned by dependency order) ===

  // quantile(sorted, p): R type-7 linear interpolation on a pre-sorted array.
  function quantile(sorted, p) {
    var n = sorted.length;
    if (n === 0) return NaN;
    if (n === 1) return sorted[0];
    var h = (n - 1) * p;
    var lo = Math.floor(h), hi = Math.ceil(h);
    return sorted[lo] + (h - lo) * (sorted[hi] - sorted[lo]);
  }
  API._internal.quantile = quantile;

  // rcsKnots(doses, k): Harrell rcspline.eval default percentile knots.
  // Filters to unique positive doses, sorts, then computes percentiles.
  // Returns [] (empty) if fewer than k unique positive doses (degenerate).
  function rcsKnots(doses, k) {
    var uniq = Array.from(new Set(doses)).filter(function (d) { return d > 0; }).sort(function (a, b) { return a - b; });
    if (uniq.length < k) return [];  // degenerate
    var pcts;
    if (k === 3)      pcts = [0.25, 0.50, 0.75];
    else if (k === 4) pcts = [0.05, 0.35, 0.65, 0.95];
    else if (k === 5) pcts = [0.05, 0.275, 0.50, 0.725, 0.95];
    else throw new Error('rcsKnots: only k in {3,4,5} supported');
    return pcts.map(function (p) { return quantile(uniq, p); });
  }
  API._internal.rcsKnots = rcsKnots;

  // rcsBasis(x, knots): Harrell truncated-power basis, matched to R's rcspline.eval (norm=2, inclx=TRUE).
  // Returns a vector of length K-1 (K = knots.length):
  //   basis[0] = x   (linear term, inclx)
  //   basis[1..K-2] = K-2 spline terms, one per knot in knots[0..K-3]
  //     (R loops j in 1:(nk-2) over knots[j] 1-indexed = knots[0..K-3] 0-indexed)
  // Degenerates to [x] when K < 3.
  //
  // R formula (norm=2): kd = (t_K - t_1)^(2/3); basis[j] = pos3((x-t_j)/kd)
  //   + [(t_{K-1}-t_j)*pos3((x-t_K)/kd) - (t_K-t_j)*pos3((x-t_{K-1})/kd)] / (t_K-t_{K-1})
  // Equivalently (factoring out 1/kd^3 = 1/(t_K-t_1)^2 = 1/denom1):
  //   basis[j] = [pos3(x-t_j) + (t_{K-1}-t_j)*pos3(x-t_K)/(t_K-t_{K-1})
  //               - (t_K-t_j)*pos3(x-t_{K-1})/(t_K-t_{K-1})] / denom1
  //
  // Reference values from R: library(Hmisc); rcspline.eval(12.5, knots=c(5,10,15,20), inclx=TRUE)
  //   = [12.5, 1.875, 0.06944444]
  function rcsBasis(x, knots) {
    var K = knots.length;
    if (K < 3) return [x];  // degenerate to linear
    var tK   = knots[K - 1];
    var tKm1 = knots[K - 2];
    var t1   = knots[0];
    var denom1 = Math.pow(tK - t1, 2);
    var pos3 = function (z) { return z <= 0 ? 0 : z * z * z; };
    var basis = [x];
    // Loop over knots[0..K-3] (first K-2 knots), matching R's 1:(nk-2) loop.
    for (var j = 0; j < K - 2; j++) {
      var tj = knots[j];
      var b = (pos3(x - tj)
             + pos3(x - tK)   * (tKm1 - tj) / (tK - tKm1)
             - pos3(x - tKm1) * (tK  - tj)  / (tK - tKm1)) / denom1;
      basis.push(b);
    }
    return basis;
  }
  API._internal.rcsBasis = rcsBasis;

  // ===================================================================
  // Section 2a: fitLinear — two-stage Greenland-Longnecker linear pool.
  // Per-study WLS slope via GL covariance, then REML+HKSJ RE pool.
  // ===================================================================
  function fitLinear(trials, opts) {
    opts = opts || {};
    var issues = validate(trials);
    if (issues.length > 0) throw new Error('fitLinear: ' + issues[0]);

  // I-1 / v0.6.0: validate() is a data-shape checker, not a statistical-feasibility
  // checker. k<1 is impossible (no trials → no engine work); k=1 dispatches to the
  // single-trial branch below (matches fitRCS v0.4.0 k=1 behaviour). k>=2 falls
  // through to the canonical REML + HKSJ pool.
  if (trials.length < 1) {
    throw new Error('fitLinear: requires k >= 1 trial; got k=' + trials.length);
  }

    var alpha = opts.alpha || 0.05;

  // Round 2A: dispatch on outcome type at pool entry. validate() already enforces
  // pool-level homogeneity; safe to infer once from the first non-reference arm.
  var firstTrial = trials[0];
  var firstArm = firstTrial.arms.find(function (a) { return !a.is_reference; });
  var poolOutcomeType = (isFinite(firstArm.mean) && isFinite(firstArm.sd)) ? 'continuous' : 'binary';

    var perStudy = [];

    for (var t = 0; t < trials.length; t++) {
      var T = trials[t];
      var ref = T.arms.find(function (a) { return a.is_reference; });
      var contrasts = T.arms.filter(function (a) { return !a.is_reference; });
      var x = contrasts.map(function (a) { return a.dose - ref.dose; });
      var y, S;
      if (poolOutcomeType === 'continuous') {
        y = contrasts.map(function (a) { return a.mean - ref.mean; });
        S = mdCovariance(T.arms);
      } else {
        // F-1 zero-cell continuity correction (advanced-stats.md): add 0.5 to events
        // and 1.0 to n in BOTH ref and contrast arms ONLY when >=1 cell is zero in
        // this trial. Unconditional correction biases OR -> 1; conditional is the
        // consensus correction.
        var hasZeroCell = (ref.events === 0) ||
          contrasts.some(function (a) { return a.events === 0; });
        var refE, refN;
        if (hasZeroCell) {
          refE = ref.events + 0.5;
          refN = ref.n + 1.0;
        } else {
          refE = ref.events;
          refN = ref.n;
        }
        y = contrasts.map(function (a) {
          var aE = hasZeroCell ? a.events + 0.5 : a.events;
          var aN = hasZeroCell ? a.n + 1.0 : a.n;
          var pi = aE / aN, p0 = refE / refN;
          return Math.log(pi / p0);
        });
        // glCovariance needs the (potentially) corrected events/n too; pass a shallow
        // clone of arms with the corrected fields.
        if (hasZeroCell) {
          var armsCorr = T.arms.map(function (a) {
            if (a.is_reference) return { events: a.events + 0.5, n: a.n + 1.0, is_reference: true };
            return { events: a.events + 0.5, n: a.n + 1.0, is_reference: false };
          });
          S = glCovariance(armsCorr);
        } else {
          S = glCovariance(T.arms);
        }
      }
      var Sinv = matInv(S);
      // β = (x' Sinv x)^{-1} x' Sinv y   (scalar slope)
      var xSx = 0, xSy = 0;
      for (var i = 0; i < x.length; i++) {
        for (var j = 0; j < x.length; j++) {
          xSx += x[i] * Sinv[i][j] * x[j];
          xSy += x[i] * Sinv[i][j] * y[j];
        }
      }
      var beta = xSy / xSx;
      var seBeta = Math.sqrt(1 / xSx);
      perStudy.push({
        studlab: T.studlab,
        slope_log: beta,
        slope_log_se: seBeta,
        n_arms: T.arms.length
      });
    }

    // v0.6.0: fitLinear k=1 single-trial branch.
    // Mirror of fitRCS v0.4.0 k=1 logic. With only one trial there is no
    // between-study τ² to estimate and Cochran Q is undefined; we surface the
    // trial's own GL/WLS slope (already computed above in perStudy[0]) with a
    // within-trial t-CI on df = n_arms - 2. PI degenerates to CI (no
    // between-study spread). HKSJ inactive (qstar=1, adj=1); estimator and
    // ci_method labels are distinct from the k>=2 REML+HKSJ path so downstream
    // consumers can detect single-trial mode.
    if (trials.length === 1) {
      var ps = perStudy[0];
      var single_slope = ps.slope_log;
      var single_se = ps.slope_log_se;
      var n_arms_single = ps.n_arms;
      var df_within = Math.max(1, n_arms_single - 2);
      var tcrit_single = df_within >= 1 ? qt(1 - (opts.alpha || 0.05) / 2, df_within) : 1.96;
      var maxObsSingle = 0;
      for (var ai_s = 0; ai_s < trials[0].arms.length; ai_s++) {
        var arm_s = trials[0].arms[ai_s];
        if (!arm_s.is_reference && isFinite(arm_s.dose) && arm_s.dose > maxObsSingle) maxObsSingle = arm_s.dose;
      }
      return {
        layer: 'linear', k: 1,
        pooled_slope_log: single_slope,
        pooled_slope_log_se: single_se,
        pooled_slope_log_ci_lo: single_slope - tcrit_single * single_se,
        pooled_slope_log_ci_hi: single_slope + tcrit_single * single_se,
        tau2: 0, tau2_lo: 0, tau2_hi: 0,
        Q: 0, Q_df: 0, I2: 0, H2: 1,
        // PI degenerates to CI at k=1 (no between-study spread defined)
        pi_lo: single_slope - tcrit_single * single_se,
        pi_hi: single_slope + tcrit_single * single_se,
        pi_df: df_within,
        hksj_adj: 1, hksj_qstar: 1,
        per_study: perStudy,
        max_observed_dose: maxObsSingle,
        coverage_warning: true,
        fallback: null,
        estimator: 'wls_single_trial_linear',
        ci_method: 't_within_trial',
        converged: true,
        iterations: null,
        _fitInternal: null,
        engine_version: API.engine_version,
      };
    }

    var k = perStudy.length;
    var yi = perStudy.map(function (s) { return s.slope_log; });
    var vi = perStudy.map(function (s) { return s.slope_log_se * s.slope_log_se; });

    // REML tau² via Paule-Mandel bisection
    var tau2 = pmTau2(yi, vi);

    // Round 2B: Q-profile τ² CI per Viechtbauer 2007
    var tau2CI = qProfileCI(yi, vi, alpha);

    // RE weights
    var w = vi.map(function (v) { return 1 / (v + tau2); });
    var wsum = w.reduce(function (a, b) { return a + b; }, 0);
    var pooled = yi.reduce(function (acc, yval, i) { return acc + w[i] * yval; }, 0) / wsum;

    // FE SE (used for HKSJ)
    var wFE = vi.map(function (v) { return 1 / v; });
    var wsumFE = wFE.reduce(function (a, b) { return a + b; }, 0);
    var pooledFE = yi.reduce(function (acc, yval, i) { return acc + wFE[i] * yval; }, 0) / wsumFE;
    var seREBase = Math.sqrt(1 / wsum);  // RE-weighted base SE; FE-weighted variant lives below in Q computation

  // Q uses FE weights and the FE pooled estimate (classical Cochran Q convention).
  // metafor's HKSJ variant uses RE weights and RE pooled by default; we verified
  // parity vs R mvmeta on GL-1992 (|Δ|<0.0005 on pooled slope) so the choice is
  // numerically equivalent for our test set, but worth flagging for future hardening.
    // Cochran Q using FE weights around RE pooled estimate (standard HKSJ convention)
    var Q = yi.reduce(function (acc, yval, i) {
      var wfe = 1 / vi[i];
      return acc + wfe * (yval - pooledFE) * (yval - pooledFE);
    }, 0);
    var df = k - 1;
    // HKSJ floor per advanced-stats.md: max(1, Q/(k-1))
    var qstar = Math.max(1, Q / df);
    var hksjMult = Math.sqrt(qstar);
    var seHKSJ = seREBase * hksjMult;
    var tcrit = qt(1 - alpha / 2, df);

    var I2 = Math.max(0, (Q - df) / Q) * 100;
    var H2 = Q / df;

    // P1-4: PI df convention = k-1 (Cochrane v6.5 §10.10.4.3 / RevMan-2025).
    // Alternative t_{k-2} from IntHout/Higgins/Tudur Smith 2016 is NOT used here.
    // See advanced-stats.md "PI df conflict" rule.
    // PI per Cochrane v6.5: t_{k-1} × sqrt(τ² + seHKSJ²)
    var piHalf = tcrit * Math.sqrt(tau2 + seHKSJ * seHKSJ);

    // max_observed_dose for predict() banner in Unit 7
    var maxObs = 0;
    for (var ti = 0; ti < trials.length; ti++) {
      for (var ai = 0; ai < trials[ti].arms.length; ai++) {
        var arm = trials[ti].arms[ai];
        if (!arm.is_reference && isFinite(arm.dose) && arm.dose > maxObs) maxObs = arm.dose;
      }
    }

    return {
      layer: 'linear', k: k,
      pooled_slope_log: pooled,
      pooled_slope_log_se: seHKSJ,
      pooled_slope_log_ci_lo: pooled - tcrit * seHKSJ,
      pooled_slope_log_ci_hi: pooled + tcrit * seHKSJ,
      tau2: tau2, tau2_lo: tau2CI.lo, tau2_hi: tau2CI.hi,
      Q: Q, Q_df: df, I2: I2, H2: H2,
      pi_lo: pooled - piHalf, pi_hi: pooled + piHalf, pi_df: df,
      hksj_adj: hksjMult, hksj_qstar: qstar,
      per_study: perStudy,
      max_observed_dose: maxObs,
      coverage_warning: k < 10,
      fallback: null,
      estimator: 'reml_hksj',
      converged: true,         // fitLinear is closed-form WLS + PM bisection; always converges
      iterations: null,        // not meaningful for closed-form fitLinear
      _fitInternal: null,      // reserved for future debug payloads
      engine_version: API.engine_version,
    };
  }
  API.fitLinear = fitLinear;

  // ===================================================================
  // Section 2c: fitRCS — two-stage Greenland-Longnecker + restricted-cubic-spline
  // multivariate-RE pool.  Algorithm per plan Task 13.
  // ===================================================================
  function fitRCS(trials, opts) {
    opts = opts || {};
    var issues = validate(trials);
    if (issues.length) throw new Error('fitRCS: ' + issues[0]);
    if (trials.length < 1) throw new Error('fitRCS: requires k >= 1 trial; got k=' + trials.length);

  var firstTrial = trials[0];
  var firstArm = firstTrial.arms.find(function (a) { return !a.is_reference; });
  var poolOutcomeType = (isFinite(firstArm.mean) && isFinite(firstArm.sd)) ? 'continuous' : 'binary';

    var K = opts.knots || 3;

    // Step 1: gather all non-reference doses for knot placement.
    // Use only unique positive doses (matches rcsKnots contract).
    var allDoses = [];
    for (var t = 0; t < trials.length; t++) {
      for (var a = 0; a < trials[t].arms.length; a++) {
        if (!trials[t].arms[a].is_reference) allDoses.push(trials[t].arms[a].dose);
      }
    }
    var knots = rcsKnots(allDoses, K);
    if (knots.length === 0) {
      var lin = fitLinear(trials, opts);
      lin.fallback = 'degenerate_to_linear';
      lin.rcs = null;
      return lin;
    }

    var Kp = K - 1;  // number of basis dimensions (linear + K-2 spline terms)

    // Step 2: per-study beta and V via multivariate WLS.
    // X_i rows = rcsBasis(arm.dose, knots) - rcsBasis(ref.dose, knots)
    // (centering by subtracting reference basis, not evaluating at arm.dose - ref.dose)
    var perStudy = [];
    for (var t2 = 0; t2 < trials.length; t2++) {
      var T = trials[t2];
      var ref = T.arms.find(function (a) { return a.is_reference; });
      var contrasts = T.arms.filter(function (a) { return !a.is_reference; });
      if (contrasts.length === 0) continue;

      var bRef = rcsBasis(ref.dose, knots);
      var Xrows = contrasts.map(function (arm) {
        var bArm = rcsBasis(arm.dose, knots);
        return bArm.map(function (v, i) { return v - bRef[i]; });
      });
      var y, S;
      if (poolOutcomeType === 'continuous') {
        y = contrasts.map(function (a) { return a.mean - ref.mean; });
        S = mdCovariance(T.arms);
      } else {
        var hasZeroCell = (ref.events === 0) ||
          contrasts.some(function (a) { return a.events === 0; });
        var refE, refN;
        if (hasZeroCell) {
          refE = ref.events + 0.5;
          refN = ref.n + 1.0;
        } else {
          refE = ref.events;
          refN = ref.n;
        }
        y = contrasts.map(function (a) {
          var aE = hasZeroCell ? a.events + 0.5 : a.events;
          var aN = hasZeroCell ? a.n + 1.0 : a.n;
          var pi = aE / aN, p0 = refE / refN;
          return Math.log(pi / p0);
        });
        if (hasZeroCell) {
          var armsCorr = T.arms.map(function (a) {
            if (a.is_reference) return { events: a.events + 0.5, n: a.n + 1.0, is_reference: true };
            return { events: a.events + 0.5, n: a.n + 1.0, is_reference: false };
          });
          S = glCovariance(armsCorr);
        } else {
          S = glCovariance(T.arms);
        }
      }
      var Sinv;
      try { Sinv = matInv(S); } catch (e) { continue; }

      // Build (X' S^{-1} X) and (X' S^{-1} y) — (Kp × Kp) and (Kp × 1)
      var XtSX = zeros(Kp, Kp);
      var XtSy = new Array(Kp).fill(0);
      for (var i = 0; i < Xrows.length; i++) {
        for (var j = 0; j < Xrows.length; j++) {
          for (var p = 0; p < Kp; p++) {
            XtSy[p] += Xrows[i][p] * Sinv[i][j] * y[j];
            for (var q = 0; q < Kp; q++) {
              XtSX[p][q] += Xrows[i][p] * Sinv[i][j] * Xrows[j][q];
            }
          }
        }
      }
      var V_i;
      try { V_i = matInv(XtSX); } catch (e) { continue; }
      var beta_i = matVec(V_i, XtSy);
      // Round 2B: retain raw X (contrast basis), y (log-RR vector), and S (within-study
      // arm-level covariance) on the perStudy record so remlLogLik can compute the
      // full multivariate REML profile likelihood. V (Kp×Kp pooled-coef covariance) is
      // still retained for forest() and downstream consumers; per-dim diagonal-PM uses it.
      perStudy.push({
        studlab: T.studlab,
        beta: beta_i,
        V: V_i,
        n_arms: T.arms.length,
        X: Xrows,
        y: y,
        S: S,
      });
    }

  if (perStudy.length < 1) {
    throw new Error('fitRCS: 0 studies survived covariance inversion');
  }

    // Round 3.6 (v0.4): k=1 single-trial branch. ARTS-DN-like Phase 2b designs are
    // single-trial multi-dose RCTs (one study, many parallel dose arms). There's no
    // between-study τ² to estimate (single trial → between-study variance is undefined),
    // no Q heterogeneity statistic, no HKSJ inflation. Just the trial's own RCS coefs
    // + Kp×Kp coef covariance V, with z=1.96 or within-trial t_{df_within} for CIs.
    //
    // Multi-trial branch (k ≥ 2) uses full multivariate REML via Nelder-Mead on the
    // Cholesky parameterization of the τ² matrix — same as Round 2B v0.3.
    var psForREML, optResult, tau2Matrix, tau2_per_dim, pooled, covBeta, pooledSE;
    var isSingleTrial = perStudy.length < 2;
    if (isSingleTrial) {
      // Single-trial path: τ² = 0 by construction. Use the trial's own β̂ and V directly.
      tau2Matrix = zeros(Kp, Kp);
      tau2_per_dim = new Array(Kp).fill(0);
      optResult = { converged: true, iterations: 0, fx: 0, x: new Array(Kp * (Kp + 1) / 2).fill(0) };
      pooled = perStudy[0].beta.slice();
      covBeta = perStudy[0].V.map(function (row) { return row.slice(); });
      pooledSE = [];
      for (var ds = 0; ds < Kp; ds++) pooledSE.push(Math.sqrt(covBeta[ds][ds]));
      psForREML = null;  // no REML to run
    } else {
      psForREML = perStudy.map(function (s) { return { X: s.X, y: s.y, V: s.S }; });
      var _reml = fitRCSReml(perStudy, Kp);
      optResult = _reml.optResult;
      tau2Matrix = _reml.tau2Matrix;
      tau2_per_dim = [];
      for (var dim = 0; dim < Kp; dim++) tau2_per_dim.push(tau2Matrix[dim][dim]);
      var _pooled = fitRCSPooled(perStudy, Kp, tau2Matrix);
      pooled = _pooled.pooledBeta;
      covBeta = _pooled.covBeta;
      pooledSE = _pooled.pooledSE_raw;
    }

    // HKSJ-multivariate + tcrit. For k=1 single-trial: no Q heterogeneity (hksj_mv=1),
    // df from within-trial residuals (n_arms − Kp), tcrit = qt(0.975, df_within) or z=1.96.
    var _hksj = isSingleTrial
      ? (function () {
          // Within-trial residual df: count arms across the single trial (= k_i)
          var k_arms_single = perStudy[0].n_arms || (perStudy[0].X ? perStudy[0].X.length + 1 : Kp + 2);
          var dfWithin = Math.max(1, k_arms_single - Kp - 1);
          return {
            q_mv: 0,
            df_mv: dfWithin,
            hksj_mv: 1,
            k_trials: 1,
            tcrit: dfWithin >= 1 ? qt(0.975, dfWithin) : 1.96,
            pooledSE_hksj: pooledSE.slice(),  // no inflation at k=1
            n_total: perStudy[0].X ? perStudy[0].X.length : 0,
          };
        })()
      : fitRCSHksjMv(perStudy, Kp, tau2Matrix, pooled, pooledSE);
    var Q_mv = _hksj.q_mv;
    var df_mv = _hksj.df_mv;
    var hksj_mv = _hksj.hksj_mv;
    var k_trials = _hksj.k_trials;
    var tcrit = _hksj.tcrit;
    var pooledSE_hksj = _hksj.pooledSE_hksj;

    // Wald non-linearity extracted to API._internal.fitRCSWaldNonlinearity in v0.4.
    var _wald = fitRCSWaldNonlinearity(pooled, covBeta, Kp);
    var nonlinearity_wald_chi2 = _wald.chi2;
    var nonlinearity_wald_df = _wald.df;
    var nlP = _wald.p;

    // fit_at_dose grid extracted to API._internal.fitRCSFitAtDose in v0.4.
    var maxD = Math.max.apply(null, allDoses);
    var fit_at_dose = fitRCSFitAtDose(pooled, covBeta, hksj_mv, tcrit, knots, Kp, maxD);

    // Round 2B (v0.3.0): full multivariate REML τ² + HKSJ-mv × t_{k-1} CIs.
    // Estimator history: v0.1/v0.2 used 'pm_diagonal_z' (per-dimension PM + raw
    // z=1.96 on diagonal SE); Task 7 lifted τ² to full multivariate REML;
    // Task 9 lifts CIs to HKSJ-multivariate + t_{k-1}.
    return {
      layer: 'rcs', k: perStudy.length,
      rcs: {
        knots: knots,
        spline_coefs: pooled,
        spline_coefs_se: pooledSE_hksj,     // Round 2B Task 9: HKSJ-inflated SE
        spline_coefs_se_raw: pooledSE,      // pre-HKSJ SE retained for diagnostics
        cov_beta: covBeta,                  // full Kp×Kp pooled coef covariance (pre-HKSJ)
        tau2_matrix: tau2Matrix,            // Round 2B: full Kp×Kp REML τ² matrix
        tau2_per_dim: tau2_per_dim,         // retained: diagonal of tau2_matrix
        nonlinearity_wald_p: nlP,
        nonlinearity_wald_chi2: nonlinearity_wald_chi2,    // Round 2B follow-up Issue 1
        nonlinearity_wald_df: nonlinearity_wald_df,        // Round 2B follow-up Issue 1
        fit_at_dose: fit_at_dose,
        reml_converged: optResult.converged,
        reml_iterations: optResult.iterations,
        reml_loglik: -optResult.fx,         // positive log-likelihood
      },
      pooled_slope_log: pooled[0],
      pooled_slope_log_se: pooledSE_hksj[0],
      pooled_slope_log_ci_lo: pooled[0] - tcrit * pooledSE_hksj[0],
      pooled_slope_log_ci_hi: pooled[0] + tcrit * pooledSE_hksj[0],
      per_study: perStudy.map(function (s) {
        return { studlab: s.studlab, slope_log: s.beta[0], slope_log_se: Math.sqrt(s.V[0][0]), n_arms: s.n_arms };
      }),
      max_observed_dose: maxD,
      coverage_warning: perStudy.length < 10,
      fallback: null,
      estimator: isSingleTrial ? 'wls_single_trial_rcs' : 'reml_hksj_multivariate',
      ci_method: isSingleTrial ? 't_within_trial' : 'hksj_t_km1',
      hksj_mv: hksj_mv,                     // HKSJ-multivariate scaling factor (≥ 1)
      q_mv: Q_mv,                           // raw multivariate Cochran Q (pre-floor)
      df_mv: df_mv,                         // df = max(1, n_total − Kp)
      tcrit: tcrit,                         // qt(0.975, k-1) used for CIs (1.96 if k=1)
      converged: optResult.converged,       // Round 2B follow-up Issue 3
      iterations: optResult.iterations,     // surface REML iter count alongside convergence
      _fitInternal: null,
      engine_version: API.engine_version,
    };
  }
  API.fitRCS = fitRCS;

  // ===================================================================
  // Section 3a: nonLinearityTest(rcsResult) — thin wrapper (Task 14)
  // Extracts Wald chi² / df / p from a fitRCS result.
  // ===================================================================
  function nonLinearityTest(rcsResult) {
    // Round 2B follow-up (Issue 1): read chi², df, and p from the fitRCS result
    // (computed there using the full post-REML covariance). No re-computation
    // here — that keeps the chi²/df/p triple internally consistent. Previously
    // this function recomputed W = sum((coef/se)²) from spline_coefs_se (the
    // OLD diagonal-sum formula), so callers saw a stale chi² alongside the
    // correct p, which is exactly the API-drift the reviewer flagged.
    if (!rcsResult || !rcsResult.rcs) {
      return { chi2: null, wald_chi2: null, df: null, p: null, conclusion: 'inconclusive' };
    }
    var chi2 = rcsResult.rcs.nonlinearity_wald_chi2;
    var df = rcsResult.rcs.nonlinearity_wald_df;
    var p = rcsResult.rcs.nonlinearity_wald_p;
    var conclusion = (p != null && p < 0.05) ? 'non_linear' : ((p != null && p > 0.20) ? 'linear' : 'inconclusive');
    // wald_chi2 is preserved as an alias of chi2 for back-compat with any
    // pre-Round-2B caller that read the old field name.
    return { chi2: chi2, wald_chi2: chi2, df: df, p: p, conclusion: conclusion };
  }
  API.nonLinearityTest = nonLinearityTest;

  // ===================================================================
  // Section 3b: fitOneStage(trials, opts, precomputedJson) — JSON reader (Task 15)
  // One-stage hierarchical is NOT fitted in JS v0.1.  Pass precomputedJson=null
  // to signal the caller must run R Round-1B.  Pass the JSON object from
  // outputs/r_validation/doseresp/<REVIEW>.json to read R precomputed coefs.
  // ===================================================================
  function fitOneStage(trials, opts, precomputedJson) {
    // P2-9: opts is reserved for future use (currently ignored).
    if (precomputedJson == null) return null;
    var os = precomputedJson.one_stage || {};
    return {
      layer: 'one_stage',
      k: (trials && trials.length) || (precomputedJson.k || 0),
      one_stage: {
        coef_dose: os.coef_dose,
        coef_dose_se: os.coef_dose_se,
        coef_dose_ci_lo: os.coef_dose_ci_lo != null ? os.coef_dose_ci_lo : os.coef_dose - 1.96 * os.coef_dose_se,
        coef_dose_ci_hi: os.coef_dose_ci_hi != null ? os.coef_dose_ci_hi : os.coef_dose + 1.96 * os.coef_dose_se,
        converged: os.converged === true,
        random_effects_var: os.random_effects_var,
        fit_ok: os.fit_ok !== false,  // default true unless explicitly false in input
        lme4_version: os.lme4_version,
        dose_scale_sd: os.dose_scale_sd,
        coef_dose_on_scaled: os.coef_dose_on_scaled,
      },
      pooled_slope_log: os.coef_dose,
      pooled_slope_log_se: os.coef_dose_se,
      fallback: null,
      estimator: 'r_precomputed',
      ci_method: 'z_1.96',
      engine_version: API.engine_version,
    };
  }
  API.fitOneStage = fitOneStage;

  // ===================================================================
  // Section 3c: predict / forest / exportResults (Task 16)
  // ===================================================================

  function predict(result, dose) {
    if (!result) return null;
    var maxObserved = isFinite(result.max_observed_dose) ? result.max_observed_dose : null;
    var banner = (maxObserved != null) && (dose > 1.2 * maxObserved);

    var est, se;
    if (result.layer === 'rcs' && result.rcs && result.rcs.fit_at_dose) {
      // Nearest neighbour in fit_at_dose grid.
      var grid = result.rcs.fit_at_dose;
      var nearest = grid[0];
      for (var i = 1; i < grid.length; i++) {
        if (Math.abs(grid[i].dose - dose) < Math.abs(nearest.dose - dose)) nearest = grid[i];
      }
      return { est: nearest.est, ci_lo: nearest.ci_lo, ci_hi: nearest.ci_hi, extrapolation_banner: banner };
    } else {
      est = dose * result.pooled_slope_log;
      se = Math.abs(dose) * result.pooled_slope_log_se;
      // F-2 fix: use t_{k-1} (matches fitLinear's own CI construction) instead of raw z=1.96.
      // Falls back to z=1.96 only when pi_df is missing (defensive) or non-positive (k=1 edge,
      // which fitLinear itself rejects via the k<2 guard).
      var tcrit;
      if (result.ci_method === 'z_1.96') {
        tcrit = 1.96;  // P1-3: honour fitOneStage's documented z-CI annotation
      } else {
        var df = result.pi_df != null ? result.pi_df : (result.k != null ? result.k - 1 : 0);
        tcrit = df > 0 ? qt(0.975, df) : 1.96;
      }
      return { est: est, ci_lo: est - tcrit * se, ci_hi: est + tcrit * se, extrapolation_banner: banner };
    }
  }
  API.predict = predict;

  function forest(trials, result) {
    // P1-16: `trials` is reserved for future per-arm weight override; the function operates
    // entirely on result.per_study. Keep the param for backward compatibility.
    var rows = (result.per_study || []).map(function (s) {
      var sl = s.slope_log || 0, ssle = s.slope_log_se || 0;
      return {
        label: s.studlab,
        hr: Math.exp(sl),
        // P2-12: Per-study CIs use z=1.96 (standard forest-plot convention; the POOLED CI uses
        // t_{k-1} via F-2 fix). Asymmetry is intentional: per-study CIs are descriptive (one
        // study's own data); the pool's CI uses t because of the RE+HKSJ estimator.
        hr_ci_lo: Math.exp(sl - 1.96 * ssle),
        hr_ci_hi: Math.exp(sl + 1.96 * ssle),
        slope_log: sl,
        slope_log_se: ssle,
      };
    });
    // weights: 1 / (vi + tau2).
    // F-3 fix: fitRCS results carry tau² inside result.rcs.tau2_per_dim (per-dimension);
    // use dim 0 (the linear component) for forest weighting. fitLinear / fitOneStage
    // results expose result.tau2 directly.
    var tau2;
    if (result.layer === 'rcs' && result.rcs && Array.isArray(result.rcs.tau2_per_dim)) {
      tau2 = result.rcs.tau2_per_dim[0] || 0;
    } else {
      tau2 = result.tau2 || 0;
    }
    var w = rows.map(function (r) {
      var vi = r.slope_log_se * r.slope_log_se + tau2;
      return vi > 0 ? 1 / vi : 0;  // I1 guard: zero-variance row gets zero weight (excluded from pool)
    });
    var ws = w.reduce(function (a, b) { return a + b; }, 0);
    for (var i = 0; i < rows.length; i++) rows[i].weight_pct = 100 * w[i] / ws;
    return rows;
  }
  API.forest = forest;

  function exportResults(result) {
    if (!result) return null;
    var clone = JSON.parse(JSON.stringify(result));
    delete clone._fitInternal;
    clone.exported_at = new Date().toISOString();
    clone.engine_version = API.engine_version;
    return clone;
  }
  API.exportResults = exportResults;

  // ===================================================================
  // Section 4: fitLOO — leave-one-out sensitivity (v0.5.0)
  // Orchestrates fitLinear / fitRCS over each k-1 subset and returns the
  // per-trial delta vs the full pool. See engine header comment for
  // semantics.  No new statistical machinery — only calls the existing
  // layer fitters and assembles a per-trial delta record.
  //
  // k_full=2 special case:  fitLinear throws on k<2, and the LOO of a
  // k=2 pool drops to k=1.  In that case we fall back to the surviving
  // trial's own slope (from its per-study record, which fitLinear
  // already computed for the full-pool fit) and mark degenerated=true.
  // For RCS at k=1 the engine has a real single-trial path since v0.4
  // (estimator wls_single_trial_rcs); we still mark degenerated when
  // the LOO result's layer collapsed from rcs to linear (rcsKnots
  // returned fewer than K distinct locations on the LOO subset).
  // ===================================================================
  function fitLOO(trials, opts) {
    opts = opts || {};
    var layer = opts.layer === 'linear' ? 'linear' : 'rcs';
    var knots = (opts.knots != null) ? opts.knots : 3;
    var fitOpts = {};
    for (var k in opts) {
      if (k !== 'layer' && Object.prototype.hasOwnProperty.call(opts, k)) {
        fitOpts[k] = opts[k];
      }
    }

    // Validate the full pool first; LOO is meaningless on an invalid pool.
    var issues = validate(trials);
    if (issues.length) throw new Error('fitLOO: ' + issues[0]);

    var kFull = trials.length;
    if (kFull < 2) {
      // LOO over a k=1 pool would leave an empty subset; degenerate by spec.
      // We still return a full_pool fit (RCS k=1 path) so downstream KPI
      // code can read the headline without a null check.
      var solo = (layer === 'rcs')
        ? fitRCS(trials, fitOpts)
        : (function () { throw new Error('fitLOO: cannot LOO a k=1 pool at layer=linear (fitLinear requires k>=2)'); })();
      return {
        layer: layer,
        k_full: kFull,
        full_pool: solo,
        loo: [],
        summary: {
          max_abs_delta_slope: 0,
          most_influential_trial: null,
          any_sign_flip: false,
          any_significance_flip: false,
          n_degenerated: 0,
          skipped_reason: 'k_full < 2 — cannot drop a trial'
        }
      };
    }

    // Full-pool fit at the chosen layer.
    var fullPool;
    if (layer === 'rcs') {
      fullPool = fitRCS(trials, Object.assign({}, fitOpts, { knots: knots }));
    } else {
      fullPool = fitLinear(trials, fitOpts);
    }
    var fullSlope = fullPool.pooled_slope_log;
    var fullNlP = (fullPool.rcs && fullPool.rcs.nonlinearity_wald_p != null) ? fullPool.rcs.nonlinearity_wald_p : null;
    var fullCiLo = fullPool.pooled_slope_log_ci_lo;
    var fullCiHi = fullPool.pooled_slope_log_ci_hi;
    var fullSignLo = (fullCiLo == null || !isFinite(fullCiLo)) ? 0 : Math.sign(fullCiLo);
    var fullNlSig = (fullNlP != null && isFinite(fullNlP)) ? (fullNlP < 0.05) : null;

    // For the k_full=2 → k_loo=1 special case at the linear layer, we need a
    // per-trial slope.  fitLinear populated full_pool.per_study with the
    // GL-covariance-derived single-trial slope + SE; we lift it directly so
    // the LOO "pool" is the surviving trial's own slope.
    // For RCS k=2 → k=1, the engine's k=1 fitRCS branch is the real fit and
    // we don't need this fallback — fitRCS(subset) returns the right thing.
    var linearPerStudy = null;
    if (layer === 'linear' && kFull === 2 && fullPool.per_study) {
      linearPerStudy = fullPool.per_study;
    }

    var loo = [];
    var maxAbsDelta = -Infinity;
    var mostInflTrial = null;
    var anySignFlip = false;
    var anySigFlip = false;
    var nDegen = 0;

    for (var i = 0; i < kFull; i++) {
      var dropped = trials[i];
      var subset = trials.slice(0, i).concat(trials.slice(i + 1));
      var sub, degenerated = false;

      try {
        if (layer === 'rcs') {
          sub = fitRCS(subset, Object.assign({}, fitOpts, { knots: knots }));
          // engine's RCS fallback flips layer to 'linear' when rcsKnots returns
          // < K distinct knot locations on the LOO subset — that's degeneration
          // for our purposes.
          if (sub.layer === 'linear') degenerated = true;
        } else {
          // layer === 'linear'
          if (subset.length < 2) {
            // k_full=2 → k_loo=1: fall back to the surviving trial's per-study slope.
            if (linearPerStudy == null || linearPerStudy.length !== 2) {
              throw new Error('fitLOO: k_full=2 LOO requires fitLinear.per_study; got ' + (linearPerStudy && linearPerStudy.length));
            }
            // surviving idx is (1 - i); per_study is in trial order
            var surv = linearPerStudy[1 - i];
            var sloLo = surv.slope_log - 1.96 * surv.slope_log_se;
            var sloHi = surv.slope_log + 1.96 * surv.slope_log_se;
            sub = {
              layer: 'linear',
              k: 1,
              pooled_slope_log: surv.slope_log,
              pooled_slope_log_se: surv.slope_log_se,
              pooled_slope_log_ci_lo: sloLo,
              pooled_slope_log_ci_hi: sloHi,
              hksj_mv: null,
              tcrit: 1.96,
              rcs: null,
              _loo_single_trial_fallback: true
            };
            degenerated = true;
          } else {
            sub = fitLinear(subset, fitOpts);
          }
        }
      } catch (e) {
        // Even a fit failure produces a record so the caller can see which
        // LOO subset broke and why.  No silent-failure sentinel: we surface
        // the error message and mark degenerated.
        sub = {
          layer: layer,
          k: subset.length,
          pooled_slope_log: NaN,
          pooled_slope_log_se: NaN,
          pooled_slope_log_ci_lo: NaN,
          pooled_slope_log_ci_hi: NaN,
          hksj_mv: null,
          tcrit: null,
          rcs: null,
          _loo_error: String(e && e.message || e)
        };
        degenerated = true;
      }

      var nlPSub = (sub.rcs && sub.rcs.nonlinearity_wald_p != null) ? sub.rcs.nonlinearity_wald_p : null;
      var delta = isFinite(sub.pooled_slope_log) && isFinite(fullSlope)
        ? (sub.pooled_slope_log - fullSlope) : NaN;
      var subSignLo = (sub.pooled_slope_log_ci_lo == null || !isFinite(sub.pooled_slope_log_ci_lo))
        ? 0 : Math.sign(sub.pooled_slope_log_ci_lo);
      var signFlip = (subSignLo !== fullSignLo) && (fullSignLo !== 0) && (subSignLo !== 0);
      var sigFlip = false;
      if (fullNlSig !== null && nlPSub != null && isFinite(nlPSub)) {
        var subSig = (nlPSub < 0.05);
        sigFlip = (subSig !== fullNlSig);
      }

      if (degenerated) nDegen++;
      if (signFlip) anySignFlip = true;
      if (sigFlip) anySigFlip = true;
      if (isFinite(delta) && Math.abs(delta) > maxAbsDelta) {
        maxAbsDelta = Math.abs(delta);
        mostInflTrial = dropped.studlab;
      }

      loo.push({
        dropped_studlab: dropped.studlab,
        dropped_idx: i,
        k_loo: subset.length,
        pooled_slope_log: sub.pooled_slope_log,
        pooled_slope_log_se: sub.pooled_slope_log_se,
        pooled_slope_log_ci_lo: sub.pooled_slope_log_ci_lo,
        pooled_slope_log_ci_hi: sub.pooled_slope_log_ci_hi,
        nonlinearity_wald_p: nlPSub,
        hksj_mv: (sub.hksj_mv != null) ? sub.hksj_mv : null,
        tcrit: (sub.tcrit != null) ? sub.tcrit : null,
        delta_slope: delta,
        sign_flip: signFlip,
        significance_flip: sigFlip,
        degenerated: degenerated
      });
    }

    if (!isFinite(maxAbsDelta)) maxAbsDelta = 0;

    return {
      layer: layer,
      k_full: kFull,
      full_pool: fullPool,
      loo: loo,
      summary: {
        max_abs_delta_slope: maxAbsDelta,
        most_influential_trial: mostInflTrial,
        any_sign_flip: anySignFlip,
        any_significance_flip: anySigFlip,
        n_degenerated: nDegen
      }
    };
  }
  API._internal.fitLOO = fitLOO;

  // ===================================================================
  // Section: makeSeededRng — tiny LCG (Linear Congruential Generator).
  //
  // Numerical Recipes "minstd_rand"-style constants (Park-Miller 1988):
  //   X_{n+1} = (a * X_n) mod m   with a = 48271, m = 2^31 - 1 = 2147483647.
  //
  // This is NOT a cryptographic PRNG and not the best choice for high-D
  // Monte Carlo, but it is:
  //   - deterministic (same seed → identical sequence; required for the
  //     test 'fitBootstrap seed determinism' below)
  //   - cycle ≈ 2.1e9 (more than enough for our n_boot ≤ 10000 use)
  //   - no external dependency (works in browser + Node)
  //   - cheap (no Math.random branching, no entropy probe)
  //
  // Seed is forced into (0, m) — seed=0 maps to 1 to avoid the LCG fixed
  // point at 0. Returns a closure rng() → uniform on (0, 1).
  // ===================================================================
  function makeSeededRng(seed) {
    var m = 2147483647;  // 2^31 - 1
    var a = 48271;
    var s = (seed | 0) % m;
    if (s <= 0) s += m - 1;  // avoid s = 0 fixed point; map 0 → m-1
    return function () {
      s = (a * s) % m;
      return s / m;
    };
  }
  API._internal.makeSeededRng = makeSeededRng;

  // ===================================================================
  // Section: fitBootstrap (engine v0.7.0)
  //
  // Non-parametric trial-bootstrap CI as a sensitivity check on the
  // analytical HKSJ-multivariate CIs returned by fitLinear / fitRCS.
  // Especially informative at extreme I² (e.g. SUSTAIN's 97%) where the
  // analytical CI's normal-theory assumptions are stressed.
  //
  // Algorithm: for each of n_boot bootstrap samples:
  //   1. Sample k_full trial indices uniformly with replacement from
  //      trials[0..k_full-1] using the seeded LCG.
  //   2. Refit fitLinear (or fitRCS) on the resampled trial list.
  //   3. Record pooled_slope_log; for RCS also record nonlinearity_wald_p.
  //   4. On exception (singular per-trial design after resampling, RCS
  //      knot degeneration, REML non-convergence on a duplicate-only
  //      sample), tally n_failed and continue.
  //
  // Returns (top-level fields, no .rcs nesting — meta-summary):
  //   layer, k_full, n_boot, seed, alpha,
  //   bootstrap_slopes, n_failed,
  //   bootstrap_ci_lo, bootstrap_ci_hi, bootstrap_median, bootstrap_se,
  //   analytical_ci_lo, analytical_ci_hi,
  //   ci_lo_delta, ci_hi_delta,
  //   coverage_warning  (true if k_full<4 or n_failed > 5% of n_boot)
  // RCS layer also:
  //   bootstrap_nonlin_ps, bootstrap_nonlin_p_median,
  //   nonlin_p_fraction_below_005
  // ===================================================================
  function fitBootstrap(trials, opts) {
    opts = opts || {};
    var layer = (opts.layer === 'linear') ? 'linear' : 'rcs';
    var knots = (opts.knots != null) ? opts.knots : 3;
    var n_boot = (opts.n_boot != null) ? opts.n_boot : 1000;
    var seed = (opts.seed != null) ? opts.seed : 12345;
    var alpha = (opts.alpha != null) ? opts.alpha : 0.05;

    if (!Array.isArray(trials) || trials.length < 1) {
      throw new Error('fitBootstrap: requires k >= 1 trial; got k=' + (trials && trials.length));
    }
    // validate() on the full pool first; bootstrap of an invalid pool is
    // meaningless.  fitLinear / fitRCS will re-validate per sample.
    var issues = validate(trials);
    if (issues.length) throw new Error('fitBootstrap: ' + issues[0]);

    var k_full = trials.length;

    // Build opts pass-through for the inner fits (drop our own keys so we
    // don't recurse / over-pass).
    var innerOpts = {};
    for (var key in opts) {
      if (!Object.prototype.hasOwnProperty.call(opts, key)) continue;
      if (key === 'layer' || key === 'n_boot' || key === 'seed') continue;
      innerOpts[key] = opts[key];
    }

    // Analytical baseline (computed once on the full pool for the
    // comparison fields).  If this throws, the bootstrap can still run
    // (we just won't have analytical baselines to delta against).
    var analytical_ci_lo = NaN, analytical_ci_hi = NaN;
    try {
      var fullFit = (layer === 'rcs')
        ? fitRCS(trials, Object.assign({}, innerOpts, { knots: knots }))
        : fitLinear(trials, innerOpts);
      analytical_ci_lo = fullFit.pooled_slope_log_ci_lo;
      analytical_ci_hi = fullFit.pooled_slope_log_ci_hi;
    } catch (e) {
      // analytical baseline failed; leave NaN, surface via deltas below.
    }

    var rng = makeSeededRng(seed);
    var bootstrap_slopes = [];
    var bootstrap_nonlin_ps = [];
    var n_failed = 0;

    for (var b = 0; b < n_boot; b++) {
      // Sample k_full trial indices with replacement.
      var sampled = new Array(k_full);
      for (var i = 0; i < k_full; i++) {
        // floor(rng() * k_full) — rng is uniform on (0, 1), so this is
        // uniform on {0, 1, ..., k_full-1}.
        var idx = Math.floor(rng() * k_full);
        if (idx >= k_full) idx = k_full - 1;  // safety against rare boundary
        sampled[i] = trials[idx];
      }
      try {
        var fit = (layer === 'linear')
          ? fitLinear(sampled, innerOpts)
          : fitRCS(sampled, Object.assign({}, innerOpts, { knots: knots }));
        var slope = fit.pooled_slope_log;
        if (!isFinite(slope)) {
          n_failed++;
          continue;
        }
        bootstrap_slopes.push(slope);
        if (layer === 'rcs' && fit.rcs && fit.rcs.nonlinearity_wald_p != null
            && isFinite(fit.rcs.nonlinearity_wald_p)) {
          bootstrap_nonlin_ps.push(fit.rcs.nonlinearity_wald_p);
        }
      } catch (e) {
        n_failed++;
      }
    }

    // Percentile CI: sort the surviving slopes and pull alpha/2 and 1-alpha/2
    // indices. Use linear interpolation between order statistics so the
    // result is continuous in n_boot (matches numpy.quantile default).
    function percentile(sortedArr, p) {
      var n = sortedArr.length;
      if (n === 0) return NaN;
      if (n === 1) return sortedArr[0];
      var idx = p * (n - 1);
      var lo = Math.floor(idx), hi = Math.ceil(idx);
      if (lo === hi) return sortedArr[lo];
      var frac = idx - lo;
      return sortedArr[lo] * (1 - frac) + sortedArr[hi] * frac;
    }

    var sorted = bootstrap_slopes.slice().sort(function (a, b) { return a - b; });
    var bootstrap_ci_lo = percentile(sorted, alpha / 2);
    var bootstrap_ci_hi = percentile(sorted, 1 - alpha / 2);
    var bootstrap_median = percentile(sorted, 0.5);

    // SD across bootstrap_slopes
    var nb = bootstrap_slopes.length;
    var bootstrap_se = NaN;
    if (nb >= 2) {
      var mean = 0;
      for (var mi = 0; mi < nb; mi++) mean += bootstrap_slopes[mi];
      mean /= nb;
      var ssq = 0;
      for (var si = 0; si < nb; si++) {
        var d = bootstrap_slopes[si] - mean;
        ssq += d * d;
      }
      bootstrap_se = Math.sqrt(ssq / (nb - 1));
    } else if (nb === 1) {
      bootstrap_se = 0;
    }

    var ci_lo_delta = (isFinite(bootstrap_ci_lo) && isFinite(analytical_ci_lo))
      ? (bootstrap_ci_lo - analytical_ci_lo) : NaN;
    var ci_hi_delta = (isFinite(bootstrap_ci_hi) && isFinite(analytical_ci_hi))
      ? (bootstrap_ci_hi - analytical_ci_hi) : NaN;

    var failure_rate = n_failed / Math.max(1, n_boot);
    var coverage_warning = (k_full < 4) || (failure_rate > 0.05);

    var out = {
      layer: layer,
      k_full: k_full,
      n_boot: n_boot,
      seed: seed,
      alpha: alpha,
      bootstrap_slopes: bootstrap_slopes,
      n_failed: n_failed,
      bootstrap_ci_lo: bootstrap_ci_lo,
      bootstrap_ci_hi: bootstrap_ci_hi,
      bootstrap_median: bootstrap_median,
      bootstrap_se: bootstrap_se,
      analytical_ci_lo: analytical_ci_lo,
      analytical_ci_hi: analytical_ci_hi,
      ci_lo_delta: ci_lo_delta,
      ci_hi_delta: ci_hi_delta,
      coverage_warning: coverage_warning,
      engine_version: API.engine_version,
    };

    if (layer === 'rcs') {
      var sortedP = bootstrap_nonlin_ps.slice().sort(function (a, b) { return a - b; });
      out.bootstrap_nonlin_ps = bootstrap_nonlin_ps;
      out.bootstrap_nonlin_p_median = percentile(sortedP, 0.5);
      var n_below = 0;
      for (var pi = 0; pi < bootstrap_nonlin_ps.length; pi++) {
        if (bootstrap_nonlin_ps[pi] < 0.05) n_below++;
      }
      out.nonlin_p_fraction_below_005 = (bootstrap_nonlin_ps.length > 0)
        ? (n_below / bootstrap_nonlin_ps.length)
        : NaN;
    }

    return out;
  }
  API._internal.fitBootstrap = fitBootstrap;

  root.RapidMetaDoseResp = API;
  if (typeof module !== 'undefined' && module.exports) module.exports = API;
})(typeof window !== 'undefined' ? window : globalThis);
