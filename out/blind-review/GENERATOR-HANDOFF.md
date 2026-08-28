# Generator handoff — declared surfaces first

## 0. THE ONE ATTRIBUTE THAT WOULD HAVE MADE TONIGHT UNNECESSARY

> **`data-artefact="review|tool|redirect|landing"` on every served page.**

Tonight cost a full census to establish that of 1,463 served root pages, 744 are
unpopulated application shells, 506 are redirect or withdrawal notices, 141 are
attributed reviews, and 58 could not be classified without opening them one at a
time. **One attribute answers retired-versus-live, tool-versus-review, and the
stub classification at once, and would have made the whole census a single grep.**

The argument for it is not that it enables a check. It is that its absence made a
night of forensic classification necessary to answer a question the pages should
have been able to state about themselves.

## 0b. `data-pool="<pool_id>"` on every reader-facing number derived from a pool

Unblocks three classes that are otherwise unbuildable: the withdrawn-analysis
denominator, outcome-specific `k`, and three-surface set equality. Detail in §7.

Both belong on `REQUIRED_GENERATOR_COMMITS` once landed.

---

# Absence-defaults and frozen literals

Owner per `git log origin/main -- ssot/build_app_v2.py`: **mahmood789**.

Every item below was converted from a *site* (a place in the code where a value can be born from
absence) to a *defect* (a reader actually receives it) by checking the served bytes. Items are
ranked by that conversion, not by how alarming the source line looks.

---

## 1. CONFIRMED READER-FACING FALSEHOOD — fix first

**`ssot/build_app_v2.py:1362,1364,1368` — `outcome.get('effect_scale', 'natural')`**

`sglt2-hf`, outcome `harmonised_cvdeath_or_hhf`: object stores `measure: "HR"` and no
`effect_scale`. The served page renders **"Effect scale reported on the natural scale"**. A hazard
ratio is a log-scale quantity, and both sibling outcomes on the same page store `'log'` — so the
page contradicts itself for anyone who reads three rows.

**The default is the minority value.** Stored corpus-wide: `log` 70, `natural` 10, `linear` 2,
`none` 1. Absence renders as the *less likely* truth.

**Fix:** derive or refuse, exactly as `_favoured_arm` now does.

```python
_SCALE = {"log": "log", "natural": "natural", "linear": "linear", "none": "none"}
scale = _SCALE.get(str(outcome.get("effect_scale")).strip().lower()
                   if outcome.get("effect_scale") is not None else None)
if scale is None:
    scale_phrase = "on a scale this object does not record"
else:
    scale_phrase = "on the %s scale" % scale
```

A ratio measure with no recorded scale should additionally be treated as an object defect, not
papered over at render time: 91 of 174 outcomes carry no `effect_scale` at all.

**Regression guard:** a ratio measure (`HR`/`OR`/`RR`/`IRR`) must never render "on the natural
scale". This is implemented and passing as `claims.chk_scale_vs_measure`, with fixtures in
`test_claims.py`.

---

## 2. CONFIRMED UNMADE CLAIM — true today, unguarded tomorrow

**`ssot/build_app_v2.py:1125` — `get('subgroup_heading', 'By age stratum')`**

`prevnar15-pneumo` renders the heading **"By age stratum"** over its subgroup table. Its object does
**not** carry `subgroup_heading`. Exactly one object in the corpus carries the field at all
(`malaria-vaccines`).

**On this page the default happens to be accurate** — the strata are age bands. That is luck, not
correctness: the object never said what the strata are, and the next page to lack the field will get
the same heading whether or not it is about age.

**Fix:** refuse. `get('subgroup_heading')` or omit the heading; do not name a stratification the
object has not declared.

---

## 3. LATENT — the seam exists, nothing reaches a reader through it yet

**`ssot/build_app_v2.py:126` — `hr.get("estimator") or "Hartung-Knapp"`**

This renders into the "Does the answer depend on the pooling method?" table. **18 served pages
render that table; 0 label a row "Hartung-Knapp".** So the default has never fired on a delivered
page. It is still a method name asserted from absence, and a method name is a claim.

**Fix:** `hr.get("estimator") or "an estimator this object does not name"`. Note line 124's
neighbour, `pub.get("estimator") or "as stored"`, is already honest and needs nothing.

---

## 4. COMPUTATIONAL, NOT RENDERED — but the two defaults disagree with each other

