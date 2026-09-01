# Registered predictions: can extraction work with mostly regex and a little AI?

**Written and committed BEFORE the test was run.** A hypothesis tested after the
fact is not a hypothesis. Nothing below may be edited after the first result; a
wrong prediction is recorded as wrong and is more useful than a right one that
was written afterwards.

## The question

Mahmood: *"will data extraction using all our sources work with mostly regex and
a tiny amount of AI at high quality? I think it will but test it."*

## The predictions, as given

**MAHMOOD** — mostly regex plus a tiny amount of AI reaches HIGH QUALITY.

**REVIEWER** — right where the source is STRUCTURED, wrong where it is not. And
the hard part is not reading numbers, it is knowing WHICH ARM IS WHICH: a
labelling problem, not a reading problem.

**THIS LANE (mine, registered so it can be scored against the others)** — I
expect the reviewer's split to hold, and I add three falsifiable claims of my
own:

1. **Availability, not method, will dominate.** In the only measurement taken so
   far, 20 of 33 trials had NO free full text — 61%. I predict TIER 0 + TIER 1
   will be unavailable for more than half of a random sample, and that no choice
   of extraction method moves that number.
2. **TIER 0 will beat TIER 1 on accuracy and lose on availability.** CT.gov
   posted results are typed fields; JATS tables are markup whose *headers* still
   have to be interpreted. So I expect TIER 0 near-perfect where present, and
   TIER 1 to produce the first real MISMATCHes.
3. **The AI's necessary job will be arm/outcome LABELLING, not number reading.**
   I predict zero cases where a tier fails because a digit could not be read,
   and multiple cases where a tier fails because which column is treatment, or
   which row is the outcome we mean, is ambiguous.

If (3) is right the honest headline is not "AI does extraction". It is: *regex
and parsers do the extraction; a model is asked one bounded labelling question
per table, which a human can check in seconds.*

## Design

    TIER 0  REGISTRY API     CT.gov posted results, structured JSON, no extraction
    TIER 1  JATS XML TABLES  Europe PMC / PMC OA <table-wrap>, parsed not scraped
    TIER 2  PROSE REGEX      numbers in body text
    TIER 3  AI               only what tiers 0-2 could not resolve

Reported PER TIER: how many trials it resolved ALONE, and its accuracy on those.
That distribution is the answer, because "mostly regex" is a claim about a
distribution across tiers, not about one method.

## Scoring rules, fixed in advance

**A wrong cell is far worse than a missing one.** A missing cell declines; a
wrong cell publishes a false number. So:

- **PRECISION and RECALL are reported separately. Never a single "accuracy".**
- **The cascade FAILS CLOSED.** If two tiers disagree on one cell the answer is
  `CONFLICT`, never the higher tier's value.
- Verdicts: `EXACT_MATCH` · `MISMATCH` · `CONFLICT_BETWEEN_TIERS` · `NOT_FOUND`
  · `NO_SOURCE_AVAILABLE` · `ERRORED`.
- The **distribution** is reported, never an accuracy over the subset a tier
  happened to handle. That is reach reported as coverage and it is this repo's
  most repeated defect.

## The leak this test must not have

The extractor runs **BLIND to our stored values**. The existing corroborator
(`scripts/pmc_inject_evidence.py`) scores a sentence by how many of our stored
numbers it contains — it cannot disagree with us, only fail to corroborate us,
and it would score 100% on a corpus of fabricated cells. This cascade must
propose a value from the source alone and only then be compared.

## Why the structured tiers deserve the benefit of the doubt

CT.gov posted results and JATS `<table-wrap>` are **not prose**. They are markup
with cells. Regex over markup and regex over prose are different problems, and
every unanchored-substring defect this project has recorded — `azilsartan`
matching `ART`, `AFRICA` matching `AF`, `anaemia` matching `MI`, `revisions`
matching `vision` — was the second kind.

## TIER 1-2 predictions, registered before the run (added after TIER 0 reported)

TIER 0 is scored. Predictions 3 (labelling, not reading) and the reviewer's
split were right; **my prediction 1 was WRONG** and the reason matters here: I
predicted availability would dominate, carrying a 61%-no-full-text figure that
was true of **PMC** across to **CT.gov**, where the real figure was 15%. A number
true of one population applied to another. So every prediction below names the
population it is about.

**P4 — availability, population = OUR 20-trial sample, source = AACT
`study_references` + PMC OA.** I predict full text is reachable for FEWER than
half of the 20. Basis: the earlier PMC measurement gave 13 of 33 (39%) on a
different sample, and I expect a similar order here. If it comes back above 50%
I was wrong, and the earlier 39% was sample-specific rather than a property of
the corpus.

**P5 — tier 1 (JATS tables), population = trials with a fetched PMC XML.** I
predict `<table-wrap>` yields the four cells CLEANLY where a results table
exists, and that the failure mode is the SAME labelling wall as tier 0: column
headers will read `Etrolizumab` and `Placebo`, not `treatment` and `control`.

**P6 — the first genuine MISMATCH appears at tier 1, not tier 0.** A typed JSON
field cannot be row-misaligned; a table can. I predict >=1 MISMATCH at tier 1
where tier 0 produced none, and that if it happens it is an alignment error
(right number, wrong cell), not a misread digit.

**P7 — tier 2 (prose regex) resolves almost nothing ALONE.** I predict it
corroborates numbers already found by tiers 0-1 and independently resolves 0 or
1 of the 20. Prose states percentages and effect sizes; denominators live in
tables and CONSORT diagrams.

**P8 — CONFLICT_BETWEEN_TIERS will be RARE but non-zero**, and where it occurs
it will be a per-protocol versus intention-to-treat denominator difference
rather than either tier being wrong. That is the case the fail-closed rule
exists for, and resolving it by tier rank would publish one analysis set while
citing another.

**Exclusion, checked before the run:** all 20 sample ids are present in AACT
`design_groups` 2026-08-30, so none is among the 45 malformed ids that resolve
to nothing for a reader. Asserted from PRESENCE in the registry, not from
absence from a list this lane does not hold.

## Scale and stopping rule

Start at 20 trials spanning all four tiers. Hand-read five extractions. Then
predict the full-corpus distribution BEFORE scaling, so the prediction can be
scored against the scaled run.
