# Build-to-core decisions for the five contaminated apps

Rule applied: build on the sourceable core however small; where the structure
collapses, **drop the structure claim, not the app**; park only if zero usable
same-area trials remain. Every app records its fabrication finding either way.

A third removal reason emerged that the disease-area filter could not see:
**wrong drug class**. A trial can be in the right disease area and still be the
wrong evidence — sotagliflozin is an SGLT1/2 inhibitor sitting in a review of
incretin agonists.

---

## 1. MPOX_VACCINE_NMA → **SINGLE-TRIAL build, network claim dropped**

| | |
|---|---|
| cited | 10 |
| fabricated | **6** — `NCT05000405`–`NCT05000410`, a consecutive block |
| wrong area | 3 — ovarian cancer, chronic kidney disease, a healthy-volunteer sleep study |
| survives | **1** — `NCT00316524` |

The survivor is MVA-BN (IMVAMUNE) versus placebo, **condition: Smallpox**,
phase 2, primary outcome **seroconversion by ELISA**.

Two structure claims are dropped, not one:

* **Not a network.** One node is not a network. No indirect comparison, no
  SUCRA, no ranking — those surfaces are removed, not left empty.
* **Not an efficacy review.** The only surviving trial measures immunogenicity.
  A vaccine-efficacy framing cannot rest on a seroconversion endpoint, so the
  built app reports what the trial measured.

Built form: a k=1 immunogenicity summary of MVA-BN, structurally identical to
the rivaroxaban pilot — no pooling language, k=1 flag, single-trial result.
MVA-BN is the vaccine used against mpox, so the trial is relevant to the topic;
it is immunobridging evidence, and the app must say so rather than implying
mpox efficacy.

---

## 2. OBESITY_DUAL_TRIPLE_AGONIST → **SINGLE-TRIAL build**

| | |
|---|---|
| cited | 15 |
| fabricated | 3 — `NCT05305249`, `NCT05971644`, `NCT06133752` |
| wrong area | 9 — four heart-failure SGLT2 outcome trials, plus depression neuromodulation, haematologic neoplasms, a wrinkle device, a surgical fluid challenge, ARDS |
| wrong drug class | 1 — `NCT03521934` sotagliflozin, an SGLT1/2 inhibitor in heart failure and T2D with a cardiovascular primary outcome. Right-ish disease area, wrong intervention class, wrong outcome |
| survives, in scope | **2** — `NCT04881760` retatrutide, `NCT06066528` survodutide |
| survives **with data** | **1** — retatrutide only; survodutide has no posted results |

Built form: k=1 on retatrutide (LY3437943), phase 2, primary outcome **mean
percent change in body weight** — a CONTINUOUS outcome across five dose arms,
not the pooled RR the app claims. Survodutide is recorded as identified and
in-scope but contributing no data, which is a different state from excluded and
must not be collapsed into it.

---

## 3. ALIROCUMAB_LIPID → **BUILD-TO-CORE, k=6**

| | |
|---|---|
| cited | 12 |
| fabricated | 0 |
| placeholder | 1 — `NCT12345678` |
| wrong area | 5 — `NCT01035255`, `NCT01920711`, `NCT02924727`, `NCT03988634`, `NCT05901831`: the sacubitril/valsartan heart-failure set plus a CKD trial |
| survives | **6**, all genuine alirocumab trials, all with posted registry results |

The strongest build-to-core candidate: six real trials of the right drug with
registry results is a genuine multi-trial analysis. This is the app that tests
the k>1 recompute detector on sourced data.

---

## 4. PREVNAR15_PNEUMO → **BUILD-TO-CORE, k=8**

| | |
|---|---|
| cited | 14 |
| fabricated | 0 |
| placeholder | 1 |
| wrong area | 5 — the **same** cardiology set as ALIROCUMAB (`NCT01035255`, `NCT01920711`, `NCT02924727`, `NCT03988634`, `NCT05901831`) |
| survives | **8**, all V114 pneumococcal conjugate vaccine trials with results |

The identical five-trial contaminating set in two unrelated reviews is one donor
template, and that is recorded as the finding. Endpoints are immunogenicity, not
clinical disease, and the built app says so.

---

## 5. DDIMER_PE_DTA → **BUILD-TO-CORE conditional on the 2x2s**

| | |
|---|---|
| cited | 6 |
| fabricated | 0 |
| wrong area | 2 — hepatocellular carcinoma, an obesity brown-adipose study |
| survives | **4** — all genuine D-dimer / PE / DVT diagnostic studies |

All four have **no posted registry results**, so the TP/FP/FN/TN tables must come
from the publications. The DTA set is valid in principle — four same-question
diagnostic studies support a bivariate analysis — but the build proceeds only
for those whose 2x2 can be sourced. Any study whose table cannot be recovered is
excluded with that reason stated, not imputed.

---

## Parked: none

Every one of the five has at least one usable same-area trial, so none is
parked. Two lose their structure claim (MPOX loses the network, OBESITY loses
the pooling), which under the rule means the app is emitted in the form its
evidence actually supports.

## Disclosure requirement

Each built app displays, prominently and as a projection of the canonical
object, the count and reason for every removed citation — fabricated,
wrong-area, wrong-drug-class, or placeholder. A reduced evidence base that is
not disclosed is a worse defect than the contamination it replaced.
