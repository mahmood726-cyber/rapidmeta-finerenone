# Canonical object schema — v2 (multi-outcome, k>1, network)

v1 was proved on one app (`rivaroxaban-acs`, k=1, one outcome, two arms) and is
frozen at tag `golden-rivaroxaban-acs-v1`. v1 is a **special case** of v2, not a
different schema: every v1 field keeps its meaning.

The load-bearing invariant is unchanged:

> No surface may contain a number that is not a pure projection of the one
> canonical object.

## Why v1 cannot express the batch

v1 hard-codes three assumptions that only hold at k=1 with a single outcome:

| v1 assumption | Breaks on |
|---|---|
| `results.single_study_ref` names *the* effect | k>1 — there is a pooled estimate *and* per-trial estimates |
| one `effect` per trial | multi-outcome — primary, secondaries and harms each have one |
| exactly two arms, roles `treatment`/`control` | networks — three or more treatments, multi-arm trials |
| `estimator: "none"` | real pooling — REML vs DL vs PM now *changes the answer* |

## v2 additions

### 1. `outcomes[]` — outcomes are first-class

```
outcomes: [
  { id, name, type: primary|secondary|harm, measure, direction_of_benefit,
    outcome_definition, timepoint }
]
```
Every outcome is declared once, at the top. Nothing else may name an outcome by
free text; surfaces reference `outcome.id`.

### 2. Trial data is keyed BY OUTCOME

```
inputs.trials[]: {
  id, name, nct, pmid, doi, year, design, arms[],
  by_outcome: {
     <outcome_id>: { arm_data: {<arm_role>: {events, n} | {mean, sd, n}},
                     effect: {...} | null,
                     provenance: {...} }
  }
}
```
An arm's data lives under the outcome it belongs to, so a trial that reports the
primary but not a secondary simply has no entry — rather than a null that some
surface might render as zero.

### 3. `results.by_outcome` — one result block per outcome

```
results.by_outcome: {
  <outcome_id>: {
     k, poolable, poolable_reason,
     model: fixed|random|single-study,
     estimator, estimator_used,          # what was ASKED for vs what RAN
     pooled: {measure, point, ci_low, ci_high, p_value, ci_level} | null,
     single_study_ref: "..."             | null,
     heterogeneity: {tau2, i2, q, df} | null,
     heterogeneity_status
  }
}
```

`k` is **derived** — it is the number of trials contributing data for that
outcome — and the validator recomputes it rather than trusting the field. At k=1
this reduces exactly to v1.

### 4. Networks

```
network: {
  treatments: [{id, label}],
  reference_treatment: <treatment_id>,
  comparisons: [{ treatment, comparator, outcome_id, measure,
                  point, ci_low, ci_high, direct_k, indirect }]
}
```
Arms in a network trial carry `treatment` (a `treatments[].id`) instead of the
two-role `treatment`/`control` pair. The role vocabulary generalises: `role` is
retained for two-arm trials, and `treatment_id` is used where a network exists.

## What v2 lets the validator check that v1 could not

These are new detectors, and they are the point of the batch phase — at k=1 there
was no pooling arithmetic to verify, so the validator could only check
consistency of labels.

1. **`k` matches the contributing trials.** A stated k that disagrees with the
   data is a block, not a note.
2. **The pooled estimate is recomputable from the inputs.** Inverse-variance
   pooling of the per-trial log-effects must reproduce the recorded pooled point
   and interval within tolerance. This is the first check in the whole design
   that can catch a *wrong pooled number* rather than an inconsistent label.
3. **Estimator asked-for vs estimator used.** `estimator` records what the
   analysis specified; `estimator_used` records what ran. They may legitimately
   differ (HKSJ is not estimable at k=2 with zero heterogeneity), but the
   difference must be recorded, not silently resolved. This is the defect class
   that produced 749 apps declaring REML+HKSJ while exporting DL.
4. **Heterogeneity is present iff k>=2**, and tau2/I2 are mutually consistent.
5. **Every outcome declared is projected, and every outcome projected is
   declared** — a surface may not invent an outcome, and a declared outcome may
   not silently vanish.
