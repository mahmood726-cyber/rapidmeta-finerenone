# HANDOVER — the candidate pool for a full-standard page, and why the arithmetic changes

**To:** the rebuild / ranking lane (owner of `tabs_with_content`).
**From:** the counterpart-identification lane.
**Do not infer any of this — it is stated because nobody else has measured it.**

    REF.commits  73cdb2442 (mapping) · 2ef7b4033 (specificity) · 55c901d72 (ID probe)
    REF.data     evidence/2026-08-31-axis/counterpart_page_map.json

---

# ⛔ THE HEADLINE FOR YOU: THE ELEVEN-PAGE ARITHMETIC IS WRONG

A page at full moat standard has to be **scored against a counterpart**. The pool is therefore
not "our pages" — it is **the topics that carry a judged counterpart**, and three facts about
that pool change the count:

1. **`PAGE_MAP.json` declares NOTHING for any of the ten.** Page identity below comes from
   the disk alone. If your lane resolves pages through `PAGE_MAP`, it will resolve **zero**
   of this pool.
2. **Six of the ten have MORE THAN ONE delivered page.** A topic with several pages does not
   have "a page" to score — someone must choose, and the choice is not ours to make.
3. ⛔ **`etripamil-psvt` has a counterpart and NO PAGE AT ALL.** It cannot reach moat standard
   until a page exists. It is the only topic in the pool whose counterpart is a
   textbook-clean match (*"The Efficacy and Safety of Etripamil Nasal Spray for Acute
   Paroxysmal Supraventricular Tachycardia"*), so it is simultaneously the best-evidenced
   candidate and the one with nothing to score.

---

# THE POOL — topic → page(s) → counterpart

| topic | page(s) on disk | counterpart | verified against |
|---|---|---|---|
| bosentan-pah | `BOSENTAN_PAH_AUTO_FULL_REVIEW` **·** `BOSENTAN_PAH_AUTO_REVIEW` | CD004434 | Cochrane objectives |
| bosentan-pah-children | `BOSENTAN_PAH_CHILDREN_REVIEW` | CD004434 | Cochrane objectives |
| bosentan-pah-monotherapy | `BOSENTAN_PAH_MONOTHERAPY_REVIEW` | CD004434 | Cochrane objectives |
| colchicine-cvd-review | `COLCHICINE_CVD_REVIEW` | CD014808 · CD015003 | Cochrane objectives |
| enoxaparin-vte | `ENOXAPARIN_VTE_AUTO_FULL_REVIEW` **·** `ENOXAPARIN_VTE_AUTO_REVIEW` | CD006681 | Cochrane objectives |
| **etripamil-psvt** | ⛔ **NONE** | PMC10328856 | abstract |
| mavacamten-hcm-review | `MAVACAMTEN_HCM_REVIEW` | 7 OA reviews | abstract |
| riociguat-pah | `RIOCIGUAT_PAH_AUTO_FULL_REVIEW` **·** `RIOCIGUAT_PAH_AUTO_REVIEW` | PMC13124407 | abstract |
| selexipag-pah | `SELEXIPAG_PAH_AUTO_FULL_REVIEW` **·** `SELEXIPAG_PAH_AUTO_REVIEW` | PMC12554579 | abstract |
| sotatercept-pah | `SOTATERCEPT_PAH_AUTO_FULL_REVIEW` **·** `_AUTO_REVIEW` **·** `_REVIEW` | 3 OA reviews | abstract |

    TOPICS 10 · comparators 6 objectives-verified + 13 abstract-verified

⚠️ **The three bosentan topics share ONE review (CD004434).** They are one question under
three names. Counting them as three independently-evidenced candidates inflates the pool.
**Independent counterpart reviews behind the whole pool: 4 Cochrane + 13 open-access.**

⚠️ **Do NOT pool the two comparator kinds into one quality claim.** A CDSR counterpart was
verified against a Cochrane objectives statement (one or two sentences); an open-access one
against an abstract (~250 words). Substituting one for the other moved `MATCHED` from 6/20 to
16/20 with no rule change. They are different measurements under one word.

---

# ⛔ WHAT THIS POOL IS **NOT**

**Infectious disease does not expand it.** The open-access lane retrieved for all 24
drug-keyed ID topics and 23 reached `MATCHED` — **and that is an artefact.** Measured: the
bare word `antibiotic` returns **6,955** open-access systematic reviews while `plazomicin`
returns **13**; the class word did **96–100%** of the retrieval on the class-dominated topics.
**Nothing in the ID run was judged and no ID topic has a counterpart.**

⇒ **Never quote "23 of 24 ID topics matched" without "and `antibiotic` did 99% of the
retrieving".** It is the same shape as our cardiology `receptor antagonist` case: the
mechanism producing the best matches is the mechanism producing the false positives.

---

# WHAT WE ARE NOT DOING, SO YOU KNOW IT IS YOURS

⛔ **We are not ranking.** `tabs_with_content` is your instrument and it is the only content
detector worth trusting; a ranking from this side would be a second opinion from the wrong
tool.

⛔ **We are not choosing which of the multiple pages is "the" page.** That needs the content
detector, not the counterpart record.

**What we will do on request:** re-run the counterpart identification for any topic you
nominate, and adjudicate additional pairs — with the caveat that adjudication is measured
**unstable** (27% of labels change under a rubric tightening that can only refuse; ~6.5% on a
straight repeat with no change at all). Treat any single judged pair as one sample.
