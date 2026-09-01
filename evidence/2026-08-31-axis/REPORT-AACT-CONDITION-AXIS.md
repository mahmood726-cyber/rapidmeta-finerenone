# A registry-sourced condition axis. **The ceiling moves 18 → 20. The axis is NOT adopted.**

    REF.rule        604ed6957a1adf17   ⛔ FROZEN
    REF.frame       a0d44914a5ef99e3   1,186 CDSR cardiology reviews
    REF.aact folder 2026-08-30
    REF.AACT DATA   2026-08-27         ⛔ the date every claim here is about
    REF.pre         PREDICTION-AACT-CONDITION-AXIS.md, written before a row was read

⭐ **The data date, not the folder name.** `aact_snapshot_guard` records that folder
`2026-04-12` holds data ending `2026-04-08`. Folder `2026-08-30` ends **2026-08-27**. Citing
the label would misdate every claim by three days — the identity-of-what-came-back rule,
applied to a snapshot.

**[MEASURED]** `conditions.txt` 1,079,141 rows · `browse_conditions.txt` 4,356,796 rows ·
599,738 NCTs carrying at least one condition row.

---

# 1 ⭐ THE CEILING MOVES: 18 → 20 **[MEASURED]**

Both previously-unreachable topics now carry a condition axis, and **R4 provenance holds —
zero unresolved NCTs across all twenty**:

    apixaban-vte-prophylaxis   5 NCTs, all in the snapshot   25 terms   184 rows (16%)
       deep vein thrombosi   <- Deep Vein Thrombosis
       pulmonary embolism    <- Pulmonary Embolism
       embolism and thrombosi <- Embolism and Thrombosis

    evolocumab-ascvd-auto2     3 NCTs, all in the snapshot   47 terms   243 rows (20%)
       hypercholesterolemia  <- Familial Hypercholesterolemia; Hypercholesterolemia
       hyperlipidemia        <- Hyperlipidemias
       lipid metabolism disorder <- Lipid Metabolism Disorders

⇒ **A registry row exists where a parsed title does not.** These two were never a literature
gap; they were a string-parsing gap, and AACT closes it.

⭐ **The risk I named in advance did NOT materialise, and I checked rather than assumed.** I
predicted a thromboprophylaxis trial might be registered under *the surgery* rather than *the
clot*, giving a non-empty but WRONG axis. `apixaban-vte-prophylaxis` returns DVT, pulmonary
embolism and thrombosis — the clot. The provenance trail is what made that checkable.

---

# 2 ⛔ THE VERDICT: NOT ADOPTED

    R2  colchicine-cvd-review loses CD015003          <- a REAL counterpart lost
    R2  olmesartan-htn loses CD004434                 <- see §2.1, this trip is SPURIOUS
    R3  colchicine-cvd-review axis is 27% of the frame
    R3  warfarin-af axis is 26% of the frame

⇒ **The incumbent title axis stands.**

## 2.1 ⚠️ One of my own regression criteria is defective, and I am naming it rather than fixing it

**R2 as written protects four review ids globally: "CD004434, CD006681, CD014808, CD015003
must survive."** But `olmesartan-htn`/CD004434 was **judged NOT_COUNTERPART** — it is the
corpus's known false positive, the one produced by the shared fragment `receptor antagonist`.
**Losing it is an improvement, and R2 scores it as a regression.**

⇒ R2 should protect the topic–review **PAIRS** that were judged COUNTERPART, not a set of
review ids independent of topic. **[MEASURED]** the verdict is unchanged either way:
colchicine/CD015003 is a genuine loss and R3 trips twice regardless.

⛔ I am not rewriting R2 now. It was pre-registered, it tripped, and amending a criterion
after seeing which cases it caught is the failure this project keeps paying for. The defect
is recorded for the next pre-registration.

---

# 3 THE DEFECT I DID NOT PREDICT: a generic word promoted to a condition

**[MEASURED]** 568 AACT terms, 365 live, 203 dead. The single highest-hitting term:

    disease   207 rows   — and it is a term for EVERY ONE of the twenty topics

`terms_from` splits multi-word registry names into content words, so *Cardiovascular
Diseases* contributes `disease`, *Lipid Metabolism Disorders* contributes `disorder`. **A
generic medical noun becomes a condition term.**

⭐ **The tell is that it is identical across all twenty topics.** A condition term that every
topic shares is not distinguishing anything — the same shape as MeSH's `prevention → control`
(47 rows) and the reason `colchicine` and `warfarin` breach 25%.

**[INFERRED]** This is the promiscuity end of the same axis defect measured all night: a
condition vocabulary with no notion of specificity fails toward matching everything, exactly
as a vocabulary with no synonyms fails toward matching nothing.

---

# 4 THE PREDICTION, SCORED

| prediction | result | |
|---|---|---|
| both blocked topics get a non-empty axis | **yes**, 184 and 243 rows | **HIT** |
| ceiling moves 18 → 20 | **yes** | **HIT** |
| topics with a judged counterpart unchanged at 10 | **unchanged** | **HIT** |
| ≥1 topic exceeds 25% of the frame (R3) | **2** — colchicine 27%, warfarin 26% | **HIT** |
| ≥2 topics where the AACT axis is NARROWER | **0 — every topic is wider** | **MISS** |
| named risk: registered under the surgery, not the clot | did not materialise | correctly checked |

⭐ **The miss is informative.** I expected registry conditions to be sometimes narrower than
a title phrase. They are **uniformly wider**, because a trial registers several conditions
and each contributes both its phrase and its words. The direction was one-way and I had
modelled it as two-way.

---

# 5 WHAT SHIPS

**Ships:** `aact_condition_axis.py`, and the finding that the ceiling is **20, not 18**.

**Does not ship:** the AACT condition axis as a replacement. R2 and R3 tripped.

**[INFERRED] The next build is not a third source.** Three condition axes have now been
measured — literal title words, MeSH-expanded, registry-sourced — and all three fail in the
same direction the frame is sensitive to: none has a notion of **term specificity**. A term
matching 207 of 1,186 reviews should not count the same as one matching 4, and no source
fixes that because it is a property of the *matcher*, not the vocabulary.

**Still open:** infectious disease, untouched; replication in the judging funnel, named and
unbuilt pending pre-registration.
