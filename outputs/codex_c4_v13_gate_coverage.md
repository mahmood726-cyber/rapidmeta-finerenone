# v13 Output Gate Coverage Audit

Date: 2026-08-23

Scope boundary: this is an output-coverage audit for `generate_living_ma_v13.py`. A gate that reads `ssot/**/*.json` is not counted as covering v13 output unless it also reads the HTML files that this generator writes.

## Bottom line

| Verdict | Count |
|---|---:|
| CAN COVER v13 OUTPUT AS-IS | 1 |
| CAN BE EXTENDED TO COVER IT | 19 |
| STRUCTURALLY CANNOT | 89 |
| Total refusal gates counted | 109 |

The important gap is real: almost all existing gates are SSOT-object, source-code, hook-integrity, or fixed-dashboard gates. They do not cover v13 output, because `generate_living_ma_v13.py` writes HTML files into sibling `*_LivingMeta` directories and does not write `ssot/**/*.json`.

## v13 Generator I/O From Code

### Located file

`generate_living_ma_v13.py` is at repo root.

### Inputs it reads

1. Template HTML:
   - Lines 3-12 state the purpose and path controls: it "Reads FINERENONE_REVIEW.html"; `TEMPLATE_PATH` defaults beside the script; `OUTPUT_BASE` defaults to the parent directory; both have env overrides.
   - Lines 21-29 define `_SCRIPT_DIR`, `TEMPLATE_PATH = LIVINGMA_TEMPLATE_PATH or _SCRIPT_DIR / "FINERENONE_REVIEW.html"`, and `OUTPUT_BASE = LIVINGMA_OUTPUT_BASE or _SCRIPT_DIR.parent`.
   - Lines 704-706 actually read `TEMPLATE_PATH` and then call `_refuse_wrong_template(template)`.

2. Template identity markers:
   - Lines 36-40 define required v13 markers and forbidden SSOT-projector markers: `_TEMPLATE_MUST_HAVE = ("window.RapidMeta", "RapidMeta.state", "tab-btn")`; `_TEMPLATE_MUST_NOT_HAVE = ("Sources for this section", "Reproducibility artifact", "<strong>Refused:</strong>")`.
   - Lines 43-61 define the refusal guard. Lines 46-50 explicitly describe the footgun: the default template may now be SSOT-projector output, and a wrong read has the "blast radius of the 1,314 pages this generator has produced."

3. Optional sibling Tailwind CSS:
   - Lines 233-239 build `css_path = os.path.join(os.path.dirname(TEMPLATE_PATH), 'FINERENONE_REVIEW.tailwind.css')`; if it exists, the generator reads and inlines it.

4. Embedded Python config:
   - Lines 582-589 define `validate_config(cfg)`, which inspects `cfg['trials']`.
   - Lines 805 onward define `APPS` and later `APPS.append(...)` entries. These are embedded in the generator, not read from `ssot/**/*.json`.

5. Optional hardcoded staging profile:
   - Lines 709-716 set `_staging_dir = Path(r"C:\Projects\rapidmeta-staging\profiles")`, derive `_profile_path = _staging_dir / f"{_storage_key}.json"`, and read it with `json.loads(_profile_path.read_text(...))` if it exists.
   - Lines 719-727 use the profile to override `protocol`, `auto_include_ids`, `trials_supplement`, and `effect_measure`.

6. Scaffold-time blocking logic:
   - Lines 692-702 run `validate_config(cfg)` and return errors if mixed outcome classes are found and `LIVINGMA_ALLOW_MIXED` is not set.

I found no code path in this generator that reads `ssot/**/*.json`. The only external JSON file read in the generator is the optional staging profile at `C:\Projects\rapidmeta-staging\profiles\{storage_key}.json` (lines 709-716).

### Outputs it writes

The write path is one HTML file per selected `APPS` entry:

- Lines 792-795 set `out_dir = output_dir or os.path.dirname(TEMPLATE_PATH)`, `out_path = os.path.join(out_dir, cfg['filename'])`, and write with `open(out_path, 'w', encoding='utf-8')`.
- Lines 7467-7474 select an optional filename substring target, then call `generate_app(app, app.get('output_dir', None))`.
- Lines 7476-7479 report total errors and exit nonzero if any were accumulated.

Current code enumerates 26 app outputs. The generator comment at line 50 records that this generator has produced 1,314 pages historically, but the current source path visible here writes one HTML file per current `APPS` entry. I do not infer any additional output path not present in the code.

