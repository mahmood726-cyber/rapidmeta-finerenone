# Running report #3 — the access ledger

**Date:** 12 August 2026 · extends reports #1 and #2
**Claims under test (Mahmood, verbatim):** *"I have a theory that a workaround is always possible but sometimes the firewalled info is also not useful"*
**Access:** read-only mount. No repo writes.

---

## 0. Headline — both claims, measured

**Claim A — a workaround always exists: supported, but the denominator is smaller than it looks.**
Of 8 access barriers hit in this work, **only 1 was an actual paywall.** The other 7 were my own tooling — bot-blocks, JavaScript gating, image retrieval, a tool that stripped reference markers. **Non-paywall barriers: 7/7 eventually yielded** (5 fully, 2 partially). **Genuine paywall: 0/1 yielded**, after 4 routes. The claim is strongest precisely where it is least interesting, and untested where it matters.

**Claim B — the firewalled content is often not useful: NOT supported in the strong form.**
**6 of 6 breaches changed at least one extracted cell.** None was a wasted trip.

But the refined version **is** supported, and it is the more useful finding: **in 1 of 2 supplement chases, the specific number being chased was not there at all** — and it was sitting in the open main text. **The thing you chase is often in the open layer; the walled layer's value lies in cells you weren't looking for.**

**New this report:** Chen 2026 confirmed as a third published-meta error, same mechanism as Jyotsna.

---

## 1. Claim A — the workaround ledger

### 1.1 Every access barrier, classified

| # | Target | Barrier | Type | Routes tried | Outcome |
|---|---|---|---|---|---|
| 1 | PARACHUTE-HF JAMA main text | Cloudflare "Validate User" | **tooling** (article is open access) | 4: jamanetwork, PMC, Europe PMC REST, NCBI eutils | **PARTIAL** via ESC press release + CTG posted results + 2 appraisals; resolved fully by user |
| 2 | JAMA Supplement 3 | same bot-block | **tooling** (supplement is free) | 2 | **SUCCESS** (user-supplied) |
| 3 | Li 2019 record (CQVIP) | JavaScript gating | **tooling** (record is free) | 7: dianda plain fetch, qikan, yiigle, Crossref, Semantic Scholar, OpenAlex, CNKI/Wanfang | **SUCCESS** — Chrome rendering, 1 route of 7 |
| 4 | Reyaz 2023 reference list | PubMed tool stripped ref markers | **tooling** (paper is open access) | 2 | **SUCCESS** — OpenAlex → publisher PDF |
| 5 | PARADIGM-HF Chagas subgroup component CIs | figure on signed CDN, image bytes unreachable | **tooling** (article open access CC BY-NC) | 3 | **PARTIAL** — point estimate 0.63 (0.31–1.28) via secondary source; component CIs still unobtained |
| 6 | Jyotsna 2023 Table 1 | none | **open** | 1 | **SUCCESS** first try |
| 7 | Chen 2026 Table 1 | none | **open** | 1 | **SUCCESS** first try |
| 8 | **ANSWER-HF per-arm event counts** | **Elsevier paywall** | **GENUINE PAYWALL** | 4: JACC abstract, ClinicalTrials.gov (`hasResults: false`), PubMed, registry | **FAILED** |

### 1.2 Rates

| Denominator | n | Workaround succeeded |
|---|---|---|
| **All barriers** | 8 | 5 full + 2 partial = **7/8 (87.5%)** |
| **Tooling / rendering barriers** | 5 | 3 full + 2 partial = **5/5 (100%)** |
| **No barrier (open, first try)** | 2 | 2/2 |
| **Genuine paywall** | **1** | **0/1 (0%)** |

**The finding that matters: 7 of 8 barriers were not paywalls at all.** Almost everything that looked like an access problem in this work was a retrieval-tooling problem on my side. Claim A is well supported for that class and essentially untested for real paywalls, because only one was encountered.

### 1.3 The split the claim needs — published-but-paywalled vs never-published

These are different problems and conflating them makes the claim unfalsifiable.

**Layer 1 — published but paywalled.** The number exists in print; access is a commercial barrier. A workaround is plausible in principle (regulator review, EPAR, HTA reprint, registry posting, preprint, author manuscript, conference slide, mirrored or non-English copy).
- Instances found: **1** — ANSWER-HF per-arm CV-death and HF-hospitalisation counts.
- Routes exhausted so far: 4. Untried: the ANSWER-HF appraisal full text (Heart Fail Rev, PMID 41870675), conference material, author contact.
- **Status: workaround not yet found. Claim A is currently 0/1 on its true test case.**

