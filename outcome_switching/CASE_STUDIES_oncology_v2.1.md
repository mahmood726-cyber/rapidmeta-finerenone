# Five oncology framework-change case studies (v2.1)

> 2026-04-30. Companion to FINDINGS_v2.0_oncology.md. Per-trial side-by-side analysis of the 5 oncology framework-change trials confirmed in v2.0 (excluding the NCT02578680 false-positive that was just hyphenation).
>
> Unlike HF's homogeneous "time-to-event → cumulative-incidence" housekeeping pattern, oncology framework changes are substantively varied: surrogate↔final endpoint switches, population narrowing, and TTE→CI reformulations all appear.

---

## 1. NCT03409614 (Regeneron) — Cemiplimab + chemotherapy

**Sponsor: Regeneron Pharmaceuticals · n=789 · Start: 2018-03-06**

**v1 (initial registration):**
> "PFS as assessed by a blinded Independent Review Committee (IRC) based on Response Evaluation Criteria in Solid Tumors version 1.1 (RECIST 1.1) assessments. [Time Frame: Up to 32 months]"

**Current registry (2 co-primaries):**
> "Part 1: Overall Survival (OS). [Time Frame: Up to a maximum of 82.2 months]"
> "Part 2: OS. [Time Frame: Up to a maximum of 68.4 months]"

**What changed:** **Surrogate→final endpoint switch** (PFS → OS). Plus the trial was split into 2 study parts with their own OS primaries. Time frames extended ~2-2.5× (32 → 68-82 months) — consistent with OS requiring much longer follow-up than PFS.

This is the classic **upgrade**: PFS is acceptable for accelerated approval but OS is the gold-standard endpoint. Reframing PFS as OS post-registration suggests the trial was originally powered for accelerated approval and later repositioned for full approval. Whether the OS analysis was pre-specified or post-hoc requires protocol/SAP review.

---

## 2. NCT02394795 PARADIGM (Takeda) — mCRC sequencing

**Sponsor: Takeda · n=823 · Start: 2015-05-29**

**v1:**
> "Overall survival (OS). OS will be measured as the time from the date of randomization to the date of death. [Time Frame: Up to 60 month]"

**Current registry (2 co-primaries):**
> "OS in Participants With Left-sided Tumors. [Time Frame: Up to approximately 60 months]"
> "Overall Survival (OS) in All Participants. [Time Frame: Up to approximately 60 months]"

**What changed:** **Subgroup elevated to primary.** The original OS-overall primary is preserved as a co-primary; a new OS-in-left-sided-tumors subgroup primary was added at the top of the list. Time frame unchanged (60 months).

PARADIGM is the metastatic colorectal cancer (mCRC) sequencing trial. The left-sided primary tumor location is a known prognostic and predictive biomarker for anti-EGFR efficacy in RAS-wildtype mCRC. Elevating left-sided as a co-primary mid-trial is consistent with the post-2015 emergence of left-sided sidedness as a standard stratification — but doing it via registry edit (rather than a published protocol amendment) is non-trivial prereg drift.

---

## 3. NCT03412773 (BeiGene) — Tislelizumab vs sorafenib in HCC

**Sponsor: BeiGene · n=684 · Start: 2017-12-18**

**v1 (3 primaries, in order):**
> 1. "Overall Survival (OS). [Time Frame: From date of randomization up to 4 years, approximately]"
> 2. "Safety Run-In Substudy [Japan only]: Percentage of patients with adverse events"
> 3. "Safety Run-In Substudy [Japan only]: Percentage of patients with dose-limiting toxicities (DLT)"

**Current registry (3 primaries, reordered):**
> 1. "Safety Run-in Sub-study: Number of Participants With Treatment-emergent Adverse Events (TEAEs)"
> 2. "Safety Run-in Sub-study: Serum Concentration of Tislelizumab"
> 3. "Main Study: Overall Survival (OS)"

**What changed:** **Primary reordering** rather than content swap — the OS primary is preserved (now position 3 instead of position 1), and the safety-run-in primaries which were always there got elevated to positions 1-2. Plus the v1 "DLT" primary was replaced with "Serum Concentration of Tislelizumab" — a real content edit on one of the 3 primaries.

This is a **borderline framework change**: the main efficacy primary (OS) is intact, but the visible-first-in-list primary changed from OS to a safety endpoint. From a registry-fidelity perspective, the order matters because reviewers and downstream tools (including our auto-detector) read the first primary as the headline. Whether this counts as substantive drift is a reader-judgement call.

---

## 4. NCT02420821 IMmotion151 (Roche) — Atezolizumab + bevacizumab in RCC

**Sponsor: Hoffmann-La Roche · n=915 · Start: 2015-05-20**

**v1:**
> "Progression-free survival (PFS) as determined by the investigator using Response Evaluation Criteria in Solid Tumors version 1.1 (RECIST v1.1). [Time Frame: Up to approximately 2.5 years]"

