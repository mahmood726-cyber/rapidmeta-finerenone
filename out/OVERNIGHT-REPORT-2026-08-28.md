# Overnight report — genstore lane — 2026-08-28

## THE NIGHT'S DIAGNOSIS, ONE MORE TIME: THE IDENTIFIERS WERE ALWAYS THERE

We recorded documents as unreachable while holding the keys to them.

- **55 of 74 PMIDs came from the registration.** Only 18 were stored on objects.
- **All 74 DOIs and 36 PMCIDs came from documents we already held.**
- **No new search was run for any of it.**

Knowledge recorded, connected to nothing — the same diagnosis as every other defect tonight,
and this time it cost roughly a third of our full texts.

## AND THE SAME TRAP CAUGHT ME FROM THE OTHER SIDE, FOUR HOURS LATER

Reading identifiers out of stored records, I took the FIRST doi/pmcid in each — and in a
PubMed record that can be a RELATED ARTICLE rather than the trial's own report. **19 of 74
trials carry an identifier shared with another trial.** Two of the colliding DOIs are provably
not trial reports: `10.1002/14651858.cd011748.pub3` is a Cochrane review, and
`10.1007/s40256-022-00524-x` is the apixaban-in-obesity review **this project identified today
as a CT.gov `DERIVED` reference** — the exact class I refuted a bulk-deletion rule over this
evening, then used as a key.

**So this lane's full-text claim is corrected downward: 45/74 (61%) → 40/74 (54%) defensible.**
Five documents are quarantined, not deleted. Corpus coverage is unaffected: the RoB lane holds
full text for all 29 trials this lane lacked.

---

Written to be true rather than encouraging. Every number carries its denominator. Where a
result is smaller or later than it looks, it says so here rather than in a footnote.

---

## SHIPPED AND SERVED

Verified from the live site with a marker that did not exist before the change, not from a
commit. Site: `https://mahmood726-cyber.github.io/rapidmeta-finerenone/`

| what | evidence | served |
|---|---|---|
| The READY index — 26 cards | banner "What this list selects" | 17:06 UTC |
| Card descriptions are RESULTS, not withdrawal text | "Estimate withdrawn" = **0** on the index | 17:24 |
| AGYW mislabel | card reads "Dapivirine vaginal ring…"; **HPTN = 0, FACTS-001 = 0** | 20:08 |
| Duplicate cards removed (3 pairs) | `0.4941` appears **once** | 20:08 |
| `k=1` reads "Single trial", not "Pooled" | bempedoic card | 20:08 |
| Measure fallback | cards reading "Pooled: estimate" = **0** | 20:22 |
| "checks not measured" → "audit never run" | badge + dated tooltip | 20:43 |
| HFrEF: patient claims, NNT, ranking, integrity score stripped | 0 patient-summary elements even when patient-mode is forced | 17:56 |
| Arm metadata repaired on 5 trials | INVERTED 5 → **0 of 168** | 18:15 |
| Trial name swaps (Ring/ASPIRE, FOCUS 1/2) | all 4 pair with the correct NCT, 0 wrong | 18:27 |
| Read-through to `as_posted` on 13 trials / 6 pages | "read through to this object" renders | 19:36 |

---

## MEASURED, WITH DENOMINATORS

**Anything false on a page — swept, nothing found.**
163 pages in PAGE_MAP · 0 skipped · **0 displayed pooled estimates contradict their object.**
One flag was adjudicated as a rounding artefact (page renders 3 s.f., check demanded 4) by
reproducing the displayed string from the object's own value. The tolerance was left at 4 s.f.
rather than widened: a check tuned until it stops complaining has stopped being a check.

**The READY criterion is now a RESULT, not a list.**
`outputs/ready_index_2026_08_28.json` carries the four legs as the code evaluates them, the
fields each reads, a verdict for all 164 pages, the failing leg per page, and the commit and
date. Arithmetic: **27 pass − 3 deduped + 2 ruled in = 26 cards.**
Reproduced by an independent implementation — Codex was given the legs and forbidden from
reading, importing or running the script: `my_pass=27, artefact_pass=27, disagreements=0`.

**Acquisition — 74 trials across the 26 indexed topics, 74 attempted, 0 skipped.**

| | after first pass | now |
|---|---|---|
| holds the registration | 74 / 74 | 74 / 74 |
| holds a PubMed record | 73 / 74 | 73 / 74 |
| **holds FULL TEXT** | **24 / 74 (32%)** | **40 / 74 (54%) defensible** |

