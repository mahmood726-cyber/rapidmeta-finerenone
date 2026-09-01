# Consolidated: the handover mapping, the amendment, and term specificity as a number

Every claim marked **[MEASURED]** with the command that produced it, or **[INFERRED]**.

    REF.rule   604ed6957a1adf17   ⛔ FROZEN and unchanged by everything below
    REF.frame  a0d44914a5ef99e3   1,186 CDSR cardiology reviews
    REF.aact   folder 2026-08-30, DATA DATE 2026-08-27

---

# 1 THE HANDOVER — topic → our page → counterpart

**[MEASURED]** `scripts/rekey20/counterpart_page_map.py`. The candidate pool is exactly the
topics carrying a **judged** counterpart: a page at full standard with no counterpart cannot
be scored against anything.

    TOPICS in the pool                      10
    COMPARATORS, objectives-verified (CDSR)  6
    COMPARATORS, abstract-verified (OA)     13

| topic | our page(s) | counterpart |
|---|---|---|
| bosentan-pah | `BOSENTAN_PAH_AUTO_FULL_REVIEW` · `_AUTO_REVIEW` | CD004434 |
| bosentan-pah-children | `BOSENTAN_PAH_CHILDREN_REVIEW` | CD004434 |
| bosentan-pah-monotherapy | `BOSENTAN_PAH_MONOTHERAPY_REVIEW` | CD004434 |
| colchicine-cvd-review | `COLCHICINE_CVD_REVIEW` | CD014808 · CD015003 |
| enoxaparin-vte | `ENOXAPARIN_VTE_AUTO_FULL_REVIEW` · `_AUTO_REVIEW` | CD006681 |
| etripamil-psvt | ⛔ **NONE** | PMC10328856 |
| mavacamten-hcm-review | `MAVACAMTEN_HCM_REVIEW` | 7 OA reviews |
| riociguat-pah | `RIOCIGUAT_PAH_AUTO_FULL_REVIEW` · `_AUTO_REVIEW` | PMC13124407 |
| selexipag-pah | `SELEXIPAG_PAH_AUTO_FULL_REVIEW` · `_AUTO_REVIEW` | PMC12554579 |
| sotatercept-pah | `SOTATERCEPT_PAH_AUTO_FULL_REVIEW` · `_AUTO_REVIEW` · `_REVIEW` | 3 OA reviews |

⛔ **NOT RANKED HERE.** `tabs_with_content` is another lane's instrument.

## Three things the ranking lane must be told

1. **`PAGE_MAP.json` declares NOTHING for any of the ten.** Page identity here comes from the
   disk alone.
2. **Six of ten have more than one delivered page**, sotatercept has three. One object with
   two delivered pages has cost this project a count before — whoever scores must be told
   *which*.
3. **`etripamil-psvt` has a counterpart and no page at all.** It cannot be candidate three
   until a page exists.

⚠️ **The two counterpart sources are NOT pooled.** CDSR counterparts were verified against a
Cochrane objectives statement, OA ones against an abstract; a quality claim across them would
compare two measurements under one name.

⭐ **My own matcher over-matched first** and I caught it before handover: a prefix match gave
`bosentan-pah` the pages of its **siblings**. A prefix match on a topic family silently
absorbs every member whose name extends it — and this mapping goes to another lane, so the
error would have propagated as a wrong page to score.

---

# 2 THE AMENDMENT — already written, committed `4dde3e3a6`, **not applied**

`PROPOSED-RULE-AMENDMENT-3.md` holds the text, justification and measured impact for A1
(`F5` misses mRNA, 1 of 68 topics), A2 (multi-stem records concatenate unrelated classes,
4 of 68, **two re-keyed with a mechanism the drug does not have**) and A3 (R2 protects review
ids where it should protect judged pairs).

**[MEASURED]** verified in the same run as the commit: fingerprint still `604ed6957a1adf17`,
`MODALITY_STEMS` unchanged. **Recommendation: approve A2 and A3, hold A1** until the
cache-derivation fix ships with it — A1 changes behaviour *without* changing the fingerprint,
because `class_is_modality` is a **stored derived value** in the ChEMBL cache.

---

# 3 ⭐ TERM SPECIFICITY, TURNED FROM A DIAGNOSIS INTO A NUMBER

**[MEASURED]** `scripts/rekey20/term_specificity.py` — document frequency over 274 distinct
candidate terms across all three condition axes, N = 1,186.

