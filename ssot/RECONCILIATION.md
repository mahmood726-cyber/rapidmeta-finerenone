# Published-meta reconciliation

For each k>1 build: find the best published review in the exact area, diff the
trial list, and reconcile the estimate — decomposing any gap into (a) our bug,
(b) different trial set, (c) different method or estimand.

---

## COVID19_VACCINES vs Cochrane

**Reference:** Graña C et al. *Efficacy and safety of COVID-19 vaccines.*
Cochrane Database of Systematic Reviews 2022. PMID 36473651,
doi 10.1002/14651858.CD015477. Full text read from PMC.

### Trial-list diff

| our trial | in Cochrane? |
|---|---|
| NCT04530396 Gam-COVID-Vac | **yes** |
| NCT04652102 CVnCoV | **yes** |
| NCT04510207 BBIBP-CorV | **yes** |
| NCT04324606 (we removed) | yes — see below |

**Nothing we carry is absent from the reference review.** No contamination
survived into our core.

On the trial we removed: Cochrane includes NCT04324606 **and** NCT04400838 as
**separate studies**. That confirms the diagnosis rather than contradicting it —
our defect was never that the trial is illegitimate, it was that we attached
Voysey's *pooled* counts across four trials to one registration. Cochrane's
ChAdOx1 figure is drawn from **2 RCTs**, for exactly this reason.

They cite 271 registrations we lack, but that is not a like-for-like gap: their
review covers *all* COVID-19 vaccines and its citation list includes ongoing and
excluded studies. Our object repairs one contaminated app; it is not an
independent systematic review and must not be read as one.

### Estimate reconciliation

| vaccine | our crude RR (VE) | Cochrane VE (95% CI) | gap |
|---|---|---|---|
| BBIBP-CorV | 0.2209 (**77.9%**) | **78.10%** (64.80–86.30) | 0.2 pp |
| Gam-COVID-Vac | 0.0845 (**91.5%**) | **91.10%** (83.80–95.10) | 0.4 pp |
| CVnCoV | 0.5439 (**45.6%**) | **48.20%** (31.70–60.90) | 2.6 pp |

Two reconcile to within rounding. The CVnCoV gap decomposes cleanly as **(c)
method**: that trial analysed its outcome on **person-time**, which our crude
count-based risk ratio ignores. The object already records this. Denominators
match exactly — 25,062 on both sides.

### RESOLVED — the app now does what the reference review does

The object was reshaped to per-vaccine and the cross-vaccine pooled estimate was
removed entirely, so the reconciliation is now direct:

| vaccine | our crude RR (VE) | Cochrane VE (95% CI) | gap |
|---|---|---|---|
| Gam-COVID-Vac | 0.0845 (**91.5%**) | **91.10%** (83.80–95.10) | +0.5 pp |
| BBIBP-CorV | 0.2209 (**77.9%**) | **78.10%** (64.80–86.30) | −0.2 pp |
| CVnCoV | 0.5439 (**45.6%**) | **48.20%** (31.70–60.90) | −2.6 pp |

Two agree to within half a point. The CVnCoV gap decomposes as **(c) method** —
that trial analysed on person-time, which a crude risk ratio ignores — and is
recorded in the object rather than smoothed away.

### The finding that drove the reshape

**Cochrane never pools across vaccines.** It reports efficacy separately for
BNT162b2, mRNA-1273, ChAdOx1, Ad26.COV2.S, BBIBP-CorV, BBV152, NVX-CoV2373 and
CoronaVac. There is no counterpart in the reference standard to the single
pooled number the source app computes across vaccine platforms.

That was a **(c) estimand** difference in which the published review was right
and the app was the anomaly. Both adversary families reached the same verdict
independently — "absolutely not defensible as a clinical estimate", "clinically
non-estimable as one effect". The correct treatment was not a better pooled
number but **no pooled number**, and that is what the object now carries. The
caveat that used to sit beside the number is gone with it: a figure that should
not be computed is not repaired by a warning printed next to it.

---

## ALIROCUMAB vs Cochrane

**Reference:** Schmidt AF et al. *PCSK9 monoclonal antibodies for the primary and
secondary prevention of cardiovascular disease.* Cochrane Database of Systematic
Reviews 2020. PMID 33078867, doi 10.1002/14651858.CD011748.pub3. Abstract read;
PMC returned metadata only, so the included-study table could not be diffed
trial by trial. That limit is stated rather than worked around.

