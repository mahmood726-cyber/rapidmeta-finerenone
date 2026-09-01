# Methodology layer — status after one working block

**Date:** 2026-09-01 · **Owner:** this lane · **Scope:** the three measured gaps
Every claim below is stamped **MEASURED** (with the command), **INFERRED**, or **CLAIMED**.

---

## Headline

| gap | before | now | state |
|---|---|---|---|
| 1 · RoB has no sentence-level provenance | absent | **locates the supporting REGION: coverage@3 = 0.398 vs chance 0.012. Does NOT identify the supporting CLAIM: SJS +0.035 over chance, and its destruction test says that is not the lexicon's doing** | **partial — region yes, claim no; second scoring bounded the first** |
| 2 · cannot say what screening missed | absent | **micro recall 10.4%, pre-registered, truncation-free** | **number exists, and it is bad** |
| 3 · no certainty rating | absent | **mechanical GRADE inputs; certainty structurally refused** | **shipped, 10/10 controls** |

---

## ⛔ FIRST, A CORRECTION TO THE MANDATE'S PREMISE

**MEASURED** — `python probe_rob_groundtruth.py`

The mandate names Cochrane's `/references` page as free RoB-with-quote ground truth. **It is
not reachable.**

| route | result |
|---|---|
| `cochranelibrary.com/.../references` | **HTTP 412 on 6/6**, bot UA *and* browser UA |
| Europe PMC full text | **2 of 400** cardiology reviews have a PMC record; both `404` |
| PubMed abstract (**control**) | `200`, 87 KB, zero RoB fields |

The control is what makes those zeros mean anything: the probe can fetch, and can read.

**But "not by that route" is not "unobtainable"** — and the replacement is better than the
original, because it is a *published benchmark with a published baseline to beat*.

### The replacement: RoBBR

**MEASURED** — `RoBBR-Benchmark/RoBBR` on HuggingFace, ungated, **CC-BY-NC-4.0**
(Lou, Tao et al., *Measuring Risk of Bias in Biomedical Reports*, EMNLP 2025,
arXiv:2411.18831). Attribution required; non-commercial only.

| file | records | serves |
|---|---|---|
| `SSR_Cochrane_test.json` | 313 | **Gap 1** — sentence-level provenance |
| `Main_task_Cochrane_test.json` | 906 | RoB label; also the **Gap 2** seed set |
| `SJS_Cochrane_test.json` | 465 | supporting-statement selection |

`SSR` is *exactly* the missing artefact: `aspect2sentence_indices` maps each RoB aspect to
the sentence indices supporting it, with a published metric at k=3 and at optimal-k.

---

## GAP 1 — sentence-level provenance for RoB

**MEASURED** — `python rob_provenance.py`

A deterministic domain-cue lexicon scorer. **No model.** It never says low/high/unclear — it
only cites — so it makes no judgement and needs no RAISE declaration, and it touches no number.

| k | coverage | chance | full-cover | lift |
|---|---|---|---|---|
| 1 | 0.236 | 0.013 | 0.180 | +0.222 |
| **3** | **0.398** | **0.012** | **0.327** | **+0.386** |
| 5 | 0.443 | 0.019 | 0.363 | +0.424 |
| 10 | 0.528 | 0.078 | 0.440 | +0.450 |
| 20 | 0.591 | 0.099 | 0.496 | +0.492 |

**The declared error rate, stated plainly: at k=3 this surfaces a correct supporting sentence
for 40% of RoB aspects and misses 60%.** Median optimal-k in the data is **1**, so a perfect
selector needs one sentence where we need three and still miss most. This is a floor to beat,
not a solved gap.

**Scope declared, not silently zeroed:** 29 of 313 records are cluster-RCT / ROBINS-I domains
outside RoB-1's canonical six (`baseline characteristics` ×14, `recruitment bias` ×5,
`baseline imbalance` ×4, …). They are **named and excluded**, not scored as failures.

**Generalises without being redone** — the lexicon is keyed on the *Handbook's fixed domains*,
not on the clinical topic. The same file serves cardiology, HIV and malaria.

### Controls (all PASS)
- **MUST-FIRE** — "Randomisation was performed using a computer-generated random number
  sequence" must be selected for `random_sequence`. It is, at k=1.
- **MUST-NOT** — allocation concealment must pick the sealed-envelope sentence over funding
  and demographics. It does.
