# Running report #2 — testing the thesis with a denominator

**Date:** 12 August 2026 · supersedes the framing of report #1, which stands for its own numbers
**Thesis under test (Mahmood, verbatim):** *"despite us only using openly accessible data the issue with other metas is that they don't search enough and check enough"*
**Access:** read-only mount of `F:\rapidmeta-finerenone`. No repo writes.
**Status:** RUNNING.

---

## 0. A confound that must be stated before any number

Report #1's three errors were **our own pipeline's errors**, not published syntheses' errors. Using them as evidence about "other metas" would be invalid. Two distinct objects are being audited and they are kept separate throughout:

- **Object A — our corpus's extraction of published metas.** Does our record of a published meta match what that meta says?
- **Object B — the published metas themselves.** Did they search enough, and did they check enough?

Only Object B bears on the thesis.

---

## 1. Headline — confirmations first

**Object A: our extraction of published metas is accurate. 20 of 21 cells correct (95.2%).**

**Object B: 6 published syntheses examined in depth. 3 correct-or-defensible, 2 with confirmed errors, 1 flagged and unconfirmed.**

The single most important result is not a catch, it is a **mechanism**: where published metas failed here, the dominant failure was **checking, not searching**. The worst case found — Jyotsna 2023 — had a *broader* search than several correct metas (PubMed, Cochrane, Google Scholar, medRxiv, preprints, **and explicit translation of non-English text**) and still produced a badly wrong result, because it counted the same patients three times.

That is a meaningful refinement of the thesis, not a confirmation of it. **Search breadth and checking are dissociable, and in this sample checking failed more often and more severely than searching.**

---

## 2. Object A — our extraction of published metas

Sample: the 4 finerenone meta-analyses in `finerenone_meta_analyses_database.md` with the strongest triage flags. Each corpus cell checked against the meta's own abstract or full text.

| Meta | PMID | Cells checked | Correct | Wrong |
|---|---|---|---|---|
| Jyotsna 2023 (Cureus) | 37575756 | 3 | 2 | **1** |
| Chen 2026 (Medicine) | 41578591 | 6 | 6 | 0 |
| Bao 2022 (Eur J Clin Pharmacol) | 36273065 | 6 | 6 | 0 |
| Zhang MZ 2022 (Front Pharmacol) | 35197856 | 6 | 6 | 0 |
| **Total** | | **21** | **20 (95.2%)** | **1 (4.8%)** |

**The one error — outcome mislabel, Jyotsna 2023.** Our database files `RR 0.86 (0.80–0.93)` under **"MACE / CV Composite"**. The source reports that value for **death from cardiovascular causes**:

> "Five out of seven studies reported death from cardiovascular causes and hospitalization due to HF, and the combined analysis showed … (RR = 0.86 (0.80, 0.93), p = 0.0002 …) and (RR = 0.77 (0.70, 0.84) …)"
> — Jyotsna 2023 full text, Efficacy Outcomes

The value is right; the outcome it is attached to is wrong. This is the **outcome-definition** failure class — the third of the four fields that silently invalidate a pool.

Confirmed-correct examples worth stating plainly: Chen 2026's four effect estimates and k/N, Bao 2022's five estimates and k/N, and Zhang MZ 2022's four estimates and k/N all match their sources exactly, including CI bounds.

*(Zhang MZ 2022's all-cause mortality RR 0.90 (0.80–1.00) in our database is not in that paper's abstract; not checkable at the level consulted. Marked unverified, not counted either way.)*

---

## 3. Object B — the published syntheses

### 3.1 Scoreboard

| Synthesis | Domain | Verdict | Failure mode |
|---|---|---|---|
| Reyaz 2023, Cureus (PMID 38084196) | ARNI vs enalapril | **ERROR** | **Checking** |
| Jyotsna 2023, Cureus (PMID 37575756) | Finerenone | **ERROR — severe** | **Checking** |
| Alam 2023, Cureus (PMID 37554618) | ARNI vs enalapril/valsartan | **Defensible** | — (stated restriction) |
| Bao 2022 (PMID 36273065) | Finerenone | **Correct as reported** | — (see independence note) |
| Zhang MZ 2022 (PMID 35197856) | Finerenone | **Correct as reported** | — (see independence note) |
| Chen 2026 (PMID 41578591) | Finerenone | **FLAGGED, unconfirmed** | suspected checking |

**Rate: 2 confirmed errors / 5 adjudicated = 40%.** One further flagged. Denominator is small and non-random — these were selected on triage signals. **This is not a field-wide error rate and must not be quoted as one.**

### 3.2 The severe case — Jyotsna 2023, and why it matters most

