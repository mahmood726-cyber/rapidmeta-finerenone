# Do published syntheses make the same reference errors? **1 of 4. See the completed denominator at the foot of this file.**

> **SUPERSEDED HEADER.** This file was written in two instalments and the first one read
> stronger than the evidence. The completed answer is **4 of 4 checked, 1 affected, 3
> handled correctly** — scroll to *DENOMINATOR COMPLETE*. The first instalment is left
> intact rather than rewritten, so the progression from a 1-of-2 headline to a 1-of-4
> result can be read rather than taken on trust.

The claim being tested — written down before it was tested, and it was untested until
now — is that a pool can be wrong in a way **no arithmetic reveals**, and that a
published synthesis making the same combination would therefore look impeccable, because
peer review does not recompute.

**Denominator, mandatory: 2 of the 4 closed topics checked. 1 affected, 1 appears
correctly handled. Two unchecked.**

---

## AFFECTED — `RIOCIGUAT_PAH`: a published meta-analysis pools PAH with CTEPH

**Wang et al., *Annals of Palliative Medicine* — "Riociguat therapy for pulmonary
hypertension: a systematic review and meta-analysis."** Verified by reading the article
directly, not from a search summary.

| what it reports | verbatim |
|---|---|
| the pooled result | *"For PAH and CTEPH patients, participants treated with riociguat could walk 39.84 meters further than those receiving placebo (P<0.00001)."* |
| the population | *"A total of 5 studies had been conducted on PAH and CTEPH patients (n=1,230), of which 810 were on a riociguat treated group and 420 on a placebo group."* |
| disaggregation | **"The analysis does not disaggregate 6MWD results between PAH and CTEPH as separate disease entities in the primary pooled estimate."** |

**That is precisely the combination this project refused.** `RIOCIGUAT_PAH` was closed as
NOT POOLABLE on 2026-08-18 because `NCT00810693` enrols pulmonary arterial hypertension
and `NCT00855465` enrols chronic thromboembolic pulmonary hypertension — a different
disease, with a different mechanism and different management — and the topic is titled
for PAH.

**Every arithmetic property of that published pool is sound.** The trials are real,
randomised, placebo-controlled; they measure the same instrument (six-minute walk
distance); the effect sizes combine correctly; the heterogeneity statistic is
computable. **Nothing in a numerical check reaches it**, because nothing about it is
numerically wrong. What is wrong is what the number is *about*.

**This is the first direct evidence for the claim**, and it is a peer-reviewed
systematic review in an indexed journal, not a preprint or a poster.

---

## APPEARS CORRECTLY HANDLED — `MIPOMERSEN_HOFH`

**"The Effect of Mipomersen in the Management of Patients with Familial
Hypercholesterolemia: A Systematic Review and Meta-Analysis of Clinical Trials"**,
*JCDD* 2021.

Two things it appears to get right, and both are the errors we found on our own page:

1. **It scopes its title to "familial hypercholesterolemia"**, not to *homozygous* FH.
   Our defect was the reverse — a page titled HoFH carrying a statin-intolerant trial.
   A review whose title covers what it pooled has not made this error.
2. **It reports against placebo** (mean difference −24.79, 95% CI −30.15 to −19.43),
   which is consistent with having excluded the uncontrolled open-label extension.

**STATED AS PROVISIONAL, because I did not verify the trial list.** The scoping and the
placebo comparison are read from the abstract-level report; whether `NCT00477594` — the
extension with no control arm — is among its five studies was **not** checked. **Marked
"appears correctly handled" and not "handled correctly", and it should be confirmed
before being quoted.**

---

## NOT CHECKED — `EDOXABAN_VTE`, `OLMESARTAN_HTN`

Neither has been searched. **Two of four remain unchecked and the denominator says so.**

---

## What this does and does not establish

**It establishes** that at least one peer-reviewed meta-analysis has pooled two distinct
diseases into a single estimate that this project independently refused, on grounds no
consistency check could have raised. **One instance is not a rate**, and this file does
not claim one.

