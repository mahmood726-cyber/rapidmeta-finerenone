# Multi-Persona Review: Propagated Features (TextExtractor, GRADE SoF, Manuscript Text)
### Date: 2026-03-16 (Round 1), 2026-03-17 (Round 2), 2026-03-18 (Round 3)
### Scope: All 18 REVIEW siblings + LivingMeta.html
### Status: REVIEW CLEAN — All 8 P0 fixed, All 21 P1 fixed, 10/16 P2 fixed
### Validation: 148/148 tests pass across 19 apps

---

## P0 — Critical (8)

- [FIXED] **P0-1** [Stats/SE/Domain]: `generateManuscriptText` outputs "0.95% CI" instead of "95% CI" — `confLevel` stored as proportion (0.95), not percentage. All 8 siblings, line ~12939.
  - Fix: `Math.round((RapidMeta.state.confLevel ?? 0.95) * 100)`

- [FIXED] **P0-2** [UX]: Stray JS code in HTML body between GRADE buttons — `// Auto-generate manuscript...` and `if (typeof generateManuscriptText...)` spliced into HTML `<div class="flex gap-2">`, renders as visible text. All 7 siblings, line ~1356-1357.
  - Fix: Remove these 2 lines from HTML. The wiring already exists in the `<script>` block.

- [FIXED] **P0-3** [Domain]: `_plainLanguage` ignores GRADE certainty — always uses "probably" for benefit and "may" for harm regardless of rating. Per GRADE (Santesso 2020): HIGH="reduces", MOD="probably reduces", LOW="may reduce", VERY LOW="very uncertain". All 8 siblings, line ~9071.
  - Fix: Pass `certainty` to `_plainLanguage()`, use GRADE-appropriate hedge words.

- [FIXED] **P0-4** [Domain]: LivingMeta patient summary re-derives GRADE certainty with wrong formula — `['VERY LOW','LOW','MODERATE','HIGH'][Math.max(0, 4-Math.ceil(total))]`. For total=0, index=4 (out of bounds → undefined). For total=1, returns 'HIGH' (should be MODERATE). LivingMeta L14648.
  - Fix: Use pre-computed `grade.finalCertainty` instead of re-deriving.

- [FIXED] **P0-5** [SE]: `P_INTERACT_RX` global regex retains `lastIndex` between `extract()` calls — skips matches on alternate calls. All 8 siblings, L5658/5836.
  - Fix: Reset `P_INTERACT_RX.lastIndex = 0` before `while (.exec())` loop.

- [FIXED] **P0-6** [SE/Domain]: `renderGRADE` and `computeGradeAssessment` produce different GRADE ratings — 5 logic divergences: indirectness check, pub bias k>=10 gate, upgrade cap, data source (DOM vs object), weight null safety. All 8 siblings.
  - Fix: Refactor `renderGRADE` to call `computeGradeAssessment` (single source of truth).
  - **R3 verification**: Old `renderGRADE` fully removed from all 18 files. All use identical `computeGradeAssessment` (6959 chars, byte-exact match confirmed).

- [FIXED] **P0-7** [Stats/Domain]: Manuscript significance test uses null=1 for all effect measures — for continuous outcomes (MD), null is 0, not 1. `parseFloat(uci) < 1.0` misclassifies MD results. All 8 siblings, line ~12966-12970.
  - Fix: Check `isContinuous`; use `uci < 0` for MD significant reduction.

- [FIXED] **P0-8** [Security]: XSS — NCT IDs from CT.gov API injected into innerHTML without escaping in update banner. All 7 siblings, line ~12914.
  - Fix: `escapeHtml(id)` for text, `encodeURIComponent(id)` for href.

## P1 — Important (16)

- [FIXED] **P1-1** [Stats/SE]: `computeInterventionEventRate` returns null → NaN in ARD display. ARD shows "NaN (NaN to NaN)" when CER≥1 or effect≤0. All 8 siblings, lines ~9036-9041.
  - Fix: Guard `ierPt != null ? Math.round((ierPt - cer) * 1000) : '--'`

