# Eligibility no longer depends on whether a registry posted results

**Decision, 2026-08-27.** A trial's eligibility is decided by the review question. It is not
decided by whether ClinicalTrials.gov happens to hold a posted results record.

Provenance becomes a **recorded field on every extracted value** — which tier of artefact the
number was read off — so a reader can see where each figure came from and weight it. That is
strictly more information than the old rule provided, and it stops discarding evidence.

---

## 1. What the old rule was, in the corpus's own words

It was never written down as a decision. It was implemented as a screening verdict,
`ELIGIBLE_NO_RESULTS_YET` — eligible on the question, held out for want of a registry record.

The clearest statement of it is the one the corpus made while obeying it. From
`incretin-hfpef-review`, arguing for a two-trial pool:

> **"THE THIRD TRIAL IS MISSING FOR A PROVENANCE REASON, NOT A CLINICAL ONE. STEP-HFpEF DM
> would very likely move this estimate very little; it is left out because its registry record
> has no results, and that is a rule about where numbers may come from rather than a judgement
> about the trial."**

**This is not the correction of an oversight. It is the reversal of a deliberate, documented,
self-aware policy.** The corpus knew exactly what it was doing, said so, and predicted
correctly that the trial would barely move the estimate.

It was right about that and wrong about the tradeoff.

---

## 2. What the rule cost — measured, not asserted

### 2.1 The headline

> **What the registry-only rule was costing us was not a different answer. It was a less
> certain one.**

`incretin-hfpef-review`, KCCQ Clinical Summary Score, with STEP-HFpEF DM restored:

| | point | 95% CI | half-width |
|---|---|---|---|
| k=2, registry-only | 7.43 | 5.09 to 9.77 | ±2.34 |
| **k=3, rule withdrawn** | **7.38** | **5.51 to 9.26** | **±1.88** |

The point moves by 0.05. **The interval narrows by 20%**, because the excluded trial carries
39% of the weight and agrees with the other two.

A reader can check that our conclusion did not change and our confidence should have. That is
harder to wave away than "we were missing trials".

### 2.2 The scale

Trials set aside under the rule, counted on the **(topic, trial)** key — the only key that is
well-defined, because a trial can be used by one topic and unused by the topic beside it:

| | |
|---|---|
| (topic, trial) pairs excluded by the rule | **215** |
| distinct trials | 185 |
| topics affected | **9** |

Of a **randomised sample of 120** of those pairs (seed `20260827`, recorded before the draw):

| | rate | projected to 215 |
|---|---|---|
| a publication exists | 37% | 79 (60–99) |
| **a directly extractable result exists** | **23%** | **50 (35–69)** |

Clopper-Pearson intervals. **49 pairs are confirmed extractable outright** — evidence rather
than projection, independent of the remaining lookups.

> An earlier estimate of ~65 was drawn from a topic-ordered slice and was about 35% too high:
> the heavy topics were also the better-published ones. The randomised draw is the estimate;
> the convenience slice is not, and it produced a number of exactly the same shape.

### 2.3 What `k` was measuring

Across the **313** stored estimates carrying a point:

| provenance recorded | n |
|---|---|
| a journal cited | **0** |
| registry recorded, in prose | 20 |
| a block with no tier | 2 |
| nothing at all | 290 |

**Not one number this review publishes cites a journal.** So `k` has not been counting
evidence; for most rows it has not been counting anything stated.

---

## 3. The worked example

`STEP-HFpEF DM`, NCT04916470, KCCQ-CSS at week 52:

| field | value |
|---|---|
| provenance tier | **`JOURNAL_FULL_TEXT`** |
| source | NEJM `10.1056/NEJMoa2313917` |
| verbatim | **"7.3 (4.1 to 10.4)"** |
| estimand | treatment policy, week 52, n = 310 / 306 |
| endpoint rank | dual primary |
| **AACT outcome rows for this trial** | **zero** |

**Not derivable from any registry tier, at all.** One row, and it is the entire argument.

---

## 4. The estimand axis, which the rule change exposed

`estimand_established: True` asserted that every contributing trial measured the same quantity
— while the object contained **zero** occurrences of "treatment policy", "trial product",
"efficacy estimand" or "on-treatment". **It asserted sameness along an axis it did not record.**

