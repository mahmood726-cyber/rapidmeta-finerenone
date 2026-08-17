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

## Logged saves — design choices that prevented a failure

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
