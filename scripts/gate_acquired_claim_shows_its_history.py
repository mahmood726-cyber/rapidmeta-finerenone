r"""GATE: a pool that ACQUIRED a definite effect must carry its history.

THE FAILURE THIS REFUSES
    Correcting an inflated tau2 narrows an interval, and a narrowed interval
    can cross the null. The pool then EXCLUDES no-effect where the published
    one did not. That change announces nothing on its own -- a withdrawn
    claim is noticed by its absence, an appearing one is not -- so a reader
    cannot tell a correction from a result we always had.

    So: if a served sidecar's interval excludes the null AND the estimator
    that produced the artefact would not have, a correction record must
    exist for it. No record, no pass.

WHY THE CHECK IS ON THE SERVED BYTES, NOT ON A LIST
    A hardcoded list of "the 90" would be a control anchored to live data:
    it retires itself the moment the corpus changes, and it cannot see a
    NEW acquisition introduced tomorrow. This recomputes the condition from
    each artefact, so the population is whatever currently satisfies it.

    Of the 90 that satisfy it under the correction, only the ones actually
    swapped have CHANGED on the served surface. The rest still carry their
    historic values and have acquired nothing, so they are counted as
    PENDING and do not fail -- but they will the moment they are swapped,
    which is the point.

THE PLANT IS SYNTHETIC, AND DELIBERATELY SO
    --plant builds a temporary sidecar, in a temp directory, whose numbers
    satisfy the condition and for which no correction exists, and requires
    this gate to REFUSE it. Anchoring the plant to one of the real 90 would
    destroy the control the moment that file was corrected: the case would
    vanish and the gate would pass for the wrong reason, looking exactly as
    it does when it is working.
"""
from __future__ import annotations
import argparse
import glob
import json
import math
import os
import shutil
import subprocess
import sys
import tempfile

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


def acquired(path):
    """Does this artefact exclude the null where the defective form did not?"""
    try:
        d = json.load(open(path, encoding="utf-8"))
    except Exception:
        return None
    trials = d.get("trials") if isinstance(d, dict) else None
    rs = ([t for t in trials if isinstance(t, dict)
           and isinstance(t.get("yi"), (int, float))
           and isinstance(t.get("vi"), (int, float)) and t["vi"] > 0]
          if isinstance(trials, list) else [])
    if len(rs) < 2:
        return None
    ys = [t["yi"] for t in rs]
    vs = [t["vi"] for t in rs]
    _, lh, hh = pool(ys, vs, historic(ys, vs))
    _, lc, hc = pool(ys, vs, reml_tau2(ys, vs))
    return (not (lc <= 0.0 <= hc)) and (lh <= 0.0 <= hh)


def swapped_stems():
    p = subprocess.run(["git", "-C", ROOT, "diff", "--name-only",
                        SWAP + "^", SWAP, "--", "outputs/r_validation"],
                       capture_output=True)
    return {os.path.basename(l)[:-5]
            for l in p.stdout.decode("utf-8", "replace").split("\n")
            if l.strip().endswith(".json")}


def scan(sidecar_dir, corrections_dir, swapped):
    have = {os.path.basename(p)[:-3]
            for p in glob.glob(os.path.join(corrections_dir, "*.md"))}
    live_ok, live_missing, pending = [], [], []
    for p in sorted(glob.glob(os.path.join(sidecar_dir, "*.json"))):
        if os.path.basename(p).startswith("_"):
            continue
        if acquired(p) is not True:
            continue
        stem = os.path.basename(p)[:-5]
        if stem in swapped:
            (live_ok if stem in have else live_missing).append(stem)
        else:
            pending.append(stem)
    return live_ok, live_missing, pending


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--plant", action="store_true",
                    help="prove the gate can refuse, using a SYNTHETIC case")
    a = ap.parse_args()

    if a.plant:
        tmp = tempfile.mkdtemp(prefix="gate_plant_")
        try:
            # A synthetic pool of three CONSISTENT trials. The corrected
            # estimator finds tau2 = 0.02 and an interval of 0.3032 to
            # 1.2968, which excludes the null. The defective increment form
            # inflates tau2 to 1.3333 -- sixty-seven times larger -- and its
            # interval, -2.0899 to 3.6899, includes it. Three trials that
            # agree, turned into "no effect" by the estimator alone.
            #
            # These values were FOUND BY SEARCH, not guessed: a first attempt
            # used trials that disagreed, which makes the CORRECTED tau2
            # large and produces the opposite condition. The plant reported
            # NO VERDICT rather than passing, which is why this one exists.
            synth = {"k": 3, "tau2": 0.0, "trials": [
                {"name": "SYNTH-A", "yi": 0.60, "vi": 0.02},
                {"name": "SYNTH-B", "yi": 0.80, "vi": 0.02},
                {"name": "SYNTH-C", "yi": 1.00, "vi": 0.02}]}
            # NOT leading-underscore: scan() skips those (they are audit
            # siblings by convention), and a first version of this plant
            # was named __SYNTHETIC_PLANT__.json and was silently skipped
            # by that very filter -- the plant reported MISSED for a gate
            # that was fine. A filter that drops a candidate before it is
            # counted is the likeliest place to lose a population.
            sp = os.path.join(tmp, "SYNTHETIC_PLANT_NOT_A_REAL_TOPIC.json")
            json.dump(synth, open(sp, "w", encoding="utf-8"))
            got = acquired(sp)
            print("SYNTHETIC PLANT")
            print("  the planted artefact satisfies 'acquired a claim': %s" % got)
            if got is not True:
                print("  *** the plant does not create the condition it tests.")
                print("  *** NO VERDICT -- fix the plant, not the gate.")
                return 2
            ok, missing, _pend = scan(tmp, CORRECTIONS,
                                      {"SYNTHETIC_PLANT_NOT_A_REAL_TOPIC"})
            caught = "SYNTHETIC_PLANT_NOT_A_REAL_TOPIC" in missing
            print("  gate refuses it for having no correction record: %s" % caught)
            print("  -> %s" % ("PLANT CAUGHT: the gate has a reachable FAIL"
                               if caught else
                               "PLANT MISSED: this gate cannot refuse anything"))
            return 0 if caught else 1
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    swapped = swapped_stems()
    ok, missing, pending = scan(SERVED, CORRECTIONS, swapped)
    print("POOLS THAT ACQUIRED A DEFINITE EFFECT UNDER THE CORRECTION")
    print("  LIVE with a correction record      %d" % len(ok))
    print("  LIVE with NO correction record     %d   <- refused" % len(missing))
    print("  PENDING (served bytes unchanged)   %d   <- nothing has appeared"
          % len(pending))
    print("  identity: %d + %d + %d == %d"
          % (len(ok), len(missing), len(pending),
             len(ok) + len(missing) + len(pending)))
    for s in missing[:20]:
        print("      NO RECORD: %s" % s)
    if missing:
        print("")
        print("REFUSED: %d served pool(s) exclude the null where the defective"
              % len(missing))
        print("estimator did not, and carry no correction record. A claim that")
        print("appears without its history reads as one we always made.")
        return 1
    print("")
    print("PASS: every pool that has acquired a definite effect on the served")
    print("surface carries a correction record. %d more will require one when"
          % len(pending))
    print("they are swapped; they have acquired nothing yet.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
