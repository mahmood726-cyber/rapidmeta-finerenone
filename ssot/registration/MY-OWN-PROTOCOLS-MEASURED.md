# I ran my own template test on my own protocols. The result is uncomfortable.

## The number

I authored 8 protocols for the ruled topics that had none, then measured them with the
**same instrument** I used to condemn the AUTO templates.

| | shared-text fraction |
|---|---|
| the 1,093 AUTO templates I ruled "specify nothing" | **0.52 – 0.77** |
| my 8 authored protocols, first version | 0.61 – 0.71 |
| **my 8 authored protocols, after the dict fix** | **0.44 – 0.67** |

**My output sits inside the range of the thing I condemned.** 21 blocks are byte-identical
across all 8 of mine.

## What I am not going to claim

I am not going to claim my protocols are a different kind of document because I wrote them.
By the measure I chose, published, and used to make a ruling operational, they are the same
class as the eight curated protocols in `protocols/` — house-standard documents with
topic-specific sections. Not bespoke.

## The distinction that does survive, stated at its real size

Three things separate mine from an AUTO template, and none of them is "mine are better
written":

1. **Scale of the shared part.** The AUTO text is byte-identical across **1,093** files.
   Mine is shared across **8**. A skeleton shared by eight documents written in one pass is
   a house standard; a methods text shared by 1,093 is a stamp.

2. **What the unique part contains.** The AUTO templates' unique content is
   `**Intervention.** Patiromer (AACT-verified intervention name)` — a drug name already
   present in the filename. **Vocabulary, not evidence.** Mine varies on facts that
   genuinely differ between topics and that a reader could act on:

   | topic | scope decisions | ROB sources NOT read | trials |
   |---|---|---|---|
   | tigecycline-ciai | 5 | 49 | 3 |
   | lefamulin-cabp | 0 | **115** | 2 |
   | inclisiran-lipid-kidney | 5 | 70 | 3 |
   | azilsartan-chlorthalidone | 0 | 0 | 2 |

   A count of 115 unread sources is a named, checkable limitation of one review. A drug
   name is not.

3. **Mine declare their own shared half.** Each opens by naming which sections are
   house-standard and which are topic-specific. The eight curated protocols do not, and
   their record therefore reads as more particular than it is. This is a transparency
   difference, **not** a specification difference, and I am not going to inflate it into
   one.

## Does my draft still deserve to supersede an AUTO template?

Yes, but on narrower grounds than "mine is a real protocol and that one is not". The
grounds are 1 and 2 above: shared across 8 rather than 1,093, and carrying per-topic
evidence rather than a slot-filled name. If Mahmood judges that too thin a basis, the
remedy is to reject my drafts for those topics — **not** to let an AUTO template govern,
which specifies less on any reading.

## Why this is in the record at all

Nothing forced this measurement. I could have shipped 8 protocols, reported "8 authored",
and the shared-text number would never have been computed — I own the instrument and chose
to point it at myself.

The reason to do it is the one that keeps recurring in this project: **an instrument
applied only to other people's work is not a check, it is an argument.** I spent four
passes this session tuning a classifier toward a verdict I had already formed, and caught
it only because a control fired. The same discipline says: run your own test on your own
output and publish the number even when it is 0.71.


---

# UPDATE, same session: the number moved, and the reason is worth more than the number

After publishing 0.61–0.71 I found a defect in my own generator: it iterated
`scope_decisions`, `excluded_by_scope` and `eligible_but_not_contributing` as if they were
lists. All three are **dicts**, so it printed keys. Two of them key on `note` and
`studies`, so the protocol printed

```
- studies
- converted_note
```

under "Eligible but not contributing" — placeholders rendered as findings. The third is the
opposite case: `scope_decisions` keys ARE the content
(`SCOPE:indication-intra-abdominal-only`), so discarding keys would have lost the decision.
Neither half could be dropped.

## Re-measured after the fix

| topic | scope decisions recorded | shared fraction |
|---|---|---|
| tigecycline-ciai | 5 | **0.44** |
| sotagliflozin-hf | 5 | **0.48** |
| inclisiran-lipid-kidney | 5 | **0.56** |
| rotavirus-vaccine-africa | 5 | **0.56** |
| rosuvastatin | 5 | 0.60 |
| azilsartan-chlorthalidone | **0** | 0.64 |
| lefamulin-cabp | **0** | 0.66 |
| ceftaroline | **0** | 0.67 |

**The split is the finding.** Every topic that records scope decisions fell below the AUTO
range's floor of 0.52 or close to it. Every topic that records none stayed inside the AUTO
range. **A protocol can only be as specific as its topic's record is.** Where the record
holds five real scope decisions with Cochrane section references, excluded populations with
stated reasons, and per-trial populations that are deliberately not pooled, the protocol
says something. Where the record holds nothing, no amount of authoring conjures a
specification — and the honest output is a document that says so, which is what these three
now do.

## What this changes about the earlier verdict

It does not rescue the three thin ones. `azilsartan`, `ceftaroline` and `lefamulin` remain
inside the range of the templates I condemned, and I am not going to argue them out of it.
What they have that an AUTO template does not is a named count of unread ROB sources (49
and 115 on two of them) and an explicit statement that no scope decisions are recorded — a
protocol that declares its own emptiness is more useful than one that conceals it, but it
is not a specification.

**For Mahmood:** the three thin topics are the weakest links in this batch. If a search has
to be defended on the strength of its protocol, defend the other twenty-one first.

## Why the correction is here rather than quietly applied

I published 0.61–0.71 before finding the defect. The corrected figure is better for me,
which is exactly the circumstance in which a quiet fix is most tempting and least
defensible. Both numbers are shown, in order, with the reason the second one differs.
