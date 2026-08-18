# STATUS — the cardiology programme, and what is parked

**Denominator: 53 cardiology topics.** Derived, not recalled: the `#sp-cardiology`
section of `index.html` carries 54 page links, one of which
(`SOTAGLIFLOZIN_HF_AUTO_FULL_REVIEW.html`, 1,605 bytes) is a redirect stub
consolidated at `ce1e9dc0e`. 54 − 1 = 53. Re-derive with
`python scripts/cardio_program_status.py` rather than quoting this line.

**DONE: 7 of 53.**

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

`FINERENONE_CV` is also at v1 and is NOT counted here: it does not sit in the
cardiology section of the index. Counting it would be the denominator drift this
file exists to prevent.

---

## The remaining 46, by what is actually on them today

Measured from the index cards, not assumed:

| state | n | what it means |
|---|---|---|
| **Audit-first build** | 26 | no estimate ever published; the topic has never been taken through |
| **live estimate, no v1 object** | 11 | a number is published that nothing in the current standard has checked |
| **withdrawn** | 7 | an estimate was retracted; the reason on the page has NOT been re-verified |
| **not poolable** | 1 | MITRAL_FUNCMR — COAPT vs MITRA-FR, stated per-trial |
| **no card at all** | 1 | INCRETIN_HFpEF is linked from the table and has no card |

The 11 with a live estimate and no object are the ones to treat as urgent. An
audit-first page publishes nothing and therefore misleads nobody; a page
publishing a pooled hazard ratio that no endpoint read stands behind is the
SGLT2_HF state, corpus-wide.

---

## Findings logged but not yet acted on

**The 26 audit-first cards contradict themselves in public.** Every one reads
`Audit-first build · N trials · AACT-verified · k>=3`, and on 13 of the 26 that
same string says `2 trials` and `k>=3` in the same breath. Either the k>=3 is a
selection criterion mislabelled as a property of the topic, or the trial count is
wrong. `card_alignment_gate` cannot see this: an audit-first card is UNCHECKABLE
by construction, so the one surface a reader meets first has an unchecked
self-contradiction on 26 cardiology pages. Not yet diagnosed — logged so the next
lane does not rediscover it.

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

3. **PCSK9 and three other objects: are the arm LABELS wrong, or the ROLES?**
   Seven trials across four objects record the intervention arm labelled
   "Placebo" and the drug arm as the control — FOURIER and ODYSSEY OUTCOMES (in
   both `pcsk9-review` and `pcsk9-inhibitors-cv-review`), MARINE and ANCHOR in
   `icosapent-lipid`, HUA TUO in `evolocumab-mixed-dyslipidemia`. All four are
   converter output, so it is the converter's arm ordering. The pooled estimate
   can be right in magnitude while every label is on the wrong arm — that is how
   EAST-AFNET 4's swap survived. **Deciding it needs each trial's own arm sizes
   and event counts from source**, which the protocol-only registry endpoint does
   not return. Left as a recorded contradiction rather than guessed.

4. **SGLT2_CKD's replacement question.** ESKD as dialysis-or-transplant, and
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
