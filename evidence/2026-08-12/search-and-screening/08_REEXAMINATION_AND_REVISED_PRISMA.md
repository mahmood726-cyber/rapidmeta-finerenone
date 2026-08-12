# Outcome-axis re-examination — complete. Revised PRISMA numbers.

Completed 2026-08-12. Overlay: `05_ADJUDICATION_OVERLAY.tsv` (19 rows). `02_CORPUS_AND_SCREENING.tsv` remains untouched.

---

## 1. Result of the re-examination

Every outcome-axis exclusion that cleared population, intervention and comparator has now been re-examined against **everything the trial reports**, not its primary. Twelve distinct trials were at risk.

| Trial | Primary (why it was excluded) | Everything else it reports | Evidence read | Verdict |
|---|---|---|---|---|
| **PARACHUTE-HF** | win ratio 1.52 | **HR 0.91 (0.73–1.13)** for the composite; LWYY RR 0.90; Fine-Gray sHR 0.74 | JAMA Table 2, PMC12676478 | **INCLUDE** — human adjudication, Mahmood, 13:30:45Z |
| **PIONEER-HF** | NT-proBNP change | registry outcome set has no composite — but Morrow 2024 reports the composite **adjudicated** in PIONEER-HF | registry + PMID 38508844 abstract | **UNDETERMINED** — NEJM text blocked |
| **ANSWER-HF** | LVEF change; win ratio 1.80 | registered outcome set is arrhythmia, remodelling and biomarker measures only | NCT04853758 outcome set | **UNDETERMINED** — JACC text blocked |
| Bano 2021 (34395116) | — | HF hospitalisation **RR 0.61 (0.39–0.97)**; HF death RR 0.47 (0.19–1.12); zero HR/Cox/Kaplan in text | Cureus full text, PMC8357012 | exclude OUTCOME — **confirmed** |
| Zhao 2022 (35874853) | pulmonary haemodynamics | MACE table: deaths 1 vs 1, readmissions 2 vs 1, mean hospital days; no composite, no HR | Pulm Circ full text, PMC9297686 | exclude OUTCOME — **confirmed** |
| EVERY mention of the composite is background citation of PARADIGM-HF in EVALUATE-HF (31475296) | aortic characteristic impedance | prior HF hospitalisation appears only as a baseline characteristic | JAMA full text, PMC6749534 | exclude OUTCOME — **confirmed** |
| ACTIVITY-HF / Halle 2021 (34591356) | peak VO2 at 12 wk | VE/VCO2 slope, ventilatory threshold, Borg, heart rate | abstract + registry | exclude OUTCOME — **confirmed** |
| Dos Santos 2021 (33992607) | peak VO2 | NCT02768298: results posted, 5 outcomes, none event-related | registry results module | exclude OUTCOME — **confirmed** |
| OUTSTEP-HF (33314487) | daily activity | NCT02900378: results posted, 20 outcomes, none event-related | registry results module | exclude OUTCOME — **confirmed** |
| AWAKE-HF (32978755) | activity and sleep | NCT02970669: results posted, 6 outcomes, none event-related | registry results module | exclude OUTCOME — **confirmed** |
| NCT03190304 | exercise tolerance | 5 outcomes, none event-related | registry | exclude OUTCOME — **confirmed** |
| NCT03917459 | erectile function | results posted, 3 outcomes, none event-related | registry | exclude OUTCOME — **confirmed** |

Across the six registry outcome sets checked programmatically, **51 registered outcome measures** contain no occurrence of *death*, *mortality*, *hospitalis/zation*, *composite* or *cardiovascular*. These are 12-week to 6-month mechanistic trials that register no event outcome at all.

### One previously-undetermined record resolved, and it is instructive

**PMID 38508844** — Morrow DA, et al., *JACC* 2024 — is a **pooled analysis of PIONEER-HF and PARAGLIDE-HF**. It reports *"Cardiovascular death or hospitalization for HF was reduced by 30%... HR: 0.70; 95% CI: 0.54-0.91"*.