- `ssot/validate_v2.py:1834,1839` — `res.get("estimator_used", "DerSimonian-Laird")`
- `ssot/validate_v2.py:3564` — `str(res.get("estimator_used") or "REML")`, then any unrecognised
  method is coerced to `REML` two lines later.

These feed **recomputation**, not display. But one validator path assumes DerSimonian-Laird and
another assumes REML for the same absent field, so where `estimator_used` is missing the validator
can disagree with itself — and a disagreement surfaces as a finding against the *object*, not
against the validator.

**Fix:** one shared resolver that refuses on absence, so a missing `estimator_used` blocks
recomputation instead of silently choosing an estimator.

---

## 5. WITHDRAWN FROM THE RANKING — I ranked this first and was wrong

**`ssot/apply_breadth_and_tigecycline_disclosure.py:183` — `hk.get("ci_low", "0.8327")`,
`hk.get("ci_high", "1.0501")`**

I reported this as the most dangerous item: a confidence interval defaulting to hardcoded bounds.

**It is inside a `print()`.** It writes to the operator's console, never to a page. The script is a
one-off migration, already applied, and nothing in the tree references it. It is not reader-facing
and it is not a loaded gun. The correction is mine, not the code's.

---

## 6. NOT A DEFECT — checked and cleared

**`ssot/apply_reml_corpus.py:335,382` — `get('environment') or 'R version 4.6.0 (2026-04-24 ucrt);
metafor 5.0.1'`**

16 objects carry that exact string; 6 served pages render it. But the string was written *by the
script that performed the refits*, so it records the environment that actually produced those
numbers. Asserting its own environment is correct behaviour, not a manufactured provenance claim.

**Honest placeholders, also cleared before counting:** `get('k', 'an unstated number of')`,
`get('checked_utc') or 'an unrecorded date'`, `get('quote') or '[nothing to quote: the item is
absent from the paper]'`, `get('started_at') or 'a starting level this review does not record'`.
Each says plainly that it does not know. **These are the system working.** 35 sites is not 35
defects.

---

## 7. Design requirement — converts two unbuildable checks into mechanical ones

Two external-review findings cannot be checked at all today, because no page emits a link between a
stated number and the pool it came from:

- a denominator that survived the withdrawal of the analysis it described;
- `k` conflated between review-level and outcome-specific counts.

> **Every reader-facing number derived from a pool must carry that pool's identifier in the markup**
> — `data-pool="hfcv_total"` on the visual-abstract N, the index-card k, and the published-comparison k.

One attribute makes both classes exact, with zero natural-language inference. The argument against
building a proxy instead is `direction_label`, retired at precision 0 of 2, whose second false
positive was caused by the patch for its first.

---

## Scan provenance

- `projector_defaults.py` — 113 files, 0 unparseable, 35 absence-default sites in 3 kinds.
  Validated by two-tree proof: finds `build_app_v2.py:269 direction_of_benefit` in the stale
  worktree, silent on `main` where it is fixed.
- `frozen_literals.py` — the same scan in reverse. **FROZEN-PARAM: 0** across 113 files, and the
  detector is proven to fire (plants a frozen claim-bearing seam → fires; a caller that overrides →
  silent). **HARDCODED-CLAIM: 76**, of which 61 are one-off `apply_*` migrations, 8 other tooling,
  1 a regex literal, and **6 in the live projector — 4 docstrings and 2 correct branches of a
  model-name normaliser.** No frozen literal reaches a reader.


---

## 8. LANDED

**Item 0 — `c5409eaa1f32461e4ab1bfb57855bac5fb63f1e4`** (short `c5409eaa1`, on `1f1c42e52`).
Absence handling in `ssot/build_app_v2.py`; 17 fixtures in `ssot/test_absence_keyerrors.py`.
Scope corrected on landing: this repairs the pre-tab control path (84/141 -> 141/141). It is
**not** a delivery blocker — the delivered path builds 140/141 both before and after.
For registration on `REQUIRED_GENERATOR_COMMITS`.

## 9. STILL OPEN, ranked

1. **Six DTA reviews, ~280 KB each, real results, zero instrument coverage** — see `THE-58.md`.
   `HSCTN_NSTEMI` and `GENEXPERT_ULTRA_TB` are in the cardiology/ID remit.
2. **`index.html` republishes 106 effect estimates** and is an unchecked staleness surface.
3. **The naming decision on 744 app shells** served under `*_REVIEW.html` URLs.
4. `subgroup_heading` correct-by-coincidence default (§2), `estimator` latent default (§3),
   and the two disagreeing validator defaults (§4).