| Lines | Filename | Output directory expression |
|---|---|---|
| 807-808 | `PFA_AF_REVIEW.html` | `os.path.join(OUTPUT_BASE, "PFA_AF_LivingMeta")` |
| 982-983 | `WATCHMAN_AMULET_REVIEW.html` | `os.path.join(OUTPUT_BASE, "LivingMeta_Watchman_Amulet")` |
| 1225-1226 | `TRICUSPID_TEER_REVIEW.html` | `os.path.join(OUTPUT_BASE, "Tricuspid_TEER_LivingMeta")` |
| 1365-1366 | `INCLISIRAN_REVIEW.html` | `os.path.join(OUTPUT_BASE, "Inclisiran_LivingMeta")` |
| 1635-1636 | `TIRZEPATIDE_CV_REVIEW.html` | `os.path.join(OUTPUT_BASE, "Tirzepatide_LivingMeta")` |
| 1932-1933 | `SEMAGLUTIDE_HFPEF_REVIEW.html` | `os.path.join(OUTPUT_BASE, "Semaglutide_HFpEF_LivingMeta")` |
| 2141-2142 | `LEADLESS_PACING_REVIEW.html` | `os.path.join(OUTPUT_BASE, "Leadless_Pacing_LivingMeta")` |
| 2440-2441 | `CSP_REVIEW.html` | `os.path.join(OUTPUT_BASE, "CSP_LivingMeta")` |
| 2657-2658 | `CORONARY_IVL_REVIEW.html` | `os.path.join(OUTPUT_BASE, "Coronary_IVL_LivingMeta")` |
| 2821-2822 | `OMECAMTIV_REVIEW.html` | `os.path.join(OUTPUT_BASE, "Omecamtiv_LivingMeta")` |
| 3061-3062 | `CTFFR_REVIEW.html` | `os.path.join(OUTPUT_BASE, "CTFFR_LivingMeta")` |
| 3247-3248 | `VERICIGUAT_REVIEW.html` | `os.path.join(OUTPUT_BASE, "Vericiguat_LivingMeta")` |
| 3484-3485 | `SOTAGLIFLOZIN_REVIEW.html` | `os.path.join(OUTPUT_BASE, "Sotagliflozin_LivingMeta")` |
| 3731-3732 | `TDXd_BREAST_REVIEW.html` | `os.path.join(OUTPUT_BASE, "TDXd_Breast_LivingMeta")` |
| 4074-4075 | `OSIMERTINIB_NSCLC_REVIEW.html` | `os.path.join(OUTPUT_BASE, "Osimertinib_NSCLC_LivingMeta")` |
| 4424-4425 | `ANTI_AMYLOID_AD_REVIEW.html` | `os.path.join(OUTPUT_BASE, "AntiAmyloid_AD_LivingMeta")` |
| 4748-4749 | `RESMETIROM_MASH_REVIEW.html` | `os.path.join(OUTPUT_BASE, "Resmetirom_MASH_LivingMeta")` |
| 5012-5013 | `SEMAGLUTIDE_CKD_REVIEW.html` | `os.path.join(OUTPUT_BASE, "Semaglutide_CKD_LivingMeta")` |
| 5180-5181 | `TICAGRELOR_MONO_REVIEW.html` | `os.path.join(OUTPUT_BASE, "Ticagrelor_Mono_LivingMeta")` |
| 5509-5510 | `SOTATERCEPT_PAH_REVIEW.html` | `os.path.join(OUTPUT_BASE, "Sotatercept_PAH_LivingMeta")` |
| 5769-5770 | `ICOSAPENT_ETHYL_REVIEW.html` | `os.path.join(OUTPUT_BASE, "Icosapent_Ethyl_LivingMeta")` |
| 6027-6028 | `K_BINDERS_REVIEW.html` | `os.path.join(OUTPUT_BASE, "K_Binders_LivingMeta")` |
| 6347-6348 | `EMPA_MI_REVIEW.html` | `os.path.join(OUTPUT_BASE, "Empa_MI_LivingMeta")` |
| 6562-6563 | `DCB_PAD_REVIEW.html` | `os.path.join(OUTPUT_BASE, "DCB_PAD_LivingMeta")` |
| 6847-6848 | `ORFORGLIPRON_REVIEW.html` | `os.path.join(OUTPUT_BASE, "Orforglipron_LivingMeta")` |
| 7109-7110 | `OBESITY_NMA_REVIEW.html` | `os.path.join(OUTPUT_BASE, "Obesity_NMA_LivingMeta")` |

Because `OUTPUT_BASE` defaults to `_SCRIPT_DIR.parent` (lines 26-29), with repo root as `_SCRIPT_DIR`, the default current-output pattern is:

`<repo-parent>/<topic_LivingMeta>/<filename>`, not `ssot/**/*.json` and not necessarily repo-root `*_REVIEW.html`.

## Gate Inventory Method

Counted:

- Refusal scripts whose names are `*gate*.py` or exact gate-like wrappers, excluding documented false positives.
- Scripts invoked by `.githooks/pre-commit` and `.githooks/pre-push`.
- Other lint/guard/validation scripts that are meant to block by returning nonzero in normal gate mode.

Hook evidence:

- `.githooks/pre-commit` invokes blockers at lines 11, 14, 16, 23-24, 28, 33, 37, 40, 44, 51, 56-60, 68, 75, 83-85, 90, 96-98, 105, 113, 120, 127, 134-139, 147-152, 171, 176, 179, 183, 193, 198, 202, 208, and 212.
- `.githooks/pre-push` invokes `scripts/regression_check.py` and output-related helpers; lines 167-171 explicitly say that a changed page with no SSOT object means "the harness did not run" and "That is not coverage."
- `.githooks/pre-commit-staging` is itself a blocking path-scope gate: lines 4-8 define the allowed staged-path pattern, and lines 9-15 refuse outside it unless `STAGING_WIDE=1`.

Excluded from the count:

