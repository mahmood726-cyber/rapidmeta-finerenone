# Embase calibration — result log

**Logged as it arrives, prediction first, so nothing can be quietly adjusted afterwards.**

---

## 1. ⚠️ THE PREDICTION MISSED ON THE RECORD COUNT. Recorded before the export landed.

| quantity | predicted | observed | verdict |
|---|---|---|---|
| Embase records | **300–700** | **1,044** unrestricted | ⚠️ **OUT OF RANGE — MISS** |
| trials judged ELIGIBLE (M) | 2 | *pending export* | open |
| of those held by free sources (N) | 2 | *pending export* | open |
| recovery N/M | 100% | *pending* | open |
| additional eligible trials | 0 | *pending* | open |

**The record-count half of my prediction is wrong and stays on the record as wrong.** It
was a falsifiable number, it was falsified, and the half that matters — eligible trials —
is untouched and still open. A prediction that only counts when it wins is not a
prediction.

### ⚠️ BUT THE MISS IS NOT YET ATTRIBUTED, AND ATTRIBUTION COMES BEFORE INTERPRETATION

Two candidate causes, and they are not the same finding:

**(a) My estimate was simply too low** for the strategy as written — plausible, because the
Emtree term turned out to expand far more widely than I allowed for (section 2).

**(b) A BROADER QUERY WAS EXECUTED THAN THE ONE I SUPPLIED.** The run is reported as a
*"single combined line"* with *Map Term to Subject Heading* **off**, and Ovid flattened one
level of nesting. My sheet was 19 numbered lines in which the drug block is **ANDed** with
the HIV block and with the vaginal-ring block (lines 16, 17). A single combined line built
as an **OR across all concepts** would return far more, and 1,044 would then be a fact
about a different search.

⇒ **I am not treating 1,044 as a measurement of my strategy until the EXECUTED string is
recorded.** Ovid reports the string it ran; that string, not the one I wrote, is what goes
in the protocol and what the count belongs to. ⚠️ *A number attributed to the wrong query is
the same defect as a finding attributed to the wrong trial, and this project has already
met that one today.*

**Requested:** the executed search string exactly as Ovid reports it, and the per-line
counts from the saved history.

---

## 2. ⭐⭐⭐ THE EMTREE FINDING — CONFIRMED BY EXECUTION, NOT ASSERTED

I refused to claim `dapivirine/` was an Emtree preferred term because I cannot see licensed
vocabulary from here, and built the strategy to survive its absence. **It mapped.** Ovid's
own *"Search terms used"* list, verbatim:

```
4 [4 (2,4,6 trimethylanilino) 2 pyrimidinylamino]benzonitrile
4 [4 (2,4,6 trimethylanilino) 2 pyrimidylamino]benzonitrile
4 [4 (2,4,6 trimethylanilino)pyrimidin 2 ylamino]benzonitrile
4 [[4 [(2,4,6 trimethylphenyl)amino] 2 pyrimidinyl]amino]benzonitrile
4 [[4 [(2,4,6 trimethylphenyl)amino] 2 pyrimidyl]amino]benzonitrile
4 [[4 [(2,4,6 trimethylphenyl)amino]pyrimidin 2 yl]amino]benzonitrile
[broader terms] · [narrower terms] · [used for]
dapavirine · dapivirine · r 147681 · r-147681 · r147681
tmc 120 · tmc-120 · tmc120 · dpv
nonnucleoside reverse transcriptase inhibitor · pyrimidine derivative
anti human immunodeficiency virus agent · drug implant
female contraceptive device · ring, vaginal · rings, vaginal · vaginal ring
```

**Embase holds a full Emtree drug term that expands to SIX chemical-name variants plus
broader, narrower and used-for relations. MEDLINE holds only a Supplementary Concept
Record, which does none of that.**

⭐ **This is the worked example of why "translated by assumption" is not a search.** The
asymmetry is not "Embase has more records" — vague, and easy to wave away. It is a named
mechanism: **a record indexed only under `4-[[4-[(2,4,6-trimethylphenyl)amino]pyrimidin-2-
yl]amino]benzonitrile` is invisible to any strategy that searches the word *dapivirine*.**
A free-source search using the INN and the development codes reaches the first eleven terms
in that list and not the six chemical names.

⚠️ **AND THAT IS A CONCRETE, TESTABLE MECHANISM FOR A MISS — which makes it far more useful
than a coverage complaint.** It generates the question the calibration must now answer: *are
there records in the 1,044 that carry ONLY a chemical-name form?* If yes, that is exactly
where an Embase-only trial would hide, and it is checkable in the export.

⚠️ **It does NOT yet mean a trial was missed.** Six chemical synonyms of one drug are a
retrieval mechanism, not a trial. Whether any of them carries an *eligible* trial our search
lacks is the open question, and it is answered by the blinded screen, not by this list.

---

## 3. What is prepared for the export

* **`scripts/embase_calibration_screen.py`** — parses the RIS, deduplicates, extracts
  registry identifiers, flags records whose only drug mention is a chemical-name form, and
  emits the screening worksheet.
* **The screen is BLINDED to provenance by construction:** the worksheet carries no column
  for "we already hold this". The join to our included set happens only *after* eligibility
  is fixed, in a second pass, so an eligibility judgement can never be a judgement about our
  own performance.
* **`scripts/search_coverage_fraction.py` refuses** to emit a recall figure while any
  difference is unattributed — it is already refusing on this question because two PACTR
  registrations cannot be attributed from a page that serves a 3,679-byte JavaScript shell.

## 4. Two numbers, and what each denominator is OF

* **1,044** — records returned by the executed Embase query, unrestricted, no human limit,
  no date limit. ⚠️ A count of **RECORDS**, not trials, and not yet attributed to a
  strategy string (section 1).
* **Human-limited count** — pending; an *"Invalid setting"* alert appeared on the limits
  attempt. If the limit will not apply, the unrestricted 1,044 is exported and the
  2026-08-18 cut is applied on my side from each record's own dates, which was the plan
  regardless. **Then the Ovid limit is the cross-check on my filtering rather than the
  source of the number.**
* **M**, the calibration denominator, is neither of those. It is **trials** the blinded
  screen judges eligible for *"randomised comparison of a dapivirine vaginal ring against a
  placebo vaginal ring, reporting HIV-1 seroconversion"*.
