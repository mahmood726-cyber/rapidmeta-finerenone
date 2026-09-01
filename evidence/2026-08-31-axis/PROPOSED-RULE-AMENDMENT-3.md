# Proposed amendment 3 to the frozen rule. **NOT APPLIED. Awaiting approval or refusal.**

    REF.rule    604ed6957a1adf17   the CURRENT frozen fingerprint
    REF.status  ⛔ PROPOSED ONLY. No file is changed by this document.
    REF.scope   68 topics with a resolved drug, across cardiology (56) and ID (62)

Both defects were found by carrying the frozen rule to a new specialty, which is what
carrying it there was for. Neither was fixed on discovery: amending a frozen rule mid-run is
what the freeze exists to prevent. This is the text, the justification, the **measured**
impact, and the controls each would need — so the decision is about a specific change rather
than a description of one.

---

# A1 — `F5_MODALITY_CLASS` catches antibodies and misses mRNA

## The defect **[MEASURED]**

    cvncov-covid19 -> ZORECIMERAN
        usan_stem            "-meran"
        usan_stem_definition "messenger RNA (mRNA)"
        class_is_modality    False          ⛔
        class phrases USED   ['messenger rna', 'mrna']

`-meran` names a **molecular modality**, exactly as `-mab` does. The re-key would search
Cochrane for `messenger rna` and `mrna` as though they were a drug class, reaching
mRNA-methodology reviews rather than COVID-vaccine reviews.

## The proposed text

`scripts/rekey20/chembl_resolve.py`, `MODALITY_STEMS` — add four entries:

    "messenger rna", "mrna", "small interfering rna", "sirna"

⚠️ **Deliberately NOT added:** `nanoparticle`, `conjugate`, `gene therapy`, `cell therapy`,
`viral vector`, `aptamer`. Each is defensible and none is exercised by the corpus, so adding
them would be widening a refusal on speculation. **A refusal that has never been exercised is
not a control, it is a guess.**

## Measured impact

| | |
|---|---|
| topics whose state changes | **1 of 68** — `cvncov-covid19`, `REKEYED` → `F5_MODALITY_CLASS` |
| counterparts lost | **0** — the topic carries none |
| topics with a modality-naming definition that the list still misses | **0** |

## Controls it would need

* **Positive:** `"messenger RNA (mRNA)"` must yield `F5_MODALITY_CLASS`.
* **Negative, and it is the one that matters:** `"enzyme inhibitors: antihyperlipidemics
  (HMG-CoA inhibitors)"` must still yield a class. `RULE-AMENDMENT.md` records that `enzyme`
  was once in this list and had to be **removed** — a mechanism class is not a modality.
  **This list has already over-refused once**, so any addition needs the negative side.
* **Sibling:** `"monoclonal antibodies"` must still fire, or the amendment has replaced a
  working branch rather than added one.

---

# A2 — a multi-stem record concatenates two unrelated classes

## The defect **[MEASURED]** — and it comes from ChEMBL, not from us

    usan_stem "-aril-; -mab"   ChEMBL's own field, two stems joined with "; "

`class_phrases` splits on `;`, so both halves become search terms.

    topic                    usan_stem       definition                                        outcome
    sarilumab-covid          -aril-; -mab    antiviral (arildone derivatives); monoclonal ab…   F5, by luck
    evinacumab-hofh          -mab; -vin-     monoclonal antibodies: fully human; VINCA ALKAL…   F5, by luck
    cab-prep-hiv-review      -vir; -vir      antivirals: RT translocation inhibitors;
                                             antivirals: integrase inhibitors                   ⛔ REKEYED
    raltegravir-hiv          -vir; -vir      same                                               ⛔ REKEYED

**[MEASURED] 4 of 68 resolved drugs carry a multi-stem record (5.9%).** `-vin-` on
**evinacumab** is a spurious infix — an ANGPTL3 antibody is not a vinca alkaloid.

⛔ **Two are re-keyed with a mechanism the drug does not have.** Cabotegravir is an integrase
inhibitor; the class terms include *reverse transcriptase translocation inhibitors*. The
shared parent (`antivirals`) is right, which is exactly why it looks harmless and is not.

⭐ **And the two that were caught were caught BY THE MODALITY FLAG, not by any rule about
multi-stem records.** A defect stopped by an unrelated check is a defect that will not be
stopped the next time the unrelated check does not apply.

## The proposed text

A new failure state in `rekey_rule.py`:

    F7_MULTI_STEM  the authority matched MORE THAN ONE stem for this molecule, so the
                   definition concatenates classes the drug may not all belong to. The
                   re-key REFUSES rather than choosing one.

