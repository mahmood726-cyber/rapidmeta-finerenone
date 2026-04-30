# Living-MA Pilot Debrief — 2026-04-30

Pilot dashboard: `DOLUTEGRAVIR_ART_SSA_REVIEW.html`
Commits: spec-lock + 3 phases + Playwright smoke (5 commits)
Status: **Pilot landed cleanly. Portfolio sweep is a separate decision.**

## What got built

| Module | Lines | Tests | Pass |
|---|---|---|---|
| `regex_helpers.js` (defensive guards) | 220 | 25 | 25/25 |
| `ctgov_fetch.js` (v2 search + structured extract) | 290 | 10 | 10/10 |
| `pubmed_fetch.js` (NCT-first auto-search + abstract parse) | 145 | 5 | 5/5 |
| `augment_ui.js` (UI glue + state.trials integration) | 410 | (Playwright e2e) | — |
| **Total** | **1,065** | **40 unit + e2e** | **40/40** |

Plus 5 lines added to `DOLUTEGRAVIR_ART_SSA_REVIEW.html` (4 `<script>` tags).

## Regression contract — verified

| Check | Expected | Observed |
|---|---|---|
| Pre-change pooled HR/CI with 0 user-added trials | bit-identical | 1.11 (1.07–1.16), k=3, n=1,743 ✓ |
| `audit_v65_engine_coverage.py` | 164/164 fully compliant | **164/164** ✓ |
| `audit_mitt_vs_allocated.py` | no new flags | no new flags ✓ |
| `audit_continuous_conventions.py` | no new flags | no new flags ✓ |
| Sentinel `cochrane_v65_invariants.py` | 0 verdicts | **0 verdicts** ✓ |
| Console errors on page load (no user-added) | 0 | 0 ✓ |
| Curated-only toggle subtracts user-added back to baseline exactly | yes | **yes** (HR back to 1.11/1.07/1.16) ✓ |

## Live exercise findings

- **CT.gov v2 search** returned 35 candidate trials for the dolutegravir+tenofovir+HIV
  query, all properly dedup-filtered against the existing curated NCTs. First wave
  surfaced cabotegravir/rilpivirine LA, B/F/TAF, SWORD-1, etc. — all topical.
- **PubMed NCT auto-search** worked for the trials we tested, finding the lowest-PMID
  primary publication.
- **Auto-prefill of outcomes** (tE/cE/tN/cN/HR+CI) succeeded only when CT.gov had
  results posted AND the PubMed abstract had a parseable HR statement. For SWORD-1 —
  a real registered trial without a results module on CT.gov — the modal correctly
  surfaced empty fields with `[NONE]` confidence badges, requiring the user to
  hand-enter from the publication. **This is the right behavior**: better to ask than
  to guess.
- **Validation modal** correctly enforced: tE ≤ tN, cE ≤ cN, hrLCI ≤ HR ≤ hrUCI,
  apostrophe screen on user-typed strings, dual-reviewer-must-differ.
- **Synthetic add → engine pool** worked end-to-end: pushed `userAdded:true` trial
  to `state.trials`, engine recomputed (k=3 → k=4, HR shifted from 1.11 to 0.91).
- **Curated-only toggle** put it back exactly: k=4 → k=3, HR back to 1.11
  bit-identical. The regression detector works.

## Surprises / scope drift

1. **CT.gov v2 filter syntax**: the v1-style `filter.advanced=AREA[StartDate]RANGE[...]`
   returns HTTP 400 in v2. Switched to client-side date filter on the returned
   `startDate` field. Smaller blast radius, same effect.
2. **Date-string compare**: works for ISO `YYYY-MM-DD` and `YYYY-MM` but would
   break on `YYYY` alone. CT.gov returns mostly month-precision in this corpus, so
   no practical issue, but the audit script could add a dateFrom-format guard.
3. **Most candidate trials lack auto-fillable outcomes.** ~63.6% of CT.gov-registered
   trials publish results (`lessons.md` Trial-to-publication-linkage finding); of
   those, fewer have structured CT.gov `outcomeMeasures` populated. So the
   "user types from the abstract" path is the realistic primary use-case, not the
   exception. Worth noting in the user-facing copy.
4. **"35 candidates"** is high for a single dashboard query. The user will need
   PICO-keyword discipline to narrow this. The `query` field in `protocol`
   becomes the primary lever — and many existing dashboards have `query: ''`.
   Portfolio sweep will need to backfill PICO query strings per dashboard.

## Lessons added to `~/.claude/rules/lessons.md`

(Already written this session.)
- **Apostrophe inside JS single-quoted string** — codemods that inject text
  must screen for `'` or use `\'`. The 27-dashboard incident is the source.

## Decision: portfolio sweep?

**Recommendation: HOLD on the sweep until at least one real living-MA add is made
end-to-end by a human user (not synthetic).** The Playwright smoke verifies the
plumbing, but it doesn't verify:
- A real user can navigate the modal without confusion.
- The auto-prefill confidence badges are intuitive.
- The dual-sign UX matches existing screening patterns enough that Makerere
  cohort users can use it.

Suggested next steps in priority order:

1. **Human pilot run** — Mahmood adds one real new RCT to DOLUTEGRAVIR_ART_SSA via
   the augment, end-to-end. Note any UX friction.
2. **Backfill `protocol.query` strings** for the 5–10 dashboards that have stable,
   well-defined PICO queries. These are the natural sweep candidates.
3. **Sweep code path**: `scripts/sweep_living_ma_to_portfolio.py` — a codemod that
   adds the 4 `<script>` tags before `</body>` in any dashboard whose `protocol.query`
   is non-empty. Idempotent (skips if tags already present). Same pattern as the
   v6.5 backfill scripts.
4. **Portfolio Sentinel rule**: a new rule that flags any dashboard with the augment
   installed but `protocol.query === ''`. Empty query = no useful search.

## Files committed this session

- `outputs/living_ma_augment_spec.md` (spec)
- `scripts/living_ma_augment/regex_helpers.js` + tests
- `scripts/living_ma_augment/ctgov_fetch.js` + tests
- `scripts/living_ma_augment/pubmed_fetch.js` + tests
- `scripts/living_ma_augment/augment_ui.js` (UI glue)
- `DOLUTEGRAVIR_ART_SSA_REVIEW.html` (4 `<script>` tags)
- `outputs/living_ma_pilot_debrief.md` (this doc)

## Re-running the pilot

```
cd C:/Projects/Finrenone
python -m http.server 8765
# browser: http://127.0.0.1:8765/DOLUTEGRAVIR_ART_SSA_REVIEW.html
# Sources tab → "Living-MA: Re-query CT.gov for new RCTs" panel.
```

Unit tests:
```
cd scripts/living_ma_augment
node test_regex_helpers.js   # 25/25
node test_ctgov_fetch.js     # 10/10
node test_pubmed_fetch.js    # 5/5
```

NEW-TOPIC FREEZE remains in effect until a human-pilot run validates UX.
