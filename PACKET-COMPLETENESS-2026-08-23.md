# An incomplete evidence packet manufactures false defect classes

**For the two-assessor standard. This is the failure mode that standard will hit first.**

---

## The result

A blinded outside model was given a slice of one SSOT object and asked to review two pieces
of newly written text — a pooled-estimate withdrawal and an arm-role correction — cold.

It was **right twice**, on things no gate in this repository looks for:

- a stored justification **truncated at exactly 400 characters**, ending mid-sentence, on
  the flagship object
- a withdrawal that gave **one ground where the record held two**

It also returned **six charges of fabrication**. Each named a specific fact and said it had
been invented:

| the reviewer said this was invented | where it actually is |
|---|---|
| the "77 patients" shared-control count | `results.by_outcome.primary.the_control_arms_behind_this_pool_2026_08_21.rows[].control_n_posted` |
| `estimand_established` | `results.by_outcome.primary.estimand_established` |
| `estimand_established_does_not_cover_the_contrast_2026_08_20` | same block, adjacent key |
| NEURO-TTR as the origin of the borrowed control group | `THE_POOL_IS_REFERRED_2026_08_20` |
| the published Duarte network | `THE_POOL_IS_REFERRED_2026_08_20` |
| the two precedent refusals that became pools | `scripts/lint_withholding_asked.py` output |

**Six for six on the object. Zero for six in the packet.** Every one was checked against the
artefact before being accepted or rejected, which is the only reason none of them was acted
on.

## Why this failure mode is worse than it sounds

A blinded reviewer with a partial packet does not fail by returning vague or hedged
findings. It fails by returning **the most actionable finding shape there is**: a specific,
quotable accusation that a named number was fabricated.

That shape is nearly indistinguishable from a true positive. It is precise, it cites the
field, it is exactly what an adversarial review is supposed to produce, and it arrives with
the authority of independence. An author who trusts a blinded read — which is the whole
point of commissioning one — will act on it, and acting on it here would have meant
**removing true statements from a withdrawal on the grounds that they were invented**.

> The mechanism that makes a blind review valuable is the same mechanism that guarantees
> this failure. Blinding is withholding context. Withholding context is what produces the
> false charge.

## The remedy has two halves and only the first is obvious

**First half — verify every finding against the artefact before acting.** This is the half
already in practice, and it caught all six. It is necessary and it is not sufficient,
because it is a filter applied *after* the reviewer's effort has been spent. Six of eight
findings were noise; the reviewer's attention was spent generating charges that the packet
made inevitable, and that attention was not spent on the parts of the text that a fuller
packet would have let it examine.

**Second half — the packet's completeness is itself a thing to assert, before the review
starts.** Not hoped for. Not assumed from the fact that a packet was built carefully.
Asserted, in the same way an instrument's controls are asserted:

1. **Name every field the text under review quotes or relies on**, mechanically, by scanning
   the text for field paths and quoted strings — not by remembering what was included.
2. **Assert each of those fields is in the packet**, and refuse to send the packet if one is
   missing.
3. **Tell the reviewer what the packet is NOT.** A blinded reviewer that knows it is seeing a
   slice can say "this may be in a part of the object I was not shown" instead of
   "fabricated". That single sentence converts a false accusation into a correct
   COULD NOT DETERMINE — which is a state this project already treats as valid and useful.
4. **Record the packet.** A finding cannot be re-adjudicated later without the evidence the
   reviewer actually saw. Keep it beside the review.

## Why this belongs in the two-assessor standard specifically

The standard exists so that a judgement is made twice, independently, and adjudicated. Its
whole value rests on the second assessor being genuinely independent — which in practice
means working from a prepared packet rather than from the full record, because a second
assessor with full context and full author's notes is not independent.

**So the standard's core mechanism is the thing that produces this failure.** The more
rigorously the blinding is done, the more reliably the packet is incomplete, and the more
confident the false charges become. An adjudicator receiving eight findings, six of which
are packet artefacts, is being asked to arbitrate between an author and a straw reviewer.

The standard therefore needs a **packet-completeness assertion as a precondition of the
second read**, in the same position and with the same force as the existing requirement that
assessors be independent. Independence without completeness does not produce a second
opinion. It produces a first opinion about a different, smaller object.

## The three states, applied to this

A finding from a blinded read is not true or false. It is one of:

| | |
|---|---|
| **CONFIRMED** | the finding checks out against the artefact |
| **PACKET ARTEFACT** | the fact the reviewer called missing or invented is in the record, outside the packet |
| **COULD NOT DETERMINE** | the artefact does not settle it either way |

Reporting a blinded review without this partition is what turns six artefacts into six
defects. Tonight's read was 2 confirmed, 6 packet artefacts, 0 could-not-determine — and
the honest headline is not "the reviewer was 25% accurate", it is **"the packet was 25%
complete on the fields the text relied on"**, which is a statement about the person who
built the packet.

---

*Recorded 2026-08-23. The two confirmed findings are applied in `b2f8dec2d`; the six
artefacts are named there and in this file so the next reader meets the reasoning rather
than the accusation.*
