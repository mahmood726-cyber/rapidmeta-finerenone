# PRISMA row population audit

Scope: enumerate only. No generator files were modified.

## Method

I parsed Python generator source with `ast`, walking `ast.Constant` and `ast.JoinedStr`
nodes containing PRISMA/reporting markers. The AST pass covered 1,025 `*.py` files
after excluding cache/output directories. Row extraction was from generator source
strings/f-strings, not from rendered pages.

Row-emitting PRISMA sources found:

| Generator | Source node | Block | Row templates |
|---|---:|---|---:|
| `generate_living_ma_v13.py` | line 479 string constant | PRISMA-NMA checklist items | 4 |
| `scripts/generate_topic_html.py` | line 308 f-string | PRISMA-style screening | 4 |
| `scripts/generate_topic_html.py` | line 514 f-string | PRISMA 2020 status | 4 |

Also found but not counted as row/value reporting rows:

| Generator/source | Why not in row population |
|---|---|
| `scripts/inject_prisma_flow.py` | Emits a PRISMA-NMA flow panel/container and script tag, not label/value rows. |
| `ssot/projectors2.py`, `ssot/projectors.py`, `scripts/add_rob_prisma.py`, `scripts/wire_new_figs.py` | Emit PRISMA SVG figures or helper functions, not checklist/status row blocks. |
| `ssot/paper_projector.py`, `ssot/make_docx.py`, `ssot/add_f1000_fields.py` | Emit manuscript/docx/metadata prose, not delivered HTML row/value blocks. |

## Counts

Total row templates emitted by row/block generators: **12**.

| Generator | Block type | Rows | Constants | Derived |
|---|---|---:|---:|---:|
| `generate_living_ma_v13.py` | PRISMA-NMA checklist | 4 | 4 | 0 |
| `scripts/generate_topic_html.py` | PRISMA-style screening | 4 | 0 | 4 |
| `scripts/generate_topic_html.py` | PRISMA 2020 status | 4 | 2 | 2 |
| **Total** |  | **12** | **6** | **6** |

The screening block's fourth row is a dynamic row template for each first failing
gate. The no-exclusions fallback row has no label/value pair and is not counted
as a reporting row.

## Row Inventory

### `generate_living_ma_v13.py` - PRISMA-NMA checklist

All four values are literal source strings in `nma_output_html`.

| Label / item | Value expression as source text | Class | Derived from |
|---|---|---|---|
| Network geometry | `<span id="nma-geometry-text">Star topology &mdash; all treatments connected via common comparator</span>` | CONSTANT | n/a |
| Transitivity assumption | `Similar patient populations across trials (all obesity/overweight adults)` | CONSTANT | n/a |
| Consistency | `<div id="nma-consistency-summary">... <strong>Consistency:</strong> Run NMA to assess</div>` | CONSTANT | n/a |
| Ranking | `P-scores with uncertainty (SUCRA interpretation caveat displayed)` | CONSTANT | n/a |

### `scripts/generate_topic_html.py` - PRISMA-style screening

| Label / item | Value expression as source text | Class | Derived from |
|---|---|---|---|
| Records identified (AACT x PubMed) | `{n_total}` | DERIVED | `n_total = len(topic_audit["trials"])` |
| Records excluded (gate failure) | `{n_excl}` | DERIVED | `n_excl = n_total - n_pass` |
| Records included (all 6 gates pass) | `{n_pass}` | DERIVED | `n_pass = sum(1 for t in topic_audit["trials"] if all(t["gates"].values()))` |
| Exclusions by first failing gate | label `{esc(g)}`, value `{n}` inside `excl_table` | DERIVED | `by_gate_failure`, built from first failed gate per trial |

### `scripts/generate_topic_html.py` - PRISMA 2020 status

| Label / item | Value expression as source text | Class | Derived from |
|---|---|---|---|
| Identification | `AACT x PubMed intersection (deterministic)` | CONSTANT | n/a |
| Screening | `6-gate audit (machine-checkable)` | CONSTANT | n/a |
| Eligibility | `k={len(trials)} trials passed all 6 gates` | DERIVED | `len(trials)` |
| Included | `k={pool["k"] if pool else 0} with extractable event counts` | DERIVED | `pool["k"] if pool else 0` |

## Constant Rows: Assertions and Risk

