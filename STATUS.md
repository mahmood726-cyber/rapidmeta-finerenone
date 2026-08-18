# STATUS — the cardiology programme, and what is parked

**Denominator: 53 cardiology topics.** Derived, not recalled: the `#sp-cardiology`
section of `index.html` carries 54 page links, one of which
(`SOTAGLIFLOZIN_HF_AUTO_FULL_REVIEW.html`, 1,605 bytes) is a redirect stub
consolidated at `ce1e9dc0e`. 54 − 1 = 53. Re-derive with
`python scripts/cardio_program_status.py` rather than quoting this line.

**DONE: 16 of 53.**

A topic is DONE when it has an SSOT object, is built through the tabbed
projector to the written standard (`scripts/standard_manifest.py`, v1), its
identity is keyed by registration id, every contributing trial's endpoint
definition has been READ FROM THE REGISTRY, and the pool either stands or is
withheld with its reason on the page. A withdrawal counts as done. An unread
endpoint does not, whatever the page looks like.

| # | topic | state | note |
|---|---|---|---|
| 1 | ARNI_HF | v1, pooled | measure question **RESOLVED 2026-08-18**; k=4 stands |
| 2 | ALIROCUMAB_LIPID | v1, pooled | six endpoint definitions read, six values confirmed |
| 3 | IV_IRON_HF | v1, pooled | five registries read, four pools stand |
| 4 | SOTAGLIFLOZIN_HF | v1, pooled | endpoints read, pool stands |
| 5 | SGLT2_HF | v1, **withheld** | four trials, two endpoint definitions |
| 6 | ABLATION_AF | v1, **withheld** | four trials, four different primary composites |
| 7 | PCSK9 | **withdrawn** | one composite counts revascularization, the other does not |
| 8 | DOAC_AF | **withdrawn** | the headline was this page's own Ruff 2014 comparator; k said 4, the pool had 3 |
| 9 | DOAC_CANCER_VTE | **withdrawn** | a bleeding endpoint averaged with two efficacy endpoints; one registration names a different trial |
| 10 | INCLISIRAN_LIPID_KIDNEY | v1, **pooled** | estimand identical in all three registries; every value matches; **pool STANDS** |
| 11 | EVOLOCUMAB_MIXED_DYSL | **withdrawn** | both trials 2×2; this pooled a fortnightly placebo against a monthly drug arm, and the values are in no source |
| 12 | COLCHICINE_CVD | **withdrawn** | COLCOT counts cardiac arrest and the others do not; CONVINCE is not a composite trial; 5 vs 3 vs 2 trial counts on one page |
| 13 | BEMPEDOIC_ACID | v1, **stands** | k=1 and correct: only CLEAR Outcomes registers a CV primary. NCT02973841 is 'Sono-ease', a 40-patient device trial |
| 14 | CANGRELOR_PCI | **withdrawn** | all-cause-mortality numerators over primary-composite denominators; correcting it reverses the conclusion |
| 15 | RIVAROXABAN_VASC | **withdrawn** | VOYAGER adds acute limb ischaemia and major amputation; COMMANDER counts all-cause death and registers a rate |
| 16 | INTENSIVE_BP | **withdrawn** | six trials, six different composites; STEP counts atrial fibrillation, SPS3 counts stroke alone; page holds 1 effect, card said k=5 |

`FINERENONE_CV` is also at v1 and is NOT counted here: it does not sit in the
cardiology section of the index. Counting it would be the denominator drift this
file exists to prevent.

---

## The remaining 37, by what is actually on them today

Measured from the index cards, not assumed:

| state | n | what it means |
|---|---|---|
| **Audit-first build** | 26 | no estimate ever published; the topic has never been taken through |
| **live estimate, no v1 object** | 1 | a number is published that nothing in the current standard has checked |
| **withdrawn** | 7 | an estimate was retracted; the reason on the page has NOT been re-verified |
| **not poolable** | 1 | MITRAL_FUNCMR — COAPT vs MITRA-FR, stated per-trial |
| **no card at all** | 1 | INCRETIN_HFpEF is linked from the table and has no card |

The 11 with a live estimate and no object are the ones to treat as urgent. An
audit-first page publishes nothing and therefore misleads nobody; a page
publishing a pooled hazard ratio that no endpoint read stands behind is the
SGLT2_HF state, corpus-wide.

---

## Findings logged but not yet acted on

**RESOLVED 2026-08-18 — and it was 212 cards, not 13.** Every audit-first card
read `Audit-first build · N trials · AACT-verified · k>=3`. Measured corpus-wide:
**416 cards carried it, and 212 of them — 51% — say `2 trials` and `k>=3` in one
sentence.** The cardiology slice was 13 of 26; the corpus figure is eight times
larger.

`integrate_new_topics.py` writes only `Audit-first build · {n_trials} trials ·
AACT-verified`, with the count measured from `len(real_data)`. The `· k>=3` was
appended later by a different edit: **a portfolio selection rule pasted into a
slot that reads as a property of the topic.**

`card_alignment_gate` returns UNCHECKABLE on any audit-first card by
construction — so the surface a reader meets first carried an unchecked
self-contradiction on 212 pages, *inside an exemption that exists for a good
reason*. **An exemption is only not a blind spot if something else watches what
it excuses.** Nothing did.

The claim is removed from all 416, including the 204 where it is true, because on
those the real count is already stated immediately before it. Trial counts are
untouched and byte-identical.

**Still open:** 212 topics really do pool 2 trials under a rule that says 3.
Whether those topics should exist is a portfolio question and is not answered by
deleting the label.

---

## SCOPE — read this before judging the night's output

**53 cardiology topics will not all be finished at this standard in one session,
and pretending otherwise would be the failure this repository exists to prevent.**

Measured, not estimated. Each topic done properly costs, in this session:
registry retrieval for every trial, endpoint definitions read word for word, the
pool defended or withdrawn with its reason, a rebuild, a content comparison
against the artefact being replaced, gates, three surfaces corrected, a push and a
live cache-busted verification. **A single page rebuild alone runs 1–6 minutes**
(ARNI is 6.2 MB). Tonight that produced **2 topics carried to a verdict** —
ARNI resolved, PCSK9 withdrawn — plus SGLT2_CKD (not in the 53), ABLATION_AF
closed out, and **eight instrument defects found and fixed**.

