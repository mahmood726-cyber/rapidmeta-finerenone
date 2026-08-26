# Paper Studio — round 1, and what the gates could not see

Lane: Paper Studio tab (`pn-paper`) only. The syntheses, stores, generator and review pages
belong to the blinded-review lane. Rubric **v1.1**, written before round 1.

## Round 1 result

**0 of 23 manuscripts pass.** Codex (`gpt-5.5`, openai) and agy (`Gemini 3.1 Pro`, google,
pinned `--model gemini-3.1-pro-high`) each returned FAIL on all 23. Families agreed 23 of 23.

| | cardiology | infectious disease | total |
|---|---|---|---|
| manuscripts reviewed | 17 | 6 | **23** |
| PASS (both families) | 0 | 0 | **0** |
| FAIL (both families) | 17 | 6 | **23** |
| calls returning real bytes | 34/34 | 12/12 | **46/46** |

Every call's output byte count is recorded; a call under 200 bytes is marked a FAILED CALL,
never "no defects found". Payload sha256 recorded per page. **All 23 re-hashed against
`c3af11ce28` after the rescue: 0 changed**, so round-1 verdicts remain adjudicable against
current bytes.

**Unanimity is a limitation, not a triumph.** 23/23 agreement means the instrument does not
yet discriminate between pages — it cannot rank them. Both families produced substantive,
differing, verbatim-quoting reviews (codex output 5,645–17,656 bytes), so this is not a
harness artefact; but a bar that everything fails cannot tell a near-miss from a wreck.

## The gates that should have caught the RoB defect, and why neither did

The confirmed defect: the Methods sentence *"risk of bias was assessed with RoB 2"* is
emitted while the same page's analysis panel says *"Risk-of-bias traffic light — not
computable. No per-domain RoB-2 assessment is stored in this object."* **23 objects; 14 are
cardiology or infectious disease.**

Cause is a **key-name schism**. Three readers of "was RoB assessed", two spellings:

| reader | key it accepts | verdict on the 23 |
|---|---|---|
| `paper_projector.py:3586` (Methods sentence) | `risk_of_bias.by_outcome` | asserts the claim |
| `projectors2.py::rob_figure` (traffic light) | `rob2.trials` | refuses to draw |
| `lint_method_claim_has_a_field.py:57,60` (the gate) | `rob2.assessors`, `rob2.tool` | **sees nothing** |

**23 of 24 objects that hold an assessment store it as `risk_of_bias.by_outcome` and not
`rob2.*`.** The gate written to prevent exactly this class is keyed to the spelling used by
ARNI — the one page that does not need it.

**And the gate is blind for a second, worse reason.** Run today it reports
`asserts 0 claim(s), 0 unbacked` for **every** object including `sotagliflozin-hf` and
`sglt2-hf`, then prints PASS over 141 objects. It reads method claims from the object's
stored prose. **The Methods sentence does not exist in the object — the projector composes it
at render time.** A gate that inspects the source cannot see a sentence created in the
projection. Its PASS is vacuous for this entire class, and it is confident.

*True of a level it never touched, blind to the level it rewrote.*

### `no_rob_banner` is NOT this defect in a gate

It was worth checking and the answer is no. `regression_check.py:449` tests for the literal
string `"Provisional RoB-2 and GRADE"` — a **disclosure element, not an assessment**. The file
documents its own failure: *"FINERENONE_REVIEW … PASSES THIS SIGNAL while printing the banner
over 0 of 145 trials assessed … One more check that fails toward comfort."*

**No control has been catching the RoB mismatch.** A page can paste the banner and pass.

## Handoff to the blinded-review lane — the seven that pool nothing

Surfaced here, classification is yours. Under *"pool the poolable"* these are **not** archive
candidates: each holds 2–4 trials on exactly one outcome and pools none of them. This is a
declined pool, not an absent one.

| page | trials | outcomes | k | pooled |
|---|---|---|---|---|
| DOAC_AF_REVIEW | 3 | 1 | 3 | 0 |
| DOAC_CANCER_VTE_REVIEW | 3 | 1 | 3 | 0 |
| RIVAROXABAN_VASC_REVIEW | 4 | 1 | 4 | 0 |
| COLCHICINE_CVD_REVIEW | 3 | 1 | 3 | 0 |
| ABLATION_AF_REVIEW | 4 | 1 | 4 | 0 |
| EVOLOCUMAB_MIXED_DYSLIPIDEMIA_AUTO_FULL_REVIEW | 2 | 1 | 2 | 0 |
| PITAVASTATIN_AUTO_FULL_REVIEW | 2 | 1 | 2 | 0 |

## ARNI is a separate workstream

`ARNI_HF_REVIEW` is the **only one of 149** rendered as "Manuscript — document view" — an
authored manuscript in `ssot/arni-hfref/` via `ssot/wysiwyg.py`, not projected by
`paper_projector.py`. **No projector fix reaches it, and no ARNI fix reaches the other 22.**

A correction on the record: an earlier note that ARNI "is missing a Title" was **my
detector's fault** — it searched for a heading literally labelled "Title". ARNI has one.
