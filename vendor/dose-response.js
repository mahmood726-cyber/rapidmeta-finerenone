/* Dose-response meta-regression panel.
 *
 * For reviews where trial arms encode a numeric dose (e.g. "Empagliflozin
 * 10 mg", "Tofacitinib 5 mg BID", "Avacincaptad 2 mg"), fits a one-stage
 * mixed-effects meta-regression of log-OR on log-dose:
 *
 *   y_i  = β₀ + β₁·log(dose_i) + ε_i,    ε_i ~ N(0, v_i + τ²)
 *
 * Weights: w_i = 1/(v_i + τ²). τ² from intercept-only DerSimonian-Laird.
 *
 * Reports:
 *   - β̂ (dose-response slope on log-OR per log-dose unit)
 *   - SE(β̂), Wald-z, p-value
 *   - Pseudo-R² = 1 − τ²_residual / τ²_total
 *   - Bubble plot SVG (x = log-dose, y = log-OR, bubble area ∝ w_i)
 *
 * Self-skips silently when fewer than 3 trials carry parseable doses.
 *
 * Methodology grounded in:
 *   Greenland & Longnecker. Methods for trend estimation from summarized
 *     dose-response data. Am J Epidemiol 1992;135(11):1301-9.
 *   Crippa A, Orsini N. Multivariate dose-response meta-analysis: the
 *     dosresmeta R package. JSS 2016;72(11):1-15.
 *   Cochrane Handbook v6.5 §10.4.
 *
 * Auto-bootstrap; collapsed by default.
 */