6. **Network connectivity.** Every treatment in `comparisons` exists in
   `treatments`; the network is connected; the reference treatment is in it.

## Extensions log

Each entry records what forced the change, so the schema's growth is auditable
rather than convenient.

| # | Extension | Forced by |
|---|---|---|
| 1 | `outcomes[]`, `by_outcome` keying | (pending first multi-outcome app) |
| 2 | `results.by_outcome`, derived `k` | (pending first k>1 app) |
| 3 | `network{}`, `treatment_id` on arms | (pending first network app) |

## Extension log — filled by COVID19_VACCINES

| # | Extension | Forced by |
|---|---|---|
| 1 | `outcomes[]` with `measure` at OUTCOME level | The source app carries `estimandType:"RR"` on trial records, `effectMeasure:"OR"` in protocol state, and prose describing "pooling of log(HR)". Three different measures for one analysis. A single top-level measure field cannot even express the disagreement, let alone detect it. |
| 2 | `by_outcome` keyed trial data | Trials contribute to different outcomes; 8 of 12 had no usable counts for the primary. A per-trial `effect` field forces a null that some surface then renders. |
| 3 | `results.by_outcome[].k` **derived** | k is now counted from contributing trials. The app declares 12 trials; only 4 could be sourced. A declared k would have shipped the 12. |
| 4 | `model` + `estimator` + `estimator_used` split | The app declares FIXED-effect pooling while its own data give I²=88.5%. Recording only "what ran" would hide that the specification itself is wrong for the data. |
| 5 | `heterogeneity{tau2,i2,q,df}` as structured fields | Needed so the recompute detector can verify them, not just display them. |
| 6 | `shared_control_note` on multi-arm trials | Al Kaabi randomised WIV04, HB02 and ONE shared alum control. Using both vaccine arms against it double-counts the control. The schema must record that only one contrast was taken. |
| 7 | `ci_level` per pooled estimate, and per-trial | ChAdOx1's published interval is **95.8%**, not 95%, because of interim looks. Assuming 95% silently converts a correct published interval into a wrong one. |
| 8 | `quarantine{excluded_trials, reason}` | 8 of 12 trials could not be sourced. The object must state what it dropped and why, or its k looks like a choice rather than a limit. |
| 9 | `interpretation_caveat` on a pooled result | At I²=92.5% the pooled number is not an estimate of a common quantity. The schema needed somewhere to say so that is projected, not a comment. |

## Extension log — filled by ALIROCUMAB_LIPID (build-to-core)

| # | Extension | Forced by |
|---|---|---|
| 10 | `pool_generic()` — inverse-variance from per-trial EFFECT + INTERVAL | Every alirocumab trial reports a least-squares mean difference from its own model. There is no 2×2 to pool, so the variance must come from the published interval. Ratio measures pool on the log scale; a mean difference does not. |
| 11 | `measure: "MD"` with `null_value: 0` at outcome level | The first continuous outcome in the batch. A null of 1 would have declared a 52-point LDL reduction non-significant. |
| 12 | `mixed-input-forms` detector | Counts and effect estimates derive their variances differently. Silently pooling both together is a defect the object must be prevented from expressing. |
| 13 | `build_mode` + `removed_citations{}` with itemised reasons | A build-to-core app must SHOW its reduction. The detector blocks a build-to-core object with no disclosure, with reasons that do not sum to the removal count, or with a reason carrying no detail. |
| 14 | "retained but contributes no data" as a state distinct from "excluded" | NCT01507831 is a genuine alirocumab trial whose primary outcome is adverse events. It is not excluded on topic, but it contributes nothing to the LDL outcome. Collapsing the two states would either inflate k or wrongly imply the trial was contaminated. |
| 15 | Absolute-floor tolerance in the recompute comparison | A purely relative tolerance is meaningless as a mean difference approaches zero. |

## 16. `provenance.source_category_title` — REQUIRED when the cited outcome posts categories