The instrument work was not a detour. Five of the eight were in gates that were
returning green, and **every one of them failed toward comfort**. Any topic taken
through before they were fixed would have been graded by an estimand gate that
reports three different composites as agreeing, an arm gate whose control-word
branch had never executed, and a card gate that stopped reading a page whenever
the card said "withdrawn". Rushing the remaining topics through those instruments
would have produced 46 pages with green checks and no evidence — the exact
artefact the standard's own preamble warns about.

**The rate to plan against is roughly 2–4 fully-verified topics per session at
this depth**, faster once the converted objects stop yielding new instrument
defects. The 26 audit-first topics should be cheaper: they publish nothing, so
there is no live claim to defend, only a build.

**What is NOT done and is not started:** the ~35 untouched cardiology topics, the
withdrawn ones needing a rebuild-or-restate decision, the rest of the tooling
queue, and the whole infectious-disease programme. None of it is blocked; it is
simply not reached.

---

## PARKED — needs Mahmood's judgement, not more work

These are decisions, not tasks. Each is blocked on a choice only he can make;
none of them blocks the rest of the programme.

1. **ABLATION_AF: EAST-AFNET 4 is not an ablation trial.** Its intervention is
   early standardised rhythm control versus usual care, delivered mostly with
   antiarrhythmic drugs, in a review about catheter ablation. Flagged on the
   trial at `60be4e4a4`, deliberately not resolved: removing a trial or
   re-scoping a review is a human decision. **Options:** drop the trial (k=3), or
   re-scope the page to rhythm-control strategy (k=4, different question).

2. **ABLATION_AF: the replacement question.** The one published synthesis that
   includes a trial from this set pools COMPONENTS rather than composites —
   all-cause mortality 0.62 (0.54–0.72), stroke 0.63 (0.56–0.70), HF
   hospitalisation 0.64 (0.51–0.80). That is the obvious replacement question and
   it was deliberately NOT taken, because a replacement question must be chosen
   before its answer is known and this comparison already knows what the
   components give. **Someone who has not seen those numbers should choose.**

3. **The arm LABELS are wrong and the ROLES are right — METHOD DEMONSTRATED
   2026-08-18, three of seven trials decided, four still parked.** The parked
   note said deciding it needs each trial's own arm sizes and event counts from
   source, "which the protocol-only registry endpoint does not return". **The
   registry's RESULTS section returns them**, and on DOAC_AF they decide it with
   no ambiguity at all:

   | trial | the object's label | what the arm size proves it is |
   |---|---|---|
   | RE-LY | "Dabigatran dose 1" (control) | N=6022 is **warfarin**; the 110 mg arm has 6015 |
   | ARISTOTLE | "1" (treatment) | N=9120 is **apixaban**; events 159+38+15 = 212 exactly |
   | ENGAGE | "Warfarin/placebo edoxaban" (treatment) | 296/7035 is **high-dose edoxaban** |

   Cause, confirmed from the registry arm lists: the converter took protocol arms
   **positionally, first and last**, skipping the middle arm — warfarin in RE-LY,
   high-dose edoxaban in ENGAGE. **Not one role was wrong on any of the three.**

   **Still parked, and still needing his judgement:** FOURIER and ODYSSEY
   OUTCOMES (in both `pcsk9-review` and `pcsk9-inhibitors-cv-review`), MARINE and
   ANCHOR in `icosapent-lipid`. **HUA TUO and BERSON were resolved 2026-08-18 as
   part of topic 11** — and they were WORSE than a label inversion: the arms were
   also CROSS-PAIRED across dosing frequencies, which a pure label swap never is.
   That is a reason to expect the remaining four to need the registry results
   section read, not merely re-labelled. The
   method above will decide them — fetch each registry results section and match
   the denominators — but those objects are **withdrawn or live-published**, so
   editing their labels changes a published surface, and the decision to do that
   on four objects at once is his. **What is now known is that on every trial
   tested so far the answer was the same: label wrong, role right, magnitude
   unaffected.** That is the pattern to expect, not a result to assume.

4. **DOAC_CANCER_VTE: `NCT02583191` names the wrong trial — repair it how?**
   The registration is CONKO-011 / AIO-SUP-0115 (AIO-Studien-gGmbH, Germany,
   enrolment 246, primary endpoint *patient-reported treatment satisfaction*
   measured to 4 weeks). **Everything else on that row is SELECT-D** — pmid
   29746227, JCO 2018;36:2017-2023, 8/101 vs 18/102 matching the 7.9% and 17.6%
   in its own quoted sentence. The data is right; the key is wrong. **Options:**
   re-key to `ISRCTN86712308` — which puts a non-ClinicalTrials.gov registration
   into an object where every other trial is an NCT, and the registry-read
   tooling speaks only ClinicalTrials.gov — or treat the row as CONKO-011 and
   re-extract, which discards correct SELECT-D data. **A schema decision, not a
   data one.**

5. **Should the corpus headline move from DerSimonian-Laird to REML? — NOW
   QUANTIFIED, so this is a one-minute decision.** The house rule is REML or
   Paule-Mandel below k=10 and the corpus publishes DL. **Measured on every live
   pool in every SSOT object, 2026-08-18 — 28 pools, all of them k<10:**

   | | |
   |---|---|
   | pools whose point estimate moves at all | **7 of 28** |
   | pools whose CONCLUSION changes | **0 of 28** |
   | median absolute point shift | **0.000%** |
   | largest point shift | **1.36%** (ARNI, HR 0.8835 → 0.8715) |
   | largest interval-width change | **+49%** (ACS_ANTIPLATELET), then +19% (ALIROCUMAB), −13% (ARNI) |

   Twenty-one of the 28 do not move at all, because τ² is already zero under both
   estimators — mostly k=2 pools, where there is nothing for an estimator to
   disagree about.

   **The finding that should decide it: the corpus is ALREADY MIXED.** ARNI
   publishes `HR 0.8715`, which is the REML value; its DL value is 0.8835.
   INCLISIRAN publishes the DL value. **So "the corpus uses DerSimonian-Laird" is
   not true today**, and the choice is not between changing and not changing — it
   is between one estimator and two.

   **Options:** (a) move everything to REML — 7 displayed values change, no
   conclusion changes, and every change needs announcing under
   `display_change_announced`; (b) keep DL everywhere and re-derive ARNI, which
   moves the flagship's headline the wrong way; (c) leave both and state the
   estimator on every card. **Not decided here: (a) and (b) both change published
   numbers, which is his call.**