It happened to be true. Nothing in the object made it true, and nothing would have caught it
had it been false.

### 4.1 The counterfactual, which is the cost of getting this wrong

Each of the three trials reports a second, on-treatment analysis of the same outcome:

| trial | pooled figure (regardless of adherence) | the paper's own on-treatment figure |
|---|---|---|
| STEP-HFpEF | 7.8 | 8.8 |
| SUMMIT | 6.9 | 9.8 |
| STEP-HFpEF DM | 7.3 | 8.6 |
| **pooled** | **7.38** | **≈ 9.0** |

> **Pooling each trial's other estimand shifts the answer by about 1.6 points, roughly 20%,
> while every individual number remains quotable and correct — and nothing in the output would
> show it.**

That is the magnitude of the error class, measured on our own data, having avoided it. We are
entitled to raise it against a published synthesis only because we can show it here first.

### 4.2 Consistent on the property, divergent on the label

The three papers label one strategy three ways: *treatment policy*, *treatment-regimen*,
*treatment policy*. `"treatment policy" == "treatment-regimen"` is **False** and the correct
answer is that they are the same.

What licenses the normalisation is **structural, not lexical**: each paper contrasts its
headline figure against an explicitly on-treatment alternative of its own. A report carrying
both a regardless-of-adherence figure and an on-treatment figure identifies which is which
without sharing anyone else's vocabulary.

**Both forms are therefore stored.** The verbatim label, because a normalised strategy alone
destroys the evidence a reader needs to check the normalisation. The normalised strategy,
because a verbatim label alone would make every future consistency check a string comparison.

### 4.3 The honest bound, with its denominator

| | n |
|---|---|
| outcome blocks in the corpus | **175** |
| assert `estimand_established: True` | **7** |
| of those, record the estimand structurally | **1** |
| **assert sameness, record nothing, and pool** | **5** |

**The fair statement is that the exposure is 5 pools, not 168.** The other 168 outcomes do not
assert sameness — they are silent, not wrong. "1 of 175 can be called like-for-like" is true
and carries an implication the evidence does not support.

### 4.4 The largest of the five, checked

`bococizumab-lipid-review/ldlc_pct_change_wk12` was checked first because it pools six trials
and because lipid trials routinely report both on-treatment and all-randomised analyses of
percentage change, where the gap is typically larger than the 20% measured on KCCQ.

**It is not mixed, on the evidence available.**

| trial | analysis population of the pooled figure | state |
|---|---|---|
| SPIRE-LDL `NCT01968967` | "Full analysis set (FAS) included all subjects who were randomized" | FOUND |
| SPIRE-LL `NCT02100514` | FAS, all randomized | FOUND |
| SPIRE-HR `NCT01968954` | FAS, all randomized | FOUND |
| SPIRE-SI `NCT02135029` | FAS, all randomized | FOUND |
| SPIRE-FH `NCT01968980` | FAS, all randomized | FOUND |
| **SPIRE-AI `NCT02458287`** | **not established** | **COULD NOT DETERMINE** |

**And the structure differs from the incretin case in a way that lowers the risk.** The NEJM
report's on-treatment analysis is a **pooled waterfall/responder analysis across all six
trials** — *"Waterfall plots were limited to the patients who had reported taking either
bococizumab or placebo within 21 days before the lipid measurement"* — not a per-trial mean
difference. There is therefore no per-trial on-treatment LS mean difference that could have
been picked up by mistake, which is the mechanism that would have produced mixing.

**The refusal is part of the result, not a caveat to it.** Five trials say FAS. The checker
was asked about six and **declined to conclude the sixth from the other five**, returning
`COULD_NOT_DETERMINE` for SPIRE-AI and saying so explicitly.

> An instrument that had generalised there would have produced a clean six-of-six that was
> **five facts and one inference**, indistinguishable in the output. Sameness must be recorded,
> not assumed from the company it keeps — which is the same claim this section makes about
> `estimand_established` itself, one level down.

**And it gives a risk criterion rather than a blanket worry.** The exposure is highest where a
paper publishes **both estimands at trial level**. That is the incretin shape — three papers,
each with its own on-treatment mean difference — and it is not the bococizumab shape. The
remaining pools should be triaged on that question first: does the paper offer a per-trial
alternative at all?

