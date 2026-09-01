# PRE-REGISTRATION — screening recall (GAP 2)

**Written 2026-09-01, BEFORE any result was computed.** Nothing below may be changed after
the first run. If the method turns out to be wrong, the fix is a *new* pre-registration with
a new seed, recorded as a second measurement — not an edit to this one.

**Frozen at:** `git hash-object PREREG-screening-recall.md` recorded in the result file.

---

## The question

**What would our screening have missed?** Stated operationally: *of the trials a published
Cochrane review actually included, what fraction does our mechanical search retrieve?*

This is **relative recall against a known-positive seed set** — a Handbook-legitimate route.
It does **not** estimate what Cochrane itself missed. It estimates our search against
Cochrane's includes, which is the number we can defend.

## Seed set — declared, not chosen after looking

- **Source:** RoBBR `Main_task_Cochrane_test.json` (Lou, Tao et al., EMNLP 2025,
  arXiv:2411.18831; CC-BY-NC-4.0). Each record pairs a Cochrane review `objective` with an
  included trial's `paper_doi`.
- **Grouping:** by exact `objective` string → the set of that review's included papers.
- **Eligibility, fixed now:** every objective with **≥ 3 distinct `paper_doi`**.
  **MEASURED before writing this: 20 objectives qualify, of 36.** No objective is dropped
  for any other reason. No cherry-picking by topic, size or outcome.
- **Seed = a DOI that a Cochrane review included.** Every seed is a known positive by
  construction.

## Search under test — mechanical, reproducible, no model

1. Take the review `objective` verbatim.
2. Lowercase; strip a leading `to assess|to compare|to determine|to evaluate|to investigate`.
3. Remove stopwords and method words (`effects`, `efficacy`, `safety`, `treatment`,
   `people`, `patients`, `adults`, `children`, `versus`, `for`, `of`, `in`, `the`, `and`,
   `with`, `on`).
4. Keep the remaining tokens of length ≥ 4 as content terms; keep at most the **first 6**.
5. Query PubMed: all content terms `AND`-ed, no date limit, no language limit,
   `retmax = 200`.
6. **Retrieved set** = the PMIDs returned.

No hand-tuning per topic. If a query returns zero, that is a result and is reported as
zero — it is not repaired.

## Matching

Seed DOI → PMID via NCBI `esearch` on `"<doi>"[AID]`, then `[DOI]`.
**A seed whose DOI cannot be resolved to any PMID is EXCLUDED from the denominator and
reported separately as `unresolvable`** — it is not counted as a miss, because a seed that
is not in PubMed cannot be found by a PubMed search, and scoring it as a miss would measure
PubMed's coverage rather than our search's.

## Metric

- **Per review:** `recall = |retrieved ∩ resolvable_seeds| / |resolvable_seeds|`
- **Headline:** the **micro** figure — total hits / total resolvable seeds across all
  eligible reviews. The macro (mean of per-review recall) is reported beside it because
  they answer different questions, and quoting one alone is the ratio trap.
- **Reported regardless of value.** A low number is the finding.

## Controls, fixed now

- **MUST-FIRE:** a query built from an objective must retrieve ≥ 1 of its own seeds for at
  least one review. If it retrieves zero everywhere, the harness is broken, not the search.
- **KNOWN-ANSWER:** a seed DOI resolved to a PMID must be retrievable by a direct PubMed
  query for that PMID. This proves the matching step can return a positive.
- **NEGATIVE CONTROL:** a deliberately unrelated query (`"quantum chromodynamics"`) must
  score **0** against the same seeds. A pipeline that cannot return zero cannot return a
  meaningful non-zero.

## Declared prior — recorded before the run

> **I expect micro recall of about 40%, and I expect the band to be wide (20–65%).**

Reasoning: the query is deliberately crude — an AND of up to six content terms with no MeSH
expansion, no synonyms, no field tags and no RCT filter. Published relative-recall figures
for *hand-built* expert searches sit high; this is not one of those.

**On the direction of my own error:** across this session my estimates missed low ten times
and then, after I corrected for that, missed high once by 44%. **Leaning against a bias just
relocates it.** So this prior is reasoned from the query's crudeness rather than adjusted for
my recent record, and it will be scored either way.

## Limitations, declared now rather than after

1. **The seed set is a SUBSET of each review's included studies** — RoBBR sampled papers per
   review, so this measures recall against a sample of the includes, not all of them.
2. **n is small** — 20 reviews, on the order of 80 seed papers. This yields a point estimate
   with a wide interval, not a precise rate. No claim of precision will be made.
3. **PubMed only.** Cochrane searches CENTRAL, Embase and trial registries. Our recall
   against a PubMed-only search is therefore an **upper bound on what a PubMed-only pipeline
   achieves and a lower bound on what a full multi-database search would achieve.**
4. **The seeds are drawn from a benchmark corpus**, not from our own corpus's topics, so
   this measures the *method*, not our corpus's actual screening.
