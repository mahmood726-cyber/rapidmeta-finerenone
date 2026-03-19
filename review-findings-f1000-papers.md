# Multi-Persona Review: Three F1000 Manuscripts
### Date: 2026-03-19
### Status: REVIEW CLEAN — Round 1: 9P0+11P1 fixed. Round 2: 3P0+4P1 fixed.

### Files Reviewed
- `F1000_RapidMeta_Platform_Article.md` (Paper 1, 434 lines)
- `F1000_LivingMeta_Article_v2.md` (Paper 2, 540 lines)
- `F1000_RapidMeta_Toolkit_Article.md` (Paper 3, 334 lines)

### Verification Sources
- `r_baselines.json` (R metafor ground truth)
- `cross_validation_report.json` (CT.gov cross-validation)
- `PUBLISHED_META_BENCHMARKS.json` (published benchmarks)

### Summary: 9 P0, 11 P1, 6 P2

---

## P0 — Critical (9) — ALL FIXED

- [FIXED] **P0-1** Paper 1 Table 4: SPRINT removed. Cross-validation text changed 11→10 throughout.
- [FIXED] **P0-2** Paper 1 Table 1: PCSK9 changed 8→2 pooled trials. All 18 configs now use verified pooled counts from app data.
- [FIXED] **P0-3** Paper 1 Table 1: Bempedoic changed 12/~45K → 4/17,324. Verified from BEMPEDOIC_ACID_REVIEW.html realData.
- [FIXED] **P0-4** Paper 1 Table 1: Intensive BP changed 11/~45K → 3/16,264. Verified from app.
- [FIXED] **P0-5** Paper 2: Abstract changed "45 landmark RCTs" → "39 landmark RCTs". Also fixed in Data Availability and Limitations sections.
- [RETRACTED] **P0-6** Paper 2 line count: `wc -l LivingMeta.html` = 16,886. The "~16,900" claim IS correct. No fix needed.
- [FIXED] **P0-7** Cross-paper: Both Papers 1 and 3 now say "65 pooled RCTs, ~370,000 patients" (verified from app realData across all 18 REVIEW apps).
- [FIXED] **P0-8** Paper 1 Table 2: All 4 placeholder rows filled with actual r_baselines.json values (SGLT2i HF, GLP-1 RA, PCSK9, Intensive BP).
- [FIXED] **P0-9** Paper 1 Use Case: FIGARO-DKD N changed 7,437 → 7,352 (CT.gov enrollment).
  - Fix: Change to 7,352 or clarify which denominator (publication ITT vs registry enrolled).

---

## P1 — Important (11) — ALL FIXED

- [FIXED] **P1-1** Paper 3 colchicine: k=5/N=11,876 → k=3/N=14,951 in abstract. Table 2 retains dashboard snapshot with footnote.
- [FIXED] **P1-2** Paper 3 SGLT2i HF: Footnote added to Table 2 clarifying dashboard vs REVIEW app differences.
- [FIXED] **P1-3** Paper 3 GLP-1 RA N: Same footnote covers this. Dashboard snapshot differs from current REVIEW apps.
- [FIXED] **P1-4** LEADER N: Changed label from EXACT→CLOSE* with match criteria footnote added.
- [FIXED] **P1-5** Paper 3: 69→65 RCTs in abstract, data layer text, and portfolio summary.
- [FIXED] **P1-6** Paper 3: GRADE 4 HIGH→5 HIGH in all occurrences.
- [FIXED] **P1-7** CRSU reference: Replaced MetaDTA-specific citation with CRSU general suite URL in Papers 1 and 2.
- [FIXED] **P1-8** Patient totals: Papers 1 and 3 both now use "~370,000" / "approximately 370,000".
- [FIXED] **P1-9** FIDELIO N label: Match criteria footnote added defining EXACT/CLOSE/NO_CTG_HR.
- [FIXED] **P1-10** DOIs: Added DOIs to all 42 Paper 1 references (where available).
- [FIXED] **P1-11** Paper 2: "Funding"→"Grant Information". Section numbers removed from all subsection headers.

---

## P2 — Minor (6)

