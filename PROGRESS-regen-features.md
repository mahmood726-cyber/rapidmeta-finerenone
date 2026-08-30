# Lane: regen-features — the six winning sections moved into the harness

**The two numbers: regeneration 13 of 13, bespoke fraction 0%.** Baseline this evening was
4 of 13 and 69%. Path: 4 → 7 → 11 → 13.

Worktree `F:/wt-regen`, branch `lane/regen-features-2026-08-29`, based on `b719e98f1`
(which `origin/main` already contains). 14,679 tracked files.

---

## What landed, in the order the judges weighted it

| # | component | what it derives | coverage over the corpus it polices |
|---|---|---|---|
| 1 | `absolute_effects.py` | risk per 1,000 and the NNT, from the pooled control arms | 4 of 175 outcomes converted (2.3%) |
| 2 | `subgroup_efficacy.py` | stratified reading in three states | 2 blocks of 176 (1.1%) |
| 3 | `other_outcomes.py` | safety and other outcomes, each row with its provenance tier | 14 rows, 1 of 141 objects |
| 4 | `count_provenance.py` | registry vs adjudicated counts, repooled under each; plus the estimand mismatch | 1 of 141 (0.7%) |
| 5 | `clinical_reading.py` | every clause conditional on a derived fact | 1 object earns all 7 clauses; 119 earn none |
| 6 | `audit_trail.py` | walked from the object, quoted and unquoted against a denominator | 2,440 sourced records, 146 quoted (6.0%) |
| 7 | `certainty_profile.py` | the GRADE profile, rating **recomputed** from its own steps | 5 recompute and agree, 1 refused, 112 hold none |

⚠️ **The coverage numbers are low and that is the honest state.** The blocker is the corpus,
not the harness: each component RENDERS on all 141 objects and prints a named refusal where it
cannot derive. **13 of 13 is a claim about ONE object**, `agyw-hiv-prep-review`.

## The acceptance bar

⛔ **Two halves, and the second is the one that failed this evening.** Six blinded judges
preferred our page; the harness reproduced 4 of its 13 winning features. It now reproduces 13.

⭐ **The detectors were checked, not just the score.** Two were strengthened — `per 1000 women`
and `21 or younger` were proxies keyed to the hand-built page's wording and scored the more
accurate harness output as ABSENT. Both replacements were planted both ways against a genuine
pre-change build of the same object (56,396 rendered characters). **The final detector set
scores that pre-change page at exactly 4 of 13 — identical to the original set.** The page
gained nine capabilities; the ruler did not move.

`LOSING_AXES` is scored **separately and deliberately not added to FEATURES**: folding it in
would change the acceptance bar's denominator, and "13 of 13" and "14 of 14" would then mean
different things while looking like progress. Currently **2 of 3** — GRADE certainty and its
derivation are covered; **ICTRP is not run and that is a real gap.**

## What the primary read corrected on the winning page

ASPIRE `PMC4993693`, `ncbi_efetch` after Europe PMC 503, 44,179 rendered chars,
sha256 `a6c75ad7e331aff7…` — the fingerprint the pilot already cited.

* The pilot labels a stratum **"18 to 24"**. ASPIRE's PRESPECIFIED stratum is **under 25**,
  P = 0.64.
* The pilot **omits the interaction test**. ASPIRE reports **P = 0.02** on the prespecified
  split.
* The pilot presents the age strata as the review's. **They are ASPIRE's alone.**
* **Three numbers on the pilot cannot be traced to any document this project holds** —
  gonorrhoea RR 1.00 (0.87–1.15), trichomoniasis RR 1.06 (0.92–1.23), serious adverse events
  RR 1.12 (0.94–1.32). The comparator was retrieved (`PMC8092571`, sha256 `a61512f81de560a9…`)
  and contains none of them. **They are not carried forward.**
* The Ring Study's adjudicated counts stay at the external-review tier: PMID 27959766 has no
  PMC id, `europepmc_by_pmid` returned 404, no other route existed.

## Gate 7, answered by measurement rather than by a line in a file

`ssot/build_tabbed.py` has radius 155 and I verified on one object. Before acknowledging:
**846 component renders over all 141 objects — 0 raised, 0 degenerate**, plus **5 full
end-to-end builds, all rc=0**, chosen to span the refusal paths (withdrawn pool, HR pool,
rate-ratio pool, multi-outcome vaccine, no subgroup block). Recorded in
`gates/BLAST_RADIUS_ACK.json` with that measurement beside it.

## Defects the controls caught in my own work, all before landing

* absolute-effect intervals printed **descending** whenever the ratio's CI crossed 1
* `subgroups` was already taken by `build_app_v2` for POOLED strata — a within-trial analysis
  written under that name **crashed the build**, and only because the shapes were incompatible
  enough to raise
* the audit-trail walk emitted **5 rows for 3 numbers**, descending into each record's own
  source block — citation apparatus counted as the numbers cited
* an escaped em-dash default rendered as the literal `&amp;mdash;`
* a `\b` in a non-raw string wrote a **literal backspace byte** into the test file

⭐ **And one my own plants missed.** A separate displayed-bytes checker, run over the whole
corpus, found `audit_trail` stringifying raw Python dicts into the Value column — **99 findings
across 141 objects**, putting the bare token `None` on the page. My model answer used scalar
values throughout, so nothing exercised the structured case. **99 → 0 after the fix**, and a
fourth control now covers it. *A second instrument found what re-reading the first would never
have.*

## Findings raised on other topics — flagged, not fixed

* `cab-prep-hiv-review` stores GRADE certainty **LOW**; its own five steps give HIGH − 3 =
  **VERY LOW**, and its own imprecision step reads "already at the floor". Recorded in
  `out/ESCALATIONS.jsonl`. The component surfaces the disagreement on the page rather than
  picking one.
* **11 of 407 trials (2.7%)** carry event counts in a non-canonical shape and need arm roles
  authored — work-list at `F:/claude-temp/regen-lane/codex/jobA_result.json`. ⚠️ Roles must be
  AUTHORED, never inferred: HPTN 083 stores `cabotegravir_events` and `tdf_ftc_events` and
  **both arms are active drugs**.
* **The four components that landed before tonight have no `plant()` and no `coverage()`** —
  `both_intervals`, `currency_query`, `estimand_statement`, `integrity_section`. Found by
  `gates/gate14_component_contract.py`. Scaffolds generated at
  `F:/claude-temp/regen-lane/codex/scaffold_*.py`; ⛔ **the model answers are deliberately left
  to a human**, because a control whose expected answer was invented by the process that wrote
  the component is a tautology.

## Next, in order

1. **SERVE IT.** Pages deploys from `main`. `AGYW_HIV_PREP_REVIEW.html` is rebuilt in this
   worktree (1,107,240 bytes, all seven sections present, manuscript guard OK, div balance 0).
   It is **not pushed**, so the live page still has none of this. ⚠️ A sibling commit on `main`
   already records this exact failure for the earlier four components: *"my four components
   were on 0 of 163 delivered pages, and I had reported them landed."*
2. **ICTRP** — the one losing axis still open.
3. The 11 trials needing authored arm roles; each one raises absolute-effects coverage.
4. Backfill `plant()`/`coverage()` on the four legacy components.
