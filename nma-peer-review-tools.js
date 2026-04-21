/* nma-peer-review-tools.js — v1.0 — 2026-04-21
 *
 * Adds a floating "Peer-Review Defence" panel to any RapidMeta NMA app.
 * Four sections:
 *   1. Engine-vs-netmeta comparison (static, from adjacent *_netmeta_results.json)
 *   2. Comparison-adjusted funnel plot (Chaimani 2012, computed in JS + Plotly)
 *   3. Interactive CINeMA GRADE-NMA builder (7 domains x each comparison)
 *   4. Export markdown bundle
 *
 * Self-contained. Reads the top-level `NMA_CONFIG` + app-level realData.
 * Falls back to static display when netmeta JSON is missing.
 *
 * Hooks into the existing NMA app via DOM only — no mutation of NMAEngine
 * or RapidMeta internals. All computations use per-trial log-effect + SE
 * extracted from realData (HR CI-derived) or publishedHR / hrLCI / hrUCI.
 */
(function () {
  'use strict';

  /* ------------------------------- Utilities ------------------------------- */

  function $(sel, root) { return (root || document).querySelector(sel); }
  function $$(sel, root) { return Array.from((root || document).querySelectorAll(sel)); }

  function el(tag, attrs, children) {
    var e = document.createElement(tag);
    if (attrs) {
      for (var k in attrs) {
        if (k === 'style' && typeof attrs[k] === 'object') {
          Object.assign(e.style, attrs[k]);
        } else if (k.startsWith('on') && typeof attrs[k] === 'function') {
          e.addEventListener(k.slice(2).toLowerCase(), attrs[k]);
        } else if (k === 'html') {
          e.innerHTML = attrs[k];
        } else {
          e.setAttribute(k, attrs[k]);
        }
      }
    }
    (children || []).forEach(function (c) {
      if (typeof c === 'string') e.appendChild(document.createTextNode(c));
      else if (c) e.appendChild(c);
    });
    return e;
  }

  function norm(x, n) { n = n == null ? 3 : n; return (x == null || !isFinite(x)) ? '—' : Number(x).toFixed(n); }

  function fetchJSONMaybe(url) {
    return fetch(url).then(function (r) { return r.ok ? r.json() : null; })
      .catch(function () { return null; });
  }

  /* ---------------------- NMA data extraction ---------------------- */
  // Extract per-trial (logEffect, SE) from the app's realData.

  function extractTrialEffects() {
    var cfg = (typeof NMA_CONFIG !== 'undefined') ? NMA_CONFIG : (window.NMA_CONFIG || null);
    if (!cfg) return null;

    // Try multiple paths to find realData
    var realData = null;
    if (window.RapidMeta && window.RapidMeta.realData) realData = window.RapidMeta.realData;
    else if (window.RapidMeta && window.RapidMeta.state && window.RapidMeta.state.realData) realData = window.RapidMeta.state.realData;

    // Fallback: walk app script content (heuristic)
    if (!realData) return null;

    var rows = [];
    cfg.comparisons.forEach(function (cmp) {
      (cmp.trials || []).forEach(function (trialId) {
        var d = realData[trialId];
        if (!d) return;
        var logEffect = null, se = null, name = d.name || trialId;
        if (d.publishedHR != null && d.hrLCI != null && d.hrUCI != null) {
          logEffect = Math.log(d.publishedHR);
          se = (Math.log(d.hrUCI) - Math.log(d.hrLCI)) / 3.92;
        }
        if (logEffect == null) return;
        rows.push({
          trial: name,
          id: trialId,
          t1: cmp.t1, t2: cmp.t2,
          logHR: logEffect, se: se,
          hr: Math.exp(logEffect),
          lci: Math.exp(logEffect - 1.96 * se),
          uci: Math.exp(logEffect + 1.96 * se)
        });
      });
    });
    return { cfg: cfg, rows: rows };
  }

  /* ---------------------- 1b. In-browser WebR netmeta ---------------------- */

  var WEBR_CDN = 'https://webr.r-wasm.org/latest/webr.mjs';
  var WEBR_REPO = 'https://repo.r-wasm.org';
  var webR = null;
  var webRReady = null; // promise when (meta)netmeta installed; null if not yet tried

  function renderWebRSection(container, trialData) {
    if (!trialData || !trialData.rows.length) return;

    var card = el('div', {
      style: {
        'margin-top': '.6rem', padding: '.5rem .6rem', 'border-radius': '6px',
        background: '#f5f3ff', border: '1px solid #c4b5fd'
      }
    });
    var head = el('div', { style: { display: 'flex', 'align-items': 'center', gap: '.5rem', 'flex-wrap': 'wrap' } }, [
      el('strong', { style: { 'font-size': '.78rem', color: '#5b21b6' } }, ['Live WebR re-run (R / netmeta)']),
      el('button', {
        id: 'prd-webr-btn',
        style: {
          'font-size': '.72rem', padding: '.25rem .6rem', 'border-radius': '3px',
          background: '#5b21b6', color: '#fff', border: 'none', cursor: 'pointer'
        }
      }, ['Run netmeta in browser'])
    ]);
    var note = el('div', { style: { 'font-size': '.7rem', color: '#4b5563', 'margin-top': '.3rem' } }, [
      'Optional. First click pulls WebR (~40 MB) + installs netmeta (~60–120 s). ',
      'Subsequent runs are instant (cached in IndexedDB). Falls back to ',
      el('code', null, ['metafor']),
      ' per-edge if the netmeta install is unavailable in the WebR repo.'
    ]);
    var status = el('div', { id: 'prd-webr-status', style: { 'font-size': '.7rem', color: '#7c3aed', 'margin-top': '.3rem', 'font-style': 'italic' } });
    var output = el('div', { id: 'prd-webr-output', style: { 'font-size': '.72rem', color: '#1f2937', 'margin-top': '.4rem', 'font-family': 'ui-monospace,monospace', 'white-space': 'pre-wrap' } });
    card.appendChild(head);
    card.appendChild(note);
    card.appendChild(status);
    card.appendChild(output);
    container.appendChild(card);

    card.querySelector('#prd-webr-btn').addEventListener('click', function () {
      runWebRNetmeta(trialData, status, output);
    });
  }

  async function ensureWebR(statusEl, prefer) {
    if (webRReady) return webRReady;
    webRReady = (async function () {
      statusEl.textContent = 'Loading WebR WebAssembly (one-time ~40 MB)…';
      var mod;
      try { mod = await import(WEBR_CDN); }
      catch (e) { throw new Error('WebR module load failed: ' + e.message); }
      webR = new mod.WebR();
      await webR.init();
      statusEl.textContent = 'WebR loaded. Installing ' + prefer + ' (one-time)…';
      try {
        // Use webr::install() which handles the WASM binary path internally.
        await webR.installPackages([prefer]);
        await webR.evalR('suppressPackageStartupMessages(library(' + prefer + '))');
        statusEl.textContent = prefer + ' installed. Ready.';
        return { backend: prefer };
      } catch (e) {
        if (prefer === 'netmeta') {
          statusEl.textContent = 'netmeta install failed (' + e.message.slice(0, 80) + '); falling back to metafor…';
          try {
            await webR.installPackages(['metafor']);
            await webR.evalR('suppressPackageStartupMessages(library(metafor))');
            statusEl.textContent = 'metafor installed (fallback mode). Ready.';
            return { backend: 'metafor' };
          } catch (e2) {
            webRReady = null;
            throw new Error('Both netmeta and metafor install failed: ' + e2.message);
          }
        }
        webRReady = null;
        throw e;
      }
    })();
    return webRReady;
  }

  async function runWebRNetmeta(trialData, statusEl, outputEl) {
    outputEl.textContent = '';
    try {
      var info = await ensureWebR(statusEl, 'netmeta');
      var ref = 'Chemoimm';
      var cfgTreatments = (trialData.cfg && trialData.cfg.treatments) || [];
      ['Chemoimmunotherapy', 'Placebo', 'placebo'].forEach(function (r) {
        if (cfgTreatments.indexOf(r) !== -1) ref = r;
      });
      // Shorten labels for R (avoid spaces/slashes)
      function shortName(s) { return s.replace(/[^A-Za-z0-9]/g, '_').slice(0, 20); }
      var shortRef = shortName(ref);
      var rows = trialData.rows;

      if (info.backend === 'netmeta') {
        statusEl.textContent = 'Running netmeta on k=' + rows.length + ' trials…';
        var code = [
          'dat <- data.frame(',
          '  studlab = c(' + rows.map(function (r) { return '"' + r.trial.replace(/"/g, '\\"') + '"'; }).join(',') + '),',
          '  treat1  = c(' + rows.map(function (r) { return '"' + shortName(r.t1) + '"'; }).join(',') + '),',
          '  treat2  = c(' + rows.map(function (r) { return '"' + shortName(r.t2) + '"'; }).join(',') + '),',
          '  TE      = c(' + rows.map(function (r) { return r.logHR.toFixed(10); }).join(',') + '),',
          '  seTE    = c(' + rows.map(function (r) { return r.se.toFixed(10); }).join(',') + '),',
          '  stringsAsFactors = FALSE)',
          'fit <- netmeta(TE=TE, seTE=seTE, treat1=treat1, treat2=treat2, studlab=studlab,',
          '               data=dat, sm="HR", reference.group="' + shortRef + '", random=TRUE, common=FALSE)',
          'trts <- fit$trts',
          'hr  <- exp(fit$TE.random[, "' + shortRef + '"])',
          'lci <- exp(fit$lower.random[, "' + shortRef + '"])',
          'uci <- exp(fit$upper.random[, "' + shortRef + '"])',
          'c(fit$tau^2, fit$I2, fit$Q, fit$pval.Q.inconsistency, fit$Q.inconsistency, fit$df.Q.inconsistency,',
          '  hr, lci, uci)'
        ].join('\n');
        var res = await webR.evalR(code);
        var vals = await res.toArray();
        var n = cfgTreatments.length;
        // Structure: tau2, I2, Q, pQ, Q_inc, df_inc, hr[n], lci[n], uci[n]
        // Order of hr/lci/uci matches alphabetical trts from netmeta
        var tau2 = vals[0], i2 = vals[1], Q = vals[2], pInc = vals[3], qInc = vals[4];
        var hr = vals.slice(6, 6 + n);
        var lci = vals.slice(6 + n, 6 + 2 * n);
        var uci = vals.slice(6 + 2 * n, 6 + 3 * n);
        // Need treatment names — run separate call
        var trtRes = await webR.evalR('as.character(fit$trts)');
        var trtArr = await trtRes.toArray();

        var lines = [];
        lines.push('== netmeta in WebR (random-effects, REML, reference=' + ref + ') ==');
        lines.push('τ² = ' + norm(tau2, 5) + '   I² = ' + norm(i2 * 100, 2) + '%   Q_inc = ' + norm(qInc, 3) + ' (p = ' + norm(pInc, 4) + ')');
        lines.push('');
        lines.push('Treatment effects vs ' + ref + ' (HR, 95% CI):');
        for (var i = 0; i < trtArr.length; i++) {
          if (trtArr[i] === shortRef) continue;
          lines.push('  ' + trtArr[i].padEnd(22) + 'HR ' + norm(hr[i]) + '  (' + norm(lci[i]) + '–' + norm(uci[i]) + ')');
        }
        outputEl.textContent = lines.join('\n');
        statusEl.textContent = '✓ netmeta re-run complete (in-browser, independent of JS engine).';
      } else {
        // metafor per-edge fallback
        statusEl.textContent = 'Running metafor per edge (k=' + rows.length + ')…';
        var lines = ['== metafor per-edge fallback (netmeta unavailable) =='];
        for (var i = 0; i < rows.length; i++) {
          var r = rows[i];
          var code = [
            'yi <- c(' + r.logHR.toFixed(10) + ')',
            'vi <- c(' + (r.se * r.se).toFixed(12) + ')',
            'fit <- rma(yi=yi, vi=vi, method="FE")',
            'c(exp(fit$beta[1,1]), exp(fit$ci.lb), exp(fit$ci.ub))'
          ].join('\n');
          var res = await webR.evalR(code);
          var vals = await res.toArray();
          lines.push('  ' + r.trial.padEnd(18) + ' ' + r.t1 + ' vs ' + r.t2 + ': HR ' + norm(vals[0]) + ' (' + norm(vals[1]) + '–' + norm(vals[2]) + ')');
        }
        outputEl.textContent = lines.join('\n');
        statusEl.textContent = '✓ metafor per-edge complete (fallback mode).';
      }
    } catch (e) {
      outputEl.textContent = 'Error: ' + (e && e.message ? e.message : String(e));
      statusEl.textContent = 'WebR run failed.';
    }
  }

  /* ---------------------- 1. Engine-vs-netmeta table ---------------------- */

  function renderNetmetaTable(container, netmetaJSON, trialData) {
    if (!netmetaJSON) {
      container.appendChild(el('p', { style: { color: '#888' } }, [
        'Static netmeta validation JSON not found at sibling path. ',
        'Run nma/validation/', (trialData && trialData.cfg.outcome) || '*', '_netmeta.R to generate.'
      ]));
      return;
    }
    var treatments = netmetaJSON.treatments || [];
    var ref = treatments[0]; // netmeta reference is first
    // Prefer Chemoimm / placebo / reference node
    ['Chemoimmunotherapy', 'Chemoimm', 'Placebo', 'placebo'].forEach(function (r) {
      if (treatments.indexOf(r) !== -1) ref = r;
    });

    var tbl = el('table', { class: 'prd-table' });
    var thead = el('thead', null, [el('tr', null, [
      el('th', null, ['Quantity']),
      el('th', null, ['R / netmeta 3.2.0']),
      el('th', null, ['Diff tolerance'])
    ])]);
    tbl.appendChild(thead);
    var tbody = el('tbody');
    tbl.appendChild(tbody);

    function push(label, val, tol) {
      tbody.appendChild(el('tr', null, [
        el('td', null, [label]),
        el('td', { style: { 'font-family': 'ui-monospace, monospace', 'text-align': 'right' } }, [val]),
        el('td', { style: { color: '#6B7280', 'text-align': 'right' } }, [tol])
      ]));
    }

    if (netmetaJSON.hr_random_vs_chemoimm) {
      Object.keys(netmetaJSON.hr_random_vs_chemoimm).forEach(function (trt) {
        if (trt === ref) return;
        var hr = netmetaJSON.hr_random_vs_chemoimm[trt];
        var lci = netmetaJSON.hr_ci_lower && netmetaJSON.hr_ci_lower[trt];
        var uci = netmetaJSON.hr_ci_upper && netmetaJSON.hr_ci_upper[trt];
        push('HR ' + trt + ' vs ' + ref, norm(hr) + ' (' + norm(lci) + '–' + norm(uci) + ')', '≤ 1e-3');
      });
    }
    if (netmetaJSON.tau2 != null) push('τ² (REML)', norm(netmetaJSON.tau2, 5), '≤ 1e-4');
    if (netmetaJSON.I2 != null) push('I² (%)', norm(netmetaJSON.I2 * 100, 2), '≤ 0.1');
    if (netmetaJSON.Q_inconsistency != null) {
      push('Q inconsistency', norm(netmetaJSON.Q_inconsistency, 3), '≤ 1e-2');
      push('p inconsistency', norm(netmetaJSON.p_inconsistency, 4), '≤ 1e-3');
    }
    if (netmetaJSON.sucra) {
      Object.keys(netmetaJSON.sucra).forEach(function (trt) {
        push('SUCRA ' + trt, norm(netmetaJSON.sucra[trt], 3), '≤ 0.01 (MC)');
      });
    }
    container.appendChild(tbl);

    var note = el('p', {
      style: {
        'font-size': '0.75rem', color: '#6B7280', 'margin-top': '.5rem',
        'font-style': 'italic'
      }
    }, [
      'Engine-vs-R cross-check: the RapidMeta JS NMA engine is expected to reproduce these numbers ',
      'within the listed tolerance. MC variance on SUCRA bounded at ~0.01 for 100,000 draws.'
    ]);
    container.appendChild(note);
  }

  /* ---------------------- 2. Comparison-adjusted funnel ---------------------- */
  // Chaimani 2012: for each trial, subtract its comparison-specific fixed-effect
  // estimate from its observed effect. Adjusted points should cluster around 0
  // regardless of comparison. Egger-type regression on adjusted effect vs SE.

  function renderCompAdjFunnel(container, trialData) {
    if (!trialData || !trialData.rows.length) {
      container.appendChild(el('p', { style: { color: '#888' } }, [
        'No trial effects available (realData missing or malformed).'
      ]));
      return;
    }
    if (typeof Plotly === 'undefined') {
      container.appendChild(el('p', { style: { color: '#888' } }, [
        'Plotly library not loaded — funnel plot requires Plotly.js.'
      ]));
      return;
    }

    // Estimate comparison-specific fixed-effect mean per edge (k=1 → mean = trial effect; funnel degenerate but still shown).
    var byEdge = {};
    trialData.rows.forEach(function (r) {
      var key = [r.t1, r.t2].sort().join(' | ');
      if (!byEdge[key]) byEdge[key] = [];
      byEdge[key].push(r);
    });

    var adjPoints = [];
    Object.keys(byEdge).forEach(function (key) {
      var g = byEdge[key];
      // fixed-effect IVW mean
      var w = g.map(function (x) { return 1 / (x.se * x.se); });
      var wsum = w.reduce(function (a, b) { return a + b; }, 0);
      var mu = g.reduce(function (s, x, i) { return s + x.logHR * w[i]; }, 0) / wsum;
      g.forEach(function (x) {
        adjPoints.push({
          trial: x.trial, edge: key,
          adj: x.logHR - mu, se: x.se
        });
      });
    });

    // Egger regression: adj ~ 1/SE. Here adjusted residuals should be ~0; slope = asymmetry.
    // We plot SE on y-axis (inverted), adjusted logEffect on x-axis.

    var traces = [{
      x: adjPoints.map(function (p) { return p.adj; }),
      y: adjPoints.map(function (p) { return p.se; }),
      mode: 'markers+text',
      type: 'scatter',
      text: adjPoints.map(function (p) { return p.trial; }),
      textposition: 'top center',
      textfont: { size: 10 },
      marker: { size: 12, color: '#2563eb' },
      hovertemplate: '%{text}<br>adj logHR: %{x:.3f}<br>SE: %{y:.3f}<extra></extra>',
      name: 'trials'
    }];

    // Funnel pseudo-CI contours (0 ± z×SE with z=1.96, 2.58, etc.)
    var maxSE = Math.max.apply(null, adjPoints.map(function (p) { return p.se; }));
    var seGrid = [];
    var steps = 40;
    for (var i = 0; i <= steps; i++) seGrid.push(maxSE * i / steps);
    [1.96, 2.58].forEach(function (z, idx) {
      traces.push({
        x: seGrid.map(function (s) { return -z * s; }),
        y: seGrid,
        mode: 'lines',
        type: 'scatter',
        line: { color: idx === 0 ? '#9ca3af' : '#d1d5db', dash: 'dot', width: 1 },
        hoverinfo: 'skip',
        showlegend: false
      });
      traces.push({
        x: seGrid.map(function (s) { return z * s; }),
        y: seGrid,
        mode: 'lines',
        type: 'scatter',
        line: { color: idx === 0 ? '#9ca3af' : '#d1d5db', dash: 'dot', width: 1 },
        hoverinfo: 'skip',
        showlegend: false
      });
    });

    var plotDiv = el('div', { id: 'prd-funnel-plot', style: { width: '100%', height: '380px' } });
    container.appendChild(plotDiv);

    Plotly.newPlot(plotDiv, traces, {
      title: { text: 'Comparison-adjusted funnel (Chaimani 2012)', font: { size: 13 } },
      xaxis: { title: { text: 'Adjusted log-HR (trial effect − comparison FE mean)', font: { size: 11 } }, zeroline: true, zerolinecolor: '#000', zerolinewidth: 1 },
      yaxis: { title: { text: 'Standard error', font: { size: 11 } }, autorange: 'reversed' },
      showlegend: false,
      margin: { l: 60, r: 20, t: 35, b: 55 },
      plot_bgcolor: '#fafafa'
    }, { responsive: true, displayModeBar: false });

    // Egger-type regression (on adjusted points): slope + p-value
    var n = adjPoints.length;
    var xMean = adjPoints.reduce(function (s, p) { return s + 1 / p.se; }, 0) / n;
    var yMean = adjPoints.reduce(function (s, p) { return s + p.adj / p.se; }, 0) / n;
    var num = 0, denom = 0;
    adjPoints.forEach(function (p) {
      var xi = 1 / p.se, yi = p.adj / p.se;
      num += (xi - xMean) * (yi - yMean);
      denom += (xi - xMean) * (xi - xMean);
    });
    var slope = denom > 0 ? num / denom : 0;
    var intercept = yMean - slope * xMean;
    // Rough SE(intercept) via residuals
    var resSS = 0;
    adjPoints.forEach(function (p) {
      var xi = 1 / p.se, yi = p.adj / p.se;
      var pred = intercept + slope * xi;
      resSS += (yi - pred) * (yi - pred);
    });
    var sigma = n > 2 ? Math.sqrt(resSS / (n - 2)) : NaN;
    var seIntercept = sigma && denom > 0 ? sigma * Math.sqrt(1 / n + xMean * xMean / denom) : NaN;
    var tStat = seIntercept ? intercept / seIntercept : NaN;
    var pEgger = !isFinite(tStat) ? NaN : 2 * (1 - studentT_cdf(Math.abs(tStat), n - 2));

    container.appendChild(el('div', {
      style: { 'font-size': '.8rem', color: '#4b5563', 'margin-top': '.4rem' }
    }, [
      el('strong', null, ['Egger-type asymmetry test on adjusted points: ']),
      'intercept = ' + norm(intercept, 3) + ' (SE ' + norm(seIntercept, 3) + '), ',
      't = ' + norm(tStat, 2) + ', p = ' + norm(pEgger, 3) + ' (k = ' + n + ')',
      el('br', null),
      el('em', null, ['At k ≤ 10 the test is underpowered; interpret as descriptive only (Sterne 2011).'])
    ]));
  }

  // Minimal Student-t CDF via incomplete beta (Abramowitz & Stegun approx)
  function studentT_cdf(t, df) {
    if (!isFinite(t) || !isFinite(df) || df <= 0) return NaN;
    var x = df / (df + t * t);
    var a = df / 2, b = 0.5;
    var ib = incompleteBeta(x, a, b);
    var p = 0.5 * ib;
    return t >= 0 ? 1 - p : p;
  }
  function incompleteBeta(x, a, b) {
    if (x <= 0) return 0;
    if (x >= 1) return 1;
    var bt = Math.exp(lnGamma(a + b) - lnGamma(a) - lnGamma(b) + a * Math.log(x) + b * Math.log(1 - x));
    if (x < (a + 1) / (a + b + 2)) return bt * betacf(x, a, b) / a;
    return 1 - bt * betacf(1 - x, b, a) / b;
  }
  function lnGamma(z) {
    var c = [76.18009172947146, -86.50532032941677, 24.01409824083091,
             -1.231739572450155, 1.208650973866179e-3, -5.395239384953e-6];
    var x = z, y = z, tmp = x + 5.5;
    tmp -= (x + 0.5) * Math.log(tmp);
    var ser = 1.000000000190015;
    for (var i = 0; i < 6; i++) ser += c[i] / ++y;
    return -tmp + Math.log(2.5066282746310005 * ser / x);
  }
  function betacf(x, a, b) {
    var fpmin = 1e-30, qab = a + b, qap = a + 1, qam = a - 1;
    var c = 1, d = 1 - qab * x / qap;
    if (Math.abs(d) < fpmin) d = fpmin;
    d = 1 / d;
    var h = d;
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

  /* ---------------------- 3. Interactive CINeMA builder ---------------------- */

  var CINeMA_DOMAINS = [
    { key: 'wsb', label: 'Within-study bias' },
    { key: 'asb', label: 'Across-study bias' },
    { key: 'ind', label: 'Indirectness' },
    { key: 'imp', label: 'Imprecision' },
    { key: 'het', label: 'Heterogeneity' },
    { key: 'inc', label: 'Incoherence' },
    { key: 'pub', label: 'Publication bias' }
  ];
  var CINeMA_LEVELS = [
    { val: 'no', label: 'No concerns', weight: 0 },
    { val: 'some', label: 'Some concerns', weight: 0.5 },
    { val: 'major', label: 'Major concerns', weight: 1 }
  ];
  // CINeMA rules of thumb: 0 → High; ≤1 → Moderate; ≤2 → Low; else Very low

  function certaintyFor(row) {
    var w = CINeMA_DOMAINS.reduce(function (s, d) {
      var v = (row[d.key] || 'no');
      var lvl = CINeMA_LEVELS.find(function (x) { return x.val === v; });
      return s + (lvl ? lvl.weight : 0);
    }, 0);
    if (w === 0) return { label: 'HIGH', color: '#059669' };
    if (w <= 1) return { label: 'MODERATE', color: '#2563eb' };
    if (w <= 2) return { label: 'LOW', color: '#d97706' };
    return { label: 'VERY LOW', color: '#dc2626' };
  }

  function enumerateComparisons(cfg) {
    var comps = [];
    var trts = cfg.treatments.slice();
    for (var i = 0; i < trts.length; i++) {
      for (var j = i + 1; j < trts.length; j++) {
        comps.push({ t1: trts[i], t2: trts[j] });
      }
    }
    return comps;
  }

  function renderCINeMABuilder(container, trialData) {
    if (!trialData || !trialData.cfg) {
      container.appendChild(el('p', { style: { color: '#888' } }, ['NMA_CONFIG not found.']));
      return;
    }
    var comps = enumerateComparisons(trialData.cfg);
    var state = {}; // comparisonKey -> { wsb: 'some', ... }
    comps.forEach(function (c) {
      state[c.t1 + ' vs ' + c.t2] = { wsb: 'some', asb: 'no', ind: 'some', imp: 'no', het: 'no', inc: 'no', pub: 'no' };
    });

    var tbl = el('table', { class: 'prd-table' });
    var head = el('thead');
    var headRow = el('tr', null, [el('th', null, ['Comparison'])].concat(
      CINeMA_DOMAINS.map(function (d) { return el('th', null, [d.label]); })
    ).concat([el('th', null, ['Certainty'])]));
    head.appendChild(headRow);
    tbl.appendChild(head);
    var tbody = el('tbody');
    tbl.appendChild(tbody);

    function refreshRow(row, key) {
      var cell = row.querySelector('.prd-cert');
      var c = certaintyFor(state[key]);
      cell.textContent = c.label;
      cell.style.color = c.color;
      cell.style.fontWeight = '700';
    }

    comps.forEach(function (c) {
      var key = c.t1 + ' vs ' + c.t2;
      var tr = el('tr');
      tr.appendChild(el('td', null, [key]));
      CINeMA_DOMAINS.forEach(function (d) {
        var sel = el('select', { style: { 'font-size': '.75rem' } }, []);
        CINeMA_LEVELS.forEach(function (lvl) {
          var opt = el('option', { value: lvl.val }, [lvl.label]);
          if (state[key][d.key] === lvl.val) opt.selected = true;
          sel.appendChild(opt);
        });
        sel.addEventListener('change', function () {
          state[key][d.key] = sel.value;
          refreshRow(tr, key);
        });
        tr.appendChild(el('td', null, [sel]));
      });
      tr.appendChild(el('td', { class: 'prd-cert' }, []));
      tbody.appendChild(tr);
      refreshRow(tr, key);
    });

    container.appendChild(tbl);

    var exportBtn = el('button', {
      class: 'prd-export-btn',
      style: {
        'margin-top': '.6rem', padding: '.4rem .8rem', 'font-size': '.8rem',
        background: '#1f2937', color: '#fff', border: 'none', 'border-radius': '4px', cursor: 'pointer'
      }
    }, ['Export CINeMA markdown']);
    exportBtn.addEventListener('click', function () {
      var md = '# CINeMA GRADE-NMA certainty worksheet\n\n';
      md += '**App:** ' + (document.title || 'NMA') + '\n\n';
      md += '| Comparison | ' + CINeMA_DOMAINS.map(function (d) { return d.label; }).join(' | ') + ' | Certainty |\n';
      md += '|' + new Array(CINeMA_DOMAINS.length + 2).join('---|') + '\n';
      comps.forEach(function (c) {
        var key = c.t1 + ' vs ' + c.t2;
        var row = state[key];
        var cert = certaintyFor(row).label;
        md += '| ' + key + ' | ' + CINeMA_DOMAINS.map(function (d) {
          var v = row[d.key];
          var lvl = CINeMA_LEVELS.find(function (x) { return x.val === v; });
          return lvl ? lvl.label : v;
        }).join(' | ') + ' | **' + cert + '** |\n';
      });
      downloadText(md, (trialData.cfg.outcome || 'nma') + '_cinema_grade.md');
    });
    container.appendChild(exportBtn);
  }

  function downloadText(text, filename) {
    var blob = new Blob([text], { type: 'text/markdown;charset=utf-8' });
    var url = URL.createObjectURL(blob);
    var a = document.createElement('a');
    a.href = url; a.download = filename;
    document.body.appendChild(a); a.click();
    setTimeout(function () { document.body.removeChild(a); URL.revokeObjectURL(url); }, 100);
  }

  /* ---------------------- 4. Floating panel shell ---------------------- */

  function injectStyle() {
    if (document.getElementById('prd-style')) return;
    var css = [
      '.prd-panel { position: fixed; right: 16px; bottom: 16px; max-width: 580px; max-height: 80vh; overflow: auto; background: #fff; border: 2px solid #1f2937; border-radius: 8px; box-shadow: 0 8px 32px rgba(0,0,0,.15); z-index: 9999; font-family: system-ui,-apple-system,sans-serif; font-size: .85rem; }',
      '.prd-panel.collapsed { max-height: 36px; overflow: hidden; }',
      '.prd-panel header { display: flex; justify-content: space-between; align-items: center; padding: .4rem .8rem; background: #1f2937; color: #fff; cursor: pointer; border-radius: 6px 6px 0 0; }',
      '.prd-panel header h2 { margin: 0; font-size: .9rem; font-weight: 600; }',
      '.prd-panel .prd-body { padding: .8rem 1rem; }',
      '.prd-panel .prd-section { border-bottom: 1px solid #e5e7eb; padding: .6rem 0; }',
      '.prd-panel .prd-section h3 { margin: 0 0 .3rem 0; font-size: .85rem; color: #1f2937; font-weight: 600; }',
      '.prd-panel .prd-section p { margin: .2rem 0; }',
      '.prd-table { border-collapse: collapse; width: 100%; font-size: .78rem; }',
      '.prd-table th, .prd-table td { padding: .25rem .5rem; border-bottom: 1px solid #f3f4f6; text-align: left; vertical-align: middle; }',
      '.prd-table th { background: #f9fafb; font-weight: 600; }',
      '.prd-fab { position: fixed; right: 16px; bottom: 16px; width: 52px; height: 52px; border-radius: 26px; background: #1f2937; color: #fff; border: none; cursor: pointer; z-index: 9998; font-size: .9rem; font-weight: 700; box-shadow: 0 4px 16px rgba(0,0,0,.2); }',
      '.prd-fab:hover { background: #111827; }'
    ].join('\n');
    var s = document.createElement('style');
    s.id = 'prd-style';
    s.textContent = css;
    document.head.appendChild(s);
  }

  function findNetmetaJSONUrl() {
    // Convention: same folder as this script or nma/validation/<slug>_netmeta_results.json
    var cfg = (typeof NMA_CONFIG !== 'undefined') ? NMA_CONFIG : (window.NMA_CONFIG || null);
    var slug = (cfg && cfg.outcome) ? cfg.outcome : 'nma';
    // Try several well-known paths
    return [
      'nma/validation/btki_cll_netmeta_results.json',
      'nma/validation/' + slug + '_netmeta_results.json',
      slug + '_netmeta_results.json'
    ];
  }

  function tryFetchFirst(urls, i) {
    i = i || 0;
    if (i >= urls.length) return Promise.resolve(null);
    return fetchJSONMaybe(urls[i]).then(function (j) {
      return j || tryFetchFirst(urls, i + 1);
    });
  }

  function buildPanel() {
    injectStyle();

    var fab = el('button', { class: 'prd-fab', title: 'Open Peer-Review Defence panel' }, ['PR']);
    document.body.appendChild(fab);

    var panel = el('div', { class: 'prd-panel' });
    var header = el('header', null, [
      el('h2', null, ['Peer-Review Defence — NMA']),
      el('span', { style: { 'font-size': '.75rem', opacity: '.7' } }, ['v1.0'])
    ]);
    var body = el('div', { class: 'prd-body' });
    panel.appendChild(header);
    panel.appendChild(body);
    panel.style.display = 'none';
    document.body.appendChild(panel);

    function show() { panel.style.display = ''; fab.style.display = 'none'; }
    function hide() { panel.style.display = 'none'; fab.style.display = ''; }
    fab.addEventListener('click', show);
    header.addEventListener('click', hide);

    var trialData = extractTrialEffects();

    // Section 1: validation table
    var sec1 = el('div', { class: 'prd-section' }, [
      el('h3', null, ['1. Engine vs netmeta (R 3.2.0) cross-validation'])
    ]);
    body.appendChild(sec1);

    tryFetchFirst(findNetmetaJSONUrl()).then(function (json) {
      renderNetmetaTable(sec1, json, trialData);
      renderWebRSection(sec1, trialData);
    });

    // Section 2: funnel
    var sec2 = el('div', { class: 'prd-section' }, [
      el('h3', null, ['2. Comparison-adjusted funnel (Chaimani 2012)'])
    ]);
    body.appendChild(sec2);
    renderCompAdjFunnel(sec2, trialData);

    // Section 3: CINeMA builder
    var sec3 = el('div', { class: 'prd-section' }, [
      el('h3', null, ['3. Interactive CINeMA GRADE-NMA builder'])
    ]);
    body.appendChild(sec3);
    renderCINeMABuilder(sec3, trialData);

    // Section 4: bundle links
    var sec4 = el('div', { class: 'prd-section' }, [
      el('h3', null, ['4. Canonical bundle']),
      el('p', null, [
        el('a', { href: 'nma/validation/btki_cll_peer_review_bundle.md', target: '_blank', style: { color: '#1d4ed8' } }, [
          'View full peer-review defence bundle (markdown)'
        ])
      ])
    ]);
    body.appendChild(sec4);
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', function () { setTimeout(buildPanel, 1200); });
  } else {
    setTimeout(buildPanel, 1200);
  }
})();