- **PLANT THE DEFECT** — lexicon replaced with a never-matching pattern → coverage collapses
  **0.398 → 0.095**; restored → **0.398 exactly**. Asserted, not eyeballed.

---

## GAP 2 — what screening missed

Two pre-registrations, both frozen before their result. **PREREG-1 was not edited when it
turned out to be flawed** — it stands as recorded, with a second measurement beside it.

| | prereg hash | micro recall | controls |
|---|---|---|---|
| **PREREG-1** (retmax 200) | `7b2b6fa8…` | **0.047** | 3/3 pass |
| **PREREG-2** (exact membership) | `4936eaa2…` | **0.104** | 3/3 pass |

**MEASURED** — `python screening_recall.py`, `python screening_recall_exact.py`

**Method:** relative recall against a known-positive seed set — 20 Cochrane review objectives
with ≥3 included trials, 106 seeds resolvable to PMIDs. Every seed is a known positive by
construction. 2 unresolvable seeds were **excluded from the denominator and reported**, because
a paper absent from PubMed cannot be found by a PubMed search and scoring it as a miss would
measure PubMed's coverage instead of ours.

### ⛔ PREREG-1 measured its own truncation, and a post-hoc check is what caught it

The exploratory OR variant scored **0.000** — *worse* than AND, which is impossible if OR's
result set contains AND's. That impossibility was the signal.

**MEASURED:** for one objective the AND query matches **843** records (200 examined) and the OR
variant matches **23,864,443** (1,000 examined = **0.004%**). PubMed sorts newest-first, so the
examined window systematically excluded older trials — exactly the ones a review included.

**⇒ Truncation cost 5.7 points: it halved the measured recall.** Same seeds, same queries; only
the instrument changed.

### The finding, reported as promised even though it embarrasses us

> **A mechanical AND-of-six-content-terms PubMed query retrieves 11 of 106 trials that Cochrane
> reviews actually included — 10.4%. Fourteen of 20 reviews score zero.**

**INFERRED, and load-bearing:** auto-generated boolean queries are not a viable screening
strategy. This is a floor for the crudest possible search, and the deliverable is not the
10.4% — **it is the apparatus that can now score any search strategy against known positives.**

**Declared prior 15% (band 6–35%) — HELD.** The first prior to hold tonight. PREREG-1's prior
of 40% missed low by a factor of eight.

---

## GAP 3 — GRADE inputs, and the line not crossed

**MEASURED** — `python grade_inputs.py` → **10/10 controls pass**

Emits k, n, df, Q, I², τ², interval bounds, **interval width as a ratio** (`hi/lo`, because on
a ratio scale a difference is meaningless), whether the interval crosses no-effect, design, and
mechanical indirectness signals (surrogate-outcome and composite-outcome pattern hits).

### ⛔ The refusal is structural, not a convention

```python
if certainty is not None:
    raise CertaintyRefused(
        "GRADE certainty is a panel judgement under Cochrane Handbook v6.5 and this "
        "system has no panel. Emit the inputs and let a human rate them.")
```

`downgrade_domains_scored` is `[]` and `certainty` is `None` on every emission, with the reason
carried **inside the payload** so it travels with any subset. **A convention that relies on
someone remembering gets broken by the next person in a hurry, and it fails silently. This one
raises.** No model is involved anywhere, so no RAISE declaration is required.

### Controls include must-fire *and* must-not-fire on every signal
Known answers hand-computed, not read off the code: Q=10/df=4 → I²=0.60 exactly; Q<df floors at
**0**; width ratio 2.0/0.5 = 4.0. `HbA1c` is flagged surrogate; **all-cause mortality is not**.
I² undefined returns **`None`, never `0`** — a blank and a zero are different facts.

---

## Defects found in my own work this block

1. **`rob_provenance.py` reassigned `sys.stdout` at module level** and closed the caller's
   wrapper on plain import — the exact failure my own rules file documents. Fixed at source
   with an `if __name__ == "__main__"` guard, not worked around.
2. **PREREG-1 measured truncation** (above). Caught by an impossible ordering, not by review.
3. **The post-hoc variant sweep did not do its job.** It was meant to show the harness could
   return a *high* number; instead every variant scored at or below the original because they
   were all truncation-bound. **The harness had not been shown able to discriminate until
   PREREG-2 moved it 4.7 → 10.4.**

