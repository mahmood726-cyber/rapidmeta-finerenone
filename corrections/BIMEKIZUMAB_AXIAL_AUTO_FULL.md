# CORRECTION (DRAFT -- NOT PUBLISHED, NOT SERVED)

    status: HELD pending a ruling on whether the 692 binary sidecars are
            regenerated. This file is append-only and does NOT overwrite,
            edit, or replace the original artefact. The original stands
            unchanged until that ruling.

## Artefact

    file    outputs/r_validation/BIMEKIZUMAB_AXIAL_AUTO_FULL.json
    sha256  0409cca5959af43a06ff6b7fca40294565e219bd97dd47331f5755b489ce5b11
    k       4 trials
    stored tau2 in the file: 0.0

The sha256 pins WHICH bytes this correction is about. If the file changes,
this correction is about the old bytes and must be re-derived, not amended.

## What was published

    pooled odds ratio  0.361486
    95% interval       0.131052 to 0.997106
    excludes the null  YES

## What the corrected estimator gives

    pooled odds ratio  0.425505
    95% interval       0.101171 to 1.789590
    excludes the null  NO
    tau2               0.191513361   (published value: 0.0)

## The defect, in one sentence

`scripts/build_binary_sidecar.py::reml_tau2` estimates the between-study
variance with an INCREMENT update that omits the `1/sum(w)` term separating
REML from ML, and because the result is clamped at zero that update has a
fixed point AT zero -- so it reported no heterogeneity for this pool when
there is some.

## The value that proves it, computable without trusting us

Take the four trials of `ssot/arni-hfref/arni-hfref.json`, outcome
`cvdeath_or_hfh_first`, whose risk differences and variances are:

    y = [-0.046899960103527, -0.031893468849991, 0.02027027027027, 0.042105263157895]
    v = [8.7019819435862e-05, 0.00098780188619885, 0.0034509021994185, 0.0019734655197551]

metafor 5.0.1 under R 4.6.0 returns tau2 = 0.0007252899298732 for these, and
that value is stored independently in the object itself at
`results.by_outcome.cvdeath_or_hfh_first.count_panels.rd.tau2`. The shipped
function returns exactly 0.0 on the same input. Either estimator can be run
against that published number by anyone; no claim here has to be taken on
trust.

    correct REML update, iterated from tau2 = 0 and clamped at >= 0:
        w = 1/(v + tau2);  sw = sum(w);  mu = sum(w*y)/sw
        tau2 <- sum(w^2*((y-mu)^2 - v)) / sum(w^2)  +  1/sw

## Reproducing this specific row

    python scripts/tau2_blast_radius.py

classifies every sidecar whose stored tau2 is exactly 0.0. This artefact is
one of 3 in state CONCLUSION_FLIPS out of 351 candidates; 250 of those 351
are LEGITIMATELY_ZERO, meaning the correct estimator also returns zero and
those files were never wrong.

## The trial-level values this pool was built from

    BE MOBILE 2                          yi -2.053765  vi 2.14696
    BE MOBILE 1                          yi -1.205464  vi 0.078457
    NCT03215277                          yi -0.387766  vi 0.354219
    BE AGILE                             yi +1.659448  vi 2.43335

## Note on duplication

BIMEKIZUMAB_AS_AUTO_FULL and BIMEKIZUMAB_AXIAL_AUTO_FULL carry IDENTICAL
trial values. They are two files over one evidence set, so the three
CONCLUSION_FLIPS artefacts represent TWO distinct pools, not three. Counting
them as three would overstate the number of independent claims affected.

## What is NOT claimed here

That the corrected interval is the right answer for this question. Only that
the published interval was produced by an estimator that could not report
heterogeneity, and that a correct estimator moves this interval across the
null. Whether this pool should exist at all is a separate judgement and is
not made here.
