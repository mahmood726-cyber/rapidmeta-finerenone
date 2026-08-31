# Bespoke fraction — 2026-08-30, pessimistically

**The test, as set:** *would this apply to topic two without being redone?* Not
"is the logic reusable", which flatters everything. A file that must be edited
before it runs on another topic is bespoke, because editing it is the work.

## The number

| | lines | share |
|---|---|---|
| Written 2026-08-30 (both sessions) | **5,096** | |
| Runs unmodified on a topic never opened — **verified by execution** | 2,035 | **40% general** |
| Must be rewritten per topic | 3,061 | **60% BESPOKE** |

**Quote 60%.** Previous honest counts: **69%** (project baseline), **84%**
(yesterday, this lane).

## How generality was established — by running it, not by reading it

A first, textual classifier scored the files by whether they contain a topic
token (`dapivirine`, an NCT id) on a code line. It returned **79% bespoke** and
it was wrong: it flags `screen_rules.py`, `count_bases.py` and
`topic_judgements.py` as bespoke because they carry NCT ids **as cited
evidence** — the seven registrations lost by query-quoting, the phase-NA trial —
not as dependencies.

So generality was tested by execution instead. Every module was run, unmodified,
against five topics never opened this session:

```
topic (never opened)             judgements abs.effect envelope   countbases  card bytes
sglt2-hf                         2 of 7     DECLINED   DECLINED   DECLINED    18748
iv-iron-hf                       2 of 7     DECLINED   EMITTED    DECLINED    27188
malaria-vaccines                 2 of 7     DECLINED   EMITTED    DECLINED    14012
nirsevimab-infant-rsv-review     0 of 7     DECLINED   EMITTED    DECLINED     7448
arni-hfref                       2 of 7     DECLINED   EMITTED    DECLINED     7416
```

5 of 5, producing real rendered output. A `DECLINED` is a correct result, not a
failure — the module says why it declined and the reason is the finding.

## The classification

**GENERAL — 2,035 lines, runs on any topic:**

| file | lines |
|---|---|
| `ssot/topic_judgements.py` | 483 |
| `ssot/recompute_envelope.py` | 352 |
| `ssot/absolute_effect.py` | 294 |
| `ssot/count_bases.py` | 263 |
| `ssot/projectors_generated.py` | 252 |
| `ssot/screen_rules.py` | 243 |
| `scripts/audit_judgements_corpus.py` | 148 |

**BESPOKE — 3,061 lines, would not regenerate:**

| file | lines | why |
|---|---|---|
| `ssot/apply_reader_renderings_agyw_2026_08_30.py` | 691 | four renderings of dapivirine prose |
| `ssot/apply_judgement_register_agyw_2026_08_30.py` | 530 | superseded by the deriver; kept as the record |
| `scripts/bibliographic_screen_dapivirine.py` | 488 | hardcoded concept block, output path, ring-vs-gel rule |
| `ssot/projectors_reader_layers.py` | 469 | renders dapivirine-specific stored blocks |
| `ssot/apply_registry_extraction_agyw_2026_08_30.py` | 415 | two NCTs, hardcoded counts |
| `ssot/apply_bibliographic_screen_agyw_2026_08_30.py` | 316 | hardcoded resolutions |
| `ssot/apply_d3_implication_agyw_2026_08_30.py` | 152 | hardcoded object path |

## ⛔ The honest caveat, and it matters more than the number

**The improvement came from ADDING general code, not from removing bespoke
code.** All 3,061 bespoke lines are still on disk and still bespoke. Nothing was
converted; the denominator grew. 84% → 60% is real arithmetic and it is not the
same achievement as retiring bespoke work.

What would actually retire it:

- `bibliographic_screen_dapivirine.py` → parameterise the concept block, the
  output path and the formulation rule. It becomes a generator in about a day
  and takes ~488 lines across the line.
- `projectors_reader_layers.py` → the four reader renderings need templating off
  the fact table rather than hand-written prose. Harder; the prose is the value.
- The five `apply_*` scripts → these are **write-once records** of what was
  applied and when. Arguably they should never be general, and counting them as
  bespoke debt may be the wrong frame. Counted as debt here anyway, because the
  pessimistic reading is the one that was asked for.

Retiring the first two would put the figure near **35% bespoke**. Not done, not
scheduled.

## What improved that is not a fraction

The per-topic **judgement count** is now derived rather than asserted, and the
corpus number exists for the first time: 146 outcome-blocks with a pooled
result, mean **0.46 of 7** judgements declared, **97 of 146 declaring nothing**.
A high bespoke fraction with 7 declared judgements is an engineering problem. A
low bespoke fraction with 400 undeclared judgements would be a science problem.
Only the second is fatal.
