# Multi-Persona Review: CT.gov Audit Pipeline

### Date: 2026-04-10
### Files reviewed:
- `ctgov_deep_mining.py` (653 lines, NEW this session)
- `cv_death_subatlas.py` (325 lines, NEW this session)
- `ctgov_integration_report.py` (187 lines, NEW this session)
- `cardiology_mortality_atlas.py` (CTGOV_AUGMENTATIONS additions, ~50 lines)

### Personas: Statistical Methodologist, Software Engineer, Domain Expert, Security Auditor
### Summary: 8 P0, 13 P1, 9 P2 — **ALL FIXED 2026-04-10**
### Status: **REVIEW CLEAN** — see file diffs in the rapidmeta-finerenone repo

---

## P0 — Critical (must fix before next push / before relying on results)

- [FIXED 2026-04-10] **P0-1** [Domain] Missing **VERTIS-CV** added to `SGLT2 CVOT (T2D)` pool — k=3→**4**, pooled HR 0.83→**0.85 (0.75-0.97)**, I²=75%→**67%** (heterogeneity reduced; VERTIS-CV at 0.93 sits between EMPA-REG 0.68 and DECLARE 0.93). VERTIS-CV ACM HR 0.93 (0.80-1.08) verified via CT.gov registry (outcome [14] "Time to Occurrence of Death From Any Cause, On-Study Approach"). — `cardiology_mortality_atlas.py:200-202`, `ctgov_mining_inventory.json`

- [FIXED 2026-04-10] **P0-2** [Domain] **Intensive glycemia (T2D)** now k=1→**3**: added ADVANCE (HR 0.93, 0.83-1.06, Patel NEJM 2008) and VADT (HR 1.07, 0.81-1.42, Duckworth NEJM 2009). Pooled HR 1.19→**1.05 (0.88-1.26)** — non-significant, properly attributing the harm signal to ACCORD alone rather than overstating it as a class effect. ACCORD RoB upgraded `'low'` → `'some'` (stopped early for harm). App renamed "Intensive glycemia (ACCORD)" → "Intensive glycemia (T2D)". — `cardiology_mortality_atlas.py:184-191`

- [FIXED 2026-04-10] **P0-3** [Domain/Stats] Added `is_exploratory_pool()` helper + JSON `is_exploratory` flag + HTML `EXPLORATORY` badge with PI display when `I² ≥ 75% AND k < 5`. Currently flags **Icosapent ethyl** (k=2, I²=82%, true REDUCE-IT vs STRENGTH disagreement). SGLT2 CVOT (T2D) post-VERTIS no longer triggers (I²=67%). Console output marks `[EXPLORATORY]` next to concordance tag. — `cardiology_mortality_atlas.py:475-491, 1057-1083, 1606`

- [FIXED 2026-04-10] **P0-4** [Stats] `select_2arm_pair` no longer fabricates a pooled experimental by summing dose arms — returns `None` if no sponsor-supplied "All [Drug]" group exists. Forces caller to fall back to a different outcome rather than break randomization. — `ctgov_deep_mining.py:233-242`

- [FIXED 2026-04-10] **P0-5** [Stats] `pm_hksj_pool` now hard-refuses at k=2 — returns `{refused: True, method: 'k=2 — REFUSED to pool ...', pooled_est: <FE point estimate>, pooled_lci: None, pooled_uci: None}`. No silent over-narrow CIs. — `cv_death_subatlas.py:188-209`

- [FIXED 2026-04-10] **P0-6** [Software] Bare `except Exception` removed; now `except HTTPError`, `except (URLError, TimeoutError, OSError, json.JSONDecodeError)`. KeyboardInterrupt and bugs propagate. — `ctgov_deep_mining.py:343-373`

- [FIXED 2026-04-10] **P0-7** [Software] `os.system` replaced with `subprocess.run([sys.executable, ...], shell=False, cwd=BASE_DIR)`. — `ctgov_deep_mining.py:546-553`

- [FIXED 2026-04-10] **P0-8** [Security] Hardcoded `C:\Projects` paths replaced with `__file__`-relative resolution. `find_app_path()` now resolves repo root via `os.path.dirname(os.path.abspath(__file__))` and walks parent dir for sibling `*_LivingMeta` repos. — `cardiology_mortality_atlas.py:259-281`

---

## P1 — Important — ALL FIXED 2026-04-10

