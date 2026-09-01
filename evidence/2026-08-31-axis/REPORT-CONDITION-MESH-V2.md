# Condition axis v2 — record-verified, tree-broadened. **REFUSED, and this time by R1 and R2.**

    REF.rule    604ed6957a1adf17   ⛔ FROZEN throughout
    REF.frame   a0d44914a5ef99e3   1,186 CDSR cardiology reviews
    REF.lookup  mesh_lookup.py — [MeSH Terms]-bound, record-identity VERIFIED, [TN] broader
    REF.pre     PREDICTION-MESH-V2.md, written before the run

---

# 1 ⛔ FIRST, A CORRECTION TO MY OWN REPORT

`REPORT-CONDITION-MESH.md` §3.1 said v1's defect was **the unit** — words expanded where a
phrase was meant. **That is true and it is not the root cause.** The phrase queries fail too:

    free-text esearch, PHRASE query               descriptor actually returned
    hypercholesterolemia                       -> Hyperlipoproteinemia Type III
    pulmonary arterial hypertension            -> Familial Primary Pulmonary Hypertension
    paroxysmal supraventricular tachycardia    -> Tachycardia, Ventricular

⇒ **The root cause is an UNVERIFIED RECORD.** `esearch db=mesh` is relevance-ranked over
every field; taking `idlist[0]` asks a confident authority a question and never checks which
question it answered. §3.1 stands where it was written; this supersedes it.

⭐ **Third occurrence of one shape tonight**: `SGLT2` → the protein, `Intravenous` → the
route, `supraventricular` → a ventricular arrhythmia. Every time a wrong seed is confidently
expanded by an authority into a plausible list. **The fix each time is to check the identity
of what came back, not the size of it.**

---

# 2 THE SEMANTIC GATE (R5) — the criterion v1's report said was missing, and it fires

    concepts refused because the record was not the one asked for : 4 of 18

    colchicine-cvd-review    cardiovascular prevention  -> (none)                  NO_RECORD
    etripamil-psvt           paroxysmal supraventricular
                             tachycardia                -> Tachycardia, Ventricular RECORD_MISMATCH
    evolocumab-dyslipidemia  dyslipidaemia              -> Dyslipidemias            RECORD_MISMATCH
    evolocumab-mixed-…       mixed dyslipidemia         -> (none)                  NO_RECORD

**The second row is the exact expansion that produced v1's worst output.** R1–R4 were all
quantitative and none of them could see it. R5 asks a question no count can: *is this the
record I asked for?*

⚠️ **And R5 over-fires once, which I am reporting rather than tuning away.** `dyslipidaemia`
→ `Dyslipidemias` is a **correct** record refused on a spelling difference the British form
introduces (`dyslipidaemia` vs `dyslipidemia`) — my singularisation fixed the plural but not
the `ae`. The frozen rule's own `norm()` already handles `ae`; the verifier does not use it.
That is a one-line fix and it is **not** applied here, because changing a gate after seeing
which cases it caught is how a gate stops measuring anything.

---

# 3 THE VERDICT: R1 AND R2 TRIPPED

    R1  colchicine-cvd-review was MATCHED and is not under v2
    R2  colchicine-cvd-review loses CD014808 and CD015003

**Two of the four counterparts that must survive.** ⇒ **v2 is NOT ADOPTED. The incumbent
literal axis stands.**

## Why, exactly — and it is the honest limit of a phrase axis

`colchicine-cvd-review`'s span is **`cardiovascular prevention`**, which is not a MeSH
concept at all — it is a *purpose*, not a disease, so the lookup returns `NO_RECORD` and v2
falls back to matching the literal phrase. `cardiovascular prevention` appears in **0 of
1,186** reviews. The incumbent's 2-of-{`cardiovascular`, `prevention`} matched 51 and found
both colchicine counterparts.

⇒ **A phrase axis is fatal wherever the span is not a concept**, and the corpus is full of
spans that are purposes, populations or settings rather than diseases. That is a structural
limitation of v2, measured rather than argued.

---

# 4 BROADENING RESCUES A DEAD TERM AND INFLATES A LIVE ONE — the same operation

