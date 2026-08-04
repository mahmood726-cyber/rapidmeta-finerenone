# Published-meta reconciliation

For each k>1 build: find the best published review in the exact area, diff the
trial list, and reconcile the estimate — decomposing any gap into (a) our bug,
(b) different trial set, (c) different method or estimand.

---

## COVID19_VACCINES vs Cochrane

**Reference:** Graña C et al. *Efficacy and safety of COVID-19 vaccines.*
Cochrane Database of Systematic Reviews 2022. PMID 36473651,
doi 10.1002/14651858.CD015477. Full text read from PMC.

### Trial-list diff

| our trial | in Cochrane? |
|---|---|
| NCT04530396 Gam-COVID-Vac | **yes** |
| NCT04652102 CVnCoV | **yes** |
| NCT04510207 BBIBP-CorV | **yes** |
| NCT04324606 (we removed) | yes — see below |

**Nothing we carry is absent from the reference review.** No contamination
survived into our core.

On the trial we removed: Cochrane includes NCT04324606 **and** NCT04400838 as
**separate studies**. That confirms the diagnosis rather than contradicting it —
our defect was never that the trial is illegitimate, it was that we attached
Voysey's *pooled* counts across four trials to one registration. Cochrane's
ChAdOx1 figure is drawn from **2 RCTs**, for exactly this reason.

They cite 271 registrations we lack, but that is not a like-for-like gap: their
review covers *all* COVID-19 vaccines and its citation list includes ongoing and
excluded studies. Our object repairs one contaminated app; it is not an
independent systematic review and must not be read as one.

### Estimate reconciliation

| vaccine | our crude RR (VE) | Cochrane VE (95% CI) | gap |
|---|---|---|---|
| BBIBP-CorV | 0.2209 (**77.9%**) | **78.10%** (64.80–86.30) | 0.2 pp |
| Gam-COVID-Vac | 0.0845 (**91.5%**) | **91.10%** (83.80–95.10) | 0.4 pp |
| CVnCoV | 0.5439 (**45.6%**) | **48.20%** (31.70–60.90) | 2.6 pp |

Two reconcile to within rounding. The CVnCoV gap decomposes cleanly as **(c)
method**: that trial analysed its outcome on **person-time**, which our crude
count-based risk ratio ignores. The object already records this. Denominators
match exactly — 25,062 on both sides.

### The decisive finding

**Cochrane never pools across vaccines.** It reports efficacy separately for
BNT162b2, mRNA-1273, ChAdOx1, Ad26.COV2.S, BBIBP-CorV, BBV152, NVX-CoV2373 and
CoronaVac. There is no counterpart in the reference standard to the single
pooled number the source app computes across vaccine platforms.

That is a **(c) estimand** difference in which the published review is right and
the app is the anomaly. It independently vindicates the I²=95% caveat: the
correct treatment is not a better pooled number, it is **no pooled number**.

---

## ALIROCUMAB vs Cochrane

**Reference:** Schmidt AF et al. *PCSK9 monoclonal antibodies for the primary and
secondary prevention of cardiovascular disease.* Cochrane Database of Systematic
Reviews 2020. PMID 33078867, doi 10.1002/14651858.CD011748.pub3. Abstract read;
PMC returned metadata only, so the included-study table could not be diffed
trial by trial. That limit is stated rather than worked around.

### Trial-list diff

They include **24 studies, 18 randomising alirocumab**; we carry **6**.

This is **(b) a different trial set**, and the reason is scope rather than error:
our object repairs the citation list of one app. It is not a systematic review of
alirocumab, and the further alirocumab RCTs are legitimate recovery candidates
for anyone who wants one.

### Estimate reconciliation — not possible, and that is the finding

**No comparable pooled estimate exists.** Cochrane pools *clinical events* — CVD
(OR 0.87, 0.80–0.94), mortality (OR 0.83, 0.72–0.96), MI (OR 0.86, 0.79–0.94),
stroke (OR 0.73, 0.58–0.91). We pool **percent change in LDL cholesterol**. A
**(c)** estimand difference so complete that no number is comparable.

Worth stating plainly: the reference review answers *does this drug prevent
events*; the app answers *how much does it lower a lipid*. The second is a
surrogate for the first, and an app reporting only the surrogate should say so.

### Trial recovered — by the gate, not by this diff

`NCT01507831` posts LDL-C at week 24 as a **secondary** outcome. An earlier build
excluded it after reading primary outcomes only. **k rose 5 → 6**; the pooled
estimate moved from **−52.58 (−60.61 to −44.56)** to **−54.66 (−60.75 to
−48.56)**, τ² 70.65 → 47.42. The superseded figure is retained in the object.

---

## Summary

| app | trial-list diff | estimate reconciliation | verdict |
|---|---|---|---|
| COVID19_VACCINES | all 3 present in the reference; nothing spurious | 2 of 3 match within rounding; third explained by person-time | **reconciles**; the reference's refusal to pool across vaccines is a finding about the app |
| ALIROCUMAB | ours a 6-of-18 subset, by scope | not comparable — different outcome | **reconciles**; a trial was recovered, k 5→6 |

Neither reconciliation manufactured a divergence, and in both cases the published
review was justified. The one substantive change came from the gate, not the diff.
