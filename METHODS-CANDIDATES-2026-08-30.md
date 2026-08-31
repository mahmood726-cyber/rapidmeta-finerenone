# Candidate advanced methods — with validation evidence and declared regression criteria

**Nothing here is adopted.** This is the list, the evidence that each was validated, the
conditions it was validated *under*, and what would count as a regression for each — declared
before any of them is run.

**Every source below was retrieved and read today via Europe PMC**, which is free and
reproducible by a reader anywhere. No claim in this document rests on recall.

---

## ⛔ THE FINDING THAT COMES BEFORE THE LIST

**The methods literature has already answered our specific question, and the answer is
uncomfortable.** Two independent simulation studies say that at **k = 2** — which is
dapivirine — no method has good properties:

> **Gonnermann et al 2017**, *Biometrical Journal*, PMID 27754556, PMC5516158 —
> *"Meta-analysis of two studies in the presence of heterogeneity with applications in rare
> diseases"*. Verbatim: **"Whereas the standard method based on normal quantiles has poor
> coverage, the HKSJ and mKH generally lead to very long, and therefore inconclusive,
> confidence intervals."**

> **Beta-binomial comparison, 2022**, *BMC Medical Research Methodology*, PMID 36514000,
> PMC9745934. Verbatim: **"No method performed well in scenarios with only 2 studies in the
> random effects scenario. In scenarios with 3 or 4 studies, most methods satisfied the
> nominal coverage probability."**

⇒ **AT k = 2 THE CHOICE IS NOT BETWEEN A GOOD METHOD AND A BETTER ONE. It is between an
interval with poor coverage and an interval so wide it is inconclusive.** Adopting a novel
estimator here to escape that trade-off would be buying complexity with no validated gain —
a regression under rule 4 even if the point estimate looked nicer.

⭐ **AND IT BEARS DIRECTLY ON OUR ONE DISPUTED GRADE LEVEL.** The imprecision downgrade that
separates us from Cochrane's MODERATE turns on how to read a Hartung–Knapp interval of
0.1725 to 2.865 at k = 2. Gonnermann says that width is **the expected behaviour of the
method at this k, not a discovery about this evidence**. That is evidence for the reading our
superseded ledger took — *uninformative in either direction* — and against the engine's
reading that the two intervals disagreeing is itself evidence of imprecision. ⚠️ It does not
settle it: "inconclusive" is arguably exactly what imprecision means. But it moves the
dispute from opinion to citation, which is where it should have been.

---

## 1. ICEMAN — credibility of the age-interaction claim ⭐ HIGHEST PRIORITY

**What it is.** Instrument for assessing the Credibility of Effect Modification Analyses.
**Schandelmaier et al 2020**, *CMAJ*, PMID 32778601, PMC7829020. **8 core questions for
meta-analyses**, 4 response options each, plus a credibility rating on a visual analogue
scale from very low to high, with a manual giving rationales and worked examples.

**Why it is first.** Our strongest clinical claim — the one now carrying a whole GRADE
domain — is that ASPIRE's treatment-by-age interaction is credible evidence of effect
modification. We currently assert that in prose. ICEMAN turns it into a scored, citable
assessment against 8 pre-specified questions.

⚠️ **HOW IT WAS VALIDATED, STATED HONESTLY: IT IS A CONSENSUS INSTRUMENT, NOT A SIMULATED
ESTIMATOR.** It was developed by a systematic survey of the literature, an expert consensus
study, and refinement against feedback from trial investigators, review authors and editors,
then tested by 17 potential users for usability. **There is no simulation study establishing
its operating characteristics, because it is not that kind of object.** Rule 1 asks for the
study that established a method's properties; for ICEMAN the honest answer is that its
warrant is consensus and use, not coverage probability. That is a real limitation and it
should not be dressed up as more.

**What would count as regression:**
- ⛔ **If it scores our interaction as MORE credible than our prose currently claims and we
  adopt the higher score, that is a regression, not an improvement** — an instrument used
  only when it flatters is not an instrument.
- If applying it requires judgements we cannot source (was the interaction pre-specified? how
  many were tested?) and we guess at them rather than refusing, the score is manufactured.
- If it replaces the quoted evidence rather than sitting beside it.

**Reproducible by a reader?** Yes — the instrument and manual are published; PMC7829020 is an
author manuscript, free to read.

**Known answer we can check it against:** ASPIRE's interaction is **post hoc** — the paper
says so ("In a post hoc analysis…") — and post-hoc status is one of the things ICEMAN scores
down. So a correct application should return a **lower** credibility than our prose implies,
not a higher one. **That is the detection arm: if ICEMAN comes back saying our claim is
highly credible, suspect the application before believing the result.**

---

## 2. Modified Knapp–Hartung (mKH) — alongside HKSJ