6. **SGLT2_CKD's replacement question.** ESKD as dialysis-or-transplant, and
   cardiovascular death, are defined identically across CREDENCE, DAPA-CKD and
   EMPA-KIDNEY and reported separately by all three. Same rule as ABLATION_AF:
   the question must be chosen before its answer is known.

---

## ARNI — the measure question, CLOSED 2026-08-18

`1.83 (0.72–4.67)` **is a hazard ratio.** JACC Table 2's column header reads
verbatim `Effect HR (95% CI)`, and the Statistical Analysis section states the
composite was analysed with *"Cox proportional hazard models, with treatment
group and research site as fixed-effect factors. HRs, 95% CIs, and 2-sided P
values are reported."* A third witness needs neither sentence: Table 2's
all-cause death row is 8/95 against 8/95 — crude RR and OR both exactly 1.000 —
and the published value is 1.08. No crude measure produces 1.08 from 8 versus 8.

**ANSWER-HF stays in. k=4 and HR 0.8715 (0.7461–1.0181) stand.** Removing it
would have given 0.8333 (0.7473–0.9292) — a null converted to a positive result,
and wrong.

Identity was established first, by registration id: `NCT04853758` is the only
registration in the document and appears twice in registration context.
PARACHUTE-HF appears eight times, every one a citation of a different trial with
its own win ratio 1.52 (1.28–1.82). Nothing was read before that check.

---

## How to work a topic (the protocol, in order)

1. Identity by **registration id**, before any number.
2. Endpoint definitions read from the **registry, word for word**, before any
   pool. Never inferred from a result sentence: a quote saying what HAPPENED is
   not a quote saying what was COUNTED.
3. The pool stands, or the estimate is withheld **with its reason on the page**.
   A withdrawal needs the same evidence as a claim — withdrawing a correct
   estimate destroys a true finding and publishes the destruction as a discovery.
4. Published-meta comparison **with a denominator**; confirmations shown as
   prominently as errors.
5. Build to v1, run the gates, push, and **verify live, cache-busted**, before
   starting the next topic.

`scripts/estimand_definition_gate.py` tells you WHERE TO LOOK and never what you
will find. It has been wrong in both directions — it over-read ARNI and under-read
SOTAGLIFLOZIN. Verify every verdict against the registry text.

---

## Session log

### 2026-08-18 — lane resumed after the API-500 crash

**Crash state, established rather than assumed.** `HEAD` = `origin/main` =
`a4fbac929`; nothing was committed-but-unpushed and no tracked file was modified.
Nothing was in flight. Two things the crash did leave:

- 20 SSOT objects under `ssot/*/` written at 13:06 on 17 Aug are **untracked** —
  they exist in this working tree and in no clone. That is ledger failure mode
  #4 (a register written into a directory git does not carry).
- `STATUS.md` and `TOOLING-QUEUE.md` did not exist. This file is the first.

**ABLATION_AF closed.** Its last open property was `card_matches_page`, and
chasing it found the gate rather than the page.

`card_alignment_gate.check()` opened with: if the card declares a withheld state,
return UNCHECKABLE. **The word "withdrawn" on the card stopped the gate reading
the page at all.** SGLT2_HF went live at `7124fdbed^` with its card announcing a
withdrawal and its page headline still publishing `HR 0.7785 (0.7296 to 0.8306)`,
and this gate recorded it as "nothing to compare" on every run in between. Proved,
not asserted: the previous version returns `UNCHECKABLE` on those exact bytes and
the current one returns `FAIL`.

The gate now reads the page in both directions and carries a fourth verdict:

| card | page | verdict |
|---|---|---|
| withheld | withheld | **WITHHELD** (exit 3) — the property is met by withholding |
| withheld | renders a value | **FAIL** — the SGLT2_HF state |
| carries a value | withheld | **FAIL** — the index serves what the page retracted |
| value | value | PASS/FAIL, numerically, as before |

Two further fixes went with it:

- **The gate read the wrong tree by construction.** `SSOT` was the hardcoded
  absolute path `F:\rapidmeta-ssot-shell`; run from any sibling clone it graded
  another working tree's index and pages and reported green about bytes nobody was
  pushing. It is now derived from `__file__`. This is the ledger's matched-pair
  false-life defect, still present in a gate.
- **`v1_coverage_audit` over-matched a substring for the third time.** It greps a
  gate's free text for blind-words BEFORE consulting the exit code, so the phrase
  "drift: UNCHECKABLE — 0 of 1 cards were numerically comparable" overrode a
  deliberate exit 3. Two previous patches to that regex had already failed. The
  fix is not a third pattern: **a declared field beats an inferred one**, so exits
  2 and 3 are now read before any text at all, and the text scan survives only for
  exits 0 and 1 where it is still needed.

The headline reader was also re-anchored on the `<h2>Pooled result</h2>` element,
because SGLT2_HF's page now contains prose *about* the old headline and a reader
that cannot tell a headline from a sentence describing one will convict a page for
confessing.

**Effect on the measured standard:** across the 7 v1 objects, properties not
established by any running check fell from 30/98 to 28/98. ABLATION_AF now has
zero UNCHECKABLE properties; its two WITHHELD ones are recorded as met by
withholding, which is what they are.

Corpus-wide the gate is still nearly blind — 5 of 514 cards numerically
comparable, 2 agreeing by withholding, 507 unmeasured — and it says so inline
rather than printing 0.0% drift over 1% of the set.

### 2026-08-18 (continued) — ARNI resolved, SGLT2_CKD withdrawn, three gate defects

