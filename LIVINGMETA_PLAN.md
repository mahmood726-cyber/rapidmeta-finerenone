# LivingMeta v1.0 — Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the first living, self-discovering, multi-method, TruthCert-certified meta-analysis engine that beats every published colchicine-CVD meta-analysis on trial count, methodological rigor, bias assessment, reproducibility, and currency.

**Architecture:** Single-file HTML app (~20-25K lines) with CONFIG_LIBRARY pattern. Colchicine-CVD is the flagship config with 5 blinded-verified baseline trials. Three-phase pipeline: DISCOVER (CT.gov + PubMed + OpenAlex) → EXTRACT (structured abstract parsing + CT.gov results) → SYNTHESIZE (dual-track HR+OR, 9 tau² estimators, HKSJ, Bayesian MCMC, 12+ bias tests, GRADE, TruthCert). Browser-native, no server, all APIs CORS-friendly.

**Tech Stack:** HTML5, Tailwind CSS (CDN), Plotly.js (CDN), vanilla JS (no frameworks). APIs: ClinicalTrials.gov v2, Europe PMC REST, OpenAlex REST.

**Source Codebases:** (paths relative to the project repo root)
- `COLCHICINE_CVD_REVIEW.html` — Discovery APIs, baseline data, basic analysis engines, UI patterns
- Truthcert1_work (sibling repo) — Superior statistical engine (metajs-lib/meta-analysis.js + app_beautified.js), TruthCert certification, GRADE, verdict system

---

## File Structure

Single file: `LivingMeta.html` (in the project repo root)

Internal sections (marked with banner comments):
```
<!-- ═══ SECTION 1: HEAD + CDN ═══ -->
<!-- ═══ SECTION 2: CSS (Tailwind + custom) ═══ -->
<!-- ═══ SECTION 3: HTML STRUCTURE (8 tabs) ═══ -->
<!-- ═══ SECTION 4: CONFIG_LIBRARY ═══ -->
<!-- ═══ SECTION 5: DISCOVERY ENGINE ═══ -->
<!-- ═══ SECTION 6: EXTRACTION ENGINE ═══ -->
<!-- ═══ SECTION 7: STATISTICAL CORE ═══ -->
<!-- ═══ SECTION 8: SYNTHESIS ENGINE ═══ -->
<!-- ═══ SECTION 9: BIAS ASSESSMENT ═══ -->
<!-- ═══ SECTION 10: GRADE + VERDICT ═══ -->
<!-- ═══ SECTION 11: VISUALIZATION ═══ -->
<!-- ═══ SECTION 12: TRUTHCERT ═══ -->
<!-- ═══ SECTION 13: UI CONTROLLERS ═══ -->
<!-- ═══ SECTION 14: APP INIT ═══ -->
```

---

## Chunk 1: Foundation + Config + Baseline Data

### Task 1: HTML skeleton with 8-tab UI

**Files:**
- Create: `LivingMeta.html` (in the project repo root)

- [ ] **Step 1: Create base HTML with CDN imports**

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>LivingMeta v1.0 — Self-Discovering Certified Meta-Analysis</title>
  <script src="https://cdn.plot.ly/plotly-2.27.0.min.js"><\/script>
  <script src="https://cdn.tailwindcss.com"><\/script>
  <style>
    /* Custom styles: dark mode, tab system, badges, scrollbars */
  </style>
</head>
<body class="bg-gray-50 dark:bg-gray-900 text-gray-900 dark:text-gray-100">
  <!-- Header with title, config selector, dark mode toggle -->
  <!-- 8-tab navigation bar -->
  <!-- Tab panels: protocol, search, screen, extract, synthesize, bias, grade, certify -->
