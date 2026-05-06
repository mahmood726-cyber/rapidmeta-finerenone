/* R metafor validation badge — fetches outputs/r_validation/<topic>.json and
 * renders a compact panel showing the local-R-validated pooled estimate.
 *
 * Auto-bootstraps. Topic inferred from filename (FOO_REVIEW.html -> FOO).
 * If JS engine pooled value can be detected on page (window.__POOLED_OR__),
 * also computes |Δ| and shows ✓/⚠ vs R.
 *
 * Container preference: #r-validation-badge, else creates a panel near top.
 *
 * Public API: RValidationBadge.render(topicSlug, container)
 */
(function (global) {
  'use strict';

  function topicFromUrl() {
    if (typeof location === 'undefined') return null;
    const m = location.pathname.match(/\/([^\/]+)_REVIEW\.html?(?:$|[?#])/i);
    if (m) return m[1];
    const m2 = location.pathname.match(/([^\/\\]+?)_REVIEW\.html?$/i);
    return m2 ? m2[1] : null;
  }

  function fmt(v, digits) {
    if (v === null || v === undefined || isNaN(v)) return '—';
    if (typeof digits === 'number') return Number(v).toFixed(digits);
    return Number(v).toPrecision(3);
  }

  function buildPanel(topic, data, jsCompare) {
    const wrap = document.createElement('div');
    wrap.id = 'r-validation-badge';
    wrap.style.cssText = [
      'background:#0f172a',
      'border:1px solid #1e3a5f',
      'border-radius:10px',
      'padding:12px 14px',
      'margin:14px 0',
      'font-family:Inter,system-ui,sans-serif',
      'font-size:12.5px',
      'color:#e2e8f0',
      'box-shadow:0 0 0 1px rgba(59,130,246,0.06)',
    ].join(';');

    const head = document.createElement('div');
    head.style.cssText = 'display:flex;justify-content:space-between;align-items:center;gap:12px;flex-wrap:wrap;';
    head.innerHTML =
      '<div style="display:flex;align-items:center;gap:8px;">' +
        '<span style="background:#1e3a5f;color:#7dd3fc;padding:2px 8px;border-radius:4px;font-size:11px;font-weight:700;letter-spacing:0.04em;">R metafor</span>' +
        '<span style="color:#cbd5e1;font-weight:600;">' + topic + '</span>' +
      '</div>' +
      '<a href="outputs/r_validation/' + topic + '.json" target="_blank" style="color:#7dd3fc;font-size:11px;text-decoration:none;">view raw R JSON ↗</a>';
    wrap.appendChild(head);

    if (data.error) {
      const err = document.createElement('div');
      err.style.cssText = 'margin-top:8px;color:#fbbf24;font-size:11.5px;';
      err.textContent = 'R validation skipped: ' + data.error + ' (k=' + (data.k || '?') + ')';
      wrap.appendChild(err);
      return wrap;
    }

    const grid = document.createElement('div');
    grid.style.cssText = 'display:grid;grid-template-columns:repeat(auto-fit,minmax(140px,1fr));gap:10px;margin-top:10px;';

    function cell(label, value, sub) {
      const c = document.createElement('div');
      c.style.cssText = 'background:#0b1220;border:1px solid #1e293b;border-radius:6px;padding:7px 9px;';
      c.innerHTML =
        '<div style="font-size:10px;color:#64748b;text-transform:uppercase;letter-spacing:0.05em;">' + label + '</div>' +
        '<div style="font-size:14px;color:#f1f5f9;font-weight:700;font-family:JetBrains Mono,monospace;margin-top:2px;">' + value + '</div>' +
        (sub ? '<div style="font-size:10.5px;color:#94a3b8;margin-top:2px;">' + sub + '</div>' : '');
      return c;
    }

    grid.appendChild(cell('Pooled OR',
      fmt(data.pooled_OR, 2),
      '95% CI ' + fmt(data.ci_low_OR, 2) + '–' + fmt(data.ci_high_OR, 2)));
    grid.appendChild(cell('Trials (k)', String(data.k || '?')));
    grid.appendChild(cell('I²', fmt(data.I2, 1) + '%'));
    grid.appendChild(cell('τ²', fmt(data.tau2, 3)));
    grid.appendChild(cell('Q (df ' + (data.Qdf || '?') + ')',
      fmt(data.Q, 2),
      'p=' + fmt(data.Qp, 3)));
    grid.appendChild(cell('PI (95%)',
      fmt(data.PI_low_OR, 2) + '–' + fmt(data.PI_high_OR, 2),
      data.pi_df_convention || 't_{k-1}'));

    wrap.appendChild(grid);

    // Method line + JS comparison
    const meth = document.createElement('div');
    meth.style.cssText = 'margin-top:9px;display:flex;justify-content:space-between;flex-wrap:wrap;gap:8px;font-size:11px;color:#94a3b8;';
    let cmp = '';
    if (jsCompare && jsCompare.pooled_OR && data.pooled_OR) {
      const delta = Math.abs(jsCompare.pooled_OR - data.pooled_OR);
      const pass = delta < 0.01;
      cmp = '<span style="color:' + (pass ? '#34d399' : '#fbbf24') + ';">' +
        (pass ? '✓' : '⚠') + ' JS engine match: |Δ|=' + delta.toFixed(4) + '</span>';
    }
    meth.innerHTML =
      '<span>method: ' + (data.method || '?') +
      (data.hksj_floor_applied ? ' (HKSJ floor applied)' : '') + '</span>' +
      cmp;
    wrap.appendChild(meth);

    return wrap;
  }

  function render(topic, container, jsCompare) {
    const url = 'outputs/r_validation/' + topic + '.json';
    return fetch(url, { cache: 'no-cache' })
      .then(r => {
        if (!r.ok) throw new Error('HTTP ' + r.status);
        return r.json();
      })
      .then(data => {
        const panel = buildPanel(topic, data, jsCompare);
        if (container) {
          container.innerHTML = '';
          container.appendChild(panel);
        }
        return panel;
      })
      .catch(err => {
        console.warn('[r-validation-badge] no JSON for ' + topic, err);
      });
  }

  function autoBootstrap() {
    if (typeof document === 'undefined') return;

    function go() {
      const topic = topicFromUrl();
      if (!topic) return;

      let host = document.getElementById('r-validation-badge');
      if (!host) {
        host = document.createElement('div');
        host.id = 'r-validation-badge';
        // Insert after the first H1 / page-header, else top of body
        const target =
          document.querySelector('header') ||
          document.querySelector('h1') ||
          document.body.firstElementChild;
        if (target && target.parentNode) {
          target.parentNode.insertBefore(host, target.nextSibling);
        } else {
          document.body.insertBefore(host, document.body.firstChild);
        }
      }

      // Try to auto-discover JS engine pooled value if exposed
      const jsCompare = (typeof global.__POOLED_OR__ === 'number')
        ? { pooled_OR: global.__POOLED_OR__ }
        : null;

      render(topic, host, jsCompare);
    }

    if (document.readyState === 'loading') {
      document.addEventListener('DOMContentLoaded', () => setTimeout(go, 300));
    } else {
      setTimeout(go, 300);
    }
  }

  global.RValidationBadge = { render, topicFromUrl };
  autoBootstrap();
})(typeof window !== 'undefined' ? window : this);
