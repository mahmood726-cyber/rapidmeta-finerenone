# `colchicine-cvd-review` — the P21 decision, taken on a COMPLETE surfaced set

**Date: 2026-08-19. Surfaced set: the 137 registrations named in
`evidence/2026-08-19-batch1/colchicine_surfaced_137.json`.**

This document is written **before any record is screened and before any count is computed**,
so that the readings and their anchors cannot be chosen to suit the numbers. Counts appear in
`evidence/2026-08-19-batch1/colchicine_split_screening.json`, produced by
`scripts/screen_colchicine_split_2026_08_19.py`, and nowhere in this file.

---

## Why a decision is owed at all

The page as it stands asks:

> *Does low-dose colchicine reduce major cardiovascular events?*

and holds three trials: **COLCOT** (after myocardial infarction), **CLEAR SYNERGY / OASIS-9**
(after myocardial infarction, inside a 2×2 factorial with spironolactone) and **CONVINCE**
(after **non-cardioembolic ischaemic stroke**). Its own `results.by_outcome.primary` already
records that these do not share an endpoint — CONVINCE's registered primary counts *recurrent
non-fatal ischaemic stroke and nothing else*, which cannot be averaged with a five-component
cardiovascular composite.

That was diagnosed as an **estimand** failure. It is also, and separately, a **question**
failure: the three trials are of three populations whose index vascular event differs, and the
complete search shows the surfaced literature separates into further populations again. One
review cannot be the review of all of them, and **choosing one is a decision to withhold
evidence from every reading that loses, leaving no trace in any object** (P21).

**Splitting is a build. Merging is Mahmood's decision and is not taken here.** If two of the
readings below should be one review, that is recoverable; a reading never built is not.

---

## The readings, each anchored to a registration in the surfaced set

Six readings. Each names an anchor **quoted from the 137**, and each anchor is asserted as a
known member of its reading **before** the partition runs (P43).

| id | reading | the question it asks | anchor(s) from the surfaced set |
|---|---|---|---|
| **CORONARY** | established coronary disease / after myocardial infarction | does colchicine reduce major adverse cardiovascular events in patients with coronary disease? | **COLCOT** `NCT02551094` n=4,745 · **CLEAR SYNERGY** `NCT03048825` n=7,264 |
| **CEREBRO** | after ischaemic stroke or TIA | does colchicine reduce recurrent vascular events after an ischaemic cerebrovascular event? | **CONVINCE** `NCT02898610` n=3,154 · **CHANCE-3** `NCT05439356` n=8,343 |
| **PAD** | peripheral artery disease / limb ischaemia | does colchicine reduce vascular and limb events in peripheral artery disease? | **LEADER-PAD** `NCT04774159` n=6,150 |
| **ICH** | after spontaneous intracerebral haemorrhage | does colchicine reduce cardiovascular events after a **haemorrhagic** index event? | `NCT06587737` n=1,125 · `NCT05159219` n=100 |
| **PERIPROC** | prevention of a complication of an operation or catheter procedure | does colchicine prevent post-operative / post-procedural cardiac complications? | **COP-AF** `NCT03310125` n=3,209 · **COPPS-2** `NCT01552187` n=360 |
| **PERICARD** | pericarditis as a disease in its own right | does colchicine prevent recurrence of pericarditis? | **ICAP** `NCT00128453` · **CORP** `NCT00128414` · **CORP-2** `NCT00235079` |

### Why ICH is a reading of *this* question and not an adjacent one

Its largest registration, `NCT06587737`, is titled *"…for Reducing Dependency and
**Cardiovascular Events** with Oral Colchicine 0.5 mg Once Daily … in Participants with
Spontaneous Intracerebral Hemorrhage **and Established, or Risk Factors for, Atherosclerosis**"*.
That is the MACE-reduction question asked of an atherosclerosis population whose index event
was haemorrhagic. It is ambiguous with the page's question in exactly the way P21 governs.

### Why PERIPROC and PERICARD are built even though they are the furthest out

