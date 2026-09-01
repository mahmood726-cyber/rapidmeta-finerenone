# HANDOVER: two live defects in `scripts/build_portfolio_index.py`

**Do not run this generator until both are fixed.** `outputs/portfolio_index.json`
was repaired on 2026-09-01 by pruning and deriving rather than regenerating,
precisely because a regenerate would have baked both defects into a fresh index.
Regenerating would have looked like the thorough option and been the worse one.

Both were MEASURED, with the commands. Neither is inferred.

---

## Defect 1 — `NCT_RE` matches nothing, and it zeroes three headline counters

```python
NCT_RE = re.compile(r"'(NCT\d{8})'\s*:")     # scripts/build_portfolio_index.py:28
```

It requires an NCT id to appear as a **single-quoted JavaScript object key**. The
pages emit registry hyperlinks and table text instead.

**Measured:** zero matches against `ARNI_HF_REVIEW.html`, a page containing **93
distinct NCT ids**.

```
git show origin/main:ARNI_HF_REVIEW.html | grep -c "'NCT[0-9]\{8\}'\s*:"     -> 0
git show origin/main:ARNI_HF_REVIEW.html | grep -oE 'NCT[0-9]{8}' | sort -u | wc -l -> 93
```

**Blast radius.** `ncts` comes out empty on every row, and three separate
counters are all derived from it:

```
n_trials         = len(ncts)
integrity_flags  = sum over ncts
n_with_baseline  = sum over ncts
```

So one dead regex renders the dashboard's `Trials`, `With integrity flag` and
`With AACT baselines` tiles as `0`. **Each row stays internally self-consistent**
(`n_trials == len(ncts)` holds on all of them), which is why no single-field
check could see it: the arithmetic is correct and the input is empty.

**When fixing:** match the id itself, not a syntactic frame around it, and add a
control that plants a page with a known NCT count and asserts the parser finds
exactly that many.

---

## Defect 2 — `bucket_of()` is a substring guess, not a lookup

`bucket_of()` scans a hand-ordered list of keyword lists and takes the first
substring hit anywhere in the topic stem. Measured mis-joins:

| topic | filed as | because the scan matched |
| --- | --- | --- |
| `AZILSARTAN_HTN` | ID/Vaccine | `ART` inside azils**art**an |
| `ROTAVIRUS_VACCINE_AFRICA` | Cardiology | `AF` inside **af**rica |
| `CHOLERA_OCV` | Cardiology | `CV` inside o**cv** |
| `ROXADUSTAT_ANEMIA_CKD` | Cardiology | `MI` inside anae**mi**a |
| `UPADACITINIB_RA` | Cardiology | `PAD` inside u**pad**acitinib |
| `HIV_TB_COINFECTION_ART_TIMING` | Cardiology | `MI` inside ti**mi**ng |
| `RHEUMATOID_ARTHRITIS` | ID/Vaccine | `ART` inside **art**hritis |

**The topic id is already a correct key.** It is being used as free text to
*infer* a label rather than to *look one up*. Ordering makes it worse: Cardiology
and ID/Vaccine sit near the front, so short tokens in those lists capture topics
belonging to specialties further down.

**When fixing:** replace the scan with an explicit `topic -> bucket` map, and
fail loudly on an unmapped topic rather than defaulting to `Other`. A default is
how a wrong label becomes invisible.

---

## Related: the same class, three times in one night

`azils`**art**`an -> ART`, `re`**vision**`s -> vision`, `INCRETIN_HFpEF` upcased
to `INCRETIN_HFPEF`. **An unanchored substring over an identifier is the most
repeated defect in this repository.** Any new pattern over a topic id, filename
or NCT should be anchored, case-checked, and given a planted control before it
ships.
