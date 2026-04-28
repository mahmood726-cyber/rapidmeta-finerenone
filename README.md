# RapidMeta Living Evidence Portfolio (v16)

Browser-native, single-file living meta-analysis platform spanning **44 cardiovascular, oncology, nephrology, pulmonology, and metabolic apps**, plus a network of **27 sibling apps** in independent repositories. Each app is a self-contained ~14,000-line HTML file with 31 inlined analytic engines, validated against published meta-analyses and the R `metafor` package.

[![Validate Living MA Portfolio](https://github.com/mahmood726-cyber/rapidmeta-finerenone/actions/workflows/validate.yml/badge.svg)](https://github.com/mahmood726-cyber/rapidmeta-finerenone/actions/workflows/validate.yml)

## Highlights

- **57 living MA apps** total across 12 specialties (18 in this repo + 39 in sibling repos)
- **17/17 in-repo apps** within 10% of published benchmarks under `--strict` (1 app, RENAL_DENERV, uses MD outcome handled by HTML JS engine and skipped by Python validator)
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

Values reflect live `validate_living_ma_portfolio.py --local --strict` output as of 2026-04-16 (17/17 within 10%, exit 0). k = trials contributing to live pool (Peto-derived HRs counted; null-HR trials with usable event counts contribute via OR).

| App | k | Live pool | Benchmark | Outcome | Notes |
|-----|---|-----------|-----------|---------|-------|
| FINERENONE | 4 | HR 0.86 (0.79-0.92) | 0.86 | CV composite | FIDELIO+FIGARO+FINEARTS-HF + ARTS-DN OR |
| GLP1_CVOT | 10 | HR 0.86 (0.81-0.90) | 0.88 | MACE | 10-trial GLP-1 CVOT pool |
| SGLT2_HF | 5 | HR 0.77 (0.72-0.82) | 0.77 | MACE | EMPEROR/DAPA-HF/DELIVER family |
| SGLT2_CKD | 3 | HR 0.68 (0.62-0.75) | 0.68 | KFE/CV death | DAPA-CKD+EMPA-KIDNEY+CREDENCE |
| ARNI_HF | 3 | HR 0.84 (0.78-0.90) | 0.84 | CV death/HFH | PARADIGM+PARADISE-MI+PARAGON |
| ABLATION_AF | 4 | HR 0.77 (0.68-0.87) | 0.77 | MACE | CABANA+CASTLE-AF family |
| IV_IRON_HF | 4 | HR 0.87 (0.79-0.96) | 0.84 | MACE | CONFIRM+AFFIRM+IRONMAN+HEART-FID |
| COLCHICINE_CVD | 5 | HR 0.81 (0.69-0.95) | 0.85 | MACE | COLCOT+LoDoCo2+COPS+CLEAR-SYNERGY+CONVINCE |
| RIVAROXABAN_VASC | 4 | HR 0.85 (0.78-0.93) | 0.85 | MACE | COMPASS+VOYAGER+COMMANDER+ATLAS |
| ATTR_CM | 4 | HR 0.71 (0.59-0.86) | 0.71 | ACM | ATTR-ACT+ATTRibute+HELIOS-B + APOLLO-B Peto |
| INTENSIVE_BP | 5 | HR 0.79 (0.71-0.87) | 0.79 | MACE | SPRINT-SENIOR/CKD strata + ACCORD-BP+STEP+SPS3 |
| LIPID_HUB | 5 | HR 0.89 (0.76-1.04) | 0.89 | MACE | 5-trial EPA/n-3 pool, I²=78%; REDUCE-IT+STRENGTH+VITAL+OMEMI+RESPECT-EPA |
| RENAL_DENERV | 5 (MD) | MD -5.12 mmHg (-6.85,-3.40) | -5.12 | Office SBP | SPYRAL+RADIANCE+REQUIRE — continuous-MD outcome (HTML JS engine; Python validator skips) |
| INCRETIN_HFpEF | 3 | HR 0.41 (0.22-0.79) | 0.41 | HF events composite | SUMMIT (published) + STEP-HFpEF/DM (Peto from worsening-HF events); outcome heterogeneity flagged |
| BEMPEDOIC_ACID | 4 | HR 0.90 (0.72-1.12) | 0.87 | MACE / lipid CVAE | CLEAR Outcomes (Cox) + CLEAR Harmony (Cox) + Wisdom/Serenity (OR from event counts); pool drifts off CVOT-only benchmark |
| PCSK9 | 2 | HR 0.85 (0.80-0.90) | 0.85 | MACE | FOURIER + ODYSSEY Outcomes (Guedeney 2020) |
| MAVACAMTEN_HCM | 3 | OR 6.67 (2.09-21.30) | 6.67 | NYHA Δ | EXPLORER+VALOR+China-Phase3; NYHA improvement OR, not mortality |
| DOAC_CANCER_VTE | 4 | HR 0.60 (0.36-1.00) | 0.55 | VTE recurrence | HOKUSAI+SELECT-D+ADAM+CARAVAGGIO |

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
python validate_living_ma_portfolio.py            # all 57 apps (requires sibling *_LivingMeta dirs; override roots via LIVINGMA_PORTFOLIO_ROOT env var)
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

## DTA review portfolio (3 reviews from a shared template)

Three Diagnostic Test Accuracy (DTA) living reviews share a single `dta_template.html` plus per-topic JSON configs:

```
dta_template.html                         # shared template (~6,000 lines)
topics/
  _schema.md                              # config-field documentation
  genexpert_ultra_tb.config.json          # GeneXpert Ultra (TB)
  covid_antigen.config.json               # SARS-CoV-2 rapid antigen
  mpmri_prostate.config.json              # multiparametric MRI (prostate)
scripts/
  build_dta_review.mjs                    # build script (vanilla Node, no deps)
GENEXPERT_ULTRA_TB_DTA_REVIEW.html        # GENERATED -- do not edit by hand
COVID_ANTIGEN_DTA_REVIEW.html             # GENERATED
MPMRI_PROSTATE_DTA_REVIEW.html            # GENERATED
```

The shared engine, validator, and service worker (`rapidmeta-dta-engine-v1.js`, `webr-dta-validator.js`, `coi-serviceworker.js`) are unchanged for any topic.

### Building all three reviews

```bash
npm run build:dta              # builds GeneXpert + COVID + mpMRI
npm run build:dta:genexpert    # one topic only
npm run test:dta               # 31 engine unit tests
```

Or directly:

```bash
node scripts/build_dta_review.mjs topics/genexpert_ultra_tb.config.json
```

### Adding a new DTA topic

1. Copy an existing config (e.g. `topics/genexpert_ultra_tb.config.json`) to `topics/<new_slug>.config.json`.
2. Edit topic-specific fields. Schema documented in `topics/_schema.md`. Critical fields:
   - `topic_slug`, `output_filename`, `ls_prefix` (must be unique per topic)
   - `tiers[]`, `default_tier_slug`, `all_tier_slug`
   - `subgroups_axes[]`, `ext_choices`, `quadas_flags`, `screening_cards[]`
   - `manuscript.*` strings
   - `trials` (the embedded JSON dataset)
3. Add a `build:dta:<slug>` line to `package.json` and chain it into `build:dta`.
4. Run `npm run build:dta` and smoke-test the generated HTML in a browser.

The build script enforces:
- 0 unsubstituted `{{key}}` placeholders
- Required fields fail-closed
- Generated HTML reproduces existing functionality (17 tabs, edit mode, sign-off, JSON export)
- Each topic has a unique localStorage prefix (no cross-talk between reviews)

## E156 Micro-Papers

13 living MAs in this portfolio have E156 micro-paper drafts in `C:\E156\rewrite-workbook.txt` (entries 402-414): Omecamtiv, Sotagliflozin, Tezepelumab, Osimertinib, Enfortumab, KRAS-G12C, Pembro-Adj-Mel, Inclisiran, Antiplatelet-NMA, Dupilumab-COPD, Semaglutide-CKD, ARNI-HF, plus the portfolio itself.

## Citation

`CITATION.cff` provides software citation metadata. Once a Zenodo DOI is minted, add it to the CITATION file and release notes.

## License

MIT.
