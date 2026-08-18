# STATUS — the cardiology programme, and what is parked

**Denominator: 53 cardiology topics.** Derived, not recalled: the `#sp-cardiology`
section of `index.html` carries 54 page links, one of which
(`SOTAGLIFLOZIN_HF_AUTO_FULL_REVIEW.html`, 1,605 bytes) is a redirect stub
consolidated at `ce1e9dc0e`. 54 − 1 = 53. Re-derive with
`python scripts/cardio_program_status.py` rather than quoting this line.

**DONE: 26 of 53.**

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
| 17 | APIXABAN_AF | **withdrawn, re-verified** | CONFIRMED: ARISTOTLE/AVERROES register stroke-SE, PACIFIC-AF/RENAL-AF register bleeding |
| 18 | APIXABAN_ACS | **withdrawn, reason REPLACED** | the card's reason was FALSE — both trials register bleeding; withdrawn instead on rate-vs-percentage, a dose subset, and scope |
| 19 | EVOLOCUMAB_DYSLIP | **withdrawn, re-verified** | CONFIRMED+sharpened: OSLER-2's primary is 'Number of Participants With Adverse Events'; FOURIER's counts and arm order are also wrong |
| 20 | RIVAROXABAN_ACS | **withdrawn, re-verified** | CONFIRMED+sharpened: ATLAS ACS TIMI 46 registers BOTH a bleeding and an efficacy primary, and no choice is recorded |
| 21 | DABIGATRAN_VTE | **withdrawn, re-verified** | CONFIRMED+sharpened: FOUR endpoint types; RE-MEDY's stored count is 1,404 of 1,430 — 98%, impossible |
| 22 | BOCOCIZUMAB_LIPID | **withdrawn, re-verified** | CONFIRMED: endpoints AGREE and the MEASURE is the defect — an OR on a continuous percent-change endpoint |
| 23 | ATTR_CM | **withdrawn, re-verified** | CONFIRMED+sharpened: hierarchical win-ratio endpoints, and the two hierarchies differ (4 levels vs 2) |
| 24 | MAVACAMTEN_HCM | **withdrawn, re-verified** | CONFIRMED+deepened: three UNRELATED primaries — a responder composite, an SRT decision, a continuous gradient |
| 25 | MITRAL_FUNCMR | **not poolable, re-verified** | CONFIRMED+sharpened: 12m vs 24m, all-cause vs CV death, FIRST vs RECURRENT events; old card named 2 of 3 trials |
| 26 | INCRETIN_HFpEF | **withdrawn** | two of three trials register ONLY continuous co-primaries; and its card was INVISIBLE to our own regex |

`FINERENONE_CV` is also at v1 and is NOT counted here: it does not sit in the
cardiology section of the index. Counting it would be the denominator drift this
file exists to prevent.

---

## The remaining 27, by what is actually on them today

Measured from the index cards, not assumed:

| state | n | what it means |
|---|---|---|
| **Audit-first build** | 26 | no estimate ever published; the topic has never been taken through |
| **live estimate, no v1 object** | 1 | a number is published that nothing in the current standard has checked |
| **withdrawn** | 0 | all eight have now been re-verified against the registry |
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

6. **HFREF_NMA needs a PROTOCOL decision before it can be worked at all, and
   the v1 standard does not contain one.** It is a NETWORK meta-analysis: 28
   trials, 15 nodes. Every rule in the standard is written for a pairwise pool.
   "Identity by registration id" applies per trial (28 of them); "the pool stands
   or is withheld with its reason" applies per CONTRAST, and a 15-node network has
   many. **There is no rule for what a withdrawal means when one contrast is sound
   and another is not.**

   **Measured before parking, because a park needs evidence too: the network's 28
   trials are not keyed to registrations.** The page carries **12 distinct NCT
   strings for 28 trials**, and several of those twelve — `NCT01920711`,
   `NCT02924727`, `NCT05901831`, `NCT01035255` — are the shared runtime residue
   that appears on unrelated pages. So the protocol's **first** step cannot be
   satisfied from this page as it stands.

   **Credit where the page has already earned it, and it has:** its own embedded
   verdict states that the per-trial integrity gates have **not** been run and that
   *"absence of findings here is absence of testing, not a clean bill"*; that the
   network fit reproduces its anchor **to 8 decimal places in R 4.6.0 / netmeta
   3.6.1**; that **no inconsistency test is fitted**, with the reason (the direct
   Placebo–ARB leg carries 9 events, minimum detectable inconsistency 8.06-fold);
   and that its **AMSTAR-2 confidence is CRITICALLY LOW, stated on the face of the
   app.** That is more self-disclosure than most pages in this corpus.

   **Options:** (a) extend the standard to networks first, then work it — the
   honest order, and it is a real piece of design; (b) work it as 28 pairwise
   identity reads and leave the contrast-level verdict undefined; (c) leave it and
   take the remaining pairwise topics first. **Not decided here.** It is roughly
   two to three topics of work at this depth and it is the only NMA among the 53.

