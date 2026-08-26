# Paper Studio — defect list, layer attribution, severity rank

Round 1, rubric v1.1. Scope: the `pn-paper` tab of 23 cardiology + ID manuscripts.
**Nothing here is closed. Mahmood closes.**

## 1. Defects, by layer

| # | defect | layer | reach | ARNI twin needed? |
|---|---|---|---|---|
| D1 | LOO clause contradicts its own count | **generator** `projectors2.py:777` + `scripts/add_visual_abstract.py:135` | 6 of 12 sentences, 5 pages (4 cardio) | **no** — ARNI emits none |
| D2 | caption asserts interval crosses null when it excludes it | **generator**, same function | >=27 of 36 captions, 23 pages (13 cardio, 4 ID) | **no** |
| D3 | Methods asserts RoB 2 while page denies any assessment | **generator, key schism** | **24 pages** (20 backed, 4 unbacked) | **YES** — ARNI is the only `rob2.*` object |
| D4 | no executed search record | **stored record** | 143 of 163 objects; **62 of 62 ID** | **n/a** |
| D5 | GRADE imprecision without OIS inputs | **stored record** | 4 cite OIS, **0 state inputs**; 26 downgrades | **n/a** |
| D6 | duplicate forest-plot control ids, shared radio group | **template** | 5 of 149 (3 cardio, 0 ID) | unknown — ARNI not checked |
| D7 | broken in-page tab anchors | **template** | **148 anchors on 143 of 149 pages** | **YES** |
| D8 | source provenance (published vs FDA) | **not attributed** | unmeasured | unknown |

**D3 correction, on the record.** I reported 45 pages carrying this contradiction. **The
correct figure is 24.** My matcher counted the projector's own *refusal* — "The claim that
risk of bias was assessed with a named tool — No further reason is recorded" — as an
assertion of it. 25 pages were refusing correctly and I scored them as defective. Re-measured
with a positive and a negative control: **24 assert, 25 refuse.**

## 2. Three lanes, three numbers, one defect — reconciled

All three are correct on nested populations. No disagreement.

| measured | n | source |
|---|---|---|
| objects holding `rob2.trials` | **1** of 155 | RoB lane |
| objects holding `risk_of_bias` (any) | **31** of 155 | RoB lane |
| — of those, lacking `rob2` | **30 of 31** (29 of 30 in PAGE_MAP) | RoB lane |
| objects holding `risk_of_bias.by_outcome` | **24** of 155 | this lane |
| — of those, lacking `rob2` | **23 of 24** | this lane |
| delivered pages asserting AND denying | **24** | this lane, rendered bytes |

## 3. The vacuous-gate sweep

**580 modules in `scripts/` can exit non-zero. 59 claim a page/reader defect while reading
only the object.** That is a floor and a candidate list, not a verdict — the claim-layer is
inferred from each module's own prose, which is a weak instrument.

Layers read: **OBJECT only 165 · OBJECT+PAGE 188 · PAGE only 138.**

### `lint_method_claim_has_a_field.py` — a correction to the escalation

It is **not** "a control that has never been able to fail." Run against
`prove_never_fired_by_graft.py` it **refuses** (exit 1): *"graft-topic asserts dual RoB
assessors and holds no rob2.assessors."* The mechanism works.

**It is vacuous for one specific class**, and the reason generalises:

> **The graft plants the claim into `manuscript.methods` on the object — the only layer the
> gate reads.** So the proof shows the gate fires for *object-authored* claims and is
> structurally incapable of showing whether it sees a *projector-composed* one. The Methods
> sentence exists nowhere in the object; `paper_projector.py` composes it at render time.
> The gate reports `asserts 0 claim(s), 0 unbacked` for `sotagliflozin-hf` and `sglt2-hf`
> while the claim is printed on their delivered pages, then prints PASS over 141 objects.

**A prover that plants at the layer the gate reads can never detect the gate's blindness to
the same defect arriving from another layer.** "Proven by graft" is evidence of mechanism,
not of coverage. Every graft in that harness should be re-read with this question asked.

## 4. Severity rank — where effort concentrates

Structural prerequisites missing from the object. Mechanical, not model-judged.

**TIER 1 — no structural gaps; fail on prose/consistency only (3 pages).** All three carry
D3, and D1/D2 are generator fixes. **These are the reachable passes.**
`IV_IRON_HF` (4 pools) · `SGLT2_HF` (2) · `BOCOCIZUMAB_LIPID_AUTO_FULL` (1)

**TIER 2 — one or two gaps (4 pages).**
`ALIROCUMAB_LIPID` (eligibility) · `ARNI_HF` (PRISMA) · `AZILSARTAN_HTN` (RoB) ·
`INCLISIRAN_LIPID_KIDNEY` (search, PRISMA)

**TIER 3 — three or more gaps; no reachable path without new evidence (16 pages).**
- **All six ID manuscripts sit here with an identical missing set** — search, PRISMA,
  eligibility. That is one ID-wide gap, not six page defects.
- The seven pool-nothing cardiology pages are the deepest, missing five each.

**So writing effort concentrates on 7 pages. The other 16 need evidence, not prose** — and
16 of 23 failing for want of a search is D4 restated per page.
