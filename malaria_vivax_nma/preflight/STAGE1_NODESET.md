# Stage 1a — IMPROV determination, revised node set, connectivity

**Date:** 2026-07-30 · **Branch:** `build/malaria-vivax-radical-cure-nma`
**Status:** node set frozen. Checkpoint before any app code is written.

---

## 1. IMPROV — arm-level 180-day counts are NOT RECOVERABLE

Full text retrieved (PMC6753019, CC BY, via PubMed Central BioC). **Table 3 reports incidence
risk at exactly three horizons: 28 days, 42 days, and 1 year. There is no 180-day or 6-month
row anywhere in the paper.**

Every occurrence of "6 month" in the full text was checked. All are non-efficacy:
a quality-control slide-reading visit, and blinded DSMB safety reviews every 6 months. Both
occurrences of "180" are bodyweight-category counts in Table 1.

| Arm | n | Day 28 risk | Day 42 risk | **1-year risk** |
|---|---|---|---|---|
| PQ 1.0 mg/kg/d × 7 d (7 mg/kg) | 935 | 0.23% | 0.87% | **14.28% (11.75–17.29)** |
| PQ 0.5 mg/kg/d × 14 d (7 mg/kg) | 937 | 0.33% | 0.82% | **12.72% (10.19–15.82)** |
| Placebo | 464 | 1.71% | 7.88% | **48.73% (43.40–54.36)** |

**Decision: IMPROV is excluded from the primary 180-day network.** The person-year rate is
**not** back-converted, and the 180-day risk is **not** interpolated between the day-42 and
1-year points. Both would be fabrication.

Three things IMPROV still contributes, recorded rather than discarded:

- **It validates the total-mg/kg node scheme (P5) directly.** Mean total dose was **7.39 mg
  base/kg in both** the 7-day and 14-day arms (7.53 and 7.54 mg/kg among completers). The two
  regimens really do deliver the same total dose — the premise of P5(a) is now measured, not
  assumed.
- **It contains an internal partner-drug confound (P3).** "At the two Indonesian sites, the
  incidence risks … were 39.33% and 28.59% after treatment with **dihydroartemisinin-piperaquine
  alone** compared with incidence risks of more than 50% at the other sites, **where chloroquine
  was used**." IMPROV is not a single-partner trial.
- **The enrolment discrepancy is now better characterised.** Publication: 2,338 enrolled, 2 withdrew
  consent before randomisation, **2,336 randomised** (935 + 937 + 464). Registry: **2,388**.
  Registry-vs-publication gap is against the *enrolled* figure (2,388 vs 2,338) and is consistent
  with a digit transposition — but that is an observation, **not a reconciliation**. Recorded as
  an open discrepancy.

---

## 2. The loss is repaired — EFFORT supplies the PQ 7-day node at the correct estimand

Looked up because IMPROV's exclusion removed the only PQ 7-day source.

**EFFORT** — Degaga TS et al. *Lancet Infect Dis* 2026;26(6):614–26, PMID **41690325**,
DOI 10.1016/S1473-3099(25)00729-7, **NCT04411836** (`hasResults: false` — publication-only).
Title read back from both registry and publication.

Primary endpoint is **cumulative incidence of any P. vivax parasitaemia within 6 months** —
exactly the target estimand. 960 randomised 1:1:1; mITT 295 / 305 / 301.

| Arm | mITT n | First recurrences, n | Crude risk | **KM cumulative incidence at 6 mo (97.55% CI)** |
|---|---|---|---|---|
| PQ 7 d high dose (**7 mg/kg total**), unsupervised | 295 | **34** | 11.5% | **13.0% (9.0–18.5)** |
| TQ 300 mg single dose | 305 | **35** | 11.5% | **12.6% (8.8–18.0)** |
| PQ 14 d low dose (**3.5 mg/kg total**), unsupervised | 301 | **49** | 16.3% | **18.5% (13.8–24.6)** |

HRs vs PQ 14 d low: 0.66 (0.40–1.09) p=0.063 for PQ 7 d; **0.64 (0.39–1.05) p=0.041** for TQ.
TQ vs PQ 7 d: 0.96 (0.56–1.66). Note the **97.55% CIs** (alpha spent on an interim look) — a
typed field, not a 95% CI.

