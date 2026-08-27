# Scoping defects — topics that cannot carry one review question

**These are defects in the corpus as it stands, not future work.** Each is a live page
presenting itself as one review over a set of trials that cannot answer one question.
Each is ready for a ruling in bulk; none needs further investigation to be actionable.

Every one was reached by two model families of different vendors, each shown identical
material and neither shown the other's reasoning, and then checked by hand against the
stored object. Where the two families agreed, that is stated. Where they split, the
split is stated as a split.

---

## 1. `apixaban-af-review` — at least two reviews, and in one of them apixaban is the control

**Both families UNANSWERABLE, stable across four rounds** with different material each
time, so this is not an artefact of what they were shown.

Verified against the object's own arms:

| trial | comparator, as stored |
|---|---|
| AVERROES | acetylsalicylic acid |
| RENAL-AF | warfarin |
| ARISTOTLE | arms stored as `'1'` and `'2'` — no drug identity at all |
| PACIFIC-AF | **BAY2433334 versus apixaban — apixaban is the CONTROL ARM** |

A review cannot pool a drug against aspirin, against warfarin, and against an
unidentified comparator, while one of its trials tests a different drug *using that
review's intervention as the control*. This is at minimum two reviews split by
comparator, and PACIFIC-AF belongs to neither of them as currently framed.

**Also a data defect:** ARISTOTLE's arm labels carry no drug identity. Arm labels that
identify nothing are the same class as every other defect this week.

## 2. `cangrelor-pci-review` — a composite that is not the same composite

Threshold split, resolved toward refusal. CHAMPION-PHOENIX adds stent thrombosis to the
three-part composite used by CHAMPION-PCI and CHAMPION-PLATFORM. **A composite that is
not the same composite is not a shared outcome.** The workaround one family proposed —
all-cause mortality at 48 hours — is a component of differing composites, which is the
pattern that required hand-checking elsewhere and was found not equivalent there.

## 3. `rosuvastatin-auto-full-review` — no shared outcome

Both families UNANSWERABLE independently.

## 4. `finerenone-review` — BLOCKED ON THE OBJECT, not a methodological verdict

**This one has a different owner from the three above.** Its stored question says
**three** trials; the object holds **four**. The question cannot be written because the
object contradicts itself — not because the topic cannot carry one. It goes to whoever
fixes the store, and folding it into a scoping verdict would give a fixable problem a
permanent label.

## 5. Twenty-three further topics, both families UNANSWERABLE

Listed in the run record. Each was independently judged unable to carry a single review
question by two families. They are **not** included above because they have not been
hand-verified the way the four have, and a machine agreement is a candidate rather than
a finding until someone reads the object. Their common causes, from the same run: no
common comparator, registered primaries that are different quantities, and outcomes
deferred to whatever each trial happened to register.

---

## What this set has in common

A page can carry the full apparatus of a systematic review — a question, an included
set, a pooled estimate — over trials that answer different questions. Nothing in the
apparatus detects it, because every part is individually well-formed. It is visible only
by comparing the trials' registered comparators and primaries against each other, which
is what the question-authoring pass did.

**The distinction to preserve when ruling:** a topic that cannot carry one question is a
SCOPING finding and is permanent until the topic is split or rescoped. A topic whose
object contradicts itself is a DATA defect and disappears when the store is fixed. They
look identical from outside and have different owners and different lifespans.
