# Peer-review harvester: coverage and comparison contract

## Incident evidence

Inspected run: [38535480296](https://github.com/mahmood726-cyber/rapidmeta-finerenone/actions/runs/38535480296), job 115757214126, source commit `95522c383fae934ad70e4d87dcca402cc532897c`.

The actual job log reports **1,427 discovered review pages: 1,043 successful, 103 skipped and 281 failed**. Of the failures, **279 were `page.waitForFunction` readiness timeouts and two were `page.goto` navigation timeouts**. These are the historical run's counts; no later test changes them.

The workflow interpolated the unavailable `github.run_started_at` value as an empty string. The log shows `OUT_DIR: findings/` and `--current "findings/"`. That mixed the new records with old snapshots and unrelated audit JSON. At the inspected commit the root contains 2,184 historical per-page records, four unrelated arrays (`default_outcome_broken.json`, `multiarm_audit.json`, `pmid_list.json`, `pmid_mismatches.json`) and two unrelated dictionaries (`pmid_groups.json`, `pmid_titles.json`). They are not a single complete previous harvest.

The old loader admitted every parsed JSON value and silently skipped invalid JSON. Its comparison assumed a dictionary, so an unrelated array caused `AttributeError: 'list' object has no attribute 'get'`. An error record or skipped record could also be read as empty findings, incorrectly implying that previous concerns had resolved.

Separately, the timeout was supplied as Playwright's second `waitForFunction` argument, which is the predicate argument, instead of the third argument containing options. The intended 15-second readiness limit therefore remained the default 30 seconds. Navigation used `networkidle`, which waited on unrelated network activity.

Source inspection of the failed pages found 143 static store reviews, 89 redirect stubs and eight dose-response reviews using a different runtime. Those formats do not provide this harvester's legacy peer-review API. The remaining 41 failures include 39 additional readiness failures requiring page-specific diagnosis and the two navigation timeouts. Unsupported formats are now explicit skips, not successes. Unknown runtime failures remain failed records with diagnostics and bounded retries.

## Output schemas

Each run uses a new directory `findings/<UTC timestamp>-<run id>-<attempt>/`. Local defaults include the full timestamp. Reusing a nonempty directory or the mixed `findings/` root is rejected.

Every processed page has its original identity and one of these states:

| Status | Record content | Comparison meaning |
| --- | --- | --- |
| `ok` | Actual `findings.editor.decision`, `findings.reviewers`, captured real analysis state and attempt diagnostics | Observed reviewer output |
| `skipped` | Explicit reason; no successful findings | Unassessed; never an empty successful review |
| `failed` | Error, failure phase and attempt diagnostics | Unassessed; never resolved |
| `pending` | Manifest entry for a discovered page not processed before a fatal interruption | Unassessed; no record file required |

`_harvest.json` records the declared page inventory, start/end times, source SHA and run identifiers, full/subset scope, page outcomes and exact `ok`, `skipped`, `failed`, `pending` and `total` counts. It is written before browser launch and updated atomically after every page and on normal/fatal completion. A cancelled job retains the last inventory and completed outcomes in its working directory; upload remains subject to GitHub runner cancellation/availability.

The comparator accepts per-page dictionaries and arrays **of complete harvest record objects with explicit app identities**. The harvester itself writes dictionaries. Unrelated audit arrays/dictionaries, scalars, corrupt JSON, duplicate app identities and malformed review structures are rejected with a file/element/field location. Reviewer entries sharing a role are merged for concern comparison rather than overwriting each other. Original finding strings are preserved.

Legacy `{app,error,timestamp}`, `findings.error`, `findings.skipped` and missing/null findings are classified as unobserved failures/skips. They cannot supply evidence of resolution. Legacy snapshots without a coverage manifest are never promoted to a trusted complete baseline.

## Completeness policy

A complete snapshot requires full discovered-page scope, a finished timestamp, at least one page and **every page successfully reviewed**. Skips, failures, pending pages and intentionally selected subsets all make a run incomplete. The comparator validates counts, page identities and status/record consistency rather than trusting the complete flag.

For incomplete/invalid runs, the workflow retains raw records and the manifest in an artifact, writes a coverage summary, blocks the issue and snapshot-commit steps, and reports failure at the final completeness gate. This deliberately means the current portfolio's unsupported pages continue to prevent a complete-harvest success. They need appropriate supported harvesting or an explicitly reviewed change of scope; this repair does not invent their peer-review findings or exempt them to turn CI green.

The first verified complete run establishes a baseline without calling all existing concerns newly identified. Later runs compare against the newest verified complete snapshot that finished before the current run began. A newer partial run cannot replace it. Pages absent from the current scope remain unassessed, not resolved. New pages are identified as newly observed. A resolved concern means **no longer emitted by that page's reviewer**, not independent adjudication that the scientific issue has been corrected.

Reports from older runs are removed before validation. Issue publication uses validated step outputs, not the mere presence/hash of a tracked Markdown report. Evidence artifacts are retained for 90 days. Complete snapshots continue to be committed by the existing bot workflow; partial snapshots remain artifacts and do not replace the repository baseline.

## Verification

Local verification at preparation of this change:

- 25 Python regression tests: dictionary/array inputs, corrupt or unexpected data, missing findings, duplicate roles, changed editorial decisions, new/resolved concerns, removed pages, incomplete/future/unverified baselines, count/scope validation and stale report removal.
- Nine Node unit tests: real timeout argument placement, fresh-page retries, errors versus skips, format reasons, exact manifest/page accounting, fatal launch failures and overwrite prevention.
- Seven real Chromium browser regression tests: delayed runtime, ongoing background traffic, recovered navigation timeout, missing runtime/analysis/API, reviewer exceptions, malformed outputs and HTTP failures. Local browser: Chromium 153.0.8010.0; Playwright 1.58.2. The PR workflow also runs these fixtures using Playwright's matching Chromium.
- All 2,184 historical per-page records validate individually: 1,768 `ok`, 229 explicit missing-analysis skips and 187 errors (129 page errors plus 58 nested reviewer errors). These historical counts are distinct from the failed run's live totals.
- Six unchanged representative repository pages: three successful reviews (ABALOPARATIDE_OSTEO_AUTO_FULL, SUMATRIPTAN_MIG_AUTO_FULL and ZILUCOPLAN_GMG_AUTO_FULL), three explicit unsupported-format skips (ABLATION_AF, ALCOHOL_BC_DOSE_RESP and ALIROCUMAB_LIPID_AUTO). The latter two successful pages were the failed run's navigation timeouts. This is a sample, not a comprehensive reharvest. External API request failures encountered locally are retained in diagnostics.

Run the regressions locally:

```sh
python -m unittest discover -s tests -p test_diff_findings.py -v
node --test tests/test_harvest_findings.mjs
npm install --no-save --package-lock=false playwright@1.58.2
npx playwright install --with-deps chromium --only-shell
node --test tests/test_harvest_findings_browser.mjs
```

For a selected local page sample, set `HARVEST_APPS` to a comma-separated list. Such runs are explicitly `subset` scope and cannot publish a complete comparison. No HTML review, canonical scientific data, analytic engine or existing scientific finding is modified by this repair.

API reference: [Playwright Page](https://playwright.dev/docs/api/class-page#page-wait-for-function) documents the third-argument timeout options; [navigation readiness](https://playwright.dev/docs/api/class-page#page-goto-option-wait-until) documents `domcontentloaded` and discourages `networkidle` as a readiness criterion.
