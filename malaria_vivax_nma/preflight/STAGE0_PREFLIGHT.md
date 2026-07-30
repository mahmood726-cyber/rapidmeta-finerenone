# Stage 0 preflight — P. vivax radical cure NMA (recurrence at 180 days)

**Date:** 2026-07-30
**Branch:** `build/malaria-vivax-radical-cure-nma`
**Status:** PREFLIGHT COMPLETE — checkpoint before any app is built.
**Scoping input:** malaria NMA scoping memo (candidate C), prior lane, 2026-07-30.

**Sourcing rule.** Every identifier, count and date below was obtained by live lookup this
session — EMA downloadable medicines register (XLSX), EMA EU-M4all infographic, openFDA
Drugs@FDA API, the two FDA multi-discipline review PDFs, ClinicalTrials.gov API v2, WHO
prequalification WHOPAR, and NCBI E-utilities. Nothing is from recall. Titles were read back
from the source before any number was used. Items that could not be verified are recorded as
unresolved rather than filled in.

---

## 1. EMA status of tafenoquine (Kozenis) — RESOLVED

**Verdict: no EMA authorisation and no EMA scientific opinion found.**

| Route | Result | Evidence |
|---|---|---|
| EU centralised marketing authorisation | **None** | EMA downloadable medicines register (`medicines-output-medicines-report_en.xlsx`, 2,738 rows, sheet `Medicine`): **0 rows** matching `tafenoquine` or `kozenis` in any column. |
| EU-M4all / Article 58 scientific opinion | **Not among them** | EMA EU-M4all infographic (`infographic-medicines-use-outside-eu-eu-m4all_en.pdf`), which states **"138 approvals … based on eleven scientific opinions"** as of **July 2020** and names all eleven. Tafenoquine/Kozenis absent; the only malaria entries are **Mosquirix** and **Pyramax**. |

**Positive controls** (proving the register probe can detect a hit): `Eurartesim`
(piperaquine tetraphosphate; artenimol) — present, Authorised. `Artesunate Amivas`
(artesunate) — present, Authorised. So a zero result for tafenoquine is a real negative for the
centralised route, not a broken query.

**Register scope caveat, stated rather than hidden.** The same register returns **0** for
`Pyramax` and `fexinidazole`, both of which *are* Article 58/EU-M4all medicines. The register
therefore covers the EU centralised route only and **cannot by itself settle the Article 58
question** — which is why the EU-M4all infographic enumeration above is used as the second,
independent source.

**Negative control that failed and was discarded.** `https://www.ema.europa.eu/en/medicines?...&search_api_fulltext=<term>`
returns HTTP 200 with a byte-identical 73,799-byte page for `artesunate`, `tafenoquine`,
`kozenis`, `primaquine` and `eurartesim` alike — it is a client-rendered shell. **This endpoint
was not used as evidence**; it cannot distinguish present from absent.

**Corroboration (independent of EMA).** WHO prequalified tafenoquine on **2024-12-04**: MA203
(150 mg film-coated) and **MA204** (50 mg dispersible, *KOZENIS Dispersible*), both manufactured
by GlaxoSmithKline in Australia. The WHOPAR for MA204 records **TGA Australia** as the reference
stringent regulatory authority (AusPAR). Had an EMA Article 58 opinion existed it would be the
natural reference dossier; it is not cited.

**Residual uncertainty, recorded not smoothed over.** The EU-M4all enumeration is dated
**July 2020**. A post-July-2020 EU-M4all opinion would not appear in it. Sources 1 and 3 make
that unlikely but do not exclude it. **The app must therefore print "no EMA authorisation or
opinion found (verified 2026-07-30); regulator coverage for tafenoquine is FDA + TGA + WHO PQ",
and must not print "EMA-covered" or "no EMA opinion exists".**

---

## 2. The two FDA review packages

Both were pulled in full from Drugs@FDA (openFDA `drugsfda` API → review-package TOC → PDF).

