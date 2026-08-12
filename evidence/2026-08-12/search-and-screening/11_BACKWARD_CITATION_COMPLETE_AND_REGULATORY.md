# Backward citation search — COMPLETE (44 of 45). Regulatory sources located.

2026-08-12. Protocol §4 and §5.

---

## 1. Backward citation: the full set

Pass 1 matched on author surname and sample size and produced two false "misses". Passes 2 and 3 use **resolved identifiers only**, through two independent routes so that a synthesis being paywalled does not stop its reference list being read.

| Route | Applies to | Syntheses | Citations harvested |
|---|---|---|---|
| **Europe PMC REST** `/{PMCID}/fullTextXML`, parsing `pub-id-type="pmid"` | the 25 with an open-access full text | 25 | **381 unique PMIDs** |
| **OpenAlex** `/works/pmid:{id}` → `referenced_works`, resolved via `/works?filter=openalex_id:` | the 19 with **no** open-access full text | 19 | **457 unique works, 379 resolved** to title + PMID |
| — | IQWiG HTA report, PMID 29144684 | 1 | **blocked** — not in Europe PMC, not in OpenAlex |
| | | **44 of 45** | |

**The OpenAlex route is the finding of this pass.** A synthesis being paywalled does not hide its reference list: OpenAlex exposes `referenced_works` for closed-access articles. Nineteen syntheses that could not be read were nonetheless diffed against the corpus. Backward citation does not require access to the synthesis — only to its bibliography.

### Result: candidates flagged, and what they were

Filtering all harvested citations to titles naming both an ARNI and a comparator, and removing those already in the 423-record corpus:

| Route | Flagged | Resolved as |
|---|---|---|
| Europe PMC (25 syntheses) | 10 | 5 × sacubitril/valsartan **vs ramipril in post-MI** (SAVE-SHOCK; PARADISE-MI win-ratio and echo substudies; a STEMI trial) — fail comparator **and** population. 2 × VALIANT (valsartan/captopril) — fail intervention. 3 × non-randomised (Bhat 2022, Zhang 2024, a real-world cohort) + 1 synthesis (PMID 38084196) |
| OpenAlex (19 syntheses) | 4 | 3 already in the corpus. **1 novel: PMID 27039128**, a cost-effectiveness analysis of sacubitril/valsartan vs enalapril — fails randomisation |

## **Randomised trials of sacubitril/valsartan versus enalapril in adult HFrEF missed by the registered search: ZERO.**

Across 44 syntheses and roughly 760 resolved citations, the registered search missed no eligible trial. Everything it missed was an observational study, a cost-effectiveness model, a synthesis, or a trial with the wrong comparator or population.

### What that null does and does not license

It supports a narrow claim: **for this comparison, the registered two-database strategy achieved complete recall of eligible randomised trials, as measured against the reference lists of 44 syntheses of the same question.**

It does not support "the search found everything". Backward citation can only find what somebody else already found. A trial that every synthesis missed is invisible to this test — and the one trial we know the registered strategy nearly lost, ANSWER-HF, was recovered by PubMed rather than by this step, because it is too recent to appear in anyone's reference list.

**The asymmetry is the interesting part.** In one day this process has produced:

- **Three confirmed checking failures in published syntheses** — (i) a JACC Advances meta-analysis labelling PIONEER-HF's NT-proBNP ratio of change *"HR: 0.71; 95% CI: 0.63-0.81"*, i.e. a biomarker ratio presented as a hazard ratio; (ii) syntheses of "sacubitril/valsartan versus enalapril in HFrEF" pooling prospective cohorts alongside randomised trials without separating them; (iii) the same syntheses pooling trials whose composites are not the same composite.
- **Zero confirmed breadth failures.**

Both counts come from the same corpus and the same day, so the comparison is at least internally fair. The tentative reading: the field's searches are in reasonable shape, and what is not in reasonable shape is what happens to a number after it has been found. That is precisely where a pre-registered estimand and a per-record ledger bite — and precisely where this run's own error also occurred.

### Still open

- **PMID 29144684** (IQWiG §35a benefit assessment) — no route to its reference list. Named as blocked.
- **78 of 457 OpenAlex works did not resolve** to title metadata in the batch lookup. Unresolved, not absent.
- **PMID 38084196** and **PMC7233178** ("protocol for a systematic review incorporating unpublished clinical study reports") are on-topic syntheses **not in our corpus**. They are §5 backward-citation inputs, so the flagged list of 45 remains a floor. The CSR-based one is worth chasing: unpublished clinical study reports are a source layer this review has not touched at all.

