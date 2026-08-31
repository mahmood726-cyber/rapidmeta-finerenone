# Handoff to the ledger lane — one token, in `ssot/screening_ledger.py`

**Owner: whoever owns `ssot/screening_ledger.py`. I am not editing your file.**

## The change

`render()` line ~112:

```python
'<details class="screen-group"%s><summary>...' % (" open" if g != "EXCLUDE" else "", ...)
```

→

```python
'<details class="screen-group"><summary>...'
```

Drop the ` open`. Every group collapsed, not five of six.

## Why — Mahmood ruled **present-and-collapsed**

As written, `render()` opens every group except EXCLUDE. On the dapivirine page
that is **205 of 1,443 records rendered expanded**:

| group | records | as shipped |
|---|---|---|
| PASS_INCLUDED_TRIAL | 13 | **open** |
| PASS_ALREADY_RETRIEVED | 22 | **open** |
| PASS_OUTSIDE_REGISTRY_SET | 2 | **open** |
| PASS_NO_ID | 61 | **open** |
| UNDECIDABLE | 107 | **open** |
| EXCLUDE | 1,238 | collapsed |

The instinct behind it is sound — *a reader auditing a screen reads the passes
to check them* — and it is the right default for a reader who has opened the
Screening tab on purpose. It is the wrong default for the page as a whole, which
two blinded judges already called **cluttered at 87,000 rendered characters**.

## What it is worth, measured on built bytes

| | all groups open | all collapsed |
|---|---|---|
| screening tab, rendered chars | 525,418 | **23,589** |
| rows present | 1,527 | **1,527** |
| outbound links | 1,453 | **1,453** |

**Collapsed is not truncated.** Every row stays in the bytes and in the saved
file; `Ctrl-F` finds text inside a closed `<details>` in current browsers. Your
no-truncation rule is untouched — this defers records, it does not remove them.

## Why it is a handoff and not a patch

I have applied it **at the wiring** in `build_tabbed.py` tonight, because three
lanes touched your file in one evening and editing it underneath you was the
worse risk. That strip is a `.replace()` on your fragment:

```python
frag = frag.replace('<details class="screen-group" open>',
                    '<details class="screen-group">')
```

⛔ **That is a habit, not a guarantee.** It works only while every caller
remembers to do it, and a collapse that depends on each caller remembering is
exactly the class of thing that failed repeatedly tonight — a rule living in
one call site protects one call site. **The token belongs in your module, where
it holds for every caller including ones not yet written.** Remove the wiring
strip when you land it; it becomes a no-op the moment your version ships, and a
no-op left in place is one more thing a later reader has to work out.

## What not to change

- **The fail-closed denominator guard.** I ran the planted control: a ledger of
  1,442 rows against a declared 1,443 was refused with
  `ledger holds 1442 rows but the denominator declares 1443 -- refusing`.
  That is the difference between shipping 1,443 records and shipping a number
  that says 1,443, and it is why your module was wired instead of mine.
- **No truncation.** Mine carried a declared 4,000-row bound. A bound that never
  fires is still a bound, and on a format whose claim is *every record* that is
  not cosmetic. Yours has none. Keep it that way.
