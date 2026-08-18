# Class 4 screen: corpus-wide, and it found nothing new

**A registered primary whose comparator is an external or historical estimate rather than
a randomised arm.** Founded on the lenacapavir closure. Run across the whole corpus —
cardiology and infectious disease together — because nothing had ever looked for it and
because it passes every arithmetic check while presenting non-randomised contrasts as
randomised results.

## Denominators first

| | n |
|---|---|
| trials referenced by built objects | 239 |
| **screened** (results posted) | **204** |
| **not screenable** (no posted results) | **35** |
| flagged by either signal | 18 |
| **confirmed Class 4 after reading** | **2 — both the founding case** |

**The screen says nothing whatever about the 35 trials with no posted results.** That is
not a clean bill; it is a hole, and `MALARIA_ACT`'s five trials sit in it.

## The result: Class 4 is n=1 topic, not a class

**The lexical signal — the one that actually looks for an external comparator — fired on
exactly two trials, and they are the two lenacapavir trials the class was built from.**

| trial | group title on the registered primary |
|---|---|
| `NCT04925752` | *"Incidence Phase: All Screened Participants With Non-…"* |
| `NCT04994509` | *"Participants Screened for HIV-1 in Incidence Phase"* |

**No other trial in 204 carries the shape.** So Class 4 joins the cross-regulator
divergence finding: **a real defect, correctly described, with a denominator of one
topic** — worth a note in the taxonomy and not worth a corpus-wide remediation programme.

## The other 16 flags are the structural signal, and they are false positives

The structural signal — an outcome measure posting more groups than the trial has
randomised arms — was included because that is how an external comparator usually appears,
appended to the real arms. **In practice it detects something else entirely**, and the
docstring predicted this before the run:

- **Extension and open-label phases** posted as extra groups (`NCT03496207` sotatercept
  *"Extension Period"*, `NCT01854918` evolocumab open-label extension)
- **Safety outcomes pooled across dose cohorts** — `NCT04425629` posts **13 groups against
  1 randomised arm** on treatment-emergent adverse events
- **Multi-arm and factorial designs** where the arm-group count in the protocol section
  simply does not match how results were grouped

**Not one of the 16 is an external comparator.** The signal is measuring registry
bookkeeping, not study design.

**Kept anyway, and here is the argument against deleting it.** A screen that only fires
on the pattern you already know finds only what you already know. The structural signal
costs nothing to run and would catch an external comparator given a neutral group title —
which is failure mode 1 in the script's own docstring and the mode the lexical signal is
blind to. **Its false-positive rate is the price of that coverage, and 16 flags a reader
can dismiss in two minutes is a cheap price.** What it must not do is be reported as 18
findings.

## What this screen does not establish

**NOT that the corpus is free of Class 4.** Three demonstrated blind spots, stated in the
script rather than discovered later:

1. An external comparator described in the outcome **description** but given a neutral
   group title (*"Group 2"*) is invisible to both signals.
2. A single-arm outcome compared against a **literature value stated only in the protocol
   document** is invisible — the registry holds no second group at all.
3. **The 35 trials with no posted results cannot be screened at all.**

**NOT that the flagged 16 are sound** — they were dismissed as Class 4, not audited for
anything else. **NOT that the two confirmed trials are poor**: PURPOSE 1 and PURPOSE 2 are
large, well-conducted, completely registered trials. The defect was never in them. It was
in the idea of pooling their registered primary.
