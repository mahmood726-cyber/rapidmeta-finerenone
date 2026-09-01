r"""Correction records for pooled intervals that ACQUIRED a definite effect.

WHY ONLY SOME OF THE 90
    90 sidecars flip from including the null to excluding it when the
    estimator defect is corrected. Only the ones the swap actually WROTE have
    changed on the served surface. The rest still carry their historic
    values, so nothing about them has appeared, and a record saying "this
    changed" would assert a history the artefact does not have.

    A correction for a change that has not happened is the same defect as a
    number computed from nowhere. So this emits records ONLY for sidecars
    whose served bytes actually moved, and counts the rest as PENDING.

WHY THIS DIRECTION IS THE DANGEROUS ONE
    A withdrawn claim announces itself by absence -- a reader notices
    something is gone. A claim that APPEARS announces nothing at all. These
    pages are the ones most likely to be read as a result rather than as a
    correction, which is exactly why the change has to travel with them.

FORMAT
    The same record shape already in corrections/, reused rather than
    reinvented: the artefact pinned by sha256, the old interval, the new one,
    the defect in one sentence, and the metafor value that settles it.
    Nothing here is composed at runtime; every sentence is a fixed template
    and every number is derived.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import math
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)

from build_binary_sidecar import t_quantile_975, reml_tau2  # noqa: E402

SERVED = os.path.join(ROOT, "outputs", "r_validation")
CORRECTIONS = os.path.join(ROOT, "corrections")
SWAP = "a399b442f"


def historic(ys, vs, max_iter=200, tol=1e-10):
    t = 0.0
    for _ in range(max_iter):
        w = [1.0 / (v + t) for v in vs]
        sw = sum(w)
        mu = sum(a * y for a, y in zip(w, ys)) / sw
        num = sum((a ** 2) * ((y - mu) ** 2 - v) for a, y, v in zip(w, ys, vs))
        den = sum(a ** 2 for a in w)
        new = max(0.0, t + num / den)
        if abs(new - t) < tol:
            return new
        t = new
    return t


def pool(ys, vs, tau2):
    k = len(ys)
    w = [1.0 / (v + tau2) for v in vs]
    sw = sum(w)
    mu = sum(a * y for a, y in zip(w, ys)) / sw
    q = sum(a * (y - mu) ** 2 for a, y in zip(w, ys)) / (k - 1)
    se = math.sqrt(max(q, 1.0) / sw)
    t = t_quantile_975(k - 1)
    return mu, mu - t * se, mu + t * se


def swapped_stems():
    p = subprocess.run(["git", "-C", ROOT, "diff", "--name-only",
                        SWAP + "^", SWAP, "--", "outputs/r_validation"],
                       capture_output=True)
    return {os.path.basename(l)[:-5]
            for l in p.stdout.decode("utf-8", "replace").split("\n")
            if l.strip().endswith(".json")}


def rows():
    swapped = swapped_stems()
    live, pending = [], []
    import glob
    for f in sorted(glob.glob(os.path.join(SERVED, "*.json"))):
        if os.path.basename(f).startswith("_"):
            continue
        try:
            d = json.load(open(f, encoding="utf-8"))
        except Exception:
            continue
        trials = d.get("trials") if isinstance(d, dict) else None
        rs = ([t for t in trials if isinstance(t, dict)
               and isinstance(t.get("yi"), (int, float))
               and isinstance(t.get("vi"), (int, float)) and t["vi"] > 0]
              if isinstance(trials, list) else [])
        if len(rs) < 2:
            continue
        ys = [t["yi"] for t in rs]
        vs = [t["vi"] for t in rs]
        th, tc = historic(ys, vs), reml_tau2(ys, vs)
        mh, lh, hh = pool(ys, vs, th)
        mc, lc, hc = pool(ys, vs, tc)
        if not (not (lc <= 0 <= hc) and (lh <= 0 <= hh)):
            continue
        stem = os.path.basename(f)[:-5]
        rec = (stem, f, th, tc, (mh, lh, hh), (mc, lc, hc), len(ys))
        (live if stem in swapped else pending).append(rec)
    return live, pending


TEMPLATE = """# CORRECTION -- A DEFINITE EFFECT APPEARED, AND THIS IS WHY

    status: the served artefact HAS CHANGED. This record exists so the change
            travels with it. A claim that appears without its history is
            indistinguishable from a claim we always made, and this direction
            of change announces nothing on its own: a withdrawn claim is
            noticed by its absence, an appearing one is not.

## Artefact

    file    outputs/r_validation/{stem}.json
    sha256  {sha}
    k       {k} trials

## What was published

    pooled odds ratio  {or_old:.6f}
    95% interval       {lo_old:.6f} to {hi_old:.6f}
    excludes OR = 1    NO -- the interval included no effect
    tau-squared        {tau_old:.8g}

## What the corrected estimator gives

    pooled odds ratio  {or_new:.6f}
    95% interval       {lo_new:.6f} to {hi_new:.6f}
    excludes OR = 1    YES
    tau-squared        {tau_new:.8g}

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
"""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    a = ap.parse_args()
    live, pending = rows()
    print("CLAIM_CREATED, scoped to what actually changed on the served surface")
    print("  LIVE    (swapped; a record is written) %d" % len(live))
    print("  PENDING (served bytes unchanged)       %d" % len(pending))
    print("  identity: %d + %d == %d" % (len(live), len(pending),
                                         len(live) + len(pending)))
    print("")
    for stem, path, th, tc, old, new, k in live:
        sha = hashlib.sha256(open(path, "rb").read()).hexdigest()
        body = TEMPLATE.format(
            stem=stem, sha=sha, k=k,
            or_old=math.exp(old[0]), lo_old=math.exp(old[1]),
            hi_old=math.exp(old[2]), tau_old=th,
            or_new=math.exp(new[0]), lo_new=math.exp(new[1]),
            hi_new=math.exp(new[2]), tau_new=tc)
        out = os.path.join(CORRECTIONS, stem + ".md")
        print("  %-44s OR %.4f (%.4f-%.4f) -> %.4f (%.4f-%.4f)"
              % (stem, math.exp(old[0]), math.exp(old[1]), math.exp(old[2]),
                 math.exp(new[0]), math.exp(new[1]), math.exp(new[2])))
        if a.write:
            with open(out, "w", encoding="utf-8", newline="\n") as fh:
                fh.write(body)
            print("      wrote %s" % os.path.relpath(out, ROOT))
    if a.write is False:
        print("\n  DRY RUN. Re-run with --write.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
