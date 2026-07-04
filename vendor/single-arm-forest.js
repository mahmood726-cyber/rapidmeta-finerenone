/* Single-arm proportion forest plot — per-trial Wilson 95% CIs with
 * summary diamond on the proportion scale.
 *
 * Companion to single-arm-proportion.js. Renders only when single-arm
 * data is detected by the same picker.
 *
 * Auto-bootstrap; collapsed by default.
 */
(function (global) {
  'use strict';
  const STORAGE_KEY = 'single-arm-forest-expanded';

  function pickSingleArmTrials(rd) {
    if (!rd) return [];
    const out = [];
    Object.values(rd).forEach(t => {
      if (!t) return;
      let e, n;
      const ao = t.allOutcomes;
      if (Array.isArray(ao)) {
        const prop = ao.find(o => o && (o.type === 'PROPORTION' || o.type === 'SINGLE_ARM')
                                     && Number.isFinite(+o.events) && Number.isFinite(+o.n) && +o.n > 0);
        if (prop) { e = +prop.events; n = +prop.n; }
      }
      if (e === undefined && t.singleArm === true && Number.isFinite(+t.events) && Number.isFinite(+t.n) && +t.n > 0) {
        e = +t.events; n = +t.n;
      }
      if (e === undefined && Number.isFinite(+t.events) && Number.isFinite(+t.n) && +t.n > 0
          && (t.cN == null || +t.cN === 0) && (t.cE == null || +t.cE === 0)) {
        e = +t.events; n = +t.n;
      }
      if (e === undefined && Number.isFinite(+t.tE) && Number.isFinite(+t.tN) && +t.tN > 0
          && (t.cN === undefined || t.cN === null || +t.cN === 0)
          && (t.cE === undefined || t.cE === null || +t.cE === 0)) {
        e = +t.tE; n = +t.tN;
      }
      if (e === undefined || n === undefined || e < 0 || n <= 0 || e > n) return;
      out.push({ name: t.name || '?', e, n });
    });
    return out;
  }

  function wilson(x, n) {
    const p = x / n, z = 1.96, denom = 1 + z*z/n;
    const center = (p + z*z/(2*n)) / denom;
    const halfw = z * Math.sqrt(p*(1-p)/n + z*z/(4*n*n)) / denom;
    return { lo: Math.max(0, center - halfw), hi: Math.min(1, center + halfw) };
  }

  // Generalized Q at tau^2 (w_i = 1/(v_i+tau2)); strictly decreasing in tau^2.
  // Shared by the Paule-Mandel solver. Ported from vendor/pairwise-pool.js.
  function genQ(yi, vi, t2) {
    let sw = 0, swy = 0;
    for (let i = 0; i < yi.length; i++) { const w = 1 / (vi[i] + t2); sw += w; swy += w * yi[i]; }
    const mu = swy / sw;
    let F = 0;
    for (let i = 0; i < yi.length; i++) F += (yi[i] - mu) * (yi[i] - mu) / (vi[i] + t2);
    return F;
  }

  // Paule-Mandel tau^2: solve genQ(tau2) = df by bisection (genQ monotone-
  // decreasing, root unique when genQ(0) > df). Robust for small k -- unlike
  // DerSimonian-Laird, which is downward-biased for small k (Veroniki 2016;
  // Cochrane Handbook v6.5). This is the small-k guard: PM stands in for DL at
  // every k, matching the vendor/pairwise-pool.js sibling.
  function tau2PM(yi, vi, df) {
    if (df < 1 || genQ(yi, vi, 0) <= df) return 0;
    let lo = 0, hi = 1, guard = 0;
    while (genQ(yi, vi, hi) > df && guard++ < 200) hi *= 2;
    for (let it = 0; it < 200; it++) {
      const mid = 0.5 * (lo + hi);
      if (genQ(yi, vi, mid) > df) lo = mid; else hi = mid;
      if (hi - lo < 1e-12) break;
    }
    return 0.5 * (lo + hi);
  }

  function logitPool(trials) {
    // Logit-scale random-effects pool. tau^2 by Paule-Mandel (small-k robust),
    // aligning with vendor/pairwise-pool.js. Was DerSimonian-Laird at any k>=2,
    // which is downward-biased for small k and narrows the summary CI.
    const points = trials.map(t => {
      let e = t.e, n = t.n;
      if (e === 0 || e === n) { e += 0.5; n += 1; }
      const p = e / n;
      return { yi: Math.log(p / (1 - p)), vi: 1/e + 1/(n - e) };
    });
    const yiA = points.map(p => p.yi);
    const viA = points.map(p => p.vi);
    const df = points.length - 1;
    // fixed-effect summary (drives Q / I2 display only)
    let W = 0, WY = 0;
    points.forEach(p => { const w = 1/p.vi; W += w; WY += w * p.yi; });
    const yFE = WY / W;
    let Q = 0;
    points.forEach(p => { const w = 1/p.vi; Q += w * Math.pow(p.yi - yFE, 2); });
    const tau2 = tau2PM(yiA, viA, df);
    let W2 = 0, WY2 = 0;
    points.forEach(p => { const w = 1/(p.vi + tau2); W2 += w; WY2 += w * p.yi; });
    const yRE = WY2 / W2;
    const seRE = Math.sqrt(1/W2);
    const I2 = (df > 0 && Q > df) ? Math.max(0, 100 * (Q - df) / Q) : 0;
    return {
      yi: yRE, ci_low: yRE - 1.96*seRE, ci_high: yRE + 1.96*seRE,
      tau2, Q, I2, k: points.length,
    };
  }

  function invLogit(y) { return Math.exp(y) / (1 + Math.exp(y)); }

  function buildForest(trials, summary) {
    const W = 760, rowH = 22, H = 60 + rowH * trials.length + 30;
    const nameCol = 200, axCol = W - nameCol - 30;
    let svg = '<svg viewBox="0 0 ' + W + ' ' + H + '" width="100%" style="background:#0b1220;border-radius:6px;font-family:Inter,system-ui,sans-serif;">';
    // Header
    svg += '<text x="6" y="20" fill="#94a3b8" font-size="10.5" font-weight="600">Trial</text>';
    svg += '<text x="' + (nameCol + axCol/2) + '" y="20" fill="#7dd3fc" font-size="11" text-anchor="middle" font-weight="600">Proportion (95% Wilson)</text>';
    // Tick lines + labels
    [0, 0.25, 0.5, 0.75, 1.0].forEach(p => {
      const xp = nameCol + p * axCol;
      svg += '<line x1="' + xp + '" x2="' + xp + '" y1="32" y2="' + (H - 30) + '" stroke="#1e293b" stroke-dasharray="2,3" />';
      svg += '<text x="' + xp + '" y="' + (H - 14) + '" fill="#94a3b8" font-size="10" text-anchor="middle">' + (p*100).toFixed(0) + '%</text>';
    });

    trials.forEach((t, i) => {
      const y = 40 + rowH * i;
      const p = t.e / t.n;
      const ci = wilson(t.e, t.n);
      svg += '<text x="6" y="' + (y + 4) + '" fill="#cbd5e1" font-size="10.5">' + (t.name || '?').slice(0, 30) + '</text>';
      svg += '<text x="' + (nameCol - 4) + '" y="' + (y + 4) + '" fill="#94a3b8" font-size="9.5" text-anchor="end" font-family="JetBrains Mono,monospace">' + t.e + '/' + t.n + '</text>';
      const xC = nameCol + p * axCol;
      const xL = nameCol + ci.lo * axCol;
      const xH = nameCol + ci.hi * axCol;
      svg += '<line x1="' + xL + '" x2="' + xH + '" y1="' + y + '" y2="' + y + '" stroke="#7dd3fc" stroke-width="1.5" />';
      // Box size proportional to weight (1/SE) — proxy: sqrt(n)
      const boxSz = Math.min(7, Math.max(2.5, Math.sqrt(t.n) / 8));
      svg += '<rect x="' + (xC - boxSz) + '" y="' + (y - boxSz) + '" width="' + (2*boxSz) + '" height="' + (2*boxSz) + '" fill="#7dd3fc" stroke="#0b1220" stroke-width="0.5" />';
    });
    // Summary diamond
    const sumY = 40 + rowH * trials.length + 8;
    const sP = invLogit(summary.yi);
    const sLo = invLogit(summary.ci_low), sHi = invLogit(summary.ci_high);
    const xC = nameCol + sP * axCol, xL = nameCol + sLo * axCol, xH = nameCol + sHi * axCol;
    svg += '<text x="6" y="' + (sumY + 4) + '" fill="#fbbf24" font-size="10.5" font-weight="600">Pooled (PM+RE logit)</text>';
    svg += '<polygon points="' + xL + ',' + sumY + ' ' + xC + ',' + (sumY-6) + ' ' + xH + ',' + sumY + ' ' + xC + ',' + (sumY+6) + '" fill="#fbbf24" stroke="#0b1220" stroke-width="0.5" />';
    svg += '</svg>';
    return svg;
  }

  function render() {
    const P = global.PanelHelper;
    if (!P) return false;
    const rd = P.getRealData();
    if (!rd) return false;
    const trials = pickSingleArmTrials(rd);
    if (trials.length < 2) return false;
    const summary = logitPool(trials);
    if (!summary) return false;
    const sP = invLogit(summary.yi);
    const sLo = invLogit(summary.ci_low), sHi = invLogit(summary.ci_high);
    const summaryStr = 'Pooled ' + P.fmt(sP*100, 1) + '% [' + P.fmt(sLo*100, 1) + '–' + P.fmt(sHi*100, 1) + '%] · k=' + summary.k;
    const svg = buildForest(trials, summary);
    const note = '<div style="font-size:10.5px;color:#64748b;margin-top:8px;line-height:1.5;">'
               + 'Per-trial proportion with Wilson 1927 95% CIs. Summary (gold diamond) is the Paule–Mandel random-effects '
               + 'pool on the logit scale, back-transformed. Box area ∝ √n (weight proxy).'
               + '</div>';
    const panel = P.buildCollapsiblePanel({
      id: 'single-arm-forest-panel', badge: 'Single-arm forest',
      summary: summaryStr, bodyHtml: svg + note, storageKey: STORAGE_KEY,
    });
    const existing = document.getElementById('single-arm-forest-panel');
    if (existing) existing.replaceWith(panel); else P.insertAfterRBadge(panel);
    return true;
  }

  function bootstrap() {
    if (typeof document === 'undefined') return;
    let tries = 0;
    const tick = () => { if (render()) return; if (++tries < 20) setTimeout(tick, 250); };
    if (document.readyState === 'loading') {
      document.addEventListener('DOMContentLoaded', () => setTimeout(tick, 1550));
    } else { setTimeout(tick, 1550); }
  }

  global.SingleArmForest = { render };
  bootstrap();
})(typeof window !== 'undefined' ? window : this);