**One further limit, stated rather than resolved:**
- **SPIRE-SI's exact −54.5 row was not served.** The FAS wording and the arm means were, but
  the LS mean-difference row itself was not captured, so that value is tied to the figure as
  listed rather than to a served registry statistic row.

**This check was performed by ONE model family, not two.** agy was asked in parallel and
returned no output: headless mode auto-denied a `command` permission it needed. It contributed
successfully to the estimand check in §4.2 and failed here, so it is inconsistent rather than
unavailable. The result below therefore has the same evidential standing as the STEP-HFpEF DM
value — one family, with verbatim quotes and served URLs — and is not adjudicated.

### 4.5 A second pool cleared, for the same structural reason

`icosapent-lipid-auto-full-review/primary` (k=2, triglyceride % change). Both trials answer
the triage question **NO**: neither publication reports a per-trial alternative analysis of
that outcome. Both use the intent-to-treat population — *"all randomized patients who had a
baseline efficacy measurement, received >=1 dose"* (NCT01047683) and *"All efficacy analyses
were performed on the intent-to-treat population"* (NCT01047501).

**Two of five pools are now cleared, and both for the same reason: the mixing mechanism is
structurally absent, not merely avoided.** That is a stronger form of safe than matching
labels. Where a paper publishes no per-trial alternative estimand, there is nothing to pick up
by mistake — and a checker cannot be fooled by a coincidence of vocabulary, because vocabulary
is not what it consulted.

One limit: the checker could not fetch the publisher page and used served article-text
reproductions of the primary American Journal of Cardiology publications. Recorded rather than
resolved.

### 4.6 A second estimand axis nobody was looking for

`empagliflozin-hf-auto-full-review/primary` (k=2) answered the triage question **YES** — and
on an axis this document had not anticipated.

| trial | the figure we pool | the paper's alternative |
|---|---|---|
| `NCT03057977` | CEC-**adjudicated** composite, OR 0.731 | investigator-**reported**, HR 0.75 (0.66-0.85) |
| `NCT03057951` | CEC-**adjudicated** composite, OR 0.780 | investigator-**reported**, HR 0.77 (0.69-0.87) |

Both on the **Randomised Set, all randomised patients**. The *population* is identical across
both trials and both versions. What differs is **who decided that an event occurred** — a
blinded clinical-events committee, or the site investigator.

**The pool is not mixed:** both trials contribute the adjudicated version. But adjudication
status is a distinct axis along which the same outcome carries two numbers, and nothing in the
object records which version was taken.

> **This is why the triage criterion must stay STRUCTURAL even though a structural criterion
> is vaguer.** It was phrased as *"does the paper publish a per-trial alternative at all"*, not
> as *"does the paper report both ITT and on-treatment"*. The author was thinking about
> population splits and would not have gone looking for adjudication status. **A structural
> criterion catches axes its author did not anticipate; a vocabulary criterion catches only the
> ones they did.** That is the same lesson as never building a label-equality check, arriving
> from a third direction.

**Three independent arrivals at one rule.** The same conclusion was reached tonight by three
lanes that were not coordinating on it: an inverted-outcome detector that had to enumerate
failure shapes rather than phrasings; the refusal to build a label-equality check for
estimands, because `"treatment policy" == "treatment-regimen"` is False and the correct answer
is that they are the same; and this triage criterion, which caught adjudication status because
it asked whether an alternative EXISTS rather than what it is CALLED. **A rule reached three
ways from three directions is much harder to argue with than a rule asserted once.**

### 4.7 The last of the five, and a discrepancy it exposed

`rotavirus-vaccine-africa-review/primary` (k=3) is **consistent**: all three trials report the
quoted figure on a **per-protocol** population. `NCT02145000` also publishes an
intention-to-treat version (31 vs 87 per-protocol; 35 vs 125 ITT) and the figure we pool is the
per-protocol one, matching its two companions.

**Two things follow, and neither is a clean pass.**

First, **the pool is consistent on a per-protocol population**, which is the more permissive
choice for a vaccine-efficacy estimate. That is a defensible decision and it is not recorded
anywhere as one.