Reported: 7 trials, **39,995 patients**. The entire finerenone randomised universe is roughly 22,000. Their own Table 1, read directly, resolves it:

| Table 1 row | n | Finerenone / placebo | What it actually is |
|---|---|---|---|
| Bakris (2020) | 5674 | 2833 / 2841 | FIDELIO-DKD |
| Bertram (2021) | 7352 | 3686 / 3666 | FIGARO-DKD |
| **Gerasimos (2021)** | **5674** | **2833 / 2841** | **FIDELIO-DKD again** — identical n and arm split |
| **Agarwal (2022)** | **13026** | **6519 / 6507** | **FIDELITY — the pooled FIDELIO + FIGARO** |
| **Gerasimos (2022)** | **7352** | **3686 / 3666** | **FIGARO-DKD again** — identical n and arm split |

All values read verbatim from Table 1.

FIDELIO-DKD and FIGARO-DKD are each entered **twice as separate "trials"**, and then a **third** time inside the FIDELITY pooled analysis. The same randomised participants are counted three times over. That is how ~22,000 patients became 39,995.

Two consequences, in ascending order of seriousness:
1. N is inflated by roughly 80%.
2. **Every pooled CI is falsely narrow**, because the same events enter the variance calculation repeatedly. Their reported I² of 0% across most outcomes is what you would expect when duplicate data are pooled against itself.

**How the duplicates hid:** the rows are labelled by the authors' *given* names — "Bertram" is Bertram Pitt, "Gerasimos" is Gerasimos Filippatos. Citation handling that mistakes a forename for a surname will not detect that "Bakris 2020" and "Gerasimos 2021" are the same trial.

**Critically for the thesis: this meta's search was broad.** PubMed, Cochrane, Google Scholar, medRxiv, preprints, no date/language filters, and — explicitly — *"Non-English text was translated using Google's translate service."* It searched better than several metas that got the right answer. **It failed entirely at checking.**

### 3.3 The ARNI case — checking failure of a different shape

Reyaz 2023, established in the Li memo: recorded Li 2019's comparator as **enalapril** when the paper says **benazepril**, and its follow-up as **6 months** when the paper says **12**; then pooled that benazepril-controlled trial into an all-cause mortality analysis whose stated comparison is sacubitril/valsartan **versus enalapril**.

Same class as Jyotsna: the trial was **found**, and mis-characterised. Not a search failure.

### 3.4 A defensible different choice — not an error

Alam 2023 excluded Li 2019 entirely. Its stated inclusion criteria restrict to *"only articles published in English."* That is a **declared eligibility restriction**, applied consistently. It narrows generalisability; it is not an error, and counting it as one would be exactly the over-claim to avoid.

This is the boundary that matters: **Reyaz included a trial and described it wrongly. Alam excluded it and said why.** Only the first is a defect.

### 3.5 A correctness finding that is not about accuracy — non-independence

Bao 2022 and Zhang MZ 2022 report **identical** estimates on two outcomes: hyperkalaemia RR 2.03 (1.83–2.26) and ESKD RR 0.80 (0.65–0.99) — despite k=4/N=13,510 versus k=5/N=13,078.

Both were checked against their own abstracts and **both are reported accurately**. The explanation is authorship: Zhang Ming-Zhu, Bao Wujisiguleng and Sun Lu-Ying appear on both, from the same institution (Dongzhimen Hospital, Beijing University of Chinese Medicine). These are two overlapping analyses by one group in two journals.

Neither is wrong. But **they are not independent replications**, and the apparent consensus across "many meta-analyses agree on RR ≈ 2.03" is partly one team counted twice. Anyone using the count of concordant syntheses as evidence of robustness is over-counting.

---

## 4. The two failure modes, counted separately

| Failure mode | Definition | Confirmed instances | Cases where it was NOT the problem |
|---|---|---|---|
| **(a) Search breadth** | Trials the synthesis never found — non-MEDLINE, non-English, off-NCT, registry-only | **0 confirmed so far** | Jyotsna searched preprints + translated non-English and still erred; Reyaz *found* the Chinese trial |
| **(b) Checking** | Trials found but characterised wrongly — comparator, population, outcome definition, or duplicate identity | **2 confirmed** (Reyaz, Jyotsna) + 1 flagged (Chen 2026) | Bao, Zhang, Alam all checked adequately |

**This inverts the emphasis of the original thesis.** In this sample, breadth failures are not yet demonstrated at all, while checking failures are confirmed twice and are severe when they occur.

