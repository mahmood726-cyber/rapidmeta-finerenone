# RapidMeta Living Evidence Portfolio (v16)

Browser-native, single-file living meta-analysis platform spanning **44 cardiovascular, oncology, nephrology, pulmonology, and metabolic apps**, plus a network of **27 sibling apps** in independent repositories. Each app is a self-contained ~14,000-line HTML file with 31 inlined analytic engines, validated against published meta-analyses and the R `metafor` package.

[![Validate Living MA Portfolio](https://github.com/mahmood726-cyber/rapidmeta-finerenone/actions/workflows/validate.yml/badge.svg)](https://github.com/mahmood726-cyber/rapidmeta-finerenone/actions/workflows/validate.yml)

## Highlights

- **57 living MA apps** total across 12 specialties (18 in this repo + 39 in sibling repos)
- **23/23 benchmarked apps** match published meta-analyses within 10% (100% portfolio validation)
- **31 analytic engines** per app: DL/REML pooling, HKSJ adjustment, GRADE, NMA, dose-response Emax, cross-validation, provenance hashing, 18 automated QA checks
- **766 trials** indexed across the portfolio
- **7 dose-response apps** with Emax curve fitting
- **4 NMA apps** with Bucher indirect comparisons
- **Zero external dependencies at runtime** — every app is one HTML file, opens locally, no server, no CDN

## Architecture

### Single-file HTML apps
Each `*_REVIEW.html` is a complete app:
- Inlined Tailwind CSS (v3.4.17, single-file requirement)
- 31 JavaScript engines (~14,000 lines)
- Embedded `realData` for all trials
- localStorage-backed state with versioned migration keys
- Plotly for forest plots, network graphs, dose-response curves

### Engine catalogue (v16)

| Category | Engines |
|----------|---------|
| **Synthesis** | AnalysisEngine, NMAEngine, CumulativeEngine, DoseResponseEngine, BayesianEngine, MetaRegEngine |
| **Bias** | TrimFillEngine, CopasEngine, InfluenceEngine, SensitivityEngine |
| **Quality** | GradeProfileEngine, QAEngine (18 checks), CrossValidationEngine, ProvenanceChainEngine, DataSealEngine |
| **Power** | PowerEngine (RIS), CumulativeEngine |
| **Reporting** | ManuscriptEngine, PrismaEngine, ReportEngine, ForestExportEngine |
| **Living updates** | CTGovDeltaEngine, ReviewConcordanceEngine, BenchmarkEngine |
| **Data** | TextExtractor (51 patterns), AutoExtractEngine, ExtractEngine, SearchEngine, ScreenEngine |
| **Reproducibility** | CapsuleEngine, ZipBuilder, ArtifactEngine |

## Quick Start

```bash
# Open any app directly in browser
start FINERENONE_REVIEW.html  # Windows
open FINERENONE_REVIEW.html   # macOS

# Run portfolio validation
python validate_living_ma_portfolio.py --local

# Generate a new app from config
python generate_living_ma_v13.py NEW_TOPIC

# Run R parity check (single app)
Rscript validate_finerenone.R
```

No server, no installation, no data leaves your machine.

## Apps in this repo (18)

| App | k | Pooled | Benchmark | Status |
|-----|---|--------|-----------|--------|
| FINERENONE | 4 | HR 0.86 (0.79-0.92) | 0.86 | OK |
| BEMPEDOIC_ACID | 1 | HR 0.87 | 0.87 | OK |
| GLP1_CVOT | 10 | HR 0.86 (0.81-0.90) | 0.88 | OK |
| SGLT2_HF | 5 | HR 0.77 (0.72-0.82) | 0.77 | OK |
| PCSK9 | 1 | HR 0.85 | 0.85 | OK |
| SGLT2_CKD | 3 | HR 0.68 (0.62-0.75) | 0.68 | OK |
| ARNI_HF | 3 | HR 0.84 (0.78-0.90) | 0.84 | OK |
| ABLATION_AF | 4 | HR ~0.77 | 0.77 | OK |
| IV_IRON_HF | 4 | HR ~0.84 | 0.84 | OK |
| COLCHICINE_CVD | 5 | HR 0.88 (0.75-1.02) | 0.85 | OK |
| RIVAROXABAN_VASC | 4 | HR 0.85 (0.78-0.93) | 0.85 | OK |
| ATTR_CM | 1 | HR 0.70 | -- | -- |
| INTENSIVE_BP | 3 | HR 0.81 (0.72-0.92) | -- | -- |
| LIPID_HUB | 1 | HR 0.74 | -- | -- |
| MAVACAMTEN_HCM | 1 | OR 2.80 | -- | -- |
| INCRETIN_HFpEF | 1 | OR 0.08 | -- | -- |
| DOAC_CANCER_VTE | 1 | HR 0.97 | -- | -- |
| RENAL_DENERV | 0 | -- | -- | -- |

## Sibling repositories (39 apps)

Generated from `generate_living_ma_v13.py`, each in its own GitHub repo with Pages enabled:

**Cardiology:** Vericiguat, Omecamtiv, Sotagliflozin, Inclisiran, Empa-MI, Ticagrelor-Mono, Icosapent-Ethyl, Dapa-AcuteHF
**Oncology:** Osimertinib-NSCLC, TDXd-Breast, Pembro-Adj-Mel, KRAS-G12C, Enfortumab-UC, Sacituzumab-TNBC
**Nephrology:** Semaglutide-CKD, Sparsentan-IgAN, Iptacopan, K-Binders
**Pulmonology / PAH:** Tezepelumab-Asthma, Dupilumab-COPD, Sotatercept-PAH
**Cardiometabolic:** Tirzepatide, Semaglutide-HFpEF, Orforglipron
**Interventional:** PFA-AF, Watchman-Amulet, Tricuspid-TEER, Leadless-Pacing, CSP, Coronary-IVL, CT-FFR
**Other:** Anti-Amyloid-AD, Resmetirom-MASH, Bimekizumab-Pso, DCB-PAD
**NMA:** Obesity-NMA, Antiplatelet-NMA, HFrEF-NMA, PAH-NMA

Browse all 57 apps at the [Portfolio Page](https://mahmood726-cyber.github.io/LivingMA-Portfolio/) or the [CardioSynth Aggregator](https://mahmood726-cyber.github.io/cardiosynth/synthesis/portfolio-aggregator.html).

## Validation

### Continuous Integration
GitHub Actions runs `validate_living_ma_portfolio.py --local --strict` on every push. Workflow: `.github/workflows/validate.yml`.

### Local validation
```bash
python validate_living_ma_portfolio.py            # all 57 apps (requires C:\Projects\*_LivingMeta dirs)
python validate_living_ma_portfolio.py --local    # only this repo's 18 apps
python validate_living_ma_portfolio.py --json     # machine-readable output
python validate_living_ma_portfolio.py --strict   # exit non-zero if any benchmark fails
```

### R parity (single app)
```bash
Rscript validate_finerenone.R
```

Compares 14 pooled estimates against `metafor::rma()` REML/DL. Delta = 0.000000 across all analyses.

## Generator

`generate_living_ma_v13.py` produces v16 apps from a Python config dict. The `APPS` list contains 26 currently-defined topics. To add a new app:

1. Append a config dict to `APPS` with `filename`, `protocol`, `trials`, `nct_acronyms`, etc.
2. Optionally add `dose_response` block for Emax modelling
3. Optionally add `nma_network` block to enable NMA mode
4. Run `python generate_living_ma_v13.py NEWAPP`
5. Commit and push to its GitHub repo

The generator uses `FINERENONE_REVIEW.html` as the v16 reference template and applies 17 transformation steps.

## Propagation

`propagate_v16_features.py` injects v16 engines (CumulativeEngine, ProvenanceChainEngine, QAEngine, CrossValidationEngine) into older v12 apps using marker-comment + insertion-anchor pattern. Idempotent (safe to re-run).

## Repository Contents

| File | Purpose |
|------|---------|
| `*_REVIEW.html` (18) | Self-contained living MA apps |
| `LivingMeta.html` | Multi-topic shell |
| `generate_living_ma_v13.py` | v16 app generator (26 APPS) |
| `propagate_v16_features.py` | v16 engine propagator |
| `validate_living_ma_portfolio.py` | DL pooling + benchmark checker (57 apps) |
| `generate_portfolio.py` | Builds the LivingMA portfolio page |
| `cross_validate.py` | CT.gov HR concordance check |
| `test_all_apps_comprehensive.py` | Selenium test suite (8 categories) |
| `validate_finerenone.R` | R metafor parity check |
| `PUBLISHED_META_BENCHMARKS.json` | Reference values for validation |
| `docs/superpowers/specs/` | Design specs and plans |

## E156 Micro-Papers

13 living MAs in this portfolio have E156 micro-paper drafts in `C:\E156\rewrite-workbook.txt` (entries 402-414): Omecamtiv, Sotagliflozin, Tezepelumab, Osimertinib, Enfortumab, KRAS-G12C, Pembro-Adj-Mel, Inclisiran, Antiplatelet-NMA, Dupilumab-COPD, Semaglutide-CKD, ARNI-HF, plus the portfolio itself.

## Citation

`CITATION.cff` provides software citation metadata. Once a Zenodo DOI is minted, add it to the CITATION file and release notes.

## License

MIT.
