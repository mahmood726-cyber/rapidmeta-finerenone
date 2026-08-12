# Adjudication log — flagged conflicts against screener A

**This file is an overlay. `02_CORPUS_AND_SCREENING.tsv` has NOT been edited.** Screener A's original decisions stand as recorded, including the ones now known to be wrong. Rewriting them would destroy the measurement.

Raised: 2026-08-12, by a sibling lane, against screener A (Claude, Anthropic family).

---

## CONFLICT 1 — PARACHUTE-HF (PMID 41335448 / NCT04023227)

| | |
|---|---|
| Screener A recorded | `exclude`, axis `OUTCOME`, at FullText |
| Challenge | The trial also reports a time-to-first-event hazard ratio for the composite, as a secondary endpoint |
| **Verified at source** | **Yes** |
| **Screener A's position now** | **I was wrong. This is a screener-A error.** The record should be `INCLUDE`. |
| **RULING** | **INCLUDE — human adjudication** |

### ⚖ HUMAN ADJUDICATION DECISION

| Field | Value |
|---|---|
| **Adjudicator** | **Mahmood** — the review's named human adjudicator (protocol §6: *"Adjudication of disagreements is by a named human"*) |
| **Decision** | **INCLUDE PARACHUTE-HF (NCT04023227 / PMID 41335448)** |
| **Grounds** | The trial reports the registered estimand: the composite of first heart-failure hospitalisation or cardiovascular death as a **time-to-first-event hazard ratio, HR 0.91 (95% CI 0.73–1.13)** — JAMA Table 2, secondary outcomes, Cox proportional hazards model stratified by country |
| **Date (UTC)** | **2026-08-12T13:30:45Z** |
| **What it overrides** | Screener A's stage-1 exclusion on the outcome axis. **That exclusion stands unaltered in `02_CORPUS_AND_SCREENING.tsv`** and is not edited, hidden or annotated in place. |
| **Verbatim instruction** | *"parachute HF should be included so add I human adjucation decision to include it"* |

The chain of record is: screener A's decision → the conflict raised against it → the evidence read at source → the human's ruling, attributed and dated. Each link is separately inspectable and none overwrites another.

### Verification, done at source and not from the challenge

Read from the JAMA main text via PMC12676478, **Table 2**, section "Secondary outcomes" — not the abstract, not from the message raising the conflict:

> **First hospitalization for HF or cardiovascular death** — 155 (33.5%), 16.8 per 100 patient-years vs 169 (36.7%), 18.8 per 100 patient-years; adjusted absolute difference −3.1 (−9.2 to 3.0); **HR: 0.91 (0.73 to 1.13)**; P = .40

Table 2 footnote **d**, which the HR carries: *"HRs were derived from Cox proportional hazards models, with stratification by country."* A Cox model on a composite estimates the hazard of the first event; the 155 and 169 are patients with an event, not events. This is the registered estimand.

Counts match the challenge exactly (155/462 and 169/460).

For completeness, Table 2 shows PARACHUTE-HF reporting **four different quantity types** for overlapping outcomes:

| Quantity | Value | Under the registered rule |
|---|---|---|
| Win ratio over the hierarchical composite (primary) | 1.52 (1.28–1.82) | excluded type |
| **HR for CV death or first HF hospitalisation (secondary)** | **0.91 (0.73–1.13)** | **the estimand — qualifies** |
| LWYY rate ratio, recurrent HF hospitalisation + CV death | 0.90 (0.63–1.28) | excluded type |
| Fine-Gray subdistribution HR, first HF hospitalisation | 0.74 (0.49–1.14) | not the composite |

A single trial carrying all of these is exactly why the rule has to be applied against the full set.

### Why I got it wrong

I applied the outcome-axis rule to **the trial's primary endpoint** and stopped. The pre-registered rule is a condition on the quantity reported, and protocol §2 nowhere restricts it to a trial's primary. I imported that restriction myself, silently, and I did not notice I had done it — my own exclusion note reads "No time-to-first-event hazard ratio for the composite", which is a statement about the whole paper that I had not checked.