Nuance on breadth: Li 2019 *was* invisible to a MEDLINE-only search — Chinese Journal of Geriatrics is not in MEDLINE, and our PubMed search returned zero. That is a real breadth limitation of the databases. But it did not cause an error in any synthesis examined: Reyaz found it anyway; Alam excluded it deliberately. **Breadth remains a plausible failure mode that this sample has not yet caught in the act.**

The remedies differ, which is why the split matters:
- Breadth failure → add CNKI/Wanfang/VIP, trial registries beyond NCT, preprints, non-English.
- Checking failure → deduplicate by **trial identity** (NCT/registry ID), not by citation string; verify comparator and outcome definition at primary for every included row.

The second remedy is what would have caught both confirmed errors. Neither would have been caught by searching harder.

---

## 5. The counter-example, sought honestly

The thesis says access was never the real barrier. Across all work in this session that has held up — CQVIP was free but JavaScript-gated; PARACHUTE-HF and its supplement were open; Cureus metas are open; the Chinese record was free. Every earlier "unavailable" was a tooling failure on my side.

**One genuine access obstacle has been found, and it should be recorded as the counter-example:**

**ANSWER-HF (NCT04853758, PMID 41396086, J Am Coll Cardiol 2025;87:1220–1232).** The per-arm sample sizes and the cardiovascular-death and HF-hospitalisation event counts are **not** in the abstract, the registry has **no posted results** (`hasResults: false`), and the full text is behind an Elsevier paywall. There is no open route to those numbers. They remain unobtained — and unlike every other case, not for want of searching.

This is a single instance and it concerns a secondary endpoint, so it does not overturn the thesis. But it is a real boundary condition: **open access covers most of what a synthesis needs, not all of it**, and the gap is largest for non-primary outcomes in paywalled journals with no registry posting.

---

## 6. Running totals

| Metric | Count |
|---|---|
| **Object A** — corpus cells checked against published metas | 21 |
| — correct | **20 (95.2%)** |
| — wrong | 1 (outcome mislabel) |
| **Object B** — published syntheses adjudicated | 5 (+1 flagged) |
| — correct or defensible | **3** |
| — confirmed error | 2 |
| — search-breadth failures confirmed | **0** |
| — checking failures confirmed | **2** |
| Corpus trial rows verified at primary (report #1) | 4 of 3,656 |
| Genuine access obstacles found | 1 (ANSWER-HF event counts) |

---

## 7. Next, in priority order

1. **Confirm or clear Chen 2026** (PMID 41578591, PMC12851658 — open). N=33,455 from 7 finerenone trials carries the same signature as Jyotsna. One table read settles it.
2. **Systematic duplicate-identity check across all 13 finerenone metas.** Now that the FIDELIO/FIGARO/FIDELITY triple-count is a known pattern, screen every meta's k and N against the trial universe. Cheap, and it targets the dominant confirmed failure mode.
3. **Hunt breadth failures deliberately**, since none is yet confirmed. Best candidates: therapy areas with substantial Chinese-language or registry-only literature. Ask of each meta: which registered completed trials exist that it did not include?
4. Resume report #1's queue — the 339 `doi.org`-sourced corpus entries and the 1,044 unsourced `publishedHR` rows.
5. Keep looking for access counter-examples rather than waiting for them.

---

## 8. Honesty caveats

- **The Object B denominator is 5.** Selected on triage signals, so enriched for errors. A 40% error rate here says nothing about the field; it says these five were worth checking.
- **Two clinical areas only** (cardio-renal and heart failure). The thesis is stated generally; the evidence is not yet general.
- **Zero confirmed breadth failures does not mean none exist.** It means this sample did not catch one, and the sample was chosen to find checking problems.
- The Jyotsna duplication was established by reading identical n values and identical arm splits in Table 1 — an identity observation. The arithmetic reconciliation to 39,995 is diagnostic reasoning, flagged as such, not an extracted cell.
- No repo writes. Read-only throughout.

**Attribution:** abstracts and full texts retrieved from PubMed. DOIs: [10.7759/cureus.41746](https://doi.org/10.7759/cureus.41746) · [10.1097/MD.0000000000047098](https://doi.org/10.1097/MD.0000000000047098) · [10.1007/s00228-022-03408-w](https://doi.org/10.1007/s00228-022-03408-w) · [10.3389/fphar.2022.819327](https://doi.org/10.3389/fphar.2022.819327) · [10.7759/cureus.48623](https://doi.org/10.7759/cureus.48623) · [10.7759/cureus.41566](https://doi.org/10.7759/cureus.41566) · [10.1016/j.jacc.2025.10.053](https://doi.org/10.1016/j.jacc.2025.10.053)