**It does not establish** that the field is generally exposed. One affected of two
checked, with two unchecked, is a finding worth pursuing and nothing more. The honest
next step is the other two topics, and then the same question asked of the corpus's
other withdrawals rather than only of this round's.

**And the running score matters more than the instance.** On every previous comparison
this project has made against the published literature — three of them — **the
literature was right and we were wrong**, which was honest and modest and is recorded as
such. This is the first comparison to go the other way. **That asymmetry is the reason
to keep the denominator visible: a project that reports only the comparisons it wins has
stopped being a measurement.**

---

## Sources

- [Riociguat therapy for pulmonary hypertension: a systematic review and meta-analysis — Wang et al., *Annals of Palliative Medicine*](https://apm.amegroups.org/article/view/81965/html)
- [The Effect of Mipomersen in the Management of Patients with Familial Hypercholesterolemia: A Systematic Review and Meta-Analysis of Clinical Trials — *JCDD* 2021](https://doi.org/10.3390/jcdd8070082)
- [Open Label Extension of ISIS 301012 (Mipomersen) — NCT00477594, ClinicalTrials.gov](https://clinicaltrials.gov/study/NCT00477594)


---

# DENOMINATOR COMPLETE: **4 of 4 checked. 1 affected, 3 handled correctly.**

Updated 2026-08-18 after verifying the mipomersen trial list and checking the two that
were outstanding. **The provisional verdict is now verified, and the headline is more
modest than the first instalment suggested.**

| topic | published synthesis found? | same combination? |
|---|---|---|
| **RIOCIGUAT_PAH** | yes | **YES — AFFECTED.** Pools PAH with CTEPH into one 6MWD estimate |
| **MIPOMERSEN_HOFH** | yes | **no — verified correct** |
| **EDOXABAN_VTE** | yes | **no — correct** |
| **OLMESARTAN_HTN** | yes | **no — correct, and pointedly so** |

---

## MIPOMERSEN — upgraded from "appears correct" to **verified correct**

The trial list was read, which is what the earlier entry said had not been done.
[JCDD 2021](https://pmc.ncbi.nlm.nih.gov/articles/PMC8304130/) includes **5 RCTs, 549
patients, all placebo-controlled and double-blind**, and **explicitly excluded open-label
extensions and single-arm studies**. `NCT00477594` — the uncontrolled extension whose two
arms are both mipomersen — **is not in it.**

Its stated inclusion criterion, verbatim: *"Randomised controlled clinical trials
comparing patients (adults or pediatric) with FH receiving subcutaneous injections of
mipomersen as an add-on to previous pharmacologic cholesterol-lowering interventions **and
a parallel group receiving a placebo or no intervention**."* The parallel-group
requirement is exactly the rule that excludes the extension.

It also scopes its title to **familial hypercholesterolaemia** and reports 4 heterozygous
and 1 homozygous trial, so its population claim covers what it pooled. **Both errors we
made on that page, it avoided.**

---

## EDOXABAN — correct: prophylaxis is pooled with prophylaxis

The published pooled analysis combines **STARS E-3 and STARS J-V — both prophylaxis after
knee or hip arthroplasty**. The Hokusai treatment trials and the paediatric Hokusai study
are reported separately. **No synthesis pools prevention with treatment.** The distinction
we drew is the one the field already draws.

---

## OLMESARTAN — correct, and it is the sharpest of the three

There **is** a published meta-analysis of essentially these trials:
[*"Comparison of safety and efficacy of combinations of Azilsartan-medoxomil/
Chlorthalidone and Olmesartan-medoxomil/Hydrochlorothiazide among hypertensive
patients"*](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC10387287/) — 4 studies, 3,146
patients.

**It names the contrast correctly.** Azilsartan/chlorthalidone **versus**
olmesartan/hydrochlorothiazide: both arms named, the intervention identified as the
intervention. It does not title itself for the comparator. **That is precisely the
discipline our page failed**, and the literature applied it without difficulty.

**A discrepancy worth recording rather than glossing:** that review reports *"no
significant differences ... in mean systolic blood pressure"* (with diastolic favouring
azilsartan, WMD −2.64 mmHg), while our k=2 pool of the two trials sharing both arms gives
**MD −5.69 mmHg (−7.30, −4.08)** on systolic. Different trial sets — theirs has four
studies — and possibly different timepoints and endpoint definitions. **Not resolved
here, and it is the next thing to look at on that topic.**

---

## What the completed denominator actually says

**One affected of four.** The claim that this class is invisible to peer review is
**supported by one verified instance and contradicted by three**. That is a much weaker
result than the first instalment read like, and it is the honest one.

**The mechanism survives even so, and it is the part worth publishing.** The riociguat
pool is arithmetically impeccable — real randomised placebo-controlled trials, one
instrument, effect sizes that combine, a computable heterogeneity statistic — and it
combines two diseases. **Nothing in peer review recomputes, so nothing in peer review
could have caught it.** One verified instance plus a demonstrated screening method is a
stronger claim than a rate, because the rate will always be contested and the mechanism
will not.

**And the running score across every literature comparison this project has made is now
3 right / 1 wrong in the literature's favour.** On the three occasions we checked our own
numbers against published work before today, the literature was right and we were wrong.
Today it is right three times and wrong once. **A project that reported only the
comparison it won would have published a finding four times stronger than the evidence.**


---

## The olmesartan discrepancy, decomposed — **reproduce before explaining**

Our k=2 pool gives **MD −5.69 mmHg (−7.30, −4.08)** on systolic. The published review
reports **no significant systolic difference**. "Different trial sets" was the explanation
*offered*; here is the explanation *established*.

**Their result, verbatim:** systolic **"WMD −2.95 [−6.64, 0.73]; P = 0.12; I² = 100%"**;
diastolic **"WMD −2.64 (−2.78, −2.51), P = 0.00001, and I² = 1%"**.

**Their four studies:** Cushman 2012 (n=1,071), Neutel 2017 (n=837), Cushman 2018
(n=1,085), Bakris 2018 (n=153). Two of those correspond to the trials we pooled; **Neutel
2017 and Bakris 2018 are additional and are not in our seeded set.**

### Three differences, and the trial set is the least of them

**1. A different estimand.** Their tables present *"Mean SBP (SD)"* at study conclusion —
**final values**, not change from baseline. Our values are the registered primary,
*"Change From Baseline to Week 8 in Trough, Sitting, Clinic Systolic Blood Pressure"*,
read from each registry's posted ANCOVA analysis. **A final-value pool and a
change-from-baseline pool are not two estimates of one quantity**, and comparing them as
if they were is the reference error this project screens for — committed by us, against
them, if we had let the "different trial sets" explanation stand.

**2. Their own heterogeneity statistic says the systolic pool is not interpretable.**
**I² = 100%** on the systolic outcome. That is not a caveat on the result; at that value
the pooled point is an average of quantities the statistic says have nothing in common.
They report it and interpret the result anyway.

**3. And it is internally odd in a way worth flagging neutrally:** the *same four
studies* give **I² = 1%** on diastolic and **I² = 100%** on systolic. Two outcomes from
one trial set do not usually behave that differently, and it is the kind of thing a
reader is entitled to see raised.

### What this changes

**Our number is not in disagreement with theirs, because they are not estimates of the
same thing.** The honest statement on our page is that it pools the registered
change-from-baseline primary across the two trials sharing both arms, and that a
published review pooling final values across four trials reports no significant systolic
difference with I² = 100%.

**And the discipline held:** reproducing their result first is what revealed that the
disagreement was not about trials at all. Had we gone straight to explaining our
difference, "they included two trials we did not" would have been written down as the
answer, and it would have been wrong.
