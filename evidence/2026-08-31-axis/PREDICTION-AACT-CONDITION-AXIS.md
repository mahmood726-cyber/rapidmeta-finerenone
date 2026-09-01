# Prediction: an AACT-sourced condition axis. Written before any condition row was read.

    REF.rule       604ed6957a1adf17   ⛔ FROZEN
    REF.frame      a0d44914a5ef99e3   1,186 CDSR cardiology reviews
    REF.aact       folder 2026-08-30  ⛔ DATA DATE 2026-08-27
    REF.guard      F:/AACT-storage/aact_snapshot_guard.py

⭐ **THE DATA DATE, NOT THE FOLDER NAME.** The snapshot guard records that folder
`2026-04-12` holds data ending `2026-04-08` — *"folder names are labels; the data is the
fact"*. Folder `2026-08-30` holds data to **2026-08-27**, and that is the version every
number below is a claim about. ⚠️ This is the identity-of-what-came-back rule again, applied
to a snapshot: citing the label instead of the data would misdate every result by three days.

---

## 1 WHY THIS MIGHT MOVE THE CEILING **[MEASURED precondition]**

The ceiling of 18 is set by two topics whose `condition_span` is null because their TITLES
carry no condition connective:

    apixaban-vte-prophylaxis   5 NCTs   NCT00371683, NCT00423319, NCT00452530, NCT00457002, …
    evolocumab-ascvd-auto2     3 NCTs   NCT01652703, NCT03060577, NCT04992065

**Both carry NCT ids.** AACT holds `conditions` and `browse_conditions` as TYPED ROWS keyed
by `nct_id`, independent of any title. ⇒ **[INFERRED]** a condition axis sourced from the
registry can exist where a title-parsed one cannot.

## 2 THE PREDICTION

| | predicted |
|---|---|
| both blocked topics get a NON-EMPTY condition axis | **yes** |
| ceiling moves | **18 → 20** |
| topics with a judged counterpart | **UNCHANGED at 10** |
| topics whose AACT axis exceeds 25% of the frame (R3) | **at least 1** |
| topics where the AACT axis is NARROWER than the title axis | **at least 2** |

⭐ **The ceiling and the count are different claims and I expect them to diverge.** A
reachable topic is not a topic with a counterpart, and last night's measurement says the
judging stage — not retrieval — is what is unreliable. **A ceiling that moves while the
count does not is the honest expected result.**

⚠️ **The specific risk: AACT conditions are registry vocabulary and skew BROAD.**
`browse_conditions` is MeSH-derived, so terms like *Cardiovascular Diseases* or *Thrombosis*
are likely, and those are the promiscuous end — the same failure that made
`bosentan-pah-children` jump 14 → 99 rows under MeSH broadening. R3 exists for that.

## 3 ⛔ REGRESSION, DEFINED BEFORE THE FIRST QUERY

    R1  no topic that is MATCHED on the incumbent title axis may become unmatched
    R2  CD004434, CD006681, CD014808, CD015003 must all survive, as a hashed SET
    R3  no topic's AACT condition axis may exceed 25% of the frame (297 of 1,186)
    R4  NEW, PROVENANCE: every condition term must trace to a typed AACT row for an NCT the
        OBJECT ITSELF includes. No term may be invented, inferred, or carried from a title.
    R5  ALONGSIDE. Both columns published per topic; the incumbent axis is not removed.

⭐ **R4 is the one this source makes possible and MeSH did not.** A registry row has an
`nct_id` and a source table, so every term carries a provenance that can be checked rather
than trusted — which is exactly what was missing when an unverified MeSH record expanded
`supraventricular` into a ventricular arrhythmia.

## 4 WHICH WAY I EXPECT TO MISS

My last several predictions missed low after over-correcting from a long optimistic run, so
I am predicting from a stated mechanism rather than a direction.

**[INFERRED]** The thing I am least sure of is whether AACT's conditions for these two
objects describe the REVIEW's question or the TRIAL's registration. A trial registered under
*Arthroplasty, Replacement, Hip* is a thromboprophylaxis trial whose registered condition is
the surgery, not the clot — in which case the axis is non-empty and WRONG, which is worse
than empty and would show up as a topic that suddenly matches orthopaedic reviews. **If that
happens it is a finding about the source, and R4's provenance trail is what will make it
visible rather than plausible.**
