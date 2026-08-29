# Layer 8 — decision support, designed before it is built

**Cochrane does not make recommendations. That is editorial policy, and it is principled:
recommendations need value judgements, context and resource information a review cannot
supply.** So this is uncontested ground — and if we simply *assert* a recommendation we commit
the exact fault we criticise: an unsupported claim, on a page, about patient care.

⇒ **The answer is our own position applied to recommendations: make it DERIVED, and show the
derivation.** A reader then disagrees with our *threshold* rather than with our conclusion, and
can recompute the result with their own.

---

## The governing rule

**Every input is one of three kinds, and each is rendered differently on the page.**

| kind | example | how it is shown |
|---|---|---|
| **COMPUTED** | absolute risk difference, NNT, certainty, direction | the value, with its source and rung |
| **PARAMETER** | the minimally important difference; how a harm is weighed against a benefit | **stated, defaulted, and changeable** — the page prints the value used |
| **UNAVAILABLE** | drug price, local capacity, patient preference evidence | **named as missing**, never guessed |

⛔ **A recommendation that depends on an UNAVAILABLE input cannot be issued.** The layer says
what is missing and what would change the answer.

---

## Component 8.1 — Comparison to previous syntheses

Our estimate · theirs · the difference · **and which of two things the difference is**:

- **EVIDENCE** — a different included set, a newer trial, different counts (registry versus
  adjudicated)
- **ESTIMAND** — the same trials measured differently (binary versus time-to-event, first-event
  versus recurrent, different composite)

⇒ **That distinction is the whole value of the comparison.** "We get 0.71 and so do they" is
corroboration; "we get 0.77 and they get 0.71 because they pooled a different endpoint" is a
finding. Already a standing requirement and still absent from most pages.

**Inputs:** comparator component (built) → published estimate; our pooled estimate. **Refuses**
when no comparator is identified.

---

## Component 8.2 — Evidence class for guideline writers

⚠️ **Not asserted as `1a`. Computed, with the rule printed beside it.**

```
class 1a   ≥2 randomised trials, pooled, certainty HIGH or MODERATE, consistent (I² < 50%)
class 1b   a single randomised trial, or pooled with certainty LOW
class 2    non-randomised evidence only
class X    certainty PENDING or NOT_ASSESSED — no class can be assigned
```

**The rule above is a proposal and it is the sort of thing that varies between guideline
bodies.** It is printed on the page precisely so a body using a different scheme can map it,
rather than inheriting ours silently.

---

## Component 8.3 — Clinician recommendation, via GRADE Evidence-to-Decision

**Nine criteria. What we can compute, what is a parameter, what is unavailable:**

| EtD criterion | status |
|---|---|
| Problem — is it a priority | **UNAVAILABLE** (context) — stated as an assumption |
| Desirable effects | **COMPUTED** — absolute reduction, NNT, per outcome |
| Undesirable effects | **COMPUTED where harms are obtained** — 72.6% of trials at rung 2 |
| Certainty of evidence | **COMPUTED** — `grade_authority.resolve()` |
| Values — how patients weigh the outcomes | **PARAMETER**, defaulted and printed |
| Balance of effects | **DERIVED** from the four above plus the threshold |
| Resources | **UNAVAILABLE** — named as missing |
| Equity | **PARTLY COMPUTED** — subgroup strata where the trials report them |
| Acceptability / feasibility | **UNAVAILABLE** — named |

### The strength rule, stated mechanically

```
NO RECOMMENDATION      certainty is PENDING or NOT_ASSESSED
                       or harms were never measured
                       or the interval spans the threshold in both directions

CONDITIONAL            certainty LOW, or the interval crosses the threshold,
                       or a named subgroup shows no effect

STRONG                 certainty HIGH or MODERATE
                       AND the whole interval lies on one side of the threshold
                       AND harms are measured and not offsetting
```

⚠️ **Strength follows from effect size, certainty, harms and the stated threshold — never from
our confidence.** The rule is short on purpose: a rule a reader cannot check is an assertion.

### ⭐ And the subgroup condition, which the dapivirine work made unavoidable

**Where a trial reports a stratum in which the effect is not demonstrated, a recommendation
must be stratified or explicitly not extended to it.** The ring shows 56% (31–71) over 21 and
−27% (−133 to 31) at 21 and under. **A single unstratified recommendation there would be
wrong for the group most likely to be offered it.**

---

## Component 8.4 — HTA view

**Absolute effects, NNT, and what a payer needs that a review never gives.** Not a
cost-effectiveness model — we have no price data, and inventing one would be the worst possible
version of asserting an unavailable input.

**What it can honestly carry:** events averted per 1,000 treated; NNT with its interval;
duration over which that holds; the subgroup in whom it does not; **and an explicit statement of
what a payer must supply** — unit cost, time horizon, local baseline risk — **to complete the
calculation.** That is a template a payer can fill, which is more useful than a number computed
from prices we do not have.

---

## Component 8.5 — Public explanation

**Cochrane has plain-language summaries and they are widely criticised as still unreadable. So
this is beatable on quality, not merely on presence.**

**Testable properties, not a style aspiration:** no unexplained relative risks · absolute
numbers as natural frequencies ("about 22 of every 1,000 women") · uncertainty stated in words
that carry direction · **and the thing that is not shown to work said as plainly as the thing
that is.**

⚠️ **It gets a readability gate like any other check**, and its result goes in the integrity
section, so "we wrote a plain summary" is a measurement rather than a claim.

---

## Where layer 8 sits, and what gates it

```
BUILD (layers 1-8)  →  DEFECT SUITE  →  FIX  →  PRE-JUDGE  →  JUDGE BLIND
```

**Layer 8 is generated content, so it is inside BUILD and gated by everything after it.** Three
new defect classes come with it, and they are the ones I would expect this layer to produce:

- **`recommendation-without-a-derivation`** — a strength with no rule shown
- **`recommendation-over-unassessed-certainty`** — the certainty-over-unadjudicated-RoB class,
  one layer up
- **`unstratified-recommendation-over-a-null-subgroup`** — from dapivirine

---

## What I want ruled before building

1. **The strength rule above** — it is mine, it is short, and it will decide what pages say
   about patient care. It should be a human ruling, not a lane's proposal.
2. **The default threshold.** A minimally important difference is a clinical judgement per
   outcome. My proposal: **no default at all** — the layer refuses until a threshold is
   supplied per outcome, and prints which outcomes lack one. A defaulted threshold that nobody
   chose would be an invisible value judgement doing real work.
3. **Whether we issue clinician recommendations at all**, given Cochrane's principled refusal.
   The derived-and-shown design answers the objection in my view — but it is a change in what
   this project claims to be, and it should be decided rather than drifted into.
