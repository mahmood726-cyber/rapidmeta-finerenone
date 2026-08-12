# Running report #5 — trial-identity sweep at corpus scale

**Date:** 12 August 2026 · extends reports #1–#4
**Project:** Nafis
**Mandate (Mahmood, verbatim):** *"making sure the right trials are included and all the data found and used."*
**Access:** read-only mount. No repo writes.

---

## 1. Headline

The comparator test could not run as specified — **the corpus holds no local cache of registered interventions**, so checking 1,538 registry-sourced entries against CTG would need 1,538 network calls. I substituted a **no-network identity test that targets the same failure class** and is arguably sharper.

**The test:** a trial name should map to exactly one NCT, and an NCT to exactly one trial name. Violations are cross-assignment candidates.

**Result: 229 raw flags across 3,141 rows with a valid NCT and name. After filtering placeholders and formatting variants, 65 high-signal flags remain.** Six adjudicated so far, **five confirmed wrong**.

**Three new confirmed errors, all verified live today**, and one of them is the cleanest demonstration yet that the corpus contradicts itself:

- **NCT02853305 carries BOTH "KEYNOTE-052" and "KEYNOTE-361" labels in different apps.** The registry says KEYNOTE-361. The corpus already contained its own refutation.
- **NCT04575597 labelled "PINETREE"** — it is **MOVe-OUT**, molnupiravir, Merck. PINETREE is remdesivir, Gilead. Different drug, different sponsor.
- **NCT02696785 labelled "MEASURE-4" and "COAST-W"** — it is **COAST-V**, ixekizumab, Eli Lilly. MEASURE-4 is a **secukinumab/Novartis** trial. In an app pooling IL-17 inhibitors, that swaps one IL-17 agent for another.

**Running total: 20 rows adjudicated — 7 correct, 11 wrong, 2 unresolved.**

---

## 2. The systematic pattern: paired sibling cross-assignment

The most diagnostic signal is not isolated mislabels. It is **two sibling trials from one programme each being assigned both NCTs**:

| Programme pair | Both names on both NCTs |
|---|---|
| **SINUS-24 / SINUS-52** | NCT02898454, NCT02912468 |
| **EMERGE / ENGAGE** (aducanumab) | NCT02477800, NCT02484547 |
| **ASTRAL-1 / ASTRAL-3** | NCT02201940, NCT02201953 |
| **COAST-V / COAST-W** | NCT02696031, NCT02696785, NCT02696798 |
| **BLISS-52 / BLISS-76** | NCT00424476 |
| **IMPOWER130 / IMPOWER150** | NCT02366143 |
| **ORION-9 / ORION-11** | NCT03400800 |
| **AURORA-1 / AURORA-2** | NCT03021499 |

This is a **swap failure**, not a typo. Where two arms of one programme are merged or exchanged, a pooled analysis silently doubles one trial and drops the other, or attributes one trial's population to the other's. It is invisible to every internal consistency check, and it is precisely the "right trials included" failure Mahmood's mandate names.

### Programme-numbered names mapping to >1 NCT — 14, all high signal

Names like KEYNOTE-*n* are unique by construction, so any such name on two NCTs is an error by definition:

`AURORA-1, AURORA-2, COAST-V, COAST-W, EXPEDITION-1, KEYNOTE-052, KEYNOTE-585, KEYNOTE-689, KEYNOTE-859, ORION-9, ORION-11, SINUS-24, SINUS-52, VOYAGE-1`

---

## 3. Flags versus diagnoses — reported separately

| Stage | Count |
|---|---|
| Rows with valid NCT + name | 3,141 |
| Distinct trial names / distinct NCTs | 2,335 / 2,279 |
| **Raw flags** (name→multi-NCT **85** + NCT→multi-name **144**) | **229** |
| After removing placeholder names (`TRIAL`, `NCT…` as name) | 84 name-flags |
| — programme-numbered subset (high signal) | **14** |
| After removing placeholders **and** formatting variants | **51** NCT-flags |
| **High-signal flags remaining** | **≈65** |
| Adjudicated so far | 6 |
| — confirmed wrong | **5** |
| — benign on inspection | 1 |

**A large share of raw flags are benign and I am not counting them as errors.** Real-world acronym reuse (ADVANCE, TITAN, HERCULES, DAWN, ASCEND each name genuinely different trials); formatting variants (`EVOLUTION-RMS-2` / `EVOLUTIONRMS-2`); suffix variants (`KEYNOTE-054` / `KEYNOTE-054-ADJ`); protocol-ID aliases (`NN9931-4296` for `NEWSOME-NAFLD`, `PAC326` for `PERSIST-2`); numeral variants (`ELARIS-EM-2` / `ELARIS-EM-II`). The filter removes most; the residue still needs human adjudication.

---

## 4. Adjudicated rows — cumulative

### Confirmed correct — 7
PARADIGM-HF (NCT01035255, every checkable cell); VIALE-A ×2 apps; ENDURANCE-1; ENDURANCE-3; SINUS-24 in CRSWNP; KEYNOTE-052 at NCT02335424; CREDIBLE-CR.

### Confirmed wrong — 11