Second — and this is owed work rather than a finding — **one stored value did not reconcile.**
The checker reports that `NCT00241644`'s stored OR 0.561 does not follow from the counts its
publication serves (56/2974 against 70/1443), and it answered the triage question structurally
rather than from that row. **Our number may be a different outcome, a different timepoint, or
wrong.** It is recorded here unresolved rather than quietly re-derived.

> This was the pool predicted **low-risk** under the original criterion, and that prediction was
> revised in advance of the result once `empagliflozin` showed adjudication to be a live axis.
> The revision is recorded because a criterion is only worth having if it is used before the
> answer is known.

The five: `bococizumab-lipid-review/ldlc_pct_change_wk12` (k=6),
`empagliflozin-hf-auto-full-review/primary` (k=2), `icosapent-lipid-auto-full-review/primary`
(k=2), `inclisiran-lipid-kidney-auto-full-review/primary` (k=3),
`rotavirus-vaccine-africa-review/primary` (k=3).

---

## 5. What replaces the rule

**Eligibility** follows the review question.

**Every extracted value declares a provenance TIER** — `ssot/provenance_tier.py`, a closed
set, enforced by `scripts/gate_stored_estimate_declares_provenance_2026_08_27.py`.

The tier is not the source. "ClinicalTrials.gov" describes both a posted results table and a
background citation the protocol listed; those are not the same evidence. `REGISTRY_POSTED_RESULT`
outranks `JOURNAL_FULL_TEXT` outranks `JOURNAL_ABSTRACT`; `DERIVED_HERE` is rank 0 and
**inherits its inputs' tiers**; `REGISTRY_REFERENCE_ROW` is barred from carrying a value at
all, because a citation on a registry record is a pointer and frequently to something else
entirely.

**Mixed provenance is declared per row. It is never a reason to suppress an eligible trial.**

---

## 6. What is owed, named rather than closed

- **Hartung–Knapp at k=3.** The k=2 caveat records −7.74 to 22.60 on 1 df, spanning no effect.
  Two degrees of freedom substantially reduces that instability. **It has not been recomputed
  and is not claimed.** A referee will ask, and "we did not recompute it" is a weak answer —
  but a better one than a number computed to close an item.
- **`inclisiran-lipid-kidney-auto-full-review/primary` (k=3)** — the one pool of the five not
  yet checked. Its triage job did not return. It is the highest-exposure remaining case on the
  criterion: three lipid trials, continuous LDL-C percentage change, the shape most likely to
  publish a per-trial alternative.
- **A LIVE DISCREPANCY IN A STORED ESTIMATE, not a caveat on a check.**
  `rotavirus-vaccine-africa-review` stores **OR 0.561** for `NCT00241644`, and that value does
  not follow from the counts its own publication serves (**56/2974 against 70/1443**). It may
  be a different outcome, a different timepoint, or wrong. It has NOT been re-derived here.
  This is one of roughly nineteen live pooled estimates in the corpus, and *"a stored number
  that does not reconcile with its own source"* is precisely the class this document spends
  section 7 proving we cannot detect passively — it was found only because an unrelated
  triage job happened to fetch the counts.
- **`bococizumab-lipid-review` / SPIRE-AI `NCT02458287`** — analysis population not established,
  and deliberately not inferred from its five neighbours (§4.4).
- **Which version of an adjudicated endpoint each stored value represents** (§4.6). Nothing in
  the corpus records it, on any topic.
- **A flag to the sotagliflozin reconciliation.** That work argues a published synthesis pooled
  count-derived risk ratios against recurrent-event hazard ratios. **Adjudication status is a
  third possible source of divergence in that same comparison.** If SOLOIST or SCORED report
  both adjudicated and investigator-reported versions, the reconciliation must say which it
  used. Better we raise it than a referee.
- **25 of 215 lookups** outstanding.
- **313 estimates carry no provenance tier**, baselined so the count cannot rise.

---

## 7. The author's measured error rate, and its direction

This section exists because a methods section that lists only what worked is a sales document.
Every claim below was made by this lane during the work that produced this document, and
withdrawn or corrected before publication.

**Twelve substantive corrections.** Eleven were the lane's claims being too strong or too
narrow. The twelfth runs the other way and is listed last: an instrument turned out **broader**
than the reasoning that built it. It is recorded precisely because it is the exception — it
establishes that the accusing bias is a property of **inference**, not of instrument-building
as such.

