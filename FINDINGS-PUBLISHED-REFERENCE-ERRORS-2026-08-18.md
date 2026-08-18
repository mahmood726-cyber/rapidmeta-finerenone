# Do published syntheses make the same reference errors? **First one checked: yes.**

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
