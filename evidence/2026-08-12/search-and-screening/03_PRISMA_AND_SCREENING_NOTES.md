# PRISMA numbers and screening notes — screener A

Screener A: Claude (Anthropic family). Independent. **Not reconciled with anything.** A second cross-family screener runs separately, per protocol §6.

Per-record decisions: `02_CORPUS_AND_SCREENING.tsv` — 423 data rows, one per record, no duplicate identifiers, all rows well formed (11 fields).

---

## 1. PRISMA flow, as it actually fell out

```
IDENTIFICATION
  Records identified from databases ......................... 423
      PubMed (esearch count, read) ......................... 331
      ClinicalTrials.gov API v2 (totalCount, read) .......... 92
  Records identified from other registered sources ............ 0
      backward citation search ........................ not run
      FDA statistical review / EMA EPAR ............... not run
  Records removed before screening
      duplicate identifiers ................................... 0
      (no identifier appears twice; see §2 on cross-source linkage)

SCREENING
  Records screened (title/abstract) ......................... 423
  Records excluded at title/abstract ........................ 412

  Records sought for full text .............................. 11
      Full text retrieved and assessed ....................... 9
      Not retrieved  ......................................... 2   <-- see §4

ELIGIBILITY
  Full-text records assessed ................................. 9
  Full-text records excluded ................................. 5

INCLUDED
  Records included ........................................... 4
  STUDIES included ........................................... 2
```

**Two studies, four records** — each included trial is represented by one publication and one registry record:

| Study | Publication | Registry | Reported quantity |
|---|---|---|---|
| PARADIGM-HF | PMID 25176015 | NCT01035255 | HR **0.80** (95% CI 0.73–0.87) for CV death or first HF hospitalisation; 914/4187 vs 1117/4212; median follow-up 27 months |
| PARALLEL-HF | PMID 33731544 | NCT02468232 | HR **1.09** (95% CI 0.65–1.82), P=0.6260, for CV death or HF hospitalisation; n=225; median follow-up 33.9 months |

k = 2. The protocol's own §11 anticipated this ("with the small number of trials this comparison has") and §10 pre-specifies that the prediction interval is not reported where k makes it undefined — at k=2 it is on 1 degree of freedom and effectively uninformative, and §12 makes the small-study-effect tests not assessable.

---

## 2. Why no records were removed as duplicates

No identifier appears in the corpus twice, within or across the two databases (checked). PubMed and ClinicalTrials.gov index different object types, so a trial legitimately appears once as a publication and once as a registry entry. Collapsing those pairs is **study-level linkage**, not duplicate removal, and I performed it only for the nine records taken to full text — where the link matters to the count of *studies*. I did not attempt registry↔publication linkage across the other 414 records, because doing it from titles alone would produce a number I could not defend.

The consequence, stated plainly: **"records screened = 423" counts registry entries and publications separately.** The "studies included = 2" figure is the one that is study-level.

---

## 3. Exclusion reasons — 417 excluded records, by the axis that failed

| Axis failed | n | What it means here |
|---|---|---|
| RANDOMISATION | 195 | not a randomised trial report — reviews, meta-analyses, editorials, letters, consensus statements, cost-effectiveness analyses, registries, observational cohorts, case series, surveillance |
| **OUTCOME** | **135** | randomised and on-topic, but the quantity reported is not a time-to-first-event hazard ratio for the composite |
| COMPARATOR | 38 | comparator is valsartan, ramipril, standard/individualised therapy, an SGLT2 inhibitor, a different initiation timing or uptitration regimen, or there is no comparator |
| POPULATION | 35 | HFpEF, paediatric, acute MI/STEMI, dialysis/ESKD, hypertension, transplant, HIV, congenital systemic right ventricle, animal models |
| INTERVENTION | 14 | the intervention under test is something else (XXB750, REGN5381, dapagliflozin, vericiguat, hydralazine/nitrates, ablation, polypills, care-delivery protocols) |

Where more than one axis failed, the row records the one I judged primary and names the reported quantity regardless.

### The outcome axis did the work it was pre-registered to do

All three offending quantity types named in advance by protocol §2 were actually present in the corpus, and each excluded a study that is otherwise large, well conducted and directly on topic:

