# The synthesis frame was short; a broader index sweep; and the CSR layer

2026-08-12. Corpus-wide work: making sure the right trials are included and all the data is found.

---

## 1. The synthesis frame was short by a factor of five

My backward-citation null rested on a frame of **45 syntheses**, assembled from records the registered PubMed string happened to return. Two on-topic syntheses were found outside it, which meant the frame was demonstrably incomplete — and a recall estimate measured against an incomplete frame overstates recall.

A dedicated search for syntheses of this comparison was run against PubMed at **2026-08-12T15:20:58.705Z** (response 15:20:59.086Z), no language or date filter:

```
(sacubitril[tiab] OR "LCZ696"[tiab] OR Entresto[tiab] OR "angiotensin receptor neprilysin"[tiab] OR ARNI[tiab])
AND ("heart failure"[MeSH Terms] OR "heart failure"[tiab] OR HFrEF[tiab])
AND (systematic review[pt] OR meta-analysis[pt] OR "systematic review"[tiab] OR "meta-analysis"[tiab]
     OR "meta analysis"[tiab] OR "network meta-analysis"[tiab] OR "evidence synthesis"[tiab])
```

**Hit count: 244** (read from `esearchresult.count`).

| | |
|---|---|
| Syntheses in the frame I used | 45 |
| Syntheses retrievable by a dedicated search | **244** |
| Of the 244, already flagged | 43 |
| **Not previously in the frame** | **201** |

**My frame was 18% of the retrievable syntheses.** The null result reported earlier — zero eligible trials missed across 44 syntheses — was measured against a frame five times too small. It is not withdrawn, but it is now known to be a weaker test than it was presented as.

**Method note:** this search is *not* part of the registered §5 string. §5 registers "every retrievable synthesis of this comparison" as the input without specifying how to retrieve them. Constructing a search to enumerate that set is executing §5, but the string itself is unregistered and post-dates the search. It is recorded here rather than slipped into the protocol.

**Status: the diff against the 201 new syntheses has NOT been run.** See §3 for why.

---

## 2. A broader-index sweep — the first genuine breadth failure of the day

Rather than only asking "did the field's reference lists contain anything we lack", I ran the direct completeness test my own caveat demanded: query an index **broader than PubMed** and diff. Europe PMC indexes MEDLINE plus PMC, preprint servers, and other sources.

Query, title/abstract-scoped so it is comparable to the registered string, executed 2026-08-12T15:22Z:

```
(TITLE:"sacubitril" OR ABSTRACT:"sacubitril" OR TITLE:"LCZ696" OR ABSTRACT:"LCZ696"
 OR TITLE:"Entresto" OR ABSTRACT:"Entresto")
AND (TITLE:"enalapril" OR ABSTRACT:"enalapril")
```

| | |
|---|---|
| Records retrieved | **324** |
| Already in our 423-record corpus | 223 |
| **NOT in our corpus** | **101** |

Of the 101, three are randomised-trial-typed or have "random*" in the title, and **seven are preprints**:

| Record | What it is | Eligible? |
|---|---|---|
| **PPR1271024** — *Sacubitril-valsartan Versus Enalapril or Losartan at Guideline-Recommended Maximum Dosages in HFrEF: Real-World Results from the BEAT-HF Cohort* (2025-12-08) | preprint; **observational cohort**, n=254 at max dosages, propensity-matched; primary outcome combined hospitalisation or death, **OR 0.650 (0.354–1.195)** | **No** — fails randomisation. Reports an odds ratio, not the estimand. |
| 32732515 (2021) | RCT, sacubitril/valsartan on ventricular remodelling after acute anterior MI | No — population |
| 39983618 (2025) | sacubitril/valsartan or enalapril on LV function in haematologic malignancies on bortezomib | No — population |
| PPR154201, PPR339479, PPR101063, PPR51899, PPR801428 | economic evaluation; very-low-dose case series; observational parameters; retrospective study; a drug-class preprint | No |

**Eligible randomised trials still missed: zero.** But this is the first test that found *records* the registered strategy cannot see at all, and it identifies the layer: **preprints**. Neither registered database indexes them, and backward citation cannot reach them because preprints are rarely cited. PPR1271024 is directly on the review's comparison and would have been invisible to every step run before this one.

It happens to be ineligible. That is luck, not method.

**Recommended amendment 4** (to be drafted alongside the other three, and equally marked as post-dating the search): add a preprint-indexing source to §4. Europe PMC covers bioRxiv, medRxiv, Research Square and SSRN in one query and is free.

---

## 3. Obstacle: OpenAlex budget exhausted mid-task

The OpenAlex route — the one that let 19 paywalled syntheses be diffed via `referenced_works` — stopped working partway through this session:

```
{"error":"Rate limit exceeded","message":"Insufficient budget. This request costs $0.001
 but you only have $0 remaining. Resets at midnight UTC."}
```

The earlier harvest consumed the free daily allowance. **The backward-citation diff against the 201 newly-found syntheses could not be run today.** Named as a blocked route with a known reset time, not as a completed step and not as an absence. I did not pay for credits or route around the limit.

Resuming after 00:00 UTC, the work is: 201 syntheses → `referenced_works` → resolve → diff. That closes the frame properly.

---

## 4. The CSR layer — route mapped, and one door is shut for a structural reason

The find that prompted this: **Byrne D, et al., *HRB Open Research*** — *"Efficacy and safety of sacubitril/valsartan in the treatment of heart failure: protocol for a systematic review incorporating unpublished clinical study reports"*, PMID **32490351** (v1, 2020) and a v2 (2021), DOI `10.12688/hrbopenres.12951.2`. Not in our corpus.

### What it planned to access, and by what route

