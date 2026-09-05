# Two gate decisions for the repo owner, 2026-09-05. Ruling-ready.

Everything below is measured. Nothing here has been applied: a blocked lane does not edit
the gate blocking it. On a ruling, each change is minutes of work because the
specification, the evidence and the test conditions are already written down.

## STATE OF ALL 155 CANONICAL OBJECTS, ALL FIVE GATES

Re-run corpus-wide with `--all` after tonight's fixes. 155 of 155 reached, no timeouts.

| gate | PASS | FAIL | could not judge | not applicable |
|---|---|---|---|---|
| derived_recompute | 6 | **0** | 16 | 133 no declared derivation |
| contradicting_surfaces | 62 | **0** | 1 | 92 |
| method_label | 52 | **0** | 2 | 101 |
| registration_chronology | 0 | **1** `arni-hfref` | 0 | 154 record no dates |
| refusal_reads_outcome_groups | 0 | **2** `bococizumab`, `evolocumab` | 0 | 153 carry no such refusal |

**Three of five are corpus-wide clean.** Both remaining failures are the subject of the two
decisions below, except `evolocumab-mixed-dyslipidemia`, which is untouched work and not part
of either ruling.

**READ THE JUDGED DENOMINATOR BEFORE THE PASS COUNT.** These gates judge 6, 62, 52, 0 and 0
objects of 155. A rule that judged nothing reads NOT OBSERVED, not SAFE. Three gates being
clean is a statement about the minority they can speak about, not about the corpus.

---

## DECISION 1 -- `refusal_reads_outcome_groups_gate` scoping

### The defect in the gate

`claims_and_disclosures()` builds `blob = json.dumps(obj).lower()` and scans the **entire
object as one string**. It has no way to represent the difference between a claim the object
asserts and a claim the object records as withdrawn. Therefore:

> **A CORRECTION THAT QUOTES WHAT IT WITHDRAWS IS INDISTINGUISHABLE, TO A STRING-SCANNING
> GATE, FROM THE THING IT WITHDRAWS.**

The gate currently penalises exactly the disclosure discipline this corpus mandates -- keep
the withdrawn text verbatim beside the key that retires it -- so every future correction
makes an object look worse.

### The evidence, classified individually rather than dismissed

Ten residual hits on `bococizumab-lipid-review`, each read at its path:

| class | hits | example path |
|---|---|---|
| quoted retraction in a `_superseded_*` key | 6 | `...a_spire_ai_..._superseded_2026_09_05` |
| a withdrawal record quoting the sentence it withdraws | 1 | `...arm_pair_claim_withdrawn_2026_09_05.the_withdrawn_sentence` |
| correction text on a live key | 3 | `.display_change_announced[1].what_changed` |
| **LIVE CLAIM NOT ADDRESSED** | **0** | -- |

**Zero live claims. This was measured, not assumed, and it did not start that way:** the
first classification of eleven hits found TWO live claims, and they were a factual error the
registry disproved (see finding 9 in FINDINGS-HARNESS-GATES-REFUSED-PUSH-2026-09-05.md).
Had the scoping fix gone in before that classification, it would have silenced a true finding
along with the false ones.

### The fix, specified

Exempt from the scan any field **whose declared purpose is to quote something no longer
asserted**, and scan only live claim fields.

**DO NOT KEY THE EXEMPTION ON A NAME SUFFIX.** One hit fires on `the_withdrawn_sentence`, a
field that exists solely to hold retracted text and carries no `_superseded` suffix. A rule
matching `_superseded_*` would leave the next such field to be discovered the same way this
one was. The exempt set is defined by declared purpose, not by spelling.

### The test it must ship with, both directions

- **It must still FAIL** on a live arm-identity refusal resolved from a trial-level source.
  This is the load-bearing half: a fix proven only on the second half is indistinguishable
  from deleting the rule.
- **It must PASS** on the same refusal quoted inside a retraction or a withdrawal record.
- Both must be shown to **fire against the pre-fix gate** -- a plant that passes post-fix
  proves nothing unless it fired pre-fix.

### What the gate got right, and it is stronger than a false-positive story

The two live hits it found were not unevidenced, they were **FALSE**, and the registry
settled it. The same registry record also confirms the gate's founding premise as fact:
`OG000` denotes *Placebo Matched to Bococizumab 150 mg* in NCT02458287's primary outcome and
*Placebo Matched to Bococizumab 75 mg* in its secondary. A trial-level arm table genuinely
cannot say which arms belong to one outcome. **A gate whose premise is confirmed by the data
it governs is a different object from one that merely has not fired wrongly yet.**

---

## DECISION 2 -- `registration_chronology_gate` and the unreachable remedy

### The defect

The gate's refusal text instructs: *"The claim must be withdrawn, or replaced with a
retrospective-formalisation statement that discloses the chronology."* **Doing exactly that
does not clear it.** `rule_search_precedes_screening` and `rule_content_predates_registration`
compare timestamps and never consult a disclosure; they FAIL unconditionally while the
recorded order is inverted. Only changing the timestamps would clear them, and the timestamps
are the facts.

### What was already done on the object, and what it achieved

`arni-hfref`'s prospectiveness claim is withdrawn at all four sites, each original kept
verbatim, replaced with a dated retrospective-formalisation statement. That cleared ONE of
four findings -- the `no surface says so` FAIL -- once the corpus's recognised wording
`"retrospectively formalised"` was used. The gate matches disclosure **literally by design**
and says so in its docstring; the earlier phrasing *"formalised retrospectively"* was
invisible to it. **That part is the gate being right and was fixed on our side.**

Three findings remain and no wording clears them.

### The question, which is a policy question and not a bug

**Should an honestly disclosed inverted chronology be a permanent block?** As it stands,
nothing containing `arni-hfref` can ever be pushed. The recommendation on the table is that
the gate accept a disclosure for the two timestamp rules.

### The caution that must be part of the ruling

If a disclosure can clear a timestamp rule, **the accepted phrase becomes the thing that must
be true**, and this gate matches literally. The phrase must be one an object cannot honestly
carry when its chronology is NOT inverted -- otherwise the escape is available to objects that
have not earned it. `"retrospectively formalised"` is a claim about the review; a gate should
not accept it as a password.

### Two facts about `arni-hfref` the ruling should weigh

- Only **9 of 449** screening records carry a date at all. The evidence is thin in both
  directions.
- The earliest decision timestamp is `2026-08-09T23:59:59` -- a **midnight sentinel**, not an
  observed time. So the first question may be whether these timestamps mean anything, and if
  they do not, the fix is to stop emitting a sentinel as a decision time and the
  prospectiveness claim becomes unevidenced rather than refuted.

---

## WHAT IS NOT BLOCKED BY EITHER DECISION

- 35 commits sit on `harness/rebuild-20260903`, unpushed. The live remote tip is
  `16da44a1caad0474dd9c8c82dd3ab74d273e8993` and the push is a clean fast-forward.
- `main` is `e5a29d9c1a9fe2caac882a3e5bb063bbaed27531`. **THE PUSH DEPLOYS NOTHING** -- the
  site serves `main` and all of this is on the rebuild branch. Only a merge changes what a
  reader sees.
- Five files remain uncommitted because `.githooks/pre-commit-staging` refuses `out/` and
  `figs/`, which are tracked source directories outside its declared set. That is a third
  open question for the owner and is documented in this repository's commit history at
  `5da8296c2`.
