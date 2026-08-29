# The review pipeline, as a component recipe rather than a page

Written before building further, because a hand-crafted page teaches nothing transferable.

## The order

```
1  BUILD          generator emits the page from the object
2  DEFECT SUITE   gate10 (18 classes, 0.33s) + the 13 undefended classes as they land
3  FIX            defects fixed at the class, not the instance
4  PRE-JUDGE      the register rules as an executable checklist, not a document
5  JUDGE BLIND    comparator found, anonymised, randomised, three families, scorecard
6  ITERATE        every new defect a judge or reviewer finds becomes a class, a plant, a check
```

**Steps 2–4 are a GATE, not a competitor to the clinical build.** The risk this ordering exists
to prevent is that pivoting to the axes the judges score quietly drops two days of defect work.
A page does not reach step 5 until it passes step 4.

## The pre-judge checklist — the register rules, made executable

A page is refused, not warned, if any of these fails:

| # | check | why it exists |
|---|---|---|
| 1 | no statistic appears twice with two values | the same number rendered from two paths |
| 2 | no narrative sentence contradicts its own table | prose written before the table changed |
| 3 | **no denial of something the page holds** | 92 pages denied a protocol we had |
| 4 | no assertion of something the page lacks | the derive-or-refuse rule |
| 5 | the estimand is named | binary pooled where the trials used time-to-event |
| 6 | both interval methods shown, and the HKSJ named as modified | the q\* floor |
| 7 | every number traceable to a field or a quoted sentence | the audit trail, mechanised |
| 8 | non-inferiority designs disclosed with their margin | gate 10 |

⭐ **And this is scoreable, which is the point.** *"This review passed N automated integrity
checks covering M known defect classes; here is the list"* is a fact a judge can weigh — like
the blind comparison, and unlike an assertion that we are rigorous.

## The blind comparison as a published component

Not a script for this page. Five parts, each reusable:

| component | input | output |
|---|---|---|
| **comparator-finder** | the topic's PICO | the best published synthesis of the same question |
| **PICO matcher** | comparator document | the section matching our PICO, not the parent review |
| **anonymiser** | both documents | branding, journals, authors, running heads stripped; residual-mark count asserted **0** |
| **randomiser** | both documents | A/B order varied per judge, mapping recorded |
| **three family calls** | prompt file | axes and weights *before* verdict; per-axis winner; what would change its mind |
| **scorecard** | three verdicts | by document, by family, by position |

⛔ **The condition that makes it honest: the verdict is published whichever way it goes, with
the axes we lost on.** A scorecard printed only when we win is marketing, and it would destroy
the only thing being sold.

⚠️ **And it answers the control's own finding.** No judge named verifiability as an axis when we
*asserted* it. A blind cross-family comparison result is not an assertion — it is content, and
content is what they score.

## ⚠️ Audit of v2: what actually generalises, and what does not

Labelled honestly. **The bespoke rows are the ones that will fail silently at review twenty.**

| improvement | class | scales? |
|---|---|---|
| Absolute effects per 1000 + NNT | **(a) generator** | ⚠️ **arithmetic is trivial — the INPUT is not.** Only **6 of 178** stored per-trial records carry the arm counts this needs. Generator-ready, data-blocked on 97% of the corpus. |
| Estimand named (binary vs time-to-event) | **(a) generator** | ✅ derivable from the stored measure and design |
| Both intervals, HKSJ named as modified | **(a) generator** | ✅ already implemented |
| Non-inferiority disclosure + margin | **(a) generator** | ✅ gate 10, 35 topics detected |
| Registry-vs-adjudicated counts, and the difference it makes | **(b) extraction** | ⚠️ needs the trial's **primary report**; we hold one for **31 of 317** documents |
| Safety and other outcomes | **(b) extraction** | ⚠️ **partly bespoke here.** Two rows are primary reads; **four are lifted from the comparator's own table.** That is not repeatable where no comparator exists — and where one does, we are reporting their extraction, not ours. |
| Age-stratified subgroups | **(b) extraction, per-topic evidence** | ⚠️ requires full text **and** the trial to have reported strata. Available here; not generally. |
| "What has happened since" currency | ⛔ **BESPOKE** | **I hand-wrote EMA 16+, WHO, REACH, iMatter from a briefing.** There is no component that finds what changed since a comparator's search date. **This is the clearest scaling failure in v2 and it is one of the strongest sections on the page.** |
| Clinical reading | ⛔ **BESPOKE** | prose written by hand from domain knowledge. Templating it from stored fields is possible and is not done. |

### What this audit says

**Two of the strongest sections in v2 — currency and clinical reading — are bespoke.** They are
also, on the control's evidence, on the highest-weighted axes. ⇒ **The pilot is currently
winning on exactly the parts that do not yet scale**, which is the opposite of what a pilot is
for, and it is better to know now than at review twenty.

**Three components would fix most of it:**

1. **A currency component.** Input: comparator's search date + the topic's intervention.
   Output: regulatory decisions, guideline changes and new trials since that date, from sources
   we already query. This is the single highest-value missing component.
2. **A per-outcome extraction component** driven by the outcome names in the object, so safety
   and secondary outcomes come from the trial reports rather than a comparator's table.
3. **A subgroup component** that reports strata where the trial reports them and refuses where
   it does not — with "not reported" as a first-class result rather than an omission.

⚠️ **And all three are gated by the same upstream fact: we hold the primary report for 31 of
317 documents.** Every extraction component is limited by that number, so **the retrieval fix
is not a separate workstream — it is the precondition for the whole recipe.**