(function (global) {
  'use strict';
  const STORAGE_KEY = 'dose-response-expanded';

  // Match a numeric dose followed by a recognised unit anywhere in the string.
  // Handles: "10 mg", "10mg", "0.5 mg", "200 µg", "200 mcg", "1 g".
  // Returns dose in milligrams (canonical scale).
  function parseDose(text) {
    if (!text) return null;
    const re = /(\d+(?:\.\d+)?)\s*(mg|μg|µg|mcg|g)\b/i;
    const m = text.match(re);
    if (!m) return null;
    let v = parseFloat(m[1]);
    const unit = m[2].toLowerCase();
    if (unit === 'g') v *= 1000;
    else if (unit === 'μg' || unit === 'µg' || unit === 'mcg') v /= 1000;
    return v > 0 ? v : null;
  }

  function trialLogOR(t) {
    let ai = t.ai, ci = t.ci, n1 = t.n1i, n2 = t.n2i;
    if (ai === 0 || ci === 0 || ai === n1 || ci === n2) {
      ai += 0.5; ci += 0.5; n1 += 1; n2 += 1;
    }
    const a = ai, b = n1 - ai, c = ci, d = n2 - ci;
    return { yi: Math.log((a*d)/(b*c)), vi: 1/a + 1/b + 1/c + 1/d };
  }

  function normalCDF(z) {
    const t = 1 / (1 + 0.2316419 * Math.abs(z));
    const d = 0.3989422804 * Math.exp(-z * z / 2);
    let p = d * t * (0.3193815 + t * (-0.3565638 + t * (1.781478 + t * (-1.821256 + t * 1.330274))));
    p = z > 0 ? 1 - p : p;
    return p;
  }

  function metaReg(yi, vi, x) {
    const k = yi.length;
    if (k < 3) return null;
    // Step 1: intercept-only DL τ²
    let W0 = 0, WY0 = 0;
    for (let i = 0; i < k; i++) { const w = 1 / vi[i]; W0 += w; WY0 += w * yi[i]; }
    const yFE = WY0 / W0;
    let Q0 = 0;
    for (let i = 0; i < k; i++) Q0 += (1 / vi[i]) * Math.pow(yi[i] - yFE, 2);
    const sumW2 = vi.reduce((s, v) => s + Math.pow(1/v, 2), 0);
    const c0 = W0 - sumW2 / W0;
    const tau2_total = Math.max(0, (Q0 - (k - 1)) / c0);

    // Step 2: weighted regression on the (μ, dose) plane
    const w = vi.map(v => 1 / (v + tau2_total));
    let Sw = 0, Swx = 0, Swy = 0, Swxx = 0, Swxy = 0;
    for (let i = 0; i < k; i++) {
      Sw += w[i];
      Swx += w[i] * x[i];
      Swy += w[i] * yi[i];
      Swxx += w[i] * x[i] * x[i];
      Swxy += w[i] * x[i] * yi[i];
    }
    const xbar = Swx / Sw, ybar = Swy / Sw;
    const Sxx = Swxx - Sw * xbar * xbar;
    const Sxy = Swxy - Sw * xbar * ybar;
    if (Sxx === 0) return null;
    const beta = Sxy / Sxx;
    const alpha = ybar - beta * xbar;
    const se_beta = Math.sqrt(1 / Sxx);
    const z = beta / se_beta;
    const p = 2 * (1 - normalCDF(Math.abs(z)));

    // Residual τ²
    let rss = 0;
    for (let i = 0; i < k; i++) {
      const fitted = alpha + beta * x[i];
      rss += (1 / vi[i]) * Math.pow(yi[i] - fitted, 2);
    }
    const c_after = Sw - sumW2 / Sw;
    const tau2_resid = Math.max(0, (rss - (k - 2)) / c_after);
    const pseudoR2 = tau2_total > 0 ? Math.max(0, 1 - tau2_resid / tau2_total) : 0;

    return { alpha, beta, se_beta, z, p, k, tau2_total, tau2_resid, pseudoR2,
             xbar, ybar, Sxx, weights: w, xbar_orig: xbar };
  }

  function buildBubble(P, mr, points, baseUnit) {
    const W = 760, H = 320, margin = { l: 60, r: 30, t: 30, b: 50 };
    const innerW = W - margin.l - margin.r, innerH = H - margin.t - margin.b;

    const xs = points.map(p => p.x);
    const ys = points.map(p => p.y);
    const xMin = Math.min(...xs) - 0.2;
    const xMax = Math.max(...xs) + 0.2;
    const yPad = (Math.max(...ys) - Math.min(...ys)) * 0.15 + 0.1;
    const yMin = Math.min(...ys, mr.alpha + mr.beta * xMin) - yPad;
    const yMax = Math.max(...ys, mr.alpha + mr.beta * xMax) + yPad;

    const x = v => margin.l + ((v - xMin) / (xMax - xMin)) * innerW;
    const y = v => margin.t + innerH - ((v - yMin) / (yMax - yMin)) * innerH;

    let svg = '<svg viewBox="0 0 ' + W + ' ' + H + '" width="100%" style="background:#0b1220;border-radius:6px;font-family:Inter,system-ui,sans-serif;">';
    svg += '<line x1="' + margin.l + '" x2="' + (W - margin.r) + '" y1="' + (H - margin.b) + '" y2="' + (H - margin.b) + '" stroke="#475569" />';
    svg += '<line x1="' + margin.l + '" x2="' + margin.l + '" y1="' + margin.t + '" y2="' + (H - margin.b) + '" stroke="#475569" />';

    // Null line at y=0 (log-OR)
    if (yMin < 0 && yMax > 0) {
      const yz = y(0);
      svg += '<line x1="' + margin.l + '" x2="' + (W - margin.r) + '" y1="' + yz + '" y2="' + yz + '" stroke="#475569" stroke-dasharray="3,3" />';
      svg += '<text x="' + (margin.l - 6) + '" y="' + yz + '" fill="#94a3b8" font-size="10" text-anchor="end" dominant-baseline="central">log-OR=0</text>';
    }

    // Regression line
    const x1 = xMin, x2 = xMax;
    const y1 = mr.alpha + mr.beta * x1, y2v = mr.alpha + mr.beta * x2;
    svg += '<line x1="' + x(x1) + '" y1="' + y(y1) + '" x2="' + x(x2) + '" y2="' + y(y2v) + '" stroke="#fbbf24" stroke-width="2" />';

    // Bubbles
    const wMax = Math.max(...mr.weights);
    points.forEach((pt, i) => {
      const r = 3 + 9 * Math.sqrt(mr.weights[i] / wMax);
      svg += '<circle cx="' + x(pt.x) + '" cy="' + y(pt.y) + '" r="' + r + '" fill="#7dd3fc" fill-opacity="0.55" stroke="#0b1220" stroke-width="1"><title>' + pt.name + ' (' + pt.dose + ' ' + baseUnit + '): logOR=' + pt.y.toFixed(3) + '</title></circle>';
    });

    // Axis labels
    svg += '<text x="' + (margin.l + innerW / 2) + '" y="' + (H - margin.b + 36) + '" fill="#cbd5e1" font-size="11" text-anchor="middle">log(dose, ' + baseUnit + ')</text>';
    svg += '<text transform="translate(' + (margin.l - 42) + ',' + (margin.t + innerH / 2) + ') rotate(-90)" fill="#cbd5e1" font-size="11" text-anchor="middle">log-OR</text>';

    // X tick labels: show as actual doses (not logs)
    [xMin, (xMin + xMax) / 2, xMax].forEach(xv => {
      const dose = Math.exp(xv);
      const display = dose < 1 ? dose.toFixed(2) : dose < 10 ? dose.toFixed(1) : dose.toFixed(0);
      svg += '<text x="' + x(xv) + '" y="' + (H - margin.b + 14) + '" fill="#94a3b8" font-size="10" text-anchor="middle">' + display + '</text>';
    });

    // Header
    svg += '<text x="' + margin.l + '" y="' + (margin.t - 8) + '" fill="#cbd5e1" font-size="11" font-weight="600">Dose-response meta-regression</text>';

    svg += '</svg>';
    return svg;
  }

  function buildBody(P, doseTrials, mr, baseUnit) {
    const fmt = P.fmt;
    let html = '';

    // Headline verdict
    const slopePerDoubling = mr.beta * Math.log(2); // log-OR change per doubling of dose
    const orPerDoubling = Math.exp(slopePerDoubling);
    let toneCol, toneBg, toneBorder, verdict;
    if (mr.p < 0.05) {
      toneCol = '#fbbf24'; toneBg = '#3a2a0a'; toneBorder = '#92400e';
      verdict = '⚠ Significant dose-response slope (β̂ = ' + fmt(mr.beta, 3)
              + ' log-OR per log-' + baseUnit + ', p = ' + fmt(mr.p, 3)
              + '). Each doubling of dose changes pooled OR by × ' + fmt(orPerDoubling, 2) + '.';
    } else {
      toneCol = '#34d399'; toneBg = '#0e3a1f'; toneBorder = '#34d399';
      verdict = '✓ No significant dose-response (p = ' + fmt(mr.p, 3) + '). Pseudo-R² = ' + fmt(mr.pseudoR2 * 100, 1) + '%.';
    }
    html += '<div style="background:' + toneBg + ';border:1px solid ' + toneBorder + ';color:' + toneCol + ';padding:8px 10px;border-radius:6px;margin-bottom:10px;font-size:11.5px;">' + verdict + '</div>';

    // Cells
    function cell(label, value, sub) {
      return '<div style="background:#0b1220;border:1px solid #1e293b;border-radius:6px;padding:6px 8px;">'
           + '<div style="font-size:9.5px;color:#64748b;text-transform:uppercase;letter-spacing:0.05em;">' + label + '</div>'
           + '<div style="font-size:13px;color:#f1f5f9;font-weight:700;font-family:JetBrains Mono,monospace;margin-top:2px;">' + value + '</div>'
           + (sub ? '<div style="font-size:10px;color:#94a3b8;margin-top:1px;">' + sub + '</div>' : '')
           + '</div>';
    }
    html += '<div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:8px;margin-bottom:10px;">';
    html += cell('β̂ (slope)', fmt(mr.beta, 3), 'log-OR per log-' + baseUnit);
    html += cell('SE(β̂)', fmt(mr.se_beta, 3));
    html += cell('Wald z', fmt(mr.z, 2), 'p = ' + fmt(mr.p, 3));
    html += cell('Pseudo-R²', fmt(mr.pseudoR2 * 100, 1) + '%', '1 − τ²_resid / τ²_total');
    html += cell('Trials with parsed dose', String(mr.k));
    html += cell('OR per doubling', fmt(orPerDoubling, 2));
    html += '</div>';

    // Bubble plot
    const points = doseTrials.map(t => ({ x: Math.log(t.dose), y: t.yi, name: t.name, dose: t.dose }));
    html += buildBubble(P, mr, points, baseUnit);

    // Per-trial table
    html += '<div style="font-size:11px;color:#94a3b8;margin-top:10px;margin-bottom:4px;">Per-trial parsed doses:</div>';
    html += '<table style="width:100%;font-size:11px;border-collapse:collapse;">';
    html += '<thead><tr style="color:#64748b;text-align:left;">'
          + '<th style="padding:3px 6px;border-bottom:1px solid #1e293b;">Trial</th>'
          + '<th style="padding:3px 6px;border-bottom:1px solid #1e293b;text-align:right;">Dose (' + baseUnit + ')</th>'
          + '<th style="padding:3px 6px;border-bottom:1px solid #1e293b;text-align:right;">log-OR</th>'
          + '<th style="padding:3px 6px;border-bottom:1px solid #1e293b;text-align:right;">OR</th>'
          + '</tr></thead><tbody>';
    doseTrials.forEach(t => {
      html += '<tr style="border-bottom:1px solid #0b1220;">'
            + '<td style="padding:3px 6px;color:#e2e8f0;">' + t.name + '</td>'
            + '<td style="padding:3px 6px;text-align:right;font-family:JetBrains Mono,monospace;color:#cbd5e1;">' + fmt(t.dose, t.dose < 1 ? 2 : (t.dose < 10 ? 1 : 0)) + '</td>'
            + '<td style="padding:3px 6px;text-align:right;font-family:JetBrains Mono,monospace;color:#cbd5e1;">' + fmt(t.yi, 3) + '</td>'
            + '<td style="padding:3px 6px;text-align:right;font-family:JetBrains Mono,monospace;color:#7dd3fc;">' + fmt(Math.exp(t.yi), 2) + '</td>'
            + '</tr>';
    });
    html += '</tbody></table>';

    // Method note
    html += '<div style="font-size:10.5px;color:#64748b;margin-top:8px;line-height:1.5;border-top:1px solid #1e293b;padding-top:8px;">'
          + '<strong>Method:</strong> doses parsed from trial name/group field via regex (mg / µg / g). '
          + 'One-stage mixed-effects meta-regression on log-dose with weights w<sub>i</sub> = 1/(v<sub>i</sub> + τ²); '
          + 'τ² from DerSimonian–Laird intercept-only pool. Pseudo-R² per Raudenbush 2009. '
          + 'Linear log-dose model (Greenland-Longnecker 1992); non-linear / spline models out of scope here. '
          + 'Cochrane Handbook v6.5 §10.4. <strong>Limitations:</strong> requires ≥1 dose per trial parseable from the name; '
          + 'trials at the same dose share regression weight; bubble plot shows trial-level points, not within-trial dose-pairs.'
          + '</div>';

    return html;
  }

  function render() {
    const P = global.PanelHelper;
    if (!P) return false;
    const rd = P.getRealData();
    if (!rd) return false;
    const trials = P.extractBinaryTrials(rd);
    if (trials.length < 3) return false;

    // Map name -> raw realData entry to recover the group / drug-name fields
    const byName = {};
    Object.values(rd).forEach(t => { if (t && t.name) byName[t.name] = t; });

    // Parse a dose for each trial; abandon if too few trials carry one
    const doseTrials = [];
    trials.forEach(t => {
      const raw = byName[t.name] || {};
      const candidate = (t.name || '') + ' ' + (raw.group || '') + ' ' + (raw.snippet || '');
      const dose = parseDose(candidate);
      if (dose == null) return;
      const lo = (function () {
        let ai = t.ai, ci = t.ci, n1 = t.n1i, n2 = t.n2i;
        if (ai === 0 || ci === 0 || ai === n1 || ci === n2) {
          ai += 0.5; ci += 0.5; n1 += 1; n2 += 1;
        }
        const a = ai, b = n1 - ai, c = ci, d = n2 - ci;
        return { yi: Math.log((a*d)/(b*c)), vi: 1/a + 1/b + 1/c + 1/d };
      })();
      doseTrials.push({ name: t.name, dose, yi: lo.yi, vi: lo.vi });
    });

    if (doseTrials.length < 3) return false;
    // Need variation in dose, otherwise regression undefined
    const uniqueDoses = new Set(doseTrials.map(t => t.dose));
    if (uniqueDoses.size < 2) return false;

    const yi = doseTrials.map(t => t.yi);
    const vi = doseTrials.map(t => t.vi);
    const x = doseTrials.map(t => Math.log(t.dose));
    const mr = metaReg(yi, vi, x);
    if (!mr) return false;

    const baseUnit = 'mg';
    const orPerDoubling = Math.exp(mr.beta * Math.log(2));
    const summary = (mr.p < 0.05 ? '⚠ ' : '✓ ')
                  + 'β̂ = ' + P.fmt(mr.beta, 3)
                  + ' (p = ' + P.fmt(mr.p, 3) + ')'
                  + ' · OR × ' + P.fmt(orPerDoubling, 2) + ' per doubling'
                  + ' · k=' + mr.k;

    const panel = P.buildCollapsiblePanel({
      id: 'dose-response-panel',
      badge: 'Dose-response',
      summary,
      bodyHtml: buildBody(P, doseTrials, mr, baseUnit),
      storageKey: STORAGE_KEY,
    });

    const existing = document.getElementById('dose-response-panel');
    if (existing) existing.replaceWith(panel);
    else P.insertAfterRBadge(panel);
    return true;
  }

  function bootstrap() {
    if (typeof document === 'undefined') return;
    let tries = 0;
    const tick = () => {
      if (render()) return;
      if (++tries < 20) setTimeout(tick, 250);
    };
    if (document.readyState === 'loading') {
      document.addEventListener('DOMContentLoaded', () => setTimeout(tick, 1250));
    } else {
      setTimeout(tick, 1250);
    }
  }

  global.DoseResponse = { render };
  bootstrap();
})(typeof window !== 'undefined' ? window : this);
