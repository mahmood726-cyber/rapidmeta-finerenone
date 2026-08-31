# Re-keying twenty topics by drug class: the difference is +3, and it rests on one drug

**Date:** 2026-08-31 · **Frame:** `F:\claude-temp\pend\cdsr_frame_cardiology.jsonl` (peer lane, reused not rebuilt)
**Code:** `scripts/rekey20/` · **Artefacts:** `evidence/2026-08-31-rekey/`

---

## WHAT THIS FOUND

**Re-keying twenty topics from drug to drug class produced ONE independent new counterpart.**
Not three: the three topics that flipped are `bosentan-pah`, `bosentan-pah-children` and
`bosentan-pah-monotherapy`, and all three gained the same single review, `CD004434`. One
observation wearing three names.

⭐ **And that is itself the more portable finding: this corpus holds topics that are one
question under several names, so ANY per-topic count taken over it carries that inflation.**

**The larger result runs opposite to the hypothesis we set out to test.** `CD012735 Pitavastatin
for lowering lipids` names our drug **in its title** — intervention identity is a perfect match —
and the pair still dies, on the *condition*: ours is "hypercholesterolemia", theirs is "lowering
lipids". **There is a second axis of unit-of-work mismatch that re-keying the intervention cannot
reach.** Alongside it, **11 of 20 topics produce no candidate in either arm**, and five of those
have a working class key and simply nothing in the frame to find. Together those say the
84-of-105 kill on intervention identity **may have been masking ABSENCE rather than MISMATCH** —
a bigger result than the +3, and pointing the other way.

---

## THE MEASUREMENT

| arm | candidates | verified | topics with a judged counterpart |
|---|---|---|---|
| **A — drug-keyed** (what the corpus is) | 7 | 2 | **1 / 20** |
| **B — class only** (re-key as replacement) | 13 | 8 | 3 / 20 |
| **A∪B — drug + class** (re-key as operated) | 20 | 10 | **4 / 20** |

**Original arm → re-keyed arm: 1 → 4.** Reported as **one independent new counterpart out of
twenty topics**, never as +3.

⛔ **The absolute counts are NOT quotable.** Shortlist noise and the frame's 80.3% recall
contaminate both arms equally, so the DIFFERENCE is the measurement — that sentence belongs
beside the numbers, not after them.

⛔ **And the difference itself is weaker than +3 makes it look.** All three flipped topics are
`bosentan-pah`, `bosentan-pah-children`, `bosentan-pah-monotherapy`; all three gained the same
single review, `CD004434 Endothelin receptor antagonists for pulmonary arterial hypertension`.
**One drug, one Cochrane review, three near-duplicate corpus topics. The effective independent
n is 1, not 3.** The "if 3 → 15 the case is made" threshold is not met and is not close.

---

## PREDICTION, and which way it missed

Written to `evidence/2026-08-31-rekey/PREDICTION.md` before the scan ran.

| arm | predicted | observed |
|---|---|---|
| A drug | 4 / 20 | **1 / 20** |
| B class | 9 / 20 | **3 / 20** |
| A∪B | 11 / 20 | **4 / 20** |
| difference | +7 | **+3** |

**I named the direction correctly for the re-keyed arm and then missed it the same way on the
arm I had hedged the other way.** I predicted I would be OPTIMISTIC on A∪B, for two reasons
stated in advance — the USAN class phrase is often not Cochrane's phrase, and a quarter of the
sample are antibodies whose stem is a modality. Both happened. But I also wrote that the
counter-risk was being PESSIMISTIC on the drug arm, and the drug arm came in at a quarter of my
figure. **The miss was optimistic on both arms and on the difference.**

---

## THE RULE

Stated once, in `scripts/rekey20/rekey_rule.py`, applied mechanically to all 56 cardiology
topics. No topic was hand-adjusted.

> **R1** Split the title at the first condition connective (`" in "`, `" for "`, `" after "`).
> Before it is the intervention span; after it, truncated at the first terminator, the condition.
> **R2** A token in the intervention span is a DRUG iff **ChEMBL** resolves it to a molecule with
> `max_phase >= 1`. The lexicon is the authority's, not mine.
> **R3** A topic is DRUG-KEYED iff its intervention span holds exactly one drug.
> **R4** RE-KEY: replace the drug with its class — the molecule's **USAN stem definition**.
> Nothing else about the topic changes.