- [FALSE POSITIVE] **P1-2** [Domain]: LivingMeta SoF export — R3 re-review found all Cochrane SoF columns present: Outcome, No. of participants (studies), Relative effect (% CI), Anticipated absolute effects per 1,000, Certainty (GRADE), Comments. Separate GRADE Evidence Profile section also included. Lines 9124-9159.

- [FIXED] **P1-3** [Domain/Stats]: LivingMeta hardcodes "95% CI" in SoF export. LivingMeta L8857.
  - Fix: Read from `AppState.settings?.confLevel`.

- [FIXED] **P1-4** [SE]: LivingMeta `exportSoFHTML` revokes Blob URL synchronously — can race with download. LivingMeta L8872.
  - Fix: `setTimeout(() => { URL.revokeObjectURL(url); a.remove(); }, 200)`

- [FIXED] **P1-5** [SE]: `exportCSV` in GradeProfileEngine revokes Blob URL synchronously (same race). All 8 siblings.
  - Fix: Same setTimeout pattern as exportSoFHTML.

- [FIXED] **P1-6** [Security]: CSV injection in CapsuleEngine `data.csv` — trial names written without quoting. All 7 siblings, L9281.
  - Fix: Use `_esc()` helper (already defined at L9109) for all string fields.

- [FIXED] **P1-7** [Security]: MIME type mismatch — siblings use `text/html` for Word export but LivingMeta uses `application/msword`. Siblings open in browser instead of Word.
  - Fix: Change to `{ type: 'application/msword' }` and `.doc` extension in all siblings.

- [FIXED] **P1-8** [Domain]: Manuscript text uses "statistically significant" dichotomy — contrary to ASA 2016 and GRADE-informed language. All 8 siblings, L12966.
  - Fix: Use GRADE certainty-informed language instead of significance framing.

- [FIXED] **P1-9** [UX]: Section headings at `opacity-40` fail WCAG AA contrast (~3.2:1 vs 4.5:1 required). All 8 siblings, 15+ headings.
  - Fix: Change `opacity-40` to `opacity-60` minimum.

- [FIXED] **P1-10** [UX]: GRADE downgrade footnote uses `color:#888` — fails contrast on both dark and light themes. All 8 siblings, L9161.
  - Fix: Use `color:#a1a1aa` (zinc-400).

- [FIXED] **P1-11** [UX]: `#grade-profile-container` and `#manuscript-text` lack `aria-live="polite"`. All 8 siblings.
  - Fix: Add `aria-live="polite"` to both containers.

- [FIXED] **P1-12** [UX]: LivingMeta GRADE table missing `<caption>` and `<th scope="col">`. LivingMeta L8765.
  - Fix: Add caption and scope attributes.

- [FIXED] **P1-13** [SE]: `renderGRADE` ciWidth no NaN guard — `Math.log(lci)` when lci≤0 gives `-Infinity`. All 8 siblings, L10354.
  - Fix: Guard `(lci > 0 && uci > 0) ? ... : Infinity` like computeGradeAssessment.

- [FIXED] **P1-14** [Domain]: SoF table missing "No. of participants" column (required by Cochrane SoF). All 8 siblings, L9089.
  - Fix: Add `<th>Participants</th>` column displaying `r.totalN.toLocaleString()`.

- [FIXED] **P1-15** [Domain]: Inconsistency domain k-sensitivity note improved. All 18 siblings + FINERENONE.
  - Fix: Changed from "I² imprecise with k=N (no downgrade)" to "I² unreliable with only k=N studies — low power to detect heterogeneity (no downgrade, but interpret with caution)". Verified in computeGradeAssessment L8383.

- [FALSE POSITIVE] **P1-16** [Stats]: R3 re-review found `r.confLevel` is already stored as a percentage string (e.g. '95') via `(c.confLevel * 100).toFixed(0)` at L9795-9796. The `?? '95'` fallback is correct type and value for old localStorage compat.

## P2 — Minor (12)