| claimed | true | direction |
|---|---|---|
| the AACT snapshot is missing; the retrieval premise is falsified | present at `F:/AACT-storage`, exactly where the resolver looks — candidate paths were retyped into a shell loop instead of calling `_resolve_aact_root()` | **accusing** |
| 73 exclusions were made unauditable | **0** — the registration ID was the dictionary key, and the extractor read only values | **accusing** |
| 147 (topic, trial) pairs excluded by the rule | **215** — same bug, opposite direction | understating |
| 0 of 176 stored estimates cite a journal | denominator is **313**; the earlier count read one of two populations | understating |
| 185 distinct trials | corrected from 195 by re-deriving | neutral |
| ~65 trials with an extractable result | **~50 (35–69)**; the earlier figure came from a topic-ordered slice running 35% high | overstating |
| the `--model` flag is proven to override, by self-reported identity and cutoff | **withdrawn** — both sides of the differential were testimony, and a differential of two testimonies inherits both instabilities | false confirmation |
| 1292 screening rows lack an identifier | **663**, then **1**, over three narrowings of the checker's own vocabulary | **accusing ×3** |
| the widened `LOST_TAIL` pattern is correct | fired on correct prose twice — regex backtracking, then a missing word boundary | **accusing ×2** |
| — | `blk["pooled"] = dict(POOL)` re-committed the wholesale-replace defect repaired that same morning | self-inflicted |
| — | credited with invocation-path evidence this lane never produced; corrected upward | mis-attribution |
| the triage criterion covers ITT-versus-on-treatment splits | it also caught **adjudication status**, an axis the author had not considered — the instrument was BROADER than the reasoning about it | **the exception** |

**Seven of twelve pointed the accusing direction** — at the corpus, or at a tool, when the
fault was the lane's own.

> **This lane is materially more likely to produce a false accusation than a false clearance.**
> That is a stable bias, not noise, and every number in this document should be read knowing
> it. The direction is the useful part: our errors inflate the corpus's apparent defects, so a
> reader should discount our criticisms of ourselves before discounting our measurements.

**The accusing errors came from inference; the understatements came from recall.** Different
sources, different remedies — the first is fixed by planting a defect, the second by
re-deriving rather than remembering.

### 7.1 What caught them

**Every one was caught by measurement — a plant, a guard, a known positive, a re-derivation.
Not one was caught by re-reading the reasoning that produced it.**

That is a resource-allocation fact rather than a counsel of despair: **review of one's own
reasoning had a measured yield of zero here.** Spend the effort on the plant.

The clearest case is the last row but one. A key-path guard was written at the start of this
session, for exactly the defect of replacing a nested block wholesale. Six hours later the same
defect was committed again, in new code, by the author of the guard. **The guard refused the
write and saved 14 nested keys — which turned out to contain the corpus's own argument for the
two-trial pool, quoted at the top of this document and the best evidence in it.**

> **A rule you have written is not a rule you have applied.** The guard is the durable form.
> Prose is not.

---

## 8. How the evidence was obtained

Estimand labels: **two model families searching independently** — Codex (GPT-5) and agy routed
to Gemini 3.1 Pro (High) — agreeing on both labels, both alternates and both alternate values.

Routing was confirmed from the agy CLI's own telemetry (`Propagating selected model override
to backend: label=...`), **not from either model's report about itself**. An earlier check
using self-reported model identity and knowledge cutoff was withdrawn: a model's report about
itself is testimony whichever field is asked for, and a differential built from two testimonies
inherits the instability of both.

**The STEP-HFpEF DM value itself rests on one family plus a source URL and a verbatim quote.
It is not adjudicated, and the object says so.**

The k=3 pool was computed by `scripts/pool_incretin_hfpef_kccq_2026_08_27.py`, which
reproduces the previous k=2 pool to four decimals before it is permitted to compute k=3, and
which **refuses an interval whose confidence level it does not recognise rather than defaulting
to 1.96**. It was compared against the published syntheses **only after** it was computed:
7.40 (4.90–9.90) differs by −0.016; 7.33 (5.84–8.82) by +0.054.

> Agreement to within 0.05 points of two published figures is precisely the condition under
> which a number gets accepted instead of derived. The order is why we can say it was derived.
