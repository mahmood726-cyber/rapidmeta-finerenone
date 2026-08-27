# Verdict-only declaration — for the rebuild lane

## The sentence

> This page records a verdict, not a synthesis. Its trials were assessed and found not
> poolable on a common estimand, so no pooled estimate is offered and none is coming;
> what follows is the assessment and its reasons.

## How to emit it

**From `build_mode`, not by editing pages.** A topic whose object carries
`build_mode: "verdict-only"` gets this sentence; nothing else does. Repairing pages one
at a time while the generator keeps emitting the old shape is the half-life problem, and
it has been observed four times on this project in a day.

## Scope, measured

**67 of 155 topic directories carry `build_mode: verdict-only`** — a plurality of the
blocked set, not a handful. 65 of them hold trials somewhere in the object; 2 hold none
anywhere (`emtricitabine-hiv-auto-full-review`, `etesevimab-covid-auto-full-review`).

## The defect it closes

**60 verdict-only topics currently carry review-shaped questions on live pages** — for
example *"Caspofungin Fungal: is a pooled estimate possible?"* A question of that form
implies a synthesis that is not coming. The page is not wrong about any particular
number; it is wrong about what kind of thing it is.

## Why this wording

**"None is coming" is the clause that does the work.** It closes the expectation rather
than deferring it. "No pooled estimate is currently available" invites a reader to wait
for one, and waiting is the wrong response to a topic that was assessed and found not
poolable.

**"Assessed and found not poolable" is the other half.** It distinguishes a verdict from
an absence. A page with no pooled estimate because nobody has done the work and a page
with no pooled estimate because the work was done and the answer was *no* look identical
from outside, and only one of them is a finding.

## What it does not claim

- NOT that the verdict was correct. It reports that a verdict was reached, and points at
  the assessment. Whether `verdict-only` is the right outcome for a given topic is a
  question no field can answer.
- NOT that the topic was searched. Most verdict-only topics hold no executed search at
  all, and the declaration is silent on that rather than implying coverage.
