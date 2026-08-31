# Specification: `build_binary_sidecar.py` must honour the store's refusals

**Status:** specification only. **I have not edited `scripts/build_binary_sidecar.py`** — it is
outside this worktree's scope and another lane may own it. Routed for whoever does.

**Measured 2026-08-31 against `98196b574`:** of **108** store objects that record a refusal to
pool, **88** have a sidecar that publishes a pooled estimate anyway, and **3** of those reach a
page a reader can see. Provenance of the 88: `scripts/build_binary_sidecar.py` 60, no provenance
recorded 26, `curated_publishedHR_via_metafor_5.0.1` 2. Evidence:
`outputs/UNPOOLABLE_OVERRIDE.json`; gate: `scripts/gate_unpoolable_override.py`.

## The defect

The store records refusals to pool in `results.by_outcome.primary`, as `pooled.withdrawn: true`
or `poolable: false`, each with a `poolable_reason` written out in full — median 705 characters,
none shorter than 109, quoting registry evidence verbatim. These are considered judgements, not
defaults.

`build_binary_sidecar.py` computes a pool from 2×2 counts without consulting them. It is not
overriding the store in the sense of disagreeing with it; **it has never been told the store
refuses.** One defect, 88 instances, one point of repair.

The three served instances are not hypothetical, and the store had already diagnosed each:

| page | the store's own words | what is served |
| --- | --- | --- |
| `BEMPEDOIC_ACID` | *"Nothing is pooled: one trial. This is not a withheld estimate — the value stands and is CLEAR Outcomes' own."* | `OR 1.141` over `k=4` |
| `CANGRELOR_PCI` | *"THE NUMERATORS AND THE DENOMINATORS ON THIS PAGE COME FROM DIFFERENT OUTCOMES, ON ALL THREE TRIALS."* | `OR 0.902` over `k=3` |
| `INCRETIN_HFpEF` | *"TWO OF THE THREE TRIALS ON THIS PAGE REGISTER ONLY CONTINUOUS PRIMARY OUTCOMES, AND THIS PAGE POOLED EVENT COUNTS."* | `OR 0.436` over `k=3` |

## What it should do

**Emit the sidecar, with the refusal carried in it, and make the refusal structurally impossible
to render as a number.** Not "emit nothing", and not "emit with a flag".

Of the three options, *emit nothing* is wrong because it destroys evidence: the pooled value is
diagnostically useful (it is how the `BEMPEDOIC` direction flip was found), and a sidecar that
silently disappears is indistinguishable from one that was never built — the same "absence read
as clearance" failure this corpus has already been bitten by. *A flag the renderers must honour*
is wrong because it depends on every current and future renderer remembering to check it, and
three renderers already disagree about this corpus.

So: keep the computation, move it out of the field the renderers read.

1. Before computing, resolve the topic to its store object via `ssot/PAGE_MAP.json` and read
   `results.by_outcome.primary`.
2. If `pooled.withdrawn` is true **or** `poolable` is false, then in the emitted sidecar:
   - **`pooled_OR`, `ci_low_OR`, `ci_high_OR`, `PI_low_OR`, `PI_high_OR` MUST be `null`.** These
     are the fields every renderer reads. A renderer that does nothing new renders nothing.
   - the computed values move to `withheld_pool: { point, ci_low, ci_high, ... }`, so the
     diagnostic value survives and no evidence is destroyed;
   - `store_refusal: { reason: <verbatim poolable_reason>, store_path, read_at_commit }`;
   - `k` stays populated — the trial count is not in dispute.
3. If the topic has **no** store object in `PAGE_MAP`, emit as today and set
   `store_refusal: null` with `store_consulted: false`. Absence of a store object is not
   permission; it is an unknown, and it must be visible as one.
4. Never infer a refusal from the shape of the data — only from a recorded one.

The point of (2) is that it removes a class rather than adding a rule. Today a renderer must
remember to check a flag; after this, a renderer that ignores the refusal entirely still cannot
print a number, because there is no number in the field it reads.

## What must be true afterwards

- `scripts/gate_unpoolable_override.py` reports **0 served**, and the count of overrides falls
  from 88 toward 0 as sidecars are regenerated.
- The baseline in `outputs/override_gate_baseline.json` is marked **OWED, not cleared**. It
  exists so the gate can refuse a regression today while the 88 are worked off, and it must be
  lowered as they are, never raised.
- Regenerating a sidecar for a refused topic must **not** silently change a served page. The
  three served pages need the refusal rendered, and that is a separate decision that belongs to
  Mahmood, not to this specification.

## What this does not cover

The 26 overrides with no provenance recorded are not attributable to this script and may have a
different producer. The 2 from `curated_publishedHR_via_metafor_5.0.1` belong to the class whose
separate defect is that it carries no registration ids and no endpoint polarity —
`17 of 17 POLARITY_UNKNOWN`, recorded in `outputs/FROZEN_PREFIX_DISAGREEMENTS.json`. Fixing this
script fixes 60 of 88.
