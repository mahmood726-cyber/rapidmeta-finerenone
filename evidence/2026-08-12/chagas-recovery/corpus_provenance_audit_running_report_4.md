# Running report #4 — enumeration complete, and a cheap test that finds the error class at scale

**Date:** 12 August 2026 · extends reports #1–#3
**Project:** Nafis — an open, multi-source, ledger-based method for verified evidence synthesis
**Access:** read-only mount. No repo writes.

---

## 1. Headline

**The exposure enumeration is now complete, not a floor.** Only one directory in the corpus carries trial rows in the evidence-bearing shape. Corpus totals are final: **1,006 apps, 3,656 trial rows, 3,389 evidence entries.**

**A no-network screening test finds the error class at scale.** A DOI cited as the evidence source for more than one distinct NCT is a suspect — a trial's own primary publication should map roughly 1:1. That test flags **14 DOIs implicating 31 rows** out of 312 distinct DOI sources, and it **independently rediscovered the Cochrane melanoma error** found by hand in report #1. It costs nothing to run.

**Rows adjudicated at primary now total 17: 8 wrong, 7 correct, 2 unresolved.**

**Still zero confirmed search-breadth failures against eleven confirmed checking failures** (8 corpus rows + 3 published syntheses). That asymmetry is now the strongest pattern in the whole audit.

---

## 2. Exposure enumeration — COMPLETE

| Directory | Files | Trial rows | Evidence entries |
|---|---|---|---|
| `outputs/extraction_audit/data` | 1,034 | **3,656** | **3,389** |
| `findings` | 2,190 | 0 | 0 |
| `outputs/extraction_audit/truthcert` | 421 | 0 | 0 |
| `outputs/extraction_audit/quarantine` | 138 | 0 | 0 |
| `nma` | 26 | 0 | 0 |

*Stated precisely: the four other directories carry zero trial rows **in the `realData`/`evidence` shape**. They may hold data in other schemas; they do not hold the provenance-bearing rows this audit is about.*

**Report #1's figures were the whole corpus, not a floor.** Correcting that caveat.

### Provenance profile (final)

| Quantity | Value |
|---|---|
| Rows with ≥1 evidence entry | 2,467 (67.5%) |
| **Rows with no evidence block at all** | **1,189 (32.5%)** |
| Rows carrying a `publishedHR` | 1,870 |
| — of those, unsourced | **1,044 (55.8%)** |
| Evidence entries citing a **published synthesis** | **3 (0.09%)** |
| Distinct `doi.org` evidence sources | 312 |
| — cited for >1 distinct NCT | **14** |
| — rows implicated | **31** |

---

## 3. The screening test, and what it caught

**Rule:** flag any DOI serving as evidence source for more than one distinct NCT. **No network calls required.**

**Validation:** the test independently re-flagged `10.1002/14651858.cd012974.pub2` — the Cochrane melanoma review found by hand in report #1. A test that rediscovers a known bug without being told about it is working.

**Important caveat: roughly half the flags are benign.** A single paper legitimately reports two trials (ENDURANCE-1 and ENDURANCE-3 in one NEJM paper), or one trial legitimately appears in two apps (VIALE-A). **Multi-NCT DOI is a screening signal, not a diagnosis** — every flag still needs adjudication.

---

## 4. Rows adjudicated at primary

### 4.1 WRONG — 8 rows

