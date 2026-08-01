# Cross-family adversarial gate brief — P. vivax radical cure NMA

**Artifact:** `VIVAX_RADICAL_CURE_NMA_REVIEW.html` (repo root)
**Branch:** `build/malaria-vivax-radical-cure-nma` · **STAGED, NOT PUSHED**
**Gate:** Claude (author) → Codex (openai) → Gemini (google) → Mahmood's go
**Rule:** three independent model families. Do not route the adversary passes to
another Anthropic model — a homogeneous panel is the weak configuration.

## Round 2 — re-gate after fixes (current state)

Round 1 (Codex gpt-5.5 + an independent re-derivation from counts) found the
arithmetic clean, confirmed the robust-core claim three ways, and kept EXPOSED.
Six items were raised; **all six are fixed** (commit `1daa80c`). Every round-1
claim was re-derived locally in `verify_gate_findings.R` before being acted on —
all six confirmed, including that F1 was a genuine error of mine.

| # | Finding | Status |
|---|---|---|
| F1 | Q-decomposition causal attribution backwards and non-invariant | **fixed** — attribution moved to the P3 multiverse split; page states the earlier version was wrong |
| F2 | Focal edge labelled with network-wide I² | **fixed** — I² 76.1% (Q 16.75, df 4, p 0.0022) |
| F3 | No edge-specific τ² | **fixed** — Paule-Mandel 1.067 (0.516, 2.210) |
| F4 | N was randomised, not analysed | **fixed** — 2,153 randomised / 2,071 evaluable, 82 (3.81%) shown by trial |
| F5 | GATHER 1.141 vs forest 1.125 | **fixed** — FDA Table 41 retrieved; all three ORs shown with derivations |
| F6 | JSON leaked an estimate for a NOT-ESTIMABLE cell | **fixed** — nulled at source |

### Gemini lane — MUST be re-run on 3.1 Pro

Round 1's Gemini lane ran on **Flash tier (3.6 Flash), not the pinned 3.1 Pro**, and
it **ratified and forged** — so its statistical check did not count and must not be
treated as a passed lane. The re-gate must force Pro.

`agy --print` **ignores `--model`**. Set the model in
`C:\Users\mahmo\.gemini\antigravity-cli\settings.json` (`"model": "Gemini 3.1 Pro (High)"`)
or via the interactive `/model` picker, then confirm with a **real exec that echoes
its own model family** — `agy --print "Reply OK + your model+family"` must come back
naming Gemini 3.1 Pro. A lane that can only report "alive" is not a check. Do not use
`--dangerously-skip-permissions`; give the model its evidence inline so it needs no
file tools.

### What round 2 should attack first

1. **The rewritten F1 passage.** Is the new attribution — partner drug shows in the
   P3 multiverse split, not in between-design Q — itself correct? Verify that
   INSPECTOR and DETECTIVE Part 2 really do share a design, and that dropping the
   single-trial nodes really does reverse the split.
2. **F3's implication.** If the edge-specific interval (0.516, 2.210) is the honest
   one, should the *network* estimate be the headline at all, or should the artifact
   lead with the pairwise edge?
3. **F5's three ORs.** Confirm 1.125 and 1.157 from the counts, and confirm 1.141
   cannot be reproduced as a cross-product from any GATHER count pair.
4. **Whether EXPOSED is still right** now that the strongest-sounding reason
   (between-design inconsistency) has been withdrawn as unsupported. The reason list
   changed; the tier did not. Argue it.

---

## What the artifact claims

| | Claim A — full network | Claim B — robust core |
|---|---|---|
| nodes | 7 | 3 |
| trials | 5 | 5 |
| N | 2,153 | 1,690 |
| τ² / I² | 0.2471 / 64.8% | 0.2471 / 64.8% |
| TQ 300 vs no-therapy | **OR 0.196 (0.098, 0.392)** | 0.196 (0.098, 0.392) |
| PQ 3.5 vs no-therapy | **OR 0.183 (0.092, 0.363)** | 0.183 (0.092, 0.363) |
| TQ 300 vs PQ 3.5 | **OR 1.072 (0.629, 1.825)** | 1.072 (0.629, 1.825) |

Headline: **both hypnozoiticidal regimens roughly quintuple the odds of staying
recurrence-free versus blood-stage drug alone; tafenoquine 300 mg and primaquine
3.5 mg/kg are indistinguishable from each other — but the trials disagree sharply
about that second comparison, and the disagreement is between designs, not within.**

---

## Pre-registered adversary targets (declared at Stage 0, before fitting)

Attack these first. They were named before any estimate existed.

1. **Recurrence ≠ relapse, irreducibly.** PCR cannot separate relapse from
   reinfection in vivax. Does the app ever call the outcome "relapse"? (It should
   not, anywhere, including the badge.)
