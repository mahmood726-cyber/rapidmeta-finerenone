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
