# The parked decisions, settled against the Cochrane Handbook

**Handbook version verified at apply-time, not cited from memory:**
**Cochrane Handbook for Systematic Reviews of Interventions, Version 6.5, 2024**,
confirmed live on 2026-08-18 at
`https://www.cochrane.org/authors/handbooks-and-manuals/handbook/current`.
Every section number below was read from the current chapter text on that date.
The Handbook moved host during this check — `training.cochrane.org/handbook/current`
now 301-redirects to `cochrane.org/authors/handbooks-and-manuals/handbook/current`
— which is itself a reason not to quote a remembered section number.

**Three of the four are DECIDED. One is genuinely a choice and is brought back with
its consequences.**

---

## 1. Estimator and interval method — **DECIDED: REML corpus-wide**

**§10.10.4.4**, verbatim: *"Until 2024, only the DerSimonian and Laird 'moment-based'
method was implemented in RevMan. As of 2024, a restricted maximum likelihood (REML)
method is also available."* And: *"In RevMan, the default option for estimating the
between-study variance is REML, while the DerSimonian and Laird moment-based method
remains an available option."*

On comparative performance the same section says: *"Several simulation studies have
concluded that an approach proposed by Paule and Mandel should be recommended; whereas
a comprehensive recent simulation study recommended the REML approach, although noted
that no single approach is universally preferable."*

**Decision: REML, everywhere.** It is Cochrane's own current default; it is one of the
two the Handbook names; and our house rule already said REML-or-PM below k=10, which
every pool in this corpus is. **The corpus was already mixed** — ARNI publishes the
REML value (0.8715, DL is 0.8835) while INCLISIRAN publishes DL — so this is not a
choice between changing and not changing, it is a choice between one estimator and two.

**Measured consequence, unchanged from the earlier quantification: 7 of 28 pools move,
0 conclusions change, median absolute shift 0.000%, largest 1.36%.** Every moved value
must be announced under `display_change_announced`.

### Hartung-Knapp — **DECIDED: sensitivity, not primary, at k≤3**

**§10.10.4.4–10.10.4.5**: the adjustment *"(generally) inflates the variance of the
summary mean and uses the t-distribution (with k − 1 degrees of freedom) in the
calculation of the confidence interval"*, and *"When there are only two or three
studies, we advise review authors to undertake a sensitivity analysis to compare
results from the different methods."*

**So HKSJ is not adopted as the primary interval.** It is reported as a sensitivity
analysis wherever k ≤ 3, which is most of this corpus. This also settles the house
note that HKSJ can *narrow* an interval when `Q < k−1`: the Handbook's own remedy for
the small-k case is to show both rather than to pick one.

---

## 2. ANSWER-HF's unregistered endpoint — **DECIDED, and Mahmood's reading is correct**

**The Handbook treats this as risk of bias, not eligibility.** **§8.7** is RoB 2's
fifth domain, *bias in selection of the reported result*, which covers bias arising
when *"the reported result is selected (based on its direction, magnitude or
statistical significance) from among multiple intervention effect estimates that were
calculated by the trial authors."* Its stated method is to *"attempt to retrieve the
pre-specified analysis intentions for each trial … allows for the identification of any
outcome measures or analyses that have been omitted from, or added to, the results
report, post hoc."*

**An endpoint added post hoc is exactly what §8.7 exists to grade.** Eligibility is
Chapter 3's business — participants, interventions, comparators, outcomes and study
design — and registration status is not among its criteria. Nothing in the Handbook
makes an unregistered analysis ineligible.

**Decision, and it is the conservative course:**
1. **ANSWER-HF stays in the primary analysis.** k=4, HR 0.8715 (0.7461–1.0181) stands.
2. **RoB 2 domain 5 (§8.7) is graded HIGH RISK for that trial**, with the registry
   enumeration as the stated evidence.
3. **k=3 is presented as a sensitivity analysis** under **§10.14**: *"Sensitivity
   analyses should be used to examine whether overall findings are robust to
   potentially influential decisions."* The k=3 value is 0.8333 (0.7473–0.9292).

**Why this ordering and not the reverse.** Excluding the trial converts a null result
into a positive one *by our own choice*, and the Handbook gives no basis for the
exclusion. Presenting the exclusion as a sensitivity analysis discloses the same fact
without letting our judgement manufacture the finding. **The direction of the error
matters: a wrong inclusion leaves a null intact; a wrong exclusion publishes a positive
result we created.**

---

## 3. The NMA verdict grain — **DECIDED: per contrast**

**§11.5**, verbatim: *"Since network meta-analysis produces estimates for several
intervention effects, the confidence in the evidence should be assessed for each
intervention effect that is reported in the results."*

