# Inventory: handlers that turn an unreadable payload into a plausible value

> ## ⛔ THE CAVEAT THAT BELONGS ON A LARGE SHARE OF EVERYTHING THIS PROJECT HAS QUOTED
>
> **186 `continue` handlers sit in programs whose entire output is a COUNT.**
>
> **Any figure from one of those is a count of objects that HAPPENED TO PARSE, and the
> output cannot show the difference.**
>
> A corrupt file, an unreadable file and a file that was never there all leave the loop by
> the same door, and none of them leaves a mark in the number that gets reported.

**253 `except` blocks return a default immediately after a file or payload read.** Listed,
not fixed — the point is to name what each one CONFLATES, because in every case one value is
standing in for two different facts about the world.

⭐ **THE WORKED EXAMPLE IS ALREADY IN THIS REPO**, which is why it is worth converging on
rather than arguing about. `ssot/growth_guard.py:93`:

```python
except OSError as exc:
    return NOT_ASSESSABLE, "Could not read the delivered page (%s)." % exc
```

**A named state carrying the reason** — not a default, not a bare `None`, and not a value a
caller can mistake for a measurement. Everything below should end up looking like that.

⭐ **AND THE ENFORCEMENT NOW EXISTS**: `ssot/population.py` provides `read_payload()` (four
distinguishable states, and it flags a truncation at a power-of-two boundary), `sweep()`
(walks with a full accounting), and `assert_parts_sum()` which RAISES. Lifted out of
`ssot/screening_ledger.py`, which was the only place in the repo enforcing it. **A convention
asking 253 authors to remember has already failed 253 times.**

Prompted by a live instance:

    evidence/acquisition/NCT03045406/registry.txt   (CARAVAGGIO)
       HEAD  123,891 b   parses
       WORK   32,768 b   fails at char 32,729      <- 2^15 EXACTLY, a buffer-boundary cut

⭐ **THE DISK-FULL CLASS IN ITS DANGEROUS FORM: not a zero-byte file, a PLAUSIBLE-SIZED one.**
Every "is it non-zero" check passes it. And the reader does

    try:    d = json.loads(raw)
    except Exception:  return None

⇒ **`None` for a CORRUPT payload is the same value as `None` for a file NEVER FETCHED**, so
the sweep files it under *no registry payload*. A claim derived from a truncated source is
not a claim with a missing source — **it is a claim whose source LIED ABOUT ITS
COMPLETENESS**, and the record cannot currently tell the two apart.

---

## The five classes, by what they conflate

| default | n | conflates | consequence |
|---|---:|---|---|
| `continue` | **186** | "unreadable" with "not in the population" | **the denominator shrinks silently** — the reach-vs-coverage defect, in a loop |
| `pass` | 26 | "failed to parse" with "nothing to do here" | the failure leaves no trace at all |
| `return None` | 25 | "corrupt", "absent", and "fetched but empty" | the CARAVAGGIO case: three facts, one value |
| `return []` / `return {}` | 13 | "could not read" with "read, and it was empty" | an empty result is reported as a finding |
| `return False` | 2 | "could not check" with "checked, and it is false" | **worst for a gate** — a gate that cannot read its input reports a pass |

Distribution: `scripts/` 233 · `ssot/` 18 · root 1 · `tests/` 1.

---

## What this does and does not put at risk

⭐ **`scripts/grade_blocker_census.py` contains NO except block — it fails loudly.** So the
numbers quoted from it tonight are NOT over a silently-reduced denominator:

    54 live results, 1 -> 4 RATED, counterfactuals 6/4/31

That was worth checking rather than assuming, because the census is the instrument behind
every certainty claim made tonight.

⚠️ **But 186 `continue` handlers sit in `scripts/audit_*` and `scripts/*_sweep.py`** — the
programs whose entire output is a count. Any corpus figure from one of those is a count of
*objects that happened to parse*, and the difference is invisible in the output. Examples:
`audit_exclusion_by_absence.py` (three), `audit_mixed_contrast_pools.py`,
`audit_property_coverage.py` (one of which returns **False**), `ambiguous_field_sweep.py`.

---

## ⛔ ONE OF THESE IS NOT A LOST FINDING — IT IS A MANUFACTURED ONE. FIXED.

`scripts/audit_property_coverage.py`, `in_hook()`, returned **`False` on `OSError`**.

**A coverage check that CANNOT OPEN the hook file reported "this module is not wired in"** —
indistinguishable from having read the hook and found it absent. It does not shrink a
denominator; **it invents a negative.** One unreadable file would have reported *every*
module unwired, and the output would have read as a coverage collapse rather than a failed
read.

⚠️ **And the correct rule was already written twenty lines below, in the same file**, in
`runs_green`'s own docstring: *"an absent or unrunnable file is an absence of evidence and
the house rule is that absence is not zero."* **The rule was stated in this file and
violated in this file.** A convention held in prose does not bind the function next to it.

Fixed rather than queued: `in_hook` is now tri-state (`True` / `False` / `None`), `None`
propagates as NOT_ASSESSABLE with its reason attached, and the close test is `wired is True`
so an unknown can never close a property. Verified unchanged where the hook is readable
(4 CLOSED / 2 PARTIAL / 16 OPEN), and `None` where it is not.

---

## The fix, stated once rather than applied 253 times

**`RETRIEVED_CORRUPT` must be its own state**, distinct from `NO_PAYLOAD` and from
`RETRIEVED_NO_VALUE`. Same shape as `INDETERMINATE` vs `FAILED`, and the third time in one
night that a single value has stood in for two facts (the others: `exit=None` reading as
FAILED, and `poolable: false` reading as a refusal).

Minimum viable change at a read site:

```python
try:
    raw = open(p, encoding="utf-8").read()
except OSError:
    return {"state": "NO_PAYLOAD", "path": p}          # never fetched
try:
    return {"state": "RETRIEVED", "value": json.loads(raw)}
except ValueError as exc:
    return {"state": "RETRIEVED_CORRUPT", "path": p,   # fetched, and it LIED
            "bytes": len(raw), "failed_at": getattr(exc, "pos", None),
            "why_it_matters": ("a plausible-sized truncation passes every non-zero check; "
                               "2^15 and 2^16 boundaries are the tell")}
```

And in a sweep, **the skip must reach the denominator**: count `corrupt` alongside
`examined`, and report `examined + corrupt + skipped == candidates`. That is the same guard
as `ssot/screening_ledger.py` refusing when its ledger disagrees with its declared
denominator — *a component that renders a subset of a declared whole must refuse when the
parts do not sum.*

---

## Audited first: the provenance modules themselves

A provenance module that silently defaults on an unreadable source would launder a
corruption into a clean record, which is the worst possible place for this idiom.

    ssot/claims.py             0 except, 0 file reads    -- cannot launder anything
    ssot/screening_ledger.py   0 except                   -- refuses on a denominator mismatch
    scripts/check_page_format.py 0 except
    ssot/growth_guard.py       1 except -> returns NOT_ASSESSABLE **by name**, with the
                               OSError text. A named state, not a silent default.

⚠️ **One of mine is in the list and it is not exempt:** `ssot/count_bases.py:268` does
`except Exception: continue` inside its corpus sweep, so an unparsable object leaves that
count invisibly. Pre-existing rather than added tonight, and it is on the same list as the
other 252.
