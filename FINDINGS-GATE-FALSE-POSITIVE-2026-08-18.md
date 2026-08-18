# The gate flagged two. Reading the registrations, **one is a false positive**

`subject_is_experimental_gate` returned FAIL for `DABIGATRAN_AF` and
`FONDAPARINUX_VTE`. Both were read by hand before anything was retired, because
OLMESARTAN was confirmed by reading three registrations and not by a verdict.

**`DABIGATRAN_AF` is a FALSE POSITIVE and is NOT retired. `FONDAPARINUX_VTE` is
confirmed, but as k=1 rather than as the OLMESARTAN shape.**

---

## `DABIGATRAN_AF` — the gate is wrong, and the cause is registry arm-typing

**`NCT00262600` is RE-LY**, the trial that established dabigatran in atrial fibrillation.
Its arms as registered:

| arm type | label | intervention |
|---|---|---|
| `ACTIVE_COMPARATOR` | Dabigatran dose 2 | Dabigatran dose 2 |
| `ACTIVE_COMPARATOR` | Warfarin | warfarin |
| `ACTIVE_COMPARATOR` | Dabigatran dose 1 | Dabigatran dose 1 |

**Every arm is typed `ACTIVE_COMPARATOR`, including both dabigatran arms. None is typed
`EXPERIMENTAL`.** Dabigatran plainly *is* the intervention — the registered primary is
"Yearly Event Rate for Composite Endpoint of Stroke/SEE" and the trial is titled
*"Randomized Evaluation of Long Term Anticoagulant Therapy (RE-LY) With Dabigatran"* —
and the registrants simply did not use the `EXPERIMENTAL` type.

**`NCT04532528` (ReAHEAD)** is a different problem again: both arms receive dabigatran
and **neither arm carries a type at all** (the field is blank). It is an *adherence*
trial — primary outcome *"Number of Patients With High (MMAS-8 Score) Adherence to
Dabigatran Treatment"* — testing whether **education** improves adherence, not whether
dabigatran works.

**So the topic is not comparator-shaped. It is k=1 on a drug-efficacy question** (RE-LY),
with a second trial that asks an adherence question and cannot pool with it. That is a
real verdict and a different one from OLMESARTAN's.

---

## `FONDAPARINUX_VTE` — confirmed in part: one trial is an edoxaban trial

| registration | experimental arm | fondaparinux's role |
|---|---|---|
| `NCT01857583` | **DU-176b (edoxaban)**, three dose arms, all `EXPERIMENTAL` | **`ACTIVE_COMPARATOR`** — genuinely the control |
| `NCT00789399` | *"Fondaparinux Sodium **Versus Placebo**"* | typed `ACTIVE_COMPARATOR` against a `PLACEBO_COMPARATOR` arm — but it **is** the intervention |

**`NCT01857583` is an edoxaban trial** and fondaparinux is correctly identified as its
comparator — that half of the gate's signal is right. **`NCT00789399` is a genuine
fondaparinux trial** whose arm is mis-typed: its own title says *versus placebo*, and the
placebo arm is typed `PLACEBO_COMPARATOR`, so fondaparinux is unambiguously the tested
agent.

**Verdict: k=1 for the fondaparinux question.** Not the OLMESARTAN shape — the topic does
contain a fondaparinux trial — but not poolable either.

---

## The gate has two false-negative modes, and both are now demonstrated

| mode | instance | what happens |
|---|---|---|
| **arm type is not `EXPERIMENTAL` even when the drug is the intervention** | RE-LY types all three arms `ACTIVE_COMPARATOR`; `NCT00789399` types fondaparinux `ACTIVE_COMPARATOR` against placebo | the subject reads as a comparator and the topic FAILs |
| **the drug is named by development code, not generic name** | `NCT01035255` (PARADIGM-HF) labels its arm **`LCZ696`**, so the token `sacubitril` does not match | the subject reads as ABSENT |
| **no arm type recorded at all** | `NCT04532528` (ReAHEAD), both arms blank | everything reads as not-experimental |

**`armGroups[].type` was the right level and is not sufficient on its own.** The fix is to
treat a non-`EXPERIMENTAL` type as *evidence*, not proof: cross-check the brief title
(*"…Versus Placebo"*, *"…With Dabigatran"*) and the presence of a `PLACEBO_COMPARATOR`
arm, and downgrade FAIL to REVIEW whenever the registration types **no** arm
`EXPERIMENTAL`. **Not implemented here** — it needs its own fixture pair, and shipping it
untested is what happened the last time this gate was built in a hurry.

**Consequence for last round's sweep: its FAIL and REVIEW counts are not reliable.** Ten
REVIEW verdicts may contain topics whose subject is genuinely experimental but
mis-typed, and the two "no registration seeded" verdicts were wrong for a third reason
(below).

---

## And a correction to something I reported last round

I said the two sacubitril pages **"seed no registration at all"**. That was wrong. Both
seed `NCT01035255` — **PARADIGM-HF** — which my sweep excluded because that id is on the
shared-runtime-residue list.

**The residue list is topic-blind.** `NCT01035255` is residue on an unrelated page and is
the *genuine trial* on a sacubitril page. Excluding it by name everywhere produced a
"no registration" verdict for a topic that has one.

**So the sacubitril pages are k=1 (PARADIGM-HF), not unidentifiable** — a different and
much less alarming state than I reported. The residue exclusion needs to be conditional
on the topic, not global.
