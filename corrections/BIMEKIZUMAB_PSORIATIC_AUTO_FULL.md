# CORRECTION -- A DEFINITE EFFECT APPEARED, AND THIS IS WHY

    status: the served artefact HAS CHANGED. This record exists so the change
            travels with it. A claim that appears without its history is
            indistinguishable from a claim we always made, and this direction
            of change announces nothing on its own: a withdrawn claim is
            noticed by its absence, an appearing one is not.

## Artefact

    file    outputs/r_validation/BIMEKIZUMAB_PSORIATIC_AUTO_FULL.json
    sha256  d24b7f755d5e371e1269d31393701b629b282866d4893536d13821e3106f8069
    k       3 trials

## What was published

    pooled odds ratio  0.063321
    95% interval       0.000000 to 134303895692.098663
    excludes OR = 1    NO -- the interval included no effect
    tau-squared        130.4445

## What the corrected estimator gives

    pooled odds ratio  0.064329
    95% interval       0.004575 to 0.904584
    excludes OR = 1    YES
    tau-squared        1.0322418

## The defect, in one sentence

`scripts/build_binary_sidecar.py::reml_tau2` estimated the between-study
variance with an INCREMENT update that omits the `1/sum(w)` term separating
REML from ML; on this pool it failed to converge and stopped at its
200-iteration cap with an INFLATED tau2, which flattened the weights and made
the published interval too WIDE.

## Why the interval narrowed rather than moved

The HKSJ half-width is t * sqrt(max(q,1)/sum(w)) with w = 1/(v + tau2).
Lowering tau2 raises every weight, raises sum(w), and NARROWS the interval.
So correcting an inflated tau2 can only ever ADD a definite effect, never
remove one -- measured across the corpus as 90 added and 0 removed, with zero
violations of that direction in 450 files where tau2 changed at all.

## The value that settles it, checkable without trusting us

metafor 5.0.1 under R 4.6.0 is the external oracle. On the four arni-hfref
trials it returns tau2 = 0.0007252899298732 where the defective form returns
exactly 0.0; that value is independently stored in the object itself at
results.by_outcome.cvdeath_or_hfh_first.count_panels.rd.tau2. The corrected
estimator is validated against 46 metafor values with 0 disagreements
(tests/test_metafor_oracle.py), and the fixture is tracked so a fresh clone
reproduces the proof without R installed.

    corrected REML, iterated from tau2 = 0 and clamped at >= 0:
        w = 1/(v + tau2);  sw = sum(w);  mu = sum(w*y)/sw
        tau2 <- sum(w^2*((y-mu)^2 - v)) / sum(w^2)  +  1/sw
    with bisection on g(t) = f(t) - t where that iteration does not settle.

## What is NOT claimed

That the corrected interval is the right answer for this question, or that
these trials should be pooled at all. Only that the published interval was
produced by an estimator that could not converge here, and that a correct one
moves it across the null.
