# Pre-registration: applying an intervention-review rubric to six DTA pages

Written BEFORE running. The harness was built for intervention reviews — pooled effect
measures, inverse-variance weighting, RoB 2. Diagnostic accuracy is a different animal:
paired sensitivity and specificity, bivariate or HSROC models, QUADAS-2. Several checks will
be wrong here in ways that are *right* for the domain they were built for.

My detectors' measured failure direction is **toward accusing the page**. A rubric applied
outside its domain is the ideal condition for that, so the predictions are recorded first and
scored afterwards.

## The six

`PTAU217_AD` · `HSCTN_NSTEMI` · `COVID_ANTIGEN` · `MPMRI_PROSTATE` · `GENEXPERT_ULTRA_TB` ·
`DDIMER_PE`

## Predictions

| check | prediction | why |
|---|---|---|
| `arithmetic` | **NOT-ASSESSABLE** | parser needs a contributing-trials table plus a τ² table in the intervention-review shape; DTA pools Se/Sp bivariately |
| `method_label` | **NOT-ASSESSABLE** | HKSJ is an inverse-variance construct; DTA uses bivariate/HSROC and should never name it |
| `three_surfaces` | **NOT-ASSESSABLE** | same parser dependency |
| `scale_vs_measure` | **FALSE FAIL possible** | `DOR` is in my RATIO_MEASURES and is a log-scale quantity, but Se/Sp are logit-scale; if a page says "natural" about a proportion my check may fire wrongly |
| `direction_label` | **FALSE FAIL possible** | already retired to ADVISORY at precision 0/2. Higher sensitivity is better; my HIGHER_BETTER list has no Se/Sp terms, so a correct label could read as contradicting |
| `rob_outcome_column` | **FALSE FAIL EXPECTED** | asserts RoB 2's per-result rule. **QUADAS-2 is assessed per review, not per result.** A FAIL here is my rubric being wrong, not the page |
| `rob_no_information` | **FALSE FAIL possible** | QUADAS-2 permits "Unclear" as a legitimate domain judgement. RoB 2 does not. A FAIL here is a domain error |
| `va_denominator` | uncertain | may work if the VA states "N studies, M patients" |
| `self_refuting_claim` | should work | domain-agnostic: a value and its own refutation adjacent |
| `falsy_render` | should work | domain-agnostic |
| `nct_links` | **NOT-ASSESSABLE likely** | DTA primary studies are often not registered trials |
| `page_stamped` | should work | domain-agnostic |
| `broken_anchor` / `promised_absent` | should work | domain-agnostic |

## Rule for scoring

Any FAIL on `rob_outcome_column`, `rob_no_information`, `scale_vs_measure` or
`direction_label` is treated as **suspect until hand-checked**, and reported as a rubric
misfire unless the page is shown to be wrong on the domain's own terms.

Only findings that survive hand-checking against DTA methodology are reported as defects.