That is a qualifying quantity attached to a **non-qualifying comparator and population**: control therapy is enalapril *or* valsartan depending on which trial the participant was in, and the population spans EF ≤40% and >40%. It is also not a single randomised trial. **Excluded on the comparator axis.**

It matters for a second reason: it is positive evidence that CV death or HF hospitalisation was **adjudicated within PIONEER-HF**. PIONEER-HF's own registry outcome set does not list it and its NEJM report has no PMC record, so I cannot see whether the trial reports it separately. Post-PARACHUTE, I will not exclude on the outcome axis from registry metadata when there is affirmative evidence pointing the other way. **PIONEER-HF is undetermined.**

---

## 2. Revised PRISMA numbers

```
IDENTIFICATION
  Records identified from databases ......................... 423
      PubMed (count read) .................................. 331
      ClinicalTrials.gov API v2 (totalCount read) ........... 92
  Records identified from backward citation (pass 1 of 45) .... 0
  Duplicate identifiers removed ............................... 0

SCREENING
  Records screened (title/abstract) ......................... 423
  Records excluded at title/abstract, as recorded by screener A  412
      of which subsequently overturned on adjudication ....... 1   (PARACHUTE-HF)

ELIGIBILITY
  Records assessed beyond title/abstract .................... 25
      published full text obtained and read .................. 4   (41335448, 34395116, 35874853, 31475296)
      resolved from registry outcome/results module + abstract  21
      full text sought but BLOCKED (no open access) ........... 7   (41396086, 30415601, 33314487, 32978755,
                                                                    34591356, 33992607, 38508844)
  Records excluded after full-text / beyond-abstract assessment 17

INCLUDED
  Records included ........................................... 6
  STUDIES included ........................................... 3
  Studies UNDETERMINED, pending blocked full text ............ 2
```

### The three included studies

| Study | Records | Estimand |
|---|---|---|
| PARADIGM-HF | 25176015, NCT01035255 | **HR 0.80 (0.73–0.87)**; 914/4187 vs 1117/4212; median 27 months |
| PARALLEL-HF | 33731544, NCT02468232 | **HR 1.09 (0.65–1.82)**, P=0.6260; n=225; median 33.9 months |
| **PARACHUTE-HF** | 41335448, NCT04023227 | **HR 0.91 (0.73–1.13)**, P=.40; 155/462 vs 169/460; median 25.2 months |

**k = 3**, up from the 2 recorded by screener A. At k=3 the protocol's §10 prediction interval is on 2 degrees of freedom and §12's small-study tests remain not assessable — both already anticipated in the registered method.

### The two undetermined studies

| Study | What is blocking it | Effect if it resolves to include |
|---|---|---|
| PIONEER-HF (n=881) | NEJM full text, no PMC record | k = 4 |
| ANSWER-HF (n=190) | JACC full text, no PMC record | k = 5 |

**Both are blocked sources, not absences.** Until they are read, **k = 3 is a lower bound**, and the pooled estimate should not be presented as final. Resolving them requires institutional access to two paywalled articles — that is the single highest-value unblocked action remaining.

---

## 3. What changed, and what did not

**Changed:** one study added by human adjudication; two undetermined records resolved (one to exclude, one contributing to a downgrade); two studies newly downgraded to undetermined; nine outcome-axis exclusions confirmed against the full set of reported quantities rather than the primary.

**Did not change:** the 423-record corpus, the two hit counts, the search timestamps, the ordering test, and every decision as originally recorded in `02_CORPUS_AND_SCREENING.tsv`. Screener A's wrong call on PARACHUTE-HF is still in that file, unedited. The adjudication overlay sits beside it.

**Still not run:** 44 of 45 flagged syntheses for backward citation; the FDA statistical review and EMA EPAR (§4's trigger is met only for ANSWER-HF, and the Entresto review package predates that trial, so it is the wrong source for the gap); RoB-2 under §9, which remains PENDING and requires two cross-family assessors, neither of them the agent that assembled the object.

**Still pending externally:** the second cross-family screener's independent pass over the same 423 records, and the agreement rate — which should be reported separately for the outcome-axis rows, where this run demonstrated the failure concentrates.