A registry outcome measure is often not a single number. ClinicalTrials.gov
posts a solicited injection-site outcome as several categories — erythema,
induration, pain, swelling — each with its own row per arm.

Naming the outcome is therefore not enough to identify the cell. A build of
`prevnar15-pneumo` cited the correct outcome title and read the **last** posted
category, which is swelling in six of seven trials, and published it as "any
solicited injection-site adverse event". Every cell was arithmetically correct
and every cell resolved to a real registry row. The object passed 16/16.

`source_category_title` names the row. The `source-category-binding` detector
requires it whenever the cited outcome posts more than one category, and checks
that the stored value equals the value posted under that category **for the
declared arms**.

## 17. `arm_selection_note` — REQUIRED when a trial contributes more than one treatment arm

Combining two intervention arms against a shared control is legitimate. Doing it
without saying so is the defect: the same build silently used one of two V114
formulation arms, and silently dropped a route-of-administration arm. `arm-roles`
now permits many treatment arms only alongside a non-empty `arm_selection_note`,
which makes the disclosure structural rather than optional.

## 18. `results.by_outcome.<id>.subgroups[]`

A list of pre-declared strata, each carrying its own `k`, effect, interval and
heterogeneity, plus a `note` saying why the split exists. Introduced because the
population stratum that a published synthesis covers is what makes the object
comparable with it at all. Reported, never tested against each other — the
generator prints that disclaimer beside the table.

## 19. `comparator_type: "active"`

Declares that the control arm is a licensed product rather than a placebo, which
is what allows a control arm labelled "Prevnar 13" to pass `role-label-agreement`.
Scoped to the control direction only: a treatment arm labelled "placebo" remains
a contradiction.

## 20. `arms_not_used[]` — REQUIRED for any posted arm the object does not use

The `arm-completeness` detector enumerates the arms the registry posts for the
cited outcome and requires each to be either declared in `arms[]` or named here.
Introduced after a reviewer showed `arm-roles` was hinged on the wrong thing: it
demanded disclosure when a trial DECLARED more than one treatment arm, so
deleting the second arm from the object entirely made the requirement vanish.
A detector reading declared arms cannot see an arm that was never declared; the
enumeration has to come from the source.

## 21. `reference-consistency` — the only external anchor when an object declines to pool

`direction-anchor` returns early when there is no pooled result, so for a
per-trial-only object an arm swap plus a recomputed ratio was self-consistent
and passed everything. Where a per-trial row carries
`reference_efficacy_percent` from a published review, that figure sits outside
the object and cannot be flipped by editing it. The stored estimate must agree
with it in direction and within 15 percentage points — loose on purpose, since a
crude count-based ratio and a model-based efficacy legitimately differ, as the
documented 2.6-point person-time gap in one trial shows.

## 22. `agreement_tol()` — proportionate, not flat

A flat 0.005 tolerance inverts for small estimates: a risk ratio of 0.0845 could
be published as 0.0890 — a five per cent error in what a reader sees — while the
absolute gap stayed under the threshold. The allowance is now the tighter of two
decimal places and one per cent of the value.

## 23. A missing `percentage` on a DERIVED registry cell BLOCKS

It previously caused both source checks to `continue`. Omitting a value must not
be a way to escape being checked on it.

## 24. `arm-role-vs-registry` — roles anchored outside the object

`check_role_label_agreement` reads an arm's own label against a keyword list,
which cannot tell one vaccine from another: both labels are product names. A
reviewer swapped the roles AND the data blocks of a head-to-head trial,
recomputed the pool, the subgroups and `favours`, and it passed with the
comparator reported as the intervention.

ClinicalTrials.gov records what each arm IS — EXPERIMENTAL, ACTIVE_COMPARATOR,
PLACEBO_COMPARATOR — and that is outside the object. Inverting the object no
longer inverts the source.

## 25. Subgroup `trial_ids` must be unique

The recomputation iterates the list, so a repeated identifier double-counted
that trial and the stored estimate could be moved to match. A trial contributes
once.