**Layer 2 — never published.** The number was never reported by anyone. **No workaround can exist**, because there is nothing to route around.
- **PARACHUTE-HF subgroup interaction p-values.** eTable 8 prints 35 subgroup win ratios and **no interaction p-values anywhere**. The main text asserts consistency without testing it. This is the cleanest example in the whole audit: not paywalled, not hidden — **not computed, or computed and not reported.**
- PARACHUTE-HF pseudo-IPD: recoverable only by digitising Figure 2 C/D/E; never published as numbers.
- ANSWER-HF individual patient data; all clinical study reports; confidential regulatory annexes.

**This is the genuinely inaccessible layer, and it is not the paywalled one.** Open access does not touch it. In this audit the unpublished layer has produced more irrecoverable cells (1 confirmed, several structural) than the paywalled layer (1).

---

## 2. Claim B — did breaching change anything?

The measurement nobody makes: every time we got behind a wall or barrier, did it **change an extracted cell**?

| # | Breach | Changed ≥1 cell? | Changed the cell we were chasing? | What it yielded |
|---|---|---|---|---|
| 1 | JAMA main text (Table 2) | **YES — large** | **YES** | All-cause mortality HR 0.98 (0.77–1.25) — the chased cell; plus Fine–Gray subdistribution HR 0.74 (0.49–1.14), composite counts 155/169, all P values, per-100py rates, full safety panel, unstratified win ratio 1.54. **Also corrected an error of mine** (the −41.1 flag) |
| 2 | **JAMA Supplement 3** | **YES** | **NO** | Chased: mortality HR, KM curves, interaction p-values → **none present; "hazard" appears zero times in 26 pages.** But yielded component win ratios 1.03 / 1.11 / **3.15**, NT-proBNP at month 8, per-protocol and total-death sensitivity WRs, per-country WRs, eTable 3 medications, eTable 9 AE terms |
| 3 | Li 2019 CQVIP record | **YES — decisive** | **YES** | Comparator is **benazepril**, not enalapril. Flipped the verdict from undetermined to ineligible |
| 4 | Reyaz 2023 publisher PDF | **YES — decisive** | **YES** | Reference [15] resolved Li's identity; per-figure source lists showed which outcomes it contributed |
| 5 | Jyotsna 2023 full text | **YES — decisive** | **YES** | Table 1 exposed FIDELIO ×2 + FIGARO ×2 + FIDELITY = triple counting |
| 6 | Chen 2026 full text | **YES — decisive** | **YES** | Same triple-count pattern confirmed |

### Rates

| Metric | Value |
|---|---|
| Breaches achieved | 6 |
| **Breaches that changed ≥1 extracted cell** | **6/6 (100%)** |
| Breaches that yielded the specific chased cell | **5/6 (83%)** |
| Breaches that were a wasted trip | **0/6** |
| **Supplement chases where the chased target was absent** | **1 of 2 (50%)** |

**Claim B is not supported in its strong form.** Nothing behind a wall in this audit turned out useless. Six for six.

**But the sharp version survives and is more interesting.** Supplement 3 is the case Mahmood cites, and it is real: I chased it for the mortality HR, the subgroup forest plot and the KM curves. **It contained none of them** — all three were main-text objects. The supplement's actual value was elsewhere: eFigure 2's component win ratios (CV death 1.03, HF hospitalisation 1.11, NT-proBNP **3.15**) are arguably the single most informative thing recovered in this entire session, and I was not looking for them.

So the defensible formulation is:

> **The specific number you chase behind a wall is often in the open layer you already had. The walled layer is rarely worthless — but its value is usually in cells you weren't looking for, which means chasing a named target through a paywall is a poor predictor of whether the trip pays.**

That reframes the access question from "can we get in" to "were we chasing the right object" — and it is testable going forward.

---

## 3. New finding — Chen 2026 confirmed as error #3

Flagged in report #2, now confirmed from its own Table 1 (open access, retrieved first try):

| Table 1 row | T | C | What it actually is |
|---|---|---|---|
| Katayama | 84 | 12 | ARTS-DN Japan |
| **Bakris** | **6519** | **6507** | **FIDELITY — the pooled FIDELIO + FIGARO** |
| Sarafidis | 440 | 450 | ARTS-DN sub-study |
| **Barkris** | **2840** | **2833** | **FIDELIO-DKD** |
| Barkris | 727 | 94 | ARTS-DN |
| **Pitt** | **3686** | **3666** | **FIGARO-DKD** |
| **Ruilope** | **2830** | **2839** | **FIDELIO-DKD again** |

All values read verbatim. FIDELIO-DKD enters as "Barkris", again as "Ruilope", and a third time inside "Bakris"=FIDELITY. FIGARO-DKD enters as "Pitt" and again inside FIDELITY.

Same mechanism as Jyotsna, and the same tell: **misspelling "Barkris" for "Bakris"** let two entries for one trial sit side by side undetected.

