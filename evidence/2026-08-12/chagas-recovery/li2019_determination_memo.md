# Determination memo — "Li 2019", ARNI_HF_REVIEW screening log

**Date:** 12 August 2026
**Revised:** 12 August 2026 — record retrieved and read at source via Chrome. Verdict is now determinate.
**Row status on entry:** eligibility UNDETERMINED; record could not be retrieved; ~126 randomised; surfaced only via PMC10710849
**Standalone document.** Nothing written to `F:\rapidmeta-finerenone`.

---

## 1. Verdict

# INELIGIBLE

**Criterion failed: Condition 2 — the comparator.**

The control arm received **benazepril 10 mg once daily**, not enalapril. This is stated in the authors' own English abstract and in the Chinese abstract, and restated in the Conclusions.

> "All patients were given a standard heart failure treatment, and the experimental group underwent sacubitril/valsartan(100 mg Bid)and the control group **received benazepril(10 mg Qd)** additionally for 12 months."
> — authors' English abstract, read verbatim

> "对照组给予**贝那普利**(10mg,1次/d)"
> — Chinese abstract, read verbatim

> "**Compared with benazepril**, sacubitril/valsartan can improve the left ventricular function and exercise tolerance…"
> — authors' Conclusions, read verbatim

Benazepril is a different ACE inhibitor. The frozen question requires sacubitril/valsartan **against enalapril**. This trial does not make that comparison, so it is out regardless of anything else.

**Condition 4 also fails, independently.** The quantity reported is not a time-to-first-event hazard ratio. The abstract enumerates exactly what was compared:

> "Left ventricular ejection fraction(LVEF), N-terminal pro-brain natriuretic peptide(NT-proBNP), six-minute walk test(6MWT) and major adverse cardiovascular events(mortality and readmission for heart failure) were compared between the two groups."

and reports them as between-group **means ± SD**:

| Outcome | Sacubitril/valsartan | Benazepril |
|---|---|---|
| LVEF | (38.5 ± 3.1)% | (36.9 ± 3.0)% |
| NT-proBNP | (744.5 ± 246.7) ng/L | (983.3 ± 326.1) ng/L |
| 6MWT | (323.4 ± 60.5) m | (283.5 ± 45.9) m |

*All four values read verbatim from the authors' English abstract.*

The event outcome is characterised as a **rate**, not a time-to-event estimate — "reduce the **readmission rate** due to chronic heart failure". **No hazard ratio, no Cox model, no time-to-event analysis appears anywhere in the abstract.**

Scope note on Condition 4: I read the abstract, not the full text. The abstract's own enumeration of compared outcomes and its mean ± SD presentation are sufficient to establish that *the abstract* reports no HR. Whether a hazard ratio appears somewhere in the five-page full text is not established — and does not need to be, because Condition 2 excludes the study outright.

**My earlier provisional lean was directionally right but landed on the wrong criterion.** I leaned toward failure on Condition 4 (the measure). The actual binding failure is Condition 2 (the comparator) — the one I had flagged as "genuinely in doubt, not merely unverified". The doubt was well placed.

---

## 2. Condition-by-condition, resolved at source

| # | Condition | Verdict | Basis |
|---|---|---|---|
| 1 | Randomised trial | **MET** | "randomly divided into the experimental group(n=62) and the control group(n=64)"; Chinese: 应用随机数字法 (random number method). **Read at source** |
| 2 | Sacubitril/valsartan **vs enalapril** | **FAILS** | Control arm is **benazepril 10 mg Qd**. Stated three times: Chinese Methods, English Methods, English Conclusions. **Read at source** |
| 3 | Adults with **HFrEF** | **Probably met — but the entry threshold is NOT stated in the abstract** | Population is elderly patients with dilated-cardiomyopathy-induced chronic HF; post-treatment LVEF 38.5% and 36.9%, both reduced. The Conclusions flag "preserved LVEF" patients as *not* covered, implying HFpEF was excluded. **No numeric EF entry criterion appears in the abstract.** Not resolved at source |
| 4 | CV death or HF hospitalisation as **time-to-first-event HR** | **FAILS (on the abstract)** | Reports LVEF, NT-proBNP, 6MWT as mean ± SD, and MACE as "mortality and readmission for heart failure" described as a **rate**. No HR. **Read at source** |

---

## 3. Resolved citation — complete

**李江, 曹佳宁, 刘文娴, 吴山, 康云鹏.**
沙库巴曲缬沙坦治疗老年人扩张型心肌病致慢性心力衰竭的疗效观察.
**Li Jiang, Cao Jianing, Liu Wenxian, Wu Shan, Kang Yunpeng.** Efficacy of Sacubitril/Valsartan in the treatment of chronic heart failure in elderly patients with dilated cardiomyopathy.
**中华老年医学杂志 [Chinese Journal of Geriatrics]. 2019;38(5):520–524.** 共5页. Chinese.

