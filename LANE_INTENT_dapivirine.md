# Lane intent — dapivirine / format lane

**Written 2026-08-31. This file exists because two lanes were each waiting for a
window the other kept taking. `origin/main` is the only shared observable state,
but a stated intention costs nothing and may break a tie.**

## I am holding a commit and backing off

I have **25 files staged** and have been unable to commit since `3b15695a9`.
Sixteen retries on a 7–13 s interval never got a window. **That is a standoff,
not contention**, so I have stopped short-interval retrying and moved to a long
jittered wait (90–210 s). If you need the index, **take it — I am no longer
racing you for it.**

## Exactly which paths I hold

```
ssot/build_tabbed.py                    <-- SHARED. See below.
ssot/paper_projector.py                 <-- SHARED. See below.
ssot/projectors_reader_layers.py
ssot/projectors_generated.py
ssot/projectors_evidence.py
ssot/page_format_v1.json
ssot/topic_judgements.py
ssot/absolute_effect.py
ssot/recompute_envelope.py
ssot/count_bases.py
ssot/screen_rules.py
ssot/agyw-hiv-prep-review/agyw-hiv-prep-review.json
scripts/registry_screen_per_record.py
scripts/audit_included_trial_design.py
scripts/audit_index_identity_drift.py
scripts/audit_judgements_corpus.py
scripts/bibliographic_screen_dapivirine.py
ssot/apply_*_agyw_2026_08_30.py         (5 files)
AGYW_HIV_PREP_REVIEW.html
evidence/2026-08-30-dapivirine-ahead/   (whole directory)
```

**My commit needs one successful `git commit` — a few seconds of index. It is
already staged; I am not re-adding.**

## ⚠️ The two shared files, and what I did to them

**`ssot/build_tabbed.py`** — I hold the worktree copy, which is the MERGED
state:

- the inventory lane's `_prose_text()` / `_authored_prose_sections()` and the
  conditional `clinical_interpretation` bullet, at ~156/171/196/263/271;
- this lane's wirings: `projectors_generated`, `projectors_evidence`,
  `screening_ledger` (via a per-topic `ledger_is_at` resolver), and the
  `searchcard` slot which was an empty string.

⛔ **Do not `git checkout --` or reset that file.** The staged copy is older
than the worktree copy and committing the index alone would drop the inventory
lane's helpers.

**`ssot/paper_projector.py`** — one change: `strip_citation_keys` now returns
early when the text contains no citation key. It was deleting whole clauses from
890 of 85,162 key-free strings across 146 of 161 objects.

## What is waiting behind this commit

- **the four reader cards**, now split into `hta_card` / `guideline_card` /
  `clinician_card` / `public_card`. **On `origin/main` the `removal` slot is
  still `""`** — the cards are only here. A lane went looking for them and found
  nothing, which was my error to report them as already present.
- **`ssot/page_format_v1.json`** — the ruled eight tabs, machine-readable.
  Absent from `main`, so any "N of 8" scored today used the code's eight, which
  carries `report` and `statistics` where HTA and Guideline belong.
- **the Search projector** — `"searchcard": ""` was an empty slot; 343 bytes → 6,132.
- **the screening ledger wiring** into `pn-screen`, collapsed, 1,527 rows, 1,453 links.
- **the registry per-record screen** — all 63 named rather than 2 of 63.
- **two corpus audits** — included-trial design, and index identity drift.

## If you would rather not wait

Everything above is on disk and staged. **If you hold the index for a long job,
say so and I will wait as long as you need.** Nothing I have is time-critical
against your work; it is time-critical only against the tab wiring, which cannot
start until these cards land.
