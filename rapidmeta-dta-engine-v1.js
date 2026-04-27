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

  // ---------- Linear algebra (k<50 dense) ----------
  function zeros(r, c) { var m=[]; for(var i=0;i<r;i++) m.push(new Array(c).fill(0)); return m; }
  function eye(n) { var m=zeros(n,n); for(var i=0;i<n;i++) m[i][i]=1; return m; }
  function matmul(a, b) {
    var ra=a.length, ca=a[0].length, cb=b[0].length, r=zeros(ra,cb);
    for(var i=0;i<ra;i++) for(var j=0;j<cb;j++) {
      var s=0; for(var k=0;k<ca;k++) s+=a[i][k]*b[k][j]; r[i][j]=s;
    }
    return r;
  }
  function transpose(m) { var r=m.length, c=m[0].length, t=zeros(c,r); for(var i=0;i<r;i++) for(var j=0;j<c;j++) t[j][i]=m[i][j]; return t; }
  function matvec(a, v) { var r=new Array(a.length).fill(0); for(var i=0;i<a.length;i++) { var s=0; for(var j=0;j<v.length;j++) s+=a[i][j]*v[j]; r[i]=s; } return r; }
  function inv2x2(M) {
    var a=M[0][0], b=M[0][1], c=M[1][0], d=M[1][1];
    var det = a*d - b*c;
    if (Math.abs(det) < 1e-15) throw new Error('Singular 2x2');
    return [[d/det, -b/det], [-c/det, a/det]];
  }

  // ---------- Clopper-Pearson exact binomial CI (per lessons.md) ----------
  // qbeta inverse via bisection on the regularized incomplete beta
  function lnGamma(z) {
    var c=[76.18009172947146,-86.50532032941677,24.01409824083091,-1.231739572450155,1.208650973866179e-3,-5.395239384953e-6];
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
      d=1+aa*d; if(Math.abs(d)<fpmin) d=fpmin; c=1+aa/c; if(Math.abs(c)<fpmin) c=fpmin; d=1/d; h*=d*c;
      aa=-(a+m)*(qab+m)*x/((a+m2)*(qap+m2));
      d=1+aa*d; if(Math.abs(d)<fpmin) d=fpmin; c=1+aa/c; if(Math.abs(c)<fpmin) c=fpmin; d=1/d;
      var del=d*c; h*=del; if(Math.abs(del-1)<3e-7) break;
    }
    return h;
  }
  function ibeta(a, b, x) {
    if (x<=0) return 0; if (x>=1) return 1;
    var bt = Math.exp(lnGamma(a+b) - lnGamma(a) - lnGamma(b) + a*Math.log(x) + b*Math.log(1-x));
    if (x < (a+1)/(a+b+2)) return bt*betacf(a,b,x)/a;
    return 1 - bt*betacf(b,a,1-x)/b;
  }
  function qbeta(p, a, b) {
    // bisection on x for ibeta(a,b,x)=p, x in (0,1)
    var lo=0, hi=1, mid;
    for(var i=0;i<60;i++){ mid=(lo+hi)/2; if (ibeta(a,b,mid) < p) lo=mid; else hi=mid; }
    return mid;
  }
  function clopperPearson(x, n, alpha) {
    alpha = alpha || 0.05;
    if (n === 0) return [0, 1];
    var lo = (x === 0) ? 0 : qbeta(alpha/2, x, n-x+1);
    var hi = (x === n) ? 1 : qbeta(1-alpha/2, x+1, n-x);
    return [lo, hi];
  }

  // ---------- Per-study Sens/Spec ----------
  function perStudy(trial) {
    var sens = trial.TP / (trial.TP + trial.FN);
    var spec = trial.TN / (trial.TN + trial.FP);
    var sens_ci = clopperPearson(trial.TP, trial.TP + trial.FN, 0.05);
    var spec_ci = clopperPearson(trial.TN, trial.TN + trial.FP, 0.05);
    return { studlab: trial.studlab, sens: sens, spec: spec, sens_ci: sens_ci, spec_ci: spec_ci };
  }

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
    _version: '1.0.0-rc',
    _internal: { matmul, inv2x2, clopperPearson, perStudy, lnGamma, ibeta, qbeta }
  };
})(typeof window !== 'undefined' ? window : globalThis);