**Current registry (3 co-primaries):**
> 1. "Percentage of Participants With Disease Progression as Determined by the Investigator According to RECIST v1.1"
> 2. "Progression-Free Survival (PFS) as Determined by the Investigator According to RECIST v1.1 in PD-L1-Selected Population"
> 3. "Percentage of Participants Who Died of Any Cause in ITT Population"

**What changed:** Multiple layered edits: (a) PFS time-to-event reformulated as **"Percentage with Disease Progression"** cumulative incidence — same DAPA-HF-style housekeeping pattern; (b) **PD-L1-selected population** added as a co-primary (subgroup elevation, like PARADIGM); (c) **OS percentage in ITT** added as a third co-primary.

IMmotion151 is the closest oncology analogue to the HF housekeeping pattern: original TTE primary preserved in spirit but reformulated as cumulative incidence. Plus subgroup + OS additions stack on top. The most heavily-edited primary in the oncology pool.

---

## 5. NCT03504423 (Cornerstone Pharmaceuticals) — FFX vs combination in pancreatic

**Sponsor: Cornerstone Pharmaceuticals · n=528 · Start: 2018-11-09**

**v1 (2 primaries):**
> 1. "Overall Response Rate (ORR). Defined as the rate of Complete Response (CR) plus Partial Response (PR). [Time Frame: At least 6 months (minimum of 12 cycles)]"
> 2. "Progression Free Survival (PFS). Defined as the duration from the date of randomization to the date of progressive disease or death from any cause. [Time Frame: At least 6 months (minimum of 12 cycles)]"

**Current registry:**
> "Overall Survival (OS). [Time Frame: 38 months]"

**What changed:** **Both original primaries dropped, replaced with OS.** ORR (rate) + PFS (TTE) → OS (TTE). This is a **double-surrogate→final endpoint upgrade**. Time frame extended 6 months → 38 months (6× longer).

Same upgrade pattern as Regeneron (NCT03409614), but more dramatic: Cornerstone dropped *two* surrogate primaries to elevate OS as the sole primary. This is the most consequential framework change in the oncology pool — the original ORR + PFS would have supported an accelerated approval; OS alone supports a full approval.

---

## Cross-trial pattern

Three observations from the 5 oncology framework changes:

1. **Surrogate→final endpoint upgrades dominate.** 2/5 (Regeneron, Cornerstone) explicitly switched from PFS or ORR to OS. This is a **different pattern from HF** where all 5 framework changes were time-to-event ↔ cumulative-incidence reformulations of the same content. Oncology framework changes more often involve substantive endpoint hierarchy changes.

2. **Subgroup-elevation is an oncology-specific drift mode.** PARADIGM (left-sided tumors) and IMmotion151 (PD-L1-selected) both elevated subgroup primaries. This pattern doesn't appear in HF and is consistent with oncology's biomarker-stratification culture.

3. **No sponsor concentration.** 5 different sponsors (Regeneron, Takeda, BeiGene, Roche, Cornerstone). Contrast with HF's Novartis ×2 + AstraZeneca ×2 corporate-template hypothesis. Each oncology framework change looks like an independent sponsor decision rather than a portfolio template.

## Adjusted true-positive count

After case-study eyeball:

| NCT | Original auto-classification | After eyeball |
|---|---|---|
| NCT03409614 Regeneron | framework_change | ✅ confirmed (PFS → OS) |
| NCT02578680 Merck | framework_change | ❌ false positive (hyphenation) |
| NCT02394795 PARADIGM | framework_change | ✅ confirmed (subgroup elevation) |
| NCT03412773 BeiGene | framework_change | ⚠️ borderline (reordering, not content swap) |
| NCT02420821 IMmotion151 | framework_change | ✅ confirmed (TTE→CI + subgroup + OS additions) |
| NCT03504423 Cornerstone | framework_change | ✅ confirmed (ORR+PFS → OS) |

**4 confirmed real framework changes** (Regeneron, PARADIGM, IMmotion151, Cornerstone) + 1 borderline (BeiGene reordering). Still 100% industry. Still 0 academic.

Updated rate: 4 confirmed / 184 = 2.2% (vs HF's 5/269 = 1.9% — same ballpark).

## Implications

The cross-area finding holds with eyeball confirmation:

- **Industry-vs-academic asymmetry on framework changes is universal**: 9 confirmed industry framework changes (5 HF + 4 oncology) vs 0 academic in either area. **9/9 industry, 0/197 academic+nonprofit combined.**
- **Mechanism varies by area**: HF is corporate-template housekeeping (TTE → CI + duplicate primaries). Oncology is substantive endpoint hierarchy churn (PFS↔OS, ORR↔OS, subgroup elevation). Different sociology.
- **Oncology framework changes are arguably more consequential** because they involve actual endpoint-tier changes (surrogate vs final), whereas HF framework changes mostly preserve the underlying analytic primary while editing the registry label.

---

## Source artefacts

- v2.0 commit: `ea6bb05`
- This v2.1 commit: TBD
- Source data: `oncology_p3_v1_history.json` + `oncology_p3_current.json` + `oncology_p3_nct_list.json` + `oncology_p3_v1_vs_current.json`
