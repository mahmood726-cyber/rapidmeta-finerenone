# The registration is looked up, written into a justification, and then lost

**Cochrane assessors obtain trial registration numbers because the method requires it. The
extraction schema has nowhere to keep them. The number survives only as free text inside a
risk-of-bias justification.**

That is a more precise claim than "reviews don't name registrations", and a more fixable one.

---

## The three parts, in order

### 1. The loss point

The structured extraction schema — the data a third party actually receives — has **no
registration field**:

```
Analysis.group, Analysis.number, Analysis.name, Subgroup, Applicability,
Study, Study.year,
Experimental.cases, Experimental.N, Control.cases, Control.N,
Experimental.mean, Experimental.SD, Control.mean, Control.SD,
GIV.Mean, GIV.SE, O.E, Variance, Weight, Mean, CI.start, CI.end,
Footnotes, review_url, review_doi
```

Everything a meta-analysis needs, and nowhere to record which trial a row *is*. Studies are
`Carter 1970`, `Coope 1986`, `SHEP 1991`.

### 2. The evidence it was obtained

Registrations appear in the data — just not where they can be used. Where an NCT does show
up, it is inside the support text for **"Bias in selection of the reported result"**:

> *"The prospective trial registry is available ClinicalTrials.gov (NCT00597194). Outcome
> analysed as pre-specified. Risk assessed to be low…"*

That is **the one RoB 2 domain whose assessment requires consulting the registry.** The
assessor had the identifier in hand, used it to reach a judgement, and wrote it into a
sentence. It exists in the record because the method forced the lookup — and it exists
*only* there.

### 3. The remedy, which costs nothing

**A registration column in the extraction schema.** At the moment of extraction the number is
already in the assessor's possession; recording it is a keystroke rather than a task. No new
lookup, no new burden, no methodological change.

The whole auditability gap for this class of defect closes at that point: a third party could
then ask, mechanically, whether a given row's trial matches a given registration.

---

## The limit that makes this fair rather than an accusation

**This is one public extraction package, not Cochrane's internal systems.** RevMan and
Cochrane's editorial infrastructure may well hold registrations; none of that is visible
here and nothing in this document claims otherwise.

**The claim is about the structured data that reaches third parties** — which is precisely
what determines whether anyone outside can audit. A registration held internally and not
exported has the same effect on an external checker as one never obtained.

---

## What was examined

`Pairwise70`, a public R data package of Cochrane pairwise meta-analysis datasets:

- **595 review datasets** (`CD000028_pub4_data.rda` and similar), one per Cochrane review
- **~50,000 study rows** claimed by its README; **11,949 study-analysis rows across a random
  sample of 59 datasets**, seed fixed so the sample is reproducible
- Extracted from official Cochrane data tables; last updated 2026-06-13

Individual `.rda` files were pulled from GitHub and read with R. The package was **not
cloned** — 253 MB on disk — and nothing was merged into this project.

## The numbers behind it

**Correction to an earlier statement of this finding.** It was first reported as "no NCT
anywhere", from one file plus a grep of `R/`, `man/` and `README`. That was **right about the
schema and wrong about the cells** — a sample of eleven datasets found 27 cells matching
`NCT########`. The distinction matters, because the cells are what make a partial join
possible at all.

Registrations appear **incidentally**, in 2 of 59 datasets (3%):

| where | datasets | |
|---|---|---|
| `Study` label happens to *be* an NCT id | 1 / 59 | 2% — **0.1%** of 1,508 study labels |
| an NCT quoted inside RoB support prose | 1 / 59 | 2% |
| **anywhere at all** | **2 / 59** | **3%** |

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
