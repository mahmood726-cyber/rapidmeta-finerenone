# The night the instruments were wrong

**2026-08-18.** Eight commits, all instrument. **Zero topics rebuilt.**

The ask was 134 topics rebuilt to the flagship spec. None were. This document says what
was found instead, and why finding it was worth more than the rebuild would have been.

---

## 1. Four recorded limitations were tested against live data. Four were accurate.

This is the load-bearing result and it is easy to lose among the corrections, so it goes
first.

The corpus publishes a **verdict** rather than an estimate on roughly 85 of its topics.
Every reassurance about that has, until tonight, been of one kind: *we refuse honestly.*
Nobody had tested whether the refusals were **right**.

| Object | What it claimed | What the registry said |
|---|---|---|
| `men-acwy-auto-full-review` | *"WE NEVER LOOKED. NOT 'no trial exists'"* — named NCT01000311 among others | **57** completed Phase 3/4 trials exist; NCT01000311 real and correctly described |
| `caspofungin-fungal-auto-full-review` | same claim — named NCT00520234 | **16** trials exist; NCT00520234 is the Mycoses Study Group prophylaxis trial, n=222, Phase 4 |
| `apixaban-vte` | *"NOT POOLABLE AS POSED — the COMPARATOR and PARTICIPANTS and OUTCOME limb fails"* | NCT02829957 is apixaban **vs rivaroxaban** (comparator), in **menstruating women** (participants), measuring **menstrual blood loss** (outcome), n=19. **All three limbs confirmed** |
| `attr-cm-review` | *"the two hierarchies are not the same hierarchy"* | ATTR-ACT: mortality + CV hospitalisation. ATTRibute-CM: **+ NT-proBNP + 6MWT**. Confirmed independently by an assessor that had never read the object's prose |

**`apixaban-vte` is the strongest.** It did not say "we don't know." It named three specific
limbs and said why each failed. A verdict that specific is falsifiable, and it survived
falsification against a registry it was not written from.

**`attr-cm-review` is the second strongest**, for a different reason: a check and a human
reached the same conclusion by different routes. That is the strongest confirmation
available to us.

---

## 2. The unifying finding: five distinct defects, one direction

Five mechanically distinct failures were found in one night, in five different layers:

| Layer | The defect | The substitution |
|---|---|---|
| Taxonomy | A classification scheme with no name for the healthy case | working → anomaly |
| Sweep script | State assigned from a tab NAME without reading the object | unread → decided |
| Assessor | `arms: []` scored FAIL | no data → wrong data |
| Helper | A raising predicate swallowed as NOT_ASSESSABLE | broken instrument → no reading |
| Classifier | Drug not found in arm labels scored `not_eligible` | **unclassifiable → excluded** |
| Estimand | Near-match reported as FAIL | undecidable → different |
| Query | Condition-only search returning a therapeutic area | malformed input → valid result |

**Every one runs the same direction: it makes the corpus look more decided than it is.**

That is not coincidence. **The failure that hides is the failure that survives, because
nothing in a system is built to notice silence.** A wrong claim eventually meets a reader
who knows better. A hidden finding meets nobody. So over time a codebase accumulates the
errors that are quiet, and its apparent confidence rises while its actual knowledge does
not.

A corollary, found live: an incomplete category list makes a real difference **invisible**
while publishing nothing false. Safe direction — and exactly how a finding disappears.

---

## 3. Documentation failed as a control, under ideal conditions

`ssot/assessment.py` put the three-state rule in **one function** so it could not be
re-derived incorrectly. It was imported. It was used. **The same author then reproduced the
same defect class four more times in a single script within hours.**

- `subject_role` written as a byte-identical copy of `inclusion_criteria_auditable` — one
  check, two names — committed *hours after* a commit whose entire subject was one **name**
  carrying two **checks**.
- `estimand` and `comparator` comparing free-text display strings.
- `contract` asserting a type on a field that is polymorphic across the corpus.

These are the most favourable conditions documentation will ever get: one page, freshly
written, by its own author, minutes earlier. **It did not work.**

What worked was **mechanical rejection**. Five detectors now refuse registration, so a
defective assessor cannot run and therefore cannot emit a number:

1. **Duplicate path** — two assessors over one path set
2. **Text equality** — normalisation + comparison without `text_match`
3. **Type declaration** — polymorphic field → NOT_ASSESSABLE, never FAIL
4. **Identical tally** — two assessors byte-identical across all objects
5. **Unit of analysis** — declared unit must be the unit actually iterated

Detector 2 **failed its own test on the first attempt, in the exact shape of the bug it
targets** — it inspected each AST node's local segment while claiming to check the
function. That is the same error as certifying a per-tab migration with a grand-total
check: *the check ran correctly on the wrong unit*. It became detector 5.

