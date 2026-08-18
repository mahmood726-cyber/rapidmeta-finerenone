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

   **2026-08-18 — THE SAFETY NET HAD THE SAME HOLES AS THE NET. Embolism added to
   all three lists.** On DOAC_AF, four registry composites each reading *stroke OR
   systemic embolism* all reduced to `{stroke}` and the gate returned **PASS —
   they agree**. Half of every composite in the topic was unread.

   The part that matters is not the miss, it is **which mechanism missed it**.
   The paragraph immediately below this one promised that `EVENT_LIKE` — the
   deliberately over-broad hunting list — makes any definition containing an
   unrecognised term UNCHECKABLE, so that *"the gate can no longer report
   agreement from a partial reading"*. `EVENT_LIKE` carried renal, oncological,
   infectious and ophthalmic terms and **no embolism**, so the promise was not
   kept and nothing said so. Its own comment predicted exactly this: *"A gap in
   THIS list is one level further back than a gap in `_CANON`, and it is the only
   comfortable failure left in the design."*

   Fixed in `COMPONENT`, `_CANON` and `EVENT_LIKE` in one commit. **Zero verdicts
   move across all 34 objects** — DOAC_AF was PASS before and after, because its
   composites really do agree — so the fix is carried by a constructible failing
   input in the selftest instead: `"Stroke or systemic embolism"` against
   `"Stroke"`, old gate PASS, new gate FAIL.

   **The general lesson, and the reason this is not closed: a hunting list is
   only a safety net for the specialties whose words are in it.** Every new
   programme needs BOTH lists extended before its first topic, not after. Sweep
   the remaining cardiology vocabulary the same way before topic 9 — this one was
   found by a topic, not by an audit, which means the audit is still owed.
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
## 2a. A concurrent git operation silently degrades the build stamp

`_generator_stamp()` shells out to `git log` and `git status`. If another git
process holds the index — a `push`, a `stash`, a `commit` in a neighbouring
shell — those calls fail and the stamp is written as **UNKNOWN**.

Observed 2026-08-18: SOTAGLIFLOZIN_HF_REVIEW was rebuilt while a `git push` was
running in this session and came out stamped `UNKNOWN`, meaning *not reproducible
from this stamp*. Two pages built minutes either side carry the correct commit.

**The gate caught it** — `build_stamp_gate` FAILs on UNKNOWN by design, and it
did, so nothing shipped. Logged as a save, not a defect: the stamp degraded
toward *alarm*, which is the rare and correct direction, and it is the reason the
UNKNOWN state exists at all rather than a silent fallback to the last known
commit.

Owed: either serialise builds against git operations, or retry the two git calls
before conceding UNKNOWN. **Do not "fix" it by defaulting to HEAD** — a stamp
that guesses is the failure the UNKNOWN state was introduced to prevent.

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

## 8. Untracked SSOT objects — CLOSED 2026-08-18

Committed at `77ec67ad6`. Verified rather than assumed: `git status
--untracked-files=all ssot/` now reports **only 16 PNGs under `ssot/figs/`** and
no `.json` object. The gate's watch list was never extended, so the *class* is
still unguarded — that part moves to item 11.

---

## 9. Object fields that gates read and no projector renders

`estimand_definition_read` is v1's twelfth property. Four topics were taken
through it. **Not one of their pages rendered a single endpoint definition.**
`PCSK9_REVIEW.html` contains "Clinical Events Committee" zero times while its
object holds FOURIER's registry description verbatim.

The definition lives in the object; `estimand_definition_gate` reads it *there*;
the gate passes; the property is reported established — and a reader gets prose
and has to take the reading on trust. Same for `eligible_but_not_contributing`,
which `subject_match_gate` reads and nothing projected, so DOAC_AF listed four
registrations and pooled three with no surface saying so.

Two cards added 2026-08-18 and live on DOAC_AF. **Owed:**