Two findings from EFFORT that independently corroborate pre-registered adversary targets:

- **Partner-drug confound (target #2), replicated.** "In Indonesia, where tafenoquine was combined
  with dihydroartemisinin–piperaquine, the cumulative incidence … was higher in the tafenoquine
  group (**22.4%**)." This reproduces INSPECTOR's signal in a completely independent trial.
- **Recurrence ≠ relapse (target #1), now with data.** Post-hoc genotyping of paired isolates found
  homologous recurrences in only **9/24 (37.5%)**, **11/23 (47.8%)** and **12/31 (38.7%)** of
  recurrences by arm. **The majority of recurrences were heterologous** — direct empirical support
  that genotyping does not resolve vivax relapse and that the estimand must remain *recurrence*.

Also recorded: median tafenoquine dose **5.4 mg/kg**, relevant to the Watson-vs-Sharma
300 mg dose-adequacy dispute.

**Correction to the scoping memo, carried forward.** The memo said EFFORT "closes the TQ↔PQ loop
for a consistency check". EFFORT does supply the PQ 7-day node and a within-trial TQ/PQ7/PQ14
triangle, but because it is the **sole** source of both PQ 7-day edges, that triangle is
within-trial and **cannot be node-split**. EFFORT's actual contribution to consistency checking is
different and still valuable: it is a **fifth independent estimate of the TQ 300 vs PQ 3.5 edge**.

---

## 3. INSPECTOR's contested cell — RESOLVED with evidence

Full text retrieved (PMC10533414, CC BY). Table 2 gives the raw counts the registry lacked:

| Arm | n | Relapse-free, n (%) | Relapsed, n (%) | KM estimate (95% CI) |
|---|---|---|---|---|
| DHA-PQP alone | 50 | **6 (12%)** | 44 (88%) | 11.2% (4.2–22.1) |
| TQ 300 mg + DHA-PQP | 50 | **11 (22%)** | 39 (78%) | 21.0% (10.7–33.6) |
| PQ 15 mg × 14 d + DHA-PQP | 50 | **26 (52%)** | 24 (48%) | 52.0% (37.4–64.7) |

**The registry and the publication were never in conflict — they report different estimators.**
CT.gov posted the **crude proportions** (6/50 = 12%, 11/50 = 22%, 26/50 = 52%); the abstract
quoted the **Kaplan-Meier estimates** (11.2%, 21.0%, 52.0%). This confirms the Stage 0 reasoning
that one percentage point at N=50 is half a patient, so at least one source could not be a simple
proportion — it was the KM one. Both values are correct and both are now typed.

**The `T2_CONTESTED` tier is lifted to `T2`.** Two further items captured from the full text:

- **Proportional hazards is violated** for the TQ-vs-PQ comparison; the authors state the HR is
  "considered unreliable" and use the odds ratio instead: **OR of relapsing 4.57 (1.75–11.97)**
  for TQ vs PQ with a DHA-PQ partner. A single pooled HR on this edge would be misleading.
- **CYP2D6 (adversary target #4) was measured**: 67/150 (45%) were poor or intermediate
  metabolisers, with no significant effect on 6-month relapse-free efficacy in any group.

---

## 4. Two further trials screened, both excluded — recorded, not quietly dropped

A registry sweep (CT.gov API v2: vivax ∩ primaquine/tafenoquine ∩ completed ∩ results-posted)
surfaced three records not in the scoping memo. Two are excluded, one is a genuine find:

- **NCT02043652** — single-arm (no randomised allocation), CQ+PQ only, n=119. No contrast.
  **Excluded.**
- **NCT04222088** — **observational** therapeutic-efficacy study, 28-day ACPR only.
  **Excluded.**
- **NCT03610399** — *Efficacy of 3 Regimens of Chloroquine and Primaquine, Cruzeiro do Sul, Acre,
  Brazil*; randomised, n=257, results posted. Arms: PQ 3.5 mg/kg **unsupervised**, PQ 3.5 mg/kg
  **supervised**, PQ **7.0 mg/kg** (14 d). Day-168 ACPR: **29/53, 44/78, 67/79**.
  **Excluded from the primary network: the horizon is 168 days, not 180.** It enters the P1(b)
  (≥120 d admitted) multiverse cell only. Two integrity flags recorded against its registry entry:
  (i) the arm labelled "Double Dose **Unsupervised**" is described as "**with** directly observed
  therapy" — the registry contradicts itself; (ii) the microsatellite-corrected secondary outcome
  reports **identical numerators** (29 / 44 / 67) to the uncorrected primary but **different
  denominators** (41 / 61 / 71), which a genotype-corrected analysis should not produce.

**Curavivax** (PMID 42114535, NCT03208907) — primary outcome is **day-42** recurrence.
**Fails the horizon; excluded from the primary network.** Not open-access via PMC.

---

## 5. FINAL NODE SET — primary network (recurrence by 180 days)

### Nodes present (7), keyed by TOTAL mg/kg

| # | Node | Total dose | Source trials |
|---|---|---|---|
| 1 | **No hypnozoiticidal therapy** (blood-stage drug alone) | 0 mg/kg | DETECTIVE Pt1, Pt2, INSPECTOR |
| 2 | **PQ 14 d low** | **3.5 mg/kg** | all five |
| 3 | **PQ 7 d high** | **7 mg/kg** | EFFORT |
| 4 | **TQ 50 mg** | single dose | DETECTIVE Pt1 |
| 5 | **TQ 100 mg** | single dose | DETECTIVE Pt1 |
| 6 | **TQ 300 mg** | single dose | all five |
| 7 | **TQ 600 mg** | single dose | DETECTIVE Pt1 |

### Nodes the scoping memo proposed that DO NOT SURVIVE — declared absent, not improvised

| Proposed node | Why it is absent at the primary estimand |
|---|---|
| **PQ 14 d high (7 mg/kg over 14 d)** | Appears only in NCT04706130 (**3-month** horizon) and NCT03610399 (**168-day** horizon). Both fail P1(a). **No 180-day evidence exists for this node.** |
| **PQ weekly × 8 weeks** | No eligible trial found at any horizon in this evidence base. |
| **Paediatric TQ** | NCT02563496 is single-arm, 4-month, and its 50 mg band enrolled zero participants. |
| **TQ + partner-drug split node** | Handled as covariate axis P3 rather than as separate nodes, so the TQ 300 node is not fragmented below the point of estimability. |

This is a **revision of the memo's 7–8 node proposal**: two of its proposed primaquine nodes have
no 180-day evidence. The network is smaller and more honest than scoped.

### Trials in the primary network

| Trial | mITT/ITT n | Nodes contributed | Partner drug | Design | Counts? |
|---|---|---|---|---|---|
| DETECTIVE Pt 1 | 329 | 1, 2, 4, 5, 6, 7 | chloroquine | double-blind | ✅ |
| DETECTIVE Pt 2 | 522 | 1, 2, 6 | chloroquine | double-blind | ✅ |
| GATHER | 251 | 2, 6 | chloroquine | double-blind | ✅ |
| INSPECTOR | 150 | 1, 2, 6 | DHA-piperaquine | double-blind | ✅ |
| EFFORT | 901 | 2, 3, 6 | **mixed** (CQ / DHA-PQ / AS-pyronaridine) | **open-label** | ✅ |

**Total N in the primary network = 2,153.** Arm-level binary counts are available for **all five**
trials, so an arm-based binary NMA is feasible across the whole network — no trial needs to enter
on contrast-level data alone.

---

## 6. CONNECTIVITY — confirmed connected, with one genuine consistency check

**Verdict: a single connected component containing all 7 nodes.** No node is isolated; no
disconnected subnetwork.

### Edge multiplicity

| Edge | # independent trials |
|---|---|
| **TQ 300 ↔ PQ 3.5** | **5** (Pt1, Pt2, GATHER, INSPECTOR, EFFORT) |
| No-therapy ↔ PQ 3.5 | 3 (Pt1, Pt2, INSPECTOR) |
| No-therapy ↔ TQ 300 | 3 (Pt1, Pt2, INSPECTOR) |
| PQ 7 d high ↔ PQ 3.5 | **1** (EFFORT) |
| PQ 7 d high ↔ TQ 300 | **1** (EFFORT) |
| TQ 50 / 100 / 600 ↔ {no-therapy, PQ 3.5, TQ 300} | **1** (DETECTIVE Pt1) |

### Leave-one-trial-out robustness — the load-bearing result

A "testable loop" verdict inferred from graph shape alone is unreliable, because a three-arm
trial closes its own triangle while being internally consistent by construction: a shape-only
rule reports inconsistency information that does not exist. (An earlier version of
`check_network.py` did exactly that and called EFFORT's within-trial triangle testable; the rule
was replaced.) What is defensible is asking what survives when each trial is removed:

| Trial dropped | Nodes still connected | Lost |
|---|---|---|
| DETECTIVE Pt 1 | 4 / 7 | **TQ 50, TQ 100, TQ 600** |
| DETECTIVE Pt 2 | 7 / 7 | — |
| GATHER | 7 / 7 | — |
| INSPECTOR | 7 / 7 | — |
| EFFORT | 6 / 7 | **PQ 7 d high** |

> **ROBUST CORE — the subnetwork surviving removal of any single trial:**
> **{no-therapy, PQ 3.5, TQ 300}. Three nodes.**

**Only 3 of 17 edges carry direct evidence from more than one trial**, and they are exactly the
three edges of that core: TQ 300 ↔ PQ 3.5 (5 trials), no-therapy ↔ PQ 3.5 (3), no-therapy ↔ TQ 300
(3). All 14 remaining edges are single-trial.

**Honest summary.** The network is connected across all 7 nodes, but that connectivity is thin.
Cross-trial comparison — and therefore any assessment of heterogeneity or inconsistency — is
possible **only within the 3-node core**. The TQ dose-ladder nodes stand or fall with DETECTIVE
Part 1; the PQ 7-day node stands or falls with EFFORT. These are the single-edge nodes preset
**P7** exists to switch off, and the app must present the 7-node network and the 3-node robust
core as two distinct claims rather than implying a densely cross-validated network.

---

## 7. Four flagged discrepancies carried forward into the app

1. **DETECTIVE Part 1 is two-source only.** NCT01376167's results section holds **Part 2 only**.
   Part 1 has no registry results table; publication and FDA agree exactly. Tier T2, not T1.
2. **GATHER: use OR 1.141 (0.643, 2.027), never the pooled 1.81.** The abstract's 67.0% of 426 vs
   72.8% of 214 is a patient-level meta-analysis pooling GATHER with DETECTIVE Pt 2
   (426 = 260+166; 214 = 129+85). Extracting it double-counts DETECTIVE Pt 2.
3. **INSPECTOR — resolved, and the resolution is displayed.** Registry = crude proportion,
   abstract = Kaplan-Meier. Both correct, both typed. Plus: proportional hazards violated on the
   TQ-vs-PQ contrast (authors use OR 4.57 [1.75–11.97] instead).
4. **Arakoda (NDA 210607) supplies ZERO efficacy nodes.** It is a prophylaxis NDA. The app must
   **not** imply two FDA packages back the network; only NDA 210795 does.

---

## 8. Residual limits to state in the app, not paper over

- **Mixed estimators within the network.** Crude proportions, Kaplan-Meier cumulative incidence and
  hazard ratios coexist; KM exceeds crude wherever censoring is non-trivial. Preset **P8** makes
  the choice explicit rather than silent.
- **EFFORT is open-label**; the other four are double-blind. A risk-of-bias axis, and EFFORT is
  also the trial deliberately measuring *effectiveness* (unsupervised dosing) rather than efficacy
  — preset **P6**.
- **EFFORT reports 97.55% CIs**, not 95%. Must be converted on the log-HR scale using the correct
  quantile, never treated as 95%.
- **Partner drug is not cleanly stratified.** EFFORT and IMPROV each mix partner drugs *within* the
  trial, so P3 cannot be a clean trial-level split for those.
- **The no-therapy node is not a placebo node.** In DETECTIVE Pt1/Pt2 it is chloroquine alone; in
  INSPECTOR it is DHA-piperaquine alone. These have different post-treatment prophylactic tails —
  adversary target #3.