They ask about a different outcome family, and a reviewer could argue they are not readings of
"major cardiovascular events" at all. **They are built anyway**, because the failure this
project is built against is the silent one: an unbuilt reading leaves no trace, and the
alternative to building them is a judgement of mine that the user has explicitly reserved.
Each of their pages will state on its face that its outcome family is **not** MACE.

---

## Precedence — stated, because the readings are not mutually exclusive by construction

A trial can be post-MI **and** peri-procedural; a cardiac-surgery trial can register both
post-pericardiotomy syndrome **and** post-operative atrial fibrillation. An assignment rule is
therefore required, and it is applied in this order, each step naming the field it reads:

1. **PERIPROC** — `outcomesModule` — the registered primary is a **complication of an operation
   or catheter procedure**: post-operative atrial fibrillation, post-pericardiotomy syndrome,
   peri-procedural myocardial injury, in-stent restenosis, graft failure, post-ablation
   arrhythmia recurrence.
2. **PERICARD** — `conditionsModule` — pericarditis or pericardial effusion as the condition
   **treated**, not prevented after an operation.
3. **ICH** — `conditionsModule` — intracerebral / intracranial haemorrhage.
4. **CEREBRO** — `conditionsModule` — ischaemic stroke, TIA, cerebral infarction, intracranial
   atherosclerotic disease.
5. **PAD** — `conditionsModule` — peripheral arterial disease, limb ischaemia, extremity
   atherosclerosis.
6. **CORONARY** — `conditionsModule` — coronary artery disease, myocardial infarction, acute
   coronary syndrome, angina.

Anything reaching none of the six is **not one of these reviews** and is dispositioned in the
screen with the criterion it failed named. It is not silently dropped.

> **PERIPROC is deliberately placed FIRST and it is the most dangerous position in this list.**
> A rule that partitions before it judges removes trials from every downstream reading before
> any of them can judge them, and each reading then looks internally consistent (P43). The step
> is therefore defined by **what the primary outcome is**, never by *a procedure having
> occurred* — because CLEAR SYNERGY randomises patients with myocardial infarction who are
> undergoing PCI, and a "was a procedure involved?" rule would take **the largest trial in the
> review's own included set** out of the coronary reading and put it in a post-procedural one.

---

## Known members asserted in advance (P43)

The partition is refused if any of these lands anywhere other than where it is named here.
These are the assertions, not a description of the output:

| registration | must be assigned to | why, in one line |
|---|---|---|
| `NCT02551094` COLCOT | **CORONARY** | randomised within 30 days of myocardial infarction; primary is a five-component CV composite |
| `NCT03048825` CLEAR SYNERGY | **CORONARY** | myocardial infarction population; primary is CV death / MI / stroke / revascularisation, **not** a procedural complication |
| `NCT02898610` CONVINCE | **CEREBRO** | non-cardioembolic ischaemic stroke |
| `NCT05439356` CHANCE-3 | **CEREBRO** | minor-to-moderate ischaemic stroke or TIA |
| `NCT04774159` LEADER-PAD | **PAD** | peripheral arterial disease |
| `NCT06587737` | **ICH** | spontaneous intracerebral haemorrhage |
| `NCT03310125` COP-AF | **PERIPROC** | primary is perioperative atrial fibrillation after thoracic surgery |
| `NCT01552187` COPPS-2 | **PERIPROC** | primary is post-pericardiotomy syndrome after cardiac surgery |
| `NCT00128453` ICAP | **PERICARD** | acute pericarditis, treated |
| `NCT00235079` CORP-2 | **PERICARD** | recurrent pericarditis, treated |

---

## The empty-question test, set BEFORE the counts exist

> **A reading with no eligible trial is not a review. It is an EMPTY QUESTION**, and the honest
> outcome is to name it as a **boundary** on the other readings' pages rather than to publish a
> page with nothing on it.
>
> **A reading with eligible trials and no posted results IS a review**, and it publishes a
> refusal naming every trial — `bosentan-pah-not-group-1` did exactly that with eight eligible
> and zero reported, and that page is a finding about a literature.