**A second, independent defect in the same paper:** the outcome-to-estimate mapping is internally contradictory. The abstract assigns HR 0.82 (0.74–0.91) to the secondary composite and HR 0.76 (0.70–0.83) to kidney failure. Results §3.4 assigns 0.76 to the secondary composite; §3.5 assigns 0.82 to kidney failure; the Discussion swaps them back. **The paper contradicts itself on which estimate belongs to which outcome.** Our corpus followed the abstract, which is defensible.

---

## 4. Updated scoreboards

### Object A — our extraction of published metas
| | |
|---|---|
| Cells checked | 21 |
| Correct | **20 (95.2%)** |
| Wrong | 1 (Jyotsna outcome mislabel) |

### Object B — published syntheses
| Synthesis | Verdict | Failure mode |
|---|---|---|
| Reyaz 2023 | ERROR | Checking (comparator, follow-up) |
| Jyotsna 2023 | ERROR — severe | Checking (triple-count) |
| **Chen 2026** | **ERROR — severe** | **Checking (triple-count + internal contradiction)** |
| Alam 2023 | Defensible | — (stated English-only restriction) |
| Bao 2022 | Correct as reported | — (non-independent with Zhang) |
| Zhang MZ 2022 | Correct as reported | — (non-independent with Bao) |

**6 adjudicated · 3 errors · 3 correct-or-defensible.**

### Failure modes, still separated
| Mode | Confirmed |
|---|---|
| **(a) Search breadth** | **0** |
| **(b) Checking** | **3** — and all 3 are duplicate-identity or comparator errors, i.e. *the same trial entered wrongly*, not a missing trial |

The pattern hardening across three independent syntheses: **the dominant published-meta failure is counting one trial as several**, enabled by citation-string matching instead of trial-identity matching. Jyotsna and Chen both inflate N by ~50–80% and both report I² ≈ 0%, which is what pooling data against itself produces.

---

## 5. Counter-examples — hunted, not awaited

**For Claim A:** ANSWER-HF's per-arm event counts. One genuine paywall, four routes failed. **This is the live counter-example** and it should be attacked next, because Claim A currently stands at 0/1 on its only real test.

**For Claim B:** none found — no breach was a wasted trip. The closest thing is Supplement 3's absence of the chased target, which is a partial counter-example to the chase, not to the value of the content.

**A wall guarding something decisive** would be the strongest counter-example to Claim B, and I have not found one. The nearest candidate remains ANSWER-HF: if its event counts turn out to change the pooled Chagas estimate, that is a paywall guarding something that matters. Unresolved, and worth resolving.

---

## 6. Next

1. **Attack ANSWER-HF's event counts through the untried routes** — Heart Fail Rev appraisal full text (PMID 41870675), ACC/AHA conference material, JACC supplementary. Claim A's only real test.
2. **Duplicate-identity screen across all 13 finerenone metas.** Three of three checked so far have the pattern in some form; k and N against the trial universe is a cheap screen.
3. **Hunt a breadth failure deliberately** — still 0 confirmed. Target areas with substantial non-MEDLINE literature.
4. Resume report #1's queue: 339 `doi.org`-sourced entries, 1,044 unsourced `publishedHR` rows.
5. Keep the access ledger running on every future retrieval — barrier type, routes tried, whether it changed a cell.

---

## 7. Caveats

- **Claim A's true denominator is 1.** Seven of eight barriers were my own tooling. Any strong statement about paywall workarounds rests on a single case that has so far failed.
- **Claim B's denominator is 6**, all from two clinical areas, all breaches I chose to attempt — selected for expected yield, so biased toward "changed a cell".
- The Object B error rate (3/6) comes from triage-selected syntheses. Not a field rate.
- Zero confirmed breadth failures still means *not yet caught*, not *absent*.
- Every value read verbatim; duplication established by identical n and identical arm splits, an identity observation, not arithmetic. No repo writes.

**Attribution:** full texts and abstracts retrieved from PubMed. DOIs: [10.1097/MD.0000000000047098](https://doi.org/10.1097/MD.0000000000047098) · [10.7759/cureus.41746](https://doi.org/10.7759/cureus.41746) · [10.7759/cureus.48623](https://doi.org/10.7759/cureus.48623) · [10.7759/cureus.41566](https://doi.org/10.7759/cureus.41566) · [10.1007/s00228-022-03408-w](https://doi.org/10.1007/s00228-022-03408-w) · [10.3389/fphar.2022.819327](https://doi.org/10.3389/fphar.2022.819327) · [10.1001/jama.2025.19808](https://doi.org/10.1001/jama.2025.19808) · [10.1016/j.jacc.2025.10.053](https://doi.org/10.1016/j.jacc.2025.10.053)