1. **Rebuild the four earlier topics** — ARNI, ALIROCUMAB, IV_IRON,
   SOTAGLIFLOZIN — plus PCSK9, SGLT2_HF, SGLT2_CKD and ABLATION_AF, so their
   definitions become visible. They were read; they are invisible.
2. **Sweep the class.** Every object key a gate reads should be checked against
   whether any projector emits it. A property established only in the object is a
   property the reader must take on trust, and that is this project's recurring
   substitution in its purest form.

---

## 10. The index TABLE ROW has no checker, and it carries its own numbers

Every topic has THREE index surfaces: the card, the page, and a table row about
eleven screens below the card carrying its **own trial count and its own
estimate**. `card_alignment_gate` reads the card. **Nothing reads the row.**

It was missed on ABLATION_AF. It was edited by hand on PCSK9, SGLT2_CKD and now
DOAC_AF (4 trials → 3, `HR 0.81 (0.73–0.91)` → withdrawn). Hand-editing a surface
three times in three topics is the definition of a checker's absence.

Constructible failing input already exists in history: the ABLATION_AF commit
where the card was corrected and the row was not.

---

## 11. `arm_identity_gate` reads its fixtures from a hardcoded absolute path

`OBJ = r"F:\E156\outputs\codex-corpus-scan\extract\full_run"`. This is the
same shape as the wrong-tree defect closed in `card_alignment_gate` on
2026-08-18, still live in a second gate. It fails toward **alarm** — a missing
directory prints "object absent -- NOT PROVEN" and returns 1 — which is why it is
item 11 and not item 1. The eleven label-level selftest cases added 2026-08-18
need no fixture on disk and run anywhere, so a clone without that directory now
still exercises the logic.

Also owed here: `received_label()` reads the word after "placebo" as a drug name
with no dictionary to check it against. That over-broadness destroyed eight
correct detections in an earlier cut of the fix; it is now reachable only inside
a *symmetric* double-dummy label. **Narrowed, not solved.**

---

## 12. `figs/`, `ssot/figs/` and `*.figaudit.json` are rewritten by every build and tracked by nothing

Raised 2026-08-18. **Measured before writing it down, and the true scope is
narrower than the first statement of it — which is why it is worth stating
precisely rather than alarmingly.**

The claim as first put was "the tabbed projector rewrites them on every build, so
a figure change is invisible to git." Checked:

| | tracked? | referenced by a page? |
|---|---|---|
| the figures a READER sees | **yes** — inline `<svg>` in the tracked HTML (ARNI 16, PCSK9 8, DOAC_AF 7) | n/a, they *are* the page |
| `figs/` — 100 files, `.eps` `.tiff` `.png` `.html` `_src.svg` per figure | **no** | **no**: `git grep figs/ -- '*.html'` returns nothing |
| `ssot/figs/` — 16 `.png` | **no** | no |
| `*.figaudit.json`, one per built page | **no** | no |

**So a figure change on a page IS recorded** — it lands in the tracked HTML diff,
and that is how the ARNI rebuild's dropped numerals were caught. The exposure is
not the reader's figure.

**What is genuinely unrecorded is the EXPORT set.** `figs/*.eps` and `*.tiff` are
the submission-grade artefacts a manuscript would carry to a journal. They are
regenerated wholesale on every build of any topic, they belong to whichever topic
was built last, and **nothing records which commit produced them.** A file named
`forest.eps` cannot be attributed to a review, a version, or a value. If one is
ever attached to a submission, the provenance chain that this entire repository
exists to maintain stops at the directory listing.

`*.figaudit.json` is the same shape one level up: it is the *evidence a gate ran*,
written beside the page and preserved nowhere.

This is the authored-cards family — a surface that changes without being
recorded — and also ledger failure mode #4, a register written into a place git
does not carry.

**Owed, and none of it is decided here:**

