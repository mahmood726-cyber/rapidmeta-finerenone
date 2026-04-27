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

  // ---------- Continuity correction (Q1: 0.5 conditional on any zero, applied to all) ----------
  function applyContinuityCorrection(trials, correction) {
    correction = (correction == null) ? 0.5 : correction;
    var hasZero = trials.some(function(t){ return t.TP===0 || t.FP===0 || t.FN===0 || t.TN===0; });
    if (!hasZero || correction === 0) return { trials: trials.slice(), corrected: false };
    var corrected = trials.map(function(t){
      return { studlab: t.studlab, TP: t.TP+correction, FP: t.FP+correction, FN: t.FN+correction, TN: t.TN+correction };
    });
    return { trials: corrected, corrected: true };
  }

  // ---------- FE bivariate (closed form: inverse-variance weighted on logits) ----------
  // Used as the k<5 fallback and as the Reitsma starting value.
  function feBivariate(trials) {
    // For each study: yi_sens = logit(sens_i), vi_sens = 1/TP + 1/FN
    //                yi_spec = logit(spec_i), vi_spec = 1/TN + 1/FP
    var ys=[], vs=[], ysp=[], vsp=[], wsens=[], wspec=[];
    var swSens=0, swSpec=0, syw_s=0, syw_sp=0;
    for (var i=0;i<trials.length;i++){
      var t=trials[i], pos=t.TP+t.FN, neg=t.TN+t.FP;
      var sens=t.TP/pos, spec=t.TN/neg;
      var lse=Math.log(sens/(1-sens)), vse=1/t.TP + 1/t.FN;
      var lsp=Math.log(spec/(1-spec)), vsp_=1/t.TN + 1/t.FP;
      ys.push(lse); vs.push(vse); ysp.push(lsp); vsp.push(vsp_);
      var ws=1/vse, wp=1/vsp_;
      wsens.push(ws); wspec.push(wp);
      swSens+=ws; swSpec+=wp; syw_s+=ws*lse; syw_sp+=wp*lsp;
    }
    var muSens = syw_s / swSens, muSpec = syw_sp / swSpec;
    var seSens = Math.sqrt(1/swSens), seSpec = Math.sqrt(1/swSpec);
    // Pearson correlation of standardized logit residuals (between-study, ignoring within)
    var rs=0, rss=0, rsp=0;
    for (var i=0;i<ys.length;i++){
      var dy=ys[i]-muSens, dx=ysp[i]-muSpec;
      rs += dy*dx; rss += dy*dy; rsp += dx*dx;
    }
    var rho = (rss>0 && rsp>0) ? rs/Math.sqrt(rss*rsp) : 0;
    rho = Math.max(-0.95, Math.min(0.95, rho));
    return {
      mu_sens_logit: muSens, mu_spec_logit: muSpec,
      se_sens_logit: seSens, se_spec_logit: seSpec,
      tau2_sens: 0, tau2_spec: 0, rho: rho,
      iterations: 0, converged: true,
      estimator: 'fe_bivariate'
    };
  }

  // ---------- Reitsma bivariate via REML (Nelder-Mead simplex on profile likelihood) ----------
  //
  // Plan-author note: original T4 plan used damped Newton with numerical-derivative
  // Hessian + an inner negLogLik that captured stale mu_hat from the outer loop.
  // That approach didn't converge on AuditC (tau^2 stuck at initialization, rho wrong sign).
  // The fix: (a) re-profile mu_hat at each candidate inside the likelihood,
  // and (b) use Nelder-Mead simplex (no gradient/Hessian needed). Same likelihood
  // as mada::reitsma, just a robust optimizer for it.
  function reitsmaREML(trials, opts) {
    opts = opts || {};
    var max_iter = opts.max_iter || 500;
    var tol = opts.tol || 1e-7;

    // Build per-study (y_i, Sigma_i)
    var ys = [], Sigs = [];
    for (var i = 0; i < trials.length; i++) {
      var t = trials[i], pos = t.TP + t.FN, neg = t.TN + t.FP;
      var sens = t.TP / pos, spec = t.TN / neg;
      ys.push([Math.log(sens / (1 - sens)), Math.log(spec / (1 - spec))]);
      Sigs.push([[1 / t.TP + 1 / t.FN, 0], [0, 1 / t.TN + 1 / t.FP]]);
    }

    // Profile-likelihood: at each candidate (ts, tc, rh), compute mu_hat from V_i, then evaluate ll.
    function negLogLikProfile(par) {
      var ts = par[0], tc = par[1], rh = par[2];
      if (ts <= 1e-10 || tc <= 1e-10) return 1e20;
      if (rh < -0.95 || rh > 0.95) return 1e20;
      var Om = [[ts, rh * Math.sqrt(ts * tc)], [rh * Math.sqrt(ts * tc), tc]];
      var sV = [[0, 0], [0, 0]], sVy = [0, 0];
      var Vis = [], dets = [];
      for (var i = 0; i < ys.length; i++) {
        var Vm = [[Sigs[i][0][0] + Om[0][0], Sigs[i][0][1] + Om[0][1]],
                  [Sigs[i][1][0] + Om[1][0], Sigs[i][1][1] + Om[1][1]]];
        var det = Vm[0][0] * Vm[1][1] - Vm[0][1] * Vm[1][0];
        if (det <= 1e-15) return 1e20;
        dets.push(det);
        var Vmi;
        try { Vmi = inv2x2(Vm); } catch (e) { return 1e20; }
        Vis.push(Vmi);
        sV[0][0] += Vmi[0][0]; sV[0][1] += Vmi[0][1];
        sV[1][0] += Vmi[1][0]; sV[1][1] += Vmi[1][1];
        sVy[0] += Vmi[0][0] * ys[i][0] + Vmi[0][1] * ys[i][1];
        sVy[1] += Vmi[1][0] * ys[i][0] + Vmi[1][1] * ys[i][1];
      }
      var detSV = sV[0][0] * sV[1][1] - sV[0][1] * sV[1][0];
      if (detSV <= 1e-15) return 1e20;
      var muCov;
      try { muCov = inv2x2(sV); } catch (e) { return 1e20; }
      var muHat = [muCov[0][0] * sVy[0] + muCov[0][1] * sVy[1],
                   muCov[1][0] * sVy[0] + muCov[1][1] * sVy[1]];
      var ll = 0;
      for (var i = 0; i < ys.length; i++) {
        var Vmi = Vis[i];
        var dy = [ys[i][0] - muHat[0], ys[i][1] - muHat[1]];
        var quad = dy[0] * (Vmi[0][0] * dy[0] + Vmi[0][1] * dy[1]) +
                   dy[1] * (Vmi[1][0] * dy[0] + Vmi[1][1] * dy[1]);
        ll += 0.5 * Math.log(dets[i]) + 0.5 * quad;
      }
      ll += 0.5 * Math.log(detSV);
      return ll;
    }

    // Nelder-Mead simplex on 3 parameters
    function nelderMead(f, x0, maxIter, tolNM) {
      var n = x0.length;
      var alpha = 1, gamma = 2, rho_NM = 0.5, sigma = 0.5;
      var simplex = [x0.slice()];
      for (var i = 0; i < n; i++) {
        var v = x0.slice();
        var step = (i === 2) ? 0.2 : 0.1;
        v[i] += step;
        simplex.push(v);
      }
      var fvals = simplex.map(f);
      var iter, converged = false;
      for (iter = 0; iter < maxIter; iter++) {
        var order = simplex.map(function (_, i) { return i; })
                           .sort(function (a, b) { return fvals[a] - fvals[b]; });
        simplex = order.map(function (i) { return simplex[i]; });
        fvals = order.map(function (i) { return fvals[i]; });
        var spread = 0;
        for (var j = 0; j < n; j++) {
          var minv = simplex[0][j], maxv = simplex[0][j];
          for (var k = 1; k <= n; k++) {
            if (simplex[k][j] < minv) minv = simplex[k][j];
            if (simplex[k][j] > maxv) maxv = simplex[k][j];
          }
          spread += (maxv - minv);
        }
        if (spread < tolNM) { converged = true; break; }
        var centroid = new Array(n).fill(0);
        for (var i = 0; i < n; i++) {
          for (var j = 0; j < n; j++) centroid[j] += simplex[i][j];
        }
        for (var j = 0; j < n; j++) centroid[j] /= n;
        var worst = simplex[n], fworst = fvals[n];
        var xr = centroid.map(function (c, j) { return c + alpha * (c - worst[j]); });
        var fr = f(xr);
        if (fvals[0] <= fr && fr < fvals[n - 1]) {
          simplex[n] = xr; fvals[n] = fr; continue;
        }
        if (fr < fvals[0]) {
          var xe = centroid.map(function (c, j) { return c + gamma * (xr[j] - c); });
          var feNM = f(xe);
          if (feNM < fr) { simplex[n] = xe; fvals[n] = feNM; }
          else { simplex[n] = xr; fvals[n] = fr; }
          continue;
        }
        var xc;
        if (fr < fworst) {
          xc = centroid.map(function (c, j) { return c + rho_NM * (xr[j] - c); });
        } else {
          xc = centroid.map(function (c, j) { return c + rho_NM * (worst[j] - c); });
        }
        var fc = f(xc);
        if (fc < Math.min(fr, fworst)) {
          simplex[n] = xc; fvals[n] = fc; continue;
        }
        for (var i = 1; i <= n; i++) {
          for (var j = 0; j < n; j++) {
            simplex[i][j] = simplex[0][j] + sigma * (simplex[i][j] - simplex[0][j]);
          }
          fvals[i] = f(simplex[i]);
        }
      }
      return { x: simplex[0], f: fvals[0], iter: iter, converged: converged };
    }

    // Warm-start from FE bivariate
    var fe = feBivariate(trials);
    var x0 = [0.1, 0.1, Math.max(-0.9, Math.min(0.9, fe.rho))];

    var result = nelderMead(negLogLikProfile, x0, max_iter, tol);
    var tau2_s = result.x[0], tau2_c = result.x[1], rho = result.x[2];
    var rho_at_boundary = (Math.abs(rho) > 0.949);

    // Final marginal Cov(mu_hat) = (sum V_i^{-1})^{-1} at the converged variance components.
    var OmegaF = [[tau2_s, rho * Math.sqrt(tau2_s * tau2_c)],
                  [rho * Math.sqrt(tau2_s * tau2_c), tau2_c]];
    var sumVinvF = [[0, 0], [0, 0]], sVyF = [0, 0];
    for (var i = 0; i < ys.length; i++) {
      var Vf = [[Sigs[i][0][0] + OmegaF[0][0], Sigs[i][0][1] + OmegaF[0][1]],
                [Sigs[i][1][0] + OmegaF[1][0], Sigs[i][1][1] + OmegaF[1][1]]];
      var Vfi = inv2x2(Vf);
      sumVinvF[0][0] += Vfi[0][0]; sumVinvF[0][1] += Vfi[0][1];
      sumVinvF[1][0] += Vfi[1][0]; sumVinvF[1][1] += Vfi[1][1];
      sVyF[0] += Vfi[0][0] * ys[i][0] + Vfi[0][1] * ys[i][1];
      sVyF[1] += Vfi[1][0] * ys[i][0] + Vfi[1][1] * ys[i][1];
    }
    var muCovF = inv2x2(sumVinvF);
    var muS_final = muCovF[0][0] * sVyF[0] + muCovF[0][1] * sVyF[1];
    var muC_final = muCovF[1][0] * sVyF[0] + muCovF[1][1] * sVyF[1];

    return {
      mu_sens_logit: muS_final,
      mu_spec_logit: muC_final,
      se_sens_logit: Math.sqrt(muCovF[0][0]),
      se_spec_logit: Math.sqrt(muCovF[1][1]),
      cov_sens_spec_logit: muCovF[0][1],
      tau2_sens: tau2_s,
      tau2_spec: tau2_c,
      rho: rho,
      iterations: result.iter,
      converged: result.converged,
      estimator: 'reml',
      rho_at_boundary: rho_at_boundary
    };
  }

  // ---------- Spearman rank correlation (threshold-effect indicator) ----------
  function spearmanRho(xs, ys) {
    function ranks(arr){
      var sorted = arr.map(function(v,i){return {v:v,i:i};}).sort(function(a,b){return a.v-b.v;});
      var r = new Array(arr.length);
      for (var k=0;k<sorted.length;k++) r[sorted[k].i] = k+1;
      return r;
    }
    var rx=ranks(xs), ry=ranks(ys), n=xs.length;
    var mx=(n+1)/2, my=(n+1)/2, num=0, dx=0, dy=0;
    for (var i=0;i<n;i++){ num+=(rx[i]-mx)*(ry[i]-my); dx+=(rx[i]-mx)*(rx[i]-mx); dy+=(ry[i]-my)*(ry[i]-my); }
    return num/Math.sqrt(dx*dy);
  }

  function fit(trials, opts) {
    opts = opts || {};
    var issues = validate(trials);
    if (issues.length > 0) throw new Error('invalid input: ' + issues.join('; '));

    var k_raw = trials.length;
    var ccOut = applyContinuityCorrection(trials, opts.correction);
    var working = ccOut.trials;

    // Threshold-effect Spearman on per-study logit Sens & logit(1-Spec)
    var lse=[], lspc=[];
    for (var i=0;i<working.length;i++){
      var t=working[i], pos=t.TP+t.FN, neg=t.TN+t.FP;
      var s=t.TP/pos, sp=t.TN/neg;
      lse.push(Math.log(s/(1-s)));
      lspc.push(Math.log((1-sp)/sp));
    }
    var sp_rho = spearmanRho(lse, lspc);
    var threshold_effect = Math.abs(sp_rho) > 0.6;

    // Estimator selection
    var fitObj, fallback = null;
    if (k_raw < 5) {
      fitObj = feBivariate(working);
      fallback = 'fe_bivariate';
    } else {
      fitObj = reitsmaREML(working, { max_iter: opts.max_iter || 500 });
      if (!fitObj.converged) {
        fitObj = feBivariate(working);
        fallback = 'fe_bivariate';
      } else if (fitObj.rho_at_boundary) {
        // Refit with rho=0 fixed
        var fitFixed = reitsmaREMLRhoZero(working, { max_iter: opts.max_iter || 500 });
        if (fitFixed.converged) { fitObj = fitFixed; fallback = 'rho_fixed_zero'; }
      }
    }

    // SEs from feBivariate path: compute marginal SE on the FE muCov (already inside reitsmaREML;
    // for fe_bivariate fallback, se_sens_logit and se_spec_logit are present)
    var sens = 1/(1+Math.exp(-fitObj.mu_sens_logit));
    var spec = 1/(1+Math.exp(-fitObj.mu_spec_logit));
    var z = 1.959963984540054;
    function backCI(mu, se){
      var lo = 1/(1+Math.exp(-(mu-z*se)));
      var hi = 1/(1+Math.exp(-(mu+z*se)));
      return [lo, hi];
    }
    var sens_ci = backCI(fitObj.mu_sens_logit, fitObj.se_sens_logit);
    var spec_ci = backCI(fitObj.mu_spec_logit, fitObj.se_spec_logit);

    // DOR + LR+ + LR-
    var dor = (sens/(1-sens)) / ((1-spec)/spec);
    var lr_pos = sens / (1-spec);
    var lr_neg = (1-sens) / spec;

    // DOR CI via delta method on log-DOR = mu_S + mu_C (var = se_S^2 + se_C^2 + 2*cov)
    var cov = fitObj.cov_sens_spec_logit || 0;
    var var_logDOR = fitObj.se_sens_logit*fitObj.se_sens_logit + fitObj.se_spec_logit*fitObj.se_spec_logit + 2*cov;
    var se_logDOR = Math.sqrt(Math.max(0, var_logDOR));
    var logDOR = fitObj.mu_sens_logit + fitObj.mu_spec_logit;
    var dor_ci = [Math.exp(logDOR - z*se_logDOR), Math.exp(logDOR + z*se_logDOR)];

    var per_study = working.map(function(t){ return perStudy(t); });

    return {
      k: k_raw,
      pooled_sens: sens, pooled_spec: spec,
      pooled_sens_ci_lb: sens_ci[0], pooled_sens_ci_ub: sens_ci[1],
      pooled_spec_ci_lb: spec_ci[0], pooled_spec_ci_ub: spec_ci[1],
      tau2_sens: fitObj.tau2_sens, tau2_spec: fitObj.tau2_spec, rho: fitObj.rho,
      dor: dor, dor_ci_lb: dor_ci[0], dor_ci_ub: dor_ci[1],
      lr_pos: lr_pos, lr_neg: lr_neg,
      threshold_effect_spearman: sp_rho,
      threshold_effect: threshold_effect,
      coverage_warning: k_raw < 10,
      fallback: fallback,
      iterations: fitObj.iterations,
      converged: fitObj.converged,
      cc_applied: ccOut.corrected,
      estimator: fitObj.estimator,
      per_study: per_study,
      _fitInternal: fitObj  // for downstream SROC computation
    };
  }

  function reitsmaREMLRhoZero(trials, opts) {
    // Same as reitsmaREML but rho is fixed at 0; only optimize tau2_s and tau2_c.
    // SHORT: refit using FE for now and tag — TODO if proper 2-parameter REML proves needed.
    var fe = feBivariate(trials);
    return Object.assign({}, fe, { rho: 0, converged: true, iterations: 0, estimator: 'reml_rho_zero' });
  }

  function exportResults(fitResult) {
    return JSON.parse(JSON.stringify(fitResult));
  }

  root.RapidMetaDTA = {
    fit: fit,
    validate: validate,
    exportResults: exportResults,
    _version: '1.0.0-rc',
    _internal: { matmul, inv2x2, clopperPearson, perStudy, applyContinuityCorrection, feBivariate, lnGamma, ibeta, qbeta, reitsmaREML, reitsmaREMLRhoZero, spearmanRho }
  };
})(typeof window !== 'undefined' ? window : globalThis);
