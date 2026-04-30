# Living-MA Augment — Pilot Spec v0.1

Date: 2026-04-30
Pilot dashboard: `DOLUTEGRAVIR_ART_SSA_REVIEW.html`
Status: **DRAFT — spec-lock in progress, no code yet**

## Goal

Convert the dashboard portfolio from "static curated MA" to "true
living MA" by adding an in-browser flow that:

1. Re-queries CT.gov v2 for new RCTs matching the dashboard's PICO.
2. Auto-prefills as much as possible from CT.gov structured endpoints
   (no narrative-text guessing where avoidable).
3. Defensively regex-extracts the rest from the abstract / publication
   with guards against the failure modes documented in
   `~/.claude/rules/lessons.md` (negated-counts, mITT-vs-allocated,
   multi-HR disambiguation, LSMD/MMRM declaration).
4. Surfaces auto-extracted values + source snippets side-by-side and
   asks the user to **review** rather than type.
5. Requires dual-reviewer signoff before any user-added trial enters
   the analysis pool.
6. Flags every user-added trial with `userAdded: true` + an audit-log
   `_seal()` hash.
7. Provides a one-click "curated-only" toggle in the Analysis tab so
   any reviewer can see whether the user-added trial *changed the
   conclusion* (the regression detector).

## Non-goals (this pilot)

- Editing existing curated `realData` entries. Out of scope.
- Pooling trials from outside CT.gov (e.g. EU CTR, ChiCTR). Out of
  scope; the pilot is CT.gov-only.
- Any change to the engine math (REML/HKSJ/Q-profile/PI/MH/ROB-ME).
  Engine code is untouched.
- Any change to the existing screen → extract → dual-sign flow on
  pre-curated trials. The augment is purely **additive**.
- Portfolio sweep across 170 dashboards. The pilot validates the
  pattern on ONE dashboard; sweep is a separate decision.

## Pilot dashboard pick

`DOLUTEGRAVIR_ART_SSA_REVIEW.html` was chosen because:
- Narrow, well-defined PICO (sub-Saharan Africa first-line ART,
  post-2015 inclusion).
- Three trials already (ADVANCE, NAMSAL, INSPIRING) — small enough
  to verify the additive-overlay UI visually.
- Binary HR primary endpoint — simplest engine path.
- Stable topic — adding a fourth trial is unlikely to dramatically
  flip the conclusion, which is the right property for a regression
  test (we can see if the UI works *correctly* without the change
  being so dramatic that signal and bug are indistinguishable).

## Architecture

### High-level

```
[user clicks "Search for new RCTs" in Sources tab]
        |
        v
[searchAugment.fetchCandidates(query, excludeNcts, dateFrom)]
   - CT.gov v2 /studies?query.term=... &filter.studyType=INTERVENTIONAL
     &filter.phase=PHASE3 &filter.advanced=AREA[StartDate]RANGE[2015,*]
   - dedup against state.trials NCTs
   - dedup against protocol.auto_include_ncts
        |
        v
[candidate panel renders]
   - per card: NCT, title, phase, status, sponsor, completion, "Validate" button
        |
        v
[user clicks Validate → modal opens]
   - Tab 1: CT.gov metadata (read-only): name, phase, year, intervention,
     comparator, study population, randomization ratio
   - Tab 2: Auto-prefilled outcomes panel
       * if CT.gov outcomeMeasures has primary results → tE/cE/tN/cN
         pre-filled with confidence=HIGH
       * else regex from PMID abstract → confidence=MEDIUM, source
         snippet shown
       * each field has: auto-value | source | "edit" button
   - Tab 3: ROB checklist (user-only; no auto-extract)
   - Tab 4: Dual-reviewer sign-off block
        |
        v
[user clicks "Add to dashboard"]
   - validation: tE<=tN, cE<=cN, hrLCI<=publishedHR<=hrUCI, all numeric
   - dual-sign required (cannot skip)
   - state.trials.push({ ...trial, userAdded: true, _addedAt: ts,
                          _addedBy: reviewerId, _seal: hash })
   - localStorage persists immediately
        |
        v
[engine recomputes via getAnalysisTrials]
   - userAdded:true entries flow through unchanged
   - forest plot renders with USER-ADDED yellow pill
   - PRISMA flow shows "Added live: 1"
        |
        v
[Analysis tab: "Curated only" toggle visible if any userAdded exists]
   - ON: re-run pool excluding userAdded → show pre-change HR + delta
   - OFF: pool with userAdded (default after add)
```

### Modules (JS, namespaced under `RapidMeta.searchAugment`)