| Constant row | What it asserts | Classification | False condition / false examples |
|---|---|---|---|
| Network geometry | This review's network is a star and all treatments connect through a common comparator. | ASSERTS A FACT | False when the page's actual NMA graph is not a star, has closed loops, has multiple hubs, or lacks one common comparator. From delivered `NMA_CONFIG`, examples include `ADC_HER2_NMA_REVIEW.html` (T=5, D=4, non-star tree), `ANTIAMYLOID_AD_NMA_REVIEW.html` (T=6, D=7, loops), `ANTIVEGF_NAMD_NMA_REVIEW.html` (T=8, D=11, loops), `BTKI_CLL_NMA_REVIEW.html` (T=8, D=7, non-star tree), `IL_PSORIASIS_NMA_REVIEW.html` (T=11, D=14, loops), and `INCRETINS_T2D_NMA_REVIEW.html` (T=11, D=15, loops). |
| Transitivity assumption | Trial populations are similar and are all obesity/overweight adults. | ASSERTS A FACT | False when the page is not an obesity/overweight-adult review, or when effect modifiers/populations are not clinically exchangeable. False examples include `ANTIAMYLOID_AD_NMA_REVIEW.html` (Alzheimer disease), `BTKI_CLL_NMA_REVIEW.html` (chronic lymphocytic leukaemia), `CFTR_MODULATORS_NMA_REVIEW.html` (cystic fibrosis), and `ADC_HER2_NMA_REVIEW.html` (HER2 breast cancer). |
| Consistency | User should run NMA before consistency is assessed. | HARMLESS BOILERPLATE | Procedural/deferred UI text; it does not claim a page-specific result. |
| Ranking | Ranking is reported as P-scores and the SUCRA caveat is displayed. | HARMLESS BOILERPLATE | Procedural/method statement for the NMA surface; no false page-specific value identified from this row alone. |
| Identification | The audit-first page used a deterministic AACT x PubMed intersection. | HARMLESS BOILERPLATE | True for pages produced by `scripts/generate_topic_html.py`; would be false only if this generator were reused for a non-AACT/PubMed source without changing the row. |
| Screening | The audit-first page used a machine-checkable six-gate audit. | HARMLESS BOILERPLATE | True for pages produced by `scripts/generate_topic_html.py`; would be false only if this generator were reused without the six-gate audit. |

## Delivered Page Counts

Delivered-page census used the repo-root glob **`*.html`**. It found **1,510**
HTML files at repo root.

| Block / marker counted | Glob | Marker | Pages |
|---|---|---|---:|
| PRISMA-NMA checklist block | `*.html` | `id="nma-prisma-nma"` / `PRISMA-NMA Checklist Items` | **18** |
| PRISMA-NMA transitivity constant | `*.html` | `all obesity/overweight adults` | **18** |
| PRISMA-style screening block | `*.html` | `PRISMA-style screening` | **21** |
| PRISMA 2020 status block | `*.html` | `PRISMA 2020 status` | **21** |
| PRISMA-NMA flow diagram panel | `*.html` | `prismaFlowContainer` / `PRISMA-NMA Flow Diagram` | **750** |
| Circulating 42-page string count | `*.html` | `Star topology` | **42** |

The circulating **42** is a real string-hit count for `Star topology`, but it is
not the count of pages carrying the full PRISMA-NMA checklist block. The actual
checklist block count is **18**. The extra 24 hits are from other generated NMA
runtime/manuscript code surfaces that contain the same phrase but not the
four-row checklist headed `PRISMA-NMA Checklist Items`.

The 18 checklist pages are:

`ADC_HER2_NMA_REVIEW.html`, `ANTIAMYLOID_AD_NMA_REVIEW.html`,
`ANTIVEGF_NAMD_NMA_REVIEW.html`, `ATOPIC_DERM_NMA_REVIEW.html`,
`BTKI_CLL_NMA_REVIEW.html`, `CARDIORENAL_DKD_NMA_REVIEW.html`,
`CD_BIOLOGICS_NMA_REVIEW.html`, `CFTR_MODULATORS_NMA_REVIEW.html`,
`CGRP_MIGRAINE_NMA_REVIEW.html`, `DOAC_VTE_NMA_REVIEW.html`,
`GLP1_CVOT_NMA_REVIEW.html`, `HF_QUADRUPLE_NMA_REVIEW.html`,
`IL_PSORIASIS_NMA_REVIEW.html`, `INCRETINS_T2D_NMA_REVIEW.html`,
`JAKI_RA_NMA_REVIEW.html`, `SEVERE_ASTHMA_NMA_REVIEW.html`,
`SGLT2I_HF_NMA_REVIEW.html`, and `UC_BIOLOGICS_NMA_REVIEW.html`.