| | KRINTAFEL | ARAKODA |
|---|---|---|
| NDA | **210795** | **210607** |
| Sponsor | GlaxoSmithKline | 60 Degrees Pharmaceuticals |
| Approved | **2018-07-20** | **2018-08-08** |
| Strength | tafenoquine succinate EQ 150 mg base | tafenoquine succinate EQ 100 mg base |
| Indication | **radical cure (relapse prevention) of P. vivax** | **prophylaxis** |
| Review format | Multi-Discipline Review (integrated: summary, office director, CDTL, clinical, non-clinical, statistical, clin-pharm) | Multi-Discipline Review |
| File | `210795Orig1s000MultidisciplineR.pdf`, 19.0 MB, 309 pp | `210607Orig1s000MultidisciplineR.pdf`, 19.8 MB, 353 pp |
| Reference ID | 4294788 | 4303418 |
| **Supplies network nodes?** | **YES** | **NO — see §2.3** |

### 2.1 Text-extraction hazard (recorded because it silently corrupts numbers)

The **210795** PDF ships subset fonts with a broken `ToUnicode` CMap. `pdftotext -layout`
returns readable-looking garbage (`E D Z Z E` for `NDA Multi-Disc…`) — it does **not** error, so
a naive pipeline would extract confident nonsense. Three distinct corruptions occur page by
page: clean ASCII (116 pp), a monoalphabetic glyph substitution (260 pp), and constant-offset
shifts (3 pp). `preflight/fda_decode.py` decodes per page by trying every candidate transform and
keeping whichever scores highest against an English word list, so the choice is evidence-driven.
Two glyphs (`B`/`H`) were initially mis-assigned; the word-score check caught them
("Hody weights" → "Body weights"). **210607 extracts cleanly and needed no decoding.**

### 2.2 NDA 210795 — arm-level recurrence data and the reviewer's own analysis

**DETECTIVE Part 1** = study **TAF112582 Part 1** — FDA Table 22/23, ITT, 6 months:

| Arm | N | Relapse-free at 6 mo, n (%) | Recurrence before Day 180, n (%) | Censored, n (%) | KM estimate % (95% CI) |
|---|---|---|---|---|---|
| CQ alone | 54 | 21 (39) | 31 (57) | 2 (4) | 37.5 (23, 52) |
| CQ + TQ 50 mg | 55 | 29 (53) | 22 (40) | 4 (7) | 57.7 (43, 70) |
| CQ + TQ 100 mg | 57 | 29 (51) | 25 (44) | 3 (5) | 54.1 (40, 66) |
| CQ + TQ 300 mg | 57 | 48 (84) | 6 (11) | 3 (5) | 89.2 (77, 95) |
| CQ + TQ 600 mg | 56 | 43 (77) | 4 (7) | 9 (16) | 91.9 (80, 97) |
| CQ + PQ 15 mg × 14 d | 50 | 34 (68) | 12 (24) | 4 (8) | 77.3 (63, 87) |

Total 329. Log-rank vs CQ alone: 0.048 (TQ 50, *not* significant after the step-down
procedure), 0.158, <0.0001, <0.0001, 0.0004.

**DETECTIVE Part 2** = **TAF112582 Part 2** — FDA Table 30, micro-ITT, 6 months:

| Arm | N | Recurrence-free at 6 mo, n (%) | Recurrence ≤6 mo, n (%) | Censored, n (%) | KM % (95% CI) | HR vs CQ alone (95% CI) |
|---|---|---|---|---|---|---|
| CQ alone | 133 | 35 (26) | 88 (66) | 10 (8) | 27.7 (19.6, 36.3) | ref |
| CQ + TQ 300 mg | 260 | 155 (60) | 85 (33) | 20 (8) | 62.4 (54.9, 69.0) | 0.299 (0.222, 0.404) |
| CQ + PQ 15 mg × 14 d | 129 | 83 (64) | 36 (28) | 10 (8) | 69.6 (60.2, 77.1) | 0.262 (0.178, 0.387) |

Total 522. FDA also reports censoring=failure HRs (0.346 / 0.312) and missing=failure ORs
(0.241 / 0.198) — **three different estimators of the same contrast**, which is a multiverse axis,
not a nuisance.

**GATHER** = **TAF116564** — FDA Tables 40/41, micro-ITT, 6 months:

| Arm | N | Recurrence-free, n (%) | Observed recurrence ≤6 mo, n (%) | Censored, n (%) | Missing=failure recurrence, n (%) | KM % (95% CI) |
|---|---|---|---|---|---|---|
| CQ + TQ 300 mg | 166 | 112 (67) | 42 (25) | 12 (7) | 54 (33) | 72.7 (64.8, 79.2) |
| CQ + PQ 15 mg × 14 d | 85 | 60 (71) | 20 (24) | 5 (6) | 25 (29) | 75.1 (64.2, 83.2) |