245 documents, 19.1 MB, each stored with its route, retrieval date and sha256.
Newly recovered by route: `ncbi_efetch` 11, `doi_resolver` 9, `pmc_direct` 1.

**The identifier was never missing — three times.** 55 of 74 PMIDs came from the registration
(only 18 were stored on objects); all 74 DOIs and 36 PMCIDs came from documents already held.
No new search was run for any of it.

**Partial repairs — the 50 marker-bearing objects are closed, and not by a sweep.**
45 of 50 have **no second copy at all**; 4 have `as_posted` only; 1 has `pmid_groups` only;
**0 have both**. A repair cannot land on one of two copies where only one exists. Corpus-wide,
only two trials carry both sides with numeric values.

---

## THINGS THAT ARE SMALLER OR LATER THAN THEY LOOK

**The never-trust-one-index rule did not pay off the way it was pitched.** 50 Europe PMC
records declare `isOpenAccess=N`. Trying anyway on every one: **zero yielded full text.** The
index was right in all 50. What trying anyway recovered is an abstract-level PubMed record for
49 of them. The rule stands, but on this corpus it overturned no closed flag, and my first
draft of this claim was the flattering version — it counted the always-available registration
record as "a document we hold".

**"0 divergences" in the partial-repair sweep is a reach of 2.** Only two trial-outcome pairs
were genuinely comparable. That reach travels with the number wherever it goes.

**A 200 is not a document.** All 29 trials still at abstract level return `doi_resolver=200` —
a publisher landing page. An access record built on status codes would have reported 74/74 and
been wrong by 29.

**ARNI is in the index by instruction, not by the criterion.** It fails leg 4 (its stamp
predates all seven required generator commits) and **cannot be rebuilt to pass honestly**: a
rebuild reproduces only 10.5% of the served text and would replace 89.6% with projection. My
first check said "+0.4% text, +3 sections" — a VOLUME measurement that masked a near-total
content swap. HFrEF is likewise in by instruction and fails leg 1 (no store object). Both
carry `verdict: RULED_IN` with `criterion_result: FAIL` and the failing leg named.

---

## BLOCKED, AND BY WHAT

- **FDA/EMA review documents and protocols/SAPs** — not yet attempted. These are this lane's
  two remaining routes and are where the 29 abstract-level trials most plausibly close.
  Not blocked by anything; simply not yet run.
- **`NCT01780987` has no PMID at all** — none stored, none on its registration. Registration
  only.
- **Coordination with the RoB lane — CHECKED, and it is settled.** Its harvest ran (317 rows,
  22:33 UTC) and this lane's 74 trials are a strict SUBSET of its 317. Complement computed:
  it holds full text for **all 29** trials this lane lacks, so the corpus reaches **74/74** and
  this lane should not re-fetch any of them.
- **19 route disagreements between the two manifests, reported not reconciled.** Every one is
  the same direction — theirs `europepmc`, mine `efetch`/`doi`/`pmc`. The cause is that the
  route recorded depends on WHICH IDENTIFIERS THE CALLER SUPPLIES, not only on the retriever.
  **The sanctioned retriever is not the whole access record; the identifier set is part of it.**
  On several of those the character counts differ four- to thirteen-fold, meaning we do not
  hold the same document at all.

---

## NEEDS A RULING

1. **`SGLT2_MACE_CVOT`'s card reads "Multiple trial-declared outcomes"** — derived from the
   object's own title, which is an outcome description rather than a topic name. Not false,
   but poor. Inventing a better one would put a hand-written name back on a card, which is the
   defect that published a real result under the wrong two trials. Left as-is deliberately.
2. **Four negative guards from another lane's file** (`scripts/lane_rob/adjudication_triage.py`)
   were admitted to this lane's baseline as SEEN and explicitly **not** justified, because
   they blocked every commit here and this lane did not write them and has not read them. That
   lane should confirm each absence is the property it means.
3. **19 of the 26 indexed cards render a dated `not ready` flag.** Kept deliberately — it is a
   different property from "carries a pooled result", and it is true. A floor of 19 is enforced
   in the served verifier so the flags cannot be quietly deleted.

---

## STATE

`main` at `c14e97684`. Working tree clean, nothing half-applied, no plant left in place.
Every class-wide change in this report was either completed or not started.
