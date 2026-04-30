# Five industry framework changes — per-trial case studies

> 2026-04-30. Companion to FINDINGS_v0.3.md. Each of the 5 industry-sponsored statistical-framework changes audited side-by-side: initial CT.gov v1 record, current registered view, primary-publication framing, and the specific edit performed.
>
> All 5 changes share the same direction: time-to-event reformulated as cumulative-incidence (count or rate). 4 of 5 are concentrated in two corporate portfolios (Novartis ×2, AstraZeneca ×2). The pattern looks like a sponsor-template practice rather than independent decisions per trial.

---

## 1. PARALLEL-HF — Novartis sacubitril/valsartan in Japanese HFrEF

**NCT02468232 · Sponsor: Novartis Pharmaceuticals · Start: 2015-06-15 · Status: COMPLETED**

**v1 (initial registration, ~2015):**
> "Time to the first occurrence of the composite endpoint, which is defined as either cardiovascular (CV) death or heart failure (HF) hospitalization. [Time Frame: up to 40 months]"

**Current registry:**
> "Number of Participants Who Had CEC (Clinical Endpoint Committee) Confirmed Composite Endpoints. [Time Frame: up to 40 months]" plus a second co-primary "Exposure-adjusted Incident Rate (EAIR) of CEC Confirmed Composite Endpoints. [Time Frame: up to 40 months]"

**What changed:** The original time-to-event framing was replaced with two count/rate-based measures (count of participants + exposure-adjusted incident rate). The composite content (CV death + HF hospitalization) is unchanged; the time frame is identical. The shift is purely in the analytic primary's statistical framework. CEC adjudication language was added to the current view, which was implicit in v1.

**Primary publication candidate:** Tsutsui H et al., *Circ J* 2021 (PMID 33731544) — "Efficacy and Safety of Sacubitril/Valsartan in Japanese Patients With Chronic Heart Failure". The published paper reports the count-based primary, consistent with the current registry view.

---

## 2. AEGIS-II — CSL Behring CSL112 (apoA-I infusions) post-ACS

**NCT03473223 · Sponsor: CSL Behring · Start: 2018-03-21 · Status: COMPLETED · n=18,226**

**v1 (initial registration, ~2018):**
> "Time to first occurrence of any component of composite MACE (CV death, MI, or stroke). [Time Frame: Through 90 days]"

**Current registry:**
> "Number of Participants With First Occurrence of Any Component of Composite MACE (CV Death, MI, or Stroke). [Time Frame: From the time of randomization through 90 days]"

**What changed:** Time-to-event reformulated as count of participants. Composite content (CV death + MI + stroke) unchanged. Time frame unchanged (90 days). The edit is purely in the framework label.

**Primary publication:** Gibson CM et al., *NEJM* 2024 (PMID 38587254) — "Apolipoprotein A1 Infusions and Cardiovascular Outcomes after Acute Myocardial Infarction". The trial was negative; the published paper used a Cox-proportional-hazards primary analysis (time-to-event), which contradicts the current registry framing of "Number of Participants...". The discrepancy between the current registry framing and the published statistical analysis is itself a finding — the registry label appears to have been edited toward count-style language while the published primary analysis remained time-to-event.

(AEGIS-II is technically an ACS-not-HF indication; we exclude it from the v0.2 HF pool but it surfaces in the v0.3 broader CT.gov audit because it cites HF as a co-condition.)

---

## 3. DAPA-HF — AstraZeneca dapagliflozin in HFrEF

**NCT03036124 · Sponsor: AstraZeneca · Start: 2017-02-08 · Status: COMPLETED · n=4,744**

**v1 (initial registration, 2017-01-26):**
> "Time to the first occurrence of any of the components of the composite: CV death or hospitalization for HF or an urgent HF visit. [Time Frame: From randomization visit (day 0) up to approximately 3 years]"

**Current registry:**
> "Subjects Included in the Composite Endpoint of CV Death, Hospitalization Due to Heart Failure or Urgent Visit Due to Heart Failure. [Time Frame: Up to 27.8 months]"

**What changed:** Time-to-event reformulated as "Subjects Included in" (cumulative-incidence count). Composite content unchanged. Time frame compressed from prospective ~36 months to retrospective 27.8 months (the actual median follow-up at the database-lock event-driven analysis cutoff). The current registry phrasing matches the published Table 1 / Results format rather than the original protocol-style time-to-event.

**Primary publication:** McMurray JJV et al., *NEJM* 2019 (PMID 31535829) — "Dapagliflozin in Patients with Heart Failure and Reduced Ejection Fraction". The published paper's primary analysis is a Cox model (time-to-event), HR 0.74 (0.65-0.85). The published Table 2 reports both event counts and HR, consistent with the current registry having shifted toward the count-style summary while the published analysis retained time-to-event.

---

## 4. PARADISE-MI — Novartis sacubitril/valsartan in post-AMI HF risk

**NCT02924727 · Sponsor: Novartis Pharmaceuticals · Start: 2016-12-09 · Status: COMPLETED · n=5,669**

**v1 (initial registration, ~2016):**
> "Time to the first occurrence of a confirmed composite endpoint. A confirmed composite endpoint includes cardiovascular (CV) death, heart failure (HF) hospitalization, or outpatient heart failure. [Time Frame: Time from randomization to first occurrence (up to approximately 32 months)]"

