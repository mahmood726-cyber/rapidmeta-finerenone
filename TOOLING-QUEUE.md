# TOOLING QUEUE

Work on the instruments rather than on the pages. **The estimand gate is first**
and everything below it is ordered behind that.

The admission rule that governs every entry here is the one in
`scripts/standard_manifest.py`: **no property enters the standard without a
constructible failing input and a real defect it would have caught.** An item on
this queue is not done when the code runs; it is done when the failing input
exists, has been run, and blocked.

---

## 1. THE ESTIMAND GATE — the recognition vocabulary is one specialty wide

**Partly closed 2026-08-18** — the structural half is done, the vocabulary half
is not, and the vocabulary half is now *visible* instead of silent.

Its component list (`COMPONENT`, `_CANON`) is entirely cardiological:
hospitalisation, CV death, stroke, MI, bleeding, cardiac arrest, ACS, worsening
heart failure. **Nothing renal, nothing infectious, nothing oncological.** Run on
SGLT2_CKD it reduced three different composites to `{cv_death}` and reported that
they agree.

What is now true: an over-broad `EVENT_LIKE` hunting list makes any definition
containing an unrecognised event term **UNCHECKABLE**, naming the terms, and
UNCHECKABLE outranks both PASS and WITHDRAWN. The gate can no longer report
agreement from a partial reading.

What is still owed:

1. **Recognition vocabulary per specialty**, added *with* its `_CANON` mapping —
   widening the finder without the classifier is the same defect in a new place,
   and this repository has done exactly that twice. Renal first (ESKD, dialysis,
   transplant, eGFR-decline thresholds, doubling of creatinine, renal death),
   then infectious disease, which is the next programme.
2. **Thresholds are not components.** Even with renal terms recognised, a
   doubling of creatinine, a ≥50% decline and a ≥40% decline would all map to one
   key and the gate would report agreement again. The comparison needs to carry
   the THRESHOLD, not only the event type. This is the deepest open item on the
   queue and the CKD case is its fixture.
3. **A fixture set from the six under-reads already in the ledger**, replayed:
   `CV mortality`; `hospitalisation for worsening heart failure`; `worsening
   heart failure requiring unplanned hospitalization`; `cardiovascular (CV)
   death`; a bare TITLE with components in the DESCRIPTION;
   `Total Mortality, Disabling Stroke, Serious Bleeding, or Cardiac Arrest`.
   Some are already canon cases; the rest are not.
4. **A third verdict for "the registry record carries no endpoint definition"**,
   distinct from "the definitions differ". Different facts, and one of them is
   not the trials' fault.

The under-read direction remains the dangerous one, and the ledger says why:

> Six separate under-reads in one component canon ALL pushed toward withdrawal.
> Withdrawing a correct estimate destroys a true finding and publishes the
> destruction as a discovery.

**And now the other direction is on the record too.** The CKD false agreement is
the first logged under-read that fails toward COMFORT rather than alarm.

---

## 2. Escaping across the projector boundary — one instance fixed, the class is not swept

`_anchor_headings` returned ESCAPED text and the caller escaped it again, so the
jump list served readers the literal characters `&middot;` and `&#x27;` and the
generated anchor ids carried `-middot-`. Fixed at source by unescaping so the
value is plain text from that point outward and escaped exactly once, at render.

**The class is not swept.** Every other place that extracts text from generated
markup and re-emits it has the same hazard. It fires only on text containing an
apostrophe, ampersand, quote or angle bracket, which is why it survived: no
heading in the corpus had one until a registry title was quoted.

Owed: a check that no built page contains `&amp;` followed by a known entity
name, wired per build. That is a constructible failing input (any of the four
pre-fix v1 pages) and it fails toward alarm.

---
## 3. `card_matches_page` corpus-wide — 507 of 514 unmeasured

Fixed on 2026-08-18 so that a withheld card is checked rather than skipped
(see `STATUS.md`), but the corpus figure barely moved: **5 comparable, 2 agreeing
by withholding, 507 unmeasured.**