</body>
```

- [ ] **Step 2: Build 8-tab navigation system**

Port tab system from TruthCert (app_beautified.js lines 388-399):
- Tab buttons with `data-tab` attributes
- Panel containers with `id="panel-{tab}"`
- Active state toggling via classList

Tabs: Protocol | Search | Screen | Extract | Synthesize | Bias | GRADE | Certify

- [ ] **Step 3: Protocol tab content**

PICO display, config selector dropdown, outcome list, search strategy preview.
Port from COLCHICINE_CVD_REVIEW.html lines 391-586.

- [ ] **Step 4: Verify renders in browser**

Open in Chrome, verify all 8 tabs switch correctly, dark mode toggles.

- [ ] **Step 5: Commit skeleton**

### Task 2: CONFIG_LIBRARY with colchicine-CVD baseline

- [ ] **Step 1: Define CONFIG_LIBRARY structure**

```javascript
const CONFIG_LIBRARY = {
  colchicine_cvd: {
    name: 'Colchicine for Atherosclerotic CVD',
    version: '1.0',
    pico: {
      P: 'Adults with established ASCVD (chronic CAD, recent ACS, non-cardioembolic stroke/TIA)',
      I: 'Low-dose colchicine (0.5 mg daily)',
      C: 'Placebo or usual care',
      O: 'Composite MACE (CV Death, MI, Stroke, Ischaemia-Driven Revascularization)'
    },
    outcomes: [
      { key: 'MACE', label: 'Composite MACE', type: 'PRIMARY' },
      { key: 'CVD', label: 'Cardiovascular Death', type: 'SECONDARY' },
      { key: 'ACM', label: 'All-Cause Mortality', type: 'SECONDARY' },
      { key: 'MI', label: 'Myocardial Infarction', type: 'SECONDARY' },
      { key: 'Stroke', label: 'Stroke', type: 'SECONDARY' }
    ],
    searchQueries: {
      ctgov: {
        terms: 'colchicine AND (cardiovascular OR coronary OR myocardial OR stroke OR MACE)',
        filters: { phase: ['PHASE2','PHASE3'], status: ['COMPLETED','ACTIVE_NOT_RECRUITING','TERMINATED'] }
      },
      pubmed: 'colchicine[ti] AND (randomized controlled trial[pt]) AND (cardiovascular OR MACE OR coronary OR myocardial OR stroke)',
      openalex: 'colchicine cardiovascular randomized controlled trial'
    },
    screeningCriteria: {
      include: ['RCT', 'colchicine intervention arm', 'CV outcome endpoint', 'human adults'],
      exclude: ['non-randomized', 'pericarditis-only', 'gout-only without CV outcomes', 'dose-finding Phase I', 'pediatric']
    },
    verifiedBaseline: { /* 5 trials from COLCHICINE_CVD_REVIEW.html */ },
    verifiedHash: null // computed at init
  }
};
```

- [ ] **Step 2: Port all 5 verified trials into verifiedBaseline**

Copy from COLCHICINE_CVD_REVIEW.html lines 1473-1631 (realData object).
All fields: name, phase, year, tE, tN, cE, cN, group, publishedHR, hrLCI, hrUCI, allOutcomes[], rob[], snippet, evidence[].

These are LOCKED — blinded-verified across 3 rounds, 12 fixes applied.

- [ ] **Step 3: App state management**

```javascript
const AppState = {
  config: 'colchicine_cvd',
  discovered: [],      // from API search
  screened: [],        // after include/exclude
  extracted: [],       // with parsed data
  baseline: [],        // from verifiedBaseline (locked)
  merged: [],          // baseline + extracted (analysis input)
  results: null,       // synthesis output
  certBundle: null,    // TruthCert bundle
  searchLog: [],
  auditLog: [],
  settings: {
    confLevel: 0.95,
    tau2Method: 'REML',
    useHKSJ: true,
    bayesianPrior: 'informative',
    continuityCorrection: 'constant'
  }
};
```

- [ ] **Step 4: localStorage persistence with migration**

Unique key: `livingmeta_${config}_v1`. Save/load AppState. Migration from older versions.

- [ ] **Step 5: Verify baseline data loads and displays**

---

## Chunk 2: Discovery Pipeline

### Task 3: ClinicalTrials.gov API v2 search

- [ ] **Step 1: Implement CT.gov search function**

Port from COLCHICINE_CVD_REVIEW.html lines 3954-4242, enhance with:

```javascript
async function searchCTgov(config) {
  const url = new URL('https://clinicaltrials.gov/api/v2/studies');
  url.searchParams.set('query.term', config.searchQueries.ctgov.terms);
  url.searchParams.set('filter.overallStatus', config.searchQueries.ctgov.filters.status.join(','));
  url.searchParams.set('filter.phase', config.searchQueries.ctgov.filters.phase.join(','));
  url.searchParams.set('pageSize', '100');
  url.searchParams.set('fields', 'NCTId,BriefTitle,Acronym,OverallStatus,Phase,EnrollmentCount,StartDate,CompletionDate,ResultsFirstPostDate,Condition,InterventionName,StudyType,DesignAllocation');

  const resp = await fetchWithTimeout(url, 15000);
  const data = await resp.json();

  return data.studies.map(s => ({
    nctId: s.protocolSection?.identificationModule?.nctId,
    title: s.protocolSection?.identificationModule?.briefTitle,
    acronym: s.protocolSection?.identificationModule?.acronym,
    phase: s.protocolSection?.designModule?.phases,
    enrollment: s.protocolSection?.designModule?.enrollmentInfo?.count,
    status: s.protocolSection?.statusModule?.overallStatus,
    hasResults: s.hasResults,
    startDate: s.protocolSection?.statusModule?.startDateStruct?.date,
    completionDate: s.protocolSection?.statusModule?.statusVerifiedDate,
    source: 'ctgov'
  }));
}
```

- [ ] **Step 2: Implement CT.gov results fetcher for trials with posted results**

```javascript
async function fetchCTgovResults(nctId) {
  const url = `https://clinicaltrials.gov/api/v2/studies/${nctId}?fields=ResultsSection`;
  // Extract outcome measures, event counts, statistical analyses
  // Return structured { outcomes: [{ title, tE, tN, cE, cN, effect, ci, pval }] }
}
```

- [ ] **Step 3: Auto-screening logic**

```javascript
function autoScreen(trial, config) {
  const reasons = [];
  // Must be RCT
  if (!trial.allocation?.includes('Randomized')) reasons.push('NOT_RCT');
  // Must have colchicine arm
  if (!trial.interventions?.some(i => /colchicine/i.test(i))) reasons.push('NO_COLCHICINE');
  // Must have CV outcome
  if (!trial.conditions?.some(c => /cardiovascular|coronary|myocardial|stroke|MACE/i.test(c)))
    reasons.push('NO_CV_OUTCOME');
  // Exclude if already in baseline
  if (AppState.baseline.some(b => b.nctId === trial.nctId)) reasons.push('IN_BASELINE');

  return { include: reasons.length === 0, reasons, confidence: reasons.length === 0 ? 'HIGH' : 'AUTO_EXCLUDE' };
}
```

- [ ] **Step 4: Render search results in Search tab**

Table with: NCT ID, acronym, title, phase, enrollment, status, has_results, screen_decision.
Manual override buttons (include/exclude/review).

### Task 4: PubMed / Europe PMC search

- [ ] **Step 1: Implement PubMed search via Europe PMC**

Port from COLCHICINE_CVD_REVIEW.html lines 4560-5160:

```javascript
async function searchPubMed(config) {
  const query = encodeURIComponent(config.searchQueries.pubmed);
  const url = `https://www.ebi.ac.uk/europepmc/webservices/rest/search?query=${query}&resultType=core&pageSize=100&format=json`;
  const resp = await fetchWithTimeout(url, 15000);
  const data = await resp.json();

  return data.resultList.result.map(r => ({
    pmid: r.pmid,
    doi: r.doi,
    title: r.title,
    authors: r.authorString,
    journal: r.journalTitle,
    year: parseInt(r.pubYear),
    abstract: r.abstractText,
    isOpenAccess: r.isOpenAccess === 'Y',
    pmcId: r.pmcid,
    source: 'pubmed'
  }));
}
```

- [ ] **Step 2: Implement OpenAlex search**

```javascript
async function searchOpenAlex(config) {
  const query = encodeURIComponent(config.searchQueries.openalex);
  const url = `https://api.openalex.org/works?search=${query}&filter=type:article&per_page=50&mailto=livingmeta@example.com`;
  const resp = await fetchWithTimeout(url, 15000);
  const data = await resp.json();

  return data.results.map(r => ({
    oaId: r.id,
    doi: r.doi,
    title: r.title,
    year: r.publication_year,
    citedByCount: r.cited_by_count,
    isOpenAccess: r.open_access?.is_oa,
    abstract: reconstructAbstract(r.abstract_inverted_index),
    source: 'openalex'
  }));
}