| # | App | NCT | Row says | Primary source says | Error class |
|---|---|---|---|---|---|
| 1 | DAPT_DE_ESCALATION_PCI | NCT03971500 | ULTIMATE-DAPT, BARC bleeding HR 0.45 | Trial identity **correct**; evidence quote is a Cochrane review on **orthodontic overjet** | provenance fabricated |
| 2 | MELANOMA_NEOADJUVANT | NCT02519322 | "IMmuNED", pembrolizumab **single-arm**, n=30 | MD Anderson, **randomised 3-arm**, nivolumab ± ipilimumab or relatlimab, **n=53**, no pembrolizumab | **intervention + design + n** |
| 3 | MELANOMA_NEOADJUVANT | NCT02437279 | "OPTIMUS-1", n=30, 2023, pCR endpoint | **OpACIN**, Netherlands Cancer Institute, **Phase 1b**, **n=20**, 2016–18, T-cell/safety endpoints | **identity + design + n + outcome** |
| 4 | COPD_BIOLOGICS_BROAD | NCT02138916 | GALATHEA, **benralizumab COPD** | Evidence quote is about **dupilumab** and **nasal polyp score** — wrong drug, wrong disease | outcome + provenance |
| 5 | COPD_BIOLOGICS_BROAD | NCT02155660 | TERRANOVA, **benralizumab COPD** | Same dupilumab/NPS quote | outcome + provenance |
| 6 | HCV_DAA_NEW_NMA | NCT02446717 | EXPEDITION-1 (12wk cirrhosis) | Given **ENDURANCE-1's** verbatim GT1 SVR quote — byte-identical to the ENDURANCE-1 row in the same app | provenance |
| 7 | AML_VEN_FLT3_NMA | NCT01757535 | QUAZAR-AML (oral azacitidine maintenance) | Given **VIALE-A's** adverse-event quote and VIALE-A's DOI | provenance + wrong trial |
| 8 | BLADDER_UROTHEL_FRONTLINE_IO_NMA | **NCT02853305** | "KEYNOTE-052", pembrolizumab **cisplatin-ineligible single-arm** | **KEYNOTE-361** — *"Pembrolizumab With or Without Platinum-based Combination Chemotherapy Versus Chemotherapy Alone in Urothelial Carcinoma (MK-3475-361/KEYNOTE-361)"*, MSD, **n=1,010**, randomised with chemo arms. **Verified live 12 Aug 2026** | **comparator + population + design + n** |

**Rows 2, 3 and 8 are the Reyaz class** — a trial pooled under a comparator or design it does not have. Invisible to every internal consistency check we run.

### 4.2 CORRECT — 7 rows

Stated first-class, not as filler.

| App | NCT | Verdict |
|---|---|---|
| ARNI_HF_REVIEW | NCT01035255 | **PARADIGM-HF — every checkable cell correct**: n 8442, tE/cE 914/1117, HR 0.80 (0.73–0.87), CV death 558/693 HR 0.80 (0.71–0.89), ACM 711/835 HR 0.84 (0.76–0.93), comparator enalapril, LVEF ≤40%, verbatim NEJM quote |
| AML_TARGETED_NEW | NCT02993523 | VIALE-A — DOI is VIALE-A's own paper, quote matches |
| AML_VEN_FLT3_NMA | NCT02993523 | VIALE-A — same trial in a second app, legitimately |
| HCV_DAA_NEW_NMA | NCT02642432 | ENDURANCE-1 — DOI and quote match |
| HCV_DAA_NEW_NMA | NCT02640482 | ENDURANCE-3 — same paper legitimately reports both |
| CRSWNP_BIOLOGIC_NMA | NCT02912468 | SINUS-24 — DOI is the SINUS paper, quote matches |
| ANTI_PDL1_BLADDER | NCT02335424 | KEYNOTE-052 — correct NCT, quote matches |
| CARBAPENEM_RESISTANT_ABX | NCT02714595 | CREDIBLE-CR — DOI is its own paper, quote matches |

### 4.3 UNRESOLVED — 2 rows

- **NCT02898454** labelled "SINUS-24" in EOSINOPHILIC_DISEASES, while CRSWNP labels **NCT02912468** as SINUS-24. One is wrong — likely SINUS-52 mislabelled. Needs lookup.
- **NCT02321800 APEKS-NP** carries CREDIBLE-CR's DOI. Quote content is plausibly APEKS-NP's own; the source DOI is not. Needs lookup.

---

## 5. Rates — with denominators, confirmations first

### Corpus rows

| Metric | Value |
|---|---|
| Rows adjudicated at primary | **17** |
| — **confirmed correct** | **7 (41%)** |
| — confirmed wrong | 8 (47%) |
| — unresolved | 2 (12%) |
| Rows in corpus | 3,656 |
| **Fraction of corpus adjudicated** | **0.46%** |