| Module | Responsibility | Lines (est) |
|--------|----------------|-------------|
| `fetchCandidates(query, excludeNcts, dateFrom)` | CT.gov v2 fetch + dedup | ~80 |
| `extractStructured(ctgovStudy)` | Pull participantFlowModule + outcomeMeasures + protocolSection into a trial-shaped object | ~150 |
| `extractFromAbstract(pmid)` | PubMed E-fetch + defensive regex helpers | ~250 |
| `regexHelpers.{negationGuard, multiHrDisambiguator, mittDetector, lsmdDetector}` | Per-helper guards from lessons.md | ~200 |
| `validateTrialUI(candidate)` | 4-tab validation modal | ~250 |
| `addUserTrial(validated, signoff)` | Validation + state push + localStorage | ~80 |
| `renderCuratedToggle(c)` | Curated-only delta panel | ~50 |
| `userAddedBadge(trialEl)` | Visible yellow pill in forest plot, screen UI, demographics | ~30 |
| **Total** | | **~1090** |

Plus ~200 lines of Playwright smoke tests.

## Defensive regex guards (from lessons.md)

| Guard | Trigger | Action |
|-------|---------|--------|
| Negation lookbehind | every numeric extraction | scan 30 chars left for `not`, `non`, `never`; if hit, drop the match |
| mITT phrase detector | denominator extraction | prefer denominators within 50 chars of `modified intention-to-treat` / `mITT` / `full analysis set`; flag completer-only as low-confidence |
| Multi-HR disambiguator | HR/CI extraction | prefer HR within 100 chars of "primary endpoint" / "primary outcome" / known endpoint anchor (passed in by dashboard) |
| LSMD/MMRM tag | continuous endpoints | scan for `LSMD`, `least-squares mean`, `MMRM`, `ANCOVA`, `mixed model`; tag the auto-fill with the detected method |
| Apostrophe-in-string | every string write to JS | screen for `'` before any string literal injection; mandatory escape (lessons.md 2026-04-30 trap) |

## Dual-sign contract

User-added trials require BOTH reviewers to sign before entering the
pool. No "skip" option (unlike pre-curated trials, which already have
the standard screening signoff). Why stricter? Because the curated
data went through one round of human curation already; user-added
data has none.

Sign block stores:
```
{
  userAdded: true,
  _addedAt: ISO timestamp,
  _addedBy: reviewer1 id,
  _coSignedBy: reviewer2 id,
  _coSignedAt: ISO timestamp,
  _seal: HMAC of (NCT + reviewer ids + timestamps + critical fields)
}
```

## Regression contract (rollback condition)

After Playwright tests + audit re-run, ANY of the following triggers
revert + reconvene:

- Pre-change pooled HR/CI changes by >0.001 with no user-added trials.
- Sentinel raises a new verdict on the patched dashboard.
- `audit_v65_engine_coverage.py` flags the dashboard.
- `audit_mitt_vs_allocated.py` or `audit_continuous_conventions.py`
  produces a new flag on a curated (non-userAdded) trial.
- Console errors on page load with no user-added trials.
- Engine bit-reproducibility against pre-change snapshot fails for
  the curated-only pool.

## Implementation phases (TDD)

1. **Spec-lock** (this doc) — committed early per
   `feedback_finrenone_build_safety.md`.
2. **Smoke-test scaffolding first** — Playwright file with the
   regression contract assertions. They all fail initially. (TDD
   per `feedback_research_methodology.md`.)
3. **Module 1: defensive regex helpers** — pure functions, easiest
   to unit-test in isolation.
4. **Module 2: CT.gov v2 fetch + structured extract** — mock the API
   response in the test fixture; real fetch behind a feature flag.
5. **Module 3: validation modal + add flow** — UI + state push.
6. **Module 4: engine integration + curated-only toggle** — the
   regression detector.
7. **Smoke test passes + audit clean** — green-light condition.
8. **Debrief** — note any surprises before any portfolio sweep.

## Out-of-scope follow-ups (after pilot)

- Sweep across 170 dashboards via codemod.
- EU CTR / ChiCTR / WHO ICTRP fetchers.
- LLM-based extraction for fields where regex fails (with the
  ~4% citation-misattribution baseline from lessons.md as the floor).
- Per-dashboard configurable extraction templates.

## Open questions (for user before implementation)

1. **Reviewer-id source**: dual-sign needs two distinct reviewer
   identities. Pre-curated trials use `RapidMeta.getReviewerId()` +
   a co-signer prompt. Should user-added trials use the same flow,
   or require a second human (e.g. via email confirmation)?
2. **CT.gov rate limits**: v2 API allows ~250 requests/hour without
   auth. For a single dashboard's search this is fine. Worth
   caching responses for 24h?
3. **PMID for abstract regex**: if a candidate trial has CT.gov
   results posted, we can skip PubMed entirely. If it doesn't, do
   we (a) require the user to provide a PMID/DOI manually, or (b)
   try to PubMed-search by NCT first?

Will spec-lock once these three are decided. Default plan if no
input: same reviewer-id flow as existing screening; 24h cache;
auto-search PubMed by NCT first.