### Trial-list diff

They include **24 studies, 18 randomising alirocumab**; we carry **6**.

This is **(b) a different trial set**, and the reason is scope rather than error:
our object repairs the citation list of one app. It is not a systematic review of
alirocumab, and the further alirocumab RCTs are legitimate recovery candidates
for anyone who wants one.

### Estimate reconciliation — not possible, and that is the finding

**No comparable pooled estimate exists.** Cochrane pools *clinical events* — CVD
(OR 0.87, 0.80–0.94), mortality (OR 0.83, 0.72–0.96), MI (OR 0.86, 0.79–0.94),
stroke (OR 0.73, 0.58–0.91). We pool **percent change in LDL cholesterol**. A
**(c)** estimand difference so complete that no number is comparable.

Worth stating plainly: the reference review answers *does this drug prevent
events*; the app answers *how much does it lower a lipid*. The second is a
surrogate for the first, and an app reporting only the surrogate should say so.

### Trial recovered — by the gate, not by this diff

`NCT01507831` posts LDL-C at week 24 as a **secondary** outcome. An earlier build
excluded it after reading primary outcomes only. **k rose 5 → 6**; the pooled
estimate moved from **−52.58 (−60.61 to −44.56)** to **−54.66 (−60.75 to
−48.56)**, τ² 70.65 → 47.42. The superseded figure is retained in the object.

---

## PREVNAR15 vs Matsumoto 2026 — the reconciliation that found the defect

**Reference:** Matsumoto Y et al. *Comparative efficacy and safety of 15-valent
and 13-valent pneumococcal conjugate vaccines alone and in combination with the
23-valent polysaccharide vaccine.* Biol Pharm Bull 2026;49:1073–86.
PMID 42419969, doi 10.1248/bpb.b26-00019. Full text retrieved and read.
It pools **6 RCTs, n = 6460**, in **adults**, and reports each solicited symptom
separately.

### This diff did not confirm the build. It broke it.

The first build of this object reported "any solicited injection-site adverse
event", **RR 1.0525 (0.9530–1.1624)** — no difference. The reference reports the
opposite for pain: **RR 1.20 (1.11–1.29)**, significant. Chasing that gap found
the cause, and it was ours.

The registry does not post one injection-site number. It posts a multi-category
outcome — erythema, induration, pain, swelling — and the extractor took the
**last** row. That is **swelling** in six of the seven trials. The object
published swelling under the name of a composite.

The reference is what proves the diagnosis: it finds **swelling and erythema do
not differ** while **pain does**. Our defective figure was not a wrong number.
It was the *right* number for swelling, carrying the wrong name.

Every one of those cells was arithmetically correct, resolved to a real registry
row, and cited a real posted outcome title. **The validator passed it 16/16.**
No internal-consistency check can see a correct value bound to the wrong row.

Two further defects surfaced in the same pass, both invisible in the object:
* **arms dropped without disclosure** — NCT02547649 randomised two V114
  formulations against one shared control and only the first was used;
  NCT03848065 has subcutaneous and intramuscular V114 arms and one was dropped.
* **wrong arms entirely** — NCT03620162 is a five-group interchangeability trial
  of mixed schedules, and the build used **Group 2** (three doses of Prevnar 13
  then one of V114) as the "treatment" arm. The only clean contrast is Group 5
  (four doses of V114) against Group 1 (four doses of Prevnar 13).

### Trial-list diff, after rebuild

| our trial | population | in the reference? |
|---|---|---|
| NCT03950622 | adults ≥50 | **yes** — PNEU-AGE, confirmed by the registry acronym field |
| NCT03547167 | adults 18–49 | **yes** — matches PNEU-DAY on age band and design; the registry carries no acronym, so this is an inference and is marked as one |
| NCT02547649 | adults ≥50 | no |
| NCT03620162 · NCT03692871 · NCT03848065 · NCT03921424 | infants and children | **cannot be** — the reference is restricted to adults |

The reference's remaining trials (Ermlich 2018, PNEU-PATH, PNEU-TRUE, and an
adults-with-HIV trial) are absent from ours. This is **(b) a different trial
set**, by scope: our object repairs one app's citation list and is not a
systematic review.

### Estimate reconciliation, after rebuild

