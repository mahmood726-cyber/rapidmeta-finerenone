# Mistake ledger

The mechanisms this project keeps producing, why they survive, and what each one
cost. Written for whoever has to trust a number on one of these pages.

The machine-readable detail — promotion criteria, per-detector reasoning, the
full instance lists — lives in `scripts/gate_integrity.py`. This file is the part
that generalises.

---

## The sentence this all reduces to

> **The question is never "did I do it". It is "did it land where it has to be".**

Four instances of one shape. In every one the action succeeded *and reported
success*, so nobody had any reason to check further:

| what was done | what was assumed | what was true |
|---|---|---|
| `git push` exited 0 | the site is updated | the ref moved; the site served the old bytes |
| the hook was repaired | the repo is gated | 6 of 12 checkouts still ran the old hook |
| a detector was written | the defect is caught | no build ever invoked it |
| a register was written | the backlog is kept | it was inside a gitignored directory and existed in no clone |

`git push` exits 0. The editor saves. `open(path, "w")` returns. **Nothing is
lying — the confirmation simply answers a different question from the one that
matters.** These come apart at every boundary an artefact must cross to take
effect: a deploy, a clone, a working tree, an import. Each boundary needs its own
confirmation, taken **from the far side** — fetch the served bytes, run the hook
from a second checkout, assert the detector was invoked, ask git whether the file
is tracked.

All four fail toward comfort. That is why all four survived.

---

## Why the ones we find are all the same shape

Ask of every check, gate, rule and instrument: **when this is wrong, is its
output alarming or reassuring?**

- **Fails toward alarm** → someone investigates → it is fixed or removed. It
  cannot survive long, because a false alarm is expensive to whoever is standing
  next to it.
- **Fails toward comfort** → nobody investigates a green result → it survives
  indefinitely, and its survival gets mistaken for its being correct.

Every mechanism found in this project failed toward comfort. That is not
coincidence, it is **selection**: the alarming ones were removed long ago by
whoever got tired of them. What remains in any long-lived codebase is
disproportionately the checks that are wrong in the pleasant direction.

**Practical consequence.** Comfortable failure modes cannot be found by waiting
for them to cause trouble, because causing no trouble is precisely their
property. They have to be hunted. When adding any check, write down its
comfortable failure mode **first** — the specific way it could report success
having established nothing — then construct that input and confirm it blocks. If
you cannot construct it, you do not yet understand the check.

Prefer designs where the comfortable direction is unavailable: an expected-section
manifest rather than a comparison of shared sections; UNMEASURED as a verdict
distinct from PASS; an unloadable page recorded as unmeasured rather than as zero.

---

## The matched pair — the cleanest evidence we have

Two probes, one root cause, opposite failure directions, wildly different
survival times.

**Root cause, both:** *a probe that establishes something answers, never that the
right thing answers.*

| | what it did | cost | how long it lasted |
|---|---|---|---|
| **False death** | a liveness probe queried the wrong model pool and reported a live seat dead | an entire verification family stood down | **caught the same day** |
| **False life** | the regression gate reused whatever answered on port 8787 — a sibling working tree of the same repo, on another branch — and passed pages that were not the pages being pushed (ARNI 912,140 bytes over the wire against 6,147,695 on disk) | every green relayed upward as confidence | **ran a full day** |

Same defect class. **The only difference was which direction it failed in.**
Nothing about the false-life version was subtler or better hidden; it simply
never gave anyone a reason to look.

Note that hash- or size-comparison is useless as an identity check between clones
of one repository — two working trees agree on most files most of the time, so
any comparison of *existing* content passes constantly. The only probe another
directory cannot satisfy is a **nonce**: content that did not exist anywhere a
moment ago. And the correct response to a failed identity check is **refuse
(exit 2), not warn** — a gate reading another directory is worse than no gate,
because no gate at least never produces a green.

---

## The payoff case for "a gate needs a constructible failing input"

