# The cardiology programme: 53 topics read against their registrations

**52 of 53 closed. One parked on a decision.** Every verdict below was decided from the
trials' own registry records — identity by registration id first, then the registered
endpoint read word for word, before any effect was extracted.

---

## The headline

| | n | of 53 |
|---|---|---|
| **publish a pooled estimate** | **9** | 17% |
| publish **no** pooled estimate | **43** | 81% |
| parked on a decision (`HFREF_NMA`) | 1 | 2% |

**The nine that pool:** ARNI_HF, SOTAGLIFLOZIN_HF (2 pools), IV_IRON_HF (4 pools),
INCRETIN_HFpEF, BEMPEDOIC_ACID, ALIROCUMAB_LIPID, AZILSARTAN (renamed, k=2),
BOCOCIZUMAB_LIPID (k=5), INCLISIRAN_LIPID_KIDNEY.

**This is the result, not a shortfall.** A corpus of 53 pages that looked like
syntheses turns out to support 9. **Four fifths of it was pooling things that cannot be
pooled**, and every one of those pages presented arithmetically impeccable numbers while
doing it.

---

## How to read the counts below — HAND COUNTS ARE FLOORS

**Added 2026-08-18, after a calibration result that changes what these numbers mean.**

The same quantity was measured on this section by two methods: **hand reading** during the
programme, and a **systematic every-rank screen** afterwards. On the unregistered-endpoint
class they disagree by a factor of four to eight — **3 found by hand; 13 ALL plus 10 MIXED
found by the screen.**

> **A count from a screen and a count from a reading are different kinds of number.**
> Every figure in the table below came from **readings**, so every one of them is a
> **FLOOR** — the number of instances found, not the number that exist.

The endpoint-definitions-differ figure of 12 and the k<2 figure of 13 are the most exposed,
because both were accumulated topic by topic and neither has been screened.

## The classes found — ALL HAND COUNTS, THEREFORE FLOORS

| class | n | what it is |
|---|---|---|
| **endpoint definitions differ** | 12 | trials registering genuinely different composites pooled as one — SGLT2_HF (3-component vs 2-component), ABLATION_AF (4 different primaries), INTENSIVE_BP (6 trials, 6 composites), COLCHICINE_CVD, PCSK9, DOAC_CANCER_VTE, RIVAROXABAN_VASC, APIXABAN_AF, EVOLOCUMAB_DYSLIP, RIVAROXABAN_ACS, DABIGATRAN_VTE, ATTR_CM |
| **the subject is the COMPARATOR, never the intervention** | 3 | OLMESARTAN_HTN (retired outright), ENOXAPARIN_VTE, EVOLOCUMAB_ASCVD_AUTO_2 — pages assembled by a drug-name search that matched a name anywhere in a trial record instead of resolving it to an arm |
| **k=1 or k=0** | 13 | the page seeds one trial or none |
| **wrong effect MEASURE for the endpoint** | 2 | BOCOCIZUMAB and PITAVASTATIN both put an **odds ratio** on a continuous percent-change endpoint. BOCOCIZUMAB was rebuilt as a mean difference (k=5); PITAVASTATIN's registry posts no analysis block, so its replacement is owed |
| **different populations** | 3 | RIOCIGUAT_PAH (PAH vs **CTEPH**), MIPOMERSEN_HOFH (homozygous FH vs statin-intolerant), DABIGATRAN_STROKE (AF vs **embolic stroke of undetermined source**) |
| **prevention pooled with treatment** | 1 | EDOXABAN_VTE — prophylaxis after arthroplasty in adults vs treatment of confirmed VTE in children |
| **an uncontrolled extension counted as a contrast** | 2 | MIPOMERSEN (`NCT00477594`, both arms mipomersen), BOSENTAN_PAH (`NCT00319020`, single arm, primaries **height-for-age** and **body weight**) |
| **endpoint types incommensurable** | 2 | SOTATERCEPT_PAH (continuous PVR vs time-to-event), ETRIPAMIL (proportion converted vs time to conversion) |
| **numerator/denominator mismatch** | 1 | CANGRELOR_PCI — all-cause-mortality numerators over primary-composite denominators; **correcting it reverses the conclusion** |
| **a fabricated contrast** | 1 | EVOLOCUMAB_MIXED_DYSL — a fortnightly placebo arm paired against a monthly drug arm; the values are in no source |
| **an endpoint absent from its own registration** | 3 hand -> **13 ALL + 10 MIXED screened** | ANSWER-HF on the ARNI flagship; all seven V114 trials on prevnar15; `NCT00436007` on malaria-vaccines, whose **eighteen outcome measures never mention malaria** |
| **withdrawal reason FALSE** | 1 | APIXABAN_ACS — the card said "bleeding and efficacy pooled"; **both** trials register bleeding |

---

## The class that matters most

**Errors of reference, not calculation.** Four of the verdicts above — different
diseases, prevention against treatment, an uncontrolled extension, comparator-arm
membership — pass **every** internal check this project has. Numbers reconcile, surfaces
agree, identifiers resolve, endpoints match.

> **The defect is never in the numbers. It is in what the numbers are about.**
> Only reading the registration finds it, and only the registration can.

---

## Do published syntheses make the same errors? **4 of 4 checked. 1 affected.**

| topic | published synthesis | same combination? |
|---|---|---|
| RIOCIGUAT_PAH | Wang et al., *Ann Palliat Med* | **YES** — pools PAH with CTEPH into one 6MWD estimate, and does not disaggregate |
| MIPOMERSEN_HOFH | *JCDD* 2021 | no — 5 RCTs, **explicitly excluded** open-label extensions |
| EDOXABAN_VTE | STARS E-3 + STARS J-V pooled analysis | no — prophylaxis pooled with prophylaxis |
| OLMESARTAN_HTN | azilsartan/chlorthalidone vs olmesartan/HCTZ meta-analysis | no — **names the contrast correctly** |

**One affected of four.** The mechanism is supported — the riociguat pool is
arithmetically impeccable and combines two diseases, and nothing in peer review
recomputes — **but the rate is not, and this document claims none.**

**Running score across every literature comparison this project has made: the literature
was right 3 times today and wrong once, after being right on all three previous
occasions.** A project that reported only the comparison it won would have published a
finding four times stronger than its evidence.

---

## Still open

- **`HFREF_NMA`** — parked on Mahmood's network-protocol decision. Its data problem is
  separate and unresolved: **12 distinct NCT strings for 28 trials.**
- **Replacement analyses owed:** PITAVASTATIN and INCRETIN_HFpEF, both needing
  least-squares mean differences the registry does not post.
- **A topic-list question, not a synthesis one:** three omecamtiv pages all seed
  `NCT02929329`; two sacubitril pages both seed `NCT01035255`; two sotatercept pages
  carry the same pair. **Seven topics over four trials.**