2. **Partner blood-stage drug confounds the anti-hypnozoite estimate.** INSPECTOR
   (OR of relapsing 4.57, 1.75–11.97) and EFFORT's Indonesia stratum (22.4%) both
   say tafenoquine underperforms with DHA-piperaquine. Is axis P3 doing real work,
   or is the pooled 1.072 being presented as if partner drug were noise?
3. **Chloroquine alone is not a placebo, and the reference node is not one thing** —
   chloroquine alone in DETECTIVE, DHA-piperaquine alone in INSPECTOR. Does pooling
   them into a single "no hypnozoiticidal therapy" node break the analysis rather
   than merely complicate it?
4. **CYP2D6 breaks transitivity between the PQ and TQ nodes specifically** (primaquine
   needs CYP2D6 activation; tafenoquine does not). INSPECTOR found 45% poor/intermediate
   metabolisers and no significant effect — in n=150. Is "no effect detected" being
   used as "no effect"?
5. **The approved 300 mg tafenoquine dose is contested** (Watson eLife 2022 vs Sharma
   eLife 2024). EFFORT's median dose was 5.4 mg/kg.

---

## Specific things to try to break

**Statistical**
- τ² by REML at k=5 — is a single common τ² across all contrasts defensible when
  14 of 17 edges are single-trial? Would Paule-Mandel or a Bayesian half-normal prior
  move the focal CI materially?
- Q = 17.04 (df 6, p 0.009) is decomposed as within-design 5.00 (df 2) / **between-design
  12.05 (df 4, p 0.017)**. Is calling that "designs disagree" correct, or is it an artefact
  of DETECTIVE Part 1's six-arm structure dominating the design space?
- Full network and robust core return **identical** shared-contrast estimates (ratio 1.000).
  The app claims this is the arithmetic signature of saturated single-trial contrasts, not
  a bug. **Verify that claim independently** — it is the load-bearing methodological
  assertion in the artifact.
- `netsplit` reports direct-evidence proportion **1.00** for the focal edge. If indirect
  evidence contributes nothing anywhere, is calling this a network meta-analysis rather
  than a set of pairwise meta-analyses overclaiming?
- Odds ratios are pooled throughout because INSPECTOR violates proportional hazards.
  Is OR the right common currency when three trials report KM and two report HRs?

**Data integrity — try to find a wrong number**
- Every arm-level count is in `preflight/arm_level_evidence.json` and `preflight/network.json`
  with its source. Re-derive any of them from CT.gov / the publication / FDA NDA 210795.
- **GATHER trap:** the app must use OR **1.141**, never the abstract's **1.81**
  (426 = 260+166, 214 = 129+85 — the abstract pools GATHER with DETECTIVE Part 2).
  Check the app never leaks 1.81 or 426/214 as GATHER's own.
- **INSPECTOR:** registry 12/22/52% are crude proportions; the abstract's 11.2/21.0/52.0%
  are Kaplan-Meier. Both should appear, neither should be called an error.
- **EFFORT:** 97.55% CIs, not 95%. Check nothing treats them as 95%.
- **IMPROV:** excluded because it has no 180-day row. Confirm no number anywhere in the
  artifact is derived from IMPROV's person-year rate.
- **Arakoda (NDA 210607):** supplies zero efficacy nodes. Check the app never implies two
  FDA packages back the network.
- **EMA:** the permitted claim is "no EMA authorisation or opinion found (verified
  2026-07-30)". The forbidden claims are "EMA-covered" and "no EMA opinion exists".

**Verdict honesty**
- `window.__verdict.verdict` = **EXPOSED**, p0_total = 0, 8 reasons.
- `check_verdict_parity.py` enforces that no rendered prose asserts a different tier.
  It passes, and it blocks on a known-bad input (negative control run).
- **Is EXPOSED the right tier?** Arithmetic and provenance gates all pass; the exposure is
  structural. An adversary should argue it either way — MODERATE (nothing is wrong) or
  EXPOSED (the pooled estimate must not be read at face value). The app takes the second view.

---

## Reproduce everything

```
cd malaria_vivax_nma
python preflight/check_network.py preflight/network.json   # integrity + connectivity
python nma_fit.py preflight/network.json                   # the fit
Rscript validate_netmeta.R                                 # independent R check
python multiverse.py                                       # 19 multiverse cells
python build_app.py                                        # regenerate the HTML
python check_verdict_parity.py                             # badge vs window.__verdict
```

Validation already recorded: `nma_fit.py` matches R `netmeta` fixed-effect log-ORs and SEs
to **4.83e-08** (tolerance 1e-6); Q, df, p, I² and all five per-trial ORs reproduce exactly.

---

## Known-honest gaps the gate should NOT flag as errors