The error is aggravated, not excused, by the fact that I marked this record `FullText`. I had the abstract, and the abstract describes only the primary. I never opened Table 2. Labelling the stage `FullText` when what I actually read was an abstract is a second, separate error in the record, and it is the one that let the first go undetected.

### The generalisable lesson

**An outcome-axis rule must be applied against everything a trial reports, not against its primary endpoint.** Endpoint rank is a property of the trial's own design; the estimand is a property of the review. Conflating them silently reintroduces the exact deference to trialists' framing that a pre-registered estimand exists to remove.

And the sharper corollary: **a title/abstract-stage decision cannot see a secondary endpoint at all.** Abstracts report primaries. Any outcome-axis exclusion made at title/abstract is therefore structurally unable to detect the qualifying quantity when it sits below the primary. That is not a lapse of care at stage 1; it is a limit of what stage 1 can see. Outcome-axis exclusions cannot safely be made at title/abstract for a record that clears population, intervention and comparator.

My own PRISMA note predicted that disagreements would concentrate in the outcome-axis rows. They did. It landed on the highest-weight trial I assessed — the existing object pools PARACHUTE-HF at roughly 24%.

---

## CONFLICT 2 — self-raised: the "not encountered" claim was wrong

Screener A recorded, in `03_PRISMA_AND_SCREENING_NOTES.md` §3, that the third pre-registered offending type — a fixed-timepoint dichotomous risk ratio — was **"not encountered"** in the corpus.

**That was wrong, and I found it while doing the re-examination below.**

PMID **34395116** (Bano et al., *Cureus* 2021, PMC8357012) — one of the two records I had left `undetermined` — is a 1:1 randomised, 12-month study of sacubitril/valsartan vs enalapril in 364 adults with LVEF <40%. Read at source (PMC8357012, Table 2):

> HF-related hospitalization: 25 (13.8%) vs 41 (22.4%); **RR 0.61 (0.39–0.97)**; RRR 38.3%; NNT 11.63; P = 0.03
> HF-related death: 7 (3.8%) vs 15 (8.1%); **RR 0.47 (0.19–1.12)**; RRR 52%; P = 0.09

A text search of the full article returns **zero** occurrences of "hazard ratio", "HR", "Cox", "Kaplan" or "time to event". The two components are reported separately and never combined; "HF-related death" is also not "cardiovascular death".

**Resolution: `exclude`, axis OUTCOME.** Quantity reported instead: fixed-timepoint dichotomous risk ratios on components. This is offending type 3, live and firing. The "not encountered" line in `03_...md` §3 should be read as superseded by this entry — I am not editing it out.

---

## CONFLICT 3 — ANSWER-HF (PMID 41396086 / NCT04853758): downgraded from exclude to undetermined

Screener A recorded `exclude`, axis `OUTCOME`, at `FullText`. Same failure mode as Conflict 1: the decision rested on the abstract, which reports the primary (LVEF change) and one hierarchical secondary (win ratio 1.80).

Re-examination:

- **Registry evidence is against a qualifying quantity.** NCT04853758's registered outcomes are: primaries — change in LVEF, win ratio analysis; secondaries — premature ventricular beats, arrhythmia density, sustained VT rates, NYHA class, six ventricular-remodelling measures, and biochemical/biomarker safety measures. No time-to-first-event composite of CV death or HF hospitalisation appears anywhere in the registered outcome set.
- **The full text was not read.** PMID 41396086 has **no PMC record** (`Identifier not found in PMC`); the JACC article is not openly accessible. **Named as a blocked source, not as an absence.**

Given Conflict 1, I will not exclude a trial on the outcome axis from registry metadata plus an abstract. **Recorded as `undetermined`, pending a read of the JACC tables.** Registry evidence makes a qualifying quantity unlikely, but "unlikely" is not the standard that just failed.

---

## Systematic re-examination of the 135 outcome-axis exclusions

The failure mode is not one row. Any record excluded on the outcome axis **that clears population, intervention and comparator** is at risk, because only such a record could carry the estimand in a secondary.

