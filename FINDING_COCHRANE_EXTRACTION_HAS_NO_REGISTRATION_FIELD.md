# Cochrane's own structured extraction data has no registration field

**The auditability finding demonstrated in data infrastructure rather than inferred from
text — and a stronger claim than the 95%.**

## What was examined

`Pairwise70`, a public R data package of Cochrane pairwise meta-analysis datasets:

- **595 review datasets** (`CD000028_pub4_data.rda` and similar), one per Cochrane review
- **~50,000 study rows** claimed by its README; **11,949 study-analysis rows across a random
  sample of 59 datasets**, seed fixed so the sample is reproducible
- Extracted from official Cochrane data tables; last updated 2026-06-13

Individual `.rda` files were pulled from GitHub and read with R. The package was **not
cloned** — 253 MB on disk — and nothing was merged into this project.

## The finding

**There is no registration column.** The schema is:

```
Analysis.group, Analysis.number, Analysis.name, Subgroup, Applicability,
Study, Study.year,
Experimental.cases, Experimental.N, Control.cases, Control.N,
Experimental.mean, Experimental.SD, Control.mean, Control.SD,
GIV.Mean, GIV.SE, O.E, Variance, Weight, Mean, CI.start, CI.end,
Footnotes, review_url, review_doi
```

Per-arm events and denominators, continuous means and SDs, per-study effect and interval —
everything a meta-analysis needs — and **no field in which a trial registration could be
recorded.** Studies are identified as `Carter 1970`, `Coope 1986`, `SHEP 1991`: the Cochrane
author-year convention.

Registrations appear **only incidentally**, in 2 of 59 datasets (3%):

| where | datasets | |
|---|---|---|
| `Study` label happens to *be* an NCT id | 1 / 59 | 2% — **0.1%** of 1,508 study labels |
| an NCT quoted inside RoB support prose | 1 / 59 | 2% |
| **anywhere at all** | **2 / 59** | **3%** |

## Why this is stronger than the 95%

The text finding — 95% of full-text reviews name no trial registration — could be dismissed
as a *reporting* convention. Journals limit space; authors cite papers, not registries.

This cannot. **The extraction schema itself has nowhere to put a registration.** Whatever a
Cochrane team knows about which registration a study corresponds to, that knowledge does not
survive into the structured data their analyses run on. The auditability gap is not a
presentation choice; it is built into the data model.

The consequence is concrete: a third party holding all 50,000 study rows still cannot
mechanically ask *"does this row's trial match this registration?"* — the join key does not
exist.

## The exception is the interesting part

Where an NCT *does* appear in RoB support prose, it appears under **"Bias in selection of
the reported result"**:

> *"The prospective trial registry is available ClinicalTrials.gov (NCT00597194). Outcome
> analysed as pre-specified. Risk assessed to be low…"*

That is the one RoB 2 domain whose assessment **requires** checking the registry. So Cochrane
assessors do look up registrations — and the identifier survives only as free text inside a
justification, in the single place the method forced them to consult it.

**The information is obtained and then discarded.** That is a more precise and more fixable
statement of the problem than "reviews don't name registrations", and it points at a concrete
recommendation: the extraction schema should carry a registration field, which would cost
nothing at the point of extraction because the assessor already has the id in hand for D5.

## Also present, and relevant elsewhere

**7 of 59 datasets (12%) carry per-study RoB 2 domain judgements with supporting text** — all
five domains plus overall, judgement and support for each, **2,870 non-empty judgements** in
the sample. Newer reviews only. That is real assessor-read risk-of-bias data at study level,
which bears directly on the RoB gap and is noted here rather than used.

## Limits, stated

- **One extraction package, not Cochrane's internal systems.** What Cochrane holds in
  RevMan or its editorial systems is not visible here, and may well include registrations.
  The claim is about *the structured data that reaches third parties*, which is what
  determines whether anyone else can audit.
- 59 of 595 datasets sampled, seed fixed, reproducible; the 3% figure carries that
  denominator.
- The package is a **third-party extraction**, not Cochrane's publication. Its numbers are
  claims about trials, at the same tier as any prior meta-analysis, and it is used here only
  to characterise the schema — not as a source of truth about any trial.