These are deliberate and documented; flag them only if the *documentation* is wrong.

- IMPROV excluded despite N=2,336 — no 180-day row exists (verified against full text).
- PQ 14 d high (7 mg/kg), PQ weekly, and paediatric TQ nodes absent — no 180-day evidence.
- P1b multiverse cell marked NOT ESTIMABLE rather than approximated from 168-day/3-month data.
- τ² fixed at 0 and labelled "not estimable" in the two single-trial cells (P3b, P6b).
- DETECTIVE Part 1 tier T2, not T1 — NCT01376167 posts results for Part 2 only.

---

## Independent re-verification of F1–F6 (2026-08-01)

The six fixes from `1daa80c` were **re-verified from scratch** rather than taken
from the commit message. The whole pipeline was re-run and every claim re-checked
against the regenerated artifact.

### Pipeline re-run — all green, and byte-identical output

| Step | Result |
|---|---|
| `preflight/check_network.py` | ALL GATES PASS, exit 0 |
| `nma_fit.py` | τ²=0.2471, Q=17.04, df=6, p=0.009, I²=64.8%; focal OR **1.072 (0.629, 1.825)** |
| `validate_netmeta.R` | exit 0; `netsplit` reproduces, focal edge k=5, direct proportion 1.00 |
| `multiverse.py` | 19 cells; P3a **1.070** (I² 37.2%, 3 chloroquine trials) vs P3b **3.841** (1 DHA-piperaquine trial) |
| `build_app.py` | exit 0 — regenerated HTML is **byte-identical** to the committed file (`git status` clean) |
| `check_verdict_parity.py` | VERDICT PARITY PASS, exit 0 |

Byte-identical regeneration is the load-bearing result: the artifact in the tree
is exactly what the committed pipeline produces from the committed inputs.

### F1 and F6 confirmed in the artifact, not just in the changelog

* **F1** — the page now states that the Q decomposition does **not** support the
  partner-drug attribution and that an earlier version wrongly said it did. It
  gives both reasons: "design" in `decomp.design()` is node-set geometry, so
  INSPECTOR shares its design with DETECTIVE Part 2 and the partner-drug contrast
  sits **inside the within-design term**; and the split reverses on the robust
  core (within 13.56 df 5 p 0.019 / between 3.48 df 1 p 0.062). The attribution is
  carried by the P3 multiverse split, which the re-run reproduces exactly.
* **F6** — `outputs/vivax_nma_results.json` was parsed directly. The only cell with
  `estimable: false` is **P1b**, and it carries **no** `or`/`lo`/`hi`. Rendered
  output agrees: the P1b row shows NOT ESTIMABLE with no number. P3b and P6b do
  carry ORs — correctly, since only their τ² is not estimable, which is a
  different claim and is labelled as such.

### The gates can fail — negative controls run this round

The recurring failure mode across the corpus is a gate that cannot return a
second answer. Both gates here were tested against deliberately broken input and
**both blocked**:

| Gate | Injected fault | Result |
|---|---|---|
| `check_verdict_parity.py` | prose asserting "MODERATE certainty" against `__verdict` = EXPOSED | `VERDICT PARITY FAILED (1)`, **exit 1** |
| `preflight/check_network.py` | DETECTIVE Part 1 no-therapy arm recurrence 31 → 104 (exceeds n=54) | `FAILED (2)` — sum mismatch and out-of-range, **exit 1** |

Both inputs were restored; `git status` is clean for both files.

### Runtime state of the rendered artifact

`window.__verdict` = **EXPOSED**, `p0_total` 0, 9 reasons; counts carry
`P1_focal_edge_heterogeneity` (the stale `P1_between_design_inconsistency` key is
gone). Badge text equals the verdict. Six tables at **7 / 3 / 5 / 5 / 19 / 17**
rows. No horizontal scroll at 375 px. **0 severe console errors.**

### Data-integrity traps from the brief — all pass

* **GATHER:** `1.81`, `426` and `214` appear only inside the passage that proves
  they are the *pooled* GATHER + DETECTIVE Part 2 figures (426 = 260+166,
  214 = 129+85) and must not be used as GATHER's own. No leak.
* **EFFORT:** 97.55% CIs are identified as alpha-spent at an interim look and
  converted on the log scale; nothing treats them as 95%.
* **IMPROV:** excluded outright, with the reason stated; no number derives from it.
* **EMA:** uses the permitted claim "no EMA authorisation or scientific opinion
  (verified 2026-07-30)". Neither forbidden form appears.
* **Arakoda:** the page states only NDA 210795 backs the network.

**Conclusion: F1–F6 are complete. No further code change was required.** The
branch is ready for the round-2 cross-family gate, whose first task is unchanged —
force the Gemini lane onto 3.1 Pro and confirm with an exec that echoes its own
model family.