**ARNI: the open measure question is ANSWERED and the trial stays in.** Identity
confirmed by NCT04853758 before any number was read. `1.83 (0.72–4.67)` is a
hazard ratio: JACC Table 2's column header reads verbatim `Effect HR (95% CI)`,
and the Statistical Analysis section names Cox proportional hazard models with
treatment group and research site as fixed-effect factors. A third witness needs
neither sentence — Table 2's all-cause death row is 8/95 against 8/95, crude RR
and OR both exactly 1.000, and the published value is 1.08; no crude measure
produces that. **k=4 and HR 0.8715 (0.7461–1.0181) stand.** Dropping the trial
would have made the result positive and would have been wrong.

The answer was already in the object: `model_statement_quote` held that Cox
sentence verbatim, in `935cf870a` — the commit that created the open question.
Two fields never read against each other.

**SGLT2_CKD: estimate WITHDRAWN, on two independent grounds.** The three trials
count kidney-function decline at three different thresholds, each on its own
registry record — CREDENCE a doubling of serum creatinine, DAPA-CKD ≥50% eGFR
decline, EMPA-KIDNEY ≥40%; the ESKD floor differs too (<15 against <10). And
separately: every stored per-trial value was an **odds ratio we derived from 2×2
counts**, while all three trials analyse time to first occurrence — and the index
card published that derived OR under the label **HR**.

Confirmed and stated as prominently: the component *types* agree across all
three, and all three results point the same way (crude RR 0.72, 0.63, 0.77).
Agreement of results is not evidence of a common estimand. The component route
(ESKD as dialysis-or-transplant, and CV death, identically defined in all three)
is identified as the replacement question and **deliberately not taken** — it
needs the registry results sections, and a replacement question must be chosen
before its answer is known. **PARKED.**

SGLT2_CKD **fails `extraction_table`, deliberately and on the record**: three
values, three links, three read/derived markers and **zero verbatim quotes**. The
endpoint definitions are quoted from the registry and the withdrawal rests on
those; the event counts are carried from the extractor and a reader cannot check
one of them. It is finished as a withdrawal, not at v1.

**SGLT2_CKD is NOT one of the 53.** It sits in the CKD section of the index, like
FINERENONE_CV. Counting it would be denominator drift.

**Three gate defects, all found by running the gates rather than by an incident:**

1. **A constant named `WITHHELD` did not match the word "withheld".** PCSK9 and
   SGLT2_CKD were classified as ordinary published values. The gate now hunts its
   own next gap with `--audit-vocabulary`.
2. **The estimand gate's component vocabulary is entirely cardiological.** Three
   different CKD composites all reduced to `{cv_death}` and it reported **PASS —
   "they agree"**. This is the CABANA under-read with the sign flipped: every
   previous under-read failed toward alarm, this one manufactures an agreement.
   Fixed structurally — a recognition list decides PASS, an over-broad hunting
   list decides whether the gate may decide at all.
3. **The jump list double-escaped its own headings.** `_anchor_headings` strips
   tags from already-escaped markup and the caller escapes again, so readers see
   the literal characters `&middot;` and `&#x27;`. **Live on four of the seven v1
   pages** — ARNI 15 occurrences, SGLT2_HF 3, IV_IRON 2, SOTAGLIFLOZIN 1 — and it
   had polluted the anchor ids (`#screen-paragon-hf-nct01920711-middot-pmid-314757`).
   Latent everywhere; it fires only on a heading containing an apostrophe,
   ampersand, quote or angle bracket.

### 2026-08-18 (continued) — PCSK9 withdrawn, and five gate defects in one night

**PCSK9: estimate WITHDRAWN on three independent grounds.** FOURIER's primary
composite counts **coronary revascularization** and ODYSSEY OUTCOMES' does not —
one whole component present in one trial and absent from the other, and
revascularization is the most frequent component of FOURIER's composite. Three
further differences: CV death vs coronary-heart-disease death; any stroke vs
ischaemic stroke only; any MI vs non-fatal MI only. Separately: the stored values
were derived odds ratios while both trials report hazard ratios. And separately
again: **the index published `HR 0.85 (0.79–0.92)` — a number that appears
nowhere in the object**, whose own pooled value was OR 0.8440.

PCSK9 **is** one of the 53 — it sits in `#sp-cardiology` — and it is finished as
a withdrawal, so the count moves to **7 of 53**. SGLT2_CKD does not count: it is
in the CKD section, like FINERENONE_CV.

**Arm labels are inverted on seven trials across four objects.** The arm carrying
role INTERVENTION is labelled "Placebo"; the drug arm carries role CONTROL. All
four are converter output, so this is the converter's arm ordering. **Which half
is wrong — the label or the role — is left open**, because deciding it needs each
trial's arm sizes and event counts from source. **PARKED.**

#### The five gate defects, all found by running the gates rather than by an incident

| gate | defect | direction |
|---|---|---|
| `card_alignment_gate` | a withheld card stopped it reading the page | comfort |
| `card_alignment_gate` | a constant named `WITHHELD` did not match "withheld" | comfort |
| `v1_coverage_audit` | grepped prose before reading the exit code (3rd instance) | comfort |
| `estimand_definition_gate` | vocabulary one specialty wide; three different CKD composites reported as agreeing | **comfort** |
| `arm_identity_gate` | regex carried literal 0x08 bytes — dead since written; and the branch never checked direction | comfort |

Plus two escaping defects in the projectors, one in each direction: heading text
escaped twice, and an em-dash fallback escaped when it should not have been.

**Every one of them failed toward comfort.** That is the ledger's selection
argument reproducing itself inside a single night's work.

### 2026-08-18 (continued) — DOAC_AF withdrawn, and the headline was the comparator

**Topic 8 of 53. DONE, live-verified byte-identical by SHA-256 on both surfaces.**

**The mechanism is new and it is the sharpest one found so far.** The card served
`Published: HR 0.81 (0.73–0.91), k=4`. The page's own bytes embed

```
PUBLISHED_META_BENCHMARKS={MACE:[{label:"Ruff pooled DOAC vs warfarin MA (stroke/SE)",
citation:"Ruff 2014",year:2014,measure:"RR",estimate:.81,lci:.73,uci:.91,k:4,...}]}
```

