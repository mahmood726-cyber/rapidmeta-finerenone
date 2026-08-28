# Ruling 2 applied: template vs curated, for the ruled 24

## The test used, and why it is the ruling's own

The ruling defines the template class explicitly: *an AUTO protocol specifies nothing —
1,093 share one byte-identical statistical-methods text.* So the test is membership of
that byte-identical block, and nothing else.

**Result: 1,093 files contain the block; 1,093 filenames carry `_auto_protocol_`;
symmetric difference = 0.** Two signals produced by unrelated means partition all 1,193
protocols identically. No threshold, therefore no knob to tune.

## Verdict — 8 / 8 / 8

| state | n | meaning |
|---|---|---|
| **EXISTING_GOVERNS** | 8 | not an AUTO template; I amend, never replace |
| **MY_DRAFT_GOVERNS** | 8 | AUTO template or nothing; my draft governs and names what it supersedes |
| **NEEDS_DRAFT** | 8 | AUTO template or nothing, and I hold no draft — cannot search until written |

EXISTING_GOVERNS: bempedoic-acid-review · cab-prep-hiv-review · cangrelor-pci-review ·
incretin-hfpef-review · iv-iron-hf · nirsevimab-infant-rsv-review · sglt2-hf ·
sglt2-mace-cvot-review

MY_DRAFT_GOVERNS: agyw-hiv-prep-review · alirocumab-lipid · apixaban-vte-prophylaxis ·
apixaban-vte-treatment · bococizumab-lipid-review · empagliflozin-hf-auto-full-review ·
finerenone-cv · icosapent-lipid-auto-full-review

NEEDS_DRAFT: azilsartan-chlorthalidone-vs-olmesartan-hctz · ceftaroline-auto-full-review ·
inclisiran-lipid-kidney-auto-full-review · lefamulin-cabp-auto-full-review ·
rosuvastatin-auto-full-review · rotavirus-vaccine-africa-review · sotagliflozin-hf ·
tigecycline-ciai

## ⚠️ Material caveat on the 8 "curated" — for Mahmood, not decided by me

They are **not bespoke documents.** Their substantive methods prose is shared with up to
**41** other protocols — including analysis-constraining statements such as the HKSJ
variance-inflation floor `max(1, Q/(k-1))`. They are house-standard documents with
topic-specific headers, not individually reasoned protocols.

This does not change the ruling's verdict — they are not AUTO templates, so they govern.
It is recorded because "the existing protocol governs" reads as a stronger guarantee than
these documents actually provide.

## Two wrong instruments, and why each was wrong

Both are recorded because the reasons generalise beyond this task.

**1. "Contains an NCT the topic holds" — over-flagged 14, true answer 8.**
An AUTO protocol is *generated from the topic's own data*, so it always restates the
topic's trials. The test cannot distinguish the classes it was built to distinguish. It
failed toward EXISTING_GOVERNS, which is the costly direction: it would have left a
template governing six searches.

**2. "Contains specifying prose unique to the file" — did not separate at all.**
10 of 12 known-AUTO files cleared it. Their unique text is
`**Intervention.** Patiromer (AACT-verified intervention name)` — a slot-fill. **Vocabulary
is not evidence.** A drug name already present in the filename specifies nothing, and any
criterion that counts characters rather than commitments will be satisfied by it.

**3. The process failure worth naming.** After the first control fired I excluded headings;
after the second I excluded author metadata; the third still fired at 41. Each exclusion
moved the threshold toward the verdict I had already formed. That is how an instrument
gets tuned to measure its author's expectation. The stopping rule that should have been
set at the start: *the class definition comes from the ruling, and controls test the
instrument against it — they do not get to redefine the class.*

## Calibration

- **Positive control, established outside this code:** the deviation lane independently
  found 1,093 protocols sharing one statistical-methods text. The instrument reproduces
  **1,093 exactly**. It measures what was already measured by other means.
- **Negative control:** ran, fired three times, and each firing was informative — heading
  sharing (74), author-address sharing (54), methods-family sharing (41). None was a
  reason to overturn the ruling's own definition; all three are reported above.