---

## 4. The correction that justifies the whole night

The batch-1 arm-role counts were reported, relayed onward, and were **wrong**.

| | Reported | Corrected | Δ |
|---|---:|---:|---:|
| Experimental-class trials across ten topics | 232 | **287** | **+55 (24%)** |
| Trials newly NOT_ASSESSABLE | 0 | **23** | — |

`ablation-af-review` alone went **57 → 99**. A drug-name matcher reading ablation trials —
where arms are labelled by *technique* (`WACA and PVI`, `PVAC`, `CFAE ablation`) — missed
nearly half. **That is not a tuning problem. It is a category error: the check asked a
question the data does not answer in that field.**

`NCT02789917` (`APixaban vs. PhenpRocoumon`) labels its arms *Dual therapy (incl. NOAC)* and
*Triple therapy (incl. VKA)*. The drug name appears only in the title. It was scored
`not_eligible` and **vanished silently** from the reconciliation queue.

**This is why zero topics were rebuilt.** Every instrument needed for the rebuild was wrong
when the night started: four of eight assessors, the classifier, the census, the build
queue, the fetch cache, and the helper written to prevent the whole class. **Rebuilding 134
topics with those would have propagated a 24% undercount into the corpus instead of into a
retraction.**

---

## 5. What was measured, honestly

- **Eight-tab matrix**, 135 objects × 8 tabs = 1080 cells, per-cell evidence. `arni-hfref`
  is the only object holding Search / Paper Studio / Statistics content — not 134 broken
  pages, one flagship and a corpus built to a narrower spec.
- **"101 of 116 pages display three of eight tabs"** — re-measured without the two blind
  spots. **The claim stands, delta 0.**
- **Ten cardiology topics searched** against live ClinicalTrials.gov. `inclusion_criteria_
  auditable`: **FAIL 6 (declared absent) / NOT-ASSESSABLE 4 (silent) / PASS 0.** No object
  in the batch can state who was eligible; six say so, four say nothing.
- **Estimand retraction**: 7 FAILs → **4 DIFFERENT** (each naming its discriminator) +
  **4 UNDECIDABLE**. Four of the original seven were unearned.
- **Published-meta comparison**: 1,174 syntheses located; **36 opened, 31 full texts,
  1,121 rows checked, 2 resolved to a registration ID.** Reference lists cite publications,
  not registrations — ID-keyed reconciliation needs a two-hop citation → PMID →
  registration resolution. **Not done, and scoped as the next unit.**

**The drug-name-matcher hypothesis on published metas is UNTESTED, not confirmed.** Zero
resolved IDs means their k could not be read, not that it is small. Recording it as support
would have been the same substitution this document is about, in the direction that
flatters us.

---

## 6. Cross-family review earned its place

Two real defects in the shared helper were found by a **different model family** (Gemini
3.1 Pro), not by same-family review:

- A raising predicate swallowed as NOT_ASSESSABLE, so an **assessor typo** reported
  "cannot assess" instead of failing loudly. *The module written to stop
  absence-scored-as-negative was scoring its own bugs as absence.*
- `{"role": ""}` counted as a non-matching value rather than an unreadable field.

Its one-line statement of the class is better than ours and is adopted: **they conflate a
data representation artifact with a definitive clinical failure.**

One disagreement was left standing rather than settled — it turned out both answers were
right for **different questions**, which is what forced the `inclusion_criteria_auditable`
/ `eligibility_met` split.

---

## 7. Ledger lines

- An instrument's inability to **start** must be distinguishable from a negative reading.
  A `codex exec` hung on open stdin returns nothing, and nothing reads as failure.
- A preflight is only evidence about **the environment it ran in**.
- A cross-run check must compare at the **finest granularity the runs disagree on**, not
  the coarsest they agree on.
- A classification scheme with no name for the **working** case routes healthy cases into
  its anomaly bucket.
- **Detector-before-defect happened once tonight** — a factorial-design question was put to
  another family, and AUGUSTUS arrived in live data *before the answer came back*. Every
  prior instance this week ran detector-after-defect.
- **Cost**: ~717k Codex tokens against a Claude side that read no corpus files. The
  expensive part of this work is reading the repo, and reading the repo is exactly the part
  that can move to the seat whose quota is not binding. Claude's irreducible share is
  deciding what to ask, noticing which step was asserted rather than proven, and refusing
  to act on the assertion.

---

## 8. Next unit

The two-hop citation → PMID → registration resolution, which makes the published-meta
comparison possible. Then batch 1's rebuild, on instruments that now reject rather than
remind.