- `scripts/gate_kinds.py`: inventory only. Lines 21-24 warn that raw `scripts/*gate*.py` overcounts false positives, lines 40-43 define `NOT_A_GATE`, and lines 137-141 return a measurement then `return 0`.
- `scripts/add_f1000_gate.py`, `scripts/extend_alignment_gate.py`, and `docs/verification-lane/test_build_gate.py`: `scripts/lint_gate_can_fail.py` lines 40-42 explicitly says these are not gates because they act on gates.
- `propagate_*`, `aggregate_*`, `fix_*`, `regenerate_*`, `add_*`, `extend_*`: `scripts/gate_kinds.py` lines 40-43 excludes them as one-off repair or name-substring false positives.
- `scripts/lint_claim_traces_to_object.py`: line 4 says "STATUS: NOT WIRED INTO THE HOOK. IT IS NOT READY", and line 14 says "Gate it when the 18 are adjudicated -- not before."
- `scripts/lint_refusal_breaks_its_collection.py`: lines 166-168 say "CANDIDATES, NOT DEFECTS"; it has no blocking exit in normal operation.
- `scripts/audit_refusal_names_object_or_renderer.py`: lines 138-141 say "WARN, NOT BLOCK" and return 0 even with `--gate`.
- `scripts/audit_standard_percentages_provenanced.py`: lines 84-87 report unprovenanced percentages and return 0; only its internal proof floor can abort.
- Top-level reporters such as `validate_all_apps.py`, `cross_validate.py`, and `scripts/aact_outcome_concordance_check.py` either do not `sys.exit` nonzero or only write reports, so I did not count them as gates.
- One-off apply/build/withdraw scripts with `REFUSED` mutation guards are not counted as repository-state gates; their purpose is to protect that mutation, not to refuse the corpus as a standing check.

## CAN COVER v13 OUTPUT AS-IS

| Gate | What it actually checks | Deciding lines |
|---|---|---|
| `validate_living_ma_portfolio.py` | Finds sibling `*_LivingMeta` / `LivingMeta_*` app directories, reads their `*_REVIEW.html` pages, and can fail in `--gate-strict` mode on benchmark/provenance/k-min conditions. This already reaches the directory shape v13 writes by default. | `find_all_apps()` lines 581-616 search sibling living-meta directories and `*_REVIEW.html`; lines 620-624 expose `--gate`/`--gate-strict`; lines 643-645 read each HTML; lines 835-841 and 843-864 enforce gate failures. |

Limit: this gate checks benchmark/provenance/k-min facts on pages it can parse. It is not a 1,314-page completeness or hub-reachability gate.

## CAN BE EXTENDED TO COVER v13 OUTPUT

These gates are about rendered/output bytes, HTML structure, links, or browser behavior. They do not structurally depend on SSOT object shape, but their current input roots do not cover v13 output. Extension means feeding the v13 output directories, v13 hub(s), or a v13 manifest to the existing logic.

| Gate | What it actually checks | What must change | Deciding lines |
|---|---|---|---|
| `scripts/_js_parse_gate.py` | Parses inline JavaScript in HTML files/globs and fails closed on no files or unmatched globs. | Feed the v13 output file list/globs. | Lines 126-158 implement CLI file/glob expansion and nonzero exits. |
| `scripts/card_alignment_gate.py` | Compares index cards to target page headlines. | Parameterize the hub/index and page roots for v13. | Lines 222-224 read root `index.html`; lines 251-271 filter target pages and open them. |
| `scripts/clone_contamination_gate.py` | Detects cross-page clone contamination in HTML pages. | Run it on v13 output files instead of only root/corpus defaults. | Lines 35-39 document FILE/`--all`; lines 855-862 select explicit files or root `*_REVIEW.html`; line 911 reads pages; line 936 returns failure. |
| `scripts/double_escape_gate.py` | Detects double-escaped HTML/entities in pages. | Feed v13 pages or replace `--corpus` root glob with v13 output globs. | Lines 37-39 define FILE/`--corpus`; lines 113-120 glob root pages; line 132 returns nonzero on hits. |
| `scripts/gate_built_and_linked_reconcile_2026_08_23.py` | Reconciles built pages against linked pages. | Replace `ssot/PAGE_MAP.json` as the built set with a v13 output manifest/glob and read v13 hub links. | Lines 1-13 describe built-vs-linked reconciliation; lines 38-44 read `ssot/PAGE_MAP.json`; lines 76-79 read `index.html` links. |
| `scripts/gate_every_linked_target_resolves_2026_08_23.py` | Resolves front-page/hub HTML links against files in the tree. | Set `HUBS` and the HTML universe to v13 hub(s) and output dirs. | Lines 58-66 define root hubs; lines 74-91 enumerate `.html`; line 108 reads HTML; lines 137-143 and 180 refuse unresolved targets. |
| `scripts/gate_paper_reads_as_prose_2026_08_22.py` | Checks prose-like rendered HTML pages. | Run against v13 page list; may need selector scoping if v13 app JS dominates the HTML text. | Lines 198-200 default to root `*_REVIEW.html`/`*_SSOT.html`; line 220 exits nonzero. |
| `scripts/index_markup_gate.py` | Checks a hub/index HTML file for malformed/nested anchors and dead local card hrefs. | Point it at v13 hub(s) and resolve hrefs relative to v13 output roots. | Lines 63-83 check anchors; lines 99-101 resolve local href targets; line 109 defaults to root `index.html`; line 176 exits. |
| `scripts/staleness_gate.py` | Checks whether root pages/index are older than generator commits. | Add `generate_living_ma_v13.py` to generator set and v13 output dirs/pages to the page set. | Lines 37-39 hardcode `REPO`/`GEN`; lines 65-68 inspect root pages/index; line 97 refuses stale output. |
| `scripts/lint_control_chars.py` | Rejects control characters in repo text bytes. | Include v13 output dirs if they live outside repo root. | Lines 54 and 74-90 define scanned text files; lines 92-97 refuse findings. |
| `scripts/lint_identifier_pairing.py` | Checks NCT/acronym pairing in text surfaces. | Add v13 output dirs to the scan roots. | Lines 89 and 115 define scan roots; line 202 records findings; lines 223-225 refuse. |
| `scripts/lint_refusal_contradicted_by_its_own_section.py` | Reads root review HTML sections and flags local refusal/prose contradictions. | Replace root `*_REVIEW.html` glob with v13 output pages. | Lines 63 and 79-86 glob/read root review pages; lines 111-114 classify page sections; line 176 returns failure. |
| `scripts/sweep_mojibake.py --gate` | Detects mojibake/encoding damage in reader HTML. | Replace root `.html` sweep with v13 output dirs. | Lines 103-121 scope to repo-root `.html`; lines 133-140 refuse; line 225 selects gate mode. |
| `scripts/regression_check.py` | Browser/smoke regression over root `*_REVIEW.html` pages. | Serve/navigate v13 output dirs and pass full paths or a v13 manifest; current pre-push changed-page basename logic will not see sibling v13 outputs. | Line 48 globs root `*_REVIEW.html`; lines 243 and 298 read root pages; lines 357 and 360 navigate by root URL path; lines 663-679 decide failure. |
| `scripts/lint_field_name_in_reader_prose_2026_08_23.py` | Detects internal field names in visible reader HTML prose. | Replace `ssot/PAGE_MAP.json` source page mapping with a v13 output manifest/list. | Lines 83-94 define visible text extraction; line 130 reads `ssot/PAGE_MAP.json`; lines 179-192 decide baseline/failure. |
| `validate_pages_links.py` | Validates local links in a fixed published HTML file list. | Extend `PUBLISHED_HTML_FILES` to v13 hubs/pages or generate that list from v13 output. | Lines 7-11 define fixed HTML files; lines 25-26 read them; lines 39-46 resolve links; line 57 returns failure. |
| `scripts/sentinel_check.py` | Scans HTML pages for sentinel content hazards. | Invoke with v13 page paths or change the default glob. | Line 41 says no args checks root HTML; lines 217-218 gate some checks to `_REVIEW`; lines 301-305 select files; line 322 reads; line 352 returns failure. |
| `scripts/jscheck.py` | Extracts inline scripts from a given HTML file and runs `node --check`. | Invoke it over v13 output pages or wrap it with a v13 file-list runner. | Lines 1-9 describe the JS parse ship gate; lines 28-60 check a passed HTML file; lines 63-78 return nonzero on syntax errors. |
| `scripts/lint_container_repr_on_a_page.py` | Detects Python dict/list repr rendered onto delivered pages. | Replace root `*_REVIEW.html` glob with v13 output globs. | Lines 62-74 scan delivered HTML; lines 91-93 currently use root `*_REVIEW.html`; lines 130-133 refuse if any hit. |

