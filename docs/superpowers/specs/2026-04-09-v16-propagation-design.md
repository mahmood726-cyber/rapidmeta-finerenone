# v16 Feature Propagation Design

> Extend `propagate_features.py` to propagate 5 additional v16 engine blocks from `FINERENONE_REVIEW.html` to all 13 sibling apps.

## Context

FINERENONE_REVIEW.html is the v16 reference implementation with 31 integrated engines. The 13 sibling apps (`*_REVIEW.html` + `LivingMeta.html`) are at v12.0-v12.5 and are missing key v16 features. All siblings are **pairwise** meta-analyses — NMA and dose-response are excluded.

The existing `propagate_features.py` handles 3 features (TextExtractor, GradeProfileEngine, Manuscript). This design adds 5 new phases using the same proven pattern: extract from source -> find anchor -> duplicate-check -> insert -> validate.

## Target Apps (13)

ABLATION_AF, ARNI_HF, ATTR_CM, BEMPEDOIC_ACID, COLCHICINE_CVD, DOAC_CANCER_VTE, GLP1_CVOT, INCRETIN_HFpEF, INTENSIVE_BP, IV_IRON_HF, LIPID_HUB, MAVACAMTEN_HCM, PCSK9, RENAL_DENERV, RIVAROXABAN_VASC, SGLT2_CKD, SGLT2_HF, LivingMeta.html

Note: Some of these may not exist as files yet. The script skips missing files.

## Phases

### Phase 4: CumulativeEngine (~97 lines, FINERENONE lines 8888-8984)

**What it does:** Cumulative meta-analysis — pools studies in chronological order, showing how the pooled estimate evolves as each trial is added. Uses DL pooling with t-distribution CIs.

**Extraction marker:** `const CumulativeEngine = {`
**Insertion anchor:** Before ManuscriptEngine or after NMA section comment.
**Fallback anchor:** Before `/* === Auto-Generated Manuscript Text === */` or before `function downloadPDFReport()`.
**HTML container:** `cumulative-container` div with `cumulative-plot` for Plotly chart. Insert in the report output section.
**Dependencies:** Plotly (already loaded in all apps), AnalysisEngine (already present).

### Phase 5: ProvenanceChainEngine + DataSealEngine (~85 lines combined)

**ProvenanceChainEngine** (FINERENONE lines 9045-9100, ~56 lines):
- SHA-256 hash chain for data provenance tracking.
- No UI containers — state-only engine.
- Extraction marker: `const ProvenanceChainEngine = {`
- Insertion anchor: After ManuscriptEngine or CumulativeEngine.

**DataSealEngine** (FINERENONE lines 9969-9997, ~29 lines):
- SHA-256 integrity seal on analysis state.
- HTML containers: `data-seal-hash`, `data-seal-time` (small display elements).
- Extraction marker: `const DataSealEngine = {`
- Insertion anchor: After PowerEngine (if present) or after CopasEngine.
- Note: Already exists in some v12 apps (SGLT2_HF, ARNI_HF) — duplicate detection will skip these.

### Phase 6: QAEngine (~125 lines, FINERENONE lines 9105-9229)

**What it does:** 18 automated quality assurance checks (QA1-QA18) covering analysis execution, data completeness, HKSJ concordance, heterogeneity, Egger test, prediction interval, fragility index, Bayesian posterior, trim-and-fill, data seal, GRADE, protocol lock, version snapshots, cross-validation, evidence extraction, provenance chain, Copas sensitivity.

**Extraction marker:** `const QAEngine = {`
**Insertion anchor:** After ProvenanceChainEngine or after DataSealEngine.
**HTML container:** `qa-container` div with grid layout for 18 check badges.
**Dependencies:** ProvenanceChainEngine, DataSealEngine (must be propagated first — Phase 5).
**Graceful degradation:** QA checks that reference missing engines (e.g., CrossValidation, NMA) should produce "N/A" or "skipped" status, not errors. The v16 QAEngine already handles this with `typeof X !== 'undefined'` guards.

### Phase 7: CrossValidationEngine (~166 lines, FINERENONE lines 8338-8503)

**What it does:** 3-source concordance — compares extracted values from ClinicalTrials.gov API, PubMed abstracts, and manual extraction. Renders summary badges on trial cards and a collapsible comparison table.

**Extraction marker:** `const CrossValidationEngine = {`
**Insertion anchor:** Before CumulativeEngine or before NMA section.
**HTML containers:**
- `xval-panel` — main collapsible panel
- `xval-header` — expandable header
- `xval-body` — content body
- `xval-table` — comparison table
**Dependencies:** AutoExtractEngine (already present in all apps), CT.gov API access (runtime, not build-time).

### Phase 8: BenchmarkEngine (~59 lines, FINERENONE lines 12735-12793)

**What it does:** Compares app's pooled effect against published meta-analyses from `PUBLISHED_META_BENCHMARKS.json`. Reports CI overlap, alignment classification (Strong/Matched/Directional/Tension), and log-distance ranking.

**Extraction marker:** `const BenchmarkEngine = {`
**Insertion anchor:** After CTGovDeltaEngine (if present) or after ReviewConcordanceEngine or before ArtifactEngine.
**HTML containers:** None — data-only engine, rendered via ReportEngine.
**Dependencies:** PUBLISHED_META_BENCHMARKS.json (already in repo root).

## Excluded from propagation

| Engine | Reason |
|--------|--------|
| NMAEngine | All siblings are pairwise — no network comparisons needed |
| DoseResponseEngine | Requires multi-dose trials — not applicable to pairwise |
| CTGovDeltaEngine | 399 lines, FINERENONE-specific (history pack JSON, ghost results monitoring). Too coupled to living registry workflow. |
| CapsuleEngine | Already in some v12 apps. The v12 version is sufficient for pairwise. |

## Safety guarantees

1. **Backup:** Each app gets `.pre_v16.bak.html` before any modification.
2. **Duplicate detection:** Skip insertion if engine's `const` marker already exists in file.
3. **Trial data preservation:** Only engine JS blocks and UI containers are touched. `realData` objects and localStorage keys are never modified.
4. **Div balance validation:** Count `<div[\s>]` vs `</div>` after all phases. Tolerance: +/- 2 (for JS regex escapes).
5. **Script tag integrity:** No literal `</script>` in template literals.
6. **Benchmark validation:** After propagation, run `cross_validate.py` to verify pooled effects still match published MAs from `PUBLISHED_META_BENCHMARKS.json`.
7. **Dynamic drug names:** Replace any hardcoded "Finerenone" in extracted blocks with `RapidMeta.state.protocol?.int ?? 'The intervention'`.

## Propagation pattern (per phase)

```python
# 1. Extract block from source
block = extract_engine_block(source_lines, 'const XxxEngine = {')

# 2. For each target app:
for fname in ALL_TARGETS:
    content = read_file(fname)
    if 'const XxxEngine' in content:
        print(f"  SKIP: already present")
        continue
    
    # 3. Find insertion anchor
    anchor = find_anchor(lines, ANCHOR_MARKERS)
    
    # 4. Insert block
    lines.insert(anchor, block)
    
    # 5. Insert HTML container (if needed)
    html_anchor = find_html_anchor(lines, HTML_MARKERS)
    lines.insert(html_anchor, container_html)
    
    # 6. Validate
    check_div_balance(lines)
```

## Validation after propagation

1. Run `python propagate_features.py` — all phases complete without errors
2. Run `python cross_validate.py` — all benchmarks still match
3. Run `python test_all_apps_comprehensive.py` — no regressions
4. Spot-check 2-3 apps in browser — new tabs/panels render, no console errors
