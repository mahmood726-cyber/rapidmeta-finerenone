# Corpus-level recommendation: enrich the screening packet before re-prompting anything

**2026-08-19. Applies to every dual-screened review in the corpus, not to one topic.**

---

## The recommendation

**A screener that returns UNDETERMINED from a truncated title is answering correctly about
what it was shown. No rewording fixes that.**

Enrich the screening packet — full title, abstract, publication type, registration id where
one exists — before spending any effort on prompt wording. It is cheaper than re-prompting,
it is likelier to raise *real* agreement rather than the appearance of it, and unlike a
wording change it cannot induce a bias of its own.

---

## The evidence

`arni-hfref` recorded that its 78.5% dual-screening agreement rate should not be read as
unbiased inter-screener reliability, proposed a cause inside its own prompt, and **named the
experiment that would settle it**. That experiment had never been run. It was run on
2026-08-19.

**Design.** The first 25 of the 91 disagreement records, same truncated titles, blinded as the
original was — no screener A decision, no axis. Run on **Gemini 3.1 Pro via agy, the same model
family as the original screener B**, so prompt wording is the only variable that moves. Two
arms differing by exactly one sentence.

| arm | prompt | UNDETERMINED |
|---|---|---:|
| **A — neutral** | eligibility criteria only, no loss statement | **22 / 25 (88%)** |
| **B — asymmetric** | identical, plus *"An UNDETERMINED that is later resolved is worth more than a confident wrong exclusion."* | **25 / 25 (100%)** |

### The finding is which three records moved, not the twelve points

| record | neutral verdict | criterion | title |
|---|---|---|---|
| `39387766` | EXCLUDE | 1 — not a randomised trial | *Race in Heart Failure: A Pooled Participant-Level Analysis…* |
| `39262640` | EXCLUDE | 2 — not the intervention | *Influenza Vaccination and Cardiovascular Events…* |
| `34758252` | EXCLUDE | 3 — not the population | *ARNI in Acute Myocardial Infarction* |

A pooled participant-level analysis, an influenza-vaccine study, and an acute-MI population —
**the three easiest calls in the set.** The clause suppressed decisions on precisely the
clear-cut cases.

> **An instrument that hesitates on hard cases is behaving well. One that hesitates on obvious
> ones is broken in a way that hands a human exactly the work they would most resent.**

That is a sharper and more useful statement of the harm than any inflation of the agreement
rate, because it names *which* decisions were lost.

### Why the packet, and not the prompt, is the primary recommendation

**22 of 25 stayed UNDETERMINED with no loss statement at all.** The wording contributes 12
points; the remaining 88% is not attributable to it. On a truncated title and nothing else,
UNDETERMINED is frequently the *correct* answer.

The object's own hedge — *"consistent with an induced bias as well as with genuine caution"* —
is vindicated **on both branches**: both are operating, and caution dominates. A page that
declined to resolve an ambiguity it could not settle, and named the experiment that would, has
been shown right either way.

---

## What must not be quoted from this

**This run saw less than the original screener did.** Screener B received title, journal, year
and source; `arni-hfref` stores its disagreement titles truncated at ~70 characters, and that
is all this run had.

- **Absolute rates do not transfer.** 88% is not a corpus fact and must not be quoted as one.
- **Only the A/B contrast is claimed**, because both arms saw the same starved input.
- **n = 25, one run per arm, no repeats.** A demonstration that an effect exists, not an
  estimate of its size.
- The sample is the *disagreements*, so the 100% baseline is definitional, not a finding.

**The 78.5% agreement rate on the live page still must not be read as unbiased reliability.**
The cause is better located, not eliminated.

---

## What to do

1. **Enrich the packet** — abstract and publication type at minimum. Publication type alone
   would have decided record `39387766` (a pooled analysis, not a trial) mechanically.
2. **Re-run dual screening on the enriched packet**, neutral wording, and report the agreement
   rate from that run rather than from the current one.
3. **Store the packet that was actually sent**, not a truncation of it. This experiment was
   limited by the corpus keeping 70 characters of a title; had the packet been stored, the
   replication would have been exact and the incomparability caveat above unnecessary.
4. **Do not reword before enriching.** A wording change on a starved packet moves 12 points and
   leaves the cause in place.

Evidence: `evidence/2026-08-19-batch1/screener_b_wording_experiment.json`;
recorded on the object at `screening.dual_screening.named_experiment_result_2026_08_19`.
