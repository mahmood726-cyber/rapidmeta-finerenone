# Census of the 462 unmapped pages — and the reading it depends on

2026-08-18. The 116 mapped pages were the smaller population. These 462 are linked from
`index.html`, carry no SSOT object, and no gate has ever run on them.

---

## An instrument's inability to read must be a distinct state from what it reads

This leads because it decided everything below it.

In the mapped-corpus census, `SOTATERCEPT_PAH_AUTO_2` scored **0 of 8 tabs held**. It holds
seven. The page uses `class="tab-panel"` markup from an older builder generation the
regex could not see. **Zero would have been quoted as the corpus's worst page** — a
finding manufactured entirely by the instrument.

**NOT_MEASURABLE is not a lesser answer than 0. It is a different answer**, and collapsing
them is how a blind spot becomes a finding. Fourth instrument this week to produce the
defect it was pointed at; second tonight, after `CHK017`.

**The prediction held.** Detecting generation *before* counting was the right order:

| Generation | n | reads under the mapped-corpus census? |
|---|---:|---|
| G1 `data-tab=` + JS engines | **449** | **no** |
| No tab markup at all | 13 | n/a — these are tools |

**Not one of the 462 uses the markup the census reads.** A naive run would have scored all
462 as zero — a 462-page version of the same defect, and it would have looked like the
largest finding of the week.

The **13 with no tab markup are not review pages**: `AutoGRADE`, `AutoManuscript`,
`META_DASHBOARD`, `dashboard`, `TrialRadar`, `MetaExtract`, `EVIDENCE_GAPS`,
`audit_table`, `auto-gallery`, `portfolio_pools`, `what_changed`,
`cardiology_mortality_atlas`, and one deliberate redirect stub. So the population is
**449 review pages plus 13 instruments**, not 462 unmeasured reviews.

---

## Structural presence is not occupancy, and here the gap is total

A G1 page carries `<div id="tab-screen" class="tab-content">` in its served bytes and
fills it at load from `ScreenEngine.render()`. **A static reader sees seven tabs on 434
pages and learns nothing about whether any holds content.**

Reporting "7 tabs present" would be the `SOTATERCEPT` error inverted: there the instrument
under-read, here it would over-read. **Both directions are the same defect.**

So the pages were **rendered** in headless Chrome. Systematic sample, every 37th page,
n=12 of 449.

| Tab | held / 12 | status |
|---|---:|---|
| 1 Protocol | **12** | measured |
| 2 Search | **10** | measured |
| 3 Screening | — | **NOT MEASURABLE** |
| 4 Extraction | — | **NOT MEASURABLE** |
| 5 Analysis | **11** | measured |
| 6 Scientific Output | **11** | measured |
| 7 Paper Studio | **0** | measured |
| 8 Statistics | **12** | measured |

### The two not-measurables, and I nearly reported them as zero

My probe returned 0/12 for Screening and Extraction. **That is my probe, not the pages.**
Both engines are triggered *on click*:

```
"screen"===id && ScreenEngine.render(),
"extract"===id && (ExtractEngine.render(), …)
```

A headless load that never clicks a tab will always see them empty. **Reporting 0/12 there
would have been the third instance tonight of an instrument's silence read as a corpus
finding** — caught only because the earlier two made me check the trigger.

**Paper Studio's 0/12 is real**: there is no `PaperEngine` in the file at all. On these
449 pages the manuscript tab has no renderer, which is a stronger statement than "no
manuscript is held."

---

## The delivery vector, extended

For the **449 G1 pages** — sampled, not gated, no object, no check ever run:

- Protocol, Statistics: populated throughout the sample
- Analysis, Scientific Output, Search: populated on 10–11 of 12
- **Paper Studio: zero, with no renderer present**
- Screening, Extraction: **unmeasured**, pending a click-driven probe

Against the 116 mapped pages, where 1 holds all eight tabs and 101 hold three.

**No scalar can carry this, and any scalar quoted will be read as the largest of these.**

---

## The class this belongs to

Two independent measures, both counting existence and reporting occupancy:

- *Coverage claims must name the checks that **emitted**, not the checks that **exist**.*
- *Delivery claims must name the slots that **hold**, not the pages that **render**.*

**The same sentence at two layers.** Not two coincidences — a general defect in how we
count. The census above is the third instance and it arrived by the same route: the
structural reading (449 pages × 7 tabs present) is an existence count, and it would have
been reported as occupancy had the pages not been rendered.

**Predicted fourth instance, not yet looked at:** the artefact registry indexes 603
artefacts *by kind*. That is an existence count over instruments. Whether each artefact is
*reachable* — that any code path actually consumes it — is the occupancy question, and
nothing asks it.

---

## Nothing was generated

No manuscript, no tab content, nothing written to any page. The Paper Studio result on 449
pages is a finding about a missing renderer and is Mahmood's decision, not a gap to fill.
