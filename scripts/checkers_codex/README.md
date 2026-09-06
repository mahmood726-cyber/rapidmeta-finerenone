# Codex-built checkers (fixture-validated, NOT yet corpus-wired)

Built by Codex (GPT-5 family, openai — independent of Claude=anthropic) in parallel scratch dirs on
2026-09-06, each cleared its own synthetic fixture on a local run before landing here. Each is a
standalone stdlib checker with a `scan(...)` entrypoint and a `_selftest()` that fires on a planted
POSITIVE and stays silent on a NEGATIVE control.

**Status: fixture-validated only.** These pass a synthetic positive/negative fixture. They are NOT
yet corpus gates — a corpus gate must additionally fire on a real known-positive instance AND clear
a real known-good page (`arni-hfref` is the standing false-positive control). Wiring each `scan()` to
read real `ssot/*/*.json` objects and validating against those controls is the required next step
before any of these is trusted as a gate or added to the pre-push suite.

| file | detects |
|---|---|
| `boilerplate_by_k_check.py` | identical interpretation text reused across different pooled-trial counts k |
| `absolute_effect_check.py` | a relative effect (RR/HR/OR) with no ARR+NNT+control-risk-source and no undefined-note |
| `composite_decomposition_check.py` | a composite primary outcome with no component breakdown and no unavailable-note |
| `self_reference_overlap_check.py` | an "external" benchmark that shares the meta's trial set (Jaccard ≥ 0.8) — the self_reference trap |
| `harms_presence_check.py` | harms absent or only generic ("adverse events"), no specific named harm |
| `num_denom_consistency_check.py` | event numerator > arm denominator, or a reported % inconsistent with events/n |

Run one: `python scripts/checkers_codex/<name>.py` (exits non-zero if its self-test fails).