7. **An AUDIT-FIRST topic cannot currently clear the harness gate, and the gate
   is right.** MAVACAMTEN_OHCM was built to standard — identity established,
   endpoint definition read from the registry — and **the push was refused**, twice,
   for the correct reason: an artefact with no displayed estimate yields almost
   nothing an artefact-decidable check can see, so the checks that do run can only
   pass *vacuously*. `CHK020` was vacuous because there is no displayed pool;
   `CHK024` because there is no network. One check executed, it was INVALID, and
   100% INVALID is above the gate's 50% ceiling.

   **Nothing here is broken.** The gate exists to refuse exactly this — a green
   produced by a check that could not have failed — and it did. The object was
   corrected once on the way (`poolable: None`, not `False`: an unmade verdict is
   not a negative one), which was a real fault of mine and is fixed.

   **The open question is what "built to standard" MEANS for a topic that
   publishes no estimate.** Twenty-six of the 53 cardiology topics are audit-first.
   If they cannot clear the harness, either they cannot be marked done, or the
   harness needs an audit-first path that checks what such a page DOES assert —
   identity, endpoint definitions, and the absence itself — rather than a pooled
   value it correctly does not have.

   **Options:** (a) give the harness an audit-first artefact shape; (b) require
   audit-first objects to carry per-trial rows so ordinary checks apply; (c) accept
   that audit-first topics are "built but not certifiable" and say so on the page.
   **Not decided here, and it gates 26 of the remaining 37 topics.**

   **What shipped anyway, because it needs no page rebuild:** the card said
   `2 trials` and the page contains **one**. EXPLORER-HCM (NCT03470545) is the only
   trial on it; `VALOR` appears **zero times** in the file. The card is corrected
   and names the trial and its registration.

8. **SGLT2_CKD's replacement question.** ESKD as dialysis-or-transplant, and
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

### 2026-08-18 — the withdrawn topics, re-verified: one reason was FALSE

**The eight withdrawn topics are unblocked by the audit-first question and they
close properly**, because a withdrawn topic counts as done when its reason is
current, sourced and on the page. Two done.

**Topic 17 — APIXABAN_AF: CONFIRMED.** ARISTOTLE and AVERROES register stroke or
systemic embolism; PACIFIC-AF and RENAL-AF register ISTH major or clinically
relevant non-major **bleeding**. For an anticoagulant those move in **opposite
directions**, so averaging them yields a number estimating neither, whose sign
depends on the trial mix. Sharpened further: AVERROES registers a **rate**, and
the two bleeding trials (249 and 82) are tiny beside ARISTOTLE's 9,120 — so the
direction was always set by the efficacy trials while the estimand was
contaminated by the safety ones. **The re-verification could have reversed this
and did not.**

**Topic 18 — APIXABAN_ACS: WITHDRAWAL CONFIRMED, REASON REPLACED. The card's
reason was false.** It said "bleeding and efficacy endpoints pooled". **Both
trials register bleeding** — APPRAISE-1 an *event rate* of major + CRNM bleeding,
APPRAISE-J a *percentage* of participants with ISTH major + CRNM bleeding. There
was no efficacy endpoint in the pool at all.

It still cannot stand, on three grounds the registry **does** support: a rate
pooled with a percentage as if both were counts; APPRAISE-1's primary being
restricted to **"Treated Participants With Placebo or Apixaban LOW Doses"** — its
315-against-599 arms are not a randomised comparison; and a review whose title
promises an ischaemic-outcome question answering a bleeding one.

**This is the first confirmed instance of the failure mode the re-verification
pass exists to catch: a withdrawal whose published reason is false.** A reader who
accepted that card was told something the source records contradict. Six
withdrawn topics remain unre-verified.

### 2026-08-18 — all eight withdrawn topics re-verified. One reason in eight was FALSE.

**The denominator, which is the point of having done this:**

| verdict | n |
|---|---|
| reason survived re-verification **unchanged** | **1** (APIXABAN_AF) |
| reason **confirmed and sharpened** — survived, and the registry supplied more | **6** |
| reason **FALSE** — refuted by the registrations, withdrawal upheld on other grounds | **1** (APIXABAN_ACS) |
| withdrawal **reversed**, estimate restored | **0** |