1. **Decide whether the export set is an artefact or a by-product.** If a
   manuscript ever consumes `figs/*.eps`, it must be tracked, per topic, in a
   per-topic directory rather than one shared one — `figs/forest.eps` is
   currently a *shared mutable name* across 53 cardiology topics, which is the
   hardcoded-path defect wearing a filename. If it is a by-product, it should be
   `.gitignore`d and regenerated on demand, and **it is currently neither**:
   untracked *and* unignored, so it sits in every `git status` making real
   untracked work harder to see.
2. **Stamp the exports.** Whatever is decided, an exported figure should carry
   the generator commit and the object id the way the page's build stamp does.
3. **Do not "fix" this by committing the current 116 files.** They belong to
   whichever build ran last and nobody knows which that was — committing them
   would record a provenance claim that is false, which is worse than recording
   none.

---

## 13. `identity_by_registration_gate` cannot see a registration that names the wrong trial — PARTIALLY CLOSED 2026-08-18

It asks whether a registration is **recorded** and **unique per row**. It never
asks whether the registration **is** that trial. It passed
`NCT02583191 = 'SELECT-D'`, a row pointing at a German treatment-satisfaction
study. It closes LABEL→IDENTITY, the PARACHUTE-HF defect, and leaves
REGISTRATION→IDENTITY open — and that direction fails toward comfort.

`scripts/registration_identity_gate.py` now screens it by comparing participants
analysed against the enrolment the registration records. **34 of 38 rows across
the 11 v1 objects come back clean**; the three listed are DOAC_AF's and are all
correct (two are three-arm trials pooled two arms at a time, which the gate now
says on the line).

**Still owed:**

1. **A wrong registration of the SAME SIZE is invisible.** The screen is
   arithmetic; two trials of similar enrolment defeat it. A second signal is
   needed — sponsor, country, or completion year against what the object records
   — and none of those is currently stored.
2. **Fold it into `run_all_checks.py`.** It runs standalone today, which means it
   runs when someone remembers.
3. **The other 500+ corpus objects have no `registration_enrolment`.** They
   report UNMEASURED, correctly and uselessly. `--fetch` is one call per trial.

---

## 14. Nineteen multi-arm rows cannot be cleared of a fabricated contrast

`declared_contrast_gate` screens whether an extracted contrast is one the
registration declares. Corpus screen, 34 objects, 109 rows:

| | |
|---|---|
| rows on a multi-arm registration — where the defect is possible | **26 (24%)** |
| FAIL — confirmed fabricated contrast | **1** (Hua Tuo) |
| PASS — contrast is declared | 6 |
| **UNCHECKABLE — cannot be cleared** | **19** |

**Nine of the nineteen are uncheckable for one specific reason: the registration
declares more than two arms and NO between-arm analyses at all**, so there is no
declared list to compare against. Those need a different signal, and the obvious
one is arithmetic rather than nominal: **does the extracted pair's arm SIZES match
two of the registration's reported arm-group denominators?** That is the same
shape as the enrolment screen in `registration_identity_gate` and would reuse its
data.

The other ten are uncheckable because the object's arm labels are the registry's
**protocol** arm titles while the declared comparisons are named with its
**results** group titles — BERSON is the worked example, carrying
`'Atorvastatin (Q2W)'` where the results groups say `'Placebo Q2W'`. Storing both
title sets at fetch time would resolve most of them.

**Do not close this by relaxing the matcher.** An UNCHECKABLE that becomes a PASS
because the comparison got fuzzier is the comfortable direction, and this gate
exists because the defect it hunts is invisible to every internal check.

---

## 15. 818 silently dropped trials across 360 pages

`silent_exclusion_screen.py`. Measured, not estimated: 1450 pages scanned, **583
had no readable include list** (UNREAD, never counted as clean), 507 complete,
**360 with at least one included trial contributing nothing.**

**The bias question came back clean and the scale question did not.** Of 604
dropped trials with a usable ratio: 352 favour the intervention, 29 null-ish, 223
favour the control, geometric mean 1.109. No sign of null trials being lost while
favourable ones are kept. But 818 trials are named and omitted, including MORDOR-I
(190,000), AVENIR (90,000), TIDES (20,067), ROCKET AF (14,171), SCORED (10,584).

