# Refusals That Are Right

Enumerated 2026-09-02, **before anything in this lane was edited**, because a cleanup pass
is exactly how these get tidied away. Across eight independent external reviews of eight
different pages, reviewers repeatedly PRAISED the behaviours below. Every one of them
looks, on the page, identical to a defect: a place where the review declines to print a
number.

Counts are MEASURED by `scripts/measure_defect_classes.py` over the 1464 served reader
pages (root-level `*.html`); page lists are in `scripts/baselines/defect_class_baseline.json`.

| id | refusal | why it is right | served pages |
|---|---|---|---:|
| R1 | The `Not recorded -- <reason>` idiom: an absent value is rendered as an absence WITH the reason, never omitted and never zero-filled | An omission is indistinguishable from a value of zero; this idiom makes absence auditable | 151 |
| R2 | `GOSH plot -- not drawn at this k` (and the same for funnel, meta-regression, TSA at small k) | At k=4 the whole subset space is 15 points. Drawing it would produce a figure whose shape is read for clustering that needs an order of magnitude more studies | 151 |
| R3 | `no funnel, Egger or Peters value is held on this object, so no meta-bias assessment is claimed` | Egger has low power below k=10; Peters is the binary-outcome test. Refusing beats reporting an underpowered test as evidence of no bias | 149 |
| R4 | `no outcome on this object carries a pooled estimate, so no synthesis method was applied` | Naming a synthesis method for a review that pooled nothing would be method boilerplate detached from any analysis | 120 |
| R5 | Subgroup analyses recorded as UNKNOWN, "which is not the same as none having been" prespecified | The distinction between "none" and "not recorded" is the whole content of the field | 149 |
| R6 | Co-primary endpoints kept SEPARATE rather than combined | Combining co-primaries invents an estimand no trial declared | 15 |
| R7 | LDL-C flagged as a SURROGATE | The endpoint is not the outcome patients experience, and the page says so | 3 |
| R8 | `Submission readiness: NOT READY`, computed from the object's own state | Every `NOT READY` flag was found correct by reviewers. It is computed, not a fixed disclaimer | 150 |
| R9 | No conversion between effect measures anywhere | Converting OR to SMD, or pooling across measures, is the substitution class this project audits for | 1 |

| R10 | **"No systematic search was run (no attestation can discharge this) -- The included set is a named programme rather than the yield of a database search. Nothing on this page should be read as though a systematic search had been performed."** | Added 2026-09-03, and the sharpest case here. The banner is HONEST, it is CORRECT, and it tells the reader what to discount. **Our own `P1_executed_search` contradicted it on 17 of the 19 pages carrying both** -- and the MARKER was the defect. A cleanup that "resolved" the contradiction by deleting the sentence would delete the only true statement of the pair. Its count clause was separately wrong (register C7) and that was a reason to fix the count, not to drop the disclosure | 147 |
| R11 | **A page WITHDRAWING its own earlier false claim** | empagliflozin retracted "no published synthesis pooled these two trials" and named EMPEROR-Pooled. Given W5 and W6, it is worth recording that this project does sometimes correct itself correctly -- and a cleanup pass must not remove the retraction as clutter | 1 |

## The rule this lane operates under

**A gate written in this lane may not turn any of the above into a failure.** If a new
check fires on one of these pages for one of these reasons, the check is wrong, not the
page. Two of the screens written while opening the register did exactly that -- a
`not drawn` screen returned 151 pages and every hit was R2 -- and those screens were
withdrawn rather than promoted.

**Corollary, and the reason X1 is in the register.** Defending a refusal is not the same
as defending its REASON. A refusal is a claim, and its reason is part of the claim. The
IV-iron win-ratio refusal is CORRECT and its stated reasons are mathematically false; both
facts are recorded, and fixing the reason must not remove the refusal.