| comparison | k | RR (95% CI) | I² |
|---|---|---|---|
| **ours, adults only** | 3 | **1.1696 (1.0677–1.2812)** | 51.7% |
| **reference, adults** | 6 | **1.20 (1.11–1.29)** | — |
| ours, infants and children | 4 | 1.1028 (1.0028–1.2128) | 0% |
| ours, all trials | 7 | 1.1406 (1.0787–1.2061) | 11.9% |

The adult subgroup — the only stratum the reference is comparable with — agrees
to **0.03 on the point estimate with overlapping intervals**. That is (a) no bug
remaining, and the residual is (b) trial set: three of their six are absent from
ours.

**Decomposition:** the original gap was **(a) our bug**, wholly. Not an estimand
difference, not a trial-set difference. The corrected object reconciles.

---

## Summary

| app | trial-list diff | estimate reconciliation | verdict |
|---|---|---|---|
| COVID19_VACCINES | all 3 present in the reference; nothing spurious | 2 of 3 match within rounding; third explained by person-time | **reconciles**; the reference's refusal to pool across vaccines is a finding about the app |
| ALIROCUMAB | ours a 6-of-18 subset, by scope | not comparable — different outcome | **reconciles**; a trial was recovered, k 5→6 |
| PREVNAR15 | 2 of our 7 are in the reference; 4 are paediatric and could not be | adults 1.1696 vs reference 1.20 — overlapping | **reconciles only after rebuild**; the diff exposed three object defects |

No reconciliation manufactured a divergence, and in every case the published
review was justified. Two of the three produced a substantive change to our
object — and the one real numeric divergence turned out to be entirely our own
defect, found by comparison with the literature rather than by any tool.

---

# Gemini file-access gate, round 3 — adjudication

Four legs run (two apps x SOURCE/JUDGE), read-only tools, no shell. Every claim
below was verified against the source or by EXECUTING the proposed exploit.
"Confirmed" means the exploit was applied to the object and the validator's exit
code checked — not that the argument sounded plausible.

## Validator findings — ALL FOUR CONFIRMED REAL

| # | claim | test | result |
|---|---|---|---|
| 1 | `per-trial-recompute` uses a flat 0.005 absolute tolerance, too wide for small RRs | set NCT04530396 point 0.0845 -> 0.0890 | **PASSED — real** |
| 2 | `direction-anchor` returns early when `pooled` is None, so a single trial's direction is never checked | swap arm events, invert the per-trial RR | **PASSED — real** |
| 3 | `arm-roles` counts arms declared in the JSON and never compares them with the arms posted in the source | drop the 2nd V114 arm entirely, no disclosure, source-consistent numbers, pool recomputed | **PASSED — real** |
| 4 | omitting `percentage` makes both `source-category-binding` and `against-sources` skip the cell | delete percentage, fabricate 900/1000, pool recomputed | **PASSED — real** |

Findings 3 and 4 were each *first* blocked incidentally — by `pooled-recompute`
and `direction-anchor` respectively — because the naive mutation left the stored
pool inconsistent. Re-running with the pool recomputed, exactly as the reviewer
specified, both passed. An incidental block is not a defence; recording it as
one would have been the same error this project exists to catch.

## Object findings

**CONFIRMED — covid19-vaccines**
* `COV001` and `1077` appear in the object's removal justification but in **no
  staged source**. `NCT04324606.ctgov.json` was never staged. The object argues
  another number is wrong using facts it cannot support. Serious, and in the
  worst possible place.
* Quarantine prose says "the rest could not be verified to a primary source",
  where "the rest" resolves to 9 (`total_cited` 12 minus `retained` 3), but
  `excluded_trials` is **8**. The 9th, NCT04324606, was removed for a
  units-of-analysis error, not unverifiability. The braced references keep the
  arithmetic right while the *claim about* those trials is wrong — a failure
  mode the prose-numeral rule does not address.

**CONFIRMED — prevnar15-pneumo**
* `interpretation_caveat` states "Between-trial variation in the ratio is low"
  without qualification, while the object's own **adults subgroup records
  I2 = 51.7%**. Misleading as written.
* `estimand_note` says an earlier build "reported a composite of all
  injection-site symptoms" and that "that composite was in fact swelling". Those
  cannot both be true as phrased. What happened is that a value was *labelled*
  as a composite. The wording is genuinely misleading and is being rewritten.

