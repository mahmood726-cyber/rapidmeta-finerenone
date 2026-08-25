# The author-year label always finds the paper, and never identifies it

**A direct author-year → NCT join returned 2%, which reads as "the route does not work".
Split in two, the route works perfectly at one stage and fails completely at the other — and
the stage that fails does so for a reason that has an obvious fix.**

---

## The split

| stage | question | result |
|---|---|---|
| **A** | PMID → NCT, via PubMed's DataBank field | **32 / 34**, null 0%, **0 wrong** |
| **B** | author-year → PMID, via esearch | recall **20 / 20**, resolved **0 / 20** |

Stage A is effectively solved. Stage B is where the join dies.

---

## Stage A: the registration is already in PubMed, in a structured field

PubMed records a trial registration as a secondary identifier:

```
<DataBank><DataBankName>ClinicalTrials.gov</DataBankName>
  <AccessionNumberList><AccessionNumber>NCT01035255</AccessionNumber>
```

Across 34 trials where our corpus holds both ids, that field returned the correct NCT
**32 times**, and — the property that matters more than the rate — **never returned a
different trial's registration.** Zero wrong. Against a deranged pairing the recovery is 0%.

So when the field is present it can be trusted, and it is present 94% of the time.

**This was scanned in the DataBank field only, not across the record.** An NCT also appears
in many abstracts, sometimes another trial's. Scanning the whole record would have inflated
the rate with matches the field does not support — and would have concealed a bug in this
very script, which first reported 0/34 because a placeholder collision shipped the pattern as
`ClinicalTrials\dOTgov`. The implausible zero is what prompted the check.

## Stage B: the label retrieves, but does not identify

A Cochrane label is `Carter 1970` — a surname and a year, and nothing else. Querying
`Surname[Author] AND Year[dp]`:

| | of 20 determinable |
|---|---|
| true PMID returned (**recall**) | **20 / 20 — 100%** |
| returned *and* the set has one record (**resolved**) | **0 / 20 — 0%** |
| returned *and* the set has ≤5 records | 1 / 20 |
| null test (year shifted seven) | **0 / 34** |

Median result set **147**. Six labels return over a thousand; `Chen 2018` returns **66,761**.

**Fourteen of the 34 are NOT MEASURABLE, not misses.** esearch was capped at `retmax=200`,
so for a label returning more than 200 records the true PMID may lie outside the returned
page. Absence there is an artefact of the cap. The 20/20 and 0/20 above are stated on the 20
where the whole set came back and the answer therefore exists.

**The null holds.** Shifting the year by seven recovers the true PMID 0 times in 34, so the
year is doing real work — the label is not merely matching a prolific surname.

---

## What this changes

**The failure is identification, not retrieval.** "2% join" invites the reading that the
lookup is unreliable. It is not: the paper is in the returned set every time the question can
be asked. What is missing is any field that narrows 147 candidates to one.

Thresholds were fixed before the run — n≤1 resolved, n≤5 resolvable with one more field,
n>5 not — so 0/20 is not a threshold chosen after seeing the data.

**The remedy is the same one already identified, and this sharpens why it is cheap.** A
registration column in the extraction schema costs a keystroke at a moment when the assessor
already holds the number (see
`FINDING_COCHRANE_EXTRACTION_HAS_NO_REGISTRATION_FIELD.md`). Everything downstream —
stage A — already works. The gap is one field wide.

**The next thing to test, and it is testable now.** Resolve the label inside the review's
own bibliography rather than against all of PubMed. The extraction schema does ship
`review_doi`, and Crossref returns reference lists for Cochrane DOIs. Matching `Carter 1970`
against the ~40 references of the review that cites it is a different problem from matching
it against 147 papers by every Carter alive that year. That is the measurement to run before
concluding anything about whether the join is achievable without schema change.

---

## Stage B′: inside the review, the same label is nearly unique

The label is never used against all of PubMed. It is used inside one review. Measured across
**61 Cochrane reviews, 4,219 references**:

| | |
|---|---|
| references yielding a surname+year at all | **3,171 / 4,219 — 75%** |
| of those, **unique within their own review** | **3,063 / 3,171 — 97%** |
| sharing a label with another reference | 108 / 3,171 — 3% |

**The same label form that resolved 0/20 against PubMed resolves 97% of the time inside the
bibliography that uses it.** The ambiguity was never a property of the label; it was a
property of the search space we pointed it at.

**This is an upper bound on the ambiguity.** These are whole bibliographies — included
studies, excluded studies, methods citations — not included trials alone. A label competing
only against the included studies of its own review faces a smaller field than 3%.

**No end-to-end rate is computed here, deliberately.** Multiplying 75% × 97% × 94% would
produce a number from three different samples with three different denominators, which is
the exact error this project has corrected twice this week. An end-to-end figure requires an
end-to-end run.

### What the route now looks like

```
Cochrane label "Carter 1970"
   → resolve within the review's own reference list      97% unique  (n=3,171)
   → PMID / DOI of that reference
   → PubMed DataBank field                               32/34, 0 wrong
   → NCT
```

Every step is measured, each on its own sample, and none of them is the direct author-year →
NCT lookup that returned 2%.

**The remedy is still one column.** This route is reconstruction — it works, and it should
not be necessary. The assessor held the registration at extraction time.

---

## Limits, stated

- **34 pairs**, from `inputs.trials` across this corpus where a row carries both a PMID and
  an NCT. Small, and every figure above carries that denominator.
- **The ground truth is our own extraction.** The NCTs were verified against live
  ClinicalTrials.gov records on 2026-08-19 and the PMIDs are a separate field, but a
  systematic mis-pairing on our side would be invisible to this measurement.
- **These are not Cochrane labels.** They are labels *built the way Cochrane builds them*,
  from the first author surname and year in each PubMed record. Cochrane also uses trial
  acronyms (`SHEP 1991`), which are far stronger identifiers; this measurement is therefore a
  lower bound on what a real Cochrane label set would achieve.
- Stage A and stage B are separate measurements and neither number is a join rate.