---

## What I would do next, in order

1. **Gap 1 is the weakest at 40%.** The SJS split (465 records) gives supporting-*statement*
   ground truth as multiple choice — a second, independent way to score the same retriever.
2. **Score a real search strategy** with the Gap 2 apparatus — MeSH expansion, synonyms, an RCT
   filter. The apparatus is the asset; 10.4% is just its first reading.
3. **Wire Gap 3's emitter into the render path as data** — the page shows the inputs and says
   plainly that no certainty is rated and why.

---

# GAP 1 — SECOND INDEPENDENT SCORING (SJS), AND WHAT IT OVERTURNS

**MEASURED** — `ROBBR_DIR=robbr python rob_provenance_sjs.py` (true `rc=1`)

The same fixed lexicon, scored on a different RoBBR split with a different task format.
**It does not survive the second scoring, and the controls are what caught it.**

| scoring | task | result | chance | lift | n |
|---|---|---|---|---|---|
| **SSR** | retrieve supporting sentences from a paper | coverage@3 **0.398** | 0.012 | **+0.386** | 284 |
| **SJS** | pick which of 7 statements supports the judgement | accuracy **0.178** | 0.143 | **+0.035** | 422 |

## ⛔ The plant-the-defect control REFUSED to collapse, so the number was not reported

Destroying the lexicon entirely — every domain pattern replaced with one that matches
nothing — moved SJS accuracy **0.178 → 0.166**, against a chance floor of 0.143.

**The lexicon contributes essentially nothing on this task.** The harness printed
`collapse observed: NO -- CHECK IS INERT`, returned `VERDICT controls FAILED -- number not
reportable`, and exited 1.

⇒ **A plant-the-defect check earns its keep precisely when it does NOT collapse.** Had this
only ever been run on SSR, where it collapses 0.398 → 0.095, I would have carried "the
lexicon works" into the next component.

## The mechanism, measured rather than guessed

**MEASURED: a mean of 0.56 of the seven options score above zero on the domain lexicon**, and
inspection shows why — *all seven distractors are statements about the same RoB domain*. A
worked example (`blinding of outcome assessment`):

```
[3] score 0.3612  "Comment: no information on whether laboratory assessors were blinded."
[6] score 0.0216  "The study reported that blinding was unveiled only after ..."   <-- CORRECT
```

The lexicon picked the densest cue-bearing option. The correct one was the statement that is
**factually true of this paper**.

⇒ **SSR asks a TOPICAL question — which sentences concern this domain. SJS asks a FACTUAL
one — which claim about this domain is true here.** The lexicon answers the first and is
blind to the second.

## What this does and does not overturn

**Does NOT overturn:** SSR's 0.398 remains valid *for what it measures* — locating the
domain-relevant region of a report. The second scoring bounded the interpretation; it did not
falsify the measurement.

**DOES overturn:** any reading of 0.398 as "the retriever identifies the supporting
sentence". **It identifies the supporting REGION.** Choosing among competing claims within
that region is a separate capability the lexicon does not have, at all.

## ⭐ And the boundary falls exactly on the cite/judge line

Deciding which of several domain-relevant statements is true of a paper **is a judgement**.
It is the same act Gap 3 structurally refuses for GRADE certainty. So the honest position is
not that the retriever is weak at SJS — it is that **SJS is not a citing task**, and our
component is deliberately a citing component.

**Publishable form, and the only one that should be quoted:**

> A mechanical Handbook-domain lexicon locates the supporting region for a Cochrane RoB
> judgement at 0.398 aspect coverage in the top 3 sentences, 33× chance — **and it misses 60%
> of aspects at k=3.** On a second, independent split requiring the correct claim to be chosen
> among plausible same-domain distractors, it performs at **+0.035 over chance, which its own
> destruction test shows is not attributable to the lexicon at all.**

Never quote the 33× without both the 60% miss and the SJS null.

## Housekeeping defect found in my own reporting, same session

The first SJS run was piped to `tail`, which reported **`rc=0` while the script returned
`rc=1`**. `$?` through a pipe is the last stage's exit code. Caught within minutes of writing
the carry-over note about impossible scores — **owning a rule is not the same as the rule
firing.** Re-run unpiped: `TRUE rc=1`.