— the locked local database of published syntheses this review is meant to be
**measured against**. All four numbers on the card are those four numbers, and
the measure was relabelled RR to HR on the way. The object's own pooled value is
OR 0.7817 (0.6710–0.9108) at k=3 and shares no digit with the card. **PCSK9
published a number that was in no object. This published the object's own
comparator.** A page that carries a benchmark table can serve the benchmark as
the finding, and every internal consistency check stays silent because both
numbers are genuinely on the page.

Two further independent grounds: **k was overstated** (card and
`AUTO_INCLUDE_TRIAL_IDS` say four, the pool holds three — ROCKET AF carries
`tE:null, cE:null` so a count-derived pool drops it in silence, and it is the
trial whose registered result is closest to no effect); and **the measure is
misnamed** (every stored value is an OR we derived from counts, while all four
registry records register a Cox analysis of time to first event).

**Stated as prominently, because it is the direction that gets under-reported:
the four endpoint definitions AGREE.** All four registry records count the first
occurrence of stroke or systemic embolism. ARISTOTLE's per-trial value on the
page is the registry's own Cox HR **digit for digit**, and its counts reconcile
exactly (212 = 159+38+15, 265 = 173+76+16). Every comparison points the right
way. **This withdrawal does NOT establish that the four trials cannot be
pooled** — it establishes that THIS pool cannot stand.

**Replacement question identified and deliberately not taken:** pool the four
REGISTERED hazard ratios. Not taken because establishing the above meant reading
them, so their answer is already known — the ABLATION_AF/SGLT2_CKD rule. It also
needs a human choice: ENGAGE registers **five** primary analyses of one composite
whose HRs run 0.79, 0.86 and 0.87, and ROCKET AF's are both "while on treatment"
where ARISTOTLE's is an intended-treatment period. **PARKED.**

#### Three instrument defects, and two of them were mine

| where | defect | direction |
|---|---|---|
| `arm_identity_gate` | a double-dummy label names both drugs, so the inverted-roles branch was skipped entirely | comfort |
| my first fix to it | deleted the control word from a *pure* placebo arm | **comfort** |
| my second fix to it | read the word after "placebo" as a drug — nine objects went FAIL→PASS, eight of them correct detections destroyed | **comfort** |
| `estimand_definition_gate` | **systemic embolism was invisible to all three lists**, including EVENT_LIKE, the one that exists to force UNCHECKABLE on exactly this | comfort |

The estimand one is worth reading twice. `TOOLING-QUEUE.md` records the
structural half of the CKD fix as done, and what it promised was that "the gate
can no longer report agreement from a partial reading". The mechanism for that
promise is the over-broad `EVENT_LIKE` hunting list. **It has renal, oncological,
infectious and ophthalmic terms and no embolism.** The net has the same
specialty-shaped holes as the thing it is netting, so the promise was not kept
and nothing said so. Its own comment had predicted it: *"a gap in THIS list … is
the only comfortable failure left in the design."*

Four registry composites, every one "stroke OR systemic embolism", all four
reduced to `{stroke}`, and the gate answered **PASS — they agree**. The verdict
was right; the reading was half. Fixed in all three lists in one commit, with a
constructible failing input in the selftest (`"Stroke or systemic embolism"` vs
`"Stroke"`: old PASS, new FAIL), because the widening moves **no verdict on any
of the 34 objects** and nothing in a routine run would ever show it mattered.

**And the two bad cuts of my own arm-gate fix are the point of that whole
episode.** Both failed toward comfort, while fixing a defect that failed toward
comfort. Only the corpus sweep caught the second — 1243 objects, old gate against
new, nine moved FAIL→PASS and none the other way. **A fix that only ever turns
red to green needs every conversion read individually.** After narrowing to the
one structure that licenses the rewrite (a double dummy is *symmetric*: both arms
name a placebo), exactly one object moves, and it is a false alarm correctly
removed.

#### The projector defect: four topics read their endpoint definitions and no page showed one

v1's twelfth property is `estimand_definition_read`. Four topics have been
through that step. **Not one of their pages rendered a single definition.**
`PCSK9_REVIEW.html` contains "Clinical Events Committee" zero times while its
object holds FOURIER's registry description verbatim.

The definition sits in the object, the gate reads it *there*, the gate passes,
the property is reported established — and the reader gets prose and has to take
the reading on trust. **If it isn't on the page, it didn't happen.** Two cards
now project from the object: *Endpoint definitions, read from the registry*
(measure, verbatim description, analysis set, registration link, read date, per
trial — and a row saying so when a trial has none) and *Named on this review,
contributing nothing to its pool*. Every page built from now on carries them;
**the four already-done topics do not, and rebuilding them is owed.**

#### Smaller things worth not rediscovering

- **This shell eats one backslash level in heredocs.** A patch written that way
  put `\x08` where `\b` belonged — which is *exactly* how `arm_identity_gate`
  got its literal 0x08 bytes in the first place, per DEFECT ONE in that file.
  Write patch scripts to a file instead.
- **Reading a CRLF file in text mode and comparing it to network bytes always
  mismatches.** It made a successful deploy look like a failed one for two
  polling rounds. Compare bytes, and hash them.
- **`k_consistency_gate` caught my own note** — a sentence written to *explain* a
  k mismatch still reads as a k claim. It was right; the note was reworded rather
  than declared `_STALE`.

### 2026-08-18 (continued) — DOAC_CANCER_VTE withdrawn, and an identity the flagship gate cannot see

**Topic 9 of 53. DONE, live-verified byte-identical by SHA-256 on both surfaces.**

**Four independent grounds**, and the first two are the substantive ones:

1. **A safety endpoint averaged with two efficacy endpoints.** Hokusai
   VTE-Cancer's registered primary counts *recurrent VTE **or major bleeding***;
   CARAVAGGIO's counts recurrent VTE only, and its registry description spells
   out the contents (proximal DVT, upper-limb DVT, PE) with no bleeding.
   **The direction is known**: edoxaban bled more, so including bleeding moves
   Hokusai from 0.71 to the registry's own Cox 0.97 (0.696–1.359). Averaging it
   with efficacy-only endpoints **drags the pool toward the null.**
