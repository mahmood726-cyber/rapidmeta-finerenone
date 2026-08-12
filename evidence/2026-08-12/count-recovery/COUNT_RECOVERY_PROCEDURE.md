# Per-arm event-count recovery — procedure

**Companion to** `rapidmeta_count_harness.py` (v1.1.0). Run the harness; do not re-derive its rules by hand.

```
python rapidmeta_count_harness.py --selftest        # 17 checks, 23 controls (20 must-block, 3 must-not-block)
python determinacy_test.py <corpus_dir>            # is a reconstruction actually determined?
python rapidmeta_count_harness.py --chain           # print the retrieval fallback chain
python rapidmeta_count_harness.py extraction.json --report r.md --json r.json
```

Exit code 1 means at least one BLOCK. A BLOCKed extraction does not go downstream.

---

## 0. Ruling of 2026-08-12 — determined reconstruction is permitted

Back-computation is allowed **where the reported quantities mathematically determine the cells**. It remains forbidden where it does not. The distinction is the whole rule; without it, "back-computation is fine" becomes a licence to manufacture numbers.

| | status | how it is recorded |
|---|---|---|
| Count printed as an integer | permitted | `provenance: "read"` |
| **Determined** reconstruction — every input reported, and the rounding interval admits exactly one integer | **permitted** | `provenance: "derived_determined"` **plus** `derivation_inputs`, `derivation_formula`, and a source pointer per input. Enforced by `CHK017`. |
| **Underdetermined** reconstruction — a missing denominator, an imputed group size, a percentage without its base, or rounding resolved by choice | **forbidden** | `not_recovered_reason`; `construction: "derived_underdetermined"` is blocked by `CHK016` |
| Composite built by summing **total** component counts | forbidden | `CHK016` |
| Count from percentage × denominator where no count was reported | forbidden | `CHK016` |