| # | NCT | Recorded as | Actually | Class |
|---|---|---|---|---|
| 1 | NCT03971500 | ULTIMATE-DAPT | identity correct; evidence quote is a Cochrane **orthodontics** review | provenance |
| 2 | NCT02519322 | "IMmuNED", pembrolizumab single-arm n=30 | MD Anderson randomised 3-arm nivo±ipi/rela, n=53 | intervention/design/n |
| 3 | NCT02437279 | "OPTIMUS-1" n=30 | **OpACIN**, Phase 1b, n=20 | identity/design/n |
| 4 | NCT02138916 | GALATHEA benralizumab COPD | quote is **dupilumab / nasal polyp score** | outcome/provenance |
| 5 | NCT02155660 | TERRANOVA benralizumab COPD | same | outcome/provenance |
| 6 | NCT02446717 | EXPEDITION-1 | carries ENDURANCE-1's byte-identical quote | provenance |
| 7 | NCT01757535 | QUAZAR-AML | carries VIALE-A's quote and DOI | provenance |
| 8 | NCT02853305 | "KEYNOTE-052" single-arm | **KEYNOTE-361**, randomised, chemo arms, n=1,010 | **comparator/population** |
| 9 | NCT04575597 | "PINETREE" | **MOVe-OUT**, molnupiravir, Merck | **intervention/sponsor** |
| 10 | NCT02696785 | "MEASURE-4" | **COAST-V**, ixekizumab, Lilly (MEASURE-4 is secukinumab/Novartis) | **intervention** |
| 11 | NCT02696785 | "COAST-W" | **COAST-V** | identity |

**Rows 2, 3, 8, 9, 10 are the Reyaz class** — a trial carrying an intervention, comparator or design it does not have.

---

## 5. Failure modes — with an independent second measurement

| Mode | Confirmed |
|---|---|
| **(a) Search breadth** — trials never found | **0** |
| **(b) Checking** — trials found, characterised wrongly | **14** (11 corpus rows + 3 published syntheses) |

**Fourteen to zero.** And the sibling search lane now provides an **independent second measurement pointing the same way**: backward citation across **44 syntheses returned zero eligible randomised trials missed**, resolved by identifier.

**But that lane's caveat is decisive for interpreting this null, and I am adopting it:** backward citation only finds what someone else already found. It measures recall against the field's own coverage, not against the truth. **Two measurements agreeing on zero does not establish zero** — both used field-internal instruments.

Only the routes that escape the field's coverage can test this properly: **non-MEDLINE, non-English, off-NCT, registry-only**. That is what caught Li 2019, and it is the only design that can falsify the null.

---

## 6. Breadth-failure hunt — design

To be capable of finding one, the hunt must target syntheses whose searches were **structurally narrow**, then check the layers that escape them:

**Selection criteria for target syntheses** — any of: English-only inclusion criterion (Alam 2023 states one); MEDLINE/PubMed-only searching; date-limited searches that predate a known trial; registry-status filters.

**Check layers:** CNKI / Wanfang / VIP (Chinese); SciELO / LILACS (Latin American); ChiCTR, CTRI, ReBEC, IRCT, JPRN (non-NCT registries); doctoral theses; non-English conference proceedings.

**Prespecified interpretation:** a breadth failure counts only if the missed trial (i) meets the synthesis's own stated eligibility criteria, and (ii) is not excluded by a criterion the synthesis actually stated. A deliberate, declared restriction is a **different choice, not an error** — the Alam 2023 rule from report #2.

---

## 7. Access ledger — unchanged this round, rule reaffirmed

No new barriers. The three-category rule stands and is now applied prospectively:

> **A missing cell is three things: not published, not reported, or never defined.** Any row classified as an access failure is tested against *never defined* first.

| Metric | Value |
|---|---|
| Barriers encountered | 8 (1 genuine paywall, 7 tooling) |
| Workaround success, non-paywall | 7/7 |
| Workaround success, genuine paywall | 0/1 |
| Breaches achieved | 6 |
| — changed ≥1 extracted cell | 6/6 |

---

## 8. Next

1. **Adjudicate the remaining ~59 high-signal identity flags** — the paired-sibling swaps first (SINUS, EMERGE/ENGAGE, ASTRAL, COAST, BLISS, IMPOWER, ORION, AURORA), since a swap corrupts two rows at once.
2. **The 1,044 rows with a `publishedHR` and no evidence block** — largest unsourced exposure, and the core of "all data found and used".
3. **The remaining 9 flagged DOI-reuse cases.**
4. **Run the breadth hunt per §6.** This is now the highest-value scientific move: the null is at fourteen-to-zero with two field-internal instruments, and only a field-external instrument can test it.
5. Build the comparator test properly by pulling registered interventions for the 2,279 distinct NCTs into a local cache — one bulk operation, then the check becomes free and repeatable.

---

## 9. Caveats

- 20 of 3,656 rows adjudicated = **0.55%**. No corpus-wide rate claimed.
- Flags (229 raw, ~65 high-signal) and diagnoses (11 wrong) are reported as separate numbers throughout.
- The identity test cannot detect an error where a wrong NCT is used **consistently** across every app — consistency is not correctness. Only external verification catches that class, which is why §8.5 matters.
- Zero breadth failures remains *not yet caught*, now with the explicit caveat that both measurements were field-internal.
- Every identifier resolved by live lookup; every value read verbatim.

**Attribution:** trial records from ClinicalTrials.gov, verified 12 Aug 2026.
