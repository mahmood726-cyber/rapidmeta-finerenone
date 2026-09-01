# Does the lane carry over to infectious disease? **Yes — better than baseline. I predicted wrong.**

    REF.rule   604ed6957a1adf17   ⛔ FROZEN. Byte-identical to the cardiology run.
    REF.base   pool.json, 56 cardiology topics
    REF.pre    PREDICTION-INFECTIOUS-DISEASE.md, written before the rule touched a topic

---

# 1 THE RESULT **[MEASURED]** — `python scripts/rekey20/id_pool.py`

| state | cardiology | infectious disease |
|---|---|---|
| **DRUG_KEYED_AND_REKEYABLE** | 17 · **30%** | 24 · **39%** |
| F1_NO_CONDITION | 7 · 12% | 11 · 18% |
| F3_MULTI_DRUG | 6 · 11% | 8 · 13% |
| F0_NO_TITLE | 6 · 11% | 7 · 11% |
| F2_NO_DRUG | 6 · 11% | 7 · 11% |
| F5_MODALITY_CLASS | 6 · 11% | 4 · 6% |
| F4_NO_CLASS | 4 · 7% | 1 · 2% |
| F6_CIRCULAR_CLASS | 1 · 2% | 0 |
| **total** | 56 | 62 |

**The claim survives: the lane carries over unchanged, and carries MORE.** 39% against 30%.

## 1.1 ⭐ The decomposition was right even though the headline was wrong

    lost to the TITLE   (F0+F1) : ID 18 (29%)   cardiology 13 (23%)   ID is WORSE
    lost to the DRUG/CLASS step : ID 20 (32%)   cardiology 23 (41%)   ID is BETTER

I read the ID titles before running and predicted they were worse. **They are.** What I got
wrong was assuming that term would dominate: the drug/class step improved by 9 points while
the titles worsened by 6, so the net moved the other way.

⇒ **[INFERRED] I modelled one term of a two-term change** — the same error as the AACT run,
where I modelled a one-way effect (registry conditions are wider) as two-way. That is now the
shape of my last two misses, and it is more useful than "predict lower".

---

# 2 ⛔ TWO REAL DEFECTS IN THE FROZEN RULE, FOUND BY CARRYING IT TO A NEW SPECIALTY

## 2.1 `F5_MODALITY_CLASS` is incomplete: it catches antibodies and misses mRNA

    cvncov-covid19  ->  ZORECIMERAN
        usan_stem            : -meran
        usan_stem_definition : messenger RNA (mRNA)
        class_is_modality    : False          ⛔ WRONG
        class phrases USED   : ['messenger rna', 'mrna']

`-meran` names a **molecular modality**, exactly as `-mab` does. F5 exists to refuse this —
*"the stem names a MOLECULAR MODALITY, not a therapeutic class"* — and it fires correctly for
`bamlanivimab`, `bezlotoxumab` and `nirsevimab` (`monoclonal antibodies`). It does not fire
for mRNA, because `class_is_modality` is False in the record.

⇒ **The re-key for a COVID vaccine would search Cochrane for `messenger rna` and `mrna` as
though they were a drug class**, reaching mRNA-methodology reviews rather than vaccine
reviews. Same identity family as `SGLT2`→the protein: **a modality wearing a class's clothes.**

⭐ **This is the check I pre-registered, firing.** I wrote in advance: *"a vaccine that
RESOLVES to some molecule is the identity defect."* One of seven vaccine-shaped topics
resolved, and it is the defect. The other six landed in `F2_NO_DRUG` or `F1_NO_CONDITION`,
which is correct — a vaccine is not a molecule with a therapeutic-class stem.

## 2.2 A stem collision produces a two-headed class

    sarilumab  ->  "antiviral (arildone derivatives); monoclonal antibodies"

Sarilumab is an interleukin-6 receptor antibody. The definition splices an **antiviral** stem
onto the antibody stem — two unrelated classes in one string. It was refused by F5 anyway, so
it costs nothing here, **but the refusal was for the right reason by luck**: had the antiviral
half appeared alone the topic would have been re-keyed as an antiviral.

⛔ **NEITHER IS FIXED HERE.** The rule is frozen, and patching it after seeing which cases it
missed is the failure this project keeps paying for. Both are recorded for a pre-registered
amendment with its own controls.

---

# 3 THE PREDICTION, SCORED — mostly missed, and HIGH this time

| prediction | result | |
|---|---|---|
| DRUG_KEYED 12–22% | **39%** | **MISS, high** |
| topics carried 8–14 of 62 | **24** | **MISS, high** |
| "the lane does NOT carry over unchanged" | it carries over **better** | **MISS** |
| titles are the losing side, worse than cardiology | **29% vs 23%** | **HIT** |
| F1_NO_CONDITION ≥ 20% | **18%** | near-miss, low |
| F3_MULTI_DRUG ≥ 12% | **13%** | **HIT** |
| F0_NO_TITLE ≥ 15% | **11%** | **MISS** |
| F5_MODALITY_CLASS higher than 11% | **6%** | **MISS** |
| a vaccine resolving to a molecule = identity defect | **1 of 7, and it is one** | **HIT** |

⭐ **I named this exact failure in advance and then made it anyway:** *"my recent misses have
been low, so the symmetric risk is that I am now over-correcting into pessimism about my own
lane… ID drug names are highly distinctive and ChEMBL may resolve them more reliably… If that
happens, the claim I doubted is the one that survives."*

**It happened. The claim I doubted survived.** Writing the escape hatch into the
pre-registration did not stop the miss — but it did make the miss legible instead of
embarrassing, and it is why this report can say *which* term I mis-modelled rather than just
*that* I was wrong.

---

# 4 WHAT THIS MEANS FOR THE FRAME

**[MEASURED]** 24 ID topics are drug-keyed and re-keyable — more than the 17 cardiology
topics that produced the twenty. **[INFERRED]** The lane's constraint on a second specialty
is therefore not the rule; it is the **frame**. The CDSR frame is cardiology-only, so an ID
run needs either a CDSR infectious-disease frame or the open-access lane, which is
frame-free by construction and already carries its own contract.

**Not run here, and not claimed:** no ID counterpart has been retrieved or judged. This
measures only whether the rule survives the move, and it does.
