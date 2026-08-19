# `acs-antiplatelet-review` — the P21 decision

**Date: 2026-08-19.** Written **before any screening**, so the readings cannot be chosen to suit
the counts. Counts do not appear in this file.

---

## Why a decision is owed

The object already withdrew its pooled estimate and stated why. The four trials it holds do not
differ by a detail — **they are four different comparisons**:

| trial | what was randomised |
|---|---|
| **PLATO** `NCT00391872` | **ticagrelor** against **clopidogrel** |
| **TRITON-TIMI 38** `NCT00097591` | **prasugrel** against **clopidogrel** |
| **ISAR-REACT 5** `NCT01944800` | **ticagrelor** against **prasugrel** |
| **TWILIGHT** `NCT02270242` | **ticagrelor alone** against **ticagrelor plus aspirin** |

> Averaging these into one pairwise odds ratio asks a question no trial answered. Three of the
> four compare *which* P2Y12 inhibitor; the fourth compares *how much* antiplatelet therapy —
> and its outcome is **BARC bleeding**, not an ischaemic event.

**A trial comparing two active drugs and a trial comparing a drug against its own withdrawal are
not the same review**, whatever their trials have in common.

---

## The readings, anchored before any count

| id | reading | the question | anchor |
|---|---|---|---|
| **A — POTENT vs CLOPIDOGREL** | a newer P2Y12 inhibitor against clopidogrel | does replacing clopidogrel with a more potent P2Y12 inhibitor reduce ischaemic events after ACS? | **PLATO**, **TRITON-TIMI 38** |
| **B — HEAD TO HEAD** | ticagrelor against prasugrel | between the two potent agents, is either better? | **ISAR-REACT 5** |
| **C — DE-ESCALATION** | withdrawing aspirin, or stepping down potency, on a background of P2Y12 inhibition | does removing part of the antiplatelet regimen reduce bleeding without costing ischaemic protection? | **TWILIGHT** |

**Reading C's outcome family is bleeding and it says so on its face.** That is not a defect of
the reading; it is what the question is *for*. What was wrong was pooling a bleeding odds ratio
with three ischaemic ones under one heading.

### Precedence, stated rather than discovered

1. **C — DE-ESCALATION** — the randomised contrast changes the NUMBER or DURATION of agents
   rather than which P2Y12 inhibitor is used. Read from `armsInterventionsModule`.
2. **B — HEAD TO HEAD** — both arms carry a *potent* P2Y12 inhibitor (ticagrelor, prasugrel).
3. **A — POTENT vs CLOPIDOGREL** — one arm potent, the other clopidogrel.

Anything reaching none of the three is **not one of these reviews** and is dispositioned in the
screen with the criterion it failed named.

## Known members asserted in advance (P43)

The partition is refused if any of these lands elsewhere:

| registration | must be | why |
|---|---|---|
| `NCT00391872` PLATO | **A** | ticagrelor vs clopidogrel |
| `NCT00097591` TRITON-TIMI 38 | **A** | prasugrel vs clopidogrel |
| `NCT01944800` ISAR-REACT 5 | **B** | both arms potent |
| `NCT02270242` TWILIGHT | **C** | the contrast is aspirin's presence, not the P2Y12 agent |

## The empty-question test, set before the counts exist

> A reading with **no eligible trial** is not a review; it is an **empty question**, named as a
> boundary on the other readings' pages. A reading with eligible trials and **no reported
> results** *is* a review and publishes a refusal naming every trial.

---

## THE SEARCH BEHIND THIS IS INCOMPLETE, AND NOTHING MAY BE BUILT UNTIL IT IS NOT

`evidence/2026-08-19-batch1/acs_antiplatelet_search.json`. Two blocking facts:

1. **The cursor exhausted at 203 records against a reported total of 430.** A null
   `next_page_token` is **not** a proof of completeness — the proof is the sum across pages
   reconciling with `totalCount`, and here it does not. **227 records are unexamined, not
   excluded.**
2. **Recall is 3/4.** TWILIGHT was never surfaced, because its coded conditions are
   `['Cardiovascular Disease', 'Interventional Cardiology']` and the query filtered on ACS
   terms. **P42: a coded field that is correct and does not answer the question asked of it.**
   The miss is **recorded, not repaired** — a query widened until it returns the answer already
   held cannot discover anything.

**So this file is a decision, not a licence to build.** The readings and their anchors are
fixed; the evidence base under them is not yet complete, and building on a search that is 47 per
cent short would produce three complete-looking reviews over an unknown denominator.
