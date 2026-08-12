# PIONEER-HF and ANSWER-HF resolved as far as the evidence allows; backward citation pass 2

2026-08-12. Overlay: `05_ADJUDICATION_OVERLAY.tsv` (22 rows). `02_CORPUS_AND_SCREENING.tsv` still untouched.

---

## 1. PIONEER-HF — DETERMINATE: exclude on the outcome axis

Both articles (NEJM and JACC) remain paywalled: Europe PMC returns `isOpenAccess=N`, `inEPMC=N`, "Subscription required" for PMID 30415601. So the primary publication was **not read**. It was resolved instead by working the layers that pay off — and, decisively, by finding parties who *did* read it.

**Four independent extractions, none of which found the registered estimand:**

| # | Source | What it records PIONEER-HF as reporting |
|---|---|---|
| 1 | **Posted results module**, NCT02554890 | 9 outcome measures: NT-proBNP time-averaged change (primary); symptomatic hypotension, hyperkalaemia, angioedema, hs-troponin, urinary cGMP, cGMP/creatinine, BNP:NT-proBNP, NT-proBNP at week 8. **No composite.** |
| 2 | **Circulation letter**, PMID 30955360 (the trial's own investigators) | exploratory composite of **death, HF rehospitalisation, LVAD implantation or transplant listing** |
| 3 | **ADHF meta-analysis**, PMC12773504 — had to extract PIONEER-HF's event outcomes | *"In PIONEER-HF, the composite outcome included HF rehospitalization, all-cause mortality, device implantation, and listing for heart transplantation"* |
| 4 | **JACC Advances meta-analysis**, PMC11883387 — same obligation | characterises PIONEER-HF solely by *"Greater time-averaged reduction in NT-proBNP"* |

Sources 3 and 4 are the ones that matter. Two independent synthesis teams went to the paper, extracted what it reports, and neither found the composite of cardiovascular death or first HF hospitalisation. Source 3 states PIONEER-HF's composite explicitly, and it is **a different composite** — it uses *all-cause* mortality rather than cardiovascular death, and adds device implantation and transplant listing as events. That is not the review's estimand and cannot be converted into it.

**Verdict: exclude, OUTCOME axis.** Flagged for re-check by anyone with NEJM access; the row names exactly what to look for.

### The Morrow 2024 thread, followed to its end

Morrow 2024 (PMID 38508844) reports *CV death or HF hospitalisation, HR 0.70 (0.54–0.91)* — but **pooled across PIONEER-HF and PARAGLIDE-HF**, adjusting for trial. It establishes that the component events were adjudicated in PIONEER-HF; it does not establish that PIONEER-HF reports the composite. The distinction is the review's whole eligibility rule: this review pools trials that *report* the estimand, not trials whose underlying data could in principle yield it. Morrow 2024 itself is excluded on the comparator axis (control is enalapril **or** valsartan) and population (spans HFpEF).

---

## 2. ANSWER-HF — REMAINS UNDETERMINED, deliberately

Every route was worked and every route is blocked:

| Layer | Result |
|---|---|
| Europe PMC REST (`resultType=core`) | `isOpenAccess=N`, `inEPMC=N`, "Subscription required: doi.org/10.1016/j.jacc.2025.10.053" |
| PMC ID converter | *Identifier not found in PMC* |
| Registry, NCT04853758 | primary: LVEF change, win ratio. 18 secondaries: arrhythmia counts, remodelling dimensions, NYHA, biomarkers, safety chemistry. **No composite.** `overallStatus=UNKNOWN`, no results posted |
| Europe PMC search, `"ANSWER-HF" AND Chagas` | 5 hits; the only trial-specific one is the *Heart Failure Reviews* mini-review, PMID 41870675, also paywalled |
| Mini-review abstract, PMID 41870675 (authors overlap the trial team) | *"Secondary endpoints included NT-proBNP, echocardiography and functional parameters, clinical events and safety."* … *"reinforces the need for larger, long-term studies, powered to hard clinical endpoints"* |
| Any synthesis that pooled it | none exists — the trial published in 2026 |
| Unpaywall | **not attempted.** The API requires an email in the query string; sending the user's address to a third party in a URL parameter is not something I will do to save a lookup. Named as a deliberate non-attempt, not a failure. |

### Why this is not enough to exclude, when PIONEER-HF's was

The distinction is **whether an independent party read the tables**.

For PIONEER-HF, two synthesis teams opened the paper and extracted its outcomes. For ANSWER-HF, nobody has. What I have is the trial's own abstract, its registry record, and a mini-review written partly by its own authors.

That is **exactly the class of evidence that failed for PARACHUTE-HF**. PARACHUTE-HF's qualifying HR of 0.91 appears in neither its registry outcome set nor its abstract — only in Table 2. ANSWER-HF is the same shape: same disease, an overlapping investigator group, the same win-ratio approach to a hierarchical secondary containing cardiovascular death and HF hospitalisation. If PARACHUTE-HF put a component HR beside its win ratio, ANSWER-HF plausibly did too.

Excluding it now would mean making the identical inference that was overturned this morning, from the identical evidence type, one row over. **It stays undetermined.** With n=190 over 6 months the event count is small and it would carry little weight, but weight is not eligibility.

**k = 3 remains a lower bound.** One paywalled article separates 3 from 4.

---

## 3. Backward citation — pass 2: 17 syntheses, by resolved identifier

Pass 1's method (matching author surnames and sample sizes) produced two false "misses" and a mislabelled row. Pass 2 does it by **resolvable identifier**: fetch each open-access synthesis's full text from the Europe PMC REST API, extract every `pub-id-type="pmid"` in its reference list, and diff those PMIDs against the corpus.

| | |
|---|---|
| Flagged syntheses | 45 |
| With an open-access record | 25 |
| Full text retrieved and reference lists parsed | **17** |
| Unique cited PMIDs harvested | **231** |
| Already in our 423-record corpus | 43 |
| Not in our corpus | 188 |
| Of those 188, mentioning both an ARNI and a comparator | **4** |

### The four candidates, resolved

| PMID | Title | In corpus? | Eligible? |
|---|---|---|---|
| 38330576 | A Comparative Analysis of the Clinical Efficacy of Sacubitril Valsartan Sodium and Enalapril in Patients with Non-Valvular Ejection Fraction Reduction (Zhang 2024) | no | **No** — prospective cohort, fails randomisation |
| 35483448 | Safety and efficacy of ARNI vs ACEI in acute heart failure — a prospective observational study (Bhat 2022) | no | **No** — observational |
| 36443599 | Real-world comparative effectiveness of ARNI versus ACEi/ARB in HF with reduced or mildly reduced ejection fraction | no | **No** — non-randomised |
| 38084196 | Comparison of Outcomes Between Sacubitril/Valsartan and Enalapril in Patients With Heart Failure: A Systematic Review and Meta-Analysis (Cureus 2023, PMC10710849) | **no** | **No** — a synthesis, not a study. But see below. |

**Randomised trials of this comparison missed by the registered search: ZERO.**

### Two findings that are worth more than the null

**(a) The registered PubMed string is a randomised-trial filter, and it behaves like one.** All three missed primary studies are observational. The fourth block (`randomized controlled trial[pt] OR randomised OR randomized OR trial`) excludes studies that describe themselves as cohorts. That is correct for this review's §3 and should be stated as a known, intended property rather than discovered again by a future reviewer.

**(b) The search missed a synthesis of exactly this comparison.** PMID 38084196 is a systematic review and meta-analysis of sacubitril/valsartan versus enalapril in heart failure — squarely on topic — and it is not in the corpus. It is not eligible as a *study*, but protocol §5 makes every retrievable synthesis of this comparison an **input to the backward citation step**. So the corpus of syntheses is itself incomplete, and the flagged list of 45 should be treated as a floor. (Read: it does not mention PIONEER-HF, and adds no trial we lack.)

### What remains

- **28 of 45 syntheses unread**: 8 open-access with full text not yet fetched, 19 with no open-access record, 1 (PMID 41923142, the Chagas-specific synthesis — the one most likely to matter now PARACHUTE-HF is in) with **no PMC record and no accessible route**. Named as blocked.
- Reference lists for 8 of the 17 fetched returned very few tagged PMIDs (some journals do not tag them), so the 231 is a floor, not a census. Those 8 need reading by eye.

**Interim result, stated as interim: across 17 syntheses and 231 resolved citations, the registered search missed no randomised trial of this comparison.** If that holds across all 45 it is a genuine finding about search breadth — and it is a finding, not an assumption, only because the identifiers were resolved rather than matched.