---

## 2. Regulatory sources — located by lookup, trigger not met

Protocol §4 admits the FDA statistical review and the EMA EPAR **"where a cell cannot be established from those"** other sources. Both are now located by lookup rather than recall, which is what the earlier abandoned attempt failed to do.

| Document | Resolvable pointer | How located |
|---|---|---|
| FDA **Statistical Review**, NDA 207620 | `https://www.accessdata.fda.gov/drugsatfda_docs/nda/2015/207620Orig1s000StatR.pdf` | openFDA API → `drugsfda.json?search=openfda.brand_name:"ENTRESTO"` → NDA207620 → approval-package TOC |
| FDA Clinical (Medical) Review | `https://www.accessdata.fda.gov/drugsatfda_docs/nda/2015/207620Orig1s000MedR.pdf` | same |
| FDA Summary Review | `https://www.accessdata.fda.gov/drugsatfda_docs/nda/2015/207620Orig1s000SumR.pdf` | same |
| EMA **EPAR public assessment report**, Entresto | `https://www.ema.europa.eu/en/documents/assessment-report/entresto-epar-public-assessment-report_en.pdf` | web search restricted to `ema.europa.eu` |

**Note on the earlier failure.** The URL abandoned earlier was `.../207620Orig1s000TOC.cfm`. The real path ends `.html`. One character of recalled structure was wrong, which is the whole argument for lookup.

**Trigger status: not met, and therefore not consulted.**

- For **PARADIGM-HF** and **PARALLEL-HF** the cells are established from the primary publications and corroborated at the registry, so §4's condition does not fire. Both documents concern the 2015 approval and would add no trial.
- For **ANSWER-HF**, the one row where a cell genuinely cannot be established, the Entresto approval package **predates the trial by a decade** and cannot contain it. It is the wrong source for the only gap that qualifies.

The pointers are recorded so that §7's requirement — a resolvable pointer to the specific document — is satisfiable the moment a cell needs them. Locating a registered source and recording that its trigger condition is unmet is executing §4, not skipping it.

---

## 3. ANSWER-HF — row held open, unchanged

No new access. OpenAlex confirms the Chagas-specific synthesis is closed too (see §4 below), so no third party has yet extracted ANSWER-HF's tables. **Remains `undetermined`.** Re-check dated 2026-08-12; the trigger for re-opening it is a reading of the JACC tables by anyone.

---

## 4. The Chagas synthesis — retried through every layer, still blocked

PMID 41923142, *Sacubitril/Valsartan Versus Enalapril in Chagas Cardiomyopathy With HFrEF: A Systematic Review and Meta-Analysis*, DOI `10.1097/crd.0000000000001242`. Now the most relevant synthesis in the set, since PARACHUTE-HF is included.

| Layer | Result |
|---|---|
| Europe PMC REST, `resultType=core` | `inEPMC: N`, `isOpenAccess: N` |
| PMC ID converter | not found in PMC |
| **OpenAlex** | `open_access.is_oa: false`, `oa_status: "closed"`, `oa_url: null`, **`any_repository_has_fulltext: false`** — no author copy, no repository deposit, no preprint, anywhere OpenAlex indexes |
| Publisher | Wolters Kluwer, subscription |
| Non-English mirror | none indexed |

**Genuinely blocked, on the authority of a source that checks every repository rather than one aggregator.**

**But the backward-citation step still ran on it.** OpenAlex exposes its 32 `referenced_works` without the text, and those were harvested and diffed with the other 18 closed syntheses. The registered step was executed against this synthesis; only the reading of its narrative was lost.

---

## Sources

- [FDA Drugs@FDA approval package, ENTRESTO NDA 207620](https://www.accessdata.fda.gov/drugsatfda_docs/nda/2015/207620Orig1s000TOC.html)
- [EMA EPAR public assessment report, Entresto](https://www.ema.europa.eu/en/documents/assessment-report/entresto-epar-public-assessment-report_en.pdf)
- [Protocol for a systematic review incorporating unpublished clinical study reports](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC7233178/)