2. **`NCT02583191` is CONKO-011, not SELECT-D** — see parked item 4.
3. **`HR 0.55 (0.30–1.00)` is reconstructable from nothing.** Object: OR 0.7290
   (0.4914–1.0817) k=3. Benchmark block: 0.63 and 0.71, **so the DOAC_AF
   comparator-leak mechanism did NOT repeat.** Ten candidate pools of the page's
   own four published HRs give 0.60, 0.58, 0.64, 0.49, 0.54, 0.75. The string
   occurs on the page only in CSS and a chart legend. Search bounded, and
   reported as bounded.
4. **k=4 with a pool of 3, for the second topic running.**

**Confirmed as prominently:** Hokusai's counts (67/522, 71/524) and CARAVAGGIO's
(32/576, 46/579) are the registry's own, exactly; Hokusai's page HR matches the
registry Cox digit for digit; the SELECT-D row's numbers are right *for
SELECT-D*; and **every arm role and label is correct on all three trials** —
worth saying, because the two topics before this had every label on the wrong
arm.

#### Two findings that generalise beyond this topic

**A count-derived pool silently drops any trial whose registered primary is a
RATE.** ADAM VTE registers "the rate (percentage) of patients experiencing major
bleeding at 6 months" — 0% of 145 against 2.1% of 142, cumulative incidence with
death as a competing risk. **There are no counts to have**, so it vanishes from a
2×2-derived pool and k falls from 4 to 3 with no surface saying so. **This is the
second topic in a row with that exact shape** (ROCKET AF on DOAC_AF), which makes
it a class: *the published k is a function of which trials happen to have counts,
and nothing declares it.*

**`identity_by_registration_gate` PASSES a row whose registration names a
different trial.** It checks that a registration is *recorded* and *unique per
row* — never that the registration **is** that trial. So the flagship identity
property passed on a row pointing at a German satisfaction study. **It closes the
label→identity direction and leaves registration→identity wide open**, and it
fails toward comfort. The detector is owed and is next.

#### The estimand gate's hunting list fired productively for the first time

It saw `venous thromboembolism`, could not classify it, and returned
**UNCHECKABLE naming the term** rather than comparing two partial readings — on a
topic whose endpoints genuinely disagree. That mechanism has been a promise since
the CKD fix; this is the first time it has been a working check, and it refused
toward *alarm*. The classifier half went in the same commit, and the gate then
reached **WITHDRAWN** independently: `{serious_bleeding, vte}` against `{vte}`
and `{vte}` — the same conclusion I had reached by hand, which is corroboration
rather than substitution. One object moves across the 34; no object gained a pass.

### 2026-08-18 (continued) — the detector owed by topic 9, built before topic 10

`scripts/registration_identity_gate.py`. The ratchet rule is that a defect found
on page N becomes a detector before page N+1, and topic 9's defect was that **the
flagship identity property never checks that the registration IS the trial.**

It screens participants **analysed** against the enrolment the **registration**
records — the two sides state that number independently, so a row keyed to the
wrong trial is a row whose halves were sized by different studies. Verdict is
**`REVIEW`, never `FAIL`**: analysed is legitimately below randomised, and a gate
that convicts on this arithmetic would be switched off within a week.

**Corpus screen, 11 v1 objects, 38 rows: 34 ok, 3 REVIEW, 1 DECLARED.** The three
are DOAC_AF's and all three are correct — two are three-arm trials pooled two arms
at a time, which the gate now states on the line rather than leaving as a bare
shortfall.

**Two defects in my own first cuts, both caught before commit, and both worth
more than the gate:**

- **The threshold excluded its own founding case.** I picked 0.75 to keep
  per-protocol analyses quiet. The SELECT-D row is at 0.825 — *above* it — so the
  one defect the gate exists for would have passed silently. **Choosing a
  threshold that excludes your own fixture is the exact shape of a check built to
  pass.** The selftest now asserts the threshold contains the founding ratio.
- **It read one arm and called it the total.** The v1 objects key analysed
  `treatment`/`control`; I read `intervention`/`control` and summed the control
  arm alone, so **thirteen correctly-keyed rows came back at 46–50%** on the first
  corpus run. `arm_identity_gate` carries a comment about hitting this exact wrong
  key, which I had read. Caught only because the ratios formed a **signature**
  rather than a spread — 49.9, 49.9, 49.8, 50.0, 50.1, 49.9, 50.0. Thirteen
  independent trials do not analyse exactly half their enrolment.

That is now four instrument defects of my own in two topics, every one caught by
running the thing against real data rather than by reading it.

### 2026-08-18 (continued) — INCLISIRAN: the first pool in this lane that STANDS

**Topic 10 of 53. DONE, live-verified byte-identical on both surfaces.**

**This is the one that matters most for whether the lane is applying a standard
or a bias.** Three consecutive withdrawals is a pattern that should make anyone
suspicious of the next verdict. This topic was checked in the same order and to
the same depth and **came out the other way.**

- **Estimand identical in all three registrations.** ORION-9 registers `Percent
  Change in LDL-C From Baseline To Day 510`; ORION-10 and ORION-11 register
  `Percentage Change in LDL-C From Baseline to Day 510`. Same quantity, anchor,
  day, ANCOVA, and the registry reports all three as `Mean Difference (Final
  Values)`. **The only difference between the strings is one word** — the
  orthography trap, and it is not one here.
- **Every per-trial value is the registry's own, digit for digit.** Arm labels
  and roles correct. Arm sizes recorded from the registry and summing to each
  registration's enrolment **exactly**: 482, 1561, 1617.
- **The pooled value reproduces**: −54.0014 (−58.1652 to −49.8377), matching card
  and object to four decimals.
- **Robust in every direction tested**: six estimator × interval combinations
  span −53.95 to −54.00 and all exclude no effect; leave-one-out gives −55.56,
  −52.18, −53.90, all excluding no effect.

**What IS wrong with it is the precision, not the estimate.** I² = 72% on three
studies; the Hartung-Knapp interval is **−63.71 to −44.30**, about twice the width
of the Wald interval on the card, and at this k it is the honest one. **The card
now carries that caveat and its value is unchanged** — the number is correct and
moving it would break a reader's record for nothing.

#### The projector asymmetry this topic exposed

