#!/usr/bin/env node
// Build a DTA review HTML from dta_template.html + per-topic config.
// Usage: node scripts/build_dta_review.mjs topics/<topic>.config.json
//
// The template has three substitution mechanisms:
//   1. Simple   {{key}}                                     -- for strings/numbers
//   2. HTML     <!-- BEGIN block --> ... <!-- END block --> -- for HTML chunks
//   3. JS       // BEGIN block_js / // END block_js          -- for JS chunks
//
// Each block has a dedicated render function. Block names are documented in
// topics/_schema.md. Adding a new block: edit dta_template.html to add the
// markers, then add a render function here.
//
// Vanilla Node only -- no npm dependencies.

import { readFileSync, writeFileSync } from 'node:fs';
import { resolve, dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = dirname(fileURLToPath(import.meta.url));
const REPO_ROOT = resolve(__dirname, '..');

function fail(msg) {
  console.error('[build_dta_review] ERROR: ' + msg);
  process.exit(1);
}

// ==================== Block-region helpers ====================

// Replace an HTML region between <!-- BEGIN name --> and <!-- END name -->.
// If stripMarkers=true, the BEGIN/END comments themselves are also removed
// (necessary for blocks that live inside a non-HTML container like a JSON <script>).
function replaceHtmlBlock(html, name, body, stripMarkers = false) {
  const startMarker = `<!-- BEGIN ${name} -->`;
  const endMarker = `<!-- END ${name} -->`;
  const startIdx = html.indexOf(startMarker);
  const endIdx = html.indexOf(endMarker, startIdx);
  if (startIdx === -1 || endIdx === -1) {
    fail(`HTML block markers for "${name}" not found in template (start=${startIdx}, end=${endIdx}).`);
  }
  if (stripMarkers) {
    const before = html.slice(0, startIdx);
    const after = html.slice(endIdx + endMarker.length);
    return before + body + after;
  }
  const before = html.slice(0, startIdx + startMarker.length);
  const after = html.slice(endIdx);
  return before + '\n' + body + '\n' + after;
}

// Replace a JS region between // BEGIN name and // END name.
function replaceJsBlock(html, name, body) {
  const startMarker = `// BEGIN ${name}`;
  const endMarker = `// END ${name}`;
  const startIdx = html.indexOf(startMarker);
  const endIdx = html.indexOf(endMarker, startIdx);
  if (startIdx === -1 || endIdx === -1) {
    fail(`JS block markers for "${name}" not found in template (start=${startIdx}, end=${endIdx}).`);
  }
  const before = html.slice(0, startIdx + startMarker.length);
  const after = html.slice(endIdx);
  return before + '\n' + body + '\n' + after;
}

// Escape <, >, & for HTML content (NOT attributes -- attributes use escAttr).
function escHtml(s) {
  if (s == null) return '';
  return String(s)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;');
}
function escAttr(s) {
  if (s == null) return '';
  return String(s)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');
}

// JSON.stringify with 2-space indent for embedded JSON+JS.
function jsonStringify(obj, indent = 2) {
  return JSON.stringify(obj, null, indent);
}

// ==================== Render functions ====================

function renderTrialsJson(html, config) {
  const trials = config.trials;
  if (!trials) fail('config.trials is required');
  // Pretty-print exactly like the original 2-space indentation. Strip the
  // BEGIN/END comment markers because the block lives inside a JSON <script>.
  const json = jsonStringify(trials, 2);
  return replaceHtmlBlock(html, 'trials_json', json, /* stripMarkers */ true);
}

function renderPlainLanguage(html, config) {
  const body = config.plain_language_html || '';
  if (!body) fail('config.plain_language_html is required');
  return replaceHtmlBlock(html, 'plain_language', body);
}

function renderProtocolBody(html, config) {
  const body = config.protocol_html || '';
  if (!body) fail('config.protocol_html is required');
  return replaceHtmlBlock(html, 'protocol_body', body);
}

function renderSearchBody(html, config) {
  const body = config.search_html || '';
  if (!body) fail('config.search_html is required');
  return replaceHtmlBlock(html, 'search_body', body);
}

function renderPrismaFlow(html, config) {
  const body = config.prisma_flow_html || '';
  if (!body) fail('config.prisma_flow_html is required');
  return replaceHtmlBlock(html, 'prisma_flow', body);
}

function renderInterRater(html, config) {
  const body = config.inter_rater_html || '';
  if (!body) fail('config.inter_rater_html is required');
  return replaceHtmlBlock(html, 'inter_rater', body);
}

function renderQuadasInlineRows(html, config) {
  const flags = config.quadas_inline_flags || [];
  if (!flags.length) fail('config.quadas_inline_flags is required (array of {studlab, flag})');
  const rows = flags.map(f =>
    `            <tr><td class="study-name">${escHtml(f.studlab)}</td><td>${f.flag_html || escHtml(f.flag)}</td></tr>`
  ).join('\n');
  return replaceHtmlBlock(html, 'quadas_inline_rows', rows);
}

function renderTierSelectorBody(html, config) {
  const tiers = config.tiers || [];
  if (!tiers.length) fail('config.tiers is required (array of {slug, label, description})');
  const defaultSlug = config.default_tier_slug;
  const desc = config.tier_selector_description || '';
  const labels = tiers.map(t => {
    const checked = t.slug === defaultSlug ? ' checked' : '';
    return `        <label><input type="radio" name="tier" value="${escAttr(t.slug)}"${checked}> ${t.label_html || escHtml(t.label)}</label>`;
  }).join('\n');
  const body = `        <p style="font-size:0.85rem;color:#374151;margin:0 0 0.6rem;">\n          ${desc}\n        </p>\n${labels}`;
  return replaceHtmlBlock(html, 'tier_selector_body', body);
}

function renderFaganTierOptions(html, config) {
  const opts = config.fagan_tier_options || [];
  if (!opts.length) fail('config.fagan_tier_options is required');
  const body = opts.map(o =>
    `            <option value="${escAttr(o.value)}">${o.label_html || escHtml(o.label)}</option>`
  ).join('\n');
  return replaceHtmlBlock(html, 'fagan_tier_options', body);
}

function renderSubgroupsAxes(html, config) {
  const axes = config.subgroups_axes || [];
  if (!axes.length) fail('config.subgroups_axes is required');
  const body = axes.map(ax => {
    const opts = (ax.options || []).map(opt => {
      const v = typeof opt === 'string' ? opt : opt.value;
      const label = typeof opt === 'string' ? opt : (opt.label || opt.value);
      return `            <option value="${escAttr(v)}">${escHtml(label)}</option>`;
    }).join('\n');
    const minWidth = ax.min_width || '150px';
    const helpHtml = ax.help_html
      ? `\n          <div style="font-size:0.65rem;color:#6b7280;margin-top:0.15rem;">${ax.help_html}</div>`
      : '';
    return `        <div>
          <label for="${ax.id}" style="display:block;font-size:0.75rem;font-weight:600;color:#374151;margin-bottom:0.25rem;">${escHtml(ax.label)}</label>
          <select id="${ax.id}" style="padding:0.4rem;border:1px solid #d1d5db;border-radius:0.25rem;min-width:${minWidth};">
${opts}
          </select>${helpHtml}
        </div>`;
  }).join('\n');
  return replaceHtmlBlock(html, 'subgroups_axes', body);
}

// ===== JS blocks =====

function renderTierJsBlock(html, config) {
  const tiers = config.tiers || [];
  const defaultSlug = config.default_tier_slug;
  const allTierSlug = config.all_tier_slug || 'combined';
  const tierKeys = tiers.map(t => t.slug);
  const buildTiersBody = tiers.map(t => {
    const studs = JSON.stringify(t.studlabs || []);
    return `          ${t.slug}: pick(${studs})`;
  }).join(',\n');
  const tierLabels = tiers.map(t => `        ${t.slug}: ${JSON.stringify(t.js_label || t.label)}`).join(',\n');
  const tierKeysJs = JSON.stringify(tierKeys);

  // primaryAlias = default_tier; allTierAlias = all_tier_slug
  // Other tiers between default and all_tier are aliased generically.
  const otherTiers = tiers.filter(t => t.slug !== defaultSlug && t.slug !== allTierSlug);
  const otherAliasInit = otherTiers.map(t =>
    `      var trials_${t.slug} = tiers.${t.slug}.slice();`
  ).join('\n');

  const body = `      // Tier definitions (generated from config):
      function buildTiers() {
        var allByLab = {};
        data.primary_tier.concat(data.sensitivity_tier_added).forEach(function (t) {
          allByLab[t.studlab] = t;
        });
        function pick(labels) {
          return labels.map(function (l) { return allByLab[l]; }).filter(function (x) { return !!x; });
        }
        return {
${buildTiersBody}
        };
      }
      var TIER_LABELS = {
${tierLabels}
      };
      var TIER_KEYS = ${tierKeysJs};
      var tiers = buildTiers();
      // Back-compat aliases used by headline-banner / subgroup filter:
      //   trials_primary  -> default tier
      //   trials_combined -> all-tier
      var trials_primary = tiers.${defaultSlug}.slice();
      var trials_combined = tiers.${allTierSlug}.slice();
${otherAliasInit}`;
  return replaceJsBlock(html, 'tier_js_block', body);
}

function renderTierAliasRebuild(html, config) {
  const tiers = config.tiers || [];
  const defaultSlug = config.default_tier_slug;
  const allTierSlug = config.all_tier_slug || 'combined';
  const otherTiers = tiers.filter(t => t.slug !== defaultSlug && t.slug !== allTierSlug);
  const lines = [
    `        trials_primary = tiers.${defaultSlug}.slice();`,
    `        trials_combined = tiers.${allTierSlug}.slice();`,
    ...otherTiers.map(t => `        trials_${t.slug} = tiers.${t.slug}.slice();`)
  ];
  return replaceJsBlock(html, 'tier_alias_rebuild', lines.join('\n'));
}

function renderQuadasBaselinesJs(html, config) {
  const flags = config.quadas_flags || {};
  const entries = Object.entries(flags);
  if (entries.length === 0) fail('config.quadas_flags is required (object keyed by studlab)');
  const lines = entries.map(([studlab, q]) => {
    const fields = [
      `q11: ${JSON.stringify(q.q11 || 'Unclear')}, q12: ${JSON.stringify(q.q12 || 'Unclear')}, q13: ${JSON.stringify(q.q13 || 'Unclear')}, rob1: ${JSON.stringify(q.rob1 || 'Unclear')}, app1: ${JSON.stringify(q.app1 || 'Unclear')}`,
      `          q21: ${JSON.stringify(q.q21 || 'Unclear')}, q22: ${JSON.stringify(q.q22 || 'Unclear')}, rob2: ${JSON.stringify(q.rob2 || 'Unclear')}, app2: ${JSON.stringify(q.app2 || 'Unclear')}`,
      `          q31: ${JSON.stringify(q.q31 || 'Unclear')}, q32: ${JSON.stringify(q.q32 || 'Unclear')}, rob3: ${JSON.stringify(q.rob3 || 'Unclear')}, app3: ${JSON.stringify(q.app3 || 'Unclear')}`,
      `          q41: ${JSON.stringify(q.q41 || 'Unclear')}, q42: ${JSON.stringify(q.q42 || 'Unclear')}, q43: ${JSON.stringify(q.q43 || 'Unclear')}, q44: ${JSON.stringify(q.q44 || 'Unclear')}, rob4: ${JSON.stringify(q.rob4 || 'Unclear')}`
    ].join(',\n');
    return `        ${JSON.stringify(studlab)}: {\n          ${fields}\n        }`;
  }).join(',\n');
  const body = `      var QUADAS_BASELINES = {\n${lines}\n      };`;
  return replaceJsBlock(html, 'quadas_baselines_js', body);
}

function renderSubgroupsAxesGlobalJs(html, config) {
  const axes = config.subgroups_axes || [];
  const ids = axes.map(a => a.id);
  const arr = axes.map(a => {
    const o = { id: a.id, field: a.field };
    if (a.match_mode) o.match_mode = a.match_mode;
    if (a.levels) o.levels = a.levels;
    if (a.label) o.label = a.label;
    return o;
  });
  const idsJs = JSON.stringify(ids);
  const arrJs = JSON.stringify(arr, null, 2).split('\n').map((l, i) => i === 0 ? l : '      ' + l).join('\n');
  const body = `      // Subgroup axes (config-driven; used by both applySubgroupFilter and renderSubgroups)
      var SG_FILTER_IDS = ${idsJs};
      var SUBGROUPS_AXES = ${arrJs};`;
  return replaceJsBlock(html, 'subgroups_axes_global_js', body);
}

function renderSgFilterIdsJs(html, config) {
  // The local block inside renderSubgroups is now a no-op (vars are global).
  // We still emit a friendly comment so the diff stays minimal.
  const body = `        // SG_FILTER_IDS / SUBGROUPS_AXES are declared at top-level (subgroups_axes_global_js).`;
  return replaceJsBlock(html, 'sg_filter_ids_js', body);
}

function renderExtChoicesJs(html, config) {
  const choices = config.ext_choices || {};
  const json = JSON.stringify(choices, null, 2);
  // Indent for embedding
  const indented = json.split('\n').map(l => '      ' + l).join('\n');
  const body = `      var EXT_CHOICES = ${indented.trimStart()};`;
  return replaceJsBlock(html, 'ext_choices_js', body);
}

function renderManuscriptStringsJs(html, config) {
  const m = config.manuscript || {};
  const required = ['title', 'abstract_background', 'abstract_methods', 'abstract_conclusions_prefix',
    'methods_para', 'limitations_para', 'primary_tier_name', 'primary_tier_short',
    'sensitivity_tier_short', 'total_raw_hits', 'discussion_high_variance_suffix',
    'discussion_topic_specific_flag', 'ppi_text'];
  for (const k of required) {
    if (m[k] === undefined) fail(`config.manuscript.${k} is required`);
  }
  // Inject ALSO output_filename, ctgov_pack_filename, pubmed_pack_filename, primary_tier_studies (optional)
  const obj = {
    title: m.title,
    abstract_background: m.abstract_background,
    abstract_methods: m.abstract_methods,
    abstract_conclusions_prefix: m.abstract_conclusions_prefix,
    methods_para: m.methods_para,
    limitations_para: m.limitations_para,
    primary_tier_name: m.primary_tier_name,
    primary_tier_studies: m.primary_tier_studies || '',
    primary_tier_short: m.primary_tier_short,
    sensitivity_tier_short: m.sensitivity_tier_short,
    total_raw_hits: m.total_raw_hits,
    discussion_high_variance_suffix: m.discussion_high_variance_suffix,
    discussion_topic_specific_flag: m.discussion_topic_specific_flag,
    ppi_text: m.ppi_text,
    output_filename: config.output_filename,
    ctgov_pack_filename: config.ctgov_pack_filename,
    pubmed_pack_filename: config.pubmed_pack_filename
  };
  const json = JSON.stringify(obj, null, 2);
  const indented = json.split('\n').map(l => '      ' + l).join('\n').trimStart();
  const body = `      var MANUSCRIPT = ${indented};`;
  return replaceJsBlock(html, 'manuscript_strings_js', body);
}

function renderScreeningStudiesJs(html, config) {
  const cards = config.screening_cards || [];
  if (!cards.length) fail('config.screening_cards is required');
  // Emit each card as a JS object literal. Use JSON.stringify per card and indent.
  const inc = cards.filter(c => c.decision === 'included');
  const exc = cards.filter(c => c.decision === 'excluded');
  function emitCard(c) {
    // Required fields plus optional ones
    const o = {
      decision: c.decision,
      tier: c.tier || null,
      studlab: c.studlab,
      title: c.title || '',
      authors: c.authors || '',
      year: c.year || null,
      journal: c.journal || '',
      country: c.country || '',
      ref_std: c.ref_std || '',
      abstract: c.abstract || '',
      rationale: c.rationale || '',
      nctid: c.nctid || null,
      pmid: c.pmid || null,
      doi: c.doi || null
    };
    if (c.reason) o.reason = c.reason;
    if (c.verbatim_source) o.verbatim_source = c.verbatim_source;
    return JSON.stringify(o, null, 2).split('\n').map(l => '        ' + l).join('\n').trimStart();
  }
  const incBlock = inc.length
    ? `        // ===== INCLUDED (k = ${inc.length}) =====\n        ${inc.map(emitCard).join(',\n        ')}`
    : '';
  const excBlock = exc.length
    ? `        // ===== EXCLUDED (${exc.length} entries) =====\n        ${exc.map(emitCard).join(',\n        ')}`
    : '';
  const sep = (incBlock && excBlock) ? ',\n\n' : '';
  const body = incBlock + sep + excBlock;
  return replaceJsBlock(html, 'screening_studies_js', body);
}

// ==================== {{key}} substitution ====================

function substituteScalars(html, config) {
  // Topic-specific scalars expected at top level of config.
  // These are simple {{key}} substitutions.
  const map = {
    review_title: config.review_title,
    og_title: config.og_title,
    og_description: config.og_description,
    header_h1: config.header_h1,
    header_subtitle: config.header_subtitle,
    default_tier_slug: config.default_tier_slug,
    ls_prefix: config.ls_prefix,
    state_schema_name: config.state_schema_name,
    combined_tier_k: config.combined_tier_k,
    primary_tier_label: config.primary_tier_label,
    headline_banner_text: config.headline_banner_text,
    combined_tier_disclosure: config.combined_tier_disclosure,
    built_ctgov_date: config.built_ctgov_date,
    built_pubmed_date: config.built_pubmed_date,
    ctgov_pack_filename: config.ctgov_pack_filename,
    pubmed_pack_filename: config.pubmed_pack_filename,
    audit_md_filename: config.audit_md_filename,
    index_test_cartridge_label: config.index_test_cartridge_label,
    prevalence_default_help: config.prevalence_default_help,
    fagan_default_help: config.fagan_default_help
  };
  let out = html;
  for (const [k, v] of Object.entries(map)) {
    if (v === undefined) {
      // Don't fail-closed on missing scalars; some are optional. But warn:
      console.warn(`[build_dta_review] WARN: scalar "${k}" missing from config`);
      continue;
    }
    out = out.split(`{{${k}}}`).join(String(v));
  }
  return out;
}

// ==================== Main ====================

function main() {
  const configPath = process.argv[2];
  if (!configPath) {
    console.error('Usage: node scripts/build_dta_review.mjs topics/<topic>.config.json');
    process.exit(1);
  }
  const absConfigPath = resolve(configPath);
  let config;
  try {
    config = JSON.parse(readFileSync(absConfigPath, 'utf-8'));
  } catch (e) {
    fail(`Could not parse config: ${e.message}`);
  }

  const templatePath = join(REPO_ROOT, 'dta_template.html');
  let html;
  try {
    html = readFileSync(templatePath, 'utf-8');
  } catch (e) {
    fail(`Could not read template at ${templatePath}: ${e.message}`);
  }

  // 1) Render structured HTML blocks
  html = renderTrialsJson(html, config);
  html = renderPlainLanguage(html, config);
  html = renderProtocolBody(html, config);
  html = renderSearchBody(html, config);
  html = renderPrismaFlow(html, config);
  html = renderInterRater(html, config);
  html = renderQuadasInlineRows(html, config);
  html = renderTierSelectorBody(html, config);
  html = renderFaganTierOptions(html, config);
  html = renderSubgroupsAxes(html, config);

  // 2) Render JS blocks
  html = renderSubgroupsAxesGlobalJs(html, config);
  html = renderTierJsBlock(html, config);
  html = renderTierAliasRebuild(html, config);
  html = renderQuadasBaselinesJs(html, config);
  html = renderSgFilterIdsJs(html, config);
  html = renderExtChoicesJs(html, config);
  html = renderManuscriptStringsJs(html, config);
  html = renderScreeningStudiesJs(html, config);

  // 3) Substitute scalar {{key}} placeholders
  html = substituteScalars(html, config);

  // 4) Sanity check: no remaining unsubstituted placeholders should leak through.
  const leftoverRe = /\{\{([a-z0-9_]+)\}\}/gi;
  const leftover = [];
  let m;
  while ((m = leftoverRe.exec(html)) !== null) {
    leftover.push(m[1]);
  }
  if (leftover.length) {
    console.warn('[build_dta_review] WARN: unsubstituted placeholders remain: ' + [...new Set(leftover)].join(', '));
  }

  const outputName = config.output_filename;
  if (!outputName) fail('config.output_filename is required');
  const outputPath = join(REPO_ROOT, outputName);
  writeFileSync(outputPath, html, 'utf-8');
  console.log(`[build_dta_review] Built ${outputName} (${html.length} chars, ${html.split('\n').length} lines)`);
}

main();