This test is written down now so that it cannot be adjusted after the counts are seen. On
`bosentan-pah` the same test **did not fire** and all four readings were built; whether it
fires here is not known at the time of writing.

---

## AMENDMENT, after the screen first ran — a seventh reading

**Dated and separated on purpose.** Everything above was written before a count existed, which
is the only thing that makes the six readings credible. This section was written *after*, and
declaring that is the point: **the fix for having to amend a pre-registered decision is to
label the amendment, not to edit the original into agreement with the numbers.**

The screen surfaced a population none of the six covers: trials enrolling **established
atherosclerotic cardiovascular disease with no vascular bed specified**.

| id | reading | anchor(s) | where it went under the original six |
|---|---|---|---|
| **ASCVD_MIXED** | established atherosclerotic disease, no bed named | **EPOCA** `NCT06930885` n=7,713 — conditions are literally *Atherothrombotic Diseases* and *Atherosclerotic Cardiovascular Disease (ASCVD)* · **COLPET** `NCT02162303` — conditions are *Atherosclerotic Vascular Disease* | EPOCA → **CORONARY**, the wrong review. COLPET → **NONE**, no review at all. |

It is applied **last**, after every bed-specific reading has had its turn, so it can only
receive a trial that names atherosclerosis and names no bed. A **negative** known member —
CONCISE `NCT06062277`, conditions `['Ischemic Stroke','Atherosclerosis']` — is asserted to land
in **CEREBRO**, because an assertion that only checks where trials *should* go cannot detect a
fallback reading that has quietly become a magnet.

### And the CORONARY reading was narrowed in the same pass

`atherosclerosis`, `cardiovascular disease`, `atherothrombotic` and `clonal hematopoiesis` were
removed from its term set. **Nine records had reached the coronary reading on one of those
alone** — among them an **aortic stenosis** trial, a **rheumatoid arthritis** trial, a **type 1
diabetes** trial and a **CKD** trial, each declaring a perfectly true `Cardiovascular Diseases`
code. P42 twice over: the code is correct, and it is not an answer to *which artery*.

---

## The boundary of this topic, stated — what is a reading and what is a different question

The search's condition filter reaches far beyond this review, and the complete set contains
colchicine trials across at least a dozen distinguishable questions. **P21 governs readings of
*this page's question*. It does not require building every question colchicine has been asked.**
The line is drawn here and applied uniformly:

> A **reading** is a randomised comparison of colchicine against an inactive or usual-care
> control in a population defined by **established atherosclerotic vascular disease or an index
> vascular event**, for **major vascular events** — plus the two adjacent outcome families
> (PERIPROC, PERICARD) that the surfaced set makes unavoidable and that are built rather than
> judged away.

Everything else is a **different question**. It is **EXCLUDED with its population named and
recorded as a candidate future topic**, so that it leaves a trace in a file rather than
disappearing: heart failure, atrial fibrillation as a disease, aortic stenosis, abdominal aortic
aneurysm, venous thromboembolism, chronic kidney disease, HIV, diabetes without established
vascular disease, Behçet's disease, IgA and cutaneous vasculitis, gout, myocarditis and
inflammatory cardiomyopathy, multiple myeloma, COVID-19, hypertension, and congenital
single-ventricle disease.

**That list is a judgement and it is written down so it can be overturned.** If any of those is
a reading of this question, it is one line of evidence away from being built.

---

## What is NOT decided here

- **Whether any two of these six should be one review.** That is a merge, and a merge is
  Mahmood's decision (`evidence/2026-08-19-batch1/corpus_duplication.json` measures the cost of
  the corpus's existing unrecorded duplication; it does not authorise anyone to create or
  resolve one).
- **What happens to the parent object `colchicine-cvd-review`.** Retiring it is a deletion and
  is not taken unilaterally. Its trials are shared with the readings that receive them and that
  sharing is recorded on both sides under **P22**.
- **The published card `HR 0.75 (0.61–0.91)` at k=2.** It is already withdrawn on the parent
  object with its reason. Closing it is a separate unit of work and is not folded into this
  decision.
