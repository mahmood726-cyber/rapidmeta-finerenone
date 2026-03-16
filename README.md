# RapidMeta Cardiology — Finerenone Living Meta-Analysis

A browser-based living meta-analysis platform for finerenone cardiovascular and renal outcome trials, validated against the R metafor package and 17 published meta-analyses.

## Quick Start

1. Open `FINERENONE_REVIEW.html` in any modern browser (Chrome, Firefox, Safari, Edge)
2. No installation, no server, no data transmitted externally

## R Validation

```bash
# Requires R >= 4.1, metafor >= 4.0
Rscript validate_finerenone.R
```

The validation script:
- Reproduces all 14 pooled estimates (5 outcomes x OR/RR/HR) using `metafor::rma()` (DerSimonian-Laird)
- Validates REML tau-squared against metafor `method = "REML"` for all 14 analyses
- Compares against 17 published finerenone meta-analyses (88% concordant within 0.03)
- Generates forest plots and funnel plots as PDFs
- Runs DL vs REML sensitivity analysis

## Included Trials

| Trial | Phase | N | Primary Endpoint | PMID |
|-------|-------|------|-----------------|------|
| FIDELIO-DKD | III | 5,674 | Renal composite | 33264825 |
| FIGARO-DKD | III | 7,437 | CV composite (MACE) | 34449181 |
| FINEARTS-HF | III | 6,001 | Worsening HF / CV death | 39225278 |
| ARTS-DN | IIb | 823 | UACR (excluded from pooling) | 26325557 |

## Key Results (validated against R metafor)

| Outcome | k | OR (95% CI) | RR (95% CI) | HR (95% CI) | I-squared |
|---------|---|-------------|-------------|-------------|-----------|
| MACE | 2 | 0.86 (0.78-0.95) | 0.88 (0.80-0.96) | 0.87 (0.79-0.95) | 0% |
| All-cause mortality | 3 | 0.90 (0.83-0.99) | 0.92 (0.85-0.99) | 0.91 (0.84-0.99) | 0% |
| Renal composite | 2 | 0.83 (0.75-0.92) | 0.86 (0.79-0.93) | 0.84 (0.77-0.92) | 0% |
| HF hospitalisation | 2 | 0.78 (0.64-0.94) | 0.79 (0.66-0.94) | 0.78 (0.65-0.94) | 20-22% |
| Hyperkalemia* | 3 | 2.25 (2.03-2.50) | 2.09 (1.90-2.29) | N/A | 0% |

*Safety outcome; uses safety analysis set denominators (not FAS).

DL and REML produce identical pooled estimates for all 14 analyses (delta = 0.000000).

## Repository Contents

- `FINERENONE_REVIEW.html` — The application (single-file, ~7,800 lines)
- `validate_finerenone.R` — R validation script (metafor-based)
- `FINERENONE_R_validation.R` — Base-R validation script (no dependencies)
- `F1000_RapidMeta_Finerenone_Article.md` — F1000Research manuscript
- `finerenone_meta_analyses_database.md` — Database of 17 published meta-analyses
- `Figure *.png` — Screenshots for manuscript

## License

MIT
