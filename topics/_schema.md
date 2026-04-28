# DTA topic config schema

Each `topics/<slug>.config.json` defines all topic-specific content for one DTA review. The build script (`scripts/build_dta_review.mjs`) reads `dta_template.html` plus a config file and emits the corresponding generated `*.html` review.

## Top-level fields

### Identity / output filenames
- `topic_slug` — short slug, lowercase with underscores (e.g., `genexpert_ultra_tb`)
- `output_filename` — file the build emits (e.g., `GENEXPERT_ULTRA_TB_DTA_REVIEW.html`)
- `ctgov_pack_filename` — JSON pack the review fetches at runtime for stale-banner
- `pubmed_pack_filename` — same, PubMed
- `audit_md_filename` — the audit-log .md the "Check for new trials" button opens
- `built_ctgov_date`, `built_pubmed_date` — ISO date baked into stale-banner

### Page metadata
- `review_title` — `<title>` content (HTML entities allowed, e.g., `&mdash;`)
- `og_title` — Open Graph title
- `og_description` — Open Graph description
- `header_h1` — Top-of-page H1
- `header_subtitle` — H1 subtitle line

### State / persistence
- `ls_prefix` — localStorage key prefix (must end with `-`); MUST be unique per topic
- `state_schema_name` — JSON-export `schema` field; used by import-validator

### Tier definitions
- `default_tier_slug` — slug of the default headline tier (e.g., `sputum_culture`)
- `all_tier_slug` — slug of the "all-tier" / combined tier (default: `combined`)
- `combined_tier_k` — total k in all-tier (used in subgroup-tab paragraph)
- `primary_tier_label` — short label for headline-banner (e.g., `Sputum+culture`)
- `tiers[]` — array of tier definitions, each:
  - `slug` (string, used as JS object key)
  - `label` (short text label)
  - `js_label` (label used in TIER_LABELS map; usually = label)
  - `label_html` (HTML rendered next to the radio button)
  - `studlabs[]` (study labels included in this tier)
- `tier_selector_description` — paragraph above tier radios

### Banners (topic-specific text)
- `headline_banner_text` — appended after "estimates diverge by N pp on Sens or Spec."
- `combined_tier_disclosure` — text shown when Combined tier is active

### Fagan tier dropdown
- `fagan_tier_options[]` — `[{ value, label, label_html }]`

### Subgroups tab
- `subgroups_axes[]` — `[{ id, field, label, options[], levels[]?, match_mode?, min_width?, help_html? }]`
  - `id` (DOM id, e.g., `sg-population-age`)
  - `field` (trial JSON field name, e.g., `population_age`)
  - `label` (axis label)
  - `options[]` (dropdown options; first should be `'any'`)
  - `levels[]` (optional; values used in Q_between subgroup interaction test)
  - `match_mode` (optional; only `regex_hiv` is currently supported)
  - `min_width` (optional CSS min-width)
  - `help_html` (optional small text under dropdown)

### Extraction tab dropdowns
- `ext_choices` — `{ population_age[], specimen[], reference_standard_specific[], prevalence_setting[], hiv_status[] }`
- `index_test_cartridge_label` — fixed text in the per-study extraction grid

### Helper text
- `prevalence_default_help` — appended to the prevalence-slider help line
- `fagan_default_help` — appended to the Fagan-slider help line

### HTML chunks (full HTML, generated from config or by hand)
- `plain_language_html` — body of the Plain-language summary tab (after the boilerplate intro)
- `protocol_html` — body of the Protocol tab (after the H2)
- `search_html` — body of the Search tab (after the H2)
- `prisma_flow_html` — content of the PRISMA-flow div
- `inter_rater_html` — content of the inter-rater agreement panel
- `quadas_inline_flags[]` — `[{ studlab, flag_html }]` for the Extraction-tab inline QUADAS table

### QUADAS-2 baselines
- `quadas_flags` — `{ <studlab>: { q11, q12, q13, q21, q22, q31, q32, q41, q42, q43, q44, rob1, rob2, rob3, rob4, app1, app2, app3 } }` (each value: `Yes` / `No` / `Unclear` / `Low` / `High`)

### Screening cards
- `screening_cards[]` — array of cards rendered into `var screeningStudies` in JS:
  - `decision`: `included` | `excluded`
  - `tier`: `primary` | `sensitivity` | null (included cards only)
  - `studlab`, `title`, `authors`, `year`, `journal`, `country`, `ref_std`
  - `abstract` (full abstract text — verbatim from PubMed when available)
  - `rationale` (reviewer-facing notes)
  - `nctid`, `pmid`, `doi` (each may be null)
  - excluded cards also have `reason`, `verbatim_source`

### Manuscript
- `manuscript` — `{ title, abstract_background, abstract_methods, abstract_conclusions_prefix, methods_para, limitations_para, primary_tier_name, primary_tier_studies?, primary_tier_short, sensitivity_tier_short, total_raw_hits, discussion_high_variance_suffix, discussion_topic_specific_flag, ppi_text }`

### Trial dataset
- `trials` — the embedded `<script type="application/json" id="dta-trials">` payload:
  - `test`, `reference_standard`, `target_condition`, `population`
  - `extracted_at`, `engine_version_baked_for`
  - `primary_tier[]` — array of trials (each: `studlab, year, country, design, nctid, pmid, ref_doi, TP, FP, FN, TN, prevalence_setting, hiv_status, specimen, population_age, reference_standard_specific, provenance, raw_quote, data_caveats?`)
  - `sensitivity_tier_added[]` — same shape
  - `_engine_expected_flags` (documentation only)

## Adding a new topic

1. Copy an existing config (e.g., `genexpert_ultra_tb.config.json`) to `topics/<new_slug>.config.json`.
2. Replace fields. Pay particular attention to:
   - `ls_prefix` must be unique (use the topic slug + `-`)
   - `state_schema_name` should match `<ls_prefix>state` convention
   - `output_filename` should match the desired generated file name
   - `default_tier_slug` and `all_tier_slug` must reference real entries in `tiers[]`
3. Run `npm run build:dta` (or `node scripts/build_dta_review.mjs topics/<new_slug>.config.json`).
4. Smoke-test the generated HTML in a browser; check the Summary, Forest, SROC, Subgroups tabs.

## Build-script invariants

- The shared engine, validator, and service worker are NEVER touched by the build:
  - `rapidmeta-dta-engine-v1.js`
  - `webr-dta-validator.js`
  - `coi-serviceworker.js`
  - `tests/test_dta_engine.mjs`
- Each generated HTML must:
  - parse as valid HTML (balanced divs, balanced `<script>` tags)
  - inline JS must parse (no `</script>` in template literals)
  - JSON `<script>` payload must parse via `JSON.parse`
  - have unique localStorage prefix (no cross-talk between topic reviews)