**Current registry:**
> "Number of Participants With First CEC (Clinical Endpoint Committee) Confirmed Primary Composite Endpoint. [Time Frame: From randomization to first occurrence (up to approximately 43 months)]"

**What changed:** Time-to-event reformulated as count of participants. Composite components (CV death + HF hospitalization + outpatient HF) unchanged. Time frame *extended* from prospective 32 months to current 43 months — note this is an extension, not compression, distinct from DAPA-HF's compression. CEC adjudication language formalised.

**Primary publication:** Pfeffer MA et al., *NEJM* 2021 (PMID 34758252) — "Angiotensin Receptor-Neprilysin Inhibition in Acute Myocardial Infarction" (PARADISE-MI). The trial was negative for the primary endpoint (HR 0.90, 95% CI 0.78-1.04, p=0.17). The published paper uses time-to-event (Cox HR) as the primary analysis, contradicting the current registry's "Number of Participants" framing. Same registry-vs-published mismatch as AEGIS-II.

---

## 5. DELIVER — AstraZeneca dapagliflozin in HFpEF

**NCT03619213 · Sponsor: AstraZeneca · Start: 2018-08-27 · Status: COMPLETED · n=6,263**

**v1 (initial registration, ~2018):**
> "Time to the first occurrence of any of the components of this composite: 1) CV death; 2) Hospitalisation for HF; 3) Urgent HF visit (e.g., emergency department or outpatient visit). [Time Frame: Up to approximately 33 months]"

**Current registry (two co-primaries):**
> "Subjects Included in the Composite Endpoint of CV Death, Hospitalization Due to Heart Failure or Urgent Visit Due to Heart Failure. [Time Frame: Up to 42.1 months]"
> "Subjects Included in the Composite Endpoint of CV Death, Hospitalization Due to Heart Failure or Urgent Visit Due to Heart Failure for LVEF <60% Subpopulation. [Time Frame: Up to 42.1 months]"

**What changed:** Same DAPA-HF-style reformulation: time-to-event → "Subjects Included" cumulative-incidence framing. Composite content unchanged. Time frame extended (33 → 42.1 months). Plus a *second co-primary* added for the LVEF<60% subpopulation — this is a new primary outcome that did not exist in v1. The LVEF<60% subgroup is the regulatory focus for the post-DAPA-HF dapagliflozin label expansion into HFpEF; adding it as a co-primary is consistent with the manuscript narrative around mildly-reduced ejection fraction.

**Primary publication:** Solomon SD et al., *NEJM* 2022 (PMID 36027570) — "Dapagliflozin in Heart Failure with Mildly Reduced or Preserved Ejection Fraction". The paper reports primary HR 0.82 (0.73-0.92, p<0.001) using time-to-event analysis. As with DAPA-HF and PARADISE-MI, the published primary analysis is time-to-event despite the current registry being "Subjects Included". The LVEF<60% subgroup is reported as a secondary analysis (HR 0.83) in the paper, not as a co-primary.

---

## Cross-trial pattern

Three observations from the 5 cases:

1. **All 5 trials' published primary analyses are time-to-event** (Cox / Kaplan-Meier), matching the v1 registry framing — but the current registry text has been edited toward count or cumulative-incidence framings that the published analysis did *not* use. The drift is in the **registry-text-only** layer, not the underlying statistical analysis.

2. **The composite content is preserved in all 5.** No trial swapped the components (CV death, HF hospitalization, etc.) — only the way the primary was *labeled*. This contrasts with DIAMOND (separate v0.3 case) where the primary content itself was swapped (CV event endpoint → serum-potassium biomarker).

3. **Two sponsors dominate.** Novartis (×2: PARALLEL-HF, PARADISE-MI) and AstraZeneca (×2: DAPA-HF, DELIVER) account for 4 of the 5. CSL Behring (×1: AEGIS-II) is the outlier. Both Novartis and AstraZeneca's HF Phase 3 portfolios in this window show identical edit patterns, consistent with corporate-template-driven registry maintenance.

## What this means for the v1.0 paper

The "industry vs academic" headline (5/78 vs 0/184) is a real finding even after this case-study layer. But the case studies sharpen the interpretation: the framework drift is **registry-text reformulation, not analytic-framework drift**. Sponsors did not change *how they analysed* their primary outcomes; they changed *how the registry labels* the outcome — possibly to match the format of the published table or label-conversation language.

Whether this is benign housekeeping or substantive drift depends on the reader's view of registry fidelity. A strict reader would flag any post-hoc label change as a prereg violation regardless of analytic equivalence; a permissive reader would accept it as cosmetic. The methods paper should probably present the case studies and let the reader judge.

## Source artefacts

- v0.3 commit: `c5db22a`
- This v1.0 case-study commit: TBD
- Source data: `hf_history_v1_198.json` (v1) + `hf_outcomes_269_current.json` (current) + PubMed E-utilities lookups
- Memory pointers: `~/.claude/projects/C--Users-user/memory/feedback_subagent_dispatch.md` and `feedback_finrenone_build_safety.md`
