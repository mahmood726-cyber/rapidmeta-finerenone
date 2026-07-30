/* prisma-flow.js — PRISMA-NMA flow diagram (Page 2021 BMJ standard).
 *
 * Reads RapidMeta.state.trials and renders a 5-box flow:
 *   Records identified through database searching (k_total)
 *   ↓
 *   Records after duplicates removed (k_search)
 *   ↓
 *   Records screened (k_screened) → Records excluded (k_excluded)
 *   ↓
 *   Full-text articles assessed (k_fulltext) → Excluded with reasons
 *   ↓
 *   Studies included in qualitative synthesis (k_included)
 *   ↓
 *   Studies included in quantitative synthesis / NMA (k_quantitative)
 *
 * Reads counts from state.trials by status:
 *   status='search'   → records identified
 *   status='exclude'  → excluded at screening
 *   status='include'  → included
 *   data.extractionSignoff.confirmed → in extraction set
 * Plus realData entries → in NMA quantitative set.
 *
 * Public API (window.PrismaFlow):
 *   compute() → counts
 *   render(container)
 */
(function (global) {
  'use strict';

  function compute() {
    const state = (global.RapidMeta && global.RapidMeta.state) || {};
    const trials = Array.isArray(state.trials) ? state.trials : [];
    const rd = (global.RapidMeta && global.RapidMeta.realData) || {};

    // `hydrated` is the honest gate. This module used to render before
    // RapidMeta.state.trials was populated and report 0 for every upstream
    // stage -- which is a false claim (zero records found), not an empty one.
    const hydrated = trials.length > 0;

    const counts = {
      hydrated: hydrated,
      // duplicates were never tracked as a separate stage in this app; the
      // search log records only a post-dedup total. null renders "not recorded".
      duplicates_removed: null,
      in_nma: Object.keys(rd).length,
      reasons: {},
    };

    if (!hydrated) {
      // Nothing about the search/screening audit trail is known yet. Report
      // that, rather than inventing zeros or back-filling from realData.
      counts.total_search = null;
      counts.screened = null;
      counts.excluded_screen = null;
      counts.unscreened = null;
      counts.fulltext = null;
      counts.excluded_fulltext = null;
      counts.included_qualitative = null;
      counts.included_not_in_nma = null;
      return counts;
    }

    counts.total_search = trials.length;
    counts.screened = 0;
    counts.excluded_screen = 0;
    counts.fulltext = 0;
    counts.excluded_fulltext = 0;
    counts.included_qualitative = 0;

    trials.forEach(t => {
      const status = (t && t.status) || '';
      const sr = (t && t.screenReview) || {};
      const ex = (t && t.data && t.data.extractionSignoff) || {};
      if (sr.decision || status === 'include' || status === 'exclude') {
        counts.screened++;
      }
      if (status === 'exclude' || sr.decision === 'exclude') {
        counts.excluded_screen++;
        const reason = (t.exclusionReason || sr.reason || 'unspecified').slice(0, 60);
        counts.reasons[reason] = (counts.reasons[reason] || 0) + 1;
      }
      if (status === 'include' || sr.decision === 'include') {
        counts.fulltext++;
        if (ex.confirmed || (t.data && Object.keys(t.data).length > 2)) {
          counts.included_qualitative++;
        } else {
          counts.excluded_fulltext++;
        }
      }
    });

    // Records that reached no screening decision at all. Previously invisible:
    // identified minus screened simply vanished from the diagram.
    // decision_recorded = reached an include/exclude decision.
    // screened (PRISMA 2020) = entered screening = every identified record.
    counts.decision_recorded = counts.screened;
    counts.unscreened = counts.total_search - counts.decision_recorded;
    counts.screened = counts.total_search;
    // Studies included qualitatively but absent from the fitted network.
    counts.included_not_in_nma = counts.included_qualitative - counts.in_nma;
    return counts;
  }

  function box(svgNS, x, y, w, h, label, count, fill) {
    const g = document.createElementNS(svgNS, 'g');
    const rect = document.createElementNS(svgNS, 'rect');
    rect.setAttribute('x', x);
    rect.setAttribute('y', y);
    rect.setAttribute('width', w);
    rect.setAttribute('height', h);
    rect.setAttribute('rx', '6');
    rect.setAttribute('fill', fill || '#1e293b');
    rect.setAttribute('stroke', '#475569');
    rect.setAttribute('stroke-width', '1');
    g.appendChild(rect);
    const t1 = document.createElementNS(svgNS, 'text');
    t1.setAttribute('x', x + w / 2);
    t1.setAttribute('y', y + 22);
    t1.setAttribute('fill', '#cbd5e1');
    t1.setAttribute('font-size', '11');
    t1.setAttribute('text-anchor', 'middle');
    t1.textContent = label;
    g.appendChild(t1);
    const t2 = document.createElementNS(svgNS, 'text');
    t2.setAttribute('x', x + w / 2);
    t2.setAttribute('y', y + 42);
    t2.setAttribute('fill', '#22d3ee');
    t2.setAttribute('font-size', '16');
    t2.setAttribute('font-weight', '700');
    t2.setAttribute('text-anchor', 'middle');
    // A null count means the stage was never recorded. Rendering it as 0 would
    // assert that zero records were found, which is a different -- and false -- claim.
    if (count === null || count === undefined) {
      t2.textContent = 'not recorded';
      t2.setAttribute('font-size', '13');
      t2.setAttribute('fill', '#fbbf24');
    } else {
      t2.textContent = 'k = ' + count;
    }
    g.appendChild(t2);
    return g;
  }

  function arrow(svgNS, x1, y1, x2, y2) {
    const line = document.createElementNS(svgNS, 'line');
    line.setAttribute('x1', x1);
    line.setAttribute('y1', y1);
    line.setAttribute('x2', x2);
    line.setAttribute('y2', y2);
    line.setAttribute('stroke', '#64748b');
    line.setAttribute('stroke-width', '1.5');
    line.setAttribute('marker-end', 'url(#arrowhead)');
    return line;
  }

  function render(container) {
    if (typeof container === 'string') {
      container = container.charAt(0) === '#'
        ? document.getElementById(container.slice(1))
        : document.getElementById(container) || document.querySelector(container);
    }
    if (!container) return;
    const c = compute();
    const W = 1000;
    const H = 470;
    const svgNS = 'http://www.w3.org/2000/svg';
    const svg = document.createElementNS(svgNS, 'svg');
    svg.setAttribute('viewBox', '0 0 ' + W + ' ' + H);
    svg.setAttribute('width', '100%');
    svg.setAttribute('style', 'background:transparent;font-family:ui-sans-serif,system-ui,sans-serif;');

    // Marker def
    const defs = document.createElementNS(svgNS, 'defs');
    const m = document.createElementNS(svgNS, 'marker');
    m.setAttribute('id', 'arrowhead');
    m.setAttribute('markerWidth', '10');
    m.setAttribute('markerHeight', '10');
    m.setAttribute('refX', '9');
    m.setAttribute('refY', '3');
    m.setAttribute('orient', 'auto');
    const mp = document.createElementNS(svgNS, 'polygon');
    mp.setAttribute('points', '0 0, 10 3, 0 6');
    mp.setAttribute('fill', '#64748b');
    m.appendChild(mp);
    defs.appendChild(m);
    svg.appendChild(defs);

    // 5 boxes vertical, with side branches for "excluded"
    const boxW = 280, boxH = 56;
    const cx = W / 2;
    const xs = [
      [cx - boxW / 2, 20, 'Records identified (search)', c.total_search, '#1e3a8a'],
      [cx - boxW / 2, 100, 'Records screened', c.screened, '#1e3a8a'],
      [cx - boxW / 2, 200, 'Full-text assessed', c.fulltext, '#1e3a8a'],
      [cx - boxW / 2, 300, 'Included (qualitative)', c.included_qualitative, '#065f46'],
      [cx - boxW / 2, 380, 'In quantitative synthesis (MA / NMA)', c.in_nma, '#0e7490'],
    ];
    xs.forEach(b => svg.appendChild(box(svgNS, b[0], b[1], boxW, boxH, b[2], b[3], b[4])));

    // Side excluded boxes
    svg.appendChild(box(svgNS, cx + 170, 100, 200, boxH,
      'Excluded at screening', c.excluded_screen, '#7f1d1d'));
    svg.appendChild(box(svgNS, cx + 170, 200, 200, boxH,
      'Excluded after full-text', c.excluded_fulltext, '#7f1d1d'));
    // Left arm: records with no recorded screening decision. Without this box,
    // screened minus (excluded + to-full-text) silently vanished from the flow.
    svg.appendChild(box(svgNS, 40, 100, 200, boxH,
      'Screening decision not recorded', c.unscreened, '#78350f'));

    // Arrows
    [
      [cx, 76, cx, 100],
      [cx, 156, cx, 200],
      [cx, 256, cx, 300],
      [cx, 356, cx, 380],
      [cx + 140, 128, cx + 170, 128],
      [cx + 140, 228, cx + 170, 228],
      [cx - 140, 128, 245, 128],
    ].forEach(a => svg.appendChild(arrow(svgNS, a[0], a[1], a[2], a[3])));

    container.innerHTML = '';
    container.appendChild(svg);

    // Caption + explicit reconciliation of every gap in the flow.
    const cap = document.createElement('div');
    cap.style.cssText = 'font-size:10.5px;color:#94a3b8;margin-top:10px;line-height:1.6;';
    let notes = '';
    if (!c.hydrated) {
      notes += '<div style="color:#fbbf24;margin-bottom:6px;"><strong>The search-and-screening audit trail is '
            +  'not available.</strong> Only the final included set is documented. The upstream stages read '
            +  '"not recorded" rather than 0, because 0 would assert that no records were found.</div>';
    } else {
      const bits = [];
      if (c.unscreened > 0) {
        bits.push('<strong>' + c.unscreened + ' screened records have no recorded screening decision</strong> '
          + '(status still "search"). They are shown on the left arm, not absorbed into the exclusions: '
          + c.screened + ' screened = ' + c.excluded_screen + ' excluded + ' + c.fulltext
          + ' to full text + ' + c.unscreened + ' not recorded.');
      }
      if (c.included_not_in_nma > 0) {
        bits.push('<strong>' + c.included_not_in_nma + ' study included qualitatively is not in the fitted '
          + 'network</strong> (' + c.included_qualitative + ' included vs ' + c.in_nma + ' in the NMA). '
          + 'The reason is not recorded in this app.');
      } else if (c.included_not_in_nma < 0) {
        bits.push('<strong>' + (-c.included_not_in_nma) + ' study in the network is not counted as included '
          + 'qualitatively</strong> (' + c.included_qualitative + ' included vs ' + c.in_nma + ' in the NMA).');
      }
      bits.push('<strong>Duplicate removal is not recorded.</strong> The search log stores only a post-dedup '
        + 'total, so no de-duplication stage can be shown; it is left blank rather than reported as 0.');
      if (bits.length) {
        notes += '<div style="background:#1a1206;border:1px solid #7c2d12;border-radius:8px;padding:9px 11px;'
              +  'margin-bottom:8px;color:#fdba74;">' + bits.map(b => '<div style="margin:3px 0;">' + b
              +  '</div>').join('') + '</div>';
      }
    }
    cap.innerHTML = notes + 'PRISMA 2020 / PRISMA-NMA flow (Page 2021 <em>BMJ</em>; Hutton 2015 '
      + '<em>Ann Intern Med</em>). Counts are read from RapidMeta.state.trials and realData at render time '
      + 'and re-read whenever that state changes. Stages this app never recorded are shown as '
      + '"not recorded", never as zero.';
    container.appendChild(cap);
  }

  function ready(fn) {
    if (document.readyState !== 'loading') fn();
    else document.addEventListener('DOMContentLoaded', fn);
  }

  // Re-render whenever the trial state actually changes. The caption always
  // claimed this happened; nothing had ever subscribed.
  let _lastSig = null;
  function stateSignature() {
    const st = (global.RapidMeta && global.RapidMeta.state) || {};
    const trials = Array.isArray(st.trials) ? st.trials : [];
    const rd = (global.RapidMeta && global.RapidMeta.realData) || {};
    let inc = 0, exc = 0;
    trials.forEach(t => {
      const s = (t && t.status) || '';
      if (s === 'include') inc++; else if (s === 'exclude') exc++;
    });
    return trials.length + '/' + inc + '/' + exc + '/' + Object.keys(rd).length;
  }

  function refresh(container) {
    const c = container || document.getElementById('prismaFlowContainer');
    if (!c) return false;
    render(c);
    _lastSig = stateSignature();
    return true;
  }

  ready(function () {
    const c = document.getElementById('prismaFlowContainer');
    if (!c) return;
    refresh(c);

    // Retry until the state is actually HYDRATED. The previous guard was
    //   if (total_search === 0 && in_nma === 0 && attempts < 10)
    // but realData is embedded and non-empty from the first paint, so in_nma
    // was already 28 and the && short-circuited: the retry loop never ran once.
    // The diagram was therefore painted exactly once, pre-hydration, and frozen.
    let attempts = 0;
    (function tick() {
      if (compute().hydrated) { refresh(c); return; }
      if (++attempts < 40) setTimeout(tick, 250);
      else refresh(c);   // give up, but render the honest "not recorded" state
    })();

    // Keep it live: cheap signature poll, so screening decisions made in the
    // Screening tab are reflected without a reload.
    setInterval(function () {
      const sig = stateSignature();
      if (sig !== _lastSig) refresh(c);
    }, 1500);
  });

  global.PrismaFlow = { compute, render, refresh };
})(typeof window !== 'undefined' ? window : globalThis);