**Owed:**

1. **Say it on the page.** Every dropped trial should appear under the card added
   for DOAC_AF and DOAC_CANCER_VTE — "Named on this review, contributing nothing
   to its pool" — with its reason. That card exists and is projected; it is
   populated by hand on three topics and by nothing anywhere else.
2. **The 583 UNREAD pages are not clean.** They use a different generation with no
   `AUTO_INCLUDE_TRIAL_IDS`. Until a reader exists for them, the 818 is a floor.
3. **91 dropped trials carry a non-ratio value in a field named `publishedHR`** —
   mean differences in a hazard-ratio slot. Surfaced as a math domain error. A
   field whose NAME asserts a measure its CONTENTS contradict is the
   `no_rob_banner` defect in a new place.

---

## 16. Multi-arm registrations that declare no comparison — a gap in the REGISTRY, not in us

Noted while screening for fabricated contrasts. Nine of the nineteen unclearable
rows are unclearable because **the registration declares three or more arms and
records NO between-arm analysis at all.** There is nothing to check the extracted
contrast against, and that is not a defect in this corpus.

Worth stating as a finding rather than only as a blocker: **a registry entry that
reports arm-level results and no comparison leaves the reader unable to tell which
arms the trialists actually contrasted.** Every synthesis downstream must then
guess, and a guess is exactly what produced the Hua Tuo cross-pairing. It is a
publishable observation about registration practice in its own right, and this
project now has the numbers to make it: **26 multi-arm rows, 9 with no declared
comparison — 35 per cent.**

---

## 17. A benchmark that shares a registration with an included trial is not an independent comparison

BEMPEDOIC_ACID's published-meta step compared its estimate **against itself**. The
page's benchmark database holds exactly one entry for that outcome — "CLEAR
Outcomes bempedoic acid vs placebo", Nissen 2023, HR 0.87 (0.79—0.96) — and CLEAR
Outcomes IS the trial on the card. The comparison agreed perfectly and established
nothing.

**Detectable, and cheaply:** a benchmark entry whose registration, trial name or
citation matches an INCLUDED trial is self-referential. It should render as
"no independent synthesis records this estimand" rather than as agreement.

**Why it matters more than it looks:** perfect agreement is the most reassuring
output a comparison step can produce, and this is the configuration that
guarantees it. It fails toward comfort by construction.

---

## 18. `count_provenance_gate` — what it still cannot do

Built 2026-08-18 after CANGRELOR_PCI. Corpus screen over 37 objects: 4 FAIL, 2
PASS, 13 REVIEW, 18 UNCHECKABLE.

**RESULT, after the false-alarm cause was fixed: ZERO FAILS ACROSS 37 OBJECTS.**
2 PASS, 4 REVIEW, 31 UNCHECKABLE. **No further instance of the CANGRELOR class
exists in any object in this repository**, and that is the answer the screen was
built to get.

All four original FAILs had one cause: **the object records no
`outcome_definition`**, so the gate fell back to the registration's PRIMARY and
disagreed with rows that were pooling something else deliberately — FIDELIO-DKD's
cardiovascular composite (a secondary there), SUMMIT's heart-failure events
(against a KCCQ primary), and pitavastatin's NCEP target attainment (against a
percent-change primary). None is a count defect. A row that does not say what it
counts now returns UNCHECKABLE, because convicting there would make one FAIL mean
two incompatible things.

**The 31 UNCHECKABLE are the real backlog** and they are mostly that same missing
declaration.

**Owed:**

1. **A better outcome-title match.** The gate compares a row against the registry
   outcome the row NAMES, by normalised title. When the object's recorded
   definition and the registry title differ in wording it falls back to the
   primary and can disagree with a correct row — FIDELIO-DKD in `finerenone-cv` is
   the worked example, and its FAIL is a false alarm. **Do not fix this by
   loosening the verdict.**
