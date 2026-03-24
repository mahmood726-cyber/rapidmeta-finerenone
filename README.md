# RapidMeta Cardiology - Finerenone Living Meta-Analysis

Browser-based living meta-analysis platform for finerenone cardiovascular and renal outcome trials, validated against the R `metafor` package and 17 published meta-analyses.

## Quick Start

1. Open `FINERENONE_REVIEW.html` in Chrome, Firefox, Safari, or Edge.
2. Review the built-in analyses and exported figures locally in the browser.
3. Run the R validation script if you want an independent parity check.

No server is required and no data is transmitted externally during normal use.

## R Validation

```bash
Rscript validate_finerenone.R
```

Validation scope:

- Reproduces 14 pooled estimates across OR, RR, and HR analyses.
- Checks REML tau-squared against `metafor::rma(method = "REML")`.
- Compares outputs against 17 published finerenone meta-analyses.
- Generates forest and funnel plots as PDFs.
- Runs DL versus REML sensitivity analysis.

## Included Trials

| Trial | Phase | N | Primary Endpoint | PMID |
|-------|-------|------:|-----------------|------:|
| FIDELIO-DKD | III | 5674 | Renal composite | 33264825 |
| FIGARO-DKD | III | 7437 | CV composite (MACE) | 34449181 |
| FINEARTS-HF | III | 6001 | Worsening HF / CV death | 39225278 |
| ARTS-DN | IIb | 823 | UACR (excluded from pooling) | 26325557 |

## Key Results

| Outcome | k | OR (95% CI) | RR (95% CI) | HR (95% CI) | I-squared |
|---------|---|-------------|-------------|-------------|-----------|
| MACE | 2 | 0.86 (0.78-0.95) | 0.88 (0.80-0.96) | 0.87 (0.79-0.95) | 0% |
| All-cause mortality | 3 | 0.90 (0.83-0.99) | 0.92 (0.85-0.99) | 0.91 (0.84-0.99) | 0% |
| Renal composite | 2 | 0.83 (0.75-0.92) | 0.86 (0.79-0.93) | 0.84 (0.77-0.92) | 0% |
| HF hospitalisation | 2 | 0.78 (0.64-0.94) | 0.79 (0.66-0.94) | 0.78 (0.65-0.94) | 20-22% |
| Hyperkalemia | 3 | 2.25 (2.03-2.50) | 2.09 (1.90-2.29) | N/A | 0% |

Safety analyses use the safety-analysis-set denominators rather than FAS denominators.

DL and REML produce identical pooled estimates across the 14 validated analyses (`delta = 0.000000`).

## Repository Contents

- `FINERENONE_REVIEW.html`: main browser application.
- `validate_finerenone.R`: `metafor`-based validation script.
- `FINERENONE_R_validation.R`: base-R fallback validation script.
- `F1000_RapidMeta_Finerenone_Article.md`: manuscript draft.
- `finerenone_meta_analyses_database.md`: curated comparison set of published meta-analyses.
- `Figure *.png`: manuscript figures and screenshots.

## Citation

Use `CITATION.cff` for software citation metadata.

If a tagged GitHub release and Zenodo archive are created, add the minted DOI to `CITATION.cff` and the release notes.

## License

MIT.