**Eight of eight withdrawals were correct as decisions. One of eight was wrong in
its published explanation.** That is the number worth carrying: **we had treated
withdrawal as the safe outcome — the thing you do when unsure — and APIXABAN_ACS
shows a withdrawal is a published claim that can be wrong on its own terms.** Its
card said "bleeding and efficacy endpoints pooled" and **both** trials register
bleeding. A reader who accepted that explanation was misled just as surely as by a
bad estimate, and by the old rule that topic was already "done".

**The counter-case matters as much:** RIVAROXABAN_ACS carries *identical card
wording* and the wording is **true** there — ATLAS ACS TIMI 46 really does
register both a bleeding and an efficacy primary. The same sentence was right on
one page and false on another, and only reading the registrations distinguishes
them.

**What re-verification added beyond confirming:** FOURIER's stored counts are not
its primary's and its arms are inverted; RE-MEDY is recorded as 1,404 events in
1,430 participants (98%, impossible for recurrent VTE); ATTRibute-CM's hierarchy
has four levels to ATTR-ACT's two, its lower two being continuous change scores;
DABIGATRAN_VTE has four endpoint types, not two; MAVACAMTEN_HCM's three trials
register three unrelated primaries, one of them a treatment *decision*.

**And one topic inverts the whole pattern.** BOCOCIZUMAB_LIPID's three
registrations declare **the same** continuous primary — the endpoints agree
perfectly and **the measure** is the defect: an odds ratio built from an
undocumented dichotomisation of a mean percent change. **A mean-difference
synthesis there is genuinely defensible**, and is the one parked replacement in
this set that is squarely available.

### 2026-08-18 — the two odd topics, and a card our own tools could not see

**Topic 25 — MITRAL_FUNCMR: NOT POOLABLE, confirmed and sharpened.** The one
cardiology topic that reached the right answer **without a detector**, by a human
noticing two headline numbers were not comparable. The registry supplies the
evidence now: MITRA-FR counts all-cause death + HF hospitalisation at **12
months**; RESHAPE-HF2 counts **recurrent** HF hospitalisation + **cardiovascular**
death within **24 months**; COAPT registers an effectiveness primary at 24 months
*and* a device-safety primary at 12. **The old card named two of the three trials**
— RESHAPE-HF2 is on the page and supplies the third composite and a continuous
KCCQ primary.

**Topic 26 — INCRETIN_HFpEF: WITHDRAWN, and why it was never caught is the
finding.** STEP-HFpEF and STEP-HFpEF DM register **only continuous co-primaries**
— KCCQ change and body-weight change. Neither can produce a 2×2, and the counts
stored for STEP-HFpEF DM (7/310, 18/306) **match no registered primary of that
trial**. SUMMIT's 29/364 and 52/367 are its registered event co-primary and are
the only defensible row.

**Its card was invisible to our own tooling.** It was reported as having *no card*.
It has one, publishing `HR 0.41 (0.22–0.79), k=3` — a different **measure**, a
different **value** and a different **trial count** from the object's OR 0.4846
(0.3178–0.7389) at k=2. Both `cardio_program_status` and `project_index_cards`
matched card links with `[A-Z0-9_]+\.html`, **which cannot match the lowercase
`p` in HFpEF**. For as long as those tools have run, this topic was reported
uncarded, its card was never compared with its page, and the projector skipped it.
**A page invisible to the tool that counts pages is worse than an uncounted page:
it is counted as a different thing.** Both regexes fixed.

**Two replacement analyses are now squarely available and need no estimand
judgement** — and they are the first cases in this programme where we can hand a
reader a correct number rather than a withdrawal:

1. **BOCOCIZUMAB_LIPID** — all three registrations declare the same continuous
   primary; a **mean-difference** synthesis of percent change in LDL-C.
2. **INCRETIN_HFpEF** — all three trials share a KCCQ clinical-summary-score
   primary; a **mean-difference** synthesis of symptom benefit.

Both need each trial's least-squares mean difference read from its results record.
**They should be done before more withdrawals**: a project that only removes
numbers is easy to dismiss.

---

### 2026-08-18 — the two REPLACEMENT analyses: a correct number in place of an absence

**Twenty-six topics in, this project had withdrawn or corrected far more than it
had delivered.** Every one of those was right. But a project that only removes
numbers is easy to dismiss, and these are the two cases where the trials support
an analysis a reader can be handed instead. **Neither needed an estimand
judgement, which is exactly why they were unblocked.**