2. **The 18 UNCHECKABLE.** Mostly objects with no complete 2x2 — continuous
   outcomes, or rows carrying only an effect estimate. A different signal is
   needed for those and this gate should keep saying it cannot see them.
3. **Wire it into `run_all_checks.py`.** It runs standalone, which means it runs
   when somebody remembers.

---

## 19. A withdrawal reason that names an endpoint type no included trial registers

**APIXABAN_ACS's card said "bleeding and efficacy endpoints pooled" and BOTH of its
trials register bleeding.** There was no efficacy endpoint in the pool to mix with
a safety one. The withdrawal was right; its published explanation was false.

**This is checkable offline and cheaply, from data the objects already hold.** Each
trial now carries `outcome_definition` read from the registry. A stated withdrawal
reason claiming an efficacy/safety mixture can be tested against them: does ANY
included trial register an efficacy endpoint? Does any register a safety one? If
the reason names a type no trial has, the reason is wrong even where the
withdrawal is right.

**The counter-case is why it needs to be a check rather than a rule of thumb:**
RIVAROXABAN_ACS carries the identical card wording and there it is TRUE. The same
sentence is right on one page and false on another, and only the registrations
separate them.

**Why it matters:** a withdrawal is a published claim. Nothing in this repository
was checking whether the reason given for one was true, and by the old rule a
topic with a false reason still counted as done.

---

## Closed

- **2026-08-18 — all eight withdrawn cardiology topics re-verified against the
  registry.** 1 unchanged, 6 confirmed-and-sharpened, 1 reason FALSE, 0 reversed.
  Every reason is now quoted from the registrations rather than asserted on a card.

- **2026-08-18 — mismatched numerator and denominator has a detector.**
  `count_provenance_gate`, replayed against CANGRELOR's three CHAMPION rows as
  published (FAIL, naming all-cause mortality as the numerators' true source) and
  against the registry's own counts (PASS). Three parser faults were fixed before
  it was trusted: arm order, rate-valued outcomes, and multi-category outcomes
  summed per arm.

- **2026-08-18 — the escaping class is swept and has a checker.**
  `double_escape_gate`, 1450 pages: found 7, including the FLAGSHIP, via numeric
  entities the previous named-entity fix could not see. Root cause was PubMed
  returning pre-encoded text. 6 remain, all in the DTA programme.

- **2026-08-18 — a fabricated contrast has a detector.** `declared_contrast_gate`,
  replayed against Hua Tuo as extracted (FAIL) and the same trial paired as it was
  actually run (PASS). Two-arm registrations return NOT_APPLICABLE, never PASS.

- **2026-08-18 — venous thromboembolism recognised, classifier added with it.**
  The hunting list fired productively for the first time: it refused to compare
  `venous thromboembolism` rather than reporting agreement from a partial
  reading, on a topic whose endpoints genuinely disagree. One object moves; no
  object gained a pass.

- **2026-08-18 — systemic embolism was invisible to `COMPONENT`, `_CANON` AND
  `EVENT_LIKE`.** Four registry composites reading "stroke or systemic embolism"
  all reduced to `{stroke}` and the gate reported agreement. The hunting list
  that exists to prevent exactly that had the same specialty-shaped hole. Fixed
  in all three; zero verdicts move on 34 objects, so it is carried by a
  constructible failing input in the selftest.
- **2026-08-18 — a double-dummy arm label defeated the inverted-roles check.**
  Both labels name a placebo, so both direction branches were skipped and the
  token fallback returned a bare PASS. Proved by swapping ENGAGE AF-TIMI 48's two
  registry arm titles: the gate passed the inverted arrangement. Fixed by
  resolving each label to what the arm RECEIVED, but **only when both labels name
  a placebo** — the two earlier cuts of that fix each destroyed correct
  detections, and both failed toward comfort.
- **2026-08-18 — the arm LABEL-versus-ROLE question is answerable from the
  registry's RESULTS section**, which returns the arm sizes the parked note said
  were unavailable. Three trials decided on DOAC_AF: label wrong, role right,
  magnitude unaffected, every time.

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