function reconstructAbstract(invertedIndex) {
  if (!invertedIndex) return null;
  const words = [];
  for (const [word, positions] of Object.entries(invertedIndex)) {
    for (const pos of positions) words[pos] = word;
  }
  return words.join(' ');
}
```

### Task 5: Deduplication + PRISMA flow

- [ ] **Step 1: Cross-source deduplication**

```javascript
function deduplicateResults(ctgov, pubmed, openalex) {
  const unified = new Map(); // key: nctId or doi or normalized title

  // Priority: CT.gov > PubMed > OpenAlex
  for (const t of ctgov) unified.set(t.nctId, { ...t, sources: ['ctgov'] });

  for (const p of pubmed) {
    // Match by NCT ID in abstract, DOI, or title similarity
    const nctMatch = p.abstract?.match(/NCT\d{8}/)?.[0];
    const existing = nctMatch ? unified.get(nctMatch) : findByDOI(unified, p.doi) ?? findByTitle(unified, p.title);
    if (existing) {
      existing.sources.push('pubmed');
      existing.pmid = p.pmid;
      existing.abstract = p.abstract;
      existing.doi = existing.doi || p.doi;
    } else {
      unified.set(p.pmid || p.doi, { ...p, sources: ['pubmed'] });
    }
  }

  // Same for OpenAlex...
  return Array.from(unified.values());
}
```

- [ ] **Step 2: PRISMA flow counter**

Track: identified → screened → eligible → included. Render as visual flow diagram.

- [ ] **Step 3: Render PRISMA in Search tab**

---

## Chunk 3: Extraction Engine

### Task 6: Abstract text parser

- [ ] **Step 1: Implement structured abstract parsing**

```javascript
const AbstractParser = {
  // Hazard ratio: "HR 0.69; 95% CI 0.57-0.83" or "hazard ratio, 0.69; 95% CI, 0.57 to 0.83"
  extractHR(text) {
    const patterns = [
      /(?:hazard ratio|HR)[,:\s]*(\d+\.\d+)\s*[;,(\s]*95%?\s*CI[,:\s]*(\d+\.\d+)\s*(?:to|[-–])\s*(\d+\.\d+)/gi,
      /HR\s*[=:]\s*(\d+\.\d+)\s*\((\d+\.\d+)\s*[-–]\s*(\d+\.\d+)\)/gi
    ];
    const results = [];
    for (const pat of patterns) {
      let m; pat.lastIndex = 0;
      while ((m = pat.exec(text)) !== null) {
        results.push({ effect: parseFloat(m[1]), lci: parseFloat(m[2]), uci: parseFloat(m[3]), type: 'HR' });
      }
    }
    return results;
  },

  // Odds ratio / Risk ratio
  extractORRR(text) {
    const pat = /(?:odds ratio|OR|risk ratio|RR|relative risk)[,:\s]*(\d+\.\d+)\s*[;,(\s]*95%?\s*CI[,:\s]*(\d+\.\d+)\s*(?:to|[-–])\s*(\d+\.\d+)/gi;
    // similar to HR extraction...
  },

  // Event counts: "187 patients (6.8%) in the colchicine group"
  extractEvents(text) {
    const pat = /(\d[\d,]*)\s*(?:of\s*)?(\d[\d,]*)\s*patients?\s*\((\d+\.?\d*)%\)/gi;
    // Also: "occurred in 187 (6.8%) vs 264 (9.6%)"
  },

  // Sample sizes: "5,522 patients were randomized"
  extractSampleSize(text) {
    const pat = /(\d[\d,]+)\s*patients?\s*(?:were\s*)?(?:randomized|enrolled|recruited)/gi;
  },

  // P-values
  extractPvalue(text) {
    const pat = /[Pp]\s*([=<>])\s*(\d+\.?\d*)/g;
  },

  // Arm sizes: "2,762 to colchicine... and 2,760 to placebo"
  extractArmSizes(text) {
    const pat = /(\d[\d,]+)\s*(?:to|assigned to|received)\s*(colchicine|placebo|usual care|control)/gi;
  },

  // Run all extractors on an abstract
  parseAbstract(text) {
    return {
      hrs: this.extractHR(text),
      ors: this.extractORRR(text),
      events: this.extractEvents(text),
      sampleSize: this.extractSampleSize(text),
      armSizes: this.extractArmSizes(text),
      pvalues: this.extractPvalue(text)
    };
  }
};
```

- [ ] **Step 2: CT.gov results parser**

For trials with posted results on CT.gov:
```javascript
async function extractCTgovOutcomes(nctId) {
  // Fetch ResultsSection
  // Parse OutcomeMeasures → event counts per arm
  // Parse StatisticalAnalyses → effect estimates
  // Return structured outcome data
}
```

- [ ] **Step 3: Cross-validation matrix**

```javascript
function crossValidate(trial) {
  const sources = { ctgov: null, pubmed: null, openalex: null, baseline: null };
  // Compare extracted values across sources
  // Assign confidence: HIGH (3 agree), MODERATE (2 agree), LOW (1 only), LOCKED (baseline)
  // Flag discrepancies for manual review
}
```

- [ ] **Step 4: Render extraction table in Extract tab**

Per-trial rows with: source badges, extracted values, confidence scores, manual override fields.

---

## Chunk 4: Statistical Core (port from TruthCert-PairwisePro)

### Task 7: Distribution functions

- [ ] **Step 1: Port all distribution functions from metajs-lib/meta-analysis.js**

Port lines 160-382:
- `erf(x)` — error function
- `normalCDF(x)`, `normalQuantile(p)` — Φ and Φ⁻¹
- `incompleteBeta(x, a, b)` — via Lentz continued fractions
- `tCDF(t, df)`, `tQuantile(p, df)` — Student's t
- `chiSquareCDF(x, df)`, `chiSquareQuantile(p, df)` — χ² (Wilson-Hilferty + Newton-Raphson)
- Frozen critical values: Z_95 = 1.959963984540054

- [ ] **Step 2: Port effect size calculators from app_beautified.js**

Port lines 923-1059:
- `calculateLogOR(tE, tN_minus_tE, cE, cN_minus_cE, cc)` — log odds ratio + variance
- `calculateLogRR(...)` — log risk ratio + variance
- `calculateRD(...)` — risk difference + variance
- `getContinuityCorrection(trial, method)` — constant/treatment/empirical/none
- HR variance from CI: `se_logHR = (ln(uci) - ln(lci)) / 3.92`

### Task 8: Tau-squared estimators

- [ ] **Step 1: Port all 9 tau² estimators from metajs-lib lines 670-933**

```javascript
const Tau2Estimators = {
  DL(yi, vi) { /* DerSimonian-Laird: tau2 = max(0, (Q-df)/C) */ },
  REML(yi, vi) { /* Fisher scoring + Newton-Raphson, tol=1e-10, max 100 iter */ },
  ML(yi, vi) { /* Maximum Likelihood, Newton-Raphson */ },
  PM(yi, vi) { /* Paule-Mandel: bisection to solve Q(tau2) = k-1 */ },
  HS(yi, vi) { /* Hunter-Schmidt: tau2 = max(0, (Q-df)/sumW) */ },
  SJ(yi, vi) { /* Sidik-Jonkman: two-step with unweighted init */ },
  HE(yi, vi) { /* Hedges: unweighted Q, tau2 = Q/(k-1) - mean(vi) */ },
  EB(yi, vi) { /* Empirical Bayes (Morris): iterative shrinkage */ },
  GENQ(yi, vi) { /* Generalized Q estimator */ }
};
```

- [ ] **Step 2: Port heterogeneity statistics from lines 940-1120**

- Q, I², H², H with CIs
- Q-profile confidence intervals for tau² and I²
- Profile likelihood CI (REML/ML)

- [ ] **Step 3: Port pooled estimate calculation from lines 1163-1225**

- Inverse-variance weighting with tau²
- HKSJ adjustment (raw Q_re/(k-1) multiplier, t-distribution CIs)
- Prediction intervals (t-distribution, df=k-2)

### Task 9: Fixed-effect methods

- [ ] **Step 1: Mantel-Haenszel OR and RR**

Port from COLCHICINE_CVD_REVIEW.html lines 7226-7249:
```javascript
function mantelHaenszelOR(trials) {
  // MH_OR = Σ(a*d/T) / Σ(b*c/T)
  // Robins-Breslow-Greenland variance
}
function mantelHaenszelRR(trials) {
  // MH_RR = Σ(a*(c+d)/T) / Σ(c*(a+b)/T)
}
```

- [ ] **Step 2: Peto OR**

```javascript
function petoOR(trials) {
  // Peto's one-step: exp(Σ(O-E)/Σ(V))
  // O = observed events treatment, E = expected under null
  // V = hypergeometric variance
}
```

- [ ] **Step 3: Inverse-variance fixed-effect**

Standard IV with tau²=0.

### Task 10: Bayesian MCMC engine

- [ ] **Step 1: Port Bayesian engine from app_beautified.js lines 1512-1722**

Key components:
- `seedRandom(seed)` — LCG for deterministic sampling
- `rnorm(mu, sigma, rng)` — Box-Muller
- `sliceSampleTau2(yi, vi, mu, tau2, prior, scale, rng)` — slice sampling
- `bayesianMetaAnalysis(yi, vi, options)` — full MCMC with multiple chains
- `computeBayesianSummary(combined, yi, vi)` — posterior means, CrIs, P(benefit)
- `computeMCMCDiagnostics(chains)` — Rhat, ESS

Priors: half-Cauchy (default), inverse-Gamma, flat. Configurable scale.

---

## Chunk 5: Bias Assessment Suite

### Task 11: Publication bias tests

- [ ] **Step 1: Port all bias tests from metajs-lib lines 1231-1485**

```javascript
const BiasSuite = {
  egger(yi, vi) { /* WLS regression: yi ~ sei, intercept test */ },
  peters(yi, vi, ni) { /* WLS regression: yi ~ 1/ni */ },
  begg(yi, vi) { /* Kendall's tau rank correlation */ },
  trimFill(yi, vi, side) { /* L0 estimator, iterative trim-and-refit */ },
  petPeese(yi, vi) { /* PET: yi ~ sei; PEESE: yi ~ vi; conditional */ },
  failsafeN(yi, vi) { /* Rosenthal's, Orwin's, Rosenberg's */ }
};
```

- [ ] **Step 2: Copas selection model**

Port from COLCHICINE_CVD_REVIEW.html (rank-reweighting heuristic) or TruthCert (full grid search):
```javascript
function copasModel(yi, vi, rhoGrid) {
  // For each rho in [-0.99, 0], compute selection-weighted pooled estimate
  // Return sensitivity contour: rho → adjusted estimate
}
```

- [ ] **Step 3: Additional bias indicators**

- P-curve analysis (evidential value)
- Test of Excess Significance (TES)
- Contour-enhanced funnel plot data

### Task 12: Sensitivity analysis suite

- [ ] **Step 1: Port leave-one-out from metajs-lib lines 1488-1512**

- [ ] **Step 2: Port cumulative MA**

By year (chronological evidence accrual) or by precision (largest first).

- [ ] **Step 3: Port influence diagnostics from lines 1517-1551**

Cook's distance, DFBETAS, leverage (hat values), studentized residuals.

- [ ] **Step 4: Meta-regression**

Port from COLCHICINE_CVD_REVIEW.html lines 6650-6770:
- WLS regression with moderator covariates (year, phase, indication, follow-up duration)
- Bubble plot rendering

---

## Chunk 6: Dual-Track Synthesis + GRADE

### Task 13: Dual-track synthesis orchestrator

- [ ] **Step 1: Implement Track A (HR pool)**

```javascript
function synthesizeTrackA(trials) {
  // Filter trials with published HRs
  const hrTrials = trials.filter(t => t.publishedHR != null);
  const yi = hrTrials.map(t => Math.log(t.publishedHR));
  const vi = hrTrials.map(t => {
    const se = (Math.log(t.hrUCI) - Math.log(t.hrLCI)) / 3.92;
    return se * se;
  });

  // Run ALL tau² estimators
  const tau2Results = {};
  for (const [method, fn] of Object.entries(Tau2Estimators)) {
    tau2Results[method] = fn(yi, vi);
  }

  // Primary: REML + HKSJ
  const primary = PooledEstimate.calculate(yi, vi, tau2Results.REML.tau2, true);
  const pi = PooledEstimate.predictionInterval(primary.estimate, primary.se, tau2Results.REML.tau2, yi.length);

  // Fixed-effect IV
  const fixed = PooledEstimate.calculate(yi, vi, 0, false);

  // Bayesian
  const bayesian = bayesianMetaAnalysis(yi, vi, { seed: 42, prior_sd: 0.5 });

  // Bias suite
  const bias = runFullBiasSuite(yi, vi);

  // Sensitivity
  const loo = leaveOneOut(yi, vi, 'REML');
  const cumulative = cumulativeMA(yi, vi, hrTrials.map(t => t.year));
  const influence = influenceDiagnostics(yi, vi, tau2Results.REML.tau2);

  return {
    track: 'A', label: 'Published HR Pool',
    k: yi.length, measure: 'HR',
    primary, fixed, tau2Results, pi, bayesian,
    bias, loo, cumulative, influence,
    trials: hrTrials
  };
}
```

- [ ] **Step 2: Implement Track B (OR from counts)**

```javascript
function synthesizeTrackB(trials) {
  // All trials with event counts
  const orTrials = trials.filter(t => t.tE != null && t.cE != null);
  // Calculate log(OR) and variance for each
  const effects = orTrials.map(t => {
    const cc = getContinuityCorrection(t, AppState.settings.continuityCorrection);
    return calculateLogOR(t.tE, t.tN - t.tE, t.cE, t.cN - t.cE, cc);
  });
  const yi = effects.map(e => e.yi);
  const vi = effects.map(e => e.vi);

  // Same full analysis as Track A...
  // PLUS: MH-OR, Peto OR (fixed-effect alternatives)
  const mhOR = mantelHaenszelOR(orTrials);
  const petoOR = petoORCalc(orTrials);

  return {
    track: 'B', label: 'OR from Event Counts',
    k: yi.length, measure: 'OR',
    primary, fixed, mhOR, petoOR, tau2Results, pi, bayesian,
    bias, loo, cumulative, influence,
    trials: orTrials
  };
}
```

- [ ] **Step 3: Per-outcome synthesis**

Loop over all 5 outcomes (MACE, CVD, ACM, MI, Stroke), run dual-track for each:
```javascript
function synthesizeAllOutcomes(trials) {
  const outcomes = CONFIG_LIBRARY[AppState.config].outcomes;
  const results = {};
  for (const outcome of outcomes) {
    const subset = selectOutcomeData(trials, outcome.key);
    results[outcome.key] = {
      trackA: synthesizeTrackA(subset),
      trackB: synthesizeTrackB(subset)
    };
  }
  return results;
}
```

### Task 14: GRADE automation

- [ ] **Step 1: Port GRADE logic from TruthCert app_beautified.js lines 10154-10230**

```javascript
function assessGRADE(synthesis, robData) {
  const domains = {
    riskOfBias: assessRoB(robData),
    inconsistency: assessInconsistency(synthesis),
    indirectness: assessIndirectness(synthesis),
    imprecision: assessImprecision(synthesis),
    publicationBias: assessPubBias(synthesis.bias)
  };

  const totalDowngrade = Object.values(domains).reduce((s, d) => s + d.downgrade, 0);
  const certainty = totalDowngrade === 0 ? 'HIGH' :
                    totalDowngrade <= 1 ? 'MODERATE' :
                    totalDowngrade <= 2 ? 'LOW' : 'VERY LOW';

  return { domains, certainty, totalDowngrade };
}
```

- [ ] **Step 2: Summary of Findings (SoF) table**

Per outcome: k, N, effect estimate, 95% CI, I², GRADE certainty, NNT.

### Task 15: Verdict system

- [ ] **Step 1: Port 12-point threat assessment from TruthCert**

Port from app_beautified.js lines 3310-3375 (scoreVerdictFactors).

- [ ] **Step 2: Narrative generation**

Automated plain-language summary per outcome, per track.

---

## Chunk 7: Visualization

### Task 16: Forest plots (dual-track)

- [ ] **Step 1: Dual forest plot renderer**

Side-by-side or stacked: Track A (HR) forest | Track B (OR) forest.
Port from TruthCert app_beautified.js lines 7958-8160 and COLCHICINE lines 7909-8110.

Features: study markers scaled by weight, pooled diamond, prediction interval bar, subgroup separators, right-side annotations (effect [CI], weight%).

- [ ] **Step 2: Funnel plot with contour enhancement**

SE vs effect, significance contours at p<0.01/0.05/0.10, trim-fill imputed studies overlay.

### Task 17: Additional plots

- [ ] **Step 1: Galbraith (radial) plot**
- [ ] **Step 2: Baujat plot** (Q contribution vs influence)
- [ ] **Step 3: L'Abbé plot** (CER vs TER)
- [ ] **Step 4: Cumulative MA plot** (sequential forest by year)
- [ ] **Step 5: Leave-one-out influence plot**
- [ ] **Step 6: Meta-regression bubble plot**
- [ ] **Step 7: PRISMA flow diagram** (from discovery counts)

### Task 18: Comparison dashboard

- [ ] **Step 1: Method comparison table**

All 9 tau² estimates side-by-side: method, tau², I², pooled effect, CI, PI, p-value.
Highlight when estimates disagree substantially.

- [ ] **Step 2: Published meta-analysis comparison panel**

Hardcoded benchmark data from the 25 published metas (from our earlier research).
Show our estimates alongside Cochrane 2025, d'Entremont 2025, Tucker 2025, Fiolet 2021, etc.

---

## Chunk 8: TruthCert + Export

### Task 19: TruthCert certification

- [ ] **Step 1: SHA-256 hashing**

```javascript
async function sha256(text) {
  const encoder = new TextEncoder();
  const data = encoder.encode(text);
  const hashBuffer = await crypto.subtle.digest('SHA-256', data);
  return Array.from(new Uint8Array(hashBuffer)).map(b => b.toString(16).padStart(2, '0')).join('');
}
```

- [ ] **Step 2: Build CertBundle**

```javascript
async function buildCertBundle() {
  const bundle = {
    version: '1.0',
    timestamp: new Date().toISOString(),
    config: AppState.config,
    searchQueries: CONFIG_LIBRARY[AppState.config].searchQueries,
    discoveredTrials: AppState.discovered.length,
    screenedTrials: AppState.screened.length,
    includedTrials: AppState.merged.length,
    baselineTrials: AppState.baseline.length,
    extractionSources: summarizeSources(),
    crossValidation: summarizeCrossValidation(),
    synthesisResults: AppState.results,
    gradeAssessments: AppState.results?.grade,
    verdict: AppState.results?.verdict,
    hashes: {
      inputData: await sha256(JSON.stringify(AppState.merged)),
      searchLog: await sha256(JSON.stringify(AppState.searchLog)),
      results: await sha256(JSON.stringify(AppState.results))
    },
    auditLog: AppState.auditLog,
    provenance: {
      engine: 'LivingMeta v1.0',
      methods: 'Dual-track (HR+OR), 9 tau² estimators, HKSJ, Bayesian MCMC, 12+ bias tests',
      baselineVerification: '3 rounds blinded verification, 12 fixes applied',
      apis: ['ClinicalTrials.gov v2', 'Europe PMC REST', 'OpenAlex REST']
    }
  };
  bundle.hashes.bundle = await sha256(JSON.stringify(bundle));
  return bundle;
}
```

- [ ] **Step 3: Certify tab UI**

Display: bundle summary, hash verification, provenance chain, export buttons.

### Task 20: Export mechanisms

- [ ] **Step 1: JSON bundle export**

Full CertBundle as downloadable JSON.

- [ ] **Step 2: CSV data export**

Trial-level data table: study, tE, tN, cE, cN, HR, CI, source, confidence.

- [ ] **Step 3: PDF report generation** (jsPDF)

Forest plots + SoF table + GRADE + verdict + provenance.

- [ ] **Step 4: R/Python validation scripts**

Auto-generate R script using metafor that reproduces the analysis.

### Task 21: Living update mechanism

- [ ] **Step 1: Re-search button**

"Update Evidence" button that re-runs all 3 API searches, diffs against existing data, highlights new trials.

- [ ] **Step 2: Version snapshots**

Before each update, snapshot current state. Allow rollback.

- [ ] **Step 3: Audit log**

Every action timestamped: search, screen decision, extraction, synthesis run, certification.

---

## Testing Strategy

### Browser Testing (Selenium)
- All 8 tabs render and switch
- Search APIs return results (live test with CT.gov)
- Baseline 5 trials load and display correctly
- Dual-track synthesis produces results for all 5 outcomes
- Forest plots render with correct number of studies
- GRADE badges appear for each outcome
- TruthCert hash is non-empty and deterministic
- Export JSON contains all required fields
- Div balance check: `<div[\s>]` count equals `</div>` count

### Statistical Validation
- Track A HR pool: compare REML/HKSJ estimate for MACE against hand-calculated ~OR 0.82
- Track B OR pool: compare MH-OR against published meta-analysis benchmarks
- Leave-one-out: removing CLEAR SYNERGY should shift MACE toward stronger benefit
- Prediction interval: should be wider than CI
- Bayesian: posterior mean should be between fixed and random estimates
- All 9 tau² estimators: compare against R metafor with tolerance 1e-4

### Cross-Validation
- Baseline COLCOT data matches COLCHICINE_CVD_REVIEW.html exactly
- CT.gov search for NCT02551094 returns COLCOT
- PubMed search returns PMID 31733140 (COLCOT)
- Percentages: 131/2366 = 5.5%, 170/2379 = 7.1% (verify in app)

---

## Published Meta-Analysis Benchmark Data (hardcoded for comparison)

```javascript
const PUBLISHED_BENCHMARKS = {
  'Fiolet 2021 (EHJ)': { k: 5, n: 11816, mace: { rr: 0.75, lci: 0.61, uci: 0.92 }, mi: { rr: 0.78, lci: 0.64, uci: 0.94 }, stroke: { rr: 0.54, lci: 0.34, uci: 0.86 } },
  'dEntremont 2025 (EHJ)': { k: 9, n: 30659, mace: { rr: 0.88, lci: 0.81, uci: 0.95 }, mi: { rr: 0.84, lci: 0.73, uci: 0.97 }, stroke: { rr: 0.90, lci: 0.80, uci: 1.02 } },
  'Tucker 2025 (EJPC)': { k: 11, n: 30808, mace: { rr: 0.83, lci: 0.73, uci: 0.95 }, mi: { rr: 0.78, lci: 0.63, uci: 0.95 }, stroke: { rr: 0.81, lci: 0.63, uci: 1.04 } },
  'Cochrane 2025': { k: 12, n: 22983, mi: { rr: 0.74, lci: 0.57, uci: 0.96 }, stroke: { rr: 0.67, lci: 0.47, uci: 0.95 }, acm: { rr: 1.01, lci: 0.84, uci: 1.21 } },
  'Laudani 2026': { k: 20, n: 21486, mace: { irr: 0.70, lci: 0.55, uci: 0.87 }, mi: { irr: 0.81, lci: 0.70, uci: 0.94 } }
};
```

---

## Execution Order

1. **Chunk 1** (Tasks 1-2): Foundation → verify app loads with baseline data
2. **Chunk 2** (Tasks 3-5): Discovery → verify API searches return results
3. **Chunk 3** (Task 6): Extraction → verify abstract parsing on known abstracts
4. **Chunk 4** (Tasks 7-10): Statistical core → verify against R metafor
5. **Chunk 5** (Tasks 11-12): Bias suite → verify Egger's on baseline data
6. **Chunk 6** (Tasks 13-15): Synthesis + GRADE → verify dual-track outputs
7. **Chunk 7** (Tasks 16-18): Visualization → verify all plots render
8. **Chunk 8** (Tasks 19-21): TruthCert + export → verify certification bundle

Each chunk produces a working, testable intermediate state.