- [FIXED] **P1-1** ACCORD `rob: 'low' → 'some'`, VICTOR `rob: 'low' → 'unclear'`; `'low'` entries documented inline. — `cardiology_mortality_atlas.py:184, 174`
- [FIXED] **P1-2** Per-pool `source_mix` dict + `sensitivity_analyses_only` leave-Peto-out HR added to `cv_death_subatlas` pools and surfaced in markdown. — `cv_death_subatlas.py:351-409`
- [FIXED] **P1-3** Each extracted record now carries `retrieved_at` ISO timestamp + `last_update_post` from CT.gov for change detection. — `ctgov_deep_mining.py:404-411`
- [FIXED] **P1-4** Replaced naive `' or '` substring with `_COMPOSITE_OR_RE` regex requiring a clinical second endpoint after "or". — `ctgov_deep_mining.py:266-271`
- [FIXED] **P1-5** Added `'number of deaths', 'deaths (all causes)', 'all deaths'` to ACM patterns + `_BARE_DEATH_RE` word-bounded fallback for older trials. Classifier reordered so CV_death and HF_hosp are checked **before** ACM (prevents bare-'death' from matching "Cardiovascular Death"). — `ctgov_deep_mining.py:34-44, 320-340`
- [FIXED] **P1-6** PM bisection now hard-caps at `PM_BISECTION_CAP=1e6` and returns the cap with implicit `converged: False` if `Q_at(hi) > k-1`. — `cv_death_subatlas.py:73-90`
- [FIXED] **P1-7** Zero-variance studies filtered upstream (`se > SE_FLOOR=1e-8`) AND clamped inside `paule_mandel_tau2` via `max(se, SE_FLOOR)`. — `cv_death_subatlas.py:46, 165`
- [FIXED] **P1-8** Custom HTTP 429 + 503 backoff in `fetch_study` honors `Retry-After` header; exponential backoff for 5xx. — `ctgov_deep_mining.py:344-373`
- [FIXED] **P1-9** All `if value:` zero-drop sites converted to `is not None` checks (mining + integration report). — `ctgov_deep_mining.py:553, 565`, `ctgov_integration_report.py:38-44, 81-95`
- [FIXED] **P1-10** `extract_arm_counts` rejects NaN/inf values via `math.isfinite(val)`. — `ctgov_deep_mining.py:194-196`
- [FIXED] **P1-11** Magic numbers extracted: `MAX_MORTALITY_RATE`, `MIN_ARM_SIZE`, `REQUEST_DELAY_S`, `REQUEST_TIMEOUT_S`, `MAX_RETRIES`, `RETRY_BASE_DELAY_S`, `CHECKPOINT_EVERY`, `DISCREPANCY_PCT_THRESHOLD`. — `ctgov_deep_mining.py:32-50`
- [FIXED] **P1-12** All 4 scripts use `BASE_DIR = Path(__file__).resolve().parent` from shared `_io_utils` module. Path constants resolved at import time. — `_io_utils.py:8`, all 4 scripts
- [FIXED] **P1-13** `is_valid_nct()` regex (`^NCT\d{8}$`) called in `fetch_study` before URL build, and at inventory load to skip malformed entries. — `_io_utils.py:62`, `ctgov_deep_mining.py:339, 615`

---

## P2 — Minor — ALL FIXED 2026-04-10

- [FIXED] **P2-1** `qt(0.975, df)` exact lookup table for df ∈ {1..5}; Cornish-Fisher only for df ≥ 6. Validated against R: 0.0000 error for df 1-30. — `cv_death_subatlas.py:96-117`
- [FIXED] **P2-2** Q-profile I² confidence interval (Viechtbauer 2007 via Wilson-Hilferty χ² inversion); reported in pool dict as `I2_lo`/`I2_hi` and shown in markdown. — `cv_death_subatlas.py:154-181`
- [FIXED] **P2-3** PRISMA exclusion log written to `ctgov_prisma_exclusions.md` per run, classifying NCTs as `fetch_error` / `no_results_posted` / `no_mortality_outcome`. — `ctgov_deep_mining.py:692-734`
- [FIXED] **P2-4** `md_cell()` helper escapes `|` → `\|`, strips newlines, prepends `'` for cells starting with `=+@\t\r` (formula injection guard per OWASP CSV Injection). Used in all 3 markdown writers. — `_io_utils.py:39-65`
- [FIXED] **P2-5** Shared `_io_utils.py` module with `ensure_utf8_stdout()` + `BASE_DIR`. All 4 scripts import it. — `_io_utils.py`
- [FIXED] **P2-6** PM `max_iter` reduced to `PM_MAX_ITER=80` (bisection converges in <60 steps). Tolerance check kept. — `cv_death_subatlas.py:14, 80`
- [FIXED] **P2-7** Deterministic tie-break in candidate-by-tag selection: `key=lambda x: (x[0], x[1].get('outcome_id') or '')`. — `ctgov_deep_mining.py:516-517`
- [FIXED] **P2-8** `merge_ctgov_augmentations` returns a new list (`list(trials)`) instead of mutating input. — `cardiology_mortality_atlas.py:215-227`
- [FIXED] **P2-9** `_validate_ctgov_augmentations()` runs at module load and asserts `0 < lo <= hr <= hi` for every augmentation entry. — `cardiology_mortality_atlas.py:230-247`

---

## False Positive Watch (claims rejected after verification)

- **Peto formula `V_e = d·(N−d)·n_e·n_c / (N²·(N−1))`** — verified correct (Yusuf 1985 hypergeometric variance). EMPA-REG HF-hosp sanity check (Peto 0.633 vs reported 0.65) within expected Peto-vs-Cox drift.
- **HKSJ Q/(k-1) floor logic** — verified: `q_floor = max(1, Q_RE/df)`, `floor_applied = raw_q_over_df < 1.0`. Correct per advanced-stats.md.
- **I² from Q_FE** (not Q_RE) — verified correct per Higgins-Thompson.
- **Direction of Peto inputs** — verified `peto_hr_from_counts(events_e, n_e, events_c, n_c)` matches caller order in `extract_outcomes`.
- **JSON parser safety** — only `json.loads` / `json.load`. No `eval` / `pickle` / `yaml.load`.
- **TLS validation** — `urllib.request.urlopen` defaults verified ON.
- **No secrets in committed files.**
