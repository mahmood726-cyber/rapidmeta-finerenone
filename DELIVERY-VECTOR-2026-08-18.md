# Delivery as a vector: the tab-occupancy census

2026-08-18. Mahmood opened `sglt2-hf` — the flagship — and photographed two tabs. Both
read *"Not held in this object."* His words: **"all incomplete."**

He is right, and the correction lands on the measure, not on the pages.

---

## What "115 of 116, gated live" actually asserted

`content_gate` asserts that a pooled estimate's point, interval and I² appear as literal
text in the **served** bytes. `verdict_gate` asserts the object's own verdict reason
appears there. **Both inspect one slot.** Neither says anything about the other seven.

So the number was true and meant: **the headline slot is right on 115 pages.** It did not
mean 115 topics a reader can open and find populated — which is exactly the distinction
`delivery-is-not-audit` exists to preserve, lost again one level up, **on the night we
re-measured.**

---

## The matrix

115 pages measurable × 8 tabs. `H` = held with content; `–` = renders "Not held".

| Tab | HELD | NOT HELD |
|---|---:|---:|
| 1 Protocol | **115** | 0 |
| 2 Search | **1** | 114 |
| 3 Screening | **4** | 111 |
| 4 Extraction | **110** | 5 |
| 5 Analysis Suite | **115** | 0 |
| 6 Scientific Output | **9** | 106 |
| 7 Paper Studio | **1** | 114 |
| 8 Statistics | **1** | 114 |

**Distribution of tabs held per page**

| tabs held | pages |
|---:|---:|
| 8 / 8 | **1** |
| 5 / 8 | 3 |
| 4 / 8 | 5 |
| 3 / 8 | **101** |
| 2 / 8 | 5 |

**One page in the corpus holds all eight tabs: `ARNI_HF_REVIEW.html`.** One hundred and
one hold exactly three — Protocol, Extraction, Analysis — and nothing else.

The flagship `SGLT2_HF_REVIEW.html` holds five: Protocol, Screening, Extraction, Analysis,
Scientific Output. **Search, Paper Studio and Statistics all refuse**, which is precisely
what the photographs show.

---

## The delivery number, stated as a vector

- **115** pages with a **gated headline** (pooled values or verdict reason verified in the
  served bytes)
- **115** with a populated **Analysis Suite**
- **115** with a populated **Protocol**
- **110** with populated **Extraction**
- **9** with **Scientific Output**
- **4** with **Screening**
- **1** with **Search**
- **1** with a **manuscript** (Paper Studio)
- **1** with **Statistics**
- **1** page complete across all eight

**One number for eight slots is what let this hide.** No single scalar can carry this, and
any scalar we quote will be read as the largest of these.

---

## The empty tab is not the failure

The absent-state text is worth quoting because it is ours and it is right:

> *"Not held in this object. A manuscript belongs to one review, or none from another
> review is shown here — this tab is empty of content rather than filled with someone
> else's."*

**That is the architecture working exactly as intended.** It refuses rather than borrows.
A tab that silently rendered a neighbouring review's manuscript would look complete and be
a fabrication; a tab that says "not held" looks incomplete and is honest. **We built the
right behaviour and then failed to count it.**

The failure is entirely in the counter: it asked one question, got a true answer, and that
answer was read as a claim about the whole page.

---

## The census got its own first run wrong

`SOTATERCEPT_PAH_AUTO_2.html` was scored **0 of 8 tabs held**. It holds seven. The page
uses `class="tab-panel"` markup from an older builder generation that the census's regex
cannot see.

**A census that cannot read a page must say so rather than score it zero.** Reporting "no
tabs" for "markup I do not recognise" is the same error the census was built to find,
committed by the instrument built to find it — the fourth time this week an instrument
produced the defect it was pointed at. It now reports that page as **not measurable**,
separately from the 115, and the totals above exclude it.

---

## Not fixed tonight, deliberately

No manuscript has been generated to fill a tab. `tabbed-shell-not-in-ssot-generator`
records that restoring tabs needs Mahmood, and content conjured to satisfy a counter is
the overreach direction — it would convert an honest refusal into a fabricated
completeness, which is strictly worse than the state we are in.

**Measure first. The fix is a separate decision and it is his.**
