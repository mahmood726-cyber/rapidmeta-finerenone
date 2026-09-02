# The comparator-seed firewall

**Status: declared before any reference list was fetched. This file and
`outputs/comparator_seed_firewall.json` are the first commit on
`feat/comparator-seeded-retrieval`; every fetch in this lane happened after it.**

---

## The rule

> **A topic seeded from a published comparator can never be scored against that
> comparator. Corpus-building topics and scored topics are disjoint sets,
> declared before either runs.**

Otherwise we mark ourselves on their homework: we would take a review's included-study
list, ingest it, and then report that our `k` now matches theirs. That number would
measure copying, not retrieval.

Two exclusions follow, and both are enforced from
`outputs/comparator_seed_firewall.json`, not from anyone remembering:

| | rule |
|---|---|
| **Topic side** | a corpus topic is seedable **iff** `norm(topic)` is not in `scored_topics` |
| **Comparator side** | a published MA is usable as a seed **iff** its DOI is not in `scored_comparator_dois` |

`norm()` collapses `Acs Antiplatelet`, `ACS_ANTIPLATELET_REVIEW.html` and
`acs-antiplatelet-review` to one key, and strips the `_AUTO_FULL_REVIEW` /
`_AUTO_REVIEW` / `_FULL_REVIEW` / `_REVIEW` / `_NEW` suffix family, so a topic cannot
re-enter the seedable set by being spelled differently.

## The declared sets (MEASURED, `scripts/comparator_seed/build_firewall.py`)

| | count |
|---|---|
| source records read | 203 (`published_meta_comparisons.json`) + 19 (`published_meta_comparison.json`) + 33 (`benchmark_set.json`) |
| **scored topics — EXCLUDED from seeding** | **238** |
| **scored comparator DOIs — EXCLUDED as seeds** | **194** |
| corpus topics (`_inventory.json`) | 936 |
| **seedable topics** | **778** |

`238 − (936 − 778) = 80` scored labels do not resolve to a corpus file under `norm()`.
They are kept in the exclusion set anyway. **The exclusion set is deliberately a
superset**: a label that cannot be matched to a page is excluded rather than dropped,
because a firewall that fails should fail closed.

`benchmark_set.json` is folded in even though it is a benchmark rather than a
comparison record, because a topic on the benchmark is a topic whose `k` gets quoted.

## Provenance tagging — structural, not a comment

Every trial that enters the corpus by this route carries, **per trial**:

```
found_via        = "FOUND_VIA_COMPARATOR"
seed_source_pmcid = "PMC……"      # the comparator it came from
seed_source_doi   = "10.…/…"
```

It is **never** counted as our own search yield. Any recall or retrieval figure
computed after this lane must partition on `found_via` before it reports a number.
A provenance label that lives only in prose is a claim; this one is a field, and a
record without it is not from this route.

## What this firewall does not do

It does not make a seeded topic worthless — a seeded topic is still a real corpus
improvement. It makes a seeded topic **unusable as evidence about our search**. Those
are different properties and the firewall separates them so that neither can borrow
the other's credibility.

## Rebuild

```
REPO_ROOT=<repo> python scripts/comparator_seed/build_firewall.py
```

Fails closed (`SystemExit`) if `outputs/published_meta_comparisons.json` is absent,
rather than emitting an empty — and therefore permissive — exclusion set.
