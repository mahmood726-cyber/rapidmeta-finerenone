# Cross-family adversarial gate brief — P. vivax radical cure NMA

**Artifact:** `VIVAX_RADICAL_CURE_NMA_REVIEW.html` (repo root)
**Branch:** `build/malaria-vivax-radical-cure-nma` · **STAGED, NOT PUSHED**
**Gate:** Claude (author) → Codex (openai) → Gemini (google) → Mahmood's go
**Rule:** three independent model families. Do not route the adversary passes to
another Anthropic model — a homogeneous panel is the weak configuration.

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