**This is not a corpus error rate and must not be quoted as one.** Every row adjudicated was drawn from a deliberately enriched suspect set (synthesis-sourced, or multi-NCT DOI). The honest statement: **within the flagged suspect set, roughly half the flags are real errors and roughly half are benign.**

### Published syntheses (from report #2, unchanged)

| Metric | Value |
|---|---|
| Syntheses adjudicated | 6 |
| — correct or defensible | **3** |
| — confirmed error | 3 (Reyaz, Jyotsna, Chen) |
| Our extraction of published metas | **20/21 cells correct (95.2%)** |

### Failure modes — kept separate

| Mode | Confirmed |
|---|---|
| **(a) Search breadth** — trials never found | **0** |
| **(b) Checking** — trials found, characterised wrongly | **11** (8 corpus rows + 3 published syntheses) |

**Eleven to zero.** Every single error found in this audit, in our corpus and in the published literature alike, is a checking failure. Not one is a breadth failure. If that holds, the remedy is deduplication and verification by **trial identity**, not searching harder.

---

## 6. Access ledger — updated, with a third category

**The new category from today, and it changes how a missing cell must be triaged:**

> **A missing cell is three things, not one: not published, not reported, or never defined.**

**ANSWER-HF is the worked example.** Its per-arm composite counts were classified as an access failure. On investigation, **ANSWER-HF has no "CV death or HF hospitalisation" composite endpoint at all** — the composite was a construct imported from PARACHUTE-HF. Its clinical events sit inside a hierarchical win ratio, and the registry classifies HF hospitalisation and all-cause mortality as **exploratory**. Europe PMC records **`hasSuppl: N`** — no supplement exists.

**No workaround can produce an unreported quantity.** Part of that row moves from "published but paywalled" into "never defined", where Claim A cannot apply by construction.

**Rule adopted:** any row classified as an access failure must first be tested against *never defined* and *not reported*. Otherwise the access ledger inflates with cells that were never behind a wall.

### Running access tallies

| Metric | Value |
|---|---|
| Barriers encountered | 8 |
| — genuine paywalls | **1** |
| — tooling / rendering / routing | 7 |
| Workaround succeeded, non-paywall barriers | **7/7** |
| Workaround succeeded, genuine paywall | **0/1** |
| Breaches achieved | 6 |
| — changed ≥1 extracted cell | **6/6** |
| — yielded the specific chased cell | 5/6 |
| New evidence tiers tested this round | **funder reports (FAPESP) — negative**; Europe PMC REST — positive |

---

## 7. Next

1. Adjudicate the remaining 9 flagged multi-NCT DOIs (~15 rows) — cheap, targeted.
2. Run the same screening test on the **1,538 ClinicalTrials.gov-sourced** entries: does the NCT's registered intervention match the row's stated comparator? That is the direct Reyaz-class test at scale.
3. Attack the **1,044 rows carrying a `publishedHR` with no evidence block** — largest pooled-and-unsourced exposure.
4. Hunt a breadth failure deliberately. Eleven-to-zero needs a genuine attempt at the null before it can be reported as a finding.
5. Resolve the 2 unresolved rows (SINUS-24/52, APEKS-NP).

---

## 8. Caveats

- 17 of 3,656 rows is 0.46%. No corpus-wide rate is claimed.
- The suspect set was enriched by construction; the ~50% hit rate applies to flags, not to the corpus.
- Multi-NCT DOI is a screening heuristic — half its flags are legitimate shared publications.
- Zero breadth failures means *not yet caught*, and the sampling was aimed at checking failures. Item 4 above is the corrective.
- Every identifier resolved by live lookup; every value read verbatim; no counts computed or back-derived.
- Read-only throughout. No repo writes.

**Attribution:** trial records from ClinicalTrials.gov; bibliographic records from PubMed, Crossref/Unpaywall, OpenAlex, Europe PMC.