The wrong-tree defect **was not found by looking for it.** It was found because
the three-state verdict needed a fixture that could fail; the real pages could
not produce one (the gate's double-load warms the cache, so they always passed);
a purpose-built fixture therefore had to be written — and it 404'd against a
server that was returning 200 for every real page.

**The discipline did not merely verify the check it was applied to. It discovered
an unrelated and much larger defect.** Insisting on a constructible failure forces
you to interact with the system in ways that passing tests never do, and the
discrepancies you trip over on the way are frequently worth more than the check
you set out to build.

---

## Checks that report something other than what they measure

Three in one day, all of which read to a human as a stronger claim than they are:

- **`no_rob_banner`** tested for a *disclosure element*; it read as "this page has
  a risk-of-bias assessment". Pages that pass it carry **zero** assessments —
  one prints "Provisional RoB-2 and GRADE" over 0 of 145 trials assessed.
- **`zero_included`** (now `no_studies_rendered`) asserted "this review includes
  no studies"; it observed "no studies rendered within the sampling window".
- **"read raw HTML"** was adopted as a rule to stop a text extractor silently
  dropping content — and then counted JavaScript template source as page content,
  reporting 62.8% of pages as carrying source links against a true 2.2%.

**Name a check for what it observes, not for what you hope it implies.**

---

## Rule regressions

A rule can make things worse, and should be logged when it does.

**"Read raw HTML, never rendered-text extraction."** Adopted in response to a real
under-count; within the hour it produced a forty-fold over-count, **in the
reassuring direction** — it said the corpus was well sourced when it is not. A
rule that fails toward comfort will not be questioned, because its output is the
answer everyone hoped for.

The corrected form has two halves:

> Rendered text **under**-counts by omitting what is not displayed. Raw HTML
> **over**-counts by including what is not content. Read raw HTML so nothing
> hidden is lost, then **attribute content to its context** — script and style
> bodies are program text, not page content. And when a page builds its own DOM,
> **say which reader you measured**: "in the served markup" and "after JavaScript
> runs" are different claims, and here they differ by a factor of forty.

Rules now earn the same treatment as gates: state what the rule does *not*
establish at the moment it is adopted, and re-derive at least one number under
both the old and the new rule before trusting it.

---

## Diagnoses that were wrong, and cheap

Kept because the cheapness is the point: each was wrong, each was testable, and
each was disproved in minutes.

- **"The Pages deploy is rate-limited."** It was an open GitHub incident affecting
  Pages. I had checked `components.json`, which said *operational*, rather than
  the unresolved-incidents feed — asking the comfortable question and then
  building a causal story on the answer.
- **"The flakiness is the third-party rate limiter."** Wrong: blocking every
  third-party host made the value settle *faster*, because the fetches fail fast
  instead of hanging.
- **"The flakiness is reused browser state / sessionStorage."** Wrong:
  sessionStorage was empty and clearing it changed nothing.

The actual cause was neither — the gate sampled a value that had not finished
settling (0 at 2.5 s, 0 at 6 s, 7 at 12 s on a cold load).

**The bad diagnoses are the untestable ones.** These three cost minutes each
because every one named something that could be checked.

---

## A false-alarm near-miss — the rarer specimen

Worth logging precisely because we have far more false-clearances than these.

The inclusion count on ~874 pages depends on data fetched at load. The obvious
inference was that those pages **compute their results** from third-party data,
which would have meant the corpus's findings evaporate whenever a CDN is down.

Tested instead of inferred:

| | included | pooled estimate | I² |
|---|---|---|---|
| 2.5 s, network allowed | 0 | 7.36 | 72% |
| 12 s, network allowed | 7 | 7.36 | 72% |
| **fully offline** | 7 | **7.36** | 72% |

**The estimates are identical offline.** They come from embedded data. The
inclusion count and the estimate travel by different paths, and **stopping at the
visible symptom would have condemned the whole corpus wrongly.**

A rule that fails toward alarm is the rarer and more valuable specimen. Log them.

---

## The sharpest instance: the rule broken by its own author, inside its own enforcer

We promoted a rule after a substring classifier matched `AF_` inside `TAF_TDF`:

> **Normalise and compare the whole field. Never test a fragment.**

Hours later I built `v1_coverage_audit.py` — a tool whose entire purpose is to
detect checks that report something other than what they measure — and its
blind-detector substring-searched gate output for `UNCHECKABLE`, matching
`card_alignment_gate`'s own **tally label** (`UNCHECKABLE 508`). It reported a
working gate as blind and inflated the headline from 20/26 to 22/26. That figure
was relayed onward before it was corrected.

**The rule was written, published, and then broken by its author in the tool
built to enforce it.**

That is worth more than a dozen clean detections, because it shows the gap is not
knowledge. We knew the rule; it was three hours old and we had all quoted it.
**Knowing a rule does not apply it. Only a check does.** Every rule in this file
that is not also a constructible check should be read as a rule we will break.

## A surface that can express failure but not justification

**The most important finding of 2026-08-18, and nothing statistical could have
caught it, because it is not in the analysis — it is in the rendering layer.**

`build_app_v2._outcome_section` had a `withdrawn_reason` field, rendered first and
prominently, with a comment explaining why: *"The reason is the deliverable; the
withdrawal is only its consequence."* **It had no field at all for the reason a
pool STANDS.**

So the projector could say why an estimate was **retracted** and had no way to say
why one was **kept**. For three consecutive topics that cost nothing, because all
three were withdrawals. On the fourth — a pool where the estimand was identical
across three registrations, every value matched the registry digit for digit, and
the pooled number reproduced to four decimals — **all of that verification landed
in the object and none of it reached the page.**

**The general form:**

> A surface that can express failure but not justification will make a careful
> project look purely destructive, and will hide exactly the work that vindicates
> a published number.

Why it is worth its own entry rather than a line in a build log:

- **It is a bias in the rendering layer, not the analysis.** Every number was
  right. Every gate passed. No statistical check exists that could fire on this,
  because nothing is wrong with the computation — the artefact simply has no slot
  for one half of the conclusion.
- **It is invisible while the news is bad.** Three withdrawals in a row and the
  asymmetry is undetectable, because a withdrawal-shaped renderer renders
  withdrawals perfectly. It becomes visible only on the first verdict that goes
  the other way — which is the verdict least likely to be reached by anyone
  working under momentum.
- **It compounds with the reader's inference.** A reader of these pages sees
  reasons attached to retractions and bare numbers attached to claims, and
  correctly concludes that the retractions are the checked ones. **The rendering
  taught a false lesson about which of our outputs were verified.**

Sweep the class the same way as any other: for every conclusion this corpus can
reach, ask whether the artefact has somewhere to put the REASON — not only for
the negative branch. `absent_from_source` had the mirror defect on the same day:
it announced "no resolvable link to a paper was recoverable" on an object whose
links had since been filled in. **An absence that has been filled must stop being
announced.**

---

## A fabricated contrast — a comparison that was never run

**Found 2026-08-18 on EVOLOCUMAB_MIXED, and it is worse than every arm defect
already in this file.**

The arm defects logged above — RE-LY entered as dabigatran-versus-dabigatran,
TAF-versus-TAF, seven trials with the intervention arm labelled "Placebo" — are
all **labelling** errors. The ledger already records why they survive: *"the
derived odds ratio was unaffected in MAGNITUDE, which is exactly why nothing
caught it."* The numbers stayed right.

A **cross-pairing** is different in kind. BERSON and Hua Tuo are four-arm 2×2
designs of dosing frequency, and each registered two comparisons, both *within* a
frequency. This corpus paired a **fortnightly placebo arm against a monthly drug
arm**, on both trials. That comparison was never registered, never analysed and
never reported by anyone — and the numbers it produced, −71.8 and −70.8, are
neither registered comparison **and not the difference between any two of the four
arm means either trial reports.**

> **The magnitude is not preserved. The contrast is invented, and so is the
> number.**

**Why no check we own could ever have found it.** Internally the row is perfectly
coherent: two real arms, from one real trial, with a real difference between them.
Every gate in this repository passed it, including the ones written specifically
about arms. **Internal consistency is exactly the wrong instrument here, because
the artefact is internally consistent by construction.** The only thing that can
convict it is the registration's own list of comparisons — a fact that lives
outside every file we control.

**Scope, measured rather than guessed.** Across 34 objects and 109 trial rows,
**26 rows (24%) sit on a multi-arm registration**, which is where the defect is
possible at all. One is confirmed, six are cleared, and **nineteen cannot be
cleared** — nine of those because the registration declares more than two arms and
no between-arm analysis at all. So the honest statement is neither "one page" nor
"a class": **one confirmed and nineteen unmeasured, over a quarter of the corpus.**

**The general form, for the next family of artefacts:** wherever a source offers
more than two things to compare, an extractor can silently choose a pair the
source never compared. Ask of every extracted contrast: *does the source declare
this comparison?* — not *are these two numbers real?*, which they always are.

---

## Silent exclusion — measured, and the answer splits in two

**818 trials are named in a page's own include list and contribute nothing to its
pool, across 360 pages. Not one of those pages says so.**

Found because COLCHICINE_CVD dropped CLEAR SYNERGY — the largest trial in the
topic at 7,264 randomised, and the only null one — in silence. DOAC_AF dropped
ROCKET AF the same way and DOAC_CANCER_VTE dropped ADAM VTE. In every case the
mechanism was MECHANICAL, not chosen: those trials carry no event COUNTS on the
page, and a pool derived from 2x2 counts drops whatever has none.

**The fear was publication bias without an author.** A pipeline that drops trials
for a reason correlated with their RESULT manufactures exactly that, and nobody
has to intend it. So it was measured rather than argued about.

**THE BIAS QUESTION: the answer is reassuring, and it is stated first because it
is the one everybody expects to be bad.** Of the 604 dropped trials carrying a
usable ratio: **352 favour the intervention, 29 are null-ish, 223 favour the
control**, geometric mean **1.109**. Dropped trials are directionally MIXED and
skew, if anything, slightly AGAINST the intervention. **There is no sign of the
specific pattern feared — null and unfavourable trials being lost while
favourable ones are retained.**

**THE SCALE QUESTION: the answer is not reassuring at all.** 818 dropped trials,
360 affected pages, and the losses include MORDOR-I at 190,000 participants,
AVENIR at 90,000, TIDES at 20,067, ROCKET AF at 14,171, SCORED at 10,584. **A
review that names a trial and then silently omits it is misreporting its own
evidence base regardless of which way that trial pointed.**

**And a third thing fell out of the measurement.** 91 of the dropped trials carry
a NON-RATIO value in a field named `publishedHR` — mean differences stored in a
hazard-ratio slot. It surfaced as a `math domain error` when the geometric mean
was computed, which is the cheapest possible way to learn it.

**The general form.** When an artefact can omit an input without saying so, the
question is never only "is the omission biased?" — it is also "how much of the
declared evidence base is missing?" The first question had a comforting answer
here and the second did not, and a screen that only asked the first would have
returned a clean bill of health over 818 missing trials.

---

## A page invisible to the tool that counts pages

`INCRETIN_HFpEF_REVIEW.html` was reported as having **no index card** by
`cardio_program_status`, and was silently skipped by `project_index_cards`. It has
a card. That card published **`HR 0.41 (0.22—0.79), k=3`** while its object held
**OR 0.4846 (0.3178—0.7389) at k=2** — a different measure, a different value and
a different trial count.

Both tools matched card links with `[A-Z0-9_]+.html`. **HFpEF has a lowercase
`p`.** For as long as those tools have run, the topic was classified as uncarded,
its card was never compared against its page, and it escaped card-alignment
checking entirely.

**The general form, and it is worse than an omission:**

> A record invisible to the instrument that counts records is not merely
> uncounted. It is counted as a DIFFERENT THING — and every rate computed over
> that denominator is wrong in a direction nobody can see.

This is the `no_studies_rendered` lesson one level up. That one taught us to
distinguish "observed zero" from "could not observe". This one is narrower and
nastier: the instrument observed confidently, reported a definite category, and
the category was an artefact of a character class.

**Practical consequence:** any pattern that enumerates the corpus — page names,
registration ids, section headings — should be tested against the *actual* set it
claims to cover, not assumed from the naming convention. The convention here was
uppercase page names, held for over 1,400 pages, and broke on one.

---

## An idempotency failure produces a well-formed object

Found 2026-08-18 on the bococizumab replacement. A patch helper **appends** to
`outcomes[]`; I re-ran it while adding two missing trials, so the same outcome
definition was appended **three times**.

**Every gate passed.** The `results` block is keyed by outcome id and therefore
held exactly one copy; the page rendered correctly; the card projected correctly;
`build_stamp`, `card_matches_page` and `headline_reproducible` were all green. The
object was internally consistent and externally correct **and still wrong**.

> **An idempotency failure produces a well-formed artefact, so no validity check
> can see it. Only a diff against the EXPECTED CHANGE reveals it.**

This is the sharpest form of a pattern this file already carries in other clothes:
`git push` exits 0, the editor saves, the detector runs. **Validity and delta are
different questions**, and every check in this repository asks the first one.

**The rule, and it is cheap: after any patch, verify the DELTA, not the validity.**
What did this change add, and is that what I meant to add? A `git diff --stat` on
the object would have shown 19 insertions where 7 were intended.

It was caught only because the card read `k=3` where the analysis was `k=5` — a
number that disagreed with something I already knew. **Had the trial count
happened to be right, three duplicate outcome definitions would have shipped and
nothing in the harness would ever have mentioned them.**

---

## An instrument that fails in the way it was built to detect

Four instances on 2026-08-18, which is the point: this is a **pattern**, not four
incidents. In each, the defect the tool exists to catch was present in the tool.

| the instrument | what it exists to catch | what it did |
|---|---|---|
| `arm_identity_gate` (fix cut 1) | an arm label that misidentifies its arm | deleted the control word from a pure placebo arm, so an inverted arrangement passed |
| `arm_identity_gate` (fix cut 2) | a finder widened without its classifier | matched `placebo <ANY WORD>`, destroying eight correct detections |
| `registration_identity_gate` threshold | a check that cannot fail | picked a threshold that **excluded its own founding case** — 0.75 against a 0.825 fixture |
| `registration_identity_gate` reader | a partial read reported as complete | read `intervention`/`control`, summed **one arm**, and called it the trial total |

The last is the sharpest: `arm_identity_gate` carries a comment documenting that
the v1 objects key arms `treatment`/`control` and that a reader expecting
`intervention` returns nothing. **I had read that comment, and wrote the same bug
into the next gate the same night.**

This is the same shape already logged as *"the rule broken by its own author,
inside its own enforcer"*, and the repetition is the finding. **Knowing a rule
does not apply it. Only a check does** — and a check written by someone who knows
the rule is not exempt, because the knowledge is what makes the author feel
entitled to skip the fixture.

**Practical consequence, and it is cheap:** the FIRST test written for any new
instrument should be its own founding case, and the SECOND should be that case
with the sign reversed. Both were what caught these. A threshold chosen before its
fixture is run is a threshold chosen to pass.

Two of the four were caught only by running the thing against the real corpus
rather than by reading it: the wrong-key read produced ratios of 49.9, 49.9, 49.8,
50.0, 50.1, 49.9, 50.0. **Thirteen independent trials do not analyse exactly half
their enrolment. The signature, not the value, was the tell.**

---

## An alarming inference from a real defect is still an inference

2026-08-18. A filename pattern, `[A-Z0-9_]+`, was found in eight scripts including
the card gate. The defect was real: one page's card had never been compared with
its page, and it published a different measure, value and trial count.

**From that I said every count those eight scripts had produced was suspect. It
was relayed onward as fact. Then it was measured: ONE figure moved, by 7 of 818,
and the move was caused by my own page rebuilds rather than by the bug. The bug's
own effect was 1 trial and 1 page, because only 19 of ~1,500 files carry a
lowercase letter in the stem and only one of those is a review page with a card.**

> **An alarming inference from a real defect spreads faster than the defect,
> because it sounds like diligence.** A sweep that finds a pattern in eight files
> invites the conclusion that eight files' worth of output is wrong. Finding a
> defect and bounding a defect are different pieces of work, and only the second
> one produces a number.

**The rule: never report the SCOPE of a defect until it has been measured
separately from its EXISTENCE.** "Found in eight scripts" and "affects eight
scripts' output" are different claims, and the first does not license the second.

---

## The instruments and the human judgement converged, independently

Worth logging precisely because it is neither a save nor a defect, and this file
records almost nothing else.

Three cardiology topics — APIXABAN_AF, DABIGATRAN_VTE and RIVAROXABAN_ACS — were
withdrawn by hand, on ENDPOINT grounds read from the registry: an efficacy
endpoint pooled with a safety one, four incompatible endpoint types, an undeclared
choice between two primaries.

`count_provenance_gate` was built afterwards, for a completely different defect
class — numerators taken from one outcome and denominators from another — and
knew nothing of those verdicts. Run across the corpus it returned **four FAILs, and
all four sit on those same three topics**: RENAL-AF's numerators are not its
primary's, nor NCT02913326's, nor ATLAS ACS TIMI 46's, and NCT00168805's counts are
that trial's *"Number of Participants With Pulmonary Embolism"*.

**Two independent routes — one human reading registry endpoint definitions, one
machine reconciling counts — reached the same three pages without either informing
the other.** Every one of those withdrawals now rests on two grounds instead of one.

**That is the closest thing to validation this programme has produced.** It does
not prove the method is right; it shows that where it can be checked twice, the
two checks agree. Given how much of this file records instruments that agreed with
nothing, the convergence is worth as much as any single finding in it.

---

## Logged saves — design choices that prevented a failure

- **Asserting an unmade judgement, caught and corrected, 2026-08-18.**
  MAVACAMTEN_OHCM's object claimed `poolable: false`. That asserts *these cannot
  legitimately be pooled* — an assessment that build never made: the topic has one
  trial and publishes no estimate, so the question was never reached. `None` is the
  honest state. **Asserting an unmade judgement is the same defect as a synthesised
  absence reason, and it fails toward confidence** — a reader sees a verdict where
  there was only silence.
- **The harness ceiling refusing a vacuous green, twice, 2026-08-18.** The same
  topic was blocked from pushing because its only executing checks could pass but
  could not FAIL — no displayed pool for `CHK020`, no network for `CHK024`. One
  check ran, it was INVALID, and 100% INVALID is above the 50% ceiling. **The page
  build was reverted rather than forced through.** This is the strongest evidence
  yet that the ceiling rule works: it is the one mechanism here that has refused a
  green produced by measuring nothing, on an artefact where every individual number
  was correct.
- **A page that discloses what it has NOT done, 2026-08-18.** Credit where it is
  due and it is rare: `HFREF_NMA_AUTO_FULL_REVIEW` states on its own face that its
  per-trial integrity gates have **not** been run and that *"absence of findings
  here is absence of testing, not a clean bill"*; that its network fit reproduces
  its anchor **to 8 decimal places in R 4.6.0 / netmeta 3.6.1**; that **no
  inconsistency test is fitted**, with the reason; and that its **AMSTAR-2
  confidence is CRITICALLY LOW**. That is the thing this whole apparatus asks of
  everyone else, done voluntarily by a page nobody was auditing.
- **Naming momentum before it acted, 2026-08-18.** Three cardiology topics had
  been withdrawn in a row when the fourth came up. It was recorded, in advance of
  reading it, that *"after three withdrawals this was the verdict most in need of
  resisting"* — and the topic was then checked in the same order and to the same
  depth as the three before it, and **the pool stood**: estimand identical across
  three registrations, every value the registry's own, the pooled number
  reproducing to four decimals.

  Worth logging because **momentum is a real bias and it is invisible from
  inside**. A lane that has withdrawn three estimates has an implicit model that
  says the fourth is probably wrong too, and that model is never written down and
  never tested. The ledger already says a withdrawal is not the safe default,
  because withdrawing a correct estimate destroys a true finding and publishes the
  destruction as a discovery. **The running score sharpens it: across ten
  cardiology topics the published literature has been implicated in NOTHING.
  Every defect found has been ours.** A lane that keeps finding its own errors is
  working correctly right up until the moment it starts finding errors that are
  not there, and nothing external distinguishes those two states.

We have far more logged failures than saves, which distorts what the file teaches.

- **UNCHECKABLE instead of PASS.** `arm_identity_gate` and `poolability` could
  not read a real v1 object and said so, rather than defaulting to pass. Had they
  passed — the natural way to write a gate that finds nothing to inspect — every
  cardiology topic would have shipped claiming eleven green properties when
  **four of twenty-six** are established by a running check. That one design
  choice is the whole distance between a measurement and a false green.
- **Exit 2 on an unfit registry**, in the imported harness: it refuses to report
  from controls that misbehave.
- **Zero check executions exits 2**, added to that gate: an adapter recognising
  nothing is otherwise indistinguishable from a clean corpus.

## Gates that ignore their target and report globally

`card_alignment_gate` was passed a page and an object and swept the whole index
regardless, returning byte-identical output for two different objects. So
`card_matches_page` **passes globally while being unmeasured per page** — a
property that appears checked at the granularity that does not matter and is
absent at the one that does.

Swept for the class: `staleness_gate` and `pooled_value_gate` also take no target
argument. A gate whose result does not change when its subject changes is not
checking the subject.

Related, same gate: it reports **0.0% drift over 6 comparable cards while 508 of
514 are UNCHECKABLE** — a reassuring headline computed over 1.2% of the corpus.
Not a rate over an empty set, which is what I first reported; a rate over a real
denominator with an enormous unmeasured remainder presented as if it were not
there. **A proportion must carry its comparable fraction inline or refuse to
render.**

---

## The lane that produced this section

Six cardiology topics taken through one protocol: establish trial identity by
registration id, **read every trial's endpoint definition from the registry
before pooling anything**, then let the pool stand or withhold it with its
reason, then reconcile against the published literature with a denominator.

**The headline finding, stated as prominently as the opposite would be: across
six topics the published literature was implicated in NOTHING.** Every defect
found was ours. Twice the literature had visibly done the harder thing — one
Bayesian analysis re-derived three trials' outcomes to match a fourth's and said
so in its abstract; an ablation synthesis pooled the COMPONENTS several trials
share rather than averaging four incompatible composites, which is exactly the
move our own page failed to make.

## The direction of a wrong check decides what it costs

A withdrawal is not the safe default. **Withdrawing a correct estimate destroys a
true finding and publishes the destruction as a discovery** — rigorous-looking
and wrong — so a withdrawal needs the same evidentiary standard as a claim. Six
separate under-reads in one component canon all pushed that way:

| the text | what the reader saw | what it would have argued for |
|---|---|---|
| `CV mortality` | no death component at all | splitting two trials that count the same events |
| `hospitalisation for worsening heart failure` | two components, not one | splitting EMPEROR-Reduced from EMPEROR-Preserved |
| `worsening heart failure requiring unplanned hospitalization` | the same, word order reversed | the same, hours after the first was fixed |
| `cardiovascular (CV) death` | hospitalisation and no death | splitting PARALLEL-HF from three identical trials |
| a bare registry TITLE with the components in the DESCRIPTION | a trial counting **nothing** | a trial that counts nothing disagrees with everything |
| `Total Mortality, Disabling Stroke, Serious Bleeding, or Cardiac Arrest` | *stroke* | the comfortable one: pooling CABANA with a stroke-only trial |

Only the last fails toward comfort. Five failed toward alarm — and were still
dangerous, because the action each argued for was destructive.

**And widening a finder without widening its classifier is not a partial fix.**
The phrase was matched and then silently assigned to no key, which is
indistinguishable from never matching it. Two places, one fact.

## A finding that lives in the artefact dies at the next build

Three instances in one day, and the third was caught mid-flight:

| where the finding lived | what the object held | what a rebuild would do |
|---|---|---|
| ABLATION_AF's withdrawal, on the page | a live pooled point | re-publish it |
| SGLT2_HF's withdrawal, in one paragraph | the withdrawn value, live, printed **six times** against one "withdrawn" | re-publish it |
| ARNI's open question, a hand-edited `<div>` | nothing at all | **delete the finding** |

The third one actually happened. The rebuild emitted a page missing its most
important paragraph, nothing errored, and it was caught only because the new
page's numerals were counted against the served page before pushing. **Compare
the artefact you are about to ship against the one you are replacing, by
content, not by whether the build succeeded.**

## An instrument that cannot vary its input is measuring nothing

The vacuity detector — built to find checks that pass without checking — forced
`stored_scale="natural"` and `back_transform="identity"` on payloads that already
held those values, producing byte-identical "mutants", and recorded the
surviving PASS as proof the check ignored the terms. Seven of nine checks on one
artefact came back INVALID and blocked a push.

**A mutation that changes nothing tests nothing.** The fix is a third state:
UNEXERCISED, distinct from both vacuous and demonstrated. The same shape appears
wherever a probe cannot distinguish "I varied this and nothing happened" from "I
did not vary this".

## Two more of the recurring shapes, in new costumes

- **A join across the wrong grain.** The exporter flattened three *per-outcome*
  facts into one *per-object* triple, so a FAIL paired one estimand's displayed
  value with another estimand's reason for being unpoolable. Both halves true, of
  different things.
- **A vocabulary mismatch at a module boundary.** Objects write `linear`; the
  detector's word is `natural`. Every difference-measure row in the corpus
  produced a FAIL saying it was not on the scale it was already on. Worse on the
  same line: `eff.get("scale") or "log"` **asserted** a scale for objects that
  record none — the one value that makes a difference measure look like a ratio,
  in the exporter whose first rule is never to synthesise a field.

## What a proportion of checks still does not establish

Across seven cardiology objects, 57 of 98 property-checks PASS and **30 are not
established by any running check**. Two are WITHHELD — the property met by
withholding an estimate rather than by agreement, which needed its own verdict
because scoring it FAIL made a page that *found* the problem look identical to
one that pooled straight through.


---

## An object field read as though it were a registry read

Found 2026-08-18 on the flagship. `arni-hfref` recorded ANSWER-HF's endpoint rank
as *"a secondary endpoint; the trial's primary is change in left ventricular
ejection fraction"*. A lane read that field, and the finding travelled onward as
**"verified from the registry word for word: all four identical, two contributing
it as a secondary"** — into a briefing, as established fact.

**The registration refutes it.** NCT04853758 declares twenty outcome measures and
**none** is a first-event union of cardiovascular death and heart-failure
hospitalisation. Only **one** trial of the four contributes it as a secondary.

> **A field in our own object is not a source. It is a claim we made earlier,
> and re-reading it confirms only that we are consistent with ourselves.**

This is the corpus-echo failure in a new costume: previously a gate with corpus
reach handed a lane its own just-written text back as "verification"; here an
object field did the same thing across sessions, and the laundering step — "read
from the registry" — was added by the retelling, not by anyone reading a registry.

**The countermeasure that worked:** the instruction to re-establish the finding
from the registry *rather than trusting the characterisation*. It cost one API
call and overturned the expected answer. **Where a claim's provenance is "an
earlier lane established this", the cheap move is to re-establish it, not to
audit the retelling.**

---

## A screen that produced a spectacular false finding, and the check that stopped it

Written 2026-08-18 to test whether PAGE_MAP's page↔object binding holds. It
reported **0 of 28 pages reproducible** and that the flagship would lose **97.4%**
of its numerals on rebuild.

**Every part of that is an artefact of the instrument.** The screen assumed
`build_app_v2.py` is the whole-page generator. It is not: these pages are
maintained by surgical row-level patches, and ARNI's last commit changed 35 lines
on a 6.17 MB page. The screen was measuring the wrong thing perfectly.

It was caught in the only way this class ever is: **the output contradicted
something already known** — ARNI is live at 6.17 MB, byte-identical to local,
verified twenty minutes earlier. The ledger's existing rule ("read the first
corpus run of any new screen before reporting it") is now **four** instances, and
the fourth was written by someone who had read the rule that morning.

**What survived the correction is smaller and true:** running that builder the
documented way on 5 of 28 objects silently truncates the page. That is queue item
21, and it is a real defect — but it is one fifth the size of what the screen
first said, and about the BUILDER rather than about the pages.

> **A screen's first run measures the screen. Only its second measures the
> corpus.**

---

## Counting at the wrong grain, twice, in the same queue item

Queue item 20 was written as "39 rows", corrected to "55 rows across 22 objects",
and is **77 across 17** when re-derived at the trial-OUTCOME-row grain the item
itself specifies. Both earlier figures counted **trials** on objects where trials
and rows happen to be equal, then carried that unit onto objects where they are
not.

**The correction is not the interesting part; the DIRECTION is.** The enumeration
did not merely undercount — it **omitted whole objects**, and one of them
(`acs-antiplatelet-review`, 4 rows) carries a **live pooled estimate**, the exact
category the item flags as needing topic-depth handling. Another
(`prevnar15-pneumo`, 25 rows) is larger than the entire batch the item scoped.
Meanwhile `iv-iron-hf` is listed as owing 3 and owes 0.

> **A backlog derived once and then quoted is a measurement that decays. Re-derive
> it at the stated grain before working from it — and check what it OMITS, not
> just what it counts wrong.**

A list that is wrong about the items it contains gets audited. A list that is
silently missing items reads as complete, and nothing about working through it
ever reveals the gap.


---

## The orchestrator as a folklore vector — a claim that gained provenance by being retold

Named by Mahmood, 2026-08-18, about his own relay, and it is the sharpest statement
of this mechanism the project has.

The chain, exactly as it ran:

| step | what existed | what it claimed |
|---|---|---|
| the object | `endpoint_rank_in_its_own_trial: "a secondary endpoint; the trial's primary is change in left ventricular ejection fraction"` | an assertion we wrote |
| a lane read it | the same sentence | a finding |
| the relay | the same sentence | **"an earlier lane verified all four endpoint definitions from the registry word for word and found them identical"** |

**Nobody read a registry at any step.** The registration says ANSWER-HF declares
twenty outcome measures and none is the pooled endpoint, and that only ONE of the
four trials contributes it as a secondary. Both halves of the relayed sentence are
false, and the phrase that made it authoritative — *"from the registry, word for
word"* — was **added by the retelling**.

> **A claim gains authority as it passes through a summary, and nobody re-checks a
> fact that arrives already attributed.**

**This is not a wrong document. It is a wrong PROVENANCE**, which is worse, because
every downstream reader's decision about whether to re-check is made on the
provenance and not on the claim. A sentence labelled "our object says" invites a
check. The identical sentence labelled "read from the registry" forecloses one.

**Same species as the PARACHUTE/ANSWER conflation, one level up.** There, two trials'
properties merged inside one document. Here, an assertion and its verification merged
inside one summary. Both are joins across the wrong grain; this one joins a claim to
a source that never carried it.

**THE RULE, and it is the whole entry:**

> **When relaying a lane's finding, carry the SOURCE IT NAMES, not the CONFIDENCE IT
> CARRIES.**

"The object records X" and "the registry says X" are different claims and must
survive as different sentences all the way down the chain. If a summary cannot say
which one it is holding, it must say *that* rather than pick the stronger.

**What made it recoverable** was an instruction to re-establish the finding from the
registry *rather than* to audit the characterisation. That cost one API call. Auditing
the retelling would have cost more and found nothing — every document in the chain was
internally consistent, because they were all the same sentence.

Related: the corpus-echo failures, where an adversary gate returned our own text as a
verification. Same mechanism, different carrier: there the loop ran through a tool,
here through a summary, and the summary is faster.


---

## A content-preserving check suite does not see an ENCODING rewrite

Found 2026-08-18, in this lane's own work, one commit after it shipped.

Two ~900 KB pages needed a 1.2 KB disclosure banner each. The patch read them with
`io.open(p, encoding="utf-8")` and wrote them back. `core.autocrlf` is **false** in
this repository, so the tree stores **CRLF** — and a text-mode round-trip silently
rewrote 6,073 and 5,958 line endings to LF. **12,031 insertions and 12,031 deletions
for a 1.2 KB change.**

**Every check written for that patch passed**, and they were not weak checks:

| check | verdict | why it could not see this |
|---|---|---|
| div balance before/after | PASS | divs are unaffected by line endings |
| `</script>` count | PASS | so are script tags |
| numerals lost | 0 | so are numerals |
| byte growth == text added | PASS *(in text mode)* | the read had already normalised |
| anchor matched exactly once | PASS | true, and irrelevant |

> **The checks all asked about CONTENT. The damage was to ENCODING, and content
> checks are blind to it by construction.**

It was caught by `git commit`'s own line count — 12,031 for a one-paragraph edit is
absurd on its face — and by nothing else. Had the files been LF already, or smaller,
nothing would have flagged it.

**The narrow, transferable rule** (the ledger already carries the broad one, "revert
rather than untangle when >50% of a diff is damage"):

> **Never text-mode round-trip a file you did not author.** Read bytes, replace
> bytes, write bytes; then assert that every byte outside the replaced span is
> identical and that the CRLF count is unchanged. Those two assertions catch what
> the entire content suite cannot.

Redone that way, the same edit produced **1 insertion and 1 deletion per file**.

**And the deeper point, which is the one this file exists for:** a check suite that
grows by accretion tends to accumulate checks of ONE KIND — here, five checks that
were all really the same check. The question to ask of any suite is not "how many
checks" but **"what class of damage is none of them looking at"**. Five content
checks provide no redundancy against an encoding fault; they provide one check,
run five times.


---

## Count KINDS of check, not checks — a suite grows by accretion into one check run N times

Mahmood's generalisation of the CRLF fault, 2026-08-18, and it reframes every
coverage number this project has quoted.

Five checks stood in front of that edit — div balance, script-tag count,
numerals-lost, byte growth, anchor-matched-once. **All five passed. All five were
the same check.** Each asks a question about CONTENT; the damage was to ENCODING.

> **We count checks as if they were independent. Five content comparisons are ONE
> check applied five times, and a defect orthogonal to content passes all of them
> by construction.**
>
> **The honest coverage question is not how many checks a page passes. It is how
> many independent KINDS — and which kinds nothing is looking at.**

This is the same shape as the ledger's older entry on a proportion of checks not
establishing what it appears to: there the problem was checks that did not run,
here it is checks that all run and all look the same way.

### The classification, measured 2026-08-18 — `scripts/gate_kinds.py`

**31 gates. Seven kinds. Three kinds with no gate at all.**

| kind | n | what it actually inspects |
|---|---|---|
| EXTERNAL AGREEMENT | 11 | ours against a source outside the repo — a registry, an article |
| INTERNAL AGREEMENT | 7 | two of our own surfaces compared with each other |
| PRESENCE / DURABILITY | 4 | does the thing exist, is it tracked, is it current |
| MARKUP / STRUCTURE | 3 | is the artefact well formed as a document |
| ARITHMETIC | 2 | do the numbers reconcile |
| TOPICALITY | 2 | is this about the right subject at all |
| SELF-CHECK | 2 | can the checks themselves fail, and did they run |

**And the part that matters — the empty rows. None of these is hypothetical; each
has already cost something this week:**

| uncovered kind | what it would inspect | what it already cost |
|---|---|---|
| **ENCODING / BYTE INTEGRITY** | line endings, BOM, charset — anything true of the FILE rather than of its text | 12,031 CRLF endings rewritten on two live pages; five content checks passed it; caught by `git commit`'s line count alone |
| **DELIVERY / LIVENESS** | does the far side actually SERVE the bytes that were pushed | `ssot/` returned 404 for weeks while every page promised the reader a canonical object. "Verify live" is a manual step, and on an object-only change it had nothing to check — so it passed **vacuously** every previous time |
| **DELTA / IDEMPOTENCY** | did this patch change what it meant to, and only that | the ledger's own entry: an append-instead-of-set produced a well-formed object every gate passed. Only a diff against the EXPECTED change reveals it, and no gate computes one |

**A page passing all 31 gates is unchecked in all three.** That sentence is the
value of the exercise, and it was not available before the kinds were named.

**A trap worth keeping**, found while doing this: `ls scripts/*gate*.py` returns
**52** files, of which **21 are `propagate_*`** — the glob matches "propa-**gate**".
Any count quoted from that glob is wrong by two thirds. `gate_kinds.py` filters
explicitly and derives the list from disk so the number cannot decay.

**Why the classification is a script and not a table in this file:** the assignment
of a gate to a kind is a judgement and belongs in prose where it can be argued with;
the LIST of gates is a fact and must be re-derived, or it becomes another memory
count of the sort this project has already had to reconcile twice.


---

## A true rule, correctly applied, producing a FALSE ANNOUNCEMENT

Found 2026-08-18 while applying the estimator decision. The rule was right (REML, per
Handbook 6.5 sec 10.10.4.4). The pools were in scope. The sweep would still have lied.

Five pools showed a shift when recomputed under REML. **On four of them tau-squared is
ZERO under both estimators.** With tau-squared identical the two estimators produce the
same pooled value *by construction*, so those shifts (0.005-0.019%) are recomputation
noise from stored, rounded `log_point` and `log_se` -- not an effect of the estimator.

Applying them would have overwritten four published numbers with noise **and announced
each one as an estimator change it was not**. The `display_change_announced` block would
have named DerSimonian-Laird-to-REML as the cause of a movement the estimator did not
cause.

> **An announcement must name the reason the value moved, not merely the process that
> moved it.**

This is a new shape for this file. Every earlier entry is a wrong rule, a wrong scope,
or a check that could not fail. Here the rule is right, the scope is right, the check
runs -- and the *attribution* is false. A reader told "we changed estimator and the
number moved" would draw a conclusion about between-study heterogeneity that the data
does not support.

**And the test is constructible, not a judgement call:** tau-squared identical under
both estimators means the estimator cannot be the cause. The guard is three lines and
prints the four excluded pools on every run.

**The general form worth carrying:** whenever a sweep applies one rule to many objects,
ask of each object not "is this in scope" but **"is the rule the REASON this one
changes"**. Scope membership and causal attribution are different questions, and only
the second is what an announcement asserts.


---

## The defect is never in the numbers — it is in what the numbers are about

Four topics closed on 2026-08-18, and **not one of them could have been questioned by
any consistency check this project has or could build.**

| topic | what agrees | what does not |
|---|---|---|
| RIOCIGUAT_PAH | same drug, same placebo, same 6MWD primary | **PAH against CTEPH** — two diseases |
| EDOXABAN_VTE | same drug, both VTE, both count VTE events | **prophylaxis against treatment**, adults against children |
| MIPOMERSEN_HOFH | same drug, same placebo, same LDL-C primary | **one arm-vs-itself extension**; HoFH against statin-intolerant |
| OLMESARTAN_HTN | same class, same BP primary, three real trials | **the titled drug is the comparator in all three** |

**Every internal check passes on all four.** The numbers reconcile, the surfaces agree,
the identifiers resolve, the endpoints match. Arithmetic cannot reach any of it, because
nothing is wrong with the arithmetic.

> **These are errors of REFERENCE, not of calculation. Only reading the registration
> finds them, and only the registration can.**

Four instances in one round, in four different shapes, is the strongest argument the
method has produced for itself. It is also the sharpest statement of what the gate set
cannot do: **31 gates across 7 kinds, and the kind that catches these is a human reading
a registration.** The `subject_is_experimental` gate built the same day automates exactly
one of the four shapes — the OLMESARTAN one — and the other three remain judgement.

### And it reframes the published-meta comparison

If a pool can be wrong in a way no arithmetic reveals, **a published synthesis making the
same combination would look impeccable too.** Peer review does not recompute; it reads
prose that describes the pool in the same terms the pool describes itself.

**So where a published review pools the same trials as one of these four, that is now the
comparison that matters most** — not as a check on our arithmetic, which agrees, but as
evidence about whether the field has made the same reference error. **This is owed work
and is not done:** none of the four has been checked against the published literature for
a synthesis combining the same trials.


---

## A rebuild destroys exactly the material that makes a page checkable

Found 2026-08-18. A rebuild of `bococizumab-lipid-review` wrote **152 lines over 1,626**.
It destroyed the withdrawn `primary` outcome **with its reason**, the sources block, the
screening record and the risk-of-bias verdict — and produced a **perfectly valid object
that every gate would have passed**, because everything it kept was internally
consistent.

> **The material a rebuild destroys is exactly the material that makes a page checkable.**
> A withdrawal reason, a source list, a RoB verdict and a screening record are not
> outputs — they are the evidence that the outputs were earned. An object stripped of
> them still validates.

Same family as the idempotency failure already in this file, and the same defence:
**validity and delta are different questions**, and every gate here asks the first one.
It was caught by reading the diff stat — 1,626 deletions for a change that should only
have added — and by nothing else.

**It is now mechanical rather than remembered.** `scripts/rebuild_guard.py`: a write that
removes more lines than it adds **refuses by default**, and an override must name its
reason out loud. Selftest carries the failing input — the halving case, which is the
bococizumab shape exactly.

**What the guard does NOT do, written in advance:** it is a line count, not a reading. A
patch that adds a hundred lines and quietly changes one value passes it, and a genuine
consolidation trips it — which is intended, so that the person consolidating says so.

---

## An identifier is not noise or signal — it is noise or signal **per topic**

`NCT01035255` was on a global "shared runtime residue" list, because it appears on page
after page of unrelated topics as build contamination. Two screens excluded it by name
everywhere.

**On a sacubitril page it is PARADIGM-HF — the trial the page is about.**

So both sacubitril pages, and `HFREF_NMA`, were reported as **"seed no registration at
all"** when each seeds exactly one, and it is the right one. I relayed that to Mahmood as
an alarming defect. It was an artefact of my own exclusion list.

> **A global denylist of identifiers cannot be right, because the same id is
> contamination in one context and the subject in another. Residue must be judged per
> topic.**

**Blast radius, measured rather than estimated: 3 of the cardiology pages** seed a residue
id — `SACUBITRIL_HEARTFAIL`, `SACUBITRIL_VALSARTAN_HF`, `HFREF_NMA` — and on all three
`NCT01035255` is plausibly genuine, because all three are heart-failure topics and
PARADIGM-HF is a heart-failure trial. **Every count derived from that list is suspect
until the exclusion is made conditional**, and the two "unidentifiable" verdicts are
withdrawn.


---

## A commit message is authored; a diff is produced. When they disagree, the message is read

Found 2026-08-18, in this lane's own work, one commit after it happened.

A chained command ran a Python script to write findings into two documents and then `git
commit` in the same shell. **The Python died on a syntax error. The git command ran
anyway.** The commit shipped a script alone — and its message set out the completed
cardiology numbers, the under-counting correction and the provenance labelling, **none of
which the diff contained.**

**This is not the "did it land where it has to be" shape already in this file**, though it
is adjacent. Those four were: the action succeeded, reported success, and did not take
effect. Here the action **partly** succeeded — and the discrepancy is between two records
of it that are produced by different mechanisms:

> **A commit message is AUTHORED. A diff is PRODUCED.**
> **The message is the one that gets read. The diff is the one that is true.**

Nothing cross-checks them. Every gate in this repository reads files; none reads what a
commit claimed about them. A reader — including a future lane — takes the message as the
record, and here the message described a state of the repository that did not exist.

**The rule, and it is free:** **never let a commit message state a finding the diff does
not contain**, and **check with `git show --stat` before moving on** — one file, 147
insertions, no document, which is what caught it.

**And the narrower lesson underneath:** a `&&` chain that ends in `git commit` will commit
whatever state exists when the earlier step fails in a way the shell does not treat as
fatal. Generating content and recording it should not share a command.


---

## The guard existed, and I wrote past it

Found 2026-08-18, twenty minutes after the guard was committed.

`scripts/rebuild_guard.py` was written *the previous day*, for exactly this: a rebuild
that writes a small object over a large one and destroys the material that makes the page
checkable. Its selftest carries the failing input. It works.

**Then a batch closer wrote a 203-line verdict object over `prevnar15-pneumo.json`'s
2,422 lines**, destroying the 25 registry-read endpoint-definition rows and the four
`poolable_reason` blocks written *earlier the same day* — and the guard did not fire,
**because the script called `io.open(...).write()` directly instead of `guard_write()`.**

> **A guard that must be remembered is not a guard.** It is a note with a selftest.

The bococizumab instance was caught by reading a diff stat. This one was caught the same
way — `git show --stat` showing 2,434 deletions on a commit that should only have added —
which means the *detection* is reliable and the *prevention* is not. **The detection is
a habit; the prevention is a function call, and only one of them is enforceable.**

**What would actually close it:** the guard cannot be opt-in. Either every object write in
this repository goes through one helper, or a pre-commit check refuses a commit whose
staged diff net-deletes from `ssot/*.json` without an explicit marker. **Neither exists
yet, and until one does this will recur** — it has now happened twice in two days, both
times to an object holding a day's registry reading.

**Fixed forward rather than reverted**, because the verdict was correct and only the write
was wrong: the prior object was restored from `HEAD~1` and the verdict MERGED into it as
its own block, so the page now carries both of its independent defects — the four
injection-site outcomes that are classes inside one registered composite, and the eight
registrations that declare no clinical endpoint at any rank.

---

## Shared code makes a wrong rule VISIBLE; hand copies make it invisible and unanimous (2026-08-18)

`scripts/ctg_binary_pool.py` was written on the third occurrence of the same pooling
arithmetic. **The line-count saving is not the point and should not be cited as the
reason.** Writing the rule down in one place is what exposed that the rule was wrong.

The heterogeneity direction test was given as: *when I-squared is high, check whether the
intervals agree in direction before choosing the sentence.* I implemented it
**unconditionally**. Applied that way it labelled a k=3 pool at **I-squared = 0%** a
"substantive disagreement" — purely because one interval was wide.

**Note the direction of that failure. It manufactured doubt about a sound result.** That
is the mirror of Class 2 in `TAXONOMY-PUBLISHED-SYNTHESIS-ERRORS.md`, and for this
programme it is **the more expensive error**: caveating or withdrawing a correct finding is
precisely the thing we have said throughout is not safe, because it publishes destruction
as rigour.

**Twelve hand-written copies would have carried the same error into twelve topics with
nothing to compare them against.** Each would have looked locally reasonable. The error
became visible the moment the rule had to be stated once, for all cases, in a form that
could be run against three known topics and checked.

**How to apply:** when the same analytical rule is about to be written a third time, the
reason to extract it is not economy — it is that a rule with one implementation can be
tested, and a rule with N implementations can only be trusted. Extract it, then run it
against every case already decided by hand and confirm the answers match.

---

## A rule stated without its precondition will be applied without it (2026-08-18)

The gate — *when I-squared is high* — was present in the instruction and **implicit**. It
was not carried into the implementation. The error was in the statement of the rule, not
in the coding of it, and it is worth separating those because the fix is different:
tightening review of the implementation would not have caught this.

Sits directly beside **"a guard that must be remembered is not a guard"**. Same family:
**a condition that lives only in the reader's head is not a condition.** If a rule has a
precondition, the precondition belongs in the rule's text, in the function's code, and in
the test — not in the shared understanding of the two people who discussed it.

**How to apply:** when writing down any conditional rule, state the condition first and
the action second, and give the rule a name that includes the condition. Then write the
test for the case where the condition is FALSE, before the case where it is true.

---

## `git add -A` in a shared tree: the message and the diff disagree (2026-08-18)

Commit `8bd645e8d` carried a message describing four topic builds and a diff containing
**249 files of another session's untracked work** — a DOI-resolution script, a MetaGuard
corpus, manifests. Nothing was lost; every file was an addition. **But the message and the
diff described different things**, which is the same class as the earlier
commit-without-content, where a `&&` chain let `git commit` run after the Python step died
and the message described findings the diff lacked.

**Twice now, from the same underlying cause: the commit was assembled by a command that
did not name what it was committing.**

Not pushed, so it was split: `3a7c02855` holds the topic work staged by path, and
`59363e766` holds the foreign files with a message saying plainly that they are not mine,
that I did not review them, and that they are committed rather than deleted because
deleting another session's work is not mine to do.

**The rule: stage by path, never `-A`, in a shared tree.** If `git status` is too noisy to
stage by path, that is the signal to fix `.gitignore` first — not to reach for `-A`, which
is how the noise becomes permanent.

---

## The classifier searched the whole file and I nearly shipped the number (2026-08-18)

`scripts/pending_vs_impossible.py` first reported **31 topics PENDING**. A spot-check of
five before reporting found `acs-antiplatelet-review` and `colchicine-cvd-review` in that
bucket — both of which carry recorded verdicts saying plainly that their trials answer
different questions. **They are IMPOSSIBLE, not PENDING.**

Cause: the data-gap regex was run against the **entire raw object text**, so any topic that
merely *mentioned* absent results — including inside a "what this does not establish" note
— matched. The fix reads only `topic_state`, `which_limb_fails` and `poolable_reason`.

**This is the third instrument artefact in this programme**, after the PAGE_MAP screen that
claimed "0 of 28 reproducible" and the unregistered-endpoint hand count that was 4–8× low.
All three had the same shape: **a measurement whose failure mode is to look like a finding.**

**How to apply:** before reporting any number a new script produces, hand-check the three or
four cases you already know the answer to. Not a sample — the ones you can independently
verify. A screen that agrees with you on known cases has earned the unknown ones; a screen
that has never been checked against a known answer has produced a number, not a finding.

---

## The selection effect on the MEASURING side (2026-08-18)

Three instrument artefacts in this programme: the PAGE_MAP screen claiming **0 of 28
reproducible**, the Class 4 screen showing **18 flags**, the pending classifier reporting
**31 pending**. All three were caught. **But note what they have in common: every one of
them looked like a finding.**

A measurement error that produced a boring result — "27 of 28 reproducible", "1 flag", "2
pending" — would have been shrugged at and investigated later, or never. **These three
nearly shipped precisely because they were interesting.** The same selection effect that
makes a striking trial result more likely to be published operates on our own instruments,
and in the same direction.

**How to apply:** an unexpectedly strong result from a NEW measurement is not evidence that
the measurement works. It is the case where checking is most urgent, because the
interestingness that makes it worth reporting is also what suppresses the instinct to
verify. Hand-check the cases you already know the answer to — **not a sample, the ones you
can independently verify** — and do it BEFORE the number is in a sentence.
