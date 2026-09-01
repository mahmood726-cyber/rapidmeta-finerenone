# PRE-REGISTRATION 2 — screening recall, TRUNCATION-FREE

**Written 2026-09-01 after PREREG-1 ran, and BEFORE this measurement was computed.**
PREREG-1 is **not edited**. Its result (micro 4.7%) stands as recorded, with its defect
documented below. This is a second, separate measurement.

## Why a second pre-registration exists

PREREG-1 defined the search with `retmax = 200` and measured recall as
`|retrieved ∩ seeds| / |seeds|`. **`retrieved` was therefore a truncated set**, and
PubMed returns newest-first, so the 200 examined were the most recent — not the ones most
likely to contain trials a Cochrane review included years earlier.

**MEASURED, and this is what exposed it:** for one eligible objective the AND query matches
**843** records (200 examined) and the OR variant matches **23,864,443** (1,000 examined,
0.004%). The post-hoc OR strategy scored **0.000**, *worse* than AND — impossible if OR's
result set contains AND's, and therefore a property of the instrument, not the query.

⇒ **PREREG-1 measured the truncation as much as the search.** Its 4.7% is a valid figure for
"a search that returns at most 200 results", and an invalid one for "does this query
retrieve the included trials".

## The fix — exact membership, no retrieval set at all

Instead of retrieving N records and intersecting, ask PubMed **directly, per seed**, whether
that seed satisfies the query:

```
(<query>) AND <seed_pmid>[UID]     ->  count is 1 (hit) or 0 (miss)
```

This is exact by construction: there is no result list to truncate, and the answer does not
depend on sort order or `retmax`. Cost is one query per seed — O(106), not O(corpus).

## Frozen parameters

- **Seed set:** identical to PREREG-1 — RoBBR `Main_task_Cochrane_test`, objectives with
  ≥ 3 distinct DOIs, seeds resolvable to a PMID. **Unchanged, so the two results are
  directly comparable.**
- **Query construction:** identical to PREREG-1 (steps 1–5), 6 content terms, AND-joined.
  **Deliberately unchanged**, so the only difference between the two measurements is the
  truncation fix.
- **Metric:** micro recall = hits / resolvable seeds. Macro reported beside it.
- **Reported regardless of value.**

## Controls, fixed now

- **MUST-FIRE:** `(<query>) AND <pmid>[UID]` must return 1 for a seed known to satisfy the
  query — take one of the 5 hits PREREG-1 already found. If that returns 0, the membership
  test is broken.
- **MUST-NOT-FIRE:** `quantum chromodynamics AND <pmid>[UID]` must return 0 for every seed.
- **CONSISTENCY:** every seed PREREG-1 scored as a hit must also be a hit here. PREREG-1's
  hits were found inside a truncated window, so they are all genuine; losing one would mean
  the new test is stricter than membership, which would be a bug.

## Declared prior — recorded before the run

> **I expect micro recall of 15%, band 6–35%.**

Reasoning: removing truncation can only *raise* recall relative to PREREG-1's 4.7%, since
every PREREG-1 hit is still a hit and previously-unexamined records can now count. The
question is by how much. The AND-of-six-terms query remains very restrictive — one topic
matched only 843 records in all of PubMed — so I do not expect it to clear a third.

**On my own record:** ten estimates low, one high by 44%, and PREREG-1's 40% missed low by a
factor of eight. I am not adjusting for that streak, because leaning against a bias relocates
it rather than removing it. The prior is reasoned from the mechanism — a strict conjunctive
query — and will be scored either way.

## Limitations — unchanged from PREREG-1, and still declared

Seed set is a subset of each review's includes; n is small (20 reviews, ~106 seeds); PubMed
only, so this is a lower bound on a full multi-database search; seeds come from a benchmark
corpus, so this measures the method rather than our corpus's actual screening.