**BOCOCIZUMAB_LIPID — MD −55.46 (−58.84 to −52.07) percentage points, REML, k=5,
n=3,628.** All five registrations declare the identical primary. **The estimand
was never the problem; the measure was** — the withdrawn value was an odds ratio
from an undocumented dichotomisation whose counts implied a 91% "event" rate in
placebo. Every input is the registry's own least-squares mean difference. The
point spans −55.43 to −55.53 across six estimator × interval combinations;
leave-one-out gives −54.60 to −56.50. **REML by choice, not inheritance** — a new
analysis, so the estimator was picked correctly from the start. **Two trials were
added that the withdrawn pool never had**, and that is stated so the k change is
not silent. **LDL-C is a surrogate, and bococizumab was discontinued for
immunogenicity — the page says so.**

**INCRETIN_HFpEF — MD 7.43 (5.09 to 9.77) KCCQ points, k=2, n=1,094, I² 0%.** All
three trials register the KCCQ clinical summary score. **Pooled at k=2, not 3, and
that is the honest number:** STEP-HFpEF DM's registry record has **no results
section**, its published value exists in the literature, and it is **deliberately
not imported** — every number on this page is registry-sourced and breaking that
for one data point would cost the guarantee that makes the rest checkable. At k=2
the Hartung-Knapp interval is **1.80 to 13.06** and is arguably the honest one;
both are recorded. **A seven-point KCCQ difference is a symptom benefit, not an
event reduction.**

Both objects keep **both** outcomes — the withdrawn one in full with its reason,
and the replacement beside it — with `headline_outcome` declared so the card leads
with the replacement rather than the retraction.

**Three of my own defects on the way, all caught before or at the gate:** an
append-shaped patch script run twice, appending one outcome three times (results
were keyed by id, so every gate passed and it had to be looked for); the
case-sensitive filename pattern found in **eight** further scripts including
`card_alignment_gate` itself; and my replacement card note using the word
"withdrawn", which correctly tripped that gate's SGLT2_HF rule. **The rule was not
weakened — the card was reworded.**

**26 of 53 topics. 25 found by instruments; 1 — MITRAL_FUNCMR — found by a person
noticing two headline numbers were not comparable.** That ratio is the argument
for the harness, and the single exception is the argument against trusting it
completely.

### 2026-08-18 — every reported figure re-run after the filename-regex fix

**I said every count those eight scripts produced was suspect. That overstated it,
and the correction is smaller and more precise than the claim.** Re-measured:

| figure as reported | re-run | moved? |
|---|---|---|
| cardiology denominator, **53 topics** | 53 | **no** |
| headline reproduction, **514 of 514** | 514 of 514, 0 failures | **no — that screen never used a filename pattern** |
| multi-arm rows, **26 of 109** | 29 of 154 | **no — the object corpus grew from 34 to 49; the original was right at the time** |
| silent exclusion, **818 trials / 360 pages** | **811 / 355** | **YES — corrected below** |
| card drift | 0.0% over 9 comparable of 522 | **no — but see the blast radius** |

**THE ONE CORRECTION: 818 dropped trials across 360 pages should read 811 across
355.** And the cause is **not** the regex: it is **my own rebuilds**. Pages
rebuilt through the tabbed projector do not carry an `AUTO_INCLUDE_TRIAL_IDS`
block, so they moved from measurable into UNREAD, which rose from 583 to 598.
**Isolating the regex alone accounts for 1 trial and 1 page** (810 / 354 with a
case-insensitive key).

**THE BLAST RADIUS OF THE FILENAME BUG IS ONE PAGE, not the corpus.** Only **19 of
~1,500 files carry a lowercase letter in the stem**, and of those only
`INCRETIN_HFpEF_REVIEW.html` is a review page with a card — the rest are
dashboards and landing pages with no card to compare. So the defect was real,
consequential on the page it hit (a card publishing `HR 0.41, k=3` against an
object holding `OR 0.4846, k=2`, never once compared), and **narrow**.

**Both halves of that are worth carrying: the bug mattered, and my estimate of how
much it mattered was wrong in the alarming direction.** A sweep that finds a
pattern in eight files invites the inference that eight files' worth of numbers
are wrong; measuring showed one. **The inference was mine, not the measurement's.**

## Where the next lane picks up

**HANDOVER, written 2026-08-18 while there was still room to write it properly
rather than at the moment of running out. Two lanes have been lost mid-run; the
one that handed over cleanly cost nothing.**

### State