| axis | terms | **dead** (df=0) | **promiscuous** (df>10%) | median df | max df |
|---|---|---|---|---|---|
| literal | 38 | 3 · 8% | 2 · 5% | 35 | 198 |
| mesh_v2 | 113 | **83 · 73%** | 1 · 1% | **0** | 198 |
| aact | 568 | 203 · 36% | 27 · 5% | 4 | **207** |

## 3.1 The terms that distinguish nothing

    axis      term                    topics using it   df      df_frac
    aact      disease                        20        207      17.5%
    aact      cardiovascular                 15        111       9.4%
    aact      vascular                       12         60       5.1%
    aact      vascular disease               12          4       0.3%
    aact      tract                           7          0       0.0%
    literal   hypertension                    7         95       8.0%

⭐ **Both failure directions are now visible in one table.** `disease` is used by **every one
of the twenty** and matches 17.5% of the frame — non-discriminating because it is everywhere.
`vascular disease` is used by twelve topics and matches **0.3%** — non-discriminating because
it is nowhere. **A matcher that counts terms equally cannot tell either from a term with
df=4**, and reporting only the zeros — which a zero-count naturally surfaces — hides half the
defect.

**[INFERRED]** `mesh_v2`'s median df of **0** is the cleanest statement yet of why the MeSH
expansion was inert: the median added term matches nothing at all.

## 3.2 The proposal, priced — **NOT ADOPTED**

> A term with df > 10% of the frame contributes a match but does **not count** toward the
> `need` threshold. Only specific terms can satisfy a topic.

**[MEASURED]** applied to the literal axis without changing it:

    unchanged                                    15 of 20
    narrower but still fires                      2  colchicine-cvd-review, evolocumab-mixed
    would LOSE the axis entirely                  3  dabigatran-stroke,
                                                     evolocumab-dyslipidemia-review,
                                                     pitavastatin-auto-full-review

⭐ **The price is low and specific: all three are topics that carry NO counterpart today** —
`AMBIGUOUS`, `NO_CANDIDATE_RETRIEVED` and `CONDITION_MISMATCH` respectively. **[MEASURED]**
none of the six MATCHED topics loses its axis.

⛔ **Still not adopted.** A novel method goes in alongside the incumbent with regression
defined first, and these would be the criteria — **S1** no MATCHED topic loses its verified
set · **S2** the four judged CDSR counterparts survive as a hashed set · **S3** verified-stage
precision must not fall · **S4** the cutoff declared before the run and never tuned to the
result · **S5** both columns published.

⚠️ **S4 is the one at risk.** I chose 10% before reading the numbers, but I chose it knowing
`disease` sat at 17.5%. That is not a clean pre-registration and I am saying so rather than
claiming one.

---

# 4 INFECTIOUS DISEASE — the characterisation, finished

**[MEASURED]** The frozen rule carries over **better**: 24 of 62 drug-keyed and re-keyable
(39%) against cardiology's 17 of 56 (30%). Titles are worse (29% lost to F0+F1 vs 23%); the
drug/class step is better (32% vs 41%).

**[MEASURED]** The constraint is the frame, and **no infectious-disease frame exists**:

    cdsr_frame_cardiology.jsonl      1,216 rows   cardiology
    opencomp_frame_id.jsonl            664 rows   100% cardiology
    opencomp_frame_id24.jsonl          788 rows   100% cardiology
    opencomp_frame_id24pmid.jsonl      788 rows   100% cardiology
    opencomp_frame_all.jsonl         2,594 rows   100% cardiology

⚠️ **AND I ALMOST REPORTED THIS AS A PEER LANE MISLABELLING ITS FILES.** Read again,
`opencomp_frame_id24pmid` far more likely means **IDentifier, k≥24, keyed by PMID** — the
`_id` is not "infectious disease" at all, and the misreading was mine. **[MEASURED]** the
finding survives either way (there is no ID frame), but the accusation does not. ⭐ This is
*check the identity of what came back* applied to a filename, and I had the accusation
drafted before the check.

**[MEASURED]** `opencomp_frame_id.jsonl` is correctly **REFUSED** by `frame_contract` — it
has no `cd_base`, `record_kind` or `objectives_verbatim`. It is an open-comparator frame
(`pmcid`, `licence_open`, `eligible_comparator`, `prospero_registered`), closer in shape to
my OA lane than to the CDSR lane.

⇒ **[INFERRED] The route for ID is the open-access lane, which is frame-free by construction
and already carries its own contract** — not a new CDSR frame. That is a claim until run, and
it is not run here.
