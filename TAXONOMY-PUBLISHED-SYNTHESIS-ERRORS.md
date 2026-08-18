# Taxonomy of published-synthesis error patterns

**Purpose is prevention, not scoring.** Every pattern found in the published literature
becomes a check we run **on ourselves**. This file is deliberately separate from
`MISTAKE-LEDGER.md`: that one records what *we* got wrong, this one records what the
literature got wrong so that we can look for it in our own work before someone else does.

## The counterweight, and it stays at the top

**Across everything checked so far, the published literature has been right more often
than wrong.** Of four published references checked in detail, **three were correct** —
and in three of our four checked cases the published authors handled correctly the very
thing we had got wrong. A taxonomy of errors read without that sentence attached becomes
a scoreboard, and a scoreboard is not what this is for.

Denominators, so the rate is visible rather than implied:

| | n |
|---|---|
| published references checked in detail | 4 |
| found to carry an error | 1 |
| additional published syntheses read for other reasons and found to carry a pattern | 2 |

**Three instances, three classes. That is enough to name the classes and nowhere near
enough to estimate their prevalence**, and no rate should be quoted from this file.

---

## Class 1 — POPULATION MERGE: two diseases pooled under one heading

**Instance.** A published riociguat review pools **pulmonary arterial hypertension** with
**chronic thromboembolic pulmonary hypertension**. The arithmetic is impeccable; the
pooling is the error. Two different diseases with different natural histories and
different treatment questions, reported as one estimate.

**Why it is hard to catch.** Nothing in the numbers looks wrong. Every check that
operates on the estimate — heterogeneity, publication bias, sensitivity analysis — passes,
because the defect is in **what the numbers are about**, not in the numbers.

**The check we run on ourselves.** The participants limb, read from the registrations
rather than from the topic title. This is exactly the check that closed
`CEFTOLOZANE_INFECTION`, `ERTAPENEM` and `PLAZOMICIN_INFECTION` in our own corpus — and
exactly the check that, applied too literally, nearly closed `MALARIA_ACT`, where five
registry strings describe one disease. **The class cuts both ways and the false-positive
direction is the expensive one.**

---

## Class 2 — HETEROGENEITY REPORTED AND THEN IGNORED

**Instance.** A published olmesartan review pools **final values** across trials, reports
**I-squared = 100%**, and interprets the pooled estimate anyway.

**Why it is hard to catch.** It is not concealed. The number is printed. The failure is
that reporting a heterogeneity statistic was treated as discharging the obligation the
statistic creates. **A disclosure is not a remedy.**

**The check we run on ourselves.** Where I-squared is high, the pooled estimate must
either not be displayed or must carry the consequence in the same sentence as the number.
Handbook 6.5 §10.10.3 and MECIR Box 10.10.a C62 — "undertake (**or display**)" — put the
obligation at *display* time, not at *calculation* time.

**And its mirror, which we have already had to write against ourselves.** At k=2 with
I-squared 0% and tau-squared 0, agreement is **weak evidence**, not strong: two points
cannot demonstrate consistency. Class 2 has a low-k twin where the statistic is quoted in
the reassuring direction on data too thin to support it. `INCRETIN_HFpEF` carries that
caveat explicitly.

---

## Class 3 — FRAMING BROADER THAN THE CONTRIBUTING DATA

**Instance.** Kosiborod et al., *Lancet* 2024;404:949–61 (PMID 39222642) — a
**"pooled analysis of the SELECT, FLOW, STEP-HFpEF, and STEP-HFpEF DM randomised trials"**.
Two of those four contribute **whole** (STEP-HFpEF 529/529, STEP-HFpEF DM 616/616); two
contribute a **selected minority** (SELECT 2,273/17,604 = 12.9%, FLOW 325/3,533 = 9.2%).
Total 3,743 of 22,282, or 16.8%.

**This is the weakest of the three instances and it is recorded with that said.** The
paper discloses its inclusion logic fully in its own Methods and abstract; the HFpEF
analyses were **prespecified** in three of the four trials' statistical analysis plans;
the authors call their own pooling *"exploratory"*. **Nothing is hidden.** The pattern is
that a title naming four randomised trials invites a reader to assume four whole trials,
and the correction lives in the Methods rather than in the framing.

**The check we run on ourselves.** State the contributing denominator wherever a topic
names its trials — not the randomised total, the **analysed** total, per trial.

---

## What this file is not

**Not a claim that published syntheses are unreliable.** Three named instances against a
literature we have otherwise found sound. **Not a rate** — the denominators above are far
too small, and quoting a percentage from three instances would itself be an error of the
kind this file catalogues. **Not a defence of our own work**: every class here is one we
have either committed or come close to committing, and each entry says so.
