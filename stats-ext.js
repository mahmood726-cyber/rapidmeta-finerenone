/* RapidMeta — REML τ² display (P1-3 fix)
 *
 * The app's native pooler already computes a REML τ² internally (via Fisher
 * scoring on the plotData) but only publishes the DL estimate to the UI.
 * Journal editors prefer REML τ² for small-k pools (Viechtbauer 2005;
 * IntHout 2014) and expect to see both.
 *
 * This shared JS re-computes REML τ² from RapidMeta.state.results.plotData
 * (which has per-trial yi/logOR and vi) and appends a small badge next to the
 * existing DL τ² display, so the reader sees both side-by-side without any
 * change to the app's core pooler.
 */
(function () {
  'use strict';

  function getRM() {
    if (window.RapidMeta) return window.RapidMeta;
    try { return (0, eval)('RapidMeta'); } catch (e) { return null; }
  }

  // Fisher-scoring REML tau^2 estimator (Viechtbauer 2005). Returns 0 on convergence failure.
  function remlTau2(plotData) {
    if (!plotData || plotData.length < 2) return 0;
    // Binary pools have logOR; continuous pools have md. Use whichever is present.
    const yi = plotData.map(d => (d.logOR != null && isFinite(d.logOR)) ? d.logOR : d.md);
    const vi = plotData.map(d => d.vi);
    if (yi.some(v => v == null || !isFinite(v))) return 0;
    if (vi.some(v => v == null || !isFinite(v) || v <= 0)) return 0;
    let tau2 = 0; // start from zero
    for (let it = 0; it < 200; it++) {
      const w = vi.map(v => 1 / (v + tau2));
      const sW = w.reduce((a, b) => a + b, 0);
      const mu = w.reduce((a, wi, i) => a + wi * yi[i], 0) / sW;
      const sW2 = w.reduce((a, wi) => a + wi * wi, 0);
      const sW3 = w.reduce((a, wi) => a + wi * wi * wi, 0);
      const trP = sW - sW2 / sW;
      const yP2y = w.reduce((a, wi, i) => a + wi * wi * Math.pow(yi[i] - mu, 2), 0);
      const trP2 = sW2 - 2 * sW3 / sW + sW2 * sW2 / (sW * sW);
      if (trP2 < 1e-15) break;
      const delta = (yP2y - trP) / trP2;
      const next = Math.max(0, tau2 + delta);
      if (Math.abs(next - tau2) < 1e-10) { tau2 = next; break; }
      tau2 = next;
    }
    return tau2;
  }

  function injectBadge() {
    const rm = getRM();
    const res = rm && rm.state && rm.state.results;
    if (!res || !Array.isArray(res.plotData) || res.plotData.length < 2) return;
    const host = document.getElementById('tab-analysis');
    if (!host) return;
    // Remove and re-add so we always reflect the latest pool.
    const existing = document.getElementById('stats-ext-reml');
    if (existing) existing.remove();
    const reml = remlTau2(res.plotData);
    const dl = typeof res.tau2 === 'number' ? res.tau2 : parseFloat(res.tau2);
    const diff = Math.abs(reml - dl);
    const card = document.createElement('div');
    card.id = 'stats-ext-reml';
    card.className = 'mt-4 p-3 rounded-lg border border-violet-500/30 bg-violet-500/5';
    const ratio = isFinite(dl) && dl > 0 ? '  (REML / DL ratio ' + (reml / dl).toFixed(2) + ')' : '';
    const flag = diff > 0.01
      ? ' <span class="text-amber-300">(notable divergence; REML preferred for small k)</span>'
      : ' <span class="text-emerald-300">(close agreement with DL)</span>';
    card.innerHTML =
      '<div class="text-[10px] font-bold uppercase tracking-widest text-violet-300 mb-2"><i class="fa-solid fa-square-root-variable mr-2"></i>Heterogeneity &tau;&sup2; &mdash; DL and REML</div>'
      + '<div class="text-xs text-slate-200">'
      +   '<span class="font-bold">REML &tau;&sup2; = ' + reml.toFixed(4) + '</span>'
      +   '  <span class="text-slate-500">&middot;  DL &tau;&sup2; = ' + (isFinite(dl) ? dl.toFixed(4) : '--') + ratio + '</span>'
      +   flag
      + '</div>'
      + '<div class="text-[10px] text-slate-500 mt-1 italic">Fisher-scoring REML estimator (Viechtbauer 2005). Editor-preferred for small k; reported alongside DL for transparency.</div>';
    // Place after the effect-measure-toggle card if present, else append to tab.
    const toggle = document.getElementById('effect-measure-toggle');
    if (toggle && toggle.parentNode === host) {
      host.insertBefore(card, toggle.nextSibling);
    } else {
      host.appendChild(card);
    }
  }

  function tryInject() {
    injectBadge();
    let tries = 0;
    const iv = setInterval(function () {
      injectBadge();
      if (document.getElementById('stats-ext-reml') || ++tries > 30) clearInterval(iv);
    }, 600);
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', tryInject);
  } else {
    tryInject();
  }

  // Re-inject when the app re-renders after analysis re-run.
  document.addEventListener('click', function (e) {
    const anchor = e.target.closest && e.target.closest('[onclick*="switchTab"], [data-tab="analysis"], [data-emt-scale]');
    if (anchor) setTimeout(function () {
      const prev = document.getElementById('stats-ext-reml');
      if (prev) prev.remove();
      injectBadge();
    }, 800);
  }, true);
})();