| Offending type (pre-registered) | Record | What it reports |
|---|---|---|
| **Recurrent-event rate ratio** | PMID 29431251 — PARADIGM-HF recurrent events | negative binomial RR 0.77 (0.67–0.89); LWYY RR 0.78 (0.68–0.90); WLW HR 0.79 (0.71–0.89); joint frailty HR 0.75 (0.66–0.86). Counts repeat events per person; the estimand counts each person once, at their first event. |
| **Win ratio over a hierarchical composite** | PMID 41335448 / NCT04023227 — PARACHUTE-HF | stratified **win ratio 1.52** (1.28–1.82), P<.001, over a hierarchy of CV death, then HF hospitalisation, then 12-week NT-proBNP change. n=922, 83 sites, four countries, McMurray on the author list. Excluded on the outcome axis, **not** on quality. |
| **Fixed-timepoint dichotomous risk ratio** | — | **not encountered.** No record in this corpus reports the composite as a fixed-timepoint dichotomous risk ratio. Recording this as "not encountered" rather than leaving the row blank: the criterion was live and simply did not fire. |

A fourth quantity type that the protocol did not name in advance also appeared and is excluded on the same reasoning: PANORAMA-HF (PMID 39319469 / NCT02678312) reports a **global rank endpoint** (Mann-Whitney probability 0.52, MW odds 0.91). It fails the population axis independently, so nothing turns on it, but it is worth flagging to whoever maintains the list.

ANSWER-HF (PMID 41396086) reports a **change in LVEF** as its primary (between-group difference 0.9 percentage points, 95% CI −0.9 to 2.6) and a **win ratio 1.80** (1.27–2.63) as a hierarchical secondary. Excluded on the outcome axis.

---

## 4. Two records left undetermined — and why

| Record | Title | Why undetermined |
|---|---|---|
| PMID 38508844 | Sacubitril/Valsartan in Patients Hospitalized With Decompensated Heart Failure (JACC 2024) | Publication type is `Randomized Controlled Trial`, but the title names neither the comparator nor the reported quantity. Abstract not retrieved. |
| PMID 34395116 | Comparison of Sacubitril/Valsartan Versus Enalapril in the Management of Heart Failure (Cureus 2021) | Title names the right comparison but does not reveal whether it is a trial report and does not reveal the reported quantity. Abstract not retrieved. |

These are **undetermined, not excluded**. Both plausibly clear population, intervention and comparator; both turn entirely on the outcome axis, which is exactly the axis that cannot be read off a title. Resolving them requires two abstracts. They are the first thing to do on resumption, and until they are resolved the included-studies count of 2 should be read as a **lower bound**.

---

## 5. What "title/abstract screening" actually rested on — stated so it is not overclaimed

Abstracts were retrieved in full for **7 records** (PMIDs 25176015, 33731544, 41335448, 41396086, 29431251, 39319469, 29144684). For the remaining 416 records the stage-1 decision rested on **title, journal and PubMed publication type**, or on **brief title, status, interventions and conditions** for registry records.

Excluding on title at stage 1 is conventional and, for the 195 records that are self-declared reviews, meta-analyses, editorials, consensus statements and cost-effectiveness analyses, it is not a close call. But it is not the same act as reading 423 abstracts, and this file should not be read as though it were. The 135 outcome-axis exclusions are the ones where an abstract could in principle change the decision — most are secondary analyses whose titles name the reported quantity explicitly ("Serum potassium in the PARADIGM-HF trial", "Effect ... on aortic stiffness"), but a second pass with abstracts would put that on firmer ground.

The second cross-family screener working from the same 423-row corpus is the right check on this, and the disagreement rate on the outcome-axis rows is worth reporting separately from the overall rate.

---

## 6. Caveat on the two included studies

The estimand for both included trials was established from the **published abstract**. The confirmatory read of the ClinicalTrials.gov primary-outcome-measure fields for NCT01035255 and NCT02468232 was **blocked by HTTP 429** and did not happen (see `01_SEARCH_CAPTURE.md` §4, obstacle 5). For PARADIGM-HF the abstract states the primary outcome as "a composite of death from cardiovascular causes or hospitalization for heart failure" with a hazard ratio, which is a time-to-first-event quantity by construction. For PARALLEL-HF the abstract states "the primary composite outcome of CV death and HF hospitalization (HR 1.09; 95% CI 0.65-1.82)". Neither abstract was cross-checked against the registry record or the statistical analysis plan. Protocol §7 requires a resolvable pointer to the specific document and table for every extracted cell; that requirement is **not yet met** for either trial.

---

## 7. Risk of bias

No RoB-2 assessment was performed. Protocol §9 records this as PENDING and requires two cross-family assessors, neither of whom may be the agent that assembled the canonical object. Nothing in this screening run executes §9.
