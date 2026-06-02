/* RapidMeta — optional R/metafor cross-validation in the browser via WebR.
 *
 * Loaded by each *_REVIEW.html with <script src="webr-validator.js" defer></script>.
 * Zero-cost at page load: no WebR fetch until the user clicks "Validate pool with R".
 * First click triggers ~40 MB WebR WebAssembly download and metafor install (~60-90 s).
 * Result is cached in the browser's service worker / IndexedDB for subsequent clicks.
 *
 * The validator mirrors the app's primary-outcome pool, which is REML + HKSJ:
 *   - For binary (HR/OR/RR) endpoints: log-scale REML + HKSJ via metafor::rma(method="REML", test="knha").
 *   - For continuous (MD) endpoints: native-scale REML + HKSJ on the effect + se.
 *
 * It compares R against the app's NUMERIC pool (window.RapidMeta.state.pooledResult),
 * not a rounded DOM string, and checks both the point estimate and the HKSJ CI,
 * with an EXACT / CLOSE / DIFFER flag. Advisory only — there is no hard gate.
 */

(function () {
  'use strict';

  const WEBR_CDN = 'https://webr.r-wasm.org/latest/webr.mjs';
  const METAFOR_REPO = 'https://repo.r-wasm.org';

  let webR = null;
  let metaforInstalled = false;
  let bootPromise = null;

  const $ = (id) => document.getElementById(id);

  function status(msg) { const el = $('rvalid-status'); if (el) el.textContent = msg; }

  async function ensureWebR() {
    if (webR && metaforInstalled) return webR;
    if (bootPromise) return bootPromise;
    // STATS-4: reset bootPromise on failure so a transient boot error (network
    // blip, CDN 502) does not poison every later click with a cached rejection
    // that can only be cleared by a full page reload.
    bootPromise = (async () => {
      status('Loading WebR WebAssembly (one-time ~40 MB)...');
      let WebRClass;
      try {
        const mod = await import(WEBR_CDN);
        WebRClass = mod.WebR;
      } catch (e) {
        throw new Error('Could not load WebR from ' + WEBR_CDN + ': ' + e.message);
      }
      webR = new WebRClass();
      await webR.init();
      status('Installing metafor (one-time ~60-90 s)...');
      try {
        await webR.evalR(`install.packages("metafor", repos = "${METAFOR_REPO}")`);
        await webR.evalR('suppressPackageStartupMessages(library(metafor))');
      } catch (e) {
        throw new Error('metafor install failed: ' + e.message);
      }
      metaforInstalled = true;
      status('WebR + metafor ready.');
      return webR;
    })();
    bootPromise.catch(() => { bootPromise = null; });
    return bootPromise;
  }

  // STATS-6: read the runtime's ACTUAL outcome shape. The app stores outcomes
  // at `t.data.allOutcomes` with fields { shortLabel, pubHR, pubHR_LCI,
  // pubHR_UCI, estimandType } — NOT `t.allOutcomes` with `effect/lci/uci`
  // (`.effect` does not exist anywhere in the runtime). The previous extractor
  // therefore matched nothing and the cross-validation silently extracted zero
  // rows on every app. We read both shapes defensively and key the field names
  // off whatever is present.
  function outcomesOf(t) {
    return (t && ((t.data && t.data.allOutcomes) || t.allOutcomes)) || [];
  }
  function effOf(ao) { return ao.pubHR != null ? ao.pubHR : ao.effect; }
  function lciOf(ao) { return ao.pubHR_LCI != null ? ao.pubHR_LCI : ao.lci; }
  function uciOf(ao) { return ao.pubHR_UCI != null ? ao.pubHR_UCI : ao.uci; }

  function extractTrialData() {
    const s = window.RapidMeta && window.RapidMeta.state;
    if (!s) return { rows: [], err: 'RapidMeta.state not initialised' };
    const outcomeKey = s.selectedOutcome || 'MACE';
    const included = (s.trials || []).filter(t => {
      const st = (t.screenReview && t.screenReview.status) || t.status ||
                 (t.data && t.data.status);
      return st === 'include';
    });
    const rows = [];
    for (const t of included) {
      const aos = outcomesOf(t);
      const ao = aos.find(o => o.shortLabel === outcomeKey) || aos[0];
      if (!ao) continue;
      const scale = String((ao.estimandType ||
        (t.data && t.data.estimandType) || 'HR')).toUpperCase();
      const eff = effOf(ao), lci = lciOf(ao), uci = uciOf(ao);
      const isContinuous = scale === 'MD' || scale === 'SMD' || scale === 'WMD' ||
        ao.type === 'CONTINUOUS';
      if (isContinuous) {
        // Native-scale effect; SE from the reported CI half-width.
        if (eff != null && lci != null && uci != null && isFinite(eff) && uci > lci) {
          const se = (uci - lci) / (2 * 1.959963984540054);
          if (se > 0) rows.push({ name: t.name, yi: eff, vi: se * se, scale, endpoint_type: 'CONTINUOUS' });
        }
      } else if (eff > 0 && lci > 0 && uci > 0) {
        const yi = Math.log(eff);
        const se = (Math.log(uci) - Math.log(lci)) / (2 * 1.959963984540054);
        if (isFinite(yi) && isFinite(se) && se > 0) {
          rows.push({ name: t.name, yi, vi: se * se, scale, endpoint_type: 'BINARY' });
        }
      }
    }
    return { rows, scale: rows.length ? rows[0].scale : null };
  }

  // Read the app's NUMERIC pooled result (point + HKSJ CI) instead of scraping
  // a rounded DOM string. pooledResult shape:
  //   { [emLabel]: pointEstimate, CI:[lo,hi], HKSJ_CI:[lo,hi], PI:[...], I2:"x%" }
  function appNumericPool() {
    const s = window.RapidMeta && window.RapidMeta.state;
    const pr = s && s.pooledResult;
    if (!pr) return null;
    let point = null;
    for (const [key, val] of Object.entries(pr)) {
      if (key === 'CI' || key === 'HKSJ_CI' || key === 'PI') continue;
      if (typeof val === 'number' && isFinite(val)) { point = val; break; }
    }
    const hksj = Array.isArray(pr.HKSJ_CI) ? pr.HKSJ_CI : null;
    return { point, hksj };
  }

  async function runValidation() {
    const out = $('rvalid-output');
    out.innerHTML = '';
    try {
      const { rows, scale } = extractTrialData();
      if (!rows.length) {
        out.textContent = 'No included trials with usable primary-outcome effect estimates.';
        return;
      }
      if (rows.length < 2) {
        out.textContent = 'Only one included trial; cannot run meta-analysis (k=1).';
        return;
      }
      await ensureWebR();
      status(`Running metafor::rma on k=${rows.length} trials...`);
      const yiLit = 'c(' + rows.map(r => r.yi.toFixed(10)).join(', ') + ')';
      const viLit = 'c(' + rows.map(r => r.vi.toFixed(12)).join(', ') + ')';
      const code = [
        'yi <- ' + yiLit,
        'vi <- ' + viLit,
        // REML + HKSJ to MATCH the app's primary pool (was wrongly "DL").
        'fit <- rma(yi = yi, vi = vi, method = "REML", test = "knha")',
        'c(as.numeric(fit$beta[1,1]), as.numeric(fit$ci.lb), as.numeric(fit$ci.ub),',
        '  as.numeric(fit$tau2), as.numeric(fit$I2), as.numeric(fit$QE), as.numeric(fit$k))'
      ].join('\n');
      const result = await webR.evalR(code);
      const vals = await result.toArray();
      // metafor returns 7 numbers on the log scale for binary, native for continuous
      const [poolRaw, lciRaw, uciRaw, tau2, i2, Q, k] = vals;
      const isLog = scale !== 'MD';
      const toDisp = (x) => isLog ? Math.exp(x) : x;
      const pool = toDisp(poolRaw);
      const lci = toDisp(lciRaw);
      const uci = toDisp(uciRaw);
      // Compare to the app's NUMERIC pool (point + HKSJ CI), with a rounded-DOM
      // fallback only if the numeric pool is unavailable.
      const numeric = appNumericPool();
      let appPool = numeric && numeric.point != null ? numeric.point : NaN;
      const appHksj = numeric && numeric.hksj;
      if (!isFinite(appPool)) {
        const resOr = $('res-or');
        appPool = parseFloat(resOr ? resOr.textContent.trim() : '');
      }
      // metafor's REML on the display scale: point compared after back-transform.
      let agreement;
      if (!isFinite(appPool)) {
        agreement = '<span class="text-amber-400">app pool unavailable for comparison</span>';
      } else {
        const relDiff = Math.abs(pool - appPool) / Math.max(Math.abs(appPool), 1e-9);
        let ciNote = '';
        if (appHksj && appHksj.length === 2 && isFinite(appHksj[0]) && isFinite(appHksj[1])) {
          const ciRel = (Math.abs(lci - appHksj[0]) + Math.abs(uci - appHksj[1])) /
            Math.max(Math.abs(appHksj[0]) + Math.abs(appHksj[1]), 1e-9);
          ciNote = ` &middot; HKSJ CI &Delta;=${(ciRel * 100).toFixed(2)}%`;
        }
        if (relDiff < 0.01) agreement = `<span class="text-emerald-400">&check; EXACT (&lt; 1% rel diff)${ciNote}</span>`;
        else if (relDiff < 0.05) agreement = `<span class="text-amber-400">~ CLOSE (${(relDiff * 100).toFixed(2)}% rel diff)${ciNote}</span>`;
        else agreement = `<span class="text-rose-400">&times; DIFFER (${(relDiff * 100).toFixed(2)}% rel diff)${ciNote}</span>`;
      }
      const fmt = (x) => (x == null || !isFinite(x)) ? '--' : (Math.abs(x) < 0.01 || Math.abs(x) > 999 ? x.toExponential(3) : x.toFixed(3));
      out.innerHTML =
        '<div class="text-emerald-300 font-bold mb-2">metafor::rma output (REML random-effects, HKSJ test)</div>' +
        '<div>Pool: <b>' + fmt(pool) + '</b>  (95% HKSJ CI ' + fmt(lci) + ' to ' + fmt(uci) + ')  [scale: ' + scale + ']</div>' +
        '<div>&tau;&sup2; = ' + fmt(tau2) + '  &middot;  I&sup2; = ' + (isFinite(i2) ? i2.toFixed(1) + '%' : '--') + '  &middot;  Q = ' + fmt(Q) + '  &middot;  k = ' + Math.round(k) + '</div>' +
        '<div class="mt-2">App-computed pool ' + (isFinite(appPool) ? appPool.toFixed(3) : '--') + ' &rarr; ' + agreement + '</div>' +
        '<div class="text-[10px] text-slate-500 mt-3">Source: metafor (Viechtbauer 2010) compiled to WebAssembly via WebR. ' +
        'Independently computed from the app state; no shared code path with the native pool. ' +
        'Advisory cross-check (REML + HKSJ, matching the app primary) — not a hard gate.</div>';
      status('Validation complete (k=' + Math.round(k) + ').');
    } catch (e) {
      out.innerHTML = '<div class="text-rose-400">Error: ' + (e && e.message ? e.message : String(e)) + '</div>';
      status('Validation failed.');
    }
  }

  function injectUI() {
    const host = document.getElementById('tab-analysis');
    if (!host) return;
    if (document.getElementById('rvalid-card')) return;
    const card = document.createElement('div');
    card.id = 'rvalid-card';
    card.className = 'mt-6 p-4 rounded-xl border border-violet-500/30 bg-violet-500/5';
    card.innerHTML =
      '<div class="flex items-start justify-between gap-3 flex-wrap">' +
        '<div>' +
          '<div class="text-[11px] font-bold uppercase tracking-widest text-violet-300"><i class="fa-brands fa-r-project mr-2"></i>R cross-validation (optional &middot; WebR)</div>' +
          '<div class="text-xs text-slate-400 mt-2 max-w-xl">Optional. The first click downloads WebR and installs <code>metafor</code> in the browser ' +
          '(~40 MB WebAssembly + ~60-90 s install). Subsequent validations are instant. ' +
          'Runs <code>metafor::rma(method="REML", test="knha")</code> independently on the current included trials and compares the result to the app\'s native pool.</div>' +
        '</div>' +
        '<button id="rvalid-btn" class="text-[11px] font-bold uppercase tracking-widest px-4 py-2 rounded-full border border-violet-400/40 bg-violet-500/20 hover:bg-violet-500/30 text-violet-200 whitespace-nowrap"><i class="fa-brands fa-r-project mr-2"></i>Validate pool with R</button>' +
      '</div>' +
      '<div id="rvalid-status" class="text-xs text-slate-400 mt-3"></div>' +
      '<div id="rvalid-output" class="text-xs text-slate-200 mt-2 font-mono leading-relaxed"></div>';
    host.appendChild(card);
    document.getElementById('rvalid-btn').addEventListener('click', runValidation);
  }

  function tryInject() {
    injectUI();
    // Fallback: some apps render #tab-analysis lazily. Retry briefly.
    let tries = 0;
    const iv = setInterval(() => {
      injectUI();
      if (document.getElementById('rvalid-card') || ++tries > 20) clearInterval(iv);
    }, 500);
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', tryInject);
  } else {
    tryInject();
  }
})();
