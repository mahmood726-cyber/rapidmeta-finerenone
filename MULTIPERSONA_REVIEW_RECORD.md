# Multi-persona review — running record

Mahmood, on the live SGLT2_HF page: *"this paper is now not that bad but needs mutlipersoan
reviews to be better."* First positive verdict of the day. This is the record of what each
round found and what changed, kept so that **when a round stops finding things we can tell
success from a blunt instrument** — the difference matters and only a record shows it.

**Method.** Five distinct roles, not one question asked five times. Each persona receives TWO
documents labelled only A and B, told one may be published and one may not, without being
told which. One is our page; the other is **Zelniker, *Lancet* 2019** — a published SGLT2
meta-analysis. Document order alternates by persona so "always prefers A" cannot sweep.
Personas rotate model family between rounds. Payloads are verified before any verdict is
believed.

---

## Round 1 — SGLT2_HF_REVIEW.html, 2026-08-24

Payload: our page 5,194 words, anchor 393 words. Both verified.

| Persona | Family | Ours was | Verdict |
|---|---|---|---|
| student | google | A | **ours decisively better** |
| sceptic | google | A | **ours decisively better** |
| methodologist | google | A | **ours decisively better** |
| specialist | google | A | comparator decisively better |
| editor | google | A | **ours DESK-REJECTED**, comparator sent for review |

**3–2 to our page against a published Lancet meta-analysis** — and, more usefully, the two
dissents are about completely different things.

### On the acceptance test Mahmood set, our page beat the published paper

The student persona, asked whether they could improve the document without being misled:

> **Ours:** *"Yes. It is impossible to be misled by Document A because it aggressively
> exposes its own errors and limitations."* … *"What could you check for yourself?
> **Everything.**"* … *"Where would you make a mistake because the document let you?
> **Nowhere.**"* … *"A confident sentence over missing data: **There are none to quote.**"*
>
> **Zelniker:** *"No. The document presents a flawless summary that completely hides any
> underlying heterogeneity, missing data, or methodological friction."* … *"What could you
> check for yourself? **Nothing.** The document does not name a single trial, provides zero
> identifiers, and gives no source data."*

The sceptic found four attacks on our page and **all four were already answered on the
page**; four attacks on the published paper, **none answered**.

### The two dissents, which are the actionable half

**EDITOR — DESK-REJECT for unreadability.** The content that convinces the sceptic is
rendered in a form that stops an editor reading it:

> *"it is fragmented by constant interruptions like 'Sources for this section (12)' and
> completely unreadable strings such as
> `results.by_outcome.harmonised_cvdeath_or_hhf.POOL_FINDINGS_2026_08_21`"*
>
> *"burying the reader in bizarre text like `k_cascade.k_unscreened_remainder` and irrelevant
> defensive claims such as 'A script that reads this object and reports that this object is
> consistent has confirmed consistency and nothing else'"*
>
> *"jarring, conversational meta-commentary such as 'The original withdrawal was
> disproportionate and this page says so.'"*

The same paper was **sent for peer review** in the comparator's form. So this is a finding
about presentation, not about evidence.

**SPECIALIST — our methodological strictness is clinically wrong.** This is the most
important finding of the round because it challenges a design principle rather than a
rendering:

> *"it refuses to pool all four heart failure trials … 'Two trials count an event class the
> other two do not'. **This is clinically false.** An 'urgent heart-failure visit' requiring
> intravenous therapy is functionally and clinically synonymous with an HF hospitalisation;
> they represent the exact same worsening heart failure pathophysiology."*
>
> *"it excludes the landmark DELIVER trial … 'A k=3 pool we can fully vouch for beats a k=4
> with one input we cannot'. **This is a catastrophic omission.** Throwing out a pivotal
> 6,263-patient trial simply because its first-event two-component outcome is reported in the
> peer-reviewed publication rather than the registry artificially shrinks the evidence base."*

**This one is not ours to fix unilaterally.** It is a direct clinical challenge to the
registry-first rule and to the endpoint-identity rule, both of which were adopted
deliberately. It goes to Mahmood with the argument on both sides.

### What round 1 says overall

The evidence and its traceability win; the presentation loses. The *same property* —
exhaustive self-disclosure, every claim carrying its field path — is what makes the sceptic
and the student trust the page and what makes the editor refuse to read it. That is a
solvable tension: provenance in reader language rather than dotted identifiers.

### Changes made in response

*(none yet — round 1 findings are recorded here before anything is changed, so that round 2
measures the change rather than the enthusiasm for it)*

---

## Harness defects found while building it

Four transport failures, none of which became a false verdict, because each layer declined to
guess rather than returning something plausible:

1. **Windows argv limit.** `agy --print <41,594 chars>` → "The filename or extension is too
   long". The obvious fix — shorten the payload — was the wrong one: truncating a manuscript
   to fit a CLI limit produces verdicts about a document no reader ever sees. Measured first
   (only 2% of the page is provenance apparatus, so there was nothing to trim a reader does
   not read), then fixed by writing the prompt to the session directory and having Gemini
   read it.
2. **Laptop SSH ceiling.** The Codex wrapper failed at 41K with `ssh transport failed
   (rc=255)`; earlier ~17K panels went through. It failed *honestly* — non-zero and empty
   rather than a truncated prompt's answer — so the harness retried three times and recorded
   the persona as MISSING, not as a verdict. Routed to local `codex exec`, which reads stdin.
3. **`codex` invisible to CreateProcess.** Bare `"codex"` raised WinError 2; the shell finds
   it via PATHEXT, `subprocess` does not. Resolved with `shutil.which`.
4. **`only=` reindexed the personas**, so re-running one persona alone changed which family
   it went to. A rotation that changes when you re-run part of a round is not a rotation.
   Fixed to index from the full list.

And one in the verifier itself: it refused SGLT2_HF on *"an element id leaked into the
text"*, having found the page's own provenance list — a deliberate, reader-facing feature.
**The check written to stop me trusting broken payloads refused a good one on its first run.**
It cost a re-run rather than a false finding, because it fails closed.