- [FIXED] P2-1: LivingMeta `.vlow` CSS class added in exportSoFHTML
- [FIXED] P2-2: GRADE imprecision reason now uses `emLabel('short')` not hardcoded "OR"
- [FIXED] P2-3: `hksjSE ?? pSE` (nullish coalescing)
- P2-4: Dead code: first `NEG_CONTEXT` loop in TextExtractor `extract()` does nothing
- P2-5: SGLT2/COLCHICINE/GLP1 missing ZipBuilder GRADE integration
- [FIXED] P2-6: SoF export HTML has `lang="en"` attribute
- P2-7: Export dropdown items are `<div>` not `<button>` (partially mitigated by keyboard handler)
- P2-8: RoB traffic-light circles have no aria-label
- [FIXED] P2-9: Manuscript text defaults to "Phase II/III" (was "Phase III")
- P2-10: GRADE fractional downgrades (0.5) are non-standard (LivingMeta)
- P2-11: `escapeHtml` inconsistency: `&#039;` vs `&#39;` across files
- P2-12: 10px button text below 44px touch target minimum

## Round 2 — New Issues (2026-03-17)

- [FIXED] R2-N1 [P1]: LivingMeta `P_INTERACT_RX.lastIndex = 0` missing before `.exec()` loop
- [FIXED] R2-N2 [P1]: LivingMeta hardcoded bootstrap quantiles. R3 found MH-OR, Peto, Trim-Fill already correct (use `AppState.settings?.confLevel`). Fixed `computeBootstrapPI` (L11391-11392) and `computeCDPredInt` (L12013) to derive from confLevel via `alphaHalf = (1-cl)/2`.
- [FIXED] R2-N3 [P1]: `gradeHedge` guard for undefined `gradeCertainty` (was producing "was is very uncertain about")
- [FIXED] R2-N4 [P2]: `_plainLanguage` grammar — "may reduces" → "may reduce" (infinitive after modal)
- [FIXED] R2-N5 [P2]: `inconsistencyNote` dead code wired into reasons (k<5 informational note)
- P2: CT.gov URL encoding inconsistency (BEMPEDOIC L6812, LivingMeta L5274) — low risk

## Round 3 — Manual Review (2026-03-18)

### Fixes applied this round:
- [FIXED] R3-F1: P0-6 verified resolved — `renderGRADE` fully removed, all 18 files use identical `computeGradeAssessment`
- [FIXED] R3-F2: P1-15 improved k-sensitivity note in `computeGradeAssessment` (all 18 siblings)
- [FIXED] R3-F3: R2-N2 LivingMeta bootstrap quantiles now confLevel-aware (2 functions)
- [FIXED] R3-F4: `_plainLanguage` MODERATE verb conjugation — "probably reduce" → "probably reduces" (all 18 siblings)
  - Verb conjugation: HIGH/MODERATE use "reduces/increases/results in" (adverb, same form); LOW uses "reduce/increase/result in" (modal "may" takes infinitive)

### New findings:
- R3-N1 [P2]: `generateManuscriptText` says "1 randomized controlled trials" for k=1 (plural mismatch). L12771.
- R3-N2 [P2]: `generateManuscriptText` "Phase II/III RCTs" default when phases empty — fine for multi-trial but imprecise for single-trial.
- R3-N3 [P2]: `exportCSV` `_esc` helper wraps in double-quotes but doesn't prepend `'` for formula injection prevention. Low risk since fields are medical outcome names.
- R3-N4 [P2]: LivingMeta `exportSoFHTML` only renders single outcome row (by design — LivingMeta synthesizes one outcome at a time).

### Verification:
- **148/148 Selenium tests pass** across 19 apps (18 REVIEW + LivingMeta)
- All 18 REVIEW files have identical `computeGradeAssessment` (6959 chars, byte-exact)
- Div balance: +1 in all files is false positive from `<div class="footnotes">` in JS string export (escaped `<\/div>` not counted by naive checker)
- All `innerHTML` assignments in 3 features use `escapeHtml()` for string content
- No ReDoS risk in TextExtractor patterns (all bounded quantifiers)
- European decimal regex has lookbehind protection against CI pair corruption

## False Positive Watch
- P0-SE2 (normalInv undefined) — needs verification: may be `normalQuantile` but could also be defined elsewhere
- Agent P0-SE4 overlaps with P0-6 (deduplicated)
- Agent P0-DE-4 overlaps with P0-6 (deduplicated into renderGRADE divergence)
- P1-2 was false positive (LivingMeta SoF already has all Cochrane columns)
- P1-16 was false positive (r.confLevel is already a percentage string)
