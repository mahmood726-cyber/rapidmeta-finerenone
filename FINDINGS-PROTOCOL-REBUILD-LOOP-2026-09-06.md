# Protocol template + per-review rebuild loop: proof on two reviews, report before applying

**Date:** 2026-09-06. **Status:** proof of the loop. NOTHING APPLIED to any served page.

## What was built

- `scripts/protocol_schema.py` — a protocol is a JSON object with **P/I/C/D as first-class
  eligibility fields**, each carrying a **rule id**; **outcomes are a reporting field**, never
  eligibility; guideline-derived criteria carry a **version**. `validate()` *refuses* a protocol
  that reproduces a known corpus failure, and its selftest proves each refusal fires: backdated
  prospectiveness, outcome-used-as-eligibility, a criterion with no rule id, a guideline without a
  version, outcomes placed inside eligibility, a missing authoring date. A gate that can only pass
  is not a gate; this one can fail, so a pass means something.
- `scripts/protocol_review_diff.py` — builds a review's eligibility block **from its authored JSON
  protocol** and diffs it against the **currently served page**, then runs the **real builder
  guards against the real page name** (do-not-rebuild, generator pin, published-correction
  survival). It writes nothing.
- Two authored protocols, each **retrospective, dated, claiming no prospectiveness**, and
  **grounded verbatim in the review's object** (not invented):
  `protocols/azilsartan_chlorthalidone_vs_olmesartan_hctz_retrospective_v1.json`,
  `protocols/iv_iron_hf_retrospective_v1.json`.

## Review A — azilsartan (one of the reviews with no protocol)

Chosen because its object **states** its eligibility, so the protocol formalises what the review
applied rather than inventing it. The object itself already says its criteria are "DERIVED POST
HOC and say so", and already separates the estimand ("governs POOLABILITY and not eligibility")
from eligibility — exactly the outcomes-not-eligibility rule.

Diff vs served (`AZILSARTAN_CLD_VS_OLM_HCTZ_REVIEW.html`): the served page shows **no PICO rows at
all** (0 `data-pico`, no eligibility-prose PICO). The protocol would **ADD** all four rows
(P/I/C/D), each with a rule id, Design marked DERIVED (the object's eligibility text names no
design). Guards: not protected, generator pin OK, no pinned correction. **Applying would be
additive.** Reported, not applied.

## Review B — iv-iron-hf (a protocol exists and the review renders criteria) — the reproduction check

Grounded in the object's **corrected** eligibility (the 2026-09-04 restatement), not the frozen
v1.0 markdown. Result:

- **P/I/C reproduce** the served eligibility prose (both come from the object): Population 1.00,
  Intervention 0.62 (protocol adds "route is load-bearing"), Comparator substance kept. The
  reproduction check **passes** — a protocol grounded in the object reproduces what is served.
- **Design is added** (the P/I/C/D model contributes a Design row the current P/I/C model has none of).

### Findings (surfaced, NOT applied)

1. **The served page states a RETRACTED eligibility criterion as live.** The iv-iron "Eligibility
   criteria" cell reads *"Eligibility turns on population, intervention, comparator, **route and
   outcome** … The outcome criterion is that the trial designates a CLINICAL-EVENT endpoint …"* —
   the **pre-2026-09-04** wording. The object retired the outcome clause from eligibility (Cochrane
   Handbook 6.5 §3.2.4) and preserved the original under `eligibility_superseded_2026_09_04`. A
   rebuild from the current object would silently correct the served page. **Per the rule, a
   silent improvement is a finding, not a success** — recorded here for Mahmood to decide, not
   applied.

2. **HFrEF vs heart failure.** The frozen v1.0 markdown protocol says population = **HFrEF**; the
   object says **heart failure** (broader). The served eligibility *prose* uses "heart failure"
   (object-consistent). So wiring the current `pico_pairs` (which reads the v1.0 markdown) onto
   this page would render an **HFrEF** PICO row that contradicts the page's own "heart failure"
   prose — a narrowing the ablation-af refusal note was written to avoid. The retrospective
   protocol keeps the object's wording and flags this rather than adopting either.

3. **A pinned published correction is PRESENT and must survive.** `check_correction_survives`
   reports iv-iron carries a pinned correction, currently present on the served page. The builder
   would **refuse** any rebuild that dropped it — the retraction-carry-forward guard the directive
   asked for already exists and is mechanical.

## Cross-cutting findings

- **22 of 24 no-protocol object-backed reviews record NO eligibility on their object.** Only
  azilsartan and malaria-vaccines state criteria. For the other 22, a retrospective protocol would
  be **invented**, which the honesty rule forbids; those must render `COULD_NOT_DETERMINE`, not
  fabricated criteria. Naming the set: acs-antiplatelet, agyw-hiv-prep, cab-prep-hiv, ceftaroline,
  covid-oral-antivirals, covid19-vaccines, cryptococcal-meningitis-africa, doravirine-hiv, fcm-hf,
  hepatitis-b-taf-tdf, hiv-prep-injectable, icosapent-lipid, lefamulin-cabp, lenacapavir-prep,
  malaria-act, malaria-vaccine, mdr-tb-shortened, nirsevimab-infant-rsv, pediatric-hiv-art,
  rosuvastatin, rotavirus-vaccine-africa, plus arni-hfref (protected, excluded).
- **P/I/C insertion is partial across the served corpus.** ACS carries 3 `data-pico` null+state
  rows (inserted ~09:18); iv-iron (built 01:48) and azilsartan carry **0**. The served surface is
  not uniform; a coverage claim must say `n of N`, not "the reviews".
- **azilsartan's object backs two served pages** (`AZILSARTAN_CLD_VS_OLM_HCTZ_REVIEW.html` and
  `AZILSARTAN_HTN_AUTO_FULL_REVIEW.html`). A rebuild decision touches both.

## What was NOT done, deliberately

No served page was modified. The loop stops at the report, as instructed. Applying would mean, per
review: wire the harness to render P/I/C/D from the JSON protocol, decide the HFrEF/heart-failure
wording with Mahmood, and let the builder's correction-survival guard gate the write.