Total 251. HR of recurrence TQ vs PQ 0.984 (0.577, 1.678); missing=failure OR 1.141 (0.643, 2.027).

> **The reviewer's own analysis, verbatim in substance.** "According to an FDA analysis, the
> difference in recurrence-free efficacy proportions was **−3.4%** with a 95% CI **[−16.0%,
> 9.8%]**, indicating that CQ+TQ could be as much as 16% worse than CQ+PQ." Under the most
> conservative handling (PQ censored = successes, TQ censored = failures) the difference was
> **−9.0%, 95% CI [−21.4%, 3.4%]." FDA concluded CQ+TQ could meet a **22% non-inferiority
> margin**, smaller than the **26%** conservative CQ+PQ-vs-CQ-alone effect estimated from the
> earlier studies, and therefore called GATHER **"supportive evidence of efficacy"** — not
> independently confirmatory. This is a materially more guarded reading than the sponsor's, and
> it is the single most important thing the FDA leg contributes.

### 2.3 NDA 210607 (Arakoda) — supplies NO nodes, and this is a finding

Arakoda is a **prophylaxis** NDA. Its trials (Studies 033, 043, 045, 030, 057, TQ-2016-01/02)
randomise **uninfected** people and measure first occurrence of parasitaemia while taking weekly
prophylaxis. In 575k characters of extracted text the word `recurrence` occurs **once**. The 19
occurrences of `radical cure` are all either (a) an 18-day pre-randomisation *clearing phase*
(quinine → doxycycline → primaquine) before prophylaxis begins, or (b) a cross-reference to
NDA 210795. **No arm in NDA 210607 is eligible for a recurrence-at-180-days network.**

Its value to this build is real but different: tafenoquine PK/half-life (~17 days), dose
rationale, and a large independent safety database. It is a **provenance and safety asset, not
an evidence node**, and the app must say so rather than implying two FDA packages back the
efficacy network.

---

## 3. Five-way reconciliation: registry × publication × FDA

Legend: ✅ concordant · ⚠️ discrepancy recorded, not resolved · ❌ source absent.

### 3.1 DETECTIVE Part 1 — NCT01376167 (Lancet 2014;383:1049–58, PMID 24360369)

| Source | Arm Ns | 6-month efficacy |
|---|---|---|
| CT.gov results table | **❌ ABSENT** | **❌ ABSENT** |
| Publication | 55 / 57 / 57 / 56 / 50 / 54 | 57.7 / 54.1 / 89.2 / 91.9 / 77.3 / 37.5 |
| FDA Table 22 | 55 / 57 / 57 / 56 / 50 / 54 | 57.7 / 54.1 / 89.2 / 91.9 / 77.3 / 37.5 |

**Publication ↔ FDA: exact, to the decimal, including all six CIs.** ✅

> ⚠️ **Correction to the scoping memo.** The memo lists DETECTIVE Part 1 as "NCT01376167
> (results posted)". That is **half true and materially misleading**. NCT01376167's *protocol*
> section carries all nine arms (both Parts), but its **results section contains Part 2 only** —
> participant-flow groups are `CQ Only` 133 / `TQ + CQ` 260 / `PQ + CQ` 129. **Part 1 has no
> registry results table at all.** Part 1 is therefore a **two-source** trial (publication +
> FDA), not three-source, and its provenance tier must be set accordingly.

### 3.2 DETECTIVE Part 2 — NCT01376167 (N Engl J Med 2019;380:215–28, PMID 30650322)

| Source | CQ alone | CQ+TQ 300 mg | CQ+PQ |
|---|---|---|---|
| CT.gov (primary outcome, recurrence-free at 6 mo) | **35 / 133** | **155 / 260** | **83 / 129** |
| FDA Table 30 | **35 (26) / 133** | **155 (60) / 260** | **83 (64) / 129** |
| Publication | 133 | 260 | 129 (total 522) |

**Three-way exact concordance on both numerator and denominator.** ✅ This is the strongest cell
in the network and should anchor the integrity gates.