**Röver et al 2015**, *BMC Medical Research Methodology*, PMID 26573817, PMC4647507 —
*"Hartung-Knapp-Sidik-Jonkman approach and its modification for random-effects meta-analysis
with few studies"*.

**Validated under:** a simulation study explicitly focused on **"the common case of
meta-analysis based on only a few studies"**. Its stated conclusion: **"Use of the modified
mKH procedure is recommended, especially when only a few studies contribute to the
meta-analysis and the involved studies' precisions (standard errors) vary."**

⭐ **That condition is met here and it is not a stretch.** Our two trials differ in size
(1,959 against 2,629) and in allocation ratio (2:1 against 1:1), so their standard errors
genuinely vary — which is the exact circumstance the paper singles out.

**What would count as regression:**
- ⛔ **A NARROWER interval is not automatically an improvement.** mKH modifies HKSJ to avoid
  intervals *shorter* than the fixed-effect one; if it narrows ours, the question is whether
  it added information or removed a caution. Widening is not regression — HKSJ widens and is
  an improvement because the incumbent was overconfident.
- If it changes the GRADE letter and we cannot state which property of the data drove the
  change.
- If it silently replaces the DerSimonian–Laird interval on the page.

**Run alongside:** DL, HKSJ and mKH all published together. **Jackson et al 2017**,
*Statistics in Medicine*, PMID 28748567, PMC5628734, recommends exactly this in its own
words: **"the results from more conventional approaches should be used as sensitivity
analyses when using the modified method."** Our rule 2 is that paper's recommendation.

---

## 3. Bayesian random-effects with an empirical heterogeneity prior — CANDIDATE, WITH A CAVEAT WE SHOULD PROBABLY REFUSE ON

**Gonnermann 2017** (above) assesses Bayesian random-effects with priors for τ² as one of its
alternatives at k = 2. **A 2024 *Research Synthesis Methods* paper**, PMID 38152969, develops
**empirical heterogeneity priors** for exactly this setting.

**Why it is attractive at k = 2:** τ² is unestimable from two studies. A prior supplies the
information the data cannot, which is the only honest way to get a usable interval.

⛔ **AND WHY IT MAY FAIL RULE 4 REGARDLESS OF PERFORMANCE.** The estimate then depends on a
prior the reader must accept. A reader in Laos with free tools can reproduce a DL or HKSJ
interval with a calculator; reproducing a posterior requires accepting our prior, our
parameterisation and our sampler. **We win on verifiability, and a number a reader cannot
check costs us more than a slightly worse one they can.** If we run it at all, it should be
as a **stated sensitivity analysis with the prior named and justified**, never as the
headline estimate.

**What would count as regression:** any presentation in which the prior is not on the page;
any narrowing of the interval attributable to the prior rather than to the data; any use that
makes the estimate unreproducible with free tools.

---

## 4. Beta-binomial / GLMM for sparse binary outcomes — **RECOMMEND NOT PURSUING FOR THIS RESULT**

**PMID 36514000, PMC9745934** (2022) compared several beta-binomial models against standard
approaches **for meta-analyses with very few studies**. Its result at our k is explicit:
**"No method performed well in scenarios with only 2 studies in the random effects
scenario."**

⇒ **The validated evidence says this class does not rescue k = 2.** Adopting it here would add
a model a reader cannot check in exchange for properties the literature says are not there.
It remains a genuine candidate for corpus results with **k ≥ 3–4**, where the same paper
found most methods achieved nominal coverage — and 155 of our 157 results are not dapivirine.

---

## 5. Prediction intervals at k = 2 — **ALREADY RULED ON, AND THE RULING SHOULD STAND**

**IntHout et al 2016**, *BMJ Open*, PMID 27406637, PMC4947751 — *"Plea for routinely
presenting prediction intervals in meta-analysis"* — argues for routine presentation.

⚠️ **But our house rule already says a prediction interval is undefined for k < 2 and unstable
at k = 2**, and Gonnermann's finding that HKSJ intervals at k = 2 are "very long, and
therefore inconclusive" applies with more force to a prediction interval, which is wider
still. **A prediction interval here would be a number so wide it excludes nothing, printed
with the authority of a statistic.** That is the definition of hiding a limitation behind a
method.

**What would count as regression:** printing one at all at k = 2 without the width stated as
uninformative.

---

## What I recommend running first, and why only one

**ICEMAN, on the ASPIRE age interaction.** It is the only candidate that addresses a claim we
are already making rather than a number we are already reporting; it is free and reproducible;
it has a known-answer check built in (post-hoc status should pull the score DOWN); and it
touches the evidence base for a live GRADE domain rather than the arithmetic of an estimate.

**Second, mKH alongside DL and HKSJ** — because its validation conditions match ours exactly,
and because the paper that criticises the method family also tells us to publish the
conventional result beside it.

**Everything else waits.** At k = 2 the literature's own answer is that no estimator performs
well, and the honest response to that is to say so on the page — not to keep trying methods
until one produces a narrower interval.
