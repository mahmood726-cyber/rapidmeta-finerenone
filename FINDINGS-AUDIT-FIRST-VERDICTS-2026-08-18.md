# The six candidates, read by hand on every limb — **one survives**

Standalone file: `STATUS.md` and `TOOLING-QUEUE.md` are held by another writer in this
tree.

The triage tested the **outcome** limb only and said so. All six candidates have now
been read against their registrations on **intervention, comparator and participants**
— MECIR Box 10.10.a C62 requires all four limbs, and Handbook 6.5 §10.10.3 names
*"participants, interventions and outcomes"* explicitly.

**All six pass the intervention limb except OLMESARTAN_HTN. Four then fail on
participants or comparator. One survives every limb.**

---

## SURVIVES — `PITAVASTATIN`, k=2

| registration | experimental arm | active comparator | registered primary |
|---|---|---|---|
| `NCT00309738` | Pitavastatin 4 mg QD | Simvastatin 40 mg QD | *Percent Change From Baseline in LDL-C* |
| `NCT00309777` | Pitavastatin 2 mg / 4 mg | Simvastatin 20 mg / 40 mg | *Percent Change From Baseline in LDL-C at 12 Weeks* |

Same intervention, same active comparator, same population, same registered primary on
the same scale. **This is a defensible k=2 pool and it is the only one of the six that
is.**

---

## RETIRE — `OLMESARTAN_HTN`: the titled drug is the comparator in all three trials

| registration | what it actually tests | olmesartan's role |
|---|---|---|
| `NCT00846365` | Azilsartan medoxomil + chlorthalidone | **ACTIVE_COMPARATOR** |
| `NCT01033071` | Azilsartan medoxomil + chlorthalidone | **ACTIVE_COMPARATOR** |
| `NCT01599104` | LCZ696 (sacubitril/valsartan) | **ACTIVE_COMPARATOR** |

**There is no honest version of this page.** It is an artefact of a drug-name search
over trial records: two azilsartan trials and one LCZ696 trial, selected because
olmesartan appears in them. **No poolable result is possible for the question the title
asks**, and the topic is retired on that ground — a finished topic under the rule that a
review need not contain a meta-analysis (§10.10.3).

---

## NOT POOLABLE AS POSED — three fail on participants or comparator

### `RIOCIGUAT_PAH` — two different diseases

| registration | population | comparator | primary |
|---|---|---|---|
| `NCT00810693` | **pulmonary arterial hypertension** | placebo | 6MWD change to **week 12** |
| `NCT00855465` | **CTEPH** (chronic thromboembolic pulmonary hypertension) | placebo | 6MWD change to **week 16** |

Intervention and comparator match; **the participants do not**. CTEPH is a different
disease from PAH, and the topic is titled for PAH. The endpoints also sit at different
timepoints. **For the PAH question this is k=1.**

### `EDOXABAN_VTE` — prevention against treatment, adults against children

| registration | question | population | comparator |
|---|---|---|---|
| `NCT01181102` | **prophylaxis** after total knee/hip replacement | adults, post-surgical | **enoxaparin** |
| `NCT02798471` | **treatment** of confirmed VTE (Hokusai paediatric) | **children** | **standard of care** |

Three limbs differ at once. **Averaging a prophylaxis trial with a treatment trial is
not a pool of one question**, and the comparators are not the same agent.

### `MIPOMERSEN_HOFH` — one uncontrolled extension, two different populations

| registration | design | comparator |
|---|---|---|
| `NCT00477594` | **open-label extension**, both arms mipomersen (200 mg weekly vs alternate-week) | **none — no control arm** |
| `NCT00607373` | randomised, **homozygous** familial hypercholesterolaemia | placebo |
| `NCT00707746` | randomised, **high-risk statin-intolerant** | placebo |

`NCT00477594` has **no control arm at all** — it is a within-drug dose comparison in an
open-label extension and cannot contribute a controlled contrast. That leaves two
placebo-controlled trials in **different populations**: the topic is titled HoFH and
only `NCT00607373` is HoFH. **For the HoFH question this is k=1.**

---

## The count, stated plainly

| | |
|---|---|
| triage said POOL POSSIBLE | 6 |
| fails the intervention limb | 1 (OLMESARTAN_HTN — retire) |
| fails participants or comparator | 3 (RIOCIGUAT_PAH, EDOXABAN_VTE, MIPOMERSEN_HOFH) |
| fails comparator, but a coherent subset survives | 1 (AZILSARTAN_HTN → k=2, renamed) |
| **survives every limb as posed** | **1 (PITAVASTATIN, k=2)** |

**Every one of these findings removes a pool rather than creating one.** That is the
conservative direction and it is worth stating: nothing here makes a result more
significant, and four pages that would have averaged different drugs, different
diseases, or a prophylaxis trial with a treatment trial will not now do so.

**And the outcome limb alone would have passed all six.** The triage was right to say it
tested one limb; reading the other three changed the answer for five of the six.