| Field | Value | How established |
|---|---|---|
| Authors (Chinese) | 李江, 曹佳宁, 刘文娴, 吴山, 康云鹏 | **read at source** (CQVIP record) |
| Authors (romanised) | Li Jiang; Cao Jianing; Liu Wenxian; Wu Shan; Kang Yunpeng | **read at source** |
| Affiliations | Department of Cardiology, Beijing Anzhen Hospital, Capital Medical University, Beijing 100029; Department of Ultrasound, Beijing Anzhen Hospital | **read at source** |
| Journal | 中华老年医学杂志 / Chinese Journal of Geriatrics | **read at source** |
| ISSN / CN | ISSN 0254-9026 · CN 11-2225/R · monthly · founded 1982 · publisher 中华医学会 | **read at source** (CQVIP journal page) |
| Year / issue / pages | 2019, issue 5, pp. 520–524 | **read at source** |
| **Volume** | **38** | **Indirect but attested** — a sibling article in the same issue is independently cited as *Chin J Geriatr* 2019;**38**(5):525–528. Not printed on the CQVIP record for this article, which shows only "2019年第5期". Not computed from the founding year |
| Indexing | CAS · CSCD core (2019–2020) · 北大核心 (2017 ed.) | **read at source** |
| Funding | 北京市卫生与健康科技成果和适宜技术推广项目 (TG-2017-34) | **read at source** |
| Keywords | 心肌病,扩张型 · 心力衰竭 · 沙库巴曲缬沙坦 | **read at source** |
| CLC codes | R541.6, R542.2 | **read at source** |
| Citation count (CQVIP) | 114 | **read at source** |
| DOI | none found | — |
| PMID | none — journal not in MEDLINE | live PubMed search, zero hits |
| Trial registration | none found | ChiCTR searched, no match |
| CQVIP record | id = 7002078122 | **read at source** |

**Trial design, read at source:**
- Enrolment: Beijing Anzhen Hospital, **January–December 2017**
- N = **126**; **62** sacubitril/valsartan, **64** benazepril — *arm sizes confirmed at source*
- Both arms on standard heart failure therapy; study drug added
- **Treatment duration 12 months**
- Mean age 67.2 ± 5.8 y; 73 male (57.9%), 53 female (42.1%)
- Baseline age, sex, hypertension, diabetes, LVEF, NT-proBNP, 6MWT balanced between groups
- Safety: 1 patient in each group developed symptomatic hypotension

---

## 4. Three errors in the parent meta-analysis, now documented

Reyaz et al., Cureus 2023;15(11):e48623 (PMID 38084196, PMCID PMC10710849) — its Table 1 row for "Li et al. [15]":

| Field | Reyaz 2023 says | Source says | Status |
|---|---|---|---|
| Comparator | **Enalapril** | **Benazepril 10 mg Qd** | **WRONG** — this is the error that kept the row alive in the screening log |
| Follow-up | **6 months** | **12 months** | **WRONG** |
| Sample sizes | 62 / 64 | 62 / 64 | correct |
| Doses | "NR" both arms | SV 100 mg; benazepril 10 mg Qd | incomplete, and the "NR" was the tell |

**Consequence for the ARNI_HF_REVIEW:** Li 2019 entered the screening log only because a meta-analysis mis-recorded its comparator. It was never a sacubitril/valsartan-versus-enalapril trial. Any other row in the log sourced from Reyaz Table 1 should be re-verified at source before use — that table has now produced two demonstrable errors in the single row examined.

**Also worth knowing:** Reyaz pooled Li 2019 into its **all-cause mortality** analysis (Figure 2 sources `[4,12,15-16,18-19]`) — i.e. it pooled a benazepril-controlled trial into a meta-analysis whose stated comparison is "sacubitril/valsartan and enalapril". That is a comparator-mismatch error in the published synthesis, not just in its table.

---

## 5. An internal inconsistency in the paper itself

The two abstracts disagree on the sacubitril/valsartan dosing frequency:

- **Chinese:** 沙库巴曲缬沙坦 **(100mg, 3次/d)** — 100 mg **three times daily**
- **English:** sacubitril/valsartan **(100 mg Bid)** — 100 mg **twice daily**

Recorded, not resolved. Either way, neither matches the 97/103 mg bid target used in the ARNI outcome trials. Immaterial to the verdict.

**Caution on P values from this record:** the CQVIP rendering has lost the inequality characters — it prints "P0.05" in several places, and prints "(P>0.05)" where the surrounding text requires P<0.05. **Do not quote directional P values from this source.** The point estimates and SDs render correctly; the inequality signs do not.

---

## 6. Search record — this session

### Succeeded

