# The corpus-wide size of the enumeration failure

**Date:** 2026-09-02 · **MEASURED** — `python aact_sweep2.py` (no args = all topics)
**Snapshot:** `F:\AACT-storage\AACT\2026-08-30` — **DATA DATE 2026-08-27**. Never blended
with `2026-04-12` (data date 2026-04-08). **No phase filter.**
**Sweep ownership:** agreed with the AACT lane before either started — one sweep, not two.

---

## The number that sizes the project

| | |
|---|---|
| topics scored | **135** |
| topics skipped **and named** (not scored zero) | **20** |
| **total trials ingested across all 135 topics** | **398** |
| **never screened — ceiling (OR over MeSH terms)** | **14,857** |
| **never screened — floor (AND over MeSH terms)** | **5,828** |
| **completed phase-3 never screened** | **3,112** |
| topics ingesting ≤ 5 trials | **125 of 135** |
| topics with zero never-screened | **2** |
| largest ingested k | 26 (`colchicine-periprocedural`) |

**Even at the floor, 5,828 randomised trials sit in a snapshot on local disk that no topic
ever screened — against a corpus that ingested 398.**

### Why a BRACKET and not a number

OR across a topic's MeSH terms is the **ceiling**; AND-of-all-terms is the **floor**. Topics
whose population is an **intersection** (`iv-iron-hf` = iron deficiency **AND** heart failure)
are over-counted by OR and under-counted by AND, and the registry does not encode which the
topic wants. `rivaroxaban-vasc-review` reads **442 vs 0** — that spread is the honest
uncertainty. **Quoting either end alone would be false precision.**

## Top of the ranked table

```
topic                          avail  ingst  NEVER-hi  NEVER-lo   cP3   condref
raltegravir-hiv                  871      3       870       716   164      2038
acs-antiplatelet-review          577      4       574        30    66      1057
rivaroxaban-vasc-review          446      4       442         0    43      1111
colchicine-stroke-prevention     441      9       432       181    64      4021
influenza-recombinant            421      2       419       321    95       295
dabigatran-vte-treatment         417      5       412        38    96       990
cangrelor-pci-review             362      3       359         1    43       331
dabigatran-vte-cerebral          351      5       346         6    78       710
iv-iron-hf                       321      5       316        15    39       407
enoxaparin-vte                   296      3       293       133    64       555
```

---

## The known-answer control, adopted from the AACT lane

**`V-INCEPTION` (NCT04873934) must be retrieved. `ORION-8` (NCT03814187) must be REFUSED.**

**MEASURED: V-INCEPTION retrieved = True · ORION-8 wrongly included = False → PASS.**

ORION-8's refusal is reported with its registry reason: `allocation=NA`,
`intervention_model=SINGLE_GROUP`, `n=3275` — a non-randomised long-term extension.
**Refusing it is correct, and both halves must be published together**: an unfiltered hand-off
would have put a single-arm extension into a pool of randomised effects. **The fix is a
FILTERED adapter, not a faster pipe.**

## Three defects the control forced out, before it would pass

1. **Whole registered strings → the RAREST TOKEN per name.** Taking the whole string meant
   `dapivirine vaginal ring` never matched a trial registering `Dapivirine`; the AACT lane hit
   the same on `inclisiran sodium` vs `Inclisiran`. **Frequency alone could not fix it** —
   `placebos` (df 577) is *rarer* than `iron` (df 628). The rule that works is the rarest
   token *within each name*: "Dapivirine Vaginal Ring" → `dapivirine`; "AMR101 1 g per day" →
   `amr101`.
2. **`placebos` escaped the stoplist** — `^placebo\b` cannot match the plural, so a placebo
   arm was scored as a drug identity.
3. **The synonymy ceiling is bridgeable — by the registry's own vocabulary.** Derivation
   cannot bridge `Acute Coronary Syndrome` → `ASCVD`; **AACT's `browse_conditions.txt` MeSH
   mapping can.** V-INCEPTION carries `hypercholesterolemia`, `dyslipidemias`,
   `atherosclerosis` under MeSH. **Blind spot on the seven-topic set fell 4,383 → 259 (94%).**

### ⛔ MeSH MUST BE MATCHED WHOLE, NEVER TOKENISED

My first MeSH attempt tokenised the terms, producing `diseases` as a match token. **A breast
neoplasms trial then qualified for a heart-failure topic, and only 15% of hits carried any
heart-failure term.** Tokenising a controlled vocabulary destroys the normalisation that is
the entire reason to use it. Whole-term set intersection only, with broad ancestors dropped by
document frequency (`cardiovascular diseases` sits on 63,922 trials and names no population;
`heart failure` on 5,790 and does).

**Every matched drug token and MeSH term is printed per topic**, so the expression can be
audited by eye rather than trusted.

---

## Two ceilings I could NOT close, both measured rather than declared

**1. Drug vocabulary inherits our own trials' choices.** `icosapent-lipid` derives only
`amr101` — the brand code its own trials registered — so this sweep reports **3 available
where the AACT lane's independent count found 19**. Derivation from a topic's own trials
cannot reach names those trials never used. **Their 19 is the better number; my 3 is the
evidence for the ceiling.**

**2. Synonymy blind spot across the corpus: 46,251 drug-matched, condition-refused.** That is
larger than the finding itself, so **the true never-screened count is ABOVE my ceiling, not
between the bounds.** The bracket brackets the measurement, not the truth.

---

## What this does to the published claim

We say *"every screened record carries a named decision"*. Across 135 topics that decision
record covers **398 trials** against **at least 5,828** sitting unscreened on local disk.

**A perfect audit trail over a pool somebody typed.**

Verbatim, and it is what makes the claim unarguable:

> I am NOT claiming those trials belong — many will be small mechanistic RCTs a review would
> rightly exclude. Their eligibility is unknown because they were never screened, and that is
> the finding rather than a hedge on it.