`HEAD` == `origin/main`. Every page below is live-verified **byte-identical by
SHA-256** against the served bytes, cache-busted. **26 of 53 cardiology topics
done.** The programme began this stretch at 7.

**Nothing is in flight.** No half-built page, no uncommitted object, no page
installed without its card projected.

### What is DONE, and what "done" now means

A topic is done when it has an SSOT object in `PAGE_MAP`, is built through the
tabbed projector, its identity is keyed by registration id, **every contributing
trial's endpoint definition has been READ FROM THE REGISTRY**, and the pool either
stands with its justification rendered or is withheld with its reason **and the
source's own values** on the page. A withdrawal counts as done. **A withdrawal
whose reason has not been re-verified does not** — that rule was added this session
and it cost one topic (APIXABAN_ACS) its "done" status until the reason was fixed.

**All 8 withdrawn topics are re-verified. All live-estimate topics are done.**
There are no unchecked published pooled numbers left in cardiology.

### The three things that are BLOCKED, and on what

1. **26 audit-first topics — blocked on Mahmood's decision** (parked item 7). An
   audit-first page publishes no estimate, so the harness gate's checks can only
   pass vacuously and it correctly refuses to certify. MAVACAMTEN_OHCM was built
   to standard and the push was refused twice. **This gates 26 of the remaining
   27 topics.** Three options are written out in the parked item.
2. **HFREF_NMA — blocked on a protocol decision** (parked item 6). The only NMA
   among the 53. The v1 standard is written for pairwise pools and has no rule for
   a 15-node network where one contrast is sound and another is not.
3. **The estimator question** (parked item 5) — quantified, 7 of 28 pools move, 0
   conclusions change, corpus already mixed. **Mahmood's call, do not pre-empt it.**

### The two REPLACEMENT ANALYSES that are unblocked and should come first

These are the only cases in the programme where a reader can be handed a **correct
number** rather than a withdrawal, and neither needs an estimand judgement:

- **BOCOCIZUMAB_LIPID** — all three registrations declare the same continuous
  primary (percent change in LDL-C at week 12). A **mean-difference** synthesis.
- **INCRETIN_HFpEF** — all three trials share a KCCQ clinical-summary-score
  primary. A **mean-difference** synthesis of symptom benefit.

Both need each trial's least-squares mean difference read from its **results**
record — a source step this session did not take. **Do these before more
withdrawals. A project that only removes numbers is easy to dismiss.**

### Tooling queue, in the order agreed

0. **DONE since this was written:** item 19 is built (`withdrawal_reason_gate`,
   corpus 49 objects: 1 FAIL, 5 PASS, 43 NOT_APPLICABLE), and **both replacement
   analyses are delivered and live.** Five one-off maintenance scripts still carry
   the case-sensitive filename pattern (`decontaminate_sglt2_clones`,
   `verify_decontamination`, `inject_e156_claim_buttons`, `restyle_index_nyt`,
   `extract_to_ssot`'s second pattern) — **cheap, and every count they produced is
   suspect until fixed.**
1. ~~Item 19 — the false-withdrawal-reason check.~~ **BUILT.** Founding fixtures
   and unusually good: APIXABAN_ACS (card says "bleeding and efficacy pooled",
   **both** trials register bleeding → FALSE) and RIVAROXABAN_ACS (**identical
   card wording**, and there it is TRUE). A detector with a true positive and a
   true negative from the same sentence.
2. **Item 18 — the 31 UNCHECKABLE count-provenance rows**, mostly objects with no
   recorded `outcome_definition`. The three unexplained FAILs are already resolved:
   all benign, same cause.
3. **Item 14 — the 19 unclearable multi-arm rows.** Establish the signal each group
   needs. **Do not close it by relaxing the matcher.**
4. **Item 2 — the six remaining `&amp;mdash;` instances**, all in the DTA
   programme, a different generation.

### Working practices that cost real time when ignored

- **Never write a regex through a shell heredoc.** It eats one backslash level and
  produces literal `0x08` bytes that render as nothing. This happened **three
  times** in one session, including inside the file that documents the same defect.
  Use the Write tool.
- **Read the first corpus run of any new screen before reporting it.** Three
  separate screens produced spectacular false findings on their first run — 43 of
  56 cards "wrong", 9 objects wrongly cleared, every included trial "dropped" —
  and every one was an artefact of the instrument.
- **Compare the artefact you are about to ship against the one you are replacing,
  by content.** Numerals present before and absent after is the check that catches
  a rebuild dropping a finding.
- **A gate that blocks you is usually right.** Three blocked pushes this session,
  three correct blocks, three fixes to the object or the exporter and none to the
  check.