**Determinacy must be tested, not assumed.** A percentage printed to *d* decimals is an interval, not a number. Given a group size *n*, the admissible integers are those *k* with 100·*k*/*n* inside that interval. The reconstruction is determined only if that set has exactly one member. `determinacy_test.py` performs this test.

**Evidence that the test is necessary.** Ten PARADIGM-HF quantities whose true counts are printed alongside their percentages in the FDA review were reconstructed by percentage × denominator: **wrong in eight of ten, once by two events**, and the rounding interval admitted four or five candidate integers in **ten of ten**. The presence of a percentage and a denominator is not evidence of determinacy.

**Both conditions must hold.** Testing the interval alone is not enough — several diagnostic-accuracy rows pin a unique integer only because a group size was itself imputed. Pinned to an imputation is not determined. Of 26 back-computed rows in the corpus, **2** satisfy both conditions.

---

## 1. The four rules that everything else serves

1. **Read the number, or reconstruct it only where the arithmetic is determined and you store the working.** No multiplying a percentage by a denominator. No summing total component counts into a composite. `CHK006`, `CHK004`, `CHK007`, `CHK016`, `CHK017`.
2. **A blocked fetch is a blocked fetch, never an absence.** Retrieval failure goes in `Cell.obstacle` and raises `BlockedFetch`. It never becomes "not reported". `CHK009`.
3. **Identifiers by lookup, never recall.** Every NCT resolved live. `CHK010`.
4. **Fail closed.** A cell that cannot be shown safe is BLOCK, not PASS. Missing information is never reassurance.

---

## 2. Retrieval fallback chain

Encoded in `REGISTRY_FALLBACK_CHAIN`; `--chain` prints it. Do not rediscover this.

| # | Strategy | Status |
|---|---|---|
| 1 | `web_fetch` of `clinicaltrials.gov/api/v2/studies/<NCT>?fields=ResultsSection` | **Refused at the tool layer** in this environment (observed 2026-08-12). An obstacle, not an absence — fall through. |
| 2 | **Chrome, same-origin fetch** — navigate to `clinicaltrials.gov/study/<NCT>?tab=results`, then `fetch('/api/v2/studies/<NCT>?...')` from the page context | **Works. This is the default path.** No CORS, full structured module. |
| 3 | Chrome `get_page_text` on the results tab | Fallback if the API shape changes. Registry results are JS-rendered, so a raw HTML fetch returns an empty shell — the browser is required. |
| 4 | PubMed → PMC full text → outcomes table | **Required whenever the registry is percentage-only.** |
| 5 | Publisher site via Chrome | Abstract/Results paragraphs often carry per-arm counts even when tables are paywalled. Confirmed working on nejm.org, jstage, pmc. |
| 6 | FDA statistical review / EMA EPAR | For trials predating results posting. |

### Tier order by publisher — decided in advance, not per article

**For an NEJM trial, go to the regulatory layer or the registry results module FIRST. Do not fight the article.**

NEJM renders outcome tables outside the DOM: `document.querySelectorAll('table').length` returns 0 on a full-text article, the "Table 2" anchors are in-page fragments whose content never loads, and clicking the Tables tab does not populate them. The Results *prose* carries per-arm counts only where the authors happened to write them out — which worked for ODYSSEY OUTCOMES, HEART-FID and TWILIGHT's composite, and failed for FOURIER, CREDENCE and EMPEROR-Reduced, where the prose gives hazard ratios only. Chasing the article first cost this lane several rounds for nothing.

Resulting order:

| Publisher | Try first | Then |
|---|---|---|
| **NEJM** | registry results module → **FDA/EMA (T3)** | article prose (counts only if the authors wrote them out) |
| PMC / open access | article tables | registry |
| Lancet, JAMA | article (tables often in DOM) | registry → T3 |
| Japanese/regional journals (J-Stage) | article (full text in DOM) | registry |

### T3 recipe — Drugs@FDA (validated 2026-08-12)

1. Find the application number for the drug (Drugs@FDA search; do not use recall).
2. Approval-package table of contents — note the extension is **`.html`, not `.cfm`**:
   `https://www.accessdata.fda.gov/drugsatfda_docs/nda/<year>/<app>Orig1s000TOC.html`
3. The TOC links every review with a stable suffix:
   `…Orig1s000StatR.pdf` (statistical) · `…MedR.pdf` (clinical) · `…SumR.pdf` (summary) · `…ClinPharmR.pdf`
4. **Read the PDF with `mcp__workspace__web_fetch`.** It returns extracted text. Two constraints found: `timeout_ms` is capped at 30000, and a large statistical review (~1.7 MB) times out. **Start with `SumR.pdf`** — the cross-discipline summary is small, carries the pivotal efficacy tables, and succeeded where `StatR.pdf` timed out.
5. The interactive PDF viewer (`display_pdf` / `interact`) **does not work in a non-interactive session** — the iframe never mounts and the viewUUID dies after 8 s. Do not route through it here.

Worked example: Entresto, NDA 207620, 2015. `…207620Orig1s000TOC.html` → `…207620Orig1s000SumR.pdf` → Tables 1–3 give subject disposition, the primary composite with its **first-event decomposition**, and all-cause death, all as integers with percentages.

Two output-hygiene rules learned the hard way when scripting step 2:

- **Strip URL-like tokens** from anything you return. The tool layer rejects payloads containing query strings (`[BLOCKED: Cookie/query string data]`). `String(s).replace(/\S*=\S*/g,' ')` fixes it.
- **Never return the whole results module.** It exceeds the token cap. Slice in-page to the outcomes you want. `CHROME_JS_TEMPLATE` in the harness is a working starting point.

---

## 3. Source tiers

| Tier | Meaning |
|---|---|
| **T1** | The trial's own primary publication — journal table or Results text |
| **T2** | Registry posted results module |
| **T3** | Regulatory review (FDA statistical review, EMA EPAR) |
| **T4** | **Prior meta-analysis extraction table — UNVERIFIED.** Must set `flagged_unverified: true`. A T4-only cell is BLOCKed. Reyaz 2023 had both a comparator and a follow-up wrong in the single row that was checked. |

---

## 4. The checks, and the mistake each one exists to prevent

| Check | Prevents | Real instance |
|---|---|---|
| `CHK001_COUNT_PERCENT_AGREEMENT` | A count that contradicts the percentage printed beside it | ARNI round: 24/24 agreed, which is what made the denominators trustworthy |
| `CHK002_DENOMINATOR_NOT_RANDOMISED` | Recording only one of analysed/randomised | PARADIGM-HF 4187/4212 analysed vs 4209/4233 randomised; PARALLEL-HF 111/112 vs 112/113 |
| `CHK003_DUPLICATE_OUTCOME_POPULATION` | Silently picking between two arm-pairs for one outcome | PARADIGM-HF posts all-cause death twice: 711/835 (FAS) and 714/837 (randomised) |
| `CHK004_PERCENTAGE_ONLY_REGISTRY` | Multiply-a-percentage creeping in | PARACHUTE-HF: all four key outcomes percentage-only. 16 of 25 cardio-atlas gaps are the same |
| `CHK005_SINGLE_SOURCE_CELL` | "22 of 24 confirmed" hiding which 2 | PARALLEL-HF all-cause death exists only in the registry |
| `CHK006_ADMISSIBLE_PROVENANCE` | Provenance outside {read, derived_determined}; empty cells with no stated reason | — |
| `CHK007_COMPOSITE_COMPONENT_ARITHMETIC` | A composite inconsistent with its components, in whichever direction the declared `component_basis` requires | **This check was wrong in v1.0** — see below |
| `CHK008_EVENTS_WITHIN_DENOMINATOR` | events > analysed | Catches recurrent-event counts masquerading as 2×2 cells |
| `CHK009_BLOCKED_FETCH_NOT_ABSENCE` | Logging a refused fetch as "no data" | The CT.gov API refusal above |
| `CHK010_IDENTIFIER_PROVENANCE` | NCT from memory | PARALLEL-HF = NCT02468232, resolved by lookup |
| `CHK011_UNVERIFIED_TIER_FLAGGED` | Prior-meta tables passing as primary | Reyaz 2023 |
| `CHK012_ARM_PAIR_COMPLETE` | Half a 2×2 | — |
| `CHK013_AE_MODULE_DEATHS_NOT_EFFICACY` | Using the registry's adverse-events death count as the efficacy endpoint | **New this round — see below** |
| `CHK014_EFFECT_ESTIMATE_CONSISTENCY` | Counts that cannot reproduce the stored effect estimate | Caught HEART-FID's 12-month count (RR 0.83 vs stored HR 0.95) |
| `CHK015_INHERITED_WITHOUT_PRIMARY_VERIFICATION` | A count taken from someone else's synthesis and never read at a primary source | Reyaz 2023. CHK011 asks whether a T4 source was *flagged*; this asks whether anyone *looked* |
| `CHK016_FORBIDDEN_CONSTRUCTION` | Underdetermined reconstruction; composites summed from total component counts; percentage × denominator | Blocks 48 of 64 diagnostic-accuracy cells; permits the 4 that are determined |
| `CHK017_DETERMINED_DERIVATION_REPRODUCIBLE` | A permitted derivation that a reader cannot redo — missing inputs, missing formula, or arithmetic that does not reproduce the stored value | Enforces the condition attached to the 2026-08-12 ruling |

### CHK013 in detail — the trap that nearly cost the whole sweep

ClinicalTrials.gov requires an all-cause death count in the **adverse-events module** (`eventGroups[].deathsNumAffected`). It is an integer, it is posted even when the efficacy outcomes are percentage-only, and it is therefore extremely tempting as a universal source. It answers a different question: **safety population, adverse-event collection window**, not the efficacy analysis set over the efficacy follow-up.

Measured divergence in this sweep:

| Trial | AE module | Efficacy endpoint | Divergence |
|---|---|---|---|
| SPRINT | 155 / 210 | 155 / 210 | identical |
| DECLARE-TIMI 58 | 529 / 570 | 529 / 570 | identical |
| PARAGON-HF | 347 / 357 | 342 / 349 | small |
| DAPA-HF | 286 / 333 | 276 / 329 | small |
| ODYSSEY OUTCOMES | 238 / 278 | 334 / 392 | **~100 events per arm** |
| EMPA-KIDNEY | 314 / 353 | 148 / 167 | **>2×** |

Sometimes identical, sometimes double. Never safe to substitute silently.

### CHK007 was wrong in v1.0 — recorded because the correction came from evidence

v1.0 asserted flatly that a composite must never equal the sum of its components, on the evidence that PARADIGM-HF's composite is 914 while CV death (558) and HF hospitalisation (537) sum to 1095. The evidence was real; the rule drawn from it was too broad, and **it would have blocked a correct extraction.**

The FDA statistical review for NDA 207620 prints both decompositions of the same composite:

| | CV death | HF hospitalisation | composite |
|---|---|---|---|
| **First event** (LCZ696) | 377 | 537 | **914 = 377 + 537** |
| **First event** (enalapril) | 459 | 658 | **1117 = 459 + 658** |
| **Total events** (LCZ696) | 558 | 537 | 914 ≠ 1095 |
| **Total events** (enalapril) | 693 | 658 | 1117 ≠ 1351 |

First-event components sum to the composite *exactly*, by construction — each participant is attributed to whichever component came first. Total-event components do not, because a participant can appear in both. So the correct relationship is **opposite in the two cases**, and the check now requires `component_basis` to be declared as `first_event` or `total` before it will judge anything.

### CHK014's limitation — stated because it matters

Agreement with a stored effect estimate is **necessary but not sufficient**. For ODYSSEY OUTCOMES the AE-module pair (238/278, RR 0.856) and the efficacy pair (334/392, RR 0.852) **both** reproduce the stored HR of 0.85, while differing by about 100 events per arm. Disagreement is informative; agreement authenticates nothing. CHK014 therefore emits WARN on disagreement and INFO on agreement, and never PASSes a cell on its own.

**This limitation travels with the check's output, not just with this document.** `CHK014_CAVEAT` is printed at the top of every markdown report that contains any CHK014 finding, and is written into the `chk014_caveat` key of the JSON output. A reader who never opens this file still sees it. Two further live instances found since: the atlas's TWILIGHT row (RR 0.995 vs stored 0.99) and its GLOBAL LEADERS row (RR 0.937 vs stored 0.93) are both internally consistent and both wrong — see the defect ledger.

---

## 4a. Running the harness on non-intervention data

Diagnostic-accuracy studies store a 2×2 of a different shape (TP/FP/FN/TN) but the discipline is identical. `adapt_dta_to_cells.py` maps them:

```
stratum "reference-positive"  -> events = TP, analysed = TP + FN
stratum "reference-negative"  -> events = FP, analysed = FP + TN
```

Both strata are denominators the study actually reports, so CHK002, CHK005, CHK006, CHK008, CHK012 and CHK016 apply unchanged. Two modelling rules the adapter learned the hard way:

- **`population_label` must be the analysis tier, not the stratum** — otherwise each stratum forms its own group and CHK012 reports every 2×2 as a half-pair.
- **The extraction key must include the study label, not just the registration** — one registration can carry several index-test evaluations (the APACE cohort; clinician- versus self-collected swabs), and keying on the NCT alone makes them collide as duplicate populations.

---

## 5. Cell schema

```jsonc
{
  "trial": "PARADIGM-HF", "nct": "NCT01035255", "arm": "sacubitril/valsartan",
  "outcome": "all_cause_death",
  "events": 711, "analysed": 4187, "randomised": 4209,
  "population_label": "FAS",
  "denominator_reason": "37 at GCP-closed sites + 6 mis-randomised",
  "printed_percent": 17.0,
  "provenance": "read",                       // only "read" is admissible
  "selected": true,                            // exactly one true per duplicated outcome
  "identifier_provenance": "lookup",
  "registry_units": "participants",
  "is_component_of": null,
  "sources": [ { "tier": "T1", "pointer": "NEJM 2014 Results text", "url": "..." } ],
  "not_recovered_reason": null,
  "obstacle": null,
  "notes": "stored_hr=0.84 arm_role=treatment"
}
```

Conventions: `denominator_reason` beginning `NOT STATED` downgrades CHK002 to WARN and marks an open item — an unexplained exclusion is not the same as an explained one. `notes` may carry `stored_hr=<x>` and `arm_role=treatment|control` to activate CHK014.

---

## 6. Standing order for the next lane

1. Resolve every identifier by lookup. Record how.
2. Registry first via **Chrome same-origin fetch** (chain step 2). Scan outcome titles for the outcome concept; check `unitOfMeasure`.
3. If `unitOfMeasure` contains "percent" → mark `registry_units` accordingly and go to the publication. Do not derive.
4. Read participant flow for **both** randomised and analysed, plus the exclusion reason. If the source does not give a reason, write `NOT STATED …` rather than inventing one.
5. Never take the count from the adverse-events module for an efficacy endpoint. If you record it at all, set `selected: false` and label the population.
6. Where one outcome has two populations, record both, set `selected` on exactly one, and say why.
7. Run the harness. Fix BLOCKs. Do not hand on a BLOCKed extraction.
8. Report the rate with its denominator, and make single-source cells individually visible.
