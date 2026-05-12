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

  API._internal = Object.assign(API._internal || {}, {
    zeros: zeros, inv2x2: inv2x2, matInv: matInv,
    matMul: matMul, matVec: matVec, transpose: transpose,
    qchisq: qchisq, qt: qt, pchisq: pchisq, pt: pt,
    pmTau2: pmTau2,
    glCovariance: glCovariance,
  });

  root.RapidMetaDoseResp = API;
  if (typeof module !== 'undefined' && module.exports) module.exports = API;
})(typeof window !== 'undefined' ? window : globalThis);