and in `class_terms_for_drug`, before the F5 check:

    if ";" in (d.get("usan_stem") or ""):
        return [], "F7_MULTI_STEM"

⭐ **Refuse, do not disambiguate.** Picking the "right" stem needs pharmacology the rule does
not have; refusing costs two topics and states why. **The rule's job is to be honest about
what it cannot key, not to guess well.**

## Measured impact

| | |
|---|---|
| topics whose state changes | **4 of 68** |
| — already refused by F5 (no behaviour change) | 2 · `sarilumab-covid`, `evinacumab-hofh` |
| — **newly refused** | 2 · `cab-prep-hiv-review`, `raltegravir-hiv` |
| counterparts lost | **0** — neither newly-refused topic is in the twenty, and neither carries a judged counterpart |

## Controls it would need

* **Positive:** `usan_stem "-aril-; -mab"` → `F7_MULTI_STEM`.
* **Negative:** `usan_stem "-xaban"` (apixaban, single stem) must still be re-keyed. Without
  it, `return [], "F7_MULTI_STEM"` unconditionally passes the positive.
* **Sibling that distinguishes A2 from A1:** a single-stem *modality* must still return
  `F5_MODALITY_CLASS`, not `F7`, or the two states have merged.

---

# A3 — R2 protects review IDS where it should protect judged PAIRS

**Not the frozen rule** — a regression criterion I pre-registered and which then tripped
wrongly. Recorded here so it is amended in the same reviewed way.

**[MEASURED]** R2 reads *"CD004434, CD006681, CD014808, CD015003 must all survive"*. But
`olmesartan-htn`/CD004434 was judged **NOT_COUNTERPART** — it is the corpus's known false
positive, produced by the shared fragment `receptor antagonist`. **R2 scores losing it as a
regression when it is an improvement**, and it did so in the AACT run.

**Proposed:** R2 protects the topic–review **pairs** judged COUNTERPART, hashed as a set.
**Measured impact: the AACT verdict is unchanged** — colchicine/CD015003 is a genuine loss
and R3 trips twice regardless. This amendment changes no published conclusion.

---

# ⛔ THE OPERATIONAL CONSEQUENCE, WHICH IS BIGGER THAN EITHER FIX

## A2 changes `rule_fingerprint()`. A1 does not — and that is the problem.

`rule_fingerprint()` hashes `class_phrases()` and `norm()` over a fixed probe. Adding F7
changes `class_terms_for_drug`, so **the probe must gain a multi-stem entry** and every
artefact built under `604ed6957a1adf17` will be **REFUSED** by `assert_fingerprint` until
rebuilt — which is the machinery working as designed.

⛔ **A1 would change behaviour and NOT change the fingerprint**, because `class_is_modality`
is computed in `chembl_resolve` and **stored in the cached record**. Two consequences:

1. Nothing would refuse the stale artefacts. The drift would be silent — precisely the
   failure `rule_fingerprint` was built for after an amendment reached the controls and not
   the twenty.
2. **Cached ChEMBL records carry a stale `class_is_modality`**, so widening `MODALITY_STEMS`
   would not reach a single already-cached molecule. `sarilumab`'s cache entry holds
   `"class_is_modality": true` as a **stored derived value**.

⭐ **This is the same defect I found and fixed in `mesh_lookup` hours ago** — a cache of
DERIVED values is a frozen copy of a rule's output, so fixing the rule does not reach cached
rows. ⇒ **A1 must not be applied without also deriving `class_is_modality` on read (or
versioning the cache key) AND extending the fingerprint probe to cover it.** Applying A1
alone would produce a rule that behaves differently while claiming the same fingerprint,
which is worse than the defect it fixes.

---

# WHAT APPROVAL WOULD MEAN

    approve A1  -> requires ALSO: derive class_is_modality on read, version the ChEMBL cache
                   key, extend FINGERPRINT_PROBE, rebuild every artefact, re-run all plants
    approve A2  -> requires ALSO: extend FINGERPRINT_PROBE with a multi-stem entry, rebuild
                   every artefact, re-run all plants; 2 ID topics become refused
    approve A3  -> changes no published conclusion; applies to the NEXT pre-registration

**[INFERRED] My own recommendation, stated as one:** approve **A2 and A3**, and hold **A1**
until the cache-derivation fix ships with it, because A1's blast radius is one topic and its
silent-drift risk is the whole corpus. ⛔ **That is a recommendation, not an action.** Nothing
here is applied.
