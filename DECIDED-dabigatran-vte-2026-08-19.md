# `dabigatran-vte-review` — the P21 decision, on a screened set

**Date: 2026-08-19.** Search reconciled (38 == 38); 38 records screened to zero; the four
readings and their anchors were fixed in `screen_dabigatran_vte_2026_08_19.py` **before** the
counts were read, and the partition refuses to write if any declared member lands elsewhere.

---

## Why a decision is owed

The object holds four trials and has already withdrawn its estimate, recording that their
registered primaries "are not even the same kind of quantity". The screen sharpens that from an
estimand problem into a **question** problem: the surfaced literature separates by **what the
drug is being given for**, and that axis decides which events are countable at all.

## The four readings — all non-empty, so all four are reviews

| reading | records | eligible | with posted results | anchors |
|---|---:|---:|---:|---|
| **TREATMENT** — acute symptomatic VTE | 8 | 5 | **3** | RE-COVER `NCT00291330` (n=2,564), RE-COVER II `NCT00680186` (n=2,589) |
| **EXTENDED** — secondary prevention after a completed course | 4 | 2 | **2** | RE-MEDY `NCT00329238` (n=2,867), RE-SONATE `NCT00558259` (n=1,353) |
| **SURGICAL** — prophylaxis after elective arthroplasty | 10 | 7 | **5** | RE-NOVATE `NCT00168818` (n=3,494), RE-NOVATE II `NCT00657150` (n=2,055) |
| **CEREBRAL** — cerebral venous and dural sinus thrombosis | 5 | 5 | 1 | RE-SPECT CVT `NCT02913326` (n=120) |
| NONE — outside all four, each dispositioned with its criterion | 11 | 0 | — | |

**The empty-question test did not fire.** Every reading has eligible trials, so none is a
boundary and all four are reviews.

Precedence, stated rather than discovered: **CEREBRAL > SURGICAL > EXTENDED > TREATMENT.**
Cerebral first because a cerebral venous thrombosis trial is not a limb-DVT trial whatever its
comparator; surgical next because prophylaxis in a surgical population is a different question
from treating a clot that has already happened.

---

## Three findings the screen produced that the object does not carry

### 1. The review holds neither of its field's two largest treatment trials

`RE-COVER` and `RE-COVER II` — **5,153 randomised between them, both with posted results** — are
the acute-treatment anchors of this drug's VTE programme and **neither is in the object.**

### 2. EXTENDED contains a comparator mismatch, and it is the P38 shape

Both eligible trials report, and they do not share a comparator:

- **RE-MEDY** randomises dabigatran against **warfarin** — an active anticoagulant.
- **RE-SONATE** randomises dabigatran against **placebo**.

**A shared estimand would not make these poolable.** *Recurrent VTE against warfarin* and
*recurrent VTE against nothing* are different quantities, and this is exactly the axis on which
AMPLIFY and AMPLIFY-EXT were declined. Any pool in this reading must state which comparator it
holds and exclude the other for a **named axis**.

### 3. One of the object's four trials is not a venous thromboembolism trial

`NCT01505881` is the follow-on from RE-ALIGN — conditions `['Thromboembolism', 'Heart Valve
Prosthesis']`, a **mechanical heart valve** population, registered primary *"Percentage of
Patients With Any Adverse Event"*. It is **not in the surfaced set and correctly so**: a VTE
condition filter excluded it. Adjudicating it out of the included set is a screening decision on
this screened set and is now available.

---

## What is NOT decided here

- **Which readings, if any, pool.** That is the estimand screen, and it has not run. The
  comparator mismatch in EXTENDED is recorded as a fact about that reading, not as a verdict.
- **Whether `NCT01505881` is removed.** Named for adjudication, not removed by this document.
- **Recall remains 2/4 and is recorded, not repaired.** `RE-MODEL` (`NCT00168805`) was missed
  because it is coded with the broader term `Thromboembolism` while the query asked for *venous*
  thromboembolism — and the behaviour is not uniform, since RE-MEDY and RE-SPECT CVT carry the
  same code and were surfaced. A query widened until it returns the answer already held cannot
  discover anything.
- **No PubMed limb has been run**, so any trial reported in the literature and never registered
  is outside what was looked at.
- **Nothing is built.** No object, no page.
