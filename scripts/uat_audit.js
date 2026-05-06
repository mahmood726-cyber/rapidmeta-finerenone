/* In-page UAT audit. Returns a JSON report describing the page health,
 * the visible widgets, and (optionally) the result of clicking key buttons.
 *
 * Usage in Playwright evaluate():
 *   const audit = (await import('uat_audit.js')).default;
 *   audit({ exerciseButtons: true })
 *
 * Or paste the function body into browser_evaluate.
 */
window.__UAT_AUDIT__ = async function (opts = {}) {
  const exerciseButtons = opts.exerciseButtons !== false;
  const out = {
    url: location.pathname.split('/').pop(),
    title: document.title,
    timestamp: new Date().toISOString(),
    parse_errors: [],
    state: {},
    widgets: {},
    buttons: {},
    text_checks: {},
    overall: 'PENDING',
  };

  // 1. Page health: did RapidMeta hydrate?
  out.state.has_RapidMeta = typeof window.RapidMeta === 'object';
  out.state.has_NMA_CONFIG = typeof window.NMA_CONFIG === 'object';
  out.state.realData_count = window.RapidMeta?.realData
    ? Object.keys(window.RapidMeta.realData).length : 0;
  out.state.is_NMA = !!window.NMA_CONFIG?.treatments;

  // 2. Widget presence (check key DOM containers)
  const widgetIds = [
    'r-validation-badge',
    'standard-network-graph',
    'nma-network-plot',
    'attestationBadgesContainer',
    'pairwise-pool-widget',
    'verdict-badge',
    'transitivityResult',
    'consistency-result',
    'doi-lfk-result',
    'comparison-funnel-result',
    'cinema-result',
    'poth-result',
    'q-decomposition-result',
    'contribution-matrix-result',
    'rob2-result',
    'rob-nma-result',
    'prismaFlow',
    'outcome-switching',
    'living-review-result',
    'extractionTab',
    'screeningTab',
  ];
  for (const id of widgetIds) {
    const el = document.getElementById(id);
    out.widgets[id] = el ? {
      present: true,
      visible: el.offsetParent !== null || el.getBoundingClientRect().height > 0,
      content_chars: (el.innerText || '').length,
    } : null;
  }

  // 3. Text checks: forbidden placeholders
  const bodyText = document.body.innerText;
  out.text_checks.has_unfilled_placeholder = /\{\{[^}]+\}\}|__PLACEHOLDER__|REPLACE_ME|TODO_FILL/.test(bodyText);
  out.text_checks.has_undefined_string = /\bundefined\b/.test(bodyText);
  out.text_checks.has_NaN = /\bNaN\b/.test(bodyText);
  out.text_checks.title_matches_h1 = (() => {
    const h1 = document.querySelector('h1');
    if (!h1) return null;
    const t = (h1.textContent || '').trim().toLowerCase();
    const d = document.title.toLowerCase();
    return t.length > 5 && d.includes(t.slice(0, 25));
  })();
  out.text_checks.no_lorem_ipsum = !/lorem ipsum/i.test(bodyText);

  // 4. Button discovery & selective exercise
  if (exerciseButtons) {
    // Find buttons by their onclick handlers (RapidMeta convention)
    const allButtons = Array.from(document.querySelectorAll('button')).filter(b => {
      const oc = b.getAttribute('onclick') || '';
      const tx = (b.textContent || '').trim();
      return tx.length > 0 && tx.length < 80;
    });
    out.buttons.total_count = allButtons.length;

    // Categorize by label keyword
    const targets = {
      'pairwise pool': /re-?pool|pairwise pool|pool.*HKSJ|live re-pool/i,
      'transitivity': /transitivity matrix/i,
      'consistency': /node.?split|consistency/i,
      'doi-lfk': /doi.*lfk|lfk index/i,
      'comparison-funnel': /comparison.adjusted funnel/i,
      'cinema': /cinema/i,
      'poth': /poth|hierarchy uncertainty/i,
      'q-decomposition': /q.?decomposition/i,
      'contribution-matrix': /contribution matrix/i,
      'rob2': /\brob.?2\b|risk of bias 2|autofill rob/i,
      'rob-nma': /rob.?nma/i,
      'prisma': /prisma/i,
      'outcome-switching': /outcome.switching|outcome switch/i,
      'living-review': /living review|trigger living|update search/i,
      'verdict': /verdict|7-gate|recompute verdict/i,
    };

    for (const [key, rx] of Object.entries(targets)) {
      const btn = allButtons.find(b => rx.test(b.textContent || '') || rx.test(b.getAttribute('onclick') || ''));
      if (!btn) {
        out.buttons[key] = { found: false };
        continue;
      }
      out.buttons[key] = {
        found: true,
        text: (btn.textContent || '').trim().slice(0, 60),
        onclick_present: !!btn.getAttribute('onclick'),
      };
      try {
        const beforeHash = JSON.stringify(Object.fromEntries(
          widgetIds.map(id => [id, document.getElementById(id)?.innerText?.length || 0])
        ));
        btn.click();
        // give it a moment
        await new Promise(r => setTimeout(r, 250));
        const afterHash = JSON.stringify(Object.fromEntries(
          widgetIds.map(id => [id, document.getElementById(id)?.innerText?.length || 0])
        ));
        out.buttons[key].clicked = true;
        out.buttons[key].state_changed = beforeHash !== afterHash;
      } catch (e) {
        out.buttons[key].clicked = false;
        out.buttons[key].error = String(e).slice(0, 200);
      }
    }
  }

  // 5. Overall
  const issues = [];
  if (!out.state.has_RapidMeta) issues.push('RapidMeta_missing');
  if (out.state.is_NMA && !out.state.has_NMA_CONFIG) issues.push('NMA_CONFIG_missing');
  if (out.state.realData_count === 0) issues.push('no_realData');
  if (out.text_checks.has_unfilled_placeholder) issues.push('placeholder_residue');
  if (out.text_checks.has_NaN) issues.push('NaN_in_dom');
  for (const [k, v] of Object.entries(out.buttons)) {
    if (typeof v === 'object' && v.found && v.clicked === false) {
      issues.push('btn_failed:' + k);
    }
  }
  out.issues = issues;
  out.overall = issues.length === 0 ? 'PASS' : (issues.length <= 2 ? 'WARN' : 'FAIL');

  return out;
};
