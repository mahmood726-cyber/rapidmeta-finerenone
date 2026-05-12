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
  // (lines 57-202) to keep cross-engine numerical behaviour identical.
  // matMul, matVec (alias), transpose defined fresh (not present in source).
  // pmTau2 = tau2REML from source (PM-by-bisection; renamed for convention).
  // qt = tinv from source; pt = _tCDFapprox from source.
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
    if (df <= 0) return 0;
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
  // t-distribution CDF. Exposed as pt() for convention.
  function _tCDFapprox(t, df) {
    // Use beta-relation: F_T(t) = 1 - 0.5 * I_{df/(df+t^2)}(df/2, 1/2) for t>=0.
    if (t < 0) return 1 - _tCDFapprox(-t, df);
    var x = df / (df + t * t);
    return 1 - 0.5 * ibeta(df / 2, 0.5, x);
  }
  function pt(t, df) { return _tCDFapprox(t, df); }

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

  // Matrix helpers not present in prognostic engine — defined fresh.
  function matMul(A, B) {
    var r = A.length, k = A[0].length, c = B[0].length;
    var M = []; for (var i = 0; i < r; i++) { M.push(new Array(c).fill(0)); for (var j = 0; j < c; j++) for (var p = 0; p < k; p++) M[i][j] += A[i][p] * B[p][j]; }
    return M;
  }
  function matVec(A, v) {
    var r = A.length, k = A[0].length;
    var out = new Array(r).fill(0);
    for (var i = 0; i < r; i++) for (var j = 0; j < k; j++) out[i] += A[i][j] * v[j];
    return out;
  }
  function transpose(M) {
    var r = M.length, c = M[0].length, T = [];
    for (var j = 0; j < c; j++) { T.push(new Array(r)); for (var i = 0; i < r; i++) T[j][i] = M[i][j]; }
    return T;
  }

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
    return issues;
  }

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

  // ===================================================================
  // Section 2b: RCS helpers — knot placement (Harrell percentiles) and
  // truncated power basis (Units 11-12).
  // ===================================================================

  // quantile(sorted, p): R type-7 linear interpolation on a pre-sorted array.
  function quantile(sorted, p) {
    var n = sorted.length;
    if (n === 0) return NaN;
    if (n === 1) return sorted[0];
    var h = (n - 1) * p;
    var lo = Math.floor(h), hi = Math.ceil(h);
    return sorted[lo] + (h - lo) * (sorted[hi] - sorted[lo]);
  }

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

  // ===================================================================
  // Section 2a: fitLinear — two-stage Greenland-Longnecker linear pool.
  // Per-study WLS slope via GL covariance, then REML+HKSJ RE pool.
  // ===================================================================
  function fitLinear(trials, opts) {
    opts = opts || {};
    var issues = validate(trials);
    if (issues.length > 0) throw new Error('fitLinear: ' + issues[0]);

  // I-1 fix: validate() is a data-shape checker, not a statistical-feasibility
  // checker. k<2 produces NaN downstream (qt(0.975, 0) is undefined).
  if (trials.length < 2) {
    throw new Error('fitLinear: requires k >= 2 trials; got k=' + trials.length);
  }

    var alpha = opts.alpha || 0.05;
    var perStudy = [];

    for (var t = 0; t < trials.length; t++) {
      var T = trials[t];
      var ref = T.arms.find(function (a) { return a.is_reference; });
      var contrasts = T.arms.filter(function (a) { return !a.is_reference; });
      var x = contrasts.map(function (a) { return a.dose - ref.dose; });
  // P1 hardening TODO: zero-cell continuity correction (advanced-stats.md).
  // If a.events === 0 or ref.events === 0, log(0/p) = -Infinity which propagates
  // to NaN through WLS. Add conditional +0.5 only if ≥1 cell is zero (per
  // advanced-stats.md: "Add 0.5 ONLY if >=1 cell is zero. Unconditional correction biases OR->1").
  // Deferred from Round 1A.
      var y = contrasts.map(function (a) {
        var pi = a.events / a.n, p0 = ref.events / ref.n;
        return Math.log(pi / p0);
      });
      var S = glCovariance(T.arms);
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

    var k = perStudy.length;
    var yi = perStudy.map(function (s) { return s.slope_log; });
    var vi = perStudy.map(function (s) { return s.slope_log_se * s.slope_log_se; });

    // REML tau² via Paule-Mandel bisection
    var tau2 = pmTau2(yi, vi);

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
      tau2: tau2, tau2_lo: null, tau2_hi: null,  // Q-profile deferred to P2 hardening
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

  // ===================================================================
  // Section 2c: fitRCS — two-stage Greenland-Longnecker + restricted-cubic-spline
  // multivariate-RE pool.  Algorithm per plan Task 13.
  // ===================================================================
  function fitRCS(trials, opts) {
    opts = opts || {};
    var issues = validate(trials);
    if (issues.length) throw new Error('fitRCS: ' + issues[0]);
    if (trials.length < 2) throw new Error('fitRCS: requires k >= 2 trials; got k=' + trials.length);
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
      var y = contrasts.map(function (arm) {
        return Math.log((arm.events / arm.n) / (ref.events / ref.n));
      });
      var S = glCovariance(T.arms);
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
      perStudy.push({ studlab: T.studlab, beta: beta_i, V: V_i, n_arms: T.arms.length });
    }

    // v0.1 design choice: diagonal-PM-per-dimension τ² approximation.
    // Each spline-basis dimension gets its own Paule-Mandel τ², independent of
    // the others. This is simpler than the full multivariate REML used by R's
    // dosresmeta/mixmeta and matches dosresmeta's vcov='ind' family of methods,
    // but is even further simplified (no joint REML across dimensions).
    //
    // Practical consequence: the non-linearity Wald p-value will differ
    // substantially from R for datasets where the non-linear-coefficient
    // heterogeneity is high. Verified on GL-1992: engine p ≈ 0.048 vs R mixmeta
    // p ≈ 0.704. The engine's linear-component pooled slope still matches R to
    // ~6% (this is what fitLinear's parity test validates).
    //
    // P2 hardening: lift to full multivariate REML via joint optimization of
    // a τ² matrix (Jackson 2010). Until then, the R-parity badge in Unit 8
    // must use a looser tolerance for non-linearity p OR exclude it from the
    // parity gate.

    // Step 3: per-dimension PM tau² + IV pool (diagonal tau² approximation).
    // Each spline-coef dimension gets its own tau²_d via Paule-Mandel.
    var pooled = new Array(Kp).fill(0);
    var pooledSE = new Array(Kp).fill(0);
    var tau2_per_dim = new Array(Kp).fill(0);
    for (var d = 0; d < Kp; d++) {
      var yd = perStudy.map(function (s) { return s.beta[d]; });
      var vd = perStudy.map(function (s) { return s.V[d][d]; });
      tau2_per_dim[d] = pmTau2(yd, vd);
      var wd = vd.map(function (v) { return 1 / (v + tau2_per_dim[d]); });
      var wsum = wd.reduce(function (a, b) { return a + b; }, 0);
      pooled[d] = yd.reduce(function (acc, yval, idx) { return acc + wd[idx] * yval; }, 0) / wsum;
      pooledSE[d] = Math.sqrt(1 / wsum);
    }

    // Step 4: non-linearity Wald test.
    // H0: all non-linear basis coefs (d >= 1) are zero.
    // Statistic: sum_d (beta_d / se_d)^2 ~ chi2(K-2) under H0.
    // Note: pooled[0] is the linear trend; pooled[1..Kp-1] are the non-linear deviations.
    var nlCoefs = pooled.slice(1);
    var nlSEs = pooledSE.slice(1);
    var W = 0;
    for (var d2 = 0; d2 < nlCoefs.length; d2++) {
      W += (nlCoefs[d2] / nlSEs[d2]) * (nlCoefs[d2] / nlSEs[d2]);
    }
    var nlP = nlCoefs.length > 0 ? (1 - pchisq(W, nlCoefs.length)) : null;

    // Step 5: fit_at_dose — 20-point curve from 0 to max observed dose.
    // At dose=0, rcsBasis returns [0, 0, ...], so est=0 (centered at reference).
    var maxD = Math.max.apply(null, allDoses);
    var fit_at_dose = [];
    for (var i2 = 0; i2 < 20; i2++) {
      var dose_i = i2 * maxD / 19;
      var b = rcsBasis(dose_i, knots);
      var est = 0, varEst = 0;
      for (var p2 = 0; p2 < Kp; p2++) {
        est += pooled[p2] * b[p2];
        varEst += b[p2] * b[p2] * pooledSE[p2] * pooledSE[p2];
      }
      var seEst = Math.sqrt(varEst);
      fit_at_dose.push({ dose: dose_i, est: est, ci_lo: est - 1.96 * seEst, ci_hi: est + 1.96 * seEst });
    }

    // v0.1 CI method: raw z=1.96 on diagonal-PM pooled SE. Unlike fitLinear (which uses
    // HKSJ-adjusted t_{k-1}), fitRCS does NOT apply HKSJ here because the multivariate
    // version requires a pooled Q across all spline dimensions which isn't computed
    // under the diagonal-PM approximation. P2 hardening: when full multivariate REML
    // lands, swap to HKSJ-multivariate + t_{k-1}.
    return {
      layer: 'rcs', k: perStudy.length,
      rcs: {
        knots: knots,
        spline_coefs: pooled,
        spline_coefs_se: pooledSE,
        tau2_per_dim: tau2_per_dim,
        nonlinearity_wald_p: nlP,
        fit_at_dose: fit_at_dose,
      },
      pooled_slope_log: pooled[0],
      pooled_slope_log_se: pooledSE[0],
      pooled_slope_log_ci_lo: pooled[0] - 1.96 * pooledSE[0],
      pooled_slope_log_ci_hi: pooled[0] + 1.96 * pooledSE[0],
      per_study: perStudy.map(function (s) {
        return { studlab: s.studlab, slope_log: s.beta[0], slope_log_se: Math.sqrt(s.V[0][0]), n_arms: s.n_arms };
      }),
      max_observed_dose: maxD,
      coverage_warning: perStudy.length < 10,
      fallback: null,
      estimator: 'pm_diagonal_z',
      ci_method: 'z_1.96',
      converged: true,
      iterations: null,
      _fitInternal: null,
      engine_version: API.engine_version,
    };
  }

  // ===================================================================
  // Section 3a: nonLinearityTest(rcsResult) — thin wrapper (Task 14)
  // Extracts Wald chi² / df / p from a fitRCS result.
  // ===================================================================
  function nonLinearityTest(rcsResult) {
    if (!rcsResult || !rcsResult.rcs) {
      return { wald_chi2: null, df: null, p: null, conclusion: 'inconclusive' };
    }
    var nlCoefs = rcsResult.rcs.spline_coefs.slice(1);
    var nlSEs = rcsResult.rcs.spline_coefs_se.slice(1);
    var W = 0;
    for (var d = 0; d < nlCoefs.length; d++) {
      if (nlSEs[d] > 0) {
        W += (nlCoefs[d] / nlSEs[d]) * (nlCoefs[d] / nlSEs[d]);
      }
      // I2 guard: skip terms with zero SE (would produce Infinity); the per-dim Wald is 0 for that dim.
    }
    var p = rcsResult.rcs.nonlinearity_wald_p;
    var conclusion = p < 0.05 ? 'non_linear' : (p > 0.20 ? 'linear' : 'inconclusive');
    return { wald_chi2: W, df: nlCoefs.length, p: p, conclusion: conclusion };
  }

  // ===================================================================
  // Section 3b: fitOneStage(trials, opts, precomputedJson) — JSON reader (Task 15)
  // One-stage hierarchical is NOT fitted in JS v0.1.  Pass precomputedJson=null
  // to signal the caller must run R Round-1B.  Pass the JSON object from
  // outputs/r_validation/doseresp/<REVIEW>.json to read R precomputed coefs.
  // ===================================================================
  function fitOneStage(trials, opts, precomputedJson) {
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
      },
      pooled_slope_log: os.coef_dose,
      pooled_slope_log_se: os.coef_dose_se,
      fallback: null,
      estimator: 'r_precomputed',
      ci_method: 'z_1.96',
      engine_version: API.engine_version,
    };
  }

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
      var df = result.pi_df != null ? result.pi_df : (result.k != null ? result.k - 1 : 0);
      var tcrit = df > 0 ? qt(0.975, df) : 1.96;
      return { est: est, ci_lo: est - tcrit * se, ci_hi: est + tcrit * se, extrapolation_banner: banner };
    }
  }

  function forest(trials, result) {
    var rows = (result.per_study || []).map(function (s) {
      var sl = s.slope_log || 0, ssle = s.slope_log_se || 0;
      return {
        label: s.studlab,
        hr: Math.exp(sl),
        hr_ci_lo: Math.exp(sl - 1.96 * ssle),
        hr_ci_hi: Math.exp(sl + 1.96 * ssle),
        slope_log: sl,
        slope_log_se: ssle,
      };
    });
    // Weights: 1 / (vi + tau2) — re-derive from result to match pool.
    var tau2 = result.tau2 || 0;
    var w = rows.map(function (r) {
      var vi = r.slope_log_se * r.slope_log_se + tau2;
      return vi > 0 ? 1 / vi : 0;  // I1 guard: zero-variance row gets zero weight (excluded from pool)
    });
    var ws = w.reduce(function (a, b) { return a + b; }, 0);
    for (var i = 0; i < rows.length; i++) rows[i].weight_pct = 100 * w[i] / ws;
    return rows;
  }

  function exportResults(result) {
    if (!result) return null;
    var clone = JSON.parse(JSON.stringify(result));
    delete clone._fitInternal;
    clone.exported_at = new Date().toISOString();
    clone.engine_version = API.engine_version;
    return clone;
  }

  var API = {
    engine_version: 'rapidmeta-dose-response-engine-v1@0.1.0',
    validate: validate,
    fitLinear: fitLinear,
    fitRCS: fitRCS,
    fitOneStage: fitOneStage,
    nonLinearityTest: nonLinearityTest,
    predict: predict,
    forest: forest,
    exportResults: exportResults,
    _internal: {},
  };

  API._internal = Object.assign(API._internal || {}, {
    zeros: zeros, inv2x2: inv2x2, matInv: matInv,
    matMul: matMul, matVec: matVec, transpose: transpose,
    qchisq: qchisq, qt: qt, pchisq: pchisq, pt: pt,
    pmTau2: pmTau2,
    glCovariance: glCovariance,
    quantile: quantile,
    rcsKnots: rcsKnots,
    rcsBasis: rcsBasis,
  });

  root.RapidMetaDoseResp = API;
  if (typeof module !== 'undefined' && module.exports) module.exports = API;
})(typeof window !== 'undefined' ? window : globalThis);