Read from the full text: searches of *"Medline (PubMed), Embase, Cochrane library, Google Scholar, Web of Science, Toxline and Scopus"*, clinical trials registries, **eight grey literature databases**, and:

> *"unpublished clinical study reports (CSRs) of relevant trials will be requested from the European Medicines Agency (EMA) and the Clinical Study Data Request database."*

Two named CSR routes: **EMA Policy 0070** and **CSDR** (`clinicalstudydatarequest.com`).

### Did it ever report? No.

A Europe PMC author search returns **only the two protocol versions — no completed review**. A CSR-based synthesis of this exact drug was designed and, so far as the literature shows, never delivered. That absence is itself worth recording: it is the outcome one would predict if the CSR route is hard.

### Route 1 — EMA Policy 0070: CLOSED for this drug, structurally

Read directly from the EMA Clinical Data Publication website today:

> *"Currently, EMA publishes clinical data submitted in support of initial marketing authorisation applications, extensions of therapeutic indications, and line extensions for medicines with CHMP opinions (positive, negative, or withdrawn) adopted **from May 2025 onwards**… In addition, clinical data packages submitted for medicines with new active substances that received a CHMP opinion **from September 2023 onwards**… have been available since January 2024. EMA had **temporarily suspended** the publication of clinical data for all medicines except those related to COVID-19, in line with the Final Programming Document 2023–2025 and the Management Board meeting of 14–15 December 2022."*

**Entresto's CHMP opinion was in 2015.** It falls outside every currently published scope — before the September 2023 new-active-substance window and before the May 2025 general window, and inside the suspension period's shadow. Its CSRs are **not** on the portal.

This is a structural exclusion by date, not a temporary outage, and it is worth stating plainly: **the flagship regulatory transparency route does not reach the pivotal trial of this review's own drug.** Access to the portal also requires an EMA account, which I did not create and would not.

### Route 2 — CSDR: open in principle, and it needs a named human

Novartis states that trial data availability follows the process at `clinicalstudydatarequest.com`, that requests are reviewed by an **independent review panel on scientific merit**, and that data are anonymised. PARADIGM-HF data are described as available by the sponsor under that policy.

This is a live route to the layer this review has never touched — but it requires a named researcher to submit a research proposal and sign a data-sharing agreement. **That is a human action and it is Mahmood's to take, not mine.** I have not initiated it and will not.

### What this changes about "all data found"

Until now the review's frame has been: published articles plus registry records. The CSR layer sits underneath both, and for this drug:

- **PARADIGM-HF**: the published HR 0.80 is established; a CSR would add adjudication detail and protocol-level information relevant to RoB-2 §9, not a different estimate.
- **ANSWER-HF and PIONEER-HF**: both currently blocked at the *published* level. A CSR would resolve them outright. This is the concrete payoff — the CSR layer is not an abstraction here, it is the thing that would move k from 3 to a settled number.
- **The general point**: a review that stops at published articles cannot tell whether a trial reports the estimand somewhere the reader cannot see. This review has now hit that wall twice in one day, on two different trials.

---

## 4b. The preprint layer, swept and screened — 2026-08-12T15:5xZ

Amendment 4's source, executed ahead of the amendment being committed, and recorded as an unregistered search event that post-dates the registered ones.

**Query** (Europe PMC, `SRC:PPR` restricts to preprint servers — bioRxiv, medRxiv, Research Square, SSRN):

```
(sacubitril OR LCZ696 OR Entresto) AND (enalapril OR "ACE inhibitor" OR ACEI) AND SRC:PPR
```

| | |
|---|---|
| Preprints mentioning the drug at all | **99** |
| Preprints also naming a comparator — the screened set | **24** |
| Screened by screener A, unreconciled | 24 of 24 |
| **Eligible under §3** | **0** |

Exclusion axes across the 24: 8 population (rat model, AMI, HFpEF, haemodialysis, post-ACS, cancer cardiotoxicity, COVID cohorts), 7 randomisation (retrospective and prospective observational studies, an economic evaluation, a meta-analysis), 5 intervention (ivabradine, home rehabilitation, SGLT2 inhibitors, bioinformatics screens), 4 comparator or not-relevant.

Two worth naming because they are the closest calls:

- **PPR1271024** — *Sacubitril-valsartan Versus Enalapril or Losartan at Guideline-Recommended Maximum Dosages in HFrEF (BEAT-HF)*, 2025-12-08. The single most on-topic record in the layer. **Observational cohort**, n=254 propensity-matched, primary outcome combined hospitalisation or death, **OR 0.650 (0.354–1.195)**. Fails randomisation; also reports an odds ratio, not the estimand.
- **PPR101063** — abstract retrieved rather than judged from the title, per the M2 lesson. Single-arm before-and-after in 205 HFrEF patients, **no comparator arm**. Fails comparator and randomisation.

**Result: the preprint layer contains no eligible trial for this review.** The layer is nonetheless real and was previously unsearchable by any registered source, and one directly on-topic comparison sat in it. Amendment 4 stands.

---

## 5. Unchanged

- **ANSWER-HF stays `undetermined`** with its dated re-check. No independent party has read its tables.
- **FDA and EMA pointers remain recorded** and ready for §7: `207620Orig1s000StatR.pdf`, `207620Orig1s000MedR.pdf`, and the Entresto EPAR. §4's trigger is still unmet for the established cells.

---

## Sources

- [EMA Clinical Data Publication website — current scope](https://clinicaldata.ema.europa.eu/)
- [EMA Policy 0070, publication and access to clinical data](https://www.ema.europa.eu/en/human-regulatory-overview/marketing-authorisation/clinical-data-publication)
- [Byrne D et al., protocol for a systematic review incorporating unpublished CSRs](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC7233178/)
- [Clinical Study Data Request](https://www.clinicalstudydatarequest.com/)
