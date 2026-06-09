# RapidMeta Living Evidence Portfolio

Browser-native living meta-analysis dashboards. The repo holds 1,521
`*_REVIEW.html` files, but **561 are thin redirect stubs** (pointing to their
`*_AUTO_FULL` sibling), so there are **~960 real dashboards**. A 2026-06
provenance pass partitioned them objectively (`scripts/partition_corpus.py`)
into three honestly-labelled tiers:

1. **Provenance-backed portfolio (~617, ≈64% of real apps)** — indexed + in the
   sitemap. Only the **17 benchmark apps** are externally *validated*; the rest are
   provenance-backed (PMID+registry), **not validated**. Each one either is
   **benchmark-validated** against a published meta-analysis +
   R `metafor` (the 17 in the reference table: FINERENONE, GLP1_CVOT, SGLT2_HF …),
   **or** pools **k≥2 trials where every pooled trial carries a PMID and a
   resolvable registry ID** (PMIDs back-filled only from a DataBankList-derived
   NCT→PMID resolver, spot-verified against PubMed — never guessed).
2. **Pooled-but-partially-provenanced** — still indexed and honestly labelled.
   These pool ≥2 trials but a trial is missing a PMID, or they are NMA / diagnostic
   (DTA) apps that pool via non-pairwise methods. Treated as scaffolds, not
   validated evidence.
3. **Quarantined (`auto-gallery.html`, de-indexed)** — **166 single-trial or
   empty pages that are NOT meta-analyses** (a meta-analysis needs ≥2 trials with
   poolable data). Each carries an in-page "AUTOMATED OUTPUT — not a validated
   meta-analysis" banner and is removed from the index and sitemap. (This is on
   top of 519 single-trial apps removed in the earlier poolability pass.)

[![Validate Living MA Portfolio](https://github.com/mahmood726-cyber/rapidmeta-finerenone/actions/workflows/validate.yml/badge.svg)](https://github.com/mahmood726-cyber/rapidmeta-finerenone/actions/workflows/validate.yml)

## Highlights

- **1,521 `*_REVIEW.html` files** (561 redirect stubs → ~960 real dashboards),
  partitioned into **~617 provenance-backed** (benchmark- or PMID+registry-backed;
  only 17 externally validated), a pooled-but-partially-provenanced middle tier, and **166 quarantined**
  single-trial/empty pages (de-indexed to `auto-gallery.html`). Full per-app lists:
  `outputs/corpus_partition.json`; re-run `python scripts/partition_corpus.py`.
- **A small set of curated apps (~17) are benchmark-validated** under
  `validate_living_ma_portfolio.py --strict` — this is a **benchmark-regression
  gate, not portfolio-wide validation**. A benchmarked app passes only if it
  actually pools **k>=2 trials**, lands within 10% of the published reference,
  **and** the reference falls inside the app's pooled CI (a k=1 app echoing one
  trial no longer counts). The **large majority of apps are UNVALIDATED** (no
  external reference); `--strict` prints benchmark **coverage** so a green run is
  not mistaken for portfolio-wide correctness, and `--require-coverage PCT`
  floors the benchmarked set so a regression can't silently empty it.
- **31 analytic engines** per app: DL/REML pooling, HKSJ adjustment, GRADE, NMA,
  dose-response Emax, cross-validation, provenance hashing, 18 automated QA checks
- **7 dose-response apps** with Emax curve fitting; **4 NMA apps** with Bucher
  indirect comparisons
- **Runtime dependencies (NOT fully offline):** most apps load **Plotly from
  `https://cdn.plot.ly`** and reference a separate `*.tailwind.css` file, so they
  need network access (or a vendored Plotly) on first load. CSP `<meta>` tags also
  allow clinicaltrials.gov / OpenAlex / webR for the live-update and R-parity
  features. (Earlier copy claiming "zero external dependencies / no CDN / one HTML
  file" described an earlier curated-only state and was inaccurate for the current
  portfolio.)

## Architecture

### HTML app structure
Each `*_REVIEW.html` is a near-complete app:
- Tailwind CSS via a sibling `*.tailwind.css` file (NOT inlined; the app is not a
  single self-contained file)
- 31 JavaScript engines (~14,000 lines)
- Embedded `realData` for all trials
- localStorage-backed state with versioned migration keys
- Plotly (loaded from `https://cdn.plot.ly`) for forest plots, network graphs,
  dose-response curves — needs network access or a vendored copy on first load

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

# Benchmark-regression gate (~17 benchmarked apps; NOT portfolio-wide validation)
python validate_living_ma_portfolio.py --local --strict --require-coverage 1.0

# Generate a new app from config
python generate_living_ma_v13.py NEW_TOPIC

# Run R parity check (single app)
Rscript validate_finerenone.R
```

No server, no installation, no data leaves your machine.

## Benchmarked reference apps

These are the **curated apps that carry an external benchmark**. They are a small
fraction of the ~1,516 files in the repo; everything not listed here (including all
`*_AUTO_FULL_REVIEW.html`) is unvalidated. Values reflect `validate_living_ma_portfolio.py
--local --strict` for the benchmarked set. k = trials contributing to live pool
(Peto-derived HRs counted; null-HR trials with usable event counts contribute via OR).

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
python validate_living_ma_portfolio.py            # this repo + sibling *_LivingMeta dirs (override roots via LIVINGMA_PORTFOLIO_ROOT env var)
python validate_living_ma_portfolio.py --local    # only this repo's apps (~1,516 scanned; ~19 carry a benchmark)
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
| `validate_living_ma_portfolio.py` | REML+HKSJ pooling + benchmark checker (57 apps) |
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