| topic | condition axis, incumbent → v2 | what happened |
|---|---|---|
| pitavastatin-auto-full-review | 0 → **1** | `Hypercholesterolemia` → tree parent `Hyperlipidemias`, which matches exactly 1 row. **The dead term is rescued.** |
| bosentan-pah-children | 14 → **99 (8%)** | broadening added the bare parent `hypertension`, 95 rows. **A live term is inflated.** |
| bosentan-pah / -monotherapy | 19 → **4** | phrase `pulmonary arterial hypertension` is stricter than 2-of-3 words. Counterparts survived anyway. |
| dabigatran-stroke | 198 → **198** | its span is the single word `stroke`; phrase match *is* word match. **v2 cannot help a one-word condition.** |

⭐ **Direction must be chosen per topic by the measured failure** — broaden a
`CONDITION_MISMATCH`, narrow an axis over ~15% of the frame — which is what §6 of the v1
report proposed and what this run turns from a proposal into a measurement.

    v2 terms generated : 113      live on the frame : 30      dead : 83

---

# 5 THE PREDICTION, SCORED

| prediction | result | |
|---|---|---|
| topics tripping R1: **0 or 1** | **1** | **HIT on the count** |
| …and `bosentan-pah` is the one I'd bet on | it was **colchicine**; bosentan narrowed 19→4 and kept both counterparts | **MISS on which** |
| `pitavastatin` state changes, counterparts stay 0 | 0 → 1 row, 0 counterparts | **HIT, exactly** |
| `dabigatran-stroke` unchanged at 198 | **198 → 198** | **HIT** |
| concepts refused for record mismatch ≥ 1 | **4** | **HIT** |
| verdict: not adopted | **not adopted** | **HIT** |

⭐ **Five of six, and the miss is the interesting one.** I named the right *risk* — a phrase
axis can lose rows — and attached it to the wrong topic. I reasoned about the span I could
see failing (`pulmonary arterial hypertension`, 3 words, needs all 3) and never considered
the span that **isn't a concept at all**. The failure mode I predicted was narrowing; the
one that bit was *absence from the authority*.

⚠️ I said I would not apply a direction after over-correcting last run. I did not, and the
result is the first prediction tonight that is neither optimistic nor pessimistic — it is
simply incomplete in a way I can name.

---

# 6 WHAT SHIPS AND WHAT DOES NOT

**Ships:** `mesh_lookup.py` — the verified lookup, the `[TN]` broadening, the rate-limit
retry, and its control that the broadening step can return a positive at all. It is a
correction to a defect, and it is worth having whether or not the axis is adopted.

**Does not ship:** the v2 condition axis. R1 and R2 tripped.

⛔ **A dead field found by giving each candidate its own count.** `[MeSH Tree Number]` — the
spelled-out, obvious name — returns **count=0 silently** for every tree number; `[TN]` works.
A `broader()` built on the obvious spelling would have returned nothing forever and read as
*"MeSH holds no broader concept"* — a wrong belief about an authority rather than a fact
about a term. `tree_field_works()` now gates the run: if the field stops resolving, no count
is printed.

## 6.1 One more hole, found by a CLEAN SIBLING and not by the corpus

`plant_mesh_lookup.py`'s M2 sibling asserts the stem does not collapse different concepts.
It failed: **`stroke` is a subset of `{stroke, genius}`**, so `Strokes of Genius Syndrome`
verified as the record for `stroke`. A one-token query is a subset of almost any descriptor
containing that token — `Heat Stroke`, `Stroke Volume`.

Fixed: containment counts only when **both** sides carry two or more tokens; otherwise the
sets must be EQUAL. Strictly stricter, which is the safe direction for a check whose job is
to refuse.

⭐ **And the claim that it costs nothing was RE-RUN, not asserted:** after the change the
twenty produce the same 4 refusals and the same R1/R2 trips. Every record that verified did
so by set equality all along.

⚠️ **The distinction from §2 is deliberate.** This failing case was SYNTHETIC — written to
test discrimination, not drawn from the corpus — so fixing it does not tune the gate to the
data it is about to judge. The British-spelling over-refusal in §2 IS a corpus case, and is
left unpatched for exactly that reason, with `plant_mesh_lookup.py` M3 asserting the DEFECT
rather than the requirement and saying so.

**Still open:** the one-line `ae` normalisation in the verifier (§2), deliberately not
applied after the fact; the thirteen truncated control topics; infectious disease.
