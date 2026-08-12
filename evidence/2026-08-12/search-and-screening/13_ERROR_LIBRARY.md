# Error library

**A standing component of Nafis papers.** Entries record verifiable discrepancies between what a document states and what its own or an external source establishes, found while executing a review's registered steps.

Version 2 — 2026-08-12. Supersedes v1 of the same date; **two v1 entries were withdrawn on verification** and the withdrawals are recorded in §6 rather than deleted.

> ### ⚠ RENDER STATUS: THIS LIBRARY DOES NOT CURRENTLY PASS ITS OWN GATE
>
> The rules in this file were stress-tested in `14_RULE_TESTS_AND_SPECIFICATIONS.md`. Three of five required repair, and on its first evaluation the repaired render gate **fired on this library**.
>
> **Failing condition: Rule 5 v2, class matching.** This library emits an external entry in class M1 (estimand mislabelling) and carries no own-entry or compliant screen record for M1. Publishing an M1 accusation without having screened our own extractions for M1 is the one-sided-catalogue failure the gate exists to prevent.
>
> **Remedy before publication:** run an M1 screen over this review's own extracted estimates and record the outcome either way, under Rule 4 v2 — with a screen ID, timestamp, input set size and criterion. A prose claim of "we checked" will not render.
>
> Two further caveats carried from testing: **Rule 1 is unproven in its accusatory direction** (no declared-then-violated case exists in the eight-document test sample, so the filter's strictness is unknown), and **Rule 2's house-style branch is untested** (no document in the sample uses `HR` uniformly loosely). Entry E1 survives both, satisfying the internal and the external test.

---

## 1. What goes in, and what does not

An entry requires **all** of:

1. an **exact quotation** of the text at issue;
2. a **resolvable identifier** — DOI, PMID or PMCID — and the **location within the document** (table number, row, section);
3. the **correct value or characterisation**;
4. the **source establishing** that correction, itself resolvable;
5. the **date verified**;
6. an assessment of **whether the discrepancy propagated** into the document's conclusions.

An entry is **excluded** if the document made a **declared choice** rather than a mistake. A review that admits observational studies under stated eligibility criteria has made a design decision. A review restricted to English-language reports has declared a limitation. Neither is an error, however much either may affect the result. Getting this distinction wrong would discredit the library, and it has already cost this library two entries (§6).

**Attribution is to the work, never to the authors.** No entry makes or implies a claim about competence, care, or motive. The unit of analysis is a document.

**Our own errors appear in the same table, at the same prominence, under the same evidentiary standard.** A catalogue of other people's mistakes with none of our own is an indictment. The same catalogue with ours in it is a field-level finding, and considerably harder to wave away.

---

## 2. Denominator and sampling — read before any rate

| | |
|---|---|
| Documents examined at extraction level (included-study tables or per-trial characteristic rows read line by line) | **4** |
| Of those, containing a verified error | **1** |
| Documents whose reference lists only were parsed (not examined for errors) | 44 |
| This review's own working documents examined | all |
| Errors found in this review's own work | **4** |

**How the sample was selected, and why it is not a prevalence estimate.** These four documents were not sampled at random. Each was opened because this review needed a specific fact from it — what a trial reported, whether a study was in a reference list. They are open-access, they are recent, and they concern one drug comparison. The sample is **enriched by construction**: we read them in the places where a discrepancy would matter to us, which is exactly where one is most likely to be noticed.

**"One of four" is therefore not a rate for the literature.** It is a count from a purposive sample, and it is reported here so that nobody can quote a proportion without seeing how it was produced. Statements of the form "many meta-analyses contain…" do not appear in this library.

---

## 3. Classification by mechanism

Classified by **how the error is produced**, not by how bad it is, so the taxonomy is applicable by others to other reviews.

| Class | Mechanism | Observed here |
|---|---|---|
| **M1 — Estimand mislabelling** | A quantity is recorded under the name of a different quantity. The number is right; the label is wrong. | **Yes** — E1 |
| **M2 — Estimand substitution at screening** | Eligibility is judged against a subset of what a study reports, typically its primary endpoint, rather than everything it reports. | **Yes** — N1 |
| **M3 — Unverified absence** | "Not found" or "not encountered" is asserted where the search that would establish it was not run. | **Yes** — N2 |
| **M4 — Frame over-claim** | A recall or completeness statistic is computed against an incomplete denominator and presented as complete. | **Yes** — N3 |
| **M5 — Identity resolution by surface features** | Studies are matched across documents by author surname, year and sample size rather than by resolved identifier. | **Yes** — N4 |
| M6 — Trial-identity failure | Two reports of one trial treated as two trials, or one trial's data attributed to another. | Not observed |
| M7 — Covert duplicate inclusion | The same participants enter a pool twice through separate publications. | Not observed |
| M8 — Comparator mismatch | Trials with different comparators pooled as if against a common control. | Not observed as an error; see §6.2 for a **declared** instance |
| M9 — Unit-of-analysis error | Events pooled as if independent when they are recurrent within participants, or arms double-counted. | Not observed |
| M10 — Numerical integrity failure | Reported summary statistics inconsistent with the stated sample (GRIM/GRIMMER-type), or distributions inconsistent with randomisation (Carlisle-type). | Not tested — no screen run |

M6–M10 are listed because a taxonomy that only contains what we happened to find is a list, not a taxonomy. M10 in particular is untested here: no numerical integrity screen has been run on any document, and their absence from the table means *not looked for*, not *absent*.

---

## 4. Entries — published documents

### E1 — Estimand mislabelling (M1)

| Field | Value |
|---|---|
| **Document** | *Sacubitril/Valsartan vs ACE Inhibitors or ARBs: A Systematic Review and Meta-Analysis of Randomized Trials.* JACC: Advances, 2025 |
| **Identifiers** | PMID **39970741**; PMCID **PMC11883387** |
| **Location** | Table of included trial characteristics, PIONEER-HF row, final column |
| **Exact quote** | *"PIONEER-HF Velazquez et al¹⁹ 2019 … Greater time-averaged reduction in NT-proBNP in SAV group (**HR: 0.71; 95% CI: 0.63-0.81; P < 0.001**)"* |
| **What is wrong** | The cell's own prose identifies the quantity as a **time-averaged reduction in NT-proBNP** — a ratio of two biomarker concentrations. It is labelled **HR**. |
| **Correct characterisation** | A ratio of change in NT-proBNP, not a hazard ratio. PIONEER-HF's primary endpoint is the time-averaged proportional change in NT-proBNP from baseline through weeks 4 and 8. |
| **Source establishing this** | **Internal to the document** — the same cell describes the quantity as an NT-proBNP reduction. Corroborated by the ClinicalTrials.gov posted results module for **NCT02554890**, whose sole primary outcome measure is *"N-terminal Pro-brain Natriuretic Peptide (NT-proBNP) Values and Time-averaged Change From Baseline"*, and by PMID **38508844**, which reports the analogous pooled quantity as *"ratio of change = 0.76; 95% CI: 0.69-0.83"*. |
| **Why it is not a house-style choice** | The same table labels other ratio-of-change quantities **correctly and differently**: PARALLAX *"GMR: 0.84"*, PARAGLIDE-HF *"ratio of change 0.85"*, PARAGON-HF *"rate ratio: 0.87"*, and elsewhere *"AUC ratio 0.95"*. The same column uses **HR** for genuine time-to-event estimates — PARALLEL-HF *"composite of CV death and HHF (HR: 1.09; 95% CI: 0.65-1.82)"* and PARADISE-MI *"composite of CV death or incident HF (HR: 0.90)"*. The document distinguishes these labels everywhere except this cell. |
| **Did it propagate?** | **No evidence that it did**, and this should be stated as prominently as the error. The document's methods state: *"Effect estimate was reported as risk ratio (RR) as 9 of the 14 included trials had no time-to-event analysis for outcomes of interest. In the absence of hazard ratio reporting in most studies… we calculated RR from the reported frequency of events."* The pooled analyses use risk ratios computed from event counts, not the tabulated estimates. The error is confined to the descriptive characteristics table. |
| **Why it still matters** | The descriptive table is what a downstream reviewer reads when deciding what a trial reports. Two numbers in one column, identically labelled, are a survival estimate and a biomarker ratio. Nothing in the label distinguishes them. |
| **Date verified** | 2026-08-12 |

**No other entry from published documents currently meets the evidentiary standard.**

---

## 5. Entries — this review's own work

Same standard, same table structure, same prominence. Full narrative in `05_ADJUDICATION_LOG.md`; all four originals remain unedited in the record.

### N1 — Estimand substitution at screening (M2)

| Field | Value |
|---|---|
| **Document** | `02_CORPUS_AND_SCREENING.tsv`, row PMID 41335448 |
| **Exact quote** | *"WIN RATIO 1.52 (1.28-1.82) over a hierarchical composite of CV death, HF hospitalisation, then 12-week NT-proBNP change. **No time-to-first-event hazard ratio for the composite.**"* |
| **What is wrong** | The final sentence is false. PARACHUTE-HF reports **HR 0.91 (95% CI 0.73–1.13), P = .40** for first HF hospitalisation or cardiovascular death, from a Cox model stratified by country. The exclusion was made on the trial's primary endpoint alone. |
| **Correct value** | HR 0.91 (0.73–1.13); 155/462 vs 169/460 |
| **Source establishing this** | *JAMA* 2026;335(1):49–59, DOI 10.1001/jama.2025.19808, **Table 2**, "Secondary outcomes" row, footnote d (*"HRs were derived from Cox proportional hazards models, with stratification by country"*), read via **PMC12676478** |
| **Did it propagate?** | **Yes.** It excluded the highest-weight eligible trial in the review — approximately 24% of the intended pool — and would have produced a two-trial synthesis. Overturned by named human adjudication (Mahmood, 2026-08-12T13:30:45Z). |
| **Date verified** | 2026-08-12 |

### N2 — Unverified absence (M3)

| Field | Value |
|---|---|
| **Document** | `03_PRISMA_AND_SCREENING_NOTES.md`, §3, offending-quantity table |
| **Exact quote** | *"**not encountered.** No record in this corpus reports the composite as a fixed-timepoint dichotomous risk ratio."* |
| **What is wrong** | The corpus contained such a record at the time of writing: PMID **34395116**, then held as `undetermined`, reports HF hospitalisation **RR 0.61 (0.39–0.97)** and HF-related death **RR 0.47 (0.19–1.12)** at 12 months, components never combined, with no hazard ratio, Cox or Kaplan–Meier anywhere in the text. |
| **Source establishing this** | *Cureus* 2021, **PMC8357012**, Table 2 |
| **Did it propagate?** | Into the write-up, not into the included set. Found by us, one step later. |
| **Date verified** | 2026-08-12 |

### N3 — Frame over-claim (M4)

| Field | Value |
|---|---|
| **Document** | `09_BLOCKED_ROWS_AND_BACKWARD_CITATION_PASS2.md` and `11_...md` |
| **Exact quote** | *"across 44 syntheses and roughly 760 resolved citations, the registered search missed no randomised trial of this comparison"* |
| **What is wrong** | The denominator was not the retrievable set. A dedicated PubMed search for syntheses of this comparison, run 2026-08-12T15:20:58.705Z, returns **244**. The 44 examined are **18%** of it. The null is real for the frame tested and was presented as stronger than it is. |
| **Correct characterisation** | No eligible randomised trial was missed **as measured against 18% of the retrievable synthesis frame**, by a method structurally blind to preprints and to anything too recent to be cited. |
| **Source establishing this** | PubMed `esearch`, count read from `esearchresult.count` = 244; and a Europe PMC title/abstract sweep returning 324 records of which 101 are outside the corpus, including 7 preprints |
| **Did it propagate?** | Into the strength of a headline claim, not into the included set. Corrected in `10_WHAT_THIS_PROCESS_DOES.md` before the claim is used. |
| **Date verified** | 2026-08-12 |

### N4 — Identity resolution by surface features (M5)

| Field | Value |
|---|---|
| **Document** | `06_BACKWARD_CITATION_PASS1.md`, direction-1 table |
| **Exact quote** | *"This is the registered backward-citation step doing what it is for: it found records that neither registered database string returned."* |
| **What is wrong** | It found no such records. Two studies were called missing because they were matched to our corpus by author surname and sample size instead of by resolved identifier. Resolving the reference list gives Santos 2021 = PMID **33992607** and Zhao 2022 = PMID **35874853**, both already in the corpus; a third row was mislabelled "Halle 2021" when Halle 2021 = PMID **34591356**. |
| **Source establishing this** | Reference list of **PMC12950259**, entries [16], [19] and [22], resolved to PMIDs |
| **Did it propagate?** | Into a claimed finding, which was retracted with the original struck through rather than rewritten. |
| **Date verified** | 2026-08-12 |

---

## 6. Withdrawn entries

Recorded, not deleted. Both were in v1 of this file and both failed the error-versus-declared-choice test on verification. This section is the library's own control.

### 6.1 — WITHDRAWN: "prospective cohorts pooled alongside randomised trials"

v1 alleged that PMID **41773097** / PMC12950259 presented two prospective cohort studies inside a table captioned *"Summary characteristics of the included RCTs."*

**Verification found a declared design choice.** The document's stated eligibility criteria are explicit: *"(1) randomized controlled trials (RCTs) **or observational studies** that investigated the use of sacubitril/valsartan as the intervention, compared to enalapril."* Its abstract states *"This study included 10 RCTs and two prospective cohort studies with 11,765 patients."* It applies **RoB 1 to the trials and the Newcastle–Ottawa Scale to the cohorts**, as separate instruments.

Admitting observational studies was a declared, signposted, methodologically equipped decision. What remains is a **table-caption inconsistency** — the caption says "included RCTs" for a table containing two cohorts — which does not meet this library's threshold and is recorded here rather than as an entry.

### 6.2 — WITHDRAWN: "trials pooled whose composites are not the same composite"

v1 alleged undeclared pooling of heterogeneous composites. The evidence cited was **PMC12773504**, which states:

> *"The definition of the primary composite endpoint (HF rehospitalization/all-cause mortality) **varied across the included trials**. In PIONEER-HF, the composite outcome included HF rehospitalization, all-cause mortality, device implantation, and listing for heart transplantation. PARAGLIDE-HF defined its composite endpoint as HF rehospitalization, cardiovascular mortality, and urgent HF visits…"*

That is the document **declaring the heterogeneity in its own methods** and pooling with it stated. Whatever one thinks of the choice, it is a choice, made in the open. **The quotation I offered as evidence of the error is in fact evidence of disclosure.**

No verified instance of *undeclared* pooling of discordant composites was found. The class remains in the taxonomy as **M8, not observed**.

**Both withdrawals reduce the published-error count from three to one.** They are the reason the remaining entry can be relied on.

---

## 7. Relation to the existing literature — placeholder, to be completed

A sibling lane is surveying the published meta-research on synthesis errors: data-extraction error prevalence, covert duplicate publication, Carlisle-type baseline-distribution screens, GRIM/GRIMMER numerical consistency, and unit-of-analysis and estimand errors.

**When that lands, each class in §3 is to be mapped onto the field's existing terminology and the prior work cited.** Where a class is already well characterised, this library should say so plainly and credit the source. None of M1–M10 is claimed as a discovery. The contribution here is not the observation that syntheses contain errors — that is established — but the practice of recording them against resolvable identifiers with denominators, alongside one's own, as a routine output of doing a review rather than as a separate meta-research study.

Until the survey lands, no entry in this file asserts novelty, and none should.

---

## 8. Reuse in Nafis papers

### The "if applicable" rule

An error library section is included in a Nafis paper when **either** condition holds:

1. **Direct relevance** — an entry concerns a document bearing on that review's own question: one of its included studies, or a synthesis of the same or an overlapping comparison.
2. **Class exposure** — the review's own data could exhibit an error class in §3, whether or not an instance was found. A review pooling a composite outcome is exposed to M1, M2 and M8, and states so, with its own entries or with an explicit "no instance found" and how it looked.

Condition 2 is the important one. A paper that prints only the classes where it found something turns the library back into a highlights reel. **"Screened for, none found, here is the screen"** is a publishable line and belongs in the table.

### Non-negotiables when projected

- Denominator and sampling method reproduced with the entries. Never a bare proportion.
- Withdrawn entries carried, not dropped. §6 travels with §4.
- Own errors at equal prominence. If a paper's projection would contain other parties' errors and none of its own, that is a defect in the projection.
- No novelty claim absent the §7 mapping.

### Where it lives in the object — for the build lane

This file is currently maintained by hand, which is the wrong shape for something published repeatedly. It should be **a projection like every other number in a Nafis paper**, not a document.

Proposed, for the build lane to accept, amend or reject:

- Entries as records in the canonical object — suggested `errors[]` — each carrying: `class` (M1–M10), `document` (DOI/PMID/PMCID), `location`, `quote_verbatim`, `correct_value`, `correcting_source`, `date_verified`, `propagated` (yes / no / unknown, with evidence), `status` (`active` / `withdrawn`), and for withdrawals a `withdrawal_reason`.
- `scope` on each entry — the review IDs it is relevant to — so the "if applicable" rule is evaluated by the object rather than by a person deciding what to include.
- The denominator computed, not typed: `documents_examined_at_extraction_level` maintained as a counter incremented when a document is opened at that depth, so a rate can never be quoted against a number nobody maintained.
- `origin` — `own` or `external` — so a projection that would emit external entries with no own entries can be **blocked by a render gate**, the same way the inadmissible-counts guard works.

The last item is the one worth building. The failure mode this library is most exposed to is not inaccuracy; it is drifting into a one-sided catalogue. That is checkable mechanically, so it should be.