### 3.3 GATHER — NCT02216123 (N Engl J Med 2019;380:229–41, PMID 30650326)

| Source | CQ+TQ | CQ+PQ |
|---|---|---|
| CT.gov participant flow | started 166, completed 160 | started 85, completed 83 |
| CT.gov outcome (KM %, 95% CI) | **72.7 (64.8, 79.2)** | **75.1 (64.2, 83.2)** |
| FDA Table 40 (KM %, 95% CI) | **72.7 (64.8, 79.2)** | **75.1 (64.2, 83.2)** |
| FDA Table 41 counts | 112 (67) free / 54 (33) recur, N=166 | 60 (71) free / 25 (29) recur, N=85 |

Registry ↔ FDA exact on KM; registry supplies **no raw counts**, FDA does. ✅

> ⚠️ **Double-counting trap — hard extraction rule required.** GATHER's *abstract* headline is
> **not** GATHER. It reports "the percentage of patients free from recurrence at 6 months was
> **67.0%** among the **426** patients in the tafenoquine group and **72.8%** among the **214**
> patients in the primaquine group … odds ratio 1.81 (0.82, 3.96)". **426 = 260 + 166** and
> **214 = 129 + 85** — this is a pre-planned **patient-level meta-analysis pooling GATHER with
> DETECTIVE Part 2**. Extracting it as GATHER's result imports DETECTIVE Part 2 a second time.
> GATHER's own trial-specific odds ratio is **1.141 (0.643, 2.027)**, not 1.81. **The extraction
> tab must show both numbers and state which one enters the network and why.**

> ⚠️ **Two event definitions inside one trial.** Observed recurrence (42 / 20) and
> missing=failure recurrence (54 / 25) differ by exactly the censored counts. Both are defensible;
> they must be a declared multiverse axis, not an unlabelled choice.

### 3.4 INSPECTOR — NCT02802501 (Lancet Infect Dis 2023;23:1153–63, PMID 37236221)

| Arm (N=50 each) | CT.gov 6-mo relapse-free | Publication 6-mo KM (95% CI) |
|---|---|---|
| DHA-PQP alone | **12%** | **11% (4–22)** ⚠️ |
| TQ 300 mg + DHA-PQP | **22%** | **21% (11–34)** ⚠️ |
| PQ 15 mg × 14 d + DHA-PQP | **52%** | **52% (37–65)** ✅ |

> ⚠️ **Registry ↔ publication disagree by 1 percentage point on two of three arms.** Both are
> labelled 6-month relapse-free efficacy on the micro-ITT population, N=50 per arm. One
> percentage point at N=50 is half a patient, so the two sources cannot both be a simple
> proportion. **This is recorded as an open discrepancy; neither value is silently preferred.**
> FDA has no INSPECTOR data (2023 trial, post-dates both 2018 NDAs) — so there is **no third
> source to break the tie**. Resolution requires the publication's own count table; until then
> the app must show both and mark the cell contested.

> ⚠️ **Unit trap.** CT.gov types this outcome `Percentage of participants` while the analogous
> DETECTIVE Part 2 outcome is typed `Participants` (a count). A single extractor reading
> "12 / 22 / 52" as counts would produce 12/50, 22/50, 52/50 — the last being impossible.
> **Every extraction row must carry the source's own unit string as a typed field.**

Corroborating registry signal: the open-label extension period enrolled **6 / 12 / 26**
participants by arm, consistent with roughly 12% / 22–24% / 52% remaining relapse-free.

### 3.5 IMPROV — NCT01814683 (Lancet 2019;394:929–38, PMID 31327563)

| Source | Status |
|---|---|
| CT.gov results table | **❌ ABSENT** — `hasResults: false`. Protocol only. |
| FDA | **❌ ABSENT** — investigator-led, not in either NDA |
| Publication | sole source |

| Arm | N (published) | Outcome as reported |
|---|---|---|
| PQ 7 d high dose (1.0 mg/kg/d, 7 mg/kg total) | 935 | 0.18 (0.15–0.21) recurrences / person-year |
| PQ 14 d high dose (0.5 mg/kg/d, 7 mg/kg total) | 937 | 0.16 (0.13–0.18) recurrences / person-year |
| Placebo (no hypnozoiticidal therapy) | 464 | 0.96 (0.83–1.08) recurrences / person-year |