| Step | Route | Result |
|---|---|---|
| 1 | Chrome → `https://qikan.cqvip.com/Qikan/Article/Detail?id=7002078122` | **Record rendered.** Full bibliographic block, Chinese abstract, English abstract, keywords, funding, indexing |
| 2 | Chrome → expanded 展开更多 and MORE | **Full Chinese and English abstracts**, both read verbatim. Decisive for Conditions 2 and 4 |
| 3 | Chrome → `Journal/Summary?gch=95748X&y=2019&n=5` | Journal-level metadata: ISSN, CN number, monthly, CMA. **Volume not displayed** |
| 4 | Web search, Chinese | Volume 38 attested via a sibling article in the same issue (pp. 525–528) |

### Failed, with the obstacle named

| Route | Obstacle | Classification |
|---|---|---|
| `http://dianda.cqvip.com/Qikan/Article/Detail?id=7002078122` (Chrome) | Chrome error page — the frame failed to load at all | **Load failure on that host.** The `qikan.cqvip.com` host served the identical record without difficulty |
| `get_page_text` on the rendered CQVIP record | Returned only the page footer; article body sits outside the text-extraction target | **Extraction limitation, not a block.** Worked around with screenshots and the accessibility tree |
| `computer` → `zoom` on the abstract region | CDP `Page.captureScreenshot` timed out at 30 s | **Renderer timeout.** Worked around with a full screenshot |
| Accessibility tree (`read_page`) | Abstract nodes truncated at ~100 characters | **Tree truncation.** Full text obtained from the screenshot instead |

**No paywall was encountered at any point.** The CQVIP record is public and free to read; it simply required JavaScript, which is why plain fetching returned a homepage shell last session. The earlier "could not be retrieved" state was a **rendering capability gap on my side**, not a restriction on the source.

The prior session's blocked routes (Crossref timeouts, Semantic Scholar empty bodies, `rs.yiigle.com` empty, environment-level fetch refusals on `qikan.cqvip.com` and one OpenAlex URL) are recorded in §6 of the previous version of this memo and are superseded — none of them were needed once Chrome was available.

---

## 7. Log entry

```
EXCLUDED
citation: 李江, 曹佳宁, 刘文娴, 吴山, 康云鹏. 沙库巴曲缬沙坦治疗老年人扩张型心肌病
          致慢性心力衰竭的疗效观察. 中华老年医学杂志. 2019;38(5):520-524. [Chinese]
          Li Jiang, Cao Jianing, Liu Wenxian, Wu Shan, Kang Yunpeng.
n = 126 (62 sacubitril/valsartan / 64 benazepril), 12-month treatment
DOI: none | PMID: none (journal not in MEDLINE) | CQVIP id: 7002078122

REASON FOR EXCLUSION — Condition 2, comparator:
  control arm received BENAZEPRIL 10 mg once daily, not enalapril.
  Verified in the authors' own Chinese and English abstracts and Conclusions.

SECONDARY (independent) FAILURE — Condition 4, measure:
  reports LVEF, NT-proBNP and 6MWT as between-group mean +/- SD, and MACE
  (mortality, HF readmission) as a RATE. No time-to-first-event hazard ratio.

PROVENANCE NOTE: this row existed only because Reyaz 2023 (PMID 38084196)
  Table 1 mis-recorded the comparator as "enalapril" and the follow-up as
  "6 months" (source: benazepril, 12 months). Re-verify any other log row
  sourced from that table.
```

---

## 8. What I resolved at source, and what I did not

**Resolved at source (read from the paper's own abstract):**
- Condition 1 — randomised. Met.
- Condition 2 — comparator is benazepril. **Fails. This is the determination.**
- Condition 4 — no hazard ratio in the abstract; LVEF / NT-proBNP / 6MWT as mean ± SD and MACE as a rate. Fails.
- Arm sizes 62 / 64.
- Treatment duration 12 months, enrolment window, mean age, sex split, funding, affiliations, indexing.

**Not resolved at source:**
- **Condition 3, the EF entry threshold.** The abstract gives no numeric LVEF inclusion criterion. Reduced EF is strongly implied by the post-treatment values (38.5% / 36.9%) and by the Conclusions excluding preserved-LVEF patients, but the threshold itself would need the full text. **Moot** — the study is already excluded on Condition 2.
- **Whether a hazard ratio appears anywhere in the five-page full text.** The abstract does not report one. Also moot.
- **The volume number is indirect** — attested from a sibling article in the same issue, not printed on this article's own record.

---

*Every value in §1–§5 was read from the source named beside it. Nothing was inferred into a data cell. The EF entry threshold, the full-text outcome list and the direction of the P values are explicitly marked unresolved rather than filled from expectation. The volume number is labelled indirect. All identifiers were resolved by live lookup.*

**Attribution:** bibliographic records and full texts for PMIDs 38084196 and 37554618 were retrieved from PubMed. DOIs: [10.7759/cureus.48623](https://doi.org/10.7759/cureus.48623) · [10.7759/cureus.41566](https://doi.org/10.7759/cureus.41566). The Li 2019 record was read from CQVIP (维普中文期刊服务平台), record id 7002078122.
