# DECIDED — `bosentan-pah` becomes FOUR reviews

Supersedes the recommendation in `BLOCKED-bosentan-pah-2026-08-19.md`, which named four
readings and **refused to quote a count for any of them** because `topic_identity.locate()` had
not been run over the surfaced set. It has now. **Unknown was not zero, and the counts are what
decided this.**

Computed by `scripts/screen_bosentan_split_2026_08_19.py` →
`evidence/2026-08-19-batch1/bosentan_split_screening.json`.

## The counts

Arm-role cascade over the 57 surfaced records:
**experimental 35 · comparator 4 · background 8 · not-assessable 10**.

| reading | records | **eligible** | of those, with posted results |
|---|---:|---:|---:|
| **A** bosentan monotherapy vs an inactive control, WHO group 1 | 14 | **4** | 2 |
| **B** bosentan as part of combination therapy | 20 | **8** | 1 |
| **C** pulmonary hypertension that is **not** WHO group 1 | 17 | **8** | **0** |
| **D** children | 6 | **3** | 3 |

**No reading is empty, so all four are reviews.** The test was set in advance: a reading with no
eligible trial is not a review but an *empty question*, to be named as a boundary on the others'
pages rather than built as a page with nothing on it. That case did not arise.

**Reading C will publish a refusal, and that is a result.** Eight eligible trials and **not one
posted result** — sarcoidosis, interstitial lung disease, diastolic heart failure, sickle cell,
idiopathic pulmonary fibrosis. Under the remainder reading in `PAGE-STANDARD.md` that is *the
field is still in flight*, not a criticism of the query, and the page will say so with the eight
named.

## Precedence, stated rather than discovered

The readings are **not mutually exclusive by construction** — a trial can be paediatric and
group-1 and a combination design at once — so an assignment rule is required and is applied in
this order, each step naming the field it reads:

```
D  CHILDREN         eligibilityModule   -- stdAges with no adult stratum, or maximumAge < 18
C  NOT GROUP 1      conditionsModule    -- and the TITLE where the coded field names only the
                                           syndrome
B  COMBINATION      armsInterventionsModule -- and the TITLE/briefSummary where the background
                                           drug is not a registered intervention
A  MONOTHERAPY      everything else placing bosentan in the randomised contrast
```

**A different precedence would move trials between readings and these counts would change with
it.** That is written down because it is a choice, not a discovery.

## Three errors the counts caught before anything was built

Each produced a complete, plausible assignment table, and each was found by a known answer.

**1. `minimumAge < 18` is not "a paediatric trial".** EARLY (NCT00091715) and COMPASS-2
(NCT00303459) are adult PAH trials that *admit adolescents* — `minimumAge: 12 Years`,
`stdAges: [CHILD, ADULT, OLDER_ADULT]`. The first rule assigned both to reading D, **taking
reading A's anchor trial and the object's own reading-B trial out of their reviews entirely**.
A precedence rule applied *first* is the most damaging place to be wrong: everything downstream
inherits it silently. Corrected to *no adult stratum at all, or `maximumAge < 18`*.

**2. An add-on design can be invisible in the arms.** COMPASS-2 declares exactly what EARLY
declares — `armGroups: bosentan | placebo`, `interventions: ['bosentan','placebo']` — because
its sildenafil is **background therapy, and background therapy is not a registered
intervention**. Read from the arms alone the two are indistinguishable, and COMPASS-2 was
assigned to *monotherapy*, the one reading it specifically is not. The design is declared in the
official title; the limb now falls back to text and **records that it did**.

**3. The coded condition names the syndrome and the title names the cause.** ASSET-1 and ASSET-2
(NCT00310830, NCT00313196) declare `conditions: ["Pulmonary Hypertension"]` and are titled
*"...in Sickle Cell Disease (SCD) Patients"*. The coded field is **true and uninformative**, and
reading it alone put two sickle-cell trials into the WHO-group-1 monotherapy reading.

> **Third instance of that shape in one day**, after `azilsartan`'s `conditions: ["Safety"]`.
> A coded field can be correct and still not answer the question being asked of it.

**And a fourth, on eligibility rather than assignment.** The first eligibility limb tested arm
role and allocation and nothing else, admitting NCT01864863 — a **bioequivalence study of two
bosentan tablet formulations in healthy male volunteers** — to reading A's eligible set.
Randomised, bosentan in the contrast, and not a trial of bosentan's effect on pulmonary
hypertension in anybody.

## What is still NOT settled, and is recorded rather than described

- **Some assignments remain arguable and are not yet adjudicated.** `NCT04273945` (macitentan
  75 mg vs 10 mg) sits in B and bosentan is not what it randomises; `NCT01824290` (tadalafil in
  children) sits in D on the same grounds. Both were admitted by `locate()` finding bosentan in
  the contrast as permitted background. **They are flagged here and not silently kept or
  silently dropped.**
- **No estimand screen has been run for any reading.** Which trials *pool* is a separate
  question from which are *eligible*, and none of the four readings has had the withholding
  question asked at every rank yet.
- **No PubMed search has been run for this topic.**

## Next concrete steps

1. Adjudicate the flagged assignments above.
2. Per reading: withholding question at every rank, estimand screen, cascade, criteria.
3. Build four objects — sharing **no block** with each other; four sibling topics built in one
   session is precisely the shape that produced the cross-topic contamination class.
4. Build, verify against the public host, push per reading.
