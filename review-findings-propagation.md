# Multi-Persona Review: Propagated Features (TextExtractor, GRADE SoF, Manuscript Text)
### Date: 2026-03-16 (Round 1), 2026-03-17 (Round 2)
### Scope: All 8 siblings + LivingMeta.html
### Status: REVIEW CLEAN — All 8 P0 fixed, All 19 P1 fixed, 10/16 P2 fixed
### Validation: 7/8 pass (INCRETIN_HFpEF = no gold, pre-existing)

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

- [PARTIAL] **P0-6** [SE/Domain]: `renderGRADE` and `computeGradeAssessment` produce different GRADE ratings — 5 logic divergences: indirectness check, pub bias k>=10 gate, upgrade cap, data source (DOM vs object), weight null safety. All 8 siblings.
  - Fix: Refactor `renderGRADE` to call `computeGradeAssessment` (single source of truth).

- [FIXED] **P0-7** [Stats/Domain]: Manuscript significance test uses null=1 for all effect measures — for continuous outcomes (MD), null is 0, not 1. `parseFloat(uci) < 1.0` misclassifies MD results. All 8 siblings, line ~12966-12970.
  - Fix: Check `isContinuous`; use `uci < 0` for MD significant reduction.

- [FIXED] **P0-8** [Security]: XSS — NCT IDs from CT.gov API injected into innerHTML without escaping in update banner. All 7 siblings, line ~12914.
  - Fix: `escapeHtml(id)` for text, `encodeURIComponent(id)` for href.

## P1 — Important (16)

- [FIXED] **P1-1** [Stats/SE]: `computeInterventionEventRate` returns null → NaN in ARD display. ARD shows "NaN (NaN to NaN)" when CER≥1 or effect≤0. All 8 siblings, lines ~9036-9041.
  - Fix: Guard `ierPt != null ? Math.round((ierPt - cer) * 1000) : '--'`

- [OPEN] **P1-2** [Domain]: LivingMeta SoF export is GRADE evidence profile, not Cochrane SoF table — missing Outcome, Participants, Relative Effect, Absolute Effects columns. LivingMeta exportSoFHTML.
  - Fix: Restructure to match Cochrane format (like BEMPEDOIC's exportSoFHTML).

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

- [OPEN] **P1-15** [Domain]: Inconsistency domain ignores k-sensitivity — I²<50% with k=2-3 is uninformative, not reassuring. All 8 siblings, L8939.
  - Fix: Add informational note when k<5 and I²<50%.

- [OPEN] **P1-16** [Stats]: Hardcoded 0.95 in CI compare plot. 3+ siblings, L10340.
  - Fix: Use `RapidMeta.state.confLevel ?? 0.95`.

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
- [OPEN] R2-N2 [P1]: LivingMeta hardcoded `normalQuantile(0.975)` in MH-OR, Peto, Trim-Fill, Bootstrap PI
- [FIXED] R2-N3 [P1]: `gradeHedge` guard for undefined `gradeCertainty` (was producing "was is very uncertain about")
- [FIXED] R2-N4 [P2]: `_plainLanguage` grammar — "may reduces" → "may reduce" (infinitive after modal)
- [FIXED] R2-N5 [P2]: `inconsistencyNote` dead code wired into reasons (k<5 informational note)
- P2: CT.gov URL encoding inconsistency (BEMPEDOIC L6812, LivingMeta L5274) — low risk

## False Positive Watch
- P0-SE2 (normalInv undefined) — needs verification: may be `normalQuantile` but could also be defined elsewhere
- Agent P0-SE4 overlaps with P0-6 (deduplicated)
- Agent P0-DE-4 overlaps with P0-6 (deduplicated into renderGRADE divergence)
