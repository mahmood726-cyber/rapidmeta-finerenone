# Control run: can three AI judges discriminate between two published reviews?

Run before any verdict on our own page, because if the judges cannot tell two published
reviews apart, a later verdict about ours measures the instrument and not the work.

**Documents, both published, both PICO-matched to dapivirine only.** Doc 1 = the Cochrane
review's dapivirine section (summary of findings, per-domain risk of bias, results, search).
Doc 2 = a 2024 journal review of the dapivirine ring. Journal names, collaboration names,
author names and running heads stripped — **zero residual identifying marks in either**.
Position randomised per judge.

## Result

| judge | family | A was | B was | verdict | strength |
|---|---|---|---|---|---|
| codex | openai | Cochrane | JAIDS | **A** — Cochrane | Moderately |
| agy `gemini-3.1-pro-high` | google | JAIDS | Cochrane | **A** — JAIDS | Moderately |
| agy `claude-opus-4-6-thinking` | anthropic | Cochrane | JAIDS | **B** — JAIDS | Moderately |

**By document: JAIDS 2, Cochrane 1.**

## The instrument works

**1. The judges discriminate.** Three confident verdicts, no ties, every one at MODERATELY,
each with named axes, weights totalling 100, and per-axis reasons citing concrete content. A
tie-prone instrument would have produced ties.

**2. It is not a pure position effect.** Two judges chose A, one chose B — and the one that
chose B did so with A presented first. Position did not decide it. With n = 3 this is
reassurance, not proof, and randomisation stays.

**3. ⭐ The authority prior does not dominate.** Two of three judges rated a non-Cochrane
review above the Cochrane one, blind. **Cochrane is beatable on these judges' axes** — which
is the single most important thing this run establishes, and it was the residual risk.

## ⚠️ And the axes that beat Cochrane are not the ones we have been building

Both judges that preferred the other document **explicitly conceded Cochrane's methodological
superiority and then outweighed it**:

> *"A's advantage is a more granular risk-of-bias assessment, but that single axis does not
> outweigh B's broader clinical and policy contextualization."*

| axis | weight given | who won it |
|---|---|---|
| Comprehensiveness of clinical outcomes | 30% (google) | not Cochrane |
| Analysis of population subgroups | 25% (google) | not Cochrane |
| Quantitative effect accuracy | 25% (openai) | tie |
| Methodological rigour / risk of bias | 20–25% | **Cochrane** |
| Search & method transparency | 15% (openai) | **Cochrane** |
| Clinical interpretation & limitations | 10% (openai) | not Cochrane |

**What repeatedly won: age-stratified subgroups, social harms, clinical applicability, evidence
gaps for key populations. What repeatedly lost, while being acknowledged: risk-of-bias
granularity and search transparency.**

⇒ **Our page is built almost entirely on the axis that loses.** The audit trail, the provenance
tiers and the published error rate all sit under methodological rigour — the axis Cochrane
already wins and that two of three judges discounted. Meanwhile the content that won twice —
**age-stratified efficacy, which we currently carry only as a limitation, and harms, which we
omit entirely** — is content we could hold.

## The prediction this tests

The prediction before the run was: lose on search breadth and certainty, win on reproducibility
and currency. **Search breadth is confirmed as a real axis (15%, Cochrane won it).
Reproducibility did not appear as an axis at all in any of the three.** No judge named
reproducibility, auditability, or verifiability unprompted.

⚠️ **That is a finding about the judges, not a reason to drop the audit trail.** It is recorded
here so that if a later round scores us down for length or up for context, we know which axes
were live before we started optimising.