**That is the answer to the parked protocol question.** A network where one contrast is
sound and another is not does not need a single network-wide verdict, because the
Handbook does not assess confidence network-wide. **Each contrast carries its own
verdict; a withdrawal is per contrast; and the standard's "the pool stands or is
withheld with its reason" applies once per reported effect.**

Two supporting sections define what a contrast-level verdict must consider:
- **§11.2.2.1** — transitivity requires that *"different sets of randomized trials are
  similar, on average, in all important factors other than the intervention comparison
  being made"*, and that all interventions be *"jointly randomizable"*.
- **§11.4.4.4** — *"tests for detecting incoherence often lack power to detect
  incoherence when it is present"*, so an unfitted or non-significant incoherence test
  is not evidence of coherence. HFREF_NMA already states this on its face, correctly.

**HFREF_NMA is therefore workable without extending the standard.** Its real blocker is
unchanged and is a data problem, not a protocol one: **12 distinct NCT strings for 28
trials**, several of them shared runtime residue. Identity by registration must be
repaired first, per contrast.

---

## 4. Cangrelor and colchicine — **DECIDED against pooling, and the Handbook is explicit**

**§10.10.3**, verbatim: *"Meta-analysis should only be considered when a group of
studies is sufficiently homogeneous in terms of participants, interventions and
outcomes to provide a meaningful summary."* And: *"If there is considerable variation
in results, and particularly if there is inconsistency in the direction of effect, it
may be misleading to quote an average value for the intervention effect."*

**MECIR Box 10.10.a, mandatory expectation C62**, verbatim: *"Undertake (or display) a
meta-analysis only if participants, interventions, comparisons and outcomes are judged
to be sufficiently similar to ensure an answer that is clinically meaningful."*

**"Or display" settles it.** MECIR does not merely discourage computing such a pool; it
forbids showing one. Both topics fail the outcome limb on the registrations already
read — COLCHICINE_CVD's trials count different composites (COLCOT counts cardiac arrest
and the others do not; CONVINCE is not a composite trial), and CANGRELOR_PCI mixed
all-cause-mortality numerators with primary-composite denominators. **Their withdrawals
stand, and are now grounded in a mandatory expectation rather than in our judgement.**

**§10.10.3 also disposes of a worry this project has carried:** *"A systematic review
need not contain any meta-analyses."* A topic that ends in a sourced non-poolable
verdict is a complete review, not a failed one.

---

## What the Handbook does NOT decide — brought back with consequences

### The ABLATION_AF and SGLT2_CKD replacement questions

The Handbook settles *whether* to pool (§10.10.3 — no, on the endpoints as they stand).
It does not choose *which replacement question* to ask, and it cannot: **§9.3.2** says
only to *"determine which studies are similar enough to be grouped within each
comparison by comparing the characteristics across studies"* and, as Chapter 9 states
plainly, provides no threshold rule.

**This remains a choice, and it is the one where the Handbook's silence is the point:**
a replacement question must be chosen **before its answer is known**, and for both
topics the components have already been seen.

| | option A | option B |
|---|---|---|
| **ABLATION_AF** | pool the COMPONENTS, as the one published synthesis does — all-cause mortality, stroke, HF hospitalisation separately | re-scope the page to rhythm-control strategy (k=4, keeping EAST-AFNET 4) and state that it is a different question from catheter ablation |
| **consequence** | the component values are already known to us (0.62, 0.63, 0.64), so choosing it now is choosing a question whose answer we have seen | preserves the trial set, but changes what the page claims to be about, and the index card and title must change with it |
| **SGLT2_CKD** | pool ESKD (dialysis-or-transplant) and CV death, defined identically across CREDENCE, DAPA-CKD and EMPA-KIDNEY and reported separately by all three | leave withheld |
| **consequence** | a genuine, defensible pool — and the same "we have seen the components" objection does not apply here, because these were identified as *definitionally identical* before any value was read | a correct page that answers nothing |

**My recommendation, stated as one:** take **SGLT2_CKD option A** — the endpoints were
established as identical from the registrations before any effect was looked at, which
is the pre-specification the Handbook asks for. **Do not take ABLATION_AF option A**;
its component values are already known to this project, and choosing that question now
is the exact failure the standard's own protocol warns about. If ABLATION_AF is to be
rescued, option B is the honest route and it needs your decision on scope.

---

## Applied in this session

| decision | status |
|---|---|
| REML corpus-wide, HKSJ as k≤3 sensitivity | **decided; application is a published-number change and is staged separately** |
| ANSWER-HF stays, RoB domain 5 HIGH, k=3 sensitivity | **decided and applied to the object** |
| NMA verdicts per contrast | **decided; recorded in the standard's scope** |
| Cangrelor / colchicine withdrawals | **decided; reasons re-grounded on §10.10.3 + MECIR C62** |
| ABLATION_AF / SGLT2_CKD replacement questions | **NOT decided — needs Mahmood, options and consequences above** |