The USAN stem is the published drug-class vocabulary that review titles are written in:
`-entan` → *endothelin receptor antagonists*, which is `CD004434`'s title verbatim. Using one
external authority for both the lexicon and the class leaves no place for my judgement to enter.

### Population and sample

⚠️ **"56 cardiology topics" was first published as a REACH COUNT.** `build_pool.py` opened with
`if not os.path.exists(f): continue`, which silently dropped every `ssot/` directory holding no
object of its own name — so the figure was "directories I got to", read as "topics that exist".
Refused by `scripts/audit_exclusion_by_absence.py --gate`, correctly, and fixed by partitioning
the walk into named kinds and asserting the parts sum to it:

```
ssot/ directories walked          : 158
  carrying an object of their name: 155
  NAMED ABSENT (no <name>.json)   : 3   __pycache__, figs, registration
  partition sums to the walk      : 155 + 3 == 158  HOLDS
of the 155 objects, cardiology    : 56
```

**The three skipped items are infrastructure directories, not topics, so the reach figure and
the true figure coincide — but that could not be known until the skip was made visible**, which
is the whole point. 56 now stands with its composition stated.

56 cardiology topics → **32 drug-keyed** → **20 drawn at seed 20260831**, recorded in `SEED.md`
before the draw. The pool deliberately includes the topics on which the rule then fails; drawing
only from where it succeeds would select on the rule working.

---

## FAILURE STATES THE RULE PRODUCED — 8 of the 20

Recorded as properties of the rule. None repaired by hand.

| state | n | what it means |
|---|---|---|
| `F5_MODALITY_CLASS` | 3 | the stem names a molecular MODALITY, not a therapeutic class: evolocumab → *"monoclonal antibodies: fully human"* |
| `F1_NO_CONDITION` | 2 | the title has no condition connective and cannot be split (`"Evolocumab Ascvd Auto2"`) |
| `F4_NO_CLASS` | 2 | the authority holds no USAN stem at all (selexipag, colchicine) |
| `F6_CIRCULAR_CLASS` | 1 | the class is named after the drug — warfarin → *"warfarin analogs"*; re-keying is a no-op |

Across all 56: also `F2_NO_DRUG` 6, `F3_MULTI_DRUG` 6, `F0_NO_TITLE` 6.

### Three FALSE NEGATIVES of the rule, named

The re-keyed arm's 4/20 is a **floor**. A false-negative probe — frame reviews matching the
condition alone, for every zero-candidate topic — found true counterparts the rule missed:

- **riociguat** → `CD011205 Guanylate cyclase stimulators for pulmonary hypertension` is in the
  frame. ChEMBL writes the class as **"guanaline cyclase activators"** — misspelled in the
  authority's own data, and "activators" where Cochrane says "stimulators". Missed.
- **selexipag** → `CD002994 Prostacyclin for pulmonary hypertension in adults`. Selexipag is a
  prostacyclin receptor agonist; ChEMBL holds no stem for it (`F4`). Missed.
- **enoxaparin** → `CD001100 Fixed dose subcutaneous low molecular weight heparins versus …`.
  The stem is *"heparin derivatives and low molecular weight or depolymerized heparins"*; split
  on `" or "` it fragments into phrases that no longer match. Missed.

⚠️ **My own probe script printed "the typo is not the cause of this particular zero" for
riociguat. That was wrong** — `CD011205` is in the frame and is the counterpart. Corrected here.

---

## THE COUNTER-EVIDENCE, which matters more than the +3

**The hypothesis says intervention identity is what kills the pairs. For most of this sample it
is not the binding constraint, because there is nothing to pair with at any key.**

- **11 of 20 topics produce no candidate in EITHER arm.** Six are rule failures; the other
  **five have a working class key and the frame simply holds no such review** (enoxaparin,
  etripamil, mavacamten, pitavastatin, riociguat).
- **`pitavastatin` is the clean counter-example.** `CD012735 Pitavastatin for lowering lipids`
  names our drug **in its title** — intervention identity is a perfect match — and the pair still
  dies, because our condition is *"hypercholesterolemia"* and theirs is *"lowering lipids"*.
  **A second axis of unit-of-work mismatch, in the CONDITION, that re-keying the intervention
  cannot touch.**

### What the mechanism check does confirm

The keying difference is real and large. Of the 14 distinct drugs in the twenty:

- **11 of 14 are named in NO Cochrane review title** in the whole 1,186-review frame;
- **9 of 14 are named in no review's objectives either.**

`CD004434` and `CD002003` (*Beta-blockers for hypertension*) name **no member drug anywhere** in
title or objectives. So `bosentan` genuinely cannot match *endothelin receptor antagonists for
PAH* — that half of the hypothesis is confirmed outright. What the twenty do not support is the
inference that fixing it recovers pairs at scale.

---

## CONTROLS AND GATES — all passed, or no count would have been printed

**Frame contract precondition checker** (`scripts/rekey20/frame_contract.py`). The base-uniqueness
and `record_kind` / `objectives_verbatim` contract is **the peer lane's, reused not rebuilt**, from
`build_cardio_frame.py`; lifted to the consumer side and extended with the one check the builder
could not make about itself — **a title-keyed frame is REFUSED with its reason**, not warned about.
Plant: **6/6** — five planted defects refused, clean frame passes.

**Scan controls, both directions** — 4/4:

| | control | result |
|---|---|---|
| P1 | *"Atenolol in hypertension"* must return `CD002003` | PASS — class arm 5 verified, `CD002003` present; **drug arm 0** |
| P2 | *"Ambrisentan in pulmonary arterial hypertension"* must return `CD004434` | PASS — class arm 2 verified; **drug arm 0** |
| N1 | *"Ambrisentan in atrial fibrillation"* must be zero | PASS — 0, and its own terms are live (class 9 rows, condition 22 rows) |
| N2 | *"Atenolol in pulmonary arterial hypertension"* must be zero | PASS — 0, terms live (23 / 19) |

The positives assert a **specific `cd_base`**, not a count, so an always-empty instrument fails
them; the negatives assert zero **and** check that each half of the control is live on its own,
so a zero produced by a dead term is refused rather than reported. The controls are **synthetic
topics that do not exist in the corpus**, so fixing a corpus topic cannot retire them.

⭐ **The positive control earned its place: P1 failed on first run** and exposed a real defect —
`class_phrases` glued USAN's exemplar qualifier into the phrase, making `beta-blockers
(propranolol type)` unmatchable against every Cochrane title that uses the class. Fixed uniformly
for all 156 topics, before the scan, recorded in `RULE-AMENDMENT.md`.

**Label-vs-reason gate** (`scripts/rekey20/gate_label_vs_reason.py`). Every judged label is
checked against its own free-text reason and refused on contradiction: quoted spans must be
literally present in **the same text the judgement was made from**; a `COUNTERPART` must quote
both limbs; a `NOT_COUNTERPART` must quote the disqualifying span. Plant: **7/7**. Real run:
**10/10 judgements pass**, coverage exact — 10 verified pairs, 10 judgements, no unjudged pair.

The gate did real work: it is what makes the four refuted pairs checkable. `olmesartan-htn` was
retrieved against two *endothelin* reviews purely on the shared two-word suffix
*"receptor antagonist"* — visible in the output, refuted with the offending span quoted.

---

## ⚠️ ONE SCOPE RULING I WILL NOT DECIDE ALONE

`CD015824 Phosphodiesterase type 5 inhibitor plus endothelin receptor antagonist compared to
either alone` was verified against `bosentan-pah`. Bosentan is a member of the intervention and
the condition matches, so **the authored rule returns COUNTERPART** — but the review's comparison
is combination-versus-monotherapy, while `bosentan-pah`'s title states no comparator at all.

I judged it `UNDECIDABLE_BY_RULE` rather than deciding it. **Does a counterpart have to match on
the comparator, or only on intervention and condition?** The same review was decidable for its
two siblings and I judged those: `NOT_COUNTERPART` for `bosentan-pah-children` (the review says
*"adults and adolescents"*) and for `bosentan-pah-monotherapy` (its comparator is an inactive
control, the review's is active monotherapy). Only the untyped parent topic is genuinely
undecidable.

---

## Denominator note, quoted both ways as instructed

The 724's coverage against this frame is **724 / 1,216 = 59.5%** of live cardiology CD **bases**
and **724 / 1,186 = 61.0%** of cardiology **reviews**. Neither alone is correct: the 724's own
composition was never recorded, so which population it counts is unknown. 30 of the 1,216 are
**protocols** and were excluded from every scan — a protocol has no results and cannot be a
counterpart.