## STRUCTURALLY CANNOT

These gates cannot cover v13 output by merely changing the input path. Their subject is the SSOT object graph, source-code mechanics, fixed benchmark/control artifacts, hook integrity, docmodel/Word artifacts, or a field shape v13 pages do not expose as standalone inputs.

| Gate | What it actually checks | Why structurally cannot cover v13 output | Deciding lines |
|---|---|---|---|
| `cross_validate_dashboard.py` | Compares `META_DASHBOARD.html` `DRUG_CLASSES` values against app synthesis results. | Requires a fixed dashboard with `const DRUG_CLASSES`, not arbitrary v13 output pages. | Lines 2-9 define dashboard-vs-app comparison; lines 40-48 parse `DRUG_CLASSES`; lines 120-122 build file URLs from repo root; lines 645-650 exit nonzero. |
| `scripts/absence_reason_gate.py` | Checks a page against an object JSON for absence/refusal reason consistency. | Requires a `<page>.html <object>.json` pair and SSOT build-mode fields. | Lines 137-150 read the page and object arguments. |
| `scripts/alignment_gate.py` | Checks docmodel/manuscript/page alignment. | Requires docmodel JSON and manuscript `.docx`, neither written by v13. | Line 20 states docmodel/manuscript/page inputs; lines 352-356 parse those paths. |
| `scripts/arm_identity_gate.py` | Checks canonical object arm identity artifacts. | Reads `*.html.canonical.json`, not v13 HTML. | Lines 274-293 and 300-312 glob/read canonical JSON artifacts. |
| `scripts/build_stamp_gate.py` | Requires generated pages to carry a `Generator build` stamp. | v13 generator does not emit this stamp; pointing v13 pages at it only fails missing stamp. | Lines 25-43 define stamp requirements; lines 76-85 take explicit page args. |
| `scripts/citation_year_gate.py` | Checks object citation year claims. | Object JSON gate. | Line 30 defines object JSON input; line 146 reads JSON; line 147 returns check result. |
| `scripts/content_gate.py` | Checks live page content against SSOT object values. | Requires SSOT object as authority. | Lines 54-92 derive expected values from object/page; line 125 requires page plus `ssot/x/x.json`. |
| `scripts/count_provenance_gate.py` | Checks count provenance in objects against optional external fetches. | Object JSON and source-fetch gate, not v13 HTML output. | Lines 62-63 define object inputs; lines 284 and 368 read JSON; lines 292-293 optionally fetch. |
| `scripts/dashboard_projection_gate.py` | Checks dashboard projection artifacts. | Reads SSOT-derived projection files, not v13 pages. | Lines 83-85 read `P.SNAP` and `P.PMAP`. |
| `scripts/declared_contrast_gate.py` | Checks declared contrasts against object/fetched registry data. | Requires object JSON fields and registry fetch shape. | Lines 49-50 define object/fetch inputs; line 211 reads object; lines 220-241 and 260 inspect contrast fields. |
| `scripts/durable_artefact_gate.py` | Checks a fixed manifest of tracked durable artifacts. | Durability manifest gate, not generated HTML corpus gate. | Lines 45-78 define `DURABLE`; lines 85-104 and 127-138 verify tracking/dirty state. |
| `scripts/estimand_definition_gate.py` | Checks SSOT estimand definition fields. | Reads SSOT objects and expected object schema. | Lines 482-505 read examples/current objects; lines 729-735 parse object CLI. |
| `scripts/extraction_table_gate.py` | Checks SSOT extraction-table signature and references. | Requires a specific extraction-table field shape; v13 template guard forbids SSOT markers. | Lines 31-47 define extraction signature; lines 147-168 parse page/object args; generator lines 36-40 forbid "Sources for this section". |
| `scripts/gate_benchmark_pmid_names_its_trial_2026_08_23.py` | Checks benchmark PMIDs against title cache/trial names. | Reads benchmark JSON/title cache, not v13 output. | Lines 39-42 read `PUBLISHED_META_BENCHMARKS.json` and PubMed title cache; lines 49-63 derive claims; lines 138-143 fail. |
| `scripts/gate_certainty_column_four_states_2026_08_23.py` | Checks certainty-column states in SSOT objects. | Reads `ssot/*/*.json` and `grade_authority` fields. | Lines 70-78 read the SGLT2 object/all SSOT objects; lines 96-145 resolve certainty state. |
| `scripts/gate_integrity.py` | Checks gate scripts themselves for failability/integrity. | Source-code gate, not page-output gate. | Lines 293-313 and 377-409 inspect scripts/hooks; line 450 returns failure status. |
| `scripts/gate_no_grammar_seam_in_stored_prose_2026_08_23.py` | Checks stored prose in SSOT JSON. | Reads `ssot/**/*.json`, explicitly not v13 output. | Lines 23 and 49-51 define SSOT scan; lines 115-120 and 141 refuse. |
| `scripts/gate_no_new_schema_synonym_2026_08_23.py` | Checks new schema synonyms in SSOT JSON. | SSOT schema gate. | Lines 150-155 scan `ssot/*/*.json`; lines 170-171 exit. |
| `scripts/gate_no_prose_bypasses_the_tidy_2026_08_23.py` | Checks source builder/projector paths for prose bypasses. | Source-code gate, not output. | Lines 36, 84, and 112-128 inspect `ssot/build_tabbed.py` and `ssot/paper_projector.py`. |
| `scripts/generator_stamp_gate.py` | Checks hardcoded gated pages for SSOT build stamp/command. | Hardwired to `ssot/build_tabbed.py` and selected pages, not v13 generator/output. | Lines 41-49 define build module/command/gated pages; lines 66-91 check stamps; lines 117-123 fail. |
| `scripts/harness_gate.py` | Checks exported artefact JSON from the pre-push harness. | Consumes exported SSOT artefact JSON, not v13 HTML pages. | Lines 51-77 parse artefact args/read JSON; lines 133-145 reject zero checks; lines 170-185 fail. |
| `scripts/headline_reproducible_gate.py` | Checks headline reproducibility from object JSON. | Object JSON gate. | Lines 47-49 and 313-321 define/read object corpus; line 351 returns status. |
| `scripts/identity_by_registration_gate.py` | Checks trial identity against known registrations. | Object JSON plus `ssot/KNOWN_REGISTRATIONS.json`. | Lines 126-137 define those inputs. |
| `scripts/identity_gate.py` | Checks object identity against source documents. | Requires object JSON and source docs. | Lines 20, 75, 105-109, and 167-176 define object/source inputs. |
| `scripts/k_consistency_gate.py` | Checks k consistency inside object JSON. | Object JSON gate. | Lines 22, 198, and 343-355 define/read object inputs. |
| `scripts/known_answer_gate.py` | Runs fixed evidence-batch known-answer suites. | Fixed suite/harness gate, not v13 output. | Lines 33-39 define suites; lines 45-67 run subprocesses; lines 78-81 refuse. |
| `scripts/marker_prefix_gate.py` | Checks marker prefixes in SSOT objects. | Reads `ssot/<d>/<d>.json`. | Lines 47-53 read SSOT objects; lines 81-85 refuse. |
| `scripts/pooled_point_in_achievable_range_gate.py` | Checks object pooled points against benchmark constraints. | Requires object JSON and benchmark files. | Lines 59-60 define usage; lines 447-448 read object; lines 439 and 483 return failure. |
| `scripts/pooled_value_gate.py` | Checks page value display against object pooled fields. | Authority is `results.by_outcome.*.pooled` in object JSON. | Lines 30-44, 61-80, and 83-102 define object/page comparison. |
| `scripts/precision_sample_gate.py` | Checks canonical JSON precision/sample artifacts. | Reads `*.html.canonical.json`, not v13 HTML. | Lines 92-105 and 144-167 glob/read canonical objects. |
| `scripts/prose_claim_gate.py` | Checks prose claims in object JSON. | Object JSON gate. | Lines 28-29 and 270-289 define SSOT/examples; lines 354-355 read object. |
| `scripts/protocol_subject_gate.py` | Checks protocol/page subject alignment from object/page pairs. | Requires SSOT `PAGE_MAP` or object JSON pairs. | Lines 214-230 derive pairs from `ssot/PAGE_MAP.json`/`ssot/*/*.json`; lines 270-303 parse CLI. |
| `scripts/registration_identity_gate.py` | Checks registration identity from object/fetch. | Object JSON plus registry fetch gate. | Lines 53-55, 270-295, and 309-315 define object/fetch flow. |
| `scripts/search_recall_gate.py` | Checks search record recall against object/corpus. | Requires search record JSON and object JSON. | Lines 55-60 and 76-83 define search/object/corpus inputs. |
| `scripts/section_manifest_gate.py` | Checks section manifest against object/page/docmodel. | Requires object JSON and docmodel JSON. | Lines 155-170 define inputs; line 178 returns failure. |
| `scripts/standard_version_agreement_gate.py` | Checks PAGE-STANDARD and build-to-standard version agreement. | Source/doc standard gate. | Lines 4, 45, 55, and 129-130 define/refuse version agreement. |
| `scripts/subject_is_experimental_gate.py` | Checks CT.gov subject intervention role. | Registry/fetch gate keyed by subject/NCTs, not output HTML. | Lines 62-63, 75, 131-133, and 214 define fetch/refusal. |
| `scripts/subject_match_gate.py` | Checks page/object subject consistency. | Requires page plus SSOT object. | Lines 70, 99-105, 112, and 120 define object/page check. |
| `scripts/verdict_gate.py` | Checks live page verdict against object verdict fields. | Object/live GitHub Pages gate, not v13 generated local output. | Lines 42-44 fix live base URL; lines 48-83 derive object reason; lines 86-123 fetch/read; lines 126-138 parse usage. |
| `scripts/withdrawal_reason_gate.py` | Checks withdrawal reasons in SSOT objects. | SSOT object gate. | Lines 268-278 scan/read `ssot/*/*.json`; line 299 returns. |
| `scripts/ssot_net_deletion_check.py` | Checks staged SSOT JSON net deletion. | Explicitly says it only covers staged `ssot/**/*.json`, not pages. | Line 21 says staged `ssot/**/*.json`; line 35 says nothing outside `ssot/`; lines 55-57 filter diff; line 191 returns. |
| `.githooks/pre-commit-staging` | Refuses staged paths outside narrow repo lanes. | Path-scope hook, not output semantics. | Lines 4-8 define allowed paths; lines 9-15 refuse. |
| `scripts/lint_subprocess_decode.py` | Checks subprocess decode hazards in source. | Source-code lint, not output. | Lines 34-39 define source scope; lines 116 and 120-124 implement baseline/refusal. |
| `scripts/lint_escape_hazards.py` | Checks source/text escape hazards. | Source-code/text lint, not generated page-output logic. | Lines 53, 97, and 129-132 define/refuse hazards. |
| `scripts/lint_gate_can_fail.py` | Checks gate scripts for actual failure paths. | Gate-source meta-lint, not v13 output. | Lines 119-128 scope verdict scripts; lines 168-186 walk scripts; lines 222-262 refuse. |
| `scripts/lint_no_false_allclear.py` | Checks source for false all-clear/census patterns. | Source-code lint. | Lines 105-112 scan source; lines 129-133 refuse. |
| `scripts/lint_question_is_a_question.py` | Checks questions in SSOT/cache. | Reads SSOT/cache fields, not output HTML. | Lines 48, 97, 119, and 203-226 define/refuse. |
| `scripts/lint_block_contradicts_object.py` | Checks SSOT blocks against their own object. | SSOT object gate. | Lines 39, 140, and 157-160 read/refuse objects. |
| `scripts/lint_restraint.py` | Checks restraint fields in SSOT/cache. | SSOT/cache gate. | Lines 69, 94, 114, 166, 218, and 229-234 define/refuse. |
| `scripts/lint_criteria_fingerprint.py` | Checks criteria fingerprint/proof controls. | Criteria/source instrument gate, not v13 output. | Lines 116-119 and 154-158 define proof/refusal. |
| `scripts/lint_string_where_collection_expected.py` | Checks source/SSOT code for string-vs-collection hazards. | Scans `ssot` and `scripts`, not output pages. | Lines 58, 136-178, and 233-235 define/refuse. |
| `scripts/lint_pmid_names_two_trials.py` | Checks PMID/trial naming in SSOT objects. | SSOT object gate. | Lines 119-121, 135-149, and 230-233 define/refuse. |
| `scripts/lint_manuscript_whole_document.py` | Checks manuscript projection from SSOT objects. | Projects from SSOT, not v13 generated pages. | Lines 103-110 scan SSOT; lines 143-145 refuse. |
| `scripts/lint_p46_refusal_is_producibility.py` | Ratchets templated refusal states in SSOT. | SSOT object gate. | Lines 34-36, 133-143, and 209-215 define/refuse. |
| `scripts/lint_pooled_point_is_displayable.py` | Checks displayability of pooled points in SSOT/projector. | SSOT object/projector gate. | Lines 47, 74, and 136-140 define/refuse. |
| `scripts/lint_search_pagination_declared.py` | Checks search pagination declarations in SSOT. | SSOT object gate. | Lines 51, 70, and 108-112 define/refuse. |
| `scripts/lint_primary_by_position.py` | Checks source for positional primary-outcome reads. | Source-code lint. | Lines 103, 135, 165-184, and 193 define/refuse. |
| `scripts/lint_composite_by_components.py` | Checks component endpoint consistency in SSOT. | SSOT object gate. | Lines 53, 151, and 227-234 define/refuse. |
| `scripts/lint_withholding_asked.py` | Checks withholding/refusal vocabulary in SSOT. | SSOT object gate. | Lines 44, 94, 110-113, and 149-156 define/refuse. |
| `scripts/lint_withholding_direction_paired.py` | Checks paired withholding direction in SSOT. | SSOT object gate. | Lines 55, 83, 119, and 162-172 define/refuse. |
| `scripts/lint_instrument_declares_a_control.py` | Checks audit/lint/gate source for declared controls. | Source-code meta-lint. | Lines 53-61, 77-81, and 185-194 define/refuse. |
| `scripts/audit_exclusion_by_absence.py` | Audits exclusion-by-absence guards in source/SSOT. | Source/SSOT audit gate, not output HTML. | Lines 77-86, 102-113, 167-177, and 321-348 define/refuse. |
| `scripts/audit_class_mechanisation.py` | Checks mechanisation of class controls. | Meta/control gate, not v13 output. | Lines 13-24, 188, and 234-241 define/refuse. |
| `scripts/lint_arm_roles_contradict_the_object.py` | Checks arm-role contradictions in SSOT. | SSOT object gate. | Lines 150-155, 114-124, and 282 define/refuse. |
| `scripts/audit_procedural_constants_all_surfaces_2026_08_23.py` | Checks procedural constants in source literals. | Source literal gate. | Lines 52-54, 98, and 186 define/refuse. |
| `scripts/regression_guard.py` | Enforces high-water no-regression ledger for SSOT objects. | Reads canonical object fields and `evidence/LEDGER.json`, not v13 output pages. | Lines 1-22 define no-regression invariant; lines 55-95 derive object state; lines 260-307 read/check objects; lines 404-409 make exit status load-bearing. |
| `scripts/lint_arm_role_is_read_not_sorted_2026_08_23.py` | Checks source for deriving treatment/control by sorted arm position. | Source-code lint over `scripts`/`ssot`, not generated pages. | Lines 101-115 scan `scripts` and `ssot` Python files; lines 130-132 refuse. |
| `scripts/lint_cascade_arithmetic.py` | Checks `k_cascade` arithmetic inside SSOT objects. | Requires `ssot/<topic>/<topic>.json` and `k_cascade`. | Lines 44-45 set `SSOT`; lines 55-69 read `k_cascade`; lines 154-162 read objects; lines 187-192 refuse. |
| `scripts/lint_encoding_defaults.py` | Checks source for machine-read writes missing explicit newline. | Source-code lint over `scripts`, not output corpus validation. | Lines 69-76 scan scripts; lines 89-94 refuse new hazards. |
| `scripts/lint_hr_between_or_and_rr.py` | Checks stored HRs against RR/OR from SSOT arm counts. | Requires SSOT `arms[]` and `by_outcome` fields. | Lines 49-57 read SSOT objects; lines 61-89 compute from arms/effects; lines 112-117 refuse. |
| `scripts/lint_method_claim_has_a_field.py` | Checks manuscript method claims resolve to fields on SSOT objects. | Requires SSOT manuscript/object fields. | Lines 221-236 scan SSOT objects/manuscript fields; lines 248-254 refuse. |
| `scripts/lint_object_write_is_atomic.py` | Checks source writers use atomic write paths for corpus content. | Source-code writer lint, not output page content. | Lines 144-148 scan `ssot` and `scripts` Python; lines 187-197 refuse in `--gate` mode. |
| `scripts/lint_ours_matches_pool.py` | Checks first-person fields in SSOT objects against object pooled values. | Requires SSOT object fields and pooled results. | Lines 209-217 read SSOT; lines 243-246 refuse mismatches. |
| `scripts/lint_pipeline_exit_status.py` | Checks hooks/scripts for shell pipeline status hazards. | Hook/source lint, not output page validation. | Lines 76-87 scan `.githooks`/`scripts`; lines 100-106 refuse baseline rise. |
| `scripts/lint_published_over_false_estimand.py` | Ratchets pooled estimates over `estimand_established: false`. | SSOT results schema gate. | Lines 61-71 scan `ssot/*/*.json`; lines 123-135 refuse new cases in gate mode. |
| `scripts/lint_reader_facing_sections.py` | Projects SSOT papers and ratchets stub/refused reader-facing sections. | It does not read delivered v13 pages; it projects from SSOT via `paper_projector`. | Lines 62-81 import projector/read SSOT; lines 134-137 refuse baseline rise. |
| `scripts/lint_registration_counts_arm_order.py` | Checks `registration_primary_counts` labels against SSOT `arms[]`. | Requires SSOT trial count and arm-role fields. | Lines 41-57 read SSOT/trial fields; lines 188-193 refuse baseline rise. |
| `scripts/lint_refusal_citation_resolves.py` | Checks refusal field-path citations resolve inside the same SSOT object. | Requires SSOT object field paths; v13 HTML does not provide resolvable object paths. | Lines 98-110 parse `--gate` and read `ssot/*/*.json`; lines 127-156 resolve/compare cited paths; lines 173-175 refuse. |
| `scripts/lint_self_describing_safety_claim.py` | Ratchets self-describing safety claims in SSOT strings. | SSOT string-field gate. | Lines 75-91 read SSOT objects/strings; lines 121-143 compare baseline and refuse. |
| `scripts/lint_unsubstituted_tokens.py` | Ratchets unsubstituted template tokens in SSOT prose. | Reads SSOT JSON text, not v13 HTML output. | Lines 26-35 define SSOT/TOKEN; lines 41-52 read SSOT; lines 63-68 refuse. |
| `scripts/lint_zero_is_a_value_2026_08_23.py` | Checks source projectors for numeric truthiness hazards. | Source-code lint against fixed SSOT/projector files. | Lines 46-47 define source files; lines 97-106 scan them; lines 127-131 refuse. |
| `scripts/audit_analysis_population_estimand.py` | Checks pooled outcomes against registered analysis-population text. | Requires SSOT trials/results plus `outputs/nct_primaries.json`. | Lines 44 and 79-83 read registry-primary cache; lines 90-98 read SSOT; lines 120-133 inspect pooled outcomes; line 179 blocks in gate mode. |
| `scripts/audit_manuscript_prose_doors.py` | Checks source projector reads of `manuscript.*` fields. | Source-code/projector audit, not output HTML. | Lines 34-35 set target source files; lines 93-107 read source; lines 163-165 block in gate mode. |
| `scripts/audit_outcome_paths_call_both.py` | Checks projector outcome-emitting loops call both referral/findings helpers. | Source-code projector gate. | Line 33 sets `ssot/paper_projector.py`; lines 81-87 parse source; lines 126-130 classify paths; line 166 blocks in gate mode. |
| `scripts/sweep_rendered_interval_is_the_house_interval.py` | Checks delivered pages against SSOT stored Hartung-Knapp intervals. | Requires SSOT stored interval fields and page/object pairing; v13 output alone lacks that object authority. | Lines 16-24 define house/raw/delivered comparison; lines 312-329 compare rendered pairs; lines 370-382 block in `--gate` mode. |
| `scripts/sweep_r_output_labels_reproduce.py` | Checks stored `r_output` labels reproduce from SSOT object fields. | Requires SSOT `r_output` and `results` fields. | Lines 18-27 define labels vs object fields; lines 226-232 count SSOT objects/blocks; lines 252-255 block in `--gate` mode. |
| `scripts/prove_abstract_argument_is_never_composed.py` | Checks projected SSOT abstract argument provenance. | Projects SSOT objects; does not read v13 HTML output. | Lines 1-25 define projected abstract checks; lines 89-98 read SSOT; lines 164-168 block in `--gate` mode. |
| `scripts/prove_figures_reach_the_paper.py` | Checks SSOT paper figures/refusal-in-place via projector. | Projects SSOT objects/figures, not v13 output pages. | Lines 1-29 define figure/refusal checks; lines 44-49 call `paper_projector`; lines 140-156 read SSOT; lines 170-176 block in gate mode. |
| `scripts/prove_no_value_lost.py` | Checks SSOT leaf values against `HEAD`. | Reads `ssot/*/*.json` and `git show HEAD:<object>`, not output HTML. | Lines 1-15 define SSOT value-loss check; lines 69-75 read SSOT/current HEAD; lines 123-125 block in gate mode. |