**REJECTED as over-claims**
* *"Pooling is mathematically impossible: at a 75.8% baseline the maximum RR is
  ~1.31."* Two errors. 75.8% is the **treatment** arm of NCT03547167, not a
  control rate. Control rates run **36.5% to 68.8%**, giving RR ceilings of
  **2.74 down to 1.45**, and every observed RR (**0.92 to 1.28**) sits below
  every one of them. No ceiling is approached, let alone violated. The
  underlying point — that widely varying baseline risk makes a common RR a
  modelling choice worth defending, with OR or risk difference as alternatives —
  is legitimate and is retained; the impossibility claim is not.
* *"Reference efficacies silently do work the object's data does not support."*
  They are explicitly labelled `reference_efficacy_percent` with a
  `reference_source_id`, and the reading note states they are the published
  review's figures shown for comparison. Nothing is silent. **But** the Cochrane
  source is not staged, so they cannot be checked against a primary record here.
  That gap is real and is being fixed; the framing of it was not.
* *"Fabricated story"* about the estimand note. The wording is misleading, not
  invented. Recorded as a prose defect, not as fabrication.

## Verdict under bar B

**NEITHER APP CERTIFIES. Nothing is pushed.**

Both objects carry confirmed defects, so criterion (1) fails on each,
independently of what the Codex legs return.

One process note: the prevnar15 SOURCE leg verified every cell binding
trial-by-trial and found **zero** failed cells, but **omitted the terminal
VERDICT line**. Substantively clean; formally not a verdict. It is recorded as a
clean source check, not as a PASS.

---

# Round 4 — Codex on the corrected objects, Gemini re-run

## Verdicts

| app | Codex | Gemini SOURCE | Gemini JUDGE |
|---|---|---|---|
| prevnar15-pneumo | DEFECTS-FOUND — **no object defect**, validator only | **PASS**, object clean, every cell traced | DEFECTS-FOUND — 2 object, 2 validator |
| covid19-vaccines | DEFECTS-FOUND — 2 object defects | DEFECTS-FOUND — 2 object, 1 artefact | DEFECTS-FOUND — 1 validator |

**NEITHER CERTIFIES. Nothing pushed.**

## Confirmed object defects, now fixed

* prevnar: "swelling in **six** of the seven trials" was wrong. Checked trial by
  trial: swelling is the last posted category in **all seven**. The reviewer
  called the swelling explanation circular reasoning, which it is not — it was
  measured, not inferred — but checking the claim in order to refute it exposed
  a miscount that was mine.
* prevnar: the adults subgroup called itself "directly comparable" with the
  published synthesis without saying that review pools six adult trials where
  this carries three.
* covid: reference efficacies cited a review that was not staged; now staged and
  all nine figures confirmed present in it.
* covid: "the reduction can be audited" while no excluded registration was
  staged. All eight now staged — and opening them found **NCT04627298 is an HPV
  vaccination video-game trial**, not a COVID trial. It had been filed under
  "counts not verifiable", true but beside the point, and the wrong reason
  survived precisely because nobody could open the record.

## Open object defects, NOT yet fixed

* covid: the object notes the person-time estimand difference for CVnCoV but not
  for BBIBP-CorV, whose reference figure is also person-time based
  (per 1000 person-years). Confirmed against the abstract.
* covid: the Sputnik reference figure of 91.1 sits against a crude 91.6 from the
  trial's own counts and the paper's own crude figure, with no note explaining
  the difference. Our sourcing rule requires recording divergence, not resolving
  it silently.

## Validator: ten exploits confirmed, eight closed

Every one verified by EXECUTING it. Four of the ten first blocked only
incidentally — the naive mutation left a pooled value, a subgroup or a direction
inconsistent — and passed once the mutation was completed as its author
specified. An incidental block is not a defence.

Still open, and the sharpest finding of the round:

**`check_reference_consistency` claims an anchor it does not have.** Its
docstring said the published figure "is outside the object and cannot be flipped
by editing the object". That is false: `reference_efficacy_percent` is stored
INSIDE the object. Inverting a trial's arms, recomputing its ratio exactly, and
moving the reference figure to match passes everything — confirmed, with the
object then reporting a vaccine that multiplies COVID risk twelvefold.

This is precisely the failure this project keeps finding in its own tool: a
check that looks strict and tests something weaker than it claims. The fix is to
read the figure back from the staged review, which is now possible because that
review is staged. A first attempt at it is reverted, not shipped: it hung the
validator at import, and the numeric comparison it needs is not a string search
— the review prints "91.10" where the object stores 91.1.