> ⚠️ **Enrolment discrepancy.** CT.gov records actual enrolment **2,388**; the publication
> reports **2,336** enrolled (935 + 937 + 464 = 2,336, internally consistent). A 52-participant
> gap. Recorded, not reconciled.

> 🛑 **BLOCKING for the primary estimand, and this is the most consequential Stage 0 finding.**
> IMPROV reports an **incidence rate per person-year over ~12 months**, not a binary
> **recurrence-by-180-days** proportion. These are different estimands and one cannot be derived
> from the other without arm-level 180-day counts, which the abstract does not contain. IMPROV is
> the **primaquine-regimen backbone** of the intended node set — it is the trial that supplies
> the PQ 7 d vs PQ 14 d contrast **and** a no-therapy anchor at scale. **Stage 1 must obtain the
> arm-level 180-day counts from the open-access full text (PMC6753019) before the network can be
> built. If they are not recoverable, the PQ 7 d ↔ PQ 14 d edge does not exist at the primary
> estimand and the node set must be revised — it must not be back-derived from the rate.**

### 3.6 Two further trials checked (both fail the primary estimand — recorded now, not later)

**NCT04706130** (Eng V et al., Lancet Infect Dis 2025;25:884–95) — arms: artesunate alone
(no PQ) 61 started/59 analysed; PQ 0.25 mg/kg/d × 14 d 49/45; PQ 0.5 mg/kg/d × 14 d 46/43.
Recurrence **48 / 11 / 2**. ⚠️ **Time frame is 3 months, not 180 days** → fails the horizon axis.
Also the partner drug is **artesunate monotherapy**, not chloroquine or an ACT — a distinct
partner-drug stratum. Useful for the horizon and partner-drug multiverse cells; **not** for the
primary 180-day network.

**NCT02563496** (paediatric PK/efficacy) — five weight-band dose groups, **no control arm**;
the 50 mg band enrolled **0** participants (14 / 5 / 22 / 19 = 60). Only a **4-month**
relapse-free outcome is posted. Single-arm and off-horizon → **cannot be a comparative node**.
Confirms the memo's warning that the paediatric subnetwork is not supportable; a paediatric node
must not inherit adult-network certainty.

---

## 4. Pre-declared multiverse inclusion presets

Fixed **now**, before any model is fitted, so no cell is post-hoc. Each preset names the
red-flag it discharges (C-numbers from the scoping memo).