## Needed v13 Output Checks Missing Today

No existing gate, as written, can fully supply these checks by only repointing an input glob:

1. v13 output completeness and hub reachability.
   - Needed read set: `generate_living_ma_v13.py` `APPS` output declarations, or a generated v13 manifest; actual generated `*_REVIEW.html` files under v13 output directories; v13 hub/index HTML.
   - Required assertion: every intended v13 output page exists, every reader-facing page expected in the corpus is linked from the v13 hub graph, and every hub link resolves. Existing link gates can resolve links, but they do not know the v13 intended-output set unless fed a v13 manifest. `ssot/PAGE_MAP.json` is the wrong source.

2. v13 output provenance/stamp gate.
   - Needed read set: generated v13 HTML pages plus an embedded v13 build stamp or sidecar manifest containing generator path, generator commit/hash, template path/hash, `OUTPUT_BASE`, and optional staging profile path/hash.
   - Existing `build_stamp_gate.py`/`generator_stamp_gate.py` are tied to SSOT build stamps and `ssot/build_tabbed.py`; v13 does not emit their expected stamp.

3. v13 embedded-data identifier/provenance gate.
   - Needed read set: generated v13 HTML `realData`, `AUTO_INCLUDE_TRIAL_IDS`, NCT/PMID/DOI/trial-name strings, embedded citations/source snippets, and any staging-profile-derived overrides.
   - Existing ID/provenance gates mostly read SSOT object fields such as `inputs.trials`, `results.by_outcome`, `citations`, or `search`. They structurally cannot validate v13 pages unless v13 output exposes an equivalent machine-readable contract or sidecar.

4. v13 optional staging-profile disclosure gate.
   - Needed read set: the optional `C:\Projects\rapidmeta-staging\profiles\{storage_key}.json` files if used, or preferably a repo-local declared profile manifest, plus generated page bytes.
   - Existing gates do not know whether this hardcoded outside-repo profile hook changed a page. A deterministic gate should fail closed if a profile influenced output but is not declared, hashed, and available.

5. v13 1,314-page census gate.
   - Needed read set: actual v13 output directories/hubs plus a source-of-truth manifest of the intended 1,314-page corpus.
   - The current generator source enumerates 26 app writes, while its own guard comment records a historical 1,314-page blast radius. A gate needs to read the real intended corpus inventory rather than infer coverage from current SSOT objects or from memory.

## Coverage Statement

An `ssot/**/*.json` gate has no coverage over v13 output unless the v13 output is independently connected to it. The pre-push hook itself encodes the same point: when changed pages have no SSOT object, lines 167-171 warn that the harness did not run and "That is not coverage." That rule applies directly here.