Filtering the 135 outcome-axis exclusions on that condition — randomised, adult, HFrEF, sacubitril/valsartan vs enalapril — leaves the following **distinct trials**. Every one requires a full-text read of its results tables before its exclusion can stand.

| Trial | Records | Primary endpoint (why I excluded it) | Priority |
|---|---|---|---|
| **PARACHUTE-HF** | 41335448 / NCT04023227 | win ratio | **RESOLVED — error, include** |
| **ANSWER-HF** | 41396086 / NCT04853758 | LVEF change | **now undetermined; full text blocked** |
| **Bano 2021** | 34395116 | components as risk ratios | **RESOLVED — exclude confirmed at source** |
| PIONEER-HF | 30415601, 30955360, NCT02554890, + 5 secondary records | NT-proBNP change | Medium — registry secondaries are safety/biomarker only; the Circulation letter reports a *different* composite (death, HF rehospitalisation, LVAD, transplant listing). Registry evidence against, full text unread. |
| EVALUATE-HF | 31475296, NCT02874794 | aortic impedance | Medium — n=464, 12 weeks |
| OUTSTEP-HF | 33314487, 32468672, NCT02900378 | daily physical activity | Medium — n=621, 12 weeks |
| Halle 2021 exercise-capacity trial | 33992607, NCT02768298 | peak VO2 | Medium — n=201 |
| ACTIVITY-HF | 34591356 | peak VO2 | Medium |
| AWAKE-HF | 34428592, 32978755, 31638338, NCT02970669 | activity and sleep | Low — n=140, 12 weeks |
| Santos 2021 / NCT03190304 | NCT03190304 | exercise tolerance | Low — n=52 |
| NCT03917459 | NCT03917459 | erectile function | Low — n=27 |
| PMID 38508844 | 38508844 | unknown | **still undetermined** — abstract not yet retrieved |

Short-follow-up mechanistic trials (12 weeks, n<250) are unlikely to report a composite event HR, but "unlikely" is the reasoning that produced Conflict 1, so they are listed rather than dismissed.

**Not at risk, and not re-examined:** the ~100 outcome-axis exclusions that are secondary analyses of PARADIGM-HF or PARALLEL-HF. Both parent trials are already included; a subgroup or biomarker paper cannot add a study. If one reports a trial-level composite HR it is a duplicate report of an included estimate, which is a deduplication question, not an eligibility one.

**Also not at risk:** records excluded on POPULATION, INTERVENTION, COMPARATOR or RANDOMISATION. Those axes are visible in a title and are not defeated by a secondary endpoint. PANORAMA-HF fails population independently and is unaffected.

---

## Revised counts — provisional, and marked as such

| | As recorded | After adjudication so far |
|---|---|---|
| Records included | 4 | **6** (+41335448, +NCT04023227) |
| **Studies included** | **2** | **3** — PARADIGM-HF, PARALLEL-HF, **PARACHUTE-HF** |
| Undetermined | 2 | 2 (34395116 resolved to exclude; 41396086 downgraded to undetermined) |
| Outcome-axis exclusions still to re-examine at full text | — | 9 distinct trials |

k = 3, provisionally. PARACHUTE-HF contributes **HR 0.91 (0.73–1.13)** to the pool.

---

## Blocked lookup from the earlier run — now cleared

The HTTP 429 that blocked the ClinicalTrials.gov confirmatory read has lifted. Both lookups have now been performed, and they discharge the caveat in `03_PRISMA_AND_SCREENING_NOTES.md` §6:

- **NCT01035255** primary outcome measure: *"Number of Participants That Had **First Occurrence** of the Composite Endpoint, Which is Defined as Either Cardiovascular (CV) Death or Heart Failure (HF) Hospitalization."* Time-to-first structure confirmed at the registry.
- **NCT02468232** primary outcome measure: *"Number of Participants Who Had CEC Confirmed Composite Endpoints"*, described as *"either cardiovascular (CV) death or heart failure (HF) hospitalization."* Confirmed.

Recording the sequence honestly: it was blocked, it is now unblocked, and it was never an absence.