| # | Axis | Levels | Discharges | Pre-declared rationale |
|---|---|---|---|---|
| **P1** | **Follow-up horizon** | (a) 180 d only *(primary)* · (b) ≥120 d admitted · (c) any horizon, horizon as covariate | C-6 | A 28-d or 90-d horizon cannot detect hypnozoite relapse. Fixes whether NCT04706130 (3 mo) and NCT02563496 (4 mo) enter. |
| **P2** | **Relapse periodicity / region** | (a) tropical frequent-relapse (SE Asia, Oceania, Papua, Amazonia) · (b) temperate long-latency (Korea, Türkiye, Central Asia) · (c) pooled with region as meta-regression covariate | C-2 | Same regimen shows different 180-d recurrence by strain phenotype. Must be a covariate, never a post-hoc subgroup. |
| **P3** | **Partner blood-stage drug** | (a) chloroquine-partner only *(primary)* · (b) DHA-PQ-partner only · (c) any ACT partner · (d) pooled with partner as covariate | C-4, C-5 | Piperaquine's prophylactic tail masks early recurrence past day 42. INSPECTOR is the direct evidence that this changes the TQ estimate. Splits INSPECTOR from DETECTIVE/GATHER. |
| **P4** | **G6PD eligibility regime** | (a) G6PD-screened, ≥70% activity required *(primary)* · (b) screened + moderate-deficient females admitted (GATHER's design) · (c) unscreened | C-3 | A network pooling screened and unscreened populations answers two different questions. |
| **P5** | **Total-dose node scheme** | (a) total mg/kg *(primary: 3.5 vs 7 mg/kg)* · (b) daily dose × duration as distinct nodes | C-9 | PQ 7 d @1.0 mg/kg/d and PQ 14 d @0.5 mg/kg/d both deliver **7 mg/kg total**. Under (a) they merge; under (b) they don't. Pre-declaring this prevents the classic unit bug. |
| **P6** | **Administration supervision** | (a) supervised only · (b) unsupervised/real-world only · (c) pooled | C-7 | Single-dose TQ vs 14-day PQ is a comparison whose whole practical value is adherence. Must not be averaged away. |
| **P7** | **Single-edge nodes** | (a) retained · (b) dropped *(TQ 50/100/600 mg, paediatric)* | memo §"sparse edges" | TQ 50/100/600 rest on one trial each; the paediatric node on n=60 with no control. |
| **P8** | **Censoring / missing-data rule** | (a) observed recurrence · (b) missing = failure · (c) censoring = failure | §3.3, §2.2 | DETECTIVE Pt 2 and GATHER each report all three. FDA's own conclusion moved with this choice (−3.4% → −9.0%). |

**Eight cells** for the headline grid = the eight axes above at their primary vs first-alternative
level, matching the HFrEF eight-cell format. Full factorial is reported in the ledger, not the badge.

---

## 5. Pre-registered adversary targets (irreducible limits, declared before fitting)

1. **Recurrence ≠ relapse, and PCR cannot fix it.** Unlike falciparum, **PCR genotyping does not
   separate vivax relapse from reinfection**, because hypnozoites are frequently genetically
   heterologous to the primary infection. Relapse, reinfection and recrudescence are not
   separable in endemic settings. The estimand is therefore **recurrence by 180 days** and the
   ambiguity is **irreducible**, not a limitation to be worked around. Cochrane CD010458.pub3
   reports recurrence as a proxy for relapse for the same reason. The app must name the estimand
   as recurrence everywhere — including in the badge — and must never label it relapse.
2. **The partner blood-stage drug confounds the anti-hypnozoite estimate.** Chloroquine, DHA-PQ
   and AL have very different post-treatment prophylactic tails; piperaquine suppresses early
   recurrence well past day 42. INSPECTOR tested exactly this and tafenoquine did **worse** with
   DHA-PQ (21%) than the CQ-partner trials would predict. Any pooled "tafenoquine effect" that
   ignores partner drug is confounded by construction. P3 exists to make this visible.
3. **Chloroquine-alone is not a placebo.** Treating the CQ-alone arm as an inert anchor is wrong
   where chloroquine-resistant vivax circulates (Indonesia/Papua, parts of Oceania) — a
   "recurrence" there may be blood-stage CQ failure, not relapse. The second place a hostile
   reviewer lands.
4. **CYP2D6 is differential effect modification across nodes.** Primaquine requires CYP2D6
   activation; tafenoquine does not. Poor-metaboliser frequency varies by population, so
   primaquine efficacy is population-dependent in a way tafenoquine efficacy is not. This is the
   worst class of effect modification for an NMA — it breaks transitivity between the PQ and TQ
   nodes specifically, not uniformly.
5. **The approved tafenoquine dose is itself contested.** Watson et al. (eLife 2022) vs Sharma
   et al. (eLife 2024, PMID 38323802) dispute whether 300 mg is adequate versus 450 mg. The
   multiverse is the honest response to a contested dose.

---

## 6. Verdict going into Stage 1

Preflight **passes with two conditions**, both of which change what can be built:

1. **IMPROV's 180-day arm-level counts must be recovered from the open-access full text before
   the network is fitted.** Without them the PQ 7 d ↔ PQ 14 d edge does not exist at the primary
   estimand. If they cannot be recovered, the node set is revised and the gap is reported — the
   rate is **not** to be converted into a proportion.
2. **INSPECTOR's registry-vs-publication 1-point discrepancy has no third source** and stays
   marked contested until the publication's count table is read.

Confirmed assets: DETECTIVE Part 2 is exactly three-way concordant; DETECTIVE Part 1 and GATHER
are exactly two-way concordant with FDA supplying raw counts the registry lacks; the FDA
reviewer's independent re-analysis of GATHER is in hand and is more guarded than the sponsor's.

Confirmed subtractions from the scoping memo's optimism: NDA 210607 supplies **no** nodes;
DETECTIVE Part 1 has **no** registry results; IMPROV and the paediatric trial have **no**
registry results; NCT04706130 and NCT02563496 **fail the 180-day horizon**.