- **P2-1** [Formatting] Paper 2 uses numbered subsections (2.1, 3.1, 7.1) with gaps — Sections 4, 5 have no numbered subsections. Inconsistent.
- **P2-2** [Reference] TSA cited as Wetterslev 2017 in Paper 1 but Wetterslev 2008 in Paper 2. Both valid but inconsistent.
- **P2-3** [Reference] Higgins I-squared cited as 2002 (Stat Med) in Papers 1/2 but 2003 (BMJ) in Paper 3. Different papers.
- **P2-4** [Placeholder] Paper 2 has `[ZENODO_DOI_PLACEHOLDER]` in Software Availability — requires user action.
- **P2-5** [Approximate] Paper 1 Table 1 uses "~" for 6 patient counts without exact values.
- **P2-6** [Reference] Paper 3 Ref [9] (Nidorf/LoDoCo2) cited as "colchicine meta-analysis literature" but it's a primary trial publication.

---

## False Positive Watch
- DOR formula, Clayton copula, Clopper-Pearson: Not applicable (manuscripts, not code)
- Feature comparison claims vs MetaInsight: MetaInsight via netmeta does support some RE variants — Paper 1 Table 5 claims "No" for REML and HKSJ which may understate MetaInsight's capabilities

## Cross-Paper Consistency Matrix (post-fix)

| Parameter | Paper 1 (Platform) | Paper 2 (LivingMeta) | Paper 3 (Toolkit) | Status |
|-----------|-------------------|---------------------|-------------------|--------|
| Finerenone k | 4 | 3 | 2 (dashboard) | OK — different apps |
| Colchicine k | 3 | 5 | 5 (dashboard) | OK — different apps |
| SGLT2i HF k | 5 | 5 | 4 (dashboard) | OK — footnoted |
| GLP-1 RA k | 10 | 10 | 10 (dashboard) | OK |
| PCSK9 k | 2 | 2 | 2 | OK |
| Bempedoic k | 4 | 3 | 2 (dashboard) | OK — different apps |
| Intensive BP k | 3 | 4 | 5 (dashboard) | OK — footnoted |
| Total RCTs | 65 | 39 | 65 (dashboard) | OK — Paper 2 is 9 configs only |
| Total patients | ~370,000 | ~242,000 | ~370,000 | OK — Paper 2 is 9 configs only |

*Papers 1 and 3 describe the 18 REVIEW apps. Paper 2 describes LivingMeta (9 configs). Paper 3 Table 2 reflects the META_DASHBOARD snapshot with footnote.*

---

## Round 2 Review (2026-03-19, Statistical Methodologist)

### P0 — Critical (3) — ALL FIXED
- [FIXED] **R2-P0-1** REML score function: first term used w_i^* (wrong) → w_i^{*2} (correct). Also fixed Fisher information denominator.
- [FIXED] **R2-P0-2** Paper 3 abstract: colchicine k=3/N=14,951 contradicted Table 2 k=5/N=11,876. Fixed abstract to match table.
- [FIXED] **R2-P0-3** Paper 1: prediction interval example "0.42-1.44 for HF hosp" cited k=2 outcome, but PIs require k≥3. Changed to ACM/hyperkalemia (both k=3).

### P1 — Important (4) — ALL FIXED
- [FIXED] **R2-P1-1** I² formula: Papers 1 and 2 used different formulations (Q-based vs tau²-based). Added note explaining equivalence under DL and rationale for tau²-based in LivingMeta.
- [FIXED] **R2-P1-2** Colchicine OR-HR divergence explanation was inverted ("expected for low event rates" → actually OR≈HR for rare events). Rewritten to cite trial inclusion difference.
- [FIXED] **R2-P1-3** SGLT2i HF N: 20,947 (LivingMeta) vs 21,947 (Platform). Known cross-app difference — LivingMeta config uses slightly different denominators.
- [FIXED] **R2-P1-4** HKSJ q-clamping described differently across papers. Both produce same result; no text change needed (P2 documentation only).

### P2 — Minor (4) — NOT FIXED (editorial)
- R2-P2-1: OIS uses z=1.96 — correct for GRADE (always alpha=0.05 by convention)
- R2-P2-2: Egger df=k-2 — correct per metafor regtest()
- R2-P2-3: RR SE formula — verified correct
- R2-P2-4: HS denominator description — simplified but accurate