**It rendered the reason for a RETRACTION and never the reason for a CLAIM.** The
withdrawal branch has always printed `withdrawn_reason` first, with a comment
saying "the reason is the deliverable". The standing branch had no equivalent.
After three consecutive withdrawals that is not neutral: **it makes destruction
legible and verification invisible**, on a page whose entire claim is that a
reader can check us. Fixed — `stands_because` now has `withdrawn_reason`'s
prominence.

And the blanket absence disclosure was **true of the conversion and false of the
object**: it announced "no resolvable link to a paper was recoverable" while the
page now carries a registration link per trial. `no_synthesised_absence` cuts both
ways — **an absence that has been filled must stop being announced.**

### 2026-08-18 (continued) — EVOLOCUMAB_MIXED: withdrawn on provenance, and the finding survives

**Topic 11 of 53. DONE, live-verified byte-identical on both surfaces.**

**The estimand was not the problem and the page says so first.** Both
registrations name percent change from baseline in LDL-C at the **mean of weeks
10 and 12**, analysed as a least-squares mean from a repeated-measures linear
model. Identity correct on both.

**Both trials are four-arm 2×2 designs of dosing frequency**, and each registers
**two** comparisons, both *within* a frequency:

| | | |
|---|---|---|
| BERSON | Placebo Q2W vs Evolocumab Q2W | −70.29 (−75.43 to −65.16) |
| BERSON | Placebo QM vs Evolocumab QM | −70.04 (−74.67 to −65.41) |
| Hua Tuo | Placebo Q2W vs Evolocumab 140 mg Q2W | −70.73 (−77.98 to −63.48) |
| Hua Tuo | Placebo QM vs Evolocumab 420 mg QM | −69.74 (−76.51 to −62.97) |

**This object crossed the frequencies on both** — a fortnightly placebo against a
monthly drug arm, a comparison neither trial ran. And the stored values (−71.8,
−70.8) are **neither registered comparison and not the difference between any two
of the four arm means either trial reports**, checked exhaustively.

**What the withdrawal is NOT, stated on the page as prominently as the reason:**
all four registered comparisons lie between **−69.74 and −70.73**, against a
withdrawn pooled value of −71.31. **The ~70% LDL-C reduction is amply supported by
the source records.** What cannot stand is *these numbers*. A reader checking us
against the registry currently finds our conclusion and not our arithmetic, and
the whole claim of this project is that those should be the same thing. **The
registry's four comparisons are now on the page**, so a reader gets the real
values and not only the news that ours were wrong.

**Parked item 3 advances.** BERSON and HUA TUO are resolved — and they were
**worse than a label inversion**: cross-paired arms change the magnitude, where a
pure label swap leaves it intact. The remaining four trials in that parked item
should be expected to need the registry *results* section read, not merely
re-labelled.

### 2026-08-18 (continued) — the multi-arm screen, then COLCHICINE_CVD

**The screen first, because it answers a scope question and the answer is not
"one page".** `declared_contrast_gate` was built before topic 12, per the ratchet,
and run across all 34 objects and 109 trial rows:

| | |
|---|---|
| rows on a **multi-arm registration** — where a fabricated contrast is possible | **26 (24%)** |
| **FAIL** — confirmed fabricated contrast | **1** (Hua Tuo) |
| PASS — the contrast is one the registration declares | 6 |
| **UNCHECKABLE — cannot be cleared** | **19** |

**One confirmed and nineteen unmeasured, over a quarter of the corpus.** Nine of
the nineteen are uncheckable for one reason: the registration declares more than
two arms and **no between-arm analyses at all**, so there is no declared list to
compare against. Recorded as queue item 14 with the signal each group needs, and
an explicit instruction **not to close it by relaxing the matcher.**

It also **narrowed a parked item**: MARINE and ANCHOR (two of the four trials
still parked under item 3) both come back PASS, so whatever is wrong with their
arms is a **label** question with the magnitude intact — not a cross-pairing.
RE-LY and ENGAGE also PASS, confirming by machine what topic 8 established by hand.

---

**Topic 12 of 53 — COLCHICINE_CVD, withdrawn, live-verified.** First topic
**AUTHORED from source** rather than converted: it had no object, so the index
number was published by a page nothing had ever checked.

- **The registered primaries differ by whole components.** COLCOT counts
  **resuscitated cardiac arrest** and **urgent hospitalisation for angina
  requiring revascularisation**; CLEAR SYNERGY's colchicine primary counts neither
  and uses a different revascularisation trigger; LoDoCo2 counts **spontaneous**
  MI. **And CONVINCE is not a composite trial at all** — it registers three
  separate primaries and the first is recurrent non-fatal ischaemic stroke alone.
- **Three trial counts on one page**: the include list names 5, the data holds 3,
  the card published k=2.
- **The headline is unreconstructable** — 33 candidate pools, none gives
  0.75 (0.61–0.91). Third topic in this lane with that shape.
- **The pool drops CLEAR SYNERGY in silence** — the largest trial (7,264) and the
  only null one.

**Credit where the page earned it, and it matters:** LoDoCo2 and COPS have no
ClinicalTrials.gov registration, and the page carries them as `ACTRN-LODOCO2` and
`ACTRN-COPS` **rather than inventing NCT numbers**. On DOAC_CANCER_VTE the
identical situation produced a row keyed to an unrelated German trial.

**My own fifth self-inflicted defect of the session, and the shortest feedback
loop yet:** the two cards I added today used the HTML entity `&mdash;` as a
fallback, passed through the escaper — so a reader saw the literal characters
`&amp;mdash;`. That is the class `TOOLING-QUEUE` item 2 records as unswept, and
the previous lane's own second escaping defect ("an em-dash fallback escaped when
it should not have been"), reproduced by someone who had read both. Fixed at
source with a literal em-dash character, which escapes to itself.

### 2026-08-18 — the card projector, then topic 13

**Cards are PROJECTED from the object now.** Queue item 3 retired for every page
with an object: numbers from the object through the page's own `sig()`, prose
authored and carried as `card_note`. 13 of 14 cards rewritten, 0.0% drift on all
six with a live value. Two of my own defects caught by `--check` before anything
was written: it **guessed** IV_IRON's headline outcome (would have swapped
`RATE_RATIO 0.8066` for `HR 0.978`, a different outcome, on the reader's first
surface) and it **double-escaped** the migrated notes. Multi-outcome objects must
now declare `results.headline_outcome` or the projector refuses.

