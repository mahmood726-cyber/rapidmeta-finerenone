# Comparator scan across the indexed corpus — and why "eight in a row" is constrained

`scripts/lane_rob/find_comparator.py`. A component, not a list: every future review needs its
best published comparator identified before it can be judged.

## The scan

**28 indexed topics. 12 have at least one Cochrane candidate; 16 have none** — recorded as
UNMATCHED rather than "no comparator exists", because a search that finds nothing has not
proved absence.

⚠️ **The first run of this component returned 8, and was wrong.** It built the query with
`subprocess.list2cmdline`, which escapes quotes for a Windows command line and emitted
`\%22Cochrane...` — a broken field name matching nothing — and it ANDed three terms where two
suffice. **Both faults pointed the same way: 0 candidates for dapivirine, the one topic whose
Cochrane review we hold in full.** The known-answer control is the only reason 8 of 28 was not
reported as a finding. Fixed with proper URL quoting; the control now returns PMID 33719075.

## Candidates by age of the NEWEST Cochrane review on that question

| topic | newest | age | candidate |
|---|---|---|---|
| AGYW_HIV_PREP | 2021 | **5y** | Topical microbicides for preventing STIs |
| ALIROCUMAB_LIPID | 2020 | **6y** | PCSK9 monoclonal antibodies for prevention |
| BOCOCIZUMAB_LIPID | 2017 | **9y** | PCSK9 monoclonal antibodies for prevention |
| ROTAVIRUS_VACCINE_AFRICA | 2021 | **5y** | Vaccines for preventing rotavirus diarrhoea |
| APIXABAN_VTE_PROPHYLAXIS | 2021 | 5y | Oral anticoagulation in people with cancer |
| TIGECYCLINE_CIAI | 2016 | 10y | Antibiotics for ventilator-associated pneumonia |
| ROSUVASTATIN | 2024 | 2y | Statins for primary prevention of VTE |
| APIXABAN_VTE_TREATMENT | 2025 | 1y | Interrupted vs uninterrupted anticoagulation |
| SGLT2_HF · CAB_PREP · INCRETIN_HFpEF · IV_IRON_HF | 2025–26 | 0–1y | — |

## ⛔ The constraint, stated before any selection

**PICO matching is a judgement and the component does not assert it.** Reading the twelve:

- **Genuine matches, ≥3 years old: about four** — dapivirine (confirmed, we hold it),
  alirocumab and bococizumab (both PCSK9 monoclonals, plausibly in scope of the same review),
  rotavirus.
- **Not matches**: TIGECYCLINE_CIAI matched a *ventilator-associated pneumonia* review;
  SGLT2_HF matched a *GLP-1 agonist* review; IV_IRON_HF matched iron supplementation *to reduce
  blood-donor deferral*. Same words, different questions.
- **Too recent to test the currency advantage**: four candidates are 0–1 years old.

⇒ **We cannot run eight comparisons against an aged Cochrane review, because the indexed corpus
does not contain eight topics that have one.** Roughly four do. That is a fact about our topic
selection, not about the method, and it is better said now than after four wins and four
strained matches.

**Three ways forward, and the choice is Mahmood's:**
1. **Four comparisons, honestly matched** — a smaller claim that survives a referee.
2. **Widen the comparator beyond Cochrane** to any published systematic review of the same
   question. The pilot already showed the authority prior does not dominate, so a non-Cochrane
   comparator is a legitimate test — and there are many more of them.
3. **Index topics that have aged Cochrane reviews.** Slowest, and it changes what the corpus is
   for.

## The selection rule, written before choosing

Each criterion is a structural advantage that has been **measured**, not assumed:

1. a published systematic review of the same PICO exists and is **≥3 years old** — currency is
   our largest measured edge, and their evidence gap is the thing that decays
2. **post-comparator evidence exists** — a new trial, a regulatory action, a guideline change
3. the trials are **registry-rich with results posted** — our data advantage
4. **small k** — small-sample intervals are handled properly here and usually are not
5. **we hold the primary reports** — the binding constraint at 37 of 353 trials

⚠️ **And the rule is published with the results.** "Eight chosen because our advantages apply,
and here is the rule" is defensible; "eight cherry-picked wins presented as typical" is not.