The unmeasured 507 are almost all `Audit-first build` cards, which are
UNCHECKABLE by construction — and 13 of those cards contain a self-contradiction
(`2 trials` and `k>=3` in one string) that no gate can currently see.

The real fix is the one the gate's own header names: **cards are authored, not
projected.** A generator that emits the card from the object retires this entire
class rather than measuring it.

---

## 4. `sections_in_both_surfaces` — NOT RUN on 7 of 7 objects

`section_manifest_gate` needs a docmodel and correctly exits 2 rather than
tracebacking when there is none. Correct behaviour, zero coverage: the property
is unestablished on every v1 object including the flagship.

Either produce a docmodel per object, or move the property to DECLARED in
`standard_manifest.ENFORCEMENT` and stop implying it is watched.

---

## 5. `self_contained` — measured corpus-wide, wired per page nowhere

`external_dependency_census` measures it; `checkbuild` enforces it on new builds
only; nothing checks a page that already exists. 19 of 21 sampled pages issue
third-party requests on load and all 19 got HTTP 429 from `api.openalex.org` in
one run. ~874 pages fetch the R runtime from a CDN at read time, so a
reproducibility claim degrades silently to whether someone else's CDN is up.

Wire the census per page so the property has a per-object verdict.

---

## 6. `tabbed_build` and `estimate_preserved` — checked only inside the build path

Both are marked ENFORCED and both are "checkbuild-equivalent", which means they
are established for pages built THROUGH the build path and unestablished for
every page already on disk. `v1_coverage_audit` reports them `NOT WIRED HERE`,
which is honest and is not coverage.

---

## 7. `display_change_announced` — UNENFORCEABLE, and correctly so

No artefact can show that a change was announced; the evidence is a message to a
reader, outside every file we control. Kept as a rule with a named owner rather
than a checker that could not fail. **Do not "fix" this by adding a checker that
inspects a changelog** — that would check that a file was written, which is a
different claim and the exact substitution this project keeps making.

---

## 8. Untracked SSOT objects — 20 of them exist in no clone

Twenty objects under `ssot/*/` were written on 17 Aug and never added. They are
ledger failure mode #4: a register written into a place git does not carry.
`durable_artefact_gate` runs unscoped on every push for precisely this class but
does not know about these paths.

Either commit them or add them to the gate's watch list. Writing a file is not
preserving it.

---

## Closed

- **2026-08-18 — the estimand gate reported three different CKD composites as
  agreeing.** Structural fix: recognition list decides PASS, hunting list decides
  whether the gate may decide. Regression across all eight objects: seven
  verdicts unchanged, one moved, and it was the false one.
- **2026-08-18 — a constant named `WITHHELD` did not match the word "withheld".**
  Two live cards classified as published values. `--audit-vocabulary` now hunts
  the next gap.
- **2026-08-18 — the jump list double-escaped its own headings.** Live on four of
  seven v1 pages.

- **2026-08-18 — `card_alignment_gate` reads the wrong tree by construction.**
  `SSOT` was a hardcoded absolute path; run from a sibling clone the gate graded
  another working tree and reported green. Now derived from `__file__`. This is
  the ledger's matched-pair false-life defect and it was still live in a gate.
- **2026-08-18 — a withheld card stopped the gate reading the page.** Replayed
  against SGLT2_HF at `7124fdbed^`, which went live with a card announcing a
  withdrawal the page had not performed. Old gate: UNCHECKABLE. New gate: FAIL.
- **2026-08-18 — `v1_coverage_audit` over-matched a substring, third instance.**
  It grepped gate output for blind-words BEFORE reading the exit code, so prose
  containing "UNCHECKABLE" overrode a deliberate exit 3. Two previous patches to
  that regex had already failed; the fix was precedence, not a third pattern.
  **A declared field beats an inferred one.**