**Topic 13 of 53 — BEMPEDOIC_ACID, estimate STANDS, live-verified.**

- HR 0.87 (0.79–0.96) **is CLEAR Outcomes' own registered Cox analysis**, digit
  for digit; counts 819/6,992 against 927/6,978 are the registry's own.
- **k=1 is correct, not a shortfall.** Only CLEAR Outcomes registers a
  cardiovascular-event primary; CLEAR Harmony's are safety endpoints and CLEAR
  Serenity's is LDL-C percent change at week 12. Excluding them is right; saying
  so was missing, and now is on the page.
- **Second wrong registration of the session:** `NCT02973841` is **Sono-ease**, a
  40-patient internal-jugular-cannulation device trial, sitting in a bempedoic
  acid include list. It carries no data so it moves no number.
- **The published-meta comparison compares the estimate against itself** — the
  only benchmark entry for this outcome is CLEAR Outcomes. **Honest denominator:
  zero independent syntheses.**
- **The push was blocked by the harness gate and the block was right.**
  `CHK020_ORPHAN_POOLED_RESULT` fired on `poolable:false` plus a displayed value.
  Fixed in the exporter: `poolable:false` was carrying two meanings, and a k=1
  single-study result is not an orphan pool. Verified the real orphan (k=2, no
  `single_study_ref`) still fails.

### 2026-08-18 — topics 14 and 15, and a detector for the class that reverses conclusions

**Topic 14 — CANGRELOR_PCI, WITHDRAWN.** The sharpest data defect of the
programme. Each row carried the primary composite's denominators **exact to the
patient** against event counts that were **all-cause mortality**, a named
secondary in the same registry record. Registry primaries are 290/276, 185/210,
257/322; the page used 8/5, 6/18, 18/18. **Correcting it reverses the
conclusion**: OR 0.8955 (0.7526–1.0656), crossing no effect, against a published
0.81 (0.71–0.91) that excludes it. **Five of six numbers in each 2×2 were right**,
which is why nothing internal could see it.

**A detector followed, and then found nothing more.** `count_provenance_gate`
replays the founding row (FAIL, naming the mortality outcome) against the same row
with the registry's counts (PASS). Three parser faults were fixed before it was
trusted — arm order, rate-valued outcomes, multi-category outcomes summed per arm
— all of which had made correct rows look wrong. **Final corpus screen: zero
FAILs across 37 objects.** The four original FAILs all shared one cause — the
object records no `outcome_definition`, so the gate fell back to the
registration's primary and disagreed with rows deliberately pooling a secondary
(FIDELIO's CV composite, SUMMIT's HF events, pitavastatin's NCEP target
attainment). **A row that does not declare its outcome now returns UNCHECKABLE**;
convicting there would make one FAIL mean two incompatible things.

**Topic 15 — RIVAROXABAN_VASC, WITHDRAWN.** VOYAGER PAD's composite adds **acute
limb ischaemia and major amputation**, in no other trial here; COMMANDER HF counts
**all-cause** rather than cardiovascular death and registers an event **rate**.
The arithmetic reproduces exactly — 0.8494 (0.7775–0.9278) against a card of 0.85
(0.77–0.94) — so nothing was miscomputed; what was averaged should not have been.
All four per-trial values are on the page and **all four point the same way**.

**Queue item 17 in the wild, second instance:** the only benchmark entry is
COMPASS, which is an included trial. Here it disagrees with the pool so nothing
was falsely corroborated; on BEMPEDOIC_ACID the same configuration agreed
perfectly with itself.

---

## Where the next lane picks up

**State at handover.** `HEAD` == `origin/main`; every commit is pushed and every
page below is verified live, cache-busted, against the bytes on disk.

Live-verified this session: **ARNI, SGLT2_HF, IV_IRON, SOTAGLIFLOZIN, PCSK9,
SGLT2_CKD, DOAC_AF, DOAC_CANCER_VTE, INCLISIRAN, EVOLOCUMAB_MIXED, COLCHICINE_CVD, BEMPEDOIC_ACID, CANGRELOR_PCI, RIVAROXABAN_VASC, INTENSIVE_BP.** Each was confirmed byte-identical by
SHA-256 against the served bytes, cache-busted. ALIROCUMAB, FINERENONE_CV and ABLATION_AF were unchanged and needed
no rebuild.

**Start here, in this order:**

1. **The 1 remaining topic with a live estimate and no object.** These are the
   dangerous ones and every one examined so far has been withdrawable:
      HFREF_NMA. Objects already exist
   under `ssot/` for several of them.
2. **Rebuild the four earlier topics** so their endpoint definitions are on the
   page. They were read and are invisible; see the projector defect above.
3. **The 26 audit-first cardiology topics.** They publish no estimate, so there
   is no live claim to defend — only identity, endpoint definitions, and a build.
   The `k>=3` self-contradiction on them was resolved corpus-wide at `abfa6b999`.
2. **The 11 with a live estimate and no object.** These are the dangerous ones —
   a published pooled number that nothing in the current standard has checked.
   Every one that has been looked at so far turned out to be withdrawable.
3. **Tooling queue item 1.2 — thresholds are not components.** Until the estimand
   gate can compare a `≥40%` decline against a `≥50%` decline, it will keep
   returning UNCHECKABLE on renal topics and every verdict there stays manual.
   The SGLT2_CKD case is its fixture.

**Two habits that earned their keep tonight, both from the ledger:**

- **Compare the artefact you are about to ship against the one you are replacing,
  by content.** It caught a rebuild that silently dropped `1.50` and `1.57` from
  ARNI's page, and it caught the escape defect by counting occurrences after each
  fix instead of declaring the fix done — 15 → 10 → 1 → 0, three separate sites.
- **Run the gate before trusting the page, and read what it says rather than
  routing around it.** The push was blocked once tonight, by a check that was
  wrong; the fix was to the check, with a constructible failing input, not a
  bypass.

**One habit that did not, and is worth naming:** I piped a long-running batch
through `tail`, which buffers all output to the end — the exact thing
`scripts/GATES.md` warns against, quoted in the file I had already read. Knowing a
rule does not apply it. Only a check does.
