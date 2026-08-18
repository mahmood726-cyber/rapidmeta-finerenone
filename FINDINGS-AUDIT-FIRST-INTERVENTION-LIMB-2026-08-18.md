# The triage's outcome limb is not enough — two of the six fail on the intervention

**Standalone file deliberately**, as the count-units lane did: `STATUS.md` and
`TOOLING-QUEUE.md` are being rewritten in this same working tree and appending to a
file another writer holds is how one of two edits disappears.

`scripts/audit_first_poolability_triage.py` said **POOL POSSIBLE** for six audit-first
cardiology topics, and said in its own "what this does not establish" that it tests
**the outcome limb only** and that *"participants and interventions still need a human
read"*. That read was done for the two topics that shared registrations. **Both fail,
and one fails badly.**

---

## OLMESARTAN_HTN — **every one of its three trials is a trial of a different drug**

Read from ClinicalTrials.gov, 2026-08-18, intervention lists verbatim:

| registration | brief title | interventions as registered |
|---|---|---|
| `NCT00846365` | *Efficacy and Safety of **Azilsartan Medoxomil** Plus Chlorthalidone…* | Azilsartan medoxomil and chlorthalidone; **Olmesartan** medoxomil-hydrochlorothiazide |
| `NCT01033071` | *Efficacy and Safety of **Azilsartan Medoxomil** and Chlorthalidone Compared to Olmesartan…* | Azilsartan medoxomil and chlorthalidone; **Olmesartan** medoxomil and hydrochlorothiazide |
| `NCT01599104` | *Efficacy and Safety of **LCZ696** in Comparison to Olmesartan in Japanese Patients…* | LCZ696; **Olmesartan**; Placebo |

**In all three, olmesartan is the COMPARATOR.** Two are azilsartan trials and one is a
sacubitril/valsartan (LCZ696) trial. **The topic contains no trial in which olmesartan
is the intervention.**

**The page was assembled from comparator-arm membership rather than from the
intervention under study.** A search that matches a drug name anywhere in a trial record
will do this, and nothing in the outcome limb can see it: all three genuinely register a
blood-pressure primary, so the outcome test passes and the topic is still not a topic.

**Verdict: NOT POOLABLE, on the intervention limb.** MECIR Box 10.10.a C62 requires
*"participants, interventions, comparisons and outcomes"* to be sufficiently similar;
here the interventions are azilsartan, azilsartan and LCZ696. **Handbook 6.5 §10.10.3:
*"Meta-analysis should only be considered when a group of studies is sufficiently
homogeneous in terms of participants, interventions and outcomes."***

**This is also a subject-identity defect, not only a synthesis one.** The topic's own
name asserts a drug that none of its trials tests. It is the ACS contamination pattern
in a third form: there the *prose* was foreign; here the *trial set* is foreign to the
title.

---

## AZILSARTAN_HTN — intervention coherent, **comparator is not**

| registration | intervention | comparator as registered |
|---|---|---|
| `NCT00591578` | Azilsartan medoxomil | **Valsartan** |
| `NCT00818883` | Azilsartan + chlorthalidone | **Azilsartan + hydrochlorothiazide** |
| `NCT00846365` | Azilsartan + chlorthalidone | **Olmesartan + hydrochlorothiazide** |
| `NCT01033071` | Azilsartan + chlorthalidone | **Olmesartan + hydrochlorothiazide** |

**All four are genuinely azilsartan-intervention trials** — that limb passes, and it is
worth saying so as plainly as the failure.

**But there are three different comparators across four trials**, and one of them
(`NCT00818883`) compares azilsartan against *itself* on a different partner diuretic,
which is a within-drug question and not a comparison against another agent at all.

**Verdict: NOT POOLABLE AS ONE PAIRWISE POOL.** C62's "comparisons" limb fails. A pool
here would average an azilsartan-vs-valsartan contrast, an azilsartan-vs-azilsartan
contrast and two azilsartan-vs-olmesartan contrasts into a single number — four trials,
three questions. **§11.2.2.1's transitivity requirement is the relevant frame and it is
not met by a pairwise pool.**

**What is left that IS coherent:** `NCT00846365` and `NCT01033071` share both
intervention and comparator (azilsartan + chlorthalidone versus olmesartan + HCTZ) and
both register a blood-pressure primary. **That is a defensible k=2 pool** — and it is a
*different topic* from "azilsartan in hypertension", so taking it means renaming the
question, which is Mahmood's call and not mine.

---

## What this changes about the triage

**The triage's six become at most four**, pending the same read on the remaining four
(MIPOMERSEN_HOFH, EDOXABAN_VTE, PITAVASTATIN, RIOCIGUAT_PAH). **The two that were
checked are the two the triage itself flagged as suspicious** — they shared
registrations — so this is not a random sample and the failure rate should not be
extrapolated to the other four. **Scope not measured beyond these two.**

**The instrument gap is real and is worth closing:** the triage reads registered
outcomes and does not read registered **interventions**, which are available in the same
API response (`protocolSection.armsInterventionsModule.interventions[].name`). Adding an
intervention-coherence limb would have caught OLMESARTAN_HTN without a human read.

**And the direction matters, per the conservative principle:** every failure found here
*removes* a topic rather than adding one. Nothing about this makes a result more
significant; it stops two pools from being built that would have averaged different
drugs.
